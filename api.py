"""
api.py
======
Thin HTTP layer for the ABG Clinical Decision Support engine.

It does TWO simple jobs and NOTHING clinical:
  1. Serves the web page (the UI) at  /
  2. Exposes  POST /analyze  which forwards inputs to abg_engine.analyze_abg()

All clinical interpretation stays inside the tested engine (v1.0.0, 31 tests).
There is NO clinical logic in this file.

Run (one command):
    uvicorn api:app --host 0.0.0.0 --port 8000
"""

from typing import Optional
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Engine imported untouched. If this import fails, an engine file is missing.
from abg_engine import analyze_abg

app = FastAPI(title="ABG Clinical Decision Support", version="1.0.0")

STATIC_DIR = Path(__file__).parent / "static"


class ABGRequest(BaseModel):
    """Mirrors analyze_abg() exactly - field names must match."""
    sample_type: str = Field(..., description="ABG | VBG | CBG")
    clinical_context: str = Field(..., description="General | ARDS | COPD")
    ph: float
    pco2: float
    hco3: float
    po2: float
    na: float
    cl: float
    on_vent: str = "no"
    mode: str = ""
    rr: Optional[float] = None
    tv: Optional[float] = None
    peep: Optional[float] = None
    fio2: Optional[float] = None
    albumin: Optional[float] = None
    height_cm: Optional[float] = None
    sex: str = "male"
    resp_chronicity: str = "unknown"


@app.get("/health")
def health():
    return {"status": "ok", "engine": "v1.0.0"}


@app.post("/analyze")
def analyze(req: ABGRequest) -> dict:
    """Forward to the engine and return its dict verbatim. No clinical logic here."""
    return analyze_abg(
        sample_type=req.sample_type, clinical_context=req.clinical_context,
        ph=req.ph, pco2=req.pco2, hco3=req.hco3, po2=req.po2, na=req.na, cl=req.cl,
        on_vent=req.on_vent, mode=req.mode, rr=req.rr, tv=req.tv, peep=req.peep,
        fio2=req.fio2, albumin=req.albumin, height_cm=req.height_cm,
        sex=req.sex, resp_chronicity=req.resp_chronicity,
    )


@app.get("/")
def home():
    """Serve the web UI."""
    return FileResponse(str(STATIC_DIR / "index.html"))
