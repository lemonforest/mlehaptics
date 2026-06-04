"""rc36 — DFT / IDFT / Kronecker as A-N cascades (the Antikythera epicycle-sum).

dft = Class I (cyclic index) o Class N (twiddle) o Class C (i-rotation) o
Class M (bundle); kron = Class I (mixed-radix index) o Class M (products).
Pure-Python on rc34's cexp; verified vs numpy.fft / numpy.kron.
"""
import numpy as np
import pytest

from srmech.amsc.cascade.spectral_cascades import dft, idft, kron


def test_dft_matches_numpy_fft():
    rng = np.random.default_rng(0)
    for n in (1, 2, 4, 8, 13):
        x = (rng.standard_normal(n) + 1j * rng.standard_normal(n)).tolist()
        got = np.array(dft(x))
        want = np.fft.fft(np.array(x))
        assert np.max(np.abs(got - want)) <= 1e-9, n


def test_idft_inverts_dft():
    rng = np.random.default_rng(1)
    for n in (1, 3, 8, 16):
        x = (rng.standard_normal(n) + 1j * rng.standard_normal(n))
        rt = np.array(idft(dft(x.tolist())))
        assert np.max(np.abs(rt - x)) <= 1e-9, n


def test_dft_empty():
    assert dft([]) == []


def test_idft_matches_numpy_ifft():
    rng = np.random.default_rng(2)
    spec = (rng.standard_normal(8) + 1j * rng.standard_normal(8))
    got = np.array(idft(spec.tolist()))
    want = np.fft.ifft(spec)
    assert np.max(np.abs(got - want)) <= 1e-9


def test_kron_matches_numpy():
    cases = [
        ([[1, 2], [3, 4]], [[0, 5], [6, 7]]),
        ([[1]], [[2, 3], [4, 5]]),
        ([[1 + 1j, 2], [0, -1j]], [[1, 0], [0, 1]]),
    ]
    for a, b in cases:
        got = np.array(kron(a, b), dtype=complex)
        want = np.kron(np.array(a, dtype=complex), np.array(b, dtype=complex))
        assert np.max(np.abs(got - want)) == 0.0, (a, b)


def test_dft_no_libm_pi_in_call_graph():
    """The DFT twiddle angle uses the Class-N pi-cascade, never math.pi / np.pi."""
    import ast
    import inspect

    from srmech.amsc.cascade import spectral_cascades as sc

    tree = ast.parse(inspect.getsource(sc))
    bad = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in {"pi", "tau"}:
            base = node.value
            if isinstance(base, ast.Name) and base.id in {"math", "np", "numpy", "cmath"}:
                bad.add(f"{base.id}.{node.attr}")
    assert not bad, f"forbidden libm pi/tau in spectral_cascades.py: {bad}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
