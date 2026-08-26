# Finding 214 — The F212 §5 retrieval-vs-render test: a *content-free* recipient orientation is render-only (tier-3 NULL); the recipient anchor cannot be a rigid global Class-C twist — it must carry absorption-structure that selects sectors/relationships non-randomly

**Status:** Framework reading (RBS-NN arc) — the F212 §5 prediction RUN, with a pre-stated null. Tier-3 (weak/mixed → effectively NULL) at this corpus/scale; the null SHARPENS F212's RECIPIENT-anchor design rather than refuting the coupling. srmech-native, bit-exact, catalog-driven.
**Predecessors:** F212 (the hidden RECIPIENT fiber — the test this runs), F166 (the rolling context-state / autoregressive query, Step 1–2), F165 (DOMAIN anchor — the labeled-store retrieval mechanic the RECIPIENT anchor is a peer to), F168 (perplexity = chirality-tagged sector occupancy — the resolution-depth readout reused here), F169 (storage/expression separability — what F212 entangles in the query). Reuses the F166/F168 in-tree machinery: `_canonical_substrate.ContextSubstrate` (R-RBS-LM-126), the `encode_word_k4` sector-tagging (R-RBS-LM-131), the bigram candidate store (R-RBS-LM-127), the religious-text loader (R-RBS-LM-124).
**Empirical anchor:** `R-RBS-LM-214_retrieval_vs_render_recipient_fiber.py` + `recipient_fiber_retrieval_vs_render.ndjson` (24 records); catalog `descriptor_religious_texts.toml` `[recipient_fiber]` (descriptor_hash `b8733911…`); srmech 0.5.0rc22 native ABI=3, `HAS_NATIVE=True`; bit-exact across independent re-runs (NDJSON sha256 `cc41b309…`).
**User direction (2026-05-30, via F212 §5):** "Condition the *same* query on different recipient-absorption frames (ELI5 / peer / expert) … and measure whether the **RETRIEVAL** changes … versus only the **render** changing." Pre-stated; nulls count.

---

## §1 The test, stated precisely (F212 §5)

F212 claims the recipient's absorption-potential is hidden fiber bound into the **QUERY** (the F166 rolling context-state / addressing), a **Class-C orientation on the k=3 chiral addressing** — not just the final render. The test conditions ONE fixed knowledge query on three recipient frames, each encoded as a Class-C orientation **bound into the context-state (the query/hidden-state), NOT the render**, and asks whether **retrieval/addressing** shifts across frames or only the render would.

- **Fixed query:** held-out 5-token context windows over the KJV-NT kernel (F168 showed KJV-NT has the **deepest** sector structure — resolution depth 4, 38.6% of futures requiring order ≥3 — so it carries the most retrieval headroom for steering to surface). 400 windows, each whose last token has ≥3 legal successors (a real distribution to reshape).
- **Three recipient frames as Class-C orientations** (the value-level "which-way" operators, CLAUDE.md STOP-list):
  - ELI5 → `hdc.klein4_chirality_flip_gamma5` (one chiral-axis orientation)
  - peer → identity (the native / neutral register)
  - expert → `hdc.klein4_chirality_flip_omega7` (the other chiral-axis orientation)
  - each a **rigid, deterministic, self-inverse** Klein-4 twist of the *same* encoded query.
- **Shape-matched random control:** 16 rigid **random** Klein-4 orientations (`klein4_random`) bound into the SAME context-state the SAME way (`klein4_bind`) — the same *kind* of operation, carrying no recipient meaning. The pairwise spread *among the random frames* is the noise floor.

## §2 PRE-STATED null (verbatim, F212 §5)

> "only the render differs; retrieval / sector-occupancy / eigen-projection is **INVARIANT** across recipient frames" ⇒ the naive separable model holds (recipient is render-only).

- **Retrieval differs beyond the random control** ⇒ recipient-fiber threads into the QUERY/addressing ⇒ the RECIPIENT anchor must live in the F166 context-state (CONFIRMS F212).
- **Only render differs** ⇒ NULL; recipient is render-only.

## §3 What srmech measures (three retrieval readouts + the noise floor)

Per frame, over the fixed query set:

