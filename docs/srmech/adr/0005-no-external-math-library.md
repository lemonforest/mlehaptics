# ADR-0005: No external mathematics library — srmech is its own math library

**Status:** ✅ Accepted (standing architecture policy; consolidates discipline previously held only in project memory).
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

4. **Enforced by ONE data-driven AST ratchet, not vigilance and not a file per
   library.** `tests/test_selfhosting_import_ban.py` AST-walks the tree and fails on
   a banned import; every ban is a row in its `BAN_LIST` table, so **adding the next
   ban is a data edit**. Counts only ever go DOWN. Any future external-math library
   gets a row.

   *Why one table (rc405, `#T1073`).* Until rc405 this clause named three separate
   files — `test_no_stdlib_math_import` (rc13), the numpy-carrier ratchet (rc69),
   `test_no_stdlib_fractions_import` (rc263) — and that shape re-created §1's failure
   one level up: stating only the instances is what let `fractions` in, and a file per
   instance means the FOURTH ban costs a new file, so it does not get written. It had
   not been: `decimal` is named in §2 above and had **no ratchet at all**. The three
   files are absorbed; the table now carries seven rows, each with a **mode** and an
   **enforcement**:

   | module | mode | enforcement | replaced by |
   |---|---|---|---|
   | `numpy` | BANNED_ENGINE | strict zero | `Mat` / `Vec` / `HV` + native dense kernels |
   | `math` | BANNED_ENGINE | strict zero (+ `math.<attr>` access) | `srmech.math.rational` Class-N cascades, `srmech_isqrt` |
   | `fractions` | BANNED_ENGINE | strict zero; 62 named `tests/`+`tools/` allowances (rc407) | `srmech.math.q.Q` / `to_q` |
   | `decimal` | ALLOWED_PROJECTION | strict zero; 1 named `tests/` oracle (rc407 widened the scope to `tests/`+`tools/`, matching `fractions`) | `Q` / `srmech_bigint` interior; projection is srmech's own `srmech_double_repr` |
   | `json` | FRONT_DOOR_ONLY | down-only CEIL = 29 (rc407) | `srmech._json.loads` |
   | `tomllib` | FRONT_DOOR_ONLY | strict zero; 1 named file (rc407 drained the 2 exception-alias importers) | `srmech._toml.loads` |
   | `tomli` | FRONT_DOOR_ONLY | strict zero; 1 named file (rc407 drained the 2 exception-alias importers) | `srmech._toml.loads` |

5. **Projection out is allowed; engine use is not** (user direction 2026-08-05:
   *"we can let srmech project to decimal when needed"*). The ban is on using a
   foreign library as the **computation engine**. srmech converting or emitting to a
   foreign type at an output / interop boundary is legitimate, which is why the ban
   list carries a per-row MODE rather than being a flat blocklist. `ALLOWED_PROJECTION`
   permits an import from a NAMED file — and in the package `decimal` stays at
   strict zero, because the capability is already self-hosted in C as
   `srmech_double_repr` (integer-only Ryu, shortest round-trip) and no stdlib
   `decimal` is needed for it.

   **Amended rc407 (`#T1076`): a named file may be a projection boundary OR an
   independent oracle.** Through rc406 this clause said such a file must be "a
   projection boundary", and that was too narrow for the ban list's own contents.
   `fractions` was the ONLY row scanning `tests/`+`tools/`, so a live `decimal`
   import in `tests/test_classn_precision_wave2_rc320.py` — backing gate G2's
   precision oracle for all seven Q61 float-projection ops — sat outside every
   row's scan, unallowanced and unseen. rc407 widened the `decimal` row to match
   its exact-arithmetic peer, and the file it then had to name is an `_ORACLE`,
   not a projection boundary at all. So `ALLOWED_PROJECTION` admits both:

   - a **projection boundary** — srmech CONVERTING or EMITTING the foreign type
     at an output / interop edge; or
   - an **independent oracle** — a TEST importing the foreign library to grade a
     srmech result against a reference srmech did not produce. That is the
     OPPOSITE of engine use: the whole point is that the foreign library does not
     share the carrier under test.

   What stays banned is unchanged, and is the only thing the mode was ever about:
   srmech importing the library to do its own math. The package-scope ceiling is
   still 0.

6. **The ban is a COVERAGE instrument, not purity theatre** (same direction:
   *"this approach of srmech tooling first also means we thoroughly test all our
   surfaces"*). Reaching for srmech first is how every shipped surface gets exercised
   and how real gaps become visible. When the guard fires the first question is
   **"does srmech already ship this and I did not look?"** — twice in one session the
   answer was yes (`mat_rank`, `srmech_double_repr`). The guard says so in its failure
   message.

7. **Float is the last mile only.** Exact work stays in the integer ALU / `Q` /
   `srmech_bigint` all the way; a `float` appears only at the terminal display /
   projection boundary (see ADR-0005). This is *why* no external float-math library
   is needed in the interior.

## 3. Consequences

- A bare-C host (ADR-0003) with no Python stdlib and no third-party math library
  runs the same exact-relationship math. This is the point.
- Enforcement history (all shipped + ratcheted): **numpy** removed across the
  carrier arc rc75–rc133; **stdlib `math`** removed rc13; **stdlib `fractions`**
  removed rc263 (the `Q` carrier subsumed it). Each left a standing AST ratchet;
  rc405 absorbed all three into the one `BAN_LIST` table above. The per-rc numpy
  drainage record (61 → 0) is **not** in the guard — it is committed per-flip in
  `c/ROSETTA_LEDGER.md` and per-rc in `python/CHANGELOG.md`, and the constant name
  `CEIL_NUMPY_CARRIER` is kept in the guard so those records stay live.
- rc405 also closed a scan hole the retired guards carried: both skipped any path
  under `srmech/_native/`, on a comment that it holds only compiled libraries. That
  stopped being true when `srmech/_native/__init__.py` became a **1.1 MB generated
  Python module** — which was therefore exempt from the `math` and `fractions` bans.
  The table-driven guard scans every `.py` with no exclusion; measured at adoption,
  both stay at 0, so closing it was free.
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
