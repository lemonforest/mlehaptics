"""srmech profile-pattern integration tests.

Ratchets the v0.27.0 simple-tier surface (PR-a: [profile.bridge] +
[profile.smoke_test] + [profile.tool_schema]) plus the v0.28.0rc2
plugin-tier addition (PR-b: [profile.native] block + ABI handshake).

The simple-tier tests run everywhere (Python BIP wheel or native).
The plugin-tier tests require srmech to be importable AND the native
library to be present in the installed wheel — skipped otherwise
with a marker that surfaces the reason (pure-Python wheel vs missing
srmech vs ABI mismatch).

Discipline:
  * Static descriptor checks (TOML parses + required fields present)
    do not need srmech installed; they validate via tomllib only.
  * Activation-path checks (srmech.profile("ephemerides")) require
    srmech and the plugin-tier wheel.
"""

from __future__ import annotations

import importlib.resources
import sys
from pathlib import Path

import pytest

# tomllib landed in stdlib at Python 3.11; fall back to the tomli
# backport on 3.10 (the package's minimum). Mirrors the same pattern
# used in codegen/regenerate.py.
if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


# ──────────────────────────────────────────────────────────────────────
# Static descriptor checks (no srmech required)
# ──────────────────────────────────────────────────────────────────────


def _load_descriptor() -> dict:
    """Read srmech_profile.toml from the installed package."""
    pkg_files = importlib.resources.files("ephemerides_spectral")
    descriptor_path = pkg_files / "srmech_profile.toml"
    with descriptor_path.open("rb") as f:
        return tomllib.load(f)


def test_descriptor_has_profile_native_block() -> None:
    """v0.28.0rc2 PR-b: [profile.native] block declared."""
    raw = _load_descriptor()
    assert "native" in raw["profile"], (
        "Missing [profile.native] block — required for plugin-tier "
        "activation per ADR-0001 §5."
    )


def test_profile_native_required_fields_present() -> None:
    """Schema-required fields per docs/srmech/adr/0001-profile-pattern.schema.json."""
    raw = _load_descriptor()
    n = raw["profile"]["native"]
    required = {"library", "install_path", "abi_version_function",
                "expected_abi_version"}
    missing = required - n.keys()
    assert not missing, f"[profile.native] missing required fields: {missing}"


def test_profile_native_expected_abi_version_matches_native_bip() -> None:
    """The descriptor's expected_abi_version MUST match what
    ephemerides-spectral's own ctypes shim expects. Drift here is
    the v0.27.0/v0.28.0rc1 silent-rejection bug that PR-b closes."""
    from ephemerides_spectral import _native_bip
    raw = _load_descriptor()
    declared = raw["profile"]["native"]["expected_abi_version"]
    shim = _native_bip.EXPECTED_ABI_VERSION
    assert declared == shim, (
        f"[profile.native].expected_abi_version={declared} but "
        f"_native_bip.EXPECTED_ABI_VERSION={shim}. These two MUST agree "
        f"or the plugin-tier profile will silently load a library that "
        f"the package's own shim rejects."
    )


def test_profile_native_library_basename_matches_wheel_layout() -> None:
    """The declared library basename must match what's in the wheel."""
    raw = _load_descriptor()
    assert raw["profile"]["native"]["library"] == "ephemerides_spectral"


def test_profile_native_install_path_is_native_subdir() -> None:
    raw = _load_descriptor()
    assert raw["profile"]["native"]["install_path"] == (
        "ephemerides_spectral/_native"
    )


def test_profile_native_abi_version_function_is_es_abi_version() -> None:
    raw = _load_descriptor()
    assert raw["profile"]["native"]["abi_version_function"] == "es_abi_version"


def test_profile_native_declares_encoder_hot_path_symbols() -> None:
    """The encoder hot path + introspection accessors MUST be declared
    so PR-c's bridge call-site migration can bind them via the
    profile-tier handle."""
    raw = _load_descriptor()
    symbols = raw["profile"]["native"].get("symbols", {})
    required = {
        "es_version", "es_abi_version", "es_n_bodies", "es_body_index",
        "es_encode_state", "es_encode_at_jd", "es_cos_lut",
        "es_residue_to_radians",
    }
    missing = required - symbols.keys()
    assert not missing, (
        f"[profile.native.symbols] missing encoder hot path declarations: "
        f"{missing}"
    )


