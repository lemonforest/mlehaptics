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
    # v0.8.0 Sol Symphony Times.
    VENUS_SIDEREAL_DAY_DAYS, VENUS_SOLAR_DAY_DAYS,
    VENUS_ORBITAL_PERIOD_YEARS, VENUS_AXIAL_TILT_DEG, VST_EPOCH_JD_TDB,
    MERCURY_SIDEREAL_DAY_DAYS, MERCURY_SOLAR_DAY_DAYS,
    MERCURY_ORBITAL_PERIOD_YEARS, MERCURY_AXIAL_TILT_DEG, MERT_EPOCH_JD_TDB,
    PLUTO_SIDEREAL_DAY_DAYS, PLUTO_ORBITAL_PERIOD_YEARS,
    PLUTO_AXIAL_TILT_DEG, PST_EPOCH_JD_TDB,
    SOL_CARRINGTON_DAY_DAYS, SOL_AXIAL_TILT_DEG, SOL_T_EPOCH_JD_TDB,
    JUPITER_SYS_III_DAY_DAYS, JUPITER_ORBITAL_PERIOD_YEARS,
    JUPITER_AXIAL_TILT_DEG, JOVT_EPOCH_JD_TDB,
    SATURN_SYS_III_DAY_DAYS, SATURN_ORBITAL_PERIOD_YEARS,
    SATURN_AXIAL_TILT_DEG, SATT_EPOCH_JD_TDB,
    NEPTUNE_SIDEREAL_DAY_DAYS, NEPTUNE_ORBITAL_PERIOD_YEARS,
    NEPTUNE_AXIAL_TILT_DEG, NEPT_EPOCH_JD_TDB,
    jd_to_lunar,
    jd_to_msd,
    jd_to_uranian_time,
    msd_to_jd,
    uranian_time_to_jd,
    jd_to_venus_time, venus_time_to_jd,
    jd_to_mercury_time, mercury_time_to_jd,
    jd_to_pluto_time, pluto_time_to_jd,
    jd_to_sol_sol_time as _jd_to_sol_sol_time,
    sol_sol_time_to_jd as _sol_sol_time_to_jd,
    jd_to_jovian_time, jovian_time_to_jd,
    jd_to_saturnian_time, saturnian_time_to_jd,
    jd_to_neptunian_time, neptunian_time_to_jd,
    # v0.9.1 Sol Terra + Sol Luna Times
    TERRA_SIDEREAL_DAY_DAYS, TERRA_SOLAR_DAY_DAYS,
    TERRA_ORBITAL_PERIOD_YEARS, TERRA_AXIAL_TILT_DEG, TERRAT_EPOCH_JD_TDB,
    LUNA_SIDEREAL_DAY_DAYS, LUNA_SOLAR_DAY_DAYS,
    LUNA_ORBITAL_PERIOD_DAYS, LUNA_AXIAL_TILT_DEG, LUNAT_EPOCH_JD_TDB,
    jd_to_terra_time, terra_time_to_jd,
    jd_to_luna_time, luna_time_to_jd,
    # v0.10.0 Sol Terra-Luna Time (STLT) — anchored Lunar time using the synodic month.
    STLT_SYNODIC_MONTH_DAYS, STLT_SAROS_CYCLE_DAYS, STLT_METONIC_CYCLE_DAYS,
    STLT_EPOCH_METON_JD_TDB, STLT_EPOCH_ANTIKYTHERA_JD_TDB,
    STLT_EPOCH_HIPPARCHUS_JD_TDB, STLT_EPOCH_MARDOKEMPAD_JD_TDB,
    STLT_EPOCH_J2000_JD_TDB, STLT_EPOCHS, STLT_DEFAULT_EPOCH,
    jd_to_terra_luna_time, terra_luna_time_to_jd,
    # v0.14.0 Sol Moon Times — generic moon-time primitive (Galileans first).
    SOL_MOON_TIME_J2000_JD_TDB, jd_to_moon_time, moon_time_to_jd,
)
from ephemerides_spectral._research.proper_time import (
    DEFAULT_REFERENCE as SPRT_DEFAULT_REFERENCE,
    SUPPORTED_REFERENCES as SPRT_SUPPORTED_REFERENCES,
    compare_proper_times as _compare_proper_times,
    get_proper_time_rate as _get_proper_time_rate_impl,
)
from ephemerides_spectral._research.kinematics import (
    DEFAULT_FRAME as KINEMATICS_DEFAULT_FRAME,
    SUPPORTED_FRAMES as KINEMATICS_SUPPORTED_FRAMES,
    AU_M as _KINEMATICS_AU_M,
    get_full_system_state as _get_full_system_state_impl,
    get_kinematic_state as _get_kinematic_state_impl,
)
from ephemerides_spectral._research.dynamics import (
    get_body_energies as _get_body_energies_impl,
    get_dynamics as _get_dynamics_impl,
    get_force_between as _get_force_between_impl,
)
from ephemerides_spectral._research.bodies import BODIES as _BODIES
from ephemerides_spectral._research.syzygy_window import (
    find_syzygies as _find_syzygies_impl,
)
from ephemerides_spectral._research.itn_window import (
    find_itn_pathways as _find_itn_pathways_impl,
    find_itn_chains as _find_itn_chains_impl,
)
from ephemerides_spectral._research.body_architecture import (
    HELIOCENTRIC_BODIES as _BODY_ARCH_DEFAULT,
    INNER_CLASS as _BODY_ARCH_INNER,
    OUTER_CLASS as _BODY_ARCH_OUTER,
    compute_body_architecture as _compute_body_architecture_impl,
)
from ephemerides_spectral._research.predict_itn_accessibility import (
    predict_itn_accessibility as _predict_itn_accessibility_impl,
)
from ephemerides_spectral._research.em_instrument import (
    compute_em_architecture as _compute_em_architecture_impl,
    compute_em_state_at_jd as _compute_em_state_at_jd_impl,
    list_em_couplings as _list_em_couplings_impl,
)
from ephemerides_spectral._research.geodetic_catalog import (
    compute_geodetic_architecture as _compute_geodetic_architecture_impl,
    compute_geodetic_state as _compute_geodetic_state_impl,
    list_geodetic_models as _list_geodetic_models_impl,
)
from ephemerides_spectral._research.magnetic_multipole_catalog import (
    compute_magnetic_architecture as _compute_magnetic_architecture_impl,
    compute_magnetic_multipoles as _compute_magnetic_multipoles_impl,
    compute_solar_synoptic_state as _compute_solar_synoptic_state_impl,
    evaluate_magnetic_field as _evaluate_magnetic_field_impl,
    list_magnetic_multipoles as _list_magnetic_multipoles_impl,
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
            "abbreviation": "SUT",
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


# ──────────────────────────────────────────────────────────────────────
# v0.8.0 — Sol Symphony Times: Venus, Mercury, Pluto, Sol, Jupiter, Saturn
# ──────────────────────────────────────────────────────────────────────
#
# Each body's "Sol Time" exposes its rotation phase + orbital phase
# anchored at a conventional epoch (J2000, IAU prime meridian, etc.).
# These complement the established Sol Mars Time (MSD/MTC) and Sol
# Lunar Time (synodic+sidereal phase) by extending the natural-symphony
# framing to every body in the encoder roster.
#
# Naming hierarchy convention (for future moon ports):
# - Established planet/star times: "Sol <Adjective> Time" (Sol Mars,
#   Sol Lunar, Sol Uranian, Sol Venusian, Sol Mercurian, Sol Plutonian,
#   Sol Jovian, Sol Saturnian, Sol Sol).
# - Future moon times follow parent-body hierarchy:
#   "Sol <Parent>-<Body> Time" (e.g., Sol Pluto-Charon Time, Sol
#   Jupiter-Io Time, Sol Earth-Moon Time). Established conventions
#   (Sol Lunar = Earth-Moon shorthand) are kept.


def _scalar_inverse(value: Any, name: str, impl: Any,
                    out_field: str) -> Dict[str, Any]:
    """Shared validation + inversion for the *_to_jd bridge methods."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return _err(f"{name} must be a number, got {type(value).__name__}")
    if not math.isfinite(f):
        return _err(f"{name} must be finite, got {f}")
    return {
        "ok": True,
        out_field: f,
        "jd_tdb": float(impl(f)),
    }


def jd_to_sol_venus_time(jd_tdb: float) -> Dict[str, Any]:
    """JD (TDB) → Sol Venusian Time. Venus is retrograde with sidereal
    day = 243.0 Earth-days (longer than its 224.7-day year), so the
    sidereal vs. solar day distinction matters: the dataclass exposes
    both, with the solar day (116.75 Earth-days) as the natural
    "what time is it on Venus" coordinate."""
    err = _validate_jd(jd_tdb)
    if err is not None: return err
    out = jd_to_venus_time(float(jd_tdb))
    return {
        "ok": True,
        **out.to_dict(),
        "epoch": {
            "description": "J2000.0 (no IAU VSD convention; mirroring MSD)",
            "jd_tdb": float(VST_EPOCH_JD_TDB),
            "sidereal_day_days": float(VENUS_SIDEREAL_DAY_DAYS),
            "solar_day_days": float(VENUS_SOLAR_DAY_DAYS),
            "orbital_period_years": float(VENUS_ORBITAL_PERIOD_YEARS),
            "axial_tilt_deg": float(VENUS_AXIAL_TILT_DEG),
            "abbreviation": "SVT",
        },
    }


def sol_venus_time_to_jd(vsd_solar: float) -> Dict[str, Any]:
    """Inverse on the Venus solar-day count (`vsd_solar`)."""
    return _scalar_inverse(vsd_solar, "vsd_solar",
                           venus_time_to_jd, "vsd_solar")


def jd_to_sol_mercury_time(jd_tdb: float) -> Dict[str, Any]:
    """JD (TDB) → Sol Mercurian Time. Mercury's 3:2 spin-orbit resonance
    means the solar day = 2 Mercury years exactly. Both sidereal and
    solar day phase are exposed; the solar day is the natural answer
    to "what time is it on Mercury" because that's what an observer
    on the surface experiences."""
    err = _validate_jd(jd_tdb)
    if err is not None: return err
    out = jd_to_mercury_time(float(jd_tdb))
    return {
        "ok": True,
        **out.to_dict(),
        "epoch": {
            "description": "J2000.0 with IAU prime meridian at Hun Kal crater",
            "jd_tdb": float(MERT_EPOCH_JD_TDB),
            "sidereal_day_days": float(MERCURY_SIDEREAL_DAY_DAYS),
            "solar_day_days": float(MERCURY_SOLAR_DAY_DAYS),
            "orbital_period_years": float(MERCURY_ORBITAL_PERIOD_YEARS),
            "axial_tilt_deg": float(MERCURY_AXIAL_TILT_DEG),
            "abbreviation": "SMeT",
            "spin_orbit_resonance": "3:2 (solar day = 2 × year exactly)",
        },
    }


def sol_mercury_time_to_jd(mer_sd_solar: float) -> Dict[str, Any]:
    """Inverse on the Mercury solar-day count."""
    return _scalar_inverse(mer_sd_solar, "mer_sd_solar",
                           mercury_time_to_jd, "mer_sd_solar")


def jd_to_sol_pluto_time(jd_tdb: float) -> Dict[str, Any]:
    """JD (TDB) → Sol Plutonian Time. Pluto's tidally-locked Pluto-Charon
    system rotates as one; the IAU-2015 prime meridian convention
    anchors at the sub-Charon point. Anchor: New Horizons closest
    approach 2015-07-14 (JD 2457217.0)."""
    err = _validate_jd(jd_tdb)
    if err is not None: return err
    out = jd_to_pluto_time(float(jd_tdb))
    return {
        "ok": True,
        **out.to_dict(),
        "epoch": {
            "description": "New Horizons closest approach 2015-07-14",
            "jd_tdb": float(PST_EPOCH_JD_TDB),
            "sidereal_day_days": float(PLUTO_SIDEREAL_DAY_DAYS),
            "orbital_period_years": float(PLUTO_ORBITAL_PERIOD_YEARS),
            "axial_tilt_deg": float(PLUTO_AXIAL_TILT_DEG),
            "abbreviation": "SPT",
            "note": "Pluto-Charon mutually tidally locked; system rotates as one",
        },
    }


def sol_pluto_time_to_jd(psd: float) -> Dict[str, Any]:
    """Inverse on the Pluto sol-date count."""
    return _scalar_inverse(psd, "psd",
                           pluto_time_to_jd, "psd")


def jd_to_sol_sol_time(jd_tdb: float) -> Dict[str, Any]:
    """JD (TDB) → Sol Sol Time. The Sun's own time, in the Carrington
    rotation system: integer Carrington Rotation Number (CRN) starting
    at CRN 1 on 1853-11-09 (JD 2398167.4), each rotation = 25.38 Earth-
    days at ~16° solar latitude. The Sun has differential rotation
    (equator ~24.47 d, poles ~38 d); 25.38 d is the conventional
    reference. Galactic-orbit phase (~219 Myr period) is included for
    completeness but is too slow for any practical use."""
    err = _validate_jd(jd_tdb)
    if err is not None: return err
    out = _jd_to_sol_sol_time(float(jd_tdb))
    return {
        "ok": True,
        **out.to_dict(),
        "epoch": {
            "description": "Carrington Rotation 1 (1853-11-09)",
            "jd_tdb": float(SOL_T_EPOCH_JD_TDB),
            "carrington_day_days": float(SOL_CARRINGTON_DAY_DAYS),
            "axial_tilt_deg": float(SOL_AXIAL_TILT_DEG),
            "abbreviation": "SSoT",
            "note": ("Sun has differential rotation; 25.38 d is the "
                     "Carrington reference at ~16° latitude"),
        },
    }


def sol_sol_time_to_jd(crn: float) -> Dict[str, Any]:
    """Inverse on the Carrington Rotation Number (CRN)."""
    return _scalar_inverse(crn, "crn", _sol_sol_time_to_jd, "crn")


def jd_to_sol_jovian_time(jd_tdb: float) -> Dict[str, Any]:
    """JD (TDB) → Sol Jovian Time. Jupiter has differential rotation;
    we use System III (magnetic-field-axis rotation, 9h 55m 30s) per
    IAU. System I (equatorial cloud features, 9h 50m 30s) and System
    II (higher-latitude clouds, 9h 55m 41s) are not exposed here. Anchor:
    System III 1965.0 reference epoch."""
    err = _validate_jd(jd_tdb)
    if err is not None: return err
    out = jd_to_jovian_time(float(jd_tdb))
    return {
        "ok": True,
        **out.to_dict(),
        "epoch": {
            "description": "System III 1965.0 reference (IAU/Riddle-Warwick)",
            "jd_tdb": float(JOVT_EPOCH_JD_TDB),
            "sys_iii_day_days": float(JUPITER_SYS_III_DAY_DAYS),
            "orbital_period_years": float(JUPITER_ORBITAL_PERIOD_YEARS),
            "axial_tilt_deg": float(JUPITER_AXIAL_TILT_DEG),
            "abbreviation": "SJT",
            "rotation_system_options": ["I (equatorial clouds)",
                                        "II (mid-latitude clouds)",
                                        "III (magnetic field — used here)"],
        },
    }


def sol_jovian_time_to_jd(jsd: float) -> Dict[str, Any]:
    """Inverse on the Jupiter sol-date count."""
    return _scalar_inverse(jsd, "jsd",
                           jovian_time_to_jd, "jsd")


def jd_to_sol_saturnian_time(jd_tdb: float) -> Dict[str, Any]:
    """JD (TDB) → Sol Saturnian Time. Uses the Cassini-revised System
    III rotation period (10h 32m 35s ± 13s, Mankovich et al. 2019 ApJ
    871:1) — the older Voyager-derived 10h 39m 22.4s is now superseded.
    Saturn's rotation rate was determined via ring seismology, not
    moon orbits — Sol Saturnian Time is fully independent of the
    Saturnian moon set. Anchor: J2000.0."""
    err = _validate_jd(jd_tdb)
    if err is not None: return err
    out = jd_to_saturnian_time(float(jd_tdb))
    return {
        "ok": True,
        **out.to_dict(),
        "epoch": {
            "description": "J2000.0",
            "jd_tdb": float(SATT_EPOCH_JD_TDB),
            "sys_iii_day_days": float(SATURN_SYS_III_DAY_DAYS),
            "orbital_period_years": float(SATURN_ORBITAL_PERIOD_YEARS),
            "axial_tilt_deg": float(SATURN_AXIAL_TILT_DEG),
            "abbreviation": "SST",
            "source": ("Mankovich et al. 2019 ApJ 871:1 — ring "
                       "seismology, supersedes Voyager value"),
        },
    }


def sol_saturnian_time_to_jd(ssd: float) -> Dict[str, Any]:
    """Inverse on the Saturn sol-date count."""
    return _scalar_inverse(ssd, "ssd",
                           saturnian_time_to_jd, "ssd")


def jd_to_sol_neptunian_time(jd_tdb: float) -> Dict[str, Any]:
    """JD (TDB) → Sol Neptunian Time. Voyager 2 (1989) measured Neptune's
    System III rotation period as 16h 6m 36s ± 3s; that's still the
    canonical value. Prograde rotation, mid-range axial tilt (28.32°).
    Year = 164.79 Earth-years. Anchor: J2000.0."""
    err = _validate_jd(jd_tdb)
    if err is not None: return err
    out = jd_to_neptunian_time(float(jd_tdb))
    return {
        "ok": True,
        **out.to_dict(),
        "epoch": {
            "description": "J2000.0",
            "jd_tdb": float(NEPT_EPOCH_JD_TDB),
            "sidereal_day_days": float(NEPTUNE_SIDEREAL_DAY_DAYS),
            "orbital_period_years": float(NEPTUNE_ORBITAL_PERIOD_YEARS),
            "axial_tilt_deg": float(NEPTUNE_AXIAL_TILT_DEG),
            "abbreviation": "SNT",
            "source": ("Voyager 2 1989 magnetic-field tilt-tracking; "
                       "no Cassini-equivalent ring-seismology mission "
                       "to Neptune yet"),
        },
    }


def sol_neptunian_time_to_jd(nsd: float) -> Dict[str, Any]:
    """Inverse on the Neptune sol-date count."""
    return _scalar_inverse(nsd, "nsd",
                           neptunian_time_to_jd, "nsd")


# ──────────────────────────────────────────────────────────────────────
# v0.9.1 — Sol Terra Time (STT) + Sol Luna Time (SLT)
# ──────────────────────────────────────────────────────────────────────
#
# Per the v0.9.1 naming-convention table, Terra and Luna get their own
# Sol Time entries — Terra's is the surface clock (sidereal day 23h
# 56m 4s; solar day = 24h by definition); Luna's is the surface clock
# of the tidally-locked moon (sidereal = orbital = 27.32 d; solar
# (synodic) = 29.53 d).
#
# Sol Luna Time (SLT) is DISTINCT from Sol Lunar Time (the existing
# `get_lunar_phase` bridge surface, which returns Luna's synodic +
# sidereal phase as observed from Terra). Same body, different
# observer frame.


def jd_to_sol_terra_time(jd_tdb: float) -> Dict[str, Any]:
    """JD (TDB) → Sol Terra Time (STT). Terra's surface clock.

    Notable distinction:
    - sidereal day = 23h 56m 4s = 0.99726957 Earth-days (rotation
      relative to the stars)
    - solar day = 24h = 1.0 Earth-day (rotation relative to the Sun)

    The 3m 56s/day gap arises because Terra moves ~1° around its orbit
    per day, so the planet rotates ~361° between successive solar noons
    but only 360° between successive star transits.
    """
    err = _validate_jd(jd_tdb)
    if err is not None: return err
    out = jd_to_terra_time(float(jd_tdb))
    return {
        "ok": True,
        **out.to_dict(),
        "epoch": {
            "description": "J2000.0 with prime meridian at Greenwich",
            "jd_tdb": float(TERRAT_EPOCH_JD_TDB),
            "sidereal_day_days": float(TERRA_SIDEREAL_DAY_DAYS),
            "solar_day_days": float(TERRA_SOLAR_DAY_DAYS),
            "orbital_period_years": float(TERRA_ORBITAL_PERIOD_YEARS),
            "axial_tilt_deg": float(TERRA_AXIAL_TILT_DEG),
            "abbreviation": "STT",
        },
    }


def sol_terra_time_to_jd(tsd_solar: float) -> Dict[str, Any]:
    """Inverse on the Terra solar-day count."""
    return _scalar_inverse(tsd_solar, "tsd_solar",
                           terra_time_to_jd, "tsd_solar")


def jd_to_sol_luna_time(jd_tdb: float) -> Dict[str, Any]:
    """JD (TDB) → Sol Luna Time (SLT). Luna's surface clock.

    Tidally locked to Terra, so Luna's sidereal day equals its orbital
    period (27.32 d). The solar day (29.53 d) is longer because the
    Terra-Luna system also moves around Sol during the cycle — that's
    the synodic month.

    DISTINCT from `get_lunar_phase` (Sol Lunar Time), which returns
    Luna's synodic + sidereal phase as observed from Terra. Same body,
    different observer frame.
    """
    err = _validate_jd(jd_tdb)
    if err is not None: return err
    out = jd_to_luna_time(float(jd_tdb))
    return {
        "ok": True,
        **out.to_dict(),
        "epoch": {
            "description": "J2000.0 with IAU 2015 prime meridian at the sub-Terra point",
            "jd_tdb": float(LUNAT_EPOCH_JD_TDB),
            "sidereal_day_days": float(LUNA_SIDEREAL_DAY_DAYS),
            "solar_day_days": float(LUNA_SOLAR_DAY_DAYS),
            "orbital_period_days": float(LUNA_ORBITAL_PERIOD_DAYS),
            "axial_tilt_deg": float(LUNA_AXIAL_TILT_DEG),
            "abbreviation": "SLT",
            "note": ("tidally locked: sidereal day = orbital period; "
                     "distinct from Sol Lunar Time (get_lunar_phase) which "
                     "returns Luna's phase observed from Terra"),
        },
    }


def sol_luna_time_to_jd(lsd_solar: float) -> Dict[str, Any]:
    """Inverse on the Luna solar (synodic) day count."""
    return _scalar_inverse(lsd_solar, "lsd_solar",
                           luna_time_to_jd, "lsd_solar")


# ──────────────────────────────────────────────────────────────────────
# v0.10.0 Sol Terra-Luna Time (STLT) — anchored Lunar time using the synodic month
# ──────────────────────────────────────────────────────────────────────
#
# A *system-level* time scale: the natural unit is the synodic month
# (29.530589 days), and the default epoch is **Meton's summer solstice
# 27 June 432 BCE** — the foundational Greek lunar-solar-reconciliation
# anchor. STLT is the first Sol Time in the package whose default
# epoch is NOT J2000.0 / Terra-borrowed.
#
# The choice rationale lives in notebook §7.4 and is independently
# validated by `research/lunar_epoch_candidates.py` (Phase A of #95):
# the Hipparchus-Babylonian eclipse-archive midpoint (Mardokempad
# 721 BCE + Hipparchus 141 BCE) lands within +240 days of Meton's
# solstice — *same year*. Greek mathematical astronomy's eclipse
# archive sits centred on Meton's lifetime.

#: Description used in epoch-block returns for each STLT epoch alias.
_STLT_EPOCH_DESCRIPTIONS: Dict[str, str] = {
    "meton":        "Meton of Athens summer solstice, 27 June 432 BCE proleptic Julian — the calibration anchor of the 19-year Metonic cycle (235 synodic months ≈ 19 tropical years).",
    "antikythera":  "Antikythera mechanism Saros-dial anchor: solar eclipse 23 August 205 BCE (Freeth & Jones 2012, 'The Cosmos in the Antikythera Mechanism').",
    "hipparchus":   "Hipparchus's calibration lunar eclipse, 25 January 141 BCE (Almagest VI.5).",
    "mardokempad":  "Earliest Babylonian eclipse Ptolemy cites (Almagest IV.6): lunar eclipse from Mardokempad's first regnal year, 19 March 721 BCE — the foundational record Hipparchus calibrated against.",
    "j2000":        "J2000.0 — modern reference epoch, Terra-borrowed.",
}


def jd_to_sol_terra_luna_time(
    jd_tdb: float,
    *,
    epoch: str = STLT_DEFAULT_EPOCH,
) -> Dict[str, Any]:
    """JD (TDB) → Sol Terra-Luna Time (STLT).

    Anchored Lunar time using the synodic month as the natural unit
    (Luna's phase observed from Terra; the "Terra-Luna" in the name
    follows the moons-stuck-to-parent convention). Synodic month
    (29.530589 days) is the natural unit; Saros (18.03 yr) and Metonic
    (19.00 yr) cycle counts come along for free.

    Parameters
    ----------
    jd_tdb : float
        Julian Date in TDB.
    epoch : str, default ``"meton"``
        Which historical anchor to count from. One of:

        - ``"meton"`` *(default)* — Meton's summer solstice, 27 June
          432 BCE. The cycle the Antikythera mechanism's Metonic dial
          encodes; Greek astronomy's center of mass.
        - ``"antikythera"`` — solar eclipse 23 August 205 BCE, the
          Antikythera mechanism's Saros-dial anchor (Freeth & Jones
          2012). Project namesake.
        - ``"hipparchus"`` — Hipparchus's calibration lunar eclipse,
          25 January 141 BCE (Almagest VI.5).
        - ``"mardokempad"`` — earliest Babylonian eclipse Ptolemy cites,
          19 March 721 BCE (Almagest IV.6). Pre-Greek anchor.
        - ``"j2000"`` — modern reference, Terra-borrowed (matches the
          existing Sol Time pattern).

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": ..., "epoch_name": "meton",
            "epoch_jd_tdb": 1645528.0, "days_since_epoch": ...,
            "synodic_count": ..., "synodic_phase": ...,
            "saros_count": ..., "saros_phase": ...,
            "metonic_count": ..., "metonic_phase": ...,
            "epoch": {description, jd_tdb, synodic_month_days, ...,
            abbreviation: "STLT"}}``.

    Notes
    -----
    STLT is the first Sol Time member with a default epoch that is *not*
    J2000.0. The `epoch` parameter lets callers swap in any of the four
    Greek-historical alternatives or fall back to J2000 for parity with
    the rest of the Sol Time series. House-epoch design choice; not a
    claim to be NASA's eventual Lunar Coordinated Time (LCT) standard.
    """
    err = _validate_jd(jd_tdb)
    if err is not None: return err
    if epoch not in STLT_EPOCHS:
        return _err(
            f"epoch must be one of {sorted(STLT_EPOCHS)}, got {epoch!r}"
        )
    out = jd_to_terra_luna_time(float(jd_tdb), epoch=epoch)
    return {
        "ok": True,
        **out.to_dict(),
        "epoch": {
            "name": epoch,
            "description": _STLT_EPOCH_DESCRIPTIONS[epoch],
            "jd_tdb": float(STLT_EPOCHS[epoch]),
            "synodic_month_days":  float(STLT_SYNODIC_MONTH_DAYS),
            "saros_cycle_days":    float(STLT_SAROS_CYCLE_DAYS),
            "metonic_cycle_days":  float(STLT_METONIC_CYCLE_DAYS),
            "abbreviation": "STLT",
            "available_epochs": sorted(STLT_EPOCHS),
            "default_epoch": STLT_DEFAULT_EPOCH,
            "note": ("STLT is anchored Lunar time (synodic-month "
                     "count from a historical epoch). The 'Terra-Luna' "
                     "in the name follows the moons-stuck-to-parent "
                     "convention. Distinct from SLT (Luna's surface "
                     "clock), STT (Terra's surface clock), and Sol "
                     "Lunar Time (Luna's phase observed from Terra). "
                     "Default epoch is Meton's solstice 432 BCE — not J2000."),
        },
    }


def sol_terra_luna_time_to_jd(
    synodic_count: float,
    *,
    epoch: str = STLT_DEFAULT_EPOCH,
) -> Dict[str, Any]:
    """Inverse on the synodic-month count.

    Parameters
    ----------
    synodic_count : float
        Number of synodic months since the chosen epoch.
    epoch : str, default ``"meton"``
        See ``jd_to_sol_terra_luna_time`` for the full list of accepted
        epoch names.
    """
    if epoch not in STLT_EPOCHS:
        return _err(
            f"epoch must be one of {sorted(STLT_EPOCHS)}, got {epoch!r}"
        )
    try:
        sc = float(synodic_count)
    except (TypeError, ValueError):
        return _err(
            f"synodic_count must be a number, got {type(synodic_count).__name__}"
        )
    return {
        "ok": True,
        "jd_tdb": terra_luna_time_to_jd(sc, epoch=epoch),
        "epoch_name": epoch,
        "synodic_count": sc,
    }


# ──────────────────────────────────────────────────────────────────────
# v0.14.0 Sol Moon Times — Galileans (Io / Europa / Ganymede / Callisto)
# v0.14.1 Sol Moon Times — Saturnians (11 moons) + abbreviation policy switch
# ──────────────────────────────────────────────────────────────────────
#
# Per the moons-stuck-to-parent naming convention (v0.9.1):
#   Sol Jupiter-Io Time, Sol Saturn-Mimas Time, ...
#
# Each moon is tidally locked, so sidereal day = orbital period =
# rotation period (one synchronized cycle). Anchored at J2000.0 by
# default — historical anchors like STLT's Meton don't generalise to
# non-Luna moons.
#
# **Abbreviation policy switch (v0.14.1).** v0.14.0 shipped Galileans
# with the 4-letter `S<Planet><Moon>T` pattern (SJIT / SJET / SJGT /
# SJCT). When v0.14.1 added the 11 Saturnians, two collisions surfaced:
#   - Tethys + Titan: both 'T' under Saturn  → both would be SSTT
#   - Enceladus + Epimetheus: both 'E'       → both would be SSET
#
# Per the ROADMAP "Naming convention contingencies" section, a single
# collision triggers a uniform switch across ALL Sol Moon Times to the
# 6-letter `S<Planet2><Moon2>T` pattern. Galileans retroactively
# renamed in v0.14.1; the new convention applies to all subsequent
# moon-family ships.
#
# Naming + abbreviations (v0.14.1+):
#
#   Body         | Sol Time name                 | Abbrev  | CLI subcommand
#   -------------|-------------------------------|---------|------------------------
#   io           | Sol Jupiter-Io Time           | SJuIoT  | time-jupiter-io
#   europa       | Sol Jupiter-Europa Time       | SJuEuT  | time-jupiter-europa
#   ganymede     | Sol Jupiter-Ganymede Time     | SJuGaT  | time-jupiter-ganymede
#   callisto     | Sol Jupiter-Callisto Time     | SJuCaT  | time-jupiter-callisto
#   mimas        | Sol Saturn-Mimas Time         | SSaMiT  | time-saturn-mimas
#   enceladus    | Sol Saturn-Enceladus Time     | SSaEnT  | time-saturn-enceladus
#   tethys       | Sol Saturn-Tethys Time        | SSaTeT  | time-saturn-tethys
#   dione        | Sol Saturn-Dione Time         | SSaDiT  | time-saturn-dione
#   rhea         | Sol Saturn-Rhea Time          | SSaRhT  | time-saturn-rhea
#   titan        | Sol Saturn-Titan Time         | SSaTiT  | time-saturn-titan
#   hyperion     | Sol Saturn-Hyperion Time      | SSaHyT  | time-saturn-hyperion
#   iapetus      | Sol Saturn-Iapetus Time       | SSaIaT  | time-saturn-iapetus
#   phoebe       | Sol Saturn-Phoebe Time        | SSaPhT  | time-saturn-phoebe
#   janus        | Sol Saturn-Janus Time         | SSaJaT  | time-saturn-janus
#   epimetheus   | Sol Saturn-Epimetheus Time    | SSaEpT  | time-saturn-epimetheus
#
# Laplace resonance among Io / Europa / Ganymede (canonical
# n_Io − 3·n_Europa + 2·n_Ganymede ≈ 0) is exposed in the test module
# and the notebook §7.6 prose. The Saturnians have multiple known
# resonances too (Mimas-Tethys 4:2 = Cassini Division, Enceladus-Dione
# 2:1 powers Enceladus's tidal heating, Titan-Hyperion 4:3 driving
# Hyperion's chaotic rotation) — same handling as Galilean Laplace:
# pair-relations stay out of the per-moon dict.
# ──────────────────────────────────────────────────────────────────────

# Each moon's sidereal period is its orbital period (tidally locked).
# Pulled from BODIES at call time so any future precision update to
# BODIES propagates automatically.
_GALILEAN_PARENT: str = "jupiter"
_SATURNIAN_PARENT: str = "saturn"
_MARTIAN_PARENT: str = "mars"
_URANIAN_PARENT: str = "uranus"
_NEPTUNIAN_PARENT: str = "neptune"
_PLUTONIAN_PARENT: str = "pluto"  # v0.15.0


def _moon_time_response(body_key: str, parent_key: str,
                        abbrev: str, sol_time_name: str) -> Any:
    """Internal helper for Galilean (and future moon-family) wrappers.

    Closure-style — returns a function that takes (jd_tdb) and returns
    the bridge-shaped Sol Moon Time response dict. Keeps the four
    near-identical Galilean wrappers below thin and consistent.
    """
    def _impl(jd_tdb: float) -> Dict[str, Any]:
        err = _validate_jd(jd_tdb)
        if err is not None:
            return err
        if body_key not in BODIES:
            return _err(
                f"internal error: body {body_key!r} not in BODIES "
                f"(this is a bug; please report)"
            )
        body = BODIES[body_key]
        out = jd_to_moon_time(
            body_key,
            float(jd_tdb),
            parent_name=parent_key,
            sidereal_period_days=float(body.period_days),
        )
        return {
            "ok": True,
            **out.to_dict(),
            "epoch": {
                "name": "j2000",
                "description": (
                    "J2000.0 — modern reference epoch shared with the "
                    "rest of the Sol Time series. Historical anchors "
                    "(like STLT's Meton solstice) don't generalise to "
                    "non-Luna moons."
                ),
                "jd_tdb": float(SOL_MOON_TIME_J2000_JD_TDB),
                "sidereal_period_days": float(body.period_days),
                "abbreviation": abbrev,
                "sol_time_name": sol_time_name,
                "parent_body": parent_key,
                "moon_body": body_key,
                "note": (
                    f"{sol_time_name} ({abbrev}) is the anchored "
                    f"sidereal-cycle count for {body.name} since "
                    f"J2000. {body.name} is tidally locked, so "
                    f"sidereal day = orbital period = rotation period "
                    f"= {float(body.period_days):.6f} days."
                ),
            },
        }
    return _impl


def _moon_time_to_jd_response(body_key: str, abbrev: str) -> Any:
    """Inverse helper — sidereal_count -> JD (TDB)."""
    def _impl(sidereal_count: float) -> Dict[str, Any]:
        if body_key not in BODIES:
            return _err(
                f"internal error: body {body_key!r} not in BODIES"
            )
        body = BODIES[body_key]
        try:
            sc = float(sidereal_count)
        except (TypeError, ValueError):
            return _err(
                f"sidereal_count must be a number, got "
                f"{type(sidereal_count).__name__}"
            )
        return {
            "ok": True,
            "jd_tdb": moon_time_to_jd(
                sc, sidereal_period_days=float(body.period_days)
            ),
            "sidereal_count": sc,
            "body_name": body_key,
            "abbreviation": abbrev,
        }
    return _impl


jd_to_sol_jupiter_io_time = _moon_time_response(
    "io", _GALILEAN_PARENT, "SJuIoT", "Sol Jupiter-Io Time"
)
jd_to_sol_jupiter_io_time.__doc__ = (
    """JD (TDB) → Sol Jupiter-Io Time (SJIT).

    Anchored sidereal-cycle count for Io since J2000.0. Io is tidally
    locked to Jupiter (sidereal day = orbital period = 1.769 days).
    Innermost Galilean; participates in the 4:2:1 Laplace resonance
    with Europa and Ganymede.

    Parameters
    ----------
    jd_tdb : float
        Julian Date in TDB.

    Returns
    -------
    dict
        ``{"ok": True, "jd_tdb": ..., "body_name": "io",
            "parent_name": "jupiter", "epoch_name": "j2000",
            "sidereal_period_days": 1.769..., "sidereal_count": ...,
            "sidereal_phase": ..., "epoch": {...abbreviation: "SJIT"}}``.
    """
)

sol_jupiter_io_time_to_jd = _moon_time_to_jd_response("io", "SJuIoT")
sol_jupiter_io_time_to_jd.__doc__ = (
    "Inverse: sidereal-cycle count → JD (TDB) for Io."
)

jd_to_sol_jupiter_europa_time = _moon_time_response(
    "europa", _GALILEAN_PARENT, "SJuEuT", "Sol Jupiter-Europa Time"
)
jd_to_sol_jupiter_europa_time.__doc__ = (
    """JD (TDB) → Sol Jupiter-Europa Time (SJET).

    Anchored sidereal-cycle count for Europa since J2000.0. Europa
    is tidally locked (sidereal day = orbital period = 3.551 days).
    Middle Galilean by Laplace ordering; participates in the 4:2:1
    resonance.
    """
)

sol_jupiter_europa_time_to_jd = _moon_time_to_jd_response("europa", "SJuEuT")
sol_jupiter_europa_time_to_jd.__doc__ = (
    "Inverse: sidereal-cycle count → JD (TDB) for Europa."
)

jd_to_sol_jupiter_ganymede_time = _moon_time_response(
    "ganymede", _GALILEAN_PARENT, "SJuGaT", "Sol Jupiter-Ganymede Time"
)
jd_to_sol_jupiter_ganymede_time.__doc__ = (
    """JD (TDB) → Sol Jupiter-Ganymede Time (SJGT).

    Anchored sidereal-cycle count for Ganymede since J2000.0. Ganymede
    is tidally locked (sidereal day = orbital period = 7.155 days).
    Largest moon in the solar system; outermost Galilean in the 4:2:1
    Laplace resonance.
    """
)

sol_jupiter_ganymede_time_to_jd = _moon_time_to_jd_response("ganymede", "SJuGaT")
sol_jupiter_ganymede_time_to_jd.__doc__ = (
    "Inverse: sidereal-cycle count → JD (TDB) for Ganymede."
)

jd_to_sol_jupiter_callisto_time = _moon_time_response(
    "callisto", _GALILEAN_PARENT, "SJuCaT", "Sol Jupiter-Callisto Time"
)
jd_to_sol_jupiter_callisto_time.__doc__ = (
    """JD (TDB) → Sol Jupiter-Callisto Time (SJCT).

    Anchored sidereal-cycle count for Callisto since J2000.0. Callisto
    is tidally locked (sidereal day = orbital period = 16.689 days).
    Outermost Galilean; the only one **not** participating in the
    Laplace resonance — its mean motion is irrational with the
    Io-Europa-Ganymede triple.
    """
)

sol_jupiter_callisto_time_to_jd = _moon_time_to_jd_response("callisto", "SJuCaT")
sol_jupiter_callisto_time_to_jd.__doc__ = (
    "Inverse: sidereal-cycle count → JD (TDB) for Callisto."
)


# ──────────────────────────────────────────────────────────────────────
# v0.14.1 Sol Moon Times — Saturnians (11 moons)
# ──────────────────────────────────────────────────────────────────────
#
# 9 classical Saturnians + 2 co-orbitals (Janus, Epimetheus).
# All tidally locked, J2000-anchored.
#
# Notable resonances (for the notebook prose, not exposed in dicts):
#   Mimas-Tethys 4:2     — Cassini Division
#   Enceladus-Dione 2:1  — powers Enceladus's tidal heating
#   Titan-Hyperion 4:3   — drives Hyperion's chaotic rotation
#   Janus-Epimetheus     — co-orbital horseshoe orbit (~4 yr swap)
# ──────────────────────────────────────────────────────────────────────

# Per-body bridge wrappers, generated via the shared helpers.
jd_to_sol_saturn_mimas_time      = _moon_time_response("mimas",      _SATURNIAN_PARENT, "SSaMiT", "Sol Saturn-Mimas Time")
jd_to_sol_saturn_mimas_time.__doc__ = "JD (TDB) → Sol Saturn-Mimas Time (SSaMiT). Innermost classical Saturnian; participates in the 4:2 Mimas-Tethys resonance that opens the Cassini Division. Sidereal day = orbital period = 0.942 days."
sol_saturn_mimas_time_to_jd      = _moon_time_to_jd_response("mimas",      "SSaMiT")
sol_saturn_mimas_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Mimas."

jd_to_sol_saturn_enceladus_time  = _moon_time_response("enceladus",  _SATURNIAN_PARENT, "SSaEnT", "Sol Saturn-Enceladus Time")
jd_to_sol_saturn_enceladus_time.__doc__ = "JD (TDB) → Sol Saturn-Enceladus Time (SSaEnT). Cryovolcanic moon with a subsurface ocean; participates in the 2:1 Enceladus-Dione resonance that powers its tidal heating. Sidereal day = orbital period = 1.370 days."
sol_saturn_enceladus_time_to_jd  = _moon_time_to_jd_response("enceladus",  "SSaEnT")
sol_saturn_enceladus_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Enceladus."

jd_to_sol_saturn_tethys_time     = _moon_time_response("tethys",     _SATURNIAN_PARENT, "SSaTeT", "Sol Saturn-Tethys Time")
jd_to_sol_saturn_tethys_time.__doc__ = "JD (TDB) → Sol Saturn-Tethys Time (SSaTeT). Inner-zone icy Saturnian; outer member of the 4:2 Mimas-Tethys resonance. Sidereal day = orbital period = 1.888 days."
sol_saturn_tethys_time_to_jd     = _moon_time_to_jd_response("tethys",     "SSaTeT")
sol_saturn_tethys_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Tethys."

jd_to_sol_saturn_dione_time      = _moon_time_response("dione",      _SATURNIAN_PARENT, "SSaDiT", "Sol Saturn-Dione Time")
jd_to_sol_saturn_dione_time.__doc__ = "JD (TDB) → Sol Saturn-Dione Time (SSaDiT). Outer member of the 2:1 Enceladus-Dione resonance. Sidereal day = orbital period = 2.737 days."
sol_saturn_dione_time_to_jd      = _moon_time_to_jd_response("dione",      "SSaDiT")
sol_saturn_dione_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Dione."

jd_to_sol_saturn_rhea_time       = _moon_time_response("rhea",       _SATURNIAN_PARENT, "SSaRhT", "Sol Saturn-Rhea Time")
jd_to_sol_saturn_rhea_time.__doc__ = "JD (TDB) → Sol Saturn-Rhea Time (SSaRhT). Second-largest Saturnian; not in any major resonance. Sidereal day = orbital period = 4.518 days."
sol_saturn_rhea_time_to_jd       = _moon_time_to_jd_response("rhea",       "SSaRhT")
sol_saturn_rhea_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Rhea."

jd_to_sol_saturn_titan_time      = _moon_time_response("titan",      _SATURNIAN_PARENT, "SSaTiT", "Sol Saturn-Titan Time")
jd_to_sol_saturn_titan_time.__doc__ = "JD (TDB) → Sol Saturn-Titan Time (SSaTiT). Largest Saturnian (second-largest moon in the solar system); thick N₂/methane atmosphere; outer member of the 4:3 Titan-Hyperion resonance. Sidereal day = orbital period = 15.945 days."
sol_saturn_titan_time_to_jd      = _moon_time_to_jd_response("titan",      "SSaTiT")
sol_saturn_titan_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Titan."

jd_to_sol_saturn_hyperion_time   = _moon_time_response("hyperion",   _SATURNIAN_PARENT, "SSaHyT", "Sol Saturn-Hyperion Time")
jd_to_sol_saturn_hyperion_time.__doc__ = "JD (TDB) → Sol Saturn-Hyperion Time (SSaHyT). Chaotically rotating Saturnian (the only known major moon NOT in tidal lock — but the 'sidereal_period_days' field still references the orbital period; rotation phase is non-trivially decoupled, an open research direction). Inner member of the 4:3 Titan-Hyperion resonance. Orbital period = 21.277 days."
sol_saturn_hyperion_time_to_jd   = _moon_time_to_jd_response("hyperion",   "SSaHyT")
sol_saturn_hyperion_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Hyperion (orbital period; rotation chaotic)."

jd_to_sol_saturn_iapetus_time    = _moon_time_response("iapetus",    _SATURNIAN_PARENT, "SSaIaT", "Sol Saturn-Iapetus Time")
jd_to_sol_saturn_iapetus_time.__doc__ = "JD (TDB) → Sol Saturn-Iapetus Time (SSaIaT). Outermost classical Saturnian; famous two-tone albedo. Sidereal day = orbital period = 79.322 days."
sol_saturn_iapetus_time_to_jd    = _moon_time_to_jd_response("iapetus",    "SSaIaT")
sol_saturn_iapetus_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Iapetus."

jd_to_sol_saturn_phoebe_time     = _moon_time_response("phoebe",     _SATURNIAN_PARENT, "SSaPhT", "Sol Saturn-Phoebe Time")
jd_to_sol_saturn_phoebe_time.__doc__ = "JD (TDB) → Sol Saturn-Phoebe Time (SSaPhT). Retrograde irregular Saturnian (captured Centaur). Long orbit — sidereal-cycle count moves slowly. Sidereal day = orbital period = 550.565 days."
sol_saturn_phoebe_time_to_jd     = _moon_time_to_jd_response("phoebe",     "SSaPhT")
sol_saturn_phoebe_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Phoebe."

jd_to_sol_saturn_janus_time      = _moon_time_response("janus",      _SATURNIAN_PARENT, "SSaJaT", "Sol Saturn-Janus Time")
jd_to_sol_saturn_janus_time.__doc__ = "JD (TDB) → Sol Saturn-Janus Time (SSaJaT). Co-orbital with Epimetheus (~4-year horseshoe-orbit swap). Sidereal day = orbital period = 0.695 days."
sol_saturn_janus_time_to_jd      = _moon_time_to_jd_response("janus",      "SSaJaT")
sol_saturn_janus_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Janus."

jd_to_sol_saturn_epimetheus_time = _moon_time_response("epimetheus", _SATURNIAN_PARENT, "SSaEpT", "Sol Saturn-Epimetheus Time")
jd_to_sol_saturn_epimetheus_time.__doc__ = "JD (TDB) → Sol Saturn-Epimetheus Time (SSaEpT). Co-orbital with Janus (~4-year horseshoe-orbit swap). Sidereal day = orbital period = 0.694 days."
sol_saturn_epimetheus_time_to_jd = _moon_time_to_jd_response("epimetheus", "SSaEpT")
sol_saturn_epimetheus_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Epimetheus."


# ──────────────────────────────────────────────────────────────────────
# v0.14.2 Sol Moon Times — Martians, Jovian inner regulars,
#                          Uranian (Titania), Neptunian (Triton)
# ──────────────────────────────────────────────────────────────────────
#
# Eight more moons across four parent families, integrated from four
# parallel subagent worktrees. All tidally locked, J2000-anchored.
#
# Naming + abbreviations (continuing the v0.14.1 6-letter convention):
#
#   Family               | Abbrev  | Sol Time name
#   ---------------------|---------|----------------------------------
#   Mars / Phobos        | SMaPhT  | Sol Mars-Phobos Time
#   Mars / Deimos        | SMaDeT  | Sol Mars-Deimos Time
#   Jupiter / Metis      | SJuMeT  | Sol Jupiter-Metis Time
#   Jupiter / Adrastea   | SJuAdT  | Sol Jupiter-Adrastea Time
#   Jupiter / Amalthea   | SJuAmT  | Sol Jupiter-Amalthea Time
#   Jupiter / Thebe      | SJuThT  | Sol Jupiter-Thebe Time
#   Uranus / Titania     | SUrTiT  | Sol Uranus-Titania Time
#   Neptune / Triton     | SNeTrT  | Sol Neptune-Triton Time
#
# Notable physical context (in test prose, not in dicts):
#   - Phobos sidereal period (0.319 d) is SHORTER than Mars's solar
#     day, so from Mars's surface Phobos rises in the WEST.
#   - Phobos / Deimos are likely captured asteroids (C/D-type spectra).
#   - Metis + Adrastea are ring-shepherd moons of Jupiter's main ring.
#   - Amalthea is the largest Jovian inner regular (84 km) and the only
#     one discovered before Voyager (Barnard 1892).
#   - Triton orbits RETROGRADE (only large moon to do so; captured
#     Kuiper Belt object); tidally decaying — will form a ring system
#     in ~3.6 Gyr when it crosses Neptune's Roche limit.
#   - SUrTiT (Titania) and SSaTiT (Saturn's Titan) share the `Ti`
#     moon-letter pair but are globally distinct via the parent prefix
#     (`Ur` vs `Sa`) — exactly the disambiguation the v0.14.1 6-letter
#     policy was designed to provide.
# ──────────────────────────────────────────────────────────────────────

# ── Mars (Phobos, Deimos) — likely captured asteroids
jd_to_sol_mars_phobos_time = _moon_time_response("phobos", _MARTIAN_PARENT, "SMaPhT", "Sol Mars-Phobos Time")
jd_to_sol_mars_phobos_time.__doc__ = "JD (TDB) → Sol Mars-Phobos Time (SMaPhT). Inner Martian moon — likely a captured asteroid (C/D-type spectral match). Sidereal period (0.319 days = 7h 39m) is SHORTER than Mars's solar day, so from Mars's surface Phobos rises in the west. Tidally locked: sidereal day = orbital period = rotation period = 0.319 days."
sol_mars_phobos_time_to_jd = _moon_time_to_jd_response("phobos", "SMaPhT")
sol_mars_phobos_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Phobos."

jd_to_sol_mars_deimos_time = _moon_time_response("deimos", _MARTIAN_PARENT, "SMaDeT", "Sol Mars-Deimos Time")
jd_to_sol_mars_deimos_time.__doc__ = "JD (TDB) → Sol Mars-Deimos Time (SMaDeT). Outer Martian moon — likely a captured asteroid (C/D-type spectral match), companion to Phobos. NOT in mean-motion resonance with Phobos (period ratio ≈ 3.96, near-but-not-locked 4:1). Tidally locked: sidereal day = orbital period = rotation period = 1.262 days."
sol_mars_deimos_time_to_jd = _moon_time_to_jd_response("deimos", "SMaDeT")
sol_mars_deimos_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Deimos."

# ── Jupiter inner regulars (Metis, Adrastea, Amalthea, Thebe)
jd_to_sol_jupiter_metis_time = _moon_time_response("metis", _GALILEAN_PARENT, "SJuMeT", "Sol Jupiter-Metis Time")
jd_to_sol_jupiter_metis_time.__doc__ = "JD (TDB) → Sol Jupiter-Metis Time (SJuMeT). Innermost known Jovian moon; ring-shepherd of Jupiter's main ring (with Adrastea). Tidally locked: sidereal day = orbital period = 0.295 days ≈ 7.07 h. Discovered in Voyager 2 imagery (1979)."
sol_jupiter_metis_time_to_jd = _moon_time_to_jd_response("metis", "SJuMeT")
sol_jupiter_metis_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Metis."

jd_to_sol_jupiter_adrastea_time = _moon_time_response("adrastea", _GALILEAN_PARENT, "SJuAdT", "Sol Jupiter-Adrastea Time")
jd_to_sol_jupiter_adrastea_time.__doc__ = "JD (TDB) → Sol Jupiter-Adrastea Time (SJuAdT). Second ring-shepherd of Jupiter's main ring (with Metis); orbits fractionally outside Metis but still just outside the ring's outer edge. Smallest Jovian inner regular by mean radius (~8 km). Tidally locked: 0.298 days ≈ 7.16 h. Discovered in Voyager 2 imagery (1979)."
sol_jupiter_adrastea_time_to_jd = _moon_time_to_jd_response("adrastea", "SJuAdT")
sol_jupiter_adrastea_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Adrastea."

jd_to_sol_jupiter_amalthea_time = _moon_time_response("amalthea", _GALILEAN_PARENT, "SJuAmT", "Sol Jupiter-Amalthea Time")
jd_to_sol_jupiter_amalthea_time.__doc__ = "JD (TDB) → Sol Jupiter-Amalthea Time (SJuAmT). Largest Jovian inner regular (radius ~84 km); distinctly reddish color (the most coloured of the small Jovian moons). The only Jovian inner regular discovered before the Voyager era — E. E. Barnard 1892, the last solar-system moon discovered by direct visual observation. Tidally locked: sidereal day = orbital period = 0.498 days ≈ 11.96 h."
sol_jupiter_amalthea_time_to_jd = _moon_time_to_jd_response("amalthea", "SJuAmT")
sol_jupiter_amalthea_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Amalthea."

jd_to_sol_jupiter_thebe_time = _moon_time_response("thebe", _GALILEAN_PARENT, "SJuThT", "Sol Jupiter-Thebe Time")
jd_to_sol_jupiter_thebe_time.__doc__ = "JD (TDB) → Sol Jupiter-Thebe Time (SJuThT). Outermost Jovian inner regular; orbits between Amalthea and Io. Tidally locked: sidereal day = orbital period = 0.675 days ≈ 16.19 h. Discovered in Voyager 1 imagery (S. Synnott, 1979)."
sol_jupiter_thebe_time_to_jd = _moon_time_to_jd_response("thebe", "SJuThT")
sol_jupiter_thebe_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Thebe."

# ── Uranus (Titania)
jd_to_sol_uranus_titania_time = _moon_time_response("titania", _URANIAN_PARENT, "SUrTiT", "Sol Uranus-Titania Time")
jd_to_sol_uranus_titania_time.__doc__ = "JD (TDB) → Sol Uranus-Titania Time (SUrTiT). Largest moon of Uranus (radius ~789 km); discovered by William Herschel 1787. Currently the only Uranian moon in BODIES; Oberon, Umbriel, Ariel, Miranda are queued for a future ship. Tidally locked: sidereal day = orbital period = 8.706 days. NOTE: SUrTiT and SSaTiT (Saturn's Titan) share the `Ti` moon prefix but are globally distinct via the parent prefix (`Ur` vs `Sa`) — exactly the disambiguation the v0.14.1 6-letter policy was designed to provide."
sol_uranus_titania_time_to_jd = _moon_time_to_jd_response("titania", "SUrTiT")
sol_uranus_titania_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Titania."

# ── Neptune (Triton)
jd_to_sol_neptune_triton_time = _moon_time_response("triton", _NEPTUNIAN_PARENT, "SNeTrT", "Sol Neptune-Triton Time")
jd_to_sol_neptune_triton_time.__doc__ = """JD (TDB) → Sol Neptune-Triton Time (SNeTrT).

