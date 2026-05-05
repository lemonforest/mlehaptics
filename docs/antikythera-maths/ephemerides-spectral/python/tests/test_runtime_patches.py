"""Runtime kernel-patching overlay tests (v0.4.0).

The diagnosed-fiber overlay is a structural commitment: the published
kernel bytes never change, patches sum onto the encoded phases AFTER
the base encode, and a cleared-overlay encode is byte-identical to
v0.3.1. These tests pin those properties.

Properties under test:

1. ``apply_patch`` + ``clear_patches`` round-trip leaves the encode
   byte-identical to the no-patches baseline.
2. A diagonal patch shifts only the targeted body's phase residue.
3. Two diagonal patches on disjoint bodies compose without
   cross-contamination.
4. The coupled (J-S) patch shifts both bodies anti-correlated to
   within ULP (sum of the signed deltas is 0).
5. Re-applying the same named patch raises (no silent shadow).
6. The ``backend="c"`` request transparently falls back to ``"bip"``
   while patches are active (correctness > speed; C-side overlay is
   v0.4.x phase F).
7. ``apply_custom_patch`` constructs a patch from primitive args.
"""

from __future__ import annotations

import pytest

pytest.importorskip("skyfield", reason="bridge encoding requires skyfield")

from ephemerides_spectral import bridge


REFERENCE_JD = 2451545.0
TEST_JD = REFERENCE_JD + 20 * 365.25
KERNEL = "de421"  # tiny calibration kernel, available everywhere
MODULO = 1 << 32


def _signed(d: int) -> int:
    """Map uint32 residue delta to signed [-2^31, 2^31)."""
    d &= MODULO - 1
    return d if d <= (MODULO >> 1) else d - MODULO


@pytest.fixture(autouse=True)
def _reset_patches():
    """Every test starts with no active patches, ends with none."""
    bridge.clear_patches()
    yield
    bridge.clear_patches()


def _encode(jd: float = TEST_JD):
    out = bridge.get_system_state(jd, backend="bip", kernel=KERNEL)
    assert out["ok"], out
    return out


# ──────────────────────────────────────────────────────────────────────
# Property 1: apply + clear round-trip
# ──────────────────────────────────────────────────────────────────────

def test_clear_restores_byte_identical_baseline() -> None:
    base = _encode()
    bridge.apply_patch("mars-7.96yr-diagonal")
    cleared = bridge.clear_patches()
    assert cleared["ok"] and cleared["cleared"] == 1
    restored = _encode()
    assert restored["phases_uint32"] == base["phases_uint32"]


# ──────────────────────────────────────────────────────────────────────
# Property 2: diagonal patch shifts only the targeted body
# ──────────────────────────────────────────────────────────────────────

def test_diagonal_patch_shifts_only_target_body() -> None:
    base = _encode()
    bridge.apply_patch("mars-7.96yr-diagonal")
    patched = _encode()
    bodies = base["bodies"]
    mars_idx = bodies.index("mars")

    for i, name in enumerate(bodies):
        if i == mars_idx:
            assert patched["phases_uint32"][i] != base["phases_uint32"][i], (
                "mars phase did not change under mars patch"
            )
        else:
            assert patched["phases_uint32"][i] == base["phases_uint32"][i], (
                f"{name!r} phase changed under diagonal mars patch"
            )


# ──────────────────────────────────────────────────────────────────────
# Property 3: composition is independent (sinusoidal kinds commute)
# ──────────────────────────────────────────────────────────────────────

def test_compose_two_disjoint_patches_independence() -> None:
    base = _encode()
    bridge.apply_patch("mars-7.96yr-diagonal")
    mars_only = _encode()
    bridge.apply_patch("mercury-10.69yr-diagonal")
    both = _encode()
    bridge.clear_patches()
    bridge.apply_patch("mercury-10.69yr-diagonal")
    mercury_only = _encode()

    bodies = base["bodies"]
    mars_idx = bodies.index("mars")
    mercury_idx = bodies.index("mercury")

    # Mars delta unchanged whether we add Mercury patch or not.
    mars_delta_alone = (
        int(mars_only["phases_uint32"][mars_idx]) - int(base["phases_uint32"][mars_idx])
    ) & (MODULO - 1)
    mars_delta_both = (
        int(both["phases_uint32"][mars_idx]) - int(base["phases_uint32"][mars_idx])
    ) & (MODULO - 1)
    assert mars_delta_alone == mars_delta_both

    # And vice versa.
    mercury_delta_alone = (
        int(mercury_only["phases_uint32"][mercury_idx])
        - int(base["phases_uint32"][mercury_idx])
    ) & (MODULO - 1)
    mercury_delta_both = (
        int(both["phases_uint32"][mercury_idx])
        - int(base["phases_uint32"][mercury_idx])
    ) & (MODULO - 1)
    assert mercury_delta_alone == mercury_delta_both


