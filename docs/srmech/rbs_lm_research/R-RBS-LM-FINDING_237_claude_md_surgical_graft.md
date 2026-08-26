# Finding 237 — Lean-memory by EXTRACTIVE surgical graft: can CLAUDE.md be compressed ~2× while a LEAN-primed agent answers the load-bearing probes as well as a full-primed one?

**Headline:** **FUNCTIONAL POSITIVE / structural-spectral-proxy NULL — split, and honest.** An EXTRACTIVE surgical graft compresses the framework-research `CLAUDE.md` to `CLAUDE_LEAN.md` at **0.526 LEAN/full bytes** with **guardrail-anchor coverage 1.0** and **zero abstractive leakage** (every LEAN line is a verbatim source line). The A/B — the decider for "lean-memory-WORKS" per the pre-stated tiering — is a **clean positive**: a harness subagent primed on LEAN scores **10/10** on the fixed load-bearing probe set, exactly matching the full-file agent (**10/10**) — **fidelity delta 0.0**, and **isolation-verified** (two full-present/LEAN-absent control probes both returned "NOT IN DOCUMENT" from the LEAN agent, proving it answered from LEAN alone, not auto-loaded context). BUT the band-graph **spectral-density-cosine is 0.78 at the 0.50 ratio — below the pre-stated 0.90 gate** — so the strict 3-way-AND POSITIVE is not met. Honest reading: **lean-memory-by-extractive-graft FUNCTIONALLY WORKS at ~2× compression; the spectral-structure proxy under-predicts it** (it gates band-graph topology, which compression necessarily perturbs, while the load-bearing *content* and its *readability* fully survived).

**Status:** **DEMONSTRATED** (bit-exact instrument) for compression / coverage / extractive-integrity / the size-invariant spectral-density-cosine; **DEMONSTRATED (isolation-verified A/B)** for the probe-fidelity. **FRAMEWORK-READING** only for any "lean memory generalizes beyond this file / beyond the guardrail probes" claim. srmech-native, 0 HARD, bit-exact. **PR #687 STAYS DRAFT.** The real `CLAUDE.md` was NOT modified; `CLAUDE_LEAN.md` is a deliverable artifact.

**Predecessors / lens:** **F223** (the ~3.3% *abstractive* mode-collapse ceiling — extractive graft avoids it by construction: kept bands are bytes COPIED, never regenerated), **F172** (the co-occurrence Laplacian eigenspectrum IS the srmech-native storage signature — used here as the band-graph structure), **F168** (sector tagging), **F166/R-126** (the substrate). Method: cross-substrate cascade-matching applied to the memory file itself. User direction 2026-05-31: "convert CLAUDE.md into an RBS-NN object, surgically graft, emit CLAUDE_LEAN.md, compare spectrally, A/B a subagent on either."

---

## §1 The three design-grounding bugs (fixed)

The design-grounding run was clean (0 HARD, bit-exact) but surfaced three honest defects; all fixed, re-run clean.

| # | bug | fix | before → after |
|---|-----|-----|----------------|
| **1** | guardrail HARD-KEEP floor ~0.73 of file (every band carrying ANY anchor force-kept) → all ratios collapsed to ~0.73 (only ~27% compression) | **tightened `GUARDRAIL_ANCHORS` to the genuinely-RARE load-bearing rule-pins** (dropped high-frequency `srmech`/`attested`/`klein4`/`Class K`/`Class C`/`dense_laplacian`/… which hit most bands); the dropped tokens stay in `SCORE_ANCHORS` (still score), only HARD-KEEP/coverage tightened; each rule keeps ≥1 rare pin so coverage 1.0 still proves no rule silently dropped | actual_C **0.73 → 0.526** at the 0.50 target |
| **2** | `spectral_similarity` used `spectral.similarity` (which is **byte-Hamming `1−2·hamming/D`**, confirmed empirically: scaled→0.86, orthogonal→0.79) on **zero-padded raw eigenspectra of different-sized graphs (169 vs 84 nodes)** → 0.187 was a length/magnitude artifact | **size-invariant normalized spectral-DENSITY histogram cosine**: each eigenvalue ÷ its own spectrum max → [0,1], fixed 32 bins, cosine of the two density histograms (numpy dot/√, `cascade.magnitude` not abs, `jacobi_eigvals` not `np.linalg.eig`) | 0.187 (artifact) → **0.78** (honest, at 0.50) |
| **3** | coverage 0.97 — anchor `"trauma-informed"` missed because §4 uses the underscore key `trauma_informed` | **variant-insensitive matching** (`_normvar`: treat `-` and `_` as equal) in HARD-KEEP + coverage | coverage **0.97 → 1.0** |

**Re-run (srmech 0.6.0rc8, HAS_NATIVE, ABI 3), `--emit`, bit-exact across two identical invocations:**

| target ratio | actual_C | coverage | spectral-density-cosine | extractive_ok |
|---|---|---|---|---|
| 0.40 | 0.459 | 1.00 | 0.760 | True |
| **0.50 (primary)** | **0.526** | **1.00** | **0.780** | True |
| 0.60 | 0.617 | 1.00 | 0.858 | True |

`response_sha256 = e1f78dc2c687ae9362728ae4d88959c41197eb99e6e64a9d3ee1b94d6ce0c99f` (body minus generated_at; identical on re-run). `CLAUDE_LEAN.md` sha256 `93c6ab9e…` (12136 bytes, 86 lines). **0 HARD** on `check_srmech_discipline.py`. Extractive-integrity assert passes (every LEAN line verbatim in source).

---

## §2 The A/B — the decider for "lean-memory-WORKS" (DEMONSTRATED, isolation-verified)

