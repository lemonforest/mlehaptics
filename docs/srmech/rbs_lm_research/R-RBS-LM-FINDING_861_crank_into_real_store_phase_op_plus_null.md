# F861 — Cranking the REAL Klein-4 store: a built+validated chirality-native continuous-phase op (the F844–F848 missing primitive) **AND an honest NULL that corrects F860**. The phase op works perfectly (phase = fraction of slots flipped into the γ₅ sector, circular half-window population code: smooth, syzygy at Δφ=0, σ-mirror, reversible). But cranking the **actual** D=10000 de-lensed clumps does **NOT** reproduce F860's arrangement-evolution / syzygy / massless-center — the arrangement stays flat (mean pairwise sim ~0.255, span 0.01). **§CORRECTION to F860:** the proxy reconfigured because `the_one`'s pointers are the *same generator* at different phases (a shared carrier = its partition-anchors); the real clumps are mutually near-orthogonal *content*, and a per-clump phase rotation leaves their pairwise similarity invariant (Klein-4 XOR algebra; confirmed: shared-carrier reconfigures 1.0→0.0, orthogonal content stays ~0.25). **An orrery needs all pointers off one mainspring.** srmech-native, sparse.

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-861_crank_into_real_store.py` (`hdc.klein4_{bind,similarity,random}`, `HV.from_sequence`, `rbs_lm.substrate.ContextSubstrate`) · **Composes / CORRECTS:** F860 (the crank — corrected here), F844–F848 (chirality-native encoder — the phase op is a first real piece), F853 (de-lens = dark-star), F778 (clumps), the user's "crank into the real store" direction (2026-06-18) · **User direction:** "crank into the real store — the most load-bearing but the biggest build."

## Built + validated: chirality-native continuous-phase op (the F844–F848 primitive)
Phase on a Klein-4 HV = **the fraction of slots carrying the γ₅ element**, applied as a *circular half-window* so it wraps:
`phase_state(hv, φ) = klein4_bind(hv, K(φ))`, where `K(φ)` holds γ₅ (sector 2) on a D/2-wide window starting at `φ·D` (mod D), identity (0) elsewhere.
| Δφ (turn) | sim | property |
|---|---|---|
| 0.00 | +1.000 | syzygy (in-phase) |
| 0.10 | +0.800 | smooth |
| 0.25 | +0.500 | linear in circular distance |
| 0.50 | +0.000 | antipode (orthogonal) |
| 0.90 | +0.800 | wraps (circular) |
Reversible (bind same key twice = identity), and σ-mirror (forward/backward phases equidistant from base). This is a genuine **continuous phase from discrete-per-slot sectors via population coding** — the missing F844–F848 op. **UPSTREAM candidate** for srmech (`klein4_phase` / `klein4_phase_bind`): no continuous Klein-4 phase op exists in 0.8.2 (logged).

## The NULL: cranking the real D=10000 store does not reconfigure the arrangement
Built the 5 de-lensed clumps as real Klein-4 HVs (`ContextSubstrate.bundle_odd` of `enc(token)`), gear-rate = mass, cranked θ over a full turn:
- mean pairwise sim **flat at ~0.255** across the whole crank (the Klein-4 4-sector chance baseline ≈ 0.25); tracked pair sim(scaffold,computing) span **0.01 = rigid**.
- "syzygy" (max mean sim 0.255) and "massless center" (bundle→clump max-sim ~0.49) are **flat** — no dynamic structure.
- **Only the structural reads transferred:** the **dark-star rate-horizon** (hub races 3.26 turns/crank, needs ~7 Nyquist samples vs 1–2 for the de-lensed cells → aliases first → unresolvable) and the **σ-mirror**.

## §CORRECTION to F860 — why the proxy moved and the real store doesn't
Confirmatory test (same phase op):
- **shared carrier, distinct phases** (orrery pointers off one mainspring): sim moves **1.000 → 0.800 → 0.500 → 0.000** with phase-gap. Reconfigures.
- **orthogonal content clumps, each phase-rotated**: sim **flat ~0.25** at every phase. No reconfiguration.

Klein-4 is XOR: `sim(a⊕Kᵢ, b⊕Kⱼ)` depends on `a⊕b ⊕ Kᵢ⊕Kⱼ`; when `a,b` are orthogonal content, `a⊕b` is ~uniform so the phase keys can't modulate the match rate → phase-invariant. F860's `the_one` pointers are the **same** 14-D generator at different phases (they share the constant partition-anchor coords), so their relationship *is* pure relative phase → it reconfigures. **The orrery works because every pointer descends from one mainspring (a shared carrier); independent content-bundles share no carrier, so a common crank cannot arrange them.** F860's "one crank drives the whole field" holds for the generator/shared-carrier, NOT for the raw orthogonal-clump store.

## Architectural consequence (the real next build)
A navigable orrery field requires clumps encoded as **phases on a SHARED carrier — position-primary, content-secondary** (the clump's *identity is its angle on a common dial*, content a minority tag), exactly the **position-keyed** form `encode_context` already uses (`pos_key`). Free orthogonal content bundles are the wrong substrate for crank-navigation. So "crank into the real store" resolves to: **re-encode the board as position/phase-primary on a shared carrier, then crank** — not bundle-of-content clumps.

## Verdict
Deliverable: the chirality-native continuous-phase op is built and validated (a real F844–F848 piece; UPSTREAM candidate). Result: cranking the raw store is a **NULL**, which **corrects F860's overreach** and yields the sharp architectural insight — the field must be a shared-carrier (position-primary) encoding for a crank to navigate it. Null findings count; evaluate by groundedness. srmech-native, 14-D + D=10000 sparse, ndarray-free, Class-K sign handling.
