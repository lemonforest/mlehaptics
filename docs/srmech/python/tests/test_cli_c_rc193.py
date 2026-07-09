"""rc193 — the CLI arg-GRAMMAR + dispatch in C (a bare-C host parses + routes the
``srmech`` console-script grammar).

``srmech_cli_parse`` reproduces the WHOLE build_parser + five add_arguments grammar
(status / bus / dsl / mcp / class, each subcommand's flags / positionals / choices /
defaults) and emits the parsed argparse namespace as canonical JSON; ``srmech_cli_dispatch``
routes the parsed command to its run body. ``srmech.cli.main.main`` runs argv through
both on the clean RUN path (hasattr-guarded), deferring help / version / errors +
anything the bounded parser declines to pure argparse (byte-identical).

THE PARITY PROOFS (the DoD):
  * For every representative VALID invocation the C-reconstructed argparse Namespace
    equals ``build_parser().parse_args(argv)`` EXACTLY (same dests, same types).
  * help / version / an arg error / a bad numeric / an unknown flag return a non-RUN
    action (or defer to pure) — the C parser NEVER routes an invalid invocation as RUN.
  * End-to-end: ``main(argv)`` on the native path and on the forced-pure path produce
    IDENTICAL exit code AND stdout / stderr (the routing invokes the same run body).

The native-requiring assertions ``skipif`` cleanly when the rc193 C peer is absent
(pure / numpy-absent / stale-lib host). numpy-free (stdlib argparse / io / json)."""
from __future__ import annotations

import contextlib
import ctypes
import importlib
import io

import pytest

from srmech.amsc import _native

_cli_main = importlib.import_module("srmech.cli.main")

_needs_native = pytest.mark.skipif(
    not _native.has_native_cli(),
    reason="rc193 CLI grammar + dispatch C peer not loaded (pure / stale host)",
)


# ── every VALID subcommand invocation: native Namespace == pure argparse ──────
_RUN_CASES = [
    ["status"],
    ["status", "--pid", "123", "-f", "--json", "--poll-interval", "0.25"],
    ["status", "--pid", "-7"],
    ["bus"],
    ["bus", "list"],
    ["bus", "list", "--json", "--all"],
    ["bus", "tap", "chan1"],
    ["bus", "tap", "chan1", "--format", "pretty", "--limit", "5"],
    ["bus", "tap", "chan1", "--seed", "deadbeef", "--filter", "evt"],
    ["bus", "pipe", "src1", "dst1"],
    ["bus", "pipe", "src1", "dst1", "--transform", "{**e}"],
    ["bus", "send", "chanX", '{"type":"ping"}'],
    ["bus", "send", "chanX", "--timeout", "2.5", "--stdin"],
    ["bus", "serve", "srv", "--echo"],
    ["bus", "serve", "srv", "--seed-mint", "--handler-module", "mod:fn"],
    ["dsl"],
    ["dsl", "run", "chain.toml"],
    ["dsl", "run", "chain.toml", "--input", "[1,2]", "--json"],
    ["dsl", "run", "c.toml", "--input-file", "x.json", "--ndjson-input"],
    ["dsl", "ops"],
    ["dsl", "ops", "--json"],
    ["dsl", "visualize", "c.toml", "--json"],
    ["mcp"],
    ["mcp", "emit-mcpb"],
    ["mcp", "emit-mcpb", "--type", "python", "--name", "foo", "--manifest-only"],
    ["mcp", "emit-mcpb", "--out", "/tmp/x", "--filter", "srmech.*"],
    ["class"],
    ["class", "list"],
    ["class", "describe", "Genome"],
    [],
]


@_needs_native
@pytest.mark.parametrize("argv", _RUN_CASES)
def test_native_namespace_equals_pure_argparse(argv):
    """The C parser's reconstructed Namespace == build_parser().parse_args(argv)."""
    parsed = _native.cli_parse_c(argv)
    assert parsed is not None, f"C parser unexpectedly declined a valid invocation: {argv}"
    action, payload = parsed
    assert action == _native.CLI_ACTION_RUN, f"expected RUN for {argv}, got action {action}"
    ns_native = vars(_cli_main._namespace_from_native(payload))
    ns_pure = vars(_cli_main.build_parser().parse_args(argv))
    assert ns_native == ns_pure, (
        f"native namespace != pure argparse for {argv}\n"
        f"  native: {ns_native}\n  pure  : {ns_pure}"
    )


# ── the command → route contract ─────────────────────────────────────────────
_ROUTE_CASES = [
    (["status"], _native.CLI_ROUTE_STATUS),
    (["bus", "list"], _native.CLI_ROUTE_BUS),
    (["bus"], _native.CLI_ROUTE_BUS),
    (["dsl", "ops"], _native.CLI_ROUTE_DSL),
    (["mcp", "emit-mcpb"], _native.CLI_ROUTE_MCP),
    (["class", "list"], _native.CLI_ROUTE_CLASS),
    ([], _native.CLI_ROUTE_HELP),   # bare `srmech` → print top help
]


@_needs_native
@pytest.mark.parametrize("argv,expected_route", _ROUTE_CASES)
def test_dispatch_routes_command(argv, expected_route):
    parsed = _native.cli_parse_c(argv)
    assert parsed is not None and parsed[0] == _native.CLI_ACTION_RUN
    route = _native.cli_dispatch_c(parsed[1])
    assert route == expected_route, f"{argv}: route {route} != {expected_route}"


