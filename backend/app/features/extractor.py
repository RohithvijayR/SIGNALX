import numpy as np
from scipy import stats
from typing import Dict, Any, Tuple

def extract_signal_features(signal: np.ndarray, sample_rate: float) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Extract comprehensive RF signal feature vector & structured report dictionary:
    - Time-Domain Statistics
    - Frequency-Domain & Spectral Statistics
    - IQ Component & Phase Statistics
    - Higher-Order Cumulants (C40, C42, C60)
    """
    n_samples = len(signal)
    if n_samples == 0:
        feature_vec = np.zeros(25, dtype=np.float32)
        return feature_vec, {}

    # 1. Time-Domain Signal Statistics
    i_samples = signal.real
    q_samples = signal.imag
    mag = np.abs(signal)
    phase = np.angle(signal)

    # Instantaneous frequency (phase derivative)
    unwrapped_phase = np.unwrap(phase)
    inst_freq = np.diff(unwrapped_phase) * sample_rate / (2.0 * np.pi)

    i_mean = float(np.mean(i_samples))
    i_var = float(np.var(i_samples))
    q_mean = float(np.mean(q_samples))
    q_var = float(np.var(q_samples))

    mag_mean = float(np.mean(mag))
    mag_var = float(np.var(mag))
    rms = float(np.sqrt(np.mean(mag**2)))
    peak = float(np.max(mag))
    crest_factor = (peak / rms) if rms > 1e-12 else 0.0
    kurtosis = float(stats.kurtosis(mag))
    skewness = float(stats.skew(mag))

    # I/Q Cross-Correlation
    iq_corr = float(np.corrcoef(i_samples, q_samples)[0, 1]) if (i_var > 0 and q_var > 0) else 0.0

    # 2. Spectral Domain Features
    nperseg = min(1024, n_samples)
    fft_vals = np.abs(np.fft.fftshift(np.fft.fft(signal) / n_samples))
    freqs = np.fft.fftshift(np.fft.fftfreq(n_samples, d=1.0/sample_rate))
    
    norm_spectrum = fft_vals / (np.sum(fft_vals) + 1e-12)
    spectral_centroid = float(np.sum(freqs * norm_spectrum))
    spectral_bw = float(np.sqrt(np.sum(((freqs - spectral_centroid)**2) * norm_spectrum)))
    
    pos_spec = fft_vals + 1e-12
    spectral_flatness = float(np.exp(np.mean(np.log(pos_spec))) / np.mean(pos_spec))
    spectral_entropy = float(-np.sum(norm_spectrum * np.log2(norm_spectrum + 1e-12)))

    # 3. Higher-Order Cumulants (Key for Modulation Recognition)
    # Zero-mean normalized signal
    norm_sig = (signal - np.mean(signal)) / (rms + 1e-12)
    
    # Moments M_p,q = E[ s^(p-q) * (s*)^q ]
    m20 = np.mean(norm_sig**2)
    m21 = np.mean(np.abs(norm_sig)**2)  # = 1 by normalization
    m40 = np.mean(norm_sig**4)
    m41 = np.mean((norm_sig**3) * np.conj(norm_sig))
    m42 = np.mean((np.abs(norm_sig)**4))

    # Cumulants C_40, C_42
    c40 = float(np.abs(m40 - 3 * (m20**2)))
    c42 = float(np.abs(m42 - np.abs(m20)**2 - 2 * (m21**2)))

    # 4. Assemble Feature Vector (20 numerical features)
    feature_vec = np.array([
        mag_mean, mag_var, rms, peak, crest_factor, kurtosis, skewness,
        i_mean, i_var, q_mean, q_var, iq_corr,
        float(np.std(inst_freq)) if len(inst_freq) > 0 else 0.0,
        spectral_centroid, spectral_bw, spectral_flatness, spectral_entropy,
        float(np.abs(m20)), c40, c42
    ], dtype=np.float32)

    structured_report = {
        "time_domain": {
            "mean": mag_mean,
            "variance": mag_var,
            "rms": rms,
            "peak": peak,
            "crest_factor": crest_factor,
            "kurtosis": kurtosis,
            "skewness": skewness
        },
        "iq_domain": {
            "i_mean": i_mean,
            "i_variance": i_var,
            "q_mean": q_mean,
            "q_variance": q_var,
            "iq_correlation": iq_corr,
            "inst_freq_std": float(np.std(inst_freq)) if len(inst_freq) > 0 else 0.0
        },
        "frequency_domain": {
            "spectral_centroid_hz": spectral_centroid,
            "spectral_bandwidth_hz": spectral_bw,
            "spectral_flatness": spectral_flatness,
            "spectral_entropy": spectral_entropy
        },
        "cumulants": {
            "C40": c40,
            "C42": c42,
            "M20_abs": float(np.abs(m20))
        }
    }

    return feature_vec, structured_report
