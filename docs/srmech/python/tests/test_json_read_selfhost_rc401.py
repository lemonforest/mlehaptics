"""srmech._json (READ half) is byte-for-byte the stdlib json — rc401, `#T1008`.

The rc401 self-host repoints srmech's descriptor / manifest / catalog / provenance
JSON reads onto :mod:`srmech._json`, which runs the native ``srmech_json_parse``
first and falls back to the stdlib. That is only safe if the two agree on the
PARSED OBJECT for every document srmech can meet — so this module compares them
directly, over the real committed corpus plus a battery aimed at the places a
hand-rolled C parser and CPython diverge.

Three properties are load-bearing and each has its own test:

1. **Equal values, equal types.** ``==`` is not enough (``1 == 1.0 == True`` in
   Python), so every comparison also checks ``repr`` and the recursive type shape.
2. **Equal failures.** The native path never raises on bad input — it DECLINES —
   so a caller's ``except json.JSONDecodeError`` must keep working. Every
   malformed input is checked to raise the same exception type from both.
3. **The divergence guards actually fire.** Historically the C parser
   returned SRMECH_OK with a WRONG value for an out-of-int64 integer (bare
   ``strtoll``, no ``errno`` check → clamped to INT64_MAX) and for numbers its
   loose ``[0-9.eE+-]`` scanner accepted but CPython rejects. Those were caught
   by a Python pre-scan rather than by a status code. **Both halves of that are
   now historical**: rc402 (`#T1068`) made the C scanner strict RFC 8259 and
   made it DECLINE the out-of-int64 case, and rc404 (`#T1069`) re-statused that
   decline to ``SRMECH_ERR_LIMIT`` and DELETED the pre-scan. The assertions
   below are unchanged and still pass, because they were always behavioural —
   ``_native_declined`` observes ``json_loads_c(...) is None`` and never named
   the mechanism. What they pin is that the DECLINE still happens; a guard that
   stopped firing would otherwise be invisible.
"""

from __future__ import annotations

import json
import math
import pathlib
import struct

import pytest

from srmech import _json, _native

from tests._native_gate import require_native

PY_DIR = pathlib.Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _typed_shape(obj):
    """Recursive (type, value) shape, so 1 / 1.0 / True never compare equal."""
    if isinstance(obj, dict):
        return ("dict", [(k, _typed_shape(v)) for k, v in obj.items()])
    if isinstance(obj, list):
        return ("list", [_typed_shape(v) for v in obj])
    if isinstance(obj, bool):
        return ("bool", obj)
    if isinstance(obj, float):
        # NaN is not self-equal, so compare the exact IEEE-754 bit pattern.
        return ("float", struct.pack(">d", obj))
    if isinstance(obj, int):
        return ("int", obj)
    return (type(obj).__name__, obj)


def _assert_parity(text, label):
    """srmech._json.loads and json.loads agree — on the value or on the raise."""
    try:
        want = json.loads(text)
        want_exc = None
    except Exception as exc:                      # noqa: BLE001 - parity is the point
        want, want_exc = None, type(exc)
    try:
        got = _json.loads(text)
        got_exc = None
    except Exception as exc:                      # noqa: BLE001
        got, got_exc = None, type(exc)

    assert got_exc is want_exc, (
        f"{label}: exception mismatch — stdlib raised {want_exc}, "
        f"srmech._json raised {got_exc}")
    if want_exc is None:
        assert _typed_shape(got) == _typed_shape(want), (
            f"{label}: parsed value/type mismatch")
        assert repr(got) == repr(want), f"{label}: repr mismatch"


def _native_declined(text):
    """True when the native path handed the document back to the floor."""
    return _native.json_loads_c(text) is None


# --------------------------------------------------------------------------
# the real committed corpus
# --------------------------------------------------------------------------
def _corpus_json_files():
    return sorted(p for p in PY_DIR.rglob("*.json")
                  if ".git" not in p.parts and "node_modules" not in p.parts)


def _corpus_ndjson_files():
    return sorted(p for p in PY_DIR.rglob("*.ndjson")
                  if ".git" not in p.parts and "node_modules" not in p.parts)


def test_corpus_has_files():
    """The corpus tests are worthless if they silently iterate nothing."""
    assert len(_corpus_json_files()) >= 5
    assert len(_corpus_ndjson_files()) >= 5


