"""A2A-compliant agent template -- serves agent card and handles JSON-RPC tasks.

Each agent instance is configured via environment variables:
  AGENT_NAME  -- agent identity (research, analyst, executor)
  AGENT_SKILLS -- comma-separated skill ids
  AGENT_PORT  -- port to listen on (default 8001)

Demo mode: all agents return simulated responses without LLM backends.
"""

import logging
import os
import random
import time
import uuid

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

import models
from auth import TokenAuthMiddleware

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("a2a-agent")

AGENT_NAME = os.environ.get("AGENT_NAME", "generic")
AGENT_PORT = int(os.environ.get("AGENT_PORT", "8001"))
AGENT_SKILLS_RAW = os.environ.get("AGENT_SKILLS", "respond")

MODEL_ENDPOINT = os.environ.get("MODEL_ENDPOINT", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "qwen2.5:1.5b")
DEMO_MODE = os.environ.get("DEMO_MODE", "").lower() in ("true", "1", "yes")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "")
GUARDRAILS_URL = os.environ.get("GUARDRAILS_URL", "")

AI_DISCLAIMER = (
    "Agent responses are AI-generated -- verify "
    "recommendations with qualified professionals."
)

# ---------------------------------------------------------------------------
# Skill and card definitions per agent type
# ---------------------------------------------------------------------------

AGENT_CONFIGS = {
    "research": {
        "description": (
            "Research agent -- investigates queries, gathers relevant "
            "information, and summarizes findings. Runs on Intel Xeon CPU."
        ),
        "skills": [
            models.AgentSkill(
                id="investigate",
                name="Investigate",
                description="Research a topic and gather relevant information",
                tags=["research", "investigation"],
                examples=["Investigate this issue", "What do we know about this?"],
            ),
            models.AgentSkill(
                id="summarize",
                name="Summarize",
                description="Summarize findings from an investigation",
                tags=["research", "summary"],
                examples=["Summarize these findings", "Give me an overview"],
            ),
        ],
    },
    "analyst": {
        "description": (
            "Analyst agent -- synthesizes research findings and produces "
            "actionable recommendations. Runs on Intel Xeon CPU."
        ),
        "skills": [
            models.AgentSkill(
                id="analyze",
                name="Analyze",
                description="Analyze data and identify patterns or issues",
                tags=["analysis", "evaluation"],
                examples=["Analyze this data", "What patterns do you see?"],
            ),
            models.AgentSkill(
                id="recommend",
                name="Recommend",
                description="Produce actionable recommendations based on analysis",
                tags=["analysis", "recommendation"],
                examples=["What do you recommend?", "What should we do?"],
            ),
        ],
    },
    "executor": {
        "description": (
            "Executor agent -- takes action on recommendations and "
            "reports results. Runs on Intel Xeon CPU."
        ),
        "skills": [
            models.AgentSkill(
                id="execute",
                name="Execute",
                description="Carry out a recommended action or task",
                tags=["execution", "action"],
                examples=["Execute this plan", "Take action on this"],
            ),
            models.AgentSkill(
                id="report",
                name="Report",
                description="Generate a status report on completed actions",
                tags=["execution", "reporting"],
                examples=["Report on progress", "What is the status?"],
            ),
        ],
    },
}

# ---------------------------------------------------------------------------
# Demo responses per agent type
# ---------------------------------------------------------------------------

DEMO_RESPONSES = {
    "research": {
        "investigate": (
            "Investigation complete. Gathered data from 3 sources. "
            "Key findings: (1) The issue has been reported 12 times in the past "
            "30 days with increasing frequency. (2) Root cause appears linked to "
            "a configuration change deployed on the 15th. (3) Affected scope is "
            "limited to the EMEA region. Forwarding findings for analysis."
        ),
        "summarize": (
            "Summary: A recurring issue has been identified, concentrated in "
            "one region and correlated with a recent configuration change. "
            "Impact is moderate -- affecting approximately 8% of requests. "
            "Detailed data attached for analyst review."
        ),
    },
    "analyst": {
        "analyze": (
            "Analysis complete. Pattern identified: the configuration change "
            "on the 15th modified timeout thresholds, causing cascading retries "
            "under high latency conditions specific to EMEA routing. "
            "Confidence: HIGH. Supporting evidence from 3 independent signals."
        ),
        "recommend": (
            "Recommendation: (1) Revert the timeout threshold to the previous "
            "value as an immediate mitigation. (2) Implement region-aware "
            "timeout configuration to prevent recurrence. (3) Add monitoring "
            "alert for retry rate exceeding 5% per region. Estimated resolution "
            "time: 2 hours for step 1, 1 sprint for steps 2-3."
        ),
    },
    "executor": {
        "execute": (
            "Action executed: Timeout threshold reverted to previous value "
            "(300ms -> 500ms). Change deployed to EMEA region at 14:32 UTC. "
            "Monitoring confirms retry rate dropped from 8.2% to 0.4% within "
            "5 minutes. Remaining recommendations queued for sprint planning."
        ),
        "report": (
            "Status report: Immediate mitigation applied successfully. "
            "EMEA retry rate normalized. Task PROJ-1234 created for "
            "region-aware timeout configuration. Task PROJ-1235 created "
            "for monitoring alert. Both assigned to next sprint."
        ),
    },
}


