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
from ephemerides_spectral._research.laplacian import RESONANCES
from ephemerides_spectral._research.time_scales import (
    DEFAULT_LEAP_SECONDS,
    URANIAN_SEASONS,
    URANUS_AXIAL_TILT_DEG,
    URANUS_ORBITAL_PERIOD_YEARS,
    URANUS_SIDEREAL_DAY_HOURS,
    SUT_EPOCH_JD_TDB,
    jd_to_lunar,
    jd_to_msd,
    jd_to_uranian_time,
    msd_to_jd,
    uranian_time_to_jd,
)
from ephemerides_spectral._research.syzygy_window import (
    find_syzygies as _find_syzygies_impl,
)
from ephemerides_spectral._research import diagnosed_fibers as _patches
from ephemerides_spectral.version import __version__


# ──────────────────────────────────────────────────────────────────────
# Constants and frozen lookups
# ──────────────────────────────────────────────────────────────────────

DEFAULT_BACKEND: str = "bip"

#: Encoder backends recognised by the bridge / CLI.
#:
#: * ``"bip"`` (default) — pure-Python BIP encoder. Always available;
#:   guaranteed correct.
#: * ``"complex128"`` — FPU complex128 reference encoder. Always
#:   available; used for the algebraic identities (Syzygy operator,
#:   observer binding) and as a regression baseline.
#: * ``"c"`` — native BIP encoder via the bundled `_native/` shared
#:   library (v0.3.1+). Requires the C path to have loaded
#:   successfully — see ``ephemerides_spectral._native_bip.HAS_NATIVE``.
#:   Byte-for-byte identical phases to ``"bip"``, faster on the
#:   hot loop. Falls back to ``"bip"`` if the binary is missing
#:   (sdist installs without a C toolchain, Pyodide / WASM, etc.).
SUPPORTED_BACKENDS: Tuple[str, ...] = ("bip", "complex128", "c")
SUPPORTED_BODIES: Tuple[str, ...] = tuple(sorted(BODIES.keys()))

#: JPL DE-series planetary kernels recognised by the loader.
ALLOWED_KERNELS: Tuple[str, ...] = ("de421", "de440", "de441", "de442")

#: Lunar-time kernels recognised in metadata. v0.3.0 lists LTE440
#: (Lin et al. 2025; SPICE-format Lunar Time Ephemeris on DE440)
#: but does not auto-load it — the .bsp file must be staged
#: separately by the user (see github.com/xlucn/LTE440 releases).
#: When NASA + international agencies finalise LTC (Lunar
#: Coordinated Time), this list and bridge.list_lunar_kernels
#: become the surface for runtime LTC resolution.
LUNAR_KERNELS: Tuple[str, ...] = ("lte440",)

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
    """List recognised JPL DE-kernels (planetary) and lunar-time kernels.

    Returns
    -------
    dict
        ``{"ok": True, "planetary": ["de421", "de440", "de441",
        "de442"], "lunar_time": ["lte440"]}``. Actual on-disk
        availability is determined when the instrument is
        constructed; the loader falls back to ``de421`` if a
        higher-resolution planetary kernel is missing (unless
        ``force_high_res``). Lunar-time kernels are listed for
        metadata purposes only — see :func:`list_lunar_kernels`.
    """
    return {
        "ok": True,
        "planetary": list(ALLOWED_KERNELS),
        "lunar_time": list(LUNAR_KERNELS),
        # Backwards-compat: v0.1.0–v0.2.0 callers expect ``allowed``.
        "allowed": list(ALLOWED_KERNELS),
    }


def list_lunar_kernels() -> Dict[str, Any]:
    """Lunar-time / lunar-orientation kernel metadata.

    v0.3.0 ships *awareness* of LTE440 (Lin et al. 2025, A&A 704
    A76) — the SPICE-format lunar time ephemeris on DE440 that
    provides TCL ↔ TCB ↔ TDB conversions with 0.15 ns accuracy
    through 2050. The kernel must be staged separately
    (``github.com/xlucn/LTE440`` releases); ephemerides-spectral
    does not auto-download.

    When NASA + international space agencies finalise LTC (Lunar
    Coordinated Time, target ~2026–2028 per the April 2024
    White House directive), this method becomes the runtime
    surface for LTC ↔ UTC ↔ JD_TDB conversions.

    Returns
    -------
    dict
        ``{"ok": True, "kernels": [{"name": ..., "purpose": ...,
        "source": ..., "size_mb": ..., "accuracy": ...}], "ltc_status": ...}``.
    """
    kernels = [
        {
            "name": "lte440",
            "purpose": "Lunar Time Ephemeris on DE440; TCL ↔ TCB ↔ TDB",
            "source": "https://github.com/xlucn/LTE440",
            "publication": "Lin et al. (2025), A&A 704, A76",
            "size_mb": 100,
            "accuracy_ns": 0.15,
            "validity_through": "2050",
        },
    ]
    return {
        "ok": True,
        "kernels": kernels,
        "ltc_status": (
            "LTC (Lunar Coordinated Time) formal definition pending "
            "(NASA + international agencies, target ~2026–2028 per "
            "April 2024 White House directive). LTE440 is the "
            "underlying ephemeris when LTC arrives."
        ),
    }


