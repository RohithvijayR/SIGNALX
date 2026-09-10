from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import json

from app.services.analyzer import run_full_signal_analysis

router = APIRouter(prefix="/api", tags=["Analysis"])


def _sigmf_stem(filename: str, suffix: str) -> str:
    """Return a case-insensitive SigMF recording stem for pairing checks."""
    return filename.lower()[:-len(suffix)]

@router.post("/analyze")
async def analyze_signal_endpoint(
    iq_file: Optional[UploadFile] = File(None),
    wav_file: Optional[UploadFile] = File(None),
    sigmf_meta_file: Optional[UploadFile] = File(None),
    datatype: str = Form("auto"),
    sample_rate_override: Optional[float] = Form(None),
    ground_truth_json: Optional[str] = Form(None)
):
    """
    Analyze raw .iq file, .wav file, .sigmf-data file, or paired IQ+WAV files.
    
    When a .sigmf-data file is uploaded as iq_file, an accompanying .sigmf-meta
    file can be uploaded via the sigmf_meta_file parameter. The metadata will be
    used for correct sample reconstruction and parameter extraction.
    """
    if iq_file is None and wav_file is None:
        raise HTTPException(status_code=400, detail="At least one file (.iq or .wav) must be provided.")

    is_sigmf_data = bool(iq_file and iq_file.filename.lower().endswith(".sigmf-data"))
    if is_sigmf_data and sigmf_meta_file is None:
        raise HTTPException(
            status_code=400,
            detail="A .sigmf-data recording requires its matching .sigmf-meta file. Select both SigMF files together."
        )
    if sigmf_meta_file is not None:
        if iq_file is None or not is_sigmf_data:
            raise HTTPException(status_code=400, detail="SigMF metadata must be paired with a .sigmf-data file.")
        if not sigmf_meta_file.filename.lower().endswith(".sigmf-meta"):
            raise HTTPException(status_code=400, detail="The SigMF metadata file must use the .sigmf-meta extension.")
        if _sigmf_stem(iq_file.filename, ".sigmf-data") != _sigmf_stem(sigmf_meta_file.filename, ".sigmf-meta"):
            raise HTTPException(status_code=400, detail="The selected SigMF data and metadata filenames do not match.")

    iq_bytes = await iq_file.read() if iq_file is not None else None
    wav_bytes = await wav_file.read() if wav_file is not None else None
    sigmf_meta_bytes = await sigmf_meta_file.read() if sigmf_meta_file is not None else None

    gt_meta = None
    if ground_truth_json:
        try:
            gt_meta = json.loads(ground_truth_json)
        except Exception:
            pass

    report = run_full_signal_analysis(
        iq_bytes=iq_bytes,
        wav_bytes=wav_bytes,
        iq_filename=iq_file.filename if iq_file else None,
        wav_filename=wav_file.filename if wav_file else None,
        datatype=datatype,
        sample_rate_override=sample_rate_override,
        ground_truth_meta=gt_meta,
        sigmf_meta_bytes=sigmf_meta_bytes,
    )

    return report
