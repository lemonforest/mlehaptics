"""rc190 — the FLOAT-CARRIER marshal + dispatch (Mat/Vec c_dispatched tools RUN in C).

rc187 built the JSON-args↔typed-C-args marshal (bucket-(a): scalar/str/list/bytes/
complex); rc188/189 wired the invoke_tool DISPATCH SPINE for the clean int/bytes/
rational tools. rc190 widens BOTH to the real float carriers: the marshal now lowers
a ``Mat`` param to a real ``srmech_mval_t`` MAT carrier (int/float leaves → f64, the
exact ``coerce_param → Mat.from_rows(is_complex=False)`` shape) and a ``Vec`` param
IDENTITY (the flat-list passthrough ``coerce_param`` does), and the invoke vtable
dispatches the dense-kernel Mat/Vec ops:

    (Mat, Mat) -> Mat   laplacian.mat_matmul   (rides srmech_dense_matmul_complex)
    (Mat, Vec) -> Vec   laplacian.mat_matvec   (rides the same kernel, k×1 column)
    (Vec, Vec) -> Mat   laplacian.mat_outer    (a lone IEEE multiply per element)

THE PARITY PROOF (the DoD). For each, the C ``_native.invoke_tool_c(name, args)``
result text == the pure ``serialise_result(invoke_tool(name, args))`` BYTE-for-byte
(json.dumps DEFAULT-separator form). This hinges on the new ``srmech_double_repr`` —
the SHORTEST round-trip decimal (CPython repr(float)/json.dumps), verified below on
adversarial doubles. A complex-via-JSON operand / empty / dim-mismatch / giant shape
DEFERS ((False, None)); the pure path is the complete fallback (never a wrong answer).

The native-requiring assertions ``skipif`` cleanly when the C peer is absent (pure /
numpy-absent / stale-lib host). numpy-free (stdlib json + the srmech.mcp pure SSoT)."""
from __future__ import annotations

import ctypes
import json
import math
import random
import struct

import pytest

from srmech.amsc import _native
from srmech.mcp._server import MCPServer, build_attestation
from srmech.mcp._tools import invoke_tool, serialise_result

_needs_native = pytest.mark.skipif(
    not _native.has_native_invoke(),
    reason="rc190 invoke float-carrier C peer not loaded (pure / stale host)",
)


# ──────────────────────────────────────────────────────────────────────
# srmech_double_repr — the shortest-round-trip float formatter keystone.
# ──────────────────────────────────────────────────────────────────────


def _double_repr_c(v: float) -> "str | None":
    """Call the C ``srmech_double_repr`` directly (ctypes), or ``None`` if the C
    reported a non-finite input (BAD_INPUT). Bound locally (the helper is not a
    Python-facing _native symbol — the marshal/serialise use it internally)."""
    lib = _native.LIB
    fn = lib.srmech_double_repr
    fn.argtypes = [ctypes.c_double, ctypes.c_void_p, ctypes.c_size_t,
                   ctypes.POINTER(ctypes.c_size_t)]
    fn.restype = ctypes.c_int
    buf = ctypes.create_string_buffer(40)
    n = ctypes.c_size_t(0)
    rc = fn(ctypes.c_double(v), ctypes.cast(buf, ctypes.c_void_p), 40,
            ctypes.byref(n))
    if rc != _native.SRMECH_OK:
        return None
    return buf.raw[:n.value].decode("ascii")


_ADVERSARIAL = [
    0.0, -0.0, 1.0, 5.0, -5.0, 0.1, 0.2, 0.3, 1.0 / 3.0, 2.0 / 3.0,
    100.0, 120.0, 15.0, 10.0, 1234567.0, 1000000000000000.0,
    1e15, 1e16, 1e17, 1e-4, 1e-5, 1e-6, 1e100, 1e-100, 1e-300,
    2.2250738585072014e-308, 4.9e-324, 1.7976931348623157e308,
    123.456, -0.001, 3.141592653589793, 2.718281828459045,
    1.5, -2.5, 0.5, 0.25, 6.022e23, 255.0, 256.0, 0.30000000000000004,
    12345678901234567.0, 0.0001, 0.00001, -1e-7,
]


