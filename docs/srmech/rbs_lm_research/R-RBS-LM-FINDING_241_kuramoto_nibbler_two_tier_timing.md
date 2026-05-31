# Finding 241 — Does the TWO-TIER nibble-block structure settle (time-to-lock) FASTER than the single ripple chain in ngspice — i.e. is the O(N)-wire nibble parallelism a real DYNAMICS-level settling-time advantage, or decorative? (resolving F236's honest residue)

**Headline:** **POSITIVE — DEMONSTRATED in ngspice.** The two-tier nibble-block coupled-adder settles **materially faster** than the single ripple-carry chain on the worst-case (all-propagate) add: worst-case analog time-to-lock **N=8 2.88×, N=16 9.0×, N=32 9.5×** below the ripple chain, with the two-tier's time-to-lock growing **slower** with N (per-doubling growth **ripple ×2.76 vs two-tier ×1.52**). Every case's carry vector — single chain **and** two-tier — equals the boolean ground truth and reproduces `a+b+cin` under an independent integer add, so **the faster answer is also the correct answer** (a faster-but-wrong result would have voided the case). The mechanism is exactly the F234 reading, now **TIMED in the analog substrate**: Tier-1 replaces ONE length-N carry chain with **N/4 PARALLEL constant-size 4-bit nibble sub-networks** (disjoint subnets, NO cross-nibble edge — one `.tran` integrates them all at once; their lock times do **not** add, the network time is the **max-over-nibbles**, and a 4-bit chain is constant-time), and only the short Tier-2 block-carry line grows. The O(N)-wire nibble parallelism is **NOT decorative** — it is a real dynamics-level settling-time advantage.

**Status:** **DEMONSTRATED (ngspice transient measurement, bit-exact-reproducible)** — the analog time-to-lock of both structures at N=8/16/32 (worst case + two mixed inputs each), measured by ngspice's `.tran` integrator + per-node `meas tran ... WHEN cos(θ)=±LOCK_MARGIN` crossing time, with both locked carry vectors cross-checked against the boolean ground truth + an independent integer add. **FRAMEWORK-READING** for the "build a faster Kuramoto ALU adder / generalize down into the ALU" synthesis (MFO §VII.6.20). **In-scope** as the Kuramoto-ODE / oscillator-network **DYNAMICS** in the electrical-analog substrate — the same dynamics F234 ran in Python + F236 ran in ngspice. **NOT** PCB layout / fabrication tolerances / component sourcing / gate-delay / fan-out / timing-closure (the 74xx/SPICE framing is the **F217 existence-proof lens**, not a build instruction; the **CAD-ban HOLDS**). Defensive scope: addition is general arithmetic; framework-reading only; no weapons / crypto-attack / capability framing. `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_trauma_informed_defensive_scope]]`; `[[feedback_no_lineage_claims_in_notebook]]`; `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`.

