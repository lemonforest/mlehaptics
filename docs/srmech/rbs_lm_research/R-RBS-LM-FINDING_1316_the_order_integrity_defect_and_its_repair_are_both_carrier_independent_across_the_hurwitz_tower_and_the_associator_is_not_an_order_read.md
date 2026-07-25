# F1316 — the genome's **order-integrity defect AND its repair are both CARRIER-INDEPENDENT across the Hurwitz tower**: the per-slot fold fails identically at 𝕆 (1502 collisions, **23/23** at the mandated gate) despite 𝕆 being **~2× less commutative** than ℍ *and* **32.8 % non-associative** — because the defect is driven by the **identity element + disjoint support**, not by algebra richness. The Class-C reorient repair **lifts unchanged** (**0** collisions at 𝕆). And the sharp negative: **the octonion ASSOCIATOR — the 𝕆-only read with no ℍ analogue — adds ZERO order information**, scoring *bit-for-bit identical* to the plain holonomy at every density (1502 = 1502). **The associator is a RICHNESS read, not an ORDER read.** So this is **genome machinery, not a siona trick** — it belongs upstream (§ ask below).

**User (2026-07-24):** *"extend test to Octonion rung. this appears to be core, biology:simulation parity cascade, genome machinery that needs to make it to srmech."*

*(F1301 convention: this is entirely the **responsion** slot — the walk-order read — now measured at two rungs of the tower.)*