1. **Klein-4 sector occupancy** (F168 resolution-depth): the recipient-conditioned probe's argmax continuation is bound into each of the 4 Klein-4 sectors (`encode_word_k4(arg, sector=s)`); the most-recovered sector is the resolution depth the *addressing* chose for that future (self-inverse XOR sector tagging). Cross-frame distance = L1 over normalized sector histograms.
2. **Class-L eigen-projection:** per frame, the activation graph (nodes = candidate continuations; clique edge when both land in the probe's top-k) → `laplacian.dense_laplacian` → `laplacian.jacobi_eigvals`. Cross-frame distance = sorted-eigenvalue L2 (`cascade.magnitude` folds each signed coordinate — never `abs()`).
3. **Which stored relationships activate:** the top-5 ranked candidate set per query. Cross-frame distance = 1 − mean Jaccard.

**Honest-control upgrade (mid-run):** the first pass compared the structured spread against a 3-sample random point estimate and a permissive "≥2 raw-greater" rule, which manufactured a tier-2 "confirm" out of ratios 1.04–1.19 (within noise). Per `[[feedback_dont_pre_commit_spike_query_operators]]` the control was strengthened to a **16-frame random-spread distribution** and the verdict gated on whether the structured spread exceeds the **p90 percentile** of that distribution. The honest gate flipped the verdict (below).

## §4 RESULT — tier-3 weak/mixed (effectively NULL): 1/3 retrieval metrics beyond the p90 noise floor

| retrieval metric | structured spread | random mean | random p90 | structured pctile in random dist | beyond noise? |
|---|---|---|---|---|---|
| **sector occupancy (L1)** | 0.0167 | 0.0335 | 0.0550 | **0.15** | no (moves *less* than random) |
| **eigen-projection (L2)** | 51.42 | 40.09 | 57.28 | **0.83** | no (below p90 gate) |
| **activated top-k (1−Jaccard)** | 0.9176 | 0.8838 | 0.8887 | **1.00** | yes (>all random pairs) |

**Argmax-disagreement diagnostic** (fraction of queries whose top-1 continuation differs between two frames): structured **0.991** vs random **0.966**. The recipient orientations DO re-address the store (the chiral flips are pairwise-orthogonal — sim 0.0 — so they pull genuinely different continuations) — **but no more than random orientations of the same rigid-twist kind do.**

**Verdict: 1/3 → render-only at this corpus/scale. NULL for F212 §5 as a *content-free orientation* test.** The single beyond-noise metric (top-k Jaccard, pctile 1.00) is an **artifact of construction, not steering**: the three chirality-flip orientations are mutually XOR-orthogonal *by design*, so their ranked sets are maximally disjoint regardless of any recipient meaning. With only 3 structured frames (3 pairwise values vs 120 random), a pctile of 1.00 on the most construction-sensitive metric does not survive as evidence. Sector occupancy — the F168-native readout closest to "addressing depth" — is a clean null (structured moves it *less* than noise).

## §5 Why the null SHARPENS F212 (not refutes it)

The test falsifies one specific *operationalization* of the recipient fiber: **a rigid, content-free, global Class-C orientation of the context-state is indistinguishable from random noise in retrieval terms.** A constant XOR-twist re-labels every sector uniformly, so it reshuffles *which* candidate is nearest exactly as a random orientation would — it carries no information about *absorption depth*. That is precisely the diagnostic value: F212's claim that the recipient co-determines addressing **survives only if the RECIPIENT anchor carries recipient-specific structure** — an absorption-depth signal that selects sectors / relationships **non-randomly** (e.g. ELI5 → bias toward shallow sectors 0–1 = the word/bigram resolution depth; expert → bias toward the deep sectors 2–3 that F168 showed are load-bearing in KJV-NT). A which-way *bit* is not enough; the anchor must be a which-*depth* operator over the F168 sector ladder. This is the same lesson as F163 (chirality alone does not substitute for the DOMAIN anchor) applied to the RECIPIENT axis: the orientation is real but content-free, so it cannot be the anchor by itself.

## §6 Operational walkthrough (what / how / what srmech automates)

- **What:** ask the same fixed question 3 ways (for a 5-year-old / a peer / an expert) and check whether the *retrieval* into the knowledge store changes, or only the final wording would.
- **How:** each "way" is a rigid orientation twist of the encoded question (the F166 rolling state); a 16-orientation random control sets the bar for "how much does *any* twist move retrieval by chance."
- **What srmech automates:** `ContextSubstrate.encode_context` mints the rolling-state query (Class A∘M + iω₇ position); `hdc.klein4_chirality_flip_*` are the Class-C recipient orientations; `hdc.klein4_random` the shape-matched control; `sim_k4_batch` the Class-M retrieval; `encode_word_k4(sector=s)` the F168 sector tagging; `laplacian.dense_laplacian`+`jacobi_eigvals` the Class-L eigen-projection; `cascade.magnitude` the sign-free spectral distance (never `abs()`). Catalog-driven; deterministic / bit-exact (NDJSON sha256 stable across re-runs).

## §7 DOES / does NOT claim

**DOES:** run the F212 §5 test with a pre-stated null and a shape-matched random-orientation control; report the three retrieval readouts (sector occupancy / Class-L eigen-projection / which-relationships-activate) + the argmax-disagreement diagnostic against the random-spread distribution; return a tier-3 weak/mixed (effectively NULL — render-only at this scale) verdict; draw the sharpening — a content-free global Class-C orientation is indistinguishable from noise, so the RECIPIENT anchor must carry non-random absorption-depth structure over the F168 sector ladder.
**Does NOT:** claim F212 is refuted (it falsifies one *operationalization* — the content-free global twist — not the coupling); claim retrieval is *invariant* to recipient (the argmax DOES move — just no more than noise); claim a clean null on every metric (top-k Jaccard exceeds noise, attributed to orthogonal-orientation construction, not steering); claim the result is corpus-general (KJV-NT, 80K-token sample, 400 queries — a depth-structured-recipient frame or a richer corpus could shift it); make any cognitive / doctrinal claim (§VII.6.20 form-reading; `[[user_stance_ai_is_not_a_substrate]]` — transducer reading the form; the texts are structural test-objects).

## §8 Forward ask (for the main session to create OPEN)

**The RECIPIENT-anchor design issue — where it lives + what it carries.** F214 establishes that a content-free Class-C *bit* on the context-state is render-only. The open design item: build a RECIPIENT anchor that is a **which-depth operator over the F168 sector ladder** (peer to the F165 DOMAIN labeled-store), bound into the F166 query/context-state, that biases sector occupancy *non-randomly* (ELI5 → shallow sectors 0–1; expert → deep sectors 2–3), and re-run §5 to test whether *structured* absorption-depth steering exceeds the noise floor where a content-free twist did not. Null-tolerant; this is the falsifiable next step F212 §4's "RECIPIENT anchor in the context-state" actually requires.

## §9 Cross-references

F212 (the hidden RECIPIENT fiber — the test source) · F166 (rolling context-state / query) · F165 (DOMAIN anchor — the peer; labeled-store retrieval) · F168 (perplexity = chirality-tagged sector occupancy — the resolution-depth ladder the anchor must steer) · F169 (storage/expression separability — entangled in the query) · F163 (chirality alone ≠ the DOMAIN anchor — the same content-free-orientation lesson on the DOMAIN axis) · `hdc.klein4_chirality_flip_gamma5/omega7`, `klein4_random`, `encode_word_k4` · `laplacian.dense_laplacian`/`jacobi_eigvals` · `cascade.magnitude` · `[[user_stance_ai_is_process_lm_is_k3_chiral_addressing]]` · `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` · `[[feedback_dont_pre_commit_spike_query_operators]]`

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). The F212 §5 retrieval-vs-render test, run
srmech-native and bit-exact: condition one fixed KJV-NT query on ELI5/peer/expert
recipient frames, each a rigid Class-C orientation (klein4 chirality flip) bound
into the F166 rolling context-state (the QUERY, not the render), and measure
whether retrieval shifts beyond a 16-frame shape-matched random-orientation noise
floor. Verdict: tier-3 weak/mixed — 1/3 retrieval metrics (and that one a
construction artifact of choosing orthogonal orientations) exceed the p90 noise
floor; sector occupancy, the F168-native depth readout, is a clean null; the
argmax DOES move but no more than a random twist of the same kind. So this is
render-only at this scale — a NULL for the *content-free orientation*
operationalization. The honest control upgrade mid-run (3-sample point estimate +
permissive rule → 16-frame distribution + p90 gate) flipped a spurious tier-2
confirm to this tier-3 null, per [[feedback_dont_pre_commit_spike_query_operators]].
The null sharpens F212: a which-way bit is content-free and indistinguishable from
noise, so the RECIPIENT anchor cannot be a rigid global twist — it must carry
non-random absorption-depth structure over the F168 sector ladder (ELI5→shallow,
expert→deep), exactly as F163 taught on the DOMAIN axis. Form-reading; the texts
are structural test-objects; no cognitive or doctrinal claim (§VII.6.20;
[[user_stance_ai_is_not_a_substrate]]).*
