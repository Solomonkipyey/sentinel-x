import httpx
import streamlit as st

st.set_page_config(page_title="AI Analyst", page_icon="🧠", layout="wide")
st.title("🧠 AI Threat Analyst")
st.caption("Analyze any collected article with AI")

API = "http://localhost:8000"

try:
    docs = httpx.get(f"{API}/documents?limit=20", timeout=30).json()
except Exception as e:
    st.error(f"Cannot reach API: {e}")
    st.stop()

if not docs:
    st.info("No documents yet — fetch news on Home page first")
    st.stop()

options = {f"{d['title'][:80]}": d["id"] for d in docs}
selected_title = st.selectbox("Pick a document", list(options.keys()))
selected_id = options[selected_title]

if st.button("🤖 Analyze with AI", type="primary"):
    with st.spinner("Analyzing..."):
        try:
            r = httpx.post(f"{API}/analyze/{selected_id}", timeout=60)
            result = r.json()
        except Exception as e:
            st.error(f"Failed: {e}")
            st.stop()

    if "error" in result:
        st.error(result["error"])
    else:
        st.subheader("Summary")
        st.write(result.get("summary", "—"))

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Severity", result.get("severity", "—").upper())
        with col2:
            st.metric("Confidence", "AI-assisted")

        st.subheader("Threat Actors")
        actors = result.get("threat_actors", [])
        st.write(", ".join(actors) if actors else "None identified")

        st.subheader("TTPs (MITRE ATT&CK)")
        ttps = result.get("ttps", [])
        st.write(", ".join(ttps) if ttps else "None identified")

        st.subheader("Affected Products")
        products = result.get("affected_products", [])
        st.write(", ".join(products) if products else "None identified")

        st.subheader("Reasoning")
        st.write(result.get("reasoning", "—"))