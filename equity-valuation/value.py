"""value.py — value ANY US-listed stock from live data.

Usage:
    python value.py MU
    python value.py AAPL --price 250        # override the fetched price

Fetches audited fundamentals (SEC EDGAR) + live price (Yahoo), derives transparent DCF
assumptions from the company's own history, runs DCF + comps + Monte Carlo, prints a summary, and
writes output/<TICKER>_valuation.{xlsx,json} + output/<TICKER>_montecarlo.png.

All monetary figures are handled in USD millions. Every derived assumption is editable in the
Excel 'Assumptions' tab and listed in the JSON. Nothing is fabricated: data the filing doesn't
provide is flagged.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import data as datamod
from valuation import (
    DCFAssumptions, MonteCarloSpec, comps_valuation, enterprise_value, monte_carlo,
    sensitivity_grid,
)
import build_xlsx

OUT = Path(__file__).resolve().parent / "output"
M = 1_000_000  # work in USD millions


def _latest(series: dict, years: list[int]):
    for y in reversed(years):
        v = series.get(y)
        if v is not None:
            return v, y
    return None, None


def _hist_cagr(series: dict, years: list[int]) -> float | None:
    vals = [series.get(y) for y in years if series.get(y) is not None and series.get(y) > 0]
    if len(vals) < 2:
        return None
    n = len(vals) - 1
    return (vals[-1] / vals[0]) ** (1 / n) - 1


def _wavg(num: dict, den: dict, years: list[int]) -> float | None:
    """Revenue-weighted average of num/den over years (smooths cyclicality)."""
    ns, ds = [], []
    for y in years:
        n, d = num.get(y), den.get(y)
        if n is not None and d:
            ns.append(n); ds.append(d)
    return (sum(ns) / sum(ds)) if ds else None


def compute_beta(stock_hist, market_hist) -> float | None:
    """Beta from overlapping daily returns vs the market (SPY)."""
    import numpy as np
    sd = dict(stock_hist)
    md = dict(market_hist)
    dates = sorted(set(sd) & set(md))
    if len(dates) < 60:
        return None
    s = np.array([sd[d] for d in dates])
    m = np.array([md[d] for d in dates])
    sr = np.diff(s) / s[:-1]
    mr = np.diff(m) / m[:-1]
    var = float(np.var(mr))
    if var == 0:
        return None
    beta = float(np.cov(sr, mr)[0, 1] / var)
    return round(beta, 3)


def build_assumptions(fund: dict, price: float | None, beta: float | None) -> tuple[DCFAssumptions, dict]:
    """Derive transparent DCF assumptions from the company's own history (all flagged)."""
    years = fund["years"]
    rev, ry = _latest(fund["revenue"], years)
    opinc, _ = _latest(fund["operating_income"], years)
    da, _ = _latest(fund["da"], years)
    capex, _ = _latest(fund["capex"], years)
    cash, _ = _latest(fund["cash"], years)
    ltd, _ = _latest(fund["long_term_debt"], years)
    std, _ = _latest(fund["short_term_debt"], years)
    shares, _ = _latest(fund["shares"], years)

    notes: list[str] = []

    def need(v, name, default):
        if v is None:
            notes.append(f"{name} missing → assumption {default}")
            return default
        return v

    rev = need(rev, "revenue", 0) / M
    cash = need(cash, "cash", 0) / M
    debt = (need(ltd, "long_term_debt", 0) + (std or 0)) / M
    shares = need(shares, "shares", None) or 0
    shares_m = shares / M if shares else None
    if not shares_m:
        notes.append("shares missing -> cannot compute per-share; defaulting to 1")
        shares_m = 1.0

    # Revenue-weighted historical averages smooth out the cycle (vs a single spot year).
    margin_avg = _wavg(fund["operating_income"], fund["revenue"], years)
    da_avg = _wavg(fund["da"], fund["revenue"], years)
    capex_avg = _wavg({y: abs(v) for y, v in fund["capex"].items() if v is not None},
                      fund["revenue"], years)
    if margin_avg is None:
        margin_avg = 0.12; notes.append("EBIT margin unavailable -> assumption 12%")
    if da_avg is None:
        da_avg = 0.05; notes.append("D&A unavailable -> assumption 5% of revenue")
    if capex_avg is None:
        capex_avg = da_avg; notes.append("capex unavailable -> assumed = D&A (maintenance)")
    ebit_margin = max(min(margin_avg, 0.6), -0.1)
    da_pct = round(da_avg, 4)
    # Capex mean-reverts toward maintenance (~D&A) in steady state; blend avoids a peak-capex
    # build-out year permanently crushing FCFF for capital-intensive cyclicals.
    capex_pct = round((capex_avg + da_avg) / 2, 4)

    # growth: historical CAGR, clamped, fading to terminal over 5 years
    cagr = _hist_cagr(fund["revenue"], years)
    if cagr is None:
        cagr = 0.05
        notes.append("revenue CAGR unavailable -> assumption 5%")
    g0 = max(min(cagr, 0.30), -0.05)
    terminal_growth = 0.025
    rev_growth = [round(g0 + (terminal_growth - g0) * i / 4, 4) for i in range(5)]
    margins = [round(ebit_margin, 4)] * 5

    if beta is None:
        beta = 1.10
        notes.append("beta unavailable -> assumption 1.10")
    beta = max(0.5, min(beta, 2.0))  # clamp to avoid extreme WACC from a noisy spot beta
    if price is None:
        notes.append("price unavailable -> equity weight uses assumption; no upside vs market")

    equity_value = (price * shares_m) if price else (rev * 2)  # crude fallback for WACC weight
    a = DCFAssumptions(
        base_revenue=rev,
        rev_growth=rev_growth,
        ebit_margin=margins,
        tax_rate=0.21,                 # US statutory (ASSUMPTION)
        da_pct_rev=da_pct,
        capex_pct_rev=capex_pct,
        nwc_pct_rev_change=0.05,       # ASSUMPTION
        terminal_growth=terminal_growth,
        risk_free=0.043,               # ASSUMPTION
        erp=0.050,                     # ASSUMPTION
        beta=beta,
        pretax_kd=0.05,                # ASSUMPTION
        equity_value=equity_value,
        debt_value=debt,
        cash=cash,
        shares=shares_m,
    )
    # EBITDA from the latest fiscal year (in $m) for comps
    opinc_l, _ = _latest(fund["operating_income"], years)
    da_l, _ = _latest(fund["da"], years)
    ebitda_m = ((opinc_l or 0) + (da_l or 0)) / M
    extras = {"ebitda": ebitda_m, "eps": _latest(fund["eps_diluted"], years)[0],
              "net_debt": debt - cash, "notes": notes, "last_fy": ry}
    return a, extras


