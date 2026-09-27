import type { LiveJourneyScene } from '../types'

type Topology = NonNullable<LiveJourneyScene['technicalTopology']>
type Node = Topology['entry']

function TechnicalNode({ node, active }: { node: Node; active: boolean }) {
  return <div className={`topology-node ${active ? 'active' : ''}`} data-node={node.id}><span className="topology-kind">{node.kind}</span><strong>{node.label}</strong><small>{node.detail}</small>{node.endpoint && <code>{node.endpoint}</code>}</div>
}

function Edge({ label, active, dashed }: { label?: string; active: boolean; dashed?: boolean }) {
  return <div className={`topology-edge ${active ? 'active' : ''} ${dashed ? 'dashed' : ''}`}><span>{label ?? 'flow'}</span><b>→</b></div>
}

export function TechnicalTopology({ topology, activeIds }: { topology: Topology; activeIds: string[] }) {
  const active = (id: string) => activeIds.includes(id)
  const renderPath = (nodes: Topology['primaryPath']) => nodes.map((node) => <div className="topology-path-item" key={node.id}><Edge label={node.edgeLabel} active={active(node.id)} /><TechnicalNode node={node} active={active(node.id)} /></div>)
  return <div className="technical-topology" aria-label="Live technical deployment topology">
    <div className="topology-legend"><span><i className="legend-live" /> active request and evidence path</span><span><i className="legend-boundary" /> deployment or trust boundary</span><span><i className="legend-optional" /> optional integration</span></div>
    <div className="topology-graph"><TechnicalNode node={topology.entry} active={active(topology.entry.id)} /><div className="topology-boundary"><div className="topology-boundary-title"><strong>{topology.boundary.label}</strong><span>{topology.boundary.detail}</span></div><div className="topology-path">{renderPath(topology.primaryPath)}</div><div className="topology-path topology-support">{renderPath(topology.supportPath)}</div></div>{topology.optionalPath && <div className="topology-optional"><Edge label={topology.optionalPath.edgeLabel} active={active(topology.optionalPath.id)} dashed /><TechnicalNode node={topology.optionalPath} active={active(topology.optionalPath.id)} /></div>}</div>
  </div>
}
