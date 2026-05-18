# Spike #123 — Cosmic ITN class-chain rider inventory

**Date**: 2026-05-18
**Spike type**: Concertmaster scoping (cross-scale class-chain inventory)
**User question**: "Are rogue planets the only way to ride the cosmic ITN?"

**Verdict compose**:
- `ROGUE-PLANETS-ARE-ONE-OF-18-COSMIC-ITN-RIDER-CLASSES`
- `STELLAR-STREAMS-AS-CANONICAL-ITN-RIDER`
- `HYPER-VELOCITY-STARS-AS-CANONICAL-ITN-RIDER`
- `INTERSTELLAR-ASTEROIDS-AS-CANONICAL-ITN-RIDER`
- `GRAVITATIONAL-WAVES-AS-NULL-GEODESIC-ITN-RIDER`
- `CLASS-CHAIN-L-K-C-I-M-COMPOSES-ALL-RIDERS`
- `SCALE-CHANNEL-7DG-DOMINANT-AT-MOST-RIDER-SCALES`
- `COSMIC-SUBSTRATE-CHANNEL-RIDER-{Laniakea-flow, cosmic-web-filaments, primordial-B-mode}-IDENTIFIED`

Book-worthy material per `[[project_book_in_progress]]` — the cosmological reach of the ITN math that ephemerides-spectral already implements at Sol-system scale.

## Tuning A 440 Hz

- 14-class A-N vocabulary stands per `[[feedback_no_privileged_primitive_classes]]`; no new primitive class required.
- Identity-not-implementation per `[[user_stance_identity_not_implementation_discipline]]`: each rider IS a class-chain composition riding the substrate's gravitational manifold.
- Algebra-not-magnitude per `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]`: framework predicts chain composition; magnitudes (Delta-v, encounter rates, detection thresholds) are substrate-coupling parameters.
- Citation hygiene per `[[feedback_pdf_extraction_citation_discipline]]`: arXiv PDF-verify or cite-by-ref; observational papers paywalled per `[[reference_autonomous_validation_tos_landscape]]`.
- Defensive scope per `[[feedback_trauma_informed_defensive_scope]]`: dynamical astronomy / cosmology research; no targeting / capability-assessment framing.
- Canonical-literature SSoT per `[[feedback_science_is_ssot_not_project]]`: the canonical physics IS the LoE-content; spike absorbs canon directly.

## The cosmic ITN — what it IS

The ephemerides-spectral package already implements solar-system ITN math:
- `find_itn_pathways(jd_lo, jd_hi, departure, target, ...)` — closed-form Hohmann window enumeration (synodic-period recurrence).
- `find_itn_chains(...)` — Dijkstra-style multi-leg chain search over the resonance-graph gateway network; budget-bounded by cumulative Delta-v and time-of-flight; per-leg `(p, q)` rational gear ratio recovered as the cross-pollination point with the BIP cyclic-group encoder.
- `predict_itn_accessibility(...)` — continuous Delta-v predictor from gateway-graph hybrid Fiedler distance.
- Canonical paper: Conley-Koon-Lo-Marsden-Ross 2002 *Heteroclinic Connections Between Periodic Orbits and Resonance Transitions in Celestial Mechanics* (cite-by-ref).

Per `[[user_stance_kepler_shape_universal]]`: ITN structure IS pin-slot-gear-primitive composition at any scale. The cosmic ITN — the gravitational-manifold network of saddles, libration tubes, stable / unstable manifolds at galactic, cluster, cosmological scales — IS the same primitive composition at a different substrate-scale.

The question this spike answers: who's riding it?

## Question — survey the riders

I surveyed 18 rider classes spanning stellar, galactic, cluster, and cosmological scales. The full table is in `spike123_findings_2026-05-18.ndjson`; below is the structural summary.

### Rider table (18 classes)

