"""comps_live.py — real, live comparable-company multiples for a peer set.

Pulls each peer's latest EBITDA / revenue / EPS (SEC EDGAR) and market cap (Yahoo price x EDGAR
shares), computes EV/EBITDA, EV/Sales and P/E, and returns the peer-set medians. This replaces the
placeholder multiples in value.py with multiples derived from live data — what an analyst defends.

Usage:
    python comps_live.py MU WDC STX INTC AMD TXN
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass

import data as datamod

# Default peer sets by theme (US-listed; EDGAR-covered). Edit freely.
PEER_SETS = {
    "MU": ["WDC", "STX", "INTC", "TXN", "AMD", "NVDA", "AVGO"],
}


@dataclass
class PeerMultiple:
    ticker: str
    ev_ebitda: float | None
    ev_sales: float | None
    pe: float | None
    flag: str | None = None


def _latest(series: dict, years: list[int]):
    for y in reversed(years):
        if series.get(y) is not None:
            return series[y]
    return None


def peer_multiple(ticker: str) -> PeerMultiple:
    try:
        f = datamod.fetch_fundamentals(ticker)
        p = datamod.fetch_price(ticker)
        yrs = f["years"]
        rev = _latest(f["revenue"], yrs)
        opinc = _latest(f["operating_income"], yrs)
        da = _latest(f["da"], yrs) or 0
        eps = _latest(f["eps_diluted"], yrs)
        shares = _latest(f["shares"], yrs)
        cash = _latest(f["cash"], yrs) or 0
        debt = (_latest(f["long_term_debt"], yrs) or 0) + (_latest(f["short_term_debt"], yrs) or 0)
        price = p["price"]
        if not (price and shares and rev):
            return PeerMultiple(ticker, None, None, None, "insufficient data")
        ebitda = (opinc or 0) + da
        mktcap = price * shares
        ev = mktcap + debt - cash
        return PeerMultiple(
            ticker,
            ev_ebitda=round(ev / ebitda, 2) if ebitda > 0 else None,
            ev_sales=round(ev / rev, 2) if rev > 0 else None,
            pe=round(price / eps, 2) if eps and eps > 0 else None,
        )
    except Exception as e:  # noqa: BLE001
        return PeerMultiple(ticker, None, None, None, f"fetch failed: {e}")


def comps_table(target: str, peers: list[str] | None = None) -> dict:
    peers = peers or PEER_SETS.get(target.upper(), [])
    peers = [p for p in peers if p.upper() != target.upper()]
    rows = [peer_multiple(p) for p in peers]
    valid = [r for r in rows if r.ev_ebitda or r.pe]

    def med(attr):
        vals = [getattr(r, attr) for r in valid if getattr(r, attr) is not None]
        return round(statistics.median(vals), 2) if vals else None

    return {
        "target": target.upper(),
        "peers": [r.__dict__ for r in rows],
        "median_ev_ebitda": med("ev_ebitda"),
        "median_ev_sales": med("ev_sales"),
        "median_pe": med("pe"),
        "n_valid": len(valid),
    }


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "MU"
    peers = sys.argv[2:] or None
    t = comps_table(target, peers)
    print(f"Peer comps for {t['target']}  (median EV/EBITDA {t['median_ev_ebitda']}x, "
          f"EV/Sales {t['median_ev_sales']}x, P/E {t['median_pe']}x; n={t['n_valid']})")
    print(f"{'Peer':<7}{'EV/EBITDA':>11}{'EV/Sales':>10}{'P/E':>9}  flag")
    for r in t["peers"]:
        print(f"{r['ticker']:<7}{str(r['ev_ebitda']):>11}{str(r['ev_sales']):>10}"
              f"{str(r['pe']):>9}  {r['flag'] or ''}")
