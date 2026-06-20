"""analysis.py — institutional financial-statement & quality analysis (the "best techniques").

Pure functions over the fundamentals dict from data.py (year-keyed concept series). Each technique
degrades gracefully: if the filing lacks an input, the metric returns None (flagged), never faked.

Techniques implemented (all named, citable):
  - Profitability/leverage ratios + DuPont ROE decomposition
  - ROIC vs WACC (value creation)
  - Piotroski F-Score (9-pt fundamental strength)
  - Altman Z-Score (distress risk)
  - Beneish M-Score (earnings-manipulation flag)
  - Sloan accrual ratio (earnings quality)
  - Reverse DCF (growth implied by the market price)
"""
from __future__ import annotations

from valuation import DCFAssumptions, enterprise_value


def v(fund: dict, concept: str, year: int):
    return fund.get(concept, {}).get(year)


# --------------------------------------------------------------------------- Recommendation
def recommend(rep: dict) -> dict:
    """Synthesize BUY / HOLD / SELL from valuation upside + quality/forensic scores.

    Transparent point system (every contribution is listed in 'rationale'). `rep` must contain the
    metric blocks plus 'upside' (DCF fair value / price - 1; may be None).
    """
    pts = 0
    rationale: list[str] = []

    def add(p, msg):
        nonlocal pts
        pts += p
        rationale.append(f"{'+' if p >= 0 else ''}{p}  {msg}")

    up = rep.get("upside")
    if up is not None:
        if up > 0.20: add(2, f"DCF upside {up:+.0%} (cheap vs intrinsic)")
        elif up > 0.0: add(1, f"DCF upside {up:+.0%} (modestly cheap)")
        elif up > -0.20: add(-1, f"DCF downside {up:+.0%} (slightly rich)")
        else: add(-2, f"DCF downside {up:+.0%} (expensive vs intrinsic)")

    rw = rep.get("roic_vs_wacc", {})
    if rw.get("creates_value") is True: add(1, "ROIC exceeds WACC (value-creating)")
    elif rw.get("value_spread") is not None: add(-1, "ROIC below WACC (value-destroying)")

    f = rep.get("piotroski", {}).get("score")
    if f is not None:
        if f >= 7: add(1, f"Piotroski F {f}/9 (strong)")
        elif f <= 3: add(-1, f"Piotroski F {f}/9 (weak)")

    az = rep.get("altman_z", {}).get("zone")
    if az == "safe": add(1, "Altman Z safe")
    elif az == "distress": add(-2, "Altman Z in distress zone")

    bm = rep.get("beneish_m", {}).get("flag")
    if bm == "possible manipulation": add(-2, "Beneish M flags earnings quality")
    elif bm == "clean": add(1, "Beneish M clean")

    sl = rep.get("sloan", {}).get("quality")
    if sl == "low": add(-1, "High accruals (low earnings quality)")

    if pts >= 4:
        rating = "BUY"
    elif pts <= -2:
        rating = "SELL"
    else:
        rating = "HOLD"
    return {"rating": rating, "score": pts, "rationale": rationale}


def _latest_two(fund: dict) -> tuple[int | None, int | None]:
    ys = fund["years"]
    return (ys[-1] if ys else None, ys[-2] if len(ys) > 1 else None)


def _safe(n, d):
    if n is None or d in (None, 0):
        return None
    return n / d


# --------------------------------------------------------------------------- Ratios + DuPont
def ratios(fund: dict) -> dict:
    y, _ = _latest_two(fund)
    rev = v(fund, "revenue", y)
    out = {
        "gross_margin": _safe(v(fund, "gross_profit", y), rev),
        "operating_margin": _safe(v(fund, "operating_income", y), rev),
        "net_margin": _safe(v(fund, "net_income", y), rev),
        "roa": _safe(v(fund, "net_income", y), v(fund, "total_assets", y)),
        "roe": _safe(v(fund, "net_income", y), v(fund, "equity", y)),
        "current_ratio": _safe(v(fund, "current_assets", y), v(fund, "current_liabilities", y)),
        "asset_turnover": _safe(rev, v(fund, "total_assets", y)),
    }
    debt = (v(fund, "long_term_debt", y) or 0) + (v(fund, "short_term_debt", y) or 0)
    out["debt_to_equity"] = _safe(debt, v(fund, "equity", y))
    ebitda = (v(fund, "operating_income", y) or 0) + (v(fund, "da", y) or 0)
    out["net_debt_to_ebitda"] = _safe(debt - (v(fund, "cash", y) or 0), ebitda)
    return out


def dupont(fund: dict) -> dict:
    """ROE = net margin x asset turnover x equity multiplier."""
    y, _ = _latest_two(fund)
    nm = _safe(v(fund, "net_income", y), v(fund, "revenue", y))
    at = _safe(v(fund, "revenue", y), v(fund, "total_assets", y))
    em = _safe(v(fund, "total_assets", y), v(fund, "equity", y))
    roe = nm * at * em if None not in (nm, at, em) else None
    return {"net_margin": nm, "asset_turnover": at, "equity_multiplier": em, "roe": roe}


