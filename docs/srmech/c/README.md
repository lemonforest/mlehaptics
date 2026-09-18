# srmech — C library

Native-C parity surface for the [`srmech`](../python/) Python package's
Attested Multi-Source Collector (AMSC) framework. Ports the three
load-bearing AMSC primitives to portable C so srmech meets the same
**Python/C parity discipline** that
[`ephemerides-spectral`](../../antikythera-maths/ephemerides-spectral/c/)
uses. Same monorepo, same quality bar.

## Status — full 14-class native C parity shipped

The full **14-class A–N C-parity primitive vocabulary** is implemented
in native C and ships in every platform wheel as
`libsrmech.{so,dll,dylib}`. The Python package binds it through a
ctypes shim (`srmech._native`) and falls back to a complete
pure-Python implementation of every API surface when no native
library is present (Pyodide / WASM, or any environment where the
shared library can't load). srmech is at **v0.6.0rc9**; this is no
longer scaffolding.

### Source files (`c/src/`)

| File | Surface |
| ---- | ------- |
| `srmech_sha256.c`   | Class A — FIPS 180-4 SHA-256 content-addressing |
| `srmech_ndjson.c`   | Class C — streaming NDJSON line reader |
| `srmech_cyclic.c`   | Class I — cyclic-group / modular arithmetic |
| `srmech_laplacian.c`| Class L — dense graph Laplacian + Jacobi eigvals |
| `srmech_primes.c`   | Class J — primality / factorisation / order |
| `srmech_tlv.c`      | Class B — TLV byte-canonical framing |
| `srmech_search.c`   | Class G — byte-pattern search |
| `srmech_meta.c`     | Class H — version + ABI self-introspection |
| `srmech_dispatch.c` | Class D — multi-needle pattern dispatch |
| `srmech_catalog.c`  | Class E — sorted-key catalog lookup |
| `srmech_template.c` | Class F — template `{key}` substitution |
| `srmech_hdc.c`      | Class M — HDC bind / bundle / permute / similarity |
| `srmech_rational.c` | Class N — rational approximation (best-rational) |
| `srmech_kepler.c`   | Class K — pin-slot / Kepler solve / equation-of-centre (Class-N Q61 cascade trig, no libm) |
| `srmech_cascade.c`  | cascade-composition primitives |
| `srmech_bus.c`      | bus / handle-registry surface |
| `srmech_parallel.c` | Klein-4 four-sector parallel dispatch |
| `srmech_kuramoto.c` | native Kuramoto coupled-oscillator step |

The two newest v0.6.0 C files:

- **`srmech_parallel.c`** — the Klein-4 four-sector parallel dispatch
  (#771 / #778), with a portable thread shim that selects pthreads,
  Win32 `CreateThread`, or a serial fallback at build time so the
  same source compiles cleanly across the CI matrix.
- **`srmech_kuramoto.c`** — the native Kuramoto coupled-oscillator
  forward-Euler step (rc9), using the Class-N cascade `srmech_sin`, not
  libm — as `srmech_kepler.c` uses the cascade's sin / cos / atan2.

### ABI

C ABI version is **28** (`SRMECH_ABI_VERSION 28` in
`c/include/srmech.h`). **The v28 bump is rc476's (`#T1188`): the square root is CORRECTLY ROUNDED,
and was not.** One bump on the oldest ground this header records — **served values move** (v21 /
v26 / v27's) — and on nothing else.

`srmech_rational_sqrt` and `srmech_sqrt_q61` read `x = M·2^e` out of the IEEE fields and computed
`isqrt(M << 54)`. `M` is the RAW mantissa field, so for a **subnormal** `x` it is far below `2^52`
and the root's WIDTH tracked the operand's magnitude instead of being fixed: `M = 1` gives
`isqrt(1 << 54) = 2^27`, a **28-bit** root where 53 are needed. And even at full width a FLOOR is
not a rounding — a floored root can sit on a rounding midpoint, and the projection then rounds it
the wrong way. **Measured at rc475, at the exported symbols, no Python in the path: 480 of the 1956
non-square integers in 2..2000 served a double one ulp LOW (all on the same side); 4032 of the 4096
subnormal mantissas 1..4096 were misrounded, the worst by 16,609,076 ulps; the narrowest root was
28 bits.** After the repair — normalise the radicand into `[2^106, 2^109)`, then a sticky low bit,
then a 53-bit rounding done in INTEGERS — the same sweeps measure **0 / 1956** and **0 / 4096**,
with a minimum root width of 54.

The evidence that had stood in for this was `srmech_sqrt.c`'s own banner: *"validated vs libm to
machine epsilon (rel err ≤ 2.3e-16) over 50000+ values"*. That is a **libm oracle** this library
does not link and a bare-C host cannot appeal to, reporting a **relative-error bound**, which cannot
see a 1-ulp misround at all. `c/test/test_srmech_sqrt_subnormal.c` replaces it with an exact
128-bit integer certificate over ~14,500 rows, and carries a can-fail control that must reject both
neighbours of the true `√2`.

Every consumer that rides those roots moves with them: all three eigenvalues of a 3×3
`jacobi_eigvals` (the largest crossing the binade at 4.0), a singular value of a 2×2 `mat_svd`, and
the λ⁸ / D^(−1/2) constants, whose own reciprocal sites are repaired in the same release —
`1.0 / s3` was a floored root then a reciprocal then a multiply, three roundings where the file's
prose claimed one, serving `0.5773502691896258` for a `1/√3` whose correctly rounded double is
`0.5773502691896257`. **The library gains two names** (`srmech_sqrt_scaled`, `srmech_inv_sqrt`,
806 → 808 `T srmech_*`) and neither is a reason to bump: both are declared in the private
`c/src/srmech_sqrt_internal.h`, reach no `srmech.h` declaration and no ctypes binding, and adding a
symbol has never bumped. `GENOME_FORMAT_VERSION` stays 20.

**The v27 bump was rc475's (`#T1188`): the Zassenhaus core's bignum pool
WIDTH, plus a deterministic equal-degree split.** One bump over three changes to
`srmech_factor_squarefree_primitive` and `srmech_factor_integer_poly`. The exported symbol set is
IDENTICAL either side — 815 names, none added, none removed, every new function `static` — so
neither the additive rule nor the removal rule reaches it. It bumps on the two grounds that remain,
and on each independently: **served values move** (v21 / v26's ground) and **an existing function
returns a larger envelope** (v10 / v12 / v23 / v24 / v25's).

**(1) The width.** `bp_buf` spaced the 30 bignum poly buffers `cw = deg+1` apart, while a quadratic
Hensel step forms products of length `n + max(a,b) - 1` (`s·e`, `t·e`, `q·g`, `s·B`, `t·B`, `c·g*`)
— longer than `deg+1` whenever a non-last mod-p split has `max(a,b) ≥ 3` — and none of `bp_mulmod`
/ `bp_addmod` / `bp_submod` / `bp_divmod_monic` checked its output against a width. So the product
ran into the NEXT pool buffer, which holds live Hensel state (the quotient, then `H`'s lead
coefficient); `bp_divmod_monic` was then handed a divisor that was no longer monic, its quotient
digit was `rem[r-1]` with no division by the lead, the top coefficient never cancelled and `r` never
decreased. **The hang was the symptom; the defect was the overrun.** Measured over 84 polynomials at
rc474, 8 s per call in a subprocess, against the pure oracle: **34 did not return, 6 returned a
WRONG VALUE, 3 DECLINED silently, 41 agreed** — and 84/84 agree after the fix. The wrong-value class
is what makes this a served-value bump rather than a bug-fix note: on
`[14,50,61,-149,-259,47,209,106,-76,-4,1]` rc474 answered `(x-1)` times ONE degree-9 factor, whose
product still equals the input, so the composite's own self-check passed while a reducible factor
was served as irreducible.

**(2) The status.** The new guards return `SRMECH_ERR_INTERNAL`, not `SRMECH_ERR_OVERFLOW`, and both
Python wrappers **raise** on it. `OVERFLOW` is documented as "the caller's arena is too small — grow
it and retry", and the wrappers mapped every non-OK status to `None`, i.e. to a silent pure
fallback. That is how the 3 declined rows above went unseen. `fw` is derived from `deg`, so a width
violation cannot be relieved by a larger arena; it is an internal invariant break and now says so.

**(3) The split.** `fp_equal_degree` no longer draws random polynomials and retries. It computes the
Berlekamp subalgebra `{v : v^p ≡ v mod g}` as `nullspace((Q − I)ᵀ)` with `Q[i] = x^(i·p) mod g`, and
separates each block by `gcd(v − s, part)` over every basis vector and every shift `s ∈ 𝔽_p`. By CRT
that subalgebra has dimension exactly `k = n/d`, and *any* basis of it separates every pair (if all
basis vectors agreed on a pair, linearity would make the whole subalgebra agree, contradicting CRT),
so the split terminates in a **proven static** number of steps where the Cantor–Zassenhaus retry it
replaces had only an EXPECTED one. The tight form of that bound is **`(k−1)·p` passes and
`p·(k−1)·⌊k/2⌋` gcds** — the constant `1` is always the first RREF basis vector, separates nothing,
and is skipped, and only parts of degree `> d` are gcd'd, each holding ≥ 2 irreducibles. (`k·p` /
`k·p·k` is also true and is what the source docstrings quote; it is not the worst case, and the
difference matters for a gate: the measured maximum is **0.9545** of the tight bound over 17,238
blocks against 0.26 of `k·p·k`, so asserting the loose form leaves a 4× slack a regression could
hide under.) Censused exhaustively over `p ∈ {3,5,7,11,13} × d ∈ {1,2,3}`, `k ≤ 6`: **0 dimension
failures, 0 incomplete returns, 0 over either bound, and the constant was the first basis vector on
17,238 of 17,238 blocks**. `p = 2` is unreachable — both prime searches start at 3. `FAC_RNG_SEED`,
`fac_rng_next`, `fp_polypow_big`, `fp_ed_exp` and `fp_equal` are gone. The mod-p factor list now
comes back in canonical `(len, coeffs)` order (`fp_mp_sort`, matching the pure peer's `sorted()`),
which is load-bearing: everything downstream — which subsets the recombination enumerates, hence the
ℤ peel order and `hit_cap` — is a function of that order. **The CORE's peel order therefore MOVES**:
on an independent 48-row set the composite is identical 48/48 *with* order, while
`srmech_factor_squarefree_primitive`'s list is reordered on 14 of 46 served rows and is an identical
multiset on 46/46. That is forced — any deterministic replacement gives a different mod-p order.

**(4) The envelope.** `srmech_factor_squarefree_primitive_ws_bound` counts `FAC_BP_N * fw` rather
than `FAC_BP_N * cw` and carves `bk_m` + `bk_piv`: 215,176 → 286,996 at `coeff_limbs` 1 / deg 6, and
48,008,632 → 48,827,716 at `coeff_limbs` 4 / deg 48. `srmech_factor_integer_poly_ws_bound` follows,
because it sums the core's. An existing function returning a larger envelope would have bumped on
its own.

The pairing this refuses is an **rc474 `.so` under rc475 Python**: it loads with `HAS_NATIVE True`
and then hangs or serves a reducible factor as irreducible, because Python asks the library for
`ws_bound` on every call and the stale library's answer is self-consistent.
`NATIVE_ABI_VERSION != EXPECTED_ABI_VERSION` is the only thing that stops it.
`SRMECH_GENOME_FORMAT_VERSION` stays 20 — no on-disk format moves.

**The v26 bump before it is rc473's (`#T1188`), and it is the SECOND bump on this
library driven by a SILENT WRONG VALUE rather than by a raise** — v21's ground, applied to the
Class-N scalar surface instead of to a chain wire. It adds no symbol, removes none and changes no
signature; what moves is *which inputs the C projection serves*, and that is the class v21's second
move bumped for, under its own sentence: **"co-equal projections must agree on what they refuse."**

Two independent halves. **(1)** Twenty-four call sites across seven translation units spelled
`(void)srmech_sin(...)` and friends, so a callee that had *already refused its argument* was
overruled by its own caller. Measured at rc472 through the exported symbols, with no Python in the
path: `srmech_equation_of_centre(2^53+1, 0.0549, 4)` returned `(SRMECH_OK, -0.08984990210223018)`
while the Python projection raised `ValueError`; `srmech_pin_slot(2^55, 0.5, 1.0)` returned
`(SRMECH_OK, 0.0)`; `srmech_kepler_solve(2^55, 0.3, 1e-12, 20)` returned `(SRMECH_OK,
3.602879701896397e+16)` — `E == M`, because the discarded refusal left the Newton iteration unable
to move; and `srmech_cascade_kuramoto_step_f64([0, 2^55], …)` returned `(SRMECH_OK, [0.0,
3.602879701896397e+16])`, oscillator 0 silently frozen at its input phase. Each now propagates its
callee's status. **(2)** The callee contracts themselves, where this header's own published promise
was being violated: `srmech_sin` / `srmech_cos` returned `SRMECH_OK` for NaN against a documented
`SRMECH_ERR_BAD_INPUT for non-finite x`; `srmech_atan` / `srmech_atan2` returned `SRMECH_OK` with
`-3.2146018366025517`, a finite value *below −π* and outside their own range, for NaN and — via
`Inf/Inf` — for both-infinite arguments with no NaN passed in; `srmech_exp` / `srmech_log` carried
an explicit `if (x != x) return SRMECH_OK;`; `srmech_rational_sqrt` served NaN and wrote `0.0`
rather than the promised NaN for every finite negative argument; `srmech_winding_fold` carried both
halves at once. All refuse now and all write NaN, and `srmech_atan2` gains the quadrant diagonal so
`atan2(±Inf, ±Inf)` answers ±π/4 / ±3π/4 as the pure projection does.

The pairing this rejects is the one that matters: an **rc472 library against rc473 Python** restores
the silent value with no other symptom, because the older `.so` computes a wrong number and reports
`SRMECH_OK` and there is no second channel to notice it by. `NATIVE_ABI_VERSION !=
EXPECTED_ABI_VERSION` is the only thing that refuses it. The `SRMECH_NODISCARD` attribute added in
the same rc is a **diagnostic**, not a wire change, and contributes nothing to the bump.
`SRMECH_GENOME_FORMAT_VERSION` stays 20.

The v25 bump before it is rc464's (`#T1188`) and it is the fourth of the REMOVAL kind (v7 / v8 / v11 before it), the plainest shape there is. Three exported symbols go — `srmech_sedenion_navmap`, `srmech_sedenion_navigate` and `srmech_sed_slots` — with the 16-slot `SedenionRegister` they were the Rosetta peer of. They are SUBSUMED, not dropped: `srmech_cd_navmap` / `srmech_cd_navigate` take the rung as a parameter and this header has documented them as bit-identical at dim 16 since rc298, and `srmech_sed_slots` was a validate-and-copy its one caller now does inline. A removed export produces no symptom other than a version mismatch, so by standing policy it always bumps. The `SRMECH_SEDENION_NUM_SLOTS` macro goes with them and contributes nothing — macros are not exported symbols. `srmech_sedenion_is_navigable` STAYS: it is the general DENSE kernel for every rung up to `SRMECH_CD_DENSE_MAX_DIM`, dispatched live by `left_mult_is_invertible`, and only its NAME was ever sedenion-specific. rc464 also changes what one existing function returns — `srmech_make_class_run_arena_bytes` now budgets the TOML parser's own stated bound instead of a hand-rolled `32 * toml_len` heuristic, so the envelope is LARGER — which is the v10 / v12 / v23 / v24 wire-sizing shape and would have bumped on its own; it rides this one. `SRMECH_GENOME_FORMAT_VERSION` stays 20.

The v24 bump before it is rc455's, and it is the SECOND instance of
a shape this header already recorded one function over. `srmech_dsl_chain_run`'s
writer reserve was derived from the INPUT length while it bounds the OUTPUT
tree, so `srmech_dsl_chain_run_arena_bytes` now returns a **smaller** envelope —
by exactly `32768 + 16*(chain_len + input_len)` — with the json builder, the
emit scratch and the write scratch carved forward from the value actually
produced instead. No signature changed and no symbol was added or removed; what
moved is what an existing function returns, which is the v10/v12 wire-sizing
shape. rc452's v23 note in `srmech.h` covers exactly that move on the SIBLING
`srmech_chain_run_arena_bytes` and says it "rides this bump rather than going
unrecorded", so declining here would leave the second instance of a recorded
shape unrecorded. Neither mixed-version pairing computes a wrong value: an old
(larger) cached figure over-provisions a v24 library, and a new (smaller) figure
handed to a v23 library gets a correct `SRMECH_ERR_OVERFLOW`.

*(⚠️ The narrative under this heading has lagged the integer even while the
integer was gated. At rc454 this paragraph still explained the **v20** bump —
rc451's `{"k":"t"}` TUPLE kind — beside a correct **23**, three bumps behind,
because `test_abi_prose_currency_rc449.py` asserts one decidable thing per file
(the integer equals the macro) and deliberately does not read the surrounding
rationale. That is the right scope for that gate and it is also the residual: a
number that cannot go stale above a story that can. rc455 rewrote the story with
the number.)*

*(This line read **3** from the v0.5.0 era until rc442 —
fourteen bumps stale, and wrong long before that release touched it. It then went
stale AGAIN five rcs later: rc447 bumped 17 → 18 and rc448 shipped over it, so by
rc449 it was two behind. The note that used to sit here said "no gate covers
`c/README.md` at all, which is exactly why it drifted the furthest" — and then it
drifted again, which is the whole argument. rc449 (`#T1158`) closed that:
`tests/test_abi_prose_currency_rc449.py` now reads this line and
`docs/srmech/CLAUDE.md`'s "ABI compatibility" section against the macro. The SSoT
is still the macro; the narrative SSoT is still that CLAUDE.md section.)* Bump it in lockstep only when the wire
format of an existing exported function changes; adding a new
symbol does not bump the ABI.

### JPL Power-of-Ten

The C library is clean on **eight** of the ten Power-of-Ten rules;
**Rule 1 (recursion half) and Rule 9 (function-pointer half) are
PARTIAL**, each under a seeded down-only ratchet — see
[JPL_AUDIT.md](JPL_AUDIT.md) for the rule-by-rule audit and the
measured Rule 9 census. *(This line said "JPL Power-of-Ten clean"
until rc452.)*
Enforcement is mechanical: `tests/test_jpl_audit.py` is a ratchet
(violations only ever go down) and the pedantic-build CI matrix
(`-Werror` / `-Wpedantic`, `/WX` on MSVC) runs on
Linux gcc / macOS clang / Windows MSVC, so any new warning fails CI.

Each rc auto-routes to TestPyPI via the rc-suffix gate in
`srmech-publish.yml`. A non-rc tag is the human-in-loop gate for
the production PyPI ship.

## Why C

srmech is **data-pipeline tooling, not embedded firmware** — but C
buys us three things ephemerides-spectral has already validated:

1. **Performance on hot paths.** Every catalog read walks NDJSON;
   every descriptor edit recomputes the canonical-TOML hash;
   SHA-256 attestation is per-row at codegen time. The Python paths
   stay correct; C is the fast path runtime can opt into.
2. **Parity discipline as quality ratchet.** The byte-exact Python/C
   parity tests catch any drift in either implementation. The C
   side is harder to get right; passing parity is evidence the
   Python side is also correct.
3. **JPL Power-of-Ten discipline** (Phase B6). The same rules
   ephemerides-spectral's C library passes — Rule 1 (no goto),
   Rule 3 (no malloc), Rule 4 (<60-line functions), Rule 5
   (≥2 assertions per function), Rule 6+7 (scope + return-value
   checks), Rule 10 (cross-platform pedantic-build CI matrix).

## Layout

```
c/
├── include/srmech.h                # public API (Phase B1)
├── src/                            # implementation .c files (B3–B5)
│   └── .gitkeep                    # placeholder; empty at B1
├── test/                           # C smoke + cross-language parity
│   └── .gitkeep                    # placeholder; empty at B1
├── Makefile                        # local build/test/parity flow
├── JPL_AUDIT.md                    # JPL Power-of-Ten compliance log
├── .gitignore                      # build/
├── .pages                          # mkdocs nav
└── README.md                       # this file
```

The top-level CMakeLists.txt lives one directory up at
`docs/srmech/CMakeLists.txt`, mirroring ephemerides-spectral's
`docs/antikythera-maths/ephemerides-spectral/CMakeLists.txt`.
scikit-build-core (wired in Phase B2) drives it via
`cmake.source-dir = ".."` from `python/pyproject.toml`.

## Build & test (post-B3)

```bash
cd c

# Build the static library
make lib

# Build + run the C smoke tests
make test

# Build + run the cross-language parity test
make parity

# Clean
make clean
```

`make` defaults to `cc -std=c17 -Wall -Wextra -Wpedantic -O2 -fPIC`.
Override `CC` and `STD` for cross-compilation; the source compiles
cleanly under C11.

### Windows note

The `feedback_run_wsl_smoke_before_amsc_push` memory applies once
real C code lands. WSL2 catches libm last-bit divergence that
Windows-local pytest doesn't. Run `scripts/smoke_local.sh` (or the
equivalent) under WSL before pushing any branch that touches C
source.

## License

MIT (parent project: mlehaptics).
