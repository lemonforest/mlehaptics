"""Quaternion / octonion discrete Fourier transforms — the native transform
for a Klein-4 object (#863, F380).

A **Klein-4 object** (the 4-state-per-coordinate HDC object srmech ships as
``hdc.klein4_*`` — the two chirality axes γ₅ and iω₇, ``Z₂×Z₂``) has two
``Z₂`` axes. The only Fourier op otherwise shipped is the **complex**
``signal_processing.closed_form_ops.fft`` (the ``k=1`` / ``S¹`` rung).
Fourier-analysing a Klein-4 object with a *complex* FFT first projects it to
``ℂ``, which collapses one of its two ``Z₂`` axes — we see only **the flat
shadow**.

The fix is exact, not analogical (F380):

    The Klein-4 group IS the quaternion units modulo sign.
    Q₈ = {±1,±i,±j,±k}, centre {±1}, and  Q₈/{±1} ≅ Z₂×Z₂ = Klein-4.

So the coefficient algebra of each FFT-ladder rung carries a different
chirality content (F379, "n things with n−1 couplings"):

    transform       coeff. algebra   units mod sign        chirality resolved
    complex FFT      ℂ                {±1,±i}/± = Z₂        one axis (flat shadow)
    quaternion FT    ℍ                Q₈/± = Z₂×Z₂          BOTH axes (γ₅ & iω₇)
    octonion FT      𝕆                the (8:7) rung        + F378 non-associativity

A quaternion FT's coefficient algebra **matches** the Klein-4 object's value
algebra, so both chirality axes survive — exactly what an RBS-SNN Klein-4
object needs and what the complex FFT cannot give.

**These are COMPOSITES, not a new primitive class** — they compose the
existing ``srmech.qm.octonion`` left/right-multiply atoms (the
non-commutativity of ``ℍ`` / ``𝕆`` is load-bearing: there are genuinely
**left- / right- / two-sided** forms; the twiddle cannot be factored out the
way the complex FFT does) with the scalar twiddle ``exp(μθ)=cos θ + μ·sin θ``.
The 14-class A–N vocabulary is intact (``[[feedback_no_privileged_primitive_classes]]``).
No ``abs()`` — the octonion norm/conjugate route through Class K+C, never an
ALU absolute value.

**Scientific tier (UPSTREAM §22).** numpy is imported **lazily inside each
op**, so ``import srmech.amsc.cascade`` stays numpy-free (the numpy-absent-safe
core, v0.7.0rc30); the qm-algebra transforms use numpy on call, consistent
with §22 ("leaving numpy for the python-side triality/qm maths is correct").
Calling a transform with numpy absent raises a clear ``ImportError``.

This is the **prototype tier** per #863: a composite over existing primitives.
A graduation to a first-class C/Python primitive (a native ``srmech_*_dft``
symbol like the existing ``fft``) is a separate, later voxel.

Citations (verified PDFs —
``docs/srmech/notes/qdft_odft_citation_verification_863.md``):
- QDFT: Sangwine, S. J. & Ell, T. A. (2012). *Complex and Hypercomplex
  Discrete Fourier Transforms Based on Matrix Exponential Form of Euler's
  Formula.* Appl. Math. Comput. 219(2):644–655. arXiv:1001.4379.
- ODFT: Błaszczyk, Ł. (2019). *A Generalization of the Octonion Fourier
  Transform to 3-D Octonion-Valued Signals.* arXiv:1905.12631. Origin:
  Hahn, S. L. & Snopek, K. M. (2011). *The unified theory of n-dimensional
  complex and hypercomplex analytic signals.* Bull. Polish Acad. Sci. Tech.
  Sci. 59(2):167–181.
"""
from __future__ import annotations

import math
from typing import List, Sequence

from srmech.amsc.rational import sqrt as _rsqrt  # §22: scalar root via Class-N, not libm

# Unit pure-imaginary quaternion axes (μ² = −1). The twiddle lives in the
# commutative subalgebra ℝ[μ] ≅ ℂ, which is WHY the one-sided transform is
# invertible: Σ_k exp(μ·2πk(n−n')/N) = N·δ_{n,n'} (geometric series in ℝ[μ]).
_MU_AXES = {
    "i": (0.0, 1.0, 0.0, 0.0),
    "j": (0.0, 0.0, 1.0, 0.0),
    "k": (0.0, 0.0, 0.0, 1.0),
}
# The body-diagonal unit axis (i+j+k)/√3 — the order-3 (triality-adjacent)
# pure-quaternion direction; still μ²=−1.
_S3 = 1.0 / _rsqrt(3.0)
_MU_AXES["ijk"] = (0.0, _S3, _S3, _S3)

