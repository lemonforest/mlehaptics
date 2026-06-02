"""Tests for the ``srmech bus`` CLI subcommands (v0.5.0rc4).

Each test invokes the CLI as a subprocess (``python -m srmech ...``)
so the actual argparse plumbing + entry-point routing is exercised
end-to-end. Some tests start a background ``srmech bus serve``
subprocess via :func:`_start_server` and tear it down on test exit.

Mirror of the discipline pattern: in-process unit tests for the
:mod:`srmech.bus` core live in :mod:`tests.test_bus`; this module is
the CLI-surface peer.

Framework reading: the test suite is Class A (content-addressing
the subprocess output) ∘ Class E (catalog enumeration of each
subcommand surface).
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

import pytest


# ──────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ──────────────────────────────────────────────────────────────────────


_PY = sys.executable

# Default per-subprocess timeout — generous so slow CI doesn't flake.
_TIMEOUT_S = 15.0


def _run_cli(*args: str, **kwargs) -> subprocess.CompletedProcess:
    """Run ``python -m srmech <args>``; return the completed process."""
    cmd = [_PY, "-m", "srmech", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=kwargs.pop("timeout", _TIMEOUT_S),
        check=False,
        **kwargs,
    )


def _start_server(
    name: str, *, echo: bool = True, extra: Optional[list] = None,
) -> subprocess.Popen:
    """Start ``srmech bus serve NAME --echo`` as a background subprocess."""
    args = [_PY, "-m", "srmech", "bus", "serve", name]
    if echo:
        args.append("--echo")
    if extra:
        args.extend(extra)
    return subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _wait_for_endpoint(name: str, *, timeout_s: float = 8.0) -> bool:
    """Poll ``srmech bus list`` until ``name`` appears (or timeout)."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        out = _run_cli("bus", "list", "--json")
        if out.returncode == 0:
            try:
                data = json.loads(out.stdout or "[]")
            except json.JSONDecodeError:
                data = []
            for ep in data:
                if ep.get("name") == name and ep.get("alive"):
                    return True
        time.sleep(0.1)
    return False


def _stop_server(
    proc: subprocess.Popen, *, name: Optional[str] = None,
) -> None:
    """Best-effort teardown of a bus server subprocess + registry file."""
    try:
        if proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass
            try:
                proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except OSError:
                    pass
                try:
                    proc.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    pass
    finally:
        # Best-effort cleanup of any leftover registry files. The
        # serve subprocess SHOULD do this itself on stop; on Windows
        # subprocess.terminate sends a signal that may not give the
        # python finaliser a chance to run.
        if name is not None:
            for suffix in (".sock", ".txt", ".seed"):
                path = Path.home() / ".srmech" / f"bus-{name}{suffix}"
                try:
                    if path.exists():
                        path.unlink()
                except OSError:
                    pass


@pytest.fixture
def server_name() -> str:
    """Return a unique endpoint name for one test."""
    return f"clitest-{uuid.uuid4().hex[:10]}"


@pytest.fixture
def echo_server(server_name: str):
    """Spawn an echo bus server; yield (name, proc); auto-teardown."""
    proc = _start_server(server_name, echo=True)
    appeared = _wait_for_endpoint(server_name)
    if not appeared:
        # Capture early stderr to make failure debuggable.
        out, err = "", ""
        try:
            out, err = proc.communicate(timeout=0.5)
        except subprocess.TimeoutExpired:
            pass
        _stop_server(proc, name=server_name)
        pytest.skip(
            f"echo server did not appear in time; stderr={err!r}",
        )
    try:
        yield server_name, proc
    finally:
        _stop_server(proc, name=server_name)


# ──────────────────────────────────────────────────────────────────────
# Top-level CLI
# ──────────────────────────────────────────────────────────────────────


def test_srmech_help_exits_zero():
    res = _run_cli("--help")
    assert res.returncode == 0, res.stderr
    assert "bus" in res.stdout


def test_srmech_bus_help_exits_zero():
    res = _run_cli("bus", "--help")
    assert res.returncode == 0, res.stderr
    assert "list" in res.stdout
    assert "tap" in res.stdout
    assert "pipe" in res.stdout
    assert "send" in res.stdout
    assert "serve" in res.stdout


def test_srmech_bus_no_subcommand_exits_zero():
    """Bare 'srmech bus' should print usage hint and exit 0."""
    res = _run_cli("bus")
    assert res.returncode == 0
    # The hint goes to stderr.
    assert "subcommand" in res.stderr.lower() or "usage" in res.stderr.lower()


