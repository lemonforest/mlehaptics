"""rc188 — the MCP tools/call DISPATCH SPINE (invoke_tool makes tools/call RUN in C).

The rc184 registry + rc187 arg-marshalling foundation now dispatch: ``srmech_invoke_tool``
resolves a dotted tool name, marshals each argument to a typed C value, runs a
SIGNATURE-SHAPE-batched thunk table (tool name → the bespoke C kernel), and serialises
the result — for a CLEAN BATCH of c_dispatched tools whose result text is byte-identical
to the pure ``serialise_result(invoke_tool(name, args))``.

THE PARITY PROOF (the DoD). For every batch-1 tool, the C
``_native.invoke_tool_c(name, args)`` result text == the pure Python
``serialise_result(invoke_tool(name, args))`` (BYTE-for-byte, json.dumps DEFAULT-
separator form). A tool with no single C kernel, an EXTRA / MALFORMED argument, an
unregistered name, or an out-of-domain input DEFERS ((False, None)); the pure path
runs + attests. Through the MCP server, a batch tool's ``tools/call`` response
(content text + MPR attestation) is structurally identical whether the result is
computed in C or in pure Python. The bare-C ``srmech_mcp_handle`` routes tools/call
to the CALL_RESULT signal (batch) / DEFER_CALL (the rest).

The native-requiring assertions ``skipif`` cleanly when the rc188 C peer is absent
(pure / numpy-absent / stale-lib host). numpy-free (stdlib json/base64 + the
srmech.mcp pure SSoT)."""
from __future__ import annotations

import base64
import ctypes
import json

import pytest

from srmech.amsc import _native
from srmech.mcp._server import MCPServer, build_attestation
from srmech.mcp._tools import invoke_tool, serialise_result

_needs_native = pytest.mark.skipif(
    not _native.has_native_invoke(),
    reason="rc188 invoke_tool dispatch-spine C peer not loaded (pure / stale host)",
)


def _b64(bs: bytes) -> str:
    return base64.b64encode(bs).decode("ascii")


# The clean batch-1 set — every signature shape. Each is ``(name, arguments)`` with
# a representative valid argument object. The pure serialise_result(invoke_tool(...))
# is the reference the C result text must match byte-for-byte.
_BATCH_CASES = [
    # uN -> u  (int result)
    ("srmech.amsc.cyclic.gcd", {"a": 48, "b": 36}),
    ("srmech.amsc.cyclic.gcd", {"a": 0, "b": 0}),
    ("srmech.amsc.cyclic.lcm", {"a": 4, "b": 6}),
    ("srmech.amsc.cyclic.mod_add", {"a": 5, "b": 7, "n": 9}),
    ("srmech.amsc.cyclic.mod_mul", {"a": 5, "b": 7, "n": 9}),
    ("srmech.amsc.cyclic.mod_pow", {"a": 3, "k": 4, "n": 7}),
    ("srmech.amsc.cyclic.mod_inv", {"a": 3, "n": 7}),
    ("srmech.amsc.cyclic.three_cycle", {"value": 5}),
    ("srmech.amsc.cascade.cyclic_gcd", {"a": 24, "b": 36}),
    ("srmech.amsc.primes.next_prime", {"n": 100}),
    # u -> bool
    ("srmech.amsc.primes.is_prime", {"n": 97}),
    ("srmech.amsc.primes.is_prime", {"n": 100}),
    # uN -> (int, int) pair  (container result, DEFAULT separators)
    ("srmech.amsc.rational.best_rational",
     {"numerator": 22, "denominator": 7, "max_denominator": 100}),
    ("srmech.amsc.rational.best_rational",
     {"numerator": 355, "denominator": 113, "max_denominator": 50}),
    # u -> list[(int, int)]  (container result)
    ("srmech.amsc.primes.factor", {"n": 360}),
    ("srmech.amsc.primes.factor", {"n": 1}),
    ("srmech.amsc.primes.factor", {"n": 97}),
    # bytes -> hex str
    ("srmech.amsc.format.sha256_bytes", {"data": _b64(b"abc")}),
    ("srmech.amsc.format.sha256_bytes", {"data": _b64(b"")}),
    # ... -> bytes  (base64 string result)
    ("srmech.amsc.tlv.tlv_pack", {"tag": 7, "value": _b64(b"hello")}),
    ("srmech.amsc.tlv.tlv_pack", {"tag": 0, "value": _b64(b"")}),
    ("srmech.amsc.hdc.bind",
     {"a": _b64(bytes([1, 2, 3])), "b": _b64(bytes([4, 5, 6]))}),
    ("srmech.amsc.hdc.permute", {"a": _b64(bytes([1, 2, 3, 4])), "rotate_bits": 3}),
    ("srmech.amsc.dispatch.mirror_pattern", {"pattern": _b64(bytes([1, 2, 3]))}),
    # bytes, bytes -> int | null
    ("srmech.amsc.hdc.hamming", {"a": _b64(bytes([0, 1])), "b": _b64(bytes([0, 3]))}),
    ("srmech.amsc.search.byte_search",
     {"haystack": _b64(b"abcabc"), "needle": _b64(b"b")}),
    ("srmech.amsc.search.byte_search",
     {"haystack": _b64(b"abc"), "needle": _b64(b"xyz")}),          # miss -> null
    ("srmech.amsc.search.byte_search",
     {"haystack": _b64(b"abc"), "needle": _b64(b"")}),             # empty needle -> 0
    ("srmech.amsc.search.byte_search_backward",
     {"haystack": _b64(b"abcabc"), "needle": _b64(b"b")}),
    ("srmech.amsc.search.byte_search_backward",
     {"haystack": _b64(b"abc"), "needle": _b64(b"z")}),            # miss -> null
]

