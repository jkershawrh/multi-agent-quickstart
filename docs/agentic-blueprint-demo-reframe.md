# Reframing the Multi-Agent QuickStart with Red Hat's Agentic AI Blueprint

## Purpose

This presentation uses Red Hat's July 20, 2026 article, [Architect an open blueprint for cloud-native AI agents](https://developers.redhat.com/articles/2026/07/20/architect-open-blueprint-cloud-native-ai-agents), as the architectural frame for the existing Multi-Agent QuickStart.

The QuickStart is a runnable subset of the blueprint, not an implementation of every component in the target architecture. The presentation must distinguish live proof from configurable integrations and future blueprint controls.

Intel remains a first-class part of the story: Red Hat provides the workload, control, integration, and governance foundation; Intel Xeon provides the CPU compute foundation for the inference path. The model may generate and explain, but it receives no evidence or action authority.

## Reframing process

### 1. Start from the blueprint thesis

The source article reframes an agent as a new cloud-native workload class. A production agent is more than a model endpoint: its model, harness, sandbox, tools, identity, inference routing, observability, and policy have distinct lifecycles and trust boundaries.

### 2. Discover what the repository actually implements

Repository contracts, runtime code, deployment manifests, tests, and live endpoints were inspected before writing the story. The resulting `demo-blueprint.yaml` records verified components, flows, evidence, decisions, and discrepancies.

### 3. Map the implementation to blueprint boundaries

| Blueprint boundary | QuickStart evidence | Presentation status |
|---|---|---|
| Control band and lifecycle | Helm/OpenShift configuration and deployment objects | Implemented now |
| Agent harness and specialists | Orchestrator plus authenticated A2A research, analyst, and executor roles | Implemented now |
| Tool governance checkpoint | MCP tools, role allow-lists, versioned policy, and approval gate | Implemented now |
| Inference plane | Semantic routing and OpenAI-compatible inference on Intel Xeon CPU | Implemented now / environment dependent |
| Audit and human authority | Proof-pack records and incident-commander approval | Implemented now |
| External guardrails and telemetry export | Configuration and fail-closed behavior | Configurable / optional |
| Sandbox control plane and agent-sandbox API | Architectural extension point | Blueprint target |
| SPIFFE workload identity | Architectural extension point | Blueprint target |
| Claims-based MCP Gateway | Direct MCP and policy are present; claims authorization is an extension | Blueprint target |
| llm-d replica routing | Semantic selection is present; replica-level routing is an extension | Blueprint target |

### 4. Turn the map into a seven-scene story

1. **Thesis:** An agent is not a model endpoint.
2. **Reframe:** Move from a bundled model demo to separated workload boundaries.
3. **Guided architecture:** Reveal control, workload, tool, inference, and foundation bands one question at a time.
4. **Live proof:** Run the implemented slice and expose discovery, routing, A2A work, MCP evidence, Intel Xeon inference, policy, latency, and human authority.
5. **Fit and gap:** Separate implemented, configurable, and blueprint-target capabilities.
6. **Open interfaces:** Explain how A2A, MCP, OpenAI-compatible inference, OpenShift, and Intel Xeon keep the system composable.
7. **Close:** State what the session proved, then hand off to the lab as the next journey.

### 5. Preserve honest live proof

The presentation reads current data from the agent registry, health, workflow, and policy endpoints. A successful call is labeled `LIVE`. Checked-in fallback data is labeled `REHEARSAL` or `OFFLINE` and must never be described as live infrastructure evidence.

### 6. Keep authority separate from inference

The model can classify, generate role-specific artifacts, and explain a proposed outcome. MCP supplies named evidence and bounded tools. Deterministic policy decides whether an action requires approval. The incident commander owns the final decision.

### 7. Close before the lab

The presentation ends after the evidence-based payoff. The hands-on lab is a separate next journey in which the learner changes one role, tool boundary, routing choice, or approval policy and then verifies the resulting proof artifact.

## Non-claims

- The QuickStart does not claim that the complete Red Hat blueprint is deployed.
- Kagenti, AgentRuntime, OpenShell, the agent-sandbox API, SPIFFE/SPIRE, a claims-based MCP Gateway, and llm-d replica routing are not presented as active unless the environment proves them.
- A configured model name does not prove the physical CPU. Live hardware labeling requires environment evidence; otherwise the presentation describes Intel Xeon as the intended CPU inference foundation.
- LLM output is not evidence, policy, approval, or authority.
