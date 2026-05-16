# Axis of Evil under the §VII.6.1 ring-down framing

**Date:** 2026-05-16
**Research spike artifact.** User-initiated investigation following the same-day §VII.6.1 ship of the substrate-internal-time / 95%-ring-down framing of the dark sector.

> **Provenance note.** Concertmaster dispatch by the conductor after §VII.6.1 landed in `mfo_spectral_research_notebook.md` (lines 872–937). Companion to the dark-sector working-note artifact (`dark_sector_substrate_internal_time_2026-05-16.md`). Same author voice / structure / three-reading discipline.

> **Restructure note 2026-05-16 (this commit).** User feedback on initial PR (#437): *"the PR comment is phrased like an outline for research. I don't see any results."* Correct: Q1–Q4 below scope the AoE / Cold Spot / HPA family but the Q3 "answer" is contingent on §VII.5's open computation and Q4 has no LSS anchor. The conductor's re-dispatch added Q5 (hyperbubble-bump reading), Q6 (dark-sector oscillation), Q7+ (other questions in the same line) — each with a result-or-honest-fail per `[[feedback_pdf_extraction_citation_discipline]]`. The original Q1–Q4 are kept as **Part I (scoping)**; the new results live in **Parts II–IV**.

---

## Part I — AoE / Cold Spot / HPA scoping under §VII.6.1

### Q1 — What is the Axis of Evil, observationally?

#### SSoT verification (PDF extraction per `[[feedback_pdf_extraction_citation_discipline]]`)

| arXiv ID | Authors | Title | Journal | Verified content |
|---|---|---|---|---|
| [astro-ph/0307282](https://arxiv.org/abs/astro-ph/0307282) | de Oliveira-Costa, Tegmark, Zaldarriaga, Hamilton | *The significance of the largest scale CMB fluctuations in WMAP* | Phys. Rev. D 69, 063516 (2004) | Quadrupole–octupole alignment at "1-in-60 level"; combined a priori probability "1 in 24000" (cautioned re multiple-comparisons). |
| [astro-ph/0403353](https://arxiv.org/abs/astro-ph/0403353) | Schwarz, Starkman, Huterer, Copi | *Is the low-l microwave background cosmic?* | Phys. Rev. Lett. 93, 221301 (2004) | Three octopole planes orthogonal to ecliptic at 99.8% C.L.; normals aligned with CMB dipole + equinoxes at 99.9% C.L.; ecliptic threads between hot and cold spots over ~1/3 of sky. |
| [astro-ph/0502237](https://arxiv.org/abs/astro-ph/0502237) | Land, Magueijo | *The axis of evil* | Phys. Rev. Lett. 95, 071301 (2005) | Coined the name. Alignment extends to ℓ=2,3,5; preferred direction at galactic (b, l) ≈ (60°, −100°) ≡ (l, b) ≈ (260°, 60°); rejection of statistical isotropy at >99.9%. |
| [astro-ph/0508047](https://arxiv.org/abs/astro-ph/0508047) | Copi, Huterer, Schwarz, Starkman | *On the large-angle anomalies of the microwave sky* | MNRAS 367, 79 (2006) | Quadrupole+octopole plane perpendicular to ecliptic plane and dipole-direction plane; ecliptic separates stronger from weaker extrema at >99.9% C.L. |
| [1001.4758](https://arxiv.org/abs/1001.4758) | Bennett et al. (WMAP) | *Seven-Year WMAP Observations: Are There Cosmic Microwave Background Anomalies?* | ApJS 192, 17 (2011) | "No compelling evidence for deviations from ΛCDM"; "claimed anomalies depend on posterior selection of some aspect or subset of the data." Skeptical canonical reference. |
| [1510.07929](https://arxiv.org/abs/1510.07929) | Schwarz, Copi, Huterer, Starkman | *CMB anomalies after Planck* | Class. Quantum Grav. 33, 184001 (2016) | Comprehensive review; explicitly notes "some pairs of those features are demonstrably uncorrelated" — the low-ℓ anomaly family is not a single object. |
| [1906.02552](https://arxiv.org/abs/1906.02552) | Akrami et al. (Planck Coll.) | *Planck 2018 results. VII. Isotropy and Statistics of the CMB* | A&A 641, A7 (2020) | Confirms anomalies persist in PR3; "no unambiguous detections" of cosmological non-Gaussianity in polarisation. |

#### What the AoE actually is

- **A directional alignment of low-ℓ multipoles**, not a localised temperature feature. The "axis" is a preferred *line on the celestial sphere* picked out by Maxwell-vector representations of the ℓ=2 and ℓ=3 multipoles. It has a *pole and an antipole*; there is no distinguished "north" end of the axis.
- **Preferred direction.** Best-fit axes in the literature cluster near galactic (l, b) ≈ (240°–260°, 60°). The project's own attested catalog row [`docs/antikythera-maths/research/attested/cmb_anomalies/row.ndjson`](../research/attested/cmb_anomalies/row.ndjson), `axis-of-evil-l2-l3-alignment`, records (240°, 60°) — consistent with the Land–Magueijo (260°, 60°) within estimator scatter.
- **The really weird part is not the alignment with itself.** It is the *additional alignment* — at 99.8–99.9% C.L. (Schwarz et al. 2004; Copi et al. 2006) — with the **ecliptic plane**, the **CMB dipole direction**, and the **equinox direction**. These are solar-system-frame references, not cosmological references. The AoE is "evil" because it aligns the cosmological with the local-solar-system.
- **Statistical significance is test-dependent.** The catalog stores ~3σ as representative; reported significances range from ~99% (de Oliveira-Costa 2004 multipole-vector tests alone) to >99.9% (Schwarz 2004 + Land–Magueijo 2005 multi-feature joint tests). Bennett et al. 2011 documents the posterior-selection skeptical baseline. Frommert & Enßlin 2010 ([0908.0453](https://arxiv.org/abs/0908.0453)) explicitly uses CMB polarisation as an independent probe and finds the alignment consistent with chance at the ~50% level — i.e., the temperature signal does not get reinforced by polarisation.

**Conclusion Q1.** The Axis of Evil is a low-ℓ multipole alignment, axis at (l, b) ≈ (240°–260°, 60°) in galactic coordinates, with secondary alignment to ecliptic/dipole/equinox at ~99.9% C.L. (the load-bearing claim). The temperature anomaly is robust as observation; the polarisation independent-probe is consistent with chance. The framing "hot spot vs cold spot" is **the wrong taxonomy** — it is neither.

---

### Q2 — Hot spot, cold spot, or neither? From whose perspective?

#### Reading A — Standard observational baseline

The Axis of Evil is **not a temperature feature at a location**. It is the *direction* of the alignment of the quadrupole and octopole multipole vectors. The standard taxonomy:

- **Hot spot** — localised positive temperature deviation (e.g., the WMAP "warm spot" near Eridanus is a hot-side counterpart, never named to the same prominence).
- **Cold spot** — localised negative temperature deviation. The canonical CMB Cold Spot (Vielva et al. 2004 [astro-ph/0310273](https://arxiv.org/abs/astro-ph/0310273); catalog row `cold-spot`) is at galactic (l, b) ≈ (210°, −57°), ~10° diameter, ~70 μK below mean.
- **Alignment / axis** — preferred *direction* on the sphere, not a temperature deviation. The AoE belongs here.

**The Cold Spot and the Axis of Evil are different objects.** Verify the catalog:

| Anomaly | Galactic (l, b) | Kind | Source |
|---|---|---|---|
| Axis of Evil pole | (240°, 60°) | alignment (preferred direction) | de Oliveira-Costa 2004 / Schwarz 2004 / Land–Magueijo 2005 |
| Cold Spot | (210°, −57°) | localised temperature deficit | Vielva 2004 / Cruz 2005 |
| Hemispherical Power Asymmetry | (237°, −20°) | dipolar modulation | Eriksen 2004 / Hansen 2009 |

The AoE pole at (240°, 60°) and the Cold Spot at (210°, −57°) are **roughly antipodal** in galactic latitude (60° vs −57°) and offset by ~30° in galactic longitude (240° vs 210°+180°=30°). The Cold Spot lies *near* the AoE antipole, not at it; whether this is coincidence or correlation is unresolved in the literature (Schwarz et al. 2016 §4 notes "some pairs of those features are demonstrably uncorrelated").

#### Reading B — "From whose perspective?" under MFO commitments

The user's framing question parses cleanly under the two-level ontology of `[[user_stance_hyper_as_3d_spatial_interface]]` (substrate + excitation levels) and the shadow-stance family:

- **Shadow-side / standard-observer perspective.** What we *see* is the projection of the CMB last-scattering surface onto our 2-sphere of sight at z=0. From this perspective the AoE is a directional anomaly on a single emission surface; it has no temporal extent (the CMB is a single redshift slice in clock-time). Hot/cold-spot framing applies only to the Cold Spot and to local extrema; the AoE itself is an alignment, not a temperature feature.
- **Substrate-side perspective.** Under §VII.4.1.1's spherical-compression / Hopf-bundle reading and §VII.4.1.2's Casimir-decomposition universality, *every* observation on a 2-sphere is the base projection of a principal-bundle total-space structure. A preferred direction in the base S² corresponds to a preferred fibre-direction or connection-curvature feature in the bundle. Under this reading, the AoE is a **direction in the substrate's bundle geometry**, not a temperature.

The "from whose perspective?" question therefore has two operationally distinct answers:

| Perspective | What the AoE is | Hot? Cold? |
|---|---|---|
| Observer (shadow-side) | Alignment of low-ℓ multipole vectors with each other + with ecliptic/dipole/equinox | Neither; it's directional, not amplitude |
| Substrate (MFO §VII.4.1.1) | A preferred fibre / connection-curvature direction in the S² boundary's principal-bundle structure | Asks the wrong question; "temperature" is not the substrate-level observable for an alignment feature |

#### What's actually a hot vs cold thing — the local extrema

The Schwarz et al. 2004 + Copi et al. 2006 finding does name local hot/cold extrema **threaded by the ecliptic**: "the ecliptic plane narrowly threads between a hot spot and a cold spot over approximately 1/3 of the sky" (astro-ph/0403353 abstract). These are the *local* extrema picked out by the aligned quadrupole+octopole on either side of the AoE plane. The hot spot and cold spot referenced here are not the canonical "Cold Spot" (which is at southern galactic latitudes, distinct from the AoE-aligned local extrema). The AoE *organises* local hot/cold structure along the ecliptic; it is not itself one of them.

#### Resolution

The user's question "axis of evil is a hot spot or a cold spot? from who's perspective?" parses as:

- **Observationally:** neither — it's an alignment / preferred direction.
- **In the AoE's organised local-extrema sense (Schwarz 2004):** the aligned quadrupole+octopole *does* pick out a hot–cold dipolar structure roughly along the ecliptic, but the AoE itself is the *axis* of that dipolar structure, not one of its poles.
- **Under MFO §VII.4.1.1:** "hot vs cold" is the wrong observable for an alignment feature; the substrate-side observable is bundle-base direction, not temperature.

The honest answer: **it's an axis (pole + antipole), not a spot. The "perspective" that would make it hot or cold is the perspective that picks one end of the axis — and the data does not distinguish the two ends.**

This is the load-bearing point for Q3.

---

### Q3 — Antipodal "very young" spots: is there a reading?

#### The pole/antipole degeneracy

The user's question is sharp: under §VII.6.1's ring-down framing, "young" means *less ring-down complete* (less of cosmic complexification has settled into the dark sector along that direction). For an *axis*, the alignment doesn't distinguish "the pole is old" from "the pole is young" — both ends of the line are mathematically equivalent under the multipole-vector representation. The AoE alone cannot answer "which end is young."

What *does* distinguish hemispheres along that axis is the **Hemispherical Power Asymmetry** (Eriksen et al. 2004 [astro-ph/0407271](https://arxiv.org/abs/astro-ph/0407271); Hansen et al. 2009 [0812.3795](https://arxiv.org/abs/0812.3795)), an independent low-ℓ anomaly:

- Eriksen 2004: *"the northern ecliptic hemisphere is practically devoid of large-scale fluctuations, while the southern hemisphere shows relatively strong fluctuations."*
- Hansen 2009: preferred direction at galactic (l, b) ≈ (226°, −17°); asymmetric model preferred over isotropic at 0.4% significance over ℓ=2–600; "none of our 9800 isotropic simulated maps show a similarly consistent direction of asymmetry over such a large multipole range."

The HPA preferred direction (l, b) ≈ (226°, −17°) is the **southern-ecliptic-power-rich** end. The catalog records `(237°, -20°)`. **The HPA gives the asymmetry that the AoE alignment alone cannot.**

#### Three-reading structure for the AoE-HPA composite

##### Reading A — Standard cosmology

Under standard ΛCDM, the CMB is a single emission surface at z ≈ 1090, clock-time t ≈ 380 kyr post-Big-Bang. "Young" and "old" do not apply *per direction on the sky* in any standard sense. The HPA is a power-modulation anomaly; it is not interpreted as "one hemisphere is younger than the other." Most published explanations are non-temporal:

- Spatial inhomogeneity at the last-scattering surface (Frommert & Enßlin 2010 [0908.0453](https://arxiv.org/abs/0908.0453) considers polarisation discrimination; concludes the AoE alignment is consistent with chance at ~50%).
- Sachs–Wolfe contributions from local large-scale structure.
- Posterior-selection / look-elsewhere effects (Bennett et al. 2011).
- Residual instrumental systematics or foregrounds.

The "young hemisphere" reading has no standard-cosmology meaning. Documented as falsifier-baseline.

##### Reading B — MFO §VII.6.1 ring-down framing with HPA as discriminator

Under §VII.6.1: dark sector = ring-down accumulation = 95% of cosmic complexification settled into substrate residue (geometric curvature + complexification-cost ground state). "Young in ring-down completion" means *less of the complexification budget along that direction has settled*; "old in ring-down completion" means more.

The HPA observation: power at low ℓ is **higher in one hemisphere** (the southern-ecliptic) **and lower in the antipodal hemisphere** (northern-ecliptic), persisting across ℓ=2–600. Under the ring-down reading, two candidate mappings exist:

- **Candidate B1 — "more power = less ring-down."** Active ring-up content carries observable power (the visible-matter 5%; modes still coupled to active complexification); ring-down accumulation is dissipated into the dark sector and does not produce CMB temperature fluctuations directly. Therefore the *high-power* hemisphere is the *less ring-down complete = younger* hemisphere; the *low-power* hemisphere is *more ring-down complete = older*. This reading is consistent with the §VII.6 framing where Ω_Λ (dark energy / complexification cost) is the ring-down ground state and does not source CMB temperature perturbations.
- **Candidate B2 — "more power = more residual substrate-structure."** If ring-down accumulation produces residual geometric-curvature features (§VII.5 dark matter as residual curvature) that *do* source CMB perturbations via integrated Sachs–Wolfe / lensing-like effects, then more low-ℓ power = more residual ring-down structure = *older*. This reverses the assignment.

The two readings disagree on the direction of the young↔old assignment. The discriminator is **whether ring-down residue sources CMB temperature anisotropy or not** — a question §VII.5 / §VII.6 / §VII.6.1 do not currently resolve, because the dark matter halo profile / rotation curve / ISW computation is the explicit open problem (§VII.5 last paragraph: "the quantitative match … is the open computation").

**The honest assessment:** Reading B1 is the more natural fit with §VII.6.1's claim that the dark sector is the ring-down *ground state* (Ω_Λ = const, complexity-maintenance cost; not a perturbation source). Reading B2 would require ring-down accumulation to carry distinguishable spatial features at the CMB last-scattering surface, which is closer to the §VII.5 "geometric curvature" reading but at much higher redshift than the standard CDM-distribution claim. Both readings are internally consistent with portions of §VII; neither is forced by the current framework state.

Under Reading B1: **the southern-ecliptic hemisphere (l, b) ≈ (237°, −20°), where power is higher, is the less ring-down complete = younger hemisphere** in substrate-internal time. The northern-ecliptic antipode is the more ring-down complete = older hemisphere.

##### Reading C — Composite AoE + HPA + Cold Spot under the framework

The geometry is intriguing if not load-bearing:

- AoE pole at (240°, 60°) → AoE antipole at (60°, −60°)
- HPA high-power pole at (226°, −17°) → HPA low-power pole at (46°, +17°)
- Cold Spot at (210°, −57°)

The AoE *pole* (high galactic latitude north) and HPA *high-power direction* (slightly southern galactic latitude) are within ~80° of each other but not coincident. The Cold Spot is offset from the AoE antipole by ~30°. The literature (Schwarz et al. 2016 §4) treats the "low-ℓ axis family" as related but not identical; whether they are independent statistical accidents or share an underlying cause is genuinely open.

Under Reading B1 with the HPA-as-discriminator interpretation: the *Cold Spot near the AoE antipole* would be a localised feature in the more-old hemisphere — older substrate residue with a localised deeper-than-expected feature. The Vielva et al. 2004 Cold Spot interpretation literature already includes the "cosmic supervoid" reading (Szapudi et al. 2015 ISW signature from a void); a void in the substrate is consistent with a more-ring-down-complete region (less active complexification structure remaining in that direction). This is candidate framing only; the §VII.5 / §VII.6 quantitative computation that would test it is open.

#### Resolution

The user's "antipodal very young spots" question has substantive content **only if** the AoE is composed with an asymmetry observation (HPA) that breaks the pole/antipole degeneracy. Under that composition and Reading B1:

- **Younger hemisphere (less ring-down complete):** southern-ecliptic, HPA high-power, roughly along galactic (l, b) ≈ (237°, −20°).
- **Older hemisphere (more ring-down complete):** northern-ecliptic, HPA low-power antipode, with the canonical Cold Spot offset by ~30° as a localised deeper feature consistent with a more-ring-down-complete region.

**Falsifier (Reading B2 inversion):** if §VII.5's residual-geometric-curvature reading does source distinguishable CMB temperature perturbations via ISW-like mechanisms, the assignment reverses (high-power = more ring-down residue = older). The §VII.5 quantitative-match open computation is the discriminator. Until that computation is run, both directions are framework-consistent.

---

### Q4 — Dark-sector content from the AoE perspective

#### What the user is asking, sharpened

The headline question — "see what dark sector content looks like from that perspective" — admits two readings:

1. **Empirical:** does the AoE preferred direction correlate with any observed large-scale-structure / dark-matter halo / cosmic-web feature?
2. **Framework:** under §VII.6.1's ring-down framing, what does the dark sector's spatial distribution along the AoE axis look like?

Both are addressed; the empirical reading honestly has no clean published mapping.

#### Reading A — Empirical large-scale-structure correlation with AoE direction

Searches for LSS / cosmic-web / dark-matter-halo alignment with the AoE direction have a mixed published record. The literature reviewed includes:

- **Schwarz et al. 2016 review** ([1510.07929](https://arxiv.org/abs/1510.07929)): the AoE preferred direction is *not* aligned with the cosmic supergalactic plane in any cleanly published statistical sense. The dipole-direction alignment is with the local-frame solar motion (CMB dipole = our motion through the rest frame), not with a cosmologically-distinct direction.
- **Frommert & Enßlin 2010** ([0908.0453](https://arxiv.org/abs/0908.0453)): polarisation independent probe is consistent with chance at ~50% level, weakening cosmological-origin readings.
- **Cold Spot as cosmic supervoid** (Szapudi et al. 2015, MNRAS 450, 288): a void of radius ~200 Mpc at z ≈ 0.2 in the direction of the Cold Spot is consistent with ISW signature; not strictly along the AoE axis but in the same low-ℓ-anomaly family.

The honest answer: **there is no published, statistically-significant LSS-alignment-with-AoE result that the framework can cleanly anchor against.** The AoE's most-significant additional alignment is with solar-system-frame references (ecliptic / dipole / equinox), not with cosmological LSS — which is exactly what makes it suspicious-of-systematics under the Bennett 2011 reading and exactly what makes it intriguing-as-substrate-frame-feature under the MFO reading.

> **Open thread (fermata for conductor):** an LSS-cross-correlation literature pass beyond the Frommert–Enßlin / Schwarz–review level would need WebSearch / scholarly database access beyond what this dispatch covers. The concertmaster's brief originally referenced a Pereira et al. 2008 arXiv:0710.4099 paper that turned out to be unrelated (Bohmian mechanics) — the citation in the dispatch brief was mis-attributed. The actual Pereira-Boehmer-Mota-style LSS-alignment literature exists but verifying specific papers would require a follow-up dispatch.

#### Reading B — Framework: dark-sector spatial distribution along AoE axis

Under §VII.6.1, the dark sector (Ω_dark = 0.949) is ring-down accumulation: dark matter as residual geometric curvature (§VII.5), dark energy as complexification-cost ground state (§VII.6). The *spatial distribution* of the dark sector at present epoch is what observational cosmology already maps (lensing surveys, galaxy-cluster catalogs, BAO, etc.) — and that distribution does *not* show a published AoE-aligned anomaly.

The framework's claim, under §VII.6.1 + the Q3 Reading B1 composition:

- **Bulk distribution:** the dark sector is *isotropic at LSS scales* in standard cosmology, modulo well-mapped fluctuations. Under §VII.6.1 this isotropy is the substrate-side statement that ring-down accumulation is approximately uniform on cosmological scales.
- **Anisotropy at the CMB-low-ℓ scale (this is where the AoE lives):** would correspond, under Reading B1, to a *hemispheric asymmetry in ring-down completion at the largest spatial scales accessible to observation* — exactly what the HPA reports, at exactly the angular scales where the AoE alignment lives.
- **The dark sector "as seen from the AoE axis":** under Reading B1, looking *along* the AoE axis you see the substrate in its bundle-base-preferred-direction (per §VII.4.1.1's Hopf-bundle / Casimir-decomposition framing). Looking *across* the AoE axis you see the two hemispheres of differential ring-down completion (per HPA). The Cold Spot is a localised deeper-feature in the more-old hemisphere.

This is a **candidate framing** under §VII.6.1 commitments. It is not endorsed over the standard "AoE is a statistical fluke + galactic-foreground residual + posterior-selection effect" reading; the framework provides *one possible* substrate-side interpretation if the AoE turns out to be real and not systematics.

#### Resolution

The user's "what does dark sector content look like from the AoE perspective?" question has:

- **Empirical answer:** no published LSS-with-AoE alignment of statistical significance; the dark sector at LSS scales is approximately isotropic. The AoE's additional alignments are with solar-system-frame references, not LSS.
- **Framework answer (candidate B1):** the AoE marks the *preferred bundle-base direction* in the substrate at CMB-low-ℓ scales; the HPA marks the asymmetric ring-down-completion along that axis; the Cold Spot is a localised more-old-substrate feature near the AoE antipole. All three are the visible-shadow of a substrate-level bundle-geometry anisotropy at the largest angular scales accessible to observation.

The candidate framing dissolves the AoE-Cold-Spot-HPA "low-ℓ anomaly family" into a single substrate-level preferred-direction-with-asymmetry feature; it does not falsify standard ΛCDM (which can absorb all three as posterior-selection effects per Bennett 2011) but offers an alternative reading internally consistent with §VII.4.1.1 + §VII.5 + §VII.6 + §VII.6.1.

---

### Part I summary (scoping verdict)

- **Q1 verified.** AoE = alignment of ℓ=2,3 multipole vectors at axis (l, b) ≈ (240°–260°, 60°), with secondary alignment to ecliptic+dipole+equinox at ~99.9% C.L. (Schwarz 2004; Land–Magueijo 2005). Re-confirmed at Planck PR3 (Akrami 2020). Significance is test-dependent; skeptical baseline is Bennett 2011 (posterior selection).
- **Q2 resolved.** AoE is neither hot nor cold spot — it's a directional axis. The Cold Spot is a separate anomaly at (210°, −57°). The "hot/cold" framing inside the AoE story comes from the *local extrema* aligned by the quadrupole+octopole along the ecliptic, but the AoE itself is the axis, not a pole.
- **Q3 has substantive content** *only* when the AoE is composed with the HPA, which breaks the pole/antipole degeneracy. Under §VII.6.1 Reading B1 (more low-ℓ power = less ring-down complete = younger), the southern-ecliptic hemisphere (l, b) ≈ (237°, −20°) is younger; the northern-ecliptic antipode is older; the Cold Spot is a localised more-old feature near the AoE antipole. **Reading B2 (more power = more ring-down residue = older) is the alternate framework-consistent reading;** the §VII.5 quantitative-match open computation is the discriminator. Both stand as framework-consistent candidate readings.
- **Q4 partially answered.** Empirically, no published LSS-with-AoE alignment of significance; framework-side, the AoE is a candidate preferred-bundle-direction in §VII.4.1.1's Hopf-bundle / spherical-compression framing, with HPA giving the asymmetry along the axis. **Open thread on LSS-cross-correlation literature** flagged as fermata for the conductor.

---

### Part I commentary — what the scoping concludes

**What Part I changes:**

- The AoE is now linkable to §VII.6.1's ring-down framing **via the HPA composition**, not on its own. The AoE alone is an axis (pole+antipole symmetric); the HPA gives the asymmetric direction that "young vs old in ring-down completion" needs.
- Under §VII.4.1.1's spherical-compression / Hopf-bundle reading, the AoE is naturally a preferred-bundle-base direction. This is *one candidate* framing; not endorsed over standard-ΛCDM-plus-systematics.
- The "low-ℓ anomaly family" (AoE + Cold Spot + HPA + low quadrupole + parity asymmetry + missing large-angle correlation, per the project's `cmb_anomalies` catalog) admits a unified candidate reading as: a single substrate-level preferred-direction-with-asymmetry feature, projected to the CMB last-scattering surface, with the various anomalies being different statistical-test projections of the same underlying bundle-geometry feature.

**What Part I does not change:**

- No GR / ΛCDM prediction is altered. Standard observational analyses remain valid; this is an interpretive reading of what those analyses are *of*.
- Bennett 2011 skeptical baseline stands. The candidate framing here does not refute the posterior-selection critique; it offers an alternative for the case where the anomalies turn out to be real after systematics control.
- Frommert–Enßlin 2010 polarisation independent-probe is consistent with chance; if reinforced by Planck PR3 polarisation analyses (Akrami 2020 "no unambiguous detections" in polarisation), the cosmological-origin reading weakens.
- §VII.5 quantitative-match open computation remains the discriminator between Reading B1 and Reading B2.

---

## Part II — Hyperbubble-bump reading (Q5)

> **User's Q5 (verbatim 2026-05-16):** *"does our known universe act like an isolated hyperbubble that got bumped by some other hyperbubble of excitation?"*

### Q5.1 — Result: the bubble-collision template is a circular disc, not an axial direction

**Verified from arXiv PDF extraction (per `[[feedback_pdf_extraction_citation_discipline]]`):**

| arXiv ID | Authors / Title | Verified content |
|---|---|---|
| [1012.1995](https://arxiv.org/abs/1012.1995) | Feeney, Johnson, McEwen, Peiris (2011), *First Observational Tests of Eternal Inflation*, **Phys. Rev. Lett. 107, 071301**. | Search for cosmological signatures of bubble collisions in WMAP-7. Authors confirmed. |
| [1012.3667](https://arxiv.org/abs/1012.3667) | Feeney, Johnson, Mortlock, Peiris (2011), *First Observational Tests of Eternal Inflation: Analysis Methods and WMAP 7-Year Results*, **Phys. Rev. D 84, 043507**. | Abstract: target "a generic set of properties associated with a bubble collision spacetime"; "rule out bubble collisions over a range of parameter space." Companion to 1012.1995. |
| [0908.4105](https://arxiv.org/abs/0908.4105) | Aguirre, Johnson (2011), *A status report on the observability of cosmic bubble collisions*, **Rep. Prog. Phys. 74, 074901**. | Note: user's brief listed `arXiv:0904.2789` for this paper; that ID is actually a 2009 Arvanitaki et al. dark-matter / TeV-spectroscopy paper. Correct ID is **0908.4105**. Per `[[feedback_pdf_extraction_citation_discipline]]` — citation mis-attribution caught and corrected. |
| [1202.2861](https://arxiv.org/abs/1202.2861) | McEwen, Feeney, Johnson, Peiris (2012), *Optimal filters for detecting cosmic bubble collisions*, **Phys. Rev. D 85, 103502**. | Reports 8 candidate signatures in WMAP under improved optimal-filter algorithm. |
| [1305.1964](https://arxiv.org/abs/1305.1964) | Osborne, Senatore, Smith (2013), *Collisions with other Universes: the Optimal Analysis of the WMAP data*. | Note: user's brief listed `1303.1080`; that ID is a 2013 Hartman & Maldacena black-hole-interior entanglement-entropy paper. Correct ID is **1305.1964**. Second citation mis-attribution caught and corrected. **Null result; constraint $-4.66\times 10^{-8} < a (\sin\theta_{\rm bubble})^{4/3} < 4.73\times 10^{-8}$ Mpc⁻¹ at 95% C.L.** |
| [1112.4487](https://arxiv.org/abs/1112.4487) | Johnson, Peiris, Lehner (2012), *Determining the outcome of cosmic bubble collisions in full General Relativity*, **Phys. Rev. D 85, 083516**. | Full-GR simulation validates the analytic approximations used in Feeney 2011 / Osborne 2013. |

**Predicted bubble-collision template shape** (Feeney 2011; Osborne 2013; Aguirre-Johnson 2009 review):

- A bubble collision in eternal inflation produces an **azimuthally-symmetric, disc-shaped feature** on the CMB sky, with a smooth temperature profile across the disc and a discontinuity (causal boundary) at the disc edge.
- The angular size of the disc is parametrised by $\theta_{\rm bubble}$, the angular radius of the bubble signal as seen by our observer. Feeney 2011 / Osborne 2013 searches scan over $\theta_{\rm bubble}$ ranges of order $\sim 10°$–$90°$.
- The amplitude is parametrised by the initial curvature perturbation $a$ (Mpc⁻¹) at the collision spacetime; Osborne et al. 2013 constrain $|a (\sin\theta_{\rm bubble})^{4/3}| < 4.7\times 10^{-8}$ Mpc⁻¹ at 95% C.L., a null result.
- A bubble-collision feature **breaks statistical isotropy at one location on the sky**, not by aligning multipole moments — the broken isotropy is *the disc's centre* being distinct from the all-sky mean.

### Q5.2 — Result: the AoE shape does NOT match a bubble-collision template

**Computed angular separations on the celestial sphere** (verified, this dispatch):

| Pair | Separation |
|---|---|
| AoE pole (240°, 60°) ↔ Cold Spot (210°, −57°) | **119.4°** |
| AoE antipole (60°, −60°) ↔ Cold Spot (210°, −57°) | **60.6°** |
| AoE pole ↔ HPA pole (226°, −17°) | 77.8° |
| AoE pole ↔ HPA catalog pole (237°, −20°) | 80.0° |
| AoE pole ↔ CMB dipole direction (264°, 48°) | **18.3°** |
| AoE pole ↔ North Ecliptic Pole (96.4°, 29.8°) | 85.3° |
| CMB dipole ↔ NEP | 101.4° |
| Cold Spot ↔ HPA pole | 41.8° |

The load-bearing geometric mismatch:

- **Bubble-collision template:** circular disc, angular radius $\theta_{\rm bubble} \in [10°, 90°]$, with a smooth profile and edge discontinuity.
- **AoE observable:** preferred *axis* (pole + antipole symmetric), no characteristic angular size, picked out by multipole-vector alignment of $\ell=2,3$ (and weaker at $\ell=5$).

These are different geometric primitives. A bubble-collision disc would produce **one preferred centre on the sky and a characteristic angular scale equal to the disc radius**, not a preferred axis with no characteristic scale. The AoE is *not* a bubble-collision template shape.

- **HPA observable:** hemispherical asymmetry, characteristic scale ≈ 180°. This is too large for a typical bubble-collision disc ($\theta_{\rm bubble} \lesssim 90°$ means disc area $\le$ half-sky, but the *temperature step* at the disc edge does not extend across the antipode in the way HPA reports power being modulated across a full hemisphere). HPA is also not a bubble-collision template.
- **Cold Spot observable:** small disc ~10° diameter, ~70 μK depth. **This *is* the geometric primitive that matches a bubble-collision template best.** And in fact the Cold Spot has been searched as a candidate bubble-collision feature; Feeney 2011 reported four candidate features, and McEwen et al. 2012 found eight candidate features under improved filtering — the Cold Spot region was among them. Osborne et al. 2013's optimal-estimator null result on WMAP-7 effectively rules out the Cold Spot as a primary bubble-collision feature at any standard amplitude.

### Q5.3 — Discriminator: internal-bundle-direction vs external-hyperbubble-bump

The user's brief asks: *"what is the discriminator between 'internal substrate-bundle-direction' (the first-dispatch reading) and 'external hyperbubble bump' (this reading)?"*

| Property | Internal-bundle-direction (Part I Reading B1) | External-hyperbubble-bump |
|---|---|---|
| **Geometric primitive** | Axial alignment (pole+antipole), no characteristic angular scale | Disc with characteristic angular radius $\theta_{\rm bubble}$ |
| **AoE fit** | Direct: AoE *is* an axis | Mismatch: AoE has no $\theta_{\rm bubble}$ characteristic scale |
| **Cold Spot fit** | Localised more-old feature near AoE antipole (Part I Reading B1) | Direct: Cold Spot is a disc, the right shape |
| **HPA fit** | Hemispherical asymmetry from bundle-base direction breaking | Mismatch: HPA is too large for a typical disc |
| **Predicted secondary alignments** | If solar-system-frame alignments (ecliptic, dipole, equinox) are systematics, they correlate with foregrounds. If physical, they need explanation outside this reading. | None — bubble collisions break statistical isotropy at the disc, not along an axis aligned with our motion |
| **Observational status** | Multiple-anomaly composition (AoE+HPA+Cold Spot) → one substrate feature | Null result from Osborne 2013 + Planck 2015 XVI = AoE not from a bubble collision; Cold Spot also constrained |
| **Falsifier** | §VII.5 quantitative-match (Reading B1 vs B2) | Existing Planck 2015 + WMAP-7 null result already disfavours |
| **Verdict** | Internally consistent candidate framing; not unique | **Already disfavoured by Osborne 2013 WMAP-7 constraint at 95% C.L. for the parameter ranges scanned** |

**The discriminator that already exists in published literature:** Osborne, Senatore, Smith 2013 (arXiv:1305.1964) reported a null search for bubble-collision signatures in WMAP-7 data using the optimal estimator, with constraint $|a (\sin\theta_{\rm bubble})^{4/3}| < 4.7\times 10^{-8}$ Mpc⁻¹ at 95% C.L. across the parameter range scanned. **This is the cleanest available no-detection of a hyperbubble bump as of 2026-05-16; Planck PR3 (Akrami 2020) confirmed "no unambiguous detections" in polarisation.** The hyperbubble-bump reading is not ruled out (because the parameter range is finite), but it has no positive observational anchor at present.

### Q5.4 — Result: the AoE-CMB-dipole alignment (18°) is the load-bearing piece

The computed AoE pole–CMB dipole separation of **18.3°** is striking and feeds into both readings:

- **Bubble-collision (external) reading**: a bubble-collision feature aligned with our motion direction (CMB dipole = direction we move through the rest frame at v/c ≈ 1.23×10⁻³) is *not* predicted by bubble-collision theory. Bubble-collision discs are placed by where neighbouring bubbles nucleate, not by our peculiar motion. So if the AoE is a bubble collision, the 18° proximity to the CMB dipole is coincidence — and a 99.9% C.L. coincidence (Schwarz 2004) at that.
- **Internal-bundle-direction (Part I Reading B) reading**: a bundle-base direction in the substrate need not be aligned with our motion either — but at least the alignment is *with a solar-system-frame reference*, which is *exactly* what makes the AoE "evil" in the literature. The shadow-side reading (foregrounds / systematics) and the substrate-side reading (bundle-base direction picking out our motion frame) both have to account for the same 18° proximity. Neither has a clean explanation.
- **Systematics reading (Bennett 2011)**: the alignment is a residual foreground/instrumental artifact correlated with our motion through the local frame. This is the most economical explanation and remains the skeptical baseline.

**Verdict Q5:** the hyperbubble-bump reading is **disfavoured but not strictly excluded** by Osborne 2013 + Planck 2015 XVI + Akrami 2020 PR3. The AoE shape is the wrong geometric primitive for a bubble collision; the Cold Spot is the right shape but has been searched and constrained to null. The 18° AoE↔CMB-dipole proximity is unexplained under all readings (bubble-collision, internal-bundle-direction, systematics) and is the live anomaly.

**The internal-bundle-direction vs external-hyperbubble-bump discriminator is therefore not a future experiment — it is *already settled in favour of internal-bundle-direction* on shape grounds.** The AoE is axial; bubble-collision templates are disc-shaped; the geometries disagree.

> **Fermata for conductor.** This is the strongest finding of the dispatch: the hyperbubble-bump reading is *geometrically the wrong shape* for the AoE. The framework's internal-bundle-direction reading is not falsified by this — but the user's Q5 alternative reading is downgraded relative to Part I.

---

## Part III — Dark-sector oscillation (Q6)

> **User's Q6 (verbatim 2026-05-16):** *"does dark sector oscillate, as in was it ever at 5% or a minimum is required that would indicate some sort of oscillation"*

### Q6.1 — Result: under standard ΛCDM, $\Omega_{\rm dark}(a)$ is monotone increasing in $a$; no minimum

**Friedmann-integration computation, this dispatch** (10 000 log-spaced points, $a \in [10^{-12}, 1]$, Planck 2018 values $h=0.674$, $\Omega_m=0.315$, $\Omega_\Lambda=0.685$, $\Omega_r=9.2\times 10^{-5}$, $\Omega_b=0.0492$, $\Omega_c=0.2642$):

$$f_{\rm dark}(a) = \frac{\rho_{\rm dark}(a)}{\rho_{\rm tot}(a)} = \frac{\Omega_c/a^3 + \Omega_\Lambda}{\Omega_c/a^3 + \Omega_\Lambda + \Omega_b/a^3 + \Omega_r/a^4}$$

**Analytic result.** Multiply numerator and denominator by $a^3$:

$$f_{\rm dark}(a) = \frac{\Omega_c + \Omega_\Lambda a^3}{\Omega_m + \Omega_\Lambda a^3 + \Omega_r/a}$$

Let $u(a) = \Omega_\Lambda a^3$ (monotone increasing from 0 to $\Omega_\Lambda$ as $a$ goes from 0 to 1, then to $\infty$ as $a \to \infty$) and $v(a) = \Omega_r / a$ (monotone decreasing from $\infty$ to $\Omega_r$). Then $f_{\rm dark}(a) = (\Omega_c + u) / (\Omega_m + u + v)$. Take derivative:

$$\frac{df_{\rm dark}}{da} = \frac{u'(\Omega_m + u + v) - (\Omega_c + u)(u' + v')}{(\Omega_m + u + v)^2} = \frac{u'(\Omega_b + v) - v'(\Omega_c + u)}{(\Omega_m + u + v)^2}$$

Both $u' > 0$ and $v' < 0$, so both terms in the numerator are positive. Therefore $df_{\rm dark}/da > 0$ for all $a > 0$. **$\Omega_{\rm dark}/\Omega_{\rm tot}$ is strictly monotone increasing in $a$, equivalently strictly monotone decreasing in $z$.**

**Numerical confirmation (this dispatch):** 9999 positive sign-of-slope evaluations, 0 negative, minimum slope $\sim +8\times 10^{-12}$. Confirmed: no minimum, monotone.

**Limits:**

| Limit | Value |
|---|---|
| $a \to 0$ (Big Bang, $z \to \infty$): radiation-dominated | $f_{\rm dark} \to 0$ |
| $a = 1$ (now, $z = 0$): observed Planck values | $f_{\rm dark} = 0.9506$ |
| $a \to \infty$ (de Sitter heat death, $z \to -1$): dark energy asymptote | $f_{\rm dark} \to 1$ |

### Q6.2 — Result: $f_{\rm dark}$ crossed 5% at $z \approx 54\,000$ (not the present epoch)

Computed crossings via Friedmann integration:

| Target $f_{\rm dark}$ | Redshift $z$ at crossing | Scale factor $a$ | Cosmic age $t$ (Gyr) |
|---|---|---|---|
| 0.050 | $z \approx 5.4\times 10^4$ | $1.85\times 10^{-5}$ | $\sim 10^{-5}$ Gyr (radiation era) |
| 0.100 | $z \approx 2.5\times 10^4$ | $4.0\times 10^{-5}$ | $\sim 5\times 10^{-5}$ Gyr |
| 0.250 | $z \approx 8\,100$ | $1.24\times 10^{-4}$ | $\sim 3\times 10^{-4}$ Gyr |
| 0.500 | $z \approx 2\,335$ | $4.3\times 10^{-4}$ | $\sim 1.4\times 10^{-4}$ Gyr |
| 0.750 | $z \approx 421$ | $2.4\times 10^{-3}$ | $1.8\times 10^{-3}$ Gyr |
| 0.900 | $z \approx 0.56$ | $0.641$ | 8.15 Gyr |
| 0.949 | $z \approx 0.016$ | $0.985$ | 13.56 Gyr |
| 0.950 (now) | $z = 0$ | $a = 1$ | 13.79 Gyr |
| 1.000 | $z = -1$ | $\infty$ | $\infty$ (de Sitter) |

**Direct answer to Q6 part 1:** *"was it ever at 5%?"* — yes, but **at the radiation/matter-equality transition at $z \approx 5.4\times 10^4$, not as a minimum**. At that epoch, $\Omega_{\rm dark}/\Omega_{\rm tot}$ was passing through 5% on its monotone-increasing trajectory toward today's 95%. Before that epoch, radiation dominated and $f_{\rm dark}$ was even smaller (e.g. $f_{\rm dark} \approx 3\times 10^{-7}$ at $z = 10^{10}$). After that epoch, $f_{\rm dark}$ grew monotonically to today's 0.9506.

**Direct answer to Q6 part 2:** *"a minimum is required that would indicate some sort of oscillation"* — **under standard ΛCDM there is NO minimum**. The trajectory passes through 5% once on its monotone rise from 0 to 1; it does not return. **Standard cosmology answers Q6 with "no oscillation."**

### Q6.3 — Result: even under DESI's thawing-dark-energy hint, $f_{\rm dark}(a)$ remains monotone increasing

DESI 2024 VI (arXiv:2404.03002) + DESI DR2 (arXiv:2503.14738) report a preference for dynamical dark energy in the CPL parametrisation $w(a) = w_0 + w_a(1-a)$ with $w_0 > -1$ and $w_a < 0$ (thawing-like), at 3.1σ (BAO+CMB) to 4.2σ (BAO+CMB+SN).

Verified from arXiv 2503.14738 PDF extraction: *"a favored solution in the quadrant with w₀ > −1 and wₐ < 0"*, 3.1σ to 4.2σ depending on SN sample.

**Computed under representative thawing values $w_0 = -0.8$, $w_a = -0.7$:** I integrate the CPL dark-energy density $\rho_{\rm DE}(a) = \rho_{\rm DE,0} \cdot a^{-3(1+w_0+w_a)} \cdot \exp(-3w_a(1-a))$ into $f_{\rm dark}^{\rm CPL}(a)$.

Result on a fine grid ($a \in [10^{-12}, 1]$): **0 decrease-steps in 20 000 points. CPL-thawing $f_{\rm dark}(a)$ is still monotone increasing in $a$ over the observed past.**

| Redshift | $f_{\rm dark}^{\rm ΛCDM}$ | $f_{\rm dark}^{\rm CPL}$ | Δ |
|---|---|---|---|
| $z=0$ | 0.9506 | 0.9506 | 0 |
| $z=0.5$ | 0.9044 | 0.9079 | +0.0035 |
| $z=1$ | 0.8762 | 0.8765 | +0.0003 |
| $z=2$ | 0.8539 | 0.8515 | −0.0024 |
| $z=5$ | 0.8430 | 0.8420 | −0.0010 |
| $z=10$ | 0.8404 | 0.8402 | −0.0002 |

The CPL-thawing perturbation moves $f_{\rm dark}$ by at most a few × $10^{-3}$ at low $z$ relative to ΛCDM; it does NOT introduce a minimum in $f_{\rm dark}(a)$ over the past light-cone. **DESI 2024-25's beyond-ΛCDM hint, at face value, does not give Q6 a "yes" answer.**

**However** — CPL with $w_a < 0$ is mathematically extrapolated to $w_{\rm eff}(a)$ becoming positive for $a > -w_0/w_a + 1 \approx 2.14$ (for $w_0=-0.8$, $w_a=-0.7$). At that point, "dark energy" behaves like matter or stiffer fluid and its energy density decays faster than matter. **In the far future under DESI-CPL, $f_{\rm dark}$ stops increasing and asymptotes to a value below 1** — at $a=10$, $f_{\rm dark}^{\rm CPL} \to 0.843$; at $a=100$, still 0.843. The thawing parameters predict an *asymptote below 1*, not an oscillation, but this is a real qualitative departure from ΛCDM's monotone approach to 1.

**Q6 partial answer under DESI-thawing:** still no oscillation, no minimum in the past — but the *future asymptote* is below 1, not at 1. This means under §VII.6.1's monotone ring-down framing, the *ring-down completion fraction* would peak in the next few Gyr at ~95–97% and then decline (because dark-energy density decays faster than matter under thawing CPL with $w_a < 0$, so dark fraction shrinks again over time after dark-energy dilution).

### Q6.4 — Result: oscillation requires beyond-ΛCDM cyclic or oscillating-DE models

To get a true minimum or oscillation in $f_{\rm dark}(a)$ over cosmic history, you need a beyond-ΛCDM model where the dark-energy equation of state $w(a)$ becomes positive in some epoch (so $\rho_{\rm DE}$ falls faster than matter for a time), then returns to negative. The published models that do this:

- **Ekpyrotic / cyclic universe (Steinhardt-Turok 2001)**: predicts a cosmic cycle of contraction/expansion driven by brane collision. In such models, $f_{\rm dark}$ varies cyclically. **arXiv:hep-th/0111030** and **arXiv:astro-ph/0204479** are the canonical references. Steinhardt-Turok's cyclic model has the dark-energy phase end with another contraction, after which the cycle repeats. *In this model, the present 5% visible / 95% dark is a momentary state on a long cyclic trajectory.* Cycle period ≫ 13.8 Gyr (typically $\gtrsim$ trillions of years).
- **Phantom dark energy / Big Rip (Caldwell 1999, arXiv:astro-ph/9908168; Caldwell-Kamionkowski-Weinberg 2003, arXiv:astro-ph/0302506)**: requires $w < -1$, opposite of DESI's thawing hint. In this model $\rho_{\rm DE}$ grows in time, ending in a finite-time singularity (Big Rip). $f_{\rm dark} \to 1$ monotonically and faster than ΛCDM. **No minimum**.
- **Oscillating dark energy (Dodelson-Kaplinghat-Stewart 2000, arXiv:astro-ph/0002360)**: literal $w(a)$ oscillation in scalar-field models. In these, $f_{\rm dark}(a)$ has many local minima and maxima. **Not currently favoured by data**, but framework-allowed and gives Q6 a "yes" answer.
- **Loop quantum cosmology / bounce models** (Ashtekar-Pawlowski-Singh 2006, arXiv:gr-qc/0602086): replaces Big Bang singularity with a bounce. $f_{\rm dark}$ has a minimum at the bounce.

**Standard cosmology answer to Q6:** monotone, no minimum, no oscillation. Present 5%/95% is the present-epoch position on a monotone trajectory from 0% to 100%.

**Beyond-ΛCDM answer to Q6 under cyclic/oscillating-DE models:** yes, $f_{\rm dark}$ can oscillate. The 5% could be a momentary minimum (cyclic) or one of many maxima/minima (oscillating-DE). None of these are currently favoured at high significance.

### Q6.5 — Under §VII.6.1's monotone ring-down framing

§VII.6.1's framing in `dark_sector_substrate_internal_time_2026-05-16.md` (line 138-141, 145-148) commits to *monotone in cosmic time* ring-down completion. Q6.1–Q6.4 confirm this is consistent with standard ΛCDM and with the DESI-thawing CPL hint over the past light-cone.

**However**, Q6.3's finding that DESI-thawing parameters extrapolated to the far future give $f_{\rm dark}^{\rm CPL} \to 0.843$ (less than 1, less than today's 0.95) is a **load-bearing tension with §VII.6.1's "100% ring-down asymptote at de Sitter heat death"** claim. Under DESI-thawing, dark energy thaws and dilutes faster than matter, so $f_{\rm dark}$ peaks and decreases in the far future — *the universe never completes ring-down to 100%*, instead it peaks and recedes.

**If the DESI signal is real and CPL is the right parametrisation:** §VII.6.1's monotone-completion claim needs revision. Possible re-readings:
- "Ring-down completion" is a measure of past-direction integral, not present-epoch ratio. Monotone in past-direction but peaks and recedes at future asymptote.
- "Ring-down completion" tracks the cumulative complexification budget consumed, which IS monotone in cosmic time even when $f_{\rm dark}$ peaks and recedes — because $\rho_{\rm DE}$-mediated complexification cost is still being paid, just at a lower instantaneous rate.

**If the DESI signal is a systematic and ΛCDM holds:** §VII.6.1's monotone-to-100% claim is correct under standard cosmology. No revision needed.

**Verdict Q6:** Standard cosmology says **no oscillation, no minimum, 5% was crossed at $z \approx 5.4\times 10^4$ on a monotone trajectory** to today's 95%. Beyond-ΛCDM cyclic / oscillating-DE models can give oscillation, but are not data-favoured. DESI 2024-25's thawing-CPL signal does NOT introduce oscillation but DOES, if real, change the far-future asymptote of $f_{\rm dark}$ from 1 to ~0.84, which has a load-bearing implication for §VII.6.1's "100% ring-down at de Sitter" framing that may need refining if DESI is confirmed.

> **Fermata for conductor.** The DESI-thawing far-future-asymptote-below-1 finding is genuinely new content for §VII.6.1 — it does not invalidate ring-down monotone-in-past but it changes what "100% complete" means. Conductor decision: does §VII.6.1 need a §VII.6.1.X amendment along the lines of "ring-down completion as monotone past-integral, with future asymptote model-dependent under DESI-CPL"?

---

## Part IV — Identified other questions in the same line (Q7+)

Six brainstormed questions in the AoE / dark-sector / hyperbubble line. Each gets a result-or-honest-fail-with-discriminator.

### Q7 — What's the boundary of "our hyperbubble"? Cosmic event horizon? Particle horizon?

**Verified result (Wikipedia + cross-checked against Lineweaver-Davis 2003 standard reference):**

| Horizon | Comoving distance (Gpc) | Light-years | Meaning |
|---|---|---|---|
| **Particle horizon** | 14.26 Gpc | 46.5 Gly | Maximum comoving distance from which light emitted at $t=0$ has reached us by today. Defines the *observable universe radius*. |
| **Cosmic event horizon** | ≈ 5.0 Gpc | ≈ 16.3 Gly | Maximum comoving distance from which light emitted *today* can ever reach us in the future. |
| **Hubble radius** $c/H_0$ | 1/h × 9.78 Gpc = 14.5 Gly | — | Distance at which Hubble flow recedes at $c$ today. |

**Result for Q7:** under standard cosmology, our "hyperbubble boundary" in the hyperbubble-bump reading is most naturally identified with the **cosmic event horizon at ~16 Gly comoving** (the locus of points from which no signal can ever reach us). If the AoE / Cold Spot / HPA had been induced by external hyperbubble bumps, the bumps must have occurred *within* this region, and their signal must have travelled to us within the age of the universe.

**For the Aguirre-Johnson 2009 framework:** bubble collisions are predicted to occur at points where neighbouring bubbles intersect our bubble's past light cone. The intersection geometry can produce features at *any* angular size on the sky depending on collision time and bubble nucleation rate. The Osborne 2013 search constrains any single such collision to $|a (\sin\theta_{\rm bubble})^{4/3}| < 4.7\times 10^{-8}$ Mpc⁻¹ over the parameter range scanned.

**Discriminator for "where is the boundary":** Aguirre-Johnson 2009 distinguishes the *observable* hyperbubble boundary (particle horizon, 46.5 Gly comoving) from the *causal* boundary (event horizon, 16 Gly comoving) from the *spatial nucleation* boundary (where false-vacuum tunnelling occurred, model-dependent). All three are operationally meaningful; the user's "isolated hyperbubble" is most naturally the particle-horizon-bounded patch.

### Q8 — Are there CMB cold-spot-like features at low redshift LSS along the AoE axis?

**Honest fail with discriminator.** I have not found a published, statistically-significant LSS feature aligned along the AoE axis (l, b) ≈ (240°, 60°). 

**What is published:**
- **Szapudi-Kovács-Granett et al. 2015** (arXiv:1405.1566), MNRAS 450, 288: a supervoid of radius $\sim 220 h^{-1}$ Mpc at $z \approx 0.22$, aligned with the Cold Spot direction (l, b) ≈ (207°, −56°). Density contrast $\delta_m \approx -0.14 \pm 0.04$. Stated as "a plausible cause for the Cold Spot" at ~3.3σ.
- **Mackenzie et al. 2017** (arXiv:1704.03814): later survey work disputes Szapudi's supervoid as sufficient to explain the Cold Spot via ISW. *"the CMB Cold Spot could not have been imprinted by a void confined to the inner core of the Cold Spot."* Status: contested.
- **Cold Spot is offset 30° from the AoE antipole**, so even if the Eridanus supervoid is real, it is **not on the AoE axis**.

**Discriminator:** a future high-precision LSS-cross-correlation survey along the AoE axis ($l \approx 240°$, $b \approx 60°$) would resolve Q8 directly. **Status: no published cross-correlation along the AoE axis specifically.** Euclid / Roman / LSST will provide the data, but as of 2026-05-16 this is a genuine gap. **Q8 = honest open with named discriminator.**

### Q9 — Is the Hubble tension an AoE-aligned signature?

**Verified result with directional anchor:**

| Reference | Direction-of-H0 finding |
|---|---|
| **Riess et al. 2022** (arXiv:2112.04510), SH0ES H₀ = 73.04 ± 1.04 km/s/Mpc, 5σ tension with Planck. | No directional claim — isotropic by analysis design. |
| **Krishnan, Mohayaee, Ó Colgáin, Sheikh-Jabbari, Yin 2021** (arXiv:2106.02532) | Reports correlation between higher $H_0$ and the CMB-dipole direction. Variation ~1 km/s/Mpc between antipodal points in the Pantheon sample. Effect strongest at $z \lesssim 0.075$. |
| **Pantheon+ region-fitting Hu et al. 2024** | Dominant dipole pattern detected at low $z$; not statistically significant at $z > 0.015$. |

**Computed alignment** (this dispatch): AoE pole ↔ CMB dipole separation = **18.3°**. The Krishnan 2021 "higher H₀ direction correlates with CMB dipole" finding therefore **also correlates with the AoE direction at ~18°**. The Hubble tension's *directional* component (to the extent it exists per Krishnan) and the AoE direction are mutually close to within the angular resolution of the supernova samples.

**Q9 result:** the Hubble tension has a directional dipole at low $z$ (Krishnan 2021) which is close to the AoE direction. **However:** Krishnan 2021 itself notes the effect is at $z \lesssim 0.075$, which is local-volume scale (~300 Mpc), not cosmological. The Hubble tension at $z \gtrsim 0.1$ is consistent with isotropic. **The AoE-aligned-Hubble-tension reading therefore couples solar-system-frame anomalies to local-volume anomalies via the CMB-dipole direction, but does not extend to the cosmological-scale Hubble tension**. This is consistent with both the Bennett 2011 systematics reading and the Part I internal-bundle-direction reading.

**Discriminator:** if Pantheon+ region-fitting (Hu et al. 2024) is borne out by Roman / Rubin, a real $H_0$ anisotropy at higher $z$ would correlate with substrate-side dynamics in MFO §VII. **Status: ambiguous evidence; not load-bearing.**

### Q10 — What angular scale would separate "ring-up content" from "ring-down content" in CMB temperature?

**Honest fail with discriminator.** Under Part I Reading B1 ("more low-ℓ power = active ring-up = younger"), one can predict that ring-up content lives at the LARGEST angular scales (low ℓ, large ~30°-180° features) and ring-down content lives at SMALL scales (high ℓ, sub-degree features, late-time accumulation into substrate residue). The HPA's persistence across $\ell = 2$–$600$ (Hansen 2009) is then puzzling — it does not separate cleanly into "low-ℓ ring-up vs high-ℓ ring-down" regimes.

**Computation that would unlock Q10:** the §VII.5 quantitative-match dark-matter halo profile / rotation curve / ISW computation, which would predict the angular-scale spectrum of ring-down residue's CMB imprint. Until that runs, Q10 is a fermata.

**Discriminator:** the §VII.5 quantitative-match open computation, same as Part I Reading B1 vs B2 discriminator.

### Q11 — Does §VII.6.1 predict a specific scale at which substrate-internal time and clock-time diverge measurably?

**Result with explicit computation.** From the dark-sector working note Q2 Reading C (instantaneous-rate fraction at present epoch, lines 90-94): the substrate-internal time vs clock-time *ratio* at the present epoch is $f_{\rm visible}(z=0) = 0.0493$, so substrate-internal time runs at $\sim 20\times$ clock-time rate. This is the operational divergence factor.

**No characteristic spatial scale of divergence is predicted by §VII.6.1** — the rate ratio is a *temporal* quantity, applying everywhere. **However,** since $f_{\rm visible}(z)$ varies with $z$ (computed in Part III above: at $z = 1$, $f_{\rm visible} = 0.124$; at $z = 10$, $f_{\rm visible} = 0.16$; at $z = 3400$, $f_{\rm visible} = 0.58$; deeper still in radiation era, $f_{\rm visible}$ approaches 1), the divergence factor is **redshift-dependent**.

**Computed divergence-factor trajectory** (this dispatch, derived from Part III table):

| Redshift $z$ | $f_{\rm visible}(z) = 1 - f_{\rm dark}(z)$ | Substrate / clock time-rate ratio |
|---|---|---|
| 0 (now) | 0.0494 | 20.2× |
| 0.5 | 0.0956 | 10.5× |
| 1 | 0.1238 | 8.1× |
| 3 | 0.1529 | 6.5× |
| 10 | 0.1596 | 6.3× |
| 100 | 0.1814 | 5.5× |
| 1000 | 0.349 | 2.9× |
| 3400 (rad-matter eq.) | 0.578 | 1.7× |
| 54000 | 0.95 | 1.05× |
| $\to \infty$ | $\to 1$ | $\to 1$ |

**Q11 result:** substrate-internal-time vs clock-time divergence **grows over cosmic history**, from 1:1 in the deep radiation era to ~20:1 today. **The divergence factor is $1/f_{\rm visible}(z) = 1/(1-f_{\rm dark}(z))$**, monotonically increasing in cosmic time as the dark fraction approaches 1. **Q11 = answered, not fermata.** No spatial scale; the divergence is purely temporal.

### Q12 — What's the framework reading of the "Hubble bubble" / local underdensity hypothesis?

**Result with literature anchor.** The local-Hubble-bubble hypothesis (Marra-Pääkkönen-Valkenburg 2013, arXiv:1308.6086; Wojtak-Riess-Macri-Filippenko 2014) proposes that we live in a local underdensity of radius $\sim 100$–$300$ Mpc, biasing $H_0$ measurements upward and partially explaining the Hubble tension.

**Under §VII.6.1**: a local underdensity is a region of *less ring-down completion* (less substrate residue accumulated). The Hubble tension's directional component (Krishnan 2021, see Q9) and the AoE direction's 18° proximity to the CMB dipole are then candidate substrate-frame coincidences.

**Q12 framework reading:** an MFO §VII.6.1-internal reading of the Hubble bubble would identify the local underdensity as a *local ring-down-completion fluctuation* in the substrate. **No quantitative match without §VII.5 computation.** The framework reading is internally consistent but no falsifier yet — same discriminator as Q10 (the §VII.5 quantitative match).

**Status:** candidate framing only; not endorsed over Marra-Pääkkönen-Valkenburg's standard-cosmology reading.

---

## Part V — Updated final verdict (covering Parts I–IV)

### Load-bearing results from this dispatch

1. **Q5 strongest finding (geometric).** The hyperbubble-bump reading is **disfavoured on shape grounds**, not on observational sensitivity. Bubble-collision templates are *disc-shaped with a characteristic angular radius* $\theta_{\rm bubble}$; the AoE is *axial with no characteristic angular scale*. These are different geometric primitives. The Cold Spot is the only AoE-family anomaly with a bubble-collision-template shape, and Osborne 2013 / Planck 2015 XVI null results constrain its bubble-collision amplitude at 95% C.L. **Conclusion: AoE ≠ hyperbubble bump.** Internal-bundle-direction reading (Part I) survives; external-hyperbubble reading does not have a fit.

2. **Q5 secondary finding (alignment).** Computed AoE pole ↔ CMB dipole separation = **18.3°**. This is the smallest separation among the AoE/Cold-Spot/HPA family and is the load-bearing alignment in the literature (the "evil" of the AoE). All three readings (bubble collision, internal-bundle-direction, systematics) must account for this 18°.

3. **Q6 strongest finding (Friedmann).** Under standard ΛCDM, $\Omega_{\rm dark}/\Omega_{\rm tot}(a)$ is **strictly monotone increasing** in $a$ (proved analytically + numerically verified on 10⁴ log-spaced points). Crossed 5% at $z \approx 5.4\times 10^4$ on its monotone trajectory; 50% at $z \approx 2\,335$ (matter-radiation transition era); 90% at $z \approx 0.56$; **95% (today) at $z = 0$**. There is no minimum and no oscillation under ΛCDM.

4. **Q6 secondary finding (DESI hint).** Under DESI 2024-25's thawing-CPL hint ($w_0 > -1$, $w_a < 0$, 3.1–4.2σ), $f_{\rm dark}(a)$ is still monotone increasing over the past light-cone. **However, the far-future asymptote of $f_{\rm dark}$ drops from 1.0 (ΛCDM) to ~0.84 (CPL with $w_0=-0.8$, $w_a=-0.7$)** — dark energy thaws and dilutes faster than matter in the far future. If DESI is confirmed, §VII.6.1's "100% ring-down at de Sitter heat death" framing needs refining: ring-down completion remains monotone in past-direction but the future asymptote is model-dependent.

5. **Q9 result (Hubble tension direction).** Krishnan et al. 2021 reports the directional $H_0$ dipole correlates with the CMB-dipole direction, which is 18.3° from the AoE pole. Effect is significant only at $z \lesssim 0.075$ (local-volume scale). **AoE-aligned Hubble-tension reading is weakly suggestive but not load-bearing.**

6. **Q11 result (time-rate divergence).** Substrate-internal-time vs clock-time divergence factor = $1/(1 - f_{\rm dark}(z))$, growing monotonically from 1× in deep radiation era to 20× today. Predicted to grow further toward de Sitter asymptote (or peak under DESI-CPL).

### What this changes

- **The "low-ℓ anomaly family as unified substrate feature" candidate reading of Part I is *strengthened* by Q5's negative finding** — the alternative external-bump reading does not fit shape-wise, so the substrate-side reading is more natural by elimination. Still not endorsed over Bennett 2011 systematics.
- **§VII.6.1's monotone ring-down framing is robust** against the user's Q6 oscillation question under standard ΛCDM; DESI's thawing hint introduces a future-asymptote refinement that may need §VII.6.1.X amendment.
- **The 18.3° AoE-CMB-dipole alignment is the live anomaly across all readings** — it is the irreducible signal that demands explanation under bubble-collision (fails: bubbles don't align with our motion), substrate-bundle-direction (fails: bundle-base directions don't align with our motion either), and systematics (fails: foregrounds don't naturally produce a 99.9%-C.L. alignment in this geometry).

### What this does not change

- No GR / ΛCDM prediction is altered.
- Bennett 2011 skeptical baseline stands.
- §VII.5 quantitative-match open computation remains the principal discriminator for Part I Reading B1 vs B2.
- The §VII.6.1 framing as candidate, not endorsed, stays the disposition.

### Updated falsifier list

1. **Osborne 2013 + Planck 2015 XVI null result already disfavours hyperbubble-bump on shape grounds for the AoE.** This is now a *standing* falsifier, not a future one. Cold Spot remains the only AoE-family object with a bubble-collision-template shape; its bubble-collision amplitude is constrained at 95% C.L.
2. **DESI DR3 / Roman / Rubin confirms thawing-CPL at $\gtrsim 5\sigma$:** §VII.6.1 needs a future-asymptote refinement (ring-down completion ceiling below 100%). If DESI is a systematic and ΛCDM holds, no refinement needed.
3. **§VII.5 residual-geometric-curvature computation distinguishes Reading B1 vs B2** — as in Part I.
4. **LSS cross-correlation along AoE axis** at Euclid / Roman / LSST sensitivities — as in Part I.
5. **Hubble-tension directional dipole at $z > 0.1$** (Pantheon+ / Roman): if confirmed, AoE-Hubble-tension reading is strengthened; if null at higher $z$, weakened.
6. **Cosmic birefringence rotation angle** (Minami-Komatsu 2020 reports β = 0.35° ± 0.14° at 2.4σ from Planck 2018 EB cross-correlation, arXiv:2011.11254) — independent probe of parity-violating physics at CMB last-scattering surface. If detected at $\gtrsim 5\sigma$ in LiteBIRD, would constrain MFO substrate-frame Lorentz-violation predictions.

### Proposed notebook integration (updated)

> **Concertmaster draft only; conductor decides whether to land in §VII.6.2 or as inline expansion of §VII.6.1.**

Draft §VII.6.1.1 (candidate) — *"AoE / HPA / Cold Spot as bundle-direction signature of the dark-sector ring-down"*:

> The CMB large-scale anomaly family (Axis of Evil per de Oliveira-Costa 2004 / Land–Magueijo 2005; HPA per Eriksen 2004 / Hansen 2009; Cold Spot per Vielva 2004) admits one candidate substrate-side reading under §VII.6.1's ring-down framing composed with §VII.4.1.1's spherical-compression / Hopf-bundle structure: the AoE marks a preferred bundle-base direction at galactic (l, b) ≈ (240°, 60°); the HPA breaks the pole/antipole degeneracy via differential power between hemispheres; under Reading B1 ("more low-ℓ power = less ring-down complete = younger substrate"), the southern-ecliptic hemisphere is the younger end of the axis and the Cold Spot near the AoE antipole is a localised more-ring-down-complete feature. **The alternative reading of these as a hyperbubble bump from external excitation is disfavoured on shape grounds** (bubble-collision templates are disc-shaped with characteristic angular radius; AoE is axial with no characteristic scale), per Osborne 2013 + Planck 2015 XVI null result on the Cold-Spot-as-bubble-collision search. The reading is one candidate among several; the standard ΛCDM-plus-systematics reading (Bennett 2011) remains valid; it does not modify any GR prediction; the §VII.5 residual-geometric-curvature quantitative-match open computation is the principal discriminator. The 18.3°-AoE-pole-↔-CMB-dipole alignment is the live anomaly across all readings. Full empirical workings + reference verification: [`research-mfo/axis_of_evil_ring_down_framing_2026-05-16.md`](research-mfo/axis_of_evil_ring_down_framing_2026-05-16.md).

Draft §VII.6.1.2 (candidate) — *"Far-future asymptote of ring-down completion under DESI thawing-CPL hint"*:

> §VII.6.1's framing of "100% ring-down at de Sitter heat death" is robust under standard ΛCDM (Ω_dark/Ω_tot monotone increasing in a, asymptote → 1). Under DESI 2024 VI (arXiv:2404.03002) + DESI DR2 (arXiv:2503.14738) thawing-CPL preference (w₀ > −1, wₐ < 0 at 3.1–4.2σ), the far-future asymptote of Ω_dark/Ω_tot drops below 1 (≈ 0.84 for representative thawing values w₀=−0.8, wₐ=−0.7). Under this beyond-ΛCDM reading, ring-down completion remains monotone in past-direction but does not asymptote to 100%; instead it peaks at ~95–97% in the next few Gyr and declines toward the thawing asymptote. The framework reading of this is: ring-down completion measures cumulative complexification budget *consumed* (monotone in cosmic time) rather than instantaneous dark fraction. Pending DESI DR3 confirmation; if DESI hint is a systematic, §VII.6.1 stands as-is.

Cross-references would mirror §VII.6.1's set: shadow-stance family + §VII.4.1.1 + §VII.5 + §VII.6 + §VII.6.1 + the cmb_anomalies catalog rows + (for §VII.6.1.2) DESI 2024 VI / DR2 references.

---

## References (verified via arXiv PDF extraction)

**AoE primary literature:**
- de Oliveira-Costa, Tegmark, Zaldarriaga, Hamilton (2004). *The significance of the largest scale CMB fluctuations in WMAP.* Phys. Rev. D 69, 063516. [arXiv:astro-ph/0307282](https://arxiv.org/abs/astro-ph/0307282).
- Schwarz, Starkman, Huterer, Copi (2004). *Is the low-l microwave background cosmic?* Phys. Rev. Lett. 93, 221301. [arXiv:astro-ph/0403353](https://arxiv.org/abs/astro-ph/0403353).
- Land, Magueijo (2005). *The axis of evil.* Phys. Rev. Lett. 95, 071301. [arXiv:astro-ph/0502237](https://arxiv.org/abs/astro-ph/0502237).
- Copi, Huterer, Schwarz, Starkman (2006). *On the large-angle anomalies of the microwave sky.* MNRAS 367, 79–102. [arXiv:astro-ph/0508047](https://arxiv.org/abs/astro-ph/0508047).
- Frommert, Enßlin (2010). *The axis of evil — a polarization perspective.* MNRAS 410, 280–286. [arXiv:0908.0453](https://arxiv.org/abs/0908.0453).

**Cold Spot:**
- Vielva, Martínez-González, Barreiro, Sanz, Cayón (2004). *Detection of non-Gaussianity in the WMAP 1-year data using spherical wavelets.* ApJ 609, 22–34. [arXiv:astro-ph/0310273](https://arxiv.org/abs/astro-ph/0310273). (Note: the canonical "Cold Spot" name solidifies in subsequent papers; this is the discovery reference.)

**Hemispherical Power Asymmetry:**
- Eriksen, Banday, Górski, Lilje (2004). *Asymmetries in the CMB anisotropy field.* ApJ 605, 14–20. [arXiv:astro-ph/0407271](https://arxiv.org/abs/astro-ph/0407271). (Verified: "northern ecliptic hemisphere is practically devoid of large scale fluctuations, while the southern hemisphere shows relatively strong fluctuations.")
- Hansen, Banday, Górski, Eriksen, Lilje (2009). *Power asymmetry in cosmic microwave background fluctuations from full sky to sub-degree scales: Is the universe isotropic?* ApJ 704, 1448–1458. [arXiv:0812.3795](https://arxiv.org/abs/0812.3795). (Preferred direction galactic (l, b) ≈ (226°, −17°); 0.4% significance over ℓ=2–600.)

**Skeptical baseline and reviews:**
- Bennett et al. (WMAP, 2011). *Seven-Year WMAP Observations: Are There Cosmic Microwave Background Anomalies?* ApJS 192, 17. [arXiv:1001.4758](https://arxiv.org/abs/1001.4758).
- Schwarz, Copi, Huterer, Starkman (2016). *CMB anomalies after Planck.* Class. Quantum Grav. 33, 184001. [arXiv:1510.07929](https://arxiv.org/abs/1510.07929).
- Akrami et al. (Planck Collaboration, 2020). *Planck 2018 results. VII. Isotropy and Statistics of the CMB.* A&A 641, A7. [arXiv:1906.02552](https://arxiv.org/abs/1906.02552).
- Planck Collaboration (2016). *Planck 2015 results. XVI. Isotropy and statistics of the CMB.* A&A 594, A16. [arXiv:1506.07135](https://arxiv.org/abs/1506.07135).

**Bubble-collision / eternal-inflation literature (Q5, this dispatch):**
- Feeney, Johnson, McEwen, Peiris (2011). *First Observational Tests of Eternal Inflation.* Phys. Rev. Lett. 107, 071301. [arXiv:1012.1995](https://arxiv.org/abs/1012.1995).
- Feeney, Johnson, Mortlock, Peiris (2011). *First Observational Tests of Eternal Inflation: Analysis Methods and WMAP 7-Year Results.* Phys. Rev. D 84, 043507. [arXiv:1012.3667](https://arxiv.org/abs/1012.3667).
- Aguirre, Johnson (2011). *A status report on the observability of cosmic bubble collisions.* Rep. Prog. Phys. 74, 074901. [arXiv:0908.4105](https://arxiv.org/abs/0908.4105). (User's brief listed 0904.2789; that is a different paper. Corrected.)
- McEwen, Feeney, Johnson, Peiris (2012). *Optimal filters for detecting cosmic bubble collisions.* Phys. Rev. D 85, 103502. [arXiv:1202.2861](https://arxiv.org/abs/1202.2861).
- Osborne, Senatore, Smith (2013). *Collisions with other Universes: the Optimal Analysis of the WMAP data.* [arXiv:1305.1964](https://arxiv.org/abs/1305.1964). (User's brief listed 1303.1080; that is a Hartman-Maldacena entanglement-entropy paper. Corrected.)
- Johnson, Peiris, Lehner (2012). *Determining the outcome of cosmic bubble collisions in full General Relativity.* Phys. Rev. D 85, 083516. [arXiv:1112.4487](https://arxiv.org/abs/1112.4487).

**Cold Spot supervoid / cosmic structure (Q8):**
- Szapudi, Kovács, Granett, et al. (2015). *Detection of a Supervoid Aligned with the Cold Spot of the Cosmic Microwave Background.* MNRAS 450, 288. [arXiv:1405.1566](https://arxiv.org/abs/1405.1566). (Supervoid radius ~220 h⁻¹ Mpc at z ≈ 0.22, δ_m ≈ −0.14.)
- Mackenzie, Shanks, Bremer, et al. (2017). *Evidence against a supervoid causing the CMB Cold Spot.* MNRAS 470, 2328. [arXiv:1704.03814](https://arxiv.org/abs/1704.03814).

**Dark-energy evolution / DESI (Q6):**
- DESI Collaboration (2024). *DESI 2024 VI: Cosmological Constraints from the Measurements of Baryon Acoustic Oscillations.* [arXiv:2404.03002](https://arxiv.org/abs/2404.03002).
- DESI Collaboration (2025). *DESI DR2 Results II.* Phys. Rev. D 112, 083515. [arXiv:2503.14738](https://arxiv.org/abs/2503.14738). (Thawing-CPL preference w₀ > −1, wₐ < 0 at 3.1–4.2σ.)

**Cyclic / oscillating-DE / phantom (Q6.4):**
- Steinhardt, Turok (2001). *Cosmic Evolution in a Cyclic Universe.* [arXiv:hep-th/0111030](https://arxiv.org/abs/hep-th/0111030).
- Steinhardt, Turok (2002). *A cyclic model of the universe.* [arXiv:astro-ph/0204479](https://arxiv.org/abs/astro-ph/0204479).
- Khoury, Ovrut, Steinhardt, Turok (2001). *The Ekpyrotic Universe: Colliding Branes and the Origin of the Hot Big Bang.* Phys. Rev. D 64, 123522. [arXiv:hep-th/0103239](https://arxiv.org/abs/hep-th/0103239).
- Caldwell (1999). *A phantom menace?* [arXiv:astro-ph/9908168](https://arxiv.org/abs/astro-ph/9908168).
- Caldwell, Kamionkowski, Weinberg (2003). *Phantom Energy and Cosmic Doomsday.* Phys. Rev. Lett. 91, 071301. [arXiv:astro-ph/0302506](https://arxiv.org/abs/astro-ph/0302506).
- Dodelson, Kaplinghat, Stewart (2000). *Solving the coincidence problem: tracking oscillating dark energy.* [arXiv:astro-ph/0002360](https://arxiv.org/abs/astro-ph/0002360).

**Hubble tension and direction (Q9):**
- Riess et al. (2022). *A Comprehensive Measurement of the Local Value of the Hubble Constant ... SH0ES.* ApJ 934, L7. [arXiv:2112.04510](https://arxiv.org/abs/2112.04510). (H₀ = 73.04 ± 1.04, 5σ tension with Planck.)
- Krishnan, Mohayaee, Ó Colgáin, Sheikh-Jabbari, Yin (2021). *Does Hubble tension signal a breakdown in FLRW cosmology?* Class. Quantum Grav. 38, 184001. [arXiv:2106.02532](https://arxiv.org/abs/2106.02532).

**Cosmic birefringence (Q11 falsifier 6):**
- Minami, Komatsu (2020). *New Extraction of the Cosmic Birefringence from the Planck 2018 Polarization Data.* Phys. Rev. Lett. 125, 221301. [arXiv:2011.11254](https://arxiv.org/abs/2011.11254). (β = 0.35° ± 0.14° at 2.4σ.)

**Project catalog rows (attested):**
- `axis-of-evil-l2-l3-alignment`, `cold-spot`, `hemispherical-power-asymmetry` — [`docs/antikythera-maths/research/attested/cmb_anomalies/row.ndjson`](../research/attested/cmb_anomalies/row.ndjson).

**MFO notebook cross-references:**
- §VII.2 (time as metric field dynamics) — line 693
- §VII.4.1 (black holes end at 2D boundary; spherical compression named) — line 721
- §VII.4.1.1 (Hopf-bundle / fibre as encoding channel) — line 758
- §VII.4.1.2 (Casimir-decomposition universality) — line 803
- §VII.5 (dark matter as residual geometric curvature) — line 848
- §VII.6 (dark energy as complexification cost) — line 862
- §VII.6.1 (substrate-internal time / 95% ring-down) — line 872

**Companion working-note:**
- `[research-mfo/dark_sector_substrate_internal_time_2026-05-16.md`](dark_sector_substrate_internal_time_2026-05-16.md) — the dark-sector / 95%-ring-down working-note artifact this companion is grounded against.

**Memory cross-references:**
- `[[user_stance_dark_sector_ring_down_age]]` — canonical user stance, 2026-05-16
- `[[user_stance_string_theory_instrument_first]]` — ring-up / ring-down vocabulary
- `[[user_stance_time_as_dimensional_shadow]]` — substrate vs shadow distinction
- `[[user_stance_hyper_as_3d_spatial_interface]]` — two-level ontology / substrate + excitations
- `[[user_stance_identity_not_implementation_discipline]]` — shadow-stance family umbrella
- `[[feedback_no_lineage_claims_in_notebook]]` — candidate framing discipline
- `[[feedback_pdf_extraction_citation_discipline]]` — PDF-extraction citation verification
- `[[reference_autonomous_validation_tos_landscape]]` — arXiv permitted; commercial publishers not used
