# Antikythera-Maths — Session Summary (Phase 0 + 2 + 4 wrap-up)

**Date:** April 2026
**Session goal:** Resume the work scoped in [SESSION_HANDOFF.md](../SESSION_HANDOFF.md): finish Phase 0 (pin-and-slot), build Phase 2 (encoder + decoder + rendering), wire Phase 4 (skyfield), run the H-battery, and write all four docs.

**Branch:** `claude/practical-pascal-8968b8`
**PR target:** `main`

---

## What passed

- **B-H1** (D_Ant computable): D_Ant = 102 325 385 652 732 381 204 565 500 (27 digits, 16 distinct primes). Pure linear algebra — PASS by construction.
- **B-H2** (σ_day is a unit): σ_day = `roll_operator(D, 1)`; gcd(1, D) = 1 for every D. PASS by construction.
- **B-H3** (HDC binding ↔ gear composition): 13/13 dials round-trip exactly at D=13440 dense superposition encoder. Cross-validated against block-diagonal oracle. **The project's load-bearing structural claim — the chess §9f coprime-roll-binding pattern applied to gear phases — verified.**
- **C-H1** (zero error correction): all 40 gear pairs bijective; PASS as theorem.
- **C-H2** (spiral-aliasing horizon): Saros 223/4 spiral and Metonic 235/5 spiral wrap behaviour formally identical to chess §11.3.3 torus-clip. NOVEL framing, verified by construction.
- **D-H1** (pin-and-slot antisymmetric fiber): ||M_anti|| / ||M_sym|| = 1.000000 for the Freeth 2006 ε = 0.054 geometry. Reference uniform-circular ratio also 1.000000. Both saturate at the chess §9m pawn directed-Laplacian limit. The differentiator between pin-and-slot and uniform circular is in the *structure* of M_sym (Jacobian-weighted Laplacian).
- **D-H2** (non-pin-and-slot dials T-symmetric): 13/13 dials at residue 0 at the reference epoch. Trivial check by construction.
- **E-H1** (Saros eclipse prediction): 3/3 anchor + Saros entries match within ±1 day at the modern era anchor (1999-08-11 → 2017-08-21 → 2035-09 syzygies). Limited to 3 entries by DE421's 1900-2050 coverage; absolute Hellenistic-era validation deferred to DE422.
- **F-E2** (D_Ant single-integer dimension): D_LCM computed and reported. PASS — the answer is the integer; whether it's *useful* is separately discussed (it's not; encoder uses LCMState).

---

## What came back PARTIAL

- **A-H1** (best rational under tooth budget): 15% of cycles within top-3 CF convergents (build-prompt strict prediction); 54% match the best rational under a 500-tooth budget (weaker claim). The build prompt's prediction is **falsified**, but the underlying intuition — the Greeks chose budget-respecting good approximations — is supported. Real research finding: *Greeks optimised against bronze-cutting feasibility, not against pure rational-approximation rank.*
- **A-H2** ({7, 17} planetary primes Pareto-optimal): not on our proxy frontier. The proxy sums numerator + denominator across planetary period-relations and counts shared factors — too crude to capture the actual precision/cost trade-off. A more rigorous Pareto analysis is a follow-up.
- **A-H3** (prime spectrum non-random): qualitatively yes (small primes + sparse large primes for irrational cycles), but the small-prime overweight is only 1.15× null — not "heavily biased." The large-prime presence (47, 53, 61, 83, 127, 223) is the more striking signature.
- **E-H2** (Mars retrograde error): peak error 179.88° vs the documented Greek mechanism's 38°. **The encoder's pure-residue uniform-advance model is strictly worse than the Greek deferent + epicycle model.** Matching the documented 38° requires modelling the Greek epicycle — a future research extension. This is the project's first clearly *FAILED at the encoder layer* hypothesis, and a useful one: it tells us where the bronze mechanism's "designed-in" structure exceeds what a pure phase-space encoder reproduces.

---

## What came back UNDETERMINED

