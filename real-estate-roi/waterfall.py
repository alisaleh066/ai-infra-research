"""waterfall.py — LP/GP equity distribution waterfall with IRR hurdles and promote.

The signature institutional return structure (Blackstone/BlackRock-style). Equity distributions
flow through tiers:
    1. Return of capital + PREFERRED RETURN  -> 100% to LP   (until LP hits hurdle 1, e.g. 8% IRR)
    2. PROMOTE tiers by IRR hurdle           -> split LP/GP   (GP's "carried interest")

Each hurdle keeps an accrued LP capital account compounding at that hurdle rate; a distribution
counts toward a hurdle only by the LP portion it pays. When the account for a hurdle reaches zero,
the LP has achieved that IRR and the next (higher-promote) band begins.

By default the GP co-invests nothing and earns only the promote (clean illustration); the project
return is reported alongside the LP return so the promote "drag" is explicit.

Pure functions; period 0 = equity contribution, periods 1..N = distributions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from underwrite import equity_multiple, irr


@dataclass
class WaterfallTiers:
    """Ascending IRR hurdles and the GP promote share that applies ABOVE each hurdle.

    Default: 8% pref (LP 100% below it), then 8-12% -> 20% promote, 12-15% -> 30%, >15% -> 40%.
    """
    hurdles: Sequence[tuple[float, float]] = field(
        default_factory=lambda: [(0.08, 0.20), (0.12, 0.30), (0.15, 0.40)]
    )

    def rates(self):
        return [h for h, _ in self.hurdles]

    def promotes(self):
        return [p for _, p in self.hurdles]


def run_waterfall(equity_cfs: Sequence[float], tiers: WaterfallTiers | None = None) -> dict:
    """Split equity cash flows into LP and GP streams via an IRR-hurdle promote waterfall.

    equity_cfs[0] is the (negative) total equity contribution; equity_cfs[1:] are distributions
    (a negative later value is treated as a capital call). GP co-invest = 0 (earns only promote).
    """
    tiers = tiers or WaterfallTiers()
    rates = tiers.rates()
    promotes = tiers.promotes()
    T = len(rates)
    accts = [0.0] * T                                  # LP owed-balance accrued at each hurdle

    lp_dist: list[float] = []
    gp_dist: list[float] = []
    contribution0 = -equity_cfs[0]

    for t, cf in enumerate(equity_cfs):
        # accrue, then add this period's contribution (period 0, or a later capital call)
        for j in range(T):
            accts[j] *= (1 + rates[j])
        if t == 0:
            for j in range(T):
                accts[j] += contribution0
            lp_dist.append(equity_cfs[0])             # LP funds the equity
            gp_dist.append(0.0)
            continue

        if cf < 0:                                     # capital call -> LP funds it
            for j in range(T):
                accts[j] += -cf
            lp_dist.append(cf)
            gp_dist.append(0.0)
            continue

        D = cf
        lp = 0.0
        gp = 0.0

        # Band 0: 100% LP until the lowest hurdle's account is repaid (capital + pref)
        if D > 0 and accts[0] > 0:
            pay = min(D, accts[0])
            lp += pay
            D -= pay
            for j in range(T):
                accts[j] -= pay

        # Middle bands: between achieving hurdle[j-1] and hurdle[j], GP promote = promotes[j-1]
        for j in range(1, T):
            if D <= 0:
                break
            if accts[j] <= 0:                          # this hurdle already achieved
                continue
            p = promotes[j - 1]
            total_band = accts[j] / (1 - p) if p < 1 else float("inf")
            pay = min(D, total_band)
            lp_part = pay * (1 - p)
            gp += pay * p
            lp += lp_part
            D -= pay
            for k in range(T):
                accts[k] -= lp_part

        # Top band: above the highest hurdle, GP promote = promotes[-1]
        if D > 0:
            p = promotes[-1]
            lp += D * (1 - p)
            gp += D * p
            for k in range(T):
                accts[k] -= D * (1 - p)
            D = 0.0

        lp_dist.append(lp)
        gp_dist.append(gp)

    total_equity = contribution0
    lp_irr = irr(lp_dist)
    project_irr = irr(equity_cfs)
    gp_profit = sum(x for x in gp_dist if x > 0)
    total_profit = sum(equity_cfs)
    return {
        "lp_cash_flows": lp_dist,
        "gp_cash_flows": gp_dist,
        "lp_irr": lp_irr,
        "lp_equity_multiple": equity_multiple(lp_dist),
        "project_irr": project_irr,
        "project_equity_multiple": equity_multiple(equity_cfs),
        "promote_drag": (project_irr - lp_irr) if (project_irr == project_irr and lp_irr == lp_irr) else float("nan"),
        "gp_promote": gp_profit,
        "gp_share_of_profit": gp_profit / total_profit if total_profit > 0 else 0.0,
        "total_equity": total_equity,
        "tiers": tiers.hurdles,
    }
