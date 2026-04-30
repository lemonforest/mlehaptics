"""Bridge API — Pyodide-friendly entry surface for `antikythera-spectral`.

Each method returns a Pyodide-JSON-serializable dict with at least an
``ok`` key:

- ``{"ok": True, ...}`` on success
- ``{"ok": False, "error": "..."}`` on caller-side input error
  (raised exceptions for unexpected failures)

Numpy arrays in return values are real-valued (``Float32`` for amplitude
payloads, real+imag interleaved for complex states) so JS consumers can
use ``new Float32Array(...)`` directly without conversion.

The 28-method surface of v0.1.0 is split across phases 4-12 of the
release plan. This module adds them incrementally as each phase lands.

Phase 4 (this commit): §5.1 + §5.2 — state↔date (7 methods).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

from antikythera_spectral._research.encode_ant import (
    DIAL_SPECS,
    D_CALLIPPIC,
    D_PACKING,
    DialSpec,
    LCMState,
    REFERENCE_JD,
    UnsupportedDialError,
    encode_ant_callippic,
    encode_ant_lcm,
    encode_ant_packing,
)
from antikythera_spectral._research.dial_decoder import (
    decode_dial_dense,
    decode_dial_lcm,
)
from antikythera_spectral._research.rendering import (
    render_dial,
    render_spatial,
)
from antikythera_spectral.version import __version__


# ──────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────

# Frozen lookup tables. Built once at module import; tiny.
_DIAL_BY_NAME: Dict[str, DialSpec] = {s.name: s for s in DIAL_SPECS}
_DIAL_NAMES: Tuple[str, ...] = tuple(s.name for s in DIAL_SPECS)
_SUPPORTED_DIMS: Tuple[int, ...] = (D_CALLIPPIC, D_PACKING)
_SUPPORTED_LAYOUTS: Tuple[str, ...] = ("dial", "spatial")
_DATA_DIR: Path = Path(__file__).resolve().parent / "_data"


def _err(message: str) -> Dict[str, Any]:
    """Build a caller-side error response."""
    return {"ok": False, "error": message}


def _validate_jd(jd_tdb: Any) -> Optional[Dict[str, Any]]:
    """Return an error dict if jd_tdb is not a finite float, else None."""
    try:
        f = float(jd_tdb)
    except (TypeError, ValueError):
        return _err(f"jd_tdb must be a number, got {type(jd_tdb).__name__}")
    if not math.isfinite(f):
        return _err(f"jd_tdb must be finite, got {f}")
    # Sanity-bound to reasonable JD range (-13 200 BCE .. +17 200 CE).
    if f < -1_000_000 or f > 5_000_000:
        return _err(f"jd_tdb {f} is far outside any plausible range")
    return None


def _validate_dim(D: Any) -> Optional[Dict[str, Any]]:
    """Return an error dict if D isn't a supported dimension."""
    if D not in _SUPPORTED_DIMS:
        return _err(
            f"D must be one of {_SUPPORTED_DIMS}, got {D!r}"
        )
    return None


def _validate_dial_name(dial: Any) -> Optional[Dict[str, Any]]:
    """Return an error dict if `dial` isn't a known dial name."""
    if not isinstance(dial, str):
        return _err(f"dial must be a string, got {type(dial).__name__}")
    if dial not in _DIAL_BY_NAME:
        return _err(
            f"unknown dial {dial!r}; valid: {list(_DIAL_NAMES)}"
        )
    return None


def _interleave_complex(state: np.ndarray) -> np.ndarray:
    """Pack a complex-D-shaped array into real+imag-interleaved Float32 of length 2*D.

    The web-side consumer reads this as a `Float32Array` of length 2*D
    where ``arr[2*k] = Re(state[k])``, ``arr[2*k+1] = Im(state[k])``.
    Pyodide passes Float32 arrays to JS as a typed array directly.
    """
    if not np.iscomplexobj(state):
        raise TypeError("state must be a complex numpy array")
    out = np.empty(2 * state.size, dtype=np.float32)
    out[0::2] = state.real.astype(np.float32, copy=False)
    out[1::2] = state.imag.astype(np.float32, copy=False)
    return out


def _angle_deg_for_dial(spec: DialSpec, jd_tdb: float) -> float:
    """Continuous angle (degrees in [0, 360)) for a dial at a date."""
    days = jd_tdb - REFERENCE_JD
    period = spec.cycle_period_days
    if period is None or period <= 0:
        raise ValueError(f"dial {spec.name!r} has no usable cycle period")
    phase = (days / period) % 1.0
    return float(phase * 360.0)


def _residue_for_dial(spec: DialSpec, jd_tdb: float) -> int:
    """Integer residue 0..modulus-1 for a dial at a date (D-independent)."""
    return int(spec.integer_residue(jd_tdb))


def _read_manifest() -> Dict[str, Any]:
    """Load `_data/manifest.json` (codegen-stamped); returns {} on miss."""
    p = _DATA_DIR / "manifest.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


# ──────────────────────────────────────────────────────────────────────
# §5.1 — State ← date (5 methods)
# ──────────────────────────────────────────────────────────────────────

