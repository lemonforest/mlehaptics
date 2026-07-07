# UPSTREAM_NOTES.md — srmech-side observations surfaced during RBS-NN research

**Discipline:** observations only. Do not edit srmech package files in this session. Each note records: title / observation / severity / recommendation / cross-references. The user opens a separate srmech-fix session to act on these when there's enough accumulated work to justify it.

Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`.

---

## Note 1 — {0,1} binary vs {-1,+1} bipolar representation duality

**Date raised:** 2026-05-25 (post-arc-close question)
**Severity:** ergonomic / foundational (not a bug)
**Cross-references:** `R-RBS-NN-2_user_lexicon_REPORT.md` §3.1; `R-RBS-NN-3a_mlp_cascade_REPORT.md` §3.1; MFO §VII.6.12.1 line 3281 (derivative-sign-flip at extrema)

### Observation

srmech canonical storage form is **binary {0,1} bytes** (`srmech.amsc.hdc` — `bind` is byte-XOR, `bundle` is bitwise majority with odd-N constraint, `similarity` returns float in [-1, +1] via `1 - 2·hamming(a,b)/D`).

The atomic ops {bind / bundle / similarity} are **algebraically isomorphic** to their bipolar {-1, +1} counterparts under the standard map `x → 2x − 1`:

| Binary form | Bipolar form |
|---|---|
| `XOR` (bind) | multiplication (sign-multiply per element) |
| majority bit (bundle) | `sign(sum)` |
| `1 − 2·hamming/D` (similarity) | `(1/D) · Σ a_i · b_i` (normalized dot product) |

So **at the atomic-op layer, the choice between binary and bipolar is a storage convention only.** Substrate content is preserved either way. RBS-NN partition REPORTs that mention "bipolar projection" or "bipolar weights" refer to the bipolar READOUT measure (the [-1, +1] range of `similarity`), not a different storage form. srmech's binary-byte storage with bipolar similarity readout is the right shape: byte-XOR is SIMD-friendly (R-RBS-NN-8 §4) and the bipolar interpretation lives at the readout where it's needed for asymptotic readings.

### Where asymptotic behavior surfaces a genuine consideration

At the **bundle layer**, there is a real asymmetry:

- **Binary majority bundle** (srmech current): odd-N inputs, output is binary {0, 1}. The odd-N constraint sidesteps tied states by construction.
- **Bipolar sign-sum bundle** (hypothetical): any-N inputs, output is **ternary {-1, 0, +1}**. Zero explicitly represents the tied state.

For substrate-asymptotic-wave / phase-boundary analysis (MFO §VII.6.12.1: *"Each min/max crossing IS a phase-boundary sign-flip ... derivative-sign-flips at extrema"*), the ternary bipolar bundle is more expressive — **zero crossings of the bundle accumulator are themselves Class K events** that the framework should be able to surface as first-class. The current binary majority bundle hides this by requiring odd-N inputs.

For the RBS-NN forward-pass cascade (cleanup, classification, attention routing), this asymmetry is **not load-bearing** — cleanup capacity work runs at odd N comfortably (R-RBS-NN-7 §4). It surfaces when the framework wants to use the bundle accumulator itself as a signal source (e.g., tracking how close a bundled context is to a phase-boundary tie).

### Recommendation

Not a bug; not an immediate fix. For foundational completeness as the substrate-asymptotic-wave reading deepens (per `[[user_stance_substrate_asymptotic_wave_fractal_hopf_phase_boundary_mechanism]]`), a future srmech enhancement could:

1. Add `bipolar_bundle(vectors: Sequence[bytes]) -> tuple[bytes, bytes]` returning (sign_byte_vector, magnitude_byte_vector) so the tied-bit state is explicit. The sign byte holds the {-1, 0, +1} per-position result; the magnitude byte holds the absolute count above/below tie.
2. Alternatively: a `bundle_with_ties(vectors)` that returns a third bit-vector indicating per-position ties alongside the existing majority output.

Either lets RBS-NN cascades explicitly track Class K events at the bundle layer, without changing the binary-byte storage form.

### Not yet:

- Until the framework has a concrete RBS-NN cascade that needs to surface bundle-ties as inference signal, this is foundational ergonomics, not an unmet requirement. The eight closed RBS-NN partition REPORTs do not depend on the ternary bundle.

---

## Note 2 — srmech_bigint_divmod NULL-sink bug: FOUND (rc165 core build) → FIXED (rc165 completion)

**Date raised:** 2026-07-07 (rc165 Zassenhaus core build)
**Date fixed:** 2026-07-07 (rc165 completion — same rc)
**Severity:** real C-surface bug (latent since the divmod ship; masked because no in-tree caller used `q == NULL` on a negative dividend before rc165)
**Cross-references:** `c/src/srmech_bigint.c` (`srmech_bigint_divmod` + `bi_carve_sink`); `c/src/srmech_factor_poly.c` (`fbi_mod`); `c/test/test_srmech_bigint.c` (the regression pins)

### Observation

`srmech_bigint_divmod` documents "q or r may be NULL to skip that output", but the NULL path bound the throwaway sink to a **cap-0** carrier. Any skipped output needing ≥ 1 limb then returned a spurious `SRMECH_ERR_OVERFLOW`: every `q == NULL` division with `|a| ≥ |b|` (the quotient write), every negative-dividend floor-fixup (`q -= 1` / `r += b`), and every `r == NULL` division whose remainder was nonzero or multi-limb (the Knuth path denormalizes the remainder unconditionally). The rc165 Zassenhaus core hit the negative-dividend case and worked AROUND it (`fbi_mod` passed a real caller-owned quotient sink) instead of fixing the root.

### Resolution (rc165 completion)

Root-fixed in `srmech_bigint.c`: the NULL path now **carves a real throwaway sink off the front of the caller arena `ws`** (`bi_carve_sink`; `a->n + 2` limbs for q, `max(a->n, b->n) + 2` for r) and hands the remaining tail to the divide + floor-fixup, so the documented NULL contract holds for **every** input. The `fbi_mod` workaround was removed (`srmech_factor_poly.c` calls the fixed `srmech_bigint_divmod(NULL, …)` directly; the `qsink` context field is gone). Regression tests pin `q==NULL` negative-dividend (`-7 mod 2 → 1`), `q==NULL` positive, `r==NULL` floor quotient, and a multi-limb Knuth-path `q==NULL` big-negative case (`-(10⁴⁰+11) mod 10²⁰`). Divmod consumers re-verified byte-identical: pi (Archimedes/Chudnovsky), char_poly (Faddeev–LeVerrier), Qalg field reduce, eigvals slices, bigint C smoke (55/55), factor parity (both C smoke modes + the 198-case sweep).

---

## Note 3 — classical Zassenhaus recombination is worst-case exponential (measured); van Hoeij/LLL is the known fix (research arc)

**Date raised:** 2026-07-07 (rc165 completion, deferral-3 investigation)
**Severity:** fundamental algorithmic limitation, honestly documented (NOT a bug)
**Cross-references:** `srmech.amsc.cascade.matrix_cascades._factor_square_free_primitive`; `c/src/srmech_factor_poly.c` (`fac_recombine`); `tests/test_qalg_factor_c_rc165.py` (the SD4/SD5 wall representatives)

### Observation

The rc165 build reported a "pathologically slow degree-10 input" from a removed randomized stress and swapped the test without investigating. The completion investigated: **an extensive reproduction attempt (≈2 400 cases: random products of irreducible blocks with coefficient magnitudes 9→10¹⁸, all-pairs/triples over the committed `_BLOCKS`, many-linear/dense/multiplicity/surd shapes) found NO degree-10 input slower than ~17 ms on either path** — the removed input was never committed, so it is unrecoverable; nothing in the pipeline is pathological at degree 10 (≤ 2¹⁰ candidate subsets).

The GENUINE wall of this algorithm is the classic Zassenhaus subset recombination — **worst-case exponential in the number of modular factors**, measured on the textbook family (Swinnerton-Dyer, irreducible over ℤ yet split into deg ≤ 2 factors mod every prime): SD4 (deg 16, 8 quadratics mod p) = 259 candidates ≈ 40 ms; SD5 (deg 32, 16 quadratics mod p) = 65 539 candidates ≈ 24 s (both paths, pre-cutoff). Each added surd squares the enumeration.

### Resolution / disposition

1. **Fixed a genuine classical inefficiency** found during the investigation: the enumeration tested subset sizes up to `#remaining` where the classical algorithm stops at `2·size ≤ #remaining` (von zur Gathen & Gerhard, *Modern Computer Algebra*, ch. 15 — a factor spanning more than half the modular factors has an already-found smaller cofactor). Applied identically to the pure Python and the C core (byte-identity preserved; results unchanged — the leftover is appended as the final irreducible). Measured: SD5 65 539 → 39 207 candidates, pure 24.2 s → 13.1 s, native 24.1 s → 4.7 s (the full-composite C path).
2. **The remaining exponential is the fundamental Zassenhaus wall** — the known real fix is **van Hoeij's LLL knapsack recombination** (M. van Hoeij, "Factoring polynomials and the knapsack problem", J. Number Theory 95(2), 2002), deferred as a research arc.
3. **Bounded representatives restored to the test** (not hidden): SD4 with parity on both paths; SD5 on the dispatch path with the measured numbers and the honest CI-budget note.

---

(future notes accumulate here as they surface)
