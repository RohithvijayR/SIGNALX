"""
SigMF Metadata Parser
=====================

Parses .sigmf-meta JSON files according to the SigMF specification (v1.x).
Maps SigMF datatype descriptors to NumPy dtypes and provides metadata
for correct binary IQ data reconstruction.

Reference: https://github.com/gnuradio/SigMF/blob/main/sigmf-spec.md
"""

import json
import numpy as np
from typing import Dict, Any, Optional, Tuple

# SigMF datatype string -> (numpy dtype for ONE component, number of components per sample, is_complex)
# Format: {type_prefix}{bit_width}_{endianness}
# type_prefix: c = complex, r = real;  f = float, i = signed int, u = unsigned int
# endianness: le = little-endian, be = big-endian
SIGMF_DTYPE_MAP: Dict[str, Tuple[np.dtype, int, bool]] = {
    # Complex float types (interleaved I, Q as float pairs)
    "cf64_le": (np.dtype("<f8"), 2, True),   # complex128 little-endian
    "cf64_be": (np.dtype(">f8"), 2, True),   # complex128 big-endian
    "cf32_le": (np.dtype("<f4"), 2, True),   # complex64 little-endian (most common)
    "cf32_be": (np.dtype(">f4"), 2, True),   # complex64 big-endian
    "cf16_le": (np.dtype("<f2"), 2, True),   # complex float16 little-endian
    "cf16_be": (np.dtype(">f2"), 2, True),   # complex float16 big-endian

    # Complex integer types (interleaved I, Q as int pairs)
    "ci32_le": (np.dtype("<i4"), 2, True),
    "ci32_be": (np.dtype(">i4"), 2, True),
    "ci16_le": (np.dtype("<i2"), 2, True),
    "ci16_be": (np.dtype(">i2"), 2, True),
    "ci8":     (np.dtype("i1"),  2, True),   # 8-bit has no endianness

    # Complex unsigned integer types
    "cu32_le": (np.dtype("<u4"), 2, True),
    "cu32_be": (np.dtype(">u4"), 2, True),
    "cu16_le": (np.dtype("<u2"), 2, True),
    "cu16_be": (np.dtype(">u2"), 2, True),
    "cu8":     (np.dtype("u1"),  2, True),

    # Real float types
    "rf64_le": (np.dtype("<f8"), 1, False),
    "rf64_be": (np.dtype(">f8"), 1, False),
    "rf32_le": (np.dtype("<f4"), 1, False),
    "rf32_be": (np.dtype(">f4"), 1, False),

    # Real integer types
    "ri32_le": (np.dtype("<i4"), 1, False),
    "ri32_be": (np.dtype(">i4"), 1, False),
    "ri16_le": (np.dtype("<i2"), 1, False),
    "ri16_be": (np.dtype(">i2"), 1, False),
    "ri8":     (np.dtype("i1"),  1, False),
    "ru8":     (np.dtype("u1"),  1, False),
}


