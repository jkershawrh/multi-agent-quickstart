import type { LiveDataAdapter } from '../types'

export const adapters = new Map<string, LiveDataAdapter>()

export function registerAdapter(adapter: LiveDataAdapter) {
  adapters.set(adapter.id, adapter)
}

export function getAdapter(id: string) {
  return adapters.get(id)
}

export function createJsonAdapter<T extends Record<string, unknown>>(options: {
  id: string
  url: string
  method?: 'GET' | 'POST'
  body?: unknown
  timeoutMs?: number
  rehearsal: { data: T; collectedAt: string }
}): LiveDataAdapter<T> {
  return {
    id: options.id,
    timeoutMs: options.timeoutMs ?? 8_000,
    rehearsal: options.rehearsal,
    async load(signal) {
      const response = await fetch(options.url, {
        method: options.method ?? 'GET',
        headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal,
      })
      if (!response.ok) throw new Error(`Live endpoint returned HTTP ${response.status}`)
      return response.json() as Promise<T>
    },
  }
}
