"""Three-way byte-exact parity check: Python BIP ↔ native C BIP.

Skipped when the native library isn't loaded (sdist installs without
C toolchain, Pyodide / WASM, the pure-Python fallback wheel). When it
runs, it pins:

* The native ABI version matches what the Python shim expects.
* `default_encode(jd, backend="c")` returns the same uint32[26]
  array as `default_encode(jd, backend="bip")` for a representative
  JD ladder spanning J2000 ± 100 yr.
* `bridge.get_system_state(jd, backend="c")` reports
  ``backend="c"`` (not the fallback "bip") AND the phase residues
  match the bridge's pure-Python path byte-for-byte.

If the parity fails, either the C codegen drifted from the Python
research source (re-run `c/codegen/emit_c_tables.py`) or one of the
two paths has a real bug. The DE441 sweep findings are calibrated
on the Python path; the native path must agree exactly to be a
drop-in replacement.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import _native_bip, default_encode, bridge


pytestmark = pytest.mark.skipif(
    not _native_bip.HAS_NATIVE,
    reason=(
        "native library not loaded; pure-Python fallback in effect. "
        f"Reason: {_native_bip.LOAD_ERROR}"
    ),
)


def test_native_abi_version_matches() -> None:
    """ABI version baked into the binary must match what the shim expects."""
    assert _native_bip.ABI_VERSION == _native_bip.EXPECTED_ABI_VERSION


def test_native_n_bodies_matches_python() -> None:
    """N_BODIES from the C side must equal what the Python research roster has."""
    from ephemerides_spectral._research.bodies import BODIES
    assert _native_bip.N_BODIES == len(BODIES)


def test_native_version_string_matches_package_version() -> None:
    """C-side ES_VERSION_STRING must match the Python wheel's __version__."""
    from ephemerides_spectral.version import __version__
    native = _native_bip.native_version()
    assert native == __version__, (
        f"version drift: native = {native!r}, package = {__version__!r}. "
        "Bump c/include/ephemerides_spectral.h in lockstep with "
        "python/pyproject.toml."
    )


@pytest.mark.parametrize("delta_t_yr", [
    0.0,
    1.0, -1.0,
    20.0, -20.0,
    100.0, -100.0,
])
def test_default_encode_native_matches_python(delta_t_yr: float) -> None:
    """default_encode(backend='c') ≡ default_encode(backend='bip') byte-for-byte."""
    from ephemerides_spectral._research.ephemeris_reference_instrument import (
        REFERENCE_JD,
    )
    jd = REFERENCE_JD + delta_t_yr * 365.25
    from ephemerides_spectral._research.bodies import BODIES
    expected_n = len(BODIES)
    py_phases = default_encode(jd, backend="bip", kernel="de421")
    c_phases = default_encode(jd, backend="c", kernel="de421")
    # v0.31.0rc4: both backends return array('I') (numpy-free).
    assert py_phases.typecode == c_phases.typecode == "I", "typecodes must match"
    assert len(py_phases) == len(c_phases) == expected_n
    py_list = py_phases.tolist()
    c_list = c_phases.tolist()
    # Byte-for-byte agreement.
    assert py_list == c_list, (
        f"native vs python phases differ at delta_t = {delta_t_yr} yr.\n"
        f"  python: {py_list}\n"
        f"  native: {c_list}\n"
        f"  diff:   {[a - b for a, b in zip(py_list, c_list)]}"
    )


def test_bridge_backend_c_reports_native() -> None:
    """bridge.get_system_state(backend='c') must report backend='c' (not the fallback)."""
    from ephemerides_spectral._research.ephemeris_reference_instrument import (
        REFERENCE_JD,
    )
    out = bridge.get_system_state(jd_tdb=REFERENCE_JD,
                                  backend="c", kernel="de421")
    assert out["ok"] is True
    assert out["backend"] == "c", (
        f"expected backend='c' but got backend={out['backend']!r}; "
        "the native fallback path activated when the binary should be loaded."
    )
    assert out["backend_requested"] == "c"


def test_bridge_backend_c_phases_match_bip() -> None:
    """bridge backend='c' phases byte-match backend='bip' phases."""
    from ephemerides_spectral._research.ephemeris_reference_instrument import (
        REFERENCE_JD,
    )
    jd = REFERENCE_JD + 20.0 * 365.25
    py = bridge.get_system_state(jd_tdb=jd, backend="bip", kernel="de421")
    c = bridge.get_system_state(jd_tdb=jd, backend="c", kernel="de421")
    assert py["ok"] is True
    assert c["ok"] is True
    assert py["phases_uint32"] == c["phases_uint32"], (
        f"bridge phases differ between backends at +20 yr.\n"
        f"  bip: {py['phases_uint32']}\n"
        f"  c:   {c['phases_uint32']}"
    )


