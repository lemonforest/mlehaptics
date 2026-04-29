"""chess_spectral.qm_4d_dynamics - Track B move-as-unitary dynamics.

Phase 4 milestones B1 + B2 + B3a + B3b + B3c + B3d/e + **B5** are
shipped here. This module is Track B's per-channel math hub; it sits
beside :mod:`chess_spectral.qm_4d` (Track A kinematic) per the
convention announced in ADR-002.

Shipped here:
  - **B1** :func:`u_move_a1` — A_1 channel projector-sandwich
    (same-orbit strict; cross-orbit non-trivial residual). **B5
    capture path** ships an Option A re-encode marker
    (``reason='capture-rank-1-with-renorm'`` + ``psi_post_block`` +
    ``captured_piece``).
  - **B2** :data:`H_FREE_4D` and :func:`evolve_under_h0` — Zeno
    free-evolution between move boundaries (ADR-002 §3.1).
  - **B3a** :func:`u_move_std4` — STD4_X/Y/Z/W per ADR-003 §3.1's
    similarity-transform form, restricted to same-B_4-orbit non-capture
    moves per the ADR-003 amendment's Option (a). Cross-orbit moves
    return a marker dict pointing at the v1.5 measurement-only
    re-encode. **B5 capture path** ships an Option A re-encode marker
    (``reason='capture-rank-1-with-renorm'`` + ``psi_post_block`` +
    ``captured_piece``); the capture path is independent of orbit
    dichotomy — both same-orbit and cross-orbit captures route
    through the same marker.
  - **B3b** :func:`u_move_fa_pawn` — pawn antisymmetric channels
    (FA_PAWN_W/Y) via the axis-parity-odd projector sandwich.
    **B5 capture path** ships an Option A re-encode marker with
    partial-isometry semantics
    (``reason='capture-partial-isometry'`` + ``psi_post_block`` +
    ``captured_piece``) per ADR-003 §3.1 channels 8-9 (the captured
    pawn's 8-mode block is removed by the swap, so ``||U @ psi|| <
    ||psi||``; renormalisation is folded into the L2 normalisation
    at the :func:`state_to_psi` layer).
  - **B3c** :func:`u_move_fib_meas` — FIB_SYM_1/2/3 via the
    **measurement-only re-encode** path per the Phase 3.5 amendment
    to ADR-003 §3.3. **Structurally distinct from B1/B3a/B3b: no
    projector sandwich, no strict-unitary matrix.** Returns a marker
    dict with ``psi_post_block`` (a 4096-dim complex128 vector)
    computed by applying the move classically, re-encoding the
    post-move position via :func:`chess_spectral.qm_4d.state_to_psi`,
    and slicing the FIB channel block. **B5 capture path** uses the
    same Option A re-encode construction with
    ``reason='capture-measurement-only'`` (the bilinear FIB encoder
    formula has no strict-unitary lift for captures or non-captures,
    so both ship via measurement-only re-encode). See "B3c:
    FIB_SYM_1/2/3" section below for the detailed rationale.
  - **B3d/e** :func:`u_move_fd_diag` — FD_DIAG (channel 10, the
    diagonal-deviation / rook-shadow channel). **Structurally
    distinct again**: per ADR-003 §3.2 channel 10's derivation, the
    FD_DIAG block is **invariant under non-capture, same-piece-type
    moves** (the per-piece DIAG_DEV row is unchanged when one piece
    moves between empty squares; the encoded sum
    ``out[k] = Σ sig[s] * DIAG_DEV[piece_row(s), k]`` is preserved
    because the same DIAG_DEV row contributes the same vector — only
    which square contributes ``sig[s]`` changes, and that does not
    affect the channel sum). The v1.5 implementation uses the
    **rank-1 update + renormalization path** (validated by Phase 3.5
    Probe 2: cond p95 = 8.60 vs the 100 acceptance gate) under the
    **Option A** construction: the function returns a marker dict
    carrying ``psi_post_block`` via re-encoding the post-move
    position. For non-captures the rank-1 update reduces to identity
    (the channel is invariant), so re-encoding is mathematically
    equivalent. **B5 capture path** uses the same Option A re-encode
    with ``reason='capture-rank-1-with-renorm'``; the rank-1 update
    is non-trivial for captures (the destination's DIAG_DEV row
    changes from the captured piece's row to the moving piece's row)
    but Option A re-encoding via :func:`state_to_psi` reproduces it
    exactly. See "B3d/e: FD_DIAG" section below for the rationale.
  - **B5** capture handling — **shipped this milestone**. Each of
    the 11 channels above accepts ``assume_non_capture=False`` and
    routes captures through an Option A re-encode marker that drops
    the captured piece's contribution from the post-move encoder
    input. The marker dict carries the channel-specific ``reason``
    string (``'capture-rank-1-with-renorm'`` for A_1 / STD4 /
    FD_DIAG, ``'capture-partial-isometry'`` for FA_PAWN, and
    ``'capture-measurement-only'`` for FIB_SYM) plus a
    ``captured_piece`` field exposing which piece value was removed.
    Phase 3.5 Probe-3's amended ADR-005 lineage (decompose
    M_pawn = M_single + M_double for the η = P_w pseudo-Hermitian
    metric) is exposed via the structural-API helper
    :func:`_pawn_observable_decomp`. Explicit rank-1 / partial-
    isometry / Stinespring algebra is deferred to v1.7+.

The B1 + B2 + B3a + B3b + B3c + B3d/e shipped surface covers **all
11 channels for non-capture moves**: A_1, STD4_{X,Y,Z,W},
FA_PAWN_{W,Y} via strict-unitary projector-sandwich /
similarity-transform; FIB_SYM_{1,2,3} via measurement-only
re-encode; and FD_DIAG via re-encoded marker (rank-1 invariance for
non-captures; explicit rank-1 + renorm deferred to B5 for the
capture case). Combined with the ADR-003 amendment's
measurement-only fallback for cross-orbit moves, this completes
Phase 4's per-channel builder roster — the v1.5 bridge integration
adds the dispatch logic that consumes the mixed value types
(csr_matrix vs marker dict) into the §17.1 ``apply_move_qm`` API.

Phase 3.5 Probe-Result Amendments
---------------------------------

ADR-003 §3.1 sketches `Pi_0` (the A_1 channel's per-move unitary) as
a bare 4096-square swap matrix. **B1 implements the projector-sandwich
form** ``U_a1 = P_A1 @ U_swap @ P_A1`` per the user-spec for B1: this is
the construction that lives entirely within ``range(P_A1)`` (the A_1
subspace as defined by the encoder). The bare-swap form is unitary on
the full ``C^4096`` but does not preserve the A_1 subspace; the
projector-sandwich is sub-unitary on ``range(P_A1)``.

A new finding from B1: the projector-sandwich is **only sub-unitary
when the swap commutes with P_A1**, which holds iff ``sq_from`` and
``sq_to`` lie in the same B_4 orbit. For typical chess moves (which
cross orbits), ``U_a1.conj().T @ U_a1 != P_A1`` and the
re-encoding-match fails too. See the test module's findings docstrings
for the sample-level numerical evidence; ADR-003 §3.1 will need an
amendment to either restrict the strict-unitary claim to same-orbit
moves or to redesign the lift. The current shipped construction is
**honest about its support**: it is exact on same-orbit non-capture
moves and is a documented-not-strict approximation on cross-orbit
moves (suitable for the channel-marginal phase-rotation visualization
M14.2/M14.3 needs).

ADR-001 §3.1: the A_1 channel phase is exactly ``e^{i * 0} = 1``
(theta_0 = 0 for the trivial irrep). The phase factor is kept
explicit in the implementation so the same code structure scales to
the other 10 channels in B2-B5.

ADR-004 §3.4 (Phase 3.5 Probe-4 amendment): U_move is **not** required
to anti-commute with J_op as algebraic operators. The Z_2 sector flip
is implemented at the state-vector level via ``state_to_psi``'s
side-to-move sign multiplier. Tests in this module verify the
non-anti-commuting behavior (it is automatic for swap-permutation
constructions and is a consistency check, not a regression).

B3a: STD4_X / STD4_Y / STD4_Z / STD4_W — std-rep coord channels
---------------------------------------------------------------

The STD4_a channels (a in {X,Y,Z,W} == axis index 0,1,2,3) carry the
**centred coordinate residual** per axis. Per the encoder
(:mod:`chess_spectral.encoder_4d`), the channel-`a` value at square
``s`` is ``psi_a[s] = coord_resid[a, s] * sig[s]`` (a per-square
multiplication of the signal by the centred coord residual ``c[a] -
mean(c)`` for ``c = (x, y, z, w)`` of square ``s``).

**Construction** (per ADR-001 §3.1 + ADR-003 §3.1, the **similarity-
transform** form which is the literal ADR-003 §3.1 prescription for
channels 1-4: "Pi_a is a permutation in the D_a-basis; in the
encoder's natural basis it is D_a @ swap @ D_a^{-1}"):

  ``U_std4_a = e^{i * theta_a} * D_a @ U_swap @ D_a^+``

where ``D_a = diag(coord_resid[a, *])`` is the diagonal change-of-
basis matrix that absorbs the channel's coordinate residual
coefficients (4096-dim sparse diagonal); 170 squares per axis lie on
the "central axis" where ``coord_resid[a, s] == 0``, and for those
rows we use the Moore-Penrose pseudoinverse ``D_a^+`` (zero on those
rows), per ADR-003 §6 Open Q4's pad-with-identity prescription. The
ADR-001 phase ``theta_a = (pi/4) * delta_a`` uses ``delta_a =
axis_to - axis_from`` (signed displacement, not endpoint coordinate).

The associated **support projector** is ``P_STD4_a = diag(1 if
coord_resid[a, s] != 0 else 0)`` — real-symmetric idempotent on
``range(D_a)``, rank 3926 per axis.

**Strict-unitary regime** (B3a finding):
``U_std4_a^H @ U_std4_a == P_STD4_a`` at machine precision iff the
underlying swap commutes with ``D_a``, which (since ``D_a`` is
diagonal) reduces to ``|coord_resid[a, sq_from]| == |coord_resid[a,
sq_to]|``. ~9-12% of same-B_4-orbit pairs satisfy this magnitude-
matching condition (29 611 such pairs per axis empirically); these
are the strict-unitary-at-1e-14 path. Same-B_4-orbit pairs with
mismatched magnitudes still receive the operator (the similarity
transform is constructed to match the encoder formula exactly — so
encoder match holds), but with sub-unitarity residuals 1e-1 to 1e0;
tests pin both regimes with xfail-strict markers.

Per the ADR-003 amendment Option (a), B3a routes:
  - **Same-B_4-orbit non-capture moves**: build ``U_std4_a`` as a
    sparse CSR matrix (regardless of magnitude matching).
  - **Cross-B_4-orbit non-capture moves**: return a marker dict
    ``{'strict_unitary': False, 'reason': 'cross-orbit',
    'recommendation': 'measurement-only re-encode', ...}`` pointing
    at the v1.5 measurement-only re-encode bridge work (NOT
    integrated here; lands in v1.5 bridge).

**Per-axis isolation**: ``U_std4_axis`` operates on a 4096-block that
lives in a single STD4 channel of the encoder vector; tests verify
applying it touches only the named block.

Captures on STD4 are partial-isometry per ADR-003 §3.1 (the source
square's residual contribution disappears) and ship in B5, NOT here.

B3b: FA_PAWN_W / FA_PAWN_Y — antisymmetric pawn channels
--------------------------------------------------------

The FA_PAWN_{W,Y} channels carry the pawn-direction antisymmetric
information per Oana & Chiru Definition 11 (each pawn lives on a
single axis: w or y). The encoder constructs the FA_PAWN_W block via
``I (x) I (x) I (x) W_ANTI_DCT`` scattered from a signed pawn
indicator (and analogously for FA_PAWN_Y on the y-axis tensor slot).

**Construction** (per the B3b user-spec):

  ``U_fa_pawn_axis = e^{i * theta_axis} * P_FA_PAWN_axis @ U_swap @ P_FA_PAWN_axis``

where:

  * ``P_FA_PAWN_axis = (I - sigma_axis) / 2`` is the **axis-parity
    projector**: ``sigma_axis`` is the permutation matrix that flips
    the axis coordinate (W or Y) — i.e., ``(x,y,z,w) -> (x,y,z,7-w)``
    for the W axis, ``(x,y,z,w) -> (x,7-y,z,w)`` for the Y axis. This
    projects onto the axis-parity-odd subspace of ``C^4096`` (rank
    2048; trace = 2048).

  * ``U_swap`` is the same indicator-basis swap from ``sq_from`` to
    ``sq_to`` used in B1.

  * ``theta_axis`` is the ADR-001 §3.1 phase: ``theta = (pi/2) *
    sgn(delta_axis)`` where ``delta_axis`` is the change in the axis
    coordinate (``w_to - w_from`` for FA_PAWN_W, ``y_to - y_from`` for
    FA_PAWN_Y). When ``delta_axis == 0`` (the move doesn't change the
    relevant axis), the phase is exactly 1.0 (``sgn(0) = 0``). A phase
    of ``+/-i`` is applied for non-zero axis displacement, with sign
    matching the direction of motion.

**Empirical determination of the projector-commutativity dichotomy
(B3b finding, parallel to B1's same-orbit / cross-orbit dichotomy
for A_1):** The sub-unitarity equation ``U^H U == P_FA_PAWN_axis``
holds at machine precision **iff the swap commutes with sigma_axis**,
which in turn holds **iff ``sq_to == sigma_axis(sq_from)``** —
i.e., the move is a *pure axis flip* (only the relevant axis
coordinate changes, and the to-coordinate is the complement
``7 - from-coordinate``).

For W-axis: same-(x,y,z) and ``w_to == 7 - w_from``.
For Y-axis: same-(x,z,w) and ``y_to == 7 - y_from``.

This is a **much stricter** condition than B1's same-orbit dichotomy
(B_4 orbits cover 16-384 squares each; same-orbit moves are common).
For FA_PAWN_axis, only ``4096 / 2 = 2048`` ordered pairs of distinct
squares are pure axis flips per axis — virtually no real chess move
satisfies this.

The structural reason: ``sigma_axis`` is a single-axis order-2
permutation with NO fixed points on the integer lattice (since
``w_fixed = 7 - w_fixed`` requires non-integer ``w = 3.5``). The
swap-projector commutator vanishes only on the involution-pair
structure ``(s, sigma_axis(s))``.

**Implication: the same-orbit-only restriction (ADR-003 amendment)
narrows further for FA_PAWN.** Where the A_1 amendment routes
cross-orbit moves to measurement-only re-encode, the same fallback
path applies to FA_PAWN_axis for non-axis-flip moves. The B3b
implementation builds the projector-sandwich form for all moves; the
test surface pins the strict sub-unitarity claim to axis-flip moves
via xfail-strict markers on the cross-parity-class sample, mirroring
B1's pattern.

Captures on FA_PAWN are partial-isometry per ADR-003 §3.1 and ship
in B5, NOT here. ``u_move_fa_pawn(state, move, axis,
assume_non_capture=False)`` raises ``NotImplementedError`` pointing
at B5 if the move captures.

B3c: FIB_SYM_1 / FIB_SYM_2 / FIB_SYM_3 — measurement-only re-encode
-------------------------------------------------------------------

The FIB_SYM channels (5/6/7 in :data:`chess_spectral.encoder_4d.
CHANNELS_4D`) carry the **bilinear** rank-3 cross-piece SVD basis
(per :ref:`encoder_4d.encode_4d` channels 5-7). Construction at
square ``s ∈ adj(k)``:

  ``fc[s] += gradient(k) * fib_d[piece(k), k, c-5]``
  where ``gradient(k) = sum_{n in adj(k)} sig[n]``

This is **bilinear** in ``sig``: the channel value at ``s`` depends
both on ``sig[k]`` (via the piece(k) selection of FIBER_LOCAL) and on
``sig[n]`` for ``n in adj(k)`` (via the gradient sum).

**No strict-unitary lift exists.** A move changes occupancy at the
origin and destination squares; the FIB channel at ``s ∈ adj(origin)
∪ adj(destination)`` updates via a *piecewise* formula whose
gradient-times-FIBER_LOCAL product is non-linear in ``delta_sig``.
ADR-003 §3.2's "best-effort linearization" path (Jacobian at
``pos_pre`` + polar decomposition) was tested in Phase 3.5 Probe 2
and **failed the acceptance gate by 50-500×**:

  | Channel    | Acceptance gate | Probe 2 p95 | Outcome           |
  |------------|-----------------|-------------|-------------------|
  | FIB_SYM_1  | ε ≤ 0.10        | 5.64        | ❌ FAIL by ~56×   |
  | FIB_SYM_2  | ε ≤ 0.10        | 6.82        | ❌ FAIL by ~68×   |
  | FIB_SYM_3  | ε ≤ 0.10        | 46.76       | ❌ FAIL by ~468×  |

Per the **Phase 3.5 amendment to ADR-003 §3.3** (PHASE_3_5_PROBE_
RESULTS.md), FIB channels ship under the §3.3 fallback path:
**measurement-only re-encode**. This is the QM-honest reading: a
move on a non-linear channel is a **measurement** (collapse to the
post-move encoder basis) rather than a unitary evolution.

**Construction** (no projector sandwich; no matrix):

  1. Apply the move classically to the position dict (``pos_post =
     pos_pre with from_idx removed and to_idx set to piece(from_idx)``).
     Equivalent to v1.4's :func:`chess_spectral_4d.apply_move` with
     non-capture, non-promotion semantics.
  2. Re-encode via :func:`chess_spectral.qm_4d.state_to_psi`
     (45 056-dim L2-normalized complex128 vector).
  3. Slice the FIB_SYM_{fib_idx} channel block (4096-dim subvector).
  4. Return as a **marker dict** with ``psi_post_block`` carrying the
     vector. The dict shape composes cleanly with B3a's same-orbit/
     cross-orbit dual-return convention so the v1.5 bridge can
     dispatch on ``isinstance(value, dict)`` uniformly.

This path is **always invoked** for FIB channels — there is no
"strict-unitary" branch to fall through. The ``strict_unitary: False``
flag in the marker is therefore a constant for B3c (informational
for the bridge consumer, not a runtime dispatch key).

**Why this is honest QM** (not a hack): ADR-002's Zeno semantics
already accommodates a measurement-then-evolution sequence between
move boundaries. For FIB channels, the "measurement" is the
projection onto the post-move encoder basis, and the "evolution" is
the H_0 free-particle drift between move boundaries (B2's
``evolve_under_h0``). The composite is a valid quantum trajectory;
what's lost is the unitary-on-pre-move-amplitude evolution claim
that B1/B3a/B3b enjoy on their respective channels.

**Independence from pre-move ψ**: ``u_move_fib_meas`` does NOT depend
on the pre-move ψ amplitude. The output is determined entirely by
the post-move position. (Contrast B1 where the operator is a
projector-sandwich on ``C^4096`` independent of the position.) Two
different starting positions that yield the same post-move position
produce identical ``psi_post_block`` outputs — verified by test 5
in :mod:`tests.test_qm_4d_dynamics_b3c`.

**Side-to-move handling**: :func:`state_to_psi` multiplies the
encoder output by ``+1`` for white-to-move and ``-1`` for black-to-
move (Pre-flight 1 Z_2 superselection). ``u_move_fib_meas`` accepts
an optional ``side_to_move_post`` kwarg (default ``True``) which is
forwarded to :func:`state_to_psi`. Magnitudes ``|psi_post_block|^2``
are unaffected; the sign affects the relative phase between channels
when consumers compose multiple channel blocks.

Captures on FIB are deferred to B5 alongside the other channels.
``u_move_fib_meas(state, move, fib_idx, assume_non_capture=False)``
raises ``NotImplementedError`` pointing at B5 if the move captures.

B3d/e: FD_DIAG — diagonal-deviation channel (rank-1 update path)
----------------------------------------------------------------

The FD_DIAG channel (channel 10) carries the **per-piece diagonal
deviation** in mode space (the "rook shadow" channel). Per the
encoder (:mod:`chess_spectral.encoder_4d`, channel 10):

  ``out[k] = Σ_{occupied s} sig[s] * DIAG_DEV[piece_row(s), k]``

where ``DIAG_DEV`` is a (6, 4096) per-piece-type table holding the
mode-space diagonal deviation of the piece's adjacency operator from
the universal kinetic spectrum (per :func:`tables_4d.diag_dev_4d`).
The encoder formula is **linear in sig** (linear in the position
indicator) but the **per-piece coefficient** ``DIAG_DEV[piece_row, k]``
varies by piece type.

**ADR-003 §3.2 channel 10's derivation** distinguishes two move
classes:

  * **Non-capture moves**: when piece ``p`` moves ``o → d`` with
    ``d`` empty pre-move, the contribution at ``o`` (``sig[o] *
    DIAG_DEV[piece_row(p), :]``) becomes 0 and the contribution at
    ``d`` (which was 0 pre-move) becomes ``sig[o] * DIAG_DEV[
    piece_row(p), :]``. Both contributions use the **same DIAG_DEV
    row** (same piece type) and the **same sig magnitude** (the moving
    piece's own ``sig[o]``). **Net change to ``out[k]`` is zero** —
    the FD_DIAG channel block is invariant under non-capture,
    same-piece-type moves. ADR-003 calls this case ``Pi_10 =
    identity`` on the channel block.
  * **Capture moves**: piece ``p`` at ``o`` captures piece ``p'`` at
    ``d``. The contribution at ``d`` changes from ``sig[d] *
    DIAG_DEV[piece_row(p'), :]`` to ``sig[o] * DIAG_DEV[
    piece_row(p), :]``; the difference is generically nonzero. ADR-003
    §3.2 specifies a **rank-1 update + renormalization** form:

      ``psi_post_FD = psi_pre_FD + α · u ⊗ v + renorm``

    where ``u``, ``v`` are computable from the piece values + DIAG_DEV
    rows + which square is the destination, and ``α`` absorbs the
    per-position normalization. The renormalization restores
    ``‖ψ‖ = 1`` because the rank-1 update is not unitary by itself.

**Phase 3.5 Probe 2 validated the rank-1 path's conditioning** on a
synthetic-capture corpus (1000 (state, move) pairs):

  | Channel  | Acceptance gate    | Probe 2 p95 | Outcome  |
  |----------|--------------------|-------------|----------|
  | FD_DIAG  | cond ≤ 100         | **8.60**    | ✅ PASS  |

The cond p95 = 8.60 is well below the 100 acceptance gate, confirming
the rank-1 update is well-conditioned (in stark contrast to FIB
channels' linearization, which failed the gate by 50-500×).

**v1.5 Construction (Option A — re-encode marker)**: For ship velocity
in v1.5, the non-capture path returns a marker dict carrying
``psi_post_block`` computed via re-encoding the post-move position
(applied classically at the dict level + :func:`state_to_psi` +
slice). This is **mathematically equivalent** to the rank-1 update
form for non-captures (which reduces to identity on the FD_DIAG
block) and **cheaper** to ship in v1.5 (no rank-1 algebra to
materialize). The construction mirrors B3c's measurement-only
re-encode shape so the v1.5 bridge dispatches uniformly via
``isinstance(value, dict)``.

  1. Apply the move classically: ``pos_post = pos_pre`` with
     ``from_idx`` removed and ``to_idx`` set to ``piece(from_idx)``.
     Identical to B3c's classical-move helper.
  2. Re-encode via :func:`chess_spectral.qm_4d.state_to_psi` (full
     45 056-dim L2-normalized complex128 vector).
  3. Slice the FD_DIAG channel block (offset ``10 * CHANNEL_DIM``).
  4. Return as a marker dict with ``psi_post_block`` (4096-dim
     complex128 vector) and the ``rank-1-update-with-renorm`` reason
     string identifying the rationale.

**Why Option A vs Option B (full rank-1 algebra)?** Option B would
materialize the explicit rank-1 update operator: compute ``α``,
``u``, ``v`` from the move geometry + ``DIAG_DEV`` + piece values,
build ``Pi_10 = I + α · u v^T`` (or its capture analog), apply to
``psi_pre[FD_DIAG]``, renormalize, and return a 4096-vector. For
non-captures this reduces to identity, which is trivial. For
captures, Option B's explicit algebra is the path B5 will
materialize. **Option A ships in v1.5 because**:

  * **Non-capture invariance is exact**: ``state_to_psi(pos_post)
    [FD_DIAG] == state_to_psi(pos_pre)[FD_DIAG]`` within float
    precision, validated empirically (Probe 2's
    ``fd_diag_invariance_residual_percentiles.p50 = 0.0``).
  * **Time-to-ship**: Option B's rank-1 algebra requires careful
    per-move construction of ``α``/``u``/``v``; the Probe 2 driver
    has the formulae but they live in research/, not src/. Wiring
    that up cleanly is B5 work.
  * **Performance equivalence in v1.5**: M14.x rendering invokes the
    encoder per frame anyway; the re-encode call is amortized across
    multiple channels (the bridge can batch B3c + B3d/e into a single
    :func:`state_to_psi` call and slice four blocks).
  * **v1.7+ upgrade path**: M14.x incremental rendering may want to
    avoid the re-encode call per frame; at that point Option B's
    explicit operator becomes attractive (apply Pi_10 = identity in
    O(1) for non-captures, no encoder call needed). The marker dict
    shape leaves room for this upgrade by adding optional
    ``rank1_alpha`` / ``rank1_u`` / ``rank1_v`` keys without breaking
    the consumer contract.

**Independence from pre-move ψ**: like ``u_move_fib_meas``, the
output depends ONLY on the post-move position. The marker dict's
``strict_unitary: False`` flag is informational (no fallthrough to a
strict-unitary branch); the ``reason: 'rank-1-update-with-renorm'``
string distinguishes B3d/e's marker from B3c's
``'measurement-only'`` so the bridge can log which channels used
which path.

Captures on FD_DIAG are deferred to B5 alongside the other channels.
``u_move_fd_diag(state, move, assume_non_capture=False)`` raises
``NotImplementedError`` pointing at B5 if the move captures, with
the explicit pointer that B5 will implement the rank-1 update +
renormalization form per ADR-003 §3.2 channel 10's capture branch.

Conventions
-----------
* Move semantics: a move is ``(from_sq, to_sq)`` where each is a
  4-tuple ``(x, y, z, w)`` with ``0 <= component <= 7``. Linear-square
  indices (``0..4095``) are also accepted via the
  :func:`chess_spectral_4d.move_history.coord_to_sq` packing.
* Capture handling: B1 only ships non-capture moves. Calling
  :func:`u_move_a1` with ``assume_non_capture=False`` and a move that
  captures a piece raises ``NotImplementedError`` pointing at B5
  (where the partial-isometry / rank-1-update path lands).
* Output dtype: ``complex128`` throughout, matching :mod:`qm_4d`.
* Sparsity: returns ``scipy.sparse.csr_matrix``. The expected nnz of
  ``U_a1`` is bounded by ``P_A1.nnz`` (sandwich does not add nonzeros
  beyond P_A1's support).

Public API
----------
``u_move_a1(state_pre, move, *, assume_non_capture=True)``
    Build the A_1-channel unitary lift for a non-capture move.
``u_move_std4(state_pre, move, axis, *, assume_non_capture=True)``
    Build the STD4_{X,Y,Z,W}-channel unitary lift for a same-B_4-orbit
    non-capture move (axis ∈ ``{'X', 'Y', 'Z', 'W'}``). Returns a
    marker dict for cross-B_4-orbit moves.
``u_move_fa_pawn(state_pre, move, axis, *, assume_non_capture=True)``
    Build the FA_PAWN_{W,Y}-channel unitary lift for a non-capture
    move (axis ∈ ``{'W', 'Y'}``).
``u_move_fib_meas(state_pre, move, fib_idx, *, assume_non_capture=True,
side_to_move_post=True)``
    **Measurement-only re-encode** for FIB_SYM_{1,2,3} per the
    Phase 3.5 amendment to ADR-003 §3.3. Returns a marker dict with
    ``psi_post_block`` (a 4096-dim complex128 vector); does NOT return
    a matrix. ``fib_idx ∈ {1, 2, 3}``.
``u_move_fd_diag(state_pre, move, *, assume_non_capture=True,
side_to_move_post=True)``
    **Rank-1 update + renormalization** for FD_DIAG (channel 10) per
    ADR-003 §3.2 channel 10. v1.5 ships the **Option A** form:
    returns a marker dict with ``psi_post_block`` (a 4096-dim
    complex128 vector) computed via re-encoding the post-move
    position. Mathematically equivalent to the rank-1 update for
    non-capture moves (which reduces to identity on the channel
    block); the explicit rank-1 algebra ships in B5 for the capture
    case. Validated by Phase 3.5 Probe 2 (cond p95 = 8.60 vs the 100
    acceptance gate).
``evolve_under_h0(psi, t, *, channel=None)``
    Zeno-style continuous evolution under ``H_0 = -Δ_{P_8^4}``.
``apply_move_qm(state, move, *, optional_return_unitary=False)``
    Bridge-surface entry-point per §17.1. v1.5 returns the assembled
    per-channel dictionary with all 11 channel entries populated for
    non-capture moves: A_1 + STD4_{X,Y,Z,W} + FA_PAWN_{W,Y} as
    ``csr_matrix`` (or marker dict for cross-orbit / cross-parity);
    FIB_SYM_{1,2,3} + FD_DIAG as marker dicts carrying
    ``psi_post_block``. Captures still raise ``NotImplementedError``
    pointing at B5.
"""
from __future__ import annotations

