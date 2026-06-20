# AI-Infrastructure Bottleneck Map

Scores the AI supply chain (GPUs → HBM → advanced packaging/CoWoS → leading-edge foundry → power
& grid → copper → uranium) on a transparent **tightness** metric, identifies the **binding
constraint**, and shows where **capital migrates** over time.

## Quick start (Windows)
1. Double-click **`setup.bat`** once.
2. Double-click **`run.bat`** → prints the tightness ranking + binding constraint, writes
   `output/bottleneck.json`.
3. Optional web app: double-click **`app.bat`** (adjust the metric weights live).

## Commands (PATH-independent; PowerShell run one line at a time)
```powershell
& "$env:USERPROFILE\anaconda3\python.exe" -m pip install -r requirements.txt
& "$env:USERPROFILE\anaconda3\python.exe" build.py
& "$env:USERPROFILE\anaconda3\python.exe" -m pytest -q
```

## Method
Tightness = 100 · Σ wᵢ·mᵢ over four sub-metrics, each normalised to [0,1] (higher = tighter):
utilisation (0.30), lead time (0.25), supply inelasticity (0.25), concentration (0.20). Weights
are explicit and editable (`scoring.py` / the app sidebar). With the default weights the binding
constraint is **advanced packaging (CoWoS)** — consistent with reported CoWoS capacity gating
accelerator shipments.

## Investability layer (links to the equity project)
`investability.py` maps each layer to investable US-listed tickers, tightest first, and — with
`--quality` — pulls a live fundamental snapshot (ROIC vs hurdle, Piotroski F-Score, quality rating)
from the sibling `equity-valuation` project, so the map becomes actionable:
```powershell
& "$env:USERPROFILE\anaconda3\python.exe" investability.py            # mapping only
& "$env:USERPROFILE\anaconda3\python.exe" investability.py --quality  # + live fundamentals
```
Foreign leaders that file 20-F (e.g. TSMC, Cameco) show `n/a` on the 10-K-based fundamentals —
flagged, never faked. Also surfaced in the web app.

## Files
- `scoring.py` — pure, tested tightness engine.
- `layers.json` — the 7 layers + curated sub-metrics + capital-flow series (provenance tagged).
- `build.py` — scores and writes `output/bottleneck.json`.
- `app.py` — Streamlit UI.

## Honesty / limitations
Sub-metric levels are **curated estimates** from public earnings/industry commentary (tagged
`curated`); the capital-flow series is **illustrative** (tagged `illustrative`), not audited capex.
The method is the deliverable — swap in measured inputs to harden the numbers. Not investment advice.
