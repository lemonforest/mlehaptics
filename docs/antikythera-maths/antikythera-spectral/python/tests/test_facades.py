"""Smoke-test the facade modules.

Each facade re-exports a curated subset of the corresponding
``_research/`` module's API. These tests:

- assert the facade imports cleanly,
- assert every name in ``__all__`` is actually present,
- exercise one round-trip-style call so we catch obvious breakage.

Bridge-method-level tests live in ``test_bridge_round_trip.py`` (phase 4+).
"""

from __future__ import annotations

from typing import List

import pytest


def _assert_dunder_all_resolves(module) -> None:
    """Every name in ``__all__`` must resolve to a real attribute."""
    missing = [n for n in module.__all__ if not hasattr(module, n)]
    assert not missing, f"{module.__name__}: __all__ lists missing names: {missing}"


def test_encoder_facade() -> None:
    from antikythera_spectral import encoder

    _assert_dunder_all_resolves(encoder)
    assert encoder.D_CALLIPPIC == 940
    assert encoder.D_PACKING == 13440
    assert encoder.REFERENCE_JD > 1_000_000  # JD TDB
    assert len(encoder.DIAL_SPECS) >= 10

    state = encoder.encode_ant_callippic(encoder.REFERENCE_JD)
    assert state.shape == (encoder.D_CALLIPPIC,)


def test_decoder_facade() -> None:
    from antikythera_spectral import decoder, encoder

    _assert_dunder_all_resolves(decoder)

    # LCM round-trip is exact by construction.
    rt = decoder.round_trip_lcm(encoder.REFERENCE_JD)
    assert isinstance(rt, dict)
    matches: List[bool] = [d.get("match", False) for d in rt.values()]
    assert all(matches), f"LCM round-trip should be exact; failures: " \
                         f"{[k for k, d in rt.items() if not d.get('match')]}"


def test_dials_facade() -> None:
    from antikythera_spectral import dials

    _assert_dunder_all_resolves(dials)
    assert len(dials.CYCLES) >= 10
    assert len(dials.DIAL_SPECS) >= 10
    # prime_factors of 235 (the Metonic numerator) = [5, 47]
    assert sorted(dials.prime_factors(235)) == [5, 47]


def test_render_facade() -> None:
    from antikythera_spectral import encoder, render

    _assert_dunder_all_resolves(render)
    state = encoder.encode_ant_callippic(encoder.REFERENCE_JD)
    xy = render.render_dial(state, D=encoder.D_CALLIPPIC)
    assert isinstance(xy, dict)
    assert len(xy) > 0
    for name, coord in xy.items():
        assert len(coord) == 2, f"{name}: render must return (x, y)"


def test_ephemeris_facade() -> None:
    from antikythera_spectral import ephemeris

    _assert_dunder_all_resolves(ephemeris)
    # Allowlist must be a non-empty tuple of known JPL kernels.
    assert isinstance(ephemeris.ALLOWED_KERNELS, tuple)
    assert "de441" in ephemeris.ALLOWED_KERNELS
    assert "de421" in ephemeris.ALLOWED_KERNELS
    # NOTE: do NOT call load_ephemeris() in this smoke test — the underlying
    # skyfield Loader auto-downloads BSP kernels on miss, which we want to
    # gate on user opt-in (per ADR 0001 / 0003). The bridge round-trip
    # tests in phase 4 exercise the loader against an env-var-pointed
    # local kernel only.
    assert ephemeris.is_available is not None
    assert callable(ephemeris.kernel_for_jd_range)


def test_eclipses_facade() -> None:
    from antikythera_spectral import eclipses

    _assert_dunder_all_resolves(eclipses)
    assert len(eclipses.HELLENISTIC_ANCHORS) >= 6
    assert len(eclipses.MODERN_SAROS_ANCHORS) >= 1

    hellenistic = eclipses.anchors_for_era("hellenistic")
    assert len(hellenistic) == len(eclipses.HELLENISTIC_ANCHORS)


def test_periods_facade() -> None:
    from antikythera_spectral import periods

    _assert_dunder_all_resolves(periods)
    assert len(periods.MULAPIN_PERIODS) >= 5
    assert len(periods.ALMAGEST_PERIODS) >= 5
    mul = periods.periods_by_source("mulapin")
    assert len(mul) == len(periods.MULAPIN_PERIODS)


def test_gears_facade() -> None:
    from antikythera_spectral import gears

    _assert_dunder_all_resolves(gears)
    assert len(gears.ALL_GEARS) >= 30
    assert len(gears.MESH_EDGES) >= 10
    assert gears.RECONSTRUCTIONS == (gears.FREETH_2021, gears.WRIGHT, gears.PRICE_1974)
    # Every gear must have a Freeth tooth count in the dict (the canonical
    # reconstruction we default to).
    missing = [g.name for g in gears.ALL_GEARS if gears.FREETH_2021 not in g.teeth]
    assert not missing, f"gears missing Freeth count: {missing}"


def test_hypotheses_facade() -> None:
    from antikythera_spectral import hypotheses

    _assert_dunder_all_resolves(hypotheses)
    assert len(hypotheses.ALL_HYPOTHESIS_IDS) == 31
    # B-H1 (cyclic-group structure) is a fast PASS — good smoke test.
    row, _ = hypotheses.hypothesis_B_H1()
    assert row["id"] == "B-H1"
    assert row["status"] in {"PASS", "FAIL", "PARTIAL", "UNDETERMINED"}
