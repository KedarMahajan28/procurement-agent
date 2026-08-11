import streamlit as st
from api_client import get, inject_theme, api_available
import pandas as pd

st.set_page_config(page_title="Think9 Procurement Intelligence", page_icon="◈", layout="wide")
inject_theme()

st.markdown('<div class="think9-eyebrow">THINK9 · CROSS-PORTFOLIO PROCUREMENT</div>', unsafe_allow_html=True)
st.title("Procurement Intelligence Layer")
st.caption("Turning 30+ brands into one intelligent procurement network.")

if not api_available():
    st.error(
        "Can't reach the backend API. Start it with:\n\n"
        "`cd backend && uvicorn app.main:app --reload`"
    )
    st.stop()

summary = get("/dashboard/summary")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Brands", summary["brands"])
with col2:
    st.metric("Active SKUs", summary["active_skus"])
with col3:
    st.metric("Active Vendors", summary["active_vendors"])

st.markdown("<br/>", unsafe_allow_html=True)

col4, col5, col6, col7 = st.columns(4)
with col4:
    st.metric("Potential Savings", f"₹{summary['potential_savings']:,.0f}")
with col5:
    st.metric("Open Risks", summary["open_risks"])
with col6:
    st.metric("Bundling Opportunities", summary["bundling_opportunities"])
with col7:
    st.metric("Price Anomalies", summary["price_anomalies"])

st.divider()

# -- Add Chart --
st.subheader("Potential Savings by Product")
recs = get("/recommendations")
if recs:
    # Aggregate savings by product
    savings_data = {}
    for r in recs:
        product = r.get("product_name", "Unknown")
        savings = r.get("potential_saving", 0)
        savings_data[product] = savings_data.get(product, 0) + savings
    
    if savings_data:
        df = pd.DataFrame(list(savings_data.items()), columns=["Product", "Savings (₹)"])
        df = df.set_index("Product")
        st.bar_chart(df, color="#4F46E5")
else:
    st.info("No savings recommendations available yet.")

st.divider()

st.subheader("How this works")
c1, c2, c3, c4, c5 = st.columns(5)
steps = [
    ("1 · Extract", "Vendor PDFs/emails → structured quote data"),
    ("2 · Compare", "Price, lead time, MOQ, reliability, capacity"),
    ("3 · Bundle", "Combine demand across brands for leverage"),
    ("4 · Flag Risk", "Operational, commercial, portfolio concentration"),
    ("5 · Recommend", "Scored, explained, awaiting your approval"),
]
for col, (title, desc) in zip([c1, c2, c3, c4, c5], steps):
    col.markdown(f"""<div class="think9-card"><b>{title}</b><br/>
        <span style="color:var(--text-color); opacity:0.7; font-size:0.85rem;">{desc}</span></div>""",
        unsafe_allow_html=True)

st.info(
    "**Nothing here places an order.** Every recommendation waits for a human "
    "procurement manager to Approve, Modify (negotiate), or Reject — see "
    "**AI Recommendations** in the sidebar.",
    icon="🛡️",
)

st.markdown("Use the sidebar to upload vendor documents, compare suppliers, "
            "review AI recommendations, and explore cross-brand savings.")
