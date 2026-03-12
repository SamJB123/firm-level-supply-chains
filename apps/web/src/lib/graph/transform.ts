import type {
  ConfidenceBand,
  FilterState,
  GraphBundle,
  GraphEdgeRecord,
  GraphNodeRecord,
  RelationType,
} from '../types'

export const COUNTRY_COLOR: Record<GraphNodeRecord['country'], string> = {
  AU: '#0f766e',
  CN: '#b91c1c',
  US: '#1d4ed8',
  OTHER: '#6b7280',
}

const CONFIDENCE_WIDTH: Record<ConfidenceBand, number> = {
  high: 2.8,
  medium: 1.9,
  low: 1.2,
}

export function createDefaultFilters(bundle: GraphBundle): FilterState {
  return {
    countries: [...new Set(bundle.nodes.map((node) => node.country))],
    relationTypes: [...new Set(bundle.edges.map((edge) => edge.relation_type))],
    confidenceBands: [...new Set(bundle.edges.map((edge) => edge.confidence))],
    sourceSystems: [...new Set(bundle.evidence.map((item) => item.source_system))],
    search: '',
    showCandidates: true,
    showPlaceholders: true,
  }
}

export function filterBundle(bundle: GraphBundle, filters: FilterState): GraphBundle {
  const matchingEvidenceIds = new Set(
    bundle.evidence
      .filter((item) => filters.sourceSystems.includes(item.source_system))
      .map((item) => item.evidence_id),
  )

  const edgeMatches = bundle.edges.filter((edge) => {
    const sourceNode = bundle.nodes.find((node) => node.id === edge.source)
    const targetNode = bundle.nodes.find((node) => node.id === edge.target)
    if (!sourceNode || !targetNode) {
      return false
    }
    const countries = [sourceNode.country, targetNode.country]
    const countryMatch = countries.some((country) => filters.countries.includes(country))
    const relationMatch = filters.relationTypes.includes(edge.relation_type)
    const confidenceMatch = filters.confidenceBands.includes(edge.confidence)
    const placeholderMatch = filters.showPlaceholders || edge.explicit
    const evidenceMatch = edge.evidence_ids.some((evidenceId) => matchingEvidenceIds.has(evidenceId))
    const searchTerm = filters.search.trim().toLowerCase()
    const searchMatch =
      searchTerm.length === 0 ||
      sourceNode.label.toLowerCase().includes(searchTerm) ||
      targetNode.label.toLowerCase().includes(searchTerm)
    return countryMatch && relationMatch && confidenceMatch && placeholderMatch && evidenceMatch && searchMatch
  })

  const visibleNodeIds = new Set(edgeMatches.flatMap((edge) => [edge.source, edge.target]))
  const candidateMatches = filters.showCandidates
    ? bundle.candidates.filter((candidate) => visibleNodeIds.has(candidate.undisclosed_entity_id))
    : []

  return {
    ...bundle,
    nodes: bundle.nodes.filter((node) => visibleNodeIds.has(node.id)),
    edges: edgeMatches,
    candidates: candidateMatches,
  }
}

export function getNodeColor(node: GraphNodeRecord): string {
  return COUNTRY_COLOR[node.country]
}

export function getNodeValue(node: GraphNodeRecord): number {
  return node.node_kind === 'placeholder' ? 3.2 : 6
}

export function getLinkColor(edge: GraphEdgeRecord): string {
  return edge.explicit ? '#64748b' : '#f59e0b'
}

export function getLinkWidth(edge: GraphEdgeRecord): number {
  return CONFIDENCE_WIDTH[edge.confidence]
}

export function getLinkParticleCount(edge: GraphEdgeRecord): number {
  return edge.explicit ? 2 : 1
}

export function getLinkArrowLength(edge: GraphEdgeRecord): number {
  return edge.explicit ? 4.5 : 3.2
}

export function collectAvailableRelationTypes(bundle: GraphBundle): RelationType[] {
  return [...new Set(bundle.edges.map((edge) => edge.relation_type))]
}

export function collectAvailableConfidenceBands(bundle: GraphBundle): ConfidenceBand[] {
  return [...new Set(bundle.edges.map((edge) => edge.confidence))]
}

export function collectSourceSystems(bundle: GraphBundle): string[] {
  return [...new Set(bundle.evidence.map((item) => item.source_system))]
}

export function findNode(bundle: GraphBundle, nodeId: string | null): GraphNodeRecord | null {
  if (!nodeId) {
    return null
  }
  return bundle.nodes.find((node) => node.id === nodeId) ?? null
}

export function findEdge(bundle: GraphBundle, edgeId: string | null): GraphEdgeRecord | null {
  if (!edgeId) {
    return null
  }
  return bundle.edges.find((edge) => edge.id === edgeId) ?? null
}
