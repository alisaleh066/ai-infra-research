"use client";

import { useState } from "react";
import { tightnessColor } from "@/lib/format";

interface Layer {
  id: string;
  name: string;
  lead_player: string;
  tightness: number;
  metrics: Record<string, number>;
  note: string;
}

const METRIC_LABELS: Record<string, string> = {
  utilization: "Utilisation",
  lead_time: "Lead time",
  supply_inelasticity: "Supply inelasticity",
  concentration: "Concentration",
};

export default function SupplyChain({
  layers,
  binding,
}: {
  layers: Layer[];
  binding: string;
}) {
  // layers come tightest-first; show in supply-chain order (downstream -> upstream) for the flow
  const ordered = [...layers].sort((a, b) => a.id === binding ? 0 : 0);
  const [sel, setSel] = useState<Layer>(layers.find((l) => l.id === binding) ?? layers[0]);

  return (
    <div className="grid md:grid-cols-[1.3fr_1fr] gap-6">
      <div className="space-y-2">
        {layers.map((l, i) => {
          const isBind = l.id === binding;
          const isSel = l.id === sel.id;
          return (
            <button
              key={l.id}
              onMouseEnter={() => setSel(l)}
              onFocus={() => setSel(l)}
              className={`w-full text-left flex items-center gap-3 group ${
                isSel ? "" : "opacity-90 hover:opacity-100"
              }`}
            >
              <div className="w-7 font-mono text-[11px] text-slatey">{i + 1}</div>
              <div
                className="flex-1 rounded-sm border px-3 py-2 transition-all"
                style={{
                  borderColor: isSel ? "#0d1422" : "#dcd5c5",
                  background: `${tightnessColor(l.tightness)}22`,
                }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-sans text-sm text-ink-900">
                    {l.name}
                    {isBind && (
                      <span className="ml-2 font-mono text-[9px] uppercase tracking-[0.15em] text-data-red border border-data-red/40 rounded-sm px-1 py-0.5">
                        binding
                      </span>
                    )}
                  </span>
                  <span className="tnum text-sm" style={{ color: tightnessColor(l.tightness) }}>
                    {l.tightness.toFixed(0)}
                  </span>
                </div>
                <div className="mt-1.5 h-1 w-full bg-paper-line rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${l.tightness}%`, background: tightnessColor(l.tightness) }}
                  />
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="card p-5 self-start">
        <div className="eyebrow">{sel.lead_player}</div>
        <h4 className="text-xl mt-1">{sel.name}</h4>
        <div className="mt-1 tnum text-3xl" style={{ color: tightnessColor(sel.tightness) }}>
          {sel.tightness.toFixed(1)}
          <span className="text-sm text-slatey ml-1">/ 100 tightness</span>
        </div>
        <div className="mt-4 space-y-2">
          {Object.entries(sel.metrics).map(([k, v]) => (
            <div key={k}>
              <div className="flex justify-between text-[11px] font-mono text-ink-700">
                <span>{METRIC_LABELS[k] ?? k}</span>
                <span>{(v * 100).toFixed(0)}</span>
              </div>
              <div className="h-1 w-full bg-paper-line rounded-full overflow-hidden">
                <div className="h-full bg-gold" style={{ width: `${v * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
        <p className="mt-4 text-sm text-ink-700 leading-relaxed">{sel.note}</p>
      </div>
    </div>
  );
}