@pytest.mark.parametrize("path", _corpus_json_files(),
                         ids=lambda p: p.name)
def test_corpus_json_file_parity(path):
    """Every committed *.json parses identically through both loaders."""
    _assert_parity(path.read_text(encoding="utf-8"), str(path))


def test_corpus_ndjson_line_parity():
    """Every committed MPR/NDJSON line parses identically through both loaders.

    This is the corpus ``MPRRecord.from_json_line`` actually walks, and rc401
    repointed that method, so it is the closest thing to an end-to-end check.
    """
    n_lines = 0
    for path in _corpus_ndjson_files():
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            _assert_parity(s, f"{path}:{i}")
            n_lines += 1
    assert n_lines >= 50, f"only {n_lines} NDJSON lines exercised"


def test_corpus_json_files_use_the_native_path():
    """The corpus is not silently riding the floor for every file.

    Without this, every corpus assertion above would still pass with the native
    path declining 100% of the time — the instrument would be measuring nothing.
    """
    require_native("srmech._json native JSON read path")
    used = [p for p in _corpus_json_files()
            if not _native_declined(p.read_text(encoding="utf-8"))]
    assert len(used) >= 5, (
        f"native path was used for only {len(used)} corpus files — the "
        f"self-host is declining nearly everything, so it buys nothing")


# --------------------------------------------------------------------------
# the hand-built battery
# --------------------------------------------------------------------------
#: A single backslash, built so no formatter can fold the JSON
#: escape sequences below into the characters they denote.
_BS = chr(92)

VALUE_CASES = [
    ("empty object", "{}"),
    ("empty array", "[]"),
    ("empty string", '""'),
    ("null", "null"),
    ("true", "true"),
    ("false", "false"),
    ("int zero", "0"),
    ("int neg zero", "-0"),
    ("int", "42"),
    ("int negative", "-42"),
    ("int64 max", "9223372036854775807"),
    ("int64 min", "-9223372036854775808"),
    ("float simple", "1.5"),
    ("float pi", "3.141592653589793"),
    ("float max", "1.7976931348623157e308"),
    ("float min normal", "2.2250738585072014e-308"),
    ("float subnormal", "5e-324"),
    ("float neg exp", "-1.234567890123456e-77"),
    ("float exp plus", "1e+5"),
    ("float zero", "0.0"),
    ("float neg zero", "-0.0"),
    ("float overflow to inf", "1e400"),
    ("float neg overflow", "-1e400"),
    ("nested objects", '{"a":{"b":{"c":{"d":1}}}}'),
    ("nested arrays", "[[[[1]]]]"),
    ("mixed nesting", '{"a":[1,{"b":[2,3]},null],"c":true}'),
    # NOTE: every backslash below is built with _BS = chr(92) at runtime.
    # Written as a literal, editors and formatters repeatedly folded
    # "\u00e9" into the CHARACTER e-acute, which silently deleted the
    # \uXXXX-decoding coverage this file exists to provide.
    ("unicode escape bmp",
     '"h' + _BS + 'u00e9llo ' + _BS + 'u4e16' + _BS + 'u754c"'),
    ("unicode raw bmp", '"h\u00e9llo \u4e16\u754c"'),
    ("astral escape surrogate pair",
     '"' + _BS + 'ud83d' + _BS + 'ude00"'),
    ("astral raw", '"' + chr(0x1F600) + '"'),
    ("all simple escapes", r'"a\"b\\c\/d\be\ff\ng\rh\ti"'),
    ("escape at end", r'"abc\n"'),
    ("duplicate keys last wins", '{"a":1,"a":2,"a":3}'),
    ("key with escapes", r'{"a\nb":1}'),
    ("empty key", '{"":1}'),
    ("whitespace everywhere", '  {  "a" :  1 , "b" : [ 2 , 3 ]  }  '),
    ("deep nesting 60", "[" * 60 + "1" + "]" * 60),
    ("wide object", json.dumps({f"k{i}": i for i in range(500)})),
    ("dense int array", json.dumps(list(range(3000)))),
    ("float array", json.dumps([i * 0.1 for i in range(300)])),
    ("array of strings", json.dumps([f"s{i}" for i in range(300)])),
    # CPython json ACCEPTS a lone surrogate and yields a lone-surrogate str;
    # srmech_json rejects it, so this rides the floor and must still match.
    ("lone high surrogate", '"' + _BS + 'ud800A"'),
]

