import type { GraphBundle, GraphSummary } from '../types'
import { dataManifest } from '../generated/dataManifest'

export async function loadGraphData(): Promise<{
  bundle: GraphBundle
  summary: GraphSummary
}> {
  const [bundleResponse, summaryResponse] = await Promise.all([
    fetch(dataManifest.graphPath),
    fetch(dataManifest.summaryPath),
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
