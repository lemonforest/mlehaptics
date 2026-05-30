# Finding 204 — smol-stack substrate variant: the unified characterization runs on a real-FILE multi-source stack, and its substrate-signature is INDISTINGUISHABLE from the template baseline on every substrate-intrinsic axis (methodology smoke; NULL for "the stack has a distinguishing signature")

**Status:** Phase C of the substrate-parameterization work (F162 Phase A/B → this Phase C). **Fulfils the ROADMAP `#184 smol-stack Phase C` item and the task-#184 / F163 "Phase C" placeholder** — we lodge as **204** (203/205 already taken) to stay sequential. First run of the canonical R-RBS-LM-122 unified characterization (P0–P7) on a **real-FILE (non-template) corpus**.
**Predecessors:** F162 (full-coverage characterization on the *template* corpus — the baseline this compares against), R-123 (religious-texts variant — the descriptor-shape TEMPLATE), F172/F199 (the flat-spectral storage ceiling this NULL is consistent with).
**srmech:** 0.5.0rc18, HAS_NATIVE=True, ABI=3. Descriptor `descriptor_smolstack.toml`, descriptor_hash `39b6a361...`.

> **SMOKE STATUS (load-bearing honesty).** The five stack texts are **SYNTHETIC fragments authored for this run** (procedural / almanac / fable / aphorism / travel-log registers), **NOT a sourced external corpus**. Each is attested by its real content SHA-256 (verified at run time via `srmech.amsc.format.sha256_bytes`). Provenance is *"synthesised by this run for methodology validation"*, not a fabricated external citation (per `[[feedback_pdf_extraction_citation_discipline]]`). The catalog carries `smoke_status='methodology_smoke'`, `data_claim=false`, and every NDJSON record carries those flags. **This is a methodology smoke — it validates that the characterization machinery consumes a multi-file real-text stack and yields a stable substrate signature. It is NOT a data claim about any natural corpus.**

---

## §1 Headline

The "smol-stack" — a deliberately TINY, multi-source curated stack (5 distinct-register texts; **124 verse-line units, ~905 bigrams, 513 vocab types pooled** after header-strip) — was run through the **canonical R-RBS-LM-122 unified characterization** (P0–P7) by `R-RBS-LM-147_smolstack_characterization.py`, which supplies a `corpus.source = "smol_stack"` loader and reuses R-122's phase functions **unchanged**. R-122's `build_corpus` previously knew only `"template"` and raised `NotImplementedError("requires Phase C smol-stack loader")` for non-template sources; this finding closes that gap. **44 attested MPR-style records.**

**The substrate-signature of the smol-stack is INDISTINGUISHABLE from the F162 template baseline on every substrate-intrinsic axis** (recall 1.000; substrate-similarity AUC 1.000; `hash` content-addressing the best-balanced router). The differences that *do* appear (sparser generation, 100% substrate-native grammar validity) trace to **corpus properties** (real prose vs rigid synthetic grammar), **not substrate behavior**. This is the **pre-stated outcome E2(b): a NULL for "the stack has its own distinguishing substrate signature"** — consistent with the F172/F199 flat-spectral ceiling. We did not lean toward the "distinct" outcome.

| Phase | Sweep | smol-stack result | template (F162) |
|---|---|---|---|
| P1 | length L ∈ {2..12} | recall **1.000** (10 pts) | recall 1.000 |
| P2 | corpus N ∈ {25..134} | recall **1.000**, 0 misclass | 1.000 (saturates only ~N=12800) |
| P3 | dimension D ∈ {2048..16384} | recall **1.000** all D | recall 1.000 all D |
| P4 | hierarchical 3×{4,8,16} | recall **1.000**; `hash` CV 0.10→0.38; `sector_then_hash` empties buckets | identical ordering; `hash` best-balanced |
| P5 | generation top_k {5,10,20} | **sparse**: 81–82 gens / 743 seeds; L9 dominant | hundreds of gens; L6 dominant |
| P6 | grammar (substrate_native) | **100%** valid (= skeleton membership) | 93.3% (pos_template — a stricter test) |
| P7 | plausibility 4 configs × 4 perturbations | substrate_only & baseline & balanced = **AUC 1.000** | identical (AUC 1.000) |
| S0/S1 | per-source signature compare | cross-register occupancy L1 **mean 0.166 / max 0.244**; pooled occupancy **≈ uniform** | n/a (template is single-source) |

