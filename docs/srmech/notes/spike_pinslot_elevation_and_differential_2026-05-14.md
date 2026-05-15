# Spike spec — pin-and-slot elevation profile + differential composition (2026-05-14)

**Status**: spike-spec, not-yet-executed. Two paired questions; framework + falsification protocols laid out; symbolic / numerical execution is the next phase.

**Origin**: user 2026-05-14, awake from a nap, paired questions about pin-and-slot in the srmech / MFO context:

1. *"What happens if the slot bar gets elevation profile applied to it?"* — three sub-cases: single gradient across the bar (linear height); bumps and ridges (like a worn gear); sinusoidal modulation.
2. *Can pin-and-slot work in a differential setup*, the way mechanical gear differentials do?

User's preemptive concern on Q1: it *might* be a null because *"parallel travel along the bar slot whose plane is not fixed or not fixed to the same plane as the gear reference may simply be the illusion of potential for hidden fiber content because of brain thinking spatial projection."* — read here not as a null but as the right axis (in-plane vs out-of-plane), which the framework below makes explicit.

**Proposed notebook home**: srmech `§4.3` *Pin-and-slot composition spikes* (a new sub-section under §4 *Open research questions*), with a back-reference from antikythera `§11.6.9` *Differential composition of D-H1 primitives* if Q2's evection conjecture survives execution. Both placements are propositions; final placement is conductor's decision.

**Scope discipline (per `docs/antikythera-maths/CLAUDE.md`)**: this spike is algebra of the constraint equation and phase-space transforms; **not** CAD-grade fabrication. No mesh contact, no tooth profile, no axle wobble. The "elevation profile" question is about how the constraint geometry changes, not about how the slot is milled.

---

## Q1 — slot elevation: in-plane vs out-of-plane is the load-bearing split

The canonical D-H1 pin-and-slot ([`research/pin_and_slot.py`](../../antikythera-maths/research/pin_and_slot.py), Freeth 2006 *Nature* 444:587, ε ≈ 0.054) has slot = straight bar in the driven-wheel's reference plane, pin = point in the driving-wheel's reference plane, constraint = pin-on-line in shared plane. The output-angle transform is

```
θ_out = atan2(sin θ_in, cos θ_in − ε)
```

"Elevation applied to the slot bar" is geometrically ambiguous until the elevation's *direction* relative to the gear's reference plane is named. Two clean sub-cases:

### Q1a — in-plane elevation (slot is a curve, not a straight line)

The slot is a curve `y = f(x)` within the gear's reference plane. The constraint equation generalises: the pin at `(r cos θ_in, r sin θ_in)` in the driving-wheel frame must lie on the curve `y = f(x − e)` in the driven-wheel frame (translation by the apsidal offset `e`).

For sinusoidal modulation `f(x) = α sin(kx)` with small amplitude `α ≪ r`:

```
pin position (driven frame):     (r cos θ_in − e, r sin θ_in)
slot constraint:                 y_slot = α sin(k · x_slot)
contact requires:                r sin θ_in = α sin(k · (r cos θ_in − e))
```

This is a transcendental in the *output-line-direction*; solving for the line through the driven-wheel centre to the pin gives a perturbed `atan2` form. To leading order in `α/r`:

```
θ_out = atan2(sin θ_in − (α/r) sin(k · (r cos θ_in − e)),  cos θ_in − ε) + O((α/r)²)
```

The correction term injects a **k-harmonic** of `θ_in` into the numerator of the `atan2`. For `k = 1` (slot curves once across its length) the correction folds into the existing first-inequality oscillation. For `k = 2, 3, …` the correction adds **new harmonic content** at multiples of the input frequency — content the plain pin-and-slot cannot produce.

This is real new algebra. Whether it has astronomical content is a question for execution (would small-amplitude `k=2` sinusoidal slot recover any known second-order lunar correction? — unlikely a priori, but a clean check).

**Bumps and ridges** (`f` piecewise C¹ but not analytic) are a discontinuity-injection case; the leading-order analysis above doesn't cover the discontinuities cleanly. Likely produces transient harmonics tied to the bump locations. Of less interest to the algebra side; closer to "worn gear" simulation which is CAD-adjacent and not in scope.