def jd_to_mars_time(jd_utc: float,
                    leap_seconds: int = DEFAULT_LEAP_SECONDS) -> Dict[str, Any]:
    """Convert UTC Julian Date → Mars Sol Date + Mars Coordinated Time.

    Implements Allison & McEwen 2000:

        MSD = (JD_UTC + (TAI - UTC)/86400 - 2405522.0025054) / 1.0274912517

    Parameters
    ----------
    jd_utc : float
        Julian Date in UTC.
    leap_seconds : int, default 37
        TAI − UTC offset in seconds. Authoritative source: IERS
        Bulletin C. The Jan 2017 value (37) is unchanged through
        2026.

    Returns
    -------
    dict
        ``{"ok": True, "jd_utc": ..., "msd": ..., "mtc_hours": ...,
        "mtc_seconds": ..., "sol_number": ..., "leap_seconds": ...}``
    """
    err = _validate_jd(jd_utc)
    if err is not None:
        # _validate_jd uses jd_tdb in its message but the envelope
        # is the same.
        return {**err, "error": err["error"].replace("jd_tdb", "jd_utc")}
    if not isinstance(leap_seconds, int):
        return _err(f"leap_seconds must be an int, got {type(leap_seconds).__name__}")
    mars = jd_to_msd(float(jd_utc), leap_seconds=leap_seconds)
    return {
        "ok": True,
        "leap_seconds": int(leap_seconds),
        **mars.to_dict(),
    }


def mars_time_to_jd(msd: float,
                    leap_seconds: int = DEFAULT_LEAP_SECONDS) -> Dict[str, Any]:
    """Inverse of :func:`jd_to_mars_time` — MSD → JD_UTC."""
    try:
        f = float(msd)
    except (TypeError, ValueError):
        return _err(f"msd must be a number, got {type(msd).__name__}")
    if not math.isfinite(f):
        return _err(f"msd must be finite, got {f}")
    if not isinstance(leap_seconds, int):
        return _err(f"leap_seconds must be an int, got {type(leap_seconds).__name__}")
    jd_utc = msd_to_jd(f, leap_seconds=leap_seconds)
    return {
        "ok": True,
        "msd": f,
        "jd_utc": float(jd_utc),
        "leap_seconds": int(leap_seconds),
    }


def jd_to_sol_uranian_time(jd_tdb: float) -> Dict[str, Any]:
    """Convert JD (TDB) → Sol Uranian Time (USD + SUT) + orbital season state.

    The third planetary time system in the package alongside Mars Sol Date
    (Allison & McEwen 2000) and lunar synodic / sidereal phase. Uranus's
    "natural harmonic" pairs three independent cycles:

    1. **Uranian Sol Date (USD)** — count of mean Uranian sidereal days
       since the SUT epoch (2007-12-16 northern equinox). One Uranian
       sidereal day = 17.24 h (retrograde rotation; we carry magnitude
       + a ``retrograde=True`` flag).
    2. **Sol Uranian Time (SUT)** — fractional part of USD expressed as
       hours [0, 24) at Uranus's prime meridian. One Uranian hour
       = 17.24 / 24 ≈ 43.1 Earth-minutes.
    3. **Orbital phase + season** — Uranus's 84.02-yr orbit partitioned
       into 4 equal seasons (~21 yr each). Anchored at the 2007 northern
       equinox; named per the configuration the *northern* hemisphere
       experiences.

    Parameters
    ----------
    jd_tdb : float
        Julian Date in TDB. Use ``REFERENCE_JD = 2451545.0`` for J2000.

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": ..., "usd": ..., "sut_hours": ...,
        "sut_seconds": ..., "orbital_phase": ..., "season": ...,
        "years_since_epoch": ..., "retrograde": True,
        "epoch": {"description": "Uranus 2007 northern equinox",
                  "jd_tdb": 2454451.0, "axial_tilt_deg": 97.77}}``.
    """
    err = _validate_jd(jd_tdb)
    if err is not None:
        return err
    sut = jd_to_uranian_time(float(jd_tdb))
    return {
        "ok": True,
        **sut.to_dict(),
        "epoch": {
            "description": "Uranus 2007 northern equinox",
            "jd_tdb": float(SUT_EPOCH_JD_TDB),
            "sidereal_day_hours": float(URANUS_SIDEREAL_DAY_HOURS),
            "orbital_period_years": float(URANUS_ORBITAL_PERIOD_YEARS),
            "axial_tilt_deg": float(URANUS_AXIAL_TILT_DEG),
            "season_names": list(URANIAN_SEASONS),
        },
    }


