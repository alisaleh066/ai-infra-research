"""model-auditor — static audit of an .xlsx for formula errors, broken refs and circularity.

Usage:
    python skills/model-auditor/auditor.py path/to/model.xlsx
Exit code 0 = pass (zero errors), 1 = errors found. See SKILL.md for limitations.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from openpyxl import load_workbook

ERROR_TOKENS = ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A", "#NULL!", "#NUM!")
_CELL_RE = re.compile(r"\$?([A-Z]{1,3})\$?(\d+)")
# Sheet-qualified references (Sheet!A1 or 'Sheet Name'!A1, incl. ranges) — these point at
# OTHER sheets and must be removed before the same-sheet circular-reference check.
_CROSS_SHEET_RE = re.compile(
    r"(?:'[^']*'|[A-Za-z_][A-Za-z0-9.]*)!\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?"
)


def audit_workbook(path: str | Path) -> dict:
    path = Path(path)
    wb = load_workbook(path, data_only=False)
    errors: list[str] = []
    formula_count = 0
    cell_count = 0

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                val = cell.value
                if val is None:
                    continue
                cell_count += 1
                text = str(val)

                # error tokens anywhere (cached value or formula text)
                for tok in ERROR_TOKENS:
                    if tok in text:
                        errors.append(f"{ws.title}!{cell.coordinate}: contains {tok} -> {text!r}")

                # formulas
                if isinstance(val, str) and val.startswith("="):
                    formula_count += 1
                    # direct circular reference: formula references its own coordinate.
                    # Strip cross-sheet references first so Sheet!A1 doesn't false-positive.
                    local = _CROSS_SHEET_RE.sub("", val.upper())
                    refs = {f"{c}{r}" for c, r in _CELL_RE.findall(local)}
                    if cell.coordinate.upper() in refs:
                        errors.append(
                            f"{ws.title}!{cell.coordinate}: circular self-reference -> {val!r}"
                        )

    passed = len(errors) == 0 and formula_count > 0
    return {
        "file": str(path),
        "passed": passed,
        "sheets": [ws.title for ws in wb.worksheets],
        "cells_populated": cell_count,
        "formula_count": formula_count,
        "errors": errors,
        "warning": None if formula_count > 0 else "No formulas found — model may be hard-coded.",
    }


def _print_report(report: dict) -> None:
    print(f"model-auditor: {report['file']}")
    print(f"  sheets         : {', '.join(report['sheets'])}")
    print(f"  cells populated: {report['cells_populated']}")
    print(f"  formulas       : {report['formula_count']}")
    if report["warning"]:
        print(f"  WARNING        : {report['warning']}")
    if report["errors"]:
        print(f"  ERRORS ({len(report['errors'])}):")
        for e in report["errors"]:
            print(f"    - {e}")
    print(f"  RESULT         : {'PASS' if report['passed'] else 'FAIL'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python auditor.py path/to/model.xlsx")
        raise SystemExit(2)
    rep = audit_workbook(sys.argv[1])
    _print_report(rep)
    raise SystemExit(0 if rep["passed"] else 1)
