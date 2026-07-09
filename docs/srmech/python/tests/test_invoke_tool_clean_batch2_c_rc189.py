"""rc189 — CLEAN BATCH 2: the invoke_tool dispatch-spine thunk vtable WIDENED.

rc188 shipped ``srmech_invoke_tool`` with 20 batch-1 c_dispatched tools across 7
signature shapes. rc189 widens the SAME vtable (no new spine, no ledger move —
``invoke_tool`` is already ``composes_c``) with 12 MORE bucket-(a) clean tools in
new signature shapes, each still byte-identical to the pure path and each still
DEFERRING (never a wrong answer) on an out-of-domain / overflow / raise input:

  (int,int)->list[int]                  rational.continued_fraction
  list[int]->list[(int,int)]            rational.continued_fraction_convergents
  (pair,pair)->pair                     rational.rational_{add,mul,div}
  (pair,int)->pair                      rational.rational_pow_uint
  (int,int,int)->int                    primes.cyclic_period
  Sequence[bytes]->bytes                hdc.bundle
  list[bytes]->list[str]                format.sha256_batch
  (bytes,list[(bytes,int)])->(bool,int) dispatch.match
  (bytes,list[(bytes,bytes)])->bytes|null   naming.lookup
  (bytes,Mapping[bytes,bytes])->bytes   template.render

THE PARITY PROOF (the DoD). For every batch-2 tool the C
``_native.invoke_tool_c(name, args)`` result text == the pure
``serialise_result(invoke_tool(name, args))`` (byte-for-byte, json.dumps DEFAULT-
separator form). An out-of-domain input (a value the Python wrapper would raise
on, an intermediate exceeding int64 → the bignum path, an even bundle count, an
unknown template key) DEFERS ((False, None)); the pure path runs + attests, so
the MCP server ``tools/call`` response is structurally identical either way.

The native-requiring assertions ``skipif`` cleanly when the C peer is absent
(pure / numpy-absent / stale-lib host). numpy-free (stdlib json/base64)."""
from __future__ import annotations

import base64

import pytest

from srmech.amsc import _native
from srmech.mcp._server import MCPServer, build_attestation
from srmech.mcp._tools import invoke_tool, serialise_result

_needs_native = pytest.mark.skipif(
    not _native.has_native_invoke(),
    reason="rc188/rc189 invoke_tool dispatch-spine C peer not loaded (pure / stale host)",
)


def _b64(bs: bytes) -> str:
    return base64.b64encode(bs).decode("ascii")


