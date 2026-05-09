"""Phase C of v0.27.0 — body→kernel registry tests.

Covers the registry abstraction (`_research.body_kernel_registry`) and
the bridge surfaces (`bridge.register_body_kernel`,
`bridge.clear_body_kernel`, `bridge.get_body_kernel_registry`), plus
metadata propagation into the `body_architecture` and
`predict_itn_accessibility` response envelopes.

Phase C ships the registry as **structural** infrastructure: registrations
are tracked + hashed + surfaced via bridge metadata, but orbital-mechanics
surfaces fall back to BODIES-distilled state lookups because the binary
kernels are not yet readable. Phase B's `binary_archive` adapter will
turn the registry from metadata into behaviour. Tests here verify the
structural contract that phase B will build against.

References
----------
* Notebook §22.6 — the three-layer mechanism architecture; layer-2-to-
  layer-3 interface this registry codifies.
* PR #294 — stored-relationship mechanism research spike.
* PR #296 — notebook §22 architecture-naming section.
* PR #297 — v0.27.0 ROADMAP entry.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research import body_kernel_registry as _bkr


# ─────────────────────────────────────────────────────────────────────
# Fixture: ensure each test starts with an empty registry, no matter
# what state previous tests left it in. Phase C's registry is module-
# level singleton state; tests must isolate.
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean_registry():
    """Clear the registry before AND after each test."""
    _bkr.clear()
    yield
    _bkr.clear()


# ─────────────────────────────────────────────────────────────────────
# Registry module — register / lookup / clear / state / hash semantics
# ─────────────────────────────────────────────────────────────────────


def test_empty_registry_is_inactive() -> None:
    assert _bkr.is_active() is False
    state = _bkr.state()
    assert state["active"] is False
    assert state["registry_size"] == 0
    assert state["registrations"] == []


def test_register_returns_ok_envelope() -> None:
    result = _bkr.register("jupiter", "/tmp/de441.bsp")
    assert result["ok"] is True
    assert result["body"] == "jupiter"
    assert result["kernel_path"] == "/tmp/de441.bsp"
    assert result["precision_tier"] == "jpl_published"
    assert result["registry_size"] == 1


def test_register_then_lookup_round_trip() -> None:
    _bkr.register("luna", "/tmp/lunar.bsp")
    found = _bkr.lookup("luna")
    assert found is not None
    assert found.body == "luna"
    assert found.kernel_path == "/tmp/lunar.bsp"
    assert found.precision_tier == "jpl_published"


def test_lookup_returns_none_for_unregistered_body() -> None:
    assert _bkr.lookup("mercury") is None


def test_register_with_explicit_precision_tier() -> None:
    result = _bkr.register(
        "bennu", "/tmp/bennu.bsp",
        precision_tier=_bkr.PRECISION_TIER_USER_FIT,
    )
    assert result["ok"] is True
    assert result["precision_tier"] == _bkr.PRECISION_TIER_USER_FIT


def test_register_rejects_empty_body() -> None:
    result = _bkr.register("", "/tmp/x.bsp")
    assert result["ok"] is False
    assert "body" in result["error"]


def test_register_rejects_empty_path() -> None:
    result = _bkr.register("mercury", "")
    assert result["ok"] is False
    assert "kernel_path" in result["error"]


def test_register_rejects_invalid_precision_tier() -> None:
    result = _bkr.register(
        "mercury", "/tmp/x.bsp", precision_tier="bogus_tier",
    )
    assert result["ok"] is False
    assert "precision_tier" in result["error"]


def test_register_overwrites_existing_body() -> None:
    _bkr.register("jupiter", "/tmp/old.bsp")
    _bkr.register("jupiter", "/tmp/new.bsp")
    found = _bkr.lookup("jupiter")
    assert found is not None
    assert found.kernel_path == "/tmp/new.bsp"
    # registry_size stays at 1 even after overwrite
    assert _bkr.state()["registry_size"] == 1


def test_clear_single_body_removes_only_that_body() -> None:
    _bkr.register("jupiter", "/tmp/a.bsp")
    _bkr.register("saturn", "/tmp/b.bsp")
    result = _bkr.clear("jupiter")
    assert result["ok"] is True
    assert result["cleared"] == 1
    assert _bkr.lookup("jupiter") is None
    assert _bkr.lookup("saturn") is not None
    assert _bkr.state()["registry_size"] == 1


def test_clear_unregistered_body_is_noop() -> None:
    _bkr.register("jupiter", "/tmp/a.bsp")
    result = _bkr.clear("ceres")
    assert result["ok"] is True
    assert result["cleared"] == 0
    assert _bkr.state()["registry_size"] == 1


def test_clear_all_empties_registry() -> None:
    _bkr.register("jupiter", "/tmp/a.bsp")
    _bkr.register("saturn", "/tmp/b.bsp")
    _bkr.register("uranus", "/tmp/c.bsp")
    result = _bkr.clear()
    assert result["ok"] is True
    assert result["cleared"] == 3
    assert _bkr.state()["registry_size"] == 0
    assert _bkr.is_active() is False


def test_state_envelope_sorts_registrations_by_body() -> None:
    _bkr.register("uranus", "/tmp/c.bsp")
    _bkr.register("saturn", "/tmp/b.bsp")
    _bkr.register("jupiter", "/tmp/a.bsp")
    state = _bkr.state()
    bodies = [reg["body"] for reg in state["registrations"]]
    assert bodies == ["jupiter", "saturn", "uranus"]


def test_all_bodies_returns_sorted_list() -> None:
    _bkr.register("uranus", "/tmp/u.bsp")
    _bkr.register("jupiter", "/tmp/j.bsp")
    assert _bkr.all_bodies() == ["jupiter", "uranus"]


# ─────────────────────────────────────────────────────────────────────
# Registry hash — determinism + invalidation semantics
# (These are load-bearing for phase B's eventual eigenbasis cache
# invalidation infrastructure.)
# ─────────────────────────────────────────────────────────────────────


def test_empty_registry_has_fixed_known_hash() -> None:
    """The empty-registry hash must be a fixed, well-defined value
    so v0.26.0-equivalent code paths can target it in byte-stable
    tests."""
    import hashlib
    expected = hashlib.sha256(b"[]").hexdigest()
    assert _bkr.state_hash() == expected


def test_hash_is_deterministic_across_calls() -> None:
    _bkr.register("jupiter", "/tmp/j.bsp")
    h1 = _bkr.state_hash()
    h2 = _bkr.state_hash()
    assert h1 == h2


def test_hash_changes_when_registration_added() -> None:
    h0 = _bkr.state_hash()
    _bkr.register("jupiter", "/tmp/j.bsp")
    h1 = _bkr.state_hash()
    assert h0 != h1


def test_hash_changes_when_registration_path_differs() -> None:
    _bkr.register("jupiter", "/tmp/a.bsp")
    h_a = _bkr.state_hash()
    _bkr.register("jupiter", "/tmp/b.bsp")
    h_b = _bkr.state_hash()
    assert h_a != h_b


def test_hash_changes_when_precision_tier_differs() -> None:
    _bkr.register("jupiter", "/tmp/x.bsp",
                  precision_tier=_bkr.PRECISION_TIER_JPL_PUBLISHED)
    h_pub = _bkr.state_hash()
    _bkr.register("jupiter", "/tmp/x.bsp",
                  precision_tier=_bkr.PRECISION_TIER_USER_FIT)
    h_fit = _bkr.state_hash()
    assert h_pub != h_fit


def test_hash_independent_of_registration_order() -> None:
    """Canonical-serialised → registration order in the call sequence
    must not affect the hash. This is what makes the hash a stable
    cache key across user workflows."""
    _bkr.register("jupiter", "/tmp/j.bsp")
    _bkr.register("saturn", "/tmp/s.bsp")
    h_js = _bkr.state_hash()
    _bkr.clear()
    _bkr.register("saturn", "/tmp/s.bsp")
    _bkr.register("jupiter", "/tmp/j.bsp")
    h_sj = _bkr.state_hash()
    assert h_js == h_sj


def test_hash_returns_to_empty_after_clear() -> None:
    h_empty = _bkr.state_hash()
    _bkr.register("jupiter", "/tmp/j.bsp")
    _bkr.clear()
    assert _bkr.state_hash() == h_empty


def test_state_hash_in_envelope_matches_state_hash_function() -> None:
    _bkr.register("jupiter", "/tmp/j.bsp")
    state = _bkr.state()
    assert state["state_hash"] == _bkr.state_hash()


# ─────────────────────────────────────────────────────────────────────
# Bridge surfaces — register_body_kernel / clear_body_kernel /
# get_body_kernel_registry
# ─────────────────────────────────────────────────────────────────────


def test_bridge_register_body_kernel_delegates() -> None:
    result = bridge.register_body_kernel("jupiter", "/tmp/j.bsp")
    assert result["ok"] is True
    assert result["body"] == "jupiter"
    # Round-trip via the underlying registry confirms the bridge
    # delegated correctly.
    assert _bkr.lookup("jupiter") is not None


def test_bridge_clear_body_kernel_delegates() -> None:
    bridge.register_body_kernel("jupiter", "/tmp/j.bsp")
    result = bridge.clear_body_kernel("jupiter")
    assert result["ok"] is True
    assert result["cleared"] == 1
    assert _bkr.lookup("jupiter") is None


def test_bridge_clear_all_body_kernels() -> None:
    bridge.register_body_kernel("jupiter", "/tmp/j.bsp")
    bridge.register_body_kernel("saturn", "/tmp/s.bsp")
    result = bridge.clear_body_kernel()
    assert result["ok"] is True
    assert result["cleared"] == 2


def test_bridge_get_body_kernel_registry_envelope_shape() -> None:
    """The Pyodide-friendly contract: ok flag + state envelope keys."""
    result = bridge.get_body_kernel_registry()
    assert result["ok"] is True
    assert result["active"] is False
    assert result["registry_size"] == 0
    assert result["registrations"] == []
    assert isinstance(result["state_hash"], str)


def test_bridge_get_body_kernel_registry_shows_registrations() -> None:
    bridge.register_body_kernel("jupiter", "/tmp/j.bsp")
    bridge.register_body_kernel(
        "bennu", "/tmp/bennu.bsp",
        precision_tier="user_fit",
    )
    result = bridge.get_body_kernel_registry()
    assert result["ok"] is True
    assert result["active"] is True
    assert result["registry_size"] == 2
    bodies = [r["body"] for r in result["registrations"]]
    assert bodies == ["bennu", "jupiter"]
    # Per-row precision tier is preserved through the bridge surface.
    bennu_row = next(r for r in result["registrations"] if r["body"] == "bennu")
    assert bennu_row["precision_tier"] == "user_fit"


def test_bridge_register_body_kernel_rejects_invalid_input() -> None:
    """Validation errors round-trip cleanly through the bridge as
    `ok=False` envelopes — the consumer sees the registry's own
    error message."""
    result = bridge.register_body_kernel("", "/tmp/x.bsp")
    assert result["ok"] is False
    result = bridge.register_body_kernel(
        "jupiter", "/tmp/x.bsp", precision_tier="bogus",
    )
    assert result["ok"] is False
    assert "precision_tier" in result["error"]


# ─────────────────────────────────────────────────────────────────────
# Metadata propagation — body_architecture + predict_itn_accessibility
# now surface the kernel_registry state in their response envelopes.
# ─────────────────────────────────────────────────────────────────────


def test_body_architecture_includes_kernel_registry_metadata() -> None:
    result = bridge.body_architecture()
    assert "kernel_registry" in result
    registry = result["kernel_registry"]
    assert registry["active"] is False
    assert registry["registry_size"] == 0
    assert isinstance(registry["state_hash"], str)


def test_body_architecture_kernel_registry_metadata_reflects_registrations() -> None:
    bridge.register_body_kernel("jupiter", "/tmp/j.bsp")
    result = bridge.body_architecture()
    registry = result["kernel_registry"]
    assert registry["active"] is True
    assert registry["registry_size"] == 1
    bodies = [r["body"] for r in registry["registrations"]]
    assert bodies == ["jupiter"]


def test_body_architecture_target_form_includes_kernel_registry() -> None:
    """Single-body form (target=name) must also surface the registry
    metadata so consumers iterating per-body don't lose attestation."""
    result = bridge.body_architecture(target="jupiter")
    assert "kernel_registry" in result