def sol_uranian_time_to_jd(usd: float) -> Dict[str, Any]:
    """Inverse of :func:`jd_to_sol_uranian_time` for the ``usd`` field.

    Returns ``JD_TDB``. The orbital-season layer is uniquely determined
    by ``usd × URANUS_SIDEREAL_DAY_DAYS / URANUS_ORBITAL_PERIOD_DAYS``
    given the SUT epoch — no information loss.
    """
    try:
        f = float(usd)
    except (TypeError, ValueError):
        return _err(f"usd must be a number, got {type(usd).__name__}")
    if not math.isfinite(f):
        return _err(f"usd must be finite, got {f}")
    return {
        "ok": True,
        "usd": f,
        "jd_tdb": float(uranian_time_to_jd(f)),
    }


def get_natural_resonance_group() -> Dict[str, Any]:
    """The natural cyclic group derived from the Phase 9 RESONANCES table.

    This is the *resonance-derived* gear group — the cyclic structure the
    bodies actually live in by virtue of their integer mean-motion ratios,
    as distinct from the architectural ``Z_{2^32}`` modulus the encoder
    imposes for `uint32`-overflow convenience. See research notebook §6
    for the full discussion.

    For each resonance pair `(n_a, m_b)`, the per-pair natural cycle is
    `lcm(n_a, m_b)`. The aggregate natural modulus is the LCM across all
    pair-LCMs. By the Chinese Remainder Theorem, the aggregate modulus
    factors into a product of prime cyclic groups.

    Returns
    -------
    dict
        ``{"ok": True, "resonances": [{"a", "b", "n_a", "m_b", "pair_lcm"}],
        "natural_modulus": int, "prime_factors": [int],
        "interpretation": str}``.
    """
    from math import gcd

    def _lcm(a: int, b: int) -> int:
        return a * b // gcd(a, b)

    def _prime_factors(n: int) -> List[int]:
        factors: List[int] = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                if not factors or factors[-1] != d:
                    factors.append(d)
                n //= d
            d += 1
        if n > 1:
            factors.append(n)
        return factors

    rows: List[Dict[str, Any]] = []
    aggregate = 1
    for r in RESONANCES:
        pair_lcm = _lcm(int(r.n_a), int(r.m_b))
        rows.append({
            "a": r.body_a,
            "b": r.body_b,
            "n_a": int(r.n_a),
            "m_b": int(r.m_b),
            "pair_lcm": pair_lcm,
            "label": r.label,
        })
        aggregate = _lcm(aggregate, pair_lcm)

    factors = _prime_factors(aggregate)
    return {
        "ok": True,
        "resonances": rows,
        "natural_modulus": int(aggregate),
        "prime_factors": factors,
        "interpretation": (
            f"{aggregate}-tooth natural gear; CRT-isomorphic to "
            + " x ".join(f"Z_{p}" for p in factors)
            + ". This is the resonance-derived cyclic structure; the "
            "encoder's architectural modulus is Z_{2^32}. See "
            "research notebook §6 for the distinction."
        ),
        "encoder_modulus": MODULO,
        "natural_divides_encoder": MODULO % aggregate == 0,
        "gcd_natural_encoder": gcd(aggregate, MODULO),
    }


