"""rc394 / `#T907` slice 4 (FINAL) — the last two stdlib-only TOML consumers now
self-host on srmech's own internal TOML front door, closing the 6-module migration.

The `#T907` arc replaced ``tomllib``/``tomli`` direct reads with ``srmech._toml``
(native ``srmech_toml`` parser first, stdlib floor otherwise) module-by-module:

* rc391 landed ``srmech._toml.loads``/``load`` and proved corpus-wide parity.
* rc392 repointed the two DSL catalog loaders.
* rc393 repointed the two AMSC loaders + the descriptor-hash gate.
* **rc394 (this slice)** repoints the LAST two stdlib-only loaders:
  - ``srmech.profile_loader._read_descriptor`` (reads a ``srmech_profile.toml``)
    and ``srmech.profile_loader._read_smoke_cache`` (reads a smoke-test cache TOML,
    catching ``tomllib.TOMLDecodeError`` on a malformed file → cache miss).
  - ``srmech.introspect.tool_schema.load_extension_file`` (reads a profile's
    tool-schema extension TOML: ``[[tools]]`` + ``[[tools.parameters]]``).

After this slice EVERY stdlib-only TOML consumer in ``srmech/`` routes through the
C ``srmech_toml`` parser wherever the native library is present; ``tomllib`` /
``tomli`` is retained ONLY as the pure / Pyodide fallback (and, in
``profile_loader``, for the ``except tomllib.TOMLDecodeError`` exception type).

THE INVARIANT this file certifies: for each of the three loaders, the value parsed
THROUGH the repointed loader is identical to a direct ``tomllib`` parse of the same
bytes — the repoint changed which parser ran, nothing observable. It holds because
``srmech._toml.load`` yields a dict equal to ``tomllib.load`` (rc391's oracle). The
synthesized fixtures are FLOAT-FREE (nested tables + arrays-of-tables + ``required``
bools + strings + decimal ints), so the C parser SELF-HOSTS every one and the
decline-set is empty; the C-path assertions are native-guarded via
``require_native`` (the `#T843` contract), while the dict-parity + error-contract
assertions are UNIVERSAL (they hold on the pure shard too, where both sides use
tomllib).

numpy-free by construction (stdlib ``tomllib`` / ``pathlib`` / ``os`` only).
"""

from __future__ import annotations

import sys

import pytest

from srmech import _native
from srmech import _toml as _frontdoor
from srmech import profile_loader as _pl
from srmech.introspect import tool_schema as _ts
from tests._native_gate import require_native

if sys.version_info >= (3, 11):
    import tomllib as _stdlib_toml
else:  # pragma: no cover — 3.10 back-port
    import tomli as _stdlib_toml  # type: ignore[no-redef]


# ── Representative, FLOAT-FREE fixtures (so the C parser self-hosts them) ─────

#: A ``srmech_profile.toml`` descriptor: nested tables (``[profile.metadata]``),
#: arrays-of-tables (``[[profile.capabilities]]``), bools, string arrays, strings.
_PROFILE_TOML = """\
profile_schema_version = "1.0"

[profile]
name = "rc394-demo-profile"
version = "2.3.0"
summary = "Representative srmech profile descriptor for rc394 self-host parity."
package = "rc394_demo_pkg"
enabled = true

[profile.metadata]
maintainer = "srmech"
tags = ["spectral", "demo", "rc394"]

[[profile.capabilities]]
name = "cyclic"
klass = "I"
native = true

[[profile.capabilities]]
name = "rational"
klass = "N"
native = false
"""

#: A smoke-test cache entry — the exact shape ``_write_smoke_cache`` emits:
#: a ``[smoke_test]`` table of strings + decimal ints (float-free).
_SMOKE_CACHE_TOML = """\
[smoke_test]
profile = "rc394-demo-profile"
profile_version = "2.3.0"
srmech_version = "0.9.0rc394"
ran_at = "2026-08-04T00:00:00Z"
status = "passed"
duration_ms = 42
n_assertions = 7
"""

