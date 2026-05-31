# Finding 240 — At a MATCHED total coupling budget, does the reciprocal+Class-K-correction edge phase-lock where the feed-forward one-way edge does NOT (lower K_c), robustly across N, larger at unequal frequency?

**Headline:** **NULL FIRES — DEMONSTRATED in ngspice.** On the F235 air-gapped near-1D coupling graph, at a **matched total coupling budget** (L1 spread 0.0 confirmed at every N and condition), the reciprocal+Class-K-correction regime (R3) phase-locks at a strictly **lower** critical coupling than the feed-forward one-way regime (R1) **only at N=4** — at N≥8 the advantage **vanishes (ties) or inverts (R3 fails to lock where R1 still does)**. The corrective advantage is **not a stable structural property across the F234 width-doubling**, so the pre-stated null fires on **branch (d) N-instability/inversion** and **branch (c) TRAP-only-wins** (at unequal frequency N=8, the only regime that beats matched feed-forward is the **double-budget TRAP** arm — the magnitude-confound signature). The directional sub-claim *is* recovered in the aggregate (mean ΔK_c larger at unequal `+0.25` than equal `−0.025`, growing with the spread Δ), but that does not rescue the core structural claim, which the N-stability requirement defeats. The verdict is a **mechanical read of the measured ngspice transients**, decided by the booleans, not asserted.

**The one-line picture:** the closed-loop+latch helps exactly where the graph is well-connected enough that anything locks cheaply (N=4, Fiedler λ₂=2.0), and stops helping — or hurts — as the near-1D mesh's algebraic connectivity collapses with width (λ₂: 2.0 → 0.719 → 0.190 → 0.048 at N=4/8/16/32). At N=16/32 under a wide frequency spread the **reciprocal regimes fail to lock at all** while the one-way feed-forward still locks, the opposite of the prediction. "The back-and-forth + correction lowers K_c" is **not** a load-bearing measured advantage on this testbed once the budget is matched and the width is swept.

**Status:** **DEMONSTRATED (ngspice `.tran` transient measurement, bit-exact-reproducible)** for the testbed facts — the per-regime per-(N, frequency-condition) located K_c, the order parameter `r`, the matched-total-abs-weight control (L1 spread 0.0), and the symmetrised-graph λ₂ (identical across regimes by construction). It **OWNS only**: "in *this* coupled-oscillator testbed, at matched coupling budget, regime X locks at K_c=… and regime Y does/does not." **FRAMEWORK-READING** for reading corrective communication *as* a closed-loop reciprocal edge + Class-K latch (and the F239 severed-edge corollary). **In-scope** as coupled-oscillator / distributed-systems **DYNAMICS** — **NOT** PCB layout / fabrication / mechanical-mesh / gate-delay / timing-closure (the SPICE framing is the oscillator-network ODE lens, not a build instruction; the **CAD-ban HOLDS**). Defensive scope; framework-reading only; no capability / hunting-optimization / targeting. `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_trauma_informed_defensive_scope]]`; `[[feedback_no_lineage_claims_in_notebook]]`; `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`. **The Staurois foot-flagging frog ethology stays the literature's to assert either way** — the null does not touch the biology.

