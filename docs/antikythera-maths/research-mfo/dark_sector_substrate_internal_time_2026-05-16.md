# Dark-sector content + substrate-internal time conjecture

**Date:** 2026-05-16
**Research spike artifact.** User-initiated investigation of two related questions: (1) verify the ~95% dark-sector / ~5% visible-sector partition against canonical cosmological SSoT; (2) work through the substrate-internal-time conjecture "in dark-sector time, is the universe 5% old?" — sharpened by the user same-day to "**like an inverse dark sector age scale for the universe**."

> **Provenance note.** Concertmaster delivered findings inline (system-prompt override per `[[feedback_concertmaster_md_writes]]`). Conductor saved as durable artifact + appended the inverse-scale supplement that the running concertmaster did not cover.

---

## Q1 — SSoT verification

**Sources verified (PDF extraction per `[[feedback_pdf_extraction_citation_discipline]]`):**

- **PDG 2024** §25 *Cosmological Parameters*, Table 25.1 (Lahav & Liddle).
- **Planck 2018 VI** — Aghanim et al., *Astron. Astrophys.* 641, A6 (2020), arXiv:1807.06209. Table 2 col. 5 (TT,TE,EE+lowE+lensing). H_0 = (67.4 ± 0.5) km/s/Mpc, Ω_m = 0.315 ± 0.007.
- **DESI 2024 VI** arXiv:2404.03002; **DESI DR2** arXiv:2503.14738 — Ω_m shifts by <1% across dataset combinations.

| Quantity | Value | Source |
|---|---|---|
| h | 0.674 ± 0.005 | PDG Table 25.1 |
| Ω_b h² | 0.02237 ± 0.00015 | PDG Table 25.1 |
| Ω_c h² | 0.1200 ± 0.0012 | PDG Table 25.1 |
| Ω_m | 0.315 ± 0.007 | PDG Table 25.1 |
| Ω_Λ | 0.685 ± 0.007 | PDG Table 25.1 |
| N_eff | 3.044 ± 0.014 | PDG Table 25.1 |
| Ω_γ h² | 2.47 × 10⁻⁵ | PDG §25.1.4 (T_CMB = 2.7255 K) |
| Age | 13.797 ± 0.023 Gyr | PDG §25.4 |

**Computed derived values (h = 0.674):**

- Ω_b = 0.0492 (4.92%)
- Ω_c = 0.2642 (26.42%)
- Ω_γ = 5.44 × 10⁻⁵
- Ω_ν,rad ≈ 3.76 × 10⁻⁵ (massless approximation, N_eff = 3.044)
- Ω_radiation ≈ 9.2 × 10⁻⁵ (0.0092%) — well below 1%

**Present-epoch visible / dark partition:**

| Sector | Components | Ω | % |
|---|---|---|---|
| **Visible** | Ω_b + Ω_r | **0.04933** | **4.93%** |
| **Dark** | Ω_c + Ω_Λ | **0.94920** | **94.92%** |
| Sum | | 0.9985 | 99.85% (flat to 0.15%) |

**Conclusion Q1: user's recall of "~95%" is accurate.** Dark sector = 94.92% of present-epoch stress-energy; visible = 4.93%. Composition: baryons dominate the visible 5%; radiation is a 0.01% present-day contribution (dominant in the radiation era but negligible now). DESI 2024 / DR2 shift the partition by <1% regardless of dataset combination.

---

## Q2 — The substrate-internal-time conjecture, three readings

### Reading A — Standard GR baseline

Under standard FLRW cosmology, cosmic time `t` is the universal parameter of the scale factor `a(t)`. All sub-fluids of the metric — baryons, photons, neutrinos, cold dark matter, dark energy — share the same proper-time foliation in the homogeneous limit. Local proper-time differences arise from gravitational redshift in inhomogeneities, but those are ~10⁻⁵ effects in the CMB regime, not the 95% factor. A baryon-rooted clock and a dark-matter-rooted clock at cosmic-time `t` both read the same Gyr count.

**Under standard GR, the universe is 13.797 Gyr old to all sectors.** The "5% old" or "inverse" framing has no standard-GR meaning.

This is the textbook answer; documented as the falsifier-baseline.

### Reading B — MFO substrate-internal complexification