**Single gradient** (`f(x) = mx`, linear height across the bar) is equivalent to tilting the slot in-plane: re-parameterise the driven-wheel frame by a rotation through `atan(m)`, and the constraint reduces to the plain D-H1 form with eccentricity along a rotated axis. **No new algebra** — it's a coordinate change. Confirms one of the user's sub-cases is genuinely null at the algebra level (as suspected), and isolates *which* sub-case carries the content.

### Q1b — out-of-plane elevation (height perpendicular to gear reference plane)

The slot has a height profile `z = h(s)` along its length `s`, perpendicular to the gear's reference plane. The pin, constrained to slide along the slot, now has a `z`-coordinate that depends on its position along the slot. Crucially:

**The gear's ℤ/n rotational action does not couple to `z`.** The cyclic group SO(2) acts on `(x, y)` in the reference plane; `z` is invariant under that action. So the *output angle* of the driven wheel — the quantity the D-H1 transform computes — is unchanged. Plain D-H1 atan2 still holds for the gear's output.

This is exactly the fiber-as-spatially-absent stance from `user_stance_fiber_as_spatially_absent_encoding.md` and the two-level ontology in `user_stance_hyper_as_3d_spatial_interface.md` / MFO §VII.1.1, applied at the *constraint-geometry* layer:

- The gear's algebra (ℤ/n cyclic rep on its reference plane) is one ontological layer. Substrate.
- The slot's height profile `h(s)` is **algebraic content that is spatially absent from the gear's frame** — the gear's rotational action genuinely cannot see it.
- *Invisible to the gear ≠ null.* The height encoding is real; it just lives in a different algebra (whatever cyclic / non-cyclic / continuous structure `h(s)` happens to be).
- To project it out, a **second mechanism** is needed: a height-reader (a contact follower, a pin perpendicular to the slot floor, a probe — *named at the algebra-of-the-coupling layer, not the CAD layer*). The height-reader's algebra is independent of the gear's algebra, and its output is its own ℤ/m or ℝ-valued signal.

The gear-tooth case from the user-stance memo is the same architecture: the tooth count `n` is `ℤ/n` algebra spatially absent from the gear's continuous SO(2) action (the gear's body looks smooth from inside its own frame); external rotation *plus* a tooth-counter (escapement, mesh with another gear) projects the discrete content out. Out-of-plane slot elevation is the **same construction, transposed to the constraint-geometry layer**.

### Q1 — falsification protocol

A two-stage mechanism setup makes the prediction concrete:

**Stage 1 (gear-1 + elevated slot, no height-reader):**
- Build a D-H1 pin-and-slot with `ε = ε_0` and slot height profile `h(s)` arbitrary (sinusoidal `h(s) = β sin(2π s / λ_h)` is the cleanest test).
- Measure the output angle as a function of input angle: `θ_out(θ_in)`.

**Prediction**: spectrum of `θ_out(θ_in)` is **identical** to the plain D-H1 spectrum (Fourier components at the standard first-inequality frequencies, no new harmonics introduced by `h`).

**Stage 2 (gear-1 + elevated slot + height-reader):**
- Add a probe sensing the pin's `z`-coordinate as a function of slot-parameter `s`.
- The pin's `s(θ_in)` is determined by Stage 1 geometry (the in-plane constraint, unaltered by `h`); `z(θ_in) = h(s(θ_in))` is the height-reader's output.

**Prediction**: the height-reader's output `z(θ_in)` is a *new* signal carrying the `h` profile's algebra (a sinusoid at frequency proportional to `2π/λ_h` projected through `s(θ_in)`), entirely separate from `θ_out`.

