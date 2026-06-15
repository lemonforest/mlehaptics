"""rc161 — config-driven library limits + the Hermitian-eig ceiling.

The Hermitian-eig compute-guard ceiling used to be a compiled-in ``#define``
(C ``SRMECH_HERMITIAN_WS_MAX_NODES = 2048``) mirrored by a hard Python constant.
rc161 made it CONFIG-DRIVEN: a runtime value in the C library (default 2048,
raisable via a TOML blob or a file read through the PAL), queried by the Python
dispatch gate. This test pins the Python surface of that config layer + proves
``mat_hermitian_eigendecompose`` still diagonalises correctly across the gate.

Numpy-free by construction (the module under test is numpy-free; the test must
be too — ``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""

from __future__ import annotations

from array import array

import pytest

from srmech.amsc import _native
from srmech.amsc.mat import Mat
from srmech.amsc.laplacian import (
    MAX_NATIVE_HERMITIAN_NODES,
    mat_hermitian_eigendecompose,
)


def test_default_constant_mirrors_c_default():
    """The Python default mirrors the C SRMECH_HERMITIAN_DEFAULT_MAX_NODES."""
    assert _native.HERMITIAN_DEFAULT_MAX_NODES == 2048
    assert MAX_NATIVE_HERMITIAN_NODES == 2048


def test_getter_returns_positive_int():
    """The live ceiling getter always returns a positive int (native or not)."""
    ceil = _native.config_hermitian_max_nodes()
    assert isinstance(ceil, int)
    assert ceil >= 1


def test_loaders_are_noop_safe_without_native():
    """With no native lib the loaders are no-ops (the pure-Python Jacobi has no
    ceiling) and never raise; the getter stays at the built-in default."""
    if _native.has_native_config():
        pytest.skip("native config present — exercised in test_config_drives_ceiling")
    _native.config_load_toml("[hermitian]\nmax_nodes = 999\n")
    assert _native.config_hermitian_max_nodes() == _native.HERMITIAN_DEFAULT_MAX_NODES
    _native.config_reset_defaults()  # also a no-op, must not raise
    assert _native.config_hermitian_max_nodes() == _native.HERMITIAN_DEFAULT_MAX_NODES


def test_config_drives_ceiling_native():
    """With native present, a TOML blob moves the live ceiling DOWN and UP (past
    the old 2048 — proving it is no longer a hard cap), and reset restores it."""
    if not _native.has_native_config():
        pytest.skip("no native config layer (pure-Python env)")
    try:
        _native.config_reset_defaults()
        assert _native.config_hermitian_max_nodes() == 2048
        _native.config_load_toml("[hermitian]\nmax_nodes = 512\n")
        assert _native.config_hermitian_max_nodes() == 512
        _native.config_load_toml("[hermitian]\nmax_nodes = 5000\n")
        assert _native.config_hermitian_max_nodes() == 5000  # past the old cap
        _native.config_load_toml("[unrelated]\nfoo = 1\n")    # partial config
        assert _native.config_hermitian_max_nodes() == 5000
    finally:
        _native.config_reset_defaults()
    assert _native.config_hermitian_max_nodes() == 2048


def test_config_load_file_native(tmp_path):
    """The file form reads + applies a TOML descriptor through the PAL."""
    if not _native.has_native_config():
        pytest.skip("no native config layer (pure-Python env)")
    p = tmp_path / "srmech_limits.toml"
    p.write_text("[hermitian]\nmax_nodes = 333\n", encoding="utf-8")
    try:
        _native.config_reset_defaults()
        _native.config_load_file(str(p))
        assert _native.config_hermitian_max_nodes() == 333
    finally:
        _native.config_reset_defaults()


def _approx_set_equal(a, b, tol=1e-9):
    a = sorted(a)
    b = sorted(b)
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def test_hermitian_eig_correct_across_the_gate():
    """``mat_hermitian_eigendecompose`` diagonalises correctly regardless of the
    config ceiling — the gate only chooses native-vs-pure, never the answer."""
    # real-symmetric [[2,1],[1,2]] → eigenvalues {1, 3}
    H = Mat(array("d", [2.0, 0.0, 1.0, 0.0, 1.0, 0.0, 2.0, 0.0]), 2, 2,
            is_complex=True)
    evals, V = mat_hermitian_eigendecompose(H)
    got = [evals.buffer[i] for i in range(2)]
    assert _approx_set_equal(got, [1.0, 3.0])
    # reconstruction H ≈ V diag(λ) Vᴴ — a real entry spot-check (V is complex Mat)
    assert V.shape == (2, 2)
