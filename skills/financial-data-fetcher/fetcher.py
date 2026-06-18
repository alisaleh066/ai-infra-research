"""financial-data-fetcher — caching + no-fabrication helpers around the market-data MCPs.

The MCP calls themselves are made by the agent; this module standardises JSON caching, the
sourced/assumption tagging contract, and a price sanity check so no implausible value is ever
treated as fact. See SKILL.md.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Optional

# Repo-root/data  (this file lives at repo/skills/financial-data-fetcher/fetcher.py)
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _path(name: str) -> Path:
    return DATA_DIR / (name if name.endswith(".json") else f"{name}.json")


def load_cache(name: str) -> Optional[dict]:
    """Load a cached JSON object by name, or None if absent."""
    p = _path(name)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def save_cache(name: str, obj: Any) -> Path:
    """Persist a JSON-serialisable object to data/<name>.json."""
    p = _path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return p


def sourced(value: Any, source: str, retrieved: Optional[str] = None) -> dict:
    """Tag a fetched value with its provenance."""
    return {
        "value": value,
        "is_assumption": False,
        "source": source,
        "retrieved": retrieved or date.today().isoformat(),
    }


def assumption(value: Any, note: str) -> dict:
    """Tag a value that could not be fetched as a labelled, replaceable input."""
    return {"value": value, "is_assumption": True, "note": note}


def sanity_price(value: Optional[float], low: float, high: float) -> Optional[float]:
    """Return value if it is a plausible positive price within [low, high], else None.

    Used to reject implausible quotes (e.g. the FMP profile returned MU at $1,144).
    """
    try:
        v = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return v if (v > 0 and low <= v <= high) else None
