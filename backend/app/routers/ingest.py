import glob
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..agents.graph import run_pipeline

router = APIRouter(prefix="/ingest", tags=["Ingest"])

QUOTES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic", "vendor_quotes")

@router.post("/process-all")
def ingest_process_all(db: Session = Depends(get_db)):
    paths = sorted(glob.glob(os.path.join(QUOTES_DIR, "*.txt")))
    if not paths:
        raise HTTPException(404, "No vendor documents found to process.")
    state = run_pipeline(db, paths)
    return {
        "documents_processed": len(paths),
        "quotes_extracted": len([r for r in state["extraction_results"] if r["quote_id"]]),
        "needs_review": len(state["needs_review"]),
        "recommendations_generated": state["recommendations_count"],
    }


@router.post("/upload")
async def ingest_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a new vendor document (.txt for this prototype) and run it
    through the same extraction pipeline as the seeded documents."""
    os.makedirs(QUOTES_DIR, exist_ok=True)
    dest = os.path.join(QUOTES_DIR, file.filename)
    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)
    state = run_pipeline(db, [dest])
    return {
        "filename": file.filename,
        "quotes_extracted": len([r for r in state["extraction_results"] if r["quote_id"]]),
        "needs_review": len(state["needs_review"]),
    }
