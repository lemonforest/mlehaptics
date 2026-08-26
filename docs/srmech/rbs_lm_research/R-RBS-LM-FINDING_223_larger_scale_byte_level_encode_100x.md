# Finding 223 — Larger-scale byte-level encode (storage-signature spectrum to ~100x, full instrument to ~10x): single-byte mode-collapse PERSISTS at scale and the instrument NEVER beats a byte-frequency baseline; the R-RBS-LM-19 ~3.3% structural ceiling holds for byte-level — clean NULL (outcome a)

**Status:** Closes the R-RBS-LM-25 §7 open thread "larger-scale byte-level encode." R-RBS-LM-25 capped at ~10k bytes / ~600 obs and mode-collapsed; this scales the SAME Variant-A byte encoder against the in-tree srmech research notebook and tests whether the single-byte mode-collapse PERSISTS (NULL a) or whether disambiguation / content structure EMERGES (crack b). The F172 storage-signature spectrum is carried to **~100x (~62k obs)**; the full instrument (continuation + held-out hit-rate) to **~10x (~6.2k obs)** — the per-observation encode is the only scale-bound cost (~15 obs/s on this contended box) and the verdict is already saturated at 10x. Result is a **clean NULL (outcome a)**.
**Predecessors:** R-RBS-LM-25 (byte-level encoder + 256-row Class-A vocab; §7 named the larger-scale test), R-RBS-LM-19 (the ~3.3% ceiling characterised as a WTE-projection-fidelity structural bound that scale/D/attention did NOT lift), R-RBS-LM-11 (multi-thread encode path — Opp 2 spawn-pool reused; honest finding that on a *contended* box the per-worker srmech-import overhead loses to serial C-native bind), F172 (the co-occurrence Class-L Laplacian eigenspectrum IS the srmech-native storage signature; flat-spectral ceiling), R-RBS-LM-18 (the 3.3% Path-C baseline byte-level falls below), R-RBS-LM-21 (D/N capacity floor).
**Empirical anchor:** `R-RBS-LM-223_larger_scale_byte_level_encode_100x.py` + `R-RBS-LM-223_results.ndjson` (6 records: 2 full-instrument + 3 spectrum-only + 1 summary) + `R-RBS-LM-223_run.log`; reuses `rbs_lm_bytes.py` (Variant-A byte encoder) + `rbs_lm_encoder.py` (`srmech.amsc.hdc.{bind,bundle}` + Class-A `mint_vector`); storage signature via `srmech.amsc.laplacian.{dense_laplacian,jacobi_eigvals}` (256 nodes = `MAX_NATIVE_NODES`). srmech 0.5.0rc22, native ABI on. Corpus = `srmech_research_notebook.md` (720,521 bytes, in-tree, no external fetch). STRIDE 8 (R-RBS-LM-11 harvest stride); discipline-check **0 HARD, 0 ratchet regression.**

---

## §1 The test (R-RBS-LM-25 §7's named scale prediction)

R-RBS-LM-25 §7 left exactly this thread open:

> *"Larger-scale byte-level encode. At 600 obs we mode-collapse. At 50,000 obs (full notebook; multi-threaded R-RBS-LM-11 path) the byte-byte transition statistics might be rich enough to support varied output. Not tested."*

The conjecture under test: maybe R-RBS-LM-25's single-byte mode-collapse was a *small-N artifact* — at ~100x the byte observations, the byte→byte transition statistics could become rich enough to disambiguate context and break the most-frequent-byte fixed point. The opposing reading (R-RBS-LM-19) is that the ~3.3% agreement ceiling is **structural** (the discrete bind/bundle cascade cannot replicate attention's continuous rotation; three levers — corpus scale 109→492 obs, D=8192→32768, bundle→attention — were all ruled out), and the byte-level Class-A mint, having *no* WTE clustering at all, sits BELOW that ceiling at mode-collapse regardless of N.