def _get_agent_config() -> dict:
    """Return the agent configuration for the current AGENT_NAME."""
    return AGENT_CONFIGS.get(AGENT_NAME, {
        "description": f"{AGENT_NAME} agent -- generic A2A-compliant agent. Runs on Intel Xeon CPU.",
        "skills": [
            models.AgentSkill(
                id=s.strip(),
                name=s.strip().title(),
                description=f"Perform {s.strip()} operation",
                tags=[AGENT_NAME, s.strip()],
            )
            for s in AGENT_SKILLS_RAW.split(",") if s.strip()
        ],
    })


def _build_agent_card() -> models.AgentCard:
    """Build the agent card from environment configuration."""
    config = _get_agent_config()
    return models.AgentCard(
        name=AGENT_NAME,
        description=config["description"],
        url=f"http://localhost:{AGENT_PORT}",
        skills=config["skills"],
    )


def _demo_response(text: str) -> str:
    """Generate a simulated response based on agent type and query content."""
    agent_responses = DEMO_RESPONSES.get(AGENT_NAME, {})

    text_lower = text.lower()
    for skill_id, response in agent_responses.items():
        if skill_id in text_lower:
            return response

    if agent_responses:
        return next(iter(agent_responses.values()))

    return (
        f"[{AGENT_NAME}] Processed query: {text[:100]}. "
        f"Analysis complete. {AI_DISCLAIMER}"
    )


async def _llm_response(
    text: str, model_name: str = "", endpoint: str = ""
) -> str:
    """Call the LLM via the OpenAI-compatible endpoint and return its reply."""
    use_model = model_name or MODEL_NAME
    use_endpoint = endpoint or MODEL_ENDPOINT
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{use_endpoint}/chat/completions",
                json={
                    "model": use_model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                f"You are a {AGENT_NAME} agent in a multi-agent workflow. "
                                "Provide concise, professional responses. "
                                f"{AI_DISCLAIMER}"
                            ),
                        },
                        {"role": "user", "content": text},
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning("LLM call failed (%s), falling back to demo response", exc)
        return _demo_response(text)


# ---------------------------------------------------------------------------
# Guardrails screening
# ---------------------------------------------------------------------------


async def _screen_text(text: str, direction: str) -> dict:
    """Screen text through the guardrails service. Returns screening result or None."""
    if not GUARDRAILS_URL:
        return {"allowed": True, "flags": [], "screened_text": text}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{GUARDRAILS_URL}/screen",
                json={"text": text, "direction": direction},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning("Guardrails screening failed (%s), allowing through", e)
    return {"allowed": True, "flags": [], "screened_text": text}


# ---------------------------------------------------------------------------
# MCP tool calling
# ---------------------------------------------------------------------------

TOOL_KEYWORDS = {
    "lookup_record": ["record", "lookup", "details", "profile", "rec-"],
    "search_knowledge_base": ["search", "knowledge", "find information", "what do we know", "documentation"],
    "create_task": ["create task", "action item", "assign", "schedule", "track", "todo"],
}


async def _call_mcp_tools(text: str) -> str:
    """Call relevant MCP tools based on query content and return results."""
    if not MCP_SERVER_URL:
        return ""

    text_lower = text.lower()
    tools_to_call = []
    for tool_name, keywords in TOOL_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            tools_to_call.append(tool_name)

    if not tools_to_call:
        return ""

    results = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for tool_name in tools_to_call:
                arguments = _build_tool_arguments(tool_name, text)
                resp = await client.post(
                    f"{MCP_SERVER_URL}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": str(uuid.uuid4()),
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": arguments},
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {})
                    content = result.get("content", [])
                    for item in content:
                        if item.get("text"):
                            results.append(f"[{tool_name}]: {item['text']}")
                            logger.info("MCP tool call: %s", tool_name)
    except Exception as e:
        logger.warning("MCP tool call failed: %s", e)

    return "\n".join(results)


