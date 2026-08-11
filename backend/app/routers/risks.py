from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RiskAlert

router = APIRouter(tags=["Risks"])

@router.get("/risks")
def list_risks(db: Session = Depends(get_db)):
    alerts = db.query(RiskAlert).all()
    return [
        {
            "id": a.id, "vendor_name": a.vendor.name, "risk_type": a.risk_type,
            "severity": a.severity, "description": a.description,
            "recommendation": a.recommendation_text,
        }
        for a in alerts
    ]
