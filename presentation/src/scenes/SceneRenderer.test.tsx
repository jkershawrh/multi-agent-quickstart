import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { demoConfig } from '../demo.config'
import '../live/demoAdapter'
import type { SceneConfig } from '../types'
import { SceneRenderer } from './SceneRenderer'

describe('SceneRenderer', () => {
  const scenes = demoConfig.acts.flatMap((act) => act.scenes)

  for (const scene of scenes) {
    it(`renders ${scene.type}: ${scene.id}`, () => {
      const { container } = render(<SceneRenderer scene={scene} brand={demoConfig.brand} />)
      expect(container.querySelector('.scene')).toBeInTheDocument()
    })
  }

  it('labels rehearsal data instead of presenting it as live', async () => {
    const scene: SceneConfig = { id: 'fallback', type: 'live-proof', beat: 'live-proof', title: 'Proof', adapterId: 'agent-registry', cta: 'Run live proof', resultFields: [{ key: 'agents', label: 'Agents' }] }
    render(<SceneRenderer scene={scene} brand={demoConfig.brand} />)
    fireEvent.click(screen.getByRole('button', { name: /run live proof/i }))
    expect(await screen.findByText('rehearsal')).toBeInTheDocument()
  })

  it('runs a guided proof through the visible architecture', async () => {
    const scene = scenes.find((item) => item.type === 'live-journey')!
    render(<SceneRenderer scene={scene} brand={demoConfig.brand} />)
    expect(screen.getByTestId('live-workspace')).toBeInTheDocument()
    expect(screen.getByText('Investigate INC-1042 and prepare—but do not execute—a remediation.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /discover capable agents/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /run a lightweight request/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /change the workflow depth/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /inspect the authority boundary/i })).toBeInTheDocument()
    expect(screen.queryByLabelText('Live technical deployment topology')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Inspect technical topology' }))
    expect(screen.getByLabelText('Live technical deployment topology')).toBeInTheDocument()
    expect(screen.getByText('OpenShift namespace')).toBeInTheDocument()
    expect(screen.getByText('POST /api/v1/workflow')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /discover live agents/i }))
    expect((await screen.findAllByText('Discover capable agents'))[0]).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /next live act/i })).toBeInTheDocument()
  })

  it('renders the statistic-grid scene', () => {
    const scene: SceneConfig = {
      id: 'coverage-stat-grid',
      type: 'stat-grid',
      beat: 'stakes',
      title: 'The stakes',
      stats: [{ value: '3×', label: 'Faster', tone: 'success' }],
    }
    render(<SceneRenderer scene={scene} brand={demoConfig.brand} />)
    expect(screen.getByText('3×')).toBeInTheDocument()
    expect(screen.getByText('Faster')).toBeInTheDocument()
  })

  it('renders the custom React scene escape hatch', () => {
    const scene: SceneConfig = {
      id: 'coverage-custom',
      type: 'custom',
      beat: 'live-proof',
      component: () => <div>Custom proof scene</div>,
    }
    render(<SceneRenderer scene={scene} brand={demoConfig.brand} />)
    expect(screen.getByText('Custom proof scene')).toBeInTheDocument()
  })

  it('guides architecture as audience questions and revealed answers', async () => {
    const scene = scenes.find((item) => item.type === 'guided-architecture')!
    render(<SceneRenderer scene={scene} brand={demoConfig.brand} />)
    expect(screen.getByText('What enters the system—and where?')).toBeInTheDocument()
    expect(screen.queryByText('A bounded workflow request enters through an OpenShift Route and Service.')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Reveal technical boundary' }))
    expect(await screen.findByText('A bounded workflow request enters through an OpenShift Route and Service.')).toBeInTheDocument()
    expect(document.querySelector('[data-node="route"]')).toHaveClass('active')
    fireEvent.click(screen.getByRole('button', { name: 'Ask next question →' }))
    expect(await screen.findByText('Who decides how much work this request needs?')).toBeInTheDocument()
  })

  it('keeps the presenter pitch at seven scenes or fewer', () => {
    expect(scenes.length).toBeLessThanOrEqual(7)
  })

  it('includes the full progressive proof arc before the lab handoff', () => {
    expect(scenes.some((scene) => scene.type === 'guided-architecture')).toBe(true)
    expect(scenes.some((scene) => scene.type === 'live-journey')).toBe(true)
    expect(scenes.some((scene) => scene.type === 'comparison' || scene.type === 'scale' || scene.type === 'tradeoff')).toBe(true)
    expect(scenes.some((scene) => scene.type === 'mechanisms')).toBe(true)
    expect(scenes.at(-1)?.type).toBe('evidence-payoff')
  })

  it('does not claim session proof before the live journey runs', () => {
    const configured = scenes.find((item) => item.type === 'evidence-payoff')!
    const scene = { ...configured, adapterIds: ['proof-that-has-not-run'] }
    render(<SceneRenderer scene={scene} brand={demoConfig.brand} />)
    expect(screen.getByText('Run the live agent journey to build the proof')).toBeInTheDocument()
    expect(screen.getByText('not run')).toBeInTheDocument()
  })

  const architectureScenes: SceneConfig[] = [
    {
      id: 'coverage-flow', type: 'architecture-flow', beat: 'system-reveal', title: 'Request flow',
      steps: [{ id: 'entry', label: 'Entry', transition: 'route' }, { id: 'model', label: 'Model' }],
    },
    {
      id: 'coverage-layers', type: 'architecture-layers', beat: 'system-reveal', title: 'Layers',
      layers: [{ id: 'platform', label: 'Platform', responsibility: 'Schedules the workload' }],
    },
    {
      id: 'coverage-compare', type: 'architecture-compare', beat: 'reframe', title: 'Structural change',
      before: { label: 'Before', nodes: ['Fixed path'] }, after: { label: 'After', nodes: ['Measured route'] }, insight: 'Measure before routing.',
    },
    {
      id: 'coverage-boundary', type: 'trust-boundary', beat: 'system-reveal', title: 'Trust boundaries',
      zones: [{ id: 'trusted', label: 'Trusted zone', boundary: 'Policy boundary', items: ['Private data'] }],
    },
    {
      id: 'coverage-topology', type: 'deployment-topology', beat: 'system-reveal', title: 'Placement',
      locations: [{ id: 'edge', label: 'Edge', workloads: ['Router'] }],
    },
  ]

  for (const scene of architectureScenes) {
    it(`renders architecture view: ${scene.type}`, () => {
      const { container } = render(<SceneRenderer scene={scene} brand={demoConfig.brand} />)
      expect(container.querySelector('.scene')).toBeInTheDocument()
    })
  }
})
