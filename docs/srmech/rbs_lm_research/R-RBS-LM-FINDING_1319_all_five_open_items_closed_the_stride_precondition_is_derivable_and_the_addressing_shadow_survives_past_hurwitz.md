# F1319 — **all five open items closed; the issue can be written.** The stride×leaf_dim gate is not a sweep-and-hope: it is a **derivable precondition** — `leaf_dim / gcd(stride, leaf_dim) ≥ n_leaves` — which **predicted pass/fail on 40/40 cases with ZERO mispredictions**. The repair scales (n=8, 40 319 perms, **0 collisions**; non-uniform densities **0**). The fiber bit can key on **content OR slot** — both work, but they are **different objects**. The Q₈ fold **correctly refuses** octonion values while the **𝕆 fold is the safe cross-rung read** (Q₈'s alphabet is a strict subset). And the headline: the **ℤ₂ⁿ addressing shadow SURVIVES PAST THE HURWITZ WALL** — exact at 𝕊 (dim 16, **0/256**) and dim 32 (**0/1024**), where *division* is already dead.

**User (2026-07-25):** *"research remaining open items before gh issue please."* All measured on srmech 0.9.0rc336, exact `Q` where algebra is involved, no float / no `abs()` / no numpy / no RNG.

## A — the stride×leaf_dim gate: DERIVED, not swept `[DEMONSTRABLE]`
The v3c reorient rotates turn *t* by `stride·t mod leaf_dim`. It can only distinguish leaves whose rotations land on **distinct offsets**, so the requirement is that `stride·t (mod leaf_dim)` be distinct for `t < n_leaves` — i.e. the additive order of `stride` in ℤ_leaf_dim must be at least `n_leaves`:

> **PRECONDITION: `leaf_dim / gcd(stride, leaf_dim) ≥ n_leaves`**

**Verified against measurement on 40 (leaf_dim, stride) pairs — 40/40 correct, 0 mispredictions.** Representative rows (n_leaves = 4):

| leaf_dim | stride | distinct offsets | predicted safe | measured collisions |
|---|---|---|---|---|
| 128 | 0 | 1 | ✗ | 11 |
| 128 | 1 | 128 | ✓ | **0** |
| 128 | 3 | 128 | ✓ | **0** |
| 128 | 4 | 32 | ✓ | **0** |
| 128 | 32 | 4 | ✓ | **0** |
| 128 | **64** | **2** | ✗ | **3** |
| 64 | 32 | 2 | ✗ | 3 |
| 32 | 16 | 2 | ✗ | 3 |

So the degenerate cases are exactly the predicted ones: `stride ≡ 0` (no rotation → reduces to the v2 false shadow) and `gcd` too large (offsets recycle before all leaves are placed). **This converts the last gate from an empirical hope into a one-line assertion a caller can check** — which is precisely what makes it shippable.

## B — scale `[DEMONSTRABLE]`
With `leaf_dim=128, stride=37` (gcd = 1 → order 128, safe to n_leaves ≤ 128):
- `n_leaves=6`, nz=1: **0 collisions / 719 perms**
- `n_leaves=8`, nz=1: **0 collisions / 40 319 perms**
- **non-uniform** densities `[1,3,17,64,1,2]`, n=6: **0 collisions**

The F1315/F1316 result was n=4 and uniform; it holds at 8 leaves, full permutation coverage, and mixed sparsity.

## C — content-keyed vs slot-keyed fiber `[DEMONSTRABLE — both work, and they differ]`
Both round-trip exactly and both vary. The distinction is structural, not quality:

| keying | round-trips | equal shadow ⇒ equal sign | what it is |
|---|---|---|---|
| **slot-keyed** `sign(the_one, i)` | ✓ | **False** | **position-bearing** — the same content at two positions can take different seats |
| **content-keyed** `sign(the_one, shadow[i])` | ✓ | **True** | the fiber becomes a **function of the shadow** — position-blind, only 2⁸ distinct lifts |

**Neither is "the" answer** — they are different constructors. Content-keyed makes the lift *reproducible from the shadow alone* (attractive for a TOC record); slot-keyed carries position (attractive for order-integrity). A design must **choose deliberately and say which**, because they are not interchangeable.

