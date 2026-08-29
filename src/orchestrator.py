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
from fastapi import FastAPI, Response

import models
from auth import TokenAuthMiddleware, AGENT_AUTH_TOKEN

try:
    import grpc
    import classify_pb2
    import classify_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        SimpleSpanProcessor,
        ConsoleSpanExporter,
    )
    _otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    _provider = TracerProvider()
    if _otel_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        _provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint=_otel_endpoint)))
    else:
        _provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(_provider)
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("orchestrator")

if OTEL_AVAILABLE:
    tracer = trace.get_tracer("orchestrator")
else:
    tracer = None

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

# Public URL advertised in this service's own A2A agent card. Defaults to
# localhost for the local track; set to the in-cluster/route URL in deploys.
ORCHESTRATOR_PUBLIC_URL = os.environ.get("ORCHESTRATOR_PUBLIC_URL", "http://localhost:8000")

MODEL_ENDPOINT = os.environ.get("MODEL_ENDPOINT", "")
MODEL_ENDPOINT_SIMPLE = os.environ.get("MODEL_ENDPOINT_SIMPLE", MODEL_ENDPOINT)
MODEL_ENDPOINT_COMPLEX = os.environ.get("MODEL_ENDPOINT_COMPLEX", MODEL_ENDPOINT)
MODEL_NAME = os.environ.get("MODEL_NAME", "qwen2.5:1.5b")
MODEL_SIMPLE = os.environ.get("MODEL_SIMPLE", "qwen2.5:0.5b")
MODEL_COMPLEX = os.environ.get("MODEL_COMPLEX", "qwen2.5:1.5b")

# Per-agent request timeout. Must exceed the agent's own LLM timeout
# (AGENT_LLM_TIMEOUT, default 60s) so slow CPU generations are not cut
# off mid-flight and reported as errors. Configurable for larger models.
A2A_CLIENT_TIMEOUT = float(os.environ.get("A2A_CLIENT_TIMEOUT", "120"))
AGENT_DISCOVERY_INTERVAL = float(os.environ.get("AGENT_DISCOVERY_INTERVAL", "10"))


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
        self, agent_name: str, text: str, model_override: str = "",
        endpoint_override: str = "",
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
        if endpoint_override:
            params["endpoint_override"] = endpoint_override

        rpc_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tasks/send",
            "params": params,
        }

        try:
            async with httpx.AsyncClient(timeout=A2A_CLIENT_TIMEOUT) as client:
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


LLM_CLASSIFY_PROMPT = (
    "Classify the following query's complexity into exactly one label: "
    "SIMPLE, MEDIUM, COMPLEX, or REASONING.\n\n"
    "SIMPLE = single fact lookup, status check, or straightforward action.\n"
    "MEDIUM = requires some analysis or a multi-step procedure.\n"
    "COMPLEX = requires deep investigation, synthesis across domains, or architecture.\n"
    "REASONING = requires formal reasoning, proofs, or multi-step logical deduction.\n\n"
    "Reply with ONLY the label, nothing else.\n\nQuery: {query}"
)

VALID_LABELS = {"SIMPLE", "MEDIUM", "COMPLEX", "REASONING"}


