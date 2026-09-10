"""DSP-first signal segmentation and cautious symbol-timing evidence."""
import numpy as np
from typing import Dict, Any, Tuple


def segment_active_signal(signal: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Find the strongest contiguous active region without assigning a modulation."""
    magnitude = np.abs(signal)
    if len(signal) < 64:
        return signal, {"active_fraction": 1.0, "method": "Capture too short for segmentation"}
    window = min(256, max(16, len(signal) // 2000))
    smooth = np.convolve(magnitude, np.ones(window) / window, mode="same")
    baseline, high = np.percentile(smooth, [50, 95])
    threshold = baseline + 0.25 * max(high - baseline, 1e-12)
    active = smooth >= threshold
    edges = np.flatnonzero(np.diff(np.r_[False, active, False]))
    starts, ends = edges[0::2], edges[1::2]
    if not len(starts):
        return signal, {"active_fraction": 1.0, "method": "No distinct burst detected"}
    best = int(np.argmax(ends - starts))
    start, end = int(starts[best]), int(ends[best])
    if end - start < 128:
        return signal, {"active_fraction": float(np.mean(active)), "method": "Bursts too short; full window retained"}
    return signal[start:end], {
        "active_fraction": float(np.mean(active)),
        "start_sample": start,
        "end_sample": end,
        "method": "Smoothed-envelope burst segmentation",
    }


def estimate_symbol_timing(signal: np.ndarray) -> Dict[str, Any]:
    """Energy-autocorrelation timing estimate; explicitly reports uncertainty."""
    if len(signal) < 512:
        return {"reliable": False, "confidence": 0.0, "samples_per_symbol": None, "reason": "Too few active samples"}
    energy = np.abs(signal) ** 2
    energy = energy - np.mean(energy)
    denom = float(np.dot(energy, energy)) + 1e-12
    max_lag = min(512, len(energy) // 4)
    lags = np.arange(2, max_lag)
    corr = np.array([np.dot(energy[:-lag], energy[lag:]) / denom for lag in lags])
    best = int(np.argmax(corr))
    confidence = float(max(corr[best], 0.0))
    sps = int(lags[best])
    reliable = confidence >= 0.35 and sps >= 2
    return {
        "reliable": reliable,
        "confidence": round(confidence, 3),
        "samples_per_symbol": sps if reliable else None,
        "reason": "Energy autocorrelation timing peak" if reliable else "No reliable symbol-timing peak",
    }


def matched_filter_symbol_samples(signal: np.ndarray, timing: Dict[str, Any], max_points: int = 1500) -> np.ndarray:
    """Use an integrate-and-dump (rectangular matched) filter only after timing is credible."""
    if not timing.get("reliable"):
        return np.array([], dtype=np.complex64)
    sps = int(timing["samples_per_symbol"])
    filtered = np.convolve(signal, np.ones(sps, dtype=np.float32) / sps, mode="same")
    offsets = range(sps)
    offset = max(offsets, key=lambda off: float(np.mean(np.abs(filtered[off::sps]) ** 2)))
    return filtered[offset::sps][:max_points].astype(np.complex64)


def independent_modulation_evidence(signal: np.ndarray, sample_rate: float, timing: Dict[str, Any], snr_db: float) -> Dict[str, Any]:
    magnitude = np.abs(signal)
    envelope_cv = float(np.std(magnitude) / (np.mean(magnitude) + 1e-12))
    inst_freq = np.diff(np.unwrap(np.angle(signal))) * sample_rate / (2 * np.pi)
    freq_std = float(np.std(inst_freq)) if len(inst_freq) else 0.0
    frequency_reliable = snr_db >= 8.0
    fsk_score = min(0.95, freq_std / (sample_rate * 0.08)) if frequency_reliable else min(0.15, freq_std / (sample_rate * 0.08))
    return {
        "envelope_cv": envelope_cv,
        "inst_freq_std_hz": freq_std,
        "hypotheses": [
            {"name": "ASK/AM family", "score": round(min(0.95, envelope_cv / 0.45), 2), "basis": "Envelope variation and amplitude distribution"},
            {"name": "FSK family", "score": round(fsk_score, 2), "basis": "Instantaneous-frequency variation" if frequency_reliable else f"Instantaneous frequency is reliability-limited at estimated SNR {snr_db:.1f} dB"},
            {"name": "QAM/PSK family", "score": round(0.45 if timing.get("reliable") else 0.0, 2), "basis": "Requires reliable timing and symbol-sampled geometry"},
        ],
    }
