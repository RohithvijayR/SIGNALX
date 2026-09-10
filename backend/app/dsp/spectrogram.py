import numpy as np
from scipy import signal as dsp_signal
from typing import Dict, Any

def compute_spectrogram(
    signal: np.ndarray,
    sample_rate: float,
    nperseg: int = 256,
    noverlap: int = 128,
    nfft: int = 512,
    max_time_bins: int = 200,
    max_freq_bins: int = 200
) -> Dict[str, Any]:
    """
    Computes STFT Spectrogram heatmap matrix.
    Allows dynamic adjustment of window size, overlap, and FFT size.
    Downsamples grid size for responsive web rendering.
    """
    f, t, Zxx = dsp_signal.stft(
        signal,
        fs=sample_rate,
        window='hann',
        nperseg=nperseg,
        noverlap=noverlap,
        nfft=nfft,
        return_onesided=False
    )

    # Shift frequencies to center 0 Hz
    f = np.fft.fftshift(f)
    Zxx = np.fft.fftshift(Zxx, axes=0)
    mag_db = 20 * np.log10(np.abs(Zxx) + 1e-6)

    # Grid Downsampling for interactive UI responsiveness
    freq_step = max(1, len(f) // max_freq_bins)
    time_step = max(1, len(t) // max_time_bins)

    f_sub = f[::freq_step]
    t_sub = t[::time_step]
    mag_sub = mag_db[::freq_step, ::time_step]

    return {
        "params": {
            "nperseg": nperseg,
            "noverlap": noverlap,
            "nfft": nfft,
            "window": "hann"
        },
        "time": t_sub.tolist(),
        "freq": f_sub.tolist(),
        "z_db": mag_sub.tolist()  # 2D array [freq][time]
    }
