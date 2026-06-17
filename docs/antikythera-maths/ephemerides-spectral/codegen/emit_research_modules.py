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
    # Cascade-compute helper — routes catalog math through srmech's
    # 14-class ops (Class-L Laplacian / Class-N trig-pow-sqrt / Class-K
    # sign) instead of raw numpy/math. Shared by the v0.30.x catalogs.
    "_cascade.py",
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
    # rc2 — the single numpy-free ITN / etak navigation cascade (shared
    # by body_architecture + predict_itn_accessibility) + the lazy
    # registrar for the GatewayNavigation [class] catalog TOML.
    "navigation_ops.py",
    "_srmech_classes.py",
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
    # First cosmology-instrument pair — AMSC-first ships (no _data.py;
    # catalog modules read directly from attested NDJSON via the AMSC
    # universal accessor).
    "cmb_power_spectrum_catalog.py",
    "cmb_anomalies_catalog.py",
    # v0.27.x — Saturn ring system, Phase 3 dual-author counterpart to
    # the AMSC literature_curated catalogue at
    # research/attested/saturn_rings/. Both paths encode the same 12
    # ring-feature rows; the dual-author diff test asserts byte-stable
    # agreement.
    "saturn_rings_data.py",
    # v0.30.0 — Saturn Ring System Catalog query surface (the temporal-
    # spectrum catalog of a multi-regime body; promotes the staged
    # saturn_rings_data dual-author fixture to a full query surface with
    # the four-regime partition + (p:q) resonance closure invariant +
    # bounded-local-Laplacian on the radial feature graph). Closes #153.
    "saturn_rings_catalog.py",
    # v0.30.0rc2 — Solar differential + internal rotation (first
    # solar-dynamics extension of the v0.24.3 Sun Dynamical Spectrum;
    # Snodgrass-Ulrich surface law + Schou-1998 internal rotation).
    "solar_rotation_data.py",
    "solar_rotation_catalog.py",
    # v0.30.0rc3 — Solar Cycle Spectrum (the Sun's slow magnetic clock;
    # Schwabe 11-yr / Hale 22-yr polarity-flip closure / Gleissberg
    # 88-yr modulation / butterfly drift). The Hale = 2 x Schwabe
    # closure is the polarity Class-K sign-flip doubling the period.
    "solar_cycle_data.py",
    "solar_cycle_catalog.py",
    # AMSC framework — REMOVED in Task #197 Phase 4 (2026-05-13). The
    # framework (format / descriptor / catalog / gap_suggester +
    # attested_adapters/) now lives at srmech.amsc.* on PyPI and is
    # pulled in via the `srmech>=0.1.0` runtime dependency in
    # pyproject.toml. ephemerides-spectral's __init__.py registers its
    # `_research/attested/` catalog root with srmech.amsc.catalog via
    # `register_attested_root()` and registers its dynamical-regime
    # classifier + probes via `register_classifier()` /
    # `register_probes()` at package-import time. Prior entries were:
    #   "attested_collector_format.py",
    #   "attested_collector_descriptor.py",
    #   "attested_collector_catalog.py",
    #   "attested_collector_gap_suggester.py",
    # LLM tool-schema export — introspects bridge.py at call time and
    # emits the bridge surface as Anthropic / OpenAI / MCP / jsonschema
    # tool descriptions. Self-describing API for LLM-tool-use clients.
    "tool_schema.py",
    # v0.27.0 phase C — Body→kernel registry (notebook §22.6); the
    # layer-2-to-layer-3 interface from the three-layer mechanism
    # architecture
    "body_kernel_registry.py",
    # v0.28.0rc1 Phase 10a — per-body equation-of-center catalog.
    # secular_elements_data.py carries J2000 Keplerian mean elements
    # for every non-Sun body in the 52-body BIP roster (51 rows);
    # eoc_catalog.py is the generator that turns each row into a
    # closed-form Newton-Kepler EccentricityCorrectionPatch (new
    # kind landed in diagnosed_fibers.py alongside this ship).
    "secular_elements_data.py",
    "eoc_catalog.py",
]

# Subdirectories under research/ to mirror recursively. Empty after
# Task #197 Phase 4 (2026-05-13) — `attested_adapters` was removed
# when the AMSC framework migrated to srmech.amsc.adapters.* on PyPI.
# Subdirectories mirrored into _research/ wholesale (both .py modules
# AND .toml data, so config-driven [class] catalogs ship). rc2 adds
# class_catalog/ (the GatewayNavigation descriptor).
_INCLUDED_SUBDIRS: List[str] = ["class_catalog"]

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
        _subdir_globs = ("*.py", "*.toml")
        for src_file in sorted(
            p for pat in _subdir_globs for p in src_dir.rglob(pat)
        ):
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
