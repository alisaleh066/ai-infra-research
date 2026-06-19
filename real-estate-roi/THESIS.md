# Real-Estate ROI — Underwriting Thesis (the GP/LP lens)

*Author: Ali Saleh Al Taher. The model (`roi.py`) is the machinery; this is how I'd use it to take
or pass a deal. Not investment advice.*

## The view: in a higher-rate world, the return has to be *manufactured*, not bought
You can no longer rely on cap-rate compression to make money in real estate. The return has to come
from **NOI growth you create** (the value-add: renovate, re-lease, stabilize) and from **financing
structured so the equity is actually paid for the risk**. The model is built to test exactly that —
and to show **who gets paid (LP vs GP) and when**, which is where most retail "ROI calculators" stop.

## What the waterfall actually tells you (the decision)
The headline project IRR is vanity; the **LP IRR after promote** is the number an investor lives on.
On the sample deal: project IRR **~16%**, but LP IRR **~14.4%** after a **~£737k GP promote** — a
**~1.8pp promote drag**. The decisions that fall out of this:
- **As an LP**, I underwrite to the *LP* IRR and stress it. An 8% pref + tiered promote is only
  attractive if the base case clears the pref comfortably *and* the downside still returns capital.
- **As a GP**, the promote is the whole business — but it only pays if I clear the hurdle, which
  disciplines leverage and basis. The structure aligns incentives only when the pref is real.

## When I take the deal vs pass
- **Take:** base-case LP IRR clears the pref with margin, **min DSCR > ~1.3x**, debt yield gives a
  refinancing cushion, and the **downside still returns LP capital** (equity multiple ≥ ~1.0x).
- **Pass:** the deal only works on exit-cap compression, DSCR is thin, or the value-add NOI uplift
  is heroic. The sensitivity grid (exit cap × NOI uplift) shows how fast the LP IRR craters when
  those assumptions slip.

## What would make me wrong (the kill criteria)
- **Exit cap expands** (rates higher-for-longer) — the single biggest swing; the downside scenario
  models +0.75pp and it roughly halves the return.
- **The value-add doesn't land** (rents/occupancy miss) — NOI never stabilizes, DSCR tightens.
- **Financing risk** — interest-only debt means the whole loan is refinanced at exit; a stressed
  credit market at exit is a real, modelled risk (downside adds +1.5pp to the rate).

## How it connects to the rest of my work
Same discipline as the equity work: **assumption-driven, transparent, stress-tested, and honest
about who captures the return.** The waterfall is the real-asset analog of the promote/economics I
studied on the Al Salam desk and the private-equity coursework — it's the structure Blackstone/
BlackRock real-estate funds actually run.

## The conclusion
Real-estate return today is an **underwriting-and-structuring problem, not a beta trade.** Use the
model to (1) manufacture NOI growth, (2) structure debt so the equity is paid for risk, and
(3) check the LP still wins after the promote and survives the downside. If it only works on cap-rate
compression, it isn't a deal.
