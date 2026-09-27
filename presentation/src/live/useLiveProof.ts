import { useCallback, useEffect, useRef, useState } from 'react'
import { getCachedProof, runProof } from './proof'
import type { LiveDataAdapter, ProofState } from '../types'

export function useLiveProof<T extends Record<string, unknown>>(adapter?: LiveDataAdapter<T>) {
  const [state, setState] = useState<ProofState<T>>(
    () => (adapter && getCachedProof(adapter.id) as ProofState<T>) ?? { status: 'idle' },
  )
  const controller = useRef<AbortController | null>(null)

  const run = useCallback(async () => {
    if (!adapter) {
      setState({ status: 'error', error: 'No adapter registered for this scene.' })
      return
    }
    controller.current?.abort()
    controller.current = new AbortController()
    setState({ status: 'loading' })
    setState(await runProof(adapter, controller.current.signal))
  }, [adapter])

  useEffect(() => () => controller.current?.abort(), [])
  return { state, run }
}
