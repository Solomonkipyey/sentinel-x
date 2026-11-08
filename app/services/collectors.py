import hashlib
import re
from datetime import datetime

import feedparser
import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Document, Source


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clean_html(html: str) -> str:
    """Strips HTML tags to get raw text for regex extraction."""
    text = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL | re.I)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def fetch_rss_feeds() -> list[dict]:
    items = []
    async with httpx.AsyncClient(
        timeout=20.0,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SENTINEL-X/0.1"},
        follow_redirects=True,
    ) as client:
        for feed_url in settings.NEWS_FEEDS.split(","):
            feed_url = feed_url.strip()
            if not feed_url:
                continue
            try:
                resp = await client.get(feed_url)
                parsed = feedparser.parse(resp.text)
                source_name = parsed.feed.get("title", feed_url)
                
                # Limit to 5 articles per feed so it doesn't take forever
                for entry in parsed.entries[:5]:
                    url = entry.get("link", "")
                    summary = entry.get("summary", entry.get("description", ""))
                    
                    # Fetch the full article text
                    full_content = summary
                    if url:
                        try:
                            article_resp = await client.get(url)
                            if article_resp.status_code == 200:
                                full_content = _clean_html(article_resp.text)
                        except Exception:
                            pass # Fallback to summary if article fetch fails
                    
                    items.append({
                        "title": entry.get("title", ""),
                        "url": url,
                        "content": full_content, # Now contains the FULL article text!
                        "source": source_name,
                    })
                print(f"[collector] {source_name}: fetched {len(parsed.entries[:5])} full articles")
            except Exception as e:
                print(f"[collector] {feed_url} failed: {e}")
    return items


def save_documents(db: Session, items: list[dict]) -> int:
    saved = 0
    for it in items:
        h = _hash(it["title"] + it["content"])
        if db.query(Document).filter_by(content_hash=h).first():
            continue
        src = db.query(Source).filter_by(name=it["source"]).first()
        if not src:
            src = Source(name=it["source"], url="", kind="rss")
            db.add(src)
            db.commit()
            db.refresh(src)
        db.add(Document(
            source_id=src.id,
            title=it["title"],
            url=it["url"],
            content=it["content"],
            content_hash=h,
            fetched_at=datetime.utcnow(),
        ))
        saved += 1
    db.commit()
    return saved