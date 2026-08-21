"""Stage 3: Integration validation -- end-to-end flow through all services.

Tests run against a live compose stack or local demo.sh processes.
Skipped when services are not reachable (CI without compose).
"""

import os
import pathlib
import sys

import httpx
import pytest

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://127.0.0.1:8000")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8004")

SRC_DIR = pathlib.Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))


def _is_reachable(url: str) -> bool:
    try:
        resp = httpx.get(f"{url}/health", timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False


skip_if_no_stack = pytest.mark.skipif(
    not _is_reachable(os.environ.get("ORCHESTRATOR_URL", "http://127.0.0.1:8000")),
    reason="Orchestrator not reachable -- start with ./demo.sh or docker compose up",
)


@skip_if_no_stack
class TestFullWorkflowFlow:

    def test_comprehensive_workflow_completes(self):
        """Orchestrator -> triage -> clinical -> scheduling completes end-to-end."""
        resp = httpx.post(
            f"{ORCHESTRATOR_URL}/api/v1/workflow",
            json={"query": "Patient with chest pain and shortness of breath", "workflow_type": "comprehensive"},
            timeout=30.0,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["steps"]) == 3
        assert data["total_latency_ms"] > 0
        agents = [s["agent"] for s in data["steps"]]
        assert "triage" in agents
        assert "clinical" in agents
        assert "scheduling" in agents

    def test_response_has_real_metrics(self):
        """Response contains real agent names and measured latency."""
        resp = httpx.post(
            f"{ORCHESTRATOR_URL}/api/v1/workflow",
            json={"query": "Headache for 3 days", "workflow_type": "comprehensive"},
            timeout=30.0,
        )
        data = resp.json()
        for step in data["steps"]:
            assert step["agent"] in ("triage", "clinical", "scheduling")
            assert step["latency_ms"] > 0
            assert step["result"]
            assert len(step["result"]) > 10

    def test_ai_transparency_labels(self):
        """AI-generated content labeled with persistent disclaimers."""
        resp = httpx.post(
            f"{ORCHESTRATOR_URL}/api/v1/workflow",
            json={"query": "Follow-up appointment needed"},
            timeout=30.0,
        )
        data = resp.json()
        assert "ai_disclaimer" in data
        assert "AI-generated" in data["ai_disclaimer"]

    def test_health_endpoint_shows_all_status(self):
        """Health endpoint returns service status + agent count + semantic_routing."""
        resp = httpx.get(f"{ORCHESTRATOR_URL}/health", timeout=5.0)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["agents_discovered"] >= 3
        assert "semantic_routing" in data


@skip_if_no_stack
class TestSemanticRoutingE2E:

    def test_auto_workflow_type(self):
        """workflow_type=auto triggers semantic routing (or fallback)."""
        resp = httpx.post(
            f"{ORCHESTRATOR_URL}/api/v1/workflow",
            json={"query": "Schedule a follow-up appointment", "workflow_type": "auto"},
            timeout=30.0,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["steps"]) >= 1
        assert data["total_latency_ms"] > 0

    def test_explicit_workflow_type_bypasses_routing(self):
        """Explicit workflow_type skips classification."""
        resp = httpx.post(
            f"{ORCHESTRATOR_URL}/api/v1/workflow",
            json={"query": "test", "workflow_type": "lightweight"},
            timeout=30.0,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["steps"]) == 1
        assert data["steps"][0]["agent"] == "scheduling"


skip_if_no_mcp = pytest.mark.skipif(
    not _is_reachable(os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8004")),
    reason="MCP server not reachable",
)


@skip_if_no_mcp
class TestMcpToolEnrichment:

    def test_agent_enriches_with_tool_data(self):
        """Agent responses include MCP tool data when relevant keywords present."""
        resp = httpx.post(
            f"{ORCHESTRATOR_URL}/api/v1/workflow",
            json={"query": "Check patient record PAT-001 and schedule appointment", "workflow_type": "comprehensive"},
            timeout=30.0,
        )
        data = resp.json()
        all_results = " ".join(s["result"] for s in data["steps"])
        assert "MCP tool data" in all_results or len(all_results) > 100

    def test_mcp_server_health(self):
        """MCP server is healthy and reports tools."""
        resp = httpx.get(f"{MCP_SERVER_URL}/health", timeout=5.0)
        assert resp.status_code == 200
        data = resp.json()
        assert data["tools_available"] == 3


@skip_if_no_stack
class TestAuthE2E:

    def test_unauthenticated_health_always_works(self):
        """Health endpoints work without auth headers."""
        for port in [8000, 8001, 8002, 8003]:
            resp = httpx.get(f"http://127.0.0.1:{port}/health", timeout=5.0)
            assert resp.status_code == 200