_FORMS = ("left", "right")
_OCTONION_FORMS = ("left", "right", "two_sided")
_BRACKETINGS = ("left_associated", "right_associated")


def _require_numpy():
    """Lazy numpy import (scientific tier, §22). Raises a clear error if absent."""
    try:
        import numpy as _np
    except ImportError as exc:  # pragma: no cover - exercised in numpy-absent CI only
        raise ImportError(
            "quaternion_dft / octonion_dft are scientific-tier qm-algebra ops "
            "and require numpy (UPSTREAM §22: numpy stays for the python-side "
            "qm maths). Install srmech with numpy available."
        ) from exc
    return _np


def _twiddle8(theta: float, mu: Sequence[float], np):
    """``exp(μθ) = cos θ·1 + sin θ·μ`` as an 8-vector in the ℍ ⊂ 𝕆 subalgebra."""
    c = math.cos(theta)
    s = math.sin(theta)
    w = np.zeros(8, dtype=float)
    w[0] = c
    w[1] = s * mu[1]
    w[2] = s * mu[2]
    w[3] = s * mu[3]
    return w


def _as8(vec, np):
    """Coerce a 4- or 8-component quaternion/octonion sample to an 8-vector."""
    a = np.asarray(vec, dtype=float).reshape(-1)
    if a.size == 4:
        out = np.zeros(8, dtype=float)
        out[:4] = a
        return out
    if a.size == 8:
        return a.astype(float, copy=True)
    raise ValueError(
        f"hypercomplex sample must have 4 (quaternion) or 8 (octonion) "
        f"components; got {a.size}"
    )


def _dft_core(x, *, form, mu_axis, inverse, two_sided_right, bracketing, octonion):
    """Shared (Q/O)DFT engine. Composes the qm.octonion left/right-mult atoms.

    X[k] = scale · Σ_n  T( W(σ·2πkn/N) ) · x[n]

    where ``W`` is the twiddle, ``σ = +1`` for the inverse (else −1), ``scale``
    = 1/N for the inverse (else 1), and ``T`` is left- or right-multiplication
    by the twiddle (``octonion_left_mult`` / ``octonion_right_mult``) — the
    non-commutative choice that distinguishes the left/right forms.
    """
    np = _require_numpy()
    from srmech.qm.octonion import octonion_left_mult, octonion_right_mult

    if mu_axis not in _MU_AXES:
        raise ValueError(f"mu_axis must be one of {sorted(_MU_AXES)}; got {mu_axis!r}")
    mu = _MU_AXES[mu_axis]

    xs = [_as8(v, np) for v in x]
    n_pts = len(xs)
    if n_pts == 0:
        return []
    if not octonion:
        # ℍ-closure guard: a quaternion DFT requires quaternion samples
        # (e4..e7 == 0); a non-zero octonion tail would silently leak.
        for v in xs:
            # ℍ-closure guard: the octonion tail e4..e7 must be all-zero. A
            # presence test (any nonzero) — no magnitude / no abs() needed.
            if bool(np.any(v[4:] != 0.0)):
                raise ValueError(
                    "quaternion_dft requires quaternion samples (components "
                    "e4..e7 must be zero); use octonion_dft for full octonions"
                )

    sigma = 1.0 if inverse else -1.0
    scale = (1.0 / n_pts) if inverse else 1.0
    two_pi = 2.0 * math.pi

    mult_left = form == "left"
    out: List = []
    for k in range(n_pts):
        acc = np.zeros(8, dtype=float)
        for n in range(n_pts):
            theta = sigma * two_pi * k * n / n_pts
            w = _twiddle8(theta, mu, np)
            if form == "two_sided":
                # Octonion two-sided: W_l · x · W_r — the bracketing of the
                # 3-factor product is meaningful (𝕆 is NON-associative, F378).
                wl = octonion_left_mult(w)
                wr_axis = two_sided_right or mu_axis
                w_r = _twiddle8(theta, _MU_AXES[wr_axis], np)
                if bracketing == "left_associated":
                    # (W_l · x) · W_r
                    inner = wl @ xs[n]
                    term = octonion_right_mult(w_r) @ inner
                else:
                    # W_l · (x · W_r)
                    inner = octonion_right_mult(w_r) @ xs[n]
                    term = wl @ inner
            elif mult_left:
                term = octonion_left_mult(w) @ xs[n]   # W · x  (left form)
            else:
                term = octonion_right_mult(w) @ xs[n]   # x · W  (right form)
            acc = acc + term
        acc = acc * scale
        out.append(acc.tolist() if octonion else acc[:4].tolist())
    return out


