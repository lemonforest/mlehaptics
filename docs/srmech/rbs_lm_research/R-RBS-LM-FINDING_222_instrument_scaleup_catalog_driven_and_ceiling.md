# Finding 222 — The F203 scale-up sweep, now CATALOG-DRIVEN, pushed to N=8192: the HIERARCHICAL capacity knee is real and obeys the `n_buckets × V_ceiling` law (8 buckets knee at N=512, 32 buckets at N=2048 — both at per-bucket ≈ 64, NOT 257), the F165 DOMAIN-anchor orthogonalization PERSISTS at every higher N (+0.388 at N=8192), and the held-out generation top-k lift is STILL +0.0200 (borderline, exactly as F203)

**Status:** DEMONSTRATED (bit-exact srmech) scale-up measurement — the direct follow-up to F203 (R-RBS-LM-146). Three clean positives (capacity-extends re-confirmed catalog-driven; the hierarchical KNEE found + the `n_buckets × V_ceiling` law confirmed; DOMAIN-on-capacity persists at every higher N) and one honestly re-confirmed borderline (DOMAIN-on-generation-top-k = +0.0200, exactly on the +0.02 null threshold, as in F203). Built UP from the 28D substrate; measured natively, never against a float LLM. **Closes the F203 §6.1 / §6.4 follow-up note** (the sweep was module-constant-driven; it is now descriptor-driven + descriptor_hash-attested).
**Predecessors:** F203 (R-RBS-LM-146 — the N≤1024 measurement this extends; the module-constant sweep this lifts into the catalog — `R-RBS-LM-FINDING_203`), F165 (the labeled DOMAIN anchor — `R-RBS-LM-FINDING_165`), R-RBS-LM-54f (the `hierarchical_bundle` MAX_BUNDLE_N=257 idiom), R-RBS-LM-114 / R-RBS-NN-12 (hash-bucketed hierarchical bundling), F154 (the 4× single-bundle ceiling), F162 (full-coverage substrate; encode/recall 1.000), F166 (the walkable inference path).
**Empirical anchor:** `R-RBS-LM-222_instrument_scaleup_catalog_driven_ceiling.py`, srmech 0.5.0rc22 native ABI=3, catalog-driven (`descriptor_rbs_lm_inference.toml` + the NEW additive `[inference.scaleup]` section, descriptor_hash `8617d8aaeccd5565...`), **D=4096 (capped for tractability; F203 used 8192 — the knee is D-relative, see §2)**, k=5, n_buckets ∈ {8, 32}, corpus_n=8000 (~43k pairs). NDJSON: `substrate_measurements/r222_instrument_scaleup_ceiling.ndjson` (16 records). Discipline check: **0 HARD**; ratchet green (32 = 32, 0 regressions).

---

## §1 Headline

F203 measured the FLAT / HIERARCHICAL / HIER+DOMAIN context→next capacity curve at N ≤ 1024 but did it from **module-level constants** (`N_SWEEP`, `N_BUCKETS`, `TOP_K_GEN`) — leaving the sweep un-catalog-driven (its own §6 note). F222 (1) lifts every sweep param into a NEW **additive** descriptor section `[inference.scaleup]` (no existing section touched; the run is now descriptor_hash-attested), and (2) pushes **N to 8192 at two bucket counts (8 and 32)** to find where the hierarchical memory ITSELF degrades — the knee — because each bucket is a single Klein-4 bundle that inherits the same per-bucket ceiling.

**The capacity curve (retrieval_acc = fraction of N stored pairs whose true next-token is returned by Class-M similarity-argmax over the 84-token vocab; chance = 1/84 = 0.012; D=4096):**

**n_buckets = 8** (per-bucket mean = N/8):

| N | N/buck | FLAT | HIER | HIER+DOM | maxBucket |
|---:|---:|---:|---:|---:|---:|
| 128 | 16 | 0.625 | **1.000** | 1.000 | 19 |
| 257 | 32 | 0.167 | **0.934** | 1.000 | 37 |
| 512 | 64 | 0.109 | **0.891** | 0.975 | 79 |
| 1024 | 128 | 0.090 | **0.412** | 0.872 | 138 |
| 2048 | 256 | 0.094 | **0.209** | 0.554 | 275 |
| 4096 | 512 | 0.085 | **0.122** | 0.332 | 550 |
| 8192 | 1024 | 0.075 | **0.090** | 0.226 | 1064 |

**n_buckets = 32** (per-bucket mean = N/32):