# The distinct tool NAMES the batch dispatches in C (the discharge evidence).
_BATCH_TOOLS = sorted({name for name, _ in _BATCH_CASES})


@_needs_native
@pytest.mark.parametrize("name,args", _BATCH_CASES)
def test_native_invoke_matches_pure(name, args) -> None:
    """The C invoke_tool_c result text == the pure serialise_result(invoke_tool)."""
    dispatched, text = _native.invoke_tool_c(name, args)
    assert dispatched is True, (name, args)
    assert text == serialise_result(invoke_tool(name, args)), (name, args)


@_needs_native
def test_batch_covers_twenty_distinct_tools() -> None:
    """The clean batch dispatches ≥ 20 distinct c_dispatched tools in C (the
    substantive-batch evidence for the invoke_tool discharge → composes_c)."""
    assert len(_BATCH_TOOLS) >= 20, _BATCH_TOOLS
    for name in _BATCH_TOOLS:
        # each is registered + resolves + dispatched in the parametrised set
        assert name.startswith("srmech."), name


# Cases the C spine must DEFER (return (False, None)) — the pure path is the
# complete fallback (never a wrong answer). Each pairs with the pure behaviour.
_DEFER_CASES = [
    ("srmech.qm.bell.tsirelson_bound", {}),                  # float, no C kernel
    ("srmech.amsc.laplacian.mat_matmul", {"a": [[1]], "b": [[1]]}),  # Mat carrier
    ("no.such.tool", {"x": 1}),                              # unregistered
    ("srmech.amsc.cyclic.gcd", {"a": 12, "b": 8, "z": 1}),   # extra arg
    ("srmech.amsc.cyclic.gcd", {"a": 12}),                   # missing required arg
    ("srmech.amsc.cyclic.gcd", {"a": -1, "b": 8}),           # negative -> pure raises
    ("srmech.amsc.cyclic.mod_add", {"a": 5, "b": 7, "n": 0}),  # n==0 -> pure raises
    ("srmech.amsc.format.sha256_bytes", {"data": "@@@@"}),   # bad base64
    ("srmech.amsc.hdc.bind", {"a": _b64(b"ab"), "b": _b64(b"abc")}),  # len mismatch
]


@_needs_native
@pytest.mark.parametrize("name,args", _DEFER_CASES)
def test_native_defers_cleanly(name, args) -> None:
    """A tool the C spine cannot cleanly dispatch → (False, None) — defer to pure."""
    assert _native.invoke_tool_c(name, args) == (False, None), (name, args)


@_needs_native
@pytest.mark.parametrize("name,args", _BATCH_CASES + _DEFER_CASES)
def test_server_tools_call_native_equals_pure(name, args) -> None:
    """Through the MCP server, tools/call is native==pure: the content TEXT and the
    MPR attestation are structurally identical whether the C spine ran the tool or
    the pure invoke_tool did. A forced-pure server is the oracle."""

    class _PureServer(MCPServer):
        def _native_call_text(self, name_, arguments_):  # force the pure path
            return None

    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": name, "arguments": args}}
    native = MCPServer().handle(dict(req))["result"]
    pure = _PureServer().handle(dict(req))["result"]
    assert native["content"] == pure["content"], (name, args)
    assert native["isError"] == pure["isError"], (name, args)
    # the attestation over the native text (with its own timestamp) recomputes
    text = native["content"][0]["text"]
    att = native["attestation"]
    assert att == build_attestation(
        tool_name=name, result_text=text, retrieved_at=att["retrieved_at"])