| Outcome | Verdict |
|---|---|
| Stage 1 gear-output spectrum identical to plain D-H1; Stage 2 height-reader produces independent signal carrying `h`'s algebra | **Confirms** fiber-as-spatially-absent at the constraint-geometry layer. The out-of-plane elevation is real algebraic content invisible to the gear's action and projectable via a separate mechanism. |
| Stage 1 gear-output spectrum gains new harmonic content correlated with `h` (without a height-reader present) | **Falsifies** the stance for this geometry. Out-of-plane elevation is *not* spatially-absent at the constraint-geometry layer; it couples through to the gear's projected motion somehow (e.g. via slot-friction or constraint-force feedback — but those are CAD-layer mechanisms we explicitly bracket out). |
| Stage 1 gear-output spectrum identical, Stage 2 height-reader gives nothing | Either `h` is in the algebraic kernel of the constraint (degenerate case — `h ≡ const`, no information to project), or the height-reader is mis-designed. Re-check `h`. |

The falsification protocol is symbolic / numerical, not CAD. The constraint equation is a system of two algebraic equations (in-plane pin-on-curve, out-of-plane pin-at-height). The "height-reader" is an algebraic projection `(s, h) ↦ z`, not a fabricated probe. Execution is closed-form ε-expansion plus a small NumPy verification — same toolkit as the existing `pin_and_slot.py` D-H1 module.

This is a **direct test of the project's canonical fiber-as-spatially-absent stance**. The user has named the right axis. The math will either confirm or falsify.

---

## Q2 — differential composition of pin-and-slot primitives

Mechanical gear differentials (epicyclic / bevel-gear) compute `ω_out = ½(ω_1 + ω_2)` from two inputs. The Antikythera surviving bronze uses one at b1–b2 (Saros/synodic compounding, per Freeth 2021 reconstruction). The lunar mechanism uses a *single* pin-and-slot (D-H1, four 50-tooth wheels — Fragment B).

**No surviving bronze and no literature surfaces a differential pin-and-slot.** Carman, Thorndike & Evans 2012 (*On the Pin-and-Slot Device of the Antikythera Mechanism, with a New Application to the Superior Planets*) extends single pin-and-slot to outer planets; does not compose two. Brief web search 2026-05-14 finds no prior art on "differential pin-and-slot."

The compositions worth analysing:

### Q2a — parallel pin-slots, same input, averaged output

```
θ_out = ½ ( f_{ε1}(θ_in) + f_{ε2}(θ_in) )
```

