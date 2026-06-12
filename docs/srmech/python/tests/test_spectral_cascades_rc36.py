"""rc36 — DFT / IDFT / Kronecker as A-N cascades (the Antikythera epicycle-sum).

dft = Class I (cyclic index) o Class N (twiddle) o Class C (i-rotation) o
Class M (bundle); kron = Class I (mixed-radix index) o Class M (products).
Pure-Python on rc34's cexp; verified vs a cmath DFT-by-definition oracle and a
hand-rolled Kronecker oracle (numpy is GONE from srmech — these tests run and
pass with numpy NOT installed).
"""
import cmath
import math
import random

import pytest

from srmech.amsc.cascade.spectral_cascades import dft, idft, kron


# --- numpy-free oracles ---------------------------------------------------------

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


def _kron_ref(a, b):
    """Kronecker product by definition: (A⊗B)[i·p+k, j·q+l] = A[i,j]·B[k,l]."""
    ma, na = len(a), len(a[0])
    mb, nb = len(b), len(b[0])
    out = [[0j for _ in range(na * nb)] for _ in range(ma * mb)]
    for i in range(ma):
        for j in range(na):
            for k in range(mb):
                for ell in range(nb):
                    out[i * mb + k][j * nb + ell] = complex(a[i][j]) * complex(b[k][ell])
    return out


def _max_abs_diff(got, want):
    return max((abs(complex(g) - complex(w)) for g, w in zip(got, want)), default=0.0)


def _rand_complex(rng, n):
    return [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]


def test_dft_matches_definition():
    rng = random.Random(0)
    for n in (1, 2, 4, 8, 13):
        x = _rand_complex(rng, n)
        assert _max_abs_diff(dft(x), _dft_ref(x)) <= 1e-9, n


def test_idft_inverts_dft():
    rng = random.Random(1)
    for n in (1, 3, 8, 16):
        x = _rand_complex(rng, n)
        rt = idft(dft(x))
        assert _max_abs_diff(rt, x) <= 1e-9, n


def test_dft_empty():
    assert dft([]) == []


def test_idft_matches_definition():
    rng = random.Random(2)
    spec = _rand_complex(rng, 8)
    assert _max_abs_diff(idft(spec), _dft_ref(spec, inverse=True)) <= 1e-9


def test_kron_matches_definition():
    cases = [
        ([[1, 2], [3, 4]], [[0, 5], [6, 7]]),
        ([[1]], [[2, 3], [4, 5]]),
        ([[1 + 1j, 2], [0, -1j]], [[1, 0], [0, 1]]),
    ]
    for a, b in cases:
        got = kron(a, b)
        want = _kron_ref(a, b)
        # Kronecker is exact integer/Gaussian-integer multiplication — bit-exact.
        for grow, wrow in zip(got, want):
            for g, w in zip(grow, wrow):
                assert complex(g) == complex(w), (a, b)


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