#: A tool-schema extension TOML: ``[[tools]]`` + nested ``[[tools.parameters]]``
#: with ``required = true`` / ``false`` bools + a ``[tools.returns]`` sub-table.
_TOOL_EXTENSION_TOML = """\
[[tools]]
name = "demo.profile.op_alpha"
category = "demo"
summary = "First representative tool entry for rc394 self-host parity."

  [[tools.parameters]]
  name = "data"
  type = "bytes"
  required = true
  summary = "Bytes to process."

  [[tools.parameters]]
  name = "seed"
  type = "int"
  required = false
  summary = "Optional deterministic seed."

  [tools.returns]
  type = "str"
  shape = "64-char lowercase hex"

[[tools]]
name = "demo.profile.op_beta"
category = "demo"
summary = "Second representative tool entry (no parameters)."
"""

_ALL_FIXTURES = {
    "profile": _PROFILE_TOML,
    "smoke_cache": _SMOKE_CACHE_TOML,
    "tool_extension": _TOOL_EXTENSION_TOML,
}


# ── the repoint itself, pinned so it cannot silently revert ──────────────────

def test_loaders_reference_srmech_internal_toml_front_door() -> None:
    """Both repointed modules now bind ``srmech._toml`` under the underscore name
    ``_toml`` (kept out of ``gen_c_claims``' ``^srmech_`` bytecode scan — see the
    import comment in each module). A revert to a stdlib-only parse would unbind it."""
    assert _pl._toml is _frontdoor, (
        "srmech.profile_loader no longer routes its parse through srmech._toml")
    assert _ts._toml is _frontdoor, (
        "srmech.introspect.tool_schema no longer routes its parse through srmech._toml")


def test_profile_loader_retains_tomllib_for_the_exception_contract() -> None:
    """``profile_loader`` DELIBERATELY keeps its ``tomllib`` alias — ``_read_smoke_cache``
    catches ``tomllib.TOMLDecodeError`` to treat a malformed cache as a miss. Removing
    it would break the error contract, so pin that it stays. (``tool_schema`` has no
    such catch, so it dropped the alias entirely.)"""
    assert hasattr(_pl, "tomllib"), (
        "profile_loader dropped its tomllib alias; the except TOMLDecodeError clause "
        "in _read_smoke_cache needs it — the error contract would break")


# ── UNIVERSAL front-door parity: srmech._toml == tomllib for each fixture ─────

@pytest.mark.parametrize("name", sorted(_ALL_FIXTURES))
def test_front_door_parity_with_tomllib(name: str) -> None:
    """``srmech._toml.loads`` yields a dict equal to ``tomllib.loads`` for every
    fixture. This is the value-preserving core the three loader repoints ride on.
    UNIVERSAL: holds on the pure shard (both sides tomllib) and the native shard
    (C-parse vs tomllib-parse)."""
    text = _ALL_FIXTURES[name]
    assert _frontdoor.loads(text) == _stdlib_toml.loads(text), (
        f"srmech._toml parsed fixture {name!r} differently than tomllib")


# ── driving the ACTUAL repointed loaders (dict-identical to tomllib) ─────────

def test_read_descriptor_identical_to_tomllib(tmp_path) -> None:
    """``profile_loader._read_descriptor`` (now via ``srmech._toml``) returns a dict
    identical to a direct ``tomllib`` parse of the same ``srmech_profile.toml``."""
    p = tmp_path / "srmech_profile.toml"
    p.write_text(_PROFILE_TOML, encoding="utf-8")
    got = _pl._read_descriptor(p, "rc394-test")
    assert got == _stdlib_toml.loads(_PROFILE_TOML), (
        "_read_descriptor parsed the profile descriptor differently through the "
        "repointed loader than a direct tomllib parse")


def test_read_smoke_cache_identical_to_tomllib(tmp_path, monkeypatch) -> None:
    """``profile_loader._read_smoke_cache`` (now via ``srmech._toml``) returns a dict
    identical to a direct ``tomllib`` parse of the cache file. The cache dir is
    redirected via ``SRMECH_PROFILE_CACHE_DIR`` (the loader's own override)."""
    monkeypatch.setenv("SRMECH_PROFILE_CACHE_DIR", str(tmp_path))
    name, version = "rc394-demo-profile", "2.3.0"
    (tmp_path / f"{name}-{version}.toml").write_text(
        _SMOKE_CACHE_TOML, encoding="utf-8")
    got = _pl._read_smoke_cache(name, version)
    assert got == _stdlib_toml.loads(_SMOKE_CACHE_TOML), (
        "_read_smoke_cache parsed the cache file differently through the repointed "
        "loader than a direct tomllib parse")


