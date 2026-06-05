"""rc37 — radix-2 Cooley-Tukey FFT as an A-N cascade.

fft = the rc36 DFT cascade (I o N o C o M) + Class J (the radix N=2*(N/2)
parity split) + Class K (the butterfly recursion depth). Power-of-2 sizes take
the O(N log N) butterfly; every other N falls back to the direct O(N^2) dft, so
fft is a drop-in for numpy.fft.fft at ANY length. Verified vs numpy.fft.
"""
import numpy as np
import pytest

from srmech.amsc.cascade.spectral_cascades import (
    dft,
    fft,
    ifft,
    _is_power_of_two,
)


def test_fft_matches_numpy_all_lengths():
    """Power-of-2 (butterfly) AND non-power-of-2 (dft fallback) both match."""
    rng = np.random.default_rng(11)
    for n in (1, 2, 3, 4, 5, 7, 8, 13, 16, 32, 64):
        x = (rng.standard_normal(n) + 1j * rng.standard_normal(n)).tolist()
        got = np.array(fft(x))
        want = np.fft.fft(np.array(x))
        assert np.max(np.abs(got - want)) <= 1e-9, n


def test_ifft_matches_numpy():
    rng = np.random.default_rng(12)
    for n in (1, 2, 4, 6, 8, 16):
        spec = (rng.standard_normal(n) + 1j * rng.standard_normal(n)).tolist()
        got = np.array(ifft(spec))
        want = np.fft.ifft(np.array(spec))
        assert np.max(np.abs(got - want)) <= 1e-9, n


def test_fft_equals_dft():
    """The fast path must be value-faithful to the direct DFT (same maths)."""
    rng = np.random.default_rng(13)
    for n in (4, 8, 16, 32):
        x = (rng.standard_normal(n) + 1j * rng.standard_normal(n)).tolist()
        assert np.max(np.abs(np.array(fft(x)) - np.array(dft(x)))) <= 1e-9, n


def test_ifft_inverts_fft():
    rng = np.random.default_rng(14)
    for n in (1, 8, 16, 64):
        x = (rng.standard_normal(n) + 1j * rng.standard_normal(n))
        rt = np.array(ifft(fft(x.tolist())))
        assert np.max(np.abs(rt - x)) <= 1e-9, n


def test_fft_empty():
    assert fft([]) == []
    assert ifft([]) == []


def test_is_power_of_two():
    powers = {1, 2, 4, 8, 16, 32, 64, 128, 256, 1024}
    for n in range(1, 130):
        assert _is_power_of_two(n) == (n in powers), n
    assert not _is_power_of_two(0)


def test_fft_no_libm_pi_in_call_graph():
    """The FFT twiddle uses the Class-N pi-cascade, never math.pi / np.pi."""
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