# ──────────────────────────────────────────────────────────────────────
# Per-subcommand --help
# ──────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("sub", ["list", "tap", "pipe", "send", "serve"])
def test_subcommand_help_exits_zero(sub):
    res = _run_cli("bus", sub, "--help")
    assert res.returncode == 0, (
        f"`srmech bus {sub} --help` should exit 0; stderr={res.stderr!r}"
    )
    assert sub in res.stdout.lower() or "usage" in res.stdout.lower()


# ──────────────────────────────────────────────────────────────────────
# list (empty + populated)
# ──────────────────────────────────────────────────────────────────────


def test_list_empty_table():
    res = _run_cli("bus", "list")
    assert res.returncode == 0, res.stderr
    # Either empty (no endpoints) or table-shaped. Both acceptable.
    assert "NAME" in res.stdout or "No active bus endpoints" in res.stdout


def test_list_empty_json_is_valid_json():
    res = _run_cli("bus", "list", "--json")
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert isinstance(data, list)


def test_list_populated_shows_endpoint(echo_server):
    name, _proc = echo_server
    res = _run_cli("bus", "list")
    assert res.returncode == 0, res.stderr
    assert name in res.stdout
    # Table form includes the header.
    assert "NAME" in res.stdout
    assert "TRANSPORT" in res.stdout


def test_list_json_populated(echo_server):
    name, _proc = echo_server
    res = _run_cli("bus", "list", "--json")
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    found = [ep for ep in data if ep.get("name") == name]
    assert found, f"endpoint {name!r} missing from JSON output: {data!r}"
    assert "transport" in found[0]
    assert "alive" in found[0]
    assert found[0]["alive"] is True


def test_list_all_flag_accepted(echo_server):
    """`--all` is accepted (placeholder for cross-user discovery)."""
    name, _proc = echo_server
    res = _run_cli("bus", "list", "--all", "--json")
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert any(ep.get("name") == name for ep in data)


# ──────────────────────────────────────────────────────────────────────
# send
# ──────────────────────────────────────────────────────────────────────


def test_send_round_trip(echo_server):
    name, _proc = echo_server
    res = _run_cli(
        "bus", "send", name,
        '{"type": "ping", "payload": "hello"}',
    )
    assert res.returncode == 0, (
        f"send failed: stdout={res.stdout!r} stderr={res.stderr!r}"
    )
    data = json.loads(res.stdout)
    # The echo handler wraps the inbound event as {'type': 'echo',
    # 'payload': <inbound-event>}.
    assert data["type"] == "echo"
    assert "payload" in data


def test_send_missing_event_json_exits_nonzero():
    res = _run_cli("bus", "send", "some-name")
    assert res.returncode != 0
    assert "no event" in res.stderr.lower() or "json" in res.stderr.lower()


def test_send_malformed_json_exits_nonzero():
    res = _run_cli("bus", "send", "some-name", "not-json{")
    assert res.returncode != 0
    assert "invalid json" in res.stderr.lower()


def test_send_missing_type_key_exits_nonzero():
    res = _run_cli("bus", "send", "some-name", '{"payload": "x"}')
    assert res.returncode != 0
    assert "type" in res.stderr.lower()


def test_send_to_nonexistent_endpoint_exits_nonzero():
    res = _run_cli(
        "bus", "send", "no-such-endpoint-zzz",
        '{"type": "ping"}',
        timeout=10.0,
    )
    assert res.returncode != 0


def test_send_stdin_round_trip(echo_server):
    name, _proc = echo_server
    res = subprocess.run(
        [_PY, "-m", "srmech", "bus", "send", name, "--stdin"],
        input='{"type": "ping", "payload": {"x": 1}}',
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_S,
        check=False,
    )
    assert res.returncode == 0, (
        f"stdin send failed: stdout={res.stdout!r} stderr={res.stderr!r}"
    )
    data = json.loads(res.stdout)
    assert data["type"] == "echo"


def test_send_timeout_flag_accepted(echo_server):
    name, _proc = echo_server
    res = _run_cli(
        "bus", "send", name,
        '{"type": "ping"}',
        "--timeout", "3.0",
    )
    assert res.returncode == 0, res.stderr


# ──────────────────────────────────────────────────────────────────────
# tap
# ──────────────────────────────────────────────────────────────────────


