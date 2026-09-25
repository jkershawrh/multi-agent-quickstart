import type { DemoConfig, StoryBeat } from '../types'

const requiredBeats: Array<{ label: string; choices: StoryBeat[] }> = [
  { label: 'stakes', choices: ['stakes'] },
  { label: 'proof', choices: ['live-proof', 'system-reveal'] },
  { label: 'payoff', choices: ['transformation'] },
]

export function validateDemoConfig(config: DemoConfig): string[] {
  const warnings: string[] = []
  const ids = new Set<string>()
  const beats = new Set(config.acts.flatMap((act) => act.scenes.map((scene) => scene.beat)))

  if (!config.acts.length) warnings.push('Demo must contain at least one act.')
  for (const act of config.acts) {
    if (!act.scenes.length) warnings.push(`Act "${act.title}" has no scenes.`)
    for (const scene of act.scenes) {
      if (ids.has(scene.id)) warnings.push(`Duplicate scene id: ${scene.id}`)
      ids.add(scene.id)
    }
  }

  for (const requirement of requiredBeats) {
    if (!requirement.choices.some((beat) => beats.has(beat))) {
      warnings.push(`Story is missing a ${requirement.label} beat.`)
    }
  }

  const scenes = config.acts.flatMap((act) => act.scenes)
  if (scenes.length > 7) warnings.push(`Presenter story has ${scenes.length} scenes; keep the pitch to 7 or fewer and move depth into the guided demo or lab.`)
  if (!scenes.some((scene) => scene.type === 'guided-architecture')) warnings.push('Story is missing a guided architecture reveal.')
  if (!scenes.some((scene) => scene.type === 'live-proof' || scene.type === 'live-journey')) warnings.push('Story is missing a live proof scene.')
  const handoffs = config.journeyHandoffs ?? config.relatedStories ?? []
  if (!handoffs.length) warnings.push('Finale must provide one explicit guided handoff or close.')
  if (!scenes.some((scene) => scene.type === 'mechanisms')) warnings.push('Pre-lab journey is missing a mechanism deep dive.')
  if (!scenes.some((scene) => scene.type === 'evidence-payoff')) warnings.push('Payoff should recap evidence produced during the live journey.')
  for (const scene of scenes) {
    if (scene.type === 'metric' || scene.type === 'stat-grid' || scene.type === 'scale') {
      warnings.push(`Scene "${scene.id}" contains static metrics; quantitative demo metrics must be returned by a live-proof or live-journey adapter.`)
    }
    if (scene.type === 'comparison' && scene.columns.some((column) => /\d/.test(column.value))) {
      warnings.push(`Scene "${scene.id}" contains static comparison numbers; quantitative comparisons must be returned by live infrastructure.`)
    }
  }

  return warnings
}
