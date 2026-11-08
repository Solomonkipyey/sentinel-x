# ==========================================
# 1. IMPORTS (MUST BE AT THE VERY TOP)
# ==========================================
import datetime
import uuid
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models
from app.services.collectors import fetch_rss_feeds, save_documents
from app.services.extractor import extract_entities, persist_entities
from app.services.scoring import compute_all_risk
from app.services.graph import build_graph, graph_to_json
from app.services.geo import aggregate_geo
from app.services.ai_analyst import analyze_document

# ==========================================
# 2. SETUP
# ==========================================
Base.metadata.create_all(engine)

app = FastAPI(title="SENTINEL-X", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Jinja2 for HTML templates
env = Environment(loader=FileSystemLoader("app/templates"))


# ==========================================
# 3. ENDPOINTS
# ==========================================
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    return {
        "documents": db.query(models.Document).count(),
        "entities": db.query(models.Entity).count(),
        "reports": db.query(models.Report).count(),
    }

@app.post("/collect/run")
async def collect(db: Session = Depends(get_db)):
    items = await fetch_rss_feeds()
    saved = save_documents(db, items)

    processed = 0
    for doc in db.query(models.Document).all():
        ents = extract_entities(doc.title + " " + doc.content)
        if persist_entities(db, doc.id, ents) > 0:
            processed += 1

    compute_all_risk(db)
    return {
        "new_documents": saved,
        "documents_processed": processed,
        "total_documents": db.query(models.Document).count(),
        "total_entities": db.query(models.Entity).count(),
    }

@app.get("/entities")
def entities(min_risk: float = 0, limit: int = 100, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Entity)
        .filter(models.Entity.risk_score >= min_risk)
        .order_by(models.Entity.risk_score.desc())
        .limit(limit)
        .all()
    )
    return [
        {"id": e.id, "kind": e.kind, "value": e.value, "risk": e.risk_score}
        for e in rows
    ]

@app.get("/graph")
def graph(db: Session = Depends(get_db)):
    return graph_to_json(build_graph(db))

@app.get("/geo/threats")
def geo_threats(db: Session = Depends(get_db)):
    return aggregate_geo(db)

@app.get("/documents")
def documents(limit: int = 20, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Document)
        .order_by(models.Document.fetched_at.desc())
        .limit(limit)
        .all()
    )
    return [{"id": d.id, "title": d.title, "url": d.url} for d in rows]

@app.post("/analyze/{doc_id}")
def analyze(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter_by(id=doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return analyze_document(doc)

@app.get("/export/pdf")
def export_pdf(db: Session = Depends(get_db)):
    entities = db.query(models.Entity).order_by(models.Entity.risk_score.desc()).limit(30).all()
    template = env.get_template("report.html")
    html_content = template.render(
        report_id=str(uuid.uuid4())[:8].upper(),
        date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        entities=entities
    )
    headers = {
        "Content-Disposition": f"attachment; filename=sentinel_x_report.html"
    }
    return HTMLResponse(content=html_content, headers=headers)