@_needs_native
@pytest.mark.parametrize("v", _ADVERSARIAL)
def test_double_repr_matches_python_repr(v) -> None:
    """srmech_double_repr(v) == repr(v) == json.dumps(v) for finite doubles —
    the shortest round-trip decimal (the `%g` loop would mis-render 100.0 → the
    `%e` + decpt algorithm is the CPython one)."""
    got = _double_repr_c(v)
    assert got == repr(v) == json.dumps(v), (v, got)


@_needs_native
def test_double_repr_random_bits() -> None:
    """srmech_double_repr == repr over a wide sweep of random finite doubles
    (scale-spread + raw bit patterns) — the byte-identity guarantee the Mat/Vec
    float serialisation rests on."""
    rng = random.Random(20260709)
    n = 0
    for _ in range(4000):
        if n % 2 == 0:
            v = rng.choice([1, -1]) * rng.random() * (10.0 ** rng.randint(-300, 300))
        else:
            v = struct.unpack("<d", struct.pack("<Q", rng.getrandbits(64)))[0]
        n += 1
        if math.isinf(v) or math.isnan(v):
            continue
        assert _double_repr_c(v) == repr(v), (struct.pack("<d", v).hex(), repr(v))


@_needs_native
def test_double_repr_non_finite_defers() -> None:
    """NaN / ±Inf → the C reports BAD_INPUT (the caller defers; they never arise
    in the exact tools). float('inf')/nan cannot ride JSON anyway."""
    assert _double_repr_c(float("nan")) is None
    assert _double_repr_c(float("inf")) is None
    assert _double_repr_c(float("-inf")) is None


# ──────────────────────────────────────────────────────────────────────
# The float-carrier dispatch batch — native == pure, byte-for-byte.
# ──────────────────────────────────────────────────────────────────────

_BATCH_CASES = [
    # (Mat, Mat) -> Mat
    ("srmech.amsc.laplacian.mat_matmul", {"a": [[1, 2], [3, 4]], "b": [[5, 6], [7, 8]]}),
    ("srmech.amsc.laplacian.mat_matmul", {"a": [[1]], "b": [[1]]}),
    ("srmech.amsc.laplacian.mat_matmul",
     {"a": [[0.1, 0.2], [0.3, 0.4]], "b": [[1.5], [2.5]]}),
    ("srmech.amsc.laplacian.mat_matmul", {"a": [[2, 0, 1]], "b": [[1], [2], [3]]}),
    # (Mat, Vec) -> Vec
    ("srmech.amsc.laplacian.mat_matvec", {"m": [[1, 2, 3], [4, 5, 6]], "v": [7, 8, 9]}),
    ("srmech.amsc.laplacian.mat_matvec", {"m": [[0.1, 0.2]], "v": [0.3, 0.7]}),
    # (Vec, Vec) -> Mat
    ("srmech.amsc.laplacian.mat_outer", {"a": [1, 2, 3], "b": [4, 5]}),
    ("srmech.amsc.laplacian.mat_outer", {"a": [0.5, -0.25], "b": [2.0, 3.0, 0.1]}),
]

_BATCH_TOOLS = sorted({name for name, _ in _BATCH_CASES})


@_needs_native
@pytest.mark.parametrize("name,args", _BATCH_CASES)
def test_native_invoke_matches_pure(name, args) -> None:
    """The C invoke_tool_c result text == the pure serialise_result(invoke_tool)."""
    dispatched, text = _native.invoke_tool_c(name, args)
    assert dispatched is True, (name, args)
    assert text == serialise_result(invoke_tool(name, args)), (name, args)


@_needs_native
def test_batch_dispatches_three_float_carrier_tools() -> None:
    """The rc190 batch dispatches the 3 dense-kernel Mat/Vec tools in C."""
    assert _BATCH_TOOLS == [
        "srmech.amsc.laplacian.mat_matmul",
        "srmech.amsc.laplacian.mat_matvec",
        "srmech.amsc.laplacian.mat_outer",
    ]