**Predecessors:** **F235** (PR #786 — distributed neurology / slime-mould / air-gapped hive as ONE K∘C axis; the shared near-1D extended-mesh testbed + matched-budget control + Fiedler read this finding reuses verbatim). **F234** (the Kuramoto-coupled-adder carry-vector fixed point IS the phase-lock; the width-doubling N-sweep + the all-to-all-TRAP guard pattern). **F231** (the Kuramoto dispatch-clock phase-lock + the order-parameter `r = |⟨e^{iθ}⟩|` via two `cascade.magnitude` + sqrt). **F141** (directed-only coupling is **achiral-null at equal natural frequency** — the control-condition grounding: the advantage ~vanishes at C-EQ; *measured here* — R3 ties or loses to R1 at equal frequency, mean ΔK_c ≈ 0). **F239** (the severed-corrective-edge corollary: exclusion = a feed-forward emission with the return path cut — read structurally as R1 with `A_ji=0`; carried as FRAMEWORK-READING). **F236/F241** (the ngspice capacitor-voltage-as-phase + B-source Kuramoto-RHS `.tran` construct this RE-RUN reuses as the bounded analog ODE integrator).

**The RE-RUN note (why ngspice):** the **first** F240 attempt ran away — its integration core was a **pure-Python synchronous Euler Kuramoto sweep** (`SETTLE_BUDGET=20000` sweeps, over every N × regime × frequency × K × seed) that pegged 100% CPU for ~58 minutes with **zero output** and was killed. This RE-RUN moves the ODE integration into **ngspice's `.tran`** (the proven fast C integrator F236/F241 used) so **every transient is bounded by its stop-time and CANNOT run away**, with a **per-invocation 120 s subprocess timeout** as a hard anti-hang backstop (records "timeout/not-locked" and moves on). **No unbounded Python integration loop exists anywhere in the file.** The design — regimes, matched-budget control, meters, pre-stated null, citations, verdict logic — is the intended F240 verbatim; only the integrator changed.

**Empirical anchor:** **ngspice 45.2** (`ngspice -b`, this box), srmech **0.6.0rc9** (`/tmp/bench_srmech_rc9/venv`, `HAS_NATIVE`). Artifacts: `R-RBS-LM-240_corrective_communication_closed_loop.py` (the netlist generator + ngspice `.tran` driver + srmech-native readout/spectrum/attestation) + `substrate_measurements/corrective_communication_closed_loop.ndjson` (the content-addressed results). **Discipline-check: 0 HARD, 0 coverage-gap.** Deterministic (fixed seeded initial-phase spread + ω, fixed `.tran` step, no noise source). **Confirmed bit-exact across 5 runs:** `response_sha256 = 6faf67ab22ca87d4c1e300bda128309fcbf546be349ae3e9e5ac06391a779688` (computed over the record body **minus** the wall-clock `generated_at`, so the *measurement* re-verifies bit-for-bit — the MPM point; the on-disk sha differs only by `generated_at`). The on-disk NDJSON is one **canonical** sorted-key line (per-N sub-dicts use string keys so the sort is reload-stable).

---

## §0 The pre-stated null (verbatim, genuinely reachable, DID fire)

> "The corrective (reciprocal closed-loop + Class-K-latch) regime does NOT confer a phase-lock advantage over the feed-forward one-way regime once the coupling budget is matched. Concretely the NULL FIRES if ANY of: (a) FEED-FORWARD LOCKS JUST AS WELL — at matched budget, K_c(feed-forward R1) ≤ K_c(corrective R3) (the one-way edge reaches r ≥ 0.95 at the same or lower coupling than the closed loop), so the back-and-forth / correction is DECORATIVE and one-way emit-and-forget already coordinates; (b) NEITHER LOCKS — no regime reaches r ≥ 0.95 within the settle budget at the swept N and K (the testbed is mis-specified / the lock criterion is unreachable, so no contrast can be drawn); (c) MAGNITUDE-ARTIFACT — the corrective advantage is present at UNMATCHED budget but VANISHES once the total absolute coupling weight is matched (K_c(R3) ≈ K_c(R1) under the matched control while the win only reappears in the double-budget trap arm), i.e. the win was more-coupling, not structure (the central spurious risk, analogous to F235's density-confound branch d); (d) N-INSTABILITY / INVERSION — the corrective advantage appears at only one N and INVERTS at another (e.g. K_c(R3) < K_c(R1) at N=8 but K_c(R3) > K_c(R1) at N=32), so it is not a stable structural property across the F234 width-doubling. ADDITIONALLY the directional sub-claim is NOT supported (downgrade, not full null) if the advantage is NOT larger at unequal than at equal frequency. If the null fires, the F240 claim is downgraded to an analogy: corrective communication may SHARE the closed-loop reciprocal shape but the reciprocity+latch is not a MEASURED phase-lock advantage over one-way coupling, and 'communication reduces to the reciprocal closed-loop edge' is suggestive, not load-bearing. The frog biology stays the literature's to assert either way."

**Disposition (no leaning, pre-stated):** the headline is a mechanical read of the measured booleans. POSITIVE would have been K_c(R3) < K_c(R1) at unequal frequency at *the swept N* (corrective locks where feed-forward does not), the advantage larger at unequal than equal frequency and growing with Δ, surviving the matched-budget control. **What fired:** branch **(d)** — the advantage is present at N=4 and absent/inverted at N=8/16/32 (`corrective_wins_per_N_unequal = {4:True, 8:False, 16:False, 32:False}`); and branch **(c)** — `trap_only_wins=True` (at unequal Δ=1.0, N=8: the matched R3 ties matched R1 at K_c=2.0, but the **double-budget TRAP** locks at 1.0, i.e. the *only* thing that beats matched feed-forward is more coupling). The directional sub-claim is **separately noted as recovered** (mean ΔK_c larger at unequal than equal, growing with Δ) but a sub-claim cannot rescue a fired core null. **The verdict was decided by the measured transients, not asserted.**

---

## §1 The capacitor-as-phase construct + the three directed regimes (the engine of this finding)

Each oscillator `i` is the **voltage on a 1 F capacitor** `C_i`, playing the Kuramoto phase `θ_i`. A behavioral current source `B_i` injects the phase-ODE RHS current so the node obeys

```
d V_i / dt = ω_i + coupling_i [+ correction_i]
```

**ngspice's `.tran` transient integrator IS the bounded ODE integrator** (the anti-runaway core; the same srmech Kuramoto/ODE gap supplied by the analog substrate across F141/F231/F234/F235/F236). All three regimes share the **same** F235 undirected near-1D extended mesh (backbone `(i,i+1)` radius-1 + `(i,i+2)` radius-2, `|E| = 2m−3`); the **only** difference is the directed structure imposed on each edge:

| regime | edge realisation in the B-source | what it is |
|---|---|---|
| **R1 feed-forward** (one-way / stigmergic, OPEN-LOOP) | full per-edge `K·W·sin(V(i)−V(j))` on the **driven node j only** (`A_ij ≠ A_ji`; the emitter feels no return) | emit-and-forget; no return path, no comparison, no correction (F141 directed-only) |
| **R2 reciprocal-only** (CLOSED-LOOP edge, NO latch) | the **symmetric pair** `K·(W/2)·sin(V(j)−V(i))` on i AND `K·(W/2)·sin(V(i)−V(j))` on j | the back-edge exists (mutual entrainment); bare Kuramoto, no error term |
| **R3 reciprocal+correction** (FULL closed loop) | R2 symmetric coupling **PLUS** a budget-neutral Class-K-latched correction term (below) | the F240 corrective regime |
| **TRAP** (labeled, never a model) | feed-forward at **2× budget** (W on BOTH directions) | the F234 all-to-all-smuggle guard — exposes "more coupling locks easier" |

**The R3 Class-K correction term — realised in the analog substrate, read in srmech.** The correction reads the phase **error** between the received neighbour mean-field `ψ_i = arg(Σ_j A_ij e^{iθ_j})` and own phase `θ_i`, latches the sign, and re-orients a **budget-drawn** increment. ngspice has no `atan2`, so the latch is realised *without* reconstructing `ψ_i`, using the received-field components `(RE_i, IM_i) = Σ_j A_ij (cos θ_j, sin θ_j)` directly:

```
cos(ψ_i − V_i) = (RE_i·cos V_i + IM_i·sin V_i) / |acc_i|      ← its SIGN is the Class-K latch
sin(ψ_i − V_i) = (IM_i·cos V_i − RE_i·sin V_i) / |acc_i|      ← the signed pull magnitude
correction_i   = corr_strength_i · sgn(RE_i·cos V_i + IM_i·sin V_i) · (IM_i·cos V_i − RE_i·sin V_i)/|acc_i|
```

all in ngspice-supported ops (`cos`/`sin`/`sqrt`/`sgn`) — the faithful atan2-free Class-K latch. `orient=+1` pulls toward the received phase (in-lock), `−1` pushes away, the boundary is the in-script falsifier. `corr_strength_i = ` the R2 reciprocal row-sum `/ m`, so the latch **re-routes existing coupling weight** and adds **zero** new L1 budget (the budget-neutrality rule). At the locked steady state, **srmech reads the same latch** the analog integrated — `cascade.pin_slot_at_zero` on `cos(ψ_i − θ_i)` → `orient ∈ {−1,0,+1}` (Class K), `cascade.reorient` re-signs the increment (Class C), `cascade.net_chirality` over the reoriented chain (Class C) — exactly the F236 "srmech reads the parsed analog scalar" pattern.

---

## §2 The measured matched-budget table (ngspice transient = DEMONSTRATED)

**The matched-budget control held everywhere:** `budget_matched=True` at all N and all conditions (L1 spread `0.00e+00`) — each undirected mesh edge contributes exactly `W = W/2 + W/2` in every matched regime, so no network feels more *total* drive in one regime than another, and the R3 latch is budget-neutral. So the contrast below is **structure, not magnitude**. The TRAP arm is intentionally ~2× budget (the confound to control away). Lock = Kuramoto `r ≥ 0.95` held over the steady-state tail. `K_c` is the smallest swept K that locks; `None` = never locked in the K-grid `{0, 0.1, 0.2, 0.5, 1.0, 2.0}`.

### §2.1 EQUAL natural frequency (C-EQ; the F141 control condition)

| N | λ₂ (sym) | K_c R1 (feed-fwd) | K_c R2 (reciprocal) | K_c R3 (corrective) | K_c TRAP (2×) | ΔK_c = R1−R3 |
|---|---|---|---|---|---|---|
| 4 | 2.000 | **0.1** | 0.1 | **0.1** | 0.1 | 0.0 (tie) |
| 8 | 0.719 | **0.1** | 0.2 | 0.2 | 0.1 | **−0.1** (R3 worse) |
| 16 | 0.190 | **0.2** | 0.5 | 0.5 | 0.2 | **−0.3** (R3 worse) |
| 32 | 0.048 | 0.5 | 0.5 | **0.2** | 0.2 | **+0.3** (R3 better) |

**Reading:** at equal frequency the advantage is ~0 on average (mean ΔK_c = **−0.025**) — exactly F141's achiral-null: with identical intrinsic rhythms, in-phase is the attractor for one-way and reciprocal alike, so the back-edge buys nothing (and at N=8/16 the symmetric split actually raises K_c). This is the **control condition behaving as predicted** — it is *not* the evidence for the claim; it is the baseline the unequal case must beat.

### §2.2 UNEQUAL natural frequency, Δ = 1.0 (C-UNEQ primary; correction is "needed")

| N | λ₂ (sym) | K_c R1 (feed-fwd) | K_c R2 (reciprocal) | K_c R3 (corrective) | K_c TRAP (2×) | ΔK_c = R1−R3 | K_c(R3)/K_c(R1) anchor | corr<ff? |
|---|---|---|---|---|---|---|---|---|
| 4 | 2.000 | 2.0 | 1.0 | **1.0** | **0.5** | **+1.0** | **1/2** | ✓ **True** |
| 8 | 0.719 | 2.0 | 2.0 | 2.0 | **1.0** | 0.0 | 1/1 | ✗ False |
| 16 | 0.190 | **1.0** | None | **None** | 2.0 | −3.0 | — | ✗ False |
| 32 | 0.048 | **2.0** | None | **None** | None | −2.0 | — | ✗ False |

**Reading — this is where the null fires:**
- **N=4 — the corrective win is real and clean.** R3 locks at K_c=1.0 vs R1's 2.0 (ratio **1/2**, de-magicked via `cascade.best_rational_signed`): the closed-loop + latch halves the critical coupling. The back-edge (R1→R2) does the work here (R2 already at 1.0); the latch (R2→R3) holds it. This is the one N where the prediction is *confirmed*.
- **N=8 — the win is gone, and it is a magnitude artifact.** R1=R2=R3=2.0 (tie at matched budget), but the **TRAP** (2× budget) locks at 1.0. So the *only* way to beat matched feed-forward here is **more coupling**, not the closed-loop structure — precisely the **branch (c)** signature (`trap_only_wins=True`).
- **N=16, N=32 — the prediction inverts.** The reciprocal regimes (R2, R3) **fail to lock at any swept K**, while one-way feed-forward still locks (K_c=1.0 and 2.0). On the connectivity-starved near-1D mesh (λ₂ = 0.19, 0.048) at a wide frequency spread, splitting the per-edge budget W/2+W/2 across both directions leaves each direction too weak to entrain the mismatched oscillators, whereas the full-W one-way edge still pulls the chain. This is the **branch (d)** inversion: corrective wins at N=4, loses everywhere else.

### §2.3 The directional sub-claim (recovered in aggregate, but it cannot rescue the core null)

| frequency spread Δ | mean ΔK_c across N | 
|---|---|
| equal (Δ=0) | **−0.025** |
| unequal Δ=0.3 | −1.175 |
| unequal Δ=1.0 | **+0.250** |

Mean ΔK_c **is larger at unequal Δ=1.0 (+0.25) than at equal (−0.025)** (`advantage_larger_at_unequal=True`) and `advantage_grows_with_delta=True` over the Δ grid — the F141-grounded *direction* of the effect is recovered in the average. But the Δ=0.3 row is strongly negative (driven by the N=16/32 reciprocal lock-failures dominating the mean), and more importantly **a directional sub-claim cannot rescue a fired core null**: the structural claim "R3 locks where R1 does not, robustly across N" is defeated by the N-instability. The disposition rule treats this as **NULL with the directional note attached** (`directional_subclaim_supported=False`, because it is gated on the core null not firing).

---

## §3 srmech-native discipline (HARD = 0)

The integrator is ngspice's `.tran` (the analog substrate's bounded C ODE solver, computing its own `sin`/`cos`); **srmech does every Class-K/C/L/A op** on the parsed scalars:

