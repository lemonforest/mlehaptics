"""Tests for ``srmech.introspect`` (v0.4.6rc2).

Covers the publish() context manager, the env-var auto-publish path,
the list() / by_pid() / Run.follow() reader API, the per-emit-hook
no-op-when-off guarantee, NDJSON serialise/parse round-trip, the
``srmech status`` CLI subcommand, and cross-platform liveness probes.

Per spec ~25-30 tests. Heavy use of pytest's ``tmp_path`` + monkey-
patching ``srmech.introspect._writer.introspect_dir`` so we never
touch the real ``~/.srmech/`` directory.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

import srmech
from srmech import introspect
from srmech.introspect import (
    Event,
    INTROSPECT_DIR_NAME,
    MPR_VERSION_INTROSPECT,
    Run,
    by_pid,
    parse,
    publish,
    serialize,
)
from srmech.introspect import _writer as _w_mod
from srmech.introspect import _event as _e_mod


# ─────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect ``~/.srmech/`` to a tmp path for the duration of one test."""
    fake = tmp_path / "fake_home"
    fake.mkdir()
    monkeypatch.setattr(
        _w_mod, "introspect_dir", lambda: fake / INTROSPECT_DIR_NAME
    )
    # The public introspect module re-exports introspect_dir; redirect
    # that too so list() / by_pid() agree.
    monkeypatch.setattr(
        introspect, "introspect_dir",
        lambda: fake / INTROSPECT_DIR_NAME,
    )
    return fake / INTROSPECT_DIR_NAME


@pytest.fixture(autouse=True)
def _ensure_clean_state():
    """Make sure no writer leaks between tests."""
    yield
    if _w_mod._ACTIVE_WRITER is not None:
        _w_mod._deactivate_writer()
    _w_mod._set_publishing(False)


# ─────────────────────────────────────────────────────────────────────
# Module exposure
# ─────────────────────────────────────────────────────────────────────


def test_module_attribute_exposed_on_srmech():
    """``from srmech import introspect`` AND ``srmech.introspect`` both work."""
    assert hasattr(srmech, "introspect")
    assert srmech.introspect is introspect


def test_public_callables_exist():
    """Spec: publish, list, by_pid callable from the module."""
    assert callable(introspect.publish)
    assert callable(introspect.list)
    assert callable(introspect.by_pid)
    # Dataclasses present.
    assert hasattr(introspect, "Run")
    assert hasattr(introspect, "Event")


# ─────────────────────────────────────────────────────────────────────
# Off-by-default
# ─────────────────────────────────────────────────────────────────────


def test_publish_no_file_when_off(fake_home):
    """Importing srmech.introspect alone must NOT create any file."""
    # fake_home is created empty.
    assert not list(fake_home.glob("run-*.ndjson"))
    # The emit_if_publishing hook on its own is a no-op.
    _w_mod.emit_if_publishing("test.no_op", class_="K", input_shape="x")
    assert not list(fake_home.glob("run-*.ndjson"))


def test_emit_noop_when_not_publishing(fake_home):
    """Cascade ops called outside publish() must NOT write."""
    from srmech.amsc.cascade import chiral_flip
    chiral_flip([1, 2, 3])
    assert not list(fake_home.glob("run-*.ndjson"))


# ─────────────────────────────────────────────────────────────────────
# publish() basics
# ─────────────────────────────────────────────────────────────────────


def test_publish_creates_file(fake_home):
    """``with publish(): ...`` creates one status file."""
    with publish() as handle:
        assert handle.active
        assert handle.file_path.exists()
        # The file must follow the canonical naming convention.
        assert handle.file_path.name.startswith(f"run-{os.getpid()}-")
        assert handle.file_path.name.endswith(".ndjson")
    # After exit the file is still present (default leave-for-list).


def test_publish_emits_session_start_and_end(fake_home):
    """session_start + session_end frame each publish() scope."""
    with publish() as handle:
        pass
    lines = handle.file_path.read_bytes().splitlines()
    events = [parse(line) for line in lines if line.strip()]
    assert events[0].op_name == "session_start"
    assert events[-1].op_name == "session_end"


def test_publish_remove_on_exit(fake_home):
    """``remove_on_exit=True`` unlinks the file at scope exit."""
    with publish(remove_on_exit=True) as handle:
        assert handle.file_path.exists()
    assert not handle.file_path.exists()