---

## §2 The smol-stack-specific result — per-source substrate signatures (S0/S1)

For each of the 5 sources the runner computes a substrate signature: structural densities + the **Klein-4 sector occupancy** of the source's bigram bundle (routed by `srmech.amsc.format.sha256_bytes`-prefix mod 4 = the **hash null-control** routing from R-123), bundled via `srmech.amsc.hdc.klein4_bundle`, with a CPT-mirror self-similarity readout.

| source (register) | units | words | bigr | uniq | TTR | bigram-reuse | sector occ [s0,s1,s2,s3] | cpt-self |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| Procedural (recipe) | 25 | 113 | 218 | 185 | 0.465 | **0.151** | [.188, .280, .271, .261] | 0.000 |
| Almanac (astro) | 25 | 124 | 205 | 193 | 0.539 | 0.059 | [.239, .288, .185, .288] | 0.000 |
| Narrative (fable) | 24 | 134 | 222 | 213 | 0.545 | 0.041 | [.279, .252, .185, .284] | 0.000 |
| Aphorism (maxim) | 25 | 131 | 160 | 154 | **0.708** | 0.037 | [.206, .250, .269, .275] | 0.000 |
| Travel-log (journal) | 25 | 156 | 216 | 211 | 0.647 | 0.023 | [.310, .236, .218, .236] | 0.000 |

- **Cross-register spread is modest:** sector-occupancy L1 **mean 0.166, max 0.244**; density(TTR, reuse) L1 **mean 0.174, max 0.357**. The only sharp separations are *content-structural* and intuitive: the **procedural recipe has the highest bigram-reuse (0.151)** — repeated imperative frames ("the X", "the Y") — and the **aphorism set the highest type/token ratio (0.708)** — short, lexically-varied maxims. These are **corpus** facts the substrate faithfully *reflects*, not substrate signatures it *imposes*.
- **Pooled-stack occupancy is ≈ uniform** `[0.247, 0.262, 0.223, 0.268]` (uniform = 0.25). Under hash-control routing, uniform IS the expected null — so the **variant-level** occupancy carries no chirality structure, exactly as the null-control predicts. `cpt_self ≈ 0` likewise: the CPT-mirror of a hash-sector-routed bundle is orthogonal to it (no chirality axis imposed by hash routing).
- **Honesty caveat (E3 confound):** the five synthetic texts share *my authoring hand* (one register-imitating author), which **biases toward small cross-register spread**. A genuinely-sourced stack of independent authors could spread more. This is exactly why the run is marked a smoke and not a data claim.

---

## §3 Cross-variant comparison (the comparison the task asked for)

Three substrate-catalog variants now exist; their substrate-intrinsic signatures line up as:

| axis | template (F162) | smol-stack (this, R-147) | religious-texts (R-123) |
|---|---|---|---|
| corpus | synthetic grammar; 84-word vocab | **5 small synthetic texts; 513 vocab; 124 units** | 6 real public-domain texts |
| P1–P3 self-recall | 1.000 | **1.000** | (R-123 is a different, signature-only script — not the P0–P7 sweep) |
| P4 `hash` CV @4 / @16 | 0.036 / 0.107 | **0.102 / 0.382** | n/a |
| P4 best router | `hash` | **`hash`** (same; `sector_then_hash` empties buckets) | n/a |
| P6 grammar validity | 93.3% (pos_template) | **100%** (substrate_native) | n/a |
| P7 substrate-similarity AUC | 1.000 | **1.000** | n/a |
| sector occupancy | n/a | **≈ uniform** (hash-control routing) | **[.44,.44,.06,.06]** (bigram_parity routing) |

