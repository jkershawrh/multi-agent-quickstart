import { registerAdapter } from './adapters'
import type { LiveDataAdapter } from '../types'

const API_BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '')

async function request(path: string, signal: AbortSignal, body?: unknown) {
  const response = await fetch(`${API_BASE}${path}`, { method: body ? 'POST' : 'GET', headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined, signal })
  if (!response.ok) throw new Error(`Live endpoint returned HTTP ${response.status}`)
  return response.json() as Promise<Record<string, unknown>>
}

function adapter(id: string, load: LiveDataAdapter['load'], data: Record<string, unknown>) {
  registerAdapter({ id, timeoutMs: 60_000, load, rehearsal: { data, collectedAt: '2026-09-25T12:00:00.000Z' } })
}

adapter('agent-registry', async (signal) => {
  const payload = await request('/api/v1/agents', signal)
  const agents = Array.isArray(payload.agents) ? payload.agents as Array<Record<string, unknown>> : []
  const health = await request('/health', signal)
  return { agentCount: payload.count ?? agents.length, agents: agents.map((item) => item.name).filter(Boolean).join(' → ') || 'none discovered', routing: health.semantic_routing ?? 'unavailable' }
}, { agentCount: 3, agents: 'research → analyst → executor', routing: 'rehearsal' })

async function runWorkflow(signal: AbortSignal, workflowType: 'lightweight' | 'comprehensive') {
  const payload = await request('/api/v1/workflow', signal, { query: 'Investigate incident INC-1042, compare the available evidence, and prepare a remediation recommendation without executing an action.', workflow_type: workflowType })
  const steps = Array.isArray(payload.steps) ? payload.steps as Array<Record<string, unknown>> : []
  const classification = (payload.classification ?? {}) as Record<string, unknown>
  return { status: payload.status ?? 'completed', workflow: classification.selected_workflow ?? workflowType, agents: steps.map((step) => step.agent).filter(Boolean).join(' → ') || 'no completed agents', model: classification.selected_model ?? 'configured model', evidence: steps.some((step) => String(step.result ?? '').includes('MCP')) ? 'MCP + guarded agent context' : 'guarded agent context', latency: payload.total_latency_ms ?? 'not reported' }
}

adapter('workflow-lightweight', (signal) => runWorkflow(signal, 'lightweight'), { status: 'completed', workflow: 'lightweight', agents: 'executor', model: 'simple tier', evidence: 'guarded agent context', latency: 2300 })
adapter('workflow-comprehensive', (signal) => runWorkflow(signal, 'comprehensive'), { status: 'pending approval', workflow: 'comprehensive', agents: 'research → analyst → executor', model: 'complex tier', evidence: 'MCP + guarded agent context', latency: 10200 })

adapter('workflow-policy', async (signal) => {
  const payload = await request('/api/v1/policy', signal)
  const approvals = Array.isArray(payload.approval_tools) ? payload.approval_tools : []
  return { policy: payload.name ?? 'certified baseline', approvalTool: approvals.join(', ') || 'none configured', reviewer: payload.reviewer_profile ?? 'human operator', authority: 'recommend only' }
}, { policy: 'incident-response-governance', approvalTool: 'create_task', reviewer: 'incident-commander', authority: 'recommend only' })
