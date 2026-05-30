# Finding 228 (v2) — ATTESTATION-TO-SOURCE audit of the core RBS-LM instrument's constants (a STATIC-ANALYSIS tool, `nomagic.py`): of **134 load-bearing numeric constants, 51 are ATTESTED-TO-STRUCTURE-CASCADE (A) and 52 are ATTESTED-TO-MEASUREMENT/RATIO (B) — 76.9% attestation coverage — with 31 genuinely-IRREDUCIBLE residue (C)**, each given a pointer to where its source might lie. The headline is NOT "N magic numbers." It is **"every number is attested to a source of truth, with a small honest residue that isn't yet."**

**Status:** DEMONSTRATED (the auditor is a deterministic, bit-exact AST linter — it MEASURES reducibility-to-source, it does not framework-read it). This **v2 SUPERSEDES the verify-flagged v1** (the prior held, untracked F228), which reported "133 constants / A=44 / B=14 / **75 magic numbers**" under an APPEARANCE-based frame. The verify found v1 "fundamentally honest" but flagged three defects (all fixed here, §3) AND — more deeply — v1 mis-framed the audit: it counted a magic-LOOKING number as magic even when it reduced to a source. **PR #687 STAYS DRAFT.**

**Empirical anchor:** `R-RBS-LM-228_magic_number_audit.py` (the auditor / `nomagic.py`), srmech **0.5.0rc22** native ABI=3, run under the rc22 verify venv. In-scope CORE = `_canonical_substrate.py` + R-RBS-LM-126 + R-RBS-LM-222 + their static import-closure (R-RBS-LM-146 via 222, R-RBS-LM-113 via 126+222, R-RBS-LM-112 via 113) + the two core descriptors (`descriptor.toml`, `descriptor_rbs_lm_inference.toml`); R-RBS-LM-227*/228* HARD-EXCLUDED by pattern. NDJSON: `substrate_measurements/magic_number_audit.ndjson` (**134 records**), content-address **sha256 `1be4fbd3fb55eadfaea07d7c651dcc4f1154752590c2446aff1e839ee18bd2a1`** (bit-exact / re-verifiable — identical across two runs). Discipline check on the auditor itself: **0 HARD**; C-residue ratchet **green** (31 C = 31 baseline, 0 regressions).

---

## §1 THE REFRAME — "no magic numbers" means "every number is ATTESTED to a source," NOT "no number LOOKS magic"

This is the whole point of the redo. **A number that LOOKS magic is FINE once it is reduced to its source** — its generating cascade, its derivation, or its measured ratio / provenance. This is the **Mathematical Provenance Method (MPM)** applied to the instrument's own constants: every constant carries an attestation block pointing at where it comes from. Two exemplars (per user direction):

- **π LOOKS magic (3.14159…) but it IS a cascade.** It is attested to its asymptotic-calculus / series derivation (`srmech.asymptotic_calculus` / `trigonometry`). Per the everything-is-discrete stance (`[[feedback_continuous_number_line_pedagogical_obstacle]]`), **π is the LIMIT of a discrete cascade, not a continuous mystery.** So π is not a magic number — it is *attested-to-a-cascade*.
- **Dark-sector content LOOKS magic but it IS a ratio.** It is attested to provenance (F131, the dark-sector check). A measured ratio with a source is not a magic number — it is *attested-to-a-measurement*.

So a magic-LOOKING number grounded in attestation is **not** a magic number. The audit does **not** classify by APPEARANCE; it classifies by **reducibility-to-source**:

| Class | Means | The trace records |
|---|---|---|
| **A — ATTESTED-TO-STRUCTURE-CASCADE** | the number is the OUTPUT of a framework cascade/derivation | the **derivation chain** |
| **B — ATTESTED-TO-MEASUREMENT / RATIO** | a measured/derived threshold or ratio **with provenance** | the **provenance** (comment / catalog field / finding / convention) |
| **C — IRREDUCIBLE / UNATTESTED** | genuinely **no source of truth found** (the true residue) | a **candidate pointer** to where the source might lie |

