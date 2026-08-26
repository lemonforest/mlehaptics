# F956 (research note, real corpus) — per-tome native coherence **routes cleanly on disjoint vocabs (F955) but FAILS on real English**, because articles **share function-word vocab** — and the fix is the de-lensing we already know we need (F782/F768). The recall *mechanism* is sound (F955: small tomes → COHERENT on the default floor, route-to-best, honest-stop), but **route-to-best by raw context-similarity can't pick the right tome when every tome contains `is/the/of`**: from `['april','apr']` (article-0 = *"april apr is the fourth month…"*) the routed walk produced `art~ activities~ activity~ object~` — it routed to an **art** article — and nonsense `[zz,yy]` did **not** STOP. This is the **F946 frequency prior / F947 hairball / F782 hub-lensing at the ROUTING layer**.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc79 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Probe:** `R-RBS-LM-FINDING_956_*.py` · **Composes:** F955 (per-tome native coherence — disjoint-vocab success), F946 (single-M frequency-prior saturation), F947 (the co-occurrence hairball; balanced-cut + IDF de-lensing fix), F782 (IDF-as-de-lensing), F768 (aboutness-gate), F944 (route-to-best) · **User direction (2026-06-26):** "continue" (extend per-tome native coherence to a real corpus).

## Measured (rc79, 6 real simplewiki article-fragment tomes, ≤30 tok each, default floor)
```
article-0 actual : april apr is the fourth month of the year in the julian
routed walk      : april apr art~ activities~ is~ art~ activities~ activity~ of~ art~ object~   <- WRONG tome (art)
nonsense [zz,yy] : it~ activity~ art~ is~ ...                                                   <- no clean STOP
```

## Why it failed (and why F955 didn't)
- **F955 used disjoint vocabs** (`a–e`, `p–t`, `m–o`): a context's tokens live in exactly one tome, the others read STOP, so route-to-best picks the right tome trivially.
- **Real articles share the function words** (`is`, `the`, `of`, `a`, …). The context `['april','apr']` encodes, and *every* tome responds (they all contain the shared words). Route-to-best then picks whichever tome has the **highest self-similarity** — here an art article with `art` repeated — **not** the tome the context belongs to. The shared vocab also means nonsense never cleanly STOPs (some tome always responds to the function-word component).
- This is the **same frequency-prior / hub-lensing wall** as F946 (single-M saturated to `an/on/in/of`) and F947 (the co-occurrence hairball wouldn't spectrally partition) — now showing up **one layer up, in the tome-routing**.

## The fix (handed forward — already on the board)
Route by **content, not raw similarity**: de-lens the shared function-word hubs *before* the route-to-best.
- **IDF-de-lensing (F782)**: weight the context tokens by `1/√(freq)` so the shared `is/the/of` stop dominating the route; the content tokens (`april`, `apr`) then carry the routing.
- **Aboutness-gate (F768, task #221)**: gate the routing on the *measured function-ness* of the context tokens — route on the operands, not the operators.
So **real-corpus per-tome routing is gated on the aboutness-gate / IDF-de-lensing** — exactly the prerequisites already identified for the cosmic-web reading (F781/F782) and the routing stoplist (F768). The recall mechanism is ready; the **routing key** must be de-lensed first.

## Honest scope
The mechanism (F955) is unchanged and correct on disjoint vocabs; this finding is that the **route-to-best key** fails on shared real-English vocab (measured: wrong-tome routing + no honest-stop). The fix (IDF-de-lensed / aboutness-gated routing) is grounded *in principle* by F782/F768 but **not yet wired here** — that is the next build, and it ties the recall scale-up to the existing de-lensing work. No claim that de-lensing fully fixes it until measured.

## Verdict / next
**Per-tome native coherence routes cleanly on disjoint vocabs but not on real English** — the shared function-word vocab makes route-to-best pick the wrong tome (the F946/F947/F782 frequency-prior/hub-lensing wall, at the routing layer). The recall *mechanism* is proven; the **routing key needs hub-de-lensing**. **Next:** wire **IDF-de-lensed / aboutness-gated routing** (F782/F768) into the route-to-best, then re-run the real-corpus per-tome native-coherence walk — the recall scale-up and the de-lensing arc converge here.