def test_predict_itn_accessibility_includes_kernel_registry_metadata() -> None:
    result = bridge.predict_itn_accessibility(
        departure="terra", target="jupiter",
    )
    assert "kernel_registry" in result
    registry = result["kernel_registry"]
    assert registry["active"] is False
    assert registry["registry_size"] == 0
    assert isinstance(registry["state_hash"], str)


def test_predict_itn_accessibility_kernel_registry_metadata_tracks_state() -> None:
    bridge.register_body_kernel("jupiter", "/tmp/j.bsp")
    result = bridge.predict_itn_accessibility(
        departure="terra", target="jupiter",
    )
    registry = result["kernel_registry"]
    assert registry["active"] is True
    assert registry["registry_size"] == 1


# ─────────────────────────────────────────────────────────────────────
# Phase A + B + C integration test stubs — these tests are scaffolded
# now so phase B's PR can fill them in once the binary_archive adapter
# + ephemeris_loader integration ships, and phase A's PR can confirm
# AMSC literature_curated catalogues coexist with the registry.
# Currently they verify only the structural contract; behaviour
# assertions activate when phases A and B land.
# ─────────────────────────────────────────────────────────────────────


def test_integration_stub_registered_kernel_path_does_not_break_surfaces() -> None:
    """When a kernel is registered, orbital-mechanics surfaces in
    phase C still return successfully (fallback to BODIES). Phase B
    will replace the fallback with actual kernel-state reads; this
    test stays valid through that transition."""
    bridge.register_body_kernel("jupiter", "/tmp/de441.bsp")
    arch = bridge.body_architecture()
    assert arch.get("ok", True) is not False
    pred = bridge.predict_itn_accessibility(
        departure="terra", target="jupiter",
    )
    assert pred.get("ok") is True


