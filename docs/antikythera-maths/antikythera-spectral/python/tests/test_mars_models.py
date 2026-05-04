"""Mars models facade — smoke + bronze-parity + FJ-38° fact.

Tests three things:

1. ``mars_models`` facade imports cleanly and every ``__all__`` name
   resolves to an attribute (matches the pattern in test_facades.py).
2. Bronze parity: ``mars_longitude_bronze`` and
   ``mars_longitude_epicycle_only`` agree to <1e-9 deg under all three
   named param sets (PTOLEMY, FREETH_2012, FREETH_2021).  Different
   derivation pathway (algebra of gear ratios via inline pin-and-slot
   transform vs. equation-of-center geometry), same transform.
3. F&J 38° finding: kernel-conditional reproduction of F&J 2012 Fig 39's
   "nearly 38°" Mars peak error.  Verifies that the bare deferent +
   epicycle (FREETH_2012_MARS_PARAMS) on the middle 7 retrogrades vs
   JPL DE422 yields RMS ≈ 38.85° (within 1° of F&J's documented 38°).
   Skipped cleanly if no DE-series kernel cached; CI gate exercises
   it explicitly.
"""

from __future__ import annotations

import math

import pytest


def _assert_dunder_all_resolves(module) -> None:
    """Every name in ``__all__`` must resolve to a real attribute."""
    missing = [n for n in module.__all__ if not hasattr(module, n)]
    assert not missing, (
        f"{module.__name__}: __all__ lists missing names: {missing}"
    )


# ---------------------------------------------------------------------------
# Smoke: facade imports + param sets distinguish + each model runs
# ---------------------------------------------------------------------------

def test_mars_models_facade_imports() -> None:
    from antikythera_spectral import mars_models

    _assert_dunder_all_resolves(mars_models)


def test_mars_models_param_sets_distinguish() -> None:
    """The three named param sets must differ on the salient axes:
    eccentricity (Ptolemy: 6, Freeth: 0) and equant_offset (Ptolemy: 12,
    Freeth: 0)."""
    from antikythera_spectral import mars_models

    assert mars_models.PTOLEMY_MARS_PARAMS.eccentricity == 6.0
    assert mars_models.PTOLEMY_MARS_PARAMS.equant_offset == 12.0
    assert mars_models.FREETH_2012_MARS_PARAMS.eccentricity == 0.0
    assert mars_models.FREETH_2012_MARS_PARAMS.equant_offset == 0.0
    assert mars_models.FREETH_2021_MARS_PARAMS.eccentricity == 0.0
    assert mars_models.FREETH_2021_MARS_PARAMS.equant_offset == 0.0


def test_mars_models_each_model_runs() -> None:
    """Every registered Mars model must evaluate without raising on
    REFERENCE_JD with the default param set."""
    from antikythera_spectral import mars_models

    for name, fn in mars_models.MODEL_FUNCTIONS.items():
        out = fn(mars_models.REFERENCE_JD, mars_models.PTOLEMY_MARS_PARAMS)
        assert isinstance(out, float), (
            f"model {name!r} returned non-float: {out!r}"
        )
        assert 0.0 <= out < 360.0, (
            f"model {name!r} returned phase outside [0, 360): {out}"
        )


def test_mars_models_get_params_resolves_lowercase() -> None:
    """``get_params(name)`` resolves the lowercase string keys used by
    bridge.compare_models / compare.compare_models_at_jd."""
    from antikythera_spectral import mars_models

    assert (mars_models.get_params("ptolemy")
            is mars_models.PTOLEMY_MARS_PARAMS)
    assert (mars_models.get_params("freeth_2012")
            is mars_models.FREETH_2012_MARS_PARAMS)
    assert (mars_models.get_params("freeth_2021")
            is mars_models.FREETH_2021_MARS_PARAMS)
    with pytest.raises(ValueError, match="Unknown Mars param set"):
        mars_models.get_params("unknown")


def test_mars_models_param_sets_table_complete() -> None:
    """``PARAM_SETS`` must cover every named param set the facade
    exports."""
    from antikythera_spectral import mars_models

    expected_constants = {
        mars_models.PTOLEMY_MARS_PARAMS,
        mars_models.FREETH_2012_MARS_PARAMS,
        mars_models.FREETH_2021_MARS_PARAMS,
    }
    table_values = set(mars_models.PARAM_SETS.values())
    assert table_values == expected_constants


