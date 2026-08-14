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
    """Poll the bus discovery layer until ``name`` is up (or timeout).

    This probes **in-process** via :func:`srmech.bus.by_name` — the same
    discovery + liveness call ``srmech bus list`` itself makes (see
    ``cli/bus.py:run_list``) — rather than spawning ``python -m srmech
    bus list --json`` per sample. It matches the helper of the same name
    in :mod:`tests.test_bus`, which has 14 call sites across 13 tests.
    (rc402 wrote "40+ bus tests already use", quoting a claim that was
    itself wrong at ``test_bus.py``; rc404 (`#T1069`) corrected both.)

    Why (rc402, a measured Windows flake): a subprocess sample costs a
    whole interpreter start + ``srmech`` import — **measured 0.67–1.25 s
    on an idle Windows box, vs 0.6–2.8 ms in-process, a 400–1000×
    gap**. The instrument cost the same order as the thing it measured,
    so an 8 s deadline bought only ~8 samples idle and ~2–3 on a 2-core
    CI runner under xdist load — while the server being waited for paid
    that identical startup cost. That is a sampling-rate defect, not a
    deadline that is too short, so the deadline below is deliberately
    UNCHANGED: this fix raises the sample count inside the same 8 s,
    it does not buy more time.

    CLI coverage is unaffected — ``bus list`` / ``bus list --json`` /
    ``bus list --all --json`` keep their own dedicated subprocess tests
    below; this helper is readiness scaffolding, not the assertion.
    """
    from srmech.bus import by_name

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        ep = by_name(name)
        if ep is not None and ep.alive:
            return True
        time.sleep(0.02)
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


def _require_endpoint(name: str, proc, *, timeout_s: float = 8.0) -> None:
    """FAIL (never skip) when a server WE spawned did not come up.

    rc404 (`#T1069`) flipped this from ``pytest.skip`` to ``pytest.fail``, to
    reconcile a contract this module held two ways at once. Readiness for the
    SAME condition was adjudicated differently depending on where it was
    checked: six sites already hard-assert it (``assert _wait_for_endpoint(...)``
    at lines ~360, ~392, ~417, ~456, ~457, ~563), while the ``echo_server``
    fixture skipped — silently removing seven tests from the run.

    A skip is the right verdict for "this environment cannot host the test"
    (no native lib, no socket support). It is the WRONG verdict for "a server
    this fixture itself launched failed to start", which is a defect in the
    thing under test, reported as absence.

    THE DECIDING EVIDENCE. CI run 30970524301 red'd at
    ``test_cli_bus.py:342`` — "broadcaster did not appear" — at an ASSERT
    site, and that red is what produced rc402. The identical condition at the
    SKIP site would have quietly passed seven tests and left the defect in the
    tree. So the measured 0 firings across 89 of 90 ``srmech-ci`` runs is not
    evidence that this never happens; it is evidence that the one time it did,
    it happened where someone could see it.

    Margin, measured: fixture setup takes 0.16-0.19 s against an 8.0 s
    deadline (~42x), and rc402 already fixed the sampling-rate half of the
    flake (~8 -> ~364 samples in the same window). ``pytest.fail`` is used
    rather than a bare ``assert`` because an ``assert`` raised in fixture
    setup reports as ERROR rather than FAILED, and because it matches the
    sibling idiom at ``test_bus.py:106``.
    """
    if _wait_for_endpoint(name, timeout_s=timeout_s):
        return
    # Capture early stderr to make the failure debuggable.
    err = ""
    try:
        _, err = proc.communicate(timeout=0.5)
    except subprocess.TimeoutExpired:
        pass
    except (ValueError, OSError):
        pass
    _stop_server(proc, name=name)
    pytest.fail(f"echo server did not appear in time; stderr={err!r}")


@pytest.fixture
def echo_server(server_name: str):
    """Spawn an echo bus server; yield (name, proc); auto-teardown."""
    proc = _start_server(server_name, echo=True)
    _require_endpoint(server_name, proc)
    try:
        yield server_name, proc
    finally:
        _stop_server(proc, name=server_name)


class _DeadProc:
    """A process that is already gone, for exercising the failure path."""

    def communicate(self, timeout=None):
        return ("", "")

    def poll(self):
        return 0

    def terminate(self):
        pass

    def kill(self):
        pass

    def wait(self, timeout=None):
        return 0


def test_readiness_timeout_is_a_failure_not_a_skip() -> None:
    """A server that never appears must RED, not vanish into the skip count.

    SCOPE, stated plainly: this is a FORWARD REGRESSION GUARD, not a
    discriminator against rc403. ``_require_endpoint`` is introduced by rc404
    (`#T1069`), so there is no earlier revision to run it against — "swap the
    expectation to ``Skipped`` and it passes on rc403" is not a testable
    claim, because on rc403 the function does not exist. What it does buy is
    real and narrow: the skip-vs-fail decision now has a test holding it, so a
    future edit cannot quietly restore ``pytest.skip`` and take seven tests
    out of the run with it.

    ``timeout_s`` is deliberately tiny. The production default is 8.0 s, and
    calling it here would add ~8 s of wall time to the flakiest cell in the
    matrix to observe a decision that needs none of it.
    """
    from _pytest.outcomes import Failed, Skipped

    with pytest.raises(Failed):
        _require_endpoint(
            "never-exists-" + uuid.uuid4().hex, _DeadProc(), timeout_s=0.05
        )

    # And it must not be raising Skipped-that-happens-to-look-like-Failed:
    # the two are unrelated classes, so pin the negative directly.
    assert not issubclass(Failed, Skipped)


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
