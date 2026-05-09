"""Unit tests for the 1.14.0 chess4D-OC consumer-driven wishlist
surface added late in the 1.14.0 cycle:

  * :func:`chess_spectral.qm_4d_bridge.get_qm_density_from_psi`
  * :func:`chess_spectral.qm_4d_bridge.get_probability_current_from_psi`
  * :func:`chess_spectral.qm_4d_bridge.channel_energies_2d`
  * :func:`chess_spectral.qm_4d_bridge.channel_energies_4d`
  * :class:`chess_spectral.engine.eval.spectral_hybrid_cache.HybridCache`
    method ``clear``

The ``get_density_matrix_of`` 1.14.0 partial implementation has its
own test class in ``test_qm_4d_bridge_v15.py::TestGetDensityMatrixOf``;
this file covers everything else on the chess4D-OC wishlist.

Why these tests live in a separate file
---------------------------------------

The wishlist items cross multiple sub-packages
(``qm_4d_bridge`` + ``engine.eval.spectral_hybrid_cache``); the
existing per-module tests use module-scoped fixtures that don't
generalize across both surfaces. Bundling here keeps the wishlist
contract auditable in one place — when a chess4D-OC PR breaks any of
these, the failing test file points at the right wishlist item.
"""
from __future__ import annotations

import os
import sys
from typing import Dict

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import qm_4d as _qm4              # noqa: E402
from chess_spectral import qm_4d_bridge as br         # noqa: E402
from chess_spectral import tables_4d as _t4           # noqa: E402
from chess_spectral.engine.eval.spectral_hybrid_cache import (  # noqa: E402
    HybridCache,
)


# =====================================================================
# Position fixtures (mirror test_qm_4d_bridge_v15.py)
# =====================================================================


@pytest.fixture(scope='module')
def imbalanced_position() -> Dict[int, str]:
    coords = {
        (0, 0, 0, 0): 'K', (5, 5, 5, 5): 'k',
        (1, 2, 3, 4): 'Q',
        (3, 1, 2, 3): 'B',
        (2, 5, 0, 1): 'N',
        (4, 3, 1, 2): 'R',
    }
    return {_t4.sq4(*c): p for c, p in coords.items()}


@pytest.fixture(scope='module')
def position_2d() -> Dict[int, str]:
    """A nontrivial 2D position for channel-energy bridge tests."""
    return {
        0: 'R', 4: 'K', 7: 'R',
        56: 'r', 60: 'k', 63: 'r',
        12: 'P', 13: 'P', 51: 'p', 52: 'p',
    }


# =====================================================================
# Tier 1 #1 — get_probability_current_from_psi
# =====================================================================


class TestProbabilityCurrentFromPsi:
    """``get_probability_current_from_psi(psi)`` — the ψ-direct variant
    that skips the encoder. M14.4c hot-path for chess4D-OC's current-
    arrow overlay updates after collapse."""

    def test_returns_flat_16384_float32(self, imbalanced_position):
        psi = _qm4.state_to_psi(imbalanced_position, True)
        res = br.get_probability_current_from_psi(psi)
        assert res['ok'] is True
        j = res['j']
        assert isinstance(j, np.ndarray)
        assert j.dtype == np.float32
        # The flat shape (16384,) is the chess4D-OC consumer contract.
        assert j.shape == (16384,)

    def test_matches_state_driven_variant(self, imbalanced_position):
        """``get_probability_current_from_psi(state_to_psi(state))``
        must yield the SAME current field as
        ``get_probability_current(state)`` — operator-level identity.
        """
        psi = _qm4.state_to_psi(imbalanced_position, True)
        res_psi = br.get_probability_current_from_psi(psi)
        res_state = br.get_probability_current(imbalanced_position)
        # res_state['j'] is (4096, 4); res_psi['j'] is (16384,) flat.
        assert np.allclose(
            res_psi['j'].reshape(4096, 4),
            res_state['j'],
            atol=1e-6,
        )

    def test_accepts_channel_block_view(self, imbalanced_position):
        """psi shape (11, 4096) accepted; matches the (45056,) result."""
        psi = _qm4.state_to_psi(imbalanced_position, True)
        psi_block = psi.reshape(_qm4.N_CHANNELS, _qm4.CHANNEL_DIM)
        res_flat = br.get_probability_current_from_psi(psi)
        res_block = br.get_probability_current_from_psi(psi_block)
        assert np.array_equal(res_flat['j'], res_block['j'])

    def test_real_promotion_for_real_input(self, imbalanced_position):
        """Real-valued ψ is promoted to complex (imag=0). j is then
        identically zero (Im(ψ* ∂ψ) = Im(real * real) = 0)."""
        psi = _qm4.state_to_psi(imbalanced_position, True).real.astype(np.float64)
        res = br.get_probability_current_from_psi(psi)
        assert res['ok'] is True
        # The probability current of a purely real ψ is exactly zero.
        assert np.allclose(res['j'], 0.0, atol=1e-12)

    def test_invalid_shape_raises(self):
        # Wrong number of elements.
        psi_bad = np.zeros(1234, dtype=np.complex128)
        with pytest.raises(ValueError):
            br.get_probability_current_from_psi(psi_bad)
        # Wrong rank.
        psi_bad2 = np.zeros((45056, 1), dtype=np.complex128)
        with pytest.raises(ValueError):
            br.get_probability_current_from_psi(psi_bad2)