# The clean batch-2 set — every new signature shape. Each is ``(name, arguments)``
# with a representative valid argument object; the pure serialise_result is the
# byte-for-byte reference.
_BATCH2_CASES = [
    # (pair, pair) -> pair
    ("srmech.amsc.rational.rational_add", {"a": [1, 2], "b": [1, 3]}),
    ("srmech.amsc.rational.rational_add", {"a": [-1, 2], "b": [1, 2]}),   # -> [0, 1]
    ("srmech.amsc.rational.rational_mul", {"a": [2, 3], "b": [3, 4]}),
    ("srmech.amsc.rational.rational_div", {"a": [1, 2], "b": [3, 4]}),
    # (pair, int) -> pair
    ("srmech.amsc.rational.rational_pow_uint", {"base": [2, 3], "exp": 4}),
    ("srmech.amsc.rational.rational_pow_uint", {"base": [-2, 3], "exp": 3}),
    # (int, int) -> list[int]
    ("srmech.amsc.rational.continued_fraction",
     {"numerator": 415, "denominator": 93}),
    ("srmech.amsc.rational.continued_fraction",
     {"numerator": 0, "denominator": 5}),               # -> [0]
    # list[int] -> list[(int, int)]
    ("srmech.amsc.rational.continued_fraction_convergents",
     {"coef_list": [3, 7, 15, 1, 292]}),
    ("srmech.amsc.rational.continued_fraction_convergents",
     {"coef_list": [-3, 7]}),                            # negative a_0 is allowed
    # (int, int, int) -> int
    ("srmech.amsc.primes.cyclic_period", {"a": 2, "n": 7, "max_k": 100}),
    ("srmech.amsc.primes.cyclic_period", {"a": 3, "n": 7}),   # max_k default = n
    # Sequence[bytes] -> bytes
    ("srmech.amsc.hdc.bundle",
     {"vectors": [_b64(bytes([1, 2, 3])), _b64(bytes([1, 3, 3])), _b64(bytes([7, 2, 3]))]}),
    ("srmech.amsc.hdc.bundle", {"vectors": [_b64(bytes([9, 9]))]}),  # single vector (odd)
    # list[bytes] -> list[str]
    ("srmech.amsc.format.sha256_batch", {"datas": [_b64(b"abc"), _b64(b"")]}),
    ("srmech.amsc.format.sha256_batch", {"datas": []}),               # -> []
    # (bytes, list[(bytes, int)]) -> (bool, int)
    ("srmech.amsc.dispatch.match",
     {"input_bytes": _b64(b"hello world"), "rules": [[_b64(b"xyz"), 7], [_b64(b"wor"), 9]]}),
    ("srmech.amsc.dispatch.match",
     {"input_bytes": _b64(b"abc"), "rules": [[_b64(b"zzz"), 1]]}),     # no match -> [false, 0]
    ("srmech.amsc.dispatch.match",
     {"input_bytes": _b64(b"abc"), "rules": []}),                      # empty rules -> [false, 0]
    # (bytes, list[(bytes, bytes)]) -> bytes | null
    ("srmech.amsc.naming.lookup",
     {"key": _b64(b"k2"), "pairs": [[_b64(b"k1"), _b64(b"v1")], [_b64(b"k2"), _b64(b"v2")]]}),
    ("srmech.amsc.naming.lookup",
     {"key": _b64(b"zz"), "pairs": [[_b64(b"k1"), _b64(b"v1")]]}),     # miss -> null
    # (bytes, Mapping[bytes, bytes]) -> bytes
    ("srmech.amsc.template.render",
     {"template_bytes": _b64(b"hi {name}!"), "mapping": {_b64(b"name"): _b64(b"bob")}}),
    ("srmech.amsc.template.render",
     {"template_bytes": _b64(b"{b}{a}"),
      "mapping": {_b64(b"a"): _b64(b"1"), _b64(b"b"): _b64(b"2")}}),   # unsorted keys -> sorted pack
    ("srmech.amsc.template.render",
     {"template_bytes": _b64(b"plain, no braces"), "mapping": {}}),    # empty mapping -> verbatim
]

# The distinct tool NAMES batch-2 dispatches in C (the discharge evidence).
_BATCH2_TOOLS = sorted({name for name, _ in _BATCH2_CASES})


@_needs_native
@pytest.mark.parametrize("name,args", _BATCH2_CASES)
def test_native_invoke_matches_pure(name, args) -> None:
    """The C invoke_tool_c result text == the pure serialise_result(invoke_tool)."""
    dispatched, text = _native.invoke_tool_c(name, args)
    assert dispatched is True, (name, args)
    assert text == serialise_result(invoke_tool(name, args)), (name, args)


@_needs_native
def test_batch2_covers_twelve_distinct_tools() -> None:
    """The clean batch-2 dispatches 12 distinct c_dispatched tools in C (the
    additional discharge evidence widening the invoke_tool composes_c surface)."""
    assert len(_BATCH2_TOOLS) == 12, _BATCH2_TOOLS
    for name in _BATCH2_TOOLS:
        assert name.startswith("srmech."), name


