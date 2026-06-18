---
name: model-auditor
description: Audit a generated .xlsx workbook for formula errors, broken references and circularity, returning a pass/fail report. Use as a verification gate after building any Excel model, before marking a project done.
---

# model-auditor

## Purpose
Enforce the "**zero spreadsheet formula errors**" engineering gate. Scans every sheet/cell of an
`.xlsx` for Excel error tokens, broken references, and self-referential (circular) formulas, and
prints a structured pass/fail report. Run it in CI / the Verifier step on every workbook.

## What it checks
- **Error literals** in cached values or formula text: `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`,
  `#N/A`, `#NULL!`, `#NUM!`.
- **Broken references** — formulas containing `#REF!` (deleted cells/ranges).
- **Direct circular references** — a formula on cell `X` that references `X` itself.
- **Coverage stats** — sheets, populated cells, formula count (a model with zero formulas is
  flagged as suspicious — it likely hard-coded values instead of linking them).

## Usage
```bash
python skills/model-auditor/auditor.py path/to/model.xlsx
# exit code 0 = pass (zero errors), 1 = errors found
```
Or import `audit_workbook(path) -> dict` and assert `report["passed"]` in a pytest.

## Limitations (stated honestly)
openpyxl does not recalculate formulas, so this is a **static** audit: it catches error tokens,
`#REF!` breaks and direct circularity. For full numeric recalculation, open the file in Excel /
LibreOffice. The model builders in this repo are written so formulas link correctly by
construction; this auditor guards against regressions.
