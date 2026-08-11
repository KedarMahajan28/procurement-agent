"""
Generates a realistic synthetic Think9 procurement dataset.

Produces:
 - brands, vendors, products, requirements as structured Python data
   (loaded straight into the DB — this represents "already known" master data)
 - raw, unstructured vendor quote "documents" as .txt files under
   backend/data/synthetic/vendor_quotes/ — these simulate parsed PDF/email text
   and are what the Quote Extraction Agent actually reads.

Five deliberate patterns are embedded so the agents have something real to find:
  1. Bundling opportunity      -> 3 brands need the same 250ml bottle
  2. Cheapest != best           -> cheapest vendor for caps has a 35-day lead time
  3. Portfolio risk             -> Vendor Novaplast supplies >55% of volume to 3 brands
  4. Price anomaly              -> a vendor's new quote is ~20% above its historical price
  5. MOQ unlocked by bundling   -> a vendor's MOQ exceeds any single brand's need but is
                                    viable once 2-3 brands' demand is combined
"""
import os
import random

random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
QUOTES_DIR = os.path.join(HERE, "synthetic", "vendor_quotes")
os.makedirs(QUOTES_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Master data
# ---------------------------------------------------------------------------

BRANDS = [
    {"name": "PureGlow", "category": "Skincare"},
    {"name": "HydraLeaf", "category": "Beverages"},
    {"name": "MintFresh", "category": "Oral Care"},
    {"name": "SunnySip", "category": "Beverages"},
    {"name": "GlowLab", "category": "Skincare"},
    {"name": "ZestBite", "category": "Snacks"},
]

VENDORS = [
    {"name": "Novaplast Industries", "category": "Packaging", "reliability_score": 0.72, "capacity": 500000},
    {"name": "Sundar Packaging Co.", "category": "Packaging", "reliability_score": 0.91, "capacity": 300000},
    {"name": "Global Bottle Works",  "category": "Packaging", "reliability_score": 0.85, "capacity": 400000},
    {"name": "Kirti Caps & Closures", "category": "Packaging", "reliability_score": 0.65, "capacity": 200000},
    {"name": "EcoPack Solutions",    "category": "Packaging", "reliability_score": 0.88, "capacity": 250000},
    {"name": "Anand Labels Pvt Ltd", "category": "Labels", "reliability_score": 0.80, "capacity": 1000000},
    {"name": "PrintCraft Labels",    "category": "Labels", "reliability_score": 0.78, "capacity": 800000},
    {"name": "Raj Ingredients Ltd",  "category": "Raw Materials", "reliability_score": 0.83, "capacity": 150000},
]

PRODUCTS = [
    {"name": "250ml PET Bottle", "sku": "BOT-250-PET", "category": "Packaging"},
    {"name": "500ml PET Bottle", "sku": "BOT-500-PET", "category": "Packaging"},
    {"name": "Flip-Top Cap 28mm", "sku": "CAP-28-FT", "category": "Packaging"},
    {"name": "Screw Cap 30mm", "sku": "CAP-30-SC", "category": "Packaging"},
    {"name": "Printed Label 250ml", "sku": "LBL-250-PR", "category": "Labels"},
    {"name": "Printed Label 500ml", "sku": "LBL-500-PR", "category": "Labels"},
    {"name": "Corrugated Shipping Carton", "sku": "CTN-STD-01", "category": "Packaging"},
    {"name": "Shrink Wrap Film", "sku": "FLM-SHR-01", "category": "Packaging"},
    {"name": "Aloe Vera Extract (kg)", "sku": "RAW-ALOE-01", "category": "Raw Materials"},
    {"name": "Citric Acid (kg)", "sku": "RAW-CTRC-01", "category": "Raw Materials"},
    {"name": "Tube 100g Laminate", "sku": "TUB-100-LM", "category": "Packaging"},
    {"name": "Snack Pouch 50g", "sku": "PCH-050-SN", "category": "Packaging"},
]

BRAND_IDX = {b["name"]: i for i, b in enumerate(BRANDS)}
PRODUCT_IDX = {p["sku"]: i for i, p in enumerate(PRODUCTS)}


def _req(brand, sku, qty, days):
    return {"brand": brand, "sku": sku, "quantity": qty, "required_by_days": days}


# Requirements are hand-authored (not random) so the 5 patterns are guaranteed present.
REQUIREMENTS = [
    # Pattern 1 + 5: three brands need 250ml PET Bottle -> combined volume unlocks
    # Novaplast's high MOQ and a volume discount.
    _req("PureGlow", "BOT-250-PET", 18000, 20),
    _req("HydraLeaf", "BOT-250-PET", 22000, 25),
    _req("SunnySip", "BOT-250-PET", 25000, 15),  # tightest deadline of the three

    # Pattern 2: Flip-Top Cap — cheapest vendor (Kirti) has a 35-day lead time,
    # not actually the best choice despite lowest price.
    _req("MintFresh", "CAP-28-FT", 40000, 20),
    _req("GlowLab", "CAP-28-FT", 15000, 18),

    # Ordinary, non-patterned requirements for realism
    _req("PureGlow", "TUB-100-LM", 12000, 25),
    _req("GlowLab", "TUB-100-LM", 9000, 30),
    _req("ZestBite", "PCH-050-SN", 60000, 20),
    _req("SunnySip", "LBL-250-PR", 25000, 15),
    _req("HydraLeaf", "LBL-500-PR", 10000, 25),
    _req("MintFresh", "CTN-STD-01", 5000, 30),
    _req("ZestBite", "CTN-STD-01", 8000, 20),
    _req("GlowLab", "RAW-ALOE-01", 400, 30),
    _req("PureGlow", "RAW-ALOE-01", 250, 30),
    _req("SunnySip", "RAW-CTRC-01", 800, 25),
    _req("MintFresh", "CAP-30-SC", 20000, 20),
    _req("HydraLeaf", "FLM-SHR-01", 3000, 25),
]

# ---------------------------------------------------------------------------
# Quote "documents" — unstructured text simulating vendor PDFs / emails.
# Each entry becomes one .txt file the Extraction Agent will parse.
# ---------------------------------------------------------------------------

QUOTE_DOCS = [
    # --- 250ml PET Bottle: multiple vendors, sets up bundling pattern ---
    dict(vendor="Novaplast Industries", sku="BOT-250-PET", price=8.50, moq=50000, lead=18,
         terms="30 days credit", valid="2026-09-15",
         filename="novaplast_250ml_bottle_quote.txt"),
    dict(vendor="Global Bottle Works", sku="BOT-250-PET", price=8.90, moq=15000, lead=14,
         terms="50% advance, 50% on delivery", valid="2026-09-01",
         filename="global_bottleworks_250ml_quote.txt"),
    dict(vendor="Sundar Packaging Co.", sku="BOT-250-PET", price=9.10, moq=10000, lead=10,
         terms="15 days credit", valid="2026-08-30",
         filename="sundar_250ml_bottle_quote.txt"),

    # --- Flip-Top Cap 28mm: cheapest-is-not-best pattern ---
    dict(vendor="Kirti Caps & Closures", sku="CAP-28-FT", price=2.10, moq=30000, lead=35,
         terms="30 days credit", valid="2026-09-10",
         filename="kirti_flipcap_quote.txt"),
    dict(vendor="EcoPack Solutions", sku="CAP-28-FT", price=2.45, moq=20000, lead=15,
         terms="30 days credit", valid="2026-09-05",
         filename="ecopack_flipcap_quote.txt"),
    dict(vendor="Sundar Packaging Co.", sku="CAP-28-FT", price=2.60, moq=15000, lead=12,
         terms="15 days credit", valid="2026-08-28",
         filename="sundar_flipcap_quote.txt"),

    # --- Screw Cap 30mm ---
    dict(vendor="Kirti Caps & Closures", sku="CAP-30-SC", price=1.85, moq=15000, lead=20,
         terms="30 days credit", valid="2026-09-12",
         filename="kirti_screwcap_quote.txt"),
    dict(vendor="EcoPack Solutions", sku="CAP-30-SC", price=2.05, moq=10000, lead=14,
         terms="30 days credit", valid="2026-09-02",
         filename="ecopack_screwcap_quote.txt"),

    # --- Printed Labels ---
    dict(vendor="Anand Labels Pvt Ltd", sku="LBL-250-PR", price=0.65, moq=10000, lead=10,
         terms="30 days credit", valid="2026-09-20",
         filename="anand_label250_quote.txt"),
    dict(vendor="PrintCraft Labels", sku="LBL-250-PR", price=0.72, moq=5000, lead=8,
         terms="15 days credit", valid="2026-09-01",
         filename="printcraft_label250_quote.txt"),
    dict(vendor="Anand Labels Pvt Ltd", sku="LBL-500-PR", price=0.85, moq=8000, lead=10,
         terms="30 days credit", valid="2026-09-20",
         filename="anand_label500_quote.txt"),

    # --- Carton, film, tube, pouch — everyday items ---
    dict(vendor="Global Bottle Works", sku="CTN-STD-01", price=22.00, moq=2000, lead=12,
         terms="30 days credit", valid="2026-09-10",
         filename="global_carton_quote.txt"),
    dict(vendor="EcoPack Solutions", sku="FLM-SHR-01", price=180.00, moq=500, lead=15,
         terms="30 days credit", valid="2026-09-05",
         filename="ecopack_shrinkfilm_quote.txt"),
    dict(vendor="Novaplast Industries", sku="TUB-100-LM", price=4.20, moq=8000, lead=20,
         terms="30 days credit", valid="2026-09-15",
         filename="novaplast_tube_quote.txt"),
    dict(vendor="Global Bottle Works", sku="PCH-050-SN", price=1.10, moq=40000, lead=16,
         terms="50% advance", valid="2026-09-08",
         filename="global_pouch_quote.txt"),

    # --- Raw materials ---
    dict(vendor="Raj Ingredients Ltd", sku="RAW-ALOE-01", price=850.00, moq=100, lead=25,
         terms="30 days credit", valid="2026-10-01",
         filename="raj_aloe_quote.txt"),
    dict(vendor="Raj Ingredients Ltd", sku="RAW-CTRC-01", price=210.00, moq=200, lead=20,
         terms="30 days credit", valid="2026-10-01",
         filename="raj_citric_quote.txt"),

    # --- Pattern 4: price anomaly — Novaplast's historical price for 500ml bottle
    # was ~9.20; this new quote is a ~20% jump with no stated reason. ---
    dict(vendor="Novaplast Industries", sku="BOT-500-PET", price=11.05, moq=20000, lead=18,
         terms="30 days credit", valid="2026-09-18",
         filename="novaplast_500ml_bottle_quote_NEW.txt", is_anomaly=True, historical_price=9.20),
    dict(vendor="Sundar Packaging Co.", sku="BOT-500-PET", price=9.60, moq=8000, lead=12,
         terms="15 days credit", valid="2026-09-03",
         filename="sundar_500ml_bottle_quote.txt"),
    dict(vendor="Global Bottle Works", sku="BOT-500-PET", price=9.35, moq=12000, lead=13,
         terms="30 days credit", valid="2026-09-06",
         filename="global_500ml_bottle_quote.txt"),
]

DOC_TEMPLATE = """From: sales@{domain}
Subject: Quotation - {product_name}

Dear Procurement Team,

Thank you for your inquiry. Please find our quotation below for {product_name} (ref: {sku}):

We can supply {product_name} at INR {price} per unit for orders above {moq} units.
Lead time will be approximately {lead} working days from order confirmation.
Payment terms: {terms}.
This quotation is valid until {valid}.

{extra}

Regards,
{vendor} Sales Team
"""


def _domain(vendor_name: str) -> str:
    return vendor_name.lower().replace(" ", "").replace(".", "").replace("&", "and")[:20] + ".com"


def generate():
    product_lookup = {p["sku"]: p["name"] for p in PRODUCTS}

    for q in QUOTE_DOCS:
        extra = ""
        if q.get("is_anomaly"):
            extra = (f"Note: due to recent resin cost increases, pricing has been revised "
                      f"from our previous rate of INR {q['historical_price']}/unit.")
        text = DOC_TEMPLATE.format(
            domain=_domain(q["vendor"]),
            product_name=product_lookup[q["sku"]],
            sku=q["sku"],
            price=q["price"],
            moq=q["moq"],
            lead=q["lead"],
            terms=q["terms"],
            valid=q["valid"],
            vendor=q["vendor"],
            extra=extra,
        )
        path = os.path.join(QUOTES_DIR, q["filename"])
        with open(path, "w") as f:
            f.write(text)

    print(f"Generated {len(QUOTE_DOCS)} vendor quote documents in {QUOTES_DIR}")
    print(f"Master data: {len(BRANDS)} brands, {len(VENDORS)} vendors, "
          f"{len(PRODUCTS)} products, {len(REQUIREMENTS)} requirements")


if __name__ == "__main__":
    generate()
