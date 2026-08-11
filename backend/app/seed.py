"""Loads synthetic master data (brands, vendors, products, requirements) into the DB.
Run once before starting the API: `python -m app.seed`
Quotes are NOT seeded here — those come from the Extraction Agent processing the
raw vendor documents, via POST /ingest/process-all.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.models import Brand, Vendor, Product, Requirement
from data.synthetic_data_generator import BRANDS, VENDORS, PRODUCTS, REQUIREMENTS


def seed():
    init_db()
    db = SessionLocal()
    try:
        if db.query(Brand).count() > 0:
            print("DB already seeded, skipping. Delete think9_procurement.db to reset.")
            return

        brand_objs = {}
        for b in BRANDS:
            obj = Brand(name=b["name"], category=b["category"])
            db.add(obj)
            brand_objs[b["name"]] = obj

        vendor_objs = {}
        for v in VENDORS:
            obj = Vendor(
                name=v["name"], category=v["category"],
                reliability_score=v["reliability_score"],
                capacity_units_per_month=v["capacity"],
            )
            db.add(obj)
            vendor_objs[v["name"]] = obj

        product_objs = {}
        for p in PRODUCTS:
            obj = Product(name=p["name"], sku=p["sku"], category=p["category"])
            db.add(obj)
            product_objs[p["sku"]] = obj

        db.flush()  # assign IDs

        for r in REQUIREMENTS:
            db.add(Requirement(
                brand_id=brand_objs[r["brand"]].id,
                product_id=product_objs[r["sku"]].id,
                quantity=r["quantity"],
                required_by_days=r["required_by_days"],
            ))

        db.commit()
        print(f"Seeded {len(BRANDS)} brands, {len(VENDORS)} vendors, "
              f"{len(PRODUCTS)} products, {len(REQUIREMENTS)} requirements.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
