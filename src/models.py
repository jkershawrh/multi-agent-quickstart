"""Pydantic models for the multi-agent quickstart.

Defines the Agent-to-Agent protocol data structures for agent discovery,
JSON-RPC task operations, and workflow orchestration.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# A2A Protocol models
# ---------------------------------------------------------------------------


class AgentCapabilities(BaseModel):
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = True


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: Optional[List[str]] = None
    examples: Optional[List[str]] = None


class AgentCard(BaseModel):
    name: str
    description: str
    version: str = "0.1.0"
    url: str = "http://localhost:8001"
    protocolVersion: str = "0.2.6"
    provider: str = "Red Hat / Intel"
    capabilities: AgentCapabilities = AgentCapabilities()
    defaultInputModes: List[str] = ["text"]
    defaultOutputModes: List[str] = ["text"]
    skills: List[AgentSkill] = []


class Part(BaseModel):
    kind: str = "text"
    text: Optional[str] = None


class Message(BaseModel):
    messageId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kind: str = "message"
    role: str = "user"
    parts: List[Part] = []


class TaskStatus(BaseModel):
    state: str = "submitted"
    timestamp: Optional[str] = None


class Artifact(BaseModel):
    artifactId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parts: List[Part] = []


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contextId: Optional[str] = None
    status: TaskStatus = TaskStatus()
    artifacts: Optional[List[Artifact]] = None
    kind: str = "task"


class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    method: str
    params: Optional[dict] = None


class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    result: Optional[Task] = None
    error: Optional[dict] = None


# ---------------------------------------------------------------------------
# Orchestrator models
# ---------------------------------------------------------------------------


class DiscoveredAgent(BaseModel):
    name: str
    url: str
    status: str = "active"
    skills: List[AgentSkill] = []


class ClassificationSignal(BaseModel):
    label: str
    score: float


class ClassificationResult(BaseModel):
    classifier_id: str
    status: str
    signals: List[ClassificationSignal] = []
    selected_workflow: str
    selected_model: str = ""
    latency_ms: float


class WorkflowRequest(BaseModel):
    query: str
    workflow_type: str = "auto"


class WorkflowStep(BaseModel):
    agent: str
    action: str
    result: str
    latency_ms: float
    status: str = "completed"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    model: Optional[str] = None


class WorkflowResponse(BaseModel):
    steps: List[WorkflowStep]
    total_latency_ms: float
    agents_involved: List[str]
    classification: Optional[ClassificationResult] = None
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    ai_disclaimer: str = (
        "Agent responses are AI-generated -- verify "
        "recommendations with qualified professionals."
    )