# =====================================================================
# Tier 1 #1b — get_qm_density_from_psi
# =====================================================================


class TestQmDensityFromPsi:
    """``get_qm_density_from_psi(psi)`` — sibling of the current
    function above. M14.4c hot-path for the density rerender after
    collapse."""

    def test_returns_4096_float32(self, imbalanced_position):
        psi = _qm4.state_to_psi(imbalanced_position, True)
        res = br.get_qm_density_from_psi(psi)
        assert res['ok'] is True
        d = res['density']
        assert d.shape == (4096,)
        assert d.dtype == np.float32

    def test_matches_state_driven(self, imbalanced_position):
        psi = _qm4.state_to_psi(imbalanced_position, True)
        res_psi = br.get_qm_density_from_psi(psi)
        res_state = br.get_qm_density(imbalanced_position)
        assert np.allclose(res_psi['density'], res_state['density'], atol=1e-6)

    def test_density_nonneg_and_sums_to_norm(self, imbalanced_position):
        psi = _qm4.state_to_psi(imbalanced_position, True)
        res = br.get_qm_density_from_psi(psi)
        d = res['density']
        assert (d >= -1e-9).all()
        # |ψ|² summed across cells == |ψ|² (Σ_chan,cell |ψ|²).
        norm_sq = float(np.vdot(psi, psi).real)
        assert abs(float(d.sum()) - norm_sq) < 1e-3

    def test_accepts_channel_block_view(self, imbalanced_position):
        psi = _qm4.state_to_psi(imbalanced_position, True)
        psi_block = psi.reshape(_qm4.N_CHANNELS, _qm4.CHANNEL_DIM)
        res_flat = br.get_qm_density_from_psi(psi)
        res_block = br.get_qm_density_from_psi(psi_block)
        assert np.array_equal(res_flat['density'], res_block['density'])

    def test_invalid_shape_raises(self):
        with pytest.raises(ValueError):
            br.get_qm_density_from_psi(np.zeros(123, dtype=np.complex128))


# =====================================================================
# Tier 2 #4 — channel_energies_2d / channel_energies_4d Pyodide bridge
# =====================================================================


class TestChannelEnergiesBridge2D:
    """``channel_energies_2d(pos)`` — Pyodide-friendly entry that
    encodes + computes channel energies in one shot."""

    def test_return_shape(self, position_2d):
        res = br.channel_energies_2d(position_2d)
        assert res['ok'] is True
        assert isinstance(res['energies'], dict)

    def test_energies_nonneg(self, position_2d):
        res = br.channel_energies_2d(position_2d)
        for name, energy in res['energies'].items():
            assert isinstance(energy, float)
            assert energy >= 0.0

    def test_matches_direct_call(self, position_2d):
        from chess_spectral.encoder_bip_hybrid import encode_2d_bip_hybrid
        from chess_spectral.engine.eval.spectral_hybrid import (
            channel_energies_from_hybrid,
        )
        hybrid = encode_2d_bip_hybrid(position_2d, magnitude_bits=8)
        direct = channel_energies_from_hybrid(hybrid)
        bridged = br.channel_energies_2d(position_2d)['energies']
        assert set(direct.keys()) == set(bridged.keys())
        for name in direct:
            assert abs(direct[name] - bridged[name]) < 1e-9, (
                f"Channel {name}: direct={direct[name]} "
                f"vs bridged={bridged[name]}"
            )

    def test_magnitude_bits_kwarg(self, position_2d):
        res8 = br.channel_energies_2d(position_2d, magnitude_bits=8)
        res4 = br.channel_energies_2d(position_2d, magnitude_bits=4)
        # Both succeed; 4-bit is coarser (1.10.0 sheets variant) but
        # shape is identical to 8-bit.
        assert res8['ok'] and res4['ok']
        assert set(res8['energies'].keys()) == set(res4['energies'].keys())


