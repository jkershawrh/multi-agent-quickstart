"""RED/GREEN proof for progressive workflow events and seat-local history."""

import asyncio
import json
import pathlib
import sys


SRC_DIR = pathlib.Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

import models
import orchestrator
import ui
from fastapi.testclient import TestClient


class FakeA2AClient:
    """Return deterministic results while preserving observable step ordering."""

    async def send_task(
        self,
        agent_name: str,
        text: str,
        model_override: str = "",
        endpoint_override: str = "",
    ) -> dict:
        await asyncio.sleep({"research": 0.003, "analyst": 0.002, "executor": 0.001}[agent_name])
        return {
            "result": {
                "artifacts": [
                    {"parts": [{"text": f"{agent_name} completed: {text}"}]}
                ]
            }
        }


class InactiveRouter:
    active = False


def _collect_events() -> list[dict]:
    async def collect() -> list[dict]:
        events = []
        async for event in orchestrator.workflow_events(
            FakeA2AClient(),
            "Investigate, analyze, and resolve the incident",
            "comprehensive",
            router=InactiveRouter(),
        ):
            events.append(event)
        return events

    return asyncio.run(collect())


def test_steps_are_published_as_they_complete_before_the_next_agent_starts():
    events = _collect_events()
    event_types = [event["event"] for event in events]

    assert event_types == [
        "workflow_started",
        "agent_started",
        "agent_completed",
        "agent_started",
        "agent_completed",
        "agent_started",
        "agent_completed",
        "workflow_completed",
    ]
    completed = [event for event in events if event["event"] == "agent_completed"]
    assert [event["agent"] for event in completed] == ["research", "analyst", "executor"]
    assert all(event["latency_ms"] > 0 for event in completed)
    assert all(event["model"] for event in completed)
    assert all(event["completed_at"] >= event["started_at"] for event in completed)
    assert len({event["completed_at"] for event in completed}) == 3


def test_next_agent_receives_prior_agent_result():
    events = _collect_events()
    completed = [event for event in events if event["event"] == "agent_completed"]

    assert "research completed" in completed[1]["result"]
    assert "analyst completed" in completed[2]["result"]


def test_workflow_completion_retains_the_existing_response_contract():
    events = _collect_events()
    response = models.WorkflowResponse(**events[-1]["response"])

    assert [step.agent for step in response.steps] == ["research", "analyst", "executor"]
    assert response.total_latency_ms > 0
    assert response.run_id == events[0]["run_id"]
    assert response.started_at <= response.completed_at


def test_stream_route_emits_ndjson_before_returning_the_compatible_response(monkeypatch):
    monkeypatch.setattr(orchestrator, "a2a_client", FakeA2AClient())
    response = TestClient(orchestrator.app).post(
        "/api/v1/workflow/stream",
        json={"query": "Investigate and resolve", "workflow_type": "comprehensive"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    events = [json.loads(line) for line in response.text.splitlines()]
    assert events[0]["event"] == "workflow_started"
    assert events[-1]["event"] == "workflow_completed"
    assert models.WorkflowResponse(**events[-1]["response"]).steps


def test_history_is_seat_local_bounded_and_newest_first():
    history = []
    for index in range(25):
        history = ui.add_history_entry(
            history,
            {
                "run_id": f"run-{index}",
                "query": f"query-{index}",
                "workflow": "comprehensive",
                "status": "completed",
                "total_latency_ms": index,
                "completed_at": f"2026-09-14T00:00:{index:02d}Z",
                "timeline": f"timeline-{index}",
            },
        )

    assert len(history) == 20
    assert history[0]["run_id"] == "run-24"
    assert history[-1]["run_id"] == "run-5"
    rendered = ui.render_history(history)
    assert "query-24" in rendered
    assert "timeline-24" in rendered
    assert "query-4" not in rendered


def test_ui_reveals_running_and_completed_steps_and_saves_the_run(monkeypatch):
    events = _collect_events()

    class FakeStreamResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def raise_for_status(self):
            return None

        def iter_lines(self):
            return [json.dumps(event) for event in events]

    monkeypatch.setattr(ui.httpx, "stream", lambda *args, **kwargs: FakeStreamResponse())
    updates = list(ui.run_workflow("Investigate and resolve", "comprehensive", []))

    assert len(updates) >= 8
    assert "Evidence gathered — RUNNING" in updates[1][3]
    assert "Evidence gathered — DONE" in updates[2][3]
    assert "Assessment and likely causes — RUNNING" in updates[3][3]
    assert "Proposed governed action — DONE" in updates[-1][3]
    assert "Total workflow time:" in updates[-1][3]
    assert updates[-1][5][0]["query"] == "Investigate and resolve"
    assert "Evidence gathered" in updates[-1][4]


def test_workspace_leads_with_the_business_workload_and_hides_diagnostics():
    config = json.dumps(ui.demo.config, default=str)

    assert "AI Operations Incident Workspace" in config
    assert "Incident Response Package" in config
    assert "Supporting Evidence" in config
    assert "Investigate Incident" in config
    assert "Technical Details" in config
    assert "Multi-Agent Quickstart" not in config
    assert '"label": "Agent Results"' not in config
    assert '"label": "Routing Decision"' not in config


def test_completed_agents_are_explained_as_business_stages(monkeypatch):
    events = _collect_events()

    class FakeStreamResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def raise_for_status(self):
            return None

        def iter_lines(self):
            return [json.dumps(event) for event in events]

    monkeypatch.setattr(ui.httpx, "stream", lambda *args, **kwargs: FakeStreamResponse())
    completed = list(
        ui.run_workflow("Investigate and resolve", "comprehensive", [])
    )[-1]

    assert "EVIDENCE GATHERED" in completed[1]
    assert "ASSESSMENT AND LIKELY CAUSES" in completed[1]
    assert "PROPOSED GOVERNED ACTION" in completed[1]
    assert "HUMAN REVIEW REQUIRED" in completed[1]
