# F277 — MS#21 #812: the loop bind carries order/tree/direction at NO capacity cost vs Klein-4 (the k=7 structure is "free")

**Headline:** The de-risk question for #812 — *does non-associativity cost capacity?* — answers **no**. Head-to-head at matched D=2048, M=128 codebook, 5 trials: the block-octonion **loop bind** holds **100% retrieval to K=64** and **0.923 at K=128**, while the commutative+associative **Klein-4 XOR bind** holds 100% to K=32, 0.997 at K=64, **0.867 at K=128**. Capacity knee (first K below 0.9): **loop-bind >128, klein4 =128**. So the loop bind is **at least as good** as the XOR bind in this regime (marginally higher at K=128) — meaning the **order + tree + direction structure it carries (F274) is free**: no capacity penalty for non-associativity. Single-model; reproducible via committed `loop_bind_capacity_812.py`; srmech v0.6.0rc20.

---

### §A — the head-to-head — **DEMONSTRATED**
Standard HDC associative-memory protocol: bundle K `key∘val` pairs; per key, unbind + clean up against the M=128 value codebook; accuracy = fraction retrieved.

| K | 2 | 4 | 8 | 16 | 32 | 64 | 128 |
|---|---|---|---|---|---|---|---|
| **loop-bind (k=7)** | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **1.000** | **0.923** |
| **klein4 XOR** | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.997 | 0.867 |

### §B — reading
- **No capacity cost.** Both binds are **norm-preserving** (octonion product preserves norm; klein4 XOR is bipolar), so the bundle cross-terms behave like random vectors and cleanup works the same way — the curves track. The loop bind's extra structure (sequence/tree/direction) does **not** come out of the capacity budget.
- **Marginally higher at the tail** (0.923 vs 0.867 at K=128). *Honest scope:* one regime, 5 trials — this is reported as "≥ klein4, no penalty," **not** claimed as a general capacity advantage (could be the 256-block averaging spreading the bundle slightly more evenly; would need a wider sweep to assert an edge). The load-bearing result is the **null cost**, not the small gap.
- **Combined with F274 + F276:** the loop bind is a viable HDC bind (unbindable), it carries order/tree/direction the XOR bind erases, it realizes at HDC scale (block-octonion), AND it does so at no capacity cost. That is the full de-risk for "is k=7 worth building" — **yes**.

### §C — #812 status + what's left in MS#21
- **#812 RESOLVED:** no capacity penalty; the klein4 head-to-head (deferred from the F276 gate run) is done.
- **#811 RESOLVED** (F276): block-octonion tiling.
- **#813 (composition)** — next; its full compose-engine test leans on the registered op (#814), so the part testable now is coexistence + the M∘C∘K cascade design.
- **#814 (op spec)** — unblocked; held for explicit authorization (edits the srmech package).

### Status / discipline
FRAMEWORK + DEMONSTRATED (head-to-head verified at D=2048, M=128, 5 trials; reproducible via committed `loop_bind_capacity_812.py`, seed attested-B). Honest scope: null capacity cost is the claim; the small tail gap is **not** asserted as a general advantage. No-magic (M, K, D = attested-to-structure / measured B). Class-K (octonion cleanup via stacked-matrix argmax = cosine; klein4 via native similarity; no `abs()`). CAD-ban. Single-model / no-twin. Baseline = srmech `klein4_bind`/`klein4_bundle`/`klein4_similarity`. Builds on F274 (the properties), F276 (the HDC realization). Resolves MS#21 #812. Verified srmech v0.6.0rc20, `/tmp/srmech_rc20_venv`. `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`.