# ──────────────────────────────────────────────────────────────────────
# Property 4: coupled patch shifts both bodies anti-correlated
# ──────────────────────────────────────────────────────────────────────

def test_coupled_jupiter_saturn_patch_anti_correlated() -> None:
    base = _encode()
    bridge.apply_patch("jupiter-saturn-9.56yr-coupled")
    patched = _encode()
    bodies = base["bodies"]

    j_idx = bodies.index("jupiter")
    s_idx = bodies.index("saturn")
    j_delta = _signed(
        int(patched["phases_uint32"][j_idx]) - int(base["phases_uint32"][j_idx])
    )
    s_delta = _signed(
        int(patched["phases_uint32"][s_idx]) - int(base["phases_uint32"][s_idx])
    )

    # Anti-correlated: j_delta == -s_delta exactly (same |delta|, opposite sign).
    assert j_delta == -s_delta, (
        f"expected anti-correlated J-S deltas; got jupiter={j_delta}, saturn={s_delta}"
    )
    # And both must be nonzero (the patch DID do something).
    assert j_delta != 0


# ──────────────────────────────────────────────────────────────────────
# Property 5: same name twice is a hard error
# ──────────────────────────────────────────────────────────────────────

def test_apply_duplicate_name_raises() -> None:
    first = bridge.apply_patch("mars-7.96yr-diagonal")
    assert first["ok"]
    second = bridge.apply_patch("mars-7.96yr-diagonal")
    assert second["ok"] is False
    assert "already active" in second["error"]


# ──────────────────────────────────────────────────────────────────────
# Property 6: C backend handles overlay natively (v0.4.1+, ABI v2)
#
# Falls back to BIP only when the native binary isn't loaded (sdist
# without C toolchain, Pyodide). When loaded, the C-side patch
# registry mirrors the Python one and produces byte-identical phases.
# ──────────────────────────────────────────────────────────────────────

def test_c_backend_handles_overlay_when_loaded() -> None:
    from ephemerides_spectral import _native_bip
    bridge.apply_patch("mars-7.96yr-diagonal")
    out = bridge.get_system_state(TEST_JD, backend="c", kernel=KERNEL)
    assert out["ok"], out
    assert out["backend_requested"] == "c"
    if _native_bip.HAS_NATIVE:
        assert out["backend"] == "c", (
            f"native loaded; C backend should apply overlay natively. "
            f"Got backend={out['backend']!r}"
        )
    else:
        assert out["backend"] == "bip", (
            f"no native loaded; C backend must fall back to bip. "
            f"Got backend={out['backend']!r}"
        )


# ──────────────────────────────────────────────────────────────────────
# Property 6b (v0.4.1): cross-backend byte-exact parity with patches
# ──────────────────────────────────────────────────────────────────────

def test_cross_backend_parity_with_patches() -> None:
    """BIP and C must produce byte-identical phases under overlay."""
    from ephemerides_spectral import _native_bip
    if not _native_bip.HAS_NATIVE:
        pytest.skip("native not loaded; cross-backend parity untestable")
    for name in [
        "mars-7.96yr-diagonal",
        "mercury-10.69yr-diagonal",
        "jupiter-saturn-9.56yr-coupled",
    ]:
        bridge.apply_patch(name)
    bip = bridge.get_system_state(TEST_JD, backend="bip", kernel=KERNEL)
    c = bridge.get_system_state(TEST_JD, backend="c", kernel=KERNEL)
    assert bip["backend"] == "bip"
    assert c["backend"] == "c"
    assert bip["phases_uint32"] == c["phases_uint32"], (
        "BIP and C must produce byte-identical phases under overlay"
    )


def test_native_registry_in_sync_with_python() -> None:
    """After every apply / clear, native and Python registries agree on n_active."""
    from ephemerides_spectral import _native_bip
    if not _native_bip.HAS_NATIVE:
        pytest.skip("native not loaded")
    assert _native_bip.native_n_active_patches() == 0
    bridge.apply_patch("mars-7.96yr-diagonal")
    assert _native_bip.native_n_active_patches() == 1
    bridge.apply_patch("mercury-10.69yr-diagonal")
    assert _native_bip.native_n_active_patches() == 2
    # Duplicate-name rejection on the C side too.
    dup = bridge.apply_patch("mars-7.96yr-diagonal")
    assert dup["ok"] is False
    assert _native_bip.native_n_active_patches() == 2  # no leak
    bridge.clear_patches()
    assert _native_bip.native_n_active_patches() == 0


