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


def test_version_is_0_5_0():
    """v0.5.0 — production graduation of the rc9–rc22 voxel arc. The final
    voxel is the `srmech mcp emit-mcpb` CLI (issue #749 / MS #19 / W13).

    Adds ``srmech mcp emit-mcpb`` (backed by ``srmech/cli/mcp.py`` +
    ``srmech/mcp/_mcpb.py``: ``build_manifest`` / ``pack_mcpb``). The
    emitted ``manifest.json`` version + ``tools[]`` are DERIVED from
    ``srmech.__version__`` and the advertised ``tool_schema`` surface
    (never a frozen literal); ``server.type`` defaults to the spec-valid
    ``"uv"`` (the host fetches the platform wheel carrying ``libsrmech``
    from PyPI at install — the portable answer to bundling a compiled
    native dep), with a ``"python"`` ``user_config``-gated fallback that
    bakes NO ``sys.executable``. An MPR attestation block carries
    ``__version__`` + a 64-hex tool-schema SHA-256 via
    ``srmech.amsc.format.sha256_bytes`` (no new ``hashlib.sha256``); the
    ``.mcpb`` is a stdlib-``zipfile`` ZIP with root ``manifest.json`` (no
    Node toolchain). NO new ToolEntry — a CLI command is not an
    ``srmech.amsc`` tool — so ``describe()`` tool total STAYS 174.
    Pure-Python; ABI unchanged at 3 (the C header VERSION strings bump to
    rc22, ``SRMECH_ABI_VERSION`` does not — no C source change). Sign /
    phase-boundary discipline preserved: no ``abs()`` (Class K pin-slot).

    (Prior rc21 — the su(3) ⊕ 3 ⊕ 3bar Lie decomposition of g2 = Der(O)
    (issue #744, wishlist).

    Added a new pure-Python qm operator ``srmech.qm.so8.an_embedding`` that
    exposes the bit-exact su(3)-module structure of the 14 g2 = Der(O)
    generators: the Lie-algebra branching 14 = 8 + 3 + 3bar (su(3) adjoint +
    fundamental + antifundamental; the 7-dim octonion-vector branches
    1 + 3 + 3bar over the same su(3)). su(3) = the stabiliser
    {D in g2 : D·e_K = 0}; the GENUINE fundamental is the +i eigenspace of
    the su(3)-INVARIANT complex structure J (J² = −I) on the 6-real-dim
    complement (a real 3-span cannot carry it — [su3, real-3] leaks ~8.3),
    so [su3, 3] ⊆ 3 is bit-exact (~3e-14). su(3) is identified by the
    INVARIANT certificate {dim 8, rank 2 via the centraliser of a regular
    element, simple (adjoint commutant dim 1)} + Killing-orthonormal total
    antisymmetry (Cartan A2) — NOT a raw-Casimir comparison. All residuals
    reduced through the scalar Class K pin-slot magnitude, never abs(). MPR
    self-attestation content-addresses the COMPUTED structure (the 14 g2
    generators' float64 bytes). +1 ToolEntry (173 -> 174). Pure-Python;
    ABI unchanged at 3 (the C header VERSION strings bump to rc21;
    SRMECH_ABI_VERSION does not — no C source change).

    Framework reading: the SAME 14-dim g2 carries TWO distinct enumerations
    — the A-N discovery partition 1 + 3 + 7 + 3 and this su(3)-Lie branching
    8 + 3 + 3bar. They are read as two languages describing the one object;
    they are explicitly NOT slot-aligned and the correspondence is NOT a
    proof (Baez §4.1 is cited for g2 = Der(O) / dim 14 ONLY — the build
    input; the branching is the op's own bit-exact self-attesting
    computation). The A-N reading is surfaced ONLY under the separately-keyed
    ``framework_an_reading`` field, tagged "framework-reading, not derived".)

    (Prior rc20 — cosmic-birefringence beta posterior AMSC catalog
    (issue #743). Added ``srmech.amsc.attested.cosmic_birefringence`` (four
    PDF-verified rows; the Eskilt & Komatsu +0.094/-0.091 asymmetric
    posterior kept as separate lo/hi half-widths, never symmetrised).
    Auto-discovered, no new tool. Pure-Python; ABI unchanged at 3.

    Prior rc19 — discoverable native-dispatch status (issue #733). Added
    top-level ``srmech.native_status()`` (also in ``__all__`` /
    ``dir(srmech)``) returning ``{has_native, dispatching, abi_version,
    expected_abi, native_version, load_error}`` — the discoverable, recipe-
    stable answer to "is the C backend loaded + ABI-matched + dispatching?",
    mirroring ``describe()['native']``. Pure-Python; ABI unchanged at 3.

    Prior rc18 — the downstream-wishlist + hygiene + perf CLEANUP rc.

    Carries the rc17 SO(8) TRIALITY voxel forward with the deterministic
    constant-returning ``srmech.qm.{octonion,so8,triality}`` builders now
    module-level cached (the public surfaces return DEFENSIVE COPIES, so the
    six bit-exact acceptance tests pass identically). Doc/accuracy fixes for
    the downstream RBS-LM wishlist (``sha256_bytes`` returns the hex digest;
    ``klein4_bundle`` accepts any count; ``weak_mixing_angle`` returns
    radians; ``_native.ABI_VERSION`` back-compat alias; cosmos references).
    Pure-Python; ABI stays 3. (The rc17 SO(8) TRIALITY voxel — three new
    qm-layer surfaces
    (``srmech.qm.octonion`` / ``srmech.qm.so8`` / ``srmech.qm.triality``)
    expose the octonion Cayley-Dickson-from-H table, the 28-generator
    ``so(8)`` adjoint (14 g2 + 7 L + 7 R), and the ``28x28`` order-3 outer
    automorphism ``tau`` with ``Fix(tau) = g2`` (dim 14 = the A-N
    ``1+3+7+3`` partition). +15 ToolEntries (158 -> 173). Plus the
    ``operator_name`` ``__module__`` hardening (rejects re-exported stdlib
    reached through a srmech module).)

    This builds on the rc16 handle dual-grammar voxel: the by-reference
    ``$srmech_handle`` id (name+uuid) + the package-scope ``srmech._handles``
    registry make the 7 ``srmech.spectral.*`` tools JSON-callable
    (handle_pending 7->0), and ``chiral_dual``'s ``op`` is accepted as a
    dotted ``srmech.*`` operator-name. This builds on the rc15 every-tool
    invocation smoke + honest mcp_callable marking (upstream §10.1).

    rc14 made all declared param TYPES JSON-coercible and shipped the
    static ``has_coercer`` ratchet. But ``has_coercer`` could not tell a
    REAL coercer from the ``_identity`` pass-through: the 7
    ``srmech.spectral.*`` tools whose surface is a bare ``SpectralHandle``
    / ``SpectralHandle | bytes`` went statically-green yet were NOT
    actually invocable across the JSON boundary (an opaque in-process
    dataclass handle cannot ride JSON by value).

    rc15 closes that gap on two fronts:

    * ``mcp_callable: bool`` on ``ToolEntry`` (default True, back-compat).
      The 7 SpectralHandle tools are marked ``mcp_callable=False`` with a
      ``mcp_unavailable_reason`` ("handle-pending: by-reference
      SpectralHandle id arrives in the bus handle-grammar (rc16)"). They
      stay in ``get_tool_schema().tools`` for introspection but are
      EXCLUDED from the advertised MCP ``tools/list`` + Anthropic catalogs
      so an LLM is never offered an uncallable tool. The spectral
      functions THEMSELVES are untouched (surface-honesty marking only).
    * THE EVERY-TOOL INVOCATION SMOKE (§10.1) —
      ``test_every_advertised_tool_invocable`` in test_mcp.py synthesises
      minimal valid args from each advertised tool's schema (rc14
      encodings per type) and actually CALLS it via ``invoke_tool``,
      asserting no binding / coercion error (tolerating domain errors that
      prove the tool was reached). The EMPIRICAL complement to rc14's
      static ratchet.

    ``srmech.introspect.describe()`` now reports the split (``total`` /
    ``mcp_callable`` / ``handle_pending`` + the handle-pending name list).
    SpectralHandle by-reference invocation is deferred to rc16 per user
    decision.

    The version-gate test stays the SINGLE deliberate human-literal gate
    (the conscious per-rc bump point); ``test_version_module_matches``
    is de-brittled (no literal) and only checks the SSoT sources AGREE,
    so it survives version bumps.

    Pure-Python; ABI unchanged at 3.

    Framework reading: the package declaring its own callable shape (which
    tools are advertisable vs handle-pending) IS Class H (self-
    introspection) at package scale — the apparatus thesis. No new
    primitive class is introduced.

    Framework reading (rc20): the cosmic-birefringence catalog is the
    parity-ODD voxel of the CMB-knowledge surface — beta is a signed,
    asymmetric quantity, and keeping the Eskilt & Komatsu +0.094/-0.091
    posterior as two separate half-widths (never abs()/symmetrised) IS the
    sign / phase-boundary discipline at the data-attestation scale.
    """
    assert srmech.__version__ == "0.5.0", (
        f"expected srmech.__version__ == '0.5.0'; got "
        f"{srmech.__version__!r}"
    )


def test_version_module_matches():
    """``srmech.version.__version__`` agrees with the package attribute.

    De-brittled 2026-05-29 — the single deliberate literal gate is
    ``test_version_is_0_5_0rcN``; this test only checks the sources
    AGREE (plus a PEP 440 sanity shape) so it survives version bumps.
    NO hardcoded ``"0.5.0rcN"`` literal here anymore.
    """
    import re

    from srmech.version import __version__ as version_str
    assert version_str == srmech.__version__
    # PEP 440 sanity: looks like a version (e.g. 0.5.0rc11 / 1.2.3).
    assert re.match(r"^\d+\.\d+\.\d+", version_str), (
        f"version {version_str!r} does not look like a version string"
    )


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
