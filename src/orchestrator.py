"""Multi-Agent Orchestrator -- discovers and delegates to A2A agents.

Discovers agents via HTTP GET to /.well-known/agent-card.json,
maintains a registry, and executes multi-step workflows by
delegating tasks to agents via the A2A JSON-RPC protocol.

Domain-agnostic: configure agent names, skills, and workflows
via environment variables. Ships with 3 example agents
(research, analyst, executor) that work in demo mode.
"""

import asyncio
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI

import models
from auth import TokenAuthMiddleware, AGENT_AUTH_TOKEN

try:
    import grpc
    import classify_pb2
    import classify_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("orchestrator")

AI_DISCLAIMER = (
    "Agent responses are AI-generated -- verify "
    "recommendations with qualified professionals."
)

# Agent URLs to discover on startup (comma-separated)
AGENT_URLS = os.environ.get(
    "AGENT_URLS",
    "http://research-agent:8001,http://analyst-agent:8002,http://executor-agent:8003",
)

SEMANTIC_ROUTER_ENDPOINT = os.environ.get("SEMANTIC_ROUTER_ENDPOINT", "")

MODEL_SIMPLE = os.environ.get("MODEL_SIMPLE", "qwen2.5:0.5b")
MODEL_COMPLEX = os.environ.get("MODEL_COMPLEX", "qwen2.5:1.5b")


# ---------------------------------------------------------------------------
# A2A Client
# ---------------------------------------------------------------------------


class A2AClient:
    """Discovers and communicates with A2A-compliant agents."""

    def __init__(self):
        self.agents: Dict[str, models.DiscoveredAgent] = {}

    def _auth_headers(self) -> dict:
        if AGENT_AUTH_TOKEN:
            return {"Authorization": f"Bearer {AGENT_AUTH_TOKEN}"}
        return {}

    async def discover(self, base_url: str) -> Optional[models.DiscoveredAgent]:
        """Fetch /.well-known/agent-card.json and register the agent."""
        url = f"{base_url.rstrip('/')}/.well-known/agent-card.json"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                card_data = resp.json()

            skills = [
                models.AgentSkill(**s)
                for s in card_data.get("skills", [])
            ]
            agent = models.DiscoveredAgent(
                name=card_data.get("name", "unknown"),
                url=base_url.rstrip("/"),
                status="active",
                skills=skills,
            )
            self.agents[agent.name] = agent
            logger.info("Discovered agent: %s at %s (%d skills)",
                        agent.name, base_url, len(skills))
            return agent
        except Exception as e:
            logger.warning("Discovery failed for %s: %s", base_url, e)
            return None

    async def send_task(
        self, agent_name: str, text: str, model_override: str = ""
    ) -> dict:
        """Send a tasks/send JSON-RPC request to a discovered agent."""
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent not found: {agent_name}"}

        task_id = str(uuid.uuid4())
        params: dict = {
            "id": task_id,
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"kind": "text", "text": text}],
            },
        }
        if model_override:
            params["model_override"] = model_override

        rpc_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tasks/send",
            "params": params,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{agent.url}/a2a",
                    json=rpc_request,
                    headers=self._auth_headers(),
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error("Task send to %s failed: %s", agent_name, e)
            return {"error": str(e)}

    def list_agents(self) -> List[models.DiscoveredAgent]:
        return list(self.agents.values())

    def get_agent(self, name: str) -> Optional[models.DiscoveredAgent]:
        return self.agents.get(name)


# ---------------------------------------------------------------------------
# Semantic Router (llm-d-sc integration)
# ---------------------------------------------------------------------------

COMPLEXITY_TO_WORKFLOW = {
    "SIMPLE": "lightweight",
    "MEDIUM": "standard",
    "COMPLEX": "comprehensive",
    "REASONING": "comprehensive",
}

COMPLEXITY_TO_MODEL = {
    "SIMPLE": "simple",
    "MEDIUM": "simple",
    "COMPLEX": "complex",
    "REASONING": "complex",
}


