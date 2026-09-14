"""Gradio UI for the Multi-Agent Quickstart."""

from __future__ import annotations

import ast
import json
import os

import gradio as gr
import httpx

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://localhost:8000")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8004")
AGENT_AUTH_TOKEN = os.environ.get("AGENT_AUTH_TOKEN", "")
UI_WORKFLOW_TIMEOUT = float(os.environ.get("UI_WORKFLOW_TIMEOUT", "300"))
HISTORY_LIMIT = 20

WORKFLOW_CHOICES = ["auto", "lightweight", "standard", "comprehensive", "general"]

BUSINESS_STAGES = {
    "research": ("Evidence gathered", "Collect relevant records and operational knowledge."),
    "analyst": ("Assessment and likely causes", "Correlate evidence and identify the most useful next step."),
    "executor": ("Proposed governed action", "Prepare an action for a person to review and approve."),
}

EXAMPLE_QUERIES = [
    ["Check the status of fictional incident REC-001 and recommend the next action.", "auto"],
    ["Investigate a fictional API error spike, assess likely causes, and prepare a remediation task.", "auto"],
    ["Research Kubernetes resource-request guidance for a fictional service and prepare a safe recommendation.", "comprehensive"],
]


def add_history_entry(history: list[dict] | None, entry: dict) -> list[dict]:
    """Keep a bounded, newest-first history inside this Gradio browser session."""
    return [entry, *list(history or [])][:HISTORY_LIMIT]


def render_history(history: list[dict] | None) -> str:
    """Render seat-local workflow history without sending it to Launchpad."""
    if not history:
        return "No workflows have run in this browser session."
    sections = []
    for entry in history:
        sections.extend(
            [
                "=" * 72,
                f"RUN {entry['run_id']}",
                f"Completed: {entry['completed_at']}",
                f"Route:     {entry['workflow']}",
                f"Duration:  {entry['total_latency_ms'] / 1000:.2f}s",
                f"Status:    {entry['status']}",
                "",
                f"Incident: {entry['query']}",
                "",
                entry["timeline"],
                "",
                entry.get("agent_results", ""),
                "",
                entry.get("tool_data", ""),
                "",
            ]
        )
    return "\n".join(sections)


def _render_timeline(steps: list[dict], total_latency_ms: float | None = None) -> str:
    lines = ["LIVE INCIDENT RESPONSE PROGRESS", ""]
    for step in steps:
        seconds = step.get("latency_ms", 0) / 1000
        if step["status"] == "running":
            state = "RUNNING"
            timing = "timer started"
        else:
            state = "DONE" if step["status"] == "completed" else "FAILED"
            timing = f"{seconds:.2f}s"
        business_stage = BUSINESS_STAGES.get(
            step["agent"], (step["agent"].title(), step["action"])
        )[0]
        lines.append(f"{step['sequence']}. {business_stage} — {state} — {timing}")
        lines.append(f"   started:   {step['started_at']}")
        if step.get("completed_at"):
            lines.append(f"   completed: {step['completed_at']}")
    if total_latency_ms is not None:
        lines.extend(["", f"Total workflow time: {total_latency_ms / 1000:.2f}s"])
    return "\n".join(lines)


def _tool_parts(result_text: str) -> tuple[str, str]:
    if "[MCP tool data retrieved]" not in result_text:
        return result_text, ""
    parts = result_text.split("[MCP tool data retrieved]", 1)
    return parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""


def _format_tool_data(agent_name: str, action: str, tool_data: str) -> list[str]:
    lines = [f"--- {agent_name} / {action} ---"]
    for line in tool_data.split("\n"):
        line = line.strip()
        if line.startswith("[") and "]: " in line:
            tool_name = line.split("]: ")[0].lstrip("[")
            raw_data = line.split("]: ", 1)[1]
            lines.append(f"  Tool: {tool_name}")
            try:
                parsed = ast.literal_eval(raw_data)
                if isinstance(parsed, dict):
                    lines.extend(f"    {key}: {value}" for key, value in parsed.items())
                else:
                    lines.append(f"    {raw_data}")
            except Exception:
                lines.append(f"    {raw_data}")
        elif line:
            lines.append(f"  {line}")
    lines.append("")
    return lines


