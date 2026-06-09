"""numpy-math ratchet — the down-only guard that keeps numpy a *carrier*, not a
*math engine* (#928; user direction 2026-06-08).

The discipline: **all math runs through srmech cascades; numpy is only ever for
vector packing** (array creation / dtype / shape / slicing / the ctypes bridge).
numpy bundles a full math engine alongside its carrier — ``np.linalg.*``,
``np.fft.*``, the ``@`` matmul, the transcendental ufuncs. Every one of those is
libm-at-the-array-level and has (or will have) a srmech cascade equivalent that
rides the libm-free C core. A stray ``np.linalg.solve`` is therefore a *defect*,
not a convenience — the same class of defect the C-transpile arc drove out of
``libsrmech`` (libm 23 → 0).

This test is the down-only debt ledger for that goal — a sibling of the libm
C-transpile ratchet and the Rosetta-completeness ratchet. It greps the srmech
**source** (carriers + math, but NOT the tests) for numpy-math callsites in three
categories and pins each at a ceiling that only ever moves **down**:

  * ``linalg_fft`` — ``np.linalg.*`` / ``np.fft.*`` (solve / svd / qr / eig /
    lstsq / inv / fft / …): the heavy-engine surface.
  * ``matmul``     — the ``@`` / ``@=`` operator, ``.dot(``, and
    ``np.{matmul,einsum,kron,convolve,correlate,outer,tensordot,vdot,inner,
    cross}``: the contraction surface.
  * ``ufunc``      — ``np.{sin,cos,tan,exp,log,sqrt,sign,abs,arctan,power,…}``:
    the transcendental / sign surface (the Python-tier residue of the C-transpile
    arc — ``libsrmech`` is already libm-free, the scientific tier is not yet).

To close debt: route a callsite through the srmech cascade that already backs it
(``laplacian.dense_solve`` / ``dense_matvec_complex``, the ``cascade.fft`` /
``dft`` family, ``rational.{sin,cos,exp,sqrt}`` / the trig cascade, …), then
**lower the matching ceiling to the new exact count**. The ceilings are TIGHT
(``== ceiling``, not ``<=``) for the same reason the Rosetta ratchet is: a count
*below* the ceiling means a callsite was removed without updating the ledger;
a count *above* means numpy math was added where a cascade belongs — which is
exactly the regression this guard exists to forbid.

Carrier ops (``np.zeros`` / ``np.asarray`` / ``np.ascontiguousarray`` /
``reshape`` / ``.T`` / elementwise ``+ - *`` on arrays / indexing) are NOT
counted — those are legitimate vector packing.

Reductions (``np.sum`` / ``np.mean`` / ``np.prod`` / ``np.cumsum`` …) sit on the
carrier⇄math boundary and are a DEFERRED category — not yet pinned here; revisit
when the three engine surfaces above approach zero.

The regex is run over the source TEXT (not via ``tokenize``), so the counts are
identical across CPython 3.10–3.14 — ``tokenize``'s f-string handling changed in
3.12 and would make the ledger version-dependent.
"""
from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# The srmech source tree (carriers + math). Tests live in a sibling dir and are
# intentionally NOT scanned.
# ---------------------------------------------------------------------------
SRMECH_PKG = Path(__file__).resolve().parent.parent / "srmech"

_LINALG_FFT = re.compile(r"\b(?:np|numpy)\.(?:linalg|fft)\.")
_MATMUL_PATTERNS = (
    re.compile(r" @[ =]"),  # binary ``a @ b`` / ``a @= b`` (decorators are ``@name`` — no space)
    re.compile(
        r"\b(?:np|numpy)\.(?:matmul|einsum|kron|convolve|correlate|outer"
        r"|tensordot|vdot|inner|cross)\b"
    ),
    re.compile(r"\.dot\("),  # ``np.dot(`` and ``x.dot(``
)
_UFUNC = re.compile(
    r"\b(?:np|numpy)\.(?:sin|cos|tan|exp|expm1|log|log1p|log2|log10|sqrt|cbrt"
    r"|sign|abs|absolute|arcsin|arccos|arctan|arctan2|power|float_power|hypot"
    r"|square|reciprocal)\("
)

