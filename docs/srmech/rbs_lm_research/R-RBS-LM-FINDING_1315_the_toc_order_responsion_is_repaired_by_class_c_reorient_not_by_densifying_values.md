# F1315 — the TOC order-responsion is **REPAIRED**, and the fix is **Class-C (reorient), not densification**: rotating each turn by its index before the per-slot fold scores **0 collisions in 3680 permutations** and **0/23 at the mandated 1-non-zero-slot/leaf gate**, exactly matching the ordered-content-address baseline — so a **holonomy-shaped (fiber) responsion CAN reach the content-address bound** and the TOC does not have to abandon the fiber read. The two intuitive fixes both FAIL, in two *different* and diagnostic ways: position-tagging the **values** improves 19.8× but still leaks (80 collisions, 2/23 at the gate), and a single cross-slot accumulator is **catastrophically worse** (2155 collisions, ~55–63 % at *every* density) because its codomain is the 8-element group Q₈ — a **capacity** failure, not an order-blindness one.

**Answers F1314 §4.5 / Q1** (the open question that blocked the distributed TOC). srmech 0.9.0rc335, native.

*(F1301 convention: **op** = the recipe (`recipe_fp`, distributional) × **operand** = the data genes (leaves, relational) × **responsion** = the walk order (`order_fp`, eigenvalues). This finding is entirely about the **responsion** slot — the one F1314 measured as a false shadow.)*

## The measurement `[DEMONSTRABLE]`
4 leaves × 128 slots; 23 non-identity permutations × 20 content-derived trials = **460 permutations per density row**, 8 densities = **3680 per candidate**. Leaves are deterministic Class-A content-addresses (never an RNG — F1259/F1304); re-running reproduces every number. Degenerate permutations (every moved leaf byte-identical to the one it replaces → a genuine wire no-op) are filtered, because counting them would *understate* a good responsion; exactly one such case occurs.

```
 nonzero/leaf  density   v2 per-slot    v3a pos-tag   v3b cross-slot   v3c rotate-idx   v3d ordered-A
        1        0.8%    460 = 100%      68 = 14.8%    256 = 55.7%       0 = 0.0%        0 = 0.0%
        2        1.6%    436 =  94.8%    12 =  2.6%    288 = 62.6%       0 = 0.0%        0 = 0.0%
        4        3.1%    400 =  87.0%     1 =  0.2%    252 = 54.8%       0 = 0.0%        0 = 0.0%
        8        6.2%    233 =  50.7%     0 =  0.0%    292 = 63.5%       0 = 0.0%        0 = 0.0%
       16       12.5%     57 =  12.4%     0 =  0.0%    280 = 60.9%       0 = 0.0%        0 = 0.0%
   32/64/128   25-100%      0 =   0.0%     0 =  0.0%   ~252 = 54.8%      0 = 0.0%        0 = 0.0%
 ─────────────────────────────────────────────────────────────────────────────────────────────────
 TOTAL / 3680             1585            80           2155              0               0
 GATE (1 nz/leaf)        23/23 FALSE     2/23 FALSE   23/23 FALSE     0/23 PASS       0/23 PASS
 stability (same order → same fp)   all five: True
```

## Why each candidate behaves as it does
- **v2 (shipped `genome_fiber_holonomy`) — FALSE SHADOW.** It folds **per slot** (`acc[s] = q8_mult(acc[s], turn_t[s])`), the Q₈ identity is byte 0, and **40/64 Q₈ pairs commute**. Leaves with **disjoint per-slot support** therefore commute in every slot. Collisions fall monotonically as density rises (100 % → 0 % by 25 %) — it is sound on dense text and unsound on sparse, which is precisely inverted from our needs.
- **v3a (position-tag the VALUES) — still leaks.** Binding a dense Class-A position key densifies every turn, so support is always full. But the slots where **no** turn carries data fold to the same key-product in any order (the keys stay in index order), so only the ≤4 data-bearing slots can discriminate — and Q₈'s commuting still bites there. 19.8× better (1585→80) and clean at density ≥8, but **2/23 at the gate**. *Improvement is not repair.*
- **v3b (single cross-slot accumulator) — CAPACITY failure, the instructive one.** ~55–63 % collisions at **every** density, flat. Order-sensitivity is irrelevant when the fingerprint's codomain is the **8-element group Q₈** (3 bits). This is a distinct failure mode from v2's and worth naming: *a responsion can fail by being order-blind, or by having nowhere to put the answer.*
- **v3c (ROTATE-BY-INDEX, Class-C reorient) — PASSES.** Cyclically rotate turn *t* by a content-derived `stride·t` before the shipped per-slot fold. This makes the support **LOCATION** position-dependent, so permuting the turns **moves** each turn's non-zero slots and disjointness cannot survive a permutation. **0/3680, 0/23 at the gate.**
- **v3d (ordered Class-A content-address) — PASSES, as the bound.** A content-address of the ordered concatenation; it cannot be defeated by any commuting structure because it never multiplies anything. Included to *bound* the problem.

