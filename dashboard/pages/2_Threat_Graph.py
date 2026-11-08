import streamlit as st
import httpx
from pyvis.network import Network
from pathlib import Path

# Auth Check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Please log in on the main page.")
    st.stop()

st.set_page_config(page_title="Threat Graph", page_icon="🕸️", layout="wide")

# Load CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    load_css(css_path)

st.markdown("<h1>🕸️ Threat Relationship Graph</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #888;'>Entities co-occurring in the same articles</p>", unsafe_allow_html=True)

API = "http://localhost:8000"

try:
    data = httpx.get(f"{API}/graph", timeout=30).json()
except Exception as e:
    st.error(f"Cannot reach API: {e}")
    st.stop()

if not data["nodes"]:
    st.info("No entities yet — go to Home and run 'INITIATE NEWS COLLECTION'")
    st.stop()

KIND_COLORS = {
    "cve": "#ff003c",    # Threat Red
    "ipv4": "#00ffff",   # Cyan
    "domain": "#00ff41", # Matrix Green
    "md5": "#ffff00",    # Yellow
    "sha256": "#ff9900", # Orange
    "email": "#cc00ff",  # Purple
}

net = Network(height="650px", bgcolor="#0a0a0a", font_color="#00ff41", directed=False)

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
    net.add_edge(e["source"], e["target"], value=e["weight"], color="#333333")

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
        f"display:inline-block;border-radius:4px;box-shadow: 0 0 10px {color};'></div> **{kind.upper()}**",
        unsafe_allow_html=True,
    )