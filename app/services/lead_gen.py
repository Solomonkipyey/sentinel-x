from sqlalchemy.orm import Session
from app.models import Document, Entity, DocumentEntity

def generate_leads(db: Session) -> list[dict]:
    """
    Scans recent documents for domains/companies that might need security help.
    """
    leads = []
    
    # Get the 50 most recent documents
    docs = db.query(Document).order_by(Document.fetched_at.desc()).limit(50).all()
    
    for doc in docs:
        # Look for breach-related keywords
        text = (doc.title + " " + doc.content).lower()
        if any(word in text for word in ["breach", "hacked", "ransomware", "leak", "compromised"]):
            
            # Find linked entities for this document
            entities = db.query(Entity).join(DocumentEntity).filter(
                DocumentEntity.document_id == doc.id,
                Entity.kind == "domain"
            ).all()
            
            for ent in entities:
                # Filter out noise domains (news sites, github, etc.)
                if not any(x in ent.value for x in ["bleepingcomputer", "hackernews", "krebs", "github", "twitter", "google", "microsoft", "schema.org"]):
                    leads.append({
                        "domain": ent.value,
                        "context": doc.title,
                        "url": doc.url,
                        "pitch": f"Hi team at {ent.value},\n\nI saw your company was mentioned in a recent cybersecurity article: '{doc.title}'.\n\nI run a threat intelligence platform that monitors the web for threats targeting companies like yours. I'd love to send you a free 3-day trial report.\n\nBest,\nSolomon"
                    })
                    
    # Remove duplicates
    unique_leads = {lead["domain"]: lead for lead in leads}.values()
    return list(unique_leads)