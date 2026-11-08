import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import DocumentEntity, Entity


PATTERNS = {
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "domain": re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.I),
    "cve": re.compile(r"CVE-\d{4}-\d{4,7}", re.I),
    "md5": re.compile(r"\b[a-f0-9]{32}\b", re.I),
    "sha256": re.compile(r"\b[a-f0-9]{64}\b", re.I),
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
}

# Reduced noise to catch more real domains
NOISE = {"schema.org", "w3.org", "w3.com"}


def _is_private_ip(ip: str) -> bool:
    try:
        parts = [int(p) for p in ip.split(".")]
    except ValueError:
        return True
    if parts[0] == 10:
        return True
    if parts[0] == 192 and parts[1] == 168:
        return True
    if parts[0] == 172 and 16 <= parts[1] <= 31:
        return True
    return False


def extract_entities(text: str) -> list[tuple[str, str]]:
    found = set()
    for kind, pat in PATTERNS.items():
        for m in pat.findall(text):
            val = m.lower() if kind in ("domain", "md5", "sha256") else m
            if kind == "domain" and val in NOISE:
                continue
            if kind == "ipv4" and _is_private_ip(val):
                continue
            found.add((kind, val))
    return list(found)


def persist_entities(db: Session, doc_id: str, entities: list[tuple[str, str]]) -> int:
    added = 0
    for kind, value in entities:
        ent = db.query(Entity).filter_by(kind=kind, value=value).first()
        if not ent:
            ent = Entity(kind=kind, value=value)
            db.add(ent)
            db.commit()
            db.refresh(ent)
        else:
            ent.last_seen = datetime.utcnow()
            db.commit()
        link = db.query(DocumentEntity).filter_by(
            document_id=doc_id, entity_id=ent.id
        ).first()
        if not link:
            db.add(DocumentEntity(document_id=doc_id, entity_id=ent.id))
            added += 1
    db.commit()
    return added