Largest Neptunian moon (radius ~1353 km — bigger than Pluto). The only large
moon in the solar system that orbits its planet RETROGRADE — strong evidence
Triton is a captured Kuiper Belt object, not a primordial Neptunian moon.

Because of the retrograde orbit, Triton experiences tidal *deceleration* (not
acceleration like prograde moons), so it's spiraling INWARD toward Neptune;
in ~3.6 Gyr it will cross Neptune's Roche limit and be torn apart into a
ring system.

Active geology — Voyager 2 (1989) observed nitrogen geysers; surface
temperature ~-235°C (one of the coldest in the solar system).

Tidally locked: sidereal day = orbital period = 5.877 days. Encoder
convention: BODIES["triton"].period_days is positive (we encode omega =
+2π/P for ALL bodies regardless of prograde/retrograde direction; the
retrograde nature is metadata, not a sign flip in the time-scale primitive)."""
sol_neptune_triton_time_to_jd = _moon_time_to_jd_response("triton", "SNeTrT")
sol_neptune_triton_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Triton (orbits retrograde; period encoded positive per encoder convention)."

# ── v0.15.0 — Remaining Uranian moons (Miranda, Ariel, Umbriel, Oberon)
# Titania already lives above; the four below complete the major-Uranian
# roster. Discovery order: Titania + Oberon (Herschel 1787) → Ariel +
# Umbriel (Lassell 1851) → Miranda (Kuiper 1948). All five orbit in the
# Uranian equatorial plane, which sits ~98° from the ecliptic because
# Uranus is tipped sideways; the encoder convention (omega = +2π/P
# regardless of orbital orientation) carries through unchanged.
jd_to_sol_uranus_miranda_time = _moon_time_response("miranda", _URANIAN_PARENT, "SUrMiT", "Sol Uranus-Miranda Time")
jd_to_sol_uranus_miranda_time.__doc__ = """JD (TDB) → Sol Uranus-Miranda Time (SUrMiT).

