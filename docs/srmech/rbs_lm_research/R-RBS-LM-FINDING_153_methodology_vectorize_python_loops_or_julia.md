# Finding 153 — Methodology: vectorize numpy / use srmech C primitives in batch; reserve Julia for non-vectorizable hot paths

**Status:** Methodology refinement; load-bearing for all future smoke design
**User direction 2026-05-28:**

> "why python when srmech/siona has C/Python parity for cascade operations?
> and also julia when you do need to script cpu intense things?"

---

## §1 The mistake (R-RBS-LM-108 v1)

R-RBS-LM-108 v1 used naive per-pair Python loops:

```python
# WRONG: O(V²) Python function-call overhead
for i in range(V):
    for j in range(V):
        sim = hdc.klein4_similarity(candidate[i], tokens[j])
```

At V=2000 this is **4 million Python function calls**. Each call has Python-interpreter overhead (~1-5μs) even though the underlying C primitive is fast (<1μs per call). The result: V=2000 ran 46 minutes before being killed.

The substrate's primitives are C-fast PER CALL. The bottleneck is the Python loop INVOKING them 4M times.

---

## §2 The correct methodology

### §2.1 srmech is C/Python parity — use the C side via batch ops

srmech v0.4.3 has native C dispatch for all primitives. Python wrappers call into libsrmech.{so,dll,dylib}. PER-CALL overhead is the Python interpreter, NOT the C work.

**Use ops in BATCH form** so the Python interpreter pays one call per batch, not per pair.

### §2.2 Vectorize via numpy

For similarity / comparison / bind operations that don't have native batch APIs, use numpy broadcasting + reduction:

```python
# RIGHT: O(V) Python calls; the V² work happens in numpy C-fast
# Match-fraction similarity, vectorized
sim_matrix = (candidates_matrix[:, np.newaxis, :] == tokens_matrix[np.newaxis, :, :]).mean(axis=2)
# (V, 1, D) == (1, V, D) → (V, V, D) → mean(-1) → (V, V)
preds = sim_matrix.argmax(axis=1)
```

For Klein-4 binding (XOR over F₂×F₂):
```python
# Klein-4 values are uint8 in {0,1,2,3}; klein4_bind ≡ bitwise XOR
bound = contexts ^ tokens  # ALL N pairs in one call
```

For Klein-4 bundling (majority vote):
```python
# Per-position mode across N rows
counts = np.zeros((4, D), dtype=np.int32)
for s in range(4):
    counts[s] = (bound == s).sum(axis=0)
composite = counts.argmax(axis=0).astype(np.uint8)
```

For polar similarity (match-fraction):
```python
sim = (candidate == target).mean()  # one op, no per-position loop
```

### §2.3 Memory-vs-time tradeoff with chunked vectorization

Full (V, V, D) tensor at V=2000, D=8192 is 32GB bool — too big.

Chunk vectorization:
```python
CHUNK = 50
preds = np.empty(V, dtype=np.int64)
for start in range(0, V, CHUNK):
    chunk = candidate_Bs[start:start+CHUNK]
    sim = (chunk[:, np.newaxis, :] == tokens[np.newaxis, :, :]).mean(axis=2)
    preds[start:start+CHUNK] = sim.argmax(axis=1)
```

This keeps memory bounded while still amortizing Python overhead over CHUNK candidates per call. Empirically: V/CHUNK = 40 Python calls instead of V² = 4M calls. ~100,000× fewer interpreter invocations.

### §2.4 When to reach for Julia

Per user direction: Julia is the right tool for **CPU-intense hot paths that don't vectorize cleanly into numpy**.

Examples where numpy isn't enough:
- Complex control flow per element (e.g., branch-heavy filter chains)
- Operations with state across iterations (e.g., Markov-chain-like updates)
- Hot loops where Python's per-iteration overhead dominates even when numpy is used
- Cases where data shape changes dynamically per iteration

Julia gives:
- JIT-compiled performance (near-C)
- No Python interpreter overhead
- Clean syntax for mathematical operations
- Good interop with numpy/scipy via PyJulia

For this project's research subtree, Julia would be reasonable for:
- Spectral classifier prototypes (per F150 §6.2 wishlist)
- Compression algorithms (per F152 §1.4)
- Multi-substrate cascade composition with branch-heavy logic
- Any hot loop where numpy vectorization can't fit the data shape

### §2.5 srmech/siona future C parity

Per UPSTREAM_NOTES.md §6 wishlist: the `srmech.siona` sub-package would have chiral A-N variants. When that lands, batch ops should ship with it (similar to how `klein4_bind` is per-call but works on `(D,)` arrays).

For batch similarity / batch bind / batch bundle at scale, srmech upstream could add:
- `klein4_similarity_batch(query, candidates)` → returns (V,) array
- `polar_similarity_batch(query, candidates)` → returns (V,) array
- `klein4_bundle_chunked(stack, chunk_size)` → memory-bounded mode

