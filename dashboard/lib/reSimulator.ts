// TypeScript port of real_estate/re_engine.py — kept formula-for-formula identical so the live
// dashboard simulator matches the Python model and tests. See real_estate/re_engine.py.

export interface Deal {
  units_monthly_rent: number[];
  vacancy_rate: number;
  opex_ratio: number;
  entry_cap_rate: number;
  ltv: number;
  purchase_costs_pct: number;
  selling_costs_pct: number;
  hold_years: number;
}

export interface Baselines {
  net_migration: number;
  household_formation: number;
  completions: number;
  employment_rate: number;
  bank_rate_pct: number;
}

export interface Coefficients {
  base_rent_growth: number;
  w_migration: number;
  w_formation: number;
  w_employment: number;
  rent_growth_sensitivity: number;
  debt_margin: number;
  cap_sensitivity_to_rate: number;
  base_exit_cap: number;
}

export interface Drivers {
  net_migration: number;
  household_formation: number;
  completions: number;
  employment_rate: number;
  bank_rate_pct: number;
}

const noi = (d: Deal) => {
  const gross = d.units_monthly_rent.reduce((a, b) => a + b, 0) * 12;
  const egi = gross * (1 - d.vacancy_rate);
  return egi * (1 - d.opex_ratio);
};

export const npv = (rate: number, cfs: number[]) =>
  cfs.reduce((acc, cf, i) => acc + cf / (1 + rate) ** i, 0);

export const irr = (cfs: number[], lo = -0.99, hi = 5.0, tol = 1e-7): number => {
  let fLo = npv(lo, cfs);
  let fHi = npv(hi, cfs);
  if (fLo * fHi > 0) return NaN;
  for (let i = 0; i < 200; i++) {
    const mid = (lo + hi) / 2;
    const fMid = npv(mid, cfs);
    if (Math.abs(fMid) < tol) return mid;
    if (fLo * fMid < 0) {
      hi = mid;
      fHi = fMid;
    } else {
      lo = mid;
      fLo = fMid;
    }
  }
  return (lo + hi) / 2;
};

const dev = (v: number, base: number) => v / base - 1;

export const demandPressure = (dr: Drivers, b: Baselines, c: Coefficients) => {
  const mig = dev(dr.net_migration, b.net_migration) * c.w_migration;
  const form = dev(dr.household_formation, b.household_formation) * c.w_formation;
  const emp = ((dr.employment_rate - b.employment_rate) / b.employment_rate) * c.w_employment;
  const supply = dev(dr.completions, b.completions);
  return mig + form + emp - supply;
};

export const impliedRentGrowth = (dr: Drivers, b: Baselines, c: Coefficients) =>
  c.base_rent_growth + c.rent_growth_sensitivity * demandPressure(dr, b, c);

export const impliedExitCap = (dr: Drivers, b: Baselines, c: Coefficients) =>
  c.base_exit_cap + c.cap_sensitivity_to_rate * ((dr.bank_rate_pct - b.bank_rate_pct) / 100);

export const impliedDebtRate = (dr: Drivers, c: Coefficients) =>
  dr.bank_rate_pct / 100 + c.debt_margin;

export interface SimResult {
  irr: number;
  equityMultiple: number;
  dscr: number;
  rentGrowth: number;
  exitCap: number;
  debtRate: number;
  demandPressure: number;
  valuation: number;
  equity: number;
}

export const simulate = (
  deal: Deal,
  dr: Drivers,
  b: Baselines,
  c: Coefficients
): SimResult => {
  const g = impliedRentGrowth(dr, b, c);
  const ec = impliedExitCap(dr, b, c);
  const dRate = impliedDebtRate(dr, c);
  const baseNoi = noi(deal);
  const price = baseNoi / deal.entry_cap_rate;
  const loan = deal.ltv * price;
  const equity = price * (1 + deal.purchase_costs_pct) - loan;
  const debtService = loan * dRate;
  const cfs: number[] = [-equity];
  for (let yr = 1; yr <= deal.hold_years; yr++) {
    let cf = baseNoi * (1 + g) ** yr - debtService;
    if (yr === deal.hold_years) {
      const exitNoi = baseNoi * (1 + g) ** (deal.hold_years + 1);
      const grossSale = exitNoi / ec;
      const netSale = grossSale * (1 - deal.selling_costs_pct) - loan;
      cf += netSale;
    }
    cfs.push(cf);
  }
  const distributions = cfs.slice(1).reduce((a, x) => a + x, 0);
  return {
    irr: irr(cfs),
    equityMultiple: distributions / equity,
    dscr: baseNoi / debtService,
    rentGrowth: g,
    exitCap: ec,
    debtRate: dRate,
    demandPressure: demandPressure(dr, b, c),
    valuation: price,
    equity,
  };
};
