export const pct = (x: number, dp = 1) =>
  `${(x * 100).toFixed(dp)}%`;

export const usd = (x: number, dp = 0) =>
  `$${x.toLocaleString("en-US", { maximumFractionDigits: dp, minimumFractionDigits: dp })}`;

export const gbp = (x: number, dp = 0) =>
  `£${x.toLocaleString("en-GB", { maximumFractionDigits: dp, minimumFractionDigits: dp })}`;

export const num = (x: number, dp = 0) =>
  x.toLocaleString("en-US", { maximumFractionDigits: dp, minimumFractionDigits: dp });

export const usdM = (x: number) => {
  if (Math.abs(x) >= 1000) return `$${(x / 1000).toFixed(1)}bn`;
  return `$${x.toFixed(0)}m`;
};

// Heatmap colour ramp: low = cool slate, high = gold. t in [0,1].
export const ramp = (t: number) => {
  const c = Math.max(0, Math.min(1, t));
  const lo = [219, 213, 197]; // paper-line
  const hi = [158, 116, 48]; // gold-deep
  const mix = lo.map((l, i) => Math.round(l + (hi[i] - l) * c));
  return `rgb(${mix[0]},${mix[1]},${mix[2]})`;
};

// Diverging ramp for tightness 0..100 (cool -> gold -> red-hot)
export const tightnessColor = (score: number) => {
  const t = Math.max(0, Math.min(1, score / 100));
  if (t < 0.5) return ramp(t * 1.4);
  const u = (t - 0.5) / 0.5;
  const a = [158, 116, 48];
  const b = [224, 99, 90];
  const mix = a.map((x, i) => Math.round(x + (b[i] - x) * u));
  return `rgb(${mix[0]},${mix[1]},${mix[2]})`;
};
