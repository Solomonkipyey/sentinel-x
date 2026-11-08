import httpx
import pandas as pd
import streamlit as st

API = "http://localhost:8000"

st.set_page_config(page_title="SENTINEL-X", page_icon="🛡️", layout="wide")

st.title("🛡️ SENTINEL-X — Threat Intelligence Console")
st.caption("Live OSINT data • Ethical use only")

@st.cache_data(ttl=30)
def api_get(path: str):
    try:
        return httpx.get(f"{API}{path}", timeout=30).json()
    except Exception as e:
        st.error(f"⚠️ Backend not reachable at {API}\n\nError: {e}")
        return None

stats = api_get("/stats") or {}
c1, c2, c3 = st.columns(3)
c1.metric("📄 Documents", stats.get("documents", 0))
c2.metric("🎯 Entities", stats.get("entities", 0))
c3.metric("📊 Reports", stats.get("reports", 0))

st.divider()
st.subheader("⚡ Actions")

a1, _ = st.columns([1, 3])
if a1.button("🔄 Fetch live news", use_container_width=True):
    with st.spinner("Fetching..."):
        try:
            r = httpx.post(f"{API}/collect/run", timeout=180)
            data = r.json()
            st.success(
                f"✅ {data.get('new_documents', 0)} new docs • "
                f"{data.get('total_documents', 0)} total docs • "
                f"{data.get('total_entities', 0)} entities"
            )
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Failed: {e}")

st.divider()
st.subheader("🎯 Top Risky Entities")

entities = api_get("/entities?min_risk=0&limit=50") or []

if not entities:
    st.info("No entities yet — click 'Fetch live news' above.")
else:
    df = pd.DataFrame(entities)
    df = df.rename(columns={"kind": "Type", "value": "Value", "risk": "Risk"})
    df = df[["Risk", "Type", "Value"]]
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Risk": st.column_config.ProgressColumn(
                "Risk", min_value=0, max_value=100, format="%.2f"
            ),
        },
    )
    st.subheader("📊 Entities by type")
    st.bar_chart(df.groupby("Type").size())

# ============================================================
# PDF EXPORT SECTION
# ============================================================
st.divider()
st.subheader("📄 Export Intelligence Report")
st.write("Generate a clean, styled HTML intelligence report containing the top 30 riskiest entities.")

if st.button("📥 Generate & Download Report"):
    with st.spinner("Generating report..."):
        try:
            response = httpx.get(f"{API}/export/pdf", timeout=30)
            st.download_button(
                label="💾 Click here to save the report",
                data=response.content,
                file_name="sentinel_x_report.html",
                mime="text/html",
                type="primary"
            )
            st.success("✅ Report generated! Click the button above to save it.")
        except Exception as e:
            st.error(f"Failed to generate report: {e}")

st.caption("SENTINEL-X v0.1 • Public data only • Respect site ToS")