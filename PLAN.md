# PLAN.md — execution plan

## Goal (restated)
Build one runnable repo with three rigorous, sequentially-built investment-research
sub-projects unified by a polished web dashboard, to an institutional standard, for a public
GitHub portfolio. Finish + verify each project (self-score ≥ 8/10 + gates pass) before the next.

## Sequential project order
1. **Project 1 — Equity Valuation Engine (MU)** — fastest path to a provably-real artifact.
2. **Project 2 — Bottleneck Map** — the visual hero.
3. **Project 3 — UK Real-Estate Underwriting + ROI Simulator.**
Then integrate all three into the dashboard and finalise docs.

## Per-project loop (repeat until ≥8/10 AND gates pass)
`PLAN → BUILD → VERIFY → CRITIQUE → REFINE → re-VERIFY`, updating `PROGRESS.md` each cycle.
On ambiguity: document a labelled assumption, flag it, continue — never stall.

## Work breakdown (roles, run inline or as subagents)
- **Data** — fetch + cache via the `financial-data-fetcher` / `uk-property-data` skills.
- **Model** — Python calc engines + Excel builders (`xlsx` skill).
- **Front-end** — Next.js + Tailwind views (`frontend-design` skill).
- **QA / Verifier** — runs everything from a clean state, runs `model-auditor` + `pytest`,
  empowered to send work back. Enforces the engineering gates.

## Milestones
- **M0** Scaffold + core docs + 3 custom skills + shared design tokens.   ← in progress
- **M1** Project 1 complete, ≥8/10, gates pass, checkpoint commit.
- **M2** Project 2 complete, ≥8/10, gates pass, checkpoint commit.
- **M3** Project 3 complete, ≥8/10, gates pass, checkpoint commit.
- **M4** Dashboard integration, root README + CONCLUSIONS.md, screenshots, final self-scores.

## Engineering gates (Verifier enforces before advancing)
- Tests for every non-trivial calc pass (`pytest -q`).
- Zero spreadsheet formula errors (`model-auditor`).
- Lint clean, pinned deps, reproducible from fresh clone.
- Each module README complete; root README has overview + architecture + run instructions.
- No fabricated figures — placeholders labelled and surfaced.

## Per-module Definition of Done
See `projects.md` (each project lists its own DoD ≥8/10 criteria).
