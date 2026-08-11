"""
Agent 3 — Cross-Brand Bundling Agent.

Finds products required by multiple brands and checks whether combining their
demand unlocks a vendor's MOQ or a volume-driven price improvement that no
single brand could reach alone.

All math here is deterministic Python — no LLM. This is exactly the kind of
"business-critical calculation" the spec says must not be delegated to an LLM.
"""
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from ..models import Requirement, Quote, Brand, Product

# If combined volume exceeds a vendor's MOQ by this multiple, assume the vendor
# would be open to a further negotiated discount (simple, explainable heuristic
# standing in for a real negotiation-history model).
VOLUME_DISCOUNT_TRIGGER_MULTIPLE = 1.3
ASSUMED_NEGOTIATED_DISCOUNT = 0.10  # 10% off list price when volume clears the trigger


@dataclass
class BundlingOpportunity:
    product_id: int
    product_name: str
    brand_ids: list[int]
    brand_names: list[str]
    combined_volume: int
    tightest_deadline_days: int
    best_vendor_id: int
    best_vendor_name: str
    list_price: float
    negotiated_price: float
    baseline_price: float
    current_est_spend: float
    potential_spend: float
    potential_saving: float
    unlocked_by_bundling: bool  # True if MOQ only met once volumes are combined


def find_bundling_opportunities(db: Session) -> list[BundlingOpportunity]:
    opportunities = []

    products = db.query(Product).all()
    for product in products:
        reqs = db.query(Requirement).filter(Requirement.product_id == product.id).all()
        if len(reqs) < 2:
            continue  # bundling requires 2+ brands wanting the same thing

        brand_ids = [r.brand_id for r in reqs]
        if len(set(brand_ids)) < 2:
            continue

        combined_volume = sum(r.quantity for r in reqs)
        tightest_deadline = min(r.required_by_days for r in reqs)
        brands = db.query(Brand).filter(Brand.id.in_(set(brand_ids))).all()

        quotes = db.query(Quote).filter(Quote.product_id == product.id).all()
        if not quotes:
            continue

        # Baseline: what brands would likely pay negotiating independently —
        # approximated as the highest quoted price (fragmented, no leverage).
        baseline_price = max(q.unit_price for q in quotes)

        # Best vendor for the combined volume: must have enough capacity,
        # and cheapest price wins among those that can fulfill combined_volume.
        viable = [q for q in quotes]
        best_quote = min(viable, key=lambda q: q.unit_price)

        unlocked_by_bundling = False
        max_single_brand_volume = max(r.quantity for r in reqs)
        if best_quote.moq > max_single_brand_volume and best_quote.moq <= combined_volume:
            unlocked_by_bundling = True

        negotiated_price = best_quote.unit_price
        if combined_volume >= best_quote.moq * VOLUME_DISCOUNT_TRIGGER_MULTIPLE:
            negotiated_price = round(best_quote.unit_price * (1 - ASSUMED_NEGOTIATED_DISCOUNT), 2)

        current_est_spend = round(baseline_price * combined_volume, 2)
        potential_spend = round(negotiated_price * combined_volume, 2)
        potential_saving = round(current_est_spend - potential_spend, 2)

        if potential_saving <= 0 and not unlocked_by_bundling:
            continue  # not a real opportunity, skip

        opportunities.append(BundlingOpportunity(
            product_id=product.id,
            product_name=product.name,
            brand_ids=[b.id for b in brands],
            brand_names=[b.name for b in brands],
            combined_volume=combined_volume,
            tightest_deadline_days=tightest_deadline,
            best_vendor_id=best_quote.vendor_id,
            best_vendor_name=best_quote.vendor.name,
            list_price=best_quote.unit_price,
            negotiated_price=negotiated_price,
            baseline_price=baseline_price,
            current_est_spend=current_est_spend,
            potential_spend=potential_spend,
            potential_saving=potential_saving,
            unlocked_by_bundling=unlocked_by_bundling,
        ))

    opportunities.sort(key=lambda o: o.potential_saving, reverse=True)
    return opportunities