def _build_tool_arguments(tool_name: str, text: str) -> dict:
    """Extract tool arguments from query text (best-effort for demo)."""
    text_lower = text.lower()
    if tool_name == "lookup_record":
        for token in text.split():
            if token.upper().startswith("REC-"):
                return {"record_id": token.upper()}
        return {"record_id": "REC-001"}
    elif tool_name == "search_knowledge_base":
        words = text_lower.split()
        query = " ".join(w for w in words if len(w) > 3)[:200]
        return {"query": query or "general information", "max_results": 3}
    elif tool_name == "create_task":
        return {
            "title": text[:100],
            "priority": "high" if "urgent" in text_lower else "medium",
        }
    return {}


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=f"A2A Agent: {AGENT_NAME}",
    description=f"A2A-compliant {AGENT_NAME} agent for multi-agent workflows.",
    version="1.0.0",
)
app.add_middleware(TokenAuthMiddleware)


@app.get("/health")
async def health():
    if MODEL_ENDPOINT and not DEMO_MODE:
        mode = "llm"
    else:
        mode = "demo"
    return {
        "status": "healthy",
        "agent": AGENT_NAME,
        "mode": mode,
    }


@app.get("/.well-known/agent-card.json")
async def agent_card():
    card = _build_agent_card()
    return card.model_dump()


@app.post("/a2a")
async def a2a_endpoint(request: models.JsonRpcRequest):
    """Handle A2A JSON-RPC 2.0 requests."""

    if request.method == "tasks/send":
        params = request.params or {}
        task_id = params.get("id", str(uuid.uuid4()))
        model_override = params.get("model_override", "")
        endpoint_override = params.get("endpoint_override", "")
        message = params.get("message", {})
        parts = message.get("parts", [])
        text = parts[0].get("text", "") if parts else ""

        start = time.monotonic()

        input_screen = await _screen_text(text, "input")
        if not input_screen["allowed"]:
            flags_summary = ", ".join(f["type"] for f in input_screen.get("flags", []))
            logger.warning("Guardrails blocked input [%s]: %s", AGENT_NAME, flags_summary)
            response_text = (
                f"Request blocked by guardrails ({flags_summary}). "
                "Please rephrase your query."
            )
        else:
            tool_context = await _call_mcp_tools(text)
            enriched_text = f"{text}\n\nTool results:\n{tool_context}" if tool_context else text

            if (endpoint_override or MODEL_ENDPOINT) and not DEMO_MODE:
                response_text = await _llm_response(
                    enriched_text, model_override, endpoint_override
                )
            else:
                response_text = _demo_response(text)

            if tool_context:
                response_text = f"{response_text}\n\n[MCP tool data retrieved]\n{tool_context}"

            output_screen = await _screen_text(response_text, "output")
            if not output_screen.get("allowed", True):
                flags_summary = ", ".join(
                    f["type"] for f in output_screen.get("flags", [])
                )
                logger.warning(
                    "Guardrails blocked output [%s]: %s", AGENT_NAME, flags_summary
                )
                response_text = (
                    f"Response blocked by guardrails ({flags_summary}). "
                    "No generated content was returned."
                )
            elif output_screen.get("flags"):
                flags_summary = ", ".join(f["type"] for f in output_screen["flags"])
                response_text += f"\n\n[Guardrails warning: {flags_summary} detected in output]"

        latency_ms = round((time.monotonic() - start) * 1000, 2)

        # Simulate realistic processing time (demo mode only)
        if not MODEL_ENDPOINT or DEMO_MODE:
            latency_ms = max(latency_ms, round(random.uniform(15, 150), 2))

        logger.info(
            "A2A tasks/send [%s] task=%s latency=%.1fms",
            AGENT_NAME, task_id, latency_ms,
        )

        return models.JsonRpcResponse(
            id=request.id,
            result=models.Task(
                id=task_id,
                contextId=str(uuid.uuid4()),
                status=models.TaskStatus(state="completed"),
                artifacts=[
                    models.Artifact(
                        parts=[models.Part(text=response_text)]
                    )
                ],
            ),
        )

    if request.method == "tasks/get":
        task_id = (request.params or {}).get("id", "unknown")
        return models.JsonRpcResponse(
            id=request.id,
            result=models.Task(
                id=task_id,
                status=models.TaskStatus(state="completed"),
            ),
        )

    return JSONResponse(
        content={
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {request.method}",
            },
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