def get_dial_state(jd_tdb: float, *, D: int = D_CALLIPPIC) -> Dict[str, Any]:
    """Encode a date as the per-dial residue state plus the HDC vector.

    Parameters
    ----------
    jd_tdb : float
        Julian Day in TDB. The mechanism's reference epoch is ~205 BCE
        (JD 1684595.0); see ``REFERENCE_JD``.
    D : int, optional
        Encoder dimension. Must be ``940`` (Callippic) or ``13440``
        (packing). Default: 940.

    Returns
    -------
    dict
        ::

            {
                "ok": True,
                "jd_tdb": float,
                "D": int,
                "dials": {
                    "<name>": {
                        "residue": int,
                        "modulus": int,
                        "angle_deg": float,
                        "cycle_period_days": float | None,
                        "supported_at_d": bool,
                    },
                    ...
                },
                "state": {
                    "shape": [int],          # [D]
                    "dtype": "complex128",
                    "interleaved_f32": list[float],  # length 2*D, real+imag interleaved
                },
            }

    The ``state.interleaved_f32`` array is in the format the web UI
    can hand to a ``Float32Array`` for shader uniforms. Per ADR
    ``0002-bridge-api-shape.md``.
    """
    err = _validate_jd(jd_tdb)
    if err:
        return err
    err = _validate_dim(D)
    if err:
        return err
    jd = float(jd_tdb)

    if D == D_CALLIPPIC:
        state = encode_ant_callippic(jd)
    else:
        state = encode_ant_packing(jd)

    interleaved = _interleave_complex(state)

    dials_out: Dict[str, Dict[str, Any]] = {}
    for spec in DIAL_SPECS:
        if spec.cycle_period_days is None or spec.cycle_period_days <= 0:
            continue
        dials_out[spec.name] = {
            "residue": _residue_for_dial(spec, jd),
            "modulus": int(spec.cycle_modulus),
            "angle_deg": _angle_deg_for_dial(spec, jd),
            "cycle_period_days": float(spec.cycle_period_days),
            "supported_at_d": bool(spec.is_supported(D)),
        }

    return {
        "ok": True,
        "jd_tdb": jd,
        "D": int(D),
        "dials": dials_out,
        "state": {
            "shape": [int(state.size)],
            "dtype": "complex128",
            "interleaved_f32": interleaved.tolist(),
        },
    }


def get_dial_angle(jd_tdb: float, dial: str) -> Dict[str, Any]:
    """Continuous angle (degrees, [0, 360)) for a single dial at a date.

    Independent of encoder D: always uses the cycle's true period in
    days, not the quantised residue.

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": float, "dial": str, "angle_deg": float,
        "residue": int, "modulus": int}``
    """
    err = _validate_jd(jd_tdb)
    if err:
        return err
    err = _validate_dial_name(dial)
    if err:
        return err
    jd = float(jd_tdb)
    spec = _DIAL_BY_NAME[dial]
    if spec.cycle_period_days is None or spec.cycle_period_days <= 0:
        return _err(f"dial {dial!r} has no usable cycle period")
    return {
        "ok": True,
        "jd_tdb": jd,
        "dial": dial,
        "angle_deg": _angle_deg_for_dial(spec, jd),
        "residue": _residue_for_dial(spec, jd),
        "modulus": int(spec.cycle_modulus),
    }


def get_pointer_xy(jd_tdb: float, *, layout: str = "dial",
                    D: int = D_CALLIPPIC) -> Dict[str, Any]:
    """Per-dial (x, y) coordinates for rendering.

    Parameters
    ----------
    jd_tdb : float
        Julian Day in TDB.
    layout : str, optional
        ``'dial'`` (concentric Antikythera dial layout) or ``'spatial'``
        (orrery / orbital-radii layout). Default: ``'dial'``.
    D : int, optional
        Encoder dimension. Default: 940 (Callippic).

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": float, "layout": str, "pointers":
        {"<dial>": [x, y], ...}}``
    """
    err = _validate_jd(jd_tdb)
    if err:
        return err
    err = _validate_dim(D)
    if err:
        return err
    if layout not in _SUPPORTED_LAYOUTS:
        return _err(
            f"layout must be one of {_SUPPORTED_LAYOUTS}, got {layout!r}"
        )

    jd = float(jd_tdb)
    if D == D_CALLIPPIC:
        state = encode_ant_callippic(jd)
    else:
        state = encode_ant_packing(jd)

    if layout == "dial":
        xy = render_dial(state, D=D)
    else:
        xy = render_spatial(state, D=D)

    return {
        "ok": True,
        "jd_tdb": jd,
        "layout": layout,
        "pointers": {name: [float(c[0]), float(c[1])] for name, c in xy.items()},
    }


def get_all_dial_metadata() -> Dict[str, Any]:
    """List of supported dials with cycle metadata.

    Returns
    -------
    dict
        ::

            {
                "ok": True,
                "n_dials": int,
                "dials": [
                    {
                        "name": str,
                        "numerator": int,
                        "denominator": int,
                        "modern_days": float | None,
                        "mechanism_days": float | None,
                        "cycle_modulus": int,
                        "tag": str,
                        "supported_dims": [int],   # subset of [940, 13440]
                        "notes": str,
                    },
                    ...
                ],
            }
    """
    out: List[Dict[str, Any]] = []
    for spec in DIAL_SPECS:
        c = spec.cycle
        out.append({
            "name": spec.name,
            "numerator": int(c.numerator),
            "denominator": int(c.denominator),
            "modern_days": (
                float(c.modern_days) if c.modern_days is not None else None
            ),
            "mechanism_days": (
                float(c.mechanism_days)
                if c.mechanism_days is not None
                else None
            ),
            "cycle_modulus": int(spec.cycle_modulus),
            "tag": str(c.tag),
            "supported_dims": [
                int(D) for D in _SUPPORTED_DIMS if spec.is_supported(D)
            ],
            "notes": str(c.notes),
        })
    return {"ok": True, "n_dials": len(out), "dials": out}


