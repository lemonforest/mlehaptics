# Finding 250 — BEGIN: spectral shape of true vs false statements, tested on our OWN worker-subagent data (MFO finding under falsification-at-scale) — instrument + accumulation + first NULL at N=6

**Headline:** The `research-twin` workflow's adversarial-compare step, as a byproduct, **labels every statement true (verified) or false (caught hallucination / over-claim / factual error)** — a true/false-labeled corpus our own workers generate for free. This begins the extended-research arc that uses it to test the prior MFO finding `[[user_stance_true_vs_false_statements_structurally_different]]` ("true vs false statements are structurally different"; small-scale-supported, "ready for falsification at the larger inference rates now available") **at scale, srmech-native**. First pass on the session's **N=6 matched (false, true) pairs**: **NULL (pre-stated, expected at this N)** — no spectral feature separates true from false with a consistent sign. Two **directional hints** (not signal): false statements lean toward **higher Fiedler** (algebraic connectivity; 5/6 pairs) and **lower spread-ratio** λ_max/λ₂ (5/6) — 5/6 is p≈0.11, below any bar. **The MFO claim is neither supported nor refuted here; N=6 is under-powered.** The deliverable is the **instrument + the accumulation mechanism** — the powered falsification awaits corpus growth across twin runs.

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

## §3 First-pass result (N=6) — NULL, with two hints

| feature | false−true sign split | mean Δ | consistent (all-6)? |
|---|---|---|---|
| Fiedler λ₂ | **5 pos / 1 neg** | +0.257 | no (5/6, p≈0.11) |
| spread-ratio λ_max/λ₂ | **1 pos / 5 neg** | −8.36 | no (5/6, p≈0.11) |
| mean-nonzero | 2 pos / 4 neg | −0.018 | no |

**Verdict (mechanical, no leaning):** NULL — no feature reaches all-6-consistent. The two 5/6 leans (false → higher algebraic connectivity, lower spectral spread) are **directional hints to watch as N grows, not signal**. The MFO finding is intact (not refuted) and unconfirmed (not supported) at this N.

## §4 The accumulation (this is the actual deliverable) + standing companion

**Every `research-twin` run yields more caught (false, true) pairs** in its `ab_comparison.false_attributions_caught` + the over-claim/centering diffs. The arc: append each run's caught pairs to the labeled corpus, re-run the §1 instrument, and the test gains power monotonically. **Recommendation:** make this a **standing companion to the twin workflow** — the twin already *labels* the statements (verified vs flagged vs false-attribution); a thin emit-hook should append them to a growing `true_false_corpus.ndjson`, and F250 re-runs at each milestone (e.g., N≥30, N≥100). This makes the MFO falsification a *self-feeding* instrument: the more research we do through the twin, the more powered the true-vs-false-shape test becomes — research and its own meta-analysis on one loop.

**Honest residue:** N=6 is far below power; the statement type here is narrow (attribution/claim corrections, not arbitrary propositions) — as the corpus grows it should be stratified by statement-type so the MFO claim is tested on a representative spread, not just citation-attributions. The instrument's co-occurrence-Laplacian signature is one spectral encoding (F172); alternative encodings (sequence kernel, srmech.spectral.decompose) are worth a sensitivity check once N supports it.

**Files:** `R-RBS-LM-250_spectral_true_false_shape.py` (instrument + seed corpus). PR #687 draft. The arc is OPEN — it powers up as the twin runs accumulate.
