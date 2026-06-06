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

from typing import List, Sequence

# §22: scalar root + trig via the Class-N rational cascade, not libm; π from the
# Archimedes pi_cascade (`[[feedback_continuous_number_line_pedagogical_obstacle]]`).
from srmech.amsc.rational import cos as _rcos
from srmech.amsc.rational import pi_cascade_digits as _pi_cascade_digits
from srmech.amsc.rational import sin as _rsin
from srmech.amsc.rational import sqrt as _rsqrt

# Cascade-π as a float: the high-precision rational digit-string projected to
# float once at import (no `math.pi`).
_PI_IP, _, _PI_FP = _pi_cascade_digits(30).partition(".")
_PI = int(_PI_IP + _PI_FP) / (10 ** len(_PI_FP))

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
    """``exp(μθ) = cos θ·1 + sin θ·μ`` as an 8-vector (μ a unit pure-imaginary
    octonion). All seven imaginary components are carried — a quaternion axis
    has ``e4..e7 == 0`` so the result is unchanged from the ℍ-only form, but a
    general / diagonal octonion ``μ`` (e.g. ``(Σeₙ)/√7``) is now honoured."""
    c = _rcos(theta)
    s = _rsin(theta)
    w = np.zeros(8, dtype=float)
    w[0] = c
    for _i in range(1, 8):
        w[_i] = s * mu[_i]
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


def _resolve_mu(mu_axis, *, octonion, np):
    """Resolve ``mu_axis`` to a **unit pure-imaginary** 8-vector ``μ`` (``e0==0``,
    ``‖μ‖=1`` ⟹ ``μ²=−1``) — the transform/coupling axis (#908, §29).

    Accepts:

    * a **named axis** ``'i'`` / ``'j'`` / ``'k'`` / ``'ijk'`` (the shipped set);
    * ``'diagonal'`` — the equal-weight pure-imaginary axis of the active
      algebra: ``(i+j+k)/√3`` for a quaternion transform, ``(Σ_{n=1..7} eₙ)/√7``
      for an octonion one. This is the axis that **couples** all streams (F436):
      ``μ·Σ sₙeₙ`` folds them into the real/anchor coherence channel;
    * a **sequence** (4- or 8-component) — a general unit pure-imaginary axis;
      it is normalised to unit length, and ``e0`` (and, for a quaternion
      transform, ``e4..e7``) must be zero.
    """
    if isinstance(mu_axis, str):
        if mu_axis in _MU_AXES:
            return _as8(_MU_AXES[mu_axis], np)
        if mu_axis == "diagonal":
            v = np.zeros(8, dtype=float)
            hi = 8 if octonion else 4
            v[1:hi] = 1.0
            return v / _rsqrt(float(hi - 1))
        raise ValueError(
            f"mu_axis must be one of {sorted(_MU_AXES) + ['diagonal']}, or a unit "
            f"pure-imaginary vector; got {mu_axis!r}"
        )
    # General axis: a 4- or 8-component pure-imaginary vector.
    v = _as8(mu_axis, np)
    if v[0] != 0.0:
        raise ValueError("a general mu_axis must be pure-imaginary (e0 == 0)")
    if not octonion and bool(np.any(v[4:] != 0.0)):
        raise ValueError(
            "a quaternion mu_axis must lie in ℍ (components e4..e7 == 0); use "
            "octonion_dft / a quaternion-scope coupler for an octonion axis"
        )
    norm = _rsqrt(float(sum(c * c for c in v[1:])))
    if norm == 0.0:
        raise ValueError("mu_axis must be a non-zero pure-imaginary vector")
    return v / norm