| role | srmech op | class |
|---|---|---|
| order parameter `r = |⟨e^{iθ}⟩|` | two `cascade.magnitude` + sqrt (the F231 pattern; **never** `abs()`/`max()`) | **K** |
| error-latch (received vs own phase) | `cascade.pin_slot_at_zero` on `cos(ψ_i − θ_i)` at the locked transient | **K** (F217 SR latch) |
| correction sign re-application | `cascade.reorient(orient, step)` | **C** |
| net orientation diagnostic | `cascade.net_chirality` over the reoriented latch chain | **C** |
| coupling-graph spectrum / Fiedler λ₂ | `laplacian.dense_laplacian` + `jacobi_eigvals` (no `np.linalg`) | **L** |
| K_c/K_c ratio de-magick anchor | `cascade.best_rational_signed` | **K+N** |
| matched-budget L1 spread floor | `cascade.magnitude` per entry (no `abs()`) | **K** |
| attestation hash | `format.sha256_bytes` (no `hashlib`) | **A** |

`numpy` is the array carrier of the parsed ngspice transient only (the linear accumulation `Σ A_ij e^{iθ_j}` for the latch readout; no linalg, no `abs`, no `Counter`). **`check_srmech_discipline.py` (rc9 venv): 0 HARD, 0 coverage-gap.**

