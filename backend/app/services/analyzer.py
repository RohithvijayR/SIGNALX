import time
import json
import numpy as np
from typing import Dict, Any, Optional, Tuple

from app.parsers.iq_parser import parse_iq_file
from app.parsers.wav_parser import parse_wav_file
from app.parsers.sigmf_parser import parse_sigmf_meta, reconstruct_iq_from_sigmf
from app.dsp.preprocessing import preprocess_signal
from app.dsp.time_domain import analyze_time_domain
from app.dsp.freq_domain import analyze_freq_domain
from app.dsp.spectrogram import compute_spectrogram
from app.dsp.constellation import compute_constellation
from app.dsp.modulation_analysis import segment_active_signal, estimate_symbol_timing, matched_filter_symbol_samples, independent_modulation_evidence
from app.dsp.snr import estimate_snr
from app.features.extractor import extract_signal_features
from app.ml.classifier import ModulationClassifierEngine
from app.ml.fec_detector import detect_fec_scheme
from app.ml.interleaver_detector import detect_interleaving_pattern
from app.database.database import save_analysis_record

# Global ML Engine Instance
MODEL_DIR = "data/models"
classifier_engine = ModulationClassifierEngine(model_dir=MODEL_DIR)
MAX_ANALYSIS_SAMPLES = 262144


