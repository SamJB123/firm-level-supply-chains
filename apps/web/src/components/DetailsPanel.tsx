import type { GraphBundle, GraphEdgeRecord, GraphNodeRecord } from '../lib/types'

interface DetailsPanelProps {
  bundle: GraphBundle
  selectedNode: GraphNodeRecord | null
  selectedEdge: GraphEdgeRecord | null
}

export function DetailsPanel({ bundle, selectedNode, selectedEdge }: DetailsPanelProps) {
  const nodeMap = new Map(bundle.nodes.map((node) => [node.id, node]))

  if (selectedEdge) {
    const source = nodeMap.get(selectedEdge.source)
    const target = nodeMap.get(selectedEdge.target)
    const evidence = bundle.evidence.filter((item) => selectedEdge.evidence_ids.includes(item.evidence_id))

    return (
      <aside className="panel details-panel">
        <div className="panel__header">
          <h2>Selected link</h2>
          <p>
            {source?.label} → {target?.label}
          </p>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Relation</dt>
            <dd>{selectedEdge.relation_type}</dd>
          </div>
          <div>
            <dt>Confidence</dt>
            <dd>{selectedEdge.confidence}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{selectedEdge.explicit ? 'Confirmed' : 'Undisclosed / inferred context'}</dd>
          </div>
        </dl>
        <section>
          <h3>Evidence</h3>
          <ul className="evidence-list">
            {evidence.map((item) => (
              <li key={item.evidence_id}>
                <strong>{item.document_title}</strong>
                <p>{item.excerpt}</p>
                <div className="evidence-meta">
                  <span>{item.source_system}</span>
                  {item.filing_year ? <span>{item.filing_year}</span> : null}
                  {item.download_url ? (
                    <a href={item.download_url} target="_blank" rel="noreferrer">
                      Source
                    </a>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        </section>
      </aside>
    )
  }

  if (selectedNode) {
    const linkedEdges = bundle.edges.filter(
      (edge) => edge.source === selectedNode.id || edge.target === selectedNode.id,
    )
    const candidates = bundle.candidates.filter(
      (candidate) =>
        candidate.undisclosed_entity_id === selectedNode.id ||
        candidate.candidate_entity_id === selectedNode.id,
    )

    return (
      <aside className="panel details-panel">
        <div className="panel__header">
          <h2>{selectedNode.label}</h2>
          <p>{selectedNode.node_kind === 'placeholder' ? 'Undisclosed placeholder' : 'Firm node'}</p>
        </div>
        <dl className="detail-grid">
          <div>
            <dt>Country</dt>
            <dd>{selectedNode.country}</dd>
          </div>
          <div>
            <dt>Linked edges</dt>
            <dd>{linkedEdges.length}</dd>
          </div>
          <div>
            <dt>Candidate links</dt>
            <dd>{candidates.length}</dd>
          </div>
        </dl>

        {candidates.length > 0 ? (
          <section>
            <h3>Candidate possibilities</h3>
            <ul className="candidate-list">
              {candidates.map((candidate) => (
                <li key={candidate.candidate_link_id}>
                  <strong>
                    #{candidate.rank} {nodeMap.get(candidate.candidate_entity_id)?.label ?? candidate.candidate_entity_id}
                  </strong>
                  <p>{candidate.rationale}</p>
                  <span className="candidate-badge">{candidate.confidence}</span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <section>
          <h3>Source manifest</h3>
          <div className="source-manifest">
            {Object.entries(bundle.sources).map(([country, items]) => (
              <div key={country}>
                <strong>{country}</strong>
                <ul>
                  {items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      </aside>
    )
  }

  return (
    <aside className="panel details-panel">
      <div className="panel__header">
        <h2>Details</h2>
        <p>Select a node or edge to inspect provenance.</p>
      </div>
      <p className="muted">
        Confirmed named links, undisclosed placeholders, and ranked candidate hints are intentionally separated.
      </p>
    </aside>
  )
}
