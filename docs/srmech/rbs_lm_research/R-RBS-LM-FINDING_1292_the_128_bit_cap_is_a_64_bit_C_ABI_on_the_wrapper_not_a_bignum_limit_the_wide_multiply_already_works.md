# F1292 — **the 128-bit "gap" is not a bignum limit — the wide multiply already works.** `cyclic.mod_mul`'s uint64 cap is a **fixed-64-bit C ABI** on the convenience wrapper, not a capacity limit: `_native.bigint_mul_c` multiplies at **any** width (verified on a 133-bit result), and for PCG64's `mod 2¹²⁸` the reduce is just a **bitmask**. The full 128-bit LCG step runs today from shipped ops — `(bigint_mul_c(state, mult) + inc) & (2¹²⁸−1)`, verified equal to raw arithmetic. **This corrects F1291/§110, which called it a "capacity gap": there is no math gap.**

**User (2026-07-21):** *"check why our srmech bignum can't accommodate the 128 bit multiply."*

The right question — because the assumption underneath my §110 ("the capacity exists via `bigint_mul_c`") was **untested when I wrote it.** Testing it flipped the finding.

## Why `cyclic.mod_mul` rejects 128-bit — the actual reason
`mod_mul` dispatches to the native symbol `srmech_mod_mul`, whose ctypes binding is:
```
srmech_mod_mul(c_uint64 a, c_uint64 b, c_uint64 n, c_uint64* out)
```
A **fixed 64-bit ABI.** Passing a value `> 2⁶⁴−1` would silently truncate at the ctypes boundary, so the Python guard `_ensure_uint64` exists to turn that truncation into a **loud error**. **The guard is correct** — it is protecting a genuinely 64-bit C entry point. The cap is a property of *that one wrapper*, not of srmech's arithmetic.

## The bignum has no such limit — measured
```python
from srmech.amsc import _native
a = (1 << 70) + 12345                       # 71 bits
_native.bigint_mul_c(a, 6364136223846793005) == a * 6364136223846793005   # True, 133-bit result
```
`bigint_mul_c` is `srmech_bigint_mul` (Karatsuba arena above rc168) — **arbitrary precision, raw product, no reduce.** It handles the 128-bit multiply directly.

## So the 128-bit modular step is already expressible — verified end to end
PCG64's modulus is `2¹²⁸`, which makes the reduce a **mask**, not a division:
```python
state1 = (_native.bigint_mul_c(state, mult) + inc) & ((1 << 128) - 1)
state1 == (state * mult + inc) % (1 << 128)      # True
```
The prototype's `step()` now runs through this path. **No new op, no numpy, no float** — the wide multiply srmech ships, plus a Class-K bitmask.

## What F1291 / §110 got wrong, and the corrected ask
F1291 listed gap (1) as *"srmech needs a 128-bit-capable modular multiply — the capacity exists but the surface is bounded."* **That framed an ergonomic wrapper as a capacity gap.** The capacity is not just present, it is *directly usable*. Corrected:

| | F1291 (wrong) | F1292 (correct) |
|---|---|---|
| gap 1 | "128-bit modular multiply is missing; capacity exists but unreachable" | **no math gap** — `bigint_mul_c` + mask does it today. A `cyclic.mod_mul_wide` wrapper is a **convenience**, not a blocker |
| gap 2 | modular family not chain-registered | **unchanged and still valid** — chain/TOML can't reach `mod_mul`/`mod_add`/`mod_pow` (only 15 ops exposed) |

**Gap 2 is now the only real srmech ask** for a *declared* PCG64 cascade. For a *hand-composed* one, there is no ask at all — the ops exist and compose today.

## Consequence for Tier 3
Better than F1291 said. A bit-exact PCG64 needs **no new srmech arithmetic whatsoever** — only the two gates that are about *correctness*, not capability:
- **attested constants** (multiplier + XSL-RR schedule — extract, don't recall);
- **a reference stream** to diff against (numpy won't install here; `default_rng` also needs SeedSequence reproduced).

So the engineering is done; what remains is verification against an attested source — which is the honest boundary F1291 drew, now with the "we need a new op" caveat removed.

## The lesson, stated against myself
I wrote "the capacity exists" in §110 **without running `bigint_mul_c` on a 128-bit input.** It was a plausible inference that happened to be *more* pessimistic than the truth — the user's "check why" is exactly the instinct that catches an untested assumption, in whichever direction it errs. `[[feedback_introspect_srmech_before_python_dispatch]]`: introspect the op, don't infer its limits.

Composes **F1291** (corrected here — gap 1 downgraded from blocker to convenience), **F1290** (Tier 3), `[[feedback_introspect_srmech_before_python_dispatch]]`, UPSTREAM_NOTES §110 (amended).