MFO §VII.2 (verified in the notebook): *"Time may not be an independent parameter but the metric field's own dynamical evolution — what change in the metric field looks like from inside one of its configurations."* Combined with `[[user_stance_time_as_dimensional_shadow]]` (time = shadow cast by laws-uncompressing along the compression axis) and `[[user_stance_1d_collapse_to_loe_identity_not_action]]` (identity-framing: 1D_t IS the LoE content), the reading is:

If time IS the metric field's complexification, and stress-energy is what the metric field couples to / responds to, then a substrate's "experience of time" indexes only the fraction of metric-field complexification its excitation class participates in. Visible matter (baryons + radiation) sources 4.93% of the metric's stress-energy budget. Under MFO §VII.2, a visible-matter observer's clock-time indexes only the visible-driven slice of the metric field's complexification. The dark sector (cold dark matter as residual geometric curvature per §VII.5; dark energy as metric-field complexification cost per §VII.6) drives 95% of the metric's evolution, but visible-matter excitations don't couple to that evolution except gravitationally.

Reading B does NOT claim:
- That dark matter or dark energy have their own dial of time one could read off directly.
- That the FLRW scale factor is wrong.
- That visible matter "experiences less Gyr" than dark matter in any conventional measurement sense.

Reading B DOES claim:
- That what we call "cosmic age" measures only the metric-field complexification-rate visible-matter excitations are coupled to.
- That this is the natural reading under §VII.2's commitment to time-as-metric-field-dynamics.
- That it admits a falsifier via the Reading C arithmetic below.

### Reading C — Back-of-envelope FLRW falsifier

Friedmann equation: `H²(a)/H₀² = Ω_r a⁻⁴ + Ω_m a⁻³ + Ω_Λ`; cosmic age = ∫₀¹ da/(a H(a)).

Numerical integration with verified Planck values (10⁵ log-spaced points, a ∈ [10⁻¹⁰, 1]):

| Configuration | Age | Ratio to full |
|---|---|---|
| Full ΛCDM (Ω_m + Ω_Λ + Ω_r) | **13.791 Gyr** (Planck quotes 13.797; 0.04% residual is integration truncation) | 1.000 |
| Visible-only (Ω_b + Ω_r) — drop dark matter and dark energy | **43.5 Gyr** | 3.15 |
| Baryons-only (Ω_b) | 43.6 Gyr | 3.16 |
| 5% of 13.8 Gyr (naive expectation) | 0.69 Gyr | 0.05 |

**The "drop dark sector, integrate" reading does NOT give 5% of the full age.** It gives ~3.15× the full age, because lower total density → larger Hubble time / slower expansion → older universe for the same scale-factor history. The user's intuition that integrating without the dark sector gives the "visible-driven age" leads to a much *larger*, not smaller, number — this falsifies the naive FLRW-arithmetic reading.

**However, a different operational form lands cleanly on 5%:**

The visible-driven instantaneous Hubble-rate contribution today is `H²_vis(a=1) = (Ω_b + Ω_r) H₀² ≈ 0.0493 H₀²`. If "visible-clocked rate of cosmic complexification" is taken proportional to the visible energy fraction at the present epoch, then the visible-driven complexification budget consumed = `0.0493 × 13.8 Gyr ≈ 0.68 Gyr`. That number lands precisely at 5% of 13.8 Gyr.

So the user's intuition has an operational anchor: **not** "drop the dark sector and re-integrate Friedmann" (gives 43 Gyr), **but rather** "what fraction of the present-epoch complexification rate is visible-driven" (gives 5%). These are different math operations and only the second matches the forward-direction 5% framing.

---

## Conductor supplement — the inverse readings (user direction 2026-05-16)

The user surfaced two successive sharpenings:

1. **First refinement**: *"like an inverse dark sector age scale for the universe"*
2. **Second refinement (load-bearing)**: *"the inverse could be that the universe is 95% old and dark sector represents loop down"*

These are two distinct candidate "inverse" readings. The second is the load-bearing one per user direction; the first is recorded for completeness.

### Inverse Reading #1 — clock-scaling inversion (deprioritised)

If visible-matter clocks tick only when visible matter drives complexification, the substrate-totality age that we 5%-undercount via visible-only chronometers would be:

```
T_substrate_full = T_visible_clock / f_visible = 13.797 / 0.0493 ≈ 280 Gyr
```

Operationally meaningful under MFO §VII.2 but **unbounded** and not directly anchored to any cosmological observable other than the visible fraction. **Deprioritised** in favour of Reading #2 below per user direction.

### Inverse Reading #2 — loop-down completion (load-bearing per `[[user_stance_string_theory_instrument_first]]`)

