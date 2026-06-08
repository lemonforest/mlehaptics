"""rc6 — coupled_wave (W17) + multiplex_streams (W18).

W17: the full-chirality (E,B) drive — handedness is a SETTABLE CONVENTION
(both first-class, endianness posture), never hardcoded; the chosen sense is
STABLE across theta (the fix vs sign(wave) flipping 2x/cycle). W18: recombine
N steering WAVES into one driver — real-field interference for superpose (NOT
hdc.bundle), clause-slot roles, the driver/emission layer boundary.
"""

import math

import pytest

from srmech.amsc.cascade import coupled_wave, multiplex_streams


# ---- W17: coupled_wave -------------------------------------------------

def test_coupled_wave_quadrature_legs():
    # default ("sin","cos"): E=sin, B=cos
    e, b, h, quad = coupled_wave(0.0)
    assert e == pytest.approx(0.0) and b == pytest.approx(1.0)
    assert quad == (0, 1) and h == 1
    e, b, _, quad = coupled_wave(math.pi / 2)
    assert e == pytest.approx(1.0) and abs(b) < 1e-9
    assert quad[0] == 1


def test_handedness_is_a_settable_convention_both_first_class():
    # -handedness == Class-K phase flip theta -> -theta (mirror chirality):
    # E flips sign, B unchanged. NEVER hardcoded.
    eR, bR, hR, _ = coupled_wave(math.pi / 4, handedness=+1)
    eL, bL, hL, _ = coupled_wave(math.pi / 4, handedness=-1)
    assert hR == 1 and hL == -1
    assert eL == pytest.approx(-eR)
    assert bL == pytest.approx(bR)


def test_handedness_is_stable_across_the_full_circle():
    # THE W17 fix: the bearing does NOT flip 2x/cycle the way sign(wave) does.
    seen = {coupled_wave(t * math.pi / 8, handedness=+1)[2] for t in range(16)}
    assert seen == {1}
    seen_left = {coupled_wave(t * math.pi / 8, handedness=-1)[2] for t in range(16)}
    assert seen_left == {-1}


def test_handedness_zero_is_not_a_convention():
    with pytest.raises(ValueError):
        coupled_wave(1.0, handedness=0)


def test_components_must_be_a_quadrature_pair():
    coupled_wave(1.0, components=("cos", "sin"))  # ok (the other handedness axis)
    with pytest.raises(ValueError):
        coupled_wave(1.0, components=("sin", "sin"))   # not quadrature
    with pytest.raises(ValueError):
        coupled_wave(1.0, components=("sin", "tan"))   # not sin/cos


def test_klein4_quadrant_signs_are_class_k():
    # (sign E, sign B) ∈ the 4 Klein-4 sectors
    quads = {coupled_wave(t * math.pi / 4)[3] for t in range(8)}
    assert quads <= {(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1),
                     (-1, 0), (-1, 1)}


# ---- W18: multiplex_streams --------------------------------------------

_S = [[1.0, 2.0, 3.0], [10.0, 20.0, 30.0], [100.0, 200.0, 300.0]]


def test_roundrobin_is_the_t_mod_n_multiplex_default():
    out = multiplex_streams(_S)
    assert out["mode"] == "roundrobin"
    assert out["driver"] == [1.0, 20.0, 300.0]   # streams[t % 3][t]


def test_superpose_is_real_interference_not_hdc_bundle():
    # elementwise SUM ([111,222,333]) renormalised by peak magnitude (333)
    out = multiplex_streams(_S, mode="superpose")["driver"]
    assert out == pytest.approx([111 / 333, 222 / 333, 1.0])


def test_pickbest_is_max_magnitude_bearing():
    assert multiplex_streams(_S, mode="pickbest")["driver"] == [100.0, 200.0, 300.0]


def test_roles_bind_each_stream_to_a_clause_slot():
    rb = multiplex_streams(_S, roles=("S", "V", "O"))["role_bound"]
    assert rb["stream_roles"] == ("S", "V", "O")
    assert [b["clause_slot"] for b in rb["bindings"]] == [0, 1, 2]
    assert rb["bindings"][1]["role"] == "V"
    assert isinstance(rb["bindings"][1]["tag"], (bytes, bytearray))  # hdc.bind tag


def test_layer_boundary_is_a_steering_driver_not_tokens():
    out = multiplex_streams(_S)
    assert "steering-driver" in out["layer"]


def test_w17_w18_compose_each_stream_a_coupled_bearing():
    streams = [[coupled_wave(p + t * 0.3)[0] for t in range(6)]
               for p in (0.0, 2.0, 4.0)]
    out = multiplex_streams(streams, mode="roundrobin", roles=("S", "V", "O"))
    assert out["n_streams"] == 3 and out["length"] == 6
    assert len(out["driver"]) == 6


def test_multiplex_validation():
    with pytest.raises(ValueError):
        multiplex_streams([])
    with pytest.raises(ValueError):
        multiplex_streams(_S, mode="nope")
    with pytest.raises(ValueError):
        multiplex_streams(_S, roles=("S", "V"))           # length mismatch
    with pytest.raises(ValueError):
        multiplex_streams([[1.0, 2.0], [3.0]])            # unequal length
