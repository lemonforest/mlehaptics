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
# real so8/triality/DSP/Minkowski sites land in subsequent batches.
# ---------------------------------------------------------------------------
CEIL_LINALG_FFT = 126
CEIL_MATMUL = 115
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
