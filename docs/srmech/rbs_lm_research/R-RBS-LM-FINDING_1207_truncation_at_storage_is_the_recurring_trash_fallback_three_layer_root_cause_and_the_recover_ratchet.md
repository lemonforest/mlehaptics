# F1207 — Truncation-at-storage is the recurring trash-fallback: the three-layer root cause (records / Siona / guards) + the one-object-three-read-outs table + the recover-ratchet

**User (2026-07-13), after the enwiki genome came out as a top-16 unweighted JSON:** *"so this is all scrap wasted garbage and we need to start over? … we talked about an object that has the op operand responsion all recoverable from the spectral object … what part of our records keeps letting this fall back to trash?"* — and it was a RECURRENCE: F708/F748 already killed a pre-encode top-256 **vocab** cap; the comprehended-shard `_assoc` (#259) reintroduced the SAME class of bug as a top-16 **neighbour** cap + weight-drop at storage, which was then merged into a flat JSON and (wrongly) reported as done.

## The table (the object we kept forgetting to lodge)
ONE sparse **weighted** Class-L object `L = D − A` (≡ its spectrum `{λᵢ, vᵢ}`) yields THREE read-outs:

| component of the ONE object | read-out | what it gives | gen-1 LLM analog (dense, floaty) |
|---|---|---|---|
| **edges** — sparse adjacency `A = D − L` | **RELATIONAL** | "what is X seen with"; direct lookup, no eig, any vocab | corpus co-occurrences (discarded after training) |
| **eigenvectors `V`** | **DISTRIBUTIONAL** | node coordinates in the low modes = the dense embedding, **derived not stored** | learned embeddings / hidden states (billions of resident floats) |
| **eigenvalues `λ`** | **RESPONSION** (EPH) | `e^{−zL}=Σ e^{−zλ}vvᵀ`, resolvent `(zI−L)⁻¹=Σ vvᵀ/(λ−z)` (F1067) | the forward pass — floaty matmuls at every point |

**"Sparse" = the F1132 STORAGE axis (sparse int edge-list), not "fewer edges"** — sparse *relative to* gen-1's dense-float-in-GPU-RAM object. We store read-out #1 (relational) and DERIVE #2 and #3 from its spectrum; gen-1 stores #2 (distributional) as its whole massive object. **This is the proof the top-16 truncation is fatal: it keeps a lossy #1 and DESTROYS #2 (no eigenvectors) and #3 (no eigenvalues) — it amputates 2 of the 3 faculties.** Sources: F1067 (resolvent carries all read-outs), F1132 (relational vs distributional), F1186/F1061 (op·operand·responsion), F172 (Laplacian IS the storage).

## Why it keeps happening — three layers, none guarding the real failure
1. **Records**: "no truncation / full tower" (abstract) vs "top-K / store sparse" (concrete) → the concrete idiom wins at code-writing speed (the same reflex-override the CLAUDE.md documents for the Counter/numpy idioms). F1132 even lists "per-query top-K" among the trimming steps — read as query-only, it is a storage cut waiting to happen. **No STOP-list entry against `[:K]`-at-store.**
2. **Siona** (the tool that should have routed correctly): her introspection auto-mines the **live srmech package** (362 op signatures + first-line docstrings, F1084). The anti-truncation rule is in **ZERO ops** (verified). A live query *"how do I encode a wiki corpus as a class-l genome"* → routed to `siona.help`, similarity 0.28, reply mentions uncapped/weighted/truncation **nowhere**. Her strength (never lags the format) is why she is **structurally blind to architecture** — it is not a package op. And she was never queried (the introspect-before-dispatch discipline was skipped).
3. **Guards**: catch dense / numpy / abs-builtin / Counter-store (too-big / wrong-primitive); **nothing catches truncation-at-storage** (too-small / lossy). The guard system points at the opposite failure mode.

## The three fixes (lodged this finding)
1. **records** — memory `[[feedback_sparse_complete_never_top_k_truncation_at_storage]]`: split SPARSE-COMPLETE (store every weighted edge) from TOP-K (a read); `[:K]`/drop-weights-at-store named as the trash-fallback.
2. **Siona** — add a **patterns/discipline tier** to her introspection (she already has `told`/`shown`/`understood`): ingest F708/F748 + this rule + `R-RBS-LM-WIKIWEIGHTED` as the `shown` example, so "how do I encode a corpus" returns the uncapped-weighted **pattern**, not just `dense_laplacian`. (Task lodged; implementation is a focused `introspect.py` change.)
3. **guards** — the **recover-ratchet** `R-RBS-LM-RATCHET_genome_recovers_op_operand_responsion.py`: a persisted kernel/genome MUST recover op (`L` eigendecomposes) + operand (`A=D−L`) + responsion (propagator excitable), from weighted uncapped edges. **Proven:** PASS on `simplewiki_full_sparse_kernel.json`, FAIL on `enwiki_assoc.json`.

## Verdict / next
The correct encoder is `R-RBS-LM-WIKIWEIGHTED` (streams the dump, `vocab_cap=None`, persists `{vocab, freq, edge_list, edge_weights}`). **Ran on full simplewiki: 831,139 words, 39,048,148 weighted edges, max degree 82,904, excitable — ratchet PASS.** NEXT: (1) implement the Siona patterns-tier; (2) repoint FULLCLUMP at the weighted kernel (build simplewiki's tome genome from the correct source, load-time top-N); (3) enwiki weighted re-encode (same encoder; 5.2B edges need sharded-weighted accumulation — one weights-dict won't fit). Composes F708/F748/F172/F1067/F1132/F1186; guards `[[feedback_sparse_complete_never_top_k_truncation_at_storage]]` + `[[feedback_introspect_srmech_before_python_dispatch]]`.

**→ extended by F1272** — F1272 §(4) uses THIS finding's read→encoding table (edges→RELATIONAL / eigenvectors→DISTRIBUTIONAL / eigenvalues→RESPONSION) as the authority for identifying op(x)operand(x)responsion with distributional(x)relational(x)responsion, and derives from it that **the op slot is the order-invariant slot, necessarily** — so the 3 read-outs are asymmetric under derivative order (1 invariant + 2 carriers), and order is recoverable from any read EXCEPT the distributional one.