class TestChannelEnergiesBridge4D:
    """``channel_energies_4d(pos4)`` — 4D analog."""

    def test_return_shape(self, imbalanced_position):
        res = br.channel_energies_4d(imbalanced_position)
        assert res['ok'] is True
        # The 4D channel set has 11 entries.
        assert len(res['energies']) == 11

    def test_energies_nonneg_and_finite(self, imbalanced_position):
        res = br.channel_energies_4d(imbalanced_position)
        for name, energy in res['energies'].items():
            assert energy >= 0.0
            assert np.isfinite(energy)

    def test_matches_direct_call(self, imbalanced_position):
        from chess_spectral.encoder_bip_hybrid import encode_4d_bip_hybrid
        from chess_spectral.engine.eval.spectral_hybrid import (
            channel_energies_from_hybrid_4d,
        )
        hybrid = encode_4d_bip_hybrid(imbalanced_position, magnitude_bits=8)
        direct = channel_energies_from_hybrid_4d(hybrid)
        bridged = br.channel_energies_4d(imbalanced_position)['energies']
        for name in direct:
            assert abs(direct[name] - bridged[name]) < 1e-9


# =====================================================================
# Tier 2 #3 — HybridCache.clear()
# =====================================================================


class TestHybridCacheClear:
    """``HybridCache.clear()`` — chess4D-OC's reset path needs a way
    to wipe cache state without rebuilding the cache object."""

    def test_clear_drops_entries(self):
        cache = HybridCache(max_size=100)
        # Populate with 3 dummy keys via get_or_compute.
        sentinel_calls = {'count': 0}

        def factory():
            sentinel_calls['count'] += 1
            return object()  # SpectralBIPHybrid2D placeholder for cache test

        cache.get_or_compute(1, factory)
        cache.get_or_compute(2, factory)
        cache.get_or_compute(3, factory)
        assert cache.size == 3
        assert cache.misses == 3

        cache.clear()
        assert cache.size == 0
        assert cache.misses == 0
        assert cache.hits == 0

    def test_clear_resets_counters_after_hits(self):
        cache = HybridCache(max_size=100)
        sentinel = object()
        cache.get_or_compute(42, lambda: sentinel)
        cache.get_or_compute(42, lambda: sentinel)  # hit
        assert cache.hits == 1
        assert cache.misses == 1

        cache.clear()
        assert cache.hits == 0
        assert cache.misses == 0
        assert cache.size == 0

    def test_clear_preserves_max_size(self):
        cache = HybridCache(max_size=42)
        cache.get_or_compute(1, lambda: object())
        cache.clear()
        # max_size is preserved; only entries + counters reset.
        stats = cache.stats()
        assert stats['max_size'] == 42
        assert stats['size'] == 0

    def test_clear_then_populate_works(self):
        cache = HybridCache(max_size=10)
        cache.get_or_compute(1, lambda: 'a')
        cache.clear()
        # Populating after clear should hit miss path again.
        result = cache.get_or_compute(1, lambda: 'b')
        assert result == 'b'  # Got a fresh value, not 'a'
        assert cache.misses == 1
        assert cache.hits == 0


# =====================================================================
# Cross-cutting: the wishlist functions are in __all__
# =====================================================================


def test_wishlist_functions_in_all():
    """Each new function must be exported via ``__all__`` so
    ``from chess_spectral.qm_4d_bridge import *`` makes them
    discoverable."""
    expected = {
        'get_qm_density_from_psi',
        'get_probability_current_from_psi',
        'channel_energies_2d',
        'channel_energies_4d',
    }
    assert expected.issubset(set(br.__all__))


def test_hybridcache_clear_is_attribute():
    cache = HybridCache(max_size=1)
    assert hasattr(cache, 'clear')
    assert callable(cache.clear)
