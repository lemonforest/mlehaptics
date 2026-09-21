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
from srmech.math.q import Q as _Q
from srmech.math.q import parse_float_exact   # rc479 (`#T1188`): contract A
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


def _deep_equal(a, b) -> bool:
    """Byte-identical-parse equality — the verb dict ``==`` cannot be.

    rc420 (`#T1114`): the cascade-catalog proof cases legitimately carry
    TOML 1.0 special floats (``x = nan`` is best_rational_signed's
    documented boundary case, ``x = inf`` magnitude's), and under ``==`` a
    parse containing NaN can NEVER equal its oracle even when both parsers
    agree bit-for-bit — a false red from the comparison verb. Floats
    therefore compare by their 8 BYTES: NaN equals the same-bits NaN, and
    ``-0.0`` is DISTINCT from ``0.0`` — STRICTER than ``==`` on the
    signed-zero axis, i.e. the honest spelling of this module's own
    "byte-identical dicts" parity claim. Twin of the helper in
    ``test_toml_dedup_parity_rc400.py``."""
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


@pytest.mark.parametrize("path", _TOML_FILES, ids=lambda p: _rel(p))
def test_c_path_parity(path: Path):
    """srmech_toml (C) == tomllib for every FLOAT-FREE shipped descriptor, and
    a CARRIER decline for every float-bearing one.

    ⚠️ **rc479 (`#T1188`) split this, and the split is not rc397's decline
    coming back.** rc397 (`#T1066`) made the C decimal→double parse
    correctly-rounded, which closed the PRECISION decline; that is untouched and
    is not retracted. What rc479 changes is the CONTRACT: the front door returns
    the exact rational a decimal literal names, and no C value layer in this
    library holds a rational (``dv_value_t`` and ``srmech_mval_t`` are both
    ``double``), so the ctypes tree-walk DECLINES a float-bearing document and
    the exact Python floor answers it. A CARRIER decline where rc397's was a
    precision one.

    The claim is stronger than "nothing declines" was, because it is a
    PARTITION derived from the document itself: a float-FREE descriptor that
    declines is still rc397's regression (or a grammar gap), and a float-bearing
    one that self-hosts means the carrier decline stopped firing and a native
    cell is serving doubles where a pure cell serves ``Q``.

    rc420 (`#T1114`): the corpus gained TOML 1.0 special floats (the proof-case
    NaN/inf boundary inputs) — parsed by the ``toml_parse_special_float``
    tokenizer arm, compared here by BITS (see :func:`_deep_equal`)."""
    require_native("srmech_toml_parse")
    assert hasattr(_native.LIB, "srmech_toml_parse"), (
        "native library is loaded but exposes no srmech_toml_parse — a stale / "
        "pre-rc391 build; the C symbol this rc adds is missing")
    text = _read(path)
    expected = _stdlib_toml.loads(text)
    got = _native.toml_loads_c(text)
    if _has_float(expected):
        assert got is None, (
            f"{_rel(path)} carries a float and the C binding SELF-HOSTED it — "
            f"contract A's carrier decline has stopped firing, so a native cell "
            f"is about to serve a double where a pure cell serves an exact "
            f"rational: same call, same version, two different types")
        return
    assert got is not None, (
        f"C parser DECLINED the FLOAT-FREE {_rel(path)} — rc397's ground is "
        f"unchanged and a decline here means an unsupported construct crept in "
        f"or the float fix regressed. It is NOT the rc479 carrier decline, "
        f"which only reaches documents carrying a float")
    assert _deep_equal(got, expected), (
        f"C-vs-tomllib dict mismatch for {_rel(path)}")


