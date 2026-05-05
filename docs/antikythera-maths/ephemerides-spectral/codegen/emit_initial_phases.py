"""Codegen: emit ``_data/initial_phases.json`` from the BIP instrument.

The C codegen (``c/codegen/emit_c_tables.py``) bakes the calibrated
initial phases at REFERENCE_JD = J2000.0 into ``es_initial_phases[]``
in ``c/src/es_laplacian.c`` — that's why ``backend="c"`` doesn't
need SPICE at runtime.

The Python BIP encoder used to calibrate at runtime, which silently
fell back to zero phases when no SPICE kernel was staged. This
codegen step closes that gap: the Python wheel ships the same
calibrated phases as a JSON in ``_data/initial_phases.json``, and
``EphemerisBIPInstrument`` loads them as the canonical source.

Result: ``pip install ephemerides-spectral`` works out of the box,
no SPICE staging required for either backend, and Python BIP is
byte-identical to native C at every JD by construction.

Run from ``regenerate.py``; this module is also importable for
inspection.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict

from _paths import DATA_DIR, RESEARCH_ROOT, ensure_research_importable

ensure_research_importable()

from research.bip_instrument import (  # noqa: E402
    EphemerisBIPInstrument,
    REFERENCE_JD,
)


def emit(kernel: str = "de441") -> Path:
    """Calibrate initial phases via the BIP instrument and emit JSON.

    Tries the requested kernel first (default ``de441``, the
    high-resolution kernel). Falls back to ``de421`` if the high-res
    kernel isn't staged on the codegen machine — for the body roster
    this project carries, ``de421`` and ``de441`` agree on calibrated
    initial phases to within Q-format ULP.

    Returns the path of the written JSON.
    """
    inst = EphemerisBIPInstrument(D=4096, kernel=kernel)
    if inst.bundle is None:
        # The instrument's __init__ falls back to de421 when de441
        # isn't on disk. If even de421 isn't there the calibration
        # would zero-out — that's a hard error at codegen time.
        raise RuntimeError(
            "no SPICE kernel could be loaded; codegen needs at least "
            "skyfield_data/de421.bsp staged at the project root."
        )

    sorted_names = list(inst.body_names)
    phases = {
        name: int(inst.initial_phases_int[i])
        for i, name in enumerate(sorted_names)
    }
    omegas = {
        name: int(inst.omega_diag[i])
        for i, name in enumerate(sorted_names)
    }

    payload = {
        "package": "ephemerides-spectral",
        "reference_jd": REFERENCE_JD,
        "kernel_used_for_calibration": getattr(inst, "kernel", kernel),
        "n_bodies": len(sorted_names),
        "body_names": sorted_names,
        "initial_phases": phases,
        "omega_diag_residues_per_day": omegas,
        "notes": (
            "Calibrated at REFERENCE_JD using the listed JPL DE-kernel. "
            "Used by EphemerisBIPInstrument as the canonical initial-"
            "phase source — eliminates the need for SPICE staging at "
            "runtime. The C codegen bakes the same values into "
            "es_initial_phases[]; this JSON IS the SSOT for the BIP "
            "side."
        ),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "initial_phases.json"
    out.write_bytes(
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    return out


if __name__ == "__main__":
    path = emit()
    print(f"wrote {path}")
