"""v0.7.0rc31 — quaternion/octonion DFT composites (#863, F380).

The native transform for a Klein-4 object: its ℍ coefficient algebra resolves
BOTH Z₂ chirality axes the complex FFT collapses (the flat shadow). Klein-4 =
Q₈/{±1} ≅ Z₂×Z₂. These are composites over the qm.octonion left/right-mult
atoms — scientific tier (§22: numpy on call), but `import srmech.amsc.cascade`
stays numpy-free.
"""
import math
import sys

import pytest

from srmech.amsc.cascade import quaternion_dft, octonion_dft


# --- Klein-4 <-> quaternion encoding (bit0 -> i-comp sign, bit1 -> j-comp sign) ---

def _enc(s):
    """Klein-4 sector s∈{0,1,2,3} -> quaternion [0, ±1(i), ±1(j), 0]."""
    return [0.0, 1.0 - 2 * (s & 1), 1.0 - 2 * ((s >> 1) & 1), 0.0]


def _dec(q):
    """Quaternion -> Klein-4 sector (sign of i-comp = bit0, sign of j-comp = bit1)."""
    bit0 = 0 if q[1] > 0 else 1
    bit1 = 0 if q[2] > 0 else 1
    return bit0 | (bit1 << 1)


# --- the cascade import stays numpy-free (rc30 core intact) -------------------

def test_cascade_import_is_numpy_free():
    """Importing the cascade package must NOT pull numpy (the DFT composites
    import it lazily inside the ops; §22 scientific tier)."""
    # If numpy is already loaded by another test, we can't re-check the import
    # side-effect — but we CAN assert the module source defers the import.
    import inspect
    from srmech.amsc.cascade import hypercomplex_dft
    src = inspect.getsource(hypercomplex_dft)
    # No top-level `import numpy` — only the lazy `_require_numpy` helper.
    top = src.split("def _require_numpy")[0]
    assert "import numpy" not in top, "hypercomplex_dft imports numpy at module load"


# --- QDFT round-trip recovers ALL FOUR components (both Z₂ axes) --------------

@pytest.mark.parametrize("form", ["left", "right"])
def test_quaternion_dft_round_trip(form):
    import random
    rng = random.Random(0)
    q = [[rng.uniform(-1, 1) for _ in range(4)] for _ in range(6)]
    X = quaternion_dft(q, form=form)
    qr = quaternion_dft(X, form=form, inverse=True)
    assert len(qr) == len(q)
    for r, o in zip(qr, q):
        assert len(r) == 4
        for a, b in zip(r, o):
            assert abs(a - b) < 1e-9


@pytest.mark.parametrize("mu_axis", ["i", "j", "k", "ijk"])
def test_quaternion_dft_round_trip_each_axis(mu_axis):
    q = [[0.5, -1.0, 0.25, 0.75], [1.0, 0.0, -0.5, 0.5], [-0.25, 0.5, 1.0, -1.0]]
    X = quaternion_dft(q, form="left", mu_axis=mu_axis)
    qr = quaternion_dft(X, form="left", mu_axis=mu_axis, inverse=True)
    for r, o in zip(qr, q):
        for a, b in zip(r, o):
            assert abs(a - b) < 1e-9


# --- the load-bearing DoD: Klein-4 both axes preserved vs the flat shadow -----

def test_klein4_object_both_axes_preserved():
    """QDFT round-trips a Klein-4 object and recovers BOTH Z₂ axes."""
    sectors = [0, 1, 2, 3, 1, 2, 3, 0]
    ks = [_enc(s) for s in sectors]
    X = quaternion_dft(ks, form="left")
    kr = quaternion_dft(X, form="left", inverse=True)
    assert [_dec(q) for q in kr] == sectors


