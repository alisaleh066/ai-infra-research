"use client";

import { useMemo } from "react";
import { usd } from "@/lib/format";

export default function Histogram({
  samples,
  dcf,
  market,
  bins = 48,
}: {
  samples: number[];
  dcf: number;
  market: number;
  bins?: number;
}) {
  const { bars, max, lo, hi } = useMemo(() => {
    const lo = Math.min(...samples);
    const hi = Math.max(...samples);
    const width = (hi - lo) / bins || 1;
    const counts = new Array(bins).fill(0);
    samples.forEach((s) => {
      const idx = Math.min(bins - 1, Math.floor((s - lo) / width));
      counts[idx]++;
    });
    return { bars: counts, max: Math.max(...counts), lo, hi };
  }, [samples, bins]);

  const W = 640;
  const H = 240;
  const pad = { l: 8, r: 8, t: 12, b: 28 };
  const bw = (W - pad.l - pad.r) / bins;
  const xOf = (v: number) => pad.l + ((v - lo) / (hi - lo)) * (W - pad.l - pad.r);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Monte Carlo distribution">
      {bars.map((c, i) => {
        const h = (c / max) * (H - pad.t - pad.b);
        return (
          <rect
            key={i}
            x={pad.l + i * bw + 0.5}
            y={H - pad.b - h}
            width={bw - 1}
            height={h}
            fill="#5b8def"
            opacity={0.85}
          />
        );
      })}
      {/* DCF base line */}
      <line x1={xOf(dcf)} x2={xOf(dcf)} y1={pad.t} y2={H - pad.b} stroke="#0d1422" strokeWidth={1.5} strokeDasharray="4 3" />
      <text x={xOf(dcf)} y={pad.t + 2} fill="#0d1422" className="font-mono" fontSize="10" textAnchor="middle">
        DCF {usd(dcf)}
      </text>
      {/* Market line */}
      <line x1={xOf(market)} x2={xOf(market)} y1={pad.t} y2={H - pad.b} stroke="#e0635a" strokeWidth={1.5} />
      <text x={xOf(market)} y={H - pad.b + 18} fill="#e0635a" className="font-mono" fontSize="10" textAnchor="middle">
        Mkt {usd(market)}
      </text>
      {/* axis ticks */}
      {[lo, (lo + hi) / 2, hi].map((v, i) => (
        <text key={i} x={xOf(v)} y={H - 6} fill="#8a93a6" className="font-mono" fontSize="9" textAnchor="middle">
          {usd(v)}
        </text>
      ))}
    </svg>
  );
}
