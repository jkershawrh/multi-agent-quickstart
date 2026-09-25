import type { DemoConfig } from './types'

const technicalTopology = {
  boundary: { label: 'OpenShift agent workload', detail: 'implemented slice of the Red Hat agentic AI blueprint' },
  entry: { id: 'operator', kind: 'human', label: 'Participant + GitOps', detail: 'declares intent; platform deploys the workload', endpoint: 'browser / Helm' },
  primaryPath: [
    { id: 'route', kind: 'route', label: 'Workload entry', detail: 'OpenShift Route + Service', endpoint: '443 → :8000', edgeLabel: 'HTTPS' },
    { id: 'orchestrator', kind: 'deployment', label: 'Agent harness', detail: 'discovery, delegation, context', endpoint: 'POST /api/v1/workflow', edgeLabel: 'Open API' },
    { id: 'agents', kind: 'deployments', label: 'A2A specialists', detail: 'research → analyst → executor', endpoint: 'JSON-RPC tasks/send', edgeLabel: 'A2A + auth' },
    { id: 'router', kind: 'service', label: 'Inference routing', detail: 'workflow depth + model tier', endpoint: 'semantic router → vLLM', edgeLabel: 'OpenAI API' },
    { id: 'model', kind: 'inference', label: 'Intel Xeon CPU inference', detail: 'role-specific generation only', endpoint: 'OpenAI-compatible model', edgeLabel: 'bounded prompt' },
  ],
  supportPath: [
    { id: 'guardrails', kind: 'service', label: 'Safety controls', detail: 'screen input and output', endpoint: ':8005', edgeLabel: 'guard' },
    { id: 'mcp', kind: 'service', label: 'MCP checkpoint', detail: 'named tools + scoped evidence', endpoint: ':8004/mcp', edgeLabel: 'tools/call' },
    { id: 'policy', kind: 'policy', label: 'Policy + audit', detail: 'allow-list, proof pack, approval rule', endpoint: 'versioned YAML', edgeLabel: 'evaluate' },
    { id: 'human', kind: 'authority', label: 'Human authority', detail: 'approve or deny remediation', endpoint: '/api/v1/approvals', edgeLabel: 'pause' },
  ],
  optionalPath: { id: 'target-controls', kind: 'target', label: 'Blueprint target controls', detail: 'sandbox API · SPIFFE · claims gateway · llm-d', endpoint: 'not claimed as deployed', edgeLabel: 'extend' },
}

