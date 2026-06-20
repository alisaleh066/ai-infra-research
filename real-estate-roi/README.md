# Real-Estate ROI — institutional underwriting + LP/GP waterfall

Underwrites a real-estate deal the way an institutional sponsor (Blackstone / BlackRock-style)
does, and splits the return between **LP (investors)** and **GP (sponsor)** through an **equity
waterfall** with a **preferred return** and **promote (carried interest)** tiers.

## Quick start (Windows)
1. Double-click **`setup.bat`** once.
2. Double-click **`run.bat`** (uses `deal.sample.json`), or `run.bat mydeal.json`.
3. Optional web app with sliders: double-click **`app.bat`**.

Outputs: `output/<name>_roi.json` and `output/deal_underwriting.xlsx`.

## Commands (PATH-independent; PowerShell one line at a time)
```powershell
& "$env:USERPROFILE\anaconda3\python.exe" -m pip install -r requirements.txt
& "$env:USERPROFILE\anaconda3\python.exe" roi.py
& "$env:USERPROFILE\anaconda3\python.exe" -m pytest -q
```

## The techniques (what these firms actually use)
- **Value-add lifecycle** (`underwrite.py`): acquire at a going-in cap → spend renovation capex →
  ramp NOI to a stabilized level → hold → exit at an exit cap. Interest-only debt.
- **Return metrics:** project **IRR**, **equity multiple (MOIC)**, **cash-on-cash**, **DSCR**,
  **debt yield**, **LTV / LTC**.
- **Equity waterfall** (`waterfall.py`) — the signature structure:
  1. **Return of capital + preferred return** (default 8%) → 100% to LP.
  2. **Promote tiers by IRR hurdle** (8–12% → GP 20%, 12–15% → 30%, >15% → 40%) → the GP's
     carried interest. Reports **LP IRR**, **GP promote $**, GP **share of profit**, and the
     **promote drag** (project IRR − LP IRR).
- **Debt options:** interest-only or **amortising** (`amortization_years`), plus an optional
  **mid-hold cash-out refinance** (`refinance_year`) that sizes a new loan on the stabilised value
  and returns capital early — how value-add sponsors actually juice IRR.
- **Two-way sensitivity** (exit cap × NOI uplift), a **downside stress** scenario, and a
  **Monte Carlo** on rent growth / exit cap / interest rate → the distribution of LP IRR and the
  **probability of clearing the preferred return**.

Each IRR hurdle keeps an LP capital account compounding at that rate; a distribution counts toward
a hurdle only by the LP portion it pays. When the account hits zero, the LP has achieved that IRR
and the next (higher-promote) band begins. GP co-invest = 0 by default (earns only promote).

## Configure a deal
Edit `deal.sample.json` (or copy it). `waterfall_tiers` is a list of `[IRR hurdle, GP promote
above it]`. Below the first hurdle the LP gets 100% (capital + preferred return).

## Verify
```powershell
& "$env:USERPROFILE\anaconda3\python.exe" -m pytest -q          # 12 tests: conservation, promote behaviour, IRR
& "$env:USERPROFILE\anaconda3\python.exe" xlsx_check.py output\deal_underwriting.xlsx
```
Tests prove the waterfall **conserves cash** (LP + GP = total every period), pays **no promote
below the pref**, and that the **GP share rises with returns**. The Excel reconciles to the Python
engine under a real recalculation. Not investment advice.
