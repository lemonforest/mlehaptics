"""Animation export — time-series HDC state over a date range."""

from __future__ import annotations

import json
import math
from io import BytesIO
from typing import Any, Dict, List

import numpy as np

from antikythera_spectral._research.encode_ant import (
    D_CALLIPPIC,
    D_PACKING,
    encode_ant_callippic,
    encode_ant_packing,
)


def encode_range(jd_lo: float, jd_hi: float, *,
                  step_days: float = 1.0,
                  D: int = D_CALLIPPIC) -> Dict[str, Any]:
    """Time-series of states over [jd_lo, jd_hi].

    Returns a compact dict ``{"jds": [...], "states_interleaved_f32":
    [[...], ...]}`` where each inner list is a 2*D-length real+imag
    interleaved Float32 state.
    """
    if jd_hi <= jd_lo:
        raise ValueError("jd_hi must be greater than jd_lo")
    if step_days <= 0:
        raise ValueError("step_days must be > 0")
    if D == D_CALLIPPIC:
        encode = encode_ant_callippic
    elif D == D_PACKING:
        encode = encode_ant_packing
    else:
        raise ValueError(f"D must be 940 or 13440, got {D}")

    n_steps = int(math.ceil((jd_hi - jd_lo) / step_days)) + 1
    jds: List[float] = []
    states: List[List[float]] = []
    for i in range(n_steps):
        jd = jd_lo + i * step_days
        if jd > jd_hi:
            break
        s = encode(jd)
        # interleave
        flat = np.empty(2 * s.size, dtype=np.float32)
        flat[0::2] = s.real.astype(np.float32, copy=False)
        flat[1::2] = s.imag.astype(np.float32, copy=False)
        jds.append(jd)
        states.append(flat.tolist())
    return {
        "D": int(D),
        "n_frames": len(jds),
        "jds": jds,
        "states_interleaved_f32": states,
    }


def export_animation(jd_lo: float, jd_hi: float, step_days: float, *,
                      format: str = "json", D: int = D_CALLIPPIC) -> bytes:
    """Render the time-series as bytes in the chosen format.

    Formats:
      - "json": UTF-8 encoded JSON (compact)
      - "npz":  numpy .npz with arrays {jds, states_real, states_imag}
    """
    series = encode_range(jd_lo, jd_hi, step_days=step_days, D=D)
    if format == "json":
        return json.dumps(series, separators=(",", ":")).encode("utf-8")
    if format == "npz":
        # Reshape interleaved Float32 list back to complex per-frame.
        states_arr = np.asarray(series["states_interleaved_f32"], dtype=np.float32)
        n_frames = states_arr.shape[0]
        D_out = states_arr.shape[1] // 2
        real = states_arr[:, 0::2]
        imag = states_arr[:, 1::2]
        buf = BytesIO()
        np.savez_compressed(
            buf,
            jds=np.asarray(series["jds"], dtype=np.float64),
            states_real=real,
            states_imag=imag,
            D=np.array([D_out]),
        )
        return buf.getvalue()
    raise ValueError(f"format must be 'json' or 'npz', got {format!r}")


__all__ = ["encode_range", "export_animation"]
