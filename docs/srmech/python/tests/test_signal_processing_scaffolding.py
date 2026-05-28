"""Phase 1 scaffolding verification for ``srmech.signal_processing`` (v0.4.2rc1).

Verifies:

- Imports succeed (top-level package + dispatcher + registry + profiling).
- Version is ``0.4.2rc1`` across all SSoT locations.
- D=8192 locked default (conductor decision #6); optional D param works.
- `begin_cascade` context-manager API (conductor decision #5) — open /
  nested / auto-flush on exception.
- `path_registry.register` / `lookup` / `has_path` round-trip; duplicate-
  registration with a different callable raises.
- `profiling.cell_grid` enumerates the full 1920-cell benchmark grid for
  a 10-op suite at default sweeps (conductor decision #3).
- `profile_op` / `update_dispatch_table` raise
  `ProfilingNotImplementedError` (Phase 8 stub).
- `dispatch(op_name, path="verify")` raises
  `DispatcherNotImplementedError` (Phase 5 stub).
- Dispatch-table-lock-state default (locked per conductor decision #7).
- Default-path-per-class table is the 14 A-N vocabulary intact.

Discipline anchors (load-bearing for the test suite):

- 14 A-N intact per ``[[feedback_no_privileged_primitive_classes]]``.
- Identity-not-implementation per
  ``[[user_stance_identity_not_implementation_discipline]]``.
- Trauma-informed defensive scope — no clinical / military framing in
  test fixtures.
"""

from __future__ import annotations

import pytest

import srmech


# ──────────────────────────────────────────────────────────────────────
# Module-level import contract
# ──────────────────────────────────────────────────────────────────────


def test_signal_processing_imports():
    """The signal_processing sub-namespace imports successfully."""
    import srmech.signal_processing as sp  # noqa: F401
    # The most heavily-cited public symbols per plan §3.3 examples:
    from srmech.signal_processing import (  # noqa: F401
        begin_cascade,
        end_cascade,
        dispatch,
        register,
        lookup,
        has_path,
        registered_ops,
        record_profile,
        cell_grid,
        profile_op,
        update_dispatch_table,
        is_dispatch_table_locked,
        D_DEFAULT,
        SUBSTRATES,
        PATH_A,
        PATH_B,
        PATH_VERIFY,
        VALID_PATHS,
        DEFAULT_PATH_PER_CLASS,
    )


def test_submodule_imports():
    """Each Phase 1 submodule imports as a module (not just re-exports)."""
    from srmech.signal_processing import (
        cascade_dispatcher,
        path_registry,
        profiling,
        _paths,
    )
    # Sanity: each module has the expected primary surface.
    assert hasattr(cascade_dispatcher, "begin_cascade")
    assert hasattr(cascade_dispatcher, "dispatch")
    assert hasattr(cascade_dispatcher, "resolve_path")
    assert hasattr(path_registry, "register")
    assert hasattr(path_registry, "lookup")
    assert hasattr(profiling, "ProfileRecord")
    assert hasattr(profiling, "cell_grid")
    assert hasattr(_paths, "D_DEFAULT")
    assert hasattr(_paths, "SUBSTRATES")


# ──────────────────────────────────────────────────────────────────────
# Version SSoT
# ──────────────────────────────────────────────────────────────────────


def test_version_is_0_5_0rc2():
    """v0.5.0rc2 — srmech.bus C peer + real Windows named pipe + envelope fixes.

    Per user direction 2026-05-28 (continuation): three changes
    folded into one rc.

    (1) **C peer for srmech.bus** — five public symbols
        (``srmech_bus_serve`` / ``srmech_bus_server_stop`` /
        ``srmech_bus_connect`` / ``srmech_bus_send_recv`` /
        ``srmech_bus_client_close``) + one function-pointer typedef
        (``srmech_bus_handler_callback_t``). JPL-clean POSIX (AF_UNIX)
        + Windows (CreateNamedPipe via ctypes — no pywin32 dep).
        **ABI bump 2 → 3**.

    (2) **Real Windows named pipe transport** — replaces rc1's
        TCP-loopback fallback. Server creates instances at
        ``\\\\.\\pipe\\srmech-{name}`` via ``CreateNamedPipeW``;
        clients connect via ``CreateFileW``. Registry token changes
        from ``tcp 127.0.0.1 <port>`` to ``pipe \\\\.\\pipe\\srmech-{name}``.
        TCP-loopback retained as defensive fallback.

    (3) **Envelope-bug fixes from rc1's smoke test**:
        - Bug 1: handler return-shape silently dropped keys beyond
          ``type``; now the full handler dict passes through as the
          response Event's ``payload`` (so ``echo``, ``server_pid``,
          etc. survive end-to-end).
        - Bug 2: client ``send()`` over-restricted ``payload`` to
          dict; now accepts any JSON-serialisable value (string,
          list, number, None, dict).
    """
    assert srmech.__version__ == "0.5.0rc2", (
        f"expected srmech.__version__ == '0.5.0rc2'; got "
        f"{srmech.__version__!r}"
    )


