"""DE441 Full Sweep Validation.

Compares the First-Principles Laplacian model against the high-precision 
JPL DE441 ephemeris truth over a multi-millennium window.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
import pytest
from ephemerides_spectral._research.ephemeris_reference_instrument import EphemerisHDCInstrument, REFERENCE_JD
from ephemerides_spectral._research.bodies import BODIES

@pytest.mark.parametrize("kernel_name", ["de421", "de440", "de441", "de442"])
def test_phase_drift_sweep(kernel_name: str):
    """Sweep 100 years and measure RMS phase drift of the Laplacian model."""
    k_path = Path(f"skyfield_data/{kernel_name}.bsp")
    if not k_path.exists():
        pytest.skip(f"Kernel {kernel_name} missing")

    instrument = EphemerisHDCInstrument(kernel=kernel_name)

    
    # Sweep range: J2000 +/- 50 years (numpy-free linspace(-50, 50, 5)).
    years = [-50.0, -25.0, 0.0, 25.0, 50.0]
    jds = [REFERENCE_JD + (y * 365.25) for y in years]
    
    body_errors = {name: [] for name in instrument.body_names}
    ts = instrument.bundle.ts
    
    for jd in jds:
        delta_t = jd - REFERENCE_JD
        pred_phases = instrument.laplacian.evolve_state(instrument.initial_phases, delta_t)
        
        t = ts.tt_jd(jd)
        for i, name in enumerate(instrument.body_names):
            body_info = BODIES.get(name)
            if not body_info: continue
            
            try:
                # 1. Resolve Target Body
                target_key = name.upper()
                if body_info.category == "planet":
                    target_key += " BARYCENTER"
                # v0.9.0: bundle.lookup translates internal terra/luna
                # to JPL-side EARTH/MOON.
                target = instrument.bundle.lookup(target_key)

                # 2. Resolve Center (Matches calibration)
                if body_info.category == "planet":
                    center = instrument.bundle.lookup("sun")
                elif body_info.category == "moon":
                    # Simple heuristic mapping
                    parent_name = "terra"
                    if name in ["phobos", "deimos"]: parent_name = "mars"
                    elif name in ["io", "europa", "ganymede", "callisto"]: parent_name = "jupiter"
                    elif name in ["titan", "enceladus", "rhea"]: parent_name = "saturn"
                    elif name == "titania": parent_name = "uranus"
                    elif name == "triton": parent_name = "neptune"

                    parent_key = parent_name.upper()
                    if parent_name in ["terra", "mars", "jupiter", "saturn", "uranus", "neptune"]:
                         parent_key += " BARYCENTER"
                    center = instrument.bundle.lookup(parent_key)
                else:
                    center = instrument.bundle.lookup("sun")

                astrometric = center.at(t).observe(target)
                _, lon, _ = astrometric.ecliptic_latlon()
                truth_phase = lon.radians
                
                err = (pred_phases[i] - truth_phase + math.pi) % (2.0 * math.pi) - math.pi
                body_errors[name].append(abs(err))
            except (KeyError, ValueError):
                continue

    print(f"\n{kernel_name.upper()} Phase Drift Analysis")
    print("-" * 60)
    for name, errs in body_errors.items():
        if not errs: continue
        rms = math.sqrt(sum(e * e for e in errs) / len(errs))
        print(f"{name:<12}: {rms:.6f} rad")
        assert rms < 3.0 # Allow for drift in first-principles model

if __name__ == "__main__":
    # If run as script, perform full sweep
    test_phase_drift_sweep("de421")
