# Spike #24 bonus 9 — time-dimensionality test (the OVERTURN test)

> **POSTSCRIPT 2026-05-16 — "Class O" dissolved into Class L.**
>
> The "Class O" framing throughout this report (the narrowed circle-to-hyperbola map this bonus identified) was the *provisional* label. Per user direction 2026-05-16 and per `[[feedback_no_privileged_primitive_classes]]`, the operation is **dissolved into Class L as a signed-Laplacian-variant sub-operation**. Vocabulary stays at **14 classes A–N**. The narrowing this bonus did — from "produces signed-metric content" to "specifically circle-to-hyperbola map" — is still the load-bearing finding; what changed is the classification (Class L sub-operation, not 15th class).
>
> See `[[project_class_o_signed_metric_composition]]` (resolution at top) and bonus 8 / MFO §VIII.8 (postscripts at top) for the full dissolution record.

**Date:** 2026-05-15. **Status:** methodological synthesis landed; concertmaster-level deliverable. **Verdict: H3 with structural refinement — bonus 8's Class O candidate is partially confirmed but its role refined.** NOT a closure-yes for H1; NOT a full closure-no for H2.
**Branch:** `research/spike-24-bonus-8-broken-d-rederivation-2026-05-15` (this bonus extends bonus 8's branch).
**Spec:** user-proposed bonus 9 directly: *"what if we go back and say 3D_s + 7D_g = 1D = 10D and/or 11D we need to find out if time really gets its own dimension or if it's a product of all dimensions. there might still be 11D where some missing class(es) live."*
**Companion probes:**
- [`spike_24_bonus_time_emergent_vs_separate_probe_2026-05-15.py`](spike_24_bonus_time_emergent_vs_separate_probe_2026-05-15.py) + [.ndjson](spike_24_bonus_time_emergent_vs_separate_probe_2026-05-15.ndjson) (18 records) — primary directed-cascade probe.
- [`spike_24_bonus_time_dispersion_shape_diagnostic_2026-05-15.py`](spike_24_bonus_time_dispersion_shape_diagnostic_2026-05-15.py) + [.ndjson](spike_24_bonus_time_dispersion_shape_diagnostic_2026-05-15.ndjson) (11 records) — circle-vs-hyperbola dispersion-shape follow-up.
- [`spike_24_bonus_time_full_spectrum_diagnostic_2026-05-15.py`](spike_24_bonus_time_full_spectrum_diagnostic_2026-05-15.py) + [.ndjson](spike_24_bonus_time_full_spectrum_diagnostic_2026-05-15.ndjson) (8 records) — full-spectrum (62208-mode) examination.

## The user's verbatim overturn-test spec

> *"what if we go back and say 3D_s + 7D_g = 1D = 10D and/or 11D we need to find out if time really gets its own dimension or if it's a product of all dimensions. there might still be 11D where some missing class(es) live."*

Operationalised: build the cascade as 10D = `3D_s + 7D_g` with NO separate temporal factor; apply Class C (iteration / oriented traversal) to the cascade-state graph; test whether the resulting directed cascade Laplacian's spectrum naturally exhibits the signed-metric structure that bonus 8 attributed to a missing Class O. If yes, time-as-cascade-traversal closes the vocabulary at 14 (H1). If no, Class O stays (H2). If partial, additional structure lives at 11D (H3).

## §1 The three discriminating measurements

### Measurement 1 — Directed cascade Laplacian has complex eigenvalues (Stage 2)

**The cyclic-shift permutation eigenvalues** sit on the complex unit circle (n-th roots of unity). The **directed cyclic Laplacian** `L_dir = (1/r²)(I − S)` inherits these as `λ_k = (1/r²)(1 − e^{2πi k/n})` — eigenvalues that sweep a circle of radius `1/r²` centered at `(1/r², 0)` in the complex plane. Verified numerically to 1.5e-15 (Stage 0).

Directed-cascade complex-eigenvalue fractions:

| Cascade | Total modes | Complex modes | Fraction | Conjugate pairing |
|---|---:|---:|---:|---:|
| Single C_8 directed | 8 | 6 | 75.0% | (algebraic) |
| Single C_32 directed | 32 | 30 | 93.8% | (algebraic) |
| Product 2× C_32 directed | 400 (truncated) | 385 | 96.3% | — |
| Product 3× C_32 (3D_s) | 400 (truncated) | 381 | 95.3% | 97.1% |
| **Full 10D directed cascade (n=62208)** | **62208** | **58128** | **93.4%** | (large-N) |

The structural finding: **the directed cascade composition produces complex eigenvalues on 90%+ of modes; conjugate pairing holds at 97%**. This is the algebraic signature of orientation-induced asymmetry. Class C iteration on the 10D cascade-state graph DOES produce a structurally non-Hermitian, asymmetric, signed-metric operator — without any new primitive class beyond A–N. **Bonus 8's strict "no class in A–N supplies signed-metric content" reading is too strong**: Class C orientation on Class L operators on Class I cyclic groups (compositions already in the vocabulary) produces a directed Laplacian with complex eigenvalues, which IS a form of signed-metric structure.

### Measurement 2 — Dispersion shape is CIRCULAR, not HYPERBOLIC (Stage 3 + diagnostics)

The single-factor cyclic-shift directed Laplacian's eigenvalues satisfy the **circle identity**:

```
Im²(λ_k) = 2·Re(λ_k) − Re²(λ_k)
```

verified to ~1e-16 across n ∈ {8, 16, 32, 64}. This is the equation of a circle of radius 1 centered at (1, 0) in the complex plane — NOT the Klein-Gordon hyperbola `ω² = c²k² + m²`.

Linear-fit `Im² = α·Re + β` results on the directed cascade composition:

| Cascade | KG slope α (KG predicts c² = 1) | R² of linear KG fit | Klein-Gordon match? |
|---|---:|---:|---|
| Single C_n directed | −0.2 to −0.02 | 0.001–0.16 | NO |
| 3D_s = 3× C_32 directed (low-Re subset) | 1.98 | 0.18 | NO (slope ≠ 1, R² low) |
| Full 10D directed cascade (n=62208) | 1.09 | 0.029 | NO |
| 7D_g directed alone (n=972) | 1.11 | 0.032 | NO |

**Mass-quantisation test**: if the dispersion encoded Klein-Gordon, `m² = Im² − Re` would take discrete values (mass eigenmodes), producing tall histogram peaks. Result: top 10 bins account for 73% of modes across 11 significant bins — **broadly distributed, no clean quantisation**.

**Rational approximation (Class N) attempt to bridge circle → KG hyperbola**: fitted `Im² = a·Re / (1 + c·Re)` got R² = 0.013. Class N alone cannot supply the circle-to-hyperbola map.

### Measurement 3 — Wick-natural-emergence test (Stage 3, two-part)

Test (a): does the structural shift from undirected (Class L alone, PSD by construction) to directed (Class C + Class L, non-Hermitian) supply the asymmetry?

| Property | Undirected 3D_s (control) | Directed 3D_s (H1) |
|---|---:|---:|
| PSD | TRUE (0 negative / 64) | TRUE (0 negative real / 64) |
| Off-real eigenvalues | 0 | 57 (89.1%) |
| Median Im/Re ratio | 0 | 5.03 |

The structural shift IS dramatic. But the resulting non-Hermitian operator has eigenvalues bounded in the **right half-disc** (Re ≥ 0, Im constrained), not the half-plane of a Lorentzian operator. The (Re, Im) projection structurally CANNOT be interpreted as (k², ω) for a Lorentzian operator because:

- Lorentzian dispersion requires arbitrarily large Im (ω) for arbitrarily small Re (k² with fixed mass). A circle bounded at Re ∈ [0, 2/r²] cannot supply this.
- The angle constraint (verified in the full 10D Class K diagnostic): `arg(λ) ∈ [−π/4, π/4]` for the cascade-summed eigenvalues — the spectrum lives in a 90° wedge, not the unbounded Lorentzian half-plane.

## §2 The structural verdict — H3 with refinement

**H1 (time-is-emergent, vocabulary closed at 14)** — REJECTED. The directed cascade produces complex eigenvalues (the algebraic shadow of orientation), but the dispersion shape is **circular**, not hyperbolic. KG R² ≈ 0.03 across all scales; mass-quantisation absent; Pade approximation insufficient. Class C orientation supplies SOME signed-metric content (asymmetric, non-Hermitian, complex-paired eigenvalues), but NOT enough to encode Lorentzian Klein-Gordon dispersion.

**H2 (time-is-its-own, Class O genuinely needed as stated in bonus 8)** — PARTIALLY UPHELD. Bonus 8 said no primitive class A–N supplies signed-metric content. Bonus 9 refines: Class C orientation DOES supply complex-valued non-Hermitian operators — which IS a form of signed-metric content. But the SPECIFIC HYPERBOLIC LORENTZIAN SHAPE that physics requires is NOT produced by Class C alone. So bonus 8's Class O placeholder is **structurally appropriate as the circle-to-hyperbola map** — Wick rotation `t → it` is exactly the operation that converts `cos(θ)` to `cosh(θ)` and a circle to a hyperbola. The naming "signed-metric composition / Wick rotation primitive" remains correct; what's refined is the *content* of the gap.

**H3 (additional structure at 11D)** — CONFIRMED in REFINED FORM. The 11D = `3D_s + 7D_g + ?D_?` decomposition's 11th dimensional kind is not simply "time" in the Kaluza-Klein sense. The directed-cascade structure already produces a non-trivial orientation / complex / asymmetric component (via Class C in the 14-class vocabulary). What remains structurally missing is the **specific Wick-rotation operation that maps the cascade's natural circular dispersion to the Lorentzian hyperbola observed in physics**.

## §3 The refined picture (per user vocabulary)

Per `[[user_stance_time_as_dimensional_shadow]]`: "Time is part of the shadow (not the projector)." The bonus 9 verdict shows this is **partially true** — Class C orientation IS the cascade-traversal mechanism that produces emergent asymmetric structure; time-as-crank IS this orientation. But the user's lean toward H1 ("time emerges entirely from cascade-state traversal") doesn't survive the dispersion-shape test: the cascade's natural traversal-dispersion is circular, not hyperbolic. Something additional — the Wick-rotation operation, or its discrete equivalent — is needed to convert circular shadow to Lorentzian shadow.

Per `[[user_stance_fractal_shadow]]`: integer-cyclic upstream / continuous downstream. The directed cyclic-shift eigenvalues ARE the upstream integer-cyclic primitive content; the circular dispersion downstream IS their projection-shadow. What's separately needed is the operation that further projects circular-shadow → hyperbolic-shadow, which is the Wick-rotation step.

Per `[[user_stance_pi_as_projection]]`: pi enters via the discrete-to-continuous projection. The cyclic-shift eigenvalue circle IS the integer-tooth-count projection on the unit circle — that's where pi appears. The Wick rotation is then a SEPARATE projection from the unit circle to the Lorentzian hyperbola via `cos → cosh`.

## §4 What this means for bonus 8's verdict

**Bonus 8 verdict status: PARTIALLY OVERTURNED, PARTIALLY CONFIRMED.**

- **Partially overturned**: bonus 8's strict claim that NO composition of A–N supplies any signed-metric content was too strong. Class C orientation on Class I cyclic groups produces a non-Hermitian operator with complex eigenvalues — which IS signed-metric content (asymmetric, off-real, paired). The bonus 8 probe missed this because it used UNDIRECTED Laplacians throughout (symmetric tridiagonal cyclic with periodic wrap), which are necessarily PSD. The choice of undirected operator was an implicit framing choice, not a forced one.
- **Partially confirmed**: bonus 8's named gap (signed-metric composition / Wick rotation primitive) remains REAL but its role is refined. It is NOT the entire signed-metric production (Class C already supplies the asymmetric orientation); it IS the specific circle-to-hyperbola map that converts the cascade's natural CIRCULAR dispersion to the LORENTZIAN HYPERBOLIC dispersion physics observes.

The refined Class O candidate:

> **Class O — Wick-rotation primitive (refined).** Operation that maps a circular dispersion (`Im² = 2·Re − Re²`, natural product of Class C-oriented cyclic cascades) to a hyperbolic dispersion (`Im² = Re + m²`, Klein-Gordon Lorentzian). Algebraically: `cos(θ) → cosh(θ)` projection, equivalent to multiplication of the dispersion variable by `i`. **Not** the entire production of signed-metric content (that's Class C); the specific signature-conversion projection that produces Lorentzian rather than Euclidean dispersion.

This is the same algebraic operation bonus 8 named, but with the structural understanding that the directed cascade ALREADY produces asymmetric / complex / oriented content via Class C; Class O is the FURTHER projection that converts circular to hyperbolic dispersion.

## §5 What this means for `[[project_space_gauge_time_framework]]`

The 11D = `3D_s + 7D_g + 1D_t` decomposition needs **refinement, not rejection**:

- The 10D `3D_s + 7D_g` substrate is well-defined and the directed cascade on it is structurally rich.
- The "11th dimension" carries **traversal-parameter content** (the τ of Class C iteration), which is part of the cascade-state graph's directed structure, not a separate cascade factor.
- **AND** carries **signature-conversion content** (the Wick-rotation Class O candidate), which is a primitive operation, not a cascade factor.

**Proposed reframing**: 11D = `3D_s + 7D_g` (10D cascade-state substrate) + `τ` (traversal parameter, Class C content) + `Class O` (signature-conversion primitive). The "+1D" of bonus 5's original framing is *not* simply "+1D_t"; it splits into a traversal parameter (already in the 14-class vocabulary as Class C) and a signature-conversion operation (Class O candidate).

This is HONEST to both bonus 8 (Class O is real) and bonus 9 (the cascade-traversal mechanism is also real and separate from Class O). The user's intuition that "time really gets its own dimension" was partially right (Class O is a separable primitive operation that introduces the Lorentzian signature) and partially wrong (the temporal cascade factor `C_64` is not load-bearing; Class C orientation on the 10D cascade-state graph already supplies the traversal).

## §6 What this means for MFO §VIII.8 (the bonus 8 landing)

The MFO §VIII.8 entry (the bonus 8 closure-test finding) needs an **annotation** rather than a rewrite:

- The closure-test verdict (FAILURE; Class O located) stands as the strict result for cascade-composition with UNDIRECTED Laplacians.
- A new MFO §VIII.9 should land the bonus 9 refinement: the directed-cascade test shows complex-eigenvalue structure is naturally present via Class C orientation, but the specific Lorentzian dispersion shape requires Class O (or equivalent circle-to-hyperbola map).
- The reframed central computation §XIII.1 now becomes: *"Find the directed cascade composition of cyclic groups in the 10D = 3D_s + 7D_g substrate whose Klein-Gordon-projected spectrum (via Class O Wick rotation) matches SM mass² ratios."* The Class O is necessary; the directed cascade is the substrate it acts on.

## §7 Discipline guards honoured

- **Spectral-graph falsifier** (per `[[feedback_antiquity_not_greek]]`): all three measurements (complex-eigenvalue count, dispersion shape via linear / quadratic / Pade fit, mass-quantisation histogram) are Class L spectral-graph operations on directed cascade Laplacians.
- **Per `[[user_stance_fractal_shadow]]`**: the circular-dispersion-as-projection-shadow framing is preserved. Cyclic groups upstream; their projection produces unit-circle eigenvalues; the cascade product produces a Minkowski-sum-of-circles dispersion shape.
- **Per `[[feedback_trauma_informed_defensive_scope]]`**: structural / methodological only.
- **Per `[[user_stance_string_theory_instrument_first]]`**: 10D / 11D appear via MFO §III.5 Witten 1981 7D minimum-isometry and the user's compression-expression duality, not via imported string-theoretic constructions.
- **Per `[[feedback_no_lineage_claims_in_notebook]]`**: technical citations only (Klein-Gordon dispersion per MFO Part II.1, Witten 1981 7D minimum-isometry, directed-graph Laplacian theory). No lineage claims about external researchers.
- **Per `[[feedback_ndjson_over_bloated_json]]`**: 18 + 11 + 8 = 37 NDJSON records across three probes, one per line.
- **Per `[[feedback_pdf_extraction_citation_discipline]]`**: primary references only. MFO Part II.1 KG equations inherited from bonus 5. Bonus 8 reference inherited from this branch's prior synthesis.
- **stdlib + numpy + scipy only.** CPU substrate per user direction.
- **NO new primitive class invented unilaterally.** Class O candidate is refined per bonus 9; whether to update its description in `[[project_class_o_signed_metric_composition]]` is a conductor decision.
- **Antiquity-not-Greek language.** "Primitive classes" not "primitives" for canonical A–N references.

## §8 Three fermatas for the conductor

1. **Update Class O memory?** The `[[project_class_o_signed_metric_composition]]` memory's description currently reads as if Class O is the *entire* missing signed-metric content. Bonus 9 refines: Class C supplies the asymmetric/oriented content; Class O is the specific *circle-to-hyperbola* projection. Should the memory be updated, or kept as bonus 8's original framing with the bonus 9 refinement landed only in this synthesis?

2. **Soften `[[project_space_gauge_time_framework]]`?** The 11D = `3D_s + 7D_g + 1D_t` framing is partially correct but understates the role of Class C orientation. Proposed refinement: 10D cascade substrate + Class C traversal + Class O signature-conversion. Not a full rewrite; a structural annotation.

3. **Counterpoint dispatch?** The directed-cascade probe found H3 because the dispersion shape is circular, not hyperbolic. A counterpoint subagent could test alternative compositions (e.g., Class K modulus-angle projection of the directed eigenvalues followed by Class N rational approximation of the angle distribution) that might supply the circle-to-hyperbola map without invoking Class O. The fermata is whether to dispatch this verification or take the H3 verdict as standing.

## §9 The one surprise

The single-factor cyclic-shift directed Laplacian's eigenvalues satisfy the **circle identity Im² = 2·Re − Re²** to machine precision across all tested n. This is structurally beautiful: the algebraic shadow of Class C orientation on a Class I cyclic group is the **unit circle in the complex plane**, and the directed Laplacian sweeps that circle into a translated circle centered at (1/r², 0). The cascade composition (Class E direct-product sum) deforms this individual-factor circle into a Minkowski sum of circles — which is broadly circular but with mass distributed over a 2D wedge in the (Re, Im) plane, NOT a hyperbola.

The H1 hypothesis would have required this dispersion to be hyperbolic. Bonus 9's data shows it is not: KG R² ≈ 0.03 across all scales; no mass-quantisation; Pade approximation insufficient. The pattern held: Klein-Gordon dispersion is NOT a natural consequence of cascade composition + Class C orientation alone. Class O (or an equivalent circle-to-hyperbola map) is needed.

The deeper surprise is that bonus 8's finding was both right and wrong: right that A–N cannot directly produce Lorentzian dispersion; wrong that A–N cannot produce ANY signed-metric content (Class C orientation supplies asymmetric complex-paired eigenvalues, which IS signed-metric content of a kind, just not the specific Lorentzian kind). The 14-class vocabulary is RICHER than bonus 8's undirected-only audit suggested, and the gap is more *specific* (a circle-to-hyperbola map) than *signed-metric in general*.

## §10 Closing one-sentence verdict

The Spike #24 14-class vocabulary A–N is **empirically partial-rich** for cascade-composition signed-metric structure (Class C orientation on Class L on Class I produces non-Hermitian, complex-paired, asymmetric operators — a circular dispersion), AND **empirically incomplete** for cascade-composition Lorentzian-KG-dispersion (the circle-to-hyperbola map is genuinely outside A–N), refining bonus 8's verdict by **locating the gap more precisely** (Class O is the specific Wick-rotation / cos→cosh / circle-to-hyperbola map, not the entire production of signed-metric content), with H3 winning over both H1 (time-is-fully-emergent vocabulary closed) and H2 (time-is-its-own dimension with Class O as the entire gap).

The math doesn't lie. Class C orientation on the 10D cascade-state graph produces real, asymmetric, complex-paired eigenvalues. The dispersion shape this produces is circular. Klein-Gordon dispersion is hyperbolic. A circle-to-hyperbola primitive is required, and it is structurally the Class O candidate from bonus 8 with refined content.
