"""The FRAME-CARRYING CARRIER — a periodic Taylor-series value that carries its
local beat-frame ``(σ, w)`` so a cross-seam compare parallel-TRANSPORTS the frame
before comparing (0.9.0rc238; #1385 F-thread — ``op / operand / responsion ≅
field / excitation / CURVATURE``; the user build-directive "an exact-rational
carrier / truncated Taylor series is NOT just a value; across a beat seam it needs
to carry its local frame-rotation, and a cross-seam compare must parallel-transport
the frame first → cross-seam bit-exactness holds where the un-framed compare was
only SOMETIMES exact").

**The drift this fixes (why it is NOT a re-wrap of winding_fold / the_one).** The
periodic Class-N series carriers :func:`~srmech.math.rational.sin_series_truncate`
/ :func:`~srmech.math.rational.cos_series_truncate` truncate the RAW rational
argument ``p/q`` **directly** — they do NOT fold it (their own docstring: "caller
should reduce to [-π, π]"). So a truncated ``sin`` at ``θ`` and at ``θ + 2π`` gives
two DIFFERENT exact rationals (the truncation is about the EXPANSION POINT, and the
raw series drifts — and eventually BLOWS UP — as ``|x|`` grows past the convergence
radius), even though ``sin`` is 2π-periodic. That is "exact WITHIN a beat
(``|x| ≤ π``, winding ``w = 0``) but NOT bit-exact ACROSS the 2π seam" under the raw
carrier. This carrier fixes exactly that:

* ``winding_fold`` cannot fix it: it returns a **float** residue (re-quantised to a
  ``2⁻⁴⁴`` grid), so it cannot feed the EXACT-rational series the exact residue the
  fix needs. The transport here is an EXACT-RATIONAL 2π divmod against the SAME
  Machin-2π anchor :data:`~srmech.math.laplacian._EPH_TWO_PI` — no float, no
  re-quantise (see :func:`_exact_seam_fold`).
* ``the_one`` cannot fix it: its 2π-periodic adjoint FOLDS the winding away (that is
  what :func:`~srmech.amsc.cascade.one.separate_winding_curvature` reads); it never
  carries a truncated-Taylor VALUE across a seam.

**The ``(value, frame)`` pair — the rc125 recoverable-fold analogue.** This carrier
is the exact structural sibling of :class:`~srmech.biology.coupling.RecoverableFold`'s
``(lossy_bundle, exact_seed_R)`` PAIR, with the **frame as the exact second leg**:

* ``value``       — the LOSSY leg: the raw local truncated series ``σ·series(θ, N)``.
                    It is exact within a beat and DRIFTS across a seam (the primary
                    projected part).
* ``frame=(σ,w)`` — the EXACT COMPLEMENT (a connection element / winding index): the
                    beat's local rotation. Its presence makes the compare recoverable
                    — parallel-transport by the frame restores cross-seam bit-exactness.
* ``residue``     — the canonical in-beat representative ``|r| ≤ π`` (``θ`` transported
                    to ``w = 0``); the transported value ``σ·series(residue, N)`` is the
                    bounded, always-in-beat value the compare aligns on.

**The exact ``is_aligned`` certificate (rc236's ``is_flat`` one level up).** Two
carriers are ALIGNED iff transporting one onto the other is trivial-or-in-the-
stabilizer: their canonical residues are EQUAL (a whole number of 2π turns apart —
the transport lands in the value's winding-stabilizer) AND their chirality ``σ``
matches. ``aligned`` is then an EXACT theorem: the transported values are
byte-identical. When NOT aligned it carries the real residual — the non-zero
``residue_delta`` holonomy the transport could not remove (or a chirality mismatch)
— so a genuinely different value is NEVER falsely reported aligned (the soundness
direction). This is the metacycle-seam instance of the rc236
:func:`~srmech.amsc.cascade.matrix_cascades.separate_frame_curvature` flatness flag:
``is_flat`` (curvature vanishes) ↔ ``is_aligned`` (the transport is a pure winding
turn, no residual holonomy).

Cascade decomposition (**composition_of_c**, no new C symbol — the SAME standalone-C
shape as ``separate_winding_curvature``): the values ride the c_dispatched Class-N
``sin/cos_series_truncate`` (``srmech_{sin,cos}_series_truncate_big``); the transport
is the EXACT-rational divmod over the Machin-2π anchor :data:`_EPH_TWO_PI` (Class-I
quotient-retained divmod over the exact Class-N 2π, the residue sign Class K/C — never
``abs()``); the reduction rides the c_dispatched Class-I ``rational._reduce_rational``
(``srmech_bigint`` / ``cyclic.gcd``); the alignment residual + the transport count ride
the c_dispatched Class-K :func:`~srmech.amsc.cascade.atoms.magnitude` (real ``|x|``,
never an ALU ``abs()``). So a bare-C host reproduces every field.

SSoT: rc125 ``RecoverableFold`` (the ``(lossy, exact_seed)`` pair pattern); rc207/rc215
``winding_fold`` / ``_eph_seam_fold`` (the 2π divmod, here made exact-rational); rc236
``separate_frame_curvature`` + rc237 ``separate_winding_curvature`` (the ``is_flat`` /
Stab shape the ``is_aligned`` cert lifts); the framework stance
``[[user_stance_bit_exact_is_local_flatness_of_connection_seams_are_holonomy]]`` (the
seam IS the holonomy; the frame is the connection element).
"""
from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["frame_carrier", "frame_carrier_compare"]