export const demoConfig: DemoConfig = {
  id: 'multi-agent-story', title: 'From agents to an open cloud-native blueprint', subtitle: 'Red Hat control and openness · Intel Xeon inference foundation', event: 'Build Multi-Agent AI Systems', audience: 'AI engineers, solution architects, and platform engineers', cta: 'Map the blueprint, then prove the implemented path.',
  brand: { primary: { name: 'Red Hat', logo: '/logos/redhat.svg', alt: 'Red Hat' }, partner: { name: 'Intel', logo: '/logos/intel.png', alt: 'Intel' }, attribution: 'Red Hat × Intel' },
  acts: [
    { id: 'stakes', label: '00', title: 'The Risk', scenes: [
      { id: 'intro', type: 'intro', beat: 'ordinary-world', title: 'An agent is not a model endpoint', subtitle: 'Red Hat turns it into a governed cloud-native workload. Intel Xeon gives its inference plane a deployable CPU foundation.', citation: { label: 'Red Hat: Architect an open blueprint for cloud-native AI agents · July 20, 2026', url: 'https://developers.redhat.com/articles/2026/07/20/architect-open-blueprint-cloud-native-ai-agents' }, speakerPrompt: 'Open with the article’s thesis, then name the partnership: Red Hat governs the workload; Intel Xeon runs the bounded inference path.' },
      { id: 'reframe', type: 'reframe', beat: 'stakes', eyebrow: 'The blueprint reframe', title: 'Move from a model demo to a governed workload', before: 'Model + prompt + tools bundled into one opaque process', after: 'Separate control, agent, tool, inference, identity, and audit boundaries', detail: 'The QuickStart implements a runnable slice. The full Red Hat blueprint supplies the target architecture and extension path.', speakerPrompt: 'Name the shift in system boundaries before introducing any product or protocol.' },
    ] },
    { id: 'architecture', label: '01', title: 'Guided Architecture', scenes: [
      { id: 'guided-architecture', type: 'guided-architecture', beat: 'system-reveal', eyebrow: 'Red Hat agentic AI blueprint', title: 'Separate the workload before connecting the flow', body: 'Each boundary shows what runs now and what the blueprint adds next.', citation: { label: 'Source architecture: Red Hat open blueprint for cloud-native AI agents', url: 'https://developers.redhat.com/articles/2026/07/20/architect-open-blueprint-cloud-native-ai-agents' }, layers: [
        { id: 'control', component: '1 · Control band', tone: 'primary', question: 'How is an agent declared, deployed, and reconciled?', answer: 'Implemented now: Helm and GitOps create an OpenShift workload with explicit configuration.', detail: 'Blueprint target: an agent blueprint drives a sandbox control plane and Sandbox resource. Kagenti and AgentRuntime are examples—not claimed as active here.', activeNodeIds: ['operator', 'route'] },
        { id: 'workload', component: '2 · Agent workload', tone: 'partner', question: 'What runs separately from the model?', answer: 'Implemented now: an orchestrator harness discovers and delegates to authenticated A2A specialists.', detail: 'Blueprint target: each workload receives an isolated sandbox, supervisor, and workload identity independent of the model lifecycle.', activeNodeIds: ['orchestrator', 'agents'] },
        { id: 'checkpoint', component: '3 · Tool checkpoint', tone: 'success', question: 'Who decides which evidence and actions an agent may use?', answer: 'Implemented now: named MCP tools, role allow-lists, versioned policy, and approval gates.', detail: 'Blueprint target: an MCP Gateway authorizes from workload-identity claims—never from model output or prompt text.', activeNodeIds: ['guardrails', 'mcp', 'policy'] },
        { id: 'inference', component: '4 · Inference plane', tone: 'partner', question: 'How is generation routed without granting authority?', answer: 'Implemented now: semantic routing selects workflow depth and an OpenAI-compatible model running on Intel Xeon CPU.', detail: 'Intel supplies the CPU inference foundation; the model generates bounded artifacts but receives no evidence or action authority. Blueprint target: llm-d adds independent replica routing.', activeNodeIds: ['router', 'model'] },
        { id: 'foundation', component: '5 · Foundation + audit', tone: 'primary', question: 'What makes every hop reviewable?', answer: 'Implemented now: OpenShift isolation, Intel Xeon compute, guardrails, proof packs, and explicit human approval.', detail: 'Blueprint target: SPIFFE identity and end-to-end tracing connect control, tools, inference, and silicon while preserving human authority.', activeNodeIds: ['model', 'policy', 'human'] },
      ], technicalTopology, speakerPrompt: 'For every band, say “implemented now” or “blueprint target.” Never imply the target controls are already deployed.' },
    ] },
    { id: 'proof', label: '02', title: 'Live Agent Journey', scenes: [
      { id: 'live', type: 'live-journey', beat: 'live-proof', eyebrow: 'Implemented blueprint slice · live', title: 'Run the workload across the mapped boundaries', body: 'The live path proves the controls present in this QuickStart—not every target capability in the blueprint.', cta: 'Discover live agents', intake: { label: 'INCIDENT GOAL', title: 'Investigate INC-1042 and prepare—but do not execute—a remediation.', detail: 'Observe discovery, routing, A2A delegation, model tier, MCP evidence, policy, latency, and final human authority.' }, nodes: [
        { id: 'discover', label: 'Discover', detail: 'AgentCards + readiness', tone: 'primary' },
        { id: 'route', label: 'Route', detail: 'workflow + model tier', tone: 'partner' },
        { id: 'delegate', label: 'Delegate', detail: 'A2A context chain', tone: 'partner' },
        { id: 'govern', label: 'Govern', detail: 'tools + approval', tone: 'success' },
        { id: 'review', label: 'Review', detail: 'human authority', tone: 'primary' },
      ], technicalTopology, steps: [
        { id: 'discover', title: 'Discover capable agents', detail: 'Read live AgentCards before assuming which specialists are available.', adapterId: 'agent-registry', activeNode: 0, activeNodeIds: ['operator', 'route', 'orchestrator', 'agents'], resultFields: [{ key: 'agentCount', label: 'Agents discovered' }, { key: 'agents', label: 'Advertised roles' }, { key: 'routing', label: 'Semantic routing' }] },
        { id: 'lightweight', title: 'Run a lightweight request', detail: 'A small request selects the shortest workflow and exposes its model and measured step.', adapterId: 'workflow-lightweight', activeNode: 2, activeNodeIds: ['operator', 'route', 'orchestrator', 'router', 'agents', 'guardrails', 'model'], resultFields: [{ key: 'workflow', label: 'Workflow' }, { key: 'agents', label: 'Participating agents' }, { key: 'model', label: 'Model tier' }, { key: 'latency', label: 'End-to-end', suffix: 'ms' }] },
        { id: 'comprehensive', title: 'Change the workflow depth', detail: 'The same platform now accumulates research, analysis, MCP evidence, and executor context.', adapterId: 'workflow-comprehensive', activeNode: 3, activeNodeIds: ['operator', 'route', 'orchestrator', 'router', 'agents', 'guardrails', 'mcp', 'model', 'policy'], resultFields: [{ key: 'status', label: 'Status' }, { key: 'agents', label: 'A2A sequence' }, { key: 'evidence', label: 'Evidence path' }, { key: 'latency', label: 'End-to-end', suffix: 'ms' }] },
        { id: 'policy', title: 'Inspect the authority boundary', detail: 'The final state comes from versioned policy and human review—not model confidence.', adapterId: 'workflow-policy', activeNode: 4, activeNodeIds: ['orchestrator', 'agents', 'mcp', 'policy', 'human'], resultFields: [{ key: 'policy', label: 'Policy' }, { key: 'approvalTool', label: 'Approval-gated action' }, { key: 'reviewer', label: 'Decision owner' }, { key: 'authority', label: 'LLM authority' }] },
      ], speakerPrompt: 'Name the source state before interpretation. Point out exactly where model generation ends and deterministic authority begins.' },
      { id: 'comparison', type: 'comparison', beat: 'trials', eyebrow: 'Blueprint fit and gap', title: 'A runnable slice with an explicit extension path', columns: [
        { label: 'Implemented now', value: 'Runnable and observable', detail: 'OpenShift workload, A2A delegation, semantic routing, Intel Xeon CPU inference, MCP tools, versioned policy, proof pack, and human approval.', tone: 'success' },
        { label: 'Configurable / optional', value: 'Environment dependent', detail: 'External guardrails, model endpoints, OpenTelemetry export, and deployment-specific routing are verified when configured.', tone: 'partner' },
        { label: 'Blueprint target', value: 'Not claimed as deployed', detail: 'Sandbox API, SPIFFE identity, claims-based MCP Gateway, llm-d replica routing, and full lifecycle control plane.', tone: 'danger' },
      ], speakerPrompt: 'Make maturity visible. The value is the mapping, not pretending the pilot already contains every blueprint component.' },
    ] },
    { id: 'mechanisms', label: '03', title: 'Why It Works', scenes: [
      { id: 'mechanisms', type: 'mechanisms', beat: 'trials', eyebrow: 'Open interfaces', title: 'The blueprint stays replaceable at every boundary', mechanisms: [
        { id: 'a2a', label: 'A2A', claim: 'The harness and specialists exchange visible task artifacts.', detail: 'Agent roles can evolve without merging orchestration, models, and authority into one process.', tone: 'partner' },
        { id: 'mcp', label: 'MCP', claim: 'Evidence retrieval and actions remain named, policy-scoped tools.', detail: 'The target gateway can later authorize those tools from workload identity claims.', tone: 'success' },
        { id: 'platform', label: 'Red Hat × Intel foundation', claim: 'OpenAI-compatible inference runs on Intel Xeon inside an OpenShift workload.', detail: 'Red Hat supplies the control and integration plane; Intel supplies the CPU compute foundation. Both remain replaceable through open interfaces.', tone: 'primary' },
      ], speakerPrompt: 'Connect the open interfaces to the live evidence. The blueprint is a composable architecture, not a mandatory monolith.' },
    ] },
    { id: 'payoff', label: '04', title: 'Close', scenes: [
      { id: 'payoff', type: 'evidence-payoff', beat: 'transformation', eyebrow: 'What this session proved', title: 'A blueprint becomes credible when its boundaries become evidence.', adapterIds: ['agent-registry', 'workflow-lightweight', 'workflow-comprehensive', 'workflow-policy'], fallbackLine: 'Run the implemented blueprint slice to build the proof', evidenceFields: [{ key: 'policy', label: 'Active policy' }, { key: 'approvalTool', label: 'Bounded action' }, { key: 'reviewer', label: 'Decision owner' }, { key: 'authority', label: 'Model authority' }], line1: 'Red Hat governed the agent workload while Intel Xeon executed its bounded inference.', line2: 'The fit-gap map shows exactly where the open blueprint extends the system next.', cta: 'Close the presentation. The hands-on lab extends one blueprint boundary.', speakerPrompt: 'Close with both partnership roles, current-session evidence, and honest gaps. Only then position the lab as the next journey.' },
    ] },
  ],
  journeyHandoffs: [
    { depth: 'lab', title: 'Build Multi-Agent AI Systems lab', duration: '60–90 minutes', question: 'Can the learner customize a role, tool policy, and approval boundary?', technology: 'OpenShift · A2A · MCP · semantic routing · human approval', instruction: 'After closing the presentation, open the Launchpad lab and continue with the same architecture and authority model.' },
  ],
}
