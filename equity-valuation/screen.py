"""screen.py — run the research workup across a watchlist and rank it into a league table.

    python screen.py                 # default AI-infrastructure watchlist
    python screen.py NVDA MU AVGO    # your own list

Reuses analyze.py per name (no per-ticker files), then ranks by the composite recommendation
score. Writes output/screen.csv. US 10-K filers only (foreign ADRs come back as n/a). Not advice.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import analyze as analyzemod

OUT = Path(__file__).resolve().parent / "output"

# Default: the AI-infrastructure chain (US-listed; some ADRs will be n/a on 10-K data).
WATCHLIST = ["NVDA", "AMD", "AVGO", "MU", "INTC", "AMKR", "QCOM", "TXN",
             "MSFT", "GOOGL", "VST", "CEG", "GEV", "ETN", "FCX", "CCJ"]


def _rank(rows: list[dict]) -> list[dict]:
    """Sort by recommendation score desc, then DCF upside desc (None last)."""
    return sorted(
        rows,
        key=lambda r: (r.get("score") if r.get("score") is not None else -99,
                       r.get("upside") if r.get("upside") is not None else -99),
        reverse=True,
    )


def screen(tickers: list[str]) -> list[dict]:
    OUT.mkdir(exist_ok=True)
    rows = []
    for t in tickers:
        try:
            r = analyzemod.analyze(t, write=False, quiet=True)
            rows.append({
                "ticker": r["ticker"], "rating": r["recommendation"]["rating"],
                "score": r["recommendation"]["score"],
                "roic": r["roic_vs_wacc"].get("roic"),
                "f_score": r["piotroski"].get("score"),
                "altman_z": r["altman_z"].get("z"),
                "upside": r.get("upside"),
            })
            print(f"  {t:<6} {r['recommendation']['rating']:<5} "
                  f"score {r['recommendation']['score']:+d}")
        except Exception as e:  # noqa: BLE001
            rows.append({"ticker": t, "rating": "n/a", "score": None, "roic": None,
                         "f_score": None, "altman_z": None, "upside": None, "flag": str(e)[:40]})
            print(f"  {t:<6} n/a  ({str(e)[:40]})")
    ranked = _rank(rows)

    with (OUT / "screen.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["Rank", "Ticker", "Rating", "Score", "ROIC", "F-Score", "Altman Z", "DCF upside"])
        for i, r in enumerate(ranked, 1):
            w.writerow([i, r["ticker"], r["rating"], r["score"],
                        f"{r['roic']:.1%}" if r["roic"] is not None else "",
                        r["f_score"], r["altman_z"],
                        f"{r['upside']:.1%}" if r["upside"] is not None else ""])
    return ranked


def main() -> None:
    tickers = [t.upper() for t in sys.argv[1:]] or WATCHLIST
    print(f"Screening {len(tickers)} names...\n")
    ranked = screen(tickers)
    print("\nLEAGUE TABLE (best composite first)")
    print(f"  {'#':<3}{'Ticker':<8}{'Rating':<7}{'Score':>6}{'ROIC':>8}{'F':>4}{'AltZ':>7}{'Upside':>9}")
    for i, r in enumerate(ranked, 1):
        roic = f"{r['roic']*100:.0f}%" if r["roic"] is not None else "n/a"
        up = f"{r['upside']*100:.0f}%" if r["upside"] is not None else "n/a"
        z = f"{r['altman_z']:.1f}" if r["altman_z"] is not None else "n/a"
        sc = f"{r['score']:+d}" if r["score"] is not None else "n/a"
        print(f"  {i:<3}{r['ticker']:<8}{r['rating']:<7}{sc:>6}{roic:>8}"
              f"{str(r['f_score'] if r['f_score'] is not None else 'n/a'):>4}{z:>7}{up:>9}")
    print(f"\nWrote: {OUT/'screen.csv'}")


if __name__ == "__main__":
    main()