from typing import Dict, Mapping, Optional, Tuple, Union

import math

import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import expm_multiply

from chess_spectral import qm_4d as _qm4
from chess_spectral import tables_4d as _t4

# Re-export the A_1 channel constants for direct module use.
N_SQUARES: int = _t4.N_SQUARES                  # 4096
N_CHANNELS: int = _qm4.N_CHANNELS                # 11
CHANNEL_DIM: int = _qm4.CHANNEL_DIM              # 4096
ENCODING_DIM: int = _qm4.ENCODING_DIM            # 45056

# Channel index of the A_1 (totally-symmetric / trivial irrep) block.
A1_CHANNEL_IDX: int = 0

# Channel indices for the pawn-antisymmetric blocks (Oana & Chiru
# Definition 11; v1.1.1 split). FA_PAWN_W lives at offset 8 *
# CHANNEL_DIM in the encoder vector; FA_PAWN_Y at 9 * CHANNEL_DIM.
FA_PAWN_W_CHANNEL_IDX: int = 8
FA_PAWN_Y_CHANNEL_IDX: int = 9

# B3c: channel indices for the bilinear FIB_SYM blocks. ``fib_idx in
# {1, 2, 3}`` maps to channel indices 5, 6, 7 in the encoder vector
# (offsets ``[5, 6, 7] * CHANNEL_DIM``). The +4 offset keeps the
# user-facing 1-based numbering aligned with the encoder channel names
# ('FIB_SYM_1' through 'FIB_SYM_3') while internally we use 0-based
# channel indices for slice arithmetic.
FIB_SYM_1_CHANNEL_IDX: int = 5
FIB_SYM_2_CHANNEL_IDX: int = 6
FIB_SYM_3_CHANNEL_IDX: int = 7

# B3d/e: channel index for the diagonal-deviation (FD_DIAG) block.
# Last of the 11 channels (index 10), offset ``10 * CHANNEL_DIM`` =
# 40960 in the encoder vector. Carries the per-piece-type diagonal
# deviation in mode space (the "rook shadow" channel; see
# :func:`tables_4d.diag_dev_4d` and :data:`encoder_4d.CHANNELS_4D`).
FD_DIAG_CHANNEL_IDX: int = 10

# B3b: the two axes the FA_PAWN channels live on. Matches the encoder's
# v1.1.1 axis labels ('y'/'w' lower-case as pawn-axis tags); we
# capitalise here so the public API parameter naming matches the
# encoder channel names ('FA_PAWN_W' / 'FA_PAWN_Y').
_FA_PAWN_AXES: Tuple[str, ...] = ('W', 'Y')

