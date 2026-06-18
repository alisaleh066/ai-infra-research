"""re_engine — UK real-estate underwriting + a transparent ROI simulator.

Two parts:
  1. Underwriting: rent roll → NOI → cap-rate valuation → debt sizing (LTV/DSCR) → 5-yr levered
     cash flows → IRR / equity multiple, plus a two-way sensitivity grid (exit cap x rent growth).
  2. ROI simulator: maps observable demand/supply drivers (net migration, household formation,
     completions, employment, interest rate) to an implied rent growth and exit cap via EXPLICIT,
     documented elasticities — then runs the same underwriting. Every driver is visible; nothing
     is hidden. This is assumption-driven, NOT a news-to-price black box.

Pure functions, unit-tested. Money in GBP. The dashboard mirrors these exact formulas in TS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


# --------------------------------------------------------------------------- Underwriting
@dataclass
class Deal:
    units_monthly_rent: Sequence[float]   # rent roll: monthly rent per unit (GBP)
    vacancy_rate: float                   # e.g. 0.05
    opex_ratio: float                     # operating costs as % of effective gross income
    entry_cap_rate: float                 # going-in cap rate (NOI / price)
    exit_cap_rate: float                  # cap rate at sale
    rent_growth: float                    # annual rent (and NOI) growth
    ltv: float                            # loan-to-value
    interest_rate: float                  # debt interest rate (interest-only)
    purchase_costs_pct: float = 0.05      # SDLT + legal + acquisition, % of price
    selling_costs_pct: float = 0.015      # agent/legal at exit, % of gross sale
    hold_years: int = 5


def gross_rent(deal: Deal) -> float:
    """Annualised gross potential rent from the rent roll."""
    return sum(deal.units_monthly_rent) * 12


def noi(deal: Deal) -> float:
    """Net operating income = effective gross income net of opex."""
    egi = gross_rent(deal) * (1 - deal.vacancy_rate)
    return egi * (1 - deal.opex_ratio)


def valuation(deal: Deal) -> float:
    """Cap-rate valuation = NOI / entry cap rate."""
    if deal.entry_cap_rate <= 0:
        raise ValueError("entry_cap_rate must be positive")
    return noi(deal) / deal.entry_cap_rate


def debt_sizing(deal: Deal) -> dict:
    """Loan, equity and DSCR for the deal (interest-only debt)."""
    price = valuation(deal)
    loan = deal.ltv * price
    debt_service = loan * deal.interest_rate
    equity = price * (1 + deal.purchase_costs_pct) - loan
    dscr = (noi(deal) / debt_service) if debt_service else float("inf")
    return {"price": price, "loan": loan, "equity": equity,
            "debt_service": debt_service, "dscr": dscr}


def levered_cash_flows(deal: Deal) -> list[float]:
    """Equity cash flows: year 0 = -equity; years 1..N = NOI - debt service; year N += net sale."""
    d = debt_sizing(deal)
    cfs = [-d["equity"]]
    base_noi = noi(deal)
    for yr in range(1, deal.hold_years + 1):
        yr_noi = base_noi * (1 + deal.rent_growth) ** yr
        cf = yr_noi - d["debt_service"]
        if yr == deal.hold_years:
            exit_noi = base_noi * (1 + deal.rent_growth) ** (deal.hold_years + 1)
            gross_sale = exit_noi / deal.exit_cap_rate
            net_sale = gross_sale * (1 - deal.selling_costs_pct) - d["loan"]
            cf += net_sale
        cfs.append(cf)
    return cfs


def npv(rate: float, cfs: Sequence[float]) -> float:
    return sum(cf / (1 + rate) ** i for i, cf in enumerate(cfs))


def irr(cfs: Sequence[float], lo: float = -0.99, hi: float = 5.0, tol: float = 1e-7) -> float:
    """IRR via bisection. Returns nan if no sign change in [lo, hi]."""
    f_lo, f_hi = npv(lo, cfs), npv(hi, cfs)
    if f_lo * f_hi > 0:
        return float("nan")
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = npv(mid, cfs)
        if abs(f_mid) < tol:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def equity_multiple(cfs: Sequence[float]) -> float:
    """Total distributions / equity invested."""
    invested = -cfs[0]
    distributions = sum(cf for cf in cfs[1:])
    return distributions / invested if invested else float("nan")


def underwrite(deal: Deal) -> dict:
    d = debt_sizing(deal)
    cfs = levered_cash_flows(deal)
    return {
        "noi": noi(deal), "valuation": valuation(deal),
        "loan": d["loan"], "equity": d["equity"], "dscr": d["dscr"],
        "cash_flows": cfs, "irr": irr(cfs), "equity_multiple": equity_multiple(cfs),
    }


def sensitivity_grid(deal: Deal, exit_caps: Sequence[float],
                     rent_growths: Sequence[float]) -> list[list[float]]:
    """IRR grid over exit cap (rows) x rent growth (cols)."""
    import dataclasses
    grid = []
    for ec in exit_caps:
        row = []
        for g in rent_growths:
            d2 = dataclasses.replace(deal, exit_cap_rate=ec, rent_growth=g)
            row.append(irr(levered_cash_flows(d2)))
        grid.append(row)
    return grid


# --------------------------------------------------------------------------- ROI simulator
@dataclass
class DriverBaselines:
    """Long-run baselines the drivers are measured against (documented assumptions)."""
    net_migration: float = 250000.0
    household_formation: float = 165000.0
    completions: float = 234000.0
    employment_rate: float = 74.8
    bank_rate_pct: float = 4.25


@dataclass
class SimulatorCoefficients:
    """EXPLICIT elasticities mapping driver deviations to rent growth / exit cap.

    Every coefficient is a documented assumption — adjust and the response is fully traceable.
    """
    base_rent_growth: float = 0.025
    w_migration: float = 0.40          # weight of migration deviation in demand pressure
    w_formation: float = 0.35          # weight of household-formation deviation
    w_employment: float = 0.25         # weight of employment deviation
    rent_growth_sensitivity: float = 0.06   # rent growth per unit of net demand pressure
    debt_margin: float = 0.015         # lender margin over Bank Rate
    cap_sensitivity_to_rate: float = 0.50   # exit-cap bps move per 1pp Bank Rate move (as fraction)
    base_exit_cap: float = 0.055
    results: dict = field(default_factory=dict)


def demand_pressure(drivers: dict, base: DriverBaselines, c: SimulatorCoefficients) -> float:
    """Net demand/supply pressure (dimensionless). Positive = demand exceeds supply.

    Each term is a proportional deviation from baseline; immigration is ONE explicit term.
    """
    mig = (drivers["net_migration"] / base.net_migration - 1) * c.w_migration
    form = (drivers["household_formation"] / base.household_formation - 1) * c.w_formation
    emp = ((drivers["employment_rate"] - base.employment_rate) / base.employment_rate) * c.w_employment
    demand = mig + form + emp
    supply = (drivers["completions"] / base.completions - 1)
    return demand - supply


def implied_rent_growth(drivers: dict, base: DriverBaselines, c: SimulatorCoefficients) -> float:
    return c.base_rent_growth + c.rent_growth_sensitivity * demand_pressure(drivers, base, c)


def implied_exit_cap(drivers: dict, base: DriverBaselines, c: SimulatorCoefficients) -> float:
    """Exit cap rises with Bank Rate (higher rates -> higher caps -> lower values)."""
    rate_gap_pp = drivers["bank_rate_pct"] - base.bank_rate_pct
    return c.base_exit_cap + c.cap_sensitivity_to_rate * (rate_gap_pp / 100.0)


def implied_debt_rate(drivers: dict, c: SimulatorCoefficients) -> float:
    return drivers["bank_rate_pct"] / 100.0 + c.debt_margin


def simulate(base_deal: Deal, drivers: dict,
             base: DriverBaselines | None = None,
             c: SimulatorCoefficients | None = None) -> dict:
    """Run the underwriting with rent growth / exit cap / debt rate implied by the drivers."""
    import dataclasses
    base = base or DriverBaselines()
    c = c or SimulatorCoefficients()
    g = implied_rent_growth(drivers, base, c)
    ec = implied_exit_cap(drivers, base, c)
    dr = implied_debt_rate(drivers, c)
    deal = dataclasses.replace(base_deal, rent_growth=g, exit_cap_rate=ec, interest_rate=dr)
    res = underwrite(deal)
    res.update({"implied_rent_growth": g, "implied_exit_cap": ec, "implied_debt_rate": dr,
                "demand_pressure": demand_pressure(drivers, base, c)})
    return res