def find_syzygies(jd_lo: float,
                  jd_hi: float,
                  *,
                  kind: str = "all",
                  threshold: float = 0.05,
                  max_candidates: int = 1000,
                  backend: str = "auto") -> Dict[str, Any]:
    """Spectral-native syzygy window search (v0.3.1+).

    Replaces the v0.3.0 point-evaluation pattern (encode-then-check
    at a single JD via ``get_eclipse_probability``). Enumerates
    candidate syzygies in [jd_lo, jd_hi] (TDB) by walking new-moon
    and full-moon multiples of the synodic month and confirming
    against the draconic-month phase. Closed-form, no per-JD
    encoding — cost is `O(n_syzygies)` instead of `O(window_days)`.

    Parameters
    ----------
    jd_lo, jd_hi : float
        Window boundaries in JD (TDB).
    kind : {"solar", "lunar", "all"}, default "all"
        ``"solar"`` filters to new-moon syzygies; ``"lunar"`` to
        full-moon; ``"all"`` returns both kinds.
    threshold : float, default 0.05
        Score cutoff (root-sum-square of synodic + draconic phase
        residuals). 0.05 catches total-class eclipses; 0.1 catches
        partials too.
    max_candidates : int, default 1000
        Safety cap for very-loose thresholds + multi-millennium windows.

    Returns
    -------
    dict
        ``{"ok": True, "n_candidates": int, "candidates":
        [{"jd_tdb", "kind", "synodic_phase_resid",
        "draconic_phase_resid", "score"}, ...]}``.
        Candidates are ordered by JD ascending; lower score = stronger
        syzygy alignment. For arc-second-class precision (which
        eclipse, total vs partial, location of totality) confirm each
        candidate against a JPL ephemeris via skyfield.
    """
    for v in (_validate_jd(jd_lo), _validate_jd(jd_hi),
              _validate_backend(backend)):
        if v is not None:
            return v
    if kind not in ("solar", "lunar", "all"):
        return _err(f"kind must be 'solar' / 'lunar' / 'all', got {kind!r}")
    try:
        f_threshold = float(threshold)
    except (TypeError, ValueError):
        return _err(f"threshold must be a number, got {type(threshold).__name__}")
    if not (0.0 < f_threshold <= 0.5):
        return _err(f"threshold must be in (0, 0.5], got {f_threshold}")
    from ephemerides_spectral import _native_bip
    if backend == "auto":
        backend = "c" if _native_bip.HAS_NATIVE else "bip"
    try:
        if backend == "c" and _native_bip.HAS_NATIVE:
            kind_filter = {
                "solar": _native_bip.ES_SYZYGY_KIND_FILTER_SOLAR,
                "lunar": _native_bip.ES_SYZYGY_KIND_FILTER_LUNAR,
                "all":   _native_bip.ES_SYZYGY_KIND_FILTER_ALL,
            }[kind]
            cand_dicts = _native_bip.native_find_syzygies(
                float(jd_lo), float(jd_hi),
                kind=kind_filter, threshold=f_threshold,
                max_candidates=int(max_candidates),
                out_capacity=int(max_candidates),
            )
            backend_str = "c"
        else:
            candidates = _find_syzygies_impl(
                float(jd_lo), float(jd_hi),
                kind=kind, threshold=f_threshold,
                max_candidates=int(max_candidates),
            )
            cand_dicts = [c.to_dict() for c in candidates]
            backend_str = "bip"
    except (ValueError, RuntimeError) as exc:
        return _err(str(exc))
    return {
        "ok": True,
        "jd_lo": float(jd_lo),
        "jd_hi": float(jd_hi),
        "kind": kind,
        "threshold": f_threshold,
        "n_candidates": len(cand_dicts),
        "candidates": cand_dicts,
        "backend": backend_str,
    }


