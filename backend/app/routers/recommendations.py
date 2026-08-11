from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Brand, Recommendation, Decision
from ..schemas import RecommendationOut, DecisionIn

router = APIRouter(tags=["Recommendations & Decisions"])

@router.get("/recommendations", response_model=list[RecommendationOut])
def list_recommendations(db: Session = Depends(get_db)):
    recs = db.query(Recommendation).order_by(Recommendation.potential_saving.desc()).all()
    out = []
    for r in recs:
        brand_names = []
        if r.involved_brand_ids:
            ids = [int(x) for x in r.involved_brand_ids.split(",")]
            brand_names = [b.name for b in db.query(Brand).filter(Brand.id.in_(ids)).all()]
        out.append(RecommendationOut(
            id=r.id, product_name=r.product.name,
            recommended_vendor=r.recommended_vendor.name,
            score=r.score, reason=r.reason, risk_level=r.risk_level,
            risk_note=r.risk_note, potential_saving=r.potential_saving,
            confidence=r.confidence, is_cross_brand=r.is_cross_brand,
            involved_brands=brand_names, combined_volume=r.combined_volume,
            created_at=r.created_at,
        ))
    return out


@router.get("/recommendations/cross-brand", response_model=list[RecommendationOut])
def cross_brand_recommendations(db: Session = Depends(get_db)):
    all_recs = list_recommendations(db=db)
    return [r for r in all_recs if r.is_cross_brand]


@router.post("/decisions")
def record_decision(payload: DecisionIn, db: Session = Depends(get_db)):
    rec = db.query(Recommendation).get(payload.recommendation_id)
    if not rec:
        raise HTTPException(404, "Recommendation not found")
    decision = Decision(
        recommendation_id=rec.id, decision=payload.decision,
        approved_by=payload.approved_by, notes=payload.notes,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return {"status": "recorded", "decision_id": decision.id}


@router.get("/decisions")
def list_decisions(db: Session = Depends(get_db)):
    decisions = db.query(Decision).order_by(Decision.timestamp.desc()).all()
    return [
        {
            "id": d.id, "recommendation_id": d.recommendation_id,
            "product": d.recommendation.product.name,
            "decision": d.decision, "approved_by": d.approved_by,
            "notes": d.notes, "timestamp": d.timestamp,
        }
        for d in decisions
    ]
