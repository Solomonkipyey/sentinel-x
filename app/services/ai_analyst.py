import json

from app.config import settings
from app.models import Document


def analyze_document(doc: Document) -> dict:
    if not settings.OPENAI_API_KEY:
        return {
            "summary": "[AI disabled — add OPENAI_API_KEY to .env to enable AI analysis]",
            "threat_actors": [],
            "ttps": [],
            "affected_products": [],
            "severity": "medium",
            "reasoning": "offline stub",
        }

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        prompt = f"""You are a cyber threat analyst. Analyze this OSINT item.
Return STRICT JSON with keys:
summary (2-3 sentences), threat_actors (list), ttps (list of MITRE ATT&CK IDs),
affected_products (list), severity (low|medium|high|critical),
reasoning (1 sentence).

Title: {doc.title}
Content: {doc.content[:4000]}
"""
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(resp.choices[0].message.content)
    
    except Exception as e:
        # If OpenAI fails (no credits, bad key, etc.), don't crash. Show the error nicely.
        return {
            "summary": f"⚠️ OpenAI Error: {str(e)}",
            "threat_actors": [],
            "ttps": [],
            "affected_products": [],
            "severity": "medium",
            "reasoning": "API failure",
        }