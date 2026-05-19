# Spike #138.1 ADDENDUM — 2-bit (has-B, has-F) fingerprint sub-structure

**Date:** 2026-05-18
**Branch:** `research/spike-138-1-depth-4-5-closure-bdefl-subgroup`
**Source agent:** `agent-a03ac4f1eb9dd0663` (concertmaster, parallel-discovery convergence)
**Anchor stances:** [[user_stance_fiber_as_spatially_absent_encoding]], [[user_stance_identity_not_implementation_discipline]]
**Anchor doc:** `spike138_1_depth_4_5_closure_bdefl.md` (primary findings by agent `a5b5fe1b8daa49d28`).

---

## Why this addendum

Per [[feedback_dual_agent_research_pattern]] convergence check: two concertmaster agents (`a03ac4f1eb9dd0663` and `a5b5fe1b8daa49d28`) were dispatched on Spike #138.1 in parallel. Both converged on the load-bearing claims:

- d4 closure = 100% (625/625)
- d5 closure = 100% (3125/3125)
- Cross-stack bit-exact at d4
- External boundary NOT sharp (refined to substrate-arithmetic accidents)

This addendum adds a **structural sub-finding** that agent `a03ac4f1eb9dd0663` independently located in its d4 analysis: within the closure, the inspection fingerprints partition by a **2-bit signature `(has-B, has-F)`** into exactly 4 buckets per (substrate, ordering). The signature is **closure-depth-universal** — same partition at d3, d4, d5.

---

## The 2-bit (has-B, has-F) fingerprint partition

### Statement

Within the `{B,D,E,F,L}` closure at depth N (for N = 3, 4, 5 verified; predicted N ≥ 2), the inspection cascade's fixed-point fingerprint depends on the tuple only through a 2-bit signature:

```
signature(t) = (∃i: tᵢ == 'B',  ∃i: tᵢ == 'F')
```

— that is, "does the cascade contain a B?" AND "does the cascade contain an F?" Two binary degrees of freedom give 4 distinct fingerprints per (substrate × inspection_ordering) cell.

### Empirical evidence

