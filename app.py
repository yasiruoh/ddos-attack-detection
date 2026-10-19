import io
import json
import streamlit as st
from src.validation import check_bytes

st.set_page_config(page_title='DDoS Flow Classification', page_icon="🔬", layout="wide")
st.title('DDoS Flow Classification')
st.caption('Batch network-flow classification using a schema-validated ONNX classifier interface.')
threshold = st.sidebar.slider("Review threshold", 0.0, 1.0, 0.5, 0.05)
st.sidebar.caption("Local inference • JSON export • No fabricated predictions")


from src.engine import predict_csv, BASE
st.info("Offline CSV flow classification. No traffic generation, packet capture, or automated blocking.")
installed = (BASE / "models/model.onnx").is_file() and (BASE / "models/schema.json").is_file()
if not installed:
    st.warning("Model not installed. This repository includes the inference application, not a verified DDoS checkpoint. See models/README.md for the artifact contract.")
uploaded = st.file_uploader("Flow CSV with exact model feature columns", type=["csv"])
if uploaded and st.button("Classify flows", type="primary", disabled=not installed):
    try:
        with st.spinner("Classifying flow records"):
            result = predict_csv(uploaded.getvalue(), threshold)
        st.json(result)
        st.download_button("Download JSON", json.dumps(result,indent=2), "result.json", "application/json")
    except Exception as exc:
        st.error(f"Analysis unavailable: {exc}")
