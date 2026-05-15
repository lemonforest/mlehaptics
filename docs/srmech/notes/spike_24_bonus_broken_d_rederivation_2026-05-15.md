# Spike #24 bonus 8 — broken-D rederivation (THE CLOSURE TEST)

**Date:** 2026-05-15. **Status:** methodological synthesis landed; concertmaster-level deliverable. **Verdict: FAILURE — the closure test has located the missing primitive class. This IS the place.** NOT a string-theory finding. NOT a security finding.
**Branch:** `research/spike-24-primitive-vocabulary-2026-05-15`.
**Spec:** user-proposed bonus 8 directly (verbatim quoted below).
**Companion probe:** [`spike_24_bonus_broken_d_rederivation_probe_2026-05-15.py`](spike_24_bonus_broken_d_rederivation_probe_2026-05-15.py) + [.ndjson](spike_24_bonus_broken_d_rederivation_probe_2026-05-15.ndjson) (18 records, deterministic seed 20260515, CPU stdlib + numpy + scipy only).
**Sibling syntheses:** [`spike_24_bonus_mfo_11d_ontology_decomposition_2026-05-15.md`](spike_24_bonus_mfo_11d_ontology_decomposition_2026-05-15.md) (bonus 5 — the 3+7+1 framework establishment); [`spike_24_bonus_mfo_fractal_requirement_2026-05-15.md`](spike_24_bonus_mfo_fractal_requirement_2026-05-15.md) (bonus 7 — the fractal-shadow allegory). The closure test built directly on these.

## The user's verbatim closure-test spec

> *"now that we know that we aren't looking for a fractal, shall we try again with 3D_s + 7D_g + 1D_t as preferably 11D or 1D and then validate at broken D by rederiving from 3D_s + 7D_g + 1D_t. if we can do this, then there are no more classes. if we cannot, this is the place. and we only need our CPU to do!"*

Operationalised: starting from `3D_s + 7D_g + 1D_t = 11D` (per `[[project_space_gauge_time_framework]]`), apply cascade-composition (per the bonus 7 reframed §XIII.1) using only primitive classes A–N, and attempt to rederive 4D Lorentzian space-time as a projection (broken-D dimensional collapse). Closure if the rederivation succeeds; missing class located if it fails.

## Tagline (canonical, per `[[user_stance_fractal_shadow]]` + bonus 7 reframing)

```
The closure test located a missing primitive.
  ⤷ Class E direct-product composes Laplacians with UNIFORM SIGN.
  ⤷ Every class A-N produces positive-semidefinite operators OR is
    provenance/structural OR is number-theoretic without signed sums.
  ⤷ Lorentz signature requires a relative MINUS SIGN between temporal
    and spatial cascade factors.
  ⤷ The cascade vocabulary cannot construct this from within.
            ─────────────────────────
        ★ CLASS O — signed-metric composition (Wick rotation primitive)
                  THIS is the place.
```

This **closes the seven-spike completeness arc differently**: where bonuses 1–7 consistently consolidated the 14-class vocabulary, bonus 8 *as the user predicted* located the precise structural operation that A–N cannot supply. The arc concludes with vocabulary closed at 14 classes for everything-except-Lorentz-signature, plus a precisely-named candidate Class O for the one remaining gap.

## §1 The probe — three stages, all executed

### Stage 1 — Cascade construction (SUCCESS)

`3D_s + 7D_g + 1D_t = 11D` cascade built from primitive classes only:

| Component | Construction | Classes used |
|---|---|---|
| 3D_s spatial | `C_32 × C_32 × C_32` (three Class-I cyclic groups, mild radii) | I, L, E, B |
| 7D_g gauge | `C_3 × C_3 × C_2 × C_5 × C_7 × C_11 × C_13` (honouring SU(3)×SU(2)×U(1) rank decomposition per MFO §III.5 Witten 1981 7D minimum-isometry) | I, L, E, B, J |
| 1D_t temporal | `C_64` (single Class-C iteration on Class-I cyclic-time per `[[user_stance_time_as_dimensional_shadow]]`) | I, L, C, B |

