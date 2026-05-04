"""Bridge API for ephemerides-spectral.

Provides a Pyodide-friendly JSON API for encoding the solar system state,
binding observer views, and detecting syzygies.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np
from ephemerides_spectral._research.ephemeris_reference_instrument import EphemerisHDCInstrument, REFERENCE_JD

_INSTRUMENT_CACHE: Optional[EphemerisHDCInstrument] = None

def _get_instrument() -> EphemerisHDCInstrument:
    global _INSTRUMENT_CACHE
    if _INSTRUMENT_CACHE is None:
        _INSTRUMENT_CACHE = EphemerisHDCInstrument()
    return _INSTRUMENT_CACHE

def _interleave_complex(state: np.ndarray) -> List[float]:
    out = np.empty(2 * state.size, dtype=np.float32)
    out[0::2] = state.real.astype(np.float32, copy=False)
    out[1::2] = state.imag.astype(np.float32, copy=False)
    return out.tolist()

def get_system_state(jd_tdb: float, force_high_res: bool = False) -> Dict[str, Any]:
    """Encode the barycentric state of the Sol Star System."""
    try:
        global _INSTRUMENT_CACHE
        if _INSTRUMENT_CACHE is None or force_high_res:
            _INSTRUMENT_CACHE = EphemerisHDCInstrument(force_high_res=force_high_res)
        state = _INSTRUMENT_CACHE.encode_state(jd_tdb)
        return {
            "ok": True,
            "jd_tdb": float(jd_tdb),
            "state_interleaved_f32": _interleave_complex(state),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

def get_resolution(body: str = "earth") -> Dict[str, Any]:
    """Get temporal resolution (seconds per residue shift) for a body."""
    try:
        instrument = _get_instrument()
        res = instrument.get_body_temporal_resolution(body)
        return {
            "ok": True,
            "body": body,
            "seconds_per_residue": float(res),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

def get_local_view(jd_tdb: float, body: str, lat: float, lon: float) -> Dict[str, Any]:
    """Encode the topocentric view from a specific body and geographic position."""
    try:
        instrument = _get_instrument()
        sys_state = instrument.encode_state(jd_tdb)
        local_state = instrument.bind_observer(sys_state, body, lat, lon)
        return {
            "ok": True,
            "jd_tdb": float(jd_tdb),
            "body": body,
            "lat": float(lat),
            "lon": float(lon),
            "state_interleaved_f32": _interleave_complex(local_state),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

def get_eclipse_probability(jd_tdb: float) -> Dict[str, Any]:
    """Detect syzygy probability at a chosen JD."""
    try:
        instrument = _get_instrument()
        state = instrument.encode_state(jd_tdb)
        prob = instrument.get_eclipse_probability(state)
        return {
            "ok": True,
            "jd_tdb": float(jd_tdb),
            "probability": float(prob),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

__all__ = ["get_system_state", "get_local_view", "get_eclipse_probability"]
