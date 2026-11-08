import httpx
import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="SENTINEL-X", page_icon="🛡️", layout="wide")

# ==========================================
# CUSTOM LOGIN SYSTEM (Professional)
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Center the login box
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h1 style='text-align: center; color: #38bdf8;'>🛡️ SENTINEL-X</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Secure Authentication</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("LOGIN", use_container_width=True)
            
            if submit:
                if username == "solomon" and password == "Drsolomon96":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    st.stop()

# ==========================================
# LOAD CUSTOM CSS
# ==========================================
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    load_css(css_path)

# ==========================================
# DASHBOARD CONTENT
# ==========================================
API = "http://localhost:8000"

st.sidebar.markdown("### System Status")
st.sidebar.success("🟢 Online")
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

st.title("🛡️ SENTINEL-X Threat Intelligence")
st.markdown("---")

@st.cache_data(ttl=30)
def api_get(path: str):
    try:
        return httpx.get(f"{API}{path}", timeout=30).json()
    except Exception as e:
        st.error(f"⚠️ Backend not reachable. Is Uvicorn running?\n\nError: {e}")
        return None

stats = api_get("/stats") or {}

# Metric Cards
col1, col2, col3 = st.columns(3)
col1.metric("Documents Analyzed", stats.get("documents", 0))
col2.metric("Threat Indicators", stats.get("entities", 0))
col3.metric("Reports Generated", stats.get("reports", 0))

st.markdown("---")

# Action Center
st.subheader("⚡ Action Center")
a1, a2, a3 = st.columns([1, 2, 1])
with a2:
    if st.button("🔄 Fetch Live Threat Intel", use_container_width=True, type="primary"):
        with st.spinner("Scraping global news feeds..."):
            try:
                r = httpx.post(f"{API}/collect/run", timeout=180)
                data = r.json()
                st.success(f"✅ Collected {data.get('new_documents', 0)} new documents.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Collection failed: {e}")

st.markdown("---")

# Threat Table
st.subheader("🎯 Active Threat Vectors")
entities = api_get("/entities?min_risk=0&limit=50") or []

if not entities:
    st.info("No indicators found. Run a collection above.")
else:
    df = pd.DataFrame(entities)
    df = df.rename(columns={"kind": "Type", "value": "Indicator", "risk": "Risk Score"})
    df = df[["Risk Score", "Type", "Indicator"]]
    
    c1, c2, c3 = st.columns([1, 10, 1])
    with c2:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Risk Score": st.column_config.ProgressColumn(
                    "Risk Score", min_value=0, max_value=100, format="%.2f"
                ),
            },
        )

# Report Export
st.markdown("---")
st.subheader("📄 Export Intelligence")
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    if st.button("Generate PDF Brief", use_container_width=True):
        with st.spinner("Compiling report..."):
            try:
                response = httpx.get(f"{API}/export/pdf", timeout=30)
                st.download_button(
                    label="💾 Download Report",
                    data=response.content,
                    file_name="sentinel_x_report.html",
                    mime="text/html",
                    type="primary"
                )
            except Exception as e:
                st.error(f"Export failed: {e}")

st.caption("SENTINEL-X v1.0 • All Systems Operational • Confidential")