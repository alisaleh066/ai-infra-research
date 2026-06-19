"""valuation_engine — DCF (FCFF), WACC build, sensitivity and comps for an equity.

Pure functions, no I/O, fully unit-tested in tests/test_valuation.py. All monetary inputs are in
USD millions; per-share outputs in USD. Assumptions are explicit arguments so the dashboard and
the Excel model can mirror the exact same math.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
@dataclass
class DCFAssumptions:
    """All inputs to the DCF. Values flagged ASSUMPTION in DATA_SOURCES.md are user-editable."""
    base_revenue: float                 # most recent FY revenue ($m)
    rev_growth: Sequence[float]         # per-year revenue growth (explicit horizon)
    ebit_margin: Sequence[float]        # per-year EBIT margin
    tax_rate: float
    da_pct_rev: float                   # D&A as % of revenue
    capex_pct_rev: float                # capex as % of revenue
    nwc_pct_rev_change: float           # incremental NWC as % of revenue change
    terminal_growth: float
    # WACC build
    risk_free: float
    erp: float                          # equity risk premium
    beta: float
    pretax_kd: float                    # pre-tax cost of debt
    equity_value: float                 # market value of equity ($m)  [ASSUMPTION price*shares]
    debt_value: float                   # total debt ($m)
    cash: float                         # cash & equivalents ($m)
    shares: float                       # diluted shares (millions)

    def __post_init__(self) -> None:
        if len(self.rev_growth) != len(self.ebit_margin):
            raise ValueError("rev_growth and ebit_margin must have the same horizon length")


# --------------------------------------------------------------------------- #
# WACC
# --------------------------------------------------------------------------- #
def cost_of_equity(risk_free: float, beta: float, erp: float) -> float:
    """CAPM cost of equity."""
    return risk_free + beta * erp


def wacc(a: DCFAssumptions) -> float:
    """Weighted average cost of capital from market-value weights."""
    ke = cost_of_equity(a.risk_free, a.beta, a.erp)
    kd_at = a.pretax_kd * (1 - a.tax_rate)
    e, d = a.equity_value, a.debt_value
    total = e + d
    if total <= 0:
        raise ValueError("equity_value + debt_value must be positive")
    return (e / total) * ke + (d / total) * kd_at


# --------------------------------------------------------------------------- #
# FCFF projection + DCF
# --------------------------------------------------------------------------- #
def project_fcff(a: DCFAssumptions) -> list[dict]:
    """Project unlevered free cash flow to firm for the explicit horizon.

    FCFF = EBIT*(1-tax) + D&A - capex - dNWC
    """
    rows: list[dict] = []
    prev_rev = a.base_revenue
    for i, (g, m) in enumerate(zip(a.rev_growth, a.ebit_margin), start=1):
        rev = prev_rev * (1 + g)
        ebit = rev * m
        nopat = ebit * (1 - a.tax_rate)
        da = rev * a.da_pct_rev
        capex = rev * a.capex_pct_rev
        dnwc = (rev - prev_rev) * a.nwc_pct_rev_change
        fcff = nopat + da - capex - dnwc
        rows.append({
            "year": i, "revenue": rev, "ebit": ebit, "nopat": nopat,
            "da": da, "capex": capex, "dnwc": dnwc, "fcff": fcff,
        })
        prev_rev = rev
    return rows


def terminal_value(last_fcff: float, wacc_rate: float, g: float) -> float:
    """Gordon-growth terminal value on the last explicit FCFF."""
    if wacc_rate <= g:
        raise ValueError("WACC must exceed terminal growth")
    return last_fcff * (1 + g) / (wacc_rate - g)


def enterprise_value(a: DCFAssumptions, wacc_rate: float | None = None) -> dict:
    """Discount projected FCFF + terminal value to an enterprise and equity value."""
    w = wacc(a) if wacc_rate is None else wacc_rate
    rows = project_fcff(a)
    pv_fcff = 0.0
    for r in rows:
        pv = r["fcff"] / (1 + w) ** r["year"]
        r["discount_factor"] = 1 / (1 + w) ** r["year"]
        r["pv_fcff"] = pv
        pv_fcff += pv
    tv = terminal_value(rows[-1]["fcff"], w, a.terminal_growth)
    pv_tv = tv / (1 + w) ** rows[-1]["year"]
    ev = pv_fcff + pv_tv
    equity = ev - a.debt_value + a.cash          # net debt bridge
    per_share = equity / a.shares
    return {
        "wacc": w,
        "rows": rows,
        "pv_fcff": pv_fcff,
        "terminal_value": tv,
        "pv_terminal_value": pv_tv,
        "enterprise_value": ev,
        "equity_value": equity,
        "value_per_share": per_share,
        "tv_pct_of_ev": pv_tv / ev,
    }


def value_per_share(a: DCFAssumptions, wacc_rate: float | None = None,
                    terminal_growth: float | None = None) -> float:
    """Convenience: intrinsic value per share, optionally overriding WACC / terminal growth."""
    if terminal_growth is None:
        return enterprise_value(a, wacc_rate)["value_per_share"]
    # override terminal growth without mutating caller's object
    import dataclasses
    a2 = dataclasses.replace(a, terminal_growth=terminal_growth)
    return enterprise_value(a2, wacc_rate)["value_per_share"]


# --------------------------------------------------------------------------- #
# Sensitivity (WACC x terminal growth)
# --------------------------------------------------------------------------- #
def sensitivity_grid(a: DCFAssumptions, waccs: Sequence[float],
                     growths: Sequence[float]) -> list[list[float]]:
    """2-D grid of value-per-share over WACC (rows) x terminal growth (cols)."""
    grid: list[list[float]] = []
    for w in waccs:
        row = [value_per_share(a, wacc_rate=w, terminal_growth=g) for g in growths]
        grid.append(row)
    return grid


# --------------------------------------------------------------------------- #
# Comparable companies
# --------------------------------------------------------------------------- #
def comps_valuation(ebitda: float, eps: float, net_debt: float, shares: float,
                    ev_ebitda_mult: float, pe_mult: float) -> dict:
    """Implied per-share value from an EV/EBITDA multiple and a P/E multiple."""
    ev = ev_ebitda_mult * ebitda
    equity_from_ev = ev - net_debt
    ps_ev = equity_from_ev / shares
    ps_pe = pe_mult * eps
    return {
        "implied_ev": ev,
        "value_per_share_ev_ebitda": ps_ev,
        "value_per_share_pe": ps_pe,
        "midpoint": (ps_ev + ps_pe) / 2,
    }


# --------------------------------------------------------------------------- #
# Monte Carlo
# --------------------------------------------------------------------------- #
@dataclass
class MonteCarloSpec:
    """Std-devs for the perturbed drivers (normal, around the base assumptions)."""
    rev_growth_sd: float = 0.05
    ebit_margin_sd: float = 0.03
    wacc_sd: float = 0.01
    terminal_growth_sd: float = 0.005
    n: int = 10000
    seed: int = 42
    results: list[float] = field(default_factory=list)


def monte_carlo(a: DCFAssumptions, spec: MonteCarloSpec) -> dict:
    """Perturb key drivers and return the distribution of value-per-share."""
    import dataclasses
    rng = np.random.default_rng(spec.seed)
    base_w = wacc(a)
    out = np.empty(spec.n)
    for i in range(spec.n):
        g_shock = rng.normal(0, spec.rev_growth_sd)
        m_shock = rng.normal(0, spec.ebit_margin_sd)
        w = max(base_w + rng.normal(0, spec.wacc_sd), 0.01)
        tg = a.terminal_growth + rng.normal(0, spec.terminal_growth_sd)
        tg = min(tg, w - 0.005)                       # keep WACC > g
        a2 = dataclasses.replace(
            a,
            rev_growth=[max(g + g_shock, -0.5) for g in a.rev_growth],
            ebit_margin=[min(max(m + m_shock, 0.0), 0.6) for m in a.ebit_margin],
            terminal_growth=tg,
        )
        try:
            out[i] = enterprise_value(a2, wacc_rate=w)["value_per_share"]
        except ValueError:
            out[i] = np.nan
    out = out[~np.isnan(out)]
    pct = np.percentile(out, [5, 25, 50, 75, 95])
    return {
        "n": int(out.size),
        "mean": float(out.mean()),
        "median": float(np.median(out)),
        "std": float(out.std()),
        "p5": float(pct[0]), "p25": float(pct[1]), "p50": float(pct[2]),
        "p75": float(pct[3]), "p95": float(pct[4]),
        "samples": out.tolist(),
    }