# ──────────────────────────────────────────────────────────────────────
# Property 7: custom patches via primitive args
# ──────────────────────────────────────────────────────────────────────

def test_apply_custom_sinusoid_patch() -> None:
    # 1.0-deg sinusoid on Earth at a 100-yr period.
    base = _encode()
    out = bridge.apply_custom_patch(
        name="earth-test-1deg-100yr",
        kind="sinusoid",
        body="terra",
        amplitude_deg=1.0,
        period_days=36525.0,
        notes="unit-test patch",
    )
    assert out["ok"]
    patched = _encode()
    earth_idx = base["bodies"].index("terra")
    delta = _signed(
        int(patched["phases_uint32"][earth_idx])
        - int(base["phases_uint32"][earth_idx])
    )
    # Should be nonzero; magnitude bounded by amp_residue = 1/360 * 2^32.
    assert delta != 0
    assert abs(delta) <= int(round((1.0 / 360.0) * MODULO)) + 1


def test_apply_custom_coupled_patch() -> None:
    base = _encode()
    out = bridge.apply_custom_patch(
        name="venus-mars-test-coupled",
        kind="coupled-sinusoid",
        body_a="venus",
        body_b="mars",
        amplitude_deg=2.0,
        period_days=5000.0,
        correlation=1,  # same-sign for the test
    )
    assert out["ok"]
    patched = _encode()
    bodies = base["bodies"]
    v_delta = _signed(
        int(patched["phases_uint32"][bodies.index("venus")])
        - int(base["phases_uint32"][bodies.index("venus")])
    )
    m_delta = _signed(
        int(patched["phases_uint32"][bodies.index("mars")])
        - int(base["phases_uint32"][bodies.index("mars")])
    )
    # correlation=+1 → same sign + magnitude
    assert v_delta == m_delta
    assert v_delta != 0


def test_apply_custom_bad_kind_returns_error() -> None:
    out = bridge.apply_custom_patch(
        name="nope", kind="quadratic", body="terra",
        amplitude_deg=1.0, period_days=100.0,
    )
    assert out["ok"] is False
    assert "kind" in out["error"]


def test_apply_custom_bad_correlation_returns_error() -> None:
    out = bridge.apply_custom_patch(
        name="nope2", kind="coupled-sinusoid",
        body_a="venus", body_b="mars",
        amplitude_deg=1.0, period_days=100.0,
        correlation=2,  # invalid
    )
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# Catalog visibility
# ──────────────────────────────────────────────────────────────────────

def test_catalog_lists_v041_plus_v052_plus_v055() -> None:
    """v0.5.5: combined catalog has 3 v1 + 3 v2 (planet) + 5 v2 (moon) entries."""
    out = bridge.list_catalog_patches()
    assert out["ok"] is True
    names = {p["name"] for p in out["patches"]}
    expected = {
        # v0.4.0 magnitude-only catalog (kept for backwards compat).
        "mars-7.96yr-diagonal",
        "mercury-10.69yr-diagonal",
        "jupiter-saturn-9.56yr-coupled",
        # v0.5.2 phase-recovered + LS-fit catalog (vindicated >=96% shrinkage on planets).
        "mars-7.96yr-diagonal-v2",
        "mercury-10.69yr-diagonal-v2",
        "jupiter-saturn-9.56yr-coupled-v2",
        # v0.5.5 LS-fit catalog (Phase C: vindicated >=93% shrinkage on moons).
        "dione-1.06yr-diagonal-v2",
        "tethys-0.38yr-diagonal-v2",
        "enceladus-0.39yr-diagonal-v2",
        "titan-0.69yr-diagonal-v2",
        "iapetus-0.22yr-diagonal-v2",
    }
    assert names == expected
    # Each entry must carry kind, amplitude, period, notes.
    for p in out["patches"]:
        assert p["kind"] in {"sinusoid", "coupled-sinusoid"}
        assert p["amplitude_deg"] > 0.0
        assert p["period_days"] > 0.0
        assert "notes" in p


def test_active_patches_starts_empty() -> None:
    out = bridge.list_active_patches()
    assert out["ok"] is True
    assert out["n_active"] == 0
    assert out["patches"] == []