These would be the "right" C primitives for large-N work. Currently the workaround is numpy vectorization in research code; future srmech versions could ship them natively.

---

## §3 Methodology rule going forward

```
RULE 1: srmech primitives are CALL-OVERHEAD-DOMINATED at large N.
        Use vectorized numpy ops that match what the C primitives
        do internally; let Python pay ONE call per batch.

RULE 2: For Klein-4: XOR is bitwise XOR (uint8); similarity is
        match-fraction over uint8 arrays. Both vectorize cleanly.

RULE 3: For polar: bind is element-wise sign-product (int8 multiply);
        similarity is match-fraction. Both vectorize cleanly.

RULE 4: For bipolar: bind is sign-product; similarity is cosine via
        dot product. Both vectorize cleanly.

RULE 5: Memory budget — full (V, V, D) tensors get prohibitive past
        V=2000 at D=8192. Use chunked vectorization (CHUNK=50-100).

RULE 6: Julia is the escape valve when:
        - numpy vectorization can't fit the shape
        - Hot path has dynamic control flow
        - C-speed is required without Python interpreter overhead
        - PyJulia interop adequate for cross-language calls

RULE 7: For methodology-blocking hot paths in srmech research:
        - First try numpy vectorization
        - Then try chunked vectorization
        - Then consider srmech upstream batch primitive (UPSTREAM_NOTES wishlist)
        - Last: Julia rewrite for that specific path
```

---

## §4 Where this methodology was missed previously

Re-reading prior smokes through this lens, several may have hit similar O(V²) Python-overhead bottlenecks:

| Finding | Where | Potential bottleneck |
|---|---|---|
| R-RBS-LM-99v2 (cross-sector retrieval) | per-concept similarity loop | likely Python-overhead at high N |
| R-RBS-LM-100 (multi-class cascade) | per-concept retrieval loop | Python-overhead |
| F140 multi-class cascade | bundle + per-query retrieve | mostly OK; small N |
| R-RBS-NN-11 capacity | bundle + per-query retrieve at N=512 | acknowledged 4 min @ N=512 |
| R-RBS-NN-12 hierarchical | per-bucket retrieval | bucket-local scoring helps somewhat |

The R-RBS-NN-11 4-minute V=512 ran fine; later work hit harder ceilings. R-RBS-LM-108 v1 hit the worst case because it's vocab-cleanup at LLM scale (V=2000).

**Going forward**: any new smoke at V ≥ 500 or N ≥ 500 should use vectorized numpy primitives by default.

---

## §5 The R-RBS-LM-108v2 rewrite (this session)

R-RBS-LM-108v2 (companion file) implements the vectorized methodology:
- Bipolar similarity via dot product matrix (`candidates @ tokens.T`)
- Klein-4 bind via `^` (bitwise XOR)
- Klein-4 bundle via per-position vectorized argmax
- Klein-4 similarity via broadcasted equality match-fraction
- Chunked similarity (CHUNK=50) for memory budgeting

Empirical speedup measured in the R-RBS-LM-108v2 run results. Logged separately.

---

## §6 What this finding does NOT claim

Per MFO §VII.6.20:

- Does NOT claim Python+numpy is universally fast enough. There are hot paths where Julia or C-extension is genuinely needed.
- Does NOT claim numpy vectorization is always cleaner. For complex control flow, Python loops over small N are sometimes more readable.
- Does NOT recommend Julia adoption for the whole research subtree. Per project conventions, Python+srmech is the canonical substrate; Julia is reserved for specific bottlenecks.
- Does NOT propose immediate srmech upstream batch-primitive additions. UPSTREAM_NOTES.md §6 wishlist is the future-scope home.

---

## §7 Cross-references

- R-RBS-LM-108 v1 (per-pair Python loop; deferred; 46-min hang)
- R-RBS-LM-108v2 (this session's vectorized rewrite)
- UPSTREAM_NOTES.md §6 (siona wishlist; future batch primitives)
- `[[user_stance_kepler_shape_universal]]` (algebra IS the primitives — and the C primitives are call-overhead-dominated, not work-bound)
- srmech v0.4.3 (HAS_NATIVE=True; per-call C dispatch is fast)

**Files committed:**
- `R-RBS-LM-108v2_klein4_4x_ceiling_vectorized.py` (vectorized rewrite)
- `R-RBS-LM-FINDING_153_*.md` (this methodology finding)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-28 per user direction. Methodology refinement: srmech is C/Python
parity with per-call C dispatch; the slow path is Python-loop CALLING fast C primitives,
not the primitives themselves. Use numpy vectorization (matrix products, broadcasting,
chunked reductions) to amortize Python overhead across batched ops. Julia is the escape
valve for hot paths that don't fit numpy vectorization cleanly. Rule going forward:
any smoke at V ≥ 500 or N ≥ 500 uses vectorized methodology by default. R-RBS-LM-108v2
demonstrates the rewrite.*