@_needs_native
def test_mcp_handle_call_result_and_defer() -> None:
    """The bare-C srmech_mcp_handle routes tools/call → CALL_RESULT (a batch tool;
    buf = the result text the caller wraps) / DEFER_CALL (a non-batch tool)."""
    req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                      "params": {"name": "srmech.amsc.cyclic.gcd",
                                 "arguments": {"a": 48, "b": 36}}}).encode("utf-8")
    kind, text = _native.mcp_handle_c(req)
    assert kind == _native.MCP_KIND_CALL_RESULT
    assert text == b"12"
    # a container-result batch tool
    req_f = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "srmech.amsc.primes.factor",
                                   "arguments": {"n": 360}}}).encode("utf-8")
    kind_f, text_f = _native.mcp_handle_c(req_f)
    assert kind_f == _native.MCP_KIND_CALL_RESULT
    assert text_f == b"[[2, 3], [3, 2], [5, 1]]"
    # a non-batch tool -> DEFER_CALL (the Python host runs pure invoke_tool)
    req_d = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                        "params": {"name": "srmech.qm.bell.tsirelson_bound",
                                   "arguments": {}}}).encode("utf-8")
    assert _native.mcp_handle_c(req_d) == (_native.MCP_KIND_DEFER_CALL, None)


@_needs_native
def test_null_arg_graceful() -> None:
    """Direct-ctypes contract: a NULL required pointer → SRMECH_ERR_NULL_ARG (no
    abort, asserts-live); a too-small buffer → the caller-sized OVERFLOW."""
    ws_len = int(_native.LIB.srmech_invoke_tool_arena_bytes(64))
    ws = (ctypes.c_char * ws_len)()
    ws_p = ctypes.cast(ws, ctypes.c_void_p)
    out = (ctypes.c_char * 256)()
    out_p = ctypes.cast(out, ctypes.c_void_p)
    got = ctypes.c_size_t(0)
    kind = ctypes.c_int(-1)
    args = b'{"a":1,"b":2}'

    # NULL name / out_len / out_kind -> NULL_ARG (never aborts on an assert)
    assert _native.LIB.srmech_invoke_tool(
        None, args, len(args), ws_p, 4096, out_p, 256,
        ctypes.byref(got), ctypes.byref(kind)) == _native.SRMECH_ERR_NULL_ARG
    assert _native.LIB.srmech_invoke_tool(
        b"srmech.amsc.cyclic.gcd", args, len(args), ws_p, 4096, out_p, 256,
        None, ctypes.byref(kind)) == _native.SRMECH_ERR_NULL_ARG
    assert _native.LIB.srmech_invoke_tool(
        b"srmech.amsc.cyclic.gcd", args, len(args), ws_p, 4096, out_p, 256,
        ctypes.byref(got), None) == _native.SRMECH_ERR_NULL_ARG

    # a too-small out buffer for a DISPATCHED result -> OVERFLOW (no over-write).
    # The arena is sized to dispatch (sha256's 64-hex result), so serialisation
    # into the 1-byte buf is where the bound bites.
    tiny = (ctypes.c_char * 1)()
    rc = _native.LIB.srmech_invoke_tool(
        b"srmech.amsc.format.sha256_bytes", b'{"data":"YWJj"}', 15,
        ws_p, ws_len, ctypes.cast(tiny, ctypes.c_void_p), 1,
        ctypes.byref(got), ctypes.byref(kind))
    assert rc == _native.SRMECH_ERR_OVERFLOW


def test_helper_degrades_without_native() -> None:
    """With the C peer absent, invoke_tool_c returns (False, None) (pure fallback)."""
    if _native.has_native_invoke():
        assert _native.invoke_tool_c(
            "srmech.amsc.cyclic.gcd", {"a": 6, "b": 4}) == (True, "2")
    else:
        assert _native.invoke_tool_c(
            "srmech.amsc.cyclic.gcd", {"a": 6, "b": 4}) == (False, None)
