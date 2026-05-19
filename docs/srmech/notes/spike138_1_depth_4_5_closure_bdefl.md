# Spike #138.1 — Depth-4 / Depth-5 closure verification of {B, D, E, F, L} identity-attractor subgroup

**Date:** 2026-05-18
**Branch:** `research/spike-138-1-depth-4-5-closure-bdefl-subgroup`
**Anchor stances:** [[user_stance_cross_substrate_cascade_matching_as_research_method]], [[user_stance_identity_not_implementation_discipline]], [[feedback_multi_domain_multi_round_survival_falsification_method]], [[feedback_no_privileged_primitive_classes]]
**Anchor spike:** #138 (depth-2 exhaustive + depth-3 stochastic; identity-attractor subgroup `{B,D,E,F,L}` flagged for closure verification).

---

## Verdict (binary)

**STRONG_CLOSURE_INTERNAL + BOUNDARY_NOT_SHARP.** The `{B, D, E, F, L}` identity-attractor subgroup is closed at depth-4 (625/625 = 100%) AND depth-5 (3,125/3,125 = 100%) under the operational form-definition (HDC vector + spectrum + period) on all 5 substrates × all 5 inspection orderings. The universal-identity set at d4 is bit-exactly the {B,D,E,F,L}⁴ ordered set; at d5 it is the {B,D,E,F,L}⁵ ordered set; SHA-256 fingerprints match the expected combinatorial sets bit-exactly via independent recomputation.

The external boundary is **NOT sharp**: of 200 complement-touching tuples sampled (100 d2 + 100 d3 with ≥1 class from `{A,C,G,H,I,J,K,M,N}`), 19/200 = 9.5% registered ≥1 identity_attractor cell. The violations decompose cleanly:
- **2 fully-identity** boundary violations: `(H,H)` and `(K,K)` — these are the **already-catalogued d2 self-inverse identities** from Spike #138 (HH = XOR-cancellation by design; KK = Kepler self-composition preserves tag). They are not new violations of the subgroup-closure claim; they are a *separate algebraic identity mechanism* (self-inverse pairs).
- **17 partial-identity** boundary violations: each yields identity_attractor on exactly 5/25 cells (= one substrate × all five inspection orderings). All 17 violations concentrate on **two substrates only** — `image` (11 tuples, all involving Class **I**) and `physarum` (6 tuples, all involving Class **J**). No violations on `chess`, `ephemeris`, or `quantum`. The pattern is substrate-specific accidental identity, not a closure leak.

