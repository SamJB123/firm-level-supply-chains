export type CountryCode = 'AU' | 'CN' | 'US' | 'OTHER'

export type RelationType =
  | 'supplier'
  | 'customer'
  | 'partner'
  | 'undisclosed_supplier'
  | 'undisclosed_customer'

export type ConfidenceBand = 'high' | 'medium' | 'low'

export type NodeKind = 'company' | 'placeholder'

export interface GraphNodeRecord {
  id: string
  label: string
  country: CountryCode
  node_kind: NodeKind
  aliases: string[]
  source_ids: Record<string, string>
}

export interface GraphEdgeRecord {
  id: string
  source: string
  target: string
  relation_type: RelationType
  confidence: ConfidenceBand
  explicit: boolean
  evidence_ids: string[]
}

export interface EvidenceRecord {
  evidence_id: string
  country: CountryCode
  relation_type: RelationType
  reporter_name: string
  counterparty_name: string
  counterparty_country?: CountryCode | null
  confidence: ConfidenceBand
  source_system: string
  document_id: string
  document_title: string
  excerpt: string
  page_reference: string
  filing_year?: number | null
  amount_text: string
  percentage_text: string
  parser_method: string
  named_counterparty: boolean
  download_url: string
  local_path: string
}

export interface CandidateLinkRecord {
  candidate_link_id: string
  undisclosed_entity_id: string
  candidate_entity_id: string
  rank: number
  confidence: ConfidenceBand
  rationale: string
  supporting_evidence_ids: string[]
}

export interface GraphBundle {
  nodes: GraphNodeRecord[]
  edges: GraphEdgeRecord[]
  evidence: EvidenceRecord[]
  candidates: CandidateLinkRecord[]
  sources: Record<string, string[]>
}

export interface GraphSummary {
  nodeCount: number
  edgeCount: number
  evidenceCount: number
  candidateCount: number
  explicitEdgeCount: number
  placeholderEdgeCount: number
  sources: Record<string, string[]>
  countries: CountryCode[]
}

export interface FilterState {
  countries: CountryCode[]
  relationTypes: RelationType[]
  confidenceBands: ConfidenceBand[]
  sourceSystems: string[]
  search: string
  showCandidates: boolean
  showPlaceholders: boolean
}
