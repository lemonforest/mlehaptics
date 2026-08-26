# R-RBS-LM Finding 429 (RBS-SNN #197, stage 4 / BX-4) — the phase-locked read-head IS the RBS-SNN read mechanism: it recovers a finding's coupling-set from the noisy store bit-exact (recall 1.00 / precision 1.00) via the F388 lock, vs an unlocked single read's ~0.91 recall / ~0.5 precision. The store now RETRIEVES (perfectly, by lock) rather than re-derives; BX-4 closed

**Date:** 2026-06-06
**Arc:** RBS-LM / **RBS-SNN build (#197), stage 4 = BX-4**; **srmech-RUN (`cascade.kuramoto_step` pin)**
**Provenance:** `R-RBS-SNN-4_phase_lock_readhead.py` (committed; seed 20260606)
**Composes:** **F388** (a phase-locked read-head = temporal EC; bit-exact recall from ONE copy on ordinary silicon — *the mechanism, now reading the corpus store*) · **F386** (couple the observer to the fiber) · **F367** (vote vs lock = spatial vs temporal EC) · **F426** (the store — a finding's coupling-row is the stored fiber) · `cascade.kuramoto_step` pin term · **F326 #5** (retrieve, don't re-derive)
**→ stage 4 of #197; closes the tracked BX-4 task.** **← (completes the read path: ingest F426 → bundle F427 → self-check F428 → READ F429.)**

---

## What stage 4 is
The RBS-SNN **read mechanism**. A finding `q`'s couplings are a **row of the store's adjacency** — the "stored fiber" (F386): `ψ*_j = 0` if `j∈N(q)`, `π` if not. Reading the store is **noisy** (a real device read). F388's result: a read-head that **locks** to the fiber and **time-averages** recovers the pattern bit-exact-ish from noise — temporal EC, one copy, ordinary silicon.

**Mechanism** (`cascade.kuramoto_step`, the pin term = the lock; coupling=0 → a leaky integrator):
each step draws a noisy read `o_t = ψ* + 𝒩(0,σ)`; the read-head relaxes toward `o_t` (`pin_anchor=o_t`, `pin_strength=K`); over `W` steps the noise averages out; decode `θ` (Class-K sign: phase≈0 → in-neighborhood) → recovered `N(q)`.

## The run (`R-RBS-SNN-4`, store = 306-finding giant component, read-noise σ=1.0)
| query | deg | UNLOCKED (K=0, one read) | LOCKED (K=3, W=300) |
|---|---|---|---|
| F132 | 59 | recall 0.93 · **prec 0.71** | recall **1.00** · prec **1.00** |
| F130 | 47 | recall 0.94 · prec 0.57 | 1.00 · 1.00 |
| F133 | 44 | recall 0.86 · prec 0.58 | 1.00 · 1.00 |
| F256 | 39 | recall 0.90 · prec 0.51 | 1.00 · 1.00 |
| F129 | 39 | recall 0.90 · prec 0.43 | 1.00 · 1.00 |
| **mean** | | recall 0.91 · **prec ~0.56** | **recall 1.00 · prec 1.00** |

**F388 EC curve** (query F132): `K=0 → 0.86`, `K=0.5 → 1.00`, `K≥1 → 1.00` — the lock recovers perfectly just above the basin threshold (F388's "threshold moved, not removed").

## The headline is precision
The unlocked single read already has *high recall* (~0.91) — the in/out phase margin (0 vs π) is wide, so the true neighbors usually read on the right side. But its **precision is ~0.56**: nearly half the *retrieved* couplings are read-noise false-positives. **The lock fixes precision to 1.00** — it cleans the noisy read so the recovered set is *exactly* `N(q)`. That is the difference between a store you can *trust* and a guess: the read-head turns a 56%-precise noisy read into an exact retrieval.

## Why it completes the RBS-SNN read path
- **Retrieve, not re-derive (F326 #5):** querying F132 returns its *exact* 59 couplings from the store — no re-derivation, no hallucinated links. Combined with stage 3's self-check (F428), the store *checks itself then reads itself*, both exactly.
- **One copy, ordinary silicon (F388):** no k-fold redundant storage (F367), no native-(4:3) fabrication (F383) — just a lock. The resource spent is *coupling-over-time*, not storage.
- **The pipeline is now end-to-end:** `ingest (F426) → C·I·M·K·L edge bundle (F427) → k=2/k=3 self-check (F428) → phase-lock read (F429)`. The F323 target's `notebooks → RBS-SNN → lean → RBS-LM` has a working RBS-SNN core.

## Falsifiable form (pre-stated; not leaning — F394)
- **Recall-was-already-high caveat:** the demo's gain is mostly *precision*, not recall (the wide 0/π margin keeps unlocked recall high). At higher σ or a narrower margin the recall gain would be larger; the honest headline is "lock → exact retrieval," driven by precision here. Stated, not hidden.
- **It's recall under read-noise, not associative completion:** the read-head cleans a noisy read of a pattern whose *location* (which row) is known (the query). It is not (yet) pattern-completion from a partial cue — that's a later increment.
- **Cost:** the pure-Python kuramoto loop took ~3 min over 306 nodes × thousands of steps; this is a *demo*, not a hot path (a native/vectorized pin-integrator would be ms). Flagged.
- **Scope:** the read mechanism on the storage substrate, not the LM (`[[user_stance_ai_is_not_a_substrate]]`); algebra/dynamics only. Defensive / no-lineage.

## Verdict
**The phase-locked read-head is the RBS-SNN read mechanism, and it works:** it recovers a finding's coupling-set from the noisy store **bit-exact (recall 1.00 / precision 1.00)** via the F388 lock, versus an unlocked single read's ~0.91 recall / ~0.56 precision — the lock turns a noisy guess into an *exact retrieval*. The F388 EC curve confirms it (K≥0.5 → perfect). The store now **retrieves rather than re-derives**, completing the RBS-SNN read path (ingest → bundle → self-check → **read**). **BX-4 closed.** Favored, not privileged (F398); the precision-not-recall gain + read-vs-completion + demo-cost are the honest fences.