## D — mixed-carrier strands `[DEMONSTRABLE]`
A v19 body may legally carry `0x51`/`0x38`/`0x39` turns together, so a cross-rung order read is a real question. Measured:
- **Q₈ fold on octonion values → correctly RAISES**: `ValueError: genome_fiber_holonomy: byte 12 is not a Q₈ element (0..7)`. **The guard exists.** Good.
- **𝕆 fold on mixed (Q₈ + octonion) turns → accepts, no error** — and that is *correct*, because Q₈'s alphabet `0..7` is a strict **subset** of 𝕆's `0..15`.

> **The 𝕆 fold is the safe cross-rung read.** This is the compounded-carrier property (F1317) showing up operationally: read the mixed strand at the widest rung and every narrower rung's symbols are already legal there.

## E — the addressing shadow SURVIVES PAST THE HURWITZ WALL `[DEMONSTRABLE — the headline]`
```
   dim  4 (H): basis(a·b) == basis(a) XOR basis(b)   0/16   violations
   dim  8 (O):                                        0/64   violations
   dim 16 (S):                                        0/256  violations   <-- past Hurwitz
   dim 32    :                                        0/1024 violations
```
At 𝕊 (dim 16) **division is dead** — zero divisors exist, the algebra is no longer a division algebra (F451/F424). **The ℤ₂ⁿ addressing shadow does not care.** It holds exactly, and keeps holding at dim 32.

**This is F1274/F1275 confirmed one level up:** *addressing needs only that basis products be a **signed permutation** (`e_i·e_j = ±e_k`) — never the division property.* Zero divisors are built from **sums** of basis elements, never a single basis pair, so the wall that destroys composition leaves addressing untouched. Verified independently here: every basis product is a single signed unit at dims 8/16/32.

**Consequence for the compounded carrier (F1317):** the shadow ladder is **not** Hurwitz-bounded. ℤ₂ ⊂ ℤ₂² ⊂ ℤ₂³ ⊂ **ℤ₂⁴ ⊂ ℤ₂⁵ …** — the *addressing* tower continues where the *algebra* tower stops. Two ceilings become three, cleanly separated:

```
   ADDRESSING (Z2^n shadow)   : unbounded -- exact at dim 32, no reason to stop  [measured]
   COMPOSITION (division)     : stops at O (dim 8) -- the Hurwitz wall           [F451/F424]
   TURNS (group/ordered fold) : stops at H (dim 4) -- S^7 is not a group         [MFO VIII.31.19 s3, F1316]
```

## Honest scope
- `[DEMONSTRABLE]`: every number above; exhaustive over the stated product tables and permutation sets, not sampled.
- `[SPECULATIVE]`: that the ℤ₂ⁿ ladder continues *forever* — measured only to dim 32. It is standard that CD basis products stay a signed permutation at every rung, so continuation is expected, but I measured 4/8/16/32 and assert only those.
- The stride precondition is derived + verified at n_leaves = 4 across 40 pairs and separately at n=6/8 for one safe stride; a full (stride × leaf_dim × n_leaves) cube was **not** enumerated.
- Content-keyed vs slot-keyed: characterised structurally, **not** ranked. Which to use is a design decision, not a measurement.

## Verdict
**Nothing is left dangling.** The Class-C reorient responsion has a checkable precondition, scales, and works at both rungs; the cross-rung read has a safe direction and a working guard; the fiber bit has two well-characterised keyings; and the addressing shadow outlives the Hurwitz wall — which strengthens the compounded-carrier case rather than bounding it. **The srmech issue can now be written** with U18 (order-integrity read + the precondition), the compounded-carrier design question, and the two silent-corruption bugs (U5/U6).

Composes **F1315** (the ℍ repair — *its stride gate is closed here*), **F1316** (the 𝕆 lift + carrier-independence — *its mixed-carrier and scale caveats are closed here*), **F1317** (the compounded carrier — *extended past Hurwitz*), **F1318** (the constructor — *its content-keying question is answered here*), **F1274/F1275** (addressing needs no division — *confirmed at 𝕊 and dim 32*), **F451/F424** (the Hurwitz wall), MFO **§VIII.31.19 §3** (the turn ceiling). Generating code: `R-RBS-LM-OPENITEMS_*.py` (exit 0).
**→ the ceiling ladder gets its REASON in F1322** — a fourth level sits between addressing and composition: the **group-extension/cocycle** level stops at **ℍ**, because the 2-cocycle identity fails on exactly the **168/512** 𝕆 triples that leave a single ℍ subalgebra (= the associator-defect set, set-equal not just count-equal).