def roic_vs_wacc(fund: dict, wacc: float, tax_rate: float = 0.21) -> dict:
    """ROIC = NOPAT / invested capital;  invested capital = debt + equity - cash."""
    y, _ = _latest_two(fund)
    ebit = v(fund, "operating_income", y)
    debt = (v(fund, "long_term_debt", y) or 0) + (v(fund, "short_term_debt", y) or 0)
    eq = v(fund, "equity", y)
    cash = v(fund, "cash", y) or 0
    invested = (debt + (eq or 0) - cash) if eq is not None else None
    nopat = ebit * (1 - tax_rate) if ebit is not None else None
    roic = _safe(nopat, invested)
    return {"roic": roic, "wacc": wacc,
            "value_spread": (roic - wacc) if roic is not None else None,
            "creates_value": (roic is not None and roic > wacc)}


# --------------------------------------------------------------------------- Piotroski F-Score
def piotroski_f(fund: dict) -> dict:
    y, p = _latest_two(fund)
    if p is None:
        return {"score": None, "max": 9, "note": "need 2 years", "signals": {}}
    s = {}
    ni = v(fund, "net_income", y); cfo = v(fund, "cfo", y)
    ta_y = v(fund, "total_assets", y); ta_p = v(fund, "total_assets", p)
    roa_y = _safe(ni, ta_y); roa_p = _safe(v(fund, "net_income", p), ta_p)
    s["positive_roa"] = (roa_y or -1) > 0
    s["positive_cfo"] = (cfo or -1) > 0
    s["rising_roa"] = (roa_y is not None and roa_p is not None and roa_y > roa_p)
    s["accruals_quality"] = (cfo is not None and ni is not None and ta_y and cfo / ta_y > ni / ta_y)
    # leverage: long-term debt / assets falling
    lev_y = _safe(v(fund, "long_term_debt", y), ta_y); lev_p = _safe(v(fund, "long_term_debt", p), ta_p)
    s["lower_leverage"] = (lev_y is not None and lev_p is not None and lev_y < lev_p)
    cr_y = _safe(v(fund, "current_assets", y), v(fund, "current_liabilities", y))
    cr_p = _safe(v(fund, "current_assets", p), v(fund, "current_liabilities", p))
    s["higher_current_ratio"] = (cr_y is not None and cr_p is not None and cr_y > cr_p)
    sh_y = v(fund, "shares", y); sh_p = v(fund, "shares", p)
    s["no_dilution"] = (sh_y is not None and sh_p is not None and sh_y <= sh_p * 1.001)
    gm_y = _safe(v(fund, "gross_profit", y), v(fund, "revenue", y))
    gm_p = _safe(v(fund, "gross_profit", p), v(fund, "revenue", p))
    s["higher_gross_margin"] = (gm_y is not None and gm_p is not None and gm_y > gm_p)
    at_y = _safe(v(fund, "revenue", y), ta_y); at_p = _safe(v(fund, "revenue", p), ta_p)
    s["higher_asset_turnover"] = (at_y is not None and at_p is not None and at_y > at_p)
    score = sum(1 for x in s.values() if x)
    return {"score": score, "max": 9, "signals": s,
            "verdict": "strong" if score >= 7 else "weak" if score <= 3 else "middling"}


# --------------------------------------------------------------------------- Altman Z-Score
def altman_z(fund: dict, market_cap: float | None) -> dict:
    """Original Altman Z (manufacturer). >2.99 safe, 1.81-2.99 grey, <1.81 distress."""
    y, _ = _latest_two(fund)
    ta = v(fund, "total_assets", y)
    tl = v(fund, "total_liabilities", y)
    wc = (v(fund, "current_assets", y) or 0) - (v(fund, "current_liabilities", y) or 0)
    re = v(fund, "retained_earnings", y)
    ebit = v(fund, "operating_income", y)
    sales = v(fund, "revenue", y)
    if None in (ta, tl, re, ebit, sales) or not ta or market_cap is None or not tl:
        return {"z": None, "note": "missing inputs (or no market cap)"}
    z = (1.2 * wc / ta + 1.4 * re / ta + 3.3 * ebit / ta
         + 0.6 * market_cap / tl + 1.0 * sales / ta)
    zone = "safe" if z > 2.99 else "distress" if z < 1.81 else "grey"
    return {"z": round(z, 2), "zone": zone}