def quaternion_dft(
    x: Sequence,
    *,
    form: str = "left",
    mu_axis: str = "i",
    inverse: bool = False,
) -> List[List[float]]:
    """Quaternion discrete Fourier transform (QDFT) — composite over qm.octonion.

    The native transform for a Klein-4 object: its ``ℍ`` coefficient algebra
    resolves **both** ``Z₂`` chirality axes the complex FFT collapses (F380).

    Parameters
    ----------
    x : sequence of quaternions
        Each sample is a 4-component ``[q0, q1, q2, q3]`` (or an 8-component
        octonion with ``e4..e7 == 0``). ``N = len(x)``.
    form : {"left", "right"}
        Left (``W·x``) or right (``x·W``) twiddle multiplication — the two
        differ because ``ℍ`` is non-commutative. Both are invertible and
        round-trip (the twiddle lives in the commutative ``ℝ[μ]≅ℂ`` subalgebra).
    mu_axis : {"i", "j", "k", "ijk"}
        The unit pure-quaternion transform axis ``μ`` (``μ²=−1``).
    inverse : bool
        Inverse QDFT (conjugate twiddle + ``1/N`` scale). ``inverse(forward(x))``
        recovers ``x`` exactly (to float round-off), including **all four**
        components — i.e. both ``Z₂`` axes.

    Returns
    -------
    list[list[float]]
        ``N`` quaternions (4-component lists).

    Class home: **M** (Clifford/HDC quaternion multiply) ∘ **C** (the
    orientation of the twiddle's ``±μ`` phase) ∘ **N** (the rational twiddle
    angle ``kn/N``). Sangwine & Ell (2012), arXiv:1001.4379.
    """
    if form not in _FORMS:
        raise ValueError(f"form must be one of {_FORMS}; got {form!r}")
    return _dft_core(
        x, form=form, mu_axis=mu_axis, inverse=inverse,
        two_sided_right=None, bracketing="left_associated", octonion=False,
    )


def octonion_dft(
    x: Sequence,
    *,
    form: str = "left",
    mu_axis: str = "i",
    bracketing: str = "left_associated",
    two_sided_right_axis: str = "j",
    inverse: bool = False,
) -> List[List[float]]:
    """Octonion discrete Fourier transform (ODFT) — composite over qm.octonion.

    Carries the F378 **non-associativity** as an *explicit declared field*: the
    ODFT is **not unique** for the two-sided form, so the bracketing/association
    convention must be stated, not assumed.

    Parameters
    ----------
    x : sequence of octonions
        Each sample is an 8-component ``[e0..e7]``. ``N = len(x)``.
    form : {"left", "right", "two_sided"}
        ``W·x`` / ``x·W`` / ``W_l·x·W_r``. The two-sided form is where octonion
        non-associativity bites.
    mu_axis : {"i", "j", "k", "ijk"}
        The left (or single) transform axis ``μ`` (``μ²=−1``).
    bracketing : {"left_associated", "right_associated"}
        **Only meaningful for** ``form="two_sided"``: ``(W_l·x)·W_r`` vs
        ``W_l·(x·W_r)``. These **differ** for octonions (F378) — the field is
        the concrete crystallisation of "the ODFT must declare its association
        order". Recorded (trivially) for the one-sided forms.
    two_sided_right_axis : {"i", "j", "k", "ijk"}
        The right twiddle axis ``μ_r`` for the two-sided form.
    inverse : bool
        Inverse ODFT (one-sided forms round-trip; the two-sided form is
        forward-only here — its inverse is open under non-associativity).

    Returns
    -------
    list[list[float]]
        ``N`` octonions (8-component lists).

    Class home: **M** (octonion multiply) ∘ **C** (twiddle orientation) ∘ **N**
    (rational angle). Błaszczyk (2019), arXiv:1905.12631; origin Hahn & Snopek
    (2011), Bull. Polish Acad. Sci. 59(2):167–181.
    """
    if form not in _OCTONION_FORMS:
        raise ValueError(f"form must be one of {_OCTONION_FORMS}; got {form!r}")
    if bracketing not in _BRACKETINGS:
        raise ValueError(f"bracketing must be one of {_BRACKETINGS}; got {bracketing!r}")
    if form == "two_sided" and inverse:
        raise NotImplementedError(
            "two-sided octonion_dft inverse is open under non-associativity "
            "(F378); only the one-sided forms round-trip"
        )
    return _dft_core(
        x, form=form, mu_axis=mu_axis, inverse=inverse,
        two_sided_right=two_sided_right_axis, bracketing=bracketing, octonion=True,
    )
