"""Class K — equation-of-centre / pin-slot (Kepler-shape projection-shadow).

Continuous projection-shadow of the integer-cyclic upstream (Class I
cyclic groups + Class J prime-period). ``[[user_stance_kepler_shape_universal]]``
+ PR #416 F2/F15/F17 read Kepler-equation algebra as pin-slot composition.
What rc473 (`#T1188`) measured against that reading, on a pure cell with
this module's own three ops (a 256-point sine quadrature), where ONE
pin-slot stage means ``pin_slot(theta, eps, 1.0) = atan2(eps sin theta,
1 + eps cos theta)``, i.e. ``eps = pin_offset / pin_distance``:

- ``E - M`` (Kepler's equation) is matched by one stage only through
  ``e**2``. With ``theta = pi - M`` and ``eps = e`` the stage's harmonics
  are ``e**k / k``; at ``e = 0.002`` the ``e**3`` terms read -0.125 (at
  ``sin M``) and +0.375 (at ``sin 3M``) for Kepler against 0 and +0.333333
  for the stage, and ``E - M - pin_slot(pi - M, e, 1.0)`` peaks over the
  M grid at 0.166667 ``e**3`` at ``e = 0.001``.
- ``nu - E`` IS a stage, doubled: ``E + 2 * pin_slot(pi - E, beta, 1.0)``
  with ``beta = e / (1 + sqrt(1 - e**2))`` agreed with the true anomaly to
  within 2.0e-15 rad at ``e`` = 0.0549, 0.3, 0.7, 0.9 and 0.99.
- ``nu - M`` (the equation of centre) is not one stage: ``c2 / c1**2`` is
  0.3125 for the series and 0.5 for a single stage at every ``eps``.
- ``M -> E`` is not a stage: :func:`kepler_solve` reaches ``E`` by
  Newton-Raphson at a declared precision.

This module ships three operations:

- :func:`pin_slot` — era-appropriate Antikythera transform
  (Freeth 2021 Supp S9).
- :func:`kepler_solve` — Newton-Raphson on Kepler's equation
  (Kepler 1609 + Smith 1979 starter).
- :func:`equation_of_centre` — Fourier-series ``nu - M`` in eccentricity
  (Brouwer & Clemence 1961 §3.2; Murray & Dermott 1999 §2.5).

Canonical SSoT (per ``[[feedback_science_is_ssot_not_project]]``): the
physics literature is the source of truth for these operations, not any
project instantiation. Antikythera-spectral / ephemerides-spectral are
substrate-consumers of these primitives, not their authors.
"""

from __future__ import annotations

import ctypes
from typing import Tuple

from srmech.math.rational import _Q61_HALF_PI_Q61, _Q61_ONE  # rc473 r1: the Q61 carrier
from srmech.math.rational import _q61_cos_core, _q61_reduce, _q61_sin_core
from srmech.math.rational import _is_finite  # rc473: the Q carrier's own finite test
from srmech.math.rational import atan2 as _ratan2  # §22: Class-N rational trig, not libm
from srmech.math.rational import cos as _rcos
from srmech.math.rational import sin as _rsin

from .. import _native


# Mirror of SRMECH_KEPLER_EOC_MAX_TERMS in srmech.h. Coefficients verified
# against Brouwer & Clemence 1961 §3.2 + Murray & Dermott 1999 eq 2.84.
EOC_MAX_TERMS: int = 6

_EOC_COEFFS: Tuple[float, ...] = (
    2.0,            # k=1: 2 e             sin(M)
    5.0 / 4.0,      # k=2: (5/4) e^2       sin(2M)
    13.0 / 12.0,    # k=3: (13/12) e^3     sin(3M)
    103.0 / 96.0,   # k=4: (103/96) e^4    sin(4M)
    1097.0 / 960.0, # k=5: (1097/960) e^5  sin(5M)
    1223.0 / 960.0, # k=6: (1223/960) e^6  sin(6M)
)

DEFAULT_KEPLER_TOLERANCE: float = 1e-12
DEFAULT_KEPLER_MAX_ITER: int = 30

