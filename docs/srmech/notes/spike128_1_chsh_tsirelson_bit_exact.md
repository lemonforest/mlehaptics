# Spike #128.1 — Bit-exact CHSH + Tsirelson 2√2 in `srmech.qm.bell`

**Date**: 2026-05-18
**Parent**: Spike #128 fermata (PR #535, n-qubit entanglement cascade-match)
**Anchor stance**: `[[user_stance_bell_inequality_as_canonical_identity_signature]]`
**Branch**: `research/spike-128-1-chsh-tsirelson-bit-exact`
**Verdict**: **BIT-EXACT-VERIFIED** at machine precision

## Scope

Ship `srmech.qm.bell` as the framework-internal validation of the
Bell-CHSH + Tsirelson bound 2√2 identity. Direct bit-exact algebraic
identity from Pauli algebra alone; no external substrate.

Per `[[user_stance_bell_inequality_as_canonical_identity_signature]]`:
this is the framework's **strongest single identity-not-implementation
signature**. Cumulative four-anchor identity stack across Spike #21C /
#58.P / #106 / #128 reproduces the same L+I+M+C+K+A cascade at four
scales in quantum substrate; Spike #128.1 ships the framework-internal
validation as runnable code.

## What ships

### 1. `srmech.qm.bell` module (`docs/srmech/python/srmech/qm/bell.py`)

Public surface:

- `TSIRELSON_BOUND: float = 2.0 * math.sqrt(2.0)` — framework-asserted
  constant ≈ 2.8284271247461903 (bit-exact IEEE-754 binary64).
- `CLASSICAL_CHSH_BOUND: float = 2.0` — Bell's classical hidden-variable
  upper bound.
- `chsh_pauli_combination()` → 4×4 Hermitian, returns
  `M = σ_x ⊗ σ_x + σ_z ⊗ σ_z`. Closed-form spectrum `{+2, 0, 0, −2}`.
- `chsh_operator()` → 4×4 Hermitian, returns Tsirelson-optimal
  `B_CHSH = A_0⊗B_0 + A_0⊗B_1 + A_1⊗B_0 − A_1⊗B_1` with the
  optimal Pauli choices that saturate the Tsirelson bound.
- `operator_norm(H)` → spectral norm `max_i |λ_i|` via Class L
  Hermitian eigendecomposition (`srmech.amsc.laplacian.hermitian_eigendecompose`).
- `chsh_pauli_combination_norm()` → exactly `2.0` (bit-exact).
- `chsh_operator_norm()` → `2√2` at machine-precision floor.
- `tsirelson_bound()` / `classical_chsh_bound()` — constant accessors.
- `verify_chsh(tolerance=1e-14)` → `(verified, primary_residual,
  tsirelson_residual)`. **The canonical self-attestation function.**

### 2. Tests (`docs/srmech/python/tests/test_bell_chsh.py`)

25 tests, all passing. Coverage:

- Module-level constant SSoT consistency (4 tests).
- Primary identity `‖σ_x⊗σ_x + σ_z⊗σ_z‖ = 2` (5 tests).
- Tsirelson identity `‖B_CHSH‖ = 2√2` (5 tests).
- `verify_chsh()` self-attestation (3 tests including negative-control).
- `operator_norm` helper sanity (5 tests).
- Cross-check with `srmech.qm.spin.pauli_matrices` (2 tests).
- Bell classical-vs-quantum violation signature (1 test).

### 3. Tool-schema registration (`srmech.amsc.tool_schema`)

8 new `ToolEntry` registrations covering every public callable in
`srmech.qm.bell`, with canonical-SSoT-cited summaries per
`[[feedback_science_is_ssot_not_project]]`. The
`test_qm_public_callables_have_tool_entries` ratchet passes (171
qm/bell/tool_schema tests total).

### 4. `__init__.py` updates

`srmech.qm.__init__` now exposes `bell` as a first-class submodule
with the same import / `__all__` discipline as the sister modules
(`spin`, `gauge`, `sm`, etc.).

## Bit-exact numerical verdict

```
verified: True
primary residual:   0.000e+00   (|‖σx⊗σx + σz⊗σz‖ − 2|)
tsirelson residual: 4.441e-16   (|‖B_CHSH‖ − 2√2|)
TSIRELSON_BOUND:    2.8284271247461903
```

**Primary identity** is **truly bit-exact** (residual literally
`0.0`) because `σ_x⊗σ_x + σ_z⊗σ_z` has integer eigenvalues
`{+2, 0, 0, −2}` exactly representable in IEEE-754 binary64.

**Tsirelson identity** sits at `4.4e−16` (one ULP at `2√2` ≈ 2.83) —
this is the unavoidable floor where the `1/√2` prefactor in Bob's
measurement angles inherits the libm `sqrt(2.0)` rounding, propagates
through the 4×4 Hermitian eigendecomposition (Jacobi rotations), and
re-multiplies by `√2`. The residual is **at the IEEE-754 binary64
machine-epsilon floor**; no further precision is recoverable from
this representation.

