from datetime import datetime
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    brands: int
    active_skus: int
    active_vendors: int
    potential_savings: float
    open_risks: int
    bundling_opportunities: int
    price_anomalies: int


class VendorComparisonRow(BaseModel):
    vendor_name: str
    unit_price: float
    moq: int
    lead_time_days: int
    total_score: float
    meets_moq: bool
    risk_hint: str


class RecommendationOut(BaseModel):
    id: int
    product_name: str
    recommended_vendor: str
    score: float
    reason: str
    risk_level: str
    risk_note: str | None
    potential_saving: float
    confidence: float
    is_cross_brand: bool
    involved_brands: list[str]
    combined_volume: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionIn(BaseModel):
    recommendation_id: int
    decision: str  # approved / rejected / negotiation_requested
    approved_by: str
    notes: str | None = None
