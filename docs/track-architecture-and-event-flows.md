# Compare the three quickstart tracks

The three tracks teach the same agent workflow at increasing levels of platform integration. Track 1 proves the application pattern locally. Track 2 runs that pattern on Red Hat OpenShift AI. Track 3 maps the pattern to the open cloud-native agent blueprint and identifies optional advanced integrations; it is not an end-to-end validated deployment.

## Track 1: Local learning architecture

```mermaid
flowchart LR
    U[User or Gradio UI]

    subgraph Host[Local Intel CPU host]
        O[FastAPI orchestrator]
        R[Research agent]
        A[Analyst agent]
        E[Executor agent]
        M[MCP tool server]
        G[Guardrails service]
        S[llm-d-sc optional<br/>or LLM classifier fallback]
        L[Ollama learning backend<br/>or demo responses]
    end

    U -->|HTTP workflow request| O
    O -->|classify| S
    O -->|A2A JSON-RPC| R
    O -->|A2A JSON-RPC| A
    O -->|A2A JSON-RPC| E
    R & A & E -->|screen input and output| G
    R & A & E -->|MCP tools/call| M
    R & A & E -->|OpenAI-compatible chat| L
```

### Track 1 request event flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant O as Orchestrator
    participant C as Classifier
    participant R as Research
    participant A as Analyst
    participant E as Executor
    participant G as Guardrails
    participant M as MCP tools
    participant L as Local model or demo

    User->>O: POST /api/v1/workflow
    O->>C: Classify query when workflow_type=auto
    C-->>O: lightweight, standard, or comprehensive
    opt Research selected
        O->>R: A2A tasks/send
        R->>G: Screen input
        opt Query requires data or an action
            R->>M: tools/call
            M-->>R: Tool result
        end
        R->>L: Chat completion
        L-->>R: Generated response
        R->>G: Screen output
        R-->>O: Completed task and latency
    end
    opt Analyst selected
        O->>A: A2A tasks/send with accumulated context
        A->>G: Screen input
        A->>L: Chat completion
        L-->>A: Analysis
        A->>G: Screen output
        A-->>O: Completed task and latency
    end
    O->>E: A2A tasks/send with accumulated context
    E->>G: Screen input
    opt Query requires a tool
        E->>M: tools/call
        M-->>E: Tool result
    end
    E->>L: Chat completion
    L-->>E: Final recommendation or action report
    E->>G: Screen output
    E-->>O: Completed task and latency
    O-->>User: Steps, metrics, classification, and AI disclaimer
```

## Track 2: OpenShift AI architecture

```mermaid
flowchart LR
    U[User]

    subgraph OCP[Red Hat OpenShift 4.22]
        RT[OpenShift Route and Service]

        subgraph App[Quickstart namespace]
            O[Orchestrator pod]
            R[Research agent pod]
            A[Analyst agent pod]
            E[Executor agent pod]
            M[MCP server pod]
            G[Guardrails pod]
            S[Optional llm-d-sc pod]
            SEC[Kubernetes Secret<br/>A2A bearer token]
        end

        subgraph RHOAI[Red Hat OpenShift AI 3.latest]
            K[KServe InferenceService]
            V[Red Hat AI Inference Server<br/>vLLM CPU]
            MODEL[Granite instruction model]
        end

        OT[OTLP collector<br/>optional]
    end

    U -->|TLS| RT --> O
    O -->|classify| S
    O -->|authenticated A2A| R & A & E
    SEC -.->|token injection| O & R & A & E
    R & A & E --> G
    R & A & E --> M
    R & A & E -->|OpenAI-compatible API| K --> V --> MODEL
    O & R & A & E -.->|OpenTelemetry spans| OT
```

### Track 2 deployment and request event flow

```mermaid
sequenceDiagram
    autonumber
    actor Operator
    actor User
    participant H as Helm and OpenShift
    participant K as KServe
    participant V as Red Hat AI Inference Server
    participant Agents as Agent pods
    participant O as Orchestrator pod
    participant M as MCP and guardrails

    Operator->>H: Install chart and configuration
    H->>K: Create or connect InferenceService
    K->>V: Start model server and load model
    V-->>K: Model ready
    H->>Agents: Start agents with model, MCP, guardrail, and auth settings
    Agents-->>H: Health probes pass
    H->>O: Start orchestrator
    loop Until every configured agent is registered
        O->>Agents: GET agent-card.json
        Agents-->>O: Name, URL, and skills
    end
    O-->>H: /ready returns 200
    User->>O: Workflow request through OpenShift Route
    O->>O: Select workflow depth
    loop Selected agents in sequence
        O->>Agents: Authenticated A2A tasks/send
        Agents->>M: Screen input and call relevant tools
        Agents->>V: Chat completion
        V-->>Agents: Granite response
        Agents->>M: Screen output
        Agents-->>O: Result and measured latency
    end
    O-->>User: Structured workflow response
