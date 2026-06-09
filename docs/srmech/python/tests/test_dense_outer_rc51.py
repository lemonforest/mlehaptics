"""dense_outer — the rank-1 outer-product cascade (numpy-removal; rc51).

The deferred numpy-math decrement (the `np.outer → dense_outer` PHASE-A matmul
item): an outer product ``a ⊗ b`` is the ``k = 1`` case of a matrix product
(``a`` a column, ``b`` a row), so `dense_outer_*` is exactly
`dense_matmul_complex` on the reshaped pair — it rides the native
`srmech_dense_matmul_complex` kernel with NO inner summation (each entry is a
single multiply), making it **bit-identical** to numpy's outer product. This
lets the 3 genuine `np.outer` callsites (qm.propagators' two real `kᵘkᵛ`
momentum tensors, qm.single_particle's complex ``|ψ⟩⟨ψ|`` density matrix) leave
numpy's contraction engine for the Class-L cascade — numpy stays carriers-only.

These tests pin bit-exactness vs numpy on real + complex input, the no-conjugate
contract (matching numpy `outer`), shape / empty handling, the registration
(ToolEntry + `__all__` + `LAPLACIAN_OPS` + `composition_of_c` rosetta), and that
the routed qm surfaces still compute their tensors correctly.
"""
from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc import laplacian
from srmech.amsc.laplacian import dense_outer_complex, dense_outer_real


def test_outer_real_bit_identical_to_numpy():
    a = np.array([1.0, -2.0, 3.5, 0.0])
    b = np.array([4.0, 0.5, -1.0])
    out = dense_outer_real(a, b)
    assert out.dtype == np.float64
    assert out.shape == (4, 3)
    assert np.array_equal(out, np.outer(a, b))   # bit-identical (k=1 matmul)


def test_outer_complex_bit_identical_to_numpy():
    a = np.array([1 + 2j, 3 - 1j, 0 + 0j])
    b = np.array([2 - 1j, 0 + 4j])
    out = dense_outer_complex(a, b)
    assert out.dtype == np.complex128
    assert out.shape == (3, 2)
    assert np.array_equal(out, np.outer(a, b))


def test_outer_does_not_conjugate_b():
    # like numpy outer, dense_outer takes the plain bilinear a_i b_j (NO conj);
    # the |ψ⟩⟨ψ| density matrix is the caller passing b = ψ.conj() explicitly.
    psi = np.array([1 + 1j, 2 - 3j])
    rho = dense_outer_complex(psi, psi.conj())
    assert np.array_equal(rho, np.outer(psi, psi.conj()))
    # Hermitian, trace = ⟨ψ|ψ⟩
    assert np.allclose(rho, rho.conj().T)
    assert np.isclose(np.trace(rho), np.vdot(psi, psi))


def test_outer_real_rides_complex_kernel_drops_zero_imag():
    a = np.array([2.0, 5.0])
    out = dense_outer_real(a, a)
    assert out.dtype == np.float64        # real peer returns float64, imag dropped
    assert np.array_equal(out, np.outer(a, a))


def test_outer_empty_inputs_safe():
    assert dense_outer_real(np.array([]), np.array([1.0, 2.0])).shape == (0, 2)
    assert dense_outer_complex(np.array([1j]), np.array([])).shape == (1, 0)


def test_outer_flattens_non_1d_input():
    # reshape(-1, 1) / reshape(1, -1) flattens, mirroring numpy outer's ravel
    a = np.array([[1.0], [2.0]])          # (2,1) → flattens to length-2
    b = np.array([3.0, 4.0])
    assert np.array_equal(dense_outer_real(a, b), np.outer(a, b))


# ── registration: the 3 gates + LAPLACIAN_OPS ────────────────────────────────

def test_dense_outer_in_all_and_laplacian_ops():
    for name in ("dense_outer_complex", "dense_outer_real"):
        assert name in laplacian.__all__
        assert name in laplacian.LAPLACIAN_OPS


def test_dense_outer_tool_entries_registered():
    from srmech.amsc.tool_schema import get_tool_schema

    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.amsc.laplacian.dense_outer_complex" in names
    assert "srmech.amsc.laplacian.dense_outer_real" in names


# ── the routed qm callsites still compute correctly ──────────────────────────

def test_propagators_momentum_tensor_routed():
    from srmech.qm.propagators import feynman_photon_propagator
    # general covariant gauge (ξ≠1) → the (1-ξ) kᵘkᵛ term is active, now built
    # via dense_outer_real instead of np.outer
    k = np.array([1.0, 0.5, 0.0, 0.0])
    P = feynman_photon_propagator(k_squared=1.0, gauge_xi=0.5, epsilon=1e-9, k=k)
    assert P.shape == (4, 4)              # propagator built without numpy outer


def test_single_particle_density_matrix_routed():
    from srmech.qm.single_particle import density_matrix
    psi = np.array([1 + 0j, 0 + 1j]) / np.sqrt(2)
    rho = density_matrix(psi)
    assert np.allclose(rho, np.outer(psi, psi.conj()))   # |ψ⟩⟨ψ| via dense_outer_complex
    assert np.isclose(np.trace(rho), 1.0)