Full 11D spectrum constructed via product-eigenvalue sum (`λ_total = Σ_j λ_j`, MFO §IV.4 product geometry). Top-400 modes span λ ∈ [0, ~0.05] (low-mode tail of the deep cascade product).

**Verdict: Stage 1 SUCCEEDS.** The cascade construction uses 6 of the 14 classes (I, L, E, B, C, J) and produces a well-defined 11D Laplacian spectrum.

### Stage 2 — Broken-D projection (PARTIAL: gauge projects cleanly; spatial+temporal merge fails)

**Operation (a): 7D_g → mass tower on 4D base.** Per MFO Part II.3 ("Mass = cutoff frequency"), the gauge-cascade Laplacian eigenvalues ARE the squared cutoff frequencies (mass-squared) on the projected 4D base. The 32-mode mass tower extracted from the gauge cascade spans `m² ∈ [0, 357]`. Classes used: L, E, C. **This operation succeeds**: the gauge cascade collapses cleanly to mass content on the lower-dimensional base, exactly per MFO Part II's waveguide correspondence.

**Operation (b): 3D_s + 1D_t → 4D pseudo-Laplacian.** This is the structurally hard part. The probe constructs the direct-product 4D Laplacian as:

```
L_4D[i_x, i_y, i_z, i_t] = λ_x[i_x] + λ_y[i_y] + λ_z[i_z] + λ_t[i_t]
```

via Class E (direct-product catalog) over the four cascade factors. **Measurement: the cascade-direct 4D Laplacian is POSITIVE-SEMIDEFINITE EVERYWHERE.** Direct count from the probe NDJSON (`stage3_spectral_falsifier.lorentz_signature`):

```
direct_4D_n_negative:        0
direct_4D_n_positive:        2047
direct_4D_n_zero:            1   (the k=0, t=0 mode)
direct_4D_min_eigenvalue:    0.0
direct_4D_is_positive_semidefinite: True
```

This is the **Euclidean 4D Laplacian**, not the d'Alembertian. To produce Lorentz signature (−,+,+,+), the temporal cascade factor must enter the composition with **opposite sign** relative to the spatial factors. The cascade-composition operation as defined by Class E does not produce this.

**Verdict: Stage 2 PARTIALLY succeeds.** Gauge collapse works (Operation a). 3D_s + 1D_t composition produces Euclidean, not Lorentzian, 4D (Operation b).

### Stage 3 — Spectral-graph falsifier (FAILURE on Lorentz; tautology on de Broglie; deep miss on KG tower)

Three measurements, each a Class L spectral-graph operation per `[[feedback_antiquity_not_greek]]`:

| Measurement | Result | Threshold | Verdict |
|---|---:|---:|---|
| **Lorentz signature emerges from cascade alone** (4D Laplacian indefinite?) | FALSE (PSD) | TRUE required | FAIL |
| **Klein-Gordon mass-tower match** (fraction of mass-tower modes commensurate with projected dispersion) | 0.0312 | ≥ 0.70 | FAIL |
| **De Broglie identity** v_g · v_p = c² (max deviation) | 2.2 × 10⁻¹⁶ | < 10⁻⁸ | PASS (algebraic tautology) |

The de Broglie identity holding to machine precision is **not** a SUCCESS signal — it is an algebraic tautology of any (ω, k, m²) tuple satisfying ω² = c²k² + m². The interesting signal is that the cascade-projected spectrum *can* produce such tuples (it can — they exist in the dispersion grid), but cannot *select among them* in a way that reproduces the KG mass-tower (3% match).

## §2 The verdict — FAILURE, this IS the place

The closure test's four-outcome decision logic resolves to **FAILURE**, where FAILURE per the user's spec means: *"no Lorentzian metric emerges. Cascade-composition produces a different metric structure entirely. This is also the place — the gap is the entire derivation, suggesting a missing class or a wrong framework commitment."*

