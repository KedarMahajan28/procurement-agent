from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Product
from ..agents.comparison_agent import score_vendors_for_product

router = APIRouter(tags=["Vendors & Products"])

@router.get("/vendors/comparison/{product_id}")
def vendor_comparison(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    scores = score_vendors_for_product(db, product_id)
    return {
        "product": product.name,
        "vendors": [
            {
                "vendor_name": s.vendor_name, "unit_price": s.unit_price,
                "moq": s.moq, "lead_time_days": s.lead_time_days,
                "meets_moq": s.meets_moq, "total_score": s.total_score,
                "component_scores": s.component_scores,
            }
            for s in scores
        ],
    }

@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    return [{"id": p.id, "name": p.name, "sku": p.sku, "category": p.category}
            for p in db.query(Product).all()]
