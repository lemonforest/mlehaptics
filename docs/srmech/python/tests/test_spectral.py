"""Tests for ``srmech.spectral`` runtime spectral decomposition surface.

Verifies bit-exact behaviour of the four rcN+1 entries (decompose / delta
/ recompose / similarity) per Spike #115 design (PR #518) + Spike #114
HDC bind identity (PR #514) + Spike #116 rank-k delta identity (PR #516).
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech import spectral
from srmech.spectral import (
    SpectralHandle,
    clear_eigenbasis_cache,
    decompose,
    delta,
    recompose,
    similarity,
)


# ---------------------------------------------------------------------------
# Helpers — small Hermitian Laplacian fixtures
# ---------------------------------------------------------------------------

def _path_laplacian(n: int) -> np.ndarray:
    """Path-graph Laplacian on n nodes (Hermitian, PSD)."""
    L = np.zeros((n, n), dtype=np.float64)
    for i in range(n - 1):
        L[i, i] += 1
        L[i + 1, i + 1] += 1
        L[i, i + 1] -= 1
        L[i + 1, i] -= 1
    return L


def _random_state(n: int, seed: int = 0) -> np.ndarray:
    """Reproducible real-valued state vector."""
    rng = np.random.default_rng(seed)
    return rng.standard_normal(n).astype(np.float64)


# ---------------------------------------------------------------------------
# decompose
# ---------------------------------------------------------------------------

class TestDecompose:
    def test_returns_handle(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(8)
        state = _random_state(8)
        h = decompose(state, L)
        assert isinstance(h, SpectralHandle)

    def test_handle_fields(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(6)
        state = _random_state(6, seed=1)
        h = decompose(state, L)
        assert h.n_modes == 6
        # coefficients_bytes is complex128 packed: 16 bytes per mode
        assert len(h.coefficients_bytes) == 6 * 16
        assert len(h.substrate_descriptor_hash) == 64  # SHA-256 hex
        assert len(h.content_sha) == 64

    def test_state_shape_rejection(self):
        L = _path_laplacian(4)
        with pytest.raises(ValueError):
            decompose(np.zeros((2, 2)), L)  # 2-D state rejected

    def test_laplacian_shape_rejection(self):
        with pytest.raises(ValueError):
            decompose(np.zeros(4), np.zeros((4, 3)))  # non-square rejected

    def test_size_mismatch_rejection(self):
        L = _path_laplacian(4)
        with pytest.raises(ValueError):
            decompose(np.zeros(5), L)

    def test_descriptor_hash_changes_with_encoder_tag(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        state = _random_state(4)
        h1 = decompose(state, L, encoder_tag="raw")
        h2 = decompose(state, L, encoder_tag="quantized")
        assert h1.substrate_descriptor_hash != h2.substrate_descriptor_hash

    def test_descriptor_hash_stable_within_tag(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        state1 = _random_state(4, seed=1)
        state2 = _random_state(4, seed=2)
        h1 = decompose(state1, L)
        h2 = decompose(state2, L)
        # same substrate -> same descriptor_hash regardless of state
        assert h1.substrate_descriptor_hash == h2.substrate_descriptor_hash
        # different state -> different content_sha
        assert h1.content_sha != h2.content_sha


# ---------------------------------------------------------------------------
# delta — Class M (HDC bind) identity per Spike #114
# ---------------------------------------------------------------------------

class TestDelta:
    def test_bytes_inputs(self):
        a = b"\x12\x34\x56\x78" * 32
        b = b"\xab\xcd\xef\x01" * 32
        d = delta(a, b)
        assert len(d) == len(a)

    def test_self_inverse_identity(self):
        """bind(a, bind(a, b)) == b per Plate 1995 / Kanerva 2009 BSC."""
        a = b"\x12\x34\x56\x78" * 16
        b = b"\xab\xcd\xef\x01" * 16
        d = delta(a, b)
        recovered = delta(a, d)
        assert recovered == b

    def test_commutativity(self):
        a = b"\x01" * 64
        b = b"\x10" * 64
        assert delta(a, b) == delta(b, a)

    def test_handle_input(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        s1 = _random_state(4, seed=1)
        s2 = _random_state(4, seed=2)
        h1 = decompose(s1, L)
        h2 = decompose(s2, L)
        d = delta(h1, h2)
        assert len(d) == len(h1.coefficients_bytes)

    def test_substrate_mismatch_rejection(self):
        clear_eigenbasis_cache()
        L_a = _path_laplacian(4)
        L_b = _path_laplacian(4) * 2  # different Laplacian -> different hash
        s = _random_state(4, seed=0)
        h_a = decompose(s, L_a)
        h_b = decompose(s, L_b)
        assert h_a.substrate_descriptor_hash != h_b.substrate_descriptor_hash
        with pytest.raises(ValueError, match="substrate_descriptor_hash"):
            delta(h_a, h_b)

    def test_length_mismatch_rejection(self):
        with pytest.raises(ValueError):
            delta(b"\x00" * 4, b"\x00" * 8)


# ---------------------------------------------------------------------------
# recompose — Class L inverse per Spike #116 rank-k delta identity
# ---------------------------------------------------------------------------

class TestRecompose:
    def test_roundtrip_bit_exact(self):
        """decompose then recompose returns original state at machine ε."""
        clear_eigenbasis_cache()
        L = _path_laplacian(8)
        state = _random_state(8, seed=42).astype(np.complex128)
        h = decompose(state, L)
        recovered = recompose(h, L)
        residual = np.max(np.abs(recovered - state))
        assert residual < 1e-12, f"residual {residual:.3e} too large"

    def test_content_sha_mismatch_rejection(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        state = _random_state(4)
        h = decompose(state, L)
        # corrupt by replacing the dataclass with mismatched content_sha
        corrupted = SpectralHandle(
            substrate_descriptor_hash=h.substrate_descriptor_hash,
            coefficients_bytes=h.coefficients_bytes,
            content_sha="0" * 64,  # wrong sha
            n_modes=h.n_modes,
        )
        with pytest.raises(ValueError, match="content_sha"):
            recompose(corrupted, L)

    def test_descriptor_hash_mismatch_rejection(self):
        clear_eigenbasis_cache()
        L_a = _path_laplacian(4)
        L_b = _path_laplacian(4) * 3
        state = _random_state(4)
        h = decompose(state, L_a)
        with pytest.raises(ValueError, match="descriptor_hash"):
            recompose(h, L_b)


# ---------------------------------------------------------------------------
# similarity — Class M HDC similarity per Kanerva 2009
# ---------------------------------------------------------------------------

class TestSimilarity:
    def test_self_similarity_is_one(self):
        a = b"\x12\x34\x56\x78" * 16
        assert similarity(a, a) == pytest.approx(1.0)

    def test_orthogonal_random_near_zero(self):
        rng = np.random.default_rng(0)
        a = bytes(rng.integers(0, 256, size=128, dtype=np.uint8))
        b = bytes(rng.integers(0, 256, size=128, dtype=np.uint8))
        # Random byte vectors are statistically near-orthogonal
        s = similarity(a, b)
        assert -0.2 < s < 0.2

    def test_handle_input(self):
        clear_eigenbasis_cache()
        L = _path_laplacian(4)
        s = _random_state(4, seed=1)
        h1 = decompose(s, L)
        h2 = decompose(s, L)  # same state -> same handle
        assert similarity(h1, h2) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Cache behaviour
# ---------------------------------------------------------------------------

class TestCache:
    def test_lru_bounded(self):
        from srmech.spectral import N_MAX_EIGENBASES, _EIGENBASIS_CACHE  # noqa
        clear_eigenbasis_cache()
        # Insert N_MAX_EIGENBASES + 3 distinct descriptors
        for i in range(N_MAX_EIGENBASES + 3):
            L = _path_laplacian(4) * (i + 1)  # distinct laplacians
            decompose(_random_state(4), L)
        # Cache should hold exactly N_MAX_EIGENBASES entries
        assert len(_EIGENBASIS_CACHE) == N_MAX_EIGENBASES

    def test_clear(self):
        from srmech.spectral import _EIGENBASIS_CACHE
        L = _path_laplacian(4)
        decompose(_random_state(4), L)
        assert len(_EIGENBASIS_CACHE) >= 1
        clear_eigenbasis_cache()
        assert len(_EIGENBASIS_CACHE) == 0


# ---------------------------------------------------------------------------
# End-to-end identity (Spike #116 rank-k delta on path graph)
# ---------------------------------------------------------------------------

class TestEndToEndIdentity:
    def test_full_roundtrip_via_delta_recovery(self):
        """state_b = recompose(handle from state_a + bind(state_a, state_b))."""
        clear_eigenbasis_cache()
        L = _path_laplacian(8)
        s_a = _random_state(8, seed=1).astype(np.complex128)
        s_b = _random_state(8, seed=2).astype(np.complex128)
        h_a = decompose(s_a, L)
        h_b = decompose(s_b, L)
        d = delta(h_a, h_b)
        # Recover h_b's coefficients via second bind
        recovered_b_bytes = delta(h_a, d)
        assert recovered_b_bytes == h_b.coefficients_bytes


# ---------------------------------------------------------------------------
# rc16 — by-reference handle JSON round-trip THROUGH the MCP dispatch seam
# (the 7 spectral tools became mcp_callable=True; a producer's returned
# SpectralHandle crosses JSON as a $srmech_handle id a consumer resolves).
# ---------------------------------------------------------------------------


def _json_invoke(name, args):
    """Invoke a tool and parse its serialised JSON-string result (the
    server wire form)."""
    import json

    from srmech.mcp import invoke_tool
    from srmech.mcp._tools import serialise_result

    return json.loads(serialise_result(invoke_tool(name, args)))


class TestHandleJSONRoundTrip:
    def test_decompose_recompose_json_roundtrip_via_invoke_tool(self):
        """invoke_tool(decompose) -> a $srmech_handle envelope (NOT an inline
        coefficients dict) -> invoke_tool(recompose, handle=envelope) matches
        the direct in-process recompose (same 2x2 Hermitian both ends so the
        substrate descriptor hashes agree)."""
        from srmech._handles import HANDLE_ENVELOPE_KEY, get_handle_registry

        clear_eigenbasis_cache()
        get_handle_registry().clear()

        L = [[1.0, -1.0], [-1.0, 1.0]]
        state = [1.0, 2.0]

        env = _json_invoke(
            "srmech.spectral.decompose", {"state": state, "laplacian": L}
        )
        # By-reference id object — NOT the inline 4-field/coefficients dict.
        assert HANDLE_ENVELOPE_KEY in env
        import json as _json

        assert "coefficients_bytes" not in _json.dumps(env)

        recomposed = _json_invoke(
            "srmech.spectral.recompose", {"handle": env, "laplacian": L}
        )
        # Compare against the direct in-process recompose of the same state.
        direct = recompose(decompose(np.array(state), np.array(L)), np.array(L))
        # recomposed is a nested [re, im] list (complex128 ndarray on wire).
        got = np.asarray(recomposed)
        got_complex = got[..., 0] + 1j * got[..., 1]
        np.testing.assert_allclose(got_complex, direct, atol=1e-9)

    def test_producer_producer_consumer_chain_via_invoke_tool(self):
        """decompose -> predict(envelope) -> truncate_sparse(envelope) ->
        recompose, all via invoke_tool — chained by-reference handles
        resolve end-to-end (each producer's returned handle is a fresh
        registered envelope the next consumer resolves)."""
        from srmech._handles import HANDLE_ENVELOPE_KEY, get_handle_registry

        clear_eigenbasis_cache()
        get_handle_registry().clear()

        L = [[2.0, -1.0, -1.0], [-1.0, 2.0, -1.0], [-1.0, -1.0, 2.0]]
        state = [1.0, 0.5, -0.5]

        h0 = _json_invoke(
            "srmech.spectral.decompose", {"state": state, "laplacian": L}
        )
        assert HANDLE_ENVELOPE_KEY in h0

        h1 = _json_invoke(
            "srmech.spectral.predict",
            {"handle": h0, "laplacian": L, "steps": 1},
        )
        assert HANDLE_ENVELOPE_KEY in h1

        h2 = _json_invoke(
            "srmech.spectral.truncate_sparse", {"handle": h1, "keep_k": 2}
        )
        assert HANDLE_ENVELOPE_KEY in h2

        recomposed = _json_invoke(
            "srmech.spectral.recompose", {"handle": h2, "laplacian": L}
        )
        got = np.asarray(recomposed)
        # A length-3 complex state reconstructs (each scalar a [re, im] pair).
        assert got.shape == (3, 2)
