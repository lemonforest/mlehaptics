"""Copy curated research/ modules into de441_spectral/_research/ for shipping."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from _paths import RESEARCH_ROOT

_RESEARCH_DST: Path = (
    Path(__file__).resolve().parents[1]
    / "python"
    / "ephemerides_spectral"
    / "_research"
)

_INCLUDED_MODULES: List[str] = [
    "__init__.py",
    "ephemeris_reference_instrument.py",
    "ephemeris_loader.py",
    "bodies.py",
    "laplacian.py",
    "bip_instrument.py",
    "time_scales.py",
    "syzygy_window.py",
    "diagnosed_fibers.py",
    "portable_prng.py",
    "bip_hd_lift.py",
    "itn_window.py",
    "proper_time.py",
    "kinematics.py",
    "dynamics.py",
    "body_architecture.py",
    "predict_itn_accessibility.py",
    "em_instrument_data.py",
    "em_instrument.py",
    "geodetic_catalog_data.py",
    "geodetic_catalog.py",
    "magnetic_multipole_catalog_data.py",
    "magnetic_multipole_catalog.py",
]

def emit() -> List[Path]:
    if _RESEARCH_DST.exists():
        shutil.rmtree(_RESEARCH_DST)
    _RESEARCH_DST.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []
    src_root = RESEARCH_ROOT / "research"
    for name in _INCLUDED_MODULES:
        src = src_root / name
        if not src.exists():
             continue
        dst = _RESEARCH_DST / name
        raw = src.read_bytes().replace(b"\r\n", b"\n")
        dst.write_bytes(raw)
        written.append(dst)

    return written

if __name__ == "__main__":
    paths = emit()
    print(f"copied {len(paths)} research modules into {_RESEARCH_DST}")
