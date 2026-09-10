import numpy as np
from typing import Dict, Any

def compute_constellation(
    signal: np.ndarray,
    max_points: int = 1500,
    symbol_samples: np.ndarray | None = None,
    timing: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Generates constellation point sets for I vs Q scatter plotting.
    Provides raw points, normalized points, and symbol-synchronized point subsets.
    """
    n_samples = len(signal)
    
    # 1. Raw & Normalized Samples
    max_mag = np.max(np.abs(signal))
    norm_signal = (signal / max_mag) if max_mag > 0 else signal

    # 2. Downsampling for raw points
    step = max(1, n_samples // max_points)
    raw_sub = signal[::step]
    norm_sub = norm_signal[::step]

    # Symbol points are supplied only by a timing-validated synchronizer.
    symbol_sub = symbol_samples if symbol_samples is not None else np.array([], dtype=np.complex64)

    return {
        "raw": {
            "i": raw_sub.real.tolist(),
            "q": raw_sub.imag.tolist()
        },
        "normalized": {
            "i": norm_sub.real.tolist(),
            "q": norm_sub.imag.tolist()
        },
        "symbol_sampled": {
            "i": symbol_sub.real.tolist(),
            "q": symbol_sub.imag.tolist()
        },
        "total_points": len(raw_sub)
        ,"timing": timing or {"reliable": False, "reason": "No timing estimate"}
    }
