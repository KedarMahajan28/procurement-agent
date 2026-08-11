import streamlit as st
from api_client import get, inject_theme, api_available

st.set_page_config(page_title="Risk Alerts · Think9", page_icon="◈", layout="wide")
inject_theme()

st.markdown('<div class="think9-eyebrow">SUPPLIER RISK AGENT</div>', unsafe_allow_html=True)
st.title("Risk Alerts")
st.caption("Operational, commercial, and portfolio-concentration risks across the vendor base.")

if not api_available():
    st.error("Can't reach the backend API.")
    st.stop()

risks = get("/risks")
if not risks:
    st.success("No risks detected — or the pipeline hasn't been run yet.")
    st.stop()

type_labels = {
    "operational": "Operational",
    "commercial": "Commercial",
    "portfolio_dependency": "Portfolio Dependency",
}
badge_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}
card_class = {"High": "risk-high", "Medium": "risk-medium", "Low": "risk-low"}

filter_type = st.multiselect("Filter by type", list(type_labels.values()), default=list(type_labels.values()))

for a in risks:
    label = type_labels.get(a["risk_type"], a["risk_type"])
    if label not in filter_type:
        continue
    st.markdown(f"""
    <div class="think9-card {card_class.get(a['severity'], 'risk-low')}">
        <span class="think9-badge {badge_class.get(a['severity'], 'badge-low')}">{a['severity']}</span>
        <span class="think9-badge" style="background:var(--secondary-background-color); color:var(--text-color); border:1px solid currentColor;">{label}</span>
        <h4 style="margin:0.4rem 0 0.1rem 0;">{a['vendor_name']}</h4>
        <p>{a['description']}</p>
        <p style="color:var(--text-color); opacity:0.7; font-size:0.85rem;"><b>Suggested action:</b> {a['recommendation']}</p>
    </div>
    """, unsafe_allow_html=True)
