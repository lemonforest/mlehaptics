"""rc391 / #T907 slice 1 — the co-equal dual-construction consistency oracle for
srmech's self-hosted TOML reader.

Per ``[[user_stance_co_equal_dual_construction_is_a_consistency_oracle]]``: this
test does NOT certify that the C parser is "correct" in the abstract. It
certifies MUTUAL REALIZABILITY — that srmech's native ``srmech_toml`` parser and
the stdlib ``tomllib`` parser produce the SAME Python dict for every TOML
document srmech actually ships. Any DISAGREEMENT is the finding, and (because
``descriptor_hash`` re-emits the parsed dict as ``json.dumps(sort_keys=True)``
for the attestation SHA) a shape divergence would silently corrupt attestation —
so full corpus parity is load-bearing, not cosmetic.

Two paths are pinned against the stdlib oracle for every ``.toml`` under
``srmech/``:

* ``srmech._native.toml_loads_c`` — the raw C parse + tree-walk (Route A).
* ``srmech._toml.loads``          — srmech's internal front-door loader.

The C-path assertions are native-guarded with ``require_native`` (the
`#T843` / `#T1004` contract): they SKIP pure-by-design in the no-native shard and
FAIL if the library is missing unexpectedly. A bare ``assert HAS_NATIVE`` is the
exact bug this contract exists to prevent, so it is never used here.

numpy-free by construction (stdlib tomllib / pathlib only).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import srmech
from srmech import _native, _toml
from tests._native_gate import require_native

if sys.version_info >= (3, 11):
    import tomllib as _stdlib_toml
else:  # pragma: no cover
    import tomli as _stdlib_toml  # type: ignore[no-redef]


_PKG_ROOT = Path(srmech.__file__).resolve().parent
_TOML_FILES = sorted(_PKG_ROOT.rglob("*.toml"))

# int64 range — the one silent-overflow class the C parser has (values beyond it
# return SRMECH_ERR_OVERFLOW, where tomllib would give an unbounded Python int).
_INT64_MIN = -(2 ** 63)
_INT64_MAX = 2 ** 63 - 1


def _read(path: Path) -> str:
    """Read a descriptor as the shipped consumers do — raw bytes, UTF-8 decode,
    NO newline translation — so both parsers see byte-identical input."""
    return path.read_bytes().decode("utf-8")


def _rel(path: Path) -> str:
    return path.relative_to(_PKG_ROOT).as_posix()


def _iter_ints(obj):
    """Yield every int in a parsed TOML object (bool is excluded — it is its own
    TOML type, and ``isinstance(True, int)`` would otherwise mis-count it)."""
    if isinstance(obj, bool):
        return
    if isinstance(obj, int):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _iter_ints(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_ints(v)


def test_corpus_is_non_empty():
    """A glob that finds nothing would make every parity test vacuously green.
    This is the false-green guard: the corpus must actually exist."""
    assert _TOML_FILES, (
        f"no .toml descriptors found under {_PKG_ROOT} — the parity oracle would "
        f"pass vacuously; the glob or the package layout is broken")


@pytest.mark.parametrize("path", _TOML_FILES, ids=lambda p: _rel(p))
def test_c_path_parity(path: Path):
    """srmech_toml (C) == tomllib for every shipped descriptor.

    As of rc397 (`#T1066`) the C float parse is correctly-rounded, so the whole
    shipped corpus — floats included — self-hosts on ``srmech_toml``. A DECLINE
    (``toml_loads_c`` returns ``None``) is therefore now a REGRESSION on this
    float-free-plus-float corpus, not an expected skip, and fails here directly;
    ``test_no_corpus_doc_declines`` is the corpus-level companion proof."""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), (
        "native library is loaded but exposes no srmech_toml_parse — a stale / "
        "pre-rc391 build; the C symbol this rc adds is missing")
    text = _read(path)
    expected = _stdlib_toml.loads(text)
    got = _native.toml_loads_c(text)
    assert got is not None, (
        f"C parser DECLINED {_rel(path)} — since rc397 the entire shipped corpus "
        f"(floats included) must self-host on srmech_toml; a decline means an "
        f"unsupported construct crept in, or the float fix regressed")
    assert got == expected, f"C-vs-tomllib dict mismatch for {_rel(path)}"


@pytest.mark.parametrize("path", _TOML_FILES, ids=lambda p: _rel(p))
def test_frontdoor_parity(path: Path):
    """srmech._toml.loads (the internal front door) == tomllib for every
    descriptor. Native-first with a tomllib floor, so the value must match the
    stdlib oracle either way."""
    require_native("srmech_toml_parse")
    text = _read(path)
    assert _toml.loads(text) == _stdlib_toml.loads(text), (
        f"_toml.loads-vs-tomllib mismatch for {_rel(path)}")


def _has_float(obj) -> bool:
    """True if a parsed TOML object contains any float (recursively)."""
    if isinstance(obj, float):
        return True
    if isinstance(obj, dict):
        return any(_has_float(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_has_float(v) for v in obj)
    return False


def test_no_corpus_doc_declines():
    """FULL COVERAGE. Before rc397 the corpus was NOT float-free —
    ``best_rational_signed.toml`` carries ``dead_band = 1e-12``, which the old
    libm-free accumulator landed 1 ULP off tomllib, so ``toml_loads_c`` DECLINED
    every float-bearing document and rode the stdlib parser. rc397 (`#T1066`)
    made the C decimal→double parse correctly-rounded (Clinger fast path +
    srmech_bigint exact tail), closing that last gap. So the boundary has moved:
    the C path now self-hosts the ENTIRE shipped corpus, floats and all, and the
    decline-set is EMPTY. Any decline here is a real grammar gap (a datetime, a
    quoted key, an int past int64) or a float-fix regression — never expected."""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), "stale lib: no srmech_toml_parse"
    declined = []
    float_docs_declined = []
    for path in _TOML_FILES:
        text = _read(path)
        if _native.toml_loads_c(text) is None:
            declined.append(_rel(path))
            if _has_float(_stdlib_toml.loads(text)):
                float_docs_declined.append(_rel(path))
    assert float_docs_declined == [], (
        f"float-bearing descriptor(s) still DECLINE after rc397 — the correctly-"
        f"rounded C float parse should self-host them bit-exactly: {float_docs_declined}")
    assert declined == [], (
        f"C parser DECLINED descriptor(s) — since rc397 the whole shipped corpus "
        f"self-hosts on srmech_toml; a decline means an unsupported construct "
        f"(datetime / quoted key / >int64) crept in: {declined}")


def test_type_fidelity():
    """int stays int (not float, not bool); bool stays bool — the type-shape
    divergences that would change a descriptor_hash silently. (Floats are the
    documented decline boundary, exercised in test_float_doc_rides_stdlib.)"""
    require_native("srmech_toml_parse")
    doc = (
        "i = 42\n"
        "big = 9000000000\n"
        "flag_true = true\n"
        "flag_false = false\n"
        "name = \"srmech\"\n"
        "items = [1, 2, 3]\n"
    )
    got = _native.toml_loads_c(doc)
    assert got is not None, "type-fidelity doc unexpectedly declined by C parser"
    assert got == _stdlib_toml.loads(doc), "type-fidelity doc: C-vs-tomllib mismatch"
    assert type(got["i"]) is int and got["i"] == 42
    assert type(got["big"]) is int and got["big"] == 9000000000
    # bool must NOT collapse to int, and int must NOT read as bool.
    assert type(got["flag_true"]) is bool and got["flag_true"] is True
    assert type(got["flag_false"]) is bool and got["flag_false"] is False
    assert type(got["i"]) is not bool
    assert type(got["name"]) is str
    assert all(type(x) is int for x in got["items"])


def test_float_doc_self_hosts():
    """The float-fidelity boundary, closed. ``1e-12`` is the exact value the
    corpus carries and that the OLD accumulator landed 1 ULP off. rc397
    (`#T1066`) makes the native path parse it correctly-rounded, so it now
    SELF-HOSTS (``toml_loads_c`` returns the dict, not None) bit-exactly, and the
    front door returns the same value it always did."""
    require_native("srmech_toml_parse")
    doc = "dead_band = 1e-12\n"
    got_c = _native.toml_loads_c(doc)
    assert got_c is not None, (
        "since rc397 a float-bearing doc must SELF-HOST on the native path "
        "(correctly-rounded C parse), not decline")
    assert got_c == _stdlib_toml.loads(doc), "C float parse is not bit-exact with tomllib"
    # The internal front door returns the same correctly-rounded value.
    assert _toml.loads(doc) == _stdlib_toml.loads(doc)
    assert type(_toml.loads(doc)["dead_band"]) is float


def test_no_corpus_int_exceeds_int64():
    """The C parser caps integers at int64; assert no shipped descriptor carries a
    value that would overflow it (which would force a tomllib fallback and break
    the full-coverage claim)."""
    offenders = []
    for path in _TOML_FILES:
        data = _stdlib_toml.loads(_read(path))
        for value in _iter_ints(data):
            if value < _INT64_MIN or value > _INT64_MAX:
                offenders.append((_rel(path), value))
    assert offenders == [], f"corpus int(s) exceed int64: {offenders}"