def test_publish_reentrant_no_op(fake_home):
    """Nested ``with publish():`` re-uses the active writer."""
    with publish() as outer:
        with publish() as inner:
            assert inner.pid == outer.pid
            assert inner.file_path == outer.file_path
        # Inner block exit must NOT teardown the writer.
        assert _w_mod.get_active_writer() is not None


# ─────────────────────────────────────────────────────────────────────
# Emit hooks
# ─────────────────────────────────────────────────────────────────────


def test_emit_inside_cascade_op(fake_home):
    """Calling ``cascade.chiral_flip`` inside publish() emits an event."""
    from srmech.amsc.cascade import chiral_flip
    with publish() as handle:
        chiral_flip([1, 2, 3])
    events = [parse(L) for L in handle.file_path.read_bytes().splitlines() if L.strip()]
    cascade_events = [e for e in events if e.op_name == "cascade.chiral_flip"]
    assert len(cascade_events) == 1
    assert cascade_events[0].class_ == "C"


def test_emit_inside_pin_slot_at_zero(fake_home):
    from srmech.amsc.cascade import pin_slot_at_zero
    with publish() as handle:
        pin_slot_at_zero(-3.5)
        pin_slot_at_zero(0.0)
    events = [parse(L) for L in handle.file_path.read_bytes().splitlines() if L.strip()]
    pins = [e for e in events if e.op_name == "cascade.pin_slot_at_zero"]
    assert len(pins) == 2
    assert all(e.class_ == "K" for e in pins)


def test_emit_writes_event(fake_home):
    """Direct emit_if_publishing inside publish() lands on disk."""
    with publish() as handle:
        _w_mod.emit_if_publishing(
            "test.manual", class_="A", input_shape="(8,)"
        )
    events = [parse(L) for L in handle.file_path.read_bytes().splitlines() if L.strip()]
    manuals = [e for e in events if e.op_name == "test.manual"]
    assert len(manuals) == 1
    assert manuals[0].class_ == "A"
    assert manuals[0].input_shape == "(8,)"


def test_emit_carries_attestation(fake_home):
    """Each event carries pid + start_time_ns + srmech_version."""
    with publish() as handle:
        _w_mod.emit_if_publishing("test.attest", class_="A")
    events = [parse(L) for L in handle.file_path.read_bytes().splitlines() if L.strip()]
    for e in events:
        assert "pid" in e.attestation
        assert "start_time_ns" in e.attestation
        assert "srmech_version" in e.attestation
        assert e.attestation["pid"] == os.getpid()
        assert e.attestation["srmech_version"] == srmech.__version__
        assert e.mpr_version == MPR_VERSION_INTROSPECT


# ─────────────────────────────────────────────────────────────────────
# Event round-trip + MPR shape
# ─────────────────────────────────────────────────────────────────────


def test_event_round_trip():
    """``parse(serialize(event))`` reconstructs the event exactly."""
    ev = Event(
        mpr_version=MPR_VERSION_INTROSPECT,
        op_name="cascade.chiral_flip",
        class_="C",
        started_ts="2026-05-28T14:21:00.000000Z",
        finished_ts=None,
        input_shape="(8,)",
        output_shape=None,
        error=None,
        attestation={"pid": 12345, "start_time_ns": 1000, "srmech_version": "0.4.6rc2"},
        extra={"path": "auto"},
    )
    line = serialize(ev)
    decoded = parse(line)
    assert decoded == ev


def test_event_serialize_one_line():
    """Serialised output is exactly one NDJSON line (one '\\n')."""
    ev = Event(
        mpr_version=MPR_VERSION_INTROSPECT,
        op_name="x",
        class_="K",
        started_ts="t",
        finished_ts=None,
        input_shape="",
        output_shape=None,
        error=None,
        attestation={},
    )
    line = serialize(ev)
    # exactly one trailing newline; no embedded newlines.
    assert line.count(b"\n") == 1
    assert line.endswith(b"\n")


def test_event_mpr_shape_keys():
    """Event JSON carries the required MPR-shape keys."""
    ev = Event(
        mpr_version=MPR_VERSION_INTROSPECT,
        op_name="x",
        class_="",
        started_ts="t",
        finished_ts=None,
        input_shape="",
        output_shape=None,
        error=None,
        attestation={"pid": 0, "start_time_ns": 0, "srmech_version": "x"},
    )
    payload = json.loads(serialize(ev).decode())
    for key in ("mpr_version", "op_name", "attestation"):
        assert key in payload


