import type { ReactNode } from 'react'
import { motion } from 'motion/react'
import type { BaseScene } from '../types'

export function SceneFrame({ scene, children }: { scene: BaseScene; children: ReactNode }) {
  return (
    <motion.section
      className="scene"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -18 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      aria-labelledby={`${scene.id}-title`}
    >
      {scene.eyebrow && <div className="eyebrow">{scene.eyebrow}</div>}
      {scene.title && <h1 id={`${scene.id}-title`}>{scene.title}</h1>}
      {scene.body && <p className="lede">{scene.body}</p>}
      {children}
      {scene.citation && (
        <div className="citation">
          {scene.citation.url ? <a href={scene.citation.url}>{scene.citation.label}</a> : scene.citation.label}
        </div>
      )}
    </motion.section>
  )
}
