"""
Agent 1 — Quote Extraction Agent.

Input: raw unstructured vendor document text (parsed PDF/email/chat).
Output: structured quote fields + a confidence score.

Per the engineering principle in the spec: the LLM only does the unstructured
extraction. Matching the extracted vendor/product names to canonical DB rows
(normalization) is deterministic string matching, not LLM-driven, so it's
reliable and auditable.
"""
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from ..llm_client import chat_json
from ..models import Vendor, Product, Quote

EXTRACTION_SYSTEM_PROMPT = """You are a procurement document extraction engine.
You will be given raw, unstructured text from a vendor quotation (email, PDF, or chat).
Extract the following fields and return ONLY a JSON object, no other text:

{
  "vendor_name": string,
  "product_name": string,
  "product_sku": string or null,
  "unit_price": number,
  "currency": string (e.g. "INR"),
  "moq": integer,
  "lead_time_days": integer,
  "payment_terms": string or null,
  "valid_until": string or null (ISO date if present),
  "confidence": number between 0 and 1 (how confident you are in this extraction;
                lower it if any field was ambiguous or missing and you inferred it)
}

Extract only what is stated or clearly implied in the text. Do not invent values."""


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _match_vendor(db: Session, name: str) -> Vendor | None:
    vendors = db.query(Vendor).all()
    best, best_score = None, 0.0
    for v in vendors:
        s = _similarity(v.name, name)
        if s > best_score:
            best, best_score = v, s
    return best if best_score > 0.6 else None


def _match_product(db: Session, sku: str | None, name: str) -> Product | None:
    if sku:
        p = db.query(Product).filter(Product.sku == sku).first()
        if p:
            return p
    products = db.query(Product).all()
    best, best_score = None, 0.0
    for p in products:
        s = _similarity(p.name, name)
        if s > best_score:
            best, best_score = p, s
    return best if best_score > 0.55 else None


def extract_quote_from_text(raw_text: str, source_filename: str) -> dict:
    """Pure extraction step — no DB access. Returns the LLM's structured read
    of the document plus its self-reported confidence."""
    extracted = chat_json(EXTRACTION_SYSTEM_PROMPT, raw_text)
    extracted["source_document"] = source_filename
    extracted["raw_text_snippet"] = raw_text[:500]
    return extracted


def normalize_and_store(db: Session, extracted: dict, confidence_threshold: float = 0.6) -> dict:
    """Normalization layer: match extracted names to canonical DB records and
    persist a Quote row. Deterministic — no LLM involved here."""
    vendor = _match_vendor(db, extracted.get("vendor_name", ""))
    product = _match_product(db, extracted.get("product_sku"), extracted.get("product_name", ""))

    result = {
        "extracted": extracted,
        "matched_vendor": vendor.name if vendor else None,
        "matched_product": product.name if product else None,
        "needs_human_review": False,
        "quote_id": None,
    }

    llm_confidence = float(extracted.get("confidence", 0.5))
    if not vendor or not product or llm_confidence < confidence_threshold:
        result["needs_human_review"] = True
        return result

    quote = Quote(
        vendor_id=vendor.id,
        product_id=product.id,
        unit_price=float(extracted.get("unit_price", 0)),
        currency=extracted.get("currency", "INR"),
        moq=int(extracted.get("moq", 0)),
        lead_time_days=int(extracted.get("lead_time_days", 0)),
        payment_terms=extracted.get("payment_terms"),
        valid_until=extracted.get("valid_until"),
        confidence=llm_confidence,
        source_document=extracted.get("source_document"),
        raw_text_snippet=extracted.get("raw_text_snippet"),
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    result["quote_id"] = quote.id
    return result