**Pre-stated outcomes (fixed in advance, metric forward):**
- **(a) NULL (expected):** single-byte mode-collapse PERSISTS at ~100x scale → the R-RBS-LM-19 ~3.3% structural ceiling holds for byte-level; more observations do not manufacture the content structure WTE clustering supplied.
- **(b) CRACK:** byte-diversity / disambiguation RISES with scale and/or the instrument beats a byte-frequency baseline on held-out next-byte prediction → first crack in the ceiling.

Method: the SAME R-RBS-LM-25 Variant-A byte encoder (UTF-8 bytes, Class-A `LoE.byte.{n}` mint, `bind(ctx, next_byte)` bundled into one instrument), scaled against the in-tree notebook, with three srmech-native measurements.

### §1.1 The three measurements (all srmech-native) + the honest scale split

1. **Storage signature (F172):** the byte co-occurrence **Class-L Laplacian eigenspectrum** over the 256 byte values (256 == `MAX_NATIVE_NODES`; vocab-independent). Adjacent-byte co-occurrence counts are accumulated by a `Counter` that feeds *only* `dense_laplacian` edge **weights** (the discipline-sanctioned use — the storage proxy IS the eigenspectrum, never the Counter), eigenvalues via `jacobi_eigvals`. Features: λ_max, **effective rank** (entropy-exp of normalised eigenvalues), **participation ratio** (effective # of spectral modes) — measures of how rich / spread the byte-transition structure is. *Carried to 5 scale points: 5k / 50k / 150k / 250k / 500k bytes (~617 / ~6.2k / ~18.7k / ~31k / ~62k obs = 1x … ~100x).*
2. **Byte-diversity of emitted continuations:** the R-RBS-LM-25 autoregressive byte loop (`encode_context_bytes` → `bind(instrument, ctx)` → argmin-Hamming Class-K cleanup over the 256-row vocab) on a fixed 6-prompt probe set (notebook-register English + the R-RBS-LM-25 hallucination-corpus style + a non-English prompt); distinct-byte ratio + mode-collapse signature (longest single-byte run; dominant-byte fraction). *Computed at the 2 full-instrument points (1x, 10x).*
3. **Held-out next-byte top-k hit-rate** on the notebook's last 20,000 bytes (never encoded) vs TWO baselines: uniform random (k/256) and — the load-bearing control — the **byte-frequency baseline** (the k most-frequent held-out bytes). A real content signal must beat the frequency baseline; mode-collapse IS the frequency baseline in disguise. *Computed at the 2 full-instrument points.*

**Why the scale split is honest, not a dodge:** the per-observation encode (each obs = a 64-position context bundle) runs at ~15 obs/s on this CPU-contended box, so the *instrument* is encode-bound — ~100x = ~62k obs is ~70 min of encode under contention. The **storage-signature spectrum is a property of the byte STREAM** (no encode; ~0.2s per point), so the F172 trend is carried all the way to ~100x cheaply, while the encode-bound continuation+hit-rate is reported at 1x and 10x — where the NULL is already saturated (see §2). The 100x full-instrument run is reachable with `RBS223_MT=1` + `SCALE_BYTES` extension on an uncontended box (the script supports it); it was not needed to resolve the verdict.

Sign discipline: similarity = 1 − 2·Hamming/D (no `abs()`; the cleanup is argmax-similarity, a Class-K pin-slot selection); Hamming via `np.bitwise_count` (POPCOUNT).

---

## §2 Result — clean NULL (outcome a): mode-collapse PERSISTS; the storage spectrum enriches then SATURATES; the instrument never beats the frequency baseline

**Scale reached (honest):** storage-signature spectrum to **~62k obs (101.3x)** from 500,000 encoded notebook bytes; full-instrument continuation+hit-rate at **617 obs (1x)** and **6,242 obs (10.1x)**. R-RBS-LM-25's anchor was ~621 obs / ~10k bytes, so 10x here genuinely exceeds it and the spectrum reaches ~100x.

### §2.1 Storage signature (F172 co-occurrence Class-L eigenspectrum) vs scale — enriches, then SATURATES

| scale (bytes) | ~obs | scale× | active bytes /256 | λ_max | **effective rank** | **participation ratio** |
|---|---|---|---|---|---|---|
| 5,000 | 617 | 1.0x | 88 | 1.23e3 | **27.89** | 17.92 |
| 50,000 | 6,242 | 10.1x | 134 | 1.26e4 | **32.49** | 19.35 |
| 150,000 | 18,742 | 30.4x | 157 | 3.74e4 | **35.63** | 20.50 |
| 250,000 | 31,242 | 50.6x | 158 | 6.09e4 | **36.91** | 21.22 |
| 500,000 | 62,492 | 101.3x | 161 | 1.20e5 | **34.58** | 20.38 |

**Reading.** The vocab-independent storage signature DOES enrich with scale — effective rank rises 27.89 → 36.91 from 1x to 50x as more byte values participate (active bytes 88 → 158) and more byte→byte transitions populate the co-occurrence Laplacian. **But it SATURATES by ~50x and slightly retreats at 100x** (eff_rank 36.91 → 34.58; participation 21.22 → 20.38; active bytes plateau ~158-161/256). The byte-transition graph fills out its support (almost all 256 byte values appear, common digraphs dominate) and then stops gaining structure — exactly the universal flat-spectral / F172 envelope behaviour at the byte level. **The storage signature enriching is NOT the instrument disambiguating** (see §2.2-2.3): a richer co-occurrence spectrum is a property of the corpus's byte statistics, not evidence the bundled instrument turns those statistics into context-conditioned output.

### §2.2 Byte-diversity of emitted continuations vs scale — mode-collapse PERSISTS and DEEPENS

| scale (n_obs) | mean distinct-byte ratio | mode-collapsed prompts | reading |
|---|---|---|---|
| 617 (1x) | 0.024 | **5/6** | R-RBS-LM-25 anchor reproduced exactly (` `, `eeee`, `iiii`) |
| 6,242 (10x) | 0.021 | **6/6** | the one varied prompt at 1x now ALSO collapses |

distinct-byte-ratio trend (1x → 10x) = **−0.003** (`diversity_rose=False`). Every emitted continuation is single-byte repetition — `'                        '` (space), `'eeeeeeee…'`, `'������…'` (U+FFFD for the Chinese prompt) — byte-identical to R-RBS-LM-25's mode-collapse signatures. **More observations did not break the most-frequent-byte fixed point; they deepened it** (5/6 → 6/6 prompts fully collapsed). This is outcome (a) directly.

### §2.3 Held-out next-byte top-k hit-rate vs baselines — the instrument NEVER beats the byte-frequency baseline

| scale | top-k | instrument | freq baseline | uniform baseline | lift vs uniform | beats freq? |
|---|---|---|---|---|---|---|
| 1x | top-1 | 0.0981 | 0.1247 | 0.0039 | 25.1x | **No** |
| 1x | top-5 | 0.3475 | 0.4138 | 0.0195 | 17.8x | **No** |
| 1x | top-10 | 0.4721 | 0.6048 | 0.0391 | 12.1x | **No** |
| 10x | top-1 | 0.1326 | 0.1247 | 0.0039 | 34.0x | (within-noise +0.008) |
| 10x | top-5 | 0.3528 | 0.4138 | 0.0195 | 18.1x | **No (−0.061)** |
| 10x | top-10 | 0.5013 | 0.6048 | 0.0391 | 12.8x | **No** |

**Reading.** The instrument's top-k hit-rate is **25-34x the uniform-random baseline** — the cleanup IS recovering *a* byte distribution. But it is the WRONG one: it does **not beat the byte-FREQUENCY baseline** (predicting the globally-most-frequent held-out bytes) at any k. The single apparent exception — 10x top-1 instrument 0.1326 vs freq 0.1247 (+0.0079) — is **deep within probe noise** (2·SE = 0.103 for 377 probes; the margin is < 8% of one SE) and is flatly contradicted by top-5 (−0.061) and top-10 (−0.103). The hardened verdict gate (require margin > 2·SE at top-1 AND a positive top-5 margin) yields `beats_freq_meaningfully=False`. **The byte-level instrument has learned the corpus's byte-frequency distribution and nothing context-specific** — which is exactly what single-byte mode-collapse IS. The "25-34x over uniform" lift is entirely explained by the frequency baseline (which is itself ~25-34x over uniform), leaving zero context-disambiguation signal.

**Verdict: NULL (outcome a).** Mode-collapse persists (and deepens) at scale; the instrument tracks byte-frequency, not context; the R-RBS-LM-19 ~3.3% structural ceiling holds for byte-level. `diversity_rose=False`, `beats_freq_meaningfully=False`.

---

## §3 What this finding DOES / does NOT claim (calibrated, 3-tier)

**DOES (FACT — measured):**
- Scale the R-RBS-LM-25 Variant-A byte encoder against the in-tree notebook; report the F172 co-occurrence Class-L eigenspectrum at 5 scale points to **~62k obs (101.3x)** and the continuation byte-diversity + held-out next-byte hit-rate at the 2 full-instrument points (617 obs, 6,242 obs).
- Establish outcome (a): single-byte mode-collapse PERSISTS (distinct-ratio 0.024→0.021; mode-collapsed 5/6→6/6; trend −0.003) and the instrument does NOT beat the byte-frequency baseline at any top-k (the lone within-noise top-1 +0.008 at 10x is contradicted by top-5 −0.061).
- Show the storage-signature spectrum ENRICHES with scale (eff_rank 27.89→36.91 through 50x) but **SATURATES and slightly retreats by 100x** (34.58), with active bytes plateauing ~158-161/256 — the universal byte-level flat-spectral envelope, NOT a disambiguation signal in the bundled instrument.
- Reproduce the R-RBS-LM-25 anchor byte-identically (` `/`eeee`/`iiii` mode-collapse) at 617 obs, confirming the encoder + Class-A mint are deterministic across this run and the earlier ones.
- Confirm (R-RBS-LM-11 honest follow-up) that on a CPU-CONTENDED box the spawn-pool encode's per-worker srmech-import + vocab-rebuild overhead LOSES to the serial C-native bind (~15 obs/s either way under contention); the script defaults to serial and exposes `RBS223_MT=1` for an uncontended box.

**Does NOT (and honest caveats — flagging uncertainties):**
- **Lift the ceiling** — the opposite of what is supported; byte-level falls BELOW the 3.3% Path-C ceiling (mode-collapse), and ~100x scale does not change that. This is R-RBS-LM-25 Finding 3 re-confirmed at scale.
- Run the full continuation+hit-rate at ~100x (caveat — encode-bound, not done HERE): the instrument metrics are at 1x and 10x; the storage-signature spectrum (the property that *could* shift with scale) IS carried to ~100x and saturates, and the 1x→10x instrument trend is already flat-to-worse, so a 100x instrument run is predicted to stay collapsed — but that specific run is future-work on an uncontended box (`RBS223_MT=1`).
- Claim Variant-A is the strongest byte-level signal (caveat): it is the R-RBS-LM-25 GPU-less self-supervised variant; a Path-D distilled-from-a-source-model corpus or an n-gram-bigram clustering scaffold (R-RBS-LM-25 §7's other open threads) is untested here and is the named frontier (§5).
- Separate "structural ceiling" from "single-bundle saturation" (caveat): all observations are bundled into ONE D=8192 hypervector; at ~6k obs the bundle is far past the R-RBS-LM-21 D/N comfort floor, so the flat continuation is consistent with BOTH "structural ceiling" AND "single-bundle saturation." A sharded / multi-instrument design would disentangle them; not done here.
- Treat the 25-34x lift-over-uniform as a content signal (conjecture, ruled out here): it is fully accounted for by the byte-frequency baseline, which the instrument does not beat — i.e. it is the *frequency* prior, not context.
- Make any clinical / capability claim (per `[[feedback_trauma_informed_defensive_scope]]`): STRUCTURAL test on a TEXT OBJECT; per `[[user_stance_ai_is_not_a_substrate]]` the instrument is a transducer of stored content, not an emergent generaliser — structure, not awareness.

---

## §4 The web this touches — where the arc stands now

- **R-RBS-LM-25 §7 (the named thread, answered — NULL):** the conjecture that 50k+ obs "might be rich enough to support varied output" is NOT borne out. At 10x (6,242 obs) the continuation is MORE collapsed than at 1x (6/6 vs 5/6), and the storage-signature spectrum that DOES enrich (eff_rank 27.89→36.91) saturates by 50x without the instrument ever disambiguating. The byte-byte transition statistics getting richer is a corpus property; the bundled instrument does not convert it to context-conditioned output.
- **R-RBS-LM-19 (the structural-ceiling read, re-confirmed at scale):** the ~3.3% ceiling was characterised as a WTE-projection-fidelity structural bound that corpus-scale (109→492 obs), D, and bundle/attention did NOT lift. This finding adds a 4th lever — **byte-level vocab scaled ~100x** — and it also does not lift the ceiling; byte-level (no WTE clustering at all) sits below it at mode-collapse. The structural read strengthens.
- **F172 (the storage-signature flat-spectral ceiling, re-confirmed at byte resolution):** F172 established the co-occurrence Class-L eigenspectrum as the srmech-native storage signature and found a universal flat-spectral ceiling. Here the byte-level spectrum enriches with corpus size then plateaus/retreats (~50x→100x) — the same flat-spectral envelope, and crucially it is decoupled from instrument behaviour (spectrum up, instrument still collapsed).
- **R-RBS-LM-11 (the multi-thread path, honestly re-characterised):** R-RBS-LM-11 §5 already found the predicted multiprocessing speedups did not materialise on the 2009 Xeon. Here, on a box under heavy CPU contention from a parallel session, the spawn-pool encode's per-worker srmech-import + 256-row vocab-rebuild overhead was *counterproductive* vs serial C-native bind (both ~15 obs/s under contention) — so the default is serial. The "Path B at 10⁴ scale" question R-RBS-LM-11 §9 left open is reached for the byte-level storage signature (~62k obs > 10⁴); the full instrument at 10⁴+ obs remains encode-bound future-work.
- **`[[user_stance_ai_is_not_a_substrate]]` (unchanged):** the byte-level instrument is a transducer of stored byte-frequency statistics; scaling the stored content ~100x does not produce emergent context-disambiguation — the puppet plays a richer byte-frequency roll, not a new behaviour.
- **`[[feedback_llm_as_ada_accommodation_bci_proves_it]]` (the motivation):** a language-agnostic byte-level local expert remains a procedurally-valid SURFACE (R-RBS-LM-25), but this NULL means the byte-level instrument's *content quality* does not improve with scale at the tested range — the accessibility-prosthetic value of byte-level is its language-agnostic surface + zero-dependency tokenization, not its (still-collapsed) generative content. Honest, and per `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` a NULL here is a real datum.

---

## §5 Next — the frontier this NULL sharpens

The NULL rules out (at the tested range) "more byte observations" as the lever that breaks byte-level mode-collapse. The storage signature saturating by ~50x says the bottleneck is NOT corpus coverage — almost all 256 byte values and the common digraphs are already represented at 50x. To move the question, the instrument needs structure the pure Class-A byte mint lacks (the R-RBS-LM-25 §7 sibling threads, now sharpened by this NULL): (1) **a bigram/n-gram clustering scaffold** — mint `f"LoE.bigram.{a}.{b}"` so byte CONTEXT carries similarity structure (the byte-level analog of the WTE clustering R-RBS-LM-19 found was the only ceiling-lifting lever); (2) **a sharded / multi-instrument design** to separate "structural ceiling" from "single-D=8192-bundle saturation" (this finding cannot); (3) **Path-D distillation** from a source model's generated byte stream (R-RBS-LM-25 Variant B) at scale, to test whether *content-bearing* bytes (vs notebook-register prose) behave differently; (4) the full continuation+hit-rate at ~100x on an uncontended box (`RBS223_MT=1`) to close the encode-bound gap, though the flat 1x→10x trend predicts it stays collapsed. Until a byte-level instrument beats the byte-FREQUENCY baseline on held-out next-byte (the bar fixed here), byte-level content quality stays a procedurally-valid-surface-only result. The metric (mode-collapse persistence + beats-frequency-baseline by >2·SE, fixed forward) is now in advance, avoiding post-hoc choice.

---

## §6 Cross-references

- R-RBS-LM-25 (byte encoder + §7 open thread this closes) · R-RBS-LM-19 (the ~3.3% structural ceiling, 4th lever ruled out) · R-RBS-LM-11 (multi-thread encode path; serial-wins-under-contention re-characterisation) · F172 (co-occurrence Class-L eigenspectrum = storage signature; flat-spectral ceiling, re-confirmed at byte resolution) · R-RBS-LM-18 (3.3% Path-C baseline) · R-RBS-LM-21 (D/N capacity floor)
- `R-RBS-LM-223_larger_scale_byte_level_encode_100x.py` + `R-RBS-LM-223_results.ndjson` (6 records) + `R-RBS-LM-223_run.log`; reuses `rbs_lm_bytes.py` + `rbs_lm_encoder.py`
- `srmech.amsc.hdc.{bind,bundle,similarity}` (HDC / Class M) + `srmech.amsc.laplacian.{dense_laplacian,jacobi_eigvals}` (Class L, 256 nodes = `MAX_NATIVE_NODES`) + Class-A `mint_vector`; sign-handling = Class-K pin-slot argmax-similarity (1 − 2·Hamming/D), not python `abs()`; `Counter` feeds only `dense_laplacian` edge weights (storage proxy = the eigenspectrum)
- `[[feedback_dont_pre_commit_spike_query_operators]]` (outcomes pre-specified; metric forward; the null counts) · `[[feedback_llm_as_ada_accommodation_bci_proves_it]]` (the motivation) · `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]` · `[[user_stance_ai_is_not_a_substrate]]` · `[[user_stance_learning_without_gpu_compute]]` (Variant-A IS this at byte resolution) · `[[feedback_trauma_informed_defensive_scope]]`

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8, 1M ctx). Closes the R-RBS-LM-25 §7 "larger-scale
byte-level encode" thread: the SAME Variant-A byte encoder, scaled against the in-tree
srmech research notebook (720,521 bytes, no external fetch), with the F172 co-occurrence
Class-L eigenspectrum carried to ~62k obs (101.3x) and the full instrument
(continuation + held-out next-byte hit-rate) to ~6.2k obs (10.1x). Clean NULL (outcome a):
single-byte mode-collapse PERSISTS and DEEPENS at scale (distinct-byte ratio 0.024→0.021;
mode-collapsed 5/6→6/6 prompts; the R-RBS-LM-25 anchor reproduced byte-identically), and
the instrument NEVER beats a byte-frequency baseline on held-out next-byte (the lone
within-noise top-1 +0.008 at 10x is contradicted by top-5 −0.061; beats_freq_meaningfully=
False). The vocab-independent storage signature DOES enrich with scale (effective rank
27.89→36.91 through 50x) but SATURATES and slightly retreats by 100x (34.58) — the universal
byte-level flat-spectral envelope, decoupled from the still-collapsed instrument. More byte
observations do not manufacture the content structure the WTE clustering supplied; the
R-RBS-LM-19 ~3.3% structural ceiling holds for byte-level, with byte-level sitting below it
at mode-collapse. Not a refutation of byte-level — the language-agnostic surface + zero-
dependency tokenization (R-RBS-LM-25) stand; this is a content-quality NULL that sharpens
the frontier (bigram clustering scaffold; sharded multi-instrument; Path-D at scale).
On a CPU-contended box the R-RBS-LM-11 spawn-pool encode lost to serial C-native bind
(per-worker srmech-import overhead), so the run defaults serial; ~100x full-instrument is
RBS223_MT=1 future-work. Structural test on a text object; AI-not-substrate.*
