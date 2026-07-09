"""rc187 — the C tool-call MARSHALLING FOUNDATION (the JSON-args↔typed-C-args
value carrier).

The MCP wire form is NOT self-describing — a param's TYPE comes from the rc184
registry, not the value — so marshalling is TWO-STAGE: (1) parse the JSON value
into a tagged carrier (``srmech_mval_t``); (2) typed-lower it keyed on the
registry type string (base64 str → BYTES, ``[re,im]`` → COMPLEX, the list /
mapping container families recursing the same leaf coercers). This rc builds
that shared carrier + ``srmech_mcp_marshal_arg`` (the C mirror of
``srmech.mcp._coercion.coerce_param`` for the bucket-(a) CLEAN scalar / str /
list / bytes / complex families) + ``srmech_mcp_serialise_result`` (the mirror
of ``serialise_native``), the foundation the rc188+ ``invoke_tool`` dispatch +
the #796 nested marshal build on.

THE PARITY PROOF (the DoD — no dispatch yet). For a representative set of
bucket-(a) param types, the C round-trip
``srmech_mcp_marshal_roundtrip(type, value_json)`` (stage-1 parse → marshal_arg
→ serialise_result) produces a canonical JSON **byte-identical** to the pure
Python ``json.dumps(serialise_native(coerce_param(value, type)),
separators=(",", ":"))`` — proving the C carrier + marshal genuinely lower a
JSON arg to a typed C value and back (base64 decode/encode == Python base64;
``complex`` ``[re,im]`` round-trips; the identity families pass through), not a
stub. A type OUTSIDE bucket-(a) (the Mat/Vec/HV/np.ndarray float carriers, the
by-reference handles) → an honest NOT_IMPL (the caller defers to pure); a
malformed wire value → BAD_INPUT.

The native-requiring assertions ``skipif`` cleanly when the rc187 C peer is
absent (pure / numpy-absent / stale-lib host). numpy-free (stdlib json/base64 +
the private ``srmech.mcp._coercion`` SSoT)."""

from __future__ import annotations

import base64
import ctypes
import json

import pytest

from srmech.amsc import _native
from srmech.mcp._coercion import coerce_param, serialise_native

_needs_native = pytest.mark.skipif(
    not _native.has_native_mcp_marshal(),
    reason="rc187 marshalling-foundation C peer not loaded (pure / stale host)",
)

_B64_HI = base64.b64encode(b"hi").decode("ascii")     # "aGk="
_B64_YA = base64.b64encode(b"ya").decode("ascii")     # "eWE="
_B64_EMPTY = base64.b64encode(b"").decode("ascii")    # ""
_B64_RAW = base64.b64encode(bytes(range(6))).decode("ascii")  # a 6-byte blob


def _py_roundtrip(value, type_string: str) -> bytes:
    """The pure Python coerce → serialise → canonical-JSON reference."""
    native = coerce_param(value, type_string)
    return json.dumps(serialise_native(native), separators=(",", ":")).encode("utf-8")


