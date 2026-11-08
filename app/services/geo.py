from app.models import Document, Entity
from sqlalchemy.orm import Session


CENTROIDS = {
    "United States": (39.8, -98.6),
    "China": (35.9, 104.2),
    "Russia": (61.5, 105.3),
    "Ukraine": (48.4, 31.2),
    "India": (20.6, 78.9),
    "Brazil": (-14.2, -51.9),
    "United Kingdom": (55.4, -3.4),
    "Germany": (51.2, 10.4),
    "France": (46.2, 2.2),
    "Japan": (36.2, 138.3),
    "Iran": (32.4, 53.7),
    "North Korea": (40.3, 127.5),
    "South Korea": (35.9, 127.8),
    "Israel": (31.0, 34.9),
    "Australia": (-25.3, 133.8),
    "Canada": (56.1, -106.3),
    "Spain": (40.4, -3.7),
    "Italy": (41.9, 12.6),
    "Netherlands": (52.1, 5.3),
    "Poland": (51.9, 19.1),
    "Taiwan": (23.7, 121.0),
    "Vietnam": (14.1, 108.3),
    "Nigeria": (9.1, 8.7),
    "South Africa": (-30.6, 22.9),
    "Turkey": (39.0, 35.2),
    "Mexico": (23.6, -102.6),
    "Argentina": (-38.4, -63.6),
}


def detect_countries(text: str) -> list[str]:
    text_lower = text.lower()
    return [c for c in CENTROIDS if c.lower() in text_lower]


def aggregate_geo(db: Session) -> list[dict]:
    counts: dict[str, int] = {}
    for doc in db.query(Document).all():
        text = (doc.title or "") + " " + (doc.content or "")
        for country in detect_countries(text):
            counts[country] = counts.get(country, 0) + 1

    result = []
    for country, count in counts.items():
        lat, lon = CENTROIDS[country]
        result.append({
            "country": country,
            "count": count,
            "lat": lat,
            "lon": lon,
        })
    return sorted(result, key=lambda x: x["count"], reverse=True)