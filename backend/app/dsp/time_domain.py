import numpy as np
from scipy import stats
from typing import Dict, Any, Tuple

def analyze_time_domain(
    signal: np.ndarray,
    sample_rate: float,
    max_plot_points: int = 2000
) -> Dict[str, Any]:
    """
    Computes time-domain statistics and visual waveform series (I, Q, magnitude, phase).
    Downsamples plot points for UI rendering responsiveness while calculating exact stats on full array.
    Guarantees that all returned arrays contain only finite values suitable for JSON serialization.
    """
    # SigMF captures may contain non-finite values.  Never serialize those to
    # JSON/Plotly; retain only actual finite complex samples for visualization.
    finite_mask = np.isfinite(signal.real) & np.isfinite(signal.imag)
    signal = signal[finite_mask]
    n_samples = len(signal)
    if n_samples == 0:
        raise ValueError("No finite complex samples are available for the time-domain plot.")
    duration = n_samples / sample_rate if sample_rate > 0 else 0.0

    # 1. Exact Statistics on full signal
    magnitude = np.abs(signal)
    phase = np.angle(signal)
    i_samples = signal.real
    q_samples = signal.imag

    rms = np.sqrt(np.mean(magnitude**2))
    peak = np.max(magnitude)
    crest_factor = (peak / rms) if rms > 1e-12 else 0.0
    kurtosis = float(stats.kurtosis(magnitude))
    skewness = float(stats.skew(magnitude))
    variance = float(np.var(magnitude))
    mean_mag = float(np.mean(magnitude))

    # 2. Downsampling for interactive Plotly charts
    idx = np.linspace(0, n_samples - 1, min(max_plot_points, n_samples), dtype=np.int64)

    # Convert to native Python lists, explicitly ensuring all values are finite
    # and converting numpy scalars to native Python types for clean JSON serialization
    chart_time = [float(t) for t in (idx / sample_rate)]
    chart_i = [float(v) for v in i_samples[idx]]
    chart_q = [float(v) for v in q_samples[idx]]
    chart_mag = [float(v) for v in magnitude[idx]]
    chart_phase = [float(v) for v in phase[idx]]
    
    # Verify all arrays have the same length and are finite
    min_len = min(len(chart_time), len(chart_i), len(chart_q), len(chart_mag), len(chart_phase))
    
    if min_len == 0:
        raise ValueError("Failed to generate finite waveform samples for time-domain plot.")
    
    # Trim all arrays to minimum length and ensure finiteness
    def ensure_finite_list(arr, length):
        result = []
        for i in range(length):
            v = arr[i]
            if np.isfinite(v):
                result.append(v)
            else:
                result.append(0.0)  # Replace any non-finite value with 0
        return result
    
    chart_time = ensure_finite_list(chart_time, min_len)
    chart_i = ensure_finite_list(chart_i, min_len)
    chart_q = ensure_finite_list(chart_q, min_len)
    chart_mag = ensure_finite_list(chart_mag, min_len)
    chart_phase = ensure_finite_list(chart_phase, min_len)

    return {
        "stats": {
            "mean": mean_mag,
            "variance": variance,
            "rms": float(rms),
            "peak": float(peak),
            "crest_factor": float(crest_factor),
            "kurtosis": kurtosis,
            "skewness": skewness,
            "duration_seconds": duration,
            "sample_count": n_samples
        },
        "chart_data": {
            "time": chart_time,
            "i": chart_i,
            "q": chart_q,
            "magnitude": chart_mag,
            "phase": chart_phase,
            "finite_point_count": len(chart_time)
        }
    }
