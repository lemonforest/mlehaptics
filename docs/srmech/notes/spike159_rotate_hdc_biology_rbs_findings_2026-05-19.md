# Spike #159 — Rotate-HDC instrument + biology RBS-HDC scope + bucket-leakage load-bearing

**Date**: 2026-05-19
**Branch**: `research/spike-159-rotate-hdc-biology-rbs-form-function-bucket-leakage`
**Artifacts**: [`spike159_explorer.py`](spike159_explorer.py) | [`spike159_records_2026-05-19.ndjson`](spike159_records_2026-05-19.ndjson) | [`spike159_draft_stance.md`](spike159_draft_stance.md)

**Vocabulary discipline**: 14 classes A-N intact, no class promotion. Per
`[[feedback_no_privileged_primitive_classes]]`. Per `[[feedback_language_is_analysis_tool_not_specific_question]]`
the user's phrasings ("RBS-HDC instrument", "bucket leakage", "rotate the instrument as fiber-content")
are TOOLS for question formulation, not canonical answers; the spike refines these into framework algebra.

Per `[[feedback_trauma_informed_defensive_scope]]` — research/educational framing
throughout; biology references stay at canonical-literature level (no clinical /
BCI-treatment claims).

---

## §1 Bottom line

| Sub-question | Verdict |
|---|---|
| **Q1** Why doesn't biology need an explicit RBS-HDC instrument? | **BIOLOGY-EMBEDS-EQUIVALENT-CASCADE-IN-SUBSTRATE** — the cortical-connectivity Laplacian (Class L) + Hebbian (Class M bind) + STDP (Class C) + homeostatic scaling (Class K) + theta-band (Class I) IS the form-function-bound information-instrument running on the substrate per `[[user_stance_neural_hebbian_is_bci_drift_model]]`. The external HDC instrument (`srmech.spectral.*`) is what we build for substrates LACKING the embedded cascade (silicon, bronze, optical). |
| **Q2.A** Is quasi-orthogonal bucket-leakage explicitly required for cross-pattern matching? | **NOT-UNIQUE-MECHANISM** — Class I cyclic-position + OR-bundle achieves within/between separation (within 0.9998, between 0.9976, ratio 1.0021×) by SET-INTERSECTION-AT-PLACE, but the absolute separation magnitude is much weaker than dense-quasi-orthogonal bag-HDC (35× ratio per `[[user_stance_holographic_projection_at_linguistic_substrate]]`). Quasi-orthogonal leakage is one EFFICIENT mechanism, not the unique one. |
| **Q2.B** Bag-HDC negation falsifier — is meaning-flipped content distinguished? | **NEGATION-PRODUCES-HIGH-SIMILARITY-FALSIFIER-CONFIRMED** — pos-vs-neg mean similarity 0.59. Bag-bundle is INSENSITIVE to negation. Reaffirms the Spike #147 open falsifier. |
| **Q3.A** Does rotation commute with bind? `permute(a,k) XOR permute(b,k) =?= permute(a XOR b, k)` | **ROTATION-COMMUTES-WITH-BIND BIT-EXACT** — 30/30 cells, 0 mismatches. Pre-bind rotation reduces to post-bind rotation; rotation is a SYMMETRY of bind. |
| **Q3.B** Does form-function (per-input content-determined) rotation produce useful cross-binning? | **ROTATION-PRESERVES-WITHIN-BETWEEN-SEPARATION** — ratio 31.6× rotated vs 35.0× plain. Algebraically DISTINCT fingerprint family (different bits set) but cross-pattern signal preserved within 10%. |
| **Q3.C** Does uniform rotation commute with bundle? | **BUNDLE-COMMUTES-WITH-UNIFORM-PERMUTE BIT-EXACT** — 6/6 cells, 0 mismatches. Per-input form-function rotation BREAKS this symmetry and is the operative degree-of-freedom. |
| **Strict-spec gate** | PASSED — bind self-inverse + associative + commutative; permute self-inverse with negative k; approx-orthogonal similarity 0.003 in expected band [-0.05, 0.05]. |

