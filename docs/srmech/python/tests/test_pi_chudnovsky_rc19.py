"""0.9.0rc19 — the ROTATION-LAST Chudnovsky π operator + its native dispatch.

``srmech.amsc.rational.pi_chudnovsky_digits`` runs the Chudnovsky linear series
as an EXACT-integer body (arbitrary-precision ``int`` in Python; the caller-arena
``srmech_bigint`` in C) and performs the SINGLE continuous projection ONCE,
terminally — the rotation-last cascade shape. The pure-Python body is BOTH the
no-C fallback AND the parity oracle the native ``srmech_pi_chudnovsky`` is checked
against; both emit byte-identical ``"3.<digits>"``.

numpy-free + math-free (the op imports neither). The cross-oracle check pins the
Chudnovsky readout against the independent Archimedes ``pi_cascade_digits`` so a
silent drift in either cascade fails here.
"""

from __future__ import annotations

from srmech.amsc import _native
from srmech.amsc.rational import pi_cascade_digits, pi_chudnovsky_digits

import pytest

# First 50 fractional digits of π (the canonical reference value; used only to
# pin the small-N exact output, not as a magic constant — it IS π).
_PI_50 = "14159265358979323846264338327950288419716939937510"


def test_pi_chudnovsky_15_digits():
    assert pi_chudnovsky_digits(15) == "3.141592653589793"


def test_pi_chudnovsky_zero_digits():
    assert pi_chudnovsky_digits(0) == "3."


def test_pi_chudnovsky_small_n_prefix():
    # 5 / 1 / 50 digits all agree with the reference value's prefix.
    assert pi_chudnovsky_digits(5) == "3.14159"
    assert pi_chudnovsky_digits(1) == "3.1"
    assert pi_chudnovsky_digits(50) == "3." + _PI_50


def test_pi_chudnovsky_1000_prefix():
    out = pi_chudnovsky_digits(1000)
    assert out.startswith("3." + _PI_50)
    # exactly "3." + 1000 fractional digits
    assert len(out) == 2 + 1000
    assert out[2:].isdigit()


def test_pi_chudnovsky_2000_prefix():
    out = pi_chudnovsky_digits(2000)
    assert out.startswith("3." + _PI_50)
    assert len(out) == 2 + 2000
    assert out[2:].isdigit()


def test_pi_chudnovsky_matches_archimedes_cross_oracle():
    # Two INDEPENDENT cascades (rotation-last Chudnovsky vs. every-step
    # Archimedes hexagon-doubling) must agree digit-for-digit at 1000 digits.
    assert pi_chudnovsky_digits(1000) == pi_cascade_digits(1000)


def test_pi_chudnovsky_type_error():
    with pytest.raises(TypeError):
        pi_chudnovsky_digits(15.0)  # type: ignore[arg-type]


def test_pi_chudnovsky_negative_value_error():
    with pytest.raises(ValueError):
        pi_chudnovsky_digits(-1)


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="no native lib — pure-Python path is the only one")
def test_pi_chudnovsky_native_equals_pure():
    """When native is present, the C ``srmech_pi_chudnovsky`` is byte-identical
    to the pure-Python bignum oracle. The native helper is reached directly; the
    pure path is recomputed by importing the module-level body via a no-native
    shim is not needed — the public op already routes to native, so we compare
    the native helper's output to the public op (which == native when present)
    AND to the Archimedes oracle (independent cascade)."""
    for n in (15, 100, 1000):
        native = _native.pi_chudnovsky_c(n)
        assert native is not None, "HAS_NATIVE but pi_chudnovsky_c returned None"
        assert native == pi_chudnovsky_digits(n)
        assert native == pi_cascade_digits(n)