def test_version_module_matches():
    """``srmech.version.__version__`` agrees with package attribute."""
    from srmech.version import __version__ as version_str
    assert version_str == "0.5.0rc2"
    assert version_str == srmech.__version__


# ──────────────────────────────────────────────────────────────────────
# Architectural constants (conductor decisions #2 / #3 / #6 / #7)
# ──────────────────────────────────────────────────────────────────────


def test_D_default_is_8192():
    """Conductor decision #6 — D=8192 locked for v0.4.2 baseline."""
    from srmech.signal_processing import D_DEFAULT
    assert D_DEFAULT == 8192


def test_D_bounds_make_sense():
    from srmech.signal_processing import D_DEFAULT, D_MIN, D_MAX
    assert D_MIN <= D_DEFAULT <= D_MAX
    assert D_MIN == 256
    assert D_MAX == 65536


def test_substrates_cover_all_four():
    """Conductor decision #2 — Phase 1 supports all 4 substrates (BCI /
    audio / RF / ephemeris), even though Phase 7 ships the catalogs."""
    from srmech.signal_processing import SUBSTRATES
    assert SUBSTRATES == ("bci", "audio", "rf", "ephemeris")
    assert len(SUBSTRATES) == 4


def test_valid_paths_are_A_B_verify():
    from srmech.signal_processing import PATH_A, PATH_B, PATH_VERIFY, VALID_PATHS
    assert PATH_A == "A"
    assert PATH_B == "B"
    assert PATH_VERIFY == "verify"
    assert set(VALID_PATHS) == {"A", "B", "verify"}


def test_dispatch_table_lock_policy_is_lock_at_release():
    """Conductor decision #7 — lock-at-release for reproducibility."""
    from srmech.signal_processing import DISPATCH_TABLE_LOCK_POLICY
    assert DISPATCH_TABLE_LOCK_POLICY == "lock-at-release"


def test_dispatch_table_is_locked_by_default_in_phase_1():
    """Phase 1 default — no learned table exists yet, table is locked."""
    from srmech.signal_processing import is_dispatch_table_locked
    assert is_dispatch_table_locked() is True


def test_dispatch_table_unlock_relock():
    """Lock-state tracking — :func:`unlock_dispatch_table` /
    :func:`lock_dispatch_table` toggle correctly."""
    from srmech.signal_processing import (
        is_dispatch_table_locked,
        lock_dispatch_table,
        unlock_dispatch_table,
    )
    assert is_dispatch_table_locked() is True
    unlock_dispatch_table()
    try:
        assert is_dispatch_table_locked() is False
    finally:
        # Restore default state so subsequent tests aren't polluted.
        lock_dispatch_table()
    assert is_dispatch_table_locked() is True


# ──────────────────────────────────────────────────────────────────────
# Default-path-per-class table (14 A-N intact)
# ──────────────────────────────────────────────────────────────────────


def test_default_path_per_class_covers_14_classes():
    """The 14 A-N vocabulary is intact; default-path table has one entry
    per class. Class K + Class M default Path B per plan §3.4; all
    others default Path A."""
    from srmech.signal_processing import (
        DEFAULT_PATH_PER_CLASS,
        PATH_A,
        PATH_B,
    )
    expected_classes = set("ABCDEFGHIJKLMN")
    assert set(DEFAULT_PATH_PER_CLASS.keys()) == expected_classes
    assert len(DEFAULT_PATH_PER_CLASS) == 14
    # Class K (rotation) + Class M (HDC) default Path B per plan §3.4.
    assert DEFAULT_PATH_PER_CLASS["K"] == PATH_B
    assert DEFAULT_PATH_PER_CLASS["M"] == PATH_B
    # All other classes default Path A.
    for cls in "ABCDEFGHIJLN":
        assert DEFAULT_PATH_PER_CLASS[cls] == PATH_A, (
            f"Class {cls} should default to Path A per plan §3.4; "
            f"got {DEFAULT_PATH_PER_CLASS[cls]!r}"
        )


