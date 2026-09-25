import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { DemoHeader } from './components/DemoHeader'
import { Finale } from './components/Finale'
import { Opening } from './components/Opening'
import { demoConfig } from './demo.config'
import './live/demoAdapter'
import { SceneRenderer } from './scenes/SceneRenderer'
import { validateDemoConfig } from './config/validate'

type Position = { act: number; scene: number }

function readPosition(): { started: boolean; position: Position; finale: boolean } {
  const params = new URLSearchParams(window.location.search)
  return {
    started: params.has('act'),
    position: {
      act: Math.max(0, Number(params.get('act') ?? 0)),
      scene: Math.max(0, Number(params.get('scene') ?? 0)),
    },
    finale: params.get('finale') === '1',
  }
}

function writePosition(position: Position, finale = false, replace = false) {
  const params = new URLSearchParams({ act: String(position.act), scene: String(position.scene) })
  if (finale) params.set('finale', '1')
  window.history[replace ? 'replaceState' : 'pushState'](null, '', `?${params}`)
}

export default function App() {
  const initial = useMemo(readPosition, [])
  const [started, setStarted] = useState(initial.started)
  const [position, setPosition] = useState<Position>(initial.position)
  const [finale, setFinale] = useState(initial.finale)
  const [showPresenterPrompt, setShowPresenterPrompt] = useState(false)
  const touchStart = useRef<number | null>(null)
  const warnings = useMemo(() => validateDemoConfig(demoConfig), [])
  const safeAct = Math.min(position.act, demoConfig.acts.length - 1)
  const act = demoConfig.acts[safeAct]
  const safeScene = Math.min(position.scene, act.scenes.length - 1)
  const scene = act.scenes[safeScene]

  useEffect(() => warnings.forEach((warning) => console.warn(`[demo-story] ${warning}`)), [warnings])

  const navigate = useCallback((next: Position, nextFinale = false, replace = false) => {
    setStarted(true)
    setPosition(next)
    setFinale(nextFinale)
    writePosition(next, nextFinale, replace)
  }, [])

  const next = useCallback(() => {
    if (finale) return
    if (safeScene < act.scenes.length - 1) navigate({ act: safeAct, scene: safeScene + 1 })
    else if (safeAct < demoConfig.acts.length - 1) navigate({ act: safeAct + 1, scene: 0 })
    else navigate({ act: safeAct, scene: safeScene }, true)
  }, [act.scenes.length, finale, navigate, safeAct, safeScene])

  const previous = useCallback(() => {
    if (finale) return navigate({ act: demoConfig.acts.length - 1, scene: demoConfig.acts.at(-1)!.scenes.length - 1 })
    if (safeScene > 0) navigate({ act: safeAct, scene: safeScene - 1 })
    else if (safeAct > 0) navigate({ act: safeAct - 1, scene: demoConfig.acts[safeAct - 1].scenes.length - 1 })
  }, [finale, navigate, safeAct, safeScene])

  const restart = useCallback(() => {
    setStarted(false)
    setPosition({ act: 0, scene: 0 })
    setFinale(false)
    window.history.pushState(null, '', window.location.pathname)
  }, [])

  useEffect(() => {
    const onPop = () => {
      const state = readPosition()
      setStarted(state.started)
      setPosition(state.position)
      setFinale(state.finale)
    }
    const onKey = (event: KeyboardEvent) => {
      if (['ArrowRight', 'PageDown', ' '].includes(event.key)) { event.preventDefault(); next() }
      if (['ArrowLeft', 'PageUp'].includes(event.key)) { event.preventDefault(); previous() }
      if (event.key === 'Home') restart()
      if (event.key.toLowerCase() === 'f') void document.documentElement.requestFullscreen?.()
      if (event.key.toLowerCase() === 'p') setShowPresenterPrompt((visible) => !visible)
    }
    window.addEventListener('popstate', onPop)
    window.addEventListener('keydown', onKey)
    return () => { window.removeEventListener('popstate', onPop); window.removeEventListener('keydown', onKey) }
  }, [next, previous, restart])

  if (!started) return <Opening config={demoConfig} onStart={() => navigate({ act: 0, scene: 0 }, false, true)} />

  return (
    <div
      className="app"
      onTouchStart={(event) => { touchStart.current = event.changedTouches[0].clientX }}
      onTouchEnd={(event) => {
        if (touchStart.current === null) return
        const delta = event.changedTouches[0].clientX - touchStart.current
        if (Math.abs(delta) > 60) delta < 0 ? next() : previous()
        touchStart.current = null
      }}
    >
      <DemoHeader
        brand={demoConfig.brand}
        acts={demoConfig.acts}
        actIndex={safeAct}
        onAct={(index) => navigate({ act: index, scene: 0 })}
        onPrevious={previous}
        onNext={next}
        onRestart={restart}
        onFullscreen={() => document.fullscreenElement ? void document.exitFullscreen() : void document.documentElement.requestFullscreen?.()}
        onPresenterPrompt={() => setShowPresenterPrompt((visible) => !visible)}
        presenterPromptVisible={showPresenterPrompt}
      />
      <div className="stage" onClick={(event) => { if ((event.target as HTMLElement).closest('button, a')) return; next() }}>
        <AnimatePresence mode="wait">
          {finale ? <motion.div key="finale"><Finale config={demoConfig} onRestart={restart} /></motion.div> : <SceneRenderer key={scene.id} scene={scene} brand={demoConfig.brand} />}
        </AnimatePresence>
      </div>
      {!finale && <div className="scene-progress">{act.label} · {safeScene + 1}/{act.scenes.length}</div>}
      {!finale && showPresenterPrompt && scene.speakerPrompt && <aside className="presenter-prompt" aria-live="polite"><strong>Presenter prompt</strong><span>{scene.speakerPrompt}</span></aside>}
    </div>
  )
}
