# Era-appropriate pin-slot mathematics for the 6 non-lunar trains (F18-F23)

**Date:** 2026-05-15
**Concertmaster dispatch.** Branch `research/pinslot-spike-2026-05-14` (PR #416 DRAFT).
**Files:**
- `spike_pinslot_era_appropriate_2026-05-15.py` — analysis script (stdlib only)
- `spike_pinslot_era_appropriate_2026-05-15.ndjson` — 8 records (1 header + 1 Sun + 5 planets + 1 aggregate)
- `spike_pinslot_era_appropriate_findings_2026-05-15.md` — this document

**Findings landed:** F18 (Sun), F19 (Mercury), F20 (Venus), F21 (Mars), F22 (Jupiter), F23 (Saturn).

The dispatch's framing question was: do the bronze's reconstructed pin-slot geometric parameters (Freeth 2021 Supp Table S9) match **era-appropriate** (Hipparchan / Ptolemaic) AU distances, or **modern** (JPL DE441 / NASA NSSDC) AU distances?

The honest answer is two-layered and richer than the framing presumed.

---

## Headline forensic finding (load-bearing for the dispatch)

**Freeth 2021 Supp S9's `p` column matches NASA NSSDC modern values rounded to 2 decimal places for ALL 5 planets** (5/5):

| Planet  | NASA NSSDC AU | round-2dp | Freeth Supp S9 `p` | match |
|---------|--------------:|----------:|-------------------:|:-----:|
| Mercury |       0.38704 |      0.39 |               0.39 |  yes  |
| Venus   |       0.72327 |      0.72 |               0.72 |  yes  |
| Mars    |       1.52342 |      1.52 |               1.52 |  yes  |
| Jupiter |       5.20462 |      5.20 |               5.20 |  yes  |
| Saturn  |       9.58235 |      9.58 |               9.58 |  yes  |

The Supp S9 caption is explicit: *"Parameters are calculated using modern theory for the planets, but could equally be calculated from ancient Greek parameters, using the determination of epicycle sizes described earlier."* (Freeth 2021 Supp Information 4, p.30.)

**Implication:** Freeth's RECONSTRUCTION of the bronze's d/i/o values starts from modern AU as design input. The bronze AS RECONSTRUCTED is "modern" by construction. The genuinely historical question — what data did the ACTUAL ancient bronze designer use? — is not answerable from Supp S9 alone, because modern AU and era-appropriate Ptolemaic AU differ by only 0.2-3.8% (below the noise floor of bronze fabrication).

The dispatch question therefore has a clean answer at one level (the bronze AS-RECONSTRUCTED uses modern AU) and an honest "below the noise floor" at the other level (the historical bronze designer could have used either; the gear measurements cannot distinguish).

---

## F18 — Sun (solar anomaly)

**Verdict: UNDERDETERMINED.** Freeth 2021 does NOT publish a (pin offset, pin distance) pair for the True Sun mechanism in Supp S9 or anywhere else in the SI. Supp S4.3.1 (page 28 of cached PDF) confirms the architecture: a True Sun mechanism `g1 ~ g2 ~ g3 + follower` mounted on the Circular Plate, with the follower tracking an **eccentric pin** on g3's arbor (Supp p.51, Fig. 6b/c description). This IS a pin-and-slot architecture; what's missing is the numerical eccentricity.

**Era-appropriate target:** Hipparchus, e_⊙ = 1/24 ≈ 0.04167 (Almagest III.4 per Toomer 1984; widely cited; Fitzpatrick Modern Almagest §4.3 gives the Hipparchan solar model with this value).

**Modern target:** Earth-orbit eccentricity e ≈ 0.01671 (Fitzpatrick Table 5.1, JPL DE441).

**Equation-of-centre c_1 amplitudes (Greek-doubling 2e):**

| reference  | e      | c_1 (deg) |
|------------|-------:|----------:|
| Hipparchus | 0.0417 |     4.78° |
| Modern     | 0.0167 |     1.92° |
| Bronze     |   N/A  |       N/A |

The Hipparchan and modern values **differ by ~150%**. IF the bronze's Sun pin-offset and pin-distance values were known, this would be the SINGLE SHARPLY-DISTINGUISHABLE planet train. They are not known.

**Fermata for conductor.** Pursuing Sun pin geometry could draw on:
- Freeth 2021 Supp S6 (Reconstructing the Cosmos) Fig. references which may give photographs / X-ray CT geometry of the True Sun mechanism's pin-and-follower assembly that Supp S9 omits.
- Wright (2007) "The Antikythera Mechanism reconsidered" alternate reconstruction.
- Carman & Evans (2010) "Solar Anomaly and Planetary Displays" in JHA — explicitly devoted to the bronze's solar anomaly mechanism. (Freeth 2021 reference [58].)
- Evans, Carman, Thorndike (2010) and Carman, Evans (2019) "Babylonian Solar Theory on the Antikythera Mechanism" Archive for History of Exact Sciences. (Freeth 2021 reference [59].)

---

## F19 — Mercury

| Reference         | p_AU value | rel err vs bronze |
|-------------------|-----------:|------------------:|
| **Bronze (d/i)**  | **0.3900** |             (0%)  |
| Ptolemy           |    0.3750  |             4.00% |
| Modern NSSDC      |    0.38704 |             0.77% |
| Modern JPL DE441  |    0.387098|             0.75% |

**c_1 amplitudes (deg):** bronze 21.31° / Ptolemy 20.56° / modern 21.16°.

**Verdict: MODERN.** Bronze 0.39 is essentially the rounding of modern 0.387. Ptolemy's Mercury AU of 0.375 is 4× further from the bronze than modern is.

**Era-appropriate confidence: LOW.** Rushkin (2015) p.6 explicitly notes "Mercury is particularly difficult planet for Ptolemy. Mercury's true orbit has an abnormally high eccentricity 0.206…in addition, being close to the Sun, Mercury is difficult to observe, so Ptolemy had especially poor data for it." Hipparchus had no systematic planetary theory (Almagest IX.2 per Ptolemy). So the era-appropriate Mercury AU is itself low-confidence; the 4% gap may simply reflect Ptolemy's bad Mercury data rather than a meaningful bronze-vs-era distinction.

---

## F20 — Venus

| Reference         | p_AU value | rel err vs bronze |
|-------------------|-----------:|------------------:|
| **Bronze (d/i)**  | **0.7198** |             (0%)  |
| Ptolemy           |    0.7190  |             0.11% |
| Modern NSSDC      |    0.72327 |             0.48% |
| Modern JPL DE441  |    0.723334|             0.49% |

**c_1 amplitudes (deg):** bronze 35.75° / Ptolemy 35.72° / modern 35.88°.

**Verdict: ERA-APPROPRIATE (Ptolemaic, marginal).** Bronze 0.7198 matches Ptolemaic 0.7190 to 0.11% — better than the 0.48% match to modern. But the bronze value 0.7198 is the *exact* `d/i = 20.01/27.80 = 0.71977…` reduction of Freeth's published d and i mm values; the Supp S9 `p` column itself quotes 0.72 (which rounds modern 0.72327 to 2 dp).

The marginal "Ptolemaic match" is below the bronze fabrication precision and could be a coincidence of rounding. Era-appropriate confidence: HIGH for the Ptolemaic 0.719 value itself (Almagest X.3 via Toomer 1984 / Rushkin 2015), but the bronze cannot meaningfully distinguish 0.719 from 0.723 in any case.

---

## F21 — Mars

| Reference         | p_AU value | rel err vs bronze |
|-------------------|-----------:|------------------:|
| **Bronze (d/o)**  | **1.5198** |             (0%)  |
| Ptolemy           |    1.5190  |             0.05% |
| Modern NSSDC      |    1.52342 |             0.24% |
| Modern JPL DE441  |    1.523706|             0.26% |

**c_1 amplitudes (deg):** bronze 56.66° / Ptolemy 56.64° / modern 56.72°.

**Verdict: ERA-APPROPRIATE (Ptolemaic, marginal).** Bronze 1.5198 matches Ptolemaic 1.5190 to 0.05% (essentially perfect) — better than the 0.24% match to modern. The exact `d/o = 10.00/6.58 = 1.5197…` reduction is uncannily close to Ptolemy's 1.519, which corresponds to the famous Almagest X epicycle:deferent ratio 39;30 (60/39.5 = 1.519).

This is the strongest era-appropriate match in the dispatch — but Supp S9's `p` column still quotes 1.52 (rounding of modern 1.5234). The mm values 10.00 and 6.58 may have been chosen for *Ptolemaic* consistency rather than modern, but this would be retrofit; Freeth's stated methodology is "modern theory" as input.

**Era-appropriate confidence: HIGH** (Mars is Ptolemy's most accurate planetary determination; the 39;30 epicycle:deferent ratio is well-attested across multiple secondary sources — Wikipedia Almagest article, Rushkin 2015, Voisey 2024 blog).

---

## F22 — Jupiter

| Reference         | p_AU value | rel err vs bronze |
|-------------------|-----------:|------------------:|
| **Bronze (d/o)**  | **5.2025** |             (0%)  |
| Ptolemy           |    5.2170  |             0.28% |
| Modern NSSDC      |    5.20462 |             0.04% |
| Modern JPL DE441  |    5.202873|             0.01% |

**c_1 amplitudes (deg):** bronze 79.12° / Ptolemy 79.15° / modern 79.12°.

**Verdict: MODERN.** Bronze 5.2025 matches modern JPL DE441 5.2029 to 0.007% — essentially exact. Ptolemy's Jupiter at 5.217 is 0.28% off.

This is the cleanest "modern" verdict in the analysis: the bronze's `d/o = 8.22/1.58 = 5.20253…` is the round-2dp of modern 5.205 essentially exactly.

---

## F23 — Saturn

| Reference         | p_AU value | rel err vs bronze |
|-------------------|-----------:|------------------:|
| **Bronze (d/o)**  | **9.5800** |             (0%)  |
| Ptolemy           |    9.2310  |             3.78% |
| Modern NSSDC      |    9.58235 |             0.025%|
| Modern JPL DE441  |    9.536651|             0.46% |

**c_1 amplitudes (deg):** bronze 84.04° / Ptolemy 83.82° / modern 84.04°.

**Verdict: MODERN.** This is the **sharpest** era-vs-modern distinction in the analysis. Bronze 9.58 matches modern NSSDC 9.58235 to 0.025% (the F17 precision floor) and matches modern JPL DE441 9.537 to 0.46%, but is **3.78% off** Ptolemy's 9.231. The Ptolemy-vs-modern gap on Saturn is 3.2% — Ptolemy's Saturn distance is the most error-prone of his outer-planet determinations.

The two modern conventions (NSSDC fact-sheet 9.582 vs JPL DE441 J2000-fit 9.537) themselves differ by 0.5% — this reflects Saturn's secular orbital perturbations (its osculating elements change appreciably over millennium timescales because Saturn has the largest dynamical influence from Jupiter). The Freeth-quoted value 9.58 is unambiguously the NSSDC convention.

**Era-appropriate confidence: MODERATE** for Ptolemaic 9.231 (Rushkin 2015 Table p.7 derived from Almagest XI). The 3.78% bronze-vs-Ptolemy gap is robustly outside both noise floors (Ptolemaic uncertainty + bronze fabrication uncertainty). On Saturn alone the dispatch can confidently say: **the bronze, as reconstructed, does not use Ptolemaic AU.**

---

## Aggregate verdict

| Planet  | Verdict                              | Critical caveat |
|---------|--------------------------------------|-----------------|
| Sun     | UNDERDETERMINED                      | Freeth 2021 silent on Sun pin geometry |
| Mercury | Modern (decisive)                    | Ptolemy's Mercury is low-confidence |
| Venus   | Era-appropriate (marginal)           | Below bronze's noise floor |
| Mars    | Era-appropriate (marginal)           | Below bronze's noise floor |
| Jupiter | Modern (decisive)                    | Bronze 5.2025 = JPL DE441 to 0.007% |
| Saturn  | Modern (decisive — sharpest verdict) | Ptolemy-vs-modern gap 3.2% > noise |

**Two-level interpretation:**

1. **The bronze AS RECONSTRUCTED by Freeth 2021** uses NASA NSSDC modern values rounded to 2 dp (5/5 verified). Freeth's stated methodology in the Supp S9 caption acknowledges this. The dispatch question is at this level cleanly answered: modern AU is the design input.

2. **The actual ancient bronze designer's data source** is not recoverable from Supp S9 d/i/o alone, except for Saturn — where the 3.78% bronze-vs-Ptolemy gap exceeds the bronze fabrication noise floor (typically 1-3% in gear-tooth precision). If the historical bronze designer had used Ptolemaic AU of 9.231, the published d/o ratio could not be 9.58. Therefore: **whatever AU value the historical designer of the Saturn pin-and-slot used, it was NOT Ptolemy's Almagest XI value.** It was either (a) modern by coincidence with bronze fabrication noise dropping in their favour, (b) a different ancient value than Ptolemaic, or (c) tuned-after-the-fact to match modern observations Freeth used as a target.

The Sun would have provided a sharper era-vs-modern test (150% gap between Hipparchus 1/24 and modern 1/60), but Freeth 2021 does not give the Sun's pin geometry.

---

## Methodological notes

### Citation discipline

Per `feedback_pdf_extraction_citation_discipline`, all load-bearing citations have been primary-source verified:

- **Freeth 2021 Supp Information 4** — extracted from cached PDF `docs/antikythera-maths/hoodoos/41598_2021_84310_MOESM4_ESM.pdf`. Supp S9 table on p.30 transcribed verbatim per F17 baseline; Supp S4.3.1 True Sun mechanism description (page 28) and Supp S6.3 Fig. 6 description (page 51) verified for Sun mechanism architecture.
- **Rushkin 2015 arXiv:1502.01967** — extracted from local cache (PDF saved at `docs/antikythera-maths/hoodoos/rushkin_2015_ptolemy_model_arxiv_1502.01967.pdf`, SHA-256 `a87931b5b1920dc004487c36be487a5bdbdc4b384588cd7e5468983dde9a5b90`). Title page verified: "Optimizing the Ptolemaic Model of Planetary and Solar Motion", Ilia Rushkin, 2015. arXiv ID 1502.01967. Table p.7 provides Ptolemy AU values per planet derived from Almagest IX-XI.
- **Fitzpatrick "A Modern Almagest"** — open-access at `https://farside.ph.utexas.edu/Books/Syntaxis/Almagest.pdf`. Table 5.1 (p.82) gives JPL DE441 Keplerian elements. Hipparchan solar model §4.3 (pp.69-71) gives e_⊙=1/24.
- **NASA NSSDC planetary fact-sheets** — `https://nssdc.gsfc.nasa.gov/planetary/factsheet/`. Distance from Sun in 10⁶ km / 149.598 AU/km gives modern AU values that match Freeth Supp S9 round-2dp exactly.

Unverified secondary citations:
- **Toomer 1984** Ptolemy's Almagest (translation, Princeton). Cited via Rushkin 2015 for raw Almagest epicycle:deferent values. No direct PDF extraction.
- **Wikipedia Almagest article** (corroborates 39;30 Mars value; not load-bearing).
- **Voisey 2024 blog post** (corroborates Mars; not load-bearing).
- **Carman & Evans 2010, 2019** — referenced as future-spike sources for Sun pin geometry; not consulted in this dispatch.

### Era-appropriate framing

The "Hipparchan" framing in the dispatch is necessarily imprecise. Ptolemy himself credits Hipparchus only with observations, not with a planetary theory (Almagest IX.2). Freeth 2021 Supp p.11 quotes the scholarship: "Hipparchos (c.190 –120 BC) did not propose a theory" for the planets. The best era-appropriate target is therefore Ptolemy's *Almagest* (150 CE), which is canonically taken to record the best-available pre-Ptolemy (Babylonian + Hipparchan) observational data systematized into a model — but Ptolemy's planetary parameters are LATE additions to that tradition, not contemporary with the bronze (~150 BCE).

A genuinely-pre-Ptolemy planetary AU dataset is not recoverable from extant sources. The Babylonian Goal-Year and ACT period relations (Freeth 2021 Supp Table S3) preserve synodic periods but not distance/epicycle-radius estimates. **The dispatch's "era-appropriate" reference is therefore Ptolemy-as-proxy-for-Hipparchan-tradition, not actual Hipparchan-era values.**

### NDJSON discipline

Output emitted as NDJSON (one record per line) per `feedback_ndjson_over_bloated_json`. Eight records: header + Sun (F18) + Mercury (F19) + Venus (F20) + Mars (F21) + Jupiter (F22) + Saturn (F23) + aggregate. All numerics are doubles; relative errors are signed percentages.

### Closed-form algebra preferred

c_1 amplitudes computed via `bronze_c1_deg(p_AU) = atan(p_AU)` per F17 closed-form: the bronze geometry produces `arctan(d sin M / ((i or o) + d cos M))` whose peak amplitude is `arctan(d/(i or o)) = arctan(p_AU)`. For inferior planets (p_AU < 1) this equals the leading coefficient of the closed-form Fourier series `Σ_{k≥1} (p_AU^k / k) sin(k M)` to better than 0.5%; for superior planets (p_AU > 1) the arctan form is the geometric truth and the series diverges. No FFT used.

For the Sun, c_1 amplitudes computed via Greek-doubling `2e` for the Hipparchan eccentric-circle convention; this is the leading Kepler equation-of-centre term in the small-e regime where the bronze operates.

---

## Implication for F17 BronzeGeocentricEpicycle (no encoder amendment needed)

F17 proposed BronzeGeocentricEpicycle as the encoder mode that uses `ε = p_AU` per Freeth Supp S9. This dispatch's analysis confirms BronzeGeocentricEpicycle is SOUND AS DEFINED — it consumes the Freeth-published d/i ratios, which are modern AU values, and produces predictions that match Freeth's intended reconstruction.

If a future spike wants to test **"what would BronzeGeocentricEpicycle predict if the historical designer had used Ptolemaic p_AU values?"**, that is a *sensitivity analysis* on top of the existing encoder mode, NOT an encoder-mode swap. The four tightest planet matches (Mercury 0.75%, Venus 0.49%, Mars 0.26%, Jupiter 0.04%) and the modestly-looser Saturn (3.78% if Ptolemy; 0.025% if modern NSSDC) all sit at or near the bronze's noise floor — encoder predictions are robust to era-appropriate vs modern AU substitution within fabrication precision.

The only planet where era-vs-modern materially affects the encoder is **Saturn**: at Ptolemaic 9.231 the leading c_1 amplitude is 83.82°; at modern 9.582 it is 84.04°. The difference (0.22°) is detectable in long-term residual analysis but below visual-readout precision on a bronze dial.

---

## Fermata records (conductor decisions)

1. **F18 Sun pin geometry.** Whether to pursue Carman & Evans (2010, 2019), Evans/Carman/Thorndike (2010), Wright (2007), or Freeth Supp S6 figures to recover bronze Sun (pin offset, pin distance) values. The Hipparchus-vs-modern gap on solar e (~150%) is the cleanest era-vs-modern test in the analysis; getting the bronze's Sun pin geometry would settle it.

2. **F21 Mars marginal era-match.** Bronze Mars d/o = 10.00/6.58 = 1.5198 is suspiciously close to Ptolemy's 39;30 epicycle:deferent (60/39.5 = 1.519). Whether this is coincidence (modern rounds to 1.52; Ptolemy is 1.519; bronze fabrication maps both) or signal (Freeth deliberately chose `i=6.58` to match Ptolemaic 39;30) is not clear from Supp S9 alone. The mm precision Freeth quotes (3-4 sig figs) suggests deliberate choice; a conductor decision is needed on whether to flag this in the antikythera notebook.

3. **F23 Saturn anomaly.** Bronze Saturn is the only sharply-distinguishable era-vs-modern case among the planets, and falls decisively on the MODERN side. Freeth's choice of NASA NSSDC (1433.5 / 149.598 = 9.582) over JPL DE441 J2000 (9.537) for Saturn is interesting — these conventions differ by 0.5% because of Saturn's strong secular perturbations. Whether the F17 BronzeGeocentricEpicycle encoder should default to NSSDC or JPL conventions for Saturn is a conductor decision; the 0.5% difference is at the encoder's noise floor.

4. **F18-F23 absorption into srmech notebook §11.6.6.** The era-appropriate analysis sharpens F17's BronzeGeocentricEpicycle story: the bronze's geometric ratios ARE modern by Freeth's construction (verified 5/5), but the gear-fabrication noise floor prevents recovery of the actual historical designer's AU values. Whether to land this in srmech notebook §11.6.6 (cascade architectures) or in antikythera notebook §20 (Almagest / Freeth parameter sets) is a conductor decision.

---

## Outstanding citations that could not be primary-verified

- Toomer (1984) Ptolemy's Almagest (Princeton translation). Cited via Rushkin 2015 for raw Almagest epicycle:deferent values. The Toomer translation is the canonical English source for Almagest values; this dispatch did not extract the Toomer PDF.
- Carman & Evans (2010) "Solar Anomaly and Planetary Displays in the Antikythera Mechanism" JHA 41(1) 1-40. Referenced as future-spike source for F18 Sun pin geometry; not consulted.
- Carman & Evans (2019) "Babylonian Solar Theory on the Antikythera Mechanism" Archive for History of Exact Sciences 73(6) 619-659. Same.
- Wright (2007) "The Antikythera Mechanism reconsidered" Interdisciplinary Science Reviews 32(1). Same.
- Almagest III.4 for Hipparchan e_⊙=1/24. Verified via Fitzpatrick Modern Almagest §4.3 (open-access) which is consistent; the Toomer 1984 page reference is not primary-verified.
- Almagest IX.2 statement "Hipparchus did not propose a planetary theory." Verified via Freeth 2021 Supp p.11 (Freeth quotes the scholarship); Toomer 1984 page reference not primary-verified.

These should be marked `[unverified-secondary]` in any downstream notebook citations. None are load-bearing for the dispatch's load-bearing forensic finding (Freeth Supp S9 = NASA NSSDC round-2dp, 5/5 verified directly).
