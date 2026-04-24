# Antikythera-Maths — Phase-Operator Preflight (Phase 3)

**Sibling to** [../othello-maths/OTHELLO_PHASE_OP_PREFLIGHT.md](../othello-maths/OTHELLO_PHASE_OP_PREFLIGHT.md). This one is short for a reason — see below.

---

## TL;DR

The Antikythera's phase operator is **trivial**. There is one operator, σ_day, applied uniformly. There are no piece-types, no orbit-types, no flip-gates, no ray-directions, no dynamic gating. The mechanism is the simplest possible phase-operator system in the mlehaptics triad-plus.

```python
σ_day(D) = roll_operator(D, 1)              # single generator of ℤ/Dℤ
advance_day(date, D, days=1) =              # one day later
    encode_ant(date + days, D)              # re-encode (multi-dial state)
```

That's the entire phase operator: ~5 lines of code. The interesting work happens at decode time, where each dial extracts its own residue from the underlying day-counter via its gear ratio.

---

## Triad-plus comparison

| Project | Pieces / channels | Operator complexity |
|---|---|---|
| chess-maths | 6 piece types × 8 D₄ orbits | Rich operator set; per-piece per-orbit move kernels (§11.4–§11.6 build prompts). |
| othello-maths | 1 piece type × 8 ray directions × dynamic gating | Rich but different; flank-gating couples cells. |
| logo-maths | Command set + grammar | Structured but different; turtle state with motion-and-turn. |
| **antikythera-maths** | **1 operator, 13 projections** | **Trivial: one σ_day, dial-specific gear ratios at decode.** |

This is a feature, not a bug. The Antikythera is the **best pedagogical entry point** for the framework because every claim has an external grounding — one can check "is this really how the 127-tooth gear works?" against the physical mechanism rather than against a constructed Laplacian.

---

## The dial → projection table

Each dial is one cycle in the `astronomical_cycles.CYCLES` list. Its decode-time projection is its `cycle_modulus` and `cycle_period_days`:

| Dial | cycle_modulus | cycle_period_days | Projection formula |
|---|---:|---:|---|
| Metonic | 235 | 6939.69 | residue = floor(D · (date − ε) / 6939.69) mod D |
| Callippic | 940 | 27758.78 | residue = floor(D · (date − ε) / 27758.78) mod D |
| Olympic | 4 | 1460.97 | residue = floor(D · (date − ε) / 1460.97) mod D |
| Saros | 223 | 6585.32 | residue = floor(D · (date − ε) / 6585.32) mod D |
| Exeligmos | 669 | 19755.96 | residue = floor(D · (date − ε) / 19755.96) mod D |
| SiderealMonth | 254 | 6939.70 | residue = floor(D · (date − ε) / 6939.70) mod D |
| DraconicMonth | 242 | 6585.36 | residue = floor(D · (date − ε) / 6585.36) mod D |
| LunarAnomaly | 251 | 6916.19 | residue = floor(D · (date − ε) / 6916.19) mod D |
| Mercury | 145 | 16802.59 | residue = floor(D · (date − ε) / 16802.59) mod D |
| Venus | 289 | 168752.74 | residue = floor(D · (date − ε) / 168752.74) mod D |
| Mars | 133 | 103732.02 | residue = floor(D · (date − ε) / 103732.02) mod D |
| Jupiter | 76 | 30314.88 | residue = floor(D · (date − ε) / 30314.88) mod D |
| Saturn | 427 | 161425.06 | residue = floor(D · (date − ε) / 161425.06) mod D |

`ε = REFERENCE_JD = 1684595.0` (≈ 205 BCE epoch).

**B-H2 follows trivially:** σ_day is a unit in ℤ/Dℤ for every D (gcd(1, D) = 1). The "physical" crank-turn is the day-advance via re-encoding; the "algebraic" σ_day is the canonical generator on the day-counter ambient. The two coincide at design time; the build prompt's CONFIRMED tag is by construction.

---

## What a sequel could cover

This minimal phase operator means there is no follow-up "Phase Operator Build Prompt" for Antikythera the way there is for chess (§11.4, §11.5, §11.6) or Othello (PHASE_1C_PLAN). If a sequel were ever needed it would cover one of:

1. **An equant-bearing Mars encoder.** Add a per-dial epicycle-and-equant model so E-H2's Mars retrograde error matches the Greek mechanism's documented 38° peak. ~50 LOC; meaningful research finding.
2. **DE422 / DE441 ground truth.** Validate E-H1 against actual Hellenistic eclipses (200 BCE – 100 CE) instead of the modern Saros-anchor proxy. ~100 LOC plus ephemeris-cache management.
3. **Manufacturing-tolerance overlay.** Reproduce the Guillermo & Szigety 2025 simulation: introduce per-gear tooth-count noise (e.g., ±0.5 tooth per gear) and measure how dial accuracy degrades.

None of these requires a new phase-operator framework. The phase operator IS already trivial. Time spent here is best spent at the decode-projection or ground-truth layer, not at the operator layer.