def get_lunar_phase(jd_tdb: float) -> Dict[str, Any]:
    """Mean synodic + sidereal lunar age/phase at a JD (TDB).

    These are the bronze-dial primitives — fixed-period
    approximations sufficient for HDC encoding and Saros-class
    navigation. For arc-second-class precision use the JPL
    ephemeris path (``get_system_state`` → moon residue) which
    has the perturbation series baked in.

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": ..., "synodic_age_days": ...,
        "synodic_phase": ..., "sidereal_age_days": ...,
        "sidereal_phase": ...}``
    """
    err = _validate_jd(jd_tdb)
    if err is not None:
        return err
    lunar = jd_to_lunar(float(jd_tdb))
    return {
        "ok": True,
        **lunar.to_dict(),
    }


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
        if backend == "bip" or backend == "c":
            inst = _get_bip(kernel=kernel, force_high_res=force_high_res)
            backend_used = "bip"
            phases = None

            if backend == "c":
                # v0.4.1: native path supports the diagnosed-fiber
                # overlay. The Python registry is mirrored into the
                # C-side registry on every apply_patch / clear_patches
                # call (see _mirror_patch_to_native), so the C encode
                # produces byte-identical phases to the Python BIP
                # encoder regardless of patches. Falls through to
                # pure-Python only when the native binary isn't
                # present (sdist install without toolchain, Pyodide).
                from ephemerides_spectral import _native_bip
                if _native_bip.HAS_NATIVE:
                    try:
                        phases = _native_bip.encode_state(jd - REFERENCE_JD)
                        backend_used = "c"
                    except OverflowError as native_exc:
                        return _err(f"overflow (native): {native_exc}")
                # Else: HAS_NATIVE is False — fall through to BIP.

            if phases is None:
                phases = inst.encode_state(jd)

            return {
                "ok": True,
                "jd_tdb": jd,
                "backend": backend_used,
                "backend_requested": backend,
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
    backend: str = "auto",
    D: int = 4096,
) -> Dict[str, Any]:
    """Encode a topocentric view from a geographic position on a body.

    Parameters
    ----------
    backend : {"auto", "bip", "c", "fpu-ref"}, default "auto"
        ``"bip"`` runs the Python BIP-and-lift HD pipeline (v0.7.0+):
            BIP integer encode → splitmix64 channel bases → roll + sum.
        ``"c"`` calls the matching native pipeline. Byte-identical to
            ``"bip"`` within float-ULP.
        ``"fpu-ref"`` runs the original FPU complex128 matrix-expm
            propagation path (`EphemerisHDCInstrument.encode_state`).
            Different bytes from ``"bip"`` / ``"c"`` (different
            propagation algorithm); kept for backwards compatibility.
        ``"auto"`` picks ``"c"`` when the native binary is loaded,
            otherwise falls back to ``"bip"``.
    D : int, default 4096
        HD vector dimension. Only used for ``backend in {"auto","bip","c"}``;
        the FPU-ref path uses the instrument's configured D.
    """
    for v in (_validate_jd(jd_tdb), _validate_body(body),
              _validate_lat_lon(lat, lon), _validate_kernel(kernel),
              _validate_backend(backend)):
        if v: return v
    from ephemerides_spectral import _native_bip
    chosen = backend
    if chosen == "auto":
        chosen = "c" if _native_bip.HAS_NATIVE else "bip"
    if chosen not in {"bip", "c", "fpu-ref"}:
        return _err(
            f"backend must be 'auto'/'bip'/'c'/'fpu-ref', got {backend!r}"
        )
    try:
        if chosen == "fpu-ref":
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
                "backend": "fpu-ref",
                "D": int(inst.D),
                "state_interleaved_f32": _interleave_complex(local),
            }
        # BIP-and-lift path (Python or C).
        inst_bip = _get_bip(kernel=kernel)
        body_idx = inst_bip.body_to_idx[body.lower()]
        if chosen == "c" and _native_bip.HAS_NATIVE:
            from ephemerides_spectral._research.bip_instrument import REFERENCE_JD
            sys_hd = _native_bip.native_encode_state_hd(
                float(jd_tdb) - REFERENCE_JD, int(D),
            )
            local = _native_bip.native_bind_observer(
                sys_hd, int(body_idx), float(lat), float(lon),
            )
            backend_str = "c"
        else:
            from ephemerides_spectral._research.bip_hd_lift import (
                encode_state_hd as _py_encode_state_hd,
                bind_observer as _py_bind_observer,
            )
            phases = inst_bip.encode_state(float(jd_tdb))
            sys_hd = _py_encode_state_hd(phases, int(D))
            local = _py_bind_observer(sys_hd, int(body_idx),
                                      float(lat), float(lon), int(D))
            backend_str = "bip"
        return {
            "ok": True,
            "jd_tdb": float(jd_tdb),
            "body": body,
            "lat": float(lat),
            "lon": float(lon),
            "kernel": kernel,
            "backend": backend_str,
            "D": int(D),
            "state_interleaved_f32": _interleave_complex(local),
        }
    except (RuntimeError, ValueError) as exc:
        return _err(str(exc))