## The measurement `[DEMONSTRABLE]` — srmech 0.9.0rc335, native
𝕆 structure, measured first so the result is not a surprise: **commuting 88/256 = 34.4 %** (vs Q₈'s 40/64 = 62.5 %), **associating triples 2752/4096 = 67.2 %** → 1344 non-associating, and — the decisive detail — **identity 0 still commutes with everything**. Same protocol as F1315: 4 leaves × 128 slots, 23 non-identity perms × 20 content-derived trials = 460 perms/row, degenerate no-op perms filtered.

```
 nonzero/leaf  density   v2O per-slot   v3aO pos-tag   v3cO rotate-idx   v3eO holo‖ASSOC   v3d ordered-A
       1         0.8%    460 = 100.0%    81 = 17.6%      0 =  0.0%       460 = 100.0%      0 = 0.0%
       2         1.6%    448 =  97.4%    21 =  4.6%      0 =  0.0%       448 =  97.4%      0 = 0.0%
       4         3.1%    416 =  90.4%     1 =  0.2%      0 =  0.0%       416 =  90.4%      0 = 0.0%
       8         6.2%    163 =  35.4%     0 =  0.0%      0 =  0.0%       163 =  35.4%      0 = 0.0%
      16        12.5%     14 =   3.0%     0 =  0.0%      0 =  0.0%        14 =   3.0%      0 = 0.0%
      32        25.0%      1 =   0.2%     0 =  0.0%      0 =  0.0%         1 =   0.2%      0 = 0.0%
   64/128    50-100%       0 =   0.0%     0 =  0.0%      0 =  0.0%         0 =   0.0%      0 = 0.0%
 ──────────────────────────────────────────────────────────────────────────────────────────────────
 TOTAL                   1502            103             0               1502              0
 GATE (1 nz/leaf)       23/23 FALSE      1/23 FALSE     0/23 PASS        23/23 FALSE     0/23 PASS
```

## Q-A — the defect is CARRIER-INDEPENDENT
𝕆 is a **strictly richer** algebra than ℍ: nearly half the commuting, plus genuine non-associativity. If the v2 false shadow were about *algebra richness*, 𝕆 should have rescued it. **It does not** — v2O is 23/23 at the gate, exactly as v2 was at ℍ. The cause is structural and rung-independent: **byte 0 is the identity at every rung and commutes with everything, so leaves with disjoint per-slot support never multiply two non-identity values in the same slot, and the fold has nothing to be non-commutative *about*.** A richer algebra cannot save a fold that never exercises it.

*Honest nuance (the richness IS visible, just not where it matters):* 𝕆 does decay faster with density than ℍ — 35.4 % vs 50.7 % at 8 non-zero slots, 3.0 % vs 12.4 % at 16 — so climbing the tower genuinely helps **in the dense regime**. It helps **not at all** at the sparsity the project mandates. Richness buys you nothing on the axis you actually need.

## Q-B — the ASSOCIATOR is NOT an order read (the sharp negative)
`genome_octonion_associator` is the 𝕆-only read, the 3-index object F1310/F1311 established that **no 2-tensor Laplacian can hold**. It was the natural candidate to rescue the sparse regime. It contributes **exactly nothing**: v3eO (`holonomy ‖ associator`) scores **1502 collisions — bit-for-bit identical to the plain holonomy's 1502 — at every single density row** (460/460, 448/448, 416/416, 163/163, 14/14, 1/1, 0, 0). Same reason: an associator over identity elements is trivial, so on sparse leaves it carries no signal the holonomy did not already carry.

**This sharpens what the associator IS.** It is a genuine richness/curvature read (F1310's 3-index object stands), but it is **not** an order read: non-associativity tells you *how the object is structured*, not *in what sequence it was walked*. Those are different questions, and conflating them would have been an easy and expensive mistake. `[This is a NEGATIVE result and it is load-bearing — it closes an obvious-looking avenue.]`

## Q-C — the repair lifts unchanged
**v3cO (rotate-by-index, Class-C reorient) scores 0 collisions at 𝕆**, matching the carrier-independent `v3d` content-address bound exactly, just as it did at ℍ (F1315). Position-tagging the *values* (v3aO) again improves a lot (1502→103) and again **still leaks** (1/23 at the gate). Both the defect and the repair are properties of **support geometry**, and support geometry does not care which rung you are on.

```
   THE ONE-LINE LAW (measured at BOTH rungs)
   ────────────────────────────────────────────────────────────────
   defect:  per-slot fold + identity element + disjoint support  ->  order-blind
   repair:  make the support LOCATION position-dependent (Class-C)  ->  order-exact
   neither depends on the rung; the algebra's richness is orthogonal.
```

## Why this is genome machinery, not a siona trick — the srmech ask
The user's reading is supported by the measurement: an **order-integrity check for a coupled strand** is (a) needed at **every** rung, (b) fixed by the **same** one-line reorient at every rung, and (c) currently **absent** from the package — `genome_fiber_holonomy` / `genome_octonion_holonomy` ship as the *fold*, and both are order-blind on sparse strands, which is the regime srmech's own genome is built for. Any downstream consumer that reaches for the shipped holonomy to detect a reorder **gets a false pass on sparse data with no error**. Written up as **U18** in `UPSTREAM_NOTES.md` (**HELD**, not filed, per the standing hold pending the worktree deliverables preview).

The biology reading is the same object: a strand whose blocks can be read back in the wrong order without the reader noticing is a strand with no **sequence integrity**. Biology does not solve that with a richer alphabet; it solves it positionally. `[SPECULATIVE as biology; DEMONSTRABLE as the measured structure.]`

## Honest scope
- `[DEMONSTRABLE]`: every number above, at both rungs, on the shipped ops.
- `[SPECULATIVE / UNSWEPT]`: the `stride × leaf_dim` degeneracy sweep is **still not done** (carried from F1315) — some (stride, leaf_dim) pairs could rotate a support set onto itself. This is the last gate before wiring in, at either rung.
- Not tested: n_leaves ≫ 4, non-uniform leaf densities, or a strand mixing rungs (a v19 body may legally carry `0x51`/`0x38`/`0x39` turns together — an order check across a **mixed-carrier** strand is unexamined and is the natural next question).
- The associator negative is scoped to **order** detection on **sparse** leaves. It says nothing against the associator as a curvature/richness read (F1310/F1311 stand).

## Verdict / next
Both the defect and the repair are **carrier-independent across ℝ/ℂ/ℍ/𝕆**, and the 𝕆-only associator is **not** an order read. The repair (`Class-C reorient ∘ shipped fold`) is one line and works at every rung — which is exactly why it should be **upstream genome machinery** rather than siona-local. **NEXT:** the stride×leaf_dim degeneracy sweep (the last gate), then the mixed-carrier strand question.

Composes **F1315** (the ℍ-rung result this lifts — *carrier-independence was its open generalisation*), **F1314** (the false shadow), **F1310/F1311** (the 𝕆 associator as the 3-index object — *sharpened here: richness read, NOT order read*), **F1307/F1309** (the Q₈ substrate), **F1272/F1301** (the responsion slot), `[[stance_bit_exact_is_the_abelian_shadow_of_non_abelian_structure]]`, `[[feedback_stay_rbs_hdc_sparse_never_dense]]`, `[[feedback_computational_provenance_discipline]]`. Generating code: `R-RBS-LM-TOCV3OCT_*.py` (exit 0).

**→ generalises F1315** — the Class-C repair is not a ℍ-rung trick; it lifts to 𝕆 unchanged, and the defect it fixes is identity-and-support driven, so it holds at every rung of the tower.

**→ extended by F1317, and INDEPENDENTLY CONFIRMED by standard math.** F1317 measures that the abelian shadow ladder NESTS (ℍ→ℤ₂², 𝕆→ℤ₂³, and `(𝕆-shadow)&3 == (ℍ-shadow)`, 0 violations each), so a compounded fibration carrier already exists in the shipped encoding — the fibration is chosen by the READ MASK WIDTH. Crucially it also locates F1316's associator negative in the standing theory: MFO §VIII.31.19 §3 already fenced, as standard math, that **turns need a GROUP and `S⁷` is a non-associative Moufang loop, so turn-composability tops out at ℍ while ADDRESSING goes higher — two different ceilings.** F1316 measured that wall empirically (the associator adds zero order information) without knowing it was predicted structurally. Same wall from two directions.