# ---------------------------------------------------------------------------
# Bronze parity: bronze == epicycle-only to <1e-9 across param sets
# ---------------------------------------------------------------------------

def _wrap_180(deg: float) -> float:
    return ((deg + 180.0) % 360.0) - 180.0


@pytest.mark.parametrize(
    "params_name",
    ["PTOLEMY_MARS_PARAMS",
     "FREETH_2012_MARS_PARAMS",
     "FREETH_2021_MARS_PARAMS"],
)
def test_bronze_parity(params_name: str) -> None:
    """``mars_longitude_bronze`` and ``mars_longitude_epicycle_only``
    must agree to numerical precision across one Mars synodic period.

    The bronze model derives the synodic phase as a projection from
    the gear-ratio cyclic-group algebra via the inline pin-and-slot
    phase-space transform; the epicycle-only model derives the same
    quantity via the explicit Hellenistic equation of center.  Same
    transform, two derivations -- a direct test of the algebra/
    eigenbasis projection framing (ADR 0012).
    """
    from antikythera_spectral import mars_models

    params = getattr(mars_models, params_name)
    peak_diff = 0.0
    n_samples = 200
    span_days = 779.94 * 5  # 5 Mars synodic periods
    step = span_days / (n_samples - 1)
    for k in range(n_samples):
        jd = mars_models.REFERENCE_JD + k * step
        a = mars_models.mars_longitude_bronze(jd, params)
        b = mars_models.mars_longitude_epicycle_only(jd, params)
        diff = abs(_wrap_180(a - b))
        if diff > peak_diff:
            peak_diff = diff
    assert peak_diff < 1e-9, (
        f"{params_name}: bronze vs epicycle-only peak diff = {peak_diff:.3e} "
        f"deg exceeds 1e-9 tolerance"
    )


# ---------------------------------------------------------------------------
# F&J 38° finding: kernel-conditional reproduction
# ---------------------------------------------------------------------------

def _de422_kernel_available() -> bool:
    """True iff a DE-series kernel covering the F&J -53 BCE window is
    cached on disk."""
    try:
        from antikythera_spectral._research.ephemeris_loader import (
            load_ephemeris,
        )
    except ImportError:
        return False
    for k in ("de422", "de441_part1", "de441"):
        if load_ephemeris(k) is not None:
            return True
    return False


@pytest.mark.skipif(
    not _de422_kernel_available(),
    reason=(
        "F&J 38° fact test requires DE422 / DE441 kernel.  "
        "Run `python -m research.ephemeris_loader --download de422` "
        "to fetch."
    ),
)
def test_fj_38deg_finding() -> None:
    """F&J 2012 Fig 39's "nearly 38°" Mars peak error reproduces directly
    as the unfit RMS shape error of the bare deferent + epicycle on the
    middle 7 retrogrades of the 1st century BC vs JPL DE422.

    Pinned tolerance: within 1.0° of F&J's documented "nearly 38°".
    Empirically the value lands at ~38.85°, well under tolerance.

    Three pieces of F&J's setup must match for the number to reproduce
    (see ADR 0012 + figures/mars_38deg_gap_findings.md):
      - model: bare deferent + epicycle (FREETH_2012_MARS_PARAMS, ε=0)
      - reference: JPL Horizons (DE422 / DE441 here)
      - subset: 7 retrograde sub-windows centred on each opposition
    """
    from antikythera_spectral import mars_models

    finding = mars_models.fj_38deg_finding()
    # Structural assertions: the dict shape is part of the contract.
    assert finding["model"].startswith("bare deferent + epicycle")
    assert finding["fj_documented_deg"] == 38.0
    assert finding["kernel_used"] in ("de422", "de441_part1", "de441")
    assert len(finding["oppositions_jd"]) == 7
    assert finding["n_samples"] == 7 * 30  # 7 retrogrades x 30 samples
    # Numerical assertion: F&J's 38° reproduces within 1°.
    assert finding["residual_deg"] <= 1.0, (
        f"F&J 38° reproduction off by {finding['residual_deg']:.2f}° "
        f"(rms_deg = {finding['rms_deg']:.2f}, expected ~38°)"
    )
    # Sanity: rms > mean > 0 (mean-corrected residuals).
    assert finding["mean_deg"] > 0.0
    assert finding["rms_deg"] >= finding["mean_deg"]
    assert finding["peak_deg"] >= finding["rms_deg"]
