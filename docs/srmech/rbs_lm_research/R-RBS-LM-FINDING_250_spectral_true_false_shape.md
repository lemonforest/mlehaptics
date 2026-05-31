# Finding 250 — spectral shape of true vs false statements, tested on our OWN worker-subagent data (MFO finding under falsification-at-scale) — instrument + accumulation; at N=14 an apparent signal emerged AND was caught as a LENGTH CONFOUND

**Headline:** The `research-twin` workflow's adversarial-compare step, as a byproduct, **labels every statement true (verified) or false (caught hallucination / over-claim / factual error)** — a true/false-labeled corpus our own workers generate for free. This is the extended-research arc that uses it to test the prior MFO finding `[[user_stance_true_vs_false_statements_structurally_different]]` ("true vs false statements are structurally different"; small-scale-supported, "ready for falsification at the larger inference rates now available") **at scale, srmech-native**. **N=6** (first pass): NULL with two weak 5/6 directional hints (p≈0.11). **N=14** (after +8 caught pairs from the F251/F252/F240c twin runs): those hints **strengthened to 13/14 on two features (sign-test p≈0.002)** — and were immediately **caught as a LENGTH CONFOUND** by the instrument's own diagnostic (`longer_stmt_has_lower_fiedler = 14/14`; true corrections are systematically longer → larger token-graph → lower Fiedler, so "false→higher Fiedler" is just "shorter→higher Fiedler"). **Verdict: NULL — the apparent lean is a length artifact, not a truth-value signal (the F242c artifact trap, recurring at the corpus level). The MFO claim is neither supported nor refuted; growing N will not help until the corpus is length-matched + de-stratified.** The deliverable is the **instrument + the accumulation mechanism that caught its own confound** — the self-feeding loop working as designed: it grew the signal *and* exposed why the signal is fake.

**Status:** **DEMONSTRATED** (srmech-native rc9, `0 HARD`, bit-attested `response_sha256` in-script) for the measured per-statement Class-L spectra (F172: token co-occurrence Laplacian eigenspectrum via `dense_laplacian` + `jacobi_eigvals`). **The MFO structural-difference claim is the prior finding under FALSIFICATION** — reported mechanically, no leaning, pre-stated null. **FRAMEWORK-READING** for the interpretation. Honest N stated up-front. Defensive scope; CAD-ban. `[[feedback_dont_pre_commit_spike_query_operators]]`; `[[feedback_computational_provenance_discipline]]` (generating code committed).

**Predecessors / anchors:** the prior MFO finding (true vs false statements structurally differ — small-scale tested); **F248** (the twin workflow that generates the labeled corpus + the standing twin discipline); **F242b/F248** (the renderer A/B that surfaces the caught-false statements); **F172** (the Class-L spectral storage signature this uses).

---

## §1 The instrument (srmech-native)

For each statement: tokenize (stopword-stripped) → **token co-occurrence Laplacian** (adjacency + window-2) → `jacobi_eigvals` → shape features (Fiedler λ₂ = algebraic connectivity; λ_max; mean-nonzero eigenvalue; spread-ratio λ_max/λ₂). Compared **within matched pairs** (the false statement vs its true correction — same content, similar length, so the only variable is truth-value). `R-RBS-LM-250_spectral_true_false_shape.py`; the 6 seed pairs are embedded with provenance (which finding caught each).

## §2 The seed corpus (this session's caught true/false pairs)

