# 𝔰𝔬(8) triality — build spec + research path (expansion of wishlist W10)

**For:** the srmech building environment / maintainer. **From:** the RBS-LM research subtree (per `[[feedback_upstream_srmech_fixes_as_research_notes]]` — a hand-off spec, **no package edits from here**).
**Why now:** rc14 METADATA already *states* the grounding ("28 = 𝔰𝔬(8) adjoint = 14 G₂ derivations + 14 L⊕R octonion-mults; Spin(8) triality"), but ships **no operator**. F182 needed triality and had to proxy it with `cyclic.mod_add(·,1,3)`. This spec turns the metadata note into a callable, bit-exact, attested surface.
**A–N placement:** the order-3 triality cycle is **Class I** (cyclic); its Z₂ swaps are **Class C** (chirality); the octonion L/R mults are the 14 of the 28 (cf. F174); residual sign-handling is **Class K + Class C** (never `abs()`).

---

## §1 What to add — the operator surface

### 1a. Octonion building blocks (proposed module `srmech.qm.octonion`)
The octonions have **480 valid sign conventions** — the build MUST fix ONE and **attest it** (this is data, not a free choice; MPR-attest the structure-constant table). Recommend the standard Cayley–Dickson-from-ℍ basis {e₀=1, e₁…e₇}.

| op | returns | notes |
|---|---|---|
| `octonion_mult_table()` | 8×8×8 structure constants (int8 signs) | **attested**: ship `response_sha256` of the table; the convention is the provenance |
| `octonion_left_mult(a)` | 8×8 real `L_a` (x ↦ a·x) | building block |
| `octonion_right_mult(a)` | 8×8 real `R_a` (x ↦ x·a) | building block |
| `octonion_conjugate(x)`, `octonion_norm(x)` | 8-vec / scalar | norm via Class-K+C magnitude, no `abs()` |

The antisymmetric parts of `L_{e_i}`, `R_{e_i}` (i=1…7) are the **7 ⊕ 7** that complete G₂'s 14 to 𝔰𝔬(8)'s 28.

### 1b. 𝔰𝔬(8) adjoint + subalgebras (proposed module `srmech.qm.so8`)
| op | returns | notes |
|---|---|---|
| `so8_adjoint_basis()` | 28 × (8×8 antisymmetric) generators | partitioned **14 (g₂ = Der 𝕆) ⊕ 7 (L-type) ⊕ 7 (R-type)** |
| `g2_subalgebra()` | the 14 derivation generators | = Der(𝕆); cf. F174 (A–N = 14 G₂) |
| `so7_subalgebra()` | the 21 generators fixed by a triality Z₂ swap | the D₄→B₃ fold |