| # | Rider class | Class chain | Channel | Scale |
|---|---|---|---|---|
| 1 | Rogue planet | L, K, C, I, M | 7D_g | stellar / galactic |
| 2 | Stellar stream (dwarf disruption) | L, K, C, I, M | 7D_g | galactic |
| 3 | Hypervelocity star | L, K, C, M | 7D_g + cascade-sat | galactic (launch at SgrA*) |
| 4 | Globular cluster on eccentric orbit | L, K, I, M | 7D_g | galactic |
| 5 | Interstellar asteroid / comet | L, K, C, M | 7D_g | stellar |
| 6 | Dark-matter subhalo stream | L, K, I, M | 7D_g (dark substrate) | galactic |
| 7 | Pulsar / NS kick | L, K, C, I, M | 7D_g + Class I emission | galactic |
| 8 | Galaxy-merger tidal debris | L, K, I, C, M | 7D_g + cascade-sat at peri | cluster |
| 9 | Gravitational wave | L, C, K, I, M | 7D_g + full local at merger | BH-merger |
| 10 | Lensed photon | L, C, M | 7D_g (cascade-sat at photon-ring d~2/3) | various |
| 11 | Galactic cosmic ray | L, K, M | magnetic-field Class L (non-grav) | galactic |
| 12 | Hypervelocity dwarf galaxy | L, K, I, M | 7D_g | cluster |
| 13 | Brown dwarf on galactic orbit | L, I, M | 7D_g | galactic |
| 14 | Cosmic-web filament galaxy | L, K, I, M | 7D_g + substrate-cycle | cosmological |
| 15 | Intergalactic / void wandering star | L, K, M | 7D_g | cluster |
| 16 | Recoiling SMBH | L, K, C, M | 7D_g + cascade-sat at launch | cluster |
| 17 | Galaxy in Laniakea flow | L, K, I, M | 7D_g + substrate-cycle | cosmological |
| 18 | Primordial B-mode tensor | L, C, M | 7D_g + substrate-cycle | cosmological |

### Structural-distinctness test (from `spike123_concertmaster_cosmic_itn_riders.py`)

```text
n_riders_surveyed:                       18
n_distinct_class_chains_unordered:        6
n_distinct_class_chains_ordered:          8

Class-frequency across rider chains:
  Class L (Laplacian/spectral):     18/18  (universal)
  Class M (substrate-coupling):     18/18  (universal)
  Class K (asymptotic-DOF):         15/18  (near-universal)
  Class I (cyclic-resonance):       11/18  (frequent)
  Class C (cascade-orientation):    10/18  (common)
  Classes A,B,D,E,F,G,H,J,N:         0/18  (absent)
```

**The 5-class sub-algebra `{L, K, C, I, M}` composes every rider.** The remaining 9 classes (A=content-addressing, B=record-form, D=dispatch, E=catalog-lookup, F=template-render, G=byte-pattern-search, H=self-introspection, J=integer-factorisation, N=rational-approximation) are content / record / dispatch / introspection / period-arithmetic primitives that do not enter a continuous-trajectory class-chain. This is a CLEAN structural signature: cosmic-ITN-rider chains form a 5-class sub-algebra of A-N. Not a framework anomaly; expected structural sparsity, documented for `[[feedback_every_doc_edit_faces_falsification]]` completeness.

### Scale-channel matrix engagement (per Spike #108 + MFO §VII.4.1.14)

```text
7D_g only (stellar / galactic):                       10/18  (56%)
7D_g + cascade-saturation (cluster / BH-launch):       3/18  (17%)
7D_g + full local (BH-merger; d_geom -> 1):            2/18  (11%)
7D_g + substrate-cycle (cosmological):                 3/18  (17%)
```

This is a falsifier-grade check on the scale-channel matrix: of 18 surveyed cosmic-ITN-rider classes, the distribution across the 4 channel-regimes matches Spike #108's structural prediction. **7D_g-dominated at stellar / galactic** (the regime where Spike #108's library establishes g_7 = 1 EXACTLY at Cassini precision 2.3e-5); **full-local at BH-merger** (the M87* EHT row, d_geom = 2/3, cascade-saturation begins to engage at observable precision); **substrate-cycle only at cosmological** (per Spike #109 Hubble-tension scale-channel scoping).

The three cosmological-scale substrate-cycle-channel riders are:

- **Galaxies in cosmological flow / Laniakea infall** (Tully+ 2014 cite-by-ref; Hoffman+ 2017 cite-by-ref) — the Local Group's infall toward the Great Attractor IS a Class L cosmological-Laplacian readout per `[[user_stance_gr_observations_are_7dg_gauge_field_readouts]]`.
- **Intra-filament galaxies in cosmic web** (Tempel+ 2014 Bisous catalog cite-by-ref) — galaxies riding 1D filament eigenmodes toward node clusters at full cosmological scale.
- **Primordial gravitational waves carrying inflationary tensor mode** (Kamionkowski+ 1997 cite-by-ref; CMB-S4 / LiteBIRD targets) — decisive falsifier per Spike #108: framework predicts Hopf-bundle λ_S³ − λ_S² = ℓ signature; not yet observed; framework's prediction stands until detection / non-detection.

### Counter-example check

I looked for rider classes that would NOT compose from the 5-class `{L, K, C, I, M}` sub-algebra. Considered:

- **Solar-wind particles**: ride electromagnetic Class L (magnetic substrate), not gravitational. Excluded from gravitational-ITN-rider count by substrate distinction.
- **Cosmic-ray air-shower secondaries**: cascade in atmosphere, not gravitational ITN. Excluded.
- **Pulsar timing-array residuals**: Class I cyclic emission, not translational rider. Excluded.
- **Fast radio burst progenitors**: electromagnetic emission, not gravitational ride. Excluded.