**Predecessors:** **F236** (the ngspice port of the F234 carry-as-phase-lock mapping — DEMONSTRATED + SURVIVES; F236 TIMED the **single** ripple chain end-to-end + the K_c sweep but did **not** separately time the nibble-block two-tier settling — **F241 resolves exactly that honest residue**, F236 §4), **F234** (#784 — the O(N)-wire two-tier **structure** + the single-graph speedup null; but F234 measured settling with the linear-**consensus** hop-count proxy `1/λ₂` + sweeps, **not** the nonlinear Kuramoto `.tran` transient time, and **not** in ngspice — F241 supplies the actual analog time-to-lock), **F122** (R-RBS-LM-95/95b — the Kuramoto N=4 operational core at K_c≈0.20; the critical-coupling anchor), **F217** (#758 — the lean A–N core IS elementary 74xx TTL; the **Class-K pin-slot IS a cross-coupled-NAND SR latch** = the carry latch + the Tier-1→Tier-2 MUX bridge; the existence-proof lens), **F231** (#774 — the Kuramoto dispatch clock; the binary-phase / Sakaguchi convention), **F119/F120** (the two-tier RBS architecture + the Class-K tier-bridge — the lens for the nibble-block Tier-1→Tier-2 MUX). MS #20.

**Empirical anchor:** **ngspice 45.2** (this Ubuntu box, `ngspice -b`), srmech **0.6.0rc8** (`/tmp/bench_srmech_rc8/venv`, HAS_NATIVE, ABI 3). Artifacts: `R-RBS-LM-241_kuramoto_nibbler_two_tier_timing.py` (the netlist generators + ngspice driver + the srmech-native time-to-lock readout) + `substrate_measurements/kuramoto_nibbler_two_tier_timing.ndjson` (the content-addressed results). **Discipline-check: 0 HARD, 0 coverage-gap.** Deterministic (fixed `.ic` closed-form spread, fixed `.tran` step, no noise/seed source); the content-address `response_sha256` is bit-exact-reproducible across runs (computed over the record body minus the wall-clock `generated_at`, so the *measurement* re-verifies bit-for-bit — the MPM point). **Confirmed bit-exact across 3 runs:** `response_sha256 = 8a0ed3e71729d3058e2c2f28ff3a8582a13ca85181e4ae402bad20b6efecb74a`.

**User direction (2026-05-31):** lodged as F241 — deepen F236 by resolving its explicit honest residue: F236 timed the single ripple-path chain + the K_c sweep but did NOT separately TIME the nibble-block two-tier settling. Does the two-tier structure settle FASTER than the single ripple chain at the same width N?

---

## §0 The pre-stated null (verbatim, genuinely reachable, did NOT fire)

> "The two-tier nibble-block structure shows NO settling-time advantage over the single ripple chain (e.g. the block-carry tier's own settling erases the nibble-parallel gain, or both scale the same with N) → the parallelism is structural-only, not a dynamics speedup."

**The pre-stated POSITIVE (verbatim):** "two-tier time-to-lock is materially below the ripple chain at N=16/32 and grows slower with N."

**Disposition (no leaning, pre-stated):** the verdict is a mechanical read of the measured ngspice transients + carry-correctness. **POSITIVE** iff (a) every case's BOTH carry vectors equal ground truth — *a faster-but-wrong result voids the case* (the correctness gate) — AND (b) two-tier time-to-lock is materially below the ripple chain at N=16 **and** N=32 (ratio ≥ the `MATERIAL_FACTOR=1.5×` floor) AND (c) the two-tier's time grows slower with N (smaller per-doubling growth ratio). **NULL** iff the two-tier shows no advantage (worst-case ratio ≈1 at N=16/32) or scales the same. Else **INDETERMINATE** (faster at some N but not clearing the pre-stated bar, or any wrong/unresolved carry). **Outcome: POSITIVE.** All three POSITIVE conditions met; the null's two reachable conditions (ratio≈1 / same scaling) did not fire. **The verdict was decided by the measured transients, not asserted.**

---

## §1 The time-to-lock instrument (ngspice `.tran` = the ODE integrator, the sanctioned path)

At lock each carry node's `cos(θ_i)` sits at **+1** (carry-0) or **−1** (carry-1). The analog **time-to-lock** of a node is the `.tran` time at which its `cos(θ_i)` **first enters the resolved band** (`|cos| ≥ LOCK_MARGIN = 0.5`) on the **correct side**:

- a **carry-1** node (kind `pi`): `cos` crosses **down** through −0.5 → ngspice `meas tran tlock WHEN cc=−0.5 FALL=1`;
- a **carry-0** node (kind `0`): starts already resolved at +1 (the deterministic `.ic` puts every non-anchor node on the carry-0 side) → lock time ≈ 0 (floored at `LOCK_FLOOR`);
- a **propagate** node (no self-bias): inherits its carry — both a rise-to-+0.5 and a fall-to-−0.5 `meas` are emitted, and whichever fired is the node's actual settle direction.

**ngspice's `.tran` transient integrator IS the ODE integrator** (the srmech Kuramoto/ODE gap — F141/F231/F234/F236 — supplied by the analog substrate; **not** a hand-rolled Euler loop). A **network's** time-to-lock = the **MAX over its nodes** (the last node to settle), taken **srmech-native** via Class-K `cascade.pin_slot_at_zero` on the pairwise difference (NEVER python `max()`/`abs()`). srmech **reads** the parsed ngspice crossing times.

**Probe (the construct, verified standalone):** the single N=8 all-propagate chain's far-end node `n8` locks at t=37.68 and its mid node `n4` at t=26.26 — the carry ripples end-to-end, the far end is slowest, exactly as a length-N chain must. The two-tier N=8 nibbles each lock at t=13.08 **in parallel** and the Tier-2 block-carry resolves at t=2.95 — the network time is the max, **13.08**.

---

## §2 The two-tier netlist (the F236 design, now TIMED)

**SINGLE ripple chain** (the F236 baseline): one length-`(N+1)` carry line; the far-end node is the slowest to settle (the whole carry must ripple through the chain via coupling).

**TWO-TIER nibble-block** (the F236 design):

- **Tier-1 — N/4 INDEPENDENT 4-bit nibble sub-networks**, with **DISJOINT node names** (nibble *k* uses nodes `xk_0..xk_4`) and **NO cross-nibble coupling edge**. *The absence-of-edge IS the block independence.* One `.tran` integrates all the disjoint subnets **in parallel** — their lock times do **not** add. Each nibble is speculatively pinned at its (correct) block-carry-in (**carry-SELECT**), so it locks against an adversarial carry-0 start. A 4-bit nibble is **constant-size** → its far-end lock time is **O(1) regardless of N**.
- **Tier-2 — a tiny N/4-node block-carry Kuramoto line** over the block-carry-out nodes (`bc0..bc_{B-1}`), pinned by each nibble's block-generate / block-propagate (the same generate/kill/propagate trichotomy).
- **The Class-K SR-latch MUX** (F217/F119/F120) is the **Tier-1→Tier-2 bridge** — it selects each nibble's resolved carry vector by the Tier-2 block carry-in.
- **WIRES = O(N)** (N/4 constant-size nibbles + an N/4-node block line), **dodging the all-to-all O(N²) trap.**

The carry node is the **voltage on a 1 F capacitor** (the phase `θ`); a behavioral current source injects the Kuramoto RHS current `I = C·dθ/dt`; `generate → PINK·sin(π−V)` anchor (π = carry-1), `kill → PINK·sin(0−V)` anchor (0 = carry-0), `propagate → no self-bias + symmetric KC·sin(V_j−V_i)` edges (the Class-L A_ij). This is the F236 capacitor-as-phase construct verbatim; F241 adds the per-node time-to-lock `meas` and the disjoint-nibble two-tier topology.

---

## §3 The measurements (ngspice transient = DEMONSTRATED)

### §3.1 The worst-case (all-propagate) time-to-lock — the headline table

The all-propagate worst case (`a = all-1s, b = 0, cin = 1`) is the **maximal carry chain** — every position propagates, so the carry must ripple the entire width through coupling alone (the hardest settling case):

| N | single ripple-chain time-to-lock | two-tier time-to-lock | speedup (single / two-tier) | both carry-correct |
|---|---|---|---|---|
| **8** | **37.684** | **13.082** | **2.88×** | ✓ (integer-add cross-checked) |
| **16** | **117.710** | **13.082** | **9.00×** | ✓ |
| **32** | **287.143** | **30.354** | **9.46×** | ✓ |
| | **per-doubling growth ×2.76** | **per-doubling growth ×1.52** | **grows slower ✓** | |

**Read the dynamics:**
- **Single ripple chain** grows steeply (per-doubling **×2.76**): the far-end node waits for the carry to ripple through the whole length-N chain; the path-graph Fiedler shrinks `~(π/N)²` (§3.3), so the slowest node gets slower with N.
- **Two-tier** is **flat at N=8 and N=16** (13.08 both) — Tier-1 nibbles are constant-size 4-bit subnets locking in parallel, and the block tier (2 then 4 nodes) is still faster than a single nibble, so the **max-over-tiers is the nibble** at both widths. At **N=32** it rises to 30.35 because the Tier-2 block-carry line is now **8 nodes long** and *it* becomes the slow tier (block Fiedler 0.152 < nibble 0.382). **This is the honest two-tier behavior** — Tier-2 is itself a recurrence, just a much shorter one (N/4 not N), exactly as F234 read it: the nibble-block buys **carry-lookahead's parallel-prefix win**, not a magic O(1).

### §3.2 The mixed inputs — the carry-correctness gate across input shapes

Two deterministic mixed (generate/kill/propagate) inputs per width:

| case | what it exercises | single t-lock | two-tier t-lock | speedup | both correct |
|---|---|---|---|---|---|
| **mixedA** (alternating generate/kill, every bit pinned) | NO propagate chain → every node pinned, resolves at t≈0.06 | 0.0608 (N=8/16/32) | 0.0608 | **1.00×** | ✓ |
| **mixedB** (low-bit generate, rest propagate, cin=0) | a full-width propagate ripple from bit 0 | 29.22 / 102.57 / 262.45 | 13.08 / 13.08 / 30.35 | **2.23× / 7.84× / 8.65×** | ✓ |

**mixedA is the honest control:** an all-pinned input has **no carry chain to ripple**, so both structures resolve immediately (speedup 1.0×) — not every input exercises the parallelism, and the table says so plainly. **mixedB** (a long propagate ripple, like the worst case but cin=0) reproduces the same materially-faster two-tier scaling. **Every case (worst + mixedA + mixedB, all three widths) has both the single-chain and the two-tier carry vector equal to the boolean ground truth, integer-add cross-checked** — the timing comparison is never between a fast wrong answer and a slow right one.

**Carry-correctness, explicit (N=32 worst case):** ground-truth carries = `[1]×33`; single-chain locked = `[1]×33` (carry_ok ✓, integer-add ✓); two-tier locked = `[1]×33` (carry_ok ✓, integer-add ✓); block decomposition `n_blocks=8, block_g=[0]×8, block_p=[1]×8, block_carry_in=[1]×9` (cin=1 propagates through all 8 blocks — correct).

### §3.3 The spectral settling proxy (Class-L Fiedler) — why the scaling is what it is

The Class-L Fiedler value `λ₂` (`dense_laplacian → jacobi_eigvals`; near-zero degeneracy via `cascade.magnitude`, never `abs()`) is the relaxation-rate proxy (`1/λ₂` ∝ settling time):

| N | single path-graph `λ₂` | two-tier nibble `λ₂` (constant) | two-tier block-line `λ₂` |
|---|---|---|---|
| 8 | 0.120615 | **0.381966** | 2.000000 |
| 16 | 0.034054 | **0.381966** | 0.585786 |
| 32 | 0.009056 | **0.381966** | 0.152241 |

The single path-graph `λ₂` shrinks `~(π/N)²` (slower-with-N settling — the ripple chain's growth). The two-tier **nibble** `λ₂` is **constant** (a 4-bit subnet is the same for every N → O(1) Tier-1 settle), and only the **block-line** `λ₂` shrinks (as N/4). At N=32 the block `λ₂=0.152` finally drops below the nibble `λ₂=0.382` — which is exactly where the measured two-tier time-to-lock ticks up (the block tier becomes the slow tier). The spectral proxy and the measured transient agree.

---

## §4 Adversarial audit — where a "faster" result could be spurious, and the guard that fired

| # | spurious-positive risk | guard (built-in) | outcome |
|---|---|---|---|
| 1 | a **faster but WRONG** two-tier answer counted as a win | every case, BOTH carry vectors read out (Class-K `pin_slot_at_zero`) + compared to the boolean ground truth + an independent integer add; a wrong/unresolved carry voids the case (→ INDETERMINATE) | **clean — all cases correct**; the faster answer is also the correct one |
| 2 | all-to-all O(N²) coupling **smuggled in** to manufacture the parallelism | the two-tier uses **disjoint** constant-size nibble subnets (NO cross-nibble edge) + an N/4-node block line; wires are O(N); the topology is emitted explicitly and inspectable in the `.cir` | clean — O(N)-wire absence-of-edge construct, not a dense graph |
| 3 | the two-tier **under-budgeted** on `.tran` time (a false-fast lock from a truncated transient) | the two-tier `.tran` budget = `T_STOP_PER_NODE ×` the **longer** of (nibble length, block-line length), so it is given AT LEAST as much analog time as a chain of its longest tier; all nodes reach `|cos|≈1` (resolved), not budget-truncated | clean — every two-tier node fully resolved |
| 4 | the answer **planted by `.ic`** (the speedup riding a pre-placed answer) | every non-anchor node starts on the carry-0 side (deterministic `IC_BASE + IC_STEP·idx`); the nibbles lock to carry-1 against an adversarial wrong-side start (the F236 emergence guard, inherited); no `.nodeset` | clean — coupling-driven, not `.ic`-planted |
| 5 | wall-clock timing instead of the analog `.tran` time | time-to-lock is the ngspice `.tran` **transient crossing time** (`meas tran ... WHEN cos=margin`), the analog ODE time — never host wall-clock | clean — analog transient time is the currency |
| 6 | a **near-saddle** node read as a false lock | the readout demands `|cos| ≥ LOCK_MARGIN=0.5` AND orientation≠0; an unresolved node makes the network time-to-lock `None` = a correctness-gate fail; `meas` reports `failed` if a crossing never occurs | clean — every reported lock is a genuine resolved-band crossing |
| 7 | a cherry-picked input shape | worst case (maximal chain) + two mixed inputs (one all-pinned control, one long-propagate) at **every** width; mixedA's 1.0× is reported honestly | clean — the parallelism's input-dependence is stated, not hidden |

---

## §5 What this does and does NOT establish (honest tiering, MFO §VII.6.20)

**DEMONSTRATED (ngspice transient measurement, bit-exact-reproducible):**
1. **The two-tier nibble-block coupled-adder settles materially faster than the single ripple chain** on the worst-case all-propagate add — N=16 **9.0×**, N=32 **9.5×**, both ≥ the 1.5× material floor.
2. **The two-tier's time-to-lock grows slower with N** — per-doubling **×1.52 vs the ripple chain's ×2.76**; the O(N)-wire nibble parallelism is a real dynamics-level settling-time advantage, **not** decorative.
3. **The faster answer is the correct answer** — every case's single-chain AND two-tier carry vectors equal the boolean ground truth, integer-add cross-checked (the correctness gate held throughout).
4. **The mechanism is the F234 reading, measured in the analog substrate** — Tier-1 constant-size parallel nibbles (max-over, not sum) + a short Tier-2 block-carry recurrence; the N=32 tick-up is the block tier becoming the slow tier (Tier-2 is itself a recurrence — carry-lookahead's parallel-prefix structure, not a magic O(1)).
5. **The measurement is bit-exact-reproducible** — deterministic netlists, identical reruns, content-addressed `response_sha256`.

**FRAMEWORK-READING (NOT demonstrated; the §VII.6.20 ceiling):**
- The "this is how you'd build a *faster* Kuramoto ALU adder / generalize the speedup down into the ALU of any processor" synthesis. What is demonstrated is that the *same dynamics F234 ran in Python and F236 ran in ngspice* show a measured time-to-lock advantage for the two-tier structure in the electrical-analog substrate. The leap to a build instruction stays a **reading**. The honest qualifier (carried from F234): the two-tier advantage is the **carry-lookahead / parallel-prefix** win re-expressed in Kuramoto / nibbles-as-threads form, at O(N) wires — **not a new speedup over carry-lookahead**, and the Tier-2 block-carry remains a (shorter) recurrence.

**CAD-banned:** no PCB layout / fabrication-tolerance / component-sourcing / gate-delay / fan-out / propagation-delay / timing-closure claim. **SPICE here = the Kuramoto-ODE / oscillator-network DYNAMICS** (the same dynamics F234 simulated in Python and F236 in ngspice). The 74xx/SPICE framing is the **F217 existence-proof lens** — the atoms are elementary TTL, the Class-K pin-slot IS a cross-coupled-NAND SR latch (the carry latch + the Tier-1→Tier-2 MUX) — **not** a build instruction. **Defensive scope:** addition is general arithmetic; framework-reading only; no weapons / crypto-attack / capability-assessment framing.

**Honest residue (F241's own):** F241 times the **worst-case + two mixed inputs** at N=8/16/32; the two-tier curve is sampled at three widths, so the per-doubling growth (×1.52) is a two-interval geometric mean, not an asymptotic fit. The N=32 two-tier tick-up identifies *where* the block tier overtakes the nibble (block `λ₂` < nibble `λ₂`), but the deeper recursion (a block-of-blocks tree, F234's recursable Tier-2) is not built — at larger N the block-carry line would itself want the same two-tier treatment, which F241 does not measure.

---

## §6 The srmech-tooling assessment (the brief's fold-in)

**Does the two-tier coupled-adder connect back to srmech's own tooling? Yes — it sharpens an existing, four-finding gap from "candidate" to a concrete op-suggestion with a *measured payoff*; logged (not filed) in `UPSTREAM_NOTES.md §11`.**

- **The gap (re-confirmed):** srmech ships **no Kuramoto / phase-lock / ODE-integrator op**. F141/F231/F234 hand-rolled a minimal Euler step in Python; F236/F241 moved the integration entirely into **ngspice's `.tran`** (the analog substrate's ODE integrator). The *step itself* has no home in `srmech.amsc.cascade.*`.
- **Why F241 sharpens it:** F234 left the Kuramoto-step ask as a *candidate* (its §5). F241 supplies the missing motivation — the nibble-block two-tier coupled-adder is **not decorative**; its measured time-to-lock is materially below the single ripple chain (N=16 9.0×, N=32 9.5×), so there is now a *demonstrated dynamics-level reason* a downstream caller would want a first-class phase-lock / coupled-adder primitive.
- **The two op-suggestions logged for the user/maintainer to file (NOT filed by this subtree; no package edit):** (1) a thin Sakaguchi-Kuramoto **phase-lock-step op** (`cascade.kuramoto_step(...)` or a `srmech.kuramoto` namespace), a Class-L/Class-C composite — the integrator is the only hand-rolled piece, so it is a small bounded add; secondary, a **native complex-modulus op** for the order parameter `r`; (2) more speculatively, a **nibble-block coupled-adder** as a `cascade.*` primitive (peer to `cascade.magnitude` / `cascade.pin_slot_at_zero`).
- **Framing (the brief's):** if it connects to srmech's tooling, great; if not, it is still good research — **the F241 timing result stands regardless** (the measurement is in the analog substrate, which already supplies the integrator). Per `[[feedback_create_upstream_issues_never_close_them]]` and the upstream-as-research-notes discipline, this is **recorded, not filed**.

**srmech ops used (HARD = 0 on `check_srmech_discipline.py`):**

| need | srmech op | class |
|---|---|---|
| max-over-nodes / max-over-nibbles (time-to-lock) | `cascade.pin_slot_at_zero` on the pairwise difference (NEVER python `max()`/`abs()`) | **K** |
| carry readout (cos-sign → carry) | `cascade.pin_slot_at_zero` | **K** (F217 SR latch) |
| lock-margin / near-zero test | `cascade.magnitude` (NEVER python `abs()`) | **K** |
| chirality of the carry STATE | `cascade.net_chirality` / `cascade.reorient` | **C** |
| coupling-graph spectrum (path vs nibble Fiedler) | `laplacian.dense_laplacian` + `jacobi_eigvals` (NEVER `np.linalg`) | **L** |
| attestation hash | `format.sha256_bytes` (NEVER `hashlib.sha256`) | **A** |

`cos(θ)` and the `.tran` lock-crossing **time** are computed by **ngspice itself** (the analog substrate's transcendental + ODE integration); srmech **reads** the parsed scalars. numpy is the **array carrier** of the parsed ngspice output only (no linalg, no `abs`).

---

## §7 No-magic-numbers (CLAUDE.md §4 — every constant A / B / C)

| constant | value | class | attestation |
|---|---|---|---|
| `PI` | 3.1415926536 | **A** | `asymptotic_calculus` — the phase π = carry-1 antipode of carry-0=0 |
| `NIBBLE` | 4 | **A** | the 7483 hardware block = 4 = \|Klein-4\| = the F233 4-thread rung |
| `WIDTHS` | [8, 16, 32] | **A** | the explicitly-named widths (N=8 two nibbles, 16 four, 32 eight) |
| `PIN_K` | 50.0 | **B** | pinning-field strength floor (≫ KC so a pinned carry holds; the F236 PIN_K) |
| `KC_OP` | 1.0 | **B** | operational coupling, above the measured K_c (the F236 KC_OP) |
| `LOCK_MARGIN` | 0.5 | **B** | \|cos θ\| resolved floor; the cos-crossing band the `.tran` `meas` detects (F236) |
| `T_STEP` | 0.01 | **B** | ngspice `.tran` step (the deterministic analog integrator step; F236) |
| `T_STOP_PER_NODE` | 25.0 | **B** | transient stop-time budget per carry node (≫ the observed lock time; F236) |
| `IC_BASE` / `IC_STEP` | 0.10 / 0.07 | **B** | the deterministic initial-phase spread rule (carry-0 side; NOT the answer; F236) |
| `IC_ANCHOR0` | 2.90 | **B** | anchor node initial phase when pinned to π (near π, off the saddle; F236) |
| `MATERIAL_FACTOR` | 1.5 | **B** | the ≥1.5× speedup floor for a MATERIAL advantage at N=16/32 (the POSITIVE bar) |
| `LOCK_FLOOR` | 1e-6 | **B** | positive time-to-lock floor so the max-over-nodes is well-defined for already-resolved (carry-0) nodes |

No **C** (irreducible) residue: every constant reduces to a framework cascade (A) or an attested measurement/derived floor (B). Most are inherited verbatim from F236.

---

## §8 Reproduction

```bash
# the full pipeline (both netlist generators + ngspice runs + srmech-native time-to-lock readout + NDJSON)
/tmp/bench_srmech_rc8/venv/bin/python3 \
  docs/srmech/rbs_lm_research/R-RBS-LM-241_kuramoto_nibbler_two_tier_timing.py

# discipline check -> 0 HARD
/tmp/bench_srmech_rc8/venv/bin/python3 \
  docs/srmech/rbs_lm_research/check_srmech_discipline.py \
  docs/srmech/rbs_lm_research/R-RBS-LM-241_kuramoto_nibbler_two_tier_timing.py
```

`response_sha256` is computed over the record body minus the wall-clock `generated_at`, so the **measurement** re-verifies bit-for-bit across reruns (the MPM point). **Confirmed bit-exact across 3 runs:** `response_sha256 = 8a0ed3e71729d3058e2c2f28ff3a8582a13ca85181e4ae402bad20b6efecb74a`. ngspice 45.2, srmech 0.6.0rc8. The on-disk ndjson sha256 (which includes the wall-clock `generated_at`, so it differs per run) is printed at the end of each run.