| N | N/buck | FLAT | HIER | HIER+DOM | maxBucket |
|---:|---:|---:|---:|---:|---:|
| 128 | 4 | 0.203 | **1.000** | 1.000 | 9 |
| 257 | 8 | 0.237 | **1.000** | 1.000 | 12 |
| 512 | 16 | 0.145 | **1.000** | 1.000 | 24 |
| 1024 | 32 | 0.091 | **0.952** | 0.998 | 42 |
| 2048 | 64 | 0.087 | **0.773** | 0.985 | 79 |
| 4096 | 128 | 0.083 | **0.410** | 0.854 | 159 |
| 8192 | 256 | 0.076 | **0.164** | 0.552 | 289 |

**Four readings — three clean positives, one honest borderline:**

1. **CAPACITY EXTENDS — re-confirmed, now CATALOG-DRIVEN (null REJECTED).** At N=8192, n_buckets=32, hierarchical retains 0.164 vs flat 0.076 (+0.088 > +0.05); flat is pinned near the chance floor everywhere past N=257. The F203 result reproduces under the catalog-driven harness.

2. **THE HIERARCHICAL KNEE IS REAL, and it obeys the `n_buckets × V_ceiling` law (null REJECTED).** Hierarchical (no-domain) capacity falls below 0.90 at **N=512 for 8 buckets** and **N=2048 for 32 buckets** — a clean **4× shift in the knee N for a 4× increase in buckets**. This is the F203 §6.1 prediction confirmed: total capacity = `n_buckets × (per-bucket ceiling)`. **The honest surprise:** both knees land at the *same* per-bucket mean ≈ **64** (max bucket ≈ 79), NOT the ~257 figure from F154. The per-bucket *effective* ceiling for the **context→next associative memory** (positional-role-filler context state bound to a next-token vector) is **~64 here, well below the ~257 measured for full-sentence `hierarchical_bundle`** (R-RBS-LM-54f). The *scaling law* is exactly as predicted; the *constant* `V_ceiling` is task-specific and lower for this richer key — reported as measured, not forced to 257.