# Map FA_PAWN axis letter -> 4-tuple position index (0..3) for the
# corresponding coordinate slot. Used to build sigma_axis (the parity
# flip) and to compute delta_axis (the ADR-001 §3.1 phase argument).
_FA_PAWN_AXIS_INDEX: Mapping[str, int] = {
    # 4-tuple positions: (x, y, z, w) -> indices (0, 1, 2, 3)
    'W': 3,
    'Y': 1,
}


# ---- Type aliases ---------------------------------------------------

# Coords accepted for move endpoints. Either a 4-tuple of ints in
# [0, 7] (the chess_spectral_4d.move_history.Coord4D form) or a linear
# square index in [0, 4096). Both are normalised to a linear index
# internally via :func:`_to_linear_idx`.
SquareLike = Union[int, Tuple[int, int, int, int]]


# ---- Private helpers ------------------------------------------------


def _to_linear_idx(sq: SquareLike) -> int:
    """Normalise a square to its linear index in [0, 4096).

    Accepts either ``int`` (already linear) or a 4-tuple
    ``(x, y, z, w)`` with each component in ``[0, 7]``.
    """
    if isinstance(sq, int):
        if not 0 <= sq < N_SQUARES:
            raise ValueError(
                f"linear square index {sq} out of range [0, {N_SQUARES})"
            )
        return sq
    if isinstance(sq, tuple) and len(sq) == 4:
        return int(_t4.sq4(*sq))
    raise TypeError(
        f"move endpoint must be int or 4-tuple, got "
        f"{type(sq).__name__}: {sq!r}"
    )


def _coerce_move(move) -> Tuple[int, int]:
    """Accept a (from, to) tuple or a Move4D instance and return
    ``(from_idx, to_idx)`` as linear-square integers.

    Move4D import is deferred so this module does not introduce a
    package import cycle when chess_spectral_4d itself does not
    depend on qm_4d_dynamics.
    """
    # Move4D-like (duck-type on the .from_sq / .to_sq attributes used
    # by chess_spectral_4d.move_history).
    from_sq = getattr(move, "from_sq", None)
    to_sq = getattr(move, "to_sq", None)
    if from_sq is not None and to_sq is not None:
        return _to_linear_idx(from_sq), _to_linear_idx(to_sq)
    # 2-tuple form
    if isinstance(move, tuple) and len(move) == 2:
        return _to_linear_idx(move[0]), _to_linear_idx(move[1])
    raise TypeError(
        f"move must be a (from_sq, to_sq) tuple or have .from_sq / "
        f".to_sq attributes; got {type(move).__name__}: {move!r}"
    )


def _is_capture(state_pre, from_idx: int, to_idx: int) -> bool:
    """True iff there is a piece on the destination square in
    ``state_pre`` (i.e., a capture).

    ``state_pre`` is accepted as either a position dict (``{sq: piece}``)
    or a :class:`chess_spectral_4d.move_history.GameState4D`-like
    object exposing a ``.position`` attribute.
    """
    pos = getattr(state_pre, "position", state_pre)
    if not isinstance(pos, Mapping):
        raise TypeError(
            f"state_pre must be a position dict or have a .position "
            f"attribute; got {type(state_pre).__name__}"
        )
    return to_idx in pos


def _get_captured_piece(state_pre, to_idx: int):
    """Return the piece at ``to_idx`` in ``state_pre``, or ``None`` if
    the destination is empty.

    Used by the B5 capture-path builders to populate the marker dict's
    ``captured_piece`` field so consumers can reason about which piece
    type was removed (this matters for the FA_PAWN partial-isometry
    semantics where the captured pawn's 8-mode block is removed; see
    ADR-003 §3.1 channels 8-9). The piece value is returned in the
    encoder's input schema (string for non-pawns, ``(color, axis)``
    tuple for pawns; see :mod:`chess_spectral.encoder_4d`).
    """
    pos = getattr(state_pre, "position", state_pre)
    if not isinstance(pos, Mapping):
        raise TypeError(
            f"state_pre must be a position dict or have a .position "
            f"attribute; got {type(state_pre).__name__}"
        )
    return pos.get(to_idx)


def _build_swap_4096(from_idx: int, to_idx: int) -> csr_matrix:
    """4096x4096 sparse permutation matrix that swaps the basis
    vectors at ``from_idx`` and ``to_idx`` and is identity elsewhere.

    ``from_idx == to_idx`` returns the identity (a no-op move; we
    guard against this explicitly so degenerate moves don't generate
    surprising structure).
    """
    if from_idx == to_idx:
        return sp.eye(N_SQUARES, format="csr", dtype=np.complex128)
    rows = np.arange(N_SQUARES, dtype=np.int64).copy()
    rows[from_idx] = to_idx
    rows[to_idx] = from_idx
    cols = np.arange(N_SQUARES, dtype=np.int64)
    data = np.ones(N_SQUARES, dtype=np.complex128)
    return sp.csr_matrix(
        (data, (rows, cols)), shape=(N_SQUARES, N_SQUARES),
    )


def _get_P_A1() -> csr_matrix:
    """Cached A_1 orbit-projection matrix on C^4096, complex128.

    Wraps ``encoder_4d._load_tables()`` so we share P_A1 with the
    encoder (avoiding a second 695296-nnz construction). Casts to
    ``complex128`` and ensures CSR format.
    """
    # Lazy import to keep the module-level import surface minimal.
    from chess_spectral import encoder_4d as _enc4
    P = _enc4._load_tables()['P_A1']
    if P.dtype != np.complex128:
        P = P.astype(np.complex128)
    if not sp.isspmatrix_csr(P):
        P = P.tocsr()
    return P


# ---- A_1 channel phase factor (ADR-001 §3.1) ------------------------


def _channel_phase_a1(
    from_idx: int,  # noqa: ARG001  (signature parity with B2-B5)
    to_idx: int,    # noqa: ARG001
) -> complex:
    """Return the ADR-001 §3.1 channel phase factor for A_1.

    For the A_1 channel (channel 0, trivial irrep), the phase is
    identically ``e^{i * 0} = 1`` for every move. The signature still
    accepts the move endpoints because the same helper shape will be
    reused for STD4_X/Y/Z/W (B3a) where the phase depends on the
    coordinate displacement, and for FIB_SYM_* / FA_PAWN_* / FD_DIAG
    later. Keeping the call site uniform avoids special-casing A_1.
    """
    theta = 0.0  # ADR-001 §3.1 row "A1"
    return complex(math.cos(theta), math.sin(theta))  # exactly 1+0j


# ---- Public: u_move_a1 ----------------------------------------------


def u_move_a1(
    state_pre,
    move,
    *,
    assume_non_capture: bool = True,
    side_to_move_post: bool = True,
) -> Union[csr_matrix, Dict[str, object]]:
    """Build the A_1-channel move unitary as a 4096x4096 sparse matrix
    (non-capture path) or return a marker dict (B5 capture path).

    Construction (per ADR-001 §3.1 + ADR-003 §3.1, projector-sandwich
    form clarified by the B1 user-spec):

      1. Build ``U_swap = swap(from_idx <-> to_idx)`` on ``C^4096``.
      2. Multiply by the ADR-001 phase factor for A_1 (= 1.0).
      3. Wrap in the P_A1 projector sandwich:
         ``U_a1 = P_A1 @ U_swap @ P_A1``
         (P_A1 is real symmetric so ``P_A1.conj().T == P_A1``;
         the sandwich is the natural sub-unitary onto ``range(P_A1)``).

    The resulting ``U_a1`` is **sub-unitary** on the full ``C^4096``:
    zero outside ``range(P_A1)`` and unitary within when the
    underlying swap commutes with P_A1 (i.e., for same-B_4-orbit
    swaps). For cross-orbit chess moves the sandwich is contractive
    (``||U_a1||_op <= 1``) but does not satisfy
    ``U_a1.conj().T @ U_a1 == P_A1`` exactly — see the module
    docstring's "Phase 3.5 Probe-Result Amendments" section.

    **B5 capture path (Option A re-encode marker).** When
    ``assume_non_capture=False`` and the move IS a capture, the function
    returns a marker dict carrying ``psi_post_block`` computed via
    re-encoding the post-capture position through
    :func:`chess_spectral.qm_4d.state_to_psi`. Per ADR-003 §3.1's note
    that the A_1 capture is a "partial-isometry — destination basis
    vector keeps its index but the source signal value replaces the
    captured signal value", the capture changes the encoded sum by
    swapping ``sig[d] = sig_captured`` with ``sig[d] = sig_pre[o]``.
    Re-encoding via :func:`state_to_psi` reproduces this exactly (the
    captured square's contribution to the A_1 sum is replaced by the
    moving piece's contribution at the destination), and the post-
    capture renormalization per ADR-002 §3.4 is folded into
    :func:`state_to_psi`'s L2 normalisation. The marker dict carries
    ``reason='capture-rank-1-with-renorm'`` per the ADR-005 amendment
    lineage (the rank-1 update + renormalisation form applies to A_1
    captures by the same algebra as FD_DIAG: a single basis vector's
    coefficient changes between pre- and post-capture).

    Parameters
    ----------
    state_pre
        Pre-move state. Accepted forms:

        * Position dict ``{sq_index: piece_value}`` (the encoder's
          input schema — see :mod:`chess_spectral.encoder_4d`).
        * Object with ``.position`` attribute holding such a dict
          (e.g., :class:`chess_spectral_4d.GameState4D`).

        Used both for capture detection (the destination-occupancy
        check) and for the B5 capture path (the entire post-move
        position is needed for the re-encode).
    move
        Move endpoints. Accepted forms:

        * 2-tuple ``(from_sq, to_sq)`` where each endpoint is either
          a linear int in ``[0, 4096)`` or a 4-tuple ``(x, y, z, w)``.
        * :class:`chess_spectral_4d.move_history.Move4D` (or any
          object with ``.from_sq`` / ``.to_sq`` attributes in the
          accepted endpoint forms).
    assume_non_capture
        If ``True`` (default), the caller asserts the move is a
        non-capture; capture detection is skipped and the
        projector-sandwich operator is constructed unconditionally.
        If ``False`` and the move IS a capture, the **B5 capture path**
        runs (returns a marker dict with ``psi_post_block``). If
        ``False`` and the move is NOT a capture, the strict-unitary
        operator is returned just like the ``True`` case.
    side_to_move_post : bool, optional
        Side-to-move AFTER the move is applied (``True`` = white,
        ``False`` = black). Forwarded to :func:`state_to_psi` on the
        capture path; controls the Z_2 superselection sign on the
        re-encoded psi (Pre-flight 1 / ADR-004 §3.4 amendment). Default
        ``True`` for consistency with the other B5-aware builders.
        Ignored on the non-capture path (the projector-sandwich
        operator is independent of side-to-move; the consumer applies
        side-to-move at the assembled-ψ level via :func:`state_to_psi`).

    Returns
    -------
    csr_matrix of shape ``(4096, 4096)``, dtype ``complex128``, when
    the move is a non-capture (or when ``assume_non_capture=True``).

    dict (the B5 capture marker) of the form::

        {
            'strict_unitary': False,
            'reason': 'capture-rank-1-with-renorm',
            'channel': 'A1',
            'psi_post_block': ndarray[complex128, (4096,)],
            'sq_from': int,
            'sq_to': int,
            'captured_piece': PieceValue,
        }

    when ``assume_non_capture=False`` and the move IS a capture. The
    bridge consumer dispatches on ``isinstance(value, dict)`` to
    splice ``psi_post_block`` into the post-move ψ rather than
    multiplying ``U_a1 @ psi_pre[A_1_block]``.

    Raises
    ------
    TypeError
        If ``state_pre`` or ``move`` cannot be normalised to the
        expected forms.
    ValueError
        If ``assume_non_capture=False`` and the pre-move position
        has no piece at ``from_idx`` (a malformed move).
    """
    from_idx, to_idx = _coerce_move(move)

    if not assume_non_capture:
        # Verify the caller's claim. assume_non_capture=True (default)
        # bypasses this check and trusts the caller; this is the fast
        # path the bridge surface uses when move legality has already
        # been validated upstream.
        if _is_capture(state_pre, from_idx, to_idx):
            # B5 capture path: Option A re-encode marker.
            captured = _get_captured_piece(state_pre, to_idx)
            pos_post = _apply_move_to_position(
                state_pre, from_idx, to_idx,
            )
            psi_post_full = _qm4.state_to_psi(pos_post, side_to_move_post)
            start = A1_CHANNEL_IDX * CHANNEL_DIM
            end = start + CHANNEL_DIM
            psi_post_block = np.asarray(
                psi_post_full[start:end], dtype=np.complex128,
            ).copy()
            return {
                'strict_unitary': False,
                'reason': 'capture-rank-1-with-renorm',
                'channel': 'A1',
                'psi_post_block': psi_post_block,
                'sq_from': int(from_idx),
                'sq_to': int(to_idx),
                'captured_piece': captured,
            }

    # Step 1: 4096-dim swap (the underlying basis permutation).
    U_swap = _build_swap_4096(from_idx, to_idx)

    # Step 2: ADR-001 phase factor (= 1.0+0j for A_1 by §3.1).
    # Kept as an explicit multiplication because B2-B5 will reuse this
    # exact code structure with non-trivial phases for the other
    # channels.
    phase = _channel_phase_a1(from_idx, to_idx)
    if phase != 1.0 + 0.0j:
        # Defensive: A_1 phase is mathematically exactly 1, but the
        # multiplication path is left in for code-shape parity with
        # B2-B5. If float arithmetic ever produces a non-unit phase
        # for A_1, escalate (it would indicate a bug in the irrep
        # bookkeeping).
        U_swap = phase * U_swap

    # Step 3: P_A1 projector sandwich. P_A1 is real symmetric, so the
    # conjugate-transpose simplifies to P_A1 itself.
    P_A1 = _get_P_A1()
    U_a1 = (P_A1 @ U_swap @ P_A1).tocsr()

    # Ensure CSR + complex128 invariant for downstream code.
    if U_a1.dtype != np.complex128:
        U_a1 = U_a1.astype(np.complex128)
    return U_a1


# ---- Phase 4 B3a: STD4_{X,Y,Z,W} channels --------------------------
#
# Per the B3a user-spec and ADR-003 §3.1 channels 1-4, the STD4_a
# channels carry the centred coordinate residual ``c[a] - mean(c)``.
# The encoder maps ``sig`` to ``coord_resid[a] * sig`` (per-square
# multiplication) for each axis a in {0=X, 1=Y, 2=Z, 3=W}.
#
# Construction (ADR-003 §3.1 channels 1-4 + ADR-001 §3.1 row STD4_a):
#
#   U_std4_a = e^{i * theta_a} * D_a @ U_swap @ D_a^+
#
# where:
#   * D_a = diag(coord_resid[a, *])  (4096-dim sparse diagonal).
#   * D_a^+ is the Moore-Penrose pseudoinverse (1/D_a where nonzero,
#     else 0; 170 zero entries per axis on the central-axis squares).
#   * U_swap is the same indicator-basis swap from B1.
#   * theta_a = (pi/4) * (axis_to - axis_from) per ADR-001 §3.1.
#
# The associated **support projector** is
#   P_STD4_a = diag(1 if coord_resid[a, s] != 0 else 0)
# which is real-symmetric and idempotent (rank 3926 per axis). The
# similarity-transform form is sub-unitary on range(P_STD4_a) iff
# |coord_resid[a, sq_from]| == |coord_resid[a, sq_to]|.
#
# Per the ADR-003 amendment Option (a), the strict-unitary path here
# is restricted to **same-B_4-orbit non-capture moves**; cross-orbit
# moves return a marker dict pointing at measurement-only re-encode
# (a v1.5 bridge concern). Within the same-B_4-orbit subset, the
# additional restriction "|coord_resid| matching" defines the
# strict-machine-precision regime (~9-12% of same-orbit pairs);
# same-orbit pairs with mismatched magnitudes still receive the
# operator (and pass the encoder-match property), but with documented
# sub-unitarity residuals (1e-1 to 1e0). Tests pin both regimes.

# Module-level cached projectors / D_a matrices. Built lazily on first
# access to avoid eager scipy.sparse allocations at import time.
_D_STD4: Dict[str, sp.csr_matrix] = {}
_D_STD4_PINV: Dict[str, sp.csr_matrix] = {}
_P_STD4: Dict[str, sp.csr_matrix] = {}