# The largest iteration count ``srmech_kepler_solve``'s ``uint32_t max_iter``
# can carry. ``ctypes.c_uint32`` wraps anything wider, so a larger ``max_iter``
# is refused before dispatch in BOTH cells (rc473, `#T1188`).
_KEPLER_MAX_ITER_WIRE: int = (1 << 32) - 1

# rc473 repair round 1 (`#T1188`): Kepler's equation on the Q61 quarter-turn
# carrier. These three helpers are ``srmech_trig_kepler_q61``'s iteration in
# ``c/src/srmech_trig.c``, step for step, in Python ints; kepler_solve's
# docstring states the contract they share.
_KQ_SAT: int = 1 << 62
_KQ_HALF: int = _Q61_HALF_PI_Q61 >> 1


def _kq_emul(e_n: int, e_sh: int, x: int) -> int:
    """``e * x`` on the Q61 grid, rounded half away from zero (``kq_emul``).

    ``e == e_n / 2**e_sh`` exactly. The magnitude is a Class-K branch and the
    sign is re-applied as Class C, never ``abs()``.
    """
    ux = x if x >= 0 else -x
    q = (e_n * ux + (1 << (e_sh - 1))) >> e_sh
    return q if x >= 0 else -q


def _kq_sincos(oct_m: int, r: int) -> Tuple[int, int]:
    """``(sin E, cos E)`` in Q61 for ``E`` = octant ``oct_m`` plus ``r``.

    ``r`` is re-reduced by whole quarter turns first (``kq_sincos``), then read
    through the octant map ``rational.sin`` / ``rational.cos`` use.
    """
    j = 0
    for _ in range(4):
        if r > _KQ_HALF:
            r -= _Q61_HALF_PI_Q61
            j += 1
        elif r < -_KQ_HALF:
            r += _Q61_HALF_PI_Q61
            j -= 1
        else:
            break
    octant = (oct_m + j) & 3
    sc = _q61_sin_core(r)
    cc = _q61_cos_core(r)
    s = sc if octant == 0 else cc if octant == 1 else -sc if octant == 2 else -cc
    c = cc if octant == 0 else -sc if octant == 1 else -cc if octant == 2 else sc
    return s, c


