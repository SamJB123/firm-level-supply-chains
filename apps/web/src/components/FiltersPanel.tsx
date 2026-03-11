import type { Dispatch, SetStateAction } from 'react'

import type { ConfidenceBand, CountryCode, FilterState, GraphBundle, RelationType } from '../lib/types'
import {
  collectAvailableConfidenceBands,
  collectAvailableRelationTypes,
  collectSourceSystems,
} from '../lib/graph/transform'

interface FiltersPanelProps {
  bundle: GraphBundle
  filters: FilterState
  setFilters: Dispatch<SetStateAction<FilterState>>
}

export function FiltersPanel({ bundle, filters, setFilters }: FiltersPanelProps) {
  const countries = [...new Set(bundle.nodes.map((node) => node.country))]
  const relationTypes = collectAvailableRelationTypes(bundle)
  const confidenceBands = collectAvailableConfidenceBands(bundle)
  const sourceSystems = collectSourceSystems(bundle)

  return (
    <aside className="panel filters-panel">
      <div className="panel__header">
        <h2>Filters</h2>
        <p>Control the visible network and evidence set.</p>
      </div>

      <label className="field">
        <span>Search firms</span>
        <input
          type="search"
          value={filters.search}
          onChange={(event) =>
            setFilters((current) => ({
              ...current,
              search: event.target.value,
            }))
          }
          placeholder="Search by firm name"
        />
      </label>

      <FilterGroup<CountryCode>
        title="Countries"
        options={countries}
        selected={filters.countries}
        toggle={(value) => {
          setFilters((current) => ({
            ...current,
            countries: toggleValue(current.countries, value),
          }))
        }}
      />

      <FilterGroup<RelationType>
        title="Relation types"
        options={relationTypes}
        selected={filters.relationTypes}
        toggle={(value) => {
          setFilters((current) => ({
            ...current,
            relationTypes: toggleValue(current.relationTypes, value),
          }))
        }}
      />

      <FilterGroup<ConfidenceBand>
        title="Confidence"
        options={confidenceBands}
        selected={filters.confidenceBands}
        toggle={(value) => {
          setFilters((current) => ({
            ...current,
            confidenceBands: toggleValue(current.confidenceBands, value),
          }))
        }}
      />

      <FilterGroup<string>
        title="Sources"
        options={sourceSystems}
        selected={filters.sourceSystems}
        toggle={(value) => {
          setFilters((current) => ({
            ...current,
            sourceSystems: toggleValue(current.sourceSystems, value),
          }))
        }}
      />

      <div className="toggle-grid">
        <label>
          <input
            type="checkbox"
            checked={filters.showPlaceholders}
            onChange={() =>
              setFilters((current) => ({
                ...current,
                showPlaceholders: !current.showPlaceholders,
              }))
            }
          />
          Show undisclosed placeholders
        </label>
        <label>
          <input
            type="checkbox"
            checked={filters.showCandidates}
            onChange={() =>
              setFilters((current) => ({
                ...current,
                showCandidates: !current.showCandidates,
              }))
            }
          />
          Show ranked candidate hints
        </label>
      </div>
    </aside>
  )
}

interface FilterGroupProps<T extends string> {
  title: string
  options: T[]
  selected: T[]
  toggle: (value: T) => void
}

function FilterGroup<T extends string>({ title, options, selected, toggle }: FilterGroupProps<T>) {
  return (
    <section className="filter-group">
      <h3>{title}</h3>
      <div className="chip-grid">
        {options.map((option) => (
          <label key={option} className={`chip ${selected.includes(option) ? 'chip--active' : ''}`}>
            <input
              type="checkbox"
              checked={selected.includes(option)}
              onChange={() => toggle(option)}
            />
            <span>{option}</span>
          </label>
        ))}
      </div>
    </section>
  )
}

function toggleValue<T extends string>(values: T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value]
}
