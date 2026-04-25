# Research Audit Report — Antikythera HDC Project

**Auditor:** Cross-disciplinary research review
**Date:** April 25, 2026
**Scope:** The 31-row H-battery + 8 architectural-mode hypotheses across the `docs/antikythera-maths/` scaffold
**Verdict:** Mostly sound research with several specific concerns flagged below; one moderate concern about iter-2 threshold relaxation, one significant concern about G-H7's synthesised data, otherwise an unusually self-disciplined project.

---

## A. Methodology — threshold-setting and post-hoc adjustment

The project's iter-1/2/3 history is unusually transparent. The commit log (`23167fe`, `d59a69d`, `3bb1fb7`) shows three explicit "what remains" passes that adjusted thresholds and split hypotheses. I traced each adjustment against its commit message and verdict change.

**Sound adjustments (no cherry-picking concern):**

- **A-H1 split into A-H1a/A-H1b** (iter-3 `3bb1fb7`). The original A-H1 reported a PARTIAL with two distinct findings folded together: "strict CF rank 15%" (FAIL) and "loose budget-respecting 54%" (PASS). The split makes both findings explicit and preserves the FAIL on the strict claim. This is the right move — a single "PARTIAL" had been hiding a real falsification of the build prompt's a-priori prediction. The strict claim (A-H1a) is still recorded as FAIL in the canonical CSV. **Honest reframing.**
- **G-H1 split into G-H1a/G-H1b** (iter-1 `23167fe`). Continuous-regime FAIL (13.2°) and intermittent-regime PASS (0.000°) are both kept in the CSV with explicit operation-regime tags. The user's notebook §11.6.10.8 states bluntly: *"G-H1's FAIL was a model-error, not a finding about the device."* That's the right honesty — the FAIL is preserved as a record of where the original modelling assumption was wrong.
- **E-H1b anchor JD correction** (iter-1 `23167fe`). The original E-H1b FAIL (1/6 anchors hit) was traced to a bug in `hellenistic_eclipses.py`: hand-curated JDs were off by half a synodic month for some entries. The fix uses DE422 to *infer* the correct JD from the date (script `correct_hellenistic_anchors.py`). Shifts ranged from −10.4 to +13.3 days. **This is a legitimate data-error correction, not p-hacking** — the encoder was always sound (E-H1c sky-driven Saros got 1.000 backward precision); only the anchor table was wrong. The corrected E-H1b reaches 6/6 within ±1 day at 0.19° mean phase error. Bug found honestly and fixed transparently.
- **E-H3 threshold widening** (iter-1 `23167fe`). Original threshold ≤10° was too optimistic; widened to 30–60° band. The notebook §9.2 explains the reasoning: *"epicycle-only and equant Mars models converge near the documented 38° Greek-attainable limit"*. The widening is justified by the empirical convergence of the three Greek planetary models around ~50°, which is itself a research finding (the equant's marginal improvement is small). However, **this comes close to post-hoc threshold tuning** — the widened threshold (30–60°) is a band centred on what the encoder produces, not a band derived independently from Greek-source-text claims. Mitigation: the notebook explicitly flags this as "the threshold was too optimistic" rather than burying the original threshold. I'd accept this as legitimate refinement, but note it as the closest the project gets to threshold cherry-picking.

**One concerning iter-2 relaxation:**

- **A-H2 threshold relaxation** (iter-2 `d59a69d`). The original A-H2 was PARTIAL because Freeth's {7,17} was on 2/3 frontiers (factor-reuse + proxy) but NOT on the primary frontier. Iter-2 changed the PASS threshold to "≥2/3 ablations agree" — making the PARTIAL into a PASS without changing any computation. The commit message rationalises this: *"Most directly captured by factor-reuse + proxy metrics (both cost = total bronze)"*. **This is the most p-hacking-shaped move in the iteration history.** The PARTIAL was substantively informative — it said Freeth's choice survives one cost framing (total bronze) but not another (max single tooth count). Promoting it to PASS at "≥2/3 metrics" reduces that information content. The CSV notes column does record what's happening, but the headline status flips. **I would have left this as PARTIAL.** This is one of the legitimate places where the verdict-tally summary of "23 PASS / 1 PARTIAL / 4 FAIL / 2 UNDETERMINED" overstates the firmness of the finding by one row.
- **G-H6 threshold relaxation** (iter-2 `d59a69d`). Originally PARTIAL (3 CAUTION verdicts on engagement locks); relaxed to PASS at "no AVOID required." The commit's defence is mechanical: *"Engagement locks MUST be at subsystem ENTRY... CAUTION verdict is APPROPRIATE for engagement-lock placement, not a partial fail."* This is a reasonable structural argument — leaves are dial *outputs*, not engagement points — but it's also a post-hoc reframing of what "CAUTION" means for the periphery rule. **I rate this as borderline acceptable.** The mechanical reasoning is right; the threshold change is principled, but it would have been cleaner to define the CAUTION-vs-FAIL distinction *before* running the test rather than after seeing the unanimous CAUTION verdict.

**Failure modes are handled honestly:**

The project preserves all four FAILs in the canonical CSV:
- A-H1a (strict CF) FAIL — kept and explained
- E-H1b's original data-error mode is documented in the notebook even after the fix
- G-H1a continuous-regime FAIL is *deliberately retained* as a record of model-assumption sensitivity
- G-H3 FAIL with the matched-control framing (iter-3 `3bb1fb7`) is the more honest result — the iter-3 fix *kept* the FAIL after controlling for tooth count, which is the harder-to-publish honest result

The project does not memory-hole failures.

---

## B. Statistical claims

**Chi-square and small-sample caveats:**

- **A-H3** (chi² p = 0.32). Iter-3 `3bb1fb7` adds a formal scipy.stats.chisquare test. The PARTIAL verdict (failing the p<0.05 threshold) is the honest call — the small-prime overweight is only 1.15× null, and the chi² test's lack of significance is preserved in the verdict. **Sound.**
- **H-H1** (chi² p = 0.32, Cramér's V = 0.103). The Cramér's V = 0.103 is reported alongside the p-value, which is good practice — that's a small effect. The headline "statistically indistinguishable" framing in §9.5 is a bit strong (failing to reject ≠ proving same-distribution; the test simply has low power for small samples), but the Cramér's V reporting compensates. **Acceptable, with minor framing concern.**

**The H-H2 perfect Jaccard (1.00):**

This is the project's most overstated claim. The notebook §2.D and §9.5 frame H-H2 as "MUL.APIN top-3 primes overlap perfectly with Antikythera" with Jaccard 1.00 between top-3 prime sets {2, 3, 5}. The project's own §1.4 sanity battery already noted *"small primes dominate; the few large primes (47, 53, 127, 223, 251) each carry a specific irrational-cycle approximation."*

**Concern:** {2, 3, 5} dominate the top-3 of *any* astronomical period system because (a) calendrical cycles are factored from common periods (lunation, year, week-like sub-units) heavily biased toward small primes; (b) any period-relation approximation under any tooth-count budget has 2/3/5 as the dominant factor pool. **The H-H2 PASS is a near-tautology dressed as a substantive cross-cultural finding.**

The notebook does mention this concern in §9.5 (*"merits a future deeper read of MUL.APIN's intercalation rules"*), but the verdict-tally summary still counts H-H2 as a confirmed PASS supporting the "Babylonian factorisation tradition anchors the Antikythera's small-prime fingerprint" narrative. **I would have rated H-H2 as UNDETERMINED rather than PASS** — perfect Jaccard between top-3 prime sets across two systems where {2,3,5} dominate is uninformative.

A more discriminating test would be: top-K Jaccard at K = 5, 7, 10, where the *non-trivial* primes start to matter. The project has the machinery (`historical_cross_reference.py`); it just chose K=3 for the headline, which is the K-value that maximally guarantees overlap.

**Monte Carlo sample sizes:**

The default n_trials = 2000 (`evaluate_G_H1`/`G_H2`) for tail statistics like p95 is on the lean side. p95 has ~5% sample variance at n=2000; for a hypothesis with a sharp 2° threshold that's enough margin to not flip the verdict (Saros at 13° vs 2° is 6.5× over), but for the marginal G-H2 ratio = 1.00 case, sample variance could push it to 1.05–1.20. The CLI supports up to 5000+ trials and the notebook §11.6.10.8 example uses 5000 — **acceptable for the stated thresholds, but the headline numbers in the CSV are at 2000 trials.**

**G-H3 matched control:**

Iter-3 `3bb1fb7` controls for tooth count by comparing rare-prime trains to peers within ±30% mean tooth count. The notebook acknowledges this leaves only 1 train in the matched set (0/1 within ±15% — a single-trial test). **The matched control is statistically defensible only as a sanity check, not as evidence for or against rare-prime fragility.** The notebook is honest about this: *"the effect is small."* The FAIL verdict on a single train is a "we couldn't refute the FAIL after controlling" rather than a strong confirmation. Adequate but limited.

---

## C. Archaeological / historical claims

**The crank-as-clutch hypothesis (§11.6.10):**

This is the largest single piece of novel reasoning in the project. My read:

- **The "absence of evidence is the evidence of absence" argument (§11.6.10.7)** does NOT cross into unfalsifiability, despite the project's own concern. The notebook states explicitly: *"That cuts both ways philosophically — it makes the hypothesis hard to falsify by inspection alone — but it also explains why, after a century of careful study, no one has confidently identified what holds the gears stationary."* The dossier `clutch_evidence_dossier.md` provides a CONFIRM/REFUTE table with concrete observable predictions (>5 mm keyway depth, brake-pad wear scars, spring-mount holes in case wall, inscriptions referencing engagement). These are real observable features. The hypothesis IS falsifiable; it's just falsifiable by archaeology (re-examining AMRP X-ray volumes), not by computation. **The DATA-BLOCKED status in the audit is the right call.**
- **The cumulative argument structure (§11.6.10.2: "five independent observations...")** is the strongest version of the hypothesis. Each individually-weak observation (a1 stress, deep-well keyway, surviving frozen state, jam crisis, drift FAIL) becomes mutually-reinforcing under one explanation. This is legitimate inference-to-best-explanation reasoning. **It does not establish the hypothesis as true; it establishes it as worth investigating.** The notebook is appropriately careful about this distinction.
- **One specific concern:** the empirical G-H1 PASS under intermittent operation (§11.6.10.8) is presented as supporting evidence for the clutch hypothesis. But the G-H1 PASS only confirms that *if* the mechanism ran intermittently, *then* drift would not be a problem. It does NOT confirm that the mechanism *did* run intermittently. The notebook §11.6.10.8 mostly handles this correctly: *"This dissolves the apparent contradiction with surviving evidence... G-H1's FAIL had to be an analysis artefact"* — but the framing slides slightly toward "G-H1's PASS supports the clutch hypothesis" when the cleaner reading is "G-H1's FAIL doesn't refute the clutch hypothesis." Minor framing concern.

**The "70% probability" estimates (and other percentage estimates):**

The notebook assigns probability estimates throughout: G-H7 carriers at "10–25%", G-H8 setting-mode at "30–50%", G-H10 clutch at "30–50%". §11.6.14.4 has a probability table with weighted factors. **These are pseudo-quantification.** They are not derived from any prior + likelihood computation; they are vibes-translated-to-numbers. The notebook does flag this in §11.6.14.4: *"Net estimate: 10–25% probability... by my best honest reading"*. Reading "honest" as code for "intuition," I think the project is being upfront about the Bayesian intuitions being intuitions. **This is acceptable in an exploratory notebook but should not be cited externally as a quantitative probability.** The verdict tags (NOVEL/SPECULATIVE/CONSEQUENTIAL) carry more information than the percentages.

**The G-H8 Venus 5/8 finding:**

The notebook §12.5 calls the Venus 5/8 alternative chain a "calibration dial" hypothesis: *"shows the operator how much the refined model deviates from the canonical 5/8 expectation."* This is a genuinely interesting conjecture but it's an *interpretation* of a coincidence (5/8 is a known-to-MUL.APIN canonical Venus cycle AND happens to be a low-bronze approximation under the Pareto search). **The interpretation as a calibration dial is overreach.** The empirical finding is: under a paired-chain enumeration with budget 500 + sync residual ≤1%, Venus admits 5/8 as one of multiple alternatives. The leap from "5/8 is in the alternative set" to "5/8 was implemented as a calibration dial" requires archaeological evidence of paired chains in the missing planetary plate, which doesn't exist.

That said, the notebook is reasonably careful: it presents G-H8 PASS as "computationally supported" (4/5 planets admit alternatives) rather than as "the missing gears are paired-chain differentials." The headline finding (4/5 planets have plausible alternatives within Greek bronze-cutting tolerance) is sound; the calibration-dial interpretation is appropriately speculative in §12.5.

**Citation usage:**

The project notes in `clutch_evidence_dossier.md` that several key papers (Voulgaris et al. 2024, Voulgaris & Mouratidis 2018, Szigety & Arenas 2025) are paywalled and the team has only read abstracts/summaries. The notebook is generally careful to attribute claims to the abstract level: e.g., §10.1's Voulgaris 2024 citation is hedged with *"argue from independent functional-reconstruction evidence"* (which is what the abstract says). Szigety & Arenas's "120-day jam" finding is consistently sourced from Phys.org's summary. **Acceptable practice** given the constraints, but it does mean some of the notebook's claims about what specific papers prove are at one-step-removed from the actual primary literature. The dossier's "Critical Gap" notes (e.g., *"the abstract does NOT specify whether these structures were 'indicator dials'..."*) show appropriate epistemic humility.

The Toomer 1984 *Almagest* citations are used appropriately for canonical Mars parameters — the project pulls specific values (R=60, r=39.5, e=6) from documented Almagest IX.6 sources. **Sound.**

---

## D. Cross-disciplinary leaps

**HDC framing (Plate's HRR, hyperdimensional computing):**

The HDC framing IS productive but the productivity is asymmetric. The directions where it pays off:

- **B-H3 (HDC binding via coprime roll = gear composition).** The encoder's 13/13 round-trip at D=13440 is a real result. The framing "gear meshing at ratio n_A/n_B is the HDC binding `h_A ⊗ R_{n_A/n_B}`" gives a clean description of the encoder structure that the chess/Othello/logo notebooks share, allowing cross-pollination of techniques.
- **C-H2 (spiral-dial wrap = torus-clip aliasing).** The framing "the spiral *physically* implements the cyclic boundary detection" is a genuine formal correspondence, not a metaphor.
- **D-H1 (pin-and-slot = antisymmetric fiber).** The ||M_anti||/||M_sym|| = 1.0 saturation result really does match the chess §9m pawn directed-Laplacian saturation. This is a non-trivial cross-domain result.

The directions where it's window-dressing:

- **The "damaged hologram" framing (§11.2).** This is metaphor rather than analytic machinery. The notebook explicitly says *"a hologram has a strong property: any sub-region encodes the whole image at reduced resolution"* — but the Antikythera fragments don't actually have this property. Fragment A doesn't encode the Saros + Metonic + planetary trains "at reduced resolution"; it encodes the Saros train *directly* and is silent on the planetary train. The notebook's own admission that this is a "sheaf-theoretic completion" problem is more accurate than the hologram framing. **The hologram metaphor is rhetorically appealing but does not buy analytic traction.**
- **"Sheaf-completion" framing for missing-gear inversion (§11.5).** Similar concern. The actual computation is a constrained graph-search problem (find missing meshes consistent with surviving DAG + DE422 ground truth + Pareto cost). Calling it sheaf-completion adds vocabulary without adding tools — there's no sheaf cohomology being computed, no actual section/restriction machinery being applied. **Window dressing.**

**The gear-DAG centrality / "periphery rule":**

This is more substantive than the holographic framing. The notebook §11.6.1 computes degree, BFS distance, and a composite periphery score on the 24-edge surviving DAG. The findings are:

- **b1 and e5 are the only degree-3 nodes** — the bridge gears.
- **i1, k2, m1 are the only degree-1 nodes** — the dial pointers.
- **All other gears are degree-2 transmission** — the chain links.

This IS a real graph-theoretic finding on a real (if small) graph. **Twenty-four edges is small for graph theory.** The notebook doesn't claim more rigor than it has — §11.6.3 frames the periphery rule as a "prior on missing-gear placement" rather than as a proven constraint. The G-H4 search-space pruning ("drops candidate count by roughly 10×") is a reasonable claim given the small graph; you don't need formal graph-theoretic guarantees to prune candidate searches with a defensible architectural prior. **Acceptable rigor for the claim.**

The graph-theoretic argument I'm most skeptical of is the synthesised G-H7 carrier insertion geometry, addressed in section E below.

---

## E. Synthesised data and assumption flags

**G-H7 carrier-insertion-geometry (FAIL at 7.3%):**

This is the most data-quality-concerning result in the H-battery. The test:

1. Enumerates 411 candidate gear-pair bridges
2. Synthesises 3D positions for each gear from `_FRAGMENT_BASE_POSITIONS_MM` (4 fragments at hand-set base coordinates) + BFS distance offsets (`x_offset = (d - 5) * 8.0`, `z_offset = (d % 3) * 5.0`) + `_synthesize_position` heuristic
4. Tests collinear-triple-tangent feasibility under a 5 mm tolerance band

**The verdict (FAIL at 7.3%) is computed against entirely synthesised geometry.** The CSV notes column says *"Sub-axle positions SYNTHESIZED; ASSUMPTION-FLAGGED. Specific FEASIBLE pairs reported as archaeological predictions."* This is the right disclosure — but the FAIL still reads as a substantive verdict in the verdict tally.

The honest framing would be: **"under one specific synthesis of gear positions consistent with fragment grouping and BFS depth, only 7.3% of candidate carrier insertions are geometrically feasible."** The verdict could equally well flip to PASS under a different synthesis (e.g., if base positions were 10 mm closer together). The 5 mm tolerance band is also assumption-driven.

The notebook §11.6.14.4 had assigned the carrier hypothesis 10–25% probability *before* the geometry test. The G-H7 FAIL implicitly tightens this estimate, but the FAIL is a function of the synthesis, not a function of the actual case geometry. **I would mark G-H7 as UNDETERMINED in the canonical CSV** rather than FAIL, with a note that the synthesised result tilts toward FAIL but doesn't settle it. The current CSV's "FAIL" verdict over-claims.

**E-H1b Hellenistic anchor data error:**

The original FAIL was due to JD assignment errors in the hand-curated `hellenistic_eclipses.py` table. When DE422 was used to re-derive JDs from the underlying date/event descriptions, the FAIL became PASS. **Was the bug an honest mistake or a worrying methodology breakdown?** My read: an honest mistake. The workflow that produced the bug — manually transcribing JD values from secondary sources — is exactly the kind of work that's error-prone, and the fix (use DE422 to *infer* JDs from the date strings) is the right systematic fix, not just a one-off correction.

The deeper concern would be: if the same workflow was used elsewhere, are there other hidden data errors? The project mostly avoids this risk because most other quantitative claims come from well-typed integer tooth counts (`gear_database.py`) and computed astronomical periods (`astronomical_cycles.py`), not from hand-transcribed JDs. The Hellenistic anchors were a small island of data that *needed* human curation against secondary historical sources. **I'd accept the iter-1 fix as legitimate and the bug as a one-off failure mode.**

That said, I note that E-H1b's PASS at 6/6 within ±1 day after the iter-1 fix is *not* truly independent confirmation of the encoder. It's confirmation that DE422-derived JDs match DE422-derived encoder predictions. The independent test is E-H1c (sky-driven Saros), which doesn't depend on Almagest anchors at all. **The iter-1 E-H1b fix moves the FAIL out of the verdict tally, but the substantive validation is E-H1c, not corrected-E-H1b.**

**The operation_regime parameter (continuous vs intermittent):**

This is the parameter the project's most-cited piece of analysis (G-H1 flip) hinges on. Is it a legitimate physical model variable, or a parameter being tuned to make hypotheses pass?

My read: **it's a legitimate physical model variable, and its tunable nature is documented carefully.** The notebook §11.6.10.4 derives the 100 active-seconds-per-year default from a quantitative sketch of operator usage (5 sessions × 5 seconds × ~5 turns/session ≈ 125 sec/yr, conservatively rounded to 100). The notebook §11.6.10.8 reports that even at 10× the budget (1000 s/yr) the drift stays below 2°. **The verdict is robust to a 10× variation in the parameter.** That's the right kind of sensitivity test for a parameter introduced post-hoc.

The notebook also preserves G-H1a (continuous regime) FAIL alongside G-H1b (intermittent) PASS in the canonical CSV, so a reader can see both verdicts. The "G-H1's FAIL was a model-error" framing in §11.6.10.8 is the correct gloss: the *original* model (continuous operation) made a prediction that failed, so the model needed to be re-examined. The intermittent-regime PASS is consistent with the crank-as-clutch hypothesis but doesn't *prove* it. **Acceptable.**

---

## F. Overall verdict

In 3-5 sentences, as requested:

This is genuinely rigorous research for what it is — an exploratory cross-disciplinary notebook combining HDC formalism with archaeology, ephemeris validation, and Greek planetary modeling. The project is unusually self-disciplined about preserving FAILs in the canonical CSV, splitting compound hypotheses honestly, and documenting threshold adjustments with full commit history; iter-1's E-H1b data-error fix is exactly the kind of bug that would be quietly memory-holed in a less careful project, and instead it's documented twice (in the commit message and in the notebook).

The single biggest concern I would raise to a senior researcher is the **A-H2 iter-2 threshold relaxation** (`d59a69d`): a PARTIAL was promoted to PASS by changing the threshold from "on the primary frontier" to "on ≥2/3 frontiers" without re-running anything, and this is the closest the project comes to p-hacking. Combined with the **G-H7 FAIL on synthesised geometry** (which over-claims a verdict from heuristically-synthesised positions) and the **H-H2 perfect-Jaccard claim** (a near-tautology of the {2,3,5} top-3 dominance in any astronomical period system), the headline tally of "23 PASS / 1 PARTIAL / 4 FAIL / 2 UNDETERMINED" probably overstates by 2–3 rows what a more conservative auditor would call PASS.

The single biggest strength is the project's **load-bearing self-honesty about modeling limits**: the §9.2 finding that "the equant's marginal improvement over the eccentric-deferent + epicycle model is only ~3°" is a real research finding that contradicts the build prompt's a-priori intuition, and it's reported as such; the §11.6.10.8 G-H1 flip is documented as a model-error rather than as vindication; the notebook §11.6.14.4 honest 10–25% probability estimate for carrier gears is a "speculative + worth-investigating" rating rather than a claim of likely truth. The project's epistemic vocabulary (KNOWN/NOVEL/CONFIRMED/FAILED/DISPUTED tags + the CONFIRM/REFUTE tables in `clutch_evidence_dossier.md`) is doing real work in keeping different claim-types separate.

**Net assessment:** Sound exploratory research with a couple of specific over-claims that should be tightened. The crank-as-clutch hypothesis and G-H8 setting-mode hypothesis are genuinely interesting conjectures worth pursuing in collaboration with the AMRP archaeology community; the project has done about as much computationally as can be done from a desktop without museum-held X-ray volumes, and is appropriately marking the remaining work as DATA-BLOCKED. Recommended changes: (a) revert A-H2 to PARTIAL, (b) reclassify G-H7 from FAIL to UNDETERMINED with the synthesis-flag prominent, (c) downgrade H-H2 from PASS to UNDETERMINED or replace with a top-K=7 Jaccard test that has actual discriminating power.

---

**End of audit.**
