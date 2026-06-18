"use client";

import { tightnessColor } from "@/lib/format";

export default function CapitalFlow({
  years,
  shares,
  names,
}: {
  years: number[];
  shares: Record<string, number[]>;
  names: Record<string, string>;
}) {
  const ids = Object.keys(shares);
  const W = 640;
  const H = 280;
  const pad = { l: 36, r: 8, t: 12, b: 28 };
  const xOf = (i: number) => pad.l + (i / (years.length - 1)) * (W - pad.l - pad.r);
  const yOf = (v: number) => pad.t + (1 - v) * (H - pad.t - pad.b);

  // colour per layer by its average share rank (proxy for upstream tightness ordering)
  const colorById: Record<string, string> = {};
  ids.forEach((id, k) => {
    colorById[id] = tightnessColor(30 + (k / ids.length) * 60);
  });

  // build cumulative stacked areas
  const cum = years.map(() => 0);
  const areas = ids.map((id) => {
    const top = years.map((_, i) => cum[i] + shares[id][i]);
    const bottom = [...cum];
    years.forEach((_, i) => (cum[i] += shares[id][i]));
    const path =
      top.map((v, i) => `${i === 0 ? "M" : "L"}${xOf(i)},${yOf(v)}`).join(" ") +
      " " +
      bottom
        .map((v, i) => `L${xOf(years.length - 1 - i)},${yOf(bottom[years.length - 1 - i])}`)
        .join(" ") +
      " Z";
    return { id, path, mid: top[top.length - 1] - shares[id][years.length - 1] / 2 };
  });

  return (
    <div className="grid md:grid-cols-[1.6fr_1fr] gap-5 items-center">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Capital flow by layer over time">
        {[0, 0.25, 0.5, 0.75, 1].map((g) => (
          <g key={g}>
            <line x1={pad.l} x2={W - pad.r} y1={yOf(g)} y2={yOf(g)} stroke="#dcd5c5" strokeWidth={0.5} />
            <text x={pad.l - 5} y={yOf(g) + 3} fill="#8a93a6" fontSize="9" className="font-mono" textAnchor="end">
              {(g * 100).toFixed(0)}%
            </text>
          </g>
        ))}
        {areas.map((a) => (
          <path key={a.id} d={a.path} fill={colorById[a.id]} opacity={0.85} stroke="#f6f3ec" strokeWidth={0.5} />
        ))}
        {years.map((yr, i) => (
          <text key={yr} x={xOf(i)} y={H - 10} fill="#8a93a6" fontSize="10" className="font-mono" textAnchor="middle">
            {yr}
          </text>
        ))}
      </svg>
      <ul className="space-y-1.5">
        {ids.map((id) => (
          <li key={id} className="flex items-center gap-2 text-[12px]">
            <span className="inline-block w-3 h-3 rounded-sm" style={{ background: colorById[id] }} />
            <span className="text-ink-800">{names[id] ?? id}</span>
            <span className="ml-auto tnum text-slatey">
              {(shares[id][shares[id].length - 1] * 100).toFixed(0)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
