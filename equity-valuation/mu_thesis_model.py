"""mu_thesis_model.py — a hand-built, thesis-driven DCF for Micron (MU).

Unlike value.py (which auto-derives assumptions for ANY ticker), this is the *analyst* model: a
deliberate base / bull / bear view of Micron through the HBM/DRAM cycle, with every driver chosen
and footnoted. Fundamentals are real (SEC EDGAR via data.py); the judgment is explicit.

Run:  python mu_thesis_model.py   ->  prints scenarios, writes output/MU_thesis.json
Reads alongside THESIS_MU.md.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import data as datamod
from valuation import DCFAssumptions, enterprise_value
from comps_live import comps_table

OUT = Path(__file__).resolve().parent / "output"
M = 1_000_000

# --------------------------------------------------------------------------- Scenarios
# Each scenario: 5-yr revenue growth path, 5-yr EBIT-margin path, capex % of revenue, terminal
# growth, and the discount rate. Footnotes (the "why") live in THESIS_MU.md.
SCENARIOS = {
    "Bear": {
        "prob": 0.25,
        "rev_growth": [0.05, -0.10, 0.06, 0.08, 0.06],   # memory oversupply returns ~FY27
        "ebit_margin": [0.22, 0.10, 0.14, 0.18, 0.20],   # margin collapses in the down-leg
        "capex_pct": 0.34,                               # capex stays high to defend share
        "terminal_growth": 0.020,
        "wacc": 0.125,
        "trigger": "DRAM/HBM oversupply by FY27: Samsung HBM3E qualifies at scale, hyperscaler "
                   "capex digestion, pricing rolls over.",
    },
    "Base": {
        "prob": 0.50,
        "rev_growth": [0.20, 0.10, 0.06, 0.05, 0.04],    # HBM ramp, then DRAM cycle normalises
        "ebit_margin": [0.30, 0.30, 0.27, 0.25, 0.24],   # peak-ish then fade to mid-cycle
        "capex_pct": 0.32,                               # elevated but productive
        "terminal_growth": 0.025,
        "wacc": 0.110,
        "trigger": "HBM stays tight into 2026, MU holds ~20-25% HBM share; DRAM cycle normalises "
                   "rather than crashes.",
    },
    "Bull": {
        "prob": 0.25,
        "rev_growth": [0.28, 0.16, 0.10, 0.07, 0.05],    # HBM scarcity persists, share gains
        "ebit_margin": [0.36, 0.37, 0.34, 0.31, 0.29],   # structurally higher mid-cycle margin
        "capex_pct": 0.31,
        "terminal_growth": 0.030,
        "wacc": 0.100,
        "trigger": "HBM remains the binding constraint through 2027; memory consolidates to a "
                   "3-player rational oligopoly; AI memory content/box keeps rising.",
    },
}


def base_inputs() -> dict:
    f = datamod.fetch_fundamentals("MU")
    yrs = f["years"]

    def latest(s):
        for y in reversed(yrs):
            if s.get(y) is not None:
                return s[y]
        return None

    rev = latest(f["revenue"]) / M
    da = (latest(f["da"]) or 0) / M
    cash = (latest(f["cash"]) or 0) / M
    debt = ((latest(f["long_term_debt"]) or 0) + (latest(f["short_term_debt"]) or 0)) / M
    shares = (latest(f["shares"]) or 0) / M
    return {"name": f["name"], "years": yrs, "rev": rev, "da_pct": round(da / rev, 4),
            "cash": cash, "debt": debt, "shares": shares}


def run() -> dict:
    OUT.mkdir(exist_ok=True)
    b = base_inputs()
    p = datamod.fetch_price("MU")
    price = p["price"]

    results = {}
    weighted = 0.0
    for name, sc in SCENARIOS.items():
        a = DCFAssumptions(
            base_revenue=b["rev"], rev_growth=sc["rev_growth"], ebit_margin=sc["ebit_margin"],
            tax_rate=0.13, da_pct_rev=b["da_pct"], capex_pct_rev=sc["capex_pct"],
            nwc_pct_rev_change=0.08, terminal_growth=sc["terminal_growth"],
            risk_free=0.043, erp=0.05, beta=1.3, pretax_kd=0.05,
            equity_value=(price * b["shares"]) if price else b["rev"] * 3,
            debt_value=b["debt"], cash=b["cash"], shares=b["shares"],
        )
        dcf = enterprise_value(a, wacc_rate=sc["wacc"])
        fv = dcf["value_per_share"]
        results[name] = {"prob": sc["prob"], "wacc": sc["wacc"],
                         "terminal_growth": sc["terminal_growth"],
                         "fair_value": round(fv, 2), "trigger": sc["trigger"],
                         "rev_growth": sc["rev_growth"], "ebit_margin": sc["ebit_margin"],
                         "capex_pct": sc["capex_pct"]}
        weighted += sc["prob"] * fv

    comps = comps_table("MU")
    out = {
        "company": b["name"], "ticker": "MU", "fiscal_years": b["years"],
        "base_revenue_m": round(b["rev"], 0), "shares_m": round(b["shares"], 0),
        "net_debt_m": round(b["debt"] - b["cash"], 0),
        "price_at_run": price,
        "scenarios": results,
        "probability_weighted_fair_value": round(weighted, 2),
        "comps_live": {"median_ev_ebitda": comps["median_ev_ebitda"],
                       "median_pe": comps["median_pe"], "n": comps["n_valid"],
                       "note": "Live peer medians; sanity-check the price feed before quoting."},
        "method": "Hand-built scenario DCF on real EDGAR fundamentals. Drivers are explicit "
                  "analyst judgment (see THESIS_MU.md). Fair value is price-independent.",
    }
    (OUT / "MU_thesis.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"{b['name']} (MU) — hand-built scenario DCF   base revenue ${b['rev']:,.0f}m, "
          f"{b['shares']:,.0f}m shares")
    print(f"{'Scenario':<8}{'Prob':>6}{'WACC':>7}{'FairValue':>12}   trigger")
    for n, r in results.items():
        print(f"{n:<8}{r['prob']:>6.0%}{r['wacc']:>7.1%}   ${r['fair_value']:>8,.2f}   {r['trigger'][:60]}...")
    print(f"\nProbability-weighted fair value: ${out['probability_weighted_fair_value']:,.2f}")
    if price:
        print(f"Price at run: ${price:,.2f}  (verify the live feed; sandbox prices may be off)")
    print(f"Live comps median EV/EBITDA {comps['median_ev_ebitda']}x, P/E {comps['median_pe']}x")
    print(f"Wrote: {OUT/'MU_thesis.json'}")
    return out


if __name__ == "__main__":
    run()
