# Native C trig cascade — design + validation (v0.7.0rc43)

**2026-06-05.** The first behavioural step of the C-transpile triality arc
(rc42→rc46, `continuous_math_as_14_class_cascade.md` §"C-transpile triality
coherence"): `c/src/srmech_trig.c` makes the **executable** compute trig via the
Class-N cascade, not libm. This note records the design + the validated
generating code (computational-provenance discipline,
`[[feedback_computational_provenance_discipline]]`).

## The discipline that shaped the design (user, 2026-06-05)

> "should prefer ints over float always for cyclic algebra"

The first C draft used float Cody–Waite reduction (`k = llround(x·2/π)`), doing
the **cyclic** step (mod π/2) in floating point — wrong. The corrected design
does the cyclic reduction in **pure integers**, mirroring the Python
`rational._principal_angle_anchor` (exact `x.as_integer_ratio()` reduction);
float appears only at the final rational→double projection.

## Algorithm (all-integer except the final projection)

1. **x → exact integer** `±M·2^E` from the IEEE-754 bit pattern (`memcpy` to
   `uint64`, mask exp/frac fields — no `frexp`, no libm).
2. **octant reduction mod π/2 in integers.** `prod = M · TWO_OVER_PI_Q64`
   (portable 64×64→128 wide-multiply, no `__int128`/`_umul128`) = `|x|·2/π`
   scaled. Shift to `V = |x|·2/π·2^61`; the octant `k = round(V/2^61)` and the
   centred fraction `frac = V − k·2^61 ∈ [−2^60, 2^60]` are exact integers.
   `r = frac · (π/2)` via one Q61 `fxmul` → `|r| ≤ π/4`.
3. **Q61 Taylor** (Class N): `sin_core`/`cos_core` (alternating series, ~10
   terms) on the integer remainder; `octant mod 4` selects sin/cos/−sin/−cos.
4. **project** `(double)sum / 2^61` — the one float step.

`atan`/`atan2`: three-band reduction (|m|≤√2−1 direct, ≥√2+1 → π/2−atan(1/m),
middle → π/4+atan((m−1)/(m+1))) + Q61 atan Taylor; π/2, π/4 from the cascade.

## Cascade constants (derived from `rational._pi_rational(50)`, no libm)

```
TWO_OVER_PI_Q64 = round((2/π)·2^64) = 11743562013128004906   (< 2^64)
HALF_PI_Q61     = round((π/2)·2^61) = 3622009729038561421
FX_ONE          = 2^61              = 2305843009213693952
```
2π·2^61 overflows int64 — hence the [−π/4, π/4] + quadrant design (cannot Taylor
on [−π, π] in Q61).

## Validation (generating code — re-runnable)

The integer reduction + Q61 multiply were prototyped in Python and checked
bit-for-bit against the reduction, then the full `srmech_trig.c` was checked
against libm:

- **Python prototype** (`reduce_simple` — one wide-mul + one `fxmul`, the exact
  C shape): `sin maxerr 1.11e-16` vs libm across 5000+ random angles in
  [−1000, 1000] + edge cases (0, π/2, π, 2π, tiny, negative).
- **C, compiled vs libm** (`srmech_sin/cos/atan/atan2`): **sin 5.26e-19,
  cos 8.13e-20, atan 2.22e-16, atan2 0.0 (bit-exact)**; 200k-angle sin sweep in
  [−1000, 1000] = **1.11e-16**. (`srmech_trig.c` is *better* than the last libm
  bit for sin/cos because the Q61 series carries guard bits.)

`tests/test_native_trig_rc43.py` exercises the C symbols via ctypes;
`tests/test_kepler_parity.py` covers the native kepler path that now routes
through the cascade.

## Domain bound (honest)

Machine-ε for `|x| < 2^55` (the 2-word product keeps the octant bits exact);
beyond that the reduction returns `false` (out of any physical-angle domain —
kepler/kuramoto angles are O(1)–O(10²)). Tiny `|x|` projects to `r ≈ x`
directly (sin x = x to double precision), no special-case needed.

## ISA learning (for the ISA tracker, per user 2026-06-05)

The native-substrate trig is **integer-only** (Q61 fixed-point Taylor + integer
Payne-Hanek-lite reduction): a substrate that has only an integer ALU + a
64×64→128 multiply can compute machine-ε trig with **no FPU transcendental and
no `__int128`** — the "continuous" trig is literally a Class-N rational the ALU
evaluates, projected to float once. Candidate comment for the lean-ISA tracker:
the 7th-primitive / native-compute-surface discussion (F305/F306, #784 family).

### rc45/rc46 extension — the SAME integer-only ISA covers sqrt + exp + log

The closeout (rc45 `srmech_sqrt.c`, rc46 `srmech_explog.c`) shows the lean-ISA
result generalises past trig to the whole §22 transcendental set:

- **sqrt** — a two-limb 128-bit *integer* restoring isqrt on a bit-extracted
  radicand (`x = M·2^e`), projected by an IEEE-exponent-field power-of-two. No
  FPU `sqrt`, no `__int128`, no division.
- **exp** — Q61 integer exp-Taylor on the reduced `r` (`x = n·ln2 + r`), scaled
  by `2^n` via the exponent field. The only float ops are the `n`-pick and the
  two-word `ln2` recombine (the projection).
- **log** — Q61 integer atanh series on `(m−1)/(m+1)` after a *bit-pattern*
  `m·2^e` split (the decomposition is integer, not `frexp`).

**ISA shopping list (full §22 transcendental coverage):** an integer ALU, a
`64×64→128` widening multiply (schoolbook from 32-bit parts if absent), a
count-leading-zeros (or a bounded normalise loop), and IEEE-754 bit access
(`memcpy`, no `ldexp`/`frexp`/`scalbn`). That set computes machine-ε
`sin/cos/atan/atan2/sqrt/exp/log` with **zero FPU transcendental and zero
`__int128`**. The pin-slot / kuramoto / Jacobi paths on a native install now
prove it end-to-end — the whole "continuous math" layer is a Class-N rational
the integer ALU evaluates, projected to float exactly once at the boundary.
Strong candidate for the lean-ISA / native-compute-surface tracker (#784 family,
F305/F306): the 7th-primitive substrate needs no transcendental FPU at all.
