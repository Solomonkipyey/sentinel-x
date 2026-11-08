import streamlit as st
import httpx
from pathlib import Path

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("Please log in on the main page.")
    st.stop()

st.set_page_config(page_title="Enterprise Tools", page_icon="🛡️", layout="wide")

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
css_path = Path(__file__).parent.parent / "assets" / "style.css"
if css_path.exists():
    load_css(css_path)

st.markdown("<h1>🛡️ Enterprise Threat Tools</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #888;'>Advanced tools with actionable remediation steps</p>", unsafe_allow_html=True)

API = "http://localhost:8000"

tab1, tab2 = st.tabs(["🔍 Dark Web Breach Checker", "🎭 Brand Impersonation Scanner"])

# --- TAB 1: BREACH CHECKER ---
with tab1:
    st.subheader("Check if an email was leaked")
    st.write("Enter a client's email (e.g., `ceo@company.com`) to see if their password was stolen.")
    
    email = st.text_input("Email Address")
    if st.button("Scan Dark Web", type="primary"):
        if email:
            with st.spinner("Scanning breach databases..."):
                try:
                    res = httpx.get(f"{API}/breach-check/{email}", timeout=15).json()
                    
                    if res.get("status") == "breached":
                        st.error(f"🚨 **BREACHED!** Found in {res.get('count')} data breaches.")
                        st.write(f"**Breaches:** {', '.join(res.get('breaches'))}")
                        st.warning("⚠️ **Actionable Remediation Plan**")
                        st.markdown(res.get("remediation", ""), unsafe_allow_html=True)
                    elif res.get("status") == "safe":
                        st.success("✅ Clean. No known breaches found for this email.")
                    else:
                        st.info(f"Notice: {res.get('message')}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

# --- TAB 2: IMPERSONATION ---
with tab2:
    st.subheader("Scan for Fake Domains")
    st.write("Enter a client's domain (e.g., `paypal.com`) to find lookalike phishing sites.")
    
    domain = st.text_input("Company Domain")
    
    # Use session_state to remember the scan results
    if "scan_results" not in st.session_state:
        st.session_state.scan_results = None

    if st.button("Scan for Fakes", type="primary"):
        if domain:
            with st.spinner("Searching certificate transparency logs..."):
                try:
                    fakes = httpx.get(f"{API}/impersonation-check/{domain}", timeout=20).json()
                    st.session_state.scan_results = fakes
                    st.session_state.scanned_domain = domain
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    # Display results if they exist in session state
    if st.session_state.scan_results is not None:
        fakes = st.session_state.scan_results
        domain = st.session_state.scanned_domain
        
        if not fakes:
            st.success("✅ No suspicious domains found. Brand is currently protected.")
        else:
            st.error(f"🚨 Found {len(fakes)} suspicious domains impersonating your brand!")
            
            for fake in fakes:
                color = "red" if fake["score"] > 70 else "orange"
                st.markdown(f"<span style='color:{color}; font-size:18px;'>⚠️ {fake['domain']} (Risk: {fake['score']}/100)</span>", unsafe_allow_html=True)
            
            st.warning("⚠️ **Actionable Remediation Plan**")
            try:
                remediation_text = httpx.get(f"{API}/remediation/{domain}", timeout=10).json().get("remediation", "")
                st.markdown(remediation_text, unsafe_allow_html=True)
            except:
                st.write("Could not load remediation.")
            
            # --- DOWNLOAD REPORT SECTION ---
            st.divider()
            st.write("### 📄 Export Client Report")
            st.write("Generate a branded HTML report to send to the client.")
            
            # Generate the report immediately so the download button appears
            try:
                with st.spinner("Preparing report..."):
                    response = httpx.get(f"{API}/export-enterprise/{domain}", timeout=20)
                    if response.status_code == 200:
                        st.download_button(
                            label="💾 Download Threat Report",
                            data=response.content,
                            file_name=f"{domain}_Threat_Report.html",
                            mime="text/html",
                            type="primary"
                        )
                        st.success("✅ Report ready! Click above to download.")
                    else:
                        st.error(f"Backend error: {response.status_code}")
            except Exception as e:
                st.error(f"Failed to generate: {e}")