# ──────────────────────────────────────────────────────────────────────
# begin_cascade context-manager (conductor decision #5)
# ──────────────────────────────────────────────────────────────────────


def test_begin_cascade_is_context_manager():
    """Conductor decision #5 — context-manager API (Pythonic; auto-flush
    on exception). Phase 1 ships the context-manager skeleton."""
    from srmech.signal_processing import begin_cascade, current_cascade
    assert current_cascade() is None
    with begin_cascade(substrate="bci") as ctx:
        assert current_cascade() is ctx
        assert ctx.substrate == "bci"
        assert ctx.depth == 0
        assert ctx.D == 8192
        assert ctx.closed is False
    assert current_cascade() is None
    assert ctx.closed is True


def test_begin_cascade_nested():
    """Nested cascades — inner wins for current_cascade()."""
    from srmech.signal_processing import begin_cascade, current_cascade
    with begin_cascade(substrate="audio") as outer:
        assert current_cascade() is outer
        with begin_cascade(substrate="rf") as inner:
            assert current_cascade() is inner
        # After inner exit, outer is back on top.
        assert current_cascade() is outer
        assert inner.closed is True
        assert outer.closed is False
    assert outer.closed is True


def test_begin_cascade_auto_flush_on_exception():
    """Conductor decision #5 — auto-flush on exception."""
    from srmech.signal_processing import begin_cascade, current_cascade

    class _CustomException(RuntimeError):
        pass

    captured_ctx = None
    with pytest.raises(_CustomException):
        with begin_cascade(substrate="ephemeris") as ctx:
            captured_ctx = ctx
            assert ctx.closed is False
            raise _CustomException("simulated cascade failure")
    # Auto-flush should have closed the cascade and popped the stack.
    assert captured_ctx is not None
    assert captured_ctx.closed is True
    assert current_cascade() is None


def test_begin_cascade_rejects_unknown_substrate():
    from srmech.signal_processing import begin_cascade
    with pytest.raises(ValueError):
        with begin_cascade(substrate="not-a-substrate"):
            pass  # pragma: no cover (ValueError fires immediately)


def test_begin_cascade_with_optional_D():
    """Conductor decision #6 — optional D param accepted for downstream
    experiments; defaults to 8192."""
    from srmech.signal_processing import begin_cascade
    with begin_cascade(substrate="bci", D=16384) as ctx:
        assert ctx.D == 16384
    with begin_cascade(substrate="bci") as ctx:
        assert ctx.D == 8192


def test_end_cascade_imperative_form():
    """`end_cascade()` is the imperative-form flush for callers that
    can't structure around `with`."""
    from srmech.signal_processing import begin_cascade, current_cascade, end_cascade
    # Open via context manager but exit early via end_cascade()
    # to confirm the imperative form is callable.
    ctx_mgr = begin_cascade(substrate="audio")
    ctx = ctx_mgr.__enter__()
    try:
        assert current_cascade() is ctx
        end_cascade(ctx)
        assert ctx.closed is True
        assert current_cascade() is None
    finally:
        # Close the cm cleanly; auto-flush is idempotent.
        ctx_mgr.__exit__(None, None, None)


# ──────────────────────────────────────────────────────────────────────
# path_registry round-trip
# ──────────────────────────────────────────────────────────────────────


def test_path_registry_register_lookup_round_trip():
    from srmech.signal_processing import (
        clear_registry,
        has_path,
        lookup,
        register,
        UnknownOperationError,
    )

    clear_registry()

    def _fake_path_a(*args, **kwargs):
        return ("path_a", args, kwargs)

    def _fake_path_b(*args, **kwargs):
        return ("path_b", args, kwargs)

    try:
        # Register Path A.
        register(
            "fake_op",
            path="A",
            impl=_fake_path_a,
            ssot_citation="test fixture",
            classes=("L",),
        )
        assert has_path("fake_op", "A") is True
        assert has_path("fake_op", "B") is False
        entry = lookup("fake_op")
        assert entry.op_name == "fake_op"
        assert entry.path_a is _fake_path_a
        assert entry.path_b is None
        assert entry.classes == ("L",)

        # Register Path B (merges into the existing entry).
        register(
            "fake_op",
            path="B",
            impl=_fake_path_b,
        )
        assert has_path("fake_op", "A") is True
        assert has_path("fake_op", "B") is True
        entry = lookup("fake_op")
        assert entry.path_a is _fake_path_a
        assert entry.path_b is _fake_path_b
        # ssot_citation + classes preserved from initial registration.
        assert entry.ssot_citation == "test fixture"
        assert entry.classes == ("L",)

        # Unknown op raises.
        with pytest.raises(UnknownOperationError):
            lookup("nonexistent_op")
    finally:
        clear_registry()


