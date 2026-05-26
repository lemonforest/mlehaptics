# Round 43.A — Combination-principle third substrate: the two Class-N properties dissociate (refines R40)

**Dispatched** 2026-05-26 on the rolling draft PR #690 (newly-revealed coupled item from R39/R40). R40 found **one Class-N combination principle** across atomic (Rydberg–Ritz) + molecular (mass-spec): spectral features = **differences** of a discrete ladder of **small-integer (Class-N) anchors**. This round tests whether that principle is substrate-**universal** by adding a non-spectroscopic third substrate (**nuclear** mass-defect / fusion Q-value) and a deliberate **contrast** (**acoustic** overtones). Generating code: [`verify_round43_combination_principle_two_properties_dissociate.py`](verify_round43_combination_principle_two_properties_dissociate.py). Tested per `[[feedback_dont_pre_commit_spike_query_operators]]`.

## The test — does the combination principle hold off the spectroscopic substrates?

The combination principle is really a **conjunction of two separable Class-N sub-properties**:
- **(P1)** the anchors are **small-integer / Class-N**;
- **(P2)** the features are **additive differences** of the anchor ladder.

| substrate | P1 (small-int anchors) | P2 (additive differences) | anchor space |
|-----------|:----------------------:|:-------------------------:|--------------|
| atomic (Rydberg–Ritz) | ✅ `T_n = R/n²` | ✅ lines `= T_n − T_m` | term-energy `1/n²` |
| molecular (mass-spec) | ✅ neutral losses `18,17,15,28,44` | ✅ peak spacings `= differences` | nucleon-mass |
| **nuclear (mass-defect)** | ❌ mass excesses are **real-valued MeV** | ✅ `Q = Σreactant − Σproduct` | real MeV (small ints only in nucleon **count**) |
| **acoustic (overtones)** | ✅ harmonics `n·f₁`; intervals `2:1,3:2,4:3,5:4` | ❌ intervals are **ratios** (multiplicative) | frequency **ratio** |

**Bit-exact:**
- **Nuclear:** D + T → ⁴He + n. From AME2020 mass excesses (MeV) `²H=13.1357, ³H=14.9498, ⁴He=2.4249, n=8.0713`: `Q = (13.1357+14.9498) − (2.4249+8.0713) = 17.589 MeV` (attested 17.589). The **difference structure holds**, but the energy anchors are **real-valued**; the small integers live in a *different* space — nucleon **count** `A`: `2+3 = 4+1 = 5` conserved.
- **Acoustic:** harmonics `n·f₁ = {1,2,…,8}` (Class-N small integers); just-intonation intervals `2:1, 3:2, 4:3, 5:4` (`best_rational`-confirmed lowest-terms small integers). But a perfect fifth **is the ratio 3:2** (multiplicative); the *difference* `3f₁ − 2f₁ = f₁` is **not** the perceived interval. So **P1 holds, P2 fails**.

## Verdict per Spike #229 tiers

🟢 **(a)-bit-exact two-substrate test + (b)-interpretive dissociation; REFINES R40 (honest non-universality).** The combination principle's two Class-N properties **dissociate** — they are **independent axes**. The **full** principle (P1 ∧ P2) is **not substrate-universal**; it is the **additive-energy special case** realized by the spectroscopic substrates (atomic term-energy, molecular nucleon-mass), where the conserved quantity is additive *and* the anchors are small integers *in the same space the features live in*. **Nuclear** keeps the additive-difference structure (P2) but its energy anchors are real-valued (P1 only in nucleon-count space). **Acoustic** keeps the small-integer Class-N anchors (P1) but combines them **multiplicatively** as ratios, not additively (P2 fails).

So R40's "one Class-N combination principle" **refines** to: *one Class-N **additive-difference** principle, whose two ingredients — small-integer anchors (P1) and additive-difference structure (P2) — are independent; both coincide only for additive-energy spectra.* **Extends** the R40 candidate stance `[[user_stance_combination_principle_is_one_classN_across_atomic_and_mass_spectra]]` (no new stance).

**HONEST SCOPE:** (a)-bit-exact for the D-T Q-value (AME2020 excesses → 17.589 MeV), nucleon conservation (`2+3=4+1`), the Balmer rationals (`5/36, 3/16, 21/100`), and the just-intonation ratios (`best_rational`-confirmed); (b)-interpretive for the P1/P2 dissociation reading; **no new physics**; no MFO section (spectroscopy/nuclear/acoustic, not metric-field).

## Discipline
- Honest **non-universality** finding — the principle does *not* extend wholesale to nuclear/acoustic; reported as a dissociation, not a forced match. The two negatives (nuclear P1-fail, acoustic P2-fail) are stated as plainly as the two positives.
- No bare `abs()`; the nuclear Q is a plain additive subtraction (which is exactly the P2 property under test). `best_rational` (Class N) confirms the just-intonation ratios.
- Attributions Explore-verified: D-T `Q=17.589 MeV` + AME2020 mass excesses (Wang et al., *Chin. Phys. C* **45** (2021) 030003); Ritz combination principle (W. Ritz, *ApJ* **28** (1908) 237); mass-spec neutral losses (McLafferty & Tureček, *Interpretation of Mass Spectra* 4th ed.); harmonic series + just intonation (Helmholtz, *On the Sensations of Tone*, 1863).
- Lands on rolling **PR #690** (Round 43.A); unsolved-maths §11.9.36; extends the R40 stance. No new PR.