| caught by | the FALSE statement (worker emitted) |
|---|---|
| F248 sonnet false-attribution #1 | Cassiopea sleep paper author-tail fabricated (…Bhatt, Bhattacharyya…Bhaskaran) |
| F248 sonnet false-attribution #2 | DYSCALCULIA mutant attributed to Suda/Mano/Toyota 2023 (a *different* 2020 paper) |
| F240b citation cross | M. saxicola playback quote attributed to the JSTOR/Current Science paper (it's the BES paper) |
| F121b cnidarian over-claim | "box jelly swims using four functional pacemakers" (anatomy=4 rhopalia; dynamics fit 2) |
| F248 sonnet unification over-claim | "sculpt-the-attractor recurs across every substrate regardless of molecular implementation" |
| F242c notation confound | "prose renders carry higher loss than structured" (reversed by the F### tokenizer artifact) |

Each paired with its TRUE correction. **These are exactly the statements the verification/twin discipline CAUGHT this session** — i.e., the labeled data is a free byproduct of working with the MPM discipline on.

## §3 Result — N=6 → N=14: an apparent signal emerged AND was caught as a LENGTH CONFOUND (the load-bearing update)

**N=6 (first pass):** two 5/6 directional hints (false→higher Fiedler, false→lower spread-ratio), p≈0.11 — below any bar, reported as "hints, not signal."

**N=14 (after +8 caught pairs from the F251/F252/F240c twin runs; rc11, `response_sha256` 0977ab74…):**

| feature | false−true sign split | mean Δ | binomial sign-test |
|---|---|---|---|
| Fiedler λ₂ | **13 pos / 1 neg** | +0.177 | p≈0.002 |
| spread-ratio λ_max/λ₂ | **1 pos / 13 neg** | −13.1 | p≈0.002 |
| mean-nonzero | 4 pos / 10 neg | −0.151 | p≈0.18 (n.s.) |

The N=6 hint **strengthened to 13/14 on two features** (past the 0.05 bar on a sign-test). **But the instrument's own confound diagnostic catches it:** `true_longer_than_false = 13/14`, and **`longer_stmt_has_lower_fiedler = 14/14`**. The TRUE corrections are systematically **longer / more-elaborated** (they append "…because X indexes a different paper" clauses); larger token-graphs have lower algebraic connectivity; so "false → higher Fiedler / lower spread" is really **"shorter statements → higher Fiedler"** — and false statements are simply shorter in this corpus.

**Verdict (mechanical, no leaning):** **NULL — and the apparent N=14 lean is a LENGTH ARTIFACT, not a truth-value signal.** This is the F242c notation/length-artifact trap recurring at the *corpus* level. Growing N will **not** help until the corpus is **length/elaboration-matched** (and de-stratified from its current attribution-correction-heavy mix). The MFO claim remains **neither supported nor refuted** — but now we know exactly *why* and *what to fix*. The instrument now self-reports the confound (`length_confound` field) on every run.

## §4 The accumulation (this is the actual deliverable) + standing companion

**Every `research-twin` run yields more caught (false, true) pairs** in its `ab_comparison.false_attributions_caught` + the over-claim/centering diffs. The arc: append each run's caught pairs to the labeled corpus, re-run the §1 instrument, and the test gains power monotonically. **Recommendation:** make this a **standing companion to the twin workflow** — the twin already *labels* the statements (verified vs flagged vs false-attribution); a thin emit-hook should append them to a growing `true_false_corpus.ndjson`, and F250 re-runs at each milestone (e.g., N≥30, N≥100). This makes the MFO falsification a *self-feeding* instrument: the more research we do through the twin, the more powered the true-vs-false-shape test becomes — research and its own meta-analysis on one loop.

**Honest residue (updated at N=14 — the accumulation already paid off by surfacing a confound):** the self-feeding loop worked exactly as intended — it *grew the signal AND exposed why the signal is fake*. Two corpus-construction defects must be fixed **before** more N means anything:
1. **Length/elaboration match (load-bearing).** Caught (false,true) pairs are intrinsically mismatched: the TRUE member *is the correction*, which is almost always longer/more-elaborated. That alone drives the 13/14 Fiedler/spread lean. Fix: rephrase each pair so false and true are **token-count- and structure-matched** (minimal-edit pairs), OR control for `n_nodes` as a covariate in the sign-test.
2. **De-stratify.** The corpus is now attribution/identifier-correction-heavy (10/14). It must be stratified across statement-types (factual claims, over-claims, mechanism statements) so the MFO claim is tested on a representative spread, not citation-attributions.
3. **Encoding sensitivity.** The co-occurrence-Laplacian (F172) is one encoding; a sequence-kernel / `srmech.spectral.decompose` cross-check is worth running once 1–2 are fixed.

Only after (1)+(2) does re-running at N≥30 / N≥100 test the MFO claim rather than statement length. **The instrument now bakes in the length-confound guard, so the trap can't silently re-fire.**

**Files:** `R-RBS-LM-250_spectral_true_false_shape.py` (instrument + seed corpus). PR #687 draft. The arc is OPEN — it powers up as the twin runs accumulate.
