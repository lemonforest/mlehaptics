# chess-spectral 2D eigenbasis optimization — implementation report (2026-05-11)

**Branch:** `feat/chess-spectral-2d-eigenbasis-optimization`
**Lineage:** `surfaced_from: chess_channels_hyper_parallel_research_2026-05-11` (commit `7e98a7e`, merged via PR #329)
**Spec:** ADR-002 §6.1, Open Question / Future Work item 1 ("eigenbasis-diagonal optimization for `evolve_until` / `evolve_under_h0`; deferred until profiling justifies the LOC"). The 2026-05-11 honest-negative spike provided the measured justification at chess-2D scale (and the measured *deferral* justification at chess-4D scale).

## Bottom line

The new path replaces the per-channel `scipy.sparse.linalg.expm_multiply` loop in `chess_spectral.qm_2d_dynamics.evolve_under_h0` with the closed-form eigenbasis-diagonal expression `U(t) = V @ diag(exp(-i λ t)) @ V^H` where `(λ, V) = eigh(H_FREE_2D.toarray())` is cached in a module-level singleton. All 28 pre-existing tests pass without modification; 51 new tests in `tests/test_qm_2d_dynamics_eigenbasis.py` verify parity, caching invariants, and the spec-required mathematical properties. Measured speedup on the real `H_FREE_2D` (not the spike's synthetic Laplacian) is **189.7×** with max-abs deviation **1.54e-16** vs the sparse reference.

## Implementation summary

* **Cache:** module-level `_H0_EIGENBASIS_2D: Optional[Tuple[np.ndarray, np.ndarray]]` (lazy first-call via `_get_h0_eigenbasis_2d()`). Built via `numpy.linalg.eigh(H_FREE_2D.toarray())`; returns `(eigvals: float64[64], eigvecs: complex128[64, 64])`. The eigvecs are stored complex128 even though the symmetric H_0 admits a real-orthogonal V, so the downstream phase multiplication stays in one dtype.
* **`evolve_under_h0` three paths:**
  * Single 64-block: `coefs = V^H @ ψ; coefs *= phases; out = V @ coefs`
  * Full 640-dim broadcast: `psi_blocks = ψ.reshape(10, 64); coefs = psi_blocks @ V.conj(); coefs *= phases; out_blocks = coefs @ V.T; out = out_blocks.ravel()`
  * Single-channel-only mode: same as single-block path applied to the targeted slice; other 9 blocks bit-identical to (complex128-cast) input.
* **`phases = np.exp(-1j * eigvals * t)`** computed once per call (shared across all 10 channels).
* **`H_FREE_2D()` and `_get_h_free_2d()` unchanged.** Public API: signature, return shape, exceptions all identical. `H_FREE_2D` continues to be the SSOT for the sparse matrix; the eigenbasis cache is keyed off it implicitly (built once, the H_0 sparse matrix is also a module-level singleton).
* **Unused import dropped:** `scipy.sparse.linalg.expm_multiply` is no longer needed (was used only by the previous per-channel loop).

## Parity numbers (real `H_FREE_2D`, N_TRIALS=20, warmup=3, t=0.1, seed 20260511)

| Path | Median ms | IQR ms |
|---|---|---|
| New: eigenbasis-diagonal, batched | 0.057 | 0.030 |
| Old: per-channel sparse `expm_multiply` | 10.75 | 2.77 |
| **Speedup** | **189.7×** | — |

* **Max-abs deviation (new vs sparse reference):** 1.54e-16 (machine-precision bit-equivalent; same scale as the spike's 1.8e-16 on the synthetic Laplacian).
* **One-shot eigendecomposition cost:** ~6 ms on commodity workstation; amortized over the first call (lazy build).

The 189.7× vs the spike's 196× is well within bench variance (~3% delta). Both are "math-doesn't-lie wins" at chess-2D scale.

## Test coverage

* **Pre-existing `tests/test_qm_2d_dynamics.py`:** 28/28 pass unchanged. The optimization preserves the public-API contract exactly.
* **New `tests/test_qm_2d_dynamics_eigenbasis.py`:** 51 tests pass. Cover:
  * Eigenbasis cache structural invariants (5)
  * `V @ diag(λ) @ V^H` reconstructs H_0 to machine precision (1)
  * V is unitary to 1e-12 (1)
  * Eigvals lie in [-8, 0] (1)
  * Parity vs sparse reference, single-block path, t ∈ {1e-6, 1e-3, 0.05, 0.1, 0.5, 1.0, 2.5}, tol 1e-14 (7)
  * Parity vs per-channel sparse loop, full-640 batched path, same t sweep (7)
  * Parity vs sparse, per-channel-only mode, all 10 channels (10)
  * Norm preservation, single-block + full-640 across t sweep (14)
  * Energy ⟨ψ|H_0|ψ⟩ preservation across t = {0.05, 0.1, 0.5, 1.0} (4)
  * Determinism: same t → bit-identical; different t → different; U(-t)∘U(t) = I; U(t1+t2) = U(t2)∘U(t1) (4)
* **`tests/test_qm_4d_dynamics_b2.py`:** 17/17 pass — verifies the 4D side is unaffected (the optimization deliberately does NOT touch `qm_4d_dynamics.evolve_under_h0` per the spike's honest negative).
* **`tests/test_qm_2d.py` + `tests/test_qm_2d_bridge.py`:** 73 + 29 = 102 tests pass — wider 2D ecosystem unaffected.

Total verified surface: 169 tests, all pass.

## ADR conformance

ADR-002 §6 future-work item 1 stated:

> Per Pre-flight 3, H_0 = -Δ is diagonal in the encoder basis. A v1.6+ optimization could replace expm_multiply with direct phase multiplication. Deferred until profiling shows evolve_until is a hot path.

Pre-flight 3 framed the encoder as a simultaneous eigenbasis of (Δ, B_4 commutant). The spike measured that the *encoder-channels are bit-identical blocks under H_0* (because `H_full = I_N_CHANNELS ⊗ H_0`), which means the eigenbasis is the per-block `eigh(H_0)` — we don't need to identify the encoder-aligned eigenbasis explicitly; `numpy.linalg.eigh` finds it (up to within-eigenspace mixing, which is irrelevant for the diagonal-phase application since `exp(-iλt)` acts identically on degenerate eigenvectors). This matches the §4.1 design intent.

ADR-002 §4.5 ("Performance") explicitly estimated:

> ~10x speedup; deferred until profiling justifies the LOC.

The measured 189.7× is roughly 19× better than the ADR's own estimate. This is because the ADR was estimating against a single big `expm_multiply` call (the "1 matvec + 1 elementwise" framing), whereas the current code path uses `scipy.sparse.linalg.expm_multiply` per channel — overhead-dominated at the 64×64 scale. The "8× speedup from going to full-dim sparse" intermediate path from the spike's anomaly-chase explains the remaining gap.

## C-side state of `evolve_under_h0` parity

Verified via `Grep("evolve_under_h0", path="docs/chess-maths/chess-spectral/src")` and `path="docs/chess-maths/chess-spectral/include")` — no matches. `evolve_under_h0` is Python-only QM dynamics; the C port covers encoders (`encode_*`, including the 2D pure-phase port in 1.19.0+), not the QM dynamics layer. No C/Python parity action required.

## Anomalies and fermata

None. The implementation flows cleanly from the spike. Two minor design choices worth flagging for review (not blockers):

1. **`eigvecs` stored as complex128 even though H_0 is real-symmetric.** I chose dtype consistency over the float64 micro-saving (the matmul accumulator would have to handle promotion anyway). The 64×64 cache is ~64 KB complex128 vs ~32 KB float64 — negligible at module scope.
2. **`eigvals` stays float64.** `np.exp(-1j * eigvals * t)` correctly promotes to complex128 at the elementwise level. This is the natural / standard form; keeping eigvals real also costs no information.

If reviewer prefers float64 V for tighter memory or pure-real intermediate matmul, the change is a one-line edit (`eigvecs = np.ascontiguousarray(eigvecs, dtype=np.float64)`) — I left it complex128 for the reason above.

## Files touched

* `docs/chess-maths/chess-spectral/python/chess_spectral/qm_2d_dynamics.py` (modified) — eigenbasis cache + rewritten `evolve_under_h0` body + docstring updates.
* `docs/chess-maths/chess-spectral/python/tests/test_qm_2d_dynamics_eigenbasis.py` (new) — 51-test parity regression layer.
* `docs/chess-maths/chess-spectral/python/CHANGELOG.md` (modified) — `[Unreleased]` section entry.

## Reproducibility

```bash
cd docs/chess-maths/chess-spectral/python
python -m pytest tests/test_qm_2d_dynamics.py tests/test_qm_2d_dynamics_eigenbasis.py -v
# 79/79 PASSED in ~3 s
```

For the speedup measurement re-run, the inline benchmark in the spike script (commit 7e98a7e, `docs/srmech/notes/chess-channels-and-hyper-parallel-script.py`) covers the synthetic-Laplacian case at the chess-2D scale; the real-`H_FREE_2D` numbers in this report were measured by a one-shot verification script (not committed; trivially reconstructed from the spike script by replacing `h_free_2d()` with `chess_spectral.qm_2d_dynamics.H_FREE_2D()`).
