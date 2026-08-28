"""
llm_engine.py
LLM integration layer for the Network Troubleshooting Diagnosis project.

Responsibilities:
1. Load the diagnosis system prompt from diagnose_prompt.md.
2. Send case evidence to the LLM (Groq or OpenAI).
3. Enforce strict JSON output matching the Diagnosis Pydantic schema.
4. Return a normal Python dictionary to the Streamlit/UI layer.

Install:
    pip install openai pydantic python-dotenv

Environment:
    GROQ_API_KEY=gsk_your_groq_api_key   # Primary API key
    GROQ_MODEL=llama-3.3-70b-versatile   # Default Groq model
    # OR
    OPENAI_API_KEY=your_openai_api_key   # Fallback API key
    OPENAI_MODEL=gpt-4o-mini
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT_PATH = BASE_DIR / "diagnose_prompt.md"

load_dotenv(override=True)


class Evidence(BaseModel):
    source: Literal["deterministic_checker", "show_output", "symptom", "topology", "inference"]
    detail: str


class Diagnosis(BaseModel):
    case_id: str
    diagnosis: str
    fault_category: Literal[
        "VLAN", "DHCP", "DNS", "Routing", "ACL", "NAT", "Wireless", "Unknown"
    ]
    severity: Literal["Low", "Medium", "High", "Critical", "Unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    root_cause: str
    explanation: str
    recommended_actions: list[str]
    verification_commands: list[str]
    evidence: list[Evidence]
    deterministic_status: Literal["PASS", "FAIL", "WARN", "NOT_AVAILABLE"]
    needs_human_review: bool


def load_system_prompt(path: Path = PROMPT_PATH) -> str:
    """Load the project diagnosis prompt from diagnose_prompt.md."""
    if not path.exists():
        raise FileNotFoundError(f"Diagnosis prompt not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def _build_user_input(
    case_id: str,
    symptom: str,
    topology_note: str = "",
    show_outputs: str = "",
    deterministic_results: list[dict[str, Any]] | None = None,
) -> str:
    """Build the evidence-only user message sent to the model."""
    deterministic_results = deterministic_results or []

    return f"""
CASE ID:
{case_id}

SYMPTOM:
{symptom}

TOPOLOGY / ENVIRONMENT:
{topology_note or "Not provided"}

SHOW COMMAND OUTPUT:
{show_outputs or "Not provided"}

DETERMINISTIC CHECKER RESULTS:
{json.dumps(deterministic_results, indent=2)}

IMPORTANT:
Treat the supplied information as evidence. Do not invent command output,
IP addresses, interfaces, routes, VLANs, or configuration that is not present.
If evidence is insufficient, say so and set needs_human_review=true.
""".strip()


def diagnose_case(
    case_id: str,
    symptom: str,
    topology_note: str = "",
    show_outputs: str = "",
    deterministic_results: list[dict[str, Any]] | None = None,
    *,
    client: OpenAI | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Diagnose one networking case using Groq or OpenAI.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    api_key = groq_key or openai_key
    if not api_key and client is None:
        raise RuntimeError("Neither GROQ_API_KEY nor OPENAI_API_KEY is set in environment.")

    is_groq = bool(groq_key) and client is None

    # Initialize client for Groq or OpenAI
    if client is None:
        if is_groq:
            client = OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
        else:
            client = OpenAI(api_key=openai_key)

    # Determine default model
    if model is None:
        if is_groq:
            model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        else:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    system_prompt = load_system_prompt()
    user_input = _build_user_input(
        case_id,
        symptom,
        topology_note,
        show_outputs,
        deterministic_results,
    )

    schema_prompt = (
        f"{system_prompt}\n\n"
        "Respond ONLY with a valid JSON object strictly matching this schema format:\n"
        "{\n"
        '  "case_id": "string",\n'
        '  "diagnosis": "string",\n'
        '  "fault_category": "VLAN" | "DHCP" | "DNS" | "Routing" | "ACL" | "NAT" | "Wireless" | "Unknown",\n'
        '  "severity": "Low" | "Medium" | "High" | "Critical" | "Unknown",\n'
        '  "confidence": 0.0 to 1.0,\n'
        '  "root_cause": "string",\n'
        '  "explanation": "string",\n'
        '  "recommended_actions": ["string"],\n'
        '  "verification_commands": ["string"],\n'
        '  "evidence": [{"source": "symptom"|"topology"|"show_output"|"deterministic_checker"|"inference", "detail": "string"}],\n'
        '  "deterministic_status": "PASS" | "FAIL" | "WARN" | "NOT_AVAILABLE",\n'
        '  "needs_human_review": boolean\n'
        "}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": schema_prompt},
            {"role": "user", "content": user_input},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("No structured diagnosis response returned by the LLM.")

    try:
        parsed_diagnosis = Diagnosis.model_validate_json(content)
        return parsed_diagnosis.model_dump()
    except ValidationError as e:
        # Fallback raw dictionary parse if minor Pydantic validation error occurs
        try:
            return json.loads(content)
        except Exception:
            raise RuntimeError(f"Failed to parse diagnosis output as valid JSON:\n{e}\nRaw output:\n{content}")


def diagnose_case_json(*args: Any, **kwargs: Any) -> str:
    """Convenience wrapper for APIs/UI layers that need a JSON string."""
    result = diagnose_case(*args, **kwargs)
    return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    sample = diagnose_case(
        case_id="CASE_021",
        symptom="Router-1 cannot reach Subnet 172.16.2.0/24 behind Router-2.",
        topology_note="Static routing environment between Router-1 and Router-2.",
        show_outputs=(
            "Router-1# show ip route\n"
            "S* 0.0.0.0/0 [1/0] via 203.0.113.1\n"
            "10.0.0.0/8 is directly connected\n"
            "(Note: no route for 172.16.2.0/24)"
        ),
        deterministic_results=[
            {
                "status": "FAIL",
                "check": "Routing",
                "message": "Missing route for 172.16.2.0/24."
            }
        ],
    )
    print(json.dumps(sample, indent=2, ensure_ascii=False))