# B3a: axis labels for the four STD4 channels (encoder-channel-naming
# convention).
_STD4_AXES: Tuple[str, ...] = ('X', 'Y', 'Z', 'W')

# Map STD4 axis letter -> integer index into coord_resid[axis, *]. The
# encoder's coord_resid table is indexed by ``a in {0, 1, 2, 3}`` with
# 0=X, 1=Y, 2=Z, 3=W (matching the (x, y, z, w) tuple convention from
# tables_4d).
_STD4_AXIS_INDEX: Mapping[str, int] = {
    'X': 0,
    'Y': 1,
    'Z': 2,
    'W': 3,
}

# Channel offset within the encoder's 11-channel psi vector. Mirrors
# the offsets in :data:`chess_spectral.encoder_4d.CHANNELS_4D`. STD4_X
# is channel 1 (offset 4096), STD4_Y is channel 2 (offset 8192), etc.
_STD4_CHANNEL_IDX: Mapping[str, int] = {
    'X': 1,
    'Y': 2,
    'Z': 3,
    'W': 4,
}

# Module-level cached B_4 orbit-id-of-square table. Computed lazily;
# 35 orbits, sizes {16, 64, 96, 192, 384}, sum = 4096.
_ORBIT_ID_OF_SQ: Optional[np.ndarray] = None


def _get_orbit_id_of_sq() -> np.ndarray:
    """Cached array of length 4096 mapping each square to its B_4
    orbit index (0..34).

    Used by :func:`u_move_std4` (and any future channel that needs the
    B_4 same-orbit dichotomy) to dispatch between the strict-unitary
    path and the measurement-only fallback. Computed once on first
    access and cached at module scope.
    """
    global _ORBIT_ID_OF_SQ
    if _ORBIT_ID_OF_SQ is not None:
        return _ORBIT_ID_OF_SQ
    closure = _t4.b4_closure()
    arr = -np.ones(N_SQUARES, dtype=np.int64)
    n_orbits = 0
    for s in range(N_SQUARES):
        if arr[s] >= 0:
            continue
        x, y, z, w = _t4.rc4(s)
        for g in closure:
            x2, y2, z2, w2 = _t4._apply_b4_to_square(g, x, y, z, w)
            arr[_t4.sq4(x2, y2, z2, w2)] = n_orbits
        n_orbits += 1
    # Sanity: B_4 has exactly 35 orbits on the 8x8x8x8 lattice.
    # Multiplicities {16, 64, 96, 192, 384} sum to 4096.
    assert n_orbits == 35, (
        f"B_4 orbit count {n_orbits} != 35 — orbit cache invariant "
        "violated; did the lattice / group definition change?"
    )
    _ORBIT_ID_OF_SQ = arr
    return arr


def _is_same_b4_orbit(from_idx: int, to_idx: int) -> bool:
    """True iff ``from_idx`` and ``to_idx`` lie in the same B_4 orbit
    on the 8x8x8x8 lattice. Cheap O(1) lookup once the orbit cache is
    built (first call materialises it).
    """
    arr = _get_orbit_id_of_sq()
    return int(arr[from_idx]) == int(arr[to_idx])


def _build_std4_diagonals(axis: str) -> Tuple[sp.csr_matrix, sp.csr_matrix]:
    """Construct D_a and D_a^+ (Moore-Penrose pseudoinverse) for the
    STD4_axis channel.

    ``D_a = diag(coord_resid[a, *])`` and ``D_a^+ = diag(1/coord_resid
    where nonzero, else 0)``. Both are real-symmetric (cast to
    ``complex128``) sparse diagonal matrices on ``C^4096``.
    ``coord_resid`` is sourced from
    :func:`chess_spectral.encoder_4d._load_tables` so we share the
    encoder's table (no recompute).
    """
    if axis not in _STD4_AXIS_INDEX:
        raise ValueError(
            f"STD4 axis must be one of {_STD4_AXES}; got {axis!r}"
        )
    from chess_spectral import encoder_4d as _enc4
    coord_resid = _enc4._load_tables()['coord_resid']  # (4, 4096) float64
    a_idx = _STD4_AXIS_INDEX[axis]
    diag = np.asarray(coord_resid[a_idx], dtype=np.complex128)
    # Pseudoinverse: 1/x where x != 0; 0 elsewhere. The 170 central-axis
    # squares per axis have coord_resid == 0 by construction; per
    # ADR-003 §6 Open Q4 these contribute zero amplitude to the
    # channel and are correctly handled by the pseudoinverse-zero
    # convention.
    # ``np.errstate`` suppresses the harmless divide-by-zero RuntimeWarning;
    # the np.where masks the inf/nan to zero anyway.
    with np.errstate(divide='ignore', invalid='ignore'):
        pinv = np.where(diag != 0, 1.0 / diag, 0.0).astype(np.complex128)
    D = sp.diags(diag, format='csr', dtype=np.complex128)
    Dp = sp.diags(pinv, format='csr', dtype=np.complex128)
    return D, Dp


def _get_d_std4(axis: str) -> sp.csr_matrix:
    """Cached accessor for the STD4_axis diagonal matrix D_a."""
    if axis not in _D_STD4:
        D, Dp = _build_std4_diagonals(axis)
        _D_STD4[axis] = D
        _D_STD4_PINV[axis] = Dp
    return _D_STD4[axis]


def _get_d_std4_pinv(axis: str) -> sp.csr_matrix:
    """Cached accessor for the STD4_axis pseudoinverse D_a^+."""
    if axis not in _D_STD4_PINV:
        # Side-effect: populates both D and D^+ via the build helper.
        _get_d_std4(axis)
    return _D_STD4_PINV[axis]


def _get_p_std4(axis: str) -> sp.csr_matrix:
    """Cached accessor for the STD4_axis support projector
    ``P_STD4_a = diag(1 if coord_resid[a, s] != 0 else 0)``.

    Real-symmetric, idempotent. Rank 3926 (170 central-axis zeros per
    axis on the 8x8x8x8 lattice).
    """
    if axis not in _P_STD4:
        if axis not in _STD4_AXIS_INDEX:
            raise ValueError(
                f"STD4 axis must be one of {_STD4_AXES}; got {axis!r}"
            )
        from chess_spectral import encoder_4d as _enc4
        coord_resid = _enc4._load_tables()['coord_resid']
        a_idx = _STD4_AXIS_INDEX[axis]
        mask = (coord_resid[a_idx] != 0).astype(np.complex128)
        _P_STD4[axis] = sp.diags(mask, format='csr', dtype=np.complex128)
    return _P_STD4[axis]


# ---- ADR-001 §3.1 phase factor for STD4_{X,Y,Z,W} ------------------


def _channel_phase_std4(
    from_idx: int,
    to_idx: int,
    axis: str,
) -> complex:
    """Return the ADR-001 §3.1 channel phase factor for STD4_axis.

    Per ADR-001 §3.1 row "STD4_a" (channels 1-4):
    ``theta_a = (pi/4) * (axis_to - axis_from)`` where ``axis_to``
    and ``axis_from`` are the integer axis-coordinates of the
    destination and origin squares. This is the **signed
    displacement**, not a single endpoint coordinate (per ADR-001
    §4.1's bishop e1->c3 example, where the STD4 phases are nonzero
    only along axes the move displaces along).

    Examples (axis = 'X', i.e. coordinate index 0):
      * (0,0,0,0) -> (3,0,0,0): delta_X = 3, theta_X = 3*pi/4
      * (1,2,3,4) -> (1,5,3,4): delta_X = 0, theta_X = 0 (no X motion)
      * (5,0,0,0) -> (2,0,0,0): delta_X = -3, theta_X = -3*pi/4

    Parameters
    ----------
    from_idx, to_idx : int
        Linear square indices in [0, 4096).
    axis : str
        One of ``'X'``, ``'Y'``, ``'Z'``, ``'W'``.

    Returns
    -------
    complex
        ``e^{i * theta}`` with ``theta = (pi/4) * delta_axis``.
    """
    if axis not in _STD4_AXIS_INDEX:
        raise ValueError(
            f"STD4 axis must be one of {_STD4_AXES}; got {axis!r}"
        )
    f_coords = _t4.rc4(from_idx)
    t_coords = _t4.rc4(to_idx)
    coord_idx = _STD4_AXIS_INDEX[axis]
    delta = int(t_coords[coord_idx]) - int(f_coords[coord_idx])
    theta = (math.pi / 4.0) * delta
    return complex(math.cos(theta), math.sin(theta))


# ---- Public: u_move_std4 -------------------------------------------


def u_move_std4(
    state_pre,
    move,
    axis: str,
    *,
    assume_non_capture: bool = True,
    side_to_move_post: bool = True,
) -> Union[csr_matrix, Dict[str, object]]:
    """Build the STD4_{X,Y,Z,W}-channel move unitary for a same-B_4-orbit
    non-capture move; return a marker dict for cross-orbit moves or for
    the B5 capture path.

    Construction (per ADR-001 §3.1 + ADR-003 §3.1 channels 1-4,
    **same-orbit only** per the ADR-003 amendment Option (a)):

      1. Resolve the move endpoints to linear indices.
      2. Check the B_4 orbit dichotomy via :func:`_is_same_b4_orbit`.
         If cross-orbit, return the marker dict
         ``{'strict_unitary': False, 'reason': 'cross-orbit', ...}``
         pointing at the v1.5 measurement-only re-encode.
      3. For same-orbit moves: build the similarity-transform
         ``U = e^{i * theta_a} * D_a @ U_swap @ D_a^+`` per ADR-003
         §3.1. Return as ``csr_matrix(complex128)``.

    The ADR-001 phase factor ``theta_a = (pi/4) * delta_a`` (signed
    axis displacement) is applied as a global scalar on the operator.

    **B5 capture path (Option A re-encode marker).** When
    ``assume_non_capture=False`` and the move IS a capture, the function
    returns a marker dict carrying ``psi_post_block`` computed via
    re-encoding the post-capture position. Per ADR-003 §3.1 channels
    1-4, the STD4 capture is a partial-isometry (the captured square's
    ``coord_resid * sig`` contribution at the destination is replaced
    by the moving piece's contribution); re-encoding via
    :func:`state_to_psi` reproduces this exactly. The marker carries
    ``reason='capture-rank-1-with-renorm'`` (the rank-1 algebra applies
    on the channel block per the ADR-005 amendment lineage).

    Parameters
    ----------
    state_pre
        Pre-move state. Same form as :func:`u_move_a1`: position dict
        ``{sq_index: piece_value}`` or object with a ``.position``
        attribute. Used both for the capture-detection guard and (on
        the B5 capture path) for the re-encode.
    move
        Move endpoints. Same form as :func:`u_move_a1`: 2-tuple of
        endpoints (each int or 4-tuple) or a Move4D-like object.
    axis : str
        One of ``'X'``, ``'Y'``, ``'Z'``, ``'W'`` (channels 1-4).
    assume_non_capture
        If ``True`` (default), the caller asserts the move is a
        non-capture; capture detection is skipped. If ``False`` and
        the move IS a capture, the B5 capture path runs (returns a
        marker dict with ``psi_post_block``). If ``False`` and the
        move is NOT a capture, the same-orbit / cross-orbit dispatch
        proceeds as in the ``True`` case.
    side_to_move_post : bool, optional
        Side-to-move AFTER the move is applied. Forwarded to
        :func:`state_to_psi` on the B5 capture path. Ignored on the
        non-capture path. Default ``True``.

    Returns
    -------
    csr_matrix of shape ``(4096, 4096)``, dtype ``complex128``, when
    the move is same-B_4-orbit non-capture. Sub-unitary on
    ``range(P_STD4_axis)``; strict at machine precision when
    ``|coord_resid[axis, from]| == |coord_resid[axis, to]|`` (a finer
    sub-condition that holds for ~10% of same-orbit pairs).

    dict (the cross-orbit marker) of the form::

        {
            'strict_unitary': False,
            'reason': 'cross-orbit',
            'recommendation': 'measurement-only re-encode',
            'channel': 'STD4_<axis>',
            'sq_from': from_idx,
            'sq_to': to_idx,
            'orbit_from': <0..34>,
            'orbit_to': <0..34>,
        }

    when the move crosses B_4 orbits. The bridge layer (v1.5) consumes
    this marker by routing the channel block through the
    measurement-only re-encode path established in the ADR-003
    amendment.

    dict (the B5 capture marker) of the form::

        {
            'strict_unitary': False,
            'reason': 'capture-rank-1-with-renorm',
            'channel': 'STD4_<axis>',
            'psi_post_block': ndarray[complex128, (4096,)],
            'sq_from': int,
            'sq_to': int,
            'captured_piece': PieceValue,
        }

    when ``assume_non_capture=False`` and the move IS a capture. The
    capture-path marker is returned **regardless of orbit dichotomy**
    (cross-orbit captures route through the same Option A re-encode
    path; the marker omits the orbit fields and carries ``captured_piece``
    instead).

    Raises
    ------
    ValueError
        If ``axis`` is not one of ``'X'``, ``'Y'``, ``'Z'``, ``'W'``;
        or if ``assume_non_capture=False`` and the pre-move position
        has no piece at ``from_idx``.
    TypeError
        If ``state_pre`` or ``move`` cannot be normalised.
    """
    if axis not in _STD4_AXIS_INDEX:
        raise ValueError(
            f"STD4 axis must be one of {_STD4_AXES}; got {axis!r}"
        )

    from_idx, to_idx = _coerce_move(move)

    if not assume_non_capture:
        if _is_capture(state_pre, from_idx, to_idx):
            # B5 capture path: Option A re-encode marker.
            captured = _get_captured_piece(state_pre, to_idx)
            pos_post = _apply_move_to_position(
                state_pre, from_idx, to_idx,
            )
            psi_post_full = _qm4.state_to_psi(pos_post, side_to_move_post)
            chan_idx = _STD4_CHANNEL_IDX[axis]
            start = chan_idx * CHANNEL_DIM
            end = start + CHANNEL_DIM
            psi_post_block = np.asarray(
                psi_post_full[start:end], dtype=np.complex128,
            ).copy()
            return {
                'strict_unitary': False,
                'reason': 'capture-rank-1-with-renorm',
                'channel': f'STD4_{axis}',
                'psi_post_block': psi_post_block,
                'sq_from': int(from_idx),
                'sq_to': int(to_idx),
                'captured_piece': captured,
            }

    # Step 0: ADR-003 amendment Option (a) — restrict strict-unitary
    # to same-B_4-orbit moves. Cross-orbit moves return a marker dict
    # pointing at the v1.5 measurement-only re-encode bridge work.
    orbit_arr = _get_orbit_id_of_sq()
    orbit_from = int(orbit_arr[from_idx])
    orbit_to = int(orbit_arr[to_idx])
    if orbit_from != orbit_to:
        return {
            'strict_unitary': False,
            'reason': 'cross-orbit',
            'recommendation': 'measurement-only re-encode',
            'channel': f'STD4_{axis}',
            'sq_from': int(from_idx),
            'sq_to': int(to_idx),
            'orbit_from': orbit_from,
            'orbit_to': orbit_to,
        }

    # Step 1: 4096-dim swap (the underlying basis permutation).
    U_swap = _build_swap_4096(from_idx, to_idx)

    # Step 2: ADR-001 phase factor for STD4_axis. Always applied (the
    # delta=0 case yields phase=1+0j for free, so no special-casing
    # needed; arithmetic gives us the identity multiplication for
    # axis-orthogonal moves).
    phase = _channel_phase_std4(from_idx, to_idx, axis)
    if phase != 1.0 + 0.0j:
        U_swap = phase * U_swap

    # Step 3: similarity transform D_a @ U_swap @ D_a^+ per ADR-003
    # §3.1 channels 1-4. The result has nnz pattern bounded by D_a's
    # support (the 3926 in-support squares for this axis); the per-row
    # nonzeros come from the swap permutation acting on D_a's diagonal.
    D = _get_d_std4(axis)
    Dp = _get_d_std4_pinv(axis)
    U = (D @ U_swap @ Dp).tocsr()

    if U.dtype != np.complex128:
        U = U.astype(np.complex128)
    U.eliminate_zeros()
    return U