def test_integration_stub_amsc_overlay_coexists_with_body_kernel() -> None:
    """Phase A (AMSC backfill) + phase C (body→kernel registry)
    operate on different layers. Registering a body kernel must not
    affect the AMSC `use_local_kernel` overlay state, and vice
    versa. This test pins the layer separation contract."""
    bridge.register_body_kernel("jupiter", "/tmp/j.bsp")
    amsc_state = bridge.get_local_kernel_state()
    # AMSC layer is independent of body→kernel registry; touching
    # one must not flip the other's "active" flag.
    assert amsc_state.get("active") in (False, None)


def test_integration_stub_state_hash_stable_in_empty_case() -> None:
    """When no body kernel is registered, the registry state_hash
    is the fixed empty hash. Phase A's literature_curated backfill +
    phase B's binary_archive registrations must not leak into this
    field unintentionally; this test guards the layer-separation
    contract from the registry side."""
    # Register an AMSC-layer overlay (phase A's territory) — should
    # not affect the body→kernel registry hash.
    body_registry_state_before = _bkr.state_hash()
    # We can't actually call use_local_kernel without a real path
    # here, so the stub asserts only that the body→kernel registry
    # hash is byte-stable regardless of unrelated bridge calls.
    bridge.list_attested_sources()
    body_registry_state_after = _bkr.state_hash()
    assert body_registry_state_before == body_registry_state_after
