# `CDRegister` as srmech's general-purpose addressing layer — the shipped contract (rc301, `#938`)

This note is the **committed design contract** for rc301. It is a hard gate: the
op code that follows must CONFORM to it, and a reviewer must be able to read this
and predict the API. It states what `CDRegister` IS (a content-agnostic addressing
floor), the derivation of its one non-obvious constant (the `min(dim, 8)`
working-set cap), the optional-layer flag semantics, and the two genuine design
choices (the EC parameterisation and the flag shape) with their reasoning.

Provenance: rc297 (`#934`) brought the general N-slot register in-tree as an
addressing object; rc298 (`#933`) raised the addressing cap to 256. rc301 ports
the four VALUE-operations that until now lived only on `SedenionRegister`
(`couple_working` / `uncouple_working` / `carry` / `correct`) onto `CDRegister` as
its two OPTIONAL layers, and establishes the layer decomposition below as the
register's architecture of record. SSoT for the Hurwitz derivation: Hurwitz
(1898); Baez, *The Octonions*, arXiv:math/0105155. SSoT for the EC ladder: Hamming
(1950), *Error detecting and error correcting codes*, Bell Syst. Tech. J.
29(2):147–160.

---

## 1. The three-layer decomposition — addressing is the universal floor

`CDRegister` is a **general-purpose addressing layer**: a structured, reversible,
*signed* pointer over a slot-space of `dim` named slots `e0..e{dim-1}`. It is NOT a
surface that subsumes every class's operations — it is the content-agnostic floor
those operations sit on. Three layers, stacked:

```
┌────────────────────────────────────────────────────────────────────────────┐
│ CORE   addressing            content-AGNOSTIC, oriented, scales freely with  │  ← the "pointer";
│                              dim (1 → 256). The universal part.              │    always present
├────────────────────────────────────────────────────────────────────────────┤
│ OPT    reversible coupling    binds VALUES into one reversible working word; │  ← opt-in
│                              capped at min(dim, 8) by Hurwitz; does not       │    (coupling=True)
│                              change KIND.                                     │
├────────────────────────────────────────────────────────────────────────────┤
│ OPT    error correction       Hamming(2ⁿ−1) block; a separate axis from dim. │  ← opt-in
│                              Single-error-correcting GF(2) code.             │    (error_correction=True)
└────────────────────────────────────────────────────────────────────────────┘
```

Four precise properties, each of which holds in what rc301 ships:

- **Addressing is content-INDEPENDENT.** `navmap(j)` is a pure function of `dim`
  (the `cd_basis_product` cocycle: `e_i · e_j = ±e_k`), identical regardless of
  what the slots contain. The pointer does not read the payload.
- **Storage is content-AGNOSTIC.** Slots hold anything — a content name, a minted
  address, a value key. The addressing layer never inspects it.
- **Orientation-aware.** `navmap` returns a `±1` alongside each destination — the
  Class-C chirality layer living *inside* the addressing. Oriented content honors
  the sign (a signed value flips); opaque content ignores it.
- **KIND is dimension-invariant.** dim 8 → 256 is the SAME signed-permutation
  addressing with more slots. More dim = more resolution (address space), not a
  different object. Going to 32 or 64 or 256 slots buys addresses, never a longer
  reversible word.

The **addressing layer is the universal / content-agnostic floor**. The two OPT
layers are consumers of specific *content shapes* (numeric values for coupling;
bit vectors for EC) that a pure-addressing consumer never pays for.

### How the 14-class consumers map onto the floor (proved in rc301, not assumed)

- **M (HDC bind)** rides the COUPLING layer: `couple_working` **IS** an HDC bind
  and `uncouple_working` its exact unbind (see §5 for the precise relationship to
  the shipped `hdc` bind family).
- **N (exact rational)** rides the CORE layer: a `CDRegister` over the `Q`
  carrier is a coherent addressable rational store — addressing is content-agnostic,
  so `Q` values are just content.
- **L (Laplacian)** rides the CORE layer as **STORAGE, not OPERATION**: a bare
  register holds a Laplacian spectrum and addresses into it; the eigendecomposition
  itself stays in `Mat`. L is the FALSIFIER for "the register subsumes every
  class" — it fits as storage precisely *because* the register is only a floor.

