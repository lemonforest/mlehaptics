"""Path A IIR filter — closed-form recursive filter with biquad cascade option.

Identity per the implementation plan §1: IIR IS a Class N (rational
``b(z)/a(z)`` coefficient pair) ∘ Class C (cyclic-cascade composition of
biquad sections) composition. Each biquad section is itself a Class N rational
of order 2.

rc149 (B4b) classification: ``c_dispatched``.  The recursive difference
equation ``y[n] = Σ b·x[n-k] − Σ a·y[n-k]`` reads the output the loop is still
producing, so it is inherently SEQUENTIAL and does NOT decompose into a
matmul / FFT — it is the ONE genuinely-new numeric kernel the filter family
needs.  ``op`` dispatches to the c_dispatched ``srmech_iir_lfilter_f64`` (via
``_native.iir_lfilter_f64_c``) when the native lib is present, and falls back to
the complete numpy-free pure-Python direct-form-II-transposed reference
(``_lfilter_direct``) otherwise (a biquad cascade dispatches per second-order
section).  NUMERIC (within-tol, not byte-identical): the accumulation may
FMA-fuse ~1 ULP on some platforms, so the parity contract is differential
(reldiff ≤ 1e-9), NOT byte-equality.

Path B dual in Phase 6 (IIR via Class N rational + Class C cascade in bound-
vector substrate).

Carrier note (#564): numpy-free. The C dispatch + the pure direct-form-II-
transposed reference both run on plain ``list``\\s (the Class-C recursive
cascade of the Class-N ``b/a`` rational); the op returns a ``list``. No scipy /
numpy is imported.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Oppenheim
& Schafer (2010, 3rd ed.) §6 + Proakis & Manolakis (2007, 4th ed.) §10.
RBJ EQ Cookbook for biquad-design forms.
"""

from __future__ import annotations

from typing import Optional, Sequence

from srmech.math.q import Q as _Q, exact_vector as _exact_vector, to_q as _to_q   # rc466 (`#T1188`)

OPERATION_NAME = "iir"
CLASS_COMPOSITION = ("N", "C")
PERFORMANCE_HINT = "shallow-cascade-biquad-amortise"
SSOT_CITATION = (
    "Oppenheim & Schafer (2010, 3rd ed.), 'Discrete-Time Signal Processing', "
    "Prentice Hall, §6 (IIR filters). Proakis & Manolakis (2007, 4th ed.), "
    "'Digital Signal Processing', Pearson, §10. Bristow-Johnson, 'Cookbook "
    "formulae for audio EQ biquad filter coefficients' (RBJ EQ Cookbook, "
    "2005), https://www.w3.org/TR/audio-eq-cookbook/."
)


def _check_ba(b, a, where: str = ""):
    """The C peer's own input domain, stated once and enforced at the front door.

    ``srmech_iir_lfilter_f64`` (``c/src/srmech_iir.c:64-77``) refuses
    ``nb == 0 || na == 0`` with ``SRMECH_ERR_NULL_ARG`` and ``a0 == 0.0`` with
    ``SRMECH_ERR_BAD_INPUT``. The ctypes wrapper re-states that predicate and
    returns ``None``, which ``op`` cannot distinguish from *"native absent"*, so
    the guard is dead through the Python front door unless ``op`` states it too.

    Called from BOTH branches of ``op``. rc431's first cut guarded only the
    direct ``(b, a)`` branch on the argument that the biquad branch always passes
    length-3 slices, so a second guard would be unreachable. **That argument
    holds for the LENGTH predicate and does not hold for ``a[0] == 0``**, which
    is a value predicate no slice length constrains: a section
    ``[1, 0, 0, 0, 0, 0]`` is exactly 6 coefficients and drove
    ``_lfilter_direct`` to a raw ``ZeroDivisionError`` at ``a0 = a[0]`` while the
    C peer refuses the same section with ``SRMECH_ERR_BAD_INPUT``. Two predicates
    were being reasoned about as one; the reachability argument was true of the
    wrong one.
    """
    b = list(b)
    a = list(a)
    if len(b) == 0 or len(a) == 0:
        raise ValueError(
            f"iir: b and a must be non-empty coefficient sequences{where}; got "
            f"len(b)={len(b)}, len(a)={len(a)}")
    if a[0] == 0:
        raise ValueError(
            f"iir: a[0] must be non-zero{where} -- a[0] == 0 is not a valid "
            f"recursion (the difference equation divides by it)")
    return b, a