**Reading (honest, routing-aware):**
- On the **substrate-intrinsic** axes shared with the template (recall, hierarchical balance ordering, plausibility AUC), the smol-stack is **indistinguishable from the template** — the substrate algebra is **corpus-agnostic at this depth** (consistent with F162's length/dimension independence and the F172/F199 flat-spectral ceiling). **This is the headline NULL.**
- The P4 `hash` CV is *higher* for the smol-stack (0.10–0.38) than the template (0.04–0.11) — but this is a **small-N artifact** (100 sentences over up to 16 buckets ⇒ Poisson load-noise dominates), not a substrate signature; the **strategy ordering** (`hash` best, `sector_then_hash` worst with empty buckets) is **identical** to F162.
- The smol-stack's **≈uniform** occupancy and the religious-texts' **[.44,.44,.06,.06]** occupancy are **NOT directly comparable** — the smol-stack signature uses **hash null-control** routing (uniform-by-design) while R-123 used **bigram_parity** (structural) routing. The honest statement: under the *same* hash-control, the stack shows the expected flat null; testing whether bigram_parity routing lifts that on the stack is deferred (it would re-run R-123's structural routing on the smol-stack).
- The P6 difference (100% vs 93.3%) is **not a substrate win** — it is a **weaker test**: `substrate_native` validity = "does the generated sentence's skeleton exist in the store?", which generated sentences satisfy by construction. The template's `pos_template` mode is a genuinely stricter syntactic check. Real prose has no fixed POS template, so substrate_native is the only available mode — but it should not be read as the smol-stack generating "better grammar."

---

## §4 What the methodology smoke validated (the machinery)

| Check | Status |
|---|---|
| Variant descriptor loads via `srmech.amsc.load_descriptor` | ✅ `descriptor_smolstack.toml`, descriptor_hash `39b6a361...` |
| 6 mandatory AMSC sections; `[source].human_readable_name`; `[fetch].ndjson_path`; flat `literature_curated` rows | ✅ all present; round-trips through the typed accessor |
| Corpus attested by content SHA-256 (srmech-native) | ✅ 5/5 verified via `format.sha256_bytes` at run time; run aborts if any mismatch/missing |
| R-122 P0–P7 phases reused **unchanged** on a real-file corpus | ✅ runner patches only `build_corpus`/`build_vocab`; closes R-122's `NotImplementedError` smol-stack gap |
| Output is MPR-style attested NDJSON | ✅ 44 records, each carrying descriptor_hash + srmech_version + ABI + `smoke_status`/`data_claim` |
| C path | ✅ HAS_NATIVE=True, ABI=3, native klein4 throughout |
| Discipline check | ✅ **0 HARD, 0 coverage-gap** on R-147 (and on the R-122 it imports); REVIEW items are legitimate `Counter()` feeding occupancy/scorer, not storage proxies |
| Cascade-honesty (no `abs()`) | ✅ the occupancy L1 uses a **named Class-K pin-slot fold** (`d if d>=0 else -d`), not python `abs()` |

**One generation gotcha found + fixed in-catalog:** R-122's P5 generation BFS (`walk_bigram_chain`) **explodes combinatorially on real prose under `cycle_policy="allow"`** (dense bigram adjacency × walk-length-30 cycles) — the template never hit this because its grammar frames are rigid. The fix is catalog-driven and principled: set `cycle_policy="forbid"` (the canonical default) + `max_walk_length=12`, which runs at ~14 ms/seed (probed). The religious-texts variant set `"allow"` only because its *own* runner (R-123) never invokes the walk; a smol-stack that runs R-122's P5 needs `"forbid"`. (This is a real-corpus operational note for any future real-text variant of R-122.)

---

## §5 What this finding DOES claim

- The canonical R-122 unified characterization **runs end-to-end on a real-FILE multi-source corpus** for the first time (closes R-122's `smol_stack`/`file` `NotImplementedError` gap) — Phase C of the substrate parameterization is **operational**.
- On every **substrate-intrinsic** axis (self-recall, hierarchical-router ordering, plausibility-discrimination AUC), the smol-stack signature is **indistinguishable from the F162 template baseline** — the substrate algebra is corpus-agnostic at this depth (**the pre-stated E2(b) NULL**).
- Within the stack, **cross-register substrate-signature spread is modest** (occupancy L1 mean 0.166); the only sharp separations (recipe's high bigram-reuse, aphorism's high TTR) are **corpus-structural facts the substrate reflects**, not signatures it imposes.
- `hash` content-addressing remains the **best-balanced hierarchical router**; `sector_then_hash` empties buckets — **same ordering as F162**.
- Substrate-similarity carries plausibility discrimination at **AUC 1.000**, reproducing F162's P7 on a different corpus.
- The variant rides the **same substrate library + same srmech AMSC machinery** with **zero new substrate code** — only a corpus loader + a per-source signature pass.

## §6 What this finding does NOT claim

Per MFO §VII.6.20 + `[[feedback_no_mvp_framing]]` + the spike-query discipline:

- **Does NOT make any data claim about natural text.** The stack is synthetic (`smoke_status='methodology_smoke'`, `data_claim=false`); this is a methodology validation only.
- Does **NOT** claim the smol-stack is *distinguishable* from the template — it is the opposite (the NULL), and we did not lean toward "distinct."
- Does NOT claim the modest cross-register spread is a real register effect — the synthetic texts share one author (a confound biasing toward small spread); a genuinely-sourced independent-author stack is the proper test.
- Does NOT claim the smol-stack's flat (≈uniform) occupancy refutes chirality structure — it uses **hash null-control** routing (uniform by design); the bigram_parity (structural) routing test on the stack is **deferred**.
- Does NOT read the 100% substrate_native grammar validity as "better grammar" — it is a **weaker** check than the template's pos_template mode (skeleton-membership is satisfied by construction).
- Does NOT claim the substrate library is yet a registered siona profile (still research-subtree; UPSTREAM_NOTES §8).
- Does NOT lift the 3.3% Path-C cascade ceiling — this characterizes the *substrate*, not a cascade.
- Per `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`: one converging methodology smoke, not a standalone claim.

---

## §7 Cross-references

- F162 (full-coverage template-corpus characterization — Phase A/B baseline; the substrate-intrinsic axes this matches)
- R-123 / `descriptor_religious_texts.toml` (the real-text variant — descriptor-shape TEMPLATE; bigram_parity occupancy compared in §3)
- F172 / F199 (flat-spectral / strong-invariance storage ceiling — the NULL here is consistent with it)
- F163 (the `#184 smol-stack Phase C / F163` placeholder this finding fulfils; lodged as 204 to stay sequential)
- `R-RBS-LM-122_substrate_characterization.py` (the unified P0–P7 driver reused unchanged; its `NotImplementedError` smol-stack gap is now closed)
- `[[feedback_no_mvp_framing]]` + `[[feedback_full_coverage_shipping_mpm_way]]` + `[[feedback_pdf_extraction_citation_discipline]]` (synthetic-provenance honesty) + `[[feedback_dont_pre_commit_spike_query_operators]]` (pre-stated falsifier; null counts)

**Files written (NOT committed — user reviews and commits):**
- `catalogs/rbs_lm_substrate/descriptor_smolstack.toml` (the variant descriptor; descriptor_hash `39b6a361...`)
- `catalogs/rbs_lm_substrate/substrate_measurements/r147_smolstack.ndjson` (44 attested records)
- `rbs_lm_research/R-RBS-LM-147_smolstack_characterization.py` (the runner; 0 HARD discipline)
- `~/.cache/rbs_lm_corpora/smolstack/{proc_recipe,almanac_astro,fable_narrative,aphorism_maxims,travel_log}.txt` (5 CC0 synthetic stack texts; cached, not in repo — attested by SHA-256 in the descriptor)
- `R-RBS-LM-FINDING_204_*.md` (this finding)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8, 1M) as Phase C of the substrate parameterization. The smol-stack variant proves the F162 catalog-first characterization machinery consumes a real-FILE multi-source stack with zero new substrate code — and returns the honest NULL: on every substrate-intrinsic axis the small curated stack is indistinguishable from the synthetic-template baseline, with only corpus-structural facts (a recipe's repeated frames, an aphorism's lexical variety) showing through. The headline is a flat-spectral confirmation, not a distinction; the run is a methodology smoke on synthetic-but-SHA-256-attested texts, not a data claim. The one real operational lesson — `cycle_policy="allow"` makes the R-122 generation BFS explode on real prose — is now a catalog note for the next real-text variant. Per `[[feedback_dont_pre_commit_spike_query_operators]]`: the falsifier was pre-stated and the null was reported as the null.*
