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


__all__ = [
    "decode_dial",
    "decode_to_jd",
    "get_all_dial_metadata",
    "get_dial_angle",
    "get_dial_state",
    "get_pointer_xy",
    "get_version",
]