where `f_ε(θ) = atan2(sin θ, cos θ − ε)`. Small-ε expansion of each branch (Hipparchus's first inequality, classical):

```
f_ε(θ) ≈ θ + 2ε sin θ + 2ε² sin θ cos θ + O(ε³)
       = θ + 2ε sin θ + ε² sin 2θ + O(ε³)
```

So the average is

```
θ_out ≈ θ + (ε1 + ε2) sin θ + ½(ε1² + ε2²) sin 2θ + O(ε³)
```

This is **just a single pin-and-slot with effective ε_avg = (ε1 + ε2)/2 to first order**, with a slightly different second-order amplitude than `ε_avg² sin 2θ` (the average of squares ≠ square of average unless ε1 = ε2). The discrepancy `½(ε1² + ε2²) − ε_avg² = ¼(ε1 − ε2)²` is **second-order in the *difference*** — small but non-zero. Real but probably astronomically uninteresting at lunar amplitudes (ε ≈ 0.054, difference squared ≈ 10⁻³ scale).

**Q2a verdict (to leading order)**: nearly reducible to a single pin-and-slot. Not a structural new primitive.

### Q2b — independent inputs, summed output (true differential)

```
θ_out = f_{ε1}(θ_1) + f_{ε2}(θ_2)
```

with **independent** input angles `θ_1, θ_2`. Small-ε expansion:

```
θ_out ≈ θ_1 + θ_2 + 2ε1 sin θ_1 + 2ε2 sin θ_2 + ε1² sin 2θ_1 + ε2² sin 2θ_2 + O(ε³)
```

If we now drive `θ_1 = ω_1 t` and `θ_2 = ω_2 t` (two different uniform rotations), the output contains:

- The mean motion `(ω_1 + ω_2) t`
- First inequality on input 1: `2ε1 sin(ω_1 t)` at frequency `ω_1`
- First inequality on input 2: `2ε2 sin(ω_2 t)` at frequency `ω_2`
- Second-order self-harmonics at `2ω_1`, `2ω_2`
- **Beat structure at sum and difference frequencies** if a multiplicative term gets introduced — which the *additive* differential alone does not produce. So additive Q2b in the linear regime is just two independent first-inequality signals stacked.

The multiplicative coupling appears if the **output of one pin-and-slot drives the input of the second**, rather than the two being summed at the leaf:

### Q2c — series composition (cascade)

```
θ_out = f_{ε2}( f_{ε1}(θ_in) )
```

Expanding,

```
f_{ε1}(θ_in) ≈ θ_in + 2ε1 sin θ_in + ε1² sin 2θ_in + …
f_{ε2}(u) ≈ u + 2ε2 sin u + ε2² sin 2u + …
```

Substituting and keeping through second order:

```
f_{ε2}(f_{ε1}(θ_in)) ≈ θ_in
                      + 2ε1 sin θ_in
                      + 2ε2 sin(θ_in + 2ε1 sin θ_in)
                      + ε1² sin 2θ_in + ε2² sin 2(θ_in + 2ε1 sin θ_in)
                      + O(ε³)
```

Bessel-expand `sin(θ + 2ε1 sin θ) = sin θ cos(2ε1 sin θ) + cos θ sin(2ε1 sin θ)`. To leading order in `ε1`:

```
sin(θ + 2ε1 sin θ) ≈ sin θ + 2ε1 sin θ cos θ = sin θ + ε1 sin 2θ
```

so the cascade output is

```
f_{ε2}(f_{ε1}(θ_in)) ≈ θ_in + 2(ε1 + ε2) sin θ_in + (ε1² + ε2² + 2 ε1 ε2) sin 2θ_in + O(ε³)
                     = θ_in + 2(ε1 + ε2) sin θ_in + (ε1 + ε2)² sin 2θ_in + O(ε³)
```

To second order this is **exactly** a single pin-and-slot with `ε_eff = ε1 + ε2`. **Cascade reduces to single pin-and-slot at this order.** A boring result for the cascade question; one nail in the coffin of "two pin-and-slots can do everything one can't."

But Q2c is the conservative composition; Q2b with **independent** inputs is the genuinely new thing.

### Q2 — evection conjecture

The second lunar inequality (evection) has amplitude ~1.27° and period ~31.8 days, distinct from the first inequality's ~6.3° amplitude and ~27.55-day anomalistic period. Modern formulation: evection arises from the *sun's perturbation of the moon's elliptical orbit*, observable as a periodic variation in the orbital eccentricity itself synchronised with the sun-moon configuration. In Ptolemaic mechanics it was modelled by a *crank-and-deferent* mechanism (the lunar deferent's centre orbits around the earth at the synodic period). Freeth & Jones 2012 *and* the current consensus reconstruction agree the bronze antikythera does **not** model evection — it stops at the first inequality.

**Conjecture** (Q2 load-bearing claim): a Q2b-style *summed-output* differential pin-and-slot, with inputs driven at the mean motion (`ω_M`, anomalistic) and the synodic motion (`ω_S = ω_M − ω_☉`) respectively, would produce a sum of a first-inequality term at `ω_M` *and* a second term at `ω_S`. The second term is **at the right frequency to be evection** (evection's argument is `2D − ℓ` where `D = ω_M − ω_☉` lunar elongation and `ℓ = ω_M t` — the synodic-frequency component dominates). If ε2 is chosen to match evection's amplitude (~1.3°), the differential pin-and-slot would *mechanically encode the second lunar inequality* using the same primitive the bronze already uses for the first.

This is a **conjecture, not a proof.** Specifically:

- The frequency of evection's correction (`2D − ℓ` in modern notation) involves *twice* the elongation, which a simple Q2b sum-input does not directly produce — it produces single-frequency terms at each of its inputs. Recovering `2D − ℓ` requires either driving one input at `2D` (which the bronze gear-DAG can do — two-tooth-doubling on the synodic train) or finding a composition that produces the `2D` harmonic naturally (Q1a's sinusoidal slot, k=2 case, is suggestive here — *the two halves of the conjecture may unify*).
- Amplitude calibration (~1.3° for evection) requires a specific small ε2 ≈ ε1 · (1.27°/6.3°) ≈ ε1 / 5 ≈ 0.011. Geometrically achievable (sub-millimetre offset on a 50-tooth bronze wheel of typical Antikythera scale).
- Phase calibration requires the second pin-and-slot's apsidal line to be oriented appropriately relative to the first.