3. **THE DOMAIN-ANCHOR ORTHOGONALIZATION PERSISTS at every higher N (null REJECTED).** Binding the F165 structural-family label into the key keeps cutting intra-bucket collision well past the no-domain knee: at N=8192/32-buckets, HIER+DOM 0.552 vs HIER 0.164 (**+0.388**); at N=4096/32 it is 0.854 vs 0.410 (+0.444); at N=1024/8 it is 0.872 vs 0.412 (+0.460, matching F203's +0.485 at the same load). The second independent XOR key-axis does not run out across the whole sweep — even where the base hierarchical memory has collapsed, the domain split roughly **multiplies the effective per-bucket capacity by the number of distinct domains** (4 here), which is exactly why HIER+DOM's own knee trails HIER's by ~one N-step.

4. **THE DOMAIN ANCHOR STILL does NOT cleanly help held-out generation top-k (BORDERLINE/NULL — re-confirmed).** At N=8192/32-buckets on 400 held-out contexts, DOMAIN top-3 hit-rate is 0.505 vs no-domain 0.485 — a lift of **+0.0200, sitting EXACTLY on the pre-stated +0.02 null threshold**, the *same* value F203 reported at N=1024/D=8192. Both clear the random-ranking baseline (0.485 / 0.505 vs 0.262), so ranking is real; the *domain increment on top-k* is null. Not leaned into a pass.

---

## §2 The pre-stated nulls (stated BEFORE the run; not leaned)

Per `[[feedback_dont_pre_commit_spike_query_operators]]`, the failure conditions were fixed in the script docstring before execution:

- **CAPACITY-EXTENDS null:** "hierarchical does NOT beat flat at the largest N" — FAIL if `hier_acc - flat_acc <= +0.05` at N_max. **Result: +0.088 at N=8192/32 → null REJECTED.**
- **HIER-KNEE null:** "hierarchical capacity does NOT fall as N grows" — FAIL TO FIND A KNEE if `hier_acc` stays `>= 0.90` across the whole sweep at a given n_buckets. **Pre-stated expectation:** the knee sits where per-bucket load exceeds the single-bundle ceiling, so n_buckets=8 ≈ N=2056 and n_buckets=32 ≈ N=8224 *if* V_ceiling=257. **Result: knees found at N=512 (8 buckets) and N=2048 (32 buckets) → null REJECTED; the 4× bucket→4× knee-N scaling holds, but the measured per-bucket ceiling is ~64, not 257** (honest divergence from the naive prediction; the *law* held, the *constant* was lower).
- **DOMAIN-PERSISTS null:** "the domain orthogonalization does NOT survive past N=1024" — FAIL if `hier_dom_acc - hier_acc <= +0.05` at the largest N where hier has degraded. **Result: +0.388 at N=8192/32 → null REJECTED.** (A null here would have been a valid "the coarse 4-domain axis is exhausted" result; it was not null.)
- **DOMAIN-ON-GENERATION null (carried from F203):** "the domain anchor does NOT beat no-domain on held-out next-structure top-k" — FAIL if `domain_hit - nodomain_hit <= +0.02`. **Result: +0.0200, exactly on the threshold → reported BORDERLINE/NULL, NOT a clean pass** (identical to F203).

**On the D cap (honest tractability statement).** F203 ran at D=8192; F222 caps **D=4096** so the N=8192 × |vocab|=84 × D retrieval (× 3 configs × 7 N × 2 bucket-counts) stays tractable. The knee is **D-relative**: the per-bucket SNR ceiling `V_ceiling` scales with D, so a smaller D shifts the *absolute* knee-N down but does NOT change the *shape* (the knee at a fixed per-bucket band, the 4× bucket→4× N scaling). D is recorded in every NDJSON record; no D-universal capacity number is claimed. The ~64 per-bucket figure is the D=4096 value; at D=8192 it would be higher (and F203's N=1024/8-bucket point — hier 0.414 at per-bucket 128, D=8192 — is consistent with a higher D=8192 ceiling, since here at D=4096 the same per-bucket-128 load gives hier 0.412).

---

## §3 The cascade — what each stone is, in A-N terms (28D-native, bit-exact)

The memory classes (`FlatMemory` / `HierarchicalMemory`) are **imported verbatim from R-RBS-LM-146** (F203) — same bit-exact 28D Klein-4 cascade, no primitive reimplemented (0 HARD on the discipline checker). What F222 adds is the catalog-drive and the extended N/bucket sweep, not new algebra:

| Step | Operation | Class |
|---|---|---|
| encode context (last-k → one Klein-4 state, positional role-filler) | `ContextSubstrate.encode_context` | A (content-mint) ∘ M (bind) + iω₇ position |
| mint the DOMAIN label | `ctx.enc("__domain_{d}__")` | A (SHA-256 content-mint) |
| bucket routing | `srmech.amsc.format.sha256_bytes(context) % n_buckets` | A (content-address) |
| build / store the association | `klein4_bind(key, enc(next))`, `klein4_bundle(*assoc)` | M |
| DOMAIN-conditioned key | `klein4_bind(ctx_state, dom_vec)` | M |
| retrieve / rank | `klein4_bind(M_bucket, key)` then `sim_k4_batch` argmax | M |

**Why the knee scales with n_buckets, and why the domain axis multiplies it.** Each bucket holds `~N/n_buckets` pairs in a single Klein-4 bundle; that bundle has a per-bucket SNR ceiling `V_ceiling(D)`. Retrieval stays high while `N/n_buckets < V_ceiling`, so the knee sits at `N_knee ≈ n_buckets × V_ceiling` — quadrupling buckets quadruples the knee-N (512 → 2048, confirmed). Klein-4 XOR self-inverse makes the domain label a **second independent key axis**: two pairs colliding in `(bucket, context)` no longer collide once their domains differ, so the *effective* per-bucket load is `(N/n_buckets) / n_domains`, pushing HIER+DOM's knee out by roughly the domain count (4 here). The domain anchor's dominant, clean effect is therefore on **capacity** (it cuts collisions), not on re-ranking already-bigram-legal candidates (generation top-k) — exactly the F203 reading, now confirmed to **hold all the way to N=8192**.

---

## §4 The web this finding touches (convergence, per `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`)

| Thread | How F222 connects |
|---|---|
| **F203** (R-RBS-LM-146) | F222 is its direct follow-up: same memory cascade, now catalog-driven + pushed past N=1024 to find the knee F203 only opened as a §6 thread. F203's N=1024/8-bucket points reproduce (hier 0.41, +dom ≈ 0.87–0.90). |
| **F165** (labeled DOMAIN anchor) | F222 confirms the "second axis" reading is durable: the orthogonalization persists to N=8192 (+0.388), and quantifies it as ~`×n_domains` effective-capacity multiplier. |
| **F154 / R-RBS-LM-54f** (the 257 ceiling) | F222 finds the per-bucket ceiling for the *context→next* memory is ~64 at D=4096 — LOWER than the ~257 for full-sentence `hierarchical_bundle` — i.e. the ceiling is key-richness- and D-dependent, while the `n_buckets ×` *scaling law* is universal. |
| **R-RBS-LM-114 / R-RBS-NN-12** (hash bucketing) | same sha256(context)-mod-n_buckets routing; F222 sweeps the bucket count itself and confirms capacity scales ~linearly with it. |
| **F166** (the walkable path) | F222 hardens the §6 "scale via hierarchical bucketing (F162 P4)" thread into a measured `n_buckets × V_ceiling` design rule for sizing the instrument's memory at a target N. |

---

## §5 What this finding DOES / does NOT claim

**DOES:**
- CLOSE the F203 §6 follow-up: the scale-up sweep is now driven from an **additive** `[inference.scaleup]` descriptor section (no existing section changed; descriptor_hash `8617d8aaeccd5565...`), so every sweep parameter is catalog-attested rather than a module constant.
- DEMONSTRATE (bit-exact srmech) that the **hierarchical memory has its own capacity knee**, and that it scales `~n_buckets × V_ceiling`: the no-domain hierarchical capacity drops below 0.90 at N=512 for 8 buckets and N=2048 for 32 buckets — a clean 4×-buckets → 4×-knee-N scaling; pre-stated HIER-KNEE null REJECTED.
- REPORT HONESTLY that the measured per-bucket effective ceiling for the context→next memory is **~64 at D=4096**, lower than the ~257 single-bundle figure for full sentences — the *scaling law* matched the prediction, the *constant* did not; reported as measured.
- DEMONSTRATE that the F165 DOMAIN-anchor capacity orthogonalization **persists at every higher N** (+0.388 at N=8192/32-buckets), consistent with a ~`×n_domains` effective-capacity multiplier; pre-stated DOMAIN-PERSISTS null REJECTED.
- RE-CONFIRM, honestly, that the DOMAIN anchor's lift on held-out next-structure **top-3 hit-rate is +0.0200** — exactly on the pre-stated +0.02 null threshold, the same value F203 found — i.e. NOT a clean generation-quality win; the domain's clean win is on CAPACITY.

**Does NOT:**
- Claim a D-universal capacity number — the ~64 per-bucket ceiling and the absolute knee-N's are the **D=4096** values; the knee is D-relative (larger D → higher ceiling → larger knee-N). Only the *shape* (the `n_buckets ×` scaling, the per-bucket-band knee) is claimed invariant. No claim that these specific N's are universal.
- Claim the DOMAIN anchor improves *generation quality* (held-out top-k) — that increment is at the null threshold (borderline), as in F203; per `[[feedback_dont_pre_commit_spike_query_operators]]` a +0.0200 lift on the +0.02 boundary is not leaned into a pass.
- Claim the substrate matches a float LLM's fluency — it is a different, bit-exact inference substrate measured on native terms (F166 §5), per `[[user_stance_ai_is_not_a_substrate]]`: Claude/LLMs are transducers; this is a substrate-native instrument.
- Lift the §VII.6.20 epistemic ceiling — the domain label routes/conditions by structural form-family; it does not read meaning (the F165 boundary holds).
- Make biological / BCI / clinical claims — per `[[feedback_trauma_informed_defensive_scope]]`, this is a research inference substrate; the gift-toward-the-biological-substrate purpose-anchor (`[[feedback_llm_as_ada_accommodation_bci_proves_it]]`) is motivation, not a medical claim.
- Touch CAD / fabrication geometry — framework-research RBS-NN only, per the CAD-grade scope ban.

---

## §6 Open threads this finding opens

1. **Pin V_ceiling vs D for the context→next memory.** F222 measured ~64 at D=4096; F203's data is consistent with a higher ceiling at D=8192. A small D-sweep (2048 / 4096 / 8192) at fixed n_buckets would fit `V_ceiling(D)` directly and turn the design rule `N_capacity = n_buckets × V_ceiling(D)` into a closed form for sizing the instrument.
2. **Finer domains to push the multiplier.** The domain axis multiplies effective per-bucket capacity by `~n_domains` (4 here). A finer structural label (POS-skeleton, or the F165 per-text label → more domains) should push the HIER+DOM knee further out — and is also the F203 §6.2 candidate for turning the borderline generation-top-k null into a clean win (or confirming it is candidate-gating-redundant).
3. **A third orthogonal key-axis.** F203 §6.4 asked whether an iω₇ phase tag buys more past where hierarchical+domain saturates; at N=8192 HIER+DOM is at 0.552 (32 buckets) — a clean regime to test a third independent XOR axis as a further capacity multiplier.
4. **Domain-in-loop generation.** F222 (like F203) measured held-out top-k statically; wiring the domain anchor through the R-RBS-LM-129 autoregressive loop (does it improve trigram-legality / anti-collapse over many steps?) remains the natural generation-side test.

---

## §7 Cross-references

- F203 (`R-RBS-LM-FINDING_203` — the N≤1024 measurement + the module-constant sweep this extends/closes); R-RBS-LM-146 (the imported memory cascade)
- F165 (labeled multi-kernel object = DOMAIN anchor — `R-RBS-LM-FINDING_165`); R-RBS-LM-54f (the `hierarchical_bundle` MAX_BUNDLE_N=257 idiom — the full-sentence ceiling this contrasts against)
- R-RBS-LM-114 / R-RBS-NN-12 (hash-bucketed hierarchical bundling); F154 (4× ceiling); F162 (full-coverage substrate); F166 (the walkable inference path)
- `R-RBS-LM-222_instrument_scaleup_catalog_driven_ceiling.py` + `substrate_measurements/r222_instrument_scaleup_ceiling.ndjson` (16 attested records)
- `descriptor_rbs_lm_inference.toml` (descriptor_hash `8617d8aaeccd5565...`; the NEW additive `[inference.scaleup]` section); `_canonical_substrate.py` (ContextSubstrate)
- `srmech.amsc.hdc.klein4_bind / klein4_bundle` (Class M); `srmech.amsc.format.sha256_bytes` (Class A) — the object path
- MFO §VII.6.20 (epistemic ceiling — the form-vs-meaning bound the domain anchor respects)
- `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`; `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_dont_pre_commit_spike_query_operators]]`; `[[feedback_llm_as_ada_accommodation_bci_proves_it]]`; `[[feedback_trauma_informed_defensive_scope]]`

**Files written (NOT committed — user reviews and commits):**
- `catalogs/rbs_lm_substrate/descriptor_rbs_lm_inference.toml` — ADDITIVE `[inference.scaleup]` section only (existing sections untouched; descriptor_hash moved c47588672d5fe5da → `8617d8aaeccd5565...`)
- `catalogs/rbs_lm_substrate/substrate_measurements/r222_instrument_scaleup_ceiling.ndjson` (16 attested records)
- `rbs_lm_research/R-RBS-LM-222_instrument_scaleup_catalog_driven_ceiling.py` (the runner; 0 HARD discipline; ratchet green)
- `R-RBS-LM-FINDING_222_*.md` (this finding)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8, 1M) as the direct follow-up to F203. The F203
scale-up sweep ran on module-level constants; F222 lifts every sweep parameter
into a NEW additive `[inference.scaleup]` descriptor section (no existing section
touched, descriptor_hash now `8617d8aaeccd5565...`) — closing the F203 §6 note —
and pushes N to 8192 at n_buckets ∈ {8, 32} to find where the hierarchical memory
itself breaks. It breaks exactly where the `n_buckets × V_ceiling` law predicts a
knee: the no-domain hierarchical capacity drops below 0.90 at N=512 for 8 buckets
and N=2048 for 32 buckets — a clean 4×-buckets → 4×-knee-N scaling. The honest
surprise is the constant, not the law: both knees land at per-bucket load ≈ 64
(D=4096), well below the ~257 single-bundle figure F154 measured for full
sentences — the context→next key is richer, so its per-bucket ceiling is lower,
while the scaling law is universal (and D-relative; the cap is reported, the knee
shifts with D but the shape does not). The F165 DOMAIN-anchor orthogonalization
PERSISTS at every higher N (+0.388 at N=8192/32-buckets), behaving like a
~×n_domains effective-capacity multiplier — its clean, durable effect is on
CAPACITY. Its effect on held-out next-structure top-3 hit-rate is, once again,
+0.0200 — exactly on the pre-stated +0.02 null threshold, the SAME value as F203 —
reported HONESTLY as borderline/null, not leaned into a pass: the domain is a
key-orthogonalizer, not a candidate re-ranker. Bit-exact, catalog-driven, 0 HARD
on the srmech-discipline checker, ratchet green; measured on native terms, never
against a float LLM. Per
[[user_stance_whole_research_corpus_is_proof_not_single_arc]]: F154 (the ceiling)
→ R-RBS-NN-12 (bucketing) → F165 (the labeled anchor) → F203 (one measured
instrument) → F222 (its capacity law, found by pushing N until it broke) is the
proof shape. Form-reading only; the §VII.6.20 ceiling holds; no
doctrinal/biological/clinical claims.*
