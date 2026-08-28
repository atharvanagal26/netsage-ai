import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root and src directory to Python path for clean imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "src"))

# --- RULE CHECKER & LLM ENGINE IMPORTS ---
try:
    from src.checker import run_rule_checker, get_rule_stats
except ImportError:
    from checker import run_rule_checker, get_rule_stats

try:
    from src.llm_engine import diagnose_case
except ImportError:
    try:
        from llm_engine import diagnose_case
    except ImportError:
        diagnose_case = None

# Page Setup
st.set_page_config(
    page_title="NetSage AI | Enterprise Network Diagnostics",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CISCO NOC DASHBOARD STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    section[data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1e293b; }
    .cisco-brand { color: #00bceb; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; font-size: 0.85rem; }
    .main-title { color: #ffffff; font-size: 2.2rem; font-weight: 800; margin-bottom: 0.2rem; }
    .noc-card { background-color: #151e32; border: 1px solid #1e293b; border-radius: 8px; padding: 18px; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); }
    .noc-header { font-size: 1.1rem; font-weight: 600; color: #38bdf8; border-bottom: 1px solid #1e293b; padding-bottom: 8px; margin-bottom: 12px; }
    .metric-box { background-color: #1e293b; padding: 12px; border-radius: 6px; text-align: center; border: 1px solid #334155; }
    .metric-value { font-size: 1.6rem; font-weight: 700; }
    .metric-pass { color: #22c55e; }
    .metric-fail { color: #ef4444; }
    .metric-total { color: #38bdf8; }
    .rule-pass { background-color: rgba(34, 197, 94, 0.1); border: 1px solid #15803d; color: #4ade80; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; }
    .rule-fail { background-color: rgba(239, 68, 68, 0.1); border: 1px solid #b91c1c; color: #f87171; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; }
    .rule-warn { background-color: rgba(245, 158, 11, 0.1); border: 1px solid #b45309; color: #fbbf24; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px; }
    .cli-box { background-color: #030712; border: 1px solid #1f2937; color: #38bdf8; font-family: monospace; padding: 10px 14px; border-radius: 6px; font-size: 0.9rem; margin-bottom: 6px; }
</style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown('<div class="cisco-brand">⚡ CISCO-STYLE NOC CONTROL CENTER</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">NetSage AI: Network Incident Diagnostics</div>', unsafe_allow_html=True)
st.caption("Automated Layered Troubleshooting: Layer 1 Rules + Layer 2 LLM Reasoning + Layer 3 Responsible AI")
st.markdown("---")

# --- DATASET LOADING ---
csv_path = "cases.csv" if os.path.exists("cases.csv") else "data/cases.csv"
if not os.path.exists(csv_path):
    st.error("⚠️ `cases.csv` missing!")
    st.stop()

df = pd.read_csv(csv_path)

# --- SIDEBAR CONTROL ---
st.sidebar.markdown("### 📋 Case Incident Selector")
selected_case_id = st.sidebar.selectbox("Select Active Incident", df["case_id"].unique())
case_data = df[df["case_id"] == selected_case_id].iloc[0]

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Incident Context")
st.sidebar.markdown("**Reported Symptom:**")
st.sidebar.info(case_data.get('symptom', 'N/A'))
st.sidebar.markdown("**Topology Note:**")
st.sidebar.warning(case_data.get('topology_note', 'N/A'))

show_outputs_val = case_data.get('show_outputs', case_data.get('show_command', ''))

# --- MAIN DASHBOARD LAYOUT ---
col1, col2 = st.columns([1, 1], gap="medium")

# =========================================================
# COLUMN 1: DETERMINISTIC RULE CHECKER (MEMBER 2)
# =========================================================
with col1:
    st.markdown('<div class="noc-card"><div class="noc-header">⚡ Layer 1: Deterministic Rule Checker</div>', unsafe_allow_html=True)
    
    combined_text = f"{case_data.get('symptom', '')} {case_data.get('topology_note', '')} {show_outputs_val}"
    rule_results = run_rule_checker(combined_text)
    stats = get_rule_stats(rule_results)
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f'<div class="metric-box"><div style="font-size:0.75rem;color:#94a3b8;">EVALUATED</div><div class="metric-value metric-total">{stats["total"]}</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><div style="font-size:0.75rem;color:#94a3b8;">PASSED</div><div class="metric-value metric-pass">{stats["pass"]}</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box"><div style="font-size:0.75rem;color:#94a3b8;">FLAGGED</div><div class="metric-value metric-fail">{stats["fail"] + stats["warn"]}</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Diagnostic Rule Log")
    
    for res in rule_results:
        if res["status"] == "FAIL":
            st.markdown(f'<div class="rule-fail">❌ <b>{res["check"]}</b><br><small>{res["message"]}</small></div>', unsafe_allow_html=True)
        elif res["status"] == "WARN":
            st.markdown(f'<div class="rule-warn">⚠️ <b>{res["check"]}</b><br><small>{res["message"]}</small></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="rule-pass">✅ <b>{res["check"]}</b><br><small>{res["message"]}</small></div>', unsafe_allow_html=True)
            
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# COLUMN 2: LLM DIAGNOSIS (MEMBER 3) & AUDIT LOG (MEMBER 4)
# =========================================================
with col2:
    st.markdown('<div class="noc-card"><div class="noc-header">🧠 Layer 2: LLM Diagnostic Engine</div>', unsafe_allow_html=True)
    
    if st.button("🚀 Run AI Deep Diagnosis", type="primary", use_container_width=True):
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            st.warning("⚠️ No API key found (`GROQ_API_KEY` or `OPENAI_API_KEY`). Displaying static fallback data.")
            ai_output = {
                "case_id": selected_case_id,
                "diagnosis": "VLAN tagging mismatch between switch port and router subinterface.",
                "fault_category": "VLAN",
                "severity": "High",
                "confidence": 0.92,
                "root_cause": f"Mismatched VLAN configuration for {selected_case_id}.",
                "explanation": "Client traffic is untagged or assigned to incorrect PVID while trunk expects 802.1Q encapsulated packets.",
                "recommended_actions": [
                    "Verify switchport access vlan on switch port",
                    "Check encapsulation dot1Q settings on router gateway"
                ],
                "verification_commands": [
                    "show vlan brief",
                    "show interfaces trunk"
                ],
                "evidence": [],
                "deterministic_status": "FAIL",
                "needs_human_review": True
            }
            st.session_state["ai_output"] = ai_output
        elif diagnose_case is None:
            st.error("⚠️ Import Error: Could not locate `diagnose_case` in `src/llm_engine.py`.")
        else:
            with st.spinner("Analyzing telemetry via LLM Engine..."):
                try:
                    ai_output = diagnose_case(
                        case_id=str(selected_case_id),
                        symptom=str(case_data.get("symptom", "")),
                        topology_note=str(case_data.get("topology_note", "")),
                        show_outputs=str(show_outputs_val),
                        deterministic_results=rule_results
                    )
                    st.session_state["ai_output"] = ai_output
                except Exception as e:
                    st.error(f"Execution Error: {str(e)}")

    if "ai_output" in st.session_state:
        ai = st.session_state["ai_output"]
        
        if ai.get("needs_human_review", False):
            st.warning("⚠️ **Human Review Flagged:** LLM requested engineer review.")
        
        st.markdown("#### Root Cause Identification")
        st.error(f"**Root Cause:** {ai.get('root_cause', 'N/A')}")
        
        st.markdown(f"**Explanation:** {ai.get('explanation', 'N/A')}")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**Category:** `{ai.get('fault_category', 'N/A')}`")
        with c2:
            st.markdown(f"**Severity:** `{ai.get('severity', 'N/A')}`")
        with c3:
            conf = ai.get('confidence', 0.0)
            conf_str = f"{conf * 100:.0f}%" if isinstance(conf, (int, float)) else str(conf)
            st.markdown(f"**Confidence:** `{conf_str}`")
            
        st.markdown("**Verification Commands:**")
        verif_cmds = ai.get("verification_commands", [])
        if isinstance(verif_cmds, str):
            verif_cmds = [verif_cmds]
        for cmd in verif_cmds:
            st.markdown(f'<div class="cli-box">$ {cmd}</div>', unsafe_allow_html=True)
        
        st.markdown("**Recommended Remediation Actions:**")
        actions = ai.get("recommended_actions", [])
        if isinstance(actions, str):
            actions = [actions]
        for idx, act in enumerate(actions, 1):
            st.markdown(f"{idx}. {act}")
            
        st.markdown("---")
        
        # MEMBER 4 RESPONSIBLE AI LOGGING
        st.markdown("#### 🛡️ Layer 3: Responsible AI Engineer Review")
        
        action = st.radio("Engineer Decision:", ["ACCEPT", "EDIT", "REJECT"], horizontal=True)
        
        default_notes = "\n".join(actions) if isinstance(actions, list) else str(actions)
        corrected_fix = st.text_area("Engineer Override / Audit Notes:", value=default_notes, height=90)
        
        if st.button("💾 Save Audit Entry", use_container_width=True):
            log_file = "responsible_ai_log.csv"
            log_entry = pd.DataFrame([{
                "case_id": selected_case_id,
                "action": action,
                "fault_category": ai.get("fault_category"),
                "severity": ai.get("severity"),
                "root_cause": ai.get("root_cause"),
                "corrected_fix": corrected_fix
            }])
            log_entry.to_csv(log_file, mode="a", header=not os.path.exists(log_file), index=False)
            st.success(f"Audit log entry appended to `{log_file}`!")

    st.markdown('</div>', unsafe_allow_html=True)