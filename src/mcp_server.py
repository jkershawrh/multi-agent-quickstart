"""MCP Tool Server -- domain-agnostic tools for agent workflows.

Implements a subset of the Model Context Protocol (MCP) over HTTP,
exposing tools that agents can call for external data during task
processing. All data is simulated for demo purposes.

Replace the demo data and tool implementations with your own domain
logic to customize this for your use case.
"""

import logging
import os
import uuid

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("mcp-server")

MCP_PORT = int(os.environ.get("MCP_PORT", "8004"))

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "lookup_record",
        "description": "Look up a record by ID from the data store. Returns the record's title, status, priority, assignee, and description.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "record_id": {
                    "type": "string",
                    "description": "Record identifier (e.g. REC-001)",
                },
            },
            "required": ["record_id"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "Search the knowledge base by query keywords. Returns matching articles with titles, summaries, and tags.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords (matched against article titles and tags)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_task",
        "description": "Create a new task or action item. Returns a confirmation with the generated task ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short title for the task",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of what needs to be done",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Task priority level",
                },
                "assignee": {
                    "type": "string",
                    "description": "Person or team to assign the task to",
                },
            },
            "required": ["title"],
        },
    },
]

# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

RECORDS = {
    "REC-001": {
        "title": "API gateway migration to v2",
        "status": "in_progress",
        "priority": "high",
        "created_date": "2026-07-10",
        "assigned_to": "Platform Team",
        "tags": ["infrastructure", "api", "migration"],
        "description": "Migrate all services from API gateway v1 to v2. Includes updating auth flow, rate limiting config, and routing rules.",
    },
    "REC-002": {
        "title": "Quarterly security audit",
        "status": "open",
        "priority": "high",
        "created_date": "2026-08-01",
        "assigned_to": "Security Team",
        "tags": ["security", "audit", "compliance"],
        "description": "Conduct Q3 security audit covering dependency scanning, access review, and penetration testing of public endpoints.",
    },
    "REC-003": {
        "title": "Onboarding flow redesign",
        "status": "completed",
        "priority": "medium",
        "created_date": "2026-06-15",
        "assigned_to": "Product Team",
        "tags": ["ux", "onboarding", "product"],
        "description": "Redesign the new user onboarding flow to reduce drop-off. A/B test with 3 variants.",
    },
    "REC-004": {
        "title": "Database read replica lag monitoring",
        "status": "open",
        "priority": "medium",
        "created_date": "2026-08-12",
        "assigned_to": "SRE Team",
        "tags": ["database", "monitoring", "sre", "infrastructure"],
        "description": "Set up alerting for read replica lag exceeding 5 seconds. Add Grafana dashboard for replica health.",
    },
}

KNOWLEDGE_BASE = [
    {
        "id": "KB-001",
        "title": "Setting up CI/CD pipelines with GitHub Actions",
        "summary": "Step-by-step guide for configuring build, test, and deploy pipelines using GitHub Actions. Covers caching, matrix builds, and secret management.",
        "tags": ["ci", "cd", "github", "automation", "pipeline"],
    },
    {
        "id": "KB-002",
        "title": "Kubernetes resource limits best practices",
        "summary": "How to set CPU and memory requests/limits for production workloads. Includes guidance on QoS classes, OOM behavior, and right-sizing.",
        "tags": ["kubernetes", "resources", "infrastructure", "sre", "deployment"],
    },
    {
        "id": "KB-003",
        "title": "API versioning strategies",
        "summary": "Comparison of URL-path, header, and query-param versioning. Pros, cons, and migration patterns for each approach.",
        "tags": ["api", "versioning", "design", "migration"],
    },
    {
        "id": "KB-004",
        "title": "Incident response runbook template",
        "summary": "Template for creating incident response runbooks. Covers detection, classification, communication, remediation, and post-mortem steps.",
        "tags": ["incident", "runbook", "sre", "operations", "security"],
    },
    {
        "id": "KB-005",
        "title": "Database migration safety checklist",
        "summary": "Pre-flight checklist for running database migrations in production. Covers backups, rollback plans, lock analysis, and staged rollout.",
        "tags": ["database", "migration", "safety", "checklist", "deployment"],
    },
    {
        "id": "KB-006",
        "title": "Monitoring and alerting with Prometheus and Grafana",
        "summary": "Guide to setting up Prometheus metrics collection, writing PromQL queries, and building Grafana dashboards for service observability.",
        "tags": ["monitoring", "prometheus", "grafana", "sre", "observability"],
    },
]

CREATED_TASKS: list = []


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _lookup_record(arguments: dict) -> dict:
    record_id = arguments.get("record_id", "").upper()
    record = RECORDS.get(record_id)
    if not record:
        return {
            "error": f"Record {record_id} not found",
            "available_ids": list(RECORDS.keys()),
        }
    return {"record_id": record_id, **record}


def _search_knowledge_base(arguments: dict) -> dict:
    query = arguments.get("query", "").lower()
    if not query:
        return {"error": "Query cannot be empty", "results": []}

    keywords = query.split()
    matches = []
    for article in KNOWLEDGE_BASE:
        title_lower = article["title"].lower()
        tags_lower = [t.lower() for t in article["tags"]]
        score = sum(
            1
            for kw in keywords
            if kw in title_lower or any(kw in tag for tag in tags_lower)
        )
        if score > 0:
            matches.append({**article, "_relevance": score})

    matches.sort(key=lambda a: a["_relevance"], reverse=True)
    for m in matches:
        del m["_relevance"]

    return {
        "query": query,
        "results_found": len(matches),
        "results": matches,
    }


def _create_task(arguments: dict) -> dict:
    title = arguments.get("title", "")
    if not title:
        return {"error": "Title is required"}

    task_id = f"TASK-{uuid.uuid4().hex[:6].upper()}"
    task = {
        "task_id": task_id,
        "title": title,
        "description": arguments.get("description", ""),
        "priority": arguments.get("priority", "medium"),
        "assignee": arguments.get("assignee", "Unassigned"),
        "status": "open",
    }
    CREATED_TASKS.append(task)
    return {"created": True, **task}


TOOL_HANDLERS = {
    "lookup_record": _lookup_record,
    "search_knowledge_base": _search_knowledge_base,
    "create_task": _create_task,
}


# ---------------------------------------------------------------------------
# MCP JSON-RPC endpoint
# ---------------------------------------------------------------------------


class McpRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str
    params: Optional[dict] = None


app = FastAPI(
    title="MCP Tool Server",
    description="Domain-agnostic tools for multi-agent workflows (MCP protocol).",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "tools_available": len(TOOLS),
        "tool_names": [t["name"] for t in TOOLS],
    }


@app.post("/mcp")
async def mcp_endpoint(request: McpRequest):
    """Handle MCP JSON-RPC requests (tools/list and tools/call)."""
    if request.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {"tools": TOOLS},
        }

    if request.method == "tools/call":
        params = request.params or {}
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            })

        logger.info("MCP tools/call [%s] args=%s", tool_name, arguments)
        result = handler(arguments)

        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {
                "content": [{"type": "text", "text": str(result)}],
                "isError": False,
            },
        }

    return JSONResponse(content={
        "jsonrpc": "2.0",
        "id": request.id,
        "error": {"code": -32601, "message": f"Method not found: {request.method}"},
    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT)
