import { motion } from 'motion/react'
import type { DemoConfig } from '../types'

export function Finale({ config, onRestart }: { config: DemoConfig; onRestart: () => void }) {
  return (
    <main className="finale">
      <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}>
        <div className="eyebrow">Story complete</div>
        <h1>{config.cta}</h1>
        {(config.journeyHandoffs ?? config.relatedStories)?.[0] && (() => { const story = (config.journeyHandoffs ?? config.relatedStories)![0]; return <div className="guided-handoff"><div className="journey-meta">Optional next step · {story.duration}</div><strong>{story.title}</strong><span>{story.instruction}</span>{story.href && <a className="button button-primary" href={story.href}>Begin guided experience →</a>}</div> })()}
        <div className="finale-actions"><button className="button button-secondary" onClick={onRestart}>Close presentation</button><button className="button button-quiet" onClick={onRestart}>Restart</button></div>
        <div className="attribution">{config.brand.attribution}</div>
      </motion.div>
    </main>
  )
}
