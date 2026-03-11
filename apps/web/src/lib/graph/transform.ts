import Graph from 'graphology'

import type {
  ConfidenceBand,
  FilterState,
  GraphBundle,
  GraphEdgeRecord,
  GraphNodeRecord,
  RelationType,
} from '../types'

const COUNTRY_COLOR: Record<GraphNodeRecord['country'], string> = {
  AU: '#0f766e',
  CN: '#b91c1c',
  US: '#1d4ed8',
  OTHER: '#6b7280',
}

const CONFIDENCE_SIZE: Record<ConfidenceBand, number> = {
  high: 8,
  medium: 6,
  low: 5,
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

export function buildSigmaGraph(bundle: GraphBundle): Graph {
  const graph = new Graph()
  const countries = [...new Set(bundle.nodes.map((node) => node.country))]
  const grouped = new Map(countries.map((country, index) => [country, { index, nodes: bundle.nodes.filter((node) => node.country === country) }]))

  grouped.forEach(({ index, nodes }, country) => {
    const centerX = (index - (countries.length - 1) / 2) * 4
    const centerY = 0
    nodes.forEach((node, nodeIndex) => {
      const angle = (Math.PI * 2 * nodeIndex) / Math.max(nodes.length, 1)
      const radius = 1.8 + nodeIndex * 0.08
      graph.addNode(node.id, {
        label: node.label,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        size: node.node_kind === 'placeholder' ? 8 : 12,
        color: COUNTRY_COLOR[country],
      })
    })
  })

  bundle.edges.forEach((edge) => {
    if (!graph.hasNode(edge.source) || !graph.hasNode(edge.target)) {
      return
    }
    graph.addEdgeWithKey(edge.id, edge.source, edge.target, {
      label: edge.relation_type,
      size: CONFIDENCE_SIZE[edge.confidence],
      color: edge.explicit ? '#475569' : '#f59e0b',
      type: 'arrow',
    })
  })

  return graph
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
