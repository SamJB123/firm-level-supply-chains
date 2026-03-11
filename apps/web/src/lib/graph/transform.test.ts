import { describe, expect, it } from 'vitest'

import { createDefaultFilters, filterBundle } from './transform'
import type { GraphBundle } from '../types'

const bundle: GraphBundle = {
  nodes: [
    { id: 'au-1', label: 'BHP Group', country: 'AU', node_kind: 'company', aliases: [], source_ids: {} },
    { id: 'us-1', label: 'NVIDIA', country: 'US', node_kind: 'company', aliases: [], source_ids: {} },
    {
      id: 'ph-1',
      label: 'Undisclosed Supplier',
      country: 'OTHER',
      node_kind: 'placeholder',
      aliases: [],
      source_ids: {},
    },
  ],
  edges: [
    {
      id: 'edge-1',
      source: 'au-1',
      target: 'us-1',
      relation_type: 'supplier',
      confidence: 'medium',
      explicit: true,
      evidence_ids: ['ev-1'],
    },
    {
      id: 'edge-2',
      source: 'ph-1',
      target: 'au-1',
      relation_type: 'undisclosed_supplier',
      confidence: 'low',
      explicit: false,
      evidence_ids: ['ev-2'],
    },
  ],
  evidence: [
    {
      evidence_id: 'ev-1',
      country: 'US',
      relation_type: 'supplier',
      reporter_name: 'NVIDIA',
      counterparty_name: 'BHP Group',
      confidence: 'medium',
      source_system: 'SEC EDGAR',
      document_id: 'doc-1',
      document_title: '10-K',
      excerpt: 'excerpt',
      page_reference: '',
      filing_year: 2025,
      amount_text: '',
      percentage_text: '',
      parser_method: 'sec_supplier_regex',
      named_counterparty: true,
      download_url: '',
      local_path: '',
    },
    {
      evidence_id: 'ev-2',
      country: 'AU',
      relation_type: 'undisclosed_supplier',
      reporter_name: 'BHP Group',
      counterparty_name: 'Undisclosed Supplier',
      confidence: 'low',
      source_system: 'Modern Slavery Statements Register',
      document_id: 'doc-2',
      document_title: 'Statement',
      excerpt: 'excerpt',
      page_reference: '',
      filing_year: 2025,
      amount_text: '',
      percentage_text: '',
      parser_method: 'modern_slavery_placeholder',
      named_counterparty: false,
      download_url: '',
      local_path: '',
    },
  ],
  candidates: [
    {
      candidate_link_id: 'cand-1',
      undisclosed_entity_id: 'ph-1',
      candidate_entity_id: 'us-1',
      rank: 1,
      confidence: 'low',
      rationale: 'Other evidence points to NVIDIA',
      supporting_evidence_ids: ['ev-1'],
    },
  ],
  sources: {
    AU: ['Modern Slavery Statements Register'],
    CN: ['CNINFO'],
    US: ['SEC EDGAR'],
  },
}

describe('filterBundle', () => {
  it('removes placeholder edges when placeholders are disabled', () => {
    const filters = createDefaultFilters(bundle)
    filters.showPlaceholders = false

    const filtered = filterBundle(bundle, filters)

    expect(filtered.edges).toHaveLength(1)
    expect(filtered.edges[0].id).toBe('edge-1')
  })
})