---

## 2. The working-set rule is DERIVED, not chosen: `min(dim, 8)`

The reversible coupling layer binds `≤ len(working_block()) − 1` values into one
working word. `working_block()` returns `e0 .. e{min(dim,8)−1}` — so the number of
bindable values is `min(dim, 8) − 1`:

| dim | algebra | `working_block()` | bindable values (cap) |
|-----|---------|-------------------|-----------------------|
| 1   | ℝ       | `(0,)`            | **0** — pure addressing, no coupling |
| 2   | ℂ       | `(0, 1)`          | **1** |
| 4   | ℍ       | `(0, 1, 2, 3)`    | **3** |
| 8   | 𝕆       | `(0..7)`          | **7** |
| 16  | 𝕊       | `(0..7)`          | **7** (pinned) |
| 32  | 𝕋       | `(0..7)`          | **7** (pinned) |
| 256 | —       | `(0..7)`          | **7** (pinned) |

This is derived from **Hurwitz's theorem (1898)**, and the derivation is written
out here so a future maintainer does not "simplify" the pin back to a bare
constant.

### The Hurwitz derivation, legible to a non-mathematician

A **normed division algebra** is a number system where (a) you can multiply, (b)
you can *divide* (every nonzero element has an inverse — so "bind by multiply,
recover by divide" works), and (c) sizes multiply: `|a·b| = |a|·|b|`. Hurwitz
proved in 1898 that such systems exist at **exactly four sizes**: dimension 1 (the
reals ℝ), 2 (the complexes ℂ), 4 (the quaternions ℍ), and 8 (the octonions 𝕆) —
and **nowhere else**. The number of *imaginary* directions is one less than the
dimension: **0, 1, 3, 7**.

The reversible coupling layer works by **binding-by-multiply and recovering-by-
divide**. That REQUIRES the division property. So:

- **Below 8, the cap shrinks to the algebra's own size.** A dim-2 register lives in
  ℂ, which has 1 imaginary slot, so it can bind 1 value reversibly. A dim-4 register
  lives in ℍ (3 imaginary slots) → 3 values. There is no reversible room the algebra
  does not have.
- **At and above 8, the cap PINS at 7 — it never grows.** This is the subtle part.
  A dim-16 (sedenion 𝕊) or dim-256 register is NOT a division algebra — at dim 16
  and up, "sizes multiply" fails and *zero divisors* appear (two nonzero things
  whose product is zero), so global division breaks. BUT the first 8 coordinates
  `e0..e7` of every higher rung form an **exact copy of the octonions sitting
  inside** (a *subalgebra*): the octonion multiplication table is literally the
  top-left 8×8 corner of the sedenion table, the top-left corner of the
  32-dimensional table, and so on. Within that `e0..e7` sub-block, all three
  division-algebra properties still hold — it is a genuine 𝕆 living inside the
  bigger, broken structure. So a reversible working word **survives** at dim 16+
  (it runs entirely inside the embedded 𝕆), but it **cannot grow past 7**, because
  the moment you use an 8th imaginary slot you leave the octonion sub-block and land
  in the zero-divisor region where recover-by-divide is no longer guaranteed.

That is why the constant is `min(dim, 8)` and not, say, `dim` or a flat `8`: below
8 it is the algebra's real size; at/above 8 it is pinned by the octonion
sub-block, not by a magic number. **The pin is a theorem, not a tuning knob.**

### Why this is DISJOINT from the addressing cap (they must not be conflated)

Addressing (the CORE layer) survives to `dim = 256` and beyond because it needs
only that `e_i · e_j` be a **signed permutation** (`±e_k`) — a property of a
*single* basis pair, which zero divisors (built from *sums* like `e1 + e10`) never
touch. Coupling (the OPT layer) needs the full division property and therefore
caps at the octonion. The two boundaries are **disjoint** and are kept so:
`working_block()` caps at 8 while `dim` runs to 256. rc297's
`cd_navmap_is_signed_permutation` already makes the addressing premise
runtime-checkable; this note pins the coupling premise in prose.

### The degenerate base: dim 1 (ℝ)

A dim-1 register has **0 imaginary directions** → cap 0 → pure addressing, no
coupling, no EC to bind. It is a **legal instantiation** and must behave, not
error: `couple_working([])` returns `[]` (couples nothing), `uncouple_working([])`
returns `[]` (uncouples to nothing). Passing any value to a dim-1
`couple_working` raises (cap 0 exceeded), exactly as passing an 8th value to a
dim-8 register raises. The tower has a floor, and the floor is real.

---

## 3. Optional at instantiation — the flag semantics

A pure-addressing consumer (address-complete to 256, e.g. an L-style spectrum
holder) must not pay for the coupling/EC machinery. Therefore the two OPT layers
are **off by default** and opted into at construction. rc301 ships **two
independent boolean flags**:

```python
CDRegister(dim, D=8192, codebook=None, minter=None, namespace=None,
           coupling=False, error_correction=False)
```

- **Bare register (both False — the default): pure signed-pointer addressing.**
  `write` / `read` / `navmap` / `navigate` / `is_navigable` / `working_block` /
  `carry_block` all work (CORE). The four value-operations
  (`couple_working`, `uncouple_working`, `carry`, `correct`) **raise a clear
  `ValueError`** directing the caller to opt in. A bare register genuinely does not
  expose the coupling/EC surface — the methods are gated, not merely unused.
- **`coupling=True`** enables `couple_working` / `uncouple_working` (the Class-M
  reversible working word).
- **`error_correction=True`** enables `carry` / `correct` (the Hamming GF(2) EC
  block).

The flags gate only method *availability*; they allocate no per-instance state
(the coupling/EC operations are stateless functions of their arguments, not of the
register's slot-map), so a bare register carries nothing extra. Storing the two
bools is what makes "does not expose" real and testable.

The module-level functions `cd_couple_working(vals, dim)` /
`cd_uncouple_working(word)` / `cd_carry(overflow_bits, n=3)` /
`cd_correct(codeword)` are the always-available computational core (mirroring
`cd_navmap(dim, j)`); the FLAG is a property of a `CDRegister` *instance* (bare vs
opted-in), not of the pure functions.

---

## 4. The EC axis is independent of `dim` — and `n` stays a parameter (default 3)

The error-correction layer is a **Hamming(2ⁿ−1) single-error-correcting GF(2)
block code**. Its size is governed by `n` (the parity-bit count), which is a
**separate decision from the working-set scaling** and must not be conflated with
it:

- The coupling cap scales with `dim` (Hurwitz: `min(dim, 8) − 1`).
- The EC block size scales with `n` (Hamming: `2ⁿ − 1` codeword bits, `2ⁿ−1−n`
  data bits), **not** with `dim`. A Hamming(7,4) carries 4 data bits whether the
  register is dim 16 or dim 256.

**Decision: `n` stays a PARAMETER, default 3** — `carry(overflow_bits, n=3)`,
matching the shipped `SedenionRegister.carry` signature exactly.

Reasoning:
1. **Oracle parity requires it.** The faithfulness gate is that `CDRegister(dim=16,
   …)` reproduces `SedenionRegister` bit-exactly; the oracle's `carry` already
   takes `n=3` as a default parameter, so the port must too.
2. **The ladder is the whole point.** The Hamming module ships the full `2ⁿ−1`
   ladder (Hamming(7,4) / (15,11) / (31,26) / …) precisely so the carry block can
   *grow with the payload*: 4 data bits at n=3, 11 at n=4, 26 at n=5. Fixing `n=3`
   would amputate that ladder for no gain.
3. **Independence is honored, not asserted.** Because `n` is a free parameter
   orthogonal to `dim`, the register cannot accidentally couple EC size to slot
   count — the independence claim is structural, not a comment.

Fence (inherited from the hamming module, F449): this is single-error-correcting
per rung (minimum distance 3); larger tolerance is BCH/RS, a different code, out of
scope. Real-coefficient EC is likewise out (GF(2) only).

---

## 5. What the port is, precisely (so the API is predictable)

The four methods delegate to the SAME shipped primitives `SedenionRegister` uses —
no new algebra, no new C symbols:

| method | delegates to | Rosetta bucket |
|--------|-------------|----------------|
| `couple_working(vals)` | `hypercomplex_couple(vals, axis="diagonal")` | `composition_of_c` |
| `uncouple_working(word)` | `hypercomplex_couple(word, axis="diagonal", inverse=True)[1:]` | `composition_of_c` |
| `carry(bits, n=3)` | `hamming_encode(bits, n)` | `composition_of_c` |
| `correct(codeword)` | `hamming_decode_correct(codeword)` | `composition_of_c` |

The ONLY difference from `SedenionRegister` is that the coupling cap is read from
`len(working_block()) − 1` (dim-scaled) instead of the constant `WORKING_WORD_CAP =
7`. At dim 16 the two coincide, which is why oracle parity is bit-exact.

The underlying coupling math is already C-backed
(`srmech_hypercomplex_couple_q61`), and the EC math is already C-backed
(`srmech_hamming_encode` / `srmech_hamming_syndrome` / the composed decode). So
each of the four ops **exists fully in C** as a composition of reachable header
symbols — the C peer for the reversible working word and for the EC block is the
one the primitive already dispatches to. rc301 therefore adds **no new C symbol**
(ABI stays 8): a dedicated `srmech_cd_couple_working` would be `srmech_hypercomplex_
couple_q61` plus a trivial Python-side cap guard — a laundered duplicate, which the
no-duplication discipline forbids. The honest classification is `composition_of_c`,
exactly as the sedenion `sed_couple_working` / `sed_carry` / `sed_correct` adapters
are classified.

### `couple_working` **IS** an HDC bind — the M mapping, stated precisely

`couple_working` folds `≤ min(dim,8)−1` streams into one quaternion/octonion via
the twiddle `T = exp(σ·μ·θ)` (`axis="diagonal"`, `θ = π/2`) and octonion multiply;
`uncouple_working` applies the conjugate twiddle `exp(−μθ)` and recovers the
streams. That is a **bind/unbind pair** in the algebraic (division-algebra) sense —
`T̄·(T·q) = ‖T‖²·q`, the F437 reversibility identity — and it is the CANONICAL
Class-M bind example the register exposes. It is the *same operation family* as the
shipped `hdc.bind`/`hdc.similarity` (bind = combine two carriers reversibly;
recover by the inverse), but at a **different carrier**: `hdc.bind` binds two
`D`-bit hypervectors by XOR/permute over 𝔽₂ᴰ, whereas `couple_working` binds
`≤7` real streams into one hypercomplex value over 𝕆. Same Class-M *role*
(reversible associative combination), two carriers (𝔽₂ᴰ vs 𝕆) — so the claim is
"same operation, characterized difference," not "literally `hdc.bind`." The
associative storage layer (`write`/`read`) uses the 𝔽₂ᴰ form; the coupling layer
uses the 𝕆 form.

---

## 6. Shipped invariants (rc301)

- **ABI stays 8** — no new C symbols; the four ops compose existing reachable C.
- **`tools.total` 466 → 470** — four new MCP `ToolEntry` (`cd_couple_working`,
  `cd_uncouple_working`, `cd_carry`, `cd_correct`), content-agnostic list/int
  signatures that carry MCP coercers (unlike the structured `sed_*` adapters, which
  stay TOML-class-only and coverage-exempt).
- **carriers stay 25**, **`CD_MAX_DIM` stays 256**, **`CEIL_WIRE_GLUE_GAPS` stays
  10**, the `non_compute` split is untouched — the four ops are `composition_of_c`,
  not `non_compute`, so no debt/glue ceiling moves.
- **`SedenionRegister` stays an independent oracle** — NOT collapsed to a dim-16
  `CDRegister` alias; the faithfulness gate depends on it.
- **c_claims manifest unchanged** — the manifest processes only `c_dispatched` ops;
  the four new `composition_of_c` ops do not appear in it (regeneration is a no-op,
  verified with `--check`).
