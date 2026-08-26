<h1 align="center">🌐 NetSage AI</h1>

<p align="center">
  <b>An AI-Assisted Network Troubleshooting Helper with Human-in-the-Loop Review</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Streamlit-1.25+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Cisco-Packet%20Tracer-1BA0D7?style=for-the-badge&logo=cisco&logoColor=white" alt="Cisco" />
  <img src="https://img.shields.io/badge/OpenAI-LLM Engine-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI" />
</p>

---

## 📖 About Project

**NetSage AI** helps junior network engineers bridge the gap between running commands and identifying real root causes in Cisco Packet Tracer lab networks[cite: 1]. 

The system analyzes symptoms, topology context, and Cisco IOS `show` command outputs to suggest probable root causes, OSI failure layers, next commands, and evidence-backed fixes—all while enforcing mandatory human review before applying a fix[cite: 1].

---

## ⚡ Key Features

* 🔍 **Deterministic Rule Checker:** Fast Python validation to catch static configuration mistakes (interface down, subnet mask mismatch, missing VLANs/routes).
* 🤖 **Structured AI Diagnosis:** Prompt-engineered LLM integration outputting strict JSON schema (`root_cause`, `evidence`, `confidence`, `fix_steps`).
* 🛡️ **Human-in-the-Loop Oversight:** Formal decision logging (`Accepted`, `Edited`, `Rejected`) to ensure safe operational deployment[cite: 1].
* 📊 **Analytics Dashboard:** Streamlit interface tracking issue categories, severity levels, and AI vs. Human agreement rates.

---

## 📂 Repository Structure

```text
netsage-ai/
├── data/
│   └── cases.csv                # 30 Cisco Packet Tracer troubleshooting lab cases
├── src/
│   ├── checker.py              # Deterministic rule-based script
│   ├── llm_engine.py           # LLM API integration engine
│   └── diagnose_prompt.md      # Structured prompt template with worked examples
├── app.py                      # Interactive Streamlit dashboard
├── requirements.txt            # Project dependencies
└── README.md                   # Repository documentation