def test_profile_native_symbol_entries_have_argtypes_and_restype() -> None:
    """Per the schema, each symbol entry is {argtypes, restype}."""
    raw = _load_descriptor()
    for sym_name, sig in raw["profile"]["native"].get("symbols", {}).items():
        assert "argtypes" in sig, f"symbol {sym_name!r} missing argtypes"
        assert "restype" in sig, f"symbol {sym_name!r} missing restype"
        assert isinstance(sig["argtypes"], list), (
            f"symbol {sym_name!r} argtypes must be a list"
        )
        assert isinstance(sig["restype"], str), (
            f"symbol {sym_name!r} restype must be a string"
        )


# ──────────────────────────────────────────────────────────────────────
# Activation-path checks (require srmech + native wheel)
# ──────────────────────────────────────────────────────────────────────


srmech = pytest.importorskip("srmech")


def _can_load_native() -> tuple[bool, str]:
    """Return (loadable, reason). Loadable = the wheel ships a native
    library AND the ABI handshake succeeds."""
    from ephemerides_spectral import _native_bip
    if not _native_bip.HAS_NATIVE:
        return False, f"_native_bip not available: {_native_bip.LOAD_ERROR}"
    return True, ""


def test_profile_activation_resolves_ephemerides() -> None:
    """srmech.profile('ephemerides') resolves the descriptor.

    Requires the ephemerides-spectral package to be installed via a
    proper wheel / pip install (entry-point discovery walks the
    installed-package metadata; source-tree shadowing has no
    entry-point registration). Skipped cleanly when the profile is
    not registered — the source-tree test run and CI smoke take
    this branch."""
    try:
        p = srmech.profile("ephemerides")
    except srmech.ProfileNotFoundError:
        pytest.skip(
            "ephemerides profile not registered as an entry point "
            "(source-tree install or non-pip install); profile "
            "activation tests require a proper wheel install"
        )
    assert p.name == "ephemerides"


def test_profile_native_loaded_when_wheel_has_native_lib() -> None:
    """On platform wheels, srmech's loader must populate p.native."""
    loadable, reason = _can_load_native()
    if not loadable:
        pytest.skip(f"pure-Python install or load error: {reason}")
    p = srmech.profile("ephemerides")
    assert p.native is not None, (
        "[profile.native] declared and the wheel ships the library, "
        "but srmech.profile('ephemerides').native is None. The plugin "
        "tier failed to load."
    )


def test_profile_native_meta_reports_abi_v8() -> None:
    loadable, reason = _can_load_native()
    if not loadable:
        pytest.skip(f"pure-Python install or load error: {reason}")
    p = srmech.profile("ephemerides")
    assert p._native_meta is not None
    assert p._native_meta["abi_version"] == 8, (
        f"Plugin-tier ABI handshake reported "
        f"{p._native_meta['abi_version']}, expected 8."
    )


def test_profile_repr_says_plugin_tier_when_native_loaded() -> None:
    loadable, reason = _can_load_native()
    if not loadable:
        pytest.skip(f"pure-Python install or load error: {reason}")
    p = srmech.profile("ephemerides")
    assert "(plugin)" in repr(p), (
        f"Profile repr should mark plugin-tier when native is loaded; "
        f"got {repr(p)!r}"
    )


def test_profile_native_resolves_declared_symbols() -> None:
    """Every symbol declared in [profile.native.symbols] MUST resolve
    via getattr(p.native, sym_name) — proves the wheel's library
    exports them."""
    loadable, reason = _can_load_native()
    if not loadable:
        pytest.skip(f"pure-Python install or load error: {reason}")
    p = srmech.profile("ephemerides")
    raw = _load_descriptor()
    for sym_name in raw["profile"]["native"].get("symbols", {}):
        sym = getattr(p.native, sym_name, None)
        assert sym is not None, (
            f"Declared symbol {sym_name!r} not exported by the native "
            f"library at {p._native_meta['library_path']}"
        )
