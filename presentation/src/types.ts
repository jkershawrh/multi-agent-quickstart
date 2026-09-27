import type { ComponentType } from 'react'

export type DiscoveryStatus = 'discovered' | 'verified' | 'assumed' | 'unknown' | 'excluded'

export interface BlueprintNode {
  id: string
  name: string
  kind: string
  responsibility: string
  status: DiscoveryStatus
  source: string
}

export interface BlueprintFlowEdge {
  from: string
  to: string
  purpose: string
  protocol?: string
  evidenceIds?: string[]
}

export interface BlueprintFlow {
  id: string
  name: string
  kind: 'request' | 'event' | 'data' | 'evidence' | 'decision' | 'authority'
  trigger: string
  outcome: string
  edges: BlueprintFlowEdge[]
}

export interface OperationalStep {
  id: string
  label: string
  question: string
  flowIds: string[]
  evidenceIds: string[]
  decisionId?: string
}

export interface AiAssessment {
  needed: boolean | 'optional' | 'unknown'
  kind: 'none' | 'rules' | 'classical-ml' | 'embeddings' | 'generative-llm' | 'agentic' | 'mixed'
  rationale: string
  tasks: string[]
  inputs: string[]
  outputs: string[]
  evidenceAccess: string[]
  actionAuthority: 'none' | 'recommend' | 'bounded-actions' | 'autonomous' | 'unknown'
  validation: string[]
  fallback: string
  finalDecisionOwner: string
}

export interface DemoBlueprint {
  version: 1
  status: 'draft' | 'reviewed' | 'approved'
  source: { name: string; kind: string; location: string; revision: string; discoveredAt?: string; inspectedArtifacts: string[]; discrepancies: string[] }
  intent: { primaryUser: string; workload: string; recognizedProblem: string; audienceDecision: string; desiredOutcome: string }
  architecture: { actors: BlueprintNode[]; runtimeObjects: BlueprintNode[]; boundaries: BlueprintNode[]; externalDependencies: BlueprintNode[]; flows: BlueprintFlow[] }
  operationalPattern: { name: string; rationale: string; steps: OperationalStep[]; changedCondition?: string; close?: string }
  evidence: Array<{ id: string; name: string; source: string; collection: string; supports: string; status: DiscoveryStatus }>
  decisions: Array<{ id: string; owner: string; policy: string; failClosedBehavior: string; status: DiscoveryStatus }>
  aiAssessment: AiAssessment
}

export type StoryBeat =
  | 'ordinary-world'
  | 'stakes'
  | 'root-cause'
  | 'reframe'
  | 'system-reveal'
  | 'live-proof'
  | 'trials'
  | 'transformation'
  | 'next-journey'

export type ProofSource = 'live' | 'rehearsal' | 'offline'

export interface BrandConfig {
  primary: { name: string; logo: string; alt: string }
  partner: { name: string; logo: string; alt: string }
  attribution: string
}

export interface Citation {
  label: string
  url?: string
}

export interface BaseScene {
  id: string
  beat: StoryBeat
  eyebrow?: string
  title?: string
  body?: string
  citation?: Citation
  speakerPrompt?: string
}

export interface GuidedArchitectureScene extends BaseScene {
  type: 'guided-architecture'
  layers: Array<{ id: string; question: string; answer: string; component: string; detail: string; tone?: 'primary' | 'partner' | 'success'; activeNodeIds?: string[] }>
  technicalTopology?: LiveJourneyScene['technicalTopology']
}

export interface IntroScene extends BaseScene {
  type: 'intro'
  subtitle: string
}

export interface MetricScene extends BaseScene {
  type: 'metric'
  value: string
  label: string
  tone?: 'neutral' | 'danger' | 'success' | 'partner'
}

export interface QuoteScene extends BaseScene {
  type: 'quote'
  quote: string
  attribution?: string
}

export interface StatGridScene extends BaseScene {
  type: 'stat-grid'
  stats: Array<{ value: string; label: string; tone?: 'neutral' | 'danger' | 'success' | 'partner' }>
}

export interface ReframeScene extends BaseScene {
  type: 'reframe'
  before: string
  after: string
  detail?: string
}

export interface ArchitectureScene extends BaseScene {
  type: 'architecture'
  nodes: Array<{ id: string; label: string; detail?: string; tone?: 'primary' | 'partner' | 'success' }>
}

export interface ArchitectureFlowScene extends BaseScene {
  type: 'architecture-flow'
  steps: Array<{ id: string; label: string; detail?: string; transition?: string; tone?: 'primary' | 'partner' | 'success' }>
}

export interface ArchitectureLayersScene extends BaseScene {
  type: 'architecture-layers'
  layers: Array<{ id: string; label: string; responsibility: string; tone?: 'primary' | 'partner' | 'success' }>
}

export interface ArchitectureCompareScene extends BaseScene {
  type: 'architecture-compare'
  before: { label: string; nodes: string[] }
  after: { label: string; nodes: string[] }
  insight: string
}