def get_version() -> Dict[str, Any]:
    """Package version + frozen-data manifest.

    Returns
    -------
    dict
        ``{"ok": True, "package": "antikythera-spectral", "version":
        "0.1.0rc1", "manifest": {...}}``

    The ``manifest`` field carries the codegen-stamped frozen-data
    manifest (source-commit hash, per-file SHAs); empty dict if the
    manifest file is missing.
    """
    return {
        "ok": True,
        "package": "antikythera-spectral",
        "version": __version__,
        "manifest": _read_manifest(),
    }


# ──────────────────────────────────────────────────────────────────────
# §5.2 — Date ← state (2 methods)
# ──────────────────────────────────────────────────────────────────────

def _coerce_state(state_vec: Any, D: int) -> np.ndarray:
    """Accept several state representations and return a complex128 array.

    Supported inputs:

    - numpy.ndarray of shape ``(D,)`` and dtype complex128
    - numpy.ndarray / list of length ``2*D`` interleaved real+imag floats
    - dict ``{"interleaved_f32": [...]}`` (the bridge's own output format)

    Raises ``ValueError`` on any other shape / type.
    """
    if isinstance(state_vec, dict):
        if "interleaved_f32" in state_vec:
            state_vec = state_vec["interleaved_f32"]
        elif "real" in state_vec and "imag" in state_vec:
            real = np.asarray(state_vec["real"], dtype=np.float32)
            imag = np.asarray(state_vec["imag"], dtype=np.float32)
            if real.size != imag.size or real.size != D:
                raise ValueError(
                    f"state real/imag must have length {D}, "
                    f"got {real.size}/{imag.size}"
                )
            return real.astype(np.complex128) + 1j * imag.astype(np.complex128)
        else:
            raise ValueError(
                "state dict must have 'interleaved_f32' or 'real'+'imag' keys"
            )

    arr = np.asarray(state_vec)
    if np.iscomplexobj(arr):
        if arr.size != D:
            raise ValueError(
                f"complex state must have length D={D}, got {arr.size}"
            )
        return arr.astype(np.complex128, copy=False)

    # Flat real array; expect interleaved real+imag of length 2*D.
    arr = arr.astype(np.float32, copy=False).ravel()
    if arr.size != 2 * D:
        raise ValueError(
            f"interleaved state must have length 2*D={2 * D}, got {arr.size}"
        )
    return arr[0::2].astype(np.complex128) + 1j * arr[1::2].astype(np.complex128)


def decode_dial(state_vec: Any, dial: str, *,
                D: int = D_CALLIPPIC) -> Dict[str, Any]:
    """Decode the residue of a single dial from a state vector.

    Parameters
    ----------
    state_vec : numpy.ndarray | list | dict
        Complex128 array of length D, OR interleaved real+imag Float32
        of length 2*D, OR ``{"interleaved_f32": [...]}`` (the bridge's
        own output shape).
    dial : str
        Dial name; must be in ``get_all_dial_metadata().dials[*].name``.
    D : int, optional
        Encoder dimension that produced the state. Default: 940.

    Returns
    -------
    dict
        ``{"ok": True, "dial": str, "D": int, "recovered_residue": int}``
    """
    err = _validate_dim(D)
    if err:
        return err
    err = _validate_dial_name(dial)
    if err:
        return err

    spec = _DIAL_BY_NAME[dial]
    if not spec.is_supported(D):
        return _err(
            f"dial {dial!r} not supported at D={D}"
        )
    try:
        state = _coerce_state(state_vec, D)
    except (TypeError, ValueError) as exc:
        return _err(str(exc))

    try:
        recovered = decode_dial_dense(state, dial, D)
    except UnsupportedDialError as exc:
        return _err(str(exc))

    return {
        "ok": True,
        "dial": dial,
        "D": int(D),
        "recovered_residue": int(recovered),
    }