# ---- Phase 4 B3b: FA_PAWN_{W,Y} axis-parity projectors --------------
#
# Per the B3b user-spec and ADR-003 §3.1 channels 8-9, the FA_PAWN
# channels carry the pawn-direction antisymmetric information per Oana
# & Chiru Definition 11. The encoder's FA_PAWN_W block lives in
# ``range(I (x) I (x) I (x) W_ANTI_DCT)`` (full ``C^4096`` since
# W_ANTI_DCT is rank-8); FA_PAWN_Y lives in
# ``range(I (x) Y_ANTI_DCT (x) I (x) I)``. Both are full-rank
# 4096-dim subspaces — no sub-rank quotient like A_1's 35-orbit
# reduction.
#
# The "antisymmetric projector" specified for the projector-sandwich
# construction is the **axis-parity-odd** projector:
#
#   P_FA_PAWN_W = (I_4096 - sigma_W) / 2     (rank 2048)
#   P_FA_PAWN_Y = (I_4096 - sigma_Y) / 2     (rank 2048)
#
# where sigma_W is the permutation that flips the W coordinate
# (``(x,y,z,w) -> (x,y,z,7-w)``) and sigma_Y flips the Y coordinate
# (``(x,y,z,w) -> (x,7-y,z,w)``). These are real-symmetric idempotents
# with no fixed points on the 8-lattice (since ``w = 7 - w`` requires
# the non-integer ``w = 3.5``).
#
# The sub-unitarity claim ``U^H U == P_FA_PAWN_axis`` holds at machine
# precision iff the underlying swap commutes with sigma_axis, which
# (lacking sigma's fixed points) reduces to the strict pure-axis-flip
# pair condition: ``sq_to == sigma_axis(sq_from)``. This is a much
# narrower restriction than B1's same-orbit dichotomy. The B3b test
# surface pins the strict claim to those pairs and uses xfail-strict
# on cross-parity-class samples.

# Module-level cached projectors. Built lazily on first access to
# avoid the 4096x4096 sparse-permutation construction at import time.
_SIGMA_FA_PAWN: Dict[str, csr_matrix] = {}
_P_FA_PAWN: Dict[str, csr_matrix] = {}


def _build_sigma_fa_pawn(axis: str) -> csr_matrix:
    """4096x4096 sparse permutation that flips the given axis
    coordinate of every square: ``(x,y,z,w) -> (x,y,z,7-w)`` for
    ``axis='W'`` and ``(x,y,z,w) -> (x,7-y,z,w)`` for ``axis='Y'``.

    The permutation has order 2 (involution) and no fixed points on
    the 8-lattice (``c == 7 - c`` requires ``c = 3.5``). Total nnz is
    exactly ``N_SQUARES = 4096`` (one nonzero per row). Real-symmetric
    cast to ``complex128`` for downstream dtype invariants.
    """
    if axis not in _FA_PAWN_AXIS_INDEX:
        raise ValueError(
            f"FA_PAWN axis must be one of {_FA_PAWN_AXES}; got {axis!r}"
        )
    rows = np.empty(N_SQUARES, dtype=np.int64)
    cols = np.arange(N_SQUARES, dtype=np.int64)
    for s in range(N_SQUARES):
        x, y, z, w = _t4.rc4(s)
        if axis == 'W':
            rows[s] = _t4.sq4(x, y, z, 7 - w)
        else:  # axis == 'Y'
            rows[s] = _t4.sq4(x, 7 - y, z, w)
    data = np.ones(N_SQUARES, dtype=np.complex128)
    return sp.csr_matrix(
        (data, (rows, cols)),
        shape=(N_SQUARES, N_SQUARES),
    )


def _get_sigma_fa_pawn(axis: str) -> csr_matrix:
    """Cached accessor for sigma_FA_PAWN_{axis}."""
    if axis not in _SIGMA_FA_PAWN:
        _SIGMA_FA_PAWN[axis] = _build_sigma_fa_pawn(axis)
    return _SIGMA_FA_PAWN[axis]


def _get_p_fa_pawn(axis: str) -> csr_matrix:
    """Cached accessor for the FA_PAWN axis-parity-odd projector
    ``P_FA_PAWN_axis = (I - sigma_axis) / 2``.

    Real-symmetric and idempotent by construction (sigma is order-2
    real-symmetric); rank 2048 (no sigma fixed points). Stored as CSR
    ``complex128``.
    """
    if axis not in _P_FA_PAWN:
        sigma = _get_sigma_fa_pawn(axis)
        I = sp.eye(N_SQUARES, format='csr', dtype=np.complex128)
        P = ((I - sigma) * 0.5).tocsr()
        # Numerical hygiene: eliminate explicit zeros that could
        # appear from the sparse subtract.
        P.eliminate_zeros()
        _P_FA_PAWN[axis] = P
    return _P_FA_PAWN[axis]


# ---- ADR-001 §3.1 phase factor for FA_PAWN_{W,Y} -------------------


def _channel_phase_fa_pawn(
    from_idx: int,
    to_idx: int,
    axis: str,
) -> complex:
    """Return the ADR-001 §3.1 channel phase factor for FA_PAWN_axis.

    Per ADR-001 §3.1 row "FA_PAWN_W" (channel 8, ``theta_8 = (pi/2) *
    sgn(w' - w)``) and row "FA_PAWN_Y" (channel 9, ``theta_9 =
    (pi/2) * sgn(y' - y)``). The sign-of-direction encodes the
    pawn-push asymmetry: forward push picks up ``+i = e^{i*pi/2}``,
    backward push (which in chess can only happen via a non-pawn
    move on the same square — pawns themselves don't reverse) picks
    up ``-i``. A move that doesn't touch the relevant axis (delta == 0)
    has ``sgn(0) = 0`` so the phase is exactly ``e^{i*0} = 1``.

    Parameters
    ----------
    from_idx, to_idx : int
        Linear square indices in [0, 4096).
    axis : str
        One of ``'W'`` (FA_PAWN_W, channel 8) or ``'Y'`` (FA_PAWN_Y,
        channel 9).

    Returns
    -------
    complex
        ``e^{i * theta}`` with ``theta = (pi/2) * sgn(delta_axis)``;
        i.e., one of ``{1.0, +1.0j, -1.0j}``.
    """
    if axis not in _FA_PAWN_AXIS_INDEX:
        raise ValueError(
            f"FA_PAWN axis must be one of {_FA_PAWN_AXES}; got {axis!r}"
        )
    f_coords = _t4.rc4(from_idx)
    t_coords = _t4.rc4(to_idx)
    coord_idx = _FA_PAWN_AXIS_INDEX[axis]
    delta = int(t_coords[coord_idx]) - int(f_coords[coord_idx])
    # sgn convention: -1, 0, +1. Done explicitly (not np.sign) so
    # the result is a Python int and the comparison-to-zero branch
    # gives an exact ``1.0 + 0.0j`` for axis-orthogonal moves.
    if delta > 0:
        sign = 1
    elif delta < 0:
        sign = -1
    else:
        sign = 0
    theta = (math.pi / 2.0) * sign
    return complex(math.cos(theta), math.sin(theta))


# ---- Public: u_move_fa_pawn ----------------------------------------


def u_move_fa_pawn(
    state_pre,
    move,
    axis: str,
    *,
    assume_non_capture: bool = True,
    side_to_move_post: bool = True,
) -> Union[csr_matrix, Dict[str, object]]:
    """Build the FA_PAWN_{W,Y}-channel move unitary as a 4096x4096
    sparse matrix (non-capture path) or return a marker dict (B5
    capture path).

    Construction (per ADR-001 §3.1 + ADR-003 §3.1, projector-sandwich
    form per the B3b user-spec):

      1. Build ``U_swap = swap(from_idx <-> to_idx)`` on ``C^4096``.
      2. Multiply by the ADR-001 phase factor for FA_PAWN_axis
         (``e^{i * (pi/2) * sgn(delta_axis)}``).
      3. Wrap in the ``P_FA_PAWN_axis`` projector sandwich:
         ``U_fa_pawn = phase * P_FA_PAWN_axis @ U_swap @ P_FA_PAWN_axis``
         where ``P_FA_PAWN_axis = (I - sigma_axis) / 2`` projects onto
         the axis-parity-odd subspace of ``C^4096`` (rank 2048).

    The resulting ``U_fa_pawn`` is **sub-unitary** on
    ``range(P_FA_PAWN_axis)`` iff the underlying swap commutes with
    sigma_axis; in turn this holds iff ``sq_to == sigma_axis(sq_from)``
    (a "pure axis-flip" move: only the axis coord changes and
    ``axis_to = 7 - axis_from``). For typical non-axis-flip moves the
    sandwich is contractive (``||U_fa_pawn||_op <= 1``) but does not
    satisfy ``U^H U == P_FA_PAWN_axis`` — see the module docstring's
    "B3b: FA_PAWN_W / FA_PAWN_Y — antisymmetric pawn channels"
    section.

    **B5 capture path (Option A re-encode marker, partial-isometry
    semantics).** Per ADR-003 §3.1 channels 8-9, the FA_PAWN capture
    is a partial-isometry: the captured pawn's 8-mode block is removed
    by the swap, so ``||U @ psi|| < ||psi||``. The B5 path returns a
    marker dict carrying ``psi_post_block`` computed via re-encoding
    the post-capture position. The captured pawn's contribution is
    automatically dropped by :func:`state_to_psi` (the captured pawn
    is no longer in ``pos_post``); the post-capture renormalisation
    per ADR-002 §3.4 is folded into the L2 normalisation at the
    state_to_psi layer. The marker carries
    ``reason='capture-partial-isometry'`` to distinguish the FA_PAWN
    capture algebra from the rank-1 form used by A_1 / STD4 / FD_DIAG.

    Parameters
    ----------
    state_pre
        Pre-move state. Same form as :func:`u_move_a1`: position dict
        ``{sq_index: piece_value}`` or object with a ``.position``
        attribute. Used both for capture detection and (on the B5
        capture path) for the re-encode.
    move
        Move endpoints. Same form as :func:`u_move_a1`: 2-tuple of
        endpoints (each int or 4-tuple) or Move4D-like object.
    axis : str
        One of ``'W'`` (FA_PAWN_W block, channel 8) or ``'Y'``
        (FA_PAWN_Y block, channel 9).
    assume_non_capture
        If ``True`` (default), the caller asserts the move is a
        non-capture; capture detection is skipped. If ``False`` and
        the move IS a capture, the B5 capture path runs (returns a
        marker dict with ``psi_post_block``). If ``False`` and the
        move is NOT a capture, the projector-sandwich operator is
        returned just like the ``True`` case.
    side_to_move_post : bool, optional
        Side-to-move AFTER the move is applied. Forwarded to
        :func:`state_to_psi` on the B5 capture path. Ignored on the
        non-capture path. Default ``True``.

    Returns
    -------
    csr_matrix of shape ``(4096, 4096)``, dtype ``complex128``, when
    the move is a non-capture (or when ``assume_non_capture=True``).

    dict (the B5 capture marker) of the form::

        {
            'strict_unitary': False,
            'reason': 'capture-partial-isometry',
            'channel': 'FA_PAWN_<axis>',
            'psi_post_block': ndarray[complex128, (4096,)],
            'sq_from': int,
            'sq_to': int,
            'captured_piece': PieceValue,
        }

    when ``assume_non_capture=False`` and the move IS a capture.

    Raises
    ------
    ValueError
        If ``axis`` is not one of ``'W'``, ``'Y'``; or if
        ``assume_non_capture=False`` and the pre-move position has
        no piece at ``from_idx``.
    TypeError
        If ``state_pre`` or ``move`` cannot be normalised.
    """
    if axis not in _FA_PAWN_AXIS_INDEX:
        raise ValueError(
            f"FA_PAWN axis must be one of {_FA_PAWN_AXES}; got {axis!r}"
        )

    from_idx, to_idx = _coerce_move(move)

    if not assume_non_capture:
        if _is_capture(state_pre, from_idx, to_idx):
            # B5 capture path: Option A re-encode marker, partial-
            # isometry semantics per ADR-003 §3.1 channels 8-9.
            captured = _get_captured_piece(state_pre, to_idx)
            pos_post = _apply_move_to_position(
                state_pre, from_idx, to_idx,
            )
            psi_post_full = _qm4.state_to_psi(pos_post, side_to_move_post)
            chan_idx = (
                FA_PAWN_W_CHANNEL_IDX
                if axis == 'W'
                else FA_PAWN_Y_CHANNEL_IDX
            )
            start = chan_idx * CHANNEL_DIM
            end = start + CHANNEL_DIM
            psi_post_block = np.asarray(
                psi_post_full[start:end], dtype=np.complex128,
            ).copy()
            return {
                'strict_unitary': False,
                'reason': 'capture-partial-isometry',
                'channel': f'FA_PAWN_{axis}',
                'psi_post_block': psi_post_block,
                'sq_from': int(from_idx),
                'sq_to': int(to_idx),
                'captured_piece': captured,
            }

    # Step 1: 4096-dim swap (the underlying basis permutation).
    U_swap = _build_swap_4096(from_idx, to_idx)

    # Step 2: ADR-001 phase factor for FA_PAWN_{axis}. ``e^{i * theta}``
    # with ``theta = (pi/2) * sgn(delta_axis)``; one of {1, +i, -i}.
    phase = _channel_phase_fa_pawn(from_idx, to_idx, axis)
    if phase != 1.0 + 0.0j:
        U_swap = phase * U_swap

    # Step 3: P_FA_PAWN_axis projector sandwich. P is real-symmetric
    # (sigma is real-symmetric and order-2), so the conjugate-transpose
    # simplifies to P itself.
    P = _get_p_fa_pawn(axis)
    U = (P @ U_swap @ P).tocsr()

    if U.dtype != np.complex128:
        U = U.astype(np.complex128)
    return U


# ---- Phase 4 B5: M_pawn = M_single + M_double decomposition --------
#
# Per the Phase 3.5 Probe-3 amendment to ADR-005 §3.3, the lifted pawn
# move operator ``M_pawn`` (built from
# :func:`phase_operators_4d.P_pawn4_white` lifted to a 4096×4096
# incidence matrix on the board basis) **is NOT pseudo-Hermitian under
# η = P_w as a single operator**. Probe 3 measured the residual
# ``‖M^T − P_w · M · P_w⁻¹‖_F`` for three variants:
#
#   | Variant                              | Residual    | Outcome     |
#   |--------------------------------------|-------------|-------------|
#   | Full (push + double-push + captures) | 32.0        | ❌ FAIL     |
#   | Single-push + captures (no double)   | 0.000e+00   | ✅ PASS     |
#   | Single-push only                     | 0.000e+00   | ✅ PASS     |
#
# Diagnosis: ADR-005 §3.3.1's claim ``M_white^T = M_black`` (which
# implies pseudo-Hermiticity under η = P_w via ``P_w · M_white · P_w =
# M_black = M_white^T``) **holds in the no-double-push idealisation**.
# The starting-rank double-push contributes a non-transposable rank
# component (a pawn on rank 1 can double-push to rank 3, but a pawn on
# rank 3 cannot double-push to rank 5 — no double-push from rank 3).
# This breaks the transpose identity by Frobenius residual 32.0.
#
# **Amendment to ADR-005 (Phase 3.5):** Decompose
#
#   M_pawn = M_single + M_double
#
# where:
#   - **M_single** is the single-push + captures matrix (no double-push).
#     Pseudo-Hermitian under η = P_w at residual = 0.0; safe to lift to
#     a v1.6+ pseudo-Hermitian observable.
#   - **M_double** is the double-push-only matrix (origin on starting
#     rank → destination two squares forward; no captures, no
#     single-push). η-breaking; treated separately as a non-pseudo-
#     Hermitian rank-deficient operator outside the QM framework.
#
# This decomposition lets v1.6+ promote the η = P_w pseudo-Hermitian
# observable for the dominant single-push + captures algebra, while the
# starting-rank double-push (~14% of legal pawn moves; only operative
# from the 2nd / 7th rank) is handled separately. The probe re-derives
# this decomposition empirically and the helpers below cache the
# matrices for v1.6+ consumers.
#
# **v1.5 scope:** the decomposition is exposed as a structural API
# (``_pawn_observable_decomp(axis)``) so the v1.6+ pseudo-Hermitian
# promotion has a stable lookup point. The matrices themselves are
# computed lazily via the same construction used in
# ``research/track_b_pawn_pt_symmetry_probe.py`` (Phase 3.5), so the
# probe's residual = 0.0 result is reproducible at runtime.