def test_path_registry_duplicate_registration_with_different_callable_raises():
    from srmech.signal_processing import (
        DuplicateRegistrationError,
        clear_registry,
        register,
    )

    clear_registry()

    def _impl_one(*args, **kwargs):
        return 1

    def _impl_two(*args, **kwargs):
        return 2

    try:
        register("dup_op", path="A", impl=_impl_one)
        # Idempotent re-registration with the same callable is allowed.
        register("dup_op", path="A", impl=_impl_one)
        # Different callable raises.
        with pytest.raises(DuplicateRegistrationError):
            register("dup_op", path="A", impl=_impl_two)
    finally:
        clear_registry()


def test_path_registry_register_invalid_path_raises():
    from srmech.signal_processing import clear_registry, register
    clear_registry()
    with pytest.raises(ValueError):
        # "verify" is dispatcher-side only; not a registration path.
        register("op", path="verify", impl=lambda *a, **k: None)
    with pytest.raises(ValueError):
        register("op", path="Z", impl=lambda *a, **k: None)


def test_path_registry_registered_ops_iteration():
    from srmech.signal_processing import (
        clear_registry,
        register,
        registered_ops,
    )
    clear_registry()
    try:
        for name in ("alpha", "beta", "gamma"):
            register(name, path="A", impl=lambda *a, **k: None)
        assert tuple(registered_ops()) == ("alpha", "beta", "gamma")
    finally:
        clear_registry()


# ──────────────────────────────────────────────────────────────────────
# Dispatcher API
# ──────────────────────────────────────────────────────────────────────


def test_dispatch_unknown_op_raises():
    from srmech.signal_processing import dispatch
    from srmech.signal_processing.path_registry import UnknownOperationError
    with pytest.raises(UnknownOperationError):
        dispatch("not_registered_in_phase_1")


def test_dispatch_verify_raises_in_phase_1():
    """Phase 5 lands `path='verify'`; Phase 1 stub raises."""
    from srmech.signal_processing import (
        DispatcherNotImplementedError,
        clear_registry,
        dispatch,
        register,
    )
    clear_registry()

    def _stub(*args, **kwargs):
        return None

    try:
        register("verify_test_op", path="A", impl=_stub)
        register("verify_test_op", path="B", impl=_stub)
        with pytest.raises(DispatcherNotImplementedError):
            dispatch("verify_test_op", path="verify")
    finally:
        clear_registry()


def test_dispatch_invalid_path_raises():
    from srmech.signal_processing import (
        clear_registry,
        dispatch,
        register,
    )
    clear_registry()
    try:
        register("bad_path_op", path="A", impl=lambda *a, **k: None)
        with pytest.raises(ValueError):
            dispatch("bad_path_op", path="Z")
    finally:
        clear_registry()


def test_dispatch_routes_to_path_A_by_default():
    """Phase 1 default — Path A unless cascade-hint or class-K/M."""
    from srmech.signal_processing import (
        clear_registry,
        dispatch,
        register,
    )

    clear_registry()
    sentinel_a = "path_a_was_called"
    sentinel_b = "path_b_was_called"

    def _impl_a(*args, **kwargs):
        return sentinel_a

    def _impl_b(*args, **kwargs):
        return sentinel_b

    try:
        # Class L op (Laplacian) — defaults to Path A per plan §3.4.
        register(
            "default_route_op",
            path="A",
            impl=_impl_a,
            classes=("L",),
        )
        register("default_route_op", path="B", impl=_impl_b)
        result = dispatch("default_route_op")
        assert result == sentinel_a
    finally:
        clear_registry()