# ---------------------------------------------------------------------------
# DOWN-ONLY ceilings. Lower (never raise) the matching one when a callsite is
# routed through a srmech cascade. Baseline pinned at v0.7.5rc13 after the lmmse
# solve+matvec migration (decrement #1: -1 linalg, -1 matmul); rc16 routed the 5
# dense complex 2-D matmuls in matrix_cascades.py (qr/svd/lstsq/eigvals internals)
# through dense_matmul_complex (matmul 185 -> 180); rc17 routed qm.single_particle's
# 12 contractions (commutator + TDSE/Heisenberg/Liouville U·…·Uᴴ) onto the
# dense_matmul/matvec cascades (matmul 180 -> 168); rc18 routed qm.spin (15 Pauli
# products) + qm.gauge (6 — Lie-algebra commutator/Casimir/Wilson) through
# dense_matmul_complex (matmul 168 -> 147); rc19 routed qm.relativistic's 9
# gamma-matrix products + qm.pseudo_hermitian's 3 (Oᴴη/ηO + V·Vᴴ) onto the
# matmul cascade (matmul 147 -> 135); rc20 added the dense_dot_complex bilinear
# helper (Σ aᵢbᵢ via elementwise-multiply + reduction) and routed the complex
# matvec/dot/sandwich sites onto the matvec + dot cascades — qm.pseudo_hermitian's
# 3 η-sandwiches (⟨a|η|b⟩, ⟨ψ|ηO|ψ⟩, ⟨ψ|η|ψ⟩ = 7 `@` tokens), heat_kernel's 2
# eigenbasis matvecs, spectral's 2 decompose/recompose matvecs, and music's
# Enᴴ·A noise-subspace matmul (matmul 135 -> 123). The remaining real-typed
# (so8 / triality / octonion-DFT / Minkowski / DSP) sites await a real-matmul +
# real-matvec cascade; the matrix_cascades QR-internal vdot/back-solves await a
# shape-polymorphic pass; rc21 introduced the real-matmul cascade trio
# (dense_matmul_real / dense_matvec_real / dense_dot_real = the complex kernel on
# imag-free input, .real → float64) and routed hypercomplex_dft's 8 octonion-rep
# (8×8 real) matvecs onto dense_matvec_real (matmul 123 -> 115). The remaining
# real so8/triality/DSP/Minkowski sites land in subsequent batches; rc22 routed
# qm.triality's 7 real products (octonion-rep matvecs + the 28×28 tau=S_B·S_C /
# tau² / tau³ matmuls) onto dense_matmul_real/dense_matvec_real and reworded the
# 3 docstring `@` to `·` (matmul 115 -> 105); rc23 routed qm.so8's 17 sites —
# 15 real (commutators, su(3)/g₂ Gram products, basis-projection matvecs,
# Gram-Schmidt dot) onto dense_matmul_real/matvec_real/dot_real, and 2 COMPLEX
# (the su(3)-weight Rayleigh quotients vᴴv / vᴴ·ad·v on the complex eigenvectors
# of the real ad(H)) onto dense_dot_complex/dense_matvec_complex (matmul
# 105 -> 86). The 2 np.kron stay (different op). Minkowski / DSP real sites next.
# rc24 routed the real "Minkowski + real-dot" sweep — qm.relativistic's eta@k
# matvec + np.dot(k_spatial,k_spatial) + the kᵀηk bilinear, qm.propagators' eta@k
# matvec, and the amsc real Class-L inner products (harmonics _spectral_scores'
# 3 ⟨x,·⟩ symmetry probes + hdc loop_inv / loop_inv_hd / g2_three_form ⟨·,·⟩
# norms) onto dense_matvec_real / dense_dot_real (matmul 86 -> 75). The amsc
# helpers import dense_dot_real function-locally to keep harmonics/hdc
# numpy-absent-safe (§22). Remaining real sites: the DSP closed_form_ops +
# matrix_cascades QR-internal vdot/back-solves; then np.outer/kron/einsum
# (distinct ops, own cascades).
# rc25 routed the real DSP closed_form_ops cluster — dct (M·arr / arr·Mᵀ DCT
# matrix products), map_ml (the AᵀR⁻¹A normal-equation matmuls + matvecs; the
# np.linalg.inv/solve stay), ica_jade (the Xᵀ·X covariance + whitening/Givens
# rotation matmuls; the 2 np.einsum + np.linalg.eigh stay) — onto
# dense_matmul_real / dense_matvec_real, plus fsk's complex tones·conj(window)
# correlator-bank matvec onto dense_matvec_complex (matmul 75 -> 60). These DSP
# modules import numpy at module top, so the helper import is top-level here
# (unlike the lazy-numpy amsc modules). Remaining: sinc_interp / vector_quant /
# farrow / esprit (dtype-verify each), the matrix_cascades QR-internals, then
# np.outer / kron / einsum / convolve / correlate (distinct ops, own cascades).
# rc26 routed the genuine-code tail of the dense-matmul migration — vector_quant's
# real vec·cbᵀ codebook product, sinc_interp's COMPLEX K·y (y is complex128 IQ →
# dense_matvec_complex, NOT real), farrow's real Lagrange C[k]·x fractional-delay
# dot, and qm.potentials' a†·a number-operator + qm.sm's V·Vᴴ CKM-unitarity (both
# complex) (matmul 60 -> 55). The remaining ~55 are NOT genuine dense-matmul code:
# ~16 are docstring/comment/summary-string `@` mentions (spectral / mimo_svd /
# heat_kernel / tool_schema / lmmse / esprit / profile_loader — a cosmetic `·`
# reword sweep), and ~25 are distinct ops needing their OWN cascades (np.convolve
# in fir/polyphase/multirate, np.correlate in matched_filter, np.kron in so8,
# np.outer in propagators, np.einsum in ica_jade). The dense-matmul-migration
# floor is essentially reached; further matmul reduction is reword-sweep +
# distinct-op cascades (separate work items). The laplacian Schur `L_pi·X` is
# deferred (in-helper, shape-polymorphic — its own careful pass).
# rc27 OPENS the linalg_fft decrement (pinned at 126 since rc13): the dense-matmul
# floor reached, the arc pivots to np.linalg/np.fft → cascade. Per user direction
# (cascade + TOML for ALL maths; numpy is a carrier only, with the carrier itself
# removed as the FINAL step AFTER the maths sweep), the cascades REPLACE numpy math
# even where not bit-exact — fft (radix-2) / svd (Gram-route) / qr (Householder) /
# eig (Jacobi) are round-off-faithful to numpy (~1e-14), not bit-identical, and
# that within-tolerance shift is accepted; any bit-equality-vs-numpy test relaxes
# to a tolerance. rc27 routes the linear-solve family: map_ml's 2 np.linalg.solve →
# dense_solve (bit-exact for the 1-D RHS both sites have) + triality/esprit's
# np.linalg.lstsq → matrix_cascades.lstsq (round-off-faithful, complex-safe; the
# bare-ndarray return replaces numpy's 4-tuple, so the callsite unpack changed)
# (linalg_fft 126 -> 122). NOT migrated: the cascade ops' OWN internal numpy
# kernels (laplacian eigh/solve — designated Class-L impls with pure-Python
# fallbacks; a deeper separate pass) and the docstring/ToolEntry-summary
# `numpy.linalg.*` cross-reference MENTIONS (precise docs — left intact, not gamed).
# Next: np.fft (n/axis handling) + np.linalg.svd/qr/eigvals + inv/pinv.
#
# rc28 EXACTIFIES the dft/fft cascade (no ratchet movement — counts unchanged).
# Per the sharpened user direction ("don't use floats for bit-exact math, that's
# what ints and complex are for; floats are for FPU lift"), the dft/fft cascade
# now routes an all-integer / Gaussian-integer power-of-two signal through an
# exact cyclotomic-integer engine (ℤ[ζ_N], ζ^{N/2}=-1 Class-K sign-flip → pure
# integer add/subtract) with ONE FPU lift at the end — exact-until-rotation, MORE
# faithful than a float FFT (which rounds every butterfly). This is the FIRST
# exact cascade and a correction to rc27's "round-off-faithful is fine" framing
# for the integer case. It adds NO numpy, NO public surface (private engine
# srmech.amsc.cascade.exact_dft), so all three ceilings (linalg_fft/matmul/ufunc)
# AND the rosetta python_only_irreducible debt bucket are untouched. Exposing the
# exact ℤ[ζ_N] spectrum as a public op belongs with its C twin (a follow-up).
# ---------------------------------------------------------------------------
CEIL_LINALG_FFT = 122
CEIL_MATMUL = 55
CEIL_UFUNC = 48