# Cases the C spine must DEFER (return (False, None)) — the pure path is the
# complete fallback. Each replicates a place the Python wrapper raises OR uses
# the bignum path OR returns a value the int64 carrier can't hold.
_DEFER_CASES = [
    ("srmech.amsc.rational.rational_add", {"a": [1, 0], "b": [1, 3]}),    # den<=0 -> ValueError
    ("srmech.amsc.rational.rational_div", {"a": [1, 2], "b": [0, 4]}),    # /0 rational
    ("srmech.amsc.rational.rational_add",
     {"a": [(1 << 62), 1], "b": [(1 << 62), 1]}),                        # overflow -> bignum
    ("srmech.amsc.rational.rational_mul",
     {"a": [(1 << 62), 1], "b": [(1 << 62), 1]}),                        # overflow -> bignum
    ("srmech.amsc.rational.rational_pow_uint", {"base": [2, 3], "exp": 0}),    # ->(1,1) pure
    ("srmech.amsc.rational.rational_pow_uint", {"base": [2, 3], "exp": 100}),  # >64 -> bignum
    ("srmech.amsc.rational.rational_pow_uint", {"base": [2, 3], "exp": -1}),   # <0 -> ValueError
    ("srmech.amsc.rational.continued_fraction", {"numerator": 5, "denominator": 0}),  # ValueError
    ("srmech.amsc.rational.continued_fraction_convergents", {"coef_list": []}),        # ValueError
    ("srmech.amsc.rational.continued_fraction_convergents", {"coef_list": [3, -1]}),   # a_k<=0
    ("srmech.amsc.primes.cyclic_period", {"a": 2, "n": 1}),              # n<2 -> ValueError
    ("srmech.amsc.primes.cyclic_period", {"a": 2, "n": 4}),              # gcd!=1 -> ValueError
    ("srmech.amsc.primes.cyclic_period", {"a": 2, "n": 7, "max_k": 1}),  # period>max_k -> Overflow
    ("srmech.amsc.hdc.bundle", {"vectors": [_b64(b"ab"), _b64(b"cd")]}), # even count -> ValueError
    ("srmech.amsc.hdc.bundle",
     {"vectors": [_b64(b"ab"), _b64(b"c"), _b64(b"de")]}),               # len mismatch -> ValueError
    ("srmech.amsc.dispatch.match",
     {"input_bytes": _b64(b"x"), "rules": [[_b64(b"x"), (1 << 40)]]}),   # tag > u32 -> defer
    ("srmech.amsc.template.render",
     {"template_bytes": _b64(b"{zzz}"), "mapping": {_b64(b"name"): _b64(b"bob")}}),  # unknown key
    ("srmech.amsc.template.render",
     {"template_bytes": _b64(b"{x}"), "mapping": {}}),                  # empty map + placeholder -> unknown key
    # shared-surface misses (mirroring rc188's contract)
    ("no.such.tool", {"x": 1}),                                          # unregistered
    ("srmech.amsc.rational.rational_add", {"a": [1, 2], "b": [1, 3], "z": 1}),  # extra arg
    ("srmech.amsc.rational.rational_add", {"a": [1, 2]}),                # missing required arg
]


@_needs_native
@pytest.mark.parametrize("name,args", _DEFER_CASES)
def test_native_defers_cleanly(name, args) -> None:
    """A tool the C spine cannot cleanly dispatch -> (False, None); defer to pure."""
    assert _native.invoke_tool_c(name, args) == (False, None), (name, args)


@_needs_native
@pytest.mark.parametrize("name,args", _BATCH2_CASES + _DEFER_CASES)
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
    text = native["content"][0]["text"]
    att = native["attestation"]
    assert att == build_attestation(
        tool_name=name, result_text=text, retrieved_at=att["retrieved_at"])


def test_helper_degrades_without_native() -> None:
    """With the C peer present, a batch-2 tool dispatches; absent, it defers."""
    if _native.has_native_invoke():
        assert _native.invoke_tool_c(
            "srmech.amsc.rational.continued_fraction",
            {"numerator": 7, "denominator": 3}) == (True, "[2, 3]")
    else:
        assert _native.invoke_tool_c(
            "srmech.amsc.rational.continued_fraction",
            {"numerator": 7, "denominator": 3}) == (False, None)