def get_eclipse_probability(
    jd_tdb: float,
    *,
    kernel: str = "de441",
    backend: str = "auto",
    D: int = 4096,
) -> Dict[str, Any]:
    """Syzygy probability via spectral alignment with the Syzygy Operator.

    Parameters
    ----------
    backend : {"auto", "bip", "c", "fpu-ref"}, default "auto"
        Same semantics as `get_local_view`.
    D : int, default 4096
        HD vector dimension for the BIP-and-lift backends.

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": ..., "probability": [0..1], "backend": ...}``.
    """
    for v in (_validate_jd(jd_tdb), _validate_kernel(kernel),
              _validate_backend(backend)):
        if v: return v
    from ephemerides_spectral import _native_bip
    chosen = backend
    if chosen == "auto":
        chosen = "c" if _native_bip.HAS_NATIVE else "bip"
    if chosen not in {"bip", "c", "fpu-ref"}:
        return _err(
            f"backend must be 'auto'/'bip'/'c'/'fpu-ref', got {backend!r}"
        )
    try:
        if chosen == "fpu-ref":
            inst = _get_ref(kernel=kernel)
            state = inst.encode_state(float(jd_tdb))
            prob = inst.get_eclipse_probability(state)
            return {
                "ok": True,
                "jd_tdb": float(jd_tdb),
                "kernel": kernel,
                "backend": "fpu-ref",
                "probability": float(prob),
            }
        # BIP-and-lift path.
        inst_bip = _get_bip(kernel=kernel)
        sun_idx = inst_bip.body_to_idx["sun"]
        moon_idx = inst_bip.body_to_idx["moon"]
        if chosen == "c" and _native_bip.HAS_NATIVE:
            from ephemerides_spectral._research.bip_instrument import REFERENCE_JD
            sys_hd = _native_bip.native_encode_state_hd(
                float(jd_tdb) - REFERENCE_JD, int(D),
            )
            prob = _native_bip.native_get_eclipse_probability(
                sys_hd, int(sun_idx), int(moon_idx),
            )
            backend_str = "c"
        else:
            from ephemerides_spectral._research.bip_hd_lift import (
                encode_state_hd as _py_encode_state_hd,
                eclipse_probability as _py_eclipse_probability,
            )
            phases = inst_bip.encode_state(float(jd_tdb))
            sys_hd = _py_encode_state_hd(phases, int(D))
            prob = _py_eclipse_probability(sys_hd, int(D),
                                           int(sun_idx), int(moon_idx))
            backend_str = "bip"
        return {
            "ok": True,
            "jd_tdb": float(jd_tdb),
            "kernel": kernel,
            "backend": backend_str,
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
    backend: str = "auto",
) -> Dict[str, Any]:
    """Inspect the Phase 9 breathing-coupling modulation at a given JD.

    Computes the resonant phase ``n_a*phi_a - n_b*phi_b`` (mod 2^32) for
    a body pair and returns the integer-LUT cosine modulation, plus a
    float reference value for calibration.

    Parameters
    ----------
    backend : {"auto", "bip", "c"}, default "auto"
        ``"bip"`` runs the pure-Python integer encoder + LUT lookup.
        ``"c"`` calls ``es_breathing_modulation`` in the native binary.
        ``"auto"`` picks ``"c"`` when the native binary is loaded,
        otherwise falls back to ``"bip"``.

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": ..., "pair": ["jupiter", "saturn"],
            "n_lobes": [5, 2], "phase_residue": ..., "cos_lut_q14": ...,
            "cos_float": ..., "modulation_factor": ...,
            "backend": "bip" | "c"}``
    """
    a, b = pair
    n_a, n_b = n_lobes
    for v in (_validate_jd(jd_tdb), _validate_body(a), _validate_body(b),
              _validate_kernel(kernel), _validate_backend(backend)):
        if v: return v
    from ephemerides_spectral import _native_bip
    if backend == "auto":
        backend = "c" if _native_bip.HAS_NATIVE else "bip"
    try:
        inst = _get_bip(kernel=kernel)
        idx_a = inst.body_to_idx[a.lower()]
        idx_b = inst.body_to_idx[b.lower()]
        if backend == "c" and _native_bip.HAS_NATIVE:
            from ephemerides_spectral._research.bip_instrument import (
                COSINE_LUT_AMP, REFERENCE_JD,
            )
            phase_residue, cos_q14, modulation = (
                _native_bip.native_breathing_modulation(
                    float(jd_tdb) - REFERENCE_JD,
                    int(idx_a), int(idx_b),
                    int(n_a), int(n_b),
                )
            )
            backend_str = "c"
        else:
            phases = inst.encode_state(float(jd_tdb))
            phi_a = int(phases[idx_a])
            phi_b = int(phases[idx_b])
            phase_residue = (n_a * phi_a - n_b * phi_b) & (MODULO - 1)
            from ephemerides_spectral._research.bip_instrument import (
                cos_lut, COSINE_LUT_AMP,
            )
            cos_q14 = cos_lut(phase_residue, n_lobes=1)
            modulation = 1.0 + 0.1 * (cos_q14 / COSINE_LUT_AMP)
            backend_str = "bip"
        cos_f = math.cos(2.0 * math.pi * phase_residue / MODULO)
        return {
            "ok": True,
            "jd_tdb": float(jd_tdb),
            "pair": [a, b],
            "n_lobes": [n_a, n_b],
            "phase_residue": int(phase_residue),
            "cos_lut_q14": int(cos_q14),
            "cos_lut_amp": int(COSINE_LUT_AMP),
            "cos_float": float(cos_f),
            "modulation_factor": float(modulation),
            "backend": backend_str,
        }
    except (RuntimeError, ValueError, OverflowError) as exc:
        return _err(str(exc))


# ──────────────────────────────────────────────────────────────────────
# v0.4.0 — runtime kernel patching surface (v0.4.1: C-side overlay)
# ──────────────────────────────────────────────────────────────────────
#
# Diagnosed-fiber patches let callers OVERLAY corrections onto the
# spectral kernel at encode time without mutating the published
# kernel bytes. Patches are authored from FFT residual peaks (see
# v0.3.1's ``de441_error_spectrum``); the bundled CATALOG carries
# three patches derived from that analysis.
#
# Discipline:
#   * Patches are data, not code edits — versionable + shareable.
#   * Multiple patches stack; sinusoidal kinds compose order-independently.
#   * v0.4.1: ``backend="c"`` natively supports the overlay (ABI v2).
#     The Python registry and the C-side registry are kept in sync —
#     every ``apply_patch`` mirrors to C; ``clear_patches`` clears
#     both. Byte-for-byte identical phases between BIP and C with
#     patches active.
#   * Patches don't propagate across processes — they're an in-process
#     registry. Re-apply on each fresh interpreter.

