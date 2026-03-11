import { createRoute } from '@tanstack/react-router'
import { useEffect, useMemo, useState } from 'react'

import { DetailsPanel } from '../components/DetailsPanel'
import { FiltersPanel } from '../components/FiltersPanel'
import { GraphCanvas } from '../components/GraphCanvas'
import { Legend } from '../components/Legend'
import { createDefaultFilters, filterBundle, findEdge, findNode } from '../lib/graph/transform'
import { loadGraphData } from '../lib/graph/loadGraph'
import type { FilterState, GraphBundle, GraphSummary } from '../lib/types'
import { rootRoute } from './__root'

export const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: IndexRoute,
})

function IndexRoute() {
  const [bundle, setBundle] = useState<GraphBundle | null>(null)
  const [summary, setSummary] = useState<GraphSummary | null>(null)
  const [filters, setFilters] = useState<FilterState>({
    countries: [],
    relationTypes: [],
    confidenceBands: [],
    sourceSystems: [],
    search: '',
    showCandidates: true,
    showPlaceholders: true,
  })
  const [filtersReady, setFiltersReady] = useState(false)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadGraphData()
      .then(({ bundle: loadedBundle, summary: loadedSummary }) => {
        setBundle(loadedBundle)
        setSummary(loadedSummary)
        setFilters(createDefaultFilters(loadedBundle))
        setFiltersReady(true)
      })
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : 'Unknown loading error')
      })
  }, [])

  const filteredBundle = useMemo(() => {
    if (!bundle || !filtersReady) {
      return null
    }
    return filterBundle(bundle, filters)
  }, [bundle, filters, filtersReady])

  const selectedNode = filteredBundle ? findNode(filteredBundle, selectedNodeId) : null
  const selectedEdge = filteredBundle ? findEdge(filteredBundle, selectedEdgeId) : null

  if (error) {
    return (
      <section className="panel status-panel">
        <h2>Unable to load graph data</h2>
        <p>{error}</p>
      </section>
    )
  }

  if (!bundle || !summary || !filtersReady || !filteredBundle) {
    return (
      <section className="panel status-panel">
        <h2>Loading processed graph</h2>
        <p>Reading graph artifacts from the local public data directory.</p>
      </section>
    )
  }

  return (
    <div className="dashboard">
      <section className="summary-grid">
        <SummaryCard label="Nodes" value={summary.nodeCount} />
        <SummaryCard label="Edges" value={summary.edgeCount} />
        <SummaryCard label="Evidence records" value={summary.evidenceCount} />
        <SummaryCard label="Candidate hints" value={summary.candidateCount} />
      </section>

      <div className="dashboard-grid">
        <FiltersPanel bundle={bundle} filters={filters} setFilters={setFilters} />
        <GraphCanvas
          bundle={filteredBundle}
          onSelectNode={setSelectedNodeId}
          onSelectEdge={setSelectedEdgeId}
        />
        <div className="sidebar-stack">
          <Legend />
          <DetailsPanel
            bundle={filteredBundle}
            selectedNode={selectedNode}
            selectedEdge={selectedEdge}
          />
        </div>
      </div>
    </div>
  )
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  )
}
