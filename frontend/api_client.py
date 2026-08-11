import os
import requests
import streamlit as st

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")


def get(path: str, **kwargs):
    r = requests.get(f"{API_BASE}{path}", timeout=30, **kwargs)
    r.raise_for_status()
    return r.json()


def post(path: str, **kwargs):
    r = requests.post(f"{API_BASE}{path}", timeout=60, **kwargs)
    r.raise_for_status()
    return r.json()


def api_available() -> bool:
    try:
        get("/dashboard/summary")
        return True
    except Exception:
        return False


def inject_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; }

        /* Metric Styling */
        [data-testid="stMetricValue"] {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.8rem;
        }
        [data-testid="stMetricLabel"] {
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.8rem;
            font-weight: 600;
            opacity: 0.7;
        }
        [data-testid="metric-container"] {
            background-color: var(--secondary-background-color);
            border: 1px solid var(--secondary-background-color);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        /* Card Styling */
        .think9-card {
            background: var(--secondary-background-color);
            border: 1px solid var(--secondary-background-color);
            border-left: 4px solid #4F46E5;
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }
        .think9-card:hover {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .think9-card.risk-high { border-left-color: #EF4444; }
        .think9-card.risk-medium { border-left-color: #F59E0B; }
        .think9-card.risk-low { border-left-color: #10B981; }

        /* Badges */
        .think9-badge {
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-transform: uppercase;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px; /* Pill shape */
            margin-right: 0.4rem;
        }
        .badge-high { background: #FEE2E2; color: #B91C1C; }
        .badge-medium { background: #FEF3C7; color: #B45309; }
        .badge-low { background: #D1FAE5; color: #047857; }
        .badge-cross-brand { background: #E0E7FF; color: #4338CA; }

        /* Eyebrow Text */
        .think9-eyebrow {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: #4F46E5;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
            font-weight: 600;
        }

    </style>
    """, unsafe_allow_html=True)
