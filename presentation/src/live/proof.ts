import type { LiveDataAdapter, ProofState } from '../types'

const sessionCache = new Map<string, ProofState>()

export function getCachedProof(id: string) {
  return sessionCache.get(id)
}

export async function runProof<T extends Record<string, unknown>>(
  adapter: LiveDataAdapter<T>,
  outerSignal?: AbortSignal,
): Promise<ProofState<T>> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), adapter.timeoutMs ?? 8_000)
  const abort = () => controller.abort()
  outerSignal?.addEventListener('abort', abort, { once: true })

  try {
    const data = await adapter.load(controller.signal)
    const state: ProofState<T> = {
      status: 'ready',
      source: 'live',
      data,
      collectedAt: new Date().toISOString(),
    }
    sessionCache.set(adapter.id, state)
    return state
  } catch (error) {
    if (outerSignal?.aborted) {
      return { status: 'error', error: 'Request cancelled.' }
    }
    const state: ProofState<T> = {
      status: 'ready',
      source: navigator.onLine ? 'rehearsal' : 'offline',
      data: adapter.rehearsal.data,
      collectedAt: adapter.rehearsal.collectedAt,
      error: error instanceof Error ? error.message : 'Live endpoint unavailable.',
    }
    sessionCache.set(adapter.id, state)
    return state
  } finally {
    window.clearTimeout(timeout)
    outerSignal?.removeEventListener('abort', abort)
  }
}

export function clearProofCache() {
  sessionCache.clear()
}