def _pack_streams(streams, np):
    """Coerce a coupler input to an (8-vector carrier, octonion?) pair.

    A length-≤3 (resp. 4–7) real sequence is **packed as streams** into the
    pure-imaginary slots of a quaternion (resp. octonion) carrier (real/anchor
    = 0); a length-4 or length-8 sequence is taken as a **literal** quaternion
    / octonion carrier (so a bound result round-trips back through the coupler).
    """
    a = np.asarray(streams, dtype=float).reshape(-1)
    n = int(a.size)
    if n == 4:
        return _as8(a, np), False
    if n == 8:
        return a.astype(float, copy=True), True
    if 1 <= n <= 3:
        q = np.zeros(8, dtype=float)
        q[1:1 + n] = a
        return q, False
    if 5 <= n <= 7:
        q = np.zeros(8, dtype=float)
        q[1:1 + n] = a
        return q, True
    raise ValueError(
        "streams must be ≤7 real coefficients (packed into the imaginary slots) "
        "or a 4-/8-component literal quaternion/octonion carrier; got length "
        f"{n}"
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

    mu = _resolve_mu(mu_axis, octonion=octonion, np=np)
    # Resolve the two-sided right axis once (defaults to the left axis).
    mu_r = _resolve_mu(two_sided_right or mu_axis, octonion=octonion, np=np)

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
    two_pi = 2.0 * _PI

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
                w_r = _twiddle8(theta, mu_r, np)
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
    mu_axis : {"i", "j", "k", "ijk", "diagonal"} or unit pure-imaginary vector
        The transform axis ``μ`` (``μ²=−1``). ``'diagonal'`` (= ``(i+j+k)/√3``
        here) **couples** all three axes into the real/anchor channel (F436); a
        single named axis only **carries** them. A general unit pure-imaginary
        quaternion vector is also accepted (#908). See :func:`_resolve_mu`.
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
    mu_axis : {"i", "j", "k", "ijk", "diagonal"} or unit pure-imaginary vector
        The left (or single) transform axis ``μ`` (``μ²=−1``). ``'diagonal'``
        (= ``(Σ_{n=1..7} eₙ)/√7`` for octonions) **couples** all seven imaginary
        streams into the real/anchor coherence channel (F436); a single named
        axis only carries them. A general unit pure-imaginary octonion vector is
        also accepted (#908). See :func:`_resolve_mu`.
    bracketing : {"left_associated", "right_associated"}
        **Only meaningful for** ``form="two_sided"``: ``(W_l·x)·W_r`` vs
        ``W_l·(x·W_r)``. These **differ** for octonions (F378) — the field is
        the concrete crystallisation of "the ODFT must declare its association
        order". Recorded (trivially) for the one-sided forms.
    two_sided_right_axis : {"i", "j", "k", "ijk", "diagonal"} or unit vector
        The right twiddle axis ``μ_r`` for the two-sided form (same resolution
        as ``mu_axis``: named / ``'diagonal'`` / general unit pure-imaginary).
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


def hypercomplex_couple(
    streams: Sequence,
    *,
    axis="diagonal",
    theta: float = _PI / 2.0,
    sigma: int = 1,
    form: str = "left",
    inverse: bool = False,
) -> List[float]:
    """Bidirectional ``(σ, θ, μ)`` hypercomplex coupler — bind ≥3 streams into
    one quaternion/octonion + a joint coherence channel, and unbind losslessly.

    This is the first-class coupler asked for in **#908 / §29** (findings
    **F436** + **F437**). Where ``quaternion_dft`` / ``octonion_dft`` *carry* N
    streams along named single axes, this **couples** them: it packs ``streams``
    into the pure-imaginary slots of a carrier ``q`` and applies the twiddle
    ``T = exp(σ_eff · μ · θ)`` (``σ_eff = σ·(−1 if inverse else +1)``):

    * **Bind** (``sigma=+1``) with a **diagonal** ``μ`` folds the streams — the
      result's **real/anchor** channel becomes a joint *coherence detector*
      (F436: coherent streams add, incoherent cancel; ``μ·Σsₙeₙ`` collects
      ``−Σsₙ``). The imaginaries carry the pairwise relations.
    * **Unbind** (``sigma=-1``, or ``inverse=True``) is the **conjugate**
      twiddle ``exp(−μθ)``; ``couple(couple(q, σ=+1), σ=-1)`` recovers ``q``
      exactly — the division-algebra identity ``T̄·(T·q)=‖T‖²·q`` (F437). This
      is **guaranteed reversible only up to 𝕆** (the Hurwitz boundary; the
      sedenion's zero divisors break it) → lossless for **≤ 7 streams**.

    ``form="left"``/``"right"`` and ``inverse`` are special discrete points of
    the same continuous ``(σ, θ, μ)`` family — exactly ``the_one``'s ``𝕊(σ,θ)``
    (F420) **plus the axis μ**. This exposes the axis + sign of the existing
    ``exp(μθ)`` twiddle; **no new algebra** (composite over ``qm.octonion``).

    Parameters
    ----------
    streams : sequence
        ≤3 real coefficients → packed into a quaternion ``(0, s₀, s₁, s₂)``;
        4–7 → packed into an octonion ``(0, s₀, …)``; a length-4 / length-8
        sequence is taken as a **literal** quaternion / octonion carrier (so a
        bound result feeds straight back in to unbind).
    axis : str or sequence
        The coupling axis ``μ`` (``'diagonal'`` default; also ``'i'``/``'j'``/
        ``'k'``/``'ijk'`` or a unit pure-imaginary vector). See
        :func:`_resolve_mu`. A single named axis does **not** couple across
        axes (it only carries) — use ``'diagonal'`` for true coupling (F436).
    theta : float
        The continuous coupling phase (default ``π/2`` — the F436 quarter-turn
        fold where the diagonal axis sends the streams into the anchor).
    sigma : {+1, -1}
        Conjugation / chirality: ``+1`` binds (forward fold), ``−1`` unbinds
        (the conjugate twiddle; F437).
    form : {"left", "right"}
        ``T·q`` or ``q·T`` (``ℍ``/``𝕆`` are non-commutative).
    inverse : bool
        Flips the effective sign (equivalently toggles ``sigma``); provided for
        symmetry with the DFT surface.

    Returns
    -------
    list[float]
        The coupled value — a 4-component quaternion (≤3 streams / literal
        quaternion) or 8-component octonion (otherwise).

    Class home: **M** (octonion multiply) ∘ **C** (the ``σ``/conjugation
    orientation) ∘ **N** (the rational phase ``θ``). F436 / F437; §29.
    """
    np = _require_numpy()
    from srmech.qm.octonion import octonion_left_mult, octonion_right_mult

    if sigma not in (1, -1, 1.0, -1.0):
        raise ValueError(f"sigma must be +1 or -1; got {sigma!r}")
    if form not in _FORMS:
        raise ValueError(f"form must be one of {_FORMS}; got {form!r}")

    q, octonion = _pack_streams(streams, np)
    mu = _resolve_mu(axis, octonion=octonion, np=np)
    eff = float(sigma) * (-1.0 if inverse else 1.0) * float(theta)
    w = _twiddle8(eff, mu, np)
    if form == "left":
        out = octonion_left_mult(w) @ q
    else:
        out = octonion_right_mult(w) @ q
    return out.tolist() if octonion else out[:4].tolist()
