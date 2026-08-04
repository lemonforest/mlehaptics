"""rc393 / `#T907` slice 3 — the AMSC descriptor + catalog loaders now self-host
on srmech's own internal TOML front door, and the attestation hash is invariant.

rc391 landed ``srmech._toml.loads`` (native ``srmech_toml`` parser first, stdlib
``tomllib`` / ``tomli`` floor) and proved corpus-wide parity with the stdlib.
rc392 repointed the two DSL catalog loaders. This slice — the attestation-critical
one — repoints the two AMSC loaders:

* ``srmech.amsc.descriptor.load_descriptor`` (the ``[source]/[fetch]/[parse]/…``
  descriptor read) AND ``srmech.amsc.descriptor.descriptor_hash`` (the
  ``json.dumps(sort_keys=True)`` canonical-serialised SHA that populates every
  attestation's ``collector_descriptor_hash``).
* ``srmech.amsc.catalog._catalog_toml_dict`` (which feeds
  ``parse_catalog_chains`` over the ``[[catalog.operator_chain]]`` bridge).

THE LOAD-BEARING INVARIANT this file certifies:

  **Every attested descriptor's ``descriptor_hash`` is byte-identical before and
  after the repoint.** A changed hash would break attestation integrity — the
  whole MPM point. It holds because ``srmech._toml.loads`` produces a dict equal
  to ``tomllib.loads`` (rc391's corpus oracle), so the SAME
  ``json.dumps(parsed, sort_keys=True, ensure_ascii=False)`` canonicalisation
  hashes to the SAME SHA. The pre-repoint code path was exactly
  ``sha256_bytes(json.dumps(tomllib.loads(raw), sort_keys=True,
  ensure_ascii=False).encode())`` — reproduced here as the oracle — so proving
  ``descriptor_hash(path) == oracle`` for the whole attested corpus IS the
  before/after equality proof.

Self-host vs decline: the shipped attested corpus is FLOAT-FREE, so the C parser
self-hosts EVERY attested descriptor and the decline-set is EMPTY (a
float-bearing descriptor would DECLINE to the bit-exact stdlib parse, `#T1066`;
the hash would still be invariant because the decline rides tomllib on BOTH the
old and new paths). The C-path assertions are native-guarded via
``require_native`` (the `#T843` contract); the hash-invariant + dict-parity
assertions are UNIVERSAL (they hold on the pure shard too, where both sides use
tomllib).

numpy-free by construction (stdlib ``tomllib`` / ``pathlib`` / ``json`` only).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import srmech
from srmech import _native
from srmech import _toml as srmech_toml_frontdoor
from srmech.amsc import catalog as _catalog_mod
from srmech.amsc import descriptor as _descriptor_mod
from srmech.amsc.descriptor import descriptor_hash, load_descriptor
from srmech.amsc.format import sha256_bytes
from tests._native_gate import require_native

if sys.version_info >= (3, 11):
    import tomllib as _stdlib_toml
else:  # pragma: no cover — 3.10 back-port
    import tomli as _stdlib_toml  # type: ignore[no-redef]


#: srmech's own attested root — the shipped descriptor corpus this slice is about.
_ATTESTED_ROOT = Path(_descriptor_mod.__file__).resolve().parent / "attested"


def _attested_descriptor_paths() -> list[Path]:
    """Every shipped ``<source>/descriptor.toml`` under srmech's attested root."""
    return sorted(_ATTESTED_ROOT.glob("*/descriptor.toml"))


def _read(path: Path) -> str:
    """Read a descriptor exactly as the shipped loaders do — raw bytes, UTF-8
    decode, NO newline translation — so every parser sees byte-identical input."""
    return path.read_bytes().decode("utf-8")


def _tomllib_oracle_hash(path: Path) -> str:
    """Reproduce the PRE-repoint ``descriptor_hash`` path exactly: a direct
    ``tomllib`` parse, the identical ``json.dumps(sort_keys=True,
    ensure_ascii=False)`` canonicalisation, then ``sha256_bytes``. This is the
    rc392 (before) value for a corpus whose ``descriptor.toml`` files this rc did
    not touch."""
    parsed = _stdlib_toml.loads(_read(path))
    canonical = json.dumps(
        parsed, sort_keys=True, ensure_ascii=False
    ).encode("utf-8")
    return sha256_bytes(canonical)


def test_attested_corpus_is_nonempty() -> None:
    """Guard against a vacuous suite: the attested root must hold descriptors."""
    paths = _attested_descriptor_paths()
    assert paths, f"no attested descriptors found under {_ATTESTED_ROOT}"


# ── the repoint itself, pinned so it cannot silently revert ──────────────────

def test_amsc_loaders_use_srmech_internal_toml_front_door() -> None:
    """Both AMSC modules now reference ``srmech._toml`` (the internal front door),
    bound under the underscore alias ``_srmech_toml`` (kept out of gen_c_claims'
    ``srmech_*`` bytecode scan; see the import comment in each module). A revert to
    a stdlib-only parse would unbind ``_srmech_toml`` here."""
    assert _descriptor_mod._srmech_toml is srmech_toml_frontdoor, (
        "srmech.amsc.descriptor no longer routes its parse through srmech._toml")
    assert _catalog_mod._srmech_toml is srmech_toml_frontdoor, (
        "srmech.amsc.catalog no longer routes its parse through srmech._toml")
    # descriptor.py DELIBERATELY retains its ``tomllib`` alias — the
    # ``except tomllib.TOMLDecodeError`` clause needs the exception type. Its
    # removal would break the error contract, so pin that it stays.
    assert hasattr(_descriptor_mod, "tomllib"), (
        "descriptor.py dropped its tomllib alias; the except TOMLDecodeError "
        "clause needs it — the error contract would break")