#: JSON-friendly names for the bundled CATALOG + CATALOG_V2 patches.
#: v0.5.2: combined view of v0.4.0 (mag-only) + v0.5.2 (LS-fit, vindicated).
CATALOG_PATCHES: Tuple[str, ...] = tuple(sorted(_patches.COMBINED_CATALOG.keys()))


def _body_index(name: str) -> int:
    """Return the C-side body index for a Python body name; -1 if not found.

    Mirrors ``EphemerisBIPInstrument.body_to_idx`` — the order is the
    sorted body-name list, identical between Python and the C codegen.
    """
    try:
        return SUPPORTED_BODIES.index(name)
    except ValueError:
        return -1


def _mirror_patch_to_native(patch: _patches.Patch) -> Optional[str]:
    """Apply a Python Patch into the C-side registry.

    Returns ``None`` on success (or when no native is loaded — the
    Python overlay handles encode-time deltas in that case). Returns
    a human-readable error string when the C side rejected (capacity,
    duplicate name, bad index, bad param).

    The bridge's ``apply_patch`` / ``apply_custom_patch`` must call
    this AFTER the Python registry has accepted the patch; on a
    non-None return, revert the Python-side change so the two
    registries never drift.
    """
    from ephemerides_spectral import _native_bip
    if not _native_bip.HAS_NATIVE:
        return None
    if isinstance(patch, _patches.SinusoidPatch):
        idx = _body_index(patch.body)
        rc = _native_bip.native_apply_sinusoid_patch(
            name=patch.name, body_idx=idx,
            amplitude_deg=patch.amplitude_deg,
            period_days=patch.period_days,
            phase_rad=patch.phase_rad,
        )
    elif isinstance(patch, _patches.CoupledSinusoidPatch):
        idx_a = _body_index(patch.body_a)
        idx_b = _body_index(patch.body_b)
        rc = _native_bip.native_apply_coupled_patch(
            name=patch.name, body_idx_a=idx_a, body_idx_b=idx_b,
            amplitude_deg=patch.amplitude_deg,
            period_days=patch.period_days,
            phase_rad=patch.phase_rad,
            correlation=patch.correlation,
        )
    else:
        return f"unknown patch type {type(patch).__name__!r}"
    if rc == 0:
        return None
    if rc == _native_bip.ES_ERR_PATCH_FULL:
        return f"native registry at capacity (ES_MAX_PATCHES={_native_bip.ES_MAX_PATCHES})"
    if rc == _native_bip.ES_ERR_PATCH_DUPLICATE_NAME:
        return f"native registry already has a patch named {patch.name!r}"
    if rc == _native_bip.ES_ERR_PATCH_BAD_INDEX:
        return f"native registry rejected patch {patch.name!r}: bad body index"
    if rc == _native_bip.ES_ERR_PATCH_BAD_PARAM:
        return f"native registry rejected patch {patch.name!r}: bad param (period or correlation)"
    if rc == _native_bip.ES_ERR_PATCH_BAD_KIND:
        return f"native registry rejected patch {patch.name!r}: unknown kind"
    return f"native registry rejected patch {patch.name!r}: status={rc}"


def _native_clear_patches() -> int:
    """Wipe the C-side patch registry; returns the prior count.

    Wraps ``_native_bip.native_clear_patches`` so callers don't need
    to import the shim module.
    """
    from ephemerides_spectral import _native_bip
    return _native_bip.native_clear_patches()


def list_catalog_patches() -> Dict[str, Any]:
    """List the bundled diagnosed-fiber patch catalog.

    Each entry includes the patch's metadata + ``notes`` describing
    the FFT peak it targets and the suspected missing physics.
    """
    return {
        "ok": True,
        "patches": [
            _patches._patch_to_dict(p)
            for p in (_patches.COMBINED_CATALOG[name] for name in CATALOG_PATCHES)
        ],
    }


def list_active_patches() -> Dict[str, Any]:
    """List the currently-active runtime overlay patches."""
    return {
        "ok": True,
        "patches": _patches.list_patches(),
        "n_active": len(_patches.snapshot()),
    }


