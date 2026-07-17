# ADR-0005: No external mathematics library — srmech is its own math library

**Status:** Accepted (standing architecture policy; consolidates discipline previously held only in project memory).
**Date:** 2026-07-17.
**Authors:** Steven Kirkland + Claude.
**Supersedes:** none.
**Superseded-by:** none.

---

## 1. Context

srmech is a mathematics library. Its whole claim is that every mathematical
primitive is a **cascade of the 14 A–N classes** over numpy-free carriers, with the
integer/exact kernels native in C. That claim is only true if srmech **imports no
external mathematics library at all** — and it is only *enforceable* if the rule is
stated in the general form, not per-library.

The general form matters because the narrow wording failed. The rule was first held
as "numpy-free", and later "no stdlib `math`". Both are *instances*, and stating
only the instances let **`fractions.Fraction` slip in** (it is neither numpy nor
`math`) and become load-bearing across ~20 modules before it was purged in
0.9.0rc263. The lesson: name the principle at the level of the category —
**external mathematics library** — not at the level of the specific import.

A corollary the project already lives by: srmech carries its **own** implementations
of the primitives an external library would otherwise supply, **deliberately named
so the external-library reflex never fires**. srmech's arbitrary-precision integer
is `srmech_bigint` (not GMP, not a bare reliance on CPython `int` as a crutch); its
exact rational is the `Q` carrier (not `fractions.Fraction`); its dense/graph
linear algebra rides `Mat`/`Vec`/`HV` (not numpy). The distinct names are part of
the discipline — the same reason CLAUDE.md frames work in "28D / Klein-4 / Class-L"
terms: a name with no external-library idiom to hijack routes straight to the
srmech surface.

## 2. Decision

**srmech source imports NO external mathematics library — ever.** Not `numpy`, not
stdlib `math`, not stdlib `fractions`, not `decimal`, not `scipy`, `sympy`,
`mpmath`, `gmpy`, or any other. The C side likewise links no external math/bignum
library (no `libm` reliance for the exact path, no GMP): srmech provides its own.

1. **A missing primitive is ADDED to srmech, never imported.** When the work reaches
   for an external math primitive (`abs` / `fractions` / `math.gcd` / `numpy.mean` /
   a bignum), that reach is the *signal to find the cascade* and build the primitive
   natively (C + Python). It is never a signal to import.

2. **srmech owns its carriers, distinctly named.** `srmech_bigint` (arbitrary
   integer), `Q` (exact rational), `Mat`/`Vec`/`HV` (linear algebra), the Class-N
   series-truncate trig/exp/log, etc. A stdlib `fractions.Fraction` (or any external
   rational) may be *accepted on input* via the numeric protocol, but is never the
   emitted carrier and is never imported.

3. **"Free" means ZERO — no import, no `np.`, no lazy bridge, no `_require_numpy()`
   subpackage gate, no "accuracy tail" exception.** A module that is numpy/math/
   fractions-free must have literally no import of it anywhere in its reachable
   graph, and a test for such a module must itself be free of the library.

4. **Enforced by AST ratchets, not vigilance.** Each purge ships a ratchet that
   AST-walks `srmech/` and fails on the banned import (`test_no_stdlib_math_import`,
   the numpy-carrier ratchet, `test_no_stdlib_fractions_import`). Ratchet counts only
   ever go DOWN. Any future external-math library gets the same treatment.

5. **Float is the last mile only.** Exact work stays in the integer ALU / `Q` /
   `srmech_bigint` all the way; a `float` appears only at the terminal display /
   projection boundary (see ADR-0005). This is *why* no external float-math library
   is needed in the interior.

## 3. Consequences

- A bare-C host (ADR-0003) with no Python stdlib and no third-party math library
  runs the same exact-relationship math. This is the point.
- Enforcement history (all shipped + ratcheted): **numpy** removed across the
  carrier arc rc75–rc133; **stdlib `math`** removed rc13; **stdlib `fractions`**
  removed rc263 (the `Q` carrier subsumed it). Each left a standing AST ratchet.
- New surfaces cost more up front (build the native primitive) but never accrue an
  external-library dependency that has to be unwound later at ~20-module scale.

## 4. Sources (consolidated from project memory)

`[[feedback_missing_math_is_added_to_srmech_as_cascade_never_imported]]` ·
`[[feedback_math_library_is_the_signal_to_find_the_cascade]]` ·
`[[feedback_numpy_free_means_zero_numpy_no_bridges]]` ·
`[[feedback_numpy_is_out_the_door_not_optional]]` ·
`[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]` ·
`[[feedback_no_numpy_rosetta_peer_continuous_float_error_collecting]]` ·
`[[feedback_never_numpy_math_when_srmech_can_cascade]]` ·
`[[feedback_carrier_ratchet_misses_require_numpy_subpackage_gates]]` ·
`[[feedback_carrier_ratchet_floors_at_gated_scientific_tail_not_zero]]` ·
`[[feedback_prefer_carrier_native_arithmetic_over_downcast_decline]]` ·
`[[feedback_best_rational_needs_nonnegative_use_signed_for_floats]]`