def scenario_band(a: DCFAssumptions, base_wacc: float) -> dict:
    """Bear / Base / Bull fair values by shifting the key drivers around the base case.

    Generic, transparent deltas (an analyst replaces these with named, defended drivers per name —
    see mu_thesis_model.py for the worked example). Headline alongside Monte Carlo.
    """
    cases = {
        "Bear": {"g": -0.03, "m": -0.04, "w": +0.015, "tg": -0.005,
                 "trigger": "demand air-pocket / margin compression / multiple de-rate"},
        "Base": {"g": 0.0, "m": 0.0, "w": 0.0, "tg": 0.0,
                 "trigger": "current trajectory holds"},
        "Bull": {"g": +0.03, "m": +0.03, "w": -0.010, "tg": +0.005,
                 "trigger": "demand stays tight / margins expand / lower risk premium"},
    }
    out = {}
    for name, c in cases.items():
        a2 = dataclasses.replace(
            a,
            rev_growth=[g + c["g"] for g in a.rev_growth],
            ebit_margin=[min(max(m + c["m"], 0.0), 0.6) for m in a.ebit_margin],
            terminal_growth=a.terminal_growth + c["tg"],
        )
        fv = enterprise_value(a2, wacc_rate=max(base_wacc + c["w"], 0.02))["value_per_share"]
        out[name] = {"fair_value": fv, "trigger": c["trigger"]}
    return out


import dataclasses  # noqa: E402


