import io
import wave
import numpy as np
from scipy.io import wavfile
from typing import Tuple, Dict, Any, Optional

def parse_wav_file(
    file_bytes: bytes,
    sample_rate_override: Optional[float] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Parse WAV audio or stereo IQ-WAV recording.
    If 2-channel (stereo), treats Channel 1 as In-phase (I) and Channel 2 as Quadrature (Q).
    Returns complex64 array (or real float32 if 1-channel) and metadata dict.
    """
    bytes_io = io.BytesIO(file_bytes)
    sample_rate, data = wavfile.read(bytes_io)

    # Normalize integer data to [-1.0, 1.0]
    if data.dtype == np.int16:
        float_data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        float_data = data.astype(np.float32) / 2147483648.0
    elif data.dtype == np.uint8:
        float_data = (data.astype(np.float32) - 128.0) / 128.0
    else:
        float_data = data.astype(np.float32)

    channels = 1
    if float_data.ndim > 1:
        channels = float_data.shape[1]

    effective_sr = float(sample_rate_override) if sample_rate_override and sample_rate_override > 0 else float(sample_rate)

    if channels >= 2:
        # Stereo: Ch1 = I, Ch2 = Q
        i_channel = float_data[:, 0]
        q_channel = float_data[:, 1]
        complex_signal = i_channel + 1j * q_channel
    else:
        # Mono: Hilbert transform or real signal representation
        # Real to analytical complex signal using basic quadrature or zero Q
        real_channel = float_data.flatten()
        complex_signal = real_channel + 1j * np.zeros_like(real_channel)

    num_samples = len(complex_signal)
    duration = num_samples / effective_sr if effective_sr > 0 else 0.0

    metadata = {
        "format": "WAV",
        "datatype": str(data.dtype),
        "total_bytes": len(file_bytes),
        "sample_count": num_samples,
        "sample_rate": effective_sr,
        "sample_rate_source": "User supplied" if sample_rate_override else "File metadata (RIFF header)",
        "duration_seconds": duration,
        "channels": channels,
        "is_stereo_iq": (channels >= 2)
    }

    return complex_signal.astype(np.complex64), metadata
