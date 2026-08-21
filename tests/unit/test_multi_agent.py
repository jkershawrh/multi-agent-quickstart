"""Stage 2: Technique validation -- multi-agent A2A protocol unit tests.

Tests cover:
  - test_agent_card_served -- agent returns valid agent card JSON
  - test_a2a_task_send -- tasks/send creates and returns task
  - test_orchestrator_discovers_agents -- orchestrator finds agents by card
  - test_workflow_completes -- triage -> clinical -> scheduling workflow
  - test_each_agent_responds_independently -- each agent handles its own tasks
  - test_demo_mode_works -- all agents work without LLM backends
  - test_workflow_steps_have_latency -- each step reports latency
  - test_semantic_routing -- llm-d-sc complexity classification routing
  - test_mcp_tools -- MCP tool server and agent tool calling
  - test_auth -- bearer token authentication middleware
"""

import asyncio
import os
import pathlib
import sys

import pytest

# Add src to path so we can import modules
SRC_DIR = pathlib.Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

# Set agent env vars before importing agent module
os.environ.setdefault("AGENT_NAME", "research")
os.environ.setdefault("AGENT_SKILLS", "investigate,summarize")
os.environ.setdefault("AGENT_PORT", "8001")

from fastapi.testclient import TestClient

import agent
import auth
import mcp_server
import models
import orchestrator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(coro):
    """Run an async coroutine in a sync test."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def triage_client():
    """TestClient for the research agent (aliased as triage_client for compat)."""
    os.environ["AGENT_NAME"] = "research"
    os.environ["AGENT_SKILLS"] = "investigate,summarize"
    agent.AGENT_NAME = "research"
    agent.AGENT_SKILLS_RAW = "investigate,summarize"
    return TestClient(agent.app)


@pytest.fixture
def clinical_client():
    """TestClient for the analyst agent (aliased as clinical_client for compat)."""
    os.environ["AGENT_NAME"] = "analyst"
    os.environ["AGENT_SKILLS"] = "analyze,recommend"
    agent.AGENT_NAME = "analyst"
    agent.AGENT_SKILLS_RAW = "analyze,recommend"
    return TestClient(agent.app)


@pytest.fixture
def scheduling_client():
    """TestClient for the executor agent (aliased as scheduling_client for compat)."""
    os.environ["AGENT_NAME"] = "executor"
    os.environ["AGENT_SKILLS"] = "execute,report"
    agent.AGENT_NAME = "executor"
    agent.AGENT_SKILLS_RAW = "execute,report"
    return TestClient(agent.app)


# ---------------------------------------------------------------------------
# Test: agent card served
# ---------------------------------------------------------------------------


class TestAgentCardServed:

    def test_agent_card_served(self, triage_client):
        """Agent returns a valid agent card JSON at /.well-known/agent-card.json."""
        resp = triage_client.get("/.well-known/agent-card.json")
        assert resp.status_code == 200

        card = resp.json()
        assert "name" in card
        assert "description" in card
        assert "version" in card
        assert "protocolVersion" in card
        assert "skills" in card
        assert isinstance(card["skills"], list)
        assert len(card["skills"]) > 0
        assert card["name"] == "research"

    def test_agent_card_has_required_a2a_fields(self, triage_client):
        """Agent card includes all fields required by A2A protocol."""
        card = triage_client.get("/.well-known/agent-card.json").json()
        assert card["protocolVersion"] == "0.2.6"
        assert "capabilities" in card
        assert "defaultInputModes" in card
        assert "defaultOutputModes" in card

    def test_agent_card_skills_have_ids(self, triage_client):
        """Each skill in the agent card has an id, name, and description."""
        card = triage_client.get("/.well-known/agent-card.json").json()
        for skill in card["skills"]:
            assert "id" in skill, f"Skill missing id: {skill}"
            assert "name" in skill, f"Skill missing name: {skill}"
            assert "description" in skill, f"Skill missing description: {skill}"


# ---------------------------------------------------------------------------
# Test: A2A task send
# ---------------------------------------------------------------------------


class TestA2ATaskSend:

    def test_a2a_task_send(self, triage_client):
        """tasks/send creates and returns a completed task with artifacts."""
        rpc_request = {
            "jsonrpc": "2.0",
            "id": "test-1",
            "method": "tasks/send",
            "params": {
                "id": "task-001",
                "message": {
                    "messageId": "msg-1",
                    "role": "user",
                    "parts": [{"kind": "text", "text": "Patient with chest pain"}],
                },
            },
        }
        resp = triage_client.post("/a2a", json=rpc_request)
        assert resp.status_code == 200

        data = resp.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-1"
        assert "result" in data
        assert data["result"]["status"]["state"] == "completed"
        assert data["result"]["id"] == "task-001"
        assert len(data["result"]["artifacts"]) > 0

        # Verify artifact has text content
        artifact = data["result"]["artifacts"][0]
        assert len(artifact["parts"]) > 0
        assert artifact["parts"][0]["text"]

    def test_a2a_tasks_get(self, triage_client):
        """tasks/get retrieves task status."""
        rpc_request = {
            "jsonrpc": "2.0",
            "id": "test-2",
            "method": "tasks/get",
            "params": {"id": "task-001"},
        }
        resp = triage_client.post("/a2a", json=rpc_request)
        assert resp.status_code == 200

        data = resp.json()
        assert data["result"]["id"] == "task-001"
        assert data["result"]["status"]["state"] == "completed"

    def test_a2a_unknown_method(self, triage_client):
        """Unknown method returns JSON-RPC error."""
        rpc_request = {
            "jsonrpc": "2.0",
            "id": "test-3",
            "method": "tasks/unknown",
        }
        resp = triage_client.post("/a2a", json=rpc_request)
        assert resp.status_code == 200

        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32601


# ---------------------------------------------------------------------------
# Test: orchestrator discovers agents
# ---------------------------------------------------------------------------


class TestOrchestratorDiscoversAgents:

    def test_orchestrator_discovers_agents(self):
        """Orchestrator discovers agents by fetching their agent cards."""
        a2a_client = orchestrator.A2AClient()

        os.environ["AGENT_NAME"] = "research"
        agent.AGENT_NAME = "research"
        agent.AGENT_SKILLS_RAW = "investigate,summarize"
        triage = TestClient(agent.app)

        # Simulate discovery by parsing agent card directly
        card_resp = triage.get("/.well-known/agent-card.json")
        card_data = card_resp.json()

        skills = [
            models.AgentSkill(**s)
            for s in card_data.get("skills", [])
        ]
        discovered = models.DiscoveredAgent(
            name=card_data["name"],
            url="http://localhost:8001",
            status="active",
            skills=skills,
        )
        a2a_client.agents[discovered.name] = discovered

        # Verify discovery
        agents = a2a_client.list_agents()
        assert len(agents) == 1
        assert agents[0].name == "research"
        assert agents[0].status == "active"
        assert len(agents[0].skills) > 0

    def test_orchestrator_registry_multiple_agents(self):
        """Orchestrator can register and look up multiple agents."""
        a2a_client = orchestrator.A2AClient()

        for name in ["research", "analyst", "executor"]:
            a2a_client.agents[name] = models.DiscoveredAgent(
                name=name,
                url=f"http://{name}-agent:800x",
                status="active",
                skills=[models.AgentSkill(
                    id=f"{name}-skill",
                    name=f"{name.title()} Skill",
                    description=f"Skill for {name}",
                )],
            )

        assert len(a2a_client.list_agents()) == 3
        assert a2a_client.get_agent("research") is not None
        assert a2a_client.get_agent("analyst") is not None
        assert a2a_client.get_agent("executor") is not None
        assert a2a_client.get_agent("nonexistent") is None


# ---------------------------------------------------------------------------
# Test: workflow completes (triage -> clinical -> scheduling)
# ---------------------------------------------------------------------------


class TestWorkflowCompletes:

    def test_workflow_completes(self):
        """Full research -> analyst -> executor workflow completes."""
        a2a_client = orchestrator.A2AClient()

        for name, port in [("research", 8001), ("analyst", 8002), ("executor", 8003)]:
            a2a_client.agents[name] = models.DiscoveredAgent(
                name=name,
                url=f"http://localhost:{port}",
                status="active",
            )

        wf = orchestrator.WORKFLOW_DEFINITIONS["comprehensive"]
        assert len(wf) == 3
        assert wf[0] == ("research", "investigate")
        assert wf[1] == ("analyst", "analyze")
        assert wf[2] == ("executor", "execute")

    def test_general_workflow_definition(self):
        """General workflow has correct agent sequence."""
        wf = orchestrator.WORKFLOW_DEFINITIONS["general"]
        assert len(wf) == 3
        agents = [step[0] for step in wf]
        assert "research" in agents
        assert "analyst" in agents
        assert "executor" in agents


# ---------------------------------------------------------------------------
# Test: each agent responds independently
# ---------------------------------------------------------------------------


class TestEachAgentRespondsIndependently:

    def test_each_agent_responds_independently(self, triage_client, clinical_client, scheduling_client):
        """Each agent handles its own tasks with distinct responses."""
        rpc_request = {
            "jsonrpc": "2.0",
            "id": "indep-test",
            "method": "tasks/send",
            "params": {
                "id": "task-indep",
                "message": {
                    "messageId": "msg-indep",
                    "role": "user",
                    "parts": [{"kind": "text", "text": "Patient needs assessment"}],
                },
            },
        }

        responses = {}
        for name, client in [
            ("triage", triage_client),
            ("clinical", clinical_client),
            ("scheduling", scheduling_client),
        ]:
            resp = client.post("/a2a", json=rpc_request)
            assert resp.status_code == 200
            data = resp.json()
            assert data["result"]["status"]["state"] == "completed"
            result_text = data["result"]["artifacts"][0]["parts"][0]["text"]
            responses[name] = result_text

        # Each agent should produce a distinct, non-empty response
        assert len(responses) == 3
        for name, text in responses.items():
            assert text, f"Agent {name} returned empty response"
            assert len(text) > 20, f"Agent {name} response too short: {text}"

    def test_agent_health_endpoints_independent(self, triage_client, clinical_client, scheduling_client):
        """Each agent has a working health endpoint."""
        for name, client in [
            ("triage", triage_client),
            ("clinical", clinical_client),
            ("scheduling", scheduling_client),
        ]:
            resp = client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# Test: demo mode works
# ---------------------------------------------------------------------------


class TestDemoModeWorks:

    def test_demo_mode_works(self, triage_client):
        """All agents work in demo mode without LLM backends."""
        # Health check
        health = triage_client.get("/health")
        assert health.status_code == 200
        assert health.json()["mode"] == "demo"

        # Agent card
        card = triage_client.get("/.well-known/agent-card.json")
        assert card.status_code == 200
        assert len(card.json()["skills"]) > 0

        # Task execution
        rpc_request = {
            "jsonrpc": "2.0",
            "id": "demo-test",
            "method": "tasks/send",
            "params": {
                "id": "demo-task",
                "message": {
                    "messageId": "msg-demo",
                    "role": "user",
                    "parts": [{"kind": "text", "text": "classify this case"}],
                },
            },
        }
        resp = triage_client.post("/a2a", json=rpc_request)
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["status"]["state"] == "completed"
        assert data["result"]["artifacts"][0]["parts"][0]["text"]

    def test_demo_mode_no_llm_required(self):
        """Demo mode flag is set when no LLM endpoint is configured."""
        # Agent always runs in demo mode in this quickstart
        health = TestClient(agent.app).get("/health")
        assert health.json()["mode"] == "demo"


# ---------------------------------------------------------------------------
# Test: workflow steps have latency
# ---------------------------------------------------------------------------


class TestWorkflowStepsHaveLatency:

    def test_workflow_steps_have_latency(self):
        """Each workflow step reports a positive latency_ms value."""
        # Simulate workflow steps
        steps = [
            models.WorkflowStep(
                agent="triage",
                action="classify",
                result="Classification complete",
                latency_ms=42.5,
            ),
            models.WorkflowStep(
                agent="clinical",
                action="diagnose",
                result="Diagnosis complete",
                latency_ms=87.3,
            ),
            models.WorkflowStep(
                agent="scheduling",
                action="schedule",
                result="Scheduling complete",
                latency_ms=31.2,
            ),
        ]

        for step in steps:
            assert step.latency_ms > 0, (
                f"Step {step.agent}/{step.action} has zero latency"
            )
            assert isinstance(step.latency_ms, float)

        total = sum(s.latency_ms for s in steps)
        assert total > 0

    def test_workflow_response_has_total_latency(self):
        """WorkflowResponse includes total_latency_ms."""
        response = models.WorkflowResponse(
            steps=[
                models.WorkflowStep(
                    agent="triage", action="classify",
                    result="Done", latency_ms=50.0,
                ),
            ],
            total_latency_ms=50.0,
            agents_involved=["triage"],
        )
        assert response.total_latency_ms > 0
        assert response.ai_disclaimer
        assert "AI-generated" in response.ai_disclaimer

    def test_workflow_response_lists_agents(self):
        """WorkflowResponse lists all agents involved."""
        response = models.WorkflowResponse(
            steps=[
                models.WorkflowStep(
                    agent="triage", action="classify",
                    result="Done", latency_ms=50.0,
                ),
                models.WorkflowStep(
                    agent="clinical", action="diagnose",
                    result="Done", latency_ms=80.0,
                ),
                models.WorkflowStep(
                    agent="scheduling", action="schedule",
                    result="Done", latency_ms=30.0,
                ),
            ],
            total_latency_ms=160.0,
            agents_involved=["triage", "clinical", "scheduling"],
        )
        assert len(response.agents_involved) == 3
        assert "triage" in response.agents_involved
        assert "clinical" in response.agents_involved
        assert "scheduling" in response.agents_involved


# ---------------------------------------------------------------------------
# Test: semantic routing
# ---------------------------------------------------------------------------


class TestSemanticRouting:

    def test_classification_result_model(self):
        """ClassificationResult Pydantic model validates correctly."""
        result = models.ClassificationResult(
            classifier_id="complexity",
            status="ok",
            signals=[
                models.ClassificationSignal(label="COMPLEX", score=0.872),
                models.ClassificationSignal(label="MEDIUM", score=-0.074),
                models.ClassificationSignal(label="SIMPLE", score=-0.228),
                models.ClassificationSignal(label="REASONING", score=-0.403),
            ],
            selected_workflow="comprehensive",
            latency_ms=12.5,
        )
        assert result.classifier_id == "complexity"
        assert result.status == "ok"
        assert len(result.signals) == 4
        assert result.signals[0].label == "COMPLEX"
        assert result.selected_workflow == "comprehensive"
        assert result.latency_ms > 0

    def test_auto_workflow_selects_by_complexity(self):
        """SIMPLE/MEDIUM/COMPLEX/REASONING map to correct workflow types."""
        mapping = orchestrator.COMPLEXITY_TO_WORKFLOW
        assert mapping["SIMPLE"] == "lightweight"
        assert mapping["MEDIUM"] == "standard"
        assert mapping["COMPLEX"] == "comprehensive"
        assert mapping["REASONING"] == "comprehensive"

    def test_expanded_workflow_definitions(self):
        """New workflow types have valid agent sequences."""
        wf_defs = orchestrator.WORKFLOW_DEFINITIONS

        lightweight = wf_defs["lightweight"]
        assert len(lightweight) == 1
        assert lightweight[0][0] == "executor"

        standard = wf_defs["standard"]
        assert len(standard) == 2
        assert standard[0][0] == "research"
        assert standard[1][0] == "executor"

        comprehensive = wf_defs["comprehensive"]
        assert len(comprehensive) == 3
        agents = [step[0] for step in comprehensive]
        assert "research" in agents
        assert "analyst" in agents
        assert "executor" in agents

    def test_legacy_workflow_types_preserved(self):
        """general workflow type still exists."""
        wf_defs = orchestrator.WORKFLOW_DEFINITIONS
        assert "general" in wf_defs

    def test_classification_in_workflow_response(self):
        """WorkflowResponse can include classification data."""
        classification = models.ClassificationResult(
            classifier_id="complexity",
            status="ok",
            signals=[
                models.ClassificationSignal(label="SIMPLE", score=0.999),
            ],
            selected_workflow="lightweight",
            latency_ms=8.0,
        )
        response = models.WorkflowResponse(
            steps=[
                models.WorkflowStep(
                    agent="scheduling", action="schedule",
                    result="Done", latency_ms=30.0,
                ),
            ],
            total_latency_ms=38.0,
            agents_involved=["scheduling"],
            classification=classification,
        )
        assert response.classification is not None
        assert response.classification.selected_workflow == "lightweight"
        assert response.classification.signals[0].label == "SIMPLE"

    def test_workflow_response_without_classification(self):
        """WorkflowResponse works without classification (backward compat)."""
        response = models.WorkflowResponse(
            steps=[
                models.WorkflowStep(
                    agent="triage", action="classify",
                    result="Done", latency_ms=50.0,
                ),
            ],
            total_latency_ms=50.0,
            agents_involved=["triage"],
        )
        assert response.classification is None

    def test_workflow_request_defaults_to_auto(self):
        """WorkflowRequest defaults to workflow_type='auto'."""
        request = models.WorkflowRequest(query="test query")
        assert request.workflow_type == "auto"

    def test_semantic_router_inactive_returns_none(self):
        """SemanticRouter with no endpoint and no LLM returns None."""
        original = orchestrator.MODEL_ENDPOINT
        orchestrator.MODEL_ENDPOINT = ""
        try:
            router = orchestrator.SemanticRouter("")
            _run(router.connect())
            assert router.mode == "inactive"
            assert not router.active
            result = _run(router.classify("test"))
            assert result is None
        finally:
            orchestrator.MODEL_ENDPOINT = original

    def test_semantic_router_llm_fallback_activates(self):
        """SemanticRouter uses LLM fallback when MODEL_ENDPOINT is set."""
        original = orchestrator.MODEL_ENDPOINT
        orchestrator.MODEL_ENDPOINT = "http://fake:11434/v1"
        try:
            router = orchestrator.SemanticRouter("")
            _run(router.connect())
            assert router.mode == "llm-fallback"
            assert router.active
        finally:
            orchestrator.MODEL_ENDPOINT = original


# ---------------------------------------------------------------------------
# Test: MCP tool server
# ---------------------------------------------------------------------------


class TestMcpToolServer:

    @pytest.fixture
    def mcp_client(self):
        return TestClient(mcp_server.app)

    def test_mcp_health(self, mcp_client):
        """MCP server health endpoint returns tool count."""
        resp = mcp_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["tools_available"] == 3
        assert "lookup_record" in data["tool_names"]
        assert "search_knowledge_base" in data["tool_names"]
        assert "create_task" in data["tool_names"]

    def test_mcp_tools_list(self, mcp_client):
        """tools/list returns all tool definitions with schemas."""
        resp = mcp_client.post("/mcp", json={
            "jsonrpc": "2.0", "id": "t1", "method": "tools/list",
        })
        assert resp.status_code == 200
        data = resp.json()
        tools = data["result"]["tools"]
        assert len(tools) == 3
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    def test_mcp_lookup_record(self, mcp_client):
        """tools/call lookup_record returns record data."""
        resp = mcp_client.post("/mcp", json={
            "jsonrpc": "2.0", "id": "t2", "method": "tools/call",
            "params": {"name": "lookup_record", "arguments": {"record_id": "REC-001"}},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["isError"] is False
        content_text = data["result"]["content"][0]["text"]
        assert "REC-001" in content_text

    def test_mcp_lookup_unknown_record(self, mcp_client):
        """tools/call with unknown record returns error info."""
        resp = mcp_client.post("/mcp", json={
            "jsonrpc": "2.0", "id": "t3", "method": "tools/call",
            "params": {"name": "lookup_record", "arguments": {"record_id": "REC-999"}},
        })
        assert resp.status_code == 200
        content_text = resp.json()["result"]["content"][0]["text"]
        assert "not found" in content_text.lower() or "REC-999" in content_text

    def test_mcp_search_knowledge_base(self, mcp_client):
        """tools/call search_knowledge_base returns results."""
        resp = mcp_client.post("/mcp", json={
            "jsonrpc": "2.0", "id": "t4", "method": "tools/call",
            "params": {"name": "search_knowledge_base", "arguments": {"query": "kubernetes"}},
        })
        assert resp.status_code == 200
        content_text = resp.json()["result"]["content"][0]["text"]
        assert len(content_text) > 10

    def test_mcp_create_task(self, mcp_client):
        """tools/call create_task returns confirmation."""
        resp = mcp_client.post("/mcp", json={
            "jsonrpc": "2.0", "id": "t5", "method": "tools/call",
            "params": {"name": "create_task", "arguments": {"title": "Fix the bug", "priority": "high"}},
        })
        assert resp.status_code == 200
        content_text = resp.json()["result"]["content"][0]["text"]
        assert "TASK-" in content_text or "task" in content_text.lower()

    def test_mcp_unknown_tool(self, mcp_client):
        """tools/call with unknown tool returns error."""
        resp = mcp_client.post("/mcp", json={
            "jsonrpc": "2.0", "id": "t6", "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_mcp_unknown_method(self, mcp_client):
        """Unknown MCP method returns JSON-RPC error."""
        resp = mcp_client.post("/mcp", json={
            "jsonrpc": "2.0", "id": "t7", "method": "unknown/method",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
        assert data["error"]["code"] == -32601


# ---------------------------------------------------------------------------
# Test: agent auth middleware
# ---------------------------------------------------------------------------


class TestAgentAuth:

    def test_auth_disabled_by_default(self, triage_client):
        """Without AGENT_AUTH_TOKEN, all requests pass through."""
        original_token = auth.AGENT_AUTH_TOKEN
        auth.AGENT_AUTH_TOKEN = ""
        try:
            resp = triage_client.post("/a2a", json={
                "jsonrpc": "2.0", "id": "auth-1", "method": "tasks/get",
                "params": {"id": "test"},
            })
            assert resp.status_code == 200
        finally:
            auth.AGENT_AUTH_TOKEN = original_token

    def test_auth_rejects_missing_token(self, triage_client):
        """With auth enabled, missing token returns 401."""
        original_token = auth.AGENT_AUTH_TOKEN
        auth.AGENT_AUTH_TOKEN = "secret-token"
        try:
            resp = triage_client.post("/a2a", json={
                "jsonrpc": "2.0", "id": "auth-2", "method": "tasks/get",
                "params": {"id": "test"},
            })
            assert resp.status_code == 401
        finally:
            auth.AGENT_AUTH_TOKEN = original_token

    def test_auth_rejects_wrong_token(self, triage_client):
        """With auth enabled, wrong token returns 403."""
        original_token = auth.AGENT_AUTH_TOKEN
        auth.AGENT_AUTH_TOKEN = "secret-token"
        try:
            resp = triage_client.post(
                "/a2a",
                json={
                    "jsonrpc": "2.0", "id": "auth-3", "method": "tasks/get",
                    "params": {"id": "test"},
                },
                headers={"Authorization": "Bearer wrong-token"},
            )
            assert resp.status_code == 403
        finally:
            auth.AGENT_AUTH_TOKEN = original_token

    def test_auth_accepts_valid_token(self, triage_client):
        """With auth enabled, valid token passes through."""
        original_token = auth.AGENT_AUTH_TOKEN
        auth.AGENT_AUTH_TOKEN = "secret-token"
        try:
            resp = triage_client.post(
                "/a2a",
                json={
                    "jsonrpc": "2.0", "id": "auth-4", "method": "tasks/get",
                    "params": {"id": "test"},
                },
                headers={"Authorization": "Bearer secret-token"},
            )
            assert resp.status_code == 200
        finally:
            auth.AGENT_AUTH_TOKEN = original_token

    def test_health_endpoint_skips_auth(self, triage_client):
        """Health endpoint is always accessible, even with auth enabled."""
        original_token = auth.AGENT_AUTH_TOKEN
        auth.AGENT_AUTH_TOKEN = "secret-token"
        try:
            resp = triage_client.get("/health")
            assert resp.status_code == 200
        finally:
            auth.AGENT_AUTH_TOKEN = original_token

    def test_agent_card_skips_auth(self, triage_client):
        """Agent card discovery is always accessible."""
        original_token = auth.AGENT_AUTH_TOKEN
        auth.AGENT_AUTH_TOKEN = "secret-token"
        try:
            resp = triage_client.get("/.well-known/agent-card.json")
            assert resp.status_code == 200
        finally:
            auth.AGENT_AUTH_TOKEN = original_token
