"""Tests for the UK real-estate engine + ROI simulator (Project 3). Run: pytest -q"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "real_estate"))

from re_engine import (  # noqa: E402
    Deal, DriverBaselines, SimulatorCoefficients, debt_sizing, demand_pressure,
    equity_multiple, gross_rent, implied_exit_cap, implied_rent_growth, irr,
    levered_cash_flows, noi, npv, sensitivity_grid, simulate, underwrite, valuation,
)


def base_deal(**over) -> Deal:
    d = dict(
        units_monthly_rent=[1000, 1000, 1000, 1000],
        vacancy_rate=0.05, opex_ratio=0.25,
        entry_cap_rate=0.06, exit_cap_rate=0.06, rent_growth=0.03,
        ltv=0.65, interest_rate=0.06,
        purchase_costs_pct=0.05, selling_costs_pct=0.015, hold_years=5,
    )
    d.update(over)
    return Deal(**d)


# --------------------------------------------------------------------------- NOI / valuation
def test_gross_and_noi():
    d = base_deal()
    assert gross_rent(d) == 4 * 1000 * 12
    egi = 48000 * 0.95
    assert noi(d) == pytest.approx(egi * 0.75)


def test_valuation_is_noi_over_cap():
    d = base_deal()
    assert valuation(d) == pytest.approx(noi(d) / 0.06)


def test_valuation_requires_positive_cap():
    with pytest.raises(ValueError):
        valuation(base_deal(entry_cap_rate=0))


# --------------------------------------------------------------------------- debt
def test_debt_sizing_and_dscr():
    d = base_deal()
    ds = debt_sizing(d)
    price = valuation(d)
    assert ds["loan"] == pytest.approx(0.65 * price)
    assert ds["equity"] == pytest.approx(price * 1.05 - ds["loan"])
    assert ds["dscr"] == pytest.approx(noi(d) / (ds["loan"] * 0.06))


# --------------------------------------------------------------------------- IRR / EM
def test_npv_zero_at_irr():
    cfs = [-100, 30, 30, 30, 30, 30]
    r = irr(cfs)
    assert npv(r, cfs) == pytest.approx(0.0, abs=1e-5)


def test_irr_known_value():
    # invest 100, get 110 in one year -> IRR 10%
    assert irr([-100, 110]) == pytest.approx(0.10, abs=1e-4)


def test_irr_no_sign_change_returns_nan():
    import math
    assert math.isnan(irr([100, 50, 50]))


def test_equity_multiple_definition():
    cfs = [-100, 20, 20, 20, 20, 120]
    assert equity_multiple(cfs) == pytest.approx(200 / 100)


def test_underwrite_positive_irr_for_reasonable_deal():
    r = underwrite(base_deal())
    assert r["irr"] > 0
    assert r["equity_multiple"] > 1
    assert len(r["cash_flows"]) == 6


# --------------------------------------------------------------------------- sensitivity
def test_sensitivity_irr_rises_with_rent_growth_and_falls_with_exit_cap():
    d = base_deal()
    caps = [0.05, 0.06, 0.07]
    growths = [0.01, 0.03, 0.05]
    grid = sensitivity_grid(d, caps, growths)
    for row in grid:
        assert row[0] < row[1] < row[2]            # higher rent growth -> higher IRR
    for j in range(3):
        assert grid[0][j] > grid[1][j] > grid[2][j]  # higher exit cap -> lower IRR


# --------------------------------------------------------------------------- ROI simulator
def baseline_drivers() -> dict:
    b = DriverBaselines()
    return {"net_migration": b.net_migration, "household_formation": b.household_formation,
            "completions": b.completions, "employment_rate": b.employment_rate,
            "bank_rate_pct": b.bank_rate_pct}


def test_demand_pressure_zero_at_baseline():
    assert demand_pressure(baseline_drivers(), DriverBaselines(),
                           SimulatorCoefficients()) == pytest.approx(0.0)


def test_higher_migration_raises_rent_growth_and_irr():
    base = DriverBaselines(); c = SimulatorCoefficients()
    low = baseline_drivers()
    high = baseline_drivers(); high["net_migration"] = base.net_migration * 2
    assert implied_rent_growth(high, base, c) > implied_rent_growth(low, base, c)
    r_low = simulate(base_deal(), low, base, c)
    r_high = simulate(base_deal(), high, base, c)
    assert r_high["irr"] > r_low["irr"]            # migration is an explicit demand driver


def test_more_supply_reduces_rent_growth():
    base = DriverBaselines(); c = SimulatorCoefficients()
    more_supply = baseline_drivers(); more_supply["completions"] = base.completions * 1.5
    assert implied_rent_growth(more_supply, base, c) < c.base_rent_growth


def test_higher_bank_rate_raises_exit_cap():
    base = DriverBaselines(); c = SimulatorCoefficients()
    d = baseline_drivers(); d["bank_rate_pct"] = base.bank_rate_pct + 2
    assert implied_exit_cap(d, base, c) > c.base_exit_cap


def test_simulator_is_transparent_immigration_one_of_several():
    # zeroing migration weight removes migration's effect entirely -> proves it's explicit, not hidden
    base = DriverBaselines()
    c_no_mig = SimulatorCoefficients(w_migration=0.0)
    d = baseline_drivers(); d["net_migration"] = base.net_migration * 3
    assert implied_rent_growth(d, base, c_no_mig) == pytest.approx(
        c_no_mig.base_rent_growth + c_no_mig.rent_growth_sensitivity *
        (-(d["completions"] / base.completions - 1)), abs=1e-9)
