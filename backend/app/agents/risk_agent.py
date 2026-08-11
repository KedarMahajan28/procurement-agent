"""
Agent 4 — Supplier Risk Agent.

Flags three categories of risk, all via deterministic rules over structured
data (no LLM needed for detection — only used later if we want a human-readable
narrative, which the Decision Agent handles per-recommendation instead).

  operational        - vendor lead time exceeds a brand's required delivery window
  commercial         - a vendor's quote is a significant price outlier vs the
                        market average for that product
  portfolio_dependency - a vendor supplies a large share of volume across
                        multiple brands for a product category (concentration risk)
"""
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models import Requirement, Quote, Vendor, Product, RiskAlert

PRICE_ANOMALY_THRESHOLD = 0.10       # 10% above market average for that product
PORTFOLIO_DEPENDENCY_THRESHOLD = 0.50  # vendor supplies >=50% of a category's combined volume


@dataclass
class Risk:
    vendor_id: int
    vendor_name: str
    risk_type: str
    severity: str
    description: str
    recommendation_text: str


def detect_operational_risks(db: Session) -> list[Risk]:
    risks = []
    for req in db.query(Requirement).all():
        quotes = db.query(Quote).filter(Quote.product_id == req.product_id).all()
        for q in quotes:
            if q.lead_time_days > req.required_by_days:
                gap = q.lead_time_days - req.required_by_days
                severity = "High" if gap > 10 else "Medium"
                risks.append(Risk(
                    vendor_id=q.vendor_id,
                    vendor_name=q.vendor.name,
                    risk_type="operational",
                    severity=severity,
                    description=(
                        f"{q.vendor.name}'s lead time for {q.product.name} is "
                        f"{q.lead_time_days} days, but {req.brand.name} needs delivery "
                        f"within {req.required_by_days} days ({gap}-day gap)."
                    ),
                    recommendation_text=(
                        f"Negotiate an expedited {req.required_by_days}-day delivery "
                        f"commitment with {q.vendor.name}, or source from an alternate vendor."
                    ),
                ))
    return risks


def detect_price_anomalies(db: Session) -> list[Risk]:
    risks = []
    products = db.query(Product).all()
    for product in products:
        quotes = db.query(Quote).filter(Quote.product_id == product.id).all()
        if len(quotes) < 2:
            continue
        avg_price = sum(q.unit_price for q in quotes) / len(quotes)
        for q in quotes:
            deviation = (q.unit_price - avg_price) / avg_price
            if deviation > PRICE_ANOMALY_THRESHOLD:
                risks.append(Risk(
                    vendor_id=q.vendor_id,
                    vendor_name=q.vendor.name,
                    risk_type="commercial",
                    severity="Medium" if deviation < 0.30 else "High",
                    description=(
                        f"{q.vendor.name}'s quote for {product.name} (INR {q.unit_price}) is "
                        f"{deviation*100:.0f}% above the market average of INR {avg_price:.2f} "
                        f"across quoted vendors."
                    ),
                    recommendation_text=(
                        f"Request justification from {q.vendor.name} or compare against "
                        f"alternate vendors before committing."
                    ),
                ))
    return risks


def detect_portfolio_dependency(db: Session) -> list[Risk]:
    """For each product *category*, checks whether one vendor's cheapest-quote
    volume share across brands needing that category crosses the threshold."""
    risks = []
    products = db.query(Product).all()
    by_category = defaultdict(list)
    for p in products:
        by_category[p.category].append(p)

    for category, cat_products in by_category.items():
        vendor_volume = defaultdict(int)
        total_volume = 0
        for product in cat_products:
            reqs = db.query(Requirement).filter(Requirement.product_id == product.id).all()
            quotes = db.query(Quote).filter(Quote.product_id == product.id).all()
            if not reqs or not quotes:
                continue
            cheapest = min(quotes, key=lambda q: q.unit_price)
            vol = sum(r.quantity for r in reqs)
            vendor_volume[cheapest.vendor_id] += vol
            total_volume += vol

        if total_volume == 0:
            continue

        for vendor_id, vol in vendor_volume.items():
            share = vol / total_volume
            if share >= PORTFOLIO_DEPENDENCY_THRESHOLD:
                vendor = db.query(Vendor).get(vendor_id)
                risks.append(Risk(
                    vendor_id=vendor_id,
                    vendor_name=vendor.name,
                    risk_type="portfolio_dependency",
                    severity="High" if share > 0.65 else "Medium",
                    description=(
                        f"{vendor.name} would supply {share*100:.0f}% of combined "
                        f"'{category}' volume if recommendations are followed as-is — "
                        f"a concentration risk if this vendor has a disruption."
                    ),
                    recommendation_text=(
                        f"Qualify a second vendor for {category} to reduce single-vendor "
                        f"dependency, even at a modest price premium."
                    ),
                ))
    return risks


def run_all_risk_checks(db: Session, persist: bool = True) -> list[Risk]:
    risks = detect_operational_risks(db) + detect_price_anomalies(db) + detect_portfolio_dependency(db)
    if persist:
        db.query(RiskAlert).delete()
        for r in risks:
            db.add(RiskAlert(
                vendor_id=r.vendor_id,
                risk_type=r.risk_type,
                severity=r.severity,
                description=r.description,
                recommendation_text=r.recommendation_text,
            ))
        db.commit()
    return risks
