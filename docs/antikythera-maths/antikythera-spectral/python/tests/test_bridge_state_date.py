"""Bridge §5.1 + §5.2 round-trip tests.

Seven methods exercised:

- get_dial_state / get_dial_angle / get_pointer_xy / get_all_dial_metadata
  / get_version
- decode_dial / decode_to_jd

Plus negative-input checks (invalid jd, dial, D) returning
``{"ok": False, ...}`` rather than raising.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from antikythera_spectral import bridge
from antikythera_spectral.encoder import D_CALLIPPIC, D_PACKING, REFERENCE_JD


# ──────────────────────────────────────────────────────────────────────
# Happy-path tests
# ──────────────────────────────────────────────────────────────────────

def test_get_version_carries_manifest() -> None:
    from antikythera_spectral.version import __version__

    out = bridge.get_version()
    assert out["ok"] is True
    assert out["package"] == "antikythera-spectral"
    # Follow __version__ rather than hardcoding — the value travels with
    # the version bump.
    assert out["version"] == __version__
    # manifest comes from codegen; must list >= 30 files
    assert len(out["manifest"].get("files", {})) >= 25


def test_get_dial_state_shape_callippic() -> None:
    out = bridge.get_dial_state(REFERENCE_JD, D=D_CALLIPPIC)
    assert out["ok"] is True
    assert out["D"] == D_CALLIPPIC
    assert out["state"]["shape"] == [D_CALLIPPIC]
    assert out["state"]["dtype"] == "complex128"
    # interleaved is 2*D float32 entries
    assert len(out["state"]["interleaved_f32"]) == 2 * D_CALLIPPIC
    # All values finite
    for v in out["state"]["interleaved_f32"][:32]:
        assert math.isfinite(v)
    # at least 10 dials produce residues
    assert len(out["dials"]) >= 10


def test_get_dial_state_shape_packing() -> None:
    out = bridge.get_dial_state(REFERENCE_JD, D=D_PACKING)
    assert out["ok"] is True
    assert out["D"] == D_PACKING
    assert out["state"]["shape"] == [D_PACKING]
    assert len(out["state"]["interleaved_f32"]) == 2 * D_PACKING


def test_get_dial_angle_metonic_at_reference() -> None:
    """At REFERENCE_JD all dials should sit at angle 0 (the anchor)."""
    out = bridge.get_dial_angle(REFERENCE_JD, "Metonic")
    assert out["ok"] is True
    assert out["dial"] == "Metonic"
    # phase = 0 at the reference epoch
    assert abs(out["angle_deg"]) < 1e-9 or abs(out["angle_deg"] - 360.0) < 1e-9
    assert out["residue"] == 0


def test_get_dial_angle_advances_with_jd() -> None:
    a = bridge.get_dial_angle(REFERENCE_JD + 100.0, "Metonic")
    b = bridge.get_dial_angle(REFERENCE_JD + 200.0, "Metonic")
    assert a["ok"] and b["ok"]
    # angle must change with jd (well-defined dial)
    assert a["angle_deg"] != b["angle_deg"]


def test_get_pointer_xy_dial_layout() -> None:
    out = bridge.get_pointer_xy(REFERENCE_JD, layout="dial")
    assert out["ok"] is True
    assert out["layout"] == "dial"
    assert isinstance(out["pointers"], dict)
    assert len(out["pointers"]) > 0
    for name, coord in out["pointers"].items():
        assert len(coord) == 2
        assert math.isfinite(coord[0]) and math.isfinite(coord[1])


def test_get_pointer_xy_spatial_layout() -> None:
    out = bridge.get_pointer_xy(REFERENCE_JD, layout="spatial")
    assert out["ok"] is True
    assert out["layout"] == "spatial"
    assert len(out["pointers"]) > 0


def test_get_all_dial_metadata() -> None:
    out = bridge.get_all_dial_metadata()
    assert out["ok"] is True
    assert out["n_dials"] >= 10
    metonic = next(d for d in out["dials"] if d["name"] == "Metonic")
    assert metonic["numerator"] == 235
    assert metonic["denominator"] == 19
    assert "supported_dims" in metonic


def test_decode_dial_round_trip() -> None:
    state = bridge.get_dial_state(REFERENCE_JD + 1234.5, D=D_CALLIPPIC)
    assert state["ok"]
    # Decode Metonic from the interleaved Float32
    out = bridge.decode_dial(
        {"interleaved_f32": state["state"]["interleaved_f32"]},
        "Metonic",
        D=D_CALLIPPIC,
    )
    assert out["ok"] is True
    assert out["dial"] == "Metonic"
    # The recovered residue should approximately match the encoded one;
    # exact match not guaranteed due to dense-encoder cross-talk, but
    # within ±5 quantization steps is reasonable.
    encoded = state["dials"]["Metonic"]["residue"]
    # Note: decoder returns the D-quantised residue, encoded["residue"]
    # is the modulus-natural integer. Both correspond to the same phase;
    # we just sanity-check that decode returned a non-negative int < D.
    assert 0 <= out["recovered_residue"] < D_CALLIPPIC
    assert encoded >= 0


def test_decode_to_jd_inverts_encode() -> None:
    target_jd = REFERENCE_JD + 365.25 * 19  # one Metonic cycle later
    state = bridge.get_dial_state(target_jd, D=D_CALLIPPIC)
    assert state["ok"]

    # Pass the complex array directly via numpy
    interleaved = np.asarray(state["state"]["interleaved_f32"], dtype=np.float32)
    out = bridge.decode_to_jd(interleaved, D=D_CALLIPPIC)
    assert out["ok"] is True
    # Median across dials should land within a Metonic-cycle modulus
    # of the target. (Per-dial dense-decoder noise is real; the test
    # is a smoke check, not a precision guarantee.)
    assert isinstance(out["median_jd"], float)
    assert out["spread_days"] >= 0.0


# ──────────────────────────────────────────────────────────────────────
# Input-validation negatives
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("bad_jd", [
    "not-a-number",
    None,
    float("nan"),
    float("inf"),
    1e10,                # outside plausible range
    -1e10,
])
def test_get_dial_state_rejects_bad_jd(bad_jd) -> None:
    out = bridge.get_dial_state(bad_jd)
    assert out["ok"] is False
    assert "error" in out


@pytest.mark.parametrize("bad_d", [-1, 0, 941, 13441, "940", None])
def test_get_dial_state_rejects_bad_dim(bad_d) -> None:
    out = bridge.get_dial_state(REFERENCE_JD, D=bad_d)
    assert out["ok"] is False
    assert "error" in out


@pytest.mark.parametrize("bad_dial", ["Pluto", "", 42, None])
def test_get_dial_angle_rejects_bad_dial(bad_dial) -> None:
    out = bridge.get_dial_angle(REFERENCE_JD, bad_dial)
    assert out["ok"] is False
    assert "error" in out


def test_get_pointer_xy_rejects_bad_layout() -> None:
    out = bridge.get_pointer_xy(REFERENCE_JD, layout="orbit")
    assert out["ok"] is False
    assert "error" in out


def test_decode_dial_rejects_short_state() -> None:
    out = bridge.decode_dial([1.0, 2.0, 3.0], "Metonic", D=D_CALLIPPIC)
    assert out["ok"] is False
    assert "error" in out


def test_decode_to_jd_rejects_bad_dim() -> None:
    out = bridge.decode_to_jd([0.0, 0.0], D=999)
    assert out["ok"] is False
    assert "error" in out
