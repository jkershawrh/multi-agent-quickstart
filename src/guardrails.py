"""Inference guardrails service -- screens agent inputs and outputs.

Demonstrates the guardrails pattern from the Red Hat AI blueprint.
In production, replace this stub with TrustyAI Guardrails Orchestrator
for ML-based content screening, bias detection, and compliance checks.

All detection here is regex-based for demo purposes.
"""

import logging
import os
import re

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("guardrails")

GUARDRAILS_PORT = int(os.environ.get("GUARDRAILS_PORT", "8005"))

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
}

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous\s+)?instructions", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*:", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(prior|above)", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all|your)\s+(you|instructions|rules)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+)?(you\s+are|a)\s+", re.IGNORECASE),
]

HARMFUL_KEYWORDS = [
    "how to hack", "exploit vulnerability", "create malware",
    "build a weapon", "synthesize drugs",
]


# ---------------------------------------------------------------------------
# Screening logic
# ---------------------------------------------------------------------------


def _detect_pii(text: str) -> List[dict]:
    flags = []
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            flags.append({
                "type": "pii",
                "subtype": pii_type,
                "count": len(matches),
                "action": "flagged",
            })
    return flags


def _detect_injection(text: str) -> List[dict]:
    flags = []
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            flags.append({
                "type": "prompt_injection",
                "pattern": pattern.pattern[:60],
                "action": "blocked",
            })
    return flags


def _detect_harmful(text: str) -> List[dict]:
    text_lower = text.lower()
    flags = []
    for keyword in HARMFUL_KEYWORDS:
        if keyword in text_lower:
            flags.append({
                "type": "harmful_content",
                "keyword": keyword,
                "action": "blocked",
            })
    return flags


def screen_text(text: str, direction: str) -> dict:
    """Screen text and return screening result."""
    flags = []
    flags.extend(_detect_pii(text))
    flags.extend(_detect_harmful(text))

    if direction == "input":
        flags.extend(_detect_injection(text))

    blocked = any(f["action"] == "blocked" for f in flags)

    return {
        "allowed": not blocked,
        "flags": flags,
        "screened_text": text,
        "direction": direction,
    }


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------


class ScreenRequest(BaseModel):
    text: str
    direction: str = "input"


app = FastAPI(
    title="Inference Guardrails",
    description="Screens agent inputs and outputs for PII, injection, and harmful content.",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "checks": ["pii", "prompt_injection", "harmful_content"],
    }


@app.post("/screen")
async def screen(request: ScreenRequest):
    """Screen text for policy violations."""
    result = screen_text(request.text, request.direction)
    if result["flags"]:
        logger.info(
            "Guardrails [%s]: %d flag(s) -- %s",
            request.direction,
            len(result["flags"]),
            ", ".join(f["type"] for f in result["flags"]),
        )
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=GUARDRAILS_PORT)
