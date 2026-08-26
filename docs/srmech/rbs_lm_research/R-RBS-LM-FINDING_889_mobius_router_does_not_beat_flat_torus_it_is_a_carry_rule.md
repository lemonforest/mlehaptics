# F889 (honest negative) — A σ↔θ-Möbius-aware router does NOT beat the flat-torus 0.81: the Möbius is an address-SPACE carry/navigation rule, not a routing-discrimination lever. Built two Möbius-aware routers on top of the F882 ODFT-twiddle key (the 0.81 winner) — (a) **möbius-MAX**: route by the best resonance over BOTH σ-sheets (`q` and `klein4_chirality_flip_gamma5(q)`, since flip ≡ θ+½, F888); (b) **möbius-PACK**: re-coordinatize position as a (σ sign-bit, θ∈[0,½)) pair, using the sign as an extra address bit at double phase-resolution. Measured @ N=1000 vs the baseline flat ODFT: **baseline 0.81 → möbius-MAX 0.81 (no change) → möbius-PACK 0.75 (worse)**. So neither beats the flat-torus ceiling. The reasons are the finding: möbius-MAX ties because reproduction-routing **stores and queries on the same σ-sheet** — the flipped sheet is empty, so the extra check finds nothing (no gain, no harm under a max); möbius-PACK **loses** because halving the θ-range and spending a sign bit gives **coarser angular discrimination** → more distractor collisions. **The takeaway: the σ↔θ Möbius (F888) is a property of the address SPACE — a carry/overflow rule where wrapping one axis flips the other — NOT a routing-discrimination lever.** Flat resonance-routing never traverses σ-sheets, so it cannot benefit; the Möbius belongs in the **sedenion-grid carry**, not the F880/F882 flat router. **0.81 stands.**

**Date:** 2026-06-20 · **srmech:** 0.9.0rc9 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-889_mobius_aware_router.py`, 1000 `simplewiki_v082` sequences · **Composes:** F882 (the 0.81 ODFT ceiling — reproduced as baseline), F888 (the σ↔θ Möbius — flip ≡ θ+½, used here), F880 (the routing task), [[feedback_hyperloop_addressing_is_a_2axis_mobius]] (the Möbius — now scoped to carry, not routing), F873 (the sedenion grid — the Möbius's actual home) · **User direction (2026-06-20):** "build the σ↔θ-Möbius-aware router and test against 0.81."

## Measured (sparse, srmech-native; N=1000)
| router | routing accuracy |
|---|---|
| baseline flat ODFT (F882) | **0.81** (ceiling reproduced) |
| möbius-MAX (both σ-sheets) | 0.81 (no change) |
| möbius-PACK (sign hi-bit, θ∈[0,½)) | 0.75 (worse) |
- Neither Möbius variant beats the flat-torus baseline. The baseline exactly reproduces F882's 0.81 (the test harness is correct).

## Why (the lesson)
- **Same-sheet reproduction:** the query context-key and the stored page-signature keys are built identically (implicit σ=+1), so they live on the **same σ-sheet**. Checking `flip(q)` (the σ=−1 sheet) finds an empty sheet → möbius-MAX = baseline. The Möbius symmetry has nothing to disambiguate *within a single sheet's routing*.
- **Packing loses resolution:** möbius-PACK trades the full θ∈[0,1) range for θ∈[0,½)+sign. The half-range halves the angular spread between adjacent-position keys → keys sit closer → more distractor collisions → 0.75. The sign bit does not recover the lost angular discrimination.
- **Where the Möbius DOES live:** the σ↔θ half-twist matters when you **navigate/wrap** the address space — a carry that rolls one axis past its period flips the other (the sedenion-grid `navigate` overflow, F873/F888-next-3). That is structural addressing, not flat resonance-routing, which is why this router test is the wrong place for it.

## Honest scope
- Clean **negative** for the router: 0.81 stands; the Möbius is not a routing lever. Reproduction-routing regime (query=stored sheet); N=1000.
- The Möbius is **real** (F888, exact ½ offset) and the negative here does not weaken it — it **re-scopes** it from "routing discrimination" to "address-space carry."
- Sparse held: `klein4_phase_bind`/`chirality_flip_gamma5`/`bundle`/`similarity` + the F882 `cd_mult` ODFT twiddle; `Q`-aware compares; no dense, no numpy, no bag.

## Verdict / next
The σ↔θ-Möbius-aware router **does not beat 0.81** (möbius-MAX ties, möbius-PACK loses) — because flat reproduction-routing stays on one σ-sheet, so the half-twist has nothing to exploit. The Möbius is an **address-space carry rule**, not a routing-discrimination lever; its home is the sedenion-grid `navigate` overflow (wrap one axis → flip the other). **0.81 stands as the routing ceiling.** **Next:** (1) put the Möbius where it belongs — the sedenion-grid **carry/overflow** test (does a half-twist carry beat the flat base-16 nesting for >16 pages?); (2) the genuine routing-ceiling lever is still the storage-density / non-superposed-address arc (Q1–Q4), not the phase geometry. Framework reading → srmech measurement; honest negative; the Möbius re-scoped, not lost.
