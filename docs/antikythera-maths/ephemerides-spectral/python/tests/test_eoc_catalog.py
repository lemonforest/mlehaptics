"""v0.28.0rc1 Phase 10a — EOC catalog tests.

Ratchets covering:

1. **Coverage**: SECULAR_ELEMENTS / EOC_CATALOG sized to 51 (= 52-body
   BIP roster minus Sun). Every body in BODIES except Sun has a row.
   Frame partition: 13 heliocentric + 38 parent-centric.

2. **Period agreement**: each row's `n_deg_per_day` agrees with
   `BODIES[body].period_days` to relative error < 5e-4 (the maximum
   tolerance set by Standish 1992's J2000-epoch round-off + DE441
   sidereal-period precision).

3. **Newton-Kepler correctness**: for an isolated body subject only
   to its own Kepler orbit (no perturbations), the patch's evaluator
   recovers `L_true - L_BIP` to machine precision. Verified against
   a direct closed-form implementation of Kepler's equation.

4. **J2000 anchoring**: every patch evaluates to ZERO at the BIP
   calibration epoch (JD_J2000 = 2451545.0). Load-bearing for the
   "BIP base = L_true(J2000), not L_mean(J2000)" calibration the
   `bip_instrument` provides.

5. **Frame discipline**: every heliocentric row has parent=None and
   every parent-centric row has parent in BODIES (and category=moon).

6. **AMSC dual-author parity**: the 51 rows the AMSC attested source
   carries match SECULAR_ELEMENTS field-for-field (modulo the four
   AMSC-only fields source_doi / source_published_date /
   entered_locally_at / source_version which the hand-coded module
   represents via the source_key + SOURCES dict, not stored per row).

7. **Attestation completeness**: every AMSC row carries a non-empty
   source_doi + source_published_date + entered_locally_at. No
   placeholder strings; no empty values.

8. **Filter semantics**: bridge / catalog filter kwargs (frame,
   parent, bodies) intersect as documented.

9. **Apply / clear round trip**: registering all 51 patches lands
   exactly 51 in the overlay; clearing returns them all.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research import (
    bodies,
    diagnosed_fibers,
    eoc_catalog,
    secular_elements_data,
)


JD_J2000 = 2451545.0


# ─────────────────────────────────────────────────────────────────────
# 1. Coverage ratchets
# ─────────────────────────────────────────────────────────────────────


def test_secular_elements_size_51() -> None:
    """SECULAR_ELEMENTS has exactly 51 rows — one per non-Sun BIP-roster
    body. Sun is excluded by design (e == 0 ⇒ no EOC term)."""
    assert len(secular_elements_data.SECULAR_ELEMENTS) == 51
    # Every key is a non-Sun BODIES key
    bodies_set = set(bodies.BODIES.keys()) - {"sun"}
    sec_set = set(secular_elements_data.SECULAR_ELEMENTS.keys())
    assert sec_set == bodies_set, (
        f"SECULAR_ELEMENTS keys diverge from BODIES (minus sun): "
        f"missing from SE = {bodies_set - sec_set}, "
        f"extra in SE = {sec_set - bodies_set}"
    )


def test_eoc_catalog_size_51() -> None:
    """EOC_CATALOG mirrors SECULAR_ELEMENTS one-to-one."""
    assert eoc_catalog.count() == 51
    assert set(eoc_catalog.EOC_CATALOG.keys()) == set(
        secular_elements_data.SECULAR_ELEMENTS.keys()
    )


def test_frame_partition_13_and_38() -> None:
    """Frame partition: 13 heliocentric (9 planets + 4 asteroids) + 38
    parent-centric (1 Luna + 2 Mars moons + 11 Jovian + 15 Saturnian +
    5 Uranian + 3 Neptunian + 1 Charon)."""
    helio = [
        b for b, r in secular_elements_data.SECULAR_ELEMENTS.items()
        if r.frame == "heliocentric_ecliptic"
    ]
    pcent = [
        b for b, r in secular_elements_data.SECULAR_ELEMENTS.items()
        if r.frame == "parent_centric_ecliptic"
    ]
    assert len(helio) == 13, helio
    assert len(pcent) == 38, pcent
    assert len(helio) + len(pcent) == 51


def test_n_sources_16() -> None:
    """The SOURCES citation dict carries 16 subsystem authority entries."""
    assert len(secular_elements_data.SOURCES) == 16


# ─────────────────────────────────────────────────────────────────────
# 2. Period agreement vs BODIES (the 9-decimal-place SSOT for n)
# ─────────────────────────────────────────────────────────────────────


def test_n_deg_per_day_matches_bodies_period() -> None:
    """For every body, 360 / n_deg_per_day agrees with
    BODIES[body].period_days to relative error < 5e-4. The looseness
    comes from Standish 1992's J2000-epoch elements vs BODIES's
    high-precision JPL HORIZONS sidereal periods; the project
    designates BODIES as the diagonal-frequency SSOT."""
    worst = 0.0
    worst_body = None
    for body, row in secular_elements_data.SECULAR_ELEMENTS.items():
        p_from_n = 360.0 / row.n_deg_per_day
        p_bodies = bodies.BODIES[body].period_days
        rel = abs(p_from_n - p_bodies) / p_bodies
        if rel > worst:
            worst = rel
            worst_body = body
        assert rel < 5e-4, (
            f"{body!r}: P_from_n={p_from_n:.6f} vs "
            f"P_BODIES={p_bodies:.6f}, rel_err={rel:.3e} > 5e-4"
        )
    # Sanity: worst case is in the expected envelope
    assert worst < 5e-4, f"worst body {worst_body!r} at rel_err={worst:.3e}"


# ─────────────────────────────────────────────────────────────────────
# 3. Newton-Kepler correctness — patch evaluator vs direct formula
# ─────────────────────────────────────────────────────────────────────


def _direct_eoc_residue(
    e: float, M0_rad: float, n_rad_per_day: float, delta_t: float
) -> int:
    """Closed-form reference EOC evaluator (independent reimplementation
    used to cross-check the patch's evaluator). Returns the residue
    delta in Z_{2^32} integer units."""
    M_t = M0_rad + n_rad_per_day * delta_t
    # Newton-solve Kepler for both M_t and M0
    def solve(M):
        E = M + e * math.sin(M) if e > 0.6 else M
        for _ in range(40):
            f = E - e * math.sin(E) - M
            fp = 1.0 - e * math.cos(E)
            E -= f / fp
            if abs(f) < 1e-15:
                break
        return E
    Et = solve(M_t)
    E0 = solve(M0_rad)
    def nu(E):
        return 2.0 * math.atan2(
            math.sqrt(1.0 + e) * math.sin(E / 2.0),
            math.sqrt(1.0 - e) * math.cos(E / 2.0),
        )
    delta_rad = (nu(Et) - M_t) - (nu(E0) - M0_rad)
    # principal branch wrap
    delta_rad = ((delta_rad + math.pi) % (2.0 * math.pi)) - math.pi
    return int(round(delta_rad / (2.0 * math.pi) * (2 ** 32)))


@pytest.mark.parametrize(
    "body,jd_delta_days",
    [
        ("terra", 100.0),
        ("terra", 365.25),
        ("mars", 200.0),
        ("mars", 5000.0),
        ("mercury", 50.0),         # high-e, short period
        ("pluto", 10000.0),        # high-e, long period
        ("nereid", 5000.0),        # extreme e=0.75
        ("io", 100.0),             # low-e (Laplace forced)
    ],
)
def test_patch_evaluator_matches_direct_formula(
    body: str, jd_delta_days: float
) -> None:
    """The patch's Newton-Kepler evaluator agrees with an independent
    closed-form implementation to within 2 residue units (machine
    precision on the integer round-trip)."""
    patch = eoc_catalog.EOC_CATALOG[body]
    body_to_idx = {body: 0}
    jd = JD_J2000 + jd_delta_days
    contributions = patch.evaluate(jd, body_to_idx)
    patch_residue = contributions[0]
    direct_residue = _direct_eoc_residue(
        patch.eccentricity,
        patch.mean_anomaly_at_j2000_rad,
        patch.n_rad_per_day,
        jd_delta_days,
    )
    assert abs(patch_residue - direct_residue) <= 2, (
        f"{body}: patch={patch_residue}, direct={direct_residue}, "
        f"diff={patch_residue - direct_residue}"
    )


# ─────────────────────────────────────────────────────────────────────
# 4. J2000 anchoring — every patch returns 0 at Δt=0
# ─────────────────────────────────────────────────────────────────────


def test_every_patch_zero_at_j2000() -> None:
    """For every patch in the catalog, evaluating at JD_J2000 must
    return exactly zero residue contribution. This is the load-bearing
    BIP-anchoring property: BIP's initial_phases[i] = L_true(J2000),
    so the EOC overlay must be zero at J2000 to not double-count."""
    body_to_idx = {b: i for i, b in enumerate(sorted(eoc_catalog.EOC_CATALOG))}
    for body, patch in eoc_catalog.EOC_CATALOG.items():
        contributions = patch.evaluate(JD_J2000, body_to_idx)
        assert contributions[body_to_idx[body]] == 0, (
            f"{body}: patch evaluates to "
            f"{contributions[body_to_idx[body]]} at JD_J2000 — must be 0 "
            f"for the BIP base = L_true(J2000) anchoring to hold"
        )


# ─────────────────────────────────────────────────────────────────────
# 5. Frame discipline
# ─────────────────────────────────────────────────────────────────────


def test_helio_rows_have_no_parent() -> None:
    for body, row in secular_elements_data.SECULAR_ELEMENTS.items():
        if row.frame == "heliocentric_ecliptic":
            assert row.parent is None, (
                f"{body}: heliocentric row has parent={row.parent!r}"
            )


def test_parent_centric_rows_name_a_moon_parent() -> None:
    expected_parents = {"terra", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"}
    for body, row in secular_elements_data.SECULAR_ELEMENTS.items():
        if row.frame == "parent_centric_ecliptic":
            assert row.parent in expected_parents, (
                f"{body}: unexpected parent {row.parent!r}; expected one of {expected_parents}"
            )
            # The body is a moon in BODIES
            assert bodies.BODIES[body].category == "moon", (
                f"{body}: parent-centric frame implies category=moon "
                f"but BODIES says {bodies.BODIES[body].category}"
            )


# ─────────────────────────────────────────────────────────────────────
# 6. AMSC dual-author parity
# ─────────────────────────────────────────────────────────────────────


def _amsc_rows_indexed_by_body():
    result = bridge.get_attested_dataset("secular_elements")
    assert result["ok"] is True
    return {row["data"]["body"]: row["data"] for row in result["rows"]}


def test_amsc_row_count_matches_hand_coded() -> None:
    amsc_rows = _amsc_rows_indexed_by_body()
    assert len(amsc_rows) == 51
    assert set(amsc_rows.keys()) == set(secular_elements_data.SECULAR_ELEMENTS.keys())


@pytest.mark.parametrize("body", sorted({"terra", "mars", "luna", "io", "nereid", "pluto", "charon", "ceres"}))
def test_amsc_row_matches_hand_coded_byte_for_byte(body: str) -> None:
    """The Kepler fields in the AMSC NDJSON row match the hand-coded
    SecularElements dataclass byte-for-byte. Spot-checked on 8 bodies
    spanning the eccentricity range (Charon e≈0 through Nereid e=0.75)
    and both frames."""
    amsc_rows = _amsc_rows_indexed_by_body()
    amsc = amsc_rows[body]
    hand = secular_elements_data.SECULAR_ELEMENTS[body]
    assert amsc["e"] == hand.e
    assert amsc["I_deg"] == hand.I_deg
    assert amsc["Omega_deg"] == hand.Omega_deg
    assert amsc["omega_bar_deg"] == hand.omega_bar_deg
    assert amsc["L0_deg"] == hand.L0_deg
    assert amsc["n_deg_per_day"] == hand.n_deg_per_day
    assert amsc["frame"] == hand.frame
    assert amsc["parent"] == hand.parent
    assert amsc["notes"] == hand.notes


def test_amsc_all_rows_have_provenance() -> None:
    """Every AMSC row carries a non-empty source_doi, source_published_date,
    and entered_locally_at. No placeholders."""
    amsc_rows = _amsc_rows_indexed_by_body()
    for body, data in amsc_rows.items():
        assert data.get("source_doi"), f"{body}: empty source_doi"
        assert data.get("source_published_date"), (
            f"{body}: empty source_published_date"
        )
        assert data.get("entered_locally_at"), (
            f"{body}: empty entered_locally_at"
        )
        # The published date must be ISO 8601 YYYY-MM-DD
        assert len(data["source_published_date"]) == 10, (
            f"{body}: published date {data['source_published_date']!r} "
            f"not ISO 8601"
        )


def test_amsc_source_doi_uses_known_prefix_convention() -> None:
    """source_doi values follow the v0.27.0-phase-A convention: real
    Crossref DOIs (10.xxxx/...), nodoi: prefix, isbn: prefix, or url:
    prefix. No bare-string / placeholder values."""
    amsc_rows = _amsc_rows_indexed_by_body()
    KNOWN_PREFIXES = ("10.", "nodoi:", "isbn:", "url:")
    for body, data in amsc_rows.items():
        doi = data["source_doi"]
        assert any(doi.startswith(p) for p in KNOWN_PREFIXES), (
            f"{body}: source_doi {doi!r} does not start with any "
            f"of {KNOWN_PREFIXES}"
        )


# ─────────────────────────────────────────────────────────────────────
# 7. Bridge filter semantics
# ─────────────────────────────────────────────────────────────────────


def test_bridge_list_secular_elements_no_filter() -> None:
    r = bridge.list_secular_elements()
    assert r["ok"] is True
    assert r["n_rows"] == 51


def test_bridge_list_secular_elements_helio_filter() -> None:
    r = bridge.list_secular_elements(frame="heliocentric_ecliptic")
    assert r["ok"] is True
    assert r["n_rows"] == 13


def test_bridge_list_secular_elements_parent_filter() -> None:
    r = bridge.list_secular_elements(parent="jupiter")
    assert r["ok"] is True
    assert r["n_rows"] == 11   # 4 inner + 4 Galileans + 3 irregulars


def test_bridge_list_secular_elements_parent_saturn() -> None:
    r = bridge.list_secular_elements(parent="saturn")
    assert r["ok"] is True
    assert r["n_rows"] == 15  # 9 classical + 2 co-orbitals + 4 trojans


def test_bridge_get_secular_elements_sun_rejected() -> None:
    r = bridge.get_secular_elements("sun")
    assert r["ok"] is False
    assert "Sun is excluded" in r["error"]


def test_bridge_list_eoc_patches_no_filter() -> None:
    r = bridge.list_eoc_patches()
    assert r["ok"] is True
    assert r["n_patches"] == 51


def test_bridge_get_eoc_patch_nereid_high_e() -> None:
    r = bridge.get_eoc_patch("nereid")
    assert r["ok"] is True
    assert r["kind"] == "eccentricity-correction"
    assert r["eccentricity"] == pytest.approx(0.7507, abs=1e-6)


# ─────────────────────────────────────────────────────────────────────
# 8. Apply / clear round trip
# ─────────────────────────────────────────────────────────────────────


def test_apply_then_clear_round_trip() -> None:
    diagnosed_fibers.clear_patches()
    assert len(diagnosed_fibers.snapshot()) == 0
    r = bridge.apply_eoc_patches()
    assert r["ok"] is True
    assert r["n_registered"] == 51
    assert r["n_active_total"] == 51
    cleared = bridge.clear_eoc_patches()
    assert cleared["cleared"] == 51
    assert cleared["n_active_total"] == 0


def test_apply_with_body_whitelist() -> None:
    diagnosed_fibers.clear_patches()
    r = bridge.apply_eoc_patches(bodies=["terra", "mars"])
    assert r["ok"] is True
    assert r["n_registered"] == 2
    assert sorted(r["registered"]) == [
        "mars-eoc-newton-kepler", "terra-eoc-newton-kepler"
    ]
    bridge.clear_eoc_patches()


def test_apply_with_unknown_body_errors() -> None:
    diagnosed_fibers.clear_patches()
    r = bridge.apply_eoc_patches(bodies=["sun", "xkcd"])
    assert r["ok"] is False
    assert "unknown body" in r["error"]


def test_apply_intersects_filters() -> None:
    """frame=helio AND parent=jupiter is empty (Jupiter is heliocentric
    itself, but its moons are parent_centric; no row has frame=helio
    AND parent=jupiter)."""
    diagnosed_fibers.clear_patches()
    r = bridge.apply_eoc_patches(frame="heliocentric_ecliptic", parent="jupiter")
    assert r["ok"] is True
    assert r["n_registered"] == 0


# ─────────────────────────────────────────────────────────────────────
# 9. parity_smoke baseline
# ─────────────────────────────────────────────────────────────────────


def test_eoc_patch_kind_now_c_native() -> None:
    """v0.28.0rc5 (ABI v9) flips the rc1 python-only ratchet.

    The eccentricity-correction patch kind is now supported on BOTH
    backends. The C-side `es_patches.c` implements the Newton-Kepler
    evaluator (see ``es_eval_eoc_residue``); the Python BIP encoder
    has the same evaluator since rc1. The mirror call must succeed
    when HAS_NATIVE — proving the rc1 backend_caveat is closed.

    Negative ratchet: if a future commit breaks C-side EOC support,
    this test fails clearly, signalling the rc1 caveat language has
    to come back in the docstring + ROADMAP simultaneously."""
    patch = eoc_catalog.EOC_CATALOG["mars"]
    assert patch.kind == "eccentricity-correction"
    from ephemerides_spectral.bridge import _mirror_patch_to_native
    from ephemerides_spectral import _native_bip

    # Clear any prior native-side state from earlier tests so the
    # mirror call's duplicate-name check stays clean.
    if _native_bip.HAS_NATIVE:
        _native_bip.native_clear_eoc_patches()

    rc = _mirror_patch_to_native(patch)
    if _native_bip.HAS_NATIVE:
        assert rc is None, (
            f"C-side EOC mirror failed: {rc!r}. ABI v9 EOC support is "
            f"the load-bearing rc5 deliverable; if this test fails, "
            f"either the wheel was built against an older ABI or the "
            f"C-side Newton-Kepler evaluator regressed."
        )
        # Clean up so the test doesn't leak state into later tests.
        _native_bip.native_clear_eoc_patches()
    else:
        # Pure-Python / Pyodide install: mirror returns None silently
        # (the bridge's _mirror_patch_to_native checks HAS_NATIVE first
        # and returns None without dispatching). This branch
        # documents the expected behaviour on installs without C.
        assert rc is None


def test_eoc_patch_byte_parity_across_backends() -> None:
    """rc5 deliverable: with an EOC patch registered, encoding via the
    Python BIP encoder and the C-side encoder must produce byte-
    identical phase residues. Pinned at four Δt epochs (J2000,
    J2000+1yr, J2000+20yr, J2000-100yr) consistent with the wheel-
    matrix native-parity test.

    Skipped on pure-Python installs (no C backend to compare against)."""
    from ephemerides_spectral import _native_bip, default_encode
    if not _native_bip.HAS_NATIVE:
        pytest.skip("native library not loaded; cross-backend parity N/A")
    from ephemerides_spectral._research.ephemeris_reference_instrument import (
        REFERENCE_JD,
    )
    from ephemerides_spectral import bridge

    # Clean slate on both registries.
    bridge.clear_eoc_patches()

    # Register Earth + Mars EOC patches (the canonical Phase 10a pair).
    result = bridge.apply_eoc_patches(bodies=["terra", "mars"])
    assert result["ok"] is True
    assert result["n_registered"] == 2
    assert result["n_registered_c_side"] == 2
    assert "bip" in result["backends_active"]
    assert "c" in result["backends_active"]

    try:
        for delta_t_yr in [0.0, 1.0, 20.0, -100.0]:
            jd = REFERENCE_JD + delta_t_yr * 365.25
            py = default_encode(jd, backend="bip", kernel="de421")
            c  = default_encode(jd, backend="c",   kernel="de421")
            assert (py == c).all(), (
                f"EOC-patched native vs Python phases differ at "
                f"delta_t = {delta_t_yr} yr.\n"
                f"  python: {py.tolist()}\n"
                f"  native: {c.tolist()}"
            )
    finally:
        # Always clean up the registries, even on parity failure.
        bridge.clear_eoc_patches()
