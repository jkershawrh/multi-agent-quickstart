import type { ActConfig, BrandConfig } from '../types'
import { BrandLockup } from './BrandLockup'

export function DemoHeader({ brand, acts, actIndex, onAct, onPrevious, onNext, onRestart, onFullscreen, onPresenterPrompt, presenterPromptVisible }: {
  brand: BrandConfig
  acts: ActConfig[]
  actIndex: number
  onAct: (index: number) => void
  onPrevious: () => void
  onNext: () => void
  onRestart: () => void
  onFullscreen: () => void
  onPresenterPrompt: () => void
  presenterPromptVisible: boolean
}) {
  return (
    <header className="demo-header">
      <button className="brand-button" onClick={onRestart} aria-label="Restart presentation"><BrandLockup brand={brand} compact /></button>
      <nav className="presenter-controls" aria-label="Presentation navigation">
        <button onClick={onPrevious} aria-label="Previous scene">←</button>
        <div className="progress" role="tablist" aria-label="Acts">
          {acts.map((act, index) => <button key={act.id} className={index === actIndex ? 'active' : index < actIndex ? 'done' : ''} onClick={() => onAct(index)} title={`${act.label} ${act.title}`} aria-label={`Go to act ${act.label}: ${act.title}`} />)}
        </div>
        <button onClick={onNext} aria-label="Next scene">→</button>
        <button className={presenterPromptVisible ? 'control-active' : ''} onClick={onPresenterPrompt} aria-label="Toggle presenter prompt">P</button>
        <button onClick={onFullscreen} aria-label="Toggle fullscreen">⛶</button>
      </nav>
    </header>
  )
}