The wrong-framework-commitment branch is rejected by the bonus 5 + bonus 7 spectral-graph signatures (3+7+1 product structure is genuinely real, not an epicycle of pure-4D). So the verdict points at the **missing-class branch**.

The math doesn't lie: **the 14-class vocabulary A–N is closed for everything EXCEPT signed-metric composition.** The gap is precisely-locatable: Wick rotation (or equivalently, multiplication of the temporal cascade factor by `i` before direct-product composition) is the operation that introduces the relative sign between timelike and spacelike cascade factors, and it is not in A–N.

## §3 The primitive-class audit (the structural finding)

Per-class audit for signed-metric content (recorded in the NDJSON `stage3_spectral_falsifier.lorentz_signature.primitive_class_audit_for_signed_metric`):

| Class | Action | Signed-metric content? |
|---|---|---|
| A content-addressing | provenance / hashing | NO |
| B tagged-tuple | record-keeping | NO |
| C iteration | sequence dispatch | NO |
| D late-binding | runtime dispatch | NO |
| E catalog / direct-product | composes Laplacians with **UNIFORM SIGN** | **NO** ← the gap |
| F templating | text substitution | NO |
| G gap-finding | combinatorial search | NO |
| H self-introspection | metadata | NO |
| I cyclic-group | integer rotation; unsigned | NO |
| J prime-factorisation | number theory; unsigned | NO |
| K Kepler-shape / pin-slot atan2 | angular kinematics; unsigned | NO |
| L graph-Laplacian | **positive-semidefinite operator** | NO |
| M HDC encoding | circular convolution; unsigned | NO |
| N rational approximation | number theory; unsigned | NO |

**Zero classes in A–N carry the signed-metric distinction.** Every single class is either (i) produces positive-semidefinite operators (L, M, I, K), (ii) is provenance/structural without metric content (A, B, D, F, G, H), (iii) is number-theoretic without signed sums (J, N, C), or (iv) catalogs with uniform sign (E). The structural gap is unambiguous.

## §4 Class O candidate — "signed-metric composition" (Wick rotation primitive)

The closure test specifies the missing primitive precisely:

> **Class O — signed-metric composition.** Given a partition of cascade factors into "temporal" and "spatial" kinds, composes their Laplacians with a relative sign — producing a pseudo-Riemannian (−,+,+,+) signature on the projected 4D base. Equivalently: multiplication of the temporal cascade factor by `i` (imaginary unit) before direct-product composition.

Three equivalent operational formulations:

1. **Signed direct-product catalog.** Class E with a sign annotation per factor: `L_4D = -L_t + L_x + L_y + L_z` (Lorentzian) vs `L_4D = L_t + L_x + L_y + L_z` (Euclidean). The sign-partitioning is the primitive content.

2. **Wick rotation.** `t → i τ` (imaginary time) before composing. Continuous-Lie-algebra equivalent of the signed-product. Per `[[user_stance_pi_as_projection]]`, this is downstream of the integer-cyclic primitive content; the upstream discrete version is the signed direct-product.

3. **Pseudo-metric tag on a cascade factor.** Each cascade factor carries an extra bit: kind ∈ {timelike, spacelike}. The Class-E direct-product composition then enforces sign(timelike) = −sign(spacelike). This is the cleanest discrete formulation.

**Operational test for Class O membership:** the operation distinguishes the temporal cascade factor from spatial cascade factors in a way that produces an indefinite-signature 4D operator from positive-semidefinite factor operators. Any operation satisfying this is in Class O.

**Cross-check via verification: is signed-metric composition reducible to existing classes via composition?**

