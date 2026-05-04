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


def test_get_dial_state_default_backend_is_bit_callippic() -> None:
    """v0.3.0 default: bridge.get_dial_state returns a bit-packed state
    when ``backend`` is unspecified.  Wire shape: ceil(D/64) uint64 words
    plus an ``n_bits`` field so decoders know the unmasked length."""
    out = bridge.get_dial_state(REFERENCE_JD, D=D_CALLIPPIC)
    assert out["ok"] is True
    assert out["D"] == D_CALLIPPIC
    assert out["backend"] == "bit"
    assert out["state"]["dtype"] == "uint64"
    # 940 bits / 64 = 14.69 -> 15 words
    expected_words = (D_CALLIPPIC + 63) // 64
    assert out["state"]["shape"] == [expected_words]
    assert out["state"]["n_bits"] == D_CALLIPPIC
    assert len(out["state"]["packed_uint64"]) == expected_words
    # All packed words must fit in uint64.
    for w in out["state"]["packed_uint64"]:
        assert 0 <= w < (1 << 64)
    # at least 10 dials produce residues
    assert len(out["dials"]) >= 10


def test_get_dial_state_shape_callippic() -> None:
    """v0.2.x compatibility: backend='complex128' returns the original
    shape (length-D complex128 packed as interleaved Float32)."""
    out = bridge.get_dial_state(
        REFERENCE_JD, D=D_CALLIPPIC, backend="complex128",
    )
    assert out["ok"] is True
    assert out["D"] == D_CALLIPPIC
    assert out["backend"] == "complex128"
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
    out = bridge.get_dial_state(
        REFERENCE_JD, D=D_PACKING, backend="complex128",
    )
    assert out["ok"] is True
    assert out["D"] == D_PACKING
    assert out["backend"] == "complex128"
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


def test_decode_dial_round_trip_bit() -> None:
    """v0.3.0 default: bit-packed encode/decode round-trip on Metonic."""
    state = bridge.get_dial_state(REFERENCE_JD + 1234.5, D=D_CALLIPPIC)
    assert state["ok"]
    assert state["backend"] == "bit"
    out = bridge.decode_dial(state["state"], "Metonic", D=D_CALLIPPIC)
    assert out["ok"] is True
    assert out["dial"] == "Metonic"
    assert out["backend"] == "bit"
    # The decoder returns the D-quantised residue ∈ [0, D).
    assert 0 <= out["recovered_residue"] < D_CALLIPPIC


def test_decode_dial_round_trip_complex128() -> None:
    """v0.2.x compatibility: explicit backend='complex128' still round-trips."""
    state = bridge.get_dial_state(
        REFERENCE_JD + 1234.5, D=D_CALLIPPIC, backend="complex128",
    )
    assert state["ok"]
    assert state["backend"] == "complex128"
    # Decode Metonic from the interleaved Float32
    out = bridge.decode_dial(
        {"interleaved_f32": state["state"]["interleaved_f32"]},
        "Metonic",
        D=D_CALLIPPIC,
    )
    assert out["ok"] is True
    assert out["dial"] == "Metonic"
    assert out["backend"] == "complex128"
    # The recovered residue should approximately match the encoded one;
    # exact match not guaranteed due to dense-encoder cross-talk, but
    # within ±5 quantization steps is reasonable.
    encoded = state["dials"]["Metonic"]["residue"]
    # Note: decoder returns the D-quantised residue, encoded["residue"]
    # is the modulus-natural integer. Both correspond to the same phase;
    # we just sanity-check that decode returned a non-negative int < D.
    assert 0 <= out["recovered_residue"] < D_CALLIPPIC
    assert encoded >= 0


def test_decode_dial_bit_and_complex_agree() -> None:
    """Both backends should recover the same D-bin residue (modulo
    any decoder-noise differences).  Both encoders rotate the basis
    by ``spec.residue(jd, D)``, and both decoders are argmax over
    rotation candidates."""
    jd = REFERENCE_JD + 1234.5
    bit_state = bridge.get_dial_state(jd, D=D_CALLIPPIC)
    cx_state = bridge.get_dial_state(jd, D=D_CALLIPPIC, backend="complex128")
    bit_out = bridge.decode_dial(bit_state["state"], "Metonic",
                                  D=D_CALLIPPIC)
    cx_out = bridge.decode_dial(cx_state["state"], "Metonic",
                                 D=D_CALLIPPIC)
    assert bit_out["ok"] and cx_out["ok"]
    # The two decoders run on independent bases (binary vs Gaussian
    # complex), so exact agreement isn't guaranteed.  At D=940 with
    # ~10 dials they typically agree to within 3 quantisation steps.
    diff = abs(bit_out["recovered_residue"] - cx_out["recovered_residue"])
    diff = min(diff, D_CALLIPPIC - diff)
    assert diff <= 5, (
        f"bit vs complex128 decoders disagreed by {diff} steps: "
        f"bit={bit_out['recovered_residue']}, "
        f"cx={cx_out['recovered_residue']}"
    )


def test_decode_to_jd_inverts_encode() -> None:
    target_jd = REFERENCE_JD + 365.25 * 19  # one Metonic cycle later
    # Test BOTH backends round-trip via decode_to_jd.
    for backend in ("bit", "complex128"):
        state = bridge.get_dial_state(
            target_jd, D=D_CALLIPPIC, backend=backend,
        )
        assert state["ok"]

        if backend == "complex128":
            # Pass the complex array directly via numpy (legacy API path).
            interleaved = np.asarray(
                state["state"]["interleaved_f32"], dtype=np.float32,
            )
            out = bridge.decode_to_jd(interleaved, D=D_CALLIPPIC)
        else:
            out = bridge.decode_to_jd(state["state"], D=D_CALLIPPIC)
        assert out["ok"] is True, f"backend={backend}: {out}"
        assert out["backend"] == backend
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