def test_run_dataclass_immutable():
    """Run is a frozen dataclass."""
    r = Run(
        pid=1, start_time_ns=2, script_name="x", current_op="y",
        current_class="K", elapsed_ms=0, status="running",
        event_count=0, file_path=Path("/tmp/x"),
    )
    with pytest.raises(Exception):  # FrozenInstanceError
        r.pid = 5  # type: ignore[misc]


def test_event_dataclass_immutable():
    """Event is a frozen dataclass."""
    ev = Event(
        mpr_version=MPR_VERSION_INTROSPECT,
        op_name="x", class_="", started_ts="t",
        finished_ts=None, input_shape="", output_shape=None,
        error=None, attestation={},
    )
    with pytest.raises(Exception):
        ev.op_name = "y"  # type: ignore[misc]


# ─────────────────────────────────────────────────────────────────────
# list() + by_pid()
# ─────────────────────────────────────────────────────────────────────


def test_list_returns_active_run(fake_home):
    """list() returns the active run."""
    with publish():
        runs = introspect.list()
        active = [r for r in runs if r.pid == os.getpid()]
        assert len(active) >= 1


def test_list_auto_cleanup_stale(fake_home, monkeypatch):
    """list() unlinks orphan files whose PID is dead."""
    fake_home.mkdir(parents=True, exist_ok=True)
    orphan = fake_home / "run-999999-12345.ndjson"
    # Use a PID that's almost-certainly not alive.
    ev = Event(
        mpr_version=MPR_VERSION_INTROSPECT,
        op_name="session_start",
        class_="",
        started_ts="2026-05-28T00:00:00.000000Z",
        finished_ts=None,
        input_shape="",
        output_shape=None,
        error=None,
        attestation={"pid": 999999, "start_time_ns": 12345, "srmech_version": "x"},
        extra={"script_name": "ghost.py"},
    )
    orphan.write_bytes(serialize(ev))
    # Force the alive-check to report dead for this PID.
    monkeypatch.setattr(
        introspect, "_process_is_alive",
        lambda pid: False if pid == 999999 else True,
    )
    runs = introspect.list()
    pids = [r.pid for r in runs]
    assert 999999 in pids  # returned at least once
    # File removed by auto-cleanup.
    assert not orphan.exists()


def test_by_pid_returns_run(fake_home):
    """by_pid() looks up a run by PID."""
    with publish() as handle:
        run = by_pid(os.getpid())
        assert run is not None
        assert run.pid == os.getpid()
        assert run.start_time_ns == handle.start_time_ns


def test_by_pid_unknown_returns_none(fake_home):
    assert by_pid(1) is None


def test_start_time_ns_defeats_pid_recycling(fake_home, monkeypatch):
    """Two files for the same PID → by_pid returns the most-recent."""
    fake_home.mkdir(parents=True, exist_ok=True)
    pid = 999998
    # Two files for the same PID with different start_time_ns.
    for start in (1000, 5000):
        ev = Event(
            mpr_version=MPR_VERSION_INTROSPECT,
            op_name="session_start",
            class_="",
            started_ts="2026-05-28T00:00:00.000000Z",
            finished_ts=None,
            input_shape="",
            output_shape=None,
            error=None,
            attestation={
                "pid": pid, "start_time_ns": start,
                "srmech_version": "x",
            },
            extra={"script_name": f"r{start}.py"},
        )
        path = fake_home / f"run-{pid}-{start}.ndjson"
        path.write_bytes(serialize(ev))
    monkeypatch.setattr(
        introspect, "_process_is_alive",
        lambda p: True if p == pid else False,
    )
    run = by_pid(pid)
    assert run is not None
    assert run.start_time_ns == 5000


# ─────────────────────────────────────────────────────────────────────
# Run.follow()
# ─────────────────────────────────────────────────────────────────────


def test_follow_streams_events(fake_home):
    """Run.follow() yields events as the publisher emits them."""
    # Same process — we drive enter / emit / exit on a background thread.
    writer = _w_mod._activate_writer()
    try:
        path = writer.file_path
        # Build a Run that points at the in-progress file. Since the
        # publisher IS this process, follow() must stop when it sees
        # session_end (the writer dies → follow returns).
        # Emit a couple of events.
        _w_mod.emit_if_publishing("test.stream", class_="A")
        _w_mod.emit_if_publishing("test.stream2", class_="B")
    finally:
        _w_mod._deactivate_writer()
    # Now construct a Run from the file and follow it (should drain in one pass).
    run = introspect._run_from_file(path)
    assert run is not None
    events = builtins_list_safe(run.follow(poll_interval_s=0.01, timeout_s=2.0))
    # We must see at least session_start, test.stream, test.stream2, session_end.
    op_names = [e.op_name for e in events]
    assert "session_start" in op_names
    assert "test.stream" in op_names
    assert "session_end" in op_names