export interface TrustBoundaryScene extends BaseScene {
  type: 'trust-boundary'
  zones: Array<{ id: string; label: string; boundary: string; items: string[]; tone?: 'primary' | 'partner' | 'success' }>
}

export interface DeploymentTopologyScene extends BaseScene {
  type: 'deployment-topology'
  locations: Array<{ id: string; label: string; detail?: string; workloads: string[]; tone?: 'primary' | 'partner' | 'success' }>
}

export interface PipelineScene extends BaseScene {
  type: 'pipeline'
  steps: Array<{ label: string; detail?: string }>
}

export interface LiveProofScene extends BaseScene {
  type: 'live-proof'
  adapterId: string
  cta: string
  resultFields: Array<{ key: string; label: string; suffix?: string }>
}

export interface LiveJourneyScene extends BaseScene {
  type: 'live-journey'
  intake?: { label: string; title: string; detail: string }
  nodes: Array<{ id: string; label: string; detail?: string; tone?: 'primary' | 'partner' | 'success' }>
  steps: Array<{
    id: string
    title: string
    detail: string
    adapterId: string
    activeNode: number
    activeNodeIds?: string[]
    resultFields: Array<{ key: string; label: string; suffix?: string }>
  }>
  cta: string
  workspace?: { label: string; href: string }
  technicalTopology?: {
    boundary: { label: string; detail: string }
    entry: { id: string; kind: string; label: string; detail: string; endpoint?: string }
    primaryPath: Array<{ id: string; kind: string; label: string; detail: string; endpoint?: string; edgeLabel?: string }>
    supportPath: Array<{ id: string; kind: string; label: string; detail: string; endpoint?: string; edgeLabel?: string }>
    optionalPath?: { id: string; kind: string; label: string; detail: string; endpoint?: string; edgeLabel?: string }
  }
}

export interface ComparisonScene extends BaseScene {
  type: 'comparison'
  columns: Array<{ label: string; value: string; detail?: string; tone?: 'neutral' | 'danger' | 'success' | 'partner' }>
}

export interface ScaleScene extends BaseScene {
  type: 'scale'
  stages: Array<{ label: string; value: string; detail?: string }>
}

export interface MechanismScene extends BaseScene {
  type: 'mechanisms'
  mechanisms: Array<{
    id: string
    label: string
    claim: string
    detail: string
    tone?: 'primary' | 'partner' | 'success'
  }>
}

export interface EvidencePayoffScene extends BaseScene {
  type: 'evidence-payoff'
  adapterIds: string[]
  fallbackLine: string
  evidenceFields: Array<{ key: string; label: string; suffix?: string }>
  line1: string
  line2: string
  cta?: string
}

export interface TradeoffScene extends BaseScene {
  type: 'tradeoff'
  options: Array<{ title: string; strength: string; tradeoff: string }>
  decision: string
}

export interface PunchlineScene extends BaseScene {
  type: 'punchline'
  line1: string
  line2: string
  cta?: string
}

export interface CustomScene extends BaseScene {
  type: 'custom'
  component: ComponentType
}

export type SceneConfig =
  | IntroScene
  | MetricScene
  | QuoteScene
  | StatGridScene
  | ReframeScene
  | ArchitectureScene
  | GuidedArchitectureScene
  | ArchitectureFlowScene
  | ArchitectureLayersScene
  | ArchitectureCompareScene
  | TrustBoundaryScene
  | DeploymentTopologyScene
  | PipelineScene
  | LiveProofScene
  | LiveJourneyScene
  | ComparisonScene
  | ScaleScene
  | MechanismScene
  | EvidencePayoffScene
  | TradeoffScene
  | PunchlineScene
  | CustomScene

export interface ActConfig {
  id: string
  label: string
  title: string
  scenes: SceneConfig[]
}

export interface RelatedStory {
  title: string
  question: string
  technology: string
  href?: string
  duration?: string
  instruction?: string
}

export type JourneyDepth = 'story' | 'guided' | 'live' | 'lab' | 'platform'

export interface JourneyHandoff {
  depth: JourneyDepth
  title: string
  question: string
  technology: string
  href?: string
  duration?: string
  instruction?: string
}

export interface DemoConfig {
  id: string
  title: string
  subtitle: string
  event?: string
  audience?: string
  cta: string
  brand: BrandConfig
  acts: ActConfig[]
  relatedStories?: RelatedStory[]
  journeyHandoffs?: JourneyHandoff[]
}

export interface RehearsalFixture<T> {
  data: T
  collectedAt: string
}

export interface LiveDataAdapter<T = Record<string, unknown>> {
  id: string
  timeoutMs?: number
  load(signal: AbortSignal): Promise<T>
  rehearsal: RehearsalFixture<T>
}

export interface ProofState<T = Record<string, unknown>> {
  status: 'idle' | 'loading' | 'ready' | 'error'
  source?: ProofSource
  data?: T
  collectedAt?: string
  error?: string
}