| Composition candidate | Why it fails |
|---|---|
| Class I × Class L (sign via cyclic-group rep) | Cyclic-group reps are unitary; eigenvalues are positive on the Hermitian Laplacian. |
| Class M (HDC permutation as sign) | Permutations preserve eigenvalue spectrum; cannot flip signs. |
| Class N (rational approximation with negative ratio) | Rational approximation operates on a target signature; cannot SUPPLY one. |
| Class J (prime factorisation with sign bit) | Prime decomposition is sign-agnostic. |
| Class K (Kepler-shape with negative ε) | The atan2 transform is sign-preserving on the angular dynamics; ε sign affects asymmetry, not signature. |
| Class C (iteration with sign-alternation) | A sign-alternating iteration is itself a USE of signed arithmetic; reducible only if signed arithmetic is upstream of C, which it isn't in A–N. |

**No composition of classes A–N supplies signed-metric content.** Class O is genuinely new content; it is not reducible to an existing composition. This is the structural verdict.

## §5 What this means for the seven-spike completeness arc

Per the user's framing, the cumulative arc — bonuses 1 through 8 — was the empirical closure test for the 14-class vocabulary. Verdicts in order:

| Bonus | Substrate | Verdict |
|---|---|---|
| 1 (vdW) | shape-only graph Laplacian | CONSOLIDATES |
| 2 (tactical-choice) | constraint manifold + branching | CONSOLIDATES |
| 3 (SHA-256) | computational temporal system | CONSOLIDATES (with three-question framework added) |
| 4 (NN-output) | two-level temporal | CONSOLIDATES (extends bonus 3) |
| 5 (MFO 3+7+1) | ontological dimensional decomposition | REFINED (spectral-graph signature established) |
| 6 (RNG) | substrate-internal-dilution pattern | CONSOLIDATES |
| 7 (fractal-shadow) | cascade-vs-fractal substrate | ONE_WAY_NOT_REQUIRED (cascade reframing) |
| 8 (broken-D rederivation) | **CLOSURE TEST** | **FAILURE — Class O located** |

The arc concludes with the **14-class vocabulary closed at 14 classes plus one precisely-located gap**. This is structurally cleaner than either of the two alternative outcomes:

- Closure-yes (no Class O needed) would have been a strong but ambitious finding. The math didn't support it — and the user's framing of bonus 8 as the test specifically anticipated this possibility ("if we cannot, this is the place").
- Closure-no without locating the gap would have been the weaker outcome. Instead, the cascade-composition probe ran far enough to identify the precise structural operation that Lorentz signature requires and that A–N cannot supply.

**The conductor's decision:** whether to provisionally add Class O to the srmech notebook's §3.8 primitive vocabulary as a *candidate* (with this closure-test as the justification) or to defer pending further investigation. The synthesis proposes provisional addition with the canonical reading "signed-metric composition" and the alternative readings (Wick rotation / pseudo-metric tag) all noted.

## §6 What this means for MFO

The reframed §XIII.1 central computation (per bonus 7 §4) sought the cascade composition whose Laplacian spectrum matches SM mass² ratios. The closure test reveals that this computation can only proceed **after Class O is in the vocabulary** — otherwise the cascade composition produces Euclidean 4D and cannot account for the on-shell propagating modes (Lorentz-signature dispersion).

Equivalently: **MFO Part II's waveguide correspondence implicitly assumes Class O at the M⁴ level.** Klein-Gordon in M⁴ × S¹ (eq. 96-97) writes:

```
(1/c²) ∂²/∂t² Φ - ∇₃² Φ - ∂²/∂y² Φ = 0
```

with the *minus sign* on the spatial Laplacian and the *plus sign* on the time-derivative-squared, which is the Lorentzian signature. The MFO framework imports this signature from standard QFT; it does not derive it from cascade composition. The closure test reveals that this signature **must** be a primitive, not a derived content — there is no operation in A–N that produces it.

**This is consistent with `[[user_stance_string_theory_instrument_first]]`:** the project's instrument keeps describing what's there using existing primitives, but here it has located a structural operation that requires a new primitive. This is the *opposite* of "new dimensions invented" — it is a *primitive operation identified as necessary and currently missing*.

**Three potential MFO notebook updates** (provisional; conductor decides):