Smallest of Uranus's five major moons (radius ~236 km). Discovered by
Gerard Kuiper in 1948 -- the only one of the five not discovered in the
1700s-1800s. Surface is the most geologically chaotic in the system:
Voyager 2 (1986) imaged 20 km cliffs (Verona Rupes, the tallest known
in the solar system) and ridge-and-groove terrain ("coronae") that
suggest a violent collisional past. Tidally locked.

Sidereal period = 1.413 d. Sol abbreviation SUrMiT distinguishes from
Saturn's Mimas (SSaMiT) under the v0.14.1 6-letter policy."""
sol_uranus_miranda_time_to_jd = _moon_time_to_jd_response("miranda", "SUrMiT")
sol_uranus_miranda_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Miranda."

jd_to_sol_uranus_ariel_time = _moon_time_response("ariel", _URANIAN_PARENT, "SUrArT", "Sol Uranus-Ariel Time")
jd_to_sol_uranus_ariel_time.__doc__ = """JD (TDB) → Sol Uranus-Ariel Time (SUrArT).

Innermost of the four classical Uranian moons (radius ~579 km).
Discovered by William Lassell, 1851. Brightest of the Uranian moons
(highest albedo). Surface shows extensive rift valleys; possible
cryovolcanic resurfacing. Tidally locked.

Sidereal period = 2.520 d."""
sol_uranus_ariel_time_to_jd = _moon_time_to_jd_response("ariel", "SUrArT")
sol_uranus_ariel_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Ariel."

