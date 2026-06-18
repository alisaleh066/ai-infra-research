"use client";

import { usd } from "@/lib/format";

interface Bar {
  label: string;
  low: number;
  high: number;
  point?: number;
  flag?: boolean;
}

export default function FootballField({
  bars,
  market,
}: {
  bars: Bar[];
  market: number;
}) {
  const all = bars.flatMap((b) => [b.low, b.high, b.point ?? b.low]).concat(market);
  const lo = Math.min(...all) * 0.92;
  const hi = Math.max(...all) * 1.05;
  const W = 640;
  const rowH = 46;
  const H = bars.length * rowH + 34;
  const padL = 150;
  const padR = 16;
  const xOf = (v: number) => padL + ((v - lo) / (hi - lo)) * (W - padL - padR);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Valuation football field">
      {/* market reference line */}
      <line x1={xOf(market)} x2={xOf(market)} y1={6} y2={H - 22} stroke="#e0635a" strokeWidth={1.5} />
      <text x={xOf(market)} y={H - 8} fill="#e0635a" fontSize="10" className="font-mono" textAnchor="middle">
        Market {usd(market)}
      </text>
      {bars.map((b, i) => {
        const y = 14 + i * rowH;
        return (
          <g key={b.label}>
            <text x={8} y={y + 14} fill="#1d2c44" fontSize="12" className="font-sans">
              {b.label}
            </text>
            {b.flag && (
              <text x={8} y={y + 28} fill="#5b8def" fontSize="9" className="font-mono">
                ASSUMPTION
              </text>
            )}
            <rect
              x={xOf(b.low)}
              y={y}
              width={Math.max(2, xOf(b.high) - xOf(b.low))}
              height={20}
              rx={2}
              fill="#c69749"
              opacity={0.5}
            />
            <text x={xOf(b.low) - 4} y={y + 14} fill="#9c7430" fontSize="10" className="font-mono" textAnchor="end">
              {usd(b.low)}
            </text>
            <text x={xOf(b.high) + 4} y={y + 14} fill="#9c7430" fontSize="10" className="font-mono">
              {usd(b.high)}
            </text>
            {b.point !== undefined && (
              <line
                x1={xOf(b.point)}
                x2={xOf(b.point)}
                y1={y - 2}
                y2={y + 22}
                stroke="#0d1422"
                strokeWidth={2}
              />
            )}
          </g>
        );
      })}
    </svg>
  );
}