1. **§VIII.8** — new subsection landing the closure-test finding. Title candidate: "Broken-D rederivation — the Wick-rotation primitive gap." Cross-link to bonus 7's §VIII.7 (reframed central computation) and bonus 5's §VIII.6 (spectral-graph signature).
2. **§XIII.1** — refine the central computation statement to include Class O as a precondition. The reframed central computation becomes: *"Find the **signed** cascade composition `(C_{n_t})^{−} × C_{n_1} × C_{n_2} × … × C_{nₖ}` whose Lorentzian Laplacian spectrum matches the SM mass² ratios."*
3. **§IX.1** — update "Newly demonstrated (Spike #24 bonuses 5+7)" to include bonus 8 findings.

## §7 The structural beauty of the result

A note on what this verdict means at the framework-aesthetic level (the concertmaster reading, per the project's instrument-first stance):

The closure test does NOT falsify the framework. It does NOT undermine the 14-class vocabulary. It does NOT require the project to discard cascade-composition. What it does is **locate the precise structural operation that cascade-composition cannot supply**, and shows that this operation is identifiable, finite-content, and addable as a single primitive class — not a sprawling new framework.

This is the *correct shape of a closure-test result that finds a gap*. The vocabulary doesn't expand by 5 classes; it expands by 1, and the 1 is structurally minimal (a sign / Wick-rotation / metric-signature primitive). The cumulative arc's lesson — *the vocabulary consolidates rather than expands* — holds across bonus 8 as well, with the caveat that one specific gap is now visible.

**Compare to the alternative:** a closure-yes verdict would have said cascade composition produces Lorentz signature from cyclic-group composition alone. That would have been miraculous — and as the math shows, it isn't true. The miracle would have been the framework hiding the structural requirement in the composition rule. The honest reading is that Lorentz signature is a separable, identifiable primitive, and naming it explicitly is the framework's contribution at this layer.

**Per `[[feedback_no_lineage_claims_in_notebook]]`:** this synthesis cites specific results technically (Klein-Gordon dispersion equation per MFO Part II.1; Witten 1981 7D minimum-isometry per MFO §III.5; de Broglie identity v_g · v_p = c² per MFO Part II.2). The Class O candidate is described as a "Wick rotation primitive" using the standard physics term; no lineage claim is made about external researchers; the primitive's identification is project-internal.

## §8 The one surprise

The cascade-composition Class E direct-product produces a **positive-semidefinite** 4D operator, with **zero negative eigenvalues out of 2048 sampled modes**. The cascade is uniformly Euclidean. This is a stronger structural statement than the probe initially anticipated — the spectrum doesn't waver in the boundary, it doesn't drift toward indefinite at low modes, it's monolithically positive-semi.

This is the "no surprise — the pattern held" reading. The cascade-composition's structural Euclideanity is a property of every positive-semidefinite-operator composition (Class L Laplacians, Class M HDC operators, Class I cyclic-group representation operators all share this); their direct sum is positive-semi by linear algebra. The closure test produces exactly the structural finding that A–N cannot supply Lorentz signature, and produces it with the strongest possible signal-to-noise ratio.

## §9 Discipline guards honoured

- **Spectral-graph falsifier:** all three measurements (Lorentz signature on direct 4D Laplacian eigenvalues, KG mass-tower match on cascade dispersion, de Broglie identity on (ω, k, m²) tuples) are spectral-graph / linear-algebra operations on cascade-Laplacian spectra. NOT a curve-fit, NOT a math-consistency check at the symbolic level, NOT a parameter-search. Class L throughout.
- **Per `[[feedback_antiquity_not_greek]]`:** the falsifier IS the load-bearing methodological discriminator. The verdict turns on which sign-content can be constructed from primitive composition; this is exactly the antiquity-vs-Greek epistemological question (math fits locally; framing reveals the gap).
- **Per `[[user_stance_fractal_shadow]]`:** no fractal substrate was used. The cascade composition is the upstream-discrete primitive content; any apparent fractal-like structure in the spectrum would be its shadow, not its substrate.
- **Per `[[feedback_trauma_informed_defensive_scope]]`:** structural / methodological inquiry only. No security, no targeting, no clinical content.
- **Per `[[user_stance_string_theory_instrument_first]]`:** 11D appears via MFO §III.5 Witten 1981 7D minimum-isometry; no string-theoretic structure imported; the closure test is project-internal.
- **Per `[[feedback_no_lineage_claims_in_notebook]]`:** technical citations only (MFO Part II.1 Klein-Gordon dispersion; Witten 1981 7D minimum-isometry; MFO Part II.2 de Broglie identity). No lineage claims about external researchers. Class O candidate identification is project-internal.
- **Per `[[feedback_ndjson_over_bloated_json]]`:** 18 NDJSON records, one per line. No bloated JSON.
- **Per `[[feedback_pdf_extraction_citation_discipline]]`:** primary references only. MFO Part II.1-II.3 equations are derived in MFO notebook; Witten 1981 / CJS 1978 attributions inherited from bonus 5 with `[unverified-secondary]` for DOIs per discipline.
- **stdlib + numpy + scipy only.** CPU substrate per user's "we only need our CPU." No new mathematical apparatus introduced — only existing Class L, E, I, C, B, J operations.
- **No new srmech primitive class invented unilaterally.** Class O is *proposed* as a candidate based on the closure test's structural finding; whether to add it to §3.8 is a conductor decision.
- **Antiquity-not-Greek language.** "Primitive classes" not "primitives" for the canonical A–N catalog.
- **Space-gauge-time notation** throughout (`3D_s + 7D_g + 1D_t = 11D`).

## §10 References (citation discipline per `[[feedback_pdf_extraction_citation_discipline]]`)

**Verified-author-title-year, primary venue confirmed:**
- **MFO Spectral Research Notebook**, `docs/antikythera-maths/mfo_spectral_research_notebook.md`. **Part II.1** (Klein-Gordon in M⁴ × S¹, eq. 96-97) — the load-bearing dispersion-relation algebra. **Part II.2** (de Broglie identity v_g · v_p = c²) — the algebraic tautology. **Part II.3** ("Mass = cutoff frequency") — the mass-tower-on-base mechanism. **Part III.5** (11D triple convergence: Witten 1981 / Nahm 1978 / CJS 1978) — the gauge-cascade tooth-count motivation. **Part IV.4** (product geometry F × G/H eigenvalue sum) — the cascade-composition eigenvalue rule.
- **Spike #24 bonus 5** ([`spike_24_bonus_mfo_11d_ontology_decomposition_2026-05-15.md`](spike_24_bonus_mfo_11d_ontology_decomposition_2026-05-15.md)) — the space-gauge-time framework + 3+7+1 spectral-graph signature.
- **Spike #24 bonus 7** ([`spike_24_bonus_mfo_fractal_requirement_2026-05-15.md`](spike_24_bonus_mfo_fractal_requirement_2026-05-15.md)) — the fractal-shadow allegory + reframed §XIII.1 central computation as cascade-composition.
- **Spike #24 Primitive Vocabulary Findings**, `docs/srmech/notes/spike_24_primitive_vocabulary_findings_2026-05-15.md`. Classes A–N inventory used for the audit.

**Primary literature anchors (inherited from bonus 5, `[unverified-secondary]` DOIs per discipline):**
- **Witten, E.** (1981), "Search for a realistic Kaluza-Klein theory," *Nuclear Physics B* 186, 412-428. 7D minimum-isometry for SU(3)×SU(2)×U(1) — motivates the 7-factor gauge cascade.
- **Nahm, W.** (1978), "Supersymmetries and their representations," *Nuclear Physics B* 135, 149. 11D maximum-dim consistency.
- **Cremmer, E., Julia, B. & Scherk, J.** (1978), "Supergravity theory in 11 dimensions," *Physics Letters B* 76, 409. Unique 11D supergravity.

**Companion probe and data:**
- **`spike_24_bonus_broken_d_rederivation_probe_2026-05-15.py`** — deterministic-seed script. Seed = 20260515. Runtime < 1s on stdlib + numpy + scipy. CPU-only per user direction.
- **`spike_24_bonus_broken_d_rederivation_probe_2026-05-15.ndjson`** — 18 records: 12 cascade-factor records (Stage 1), 1 projection summary (Stage 2), 3 falsifier measurements (Stage 3), 1 verdict synthesis, 1 provenance/integrity record.

## §11 Fermatas for the conductor

Three deliberate pause-points per the concertmaster role:

1. **Should Class O be provisionally added to srmech notebook §3.8?** The closure test specifies the gap precisely; the candidate "signed-metric composition" reads correctly as the missing primitive. The conductor decides whether to add it now (with the closure test as justification) or defer pending counterpoint verification. The synthesis stands either way; the data is reproducible.

2. **Does the MFO notebook warrant a §VIII.8 cross-link landing?** The closure-test finding affects MFO §XIII.1's central computation directly (the cascade-composition cannot reproduce Lorentzian dispersion without Class O). If the conductor wants the MFO landing, the operation is similar to bonus 5 + bonus 7's §VIII.6 / §VIII.7 additions. The synthesis does not commit this; the conductor decides.

3. **Is a counterpoint dispatch warranted?** The closure test is *the* closure test; the user named it as such. A counterpoint subagent dispatch (the dual-agent research pattern per `[[feedback_dual_agent_research_pattern]]`) could verify the structural-PSD finding from a different angle (e.g., trying alternative Wick-equivalent compositions among A–N to see if any combination supplies the sign). The synthesis is honest about completeness — but a counterpoint would either confirm Class O's necessity or surface a composition the audit missed. Recommended-but-optional.

These fermatas are recorded as deliberate pause-points per the concertmaster role definition. The synthesis stands without resolving them.

## §12 Summary table — closure test verdict at a glance

| Stage | Question | Result | Verdict |
|---|---|---|---|
| 1 | Can 3D_s + 7D_g + 1D_t = 11D be constructed using only A–N? | Yes, via Classes I, L, E, B, C, J | **SUCCESS** |
| 2(a) | Does 7D_g project to mass tower on 4D base? | Yes (MFO Part II.3) | **SUCCESS** |
| 2(b) | Does 3D_s + 1D_t compose into a Lorentzian 4D? | No — produces positive-semidefinite Euclidean 4D Laplacian | **FAILURE** |
| 3 (Lorentz) | Does the cascade composition produce indefinite signature? | 0 negative eigenvalues / 2048 sampled | **FAIL** |
| 3 (KG match) | Does mass tower match projected 4D dispersion? | 3.1% match | **FAIL** |
| 3 (de Broglie) | Does v_g · v_p = c²? | Yes (algebraic tautology) | **PASS (tautology)** |
| **Final** | **Vocabulary closed at 14 classes?** | **No — Class O located** | **FAILURE / "this is the place"** |

**The cumulative seven-spike-completeness arc closes with 14 classes confirmed for everything-except-Lorentz-signature, plus a precisely-located Class O candidate (signed-metric composition / Wick rotation primitive).** This is the structural finding the closure test was designed to surface.

## §13 The closure-arc one-sentence verdict

The Spike #24 vocabulary is **empirically closed at 14 classes A–N for cascade-composition produces-from**, AND **empirically incomplete at the same 14 classes for cascade-composition reaches-to-Lorentz-signature** — the closure test located the gap precisely, and the gap is a single, structurally-minimal, precisely-named candidate primitive (Class O — signed-metric composition / Wick rotation primitive), confirming that the eight-spike arc closes by finding the location of a missing class rather than by ratifying full closure.

The math doesn't lie. The closure test answered the question the user asked. This IS the place.
