from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.ml.generator import generate_synthetic_rf_signal
from app.services.analyzer import run_full_signal_analysis, classifier_engine
from scipy.io import wavfile
import numpy as np

router = APIRouter(prefix="/api", tags=["Generator & Training"])

class SyntheticGenRequest(BaseModel):
    modulation: str = "QPSK"
    snr_db: float = 15.0
    fec_scheme: str = "Convolutional"
    interleaving_pattern: str = "16x16 Matrix"
    sample_rate: float = 1000000.0
    num_samples: int = 16384

@router.post("/generate")
async def generate_and_analyze_synthetic_signal(req: SyntheticGenRequest):
    """
    Generate synthetic signal with ground-truth metadata and run immediate analysis.
    """
    sig, gt = generate_synthetic_rf_signal(
        modulation=req.modulation,
        num_samples=req.num_samples,
        sample_rate=req.sample_rate,
        snr_db=req.snr_db,
        fec_scheme=req.fec_scheme,
        interleaving_pattern=req.interleaving_pattern
    )

    iq_bytes = sig.tobytes()

    # Create corresponding stereo WAV bytes
    i_int16 = np.clip(sig.real * 32767.0, -32768, 32767).astype(np.int16)
    q_int16 = np.clip(sig.imag * 32767.0, -32768, 32767).astype(np.int16)
    stereo_int16 = np.column_stack((i_int16, q_int16))
    
    import io
    wav_io = io.BytesIO()
    wavfile.write(wav_io, int(req.sample_rate), stereo_int16)
    wav_bytes = wav_io.getvalue()

    report = run_full_signal_analysis(
        iq_bytes=iq_bytes,
        wav_bytes=wav_bytes,
        iq_filename=f"synthetic_{req.modulation.lower()}.iq",
        wav_filename=f"synthetic_{req.modulation.lower()}.wav",
        ground_truth_meta=gt
    )

    return report

@router.post("/train")
async def train_models_endpoint():
    """
    Trigger model training on synthetic signal dataset.
    """
    classifier_engine.train_baseline_models(n_samples_per_class=60)
    return {"status": "success", "message": "ML Modulation Classifiers successfully retrained."}
