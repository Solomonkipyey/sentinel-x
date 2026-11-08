# 🛡️ SENTINEL-X: Open-Source Intelligence & Cyber Threat Analysis Platform

SENTINEL-X is a full-stack OSINT (Open-Source Intelligence) platform that automatically aggregates publicly available cybersecurity data, extracts threat indicators (IOCs), scores their risk, and visualizes relationships between entities. 

It includes a built-in Lead Generator to identify companies recently mentioned in breach articles, making it a powerful tool for B2B cybersecurity sales and threat hunting.

---

## 🚀 Features

- **Automated OSINT Collection:** Scrapes live RSS feeds (BleepingComputer, The Hacker News, Krebs) and extracts full-text articles.
- **IOC Extraction:** Uses Regular Expressions to automatically identify CVEs, IP addresses, domains, MD5/SHA256 hashes, and emails.
- **Risk Scoring Engine:** Calculates risk scores (0-100) based on severity, recency, and frequency of mentions.
- **Threat Graph:** Visualizes relationships between CVEs, domains, and IPs using NetworkX and PyVis.
- **Global Threat Map:** Geographically maps threat mentions using Folium and Streamlit-Folium.
- **Client Lead Generator:** Identifies companies mentioned in ransomware/breach news and auto-generates personalized B2B outreach pitches.
- **AI Integration:** Uses OpenAI to generate executive summaries and map threats to MITRE ATT&CK TTPs.
- **Auto-Pilot:** Background scheduler (APScheduler) fetches new intel every 30 minutes.
- **Export Reports:** Generates professional HTML/PDF intelligence briefs for clients.
- **Authentication:** Secure login system with custom CSS (Dark Slate & Cyan theme).
## 📸 Screenshots

<img width="1811" height="910" alt="Screenshot 2026-11-09 002359" src="https://github.com/user-attachments/assets/43ad9f2f-90c3-46b6-b551-ef0d3026d61b" />
<img width="1857" height="777" alt="Screenshot 2026-11-09 002420" src="https://github.com/user-attachments/assets/46c3028a-f667-4153-ac1c-d123a5244855" />
<img width="1897" height="648" alt="Screenshot 2026-11-09 002431" src="https://github.com/user-attachments/assets/67dd7b12-f9f4-41d6-aa9b-cd3a2d825e71" />
<img width="1761" height="523" alt="Screenshot 2026-11-09 002440" src="https://github.com/user-attachments/assets/b0b47b84-0c01-40af-80cd-8654df949060" />
<img width="1452" height="874" alt="Screenshot 2026-11-09 002450" src="https://github.com/user-attachments/assets/eb932bf4-bace-401d-bdb1-483aeda15581" />

## 🛠️ Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy
- **Frontend:** Streamlit, Pandas
- **Database:** SQLite
- **Graph & Mapping:** NetworkX, PyVis, Folium
- **AI & Automation:** OpenAI API, APScheduler
- **Security:** Custom Session State Auth

## 💻 How to Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/Solomonkipyey/sentinel-x.git
cd sentinel-x

## 2.⚖️ Ethical Use & Disclaimer
SENTINEL-X is built for defensive cybersecurity and threat intelligence purposes only. It only collects publicly available data (OSINT) and respects the Terms of Service of the sources it scrapes.
Do not use this tool for unauthorized access, exploitation, or malicious activities.

👨‍💻 Author
Solomon Kipyey

GitHub: @Solomonkipyey
email:skipyey@gmail.com
