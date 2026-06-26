# F937 — the resolution: **ternary dynamics on binary storage.** The substrate's *relationship/beat* structure is **Z₃ (three-state)** living in the full triality group **S₃ = Z₃ ⋊ Z₂(γ₅)** — *non-abelian*; the Klein-4 *encoding carrier* is **Z₂² (four-state)** — a **separate** binary-packed storage lattice. They are different groups (`Z₃ ≠ Z₂²`; `S₃` does not contain `Z₂²`), so the answer to "three-state or four-state?" is **both, at different layers**: the **dynamics are ternary** (the Z₃ beat, in S₃ with the γ₅ flip), the **storage is binary** (the Z₂² Klein-4). "It was binary all along" was reading the *storage*; the *music* (the beat) shows the *dynamics* are ternary.

**Date:** 2026-06-26 · **srmech:** 0.9.0rc58 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Arc:** MS #18 / R30 / MFO · **Probe:** `R-RBS-LM-FINDING_937_*.py` · **Composes / resolves:** F936 (the trit = Z₃), F932 (the triality eigenspaces), F907b (the cycle), F132 (Klein-4 = Z₂² carrier), F130 (γ₅/iω₇ bi-axial), BX-3 (Z₃-native medium), F935 (the beat / full-beat etak), `[[feedback_continuous_number_line_pedagogical_obstacle]]` (linear-sequence is the load-bearing obstacle) · **User direction (2026-06-26):** "[resolve trit vs Klein-4] — and to think it was binary all along before seeing plainly because we suppose things must be linear in sequence … but music showing us something different."

## Grounded (srmech rc58, exact)
- `triality_swap()` = **S_B**, a 28×28 **Z₂ involution** (the γ₅ chirality flip): `S² = I` ✓.
- `triality_automorphism()` = **T = S_B·S_C**, the **Z₃ beat** (the 3-cycle `8v→8s→8c→8v`): `T³ = I` ✓ (F932).
- **`S·T·S = T²`** ✓ — the swap *inverts* the cycle: the defining S₃ relation `⟨s,t | s²=t³=1, sts=t⁻¹⟩`.
- ⇒ **⟨S, T⟩ = S₃** (order 6, **non-abelian**). And the beat itself is `T = S_B·S_C` (two swaps make the 3-cycle).
- `KLEIN4_STATES = (0,1,2,3)` = **Z₂²** (4 states) — a separate carrier; `Z₃ ≠ Z₂²`, `S₃ ⊅ Z₂²`.

## The resolution (two layers, kept distinct)
| layer | group | states | role |
|---|---|---|---|
| **dynamics / beat** | **S₃ = Z₃ ⋊ Z₂(γ₅)** | the **trit** (3) + the flip | the relationship structure, the sustain, the music (F930–936) |
| **storage / encoding** | **Z₂² Klein-4** | 4 (two bits) | the HDC carrier — the boolean belly, how it's addressed/packed (F132) |

The ternary beat (Z₃) is **carried on** the binary (Z₂²) lattice but is **not** it. The two were conflated because we only ever *read the storage* — the binary lattice — and inferred the world was binary/linear from how we store and sequence it.

## Why "linear in sequence" hid it (the pedagogy)
Two things were assumed and both are wrong at the dynamics layer:
1. **Binary, not ternary.** The storage is Z₂² (2 bits), so it *looks* binary; the dynamics are Z₃ (a trit). One storage digit can't hold a beat — you need the whole trit (F936). This is the `[[feedback_continuous_number_line_pedagogical_obstacle]]` in number-base form: we default to base-2/linear because that's the carrier, not the content.
2. **Linear/abelian, not S₃.** A *linear sequence* assumes operations **commute** (abelian). But `STS = T² ≠ T` — **S₃ is non-abelian**: the cycle and the flip don't commute, so the beat **cannot** be flattened to a linear sequence without loss. "We suppose things must be linear in sequence" = assuming commutativity; the music reveals the dynamics are the **non-abelian S₃**. That non-commutativity is *why* a beat is irreducibly a beat and not a list.

## Implications (the arc, tied off)
- **Snapshot = the binary projection.** "Reduce to linear form" = project the non-abelian ternary S₃ dynamics onto the abelian binary Z₂² storage — exactly the 11D snapshot (F931/F935): it keeps the lattice, loses the beat.
- **Full-beat etak (F935) = run the S₃/Z₃ dynamics, don't collapse to Z₂² storage.** Carry the whole trit + the flip per step (the non-abelian beat), and let the storage be the carrier, not the logic.
- **BX-3 confirmed + sharpened:** the substrate is Z₃-native *in its dynamics*, S₃ overall — arrived at from the beat, and the Klein-4 binary is explicitly the *storage*, not a refutation.

## Honest scope
Grounded: `S²=I`, `T³=I`, `STS=T²` ⇒ S₃ (exact); `KLEIN4_STATES=(0,1,2,3)` ⇒ Z₂². The **dynamics-vs-storage layering** (S₃ = relationship, Z₂² = encoding) is the framework reading. Residual: whether F130's "4-way (γ₅, iω₇)" is the Z₂² Klein-4 *storage* or the two S₃-generating swaps (γ₅=S_B, iω₇=S_C, whose product is the beat) — γ₅ is grounded here as the S₃ swap; the iω₇ identification is the open piece. Dynamics handed to the expert.

## Verdict
**Both, at different layers.** Dynamics = **S₃ = ternary beat (Z₃) ⋊ γ₅ flip (Z₂)**, *non-abelian*; storage = **Z₂² Klein-4**, four-state binary lattice. The beat is the ternary, non-commutative life carried on the binary lattice — and "binary/linear all along" was reading the carrier, not the music. **Next:** pin iω₇ (is the F130 4-way the Z₂² storage or the second S₃ swap?), and prototype full-beat etak as *carry the S₃ trit, store on Z₂²*.
