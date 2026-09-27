import { getAdapter } from '../live/adapters'
import { useLiveProof } from '../live/useLiveProof'
import type { LiveProofScene } from '../types'
import { SceneFrame } from './SceneFrame'

export function LiveProof({ scene }: { scene: LiveProofScene }) {
  const adapter = getAdapter(scene.adapterId)
  const { state, run } = useLiveProof(adapter)

  return (
    <SceneFrame scene={scene}>
      <div className="proof-toolbar">
        <button className="button button-primary" onClick={run} disabled={state.status === 'loading'}>
          {state.status === 'loading' ? 'Running…' : state.status === 'ready' ? 'Retry live proof' : scene.cta}
        </button>
        {state.source && <span className={`source-badge source-${state.source}`}>{state.source}</span>}
      </div>
      {state.status === 'error' && <div className="error-panel">{state.error}</div>}
      {state.status === 'ready' && state.data && (
        <div className="metric-grid">
          {scene.resultFields.map((field) => (
            <div className="metric-card" key={field.key}>
              <div className="metric-label">{field.label}</div>
              <div className="metric-value">{String(state.data?.[field.key] ?? '—')}{field.suffix}</div>
            </div>
          ))}
        </div>
      )}
      {state.error && state.status === 'ready' && (
        <p className="fallback-note">Live service unavailable. Showing clearly labeled rehearsal data. {state.error}</p>
      )}
      {state.collectedAt && <div className="timestamp">Collected {new Date(state.collectedAt).toLocaleString()}</div>}
    </SceneFrame>
  )
}
