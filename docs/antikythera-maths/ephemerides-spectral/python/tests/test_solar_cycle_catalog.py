"""v0.30.0rc3 — Sol Solar Cycle Spectrum tests.

Pins the third solar-dynamics catalogue (after the v0.24.3 Sun
Dynamical Spectrum's p-modes and the rc2 differential rotation): the
Sun's slow magnetic clock.

* The Schwabe sunspot cycle (~11 yr), the Hale magnetic-polarity cycle
  (22 yr), the Gleissberg amplitude modulation (~88 yr).
* THE closure invariant: the Hale cycle is exactly two Schwabe cycles
  (Hale = 2 x Schwabe), the polarity Class-K sign-flip doubling the
  period — the same sign-flip-doubles-the-period structure as an
  epicycle.
* The butterfly diagram (Spörer's law): sunspots drift from ~30 deg to
  ~8 deg latitude over each cycle.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.solar_cycle_catalog import (
    get_butterfly_drift,
    get_hale_polarity_closure,
    get_solar_cycle_spectrum,
    list_solar_cycle_spectrum,
)
from ephemerides_spectral._research.solar_cycle_data import (
    BUTTERFLY_END_LATITUDE_DEG,
    BUTTERFLY_START_LATITUDE_DEG,
    GLEISSBERG_PERIOD_YEARS,
    HALE_PERIOD_YEARS,
    HALE_TO_SCHWABE_RATIO,
    SCHWABE_PERIOD_YEARS,
    SOLAR_CYCLES,
    SOURCES,
)


# ──────────────────────────────────────────────────────────────────────
# Periods + roster
# ──────────────────────────────────────────────────────────────────────


def test_cycle_periods() -> None:
    """Schwabe ~11 yr, Hale 22 yr, Gleissberg ~88 yr."""
    assert SCHWABE_PERIOD_YEARS == pytest.approx(11.0, abs=1e-9)
    assert HALE_PERIOD_YEARS == pytest.approx(22.0, abs=1e-9)
    assert GLEISSBERG_PERIOD_YEARS == pytest.approx(88.0, abs=1e-9)


def test_sources_count_4() -> None:
    assert len(SOURCES) == 4


def test_cycle_count_3() -> None:
    assert len(SOLAR_CYCLES) == 3


def test_every_cycle_source_resolves() -> None:
    for c in SOLAR_CYCLES:
        assert c.source_key in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Spectrum surface
# ──────────────────────────────────────────────────────────────────────


def test_spectrum_periods() -> None:
    r = get_solar_cycle_spectrum()
    assert r["periods_years"]["schwabe"] == pytest.approx(11.0, abs=1e-9)
    assert r["periods_years"]["hale"] == pytest.approx(22.0, abs=1e-9)
    assert r["periods_years"]["gleissberg"] == pytest.approx(88.0, abs=1e-9)


def test_spectrum_n_cycles() -> None:
    r = get_solar_cycle_spectrum()
    assert r["n_cycles"] == 3
    assert len(r["cycles"]) == 3


def test_spectrum_butterfly_latitudes() -> None:
    r = get_solar_cycle_spectrum()
    bl = r["butterfly_latitude_deg"]
    assert bl["cycle_start"] == pytest.approx(30.0, abs=1e-9)
    assert bl["cycle_end"] == pytest.approx(8.0, abs=1e-9)


# ──────────────────────────────────────────────────────────────────────
# THE closure invariant: Hale = 2 x Schwabe (the polarity sign-flip)
# ──────────────────────────────────────────────────────────────────────


def test_hale_is_two_schwabe() -> None:
    """THE headline: the Hale magnetic cycle is exactly two Schwabe
    sunspot cycles — the predicted Hale period equals the observed one
    (residual exactly 0 by the integer 2:1 commensurability)."""
    r = get_hale_polarity_closure()
    assert r["hale_to_schwabe_ratio"] == 2
    assert r["predicted_hale_years"] == pytest.approx(
        HALE_PERIOD_YEARS, abs=1e-9,
    )
    assert r["residual_years"] == pytest.approx(0.0, abs=1e-9)


def test_hale_ratio_is_integer_two() -> None:
    """The Hale:Schwabe ratio is the exact integer 2 — the polarity
    sign-flip-doubles-the-period (Class-K)."""
    assert HALE_TO_SCHWABE_RATIO == 2
    r = get_hale_polarity_closure()
    assert r["polarity_flips_per_hale_cycle"] == 2


def test_hale_closure_interpretation_mentions_sign_flip() -> None:
    r = get_hale_polarity_closure()
    assert "sign-flip" in r["interpretation"]
    assert "epicycle" in r["interpretation"]


# ──────────────────────────────────────────────────────────────────────
# Butterfly drift (Spörer's law)
# ──────────────────────────────────────────────────────────────────────


def test_butterfly_equatorward_drift() -> None:
    """Sunspots drift from ~30 deg to ~8 deg latitude (22 deg toward the
    equator over the cycle)."""
    r = get_butterfly_drift()
    assert r["start_latitude_deg"] == pytest.approx(30.0, abs=1e-9)
    assert r["end_latitude_deg"] == pytest.approx(8.0, abs=1e-9)
    assert r["equatorward_drift_deg"] == pytest.approx(
        BUTTERFLY_START_LATITUDE_DEG - BUTTERFLY_END_LATITUDE_DEG, abs=1e-9,
    )


def test_butterfly_drift_is_positive() -> None:
    """The drift is equatorward (start latitude exceeds end latitude)."""
    r = get_butterfly_drift()
    assert r["equatorward_drift_deg"] > 0.0


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_solar_cycle_spectrum_smoke() -> None:
    r = get_solar_cycle_spectrum()
    assert r["ok"] is True
    assert r["body"] == "sol"


def test_get_hale_polarity_closure_smoke() -> None:
    r = get_hale_polarity_closure()
    assert r["ok"] is True
    assert r["body"] == "sol"


def test_list_solar_cycle_spectrum_smoke() -> None:
    r = list_solar_cycle_spectrum()
    assert r["ok"] is True
    assert r["n_sources"] == 4
    assert r["n_cycles"] == 3


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_solar_cycle_spectrum() -> None:
    r = bridge.get_solar_cycle_spectrum()
    assert r["ok"] is True
    assert r["n_cycles"] == 3


def test_bridge_get_hale_polarity_closure() -> None:
    r = bridge.get_hale_polarity_closure()
    assert r["ok"] is True
    assert r["residual_years"] == pytest.approx(0.0, abs=1e-9)


def test_bridge_get_butterfly_drift() -> None:
    r = bridge.get_butterfly_drift()
    assert r["ok"] is True
    assert r["equatorward_drift_deg"] > 0.0


def test_bridge_list_solar_cycle_spectrum() -> None:
    r = bridge.list_solar_cycle_spectrum()
    assert r["ok"] is True
    assert r["n_sources"] == 4


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def _cli_json(argv):
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(argv)
    assert rc == 0
    return _json.loads(buf.getvalue())


def test_cli_solar_cycle_spectrum_smoke() -> None:
    payload = _cli_json(["solar-cycle-spectrum"])
    assert payload["body"] == "sol"
    assert payload["n_cycles"] == 3


def test_cli_hale_polarity_closure_smoke() -> None:
    payload = _cli_json(["hale-polarity-closure"])
    assert payload["hale_to_schwabe_ratio"] == 2


def test_cli_butterfly_drift_smoke() -> None:
    payload = _cli_json(["butterfly-drift"])
    assert payload["equatorward_drift_deg"] > 0.0


def test_cli_solar_cycle_spectrum_full_smoke() -> None:
    payload = _cli_json(["solar-cycle-spectrum-full"])
    assert payload["n_sources"] == 4


def test_cli_solar_cycle_help() -> None:
    """All v0.30.0rc3 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("solar-cycle-spectrum",
                "hale-polarity-closure",
                "butterfly-drift",
                "solar-cycle-spectrum-full"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
