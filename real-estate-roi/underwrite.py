"""underwrite.py — institutional real-estate deal underwriting (value-add lifecycle).

Models a deal the way a sponsor (Blackstone/BlackRock-style) does:
  acquire at a going-in cap -> spend value-add capex -> grow NOI to a stabilized level ->
  hold -> exit at an exit cap (or refinance). Produces levered equity cash flows and the
  return metrics underwriters live by: project IRR, equity multiple, cash-on-cash, DSCR,
  debt yield, LTV/LTC.

Pure functions; money in absolute currency units (GBP or USD — your choice, just be consistent).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


# --------------------------------------------------------------------------- IRR / NPV
def npv(rate: float, cfs: Sequence[float]) -> float:
    return sum(cf / (1 + rate) ** i for i, cf in enumerate(cfs))


def irr(cfs: Sequence[float], lo: float = -0.99, hi: float = 5.0, tol: float = 1e-9) -> float:
    """IRR via bisection on the sign change. Returns nan if no sign change in [lo, hi]."""
    flo, fhi = npv(lo, cfs), npv(hi, cfs)
    if flo * fhi > 0:
        return float("nan")
    for _ in range(300):
        mid = (lo + hi) / 2
        fmid = npv(mid, cfs)
        if abs(fmid) < tol:
            return mid
        if flo * fmid < 0:
            hi, fhi = mid, fmid
        else:
            lo, flo = mid, fmid
    return (lo + hi) / 2


def equity_multiple(cfs: Sequence[float]) -> float:
    """Total distributions / equity invested (a.k.a. MOIC)."""
    invested = -sum(cf for cf in cfs if cf < 0)
    distributions = sum(cf for cf in cfs if cf > 0)
    return distributions / invested if invested else float("nan")


# --------------------------------------------------------------------------- Deal
@dataclass
class Deal:
    purchase_price: float
    in_place_noi: float                 # year-0 in-place net operating income
    going_in_cap: float                 # for reference / implied value
    exit_cap: float
    hold_years: int = 5
    # value-add lifecycle
    noi_uplift_pct: float = 0.25        # stabilized NOI = in-place * (1 + uplift)
    stabilize_years: int = 2            # years to ramp from in-place to stabilized
    post_stabilize_growth: float = 0.03 # annual NOI growth once stabilized
    renovation_capex: float = 0.0       # value-add budget, spent at close (year 0)
    acquisition_costs_pct: float = 0.02
    selling_costs_pct: float = 0.015
    # debt
    ltv: float = 0.65                   # loan = ltv * purchase_price
    interest_rate: float = 0.06
    amortization_years: int = 0         # 0 = interest-only; else amortise over N years
    # optional mid-hold cash-out refinance (0 = none)
    refinance_year: int = 0
    refinance_ltv: float = 0.65         # LTV on the stabilised value at refinance
    refinance_rate: float = 0.0         # new rate (0 -> keep current rate)

    def stabilized_noi(self) -> float:
        return self.in_place_noi * (1 + self.noi_uplift_pct)

    def noi_at(self, year: int) -> float:
        """NOI in a given hold year (1-indexed): linear ramp to stabilized, then growth."""
        stab = self.stabilized_noi()
        if year <= self.stabilize_years and self.stabilize_years > 0:
            return self.in_place_noi + (stab - self.in_place_noi) * (year / self.stabilize_years)
        extra = year - self.stabilize_years
        return stab * (1 + self.post_stabilize_growth) ** max(extra, 0)


def total_cost(d: Deal) -> float:
    return d.purchase_price * (1 + d.acquisition_costs_pct) + d.renovation_capex


def loan_amount(d: Deal) -> float:
    return d.ltv * d.purchase_price


def equity_required(d: Deal) -> float:
    return total_cost(d) - loan_amount(d)


def _mortgage_constant(rate: float, n_years: int) -> float:
    """Level annual payment per unit of loan for an amortising loan."""
    if n_years <= 0:
        return 0.0
    if rate == 0:
        return 1.0 / n_years
    return rate / (1 - (1 + rate) ** (-n_years))


def debt_service(d: Deal) -> float:
    """Recurring annual payment: interest-only, or the amortising mortgage payment."""
    loan = loan_amount(d)
    if d.amortization_years > 0:
        return loan * _mortgage_constant(d.interest_rate, d.amortization_years)
    return loan * d.interest_rate


def debt_schedule(d: Deal) -> list[dict]:
    """Per-year payment / interest / principal / end-balance, incl. any refinance + cash-out."""
    loan = loan_amount(d)
    balance = loan
    rate = d.interest_rate
    pmt = debt_service(d)
    rows = []
    for t in range(1, d.hold_years + 1):
        interest = balance * rate
        principal = (pmt - interest) if d.amortization_years > 0 else 0.0
        principal = min(max(principal, 0.0), balance)
        balance -= principal
        cash_out = 0.0
        if d.refinance_year and t == d.refinance_year:
            refi_value = d.noi_at(t + 1) / d.exit_cap        # stabilised value at refi
            new_loan = d.refinance_ltv * refi_value
            cash_out = new_loan - balance
            balance = new_loan
            rate = d.refinance_rate or rate
            pmt = new_loan * _mortgage_constant(rate, d.amortization_years) if d.amortization_years > 0 else new_loan * rate
        rows.append({"year": t, "payment": pmt if d.amortization_years > 0 else balance * rate,
                     "interest": interest, "principal": principal,
                     "balance": balance, "cash_out": cash_out})
    return rows


def equity_cash_flows(d: Deal) -> list[float]:
    """Levered equity cash flows: year-0 outflow, operating CF + refi cash-out, sale in year N."""
    sched = debt_schedule(d)
    cfs = [-equity_required(d)]
    for t in range(1, d.hold_years + 1):
        row = sched[t - 1]
        cf = d.noi_at(t) - row["payment"] + row["cash_out"]
        if t == d.hold_years:
            gross_sale = d.noi_at(t + 1) / d.exit_cap
            net_sale = gross_sale * (1 - d.selling_costs_pct) - row["balance"]
            cf += net_sale
        cfs.append(cf)
    return cfs


def underwrite(d: Deal) -> dict:
    cfs = equity_cash_flows(d)
    sched = debt_schedule(d)
    loan = loan_amount(d)
    eq = equity_required(d)
    coc = [(d.noi_at(t) - sched[t - 1]["payment"]) / eq for t in range(1, d.hold_years + 1)]
    dscr = [d.noi_at(t) / sched[t - 1]["payment"] if sched[t - 1]["payment"] else float("inf")
            for t in range(1, d.hold_years + 1)]
    exit_noi = d.noi_at(d.hold_years + 1)
    refi_cash = next((r["cash_out"] for r in sched if r["cash_out"]), 0.0)
    return {
        "implied_value_going_in": d.in_place_noi / d.going_in_cap,
        "purchase_price": d.purchase_price,
        "total_cost": total_cost(d),
        "loan": loan, "equity": eq,
        "ltv": loan / d.purchase_price,
        "ltc": loan / total_cost(d),
        "debt_service": debt_service(d),
        "amortizing": d.amortization_years > 0,
        "refinance_cash_out": refi_cash,
        "exit_loan_balance": sched[-1]["balance"],
        "debt_yield": d.in_place_noi / loan if loan else float("inf"),
        "stabilized_noi": d.stabilized_noi(),
        "exit_value": exit_noi / d.exit_cap,
        "cash_flows": cfs,
        "debt_schedule": sched,
        "project_irr": irr(cfs),
        "equity_multiple": equity_multiple(cfs),
        "avg_cash_on_cash": sum(coc) / len(coc),
        "cash_on_cash": coc,
        "dscr": dscr,
        "min_dscr": min(dscr),
    }
