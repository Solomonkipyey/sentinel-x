import math
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import DocumentEntity, Entity


def compute_all_risk(db: Session) -> int:
    updated = 0
    for ent in db.query(Entity).all():
        mentions = db.query(func.count(DocumentEntity.document_id)).filter(
            DocumentEntity.entity_id == ent.id
        ).scalar() or 0
        
        if mentions == 0:
            ent.risk_score = 0.0
            updated += 1
            continue
            
        cve_boost = 30.0 if ent.kind == "cve" else 0.0
        age_days = max(0, (datetime.utcnow() - ent.last_seen).days)
        recency = math.exp(-age_days / 30)
        
        score = min(100.0, (20 * math.log(1 + mentions) + cve_boost) * recency)
        ent.risk_score = round(score, 2)
        updated += 1
        
    db.commit()
    return updated