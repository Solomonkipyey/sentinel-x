import folium
import httpx
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Threat Map", page_icon="🌍", layout="wide")
st.title("🌍 Global Threat Map")
st.caption("Threats mentioned per country in collected articles")

API = "http://localhost:8000"

try:
    data = httpx.get(f"{API}/geo/threats", timeout=30).json()
except Exception as e:
    st.error(f"Cannot reach API: {e}")
    st.stop()

if not data:
    st.info("No geo data yet — run collection first")
    st.stop()

df = pd.DataFrame(data)

m = folium.Map(
    location=[20, 0],
    zoom_start=2,
    tiles="cartoDB dark_matter",
    prefer_canvas=True,
)

max_count = df["count"].max()

for _, row in df.iterrows():
    radius = 5 + (row["count"] / max_count) * 25
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=radius,
        color="#ff4d4d",
        fill=True,
        fill_color="#ff4d4d",
        fill_opacity=0.5,
        weight=2,
        popup=f"<b>{row['country']}</b><br>{row['count']} threats",
        tooltip=f"{row['country']}: {row['count']}",
    ).add_to(m)

st_folium(m, width=1400, height=600)

st.subheader("Top target countries")
top = df.sort_values("count", ascending=False).head(10)
st.bar_chart(top.set_index("country")["count"])