MALFORMED_CASES = [
    ("empty input", ""),
    ("whitespace only", "   "),
    ("leading zero", "01"),
    ("double decimal", "1.2.3"),
    ("bare exponent", "1e"),
    ("bare minus", "-"),
    ("double minus", "--1"),
    ("leading plus", "+1"),
    ("leading dot", ".5"),
    ("trailing dot", "1."),
    ("trailing garbage", "{} x"),
    ("unterminated string", '"abc'),
    ("unterminated object", '{"a":1'),
    ("trailing comma object", '{"a":1,}'),
    ("trailing comma array", "[1,2,]"),
    ("single quotes", "{'a':1}"),
    ("unquoted key", "{a:1}"),
    ("bad escape", r'"\q"'),
    ("raw control in string", '"a\x01b"'),
]


@pytest.mark.parametrize("label,text", VALUE_CASES, ids=[c[0] for c in VALUE_CASES])
def test_battery_value_parity(label, text):
    _assert_parity(text, label)


@pytest.mark.parametrize("label,text", MALFORMED_CASES,
                         ids=[c[0] for c in MALFORMED_CASES])
def test_battery_malformed_parity(label, text):
    """Both loaders raise, and raise the SAME exception type.

    The native path declines rather than raising, so every exception here comes
    from the stdlib floor — which is exactly why ``except json.JSONDecodeError``
    still works at all 28 repointed call sites.
    """
    with pytest.raises(json.JSONDecodeError):
        _json.loads(text)
    _assert_parity(text, label)


# --------------------------------------------------------------------------
# floats — rc397's correct-rounding work is what makes this pass
# --------------------------------------------------------------------------
FLOAT_LITERALS = [
    "0.1", "0.2", "0.3", "1e-323", "5e-324", "1.7976931348623157e308",
    "2.2250738585072014e-308", "1.0000000000000002", "0.30000000000000004",
    "123456789.123456789", "1e-7", "9007199254740993.0", "1.1e-300",
    "-2.5e-10", "6.02214076e23", "1.602176634e-19", "0.000001", "1E5",
]


@pytest.mark.parametrize("lit", FLOAT_LITERALS)
def test_float_bit_exact(lit):
    """Floats must match to the BIT, not to a tolerance."""
    got = _json.loads(lit)
    want = json.loads(lit)
    assert isinstance(got, float) and isinstance(want, float)
    assert struct.pack(">d", got) == struct.pack(">d", want), (
        f"{lit}: {got!r} != {want!r} at the bit level")


def test_float_array_bit_exact():
    """A whole array of awkward floats, in one document, through the C parser."""
    vals = [i * 0.1 for i in range(1000)] + [1 / 3, 2 / 3, math.pi, math.e]
    text = json.dumps(vals)
    got = _json.loads(text)
    assert [struct.pack(">d", v) for v in got] == \
           [struct.pack(">d", v) for v in vals]


def test_nan_and_infinity_parity():
    """CPython accepts these non-standard literals; srmech_json does not.

    So they must DECLINE to the floor and still come back as the float values
    CPython would produce — not raise, and not come back wrong.
    """
    assert math.isnan(_json.loads("NaN"))
    assert _json.loads("Infinity") == math.inf
    assert _json.loads("-Infinity") == -math.inf
    assert math.isnan(_json.loads('{"x": NaN}')["x"])


# --------------------------------------------------------------------------
# the silent-divergence guards — these MUST decline, or the value is wrong
# --------------------------------------------------------------------------
BIG_INTS = [
    "99999999999999999999",
    "-99999999999999999999",
    "9223372036854775808",            # int64 max + 1
    "-9223372036854775809",           # int64 min - 1
    "1" + "0" * 40,
    "170141183460469231731687303715884105727",
]