def _count_category() -> dict[str, int]:
    counts = {"linalg_fft": 0, "matmul": 0, "ufunc": 0}
    for path in sorted(SRMECH_PKG.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        counts["linalg_fft"] += len(_LINALG_FFT.findall(text))
        counts["matmul"] += sum(len(p.findall(text)) for p in _MATMUL_PATTERNS)
        counts["ufunc"] += len(_UFUNC.findall(text))
    return counts


def _per_file_breakdown() -> str:
    rows = []
    for path in sorted(SRMECH_PKG.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        lf = len(_LINALG_FFT.findall(text))
        mm = sum(len(p.findall(text)) for p in _MATMUL_PATTERNS)
        uf = len(_UFUNC.findall(text))
        if lf or mm or uf:
            rows.append((lf + mm + uf, lf, mm, uf, str(path.relative_to(SRMECH_PKG))))
    rows.sort(reverse=True)
    return "\n".join(
        f"    {lf:3d} linalg/fft  {mm:3d} matmul  {uf:3d} ufunc   {name}"
        for _tot, lf, mm, uf, name in rows
    )


def test_numpy_math_ledger_is_tight():
    """Each engine-category count equals its down-only ceiling.

    A count ABOVE ceiling → numpy math was added where a srmech cascade belongs
    (the regression this guard forbids). A count BELOW ceiling → a callsite was
    migrated but the ceiling wasn't lowered — lower it to the new exact count.
    """
    counts = _count_category()
    ceilings = {
        "linalg_fft": CEIL_LINALG_FFT,
        "matmul": CEIL_MATMUL,
        "ufunc": CEIL_UFUNC,
    }
    mismatches = {k: (counts[k], ceilings[k]) for k in ceilings if counts[k] != ceilings[k]}
    assert not mismatches, (
        "numpy-math ledger drift "
        + ", ".join(
            f"{k}: live={live} ceiling={ceil}" for k, (live, ceil) in mismatches.items()
        )
        + ".\n  ABOVE ceiling → route the new callsite through a srmech cascade "
        "(numpy is carriers-only, never the math engine).\n  BELOW ceiling → you "
        "migrated a callsite; lower the matching CEIL_* to the new exact count.\n"
        "  Current per-file breakdown:\n" + _per_file_breakdown()
    )


def test_numpy_math_total_is_down_only():
    """The grand total is at or below the pinned sum (a coarse safety net)."""
    counts = _count_category()
    total = sum(counts.values())
    ceil_total = CEIL_LINALG_FFT + CEIL_MATMUL + CEIL_UFUNC
    assert total <= ceil_total, (
        f"numpy-math total {total} exceeds pinned {ceil_total}; a cascade op "
        "regressed to numpy math. Per-file breakdown:\n" + _per_file_breakdown()
    )
