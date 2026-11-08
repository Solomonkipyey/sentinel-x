import streamlit as st
import httpx
from pathlib import Path

# Auth Check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Please log in on the main page.")
    st.stop()

st.set_page_config(page_title="Lead Generator", page_icon="💼", layout="wide")

# Load CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    load_css(css_path)

st.markdown("<h1>💼 Client Lead Generator</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #888;'>Companies recently mentioned in cyber attacks. Reach out to offer your services.</p>", unsafe_allow_html=True)

API = "http://localhost:8000"

try:
    leads = httpx.get(f"{API}/leads", timeout=30).json()
except Exception as e:
    st.error(f"Backend not reachable: {e}")
    st.stop()

if not leads:
    st.info("No leads found yet. Fetch more news on the Home page and try again.")
    st.stop()

st.success(f"Identified {len(leads)} potential targets from recent news!")
st.divider()

for lead in leads:
    with st.expander(f"🏢 {lead['domain']} (Context: {lead['context'][:60]}...)"):
        st.markdown(f"**Source Article:** [LINK]({lead['url']})", unsafe_allow_html=True)
        st.text_area("Pitch Template:", value=lead["pitch"], height=150)
        st.caption("💡 Tip: Find the IT Director of this company on LinkedIn and send them this pitch.")