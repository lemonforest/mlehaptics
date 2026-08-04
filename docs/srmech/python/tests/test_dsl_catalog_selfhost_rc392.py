"""rc392 / `#T907` slice 2 — the DSL cascade + class catalog loaders now
self-host on srmech's own internal TOML front door.

rc391 landed ``srmech._toml.loads`` (native ``srmech_toml`` parser first, stdlib
``tomllib`` / ``tomli`` floor) and proved corpus-wide parity with the stdlib.
This slice REPOINTS the two lowest-risk consumers — ``srmech.dsl._catalog``'s
``load_catalog`` (the ~20 ``[cascade]`` descriptors) and
``srmech.dsl._class_catalog``'s ``load_class_catalog`` (the 4 ``[class]``
descriptors) — off the module-top ``tomllib`` guard onto that loader.

What this file certifies, distinct from the rc391 oracle (which pinned
``_toml.loads == tomllib`` on the raw corpus):

* **Registry identity through the REPOINTED loaders.** ``load_catalog()`` /
  ``load_class_catalog()`` produce a registry byte-identical (modulo the two
  synthetic ``_provenance`` / ``_source`` keys the loaders add) to a DIRECT
  ``tomllib`` parse of the same descriptor files — i.e. routing the parse through
  ``srmech._toml`` changed nothing observable about the built-in catalogs.
* **The C parser self-hosts the ENTIRE catalog corpus** (native-guarded via
  ``require_native`` — the `#T843` / `#T1004` contract). As of rc397 (`#T1066`)
  the C decimal→double parse is correctly-rounded, so ``best_rational_signed.toml``
  (``dead_band = 1e-12``) self-hosts too — the float boundary that used to force
  it to tomllib is closed. Every cascade descriptor and all four class
  descriptors self-host on ``srmech_toml`` and equal the stdlib parse.
* **A malformed descriptor still raises the same error type as before** —
  ``tomllib.TOMLDecodeError`` — through the repointed loaders (the C path
  DECLINES a syntactically broken doc and rides the stdlib parse, which raises).

numpy-free by construction (stdlib ``tomllib`` / ``pathlib`` only).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import srmech
from srmech import _native
from srmech import _toml as srmech_toml_frontdoor
from srmech.dsl import _catalog, _class_catalog
from tests._native_gate import require_native

if sys.version_info >= (3, 11):
    import tomllib as _stdlib_toml
else:  # pragma: no cover — 3.10 back-port
    import tomli as _stdlib_toml  # type: ignore[no-redef]


#: The two keys the loaders synthesise onto each parsed descriptor; a raw
#: ``tomllib`` parse carries neither, so they are stripped before comparison.
_SYNTHETIC = ("_provenance", "_source")

#: The one cascade descriptor that carries a float (``best_rational_signed.toml``,
#: ``dead_band = 1e-12``). It USED to decline to tomllib (the old libm-free
#: accumulator was 1 ULP off); rc397 (`#T1066`) made the C float parse
#: correctly-rounded, so it now self-hosts like every other descriptor.
_FLOAT_BEARING_CASCADE = "best_rational_signed.toml"


def _read(path: Path) -> str:
    """Read a descriptor exactly as the shipped loaders do — raw bytes, UTF-8
    decode, NO newline translation — so every parser sees byte-identical input."""
    return path.read_bytes().decode("utf-8")


def _strip(desc: dict) -> dict:
    return {k: v for k, v in desc.items() if k not in _SYNTHETIC}


def _expected_cascade() -> dict:
    """The cascade registry built the loader's way but via a DIRECT ``tomllib``
    parse — keyed by ``[cascade].name``."""
    out = {}
    for p in sorted(_catalog.CATALOG_DIR.glob("*.toml")):
        doc = _stdlib_toml.loads(_read(p))
        out[doc["cascade"]["name"]] = doc
    return out


def _expected_class() -> dict:
    out = {}
    for p in sorted(_class_catalog.CLASS_CATALOG_DIR.glob("*.toml")):
        doc = _stdlib_toml.loads(_read(p))
        out[doc["class"]["name"]] = doc
    return out


# ── the repoint itself, pinned so it cannot silently revert ──────────────────

def test_loaders_use_srmech_internal_toml_front_door() -> None:
    """Both loaders now reference ``srmech._toml`` (the internal front door), and
    the stale module-top ``tomllib`` / ``tomli`` alias is GONE. A revert to the
    stdlib guard would re-bind ``_toml`` here and unbind ``srmech_toml``."""
    assert _catalog.srmech_toml is srmech_toml_frontdoor, (
        "srmech.dsl._catalog no longer routes its parse through srmech._toml")
    assert _class_catalog.srmech_toml is srmech_toml_frontdoor, (
        "srmech.dsl._class_catalog no longer routes its parse through srmech._toml")
    # the old stdlib-guard alias must not linger under either module.
    assert not hasattr(_catalog, "_toml"), (
        "_catalog still binds a module-top `_toml` (the stale stdlib guard)")
    assert not hasattr(_class_catalog, "_toml"), (
        "_class_catalog still binds a module-top `_toml` (the stale stdlib guard)")


# ── registry identity through the repointed loaders ──────────────────────────

def test_cascade_catalog_self_hosts_to_the_same_registry() -> None:
    """``load_catalog()`` (now via ``srmech._toml``) == a direct ``tomllib`` parse
    of the built-in ``[cascade]`` descriptors, descriptor-for-descriptor."""
    expected = _expected_cascade()
    assert expected, "no cascade descriptors found — the comparison would be vacuous"
    _catalog.load_catalog.cache_clear()
    try:
        got = _catalog.load_catalog()
    finally:
        _catalog.load_catalog.cache_clear()
    # restrict to the SHIPPED descriptors (an env-registered user dir would add
    # more; this slice's claim is about the built-in catalog).
    got_shipped = {
        name: desc for name, desc in got.items()
        if Path(desc["_source"]).resolve().parent == _catalog.CATALOG_DIR.resolve()
    }
    assert set(got_shipped) == set(expected), (
        f"shipped cascade op-name set diverged from a direct tomllib parse: "
        f"loader-only={sorted(set(got_shipped) - set(expected))}, "
        f"tomllib-only={sorted(set(expected) - set(got_shipped))}")
    for name in expected:
        assert _strip(got_shipped[name]) == expected[name], (
            f"cascade descriptor {name!r} parsed DIFFERENTLY through the repointed "
            f"loader than through a direct tomllib parse")


def test_class_catalog_self_hosts_to_the_same_registry() -> None:
    """``load_class_catalog()`` (now via ``srmech._toml``) == a direct ``tomllib``
    parse of the built-in ``[class]`` descriptors, descriptor-for-descriptor."""
    expected = _expected_class()
    assert expected, "no class descriptors found — the comparison would be vacuous"
    _class_catalog.load_class_catalog.cache_clear()
    try:
        got = _class_catalog.load_class_catalog()
    finally:
        _class_catalog.load_class_catalog.cache_clear()
    got_shipped = {
        name: desc for name, desc in got.items()
        if Path(desc["_source"]).resolve().parent
        == _class_catalog.CLASS_CATALOG_DIR.resolve()
    }
    assert set(got_shipped) == set(expected), (
        f"shipped class-name set diverged from a direct tomllib parse: "
        f"loader-only={sorted(set(got_shipped) - set(expected))}, "
        f"tomllib-only={sorted(set(expected) - set(got_shipped))}")
    for name in expected:
        assert _strip(got_shipped[name]) == expected[name], (
            f"class descriptor {name!r} parsed DIFFERENTLY through the repointed "
            f"loader than through a direct tomllib parse")


# ── the C parser actually self-hosts the catalog corpus (native-guarded) ─────

def test_c_path_self_hosts_the_cascade_catalog() -> None:
    """The native ``srmech_toml`` parser self-hosts EVERY cascade descriptor,
    including the float-bearing ``best_rational_signed.toml`` — since rc397
    (`#T1066`) the C float parse is correctly-rounded, so nothing declines. Each
    self-hosted parse equals the stdlib oracle."""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), (
        "native library is loaded but exposes no srmech_toml_parse — a stale / "
        "pre-rc391 build")
    self_hosted, declined = [], []
    for p in sorted(_catalog.CATALOG_DIR.glob("*.toml")):
        text = _read(p)
        got_c = _native.toml_loads_c(text)
        if got_c is None:
            declined.append(p.name)
        else:
            self_hosted.append(p.name)
            assert got_c == _stdlib_toml.loads(text), (
                f"C-vs-tomllib dict mismatch for cascade descriptor {p.name}")
    assert declined == [], (
        f"cascade descriptor(s) DECLINED by the C parser — since rc397 the whole "
        f"catalog self-hosts (floats included): {declined}")
    assert _FLOAT_BEARING_CASCADE in self_hosted, (
        f"the float-bearing {_FLOAT_BEARING_CASCADE!r} must now self-host on the "
        f"correctly-rounded C float parse, not decline to tomllib")


def test_c_path_self_hosts_the_class_catalog() -> None:
    """Every ``[class]`` descriptor self-hosts on ``srmech_toml`` (none carries a
    float) and equals the stdlib oracle."""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), "stale lib: no srmech_toml_parse"
    declined = []
    for p in sorted(_class_catalog.CLASS_CATALOG_DIR.glob("*.toml")):
        text = _read(p)
        got_c = _native.toml_loads_c(text)
        if got_c is None:
            declined.append(p.name)
        else:
            assert got_c == _stdlib_toml.loads(text), (
                f"C-vs-tomllib dict mismatch for class descriptor {p.name}")
    assert declined == [], (
        f"class descriptor(s) unexpectedly declined by the C parser: {declined}")


# ── error-type continuity: a malformed descriptor still raises the same type ──

def _malformed_toml() -> str:
    """A syntactically invalid TOML doc (empty key). The C parser DECLINES it
    (SRMECH_ERR_BAD_INPUT → None) and the stdlib floor raises — exactly the path
    a malformed shipped descriptor would have taken before the repoint too."""
    return "= 1\n"


def test_malformed_toml_raises_tomldecodeerror_at_the_front_door() -> None:
    """srmech._toml.loads surfaces tomllib's TOMLDecodeError on a broken doc —
    native-first with the stdlib as the correctness floor, so the exception type
    the repointed loaders can propagate is unchanged."""
    with pytest.raises(_stdlib_toml.TOMLDecodeError):
        srmech_toml_frontdoor.loads(_malformed_toml())


def test_malformed_cascade_descriptor_still_raises_tomldecodeerror(
        tmp_path: Path) -> None:
    """End-to-end through the repointed ``load_catalog``: a malformed descriptor
    in a registered user dir raises the SAME ``TOMLDecodeError`` it raised before
    the repoint."""
    (tmp_path / "broken.toml").write_text(_malformed_toml(), encoding="utf-8")
    saved = list(_catalog._USER_CATALOG_DIRS)
    try:
        _catalog.register_catalog_dir(tmp_path)
        with pytest.raises(_stdlib_toml.TOMLDecodeError):
            _catalog.load_catalog()
    finally:
        _catalog._USER_CATALOG_DIRS[:] = saved
        _catalog.load_catalog.cache_clear()


def test_malformed_class_descriptor_still_raises_tomldecodeerror(
        tmp_path: Path) -> None:
    """The same continuity for ``load_class_catalog``."""
    (tmp_path / "broken.toml").write_text(_malformed_toml(), encoding="utf-8")
    saved = list(_class_catalog._USER_CLASS_DIRS)
    try:
        _class_catalog.register_class_dir(tmp_path)
        with pytest.raises(_stdlib_toml.TOMLDecodeError):
            _class_catalog.load_class_catalog()
    finally:
        _class_catalog._USER_CLASS_DIRS[:] = saved
        _class_catalog.load_class_catalog.cache_clear()
