import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.analyze import router as analyze_router
from app.api.generate import router as generate_router
from app.api.history import router as history_router
from app.ml.generator import save_synthetic_dataset
from app.database.database import init_db

app = FastAPI(
    title="SIGNALFUSION — AI-Driven IQ & WAV Signal Intelligence Platform",
    description="Automated model for analysis of .IQ and .wav files along with signal parameter extraction for NTRO SIH 2026 Problem Statement 26147.",
    version="1.0.0"
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(analyze_router)
app.include_router(generate_router)
app.include_router(history_router)

# Mount Synthetic Demo Data Directory
DEMO_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic")

@app.on_event("startup")
def startup_event():
    init_db()
    # Pre-generate demo signal dataset if missing
    save_synthetic_dataset(DEMO_DATA_DIR)

@app.get("/")
def root():
    return {
        "platform": "SIGNALFUSION",
        "description": "AI-Driven IQ & WAV Signal Intelligence Platform",
        "organization": "National Technical Research Organisation (NTRO)",
        "sih_problem_statement": "26147",
        "status": "Operational"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