# ──────────────────────────────────────────────────────────────────────
# PR-c (v0.28.0rc4) — profile-tier call-site migration
# ──────────────────────────────────────────────────────────────────────


def test_load_source_is_srmech_profile_when_available() -> None:
    """When srmech + ephemerides plugin tier are present, _native_bip
    must load THROUGH the srmech profile (single shared CDLL handle),
    not through the direct ctypes fallback. Pins the PR-c migration:
    the bridge call sites and srmech profile callers see object-
    identical native library state."""
    try:
        import srmech  # noqa: F401
    except ImportError:
        pytest.skip("srmech not installed; LOAD_SOURCE check N/A")
    profile = srmech.profile("ephemerides")
    if profile.native is None:
        pytest.skip(
            "srmech profile registered but plugin tier did not load "
            "(pure-Python wheel?); LOAD_SOURCE check N/A"
        )
    assert _native_bip.LOAD_SOURCE == "srmech_profile", (
        f"expected LOAD_SOURCE='srmech_profile' (the profile-tier "
        f"path), got {_native_bip.LOAD_SOURCE!r}. The PR-c migration "
        f"silently fell back to direct ctypes."
    )


def test_lib_is_same_object_as_profile_native() -> None:
    """_native_bip.LIB and srmech.profile('ephemerides').native must
    be the SAME ctypes.CDLL object (identity, not equality). Catches
    the regression class where ephemerides-spectral re-opens the
    library and ends up with a second CDLL instance that doesn't
    share patch-registry / coupling-table runtime state with the
    srmech-loaded one."""
    try:
        import srmech  # noqa: F401
    except ImportError:
        pytest.skip("srmech not installed; identity check N/A")
    profile = srmech.profile("ephemerides")
    if profile.native is None:
        pytest.skip("plugin tier not loaded; identity check N/A")
    assert _native_bip.LIB is profile.native, (
        "_native_bip.LIB is not the same object as "
        "srmech.profile('ephemerides').native. PR-c's "
        "_load_via_srmech_profile() should have wired the same CDLL "
        "handle into both surfaces; a fresh ctypes.CDLL() call "
        "happened somewhere."
    )


def test_profile_native_encode_matches_direct_ctypes_encode() -> None:
    """Open a SECOND independent ctypes.CDLL on the same library file
    and prove its es_encode_state() output byte-matches the profile-
    loaded path. This pins that the byte-parity property is a
    property of the *library file*, not an artifact of single-handle
    coincidence — defends PR-c's migration against the hypothetical
    'profile path returns garbage and direct returns garbage and
    they happen to match because they're the same object' bug."""
    import ctypes
    from ephemerides_spectral._research.ephemeris_reference_instrument import (
        REFERENCE_JD,
    )
    if _native_bip.LIB is None or _native_bip.LIB_PATH is None:
        pytest.skip("native not loaded; cannot run dual-handle parity")

    # Fresh, independent CDLL on the same library file.
    fresh_lib = ctypes.CDLL(str(_native_bip.LIB_PATH))
    fresh_lib.es_encode_state.argtypes = [
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    fresh_lib.es_encode_state.restype = ctypes.c_int
    fresh_lib.es_n_bodies.argtypes = []
    fresh_lib.es_n_bodies.restype = ctypes.c_int

    n = fresh_lib.es_n_bodies()
    from array import array
    for delta_t_days in [0.0, 365.25, 20 * 365.25, -100 * 365.25]:
        # v0.31.0rc4: numpy-free buffers — stdlib array('I') + ctypes.
        # Via the profile-loaded handle (= _native_bip.LIB).
        profile_buf = array("I", [0]) * n
        p_ptr = (ctypes.c_uint32 * n).from_buffer(profile_buf)
        rc1 = _native_bip.LIB.es_encode_state(
            ctypes.c_double(delta_t_days),
            ctypes.cast(p_ptr, ctypes.POINTER(ctypes.c_uint32)),
        )
        assert rc1 == 0, f"profile handle es_encode_state returned {rc1}"

        # Via the fresh CDLL handle.
        fresh_buf = array("I", [0]) * n
        f_ptr = (ctypes.c_uint32 * n).from_buffer(fresh_buf)
        rc2 = fresh_lib.es_encode_state(
            ctypes.c_double(delta_t_days),
            ctypes.cast(f_ptr, ctypes.POINTER(ctypes.c_uint32)),
        )
        assert rc2 == 0, f"fresh handle es_encode_state returned {rc2}"

        assert profile_buf.tolist() == fresh_buf.tolist(), (
            f"profile-loaded vs fresh-CDLL phases differ at "
            f"delta_t={delta_t_days} d.\n"
            f"  profile: {profile_buf.tolist()}\n"
            f"  fresh:   {fresh_buf.tolist()}"
        )
