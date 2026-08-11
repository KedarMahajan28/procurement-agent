from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import dashboard, ingest, vendors, recommendations, risks

app = FastAPI(title="Think9 Procurement Intelligence Agent")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

# Register Routers
app.include_router(dashboard.router)
app.include_router(ingest.router)
app.include_router(vendors.router)
app.include_router(recommendations.router)
app.include_router(risks.router)