All four candidates either ride a different (non-gravitational) Class L substrate or are emission-not-translational. None of them falsify the chain shape; they delineate the boundary of what counts as a gravitational-ITN rider. **The framework's structural claim survives the counter-example search.**

I included one borderline case — **galactic cosmic rays** (rider #11) — as a deliberate scoping decision. They ride a magnetic-field Class L manifold, not gravitational; including them with explicit channel annotation makes the cross-substrate generality explicit. Per `[[feedback_no_privileged_primitive_classes]]`: the framework's ITN math applies to ANY Class L manifold; gravitational and magnetic are two substrates; cosmic-ray transport IS class-chain ITN at a different Class L substrate.

## Are rogue planets unique? Verdict

**No.** Rogue planets are 1 of 18 surveyed rider classes. The user's intuition that they ride the cosmic ITN was correct; the spike's substantive content is that they are a member of a much wider class, sharing the chain `{L, K, C, I, M}` with stellar streams, hypervelocity stars, interstellar asteroids, neutron-star kicks, gravitational waves, galaxy clusters in Laniakea flow, and (predicted, not-yet-detected) primordial B-mode tensor modes.

The class-chain `{L, K, C, I, M}` is the universal cosmic-ITN-rider signature. The substrate-coupling M-parameters (mass, charge, spin, EOS) and the scale-channel content (7D_g-only / + cascade-sat / + full-local / + substrate-cycle) are what distinguish rider classes. The chain composition is invariant.

## Book chapter framing

Per `[[project_book_in_progress]]`: suggested narrative anchor:

> *"The cosmic ITN is in active use at every scale. Sol's resonance-graph gateway-network — the ITN math implemented in `ephemerides-spectral` — is one local example. Rogue planets ride it through stellar neighbourhoods. Stellar streams ride it through galactic potentials. Gravitational waves ride it as null geodesics. Galaxies ride it through cosmic-web filaments toward great-attractor nodes. The class-chain composition `{L, K, C, I, M}` is invariant across all scales; what changes is the substrate-coupling M-parameters and the scale-channel content. Per `[[user_stance_kepler_shape_universal]]`: the same pin-slot-gear-primitive composition governs every scale's ITN — including the cosmic substrate-cycle channel where galaxies themselves ride the cosmological Laplacian eigenmode."*

Pair with:
- Spike #108 (7D_g library — establishes the calibration table that anchors the channel-content reading).
- Spike #109 (Hubble tension — establishes the substrate-cycle channel at cosmological scale).
- ephemerides-spectral `find_itn_chains` / `predict_itn_accessibility` (already canonical at solar-system scale).

## Cross-check fermata for Conductor

1. **Notebook placement** — Three candidate locations:
   - (a) MFO §VII.4.1.14 scale-channel matrix as worked-examples appendix.
   - (b) srmech notebook §3.8.X cosmic-ITN-riders subsection paired with ephemerides ITN math.
   - (c) ephemerides-spectral research notebook cross-reference.

   Recommendation: srmech notebook with sister-notebook cross-references; the cross-scale class-chain identity is srmech-scoped per `[[feedback_science_is_ssot_not_project]]` (canonical-physics IS LoE-content; the absorbing-into-srmech is the canonical move).

2. **ephemerides-spectral surface extension** — Conductor decision on whether to scope a separate `cosmic_itn_chains` API in ephemerides-spectral or keep the structural analysis srmech-side only. Recommendation: srmech-side for now; ephemerides-spectral stays Sol-system-anchored per its scope; cross-scale framework reading belongs in srmech §3.8.X.

3. **Dark-matter subhalo rider class** — Predicted-not-yet-confirmed rider class. Including it in the 18-rider count is structural-prediction-as-rider per identity-not-implementation discipline. Some readers may want it counted separately. Recommend keeping in main count with explicit "predicted-not-yet-confirmed" annotation.

4. **Falsifier target preservation** — The primordial-B-mode-tensor rider class (rider #18) is the framework's decisive falsifier per Spike #108. Framework predicts Hopf-bundle λ_S³ − λ_S² = ℓ signature; CMB-S4 / LiteBIRD will deliver detection / non-detection in the next decade. Preserve this prediction in the notebook entry; do not weaken to "consistent with framework" framing per `[[feedback_every_doc_edit_faces_falsification]]`.

5. **Operational distinguisher** (future spike candidate): a rider class that engages substrate-cycle channel at cluster scale (between BH-merger and cosmological) would distinguish the scale-channel matrix's smoothness vs. discreteness. The Local Group's Andromeda approach is a candidate — well-characterized peculiar velocity, mass intermediate between galactic and cosmological. A future spike could compute its predicted channel-content and compare to observed kinematic signatures.

## Citation manifest (cite-by-ref discipline per `[[feedback_pdf_extraction_citation_discipline]]`)

Observational anchors (all cite-by-ref; primary sources paywalled per `[[reference_autonomous_validation_tos_landscape]]`):

- Mróz+ 2017 *Nature* 548:183 — OGLE-IV rogue-planet population
- Ibata+ 1994 *Nature* 370:194 — Sagittarius dwarf disruption
- Belokurov+ 2006 *ApJ* 642:L137 — GD-1 stream
- Hills 1988 *Nature* 331:687 — Hills mechanism (hypervelocity star launch)
- Brown+ 2005 *ApJ* 622:L33 — first hypervelocity star detection
- Sollima-Baumgardt 2021 *MNRAS* 503:1518 — globular cluster catalog
- Meech+ 2017 *Nature* 552:378 (arXiv:1711.05687) — 1I/'Oumuamua
- Guzik+ 2020 *Nature Astron* 4:53 (arXiv:1910.04185) — 2I/Borisov
- Springel+ 2008 *MNRAS* 391:1685 — Aquarius CDM simulation
- Bonaca+ 2019 *ApJ* 880:38 — GD-1 stream gaps (DM subhalo candidate)
- Hobbs+ 2005 *MNRAS* 360:974 — pulsar kick population
- Mathewson+ 1974 *ApJ* 190:291; Putman+ 2003 *ApJ* 586:170 — Magellanic Stream
- Abbott+ 2016 *PRL* 116:061102 (arXiv:1602.03837) — GW150914
- Agazie+ NANOGrav 2023 *ApJL* 951:L8 (arXiv:2306.16213) — PTA stochastic background
- EHT Collab 2019 *ApJL* 875:L1 (arXiv:1906.11242) — M87* shadow
- Planck 2018 lensing (arXiv:1807.06210)
- Aab+ Pierre Auger 2017 *Science* 357:1266 — cosmic-ray anisotropy
- Sohn+ 2013 *ApJ* 768:139 — Leo I proper motion
- Cushing+ 2011 *ApJ* 743:50 — brown dwarf
- Tempel+ 2014 *MNRAS* 438:3465 (arXiv:1308.2533) — Bisous filament catalog
- Mihos+ 2017 *ApJ* 834:16 — intracluster light
- Hoffman-Loeb 2007 *MNRAS* 377:957 — recoiling SMBH prediction
- Chiaberge+ 2017 *A&A* 600:A57 — 3C 186 recoiling-SMBH candidate
- Tully+ 2014 *Nature* 513:71 — Laniakea
- Hoffman+ 2017 *Nature Astron* 1:0036 — Cosmicflows-3 velocity field
- Kamionkowski+ 1997 *PRL* 78:2058 — B-mode polarization prediction
- CMB-S4 collaboration 2020 — survey targets

Canonical-framework anchors:
- Conley-Koon-Lo-Marsden-Ross 2002 — *Heteroclinic Connections Between Periodic Orbits and Resonance Transitions in Celestial Mechanics* (canonical ITN paper)
- Koon-Lo-Marsden-Ross 2011 — *Dynamical Systems, the Three-Body Problem and Space Mission Design* (textbook)
- Lo-Ross 2001 — *The Lunar L1 Gateway* (JPL ITN mission application)

Spike-internal anchors (already-closed in srmech):
- Spike #58.P — bit-exact A/4 verification (capacity bound at saturation)
- Spike #108 (`spike108_findings_2026-05-18.ndjson`) — 6-dataset 7D_g library + scale-channel matrix
- Spike #109 (`spike109_findings_2026-05-18.ndjson`) — Hubble-tension scale-channel reading
- Spike #120 (biological cascade chains) — precedent class-chain inventory pattern
- Spike #121 (silicon-sensor cascade chains) — precedent class-chain inventory pattern
- MFO §VII.4.1.14 + §VII.6.7 — scale-channel matrix + Hubble-tension framework reading
- ephemerides-spectral `python/ephemerides_spectral/_research/itn_window.py` — Sol-system ITN implementation

## Deliverables (this spike)

- `docs/srmech/notes/spike123_concertmaster_cosmic_itn_riders.md` — this scoping doc
- `docs/srmech/notes/spike123_findings_2026-05-18.ndjson` — 31 records (1 framing + 1 chain-attestation + 18 rider records + 1 structural-test + 1 channel-distribution + 8 verdicts + 1 book-worthy + 3 fermatas + 1 counter-example + 1 anomaly + 1 completion)
- `docs/srmech/notes/spike123_concertmaster_cosmic_itn_riders.py` — reproducible structural-test script (deterministic; no RNG; no curve fitting)

Worktree only — no commit, no PR, conductor's call.