#: The two 2π-PERIODIC series carriers this op frames. ``atan``/``exp``/``log1p``
#: are NOT periodic — there is no 2π seam to transport across (``atan`` folds to a
#: different value; ``exp``/``log1p`` are aperiodic), so they are deliberately
#: excluded: the frame-carry is meaningful only where a beat seam exists.
_PERIODIC_FUNCS: Tuple[str, str] = ("sin", "cos")


def _validate(func: str, numerator: int, denominator: int,
              num_terms: int, sigma: int) -> None:
    """Shared input validation. ``sigma`` (the chirality frame component) is a
    Class-K/C sign flag — exactly ``+1`` or ``-1``, never a bare truthy int."""
    if func not in _PERIODIC_FUNCS:
        raise ValueError(
            f"frame_carrier: func must be one of {_PERIODIC_FUNCS} (the "
            f"2π-periodic series that HAVE a beat seam); got {func!r}")
    if not isinstance(numerator, int):
        raise TypeError(
            f"frame_carrier: numerator must be int; got {type(numerator).__name__}")
    if not isinstance(denominator, int):
        raise TypeError(
            f"frame_carrier: denominator must be int; got {type(denominator).__name__}")
    if denominator == 0:
        raise ValueError("frame_carrier: denominator must be a non-zero int")
    if not isinstance(num_terms, int) or num_terms < 0:
        raise ValueError(
            f"frame_carrier: num_terms must be a non-negative int; got {num_terms!r}")
    if sigma not in (1, -1):
        raise ValueError(
            f"frame_carrier: sigma (the chirality frame component) must be "
            f"+1 or -1; got {sigma!r}")


def _series(func: str, numerator: int, denominator: int,
            num_terms: int) -> Tuple[int, int]:
    """The c_dispatched Class-N periodic Taylor partial sum as an exact rational.

    Lazy import (``rational`` is a heavy module and the cascade package imports
    it on demand elsewhere too) — dispatches to
    ``srmech_{sin,cos}_series_truncate_big`` when native, exact bignum pure
    otherwise (byte-identical)."""
    from srmech.math.rational import sin_series_truncate, cos_series_truncate
    if func == "sin":
        return sin_series_truncate(numerator, denominator, num_terms)
    return cos_series_truncate(numerator, denominator, num_terms)


def _exact_seam_fold(a_num: int, a_den: int) -> Tuple[int, Tuple[int, int]]:
    """The EXACT-RATIONAL 2π seam-fold: ``a_num/a_den → (w, (r_num, r_den))`` with
    ``a_num/a_den = 2π·w + r_num/r_den`` and ``|r_num/r_den| ≤ π``.

    This is the exact-rational sibling of ``winding_fold`` /
    :func:`~srmech.math.laplacian._eph_seam_fold` — the SAME divmod against the
    SAME Machin-2π anchor :data:`~srmech.math.laplacian._EPH_TWO_PI`, but WITHOUT
    ``winding_fold``'s float residue and WITHOUT ``_eph_seam_fold``'s
    ``_EPH_FOLD_DEN`` re-quantisation. The residue stays an EXACT reduced
    rational, so it can feed the EXACT-rational series and two arguments a whole
    number of 2π-turns apart fold to the byte-IDENTICAL residue.

    Cascade: Class-I divmod with the quotient RETAINED (the winding ``w``) over the
    exact Class-N 2π; the residue is exact rational subtraction; the sign of the
    residue is a Class-K/C branch inside ``_eph_round_div`` (round-half-toward-+∞),
    never an ``abs()``. Reduction rides the c_dispatched Class-I ``_reduce_rational``.
    """
    from srmech.math.laplacian import _EPH_TWO_PI, _eph_round_div
    from srmech.math.rational import _reduce_rational

    # Normalise to a positive denominator so the round-div (den > 0) is well-posed
    # — a Class-K/C sign move, never abs().
    if a_den < 0:
        a_num, a_den = -a_num, -a_den
    pn, pd = _EPH_TWO_PI                     # 2π ≈ pn/pd, exact (pd = 2^80), pn > 0
    # w = round((a_num/a_den) / (pn/pd)) = round(a_num·pd / (a_den·pn)); den > 0.
    w = _eph_round_div(a_num * pd, a_den * pn)
    # residue = a − w·2π = (a_num·pd − w·pn·a_den) / (a_den·pd), exact rational.
    r_num = a_num * pd - w * pn * a_den
    r_den = a_den * pd
    return w, _reduce_rational(r_num, r_den)