def decode_to_jd(state_vec: Any, *,
                 D: int = D_CALLIPPIC,
                 reference_jd: float = REFERENCE_JD) -> Dict[str, Any]:
    """Best-fit JD from a state vector (per-dial vote).

    For each dial, decode the residue and compute the JD shift that
    matches; report the median + spread across dials.

    Parameters
    ----------
    state_vec : numpy.ndarray | list | dict
        Same accepted formats as ``decode_dial``.
    D : int, optional
        Encoder dimension. Default: 940.
    reference_jd : float, optional
        Anchor JD to add the recovered phase to. Default: ``REFERENCE_JD``
        (~205 BCE).

    Returns
    -------
    dict
        ::

            {
                "ok": True,
                "D": int,
                "reference_jd": float,
                "estimates": {dial: jd},
                "median_jd": float,
                "spread_days": float,        # max - min across dials
            }

    Caveat: dense-encoder decoding has cross-talk between dials.  The
    per-dial JD estimates may disagree; the spread is reported as a
    confidence proxy.  Use the LCM variant (D=lcm) for exact decoding;
    that path lands in phase 4-extra.
    """
    err = _validate_dim(D)
    if err:
        return err
    try:
        state = _coerce_state(state_vec, D)
    except (TypeError, ValueError) as exc:
        return _err(str(exc))

    estimates: Dict[str, float] = {}
    for spec in DIAL_SPECS:
        if not spec.is_supported(D):
            continue
        if spec.cycle_period_days is None or spec.cycle_period_days <= 0:
            continue
        try:
            recovered = decode_dial_dense(state, spec.name, D)
        except (UnsupportedDialError, ValueError):
            continue
        # recovered ∈ [0, D); convert to phase fraction, then to days.
        phase = float(recovered) / float(D)
        jd_est = reference_jd + phase * spec.cycle_period_days
        estimates[spec.name] = jd_est

    if not estimates:
        return _err("no decodable dials at this D")

    values = sorted(estimates.values())
    median = values[len(values) // 2]
    spread = max(values) - min(values)
    return {
        "ok": True,
        "D": int(D),
        "reference_jd": float(reference_jd),
        "estimates": {k: float(v) for k, v in estimates.items()},
        "median_jd": float(median),
        "spread_days": float(spread),
    }


# ──────────────────────────────────────────────────────────────────────
# §5.3 — Calendar conversion (5 methods, phase 4)
# ──────────────────────────────────────────────────────────────────────

from antikythera_spectral import dates as _dates  # noqa: E402


def jd_to_gregorian(jd_tdb: float) -> Dict[str, Any]:
    """Proleptic Gregorian calendar date for a Julian Day."""
    err = _validate_jd(jd_tdb)
    if err:
        return err
    return {"ok": True, **_dates.jd_to_gregorian(float(jd_tdb))}


def gregorian_to_jd(year: int, month: int, day: int,
                    hour: int = 0, minute: int = 0, second: int = 0,
                    era: str = "CE") -> Dict[str, Any]:
    """Julian Day for a proleptic Gregorian date.

    Parameters
    ----------
    year, month, day : int
        Calendar fields. ``year`` is a positive ordinal; pre-1 CE dates
        use ``era='BCE'``.
    hour, minute, second : int, optional
        Time of day. Default midnight.
    era : str, optional
        ``'CE'`` (default) or ``'BCE'``.
    """
    if not isinstance(year, int) or not isinstance(month, int) or not isinstance(day, int):
        return _err("year, month, day must all be integers")
    if not (1 <= month <= 12):
        return _err(f"month must be in 1..12, got {month}")
    if not (1 <= day <= 31):
        return _err(f"day must be in 1..31, got {day}")
    if not (0 <= hour <= 23):
        return _err(f"hour must be in 0..23, got {hour}")
    if not (0 <= minute <= 59):
        return _err(f"minute must be in 0..59, got {minute}")
    if not (0 <= second <= 59):
        return _err(f"second must be in 0..59, got {second}")
    if era not in ("CE", "BCE"):
        return _err(f"era must be 'CE' or 'BCE', got {era!r}")
    try:
        jd = _dates.gregorian_to_jd(year, month, day, hour, minute, second, era)
    except (ValueError, OverflowError) as exc:
        return _err(str(exc))
    return {"ok": True, "jd_tdb": float(jd)}


def jd_to_julian_calendar(jd_tdb: float) -> Dict[str, Any]:
    """Julian-calendar (not proleptic Gregorian) date for a Julian Day.

    Used for historical research where the original record is in the
    Julian calendar (i.e. pre-1582-10-15).
    """
    err = _validate_jd(jd_tdb)
    if err:
        return err
    return {"ok": True, **_dates.jd_to_julian_calendar(float(jd_tdb))}


def jd_to_athenian(jd_tdb: float, *,
                    archon_table: str = "attic") -> Dict[str, Any]:
    """Approximate Attic-month + day for a Julian Day.

    See ``dates.jd_to_athenian`` for caveats (uniform-synodic-month
    model; archon name pending v0.2.0).
    """
    err = _validate_jd(jd_tdb)
    if err:
        return err
    out = _dates.jd_to_athenian(float(jd_tdb), archon_table=archon_table)
    if "ok" in out and not out["ok"]:
        return out  # forwarded error
    return {"ok": True, **out}


def jd_to_olympiad(jd_tdb: float) -> Dict[str, Any]:
    """Olympiad number + year-in-Olympiad for a Julian Day.

    The Antikythera back dial displays this; Olympiad I.1 = 776-07-01
    BCE (Olympic Games anchor).
    """
    err = _validate_jd(jd_tdb)
    if err:
        return err
    return {"ok": True, **_dates.jd_to_olympiad(float(jd_tdb))}


# ──────────────────────────────────────────────────────────────────────
# §5.4 — Astronomical observables (6 methods, phase 5)
# ──────────────────────────────────────────────────────────────────────

from antikythera_spectral import (  # noqa: E402
    eclipses as _eclipses,
    eclipses_algebraic as _eclipses_algebraic,
    eclipses_search as _eclipses_search,
    periods as _periods,
    visibility as _visibility,
    visibility_algebraic as _visibility_algebraic,
)


def _validate_planet(planet: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(planet, str):
        return _err(f"planet must be a string, got {type(planet).__name__}")
    if planet.lower() not in _visibility.SUPPORTED_PLANETS:
        return _err(
            f"unknown planet {planet!r}; "
            f"valid: {list(_visibility.SUPPORTED_PLANETS)}"
        )
    return None


def get_visibility_windows(jd_lo: float, jd_hi: float, planet: str,
                            *, precise: bool = False,
                            kernel: str = "de421") -> Dict[str, Any]:
    """Heliacal-visibility windows for a planet over a JD range.

    Default (``precise=False``): self-contained algebraic mode using
    per-planet anchors + synodic-cycle propagation. ±1-day Antikythera-
    grade precision, no skyfield required. Always returns ``ok=True``.

    With ``precise=True``: skyfield-backed sample-and-threshold scan
    against a JPL DE-kernel. Sub-arcsec precision; requires the
    ``[ephemeris]`` extras + the chosen kernel locally. Returns
    ``ok=False`` if the kernel isn't available.

    See ADR 0011 (algebraic-default-precise-opt-in).
    """
    err = _validate_jd(jd_lo) or _validate_jd(jd_hi) or _validate_planet(planet)
    if err:
        return err
    if jd_hi <= jd_lo:
        return _err("jd_hi must be greater than jd_lo")

    if not precise:
        # Algebraic / self-contained mode.
        windows = _visibility_algebraic.get_visibility_windows(
            jd_lo, jd_hi, planet,
        )
        return {
            "ok": True, "mode": "algebraic",
            "planet": planet.lower(),
            "n_windows": len(windows),
            "windows": [
                {"rise_jd": float(rise), "set_jd": float(set_),
                 "duration_days": float(set_ - rise)}
                for rise, set_ in windows
            ],
        }

    if kernel not in ("de421", "de422", "de440", "de441", "de441_part1", "de441_part2"):
        return _err(f"unsupported kernel {kernel!r}")
    windows = _visibility.get_visibility_windows(jd_lo, jd_hi, planet, kernel)
    if windows is None:
        return _err(
            f"ephemeris kernel {kernel!r} not available; "
            "install skyfield + run `antikythera-spectral kernel download "
            f"{kernel}` to enable."
        )
    return {
        "ok": True, "mode": "ephemeris",
        "planet": planet.lower(), "kernel": kernel,
        "n_windows": len(windows),
        "windows": [
            {"rise_jd": float(rise), "set_jd": float(set_),
             "duration_days": float(set_ - rise)}
            for rise, set_ in windows
        ],
    }


def get_next_heliacal_rising(jd_tdb: float, planet: str,
                              *, precise: bool = False,
                              kernel: str = "de421") -> Dict[str, Any]:
    """Next JD when `planet` emerges from solar glare after `jd_tdb`.

    Default (``precise=False``): closed-form ``anchor + n*synodic``
    propagation. Always succeeds.
    """
    err = _validate_jd(jd_tdb) or _validate_planet(planet)
    if err:
        return err

    if not precise:
        rise = _visibility_algebraic.get_next_heliacal_rising(jd_tdb, planet)
        return {
            "ok": True, "mode": "algebraic",
            "planet": planet.lower(),
            "jd_after": float(jd_tdb),
            "heliacal_rising_jd": float(rise),
            "delay_days": float(rise - jd_tdb),
        }

    rise = _visibility.get_next_heliacal_rising(jd_tdb, planet, kernel)
    if rise is None:
        return _err(
            "no heliacal rising found within search window or kernel unavailable"
        )
    return {
        "ok": True, "mode": "ephemeris",
        "planet": planet.lower(), "kernel": kernel,
        "jd_after": float(jd_tdb),
        "heliacal_rising_jd": float(rise),
        "delay_days": float(rise - jd_tdb),
    }


def get_solar_elongation(jd_tdb: float, planet: str,
                          *, precise: bool = False,
                          kernel: str = "de421") -> Dict[str, Any]:
    """Solar elongation (degrees) for `planet` at `jd_tdb`.

    Default (``precise=False``): sinusoidal phase model. ~±5° accurate.
    """
    err = _validate_jd(jd_tdb) or _validate_planet(planet)
    if err:
        return err

    if not precise:
        elong = _visibility_algebraic.get_solar_elongation_deg(jd_tdb, planet)
        return {
            "ok": True, "mode": "algebraic",
            "planet": planet.lower(),
            "jd_tdb": float(jd_tdb),
            "elongation_deg": float(elong),
        }

    elong = _visibility.get_solar_elongation_deg(jd_tdb, planet, kernel)
    if elong is None:
        return _err(f"kernel {kernel!r} not available")
    return {
        "ok": True, "mode": "ephemeris",
        "planet": planet.lower(), "kernel": kernel,
        "jd_tdb": float(jd_tdb),
        "elongation_deg": float(elong),
    }


def get_eclipse_anchors(era: str = "hellenistic") -> Dict[str, Any]:
    """Frozen Hellenistic / modern Saros anchor list with citations."""
    if era not in ("hellenistic", "modern", "all"):
        return _err(
            f"era must be one of 'hellenistic', 'modern', 'all'; got {era!r}"
        )
    if era == "hellenistic":
        anchors = list(_eclipses.HELLENISTIC_ANCHORS)
    elif era == "modern":
        anchors = list(_eclipses.MODERN_SAROS_ANCHORS)
    else:
        anchors = list(_eclipses.HELLENISTIC_ANCHORS) + list(_eclipses.MODERN_SAROS_ANCHORS)
    return {
        "ok": True,
        "era": era,
        "n_anchors": len(anchors),
        "anchors": [
            {
                "jd": float(a.jd),
                "date_iso": str(a.date_iso),
                "eclipse_type": str(a.eclipse_type),
                "almagest_ref": str(a.almagest_ref) if hasattr(a, "almagest_ref") else "",
                "espenak_id": str(a.espenak_id) if hasattr(a, "espenak_id") else "",
                "location": str(a.location) if hasattr(a, "location") else "",
                "interpretation_confidence": str(getattr(a, "interpretation_confidence", "")),
                "note": str(getattr(a, "note", "")),
            }
            for a in anchors
        ],
    }


def get_period_relations(source: str = "almagest") -> Dict[str, Any]:
    """Frozen MUL.APIN / Almagest period relations."""
    if source not in ("mulapin", "almagest", "all"):
        return _err(
            f"source must be one of 'mulapin', 'almagest', 'all'; got {source!r}"
        )
    relations = _periods.periods_by_source(source)
    return {
        "ok": True,
        "source": source,
        "n_relations": len(relations),
        "relations": [
            {
                "source": str(r.source),
                "phenomenon": str(r.phenomenon),
                "numerator": int(r.numerator),
                "denominator": int(r.denominator),
                "unit_num": str(r.unit_num) if hasattr(r, "unit_num") else "",
                "unit_den": str(r.unit_den) if hasattr(r, "unit_den") else "",
                "citation": str(r.citation),
                "interpretation_confidence": str(r.interpretation_confidence),
                "provenance_note": str(getattr(r, "provenance_note", "")),
            }
            for r in relations
        ],
    }


def find_eclipses(jd_lo: float, jd_hi: float, *,
                   kind: str = "all",
                   precise: bool = False,
                   kernel: str = "de421") -> Dict[str, Any]:
    """Enumerate eclipses in [jd_lo, jd_hi].

    Default (``precise=False``): Saros-cycle propagation from the
    frozen Hellenistic + modern anchor list. ±1-2 day accuracy across
    -1500 BCE .. +2100 CE.

    With ``precise=True``: sky-driven syzygy enumeration via skyfield
    against a JPL DE-kernel.
    """
    err = _validate_jd(jd_lo) or _validate_jd(jd_hi)
    if err:
        return err
    if jd_hi <= jd_lo:
        return _err("jd_hi must be greater than jd_lo")
    if kind not in ("lunar", "solar", "all"):
        return _err(f"kind must be one of 'lunar', 'solar', 'all'; got {kind!r}")

    if not precise:
        try:
            eclipses = _eclipses_algebraic.find_eclipses_in_range(
                jd_lo, jd_hi, kind=kind,
            )
        except (ValueError, RuntimeError) as exc:
            return _err(str(exc))
        return {
            "ok": True, "mode": "algebraic",
            "jd_lo": float(jd_lo), "jd_hi": float(jd_hi),
            "kind": kind,
            "n_eclipses": len(eclipses),
            "eclipses": eclipses,
        }

    eclipses = _eclipses_search.find_eclipses_in_range(jd_lo, jd_hi, kind, kernel)
    if eclipses is None:
        return _err(
            f"ephemeris kernel {kernel!r} not available, "
            "or sky_driven_validation does not expose find_syzygies."
        )
    return {
        "ok": True, "mode": "ephemeris",
        "jd_lo": float(jd_lo), "jd_hi": float(jd_hi),
        "kind": kind, "kernel": kernel,
        "n_eclipses": len(eclipses),
        "eclipses": eclipses,
    }


# ──────────────────────────────────────────────────────────────────────
# §5.5 — Operator workflow (6 methods, phase 6)
# ──────────────────────────────────────────────────────────────────────

from antikythera_spectral import operator as _operator  # noqa: E402


def start_operator_session(initial_jd: float, *,
                            D: int = D_CALLIPPIC,
                            dials: str = "all") -> Dict[str, Any]:
    err = _validate_jd(initial_jd) or _validate_dim(D)
    if err:
        return err
    return {
        "ok": True,
        "state": _operator.start_session(float(initial_jd), D=D, dials=dials),
    }


def operator_advance(state: Dict[str, Any], delta_days: float) -> Dict[str, Any]:
    if not isinstance(state, dict) or "schema_version" not in state:
        return _err("state must be an OperatorState dict")
    try:
        new_state = _operator.advance(state, float(delta_days))
    except (ValueError, TypeError) as exc:
        return _err(str(exc))
    return {"ok": True, "state": new_state}


def operator_observe(state: Dict[str, Any], dial: str,
                      observed_residue: int) -> Dict[str, Any]:
    if not isinstance(state, dict) or "schema_version" not in state:
        return _err("state must be an OperatorState dict")
    err = _validate_dial_name(dial)
    if err:
        return err
    if not isinstance(observed_residue, int):
        return _err(f"observed_residue must be int, got {type(observed_residue).__name__}")
    try:
        new_state = _operator.observe(state, dial, observed_residue)
    except (ValueError, TypeError) as exc:
        return _err(str(exc))
    return {"ok": True, "state": new_state}


def operator_diagnostics(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict) or "schema_version" not in state:
        return _err("state must be an OperatorState dict")
    return {"ok": True, **_operator.diagnostics(state)}


def set_anchor(dial: str, jd_tdb: float, observed_residue: int) -> Dict[str, Any]:
    """Bare CalibrationDelta for a dial — for callers using the pure-functional path."""
    err = _validate_jd(jd_tdb) or _validate_dial_name(dial)
    if err:
        return err
    if not isinstance(observed_residue, int):
        return _err(f"observed_residue must be int")
    return {
        "ok": True,
        "dial": dial,
        "jd": float(jd_tdb),
        "observed_residue": int(observed_residue),
    }


def apply_anchor(state: Dict[str, Any], calibration_delta: Dict[str, Any]) -> Dict[str, Any]:
    """Apply a CalibrationDelta to an OperatorState (pure-functional)."""
    if not isinstance(state, dict) or "schema_version" not in state:
        return _err("state must be an OperatorState dict")
    if not isinstance(calibration_delta, dict) or "dial" not in calibration_delta:
        return _err("calibration_delta must have at least 'dial'")
    return operator_observe(
        state,
        calibration_delta["dial"],
        int(calibration_delta.get("observed_residue", 0)),
    )


# ──────────────────────────────────────────────────────────────────────
# §5.6 — Cross-comparators (3 methods, phase 7)
# ──────────────────────────────────────────────────────────────────────

from antikythera_spectral import compare as _compare  # noqa: E402


def compare_ephemerides(jd_tdb: float, body: str,
                         kernel_a: str, kernel_b: str) -> Dict[str, Any]:
    err = _validate_jd(jd_tdb)
    if err:
        return err
    if body.lower() not in _compare._BODY_NAMES:
        return _err(f"unknown body {body!r}")
    allowed = ("de421", "de422", "de440", "de441", "de441_part1", "de441_part2")
    if kernel_a not in allowed or kernel_b not in allowed:
        return _err(f"kernels must be in {allowed}")
    delta = _compare.compare_ephemerides_at_jd(jd_tdb, body, kernel_a, kernel_b)
    if delta is None:
        return _err(
            f"could not load both kernels {kernel_a!r} and {kernel_b!r}; "
            "install skyfield + run kernel download"
        )
    return {
        "ok": True, "jd_tdb": float(jd_tdb), "body": body.lower(),
        "kernel_a": kernel_a, "kernel_b": kernel_b, **delta,
    }


def compare_models(jd_tdb: float, body: str,
                    model_a: str, model_b: str,
                    kernel: str = "de421") -> Dict[str, Any]:
    err = _validate_jd(jd_tdb)
    if err:
        return err
    out = _compare.compare_models_at_jd(jd_tdb, body, model_a, model_b, kernel)
    if out is None:
        return _err(
            "compare_models supports body='mars' only; "
            "models must be one of {'uniform','epicycle','equant'}; "
            "skyfield + kernel must be available."
        )
    return {"ok": True, **out}


def compare_reconstructions(jd_tdb: float, *,
                              dials: str = "all") -> Dict[str, Any]:
    err = _validate_jd(jd_tdb)
    if err:
        return err
    return {"ok": True, **_compare.compare_reconstructions_at_jd(jd_tdb, dials)}


# ──────────────────────────────────────────────────────────────────────
# §5.7 — What-if + archaeology (3 methods, phase 8)
# ──────────────────────────────────────────────────────────────────────

from antikythera_spectral import (  # noqa: E402
    archaeology as _archaeology,
    whatif as _whatif,
)


def encode_with_custom_train(jd_tdb: float, dial: str, p: int, q: int) -> Dict[str, Any]:
    err = _validate_jd(jd_tdb)
    if err:
        return err
    try:
        return {"ok": True, **_whatif.encode_with_custom_train(jd_tdb, dial, p, q)}
    except (ValueError, TypeError) as exc:
        return _err(str(exc))


def compare_to_ground_truth(jd_tdb: float, dial: str, p: int, q: int) -> Dict[str, Any]:
    err = _validate_jd(jd_tdb)
    if err:
        return err
    try:
        return {"ok": True, **_whatif.compare_to_ground_truth(jd_tdb, dial, p, q)}
    except (ValueError, TypeError) as exc:
        return _err(str(exc))


def get_fragment_inventory(fragment: str = "all") -> Dict[str, Any]:
    out = _archaeology.get_fragment_inventory(fragment)
    if "error" in out:
        return _err(out["error"])
    return {"ok": True, **out}


# ──────────────────────────────────────────────────────────────────────
# §5.8 — Babylonian Goal-Year overlay (2 methods, phase 9)
# ──────────────────────────────────────────────────────────────────────

from antikythera_spectral import goalyear as _goalyear  # noqa: E402


def goalyear_predict(planet: str, jd_tdb: float, *,
                      source: str = "mulapin") -> Dict[str, Any]:
    err = _validate_jd(jd_tdb)
    if err:
        return err
    try:
        return {"ok": True, **_goalyear.predict(planet, jd_tdb, source=source)}
    except (ValueError, TypeError) as exc:
        return _err(str(exc))


def goalyear_compare(planet: str, jd_tdb: float) -> Dict[str, Any]:
    err = _validate_jd(jd_tdb)
    if err:
        return err
    try:
        return {"ok": True, **_goalyear.compare(planet, jd_tdb)}
    except (ValueError, TypeError) as exc:
        return _err(str(exc))


# ──────────────────────────────────────────────────────────────────────
# §5.9 — Animation export (2 methods, phase 10)
# ──────────────────────────────────────────────────────────────────────

from antikythera_spectral import animation as _animation  # noqa: E402


def encode_range(jd_lo: float, jd_hi: float, *,
                  step_days: float = 1.0,
                  D: int = D_CALLIPPIC) -> Dict[str, Any]:
    err = _validate_jd(jd_lo) or _validate_jd(jd_hi) or _validate_dim(D)
    if err:
        return err
    if jd_hi <= jd_lo:
        return _err("jd_hi must be greater than jd_lo")
    if step_days <= 0:
        return _err("step_days must be > 0")
    try:
        return {"ok": True, **_animation.encode_range(jd_lo, jd_hi, step_days=step_days, D=D)}
    except ValueError as exc:
        return _err(str(exc))


def export_animation(jd_lo: float, jd_hi: float, step_days: float, *,
                      format: str = "json",
                      D: int = D_CALLIPPIC) -> Dict[str, Any]:
    err = _validate_jd(jd_lo) or _validate_jd(jd_hi) or _validate_dim(D)
    if err:
        return err
    if format not in ("json", "npz"):
        return _err(f"format must be 'json' or 'npz', got {format!r}")
    try:
        payload = _animation.export_animation(
            jd_lo, jd_hi, step_days, format=format, D=D,
        )
    except ValueError as exc:
        return _err(str(exc))
    return {
        "ok": True,
        "format": format,
        "n_bytes": len(payload),
        # Pyodide can transfer bytes directly; for JSON consumers, also
        # provide a base64 fallback for transport over text channels.
        "payload_b64": _b64(payload),
    }


def _b64(b: bytes) -> str:
    import base64
    return base64.b64encode(b).decode("ascii")


# ──────────────────────────────────────────────────────────────────────
# §5.10 — Hypothesis battery (2 methods, phase 11)
# ──────────────────────────────────────────────────────────────────────

from antikythera_spectral import hypotheses as _hypotheses  # noqa: E402


def run_hypothesis_battery(*, ephemeris: Optional[str] = None) -> Dict[str, Any]:
    """Run all 31 H-battery rows. Skyfield-gated rows skip if ephemeris=None."""
    rows: List[Dict[str, Any]] = []
    details: Dict[str, Any] = {}
    for hid in _hypotheses.ALL_HYPOTHESIS_IDS:
        fn_name = "hypothesis_" + hid.replace("-", "_")
        fn = getattr(_hypotheses, fn_name, None)
        if fn is None:
            rows.append({
                "id": hid, "status": "UNDETERMINED",
                "notes": f"evaluator {fn_name!r} not exposed",
            })
            continue
        try:
            row, detail = fn()
            rows.append(dict(row))
            details[hid] = detail
        except Exception as exc:  # noqa: BLE001
            rows.append({
                "id": hid, "status": "UNDETERMINED",
                "notes": f"evaluator raised {type(exc).__name__}: {exc!r}",
            })
    return {
        "ok": True,
        "n_rows": len(rows),
        "rows": rows,
        "details_keys": sorted(details.keys()),
    }


def get_hypothesis(id: str) -> Dict[str, Any]:
    if id not in _hypotheses.ALL_HYPOTHESIS_IDS:
        return _err(f"unknown hypothesis id {id!r}")
    fn = getattr(_hypotheses, "hypothesis_" + id.replace("-", "_"), None)
    if fn is None:
        return _err(f"evaluator for {id!r} not exposed")
    try:
        row, detail = fn()
    except Exception as exc:  # noqa: BLE001
        return _err(f"evaluator raised {type(exc).__name__}: {exc!r}")
    return {"ok": True, "row": dict(row), "detail": detail}


__all__ = [
    # §5.1 + §5.2 (phase 3)
    "decode_dial",
    "decode_to_jd",
    "get_all_dial_metadata",
    "get_dial_angle",
    "get_dial_state",
    "get_pointer_xy",
    "get_version",
    # §5.3 (phase 4)
    "jd_to_gregorian",
    "gregorian_to_jd",
    "jd_to_julian_calendar",
    "jd_to_athenian",
    "jd_to_olympiad",
    # §5.4 (phase 5)
    "get_visibility_windows",
    "get_next_heliacal_rising",
    "get_solar_elongation",
    "get_eclipse_anchors",
    "get_period_relations",
    "find_eclipses",
    # §5.5 (phase 6)
    "start_operator_session",
    "operator_advance",
    "operator_observe",
    "operator_diagnostics",
    "set_anchor",
    "apply_anchor",
    # §5.6 (phase 7)
    "compare_ephemerides",
    "compare_models",
    "compare_reconstructions",
    # §5.7 (phase 8)
    "encode_with_custom_train",
    "compare_to_ground_truth",
    "get_fragment_inventory",
    # §5.8 (phase 9)
    "goalyear_predict",
    "goalyear_compare",
    # §5.9 (phase 10)
    "encode_range",
    "export_animation",
    # §5.10 (phase 11)
    "run_hypothesis_battery",
    "get_hypothesis",
]