class SemanticRouter:
    """Classifies queries via llm-d-sc gRPC and selects workflows."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.channel = None
        self.stub = None

    async def connect(self):
        if not GRPC_AVAILABLE:
            logger.warning("grpc not installed -- semantic routing disabled")
            return
        if not self.endpoint:
            return
        try:
            self.channel = grpc.aio.insecure_channel(self.endpoint)
            self.stub = classify_pb2_grpc.ClassifyStub(self.channel)
            logger.info("Semantic router connected: %s", self.endpoint)
        except Exception as e:
            logger.warning("Semantic router connection failed: %s", e)
            self.stub = None

    async def classify(self, text: str) -> Optional[models.ClassificationResult]:
        if not self.stub:
            return None
        start = time.monotonic()
        try:
            request = classify_pb2.ClassifyRequest(
                request_id=str(uuid.uuid4()),
                context=text,
            )
            response = await self.stub.Classify(request, timeout=5.0)
            latency_ms = round((time.monotonic() - start) * 1000, 2)

            if response.status != classify_pb2.OK:
                logger.warning(
                    "Semantic router returned status %s", response.status
                )
                return None

            signals = [
                models.ClassificationSignal(label=s.label, score=round(s.score, 4))
                for s in response.ranked
            ]
            top_label = signals[0].label if signals else "COMPLEX"
            selected = COMPLEXITY_TO_WORKFLOW.get(top_label, "comprehensive")
            model_tier = COMPLEXITY_TO_MODEL.get(top_label, "complex")

            return models.ClassificationResult(
                classifier_id=response.classifier_id,
                status="ok",
                signals=signals,
                selected_workflow=selected,
                selected_model=model_tier,
                latency_ms=latency_ms,
            )
        except Exception as e:
            logger.warning("Semantic classification failed: %s", e)
            return None

    async def close(self):
        if self.channel:
            await self.channel.close()


# ---------------------------------------------------------------------------
# Workflow engine
# ---------------------------------------------------------------------------

WORKFLOW_DEFINITIONS = {
    "lightweight": [
        ("executor", "execute"),
    ],
    "standard": [
        ("research", "investigate"),
        ("executor", "execute"),
    ],
    "comprehensive": [
        ("research", "investigate"),
        ("analyst", "analyze"),
        ("executor", "execute"),
    ],
    "general": [
        ("research", "investigate"),
        ("analyst", "recommend"),
        ("executor", "report"),
    ],
}


async def execute_workflow(
    a2a_client: A2AClient,
    query: str,
    workflow_type: str = "auto",
) -> models.WorkflowResponse:
    """Execute a multi-agent workflow by delegating tasks sequentially."""
    classification = None

    model_override = ""

    if workflow_type == "auto" and semantic_router.stub:
        classification = await semantic_router.classify(query)
        if classification:
            workflow_type = classification.selected_workflow
            model_tier = classification.selected_model
            if model_tier == "simple":
                model_override = MODEL_SIMPLE
            else:
                model_override = MODEL_COMPLEX
            logger.info(
                "Semantic routing: %s -> %s, model=%s (top signal: %s %.3f)",
                workflow_type,
                classification.selected_workflow,
                model_override,
                classification.signals[0].label if classification.signals else "?",
                classification.signals[0].score if classification.signals else 0,
            )
        else:
            workflow_type = "comprehensive"
    elif workflow_type == "auto":
        workflow_type = "comprehensive"

    steps_config = WORKFLOW_DEFINITIONS.get(
        workflow_type,
        WORKFLOW_DEFINITIONS["comprehensive"],
    )

    steps: List[models.WorkflowStep] = []
    agents_involved: List[str] = []
    total_start = time.monotonic()

    # Build context that accumulates across steps
    context = query
    for agent_name, action in steps_config:
        step_start = time.monotonic()

        task_text = f"[{action}] {context}"
        result = await a2a_client.send_task(agent_name, task_text, model_override)

        step_latency = round((time.monotonic() - step_start) * 1000, 2)

        # Extract result text from A2A response
        result_text = _extract_result_text(result)

        steps.append(models.WorkflowStep(
            agent=agent_name,
            action=action,
            result=result_text,
            latency_ms=step_latency,
        ))
        agents_involved.append(agent_name)

        # Accumulate context for next step
        context = f"{context}\n\nPrevious step ({agent_name}/{action}): {result_text}"

    total_latency = round((time.monotonic() - total_start) * 1000, 2)

    return models.WorkflowResponse(
        steps=steps,
        total_latency_ms=total_latency,
        agents_involved=list(dict.fromkeys(agents_involved)),
        classification=classification,
        ai_disclaimer=AI_DISCLAIMER,
    )


def _extract_result_text(rpc_response: dict) -> str:
    """Extract text from A2A JSON-RPC response."""
    if rpc_response.get("error"):
        return f"Error: {rpc_response['error']}"

    result = rpc_response.get("result", {})
    artifacts = result.get("artifacts", [])
    if not artifacts:
        return "No result returned"

    texts = []
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if part.get("text"):
                texts.append(part["text"])

    return " ".join(texts) if texts else "No text in response"


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

a2a_client = A2AClient()
semantic_router = SemanticRouter(SEMANTIC_ROUTER_ENDPOINT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Discover agents and connect to semantic router on startup."""
    if SEMANTIC_ROUTER_ENDPOINT:
        await semantic_router.connect()

    urls = [u.strip() for u in AGENT_URLS.split(",") if u.strip()]
    logger.info("Discovering %d agents...", len(urls))

    # Try discovery with retries for startup ordering
    for attempt in range(3):
        for url in urls:
            if not any(a.url == url.rstrip("/") for a in a2a_client.list_agents()):
                await a2a_client.discover(url)

        discovered = len(a2a_client.list_agents())
        if discovered >= len(urls):
            break

        if attempt < 2:
            wait = 2 * (attempt + 1)
            logger.info(
                "Discovered %d/%d agents, retrying in %ds...",
                discovered, len(urls), wait,
            )
            await asyncio.sleep(wait)

    logger.info(
        "Agent discovery complete: %d agents registered",
        len(a2a_client.list_agents()),
    )
    yield
    await semantic_router.close()


