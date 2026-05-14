"""Unit tests for srmech.profile_loader (Task #199, ADR-0001).

The loader is tested without actually installing a real profile-bearing
package — instead, tests fabricate _EnumeratedDescriptor records directly
to exercise the validation, smoke-test, and activation paths.

Tests covering the entry-point discovery path require a profile to be
pip-installed, which we exercise via the integration test in the
v0.3.0 release verification flow.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

import srmech
from srmech.profile_loader import (
    SUPPORTED_PROFILE_SCHEMA_VERSION,
    InvalidProfileError,
    ProfileSchemaVersionError,
    _read_descriptor,
    _validate_descriptor,
    reset_for_testing,
)


@pytest.fixture(autouse=True)
def _reset_loader():
    """Clear the loader's caches before and after each test so tests
    don't leak state into each other."""
    reset_for_testing()
    yield
    reset_for_testing()


def _write_minimal_profile_toml(tmp_path: Path, **overrides) -> Path:
    """Helper: write a minimal valid srmech_profile.toml and return its path."""
    fields = {
        "name": "test_profile",
        "version": "1.0.0",
        "summary": "Test profile for unit tests",
        "package": "test_pkg",
        "srmech_requires": ">=0.3,<0.4",
    }
    fields.update(overrides)
    content = textwrap.dedent(f"""\
        profile_schema_version = "1.0"

        [profile]
        name = "{fields["name"]}"
        version = "{fields["version"]}"
        summary = "{fields["summary"]}"
        package = "{fields["package"]}"
        srmech_requires = "{fields["srmech_requires"]}"
    """)
    p = tmp_path / "srmech_profile.toml"
    p.write_text(content, encoding="utf-8")
    return p


# ──────────────────────────────────────────────────────────────────────
# Schema validation
# ──────────────────────────────────────────────────────────────────────


def test_minimal_valid_profile(tmp_path: Path) -> None:
    """A descriptor with only the required fields validates cleanly."""
    p = _write_minimal_profile_toml(tmp_path)
    data = _read_descriptor(p, "test")
    _validate_descriptor(data, "test")  # no exception


def test_missing_profile_schema_version(tmp_path: Path) -> None:
    """A descriptor without profile_schema_version is rejected."""
    p = tmp_path / "no_version.toml"
    p.write_text(
        '[profile]\nname = "a"\nversion = "1.0.0"\nsummary = "x"\n'
        'package = "x"\nsrmech_requires = ">=0.3"\n',
        encoding="utf-8",
    )
    data = _read_descriptor(p, "test")
    with pytest.raises(InvalidProfileError, match="profile_schema_version"):
        _validate_descriptor(data, "test")


def test_unsupported_schema_version(tmp_path: Path) -> None:
    """A descriptor against an unsupported schema version raises
    ProfileSchemaVersionError (a subclass of InvalidProfileError)."""
    content = textwrap.dedent("""\
        profile_schema_version = "99.0"

        [profile]
        name = "future"
        version = "1.0.0"
        summary = "from the future"
        package = "future_pkg"
        srmech_requires = ">=0.3"
    """)
    p = tmp_path / "future.toml"
    p.write_text(content, encoding="utf-8")
    data = _read_descriptor(p, "test")
    with pytest.raises(ProfileSchemaVersionError, match="99.0"):
        _validate_descriptor(data, "test")


def test_invalid_name_pattern(tmp_path: Path) -> None:
    """profile.name must match the allowed character set."""
    p = _write_minimal_profile_toml(tmp_path, name="InvalidName")  # uppercase
    data = _read_descriptor(p, "test")
    with pytest.raises(InvalidProfileError, match="name"):
        _validate_descriptor(data, "test")


def test_invalid_version_pattern(tmp_path: Path) -> None:
    """profile.version must match MAJOR.MINOR.PATCH[rcN]."""
    p = _write_minimal_profile_toml(tmp_path, version="not-a-version")
    data = _read_descriptor(p, "test")
    with pytest.raises(InvalidProfileError, match="version"):
        _validate_descriptor(data, "test")


def test_rc_version_accepted(tmp_path: Path) -> None:
    """RC version syntax (0.1.0rc1) is valid."""
    p = _write_minimal_profile_toml(tmp_path, version="0.1.0rc1")
    data = _read_descriptor(p, "test")
    _validate_descriptor(data, "test")  # no exception