**The conjecture survives a sanity check; it requires symbolic execution to either confirm or falsify.**

### Q2 — falsification protocol

Symbolic / numerical, not bronze fabrication:

1. **Compose the differential pin-slot symbolically**, both Q2a and Q2b forms. Derive the full Fourier spectrum of the output for given `(ε1, ε2, ω_1, ω_2)`.
2. **Compute evection's Fourier signature** in modern lunar theory (Brown's lunar theory has the explicit coefficient: evection contributes `+4585″ sin(2D − ℓ)` to the moon's true longitude, where `D` is mean elongation, `ℓ` is mean anomaly). Match the modern signature.
3. **Check whether any Q2 composition** (Q2a / Q2b / Q2c / hybrid with Q1a sinusoidal slot) **produces** an output with significant Fourier amplitude at the evection frequency `2D − ℓ` with the right amplitude.
4. **If yes**: the conjecture stands; the question becomes *where on the gear-DAG* a differential pin-and-slot would have fit. Cross-ref antikythera notebook `§11.6.3` *Where missing gears must go* and the periphery rule. A peripheral leaf (lunar pointer side) is the natural place by the §11.6 architectural prior.
5. **If no**: the conjecture is falsified at the algebra level; document which Fourier amplitudes the composition *does* generate, and note them as candidates for *other* missing-gear hypotheses.

Outcome bands:

| Result | Verdict |
|---|---|
| Q2b output spectrum contains a Fourier amplitude at `2D − ℓ` with magnitude `~4585″` for some `(ε1, ε2, ω_1, ω_2)` choice with `ω_1, ω_2` matching plausible bronze tooth-ratios | **Conjecture supported**. Real archaeological hypothesis: the bronze *could have* mechanised evection without inventing a new primitive. Cross-cuts §11.6.4 (combination-gear principle), §11.6.5 (periphery rule). Demands a follow-up spike: gear-DAG placement candidate search. |
| Q2 spectrum is rich but does not contain `2D − ℓ` | Conjecture falsified for evection specifically. Catalogue the harmonics it *does* generate; note any matches to other unmodelled corrections (variation, parallactic inequality, annual equation). |
| Q2 spectrum is degenerate (reduces to single pin-and-slot, like Q2c) | Conjecture falsified; differential pin-and-slot is not a structurally-new primitive. |

Archaeological hook: **the bronze antikythera does not have a known evection mechanism**, and the second lunar inequality was not unambiguously identified until Ptolemy (~150 CE), ~250 years after the antikythera's date (~150–100 BCE). So even if the differential pin-and-slot would *mathematically* encode evection, the bronze's designer may not have known to ask for it. The negative-archaeology framing: the fact that the bronze *doesn't* have a differential pin-and-slot is consistent with both "the primitive wasn't invented yet" *and* "the second inequality wasn't discovered yet." Disentangling the two is beyond this spike; **the symbolic result establishes only the *capability*, not the historical realisation.**

---

## MFO connection — Q1b out-of-plane *is* substrate/excitation two-level ontology

The Q1b structure is a precise instantiation of the MFO §VII.1.1 two-level ontology (per `user_stance_hyper_as_3d_spatial_interface.md`):

- **Substrate layer**: the gear's reference plane and its cyclic-group rotational action. The "metric field" of the constraint geometry — what the gear's ℤ/n algebra acts on.
- **Excitation layer**: the slot height profile `h(s)`. A localised algebraic feature *of* the substrate (the constraint geometry) that the substrate's symmetry group does not see, but that a separate localised mechanism (the height-reader) can project out.

