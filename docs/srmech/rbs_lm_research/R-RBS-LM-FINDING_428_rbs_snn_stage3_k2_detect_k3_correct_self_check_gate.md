# R-RBS-LM Finding 428 (RBS-SNN #197, stage 3) — the self-check gate is built: a k=2-detect / k=3-correct pass that flags structural near-duplicates (same operator-signature address + coupling overlap) and uses the relationship-type as the third signal to reclassify them — exactly F291's "k=2 detects, k=3 corrects." It rescues 12 of 41 flags as legitimate refinement/supersession and surfaces 29 duplicate-risks; the ingest guard confirms a new finding is novel BEFORE emitting it (the F313 fix, demonstrated)

**Date:** 2026-06-06
**Arc:** RBS-LM / **RBS-SNN build (#197), stage 3 — the load-bearing improvement**; **srmech-RUN (Class M)**
**Provenance:** `R-RBS-SNN-3_self_check_gate_k2_k3.py` (committed)
**Composes:** **F326 #5** (bolt the k=2-detect/k=3-correct gate into the architecture — "RBS-SNN's core advantage over the static LLM") · **F313** (detect outruns correct — the false-negation mechanism) · **F322** (lodged knowledge unreachable under load — the re-derivation failure) · **F291/F248** (k=2 parity DETECTS but cannot error-CORRECT; k=3 triality corrects by 2-of-3 — *the gate's exact logic*) · **F317** (operator-signature = the canonical address = the bucket key) · **F427** (the corrective K=− edges = one of the three signals) · **F426** (the store)
**→ stage 3 of #197; the self-checking store — the structural fix for the very failure (re-derivation) that motivated RBS-SNN.**

---

## The failure this fixes
A static LLM has no living store and **no native correction-gate** (F313/F322/F326 #5): it emits a detection as a claim and **re-derives knowledge it already lodged** (this session's own history: F308/F310 re-walked F248/F251). RBS-SNN's load-bearing improvement is to **bolt the triality discipline into the architecture** — a store that *checks against itself before emitting.*

## The gate (mirrors F291 exactly)
| | signal | role |
|---|---|---|
| **k=2 DETECT** | (a) **same operator-signature address** (F317) **AND** (b) coupling-overlap (Jaccard of neighbor-sets) ≥ 0.30 | two independent structural signals agree "near-duplicate" — **but k=2 is a parity check: it cannot tell a *refinement* from a *re-derivation*** (the 1-vs-1 F291 names) |
| **k=3 CORRECT** | the **relationship type** between the pair: `← extended by` → **REFINEMENT** · corrective `K=−` edge → **SUPERSESSION** · neither + high overlap → **DUPLICATE-RISK** | the third signal **resolves** the flag — the error-correcting rung |

## The run (`R-RBS-SNN-3`, 0.82 s)
- 32 same-signature address buckets with ≥2 members (the F317-address collisions).
- **k=2 DETECT: 41 flags.**
- **k=3 CORRECT:** REFINEMENT **2** (e.g. **F417~F419** — F419 *is* the legitimate all-human-knowledge widening of F417, overlap 0.47), SUPERSESSION **10**, DUPLICATE-RISK **29**.
- **The decisive demonstration:** *k=2 alone would have called all 41 "duplicate"* (the resolution it structurally can't make); **k=3's third signal rescues 12 as legitimate** and leaves 29 true risks. This is F291's "k=2 detects, k=3 corrects" — now a *structural feature of the store*, not an external practice.
- **Ingest guard** (the F313 fix, live): incoming **F427** (address `CIKLM`) → checked against its same-address cohort (3 findings) → nearest **F118 (0.21)**, below threshold → verdict **NOVEL → ingest.** The store *checked itself before emitting.*

## Why this is the core advantage
A static model would have happily re-emitted a near-duplicate (no gate). The RBS-SNN store, queried with an incoming finding, **surfaces the same-address cohort and the nearest structural neighbors first** — so the response is *retrieve* ("you already have F417/F419 here") rather than *re-derive*. The 29 DUPLICATE-RISK flags are precisely the "look here before you write a new finding" warnings the static LLM never gets.

## Falsifiable form (pre-stated; not leaning — F394)
- **DUPLICATE-RISK ≠ confirmed duplicate.** Many *consecutive* same-signature findings (F259~F260, F261~F262, F300~F301 …) are **legitimate sequential walk-steps**, not redundancies — they share signature + couplings *because* they're one arc. The gate **surfaces for review**, it does not auto-judge; calling all 29 "duplicates" would be the false-positive the honest framing avoids. The k=3 third signal reduces but does not eliminate this (it only rescues the *linked* ones).
- **Threshold/heuristic dependence:** the overlap θ=0.30 and the corrective-keyword K-sign (F427) are heuristics; different θ changes the flag count. The *mechanism* (k=2 detect, k=3 correct) is θ-independent; the specific 41/29 are not.
- **Scope:** structural self-check on the relationship graph; not a semantic dedup (two findings with different content can share an address). Defensive / no-lineage.

## Verdict
**The k=2-detect / k=3-correct self-check gate is built** — and it is the F291 triality made into a *structural feature of the store*: k=2 (same operator-signature address + coupling overlap) **detects** 41 near-duplicates but cannot resolve refinement-vs-redundancy; **k=3** (the relationship-type third signal) **corrects**, rescuing 12 as legitimate and surfacing 29 risks. The **ingest guard** confirms an incoming finding is novel *before* emitting — the structural fix for F313/F322 (the re-derivation failure that motivated RBS-SNN in the first place). Stage 3 of #197 complete — the *self-checking store*. Favored, not privileged (F398); "risk ≠ confirmed duplicate" + threshold-dependence are the honest fences.