@pytest.mark.parametrize("path", _TOML_FILES, ids=lambda p: _rel(p))
def test_frontdoor_parity(path: Path):
    """srmech._toml.loads (the internal front door) == tomllib for every
    descriptor, GIVEN THE SAME READER. Native-first with a stdlib floor, so the
    value must match the oracle either way.

    ⚠️ **rc479 (`#T1188`): the self-hosting contract is HOOK-RELATIVE.**
    Contract A makes the front door read a decimal literal as the exact rational
    it names, so a BARE ``tomllib`` oracle compares a hook against no hook and
    measures contract A rather than the self-host. The property this test was
    always about is *the front door equals the backend given the same
    ``parse_float``*, and that is what is compared. Restated, not weakened: the
    equality is still descriptor-for-descriptor and still byte-typed through
    :func:`_deep_equal`.
    """
    require_native("srmech_toml_parse")
    text = _read(path)
    oracle = _stdlib_toml.loads(text, parse_float=parse_float_exact)
    assert _deep_equal(_toml.loads(text), oracle), (
        f"_toml.loads-vs-stdlib mismatch for {_rel(path)} under the same reader")


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
    # ⚠️ rc479 (`#T1188`) INVERTS this clause, and the ground is a
    # different one from rc397's. rc397 removed the PRECISION decline and that
    # stays removed. Contract A opens a CARRIER decline: the front door returns
    # the exact rational a decimal literal names and no C value layer here holds
    # one, so a float-bearing document goes to the exact floor. The assertion is
    # therefore an EQUALITY between two sets derived from the corpus, which says
    # more than either direction alone.
    float_docs = sorted(_rel(p) for p in _TOML_FILES
                        if _has_float(_stdlib_toml.loads(_read(p))))
    assert float_docs, (
        "no shipped descriptor carries a float at all — the equality below "
        "would be vacuous and this test would certify nothing")
    assert sorted(declined) == float_docs, (
        f"the C binding's declines are no longer EXACTLY the float-bearing "
        f"descriptors.\n  declined:      {sorted(declined)}\n"
        f"  float-bearing: {float_docs}\n"
        f"A float-FREE document among the declines is rc397's regression or a "
        f"grammar gap. A float-bearing one among the self-hosted means contract "
        f"A's carrier decline stopped firing, and a native cell is serving "
        f"doubles where a pure cell serves an exact rational.")
    # The old trailing clause was `declined == []`, which the equality above
    # now SUBSUMES in one direction and CORRECTS in the other: after rc479 the
    # decline set is not empty, it is exactly the float-bearing set. What that
    # clause uniquely protected — a FLOAT-FREE document declining for a grammar
    # reason (a datetime, a quoted key, an int past int64) — is kept here as
    # its own assertion with its own message, because that failure has a
    # completely different remedy from a carrier one and must not arrive
    # wearing the carrier's name.
    grammar_declines = sorted(set(declined) - set(float_docs))
    assert grammar_declines == [], (
        f"C parser DECLINED FLOAT-FREE descriptor(s): {grammar_declines}. This "
        f"is NOT contract A's carrier decline — that one only reaches documents "
        f"carrying a float. An unsupported construct (datetime / quoted key / "
        f"int past int64) has crept into the shipped corpus, or rc397's "
        f"correctly-rounded float parse regressed.")


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
    """THE FLOAT BOUNDARY, now a CARRIER one — and rc397's is still closed.

    ``1e-12`` is the value the corpus carries and that the OLD libm-free
    accumulator landed 1 ULP off. rc397 (`#T1066`) made the C parse
    correctly-rounded and the PRECISION decline went away; **that is still true,
    and this test still proves it** — by reading the C parser's own double at
    the export, where the binding's carrier decline cannot reach.

    What rc479 (`#T1188`) changes is the BINDING: contract A returns the exact
    rational a decimal literal names, no C value layer holds one, so
    ``toml_loads_c`` declines and the exact floor answers. The name is kept
    because the subject is unchanged — this is the one float document, read
    three ways.
    """
    require_native("srmech_toml_parse")
    doc = "dead_band = 1e-12\n"

    # 1. the BINDING declines — the rc479 carrier decline
    assert _native.toml_loads_c(doc) is None, (
        "a float-bearing document no longer declines at the ctypes binding; "
        "contract A's carrier decline has stopped firing")

    # 2. the C PARSER is still correctly rounded — rc397's claim, read at the
    #    export as a C host would, because the binding can no longer report it.
    import ctypes
    import struct
    raw = doc.encode("utf-8")
    ws = ctypes.create_string_buffer(65536)
    out = ctypes.POINTER(_native._TomlValue)()
    rc = int(_native.LIB.srmech_toml_parse(
        raw, ctypes.c_size_t(len(raw)), ctypes.cast(ws, ctypes.c_void_p),
        ctypes.c_size_t(65536), ctypes.byref(out)))
    assert rc == _native.SRMECH_OK, rc
    root = out.contents
    assert root.type == _native.SRMECH_TOML_TABLE
    node = root.u.tbl.vals[0].contents
    assert node.type == _native.SRMECH_TOML_FLOAT, node.type
    assert struct.pack("<d", float(node.u.f)) == struct.pack("<d", 1e-12), (
        "the C float parse is no longer bit-exact with float('1e-12') — this "
        "IS rc397's claim and it is not what rc479 moved")

    # 3. the FRONT DOOR answers exactly, and the value is the decimal the
    #    literal spells. Decided by the integers: 1e-12 == 1/10**12 exactly.
    got = _toml.loads(doc)["dead_band"]
    assert isinstance(got, _Q), type(got).__name__
    assert got.numerator == 1 and got.denominator == 10 ** 12, (
        got.numerator, got.denominator)
    # and it PROJECTS to the same double the C parser produced
    assert struct.pack("<d", float(got)) == struct.pack("<d", 1e-12)


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
