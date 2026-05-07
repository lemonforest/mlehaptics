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
    "fluid_instrument_data.py",
    "fluid_instrument.py",
    "spherical_harmonic_catalog.py",
    "admittance_catalog_data.py",
    "admittance_catalog.py",
    "dynamo_catalog_data.py",
    "dynamo_catalog.py",
    "orographic_forcing_data.py",
    "orographic_forcing.py",
    "rotational_constraint_data.py",
    "rotational_constraint_catalog.py",
    "auroral_coupling_data.py",
    "auroral_coupling_catalog.py",
    "tidal_migration_data.py",
    "tidal_migration_catalog.py",
    "atmospheric_escape_data.py",
    "atmospheric_escape_catalog.py",
    "heat_flow_data.py",
    "heat_flow_catalog.py",
    "volcanic_outgassing_data.py",
    "volcanic_outgassing_catalog.py",
    "thermal_balance_data.py",
    "thermal_balance_catalog.py",
    "ballistic_trajectory_data.py",
    "ballistic_trajectory_catalog.py",
    "icbm_trajectory_data.py",
    "icbm_trajectory_catalog.py",
    "sensor_access_data.py",
    "sensor_access_catalog.py",
    "decoy_discrimination_data.py",
    "decoy_discrimination_catalog.py",
    "spin_orbit_resonance_data.py",
    "spin_orbit_resonance_catalog.py",
    "mercury_dynamical_spectrum_data.py",
    "mercury_dynamical_spectrum_catalog.py",
    "luna_dynamical_spectrum_data.py",
    "luna_dynamical_spectrum_catalog.py",
    "mars_dynamical_spectrum_data.py",
    "mars_dynamical_spectrum_catalog.py",
    "sun_dynamical_spectrum_data.py",
    "sun_dynamical_spectrum_catalog.py",
    "toroidal_residual_data.py",
    "toroidal_residual_catalog.py",
    "hawaii_chain_data.py",
    "hawaii_chain_catalog.py",
    "yarkovsky_yorp_data.py",
    "yarkovsky_yorp_catalog.py",
    "mars_tharsis_data.py",
    "mars_tharsis_catalog.py",
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
