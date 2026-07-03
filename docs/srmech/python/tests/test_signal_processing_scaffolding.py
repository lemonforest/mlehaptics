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


def test_version_is_0_7_0rc10():
    """v0.7.0rc10 — F292 graft #1: the N-way SIMD SHA-256 BATCH
    (`srmech.amsc.format.sha256_batch`), folding the F292 perf-engineering
    hand-down into v0.7.0. cpuminer's N-way-lane TECHNIQUE re-implemented
    JPL-clean in `c/src/srmech_sha256_batch.c`: a runtime cpuid dispatch to
    AVX2 8-way / SSE2 4-way (scalar fallback for the remainder / non-x86 /
    Pyodide), each lane stepping its own message's blocks in SIMD lockstep
    with a per-lane mask freezing finished (shorter) messages. Every tier
    is bit-exact with the single-stream `sha256_hex_c` / hashlib / NIST KATs
    (all three proven locally via the SRMECH_SHA256_FORCE_TIER hook). SCOPE:
    energy/perf of srmech's own provenance hashing — NOT mining (SHA-256 has
    no PoW shortcut; technique attested to FIPS 180-4 / Intel / Gueron-
    Krasnov). +1 ToolEntry ⟹ `describe()` 194; a NEW symbol ⟹ ABI stays 3
    (additive); no `-mavx2` global (the AVX2 kernel self-isolates via the
    target attribute).

    Prior v0.7.0rc9 — MS #21 rc9 voxel: the v0.7.0 graduation-prep PyPI
    description refresh (the genuinely-last rcN before the clean v0.7.0
    cut). The PyPI ``Summary`` now names the v0.7.0 headlines it had been
    missing — the **Moufang loop-bind** octonion family (loop-bind / 7-D
    cross / G_2 3-form; rc1–rc7) and the **Wiener-Khinchin autocorrelation**
    (rc8) — alongside the preserved 28-dim so(8) = 14 g_2 + 14 L/R octonion
    / Spin(8)-triality spine, trimmed to 472 chars (under the 480 soft / 512
    hard PyPI limit), byte-IDENTICAL in pyproject.toml + pyproject-pure.toml
    (the publish-workflow drift guard). Description-only: NO code change, so
    ``describe()`` stays 193, the DSL catalog stays 11 ops, ABI stays 3.

    Prior v0.7.0rc8 — MS #21 rc8 voxel: the Class-L circular autocorrelation
    primitive (the F290 §C un-flatten Wiener-Khinchin op) shipped CO-EQUAL
    in Python AND C. ``srmech.amsc.cascade.autocorrelation(x)`` returns the
    circular autocorrelation r[k] = Σ_i x[i]·x[(i+k) mod n] (r[0] = Σ x² =
    energy) = Re(IFFT(|FFT(x)|²)) — the Wiener-Khinchin identity that makes
    it Class L. The Python wrapper uses the fast numpy FFT; the native peer
    ``srmech_autocorrelation_f64`` (c/src/srmech_autocorr.c) computes the
    DIRECT O(n²) multiply-add sum — the same object, JPL-clean (no FFT, so
    no recursion / no transcendentals). +1 ToolEntry ⟹ ``describe()`` total
    193; +1 cascade-catalog op ⟹ 11 DSL ops; a new symbol only ⟹ ABI stays
    3 (additive). Unblocks the F290 §C un-flatten composite (autocorr ->
    difference-graph -> conservation-validate) as pure-TOML over named ops.

    Prior v0.7.0rc7 — MS #21 rc7 voxel: the co-equal C peer for the octonion
    loop-bind family (the Python→C transpile). ``c/src/srmech_loopbind.c`` ports
    the dim-8 octonion (Cayley-Dickson) product loop_bind + loop_conj / loop_inv /
    cross7 / g2_three_form to native ``srmech_loop_*_f64`` symbols — recursion-free
    (a fixed real→complex→quaternion→octonion call DAG), bit-exact with the Python
    ``_loop_bind_raw``. ``srmech.amsc.hdc`` dispatches the five public ops to C for
    the n==8 octonion; the HD block wrappers inherit native per-block for free. New
    symbols only ⟹ ABI stays 3 (additive); no new ToolEntry ⟹ ``describe()`` stays
    192. JPL Power-of-Ten clean (no recursion/malloc/goto; ≤60-line functions; ≥2
    asserts each; gcc/clang/MSVC -Werror/-WX).

    Prior v0.7.0rc6 — MS #21 rc6 voxel: bring-your-own (BYO) cascade-TOML (F289 D2).
    A domain specialist drops ``*.toml`` cascade descriptors in a dir and
    registers it (``srmech.dsl.register_catalog_dir``) — or points
    ``SRMECH_CASCADE_PATH`` at it — and the ops resolve / run / surface
    identically to shipped ops, flagged ``provenance="user"`` (B-tier, attested
    to their own descriptor hash). A user descriptor may be a PURE-TOML composite
    (a ``[composite]`` body = a chain of named ops, no Python) or a primitive; it
    may NOT shadow a shipped op-name (raises at load) and composites validate at
    load (referenced ops resolve + the graph is acyclic). Config API only —
    ``describe()`` stays 192; ABI stays 3 (pure-Python).

    Prior v0.7.0rc5 — MS #21 rc5 voxel: the per-block HD Moufang-division family +
    the loop_inv/loop_conj HD footgun guard (F-§12.1 / §12.2). Adds to
    ``srmech.amsc.hdc``: ``loop_conj_hd`` (the missing per-block conjugate atom),
    ``loop_inv_hd`` (per-block Moufang inverse), and ``loop_runbind_hd`` (per-block
    RIGHT-division b_k·conj(a_k) — peels the right factor for a left-fold sequence
    store; runbind recovers v to <1e-15). The single-element ``loop_inv`` /
    ``loop_conj`` now RAISE on an HD block-octonion vector (a multiple of 8 wider
    than one octonion) instead of being silently wrong — 2048 = 256·8 is also a
    power of two, so the global conj/inv used to pass _as_loop unflagged. +3
    ToolEntries ⟹ ``describe()`` total 192; ABI stays 3 (pure-Python; the co-equal
    C peer is the arc's transpile-to-C step).

    Prior v0.7.0rc4 — MS #21 rc4 voxel: the block-octonion HD tiling (#811) +
    capacity-free vs Klein-4 (#812). Adds to ``srmech.amsc.hdc``: ``loop_bind_hd``
    = the direct sum ⊕ of 256 independent dim-8 octonion loop_binds (D=2048;
    block-DIAGONAL, no coupling — block err 0.0) and ``loop_unbind_hd`` = per-block
    Moufang left-division (recovers v to 2.9e-15 on unit blocks). Ground-truth
    computed FROM the shipped loop_bind (F289), so it agrees with rc1 by
    construction; the bind is M (per-block loop_bind) over a direct-sum TILE — NO
    new class. Capacity-free verdict (owned, F289/F277): loop-bind ≥ Klein-4 at
    matched D — order/tree/direction at no capacity cost. +2 ToolEntries ⟹
    ``describe()`` total 189; ABI stays 3 (pure-Python; the co-equal C peer is the
    arc's transpile-to-C step).

    Prior v0.7.0rc3 — MS #21 rc3 voxel: the loop-bind family slots into the compose
    engine (#813). PROOF, no new surface: the octonion ops resolve dynamically as
    ``class="M", op="<name>"`` against ``DEFAULT_CLASS_REGISTRY`` (M →
    ``srmech.amsc.hdc``), so ``loop_bind`` / ``loop_conj`` / ``loop_associator`` /
    ``cross7`` / ``g2_three_form`` run through ``srmech.amsc.compose.run_chain``
    (the M∘C-with-K-residue cascade #813 describes; a multi-step ``@step[0]`` M∘C
    chain included). Test-only voxel: NO new ToolEntries (``describe()`` stays
    187), NO new class, ABI stays 3 (pure-Python). The shipped cascade-catalog
    descriptor for the bind carries a C symbol, so it rides with the C-transpile
    step at the end of the arc.

    Prior v0.7.0rc2 — MS #21 rc2 voxel: the 7-D cross product + the G₂ associative
    3-form, the gauge ARITHMETIC's companion invariants (#813 / F281). Adds to
    ``srmech.amsc.hdc``: ``cross7(x,y) = Im(loop_bind(x,y))`` (M∘C) and
    ``g2_three_form(x,y,z) = ⟨x, cross7(y,z)⟩`` ((M∘C)∘⟨·,·⟩) — ground-truth
    computed FROM the shipped loop_bind, so both agree with the rc1 bind by
    construction (no convention guess). The owned triality VERDICT lands as a
    test: ``dim Der(loop_bind) = 14`` (= G₂) and a generic O(8) rotation BREAKS
    the bind ⟹ triality does NOT preserve the bind; the 14-dim G₂ does (F281).
    NO new class; Class O stays dissolved. +2 ToolEntries ⟹ ``describe()`` total
    187; ABI stays 3 (pure-Python; the co-equal C peer is a later voxel).

    Prior v0.7.0rc1 — MS #21 loop-bind (Moufang) voxel: the k=7 gauge ARITHMETIC
    the triality SYMMETRY is blind to (#814 / F271). The first v0.7.0 voxel
    ports the ``loop_bind_moufang.py`` research oracle into ``srmech.amsc.hdc``:
    ``loop_bind`` (the octonion / Cayley-Dickson product), ``loop_conj``,
    ``loop_inv`` (the Moufang-division unbind), ``loop_left_op``/``loop_right_op``
    (the (4:3)|(3:4) L/R order-chirality), and ``loop_associator`` (the Class-K
    residue (ab)c−a(bc), zero on a Fano line). M∘C-with-a-Class-K-residue — NO
    new class (the 14 A–N hold; Class O stays dissolved); structure = the
    Moufang loop. Canonical SSoT Baez 2002. +6 ToolEntries ⟹ ``describe()``
    total 185; ABI stays 3 (pure-Python; the co-equal C peer is a later voxel).

    Prior v0.6.0 — PRODUCTION GRADUATION of the rc1–rc21 lean-ISA voxel arc to
    PyPI. The clean (non-rc) tag promotes the rc21 state already verified-green
    on TestPyPI; the only delta is this version string + the CHANGELOG
    graduation entry, and the full pedantic-C + test + pure-wheel CI matrix
    re-verifies the 0.6.0 build before the production tag. The arc: the
    ``cascade.atoms`` / ``cascade.compose`` two-tier lean-ISA split (#751); the
    ``srmech.qm.so8`` / ``srmech.qm.triality`` engine (28-dim adjoint + order-3
    outer automorphism + ``Fix(tau)=g₂=14`` + ``quaternion_subalgebra_stabilizer``
    + ``lean_isa_seventh_primitive``); the reentrant C core (#772); the Klein-4
    four-sector ``parallel_sector_dispatch`` (+ C peer) made chainable; the
    generalised Kuramoto-Sakaguchi step (co-equal Python + C); and the rc16–rc21
    triality voxel sub-arc (combinator-kernel closure → ``klein4_triality_cycle``
    Python + co-equal C → worked instance → coherence ratchet → MFO §VII.6.22
    H-gate rung). ``describe()`` total 179; ABI 3.

    Prior v0.6.0rc21 — MS #20 H-gate / triality MFO rung voxel (the meaning-tier
    closer): MFO notebook §VII.6.22 connects the rc16–rc20 triality voxel-arc to
    the §VII.6.21 Rosetta-table H-gate / fix-rotate axis — the order-3
    ``klein4_triality_cycle`` (rc17 Python + rc18 C) IS the discrete-cyclic
    rotate-operator whose continuous-Hopf companion ``tau`` fixes g₂=14 (the
    §VII.6.21.4 frame-invariant), with ``klein4_similarity`` the H gate, and the
    discrete triality CLOSES (T³=id, no Class-N leak) where the continuous
    epicycle leaks. DOC only (MFO notebook) — no code, no new symbol/ToolEntry
    (``describe()`` total stays 179); ABI stays 3.

    Prior v0.6.0rc20 — MS #20 SSoT two-tier coherence-ratchet voxel: a new
    ``tests/test_ssot_coherence_scan.py`` scans the continuum tier and asserts
    the two-tier SSoT stays coherent as it grows — every
    ``worked_instances/*.toml`` is well-formed, every op it references resolves
    to a real callable, the kernel (worked-instance names) and continuum
    (cascade DSL catalog) name-spaces stay DISJOINT, and every cascade-catalog
    op still resolves. The rc19 triality TOML gains a machine-readable
    ``[worked_instance.ops]`` table for the scan. DOC + TEST only; no new
    symbol/ToolEntry (``describe()`` total stays 179); ABI stays 3.

    Prior v0.6.0rc19 — MS #20 triality S₃=Aut(V₄) worked-instance voxel (the
    continuum-tier instantiation): a worked cascade INSTANCE
    (``_research/worked_instances/triality_s3_klein4.toml``) + its executable
    attestation (``test_triality_s3_worked_instance.py``) showing
    ``klein4_triality_cycle`` IS the order-3 generator of Aut(V₄)=S₃ — via the
    conjugation ``T ∘ XOR_a ∘ T⁻¹ = XOR_{T(a)}`` cyclically permuting the three
    klein4 flips (iω₇ → γ₅ → CPT). The klein4 ops stay KERNEL-tier (hdc; NOT
    re-exported to the DSL cascade catalog); the TOML is the continuum-tier
    *instance*, verified in Python against the real ops. DOC + TEST only; no new
    symbol/ToolEntry (``describe()`` total stays 179); ABI stays 3; JPL ratchet 0.

    Prior v0.6.0rc18 — MS #20 klein4-triality-cycle C peer voxel (the A-arc's
    silicon tier): the co-equal native symbol ``srmech_klein4_triality_cycle``
    (in ``srmech_hdc.c``) computes the identical order-3 ``S₃ = Aut(V₄)``
    relabel as the rc17 Python op — additive symbol → **ABI stays 3**;
    JPL-clean (≤60-line, ≥2-assert, no malloc/goto); bound under its own
    ctypes ``hasattr`` so a pre-rc18 klein4 lib still loads. Differential
    C↔Python parity-tested both directions. No new ToolEntry (``describe()``
    total stays 179). NEVER a Python callback.

    Prior v0.6.0rc17 — MS #20 klein4-triality-cycle voxel (the A-arc's first code):
    ``srmech.amsc.hdc.klein4_triality_cycle`` — the order-3 ``S₃ = Aut(V₄)``
    generator cycling the three Klein-4 involutions ``iω₇(1) → γ₅(2) → CPT(3)``
    (identity fixed), the V₄-carrier image of the so(8) ``8v → 8s → 8c``
    triality (``srmech.qm.triality.triality_cycle``). The "third axis" (F182)
    the three order-2 flips cannot reach — order-3 cycling, NOT a fourth
    order-2 chirality. Class I; pure uint8 relabel (no sign / no ``abs()``);
    ``T∘T∘T = id``, ``T² = T⁻¹``. Pure-Python (co-equal C peer is rc18); +1
    ToolEntry → ``describe()`` total 179; ABI stays 3.

    Prior v0.6.0rc16 — MS #20 combinator-kernel-closure voxel (B-boundary
    codification): the cascade DSL's FIVE control-flow combinators (``then`` /
    ``loop`` / ``fold`` / ``reduce`` / ``parallel``) are RATIFIED as a CLOSED,
    FINITE kernel — the finite anharmonic-kernel tier of the two-tier SSoT
    (kernel HARDCODED in code + co-equally in C; the asymptotic cascade
    INSTANCES it sequences live as TOML op-descriptors — "you can't hardcode a
    continuum"). Closure is DESIGN-ENFORCED (data-dependent while/unfold
    iteration is exiled to the op-instance layer; a 6th form would be a
    conscious widening). DOC + TEST only: a new
    ``test_combinator_kernel_closure.py`` pins the five-builder ⇆
    five-discriminator bijection + the |V₄|=4 Klein-4 cap; the ``_control_flow``
    docstring carries the two-tier statement. No DSL behaviour change; no C
    touched; ABI stays 3; ``describe()`` total stays 178.

    Prior v0.6.0rc15 — MS #20 self-recognition reads voxel: top-level
    ``srmech.describe()`` (graduated from ``srmech.introspect``) + fuzzy
    ``ToolSchema.resolve()`` / ``resolve_all()`` (bare-leaf / dotted-suffix →
    FQN) + iterable ``ToolSchema`` (``for t in schema`` / ``len``). Pure-Python
    introspection surface; ABI stays 3; ``describe()`` total stays 178.

    Prior v0.6.0rc14 — MS #20 kuramoto matrix-step voxel (§11.1 forward-ask):
    ``kuramoto_step`` gains the GENERALISED Kuramoto-Sakaguchi step —
    ``adjacency`` (n×n coupling matrix; non-symmetric → directed, Laplacian →
    graph-structured; None → all-to-all uniform K/n), ``alpha`` (Sakaguchi
    phase frustration sin(θ_j−θ_i−α)), and per-oscillator pinning
    (``pin_anchor`` + ``pin_strength``: + p_i·sin(ψ_i−θ_i)). Defaults
    reproduce the plain step byte-for-byte. The FIRST C-touching rc of the
    §11 arc: a CO-EQUAL standalone-C peer
    ``srmech_cascade_kuramoto_step_general_f64`` (additive symbol → ABI stays
    3; JPL-clean; NULL adjacency → uniform, NULL pin → none; NO Python
    callback) computes the identical step, differential-tested vs the Python
    fallback to libm-trig tolerance. The 3 new kuramoto ToolEntry params
    (adjacency/alpha/pin_anchor/pin_strength) keep describe() at 178. No
    ``abs()`` (sin coupling + Σ-reduce + Class-C Euler add + Class-C α offset
    + Class-C/M pin).

    Prior v0.6.0rc13 — MS #20 klein4 sectors-flag voxel (§11.3 forward-ask):
    the ``srmech.amsc.hdc.klein4_bind`` / ``klein4_bundle`` / ``klein4_similarity``
    HDC ops get an optional ``sectors=`` / ``parallel=`` / ``mode=`` flag that
    fans the op across ≤4 concurrent lanes (default-ON when ``os.cpu_count() >=
    4``). TWO modes: ``mode="chunk"`` (default) data-parallel position-slices,
    BIT-IDENTICAL to serial; ``mode="chirality"`` the F233 4-sector dispatch
    using klein4's OWN XOR sector-flips (γ₅ XOR 2 / iω₇ XOR 1 / CPT XOR 3) +
    klein4_bundle recombine (similarity recombines via sector-0 = value-
    transparent). All defaults are value-preserving, so default-on changes only
    the execution path. Pure-Python orchestration over the pure-Python/numpy
    klein4 ops — CO-EQUAL PARITY: it does NOT route through the C peer; a
    standalone-C klein4 sector dispatch (C bodies, no Python callback) is the
    tracked follow-up. No new ToolEntry (``describe()`` stays 178; the 3 klein4
    entries gain sectors/parallel/mode params); ABI unchanged at 3; no ``abs()``.

    Prior v0.6.0rc12 — MS #20 parallel-composability voxel (§11.3 DEV-UPDATE):
    parallel_sector_dispatch becomes CHAINABLE / NESTABLE. The Klein-4
    four-sector dispatch was a *leaf* introspection-Dict tool — feeding its
    output (or the per-sector list) back into another sector dispatch
    crashed (`unary -: 'list'`), so the 4-way splay applied at ONE level
    only and did not carry through a chained cascade. rc12 adds an optional
    `combine=` recombine (`bundle`/`mean`/`sector0`/`concat`/callable) +
    `result["combined"]` + a `sectorize()` nesting wrapper; the DSL
    `parallel_sectors` stage recombines by DEFAULT (`combine="bundle"`) so
    it is `stream → stream` and chains / nests like loop/fold/reduce
    (`combine=None` keeps the terminal per-sector list, guarded against
    chaining-past). The TOML `parallel_body=` gains `combine=`. Also fixes
    a stale top-help string (now enumerates all four subcommands
    status/bus/dsl/mcp). No new ToolEntry → describe() tool total stays 178;
    ABI unchanged at 3; pure-Python.

    Prior v0.6.0rc11 — MS #20 DSL parallel-discriminator voxel: the Klein-4
    four-sector fan-out parallel_sector_dispatch becomes a first-class
    chain special form (chain.parallel_sectors / `parallel_body=`),
    alongside loop/fold/reduce — it is a 1→N fan-out COMBINATOR
    (kind='combinator'), not a plain `op=` value→value stage. The
    cascade catalog gains a `kind` field; list_catalog_ops + `srmech dsl
    ops` + the tool_schema summaries surface it; using the combinator as
    `op=` raises a guided error pointing at the `parallel` discriminator.
    No new ToolEntry → describe() tool total stays 178; ABI unchanged at 3.

    Prior v0.6.0rc10 — MS #20 release-prep doc-hygiene voxel: the two v0.6.0
    cascade ops get their cascade-catalog TOML descriptors
    (parallel_sector_dispatch + kuramoto_step → srmech.dsl catalog now 10
    descriptors), and the PyPI README / subtree CLAUDE.md / C README +
    JPL_AUDIT / research notebook §3.28 are brought current with the
    v0.5.0 + v0.6.0 shipped state. No runtime change; describe() tool
    total stays 178; ABI unchanged at 3.

    Prior v0.6.0rc9 — MS #20 parity voxel (#778 follow-on): the Kuramoto
    coupled-oscillator forward-Euler step gets a native C peer. Closes a
    C/Python parity gap — the dispatch-clock Euler integration the
    spectral-research arc hand-rolled in Python (F141/F231/R-95/F234) had
    NO srmech_* primitive, so srmech could not run the Kuramoto step under
    its full-parity commitment (no host Python). Adds
    srmech_cascade_kuramoto_step_f64 (one forward-Euler step:
    theta_i <- theta_i + dt*(omega_i + (K/n)*Σ_j sin(theta_j - theta_i));
    O(n²) sin-coupling native, libm sin like kepler.c; JPL-clean, no
    malloc/goto, ≥2 asserts) + the Python peer
    srmech.amsc.cascade.kuramoto_step (dispatch-to-C when HAS_NATIVE,
    pure-Python fallback; libm-trig TOLERANCE parity, same coupling-sum
    index order). Honest cascade shape: Class I cyclic phase + sin coupling
    + sum-reduce + Class-C Euler add; NOT a new privileged primitive. No
    abs(). +1 ToolEntry → describe() tool total 177 → 178; ABI unchanged
    at 3 (additive C symbol). n==1 is pure drift; n==0 is [].

    Prior v0.6.0rc8 — MS #20 slowdown-fix voxel (#778/#771): the Klein-4
    four-sector parallel dispatch no longer SLOWS DOWN vs serial. TWO defects
    fixed (both Python-side; the C dispatch was already correct — create-all-
    then-join-all). (1) The native shim _native.cascade_parallel_sector_dispatch_c
    ran N serial n_sectors=1 calls (the rc7 "GIL-hazard" workaround) → ZERO
    cross-sector concurrency (0.99× vs serial); now ONE n_sectors=N threaded C
    call, so the ≤4 sector callbacks OVERLAP for a GIL-releasing body (measured
    ~4× on a sleep body — ctypes holds the GIL per CFUNCTYPE callback, so
    invoking a Python body from the C-spawned threads is safe; the hazard was
    empirically disproven). (2) The rc6 Python cascade.parallel_sector_dispatch
    recomputed the serial reference (+ chiral_dual) inline on EVERY call →
    ~2.25× body invocations = a 2.6–7.7× slowdown vs serial; the
    parallel==serial / sector2==chiral_dual invariants are now STRUCTURAL
    guarantees (proven in the test suite), with a new verify=False kwarg for
    the opt-in runtime cross-check. No new ToolEntry → describe() STAYS 177;
    ABI unchanged at 3 (Python-only change; no C source edit). Delivers the
    F233 4-thread speedup as shipped (#778/#771).

    Prior v0.6.0rc7 — MS #20 C-parity voxel #771: the C-orchestration half of the
    Klein-4 four-sector parallel cascade dispatch (the C peer of rc6's Python
    cascade.parallel_sector_dispatch). New ABI-additive C symbol
    srmech_cascade_parallel_sector_dispatch runs the <=4 sector-duals
    inv_T_s(body(T_s(x))) into disjoint caller buffers (no malloc; JPL Rule 3)
    via a portable thread shim (pthread / Windows / serial fallback) — so srmech
    runs the four-sector dispatch with NO host Python (full C/Python parity).
    sector-2 == cascade.chiral_dual; serial == threaded bit-exact; cap-at-4.
    Closes the rc6 Python-only parity gap. No new ToolEntry → describe() STAYS
    177; ABI unchanged at 3 (additive symbol). Closes #771.

    Prior v0.6.0rc6 — MS #20 parallel-dispatch voxel (F233 / #778): pure-Python
    srmech.amsc.cascade.parallel_sector_dispatch(body, x) — runs a cascade
    across its ≤4 Klein-4 chirality sectors (γ₅± × iω₇±) CONCURRENTLY on a
    ThreadPoolExecutor, capped at 4 (the order-3 triality is the only escape
    past 4, F220). Each sector reconstructs from its OWN sector-transformed
    input (0 cross-thread reads → parallel == serial bit-exact); sector-2 ==
    cascade.chiral_dual. Composes ONLY already-C-parity'd atoms (chiral_flip /
    reorient / chiral_dual / net_chirality / magnitude) — no Python-only
    cascade capability; the C-orchestration parity is #771 (kept open; full
    C/Python parity = srmech needs no Python to run the 4-sector dispatch).
    +1 ToolEntry → describe() tool total 176 → 177. Pure-Python; ABI 3; no abs().

    Prior v0.6.0rc5 — MS #20 reentrant-core voxel #772: the C core is now fully
    reentrant — the two remaining shared-static scratch buffers (ndjson
    g_line_buf, laplacian Hwork) are gone. g_line_buf (1 MiB) is now a
    function-local static SRMECH_THREAD_LOCAL buffer in srmech_ndjson_iter
    (per-thread, cross-chunk-persistent, no stack-overflow risk); Hwork moves to
    a new ABI-additive srmech_hermitian_eigendecompose_ws(..., workspace, ws_len)
    caller-supplied entry, with the existing symbol routing through it via a
    thread-local workspace. No shared mutable static remains in any op call path
    → the #771 plugin can parallelize the full surface. ABI unchanged at 3 (new
    symbol is additive); no API/behaviour change → describe() tool total STAYS
    176; JPL Power-of-Ten ratchet green; no abs(). Closes #772.

    Prior v0.6.0rc4 — MS #20 docs/accuracy voxel #738: the sha256_bytes docstring
    now documents the int-conversion path — it returns a 64-char hex str (the
    Class A content-address), so a caller wanting an int uses int(h, 16) /
    int(h[:8], 16), NOT int.from_bytes(...). Docs-only (no API change);
    describe() tool total STAYS 176; ABI unchanged at 3. (#739/#740/#741 were
    verified already correct as of rc18 — W5/W6b/W6c.) Closes #738.

    Prior v0.6.0rc3 — MS #20 forward-arch voxel #761 (F220): the order-3 triality
    surfaced as the 7th lean-ISA primitive — srmech.qm.triality.
    lean_isa_seventh_primitive(). The chirality-complete A–N core = 6 order-2
    cascade.atoms + 1 order-3 triality (triality_automorphism, τ³=I) = 7 — the
    only access to the 3rd chiral axis. BIT-EXACT certificate: τ has order
    exactly 3 + the Lagrange arithmetic 3∤8 (the 6 atoms commute → abelian
    Z₂×Z₂×Z₂, |G|=8, no order-3 element ⇒ the order-3 axis is unreachable —
    held as framework-reading, NOT a derived theorem, under
    framework_chirality_complete_reading). +1 ToolEntry → describe() tool total
    175 → 176. Pure-Python; ABI unchanged at 3; no abs() (Class K pin-slot,
    scalar cascade.magnitude). Closes #761.

    Prior v0.6.0rc2 — MS #20 forward-arch voxel #759: new srmech.qm.so8 op
    quaternion_subalgebra_stabilizer() — the bit-exact 6-dim so(4)=su(2)⊕su(2)
    G₂-stabiliser of a quaternion ℍ⊂𝕆 (the ℍ-reading sibling of an_embedding;
    F215). Keeps the Lie SYMMETRY surface (so(4)⊂g₂) distinct from the
    cascade.atoms OPERATOR surface so the 6=6 coincidence can't recur. +1
    ToolEntry → describe() tool total 174 → 175. Pure-Python; ABI unchanged
    at 3; no abs() (Class K pin-slot). Closes #759.

    Prior v0.6.0rc1 — MS #20 forward-arch voxel #751: srmech.amsc.cascade split
    into a two-tier lean-ISA package — cascade.atoms.* (6 silicon-able 1:1
    intrinsics: pin_slot_at_zero, reorient, magnitude, chiral_flip,
    chiral_dual, net_chirality) vs cascade.compose.* (2 iterative algorithms:
    cyclic_gcd = Euclid, best_rational_signed = CF-loop). Flat cascade.<op>
    names retained as deprecated-for-one-release aliases; public surface
    byte-identical (describe() tool total STAYS 174); ABI unchanged at 3;
    no abs() (Class K pin-slot). Closes #751.

    Prior v0.5.0 — production graduation of the rc9–rc22 voxel arc. The final
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
    complement (a real 3-span cannot carry it — [su3, real-3] leaks O(1)),
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
    assert srmech.__version__ == "0.9.0rc110", (
        f"expected srmech.__version__ == '0.9.0rc110'; got "
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
        ops = tuple(registered_ops())
        # Eagerly-registered ops appear first, in registration order.
        assert ops[:3] == ("alpha", "beta", "gamma")
        # rc71: registered_ops() is declarative — the package's lazily-
        # registrable numpy Path-B ops (matched_filter / sign_quantise /
        # wiener) are listed as PENDING (no numpy-pulling import forced) after
        # the loaded ops. clear_registry() wipes _REGISTRY, not the lazy
        # loaders, so they trail the three we just registered.
        for extra in ops[3:]:
            assert extra in {"matched_filter", "sign_quantise", "wiener"}, extra
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
