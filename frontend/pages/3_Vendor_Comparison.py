import pandas as pd
import streamlit as st
from api_client import get, inject_theme, api_available

st.set_page_config(page_title="Vendor Comparison · Think9", page_icon="◈", layout="wide")
inject_theme()

st.markdown('<div class="think9-eyebrow">SUPPLIER COMPARISON AGENT</div>', unsafe_allow_html=True)
st.title("Vendor Comparison")
st.caption("Not just cheapest-wins — weighted on price, lead time, MOQ fit, reliability, and capacity.")

if not api_available():
    st.error("Can't reach the backend API.")
    st.stop()

products = get("/products")
if not products:
    st.warning("No products found. Seed the database first (`python -m app.seed`).")
    st.stop()

names = {p["name"]: p["id"] for p in products}
selected = st.selectbox("Product", list(names.keys()))
product_id = names[selected]

data = get(f"/vendors/comparison/{product_id}")

if not data["vendors"]:
    st.info("No vendor quotes for this product yet — run the extraction pipeline on the Upload page first.")
    st.stop()

st.markdown(f"#### {data['product']} — {len(data['vendors'])} vendor(s) quoted")

df = pd.DataFrame([
    {
        "Vendor": v["vendor_name"],
        "Price (₹)": v["unit_price"],
        "MOQ": v["moq"],
        "Meets MOQ": "✓" if v["meets_moq"] else "✗",
        "Lead Time (days)": v["lead_time_days"],
        "Score": v["total_score"],
    }
    for v in data["vendors"]
])
df = df.sort_values("Score", ascending=False).reset_index(drop=True)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("##### Score breakdown (weights: Price 40% · Lead Time 20% · MOQ 15% · Reliability 15% · Capacity 10%)")
for v in sorted(data["vendors"], key=lambda x: -x["total_score"]):
    with st.expander(f"{v['vendor_name']} — {v['total_score']}/100"):
        cs = v["component_scores"]
        cols = st.columns(5)
        cols[0].metric("Price", cs["price"])
        cols[1].metric("Lead Time", cs["lead_time"])
        cols[2].metric("MOQ Fit", cs["moq"])
        cols[3].metric("Reliability", cs["reliability"])
        cols[4].metric("Capacity", cs["capacity"])