def run(ticker: str, price_override: float | None = None) -> dict:
    OUT.mkdir(exist_ok=True)
    fund = datamod.fetch_fundamentals(ticker)
    pr = datamod.fetch_price(ticker)
    price = price_override if price_override is not None else pr["price"]

    beta = None
    if pr["history"]:
        mkt = datamod.fetch_price("SPY")
        beta = compute_beta(pr["history"], mkt["history"]) if mkt["history"] else None

    a, extras = build_assumptions(fund, price, beta)
    dcf = enterprise_value(a)
    w = dcf["wacc"]

    waccs = [round(w + d, 4) for d in (-0.015, -0.0075, 0.0, 0.0075, 0.015)]
    growths = [0.015, 0.020, 0.025, 0.030, 0.035]
    grid = sensitivity_grid(a, waccs, growths)

    comps = comps_valuation(extras["ebitda"], extras["eps"] or 0.0, extras["net_debt"],
                            a.shares, ev_ebitda_mult=12.0, pe_mult=18.0)  # ASSUMPTION multiples
    mc = monte_carlo(a, MonteCarloSpec(n=10000, seed=42))
    scenarios = scenario_band(a, w)

    upside = (dcf["value_per_share"] / price - 1) if price else None
    summary = {
        "ticker": fund["ticker"], "company": fund["name"], "cik": fund["cik"],
        "fiscal_years": fund["years"], "currency": pr.get("currency", "USD"),
        "price": price, "beta": a.beta, "wacc": w,
        "dcf_value_per_share": dcf["value_per_share"],
        "enterprise_value_m": dcf["enterprise_value"],
        "comps": comps,
        "monte_carlo": {k: v for k, v in mc.items() if k != "samples"},
        "scenarios": scenarios,
        "sensitivity": {"waccs": waccs, "growths": growths, "grid": grid},
        "upside_vs_price": upside,
        "assumptions": {
            "base_revenue_m": a.base_revenue, "rev_growth": a.rev_growth,
            "ebit_margin": a.ebit_margin, "tax_rate": a.tax_rate,
            "da_pct_rev": a.da_pct_rev, "capex_pct_rev": a.capex_pct_rev,
            "terminal_growth": a.terminal_growth, "risk_free": a.risk_free,
            "erp": a.erp, "pretax_kd": a.pretax_kd, "debt_m": a.debt_value,
            "cash_m": a.cash, "shares_m": a.shares,
        },
        "data_flags": fund["missing_flags"],
        "assumption_notes": extras["notes"],
        "price_flag": pr["flag"],
        "sources": "Fundamentals: SEC EDGAR (10-K). Price: Yahoo Finance. Assumptions derived "
                   "from company history + documented defaults; edit in the xlsx Assumptions tab.",
    }

    (OUT / f"{fund['ticker']}_valuation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _plot_mc(mc["samples"], dcf["value_per_share"], price, fund["ticker"])
    xlsx = build_xlsx.build(fund, a, dcf, comps, waccs, growths, grid, summary, extras)

    _print(summary, dcf)
    print(f"\nWrote: {xlsx}")
    print(f"Wrote: {OUT / (fund['ticker'] + '_valuation.json')}")
    return summary


def _plot_mc(samples, dcf_ps, price, ticker):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(samples, bins=60, color="#3b82f6", alpha=0.85, edgecolor="white", linewidth=0.3)
    ax.axvline(dcf_ps, color="#0f172a", linestyle="--", linewidth=1.6, label=f"DCF ${dcf_ps:,.0f}")
    if price:
        ax.axvline(price, color="#ef4444", linewidth=1.6, label=f"Price ${price:,.0f}")
    ax.set_title(f"{ticker} — Monte Carlo fair value per share")
    ax.set_xlabel("Value per share (USD)"); ax.set_ylabel("Frequency")
    ax.legend(frameon=False); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(OUT / f"{ticker}_montecarlo.png", dpi=130); plt.close(fig)


def _print(s, dcf):
    print(f"\n{s['company']} ({s['ticker']})  —  FY {s['fiscal_years']}")
    print(f"  WACC                 : {s['wacc']:.2%}  (beta {s['beta']})")
    print(f"  DCF value / share    : ${dcf['value_per_share']:,.2f}")
    print(f"  Comps midpoint /share: ${s['comps']['midpoint']:,.2f}")
    sc = s["scenarios"]
    print(f"  Scenarios            : Bear ${sc['Bear']['fair_value']:,.2f}  |  "
          f"Base ${sc['Base']['fair_value']:,.2f}  |  Bull ${sc['Bull']['fair_value']:,.2f}")
    mc = s["monte_carlo"]
    print(f"  Monte Carlo median   : ${mc['median']:,.2f}  (P5 ${mc['p5']:,.2f} - P95 ${mc['p95']:,.2f})")
    if s["price"] is not None:
        arrow = "+" if (s["upside_vs_price"] or 0) >= 0 else ""
        print(f"  Price                : ${s['price']:,.2f}  -> upside {arrow}{s['upside_vs_price']:.1%}")
    if s["data_flags"] or s["assumption_notes"]:
        print(f"  Flags                : {', '.join(s['data_flags']) or '—'}")
        for n in s["assumption_notes"]:
            print(f"     · {n}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Value any US-listed stock from live data.")
    ap.add_argument("ticker", help="e.g. MU, AAPL, NVDA")
    ap.add_argument("--price", type=float, default=None, help="override fetched price")
    args = ap.parse_args()
    try:
        run(args.ticker, args.price)
    except ValueError as e:
        print(f"\n{e}\nTip: use a US-listed ticker as it appears on SEC EDGAR (e.g. MU, AAPL, NVDA).")
        raise SystemExit(1)
