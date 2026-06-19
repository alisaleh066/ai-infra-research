"""data.py — keyless live financial data for ANY US-listed ticker.

No API key, no MCP. Pure `requests`:
  - Fundamentals: SEC EDGAR REST API (company_tickers + companyfacts XBRL). Audited 10-K values.
  - Prices: Yahoo Finance chart API (keyless JSON). Stooq is no longer usable from scripts
    (it serves a JavaScript anti-bot wall), so Yahoo's public chart endpoint is the default.

EDGAR REQUIRES a descriptive User-Agent header (name + email) or it returns 403 — set
SEC_EDGAR_USER_AGENT in the environment, or edit DEFAULT_UA below. Responses are cached under
cache/ so re-runs are fast and work offline after the first fetch.

Honesty rule: any concept that cannot be found is returned as a flagged ASSUMPTION (None value),
never fabricated.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

import requests

CACHE = Path(__file__).resolve().parent / "cache"
CACHE.mkdir(exist_ok=True)

# Override with env var SEC_EDGAR_USER_AGENT="Your Name your@email.com"
DEFAULT_UA = os.environ.get(
    "SEC_EDGAR_USER_AGENT", "projectsf equity-valuation research contact@example.com"
)
HEADERS = {"User-Agent": DEFAULT_UA, "Accept-Encoding": "gzip, deflate"}
# Yahoo's public endpoints expect a browser-like UA.
YAHOO_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
TIMEOUT = 30

# XBRL tag fallback lists per concept (companies tag the same line differently).
TAGS = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "eps_diluted": ["EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted"],
    "da": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAmortizationAndAccretionNet",
        "DepreciationAndAmortization",
    ],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    "long_term_debt": ["LongTermDebtNoncurrent", "LongTermDebt"],
    "short_term_debt": ["LongTermDebtCurrent", "DebtCurrent"],
    "shares": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "WeightedAverageNumberOfSharesOutstandingBasic",
        "CommonStockSharesOutstanding",
    ],
}


def _get(url: str, *, is_json: bool = True, cache_name: Optional[str] = None,
         max_age_h: float = 24.0):
    """GET with EDGAR-friendly headers + on-disk cache."""
    if cache_name:
        p = CACHE / cache_name
        if p.exists() and (time.time() - p.stat().st_mtime) < max_age_h * 3600:
            raw = p.read_text(encoding="utf-8")
            return json.loads(raw) if is_json else raw
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    text = r.text
    if cache_name:
        (CACHE / cache_name).write_text(text, encoding="utf-8")
    return r.json() if is_json else text


def ticker_to_cik(ticker: str) -> Optional[str]:
    """Map a ticker to a zero-padded 10-digit CIK via SEC's official mapping file."""
    data = _get("https://www.sec.gov/files/company_tickers.json",
                cache_name="company_tickers.json", max_age_h=168)
    t = ticker.upper().strip()
    for row in data.values():
        if row.get("ticker", "").upper() == t:
            return str(row["cik_str"]).zfill(10)
    return None


def _annual_series(facts: dict, tag: str) -> dict[int, float]:
    """Extract {fiscal_year: value} for a us-gaap tag from companyfacts.

    Keyed by each value's PERIOD-END year (not the filing's fiscal year — otherwise the three
    comparative years inside one 10-K collapse onto a single year). Flow concepts are restricted to
    ~annual durations; per period we keep the value from the latest filing (handles restatements).
    """
    from datetime import date
    node = facts.get("facts", {}).get("us-gaap", {}).get(tag)
    if not node:
        return {}
    best: dict[int, tuple[str, float]] = {}  # year -> (filed_date, value)
    for unit_vals in node.get("units", {}).values():
        for item in unit_vals:
            end = item.get("end")
            val = item.get("val")
            form = item.get("form", "")
            if end is None or val is None or not form.startswith("10-K"):
                continue
            if "start" in item:  # flow concept — require a full-year duration
                try:
                    dur = (date.fromisoformat(end) - date.fromisoformat(item["start"])).days
                except ValueError:
                    continue
                if not 330 <= dur <= 400:
                    continue
            year = int(end[:4])
            filed = item.get("filed", "")
            if year not in best or filed > best[year][0]:
                best[year] = (filed, val)
    return {y: v for y, (_, v) in best.items()}


