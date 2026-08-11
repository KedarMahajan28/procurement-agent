import streamlit as st
from api_client import get, inject_theme, api_available

st.set_page_config(page_title="Cross-Brand Opportunities · Think9", page_icon="◈", layout="wide")
inject_theme()

st.markdown('<div class="think9-eyebrow">BUNDLING AGENT · PORTFOLIO VIEW</div>', unsafe_allow_html=True)
st.title("Cross-Brand Savings")
st.caption("Opportunities invisible to any single brand, visible only from the portfolio level.")

if not api_available():
    st.error("Can't reach the backend API.")
    st.stop()

recs = get("/recommendations/cross-brand")
if not recs:
    st.info("No cross-brand opportunities found yet — run the extraction pipeline first.")
    st.stop()

total = sum(r["potential_saving"] for r in recs)
st.metric("Total cross-brand savings identified", f"₹{total:,.0f}")
st.divider()

for i, r in enumerate(recs, 1):
    st.markdown(f"""
    <div class="think9-card">
        <div class="think9-eyebrow">OPPORTUNITY #{i}</div>
        <h4 style="margin:0.1rem 0;">{r['product_name']}</h4>
        <p style="color:var(--text-color); opacity:0.7; margin:0.2rem 0;">
            Brands: <b>{' + '.join(r['involved_brands'])}</b>
        </p>
        <p>Combined volume: <b>{r['combined_volume']:,} units</b> via <b>{r['recommended_vendor']}</b></p>
        <p style="font-family:'JetBrains Mono', monospace; color:#10b981; font-weight:600; font-size:1.1rem;">
            Potential saving: ₹{r['potential_saving']:,.0f}
        </p>
        <p style="color:var(--text-color); opacity:0.7; font-size:0.85rem;">Confidence: {r['confidence']*100:.0f}% · Risk: {r['risk_level']}</p>
        <p style="margin-top:0.5rem;">{r['reason']}</p>
    </div>
    """, unsafe_allow_html=True)
