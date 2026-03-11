export function Legend() {
  return (
    <section className="panel legend-panel">
      <div className="panel__header">
        <h2>Legend</h2>
      </div>
      <ul className="legend-list">
        <li>
          <span className="legend-swatch legend-swatch--au" />
          Australia
        </li>
        <li>
          <span className="legend-swatch legend-swatch--cn" />
          China
        </li>
        <li>
          <span className="legend-swatch legend-swatch--us" />
          United States
        </li>
        <li>
          <span className="legend-line legend-line--explicit" />
          Explicit named link
        </li>
        <li>
          <span className="legend-line legend-line--placeholder" />
          Undisclosed placeholder
        </li>
      </ul>
    </section>
  )
}
