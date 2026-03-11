import type { GraphBundle, GraphSummary } from '../types'

export async function loadGraphData(): Promise<{
  bundle: GraphBundle
  summary: GraphSummary
}> {
  const [bundleResponse, summaryResponse] = await Promise.all([
    fetch('/data/graph.json'),
    fetch('/data/summary.json'),
  ])

  if (!bundleResponse.ok || !summaryResponse.ok) {
    throw new Error('Unable to load processed graph data.')
  }

  const [bundle, summary] = await Promise.all([
    bundleResponse.json() as Promise<GraphBundle>,
    summaryResponse.json() as Promise<GraphSummary>,
  ])

  return { bundle, summary }
}