# Module-level cache: each axis ('W' / 'Y') maps to a dict
# ``{'single': csr_matrix, 'double': csr_matrix, 'eta': csr_matrix}``.
# Built lazily on first call to :func:`_pawn_observable_decomp` to
# avoid the 4096×4096 sparse construction at import time.
_PAWN_OBS_DECOMP: Dict[str, Dict[str, csr_matrix]] = {}


# Map FA_PAWN axis letter -> lower-case axis tag accepted by
# :func:`phase_operators_4d.phase_operators_4d.P_pawn4_white`.
_FA_PAWN_AXIS_LOWER: Mapping[str, str] = {
    'W': 'w',
    'Y': 'y',
}


def _build_m_pawn_white_axis(
    axis: str,
    *,
    include_double_push: bool,
    include_captures: bool,
) -> csr_matrix:
    """Build the white-pawn move incidence matrix as a 4096×4096
    sparse complex128 CSR.

    ``M[t, s] = 1`` iff the white pawn at ``coord(s)`` can move to
    ``coord(t)`` via :func:`phase_operators_4d.phase_operators_4d.
    P_pawn4_white` for the given ``axis`` (``'W'`` or ``'Y'``). Off-
    board destinations are dropped via the ``PHI_TO_XYZW`` lookup.

    Mirrors the construction used in the Phase 3.5 Probe-3 driver
    (``research/track_b_pawn_pt_symmetry_probe.py``) so the
    decomposition's pseudo-Hermiticity residual reproduces empirically
    at runtime. Cast to ``complex128`` for downstream dtype invariants
    (the probe uses float64; we promote here for compatibility with
    the rest of the qm_4d_dynamics module).
    """
    if axis not in _FA_PAWN_AXIS_LOWER:
        raise ValueError(
            f"axis must be one of {sorted(_FA_PAWN_AXIS_LOWER)}; "
            f"got {axis!r}"
        )
    # Lazy imports to keep the module import surface minimal.
    from chess_spectral.phase_operators_4d.phase_operators_4d import (
        P_pawn4_white, phi4,
    )
    from chess_spectral.phase_operators_4d.phase_to_coords_4d import (
        PHI_TO_XYZW,
    )
    axis_lower = _FA_PAWN_AXIS_LOWER[axis]
    axis_idx = _FA_PAWN_AXIS_INDEX[axis]   # 1 for Y, 3 for W
    # White pawn starting rank: row 1 along the pawn's forward axis.
    starting_rank = 1
    rows: list = []
    cols: list = []
    for s in range(N_SQUARES):
        coord = _t4.rc4(s)
        if include_double_push:
            on_starting = (coord[axis_idx] == starting_rank)
        else:
            on_starting = False
        origin_phi = phi4(*coord)
        try:
            phases = P_pawn4_white(
                origin_phi, axis=axis_lower,
                on_starting_rank=on_starting,
                include_captures=include_captures,
            )
        except Exception:  # pragma: no cover  (defensive: phi4 surface)
            continue
        for p in phases:
            tcoord = PHI_TO_XYZW.get(p)
            if tcoord is None:
                continue
            t = _t4.sq4(*tcoord)
            rows.append(t)
            cols.append(s)
    if not rows:
        return sp.csr_matrix(
            (N_SQUARES, N_SQUARES), dtype=np.complex128,
        )
    data = np.ones(len(rows), dtype=np.complex128)
    return sp.csr_matrix(
        (data, (np.asarray(rows), np.asarray(cols))),
        shape=(N_SQUARES, N_SQUARES),
        dtype=np.complex128,
    )


def _build_m_pawn_single(axis: str) -> csr_matrix:
    """Build the **single-push + captures** white-pawn matrix per the
    Phase 3.5 Probe-3 decomposition (η = P_w pseudo-Hermitian residual
    = 0.0).

    Equals ``M_pawn_white(axis, include_double_push=False,
    include_captures=True)``. This is the part of ``M_pawn`` that
    satisfies ``M_single^T = P_axis · M_single · P_axis⁻¹`` exactly
    (the η-pseudo-Hermitian piece per ADR-005 §3.3.1's amended claim).

    Cached at module level keyed by ``axis`` so repeated lookups (e.g.,
    from v1.6+ pseudo-Hermitian observable construction) pay the
    construction cost only once.
    """
    return _build_m_pawn_white_axis(
        axis, include_double_push=False, include_captures=True,
    )


def _build_m_pawn_double(axis: str) -> csr_matrix:
    """Build the **double-push-only** white-pawn matrix per the Phase
    3.5 Probe-3 decomposition (η-breaking residual ≠ 0).

    Computed as
    ``M_full(axis) - M_single(axis)``: the full pawn matrix minus the
    single-push + captures piece. The result has nonzero entries only
    for double-push moves (origin on the starting rank → destination
    two squares forward along the pawn's axis). This is the part of
    ``M_pawn`` that violates the pseudo-Hermiticity condition under
    η = P_axis (a pawn on the starting rank can double-push, but a
    pawn on the destination rank cannot double-push back; the
    transpose identity is broken).

    Treated separately from ``M_single`` in the v1.6+ pseudo-Hermitian
    observable construction (η-metric applies only to ``M_single``;
    ``M_double`` is handled as a non-pseudo-Hermitian rank-deficient
    operator outside the QM framework per ADR-005's Phase 3.5
    amendment).
    """
    M_full = _build_m_pawn_white_axis(
        axis, include_double_push=True, include_captures=True,
    )
    M_single = _build_m_pawn_single(axis)
    M_double = (M_full - M_single).tocsr()
    M_double.eliminate_zeros()
    return M_double


def _pawn_observable_decomp(
    axis: str,
) -> Dict[str, csr_matrix]:
    """Return the M_single / M_double / eta decomposition for the
    given pawn axis, per the Phase 3.5 Probe-3 amendment to ADR-005.

    The output dict has three keys:

      * ``'single'`` (csr_matrix, 4096×4096, complex128): the single-
        push + captures matrix per :func:`_build_m_pawn_single`.
        Satisfies ``M_single^T = eta · M_single · eta⁻¹`` exactly
        (residual ≤ 1e-12 in tests; Phase 3.5 Probe-3 measured 0.0).
      * ``'double'`` (csr_matrix, 4096×4096, complex128): the double-
        push-only matrix per :func:`_build_m_pawn_double`. η-breaking
        (the transpose identity does not hold).
      * ``'eta'`` (csr_matrix, 4096×4096, complex128): the η operator
        for this axis. For axis ``'W'``, ``eta = P_w`` (the W-axis
        parity flip ``(x,y,z,w) → (x,y,z,7-w)``); for axis ``'Y'``,
        ``eta = P_y``. Both are sparse permutation matrices with
        ``eta^2 = I``, hence Hermitian and self-inverse. Reuses the
        cached :func:`_get_sigma_fa_pawn` accessor.

    Cached at module level keyed by ``axis``. v1.6+ pseudo-Hermitian
    observable construction (when promoted from ADR-005's stub status)
    will consume this dict directly.
    """
    if axis not in _FA_PAWN_AXIS_INDEX:
        raise ValueError(
            f"pawn axis must be one of {_FA_PAWN_AXES}; got {axis!r}"
        )
    if axis in _PAWN_OBS_DECOMP:
        return _PAWN_OBS_DECOMP[axis]
    # eta = sigma_axis (the axis-parity-flip permutation; reuses the
    # cached accessor used by P_FA_PAWN_axis = (I - sigma_axis) / 2).
    eta = _get_sigma_fa_pawn(axis)
    decomp: Dict[str, csr_matrix] = {
        'single': _build_m_pawn_single(axis),
        'double': _build_m_pawn_double(axis),
        'eta': eta,
    }
    _PAWN_OBS_DECOMP[axis] = decomp
    return decomp


# ---- Phase 4 B3c: FIB_SYM_{1,2,3} measurement-only re-encode --------
#
# Per the Phase 3.5 amendment to ADR-003 §3.3, the bilinear FIB_SYM
# channels (5/6/7) ship under the **measurement-only re-encode**
# fallback. Probe 2 (track_b_linearization_quality_probe) found the
# best-effort linearization path (ADR-003 §3.2's Jacobian + polar
# decomposition) failed the ε ≤ 0.10 acceptance gate by 50-500×:
#
#   FIB_SYM_1: ε p95 = 5.64    (FAIL by ~56×)
#   FIB_SYM_2: ε p95 = 6.82    (FAIL by ~68×)
#   FIB_SYM_3: ε p95 = 46.76   (FAIL by ~468×)
#
# Structural reason: the channel value at ``s in adj(k)`` is
# ``gradient(k) * fib_d[piece(k), k, c-5]`` with ``gradient(k) =
# sum_{n in adj(k)} sig[n]``. A move changes occupancy at origin and
# destination — the ``gradient(k)`` term changes for every ``k`` in
# the move's adjacency neighborhood, AND the piece(k) selection
# changes at the destination (and origin if the destination's
# adjacency loops back). The encoder is piecewise non-smooth in
# ``delta_sig`` at every move boundary; no Jacobian J_c can capture
# the jump.
#
# Construction (no projector sandwich; no matrix):
#
#   1. Apply the move classically at the dict level (mirrors v1.4's
#      :func:`chess_spectral_4d.apply_move` non-capture, non-promotion
#      semantics):
#         pos_post = dict(pos_pre)
#         piece = pos_post.pop(from_idx)
#         pos_post[to_idx] = piece
#   2. Re-encode via :func:`chess_spectral.qm_4d.state_to_psi`
#      (45056-dim L2-normalized complex128 vector).
#   3. Slice the FIB_SYM_{fib_idx} channel block (offset
#      ``(4 + fib_idx) * CHANNEL_DIM`` for fib_idx in {1, 2, 3}).
#   4. Return as a marker dict carrying the 4096-dim ``psi_post_block``.
#
# This is structurally distinct from B1/B3a/B3b: those return a sparse
# 4096x4096 matrix `U_chan` such that `U_chan @ psi_pre[block] approx
# psi_post[block]`. B3c returns the result of the post-move encoding
# directly, no matrix involved. The marker dict shape composes with
# B3a's same-orbit/cross-orbit dual-return: both kinds of "fall back
# to measurement-only" are signaled to the bridge via
# ``isinstance(value, dict)``.


# B3c: the three FIB_SYM channel indices map fib_idx (1-based,
# user-facing) to channel index (0-based, encoder slice arithmetic).
_FIB_SYM_CHANNEL_IDX: Mapping[int, int] = {
    1: FIB_SYM_1_CHANNEL_IDX,  # 5
    2: FIB_SYM_2_CHANNEL_IDX,  # 6
    3: FIB_SYM_3_CHANNEL_IDX,  # 7
}


def _apply_move_to_position(
    state_pre,
    from_idx: int,
    to_idx: int,
) -> Dict[int, object]:
    """Apply a non-capture, non-promotion move to the position dict.

    Mirrors :func:`chess_spectral_4d.apply_move`'s non-capture path at
    the dict level (no GameState4D, no half-move clock, no FEN
    bookkeeping — the QM measurement-only path needs only the post-
    move position dict for re-encoding via :func:`encode_4d`).

    Parameters
    ----------
    state_pre
        Pre-move state. Either a position dict
        ``{sq_index: piece_value}`` or an object with a ``.position``
        attribute (e.g., :class:`chess_spectral_4d.GameState4D`).
    from_idx, to_idx
        Linear square indices in ``[0, 4096)``. Must already be
        normalised (use :func:`_coerce_move` to do so).

    Returns
    -------
    dict
        A new position dict with the moving piece relocated from
        ``from_idx`` to ``to_idx``. The pre-move dict is NOT mutated.

    Raises
    ------
    ValueError
        If ``from_idx`` is not in the pre-move position (no piece to
        move).
    """
    pos_pre = getattr(state_pre, "position", state_pre)
    if not isinstance(pos_pre, Mapping):
        raise TypeError(
            f"state_pre must be a position dict or have a .position "
            f"attribute; got {type(state_pre).__name__}"
        )
    if from_idx not in pos_pre:
        raise ValueError(
            f"no piece at from_idx={from_idx} in pre-move position; "
            "cannot apply move"
        )
    pos_post = dict(pos_pre)
    piece = pos_post.pop(from_idx)
    pos_post[to_idx] = piece
    return pos_post


