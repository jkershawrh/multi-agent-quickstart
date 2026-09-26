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
  id: 'multi-agent-story', title: 'A repeatable blueprint for enterprise AI agents', subtitle: 'From business outcome to governed implementation', event: 'Build Multi-Agent AI Systems', audience: 'Business leaders, architects, AI engineers, and platform teams', cta: 'Define the outcome, build the agent process, and prove it can be governed.',
  brand: { primary: { name: 'Red Hat', logo: '/logos/redhat.svg', alt: 'Red Hat' }, partner: { name: 'Intel', logo: '/logos/intel.png', alt: 'Intel' }, attribution: 'Red Hat × Intel' },
  acts: [
    { id: 'stakes', label: '00', title: 'The Risk', scenes: [
      { id: 'intro', type: 'intro', beat: 'ordinary-world', title: 'Turn an AI idea into a repeatable business process', subtitle: 'Red Hat provides the blueprint for building and governing the process. Intel Xeon provides the CPU foundation for running its AI inference.', citation: { label: 'Based on Red Hat’s open blueprint for cloud-native AI agents · July 20, 2026', url: 'https://developers.redhat.com/articles/2026/07/20/architect-open-blueprint-cloud-native-ai-agents' }, speakerPrompt: 'Start with the business need: move from an interesting AI pilot to a process the organization can own, operate, and improve.' },
      { id: 'reframe', type: 'reframe', beat: 'stakes', eyebrow: 'The business reframe', title: 'An agent is a business process—not just an AI response', before: 'A useful answer with unclear ownership, evidence, and follow-through', after: 'A defined process with roles, approved information, controls, and a measurable outcome', detail: 'The Agentic AI blueprint gives business, development, and platform teams one structure for designing that process and implementing it safely.', speakerPrompt: 'Make the audience decision explicit: can this become a repeatable process their organization is prepared to own?' },
    ] },
    { id: 'architecture', label: '01', title: 'Guided Architecture', scenes: [
      { id: 'guided-architecture', type: 'guided-architecture', beat: 'system-reveal', eyebrow: 'A development blueprint teams can reuse', title: 'Five decisions turn an AI idea into an operating process', body: 'Begin with ownership and outcome. Add technology only when the process requires it.', citation: { label: 'Architecture basis: Red Hat open blueprint for cloud-native AI agents', url: 'https://developers.redhat.com/articles/2026/07/20/architect-open-blueprint-cloud-native-ai-agents' }, layers: [
        { id: 'control', component: '1 · Define', tone: 'primary', question: 'What outcome should this agent process deliver—and who owns it?', answer: 'Define the request, expected result, business owner, and deployment policy before selecting models or tools.', detail: 'Implementation basis: a versioned blueprint is deployed through Helm and GitOps as a managed OpenShift workload.', activeNodeIds: ['operator', 'route'] },
        { id: 'workload', component: '2 · Organize', tone: 'partner', question: 'Which responsibilities should people, agents, and applications each own?', answer: 'Break the process into specialist responsibilities while keeping one accountable workflow owner.', detail: 'Implementation basis: the orchestrator delegates visible work to research, analysis, and execution roles through A2A.', activeNodeIds: ['orchestrator', 'agents'] },
        { id: 'checkpoint', component: '3 · Govern', tone: 'success', question: 'What information may the process use—and which actions require approval?', answer: 'Approve the evidence sources, permitted tools, policy rules, and human decision points before execution.', detail: 'Implementation basis: MCP exposes named tools; allow-lists, versioned policy, guardrails, and approval gates constrain their use.', activeNodeIds: ['guardrails', 'mcp', 'policy'] },
        { id: 'inference', component: '4 · Run', tone: 'partner', question: 'What level of AI capability does each step actually need?', answer: 'Route each task to an appropriate model and infrastructure tier without giving the model business authority.', detail: 'Implementation basis: semantic routing selects an OpenAI-compatible model running on Intel Xeon CPU. The model generates bounded work products only.', activeNodeIds: ['router', 'model'] },
        { id: 'foundation', component: '5 · Improve', tone: 'primary', question: 'How will the organization prove, review, and improve the process?', answer: 'Preserve the evidence, timing, policy decision, and human outcome from every run.', detail: 'Implementation basis: OpenShift isolation, Intel Xeon compute, proof packs, and human approval create an operable foundation; the wider blueprint adds identity, sandboxing, and end-to-end tracing.', activeNodeIds: ['model', 'policy', 'human'] },
      ], technicalTopology, speakerPrompt: 'Lead each reveal with the business decision, then use the architecture as the concrete implementation answer.' },
    ] },
    { id: 'proof', label: '02', title: 'Live Agent Journey', scenes: [
      { id: 'live', type: 'live-journey', beat: 'live-proof', eyebrow: 'The blueprint in practice · live', title: 'Watch one business request become a governed decision', body: 'The process identifies the right capabilities, gathers approved evidence, prepares a recommendation, and preserves human authority.', cta: 'Start the live process', intake: { label: 'BUSINESS REQUEST', title: 'Investigate INC-1042 and prepare—but do not execute—a remediation.', detail: 'Follow who participates, what evidence they use, where AI contributes, how long the process takes, and who owns the final action.' }, nodes: [
        { id: 'discover', label: 'Discover', detail: 'AgentCards + readiness', tone: 'primary' },
        { id: 'route', label: 'Route', detail: 'workflow + model tier', tone: 'partner' },
        { id: 'delegate', label: 'Delegate', detail: 'A2A context chain', tone: 'partner' },
        { id: 'govern', label: 'Govern', detail: 'tools + approval', tone: 'success' },
        { id: 'review', label: 'Review', detail: 'human authority', tone: 'primary' },
      ], technicalTopology, steps: [
        { id: 'discover', title: 'Confirm available capabilities', detail: 'The process discovers which specialist roles are ready before assigning work.', adapterId: 'agent-registry', activeNode: 0, activeNodeIds: ['operator', 'route', 'orchestrator', 'agents'], resultFields: [{ key: 'agentCount', label: 'Capabilities available' }, { key: 'agents', label: 'Business roles' }, { key: 'routing', label: 'Work selection' }] },
        { id: 'lightweight', title: 'Match effort to the request', detail: 'A smaller request uses a shorter process and exposes the selected AI service and elapsed time.', adapterId: 'workflow-lightweight', activeNode: 2, activeNodeIds: ['operator', 'route', 'orchestrator', 'router', 'agents', 'guardrails', 'model'], resultFields: [{ key: 'workflow', label: 'Process selected' }, { key: 'agents', label: 'Roles involved' }, { key: 'model', label: 'AI service' }, { key: 'latency', label: 'Time to result', suffix: 'ms' }] },
        { id: 'comprehensive', title: 'Build an evidence-backed recommendation', detail: 'A higher-stakes request adds research, analysis, approved information, and execution context.', adapterId: 'workflow-comprehensive', activeNode: 3, activeNodeIds: ['operator', 'route', 'orchestrator', 'router', 'agents', 'guardrails', 'mcp', 'model', 'policy'], resultFields: [{ key: 'status', label: 'Process status' }, { key: 'agents', label: 'Roles involved' }, { key: 'evidence', label: 'Approved evidence' }, { key: 'latency', label: 'Time to result', suffix: 'ms' }] },
        { id: 'policy', title: 'Keep the decision with the accountable owner', detail: 'Policy determines when work pauses for human review; model confidence never becomes permission.', adapterId: 'workflow-policy', activeNode: 4, activeNodeIds: ['orchestrator', 'agents', 'mcp', 'policy', 'human'], resultFields: [{ key: 'policy', label: 'Operating policy' }, { key: 'approvalTool', label: 'Controlled action' }, { key: 'reviewer', label: 'Accountable owner' }, { key: 'authority', label: 'AI authority' }] },
      ], speakerPrompt: 'Describe the business process first. Use the returned technical evidence to prove that each responsibility and control actually operated.' },
      { id: 'comparison', type: 'comparison', beat: 'trials', eyebrow: 'An adoption path—not a big-bang project', title: 'Start with one process, then mature the shared foundation', columns: [
        { label: 'Start', value: 'Prove one outcome', detail: 'Define one accountable process with visible roles, approved information, Intel Xeon inference, policy, evidence, and human review.', tone: 'success' },
        { label: 'Standardize', value: 'Reuse the pattern', detail: 'Turn common agent roles, tools, guardrails, deployment, and evidence requirements into organization-wide building blocks.', tone: 'partner' },
        { label: 'Scale', value: 'Add production controls', detail: 'Extend the foundation with workload identity, sandboxing, gateway authorization, observability, and advanced inference routing.', tone: 'neutral' },
      ], speakerPrompt: 'Position the blueprint as a practical adoption roadmap: prove value, standardize the pattern, then add controls as scale and risk require them.' },
    ] },
    { id: 'mechanisms', label: '03', title: 'Why It Works', scenes: [
      { id: 'mechanisms', type: 'mechanisms', beat: 'trials', eyebrow: 'A shared implementation model', title: 'Business, development, and platform teams work from one blueprint', mechanisms: [
        { id: 'business', label: 'Business design', claim: 'Define the outcome, owner, evidence, decision, and acceptable risk.', detail: 'Success is a governed business result—not simply an agent response.', tone: 'success' },
        { id: 'development', label: 'Agent development', claim: 'Implement responsibilities, collaboration, information access, and human handoffs.', detail: 'A2A and MCP provide open implementation patterns without becoming the business story.', tone: 'partner' },
        { id: 'platform', label: 'Red Hat × Intel platform', claim: 'Operate the process on OpenShift with Intel Xeon CPU inference.', detail: 'The shared foundation supplies deployment, scaling, controls, observability, and a path to stronger production isolation.', tone: 'primary' },
      ], speakerPrompt: 'Show how one blueprint aligns three teams. Mention protocols only as implementation choices beneath the shared process.' },
    ] },
    { id: 'payoff', label: '04', title: 'Close', scenes: [
      { id: 'payoff', type: 'evidence-payoff', beat: 'transformation', eyebrow: 'What the blueprint enables', title: 'Build an agent process the organization can own', adapterIds: ['agent-registry', 'workflow-lightweight', 'workflow-comprehensive', 'workflow-policy'], fallbackLine: 'Run the business process to build the proof', evidenceFields: [{ key: 'policy', label: 'Operating policy' }, { key: 'approvalTool', label: 'Controlled action' }, { key: 'reviewer', label: 'Accountable owner' }, { key: 'authority', label: 'AI authority' }], line1: 'Red Hat turns agent development into an operable, governed process.', line2: 'Intel Xeon provides the CPU inference foundation that runs the AI work inside it.', cta: 'Close the presentation. The hands-on lab applies the blueprint to the next process.', speakerPrompt: 'Close on organizational value: a repeatable way to design, implement, govern, and improve agent processes.' },
    ] },
  ],
  journeyHandoffs: [
    { depth: 'lab', title: 'Apply the Agentic AI blueprint', duration: '60–90 minutes', question: 'Can the learner turn another business process into defined roles, evidence, AI work, policy, and accountable action?', technology: 'Red Hat OpenShift · Intel Xeon · A2A · MCP · semantic routing · human approval', instruction: 'After closing the presentation, open the Launchpad lab and use the same blueprint to customize one process.' },
  ],
}
