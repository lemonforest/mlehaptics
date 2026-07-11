"""test_native_parity — the [profile.native] scaffold proof.

Asserts the whole chain works end-to-end:
  1. libsiona_native.so loads (siona._native.HAS_NATIVE) with the ABI handshake.
  2. The native op == the validated pure-Python reference, bit-for-bit, over
     many inputs (the has_native dispatch is value-identical either way).
  3. srmech's profile_loader picks the SAME lib up as srmech.profile("siona").native
     (a "plugin"-kind Profile, not "simple").

Skips gracefully (not fails) when the .so is absent — a pure-Python-only install
(Pyodide/WASM or a source checkout with no `make -C c`) is a supported mode.
"""
import pytest

from siona import _native


def test_native_loaded_or_skipped():
    if not _native.HAS_NATIVE:
        pytest.skip(f"libsiona_native.so absent (pure-Python mode): {_native.LOAD_ERROR}")
    st = _native.native_status()
    assert st["has_native"] is True
    assert st["abi_version"] == _native.EXPECTED_ABI_VERSION
    assert st["library_path"] is not None


@pytest.mark.parametrize("data", [
    b"", b"a", b"srmech", b"the quick brown fox",
    b"\x00\x01\x02\xff", bytes(range(256)), b"x" * 4096,
    "σ_OC ≠ σ_SC".encode("utf-8"), "café — naïve".encode("utf-8"),
])
def test_fnv1a64_parity(data):
    """native == pure-Python reference, bit-for-bit."""
    py = _native._fnv1a64_py(data)
    got = _native.fnv1a64(data)               # dispatches native when present
    assert got == py, f"dispatch != reference for {data!r}"
    if _native.HAS_NATIVE:
        assert int(_native._LIB.siona_native_fnv1a64(data, len(data))) == py


def test_fnv1a64_known_vector():
    """Anchor to the published FNV-1a-64 test vector (de-magics the constant)."""
    # FNV-1a-64("") = the offset basis; FNV-1a-64("a") is the canonical first step.
    assert _native.fnv1a64(b"") == 14695981039346656037
    assert _native.fnv1a64(b"a") == 12638187200555641996


def test_profile_native_surface():
    """srmech's profile_loader loads the SAME .so as Profile.native (plugin tier)."""
    srmech = pytest.importorskip("srmech")
    if not _native.HAS_NATIVE:
        pytest.skip("native absent; profile loads as simple-tier")
    prof = srmech.profile("siona")
    assert prof.native is not None, "profile did not load the native plugin"
    assert "plugin" in repr(prof)
    # the bound lib exposes our declared symbol
    assert hasattr(prof.native, "siona_native_fnv1a64")
