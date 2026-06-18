"""Tests for the valuation engine (Project 1). Run: pytest -q tests/test_valuation.py"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "valuation"))

from valuation_engine import (  # noqa: E402
    DCFAssumptions, MonteCarloSpec, comps_valuation, cost_of_equity, enterprise_value,
    monte_carlo, project_fcff, sensitivity_grid, terminal_value, value_per_share, wacc,
)


def base_assumptions(**over) -> DCFAssumptions:
    d = dict(
        base_revenue=1000.0,
        rev_growth=[0.10, 0.08, 0.06, 0.05, 0.04],
        ebit_margin=[0.30, 0.30, 0.30, 0.30, 0.30],
        tax_rate=0.20,
        da_pct_rev=0.10,
        capex_pct_rev=0.10,
        nwc_pct_rev_change=0.05,
        terminal_growth=0.025,
        risk_free=0.04,
        erp=0.05,
        beta=1.0,
        pretax_kd=0.05,
        equity_value=9000.0,
        debt_value=1000.0,
        cash=200.0,
        shares=100.0,
    )
    d.update(over)
    return DCFAssumptions(**d)


# --------------------------------------------------------------------------- WACC
def test_cost_of_equity_capm():
    assert cost_of_equity(0.04, 1.0, 0.05) == pytest.approx(0.09)


def test_wacc_weights_and_value():
    a = base_assumptions()
    # ke = 0.09; kd_at = 0.05*0.8 = 0.04; E=9000 D=1000 -> 0.9*0.09 + 0.1*0.04 = 0.085
    assert wacc(a) == pytest.approx(0.085, abs=1e-9)


def test_wacc_requires_positive_capital():
    with pytest.raises(ValueError):
        wacc(base_assumptions(equity_value=0.0, debt_value=0.0))


# --------------------------------------------------------------------------- FCFF
def test_project_fcff_first_year():
    a = base_assumptions()
    rows = project_fcff(a)
    rev1 = 1000 * 1.10
    ebit1 = rev1 * 0.30
    nopat1 = ebit1 * 0.80
    fcff1 = nopat1 + rev1 * 0.10 - rev1 * 0.10 - (rev1 - 1000) * 0.05
    assert rows[0]["revenue"] == pytest.approx(rev1)
    assert rows[0]["fcff"] == pytest.approx(fcff1)
    assert len(rows) == 5


def test_project_fcff_horizon_mismatch_raises():
    with pytest.raises(ValueError):
        base_assumptions(rev_growth=[0.1, 0.1], ebit_margin=[0.3])


# --------------------------------------------------------------------------- Terminal value
def test_terminal_value_formula():
    assert terminal_value(100.0, 0.10, 0.02) == pytest.approx(100 * 1.02 / 0.08)


def test_terminal_value_requires_wacc_above_growth():
    with pytest.raises(ValueError):
        terminal_value(100.0, 0.02, 0.02)


# --------------------------------------------------------------------------- DCF
def test_enterprise_value_bridge_and_positive():
    a = base_assumptions()
    r = enterprise_value(a)
    # equity = EV - debt + cash ; per share = equity / shares
    assert r["equity_value"] == pytest.approx(r["enterprise_value"] - a.debt_value + a.cash)
    assert r["value_per_share"] == pytest.approx(r["equity_value"] / a.shares)
    assert r["value_per_share"] > 0
    assert 0 < r["tv_pct_of_ev"] < 1


def test_value_per_share_monotonic_in_wacc():
    a = base_assumptions()
    low = value_per_share(a, wacc_rate=0.08)
    high = value_per_share(a, wacc_rate=0.12)
    assert low > high  # higher discount rate -> lower value


def test_value_per_share_monotonic_in_growth():
    a = base_assumptions()
    assert value_per_share(a, terminal_growth=0.03) > value_per_share(a, terminal_growth=0.01)


# --------------------------------------------------------------------------- Sensitivity
def test_sensitivity_grid_shape_and_ordering():
    a = base_assumptions()
    waccs = [0.08, 0.09, 0.10]
    growths = [0.01, 0.02, 0.03]
    grid = sensitivity_grid(a, waccs, growths)
    assert len(grid) == 3 and all(len(r) == 3 for r in grid)
    # within a row, value rises with growth; down a column, value falls as WACC rises
    for row in grid:
        assert row[0] < row[1] < row[2]
    for j in range(3):
        assert grid[0][j] > grid[1][j] > grid[2][j]


# --------------------------------------------------------------------------- Comps
def test_comps_valuation_math():
    r = comps_valuation(ebitda=1000, eps=5.0, net_debt=500, shares=100,
                        ev_ebitda_mult=8.0, pe_mult=12.0)
    assert r["implied_ev"] == pytest.approx(8000)
    assert r["value_per_share_ev_ebitda"] == pytest.approx((8000 - 500) / 100)
    assert r["value_per_share_pe"] == pytest.approx(60.0)
    assert r["midpoint"] == pytest.approx((75 + 60) / 2)


# --------------------------------------------------------------------------- Monte Carlo
def test_monte_carlo_reproducible_and_bounded():
    a = base_assumptions()
    r1 = monte_carlo(a, MonteCarloSpec(n=2000, seed=7))
    r2 = monte_carlo(a, MonteCarloSpec(n=2000, seed=7))
    assert r1["median"] == pytest.approx(r2["median"])      # deterministic with seed
    assert r1["p5"] < r1["median"] < r1["p95"]
    assert r1["n"] > 0
