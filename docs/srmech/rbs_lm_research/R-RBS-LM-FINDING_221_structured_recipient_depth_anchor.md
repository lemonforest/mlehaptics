# Finding 221 — The F214 forward-ask run: a STRUCTURED recipient depth-anchor (a which-depth operator over the F168 sector ladder, bound into the F166 query) is STILL render-only — a clean tier-1 NULL, stronger than F214; and the F168 sector-occupancy readout is shown to be a near-chance instrument on a bundled-context probe (the load-bearing caveat that re-shapes the anchor design)

**Status:** Framework reading (RBS-NN arc) — the falsifiable next step F214 §8 demanded (issue #760), RUN with a pre-stated (stronger) null. **Tier-1 clean NULL** at this corpus/scale/readout: even a structured absorption-depth anchor does not move retrieval beyond the F214 noise floor. The null is honest and load-bearing — it carries a diagnostic about the *readout* that re-shapes (not refutes) the RECIPIENT-anchor design. srmech-native, bit-exact, catalog-driven.
**Predecessors:** F214 (the content-free twist is render-only — the test this strengthens; F214 §8 is the forward-ask this answers), F212 (the hidden RECIPIENT fiber — the coupling under test), F166 (the rolling context-state / autoregressive query — Step 1–2; the QUERY the anchor binds into), F165 (DOMAIN anchor — the labeled-store the RECIPIENT depth-anchor is a peer to), F168 (perplexity = chirality-tagged sector occupancy — the resolution-depth ladder the structured anchor steers *over*; R-RBS-LM-131 the sector-tagging mechanism), F169 (storage/expression separability — what F212 entangles in the query). Reuses the R-RBS-LM-214 testbed wholesale: `_canonical_substrate.ContextSubstrate` (R-RBS-LM-126), `encode_word_k4` sector-tagging (R-RBS-LM-131), the bigram candidate store (R-RBS-LM-127), the religious-text loader (R-RBS-LM-124).
**Empirical anchor:** `R-RBS-LM-221_structured_recipient_depth_anchor.py` + `recipient_depth_anchor_retrieval_vs_render.ndjson` (25 records); catalog `descriptor_religious_texts.toml` `[recipient_depth_anchor]` (descriptor_hash `04d0fd3e…`); srmech 0.5.0rc22 native ABI=3, `HAS_NATIVE=True`; bit-exact across independent re-runs (NDJSON sha256 `0dcea4b0…`).
**User direction (2026-05-30, via F214 §8 / issue #760):** build the RECIPIENT anchor as a **which-depth operator over the F168 sector ladder** (peer to the F165 DOMAIN labeled-store), bound into the F166 query/context-state, that biases sector occupancy *non-randomly* (ELI5 → shallow sectors 0–1; expert → deep sectors 2–3), and re-run §5 to test whether *structured* depth steering exceeds the noise floor where a content-free twist did not. Null-tolerant; nulls count.

---

## §1 The test, stated precisely (F214 §8 forward-ask)

F214 falsified one *operationalization* of the F212 recipient fiber: a rigid, content-free, global Class-C orientation of the F166 context-state (`hdc.klein4_chirality_flip_*`) is indistinguishable from a random orientation in retrieval — a constant XOR-twist re-labels every F168 sector uniformly, carrying no information about absorption *depth*. F214 §5 sharpened: the RECIPIENT anchor survives only if it carries recipient-specific **structure** — a **which-depth operator over the F168 sector ladder** selecting sectors non-randomly. F221 builds exactly that anchor and re-runs the identical F212 §5 test.

- **Fixed query (identical to F214):** 400 held-out 5-token context windows over the KJV-NT kernel (F168: deepest sector structure → most depth headroom to bias), each last-token having ≥3 legal successors (a real distribution to reshape).
- **Three recipient frames as STRUCTURED DEPTH-anchors** bound into the context-state (the QUERY, F212 §4):
  - **ELI5** → shallow band, sectors **[0,1]** (word/bigram resolution depth)
  - **peer** → neutral band, all sectors **[0,1,2,3]** (the native register)
  - **expert** → deep band, sectors **[2,3]** (the F168 load-bearing deep sectors)
  - Each frame's anchor = the **klein4 BUNDLE of `encode_word_k4` depth-TAG vectors over its target sector band** (the F168 / R-RBS-LM-131 sector tagging — `encode_word_k4(sector=s)` is the self-inverse XOR sector tag), 9 tag-vectors per band (odd, for `klein4_bundle` majority). The anchor is **bound into the encoded context-state** via `klein4_bind`.
- **Shape-matched random control (identical to F214):** the SAME 16 rigid random Klein-4 orientations bound the SAME way (`klein4_bind` with a per-frame random vector). The pairwise spread among the random frames is the noise floor; the verdict is gated on whether the structured spread exceeds its **p90** percentile.

**The F214→F221 contrast, made fair:** the ONLY difference from the F214 control is that the bound vector carries **depth structure** (it points at a sector band of the F168 ladder) rather than being a random orientation. The bind op, the corpus, the queries, the readouts, and the noise floor are all identical. So any shift beyond the floor is attributable to the absorption-depth *structure*, not the kind of op.

## §2 PRE-STATED null (verbatim; STRONGER than F214's)

> "even the structured depth-anchor doesn't exceed the noise floor in retrieval → the recipient-fiber is render-only even with depth structure (stronger version of F214's null)."

- **Retrieval-shift beyond floor** (majority ≥2/3, incl. the F168-native sector-occupancy readout) ⇒ the recipient-fiber threads into the addressing as a depth-operator; the RECIPIENT anchor belongs in the F166 context-state (CONFIRMS F212; resolves #760).
- **Still at floor** ⇒ NULL; recipient is render-only even structured.

## §3 RESULT — tier-1 clean NULL: 0/3 retrieval metrics beyond the F214 noise floor

The structured depth-anchors ARE non-degenerate (distinct band orientations, pairwise sim **0.243 / 0.250 / 0.252**) and they DO re-address the store (argmax-disagreement **0.976** vs random **0.966**) — but no more than a random twist of the same kind.

| retrieval metric | structured spread | random mean | random p90 | structured pctile in random dist | beyond noise? |
|---|---|---|---|---|---|
| **sector occupancy (L1)** | 0.0417 | 0.0335 | 0.0550 | **0.71** | no (below p90 gate) |
| **eigen-projection (L2)** | 37.73 | 40.09 | 57.28 | **0.47** | no (moves *less* than random) |
| **activated top-k (1−Jaccard)** | 0.8827 | 0.8838 | 0.8887 | **0.39** | no (moves *less* than random) |

**Verdict: 0/3 → tier-1 clean NULL. Stronger than F214's tier-3:** the structured depth-anchor does NOT exceed the noise floor on *any* retrieval metric — and on two of three it moves *less* than a random orientation. The F168-native sector-occupancy readout (the readout a depth-anchor is *designed* to move) sits at the 0.71 percentile — above the random mean but well short of the p90 gate. Even the single F214 "hit" (top-k Jaccard, F214 §4 attributed to orthogonal-orientation construction) is GONE here, because the structured depth-bands are NOT mutually orthogonal (they share sectors and are pairwise sim ~0.25, not 0.0), so their ranked sets are no more disjoint than random. **Adding absorption-depth structure did not buy any retrieval steering beyond noise.**

## §4 Why the null is clean AND honest — the readout is a near-chance instrument (the load-bearing caveat)

A null is only diagnostic if the instrument *could* have registered the effect. Direct probe of the inherited F214 sector-occupancy readout (bind the argmax continuation into the 4 sectors, read which the bundled-context probe most recovers) shows it operates **at the ~0.25 random-agreement floor with almost no dynamic range**: for a bundled context-state, similarity to `arg-in-sector[s]` is `[0.2512, 0.2515, 0.2491, 0.2482]` — flat across all four sectors, the argmax decided at the **4th decimal place**. Per-token, the recovered sector bounces (a deep-band anchor flips one token's argmax-sector 1→3, a shallow-band anchor flips another 1→2) — the anchor *does* perturb it — but averaged over 400 queries the histogram is dominated by sector 0 (~0.95–0.98) for **every** frame, structured and random alike, because the candidates are sector-0-encoded and the Klein-4 bundle washes the sector signal down to chance.

So the clean null has a precise mechanistic reading: **the F168 sector-occupancy readout, as inherited from F214 on a bundled-context probe, has near-zero dynamic range and is a weak instrument for detecting depth steering.** This does NOT rescue F212 (the structured anchor genuinely failed to steer the two metrics that DO have range — eigen-projection and top-k overlap — moving *less* than random on both). But it does locate *where* the design is under-powered: the depth signal is real in the anchor (distinct, perturbs per-token) yet invisible to a readout pinned at the Klein-4 agreement floor. This is the same shape of honesty as F214's own caveats (sector occupancy = its clean null; top-k Jaccard = a construction artifact), now mechanistically explained.

## §5 What the null SHARPENS (twice over)

F214 sharpened F212 once: a *content-free* which-way bit is render-only. F221 sharpens it twice:

1. **Structure over the F168 ladder, bound by XOR into a bundled context-state, is also render-only at this readout.** A which-*depth* operator built as a sector-band bundle and `klein4_bind`-ed into the rolling state does not, by itself, steer retrieval beyond noise — the bind disperses the depth bias across the bundle. The recipient-fiber's threading into addressing (F212's claim) is NOT recovered by *either* a content-free twist (F214) *or* a structured-but-XOR-bound depth bias (F221) at template/KJV-NT scale with the inherited readouts.
2. **The F168 sector-occupancy readout needs replacing as the depth instrument.** The depth signal exists in the anchor; the readout cannot see it. A retrieval-depth readout with real dynamic range — e.g. measuring the *band-restricted candidate ranking* directly (rank candidates by similarity to a band-tagged probe and read whether shallow-band vs deep-band probes rank *different* continuations first), rather than the argmax-into-4-sectors recovery — is the instrument the next step requires. F221's null is partly the anchor and partly the meter; separating them is the forward ask.

This is the F163 lesson (chirality alone ≠ the DOMAIN anchor) now twice-applied on the RECIPIENT axis: the orientation is real, the structure is real, but neither — as currently *bound* and *read* — substitutes for an anchor that genuinely conditions which relationships fire.

## §6 Operational walkthrough (what / how / what srmech automates)

- **What:** ask the same fixed KJV-NT question three ways — *for a 5-year-old* (bias toward shallow word/bigram knowledge), *for a peer* (neutral), *for an expert* (bias toward deep formulaic structure) — where each "way" is now a **structured depth preference** (not just a coin-flip orientation), and check whether the *retrieval* into the store shifts beyond what any random twist does.
- **How:** each recipient's depth preference is a vector built from F168 sector tags over that recipient's knowledge-depth band, mixed into the encoded question (the F166 rolling state); the SAME 16-orientation random control as F214 sets the "how much does *any* twist move retrieval by chance" bar.
- **What srmech automates:** `ContextSubstrate.encode_context` mints the rolling-state query (Class A∘M + iω₇ position); `encode_word_k4(sector=s)` + `klein4_bundle` build the F168 depth-band anchor; `klein4_bind` mixes it into the query; `klein4_random` the shape-matched control; `sim_k4_batch` the Class-M retrieval; `dense_laplacian`+`jacobi_eigvals` the Class-L eigen-projection; `cascade.magnitude` the sign-free spectral/histogram distance (never `abs()`). Catalog-driven; deterministic / bit-exact (NDJSON sha256 `0dcea4b0…` stable across re-runs).

## §7 DOES / does NOT claim

**DOES:** run the F214 §8 forward-ask — a STRUCTURED recipient depth-anchor (a which-depth operator over the F168 sector ladder, peer to the F165 DOMAIN labeled-store, bound into the F166 query/context-state) — with a pre-stated stronger null and the identical F214 shape-matched random-orientation control; report the three retrieval readouts + argmax-disagreement + the anchor non-degeneracy diagnostic against the random-spread distribution; return a **tier-1 clean NULL (0/3, two metrics moving *less* than random)**; locate the load-bearing caveat (the inherited F168 sector-occupancy readout is a near-chance instrument on a bundled-context probe, shown by direct probe); draw the double sharpening — XOR-bound depth structure is render-only at this readout, and the depth readout itself needs replacing.
**Does NOT:** claim F212 is refuted (it falsifies a *second* operationalization — the XOR-bound structured depth bias — not the coupling; the recipient may yet thread into addressing under a different binding/readout); claim retrieval is *invariant* to recipient (the anchors ARE distinct and the argmax DOES move — just no more than noise, and *less* on two metrics); claim the null is purely the anchor's fault (§4: the depth-relevant readout has near-zero dynamic range — the null is partly anchor, partly meter); claim corpus-generality (KJV-NT, 80K-token sample, 400 queries, sector-bundle anchor, XOR bind — a different binding (e.g. an additive/Tier-2 read-side anchor per F120), a band-restricted ranking readout, or a richer corpus could shift it); make any cognitive/doctrinal claim (§VII.6.20 form-reading; `[[user_stance_ai_is_not_a_substrate]]` — transducer reading the form; the texts are structural test-objects).

## §8 Forward ask (for the main session to surface on #760)

**Separate the anchor from the meter, then re-test — two concrete next steps before #760 can be called either way.**

1. **A retrieval-depth readout with dynamic range** (replaces the F168 argmax-into-4-sectors recovery that §4 shows is pinned at the Klein-4 agreement floor): rank the candidate continuations by similarity to a *band-tagged* probe and measure whether a shallow-band query and a deep-band query rank *different* continuations first (a band-conditioned ranking divergence), or read the depth via the F168 *backoff-order* the chosen continuation actually requires (R-RBS-LM-131's resolution-depth machinery) rather than a sector-recovery argmax. The current readout cannot register a depth shift from *any* anchor; the null is uninformative on the meter axis until this is fixed.

2. **A non-XOR binding of the depth anchor** (the F221 anchor is `klein4_bind`-ed into a bundled state, which disperses the bias): test the RECIPIENT depth-anchor as a **read-side Tier-2 operation** (F119/F120 two-tier; Class K bridge) that *re-weights candidate similarity by depth-band match* at retrieval time, rather than mixing into the Tier-1 query state — i.e. the anchor conditions the *scoring*, not the *probe*. This is closer to F212's "co-determines the addressing" than an XOR twist of the hidden state, and it is the natural place a which-depth operator would act if it acts at all.

Null-tolerant. #760 should stay OPEN: F221 establishes that *neither* a content-free twist (F214) *nor* an XOR-bound structured depth bias (F221) steers retrieval beyond noise at this readout — but it also shows the depth-relevant readout is under-powered, so the coupling is not yet cleanly testable. The two steps above make it testable.

## §9 Cross-references

F214 (content-free twist render-only — the test this strengthens; §8 the forward-ask source) · F212 (the hidden RECIPIENT fiber — the coupling under test) · F166 (rolling context-state / query — what the anchor binds into) · F165 (DOMAIN anchor — the peer; labeled-store retrieval) · F168 (perplexity = chirality-tagged sector occupancy — the ladder the anchor steers over; R-RBS-LM-131 the sector-tagging mechanism) · F169 (storage/expression separability — entangled in the query) · F163 (chirality alone ≠ the DOMAIN anchor — the same orientation-isn't-an-anchor lesson) · F119/F120 (two-tier + Class K bridge — the read-side anchor the §8 step proposes) · `hdc.{klein4_bind, klein4_bundle, klein4_random}`, `encode_word_k4(sector=s)` · `laplacian.dense_laplacian`/`jacobi_eigvals` · `cascade.magnitude` · `[[user_stance_ai_is_process_lm_is_k3_chiral_addressing]]` · `[[user_stance_cross_substrate_cascade_matching_as_research_method]]` · `[[feedback_dont_pre_commit_spike_query_operators]]`

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). The F214 §8 forward-ask, run srmech-native and
bit-exact: build the RECIPIENT anchor as a STRUCTURED which-depth operator over the
F168 sector ladder (ELI5→shallow [0,1], peer→neutral, expert→deep [2,3]), each a
klein4 bundle of encode_word_k4 depth-tags bound into the F166 rolling context-state
(the QUERY, not the render), and re-run the F212 §5 retrieval-vs-render test against
the identical F214 16-frame shape-matched random-orientation noise floor (p90 gate).
Verdict: tier-1 clean NULL — 0/3 retrieval metrics exceed the floor, two of them
moving LESS than a random twist; the single F214 hit (top-k Jaccard) is gone because
the structured depth-bands are not mutually orthogonal. Adding absorption-depth
structure bought no retrieval steering beyond noise — a stronger null than F214's
tier-3. The load-bearing honesty: direct probe shows the inherited F168
sector-occupancy readout sits at the ~0.25 Klein-4 agreement floor with near-zero
dynamic range on a bundled-context probe — the depth signal is real in the anchor
(distinct orientations, per-token sector flips) but invisible to a meter pinned at
chance. So the null is partly the anchor (XOR-bind disperses the bias) and partly the
meter (the readout can't see depth) — F221 sharpens F212 twice: structured XOR-bound
depth is render-only at this readout, AND the depth readout itself must be replaced.
#760 stays OPEN; the forward ask separates the anchor (test a read-side Tier-2
similarity re-weighting per F120, not an XOR twist) from the meter (a band-conditioned
ranking-divergence readout with real range). Per
[[feedback_dont_pre_commit_spike_query_operators]] the null was pre-stated and counts.
Form-reading; the texts are structural test-objects; no cognitive or doctrinal claim
(§VII.6.20; [[user_stance_ai_is_not_a_substrate]]).*