app = FastAPI(
    title="Multi-Agent Orchestrator",
    description=(
        "Domain-agnostic orchestrator that discovers and coordinates "
        "A2A-compliant agents with semantic routing, MCP tool calling, "
        "and inter-agent authentication. Runs on Intel Xeon CPU."
    ),
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(TokenAuthMiddleware)


@app.get("/health")
async def health():
    agents = a2a_client.list_agents()
    return {
        "status": "healthy",
        "agents_discovered": len(agents),
        "agent_names": [a.name for a in agents],
        "semantic_routing": "active" if semantic_router.stub else "inactive",
    }


@app.get("/.well-known/agent-card.json")
async def orchestrator_agent_card():
    """Serve the orchestrator's own A2A agent card."""
    card = models.AgentCard(
        name="orchestrator",
        description=(
            "Multi-agent orchestrator -- discovers and coordinates "
            "A2A-compliant agents with semantic routing. Runs on Intel Xeon CPU."
        ),
        url="http://localhost:8000",
        skills=[
            models.AgentSkill(
                id="orchestrate-workflow",
                name="Orchestrate Workflow",
                description="Execute a multi-agent workflow across discovered agents",
                tags=["orchestration", "workflow", "multi-agent"],
                examples=[
                    "Run a comprehensive workflow",
                    "Investigate and analyze this request",
                ],
            ),
        ],
    )
    return card.model_dump()


@app.get("/api/v1/agents")
async def list_agents():
    """List all discovered agents."""
    agents = a2a_client.list_agents()
    return {
        "agents": [a.model_dump() for a in agents],
        "count": len(agents),
    }


@app.post("/api/v1/workflow")
async def run_workflow(request: models.WorkflowRequest):
    """Execute a multi-agent workflow."""
    return await execute_workflow(
        a2a_client,
        query=request.query,
        workflow_type=request.workflow_type,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