# The representative bucket-(a) CLEAN set — every coercer family. Each is
# ``(type_string, wire_value)`` where wire_value is the JSON-native inbound form.
_CLEAN_CASES = [
    # ── identity scalars ──
    ("int", 5), ("int", -42), ("Optional[int]", 7),
    ("float", 1.5), ("float", 3), ("number", 2.25),
    ("bool", True), ("bool", False),
    ("str", "hi"), ("str", 'a"b\\c'), ("Optional[str]", "x"),
    ("str", "café — π"),               # non-ASCII → ensure_ascii=True \uXXXX
    # ── identity containers (JSON-native passthrough) ──
    ("list", [1, 2, 3]), ("list[int]", [1, 2, 3]),
    ("list[list[int]]", [[1, 2], [3, 4]]),
    ("dict", {"a": 1, "b": [2, 3], "c": {"d": 4}}),
    ("Optional[dict]", {"k": "v"}),
    ("Sequence[str]", ["a", "b"]),
    ("iterable[int]", [9, 8]), ("sequence", [1, "x", True]),
    ("list[tuple[int, int]]", [[1, 2], [3, 4]]),
    # NOTE: `pathlib.Path` is NOT here — its coerce->serialise round-trip is
    # OS-dependent (str(WindowsPath) normalises '/'->'\\'), so it defers to pure
    # (see test_pathlib_path_defers_os_dependent below).
    # ── transforming: bytes ──
    ("bytes", _B64_HI), ("bytes", _B64_EMPTY), ("bytes", _B64_RAW),
    ("Sequence[bytes]", [_B64_HI, _B64_YA]),
    ("list[bytes]", [_B64_HI]),
    ("Mapping[bytes, bytes]", {_B64_HI: _B64_YA, _B64_YA: _B64_HI}),
    ("list[tuple[bytes, int]]", [[_B64_HI, 5], [_B64_YA, -3]]),
    ("list[tuple[bytes, bytes]]", [[_B64_HI, _B64_YA]]),
    # ── transforming: complex ──
    ("complex", [3, 4]), ("complex", 5), ("complex", [1.5, -2.5]),
    ("list[complex]", [[1, 2], 3, [0.5, 0.25]]),
    ("list[list[complex]]", [[[1, 2]], [[3, 4], [5, 6]]]),
    # ── tuple[int, int] ──
    ("tuple[int, int]", [3, 4]),
    # ── rc190 float carriers ──
    # "Mat" builds a real Mat (int/float leaves -> f64), so the roundtrip
    # promotes ints to floats ([[1,2]] -> [[1.0,2.0]]); "Vec" is IDENTITY
    # (coerce_param passes the flat list through, ints kept).
    ("Mat", [[1, 2], [3, 4]]),
    ("Mat", [[0.1, 0.2]]),
    ("Mat", [[1.5, 2.5], [3.0, 100.0]]),
    ("Vec", [1, 2, 3]),
    ("Vec", [0.1, 0.2, 0.3]),
]


@_needs_native
@pytest.mark.parametrize("type_string,value", _CLEAN_CASES)
def test_marshal_roundtrip_byte_identical_to_python(type_string, value) -> None:
    """C round-trip == pure Python coerce_param → serialise_native (byte-for-byte)."""
    expected = _py_roundtrip(value, type_string)
    status, out = _native.mcp_marshal_roundtrip_c(
        type_string, json.dumps(value).encode("utf-8"))
    assert status == _native.MARSHAL_OK, (type_string, value, status)
    assert out == expected, (type_string, value, out, expected)


@_needs_native
def test_uint32_accumulator_identity_passthrough() -> None:
    """The §50 holographic-bundle accumulator (``array('I')``) is a param-input-
    only family: coerce_param builds an ``array('I')`` the rc188 thunk will lower
    to a C uint32 buffer, so the FOUNDATION carrier form is the passthrough int
    list (serialise_native is not its inverse — it cannot emit an ``array``). The
    marshal is therefore IDENTITY over the wire list; ``None`` rides through."""
    for wire in (b"[1,2,3]", b"[]"):
        assert _native.mcp_marshal_roundtrip_c("array('I')", wire) == (
            _native.MARSHAL_OK, wire)
    assert _native.mcp_marshal_roundtrip_c("array('I')|None", b"[4,5]") == (
        _native.MARSHAL_OK, b"[4,5]")
    assert _native.mcp_marshal_roundtrip_c("array('I')|None", b"null") == (
        _native.MARSHAL_OK, b"null")


@_needs_native
def test_null_passes_through_for_any_type() -> None:
    """A JSON null rides through for ANY type (coerce_param's null-first rule)."""
    for t in ("Optional[int]", "bytes", "complex", "Mat", "dict"):
        status, out = _native.mcp_marshal_roundtrip_c(t, b"null")
        assert status == _native.MARSHAL_OK, t
        assert out == b"null", (t, out)


@_needs_native
def test_base64_codec_matches_python_exactly() -> None:
    """The C base64 decode→encode round-trip == Python base64 for varied lengths."""
    for n in range(0, 20):
        raw = bytes((i * 37 + 11) & 0xFF for i in range(n))
        wire = base64.b64encode(raw).decode("ascii")
        status, out = _native.mcp_marshal_roundtrip_c(
            "bytes", json.dumps(wire).encode("utf-8"))
        assert status == _native.MARSHAL_OK, n
        # round-trips to the SAME canonical base64 Python produces
        assert out == json.dumps(wire, separators=(",", ":")).encode("utf-8"), n


