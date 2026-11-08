import httpx
import requests
import tldextract
import datetime
from app.config import settings

# ==========================================
# REMEDIATION ENGINE (Actionable Advice)
# ==========================================
def get_remediation(threat_type: str, identifier: str) -> str:
    """Returns professional mitigation steps based on the threat."""
    
    if threat_type == "breach":
        return f"""
<h3>Immediate Actions Required:</h3>
<ol>
    <li><strong>Force Password Reset:</strong> Immediately reset the password for <code>{identifier}</code> and any accounts sharing that password.</li>
    <li><strong>Enable MFA:</strong> Enforce Multi-Factor Authentication (MFA) on the affected account.</li>
    <li><strong>Check Login Logs:</strong> Review Active Directory / Email logs for unauthorized access in the last 30 days.</li>
    <li><strong>Alert the User:</strong> Notify the employee that their credentials were found in a public breach.</li>
</ol>
        """
        
    elif threat_type == "impersonation":
        return f"""
<h3>Immediate Actions Required:</h3>
<ol>
    <li><strong>Report the Domain:</strong> Submit a takedown request to the hosting provider and registrar of <code>{identifier}</code>.</li>
    <li><strong>Warn Customers:</strong> Post a security advisory on your official website warning customers about the fake site.</li>
    <li><strong>Block the Domain:</strong> Add <code>{identifier}</code> to your email gateway blocklist and web proxy.</li>
    <li><strong>Monitor DNS:</strong> Set up alerts for newly registered domains similar to your brand.</li>
</ol>
        """
        
    return "No remediation available."

# ==========================================
# 1. DARK WEB CREDENTIAL CHECKER
# ==========================================
def check_breach(email: str) -> dict:
    url = f"https://leakcheck.io/api/public?check={email}"
    headers = {"User-Agent": "SENTINEL-X-Enterprise"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("found"):
                return {
                    "status": "breached",
                    "count": data.get("count", 0),
                    "breaches": [s.get("name", "Unknown") for s in data.get("sources", [])],
                    "details": data,
                    "remediation": get_remediation("breach", email)
                }
            else:
                return {"status": "safe", "count": 0, "breaches": []}
        else:
            return {"status": "error", "message": f"API Error: {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# 2. BRAND IMPERSONATION DETECTOR
# ==========================================
def check_impersonation(company_domain: str) -> list:
    extracted = tldextract.extract(company_domain)
    base_name = extracted.domain
    
    url = f"https://crt.sh/?q=%25.{base_name}&output=json"
    
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            domains = set(item.get("common_name", "") for item in data if item.get("common_name"))
            
            fake_domains = []
            for d in domains:
                if base_name in d and d != company_domain and not d.endswith(f".{company_domain}"):
                    suspicion_score = 50
                    if "-" in d: suspicion_score += 30
                    if any(word in d for word in ["login", "secure", "update", "verify", "support", "auth", "portal"]): suspicion_score += 40
                    
                    fake_domains.append({"domain": d, "score": min(suspicion_score, 100)})
            
            return sorted(fake_domains, key=lambda x: x["score"], reverse=True)[:10]
    except Exception:
        pass
    return []

# ==========================================
# 3. SLACK ALERTS
# ==========================================
def send_slack_alert(alert_type: str, message: str):
    if not settings.SLACK_WEBHOOK_URL:
        return False
    payload = {"text": f"🚨 *SENTINEL-X ALERT: {alert_type}*\n{message}"}
    try:
        httpx.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=10)
        return True
    except Exception:
        return False

# ==========================================
# 4. PDF REPORT GENERATOR
# ==========================================
def generate_enterprise_report(domain: str, fakes: list, remediation: str) -> str:
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px; }}
            .header {{ border-bottom: 2px solid #38bdf8; padding-bottom: 20px; margin-bottom: 30px; }}
            h1 {{ color: #38bdf8; margin: 0; }}
            h2 {{ color: #38bdf8; margin-top: 30px; }}
            .danger {{ color: #ef4444; font-weight: bold; }}
            .warning {{ background: #1e293b; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ border: 1px solid #334155; padding: 10px; text-align: left; }}
            th {{ background: #1e293b; color: #38bdf8; }}
            .footer {{ margin-top: 50px; font-size: 12px; color: #64748b; text-align: center; border-top: 1px solid #334155; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ SENTINEL-X Intelligence Brief</h1>
            <p><strong>Target Domain:</strong> {domain}</p>
            <p><strong>Report Date:</strong> {date_str}</p>
            <p><strong>Classification:</strong> TLP:AMBER (Confidential)</p>
        </div>

        <h2>Executive Summary</h2>
        <p>SENTINEL-X has detected <span class="danger">{len(fakes)}</span> suspicious domains that appear to be impersonating your brand. These domains are likely being used for phishing attacks, credential harvesting, or brand damage.</p>

        <h2>Detected Impersonations</h2>
        <table>
            <tr>
                <th>Risk Level</th>
                <th>Suspicious Domain</th>
                <th>Threat Type</th>
            </tr>
    """
    
    for f in fakes:
        threat_type = "High Risk Phishing" if f['score'] >= 90 else "Suspicious Domain"
        html += f"""
            <tr>
                <td class="danger">{f['score']}/100</td>
                <td>{f['domain']}</td>
                <td>{threat_type}</td>
            </tr>
        """
        
    html += f"""
        </table>

        <h2>Remediation Plan</h2>
        <div class="warning">
            {remediation}
        </div>

        <div class="footer">
            Generated by SENTINEL-X OSINT Platform | Confidential
        </div>
    </body>
    </html>
    """
    return html