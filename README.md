# SIGNALFUSION — AI-Driven IQ & WAV Signal Intelligence Platform

**Smart India Hackathon 2026 Problem Statement 26147**  
**Organization:** National Technical Research Organisation (NTRO)  
**Category:** Software | **Theme:** Space Technology  

---

## 1. Project Overview

**SIGNALFUSION** is an end-to-end, deep-tech RF signal intelligence platform designed to ingest raw `.iq` complex binary signals and `.wav` audio/IQ recordings (standalone or paired), execute DSP preprocessing and spectral analysis, extract statistical signal features, estimate core parameters (Sampling Rate, Modulation Type, FEC Scheme, Interleaving Pattern, SNR, Bandwidth), and present analyst-ready insights through an interactive React dashboard.

> **Key Slogan:** *"From raw signal recordings to an interpretable signal profile — automatically."*

---

## 2. Core Features & Capabilities

- **Multi-Format Input Support**: Ingest standalone binary `.iq` files (`complex64`, `complex128`, `int16` interleaved, `float32` interleaved), `.wav` files (stereo I/Q or mono audio), or paired `.iq` + `.wav` recordings.
- **Multi-Modal Feature Fusion**: Processes raw binary I/Q and stereo WAV audio containers simultaneously to compute fused cross-format predictions with side-by-side mode comparisons (IQ-only vs WAV-only vs Fused).
- **Honest Parameter Origin & Fallbacks**: Every parameter displays its exact origin (`File Metadata`, `DSP Integration`, `ML Classifier`, `Hypothesis Testing`) and confidence score. Parameters that cannot be reliably inferred cleanly show `"Insufficient Evidence"` or `"Not Available"`.
- **Ground Truth vs Inference Validation**: For synthetic/demo recordings, an explicit comparison table evaluates blind inferences against ground-truth metadata.
- **DSP Visualization Suite**: Interactive Plotly charts for Time-Domain Waveforms (I, Q, Magnitude, Phase), FFT Spectrum & Welch PSD (99% occupied bandwidth & -3dB bandwidth), STFT Spectrogram Heatmap, and I vs Q Constellation Scatter Diagrams.
- **Advanced Hypothesis Testing**: Structural bit correlation and autocorrelation matrix analysis for candidate Forward Error Correction (FEC) schemes and Interleaving patterns.
- **Report Exporter**: Generate downloadable PDF and JSON signal intelligence reports.
- **SIH Presentation Demo Mode**: 1-click execution of pre-generated test signals (`QPSK`, `BPSK`, `16QAM`, `2FSK`, `Paired IQ + WAV`).

---

## 3. System Architecture & Processing Workflow

```
                        ┌───────────────────────────────┐
                        │        RAW SIGNAL INPUT       │
                        │  (.IQ / .WAV / Paired IQ+WAV) │
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │     FILE PARSERS & AUDIT      │
                        │  (Complex64, Int16, Stereo)   │
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │         DSP PREPROCESSING     │
                        │ (DC Removal, Norm, Lowpass)   │
                        └───────────────┬───────────────┘
                                        │
                        ┌───────────────┴───────────────┐
                        │                               │
                        ▼                               ▼
        ┌───────────────────────────────┐ ┌───────────────────────────────┐
        │       DSP ANALYTICAL ENGINES  │ │   FEATURE EXTRACTION MATRIX   │
        │  Waveform, FFT, PSD, STFT,    │ │ (Time, Spectral, Cumulants    │
        │  Constellation, M2M4 SNR      │ │  C40, C42, I/Q Variance)      │
        └───────────────┬───────────────┘ └───────────────┬───────────────┘
                        │                               │
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │   MULTI-MODAL ML AI ENGINE    │
                        │ (IQ Encoder + WAV Encoder ->  │
                        │  Cross-Format Fusion Layer)   │
                        └───────────────┬───────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ PARAMETER EXTRACTION & REPORT │
                        │ Mod, FEC, Interleaving, SNR,  │
                        │ Evidence, PDF/JSON Export     │
                        └───────────────────────────────┘
```