def test_complex_fft_collapses_one_axis_the_flat_shadow():
    """The measurable contrast: a COMPLEX FFT must first project the quaternion
    to ℂ (q0 + q1·i), which drops the j-component = bit1. Its round-trip
    recovers bit0 but bit1 is gone — the flat shadow the QDFT does NOT cast."""
    import cmath
    sectors = [0, 1, 2, 3, 1, 2, 3, 0]
    ks = [_enc(s) for s in sectors]
    # complex projection drops the j-comp (bit1):
    cz = [complex(q[0], q[1]) for q in ks]
    n = len(cz)
    cx = [sum(cz[m] * cmath.exp(-2j * math.pi * k * m / n) for m in range(n)) for k in range(n)]
    cr = [sum(cx[k] * cmath.exp(2j * math.pi * k * m / n) for k in range(n)) / n for m in range(n)]
    # bit0 (i-comp sign) survives the complex round-trip:
    rec_bit0 = [0 if c.imag > 0 else 1 for c in cr]
    assert rec_bit0 == [s & 1 for s in sectors]
    # ...but bit1 (j-comp) was projected away — it is NOT in cr at all.
    true_bit1 = [(s >> 1) & 1 for s in sectors]
    assert any(true_bit1), "test needs at least one set bit1"
    # The complex carrier has no second imaginary axis to hold bit1: confirm the
    # QDFT recovers it where the complex FFT structurally cannot.
    kr = quaternion_dft(quaternion_dft(ks, form="left"), form="left", inverse=True)
    qdft_bit1 = [(_dec(q) >> 1) & 1 for q in kr]
    assert qdft_bit1 == true_bit1  # QDFT keeps the axis the complex FFT dropped


# --- ODFT: the bracketing convention is meaningful (non-associativity, F378) --

def test_octonion_dft_one_sided_round_trip():
    import random
    rng = random.Random(1)
    o = [[rng.uniform(-1, 1) for _ in range(8)] for _ in range(4)]
    for form in ("left", "right"):
        X = octonion_dft(o, form=form)
        orr = octonion_dft(X, form=form, inverse=True)
        for r, src in zip(orr, o):
            assert len(r) == 8
            for a, b in zip(r, src):
                assert abs(a - b) < 1e-9


def test_octonion_dft_two_sided_bracketing_is_meaningful():
    """The two-sided ODFT (W_l·x·W_r) is NOT associative: left- vs
    right-associated bracketing give DIFFERENT results (F378). This is WHY the
    bracketing convention must be an explicit declared field, not assumed."""
    import random
    rng = random.Random(2)
    o = [[rng.uniform(-1, 1) for _ in range(8)] for _ in range(4)]
    la = octonion_dft(o, form="two_sided", bracketing="left_associated",
                      mu_axis="i", two_sided_right_axis="j")
    ra = octonion_dft(o, form="two_sided", bracketing="right_associated",
                      mu_axis="i", two_sided_right_axis="j")
    diff = max(abs(a - b) for u, v in zip(la, ra) for a, b in zip(u, v))
    assert diff > 1e-6, "octonion two-sided bracketing must be non-associative"


def test_octonion_dft_two_sided_inverse_raises():
    o = [[0.0] * 8 for _ in range(3)]
    with pytest.raises(NotImplementedError):
        octonion_dft(o, form="two_sided", inverse=True)


# --- input validation --------------------------------------------------------

def test_quaternion_dft_rejects_octonion_tail():
    bad = [[0, 1, 0, 0, 0, 0, 0, 1]]  # e7 != 0 -> not a quaternion
    with pytest.raises(ValueError):
        quaternion_dft(bad)


def test_invalid_form_and_axis_raise():
    with pytest.raises(ValueError):
        quaternion_dft([[0, 1, 0, 0]], form="two_sided")  # quaternion has no two_sided
    with pytest.raises(ValueError):
        quaternion_dft([[0, 1, 0, 0]], mu_axis="z")
    with pytest.raises(ValueError):
        octonion_dft([[0] * 8], form="bogus")
    with pytest.raises(ValueError):
        octonion_dft([[0] * 8], bracketing="middle")


def test_empty_input_returns_empty():
    assert quaternion_dft([]) == []
    assert octonion_dft([]) == []


# --- numpy-absent: scientific-tier ops raise a clear ImportError -------------

def test_dft_requires_numpy_clear_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)  # `import numpy` -> ImportError
    with pytest.raises(ImportError):
        quaternion_dft([[0, 1, 0, 0]])
