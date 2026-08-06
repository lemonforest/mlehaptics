"""rc400 — the DUPLICATE native-TOML path (dsl/_toml_chain) collapses onto
srmech._toml (#T1067, the last tail of the #T907 TOML self-host arc).

Before rc400 THREE loaders hand-rolled a native-first-then-tomllib dance by
borrowing the DSL chain's private native front-end `_toml_loads_native` (which
fronts the DISTINCT C symbol `srmech_dsl_toml_chain_to_json`) plus a local
`import tomllib` floor:

* srmech.dsl._toml_chain.build_chain_from_toml_str / load_chain_toml
* srmech.dsl._alias.build_aliases_from_toml_str
* srmech.biology.genome.load_type_aliases_toml

rc400 repoints all three onto srmech._toml (the ONE canonical native-first TOML
loader — native `srmech_toml_parse` direct-tree-walk, tomllib/tomli floor),
deletes `_toml_loads_native`, and drops the `import tomllib` alias from
_toml_chain.py. After rc400 the tree has exactly ONE native-first TOML
implementation and exactly ONE parse-floor `import tomllib` (in srmech/_toml.py).

The `srmech_dsl_toml_chain_to_json` C symbol is UNCHANGED (ABI stays 11) — it
remains the C-only-host chain-spec TOML->canonical-JSON front-end; its parity
coverage moved into test_dsl_combinators_c_rc182.py's own direct C probe.

Parity contract proved here: the repointed surfaces parse byte-identical dicts to
srmech._toml.loads AND to the stdlib tomllib oracle, over the real shipped
descriptor corpus, on BOTH the native path (require_native) and a forced-pure
path. numpy-free by construction (stdlib tomllib / pathlib only).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

from srmech import _native
from srmech import _toml as srmech_toml_frontdoor
from srmech.dsl import _toml_chain
from tests._native_gate import require_native

if sys.version_info >= (3, 11):
    import tomllib as _stdlib_toml
else:  # pragma: no cover — 3.10 back-port
    import tomli as _stdlib_toml  # type: ignore[no-redef]


_CATALOGS = Path(_toml_chain.__file__).resolve().parent.parent / "cascade" / "catalogs"
_CASCADE_DIR = _CATALOGS / "cascade_catalog"
_ALIAS_DIR = _CATALOGS / "alias_catalog"


def _read(p: Path) -> str:
    """Byte-identical input for every parser: raw bytes, UTF-8, no newline xlate."""
    return p.read_bytes().decode("utf-8")


def _corpus() -> list[Path]:
    paths = sorted(_CASCADE_DIR.glob("*.toml")) + sorted(_ALIAS_DIR.glob("*.toml"))
    assert paths, "no descriptors found — the parity comparison would be vacuous"
    return paths


class _force_pure:
    """Disable the native lib so srmech._toml.loads takes the tomllib floor."""

    def __enter__(self):
        self._saved = _native.HAS_NATIVE
        _native.HAS_NATIVE = False
        return self

    def __exit__(self, *exc):
        _native.HAS_NATIVE = self._saved
        return False


# ── the repoint itself, pinned so it cannot silently revert ──────────────────

def test_toml_chain_routes_through_srmech_internal_front_door() -> None:
    """_toml_chain now references srmech._toml (the internal front door), and the
    stale module-top `import tomllib as _toml` alias + the duplicate
    `_toml_loads_native` native-first probe are GONE. A revert to either would
    re-bind `_toml` / `_toml_loads_native` here and unbind `_srmech_toml`."""
    assert _toml_chain._srmech_toml is srmech_toml_frontdoor, (
        "srmech.dsl._toml_chain no longer routes its parse through srmech._toml")
    assert not hasattr(_toml_chain, "_toml"), (
        "_toml_chain still binds a module-top `_toml` (the stale stdlib guard)")
    assert not hasattr(_toml_chain, "_toml_loads_native"), (
        "_toml_chain still exposes `_toml_loads_native` (the duplicate native-first "
        "TOML implementation rc400 collapsed onto srmech._toml)")


def _stdlib_toml_parse_floor_offenders(pkg_root: Path) -> list[str]:
    """Every srmech/ module (except srmech/_toml.py) that actually CALLS a
    stdlib-tomllib-bound name's ``.loads`` / ``.load`` — i.e. a duplicate parse
    floor. Uses AST so it is precise about two legitimate NON-floors that a naive
    text grep would false-positive:

    * an EXCEPTION-TYPE reference (``except tomllib.TOMLDecodeError``) — a
      module importing the stdlib solely to NAME a type, not to parse. Not a
      floor. Through rc406 ``amsc/descriptor.py`` and ``profile_loader.py`` were
      the live examples; rc407 (`#T1076`) drained BOTH, because
      ``srmech._toml`` now re-exports ``TOMLDecodeError`` itself and a front
      door that does not name the error it raises forces its callers into the
      banned import. The carve-out stays — it is the correct rule, and the next
      such module must not be miscounted as a floor — but it currently matches
      NOTHING, which is the intended end state.
    * ``import tomli as tomllib`` sitting inside a STRING literal (the
      ``_tool_docs`` curated worked-example prose) — not a real Import node.
    """
    offenders: list[str] = []
    for p in sorted(pkg_root.rglob("*.py")):
        rel = p.relative_to(pkg_root).as_posix()
        if rel == "_toml.py":
            continue  # THE one canonical native-first loader + its tomllib floor
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover
            continue
        toml_names = {
            (alias.asname or alias.name)
            for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names if alias.name in ("tomllib", "tomli")
        }
        if not toml_names:
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("loads", "load")
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in toml_names):
                offenders.append(
                    f"{rel}:{node.lineno}: {node.func.value.id}.{node.func.attr}(...)")
    return offenders


def test_exactly_one_native_first_toml_parse_floor() -> None:
    """The whole srmech/ real source PARSES TOML via the stdlib floor in exactly ONE
    place — srmech/_toml.py. Any other module that calls ``tomllib.loads`` /
    ``tomllib.load`` directly (a second native-first-or-not TOML implementation) is a
    regression. Exception-type references (``except tomllib.TOMLDecodeError``) and
    ``_tool_docs`` string-literal prose are correctly NOT flagged (see helper)."""
    pkg = Path(srmech_toml_frontdoor.__file__).resolve().parent
    offenders = _stdlib_toml_parse_floor_offenders(pkg)
    assert not offenders, (
        "a duplicate stdlib-TOML PARSE FLOOR lingers outside srmech/_toml.py — a "
        "module calling tomllib.loads/.load directly instead of srmech._toml:\n"
        + "\n".join(offenders))


# ── deduped surfaces == srmech._toml.loads == tomllib, native + pure ─────────

def _assert_corpus_parity() -> None:
    for p in _corpus():
        text = _read(p)
        oracle = _stdlib_toml.loads(text)
        # (a) the deduped file surface
        assert _toml_chain.load_chain_toml(p) == oracle, (
            f"load_chain_toml diverged from tomllib for {p.name}")
        # (b) the deduped in-memory surface — build a Chain from a chain-spec is
        # tested elsewhere; here we prove the PARSE step (front door) matches.
        assert srmech_toml_frontdoor.loads(text) == oracle, (
            f"srmech._toml.loads diverged from tomllib for {p.name}")


def test_corpus_parity_pure() -> None:
    """Forced-pure: the deduped surfaces == tomllib for every shipped descriptor
    (exercises the stdlib floor deterministically, native present or not)."""
    with _force_pure():
        _assert_corpus_parity()


def test_corpus_parity_native() -> None:
    """Native: the deduped surfaces == tomllib for every shipped descriptor
    (exercises the C srmech_toml direct-tree-walk marshalling)."""
    require_native("srmech_toml_parse")
    _assert_corpus_parity()


# ── consumer-level parity (genome / alias loaders) ───────────────────────────

def test_alias_loader_key_set_matches_frontdoor() -> None:
    """build_aliases_from_toml_str's {name: callable} keys == the `[[alias]]`
    entry names in srmech._toml.loads of the same doc — the alias loader now
    parses via the canonical front door."""
    from srmech.dsl._alias import build_aliases_from_toml_str
    spec = _read(_ALIAS_DIR / "music_domain_aliases.toml")
    names = set(build_aliases_from_toml_str(spec))
    expected = {e["name"] for e in srmech_toml_frontdoor.loads(spec).get("alias", [])}
    assert names == expected and names, (
        f"alias key-set diverged: loader={sorted(names)} frontdoor={sorted(expected)}")


def test_genome_type_aliases_loader_matches_frontdoor() -> None:
    """genome.load_type_aliases_toml applies the `[genome.type_aliases]` section
    exactly as srmech._toml.loads parses it — the genome loader now parses via the
    canonical front door."""
    from srmech.biology import genome
    path = _ALIAS_DIR / "genome_type_aliases_legacy.toml"
    parsed = srmech_toml_frontdoor.loads(_read(path))
    section = parsed.get("genome", {}).get("type_aliases") or parsed.get("type_aliases", {})
    assert section, "fixture carries no [genome.type_aliases] — comparison vacuous"
    try:
        genome.load_type_aliases_toml(path)
        applied = {v for v in section.values()}
        active = {genome._alias_type_value(k) for k in section}
        assert applied == active, (
            f"genome type-alias apply diverged from the front-door parse: "
            f"applied={sorted(applied)} active={sorted(active)}")
    finally:
        genome.set_type_aliases({})  # reset global alias state
