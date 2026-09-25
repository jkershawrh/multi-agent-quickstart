import type { DemoConfig } from './types'

const technicalTopology = {
  boundary: { label: 'OpenShift namespace', detail: 'multi-agent runtime and policy boundary' },
  entry: { id: 'operator', kind: 'human', label: 'Participant', detail: 'submits goal and owns final authority', endpoint: 'browser' },
  primaryPath: [
    { id: 'route', kind: 'route', label: 'Route + Service', detail: 'TLS entry to orchestrator', endpoint: '443 → :8000', edgeLabel: 'HTTPS' },
    { id: 'orchestrator', kind: 'deployment', label: 'Orchestrator', detail: 'discovery, routing, context, policy', endpoint: 'POST /api/v1/workflow', edgeLabel: 'HTTP' },
    { id: 'router', kind: 'service', label: 'Semantic router', detail: 'workflow depth + model tier', endpoint: 'gRPC :50051', edgeLabel: 'classify' },
    { id: 'agents', kind: 'deployments', label: 'A2A agent chain', detail: 'research → analyst → executor', endpoint: 'JSON-RPC tasks/send', edgeLabel: 'A2A + auth' },
  ],
  supportPath: [
    { id: 'guardrails', kind: 'service', label: 'Guardrails', detail: 'screen input and output', endpoint: ':8005', edgeLabel: 'screen' },
    { id: 'mcp', kind: 'service', label: 'MCP tools', detail: 'lookup, search, create_task', endpoint: ':8004/mcp', edgeLabel: 'tools/call' },
    { id: 'policy', kind: 'policy', label: 'Workflow policy', detail: 'allow-list + approval rule', endpoint: 'versioned YAML', edgeLabel: 'evaluate' },
    { id: 'human', kind: 'authority', label: 'Human review', detail: 'approve or deny remediation', endpoint: '/api/v1/approvals', edgeLabel: 'pause' },
  ],
  optionalPath: { id: 'model', kind: 'inference', label: 'Intel CPU model', detail: 'role-specific generation only', endpoint: 'OpenAI-compatible API', edgeLabel: 'bounded prompt' },
}

