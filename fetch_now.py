import asyncio

from app.database import SessionLocal
from app.models import Document, Entity
from app.services.collectors import fetch_rss_feeds, save_documents
from app.services.extractor import extract_entities, persist_entities
from app.services.scoring import compute_all_risk

print("=" * 60)
print("STEP 1: Fetching live news feeds...")
print("=" * 60)

db = SessionLocal()
items = asyncio.run(fetch_rss_feeds())
print(f"\n-> Fetched {len(items)} items")

print("\n" + "=" * 60)
print("STEP 2: Saving new documents...")
print("=" * 60)

saved = save_documents(db, items)
print(f"-> Saved {saved} new documents")

print("\n" + "=" * 60)
print("STEP 3: Extracting entities...")
print("=" * 60)

docs = db.query(Document).all()
for i, doc in enumerate(docs, 1):
    ents = extract_entities(doc.title + " " + doc.content)
    persist_entities(db, doc.id, ents)
    if i % 10 == 0:
        print(f"  processed {i}/{len(docs)}")

print(f"-> Total documents: {db.query(Document).count()}")
print(f"-> Total entities: {db.query(Entity).count()}")

print("\n" + "=" * 60)
print("STEP 4: Computing risk scores...")
print("=" * 60)

updated = compute_all_risk(db)
print(f"-> Updated {updated} entities")

print("\n✅ Done. Refresh your Streamlit browser tab!")
db.close()