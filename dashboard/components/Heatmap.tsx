"use client";

import { useState } from "react";
import { pct, usd } from "@/lib/format";

type Fmt = "pct" | "pct0" | "usd";

const FMT: Record<Fmt, (v: number) => string> = {
  pct: (v) => pct(v, 1),
  pct0: (v) => pct(v, 0),
  usd: (v) => usd(v),
};

export default function Heatmap({
  rows,
  cols,
  grid,
  rowLabel,
  colLabel,
  rowFmt,
  colFmt,
  cellFmt,
  baseRow,
  baseCol,
}: {
  rows: number[];
  cols: number[];
  grid: number[][];
  rowLabel: string;
  colLabel: string;
  rowFmt: Fmt;
  colFmt: Fmt;
  cellFmt: Fmt;
  baseRow?: number;
  baseCol?: number;
}) {
  const fmtRow = FMT[rowFmt];
  const fmtCol = FMT[colFmt];
  const fmtCell = FMT[cellFmt];
  const [hover, setHover] = useState<{ i: number; j: number } | null>(null);
  const flat = grid.flat().filter((v) => isFinite(v));
  const min = Math.min(...flat);
  const max = Math.max(...flat);
  const color = (v: number) => {
    if (!isFinite(v)) return "#ece7db";
    const t = (v - min) / (max - min || 1);
    const lo = [236, 231, 219];
    const hi = [158, 116, 48];
    const m = lo.map((l, k) => Math.round(l + (hi[k] - l) * t));
    return `rgb(${m[0]},${m[1]},${m[2]})`;
  };

  return (
    <div className="overflow-x-auto">
      <div className="text-center eyebrow mb-1">{colLabel} →</div>
      <table className="border-collapse mx-auto">
        <thead>
          <tr>
            <th className="text-[10px] font-mono text-slatey p-1 align-bottom">
              {rowLabel} ↓
            </th>
            {cols.map((c, j) => (
              <th key={j} className="text-[11px] font-mono text-ink-700 p-1 font-500">
                {fmtCol(c)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {grid.map((row, i) => (
            <tr key={i}>
              <td className="text-[11px] font-mono text-ink-700 p-1 pr-2 text-right font-500">
                {fmtRow(rows[i])}
              </td>
              {row.map((v, j) => {
                const isBase = rows[i] === baseRow && cols[j] === baseCol;
                const isHover = hover?.i === i && hover?.j === j;
                return (
                  <td
                    key={j}
                    onMouseEnter={() => setHover({ i, j })}
                    onMouseLeave={() => setHover(null)}
                    className="relative"
                    style={{ background: color(v), padding: 0 }}
                  >
                    <div
                      className={`w-[58px] h-[38px] flex items-center justify-center text-[11px] tnum ${
                        (v - min) / (max - min || 1) > 0.6 ? "text-paper" : "text-ink-900"
                      } ${isBase ? "ring-2 ring-ink-900 ring-inset" : ""} ${
                        isHover ? "outline outline-1 outline-gold-deep" : ""
                      }`}
                    >
                      {isFinite(v) ? fmtCell(v) : "—"}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