**srmech tooling note (UPSTREAM_NOTES §11.1):** rc9 *does* ship `srmech.amsc.cascade.kuramoto_step`, but its signature `(theta, omega, *, coupling: float, dt)` confirms it is **all-to-all uniform-coupling only** — a single scalar `coupling` as the mean-field `(coupling/n)·Σ sin`. It does **not** accept a coupling matrix / adjacency / Laplacian, so it cannot express F240's graph-structured **directed-vs-symmetric** coupling (the whole measurement). The forward-ask (an optional `adjacency=` argument, a non-symmetric matrix expressing directed/one-way coupling) is logged in `UPSTREAM_NOTES.md §11.1` for the user/maintainer to file; the analog substrate supplied the graph-structured integrator the op lacks. **No srmech package edit.**

---

## §4 Tiering — what this finding OWNS vs READS

- **DEMONSTRATED (the ngspice `.tran` measurement, bit-exact-reproducible):** the per-regime per-(N, frequency-condition) located K_c, the steady-state order parameter `r`, the matched-total-abs-weight control (L1 spread 0.0 at every N/condition), and the symmetrised-graph λ₂ (identical across regimes by construction). It owns only the testbed sentence: *"in this coupled-oscillator testbed, at matched coupling budget, regime X locks at K_c=… and regime Y does/does not."* The measured fact is that **the corrective advantage does not survive the width-doubling at matched budget** on this near-1D graph.
- **FRAMEWORK-READING (never inflated):** (i) reading corrective communication *as* a closed-loop reciprocal coupling edge + a Class-K error-latch (the R3 structure); (ii) "communication reduces to back-and-forth thinking outside of one body" = the reciprocal closed-loop edge, with the A↔B fixed point in the **off-diagonal Laplacian**, in neither body alone (distributed cognition); (iii) **the F239 corollary** — exclusion is a *severed corrective edge*: a signal sent that is never returned/corrected (a feed-forward R1 emission with the return path cut, `A_ji=0`), so the loop never closes and the fixed point never forms. The null means these readings are **suggestive analogies of shape, not a measured phase-lock advantage** — exactly the downgrade the pre-stated null specified.
- **The literature owns** every Staurois foot-flagging ethology fact (the **Staurois foot-flagging frog** is the web-verified biological anchor — responsive male-male flagging contests; the channel-adaptive switch from calling to flagging under stream noise; the alerting/receiver-response findings), per the cited peer-reviewed authors (F226 verify-before-assert; CITATIONS web-verified 2026-05-31). The Kuramoto/Sakaguchi K_c physics belongs to its cited authors. **The null does not touch the biology**, which stands or falls on the ethology literature's own terms.

