"""Class K — equation-of-centre / pin-slot (Kepler-shape projection-shadow).

Continuous projection-shadow of the integer-cyclic upstream (Class I
cyclic groups + Class J prime-period). Per ``[[user_stance_kepler_shape_universal]]``
+ PR #416 F2/F15/F17: Kepler-equation algebra IS pin-slot composition.

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

from srmech.amsc.rational import atan2 as _ratan2  # §22: Class-N rational trig, not libm
from srmech.amsc.rational import cos as _rcos
from srmech.amsc.rational import sin as _rsin

from . import _native


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


def pin_slot(theta: float, pin_offset: float, pin_distance: float) -> float:
    """Antikythera pin-and-slot transform.

    A pin at radial offset ``pin_offset`` on the input gear engages a
    radial slot on a rocker whose axis is at distance ``pin_distance``
    from the input gear's center. As the input rotates by ``theta``
    (radians), the rocker follower turns by::

        phi = atan2(i * sin(theta), d + i * cos(theta))

    Per ``[[user_stance_kepler_shape_universal]]`` + PR #416 F2/F15/F17,
    this transform IS the Kepler equation of centre to second order in
    eccentricity ``epsilon = pin_offset / pin_distance``.

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
            (atan2(0, 0) is implementation-defined).
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
        if rc != _native.SRMECH_OK:
            raise ValueError(f"srmech_pin_slot returned status {rc}")
        return out.value
    # Pure-Python fallback. The pin-slot internal cascade flows Q (exact ALU
    # arithmetic); ``float()`` is the FPU last-mile rotate that matches the
    # native ``srmech_pin_slot`` c_double contract (the angle is the observable).
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
    Converges in 4-6 iterations for ``e < 0.5``; ``e >= 0.95`` may need
    more (raise ``max_iter``).

    Args:
        M_rad: Mean anomaly in radians.
        e: Eccentricity, ``0 <= e < 1``.
        tolerance: Halt when ``|delta E| < tolerance``.
        max_iter: Maximum Newton-Raphson iterations.

    Returns:
        Eccentric anomaly ``E`` in radians.

    Raises:
        ValueError: For ``e < 0``, ``e >= 1``, or ``max_iter <= 0``.
        RuntimeError: If not converged within ``max_iter`` iterations.
    """
    if not (0.0 <= e < 1.0):
        raise ValueError(f"kepler_solve: e must satisfy 0 <= e < 1; got {e}")
    if max_iter <= 0:
        raise ValueError(f"kepler_solve: max_iter must be positive; got {max_iter}")
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
        raise ValueError(f"srmech_kepler_solve returned status {rc}")
    # Pure-Python fallback.
    if e == 0.0:
        return M_rad
    E = M_rad + e * _rsin(M_rad)
    for _ in range(max_iter):
        f = E - e * _rsin(E) - M_rad
        f_prime = 1.0 - e * _rcos(E)
        delta = f / f_prime
        E -= delta
        # Class-K magnitude of the Newton step as an EXPLICIT sign-branch,
        # never an ALU abs().
        delta_mag = delta if delta >= 0.0 else -delta
        if delta_mag < tolerance:
            return float(E)        # FPU last-mile (native srmech_kepler_solve → c_double)
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
            ``n_terms > EOC_MAX_TERMS``.
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
    if _native.HAS_NATIVE:
        out = ctypes.c_double(0.0)
        rc = _native.LIB.srmech_equation_of_centre(
            ctypes.c_double(M_rad),
            ctypes.c_double(e),
            ctypes.c_uint32(n_terms),
            ctypes.byref(out),
        )
        if rc != _native.SRMECH_OK:
            raise ValueError(f"srmech_equation_of_centre returned status {rc}")
        return out.value
    # Pure-Python fallback.
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
