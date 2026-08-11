"""
Database models for the Think9 Procurement Intelligence Agent.

Schema is deliberately written to be Postgres-compatible (standard SQLAlchemy
types, no SQLite-only tricks) even though the prototype runs on SQLite for
zero-setup local development. Swapping DATABASE_URL to a postgres:// DSN in
database.py is the only change needed to move to Postgres in production.
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship

from .database import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)

    requirements = relationship("Requirement", back_populates="brand")


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    reliability_score = Column(Float, default=0.75)  # 0-1, historical on-time/quality performance
    capacity_units_per_month = Column(Integer, default=100000)

    quotes = relationship("Quote", back_populates="vendor")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sku = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)

    quotes = relationship("Quote", back_populates="product")
    requirements = relationship("Requirement", back_populates="product")


class Requirement(Base):
    """A brand's demand for a product — what a brand needs to buy."""
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    required_by_days = Column(Integer, nullable=False)  # delivery window in days from now

    brand = relationship("Brand", back_populates="requirements")
    product = relationship("Product", back_populates="requirements")


class Quote(Base):
    """A structured vendor quotation — output of the Quote Extraction Agent."""
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    unit_price = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    moq = Column(Integer, nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    payment_terms = Column(String, nullable=True)
    valid_until = Column(String, nullable=True)  # ISO date string
    confidence = Column(Float, default=1.0)  # extraction confidence, 0-1

    source_document = Column(String, nullable=True)  # filename this was extracted from
    raw_text_snippet = Column(Text, nullable=True)   # what the LLM extracted from
    extracted_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="quotes")
    product = relationship("Product", back_populates="quotes")


class Recommendation(Base):
    """Output of the Decision Agent — a scored, explained recommendation."""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    recommended_vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)

    score = Column(Float, nullable=False)              # 0-100 composite score
    reason = Column(Text, nullable=False)               # LLM-generated explanation
    risk_level = Column(String, nullable=False)          # Low / Medium / High
    risk_note = Column(Text, nullable=True)
    potential_saving = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)

    is_cross_brand = Column(Boolean, default=False)
    involved_brand_ids = Column(String, nullable=True)   # comma-separated brand ids
    combined_volume = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")
    recommended_vendor = relationship("Vendor")
    decisions = relationship("Decision", back_populates="recommendation")


class Decision(Base):
    """Human-in-the-loop outcome on a recommendation."""
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False)
    decision = Column(String, nullable=False)   # approved / rejected / negotiation_requested
    approved_by = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    recommendation = relationship("Recommendation", back_populates="decisions")


class RiskAlert(Base):
    """Output of the Supplier Risk Agent."""
    __tablename__ = "risk_alerts"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    risk_type = Column(String, nullable=False)   # operational / commercial / portfolio_dependency / price_anomaly
    severity = Column(String, nullable=False)     # Low / Medium / High
    description = Column(Text, nullable=False)
    recommendation_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor")