@pytest.mark.parametrize("lit", BIG_INTS)
def test_bigint_declines_and_value_is_exact(lit):
    """An out-of-int64 integer must NOT ride the C parser.

    Before rc402 (`#T1068`) ``srmech_json.c`` parsed ints with a bare
    ``strtoll`` and never inspected ``errno``, so it returned SRMECH_OK with the
    value CLAMPED to ``INT64_MAX`` — a silent wrong answer no status check could
    catch, which a Python pre-scan had to catch first. rc402 made the C parser
    decline it itself and rc404 (`#T1069`) re-statused that decline to
    ``SRMECH_ERR_LIMIT`` (a value range no arena relieves), deleting the
    pre-scan. Both halves are still asserted: the decline happens, AND the value
    that comes back is the exact Python int.
    """
    require_native("srmech._json out-of-int64 decline guard")
    assert _native_declined(lit), (
        f"{lit}: native path did NOT decline — it would clamp to int64")
    assert _json.loads(lit) == int(lit)
    assert _json.loads(f'{{"n": {lit}}}')["n"] == int(lit)


LOOSE_NUMBERS = ["01", "1.2.3", "1e", "-", "--1", "1.", "[1,2.3.4]", "{\"a\":01}"]


@pytest.mark.parametrize("text", LOOSE_NUMBERS)
def test_loose_number_declines(text):
    """Numbers CPython rejects must not come back as values.

    The C scanner's ``[0-9.eE+-]`` character class used to swallow these, so
    before rc402 (`#T1068`) the parser returned a VALUE where CPython raises and
    a Python pre-scan was the only thing catching it. rc402 made the C scanner
    strict RFC 8259, so it now rejects exactly what CPython rejects and the
    pre-scan became redundant — rc404 (`#T1069`) removed it. This assertion is
    unchanged and still passes; only what satisfies it moved into C.
    """
    require_native("srmech._json loose-number decline guard")
    assert _native_declined(text), (
        f"{text!r}: native path did NOT decline a number CPython rejects")


# Built by concatenation so the six-character JSON escape can never be folded
# into a real NUL byte by an editor or a tool that rewrites this file.
_NUL_ESC = chr(92) + 'u0000'
_NUL_KEY_DOC = '{"' + _NUL_ESC + '":1}'
_NUL_VAL_DOC = '"a' + _NUL_ESC + 'b"'


def test_nul_escape_declines():
    """An object KEY carrying a NUL would be truncated by the C strlen storage."""
    require_native("srmech._json NUL-escape decline guard")
    assert _native_declined(_NUL_KEY_DOC)
    assert _json.loads(_NUL_KEY_DOC) == {"\x00": 1}
    assert _json.loads(_NUL_VAL_DOC) == "a\x00b"


def test_long_number_literal_declines():
    """>= 63 bytes hits the C scanner's ``tmp[64]`` staging buffer.

    This returned ``SRMECH_ERR_OVERFLOW`` until rc404 (`#T1069`) — indistinguishable
    from arena exhaustion, so it had to be caught BEFORE the call or the grow
    loop doubled to the cap for nothing. It is now ``SRMECH_ERR_LIMIT``: a
    compiled-in structural bound, distinguishable at the status, so the loop
    declines on the first call and no pre-scan is needed.
    """
    require_native("srmech._json long-number decline guard")
    lit = "1." + "0" * 70
    assert _native_declined(lit)
    assert _json.loads(lit) == float(lit)


def test_deep_nesting_declines_past_c_limit():
    """SRMECH_JSON_MAX_DEPTH is 64; CPython goes much deeper."""
    require_native("srmech._json depth decline guard")
    deep = "[" * 200 + "1" + "]" * 200
    assert _native_declined(deep)
    _assert_parity(deep, "deep 200")


def test_lone_surrogate_declines():
    require_native("srmech._json lone-surrogate decline guard")
    assert _native_declined(r'"\ud800"')
    assert _native_declined(r'"\udc00"')
    assert _json.loads(r'"\ud800"') == "\ud800"


def test_shallow_document_uses_native():
    """The guards must not have swallowed the ordinary case.

    Every decline test above passes trivially if the native path declines
    EVERYTHING, so pin the positive direction too.
    """
    require_native("srmech._json native JSON read path")
    for text in ('{"a":1}', "[1,2,3]", '"hello"', "3.14", "true",
                 '{"nested":{"deep":[1,2,{"x":"y"}]}}'):
        assert not _native_declined(text), f"{text!r} should use the native path"


