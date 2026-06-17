"""Tier 2b HD-pipeline byte-parity (v0.7.0).

Pins agreement between the Python `_research/bip_hd_lift` BIP-and-lift
pipeline and the matching C entry points (`es_encode_state_hd`,
`es_bind_observer`, `es_get_eclipse_probability`).

The parity smoke test (test_parity_smoke.py) covers the bridge-level
agreement; this file covers the underlying primitives directly so any
regression points specifically at which step diverged.

Skipped when the native binary isn't loaded.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import _native_bip


# v0.31.0rc4: numpy-free oracle helpers — the HD vectors are list[complex].
def _max_abs_diff(a, b) -> float:
    """max |a[k] - b[k]| over two complex sequences."""
    return max((abs(complex(x) - complex(y)) for x, y in zip(a, b)), default=0.0)


def _norm(v) -> float:
    """Euclidean norm of a complex vector (np.linalg.norm for 1-D)."""
    return math.sqrt(sum((complex(z).real ** 2 + complex(z).imag ** 2) for z in v))


def _vdot(a, b) -> complex:
    """Conjugate-linear inner product matching np.vdot (conj first arg)."""
    return sum(complex(x).conjugate() * complex(y) for x, y in zip(a, b))
from ephemerides_spectral._research.bip_hd_lift import (
    encode_state_hd as py_encode_state_hd,
    bind_observer as py_bind_observer,
    eclipse_probability as py_eclipse_probability,
)
from ephemerides_spectral._research.bip_instrument import (
    EphemerisBIPInstrument, REFERENCE_JD,
)
from ephemerides_spectral._research.bodies import BODIES


pytestmark = pytest.mark.skipif(
    not _native_bip.HAS_NATIVE,
    reason="native library not loaded; HD parity requires C path",
)


# Tolerance: float-ULP across D=4096 elements. Each accumulator step
# accumulates 38 body sums and a normalisation; worst-case the float32
# round-off compounds to ~1e-5. Empirically the diff is ~1e-9.
_HD_TOLERANCE = 1e-5
_PROB_TOLERANCE = 1e-7


@pytest.fixture(scope="module")
def jd_J2000():
    return REFERENCE_JD


@pytest.fixture(scope="module")
def D():
    return 4096


@pytest.fixture(scope="module")
def bip_inst():
    return EphemerisBIPInstrument(
        D=2**12, kernel="de441", force_high_res=False,
    )


@pytest.fixture(scope="module")
def py_phases(bip_inst, jd_J2000):
    return bip_inst.encode_state(jd_J2000)


def test_hd_encode_state_byte_close(py_phases, D, jd_J2000) -> None:
    py_state = py_encode_state_hd(py_phases, D)
    c_state = _native_bip.native_encode_state_hd(jd_J2000 - REFERENCE_JD, D)
    assert len(py_state) == len(c_state) == D
    diff = _max_abs_diff(py_state, c_state)
    assert diff < _HD_TOLERANCE, f"HD encode diverged: max|py-c|={diff:.2e}"
    # Both should be unit-norm (up to float32 round-off).
    assert abs(_norm(py_state) - 1.0) < 1e-5
    assert abs(_norm(c_state) - 1.0) < 1e-5


@pytest.mark.parametrize("body,lat,lon", [
    ("terra", 51.5, -0.1),    # London
    ("terra", -33.9, 151.2),  # Sydney
    ("mars", 0.0, 0.0),       # equator/prime
    ("luna", 45.0, 90.0),     # off-grid coord
])
def test_hd_bind_observer_byte_close(py_phases, D, jd_J2000, bip_inst,
                                     body, lat, lon) -> None:
    py_state = py_encode_state_hd(py_phases, D)
    c_state = _native_bip.native_encode_state_hd(jd_J2000 - REFERENCE_JD, D)
    body_idx = bip_inst.body_to_idx[body]
    py_local = py_bind_observer(py_state, body_idx, lat, lon, D)
    c_local = _native_bip.native_bind_observer(c_state, body_idx, lat, lon)
    diff = _max_abs_diff(py_local, c_local)
    assert diff < _HD_TOLERANCE, (
        f"observer-bind diverged at ({body}, {lat}, {lon}): "
        f"max|py-c|={diff:.2e}"
    )


def test_hd_eclipse_probability_close(py_phases, D, jd_J2000, bip_inst) -> None:
    py_state = py_encode_state_hd(py_phases, D)
    c_state = _native_bip.native_encode_state_hd(jd_J2000 - REFERENCE_JD, D)
    sun_idx = bip_inst.body_to_idx["sun"]
    moon_idx = bip_inst.body_to_idx["luna"]
    py_prob = py_eclipse_probability(py_state, D, sun_idx, moon_idx)
    c_prob = _native_bip.native_get_eclipse_probability(
        c_state, sun_idx, moon_idx,
    )
    diff = abs(py_prob - c_prob)
    assert diff < _PROB_TOLERANCE, (
        f"eclipse probability diverged: py={py_prob:.10f} c={c_prob:.10f} "
        f"diff={diff:.2e}"
    )
    # Both in [0, 1].
    assert 0.0 <= py_prob <= 1.0
    assert 0.0 <= c_prob <= 1.0


def test_hd_encode_state_idempotent_under_normalisation(D, jd_J2000) -> None:
    """Encoding twice at the same JD produces the same state (deterministic)."""
    s1 = _native_bip.native_encode_state_hd(jd_J2000 - REFERENCE_JD, D)
    s2 = _native_bip.native_encode_state_hd(jd_J2000 - REFERENCE_JD, D)
    assert list(s1) == list(s2)


def test_hd_encode_at_different_jds_distinct_states(D, jd_J2000) -> None:
    """Encoding at JDs separated by a year gives distinct hypervectors."""
    s1 = _native_bip.native_encode_state_hd(jd_J2000 - REFERENCE_JD, D)
    s2 = _native_bip.native_encode_state_hd((jd_J2000 + 365.25) - REFERENCE_JD, D)
    # Cosine similarity should be < 1 (states diverged).
    sim = abs(_vdot(s1, s2))
    assert sim < 0.99, f"states at +1yr should diverge; |<s1,s2>|={sim:.4f}"
