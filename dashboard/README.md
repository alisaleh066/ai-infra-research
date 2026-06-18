# Dashboard — unified research interface

A single Next.js + Tailwind site presenting all three projects under one institutional design
system. **Static-exported** (no server), so it deploys to GitHub Pages or Vercel as plain files.

## Why this stack
- **Next.js (static export)** — one `npm run build` produces a fully static `out/` that hosts
  anywhere; ideal for a public GitHub portfolio with zero infra.
- **Tailwind** — a single, consistent design system (deep navy/slate + one gold accent, Fraunces
  display serif + IBM Plex Sans/Mono) without a component library's generic look.
- **Client-side recompute** — the ROI simulator is ported to TypeScript (`lib/reSimulator.ts`,
  formula-for-formula identical to `real_estate/re_engine.py`) so reviewers flex drivers and see
  IRR move live, with no backend. Verified to match the Python engine to 4 dp.
- **JSON imported at build time** — the Python models write `public/data/*.json`; the dashboard
  imports them directly, so there is no fetch/CORS/basePath fragility in the static export.

## Views
- **Overview** — the three modules, each with a one-line thesis and headline stat.
- **01 Valuation** — football field, Monte Carlo distribution, WACC × terminal-growth heatmap,
  and the thesis-vs-portfolio panel (sample positions — no Trading212 MCP).
- **02 Bottleneck Map** — interactive tightness-by-layer panel (hover for sub-metrics) and the
  capital-migration chart.
- **03 Real Estate** — the live ROI simulator (a slider per demand/supply driver) and the
  exit-cap × rent-growth IRR heatmap.

## Run
```bash
cd dashboard
npm install
npm run dev      # http://localhost:3000
npm run build    # static export to ./out  (deploy to GitHub Pages / Vercel)
```
For a GitHub Pages project subpath, build with `NEXT_PUBLIC_BASE_PATH=/projectsf npm run build`.

## Data refresh
Re-run the Python builds (`python valuation/build.py`, `bottleneck_map/build.py`,
`real_estate/build.py`) to regenerate `public/data/*.json`, then rebuild the dashboard.

## Notes
- No browser-storage APIs are used.
- Fonts load from Google Fonts at runtime (build stays offline-friendly).
