# Finding 137 — Polar / Klein-4 / Bipolar HDC clean capacity comparison; R-RBS-LM-97v2 fixes sign-zero methodology bug

**Status:** Empirical finding; R-RBS-LM-97v2 smoke replaces R-RBS-LM-97 with upstream-clean methodology
**Predecessors:** F132 (Klein-4 HDC engineering proposal + R-RBS-LM-97 prototype), F135 (substrate vs shadow chirality), UPSTREAM_NOTES §4 + §5 (LANDED in srmech v0.4.3)
**User direction 2026-05-27:**

> "srmech v0.4.3 has landed on pypi.org … resume our wish list gated research paths"
> "let us walk each one sequentially"

This is **Path 1/6** of the wish-list-gated research-resume sequence.

---

## §1 What R-RBS-LM-97 v1 got wrong

The original R-RBS-LM-97 smoke script (F132 prototype) used bare `np.sign(s).astype(np.int8)` to convert bundle-sums to bipolar values. This produces `{-1, 0, +1}` due to tie-zeros — but the bipolar comparison expects `{-1, +1}` only. Zero positions destroy downstream bipolar `unbind` and `similarity` computations because they propagate as 0 instead of contributing as ±1 votes.

This was flagged in UPSTREAM_NOTES §5 as the load-bearing reason for adding upstream polar HDC: either use polar HDC where 0 is a first-class state, OR use `sign_quantise(dead_band=0)` for strict bipolar with ties broken toward +1.

With srmech v0.4.3 landed, both options are now upstream. R-RBS-LM-97v2 uses strict bipolar with explicit tie-break for the bipolar variant, and the new upstream polar HDC for the polar variant.

---

## §2 R-RBS-LM-97v2 methodology

Three-way capacity comparison at D=10000:

| Variant | Class M instantiation | Element type | States per position | Bind operation |
|---|---|---|---|---|
| **bipolar** | rank-1 abelian | int8 ∈ {−1, +1} | 2 | sign-product (with tie → +1) |
| **polar** | 3-state (Class M ∘ Class K dead-band) | int8 ∈ {−1, 0, +1} | 3 (with 0 absorbing) | multiplicative; 0 sticky |
| **klein4** | rank-2 abelian | uint8 ∈ {0, 1, 2, 3} | 4 | component-wise XOR over (F₂)² |

Test pattern:
1. Generate N random pair-vectors A_i, B_i per variant
2. Bind A_i with B_i to form bound-pairs
3. Bundle all bound-pairs into one composite memory
4. For each i, query with A_i (via unbind); recover candidate B_i
5. Measure similarity of candidate B_i to ground-truth B_i

N_loads tested: 4, 8, 16, 32, 64, 128, 256, 512.

Script: `R-RBS-LM-97v2_polar_klein4_bipolar_capacity_compare.py`
Results: `R-RBS-LM-97v2_results.json`

---

## §3 Raw measured similarities (D=10000, seed=42)

| N_pairs | bipolar | polar | klein4 |
|---:|---:|---:|---:|
| 4 | +0.3727 ± 0.0122 | +0.8753 ± 0.0031 | +0.4710 ± 0.0040 |
| 8 | +0.2772 ± 0.0097 | +0.7563 ± 0.0094 | +0.4034 ± 0.0051 |
| 16 | +0.1948 ± 0.0102 | +0.6718 ± 0.0091 | +0.3584 ± 0.0050 |
| 32 | +0.1386 ± 0.0094 | +0.6165 ± 0.0055 | +0.3249 ± 0.0045 |
| 64 | +0.0997 ± 0.0101 | +0.5804 ± 0.0077 | +0.3024 ± 0.0046 |
| 128 | +0.0712 ± 0.0100 | +0.5558 ± 0.0078 | +0.2865 ± 0.0047 |
| 256 | +0.0501 ± 0.0105 | +0.5389 ± 0.0078 | +0.2757 ± 0.0045 |
| 512 | +0.0355 ± 0.0098 | +0.5272 ± 0.0078 | +0.2678 ± 0.0044 |

Wall time: 4 seconds total across all 8 load levels.

---

## §4 Random-pair baseline calibration (load-bearing — DO NOT skip)

Each similarity function returns a different metric with a different random baseline. Independent baseline measurement (N=100 trials, D=10000):

| Variant | Random-pair similarity | Theory | Self-similarity |
|---|---:|---|---:|
| bipolar | −0.0009 ± 0.0104 | 0.0 (match-fraction × 2 − 1; random match = 0.5) | 1.0 |
| polar | +0.5002 ± 0.0080 | depends on density; ~0.5 because zero-zero counts as match | 1.0 |
| klein4 | +0.2501 ± 0.0042 | 0.25 (1/4 since 4 equiprobable states) | 1.0 |