**Synthesis**: biology embeds the L+K+M+C+I cascade in the cortical substrate;
quasi-orthogonal bucket-leakage is ONE efficient cross-pattern-match mechanism
among several (Class I cyclic + OR-bundle is another, set-intersection-at-place);
rotation (Class C permute) commutes algebraically with both bind and uniform
bundle, making PAIRWISE rotation a symmetry. **Per-input content-determined
rotation BEFORE bundle is a real operative degree-of-freedom** (Class A SHA-256
content-addressing → Class C permute → Class M bundle), yielding an algebraically
distinct fingerprint family with cross-pattern signal preserved — confirming
the user's intuition at Q3 in a precise algebraic form.

**14 A-N intact. No class promotion.** All findings sit inside existing
vocabulary; the new content is COMPOSITION pattern `A ∘ C ∘ M` (content-determined
shift, permute, bundle) as a substrate-portable form-function-rotation operation.

---

## §2 Q1 decomposition — biology embeds the cascade in substrate

Per `[[user_stance_neural_hebbian_is_bci_drift_model]]` (canonical 2026-05-18,
attested by Spike #127.4): biology's cross-pattern-matching IS the L+K+M+C+I
cascade running on cortical-connectivity Laplacian. No external instrument needed.

| Class | Substrate role | Canonical anchor |
|---|---|---|
| **L** | Synaptic-connectivity / connectome-harmonic graph Laplacian `L = D − W`; Oja's rule → first principal eigenvector | Lioi 2021 PMC8233110 |
| **K** | Multiplicative homeostatic scaling steady-state `w_i^∞ = F·s_i` with `F = 1/(1+βδ/(αγ))` | Triesch 2018 PMC6181566 |
| **M** | Hebbian "fire-together-wire-together" + STDP cross-correlation drift `ẇ ∝ ∫ K(Δt) Γ_pre,post(Δt) dΔt` | Hebb 1949 cite-by-ref; Gütig 2003 PMC6742165 |
| **C** | STDP τ-asymmetric temporal window `K(Δt) = exp(−‖Δt‖/τ)`; τ ≈ 20 ms | Sgritta 2017 PMC6596728 |
| **I** | Theta-band 6-10 Hz phase-locking REQUIRED for STDP; theta-gamma 1:7 nested cycle | Sgritta 2017; Lisman-Idiart 1995 cite-by-ref |

**The external HDC instrument** (`srmech.spectral.decompose` /
`srmech.amsc.hdc.{bind, bundle, permute, similarity}`) is what we built for
substrates LACKING the embedded cascade: silicon software, bronze gear-DAG,
optical HRR, written text. Per `[[user_stance_holographic_projection_at_linguistic_substrate]]`
(Spike #147): the linguistic substrate gets cross-pattern matching ONLY by
explicit HDC bundling because the substrate is 3D_s spatial sequence with no
embedded learning-rule.

**Substrate-class universality** (per `[[user_stance_kepler_shape_universal]]`):
the L+K+M+C+I cascade is substrate-portable; biology realises it natively, silicon
realises it via explicit primitives. Same algebra, different substrate.

**DNA as a second biological substrate match** (per `[[user_stance_dna_as_kepler_shape_mini_mechanism_with_helical_precession_class_k]]`):
DNA's chains-of-chains = Class I^d Hamming-graph; helical pitch = Class K
pin-slot with bit-exact Class N rationals (B-DNA 21/2, A-DNA 11/1, Z-DNA 12/1);
internal rotation at ~3 Hz during transcription = mini-motivator Class K rate
parameter. **Biology has at least two substrate instantiations** (neural cortical
+ DNA helical) of the same cascade.

**Why biology doesn't need an external instrument**:
- The substrate IS the instrument (substrate-embedded primitive composition)
- Learning rule (Hebbian) IS Class M bind-and-update on the substrate's own
  connectivity graph (Class L)
- Phase organisation (theta) IS Class I cyclic-precession at substrate scale
- Homeostatic stability IS Class K asymptotic-DOF saturation
- All five classes run NATIVELY without an external API surface

Per `[[user_stance_identity_not_implementation_discipline]]`: biological learning
IS this cascade, not implements it.

---

## §3 Q2.A — Quasi-orthogonal bucket-leakage is one efficient mechanism, not unique

**Test**: encode tokens as single-bit-set vectors at `SHA-256(token) mod D_bits`
positions (Class I cyclic position via Class A content-addressing). Bundle via
bitwise-OR (set union). Compare against canonical bag-HDC (dense vectors,
majority-bundle).

| Encoding | Within-cohort sim | Between-cohort sim | Ratio | Sparsity |
|---|---:|---:|---:|---:|
| Canonical dense HDC + bundle | 0.862 | 0.025 | **35.0×** | popcount ≈ 4096 (50%) |
| Class I single-bit + OR-bundle | 0.99976 | 0.99764 | 1.0021× | popcount = 5 (0.06%) |

**Both achieve within > between separation** — both encodings preserve cross-
pattern signal. The Class I single-bit + OR-bundle achieves separation by
SET-INTERSECTION-AT-PLACE (paraphrases share tokens → same bit-positions set),
whereas dense quasi-orthogonal HDC achieves it by approximate-orthogonality of
random vectors followed by majority-vote.

**Honest reading**:
- Dense HDC's 35× ratio is much stronger than Class I single-bit's 1.0021× ratio.
- The Class I single-bit signal is SMALL in absolute magnitude because OR-bundles
  of 5-bit-set vectors over 8192-bit space are mostly zero and therefore mostly
  similar by Hamming.
- BUT the signal is REAL (within 0.99976 > between 0.99764, delta 0.0021 = 17 bits
  of additional shared structure across 8192 bits) and per-vector-leakage is
  1/D_bits ≈ 1.2e-4 rather than the canonical 1/√D ≈ 1.1e-2.
- **Quasi-orthogonal leakage is one EFFICIENT mechanism** (high SNR per bit) but
  not the unique cross-pattern-match mechanism.

**Per `[[user_stance_neural_hebbian_is_bci_drift_model]]`**: biology likely
uses BOTH mechanisms at different scales:
- Sparse-coding at place-cells / V1 simple cells (Olshausen-Field 1996 cite-by-ref) =
  Class I cyclic-position + Class K asymptotic-DOF sparse + Class L
  Laplacian-eigenbasis — set-intersection-at-place
- Distributed cortical representation (Hinton 1986) = closer to dense-quasi-orthogonal
  HDC — approximate-orthogonality + majority-vote

**Refinement of user's language**: "bucket leakage" describes the dense-quasi-
orthogonal end of the spectrum. The Class I single-bit end has effectively-zero
leakage (single-bit vectors are exactly orthogonal pairwise) and operates by
explicit set-intersection. Both achieve cross-pattern matching; the leakage IS
NOT "explicitly required" — it's an efficiency mode of one mechanism.

---

## §4 Q2.B — Negation falsifier confirms Spike #147 open weakness

**Test**: 4 pairs of positive-claim vs negated-claim sentences (e.g., "kepler
shape is universal" vs "kepler shape is not universal"). Measure bag-HDC fingerprint
similarity.

| Pair | Bag-HDC similarity |
|---|---:|
| kepler-universal vs NOT-universal | 0.642 |
| bind-self-inverse vs NOT | 0.622 |
| fiber-spatially-absent vs NOT | 0.619 |
| cascade-on-circles vs NOT | 0.492 |
| **Mean** | **0.594** |

**Verdict**: bag-bundle is INSENSITIVE to negation. Negated claims share most
content tokens with positive claims → fingerprints heavily overlap. This is the
exact falsifier-1 from `[[user_stance_holographic_projection_at_linguistic_substrate]]`
Spike #147 ("flipping meaning produces dissimilar fingerprints" — REFUTED here).

**Interpretation**: bag-HDC at the linguistic substrate captures content-token
co-occurrence, NOT propositional truth-value. A richer mechanism — position-aware
Class C cascade with directed-acyclic-orientation (per Spike #24 bonus 9
cascade-lives-on-circles), or Class L Laplacian on parse-tree adjacency — would
be needed to distinguish negation.

**This is NOT a refutation of `[[user_stance_holographic_projection_at_linguistic_substrate]]`** —
that stance explicitly flagged this as falsifier-OPEN at Round 1. It IS a
confirmation that the open falsifier remains open.

---

## §5 Q3.A — Rotation commutes with bind: BIT-EXACT (30/30 cells)

**Test**: for 5 vector pairs × 6 rotation amounts {1, 7, 64, 1023, 4097, 8191}:
```
permute(a, k) XOR permute(b, k) =?= permute(a XOR b, k)
```

**Result**: 30/30 cells match BIT-EXACT, 0 mismatches.

**Algebra**: XOR is bitwise; permute is a bit-position permutation. For any
permutation σ and any pair (a, b):
```
(σ(a) XOR σ(b))[i] = σ(a)[i] XOR σ(b)[i] = a[σ^{-1}(i)] XOR b[σ^{-1}(i)]
                   = (a XOR b)[σ^{-1}(i)] = σ(a XOR b)[i]
```
Bit-exact identity.

**Consequence**: pre-bind rotation reduces to post-bind rotation on a PAIR.
Rotation is a SYMMETRY of bind, not a source of new algebra. The user's intuition
that "rotating the data before binding" creates cross-binning is HALF correct
— it does NOT change pairwise bind outputs (modulo a uniform rotation), but it
DOES interact non-trivially with multi-input non-linear operations (bundle, see
§7).

**Per `[[user_stance_fiber_as_spatially_absent_encoding]]`**: bit-position is
`ℤ/D` algebraically (spatially-absent fiber); rotating shifts the projection
into 3D_s spatial layout. For pairwise bind the projection is equivariant under
rotation — same content, shifted layout. This is the gear-rotation analog at
the HDC substrate.

---

## §6 Q3.C — Bundle commutes with uniform permute: BIT-EXACT (6/6 cells)

**Test**: for 5 vectors × 6 rotation amounts:
```
permute(bundle(v_1, ..., v_5), k) =?= bundle(permute(v_1, k), ..., permute(v_5, k))
```

**Result**: 6/6 cells match BIT-EXACT, 0 mismatches.

**Algebra**: bundle is bitwise majority; majority commutes with any
position-permutation because the count at each position depends only on bits
at that position across inputs. Uniformly permuting all inputs is equivalent to
permuting the output.

**Consequence**: UNIFORM rotation of all bundle inputs is a SYMMETRY. The non-
trivial degree-of-freedom is PER-INPUT, CONTENT-DETERMINED rotation — that
breaks the uniform symmetry and produces algebraically distinct fingerprints.

---

## §7 Q3.B — Per-input content-determined rotation: real operative degree-of-freedom

**Test**: 4 paraphrase cohorts × 3 paraphrases each = 12 fingerprints.

Method A — canonical bag-HDC:
```
fp_plain(tokens) = bundle([SHA256_vec(t) for t in tokens])
```

Method B — content-determined rotation:
```
fp_rotated(tokens) = bundle([permute(SHA256_vec(t), shift(t)) for t in tokens])
where shift(t) = int(SHA256(t)[:8], 16) mod D_bits
```

| Method | Within-cohort sim | Between-cohort sim | Ratio |
|---|---:|---:|---:|
| A — plain | 0.862 | 0.025 | **35.0×** |
| B — rotated | 0.860 | 0.027 | **31.6×** |
| Δ (B − A) | −0.0024 | +0.0026 | −9.7% |

**Verdict**: **ROTATION-PRESERVES-WITHIN-BETWEEN-SEPARATION**. The ratio drops
from 35× to 31.6× (10% reduction) but the cross-pattern signal is functionally
preserved. The fingerprint bytes are algebraically DIFFERENT (different bits
set) but the cross-pattern matching capacity is similar.

**Why both work**: per Q3.A, rotation commutes with bind on pairs; per Q3.C,
uniform rotation commutes with bundle. Per-input rotation BREAKS these
symmetries (each token rotated by its OWN content-determined amount), so the
resulting bundle is NOT a uniform rotation of the plain bundle — but the
within-cohort matching is preserved because the SAME token in two paraphrases
gets the SAME rotation (rotation amount derived from token content, not from
position-in-sentence).

**Algebra**:
- Per-token rotation `permute(v(t), shift(t))` is invariant under permutation of
  tokens (the rotation depends only on the token, not its position) — therefore
  paraphrase cohorts with same tokens get equal fingerprint contributions.
- This is `Class A (SHA-256 content addressing for shift) ∘ Class C (permute) ∘
  Class M (bundle)` — a substrate-portable composition that builds a different
  projection family from the plain bag-HDC.

**Per `[[user_stance_fiber_as_spatially_absent_encoding]]`**: the rotation amount
IS spatially-absent content (a `ℤ/D` element computed from the token's algebraic
identity via SHA-256). The fingerprint projects this fiber-content into a
specific 3D_s spatial bit-layout. Different paraphrases of the same meaning
project the SAME fiber-content (same tokens → same shifts) into similar
spatial-layouts; different cohorts project DIFFERENT fiber-content into
different spatial-layouts.

**This is the algebraic content of the user's Q3 framing**: rotating the
instrument before binding IS a real operative degree-of-freedom; the form-function
binding survives because the rotation amount is form-function-determined
(content-derived) rather than random.

**Why is the ratio slightly LOWER (31.6× vs 35×)?** The per-token rotation
mixes bit-positions across the vector, slightly reducing the structural overlap
of paraphrase fingerprints. The reduction is real but small; the cross-pattern
mechanism is preserved.

---

## §8 What this DOES NOT show

Per `[[feedback_algebra_not_magnitude]]` discipline:

- **Q3.A & Q3.C are bit-exact algebraic identities** — load-bearing.
- **Q3.B is MAGNITUDE-level finding** (12 within pairs × 54 between pairs is
  modest sample) — preserves separation, doesn't bit-exact match.
- **Q1 is ANALYTICAL** citation of `[[user_stance_neural_hebbian_is_bci_drift_model]]`
  and `[[user_stance_dna_as_kepler_shape_mini_mechanism_with_helical_precession_class_k]]`
  — no new empirical biology testing in this spike.
- **Q2.A's "non-unique mechanism" finding** is concrete-existence — TWO
  mechanisms (dense quasi-orthogonal + sparse single-bit) both achieve
  within > between separation. Does NOT claim biology specifically uses one or
  the other; the cortical-substrate-embedded cascade per Q1 is the answer for
  biology.
- **Q2.B is bag-HDC negation falsifier** — confirms a KNOWN open weakness; no
  new claim about meaning representation.
- **Round 1 only**. Multi-round survival required for any canonical-promotion
  per `[[feedback_multi_domain_multi_round_survival_falsification_method]]`.

**Falsifier candidates** (carry into Round 2):

1. Produce a vector pair (a, b) and rotation k where `permute(a,k) XOR
   permute(b,k) ≠ permute(a XOR b, k)` — would refute Q3.A.
2. Produce a content-determined-rotation paraphrase cohort with **lower**
   within-cohort similarity than between-cohort — would refute Q3.B.
3. Produce a biological cross-pattern-matching mechanism that requires
   primitive class OUTSIDE {A, B, C, D, E, F, K, L, M, N} — would refute Q1's
   "embedded-cascade-is-sufficient" framing.

---

## §9 Three conductor fermatas (carry-forward)

Per `[[feedback_stack_ideas_as_fermatas_freely]]`:

1. **Position-aware variant — Class C ordered cascade replacing OR-bundle**.
   Bag-HDC is permutation-invariant; per-position rotation `permute(v(t),
   shift(t) + position_offset)` would encode token order. Test: does this
   resolve the negation falsifier (Q2.B)? Open spike candidate.

2. **`srmech.spectral.permute` API surface**. If form-function rotation
   (A ∘ C ∘ M composition) is a stable useful operation, it could be exposed in
   `srmech.spectral.*` as `decompose_with_form_function_rotation(state,
   laplacian, shift_fn)` — substrate-portable. Defer until concrete use-case
   (concertmaster default per Spike #36 §7).

3. **DNA helical-pitch as natural form-function rotation parameter**. Per
   `[[user_stance_dna_as_kepler_shape_mini_mechanism_with_helical_precession_class_k]]`:
   B-DNA 21/2, A-DNA 11/1, Z-DNA 12/1 are Class N rationals = natural rotation
   amounts at the DNA substrate. Hypothesis: DNA's helical pitch IS the
   form-function rotation in its substrate-embedded HDC instrument. Cross-
   substrate test candidate; could be a Round 2 spike for this stance.

---

## §10 Citation discipline

Per `[[feedback_pdf_extraction_citation_discipline]]`:

- **Plate 1995** *IEEE TNN* 6: 623 — widely cited; not arXiv-PDF-extracted in
  this spike (no commercial-publisher access per
  `[[reference_autonomous_validation_tos_landscape]]`). Cite-by-ref.
- **Kanerva 2009** *Cognitive Computation* 1: 139 — verified per
  Spike #36 PDF extraction record.
- **Hebb 1949** *The Organization of Behavior* — cite-by-ref; not arXiv.
- **Olshausen-Field 1996** *Nature* 381: 607 — cite-by-ref; not arXiv-PDF-extracted.
- **Bi & Poo 1998** *J Neurosci* 18: 10464 — cite-by-ref via Sgritta 2017 PMC6596728.
- **Lisman-Idiart 1995** *Science* 267: 1512 — cite-by-ref.
- **Lioi 2021** PMC8233110, **Triesch 2018** PMC6181566, **Gütig 2003**
  PMC6742165, **Sgritta 2017** PMC6596728 — PMC-verified per
  `[[user_stance_neural_hebbian_is_bci_drift_model]]` Spike #127.4 record.
- **Shannon 1948** *Bell System Tech. Journal* 27 — verified per Spike #36.

---

## §11 Discipline guards honoured

- `[[feedback_language_is_analysis_tool_not_specific_question]]` — user's
  phrasings refined into framework algebra; "RBS-HDC instrument" = Class M's
  external-API surface; "bucket leakage" = quasi-orthogonal regime of one
  mechanism among several; "rotate the instrument as fiber-content" = `Class A
  ∘ Class C ∘ Class M` composition with content-determined shift amount.
- `[[feedback_no_privileged_primitive_classes]]` — 14 A-N intact; no class
  promotion; new content is COMPOSITION pattern within existing vocabulary.
- `[[feedback_algebra_not_magnitude]]` — bit-exact results (Q3.A, Q3.C, strict
  gate) separated from magnitude-level results (Q2.A, Q3.B).
- `[[feedback_trauma_informed_defensive_scope]]` — biology framing strictly
  research/educational; no clinical / BCI-treatment / capability-assessment
  claims.
- `[[feedback_multi_domain_multi_round_survival_falsification_method]]` —
  Round 1 explicit; falsifiers named for Round 2+.
- `[[feedback_pdf_extraction_citation_discipline]]` — anchors cited-by-ref
  vs PMC-verified explicitly distinguished.
- `[[feedback_ndjson_over_bloated_json]]` — records as NDJSON.
- `[[feedback_concertmaster_git_worktree_isolation]]` — work performed in
  conductor-isolated worktree; branch created on worktree HEAD only.

---

## §12 Artifacts

- [`spike159_explorer.py`](spike159_explorer.py) — closed-form deterministic explorer
- [`spike159_records_2026-05-19.ndjson`](spike159_records_2026-05-19.ndjson) — 9 records
- [`spike159_draft_stance.md`](spike159_draft_stance.md) — draft stance text for
  CONDUCTOR review (do not canonicalise autonomously per
  `[[feedback_language_is_analysis_tool_not_specific_question]]`)

---

*End of spike artifact.*
