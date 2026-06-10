"""rc69 — the numpy-free 2-D ``Mat`` carrier (carrier-removal arc Phase 0, #564).

``Mat`` is the 2-D peer of ``HV``: a flat ``array('d')`` (row-major; interleaved
``(re, im)`` for complex, C99 ``double _Complex`` order) with an opt-in
``to_numpy()`` bridge and **no numpy at import**. These tests pin: construction
(rows / flat, real / complex), plain-scalar element access, round-trip out
(tolist / tobytes / buffer), transpose + conj, value-equality, the numpy bridge
correctness when numpy is present, and the clean ImportError when it is absent.
"""

from __future__ import annotations

import sys
from array import array

import pytest

from srmech.amsc.mat import Mat


def test_from_rows_real_shape_and_access():
    m = Mat.from_rows([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    assert m.shape == (2, 3)
    assert not m.is_complex
    assert len(m) == 2
    assert m[0, 0] == 1.0 and m[1, 2] == 6.0
    assert isinstance(m[0, 0], float)  # PLAIN float, never a numpy scalar
    assert m.row(1) == [4.0, 5.0, 6.0]
    assert m.tolist() == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]


def test_from_rows_complex_autodetect_interleaved_layout():
    m = Mat.from_rows([[1 + 2j, 3 + 0j], [0 - 1j, 4 + 4j]])
    assert m.is_complex and m.shape == (2, 2)
    assert m[0, 0] == (1 + 2j) and m[1, 0] == -1j
    assert isinstance(m[0, 0], complex)
    # interleaved (re, im) row-major: 1,2, 3,0, 0,-1, 4,4
    assert list(m.buffer) == [1.0, 2.0, 3.0, 0.0, 0.0, -1.0, 4.0, 4.0]


def test_from_flat_round_trip():
    m = Mat.from_flat([1, 2, 3, 4, 5, 6], 3, 2)
    assert m.shape == (3, 2)
    assert m.tolist() == [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]


def test_transpose_real_and_complex():
    m = Mat.from_rows([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    assert m.T.tolist() == [[1.0, 4.0], [2.0, 5.0], [3.0, 6.0]]
    c = Mat.from_rows([[1 + 1j, 2 + 0j], [0 + 3j, 4 - 4j]])
    assert c.T.tolist() == [[1 + 1j, 3j], [2 + 0j, 4 - 4j]]


def test_conj_is_class_k_sign_flip_on_imag():
    c = Mat.from_rows([[1 + 2j, -3 - 4j]])
    assert c.conj().tolist() == [[1 - 2j, -3 + 4j]]
    # real conj is a faithful copy (distinct buffer)
    r = Mat.from_rows([[1.0, 2.0]])
    rc = r.conj()
    assert rc.tolist() == [[1.0, 2.0]] and rc.buffer is not r.buffer


def test_equality_against_mat_list_and_numpy():
    m = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
    assert m == Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
    assert m == [[1.0, 2.0], [3.0, 4.0]]
    assert m != [[1.0, 2.0], [3.0, 5.0]]
    assert m != Mat.from_rows([[1.0, 2.0, 0.0], [3.0, 4.0, 0.0]])  # shape mismatch


def test_ragged_rows_rejected():
    with pytest.raises(AssertionError):
        Mat.from_rows([[1.0, 2.0], [3.0]])


def test_buffer_is_contiguous_array_d():
    m = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
    assert isinstance(m.buffer, array) and m.buffer.typecode == "d"
    assert m.tobytes() == m.buffer.tobytes()


def test_to_numpy_real_and_complex_when_present():
    np = pytest.importorskip("numpy")
    m = Mat.from_rows([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    arr = m.to_numpy()
    assert arr.shape == (2, 3) and arr.dtype == np.float64
    assert np.array_equal(arr, np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]))
    c = Mat.from_rows([[1 + 2j, 3 - 1j], [0 + 0j, 4 + 4j]])
    carr = c.to_numpy()
    assert carr.dtype == np.complex128 and carr.shape == (2, 2)
    assert np.array_equal(carr, np.array([[1 + 2j, 3 - 1j], [0, 4 + 4j]]))
    # equality bridge accepts the numpy array back
    assert m == arr


def test_to_numpy_raises_cleanly_when_absent(monkeypatch):
    monkeypatch.setitem(sys.modules, "numpy", None)  # `import numpy` → ImportError
    m = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
    # the numpy-free path still works with numpy hidden
    assert m.tolist() == [[1.0, 2.0], [3.0, 4.0]]
    assert list(m.buffer) == [1.0, 2.0, 3.0, 4.0]
    with pytest.raises(ImportError, match="numpy-free path is Mat.tolist"):
        m.to_numpy()