def test_bridge_target_must_match_dotted_callable(tmp_path: Path) -> None:
    """Bridge surface values must be 'module:callable' shape."""
    p = tmp_path / "bad_bridge.toml"
    p.write_text(textwrap.dedent("""\
        profile_schema_version = "1.0"

        [profile]
        name = "bb"
        version = "0.0.1"
        summary = "Bad bridge target"
        package = "bb_pkg"
        srmech_requires = ">=0.3"

        [profile.bridge]
        get_thing = "not_a_valid_target"
    """), encoding="utf-8")
    data = _read_descriptor(p, "test")
    with pytest.raises(InvalidProfileError, match="bridge"):
        _validate_descriptor(data, "test")


def test_native_block_required_fields(tmp_path: Path) -> None:
    """The [profile.native] block requires library, install_path,
    abi_version_function, expected_abi_version."""
    p = tmp_path / "bad_native.toml"
    p.write_text(textwrap.dedent("""\
        profile_schema_version = "1.0"

        [profile]
        name = "bn"
        version = "0.0.1"
        summary = "Bad native"
        package = "bn_pkg"
        srmech_requires = ">=0.3"

        [profile.native]
        library = "thing"
        # missing install_path + abi_version_function + expected_abi_version
    """), encoding="utf-8")
    data = _read_descriptor(p, "test")
    with pytest.raises(InvalidProfileError, match="install_path"):
        _validate_descriptor(data, "test")


def test_native_block_full_valid(tmp_path: Path) -> None:
    """A complete [profile.native] block validates cleanly."""
    p = tmp_path / "good_native.toml"
    p.write_text(textwrap.dedent("""\
        profile_schema_version = "1.0"

        [profile]
        name = "gn"
        version = "0.0.1"
        summary = "Good native"
        package = "gn_pkg"
        srmech_requires = ">=0.3"

        [profile.native]
        library = "gn_native"
        install_path = "_native"
        abi_version_function = "gn_abi_version"
        expected_abi_version = 1

        [profile.native.symbols.gn_do_thing]
        argtypes = ["c_int"]
        restype = "c_int"
    """), encoding="utf-8")
    data = _read_descriptor(p, "test")
    _validate_descriptor(data, "test")


def test_interpreted_block_warns_but_does_not_fail(tmp_path: Path) -> None:
    """[profile.interpreted] is RESERVED; v0.3.0 issues FutureWarning
    but the descriptor validates."""
    p = tmp_path / "interpreted.toml"
    p.write_text(textwrap.dedent("""\
        profile_schema_version = "1.0"

        [profile]
        name = "interp"
        version = "0.0.1"
        summary = "Interpreted-runtime plugin (reserved)"
        package = "interp_pkg"
        srmech_requires = ">=0.3"

        [profile.interpreted]
        runtime = "julia"
        script = "main.jl"
    """), encoding="utf-8")
    data = _read_descriptor(p, "test")
    with pytest.warns(FutureWarning, match="interpreted"):
        _validate_descriptor(data, "test")


# ──────────────────────────────────────────────────────────────────────
# Public API surface
# ──────────────────────────────────────────────────────────────────────


def test_list_profiles_returns_dict() -> None:
    """list_profiles returns a dict (possibly empty); no profile
    fixtures installed → empty."""
    out = srmech.list_profiles()
    assert isinstance(out, dict)
    # No real profile entry points installed in this test environment;
    # may be 0 or may pick up a future fixture. Either is acceptable.


def test_profile_unknown_raises() -> None:
    """Requesting an unknown profile raises ProfileNotFoundError."""
    with pytest.raises(srmech.ProfileNotFoundError, match="no profile named"):
        srmech.profile("definitely_not_a_real_profile_name")


def test_supported_schema_version_is_1_0() -> None:
    """Sanity: srmech v0.3.x speaks profile_schema_version 1.0."""
    assert SUPPORTED_PROFILE_SCHEMA_VERSION == "1.0"


def test_profile_loader_constants_exported() -> None:
    """The error classes + APIs are exposed at the top-level srmech
    package, not just under srmech.profile_loader."""
    # Imported into srmech.__all__
    assert hasattr(srmech, "profile")
    assert hasattr(srmech, "list_profiles")
    assert hasattr(srmech, "Profile")
    assert hasattr(srmech, "ProfileError")
    assert hasattr(srmech, "ProfileNotFoundError")
    assert hasattr(srmech, "InvalidProfileError")
    assert hasattr(srmech, "SmokeTestFailedError")
    assert hasattr(srmech, "AbiMismatchError")
    assert hasattr(srmech, "ProfileSchemaVersionError")
    assert hasattr(srmech, "ProfileStatus")
