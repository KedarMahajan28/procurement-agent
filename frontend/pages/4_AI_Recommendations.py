import streamlit as st
from api_client import get, post, inject_theme, api_available

st.set_page_config(page_title="AI Recommendations · Think9", page_icon="◈", layout="wide")
inject_theme()

st.markdown('<div class="think9-eyebrow">DECISION AGENT · HUMAN-IN-THE-LOOP</div>', unsafe_allow_html=True)
st.title("AI Recommendations")
st.caption("Every recommendation is explained and scored. Nothing here places an order without your sign-off.")

if not api_available():
    st.error("Can't reach the backend API.")
    st.stop()

recs = get("/recommendations")
if not recs:
    st.info("No recommendations yet — run the extraction pipeline on the Upload Documents page first.")
    st.stop()

total_savings = sum(r["potential_saving"] for r in recs)
st.metric("Total identified potential savings", f"₹{total_savings:,.0f}")
st.divider()

risk_class = {"High": "risk-high", "Medium": "risk-medium", "Low": "risk-low"}
badge_class = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}

approver = st.text_input("Reviewing as", value="Procurement Manager")

for r in recs:
    card_class = risk_class.get(r["risk_level"], "risk-low")
    badges = f'<span class="think9-badge {badge_class.get(r["risk_level"], "badge-low")}">{r["risk_level"]} RISK</span>'
    if r["is_cross_brand"]:
        badges += '<span class="think9-badge badge-cross-brand">CROSS-BRAND</span>'

    st.markdown(f"""
    <div class="think9-card {card_class}">
        {badges}
        <h4 style="margin:0.4rem 0 0.1rem 0;">{r['product_name']} → {r['recommended_vendor']}</h4>
        <span style="color:var(--text-color); opacity:0.7; font-size:0.85rem;">
            Score {r['score']}/100 · Confidence {r['confidence']*100:.0f}%
            {'· Brands: ' + ', '.join(r['involved_brands']) if r['involved_brands'] else ''}
            {'· Combined volume: ' + f"{r['combined_volume']:,} units" if r['combined_volume'] else ''}
        </span>
        <p style="margin-top:0.6rem;">{r['reason']}</p>
        {'<p style="color:#ef4444; font-size:0.88rem;"><b>Risk:</b> ' + r['risk_note'] + '</p>' if r['risk_note'] else ''}
        <p style="font-family:'JetBrains Mono', monospace; color:#10b981; font-weight:600;">
            Potential saving: ₹{r['potential_saving']:,.0f}
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, _ = st.columns([1, 1, 1, 3])
    if c1.button("✓ Approve", key=f"approve_{r['id']}"):
        post("/decisions", json={
            "recommendation_id": r["id"], "decision": "approved",
            "approved_by": approver or "Procurement Manager",
        })
        st.success("Approved and recorded.")
        st.rerun()
    if c2.button("↻ Request Negotiation", key=f"negotiate_{r['id']}"):
        post("/decisions", json={
            "recommendation_id": r["id"], "decision": "negotiation_requested",
            "approved_by": approver or "Procurement Manager",
        })
        st.info("Marked for negotiation.")
        st.rerun()
    if c3.button("✗ Reject", key=f"reject_{r['id']}"):
        post("/decisions", json={
            "recommendation_id": r["id"], "decision": "rejected",
            "approved_by": approver or "Procurement Manager",
        })
        st.warning("Rejected.")
        st.rerun()

st.divider()
st.markdown("### Decision history")
decisions = get("/decisions")
if decisions:
    import pandas as pd
    st.dataframe(pd.DataFrame(decisions)[["product", "decision", "approved_by", "timestamp"]],
                 use_container_width=True, hide_index=True)
else:
    st.caption("No decisions recorded yet.")