def _framed(func: str, numerator: int, denominator: int,
            num_terms: int, sigma: int) -> Dict:
    """Build the frame-carrying carrier record (shared by both public ops)."""
    _validate(func, numerator, denominator, num_terms, sigma)
    from srmech.math.rational import _reduce_rational

    arg = _reduce_rational(numerator, denominator)      # canonical (num, den>0)
    w, residue = _exact_seam_fold(arg[0], arg[1])
    r_num, r_den = residue

    # LOSSY leg — the RAW local truncated series at the UN-folded argument. This is
    # exactly what today's carrier returns; it drifts (and eventually blows up)
    # across the 2π seam. sigma applies as the Class-K/C chirality sign on the value.
    v_num, v_den = _series(func, arg[0], arg[1], num_terms)
    value = (sigma * v_num, v_den)

    # CANONICAL transported value — the same series at the folded residue (bounded,
    # |r| ≤ π, no blow-up). Two arguments a whole number of 2π-turns apart share
    # this residue, so this value is byte-identical for them: the frame-carried,
    # always-in-beat representative the cross-seam compare aligns on.
    t_num, t_den = _series(func, r_num, r_den, num_terms)
    transported = (sigma * t_num, t_den)

    return {
        "func": func,
        "arg": arg,                 # the raw exact-rational argument (num, den)
        "sigma": sigma,             # chirality frame component (+1 / -1)
        "winding": w,               # metacycle winding — the frame's rotation index
        "residue": residue,         # canonical in-beat representative (|r| ≤ π)
        "num_terms": num_terms,
        "value": value,             # LOSSY leg: raw series at arg (drifts across seam)
        "transported": transported,  # frame-carried in-beat value (seam-invariant)
    }


def frame_carrier(func: str,
                  numerator: int,
                  denominator: int,
                  num_terms: int,
                  sigma: int = 1) -> Dict:
    """Construct the frame-carrying carrier ``(value, frame)`` for a 2π-periodic
    truncated Taylor series (rc238).

    Augments the raw Class-N periodic series carrier
    (:func:`~srmech.math.rational.sin_series_truncate` /
    :func:`~srmech.math.rational.cos_series_truncate`) with its local beat-frame
    ``(σ, w)`` — the connection element the raw carrier LOSES across the 2π seam.
    The returned record is the ``(lossy value, exact frame)`` pair (the rc125
    recoverable-fold analogue): ``value`` is the raw series at the argument (exact
    within a beat, DRIFTS across the seam); ``winding`` / ``residue`` / ``sigma`` are
    the exact frame that :func:`frame_carrier_compare` parallel-transports to restore
    cross-seam bit-exactness. See the module docstring for the full contract and the
    non-shell rationale.

    Args:
        func: ``"sin"`` or ``"cos"`` — the 2π-periodic series to frame.
        numerator, denominator: the argument angle as an exact rational ``p/q`` in
            radians (``denominator`` non-zero; sign is normalised into the numerator).
        num_terms: the Taylor truncation depth ``N`` (``0 ≤ N ≤ 50``).
        sigma: the chirality frame component — exactly ``+1`` or ``-1`` (Class-K/C
            sign; a left-handed reading of the value). Default ``+1``.

    Returns:
        The carrier record ``{func, arg, sigma, winding, residue, num_terms, value,
        transported}`` (all rationals are reduced ``(num, den)`` integer pairs; ``arg``
        / ``residue`` / ``value`` / ``transported`` are ``(num, den)``; ``winding`` /
        ``num_terms`` / ``sigma`` are ``int``).

    Raises:
        ValueError / TypeError: bad ``func`` / non-int or zero-denominator argument /
            negative or out-of-range ``num_terms`` / ``sigma`` not in ``{+1, -1}``.
    """
    return _framed(func, numerator, denominator, num_terms, sigma)


