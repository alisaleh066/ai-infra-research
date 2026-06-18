import Nav from "@/components/Nav";
import Histogram from "@/components/Histogram";
import FootballField from "@/components/FootballField";
import Heatmap from "@/components/Heatmap";
import SupplyChain from "@/components/SupplyChain";
import CapitalFlow from "@/components/CapitalFlow";
import RoiSimulator from "@/components/RoiSimulator";
import { pct, usd, usdM, gbp, num } from "@/lib/format";

import valuation from "@/public/data/valuation.json";
import mc from "@/public/data/valuation_mc.json";
import bottleneck from "@/public/data/bottleneck.json";
import realEstate from "@/public/data/real_estate.json";
import portfolio from "@/public/data/portfolio.json";

export default function Page() {
  const v = valuation;
  const re = realEstate;
  const sim = re.simulator;

  // football field bars
  const sensFlat = v.sensitivity.grid.flat();
  const bars = [
    {
      label: "DCF (sensitivity range)",
      low: Math.min(...sensFlat),
      high: Math.max(...sensFlat),
      point: v.dcf.value_per_share,
    },
    {
      label: "Comps (EV/EBITDA · P/E)",
      low: Math.min(v.comps.value_per_share_ev_ebitda, v.comps.value_per_share_pe),
      high: Math.max(v.comps.value_per_share_ev_ebitda, v.comps.value_per_share_pe),
      point: v.comps.midpoint,
      flag: true,
    },
    {
      label: "Monte Carlo (P5–P95)",
      low: v.monte_carlo.p5,
      high: v.monte_carlo.p95,
      point: v.monte_carlo.p50,
    },
  ];

  const layerNames: Record<string, string> = Object.fromEntries(
    bottleneck.layers.map((l) => [l.id, l.name])
  );

  return (
    <main>
      <Nav />

      {/* ===================== OVERVIEW ===================== */}
      <section id="overview" className="mx-auto max-w-6xl px-6 pt-20 pb-24">
        <div className="rise">
          <span className="eyebrow">AI-Infrastructure & Real-Asset Investment Research</span>
          <h1 className="mt-4 text-5xl sm:text-7xl leading-[0.95] text-ink-950 max-w-4xl">
            Where the AI build-out{" "}
            <span className="text-gold-deep italic">actually pays.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-lg text-ink-700 leading-relaxed">
            Three rigorous studies under one roof: a disciplined equity valuation of the memory
            bottleneck, a map of where the supply chain is binding and capital is migrating, and a
            transparent underwriting of UK real assets. Audited data where it exists; every
            assumption flagged.
          </p>
        </div>

        <div className="mt-14 grid md:grid-cols-3 gap-4">
          {[
            {
              href: "#valuation",
              n: "01",
              title: "Equity Valuation — Micron",
              line: "What is the HBM memory leader worth on audited fundamentals?",
              stat: `${usd(v.dcf.value_per_share)} DCF · WACC ${pct(v.wacc)}`,
            },
            {
              href: "#bottleneck",
              n: "02",
              title: "Bottleneck Map",
              line: "Which layer of the AI supply chain is the binding constraint?",
              stat: `${bottleneck.binding_constraint.name} · ${bottleneck.binding_constraint.tightness.toFixed(0)}/100`,
            },
            {
              href: "#realestate",
              n: "03",
              title: "UK Real Estate + ROI Simulator",
              line: "How does return respond to migration, supply and rates — transparently?",
              stat: `${pct(re.base_case.irr)} base IRR · ${re.base_case.equity_multiple.toFixed(2)}x`,
            },
          ].map((c) => (
            <a
              key={c.n}
              href={c.href}
              className="card p-6 group hover:border-ink-700 transition-colors block"
            >
              <div className="flex items-center justify-between">
                <span className="font-display text-3xl text-paper-line group-hover:text-gold transition-colors">
                  {c.n}
                </span>
                <span className="text-gold-deep text-lg group-hover:translate-x-1 transition-transform">
                  →
                </span>
              </div>
              <h3 className="mt-4 text-xl text-ink-900">{c.title}</h3>
              <p className="mt-2 text-sm text-ink-700 leading-relaxed">{c.line}</p>
              <div className="mt-4 tnum text-[12px] text-gold-deep">{c.stat}</div>
            </a>
          ))}
        </div>
      </section>

      {/* ===================== VALUATION ===================== */}
      <section id="valuation" className="border-t border-paper-line bg-paper-dim/40">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <Header n="01" kicker="Equity Valuation" title="Micron Technology (MU)" />
          <p className="max-w-2xl text-ink-700 leading-relaxed">
            A linked DCF on <strong>audited SEC EDGAR</strong> financials (FY2022–FY2025) with a
            full WACC build, two-way sensitivity, a comps cross-check and a 10,000-path Monte Carlo.
            Share price, beta and peer multiples are flagged assumptions.
          </p>

          <div className="mt-10 grid sm:grid-cols-4 gap-4">
            <Stat label="DCF value / share" value={usd(v.dcf.value_per_share)} accent />
            <Stat label="WACC" value={pct(v.wacc)} />
            <Stat label="Enterprise value" value={usdM(v.dcf.enterprise_value_m)} />
            <Stat
              label="vs market (assumed)"
              value={`${v.upside_vs_market >= 0 ? "+" : ""}${pct(v.upside_vs_market)}`}
            />
          </div>

          <div className="mt-10 grid lg:grid-cols-2 gap-8">
            <Panel title="Football field" sub="Valuation ranges vs assumed market price">
              <FootballField bars={bars} market={v.market_price_ASSUMPTION} />
            </Panel>
            <Panel title="Monte Carlo" sub="Fair-value distribution across 10k driver paths">
              <Histogram
                samples={mc.samples}
                dcf={mc.dcf}
                market={mc.market}
              />
              <div className="mt-2 grid grid-cols-3 gap-2 text-center">
                {[
                  ["P5", v.monte_carlo.p5],
                  ["Median", v.monte_carlo.p50],
                  ["P95", v.monte_carlo.p95],
                ].map(([l, val]) => (
                  <div key={l as string}>
                    <div className="font-mono text-[10px] uppercase tracking-[0.12em] text-slatey">
                      {l}
                    </div>
                    <div className="tnum text-ink-900">{usd(val as number)}</div>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          <div className="mt-8 grid lg:grid-cols-2 gap-8">
            <Panel title="Sensitivity" sub="Value / share — WACC × terminal growth">
              <Heatmap
                rows={v.sensitivity.waccs}
                cols={v.sensitivity.growths}
                grid={v.sensitivity.grid}
                rowLabel="WACC"
                colLabel="Terminal growth"
                rowFmt="pct"
                colFmt="pct"
                cellFmt="usd"
                baseRow={v.sensitivity.waccs[2]}
                baseCol={0.025}
              />
            </Panel>
            <Panel
              title="Thesis vs portfolio"
              sub="Sample positions — no Trading212 MCP connected"
            >
              <div className="mb-3">
                <span className="flag">Sample data — replace with live holdings</span>
              </div>
              <ul className="space-y-2">
                {portfolio.positions.map((p) => (
                  <li
                    key={p.ticker}
                    className="flex items-center gap-3 text-sm border-b border-paper-line pb-2"
                  >
                    <span className="font-mono text-ink-900 w-14">{p.ticker}</span>
                    <span className="text-ink-700 flex-1">{p.name}</span>
                    <span className="font-mono text-[11px] text-gold-deep">{p.theme}</span>
                    <span className="tnum text-ink-900 w-12 text-right">
                      {p.weight_pct.toFixed(0)}%
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-[12px] text-slatey leading-relaxed">
                Micron sits in the HBM layer — the same node the bottleneck map flags as one of the
                tightest. The thesis and the (sample) book line up around memory, packaging and power.
              </p>
            </Panel>
          </div>
        </div>
      </section>

      {/* ===================== BOTTLENECK ===================== */}
      <section id="bottleneck" className="border-t border-paper-line">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <Header n="02" kicker="Supply-Chain Bottleneck Map" title="Where the chain binds" />
          <p className="max-w-2xl text-ink-700 leading-relaxed">
            Each AI-infrastructure layer scored on a transparent <strong>tightness</strong> metric
            (utilisation, lead time, supply inelasticity, concentration). The binding constraint —
            and where capital migrates next — is the investable signal.
          </p>

          <div className="mt-10 grid sm:grid-cols-3 gap-4">
            <Stat label="Binding constraint" value={bottleneck.binding_constraint.name} accent />
            <Stat
              label="Tightness score"
              value={`${bottleneck.binding_constraint.tightness.toFixed(1)} / 100`}
            />
            <Stat label="Layers mapped" value={num(bottleneck.layers.length)} />
          </div>

          <div className="mt-10">
            <Panel title="Tightness by layer" sub="Hover a layer for its underlying metrics">
              <SupplyChain
                layers={bottleneck.layers}
                binding={bottleneck.binding_constraint.id}
              />
            </Panel>
          </div>

          <div className="mt-8">
            <Panel
              title="Capital migration"
              sub="Share of investment by layer over time — illustrative"
            >
              <div className="mb-3">
                <span className="flag">Illustrative intensity — not audited capex</span>
              </div>
              <CapitalFlow
                years={bottleneck.capital_flow.years}
                shares={bottleneck.capital_flow.shares}
                names={layerNames}
              />
            </Panel>
          </div>
        </div>
      </section>

      {/* ===================== REAL ESTATE ===================== */}
      <section id="realestate" className="border-t border-paper-line bg-paper-dim/40">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <Header n="03" kicker="UK Real-Estate Underwriting" title="Return, made transparent" />
          <p className="max-w-2xl text-ink-700 leading-relaxed">
            A levered acquisition model for an illustrative {re.deal.units}-unit block, plus a
            simulator driven by the indicators institutions actually underwrite. UK data from{" "}
            <strong>HM Land Registry & ONS</strong>.
          </p>

          <div className="mt-10 grid sm:grid-cols-4 gap-4">
            <Stat label="Base levered IRR" value={pct(re.base_case.irr)} accent />
            <Stat label="Equity multiple" value={`${re.base_case.equity_multiple.toFixed(2)}x`} />
            <Stat label="DSCR" value={`${re.base_case.dscr.toFixed(2)}x`} />
            <Stat label="Valuation" value={gbp(re.base_case.valuation)} />
          </div>

          <div className="mt-12">
            <Panel
              title="ROI simulator"
              sub="Flex each demand / supply driver — IRR responds live"
            >
              <RoiSimulator
                deal={{
                  units_monthly_rent: re.deal.units_monthly_rent,
                  vacancy_rate: re.deal.vacancy_rate,
                  opex_ratio: re.deal.opex_ratio,
                  entry_cap_rate: re.deal.entry_cap_rate,
                  ltv: re.deal.ltv,
                  purchase_costs_pct: re.deal.purchase_costs_pct,
                  selling_costs_pct: re.deal.selling_costs_pct,
                  hold_years: re.deal.hold_years,
                }}
                baselines={sim.baselines}
                coefficients={sim.coefficients}
                defaultDrivers={sim.default_drivers}
                ranges={sim.driver_ranges}
              />
            </Panel>
          </div>

          <div className="mt-8">
            <Panel title="Sensitivity" sub="Levered IRR — exit cap × rent growth">
              <Heatmap
                rows={re.sensitivity.exit_caps}
                cols={re.sensitivity.rent_growths}
                grid={re.sensitivity.grid}
                rowLabel="Exit cap"
                colLabel="Rent growth"
                rowFmt="pct"
                colFmt="pct0"
                cellFmt="pct0"
                baseRow={re.deal.entry_cap_rate}
                baseCol={0.03}
              />
            </Panel>
          </div>
        </div>
      </section>

      {/* ===================== FOOTER ===================== */}
      <footer className="border-t border-paper-line">
        <div className="mx-auto max-w-6xl px-6 py-12 flex flex-col sm:flex-row justify-between gap-4">
          <div>
            <div className="font-display text-lg">
              projects<span className="text-gold">f</span>
            </div>
            <p className="text-[12px] text-slatey mt-1 max-w-md leading-relaxed">
              Research / portfolio artifact — not investment advice. Fundamentals: SEC EDGAR.
              UK data: Land Registry + ONS. All assumptions flagged; sources in DATA_SOURCES.md.
            </p>
          </div>
          <div className="font-mono text-[11px] text-slatey">
            Built with Next.js · Python · openpyxl
          </div>
        </div>
      </footer>
    </main>
  );
}

function Header({ n, kicker, title }: { n: string; kicker: string; title: string }) {
  return (
    <div className="mb-6">
      <div className="flex items-baseline gap-3">
        <span className="font-display text-2xl text-gold">{n}</span>
        <span className="eyebrow">{kicker}</span>
      </div>
      <h2 className="mt-2 text-4xl sm:text-5xl text-ink-950">{title}</h2>
    </div>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className={`card p-4 ${accent ? "border-gold/50" : ""}`}>
      <div className="font-mono text-[10px] uppercase tracking-[0.13em] text-slatey">
        {label}
      </div>
      <div
        className={`tnum mt-1 text-xl ${accent ? "text-gold-deep" : "text-ink-900"}`}
      >
        {value}
      </div>
    </div>
  );
}

function Panel({
  title,
  sub,
  children,
}: {
  title: string;
  sub: string;
  children: React.ReactNode;
}) {
  return (
    <div className="card p-6">
      <div className="mb-4">
        <h4 className="text-lg text-ink-900">{title}</h4>
        <p className="text-[12px] text-slatey font-mono">{sub}</p>
      </div>
      {children}
    </div>
  );
}
