"""Mars planetary models — Hellenistic theory + bronze-projection facade.

Curated public re-export of ``_research.equant_encoder``: four Mars
longitude models and three reconstruction-source-specific parameter
sets.  Exposed here as a separate facade (rather than under
``antikythera_spectral.encoder``) because Mars planetary theory is a
distinct concern from the HDC encoder family — Mars models are
analytic Hellenistic geometry plus the bronze projection, whereas
``encoder`` is the cyclic-group / hypervector encode_ant family.

Models
------

``mars_longitude_uniform``
    Constant 360 / 779.94 deg/day synodic phase.  The Antikythera
    encoder's baseline for Mars; peak ~180° vs JPL DE-series at
    Hellenistic-era epochs (E-H2 in the H-battery).

``mars_longitude_epicycle_only``
    Hipparchus-style eccentric deferent + epicycle; no equant.  The
    Antikythera mechanism's gear-train can mechanically approximate
    this model with a pin-and-slot (Freeth 2006).

``mars_longitude_equant``
    Ptolemy's Almagest IX-X model: deferent rotates uniformly w.r.t.
    an equant point offset 2e from Earth (bisected eccentricity);
    epicycle uniform on its own centre.  Documented Greek attainable
    band (Toomer 1984): peak ~30-50° on Antikythera-era windows.

``mars_longitude_bronze``
    **Projection from the cyclic-group / graph-Laplacian eigenbasis
    representation of the Mars deferent gear ratios back to the
    pointer's spatial longitude.**  Mathematically: the pin-and-slot
    phase-space transform ``atan2(sin θ_in, cos θ_in + e/R)`` applied
    inline to the deferent input mean-motion.  Numerically agrees
    with ``mars_longitude_epicycle_only`` to ~10⁻¹³ deg under all
    three named param sets — same transform, two derivation
    pathways (see ``test_mars_models.test_bronze_parity``).  The
    ``bronze`` model is the algebra/eigenbasis-projected complement
    to the analytic equation-of-center pathway; see ADR 0012 for the
    scope rationale.

Parameter sets
--------------

``PTOLEMY_MARS_PARAMS``
    Almagest IX-X canonical: R=60, r=39.5, e=6, equant_offset=12,
    Almagest IX.6 mean motions.

``FREETH_2012_MARS_PARAMS``
    Freeth & Jones 2012 (ISAW Papers 4, §3.10 + Fig 39) pre-
    Hipparchian: bare deferent + epicycle, no eccentricity, no
    equant, Babylonian (37, -79) period relation.  The setup F&J
    used to document the famous "nearly 38°" Mars peak error.

``FREETH_2021_MARS_PARAMS``
    Freeth 2021 reconstruction of the Mars planetary plate; same
    kinematic class as F&J 2012 (deferent + epicycle, no
    eccentricity), gear-derived 133/125 synodic ratio.  Bundled here
    as a label-distinct param set; numerical content matches
    FREETH_2012 within Hellenistic-era arcsec.

The 38° finding
---------------

``fj_38deg_finding()`` is a lazy callable that reproduces the F&J
2012 Figure 39 documented "nearly 38°" Mars peak error directly
from the bare deferent + epicycle model on the middle 7 retrogrades
of the 1st century BC vs JPL DE422.  Returns the numerical
reproduction (~38.85°, within 0.85° of F&J's number) and the three
component pieces of the setup.  Requires ``de422`` or ``de441``
ephemeris kernel; raises ``RuntimeError`` if no kernel is available.
See ``docs/antikythera-maths/figures/mars_38deg_gap_findings.md``
for the full ten-analysis decomposition.

References
----------

- Toomer, G. J. (1984). *Ptolemy's Almagest*. Princeton.
- Freeth, T. & Jones, A. (2012). "The Cosmos in the Antikythera
  Mechanism." *ISAW Papers* 4. http://dlib.nyu.edu/awdl/isaw/isaw-papers/4/
- Freeth, T. (2021). "A Model of the Cosmos in the ancient Greek
  Antikythera Mechanism." *Sci. Rep.* 11:5821.
- Freeth, T. et al. (2006). *Nature* 444:587 (lunar pin-and-slot).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from antikythera_spectral._research.equant_encoder import (
    MODEL_FUNCTIONS,
    REFERENCE_JD,
    VALID_MODELS,
    FREETH_2012_MARS_PARAMS,
    FREETH_2021_MARS_PARAMS,
    PTOLEMY_MARS_PARAMS,
    MarsParams,
    mars_longitude_bronze,
    mars_longitude_epicycle_only,
    mars_longitude_equant,
    mars_longitude_uniform,
    model_residue_function,
)


# ---------------------------------------------------------------------------
# Named param-set lookup (lowercase strings -> MarsParams instances).
# Used by compare.compare_models_at_jd and bridge.compare_models for
# string-keyed parameter selection.
# ---------------------------------------------------------------------------

PARAM_SETS: Dict[str, MarsParams] = {
    "ptolemy":     PTOLEMY_MARS_PARAMS,
    "freeth_2012": FREETH_2012_MARS_PARAMS,
    "freeth_2021": FREETH_2021_MARS_PARAMS,
}
"""Lookup from lowercase string keys to MarsParams instances.  The
public API surface (``compare_models``, ``bridge.compare_models``)
takes lowercase string keys; this is the mapping."""


def get_params(name: str) -> MarsParams:
    """Resolve a lowercase param-set name to its MarsParams instance.

    Raises ``ValueError`` on unknown name.  Wrapped here so callers in
    other modules don't need to import the constant table directly.
    """
    if name not in PARAM_SETS:
        valid = ", ".join(sorted(PARAM_SETS))
        raise ValueError(
            f"Unknown Mars param set {name!r}; valid options: {valid}"
        )
    return PARAM_SETS[name]


# ---------------------------------------------------------------------------
# Lazy F&J 38° finding reproduction
# ---------------------------------------------------------------------------

def fj_38deg_finding(
    n_per_window: int = 30,
    half_width_days: float = 35.0,
) -> Dict[str, Any]:
    """Reproduce F&J 2012 Fig 39's "nearly 38°" Mars peak error directly.

    Runs the bare deferent + epicycle (``FREETH_2012_MARS_PARAMS``)
    against JPL DE422 on the middle 7 retrogrades of the 1st century
    BC, and returns the unfit-RMS shape error.  Three pieces of F&J's
    setup must match for the number to reproduce:

    - model: bare deferent + epicycle (no eccentricity, no equant)
      = ``FREETH_2012_MARS_PARAMS``
    - reference: JPL Horizons (``de422`` here, ≈ Horizons at -53 BCE
      precision)
    - subset: 7 retrograde sub-windows centred on each opposition

    Match all three and the unfit RMS reproduces F&J's "nearly 38°"
    to within 1°.

    Returns
    -------
    dict with keys:
        - ``rms_deg``: unfit RMS shape error against DE422 (target: ~38°)
        - ``mean_deg``: mean absolute residual
        - ``peak_deg``: max absolute residual
        - ``oppositions_jd``: list of 7 opposition JDs detected
        - ``n_samples``: total number of JDs sampled
        - ``kernel_used``: which JPL kernel resolved
        - ``fj_documented_deg``: 38.0 (F&J's reported figure)
        - ``residual_deg``: ``abs(rms_deg - fj_documented_deg)``
        - ``model``: ``"bare deferent + epicycle (FREETH_2012_MARS_PARAMS)"``

    Raises
    ------
    RuntimeError
        If skyfield is not installed or no DE-series kernel is
        cached.  Run ``python -m research.ephemeris_loader --download
        de422`` to fetch (~660 MB).

    Notes
    -----
    Lazy: nothing happens at import time.  The call costs ~1 second
    on a warm kernel cache (mostly skyfield ephemeris evaluation at
    210 sample JDs).  See
    ``docs/antikythera-maths/figures/mars_38deg_gap_findings.md`` for
    the full ten-analysis decomposition that puts this finding in
    context.
    """
    import math

    from antikythera_spectral._research.ephemeris_loader import load_ephemeris

    # Try the smallest kernel first that covers the F&J window.
    bundle = None
    kernel_used: Optional[str] = None
    for k in ("de422", "de441_part1", "de441"):
        b = load_ephemeris(k)
        if b is not None:
            bundle = b
            kernel_used = k
            break
    if bundle is None:
        raise RuntimeError(
            "F&J 38° reproduction requires a JPL DE-series kernel covering "
            "JD 1718935-1723634 (~-53 BCE ± 7 yr).  Run "
            "`python -m research.ephemeris_loader --download de422` "
            "to fetch ~660 MB."
        )

    # F&J window centre: -53 BCE = JD 1721423.5; widen to 15 yr to
    # capture exactly 7 oppositions.
    center_jd = 1721423.5
    half_span_yr = 7.5
    start_jd = center_jd - half_span_yr * 365.25
    end_jd = center_jd + half_span_yr * 365.25

    # Reference closure: JD -> Mars-Sun synodic phase (deg).
    cache: Dict[float, float] = {}

    def _reference(jd: float) -> float:
        if jd in cache:
            return cache[jd]
        t = bundle.ts.tdb_jd(float(jd))
        e = bundle.earth.at(t)
        m = e.observe(bundle.mars).apparent()
        s = e.observe(bundle.sun).apparent()
        _, m_lon, _ = m.ecliptic_latlon()
        _, s_lon, _ = s.ecliptic_latlon()
        phase = math.degrees(m_lon.radians - s_lon.radians) % 360.0
        cache[jd] = phase
        return phase

    # Detect oppositions (down-crossings of phase=180°).  1500 samples
    # over 15 yr is ~3.6-day spacing -- plenty to bracket the 180°
    # down-crossings (Mars-Sun synodic phase changes ~0.46°/day, so each
    # step covers ~1.65°).
    n_dense = 1500
    step = (end_jd - start_jd) / (n_dense - 1)
    phases = [_reference(start_jd + i * step) for i in range(n_dense)]
    oppositions = []
    for i in range(n_dense - 1):
        a, b = phases[i], phases[i + 1]
        if a > 180.0 >= b and (a - b) < 30.0:
            frac = (a - 180.0) / (a - b)
            oppositions.append(start_jd + (i + frac) * step)

    if len(oppositions) < 7:
        raise RuntimeError(
            f"Expected >=7 oppositions in 15-yr window centred on -53 BCE; "
            f"found {len(oppositions)}.  Kernel coverage or detection bug."
        )

    # Pick the 7 closest to centre.
    middle_7 = sorted(
        sorted(oppositions, key=lambda j: abs(j - center_jd))[:7]
    )

    # Build sample JDs: ±half_width_days × n_per_window per opposition.
    subset_jds = []
    for opp_jd in middle_7:
        lo = opp_jd - half_width_days
        hi = opp_jd + half_width_days
        s_step = (hi - lo) / max(n_per_window - 1, 1)
        for j in range(n_per_window):
            subset_jds.append(lo + j * s_step)
    subset_jds.sort()

    # Compute mean-corrected residuals.
    def _wrap_180(x: float) -> float:
        return ((x + 180.0) % 360.0) - 180.0

    signed = []
    for jd in subset_jds:
        pred = mars_longitude_epicycle_only(jd, FREETH_2012_MARS_PARAMS)
        truth = _reference(jd)
        signed.append(_wrap_180(pred - truth))

    sx = sum(math.cos(math.radians(s)) for s in signed)
    sy = sum(math.sin(math.radians(s)) for s in signed)
    mean_off = math.degrees(math.atan2(sy, sx))
    residuals = [_wrap_180(s - mean_off) for s in signed]
    abs_res = [abs(r) for r in residuals]
    rms = math.sqrt(sum(r * r for r in residuals) / len(residuals))
    mean = sum(abs_res) / len(abs_res)
    peak = max(abs_res)

    return {
        "rms_deg": float(rms),
        "mean_deg": float(mean),
        "peak_deg": float(peak),
        "oppositions_jd": [float(j) for j in middle_7],
        "n_samples": int(len(subset_jds)),
        "kernel_used": kernel_used,
        "fj_documented_deg": 38.0,
        "residual_deg": float(abs(rms - 38.0)),
        "model": "bare deferent + epicycle (FREETH_2012_MARS_PARAMS)",
    }


__all__ = [
    # Constants
    "REFERENCE_JD",
    "VALID_MODELS",
    "MODEL_FUNCTIONS",
    "PARAM_SETS",
    # Param sets
    "PTOLEMY_MARS_PARAMS",
    "FREETH_2012_MARS_PARAMS",
    "FREETH_2021_MARS_PARAMS",
    # Types
    "MarsParams",
    # Models
    "mars_longitude_uniform",
    "mars_longitude_epicycle_only",
    "mars_longitude_equant",
    "mars_longitude_bronze",
    # Helpers
    "model_residue_function",
    "get_params",
    # Lazy verified-finding accessor
    "fj_38deg_finding",
]
