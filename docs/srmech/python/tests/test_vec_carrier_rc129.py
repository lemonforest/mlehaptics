"""rc129 — the numpy-free 1-D ``Vec`` carrier (carrier-FORMAT restore, #564).

``Vec`` is the 1-D peer of ``Mat``: a flat ``array('d')`` (real → ``n`` doubles;
complex → ``2n`` interleaved ``(re, im)`` doubles, C99 ``double _Complex`` order)
and **no numpy at all**. rc127 regressed ~17 Class-L ops from the numpy-carrier
to bare Python lists/tuples (losing ``.shape`` / 1-D structure / a C wire form);
rc129 restores the FORMAT by returning ``Mat`` (matrices) / the new ``Vec``
(vectors). These tests pin the ``Vec`` surface: construction (sequence / flat,
real / complex), plain-scalar indexing, iteration-yields-SCALARS, ``tolist`` /
``tobytes`` round-trip, ``.conj`` (Class-K imag sign-flip), value-equality, and
the ``.shape == (n,)`` / ``__len__`` contract — real AND complex.

The whole module is numpy-free; a companion subprocess cell proves the carrier
imports + runs with numpy genuinely absent at ``sys.meta_path``.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from array import array

import pytest

from srmech.amsc.vec import Vec


def test_from_sequence_real_shape_and_access():
    v = Vec.from_sequence([1.0, 2.0, 3.0])
    assert v.shape == (3,)            # 1-tuple, like a 1-D ndarray
    assert len(v) == 3
    assert not v.is_complex
    assert v[0] == 1.0 and v[2] == 3.0
    assert isinstance(v[0], float)    # PLAIN float, never a numpy scalar
    assert v.tolist() == [1.0, 2.0, 3.0]


def test_from_sequence_complex_autodetect_interleaved_layout():
    v = Vec.from_sequence([1 + 2j, 3 + 0j, 0 - 1j])
    assert v.is_complex and v.shape == (3,)
    assert v[0] == (1 + 2j) and v[2] == -1j
    assert isinstance(v[0], complex)
    # interleaved (re, im): 1,2, 3,0, 0,-1
    assert list(v.buffer) == [1.0, 2.0, 3.0, 0.0, 0.0, -1.0]


def test_iter_yields_scalars_not_rows():
    v = Vec.from_sequence([4.0, 5.0, 6.0])
    items = list(v)                   # __iter__ yields SCALARS (not rows)
    assert items == [4.0, 5.0, 6.0]
    assert all(isinstance(x, float) for x in items)
    c = Vec.from_sequence([1 + 1j, 2 - 2j])
    assert list(c) == [1 + 1j, 2 - 2j]
    assert all(isinstance(x, complex) for x in c)


def test_from_flat_round_trip_real_and_complex():
    v = Vec.from_flat([1, 2, 3], 3, is_complex=False)
    assert v.shape == (3,) and v.tolist() == [1.0, 2.0, 3.0]
    # complex: 2n interleaved doubles (re, im)
    c = Vec.from_flat([1.0, 2.0, 3.0, 4.0], 2, is_complex=True)
    assert c.shape == (2,) and c.tolist() == [1 + 2j, 3 + 4j]


def test_conj_is_class_k_sign_flip_on_imag():
    c = Vec.from_sequence([1 + 2j, -3 - 4j])
    assert c.conj().tolist() == [1 - 2j, -3 + 4j]
    # real conj is a faithful copy (distinct buffer)
    r = Vec.from_sequence([1.0, 2.0])
    rc = r.conj()
    assert rc.tolist() == [1.0, 2.0] and rc.buffer is not r.buffer


def test_equality_against_vec_and_sequence():
    v = Vec.from_sequence([1.0, 2.0, 3.0])
    assert v == Vec.from_sequence([1.0, 2.0, 3.0])
    assert v == [1.0, 2.0, 3.0]                 # scalar bool, never elementwise
    assert v != [1.0, 2.0, 4.0]
    assert v != Vec.from_sequence([1.0, 2.0])   # length mismatch
    c = Vec.from_sequence([1 + 1j, 2 - 2j])
    assert c == [1 + 1j, 2 - 2j]
    assert c != Vec.from_sequence([1.0, 2.0])   # complex vs real layout


def test_negative_index_and_out_of_range():
    v = Vec.from_sequence([10.0, 20.0, 30.0])
    assert v[-1] == 30.0 and v[-3] == 10.0
    with pytest.raises(AssertionError):
        _ = v[3]


def test_tobytes_and_buffer_contract():
    v = Vec.from_sequence([1.0, 2.0, 3.0])
    assert isinstance(v.buffer, array) and v.buffer.typecode == "d"
    assert v.tobytes() == v.buffer.tobytes()


def test_repr_and_unhashable():
    assert "Vec(3, real)" in repr(Vec.from_sequence([1.0, 2.0, 3.0]))
    assert "complex" in repr(Vec.from_sequence([1j]))
    with pytest.raises(TypeError):
        {Vec.from_sequence([1.0])}          # mutable buffer → unhashable


def test_empty_vec_real_and_complex():
    v = Vec.from_sequence([])
    assert v.shape == (0,) and len(v) == 0 and v.tolist() == []
    c = Vec(array("d"), 0, is_complex=True)
    assert c.shape == (0,) and c.is_complex and c.tolist() == []


# ── numpy-ABSENT reachability (the real numpy-free gate) ──────────────────────

_BLOCK_NUMPY = textwrap.dedent(
    """
    import sys
    class _NoNumpy:
        def find_spec(self, name, path=None, target=None):
            if name == "numpy" or name.startswith("numpy."):
                raise ModuleNotFoundError("No module named 'numpy'", name="numpy")
            return None
    sys.meta_path.insert(0, _NoNumpy())
    """
)


def test_vec_imports_and_runs_numpy_free():
    """``srmech.amsc.vec`` imports + the full ``Vec`` surface runs numpy-absent."""
    script = _BLOCK_NUMPY + textwrap.dedent(
        """
        try:
            import numpy
            raise SystemExit("numpy importable - block failed")
        except ModuleNotFoundError:
            pass
        from srmech.amsc.vec import Vec
        v = Vec.from_sequence([1.0, 2.0, 3.0])
        assert v.shape == (3,) and v[1] == 2.0 and list(v) == [1.0, 2.0, 3.0]
        c = Vec.from_sequence([1 + 2j, 3 - 4j])
        assert c.is_complex and c.conj().tolist() == [1 - 2j, 3 + 4j]
        assert v == [1.0, 2.0, 3.0] and v.tobytes() == v.buffer.tobytes()
        print("VEC_OK")
        """
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in sys.path if p)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, env=env
    )
    assert proc.returncode == 0, f"Vec not numpy-free:\n{proc.stderr}"
    assert "VEC_OK" in proc.stdout, proc.stdout
