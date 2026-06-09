# Finding 712 — recursive quad-streams give a 4^k address space (clean) — but only the first quad is chirality; the rest is radix

**Script:** `R-RBS-LM-QUADTREE_recursive_quad_streams_4pow_k_address_space_chirality_vs_radix.py`
**Status:** VERIFIED (srmech 0.7.5rc28)
**User direction:** *"and also no reason we can't do quad quad quad streams with larger address space, right or no?"*

## Yes — for address space (and the math is exact)

Nesting the Klein-4 four-sector dispatch k deep addresses **4^k blocks**, each ≤256 (the native dense bound):

| depth | nodes | bits | |
|---|---|---|---|
| 1 (quad) | 4 × 256 = 1,024 | 2¹⁰ | the biaxial "+" shelf (F711) |
| 2 (quad quad) | 4,096 | 2¹² | |
| **3 (quad quad quad)** | **16,384** | **2¹⁴** | |
| k | 4^k × 256 | 2^(2k+8) | |

The address is a **base-4 (quaternary) number** — 2k address bits + 8 leaf bits — and it **round-trips exactly** (verified:
idx 12345 → sector-path `(3,0,0)` + leaf-slot 57 → back to 12345; idx 1,000,000 → depth 11, exact). The bounding is exact +
content-addressable (F613). **So there is no reason we can't** — it is just hierarchical 4-ary addressing.

## But be precise (the no-overclaim discipline you just enforced): chirality is ONE quad; the rest is radix

- **Level 0 — the first quad IS chirality.** Klein-4 V4 = the 4 sectors (γ₅ × iω₇) = the substrate's 4-way (F130) = the
  native `parallel_sector_dispatch` (CAP=4). Real, on-thesis chirality.
- **Levels 1… — the further quads are a 4-ary RADIX addressing tree** (a quadtree over ≤256 blocks). Each level is a
  **base-4 digit** of the block address — **not** another physical chirality axis. The substrate stays **bi-axial 4-way**
  (F130); nesting adds address *bits*, not chirality *axes*.

So "quad quad quad" = (1 chirality quad) × (k−1 radix quads) × (256 dense leaf). It would be an overclaim to call the deeper
nesting "more chirality" — it's address space. (This is the *same* distinction as F708: don't dress an addressing/impl
structure up as substrate meaning.)

## How it composes (the whole storage picture, now)

**Helix (F711) × quad-tree (F712) × Klein-4 (F710/F130) × 256-leaf (F708):**
- the **helix** winds turns on the outside → *unbounded history* (RAM-bounded, disk-paged, bounding-tracked);
- each turn is a **quad-tree** of ≤256 leaves → *4^k address space* (base-4 radix; this IS F690's bucketed path made
  recursive);
- the **leaf** carries the bi-axial **Klein-4** chirality (the base quad, the native CAP=4 dispatch);
- the leaf is **≤256 = 2⁸ = one byte** (the native dense-eig bound), and D = 2^n (F222).

Result: a store that is **unbounded in history, 4^k-addressable, full-chirality per leaf, and never quantizes** (F49/F50) —
it bounds RAM and the dense block, not the data.

**Composes:** F711 (helix) · F690 (bucketed path = this tree) · F130/F132 (Klein-4 chirality) · F710 (native quad-stream,
CAP=4) · F222 (D=2^n) · F708/F640 (256=2⁸, no-overclaim) · F49/F50 (no quantization). srmech 0.7.5rc28. Reference scaffold;
held open (F394).
