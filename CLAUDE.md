# CLAUDE.md — `projectsf` working rules

> Repo-local rules for any AI agent working in this monorepo. Overrides global defaults
> where they conflict. Read this and `projects.md` before touching anything.

## What this repo is
A public, GitHub-facing portfolio: an **AI-Infrastructure & Real-Asset Investment Research
Platform**. Three rigorous sub-projects unified by one polished web dashboard. It is shown
to senior investment professionals (Blackstone et al.), so correctness, sourcing, and visual
polish are judged to an institutional standard.

## Golden rules
1. **Never fabricate a financial figure.** Every number is either fetched from a documented
   source or a clearly-labelled placeholder (`# ASSUMPTION:` in Python / `// ASSUMPTION:` in
   TS / BLUE font in Excel) surfaced in the UI and README as "input — replace with your figure."
2. **Sequential build.** Finish and verify Project 1 before 2, and 2 before 3. Each must
   self-score ≥ 8/10 against its Definition of Done (see `projects.md`) and pass all gates.
3. **Reproducible from a clean clone.** Pinned deps, cached data committed under `/data`,
   one documented command per stage. The repo runs offline after the first fetch.
4. **Tests for every non-trivial calc** (DCF, WACC, IRR, equity multiple, sensitivity grids,
   tightness scoring, ROI-simulator response). They must pass (`pytest -q`).
5. **Surgical changes.** Touch only what the task needs. No unrelated cleanup in a commit.

## Conventions
- **Python**: 3.12, snake_case, type hints on public functions, docstrings stating units.
  Each project has a `build.py` entry point that regenerates its artifacts into `output/`
  and `dashboard/public/data/`.
- **Excel** (`xlsx` skill): blue = inputs, black = formulas, dedicated **Assumptions** tab,
  units in every header, parentheses for negatives, **zero formula errors** (audited by the
  `model-auditor` skill).
- **TypeScript/Dashboard**: strict mode, no `any` without an inline reason. The DCF and ROI
  simulator recompute **client-side** from documented formulas so reviewers can flex inputs.
- **Commits**: conventional (`feat:`/`fix:`/`docs:`/`test:`/`refactor:`). Never push to anyone
  else's `main`. This is a standalone repo — work on a branch, commit checkpoints per project.

## Data provenance
- Market/fundamentals: SEC EDGAR + market-data MCPs (`edgartools`, `stocks`, `eodhd`,
  `finnhub`, `alpha-vantage`). UK property: HM Land Registry Price Paid + ONS.
- Every source and its retrieval date is logged in `DATA_SOURCES.md`. Cache raw pulls under
  `data/cache/` and commit tidy derived data so the repo is offline-reproducible.

## Self-check before marking a project done
- [ ] `python <project>/build.py` runs clean and writes artifacts
- [ ] `pytest -q` green for that project's tests
- [ ] `model-auditor` reports zero formula errors on any `.xlsx`
- [ ] module `README.md` complete (what / how / methodology / limitations / thesis)
- [ ] dashboard view renders from the committed JSON
- [ ] `PROGRESS.md` updated with the cycle result and self-score
