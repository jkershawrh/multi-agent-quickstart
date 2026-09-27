import { motion } from 'motion/react'
import type { DemoConfig } from '../types'
import { BrandLockup } from './BrandLockup'

export function Opening({ config, onStart }: { config: DemoConfig; onStart: () => void }) {
  return (
    <main className="opening" onClick={onStart} onKeyDown={(event) => (event.key === 'Enter' || event.key === ' ') && onStart()} tabIndex={0}>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1.1 }}>
        <BrandLockup brand={config.brand} />
      </motion.div>
      <motion.h1 initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>{config.title}</motion.h1>
      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 }}>{config.subtitle}</motion.p>
      <motion.span className="start-hint" animate={{ opacity: [0.35, 0.85, 0.35] }} transition={{ repeat: Infinity, duration: 2.4 }}>click or press space to begin</motion.span>
    </main>
  )
}
