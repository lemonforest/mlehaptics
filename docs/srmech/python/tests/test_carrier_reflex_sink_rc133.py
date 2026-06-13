"""Carrier numpy-reflex-sink ratchet (#564 / rc133) — the package-side mirror of
the research-env F728 audit (`R-RBS-LM-CARRIERAUDIT_numpy_idiom_coverage.py`).

**Why this is a permanent test.** The carrier discipline exists to stop an LLM
dropping srmech and reaching for numpy. Every numpy idiom the carrier ANSWERS
routes through srmech silently; every idiom that RAISES bails the LLM to
``np.asarray(m.tolist())`` → numpy, defeating the carrier's purpose. So the
carrier's numpy-idiom coverage IS its reflex-absorption score. rc129→rc130 closed
``m[0]`` + ``@``; **rc133 closes the last 9 — elementwise/scalar arithmetic
(``+ - * /``, ``-x``), slicing (``m[:2]`` / ``m[:,j]`` column / ``v[:2]``), and
negative tuple indices (``m[-1,-1]``)** — making ``Mat``/``Vec`` a near-total
reflex sink. This test pins **17/17** so a regression that re-opens any idiom
(re-arming the numpy bail-out) fails loudly.

Runs with numpy genuinely absent (it is part of the numpy-FREE surface it certifies).
"""

import builtins

from srmech.amsc import laplacian as Lp
from srmech.amsc.mat import Mat
from srmech.amsc.vec import Vec


def _the_17_idioms():
    """The exact 17 numpy idioms the F728 audit scores, as ``(label, thunk)``."""
    m = Lp.dense_laplacian(3, [(0, 1), (1, 2), (2, 0)])
    m2 = Mat.from_rows([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    v = Lp.jacobi_eigvals(m)
    return [
        ("shape", lambda: m.shape),
        ("m[i,j]", lambda: m[0, 0]),
        ("m[i] row", lambda: m[0][0]),
        ("len/iterate", lambda: (len(m), sum(1 for _ in m))),
        (".T", lambda: m.T.shape),
        ("@ matmul", lambda: (m @ m2).shape),
        ("v @ v dot", lambda: v @ v),
        (".tolist", lambda: m.tolist()),
        ("a + b", lambda: m + m),
        ("a - b", lambda: m - m),
        ("a * scalar", lambda: m * 2),
        ("scalar * a", lambda: 2 * m),
        ("slice m[:2]", lambda: m[:2]),
        ("col m[:,0]", lambda: m[:, 0]),
        ("neg m[-1,-1]", lambda: m[-1, -1]),
        ("v slice v[:2]", lambda: v[:2]),
        ("v + v", lambda: v + v),
    ]


def test_carrier_absorbs_all_17_numpy_idioms():
    """Every one of the F728 17 numpy idioms is ANSWERED by ``Mat``/``Vec`` — none
    raises (a raise would bail the LLM to numpy). Pins 17/17."""
    gaps = []
    for label, thunk in _the_17_idioms():
        try:
            thunk()
        except Exception as exc:  # noqa: BLE001 — any raise is a reflex-bail gap
            gaps.append((label, f"{type(exc).__name__}: {exc}"))
    assert not gaps, (
        "carrier numpy-reflex-sink REGRESSED — these idioms RAISE (each bails an "
        "LLM back to np.asarray(x.tolist()) → numpy):\n"
        + "\n".join(f"  - {lbl}: {err}" for lbl, err in gaps)
    )


def test_carrier_arithmetic_is_correct_not_just_non_raising():
    """The reflex-sink ops compute the right values (elementwise, format-preserving)
    — ``*`` is Hadamard (numpy elementwise), matmul stays ``@``."""
    a = Mat.from_rows([[1.0, 2.0], [3.0, 4.0]])
    assert (a + a).tolist() == [[2.0, 4.0], [6.0, 8.0]]
    assert (a - a).tolist() == [[0.0, 0.0], [0.0, 0.0]]
    assert (a * 2).tolist() == [[2.0, 4.0], [6.0, 8.0]]
    assert (2 * a).tolist() == [[2.0, 4.0], [6.0, 8.0]]
    assert (a * a).tolist() == [[1.0, 4.0], [9.0, 16.0]]   # Hadamard, NOT matmul
    assert (a / 2).tolist() == [[0.5, 1.0], [1.5, 2.0]]
    assert (-a).tolist() == [[-1.0, -2.0], [-3.0, -4.0]]
    assert (5 - a).tolist() == [[4.0, 3.0], [2.0, 1.0]]    # reflected scalar
    # complex stays complex
    c = Mat.from_rows([[1j, 2.0], [3.0, 4j]], is_complex=True)
    assert (c + c).is_complex and (c * 2).is_complex

    w = Vec.from_sequence([1.0, 2.0, 3.0])
    assert (w + w).tolist() == [2.0, 4.0, 6.0]
    assert (w * 2).tolist() == [2.0, 4.0, 6.0]
    assert (-w).tolist() == [-1.0, -2.0, -3.0]
    assert (w - w).tolist() == [0.0, 0.0, 0.0]


def test_carrier_slicing_and_negative_indices_are_correct():
    """Row/column/sub-block slices preserve the carrier FORMAT (Mat→Mat row-slice,
    Mat→Vec column, Vec→Vec slice); negatives address from the end."""
    a = Mat.from_rows([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    assert isinstance(a[:2], Mat) and a[:2].tolist() == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    assert isinstance(a[:, 0], Vec) and a[:, 0].tolist() == [1.0, 4.0, 7.0]   # column
    assert isinstance(a[0, 1:], Vec) and a[0, 1:].tolist() == [2.0, 3.0]      # row slice
    assert isinstance(a[1:, 1:], Mat) and a[1:, 1:].tolist() == [[5.0, 6.0], [8.0, 9.0]]
    assert a[-1, -1] == 9.0 and a[-1].tolist() == [7.0, 8.0, 9.0]             # negatives

    w = Vec.from_sequence([10.0, 20.0, 30.0, 40.0])
    assert isinstance(w[1:3], Vec) and w[1:3].tolist() == [20.0, 30.0]
    assert w[-1] == 40.0 and w[-2] == 30.0


def test_reflex_sink_is_itself_numpy_free():
    """The whole reflex surface runs with numpy hard-blocked at import — it is part
    of the numpy-FREE guarantee it certifies (#564)."""
    real_import = builtins.__import__

    def _blocked(name, *args, **kwargs):
        if name == "numpy" or name.startswith("numpy."):
            raise ImportError("numpy is removed (#564 numpy-zero gate)")
        return real_import(name, *args, **kwargs)

    builtins.__import__ = _blocked
    try:
        gaps = [lbl for lbl, thunk in _the_17_idioms()
                if not _silently_ok(thunk)]
        assert not gaps, f"reflex-sink idioms raised numpy-absent: {gaps}"
    finally:
        builtins.__import__ = real_import


def _silently_ok(thunk):
    try:
        thunk()
        return True
    except Exception:  # noqa: BLE001
        return False
