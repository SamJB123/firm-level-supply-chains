import { useEffect, useMemo, useRef } from 'react'

import Sigma from 'sigma'

import { buildSigmaGraph } from '../lib/graph/transform'
import type { GraphBundle } from '../lib/types'

interface GraphCanvasProps {
  bundle: GraphBundle
  onSelectNode: (nodeId: string | null) => void
  onSelectEdge: (edgeId: string | null) => void
}

export function GraphCanvas({ bundle, onSelectNode, onSelectEdge }: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const sigmaRef = useRef<Sigma | null>(null)
  const graph = useMemo(() => buildSigmaGraph(bundle), [bundle])

  useEffect(() => {
    if (!containerRef.current || graph.order === 0) {
      return
    }

    const sigma = new Sigma(graph, containerRef.current, {
      allowInvalidContainer: true,
      renderEdgeLabels: false,
      labelDensity: 0.08,
      labelSize: 12,
      defaultEdgeType: 'arrow',
    })
    sigmaRef.current = sigma

    sigma.on('clickNode', ({ node }) => {
      onSelectEdge(null)
      onSelectNode(node)
    })

    sigma.on('clickEdge', ({ edge }) => {
      onSelectNode(null)
      onSelectEdge(edge)
    })

    sigma.on('clickStage', () => {
      onSelectNode(null)
      onSelectEdge(null)
    })

    return () => {
      sigma.kill()
      sigmaRef.current = null
    }
  }, [graph, onSelectEdge, onSelectNode])

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
        <h2>Supply-chain network</h2>
        <p>Click a node or edge to inspect evidence and candidate hypotheses.</p>
      </div>
      <div className="graph-canvas" ref={containerRef} />
    </section>
  )
}
