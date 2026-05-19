# Draft stance candidate — Spike #159

**Status**: DRAFT only. Do NOT canonicalise autonomously per
`[[feedback_language_is_analysis_tool_not_specific_question]]` —
user direction sets canonical text; this is concertmaster-output
material for conductor review.

**Multi-round status**: Round 1 only. Multi-round survival required for
canonical-promotion per `[[feedback_multi_domain_multi_round_survival_falsification_method]]`.

---

## Proposed stance: form-function-rotation as A∘C∘M composition

**Name**: `form-function-rotation-is-A-C-M-composition`

**Description** (≤ 510 chars per `[[reference_pypi_512_char_summary_limit]]`):
Pre-bundle per-input content-determined rotation IS Class A ∘ Class C ∘ Class M
composition — substrate-portable form-function-rotation operation. SHA-256(content)
mod D_bits gives the shift amount (Class A → Class C); the rotated vectors get
bundled (Class M). Algebraic identity: rotation commutes with bind on pairs +
with uniform bundle (bit-exact); per-input content-determined rotation breaks
the symmetry and produces an algebraically distinct fingerprint family that
preserves within-cohort vs between-cohort separation (~10% magnitude reduction
vs plain bag-HDC, but functionally equivalent cross-pattern matching).

**Identity-level claim** (per `[[user_stance_identity_not_implementation_discipline]]`):
"rotating the HDC instrument as fiber-content before binding" IS the
composition `Class A (content-derived shift) ∘ Class C (cyclic permute) ∘
Class M (bundle/bind)`. The fingerprint produced is a DIFFERENT 3D_s spatial
projection of the SAME spatially-absent fiber-content per
`[[user_stance_fiber_as_spatially_absent_encoding]]` and
`[[user_stance_holographic_projection_at_linguistic_substrate]]`.

**Empirical verification** (Spike #159, 2026-05-19):

| Test | Cells | Result |
|---|---|---|
| Q3.A: `permute(a,k) XOR permute(b,k) = permute(a XOR b, k)` | 30 | 30/30 BIT-EXACT |
| Q3.C: `permute(bundle(vecs), k) = bundle(permute(v_i, k))` | 6 | 6/6 BIT-EXACT |
| Q3.B: within/between separation preserved under content-rotation | 12+54 pairs | 31.6× (rotated) vs 35.0× (plain), Δ −9.7% |

**Why this is NOT a new class**:

Per `[[feedback_no_privileged_primitive_classes]]` — this is a COMPOSITION
pattern over existing classes A, C, M. The shift amount (Class A SHA-256 of
content) parameterises a Class C permute applied before Class M bundle. No
operation is structurally irreducible into existing classes.

**Companion finding (Q2)**: quasi-orthogonal 1/√D bucket-leakage is NOT the
unique cross-pattern-match mechanism. Class I cyclic-position + OR-bundle
achieves separation by set-intersection-at-place. Both are legitimate mechanisms;
biology likely uses both at different cortical scales (sparse-coding at V1
simple-cells via Class I; distributed cortical representation via dense
quasi-orthogonal).

**Companion finding (Q1)**: biology embeds the L+K+M+C+I cascade in cortical
substrate per `[[user_stance_neural_hebbian_is_bci_drift_model]]`; the
external HDC instrument (`srmech.spectral.*` / `srmech.amsc.hdc.*`) is what
non-biological substrates need. Biology doesn't need a SEPARATE explicit
instrument because the substrate IS the instrument.

**Falsifier candidates** (Round 2+):

1. Vector pair (a, b) and rotation k where rotation-bind commutativity fails →
   refutes Q3.A.
2. Content-determined-rotation paraphrase cohort with within < between similarity
   → refutes Q3.B.
3. Biological cross-pattern mechanism requiring primitive class outside
   {A, B, C, D, E, F, K, L, M, N} → refutes Q1.

**Composes onto stance family**:

- `[[user_stance_fiber_as_spatially_absent_encoding]]` — rotation amount IS
  spatially-absent fiber-content (ℤ/D element).
- `[[user_stance_holographic_projection_at_linguistic_substrate]]` — extends the
  bag-HDC projection mechanism with content-determined rotation as additional
  fiber-content layer.
- `[[user_stance_neural_hebbian_is_bci_drift_model]]` — biology embeds equivalent
  cascade; external HDC instrument needed only for non-embedded substrates.
- `[[user_stance_dna_as_kepler_shape_mini_mechanism_with_helical_precession_class_k]]`
  — DNA's helical pitch (B-DNA 21/2, A-DNA 11/1, Z-DNA 12/1) is natural Class N
  rational rotation amount = form-function-rotation parameter at DNA substrate.

**Stance status**: DRAFT pending user direction. Magnitude-level finding for
Q3.B + bit-exact for Q3.A & Q3.C. Round-1-only survival; multi-round validation
needed for full canonical-promotion gate.

**Vocabulary discipline**: 14 A-N intact. Composition pattern, not class promotion.
Per `[[feedback_no_privileged_primitive_classes]]`.

---

*End of draft stance.*