# --------------------------------------------------------------------------
# the API surface
# --------------------------------------------------------------------------
def test_load_from_binary_and_text_handles(tmp_path):
    """:func:`srmech._json.load` mirrors ``json.load`` for both handle modes."""
    payload = {"a": [1, 2, {"b": "héllo 世界"}], "c": None, "d": 1.5}
    p = tmp_path / "doc.json"
    p.write_text(json.dumps(payload), encoding="utf-8")

    with open(p, "rb") as fh:
        assert _json.load(fh) == payload
    with open(p, "r", encoding="utf-8") as fh:
        assert _json.load(fh) == payload


def test_loads_accepts_bytes_like_stdlib():
    raw = b'{"a": 1}'
    assert _json.loads(raw) == json.loads(raw) == {"a": 1}


def test_is_internal_not_a_registered_tool():
    """rc401 adds no ToolEntry, no rosetta row, no describe() surface.

    ``srmech._json`` is plumbing srmech calls on itself — the same call made for
    ``srmech._toml`` in `#T907`.
    """
    import srmech

    assert srmech.describe()["tools"]["total"] == 598
    blob = json.dumps(srmech.describe())
    assert "_json" not in blob
    assert "json_loads_c" not in blob


def test_native_symbol_is_bound_when_native():
    require_native("srmech._json native JSON read path")
    assert hasattr(_native.LIB, "srmech_json_parse")
    assert hasattr(_native, "json_loads_c")
    # Binding an already-exported symbol adds no C surface.
    assert _native.EXPECTED_ABI_VERSION == 13


def test_pure_floor_is_reachable_and_correct():
    """The stdlib floor is the correctness path and must work on its own.

    Runs in BOTH modes: it never touches the native path, so it is the test that
    proves a pure / Pyodide install still reads every document correctly.
    """
    for _label, text in VALUE_CASES:
        assert _typed_shape(_json.loads(text)) == _typed_shape(json.loads(text))


# --------------------------------------------------------------------------
# The CLASSIFICATION gate — the structural analogue of the TOML arc's
# `test_exactly_one_native_first_toml_parse_floor` (rc400).
#
# Without this, the 27 / 13 / 4 split rc401 decided would live only in prose,
# and a later edit could quietly repoint a protocol boundary or un-repoint a
# self-host target with nothing going red. Every stdlib `json.loads` /
# `json.load` left in `srmech/` must be one of the ALLOWLISTED files below, and
# every allowlisted file must still HAVE one — a stale allowlist entry is as
# much a defect as a missing one.
# --------------------------------------------------------------------------

#: Files deliberately left on stdlib json, and WHY. Anything else with a
#: stdlib json read is an unfenced site and fails the gate.
STDLIB_JSON_ALLOWLIST = {
    # PROTOCOL BOUNDARY — untrusted / external data on a protocol contract.
    "srmech/mcp/_server.py": "MCP JSON-RPC wire",
    "srmech/mcp/_sse.py": "MCP JSON-RPC wire",
    "srmech/mcp/_stdio.py": "MCP JSON-RPC wire",
    "srmech/mcp/_tools.py": "MCP JSON-RPC wire",
    "srmech/cli/dsl.py": "user-supplied CLI input",
    "srmech/cli/main.py": "user-supplied CLI input",
    "srmech/cli/bus.py": "user-supplied CLI input",
    "srmech/bus/_event.py": "bus wire, cross-process payloads",
    "srmech/bus/_bio_totp.py": "bus wire, cross-process payloads",
    "srmech/amsc/adapters/json_api.py": "fetched external HTTP response body",
    # LAYERING — srmech._json is a CONSUMER of this shim; repointing it would
    # invert the dependency (see the comment at its `import json`).
    "srmech/_native/__init__.py": "the ctypes shim srmech._json itself calls",
}

#: Modules rc401 repointed. Each must bind the front door and must have NO
#: stdlib json read left.
REPOINTED_MODULES = [
    "srmech.biology.genome",
    "srmech.amsc.catalog",
    "srmech.amsc.format",
    "srmech.amsc.adapters.literature_curated",
    # rc418 (`#T1108`): the envelope-shaped curated peer. It reads committed
    # MPR v1 lines, so it binds the front door like every other repointed
    # module and carries NO stdlib json read. 27 -> 28 sites.
    "srmech.amsc.adapters.mpr_committed",
    "srmech.amsc.adapters.substrate_parameterization",
    "srmech.cascade.compose",
    "srmech.dsl._chain",
    "srmech.introspect.op_provenance",
    "srmech.introspect.carrier_schema",
    "srmech.introspect.responsion_schema",
    "srmech.introspect.tool_schema",
    "srmech.introspect._event",
]

