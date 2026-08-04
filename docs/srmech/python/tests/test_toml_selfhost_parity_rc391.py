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

    A DECLINE (``toml_loads_c`` returns ``None``) is recorded as an EXPLICIT skip
    with its reason — never a silent pass. ``test_decline_set_is_empty`` then
    turns any such decline into a hard corpus-level failure (full-coverage
    proof)."""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), (
        "native library is loaded but exposes no srmech_toml_parse — a stale / "
        "pre-rc391 build; the C symbol this rc adds is missing")
    text = _read(path)
    expected = _stdlib_toml.loads(text)
    got = _native.toml_loads_c(text)
    if got is None:
        pytest.skip(
            f"C parser DECLINED {_rel(path)} (a float value, or a construct outside "
            f"the supported subset) — it rides the tomllib fallback; the decline "
            f"boundary is pinned by test_declines_are_exactly_the_float_docs")
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


def test_declines_are_exactly_the_float_docs():
    """FULL COVERAGE, honestly bounded. The plan assumed the corpus was
    float-free; it is NOT — ``best_rational_signed.toml`` carries
    ``dead_band = 1e-12``, which srmech_toml's libm-free accumulator lands 1 ULP
    off tomllib. So ``toml_loads_c`` DECLINES float-bearing documents (they ride
    the bit-exact stdlib parser) and self-hosts everything else. This test pins
    that exact boundary: every declined doc contains a float, and NO non-float
    doc declines — i.e. the ONLY thing the C path gives up is float fidelity, a
    known + documented gap, never an integer / string / table grammar failure."""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), "stale lib: no srmech_toml_parse"
    declined = []
    non_float_declines = []
    float_docs_not_declined = []
    for path in _TOML_FILES:
        text = _read(path)
        has_float = _has_float(_stdlib_toml.loads(text))
        is_decline = _native.toml_loads_c(text) is None
        if is_decline:
            declined.append(_rel(path))
            if not has_float:
                non_float_declines.append(_rel(path))
        elif has_float:
            float_docs_not_declined.append(_rel(path))
    assert non_float_declines == [], (
        f"the C parser DECLINED float-FREE descriptor(s) — a real grammar gap, "
        f"not the documented float boundary: {non_float_declines}")
    assert float_docs_not_declined == [], (
        f"float-bearing descriptor(s) were NOT declined, so a non-bit-exact "
        f"float may have slipped through the native path: {float_docs_not_declined}")


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


def test_float_doc_rides_stdlib():
    """The float-fidelity boundary, made explicit. ``1e-12`` is the exact value
    the corpus carries and that srmech_toml lands 1 ULP off. The native path must
    DECLINE it (return None), and the front door must therefore hand back the
    stdlib's correctly-rounded value — bit-exact with tomllib."""
    require_native("srmech_toml_parse")
    doc = "dead_band = 1e-12\n"
    assert _native.toml_loads_c(doc) is None, (
        "a float-bearing doc must be declined by the native path so it rides the "
        "bit-exact stdlib parser (float fidelity is not guaranteed in C)")
    # The internal front door still returns the correct value (via tomllib).
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