class SemanticRouter:
    """Classifies queries via llm-d-sc gRPC or LLM fallback."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.channel = None
        self.stub = None
        self.mode = "inactive"

    async def connect(self):
        if self.endpoint and GRPC_AVAILABLE:
            try:
                self.channel = grpc.aio.insecure_channel(self.endpoint)
                self.stub = classify_pb2_grpc.ClassifyStub(self.channel)
                self.mode = "llm-d-sc"
                logger.info("Semantic router connected (llm-d-sc): %s", self.endpoint)
                return
            except Exception as e:
                logger.warning("llm-d-sc connection failed: %s", e)

        if MODEL_ENDPOINT:
            self.mode = "llm-fallback"
            logger.info("Semantic router using LLM fallback via %s", MODEL_ENDPOINT)
        else:
            self.mode = "inactive"
            logger.info("Semantic routing disabled (no llm-d-sc or LLM endpoint)")

    @property
    def active(self) -> bool:
        return self.mode != "inactive"

    async def classify(self, text: str) -> Optional[models.ClassificationResult]:
        if self.mode == "llm-d-sc" and self.stub:
            return await self._classify_grpc(text)
        elif self.mode == "llm-fallback":
            return await self._classify_llm(text)
        return None

    async def _classify_grpc(self, text: str) -> Optional[models.ClassificationResult]:
        start = time.monotonic()
        try:
            request = classify_pb2.ClassifyRequest(
                request_id=str(uuid.uuid4()),
                context=text,
            )
            response = await self.stub.Classify(request, timeout=5.0)
            latency_ms = round((time.monotonic() - start) * 1000, 2)

            if response.status != classify_pb2.OK:
                logger.warning("llm-d-sc returned status %s, falling back", response.status)
                return await self._classify_llm(text)

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
            logger.warning("llm-d-sc classify failed (%s), trying LLM fallback", e)
            return await self._classify_llm(text)

    async def _classify_llm(self, text: str) -> Optional[models.ClassificationResult]:
        if not MODEL_ENDPOINT:
            return None
        # Classify with the cheap/simple tier -- classification runs on every
        # "auto" query, so using the complex model here would defeat the
        # cost-optimization the router exists to provide.
        classify_endpoint = MODEL_ENDPOINT_SIMPLE or MODEL_ENDPOINT
        classify_model = MODEL_SIMPLE or MODEL_NAME
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{classify_endpoint}/chat/completions",
                    json={
                        "model": classify_model,
                        "messages": [
                            {"role": "user", "content": LLM_CLASSIFY_PROMPT.format(query=text[:500])},
                        ],
                        "temperature": 0,
                        "max_tokens": 10,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
            raw = data["choices"][0]["message"]["content"].strip().upper()
            label = raw.split()[0].strip(".,!") if raw else "COMPLEX"
            if label not in VALID_LABELS:
                label = "COMPLEX"
            latency_ms = round((time.monotonic() - start) * 1000, 2)

            selected = COMPLEXITY_TO_WORKFLOW.get(label, "comprehensive")
            model_tier = COMPLEXITY_TO_MODEL.get(label, "complex")

            return models.ClassificationResult(
                classifier_id="llm-fallback",
                status="ok",
                signals=[models.ClassificationSignal(label=label, score=1.0)],
                selected_workflow=selected,
                selected_model=model_tier,
                latency_ms=latency_ms,
            )
        except Exception as e:
            logger.warning("LLM classification failed: %s", e)
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
    return await _execute_workflow_inner(a2a_client, query, workflow_type)


async def _execute_workflow_inner(
    a2a_client: A2AClient,
    query: str,
    workflow_type: str,
) -> models.WorkflowResponse:
    classification = None
    model_override = ""
    endpoint_override = ""

    _wf_span = tracer.start_span("workflow", attributes={"workflow.type_requested": workflow_type}) if tracer else None
    try:
        if workflow_type == "auto" and semantic_router.active:
            _cls_span = tracer.start_span("classify", attributes={"classify.mode": semantic_router.mode}) if tracer else None
            try:
                classification = await semantic_router.classify(query)
            finally:
                if _cls_span:
                    if classification:
                        _cls_span.set_attribute("classify.result", classification.selected_workflow)
                        _cls_span.set_attribute("classify.top_label", classification.signals[0].label if classification.signals else "")
                        _cls_span.set_attribute("classify.latency_ms", classification.latency_ms)
                    _cls_span.end()

            if classification:
                workflow_type = classification.selected_workflow
                model_tier = classification.selected_model
                if model_tier == "simple":
                    model_override = MODEL_SIMPLE
                    endpoint_override = MODEL_ENDPOINT_SIMPLE
                else:
                    model_override = MODEL_COMPLEX
                    endpoint_override = MODEL_ENDPOINT_COMPLEX
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

        if _wf_span:
            _wf_span.set_attribute("workflow.type_resolved", workflow_type)
            _wf_span.set_attribute("workflow.model_override", model_override or "default")

        steps_config = WORKFLOW_DEFINITIONS.get(
            workflow_type,
            WORKFLOW_DEFINITIONS["comprehensive"],
        )

        steps: List[models.WorkflowStep] = []
        agents_involved: List[str] = []
        total_start = time.monotonic()

        context = query
        for agent_name, action in steps_config:
            step_start = time.monotonic()

            _agent_span = tracer.start_span("agent_call", attributes={
                "agent.name": agent_name,
                "agent.action": action,
            }) if tracer else None

            try:
                task_text = f"[{action}] {context}"
                result = await a2a_client.send_task(
                    agent_name, task_text, model_override, endpoint_override
                )
            finally:
                step_latency = round((time.monotonic() - step_start) * 1000, 2)
                if _agent_span:
                    _agent_span.set_attribute("agent.latency_ms", step_latency)
                    _agent_span.end()

            result_text = _extract_result_text(result)

            steps.append(models.WorkflowStep(
                agent=agent_name,
                action=action,
                result=result_text,
                latency_ms=step_latency,
            ))
            agents_involved.append(agent_name)
            context = f"{context}\n\nPrevious step ({agent_name}/{action}): {result_text}"

        total_latency = round((time.monotonic() - total_start) * 1000, 2)

        if _wf_span:
            _wf_span.set_attribute("workflow.total_latency_ms", total_latency)
            _wf_span.set_attribute("workflow.steps_count", len(steps))

        return models.WorkflowResponse(
            steps=steps,
            total_latency_ms=total_latency,
            agents_involved=list(dict.fromkeys(agents_involved)),
            classification=classification,
            ai_disclaimer=AI_DISCLAIMER,
        )
    finally:
        if _wf_span:
            _wf_span.end()


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


def _agent_urls() -> List[str]:
    return [u.strip().rstrip("/") for u in AGENT_URLS.split(",") if u.strip()]


async def _discover_missing_agents(urls: List[str]) -> int:
    registered_urls = {agent.url for agent in a2a_client.list_agents()}
    for url in urls:
        if url not in registered_urls:
            await a2a_client.discover(url)
    return len(a2a_client.list_agents())


async def _discovery_loop(urls: List[str]):
    """Keep discovering agents that were unavailable during startup."""
    while True:
        await asyncio.sleep(AGENT_DISCOVERY_INTERVAL)
        discovered = await _discover_missing_agents(urls)
        if discovered < len(urls):
            logger.warning("Agent registry incomplete: %d/%d registered", discovered, len(urls))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Discover agents and connect to semantic router on startup."""
    await semantic_router.connect()

    urls = _agent_urls()
    logger.info("Discovering %d agents...", len(urls))

    # Try discovery with retries for startup ordering
    for attempt in range(3):
        discovered = await _discover_missing_agents(urls)
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
    discovery_task = asyncio.create_task(_discovery_loop(urls))
    try:
        yield
    finally:
        discovery_task.cancel()
        try:
            await discovery_task
        except asyncio.CancelledError:
            pass
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
        "semantic_routing": semantic_router.mode,
        "tracing": "active" if OTEL_AVAILABLE else "inactive",
    }


@app.get("/ready")
async def ready(response: Response):
    """Report ready only after every configured agent is registered."""
    agents = a2a_client.list_agents()
    expected = len(_agent_urls())
    is_ready = len(agents) >= expected
    if not is_ready:
        response.status_code = 503
    return {
        "status": "ready" if is_ready else "not_ready",
        "agents_discovered": len(agents),
        "agents_expected": expected,
        "agent_names": [a.name for a in agents],
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
        url=ORCHESTRATOR_PUBLIC_URL,
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