def builtins_list_safe(it):
    """Materialise an iterator into a python list (the test file
    shadows ``list`` via the import, this helper avoids confusion)."""
    out = []
    for x in it:
        out.append(x)
    return out


# ─────────────────────────────────────────────────────────────────────
# Thread-safety
# ─────────────────────────────────────────────────────────────────────


def test_writer_thread_safe(fake_home):
    """Concurrent emits produce one NDJSON line per emit; no corruption."""
    n_threads = 4
    per_thread = 25
    with publish() as handle:
        # Activate publishing on each spawned worker thread (the TLS
        # flag is per-thread; the writer is shared).
        def worker(tid):
            _w_mod._set_publishing(True)
            try:
                for i in range(per_thread):
                    _w_mod.emit_if_publishing(
                        f"thread.{tid}",
                        class_="K",
                        input_shape=f"{tid}.{i}",
                    )
            finally:
                _w_mod._set_publishing(False)
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    raw = handle.file_path.read_bytes()
    lines = [L for L in raw.splitlines() if L.strip()]
    # Every line must parse cleanly.
    for L in lines:
        parse(L)
    # We must see n_threads * per_thread thread events (plus the
    # session_start + session_end framing).
    thread_lines = [L for L in lines if b'"thread.' in L]
    assert len(thread_lines) == n_threads * per_thread


# ─────────────────────────────────────────────────────────────────────
# Pyodide degradation
# ─────────────────────────────────────────────────────────────────────


def test_pyodide_degrades_list_returns_empty(monkeypatch):
    """Under PYODIDE=1, list() returns empty without touching disk."""
    monkeypatch.setenv("PYODIDE", "1")
    assert introspect.list() == []


def test_pyodide_degrades_by_pid_returns_none(monkeypatch):
    monkeypatch.setenv("PYODIDE", "1")
    assert by_pid(1) is None


def test_pyodide_degrades_publish_noop(monkeypatch, fake_home):
    monkeypatch.setenv("PYODIDE", "1")
    with publish() as handle:
        assert not handle.active
    # No file should have been created.
    assert not list(fake_home.glob("run-*.ndjson"))


# ─────────────────────────────────────────────────────────────────────
# env-var auto-publish
# ─────────────────────────────────────────────────────────────────────