def _kepler_q61(
    M_rad: float, e: float, tolerance: float, max_iter: int,
) -> Tuple[bool, float]:
    """``(converged, E)``: the Q61 Newton iteration, for ``0 < e < 1``.

    The caller has already refused an ``M_rad`` with no Q61 reduction, a
    non-finite ``tolerance`` and ``max_iter <= 0``. ``E`` is the float last
    mile either way — the converged answer, or the best-effort iterate a
    non-convergence message reports.
    """
    ok, oct_m, r_m = _q61_reduce(M_rad)
    assert ok, "kepler_solve refuses an M the Q61 reduction cannot hold first"
    e_n, e_d = float(e).as_integer_ratio()
    e_sh = e_d.bit_length() - 1
    eq = _kq_emul(e_n, e_sh, _Q61_ONE)
    s, _ = _kq_sincos(oct_m, r_m)                    # the Smith starter
    eps = _kq_emul(e_n, e_sh, s)
    t_n, t_d = float(tolerance).as_integer_ratio()
    converged = False
    for _ in range(max_iter):
        s, c = _kq_sincos(oct_m, r_m + eps)
        g = eps - _kq_emul(e_n, e_sh, s)
        gp = _Q61_ONE - _kq_emul(e_n, e_sh, c)
        ug = g if g >= 0 else -g                     # Class-K magnitude
        q = min(((ug << 62) + gp) // (2 * gp), _KQ_SAT)
        nxt = eps + q if g < 0 else eps - q          # Class-C re-orientation
        nxt = eq if nxt > eq else -eq if nxt < -eq else nxt
        step = nxt - eps
        eps = nxt
        us = step if step >= 0 else -step
        if us * t_d < t_n * _Q61_ONE:                # |step| * 2**-61 < tolerance
            converged = True
            break
    m_n, m_d = float(M_rad).as_integer_ratio()
    return converged, (m_n * _Q61_ONE + eps * m_d) / (m_d * _Q61_ONE)


def pin_slot(theta: float, pin_offset: float, pin_distance: float) -> float:
    """Antikythera pin-and-slot transform.

    A pin at radial offset ``pin_offset`` on the input gear engages a
    radial slot on a rocker whose axis is at distance ``pin_distance``
    from the input gear's center. As the input rotates by ``theta``
    (radians), the rocker follower turns by::

        phi = atan2(i * sin(theta), d + i * cos(theta))

    ``[[user_stance_kepler_shape_universal]]`` + PR #416 F2/F15/F17 read
    this transform as Kepler's shape. With ``eps = pin_offset /
    pin_distance``, ``pin_slot(theta, eps, 1.0)`` has sine harmonics
    ``(-1)**(k+1) eps**k / k``. Measured at rc473 (`#T1188`), pure cell,
    256-point quadrature: it is NOT the equation of centre ``nu - M`` to
    second order (``c2 / c1**2`` is 0.3125 for that series and 0.5 here, at
    every ``eps``); at ``theta = pi - M`` and ``eps = e`` it matches
    ``E - M`` through ``e**2`` and departs at ``e**3``; and at
    ``theta = pi - E`` and ``eps = e / (1 + sqrt(1 - e**2))``,
    ``E + 2 * pin_slot(theta, eps, 1.0)`` is the true anomaly to within
    2.0e-15 rad for ``e`` from 0.0549 to 0.99. The module docstring
    carries the figures.

    Args:
        theta: Input shaft angle in radians.
        pin_offset: Pin radius ``i`` on the input gear (any units;
            distance is a ratio).
        pin_distance: Center-to-center distance ``d`` between input
            and output axes.

    Returns:
        Follower angle ``phi`` in radians.

    Raises:
        ValueError: When ``pin_offset == 0 and pin_distance == 0``
            (atan2(0, 0) is implementation-defined) — refused HERE, before
            either projection, because it is a precondition on the ARGUMENTS
            and the C peer refuses the same pair; and (rc473, `#T1188`) for
            any ``theta`` the Class-N cascade cannot reduce, in the pure
            cascade's own words. ``srmech_pin_slot`` now PROPAGATES
            ``srmech_cos`` / ``srmech_sin`` / ``srmech_atan2``'s refusal
            instead of discarding it, so the native cell reaches the same
            refusal through the C symbol rather than around it.

            **rc473 twin-defect pass (`#T1188`) — the GEOMETRY slots.** A
            non-finite ``pin_offset`` or ``pin_distance`` is refused by
            ``srmech_pin_slot`` itself, because no callee refuses every
            non-finite value — in C it enters at bare double arithmetic whose
            one callee, ``srmech_atan2``, refuses a NaN but serves an infinite
            argument (measured at the symbol: ``srmech_atan2(inf, inf)`` ->
            ``(0, 0.7853981633974483)``), and in
            the pure cascade at ``pin_distance + pin_offset * cos(theta)``,
            which is ``float + Q`` with ``Q`` the finite-rational carrier.
            MEASURED on an authenticated rc473 cell (ABI 26) at ``1ab8d405b``,
            before the repair: ``pin_slot(0.0, 1.0, +inf)`` returned ``0.0``
            through C and ``-inf`` returned ``3.141592653589793``, while the
            pure projection raised ``TypeError`` on both — a serve-vs-refuse
            divergence (ADR-0009 §2.4) at a slot no §1.2 row named. The
            check that supplies the text sits AFTER the native call, the
            placement ``equation_of_centre`` uses, so a native cell reaches
            the refusal through the C symbol and a C regression there is
            visible to every public-op gate;
            ``tests/test_kepler_non_finite_slots_rc473.py`` requires both the
            symbol's refusal and that the public op consulted it.
    """
    if pin_offset == 0.0 and pin_distance == 0.0:
        raise ValueError(
            "pin_slot: pin_offset and pin_distance cannot both be zero"
        )
    if _native.HAS_NATIVE:
        out = ctypes.c_double(0.0)
        rc = _native.LIB.srmech_pin_slot(
            ctypes.c_double(theta),
            ctypes.c_double(pin_offset),
            ctypes.c_double(pin_distance),
            ctypes.byref(out),
        )
        if rc == _native.SRMECH_OK:
            return out.value
        if rc != _native.SRMECH_ERR_BAD_INPUT:
            raise ValueError(f"srmech_pin_slot returned status {rc}")
        # rc473 (`#T1188`): the C peer REFUSED. Fall through to the pure
        # cascade, which reaches the same refusal one line later and names it
        # in its own words — one text in both cells (rc466 rule D1), reached
        # only AFTER the C symbol has been consulted. The measured
        # alternative is the bare status number: through rc472 this line read
        # ``raise ValueError(f"srmech_pin_slot returned status {rc}")``, which
        # says "status 2" where the pure cell says
        # "cos: |x| too large for the Q61 octant reduction; got …".
    # Pure-Python fallback, and the refusal path above. The pin-slot internal
    # cascade flows Q (exact ALU arithmetic); ``float()`` is the FPU last-mile
    # rotate that matches the native ``srmech_pin_slot`` c_double contract (the
    # angle is the observable).
    #
    # rc473 twin-defect pass (`#T1188`): the finite-geometry check lives HERE,
    # after the native call, and not before dispatch. srmech_pin_slot refuses
    # a non-finite pin_offset / pin_distance itself, so a native cell reaches
    # this line only after the C symbol has said SRMECH_ERR_BAD_INPUT, and this
    # check supplies the one text both cells raise. Before dispatch it would
    # answer before C was consulted, which is the shape that kept
    # equation_of_centre's C defect invisible for eight release candidates.
    if not (_is_finite(pin_offset) and _is_finite(pin_distance)):
        raise ValueError(
            f"pin_slot: pin_offset and pin_distance must be finite (Q is the "
            f"finite-rational carrier); got pin_offset={pin_offset!r}, "
            f"pin_distance={pin_distance!r}"
        )
    x = pin_distance + pin_offset * _rcos(theta)
    y = pin_offset * _rsin(theta)
    return float(_ratan2(y, x))


def kepler_solve(
    M_rad: float,
    e: float,
    tolerance: float = DEFAULT_KEPLER_TOLERANCE,
    max_iter: int = DEFAULT_KEPLER_MAX_ITER,
) -> float:
    """Newton-Raphson solver for Kepler's equation ``M = E - e * sin(E)``.

    Canonical SSoT: Kepler (1609) *Astronomia Nova*. Newton-Raphson
    starter via Smith (1979) Celestial Mech 19, 163: ``E_0 = M + e * sin(M)``.
    MEASURED at rc473 (`#T1188`) with the default tolerance, over eight ``M``
    from 0.1 to 3.1: 3 iterations at ``e = 0.0549``, 3 to 5 for ``e`` from
    0.2 to 0.5, and 3 to 7 for ``e`` from 0.9 to 0.999.

    Args:
        M_rad: Mean anomaly in radians.
        e: Eccentricity, ``0 <= e < 1``.
        tolerance: Halt when ``|step| * 2**-61 < tolerance``, the step
            in Q61 units (see the Convergence paragraph below).
        max_iter: Maximum Newton-Raphson iterations.

    Returns:
        Eccentric anomaly ``E`` in radians.

    Raises:
        ValueError: For ``e < 0``, ``e >= 1``, ``max_iter <= 0``,
            ``max_iter > 2**32 - 1``, or a non-finite ``tolerance``; and
            (rc473, `#T1188`), when ``e > 0``, for any ``M_rad`` the Class-N
            ``sin`` cascade cannot reduce, in the pure cascade's own words (at
            ``e == 0`` ``M_rad`` is returned for any value, NaN and ±inf
            included, as ``srmech_kepler_solve`` does). Through rc472
            ``srmech_kepler_solve`` discarded ``srmech_sin``'s refusal, the
            Newton iteration never moved ``E`` off its ``M`` initial guess and
            the caller was handed ``E == M`` with ``SRMECH_OK``; rc473
            propagated the refusal, and since repair round 1 the symbol
            refuses that ``M`` at the Q61 reduction, before any iterate
            exists.

            **rc473 twin-defect pass (`#T1188`) — the TOLERANCE slot.** Until
            repair round 1 it reached no callee: it was only ever the
            right-hand side of ``|delta| < tolerance``, so a non-finite one
            was never examined.
            MEASURED on an authenticated rc473 cell (ABI 26) at ``1ab8d405b``,
            before the repair, at ``M = pi/2``, ``e = 0.0549``,
            ``max_iter = 20``: ``tolerance=+inf`` returned
            ``1.625613861425157`` through C — the ONE-Newton-step estimate,
            reported as converged — where the pure projection raised
            ``TypeError``; ``nan`` and ``-inf`` raised "did not converge"
            through C, a story about an argument that was never a tolerance.
            ``srmech_kepler_solve`` now refuses all three before its own
            ``e == 0`` shortcut, and the check supplying the text sits after
            the native call and before the pure ``e == 0.0`` return, so a
            native cell reaches the refusal through the C symbol.

            **The MAX_ITER wire (`#T1188`).** ``srmech_kepler_solve`` takes a
            ``uint32_t``, and ``ctypes.c_uint32`` WRAPS: measured at
            ``1ab8d405b``, ``max_iter=2**32 + 1`` crossed the wire as ``1``,
            C ran one Newton step and the native cell raised "did not
            converge in 4294967297 iterations" where the pure cell returned
            ``1.625613861239322``. No C code can refuse a value its parameter
            type cannot hold, so this precondition is checked BEFORE
            dispatch, in both cells, with one text — the one refusal here the
            C projection cannot express.
        RuntimeError: If not converged within ``max_iter`` iterations. The
            message reports ``best_E`` as the float last mile of the final
            iterate — the double the C peer writes — so both cells raise ONE
            text.

    **Convergence, on the Q61 carrier (rc473 repair round 1, `#T1188`).**
    Through the twin-defect pass the C peer iterated on ``double`` and this
    body on an exact, ever-growing ``Q``, and the two decided convergence on
    different quantities: a double step can reach an exact ``0.0`` or stall
    one ULP away, and an exact-``Q`` step does neither. MEASURED at
    ``2eb05877f`` on an authenticated WSL2 gcc 13.3.0 Release cell (ABI 26)
    against a pure sibling with no library file, ``max_iter=30``: over ``M``
    in {pi/2, 1, 3, 0.1, 100, 1e6} x ``e`` in {0.0549, 0.5, 0.9} x 17
    tolerances from ``1e-12`` to ``5e-324``, 134 of 306 rows returned a
    different verdict in the two cells, in both directions; the non-convergence
    message rendered ``best_E`` as a double natively and as the exact ``Q``
    here; and ADR-0009 row 52's ``kepler_solve(2**53, 0.999)`` returned
    ``9007199254740992.0`` natively where this body raised.

    Both projections now run ONE integer iteration (``_kepler_q61`` here,
    ``srmech_trig_kepler_q61`` in ``c/src/srmech_trig.c``):

    * ``M`` is reduced once to its Q61 octant and residue; ``E`` is carried as
      ``M + eps`` with ``eps`` a Q61 integer, and ``sin E`` / ``cos E`` are
      read off the residue plus ``eps``, re-reduced by whole quarter turns,
      through the Q61 Taylor cores ``_q61_sin_core`` / ``_q61_cos_core`` — no
      float between steps.
    * ``e`` multiplies on the Q61 grid, rounded half away from zero; the
      Newton step ``round(g * 2**61 / g')`` is one integer division; and the
      iterate is held in its own bracket ``|eps| <= round(e * 2**61)``, where
      every fixed point lies because ``|sin E| <= 1`` (so ``|eps| * 2**-61``
      exceeds ``e`` by at most ``2**-62``, at a rounding tie).
    * CONVERGED means ``|step| * 2**-61 < tolerance``, decided exactly. A
      zero or negative tolerance is never met, as before; a tolerance below
      one grid unit is met only by a zero step.
    * The answer is ``M + eps * 2**-61`` correctly rounded to ``float``
      (ties to even) — the last mile.

    The carrier resolves ``2**-61`` rad absolute, the resolution
    ``rational.sin`` itself has. This is Newton-Raphson at that declared
    precision: not an exact root of Kepler's equation, and not a cyclic form
    of it. MEASURED after the repair on the same cells:
    the 306 frontier rows and the 107 slot-sweep rows are the same outcome in
    both cells, verdict, value and text; the C symbol matches this iteration
    bit for bit over a seeded 200000-row fuzz (184218 rows compared, 15782
    refused by both at the reduction, 0 mismatches); and served values move
    where the two old loops rounded differently — ``kepler_solve(pi/2, 0.9)``
    was ``2.2634151063569425`` in both cells and is ``2.263415106356943``.
    """
    if not (0.0 <= e < 1.0):
        raise ValueError(f"kepler_solve: e must satisfy 0 <= e < 1; got {e}")
    if max_iter <= 0:
        raise ValueError(f"kepler_solve: max_iter must be positive; got {max_iter}")
    if max_iter > _KEPLER_MAX_ITER_WIRE:
        # rc473 (`#T1188`): the uint32 wire cannot carry it, so C cannot refuse
        # it — c_uint32 would wrap it silently. Checked before dispatch, in
        # both cells, with one text. See the docstring's MAX_ITER paragraph.
        raise ValueError(
            f"kepler_solve: max_iter must be at most 2**32 - 1 (the uint32 "
            f"iteration count srmech_kepler_solve takes); got {max_iter}"
        )
    if _native.HAS_NATIVE:
        out = ctypes.c_double(0.0)
        rc = _native.LIB.srmech_kepler_solve(
            ctypes.c_double(M_rad),
            ctypes.c_double(e),
            ctypes.c_double(tolerance),
            ctypes.c_uint32(max_iter),
            ctypes.byref(out),
        )
        if rc == _native.SRMECH_OK:
            return out.value
        if rc == _native.SRMECH_ERR_OVERFLOW:
            raise RuntimeError(
                f"kepler_solve: did not converge in {max_iter} iterations "
                f"(M={M_rad}, e={e}, best_E={out.value})"
            )
        if rc != _native.SRMECH_ERR_BAD_INPUT:
            raise ValueError(f"srmech_kepler_solve returned status {rc}")
        # rc473 (`#T1188`): the C peer REFUSED. Fall through to the pure
        # cascade for the refusal text, AFTER the C symbol has answered. C
        # refuses two things here, and the pure body below re-raises each in
        # the same order: a non-finite tolerance (checked before its own
        # ``e == 0`` shortcut, as the tolerance check below precedes the pure
        # one), and, for ``e > 0`` only, an ``M_rad`` the Q61 reduction cannot
        # hold (which ``rational.sin`` refuses just before the Q61 iteration).
    # Pure-Python fallback, and the refusal path above.
    #
    # rc473 twin-defect pass (`#T1188`): the tolerance check lives HERE, after
    # the native call and before the ``e == 0.0`` return — not before dispatch.
    # srmech_kepler_solve refuses a non-finite tolerance itself, so a native
    # cell reaches this line only through the C symbol's refusal.
    if not _is_finite(tolerance):
        raise ValueError(
            f"kepler_solve: tolerance must be finite (Q is the "
            f"finite-rational carrier); got {tolerance!r}"
        )
    if e == 0.0:
        return M_rad
    # rc473 repair round 1 (`#T1188`): the refusal of an M the Q61 reduction
    # cannot hold is rational.sin's, in its own words, and C refuses the same M
    # at the same reduction. Then the one Q61 iteration both projections run.
    _rsin(M_rad)
    converged, E = _kepler_q61(M_rad, e, tolerance, max_iter)
    if converged:
        return E                   # FPU last mile, the double srmech_kepler_solve writes
    raise RuntimeError(
        f"kepler_solve: did not converge in {max_iter} iterations "
        f"(M={M_rad}, e={e}, best_E={E})"
    )


def equation_of_centre(
    M_rad: float,
    e: float,
    n_terms: int = 4,
) -> float:
    """Fourier-series equation of centre ``nu - M`` (true minus mean anomaly).

    Principal-term-per-harmonic in eccentricity::

        nu - M = sum_{k=1..n} c_k * e^k * sin(k * M)

    with ``c_k = [2, 5/4, 13/12, 103/96, 1097/960, 1223/960]`` for
    ``k = 1..6``. Coefficients verified against Brouwer & Clemence
    (1961) §3.2 + Murray & Dermott (1999) §2.5 eq 2.84-2.88.

    Args:
        M_rad: Mean anomaly in radians.
        e: Eccentricity, ``0 <= e < 1``.
        n_terms: Number of harmonics (1..6).

    Returns:
        ``nu - M`` in radians.

    Raises:
        ValueError: For ``e < 0``, ``e >= 1``, ``n_terms == 0``, or
            ``n_terms > EOC_MAX_TERMS``; and for any harmonic
            ``(k + 1) * M_rad`` that is not finite or whose magnitude reaches
            :data:`srmech.math.rational.Q61_TRIG_RANGE` (``2**55``) — the two
            refusals :func:`srmech.math.rational.sin` makes, in its own words.

            rc472 raised those two HERE, before ``if _native.HAS_NATIVE:``,
            because the C peer discarded ``srmech_sin``'s status and the
            native cell returned a value where the pure cell raised. rc473
            (`#T1188`) repaired ``srmech_kepler.c`` instead, and DELETED that
            pre-dispatch guard: a guard that answers before the C symbol is
            consulted is exactly what kept the defect invisible for eight
            release candidates. The refusal is now the C peer's, reached
            through it, and the pure cascade below supplies the text.
            MEASURED at rc473 over 118 candidate ``M_rad`` values x 6
            ``n_terms`` = 708 direct ``srmech_equation_of_centre`` calls: the
            deleted guard and the C symbol refuse the SAME 364 inputs, 0
            disagreements.
    """
    if not (0.0 <= e < 1.0):
        raise ValueError(
            f"equation_of_centre: e must satisfy 0 <= e < 1; got {e}"
        )
    if not (1 <= n_terms <= EOC_MAX_TERMS):
        raise ValueError(
            f"equation_of_centre: n_terms must be in [1, {EOC_MAX_TERMS}]; "
            f"got {n_terms}"
        )
    # rc473 (`#T1188`): rc472's pre-dispatch guard loop stood HERE and is
    # GONE. It walked the harmonics and raised rational.sin's two refusals
    # before `if _native.HAS_NATIVE:` was consulted, which made every parity
    # gate green while srmech_kepler.c:180 went on discarding srmech_sin's
    # status -- the cover satisfied the instrument without touching the thing
    # it measured. rc473 repaired the C site; the refusal is the C peer's now,
    # and the pure cascade below supplies its text.
    if _native.HAS_NATIVE:
        out = ctypes.c_double(0.0)
        rc = _native.LIB.srmech_equation_of_centre(
            ctypes.c_double(M_rad),
            ctypes.c_double(e),
            ctypes.c_uint32(n_terms),
            ctypes.byref(out),
        )
        if rc == _native.SRMECH_OK:
            return out.value
        if rc != _native.SRMECH_ERR_BAD_INPUT:
            raise ValueError(
                f"srmech_equation_of_centre returned status {rc}")
        # rc473 (`#T1188`): the C peer REFUSED -- fall through to the pure
        # cascade, which walks the same harmonics in the same order and raises
        # rational.sin's own text. float(...) inside rational.sin is what makes
        # that text match for an int M_rad: the int spelling would render
        # 36028797018963972 where the pure cascade says 3.602879701896397e+16.
    # Pure-Python fallback, and the refusal path above.
    delta = 0.0
    e_power = 1.0
    for k_idx in range(n_terms):
        e_power *= e
        harmonic = (k_idx + 1) * M_rad
        delta += _EOC_COEFFS[k_idx] * e_power * _rsin(harmonic)
    return float(delta)            # FPU last-mile (native srmech_equation_of_centre → c_double)


__all__ = [
    "DEFAULT_KEPLER_MAX_ITER",
    "DEFAULT_KEPLER_TOLERANCE",
    "EOC_MAX_TERMS",
    "equation_of_centre",
    "kepler_solve",
    "pin_slot",
]
