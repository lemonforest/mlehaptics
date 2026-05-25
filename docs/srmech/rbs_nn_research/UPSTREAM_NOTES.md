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

(future notes accumulate here as they surface)
