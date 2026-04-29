# ADR-003 Amendment: Strict-unitary tier restricted to same-orbit moves

**Date:** 2026-04-29
**Branch:** `chess-spectral/adr-003-amendment-strict-unitary-orbit-restriction`
**Triggering PR:** [#76](https://github.com/lemonforest/mlehaptics/pull/76) — Phase 4 milestone B1 (A_1 channel move-as-unitary).
**Amends:** [`ADR-003-per-channel-move-transformation.md`](ADR-003-per-channel-move-transformation.md) §3.1.
**Companion amendment:** [`PHASE_3_5_PROBE_RESULTS.md`](PHASE_3_5_PROBE_RESULTS.md) (FIB → measurement-only).

---

## 1. Status

**Accepted (2026-04-29; post-PR-#76 / commit `79ba509`).**

This is the **second** amendment to ADR-003. The first (Phase 3.5
Probe-2) moved FIB_SYM_1/2/3 to measurement-only re-encode. This one
restricts the strict-unitary tier itself: the projector-sandwich
construction `U_c = P_c @ swap @ P_c` is only sub-unitary on
`range(P_c)` for **same-orbit** moves; cross-orbit moves drop to the
measurement-only path that the Phase 3.5 amendment already established.

The amendment is **documentation-level for v1.5** (Option (a) below).
A v1.7+ refactor (Option (b)) is sketched but not adopted here.

---

## 2. Context

ADR-003 §3.1 sketches `Pi_0` (the A_1 channel's per-move unitary) as a
bare 4096-square swap matrix and asserts the **verification claim**

> `Pi_0 @ encode_4d_A1(pos_pre) = encode_4d_A1(pos_post)` exactly,
> provided sig values for non-`o`, non-`d` squares are unchanged.

PR #76 implemented the projector-sandwich form
`U_a1 = P_A1 @ swap @ P_A1` (which is the construction that lives
inside `range(P_A1)` and matches the encoder's A_1 subspace) and
discovered that the verification claim fails for typical chess moves.

The B1 implementation ships **as-is** with two strict-xfail tests
pinning the cross-orbit failure
([`test_qm_4d_dynamics_b1.py`](../../../python/tests/test_qm_4d_dynamics_b1.py)
`test_b1_subunitarity_cross_orbit_xfail`,
`test_b1_re_encoding_match_cross_orbit_xfail`) and a "Findings" block
in the module docstring
([`qm_4d_dynamics.py`](../../../python/chess_spectral/qm_4d_dynamics.py)
"Phase 3.5 Probe-Result Amendments" section, lines 24-46) calling for
this amendment before B3a launches. This document is that amendment.

---

## 3. Finding precision

### 3.1 Numerics from PR #76

| Move geometry | `‖U†U − P_A1‖_F` | `‖U·ψ_pre − ψ_post‖` | Test outcome |
|---|---|---|---|
| Same-orbit non-capture | **1e-14** | **1e-14** | 13/13 strict tests PASS |
| Cross-orbit non-capture (typical) | 1e-2 to 3e-1 | 1e-2 to 3e-1 | 2/2 strict-xfail (trips on unexpected PASS) |

Same-orbit residuals are at machine precision. Cross-orbit residuals
exceed the 1e-10 strict-unitary tolerance by **8 to 12 orders of
magnitude** — this is a structural failure, not a numerical one.

### 3.2 Why: projector-sandwich commutativity

`P_A1` is the A_1 orbit-mean projector on the B_4 action over
`Z_8^4`. By construction, `P_A1 @ e_s = (1/|orbit(s)|) Σ_{s' ∈ orbit(s)} e_{s'}`
for every basis vector `e_s`. Two facts follow algebraically:

1. **`swap_{from,to}` commutes with `P_A1` iff `from` and `to` lie in
   the same B_4 orbit.** When they share an orbit, swapping them
   permutes within an orbit-mean and leaves the orbit-mean invariant.
   Cross-orbit swap mixes two distinct orbit-means and cannot be
   absorbed into `P_A1`.

2. **The sandwich `P_A1 @ swap @ P_A1` is sub-unitary on `range(P_A1)`
   exactly when `[swap, P_A1] = 0`.** Otherwise `U†U` picks up
   off-diagonal mass from the non-commuting pair.

Z_8^4 has **35 B_4 orbits**, of sizes {16, 64, 96, 192, 384} (sum =
4096). Most ordered pairs of distinct squares belong to different
orbits; "same-orbit" is a sparse subset of legal chess moves. The
strict-unitary path therefore covers only a small fraction of the move
space if interpreted under ADR-003 §3.1's original scope.

### 3.3 Propagation to the rest of the strict-unitary tier

ADR-003 §3.1's strict-unitary roster is `{A_1, STD4_X, STD4_Y, STD4_Z,
STD4_W, FA_PAWN_W, FA_PAWN_Y}`. Their constructions share the
projector-sandwich shape:

* **STD4_X/Y/Z/W (B3a):** `Pi_a = D_a @ swap @ D_a^{-1}` (rescaled
  swap; ADR-003 §3.1 channels 1-4). The rescaling is diagonal and
  commutes with the orbit projector iff the swap does — i.e., the same
  orbit dichotomy applies. **Predicted to fail cross-orbit by the
  same mechanism**; B3a's tests will quantify.
* **FA_PAWN_W/Y (B3b):** block scatter on 16-mode `(sx, sy, sz, *)`
  blocks via `W_ANTI_DCT` / `Y_ANTI_DCT` (ADR-003 §3.1 channels 8-9).
  The relevant projector here is the antisymmetric DCT block selector,
  not `P_A1`; B3b's structure is **orthogonal sub-channel decomposition**
  (rather than orbit-quotient) and may avoid the dichotomy. **To be
  confirmed by B3b's tests** before declaring strict-unitary scope.
* **FD_DIAG (B3d/e, channel 10):** rank-1 update on a piece-coefficient
  diagonal. **Orbit issue does not apply** (no projector sandwich; the
  rank-1 + renormalization path validated in Phase 3.5 Probe-2 is
  unchanged).

The "predicted same-orbit-only" outcome for STD4 is a load-bearing
guess, not yet probed; B3a's test surface must include the
same-orbit / cross-orbit dichotomy explicitly.

---

## 4. Decision

### 4.1 v1.5: adopt Option (a) — restrict + measurement-only fallback

ADR-003 §3.1's strict-unitary tier is **restricted to same-orbit
non-capture moves** for channels A_1 and (predicted) STD4_*. Cross-orbit
non-capture moves drop to the §3.3 measurement-only re-encode path
established by the Phase 3.5 FIB amendment.

**Rationale:**

* **Ship velocity.** Option (a) is configuration-level: which moves take
  which path. No architectural redesign. B2, B3a, B3b can proceed in
  parallel with this amendment landing.
* **Phase 3.5 precedent.** The FIB amendment established measurement-only
  re-encode as an honest QM-formalism fallback (a measurement-then-
  evolution sequence). Re-using the same fallback for cross-orbit
  strict-unitary moves is conceptually consistent and re-uses the
  same infrastructure.
* **Test surface preserved.** B1's xfail-strict tests already pin the
  cross-orbit residual. Cross-orbit measurement-only re-encode produces
  correct `ψ_post` without claiming strict unitarity, so the
  re-encoding-match assertion still holds — it just routes through a
  different code path. No test changes needed in B1; B3a/B3b's tests
  must mirror the same-orbit / cross-orbit split.
* **Zeno semantics.** Cross-orbit transitions naturally fit ADR-002's
  Zeno-style evolution as projector-mediated jumps, which is exactly
  what the measurement-only re-encode implements operationally.

### 4.2 Acceptance criteria for the v1.5 strict-unitary tier

For each channel claiming strict-unitary status in v1.5, the
implementation must:

1. Detect the same-orbit / cross-orbit case at construction time
   (cheap: precomputed `orbit_id_of_sq` lookup; 35 orbits over 4096
   squares).
2. Build the projector-sandwich form (or its channel-specific analogue)
   only when the move is same-orbit; otherwise route to the
   measurement-only re-encode of that channel.
3. Document the dichotomy in the module docstring and in the per-move
   return value (e.g., a flag indicating which path was taken).
4. Test surface: `‖U†U − P_c‖_F < 1e-10` on a sample of ≥ 30 same-orbit
   non-capture moves; cross-orbit cases verified to route to
   measurement-only and recover `ψ_post` from `encode_4d` re-encoding
   within 1e-10.

### 4.3 Updated strict-unitary tier roster

| # | Channel | v1.5 strict-unitary scope | v1.5 fallback path | Status |
|---|---|---|---|---|
| 0 | A_1 | **Same-orbit non-capture only** | Cross-orbit → measurement-only re-encode | ✅ Verified by B1 (PR #76) |
| 1 | STD4_X | Same-orbit non-capture only (predicted) | Cross-orbit → measurement-only | ⚠️ To verify in B3a |
| 2 | STD4_Y | Same-orbit non-capture only (predicted) | Cross-orbit → measurement-only | ⚠️ To verify in B3a |
| 3 | STD4_Z | Same-orbit non-capture only (predicted) | Cross-orbit → measurement-only | ⚠️ To verify in B3a |
| 4 | STD4_W | Same-orbit non-capture only (predicted) | Cross-orbit → measurement-only | ⚠️ To verify in B3a |
| 8 | FA_PAWN_W | Strict (orthogonal sub-channel — to confirm) | Cross-orbit issue may not apply; capture → partial isometry per §3.1 | ⚠️ To verify in B3b |
| 9 | FA_PAWN_Y | Strict (orthogonal sub-channel — to confirm) | As FA_PAWN_W | ⚠️ To verify in B3b |
| 10 | FD_DIAG | Rank-1 + renormalization (orbit issue N/A) | Phase 3.5 path unchanged | ✅ Probe-2 validated |
| 5-7 | FIB_SYM_1/2/3 | — (measurement-only) | Phase 3.5 amendment | ✅ Probe-2 validated |

The aggregate v1.5 unitarity claim weakens correspondingly: for
non-capture moves, **same-orbit moves are strictly unitary on the
strict-tier channels**; cross-orbit moves use measurement-only
re-encode on those channels (with FA_PAWN possibly retaining strict
behavior pending B3b).

---

## 5. Implications for downstream milestones

### 5.1 B3a (STD4_X/Y/Z/W)

* **Test surface MUST include the same-orbit / cross-orbit split.** The
  test module should generate same-orbit and cross-orbit pairs (re-using
  B1's `_gen_same_orbit_pairs` / `_gen_cross_orbit_pairs` helpers or
  equivalents) and assert strict unitarity only on the same-orbit subset.
* **Implementation pattern follows B1.** Routing logic at the
  `u_move_std4_*` builder level: detect orbit case, dispatch to
  projector-sandwich (same-orbit) or measurement-only re-encode
  (cross-orbit). The dispatch should be a shared helper across A_1 and
  STD4_*.
* **D_a boundary case (ADR-003 §6 Open Q4).** Where `coord_resid[a, *]`
  has zero entries (256 central-axis squares per channel), the
  similarity transform is ill-defined. ADR-003's pad-with-identity fix
  remains applicable; orthogonality to those rows means the orbit
  dichotomy plays no role there.

### 5.2 B3b (FA_PAWN_W/Y)

* **Verify whether the orbit dichotomy applies.** FA_PAWN's projector
  is the W/Y antisymmetric DCT block selector, not `P_A1`. Construct a
  probe analogous to B1's cross-orbit test and measure
  `‖U_pawn† @ U_pawn − P_pawn‖_F` on cross-block pawn moves. If the
  residual is at machine precision regardless of pawn-block geometry,
  FA_PAWN_W/Y stays strict-unitary unconditionally for non-captures; if
  not, this amendment's restriction extends to FA_PAWN with a similar
  measurement-only fallback.
* **Capture path unchanged.** FA_PAWN's capture handling remains the
  partial-isometry path of ADR-003 §3.1 + ADR-002 renormalization,
  independent of the orbit issue.

### 5.3 B5 (capture-move dispatcher)

* The capture-move path was already a partial-isometry / rank-1-update
  case under ADR-003. **No additional restriction from this amendment**
  — capture handling routes through ADR-002's renormalization regardless
  of orbit geometry. The amendment narrows the *non-capture* strict-
  unitary path; capture handling is orthogonal.
* The dispatcher in `apply_move_qm` (per `qm_4d_bridge.py`) needs **two
  conditions** at routing time: capture-vs-non-capture (existing) AND
  same-orbit-vs-cross-orbit (new). The four-way table is well-defined
  per channel.

### 5.4 ADR-002 (time-evolution semantics)

No change required. The Zeno-style evolution and capture renormalization
are unchanged. Cross-orbit measurement-only re-encode fits naturally
under the Zeno framing as a projector-mediated jump between channel
subspaces.

### 5.5 ADR-004 (Z_2 superselection)

No change required. Phase 3.5 Probe-4's amendment moved Z_2 sector flip
to `state_to_psi`'s sign multiplier; the orbit-restriction here is
upstream of that and does not interact.

---

## 6. Option (b) — orbit-quotient refactor (deferred to v1.7+)

The v1.7+ candidate refactor noted in B1's findings docstring works on
the **35-dim orbit quotient** rather than the full 4096-dim channel
space. `range(P_A1)` is naturally 35-dimensional (one mean value per
B_4 orbit); a move from `o` (in orbit `a`, size `n_a`) to `d` (in orbit
`b`, size `n_b`) induces the deterministic quotient-space update

```
m_a → m_a − sig[o] / n_a
m_b → m_b + sig[o] / n_b
```

— a non-unitary translation by `(−v/n_a, +v/n_b)` on the two affected
orbit-mean components, identity on the other 33 orbits.

**Pros:**
* Geometrically natural. Uses the full B_4-orbit reduction structure
  rather than embedding it in a redundant 4096-dim representation.
* Eliminates the dichotomy: same-orbit and cross-orbit moves are both
  expressible in the same closed form (same-orbit reduces to
  `m_a → m_a` because the from / to terms cancel).
* Could simplify the spectral identity (Pre-flight 3) since the orbit
  quotient is the natural reduction modulo B_4.

**Cons:**
* **Semantic shift in the API.** `apply_move_qm` returns a per-channel
  ψ in `C^4096`; switching one channel to live in the 35-dim quotient
  breaks the uniform per-channel interface. Either every consumer
  learns about the quotient embedding, or there's a 4096↔35 lift
  layer that re-introduces the projector machinery.
* **Reconciling with the channel PVM.** Notebook §15.2(3) frames the
  11-channel decomposition as a built-in PVM on the encoder. The
  quotient view changes which Hilbert space the A_1 PVM lives on
  (35-dim quotient vs. `range(P_A1) ⊂ C^4096`). Channel-projector
  observables in Phase 6's QM evaluator need re-derivation.
* **Substantial refactor of `qm_4d.py` / `qm_4d_dynamics.py`.** The
  existing P_A1 / encoder integration would need a parallel
  quotient-space implementation that interoperates with Track A's
  kinematic operators. ~600-1000 LOC; defers v1.5 ship.

**Recommendation:** Treat Option (b) as a **v1.7+ research direction**
rather than a v1.5 production change. Revisit if Phase 6's QM
evaluator empirically benefits from the orbit-quotient picture, or if
the v1.7+ Stinespring dilation work (already deferred per ADR-002)
makes the larger refactor opportune. Until then, the v1.5 strict-tier
ships under Option (a) and accepts the same-orbit-only narrowing as
documented.

---

## 7. References

* **ADR-003 (original):**
  [`ADR-003-per-channel-move-transformation.md`](ADR-003-per-channel-move-transformation.md) §3.1 — the strict-unitary tier construction this amends.
* **Phase 3.5 probe results:**
  [`PHASE_3_5_PROBE_RESULTS.md`](PHASE_3_5_PROBE_RESULTS.md) — first
  ADR-003 amendment (FIB → measurement-only); structural template for
  this document.
* **PR #76:**
  [chess-spectral Phase 4 B1: A_1 channel move-as-unitary + bridge stub](https://github.com/lemonforest/mlehaptics/pull/76)
  — implementation that surfaced the finding; merged at commit
  `79ba509`.
* **B1 implementation:**
  [`qm_4d_dynamics.py`](../../../python/chess_spectral/qm_4d_dynamics.py)
  — module docstring "Phase 3.5 Probe-Result Amendments" section
  (lines 24-46) + `u_move_a1` builder.
* **B1 tests:**
  [`test_qm_4d_dynamics_b1.py`](../../../python/tests/test_qm_4d_dynamics_b1.py)
  — module docstring "Findings" block (lines 33-59);
  `test_b1_subunitarity_cross_orbit_xfail`,
  `test_b1_re_encoding_match_cross_orbit_xfail` (strict-xfail markers
  pinning the cross-orbit residual at lines 287-326 and 407-445).
* **ADR-001 / ADR-002 / ADR-004 / ADR-005:** unchanged by this
  amendment. See README.md for the full set.
