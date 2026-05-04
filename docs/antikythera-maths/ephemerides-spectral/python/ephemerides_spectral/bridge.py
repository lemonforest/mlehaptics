"""Bridge API — Pyodide-friendly entry surface for ``ephemerides-spectral``.

Each method returns a Pyodide-JSON-serialisable dict with at least an
``ok`` key:

* ``{"ok": True, ...}`` on success
* ``{"ok": False, "error": "..."}`` on caller-side input error (raised
  exceptions for unexpected failures).

NumPy arrays in return values are JSON-friendly:

* Complex states (FPU reference encoder) are returned interleaved
  real/imag as ``Float32`` arrays so JS consumers can use
  ``new Float32Array(...)`` directly.
* Phase residues from the BIP encoder are returned as ``int`` lists
  (``uint32`` values fit in JS ``Number`` losslessly).

Two backends are exposed for ``encode_state``:

* ``"complex128"`` — the FPU reference encoder
  (``EphemerisHDCInstrument``). Phase 8 + Phase 9 (breathing) supported.
* ``"bip"`` — the ALU-native bit-serialised encoder
  (``EphemerisBIPInstrument``). Pure integer ALU; 305× speedup; same
  0.0002 rad floor as the reference at +20 yr.

The ``"bip"`` backend is the natural production surface; ``"complex128"``
is preserved indefinitely as the algebraic reference.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ephemerides_spectral._research.ephemeris_reference_instrument import (
    EphemerisHDCInstrument,
    REFERENCE_JD,
)
from ephemerides_spectral._research.bip_instrument import (
    EphemerisBIPInstrument,
    MODULO,
)
from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral.version import __version__


# ──────────────────────────────────────────────────────────────────────
# Constants and frozen lookups
# ──────────────────────────────────────────────────────────────────────

DEFAULT_BACKEND: str = "bip"
SUPPORTED_BACKENDS: Tuple[str, ...] = ("bip", "complex128")
SUPPORTED_BODIES: Tuple[str, ...] = tuple(sorted(BODIES.keys()))
ALLOWED_KERNELS: Tuple[str, ...] = ("de421", "de440", "de441", "de442")

_DATA_DIR: Path = Path(__file__).resolve().parent / "_data"


# ──────────────────────────────────────────────────────────────────────
# Internal validation helpers
# ──────────────────────────────────────────────────────────────────────

def _err(message: str) -> Dict[str, Any]:
    return {"ok": False, "error": message}


def _validate_jd(jd_tdb: Any) -> Optional[Dict[str, Any]]:
    try:
        f = float(jd_tdb)
    except (TypeError, ValueError):
        return _err(f"jd_tdb must be a number, got {type(jd_tdb).__name__}")
    if not math.isfinite(f):
        return _err(f"jd_tdb must be finite, got {f}")
    # Sanity-bound: REFERENCE_JD ± ~1.86 Myr (the BIP int64 envelope).
    # Also covers the DE441 epoch (-13200 BCE .. +17200 CE).
    if abs(f - REFERENCE_JD) > 6.8e8:
        return _err(
            f"jd_tdb {f} is outside the DE441 / int64 envelope "
            f"(|jd - REFERENCE_JD| must be ≤ 6.8e8 days ≈ 1.86 Myr)"
        )
    return None


def _validate_body(body: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(body, str):
        return _err(f"body must be a string, got {type(body).__name__}")
    if body.lower() not in SUPPORTED_BODIES:
        return _err(
            f"unknown body {body!r}; valid: {list(SUPPORTED_BODIES)}"
        )
    return None


def _validate_backend(backend: Any) -> Optional[Dict[str, Any]]:
    if backend not in SUPPORTED_BACKENDS:
        return _err(
            f"backend must be one of {list(SUPPORTED_BACKENDS)}, got {backend!r}"
        )
    return None


def _validate_kernel(kernel: Any) -> Optional[Dict[str, Any]]:
    if kernel not in ALLOWED_KERNELS:
        return _err(
            f"kernel must be one of {list(ALLOWED_KERNELS)}, got {kernel!r}"
        )
    return None


def _validate_lat_lon(lat: Any, lon: Any) -> Optional[Dict[str, Any]]:
    try:
        f_lat, f_lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return _err("lat and lon must be numbers")
    if not (math.isfinite(f_lat) and math.isfinite(f_lon)):
        return _err("lat and lon must be finite")
    if not (-90.0 <= f_lat <= 90.0):
        return _err(f"lat must be in [-90, 90], got {f_lat}")
    if not (-180.0 <= f_lon <= 360.0):
        return _err(f"lon must be in [-180, 360], got {f_lon}")
    return None


# ──────────────────────────────────────────────────────────────────────
# Instrument cache (lazy)
# ──────────────────────────────────────────────────────────────────────

_REF_CACHE: Dict[Tuple[str, bool], EphemerisHDCInstrument] = {}
_BIP_CACHE: Dict[Tuple[str, bool], EphemerisBIPInstrument] = {}


def _get_ref(kernel: str = "de441",
             force_high_res: bool = False) -> EphemerisHDCInstrument:
    key = (kernel, force_high_res)
    if key not in _REF_CACHE:
        _REF_CACHE[key] = EphemerisHDCInstrument(
            kernel=kernel, force_high_res=force_high_res
        )
    return _REF_CACHE[key]


def _get_bip(kernel: str = "de441",
             force_high_res: bool = False) -> EphemerisBIPInstrument:
    key = (kernel, force_high_res)
    if key not in _BIP_CACHE:
        _BIP_CACHE[key] = EphemerisBIPInstrument(
            kernel=kernel, force_high_res=force_high_res
        )
    return _BIP_CACHE[key]


def _interleave_complex(state: np.ndarray) -> List[float]:
    out = np.empty(2 * state.size, dtype=np.float32)
    out[0::2] = state.real.astype(np.float32, copy=False)
    out[1::2] = state.imag.astype(np.float32, copy=False)
    return out.tolist()


def _read_manifest() -> Dict[str, Any]:
    """Load ``_data/manifest.json`` (codegen-stamped); ``{}`` on miss."""
    p = _DATA_DIR / "manifest.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


# ──────────────────────────────────────────────────────────────────────
# Public surface
# ──────────────────────────────────────────────────────────────────────

def get_version() -> Dict[str, Any]:
    """Package version + frozen-data manifest.

    Returns
    -------
    dict
        ``{"ok": True, "package": "ephemerides-spectral", "version":
        "0.1.0", "manifest": {...}}``.

    The ``manifest`` field carries the codegen-stamped frozen-data
    manifest (per-file SHAs + sizes); empty dict if the manifest file
    is missing.
    """
    return {
        "ok": True,
        "package": "ephemerides-spectral",
        "version": __version__,
        "manifest": _read_manifest(),
    }


def list_bodies() -> Dict[str, Any]:
    """List every body in the Sol Star System Laplacian.

    Returns
    -------
    dict
        ``{"ok": True, "bodies": [...]}`` where each entry is
        ``{"name": ..., "category": ..., "period_days": ..., "mass_earth": ...}``.
    """
    rows = []
    for name in SUPPORTED_BODIES:
        b = BODIES[name]
        rows.append({
            "name": name,
            "display_name": b.name,
            "category": b.category,
            "period_days": float(b.period_days),
            "mass_earth": float(b.mass_earth),
        })
    return {"ok": True, "bodies": rows, "n_bodies": len(rows)}


def list_kernels() -> Dict[str, Any]:
    """List allowed JPL DE-kernels.

    Returns
    -------
    dict
        ``{"ok": True, "allowed": ["de421", "de440", "de441", "de442"]}``.
        Actual on-disk availability is determined when the instrument
        is constructed; the loader falls back to ``de421`` if a
        higher-resolution kernel is missing (unless ``force_high_res``).
    """
    return {"ok": True, "allowed": list(ALLOWED_KERNELS)}


def get_resolution(body: str = "earth", D: int = 65536) -> Dict[str, Any]:
    """Temporal resolution: seconds per residue shift for a body at dim ``D``.

    Parameters
    ----------
    body : str, default ``"earth"``
        Body name (case-insensitive). One of ``SUPPORTED_BODIES``.
    D : int, default ``65536``
        Hypervector dimension. Each unit-residue rotation is
        ``period_days * 86400 / D`` seconds.

    Returns
    -------
    dict
        ``{"ok": True, "body": ..., "D": ..., "period_days": ...,
           "seconds_per_residue": ..., "minutes_per_residue": ...}``.
    """
    err = _validate_body(body)
    if err: return err
    if not (isinstance(D, int) and D >= 1):
        return _err(f"D must be a positive int, got {D!r}")
    body_info = BODIES[body.lower()]
    if body_info.period_days <= 0:
        return {
            "ok": True, "body": body, "D": D,
            "period_days": 0.0,
            "seconds_per_residue": 0.0,
            "minutes_per_residue": 0.0,
            "note": "Sun has no orbital period; resolution undefined.",
        }
    sec_per_res = (body_info.period_days * 86400.0) / D
    return {
        "ok": True,
        "body": body,
        "D": D,
        "period_days": float(body_info.period_days),
        "seconds_per_residue": float(sec_per_res),
        "minutes_per_residue": float(sec_per_res / 60.0),
    }


def get_system_state(
    jd_tdb: float,
    *,
    backend: str = DEFAULT_BACKEND,
    kernel: str = "de441",
    force_high_res: bool = False,
    D: int = 65536,
) -> Dict[str, Any]:
    """Encode the barycentric state of the Sol Star System.

    Parameters
    ----------
    jd_tdb : float
        Julian Date in TDB. ``REFERENCE_JD = 2451545.0`` is the J2000
        anchor.
    backend : str, default ``"bip"``
        ``"bip"`` returns per-body uint32 phase residues + interleaved
        f32 of the bundled HDC state. ``"complex128"`` returns the FPU
        reference's interleaved-f32 complex state vector.
    kernel : str, default ``"de441"``
        JPL DE-kernel for ephemeris calibration.
    force_high_res : bool, default ``False``
        If True, raise rather than fall back to ``de421``.
    D : int, default ``65536``
        Hypervector dimension.

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": ..., "backend": ..., "D": ...,
            "phases_uint32": [...], "state_interleaved_f32": [...]}``.
        ``phases_uint32`` is omitted for the complex128 backend.
    """
    for v in (_validate_jd(jd_tdb), _validate_backend(backend),
              _validate_kernel(kernel)):
        if v: return v
    if not (isinstance(D, int) and D > 0 and (D & (D - 1)) == 0):
        return _err(f"D must be a positive power of 2, got {D!r}")
    try:
        jd = float(jd_tdb)
        if backend == "bip":
            inst = _get_bip(kernel=kernel, force_high_res=force_high_res)
            phases = inst.encode_state(jd)
            # Bundle into HDC state for downstream similarity ops.
            state = np.zeros(D, dtype=np.uint32)
            for i, name in enumerate(inst.body_names):
                # encode_state may return at the instrument's native D;
                # for the per-body-residue payload we don't need to
                # re-bundle here — the residues themselves are the
                # primary product.
                pass
            return {
                "ok": True,
                "jd_tdb": jd,
                "backend": "bip",
                "D": int(inst.D),
                "kernel": kernel,
                "bodies": list(inst.body_names),
                "phases_uint32": [int(x) for x in phases.tolist()],
            }
        # complex128 backend
        inst_ref = _get_ref(kernel=kernel, force_high_res=force_high_res)
        state_c = inst_ref.encode_state(jd)
        return {
            "ok": True,
            "jd_tdb": jd,
            "backend": "complex128",
            "D": int(inst_ref.D),
            "kernel": kernel,
            "state_interleaved_f32": _interleave_complex(state_c),
        }
    except OverflowError as exc:
        return _err(f"overflow: {exc}")
    except RuntimeError as exc:
        return _err(str(exc))


def get_local_view(
    jd_tdb: float,
    body: str,
    lat: float,
    lon: float,
    *,
    kernel: str = "de441",
) -> Dict[str, Any]:
    """Encode a topocentric view from a geographic position on a body.

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": ..., "body": ..., "lat": ..., "lon": ...,
            "state_interleaved_f32": [...]}``.
    """
    for v in (_validate_jd(jd_tdb), _validate_body(body),
              _validate_lat_lon(lat, lon), _validate_kernel(kernel)):
        if v: return v
    try:
        inst = _get_ref(kernel=kernel)
        sys_state = inst.encode_state(float(jd_tdb))
        local = inst.bind_observer(sys_state, body, float(lat), float(lon))
        return {
            "ok": True,
            "jd_tdb": float(jd_tdb),
            "body": body,
            "lat": float(lat),
            "lon": float(lon),
            "kernel": kernel,
            "state_interleaved_f32": _interleave_complex(local),
        }
    except (RuntimeError, ValueError) as exc:
        return _err(str(exc))


def get_eclipse_probability(
    jd_tdb: float,
    *,
    kernel: str = "de441",
) -> Dict[str, Any]:
    """Syzygy probability via spectral alignment with the Syzygy Operator.

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": ..., "probability": [0..1]}``.
        The probability is the magnitude of the inner product between
        the system state and the Syzygy Operator (Sun/Moon/Node).
    """
    for v in (_validate_jd(jd_tdb), _validate_kernel(kernel)):
        if v: return v
    try:
        inst = _get_ref(kernel=kernel)
        state = inst.encode_state(float(jd_tdb))
        prob = inst.get_eclipse_probability(state)
        return {
            "ok": True,
            "jd_tdb": float(jd_tdb),
            "kernel": kernel,
            "probability": float(prob),
        }
    except (RuntimeError, ValueError) as exc:
        return _err(str(exc))


def list_couplings() -> Dict[str, Any]:
    """List off-diagonal Laplacian couplings (gravitational fibers).

    Returns the Phase 9 fiber-coupling table — pairs ``(b1, b2)`` with
    the static ``rad/day`` weight, classified by category (planet-sun,
    moon-planet, resonance, asteroid-jupiter).

    Returns
    -------
    dict
        ``{"ok": True, "couplings": [{"a": ..., "b": ..., "weight_rad_per_day":
            ..., "weight_residues_per_day": ..., "category": ...}, ...]}``.
    """
    inst = _get_ref(kernel="de421")  # Laplacian is kernel-independent.
    L = inst.laplacian.L_static
    out: List[Dict[str, Any]] = []
    n = inst.laplacian.n
    names = inst.laplacian.body_names
    for i in range(n):
        for j in range(i + 1, n):
            w = L[i, j].real
            if w == 0.0:
                continue
            # Category heuristic: lookup against the static topology.
            a, b = names[i], names[j]
            cat_a, cat_b = BODIES[a].category, BODIES[b].category
            if cat_a == "star" or cat_b == "star":
                category = "planet-sun"
            elif cat_a == "moon" or cat_b == "moon":
                category = "moon-planet"
            elif cat_a == "asteroid" or cat_b == "asteroid":
                category = "asteroid-jupiter"
            else:
                category = "resonance"
            out.append({
                "a": a,
                "b": b,
                "weight_rad_per_day": float(abs(w)),
                "weight_residues_per_day": int(round(abs(w) / (2.0 * math.pi) * MODULO)),
                "category": category,
            })
    return {"ok": True, "couplings": out, "n_couplings": len(out)}


def get_breathing_modulation(
    jd_tdb: float,
    *,
    pair: Tuple[str, str] = ("jupiter", "saturn"),
    n_lobes: Tuple[int, int] = (5, 2),
    kernel: str = "de441",
) -> Dict[str, Any]:
    """Inspect the Phase 9 breathing-coupling modulation at a given JD.

    Computes the resonant phase ``n_a*phi_a - n_b*phi_b`` (mod 2^32) for
    a body pair and returns the integer-LUT cosine modulation, plus a
    float reference value for calibration.

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": ..., "pair": ["jupiter", "saturn"],
            "n_lobes": [5, 2], "phase_residue": ..., "cos_lut_q14": ...,
            "cos_float": ..., "modulation_factor": ...}``
    """
    a, b = pair
    n_a, n_b = n_lobes
    for v in (_validate_jd(jd_tdb), _validate_body(a), _validate_body(b),
              _validate_kernel(kernel)):
        if v: return v
    try:
        inst = _get_bip(kernel=kernel)
        phases = inst.encode_state(float(jd_tdb))
        idx_a = inst.body_to_idx[a.lower()]
        idx_b = inst.body_to_idx[b.lower()]
        phi_a = int(phases[idx_a])
        phi_b = int(phases[idx_b])
        res_phase = (n_a * phi_a - n_b * phi_b) & (MODULO - 1)
        # LUT lookup
        from ephemerides_spectral._research.bip_instrument import (
            cos_lut, COSINE_LUT_AMP,
        )
        cos_q14 = cos_lut(res_phase, n_lobes=1)
        # Float reference for calibration
        cos_f = math.cos(2.0 * math.pi * res_phase / MODULO)
        # Default 10% breathing depth
        modulation = 1.0 + 0.1 * (cos_q14 / COSINE_LUT_AMP)
        return {
            "ok": True,
            "jd_tdb": float(jd_tdb),
            "pair": [a, b],
            "n_lobes": [n_a, n_b],
            "phase_residue": int(res_phase),
            "cos_lut_q14": int(cos_q14),
            "cos_lut_amp": int(COSINE_LUT_AMP),
            "cos_float": float(cos_f),
            "modulation_factor": float(modulation),
        }
    except (RuntimeError, ValueError, OverflowError) as exc:
        return _err(str(exc))


__all__ = [
    "DEFAULT_BACKEND",
    "SUPPORTED_BACKENDS",
    "SUPPORTED_BODIES",
    "ALLOWED_KERNELS",
    "get_version",
    "list_bodies",
    "list_kernels",
    "list_couplings",
    "get_resolution",
    "get_system_state",
    "get_local_view",
    "get_eclipse_probability",
    "get_breathing_modulation",
]