def frame_carrier_compare(func: str,
                          num_a: int, den_a: int,
                          num_b: int, den_b: int,
                          num_terms: int,
                          sigma_a: int = 1,
                          sigma_b: int = 1) -> Dict:
    """Cross-seam compare of two frame-carrying carriers — PARALLEL-TRANSPORT the
    frame, THEN compare — with the exact ``is_aligned`` certificate (rc238).

    Builds the two frame-carriers (``A`` at ``num_a/den_a``, ``B`` at ``num_b/den_b``,
    both ``func`` truncated to ``num_terms``, chiralities ``sigma_a`` / ``sigma_b``) and
    reports BOTH compares:

    * ``raw_equal`` — the UN-FRAMED compare ``A.value == B.value``: comparing the two
      carriers in their DIFFERENT local frames without transporting. This is the
      "sometimes not bit-exact across the seam" symptom — it DRIFTS (generically
      ``False``) when ``A`` and ``B`` sit on opposite sides of a 2π seam.
    * ``transported_equal`` — the FRAMED compare ``A.transported == B.transported``:
      each argument parallel-transported (exact-rational-folded) to its canonical
      in-beat residue FIRST, then compared. Bit-exact across the seam where the raw
      compare only sometimes matched — the win.

    The exact ``is_aligned`` certificate: ``aligned`` is ``True`` iff the transport
    lands in the value's winding-stabilizer — the canonical residues are EQUAL (a
    whole number of 2π turns apart; a zero ``residue_delta`` by its Class-K magnitude)
    AND the chiralities match. ``aligned is True`` is then a THEOREM: the transported
    values are byte-identical. When ``False`` it carries the real residual — the
    non-zero ``residue_delta`` holonomy (or ``chirality_match=False``) — so a genuinely
    different value is never falsely reported aligned (soundness).

    Args:
        func: ``"sin"`` or ``"cos"`` (the same series for both carriers).
        num_a, den_a: carrier ``A``'s exact-rational argument.
        num_b, den_b: carrier ``B``'s exact-rational argument.
        num_terms: the shared Taylor truncation depth ``N``.
        sigma_a, sigma_b: the two chirality frame components (``±1``).

    Returns:
        ``{func, raw_equal, transported_equal, aligned, transport_turns,
        transport_magnitude, residue_delta, chirality_match}`` — ``*_equal`` /
        ``aligned`` / ``chirality_match`` bool; ``transport_turns`` int (``w_A − w_B``,
        the crank applied); ``transport_magnitude`` int (Class-K ``|w_A − w_B|``);
        ``residue_delta`` the reduced ``(num, den)`` holonomy residual (``(0, 1)`` iff
        the residues coincide).
    """
    from srmech.math.rational import _reduce_rational
    from srmech.amsc.cascade.atoms import magnitude

    a = _framed(func, num_a, den_a, num_terms, sigma_a)
    b = _framed(func, num_b, den_b, num_terms, sigma_b)

    raw_equal = (a["value"] == b["value"])
    transported_equal = (a["transported"] == b["transported"])

    # residue_delta = residue_A − residue_B, exact rational (the holonomy the
    # transport could not remove). aligned ⟺ it VANISHES (Class-K magnitude of the
    # reduced numerator is 0 — never abs()) AND the chirality matches.
    ra_n, ra_d = a["residue"]
    rb_n, rb_d = b["residue"]
    residue_delta = _reduce_rational(ra_n * rb_d - rb_n * ra_d, ra_d * rb_d)
    residual_magnitude = magnitude(residue_delta[0])   # Class-K |num|; 0 ⇔ equal
    chirality_match = (a["sigma"] == b["sigma"])
    aligned = (residual_magnitude == 0) and chirality_match

    transport_turns = a["winding"] - b["winding"]
    return {
        "func": func,
        "raw_equal": raw_equal,
        "transported_equal": transported_equal,
        "aligned": aligned,
        "transport_turns": transport_turns,
        "transport_magnitude": magnitude(transport_turns),   # Class-K |Δw|
        "residue_delta": residue_delta,
        "chirality_match": chirality_match,
    }