jd_to_sol_uranus_umbriel_time = _moon_time_response("umbriel", _URANIAN_PARENT, "SUrUmT", "Sol Uranus-Umbriel Time")
jd_to_sol_uranus_umbriel_time.__doc__ = """JD (TDB) → Sol Uranus-Umbriel Time (SUrUmT).

Second of the four classical Uranian moons (radius ~585 km), discovered
by William Lassell, 1851 (same night as Ariel). Darkest surface of the
Uranian moons (lowest albedo) -- composition similar to a primordial
ice/rock mix without the cryovolcanic refresh of Ariel. Tidally locked.

Sidereal period = 4.144 d."""
sol_uranus_umbriel_time_to_jd = _moon_time_to_jd_response("umbriel", "SUrUmT")
sol_uranus_umbriel_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Umbriel."

jd_to_sol_uranus_oberon_time = _moon_time_response("oberon", _URANIAN_PARENT, "SUrObT", "Sol Uranus-Oberon Time")
jd_to_sol_uranus_oberon_time.__doc__ = """JD (TDB) → Sol Uranus-Oberon Time (SUrObT).

Outermost (and second-largest) of Uranus's classical moons (radius ~761
km). Discovered by William Herschel, 1787 -- same night as Titania.
Heavily cratered surface with darker patches inside crater floors that
may be cryovolcanic deposits. Tidally locked.

Sidereal period = 13.463 d -- the longest of the major-Uranian roster."""
sol_uranus_oberon_time_to_jd = _moon_time_to_jd_response("oberon", "SUrObT")
sol_uranus_oberon_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Oberon."

# ── v0.15.0 — Pluto (Charon)
jd_to_sol_pluto_charon_time = _moon_time_response("charon", _PLUTONIAN_PARENT, "SPlChT", "Sol Pluto-Charon Time")
jd_to_sol_pluto_charon_time.__doc__ = """JD (TDB) → Sol Pluto-Charon Time (SPlChT).

Pluto's largest moon. Discovered by Jim Christy, 1978. Mutually tidally
locked with Pluto -- both bodies show the same face to each other
forever, the only such 1:1:1 spin-orbit lock in the solar system. The
mass ratio (Charon:Pluto ≈ 0.12) is the highest of any moon-planet
pair; the Pluto-Charon barycentre lies OUTSIDE Pluto, which makes the
pair more like a *binary planet* than a planet-with-moon. New Horizons
(2015) imaged Charon's "Mordor Macula" north-polar reddish region (an
organic tholin deposit) and a vast equatorial canyon system.

Sidereal period = mutual rotation period = 6.387 d (the synchronous
spin-orbit lock collapses these into a single timescale)."""
sol_pluto_charon_time_to_jd = _moon_time_to_jd_response("charon", "SPlChT")
sol_pluto_charon_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Charon (mutually tidally locked with Pluto; sidereal period = mutual rotation period)."

# ── v0.16.0 Tier-1 BODIES expansion (43 → 52) ────────────────────────
#
# Saturnian Lagrange trojans (4): Telesto + Calypso ride at Tethys's
# L4 + L5; Helene + Polydeuces ride at Dione's L4 + L5. Each shares
# its host moon's sidereal period EXACTLY (1:1 mean-motion lock at
# the L4/L5 fixed points of the Saturn-host CR3BP), giving the
# body-graph Laplacian a multiplicity-2 degeneracy at the host's
# frequency. The natural intersection point with v0.16.x's
# resonance-graph multi-leg find_itn_chains.

