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
* **The C parser self-hosts every FLOAT-FREE descriptor, and declines exactly
  the float-bearing ones** (native-guarded via ``require_native`` — the `#T843`
  / `#T1004` contract). rc397 (`#T1066`) made the C decimal→double parse
  correctly-rounded and closed the PRECISION decline; that is unchanged and not
  retracted. rc479 (`#T1188`) opened a different one: under contract A the front
  door reads a decimal literal as the exact rational it names, and no C value
  layer in this library can hold a rational, so a float-bearing document is
  DECLINED to the exact Python floor rather than answered in ``double``. It is a
  CARRIER decline, and it is what keeps a native cell and a pure cell returning
  the same object. All four class descriptors carry no float and self-host.
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
from srmech.math.q import Q as _Q            # rc479 (`#T1188`): contract A
from srmech.math.q import parse_float_exact  # rc479 (`#T1188`): contract A
from tests._native_gate import require_native

if sys.version_info >= (3, 11):
    import tomllib as _stdlib_toml
else:  # pragma: no cover — 3.10 back-port
    import tomli as _stdlib_toml  # type: ignore[no-redef]


#: The two keys the loaders synthesise onto each parsed descriptor; a raw
#: ``tomllib`` parse carries neither, so they are stripped before comparison.
_SYNTHETIC = ("_provenance", "_source")

#: A cascade descriptor that carries a float (``best_rational_signed.toml``,
#: ``dead_band = 1e-12``). Its history is two DIFFERENT declines: it declined
#: pre-rc397 on PRECISION (the old libm-free accumulator was 1 ULP off), rc397
#: (`#T1066`) closed that, and rc479 (`#T1188`) opens a CARRIER one — contract A
#: reads that literal as an exact rational and a C ``double`` cannot carry it.
#: It is named here as a WITNESS, not as the population: the float-bearing set
#: below is derived from the documents.
_FLOAT_BEARING_CASCADE = "best_rational_signed.toml"


def _read(path: Path) -> str:
    """Read a descriptor exactly as the shipped loaders do — raw bytes, UTF-8
    decode, NO newline translation — so every parser sees byte-identical input."""
    return path.read_bytes().decode("utf-8")


def _strip(desc: dict) -> dict:
    return {k: v for k, v in desc.items() if k not in _SYNTHETIC}


def _oracle(text: str) -> dict:
    """The stdlib parse under the SAME reader the front door installs.

    ⚠️ rc479 (`#T1188`): the self-hosting contract is HOOK-RELATIVE. Contract A
    makes ``srmech._toml.loads`` read a decimal literal as the exact rational it
    names, so a BARE ``tomllib`` oracle would be comparing a hook against no
    hook — measuring contract A rather than the self-host. The property this
    module was always about is *the front door equals the backend GIVEN THE
    SAME READER*, and that is what is compared now. Restated, not weakened:
    the equality is still descriptor-for-descriptor and still byte-typed.
    """
    return _stdlib_toml.loads(text, parse_float=parse_float_exact)


def _expected_cascade() -> dict:
    """The cascade registry built the loader's way but via a DIRECT stdlib
    parse under the same reader — keyed by ``[cascade].name``."""
    out = {}
    for p in sorted(_catalog.CATALOG_DIR.glob("*.toml")):
        doc = _oracle(_read(p))
        out[doc["cascade"]["name"]] = doc
    return out


def _expected_class() -> dict:
    out = {}
    for p in sorted(_class_catalog.CLASS_CATALOG_DIR.glob("*.toml")):
        doc = _oracle(_read(p))
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