def test_dispatch_routes_to_path_B_inside_cascade():
    """Plan §3.1 criterion #2 — cascade-hint mode prefers Path B."""
    from srmech.signal_processing import (
        begin_cascade,
        clear_registry,
        dispatch,
        register,
    )

    clear_registry()
    sentinel_a = "path_a_was_called"
    sentinel_b = "path_b_was_called"

    def _impl_a(*args, **kwargs):
        return sentinel_a

    def _impl_b(*args, **kwargs):
        return sentinel_b

    try:
        register(
            "cascade_route_op",
            path="A",
            impl=_impl_a,
            classes=("L",),
        )
        register("cascade_route_op", path="B", impl=_impl_b)
        # Outside cascade → Path A.
        assert dispatch("cascade_route_op") == sentinel_a
        # Inside cascade → Path B.
        with begin_cascade(substrate="audio"):
            assert dispatch("cascade_route_op") == sentinel_b
    finally:
        clear_registry()


def test_dispatch_explicit_path_override_always_honoured():
    """Plan §3.4 — override always honoured (Phase 4 acceptance criterion)."""
    from srmech.signal_processing import (
        clear_registry,
        dispatch,
        register,
    )

    clear_registry()
    sentinel_a = "path_a"
    sentinel_b = "path_b"

    try:
        register(
            "override_op",
            path="A",
            impl=lambda *a, **k: sentinel_a,
            classes=("L",),
        )
        register("override_op", path="B", impl=lambda *a, **k: sentinel_b)
        assert dispatch("override_op", path="A") == sentinel_a
        assert dispatch("override_op", path="B") == sentinel_b
    finally:
        clear_registry()


def test_dispatch_forwards_D_parameter():
    """Conductor decision #6 — D=8192 locked default; optional D param
    forwarded by dispatcher to ops that accept it."""
    from srmech.signal_processing import (
        clear_registry,
        dispatch,
        register,
    )

    clear_registry()
    captured = {}

    def _impl_with_D(x, *, D=8192, **kwargs):
        captured["D"] = D
        return x

    try:
        register("D_forward_op", path="A", impl=_impl_with_D, classes=("L",))
        dispatch("D_forward_op", 42)
        assert captured["D"] == 8192
        dispatch("D_forward_op", 42, D=16384)
        assert captured["D"] == 16384
    finally:
        clear_registry()


def test_dispatch_does_not_force_D_on_callables_without_D():
    """Phase 1 ergonomics — Path A ops that don't accept D shouldn't
    error; the dispatcher should detect signature and skip injection."""
    from srmech.signal_processing import (
        clear_registry,
        dispatch,
        register,
    )

    clear_registry()
    captured = {}

    def _impl_no_D(x):  # no **kwargs, no D param
        captured["x"] = x
        return x

    try:
        register("no_D_op", path="A", impl=_impl_no_D, classes=("L",))
        # Should not raise TypeError("unexpected keyword argument 'D'").
        result = dispatch("no_D_op", 42)
        assert result == 42
        assert captured["x"] == 42
    finally:
        clear_registry()


def test_resolve_path_explicit_override():
    from srmech.signal_processing import resolve_path
    assert resolve_path("any_op", explicit_path="A") == "A"
    assert resolve_path("any_op", explicit_path="B") == "B"
    assert resolve_path("any_op", explicit_path="verify") == "verify"


def test_resolve_path_invalid_explicit_raises():
    from srmech.signal_processing import resolve_path
    with pytest.raises(ValueError):
        resolve_path("any_op", explicit_path="Z")


def test_resolve_path_unknown_op_defaults_to_path_A():
    """Phase 1 fallback — unknown op (no class info) defaults Path A."""
    from srmech.signal_processing import clear_registry, resolve_path
    clear_registry()
    assert resolve_path("unknown_in_phase_1") == "A"


# ──────────────────────────────────────────────────────────────────────
# Profiling API (Phase 8 stubs)
# ──────────────────────────────────────────────────────────────────────


def test_cell_grid_enumerates_1920_cells_for_10_ops():
    """Conductor decision #3 — full per-op × per-cascade-depth ×
    per-substrate granularity. Default sweeps produce
    10 ops × 6 sizes × 4 depths × 4 substrates × 2 paths = 1920 cells."""
    from srmech.signal_processing import cell_grid
    op_names = tuple(f"op_{i}" for i in range(10))
    cells = list(cell_grid(op_names=op_names))
    assert len(cells) == 1920, (
        f"expected 1920 cells (10×6×4×4×2 per plan §5.1); got {len(cells)}"
    )


def test_cell_grid_one_op_default_sweeps():
    """Single op at defaults yields 6×4×4×2 = 192 cells."""
    from srmech.signal_processing import cell_grid
    cells = list(cell_grid(op_names=("fft",)))
    assert len(cells) == 192


