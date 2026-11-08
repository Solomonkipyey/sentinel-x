import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def uuidstr() -> str:
    return str(uuid.uuid4())


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuidstr)
    name: Mapped[str] = mapped_column(String, unique=True)
    url: Mapped[str] = mapped_column(String, default="")
    kind: Mapped[str] = mapped_column(String, default="rss")
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    last_polled: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuidstr)
    source_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("sources.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Entity(Base):
    __tablename__ = "entities"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuidstr)
    kind: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[str] = mapped_column(String, index=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)


class DocumentEntity(Base):
    __tablename__ = "document_entities"
    document_id: Mapped[str] = mapped_column(
        String, ForeignKey("documents.id"), primary_key=True
    )
    entity_id: Mapped[str] = mapped_column(
        String, ForeignKey("entities.id"), primary_key=True
    )


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuidstr)
    title: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String, default="medium")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    ai_analysis: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GeoEvent(Base):
    __tablename__ = "geo_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuidstr)
    entity_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("entities.id"), nullable=True
    )
    country: Mapped[str] = mapped_column(String, index=True)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    description: Mapped[str] = mapped_column(Text, default="")
    # ==========================================
# THE NEW WATCHLIST TABLE
# ==========================================
class Watchlist(Base):
    __tablename__ = "watchlists"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuidstr)
    keyword: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)