def apply_patch(patch_name: str) -> Dict[str, Any]:
    """Load a named bundled patch into the runtime overlay registry.

    See ``list_catalog_patches`` for available names. Same patch
    cannot be applied twice (raises ``ValueError`` underneath; we
    surface as ``{"ok": False}``).

    v0.4.1: also mirrors into the C-side registry so ``backend="c"``
    can apply the overlay natively. If the C side rejects the patch
    (capacity exceeded, etc.), the Python side is reverted so the
    two registries never drift.
    """
    if not isinstance(patch_name, str):
        return _err(f"patch_name must be a string, got {type(patch_name).__name__}")
    try:
        patch = _patches.apply_catalog_patch(patch_name)
    except KeyError:
        return _err(
            f"unknown catalog patch {patch_name!r}; "
            f"available: {list(CATALOG_PATCHES)}"
        )
    except ValueError as exc:
        return _err(str(exc))
    # Mirror to C; revert Python-side on failure to keep registries in sync.
    native_err = _mirror_patch_to_native(patch)
    if native_err is not None:
        # Roll back the Python registry — find and remove this patch by name.
        for active in _patches.snapshot():
            if active.name == patch.name:
                # No public per-item remove; clear+reapply remaining.
                remaining = [p for p in _patches.snapshot() if p.name != patch.name]
                _patches.clear_patches()
                for p in remaining:
                    _patches.apply_patch(p)
                break
        return _err(native_err)
    return {
        "ok": True,
        "applied": _patches._patch_to_dict(patch),
        "n_active": len(_patches.snapshot()),
    }


def apply_custom_patch(
    *,
    name: str,
    kind: str,
    body: Optional[str] = None,
    body_a: Optional[str] = None,
    body_b: Optional[str] = None,
    amplitude_deg: float = 0.0,
    period_days: float = 0.0,
    phase_rad: float = 0.0,
    correlation: int = -1,
    notes: str = "",
) -> Dict[str, Any]:
    """Construct + apply a user-authored patch from primitive args.

    Pyodide-friendly: takes only JSON-serialisable scalars. Use this
    when you've FFT-diagnosed your own residual peak and want to
    test a Fourier correction without authoring it as a dataclass.

    ``kind="sinusoid"`` requires ``body``; ``kind="coupled-sinusoid"``
    requires ``body_a`` and ``body_b``.
    """
    if not isinstance(name, str) or not name:
        return _err("patch name must be a non-empty string")
    try:
        if kind == "sinusoid":
            if not isinstance(body, str):
                return _err("sinusoid patch requires `body` (str)")
            patch: _patches.Patch = _patches.SinusoidPatch(
                name=name, body=body,
                amplitude_deg=float(amplitude_deg),
                period_days=float(period_days),
                phase_rad=float(phase_rad),
                notes=str(notes),
            )
        elif kind == "coupled-sinusoid":
            if not (isinstance(body_a, str) and isinstance(body_b, str)):
                return _err(
                    "coupled-sinusoid patch requires `body_a` and `body_b` (str)"
                )
            patch = _patches.CoupledSinusoidPatch(
                name=name, body_a=body_a, body_b=body_b,
                amplitude_deg=float(amplitude_deg),
                period_days=float(period_days),
                phase_rad=float(phase_rad),
                correlation=int(correlation),
                notes=str(notes),
            )
        else:
            return _err(
                f"unknown patch kind {kind!r}; "
                f"expected 'sinusoid' or 'coupled-sinusoid'"
            )
    except (ValueError, TypeError) as exc:
        return _err(str(exc))
    try:
        _patches.apply_patch(patch)
    except (ValueError, TypeError) as exc:
        return _err(str(exc))
    # Mirror to C; revert on failure.
    native_err = _mirror_patch_to_native(patch)
    if native_err is not None:
        remaining = [p for p in _patches.snapshot() if p.name != patch.name]
        _patches.clear_patches()
        for p in remaining:
            _patches.apply_patch(p)
        return _err(native_err)
    return {
        "ok": True,
        "applied": _patches._patch_to_dict(patch),
        "n_active": len(_patches.snapshot()),
    }


def clear_patches() -> Dict[str, Any]:
    """Remove all active runtime patches from both Python and C registries."""
    n_py = _patches.clear_patches()
    _native_clear_patches()  # idempotent; no-op if no native loaded
    return {"ok": True, "cleared": int(n_py)}


__all__ = [
    "DEFAULT_BACKEND",
    "SUPPORTED_BACKENDS",
    "SUPPORTED_BODIES",
    "ALLOWED_KERNELS",
    "LUNAR_KERNELS",
    "CATALOG_PATCHES",
    "get_version",
    "list_bodies",
    "list_kernels",
    "list_lunar_kernels",
    "list_couplings",
    "get_resolution",
    "get_system_state",
    "get_local_view",
    "get_eclipse_probability",
    "get_breathing_modulation",
    "jd_to_mars_time",
    "mars_time_to_jd",
    "jd_to_sol_uranian_time",
    "sol_uranian_time_to_jd",
    "get_lunar_phase",
    "get_natural_resonance_group",
    "find_syzygies",
    "list_catalog_patches",
    "list_active_patches",
    "apply_patch",
    "apply_custom_patch",
    "clear_patches",
]