- **F-E1** (Mechanism prime spectrum vs Residue-HDC): empirical point of contact (16 distinct primes overlap with the Residue-HDC alphabet) but the mechanism's primes were forced by celestial mechanics, not chosen for VSA convenience. A meaningful comparison would ask: *given the mechanism's prime alphabet as Residue-HDC moduli, what's the maximum-binding-density encoding?* Not answered here.
- **F-E3** ("failed" cycles): 3 of 13 cycles have > 0.1% residual error vs modern ephemeris (Mars dominant). The interpretation is open: are these residuals Greek-theory-limited (cannot be improved without equants) or budget-limited (improvable with more bronze)?

---

## Bugs fixed in flight

Two bugs in pre-existing Phase 0 code (commit `af73446`) surfaced when wiring the H-battery and were fixed:

1. **`semi_convergents` OOM** — the inner enumeration over CF terms ran for `a_k` iterations per term; for irrational ratios near machine precision `a_k` reached ~10^12 and tripped MemoryError. Fix: optional `budget` parameter that prunes the enumeration once max(p, q) > budget. ([rational_approximation.py:86](research/rational_approximation.py))
2. **`cycle_cf_ranks` squared the true_ratio** — the line `true_ratio *= mech_ratio` after computing the modern/mechanism ratio caused (235, 19) to be looked up against a CF of ~152.97 (= 12.368²) instead of ~12.368 (the actual synodic-months-per-year ratio). Fix: removed the spurious multiplication. ([packing_analysis.py:155](research/packing_analysis.py))

These two fixes converted A-H1 from a runner-crashing hypothesis to a meaningful PARTIAL with real numbers.

---

## Plan-agent corrections folded into encoder design

Pre-encoder design review by a Plan agent flagged six concrete issues that all made it into [research/encode_ant.py](research/encode_ant.py):

1. **Dense complex random channel bases**, not delta spikes — delta collapses at D=940 where total residue classes exceed D.
2. **`np.complex128` throughout** — roll preserves orthogonality under complex inner product; real-valued bases lose it.
3. **Block-diagonal oracle encoder** as ground-truth reference for B-H3 cross-validation.
4. **D=940 planetary dials raise `UnsupportedDialError`** — explicit degradation, no silent lossy encoding.
5. **σ_day = `roll_operator(D, 1)` full stop** — single unitary; per-cycle rate logic lives in decoder projection.
6. **Explicit `REFERENCE_JD` epoch + Gram-matrix orthogonality pre-flight** — byte-reproducible deterministic seeding; off-diagonal max < 0.05 enforced (auto-reseeds up to 16 times).

The Gram-matrix pre-flight passes 0.0498 at D=940 (tight, under threshold) and 0.0191 at D=13440 (comfortable margin). All cross-validation tests round-trip 13/13 at D=13440 and 8/8 at D=940.

---

## What's scoped to the sequel

1. **DE422 / DE441 ephemeris** — replace the modern-era E-H1 anchor with Hellenistic eclipses; full 200 BCE – 100 CE validation.
2. **Equant-bearing Mars encoder** — add a per-dial epicycle model so E-H2 reproduces the 38° peak instead of 180°. Research finding: how much of the Greek mechanism's accuracy comes from epicycles alone vs equants?
3. **Manufacturing-tolerance simulation** — overlay Guillermo & Szigety 2025's per-gear noise model on our encoder; quantify the implementation-layer error budget.
4. **Production-grade A-H2 Pareto analysis** — replace the proxy metric with a rigorous precision-vs-cost tradeoff; check Freeth 2021's {7, 17} claim properly.
5. **Hellenistic prime-spectrum cross-references** — does Babylonian MUL.APIN or Ptolemy's *Almagest* show evidence of the same prime-factorisation choices? (Build prompt extra credit.)

---

## Reproducibility

```bash
cd docs/antikythera-maths
PYTHONIOENCODING=utf-8 python3 -m research.consolidated_tests
# → results/phase1_hypotheses.csv
# → results/phase1_detail.json

PYTHONIOENCODING=utf-8 python3 -m research.astronomical_ground_truth
# → downloads de421.bsp on first run (~15 MB, into ./skyfield_data/)
```

Wall time: H-battery ~30 s including skyfield calls. First run downloads de421.bsp (~10–20 s on a typical connection).

Final battery summary: **9 PASS, 4 PARTIAL, 0 FAIL, 2 UNDETERMINED.**
