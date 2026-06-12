"""rc37 — radix-2 Cooley-Tukey FFT as an A-N cascade.

fft = the rc36 DFT cascade (I o N o C o M) + Class J (the radix N=2*(N/2)
parity split) + Class K (the butterfly recursion depth). Power-of-2 sizes take
the O(N log N) butterfly; every other N falls back to the direct O(N^2) dft, so
fft is a drop-in for the DFT-by-definition at ANY length. Verified vs a cmath
DFT-by-definition oracle (numpy is GONE from srmech — these tests run and pass
with numpy NOT installed).
"""
import cmath
import math
import random

import pytest

from srmech.amsc.cascade.spectral_cascades import (
    dft,
    fft,
    ifft,
    _is_power_of_two,
)


def _dft_ref(x, inverse=False):
    """DFT by definition via cmath: X[k] = Σ_n x[n]·e^{∓2πi·kn/N} (÷N if inverse)."""
    n = len(x)
    sign = 1.0 if inverse else -1.0
    out = []
    for k in range(n):
        acc = 0j
        for idx in range(n):
            acc += complex(x[idx]) * cmath.exp(sign * 2j * math.pi * k * idx / n)
        out.append(acc / n if inverse else acc)
    return out


def _max_abs_diff(got, want):
    return max((abs(complex(g) - complex(w)) for g, w in zip(got, want)), default=0.0)


def _rand_complex(rng, n):
    return [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]


def test_fft_matches_definition_all_lengths():
    """Power-of-2 (butterfly) AND non-power-of-2 (dft fallback) both match."""
    rng = random.Random(11)
    for n in (1, 2, 3, 4, 5, 7, 8, 13, 16, 32, 64):
        x = _rand_complex(rng, n)
        assert _max_abs_diff(fft(x), _dft_ref(x)) <= 1e-9, n


def test_ifft_matches_definition():
    rng = random.Random(12)
    for n in (1, 2, 4, 6, 8, 16):
        spec = _rand_complex(rng, n)
        assert _max_abs_diff(ifft(spec), _dft_ref(spec, inverse=True)) <= 1e-9, n


def test_fft_equals_dft():
    """The fast path must be value-faithful to the direct DFT (same maths)."""
    rng = random.Random(13)
    for n in (4, 8, 16, 32):
        x = _rand_complex(rng, n)
        assert _max_abs_diff(fft(x), dft(x)) <= 1e-9, n


def test_ifft_inverts_fft():
    rng = random.Random(14)
    for n in (1, 8, 16, 64):
        x = _rand_complex(rng, n)
        rt = ifft(fft(x))
        assert _max_abs_diff(rt, x) <= 1e-9, n


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