def test_load_extension_file_reflects_tomllib_parse(tmp_path) -> None:
    """``tool_schema.load_extension_file`` (now via ``srmech._toml``) builds
    ``ToolEntry`` objects whose fields exactly reflect a direct ``tomllib`` parse of
    the extension TOML — proving the repointed parse fed identical data through,
    including nested ``[[tools.parameters]]`` and the ``required`` bools."""
    p = tmp_path / "tool_schema_ext.toml"
    p.write_text(_TOOL_EXTENSION_TOML, encoding="utf-8")
    entries = _ts.load_extension_file(str(p), owner="rc394-test")

    oracle = _stdlib_toml.loads(_TOOL_EXTENSION_TOML)
    oracle_tools = oracle["tools"]
    assert [e.name for e in entries] == [t["name"] for t in oracle_tools]
    assert [e.category for e in entries] == [t["category"] for t in oracle_tools]
    assert [e.summary for e in entries] == [t["summary"] for t in oracle_tools]
    assert all(e.owner == "rc394-test" for e in entries)

    # First tool: two parameters with the required bools carried through verbatim.
    op_alpha = entries[0]
    oracle_params = oracle_tools[0]["parameters"]
    assert [pm.name for pm in op_alpha.parameters] == \
        [op["name"] for op in oracle_params]
    assert [pm.type for pm in op_alpha.parameters] == \
        [op["type"] for op in oracle_params]
    assert [pm.required for pm in op_alpha.parameters] == \
        [op["required"] for op in oracle_params]
    assert op_alpha.returns is not None
    assert op_alpha.returns.type == oracle_tools[0]["returns"]["type"]
    assert op_alpha.returns.shape == oracle_tools[0]["returns"]["shape"]

    # Second tool: no parameters table → empty tuple, returns None.
    op_beta = entries[1]
    assert op_beta.parameters == ()
    assert op_beta.returns is None


# ── error contract: a malformed descriptor still raises the SAME type ────────

def test_malformed_descriptor_raises_tomldecodeerror(tmp_path) -> None:
    """A malformed ``srmech_profile.toml`` still raises ``tomllib.TOMLDecodeError``
    through ``_read_descriptor`` — the repoint did NOT change the error contract. On
    the native path the C parser DECLINES the syntax error (returns None) and control
    rides the stdlib parse, which raises the identical type; on the pure path the
    stdlib parse raises it directly."""
    bad = tmp_path / "srmech_profile.toml"
    bad.write_text('[profile\nname = "unterminated table header"\n', encoding="utf-8")
    with pytest.raises(_stdlib_toml.TOMLDecodeError):
        _pl._read_descriptor(bad, "rc394-test")


def test_malformed_smoke_cache_is_a_miss(tmp_path, monkeypatch) -> None:
    """A malformed smoke-cache file is treated as a cache MISS (``None``), unchanged
    by the repoint: ``_read_smoke_cache`` catches ``tomllib.TOMLDecodeError`` and
    ``srmech._toml.load`` propagates that same type on a malformed document."""
    monkeypatch.setenv("SRMECH_PROFILE_CACHE_DIR", str(tmp_path))
    name, version = "rc394-demo-profile", "9.9.9"
    (tmp_path / f"{name}-{version}.toml").write_text(
        "this is = = not valid toml\n", encoding="utf-8")
    assert _pl._read_smoke_cache(name, version) is None, (
        "a malformed smoke-cache file should be a cache miss (None), not an error")


# ── the C parser actually self-hosts the fixtures (native-guarded) ───────────

def test_c_path_self_hosts_the_fixtures() -> None:
    """The native ``srmech_toml`` parser self-hosts every (float-free) fixture: each
    C parse equals the stdlib oracle, and NONE decline. This is what makes the three
    loaders take the native path in a wheel install."""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), (
        "native library is loaded but exposes no srmech_toml_parse — a stale / "
        "pre-rc391 build")
    declined = []
    for name, text in sorted(_ALL_FIXTURES.items()):
        got_c = _native.toml_loads_c(text)
        if got_c is None:
            declined.append(name)
            continue
        assert got_c == _stdlib_toml.loads(text), (
            f"C-vs-tomllib dict mismatch for fixture {name!r}")
    assert declined == [], (
        f"fixture(s) unexpectedly DECLINED by the C parser: {declined}. The rc394 "
        f"fixtures are float-free; a decline means an unsupported construct crept in.")
