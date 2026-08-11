import streamlit as st
from api_client import get, post, inject_theme, api_available

st.set_page_config(page_title="Upload Documents · Think9", page_icon="◈", layout="wide")
inject_theme()

st.markdown('<div class="think9-eyebrow">DOCUMENT INGESTION</div>', unsafe_allow_html=True)
st.title("Upload Procurement Documents")
st.caption("Vendor quotations go in unstructured. The Extraction Agent turns them into structured data.")

if not api_available():
    st.error("Can't reach the backend API. Start it with `uvicorn app.main:app --reload` in `backend/`.")
    st.stop()

st.markdown("### Process the seeded synthetic dataset")
st.write(
    "This prototype ships with 20 synthetic vendor quote documents (emails from 8 vendors "
    "across 6 brands) already sitting in `backend/data/synthetic/vendor_quotes/`. "
    "Run the full pipeline over them:"
)

if st.button("▶ Run extraction pipeline over synthetic documents", type="primary"):
    with st.spinner("Extracting quotes, normalizing, running comparison/bundling/risk/decision agents…"):
        try:
            result = post("/ingest/process-all")
            st.success("Pipeline complete.")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Documents processed", result["documents_processed"])
            c2.metric("Quotes extracted", result["quotes_extracted"])
            c3.metric("Needs human review", result["needs_review"])
            c4.metric("Recommendations generated", result["recommendations_generated"])
        except Exception as e:
            st.error(f"Pipeline failed: {e}")

st.divider()

st.markdown("### Upload a new vendor document")
st.write("Add a new quote as a .txt file (simulating parsed PDF/email text) and it "
         "runs through the same Extraction Agent immediately.")

uploaded = st.file_uploader("Vendor quote document (.txt)", type=["txt"])
if uploaded is not None:
    if st.button("Process this document"):
        with st.spinner("Extracting…"):
            try:
                files = {"file": (uploaded.name, uploaded.getvalue(), "text/plain")}
                result = post("/ingest/upload", files=files)
                if result["quotes_extracted"] > 0:
                    st.success(f"Extracted and stored quote from {result['filename']}.")
                else:
                    st.warning(
                        f"Extraction confidence was too low or the vendor/product "
                        f"couldn't be matched — routed to human review."
                    )
            except Exception as e:
                st.error(f"Upload failed: {e}")