jd_to_sol_saturn_telesto_time = _moon_time_response("telesto", _SATURNIAN_PARENT, "SSaTeT2", "Sol Saturn-Telesto Time")
jd_to_sol_saturn_telesto_time.__doc__ = """JD (TDB) → Sol Saturn-Telesto Time.

Tethys L4 trojan. Discovered Smith / Reitsema / Larson / Fountain 1980.
Period 1.88780216 d -- IDENTICAL to Tethys's. The first L4 entry in
BODIES; the body-graph Laplacian acquires a multiplicity-2 eigenvalue
at the Tethys frequency 2π/1.88780216 d⁻¹.

NOTE on abbreviation: SSaTeT collides with the v0.14.1-shipped Tethys
abbreviation (SSaTeT). The trojan therefore takes the suffixed form
**SSaTeT2** to distinguish them; this is the first invocation of the
suffix-disambiguation policy reserved in v0.14.1's roadmap for cases
where two moons of the SAME parent share their first-two-letters
(here: Tethys vs Telesto, both 'Te'). The suffix '2' marks the L4
trojan; Calypso (L5) gets SSaTeT3 by the same rule."""
sol_saturn_telesto_time_to_jd = _moon_time_to_jd_response("telesto", "SSaTeT2")
sol_saturn_telesto_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Telesto (Tethys L4 trojan; period locked to Tethys's)."

jd_to_sol_saturn_calypso_time = _moon_time_response("calypso", _SATURNIAN_PARENT, "SSaCaT", "Sol Saturn-Calypso Time")
jd_to_sol_saturn_calypso_time.__doc__ = """JD (TDB) → Sol Saturn-Calypso Time (SSaCaT).

Tethys L5 trojan. Discovered Pascu / Seidelmann / Baum / Currie 1980.
Period 1.88780216 d -- IDENTICAL to Tethys's and Telesto's. Forms an
L4/L5 pair with Telesto.

Mass ~10⁻¹² Earth (radius ~9.6 km, irregular shape); the trojan slot
is a Lagrange-point identity, not a mass argument. The Laplacian
multiplicity-2 degeneracy at the Tethys frequency is the spectral
content the trojan slot earns."""
sol_saturn_calypso_time_to_jd = _moon_time_to_jd_response("calypso", "SSaCaT")
sol_saturn_calypso_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Calypso (Tethys L5 trojan; period locked to Tethys's)."

jd_to_sol_saturn_helene_time = _moon_time_response("helene", _SATURNIAN_PARENT, "SSaHeT", "Sol Saturn-Helene Time")
jd_to_sol_saturn_helene_time.__doc__ = """JD (TDB) → Sol Saturn-Helene Time (SSaHeT).

Dione L4 trojan. Discovered Laques / Lecacheux 1980 (visually from the
Pic du Midi during a Saturn ring-plane crossing). Period 2.73691500 d
-- IDENTICAL to Dione's. Cassini (2010) close flyby imaged a heavily
regolith-coated surface with curious "downhill"-streaming patterns.

Largest of the four Saturnian trojans (radius ~17.5 km, mass ~2e-12
Earth)."""
sol_saturn_helene_time_to_jd = _moon_time_to_jd_response("helene", "SSaHeT")
sol_saturn_helene_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Helene (Dione L4 trojan; period locked to Dione's)."

jd_to_sol_saturn_polydeuces_time = _moon_time_response("polydeuces", _SATURNIAN_PARENT, "SSaPoT", "Sol Saturn-Polydeuces Time")
jd_to_sol_saturn_polydeuces_time.__doc__ = """JD (TDB) → Sol Saturn-Polydeuces Time (SSaPoT).

Dione L5 trojan. Discovered Murray et al. 2004 (Cassini imagery).
Period 2.73691500 d -- IDENTICAL to Dione's and Helene's. Forms an
L4/L5 pair with Helene.

Smallest body in the v0.16.0 ship (radius ~1.3 km, mass ~4e-15
Earth) -- a "moonlet" by most categorisations -- but the Lagrange-
point identity earns the slot regardless of mass. Notable for
having an unusually wide libration amplitude around L5 (~32°),
suggesting a relatively recent capture or perturbation event."""
sol_saturn_polydeuces_time_to_jd = _moon_time_to_jd_response("polydeuces", "SSaPoT")
sol_saturn_polydeuces_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Polydeuces (Dione L5 trojan; period locked to Dione's; wide libration amplitude ~32°)."

# Jovian irregular moons (3) — Himalia (largest prograde) + Pasiphae /
# Sinope (the second retrograde marker beyond Triton).
jd_to_sol_jupiter_himalia_time = _moon_time_response("himalia", _GALILEAN_PARENT, "SJuHiT", "Sol Jupiter-Himalia Time")
jd_to_sol_jupiter_himalia_time.__doc__ = """JD (TDB) → Sol Jupiter-Himalia Time (SJuHiT).

Largest Jovian irregular moon (radius ~85 km). Discovered C. D. Perrine
1904. Period 250.566 d -- prograde, sits cleanly between Callisto
(16.7 d) and the long-period retrograde captures Pasiphae/Sinope
(743 / 759 d). Eponym of the Himalia group of irregular Jovian
satellites (Lysithea, Elara, Leda, Dia all share similar orbital
characteristics, suggesting common-progenitor capture).

Mass ~1.1e-9 Earth -- a real spectral contributor to the Jovian
sub-graph, distinct from the dust-grain class of the inner regulars."""
sol_jupiter_himalia_time_to_jd = _moon_time_to_jd_response("himalia", "SJuHiT")
sol_jupiter_himalia_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Himalia (largest Jovian prograde irregular)."

jd_to_sol_jupiter_pasiphae_time = _moon_time_response("pasiphae", _GALILEAN_PARENT, "SJuPaT", "Sol Jupiter-Pasiphae Time")
jd_to_sol_jupiter_pasiphae_time.__doc__ = """JD (TDB) → Sol Jupiter-Pasiphae Time (SJuPaT).

Jovian retrograde irregular. Discovered P. J. Melotte 1908. Period
743.63 d, RETROGRADE -- inclination ~141°, deep into retrograde
territory. Eponym of the Pasiphae group of retrograde captures
(Sinope, Carpo, Sponde, Megaclite, etc., all sharing similar
near-resonant orbital characteristics that suggest fragmentation
of a common progenitor body).

Encoder convention: BODIES['pasiphae'].period_days is positive (we
encode omega = +2π/P for ALL bodies regardless of orbital direction;
retrograde-ness is metadata, not a sign flip in the time-scale
primitive). Same convention as Triton (v0.14.2) and Sol Uranian
Time (v0.5.4)."""
sol_jupiter_pasiphae_time_to_jd = _moon_time_to_jd_response("pasiphae", "SJuPaT")
sol_jupiter_pasiphae_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Pasiphae (Jovian retrograde irregular; period encoded positive per encoder convention)."

jd_to_sol_jupiter_sinope_time = _moon_time_response("sinope", _GALILEAN_PARENT, "SJuSiT", "Sol Jupiter-Sinope Time")
jd_to_sol_jupiter_sinope_time.__doc__ = """JD (TDB) → Sol Jupiter-Sinope Time (SJuSiT).

Jovian retrograde irregular. Discovered S. B. Nicholson 1914. Period
758.90 d, RETROGRADE -- inclination ~153°. Member of the Pasiphae
group; near-resonant with Pasiphae itself (orbital periods differ
by ~2%).

Encoder convention same as Pasiphae: positive period_days, retrograde
metadata-only."""
sol_jupiter_sinope_time_to_jd = _moon_time_to_jd_response("sinope", "SJuSiT")
sol_jupiter_sinope_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Sinope (Jovian retrograde irregular; period encoded positive per encoder convention)."

# Neptunian sub-graph completion (2) — Proteus + Nereid.
jd_to_sol_neptune_proteus_time = _moon_time_response("proteus", _NEPTUNIAN_PARENT, "SNePrT", "Sol Neptune-Proteus Time")
jd_to_sol_neptune_proteus_time.__doc__ = """JD (TDB) → Sol Neptune-Proteus Time (SNePrT).

Neptune's second-largest moon (radius ~210 km, near-spherical despite
sitting below the canonical hydrostatic-equilibrium threshold for icy
bodies). Discovered Voyager 2 imagery 1989. Period 1.122 d -- fills
the Neptune sub-graph between Triton (5.88 d) and the inner-Neptunian
close-packed cluster (Naiad / Thalassa / Despina / Galatea / Larissa,
all <0.6 d, all deferred to a future thematic shepherd-cluster ship).

Surface dominated by the giant Pharos crater (radius ~75 km, ~13× the
moon's radius -- a near-fatal impact); near-spherical shape suggests
a post-impact gravitational rebound."""
sol_neptune_proteus_time_to_jd = _moon_time_to_jd_response("proteus", "SNePrT")
sol_neptune_proteus_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Proteus (Neptune's second-largest moon)."

jd_to_sol_neptune_nereid_time = _moon_time_response("nereid", _NEPTUNIAN_PARENT, "SNeNeT", "Sol Neptune-Nereid Time")
jd_to_sol_neptune_nereid_time.__doc__ = """JD (TDB) → Sol Neptune-Nereid Time (SNeNeT).

Neptune's third-largest moon (radius ~170 km). Discovered G. P. Kuiper
1949. Period 360.13619 d -- almost exactly one terrestrial year (which
is a numerical coincidence, not a resonance). Eccentricity 0.749, the
HIGHEST of any major moon in the solar system -- ranges from 1.4 Gm
(perigee) to 9.7 Gm (apogee). Likely a captured asteroid or KBO whose
post-capture orbit has been pumped by chaotic libration with Triton.

Spectrally interesting because the 360-day period extends Neptune's
low-frequency tail dramatically -- before v0.16.0 the longest
Neptunian period was Triton's 5.88 d. SNeNeT is also the first Sol
Time wrapper whose name has a 'self-collision' (NeNe — Neptune's
Nereid); cute, not a problem (the suffix policy isn't triggered
because there's only one such moon)."""
sol_neptune_nereid_time_to_jd = _moon_time_to_jd_response("nereid", "SNeNeT")
sol_neptune_nereid_time_to_jd.__doc__ = "Inverse: sidereal-cycle count → JD (TDB) for Nereid (most eccentric major moon orbit, e=0.749)."


# ──────────────────────────────────────────────────────────────────────
# v0.11.0 Sol Proper Time (SPrT) — gravitational + kinematic time dilation
# ──────────────────────────────────────────────────────────────────────
#
# Per-body proper-time rate vs. TCB (barycentric coordinate time).
# Two leading-order components: surface gravitational dilation
# (GM/(R·c²)) and orbital kinematic dilation (v_orb²/(2c²)).
#
# The user-facing surface is exposed two ways:
#
#   1. Standalone `get_proper_time_rate(body, ...)` — returns the rate
#      directly, for queries like "how fast does a Mars-surface clock
#      tick relative to TCB."
#
#   2. The CLI `--proper` flag on every existing `time-*` subcommand —
#      transparently applies the body's proper-time correction to the
#      Sol Time count, attaching a `proper_time` block to the output.
#      "Same answer, but proper-time-corrected for this body."
#
# Validated against six published values (Earth GR, Sun GR, Mars GR,
# Pluto GR, Earth orbital kinematic, Mars-vs-Earth GR difference) to
# within 0.30 % — see `tests/test_sprt.py` and the Phase A audit
# script `research/proper_time_rates.py` for the validation discipline.

#: The `body` argument's accepted set — all 52 bodies in the roster.
_SPRT_BODY_KEYS = sorted(_BODIES)


def get_proper_time_rate(
    body: str,
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    jd_tdb: Optional[float] = None,
    reference: str = SPRT_DEFAULT_REFERENCE,
) -> Dict[str, Any]:
    """Compute the leading-order proper-time rate for a body vs. TCB.

    Wraps `_research.proper_time.get_proper_time_rate` with the bridge
    error-dict convention.

    Parameters
    ----------
    body : str
        A body key in `BODIES`.
    lat, lon : float, optional
        Surface latitude / longitude in degrees. v0.11.0 ignores these
        (J₂ oblateness is deferred to v0.12.0+); accepted for forward
        compatibility so callers can already write
        `get_proper_time_rate("terra", lat=51.5, lon=-0.1)` and have
        it pass through cleanly.
    jd_tdb : float, optional
        Julian Date in TDB. v0.11.0 uses each body's mean orbital
        velocity (no per-JD eccentricity correction); accepted for
        forward compatibility.
    reference : str, default ``"tcb"``
        Reference time scale. ``"tcb"`` and ``"tdb"`` accepted; produce
        the same numerical answer at v0.11.0 precision.

    Returns
    -------
    dict
        ``{"ok": True, "body": ..., "reference": "tcb",
            "rate_relative_to_reference": ...,
            "components": {gr_surface, kinematic_orbital, j2_oblateness, total},
            "orbital_velocity_kms": ..., "parent_body": ..., "abbreviation": "SPrT"}``.
        On error: ``{"ok": False, "error": "..."}``.
    """
    if not isinstance(body, str) or body not in _BODIES:
        return _err(
            f"body must be one of {_SPRT_BODY_KEYS}, got {body!r}"
        )
    if reference not in SPRT_SUPPORTED_REFERENCES:
        return _err(
            f"reference must be one of {list(SPRT_SUPPORTED_REFERENCES)}, "
            f"got {reference!r}"
        )
    rate = _get_proper_time_rate_impl(
        body, lat=lat, lon=lon, jd_tdb=jd_tdb, reference=reference,
    )
    out: Dict[str, Any] = {"ok": True, **rate.to_dict()}
    out["abbreviation"] = "SPrT"
    return out


def compare_proper_times(
    body_a: str,
    body_b: str,
    *,
    reference: str = SPRT_DEFAULT_REFERENCE,
) -> Dict[str, Any]:
    """Compare two bodies' proper-time rates against TCB.

    Returns the rate ratio plus a "drift per Earth-year" diagnostic —
    the most intuitive number for human comparison.

    Convention: positive `seconds_per_earth_year` means body_a's
    surface clocks tick *slower* than body_b's (consistent with TCB
    convention "more dilation = lower rate").
    """
    if body_a not in _BODIES:
        return _err(
            f"body_a must be one of {_SPRT_BODY_KEYS}, got {body_a!r}"
        )
    if body_b not in _BODIES:
        return _err(
            f"body_b must be one of {_SPRT_BODY_KEYS}, got {body_b!r}"
        )
    if reference not in SPRT_SUPPORTED_REFERENCES:
        return _err(
            f"reference must be one of {list(SPRT_SUPPORTED_REFERENCES)}, "
            f"got {reference!r}"
        )
    return {"ok": True, "abbreviation": "SPrT",
            **_compare_proper_times(body_a, body_b, reference=reference)}


# ──────────────────────────────────────────────────────────────────────
# v0.11.0 Sol Time `--proper` post-processor
# ──────────────────────────────────────────────────────────────────────
#
# Each Sol Time bridge function (`jd_to_sol_*_time`) returns a dict
# with one or more "count" fields (msd, lsd_solar, synodic_count, ...).
# When the CLI's `--proper` flag is set, the corresponding count fields
# get a `<field>_proper` sibling that's the count multiplied by the
# body's proper-time rate, plus a `proper_time` metadata block.
#
# This keeps the existing time-* bridge surface untouched (the
# `--proper` correction is purely additive at the CLI layer) and lets
# the user transparently opt into the GR + kinematic correction
# without learning a new function or subcommand. It's the "users
# don't even need to know anything extra had to happen in the back
# end" UX the user asked for.

#: Map from Sol Time CLI subcommand → (canonical body for SPrT, list of
#: count fields to apply the proper-time correction to).
_SPRT_COMMAND_MAP: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "time-mars":       ("mars",    ("msd",)),
    "time-lunar":      ("luna",    ("synodic_phase", "sidereal_phase")),
    "time-uranus":     ("uranus",  ("usd",)),
    "time-venus":      ("venus",   ("vsd_solar", "vsd_sidereal")),
    "time-mercury":    ("mercury", ("mer_sd_solar", "mer_sd_sidereal")),
    "time-pluto":      ("pluto",   ("psd",)),
    "time-sol":        ("sun",     ("crn",)),
    "time-jupiter":    ("jupiter", ("jsd",)),
    "time-saturn":     ("saturn",  ("ssd",)),
    "time-neptune":    ("neptune", ("nsd",)),
    "time-terra":      ("terra",   ("tsd_solar", "tsd_sidereal")),
    "time-luna":       ("luna",    ("lsd_solar", "lsd_sidereal")),
    "time-terra-luna": ("terra",   ("synodic_count", "saros_count", "metonic_count")),
}


def apply_proper_correction(
    result: Dict[str, Any],
    subcommand: str,
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    reference: str = SPRT_DEFAULT_REFERENCE,
) -> Dict[str, Any]:
    """Augment a Sol Time bridge result with proper-time-corrected counts.

    Used by the CLI when `--proper` is set. No-op (returns the input
    unchanged) if the result is an error response or if the subcommand
    isn't in the SPrT command map.
    """
    if not result.get("ok"):
        return result
    if subcommand not in _SPRT_COMMAND_MAP:
        return result
    body_key, count_fields = _SPRT_COMMAND_MAP[subcommand]
    rate_result = get_proper_time_rate(
        body_key, lat=lat, lon=lon, reference=reference,
    )
    if not rate_result.get("ok"):
        return result
    rate = rate_result["rate_relative_to_reference"]
    for field in count_fields:
        if field in result and isinstance(result[field], (int, float)):
            result[f"{field}_proper"] = float(result[field]) * rate
    result["proper_time"] = {
        "applied": True,
        "body": body_key,
        "rate_relative_to_reference": rate,
        "components": rate_result["components"],
        "reference": rate_result["reference"],
        "abbreviation": "SPrT",
        "note": (f"Proper-time correction for {body_key}: count_proper = "
                 f"count × {rate:.12g}. v0.11.0 captures GR surface + "
                 f"orbital kinematic; J₂ oblateness deferred."),
    }
    return result


# ──────────────────────────────────────────────────────────────────────
# v0.12.0 Sol Kinematics — per-body orbital state
# ──────────────────────────────────────────────────────────────────────
#
# Static encoding of orbital state — semi-major axis, mean orbital
# velocity, kinetic energy, angular momentum — for every body in the
# 38-body roster. Mirrors chess-spectral's `qm_2d.py` / `qm_4d.py`
# *kinematics* layer (static observables, no time-evolution).
#
# v0.12.0 implements the circular-orbit Kepler-mean approximation
# (same math as `proper_time.py` for SPrT's kinematic dilation term);
# eccentricity / inclination corrections ship as v0.12.x refinements.
# Per-JD evolution + force vectors + energy budgets are the v0.13.0
# *Dynamics* counterpart.
#
# Validation pinned by `tests/test_kinematics.py` against the same
# 9 published Solar-System values that the Phase A audit script
# (`research/kinematics_dynamics_audit.py`) verifies independently:
#
#   Mercury / Earth / Mars / Jupiter / Pluto orbital velocities
#   (within 1.1 / 0.02 / 0.25 / 0.08 / 0.02 % of NASA fact sheets)
#   Total system energy < 0 (system is bound)
#   Jupiter holds ~61% of total angular momentum
#   Outer planets hold ~99.84% of planetary angular momentum
#   Sun KE / Mc² < 1e-12 (Sun barely moves in barycentric frame)


def get_kinematic_state(
    body: str,
    *,
    jd_tdb: Optional[float] = None,
    frame: str = KINEMATICS_DEFAULT_FRAME,
) -> Dict[str, Any]:
    """Mean orbital kinematic state for one body.

    Parameters
    ----------
    body : str
        A body key in `BODIES` (e.g. ``"mars"``, ``"luna"``, ``"sun"``).
    jd_tdb : float, optional
        Julian Date in TDB. v0.12.0 ignores this (uses mean orbital
        elements; no per-JD eccentricity correction); accepted for
        forward compatibility.
    frame : str, default ``"heliocentric_ecliptic"``
        Reference frame. ``"heliocentric_ecliptic"`` and
        ``"parent_centric"`` accepted; both report the same orbital
        elements at v0.12.0 precision (the keyword reserves room for
        v0.12.x-style barycentric or J2000-ICRS frame switching).

    Returns
    -------
    dict
        ``{"ok": True, "body": ..., "frame": ..., "parent": ...,
            "mass_kg": ..., "semi_major_axis_au": ..., "orbital_velocity_km_s": ...,
            "orbital_period_days": ..., "kinetic_energy_j": ...,
            "angular_momentum_z_kg_m2_s": ..., "abbreviation": "Sol-K"}``.
        On error: ``{"ok": False, "error": "..."}``.

    For the Sun the orbital fields are zeroed and a `note` is set
    ("Body has period_days = 0 in BODIES table; ...") — the Sun's
    barycentric motion is dominated by Sun-Jupiter wobble (~12 m/s
    peak), two orders of magnitude below this approximation's noise
    floor.
    """
    if not isinstance(body, str) or body not in _BODIES:
        return _err(
            f"body must be one of {sorted(_BODIES)}, got {body!r}"
        )
    if frame not in KINEMATICS_SUPPORTED_FRAMES:
        return _err(
            f"frame must be one of {list(KINEMATICS_SUPPORTED_FRAMES)}, "
            f"got {frame!r}"
        )
    state = _get_kinematic_state_impl(body, jd_tdb=jd_tdb, frame=frame)
    out: Dict[str, Any] = {"ok": True, **state.to_dict()}
    out["abbreviation"] = "Sol-K"
    return out


def get_full_system_state(
    *,
    jd_tdb: Optional[float] = None,
    frame: str = KINEMATICS_DEFAULT_FRAME,
) -> Dict[str, Any]:
    """Kinematic state for every body in the 38-body roster.

    Returns
    -------
    dict
        ``{"ok": True, "frame": ..., "n_bodies": 38, "n_with_state": 37,
            "bodies": {body_key: KinematicState_dict, ...},
            "totals": {total_kinetic_energy_j, total_angular_momentum_z, ...},
            "abbreviation": "Sol-K"}``.

    The `totals` block aggregates the per-body computations into the
    Solar-System-level numbers used by the Phase A audit (Jupiter's
    fraction of total L; outer-planet fraction; system bound check
    requires the dynamics surface in v0.13.0 to add potential energy).
    """
    if frame not in KINEMATICS_SUPPORTED_FRAMES:
        return _err(
            f"frame must be one of {list(KINEMATICS_SUPPORTED_FRAMES)}, "
            f"got {frame!r}"
        )
    states = _get_full_system_state_impl(jd_tdb=jd_tdb, frame=frame)
    bodies_dict = {key: s.to_dict() for key, s in states.items()}
    # System-level aggregates
    n_with_state = sum(1 for s in states.values() if s.note is None)
    total_ke = sum(s.kinetic_energy_j for s in states.values() if s.note is None)
    total_lz = sum(s.angular_momentum_z_kg_m2_s for s in states.values() if s.note is None)
    # Planet vs. total split (the "Jupiter holds ~61%" headline)
    planet_lz = sum(
        s.angular_momentum_z_kg_m2_s
        for body_key, s in states.items()
        if s.note is None and _BODIES[body_key].category == "planet"
    )
    jupiter_lz = states["jupiter"].angular_momentum_z_kg_m2_s if "jupiter" in states else 0.0
    outer_lz = sum(
        states[k].angular_momentum_z_kg_m2_s
        for k in ("jupiter", "saturn", "uranus", "neptune")
        if k in states and states[k].note is None
    )
    return {
        "ok": True,
        "frame": frame,
        "n_bodies": len(_BODIES),
        "n_with_state": n_with_state,
        "abbreviation": "Sol-K",
        "totals": {
            "total_kinetic_energy_j": float(total_ke),
            "total_angular_momentum_z_kg_m2_s": float(total_lz),
            "planet_angular_momentum_z_kg_m2_s": float(planet_lz),
            "jupiter_angular_momentum_z_kg_m2_s": float(jupiter_lz),
            "outer_planets_angular_momentum_z_kg_m2_s": float(outer_lz),
            "fraction_in_planets":
                float(planet_lz / total_lz) if total_lz else 0.0,
            "fraction_in_jupiter":
                float(jupiter_lz / total_lz) if total_lz else 0.0,
            "fraction_in_outer_planets_of_planet_total":
                float(outer_lz / planet_lz) if planet_lz else 0.0,
        },
        "bodies": bodies_dict,
    }


# ──────────────────────────────────────────────────────────────────────
# v0.12.0 Sol Time `--state` post-processor
# ──────────────────────────────────────────────────────────────────────
#
# Each Sol Time bridge function (`jd_to_sol_*_time`) returns a dict
# describing *time*. The CLI's `--state` flag (analogous to v0.11.0's
# `--proper`) augments that with a `kinematic_state` block — same body
# the Sol Time refers to, its orbital state at the JD.
#
# Same canonical-body lookup as the SPrT post-processor; reuses the
# `_SPRT_COMMAND_MAP` body keys (Mars time → Mars; STLT → Terra,
# since STLT is observed-from-Terra; etc.).


def apply_state_correction(
    result: Dict[str, Any],
    subcommand: str,
    *,
    frame: str = KINEMATICS_DEFAULT_FRAME,
) -> Dict[str, Any]:
    """Augment a Sol Time bridge result with a `kinematic_state` block.

    Used by the CLI when `--state` is set on a `time-*` subcommand.
    No-op (returns input unchanged) on error responses or unknown
    subcommands. Mirrors `apply_proper_correction` for the SPrT
    `--proper` flag.
    """
    if not result.get("ok"):
        return result
    if subcommand not in _SPRT_COMMAND_MAP:
        return result
    body_key, _ = _SPRT_COMMAND_MAP[subcommand]
    state_result = get_kinematic_state(body_key, frame=frame)
    if not state_result.get("ok"):
        return result
    result["kinematic_state"] = {
        "applied": True,
        "body": body_key,
        "frame": frame,
        "abbreviation": "Sol-K",
        # Pull the headline numbers up to the top level of the block;
        # callers that just want "where is Mars right now" don't need
        # to drill into the nested dict.
        "orbital_velocity_km_s": state_result.get("orbital_velocity_km_s"),
        "semi_major_axis_au": state_result.get("semi_major_axis_au"),
        "kinetic_energy_j": state_result.get("kinetic_energy_j"),
        "angular_momentum_z_kg_m2_s": state_result.get("angular_momentum_z_kg_m2_s"),
        "note": (f"Mean orbital state for {body_key} (circular Kepler "
                 f"approximation; v0.12.0). Per-JD eccentricity "
                 f"corrections deferred to v0.12.x."),
    }
    return result


# ──────────────────────────────────────────────────────────────────────
# v0.13.0 Sol Dynamics — system energy, forces, evolution
# ──────────────────────────────────────────────────────────────────────
#
# The dynamics counterpart to v0.12.0's Sol Kinematics. Mirrors chess-
# spectral's `qm_*_dynamics.py` (Hamiltonian + evolution + force /
# energy queries) at the orbital-mechanics scale.
#
# Where Kinematics describes *what is* (positions, velocities,
# kinetic energies, angular momenta), Dynamics describes *what changes
# things* — potential energies, gravitational forces, the Hamiltonian
# (the existing Laplacian!), the time-evolution operator (the existing
# `bip_instrument.encode_state`).
#
# Validation pinned by `tests/test_dynamics.py` against the same audit
# numbers as Kinematics, plus dynamics-specific pins:
#
#   Total system energy < 0 (system is gravitationally bound)
#   Sun's KE / Mc² < 1e-12 (Sun barely moves)
#   Earth-Sun force = G M_sun M_earth / a_earth² ≈ 3.54×10²² N
#   Mars-Jupiter force at mean separation ≈ 1.2×10¹⁷ N


def get_dynamics(
    *,
    jd_tdb: Optional[float] = None,
    frame: str = KINEMATICS_DEFAULT_FRAME,
) -> Dict[str, Any]:
    """System-level dynamics aggregate at a JD.

    Returns kinetic + potential + total energies (system-bound check),
    angular-momentum partitions (Jupiter / outer-planets fractions),
    and Sun's barycentric KE fraction. v0.13.0 reuses the v0.12.0
    Kinematics machinery for the per-body states + adds the PE
    computation.
    """
    if frame not in KINEMATICS_SUPPORTED_FRAMES:
        return _err(
            f"frame must be one of {list(KINEMATICS_SUPPORTED_FRAMES)}, "
            f"got {frame!r}"
        )
    state = _get_dynamics_impl(jd_tdb=jd_tdb, frame=frame)
    out: Dict[str, Any] = {"ok": True, **state.to_dict()}
    out["abbreviation"] = "Sol-D"
    return out


def get_force_between(
    body_a: str,
    body_b: str,
    *,
    jd_tdb: Optional[float] = None,
    frame: str = KINEMATICS_DEFAULT_FRAME,
) -> Dict[str, Any]:
    """Newtonian gravitational force between two bodies.

    Returns the force *on body_a from body_b*. v0.13.0 reports
    magnitude only; 3D vectors deferred to v0.13.x.
    """
    if body_a not in _BODIES:
        return _err(
            f"body_a must be one of {sorted(_BODIES)}, got {body_a!r}"
        )
    if body_b not in _BODIES:
        return _err(
            f"body_b must be one of {sorted(_BODIES)}, got {body_b!r}"
        )
    if frame not in KINEMATICS_SUPPORTED_FRAMES:
        return _err(
            f"frame must be one of {list(KINEMATICS_SUPPORTED_FRAMES)}, "
            f"got {frame!r}"
        )
    contrib = _get_force_between_impl(
        body_a, body_b, jd_tdb=jd_tdb, frame=frame,
    )
    out: Dict[str, Any] = {"ok": True, **contrib.to_dict()}
    out["abbreviation"] = "Sol-D"
    return out


def get_body_energies(
    body: str,
    *,
    jd_tdb: Optional[float] = None,
    frame: str = KINEMATICS_DEFAULT_FRAME,
) -> Dict[str, Any]:
    """Per-body kinetic + potential + total energy budget."""
    if body not in _BODIES:
        return _err(
            f"body must be one of {sorted(_BODIES)}, got {body!r}"
        )
    if frame not in KINEMATICS_SUPPORTED_FRAMES:
        return _err(
            f"frame must be one of {list(KINEMATICS_SUPPORTED_FRAMES)}, "
            f"got {frame!r}"
        )
    energies = _get_body_energies_impl(body, jd_tdb=jd_tdb, frame=frame)
    out: Dict[str, Any] = {"ok": True, **energies.to_dict()}
    out["abbreviation"] = "Sol-D"
    return out


# ──────────────────────────────────────────────────────────────────────
# v0.13.0 Sol Time `--dynamics` post-processor
# ──────────────────────────────────────────────────────────────────────


def apply_dynamics_correction(
    result: Dict[str, Any],
    subcommand: str,
    *,
    frame: str = KINEMATICS_DEFAULT_FRAME,
) -> Dict[str, Any]:
    """Augment a Sol Time bridge result with a `dynamics` block.

    Used by the CLI when `--dynamics` is set on a `time-*` subcommand.
    No-op on error responses or unknown subcommands. Mirrors
    `apply_state_correction` for the v0.12.0 `--state` flag and
    `apply_proper_correction` for the v0.11.0 `--proper` flag.
    """
    if not result.get("ok"):
        return result
    if subcommand not in _SPRT_COMMAND_MAP:
        return result
    body_key, _ = _SPRT_COMMAND_MAP[subcommand]
    energies = get_body_energies(body_key, frame=frame)
    if not energies.get("ok"):
        return result
    result["dynamics"] = {
        "applied": True,
        "body": body_key,
        "frame": frame,
        "abbreviation": "Sol-D",
        "kinetic_energy_j": energies.get("kinetic_energy_j"),
        "potential_energy_j": energies.get("potential_energy_j"),
        "total_energy_j": energies.get("total_energy_j"),
        "is_bound": (
            energies.get("total_energy_j") is not None
            and energies.get("total_energy_j") < 0
        ),
        "note": (f"Energy budget for {body_key} (circular Kepler PE; "
                 f"v0.13.0). 3D forces and time-evolution operator "
                 f"deferred to v0.13.x."),
    }
    return result


# ──────────────────────────────────────────────────────────────────────
# v0.8.x — ITN pathway / Lagrange-tube query (find-tubes)
# ──────────────────────────────────────────────────────────────────────


def find_itn_pathways(jd_lo: float,
                      jd_hi: float,
                      *,
                      departure: str,
                      target: str,
                      threshold: float = 0.02,
                      max_candidates: int = 1000,
                      backend: str = "auto") -> Dict[str, Any]:
    """Enumerate Hohmann transfer windows between two bodies.

    First-cut implementation of the ITN pathway query — mirrors
    v0.3.1's ``find-syzygies`` discipline. Closed-form synodic-
    period enumeration anchored at the Hohmann launch geometry
    (target leads departure by ``π − n_target × T_hohmann`` for
    outer transfers, or trails by the same magnitude for inner
    transfers). Each candidate carries a transfer-time + Δv
    estimate.

    The Hohmann window is the lowest-effort transfer between two
    bodies and the natural first ITN target. Future extensions
    will layer ``backend="c"`` (ABI bump) and additional
    ``transfer_kind`` values for low-energy / heteroclinic-tube
    candidates as the CR3BP manifold computation lands.

    Parameters
    ----------
    jd_lo, jd_hi : float
        Window boundaries in JD (TDB).
    departure, target : str
        Body names. Both must orbit the Sun (planet, dwarf-planet,
        or asteroid).
    threshold : float, default 0.02
        Score cutoff in (0, 1]. ``score = |phase_residual| / π``.
        0.02 → tight window (~3.6° of ideal Hohmann phase angle).
        0.05 → wider (~9°).
    max_candidates : int, default 1000
        Safety cap.
    backend : {"auto", "bip", "c"}, default "auto"
        Forward-compatibility hook. v0.8.x ships only the Python
        impl (``"bip"``); the ``"c"`` path will land in a follow-up
        version with ABI bump. ``"auto"`` selects the available
        path; today that means ``"bip"`` either way.

    Returns
    -------
    dict
        ``{"ok": True, "jd_lo": ..., "jd_hi": ..., "departure": ...,
        "target": ..., "threshold": ..., "n_candidates": int,
        "candidates": [{"jd_tdb", "transfer_kind", "transfer_time_days",
        "launch_phase_angle_deg", "actual_phase_angle_deg",
        "phase_residual_deg", "score", "estimated_dv_kms",
        "synodic_period_days", "gateway_lp"}, ...],
        "backend": "bip"}``.
    """
    for v in (_validate_jd(jd_lo), _validate_jd(jd_hi),
              _validate_body(departure), _validate_body(target)):
        if v is not None:
            return v
    # backend is forward-compatibility only in v0.8.1 — accept any of
    # {"auto", "bip", "c"} and dispatch to "bip" (the only impl).
    if backend not in ("auto", "bip", "c"):
        return _err(
            f"backend must be 'auto'/'bip'/'c', got {backend!r}"
        )
    if departure.lower() == target.lower():
        return _err("departure and target must differ")
    try:
        f_threshold = float(threshold)
    except (TypeError, ValueError):
        return _err(
            f"threshold must be a number, got {type(threshold).__name__}"
        )
    if not (0.0 < f_threshold <= 1.0):
        return _err(f"threshold must be in (0, 1], got {f_threshold}")
    # backend dispatch — v0.8.x only ships the BIP path; "auto"/"c"
    # both fall back to the Python impl. The C twin will land in a
    # follow-up minor with the standard bridge dispatch pattern.
    chosen = "bip"
    try:
        candidates = _find_itn_pathways_impl(
            float(jd_lo), float(jd_hi),
            departure=departure.lower(),
            target=target.lower(),
            threshold=f_threshold,
            max_candidates=int(max_candidates),
        )
    except (ValueError, RuntimeError) as exc:
        return _err(str(exc))
    return {
        "ok": True,
        "jd_lo": float(jd_lo),
        "jd_hi": float(jd_hi),
        "departure": departure.lower(),
        "target": target.lower(),
        "threshold": f_threshold,
        "n_candidates": len(candidates),
        "candidates": [c.to_dict() for c in candidates],
        "backend": chosen,
    }


# ──────────────────────────────────────────────────────────────────────
# v0.17.0 — multi-leg ITN chain search (find_itn_chains)
# ──────────────────────────────────────────────────────────────────────


def find_itn_chains(jd_lo: float,
                    jd_hi: float,
                    *,
                    departure: str,
                    target: str,
                    intermediates: Optional[List[str]] = None,
                    max_legs: int = 4,
                    dv_budget_kms: float = 30.0,
                    tof_budget_days: float = 365.25 * 20.0,
                    threshold: float = 0.05,
                    max_chains: int = 200,
                    max_intermediate_windows: int = 8,
                    backend: str = "auto") -> Dict[str, Any]:
    """Multi-leg ITN chain search via Dijkstra-style graph search on
    the (body, epoch) state space. Each leg is a closed-form Hohmann
    window from :func:`find_itn_pathways`; legs stitch end-to-end at
    intermediate bodies. The cumulative Δv and time-of-flight are
    budget-bounded; the search emits chains in optimal-Δv-first order.

    The advanced Lagrange-highway extension that the v0.8.1
    ``find_itn_pathways`` first-cut left room for. Stays in the
    integer-ALU + FPU pipeline discipline (no CR3BP integrator). Each
    leg carries a small-integer (p, q) gear-ratio "resonance
    signature" -- the cross-pollination point with the BIP cyclic-
    group encoder.

    Parameters
    ----------
    jd_lo, jd_hi : float
        Search window [jd_lo, jd_hi] in JD (TDB).
    departure, target : str
        Body names. Both must orbit the Sun.
    intermediates : Optional[List[str]]
        Bodies allowed as intermediate stops. None = all heliocentric
        bodies in BODIES (planets + dwarf planets + asteroids), minus
        ``departure`` and ``target``. Pass ``[]`` to force a single-
        leg direct chain.
    max_legs : int, default 4
        Hard cap on legs per chain.
    dv_budget_kms : float, default 30.0
        Cumulative-Δv ceiling.
    tof_budget_days : float, default 7305.0 (20 yr)
        Cumulative time-of-flight ceiling.
    threshold : float, default 0.05
        Per-leg phase-residual cutoff (passed to find_itn_pathways).
    max_chains : int, default 200
        Cap on total chains returned.
    max_intermediate_windows : int, default 8
        Per-(body, epoch) cap on enumerated next-leg windows.
    backend : {"auto", "bip", "c"}, default "auto"
        Forward-compatibility hook. v0.17.0 ships only the Python impl.

    Returns
    -------
    dict
        ``{"ok": True, "jd_lo": ..., "jd_hi": ..., "departure": ...,
        "target": ..., "n_chains": int,
        "chains": [{"jd_tdb_launch", "jd_tdb_arrival", "legs": [...],
        "total_dv_kms", "total_tof_days", "resonance_signature": [[p, q], ...],
        "score"}, ...], "backend": "bip"}``.
    """
    for v in (_validate_jd(jd_lo), _validate_jd(jd_hi),
              _validate_body(departure), _validate_body(target)):
        if v is not None:
            return v
    if backend not in ("auto", "bip", "c"):
        return _err(f"backend must be 'auto'/'bip'/'c', got {backend!r}")
    if departure.lower() == target.lower():
        return _err("departure and target must differ")

    if intermediates is not None:
        try:
            intermediates_clean = [str(b).lower() for b in intermediates]
        except (TypeError, ValueError):
            return _err("intermediates must be an iterable of body-name strings")
    else:
        intermediates_clean = None

    try:
        f_threshold = float(threshold)
        i_max_legs = int(max_legs)
        f_dv_budget = float(dv_budget_kms)
        f_tof_budget = float(tof_budget_days)
        i_max_chains = int(max_chains)
        i_max_windows = int(max_intermediate_windows)
    except (TypeError, ValueError):
        return _err("numeric parameter has wrong type")

    if not (0.0 < f_threshold <= 1.0):
        return _err(f"threshold must be in (0, 1], got {f_threshold}")
    if i_max_legs < 1:
        return _err(f"max_legs must be ≥ 1, got {i_max_legs}")
    if f_dv_budget <= 0.0:
        return _err(f"dv_budget_kms must be > 0, got {f_dv_budget}")
    if f_tof_budget <= 0.0:
        return _err(f"tof_budget_days must be > 0, got {f_tof_budget}")

    chosen = "bip"
    try:
        chains = _find_itn_chains_impl(
            float(jd_lo), float(jd_hi),
            departure=departure.lower(),
            target=target.lower(),
            intermediates=intermediates_clean,
            max_legs=i_max_legs,
            dv_budget_kms=f_dv_budget,
            tof_budget_days=f_tof_budget,
            threshold=f_threshold,
            max_chains=i_max_chains,
            max_intermediate_windows=i_max_windows,
        )
    except (ValueError, RuntimeError) as exc:
        return _err(str(exc))

    return {
        "ok": True,
        "jd_lo": float(jd_lo),
        "jd_hi": float(jd_hi),
        "departure": departure.lower(),
        "target": target.lower(),
        "max_legs": i_max_legs,
        "dv_budget_kms": f_dv_budget,
        "tof_budget_days": f_tof_budget,
        "threshold": f_threshold,
        "n_chains": len(chains),
        "chains": [c.to_dict() for c in chains],
        "backend": chosen,
    }


# ──────────────────────────────────────────────────────────────────────
# v0.18.0 — Body Architecture (resonance-weighted gateway-graph
# Laplacian Fiedler partition; inner/outer system classification)
# ──────────────────────────────────────────────────────────────────────


def body_architecture(target: Optional[str] = None) -> Dict[str, Any]:
    """Inner/outer architectural classification of heliocentric bodies.

    Computes the Fiedler partition of the resonance-weighted gateway-
    graph Laplacian on the v0.16.0 13-body heliocentric Tier-1 roster
    (planets + main-belt asteroids; Sun excluded; moons excluded).
    The partition cleanly bipartitions the roster on the asteroid-belt
    boundary: outer 5 = jupiter / saturn / uranus / neptune / pluto;
    inner 8 = mercury / venus / terra / mars / vesta / ceres / pallas
    / hygiea.

    The classification is the v0.17.x research output (notebook §13.8)
    promoted to a stable ship surface. The cyclic-group encoder
    discovers the canonical inner/outer system division without being
    told it exists — Pluto and Neptune share the deepest negative
    Fiedler entry via their well-known 2:3 mean-motion lock.

    Parameters
    ----------
    target : str, optional. If given, return just the named body's
        record (lower-cased; must be in the heliocentric roster); else
        return the full partition.

    Returns
    -------
    dict
        Full partition (target=None):
            ``{"ok": True, "n_bodies": 13, "lambda_2": float,
              "bodies": [{name, class, fiedler_value, period_days}, ...],
              "partitions": {"inner": [...], "outer": [...]}}``
        Single-body (target=name):
            ``{"ok": True, "name": "...", "class": "inner"|"outer",
              "fiedler_value": float, "period_days": float,
              "lambda_2": float}``
        On error:
            ``{"ok": False, "error": "..."}``

    Notes
    -----
    Pure-Python; no ABI dependency. The Fiedler-vector sign is anchored
    to the shortest-period body (positive ⇒ inner) so the class labels
    are reproducible across platforms regardless of LAPACK pivoting.

    Reference: notebook §13.8 (the resonance-weighting research) and
    §13.9 (the hybrid follow-up that motivated shipping the resonance-
    only partition as the architectural surface, while deferring the
    hybrid-Fiedler-distance Δv predictor to v0.18.x or later).
    """
    try:
        result = _compute_body_architecture_impl()
    except (ValueError, RuntimeError) as exc:
        return {"ok": False, "error": str(exc)}

    if target is None:
        return result

    name = str(target).lower()
    for record in result["bodies"]:
        if record["name"] == name:
            return {
                "ok": True,
                "name": record["name"],
                "class": record["class"],
                "fiedler_value": record["fiedler_value"],
                "period_days": record["period_days"],
                "lambda_2": result["lambda_2"],
            }
    return {
        "ok": False,
        "error": (
            f"unknown body {target!r}; valid names are "
            f"{list(_BODY_ARCH_DEFAULT)}"
        ),
    }


# ──────────────────────────────────────────────────────────────────────
# v0.18.1 — predict_itn_accessibility (closed-form spectral Δv estimate
# from the §13.9 hybrid-Fiedler-distance regression)
# ──────────────────────────────────────────────────────────────────────


def predict_itn_accessibility(
    departure: str,
    target: str,
) -> Dict[str, Any]:
    """Predict the minimum cumulative Δv for a multi-leg ITN chain
    between two heliocentric bodies — closed-form spectral estimate.

    Promoted from the v0.17.x research output (notebook §13.9): the
    hybrid ``inv_dv × resonance`` gateway-graph Laplacian's Fiedler
    distance achieves Spearman ρ = +0.857 against empirical Δv from
    v0.17.0 ``find_itn_chains``. This bridge surface wraps the
    calibrated linear regression of that Fiedler distance against
    ground-truth Δv (slope ≈ 15.62 km/s per Fiedler-unit, intercept
    ≈ 8.68 km/s; LOOCV MAE ≈ 4.24 km/s on the v0.16.0 13-body
    heliocentric Tier-1 roster).

    Use case: **fast first-pass triage** before calling the costly
    Dijkstra in :func:`find_itn_chains`. The predictor runs in
    microseconds (one eigh on a 13×13 symmetric matrix at module
    load, then O(1) lookup per query); ``find_itn_chains`` runs in
    ~1.5 s per pair.

    **Do not use for trajectory design** — the absolute MAE is ~4
    km/s on a 2–28 km/s domain, useful for ranking pairs but too
    coarse for mission-budget purposes. Mission design should call
    ``find_itn_chains`` for the full Dijkstra answer.

    Parameters
    ----------
    departure, target : str
        Body names from the v0.16.0 13-body heliocentric Tier-1
        roster (planets + main-belt asteroids; case-insensitive).
        Both must be in the roster; both must differ.

    Returns
    -------
    dict
        ``{"ok": True, "departure": str, "target": str,
        "fiedler_distance": float, "predicted_dv_kms": float,
        "calibration": {...}}``

        On error: ``{"ok": False, "error": "..."}``.

    Notes
    -----
    The calibration is window-specific (50 yr at J2000, max_legs=3,
    dv_budget=30 km/s, threshold=0.1) — see ``research/calibrate_
    predict_itn_accessibility.py`` for re-calibration against
    different windows. The hybrid Fiedler vector is computed once
    at module import time and memoised; no per-query cost beyond
    a dict lookup.

    Reference: notebook §13.9 + §14 (the holographic-principle
    framing of this regression as the bulk-boundary correspondence's
    real empirical payload).
    """
    return _predict_itn_accessibility_impl(departure, target)


# ──────────────────────────────────────────────────────────────────────
# v0.19.0 — Sol Electromagnetic Instrument
# ──────────────────────────────────────────────────────────────────────


def get_em_state(jd_tdb: float) -> Dict[str, Any]:
    """Per-body EM state at the requested JD.

    Promotes the v0.19.0 architectural commitment from research notebook
    §16.9 to a stable ship surface. Returns rotation phase + intrinsic
    dipole moment + synchrotron power + plasma source rate + photoelectric
    potential per body, advanced from EM_REFERENCE_JD = J2000.0.

    The Sol Electromagnetic Instrument is a **state-at-epoch query
    surface**, not a BIP encoder — the §16.3 / §16.9.1 rhythm-mismatch
    finding established that EM clocks (rotational, Carrington, solar
    cycle, plume duty cycle, secular Yarkovsky) don't form a low-order
    rational lattice with each other or with orbital periods, so the
    cyclic-group encoder discipline doesn't transplant.

    Roster: 16 bodies (sun + 7 magnetised + 4 induced + 4 unmagnetised) —
    strict subset of the v0.16.0 52-body celestial roster, picked for
    significant EM observables.

    See research notebook §16 for the architectural scoping.
    """
    return _compute_em_state_at_jd_impl(jd_tdb)


def list_em_couplings() -> Dict[str, Any]:
    """Static catalog of significant pairwise EM couplings.

    Returns 7 entries: Jupiter-Io flux tube (10¹² W, dominant);
    Saturn-Enceladus plasma mass loading; Saturn-Titan induced
    magnetosphere; Sun-Earth IMF reconnection; Jupiter-Europa /
    Jupiter-Ganymede (induced + intrinsic-field-to-intrinsic-field);
    Sun-asteroid-belt radiation pressure (scoping anchor).

    Each entry carries a `source_key` pointing into the
    `_research.em_instrument_data.SOURCES` citation dict.
    """
    return _list_em_couplings_impl()


def em_architecture(target: Optional[str] = None) -> Dict[str, Any]:
    """Magnetised / induced / unmagnetised classification of EM-roster
    bodies.

    Different partition than the v0.18.0 inner/outer split from
    `bridge.body_architecture` — that one classifies by orbital
    position via the resonance Fiedler partition; this one classifies
    by intrinsic-field presence (lookup, not eigendecomposition).

    Parameters
    ----------
    target : str, optional. If given, return just that body's record;
        else return the full partition.

    Returns
    -------
    dict
        Full partition (target=None): `{ok, n_bodies, bodies, partitions}`
        with `partitions = {"magnetised": [...], "induced": [...],
        "unmagnetised": [...], "star": [...]}`.
        Single-body (target=name): per-body record + class.
    """
    return _compute_em_architecture_impl(target=target)


# ──────────────────────────────────────────────────────────────────────
# v0.20.0 — Sol Geodetic Catalog
# ──────────────────────────────────────────────────────────────────────


def get_geodetic_state(body: Optional[str] = None) -> Dict[str, Any]:
    """Per-body geodetic state — gravity + topography + interior records.

    Promotes the v0.20.0 architectural commitment from research notebook
    §17.1 + §17.4.2 to a stable ship surface, mirroring the v0.19.0 Sol
    Electromagnetic Instrument pattern. **This is not a BIP encoder
    running on geodetic rhythms** — solid-body geodetic observables are
    static parameters with no native rhythm (per §17.4.1 the rhythm-
    mismatch finding generalises across solid-body geodesy alongside
    magnetic multipoles and fluid-envelope channels). The cyclic-group
    encoder discipline does not transplant.

    Returns three internal channels per body:

    * gravity — multipole expansion (full spherical-harmonic Stokes
      coefficients for terrestrial bodies + the Moon; zonal-only J_n
      series for the gas + ice giants).
    * topography — DEM / shape-model metadata (full-coverage DEMs for
      the inner solar system + the Moon; partial-coverage SARTopo for
      Titan; polyhedral shape models for the small-body roster).
    * interior — radial density profiles, layered models,
      moment-of-inertia constraints (PREM / GRAIL+Apollo / InSight /
      JRM33-companion / Cassini Grand Finale ring-seismology /
      Voyager-derived for the ice giants).

    Parameters
    ----------
    body : str, optional. If given, return just that body's records;
        else return the full per-body catalog.

    Returns
    -------
    dict
        Single body (body=name): `{ok, body, gravity, topography, interior}`
        with each channel either a record dict or None for sparse coverage.
        Full roster (body=None): `{ok, n_bodies, bodies}` with bodies a
        dict keyed by body name.

    See research notebook §17 for the architectural scoping.
    """
    return _compute_geodetic_state_impl(body=body)


def list_geodetic_models() -> Dict[str, Any]:
    """Static enumeration of the full Sol Geodetic Catalog.

    Returns every model in every channel — gravity multipole expansions,
    topography / shape models, interior structure models — across the
    full body roster. Each entry carries a `source_key` pointing into
    the `_research.geodetic_catalog_data.SOURCES` citation dict so users
    can verify the provenance of every numeric value.
    """
    return _list_geodetic_models_impl()


def geodetic_architecture(target: Optional[str] = None) -> Dict[str, Any]:
    """Per-body data-quality-tier partition over the Sol Geodetic Catalog.

    Per the §17.1.6 ship-readiness convention, each body lands in a
    HIGH / MEDIUM / LOW / NONE tier based on the median precision flag
    across its three channels (gravity / topography / interior). A body
    with HIGH gravity but LOW interior is summarised as MEDIUM.

    This is a different partition than the v0.18.0 inner/outer split
    from `bridge.body_architecture` (which classifies by orbital
    position via the resonance Fiedler partition) and the v0.19.0
    magnetised/induced/unmagnetised split from `bridge.em_architecture`
    (which classifies by intrinsic-field presence). The geodetic
    partition classifies by **published-data quality**, not by physical
    body class.

    Parameters
    ----------
    target : str, optional. If given, return just that body's tier and
        per-channel flags; else return the full partition.

    Returns
    -------
    dict
        Full partition (target=None):
            `{ok, n_bodies, partitions, bodies}` with
            `partitions = {"HIGH": [...], "MEDIUM": [...], "LOW": [...],
            "NONE": [...]}`.
        Single body (target=name):
            `{ok, body, tier, channel_flags}`.
    """
    return _compute_geodetic_architecture_impl(target=target)


# ──────────────────────────────────────────────────────────────────────
# v0.20.1 — Sol Magnetic Multipole Catalog
# ──────────────────────────────────────────────────────────────────────


def get_magnetic_multipoles(
    body: Optional[str] = None,
    crustal: bool = False,
) -> Dict[str, Any]:
    """Per-body internal-field spherical-harmonic expansion.

    Promotes the v0.20.1 architectural commitment from research notebook
    §17.2 + §17.4.2 to a stable ship surface, mirroring the v0.19.0 EM
    Instrument and v0.20.0 Sol Geodetic Catalog patterns. Schmidt
    quasi-normalised g_n^m / h_n^m coefficients (geomagnetic
    convention) for the published per-body internal-field roster:
    Earth IGRF-13 (deg 13), Jupiter JRM33 (deg 18), Saturn Cao 2020
    (deg 14, axisymmetric), Mercury Thébault 2018 (deg 5, offset
    dipole), Uranus Holme & Bloxham 1996 AH5 (deg 3, Voyager-only),
    Neptune Holme & Bloxham 1996 O8 (deg 3, Voyager-only), Ganymede
    Kivelson 2002 (dipole-only — the only solar-system moon with a
    confirmed intrinsic dipole).

    The Sol Magnetic Multipole Catalog is a **state-lookup query
    surface**, not a BIP encoder — per §17.4.1 the rhythm-mismatch
    finding generalises across magnetic multipoles alongside solid-
    body geodesy and fluid-envelope channels: internal-field Schmidt
    coefficients are static at their epoch (IGRF main field updates
    every 5 years on a published schedule; JRM33 is a Juno-prime-
    mission snapshot; Voyager-derived AH5/O8 are single-flyby fits).
    The cyclic-group encoder discipline does not transplant.

    Parameters
    ----------
    body : str, optional. If given, return just that body's record;
        else return the full per-body catalog.
    crustal : bool, default False. If True and the requested body has
        a crustal field model on file (Earth EMM2017 only), the
        crustal record is included alongside the main-field record.

    Returns
    -------
    dict
        Single body (`body=name`):
            ``{"ok": True, "body": str, "main_field": {...} or None,
              "crustal_field": {...} or None}``
        Full roster (`body=None`):
            ``{"ok": True, "n_bodies": int, "bodies": {name: {...}}}``

    See research notebook §17.2 for the architectural scoping and
    §17.4.2 for the v0.20.1 ship sequence.
    """
    return _compute_magnetic_multipoles_impl(body=body, crustal=crustal)


def evaluate_magnetic_field(
    body: str,
    r_km: float,
    lat_deg: float,
    lon_deg: float,
    jd_tdb: Optional[float] = None,
) -> Dict[str, Any]:
    """Evaluate the vector magnetic field at (r, lat, lon).

    Closed-form Schmidt-quasi-normalised dipole synthesis from the
    per-body multipole expansion. Returns spherical components
    (B_r, B_θ, B_φ) and total magnitude in nT.

    The v0.20.1 ship surface returns the dipole approximation
    (synthesis_degree=1), which is the dominant contribution beyond
    a few body-radii for every body in the roster. Higher-degree
    synthesis is left for a future minor version — the dipole-only
    surface ships now per the §17.4.2 full-coverage commitment.

    Parameters
    ----------
    body : str. Lower-case body name (must be in the multipole roster).
    r_km : float. Radial distance from body centre, km. Must be > 0.
    lat_deg : float. Geocentric latitude, degrees, [-90, 90].
    lon_deg : float. Body-fixed longitude, degrees.
    jd_tdb : float, optional. Reserved for forward compatibility
        (secular variation handling in a future minor version).

    Returns
    -------
    dict
        ``{"ok": True, "body": str, "B_r_nT": float, "B_theta_nT": float,
          "B_phi_nT": float, "B_total_nT": float, "epoch_year": float,
          "synthesis_degree": int, "below_surface": bool}``
    """
    return _evaluate_magnetic_field_impl(
        body=body, r_km=r_km, lat_deg=lat_deg, lon_deg=lon_deg, jd_tdb=jd_tdb,
    )


def get_solar_synoptic_state(
    jd_tdb: Optional[float] = None,
) -> Dict[str, Any]:
    """Sun synoptic-state pointer surface.

    The Sun's internal field is time-varying with a ~22-yr Hale cycle
    modulated by the ~11-yr sunspot cycle; a single static set of
    Schmidt coefficients is not the right representation. The package
    therefore ships a pointer into the published synoptic-magnetogram
    archive (Stanford HMI / Wilcox Solar Observatory) so consumers
    can pull the correct Carrington-rotation-cadence field for a
    specific JD outside the package itself.

    Parameters
    ----------
    jd_tdb : float, optional. If given, the response includes
        coverage-status triage relative to each archive's start year.

    Returns
    -------
    dict
        ``{"ok": True, "body": "sun", "n_archives": int,
          "archives": [...], (optional) "jd_tdb", "year_at_jd",
          "coverage_status": "in_coverage" | "before_archive" | "future"}``
    """
    return _compute_solar_synoptic_state_impl(jd_tdb=jd_tdb)


def list_magnetic_multipoles() -> Dict[str, Any]:
    """Static enumeration of the full Sol Magnetic Multipole Catalog.

    Returns every published main-field multipole model + every
    crustal-field model + every solar synoptic reference. Each entry
    carries a `source_key` pointing into the
    `_research.magnetic_multipole_catalog_data.SOURCES` citation dict
    so users can verify the provenance of every numeric value.
    """
    return _list_magnetic_multipoles_impl()


def magnetic_architecture(target: Optional[str] = None) -> Dict[str, Any]:
    """Per-body data-quality-tier partition over the Sol Magnetic
    Multipole Catalog.

    Each body lands in HIGH / MEDIUM / LOW / NONE based on its
    main-field `precision_flag`. Voyager-only models (Uranus, Neptune)
    are LOW; current-best models (Earth IGRF-13, Jupiter JRM33,
    Saturn Cao 2020) are HIGH; single-mission limited-coverage models
    (Mercury Thébault 2018, Ganymede Kivelson 2002 dipole-only) are
    MEDIUM. Bodies with a published crustal anomaly model carry a
    `has_crustal` flag (Earth EMM2017 only in v0.20.1).

    This is a different partition than v0.20.0's `geodetic_architecture`
    (which classifies by gravity / topography / interior data quality)
    — this one tracks the magnetic channel specifically. Bodies that
    appear in both partitions may land in different tiers (e.g.,
    Mars is HIGH-tier geodetic but absent from the magnetic roster
    entirely because Mars has no significant intrinsic global dipole;
    its crustal magnetic anomalies are a candidate for a future minor).

    Parameters
    ----------
    target : str, optional. If given, return just that body's tier;
        else return the full partition.
    """
    return _compute_magnetic_architecture_impl(target=target)


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
    # Resolve backend="auto" before _validate_backend, matching the v0.9.2
    # fix for get_breathing_modulation. SUPPORTED_BACKENDS is the
    # concrete-backend roster; "auto" is the CLI-friendly sentinel that
    # picks the best available concrete backend at call time.
    from ephemerides_spectral import _native_bip
    if backend == "auto":
        backend = "c" if _native_bip.HAS_NATIVE else "bip"
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
        moon_idx = inst_bip.body_to_idx["luna"]
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
    # Resolve "auto" before validation: SUPPORTED_BACKENDS is the
    # concrete-backend roster ({"bip", "complex128", "c"}), and "auto"
    # is a CLI-friendly sentinel that picks the best available concrete
    # backend at call time. Doing the resolution first lets us reuse
    # _validate_backend without polluting it with the sentinel.
    from ephemerides_spectral import _native_bip
    if backend == "auto":
        backend = "c" if _native_bip.HAS_NATIVE else "bip"
    for v in (_validate_jd(jd_tdb), _validate_body(a), _validate_body(b),
              _validate_kernel(kernel), _validate_backend(backend)):
        if v: return v
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
