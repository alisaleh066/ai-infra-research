# ai-infra-research

Three independent investment-analysis tools: `equity-valuation/` (DCF, comps, Monte Carlo on SEC EDGAR data), `ai-bottleneck-map/`, `real-estate-roi/`. Windows + Anaconda; no API keys needed.

## Commands
Each tool has its own README, launchers (`*.bat`) and tests. CI: `.github/workflows/tests.yml`. Read the tool's README before running anything.

## Rules
- Keep the three tools independent; do not share code between them.
- Analysis output is not investment advice. Do not place or suggest trades.
- Free data only. No secrets committed.
