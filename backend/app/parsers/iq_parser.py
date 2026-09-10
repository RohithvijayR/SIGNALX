import numpy as np
from typing import Tuple, Dict, Any, Optional

def parse_iq_file(
    file_bytes: bytes,
    datatype: str = "auto",
    sample_rate_override: Optional[float] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Parse raw IQ binary data into a complex64 NumPy array.
    Supports datatypes: 'complex64', 'complex128', 'int16', 'float32', 'auto'.
    """
    total_bytes = len(file_bytes)
    detected_type = datatype

    if datatype == "auto":
        # Heuristic auto-detection based on file length
        if total_bytes % 8 == 0:
            detected_type = "complex64"
        elif total_bytes % 4 == 0:
            detected_type = "int16"
        elif total_bytes % 16 == 0:
            detected_type = "complex128"
        else:
            detected_type = "complex64"

    if detected_type == "complex64":
        raw_arr = np.frombuffer(file_bytes, dtype=np.complex64)
    elif detected_type == "complex128":
        raw_arr = np.frombuffer(file_bytes, dtype=np.complex128).astype(np.complex64)
    elif detected_type == "int16":
        # Interleaved int16 I and Q
        raw_int = np.frombuffer(file_bytes, dtype=np.int16)
        if len(raw_int) % 2 != 0:
            raw_int = raw_int[: len(raw_int) - (len(raw_int) % 2)]
        i_comp = raw_int[0::2].astype(np.float32) / 32768.0
        q_comp = raw_int[1::2].astype(np.float32) / 32768.0
        raw_arr = i_comp + 1j * q_comp
    elif detected_type == "float32":
        # Interleaved float32 I and Q
        raw_float = np.frombuffer(file_bytes, dtype=np.float32)
        if len(raw_float) % 2 != 0:
            raw_float = raw_float[: len(raw_float) - (len(raw_float) % 2)]
        i_comp = raw_float[0::2]
        q_comp = raw_float[1::2]
        raw_arr = i_comp + 1j * q_comp
    else:
        # Fallback to complex64
        raw_arr = np.frombuffer(file_bytes, dtype=np.complex64)
        detected_type = "complex64"

    num_samples = len(raw_arr)
    sample_rate = sample_rate_override if sample_rate_override and sample_rate_override > 0 else 1000000.0  # Default 1 MS/s
    duration = num_samples / sample_rate if sample_rate > 0 else 0.0

    metadata = {
        "format": "IQ",
        "datatype": detected_type,
        "total_bytes": total_bytes,
        "sample_count": num_samples,
        "sample_rate": sample_rate,
        "sample_rate_source": "User supplied" if sample_rate_override else "Default / Heuristic (1 MS/s)",
        "duration_seconds": duration,
        "channels": 2,  # I & Q
    }

    return raw_arr.astype(np.complex64), metadata