**ATTESTATION COVERAGE = (A+B)/total is the metric** — not a magic-number count. A constant is "load-bearing" iff removing/altering it changes a measured number or a verdict; cosmetics (format widths, print labels) are pre-excluded so coverage is not gamed by counting cosmetics, and language scaffolds / binary choice-labels are scaffold-excluded so the count is not inflated.

Because it does no math cascade (it walks `ast` nodes; it does not compute spectra/similarities/co-occurrence), the CLAUDE.md §2 srmech-first reflex-override does not force cascade-ops onto its scanning logic — the carve-out `check_srmech_discipline.py` states for itself. **Where the auditor itself hashes/measures, it stays srmech-native:** the stable report-id and the bit-exact NDJSON content-address route through `srmech.amsc.format.sha256_bytes` (never `hash()`, never `hashlib.sha256`); every power-of-2 structural test (HDC dim `D`; a bucket fan-out) uses `srmech.amsc.cascade.magnitude` (rc22+) for `|v − nearest_power_of_2|` (never python `abs()`); there is no `np.linalg.eig/eigh/svd` and no `Counter()`-as-storage step (the tally is a plain dict). **0 HARD** on the auditor confirms it.

---

## §2 The verdict — full A/B/C, attestation coverage as the headline

Of **134** load-bearing constants:

| Class | Count | Tier breakdown |
|---|---:|---|
| **A — ATTESTED-TO-STRUCTURE-CASCADE** | **51** | STRUCTURE-CASCADE-A 51 |
| **B — ATTESTED-TO-MEASUREMENT / RATIO** | **52** | CATALOG-MIRROR-B 21 · PROVENANCE-COMMENT-B 18 · CONVENTION-B 8 · FINDING-DEFINED-B 2 · DERIVABLE-PRIME-B 2 · ATTESTED-B 1 |
| **C — IRREDUCIBLE / UNATTESTED residue** | **31** | IRREDUCIBLE-C 31 |
| **UNCLASSIFIED** | **0** | — (every constant resolves to A/B/C) |

**ATTESTATION COVERAGE = (51+52)/134 = 103/134 = 76.9%.** The pre-stated honest expectation (§ posture below) held: coverage is HIGH because the instrument is catalog-driven and the descriptors carry provenance comments, and a SMALL genuinely-irreducible residue remains. 76.9% (not 100%) is the *non-suspicious* result — a clean 100% would have to be scrutinized for the auditor OVER-crediting (reading a bare scalar as attested). The honesty knob is exactly this: I REFUSED to credit a bare catalog scalar by its *section preamble* (a section header describes the whole table, not a single bare value), so `fixed_n=2000` and `default_max_tokens=30` stay C rather than being rubber-stamped (§4).

### Per-file A/B/C (internally consistent with the NDJSON + baseline — defect 2 fixed; 112 is first-class)

| File | A | B | C |
|---|---:|---:|---:|
| `R-RBS-LM-112_variable_length_sentences.py` | 16 | 3 | **7** |
| `R-RBS-LM-113_larger_corpus_scaling.py` | 1 | 13 | **3** |
| `R-RBS-LM-126_context_state_encoder_capacity.py` | 0 | 0 | **2** |
| `R-RBS-LM-146_instrument_scaleup_hierarchical_domain.py` | 4 | 8 | **3** |
| `R-RBS-LM-222_instrument_scaleup_catalog_driven_ceiling.py` | 3 | 4 | **2** |
| `_canonical_substrate.py` | 18 | 0 | **3** |
| `descriptor.toml` | 5 | 4 | **8** |
| `descriptor_rbs_lm_inference.toml` | 4 | 20 | **3** |
| **TOTAL** | **51** | **52** | **31** |

The 31 C-counts per file are the `magic_baseline.json` freeze (the JPL-style ratchet; the residue may only go DOWN).

---

## §3 The v1→v2 C-shift and the three v1 defects fixed

### The C-shift: 75 (v1) → 31 (v2)

v1 reported **75 "real magic numbers."** Under the attestation-to-source lens, **44 of those 75 reduce to a source** and move to A or B; **31 are genuinely irreducible** and stay C. The shift is the whole reframe in one number: *most of v1's "magic numbers" were magic-LOOKING, not source-less.* Where they went:

