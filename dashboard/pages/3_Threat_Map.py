import streamlit as st
import httpx
from pathlib import Path

# Auth Check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Please log in on the main page.")
    st.stop()

st.set_page_config(page_title="AI Analyst", page_icon="🧠", layout="wide")

# Load CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    load_css(css_path)

st.markdown("<h1>🧠 AI Threat Analyst</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #888;'>Analyze any collected article with AI</p>", unsafe_allow_html=True)

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

if st.button("🤖 INITIATE ANALYSIS", type="primary"):
    with st.spinner("Analyzing threat data..."):
        try:
            r = httpx.post(f"{API}/analyze/{selected_id}", timeout=60)
            result = r.json()
        except Exception as e:
            st.error(f"Failed: {e}")
            st.stop()

    if "error" in result:
        st.error(result["error"])
    else:
        st.markdown("<h3>Executive Summary</h3>", unsafe_allow_html=True)
        st.info(result.get("summary", "—"))

        col1, col2 = st.columns(2)
        col1.metric("SEVERITY", result.get("severity", "—").upper())
        col2.metric("STATUS", "AI-ASSISTED")

        st.markdown("<h3>Threat Actors</h3>", unsafe_allow_html=True)
        actors = result.get("threat_actors", [])
        st.write(", ".join(actors) if actors else "None identified")

        st.markdown("<h3>TTPs (MITRE ATT&CK)</h3>", unsafe_allow_html=True)
        ttps = result.get("ttps", [])
        st.write(", ".join(ttps) if ttps else "None identified")

        st.markdown("<h3>Affected Products</h3>", unsafe_allow_html=True)
        products = result.get("affected_products", [])
        st.write(", ".join(products) if products else "None identified")