# Think9 Procurement Intelligence Agent

A centralized AI procurement intelligence layer for Think9's 30+ brand portfolio.
Ingests vendor quotations, extracts structured data, compares suppliers,
detects cross-brand bundling opportunities, flags risk, and produces scored,
explained recommendations — always with a human approval step before any
decision is finalized.

Submission for the Think9 AI & Intelligence Challenge (Cross-Portfolio Supply
Chain & Sourcing/Procurement Intelligence track).

## Architecture

```
Vendor documents (PDF/email/chat, as text)
        ↓
Quote Extraction Agent (LLM) — unstructured text → structured JSON
        ↓
Normalization layer (deterministic) — match to canonical vendor/product
        ↓
Structured store (SQLite, Postgres-compatible schema)
        ↓
Supplier Comparison Agent (deterministic) — weighted scoring, not cheapest-wins
Cross-Brand Bundling Agent (deterministic) — combined-volume savings
Supplier Risk Agent (deterministic) — operational / commercial / portfolio risk
        ↓
Decision Agent — combines the above; LLM only writes the plain-English "why"
        ↓
Human approval (Streamlit UI) — Approve / Request Negotiation / Reject
        ↓
Decision recorded, feeds future recommendations
```

Orchestrated via **LangGraph**. Per the project's core engineering principle:
LLMs handle unstructured reasoning and explanation; every number that a
decision depends on (savings, scores, MOQs, volumes) is computed by
deterministic Python, never by an LLM.

## Tech stack

- **Backend:** FastAPI + SQLAlchemy + SQLite (schema is Postgres-compatible —
  swap `DATABASE_URL` to move to Postgres with zero model changes)
- **Agent orchestration:** LangGraph
- **LLM:** Groq (`llama-3.3-70b-versatile` by default, configurable)
- **Frontend:** Streamlit

## Project structure

```
backend/
  app/
    models.py, database.py, schemas.py    — data layer
    llm_client.py                          — Groq wrapper
    seed.py                                — loads synthetic master data
    main.py                                — FastAPI routes
    agents/
      extraction_agent.py                  — Agent 1: Quote Extraction
      comparison_agent.py                  — Agent 2: Supplier Comparison
      bundling_agent.py                    — Agent 3: Cross-Brand Bundling
      risk_agent.py                        — Agent 4: Supplier Risk
      decision_agent.py                    — Agent 5: Decision/Recommendation
      graph.py                             — LangGraph orchestration
  data/
    synthetic_data_generator.py            — generates brands/vendors/products/
                                              requirements + 20 raw vendor
                                              quote documents with 5 deliberate
                                              patterns for the agents to find
    synthetic/vendor_quotes/*.txt          — generated documents (unstructured
                                              input to the Extraction Agent)
frontend/
  app.py                                   — Dashboard
  pages/                                   — Upload, Vendor Comparison,
                                              AI Recommendations, Cross-Brand
                                              Opportunities, Risk Alerts
  api_client.py                            — shared API client + theme
```

## Setup

```bash
cd think9-procurement-agent

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt

export GROQ_API_KEY=your_key_here   # Windows: 

```

## Run

**1. Generate the synthetic dataset** (only needed once, already generated in this repo):
```bash
python backend/data/synthetic_data_generator.py
```

**2. Seed the database:**
```bash
cd backend
python -m app.seed
```

**3. Start the backend:**
```bash
uvicorn app.main:app --reload --port 8000
```

**4. In a second terminal, start the frontend:**
```bash
cd frontend
streamlit run app.py
```

Open http://localhost:8501. On the **Upload Documents** page, click
**"Run extraction pipeline over synthetic documents"** to process all 20
seeded vendor quotes and generate recommendations — this is the core demo
moment.

## The 5 planted patterns in the synthetic data

The synthetic dataset (`backend/data/synthetic_data_generator.py`) deliberately
encodes 5 patterns so the agents have something real to discover:

1. **Bundling opportunity** — PureGlow, HydraLeaf, and SunnySip each need
   250ml PET bottles; combined (65,000 units) unlocks Novaplast's 50,000-unit
   MOQ and a better price than any brand could get alone.
2. **Cheapest ≠ best** — Kirti's Flip-Top Cap quote is the cheapest but has a
   35-day lead time, well past MintFresh's and GlowLab's delivery windows —
   flagged as High operational risk even though it scores well on price.
3. **Portfolio dependency risk** — Anand Labels and Raj Ingredients each supply
   100% of their category's recommended volume — a concentration risk.
4. **Price anomaly** — Novaplast's 500ml bottle quote is ~11% above the
   market average across other vendors (stated as a resin-cost increase from a
   previous ~₹9.20/unit rate).
5. **MOQ unlocked by bundling** — Novaplast's 50,000-unit MOQ exceeds any
   single brand's 250ml bottle requirement but is cleared once three brands'
   demand is combined.

Reset the dataset/DB anytime with `rm backend/think9_procurement.db` and
re-running steps 1–2.

## API reference (selected)

| Endpoint | Purpose |
|---|---|
| `GET /dashboard/summary` | Portfolio-level KPIs |
| `POST /ingest/process-all` | Run the full pipeline over seeded documents |
| `POST /ingest/upload` | Upload + process a new vendor document |
| `GET /vendors/comparison/{product_id}` | Scored vendor comparison for a product |
| `GET /recommendations` | All AI recommendations |
| `GET /recommendations/cross-brand` | Cross-brand bundling opportunities only |
| `POST /decisions` | Record a human approve/reject/negotiate decision |
| `GET /risks` | All risk alerts |

## Human-in-the-loop

No purchase decision is ever made automatically. Every recommendation sits in
the **AI Recommendations** page until a procurement manager clicks
**Approve**, **Request Negotiation**, or **Reject** — the decision is stored
with a timestamp and approver, forming the audit trail called for in the
spec's governance section.

## What's intentionally out of scope for this prototype

- **Vector search (FAISS/Chroma):** no concrete semantic-retrieval need yet
  with this dataset size; noted as future work.
- **Real OCR:** synthetic vendor "PDFs" are provided as parsed text directly,
  since OCR quality isn't what this challenge is evaluating.
- **Postgres:** SQLite is used for zero-setup local running; the schema in
  `models.py` uses only standard SQLAlchemy types and moves to Postgres by
  changing one connection string.


