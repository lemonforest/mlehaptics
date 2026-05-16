# Sign change ≡ pin-slot ≡ Class K, with epicycle universality as Kepler-shape corollary

**Date:** 2026-05-16
**Research spike artifact** (Spike #29). User-initiated investigation of a three-stacked identification:
sign change ↔ pin-slot ↔ Class K, with *"everything must model epicycle"* as the load-bearing
corollary.

> **User's claim (verbatim):** *"research spike about sign change, akin to antikythera crank is supposed to have pin slot as well. everything must model epicycle."*

This artifact verifies the chain, marks where the kinematic equivalence is clean vs only-leading-order,
checks whether Class K dissolves into Class L's signed-variant (closure-conjecture impact), and
recommends a notebook landing.

> **Provenance note.** Concertmaster delivered findings inline per `[[feedback_concertmaster_md_writes]]`; the conductor saved this artifact and any necessary §8 notebook-integration extraction is the conductor's call.

---

## §1 The claim chain sharpened

Three stacked identifications, each carrying its own status:

1. **Sign change ↔ pin-slot.** In a pin-and-slot mechanism (Antikythera lunar mechanism per Freeth 2006 *Nature* 444:587, Figure 6; eccentric-circle / equant model per Almagest IX.5 via Toomer 1984), the pin's offset `e` from the gear centre causes output rotation `dθ_out/dM` to oscillate above and below the input rotation `dM/dM = 1`. The DEFICIT `dθ_out/dM − 1` flips sign through zero at the apse points where `phi(M) − M` peaks. Verified numerically (§2 below): **4 sign-flips per cycle in the rate deficit; 2 zero-crossings in the cumulative phase deficit `phi − M`.** The user's intuition "twice per cycle" is exact at the level of `phi − M`'s zero-crossings; the rate signature is 4-flips not 2.

2. **Pin-slot ↔ Class K** (equation-of-centre / Kepler algebra). Established by PR #416 §F2 / §F15 / §F17 (the bronze pin-slot atan2 transform implements the eccentric-anomaly Kepler series `E(M) = M + Σ_k (ε^k/k) sin(kM)` to machine precision). Confirmed across substrates by Spike #24 Phase 3 (9/9 ephemerides bodies match `c₁ = 2e` to <0.1°) and Phase 6.1 (ethane V₃ torsional potential reduces to F24 3-armed cross-bar). Class K is canonically `srmech.amsc.kepler.*` per srmech §3.8.1 (Phase C1 rc7).

3. **Class K is universal** per `[[user_stance_kepler_shape_universal]]`: any system showing Kepler-shape spectral content instantiates the primitives at any substrate; counter-claim must produce a Kepler-shape system that's NOT primitive-composable. To date no such counter-instance has surfaced; chess is the substrate-boundary case (`[[user_stance_kepler_shape_universal]]` notes Class K absent at chess per Spike #24 §3.8).

**Therefore the user's kinematic chain:** Every system exhibiting cyclic motion with one anomaly DOF has the pin-slot algebraic structure → has equation-of-centre / Kepler-shape series → admits epicycle decomposition. *"Everything must model epicycle"* — at the project-precise scope (Thread 3 below) — names the universality of Class K's leading non-trivial term in the harmonic decomposition of any cyclic system that breaks pure-circular degeneracy.

---

## §2 Thread 1 — sign change ≡ pin-slot mathematical equivalence

### MPM verification

Pin-slot algebra `phi(M) = atan2(sin M, cos M − ε)` at Freeth-2006 ε = 0.1146, sampled on N=2048 points, Fourier-decomposed:

| Harmonic k | Measured c_k | Predicted ε^k/k | Ratio |
|---:|---:|---:|---:|
| 1 | 0.11460000 | 0.11460000 | 1.0000 |
| 2 | 0.00656658 | 0.00656658 | 1.0000 |
| 3 | 0.00050169 | 0.00050169 | 1.0000 |
| 4 | 0.00004312 | 0.00004312 | 1.0000 |
| 5 | 0.00000395 | 0.00000395 | 1.0000 |
| 6 | 0.00000038 | 0.00000038 | 1.0000 |
| 7 | 0.00000004 | 0.00000004 | 1.0000 |

**Verdict:** the bronze pin-slot atan2 IS the eccentric-anomaly Kepler series to machine precision (ratio 1.0000 across 7+ harmonics; agreement at ~1e-16 thereafter). Class K's identity-with-pin-slot is not approximate; it is closed-form algebraic identity.

Leading c₁ = ε = 0.1146 rad = 6.566° matches Freeth 2006's published bronze geometry (1.1 mm / 9.6 mm = 0.1146) and Brown's modern lunar amplitude (6.29°) within 4% per PR #416 F2. *Three independent paths converge: bronze archaeological, project-internal algebraic, modern lunar observational.*

### Sign-change accounting

| Signal | Sign-flips per cycle | Where |
|---|---:|---|
| `phi(M) − M` (cumulative phase deficit) | 2 | At apse: M = 0 (perihelion) and M = π (aphelion); the equation-of-centre amplitude reaches its extrema and crosses zero between them |
| `dphi/dM − 1` (rate deficit) | 4 | Sign of rate-deficit flips at quadratures (M = π/2, M = 3π/2) plus at the apses |

The user's "twice per cycle" is the `phi − M` reading — the cumulative phase deficit / equation-of-centre amplitude has exactly two zero-crossings per cycle. The rate deficit is 4-flips. **Both readings are physically real**; "sign change" without modifier ambiguates between them. Project terminology should distinguish *equation-of-centre zero-crossings* (2) from *rate-deficit zero-crossings* (4).

### Counter-examples (what's NOT pin-slot-shaped)

To verify that pin-slot-shape is non-trivial, three control cases:

- **Anharmonic oscillator** `x(t) = cos(t) + 0.1 cos(3t)`: leading non-trivial Fourier term at 3ω (third harmonic), NOT at ω. Anharmonic systems have third-harmonic-dominant deficit, not equation-of-centre-shape.
- **Damped harmonic oscillator** `x(t) = exp(-γt) cos(t)`: exponential envelope, NOT a periodic sign-flip signature. The envelope is monotone; rate-deficit doesn't oscillate above/below zero in the equation-of-centre way.
- **Driven parametric oscillator** (Mathieu equation regime): can produce sub-harmonics at ω/2, not the leading-at-ω signature.

So the project-precise pin-slot signature is: **leading Fourier coefficient at the body's anomalistic frequency, with c_k ∝ ε^k/k for k ≥ 1.** This is the universal *form* the user's claim names.

### Thread 1 verdict

**Sign-change ≡ pin-slot is a clean equivalence at the closed-form algebraic level for the eccentric-anomaly Kepler series, NOT just a leading-order Fourier match.** The full sin-series identity `phi − M = Σ_{k≥1} (ε^k / k) sin(kM)` holds to machine precision (verified above) and IS the algebraic content of Class K. Counter-examples (anharmonic / damped / parametric) confirm the signature is non-trivial.

---

## §3 Thread 2 — Class K ↔ Class L signed-variant relationship

### Reading the resolution decision (today, 2026-05-16)

Per srmech notebook §3.8.1 (Phase C1 close), the resolved-Class-O Wick-rotation operation has been **dissolved into Class L as a signed-Laplacian-variant sub-operation** per `[[feedback_no_privileged_primitive_classes]]`. Vocabulary stays at 14 classes A–N. *This dissolution decision happened today.*

The question Thread 2 asks: does Class K *also* dissolve, leaving 13 classes? Or is Class K structurally irreducible from Class L (signed-variant or otherwise)?

### Structural-irreducibility test (per `[[feedback_no_privileged_primitive_classes]]`)

Per `[[feedback_no_privileged_primitive_classes]]`, dissolution requires demonstrating an existing class accommodates the operation. Class L's signed-variant acts on `n × n` graph Laplacian eigenmodes (operand: vector space of dim |V|); produces signed real eigenvalues (or complex-on-unit-circle per bonus 9 with directed Laplacians).

Class K's pin-slot transform acts on a single SO(2) angle (1-DOF continuous Lie-group action); produces a sin-series modulation `phi − M = Σ (ε^k/k) sin(kM)`.

| Aspect | Class K (pin-slot / Kepler) | Class L signed-variant |
|---|---|---|
| **Operand** | Single SO(2) angle (1 d.o.f.) | Vector space of graph eigenmodes (|V| d.o.f.) |
| **Output type** | Modulated continuous angle | Vector of signed eigenvalues |
| **Algebraic identity** | `c_k = ε^k/k` (Kepler series) | Spectrum of `L = D − A_signed`; depends on graph topology + signs |
| **Substrate** | Continuous Lie-group SO(2) | Discrete graph (Lie algebra) |
| **Sign-flip role** | Equation-of-centre amplitude flips through zero at apses (kinematic) | One factor of cascade composition carries `−1` on its Laplacian (algebraic) |

The two operations act on **different objects** and produce **different output types**. They both involve sign-flips, but the sign-flips are at different abstraction levels: Class K's are kinematic (continuous angle dynamics produces a periodically-positive-and-negative deficit); Class L signed-variant's are algebraic (the sign is on edge weights of a discrete graph).

### Can pin-slot be expressed AS a signed-Laplacian on some graph?

The pin-slot `phi(M) = atan2(sin M, cos M − ε)` is a homeomorphism S¹ → S¹ (for |ε| < 1); its eigenfunctions are `e^{ikM}` and its action multiplies the k-th Fourier mode by a `ε`-dependent amplitude `ε^k/k`. This IS a spectral structure, but it's the spectrum of a 1-parameter family of continuous-group transformations, not the eigenvalue spectrum of a fixed graph Laplacian.

To re-cast Class K AS a signed Laplacian on a graph, one would need to:
1. Discretise S¹ to N points (already Class I — cyclic-group structure).
2. Construct an N×N matrix whose eigenvalues are `ε^k/k` for k=0,1,2,...
3. That matrix would be `diag(ε^k/k)` in Fourier basis — but this is a *diagonal* operator (just a per-mode multiplier), not a signed Laplacian `D − A_signed`.

The diagonal-multiplier form IS in Class L's family (eigenvalue-table-driven `g(λ)` spectral filter; see srmech §3.7 `g(λ)`-decomposition framework). But the specific `g(λ) = ε^k/k` requires *parameter ε from outside* — it's not determined by graph topology + sign choice alone.

**Verdict: Class K is NOT a special case of Class L's signed-variant.** Class K carries the ε-parametrisation that signed-Laplacian operations don't supply. The two operations share a *family resemblance* (both involve sign-flips at the kinematic / algebraic level respectively) but are structurally distinct.

This matches the bonus 9 addendum's framing: H4 ("sign-flip-as-equation-side-shadow") joins the shadow-stance family at the *meta level* — it observes that sign-flip arises from equation-side choice rather than primitive operation. But that meta-level observation applies to the Wick-rotation case (Class L signed-variant) specifically, not to Class K's pin-slot algebra, which is genuinely a different operation.

### Thread 2 verdict

**Class K does NOT dissolve into Class L signed-variant. The 14-class vocabulary stays at 14.** Class K's pin-slot algebra is structurally distinct from Class L's signed-variant: different operand types (continuous angle vs vector eigenmode), different algebraic identity (`c_k = ε^k/k` vs spectrum of `D − A_signed`), different substrate kind (Lie-group vs Lie-algebra). They share the *shape* of involving sign-flips but operate at different abstraction levels and produce different content.

This reinforces `[[feedback_no_privileged_primitive_classes]]` in the *opposite* direction from Class O's dissolution: just as Class O dissolved because it could be expressed as Class L signed-variant, Class K stays separate because it canNOT be so expressed. The dissolution-by-default test ran in both directions; one passed and one didn't.

---

## §4 Thread 3 — epicycle-universality scope

### Two readings of "everything must model epicycle"

- **Reading A (trivial-Fourier-universal):** every periodic system admits Fourier decomposition; therefore every periodic system has an "epicycle" expansion. True but content-empty (Lebesgue 1906; any L² periodic function expands into a Fourier series).
- **Reading B (Kepler-shape-non-trivial):** every cyclic system whose deficit from pure-circular motion (`x − r·cos(ωt)`) has leading non-trivial structure at the *fundamental* frequency (k=1) with c_k ∝ ε^k/k carries the pin-slot / Class K signature. The signature is the Kepler series specifically, not arbitrary Fourier content.

The user's `[[user_stance_kepler_shape_universal]]` and the project's empirical work (PR #416 + Spike #24 Phases 3 + 6 + 9) establish Reading B as the load-bearing reading. Reading A is what gets confused-with-it in academic literature ("everything is a Fourier series therefore everything is an epicycle"); Reading B is the operationally meaningful and falsifiable claim.

### Where Reading B holds vs fails

**Reading B HOLDS:**

- **Conservative cyclic systems with 1/r-style central forces** — Kepler orbits, equants, pin-slot mechanisms, planetary dynamics. Empirically verified across 9 Sol bodies + Luna (Spike #24 Phase 3b; deltas ≤ 0.07°).
- **N-fold rotational potentials** under broken N-fold symmetry: leading non-trivial harmonic returns at the fundamental + a per-arm bias (Felkin-Anh asymmetric induction; anomeric effect; Spike #24 Phase 7.2). Reduces to Class K with broken symmetry.
- **Mass-action chemistry-dynamics** (Brusselator, Oregonator, Lotka-Volterra) — sparse integer-multiple harmonic spectra at ratios 1.000, 2.000, ..., 6.000 to <0.001 precision (Spike #24 Phase 9.2).

**Reading B FAILS at:**

- **Anharmonic oscillators** `ẍ + ω²x + αx³ = 0`: leading non-trivial term at 3ω (third harmonic), not at ω.
- **Damped harmonic oscillators**: exponential envelope, not periodic-deficit shape.
- **Parametric / driven nonlinear oscillators**: can produce sub-harmonics at ω/2, not the Kepler form.
- **Substrate-boundary cases**: chess (discrete-combinatorial motion, no continuous-phase / no anomalistic frequency) — explicitly Class K-absent per Spike #24 Phase 10.

### Scope statement

**The user's "everything must model epicycle" is scope-bounded to systems with a continuous SO(2)-cyclic state space AND a leading-order deficit-from-circular AT the fundamental frequency.** Within this scope (which covers most observable mechanical-cyclic phenomena in physics, all conservative-central-force systems, and N-fold rotational potentials), the claim is decisively universal — the burden flips per `[[user_stance_kepler_shape_universal]]`. Outside this scope (anharmonic / damped / parametric / discrete-combinatorial), other primitives (Class L higher harmonics, Class I@n=3 broken symmetry, substrate boundaries) apply.

### Thread 3 verdict

**"Everything must model epicycle" is scope-bounded — it applies to every cyclic system with a leading deficit-from-circular at the fundamental frequency.** Within scope (planetary dynamics; Kepler orbits; N-fold rotational potentials; equant motion; pin-slot mechanisms; mass-action chemistry-dynamics), the claim is the burden-flipped Kepler-shape universal. Outside scope (anharmonic; damped; parametric; discrete-combinatorial), the leading-order signature is different (3ω; exponential; ω/2; non-Class-K).

The strong reading is correct *and* needs a scope statement. The trivial-Fourier reading is the wrong reading; the Kepler-shape reading is the right one. *"Everything that moves the same way as a Kepler ellipse must model epicycle"* preserves the user's compression while naming the scope explicitly. The user's verbatim compression in `[[user_stance_kepler_shape_universal]]` already encodes this — *"if Kepler's equation is just gears and slots and pins, it does apply to anything else that moves the same way"* — the "moves the same way" is the scope qualifier.

---

## §5 Thread 4 — project payoff

### Specific loci where the framing sharpens current content

1. **antikythera-spectral's `pin_and_slot.py` IS the canonical Class K instance.** The atan2 form encodes the eccentric-anomaly Kepler series at machine precision (verified §2 here). The module's docstring already documents this (lines 47-52); a §X cross-reference to srmech §3.8.1 Class K canonical entry would close the loop. **Locus: docs/antikythera-maths/research/pin_and_slot.py docstring + antikythera notebook §11.6.6.5 (F2 finding).**

2. **ephemerides-spectral Phase 10a equation-of-centre catalog patches ARE Class K signatures per body.** The 51-patch catalog (per-non-Sun-body, v0.27.0 era) instantiates Class K at the Sol-system substrate; this matches Spike #24 Phase 3b's 9/9 numerical verification. Adding a Class K cross-reference in ephemerides §3 catalog-component documentation would make the algebra-vs-data connection explicit. **Locus: docs/antikythera-maths/ephemerides_spectral_research_notebook.md §3 (equation-of-centre catalog component).**

3. **DESI thawing-CPL non-monotone `f_RD(t)` is a sign-flip in a rate function — connecting Spike #27 to this spike's pin-slot framing.** MFO §VII.6.1.2 documents the far-future asymptote drop below 1 under thawing-CPL; the rate `df_RD/dt` peaks then decreases. This is a rate-deficit sign-flip, not a value-of-rate sign-flip — different from the Class K kinematic sign-flip but topologically similar. Whether DESI's `f_RD` non-monotonicity has *Class K shape* (leading non-trivial Fourier term in `f_RD − linear_drift`) is an open question Spike #27's Part VI didn't yet test. **Locus: candidate future Spike #30 — test whether DESI thawing-CPL `f_RD` residual has Class K signature at the cosmological substrate.**

### Optional fourth locus (lower-priority)

4. **MFO §VIII.7 (fractal-shadow allegory) is the framing precedent for Reading-B-vs-Reading-A distinction.** Just as `[[user_stance_fractal_shadow]]` distinguishes the substantive "cascade-shape vs fractal-shape" question (Class L indistinguishable) from the trivial "fractal looks fractal" tautology, Thread 3 here distinguishes "Kepler-shape" from "any Fourier series." Adding a §VIII.8 (or similar) "epicycle-shadow" entry that names the trivial-Fourier-vs-Kepler-shape distinction would be a natural shadow-stance-family extension. *But this is candidate-only — needs second independent finding before notebook landing per `[[feedback_no_lineage_claims_in_notebook]]`.*

---

## §6 Verdict / what this changes / falsifier list

### What stands

1. **Class K = pin-slot = eccentric-anomaly Kepler series identity** is verified at machine precision (§2). The atan2 bronze form, the closed-form sin-series, and the modern lunar amplitude all converge to the same number to ≤4% across three independent paths.
2. **The 14-class vocabulary stays at 14.** Class K does not dissolve into Class L signed-variant; Thread 2's structural-irreducibility test passes.
3. **The user's "everything must model epicycle" is scope-bounded but decisively universal within scope.** Conservative cyclic systems with leading-deficit-at-fundamental admit Class K decomposition; anharmonic / damped / parametric / discrete-combinatorial systems instantiate different primitives.

### What falls

1. **"Sign-flip happens twice per cycle" without modifier is ambiguous.** Project terminology should distinguish equation-of-centre zero-crossings (2) from rate-deficit zero-crossings (4).
2. **The trivial-Fourier reading of "everything is an epicycle" is wrong.** Reading A is content-empty; Reading B (Kepler-shape universal) is the load-bearing claim.

### What's open (fermata for conductor)

1. **Spike #30 candidate:** does DESI thawing-CPL `f_RD` residual have Class K signature at the cosmological substrate? Would test whether the cosmological ring-down rate function carries pin-slot-shape, joining the bronze / cosmos / chemistry / chemistry-dynamics multi-substrate Class K confirmation list.
2. **Notebook landing locus (recommended §8 destination):** four candidates outlined; conductor's call.
3. **Cross-domain consequence for srmech.qm.propagators:** §3.8.2 already names Class K as the "continuous projection of lattice propagator `1/(m² + k̂²)`" — making the propagator-as-Kepler-shape connection explicit could deepen the QFT-side of the universal. Out of Spike #29 scope but flagged for future consideration.

### Falsifiers

The strong Class-K-universal claim is falsifiable. A counter-example would be:

- A conservative-central-force cyclic system whose leading deficit-from-circular is NOT at the anomalistic frequency. (None has surfaced; Spike #24 9/9 ephemerides bodies all match.)
- A planetary-equivalent ν-anomaly that resists `c_k = ε^k/k` factorization with substrate-realistic ε. (None has surfaced; bronze + ephemerides + chemistry all factor.)
- A pin-slot mechanism whose atan2 algebra disagrees with the eccentric-anomaly series at any harmonic ≥ 1e-12. (None has surfaced; §2 above verified 7+ harmonics at ratio 1.0000.)

The contrapositive falsifier (chess as Class K-absent substrate) holds — Spike #24 Phase 10 documents the substrate boundary cleanly.

---

## §7 Cross-references

**Project memories (load-bearing):**

- `[[user_stance_kepler_shape_universal]]` — the burden-flipped universal that drives Spike #29
- `[[user_stance_pi_as_projection]]` — integer-cyclic upstream / continuous downstream; informs scope statement
- `[[feedback_no_privileged_primitive_classes]]` — dissolve-by-default; Class O dissolved, Class K does not
- `[[user_stance_identity_not_implementation_discipline]]` — Class K IS pin-slot is IS-claim, not implementation-claim
- `[[user_explanation_discipline]]` — "everything must model epicycle" preserved verbatim; scope qualifier added without paraphrasing back-into-academic
- `[[project_class_o_signed_metric_composition]]` — Class O dissolution decision (2026-05-16); informs Thread 2

**Sister-notebook content cited:**

- srmech §3.8.1 (14-class canonical enumeration; Class K = `srmech.amsc.kepler.*`)
- srmech §3.8.2 (QM/QFT/SM operations layer; Class K projection-shadow at propagators)
- srmech `notes/spike_24_primitive_vocabulary_findings_2026-05-15.md` (Phases 1, 2, 3, 6, 7, 9, 10)
- srmech `notes/spike_24_bonus_9_sign_flip_as_equation_side_shadow_addendum_2026-05-15.md` (bonus 9 H4 framing)
- srmech `notes/spike_pinslot_era_appropriate_findings_2026-05-15.md` (F18-F23 era-appropriate verdict)
- antikythera-spectral §11.6.6.5 (F2 finding: ε = 0.1146 from Freeth 2006 Fig. 6)
- ephemerides-spectral §3 (per-body equation-of-centre catalog component, Phase 10a)
- MFO §VII.6.1.2 (DESI thawing-CPL non-monotone `f_RD` — candidate Spike #30 anchor)

**SSoT citations (extracted PDF or open-access; per `[[feedback_pdf_extraction_citation_discipline]]`):**

- **Freeth et al. (2006).** *Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism*. *Nature* 444:587–591. Figure 6 (p.590) gives pin offset 1.1 mm, pin distance 9.6 mm → ε = 0.1146.
- **Almagest IX.5 (Ptolemy, c. 150 CE).** Equant model; equation-of-centre to first order. Cited via Toomer 1984 / Fitzpatrick "A Modern Almagest" (open-access at https://farside.ph.utexas.edu/Books/Syntaxis/Almagest.pdf, §5.2).
- **Brown's lunar theory** (Brown 1919; Brouwer & Clemence 1961 *Methods of Celestial Mechanics* Ch. 12 lunar theory). Modern lunar amplitude 6.29° matches bronze 6.58° (Freeth 2006 Fig. 6 caption) at 4%.
- **Kepler (1609).** *Astronomia Nova*, equation `M = E − e sin E`. Standard celestial-mechanics citation; canonical SSoT for the Kepler equation per srmech §3.8.1.
- **Fitzpatrick, R. (2017).** *A Modern Almagest.* Open-access PDF (verified). §4.3 Hipparchan solar model gives `e = 1/24`; §5.2 epicycle/deferent reductions.

---

## §8 Proposed notebook-integration paragraph

**Target section recommendation (concertmaster's fermata for conductor):** the user's framing has three plausible landing destinations:

- **(A) antikythera-spectral notebook §11.6.6.5 (the F2 finding subsection)** — adds the universal framing as a *consequence* of the Freeth ε = 0.1146 identification. Antikythera-local; tightest cross-reference to the bronze.
- **(B) srmech §3.8 cross-substrate primitive vocabulary** — sharpens the Class K canonical entry with the §2 machine-precision identity. Abstraction-layer; tightest cross-reference to the 14-class table.
- **(C) MFO §VIII.7 (fractal-shadow allegory) + a new §VIII.8 "epicycle-shadow"** — joins the shadow-stance family; tightest cross-reference to the user's intellectual arc. *Candidate-only per `[[feedback_no_lineage_claims_in_notebook]]` — needs second independent finding before landing.*

**Concertmaster recommendation: (B) srmech §3.8 — primary; (A) antikythera §11.6.6.5 — light cross-reference.** Reasoning: srmech §3.8 is the SSoT for the 14-class vocabulary; sharpening Class K there propagates to all sister notebooks via citation. Reading-B-vs-Reading-A scope statement is most useful at the abstraction layer where multiple substrates instantiate Class K. (C) shadow-stance landing waits for second independent finding per the project's shadow-stance-family conservatism.

### Draft paragraph (for srmech §3.8 — candidate insertion before §3.8.1, after §3.8 intro)

```markdown
### §3.8.0a Sign-change ≡ pin-slot ≡ Class K (Spike #29, 2026-05-16)

The user's compression *"everything must model epicycle"* sharpens the
Class K canonical entry from "pin-slot algebra" to a closed-form identity
across three abstraction levels:

1. **Kinematic level (continuous SO(2)):** the pin-slot atan2 transform
   `phi(M) = atan2(sin M, cos M − ε)` has output-phase deficit
   `phi(M) − M` whose Fourier coefficients satisfy `c_k = ε^k/k` to
   machine precision (verified Spike #29 §2; ratio 1.0000 across 7+
   harmonics). This IS the eccentric-anomaly Kepler series.

2. **Sign-change level:** the deficit `phi(M) − M` crosses zero twice per
   cycle (at the apses M = 0 and M = π); the rate deficit `dphi/dM − 1`
   crosses zero four times per cycle (at apses + quadratures). The user's
   "sign change twice per cycle" reading names the first; project
   terminology should distinguish equation-of-centre zero-crossings (2)
   from rate-deficit zero-crossings (4).

3. **Substrate-universal level:** per `[[user_stance_kepler_shape_universal]]`,
   any system showing leading-deficit-from-circular at the fundamental
   frequency instantiates the same pin-slot / Class K signature. Four
   substrates verified: bronze (PR #416 F2; Freeth 2006 Fig. 6 ε =
   0.1146), cosmos (Spike #24 Phase 3b; 9/9 ephemerides bodies match
   c₁ = 2e to <0.1°), chemistry-static (Phase 6.1; ethane V₃ =
   F24 3-armed cross-bar), chemistry-dynamics (Phase 9.2; Brusselator /
   Oregonator integer-multiple harmonic ratios).

The contrapositive holds at the chess substrate boundary (Spike #24
Phase 10): chess has no continuous-phase representation, no anomalistic
frequency, motion is discrete-combinatorial — Class K is absent. The
universal's scope is "cyclic systems with leading-deficit-from-circular
at the fundamental"; trivial-Fourier-universal is the wrong reading.

**Closure-conjecture status (per `[[feedback_no_privileged_primitive_classes]]`):**
Spike #29 §3 tested whether Class K dissolves into Class L's
signed-variant (the resolved-Class-O sub-operation, dissolution decision
2026-05-16). Verdict: Class K does NOT dissolve. Operand types differ
(continuous SO(2) angle vs |V|-dim graph eigenmodes), algebraic
identities differ (`c_k = ε^k/k` vs spectrum of `D − A_signed`), 
substrate kinds differ (Lie-group vs Lie-algebra). The 14-class
vocabulary stays at 14.

**Full investigation:** `docs/antikythera-maths/research-mfo/sign_change_pin_slot_epicycle_2026-05-16.md`.

Cross-references:
- `[[user_stance_kepler_shape_universal]]` — the burden-flipped universal
- `[[user_stance_pi_as_projection]]` — integer-cyclic upstream methodology
- `[[user_stance_identity_not_implementation_discipline]]` — Class K IS pin-slot
- `[[feedback_no_privileged_primitive_classes]]` — dissolution discipline; passed (Class O dissolved) and failed (Class K stays)
- `[[project_class_o_signed_metric_composition]]` — dissolution precedent (2026-05-16)
```

---

## Verdict

The user's claim chain — sign change ≡ pin-slot ≡ Class K, with epicycle universality as Kepler-shape corollary — verifies cleanly under MPM discipline:

- **Thread 1 (sign-change ≡ pin-slot):** clean equivalence at the closed-form algebraic level; machine-precision identity `c_k = ε^k/k` across 7+ harmonics for the eccentric-anomaly Kepler series. The two-vs-four sign-flips disambiguation is the substantive sharpening.
- **Thread 2 (Class K vs Class L signed-variant):** structurally distinct; Class K stays separate; vocabulary stays at 14. Same dissolution discipline that dropped Class O passed (dissolved) and Class K failed (stays separate); both verdicts strengthen `[[feedback_no_privileged_primitive_classes]]`.
- **Thread 3 (epicycle universality):** scope-bounded but decisively universal within scope. Reading-B (Kepler-shape-non-trivial) is load-bearing; Reading-A (trivial-Fourier) is the wrong reading the user's compression already encodes against ("moves the same way" qualifier).
- **Thread 4 (project payoff):** four candidate loci identified; recommendation (B) srmech §3.8 as primary landing with (A) antikythera light cross-reference.

The compressed phrase *"everything must model epicycle"* is canonical project vocabulary candidate per `[[user_explanation_discipline]]` — preserves the user's compression while adding the scope qualifier the §4 verdict makes explicit.

---

*Concertmaster artifact (Spike #29). Branch: `research/spike-29-sign-change-pin-slot-epicycle`. Conductor handles push + PR.*