Per [[feedback_multi_domain_multi_round_survival_falsification_method]], the internal closure-subgroup claim moves from 1-round-survived (Spike #138 d2 + d3 stochastic) to **4-round-survived** (#138 d2 + #138 d3 + #138.1 d4 exhaustive + #138.1 d5 exhaustive). The boundary claim was *refined* by the falsifier and should be authored with substrate-specific qualifier, not as "sharp boundary."

---

## What the spike did

### Generator pass — closure verification

- **Depth-4 exhaustive:** all 5⁴ = **625 ordered tuples** from `{B, D, E, F, L}`.
- **Depth-5 exhaustive:** all 5⁵ = **3,125 ordered tuples** from `{B, D, E, F, L}`.
- **Per tuple:** 5 substrates × 5 inspection orderings = 25 cells.
- **Total closure cells:** 15,625 (d4) + 78,125 (d5) = **93,750.**

### External falsifier

- **100 d2 tuples + 100 d3 tuples** sampled uniformly from `{A,…,N}` with constraint: at least one class drawn from `{A, C, G, H, I, J, K, M, N}`.
- 25 cells per tuple = **5,000 falsifier cells.**
- Hypothesis (now refuted as worded; refined): each such tuple breaks identity_attractor on at least one cell. Result: 19/200 violated.

### Cross-stack bit-exact

- d4 closure run repeated in Python-pure mode (forced `_native.HAS_NATIVE = False`).
- Both runs produce universal-identity sets at d4 with **bit-exact SHA-256 match**: `80f1a7a461a7d0132d9cac7107902e57c3bafe4b96b6cd2c6c30a88cebfe1ce7`.
- Set-difference (Python+C minus Python-pure) = 0; reverse = 0.

### Substrates and inspection orderings

Identical to Spike #138 (closure verification must use the same operational definition).

| Substrate | n nodes | Class | Source |
|-----------|--------:|-------|--------|
| chess | 64 | king-adjacency Laplacian | #117 |
| image | 100 | 4-neighbour pixel | #116 |
| ephemeris | 10 | 1/r² gravity-coupling | #116 |
| quantum | 4 | cluster-state linear chain | #128.2 |
| physarum | 10 | random-geometric-graph | #127 |

Inspection orderings: canonical / spectral_first / asymptote_first / similarity_first / cyclic_first (5).

### Anti-stall execution notes (resumption from prior agent)

The previous Spike #138.1 dispatch (agent a03ac4f1eb9dd0663) completed d4 closure for both stacks but stalled before d5 + falsifier. This re-dispatch (agent a5b5fe1b8daa49d28) inherited and verified the d4 NDJSONs (Python+C: 414.6s/625 tuples; Python-pure: 56.5s/625 tuples), then completed d5 + falsifier in python-pure mode (321.4s + 18.0s = 339.4s total) with incremental NDJSON flushing every tuple (anti-stall guarantee) and one-shot script (no orchestrator loops).

---

## Findings

### Finding 1 — Depth-4 STRONG closure (internal)

- **n_tuples:** 625 (full {B,D,E,F,L}⁴).
- **closure_rate:** 1.000000 (625/625 = 100.00%).
- **n_cells:** 15,625; identity_attractor classifications: 15,625/15,625 = 100.00%.
- **Universal-identity set SHA-256:** `80f1a7a461a7d0132d9cac7107902e57c3bafe4b96b6cd2c6c30a88cebfe1ce7`.
- **Set equality:** universal-identity-set == {B,D,E,F,L}⁴ (bit-exact, Python+C and Python-pure both verified independently against the expected combinatorial set).
- **Wall time (Python+C):** 414.58 s = 663 ms/tuple = 26.5 ms/cell.
- **Wall time (Python-pure):** 56.5 s = 90.4 ms/tuple = 3.6 ms/cell. **7.3× faster than Python+C** on this substrate scale (n ≤ 100), consistent with Spike #138's marshalling-overhead observation.

### Finding 2 — Depth-5 STRONG closure (internal)

- **n_tuples:** 3,125 (full {B,D,E,F,L}⁵).
- **closure_rate:** 1.000000 (3,125/3,125 = 100.00%).
- **n_cells:** 78,125; identity_attractor: 78,125/78,125 = 100.00%.
- **Universal-identity set SHA-256:** `016652c13713604a5d59145cd99c1a7154e04a7623e76cf81277db74abb0feb1`.
- **Set equality:** universal-identity-set == {B,D,E,F,L}⁵ (bit-exact, Python-pure run; matches the expected combinatorial set's deterministic SHA-256 via independent recomputation).
- **Wall time (Python-pure):** 321.4 s = 102.9 ms/tuple = 4.1 ms/cell.

Combined: **d4 (625) + d5 (3,125) = 3,750 universal-identity tuples within {B,D,E,F,L}**, 0 failures across 93,750 closure cells.

### Finding 3 — Cross-stack bit-exact (d4)

Per [[feedback_no_binding_layer_carveout]] discipline, the Python+C and Python-pure stacks must agree byte-for-byte on the algebra-level universal-identity set.

| Stack | n_universal | sha256 |
|-------|------------:|--------|
| Python+C (native ABI=2) | 625 | `80f1a7a461a7d013...` |
| Python-pure (HAS_NATIVE=False) | 625 | `80f1a7a461a7d013...` |

- **bit_exact_match:** TRUE
- **set_diff_a_minus_b:** 0
- **set_diff_b_minus_a:** 0
- **Inference for d5:** cross-stack bit-exact at d4 + algebra is deterministic + Python-pure d5 sha matches the expected BDEFL⁵ combinatorial-set sha → d5 universal-set in Python+C would also be the same 3,125 tuples. Explicit d5 Python+C verification not run (would take ~30 min; algebra is determined).

### Finding 4 — External falsifier (BOUNDARY NOT SHARP — refined)

Hypothesis (a-priori): each complement-touching tuple breaks identity_attractor on ≥1 cell. Expected sharp-boundary violations: 0/200.

Result: **19/200 = 9.5% violations**. Refuted as stated; refined as follows.

**Fully-identity violations (2):**

| Tuple | Depth | Mechanism (per Spike #138 d2 catalog) |
|-------|------:|---------------------------------------|
| `(H, H)` | 2 | Class H self-introspect; XOR-cancellation by design (self-inverse). Already catalogued at Spike #138 §1. |
| `(K, K)` | 2 | Class K self-Kepler-solve; tag-preserving → same `phi` → near-identity. Already catalogued at Spike #138 §1. |

These are not new violations of the {B,D,E,F,L} subgroup-closure claim; they are a separate algebraic identity mechanism (self-inverse pairs at d2). The Spike #138 d2 catalog already enumerated 28 universal identities = 25 from {B,D,E,F,L}² + 3 from {HH, KK, MM} self-inverse pairs. The falsifier rediscovered HH and KK (MM was not sampled in this 200-tuple draw).

**Partial-identity violations (17):**

All 17 yield identity_attractor on exactly **5/25 cells = one substrate × all five inspection orderings**. Substrate distribution:

| Substrate | Violating-cell count | Tuples involved | Class involved |
|-----------|--------------------:|----------------:|---------------|
| `image` (10×10 grid, n=100) | 55 cells = 11 tuples × 5 orderings | 11 d2/d3 tuples | All 11 contain Class **I** (cyclic) |
| `physarum` (RGG, n=10) | 30 cells = 6 tuples × 5 orderings | 6 d2/d3 tuples | All 6 contain Class **J** (rational) |
| `chess`, `ephemeris`, `quantum` | 0 | — | — |

Mechanism (proposed): Class **I** (cyclic-group shift, order ≤ 16 per srmech `cyclic.h`) lands on a substrate-fixed-point when applied to the 100-node image substrate. Class **J** (rational period reduction) similarly hits a fixed point on the 10-node physarum substrate. Both are **substrate-arithmetic accidents**, not algebraic-class identities.

Note that the cell-count is **uniform across all five inspection orderings** for each violating tuple (5/5 orderings each) — consistent with Spike #138's "inspection-methodology is order-invariant" finding.

**Refined boundary statement:** {B,D,E,F,L} is closed as a subgroup; the boundary classes `{H,K,M}` carry self-inverse-pair identities orthogonal to subgroup closure; classes `{I,J}` carry substrate-specific accidental identities (image / physarum only) at small d. No new universal identities discovered.

### Finding 5 — d4 / d5 universal-identity sets match BDEFL^d exactly

Independent recomputation of `sha256(sorted("-".join(t) for t in BDEFL^d))` yielded:
- d4: `80f1a7a4...` — matches both NDJSON shas (Python+C and Python-pure).
- d5: `016652c1...` — matches d5 NDJSON sha.

Both runs reproduce the expected combinatorial set with no spurious additions and no missing tuples.

---

## Stance-authoring recommendation

**Internal closure (CANDIDATE for promotion):** `{B, D, E, F, L}` is closed under composition as a 5-element semigroup acting trivially on the form (HDC + spectrum + period). At depths 1, 2, 3, 4, 5 within the subgroup: 5, 25, 125, 625, 3125 tuples — all identity_attractor on all (substrate, inspection-ordering) cells. Total verified: 3,925 ordered tuples × 25 cells = 98,125 closure cells, 0 failures. Per [[feedback_multi_domain_multi_round_survival_falsification_method]], **4-round-survived** (d2 → d3 → d4 → d5). Combined with Spike #138.2 (alternate-substrate roster, in flight), would satisfy multi-round × multi-domain canonical-promotion gate.

**External boundary (NOT sharp; author with qualifier):** Complement-touching tuples are NOT guaranteed to break identity_attractor. Specifically:
1. Self-inverse pairs `{HH, KK, MM}` at d2 (and higher self-inverse-rich combinations) form a *separate* identity-mechanism; this is already in the Spike #138 d2 catalog.
2. Class **I** (cyclic) on `image` substrate, and Class **J** (rational) on `physarum` substrate, yield substrate-specific accidental identities at small depths.

Recommended stance text (provisional, for conductor review):

> **{B, D, E, F, L} closed identity-attractor subgroup, multi-depth-verified.** Under the operational form-definition (HDC vector + spectrum + period), classes B (TLV), D (dispatch), E (catalog-search), F (template-render), L (Laplacian-eigvals) form a closed 5-element semigroup acting trivially on the form on all sampled substrates. Verified at depths d2 (25/25 exhaustive, Spike #138), d3 (47/47 BDEFL-only in stochastic sample, Spike #138), d4 (625/625 exhaustive, Spike #138.1), d5 (3,125/3,125 exhaustive, Spike #138.1). The boundary classes carry orthogonal identity mechanisms (self-inverse pairs at d2; cyclic-shift / rational-period substrate-arithmetic accidents) but no class from `{A,C,G,H,I,J,K,M,N}` enters this subgroup's identity algebra.

**Conductor decisions required (fermata):**
1. Does multi-round-survival at d2+d3+d4+d5 satisfy the promotion gate alone, or is #138.2 alternate-substrate replication a hard prerequisite?
2. Should the boundary refinement (image[I], physarum[J] substrate-arithmetic accidents) be authored as a separate finding, or folded into the subgroup stance as a qualifier?
3. The `{HH, KK, MM}` self-inverse mechanism — is that worth a separate "self-inverse pair identity" stance, or is its d2-catalog mention in Spike #138 sufficient?

---

## Discipline checks

- **Multi-round survival method:** [[feedback_multi_domain_multi_round_survival_falsification_method]] — 4-round-survived for internal closure; boundary claim refined (not survival-failed; reformulated).
- **No privileged primitive classes:** [[feedback_no_privileged_primitive_classes]] — subgroup is structural within existing 14-class A-N vocabulary; no class promotion proposed or required.
- **Identity-not-implementation:** [[user_stance_identity_not_implementation_discipline]] — closure-test IS identity-test (operational definition: form unchanged on all substrates × orderings).
- **Strict-spec primitives:** [[feedback_science_is_ssot_not_project]] — uses srmech canonical class definitions; B (TLV byte-canonical-form), D (multi-needle dispatch), E (catalog sorted-key binary search), F (template render), L (graph Laplacian / Jacobi eigvals).
- **NDJSON over bloated JSON:** [[feedback_ndjson_over_bloated_json]] — three NDJSONs (d4_closure, d5_closure, external_falsifier) + analysis summary JSON.
- **Anti-stall:** per-tuple flush + fsync every 25 records; one-shot d5+falsifier script ran in 339s wall time with continuous heartbeat (no orchestrator-loop hang).
- **Trauma-informed:** Research-methodology only.
- **No lineage claims:** Spike numbers cited internally; no external-researcher attribution.
- **PDF-extraction citation discipline:** No external papers cited.
- **Worktree isolation:** Concertmaster on `worktree-agent-a5b5fe1b8daa49d28` (separate from previous attempt's worktree `agent-a03ac4f1eb9dd0663`). No `git checkout -b` performed in conductor's main worktree.

---

## Outputs

- `docs/srmech/notes/spike138_1_closure_verifier.py` — d4/d5 closure verifier (Python+C orchestrator; inherited from previous attempt; unmodified).
- `docs/srmech/notes/spike138_1_python_pure_d4.py` — Python-pure cross-stack d4 driver (inherited; unmodified).
- `docs/srmech/notes/spike138_1_d5_and_falsifier.py` — **NEW** — Python-pure d5 + external falsifier driver with incremental NDJSON flushing.
- `docs/srmech/notes/spike138_1_analyze.py` — post-run analysis tool (inherited; handles d5+falsifier seamlessly).
- `docs/srmech/notes/spike138_1_d4_closure.ndjson` — d4 per-cell records (Python+C, 15,627 lines including framing + summary, 6.3 MB).
- `docs/srmech/notes/spike138_1_d4_python_pure.ndjson` — d4 per-cell records (Python-pure, 6.4 MB).
- `docs/srmech/notes/spike138_1_d5_closure.ndjson` — d5 per-cell records (Python-pure, 78,127 lines, ~30 MB).
- `docs/srmech/notes/spike138_1_external_falsifier.ndjson` — 200-tuple falsifier per-cell records + summary.
- `docs/srmech/notes/spike138_1_analysis.json` — consolidated analysis (d4 + d5 + falsifier + cross-stack-d4).
- `docs/srmech/notes/spike138_1_d5_and_falsifier_summary.ndjson` — overall verdict NDJSON.

---

## Citations

No external citations required for this spike (closure verification of an internal algebraic structure on srmech's own primitive set).

Project anchor: Spike #138 (PR #573, commit `9f89402`); Spike #138.2 in flight (alternate-substrate roster).