Two HARNESS subagents (Agent tool — dollar-free, NOT the Anthropic API balance), each isolated to a single neutral-named `/tmp` document (full vs LEAN) with strict "answer ONLY from this document; NOT IN DOCUMENT if absent; ignore all background memory" instructions, given the **fixed probe set but NOT the ground-truth answers** (probe-leak guard). Scored by the orchestrator against the real `CLAUDE.md`.

**Isolation controls (the contamination guard):** because all 10 load-bearing probes survived into LEAN (coverage 1.0), they cannot by themselves detect auto-load contamination — so two **full-present / LEAN-absent control probes** were added (Class G's role; the EMDR_CLAUDE.md reference). Result: the **LEAN agent answered "NOT IN DOCUMENT" for BOTH** (the full agent answered both correctly). This **proves the LEAN agent used only LEAN** — no auto-loaded `CLAUDE.md` leakage — so its load-bearing scores are valid.

**Fidelity (10 load-bearing probes):**

| probe (load-bearing rule) | in LEAN? | full agent | LEAN agent |
|---|---|---|---|
| 1 Counter() → `dense_laplacian` | ✓ | correct | correct |
| 2 no-magic = unattested (not "looks magic") | ✓ | correct | correct |
| 3 CAD-grade scope ban | ✓ | correct | correct |
| 4 never `abs()` in a cascade | ✓ | correct | correct |
| 5 A-N partition 1 + 3 + 7 + 3 | ✓ | correct | correct |
| 6 never squash-merge | ✓ | correct | correct |
| 7 defensive-scope | ✓ | correct | correct |
| 8 attestation / MPR | ✓ | correct | correct |
| 9 rc-before-PyPI | ✓ | correct | correct |
| 10 Class K / Class C sign-handling | ✓ | correct | correct |
| **load-bearing score** | | **10/10** | **10/10** |
| *control 11 Class G role* | ✗ (dropped) | correct | **NOT IN DOCUMENT** ✓ |
| *control 12 EMDR_CLAUDE.md* | ✗ (dropped) | correct | **NOT IN DOCUMENT** ✓ |

**Fidelity delta (full − lean) = 0.0; lean = 1.0 × full ≥ 0.85.** A LEAN-primed agent answers every load-bearing probe exactly as well as the full-primed one, demonstrably from the 0.526-compressed file alone.

---

## §3 Pre-stated criteria → honest verdict (no leaning)

Pre-stated POSITIVE = coverage 1.0 **AND** spectral_sim ≥ 0.90 **AND** lean fidelity ≥ 0.85·full. Pre-stated NULL = fidelity-gap > 0.15 **OR** coverage < 1.0 / spectral_sim < 0.90 **OR** any abstractive LEAN line.

- coverage **1.0** ✓ · extractive **clean** (no abstractive line) ✓ · fidelity **1.0 ≥ 0.85** ✓ · spectral_sim **0.78 < 0.90** ✗.
- **By the strict 3-way conjunction the POSITIVE is NOT met** — the spectral_sim gate fails (NULL clause b). Reported as-is; the goalpost is not moved.
- **But the FUNCTIONAL decider (the A/B probe scores, which the pre-stated tiering names as what decides "lean-memory-WORKS") is a clean POSITIVE** (fidelity 1.0, isolation-verified).

**Interpretation (FRAMEWORK-READING):** the spectral≥0.90 gate is a *structural* proxy on the band-graph eigenspectrum topology, which dropping ~half the bands necessarily perturbs (0.78); it **under-predicts** the functional outcome. The load-bearing *content* (coverage 1.0) and its *readability by a primed agent* (A/B 1.0) fully survived a ~2× extractive compression. So **lean-memory-by-extractive-surgical-graft functionally works at ~0.5 compression for this file**; the right success proxy is probe-fidelity, not band-graph spectral similarity.

---

## §4 Scope, honesty, caveats (MFO §VII.6.20)

- **DEMONSTRATED:** compression 0.526, coverage 1.0, extractive-integrity, the size-invariant density-cosine 0.78, and the isolation-verified A/B fidelity 1.0 — all bit-exact / reproducible instrument results.
- **The A/B tests the GUARDRAIL-preserved content only.** All 10 probes are the load-bearing rules the graft is built to keep; the test confirms those are functionally readable from LEAN. It does **not** test non-guardrail recall (the dropped ~47% — e.g., Class G/E/M definitions, §5 file locations, the EMDR pointer), which is expected to degrade and which the controls confirm IS dropped. "Lean memory" here means **the load-bearing discipline survives at ~2× compression**, not that the file is losslessly halved.
- **Isolation limitation, mitigated:** harness subagents can auto-load the worktree `CLAUDE.md`; the neutral-named `/tmp` documents + strict single-document instruction + the two full-present/LEAN-absent control probes (both → NOT IN DOCUMENT from the LEAN agent) are the mitigation, and they held — but this is harness-side isolation, not a hermetically sealed model. The **current-gen-LLM (SDK/API) twin (#789) remains the dollar-gated, hermetic version** and is gated behind this finding.
- **Extractive, never abstractive (F223):** every kept band is a verbatim source span; the post-emit assert makes any regenerated line a HARD build failure.
- srmech-native (Class M klein4 encode; Class L `dense_laplacian`/`jacobi_eigvals` storage signature; `cascade.magnitude` not abs; `sha256_bytes` not hashlib); 0 HARD. Real `CLAUDE.md` untouched. ai-is-not-a-substrate; no-lineage; trauma-informed.

**Files:** `R-RBS-LM-237_claude_md_surgical_graft.py` · `substrate_measurements/claude_md_surgical_graft.ndjson` (response_sha256 `e1f78dc2…`) · `CLAUDE_LEAN.md` (the deliverable; sha `93c6ab9e…`). **PR #687 STAYS DRAFT.**