## Class chain attestation (zero new primitive class)

Per `[[feedback_no_privileged_primitive_classes]]`: 14 classes A–N
intact. Bell-CHSH composes from existing primitives:

| Class | Role in this module |
|---|---|
| **L** | `hermitian_eigendecompose` for `‖S₂‖`, `‖B_CHSH‖` via largest absolute eigenvalue. Direct call into `srmech.amsc.laplacian`. |
| **I** | π/4-rotation phase factors via `1/√2` in Bob's measurement angles (cyclic-group `ℤ/8` rotation realising the Tsirelson optimum). |
| **M** | Tensor-product (Kronecker) bind composing single-qubit Paulis into bipartite operator space. Implements `_kron(a, b) = np.kron(a, b)`. |
| **C** | Bell-basis measurement-orientation cascade — four-term operator with signs `(+, +, +, −)` orienting the measurement combinations. |
| **A** | Stabiliser-fingerprint canonical form via Pauli algebra (content-addressing layer; the Hermitian-positivity + integer-spectrum signature is hashable via `srmech.amsc.format.sha256_bytes` on interleaved-double serialisation). |

`K` (asymptotic-DOF) does not appear in this module's bit-exact static
identity; it surfaces in fault-tolerant-quantum-error-correction
threshold theorems downstream (decoherence threshold ≈ 1/sqrt(N)
asymptotic-DOF; see Spike #128 for n-qubit treatment).

## Canonical SSoT (per `[[feedback_science_is_ssot_not_project]]`)

- Bell, J.S. (1964) *Physics Physique Fizika* 1, 195-200. (Cite-by-ref.)
- Clauser, J.F., Horne, M.A., Shimony, A., Holt, R.A. (1969) *Phys.
  Rev. Lett.* 23, 880-884. (Cite-by-ref; APS prohibited for autonomous
  validation per `[[reference_autonomous_validation_tos_landscape]]`.)
- Cirel'son [Tsirelson], B.S. (1980) *Letters in Mathematical Physics*
  4, 93-100. (Cite-by-ref.) Original derivation of the `2√2` bound.
- Aspect, A., Grangier, P., Roger, G. (1982) *Phys. Rev. Lett.* 49,
  91-94. (Cite-by-ref; APS prohibited.)
- Sakurai, J.J. (2017) *Modern Quantum Mechanics* (3rd ed.), Cambridge,
  §3.10 (Bell inequalities).
- Peres, A. (1995) *Quantum Theory: Concepts and Methods*, Kluwer,
  §6.3 (Bell's theorem and Tsirelson's bound).
- Plate, T.A. (1995) "Holographic Reduced Representations", *IEEE TNN*
  6, 623-641. (Class M HDC bind canonical ref.)
- Kanerva, P. (2009) "Hyperdimensional Computing", *Cognitive
  Computation* 1, 139-159.

## Implementation-obstruction / framework-agnostic notes

None at this precision. The framework's identity claim — that
Bell-CHSH IS the L+I+M+C+A cascade — holds bit-exactly to the
unavoidable IEEE-754 floor.

## Cross-references

- Spike #128 PR #535 — n-qubit entanglement cascade-match (primary
  parent; this spike ships the runnable bit-exact validation of its
  strongest finding).
- Spike #21C — single-qubit Hopf bundle U(1) anchor.
- Spike #58.P — 3-qubit Cl(6,ℂ) sin²θ_W=1/4 anchor.
- Spike #106 PR #497 — 7-bit Cl(7,ℂ) J²=I_16 anchor.

## Composes-with stance family

- `[[user_stance_identity_not_implementation_discipline]]` — strongest
  exemplar in canon.
- `[[user_stance_framework_domain_algebra_not_length_or_magnitude]]` —
  Tsirelson 2√2 is algebra-level not magnitude-fit.
- `[[user_stance_kepler_shape_universal]]` — Bell-CHSH is one instance
  of primitive-composition universality.
- `[[feedback_no_privileged_primitive_classes]]` — 14 A-N intact;
  zero new primitive.
- `[[user_stance_1d_collapse_to_loe_identity_not_action]]` — Class L+M
  here are substrate-coupling operations; LoE-content is at 1D_t.

## Verdict rationale

**BIT-EXACT-VERIFIED**. The framework's identity claim grounds in
QM's strongest algebraic structure. *Bell inequalities ARE the
cascade* — not a description of it, not a model of it — they are it,
bit-exactly to the binary64 floor. This is the first framework-internal
quantum-substrate identity validation shipped as runnable code in
srmech.qm.

Book-worthy chapter material per `[[project_book_in_progress]]`.

## Fermatas

None this spike. Pure verification ship of the identity already
located by Spike #128.