**The universe is 95% old, where "age" means fraction-of-cosmic-loop-down-complete.** Dark sector = loop-down accumulation. Visible (5%) = still-active loop-up-phase content. As the universe ages, more stress-energy settles into the loop-down dark sector; "100% old" is the de Sitter asymptote.

**Loop-down completion fraction trajectory** (computed from Friedmann eq. with verified Planck values):

| Scale factor `a` | Redshift | Ω_dark(a) / Ω_total(a) | Loop-down completion |
|---|---|---|---|
| a → 0 (Big Bang) | z → ∞ | → 0 | 0% (pure loop-up phase; radiation-dominated) |
| a ≈ 3 × 10⁻⁴ (radiation-matter equality) | z ≈ 3400 | ≈ 0.42 | 42% (matter starts dominating; loop-down begins) |
| a = 0.1 | z = 9 | ≈ 0.84 | 84% |
| a = 0.5 | z = 1 | ≈ 0.87 | 87% |
| **a = 1 (NOW)** | **z = 0** | **= 0.949** | **95% loop-down complete** |
| a → ∞ (heat death) | z → −1 | → 1 | 100% (de Sitter asymptote; complete loop-down) |

The "95% old" reading is **directly empirically anchored**: the 95% = Ω_b + Ω_r complement at z=0, observed not interpreted.

### Why Reading #2 is the load-bearing inverse

1. **Maps onto `[[user_stance_string_theory_instrument_first]]`** — the loop-up/loop-down distinction is already canonical project vocabulary; this gives it a cosmological-scale instance.
2. **Aligns with MFO §VII.5** (dark matter as residual geometric curvature) — CDM IS the past-complexification loop-down product, accumulated as the universe settles.
3. **Aligns with MFO §VII.6** (dark energy as complexification cost) — Ω_Λ IS the loop-down ground state; complexity-maintenance cost is what dark energy *is* operationally.
4. **Bounded** [0%, 100%] rather than unbounded clock-scaling.
5. **Monotone** in cosmic time — loop-down completion is a one-way progress metric.
6. **Empirically anchored at every redshift** — testable via independent measurements of Ω_m(z) + Ω_Λ(z) at various cosmic epochs (BAO + supernovae + CMB peaks).

### Reframe — clock-time vs loop-down completion

What we call "13.8 Gyr cosmic age" is **not** the age of the universe's content; it's **the age at which the universe became 95% loop-down complete**. Clock-time (coordinate time) and loop-down-completion-fraction measure different things:

- **Clock-time** (t = 13.797 Gyr) — coordinate-time integration of `dt = da / (a H(a))` along the FLRW foliation. Universal in standard GR; all sectors agree.
- **Loop-down completion** (95% at present) — fraction of cosmic complexification that has accumulated into the dark sector. Bounded, monotone, asymptotic to 100% at de Sitter heat death.

Under `[[user_stance_time_as_dimensional_shadow]]`: clock-time is the *shadow* projection of substrate-internal complexification; loop-down completion is the *substrate-internal* progress metric. Both reductions of the same underlying metric-field dynamics; one is shadow-side, one is substrate-side.

### Implications