def _deep_equal(a, b) -> bool:
    """Byte-identical-parse equality (rc420, `#T1114`): the cascade
    descriptors now carry TOML 1.0 special floats (the documented NaN /
    inf proof-case boundary inputs), and dict ``==`` can NEVER equate a
    NaN-bearing parse with its oracle even when both parsers agree
    bit-for-bit. Floats compare by their 8 BYTES (NaN == same-bits NaN;
    ``-0.0`` distinct from ``0.0`` — stricter than ``==``). Twin of the
    helpers in test_toml_selfhost_parity_rc391.py /
    test_toml_dedup_parity_rc400.py."""
    if isinstance(a, float) or isinstance(b, float):
        import struct
        return (isinstance(a, float) and isinstance(b, float)
                and struct.pack("<d", a) == struct.pack("<d", b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(
            _deep_equal(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


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
        assert _deep_equal(_strip(got_shipped[name]), expected[name]), (
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

def _carries_a_float(text: str) -> bool:
    """Does this document contain a TOML float? Asked of the stdlib LEXER via
    its ``parse_float`` hook rather than answered from a hand-written list,
    which would go stale the first time a descriptor gained or lost a literal
    and would take the partition below down with it."""
    seen: list[str] = []

    def _note(tok: str) -> float:
        seen.append(tok)
        return 0.0

    _stdlib_toml.loads(text, parse_float=_note)
    return bool(seen)


def test_c_path_self_hosts_the_cascade_catalog() -> None:
    """The native ``srmech_toml`` parser self-hosts every FLOAT-FREE cascade
    descriptor and DECLINES every float-bearing one — a partition, with the
    float set derived from the documents.

    ⚠️ **rc479 (`#T1188`) inverted the float half of this claim, and the
    reason is not the one rc397 removed.** Through rc478 this asserted
    ``declined == []`` on rc397's ground: the C decimal→double parse became
    correctly-rounded, so a float value was bit-identical to ``tomllib``'s and
    the PRECISION decline went away. **That is still true and is not
    retracted.** What changed is the CONTRACT. Under contract A the front door
    returns the exact rational a decimal literal names, and no C value layer in
    this library can hold a rational (``dv_value_t`` and ``srmech_mval_t`` are
    both ``double``), so the binding declines a float-bearing document and the
    exact Python floor answers it. It is a CARRIER decline where rc397's was a
    precision one, and it is what keeps a native cell and a pure cell returning
    the same object rather than a ``double`` in one and a ``Q`` in the other.

    The restated property is strictly STRONGER than ``declined == []`` was: it
    pins BOTH directions. A float-free descriptor that declines is a real
    regression in the C parser — rc397's ground, still guarded. A float-bearing
    one that self-hosts means the carrier decline stopped firing and a native
    cell is serving doubles where a pure cell serves exact rationals, which is
    the silent half and the reason this is not written as a skip.
    """
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
            assert _deep_equal(got_c, _stdlib_toml.loads(text)), (
                f"C-vs-tomllib dict mismatch for cascade descriptor {p.name}")

    float_bearing = sorted(
        p.name for p in sorted(_catalog.CATALOG_DIR.glob("*.toml"))
        if _carries_a_float(_read(p)))
    assert float_bearing, (
        "no cascade descriptor carries a float at all — the partition below "
        "would be vacuous and would certify nothing")
    assert self_hosted, (
        "the C parser self-hosted NOTHING — rc397's correctly-rounded parse is "
        "not the thing that regressed here; the parser is")
    assert sorted(declined) == float_bearing, (
        f"the C parser's declines are no longer EXACTLY the float-bearing "
        f"documents. declined={sorted(declined)} float-bearing={float_bearing}. "
        f"A float-FREE document among the declines is a C-parser regression; a "
        f"float-bearing one among the self-hosted means the contract-A carrier "
        f"decline stopped firing, and a native cell is then serving doubles "
        f"where a pure cell serves exact rationals — same call, same input, "
        f"different type, no error.")
    assert _FLOAT_BEARING_CASCADE in declined, (
        f"the float-bearing {_FLOAT_BEARING_CASCADE!r} must DECLINE under "
        f"contract A — a CARRIER decline, not rc397's precision one — so the "
        f"exact floor answers it")

    # and the FLOOR does answer it exactly: the decline costs a parse, never a
    # value. Typed, not just equal — a ``float`` here would mean the decline
    # reached a reader that still rounds.
    doc = srmech_toml_frontdoor.loads(
        _read(_catalog.CATALOG_DIR / _FLOAT_BEARING_CASCADE))
    leaves: list[object] = []

    def _walk(v: object) -> None:
        if isinstance(v, dict):
            for x in v.values():
                _walk(x)
        elif isinstance(v, list):
            for x in v:
                _walk(x)
        else:
            leaves.append(v)

    _walk(doc)
    exact = [v for v in leaves if isinstance(v, _Q)]
    assert exact, (
        f"the front door returned no exact leaf for {_FLOAT_BEARING_CASCADE!r} "
        f"— the C decline did not reach the exact floor")
    # Every float leaf that REMAINS must be a Z1 one — a non-finite or a signed
    # zero, which contract A deliberately leaves as ``float`` because no
    # rational names them. This descriptor carries both (`nan` and `-0.0`, the
    # documented proof-case boundary inputs), so the clause is not vacuous; a
    # FINITE NON-ZERO float leaf would mean contract A read part of the
    # document and rounded the rest. Decided by integer arithmetic on the
    # IEEE bytes, never by an inequality against a tolerance.
    import struct as _struct
    residue = [v for v in leaves if isinstance(v, float)]
    assert residue, (
        f"{_FLOAT_BEARING_CASCADE!r} no longer carries a Z1 float leaf, so the "
        f"clause below certifies nothing — restate it against a descriptor "
        f"that does")
    bad = []
    for v in residue:
        bits = int.from_bytes(_struct.pack("<d", v), "little")
        expo = (bits >> 52) & 0x7FF
        mant = bits & ((1 << 52) - 1)
        finite = expo != 0x7FF
        zero = expo == 0 and mant == 0
        if finite and not zero:
            bad.append(v)
    assert not bad, (
        f"the front door returned a FINITE NON-ZERO float leaf for "
        f"{_FLOAT_BEARING_CASCADE!r} alongside the exact ones ({bad}) — "
        f"contract A read part of the document and rounded the rest")


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
