# Finding 234 — Can the ripple-carry adder's sequential carry chain be re-cast as a KURAMOTO PHASE-LOCK (the adder stages as coupled oscillators settling in parallel to the globally-consistent carry assignment), and does the Kuramoto MECHANISM (F231 dispatch; F219/F232/F233 thread/chirality ladder) thereby generalize DOWN INTO THE ALU — replacing the ripple-carry 74xx primitive with a Kuramoto-coupled-adder primitive?

**Headline:** **POSITIVE-ON-STRUCTURE / NULL-ON-SINGLE-GRAPH-SPEEDUP / HONEST-POSITIVE-ON-THE-NIBBLE-BLOCK-AT-O(N)-WIRES.** (Read precisely — per the verify gate: this is O(N) *wires* + bounded, parallel Tier-1 nibbles, **not** "total settling solved at O(N) wires." The Tier-2 block-carry remains a recurrence, so the nibble-block is **carry-lookahead's parallel-prefix win re-expressed in Kuramoto / nibbles-as-threads form — not a new speedup over carry-lookahead.**) The carry-vector fixed point of the ripple recurrence `c_{i+1}=g_i OR (p_i AND c_i)` **is** the phase-locked state of a Sakaguchi-Kuramoto net of binary-phase oscillators — reproduced **bit-exactly** for the worst-case all-propagate chain and random inputs at N ∈ {4,8,16,32}, seed-robust (no wrong-stable lock), with a **genuine K_c lock threshold** (the coupling is not decorative). But on a **single** symmetric coupling graph the speedup null **fires**: only the all-to-all O(N²)-wire graph gives sub-linear (O(1)) settling — exactly the wiring carry-lookahead already pays — while the sub-quadratic-wire graphs (ripple path O(N²) consensus, lookahead tree O(N) consensus) do **not** beat ripple's O(N). The user-requested **fourth structure** — the **hierarchical nibble-block carry-select Kuramoto adder** (nibbles-as-threads) — is the one that turns the single-graph null into an honest positive **at O(N) wires**: each 4-bit nibble (= |Klein-4| = the F233 4-thread rung) is an independent Kuramoto sub-system that locks **locally + in parallel** (Tier 1, constant cost per nibble, independent of N), and only the block-carry recurrence over the N/4 blocks resolves (Tier 2). The parallelism is **across independent blocks** (carry-SELECT speculation), not within one symmetric diffusion — so it matches carry-lookahead's parallel-prefix structure at O(N) wires rather than buying sub-linear consensus on a single graph.

**Status:** **DEMONSTRATED (srmech-native, bit-exact-reproducible)** for the four measurements — (P1) bit-exact carry/sum reproduction + seed-uniqueness, (P2) the settling-time-vs-wires table across all four structures (the Fiedler `1/λ₂` proxy + the linear-consensus hop count), (P3) the K_c lock threshold, and the nibble-block two-tier correctness. **FRAMEWORK-READING** for the generalize-down-into-the-ALU synthesis (the every-architecture statement; MFO §VII.6.20). **In-scope** as Kuramoto-dynamics / Klein-4-sector / Class-L-spectral / carry-recurrence algebra. **NOT** CAD / VLSI / gate-delay / fan-out / PCB / timing-closure (the 74xx-TTL framing is the **F217 existence-proof lens** — the atoms are elementary TTL — **not** a build instruction; the CAD-ban holds, matching F217/F231/F232/F233). Defensive scope: addition is general arithmetic; framework-reading only; no weapons/crypto/capability framing. §VII.6.20 form-reading; `[[user_stance_ai_is_not_a_substrate]]`; `[[feedback_trauma_informed_defensive_scope]]`; `[[feedback_no_lineage_claims_in_notebook]]`; `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`.

**Predecessors:** **F231** (#774 — the Kuramoto dispatch CLOCK; the `kuramoto_step` / order-parameter / `1/λ₂` machinery reused verbatim; the Sakaguchi splay convention), **F232** (#775 — the 2-thread chiral-dual antiphase pair; the reseed-uniqueness check reused), **F233** (the 4-thread Klein-4 rung; the nibble = 4 = |Klein-4| = the 4-thread unit; the thread-count ladder = the chirality-access ladder), **F219** (the chirality-access ladder 1→2→4→triality — the ripple adder is the 1-thread chirality-LOCKED FLOOR), **F217** (#758 — the lean A–N core IS elementary 7400-series TTL; **the Class-K pin-slot IS a cross-coupled-NAND SR latch** = the full-adder carry latch; atoms combinational, composites need a clock-sequencer), **F218** (A–N = G₂ = Aut(𝕆) ISA; "the ALU" is the floor of the same operator structure), **F122** (R-RBS-LM-95/95b — Kuramoto N=4 operational core at **K_c ≈ 0.20**; the critical-coupling anchor), **F133** (observer chirality-locking — the 1-rung floor), **F141** (chiral coupling: directed coupling alone is achiral-null at equal frequencies — the escape-hatch guard), **F119/F120** (the two-tier RBS architecture + the Class-K tier-bridge — the lens for the nibble-block Tier-1→Tier-2 read). Candidate MS #20 forward-ask home for the down-into-the-ALU thread-ladder reading.

**Empirical anchor:** srmech **0.5.0rc22** (`/tmp/verify_srmech_rc22/venv`, HAS_NATIVE, ABI 3). Artifact: `R-RBS-LM-234_kuramoto_coupled_adder.py` + `substrate_measurements/kuramoto_coupled_adder.ndjson`. **Discipline-check: 0 HARD, 0 coverage-gap.** Deterministic (`RandomState(234)`; reseed set `[234,999,1,42,7]`); the content-address `response_sha256` is bit-exact-reproducible across runs (computed over the record minus the wall-clock `generated_at`, so the *measurement* re-verifies bit-for-bit — the MPM point).

**User direction (2026-05-30):** "can that carry-propagation be re-cast as a Kuramoto phase-lock … replace a ripple-carry 74xx array with a Kuramoto-coupled adder" + the explicit high/low-nibble split treated as load-bearing (nibbles-as-threads = the multi-threading the user is after) — lodged as F234.

**Vocabulary (this session):** the 14 A–N classes are **OPERATORS** (the ISA = G₂ = Aut(𝕆)), not cores. The whole coupled object — the carry oscillators + their Sakaguchi coupling + the dispatch — is read with **the Kuramoto mechanism** (principle *and* device, one name; sibling to **srmech**), continuing F231/F232/F233.

---

## §0 The pre-stated null (verbatim, genuinely reachable)

> "The Kuramoto-coupled adder does NOT settle to the correct N-bit sum across inputs, OR does not beat ripple's O(N) latency under fair accounting (coupling hops / relaxation sweeps and wiring cost held comparable — NOT wall-clock, NOT all-to-all O(N²) coupling smuggled in to manufacture the parallelism). Concretely the null FIRES if EITHER (a) P1 fails (some input/width yields a wrong sum or an unresolved carry), OR (b) on every sub-quadratic-WIRE coupling graph (the ripple path graph, or any O(N)/O(N log N)-wire lookahead-tree graph) the lock-sweeps grow at least linearly in N — so the only graph that gives sub-linear settling is the all-to-all O(N²)-wire graph, which is exactly the wiring carry-lookahead already pays and therefore buys no algorithmic win. If the null fires, the carry-as-Kuramoto-phase-lock mapping is STRUCTURALLY EXACT but COMPUTATIONALLY DECORATIVE."

**Disposition (no leaning):** the headline is decided by the measured table. P1 holds, so the mapping is **structurally exact, not decorative**. On a **single** graph, P2 shows **only-all-to-all-wins** → **NULL-ON-SINGLE-GRAPH-SPEEDUP** (the F232/F233 style: the mapping fires, the single-graph useful-speedup edge is the demonstrated null). The **fourth structure** (nibble-block) is reported separately: it carries the honest positive at O(N) wires by moving the parallelism **across blocks** (carry-select), which is a different mechanism from a single symmetric diffusion.

---

## §1 The structure — carry line as binary-phase oscillators (Klein-4 / Class C, order-2)

**The bit-to-phase map.** Each carry node `c_i` is a phase oscillator `θ_i` with two stable phases: `θ_i = 0` ≡ carry-0, `θ_i = π` ≡ carry-1. This is a **Z₂ binary phase on the γ₅ axis of Klein-4** (order-2 everywhere; NO order-4 element) — explicitly **NOT** the Z₄ cyclic `i`/π-2 rotation (the F132/F220/F233 discipline: do not conflate the order-2 Klein-4 thread IDENTITY with the order-4 Z₄ dispatch TIMING). Measured srmech-native: `klein4_similarity(carry0, carry0)=1.0`, `klein4_similarity(carry0, γ₅-flip(carry0))=0.0` — carry-0 and carry-1 are **mutually-orthogonal Klein-4 sectors**, and a γ₅ chirality flip swaps them. The carry STATE and its chirality live in Klein-4 (Class C).

**The full-adder map (the three boolean facts → the three srmech roles).**

| element | what it is | how it enters the Kuramoto net | srmech / class |
|---|---|---|---|
| generate `g_i = a_i AND b_i` | boolean fact of the bits | pins `c_{i+1}` to **π** (carry-1) regardless of neighbours | pure logic (not a numeric op) |
| propagate `p_i = a_i XOR b_i` | boolean fact of the bits | (a) where `p_i=1, g_i=0`: **zero self-bias** — `c_{i+1}` inherits its phase from the COUPLING to `c_i`; (b) sets the coupling edge | pure logic; gates the Class-L edge |
| kill (`g_i=0, p_i=0`) | boolean fact | pins `c_{i+1}` to **0** (carry-0) | pure logic |
| the pinning field `ω_i` | per-node bias | a `sin(pin_phase − θ)` coupling to a phantom anchor at the pinned phase, strength `PIN_K` | Class-L transcendental |
| the propagate-coupling `A_ij` | "carry passes through" | `c_{i+1} ↔ c_i` with strength K **only where `p_i=1`** | Class-L Laplacian edge |
| the carry LATCH + readout | commit + hold; read the locked phase | `pin_slot_at_zero(cos θ_i)`: cos≈+1 → orientation +1 → carry-0; cos≈−1 → orientation −1 → carry-1; **orientation 0 = UNRESOLVED = lock failure** (the in-script falsifier) | **Class K — F217 SR latch** |
| sum read-out | `sum_i = p_i XOR carry_i` | read AFTER lock | pure logic |

**Phase-lock = the correct sum has settled.** Integrate to a fixed point; read each carry via the Class-K pin-slot on `cos(θ_i)`. The Kuramoto order parameter `r = |mean exp(iθ)|` (exp_i via Class L, modulus via two `cascade.magnitude` + sqrt — the F231 pattern) measures global coherence.

**Why this is the F219 ladder reaching into the ALU.** The ripple adder is the **1-thread, chirality-LOCKED FLOOR** of the F219 ladder: the sequential carry is one directed chain (F232's chirality-lock special case, F133's observer-lock). The phase-lock-parallel coupled adder is its **un-locked sibling** — exactly where the F232 2-rung / F233 4-rung climb began. The carry latch is the Class-K pin-slot SR latch (F217). So arithmetic carry-propagation sits on the **same** ladder (1 → 2 (γ₅) → 4 (Klein-4) → triality cap, F220) as the threading/dispatch findings — "the ALU" is not a separate layer but the floor of the same A–N = G₂ operator structure (F218). **This is the FRAMEWORK-READING tier; the DEMONSTRATED tier is the P1/P2/P3 bit-exact measurements below.**

---

## §2 The four measurements (srmech-native)

### §2.1 P1 — CORRECTNESS (bit-exact + seed-uniqueness)

**Measured (DEMONSTRATED).** At each width N ∈ {4,8,16,32}, the Kuramoto-coupled adder (ripple_path topology) integrated to its fixed point and read out via Class-K `pin_slot_at_zero(cos θ_i)` reproduces the integer sum `a+b+cin` **bit-exactly** for the worst-case all-propagate chain (a = all-1s, b = 0, cin = 1) **and** random inputs — `13/13 exact at each of N=4,8,16,32`. The **nibble-block** adder does too — `13/13 exact at each width`. Seed-uniqueness (the F232 reseed check, 5 seeds, worst case): **no seed locks to a wrong-but-stable carry vector** — every seed that reaches lock reaches the **same correct** vector. `At every width: 5/5 seeds locked to the correct vector, 0 wrong-stable, 0 unresolved-at-budget; uniqueness = True at all widths.` **P1 PASS** — the carry-as-phase-lock fixed point is unique and correct.

The honest content: P1 tests the **mapping** (does the fixed point reproduce the sum) and **uniqueness** (no seed-dependent wrong lock), at a settle budget (`SETTLE_BUDGET`, larger than the worst observed N=32 path lock time) chosen so a lock is genuinely reached rather than budget-truncated. The lock-**time** variance across seeds (some N=32 worst-case seeds need ~15,700 sweeps) is **not** a correctness issue — it is the O(N²) path-graph settling cost, which is P2's subject. It could have failed (a fundamentally seed-dependent or coupling-broken carry would lock to different vectors); it did not.

### §2.2 P2 — SETTLING-TIME vs WIRE-COUNT (hop-counted, NOT wall-clock), all FOUR structures

Two srmech-native instruments, both Class L: (i) the **Fiedler value `λ₂`** of each coupling graph's Laplacian (`dense_laplacian → jacobi_eigvals`; near-zero test via `cascade.magnitude`, never `abs()`) — `1/λ₂` is the relaxation-rate proxy and the F122 K_c tie; (ii) the **linear-consensus hop count** — synchronous `x ← x − dt·L·x` with `dt = 0.9/λ_max` (stable on every graph), counting sweeps until deviation-from-mean < tol. The consensus count is the honest, **non-gameable** settling-rate measurement (decoupled from the binary-pinning nonlinearity, so it cannot be inflated by pinning strength); it tracks the condition number `λ_max/λ₂` (textbook).

**Single-graph topologies** (carry nodes m = N+1):

| graph | wires | λ₂ scaling | `1/λ₂` (N=4→32) | consensus sweeps (N=4→32) | per-doubling ratio | reading |
|---|---|---|---|---|---|---|
| **ripple path** (1-D line) | **O(N)** | ~(π/N)² | `2.62 → 8.29 → 29.37 → 110.42` | `131 → 442 → 1437 → 5258` | **~×3–3.5 → O(N²)** | **WORSE than ripple O(N)** |
| **lookahead tree** (binary, log depth) | **O(N)** | ~1/N | `1.93 → 5.46 → 12.51 → 27.07` | `99 → 340 → 832 → 1733` | **~×2–3 → O(N)** | **no better than ripple** (log DEPTH ≠ O(log N) consensus) |
| **all-to-all** (dense) | **O(N²)** | = N exactly | `0.200 → 0.111 → 0.059 → 0.030` | `6 → 7 → 7 → 7` | **~×1 → O(1)** | sub-linear **only** here, at O(N²) wires |

The key subtlety, **measured**: the lookahead tree has log combinational DEPTH but its **symmetric diffusion** consensus time is O(N), not O(log N), because a symmetric relaxation must cross the root-to-leaf paths of length log N both ways. So **only** the all-to-all O(N²)-wire graph gives sub-linear (O(1)) settling — and that is exactly the wiring carry-lookahead already pays. **On a single symmetric graph, the speedup null fires.**

**The fourth structure — hierarchical nibble-block carry-select (the F119/F120 two-tier read):**

| N | wires | Tier-1 (parallel, max-over-nibbles) | Tier-2 (block-carry) | n_nibbles | reading |
|---|---|---|---|---|---|
| 4 | `6` | `243` | `27` | 1 | one nibble = base case |
| 8 | `13` | `243` | `8` | 2 | hi/lo nibble = the F232 2-thread |
| 16 | `27` | `445` | `9` | 4 | 4 nibbles = the F233 4-thread |
| 32 | `55` | `445` | `8` | 8 | N/4 nibbles = the multi-threading |

**Tier 1 (intra-nibble local lock = the 4-thread Klein-4 unit):** each 4-bit nibble (= |Klein-4| = the F233 4-thread rung = the 7483 hardware block) is an **independent** small Kuramoto sub-system that locks **locally + in parallel**, speculatively computing BOTH carry-in hypotheses (cin=0 AND cin=1 = carry-SELECT) → block-generate `G_k` and block-propagate `P_k`. The nibbles **do not wait on each other** — THAT is the parallelism, and each nibble is a THREAD (F231-dispatched). Cost = **max-over-nibbles, NOT sum** — and a 4-bit nibble is **constant-size**, so Tier-1 cost is **O(1) regardless of N**. **Tier 2 (inter-nibble block-carry):** the block-carry recurrence `c_block_{k+1} = G_k OR (P_k AND c_block_k)` over the N/4 blocks, itself a tiny Kuramoto carry line (recursable to a log-depth block-of-blocks tree). The **Class-K carry latch** (F217 SR latch) is the **Tier-1 → Tier-2 BRIDGE** (F120): a MUX that selects each nibble's resolved carry vector by the block carry-in. **WIRES = O(N)** (`2 · (N/4) · (NIBBLE−1) + (N/4 − 1)` — two hypotheses × constant-size nibbles + the block graph), **dodging the all-to-all O(N²) trap.**

**The honest positive:** the nibble-block structure beats the single-graph null **at O(N) wires** because the parallelism is **across independent blocks** (carry-SELECT speculation), **not within one symmetric diffusion**. Its remaining serial cost is the Tier-2 block recurrence — which is exactly carry-lookahead's parallel-prefix structure. So it does **not** buy sub-linear consensus on one graph; it buys the **carry-lookahead win** (O(N) wires, parallel speculative blocks) in Kuramoto form. This is the structurally-correct reading of "the Kuramoto-coupled adder" the user asked for: **the nibbles-as-threads two-tier adder, not a single dense-coupled line.**

### §2.3 P3 — K_c LOCK THRESHOLD (the coupling is NOT decorative)

**Measured (DEMONSTRATED).** Sweeping global coupling K through the critical point on the worst-case all-propagate add (where propagate nodes have zero self-bias and MUST inherit via coupling): there is a **K_c** below which the net fails to lock (wrong/unresolved carries, low r) and at/above which it locks to the correct carry assignment. `Measured K-sweep (worst-case all-propagate, N=16, ripple_path): K=0.0 → r=0.137 WRONG; K=0.05 → r=0.790 WRONG; K=0.10 → r=0.927 CORRECT; K=0.20/0.30/0.50/1.0/2.0 → all CORRECT (r 0.83–0.93).` Crucially **it does NOT lock correctly at K=0** (`locks_at_K0 = False`) — so the coupling does real work; the pinning field alone does **not** fix the propagate-position carries. **Genuine threshold = True.** Measured K_c `≈ 0.10` against the F122 anchor K_c ≈ 0.20 and the ripple-path Fiedler value `0.009056 (λ₂ of the N=16 carry-node path graph, m=17)` (the gap-sets-threshold reading: the longer the worst-case chain, the larger the K needed to drive the propagate cascade to lock within budget — the spectral-gap / critical-coupling tie). This closes the spurious-positive risk that the pinning field is doing all the work (guard #6): it is not.

---

## §3 Adversarial audit — where a positive could be spurious, and the guard that fired

| # | spurious-positive risk | guard (built-in) | outcome |
|---|---|---|---|
| 1 | all-to-all O(N²) coupling smuggling in the parallelism | all three graphs spectrally measured **with edge-count**; speedup verdict requires sub-linear settling on a **sub-quadratic-wire** graph; all-to-all row included explicitly as the trap | **fired** — the null-on-single-graph-speedup verdict; all-to-all's O(1) settling is quoted **with** its O(N²) wires |
| 2 | wall-clock instead of hop-count | P2 measured in synchronous **sweeps/hops** only (consensus sweeps; tier sweeps); never wall-clock | clean — sweep-count is the currency |
| 3 | cherry-picked inputs | P1 includes the all-propagate **worst case** (maximal chain) + random at every width | clean — 100% exact required and met |
| 4 | seed-dependent / relabeling lock | readout is **absolute** (`cos θ_i` sign via pin_slot against the pinned generate/kill anchors, not relative phase); 5-seed reseed requires the **same** carry vector; wrong-stable distinguished from not-yet-locked | clean — **no wrong-stable lock** at any width |
| 5 | convergence-tolerance gaming | readout demands orientation ≠ 0 (`pin_slot_at_zero`); an unresolved carry is a hard P1 fail; tolerance attested (B) | clean |
| 6 | pinning-field doing the work (coupling decorative) | **P3** sweeps K; K=0 does **not** lock correctly | clean — genuine K_c, coupling load-bearing |
| 7 | directed-coupling escape hatch | the **symmetric** Kuramoto coupling is the object under test (F141: directed coupling alone is achiral-null at equal frequencies); any directed variant flagged as a DIFFERENT mechanism | held — symmetric coupling throughout; the directed prefix-scan is acknowledged as what the path graph's O(N²) consensus cannot beat |

---

## §4 What this does and does NOT establish (honest tiering)

**DEMONSTRATED (bit-exact simulation measurement, fixed N):**
1. **The carry-as-Kuramoto-phase-lock mapping is STRUCTURALLY EXACT** — the carry vector IS the phase-locked fixed point, reproduced bit-exactly + seed-uniquely (P1).
2. **The coupling is load-bearing, not decorative** — a genuine K_c threshold exists; K=0 does not lock (P3).
3. **On a single symmetric graph the speedup null fires** — only all-to-all (O(N²) wires) gives sub-linear settling; path (O(N²) consensus) and tree (O(N) consensus) do not beat ripple O(N) (P2). The relaxation-to-consensus primitive (rate `1/λ₂`) is the wrong dynamical tool to beat a directed parallel-prefix scan on a single graph.
4. **The nibble-block carry-select structure carries an honest positive at O(N) wires** — Tier-1 constant-cost parallel nibbles (nibbles-as-threads) + Tier-2 block-carry, matching carry-lookahead's parallel-prefix structure without the O(N²) all-to-all wiring (P2, fourth structure).

**FRAMEWORK-READING (NOT demonstrated; MFO §VII.6.20 ceiling):**
- The "Kuramoto mechanism generalizes DOWN INTO THE ALU of any processor architecture" / "replaces the ripple-carry primitive" synthesis. What is demonstrated is the **fixed-N mapping** + the **structural** placement of the ripple adder as the 1-thread chirality-LOCKED floor of the F219 ladder and the coupled adder as its un-locked sibling. The leap to every-architecture stays a **reading**. The honest qualifier: on a **single** coupling graph the Kuramoto framing **re-describes** the carry fixed point but does **not** replace ripple with a faster primitive; the useful replacement is the **nibble-block carry-select** structure — which is the Kuramoto-form of carry-lookahead, a known parallel-prefix idea, here read as nibbles-as-threads on the F219/F232/F233 ladder, **not** a new speedup over carry-lookahead.

**CAD-banned:** no gate-delay / fan-out / propagation-delay / PCB / timing-closure / fabrication-tolerance claim. The 74xx-TTL framing (F217: the Class-K pin-slot IS a cross-coupled-NAND SR latch = the carry latch) is the **existence-proof lens** — the atoms are elementary TTL — **not** a build instruction. **Defensive scope:** addition is general arithmetic; framework-reading only; no weapons / crypto-attack / capability-assessment framing.

---

## §5 srmech gap (logged for UPSTREAM_NOTES — candidate; not filed by this finding)

**CONFIRMED gap:** srmech 0.5.0rc22 ships **no Kuramoto/ODE integrator** (checked the cascade / laplacian / hdc / cyclic / primes / rational surfaces; consistent with F231, F141, and the R-95 precedent, all of which hand-rolled the Euler step). The **minimal** hand-roll here is the Euler accumulation `θ ← θ + dt·(coupling + pinning)` **only**; every transcendental (`sin`/`cos`/`exp_i` via `laplacian.elementwise_transcendental`), modulus (two `cascade.magnitude` + sqrt), spectrum (`dense_laplacian` + `jacobi_eigvals`), carry latch + readout (`cascade.pin_slot_at_zero`), and chirality op (`cascade.reorient` / `net_chirality`) inside it routes through srmech. numpy is the array carrier only. **No existing srmech op is routed around.**

**Candidate UPSTREAM_NOTES item (for the user/maintainer to file):** a thin `srmech.amsc.cascade` (or a `kuramoto`-namespaced) **Sakaguchi-Kuramoto step op** — a candidate Class-L/Class-C composite (transcendental coupling + chirality phase-state) — would close this gap; now requested by **three** findings (F141, F231, F234). Secondary: `cascade.magnitude` takes a real scalar, so the complex order-parameter modulus is built from two `magnitude` calls + sqrt (the F231 pattern); a **native complex-modulus op** would also be a clean add.

---

## §6 Reproduction

```bash
/tmp/verify_srmech_rc22/venv/bin/python3 \
  docs/srmech/rbs_lm_research/R-RBS-LM-234_kuramoto_coupled_adder.py
/tmp/verify_srmech_rc22/venv/bin/python3 \
  docs/srmech/rbs_lm_research/check_srmech_discipline.py \
  docs/srmech/rbs_lm_research/R-RBS-LM-234_kuramoto_coupled_adder.py   # -> 0 HARD
```

`response_sha256` is computed over the record body minus the wall-clock `generated_at`, so the **measurement** re-verifies bit-for-bit across reruns (the MPM point). **Confirmed bit-exact across two independent runs:** `response_sha256 = 62f19d37de631f3aaf88dae88a24063642fd07822ea5fd4462609491ea33c0b8`. The on-disk ndjson sha256 (which includes the wall-clock `generated_at`, so it differs per run) is reported at the end of each run.