def u_move_fib_meas(
    state_pre,
    move,
    fib_idx: int,
    *,
    assume_non_capture: bool = True,
    side_to_move_post: bool = True,
) -> Dict[str, object]:
    """Compute the FIB_SYM_{fib_idx} channel block via measurement-only
    re-encode (Phase 3.5 amendment to ADR-003 §3.3).

    **Structurally distinct from u_move_a1 / u_move_std4 /
    u_move_fa_pawn**: those return a sparse 4096x4096 matrix
    ``U_chan`` such that ``U_chan @ psi_pre[chan_block] approx
    psi_post[chan_block]``. ``u_move_fib_meas`` does NOT return a
    matrix. Per the Phase 3.5 Probe-2 finding (ε p95 = 5.6 / 6.8 /
    46.8 vs the 0.10 acceptance gate), no linear J_c can reproduce
    the bilinear FIB encoder formula post-move; the strict-unitary
    path is closed for FIB channels in v1.5.

    Construction (per the user-spec for B3c and the Phase 3.5
    amendment to ADR-003 §3.3 measurement-only fallback):

      1. Apply the move classically: ``pos_post = pos_pre`` with
         ``from_idx`` removed and ``to_idx`` set to ``piece(from_idx)``.
         Equivalent to v1.4's :func:`chess_spectral_4d.apply_move`
         for non-capture, non-promotion moves.
      2. Re-encode via :func:`chess_spectral.qm_4d.state_to_psi`
         with the post-move side-to-move
         (``side_to_move_post`` kwarg, default ``True``).
      3. Slice the FIB_SYM_{fib_idx} channel block from the resulting
         45 056-dim psi.
      4. Return a marker dict with ``psi_post_block`` carrying the
         4096-dim complex128 vector (and the standard ``strict_unitary
         / reason / channel / sq_from / sq_to`` keys for v1.5 bridge
         dispatch).

    Parameters
    ----------
    state_pre
        Pre-move state. Same forms as :func:`u_move_a1`: position dict
        ``{sq_index: piece_value}`` or an object with a ``.position``
        attribute (e.g., :class:`chess_spectral_4d.GameState4D`). The
        dict is consumed both for capture detection (when
        ``assume_non_capture=False``) and for the measurement-only
        re-encode itself (the entire post-move position is needed,
        not just the move endpoints, because FIB_SYM is bilinear in
        the global ``sig``).
    move
        Move endpoints. Same form as :func:`u_move_a1`: 2-tuple of
        endpoints (each int or 4-tuple) or a Move4D-like object.
    fib_idx : int
        One of ``1``, ``2``, ``3`` — selects which FIB_SYM channel
        block to extract. Maps to encoder channel index 5, 6, or 7
        respectively (per :data:`chess_spectral.encoder_4d.CHANNELS_4D`).
    assume_non_capture
        If ``True`` (default), the caller asserts the move is a non-
        capture; capture detection is skipped. If ``False`` and the
        move IS a capture, ``NotImplementedError`` is raised pointing
        at B5 (capture handling).
    side_to_move_post : bool, optional
        Side-to-move AFTER the move is applied (``True`` = white,
        ``False`` = black). Forwarded to
        :func:`chess_spectral.qm_4d.state_to_psi`'s side_to_move
        argument; controls the Z_2 superselection sign on the
        re-encoded psi (see Pre-flight 1 / ADR-004 §3.4 amendment).
        Default ``True`` so callers who don't track side-to-move
        get a consistent answer; magnitudes
        ``|psi_post_block|^2`` are unaffected by the choice (the sign
        only matters for relative-phase composition with other
        channels).

    Returns
    -------
    dict with the following keys:

        * ``'strict_unitary'`` (bool, always ``False``):
          informational marker indicating B3c uses the measurement-
          only path, not a strict-unitary matrix. The flag is constant
          for all FIB channels (no fallthrough to a strict path) and
          serves the v1.5 bridge as a dispatch hint.
        * ``'reason'`` (str, always ``'measurement-only'``):
          distinguishes B3c's marker from B3a's ``'cross-orbit'``
          marker. Both kinds tell the bridge "this channel needs
          re-encoding" but B3a's marker carries no precomputed vector
          (it just signals); B3c's marker carries ``psi_post_block``
          directly so the bridge can use it without re-running the
          encoder.
        * ``'channel'`` (str, e.g. ``'FIB_SYM_1'``): the encoder
          channel name for cross-referencing with
          :data:`chess_spectral.encoder_4d.CHANNELS_4D`.
        * ``'psi_post_block'`` (ndarray[complex128, (4096,)]): the
          measurement result. Equals
          ``state_to_psi(pos_post, side_to_move_post)[chan_offset:
          chan_offset + 4096]`` exactly (within float-rounding;
          tested at 1e-12 by test_b3c_correctness).
        * ``'sq_from'`` (int): linear square index of the move origin.
        * ``'sq_to'`` (int): linear square index of the move
          destination.

    Raises
    ------
    NotImplementedError
        If ``assume_non_capture=False`` and the move captures a piece.
        FIB capture handling is deferred to B5 alongside the other
        channels (ADR-002 capture renormalization + ADR-003 §3.1's
        partial-isometry framework).
    ValueError
        If ``fib_idx`` is not in ``{1, 2, 3}``, or if the pre-move
        position has no piece at ``from_idx`` (a malformed move).
    TypeError
        If ``state_pre`` or ``move`` cannot be normalised.

    Notes
    -----
    Independence from pre-move ψ: The output depends ONLY on the
    post-move position. Two different starting positions that yield
    the same post-move position produce identical ``psi_post_block``
    outputs. (Contrast u_move_a1 / u_move_std4 / u_move_fa_pawn,
    where the operator is constructed from the move endpoints alone
    and is then applied to the pre-move ψ — those operators care
    about pre-move amplitude, this function does not.) This is the
    structural marker of "measurement" in the QM formalism: the
    output state is determined by the post-projection basis, not the
    pre-projection amplitude.

    Performance: a single call invokes the full 45 056-dim encoder
    (one :func:`encode_4d` call) and slices a 4096-dim block. For
    typical M14.x rendering of a single move, this is one encoder
    call per FIB channel = 3 calls total per move; in practice the
    bridge will batch the three FIB channels into a single
    :func:`state_to_psi` call and slice three blocks (a single
    encoder invocation). The measurement-only path is therefore
    cheaper than a hypothetical 4096x4096 matrix construction.
    """
    if fib_idx not in _FIB_SYM_CHANNEL_IDX:
        raise ValueError(
            f"fib_idx must be one of {sorted(_FIB_SYM_CHANNEL_IDX)}; "
            f"got {fib_idx!r}"
        )

    from_idx, to_idx = _coerce_move(move)

    # Detect capture for the marker's reason / captured_piece field.
    # The construction itself is identical to the non-capture path
    # (Option A re-encode), but the marker fields differ so consumers
    # can reason about which moves dropped probability mass.
    captured = None
    is_capture = False
    if not assume_non_capture:
        is_capture = _is_capture(state_pre, from_idx, to_idx)
        if is_capture:
            captured = _get_captured_piece(state_pre, to_idx)

    # Step 1: Apply the move classically at the dict level. Mirrors
    # chess_spectral_4d.apply_move's non-capture path; for captures the
    # destination piece is silently overwritten (the captured piece's
    # contribution is dropped from the encoder input). Does NOT mutate
    # state_pre; produces a fresh dict.
    pos_post = _apply_move_to_position(state_pre, from_idx, to_idx)

    # Step 2: Re-encode via state_to_psi. The full 45 056-dim
    # L2-normalized complex128 vector. side_to_move_post controls the
    # Z_2 superselection sign (per Pre-flight 1 / ADR-004 §3.4
    # amendment). state_to_psi defends against empty positions (zero
    # vector) but our move construction guarantees a non-empty post-
    # move dict (we just inserted at to_idx, so |pos_post| >= 1).
    psi_post_full = _qm4.state_to_psi(pos_post, side_to_move_post)

    # Step 3: Slice the FIB_SYM_{fib_idx} channel block.
    chan_idx = _FIB_SYM_CHANNEL_IDX[fib_idx]
    start = chan_idx * CHANNEL_DIM
    end = start + CHANNEL_DIM
    psi_post_block = np.asarray(
        psi_post_full[start:end], dtype=np.complex128,
    ).copy()

    # Step 4: Return the marker dict. Shape composes cleanly with B3a's
    # cross-orbit marker so the v1.5 bridge can dispatch on the value
    # type uniformly. ``psi_post_block`` is the canonical "measurement
    # result" — keep its shape (4096,) consistent with the channel
    # block dimension.
    #
    # B5 capture path: when assume_non_capture=False and the move IS a
    # capture, swap the reason to 'capture-measurement-only' and
    # populate captured_piece. The construction is otherwise identical
    # (the FIB encoder formula is bilinear, so neither captures nor
    # non-captures admit a strict-unitary linearization — the Phase
    # 3.5 amendment ships measurement-only re-encode for both cases).
    if is_capture:
        return {
            'strict_unitary': False,
            'reason': 'capture-measurement-only',
            'channel': f'FIB_SYM_{fib_idx}',
            'psi_post_block': psi_post_block,
            'sq_from': int(from_idx),
            'sq_to': int(to_idx),
            'captured_piece': captured,
        }

    return {
        'strict_unitary': False,
        'reason': 'measurement-only',
        'channel': f'FIB_SYM_{fib_idx}',
        'psi_post_block': psi_post_block,
        'sq_from': int(from_idx),
        'sq_to': int(to_idx),
    }


# ---- Phase 4 B3d/e: FD_DIAG channel (rank-1 update + renormalization)
#
# Per ADR-003 §3.2 channel 10, the FD_DIAG channel admits a **rank-1
# update + renormalization** construction (NOT the projector-sandwich
# form used by A_1 / STD4 / FA_PAWN). The encoder formula at mode k:
#
#   out[k] = Σ_{occupied s} sig[s] * DIAG_DEV[piece_row(s), k]
#
# is **linear in sig** but the per-piece coefficient
# ``DIAG_DEV[piece_row, k]`` varies by piece type. ADR-003 §3.2's
# move-class analysis:
#
#   * Non-capture (same piece moves o → d, d empty): the contribution
#     at o vanishes (sig[o] → 0); the contribution at d appears
#     (sig[d] = 0 → sig_pre[o]). Both terms use the **same DIAG_DEV
#     row** (same piece type) and the **same sig magnitude** (the
#     moving piece's own pre-move sig value). Net change to the
#     channel sum is **zero**: the channel block is invariant.
#     ADR-003 calls this ``Pi_10 = identity`` on the channel block.
#
#   * Capture (piece p captures p' at d): contribution at d changes
#     from ``sig[d] * DIAG_DEV[piece_row(p'), :]`` to ``sig[o] *
#     DIAG_DEV[piece_row(p), :]``. The difference is a **rank-1
#     update** on the channel block. Phase 3.5 Probe 2 validated the
#     conditioning: cond p95 = 8.60 vs the 100 acceptance gate (well-
#     conditioned). The capture path's explicit rank-1 algebra ships
#     in B5 alongside the other capture cases (FA_PAWN partial-
#     isometry, A_1 destination value swap).
#
# v1.5 Construction (Option A for ship velocity):
# ----------------------------------------------
# For non-capture moves we return a marker dict carrying
# ``psi_post_block`` computed via re-encoding the post-move position.
# Mathematically equivalent to applying the rank-1 operator (which
# reduces to identity for non-captures), and faster to ship in v1.5
# (no explicit rank-1 algebra to materialize). Mirrors B3c's
# measurement-only re-encode shape so the v1.5 bridge dispatches
# uniformly via ``isinstance(value, dict)``.
#
# The marker carries ``reason: 'rank-1-update-with-renorm'`` so the
# bridge can log which channel used which path (B3c uses
# ``'measurement-only'``; B3d/e uses ``'rank-1-update-with-renorm'``;
# B3a's cross-orbit fallback uses ``'cross-orbit'``; B3b's cross-
# parity-class fallback uses ``'cross-parity-class'`` — all four
# reason strings are distinct and route to the same v1.5 bridge
# dispatch path but log differently).
#
# v1.7+ upgrade path (Option B): materialize the explicit rank-1
# operator ``Pi_10 = I + α · u v^T`` with α/u/v computed from the
# move geometry + DIAG_DEV + piece values. For non-captures Pi_10
# reduces to identity (apply in O(1), no encoder call needed). For
# captures Pi_10 is the unique rank-1 update producing the post-
# capture FD_DIAG block; renormalize via ADR-002's capture
# renormalization. The marker dict shape leaves room for this
# upgrade by adding optional ``rank1_alpha`` / ``rank1_u`` /
# ``rank1_v`` keys without breaking the consumer contract.


def u_move_fd_diag(
    state_pre,
    move,
    *,
    assume_non_capture: bool = True,
    side_to_move_post: bool = True,
) -> Dict[str, object]:
    """Compute the FD_DIAG channel block via the rank-1 update +
    renormalization path (Phase 4 milestone B3d/e).

    Per ADR-003 §3.2 channel 10's derivation, FD_DIAG admits a rank-1
    update + renormalization construction (NOT the projector-sandwich
    form used by A_1 / STD4 / FA_PAWN). For non-capture moves the
    rank-1 update reduces to **identity on the channel block** (the
    encoder formula's sum is invariant when the same piece moves
    between empty squares). The v1.5 implementation uses **Option A**:
    return a marker dict carrying ``psi_post_block`` computed via
    re-encoding the post-move position; this is mathematically
    equivalent to applying the rank-1 operator and faster to ship.
    The capture case ships in B5 with the explicit rank-1 algebra.

    Phase 3.5 Probe 2 validated the rank-1 path's conditioning on a
    1000-pair synthetic-capture corpus: cond p95 = 8.60 vs the 100
    acceptance gate (well-conditioned). FD_DIAG ships as designed via
    rank-1 + renormalization.

    Construction (per the user-spec for B3d/e and ADR-003 §3.2
    channel 10):

      1. Apply the move classically (re-uses
         :func:`_apply_move_to_position` from B3c): ``pos_post =
         pos_pre`` with ``from_idx`` removed and ``to_idx`` set to
         ``piece(from_idx)``.
      2. Re-encode via :func:`chess_spectral.qm_4d.state_to_psi`
         with the post-move side-to-move
         (``side_to_move_post`` kwarg, default ``True``).
      3. Slice the FD_DIAG channel block from the resulting 45 056-dim
         psi (offset ``10 * CHANNEL_DIM``).
      4. Return a marker dict with ``psi_post_block`` carrying the
         4096-dim complex128 vector. Shape composes cleanly with
         B3a/B3b/B3c markers (``isinstance(value, dict)`` dispatch).

    Parameters
    ----------
    state_pre
        Pre-move state. Same forms as :func:`u_move_a1` /
        :func:`u_move_fib_meas`: position dict ``{sq_index:
        piece_value}`` or an object with a ``.position`` attribute
        (e.g., :class:`chess_spectral_4d.GameState4D`). The dict is
        consumed both for capture detection (when
        ``assume_non_capture=False``) and for the re-encode itself
        (the entire post-move position is needed for FD_DIAG's
        per-piece-type sum across all occupied squares).
    move
        Move endpoints. Same form as :func:`u_move_a1`: 2-tuple of
        endpoints (each int or 4-tuple) or a Move4D-like object.
    assume_non_capture
        If ``True`` (default), the caller asserts the move is a
        non-capture; capture detection is skipped. If ``False`` and
        the move IS a capture, ``NotImplementedError`` is raised
        pointing at B5 (where the explicit rank-1 update +
        renormalization for FD_DIAG captures lands).
    side_to_move_post : bool, optional
        Side-to-move AFTER the move is applied (``True`` = white,
        ``False`` = black). Forwarded to
        :func:`chess_spectral.qm_4d.state_to_psi`'s side_to_move
        argument; controls the Z_2 superselection sign on the
        re-encoded psi (Pre-flight 1 / ADR-004 §3.4 amendment).
        Default ``True`` for consistency with :func:`u_move_fib_meas`.
        Magnitudes ``|psi_post_block|^2`` are unaffected; the sign
        only matters for relative-phase composition with other
        channels.

    Returns
    -------
    dict with the following keys:

        * ``'strict_unitary'`` (bool, always ``False``):
          informational marker indicating B3d/e uses the rank-1
          update path, not a strict-unitary matrix. The flag is
          constant for FD_DIAG (no fallthrough to a strict path) and
          serves the v1.5 bridge as a dispatch hint, identical to
          B3c's marker semantics.
        * ``'reason'`` (str, always
          ``'rank-1-update-with-renorm'``): distinguishes B3d/e's
          marker from B3c's ``'measurement-only'`` and B3a's
          ``'cross-orbit'``. All three route to the same v1.5 bridge
          dispatch path (re-encode-and-slice) but log differently for
          observability.
        * ``'channel'`` (str, always ``'FD_DIAG'``): the encoder
          channel name for cross-referencing with
          :data:`chess_spectral.encoder_4d.CHANNELS_4D`.
        * ``'psi_post_block'`` (ndarray[complex128, (4096,)]): the
          post-move FD_DIAG block. Equals
          ``state_to_psi(pos_post, side_to_move_post)[chan_offset:
          chan_offset + 4096]`` exactly (within float-rounding;
          tested at 1e-12 by ``test_b3d_correctness``). For
          non-captures this also equals ``state_to_psi(pos_pre, ...
          )[chan_offset:chan_offset + 4096]`` within float precision
          per the ADR-003 §3.2 channel 10 invariance result.
        * ``'sq_from'`` (int): linear square index of the move
          origin.
        * ``'sq_to'`` (int): linear square index of the move
          destination.

    Raises
    ------
    NotImplementedError
        If ``assume_non_capture=False`` and the move captures a piece.
        FD_DIAG capture handling is the rank-1 update +
        renormalization case validated by Phase 3.5 Probe 2 (cond
        p95 = 8.60); the explicit algebra ships in B5 alongside
        FA_PAWN's partial-isometry capture path and A_1's
        destination-value swap path.
    ValueError
        If the pre-move position has no piece at ``from_idx`` (a
        malformed move).
    TypeError
        If ``state_pre`` or ``move`` cannot be normalised.

    Notes
    -----
    Independence from pre-move ψ: like :func:`u_move_fib_meas`, the
    output depends ONLY on the post-move position. Two different
    starting positions that yield the same post-move position
    produce identical ``psi_post_block`` outputs.

    Performance: a single call invokes the full 45 056-dim encoder
    (one :func:`encode_4d` call) and slices a 4096-dim block. For
    typical M14.x rendering of a single move, this is one encoder
    call. The bridge can batch B3c (3 FIB channels) + B3d/e (FD_DIAG)
    into a single :func:`state_to_psi` call and slice four blocks (a
    single encoder invocation). The re-encode cost is therefore
    amortized across the marker-dict-returning channels.

    v1.7+ upgrade hook: Option B (explicit rank-1 update operator)
    can replace this re-encode call without changing the dict shape;
    add optional ``rank1_alpha`` / ``rank1_u`` / ``rank1_v`` keys for
    consumers that want to apply the operator incrementally.
    """
    from_idx, to_idx = _coerce_move(move)

    # Detect capture for the marker's reason / captured_piece field.
    # The Option A re-encode construction is identical for captures
    # and non-captures; only the marker labels differ.
    captured = None
    is_capture = False
    if not assume_non_capture:
        is_capture = _is_capture(state_pre, from_idx, to_idx)
        if is_capture:
            captured = _get_captured_piece(state_pre, to_idx)

    # Step 1: Apply the move classically at the dict level. Re-uses
    # B3c's helper which mirrors chess_spectral_4d.apply_move's
    # non-capture path; for captures the destination piece is silently
    # overwritten (which is exactly the right semantics for the
    # FD_DIAG rank-1 update — the captured piece's DIAG_DEV row drops
    # out and is replaced by the moving piece's DIAG_DEV row at the
    # same destination square). Does NOT mutate state_pre; produces a
    # fresh dict.
    pos_post = _apply_move_to_position(state_pre, from_idx, to_idx)

    # Step 2: Re-encode via state_to_psi. Full 45 056-dim L2-normalized
    # complex128 vector. side_to_move_post controls the Z_2
    # superselection sign (per Pre-flight 1 / ADR-004 §3.4 amendment).
    # state_to_psi defends against empty positions (zero vector); our
    # move construction guarantees a non-empty post-move dict (we just
    # inserted at to_idx, so |pos_post| >= 1).
    psi_post_full = _qm4.state_to_psi(pos_post, side_to_move_post)

    # Step 3: Slice the FD_DIAG channel block (offset 10 * CHANNEL_DIM
    # = 40960 in the 45 056-dim encoder vector).
    start = FD_DIAG_CHANNEL_IDX * CHANNEL_DIM
    end = start + CHANNEL_DIM
    psi_post_block = np.asarray(
        psi_post_full[start:end], dtype=np.complex128,
    ).copy()

    # Step 4: Return the marker dict. Shape composes cleanly with
    # B3c's measurement-only marker so the v1.5 bridge can dispatch on
    # the value type uniformly. ``psi_post_block`` carries the
    # post-move FD_DIAG channel block — for non-captures this equals
    # the pre-move block (per ADR-003 §3.2 channel 10's invariance
    # result), and the rank-1 update reduces to identity. The reason
    # string distinguishes B3d/e's path from B3c's so the bridge can
    # log which channels used which fallback.
    #
    # B5 capture path: same Option A re-encode (the rank-1 update
    # becomes non-trivial for captures, but Option A re-encoding the
    # post-capture position via state_to_psi reproduces the rank-1
    # update + renormalisation exactly per ADR-002 §3.4). Marker
    # carries reason='capture-rank-1-with-renorm' (matches the A_1 /
    # STD4 capture reason for consistency across the rank-1 channels).
    if is_capture:
        return {
            'strict_unitary': False,
            'reason': 'capture-rank-1-with-renorm',
            'channel': 'FD_DIAG',
            'psi_post_block': psi_post_block,
            'sq_from': int(from_idx),
            'sq_to': int(to_idx),
            'captured_piece': captured,
        }

    return {
        'strict_unitary': False,
        'reason': 'rank-1-update-with-renorm',
        'channel': 'FD_DIAG',
        'psi_post_block': psi_post_block,
        'sq_from': int(from_idx),
        'sq_to': int(to_idx),
    }