# ── THE load-bearing invariant: descriptor_hash byte-identical before/after ──

def test_descriptor_hash_byte_identical_before_and_after_repoint() -> None:
    """For EVERY attested descriptor, the repointed ``descriptor_hash`` equals the
    pre-repoint ``tomllib``-oracle hash — the attestation ``collector_descriptor_hash``
    is invariant to which parser ran. UNIVERSAL: holds on the pure shard (both
    sides tomllib) and on the native shard (C-parse vs tomllib-parse)."""
    paths = _attested_descriptor_paths()
    assert paths, "vacuous — no attested descriptors"
    mismatches = []
    for path in paths:
        after = descriptor_hash(path)
        oracle = _tomllib_oracle_hash(path)
        if after != oracle:
            mismatches.append((path.parent.name, after, oracle))
    assert not mismatches, (
        "descriptor_hash changed across the repoint for: "
        + ", ".join(
            f"{name} (after={a[:12]}… oracle={o[:12]}…)"
            for name, a, o in mismatches
        )
        + " — this BREAKS attestation integrity (collector_descriptor_hash)"
    )


# ── load_descriptor parses to the same section dicts as a direct tomllib parse ─

def test_load_descriptor_sections_identical_to_tomllib() -> None:
    """``load_descriptor`` (now via ``srmech._toml``) yields section dicts equal to
    a direct ``tomllib`` parse of the same file — the repoint changed nothing
    observable about the parsed descriptor."""
    for path in _attested_descriptor_paths():
        oracle = _stdlib_toml.loads(_read(path))
        d = load_descriptor(path)
        assert d.source == oracle["source"], f"{path.parent.name}: [source] diverged"
        assert d.fetch == oracle["fetch"], f"{path.parent.name}: [fetch] diverged"
        assert d.parse == oracle["parse"], f"{path.parent.name}: [parse] diverged"
        assert d.schema == oracle["schema"], f"{path.parent.name}: [schema] diverged"
        assert d.rendering == oracle["rendering"], (
            f"{path.parent.name}: [rendering] diverged")
        assert d.attestation == oracle["attestation"], (
            f"{path.parent.name}: [attestation] diverged")
        assert d.gap_targeting == dict(oracle.get("gap_targeting", {})), (
            f"{path.parent.name}: [gap_targeting] diverged")


# ── _catalog_toml_dict parses to the same full dict as a direct tomllib parse ─

def test_catalog_toml_dict_identical_to_tomllib() -> None:
    """``_catalog_toml_dict`` (the ``[[catalog.operator_chain]]`` bridge feed, now
    via ``srmech._toml``) returns the full parsed dict equal to a direct
    ``tomllib`` parse for every registered source."""
    descriptors = _catalog_mod._descriptors()
    assert descriptors, "no registered descriptors — comparison would be vacuous"
    for key, desc in descriptors.items():
        _d, toml_dict = _catalog_mod._catalog_toml_dict(key)
        oracle = _stdlib_toml.loads(desc.path.read_bytes().decode("utf-8"))
        assert toml_dict == oracle, (
            f"_catalog_toml_dict({key!r}) parsed DIFFERENTLY through the repointed "
            f"loader than a direct tomllib parse")


# ── the C parser actually self-hosts the attested corpus (native-guarded) ────

def test_c_path_self_hosts_the_attested_corpus() -> None:
    """The native ``srmech_toml`` parser self-hosts the attested descriptor corpus.
    The shipped corpus is FLOAT-FREE, so the decline-set is EMPTY; each self-hosted
    parse equals the stdlib oracle. (A float-bearing descriptor would DECLINE and
    ride tomllib bit-exactly — `#T1066` — and the hash would STILL be invariant, per
    the universal test above.)"""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), (
        "native library is loaded but exposes no srmech_toml_parse — a stale / "
        "pre-rc391 build")
    self_hosted, declined = [], []
    for path in _attested_descriptor_paths():
        text = _read(path)
        got_c = _native.toml_loads_c(text)
        if got_c is None:
            declined.append(path.parent.name)
        else:
            self_hosted.append(path.parent.name)
            assert got_c == _stdlib_toml.loads(text), (
                f"C-vs-tomllib dict mismatch for attested descriptor "
                f"{path.parent.name}")
    assert declined == [], (
        f"attested descriptor(s) unexpectedly DECLINED by the C parser: {declined}. "
        f"The shipped attested corpus is float-free; a new decline means a float "
        f"(or other unsupported construct) was added — update this expectation and "
        f"confirm the descriptor_hash invariant still holds (it does, via the "
        f"universal test, because the decline rides tomllib on both paths).")
    assert self_hosted, "no attested descriptor self-hosted on the C parser"