# --------------------------------------------------------------------------- Beneish M-Score
def beneish_m(fund: dict) -> dict:
    """8-variable Beneish M-Score. > -1.78 suggests possible earnings manipulation."""
    y, p = _latest_two(fund)
    if p is None:
        return {"m": None, "note": "need 2 years"}
    g = lambda c, yr: v(fund, c, yr)  # noqa: E731
    try:
        rec_y, rec_p = g("receivables", y), g("receivables", p)
        sale_y, sale_p = g("revenue", y), g("revenue", p)
        gp_y, gp_p = g("gross_profit", y), g("gross_profit", p)
        ca_y, ca_p = g("current_assets", y), g("current_assets", p)
        ppe_y, ppe_p = g("ppe_net", y), g("ppe_net", p)
        ta_y, ta_p = g("total_assets", y), g("total_assets", p)
        da_y, da_p = g("da", y), g("da", p)
        sga_y, sga_p = g("sga", y), g("sga", p)
        tl_y, tl_p = g("total_liabilities", y), g("total_liabilities", p)
        ni_y, cfo_y = g("net_income", y), g("cfo", y)
        if None in (rec_y, rec_p, sale_y, sale_p, gp_y, gp_p, ca_y, ca_p, ppe_y, ppe_p,
                    ta_y, ta_p, ni_y, cfo_y):
            return {"m": None, "note": "missing inputs"}
        dsri = (rec_y / sale_y) / (rec_p / sale_p)
        gmi = (gp_p / sale_p) / (gp_y / sale_y)
        aqi_y = 1 - (ca_y + ppe_y) / ta_y
        aqi_p = 1 - (ca_p + ppe_p) / ta_p
        aqi = aqi_y / aqi_p if aqi_p else 1.0
        sgi = sale_y / sale_p
        depi = (da_p / (da_p + ppe_p)) / (da_y / (da_y + ppe_y)) if (da_y and da_p) else 1.0
        sgai = (sga_y / sale_y) / (sga_p / sale_p) if (sga_y and sga_p) else 1.0
        lvgi = (tl_y / ta_y) / (tl_p / ta_p) if (tl_y and tl_p) else 1.0
        tata = (ni_y - cfo_y) / ta_y
        m = (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi
             + 0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)
        return {"m": round(m, 2), "flag": "possible manipulation" if m > -1.78 else "clean"}
    except (TypeError, ZeroDivisionError):
        return {"m": None, "note": "could not compute"}


# --------------------------------------------------------------------------- Sloan accruals
def sloan_accruals(fund: dict) -> dict:
    """(Net income - CFO) / total assets. High positive = low earnings quality."""
    y, _ = _latest_two(fund)
    ni, cfo, ta = v(fund, "net_income", y), v(fund, "cfo", y), v(fund, "total_assets", y)
    ratio = _safe((ni - cfo) if (ni is not None and cfo is not None) else None, ta)
    if ratio is None:
        return {"accrual_ratio": None}
    return {"accrual_ratio": round(ratio, 4),
            "quality": "low" if ratio > 0.10 else "high" if ratio < 0 else "ok"}


# --------------------------------------------------------------------------- Reverse DCF
def reverse_dcf(fund: dict, price: float | None, wacc: float, tax_rate: float = 0.21) -> dict:
    """Solve for the flat 5-yr revenue growth the current price implies (other drivers from history)."""
    if not price:
        return {"implied_growth": None, "note": "no price"}
    y, _ = _latest_two(fund)
    rev = v(fund, "revenue", y)
    shares = v(fund, "shares", y)
    if not rev or not shares:
        return {"implied_growth": None, "note": "missing revenue/shares"}
    ys = fund["years"]
    def wavg(num):
        ns = [v(fund, num, k) for k in ys if v(fund, num, k) is not None and v(fund, "revenue", k)]
        ds = [v(fund, "revenue", k) for k in ys if v(fund, num, k) is not None and v(fund, "revenue", k)]
        return sum(ns) / sum(ds) if ds else None
    margin = wavg("operating_income") or 0.15
    da_pct = wavg("da") or 0.05
    capex_pct = abs(wavg("capex") or 0.05)
    capex_pct = (capex_pct + da_pct) / 2
    debt = (v(fund, "long_term_debt", y) or 0) + (v(fund, "short_term_debt", y) or 0)
    cash = v(fund, "cash", y) or 0

    def value_at(growth: float) -> float:
        a = DCFAssumptions(
            base_revenue=rev, rev_growth=[growth] * 5, ebit_margin=[margin] * 5,
            tax_rate=tax_rate, da_pct_rev=da_pct, capex_pct_rev=capex_pct,
            nwc_pct_rev_change=0.05, terminal_growth=min(0.025, wacc - 0.005),
            risk_free=0.043, erp=0.05, beta=1.0, pretax_kd=0.05,
            equity_value=price * shares, debt_value=debt, cash=cash, shares=shares)
        return enterprise_value(a, wacc_rate=wacc)["value_per_share"]

    lo, hi = -0.20, 0.60
    if (value_at(lo) - price) * (value_at(hi) - price) > 0:
        return {"implied_growth": None, "note": "price outside solvable growth band"}
    for _ in range(100):
        mid = (lo + hi) / 2
        if (value_at(mid) - price) * (value_at(lo) - price) <= 0:
            hi = mid
        else:
            lo = mid
    return {"implied_growth": round((lo + hi) / 2, 4), "wacc_used": wacc,
            "note": "flat 5-yr revenue growth implied by the current price"}