```

## Track 3: Advanced blueprint mapping

Track 3 is a target architecture and exploration path. Solid connections below are represented by the current quickstart or its example manifests. Dashed connections are advanced blueprint integrations that require additional platform components and validation.

```mermaid
flowchart LR
    U[User or calling service]

    subgraph Control[Control and identity plane]
        GIT[GitOps or Helm]
        LIFE[Kagenti lifecycle<br/>example manifests]
        ID[SPIFFE and SPIRE identity<br/>optional target]
        AS[agent-sandbox or OpenShell<br/>optional target]
    end

    subgraph AgentPod[Agent workload]
        SUP[Sandbox supervisor<br/>optional target]
        H[Agent harness]
        A2A[A2A AgentCard and transport]
    end

    subgraph Governance[Governed services]
        MG[MCP Gateway<br/>optional target]
        SK[Skill backends]
        TG[TrustyAI guardrails<br/>optional target]
    end

    subgraph Inference[Inference plane]
        GW[AI or MaaS gateway<br/>optional target]
        SR[Semantic router]
        EPP[llm-d Router or EPP<br/>optional target]
        V[vLLM workers]
    end

    OBS[OpenTelemetry and MLflow<br/>MLflow optional target]

    U --> H
    GIT --> LIFE --> H
    H --> A2A
    H --> SR --> V
    H --> SK
    H --> TG
    H --> OBS
    ID -.->|short-lived workload identity| SUP
    AS -.->|policy and isolation| SUP -.-> H
    H -.->|claims-bearing MCP request| MG -.-> SK
    H -.-> GW -.-> SR -.-> EPP -.-> V
    MG -.-> OBS
    GW -.-> OBS
```

### Track 3 governed event flow

```mermaid
sequenceDiagram
    autonumber
    actor Platform as Platform team
    actor Caller
    participant Control as GitOps and lifecycle control
    participant Identity as SPIFFE/SPIRE identity
    participant Sandbox as Agent sandbox
    participant Agent as Agent harness
    participant Gateway as MCP Gateway
    participant Guard as TrustyAI guardrails
    participant Router as Semantic and llm-d routing
    participant Model as vLLM worker
    participant Audit as OTel and MLflow

    Platform->>Control: Declare agent, policy, tools, and model access
    Control->>Sandbox: Reconcile one governed agent workload
    Identity-->>Sandbox: Issue short-lived workload identity
    Caller->>Agent: Submit goal
    Agent->>Guard: Screen input
    Guard-->>Agent: Allow, redact, or block
    Agent->>Router: Governed inference request
    Router->>Router: Select model and serving replica
    Router->>Model: OpenAI-compatible request
    Model-->>Agent: Generated plan or tool intent
    Agent->>Gateway: MCP call with identity claims
    Gateway->>Gateway: Authorize tool by claims
    Gateway-->>Agent: Governed tool result
    Agent->>Guard: Screen final output
    Agent-->>Caller: Result
    Agent-->>Audit: Workflow and tool spans
    Gateway-->>Audit: Authorization decision
    Router-->>Audit: Routing and inference metrics
```

## What changes between tracks

| Concern | Track 1 | Track 2 | Track 3 |
|---|---|---|---|
| Purpose | Learn and inspect the agent pattern | Run and validate it on OpenShift AI | Explore the full blueprint and governance boundaries |
| Runtime | Local processes or Compose | Pods, Services, Route, Helm, and KServe | Agent lifecycle and sandbox control planes |
| Inference | Ollama or simulated responses | Red Hat AI Inference Server or MaaS | Governed gateway, semantic routing, llm-d, and vLLM workers |
| Identity | Optional shared bearer token | Kubernetes Secret-backed bearer token | Short-lived SPIFFE/SPIRE workload identity target |
| Tools | Direct MCP calls | Direct in-cluster MCP calls | Claims-authorized MCP Gateway target |
| Isolation | Local process boundary | Hardened pod SecurityContext | OpenShell or agent-sandbox and optional Kata target |
| Evidence level | Automated local and demo validation | Live sequential Intel CPU validation | Architecture mapping; not end-to-end validated |