@_needs_native
def test_native_invoke_matches_pure_random() -> None:
    """A random sweep of REAL matmul / matvec / outer — byte-identical to pure
    (messy floats that do NOT round-trip cleanly under %.17g are the point)."""
    rng = random.Random(4242)
    for _ in range(150):
        m, k, n = (rng.randint(1, 5) for _ in range(3))
        A = [[rng.uniform(-4, 4) for _ in range(k)] for _ in range(m)]
        B = [[rng.uniform(-4, 4) for _ in range(n)] for _ in range(k)]
        args = {"a": A, "b": B}
        disp, text = _native.invoke_tool_c("srmech.amsc.laplacian.mat_matmul", args)
        assert disp and text == serialise_result(
            invoke_tool("srmech.amsc.laplacian.mat_matmul", args)), args
        Mm = [[rng.uniform(-4, 4) for _ in range(k)] for _ in range(m)]
        v = [rng.uniform(-4, 4) for _ in range(k)]
        args = {"m": Mm, "v": v}
        disp, text = _native.invoke_tool_c("srmech.amsc.laplacian.mat_matvec", args)
        assert disp and text == serialise_result(
            invoke_tool("srmech.amsc.laplacian.mat_matvec", args)), args
        a = [rng.uniform(-4, 4) for _ in range(rng.randint(1, 6))]
        b = [rng.uniform(-4, 4) for _ in range(rng.randint(1, 6))]
        args = {"a": a, "b": b}
        disp, text = _native.invoke_tool_c("srmech.amsc.laplacian.mat_outer", args)
        assert disp and text == serialise_result(
            invoke_tool("srmech.amsc.laplacian.mat_outer", args)), args


# ──────────────────────────────────────────────────────────────────────
# DEFER cases — the pure path is the complete fallback (never a wrong answer).
# ──────────────────────────────────────────────────────────────────────

_DEFER_CASES = [
    # dim / shape mismatch → pure raises the ValueError
    ("srmech.amsc.laplacian.mat_matmul", {"a": [[1, 2]], "b": [[1, 2]]}),
    ("srmech.amsc.laplacian.mat_matvec", {"m": [[1, 2]], "v": [1, 2, 3]}),
    # empty operand → pure
    ("srmech.amsc.laplacian.mat_matmul", {"a": [[1]], "b": [[]]}),
    ("srmech.amsc.laplacian.mat_outer", {"a": [], "b": [1]}),
    # complex-via-JSON ([re,im] leaf) → the pure complex path
    ("srmech.amsc.laplacian.mat_matmul", {"a": [[[1, 2]]], "b": [[1]]}),
    ("srmech.amsc.laplacian.mat_outer", {"a": [[1, 2]], "b": [1]}),
    # a Mat carrier tool with NO C thunk this rc → defer
    ("srmech.amsc.laplacian.mat_eigvals", {"a": [[1, 0], [0, 2]]}),
    ("srmech.amsc.laplacian.mat_svd", {"a": [[1, 0], [0, 1]]}),
    # a "Mat | Vec" param is not marshalled this rc → defer
    ("srmech.amsc.laplacian.dense_solve",
     {"A": [[2, 0], [0, 2]], "B": [2, 4], "exact": False}),
]


@_needs_native
@pytest.mark.parametrize("name,args", _DEFER_CASES)
def test_native_defers_cleanly(name, args) -> None:
    """A float-carrier call the C spine cannot cleanly dispatch → (False, None)."""
    assert _native.invoke_tool_c(name, args) == (False, None), (name, args)


@_needs_native
@pytest.mark.parametrize("name,args", _BATCH_CASES + _DEFER_CASES)
def test_server_tools_call_native_equals_pure(name, args) -> None:
    """Through the MCP server, tools/call is native==pure: content text + the MPR
    attestation are identical whether the C spine ran the tool or the pure path did."""

    class _PureServer(MCPServer):
        def _native_call_text(self, name_, arguments_):  # force the pure path
            return None

    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": name, "arguments": args}}
    native = MCPServer().handle(dict(req))["result"]
    pure = _PureServer().handle(dict(req))["result"]
    assert native["content"] == pure["content"], (name, args)
    assert native["isError"] == pure["isError"], (name, args)
    text = native["content"][0]["text"]
    att = native["attestation"]
    assert att == build_attestation(
        tool_name=name, result_text=text, retrieved_at=att["retrieved_at"])


def test_helper_degrades_without_native() -> None:
    """With the C peer absent, invoke_tool_c returns (False, None) (pure fallback);
    present, mat_matmul dispatches the [[1.0]] identity product in C."""
    if _native.has_native_invoke():
        assert _native.invoke_tool_c(
            "srmech.amsc.laplacian.mat_matmul", {"a": [[1]], "b": [[1]]}) == (
            True, "[[1.0]]")
    else:
        assert _native.invoke_tool_c(
            "srmech.amsc.laplacian.mat_matmul", {"a": [[1]], "b": [[1]]}) == (
            False, None)