# ── help / version / errors do NOT route as a clean RUN ──────────────────────
@_needs_native
@pytest.mark.parametrize("argv,expected_action", [
    (["--help"], _native.CLI_ACTION_HELP),
    (["-h"], _native.CLI_ACTION_HELP),
    (["status", "--help"], _native.CLI_ACTION_HELP),
    (["bus", "--help"], _native.CLI_ACTION_HELP),
    (["--version"], _native.CLI_ACTION_VERSION),
    (["boguscmd"], _native.CLI_ACTION_ERROR),
    (["bus", "bogussub"], _native.CLI_ACTION_ERROR),
    (["bus", "tap"], _native.CLI_ACTION_ERROR),          # missing required positional
    (["bus", "tap", "a", "b"], _native.CLI_ACTION_ERROR),  # too many positionals
    (["bus", "tap", "c", "--format", "bogus"], _native.CLI_ACTION_ERROR),  # bad choice
    (["mcp", "emit-mcpb", "--type", "nope"], _native.CLI_ACTION_ERROR),    # bad choice
])
def test_non_run_actions_are_not_run(argv, expected_action):
    parsed = _native.cli_parse_c(argv)
    assert parsed is not None, f"expected a decided action for {argv}, got a defer"
    action, _ = parsed
    assert action == expected_action, f"{argv}: action {action} != {expected_action}"
    assert action != _native.CLI_ACTION_RUN


@_needs_native
@pytest.mark.parametrize("argv", [
    ["bus", "tap", "chan1", "--limit", "notint"],   # bad int → defer to pure
    ["status", "--poll-interval", "abc"],           # bad float → defer to pure
    ["status", "--unknownflag"],                    # unknown option → defer (abbrev)
    ["bus", "tap", "chan1", "--"],                  # inline `--` → defer
])
def test_bounded_parser_defers_cleanly(argv):
    """A grammar the bounded parser declines returns None (SRMECH_ERR_NOT_IMPL) so
    the Python host runs pure argparse — never a wrong RUN."""
    parsed = _native.cli_parse_c(argv)
    if parsed is not None:
        assert parsed[0] != _native.CLI_ACTION_RUN


# ── end-to-end main() behavior-parity: native path == forced-pure path ───────
# Only run bodies with DETERMINISTIC output (no dependency on the live ~/.srmech
# introspection dir or the per-user bus dir, which concurrent test subprocesses
# mutate between the two invocations). `status` / `bus list` read that mutable
# host state, so their run-body output is time-dependent — the C grammar for them
# is proven exhaustively by the namespace + route parity tests above instead.
_E2E_CASES = [
    ["dsl", "ops"],
    ["dsl", "ops", "--json"],
    ["class", "list"],
    ["bus"],
    ["dsl"],
    ["mcp"],
    [],
    ["--version"],
    ["--help"],
    ["boguscmd"],
    ["bus", "tap"],
    ["dsl", "run", "/nonexistent/rc193.toml", "--input", "5"],
    ["bus", "send", "chanX", "not-json"],
]


def _invoke_main(argv):
    out, err = io.StringIO(), io.StringIO()
    code = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = _cli_main.main(argv)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    return code, out.getvalue(), err.getvalue()


@_needs_native
@pytest.mark.parametrize("argv", _E2E_CASES)
def test_main_native_matches_pure(argv, monkeypatch):
    native = _invoke_main(argv)
    monkeypatch.setattr(_native, "has_native_cli", lambda: False)
    pure = _invoke_main(argv)
    assert native == pure, (
        f"main() native vs pure diverged for {argv}\n"
        f"  native: {native!r}\n  pure  : {pure!r}"
    )


# ── the C entry points guard NULL args (rc187 null-check-before-assert) ──────
@_needs_native
def test_cli_dispatch_null_and_bad_input():
    lib = _native.LIB
    route = ctypes.c_int(-1)
    # NULL parsed_json → SRMECH_ERR_NULL_ARG (graceful, no crash)
    rc = lib.srmech_cli_dispatch(None, 0, ctypes.byref(route))
    assert rc == 1  # SRMECH_ERR_NULL_ARG
    # JSON with no recognizable command → SRMECH_ERR_BAD_INPUT
    rc = lib.srmech_cli_dispatch(b'{"nope":1}', 10, ctypes.byref(route))
    assert rc == 2  # SRMECH_ERR_BAD_INPUT
    # a valid command routes cleanly
    ok = _native.cli_dispatch_c(b'{"command":"dsl","dsl_command":"ops"}')
    assert ok == _native.CLI_ROUTE_DSL


@_needs_native
def test_cli_parse_null_out_returns_null_arg():
    lib = _native.LIB
    arr = (ctypes.c_char_p * 1)()
    arr[0] = b"status"
    got = ctypes.c_size_t(0)
    action = ctypes.c_int(-1)
    exit_code = ctypes.c_int(-1)
    argv_p = ctypes.cast(arr, ctypes.POINTER(ctypes.c_char_p))
    # NULL out buffer → SRMECH_ERR_NULL_ARG (no assert-abort, no crash)
    rc = lib.srmech_cli_parse(
        1, argv_p, None, 0, ctypes.byref(got),
        ctypes.byref(action), ctypes.byref(exit_code))
    assert rc == 1  # SRMECH_ERR_NULL_ARG