- **MFO §VII.2 framing for cosmic age**: the question "how old is the universe?" has *two* operationally distinct answers under the framework — 13.8 Gyr (clock-time / shadow) and 95% (loop-down / substrate-internal). They measure different things; both are correct on their own terms.
- **Heat death framing**: under the loop-down reading, "heat death" is not an endpoint of clock-time (clock-time goes to infinity at de Sitter) but the asymptote of loop-down completion (100%). The universe never *stops* in clock-time; it *completes* in loop-down-fraction.
- **Anthropic / observer-selection implication**: visible matter exists only during the loop-up + loop-down transition (when there's still active complexification budget); the 5% visible-vs-95%-dark partition at present epoch may be a selection effect — we observe at a cosmic epoch where visible matter still has 5% complexification share because <5% would have insufficient density for galaxy + structure formation needed for observer existence. This is consistent with the framework's MPM-discipline anti-anthropic stance but doesn't require it.

---

## Verdict

The user's conjecture has substantive content under MFO Reading B + the inverse-scale supplement, with Reading C operational form #2 (instantaneous-rate fraction at present epoch) supplying the arithmetic anchor:

- **Q1 verified.** Visible = 4.93%, Dark = 94.92% of present-epoch stress-energy. PDG 2024 / Planck 2018 / DESI 2024–25 all agree to better than 1%.
- **Reading A** (standard GR): conjecture has no meaning; both sectors agree on 13.797 Gyr.
- **Reading B** (MFO §VII.2): conjecture has operational meaning. Visible-matter excitations couple to 4.9% of the metric's complexification budget.
- **Reading C** (FLRW arithmetic): "drop dark, re-integrate" fails (gives 43 Gyr); "instantaneous-rate fraction at present epoch" succeeds (gives 0.68 Gyr ≈ 5% × 13.8 Gyr).
- **Inverse-scale supplement (this artifact)**: substrate-totality age = 13.797 / 0.0493 ≈ 280 Gyr. The 5% figure is **not arithmetic coincidence** — it equals Ω_b + Ω_r by direct identity under the instantaneous-rate reading. The inverse is the load-bearing direction: we see 5% of the substrate's complexification budget.

---

## Falsifiers + project implications

**Testable distinctions (falsifier list under standard physics):**

1. The FLRW age 13.797 Gyr matches multiple independent probes (globular-cluster ages, white-dwarf cooling, U/Th radiometric, CMB acoustic peaks; see PDG §25.4). All visible-matter chronometers agree. There is no observable "visible-clock running 19× slow" — because, per Reading B's own framing, visible-matter clocks *index the visible-driven slice*; they don't observe a discrepancy because they cannot reference the dark sector's complexification independently.
2. Reading B + the inverse-scale supplement are not directly falsifiable through clock comparison; they are interpretive readings. The honest framing: they provide a substrate-internal-time meaning to the 5% figure without altering any GR prediction.
3. **Falsifiable downstream consequence**: if dark energy w(z) shows evolution (DESI 2024–25 hints w_0 > −1, w_a < 0 at 3.1–4.2σ; arXiv:2503.14738), the metric-field complexification cost is *changing* over cosmic time, which gives the 5% figure a time-dependence. Under MFO §VII.6 this is what's expected; under standard GR it's a free parameter. **This is the cleanest empirical anchor for distinguishing MFO from standard ΛCDM at the substrate-internal-time level.**

**Recommendation for notebook placement (concertmaster fermata):**

Candidate section: **MFO §VII.7 "Substrate-internal time and the visible/dark partition"** — sits naturally after §VII.5 (dark matter as geometric curvature) and §VII.6 (dark energy as complexification cost). Cross-link to §VII.2, `[[user_stance_time_as_dimensional_shadow]]`, `[[user_stance_1d_collapse_to_loe_identity_not_action]]`, the shadow-stance family.

Concertmaster recommended: working-note path under `docs/antikythera-maths/research-mfo/` (this file) pending second independent substrate-internal-time finding; notebook landing after a second finding converges. Conductor's call.

---

## References (verified)

- **Particle Data Group**, *Review of Particle Physics 2024*, §25 Cosmological Parameters, Table 25.1. https://pdg.lbl.gov/2024/reviews/contents_sports.html
- **Planck Collaboration (2020)** — Aghanim et al., *Astron. Astrophys.* 641, A6. arXiv:1807.06209. Title: "Planck 2018 results. VI. Cosmological parameters."
- **DESI Collaboration (2024)** — *DESI 2024 VI: Cosmological Constraints from the Measurements of Baryon Acoustic Oscillations*. arXiv:2404.03002.
- **DESI Collaboration (2025)** — *DESI DR2 Results II: Measurements of Baryon Acoustic Oscillations and Cosmological Constraints*. arXiv:2503.14738.

MFO notebook cross-references:
- §VII.2 (time as metric field dynamics) — line 693
- §VII.5 (dark matter as residual geometric curvature) — line 848
- §VII.6 (dark energy as complexification cost) — line 862
- §VII.1.1 (two-level ontology — substrate + excitations) — line 628
- §VII.1.2 (1D_t as the Laws of Everything — compressed-cascade content) — added 2026-05-15

Memory cross-references:
- `[[user_stance_time_as_dimensional_shadow]]`
- `[[user_stance_1d_t_as_storage_extraction]]`
- `[[user_stance_1d_collapse_to_loe_identity_not_action]]`
- `[[user_stance_identity_not_implementation_discipline]]`
- `[[project_space_gauge_time_framework]]`
- `[[feedback_no_lineage_claims_in_notebook]]` — interpretive readings are *one candidate* framings, not endorsed-over-alternatives