def run_workflow(query: str, workflow_type: str, history: list[dict] | None):
    """Stream progress, reveal each completed agent, and retain local history."""
    if not query.strip():
        yield "Describe a fictional incident.", "", "", "", render_history(history), history or []
        return

    route_lines = ["Selecting the right response path..."]
    agent_lines: list[str] = []
    tool_lines: list[str] = []
    steps: list[dict] = []
    run_id = "pending"
    resolved_workflow = workflow_type
    current_history = list(history or [])
    headers = {"Authorization": f"Bearer {AGENT_AUTH_TOKEN}"} if AGENT_AUTH_TOKEN else {}

    def outputs(total_latency_ms: float | None = None):
        tools = tool_lines or ["No governed data tools have completed for this run."]
        return (
            "\n".join(route_lines),
            "\n".join(agent_lines) or "Waiting for the first agent result...",
            "\n".join(tools),
            _render_timeline(steps, total_latency_ms),
            render_history(current_history),
            current_history,
        )

    try:
        with httpx.stream(
            "POST",
            f"{ORCHESTRATOR_URL}/api/v1/workflow/stream",
            json={"query": query, "workflow_type": workflow_type},
            headers=headers,
            timeout=UI_WORKFLOW_TIMEOUT,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                event = json.loads(line)
                event_type = event["event"]
                run_id = event.get("run_id", run_id)

                if event_type == "workflow_started":
                    if workflow_type == "auto":
                        route_lines[:] = [
                            "AUTOMATIC WORKFLOW SELECTION",
                            "Assessing the incident and choosing an appropriate response depth...",
                        ]
                    else:
                        route_lines[:] = [
                            "INSTRUCTOR-SELECTED WORKFLOW",
                            f"  Response depth: {workflow_type}",
                        ]
                    yield outputs()
                elif event_type == "classification_completed":
                    resolved_workflow = event["resolved_workflow"]
                    classification = event.get("classification")
                    route_lines[:] = ["AUTOMATIC WORKFLOW SELECTED"]
                    if classification:
                        route_lines.extend(
                            [
                                f"  Response depth: {resolved_workflow}",
                                f"  Model tier:     {classification.get('selected_model', 'N/A')}",
                                f"  Selection time: {classification.get('latency_ms', 'N/A')} ms",
                                "  Why it matters: simple requests use fewer stages; complex incidents receive deeper analysis.",
                            ]
                        )
                    else:
                        route_lines.extend(
                            [
                                f"  Response depth: {resolved_workflow}",
                                "  Automatic selection was unavailable, so the safe comprehensive path was used.",
                            ]
                        )
                    yield outputs()
                elif event_type == "agent_started":
                    steps.append(
                        {
                            "sequence": event["sequence"],
                            "agent": event["agent"],
                            "action": event["action"],
                            "status": "running",
                            "started_at": event["started_at"],
                        }
                    )
                    yield outputs()
                elif event_type == "agent_completed":
                    step = next(item for item in steps if item["sequence"] == event["sequence"])
                    step.update(
                        status=event["status"],
                        latency_ms=event["latency_ms"],
                        completed_at=event["completed_at"],
                    )
                    prose, tool_data = _tool_parts(event["result"])
                    stage_title, stage_purpose = BUSINESS_STAGES.get(
                        event["agent"],
                        (event["agent"].title(), event["action"]),
                    )
                    agent_lines.extend(
                        [
                            f"STEP {event['sequence']} — {stage_title.upper()}",
                            stage_purpose,
                            f"Completed in {event['latency_ms'] / 1000:.2f}s using {event.get('model', 'default')}",
                            "-" * 60,
                            prose,
                            "",
                        ]
                    )
                    if tool_data:
                        tool_lines.extend(
                            _format_tool_data(event["agent"], event["action"], tool_data)
                        )
                    yield outputs()
                elif event_type == "workflow_completed":
                    total_latency_ms = event["total_latency_ms"]
                    agent_lines.append(
                        "HUMAN REVIEW REQUIRED\n"
                        "This is an AI-generated response package. A qualified person must "
                        "verify the evidence and approve any action."
                    )
                    if not tool_lines:
                        tool_lines.extend(
                            [
                                "No governed data tools were needed for this incident.",
                                "Try a record lookup, knowledge-base search, or task-creation scenario.",
                            ]
                        )
                    timeline = _render_timeline(steps, total_latency_ms)
                    current_history = add_history_entry(
                        current_history,
                        {
                            "run_id": run_id,
                            "query": query,
                            "workflow": resolved_workflow,
                            "status": "completed",
                            "total_latency_ms": total_latency_ms,
                            "completed_at": event["completed_at"],
                            "timeline": timeline,
                            "agent_results": "\n".join(agent_lines),
                            "tool_data": "\n".join(tool_lines),
                        },
                    )
                    yield outputs(total_latency_ms)
    except httpx.HTTPStatusError as exc:
        route_lines[:] = [f"HTTP error {exc.response.status_code}: {exc.response.text}"]
        yield outputs()
    except httpx.RequestError as exc:
        route_lines[:] = [f"Connection error: {exc}"]
        yield outputs()


def fetch_agents() -> str:
    """GET the agent registry from the orchestrator."""
    try:
        resp = httpx.get(f"{ORCHESTRATOR_URL}/api/v1/agents", timeout=10.0)
        resp.raise_for_status()
        agents = resp.json()
    except httpx.HTTPStatusError as exc:
        return f"HTTP error {exc.response.status_code}: {exc.response.text}"
    except httpx.RequestError as exc:
        return f"Connection error: {exc}"

    agent_list = agents.get("agents", []) if isinstance(agents, dict) else agents
    if not agent_list:
        return "No agents discovered."

    lines: list[str] = []
    for agent in agent_list:
        lines.append(f"{'=' * 40}")
        lines.append(f"  {agent.get('name', 'unknown').upper()}")
        lines.append(f"{'=' * 40}")
        lines.append(f"  URL:    {agent.get('url', 'N/A')}")
        lines.append(f"  Status: {agent.get('status', 'N/A')}")
        skills = agent.get("skills", [])
        if skills:
            skill_names = [
                s.get("name", s.get("id", str(s)))
                if isinstance(s, dict) else str(s)
                for s in skills
            ]
            lines.append(f"  Skills: {', '.join(skill_names)}")
        lines.append("")
    return "\n".join(lines)


def fetch_tools() -> str:
    """GET the MCP tool listing."""
    try:
        resp = httpx.post(
            f"{MCP_SERVER_URL}/mcp",
            json={"jsonrpc": "2.0", "id": "ui-list", "method": "tools/list"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as exc:
        return f"HTTP error {exc.response.status_code}: {exc.response.text}"
    except httpx.RequestError as exc:
        return f"Connection error: {exc}"

    tools = data.get("result", {}).get("tools", [])
    if not tools:
        return "No tools available."

    lines: list[str] = []
    for tool in tools:
        lines.append(f"{'=' * 40}")
        lines.append(f"  {tool['name']}")
        lines.append(f"{'=' * 40}")
        lines.append(f"  {tool.get('description', 'N/A')}")
        schema = tool.get("inputSchema", {})
        props = schema.get("properties", {})
        if props:
            lines.append("  Parameters:")
            for pname, pschema in props.items():
                req = " (required)" if pname in schema.get("required", []) else ""
                lines.append(f"    - {pname}: {pschema.get('type', '?')}{req}")
                if pschema.get("description"):
                    lines.append(f"      {pschema['description']}")
        lines.append("")
    return "\n".join(lines)


def fetch_stats() -> str:
    """GET health from orchestrator and MCP server."""
    lines: list[str] = []

    try:
        resp = httpx.get(f"{ORCHESTRATOR_URL}/health", timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        lines.append("ORCHESTRATOR")
        lines.append(f"  Status:           {data.get('status', 'N/A')}")
        lines.append(f"  Agents discovered: {data.get('agents_discovered', 'N/A')}")
        agent_names = data.get("agent_names", [])
        if agent_names:
            lines.append(f"  Agent names:      {', '.join(str(n) for n in agent_names)}")
        lines.append(f"  Semantic routing: {data.get('semantic_routing', 'N/A')}")
    except Exception as exc:
        lines.append(f"Orchestrator: {exc}")

    lines.append("")

    try:
        resp = httpx.get(f"{MCP_SERVER_URL}/health", timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        lines.append("MCP TOOL SERVER")
        lines.append(f"  Status:          {data.get('status', 'N/A')}")
        lines.append(f"  Tools available: {data.get('tools_available', 'N/A')}")
        tool_names = data.get("tool_names", [])
        if tool_names:
            lines.append(f"  Tool names:      {', '.join(tool_names)}")
    except Exception as exc:
        lines.append(f"MCP Server: {exc}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Build the Gradio interface
# ---------------------------------------------------------------------------

with gr.Blocks(title="AI Operations Incident Workspace", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# AI Operations Incident Workspace\n"
        "Investigate a fictional service incident, assemble evidence, assess likely "
        "causes, and prepare a governed action for human approval."
    )
    gr.Markdown(
        "**What this workload demonstrates:** specialized AI agents can coordinate "
        "an operations response while governed tools, guardrails, and a human "
        "decision remain explicit boundaries."
    )

    history_state = gr.State([])

    with gr.Tab("Incident Workspace"):
        gr.Markdown(
            "## 1. Describe the incident\n"
            "Use fictional or sanitized information. The workspace will choose a "
            "response depth automatically unless an instructor opens the advanced option."
        )
        with gr.Row():
            query_input = gr.Textbox(
                label="Fictional incident or operations request",
                placeholder="Example: Investigate an API error spike and prepare a remediation task.",
                lines=4,
                scale=3,
            )
            timeline_output = gr.Textbox(
                label="Live response progress",
                value="Waiting for an incident.",
                lines=8,
                scale=2,
            )

        with gr.Accordion("Advanced response options", open=False):
            workflow_type = gr.Dropdown(
                choices=WORKFLOW_CHOICES,
                value="auto",
                label="Response depth",
                info="Keep Automatic for the guided business scenario.",
            )

        run_btn = gr.Button("Investigate Incident", variant="primary")

        gr.Examples(
            examples=EXAMPLE_QUERIES,
            inputs=[query_input, workflow_type],
            label="Guided incident scenarios",
        )

        gr.Markdown(
            "## 2. Review the response package\n"
            "Results appear as each dependent stage completes. Evidence informs the "
            "assessment; the proposed action still requires human review."
        )

        with gr.Row():
            agent_output = gr.Textbox(
                label="Incident Response Package",
                lines=20,
                scale=3,
            )
            tool_output = gr.Textbox(
                label="Supporting Evidence",
                lines=20,
                scale=2,
            )

        with gr.Accordion("Why this response path was selected", open=False):
            routing_output = gr.Textbox(
                label="Workflow selection details",
                lines=8,
            )

        with gr.Accordion("Previous incident runs (this seat and browser session)", open=False):
            history_output = gr.Textbox(
                label="Run history",
                value="No incident workflows have run in this browser session.",
                lines=24,
            )
            clear_history_btn = gr.Button("Clear History")

        run_btn.click(
            fn=run_workflow,
            inputs=[query_input, workflow_type, history_state],
            outputs=[
                routing_output,
                agent_output,
                tool_output,
                timeline_output,
                history_output,
                history_state,
            ],
        )
        clear_history_btn.click(
            fn=lambda: ("No incident workflows have run in this browser session.", []),
            inputs=[],
            outputs=[history_output, history_state],
        )

    with gr.Tab("Technical Details"):
        gr.Markdown(
            "## How the workload operates\n"
            "The orchestrator delegates bounded work to independently discoverable "
            "agents. Governed MCP tools remain separate from model inference, and "
            "guardrails screen inputs and outputs."
        )
        with gr.Accordion("Agent responsibilities and discovery", open=True):
            gr.Markdown(
                "**Research** gathers evidence. **Analyst** assesses likely causes. "
                "**Executor** prepares a proposed action. Each role publishes an A2A card."
            )
            refresh_btn = gr.Button("Refresh Agent Registry")
            agents_output = gr.Textbox(label="Discovered agent contracts", lines=15)
            refresh_btn.click(fn=fetch_agents, inputs=[], outputs=agents_output)

        with gr.Accordion("Governed tools", open=False):
            gr.Markdown(
                "MCP tools perform schema-defined lookup or task actions outside the "
                "language model so access can be authorized, tested, and audited."
            )
            tools_btn = gr.Button("Refresh Governed Tools")
            tools_output = gr.Textbox(label="Available tool contracts", lines=20)
            tools_btn.click(fn=fetch_tools, inputs=[], outputs=tools_output)

        with gr.Accordion("Runtime health", open=False):
            stats_btn = gr.Button("Refresh System Status")
            stats_output = gr.Textbox(label="Technical system health", lines=15)
            stats_btn.click(fn=fetch_stats, inputs=[], outputs=stats_output)

    gr.Markdown(
        "---\n"
        "Agent responses are AI-generated. Verify evidence and approve actions through "
        "your organization's established operational process."
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