export const demoConfig: DemoConfig = {
  id: 'multi-agent-story', title: 'Three agents. One governed decision.', subtitle: 'Open cooperation with human authority', event: 'Build Multi-Agent AI Systems', audience: 'AI engineers, solution architects, and platform engineers', cta: 'Follow the evidence from request to human authority.',
  brand: { primary: { name: 'Red Hat', logo: '/logos/redhat.svg', alt: 'Red Hat' }, partner: { name: 'Intel', logo: '/logos/intel.png', alt: 'Intel' }, attribution: 'Red Hat × Intel' },
  acts: [
    { id: 'stakes', label: '00', title: 'The Risk', scenes: [
      { id: 'intro', type: 'intro', beat: 'ordinary-world', title: 'Three agents. One governed decision.', subtitle: 'The hard part is not cooperation. It is knowing who saw what—and who may act.', speakerPrompt: 'Open on the governance problem. Do not introduce component names yet.' },
      { id: 'reframe', type: 'reframe', beat: 'stakes', eyebrow: 'The reframe', title: 'More agents do not create more trust', before: 'One opaque answer assembled by many models', after: 'One inspectable evidence path with human authority', detail: 'Routing, accumulated context, tools, model output, policy, and approval remain separately visible.', speakerPrompt: 'State the audience decision: is this an inspectable foundation for their own domain workflow?' },
    ] },
    { id: 'architecture', label: '01', title: 'Guided Architecture', scenes: [
      { id: 'guided-architecture', type: 'guided-architecture', beat: 'system-reveal', eyebrow: 'Guided system boundaries', title: 'Earn each handoff before the workflow runs', body: 'Every reveal answers one operational question.', layers: [
        { id: 'entry', component: 'Request boundary', tone: 'primary', question: 'What enters the system—and where?', answer: 'A bounded workflow request enters through an OpenShift Route and Service.', detail: 'The participant supplies the goal. The platform owns TLS, placement, health, and the namespace boundary.', activeNodeIds: ['operator', 'route'] },
        { id: 'selection', component: 'Workflow selection', tone: 'partner', question: 'Who decides how much work this request needs?', answer: 'The orchestrator asks the semantic router for workflow depth and model tier.', detail: 'Routing chooses workflow depth. It does not grant tool or action authority.', activeNodeIds: ['orchestrator', 'router'] },
        { id: 'delegation', component: 'A2A cooperation', tone: 'partner', question: 'How do specialists cooperate without becoming one hidden agent?', answer: 'The orchestrator delegates authenticated A2A tasks and carries explicit context forward.', detail: 'Research investigates, analyst interprets, and executor prepares the bounded outcome. Each step returns its own result and latency.', activeNodeIds: ['agents', 'model'] },
        { id: 'evidence', component: 'Evidence boundary', tone: 'success', question: 'What evidence may each agent use?', answer: 'Guardrails screen content while policy-scoped MCP tools provide records, knowledge, or a proposed task.', detail: 'Model output remains distinct from MCP evidence. Unavailable configured guardrails fail closed.', activeNodeIds: ['guardrails', 'mcp', 'policy'] },
        { id: 'authority', component: 'Human authority', tone: 'primary', question: 'Can the executor turn its recommendation into an action?', answer: 'Not when the versioned policy requires approval.', detail: 'create_task pauses. The incident commander approves or denies one action; restart never implies consent.', activeNodeIds: ['human'] },
      ], technicalTopology, speakerPrompt: 'Ask the question first. Reveal the runtime object, protocol, and authority limit only after the room has reasoned about it.' },
    ] },
    { id: 'proof', label: '02', title: 'Live Agent Journey', scenes: [
      { id: 'live', type: 'live-journey', beat: 'live-proof', eyebrow: 'Live infrastructure', title: 'Watch one goal become governed evidence', body: 'Run a small workflow, change its depth, then inspect the policy boundary.', cta: 'Discover live agents', intake: { label: 'INCIDENT GOAL', title: 'Investigate INC-1042 and prepare—but do not execute—a remediation.', detail: 'We will observe discovery, workflow selection, A2A participation, model tier, MCP evidence, latency, policy, and final authority.' }, nodes: [
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
      { id: 'comparison', type: 'comparison', beat: 'trials', eyebrow: 'Changed condition', title: 'The policy changes authority—not the number of agents', columns: [
        { label: 'Certified baseline', value: 'Workflow completes', detail: 'The same three advertised roles cooperate under the baseline tool behavior.', tone: 'partner' },
        { label: 'Governed incident policy', value: 'Action pauses', detail: 'create_task requires an explicit incident-commander decision.', tone: 'success' },
        { label: 'Failure boundary', value: 'Consent is never inferred', detail: 'Invalid policy fails readiness; restart discards pending approval state.', tone: 'danger' },
      ], speakerPrompt: 'The comparison is an authority change. Do not claim a performance winner or invent a latency result.' },
    ] },
    { id: 'mechanisms', label: '03', title: 'Why It Works', scenes: [
      { id: 'mechanisms', type: 'mechanisms', beat: 'trials', eyebrow: 'Mechanism, not magic', title: 'Three contracts keep the journey reviewable', mechanisms: [
        { id: 'a2a', label: 'A2A contract', claim: 'Roles advertise capabilities and return explicit task artifacts.', detail: 'Discovery and JSON-RPC delegation keep each specialist visible.', tone: 'partner' },
        { id: 'mcp', label: 'MCP contract', claim: 'Evidence retrieval and actions use named tools.', detail: 'Agent-specific allow-lists keep generated reasoning separate from tool authority.', tone: 'success' },
        { id: 'policy', label: 'Human policy contract', claim: 'A versioned rule—not an LLM—owns remediation.', detail: 'The proof pack preserves routing, steps, guardrails, policy, and approval evidence.', tone: 'primary' },
      ], speakerPrompt: 'Connect each mechanism to evidence the audience just saw. The reviewer is a human role, not a fourth agent.' },
    ] },
    { id: 'payoff', label: '04', title: 'Close', scenes: [
      { id: 'payoff', type: 'evidence-payoff', beat: 'transformation', eyebrow: 'What this session proved', title: 'Cooperation stayed open. Authority stayed human.', adapterIds: ['agent-registry', 'workflow-lightweight', 'workflow-comprehensive', 'workflow-policy'], fallbackLine: 'Run the live agent journey to build the proof', evidenceFields: [{ key: 'policy', label: 'Active policy' }, { key: 'approvalTool', label: 'Bounded action' }, { key: 'reviewer', label: 'Decision owner' }, { key: 'authority', label: 'Model authority' }], line1: 'The agents generated and accumulated context.', line2: 'The human still owned the action.', cta: 'Close the presentation. The hands-on lab is the next journey.', speakerPrompt: 'Close the presentation before mentioning the lab. Recap only current-session evidence.' },
    ] },
  ],
  journeyHandoffs: [
    { depth: 'lab', title: 'Build Multi-Agent AI Systems lab', duration: '60–90 minutes', question: 'Can the learner customize a role, tool policy, and approval boundary?', technology: 'OpenShift · A2A · MCP · semantic routing · human approval', instruction: 'After closing the presentation, open the Launchpad lab and continue with the same architecture and authority model.' },
  ],
}
