# Firm-level supply chain links visualization

This repository builds a static, evidence-backed visualization of firm-level supply-chain links across:

- Australia
- China
- United States

It combines a Python ingestion / normalization pipeline with a React web app.

## What the project does

The pipeline:

1. builds a seed universe of the 20 largest listed firms by market capitalization in each country
2. downloads real public-source documents
3. extracts named and undisclosed supply-chain evidence
4. normalizes evidence into graph nodes and edges
5. exports a static graph bundle for the web application

The web app renders:

- confirmed named links
- undisclosed supplier / customer placeholder links
- per-edge provenance
- country and confidence filters
- a source manifest showing which public datasets feed each country

## Source families

### Australia

- Modern Slavery Statements Register
- public annual-report / announcement PDFs where available
- ABN / ABR enrichment support in the pipeline design

### China

- CNINFO annual report metadata search
- CNINFO annual report PDFs

### United States

- SEC EDGAR submissions metadata
- SEC filing HTML documents
- SEC XBRL / CompanyFacts supporting sources where useful

## Repository layout

```text
apps/web/                  React + TanStack Router visualization
pipeline/                  Python ingestion and normalization pipeline
config/                    Seed universe and manual entity overrides
data/raw/                  Downloaded source documents (gitignored)
data/intermediate/         Intermediate manifests / parser outputs (gitignored)
data/processed/demo/       Processed demo graph tables and JSON
```

## Setup

### JavaScript

```sh
pnpm install
```

### Python

```sh
python3 -m pip install -e "./pipeline[dev]"
```

## Main commands

### Generate the top-20 seed universe

```sh
python3 -m supply_chain.cli generate-seeds --limit 20
```

This writes:

- `config/seed_companies.csv`
- `config/entity_overrides.csv`

### Fetch documents for one country

Examples:

```sh
python3 -m supply_chain.cli fetch --country AU --limit 3
python3 -m supply_chain.cli fetch --country CN --selector BYD --limit 1 --years-back 3
python3 -m supply_chain.cli fetch --country US --selector NVIDIA,Tesla --limit 2 --years-back 3
```

### Build the demo dataset

```sh
python3 -m supply_chain.cli build-demo --seed-limit 20 --years-back 3
```

This produces:

- `data/processed/demo/graph.json`
- `data/processed/demo/summary.json`
- `data/processed/demo/*.csv`
- `data/processed/demo/*.parquet`
- `apps/web/public/data/graph.json`
- `apps/web/public/data/summary.json`

## Run the web app

```sh
pnpm dev
```

Build:

```sh
pnpm build
```

## Testing

### Pipeline tests

```sh
python3 -m pytest pipeline/tests
```

### Web tests

```sh
pnpm --filter web test
pnpm --filter web lint
pnpm --filter web build
```

## Current demo behavior

The committed demo dataset is built from real downloaded documents and currently emphasizes:

- Australian modern slavery statement placeholder links
- Chinese top-5 supplier / customer disclosures where counterparties are masked
- US named supplier links from SEC filings plus unnamed major-customer placeholders

The present demo intentionally distinguishes:

- **confirmed named links** — e.g. TSMC → NVIDIA, CATL → Tesla
- **undisclosed placeholders** — e.g. BYD → Undisclosed Customer

## Important limitations

- Australia and China often disclose supply-chain evidence in narrative or masked form, so undisclosed placeholders are common.
- CNINFO annual reports may mask top suppliers / customers as `客户一`, `供应商一`, etc.
- US XBRL does not consistently provide named counterparties; named relationships often come from filing narrative rather than structured facts.
- Candidate inference support exists in the pipeline design, but candidate output depends on cross-document corroboration in the downloaded corpus.

## Notes on reproducibility

- Raw downloaded documents are intentionally excluded from git.
- The committed graph bundle under `apps/web/public/data/` is generated from real downloaded-source material.
- Re-running the pipeline will reuse cached downloaded files when present.
