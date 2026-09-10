import pytest
import numpy as np
import json
from app.parsers.iq_parser import parse_iq_file
from app.parsers.wav_parser import parse_wav_file
from app.dsp.preprocessing import preprocess_signal
from app.dsp.time_domain import analyze_time_domain
from app.dsp.freq_domain import analyze_freq_domain
from app.features.extractor import extract_signal_features
from app.ml.generator import generate_synthetic_rf_signal
from app.parsers.sigmf_parser import parse_sigmf_meta, reconstruct_iq_from_sigmf
from app.services.analyzer import run_full_signal_analysis

def test_iq_parser():
    # Create fake complex64 bytes
    iq_data = (np.ones(100, dtype=np.float32) + 1j * np.ones(100, dtype=np.float32)).astype(np.complex64)
    raw_bytes = iq_data.tobytes()
    arr, meta = parse_iq_file(raw_bytes, datatype="complex64")
    assert len(arr) == 100
    assert meta["format"] == "IQ"

def test_dsp_pipeline():
    sig, _ = generate_synthetic_rf_signal(modulation="QPSK", num_samples=1000)
    proc_sig, audit = preprocess_signal(sig, sample_rate=1e6)
    assert len(proc_sig) == 1000
    assert "actions" in audit

    t_res = analyze_time_domain(proc_sig, sample_rate=1e6)
    assert "stats" in t_res
    assert t_res["stats"]["sample_count"] == 1000

    f_res = analyze_freq_domain(proc_sig, sample_rate=1e6)
    assert "characteristics" in f_res
    assert f_res["characteristics"]["occupied_bandwidth_hz"] >= 0

def test_feature_extraction():
    sig, _ = generate_synthetic_rf_signal(modulation="16QAM", num_samples=2000)
    vec, report = extract_signal_features(sig, 1e6)
    assert len(vec) == 20
    assert "cumulants" in report
    assert "C40" in report["cumulants"]


def test_sigmf_cf32_le_uses_metadata_and_never_exposes_ground_truth():
    samples = np.array([1.25 - 2.5j, -3.0 + 4.75j], dtype=np.complex64)
    # Explicit little-endian float32 I/Q components, as specified by cf32_le.
    components = np.empty(samples.size * 2, dtype="<f4")
    components[0::2] = samples.real
    components[1::2] = samples.imag
    meta_bytes = json.dumps({
        "global": {"core:datatype": "cf32_le", "core:num_channels": 1, "core:sample_rate": 2400000},
        "captures": [{"core:sample_start": 0, "core:frequency": 160787050}],
    }).encode()

    reconstructed, metadata = reconstruct_iq_from_sigmf(components.tobytes(), parse_sigmf_meta(meta_bytes))
    np.testing.assert_allclose(reconstructed, samples)
    assert metadata["sample_rate"] == 2400000
    assert metadata["center_frequency"] == 160787050
    assert metadata["datatype"] == "cf32_le"

    analysis_samples = np.exp(1j * np.linspace(0, 40 * np.pi, 2048)).astype(np.complex64)
    analysis_components = np.empty(analysis_samples.size * 2, dtype="<f4")
    analysis_components[0::2] = analysis_samples.real
    analysis_components[1::2] = analysis_samples.imag
    report = run_full_signal_analysis(
        iq_bytes=analysis_components.tobytes(),
        iq_filename="pulsed_ASK.sigmf-data",
        sigmf_meta_bytes=meta_bytes,
        ground_truth_meta={"modulation": "Demo-only value"},
    )
    assert report["metadata"]["sample_rate"] == 2400000
    assert report["metadata"]["center_frequency"] == 160787050
    assert report["metadata"]["metadata_source"] == "SigMF Metadata"
    assert report["is_demo_signal"] is False
    assert report["ground_truth_validation"] is None
    assert all(row["ground_truth"] == "Not available" for row in report["parameter_table"])
