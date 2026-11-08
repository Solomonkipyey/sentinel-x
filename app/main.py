import datetime
import uuid
import smtplib
from email.message import EmailMessage
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db, SessionLocal
from app import models
from app.services.collectors import fetch_rss_feeds, save_documents
from app.services.extractor import extract_entities, persist_entities
from app.services.scoring import compute_all_risk
from app.services.graph import build_graph, graph_to_json
from app.services.geo import aggregate_geo
from app.services.ai_analyst import analyze_document
from app.services.lead_gen import generate_leads
from app.services.enterprise import (
    check_breach, 
    check_impersonation, 
    send_slack_alert, 
    generate_enterprise_report, 
    get_remediation
)

Base.metadata.create_all(engine)
env = Environment(loader=FileSystemLoader("app/templates"))

# ==========================================
# BACKGROUND SCHEDULER
# ==========================================
scheduler = AsyncIOScheduler()

async def auto_fetch_task():
    print("⏰ [AUTO-PILOT] Starting background fetch...")
    db = SessionLocal()
    try:
        items = await fetch_rss_feeds()
        save_documents(db, items)

        watchlist = [w.keyword.lower() for w in db.query(models.Watchlist).all()]
        alerts = []

        for doc in db.query(models.Document).all():
            text = (doc.title + " " + doc.content).lower()
            for keyword in watchlist:
                if keyword in text:
                    alerts.append((keyword, doc.title, doc.url))
                    break

        compute_all_risk(db)

        if alerts and settings.SMTP_EMAIL:
            msg = EmailMessage()
            msg['Subject'] = f"🚨 SENTINEL-X Alert: {len(alerts)} Matches"
            msg['From'] = settings.SMTP_EMAIL
            msg['To'] = settings.SMTP_EMAIL
            body = "SENTINEL-X Alerts:\n\n"
            for keyword, title, url in alerts:
                body += f"🎯 MATCH: {keyword.upper()}\n📰 {title}\n🔗 {url}\n\n"
            msg.set_content(body)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
                smtp.send_message(msg)

        print(f"✅ [AUTO-PILOT] Done. Total docs: {db.query(models.Document).count()}")
    except Exception as e:
        print(f"❌ [AUTO-PILOT] Error: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(auto_fetch_task, "interval", minutes=30, id="fetch_job")
    scheduler.start()
    print("🚀 [SENTINEL-X] Auto-pilot started.")
    yield
    scheduler.shutdown()
    print("🛑 [SENTINEL-X] Auto-pilot stopped.")


app = FastAPI(title="SENTINEL-X", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ==========================================
# CORE ENDPOINTS
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
    rows = db.query(models.Entity).filter(models.Entity.risk_score >= min_risk).order_by(models.Entity.risk_score.desc()).limit(limit).all()
    return [{"id": e.id, "kind": e.kind, "value": e.value, "risk": e.risk_score} for e in rows]

@app.get("/graph")
def graph(db: Session = Depends(get_db)):
    return graph_to_json(build_graph(db))

@app.get("/geo/threats")
def geo_threats(db: Session = Depends(get_db)):
    return aggregate_geo(db)

@app.get("/documents")
def documents(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.query(models.Document).order_by(models.Document.fetched_at.desc()).limit(limit).all()
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
    headers = {"Content-Disposition": "attachment; filename=sentinel_x_report.html"}
    return HTMLResponse(content=html_content, headers=headers)

@app.post("/watchlist/add")
def add_to_watchlist(keyword: str, db: Session = Depends(get_db)):
    existing = db.query(models.Watchlist).filter_by(keyword=keyword.lower()).first()
    if not existing:
        db.add(models.Watchlist(keyword=keyword.lower()))
        db.commit()
    return {"status": "added", "keyword": keyword}

@app.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    items = db.query(models.Watchlist).all()
    return [{"id": w.id, "keyword": w.keyword} for w in items]

@app.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    return generate_leads(db)

# ==========================================
# ENTERPRISE ENDPOINTS
# ==========================================
@app.get("/breach-check/{email}")
def breach_check(email: str):
    return check_breach(email)

@app.get("/impersonation-check/{domain}")
def impersonation_check(domain: str):
    return check_impersonation(domain)

@app.post("/test-slack")
def test_slack():
    success = send_slack_alert("SYSTEM TEST", "SENTINEL-X is now connected to Slack!")
    return {"success": success}

@app.get("/remediation/{domain}")
def remediation(domain: str):
    text = get_remediation("impersonation", domain)
    return {"remediation": text}

@app.get("/export-enterprise/{domain}")
def export_enterprise(domain: str):
    fakes = check_impersonation(domain)
    remediation = get_remediation("impersonation", domain) if fakes else "No immediate action required."
    
    html = generate_enterprise_report(domain, fakes, remediation)
    
    headers = {
        "Content-Disposition": f"attachment; filename=sentinel_x_{domain}_report.html"
    }
    return Response(content=html, media_type="text/html", headers=headers)