def test_env_var_auto_publish(tmp_path):
    """SRMECH_PUBLISH_STATUS=1 set BEFORE import activates publish."""
    # Use subprocess so we can set the env var before srmech imports.
    fake_home = tmp_path / "auto_publish_home"
    script = (
        "import os, sys, time;"
        "os.environ['HOME'] = " + repr(str(fake_home)) + ";"
        "os.environ['USERPROFILE'] = " + repr(str(fake_home)) + ";"
        # Some platforms use HOMEDRIVE+HOMEPATH on Windows; cover both.
        "fake_home = " + repr(str(fake_home)) + ";"
        "from pathlib import Path;"
        "Path(fake_home).mkdir(parents=True, exist_ok=True);"
        # Stub Path.home() via env to keep it portable.
        "import srmech;"
        "import srmech.introspect as I;"
        "from srmech.amsc.cascade import chiral_flip;"
        "chiral_flip([1,2,3]);"
        "w = I._writer.get_active_writer();"
        "print('FILE:' + str(w.file_path) if w else 'NOFILE');"
    )
    env = dict(os.environ)
    env["SRMECH_PUBLISH_STATUS"] = "1"
    env["HOME"] = str(fake_home)
    env["USERPROFILE"] = str(fake_home)
    proc = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    # The subprocess must have created a status file under fake_home.
    status_dir = fake_home / INTROSPECT_DIR_NAME
    files = list(status_dir.glob("run-*.ndjson")) if status_dir.exists() else []
    assert files, (
        f"expected an auto-published status file under {status_dir!r}; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────


def test_cli_status_no_runs(fake_home, capsys, monkeypatch):
    from srmech.cli.main import main as cli_main
    rc = cli_main(["status"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "No active publishing srmech runs." in captured.out


def test_cli_status_lists_active_run(fake_home, capsys):
    from srmech.cli.main import main as cli_main
    with publish():
        rc = cli_main(["status"])
        assert rc == 0
        captured = capsys.readouterr()
        # The PID column header must appear; our PID row must appear.
        assert "PID" in captured.out
        assert str(os.getpid()) in captured.out


def test_cli_status_detail(fake_home, capsys):
    from srmech.cli.main import main as cli_main
    with publish():
        rc = cli_main(["status", "--pid", str(os.getpid())])
        assert rc == 0
        captured = capsys.readouterr()
        assert "PID:" in captured.out
        assert str(os.getpid()) in captured.out
        assert "Status:" in captured.out


def test_cli_status_json(fake_home, capsys):
    from srmech.cli.main import main as cli_main
    with publish():
        rc = cli_main(["status", "--json"])
        assert rc == 0
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert any(r["pid"] == os.getpid() for r in payload)


def test_cli_status_pid_not_found(fake_home, capsys):
    from srmech.cli.main import main as cli_main
    rc = cli_main(["status", "--pid", "1"])
    assert rc == 1


# ─────────────────────────────────────────────────────────────────────
# describe_shape helper
# ─────────────────────────────────────────────────────────────────────


def test_describe_shape_handles_common_inputs():
    from srmech.introspect._event import describe_shape
    assert describe_shape(None) == "None"
    assert describe_shape(3.14).startswith("float")
    assert describe_shape([1, 2, 3]).startswith("list(len=3")
    # a 2-D shaped carrier — numpy-free (#564): describe_shape duck-types
    # `.shape`, so the numpy-free Mat (shape (4, 4)) exercises the same branch
    # an ndarray used to. (numpy is GONE from srmech and its test oracle.)
    from srmech.amsc.mat import Mat
    s = describe_shape(Mat.from_rows([[0.0] * 4 for _ in range(4)]))
    assert "(4, 4)" in s


def test_describe_shape_never_raises():
    """Even pathological inputs should not crash the emit path."""
    from srmech.introspect._event import describe_shape

    class Pathological:
        @property
        def shape(self):
            raise RuntimeError("hostile")

    # Property access raises → describe_shape must catch and degrade.
    assert isinstance(describe_shape(Pathological()), str)


# ─────────────────────────────────────────────────────────────────────
# native_status() — discoverable native-dispatch status (v0.5.0rc20; #743)
# ─────────────────────────────────────────────────────────────────────


def test_native_status():
    """``srmech.native_status()`` is the discoverable native-dispatch check.

    The post-rc18 replacement for poking ``srmech.amsc._native.HAS_NATIVE``
    in the TestPyPI-before-PyPI verification recipe (issue #733): a single
    top-level call, surfaced where ``dir(srmech)`` finds it, returning a
    fixed-shape dict that mirrors ``describe()['native']``.

    State-agnostic: passes in BOTH the native (wheel + libsrmech) and
    pure-Python (source-tree / Pyodide / ABI-mismatch) states — it asserts
    ONLY the contract (keys / types / cross-source agreement), never that
    ``has_native`` is True.
    """
    # Discoverable: top-level attr, in dir(), in __all__.
    assert hasattr(srmech, "native_status")
    assert callable(srmech.native_status)
    assert "native_status" in dir(srmech)
    assert "native_status" in srmech.__all__

    status = srmech.native_status()
    assert isinstance(status, dict)

    # Exactly these keys — no more, no less.
    assert set(status.keys()) == {
        "has_native",
        "dispatching",
        "abi_version",
        "expected_abi",
        "native_version",
        "load_error",
    }

    # Type contract.
    assert isinstance(status["has_native"], bool)
    assert isinstance(status["dispatching"], bool)
    assert status["abi_version"] is None or isinstance(status["abi_version"], int)
    assert isinstance(status["expected_abi"], int)
    assert status["native_version"] is None or isinstance(
        status["native_version"], str
    )
    assert status["load_error"] is None or isinstance(status["load_error"], str)

    # expected_abi is the compiled-against ABI (pinned at 3 for this line).
    assert status["expected_abi"] == 3

    # Agrees with describe()['native'] on the shared fields (single source
    # of truth: both read srmech.amsc._native).
    native = srmech.introspect.describe()["native"]
    assert status["has_native"] == native["has_native"]
    assert status["abi_version"] == native["abi_version"]
    assert status["native_version"] == native["native_version"]
