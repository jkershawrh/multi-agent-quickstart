import { beforeEach, describe, expect, it, vi } from 'vitest'
import { clearProofCache, runProof } from './proof'
import type { LiveDataAdapter } from '../types'

describe('runProof', () => {
  beforeEach(clearProofCache)

  it('marks successful data as live', async () => {
    const adapter: LiveDataAdapter<{ value: number }> = {
      id: 'success', rehearsal: { data: { value: 1 }, collectedAt: '2026-01-01T00:00:00Z' },
      load: vi.fn().mockResolvedValue({ value: 42 }),
    }
    const state = await runProof(adapter)
    expect(state).toMatchObject({ status: 'ready', source: 'live', data: { value: 42 } })
  })

  it('labels fallback data as rehearsal', async () => {
    const adapter: LiveDataAdapter<{ value: number }> = {
      id: 'fallback', rehearsal: { data: { value: 7 }, collectedAt: '2026-01-01T00:00:00Z' },
      load: vi.fn().mockRejectedValue(new Error('offline')),
    }
    const state = await runProof(adapter)
    expect(state).toMatchObject({ status: 'ready', source: 'rehearsal', data: { value: 7 }, error: 'offline' })
  })

  it('uses fallback when the request times out', async () => {
    vi.useFakeTimers()
    const adapter: LiveDataAdapter<{ value: number }> = {
      id: 'timeout', timeoutMs: 10, rehearsal: { data: { value: 9 }, collectedAt: '2026-01-01T00:00:00Z' },
      load: (signal) => new Promise((_, reject) => signal.addEventListener('abort', () => reject(new Error('timed out')))),
    }
    const promise = runProof(adapter)
    await vi.advanceTimersByTimeAsync(11)
    expect(await promise).toMatchObject({ source: 'rehearsal', data: { value: 9 } })
    vi.useRealTimers()
  })
})