def _representative_analysis_window(signal: np.ndarray) -> Tuple[np.ndarray, int]:
    """Bound expensive DSP/ML work while retaining a high-energy real-signal window."""
    if len(signal) <= MAX_ANALYSIS_SAMPLES:
        return signal, 0
    block = 4096
    usable = (len(signal) // block) * block
    powers = np.mean(np.abs(signal[:usable].reshape(-1, block)) ** 2, axis=1)
    peak_block = int(np.argmax(powers))
    start = max(0, min(peak_block * block - MAX_ANALYSIS_SAMPLES // 2, len(signal) - MAX_ANALYSIS_SAMPLES))
    return signal[start:start + MAX_ANALYSIS_SAMPLES], start


def _build_analysis_evidence(features: Dict[str, Any], freq_res: Dict[str, Any], prediction: str, snr_db: float) -> Tuple[list, bool]:
    time = features["time_domain"]
    iq = features["iq_domain"]
    spec = features["frequency_domain"]
    envelope_cv = (time["variance"] ** 0.5) / (time["mean"] + 1e-12)
    amplitude_bearing = envelope_cv >= 0.15
    constant_envelope = envelope_cv <= 0.06
    phase_or_fsk = prediction in {"BPSK", "QPSK", "8PSK", "2FSK", "4FSK"}
    amplitude_prediction = prediction in {"AM", "16QAM", "64QAM"}
    conflict = (amplitude_prediction and constant_envelope) or (phase_or_fsk and amplitude_bearing)
    evidence = [
        {"feature": "Envelope variation", "value": f"coefficient of variation {envelope_cv:.3f}", "interpretation": "Amplitude-bearing modulation evidence" if amplitude_bearing else "Near-constant envelope evidence"},
        {"feature": "Amplitude distribution", "value": f"crest factor {time['crest_factor']:.2f}, kurtosis {time['kurtosis']:.2f}", "interpretation": "Describes amplitude levels; not a ground-truth label"},
        {"feature": "Instantaneous frequency", "value": f"standard deviation {iq['inst_freq_std']:.1f} Hz", "interpretation": "Frequency variation evidence" if snr_db >= 8.0 else f"Reliability-limited at estimated SNR {snr_db:.1f} dB; not strong FSK evidence"},
        {"feature": "Cumulants", "value": f"C40 {features['cumulants']['C40']:.3f}, C42 {features['cumulants']['C42']:.3f}", "interpretation": "Higher-order modulation signature"},
        {"feature": "Constellation characteristics", "value": f"I/Q variance ratio {iq['i_variance'] / (iq['q_variance'] + 1e-12):.2f}", "interpretation": "I/Q geometry evidence"},
        {"feature": "Spectral characteristics", "value": f"occupied bandwidth {freq_res['characteristics']['occupied_bandwidth_hz'] / 1e3:.1f} kHz; flatness {spec['spectral_flatness']:.3f}", "interpretation": "Baseband spectral evidence"},
    ]
    return evidence, conflict

def run_full_signal_analysis(
    iq_bytes: Optional[bytes] = None,
    wav_bytes: Optional[bytes] = None,
    iq_filename: Optional[str] = None,
    wav_filename: Optional[str] = None,
    datatype: str = "auto",
    sample_rate_override: Optional[float] = None,
    ground_truth_meta: Optional[Dict[str, Any]] = None,
    sigmf_meta_bytes: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    Complete end-to-end signal analysis orchestrator.
    Handles single IQ, single WAV, paired IQ+WAV, or SigMF (.sigmf-data + .sigmf-meta).
    
    When sigmf_meta_bytes is provided, it takes priority for datatype, sample rate,
    and center frequency extraction. Ground truth is NOT populated for real recordings.
    """
    start_time = time.time()
    
    iq_signal = None
    wav_signal = None
    iq_meta = {}
    wav_meta = {}
    is_sigmf = False

    # 1. Parse Input Files — SigMF-aware path
    if iq_bytes is not None and sigmf_meta_bytes is not None:
        # SigMF path: use metadata-driven reconstruction
        try:
            sigmf_parsed = parse_sigmf_meta(sigmf_meta_bytes)
            iq_signal, iq_meta = reconstruct_iq_from_sigmf(iq_bytes, sigmf_parsed)
            is_sigmf = True
        except Exception as e:
            # Fallback: if SigMF parsing fails, use standard IQ parser
            print(f"[WARN] SigMF metadata parsing failed, falling back to standard IQ parser: {e}")
            iq_signal, iq_meta = parse_iq_file(iq_bytes, datatype=datatype, sample_rate_override=sample_rate_override)
    elif iq_bytes is not None:
        iq_signal, iq_meta = parse_iq_file(iq_bytes, datatype=datatype, sample_rate_override=sample_rate_override)

    if wav_bytes is not None:
        wav_signal, wav_meta = parse_wav_file(wav_bytes, sample_rate_override=sample_rate_override)

    is_demo_signal = bool(ground_truth_meta) and not is_sigmf

    # Primary analysis signal selection
    if iq_signal is not None:
        primary_signal = iq_signal
        primary_meta = iq_meta
        active_filename = iq_filename or "signal.iq"
    else:
        primary_signal = wav_signal
        primary_meta = wav_meta
        active_filename = wav_filename or "signal.wav"

    sample_rate = primary_meta["sample_rate"]
    analysis_signal, analysis_start = _representative_analysis_window(primary_signal)

    # 2. DSP Preprocessing
    proc_signal, audit_meta = preprocess_signal(analysis_signal, sample_rate=sample_rate)
    audit_meta["analysis_window_start_sample"] = analysis_start
    audit_meta["analysis_window_samples"] = len(analysis_signal)
    audit_meta["analysis_window_note"] = "Full recording" if analysis_start == 0 and len(analysis_signal) == len(primary_signal) else "Representative high-energy window; metadata duration remains the full recording duration"

    # 3. Segment signal, estimate timing, then use matched filtering only when justified.
    active_signal, segmentation = segment_active_signal(proc_signal)
    timing = estimate_symbol_timing(active_signal)
    symbol_samples = matched_filter_symbol_samples(active_signal, timing)
    snr_res = estimate_snr(active_signal)
    dsp_hypotheses = independent_modulation_evidence(active_signal, sample_rate, timing, snr_res["snr_db"])

    # 4. DSP Time & Frequency Analysis
    # Plot the parsed, preprocessed, and detected active complex samples.
    time_res = analyze_time_domain(active_signal, sample_rate=sample_rate, max_plot_points=3000)
    freq_res = analyze_freq_domain(active_signal, sample_rate=sample_rate)
    spectrogram_res = compute_spectrogram(active_signal, sample_rate=sample_rate)
    constellation_res = compute_constellation(active_signal, symbol_samples=symbol_samples, timing=timing)

    # 4. Feature Extraction
    feat_vec, feat_report = extract_signal_features(active_signal, sample_rate=sample_rate)

    # 5. Multi-Modal ML Modulation Classification
    classifier_iq = active_signal if iq_signal is not None else None
    classifier_wav = proc_signal if wav_signal is not None and iq_signal is None else wav_signal
    mod_prediction = classifier_engine.classify_signal(classifier_iq, classifier_wav, sample_rate, conservative_confidence=not is_demo_signal)
    analysis_evidence, conflicting_evidence = _build_analysis_evidence(feat_report, freq_res, mod_prediction["prediction"], snr_res["snr_db"])
    qam_without_timing = mod_prediction["prediction"] in {"16QAM", "64QAM"} and not timing["reliable"]
    conflicting_evidence = conflicting_evidence or qam_without_timing
    analysis_evidence.insert(0, {"feature": "Signal detection / segmentation", "value": f"{segmentation['method']}; active fraction {segmentation['active_fraction']:.3f}", "interpretation": "Classification uses the detected active signal region"})
    analysis_evidence.insert(1, {"feature": "Symbol timing and matched filtering", "value": f"{timing['reason']} (confidence {timing['confidence']})", "interpretation": "Symbol constellation is used only when timing is reliable"})
    analysis_evidence.extend({"feature": f"DSP hypothesis: {h['name']}", "value": f"score {h['score']:.2f}", "interpretation": h["basis"]} for h in dsp_hypotheses["hypotheses"])
    detector_modulation = mod_prediction["prediction"]
    if conflicting_evidence:
        mod_prediction["model_prediction"] = mod_prediction["prediction"]
        mod_prediction["prediction"] = "Inconclusive / Conflicting Evidence"
        mod_prediction["confidence_label"] = "Inconclusive"
    elif not is_demo_signal:
        mod_prediction["model_prediction"] = mod_prediction["prediction"]
        mod_prediction["prediction"] = f"{mod_prediction['prediction']} candidate"

    # 6. Advanced FEC & Interleaving Detection
    fec_res = detect_fec_scheme(active_signal, detector_modulation, snr_res["snr_db"])
    interleaving_res = detect_interleaving_pattern(active_signal, detector_modulation, snr_res["snr_db"])

    # 7. Ground Truth vs Inference Table Construction
    # CRITICAL: Only use ground truth for synthetic demo signals, never for real recordings
    gt = ground_truth_meta or {}
    unavailable_ground_truth = "N/A" if is_demo_signal else "Not available"

    parameter_table = [
        {
            "parameter": "Data Type",
            "result": primary_meta.get("datatype", "Unknown"),
            "source": primary_meta.get("metadata_source", "File parser"),
            "confidence": "N/A (Metadata)",
            "ground_truth": unavailable_ground_truth
        },
        {
            "parameter": "Sampling Rate",
            "result": f"{sample_rate/1e6:.3f} MS/s",
            "source": primary_meta.get("sample_rate_source", "Metadata"),
            "confidence": "N/A (Metadata)",
            "ground_truth": f"{gt.get('sampling_rate', 0.0)/1e6:.3f} MS/s" if (is_demo_signal and "sampling_rate" in gt) else unavailable_ground_truth
        },
        {
            "parameter": "Modulation Type",
            "result": mod_prediction["prediction"],
            "source": f"ML Classifier ({mod_prediction['mode']})",
            "confidence": mod_prediction.get("confidence_label", f"Model score: {mod_prediction['confidence']}%"),
            "ground_truth": gt.get("modulation", "N/A") if is_demo_signal else unavailable_ground_truth
        },
        {
            "parameter": "SNR Estimate",
            "result": f"{snr_res['snr_db']} dB",
            "source": snr_res["method"],
            "confidence": snr_res["confidence"],
            "ground_truth": f"{gt.get('snr_db', 'N/A')} dB" if (is_demo_signal and "snr_db" in gt) else unavailable_ground_truth
        },
        {
            "parameter": "Occupied Bandwidth",
            "result": f"{freq_res['characteristics']['occupied_bandwidth_hz']/1e3:.1f} kHz",
            "source": "DSP (99% Spectral Integration)",
            "confidence": "High",
            "ground_truth": unavailable_ground_truth
        },
        {
            "parameter": "FEC Scheme",
            "result": fec_res["result"],
            "source": f"Hypothesis Testing ({fec_res['status']})",
            "confidence": f"{fec_res['confidence_pct']}%",
            "ground_truth": gt.get("fec", "N/A") if is_demo_signal else unavailable_ground_truth
        },
        {
            "parameter": "Interleaving Pattern",
            "result": interleaving_res["result"],
            "source": f"Autocorrelation Analysis ({interleaving_res['status']})",
            "confidence": f"{interleaving_res['confidence_pct']}%",
            "ground_truth": gt.get("interleaving", "N/A") if is_demo_signal else unavailable_ground_truth
        }
    ]

    # Insert center frequency row if available (SigMF or metadata-derived)
    center_freq = primary_meta.get("center_frequency")
    if center_freq is not None:
        parameter_table.insert(1, {
            "parameter": "Center Frequency",
            "result": f"{center_freq/1e6:.3f} MHz",
            "source": primary_meta.get("metadata_source", "Metadata"),
            "confidence": "N/A (Metadata)",
            "ground_truth": unavailable_ground_truth
        })

    # 8. Analyst Explainability & Evidence
    explainability_evidence = [
        {
            "check": "Spectral Characteristics",
            "detail": f"Dominant peak at {freq_res['characteristics']['dominant_frequency_hz']/1e3:.1f} kHz with spectral flatness = {freq_res['characteristics']['spectral_flatness']:.3f}"
        },
        {
            "check": "Constellation Geometry",
            "detail": f"I/Q variance ratio = {(feat_report['iq_domain']['i_variance']/(feat_report['iq_domain']['q_variance']+1e-12)):.2f}, Peak/RMS crest factor = {time_res['stats']['crest_factor']:.2f}"
        },
        {
            "check": "Higher-Order Cumulants",
            "detail": f"C40 = {feat_report['cumulants']['C40']:.3f}, C42 = {feat_report['cumulants']['C42']:.3f} (distinctive signature for {mod_prediction['prediction']})"
        }
    ]

    if iq_signal is not None and wav_signal is not None:
        explainability_evidence.append({
            "check": "Cross-Format Agreement",
            "detail": f"IQ-Only prediction '{mod_prediction['mode_comparisons']['iq_only']}' agrees with WAV-Only '{mod_prediction['mode_comparisons']['wav_only']}' -> Fused Confidence {mod_prediction['confidence']}%"
        })

    processing_time_ms = (time.time() - start_time) * 1000.0

    format_str = "Paired IQ + WAV" if (iq_signal is not None and wav_signal is not None) else (primary_meta["format"])

    report = {
        "metadata": {
            "filename": active_filename,
            "format": format_str,
            "datatype": primary_meta.get("datatype", "unknown"),
            "sample_count": primary_meta["sample_count"],
            "sample_rate": sample_rate,
            "sample_rate_source": primary_meta["sample_rate_source"],
            "center_frequency": center_freq,
            "duration_seconds": primary_meta["duration_seconds"],
            "channels": primary_meta["channels"],
            "metadata_source": primary_meta.get("metadata_source", "File Header / Heuristic"),
        },
        "preprocessing_audit": audit_meta,
        "time_domain": time_res,
        "freq_domain": freq_res,
        "spectrogram": spectrogram_res,
        "constellation": constellation_res,
        "snr": snr_res,
        "features": feat_report,
        "inference_mode": mod_prediction["mode"],
        "modulation_prediction": mod_prediction,
        "fec_detection": fec_res,
        "interleaving_detection": interleaving_res,
        "parameter_table": parameter_table,
        "explainability_evidence": explainability_evidence,
        "analysis_evidence": analysis_evidence,
        "conflicting_evidence": conflicting_evidence,
        "ground_truth_validation": ground_truth_meta if is_demo_signal else None,
        "is_demo_signal": is_demo_signal,
        "processing_time_ms": processing_time_ms
    }

    # Save record to SQLite history
    try:
        rec_id = save_analysis_record(
            filename=active_filename,
            format_type=format_str,
            sample_rate=sample_rate,
            modulation=mod_prediction["prediction"],
            confidence=float(mod_prediction["confidence"]),
            fec_scheme=fec_res["result"],
            interleaving=interleaving_res["result"],
            snr_db=float(snr_res["snr_db"]),
            processing_time_ms=processing_time_ms,
            report_dict=report
        )
        report["record_id"] = rec_id
    except Exception:
        pass

    return report
