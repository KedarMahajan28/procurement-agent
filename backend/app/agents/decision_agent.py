"""
Agent 5 — Decision / Recommendation Agent.

Combines the outputs of the Comparison, Bundling, and Risk agents into a
final scored recommendation per product. All scores/savings are computed by
the other (deterministic) agents; this agent's only LLM call is to turn
already-computed numbers into a plain-English explanation. The LLM never
computes a number that ends up in the DB.
"""
from sqlalchemy.orm import Session

from ..llm_client import chat_text
from ..models import Recommendation, Product, Requirement
from .comparison_agent import score_vendors_for_product
from .bundling_agent import find_bundling_opportunities, BundlingOpportunity
from .risk_agent import run_all_risk_checks

EXPLANATION_SYSTEM_PROMPT = """You are a procurement analyst writing a short, clear
explanation for a recommendation that has ALREADY been decided by deterministic
scoring. Do not change or second-guess the numbers given to you — just explain
WHY this vendor scored well, referencing the specific figures provided, in 2-4
sentences. Do not invent any numbers not given to you."""


def _explain(prompt_facts: str) -> str:
    try:
        return chat_text(EXPLANATION_SYSTEM_PROMPT, prompt_facts)
    except Exception as e:  # LLM call is best-effort; never block a recommendation on it
        return f"(explanation unavailable: {e})"


def generate_recommendations(db: Session, persist: bool = True) -> list[dict]:
    db.query(Recommendation).delete()
    risks = run_all_risk_checks(db, persist=persist)
    risks_by_vendor = {}
    for r in risks:
        risks_by_vendor.setdefault(r.vendor_id, []).append(r)

    bundling_opps = find_bundling_opportunities(db)
    bundled_product_ids = {o.product_id: o for o in bundling_opps}

    results = []
    products = db.query(Product).all()
    for product in products:
        scores = score_vendors_for_product(db, product.id)
        if not scores:
            continue
        top = scores[0]

        bundle: BundlingOpportunity | None = bundled_product_ids.get(product.id)

        vendor_risks = risks_by_vendor.get(top.vendor_id, [])
        risk_level = "Low"
        risk_note = None
        if vendor_risks:
            severities = [r.severity for r in vendor_risks]
            risk_level = "High" if "High" in severities else "Medium"
            risk_note = " ".join(r.description for r in vendor_risks[:2])

        if bundle and bundle.best_vendor_id == top.vendor_id:
            potential_saving = bundle.potential_saving
            confidence = 0.85 if not bundle.unlocked_by_bundling else 0.75
            volume = bundle.combined_volume
            is_cross_brand = True
            brand_ids_str = ",".join(str(b) for b in bundle.brand_ids)
            facts = (
                f"Product: {product.name}\n"
                f"Recommended vendor: {top.vendor_name} (score {top.total_score}/100)\n"
                f"Combined demand across brands {', '.join(bundle.brand_names)}: {volume} units\n"
                f"List price: INR {bundle.list_price}, negotiated price: INR {bundle.negotiated_price}\n"
                f"Potential saving: INR {potential_saving:,.0f}\n"
                f"MOQ unlocked only by combining brand volumes: {bundle.unlocked_by_bundling}\n"
                f"Component scores: {top.component_scores}\n"
                f"Risk note: {risk_note or 'none'}"
            )
        else:
            reqs = db.query(Requirement).filter(Requirement.product_id == product.id).all()
            volume = sum(r.quantity for r in reqs) if reqs else top.moq
            # Baseline = most expensive quote (proxy for pre-AI fragmented pricing)
            baseline = max(s.unit_price for s in scores)
            potential_saving = round((baseline - top.unit_price) * volume, 2)
            confidence = 0.7
            is_cross_brand = False
            brand_ids_str = None
            facts = (
                f"Product: {product.name}\n"
                f"Recommended vendor: {top.vendor_name} (score {top.total_score}/100)\n"
                f"Price: INR {top.unit_price}, lead time: {top.lead_time_days} days, "
                f"MOQ: {top.moq}, reliability: {top.reliability_score}\n"
                f"Volume: {volume} units, potential saving vs highest-priced vendor: "
                f"INR {potential_saving:,.0f}\n"
                f"Component scores: {top.component_scores}\n"
                f"Risk note: {risk_note or 'none'}"
            )

        reason = _explain(facts)

        rec = Recommendation(
            product_id=product.id,
            recommended_vendor_id=top.vendor_id,
            score=top.total_score,
            reason=reason,
            risk_level=risk_level,
            risk_note=risk_note,
            potential_saving=max(potential_saving, 0),
            confidence=confidence,
            is_cross_brand=is_cross_brand,
            involved_brand_ids=brand_ids_str,
            combined_volume=volume,
        )
        if persist:
            db.add(rec)
        results.append(rec)

    if persist:
        db.commit()
        for r in results:
            db.refresh(r)

    return results