## The result that matters
**v3c ties v3d exactly (0 = 0).** That is the load-bearing outcome: the **framework-native fiber read reaches the content-address bound**, so the TOC's order check does **not** have to be demoted from a holonomy to a hash. The repair is one Class-C reorient in front of the shipped Class-M fold — `Class-C ∘ (the existing genome_fiber_holonomy)` — not a new algebra and not an abandonment of the responsion slot.

**The general lesson, stated so it transfers:** when a per-slot non-abelian fold is order-blind, the defect is **support geometry, not value entropy**. Densifying the values (v3a) treats the symptom; moving the support (v3c) removes the cause. And a fold's codomain must be large enough to hold the answer (v3b) — order-sensitivity in an 8-element group is worthless.

## Honest scope
- `[DEMONSTRABLE]` everything above: the sweep, the gate, the stability control, the degenerate diagnosis (the single residual collision was two **identical** leaves swapped — a no-op whose equal fingerprint is *correct*).
- `[SPECULATIVE]` v3c's `stride` is a content-derived constant from one Class-A address; whether some (stride, leaf_dim, n_leaves) combinations degenerate (e.g. stride ≡ 0 mod leaf_dim, or a rotation that maps a support set onto itself) is **not swept**. Before wiring in: sweep stride × leaf_dim, and assert `gcd(stride, leaf_dim)` behaviour explicitly.
- Not tested at the 𝕆 rung (`genome_octonion_holonomy`), where non-**associativity** adds a failure mode absent at ℍ. F1314 Q6 predicts an 𝕆-carried index needs `genome_octonion_associator` in it; unexamined.
- This repairs the **order** responsion only. Every other F1314 correction stands (the TOC is not a demand-load; `gene_express` is a read-time filter; the coupling ships in plaintext; 35.8 % byte overhead at 200 chromosomes).

## Verdict / next
The TOC's lift-gate is **repairable and repaired in prototype**: adopt **v3c** (`order_fp = ClassA(genome_fiber_holonomy(rotate_by_index(turns)))`). It is still **not wired into `genome_store.py`** — the remaining gate is the stride×leaf_dim degeneracy sweep, then the F1314 migration steps. Generating code: `R-RBS-LM-TOCV3_*.py` (exit 0; numpy-free, fractions-free, no `abs()`).

Composes **F1314** (the false-shadow measurement this answers — *§4.5 Q1 closed*), **F1307/F1309** (the Q₈ substrate whose commuting structure is the cause), **F1272** (the responsion slot carries order — here it *failed* to, and why), **F1301** (the triple), `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]` (the gate that killed v1/v2 and now certifies v3c), `[[feedback_stay_rbs_hdc_sparse_never_dense]]` (why the sparse regime is the one that counts), `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`, `[[feedback_computational_provenance_discipline]]`.

**→ closes F1314 Q1** — the v3 responsion exists: **Class-C reorient before the fold**, 0 collisions at the mandated sparsity, matching the content-address bound.

**→ generalised by F1316** — the repair is NOT a ℍ-rung trick: it lifts to 𝕆 unchanged (0 collisions), while the per-slot fold fails IDENTICALLY at 𝕆 (23/23 at the gate) despite 𝕆 being ~2x less commutative and 32.8% non-associative. So both the defect and the repair are **carrier-independent** — driven by the identity element + support geometry, not algebra richness. F1316 also settles a sharp negative: the 𝕆-only **associator adds ZERO order information** (bit-for-bit identical collisions to the plain holonomy), so it is a RICHNESS read, not an ORDER read.

**→ stride gate CLOSED by F1319** — the degeneracy question is not a sweep but a **derivable precondition**: `leaf_dim / gcd(stride, leaf_dim) ≥ n_leaves`, which predicted pass/fail on **40/40** (leaf_dim, stride) pairs with **zero mispredictions**. The degenerate cases are exactly `stride ≡ 0` (no rotation → reduces to the v2 false shadow) and gcd-too-large (offsets recycle). Also scaled: n=8 over 40,319 perms and non-uniform densities, both **0 collisions**.
