import numpy as np
from scipy import signal as dsp_signal
from scipy import stats
from typing import Dict, Any

def analyze_freq_domain(
    signal: np.ndarray,
    sample_rate: float,
    max_plot_points: int = 1000
) -> Dict[str, Any]:
    """
    FFT-based frequency domain analysis, PSD calculation, occupied bandwidth estimation,
    and spectral statistical feature extraction.
    """
    n_samples = len(signal)
    
    # 1. FFT Spectrum
    fft_vals = np.fft.fftshift(np.fft.fft(signal) / n_samples)
    freqs = np.fft.fftshift(np.fft.fftfreq(n_samples, d=1.0/sample_rate))
    fft_mag_db = 20 * np.log10(np.abs(fft_vals) + 1e-12)

    # 2. Welch PSD
    nperseg = min(1024, n_samples)
    psd_freqs, psd_vals = dsp_signal.welch(signal, fs=sample_rate, nperseg=nperseg, return_onesided=False)
    psd_freqs = np.fft.fftshift(psd_freqs)
    psd_vals = np.fft.fftshift(psd_vals)
    psd_db = 10 * np.log10(psd_vals + 1e-12)

    # 3. Dominant Frequency & Peaks
    peak_idx = np.argmax(psd_vals)
    dominant_freq = float(psd_freqs[peak_idx])

    # 4. Occupied Bandwidth (99% power integration)
    total_power = np.sum(psd_vals)
    if total_power > 0:
        cum_power = np.cumsum(psd_vals) / total_power
        low_idx = np.searchsorted(cum_power, 0.005)
        high_idx = np.searchsorted(cum_power, 0.995)
        occupied_bw = float(abs(psd_freqs[high_idx] - psd_freqs[low_idx]))
    else:
        occupied_bw = 0.0

    # 5. -3dB Bandwidth
    max_psd = np.max(psd_vals)
    half_power_mask = psd_vals >= (max_psd * 0.5)
    if np.any(half_power_mask):
        half_power_freqs = psd_freqs[half_power_mask]
        bw_3db = float(np.max(half_power_freqs) - np.min(half_power_freqs))
    else:
        bw_3db = 0.0

    # 6. Spectral Features (Centroid, Flatness, Rolloff, Entropy)
    pos_psd = np.abs(psd_vals) + 1e-12
    norm_psd = pos_psd / np.sum(pos_psd)
    
    # Spectral Centroid
    spectral_centroid = float(np.sum(psd_freqs * norm_psd))
    
    # Spectral Bandwidth
    spectral_bw = float(np.sqrt(np.sum(((psd_freqs - spectral_centroid)**2) * norm_psd)))
    
    # Spectral Flatness (Geometric Mean / Arithmetic Mean)
    geom_mean = np.exp(np.mean(np.log(pos_psd)))
    arith_mean = np.mean(pos_psd)
    spectral_flatness = float(geom_mean / arith_mean) if arith_mean > 0 else 0.0
    
    # Spectral Entropy
    spectral_entropy = float(-np.sum(norm_psd * np.log2(norm_psd + 1e-12)))

    # 7. Chart Downsampling
    step_fft = max(1, len(freqs) // max_plot_points)
    idx_fft = np.arange(0, len(freqs), step_fft)
    
    step_psd = max(1, len(psd_freqs) // max_plot_points)
    idx_psd = np.arange(0, len(psd_freqs), step_psd)

    return {
        "characteristics": {
            "dominant_frequency_hz": dominant_freq,
            "occupied_bandwidth_hz": occupied_bw,
            "bandwidth_3db_hz": bw_3db,
            "spectral_centroid_hz": spectral_centroid,
            "spectral_bandwidth_hz": spectral_bw,
            "spectral_flatness": spectral_flatness,
            "spectral_entropy": spectral_entropy,
            "frequency_label": "Baseband Frequency (Hz)"
        },
        "chart_data": {
            "fft_freqs": freqs[idx_fft].tolist(),
            "fft_mag_db": fft_mag_db[idx_fft].tolist(),
            "psd_freqs": psd_freqs[idx_psd].tolist(),
            "psd_db": psd_db[idx_psd].tolist()
        }
    }
