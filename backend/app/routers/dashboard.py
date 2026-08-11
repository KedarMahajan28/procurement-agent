from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Brand, Vendor, Product, Recommendation, RiskAlert
from ..schemas import DashboardSummary
from ..agents.bundling_agent import find_bundling_opportunities

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    brands = db.query(Brand).count()
    skus = db.query(Product).count()
    vendors = db.query(Vendor).count()
    savings = db.query(func.sum(Recommendation.potential_saving)).scalar() or 0.0
    open_risks = db.query(RiskAlert).count()
    bundling_opps = len(find_bundling_opportunities(db))
    anomalies = db.query(RiskAlert).filter(RiskAlert.risk_type == "commercial").count()
    return DashboardSummary(
        brands=brands, active_skus=skus, active_vendors=vendors,
        potential_savings=savings, open_risks=open_risks,
        bundling_opportunities=bundling_opps, price_anomalies=anomalies,
    )