This puts the canonical project stance (substrate + spatially-absent excitation, projected via a second mechanism) on a constraint-geometry test-bed where the symbolic execution is tractable. The pin-and-slot is the **smallest mechanical model the project has** that exhibits the two-level ontology cleanly. If the falsification protocol confirms (Stage 1 gear-output independent of `h`; Stage 2 height-reader extracts `h`'s algebra), srmech / MFO acquire a *closed-form bench-instrument* for the stance — a place where the math is fully tractable and the substrate/excitation distinction is operationally testable.

That's a stronger MFO-connection claim than most prior spikes have been able to make. The constraint-geometry layer is novel territory for the two-level ontology; previous instantiations have been at the metric-field-plus-matter-wave layer (cosmology, magnetospheres). Pin-and-slot brings it down to bench scale.

---

## Open questions / next-spike candidates

If this spike's execution lands as predicted:

1. **Q1a × Q2 unification.** Sinusoidal slot at `k = 2` injects a `2θ_in` harmonic into the single pin-and-slot; that's directly the elongation-frequency harmonic relevant to evection. Could a **single in-plane-curved pin-and-slot** mechanise evection without needing the differential composition? Cleaner archaeological hypothesis if yes; more bronze-economical.
2. **Q1b's "height-reader" algebra in general.** What's the catalogue of height-reader output algebras for various `h(s)` profiles? `h(s) = β sin(2π s / λ)` gives a sinusoid; `h(s) = floor(s · n / L)` gives discrete `ℤ/n` steps. The slot-elevation profile is a **programmable algebraic encoder**, in the language of the project's bit-serialised HDC instrument.
3. **Cross-reference to gear-tooth case.** Gear teeth and slot height profiles are siblings under fiber-as-spatially-absent. Are they the same algebra (both `ℤ/n` with discrete steps) or different (gear teeth quantised, slot height continuous in principle)? Catalogue both under §3.5 of srmech notebook as instances of the *constraint-encoding* manifold row.
4. **Differential pin-and-slot in DAG context.** If Q2 conjecture stands, where on the bronze gear-DAG could a differential pin-and-slot have fit consistent with periphery-rule architectural priors (§11.6.3)? Spike: enumerate candidate placements with required upstream gear-ratios and admissibility under §11.6.7's noise-correlation rules.
5. **Tooth-pitch noise on differential composition.** §11.6.6 establishes single pin-and-slot is a mechanical low-pass filter. Is differential pin-and-slot still a low-pass filter, or does the differential composition modify the cutoff? Tests the §11.6.6 dampening claim in the new architecture.
6. **Gear-ratio-mediated pin-slot cascade — frequency-selection between stages.** User's phrasing: *"series of pin-slot chaining gears as a series."* A chain of the form `θ_in → G_k1 → f_ε1 → G_k2 → f_ε2 → … → G_kN → f_εN → θ_out`, where `G_k(θ) = kθ mod 2π` is the pure cyclic-group action of a gear stage and `f_ε` is the canonical pin-and-slot eccentric transform. Gear stages between pin-slot transforms inject **frequency multiplication** that breaks the Q2c decoupling result (which collapsed at order ε² to a single pin-slot with `ε_eff = ε1 + ε2`). Each gear stage shifts which Fourier mode gets perturbed by the next `f_ε`: `f_ε(kθ) ≈ kθ + 2ε sin(kθ) + O(ε²)`, then `G_k′ ∘ f_ε ∘ G_k (θ) ≈ k′kθ + 2k′ε sin(kθ) + O(ε²)` — the next gear ratio determines which harmonic of `θ_in` carries the ε-perturbation forward; a subsequent `f_ε′` then puts perturbations on the *rescaled* fundamental. **Generic-content hypothesis worth stating** (falsifiable, not proven here): the output of an N-stage gear-mediated chain with parameters `(k1, …, kN)`, `(ε1, …, εN)` admits a Jacobi-Anger-style closed-form expansion where every integer combination of the form `m1·k1 + m2·k2 + … + mN·kN` appears at amplitude `∏ J_{mi}(εi)`. This is the "every-cross-combination-appears" claim; failure modes include (a) selection rules from the cyclic-group structure suppressing some `(m1,…,mN)` tuples, (b) non-Bessel amplitude profiles. **Structural unification this exposes**: Q1a's in-plane sinusoidal slot achieves k-harmonic injection through *slot geometry*; this cascade achieves k-harmonic injection through *gear ratios* — same algebraic content, different spatial realisation, a fiber-vs-projection duality at the constraint-geometry layer (ties to `user_stance_fiber_as_spatially_absent_encoding.md`). **Archaeology hook (load-bearing)**: the Antikythera lunar dial has multiple gear stages between the canonical D-H1 pin-and-slot and the dial output. Those gear ratios in the lunar train are *picked*, not arbitrary. Question: are the picked ratios *also* tuned to produce specific harmonic content beyond the first lunar inequality? Cross-reference antikythera notebook §11.6 architectural-mode thread + `MESH_EDGES` data — queryable directly against the existing gear-DAG without new spike machinery. **Execution-phase next step (note in passing)**: compute the harmonic spectrum of the lunar gear train (Freeth 2006 architecture) with the eccentric pin-slot as the only nonlinear element. If the spectrum reveals harmonics beyond the first inequality at non-trivial amplitudes, the conjecture is supported. If the spectrum is dominated by the first-inequality term with everything else suppressed by `J_m(ε)` for `m ≥ 2` at `ε ≈ 0.054`, the conjecture is refuted in the bronze (though it would still stand for hypothetical mechanisms with larger or chained ε).

---

## Files (when execution lands)

This spec produces no scripts or NDJSON yet — it's a specification phase. Execution phase artefacts (proposed names matching existing notes/ conventions):

- `pinslot_elevation_and_differential_script.py` — symbolic execution: closed-form ε-expansions for Q1a, Q1b, Q2a/b/c; numerical verification with NumPy on representative parameter grid; Fourier-amplitude scan for Q2 evection-frequency match.
- `pinslot-elevation-and-differential-per-test-2026-05-XX.ndjson` — per-test outcomes: per-parameter spectrum, evection-frequency amplitude, verdict.
- `pinslot-elevation-and-differential-2026-05-XX.md` — execution report in spike-format (mimic `dynamic-laplacian-fiber-reshape-2026-05-12.md`).
- `pinslot-elevation-and-differential-2026-05-XX.png` — Fourier amplitude plots for the four compositions.

---

## Citations

- **Freeth, T., A. Bitsakis, X. Moussas, J. H. Seiradakis, A. Tselikas, H. Mangou, M. Zafeiropoulou, R. Hadland, D. Bate, A. Ramsey, M. Allen, A. Crawley, P. Hockley, T. Malzbender, D. Gelb, W. Ambrisco, M. G. Edmunds.** *Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism*, Nature **444**:587–591 (2006). DOI: [10.1038/nature05357](https://doi.org/10.1038/nature05357). Establishes the D-H1 pin-and-slot lunar mechanism with ε ≈ 0.054 and the four 50-tooth wheel structure. Used here for the single-pin-and-slot baseline. *Verification status*: cited from the project's existing `research/pin_and_slot.py` header docstring, which has been load-bearing through the antikythera notebook. PDF not re-extracted for this spike spec; flagged for re-verification per `feedback_pdf_extraction_citation_discipline.md` before execution-phase landing.
- **Carman, C., A. Thorndike, J. Evans.** *On the Pin-and-Slot Device of the Antikythera Mechanism, with a New Application to the Superior Planets*. Journal for the History of Astronomy **43**(1):93–116 (2012). Surveyed via web search 2026-05-14 (Semantic Scholar / ResearchGate / University of Puget Sound webspace). **Establishes that the literature extends single pin-and-slot to outer planets but does not compose two pin-and-slots into a differential.** Confirms no prior art for Q2. PDF not extracted; flagged for verification before execution-phase landing.
- **Brown, E. W.** *An Introductory Treatise on the Lunar Theory* (Cambridge University Press, 1896; Dover reprint 1960). Standard reference for the modern lunar Fourier coefficients including evection (`+4585″ sin(2D − ℓ)`). Cited in this spec for the target Fourier signature in Q2's falsification protocol step 2. *Verification status*: standard reference; classical formulation; cross-referenceable against modern lunar-theory texts (Meeus, Chapront).
- **Freeth, T., J. Jones.** *The Cosmos in the Antikythera Mechanism*, Institute for the Study of the Ancient World Papers **4** (2012). Cited for the consensus that the bronze antikythera does **not** model evection (the second lunar inequality is absent from the surviving and reconstructed gear-DAG). Used in Q2 archaeological framing. *Verification status*: not re-extracted; flagged.
- **Project-internal memos** (verified in this session):
    - `user_stance_fiber_as_spatially_absent_encoding.md` (2026-05-13) — fiber-as-spatially-absent stance; Q1b falsification tests this directly.
    - `user_stance_hyper_as_3d_spatial_interface.md` (2026-05-11) — two-level ontology (substrate + excitation); Q1b instantiates at constraint-geometry layer.
    - `project_mfo_sister_notebook.md` — MFO §VII.1.1 framing; Q1b is the bench-instrument candidate.
    - `feedback_no_lineage_claims_in_notebook.md` — discipline applied throughout: Freeth 2006 / Carman-Thorndike-Evans 2012 cited for specific results, not as lineage. Q2 differential composition is not framed as "natural extension of Freeth 2006"; it's an unattested mechanism that the project is independently asking the algebra about.
    - `feedback_pdf_extraction_citation_discipline.md` — three external citations above flagged for PDF re-verification before any execution-phase landing.

---

## Honest summary

**Q1a** (in-plane curved slot, sinusoidal): real new algebra; injects k-harmonics of the input frequency into the output. Tractable closed-form to leading order in slot amplitude. Single-gradient sub-case reduces to coordinate change (null). Bumps-and-ridges sub-case is discontinuity-injection, of less interest at algebra layer.

**Q1b** (out-of-plane height): the gear's rotational action cannot see `h(s)`; gear-output spectrum unchanged; a separate height-reader projects out `h`'s algebra as an independent signal. **This is the canonical fiber-as-spatially-absent construction at the constraint-geometry layer, and the falsification protocol is the cleanest bench-test for the stance the project has scoped.**

**Q2** (differential composition): Q2a parallel-averaged reduces to single pin-and-slot at first order; Q2c series cascade reduces to single pin-and-slot at first *and* second order. Q2b independent-input summed-output is the genuinely new composition. **The evection conjecture** (Q2b producing the second lunar inequality's `2D − ℓ` Fourier signature) is plausible at the order-of-magnitude / dimensional level; requires symbolic execution to confirm or falsify. **No prior literature found on differential pin-and-slot.**

**MFO connection**: Q1b gives the project a bench-scale, closed-form, fully-tractable testbed for the substrate/excitation two-level ontology. Stronger MFO-connection than most prior spikes have been able to claim.

**Open spike-cluster**: Q1a × Q2 unification (k=2 sinusoidal slot might mechanise evection on its own); height-reader algebra catalogue; gear-DAG placement for differential pin-and-slot if Q2 conjecture stands; tooth-pitch noise on differential composition.

The user identified the right axes on both questions. Math is tractable. Conductor's decision: bless / hand back / execute.

---

## Execution status: complete 2026-05-14

See findings document: [`spike_pinslot_elevation_and_differential_findings_2026-05-14.md`](spike_pinslot_elevation_and_differential_findings_2026-05-14.md).

Headline: **Q2 evection conjecture FALSIFIED.** Q2b is structurally separable (additive-in-angle), produces zero cross-terms in the 2D Fourier spectrum, cannot deliver the `2D − ℓ` mixing-frequency. Q1a k=2 single pin-slot injects a `2 θ_in` line but at the wrong frequency. The pin-and-slot family lacks a multiplicative-in-angle mixer primitive.

Other findings: spec algebra typo caught (leading expansion is `θ + ε sin θ`, not `θ + 2ε sin θ`); bronze under-models eq-of-centre by ~2× at the leading order; Q1b height-reader catalogue confirms the slot as a programmable algebraic encoder; tooth-pitch noise §11.6.6 framing needs refinement (pin-slot is NOT a frequency-band low-pass).