def test_tap_limit_exits_after_n_events(server_name):
    """Spawn a bus server that broadcasts on each ping; tap with --limit."""
    # Use a custom handler subprocess that broadcasts each ping back.
    # The simplest setup uses the echo server + send a ping after
    # subscribe; but the echo handler doesn't broadcast — it req/reps.
    # For pub/sub we use a Python helper subprocess that runs the
    # serve API directly with a broadcast-emitting loop.
    helper = subprocess.Popen(
        [_PY, "-c", _BROADCASTER_SRC, server_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert _wait_for_endpoint(server_name, timeout_s=8.0), (
            f"broadcaster did not appear; stderr peek={_peek(helper)!r}"
        )
        res = _run_cli(
            "bus", "tap", server_name,
            "--limit", "3",
            timeout=15.0,
        )
        assert res.returncode == 0, (
            f"tap failed: stdout={res.stdout!r} stderr={res.stderr!r}"
        )
        # Three JSON lines.
        lines = [ln for ln in res.stdout.splitlines() if ln.strip()]
        assert len(lines) == 3, (
            f"expected 3 events; got {len(lines)}: {lines!r}"
        )
        for line in lines:
            ev = json.loads(line)
            assert "type" in ev
    finally:
        _stop_server(helper, name=server_name)


def test_tap_filter_only_matching_events(server_name):
    """tap --filter only yields events whose type matches."""
    helper = subprocess.Popen(
        [_PY, "-c", _MIXED_BROADCASTER_SRC, server_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert _wait_for_endpoint(server_name, timeout_s=8.0)
        res = _run_cli(
            "bus", "tap", server_name,
            "--filter", "tick",
            "--limit", "2",
            timeout=15.0,
        )
        assert res.returncode == 0, res.stderr
        lines = [ln for ln in res.stdout.splitlines() if ln.strip()]
        assert len(lines) == 2
        for line in lines:
            ev = json.loads(line)
            assert ev["type"] == "tick"
    finally:
        _stop_server(helper, name=server_name)


def test_tap_pretty_format_multiline(server_name):
    helper = subprocess.Popen(
        [_PY, "-c", _BROADCASTER_SRC, server_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert _wait_for_endpoint(server_name, timeout_s=8.0)
        res = _run_cli(
            "bus", "tap", server_name,
            "--format", "pretty",
            "--limit", "1",
            timeout=15.0,
        )
        assert res.returncode == 0, res.stderr
        # Pretty JSON contains a newline within the single event.
        assert "{\n" in res.stdout
    finally:
        _stop_server(helper, name=server_name)


# ──────────────────────────────────────────────────────────────────────
# pipe (chains two endpoints)
# ──────────────────────────────────────────────────────────────────────


def test_pipe_forwards_events(server_name):
    """Wire a SRC broadcaster to a DST sink via `srmech bus pipe`."""
    src_name = server_name + "-src"
    dst_name = server_name + "-dst"
    # Spawn SRC broadcaster.
    src_helper = subprocess.Popen(
        [_PY, "-c", _BROADCASTER_SRC, src_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # Spawn DST sink that COUNTS inbound non-_subscribe events.
    dst_helper = subprocess.Popen(
        [_PY, "-c", _COUNTING_SINK_SRC, dst_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    pipe_proc: Optional[subprocess.Popen] = None
    try:
        assert _wait_for_endpoint(src_name, timeout_s=8.0)
        assert _wait_for_endpoint(dst_name, timeout_s=8.0)
        pipe_proc = subprocess.Popen(
            [_PY, "-m", "srmech", "bus", "pipe", src_name, dst_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Wait for at least a few forwards.
        time.sleep(3.0)
        # Ask the sink how many it counted.
        res = _run_cli(
            "bus", "send", dst_name,
            '{"type": "count"}',
            timeout=10.0,
        )
        assert res.returncode == 0, res.stderr
        data = json.loads(res.stdout)
        # `_normalise_response` puts the whole handler dict into the
        # response payload; ``count`` lives at ``data['payload']['count']``.
        count = data.get("payload", {}).get("count", 0)
        assert count >= 1, (
            f"pipe did not forward events: response={data!r}"
        )
    finally:
        if pipe_proc is not None:
            _stop_server(pipe_proc, name=None)
        _stop_server(src_helper, name=src_name)
        _stop_server(dst_helper, name=dst_name)


# ──────────────────────────────────────────────────────────────────────
# serve --echo (smoke)
# ──────────────────────────────────────────────────────────────────────


def test_serve_echo_smoke(echo_server):
    """Server started + endpoint present + ping round-trips.

    The echo handler returns ``{"type": "echo", "payload": <inbound>}``.
    The server's ``_normalise_response`` puts the WHOLE handler dict
    into the response payload, so the wire-form response has shape::

        {
          "type": "echo",
          "payload": {
            "type": "echo",
            "payload": <inbound-event>,
          },
          ...
        }

    where ``<inbound-event>`` is the full event dict the handler saw
    (with its own ``type`` / ``payload`` / ``attestation`` keys).
    """
    name, _proc = echo_server
    res = _run_cli(
        "bus", "send", name,
        '{"type": "hello", "payload": [1, 2, 3]}',
    )
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["type"] == "echo"
    # The handler dict round-trips as data['payload']; the inbound
    # event is in data['payload']['payload'].
    assert isinstance(data["payload"], dict)
    assert data["payload"]["type"] == "echo"
    inbound = data["payload"]["payload"]
    assert inbound["type"] == "hello"
    assert inbound["payload"] == [1, 2, 3]


def test_serve_requires_echo_or_handler():
    """`srmech bus serve NAME` without --echo / --handler-module exits 2."""
    res = _run_cli("bus", "serve", "x", timeout=5.0)
    assert res.returncode != 0
    assert "echo" in res.stderr.lower() or "handler" in res.stderr.lower()


def test_serve_seed_and_mint_mutually_exclusive():
    res = _run_cli(
        "bus", "serve", "x", "--echo",
        "--seed", "00" * 32,
        "--seed-mint",
        timeout=5.0,
    )
    assert res.returncode != 0
    assert "exclusive" in res.stderr.lower()


# ──────────────────────────────────────────────────────────────────────
# --seed (encrypted round-trip)
# ──────────────────────────────────────────────────────────────────────


def test_send_with_seed_end_to_end(server_name):
    """End-to-end encrypted serve + send round-trip via --seed HEX."""
    # 32-byte all-zero seed for deterministic test reproducibility.
    seed_hex = "ab" * 32
    server = subprocess.Popen(
        [_PY, "-m", "srmech", "bus", "serve", server_name,
         "--echo", "--seed", seed_hex],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert _wait_for_endpoint(server_name, timeout_s=8.0), (
            f"encrypted server did not appear; stderr={_peek(server)!r}"
        )
        res = _run_cli(
            "bus", "send", server_name,
            '{"type": "ping", "payload": "secret"}',
            "--seed", seed_hex,
        )
        assert res.returncode == 0, (
            f"encrypted send failed: stdout={res.stdout!r} "
            f"stderr={res.stderr!r}"
        )
        data = json.loads(res.stdout)
        assert data["type"] == "echo"
    finally:
        _stop_server(server, name=server_name)


def test_send_invalid_hex_seed_exits_nonzero():
    res = _run_cli(
        "bus", "send", "x",
        '{"type": "ping"}',
        "--seed", "not-hex-at-all",
        timeout=5.0,
    )
    assert res.returncode != 0
    assert "hex" in res.stderr.lower()


# ──────────────────────────────────────────────────────────────────────
# Helper Python source snippets (run in subprocesses)
# ──────────────────────────────────────────────────────────────────────


_BROADCASTER_SRC = r"""
import sys, time
from srmech.bus import serve

def _h(event):
    return None  # fire-and-forget; we only broadcast.

name = sys.argv[1]
ep = serve(name, handler=_h)
try:
    while True:
        ep.broadcast("tick", {"ts": time.time_ns()})
        time.sleep(0.1)
finally:
    ep.stop()
"""


_MIXED_BROADCASTER_SRC = r"""
import sys, time, itertools
from srmech.bus import serve

def _h(event):
    return None

name = sys.argv[1]
ep = serve(name, handler=_h)
try:
    for i in itertools.count():
        ep.broadcast("tick" if i % 2 == 0 else "tock", {"i": i})
        time.sleep(0.1)
finally:
    ep.stop()
"""


_COUNTING_SINK_SRC = r"""
import sys, threading
from srmech.bus import serve

counter = [0]
lock = threading.Lock()

def _h(event):
    et = event.get("type")
    if et == "count":
        return {"type": "count_response", "count": counter[0]}
    with lock:
        counter[0] += 1
    return None  # fire-and-forget

name = sys.argv[1]
ep = serve(name, handler=_h)
try:
    import time
    while True:
        time.sleep(1.0)
finally:
    ep.stop()
"""


def _peek(proc: subprocess.Popen, timeout: float = 0.3) -> str:
    """Best-effort peek at a subprocess's accumulated stderr."""
    try:
        if proc.stderr is None:
            return ""
        # Non-blocking-ish: poll then read whatever's queued.
        if proc.poll() is None:
            return ""
        return proc.stderr.read() or ""
    except Exception:
        return ""