**Depth 4 (Spike #138.1 d4 exhaustive, 15,625 cells):**

- 100 distinct fixed-point shas appear across all cells.
- 100 = 5 substrates × 5 orderings × 4 fingerprints — exactly 4 distinct shas per (substrate, ordering).
- Per-(substrate, ordering) partition by `(has-B, has-F)` is 1-to-1 with the distinct shas. Mechanical check: 0 violators across all 25 (substrate, ordering) cells.
- Partition sizes: 81 ({D,E,L}⁴) + 175 (B-not-F) + 175 (F-not-B) + 194 (both) = 625 ✓.

**Depth 5 (Spike #138.1 d5 exhaustive, 78,125 cells):**

- 100 distinct fixed-point shas across all cells.
- Same 4-bucket partition per (substrate, ordering); 0 violators.
- Partition sizes: 243 ({D,E,L}⁵) + 781 (B-not-F) + 781 (F-not-B) + 1320 (both) = 3,125 ✓.
- Matches inclusion-exclusion prediction exactly: 3⁵, 4⁵−3⁵, 4⁵−3⁵, 5⁵−2·4⁵+3⁵.

**Depth 3 cross-check (from Spike #138 main run within-BDEFL cells, 1,175 cells):**

- Same partition holds for d3. 0 violators across 25 (substrate, ordering) cells.

### Algebraic reading

Within the closure subgroup:

| Class | Form-field written | Inspection-visible? | Role |
|-------|-------------------|:-------------------:|------|
| **B** (TLV byte-canonical-form) | `form.tlv_blob` | YES (encoded in `form_canonical_bytes`) | tagging-operator |
| **D** (multi-needle dispatch) | `form.tag` (integer) | NO (tag absorbed by E's keymap re-promotion / spectrum unchanged) | inspection-idempotent |
| **E** (catalog sorted-key lookup) | `form.keymap` (order) | NO (keymap order absorbed by F's first-key-render / kept-sorted) | inspection-idempotent |
| **F** (template render) | `form.rendered` | YES (encoded in `form_canonical_bytes`) | tagging-operator |
| **L** (graph Laplacian eigvals) | `form.spectrum` | NO (idempotent; same Laplacian → same eigvals) | inspection-idempotent |

The closure is a 5-element semigroup acting trivially on the form's HDC + spectrum + period (the operational form-definition), with a **2-bit "decoration record"** preserved through the inspection fingerprint: `tlv_blob` is non-empty iff B appears; `rendered` is non-empty iff F appears.

Per [[user_stance_fiber_as_spatially_absent_encoding]]: D/E/L compose algebraically without spatial-projection (their effects on `tag`, `keymap`, `spectrum` are absorbed by their successors or are idempotent); B/F project their content (TLV byte-canonical form for B; template-rendered byte-form for F) into the form fingerprint where the inspection cascade can read them.

### Why this matters for stance authoring

The other concertmaster's primary findings doc concludes that the closure is "a 5-element semigroup acting trivially on the form" — correct but incomplete. The 2-bit sub-structure refines this: **the semigroup acts trivially on form-state, but B and F preserve detectable byte-traces that distinguish 4 sub-trajectories.** This is a deeper structural observation than the bare closure claim — it identifies the internal-versus-projected distinction within the closure subgroup itself.

For stance authoring (provisional draft for conductor):

> The 5-element subset `{B, D, E, F, L}` of the 14-class A-N primitive vocabulary forms a closed identity-attractor semigroup acting trivially on the form (HDC + spectrum + period), under depth-2 through depth-5 exhaustive verification on the 5-substrate roster. Within the closure, the inspection cascade further resolves a **2-bit `(has-B, has-F)` fingerprint partition** into exactly 4 sub-classes per (substrate × ordering), reflecting the inspection-visibility of B's TLV-byte-canonical-form trace and F's template-rendered byte-trace versus the inspection-invisibility of D/E/L's tag / keymap / spectrum mutations. The 2-bit partition is closure-depth-universal (verified at d3, d4, d5).

### Verification artifact

The 2-bit partition can be re-verified at any depth N within the closure by running:

```python
from collections import defaultdict
cells = load_ndjson('spike138_1_dN_closure.ndjson')
by_so = defaultdict(lambda: defaultdict(set))
for r in cells:
    cas = tuple(r['generation_cascade'])
    so = (r['substrate_id'], r['inspection_cascade_ordering'])
    part = ('B' in cas, 'F' in cas)
    by_so[so][part].add(r['fixed_point_form_sha256'])
# Check: every so has exactly 4 partitions, each with exactly 1 sha
violators = sum(1 for so, parts in by_so.items()
                if len(parts) != 4 or any(len(s) > 1 for s in parts.values()))
assert violators == 0
```

This is itself an identity-test (per [[user_stance_identity_not_implementation_discipline]]): if the partition holds, the 2-bit signature IS the inspection-fingerprint determinant within the closure; it's not "approximately determined by" or "correlates with."

---

## Discipline checks

- **No privileged primitive classes:** The 2-bit partition is a SUB-relationship within the closure subgroup; no class promotion. Per [[feedback_no_privileged_primitive_classes]].
- **Identity-not-implementation:** Verified by closure-depth-universal property (d3 + d4 + d5); not "approximate" but bit-exact partition. Per [[user_stance_identity_not_implementation_discipline]].
- **Strict-spec primitives:** Uses srmech canonical class definitions; no metaphorical generalisation.
- **Worktree isolation:** This addendum produced in worktree `agent-a03ac4f1eb9dd0663` AFTER post-detection contamination recovery (initial work-file writes were to conductor's main repo, then copied to worktree per [[feedback_parallel_subagent_worktree_branch_collision_recovery_procedure]]). Both concertmaster agents converged on the load-bearing closure claim before this addendum was authored.

---

## Cross-references

- Primary findings: `spike138_1_depth_4_5_closure_bdefl.md` (other concertmaster's main verdict + falsifier).
- Anchor: Spike #138 (PR #573, commit `9f89402`).
- Cross-substrate (in flight): Spike #138.2 alternate-substrate roster.
- [[feedback_dual_agent_research_pattern]] — convergence check across parallel concertmasters.