def _pick(facts: dict, concept: str) -> dict[int, float]:
    """Merge all fallback tags for a concept, preferring the tag with the most recent coverage.

    Companies switch XBRL tags over time (e.g. NVDA reports recent revenue under `Revenues` but
    older years under `RevenueFromContractWithCustomerExcludingAssessedTax`). We take the most-recent
    tag's years first, then backfill earlier years from older tags.
    """
    series = [(tag, _annual_series(facts, tag)) for tag in TAGS[concept]]
    series = [(t, s) for t, s in series if s]
    if not series:
        return {}
    series.sort(key=lambda ts: max(ts[1]), reverse=True)  # most-recent coverage first
    merged: dict[int, float] = {}
    for _, s in series:
        for year, val in s.items():
            merged.setdefault(year, val)  # earlier (more recent) tag wins on conflicts
    return merged


def fetch_fundamentals(ticker: str) -> dict:
    """Return audited annual fundamentals for the last up-to-4 fiscal years + flags."""
    cik = ticker_to_cik(ticker)
    if cik is None:
        raise ValueError(f"Ticker '{ticker}' not found in SEC ticker map (US-listed only).")
    facts = _get(
        f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
        cache_name=f"facts_{cik}.json", max_age_h=24,
    )
    name = facts.get("entityName", ticker.upper())

    concepts = {c: _pick(facts, c) for c in TAGS}
    # D&A fallback: some filers (e.g. MSFT) report Depreciation and Amortization separately.
    if not concepts["da"]:
        dep = _annual_series(facts, "Depreciation")
        amort = _annual_series(facts, "AmortizationOfIntangibleAssets")
        if dep or amort:
            concepts["da"] = {y: dep.get(y, 0) + amort.get(y, 0)
                              for y in set(dep) | set(amort)}
    # union of fiscal years we actually have for revenue (the anchor)
    years = sorted(concepts["revenue"].keys())[-4:] if concepts["revenue"] else []
    flags: list[str] = []

    def series(concept: str) -> dict:
        s = concepts[concept]
        if not s:
            flags.append(concept)
        return {y: s.get(y) for y in years}

    fund = {
        "ticker": ticker.upper(),
        "name": name,
        "cik": cik,
        "years": years,
        "units": "USD (absolute)",
        "source": "SEC EDGAR companyfacts (10-K, us-gaap)",
        "revenue": series("revenue"),
        "operating_income": series("operating_income"),
        "net_income": series("net_income"),
        "eps_diluted": series("eps_diluted"),
        "da": series("da"),
        "capex": series("capex"),
        "cash": series("cash"),
        "long_term_debt": series("long_term_debt"),
        "short_term_debt": series("short_term_debt"),
        "shares": series("shares"),
        "missing_flags": flags,
    }
    return fund


def fetch_price(ticker: str) -> dict:
    """Latest price + ~2y daily closes from Yahoo's keyless chart API. Flagged None on failure."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker.upper()}"
           f"?range=2y&interval=1d")
    try:
        p = CACHE / f"price_{ticker.lower()}.json"
        if p.exists() and (time.time() - p.stat().st_mtime) < 12 * 3600:
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            r = requests.get(url, headers=YAHOO_HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            p.write_text(json.dumps(data), encoding="utf-8")
        res = data["chart"]["result"][0]
        meta = res["meta"]
        price = meta.get("regularMarketPrice")
        ts = res.get("timestamp", []) or []
        closes_raw = res["indicators"]["quote"][0].get("close", []) or []
        from datetime import datetime, timezone
        history = [
            (datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d"), float(c))
            for t, c in zip(ts, closes_raw) if c is not None
        ]
        if price is None and history:
            price = history[-1][1]
        return {"price": price, "currency": meta.get("currency", "USD"),
                "history": history, "flag": None if price else "price unavailable"}
    except Exception as e:  # noqa: BLE001 - degrade gracefully, never fabricate
        return {"price": None, "currency": "USD", "history": [],
                "flag": f"price fetch failed: {e}"}


if __name__ == "__main__":
    import sys
    tk = sys.argv[1] if len(sys.argv) > 1 else "MU"
    f = fetch_fundamentals(tk)
    p = fetch_price(tk)
    print(f"{f['name']} ({f['ticker']}) CIK {f['cik']}  years={f['years']}")
    print(f"  revenue: {f['revenue']}")
    print(f"  op income: {f['operating_income']}")
    print(f"  price: {p['price']}  flag={p['flag']}  history pts={len(p['history'])}")
    if f["missing_flags"]:
        print(f"  MISSING (flagged assumptions): {f['missing_flags']}")
