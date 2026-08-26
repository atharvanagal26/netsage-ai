# NetSage AI — Network Troubleshooting Assistant

NetSage AI is an AI-assisted troubleshooter for Cisco Packet Tracer lab environments. It processes network symptoms, topology context, and Cisco IOS `show` command outputs to identify likely root causes, specify OSI layers, recommend next steps, and suggest evidence-backed configuration fixes[cite: 1]. 

To ensure safety and diagnostic accuracy, NetSage AI follows a **Human-in-the-Loop (HITL)** architecture: a human reviewer must evaluate, edit, or approve every AI-generated diagnosis before applying fixes[cite: 1].

---

## 🚀 Key Features

* **Deterministic Rule Checker (`checker.py`):** Runs automated Python checks to detect common static configuration errors (e.g., interface down, missing VLANs, subnet mask mismatches).
* **LLM Diagnostic Engine (`llm_engine.py`):** Utilizes structured prompt templates (`diagnose_prompt.md`) enforcing JSON-formatted output containing root cause analysis, evidence extraction, confidence score, and fix steps.
* **Human Oversight & Review Log:** Captures human reviewer decisions (`Accepted`, `Edited`, `Rejected`) and tracks audit records for cases where AI recommendations required human correction[cite: 1].
* **Interactive Dashboard (`app.py`):** A Streamlit dashboard displaying fault distribution, severity levels, and AI vs. Human agreement analytics.

---

## 📁 Repository Structure

```text
netsage-ai/
├── data/
│   └── cases.csv                # 30 Cisco Packet Tracer troubleshooting lab cases
├── src/
│   ├── checker.py              # Rule-based validation script for static config errors
│   ├── llm_engine.py           # LLM API integration and JSON schema parser
│   └── diagnose_prompt.md      # Structured system prompts and worked examples
├── app.py                      # Streamlit UI dashboard and human review workflow
├── NetSage_AI_Guide.docx       # Project documentation and handbook
├── requirements.txt            # Python dependencies
└── README.md                   # Project overview & documentation