def _lfilter_direct(b: Sequence[float], a: Sequence[float], x: Sequence[float]):
    """Direct-form-II transposed IIR filter (closed-form reference).

    The Class-C recursive cascade of the Class-N ``b/a`` rational over a plain
    ``list`` carrier; ``y[i]`` and the state ``z`` are accumulated by explicit
    multiply-adds (no numpy).
    """
    a0 = a[0]
    b = [bi / a0 for bi in b]
    a = [ai / a0 for ai in a]
    n = len(x)
    # DF2T needs b and a to share the filter length: pad the shorter with zeros
    # (a shorter b would otherwise drop the trailing feedback taps, since the
    # a[j]·y[i] correction lives inside the b-indexed state loop). This matches
    # scipy.lfilter's b/a padding to max(len(a), len(b)).
    nfilt = max(len(a), len(b))
    b = b + [0.0] * (nfilt - len(b))
    a = a + [0.0] * (nfilt - len(a))
    y = [0.0] * n
    nz = nfilt - 1
    z = [0.0] * nz
    for i in range(n):
        y[i] = b[0] * x[i] + (z[0] if nz > 0 else 0.0)
        for j in range(1, nfilt):
            if j - 1 < nz:
                z[j - 1] = (
                    b[j] * x[i]
                    - a[j] * y[i]
                    + (z[j] if j < nz else 0.0)
                )
    return y


def _lfilter_exact(b, a, x):
    """rc466 (`#T1188`): the direct-form-II-transposed recursion on the EXACT
    carrier — the same loop as :func:`_lfilter_direct`, state seeded with the
    integer ``0``. With ``a[0] == 1`` no division runs and integer operands
    give INTEGER output (the difference equation is closed over ℤ); otherwise
    every coefficient is divided by ``a[0]`` on ``Q`` and the output is exact
    ``Q``. ``b`` / ``a`` / ``x`` arrive as ``list[Q]`` from the admission
    gate, or as the caller's own ``int`` / ``Q`` leaves."""
    a0 = a[0]
    if a0 != 1:
        a0q = _to_q(a0)                      # int / int would be a FLOAT division
        b = [_to_q(bi) / a0q for bi in b]
        a = [_to_q(ai) / a0q for ai in a]
    else:
        b = list(b)
        a = list(a)
    n = len(x)
    nfilt = max(len(a), len(b))
    b = b + [0] * (nfilt - len(b))
    a = a + [0] * (nfilt - len(a))
    y = [0] * n
    nz = nfilt - 1
    z = [0] * nz
    for i in range(n):
        y[i] = b[0] * x[i] + (z[0] if nz > 0 else 0)
        for j in range(1, nfilt):
            if j - 1 < nz:
                z[j - 1] = (
                    b[j] * x[i]
                    - a[j] * y[i]
                    + (z[j] if j < nz else 0)
                )
    return y


def _exact_leaves(seq):
    """The operand AS GIVEN when every leaf is a plain ``int`` / ``Q`` (so integer
    output stays integer), else its ``list[Q]`` reading (``(num, den)`` pairs /
    Fractions become ``Q``); ``None`` when any leaf is inexact."""
    qs = _exact_vector(seq)
    if qs is None:
        return None
    items = list(seq)
    if all(isinstance(v, (int, _Q)) and not isinstance(v, bool) for v in items):
        return items
    return qs