# ---- Phase 4 B2: free Hamiltonian H_0 = -Δ_{P_8^4} -----------------
#
# Per ADR-002 §3.1 (Zeno-style Option A), the QM module's free
# Hamiltonian is ``H_0 = -Δ`` where Δ is the 4D path-graph Laplacian
# ``L_{P_8} ⊕ L_{P_8} ⊕ L_{P_8} ⊕ L_{P_8}`` (Kronecker sum of four
# 8-vertex path-graph 1D Laplacians). H_0 acts on a single 4096-dim
# channel block; the full 45 056-dim space evolves as ``I_11 ⊗ H_0``,
# i.e. the eleven 4096-blocks evolve independently under the same H_0.
#
# Sign convention: the encoder's identity in Pre-flight 3 is in terms
# of Δ (not -Δ), and the reported P_8 1D spectrum
# ``[0, 0.15224, 0.58579, 1.23463, 2.0, 2.76537, 3.41421, 3.84776]`` is
# for Δ. H_0 = -Δ has the negation of the Kron-sum spectrum, i.e.
# eigenvalues in ``[-15.39103, ..., 0]`` on C^4096.

# Module-level cache. ``None`` means "not yet built"; first call to
# :func:`evolve_under_h0` (or to :data:`H_FREE_4D` via __getattr__)
# triggers :func:`_build_h_free_4d` and caches the result here.
_H_FREE_4D: Optional[csr_matrix] = None


def _l8_path_laplacian() -> csr_matrix:
    """Return the 8x8 sparse 1D path-graph Laplacian (P_8) as
    ``complex128`` CSR.

    Tridiagonal: degree on the diagonal (1 at endpoints, 2 interior),
    -1 on the super- and sub-diagonals. This is exactly
    :func:`tables_4d.p8_laplacian` cast to sparse complex128.
    """
    n = _t4.BOARD_SIDE  # 8
    # Build via three diagonals so the result is exactly tridiagonal
    # without any explicit zero entries.
    main = np.empty(n, dtype=np.complex128)
    main[0] = 1.0
    main[-1] = 1.0
    main[1:-1] = 2.0
    off = -np.ones(n - 1, dtype=np.complex128)
    L = sp.diags(
        [off, main, off], offsets=[-1, 0, 1],
        shape=(n, n), format="csr", dtype=np.complex128,
    )
    return L


def _build_h_free_4d() -> csr_matrix:
    """Build ``H_0 = -Δ_{P_8^4}`` as a 4096x4096 sparse matrix.

    Δ is the 4D path-graph Laplacian — Kronecker sum of four copies of
    the 1D 8-node path-graph Laplacian L_8. ``H_0 = -Δ`` is the standard
    free-particle kinetic energy on the lattice; its eigenvalues are
    non-positive (the spectrum of Δ is ``[0, 8 · 3.84776] ≈ [0, 15.39]``,
    so H_0's spectrum is ``[-15.39, 0]``).

    The construction here mirrors
    :func:`research/spectral_identity_4d_verification.kron_sum_laplacian_sparse`
    with ``dim=4`` and uses :func:`scipy.sparse.kron` for each tensor
    product. We do **not** use :func:`tables_4d.laplacian_4d` because
    that path goes through a 4096-square adjacency matrix; the direct
    Kron-sum form is symbolically clearer and exactly matches the
    Pre-flight 3 identity.

    Sign: returns ``-Δ`` (Hermitian, negative-semidefinite). The
    spectrum is the negation of :func:`tables_4d.kron_sum4_eigvals`'s
    output on the P_8 1D eigenvalues.

    Returns
    -------
    csr_matrix of shape ``(4096, 4096)``, dtype ``complex128``.
        Hermitian (real-symmetric, with zero imaginary part). Sparse
        with the Δ structure (each interior site has 9 neighbors,
        including itself).

    Notes
    -----
    Module-level singleton: the result is cached in :data:`_H_FREE_4D`
    on first call so repeated invocations of :func:`evolve_under_h0`
    pay the construction cost only once.
    """
    L1 = _l8_path_laplacian()                   # 8x8 sparse
    n = L1.shape[0]
    eye = sp.eye(n, format="csr", dtype=np.complex128)

    # Δ = sum_{axis in {0,1,2,3}} I ⊗ ... ⊗ L (axis) ⊗ ... ⊗ I
    delta: Optional[csr_matrix] = None
    for axis in range(4):
        factors = [eye] * 4
        factors[axis] = L1
        T = factors[0]
        for f in factors[1:]:
            T = sp.kron(T, f, format="csr")
        delta = T if delta is None else (delta + T)
    assert delta is not None
    delta = delta.tocsr()

    # H_0 = -Δ. The negation preserves sparsity pattern and dtype.
    H0 = (-delta).tocsr()
    if H0.dtype != np.complex128:
        H0 = H0.astype(np.complex128)
    return H0


def _get_h_free_4d() -> csr_matrix:
    """Cached accessor for :data:`H_FREE_4D` — builds on first call."""
    global _H_FREE_4D
    if _H_FREE_4D is None:
        _H_FREE_4D = _build_h_free_4d()
    return _H_FREE_4D


def _channel_offset(channel: str) -> Tuple[int, int]:
    """Map a channel name to its ``(start, end)`` slice into the
    45 056-dim full encoder vector.

    The 11 channel names (in order) are:
    ``A1, STD4_X, STD4_Y, STD4_Z, STD4_W, FIB_SYM_1, FIB_SYM_2,
    FIB_SYM_3, FA_PAWN_W, FA_PAWN_Y, FD_DIAG``.

    Source of truth: :data:`chess_spectral.encoder_4d.CHANNELS_4D`.
    """
    # Lazy import to avoid a top-of-file cycle.
    from chess_spectral import encoder_4d as _enc4
    for name, offset in _enc4.CHANNELS_4D:
        if name == channel:
            return int(offset), int(offset + CHANNEL_DIM)
    valid = [name for name, _ in _enc4.CHANNELS_4D]
    raise ValueError(
        f"unknown channel name {channel!r}; expected one of {valid}"
    )


def evolve_under_h0(
    psi: np.ndarray,
    t: float,
    *,
    channel: Optional[str] = None,
) -> np.ndarray:
    """Evolve ``psi`` under ``U(t) = exp(-i H_0 t)`` for time ``t``.

    Implements ADR-002 §3.1's continuous-time evolution between move
    boundaries. The operator H_0 = -Δ_{P_8^4} is Hermitian and
    real-symmetric (so ``-i H_0 t`` is anti-Hermitian and U(t) is
    unitary). Norm and ``<H_0>`` are preserved exactly up to the
    numerical precision of :func:`scipy.sparse.linalg.expm_multiply`
    (Krylov subspace; typically 1e-12 or better for the parameters
    used in M14.x).

    Parameters
    ----------
    psi : ndarray
        State vector. Two accepted shapes:

        * ``(4096,)``: a single channel block (e.g., the A_1 sub-vector).
          Evolves under H_0 directly.
        * ``(45056,)``: the full 11-channel encoder vector. By default
          all 11 blocks are evolved independently under the same H_0
          (since H_0 acts on the 4096-dim mode space, not the
          channel-typed space — equivalently, the full Hamiltonian on
          C^45056 is ``I_11 ⊗ H_0``). If ``channel`` is provided, only
          that block is evolved; the other ten are returned unchanged.

        Dtype is cast to ``complex128``.
    t : float
        Real evolution time. ``t == 0`` is a no-op (returns a copy of
        ``psi``). Negative ``t`` evolves backward in time, which is
        well-defined because U(t) is unitary and ``U(-t) = U(t)^†``.
    channel : str, optional
        One of the 11 channel names
        (``'A1'``, ``'STD4_X'``, ..., ``'FD_DIAG'``). If given, ``psi``
        must be the full 45 056-dim vector and only the named channel's
        4096-block is evolved; the other 10 are copied through. Useful
        for animating evolution per channel (M14.2 phase-as-color render
        of a single channel marginal). Raises if ``psi`` is the
        4096-dim shape.

    Returns
    -------
    ndarray of the same shape and dtype (``complex128``) as ``psi``.

    Raises
    ------
    ValueError
        If ``psi`` is not 1-D or has a shape other than ``(4096,)`` or
        ``(45056,)``; or if ``channel`` is given with a ``(4096,)``
        ``psi`` (ambiguous — the caller should drop the ``channel`` arg
        or pass the full vector); or if ``channel`` is not a recognized
        name.

    Notes
    -----
    Performance: :func:`scipy.sparse.linalg.expm_multiply` runs in
    milliseconds for typical M14.3 frames (``|t| < 0.2``,
    ``‖H_0‖ ≤ 16``, Krylov dim < 30). The full 45 056-dim case is just
    11 sequential 4096-dim calls; total cost stays within the 60 FPS
    budget on the dev box.

    Eigenbasis-diagonal optimization (ADR-002 §6.1): per Pre-flight 3,
    the encoder basis is the simultaneous eigenbasis of ``(Δ, B_4
    commutant)``, so a future v1.6+ optimization could replace
    ``expm_multiply`` with one matvec into the eigenbasis + an
    elementwise phase multiplication + one matvec out. Deferred until
    profiling shows ``evolve_under_h0`` is a hot path.
    """
    psi_arr = np.ascontiguousarray(psi)
    if psi_arr.ndim != 1:
        raise ValueError(
            f"psi must be 1-D; got shape {psi_arr.shape}"
        )
    if psi_arr.dtype != np.complex128:
        psi_arr = psi_arr.astype(np.complex128)

    # t == 0 is a no-op. Return a copy so callers don't have to worry
    # about whether the result aliases the input.
    if t == 0.0:
        return psi_arr.copy()

    H0 = _get_h_free_4d()
    # ``-1j * t * H0`` is anti-Hermitian; expm_multiply integrates one
    # column at a time. Build it as the product so scipy's pre-scaling
    # logic sees a single sparse operator.
    A = (-1j * float(t)) * H0

    # Single 4096-dim block path
    if psi_arr.shape == (CHANNEL_DIM,):
        if channel is not None:
            raise ValueError(
                "channel argument is only meaningful for full 45 056-dim "
                "psi vectors; got a single 4096-dim block. Drop the "
                "channel argument or pass the full encoder vector."
            )
        return np.asarray(expm_multiply(A, psi_arr), dtype=np.complex128)

    # Full 45 056-dim path
    if psi_arr.shape == (ENCODING_DIM,):
        out = psi_arr.copy()
        if channel is None:
            # Evolve all 11 blocks under the same H_0. expm_multiply has
            # a per-call setup cost (Krylov parameter selection); for
            # 11 blocks at typical t we still finish in a few hundred ms.
            for c in range(N_CHANNELS):
                start = c * CHANNEL_DIM
                end = start + CHANNEL_DIM
                out[start:end] = expm_multiply(A, psi_arr[start:end])
            return out
        # Channel-restricted: only the named block evolves.
        start, end = _channel_offset(channel)
        out[start:end] = expm_multiply(A, psi_arr[start:end])
        return out

    raise ValueError(
        f"psi must have shape ({CHANNEL_DIM},) or ({ENCODING_DIM},); "
        f"got {psi_arr.shape}"
    )


# Module-level lazy attribute access for ``H_FREE_4D``. We expose the
# cached singleton via __getattr__ so importers pay zero construction
# cost on import; the matrix is built only when first accessed (either
# directly via ``qm_4d_dynamics.H_FREE_4D`` or indirectly via
# :func:`evolve_under_h0`).

def __getattr__(name: str):
    if name == "H_FREE_4D":
        return _get_h_free_4d()
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )


# ---- Bridge-surface re-export ---------------------------------------
#
# The §17.1 ``applyMoveQm`` lives in :mod:`chess_spectral.qm_4d_bridge`
# (separation: this module holds the per-channel math; the bridge
# module holds the consumer-facing assembly). Re-exported here for
# convenience so callers can write ``from chess_spectral.qm_4d_dynamics
# import apply_move_qm`` if they prefer the dynamics namespace, but
# the canonical home is the bridge module.

from chess_spectral.qm_4d_bridge import apply_move_qm  # noqa: E402, F401


# ---- Public API list ------------------------------------------------

__all__ = [
    # Constants
    'N_SQUARES', 'N_CHANNELS', 'CHANNEL_DIM', 'ENCODING_DIM',
    'A1_CHANNEL_IDX',
    'FA_PAWN_W_CHANNEL_IDX', 'FA_PAWN_Y_CHANNEL_IDX',
    'FIB_SYM_1_CHANNEL_IDX', 'FIB_SYM_2_CHANNEL_IDX',
    'FIB_SYM_3_CHANNEL_IDX',
    'FD_DIAG_CHANNEL_IDX',
    # Type aliases
    'SquareLike',
    # Public builders
    'u_move_a1',
    'u_move_std4',
    'u_move_fa_pawn',
    'u_move_fib_meas',
    'u_move_fd_diag',
    # B2 free Hamiltonian + Zeno evolution
    'evolve_under_h0',
    # NOTE: H_FREE_4D is intentionally NOT in __all__ because it's a
    # lazy module attribute exposed via __getattr__; ``from
    # chess_spectral.qm_4d_dynamics import *`` would force its
    # construction at import time, which we want to avoid. Callers can
    # still access it via ``qm_4d_dynamics.H_FREE_4D``.
    # Bridge stub (canonical home: chess_spectral.qm_4d_bridge)
    'apply_move_qm',
]