def test_cell_grid_covers_all_substrates():
    """Each substrate appears in the enumerated grid."""
    from srmech.signal_processing import cell_grid, SUBSTRATES
    cells = list(cell_grid(op_names=("fft",)))
    substrates_seen = {c.substrate for c in cells}
    assert substrates_seen == set(SUBSTRATES)


def test_profile_op_raises_in_phase_1():
    """Phase 8 lands the runner; Phase 1 stub raises."""
    from srmech.signal_processing import (
        ProfilingNotImplementedError,
        profile_op,
    )
    with pytest.raises(ProfilingNotImplementedError):
        profile_op("fft")


def test_update_dispatch_table_raises_in_phase_1():
    """Phase 8 lands the regression pipeline; Phase 1 stub raises."""
    from srmech.signal_processing import (
        ProfilingNotImplementedError,
        update_dispatch_table,
    )
    with pytest.raises(ProfilingNotImplementedError):
        update_dispatch_table()


def test_profile_record_ndjson_serialisation():
    """ProfileRecord serialises to one NDJSON line per
    ``[[feedback_ndjson_over_bloated_json]]``."""
    import json

    from srmech.signal_processing import (
        ProfileCellKey,
        ProfileRecord,
    )

    key = ProfileCellKey(
        op_name="fft",
        path="A",
        input_size=1024,
        cascade_depth=1,
        substrate="audio",
    )
    record = ProfileRecord(
        key=key,
        wall_time_s=0.001234,
        cpu_time_s=0.001100,
        memory_bytes=4096,
        n_repeats=5,
        notes="phase-1 unit test fixture",
    )
    line = record.to_ndjson_line()
    # No embedded newline (NDJSON contract).
    assert "\n" not in line
    parsed = json.loads(line)
    assert parsed["op_name"] == "fft"
    assert parsed["path"] == "A"
    assert parsed["input_size"] == 1024
    assert parsed["cascade_depth"] == 1
    assert parsed["substrate"] == "audio"
    assert parsed["wall_time_s"] == 0.001234
    assert parsed["n_repeats"] == 5


def test_profiling_record_buffer_round_trip():
    """In-memory record buffer round-trip — record / iter / clear."""
    from srmech.signal_processing import (
        ProfileCellKey,
        ProfileRecord,
        clear_records,
        iter_records,
        record_profile,
    )

    clear_records()
    key = ProfileCellKey(
        op_name="fft", path="A", input_size=256,
        cascade_depth=1, substrate="bci",
    )
    rec = ProfileRecord(key=key, wall_time_s=0.001, cpu_time_s=0.001)
    record_profile(rec)
    out = list(iter_records())
    assert len(out) == 1
    assert out[0] is rec
    clear_records()
    assert list(iter_records()) == []


# ──────────────────────────────────────────────────────────────────────
# Locked-dispatch-table path on disk
# ──────────────────────────────────────────────────────────────────────


def test_learned_dispatch_table_path_exists_and_is_empty():
    """Phase 1 ships an empty NDJSON at the locked path; Phase 8 populates."""
    from srmech.signal_processing import LEARNED_DISPATCH_TABLE_PATH
    assert LEARNED_DISPATCH_TABLE_PATH.exists(), (
        f"locked dispatch-table path should exist for Phase 1 (empty "
        f"placeholder); got {LEARNED_DISPATCH_TABLE_PATH!r}"
    )
    content = LEARNED_DISPATCH_TABLE_PATH.read_text(encoding="utf-8")
    # Empty file — Phase 8 will populate with regression-fit entries.
    assert content == "" or content.strip() == ""


# ──────────────────────────────────────────────────────────────────────
# Discipline checks (14 A-N intact + identity-not-implementation)
# ──────────────────────────────────────────────────────────────────────


def test_no_new_primitive_class_introduced():
    """14 A-N vocabulary intact per
    ``[[feedback_no_privileged_primitive_classes]]``. The Phase 1
    DEFAULT_PATH_PER_CLASS table uses exactly the 14 classes A-N; no
    extra entries (no Class O / P / Q / etc.)."""
    from srmech.signal_processing import DEFAULT_PATH_PER_CLASS
    keys = set(DEFAULT_PATH_PER_CLASS.keys())
    assert keys == set("ABCDEFGHIJKLMN")
    # Explicit no-O check — Class O was dissolved into Class L per
    # `[[feedback_no_privileged_primitive_classes]]` (2026-05-16).
    assert "O" not in keys