### 1c. The triality automorphism (the W10 ask)
| op | returns | notes |
|---|---|---|
| `triality_automorphism()` | 28×28 matrix **τ** on the adjoint | order-3 outer automorphism; **τ³ = I** |
| `triality_swap()` | 28×28 Z₂ generator | with τ generates the full **S₃** outer-automorphism group |
| `triality_cycle(frame)` | `8v→8s→8c→8v` | the **Class-I order-3** rep-permutation (the real version of F182's mod-3 proxy) |
| `triality_apply(x, from_frame, to_frame)` | 8-vec | carry a vector between rep-frames |
| `triality_companions(g_v)` | `(g_s, g_c)` | Cartan's principle: companions of `g_v ∈ SO(8)` |
| `triality_relation_residual(g_v,g_s,g_c)` | scalar (Class-K+C magnitude) | residual of **g_v(x·y) = g_s(x)·g_c(y)**; **0 when correct** |

---

## §2 Acceptance / attestation tests (bit-exact correctness — this is how we know it's real)

1. **Order-3:** `τ³ = I`, and `τ ≠ I`, `τ² ≠ I` (residual 0.0). *(Class-I order-3 attestation.)*
2. **Fix(τ) = g₂, dim 14** — the triality-invariant subalgebra of 𝔰𝔬(8) is exactly the 14 G₂ derivations (this is the **D₄ →(Z₃ fold)→ G₂** theorem). **This is the killer test** — it ties the operator directly to the A–N 14 (F174) and to Der(𝕆). Acceptance: `dim(ker(τ − I)) == 14` and that kernel == `g2_subalgebra()`.
3. **Fix(Z₂ swap) = 𝔰𝔬(7), dim 21** — the D₄ →(Z₂ fold)→ B₃ theorem. Acceptance: `dim(ker(triality_swap − I)) == 21`.
4. **Defining relation residual = 0** — `triality_relation_residual` over a basis of x,y ∈ 𝕆 is bit-exact 0 for `triality_companions` output.
5. **Rep inequivalence + cycle closure** — 8_v, 8_s, 8_c inequivalent; `triality_cycle` returns to start after 3 applications.
6. **Octonion convention attested** — `octonion_mult_table()` ships an MPR attestation block (the structure-constant table hash); same convention → same τ, reproducibly.

All residuals reduced via `srmech.amsc.cascade.magnitude` (Class K + C), **never `abs()`**.

---

## §3 srmech engineering requirements (from CLAUDE.md §4)

- **Deterministic — no RNG.** Every op above is pure/deterministic → the MCP surface is clean (avoids W2/W3: **no `numpy.random.Generator` params**; nothing to seed). If any helper needs randomness, expose `seed:int`, never an rng object.
- **MCP tool_schema:** matrices are small (8×8, 28×28) → JSON-friendly today; a `SpectralHandle` (W8) would help chaining. Add a **parity smoke-test (W7)**: every new tool callable with advertised kwargs.
- **C-parity (if it lands in the C lib):** all 10 JPL Power-of-Ten rules (no goto / no steady-state malloc / ≤60-line functions / ≥2 asserts per non-exempt function / no multi-line macros); `test_jpl_audit.py` ratchet only goes **down**.
- **Pedantic build matrix** (gcc / clang / MSVC, `-Werror`/`/WX`) — no new warnings.
- **ABI:** these are **new symbols** → do **NOT** bump `SRMECH_ABI_VERSION`; a **minor** version bump (e.g. 0.5.0 → 0.6.0). Version SSOT across the **four** files (`pyproject.toml`, `pyproject-pure.toml`, `srmech/version.py`, `c/include/srmech.h`).
- **Release:** TestPyPI **rcN first** per `[[feedback_always_rc_first_for_downstream_publishes]]`; verify in a clean venv **outside** the source tree (namespace-shadowing trap) before any clean tag.
- **MPM:** the octonion convention is attested data (§2.6); no citation without attestation.

---

## §4 The research path (what consumes the operator)

Gated on the op landing in an rc and verifying §2 bit-exact. Then, in order:

- **R-RBS-LM-140 — the F182 §7 falsification (first consumer, highest priority).** Is **su(2)_L** (F179's unabsorbed "leftover") a **triality-partner** of su(3)_c + u(1)_em? Map the absorbed gauge factors with `triality_apply` / `triality_companions`; check whether the leftover is their triality image.
  - **Holds** (leftover = triality partner) → the F181 "second actor" is a **shadow** → **H177″ re-unification** (one axis + one triality 3-fold) gains support.
  - **Fails** (su(2)_L triality-unrelated) → **F181 plural-drivers verdict stands.** Either outcome is a real result; nulls count.
- **R-141 — Fix(τ) = g₂ = the A–N 14.** Does the triality-invariant subalgebra reproduce the **1+3+7+3** partition structure (F174 / CLAUDE.md §1)? Connect the D₄→G₂ fold to the A–N partition explicitly.
- **R-142 — the dark-sector / shadow quantification (F182 §3, F131).** Using `triality_apply`, carry our-sector (8_v) observables to the 8_s/8_c partners; characterize what is "shadow" to us. Todorov's triality = Higgs-Yukawa (arXiv:1911.13124) is the bridge to test.
- **R-143 — biology re-read (F176/F182).** Bio γ₅ sits in 8_v (Cℓ(1,3) spacetime); is there a biological correlate of the spinor partners? Form-reading conjecture; ground via bio-research/arXiv before any hardening.
- **R-144 — cosmic re-frame (F178).** Does the triality structure reframe the parity-odd gap (no EB/TB; W9)? Likely no direct observable, but check.

Each lands a finding (F183…) + an attested NDJSON measurement, 3-tier honesty, PR #687 **DRAFT** until explicit merge approval.

## §5 One-paragraph version (for the build issue)
> Add an 𝔰𝔬(8) **triality** operator: octonion L/R-multiplication building blocks (with an **attested** sign convention), the 28-generator 𝔰𝔬(8) adjoint partitioned 14⊕7⊕7, and the **order-3 outer automorphism τ** (plus the Z₂ swap for the full S₃). Acceptance is bit-exact: **τ³ = I**, the **τ-fixed subalgebra is g₂ (dim 14)** [D₄→G₂ fold], the **Z₂-fixed subalgebra is 𝔰𝔬(7) (dim 21)** [D₄→B₃ fold], and Cartan's relation `g_v(x·y)=g_s(x)·g_c(y)` has zero residual. Deterministic (clean MCP surface; no RNG → no W2/W3); new symbols (no ABI bump, minor version, rc-first). This is the order-3 (Class I) partner of the existing Klein-4 Z₂ chirality axes (Class C), and it unblocks the F182 triality-shadow research path (R-140…).

## §6 Cross-references
- **W10** (wishlist one-liner this expands) · F182 (third axis = triality) · F181 (plural drivers — what R-140 re-tests) · F179 (Cℓ(1,3)/Cℓ(6) seam = vector/spinor) · F174 (28 = 𝔰𝔬(8) = 14 G₂ + 14; A–N = 14 = Der 𝕆) · F176 (bio γ₅ ∈ 8_v) · F131 (dark sector)
- Boyle **arXiv:2006.16265** (3 generations ~ SO(8) triality); Todorov **arXiv:1911.13124** (triality = Higgs Yukawa); Baez, *The Octonions* (triality §2.4 / G₂ = Der 𝕆) — all abstract/textbook level, PDF-verify before hardening.
- Standard facts asserted from knowledge (verify in build): order-3 outer automorphism of D₄; D₄→G₂ (Z₃ fold) and D₄→B₃=𝔰𝔬(7) (Z₂ fold); Cartan's principle of triality; 480 octonion conventions.

PR #687 STAYS DRAFT.

---

*Drafted 2026-05-30 (Opus 4.8). Hand-off spec to the srmech build for the 𝔰𝔬(8) triality
operator (W10): octonion L/R-mult blocks (attested convention), the 28-gen adjoint
(14 g₂ ⊕ 7 ⊕ 7), and the order-3 automorphism τ + S₃. The acceptance test that makes it
real and ties it to the framework: **Fix(τ) = g₂, dim 14** (the D₄→G₂ fold = the A–N 14).
Deterministic → clean MCP surface, new symbols → no ABI bump, rc-first. Unblocks the
F182 triality-shadow path, starting with R-140: is su(2)_L a triality partner of
su(3)/u(1)? — the test that decides whether F181's plural drivers re-unify (H177″) or
stand. We hand the spec over; we do not edit the package.*
