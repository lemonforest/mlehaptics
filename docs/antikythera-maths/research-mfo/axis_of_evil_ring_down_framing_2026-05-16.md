# Axis of Evil under the §VII.6.1 ring-down framing

**Date:** 2026-05-16
**Research spike artifact.** User-initiated investigation following the same-day §VII.6.1 ship of the substrate-internal-time / 95%-ring-down framing of the dark sector. Three nested questions:

1. *"we want to see if we can learn about the axis of evil and if we can see what dark sector content looks like from that perspective."*
2. *"axis of evil is a hot spot or a cold spot? from who's perspective?"*
3. *"can we see spots that are opposite of the axis of evil that might be very young?"*

> **Provenance note.** Concertmaster dispatch by the conductor after §VII.6.1 landed in `mfo_spectral_research_notebook.md` (lines 872–937). Companion to the dark-sector working-note artifact (`dark_sector_substrate_internal_time_2026-05-16.md`). Same author voice / structure / three-reading discipline.

---

## Q1 — What is the Axis of Evil, observationally?

### SSoT verification (PDF extraction per `[[feedback_pdf_extraction_citation_discipline]]`)

| arXiv ID | Authors | Title | Journal | Verified content |
|---|---|---|---|---|
| [astro-ph/0307282](https://arxiv.org/abs/astro-ph/0307282) | de Oliveira-Costa, Tegmark, Zaldarriaga, Hamilton | *The significance of the largest scale CMB fluctuations in WMAP* | Phys. Rev. D 69, 063516 (2004) | Quadrupole–octupole alignment at "1-in-60 level"; combined a priori probability "1 in 24000" (cautioned re multiple-comparisons). |
| [astro-ph/0403353](https://arxiv.org/abs/astro-ph/0403353) | Schwarz, Starkman, Huterer, Copi | *Is the low-l microwave background cosmic?* | Phys. Rev. Lett. 93, 221301 (2004) | Three octopole planes orthogonal to ecliptic at 99.8% C.L.; normals aligned with CMB dipole + equinoxes at 99.9% C.L.; ecliptic threads between hot and cold spots over ~1/3 of sky. |
| [astro-ph/0502237](https://arxiv.org/abs/astro-ph/0502237) | Land, Magueijo | *The axis of evil* | Phys. Rev. Lett. 95, 071301 (2005) | Coined the name. Alignment extends to ℓ=2,3,5; preferred direction at galactic (b, l) ≈ (60°, −100°) ≡ (l, b) ≈ (260°, 60°); rejection of statistical isotropy at >99.9%. |
| [astro-ph/0508047](https://arxiv.org/abs/astro-ph/0508047) | Copi, Huterer, Schwarz, Starkman | *On the large-angle anomalies of the microwave sky* | MNRAS 367, 79 (2006) | Quadrupole+octopole plane perpendicular to ecliptic plane and dipole-direction plane; ecliptic separates stronger from weaker extrema at >99.9% C.L. |
| [1001.4758](https://arxiv.org/abs/1001.4758) | Bennett et al. (WMAP) | *Seven-Year WMAP Observations: Are There Cosmic Microwave Background Anomalies?* | ApJS 192, 17 (2011) | "No compelling evidence for deviations from ΛCDM"; "claimed anomalies depend on posterior selection of some aspect or subset of the data." Skeptical canonical reference. |
| [1510.07929](https://arxiv.org/abs/1510.07929) | Schwarz, Copi, Huterer, Starkman | *CMB anomalies after Planck* | Class. Quantum Grav. 33, 184001 (2016) | Comprehensive review; explicitly notes "some pairs of those features are demonstrably uncorrelated" — the low-ℓ anomaly family is not a single object. |
| [1906.02552](https://arxiv.org/abs/1906.02552) | Akrami et al. (Planck Coll.) | *Planck 2018 results. VII. Isotropy and Statistics of the CMB* | A&A 641, A7 (2020) | Confirms anomalies persist in PR3; "no unambiguous detections" of cosmological non-Gaussianity in polarisation. |

### What the AoE actually is

- **A directional alignment of low-ℓ multipoles**, not a localised temperature feature. The "axis" is a preferred *line on the celestial sphere* picked out by Maxwell-vector representations of the ℓ=2 and ℓ=3 multipoles. It has a *pole and an antipole*; there is no distinguished "north" end of the axis.
- **Preferred direction.** Best-fit axes in the literature cluster near galactic (l, b) ≈ (240°–260°, 60°). The project's own attested catalog row [`docs/antikythera-maths/research/attested/cmb_anomalies/row.ndjson`](../research/attested/cmb_anomalies/row.ndjson), `axis-of-evil-l2-l3-alignment`, records (240°, 60°) — consistent with the Land–Magueijo (260°, 60°) within estimator scatter.
- **The really weird part is not the alignment with itself.** It is the *additional alignment* — at 99.8–99.9% C.L. (Schwarz et al. 2004; Copi et al. 2006) — with the **ecliptic plane**, the **CMB dipole direction**, and the **equinox direction**. These are solar-system-frame references, not cosmological references. The AoE is "evil" because it aligns the cosmological with the local-solar-system.
- **Statistical significance is test-dependent.** The catalog stores ~3σ as representative; reported significances range from ~99% (de Oliveira-Costa 2004 multipole-vector tests alone) to >99.9% (Schwarz 2004 + Land–Magueijo 2005 multi-feature joint tests). Bennett et al. 2011 documents the posterior-selection skeptical baseline. Frommert & Enßlin 2010 ([0908.0453](https://arxiv.org/abs/0908.0453)) explicitly uses CMB polarisation as an independent probe and finds the alignment consistent with chance at the ~50% level — i.e., the temperature signal does not get reinforced by polarisation.

**Conclusion Q1.** The Axis of Evil is a low-ℓ multipole alignment, axis at (l, b) ≈ (240°–260°, 60°) in galactic coordinates, with secondary alignment to ecliptic/dipole/equinox at ~99.9% C.L. (the load-bearing claim). The temperature anomaly is robust as observation; the polarisation independent-probe is consistent with chance. The framing "hot spot vs cold spot" is **the wrong taxonomy** — it is neither.

---

## Q2 — Hot spot, cold spot, or neither? From whose perspective?

### Reading A — Standard observational baseline

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

### Reading B — "From whose perspective?" under MFO commitments

The user's framing question parses cleanly under the two-level ontology of `[[user_stance_hyper_as_3d_spatial_interface]]` (substrate + excitation levels) and the shadow-stance family:

- **Shadow-side / standard-observer perspective.** What we *see* is the projection of the CMB last-scattering surface onto our 2-sphere of sight at z=0. From this perspective the AoE is a directional anomaly on a single emission surface; it has no temporal extent (the CMB is a single redshift slice in clock-time). Hot/cold-spot framing applies only to the Cold Spot and to local extrema; the AoE itself is an alignment, not a temperature feature.
- **Substrate-side perspective.** Under §VII.4.1.1's spherical-compression / Hopf-bundle reading and §VII.4.1.2's Casimir-decomposition universality, *every* observation on a 2-sphere is the base projection of a principal-bundle total-space structure. A preferred direction in the base S² corresponds to a preferred fibre-direction or connection-curvature feature in the bundle. Under this reading, the AoE is a **direction in the substrate's bundle geometry**, not a temperature.

The "from whose perspective?" question therefore has two operationally distinct answers:

| Perspective | What the AoE is | Hot? Cold? |
|---|---|---|
| Observer (shadow-side) | Alignment of low-ℓ multipole vectors with each other + with ecliptic/dipole/equinox | Neither; it's directional, not amplitude |
| Substrate (MFO §VII.4.1.1) | A preferred fibre / connection-curvature direction in the S² boundary's principal-bundle structure | Asks the wrong question; "temperature" is not the substrate-level observable for an alignment feature |

### What's actually a hot vs cold thing — the local extrema

The Schwarz et al. 2004 + Copi et al. 2006 finding does name local hot/cold extrema **threaded by the ecliptic**: "the ecliptic plane narrowly threads between a hot spot and a cold spot over approximately 1/3 of the sky" (astro-ph/0403353 abstract). These are the *local* extrema picked out by the aligned quadrupole+octopole on either side of the AoE plane. The hot spot and cold spot referenced here are not the canonical "Cold Spot" (which is at southern galactic latitudes, distinct from the AoE-aligned local extrema). The AoE *organises* local hot/cold structure along the ecliptic; it is not itself one of them.

### Resolution

The user's question "axis of evil is a hot spot or a cold spot? from who's perspective?" parses as:

- **Observationally:** neither — it's an alignment / preferred direction.
- **In the AoE's organised local-extrema sense (Schwarz 2004):** the aligned quadrupole+octopole *does* pick out a hot–cold dipolar structure roughly along the ecliptic, but the AoE itself is the *axis* of that dipolar structure, not one of its poles.
- **Under MFO §VII.4.1.1:** "hot vs cold" is the wrong observable for an alignment feature; the substrate-side observable is bundle-base direction, not temperature.

The honest answer: **it's an axis (pole + antipole), not a spot. The "perspective" that would make it hot or cold is the perspective that picks one end of the axis — and the data does not distinguish the two ends.**

This is the load-bearing point for Q3.

---

## Q3 — Antipodal "very young" spots: is there a reading?

### The pole/antipole degeneracy

The user's question is sharp: under §VII.6.1's ring-down framing, "young" means *less ring-down complete* (less of cosmic complexification has settled into the dark sector along that direction). For an *axis*, the alignment doesn't distinguish "the pole is old" from "the pole is young" — both ends of the line are mathematically equivalent under the multipole-vector representation. The AoE alone cannot answer "which end is young."

What *does* distinguish hemispheres along that axis is the **Hemispherical Power Asymmetry** (Eriksen et al. 2004 [astro-ph/0407271](https://arxiv.org/abs/astro-ph/0407271); Hansen et al. 2009 [0812.3795](https://arxiv.org/abs/0812.3795)), an independent low-ℓ anomaly:

- Eriksen 2004: *"the northern ecliptic hemisphere is practically devoid of large-scale fluctuations, while the southern hemisphere shows relatively strong fluctuations."*
- Hansen 2009: preferred direction at galactic (l, b) ≈ (226°, −17°); asymmetric model preferred over isotropic at 0.4% significance over ℓ=2–600; "none of our 9800 isotropic simulated maps show a similarly consistent direction of asymmetry over such a large multipole range."

The HPA preferred direction (l, b) ≈ (226°, −17°) is the **southern-ecliptic-power-rich** end. The catalog records `(237°, -20°)`. **The HPA gives the asymmetry that the AoE alignment alone cannot.**

### Three-reading structure for the AoE-HPA composite

#### Reading A — Standard cosmology

Under standard ΛCDM, the CMB is a single emission surface at z ≈ 1090, clock-time t ≈ 380 kyr post-Big-Bang. "Young" and "old" do not apply *per direction on the sky* in any standard sense. The HPA is a power-modulation anomaly; it is not interpreted as "one hemisphere is younger than the other." Most published explanations are non-temporal:

- Spatial inhomogeneity at the last-scattering surface (Frommert & Enßlin 2010 [0908.0453](https://arxiv.org/abs/0908.0453) considers polarisation discrimination; concludes the AoE alignment is consistent with chance at ~50%).
- Sachs–Wolfe contributions from local large-scale structure.
- Posterior-selection / look-elsewhere effects (Bennett et al. 2011).
- Residual instrumental systematics or foregrounds.

The "young hemisphere" reading has no standard-cosmology meaning. Documented as falsifier-baseline.

#### Reading B — MFO §VII.6.1 ring-down framing with HPA as discriminator

Under §VII.6.1: dark sector = ring-down accumulation = 95% of cosmic complexification settled into substrate residue (geometric curvature + complexification-cost ground state). "Young in ring-down completion" means *less of the complexification budget along that direction has settled*; "old in ring-down completion" means more.

The HPA observation: power at low ℓ is **higher in one hemisphere** (the southern-ecliptic) **and lower in the antipodal hemisphere** (northern-ecliptic), persisting across ℓ=2–600. Under the ring-down reading, two candidate mappings exist:

- **Candidate B1 — "more power = less ring-down."** Active ring-up content carries observable power (the visible-matter 5%; modes still coupled to active complexification); ring-down accumulation is dissipated into the dark sector and does not produce CMB temperature fluctuations directly. Therefore the *high-power* hemisphere is the *less ring-down complete = younger* hemisphere; the *low-power* hemisphere is *more ring-down complete = older*. This reading is consistent with the §VII.6 framing where Ω_Λ (dark energy / complexification cost) is the ring-down ground state and does not source CMB temperature perturbations.
- **Candidate B2 — "more power = more residual substrate-structure."** If ring-down accumulation produces residual geometric-curvature features (§VII.5 dark matter as residual curvature) that *do* source CMB perturbations via integrated Sachs–Wolfe / lensing-like effects, then more low-ℓ power = more residual ring-down structure = *older*. This reverses the assignment.

The two readings disagree on the direction of the young↔old assignment. The discriminator is **whether ring-down residue sources CMB temperature anisotropy or not** — a question §VII.5 / §VII.6 / §VII.6.1 do not currently resolve, because the dark matter halo profile / rotation curve / ISW computation is the explicit open problem (§VII.5 last paragraph: "the quantitative match … is the open computation").

**The honest assessment:** Reading B1 is the more natural fit with §VII.6.1's claim that the dark sector is the ring-down *ground state* (Ω_Λ = const, complexity-maintenance cost; not a perturbation source). Reading B2 would require ring-down accumulation to carry distinguishable spatial features at the CMB last-scattering surface, which is closer to the §VII.5 "geometric curvature" reading but at much higher redshift than the standard CDM-distribution claim. Both readings are internally consistent with portions of §VII; neither is forced by the current framework state.

Under Reading B1: **the southern-ecliptic hemisphere (l, b) ≈ (237°, −20°), where power is higher, is the less ring-down complete = younger hemisphere** in substrate-internal time. The northern-ecliptic antipode is the more ring-down complete = older hemisphere.

#### Reading C — Composite AoE + HPA + Cold Spot under the framework

The geometry is intriguing if not load-bearing:

- AoE pole at (240°, 60°) → AoE antipole at (60°, −60°)
- HPA high-power pole at (226°, −17°) → HPA low-power pole at (46°, +17°)
- Cold Spot at (210°, −57°)

The AoE *pole* (high galactic latitude north) and HPA *high-power direction* (slightly southern galactic latitude) are within ~80° of each other but not coincident. The Cold Spot is offset from the AoE antipole by ~30°. The literature (Schwarz et al. 2016 §4) treats the "low-ℓ axis family" as related but not identical; whether they are independent statistical accidents or share an underlying cause is genuinely open.

Under Reading B1 with the HPA-as-discriminator interpretation: the *Cold Spot near the AoE antipole* would be a localised feature in the more-old hemisphere — older substrate residue with a localised deeper-than-expected feature. The Vielva et al. 2004 Cold Spot interpretation literature already includes the "cosmic supervoid" reading (Szapudi et al. 2015 ISW signature from a void); a void in the substrate is consistent with a more-ring-down-complete region (less active complexification structure remaining in that direction). This is candidate framing only; the §VII.5 / §VII.6 quantitative computation that would test it is open.

### Resolution

The user's "antipodal very young spots" question has substantive content **only if** the AoE is composed with an asymmetry observation (HPA) that breaks the pole/antipole degeneracy. Under that composition and Reading B1:

- **Younger hemisphere (less ring-down complete):** southern-ecliptic, HPA high-power, roughly along galactic (l, b) ≈ (237°, −20°).
- **Older hemisphere (more ring-down complete):** northern-ecliptic, HPA low-power antipode, with the canonical Cold Spot offset by ~30° as a localised deeper feature consistent with a more-ring-down-complete region.

**Falsifier (Reading B2 inversion):** if §VII.5's residual-geometric-curvature reading does source distinguishable CMB temperature perturbations via ISW-like mechanisms, the assignment reverses (high-power = more ring-down residue = older). The §VII.5 quantitative-match open computation is the discriminator. Until that computation is run, both directions are framework-consistent.

---

## Q4 — Dark-sector content from the AoE perspective

### What the user is asking, sharpened

The headline question — "see what dark sector content looks like from that perspective" — admits two readings:

1. **Empirical:** does the AoE preferred direction correlate with any observed large-scale-structure / dark-matter halo / cosmic-web feature?
2. **Framework:** under §VII.6.1's ring-down framing, what does the dark sector's spatial distribution along the AoE axis look like?

Both are addressed; the empirical reading honestly has no clean published mapping.

### Reading A — Empirical large-scale-structure correlation with AoE direction

Searches for LSS / cosmic-web / dark-matter-halo alignment with the AoE direction have a mixed published record. The literature reviewed includes:

- **Schwarz et al. 2016 review** ([1510.07929](https://arxiv.org/abs/1510.07929)): the AoE preferred direction is *not* aligned with the cosmic supergalactic plane in any cleanly published statistical sense. The dipole-direction alignment is with the local-frame solar motion (CMB dipole = our motion through the rest frame), not with a cosmologically-distinct direction.
- **Frommert & Enßlin 2010** ([0908.0453](https://arxiv.org/abs/0908.0453)): polarisation independent probe is consistent with chance at ~50% level, weakening cosmological-origin readings.
- **Cold Spot as cosmic supervoid** (Szapudi et al. 2015, MNRAS 450, 288): a void of radius ~200 Mpc at z ≈ 0.2 in the direction of the Cold Spot is consistent with ISW signature; not strictly along the AoE axis but in the same low-ℓ-anomaly family.

The honest answer: **there is no published, statistically-significant LSS-alignment-with-AoE result that the framework can cleanly anchor against.** The AoE's most-significant additional alignment is with solar-system-frame references (ecliptic / dipole / equinox), not with cosmological LSS — which is exactly what makes it suspicious-of-systematics under the Bennett 2011 reading and exactly what makes it intriguing-as-substrate-frame-feature under the MFO reading.

> **Open thread (fermata for conductor):** an LSS-cross-correlation literature pass beyond the Frommert–Enßlin / Schwarz–review level would need WebSearch / scholarly database access beyond what this dispatch covers. The concertmaster's brief originally referenced a Pereira et al. 2008 arXiv:0710.4099 paper that turned out to be unrelated (Bohmian mechanics) — the citation in the dispatch brief was mis-attributed. The actual Pereira-Boehmer-Mota-style LSS-alignment literature exists but verifying specific papers would require a follow-up dispatch.

### Reading B — Framework: dark-sector spatial distribution along AoE axis

Under §VII.6.1, the dark sector (Ω_dark = 0.949) is ring-down accumulation: dark matter as residual geometric curvature (§VII.5), dark energy as complexification-cost ground state (§VII.6). The *spatial distribution* of the dark sector at present epoch is what observational cosmology already maps (lensing surveys, galaxy-cluster catalogs, BAO, etc.) — and that distribution does *not* show a published AoE-aligned anomaly.

The framework's claim, under §VII.6.1 + the Q3 Reading B1 composition:

- **Bulk distribution:** the dark sector is *isotropic at LSS scales* in standard cosmology, modulo well-mapped fluctuations. Under §VII.6.1 this isotropy is the substrate-side statement that ring-down accumulation is approximately uniform on cosmological scales.
- **Anisotropy at the CMB-low-ℓ scale (this is where the AoE lives):** would correspond, under Reading B1, to a *hemispheric asymmetry in ring-down completion at the largest spatial scales accessible to observation* — exactly what the HPA reports, at exactly the angular scales where the AoE alignment lives.
- **The dark sector "as seen from the AoE axis":** under Reading B1, looking *along* the AoE axis you see the substrate in its bundle-base-preferred-direction (per §VII.4.1.1's Hopf-bundle / Casimir-decomposition framing). Looking *across* the AoE axis you see the two hemispheres of differential ring-down completion (per HPA). The Cold Spot is a localised deeper-feature in the more-old hemisphere.

This is a **candidate framing** under §VII.6.1 commitments. It is not endorsed over the standard "AoE is a statistical fluke + galactic-foreground residual + posterior-selection effect" reading; the framework provides *one possible* substrate-side interpretation if the AoE turns out to be real and not systematics.

### Resolution

The user's "what does dark sector content look like from the AoE perspective?" question has:

- **Empirical answer:** no published LSS-with-AoE alignment of statistical significance; the dark sector at LSS scales is approximately isotropic. The AoE's additional alignments are with solar-system-frame references, not LSS.
- **Framework answer (candidate B1):** the AoE marks the *preferred bundle-base direction* in the substrate at CMB-low-ℓ scales; the HPA marks the asymmetric ring-down-completion along that axis; the Cold Spot is a localised more-old-substrate feature near the AoE antipole. All three are the visible-shadow of a substrate-level bundle-geometry anisotropy at the largest angular scales accessible to observation.

The candidate framing dissolves the AoE-Cold-Spot-HPA "low-ℓ anomaly family" into a single substrate-level preferred-direction-with-asymmetry feature; it does not falsify standard ΛCDM (which can absorb all three as posterior-selection effects per Bennett 2011) but offers an alternative reading internally consistent with §VII.4.1.1 + §VII.5 + §VII.6 + §VII.6.1.

---

## Verdict

- **Q1 verified.** AoE = alignment of ℓ=2,3 multipole vectors at axis (l, b) ≈ (240°–260°, 60°), with secondary alignment to ecliptic+dipole+equinox at ~99.9% C.L. (Schwarz 2004; Land–Magueijo 2005). Re-confirmed at Planck PR3 (Akrami 2020). Significance is test-dependent; skeptical baseline is Bennett 2011 (posterior selection).
- **Q2 resolved.** AoE is neither hot nor cold spot — it's a directional axis. The Cold Spot is a separate anomaly at (210°, −57°). The "hot/cold" framing inside the AoE story comes from the *local extrema* aligned by the quadrupole+octopole along the ecliptic, but the AoE itself is the axis, not a pole.
- **Q3 has substantive content** *only* when the AoE is composed with the HPA, which breaks the pole/antipole degeneracy. Under §VII.6.1 Reading B1 (more low-ℓ power = less ring-down complete = younger), the southern-ecliptic hemisphere (l, b) ≈ (237°, −20°) is younger; the northern-ecliptic antipode is older; the Cold Spot is a localised more-old feature near the AoE antipole. **Reading B2 (more power = more ring-down residue = older) is the alternate framework-consistent reading;** the §VII.5 quantitative-match open computation is the discriminator. Both stand as framework-consistent candidate readings.
- **Q4 partially answered.** Empirically, no published LSS-with-AoE alignment of significance; framework-side, the AoE is a candidate preferred-bundle-direction in §VII.4.1.1's Hopf-bundle / spherical-compression framing, with HPA giving the asymmetry along the axis. **Open thread on LSS-cross-correlation literature** flagged as fermata for the conductor.

---

## What this changes

- The AoE is now linkable to §VII.6.1's ring-down framing **via the HPA composition**, not on its own. The AoE alone is an axis (pole+antipole symmetric); the HPA gives the asymmetric direction that "young vs old in ring-down completion" needs.
- Under §VII.4.1.1's spherical-compression / Hopf-bundle reading, the AoE is naturally a preferred-bundle-base direction. This is *one candidate* framing; not endorsed over standard-ΛCDM-plus-systematics.
- The "low-ℓ anomaly family" (AoE + Cold Spot + HPA + low quadrupole + parity asymmetry + missing large-angle correlation, per the project's `cmb_anomalies` catalog) admits a unified candidate reading as: a single substrate-level preferred-direction-with-asymmetry feature, projected to the CMB last-scattering surface, with the various anomalies being different statistical-test projections of the same underlying bundle-geometry feature.

## What this does not change

- **No GR / ΛCDM prediction is altered.** Standard observational analyses remain valid; this is an interpretive reading of what those analyses are *of*.
- **Bennett 2011 skeptical baseline stands.** The candidate framing here does not refute the posterior-selection critique; it offers an alternative for the case where the anomalies turn out to be real after systematics control.
- **Frommert–Enßlin 2010 polarisation independent-probe** is consistent with chance; if reinforced by Planck PR3 polarisation analyses (Akrami 2020 "no unambiguous detections" in polarisation), the cosmological-origin reading weakens, and with it this candidate framework reading.
- **§VII.5 quantitative-match open computation** remains the discriminator between Reading B1 and Reading B2; running that computation is the load-bearing next step, not modifying §VII.6.1.

---

## Falsifier list

1. **Planck PR4 / future-mission polarisation re-confirms the AoE in polarisation** (i.e., reverses Frommert–Enßlin 2010's 50%-chance reading): strengthens the cosmological-origin claim and with it the framework reading.
2. **§VII.5 residual-geometric-curvature computation distinguishes Reading B1 vs B2:** the dark-matter halo profile / rotation curve / ISW match resolves whether ring-down residue sources CMB-temperature perturbations or not. This is the explicit `[[user_stance_dark_sector_ring_down_age]]` falsifier path.
3. **LSS cross-correlation with AoE direction:** a future high-precision survey (Euclid, Roman, LSST) cross-correlating large-scale galaxy distribution with the AoE axis would either find or not find a corresponding LSS preferred direction. Null result → framework reading downgraded to "no longer requires substrate-bundle-direction"; positive result → strong evidence for the bundle-direction reading.
4. **The HPA persists to higher ℓ in PR4+ but the AoE does not:** would weaken the AoE-HPA composition reading (they would be distinct anomalies in different ℓ regimes, not a single substrate feature).

---

## Proposed notebook integration

> **Concertmaster draft only; conductor decides whether to land in §VII.6.2 or as inline expansion of §VII.6.1, or to defer until §VII.5 quantitative-match computation converges.**

Draft §VII.6.1.1 (candidate) — *"AoE / HPA / Cold Spot as bundle-direction signature of the dark-sector ring-down"*:

> The CMB large-scale anomaly family (Axis of Evil quadrupole-octupole alignment per de Oliveira-Costa et al. 2004 / Land–Magueijo 2005; Hemispherical Power Asymmetry per Eriksen et al. 2004 / Hansen et al. 2009; Cold Spot per Vielva et al. 2004 / Cruz et al. 2005) admits **one candidate substrate-side reading** under §VII.6.1's ring-down framing composed with §VII.4.1.1's spherical-compression / Hopf-bundle structure. The AoE marks a preferred bundle-base direction at galactic (l, b) ≈ (240°, 60°); the HPA breaks the pole/antipole degeneracy by reporting more low-ℓ power in the southern-ecliptic hemisphere (l, b) ≈ (237°, −20°); under the "more power = less ring-down complete = younger substrate" reading, the southern-ecliptic hemisphere is the younger end of the AoE axis and the Cold Spot near the AoE antipole is a localised more-ring-down-complete substrate feature. The reading is one candidate among several (the standard ΛCDM-plus-systematics reading remains valid per Bennett et al. 2011), it does not modify any GR prediction, and the §VII.5 residual-geometric-curvature quantitative-match open computation is the discriminator. Full empirical workings + reference verification: [`research-mfo/axis_of_evil_ring_down_framing_2026-05-16.md`](research-mfo/axis_of_evil_ring_down_framing_2026-05-16.md).

Cross-references would mirror §VII.6.1's set: shadow-stance family + §VII.4.1.1 + §VII.5 + §VII.6 + §VII.6.1 + the cmb_anomalies catalog rows.

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
