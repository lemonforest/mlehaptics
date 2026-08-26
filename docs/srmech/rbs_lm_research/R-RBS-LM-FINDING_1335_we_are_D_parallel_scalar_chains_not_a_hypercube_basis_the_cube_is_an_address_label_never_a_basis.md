# F1335 — **we are NOT a hypercube-basis object. We are `D` parallel scalar chains, folded sequentially, and the cube is used as an ADDRESS LABEL — never as a BASIS.** The decisive test is **slot-permutation equivariance**: if permuting the slots of every input merely permutes the output, the operation has **no cross-slot structure**. Measured on rc349: `genome_fiber_holonomy`, `klein4_bind` and `klein4_bundle` are **all equivariant**, while a Walsh–Hadamard butterfly (positive control) is **not**. So each slot holds a **point** of the cube (an index + a sign); the carrier does **not** hold a **function on** the cube. **No slot ever sees another slot.** We have been saying "hypercube" about an addressing scheme while every operation is scalar-and-sequential.

**User (2026-07-28):** *"look again to see if we are using scalar based loudness+phase or if we are doing hypercube basis."* — **Scalar. Measured, not argued.**

## 1 — the test and the result `[DEMONSTRABLE]`
```
  genome_fiber_holonomy : permuting every turn's slots just PERMUTES the output   -> slot-wise
  klein4_bind           : equivariant                                             -> slot-wise
  klein4_bundle         : equivariant                                             -> slot-wise
  Walsh-Hadamard        : NOT equivariant -- it genuinely mixes                    -> cube-basis
```
The control matters, because "everything is equivariant" would otherwise be consistent with the test being broken:
```
  src                 [2, 1, 0, 0, 3, 3, 1, 2]
  WHT(src)            [12, 0, 6, 2, -6, 2, 0, 0]
  WHT(permuted src)   [12, -6, 2, 0, -4, 2, -2, -4]     a different mixture, not a relabel
```

## 2 — what we actually have
- **Each slot holds a POINT of the cube** — an index plus a sign, 2 or 3 or 4 bits.
- The carrier does **not** hold a **FUNCTION ON** a cube (2ⁿ coefficients read together).
- The fold is `acc ← acc · turn`, **one turn at a time**, `D` times in parallel — **order-locked and serial**.
- The cube enters only as `basis(a·b) = basis(a) ⊕ basis(b)` — **an address label.**

> **We have been describing an addressing scheme as a basis.** Those are different objects, and the difference is exactly one measurable property.

## 3 — why this is the lane that matters
Our own ceiling work (F1319, now shipped as constants) says the **index lane is exact at every dimension probed** — `CD_ADDRESS_VERIFIED_DIM = 64` — while composition stops at 8 and ordered turns at 4. **The one lane that scales without limit is precisely the one we are only using as a label.** A cube basis would put work *into* that lane instead of alongside it.

And the transform that makes it a basis is the cheapest exact spectrum available to a float-free package: Walsh–Hadamard characters are **±1**, so it is **exact in whole numbers with no roots of unity** — where an ordinary length-*n* transform is **not** exact in ℚ (it needs `ℚ(ζₙ)`, degree `φ(n)`; F1331 §4). Filed: gh **#1530 §J** (the missing op) and gh **#1535** (the carrier-shape ask).

## 4 — and it re-reads the question that started this
F1332 read the `1 + n` split as *one loudness, n phases*. F1333/F1334 then closed the **resonator** reading of that — structurally, via conjugate pairing. This finding says something different and about **us**: even setting the physics aside, **our carrier is not holding one magnitude over n phases either.** It holds `D` separate little objects, each with its own index and its own sign, that never interact.

So the honest position on the whole thread: **the `1+n` we measured (F1328) is a property of the algebra at one slot. It is not a property of the carrier, which is `D` copies of that slot with nothing between them.**

## Honest scope
- `[DEMONSTRABLE]`: §1, on rc349 — four ops, one decisive property, with a positive control.
- **Not a defect.** Slot-wise operations are correct, native-dispatched and fast. **The issue is descriptive**, and it is ours: we said "hypercube" about parallel scalar chains.
- **Not established**: that a cube-basis carrier would do better at anything we care about. This finding says what we **are**, not that the alternative is superior — adopting it needs a measured win, and none exists yet.
- I probed four ops, not the whole 511-op surface. Other ops may mix slots; **the claim is about the ones tested**, which are the ones our genome work actually runs on.

Composes **F1328/F1329** (the `1+n` and the ceilings — *the index lane is the unbounded one*), **F1331 §4** (a length-*n* transform is not exact in ℚ; WHT is), **F1332** (*its "one loudness" reading does not hold at carrier level either*), **F1333/F1334** (the resonator reading, closed structurally). Generating code: `R-RBS-LM-CUBEPROBE_*.py` (exit 0). Filed: gh #1530 §J, gh #1535; and the driven-dissipative hand-off as gh #1534.
