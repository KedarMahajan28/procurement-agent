"""
Agent 2 — Supplier Comparison Agent.

Scores vendors on more than price alone, per the spec's weighting:
  Price 40% | Lead Time 20% | MOQ 15% | Reliability 15% | Capacity 10%

Pure deterministic scoring — no LLM. Returns a ranked comparison table per
product that the Decision Agent then turns into a recommendation + explanation.
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models import Quote, Product, Requirement

WEIGHTS = {"price": 0.40, "lead_time": 0.20, "moq": 0.15, "reliability": 0.15, "capacity": 0.10}


@dataclass
class VendorScore:
    vendor_id: int
    vendor_name: str
    quote_id: int
    unit_price: float
    lead_time_days: int
    moq: int
    reliability_score: float
    capacity: int
    meets_moq: bool
    meets_capacity: bool
    component_scores: dict
    total_score: float  # 0-100


def score_vendors_for_product(db: Session, product_id: int) -> list[VendorScore]:
    quotes = db.query(Quote).filter(Quote.product_id == product_id).all()
    if not quotes:
        return []

    reqs = db.query(Requirement).filter(Requirement.product_id == product_id).all()
    demand = sum(r.quantity for r in reqs) if reqs else max(q.moq for q in quotes)

    prices = [q.unit_price for q in quotes]
    lead_times = [q.lead_time_days for q in quotes]
    min_price, max_price = min(prices), max(prices)
    min_lead, max_lead = min(lead_times), max(lead_times)

    scores = []
    for q in quotes:
        # Lower price/lead time is better -> invert normalization
        price_score = 100.0 if max_price == min_price else \
            100.0 * (max_price - q.unit_price) / (max_price - min_price)
        lead_score = 100.0 if max_lead == min_lead else \
            100.0 * (max_lead - q.lead_time_days) / (max_lead - min_lead)

        meets_moq = demand >= q.moq
        moq_score = 100.0 if meets_moq else max(0.0, 100.0 * demand / q.moq)

        reliability_score = q.vendor.reliability_score * 100

        meets_capacity = q.vendor.capacity_units_per_month >= demand
        capacity_score = 100.0 if meets_capacity else \
            max(0.0, 100.0 * q.vendor.capacity_units_per_month / demand)

        total = (
            price_score * WEIGHTS["price"]
            + lead_score * WEIGHTS["lead_time"]
            + moq_score * WEIGHTS["moq"]
            + reliability_score * WEIGHTS["reliability"]
            + capacity_score * WEIGHTS["capacity"]
        )

        scores.append(VendorScore(
            vendor_id=q.vendor_id,
            vendor_name=q.vendor.name,
            quote_id=q.id,
            unit_price=q.unit_price,
            lead_time_days=q.lead_time_days,
            moq=q.moq,
            reliability_score=q.vendor.reliability_score,
            capacity=q.vendor.capacity_units_per_month,
            meets_moq=meets_moq,
            meets_capacity=meets_capacity,
            component_scores={
                "price": round(price_score, 1), "lead_time": round(lead_score, 1),
                "moq": round(moq_score, 1), "reliability": round(reliability_score, 1),
                "capacity": round(capacity_score, 1),
            },
            total_score=round(total, 1),
        ))

    scores.sort(key=lambda s: s.total_score, reverse=True)
    return scores