def op(
    signal,
    b,
    a,
    *,
    biquad_sections: Optional[Sequence[Sequence]] = None,
    D: int = 8192,
):
    """Recursive IIR filter applied to ``signal``.

    Parameters
    ----------
    signal:
        1-D real input.
    b:
        Numerator (feed-forward) coefficient sequence.
    a:
        Denominator (feed-back) coefficient sequence; ``a[0]`` typically 1.
    biquad_sections:
        Optional list of 6-tuples ``[b0, b1, b2, a0, a1, a2]`` for cascade
        application. When provided, ``b`` / ``a`` are ignored.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    list
        Filtered output; numpy-free (#564). ``int`` / ``Q`` leaves on the exact
        route (see Accuracy).

    Accuracy (rc466, `#T1188`)
    --------------------------
    **The carrier is the operand's.** When ``signal``, ``b`` and ``a`` (or, in
    cascade form, every ``biquad_sections`` entry) are all exact — every leaf
    ``int`` / ``Q`` / ``(num, den)`` — the recursion runs on the exact carrier
    on BOTH projections (:func:`_lfilter_exact`): the difference equation is
    closed over ℚ, so the output is EXACT ``Q``, and with ``a[0] == 1`` and
    integer coefficients it is INTEGER. A float leaf anywhere keeps the
    c_dispatched ``srmech_iir_lfilter_f64`` (pure DF2T fallback), **accurate
    to round-off** (~1 ULP; the accumulation may FMA-fuse, so the parity
    contract is reldiff <= 1e-9, not byte-equality). Through rc465 the two
    projections DISAGREED on an exact operand (the census's one native/pure
    DIVERGENT row): the C wrapper rounded ``a`` to float64 before dividing
    while the pure body divided int by int with one correctly-rounded
    division — two answers one ULP apart under one name, neither exact.

    Raises
    ------
    ValueError
        A non-1-D ``signal``; an empty ``b`` or ``a``; ``a[0] == 0`` — in the
        direct form OR in any ``biquad_sections`` entry, whose ``a0`` is
        ``section[3]``; or a ``biquad_sections`` entry that is not 6
        coefficients.

    Notes
    -----
    The ``b`` / ``a`` domain guard (``_check_ba``) states the SAME predicate the C peer
    ``srmech_iir_lfilter_f64`` already enforces (``srmech_iir.c``: ``nb == 0 ||
    na == 0`` -> ``SRMECH_ERR_NULL_ARG``, ``a0 == 0.0`` -> ``SRMECH_ERR_BAD_INPUT``).
    Through rc430 that guard was DEAD through the Python front door: the ctypes
    wrapper re-stated the predicate and returned ``None``, which ``op`` reads as
    *"native absent"*, so the pure body ran instead -- and for ``b == []`` the
    pure body RETURNED ``[0.0] * len(signal)`` by zero-padding to ``len(a)``,
    answering an input the co-equal C projection calls invalid (``na == 0`` and
    ``a[0] == 0`` escaped as a raw ``IndexError`` / ``ZeroDivisionError`` from
    inside ``_lfilter_direct``). Python moves to C here, never the reverse: C is
    the already-shipped, stricter, correct contract, and the capability is the
    invariant across co-equal projections
    (``[[user_stance_srmech_is_multi_implementation_not_python_with_c_accel]]``).

    The guard belongs at ``op``, not inside ``_lfilter_direct``: only the PURE
    arm runs that body, so a guard there would leave the native arm accepting
    what the pure arm refuses — the same one-sided contract this repair exists
    to remove. It is applied in ``op`` on BOTH branches. rc431's first cut
    applied it to the direct ``(b, a)`` branch only, reasoning that the biquad
    branch always passes length-3 slices of a length-6 section so a second guard
    would be unreachable. **That is true of the LENGTH predicate and false of
    ``a[0] == 0``**, which no slice length constrains: the section
    ``[1, 0, 0, 0, 0, 0]`` is a well-formed 6-tuple, and through that cut it
    still reached ``_lfilter_direct`` and raised a raw ``ZeroDivisionError``
    while the C peer refuses the identical section with
    ``SRMECH_ERR_BAD_INPUT``. The reachability argument was sound about the
    wrong one of two predicates that had been reasoned about as one, so the
    headline divergence survived on the branch nobody probed.
    """
    sig_exact = _exact_leaves(signal)
    if sig_exact is not None:
        if biquad_sections is None:
            b_x = _exact_leaves(b)
            a_x = _exact_leaves(a)
            if b_x is not None and a_x is not None:
                b_x, a_x = _check_ba(b_x, a_x)
                return _lfilter_exact(b_x, a_x, sig_exact)
        else:
            secs = [list(s) for s in biquad_sections]
            secs_x = [_exact_leaves(s) for s in secs]
            if all(s is not None for s in secs_x):
                out = list(sig_exact)
                for idx, section in enumerate(secs_x):
                    if len(section) != 6:
                        raise ValueError(
                            f"biquad section requires 6 coefficients; got "
                            f"{len(section)}"
                        )
                    b_s, a_s = _check_ba(section[:3], section[3:],
                                         where=f" (biquad section {idx})")
                    out = _lfilter_exact(b_s, a_s, out)
                return out
    try:
        sig = [float(x) for x in signal]
    except TypeError as exc:  # nested sequence -> not 1-D
        raise ValueError("iir expects a 1-D real signal") from exc

    if biquad_sections is None:
        b, a = _check_ba(b, a)

    from srmech import _native

    if biquad_sections is not None:
        # Cascade of second-order sections (sosfilt): apply each in turn, each
        # dispatched to the c_dispatched srmech_iir_lfilter_f64 (else pure).
        out = list(sig)
        for idx, section in enumerate(biquad_sections):
            if len(section) != 6:
                raise ValueError(
                    f"biquad section requires 6 coefficients; got "
                    f"{len(section)}"
                )
            # Same C domain, per section, BEFORE dispatch. The length half is
            # unreachable here (the slices are always 3) but `a[0] == 0` is not:
            # section [1, 0, 0, 0, 0, 0] is a well-formed 6-tuple whose a0 is 0.
            b_s, a_s = _check_ba(section[:3], section[3:],
                                 where=f" (biquad section {idx})")
            native = _native.iir_lfilter_f64_c(b_s, a_s, out)
            out = native if native is not None else _lfilter_direct(b_s, a_s, out)
        return out

    # Direct (b, a) form: prefer the c_dispatched srmech_iir_lfilter_f64; the
    # pure direct-form-II-transposed reference is the complete fallback.
    native = _native.iir_lfilter_f64_c(b, a, sig)
    if native is not None:
        return native
    return _lfilter_direct(list(b), list(a), sig)
