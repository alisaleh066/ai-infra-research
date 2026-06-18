"use client";

import { useMemo, useState } from "react";
import { gbp, num, pct } from "@/lib/format";
import {
  Baselines,
  Coefficients,
  Deal,
  Drivers,
  simulate,
} from "@/lib/reSimulator";

interface Range {
  min: number;
  max: number;
  step: number;
  unit: string;
  label: string;
}

export default function RoiSimulator({
  deal,
  baselines,
  coefficients,
  defaultDrivers,
  ranges,
}: {
  deal: Deal;
  baselines: Baselines;
  coefficients: Coefficients;
  defaultDrivers: Drivers;
  ranges: Record<string, Range>;
}) {
  const [drivers, setDrivers] = useState<Drivers>(defaultDrivers);
  const keys: (keyof Drivers)[] = [
    "net_migration",
    "household_formation",
    "completions",
    "employment_rate",
    "bank_rate_pct",
  ];

  const res = useMemo(
    () => simulate(deal, drivers, baselines, coefficients),
    [deal, drivers, baselines, coefficients]
  );
  const baseRes = useMemo(
    () => simulate(deal, defaultDrivers, baselines, coefficients),
    [deal, defaultDrivers, baselines, coefficients]
  );

  const set = (k: keyof Drivers, v: number) =>
    setDrivers((d) => ({ ...d, [k]: v }));
  const reset = () => setDrivers(defaultDrivers);

  const fmtDriver = (k: keyof Drivers, v: number) =>
    k === "employment_rate" || k === "bank_rate_pct"
      ? `${v.toFixed(k === "bank_rate_pct" ? 2 : 1)}${ranges[k].unit === "%" ? "%" : ""}`
      : `${num(v)} ${ranges[k].unit}`;

  const irrDelta = res.irr - baseRes.irr;

  return (
    <div className="grid lg:grid-cols-[1.1fr_1fr] gap-8">
      {/* Sliders */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <span className="eyebrow">Demand / supply drivers</span>
          <button
            onClick={reset}
            className="font-mono text-[10px] uppercase tracking-[0.15em] text-slatey hover:text-ink-800 border border-paper-line rounded-sm px-2 py-1"
          >
            Reset to UK data
          </button>
        </div>
        {keys.map((k) => {
          const r = ranges[k];
          const atBase = drivers[k] === defaultDrivers[k];
          return (
            <div key={k}>
              <div className="flex items-baseline justify-between mb-1">
                <label className="text-sm text-ink-800">{r.label}</label>
                <span className={`tnum text-sm ${atBase ? "text-slatey" : "text-gold-deep"}`}>
                  {fmtDriver(k, drivers[k])}
                </span>
              </div>
              <input
                type="range"
                className="w-full"
                min={r.min}
                max={r.max}
                step={r.step}
                value={drivers[k]}
                onChange={(e) => set(k, parseFloat(e.target.value))}
              />
              <div className="flex justify-between font-mono text-[9px] text-slatey mt-0.5">
                <span>{num(r.min)}</span>
                <span>baseline {num(baselines[k as keyof Baselines])}</span>
                <span>{num(r.max)}</span>
              </div>
            </div>
          );
        })}
        <p className="text-[12px] text-slatey leading-relaxed border-l-2 border-gold/40 pl-3">
          Every driver is explicit. Migration is <em>one</em> visible demand input — not a hidden
          signal. The model maps drivers → demand pressure → rent growth / exit cap → IRR through
          documented elasticities (see <span className="font-mono">re_engine.py</span>).
        </p>
      </div>

      {/* Live outputs */}
      <div className="card p-6 self-start">
        <div className="eyebrow">Levered return (5-yr hold)</div>
        <div className="mt-2 flex items-end gap-3">
          <span className="tnum text-5xl text-ink-900">{pct(res.irr, 1)}</span>
          <span className="text-sm text-slatey mb-1">IRR</span>
          {Math.abs(irrDelta) > 1e-4 && (
            <span
              className={`mb-1.5 tnum text-sm ${irrDelta >= 0 ? "text-data-teal" : "text-data-red"}`}
            >
              {irrDelta >= 0 ? "▲" : "▼"} {pct(Math.abs(irrDelta), 1)} vs base
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 mt-5">
          {[
            ["Equity multiple", `${res.equityMultiple.toFixed(2)}x`],
            ["DSCR", `${res.dscr.toFixed(2)}x`],
            ["Implied rent growth", pct(res.rentGrowth, 2)],
            ["Implied exit cap", pct(res.exitCap, 2)],
            ["Debt rate", pct(res.debtRate, 2)],
            ["Net demand pressure", res.demandPressure.toFixed(3)],
          ].map(([label, val]) => (
            <div key={label} className="border-t border-paper-line pt-2">
              <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-slatey">
                {label}
              </div>
              <div className="tnum text-lg text-ink-900">{val}</div>
            </div>
          ))}
        </div>

        <div className="mt-5 rule pt-3 text-[12px] text-ink-700">
          On <span className="font-mono">{gbp(res.valuation)}</span> valuation ·{" "}
          <span className="font-mono">{gbp(res.equity)}</span> equity in.
        </div>
      </div>
    </div>
  );
}
