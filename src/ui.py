"""Gradio UI for the Multi-Agent Quickstart."""

import os

import gradio as gr
import httpx

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://localhost:8000")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8004")

WORKFLOW_CHOICES = ["auto", "lightweight", "standard", "comprehensive", "general"]

EXAMPLE_QUERIES = [
    ["Create a task to fix the login timeout bug", "auto"],
    ["Investigate the recent spike in API error rates in EMEA", "auto"],
    ["Look up record REC-001 and recommend next steps", "comprehensive"],
    ["Search the knowledge base for Kubernetes resource limits best practices", "auto"],
    ["Assign a high-priority task to review the security audit findings", "comprehensive"],
    ["What is the status of the API migration project?", "lightweight"],
]


def run_workflow(query: str, workflow_type: str) -> tuple[str, str, str]:
    """POST a query and return (routing, agent results, tool data)."""
    if not query.strip():
        return "Enter a query.", "", ""
    try:
        resp = httpx.post(
            f"{ORCHESTRATOR_URL}/api/v1/workflow",
            json={"query": query, "workflow_type": workflow_type},
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as exc:
        return f"HTTP error {exc.response.status_code}: {exc.response.text}", "", ""
    except httpx.RequestError as exc:
        return f"Connection error: {exc}", "", ""

    # --- Routing panel ---
    routing_lines: list[str] = []
    classification = data.get("classification")
    if classification:
        routing_lines.append("SEMANTIC ROUTING ACTIVE")
        routing_lines.append(f"  Classifier:  {classification.get('classifier_id', 'N/A')}")
        routing_lines.append(f"  Workflow:    {classification.get('selected_workflow', 'N/A')}")
        model = classification.get("selected_model", "")
        if model:
            routing_lines.append(f"  Model tier:  {model}")
        routing_lines.append(f"  Latency:     {classification.get('latency_ms', 'N/A')} ms")
        signals = classification.get("signals", [])
        if signals:
            routing_lines.append("")
            routing_lines.append("  Signal rankings:")
            for s in signals:
                bar_len = max(0, int((s["score"] + 1) * 12))
                bar = "#" * bar_len
                routing_lines.append(f"    {s['label']:<12} {s['score']:+.3f}  {bar}")
    else:
        routing_lines.append("STATIC ROUTING")
        routing_lines.append(f"  Workflow: {workflow_type}")
        routing_lines.append("  (llm-d-sc not connected -- using default)")

    routing_lines.append("")
    routing_lines.append(f"Agents involved: {', '.join(data.get('agents_involved', []))}")
    routing_lines.append(f"Total latency:   {data.get('total_latency_ms', 'N/A')} ms")
    routing_lines.append(f"Steps:           {len(data.get('steps', []))}")

    # --- Agent results panel ---
    agent_lines: list[str] = []
    tool_lines: list[str] = []

    for i, step in enumerate(data.get("steps", []), start=1):
        result_text = step.get("result", "")
        agent_name = step.get("agent", "unknown")
        action = step.get("action", "N/A")
        latency = step.get("latency_ms", "N/A")

        # Split MCP tool data from agent prose
        if "[MCP tool data retrieved]" in result_text:
            parts = result_text.split("[MCP tool data retrieved]", 1)
            prose = parts[0].strip()
            tool_data = parts[1].strip() if len(parts) > 1 else ""
        else:
            prose = result_text
            tool_data = ""

        agent_lines.append(f"{'=' * 60}")
        agent_lines.append(f"  Step {i}: {agent_name} / {action}  ({latency} ms)")
        agent_lines.append(f"{'=' * 60}")
        agent_lines.append(prose)
        agent_lines.append("")

        if tool_data:
            tool_lines.append(f"--- {agent_name} / {action} ---")
            for line in tool_data.split("\n"):
                line = line.strip()
                if line.startswith("[") and "]: " in line:
                    tool_name = line.split("]:")[0].lstrip("[")
                    raw_data = line.split("]: ", 1)[1]
                    tool_lines.append(f"  Tool: {tool_name}")
                    # Pretty-print the dict-like data
                    try:
                        import ast
                        parsed = ast.literal_eval(raw_data)
                        if isinstance(parsed, dict):
                            for k, v in parsed.items():
                                tool_lines.append(f"    {k}: {v}")
                        else:
                            tool_lines.append(f"    {raw_data}")
                    except Exception:
                        tool_lines.append(f"    {raw_data}")
                elif line:
                    tool_lines.append(f"  {line}")
            tool_lines.append("")

    if not tool_lines:
        tool_lines.append("No MCP tools were called for this query.")
        tool_lines.append("")
        tool_lines.append("Try queries that mention:")
        tool_lines.append("  - Records (e.g. 'REC-001')")
        tool_lines.append("  - Knowledge base searches")
        tool_lines.append("  - Task creation or assignments")

    agent_lines.append(
        "** AI Disclaimer: These results are AI-generated and must not "
        "be used as a substitute for professional advice. **"
    )

    return "\n".join(routing_lines), "\n".join(agent_lines), "\n".join(tool_lines)


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

with gr.Blocks(title="Multi-Agent Quickstart", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# Multi-Agent Quickstart\n"
        "A2A Protocol | Semantic Routing | MCP Tool Calling | Agent Auth"
    )

    with gr.Tab("Workflow"):
        with gr.Row():
            query_input = gr.Textbox(
                label="Query",
                placeholder="Describe what you need...",
                lines=3,
                scale=3,
            )
            workflow_type = gr.Dropdown(
                choices=WORKFLOW_CHOICES,
                value="auto",
                label="Workflow Type",
                info="auto = let llm-d-sc decide; or pick explicitly",
                scale=1,
            )
        run_btn = gr.Button("Run Workflow", variant="primary")

        with gr.Row():
            routing_output = gr.Textbox(
                label="Routing Decision",
                lines=12,
                scale=1,
            )
            agent_output = gr.Textbox(
                label="Agent Results",
                lines=12,
                scale=2,
            )
            tool_output = gr.Textbox(
                label="MCP Tool Data",
                lines=12,
                scale=1,
            )

        run_btn.click(
            fn=run_workflow,
            inputs=[query_input, workflow_type],
            outputs=[routing_output, agent_output, tool_output],
        )

        gr.Examples(
            examples=EXAMPLE_QUERIES,
            inputs=[query_input, workflow_type],
            label="Example queries",
        )

    with gr.Tab("Agent Registry"):
        refresh_btn = gr.Button("Refresh Agents")
        agents_output = gr.Textbox(label="Discovered Agents", lines=15)
        refresh_btn.click(fn=fetch_agents, inputs=[], outputs=agents_output)

    with gr.Tab("MCP Tools"):
        tools_btn = gr.Button("Refresh Tools")
        tools_output = gr.Textbox(label="Available MCP Tools", lines=20)
        tools_btn.click(fn=fetch_tools, inputs=[], outputs=tools_output)

    with gr.Tab("System Status"):
        stats_btn = gr.Button("Refresh")
        stats_output = gr.Textbox(label="System Health", lines=15)
        stats_btn.click(fn=fetch_stats, inputs=[], outputs=stats_output)

    gr.Markdown(
        "---\n"
        "Agent responses are AI-generated -- verify "
        "recommendations with qualified professionals."
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