---

## 4. Parameter Origin & Confidence Matrix

| Parameter | Inferred Result | Source / Method | Confidence | Ground Truth Comparison |
|---|---|---|---|---|
| **Sampling Rate** | `1.000 MS/s` | Metadata / User Override | N/A (Metadata) | Ground Truth Matched |
| **Modulation Type** | `QPSK` | Multi-Modal ML Fusion | `94.2%` | Ground Truth Matched |
| **SNR Estimate** | `15.2 dB` | DSP (M2M4 Moments + PSD) | High | Ground Truth Matched |
| **Occupied Bandwidth**| `240.0 kHz` | DSP (99% Power Integration) | High | N/A |
| **FEC Scheme** | `Convolutional` | Hypothesis Testing | `68.0%` | Candidate Detected |
| **Interleaving** | `16x16 Matrix` | Autocorrelation Periodicity | `62.0%` | Candidate Pattern |

---

## 5. Technology Stack

- **Backend**: Python 3.11/3.12, FastAPI, Uvicorn, NumPy, SciPy, PyTorch, scikit-learn, ReportLab, SQLite3.
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, Plotly.js (`react-plotly.js`).

---

## 6. Quick Start & Execution Commands

### Prerequisites
- Python 3.11+
- Node.js v18+ & npm

### Running Backend (Terminal 1)
```bash
# Navigate to workspace
cd /Users/rohith/Desktop/TestSIH

# Activate Python Virtual Environment
source backend/venv/bin/activate

# Run FastAPI Dev Server (Port 8000)
PYTHONPATH=backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*The backend automatically initializes the SQLite history database and synthesizes demo datasets into `data/synthetic/` on startup.*

### Running Frontend (Terminal 2)
```bash
# Navigate to frontend directory
cd /Users/rohith/Desktop/TestSIH/frontend

# Run Vite Dev Server (Port 5173)
npm run dev
```

Open browser at `http://localhost:5173` to access the platform dashboard!

---

## 7. Running Tests

To run the automated backend unit tests:
```bash
cd /Users/rohith/Desktop/TestSIH
PYTHONPATH=backend backend/venv/bin/pytest backend/tests/test_all.py
```

---

## 8. SIH Presentation Walkthrough

1. Open `http://localhost:5173`.
2. Click **Demo 5 — Paired IQ + WAV** in the top presentation demo bar.
3. Observe automatic loading, stereo WAV parsing, and IQ parsing.
4. View interactive Plotly charts: Waveform, FFT Spectrum & PSD, STFT Spectrogram, and Constellation Diagram.
5. Review the **Parameter Profile Table** with explicit source origins and ground truth comparison.
6. Inspect the **Multi-Modal Feature Fusion View** displaying side-by-side predictions for IQ-only, WAV-only, and Fused modes.
7. Click **Export PDF Report** to download an analyst report.

---

## 9. Genuine Implementation vs Roadmap

### Genuinely Implemented
- Full end-to-end web prototype (FastAPI backend + React Vite frontend).
- IQ binary parsing (`complex64`, `complex128`, `int16`, `float32`) & Stereo WAV parsing.
- Real DSP preprocessing (DC offset removal, peak normalization, lowpass filtering, resampling).
- Real time-domain, frequency-domain, STFT spectrogram, constellation, and M2M4 SNR estimation.
- 20-dimensional feature extraction including 4th & 6th order cumulants ($C_{40}, C_{42}$).
- Multi-modal ML modulation classifier supporting 9 classes (BPSK, QPSK, 8PSK, 2FSK, 4FSK, 16QAM, 64QAM, AM, FM).
- Honest FEC & Interleaving hypothesis testing with `"Insufficient Evidence"` fallbacks.
- PDF and JSON report export.

### Experimental / Future Roadmap
- Blind symbol synchronization using Mueller & Müller clock recovery loops.
- Support for GNU Radio `.sigmf` metadata headers.
- Deep neural network Viterbi decoder integration for blind FEC decoding.