N_REPOINTED_SITES = 28
N_ALLOWLISTED_SITES = 17


def _json_read_sites(pkg_root):
    """{relpath: [(lineno, 'stdlib'|'selfhost')]} for every real json read call.

    AST-based on purpose: a plain grep over this tree reports 86 hits, but 42 of
    those are generated docstring PROSE in introspect/_tool_docs*.py. Only a
    real ast.Call counts.
    """
    import ast as _ast

    found = {}
    for path in sorted(pkg_root.rglob("*.py")):
        try:
            tree = _ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:                              # pragma: no cover
            continue
        rel = path.relative_to(pkg_root.parent).as_posix()
        for node in _ast.walk(tree):
            if not (isinstance(node, _ast.Call)
                    and isinstance(node.func, _ast.Attribute)
                    and node.func.attr in ("loads", "load")):
                continue
            base = getattr(node.func.value, "id", None)
            if base in ("json", "_json"):
                found.setdefault(rel, []).append((node.lineno, "stdlib"))
            elif base == "_srmech_json":
                found.setdefault(rel, []).append((node.lineno, "selfhost"))
    return found


def _pkg_root():
    import srmech

    return pathlib.Path(srmech.__file__).resolve().parent


def test_no_unfenced_stdlib_json_read_in_srmech():
    """Every stdlib json read left in srmech/ is on the documented allowlist."""
    sites = _json_read_sites(_pkg_root())
    offenders = {
        rel: [ln for ln, kind in hits if kind == "stdlib"]
        for rel, hits in sites.items()
        if any(k == "stdlib" for _, k in hits)
        and rel not in STDLIB_JSON_ALLOWLIST
        and rel != "srmech/_json.py"
    }
    assert not offenders, (
        "unfenced stdlib json read(s) — either repoint onto srmech._json or add "
        f"to STDLIB_JSON_ALLOWLIST with a reason: {offenders}")


def test_allowlist_has_no_stale_entries():
    """A file on the allowlist that no longer reads json is a stale fence.

    Enforced in BOTH directions so the allowlist cannot rot into a rubber stamp.
    """
    sites = _json_read_sites(_pkg_root())
    stale = [rel for rel in STDLIB_JSON_ALLOWLIST
             if not any(k == "stdlib" for _, k in sites.get(rel, []))]
    assert not stale, (
        f"STDLIB_JSON_ALLOWLIST names file(s) with no stdlib json read left: {stale}")


def test_repointed_modules_bind_the_front_door():
    """Each repointed module routes through srmech._json and keeps none of its own."""
    import importlib

    import srmech

    sites = _json_read_sites(_pkg_root())
    for name in REPOINTED_MODULES:
        mod = importlib.import_module(name)
        assert getattr(mod, "_srmech_json", None) is srmech._json, (
            f"{name} no longer routes its JSON reads through srmech._json")
        rel = name.replace(".", "/") + ".py"
        left = [ln for ln, kind in sites.get(rel, []) if kind == "stdlib"]
        assert not left, (
            f"{name} still has stdlib json read(s) at line(s) {left}")


def test_classification_counts_are_pinned():
    """The 28 / 17 split is a measurement, so pin it — prose cannot go red."""
    sites = _json_read_sites(_pkg_root())
    n_self = sum(1 for hits in sites.values() for _, k in hits if k == "selfhost")
    n_std = sum(len([1 for _, k in hits if k == "stdlib"])
                for rel, hits in sites.items() if rel in STDLIB_JSON_ALLOWLIST)
    assert n_self == N_REPOINTED_SITES, (
        f"repointed self-host json read sites moved: {n_self} != {N_REPOINTED_SITES}")
    assert n_std == N_ALLOWLISTED_SITES, (
        f"allowlisted stdlib json read sites moved: {n_std} != {N_ALLOWLISTED_SITES}")
