import streamlit as st
import httpx
from pathlib import Path

# Auth Check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Please log in on the main page.")
    st.stop()

st.set_page_config(page_title="Watchlist", page_icon="🎯", layout="wide")

# Load CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    load_css(css_path)

st.markdown("<h1>🎯 Target Watchlist</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #888;'>Add keywords, companies, or technologies you want to monitor.</p>", unsafe_allow_html=True)

API = "http://localhost:8000"

with st.form("add_form"):
    keyword = st.text_input("New Target (e.g., 'Cisco', 'Exchange', 'Ransomware')")
    submitted = st.form_submit_button("ADD TARGET", type="primary")
    if submitted and keyword:
        try:
            httpx.post(f"{API}/watchlist/add?keyword={keyword}", timeout=10)
            st.success(f"Target '{keyword.upper()}' acquired.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed: {e}")

st.divider()
st.markdown("<h3>Active Targets</h3>", unsafe_allow_html=True)
try:
    items = httpx.get(f"{API}/watchlist", timeout=10).json()
    if items:
        for item in items:
            st.info(f"🔍 {item['keyword'].upper()}")
    else:
        st.write("No targets acquired. Add a keyword above.")
except Exception as e:
    st.error(f"Backend not reachable: {e}")