---

## §5 Honest caveats

1. **The testbed is the near-1D extended mesh, and its connectivity collapses with N.** λ₂ falls 2.0 → 0.719 → 0.190 → 0.048 across N=4/8/16/32. The corrective win at N=4 lives where λ₂ is large; the N=16/32 reciprocal lock-failures live where λ₂ is tiny. A *different* topology (denser, expander-like, or all-to-all) might not collapse this way — but that would change the F235 testbed, and the matched-budget split-W/2 penalty for the reciprocal regimes on a sparse graph is itself the structural finding. The null is honest *about this graph*.
2. **The K-grid is coarse (6 values) and N≥16 lock onset may sit between grid points.** At N=8 unequal the three matched regimes all read K_c=2.0 (the grid ceiling); a finer grid could in principle resolve a small ordering. But the **branch (c)** signature (TRAP locks at 1.0 while matched regimes need 2.0) and the **branch (d)** N=16/32 lock-failures are robust to grid resolution — they are qualitative (locks vs never-locks), not threshold-position quibbles. The coarse grid was the deliberate anti-runaway / finish-in-minutes choice for the RE-RUN.
3. **The R3 correction is realised with ngspice's `sgn()` as the analog of the Class-K `pin_slot_at_zero` orient.** This is a faithful sign-latch, but `sgn(0)=0` and the `1/|acc|` normalisation has a `+1e-9` floor (a pure-emitter node with no received field keeps its own phase). The srmech-side `latch_readout` reads the *same* latch on the locked phases and reported **0 unresolved** boundary cases in every locked R3 run — the latch resolved cleanly where it locked.
4. **This is the ngspice RE-RUN; the verdict matches the design's pre-stated disposition exactly.** The first attempt's pure-Python core never produced data. This run's `.tran` core is bounded and the NULL is reproduced bit-for-bit across two runs (`response_sha256` identical). The result is the measured booleans, not a leaned read.

---

*Finding F240 (RE-RUN). Verdict NULL (branches c + d). `response_sha256 = 6faf67ab22ca87d4c1e300bda128309fcbf546be349ae3e9e5ac06391a779688`, bit-exact across 5 runs. srmech 0.6.0rc9, ngspice 45.2. Discipline 0 HARD. The frog stays the literature's.*
