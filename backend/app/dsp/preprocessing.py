import numpy as np
from scipy import signal as dsp_signal
from typing import Tuple, Dict, Any, List

def preprocess_signal(
    signal: np.ndarray,
    sample_rate: float,
    remove_dc: bool = True,
    normalize: bool = True,
    cutoff_freq: float = 0.0,  # 0 means no filter
    target_sample_rate: float = 0.0  # 0 means no resampling
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Real preprocessing pipeline for IQ/WAV complex signals.
    - DC offset removal
    - Amplitude normalization
    - Optional Butterworth lowpass/bandpass filtering
    - Optional resampling
    - Transformation audit log
    """
    proc_signal = signal.copy()
    actions_taken: List[str] = []

    # 1. Check & Remove DC Offset
    if remove_dc:
        dc_val = np.mean(proc_signal)
        proc_signal = proc_signal - dc_val
        actions_taken.append(f"Removed DC offset (I_mean={dc_val.real:.4e}, Q_mean={dc_val.imag:.4e})")

    # 2. Filtering (if specified)
    if cutoff_freq > 0 and cutoff_freq < (sample_rate / 2.0):
        nyquist = sample_rate / 2.0
        norm_cutoff = cutoff_freq / nyquist
        b, a = dsp_signal.butter(5, norm_cutoff, btype='low')
        
        # Apply filter to I and Q independently
        i_filt = dsp_signal.filtfilt(b, a, proc_signal.real)
        q_filt = dsp_signal.filtfilt(b, a, proc_signal.imag)
        proc_signal = i_filt + 1j * q_filt
        actions_taken.append(f"Applied 5th order Butterworth lowpass filter (Cutoff: {cutoff_freq/1e3:.1f} kHz)")

    # 3. Resampling (if specified)
    effective_sr = sample_rate
    if target_sample_rate > 0 and target_sample_rate != sample_rate:
        num_target = int(len(proc_signal) * target_sample_rate / sample_rate)
        if num_target > 0:
            proc_signal = dsp_signal.resample(proc_signal, num_target)
            actions_taken.append(f"Resampled signal from {sample_rate/1e6:.2f} MS/s to {target_sample_rate/1e6:.2f} MS/s")
            effective_sr = target_sample_rate

    # 4. Amplitude Normalization
    if normalize:
        max_mag = np.max(np.abs(proc_signal))
        if max_mag > 0:
            proc_signal = proc_signal / max_mag
            actions_taken.append(f"Normalized peak amplitude to 1.0 (Scaling factor: {1.0/max_mag:.4f})")

    # Summary Statistics post-preprocessing
    power = np.mean(np.abs(proc_signal)**2)
    peak_mag = np.max(np.abs(proc_signal))
    rms_mag = np.sqrt(power)

    audit_meta = {
        "actions": actions_taken,
        "original_samples": len(signal),
        "preprocessed_samples": len(proc_signal),
        "effective_sample_rate": effective_sr,
        "peak_magnitude": float(peak_mag),
        "rms_magnitude": float(rms_mag),
        "signal_power_db": float(10 * np.log10(power + 1e-12))
    }

    return proc_signal.astype(np.complex64), audit_meta