def parse_sigmf_meta(meta_bytes: bytes) -> Dict[str, Any]:
    """
    Parse a .sigmf-meta JSON file and extract all relevant fields.
    
    Returns a dictionary with:
      - datatype: SigMF datatype string (e.g. 'cf32_le')
      - sample_rate: float (Hz)
      - center_frequency: float (Hz) or None
      - num_channels: int
      - description: str or None
      - author: str or None
      - version: str or None
      - captures: list of capture segments
      - annotations: list of annotation segments
      - raw_global: full global dict
    """
    try:
        meta = json.loads(meta_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Failed to parse SigMF metadata JSON: {e}")

    global_section = meta.get("global", {})
    captures = meta.get("captures", [])
    annotations = meta.get("annotations", [])

    datatype = global_section.get("core:datatype", None)
    sample_rate = global_section.get("core:sample_rate", None)
    num_channels = global_section.get("core:num_channels", 1)
    description = global_section.get("core:description", None)
    author = global_section.get("core:author", None)
    version = global_section.get("core:version", None)
    recorder = global_section.get("core:recorder", None)
    hw = global_section.get("core:hw", None)

    # A capture frequency applies from that capture's sample start.  This
    # application analyzes the stream from sample zero, so use its first
    # capture and fall back to the global value when absent.
    center_frequency = (
        captures[0].get("core:frequency") if captures else None
    )
    if center_frequency is None:
        center_frequency = global_section.get("core:frequency", None)

    return {
        "datatype": datatype,
        "sample_rate": float(sample_rate) if sample_rate is not None else None,
        "center_frequency": float(center_frequency) if center_frequency is not None else None,
        "num_channels": int(num_channels),
        "description": description,
        "author": author,
        "version": version,
        "recorder": recorder,
        "hw": hw,
        "captures": captures,
        "annotations": annotations,
        "raw_global": global_section,
    }


def reconstruct_iq_from_sigmf(
    data_bytes: bytes,
    sigmf_meta: Dict[str, Any]
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Reconstruct a complex64 NumPy array from raw .sigmf-data bytes
    using parsed SigMF metadata.

    Handles all SigMF datatype strings including:
    - cf32_le (complex float32 LE) - most common for SDR recordings
    - ci16_le (complex int16 LE) - common for RTL-SDR
    - cu8 (complex unsigned int8) - common for RTL-SDR raw captures
    - All other SigMF defined types

    Returns:
        (complex_signal, parse_metadata)
    """
    datatype_str = sigmf_meta.get("datatype")
    sample_rate = sigmf_meta.get("sample_rate")
    center_frequency = sigmf_meta.get("center_frequency")

    if datatype_str is None:
        raise ValueError("SigMF metadata missing 'core:datatype' field.")
    if sigmf_meta.get("num_channels", 1) != 1:
        raise ValueError(
            "Only single-channel SigMF recordings are currently supported."
        )

    datatype_key = datatype_str.lower().strip()
    if datatype_key not in SIGMF_DTYPE_MAP:
        raise ValueError(
            f"Unsupported SigMF datatype: '{datatype_str}'. "
            f"Supported types: {list(SIGMF_DTYPE_MAP.keys())}"
        )

    np_dtype, components_per_sample, is_complex = SIGMF_DTYPE_MAP[datatype_key]
    bytes_per_component = np_dtype.itemsize

    # Read raw components
    raw = np.frombuffer(data_bytes, dtype=np_dtype)

    if is_complex:
        # Interleaved I, Q pairs
        if len(raw) % 2 != 0:
            raw = raw[:len(raw) - 1]
        i_comp = raw[0::2].astype(np.float32)
        q_comp = raw[1::2].astype(np.float32)

        # Normalize integer types to [-1, 1] range
        if np.issubdtype(np_dtype, np.integer):
            if np.issubdtype(np_dtype, np.unsignedinteger):
                # Unsigned: center around 0 (e.g., cu8: 0-255 -> -128..127)
                max_val = float(np.iinfo(np_dtype).max)
                offset = (max_val + 1) / 2.0
                i_comp = (i_comp - offset) / offset
                q_comp = (q_comp - offset) / offset
            else:
                # Signed: normalize by max positive value
                max_val = float(np.iinfo(np_dtype).max)
                i_comp = i_comp / max_val
                q_comp = q_comp / max_val

        complex_signal = (i_comp + 1j * q_comp).astype(np.complex64)
        num_samples = len(complex_signal)
    else:
        # Real-only signal — store as complex with Q=0
        real_data = raw.astype(np.float32)
        if np.issubdtype(np_dtype, np.integer):
            if np.issubdtype(np_dtype, np.unsignedinteger):
                max_val = float(np.iinfo(np_dtype).max)
                offset = (max_val + 1) / 2.0
                real_data = (real_data - offset) / offset
            else:
                max_val = float(np.iinfo(np_dtype).max)
                real_data = real_data / max_val
        complex_signal = (real_data + 0j).astype(np.complex64)
        num_samples = len(complex_signal)

    # Determine effective sample rate
    effective_sample_rate = float(sample_rate) if sample_rate and sample_rate > 0 else 1000000.0
    sr_source = "SigMF Metadata" if (sample_rate and sample_rate > 0) else "Default (1 MS/s — no SigMF sample_rate)"

    duration = num_samples / effective_sample_rate if effective_sample_rate > 0 else 0.0

    parse_metadata = {
        "format": "SigMF",
        "datatype": datatype_str,
        "sigmf_datatype": datatype_str,
        "total_bytes": len(data_bytes),
        "sample_count": num_samples,
        "sample_rate": effective_sample_rate,
        "sample_rate_source": sr_source,
        "center_frequency": center_frequency,
        "duration_seconds": duration,
        "channels": 2 if is_complex else 1,
        "is_complex": is_complex,
        "metadata_source": "SigMF Metadata",
        "sigmf_description": sigmf_meta.get("description"),
        "sigmf_recorder": sigmf_meta.get("recorder"),
        "sigmf_hw": sigmf_meta.get("hw"),
    }

    return complex_signal, parse_metadata
