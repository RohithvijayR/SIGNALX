import numpy as np
from typing import Dict, Any

def estimate_snr(signal: np.ndarray) -> Dict[str, Any]:
    """
    Estimates Signal-to-Noise Ratio (SNR) in dB using M2M4 moments estimator
    and spectral noise-floor power integration.
    """
    mag_sq = np.abs(signal)**2
    
    # 1. M2M4 Moments Estimator
    m2 = np.mean(mag_sq)
    m4 = np.mean(mag_sq**2)
    
    # Under M2M4 derivation:
    # m2 = S + N
    # m4 = (1 + k_s)*S^2 + 4*S*N + 2*N^2 (for complex AWGN)
    # Simplified M2M4 solution for constant envelope / PSK signals:
    denom = 2 * (m2**2) - m4
    if denom > 0:
        s_est = np.sqrt(denom)
        n_est = m2 - s_est
        if n_est > 0:
            snr_m2m4 = float(10 * np.log10(s_est / n_est))
        else:
            snr_m2m4 = 30.0  # Cap clean signals
    else:
        snr_m2m4 = 0.0

    # 2. Spectral Noise Floor Estimator (Lower 25% quantile of PSD)
    psd_vals = np.abs(np.fft.fft(signal))**2
    noise_power_est = np.median(np.sort(psd_vals)[: len(psd_vals) // 4])
    total_power = np.mean(psd_vals)
    signal_power_est = max(1e-12, total_power - noise_power_est)
    snr_spectral = float(10 * np.log10(signal_power_est / (noise_power_est + 1e-12)))

    # Final combined SNR estimate
    snr_db = float(np.clip(0.6 * snr_m2m4 + 0.4 * snr_spectral, -5.0, 45.0))

    confidence = "High" if snr_db > 10 else ("Medium" if snr_db > 3 else "Low")

    return {
        "snr_db": round(snr_db, 2),
        "snr_m2m4_db": round(snr_m2m4, 2),
        "snr_spectral_db": round(snr_spectral, 2),
        "confidence": confidence,
        "method": "DSP (M2M4 Moments + Spectral Noise-Floor)"
    }