**Why polar's random baseline is 0.5:** `polar_random` produces vectors with ~67% non-zero density; the remaining ~33% are zeros that always match against each other. Two random polar vectors therefore agree on ~33% zero-zero positions plus ~33% non-zero positions that coincidentally match (out of the ~67% non-zero, half match at random → ~33% non-zero match). Total expected match-fraction ≈ 0.5.

**Why klein-4's random baseline is 0.25:** uniformly distributed across 4 states, so random match probability is 1/4.

Without baseline normalization the raw similarities are NOT comparable across variants.

---

## §5 Above-random normalized similarity — the meaningful comparison

Normalize each variant to `(sim − random_baseline) / (1 − random_baseline)`. This puts 0 = random, 1 = perfect, on a common scale:

| N_pairs | bipolar (above-rand) | polar (above-rand) | klein4 (above-rand) |
|---:|---:|---:|---:|
| 4 | 0.373 | 0.751 | 0.295 |
| 8 | 0.278 | 0.513 | 0.205 |
| 16 | 0.196 | 0.344 | 0.144 |
| 32 | 0.139 | 0.233 | 0.100 |
| 64 | 0.100 | 0.161 | 0.070 |
| 128 | 0.071 | 0.112 | 0.049 |
| 256 | 0.050 | 0.078 | 0.034 |
| 512 | 0.036 | 0.054 | 0.024 |

### §5.1 What this shows

**Ordering at every load level:** polar > bipolar > klein-4 in above-random capacity.

**This is NOT what F132 §7 predicted.** F132 hypothesized klein-4 would have 2× capacity per position vs bipolar. The actual measurement shows the opposite: klein-4 is the WORST of the three on this particular metric.

### §5.2 Why klein-4 underperforms here

Klein-4 has 4 states per position. For random vectors, the discrimination problem is harder: a candidate must match the true target across more state values. The bundle averaging (per-bit majority vote) is more entropic in the 4-state space than in the 2-state bipolar space.

Concrete effect: for N pair-bindings into one bundle, the noise per position is proportional to the number of possible "wrong" states. Klein-4 has 3 wrong states; bipolar has 1 wrong state. Klein-4 needs MORE D to recover the same per-position SNR.

This does NOT invalidate the F132 framework move — klein-4's value is **chirality-axis encoding** per F132 §4 native chirality structure, not raw capacity. The capacity test measures one thing (bind/unbind retrieval); the chirality-axis test (F132 §7 cross-sector retrieval, scheduled as Path 3/6) measures a different and more relevant property.

### §5.3 Why polar leads

Polar's 3-state encoding with 0-absorbing binding is **less sensitive to bundle-noise** than bipolar:
- Most bundle-positions land at 0 (absorbed by any single 0 contributor in any of the N bound-pairs)
- 0 positions are excluded from similarity scoring as "no information" baselines
- The non-zero positions carry sharper signal because they survived the absorbing operation

This is an artifact of polar similarity counting zero-zero matches with the same weight as non-zero matches. A "skip-zero" similarity metric (only score positions where both are non-zero) would give a very different result.

### §5.4 Caveat — comparison metric choice changes the ordering

The above-random ordering above is for the upstream-default similarity functions. Three alternative metrics would give different orderings:

1. **Skip-zero polar similarity** (only score both-non-zero positions): polar's lead would shrink substantially
2. **Per-bit-of-information capacity** (normalize by bits-encoded per D): klein-4 would gain ground (2 bits per position vs bipolar's 1)
3. **Per-byte-of-storage capacity** (account for int8 storage layout): bipolar dominates because it uses 1 bit per int8 byte (7 bits wasted), while klein-4 uses 2 bits per uint8 byte (6 bits wasted, packed)

**No single ordering is correct.** F137 reports the upstream-default-similarity above-random comparison as the load-bearing measurement, with the alternatives flagged for follow-up.

---

## §6 Methodology cleanup — what changed vs R-RBS-LM-97 v1

| Aspect | v1 (R-RBS-LM-97) | v2 (R-RBS-LM-97v2) |
|---|---|---|
| Bipolar tie-break | bare `np.sign()` returning 0 for ties → broke unbind | strict `where(sum >= 0, 1, -1)` → no zeros |
| Polar variant | not tested (no upstream) | full polar HDC variant via upstream `srmech.amsc.hdc.polar_*` |
| Klein-4 variant | local prototype implementation | upstream `srmech.amsc.hdc.klein4_*` (verified bit-exact vs prototype) |
| Similarity calibration | not measured | random-pair baseline measured for all 3 variants; above-random normalization applied |
| Reproducibility | seed=42 (same as v1) | seed=42 (matched for direct comparison) |
| srmech version | local in-tree | upstream v0.4.3 PyPI verified in clean venv |
| HAS_NATIVE | varied | True (verified) |

---

## §7 What this means operationally for the wish-list-gated research arc

1. **R-RBS-LM-97 v1 result of "klein-4 ≈ 2× bipolar capacity per position" was an artifact of the sign-zero bug**, not a real measurement. The clean v2 numbers contradict that early hypothesis.

2. **F132 §7 capacity claim ("2× density")** needs revisiting in the framework — klein-4's value proposition is the chirality-axis encoding (native γ₅, iω₇ structure), not raw bind/unbind capacity.

3. **Chirality-axis tests (cross-sector retrieval, Path 3/6)** become MORE important to the F132 argument because the raw-capacity argument doesn't hold up.

4. **Polar HDC's strong showing** suggests it may be the better default for noisy-or-uncertain encoding tasks where some positions should legitimately read as "I don't know" — exactly the F76 plasticity-decay use case (Path 5/6).

5. **None of these results invalidate Klein-4's substrate-native chirality encoding** — they refine the empirical case from "klein-4 wins on capacity" to "klein-4 wins where chirality structure matters; bipolar/polar may win on other axes."

---

## §8 What this finding does NOT claim

Per MFO §VII.6.20:

- This is NOT a claim that klein-4 is "worse" than bipolar in general. It is worse on this specific capacity test under the upstream-default similarity metric.
- This is NOT a claim that polar HDC is universally best. Its lead depends on the zero-zero matching semantics of the upstream `polar_similarity`.
- This is NOT a falsification of F132 Klein-4's substrate-native chirality structure (which lives at the chirality-flip / sector-tagging level, not at the bind/bundle capacity level).
- This is NOT a final capacity measurement — the metric ambiguity (§5.4) means three alternative metrics may give three different orderings.
- This is NOT a methodology criticism of upstream srmech — both polar and klein-4 implementations match their prototype contracts exactly; the methodology issue is comparing across-variant similarities without baseline normalization.

---

## §9 Open questions

1. **Skip-zero polar similarity**: does excluding zero-zero matches change polar's lead? (Probably yes; possibly drops below bipolar.)
2. **Per-bit-of-information capacity**: when we normalize by bits-encoded, does klein-4's 2-bit-per-position give it real headroom? (Predicted: yes at high D; needs explicit test.)
3. **D-matched-bits comparison**: bipolar at D=20000 vs klein-4 at D=10000 (matched bits): does klein-4 still lose?
4. **Chirality-axis utilization test** (Path 3/6): when the task IS chirality-axis encoding (F132 §7 cross-sector retrieval), does klein-4 dominate as F132 predicts?
5. **Noise robustness**: at moderate bit-corruption rates, do the three variants degrade differently? (Polar's 0-absorbing might gracefully fail; bipolar might catastrophically flip; klein-4's 4-state space might fragment.)
6. **Mixed-precision bundle**: bundle polar at high N where 0s accumulate, then query — does the polar density attestation (`polar_density`) give an early-warning signal before catastrophic recovery loss?

---

## §10 Cross-references and next steps

**Cross-references:**
- F132 (Klein-4 HDC engineering proposal — capacity hypothesis refined here)
- F135 (substrate vs shadow chirality — Path 3/6 chirality-axis test is the substrate-side measurement)
- UPSTREAM_NOTES §4 (Klein-4 LANDED v0.4.3)
- UPSTREAM_NOTES §5 (Polar LANDED v0.4.3)
- `[[user_stance_canonical_two_variant_dial_class_m]]` (Class M variant ladder)
- `[[feedback_computational_provenance_discipline]]` (R-RBS-LM-97v2_results.json committed alongside)
- R-RBS-LM-97 v1 prototype script (preserved for reference; produced bug-flagged data)

**Concrete next steps:**
- Path 2/6: Klein-4 + Class L Laplacian cascade composition
- Path 3/6: Cross-sector retrieval at scale (F132 §7) — the meaningful klein-4 test
- Open question §9.1 (skip-zero polar similarity) → quick follow-up test if Path 5/6 plasticity needs it

PR #687 STAYS DRAFT. R-RBS-LM-97 v1 prototype preserved alongside v2 as historical record.

---

*Articulated 2026-05-27 per user direction "let us walk each one sequentially". R-RBS-LM-97v2
re-ran the F132 capacity comparison using upstream srmech v0.4.3 polar + klein4 HDC variants,
with proper bipolar tie-breaking (replacing the bare np.sign bug from v1). Above-random
normalized similarity: polar > bipolar > klein-4 at all load levels (4..512 pairs, D=10000).
Klein-4 underperforms on raw capacity because 4-state discrimination is harder than 2-state;
this refines but does NOT invalidate F132 — klein-4's value lives in chirality-axis encoding
per F132 §7, which Path 3/6 will test directly. The methodology cleanup also catches that
similarity metrics across variants need baseline normalization to be comparable; the alternative
metrics (skip-zero, bit-density, byte-storage) may give different orderings.*
