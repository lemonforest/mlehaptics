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
    "axial_seamount_data.py",
    "axial_seamount_catalog.py",
    "dynamical_regime_data.py",
    "dynamical_regime_probes_data.py",
    "dynamical_regime_catalog.py",
    "pluto_charon_dynamical_spectrum_data.py",
    "pluto_charon_dynamical_spectrum_catalog.py",
    "loki_patera_data.py",
    "loki_patera_catalog.py",
    # v0.25.0a — Attested Multi-Source Collector framework
    "attested_collector_format.py",
    "attested_collector_descriptor.py",
    "attested_collector_catalog.py",
]

# Subdirectories under research/ to mirror recursively (preserves
# package structure for nested modules like attested_adapters/).
_INCLUDED_SUBDIRS: List[str] = [
    "attested_adapters",
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

    # Mirror nested-package subdirectories (v0.25.0+).
    for subdir in _INCLUDED_SUBDIRS:
        src_dir = src_root / subdir
        if not src_dir.exists():
            continue
        dst_dir = _RESEARCH_DST / subdir
        dst_dir.mkdir(parents=True, exist_ok=True)
        for src_file in sorted(src_dir.rglob("*.py")):
            rel = src_file.relative_to(src_dir)
            dst_file = dst_dir / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            raw = src_file.read_bytes().replace(b"\r\n", b"\n")
            dst_file.write_bytes(raw)
            written.append(dst_file)

    return written

if __name__ == "__main__":
    paths = emit()
    print(f"copied {len(paths)} research modules into {_RESEARCH_DST}")