@_needs_native
def test_pathlib_path_defers_os_dependent() -> None:
    """`pathlib.Path` is DEFERRED (NOT_IMPL), not C-marshalled: its coerce ->
    serialise round-trip goes through an OS-aware Path object — Python's
    str(Path("a/b")) is "a/b" on POSIX but "a\\b" on Windows (WindowsPath
    normalises the separator). A portable C data-marshal cannot be byte-identical
    on every OS, so path normalisation is left to the OS-correct pure coerce_param
    (a bare-C host uses its own path convention). The C marshal returns NOT_IMPL
    regardless of the wire value shape."""
    for wire in (b'"some/path"', b'"a/b/c.txt"', b'"plain"'):
        status, out = _native.mcp_marshal_roundtrip_c("pathlib.Path", wire)
        assert status == _native.MARSHAL_NOT_IMPL, wire
        assert out is None
    # a null path still rides through (coerce_param's null-first rule)
    assert _native.mcp_marshal_roundtrip_c("pathlib.Path", b"null") == (
        _native.MARSHAL_OK, b"null")


@_needs_native
def test_non_bucket_a_types_defer_not_impl() -> None:
    """Still-unmarshalled carriers + by-ref handles + unknown types → NOT_IMPL
    (defer). rc190 now marshals ``Mat`` (real carrier) + ``Vec`` (identity), so
    they are NO LONGER here — see the ``Mat`` / ``Vec`` cases in ``_CLEAN_CASES``.
    ``HV`` (int/byte hypervector carrier) + ``np.ndarray`` (legacy) stay deferred."""
    for t in ("HV", "np.ndarray", "Sequence[np.ndarray]",
              "SpectralHandle", "operator_name", "totally.unknown.type"):
        status, out = _native.mcp_marshal_roundtrip_c(t, b"[[1,2]]")
        assert status == _native.MARSHAL_NOT_IMPL, t
        assert out is None


@_needs_native
def test_malformed_wire_values_bad_input() -> None:
    """A non-base64 bytes str / wrong-length base64 / non-str bytes / bad complex
    → BAD_INPUT (the pure coerce_param raises ValueError on the same inputs)."""
    bad = [
        ("bytes", b'"@@@@"'),          # '@' not in the alphabet
        ("bytes", b'"aGk"'),           # length not a multiple of 4
        ("bytes", b"5"),               # not a string
        ("complex", b"[1,2,3]"),       # not a 2-list
        ("complex", b'"x"'),           # not a number / pair
    ]
    for t, wire in bad:
        status, out = _native.mcp_marshal_roundtrip_c(t, wire)
        assert status == _native.MARSHAL_BAD_INPUT, (t, wire, status)
        assert out is None


@_needs_native
def test_roundtrip_two_pass_overflow_and_null_arg() -> None:
    """Direct-ctypes contract: a too-small out buffer → SRMECH_ERR_OVERFLOW;
    a NULL required pointer → SRMECH_ERR_NULL_ARG (never writes past the buffer)."""
    ts = b"bytes"
    val = json.dumps(_B64_RAW).encode("utf-8")
    ws = (ctypes.c_char * 4096)()
    ws_p = ctypes.cast(ws, ctypes.c_void_p)
    got = ctypes.c_size_t(0)

    tiny = (ctypes.c_char * 2)()
    rc = _native.LIB.srmech_mcp_marshal_roundtrip(
        ts, val, len(val), ws_p, 4096,
        ctypes.cast(tiny, ctypes.c_void_p), 2, ctypes.byref(got))
    assert rc == _native.SRMECH_ERR_OVERFLOW

    out = (ctypes.c_char * 256)()
    rc = _native.LIB.srmech_mcp_marshal_roundtrip(
        ts, val, len(val), ws_p, 4096,
        ctypes.cast(out, ctypes.c_void_p), 256, None)
    assert rc == _native.SRMECH_ERR_NULL_ARG


# ──────────────────────────────────────────────────────────────────────
# gate parity (always runs) — the helper degrades cleanly with no C peer
# ──────────────────────────────────────────────────────────────────────


def test_helper_degrades_without_native() -> None:
    """When the C peer is absent, the helper returns (-1, None) (pure fallback)."""
    if _native.has_native_mcp_marshal():
        status, out = _native.mcp_marshal_roundtrip_c("int", b"5")
        assert status == _native.MARSHAL_OK
        assert out == b"5"
    else:
        assert _native.mcp_marshal_roundtrip_c("int", b"5") == (-1, None)
