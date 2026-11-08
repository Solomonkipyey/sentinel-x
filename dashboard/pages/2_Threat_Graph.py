import httpx
import streamlit as st
from pyvis.network import Network

st.set_page_config(page_title="Threat Graph", page_icon="🕸️", layout="wide")
st.title("🕸️ Threat Relationship Graph")
st.caption("Entities co-occurring in the same articles")

API = "http://localhost:8000"

try:
    data = httpx.get(f"{API}/graph", timeout=30).json()
except Exception as e:
    st.error(f"Cannot reach API: {e}")
    st.stop()

if not data["nodes"]:
    st.info("No entities yet — go to Home and click 'Fetch live news'")
    st.stop()

KIND_COLORS = {
    "cve": "#ff4d4d",
    "ipv4": "#4da6ff",
    "domain": "#4dff88",
    "md5": "#ffd24d",
    "sha256": "#ff994d",
    "email": "#cc66ff",
}

net = Network(height="650px", bgcolor="#0e1117", font_color="white", directed=False)

for n in data["nodes"]:
    kind = n.get("kind", "unknown")
    risk = n.get("risk", 0)
    net.add_node(
        n["id"],
        label=n.get("value", n["id"])[:30],
        size=10 + risk / 3,
        color=KIND_COLORS.get(kind, "#aaaaaa"),
        title=f"{kind}: {n.get('value')}\nRisk: {risk:.2f}",
    )

for e in data["edges"]:
    net.add_edge(e["source"], e["target"], value=e["weight"])

net.save_graph("data/graph.html")

st.markdown(f"**{len(data['nodes'])} nodes** • **{len(data['edges'])} edges**")

with open("data/graph.html", "r", encoding="utf-8") as f:
    html = f.read()

st.components.v1.html(html, height=680, scrolling=True)

st.markdown("### Legend")
cols = st.columns(len(KIND_COLORS))
for col, (kind, color) in zip(cols, KIND_COLORS.items()):
    col.markdown(
        f"<div style='background:{color};width:20px;height:20px;"
        f"display:inline-block;border-radius:4px'></div> **{kind}**",
        unsafe_allow_html=True,
    )