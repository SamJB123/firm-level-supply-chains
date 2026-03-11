import { useEffect, useRef } from 'react'

import ForceGraph3D, {
  type ForceGraph3DInstance,
  type LinkObject,
  type NodeObject,
} from '3d-force-graph'

import type { GraphBundle } from '../lib/types'

interface GraphCanvasProps {
  bundle: GraphBundle
  onSelectNode: (nodeId: string | null) => void
  onSelectEdge: (edgeId: string | null) => void
}

export function GraphCanvas({ bundle, onSelectNode, onSelectEdge }: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const graphRef = useRef<ForceGraph3DInstance | null>(null)

  useEffect(() => {
    if (!containerRef.current) {
      return
    }

    const container = containerRef.current
    const graph = new ForceGraph3D(container, {
      controlType: 'orbit',
      rendererConfig: { antialias: true, alpha: true },
    })
      .backgroundColor('#081221')
      .showNavInfo(false)
      .nodeLabel((node) => getNodeLabel(node))
      .nodeColor((node) => getNodeColor(node))
      .nodeVal((node) => getNodeValue(node))
      .nodeOpacity(0.95)
      .nodeResolution(16)
      .linkLabel((link) => getLinkLabel(link))
      .linkColor((link) => getLinkColor(link))
      .linkOpacity(0.85)
      .linkWidth((link) => getLinkWidth(link))
      .linkDirectionalArrowLength((link) => getLinkArrowLength(link))
      .linkDirectionalArrowRelPos(1)
      .linkDirectionalArrowColor((link) => getLinkColor(link))
      .linkDirectionalParticles((link) => getLinkParticleCount(link))
      .linkDirectionalParticleWidth((link) => getLinkWidth(link) * 1.5)
      .linkDirectionalParticleColor((link) => getLinkColor(link))
      .enablePointerInteraction(true)
      .onNodeClick((node) => {
        onSelectEdge(null)
        onSelectNode(typeof node.id === 'string' ? node.id : null)
      })
      .onLinkClick((link) => {
        onSelectNode(null)
        onSelectEdge(getLinkId(link))
      })
      .onBackgroundClick(() => {
        onSelectNode(null)
        onSelectEdge(null)
      })
      .onEngineStop(() => {
        graph.zoomToFit(500, 80)
      })

    graph.d3Force('charge')?.strength(-220)
    graph.d3Force('link')?.distance(120)
    graph.cooldownTicks(180)
    graphRef.current = graph

    const updateSize = () => {
      graph.width(container.clientWidth)
      graph.height(Math.max(container.clientHeight, 620))
    }
    updateSize()

    const resizeObserver = new ResizeObserver(() => {
      updateSize()
    })
    resizeObserver.observe(container)

    return () => {
      resizeObserver.disconnect()
      graph._destructor()
      graphRef.current = null
    }
  }, [onSelectEdge, onSelectNode])

  useEffect(() => {
    if (!graphRef.current) {
      return
    }

    graphRef.current.graphData({
      nodes: bundle.nodes.map((node) => ({ ...node })),
      links: bundle.edges.map((edge) => ({ ...edge })),
    })
    graphRef.current.d3ReheatSimulation()
  }, [bundle])

  if (bundle.nodes.length === 0) {
    return (
      <section className="panel graph-panel graph-panel--empty">
        <h2>No graph items match the current filters.</h2>
      </section>
    )
  }

  return (
    <section className="panel graph-panel">
      <div className="panel__header">
        <h2>Supply-chain network (3D)</h2>
        <p>Drag to orbit, scroll to zoom, and click a node or edge to inspect evidence.</p>
      </div>
      <div className="graph-canvas" ref={containerRef} />
    </section>
  )
}

interface ForceNodeLike extends NodeObject {
  id?: string | number
  label?: string
  country?: string
  node_kind?: string
}

interface ForceLinkLike extends LinkObject<NodeObject> {
  id?: string | number
  relation_type?: string
  confidence?: string
  explicit?: boolean
  evidence_ids?: string[]
}

function getNodeLabel(node: ForceNodeLike): string {
  const label = typeof node.label === 'string' ? node.label : String(node.id ?? 'Unknown node')
  const country = typeof node.country === 'string' ? node.country : 'OTHER'
  return `${label} (${country})`
}

function getNodeColor(node: ForceNodeLike): string {
  switch (node.country) {
    case 'AU':
      return '#0f766e'
    case 'CN':
      return '#b91c1c'
    case 'US':
      return '#1d4ed8'
    default:
      return '#6b7280'
  }
}

function getNodeValue(node: ForceNodeLike): number {
  return node.node_kind === 'placeholder' ? 3.2 : 6
}

function getLinkLabel(link: ForceLinkLike): string {
  const relation = typeof link.relation_type === 'string' ? link.relation_type : 'relationship'
  const confidence = typeof link.confidence === 'string' ? link.confidence : 'unknown'
  const evidenceCount = Array.isArray(link.evidence_ids) ? link.evidence_ids.length : 0
  return `${relation} • ${confidence} • ${evidenceCount} evidence records`
}

function getLinkColor(link: ForceLinkLike): string {
  return link.explicit ? '#64748b' : '#f59e0b'
}

function getLinkWidth(link: ForceLinkLike): number {
  switch (link.confidence) {
    case 'high':
      return 2.8
    case 'medium':
      return 1.9
    default:
      return 1.2
  }
}

function getLinkParticleCount(link: ForceLinkLike): number {
  return link.explicit ? 2 : 1
}

function getLinkArrowLength(link: ForceLinkLike): number {
  return link.explicit ? 4.5 : 3.2
}

function getLinkId(link: ForceLinkLike): string | null {
  return typeof link.id === 'string' ? link.id : null
}
