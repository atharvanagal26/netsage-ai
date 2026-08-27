"""
llm_engine.py
LLM integration layer for the Network Troubleshooting Diagnosis project.

Responsibilities:
1. Load the diagnosis system prompt from diagnose_prompt.md.
2. Send case evidence to the LLM through the OpenAI Responses API.
3. Enforce a strict JSON schema for the diagnosis response.
4. Return a normal Python dictionary to the Streamlit/UI layer.

Install:
    pip install openai pydantic python-dotenv

Environment:
    OPENAI_API_KEY=your_api_key
    OPENAI_MODEL=gpt-4o-mini   # change if required by your project/account
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

load_dotenv()


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
    Diagnose one networking case.

    The deterministic checker is the first line of evidence. The LLM explains
    the evidence, resolves ambiguity, and proposes verification/remediation
    steps. The LLM must not override explicit deterministic evidence without
    explaining the conflict.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key and client is None:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = client or OpenAI(api_key=api_key)
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    system_prompt = load_system_prompt()
    user_input = _build_user_input(
        case_id,
        symptom,
        topology_note,
        show_outputs,
        deterministic_results,
    )

    response = client.responses.parse(
        model=model,
        instructions=system_prompt,
        input=user_input,
        text_format=Diagnosis,
    )

    # Refusals or unexpected output should be surfaced clearly.
    for item in response.output:
        if getattr(item, "type", None) != "message":
            continue

        for content in getattr(item, "content", []):
            if getattr(content, "type", None) != "output_text":
                continue

            parsed = getattr(content, "parsed", None)
            if parsed is not None:
                return parsed.model_dump()

            refusal = getattr(content, "refusal", None)
            if refusal:
                raise RuntimeError(f"LLM refused the diagnosis request: {refusal}")

    raise RuntimeError("No structured diagnosis was returned by the LLM.")


def diagnose_case_json(*args: Any, **kwargs: Any) -> str:
    """Convenience wrapper for APIs/UI layers that need a JSON string."""
    result = diagnose_case(*args, **kwargs)
    return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Simple local smoke test. It requires OPENAI_API_KEY.
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