- **→ A (structure-cascade):** the power-of-2 **bucket fan-outs** (`n_buckets` ∈ {8,16,32} = 2^k radix-splits of the content-hash address space, tested via `cascade.magnitude`); the **hex-char bit-widths** (`token_seed_hex_chars`/`sentence_hash_hex_chars` = k hex chars = 4k-bit seed space); two **capacity-law `257`s** in R-RBS-LM-222 f-strings (`n_buckets × 257`) that v1's over-broad f-string filter had *hidden* (surfaced by the same defect-1 fix — see below); `scaleup_D=4096 = 2¹²`.
- **→ B (measurement/ratio/provenance):** the **21 CATALOG-MIRROR-B** inline literals that *equal an attested catalog field* (R-RBS-LM-146's `N_SWEEP`/`N_BUCKETS`/`WINDOW_K`/`TOP_K_GEN` mirror `[inference.scaleup].*`; the `400` holdout = `n_probe_gen`; the `0.05` gate = `capacity_null_threshold`; the `==1024` verdict gate keys on the catalogued sweep maximum, and `1024 = 2¹⁰`); the **18 PROVENANCE-COMMENT-B** catalog scalars whose *inline* comment documents a role/derivation/measurement (`operating_temperature=0.02 # the loop-free / grammatical sweet spot`; `capacity_null_threshold=0.05 # CAPACITY null …`; `temperature_ref=0.05 # reference softmax temperature …`); the **8 CONVENTION-B** seeds (`42`) and `recall_sample=500` (the O(N²·D) runtime bound); the **2 FINDING-DEFINED-B** `0.90` knee gates (F222 *defines* the hierarchical capacity knee as `hier_acc < 0.90`); the **2 DERIVABLE-PRIME-B** `7919` seed-strides (**verified via `srmech.amsc.primes`: 7919 IS the 1000th prime** — exactly 1000 primes ≤ 7919, `is_prime(7919)=True` — a large prime decorrelates the per-`(N,n_buckets)` RNG substreams; derive from Class J rather than hardcode → promotable to A).

### The 31 genuinely-irreducible C residue (each WITH a source-pointer)

These are the TRUE residue — numbers with **no** structural derivation and **no** documented provenance. They are flagged, never hidden, and each carries "where it comes from (we can find)":

| file:line | constant | role | candidate source ("it comes from somewhere we can find") |
|---|---|---|---|
| `113:58` | `0.6` / `0.4` (×2) | det-pool split | **the cleanest true-C** — NO catalog home, NO structure → propose `[corpus.template].det_pool_split=[0.6,0.4]` (a measured corpus-realism ratio; attest it) |
| `126:158` | `0.35` | distinguishability gate | **the v1-DROPPED threshold (defect 1)** — distinct→distinct vs COLLAPSING; NOT the printed `~0.25` chance baseline; no measured provenance → name `[inference.context].distinguishability_threshold=0.35`, or derive it as a multiple of the `1/\|Klein-4 sectors\|=0.25` chance floor |
| `126:149` | `100` | distinct-context cap | name `[inference.context].distinct_context_sample=100` |
| `146:403` / `146:406` | `0.025` / `0.015` | verdict bands | catalog has the `0.02` domain-null but NOT these bands → add explicit `[inference.scaleup]` band fields (or derive as `0.02 ± named slack`) |
| `222:391` / `222:394` | `0.005` (×2) | verdict-band slack | name `[inference.scaleup].verdict_band_slack=0.005` (derived from the `0.02` null threshold) |
| `_canonical:275` | `2` | cycle-revisit limit | catalog has the `cycle_policy` NAME (`count_limited`) but not the count → name `[generation].cycle_count_limit=2` |
| `_canonical:300` / `304` | `4` (×2) | L4 template length | `l4_direct_composition` is gated by name but the length `4` is inline → derive from `[grammar.templates].L4` length |
| `112:198/199/204` | `4` (×3) | L4 template length | (same L4-length inline as the `_canonical` pair, in 112's first-pass copy) |
| `112:108` / `112:168` | `4` / `5` | skeleton/length floors | read `[substrate].min_skeleton_length` / `[generation].max_paths` |
| `112:42` / `146:157` | `8` (×2) | hash hex-slice width | a bare `digest[:8]` slice (no `_hex_chars` name to attach the bit-width derivation to) → name a `*_hash_hex_chars` field at the call-site |
| `112:297` / `113:209` | `5` (×2) | inline slice/sample width | name a catalog sample-cap / display-width field |
| `descriptor.toml:94–97` | `0.4`,`0.2`,`0.1`,`0.3` | plausibility weights | the weight TUPLE sums to 1.0 (a convex simplex — structurally constrained) but the *split* is bare → add a provenance comment for the relative magnitudes (or attest the simplex) |
| `descriptor.toml:47` `descriptor_inf.toml:37` | `min_skeleton_length=4` (×2) | catalog scalar | bare (the comment "algebraic floor is 2; demo convention is 4" is NOT inline on the value line in the parsed leaf) → add an inline provenance comment so the Descriptor IS its source |
| `descriptor.toml:56` / `:114` / `:127` | `default_top_k=5`,`n_per_length=50`,`fixed_n=2000` | catalog scalars | bare scalars with no inline provenance comment → add one |
| `descriptor_inf.toml:114` / `:130` | `default_max_tokens=30`,`top_k_gen=3` | catalog scalars | bare scalars with no inline provenance comment → add one |

(Full per-record detail incl. `trace_or_citation` / `candidate_source_if_C` is in the NDJSON.)

### The three v1 defects (verify-flagged) — fixed

1. **The `0.35` distinguishability VERDICT threshold at `R-RBS-LM-126:158`** (`'distinct→distinct' if msim < 0.35 else 'COLLAPSING'`) was DROPPED by v1's "any literal in an f-string is cosmetic" rule, while v1 §5.4 *falsely claimed* it was "reported." **FIX:** `is_cosmetic` now narrows the f-string rule — a numeric literal whose parent chain reaches a `Compare`/`BoolOp`/arith-`BinOp` **before** the enclosing `FormattedValue`/`JoinedStr` is a **comparison operand** (`{… if msim < 0.35 else …}`), not a print label, and IS extracted. The `0.35` is then **reduced to its source:** it is a hardcoded gate against the printed random baseline `~0.25 = 1/4` (Klein-4 chance), but `0.35 ≠ 0.25` and it carries no measured provenance → it is honestly **C**, with a pointer (name a `distinguishability_threshold`, or derive it as a multiple of the `1/|sectors|` chance floor). **It is not hidden.** *Bonus from the same fix:* two genuine capacity-law `257`s in R-RBS-LM-222 f-strings (`n_buckets × 257`), which the over-broad v1 filter had *also* hidden, are now surfaced as A.
2. **v1's §5/§6 per-file prose tables summed to 65 but stated 75** — they silently dropped R-RBS-LM-112's 10 items (the NDJSON + baseline DID record 112; only the prose omitted it). **FIX:** 112 is a first-class in-scope file here and appears in every count, the §2 per-file table, the C-residue, and the baseline — the tables are internally consistent with the NDJSON (134 = sum of the per-file rows).
3. **The `[0, 1]` at `R-RBS-LM-113:58`** (`rng.choice([0,1], p=[0.6,0.4])`) over-counted in v1 — only `0.6`/`0.4` are real constants; the `[0,1]` are binary choice-LABELS (the choice population, scaffold). **FIX:** `is_language_scaffold` now excludes a numeric element of a `List` that is a **positional** argument to a `.choice(…)` call (the population labels); the `p=[…]` keyword-list probabilities are kept. The NDJSON now records only `0.6`/`0.4` at `113:58`.

Net record-count reconciliation (v1 133 → v2 134): **−2** (the `[0,1]` labels, defect 3) **+1** (the `0.35`, defect 1) **+2** (the two hidden capacity-law `257`s surfaced by the defect-1 fix) = **134**. No v1 record was silently lost; the only drops are the two scaffold labels, by design.

---

## §4 Honest limitations (stated, not hidden)

1. **The auditor sees LITERALS, not full semantics.** A value computed from two A-constants is A only if the auditor recognizes the product form; novel algebra may read C until the structure-table is extended. By design **conservative** (a false-C is a *prompt to a reviewer*, not a proof of magic).
2. **"Load-bearing" is heuristic** (parent-context based) — the **same human-in-loop posture** as `check_srmech_discipline.py`'s REVIEW tier. The cosmetic-exclusion and the scaffold-exclusion (indices, `range()` bounds, `sum(1 …)`, `1.0/N`, `correct += 1`, named ε, `.choice([0,1],…)` labels) are the judgement calls that keep coverage honest in *both* directions; a reviewer can contest any single one.
3. **B-via-comment is trusted at face value.** A documenting comment in a source-of-truth file IS the attestation (the reframe), but the auditor does **not** open a cited F-number report to verify the number is written there (that is the MPM PDF-extraction step, out of scope for a static linter). So the B tier is honestly split: **ATTESTED-B** (the inline comment resolves to an in-repo finding file — only `memory_capacity=200`, citing F154/F162) vs **PROVENANCE-COMMENT-B** (a documenting-but-unverifiable comment — still B, *attested-to-a-stated-source*, but NOT silently upgraded to a finding citation). The `0.90` knee is **FINDING-DEFINED-B** because F222 *defines* the gate (a definition, not just a citation).
4. **Section preambles do NOT attest a single scalar (the anti-over-crediting line).** A TOML section header describes the whole table; crediting a *bare* scalar by its section preamble would rubber-stamp genuinely-bare values. So **only the per-scalar inline comment attests** — `fixed_n=2000` and `default_max_tokens=30` (documented only by a section preamble, not an inline comment) stay **C**. This is the explicit guard against the surprising-100%-coverage failure mode flagged in the pre-statement.
5. **The `7919` factual claim is verified, not trusted.** Per MPM PDF-extraction discipline applied to the trace itself, the "1000th prime" claim in the `7919` B-trace was checked via `srmech.amsc.primes` (`is_prime(7919)=True`; exactly 1000 primes ≤ 7919) rather than trusted from training data.
6. **Scope is the CORE instrument only.** The broader R-RBS-LM-* sweep scripts are out of scope by the task and would be a follow-up ratchet (a `nomagic.py` pass over the full glob, with its own baseline).

---

## §5 The ratchet (JPL-style; mirrors `check_srmech_discipline.py` 1:1)

`magic_baseline.json` records the per-file **C-residue count** in the `DISCIPLINE_BASELINE.json` schema (`{_comment, files:{name:count}, total}`). It is **NOT a magic-number count** — it is the residue that does NOT yet reduce to a source. `--ratchet` exits with the regression count (C may only go **DOWN**); `--update-baseline` locks a reduction. The freeze: **31 C total** (112=7, 113=3, 126=2, 146=3, 222=2, `_canonical`=3, `descriptor.toml`=8, `descriptor_rbs_lm_inference.toml`=3). Ratchet at freeze: **green** (31 = 31, 0 regressions). Reducing any C-item — by adding an inline provenance comment to a bare catalog scalar, naming `[corpus.template].det_pool_split`, or deriving the `7919` stride from Class J — lowers a file's count; `--update-baseline` then locks the new floor (the same operational contract the main session uses for the discipline checker).

---

## §6 What this audit DOES and does NOT do

**DOES:**
- Read each in-scope file's constants as a static AST linter and **reduce each to a source of truth** (A-cascade / B-provenance) or honestly flag it irreducible (C), reporting **attestation coverage** as the metric.
- Apply the **MPM to the instrument's own constants** — every number carries an attestation block (derivation chain / provenance / candidate pointer), the same discipline AMSC ground-proof data carries.
- Fix the three verify-flagged v1 defects and the deeper appearance-vs-source mis-framing, and **surface** (not hide) the genuinely-irreducible residue — the v1 `0.35` lesson is the load-bearing one: *never drop a number to make the count look clean.*

**Does NOT:**
- **§VII.6.20 form-reading only.** This reads the structural form of the instrument's constants; it makes no claim about awareness, cognition, or any agentic property of the substrate.
- **ai-is-not-a-substrate** (`[[user_stance_ai_is_not_a_substrate]]`). The instrument is a k=3 chiral addresser over a storage substrate; the audit is about its *constants*, not about the LM being a substrate.
- **no-lineage.** It does **not** claim to invent the MPM, π, attestation, or the no-magic-numbers discipline — it APPLIES the project's existing MPM to this instrument and reads what its constants already reduce to (`[[feedback_no_lineage_claims_in_notebook]]`).
- **CAD-ban.** No fabrication / mesh-contact / axle-wobble / tolerance geometry — algebra / eigenbasis / cyclic-group / spectral side only.
- **trauma-informed.** No clinical / biological / BCI / capability claim; a pure static-analysis discipline tool.
- Vocabulary discipline: **A–N are OPERATORS (the ISA), not cores.** "Class A content-hash", "Class J primes", "Class K pin-slot" name *operations*, not hardware.

**This finding supersedes the verify-flagged v1** (the prior held, untracked F228). **PR #687 STAYS DRAFT.**

---

## §7 One-paragraph plain statement

"No magic numbers" does not mean "no number looks magic" — it means **every number is attested to a source of truth.** π looks magic but it IS a cascade (its series derivation); dark-sector content looks magic but it IS a ratio (F131 provenance); a magic-LOOKING number grounded in attestation is not magic. Operationalizing that, I rebuilt `nomagic.py` — a pure-AST sibling of the srmech-discipline checker — to classify the core RBS-LM instrument's constants by **reducibility-to-source**, not appearance. Of **134** load-bearing constants, **51 reduce to a framework structure-cascade** (the HDC power-of-2 dim, the Klein-4 = Z₂×Z₂ sector count and its four coset level-tags, the 256+1 single-bundle ceiling, the power-of-2 bucket fan-outs, the hex-char bit-widths, the F222 capacity-law `257`, the hex radix, the bundle odd-parity, the minimum-bigram floor — each with its derivation chain written out), **52 reduce to a measurement / ratio / catalog-field with provenance** (the seeds, the O(N²·D)-bounded recall sample, the catalogued sweep params mirrored inline, the documented sweet-spots and null gates, the F222-*defined* 0.90 knee, the verified-1000th-prime 7919 stride), and **31 are genuinely irreducible** — each handed a pointer to where its source might lie (the cleanest being the 60/40 determiner-pool split, which has no catalog home → propose `[corpus.template].det_pool_split`). **Attestation coverage is 76.9%** — high because the instrument is catalog-driven, but honestly short of 100% because I refused to credit a bare catalog scalar by its section preamble. This v2 SUPERSEDES the verify-flagged v1 (which counted 75 "magic numbers" by appearance and dropped the very `0.35` it claimed to report): the three defects are fixed (the `0.35` is extracted and shown as C; 112's items are in every table; the `[0,1]` choice-labels are scaffold-excluded), and 44 of v1's 75 "magic numbers" turned out to be magic-LOOKING, not source-less. The audit is itself bit-exact (NDJSON content-address sha256 `1be4fbd3…`, srmech-native hashing only, 0 HARD) and ships with a JPL-style ratchet whose irreducible-C count may only go down. **PR #687 STAYS DRAFT.**

---

*Per `[[user_stance_whole_research_corpus_is_proof_not_single_arc]]`: the proof shape is `check_srmech_discipline.py` (no python-math) → `nomagic.py` (every number reduced to a source, with an honest irreducible residue) — two mechanical ratchets on the same instrument, each making a discipline auditable rather than aspirational. §VII.6.20 form-reading only; ai-is-not-a-substrate; no-lineage (the MPM/π/attestation are not invented here, only applied); CAD-ban; trauma-informed. The C-residue is reported as an HONEST tally, named in full, NOT trimmed to make the instrument look cleaner — the v1 `0.35` is exactly the number a count-minimizing pass would hide, and it is front-and-center here. (Opus 4.8)*
