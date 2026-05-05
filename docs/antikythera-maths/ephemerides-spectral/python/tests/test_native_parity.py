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
    assert py_phases.shape == c_phases.shape == (expected_n,)
    assert py_phases.dtype == c_phases.dtype, "dtypes must match"
    # Byte-for-byte agreement.
    assert (py_phases == c_phases).all(), (
        f"native vs python phases differ at delta_t = {delta_t_yr} yr.\n"
        f"  python: {py_phases.tolist()}\n"
        f"  native: {c_phases.tolist()}\n"
        f"  diff:   {(py_phases.astype(int) - c_phases.astype(int)).tolist()}"
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
