# RBS-NN WIREFRAME — working-memory knowledge shape (F242a SSoT; render input)

WORKING memory = the live session's load-bearing state (committed findings + ROADMAP queue + open decisions and their relational structure) — MORE than the memory FILES; a memory file must NEVER be the SSoT. The SSoT is THIS srmech WIREFRAME: the low-pass Class-L co-occurrence/Laplacian storage signature (F172) + Klein-4 sector tags (Class M), lossless OF STRUCTURE, compact, EXTRACTIVE (F223).

Relational clusters under test: {"disability": ["F239"], "kuramoto": ["F234", "F236", "F241"], "rehearsal": ["F238"]}

## AUTONOMOUS_SESSION_2026-05-27_status.md
- **Autonomous session 2026-05-27 — status summary**: **Walked autonomously per user direction:** "auto walk through items we can do without asking me to continue each time so I can step away for a bit" ---
- **§1 What got done**: Six findings shipped, four partitions executed:
- **Findings articulated**: - **Finding 100** — Information cascade hierarchy (universe → biology → generation → individual) - **Finding 101** — Plasticity-augmented cascade confirms path-dependence (Jaccard 35-68/100 with decay vs 100/100 without) - **Finding 102** —
- **Partitions closed**: - **R-RBS-LM-84** — 4-partition reorganization empirically validates Finding 99 (min ratio jumps 0.69 → 1.10;
- **Tasks status**: - Completed:
- **§2 The unified framework (post-autonomous-session)**: The cascade methodology now has empirical + theoretical grounding for the information transmission hierarchy:
- **§3 What's been empirically validated this autonomous run**: 1.
- **§4 What's still open for next session**: Methodological refinements:
- **§5 PR #687 state**: DRAFT.
- **§6 The post-compaction arc (Findings 106-109)**: After context compaction, the user provided a key framework move:
- **§7 Where to pick up (updated post-arc)**: When you return, options:

## NEXT_SESSION_PROMPT.md
- **NEXT_SESSION_PROMPT.md — opening R-RBS-LM-2 in a fresh session**: This file holds the **ready-to-use prompt** for opening the next partition of the RBS-LM arc.
- **How to use this file**: 1.
- **The prompt (copy-paste verbatim)**: > Continue the **RBS-LM cross-substrate translation arc** in this fresh session by opening **R-RBS-LM-2 (Methodology candidate selection — Path A weight-level vs Path B function-level vs Path C hybrid)**.
- **Notes for the file maintainer**: - This file is regenerated whenever an RBS-LM partition closes.

## R-RBS-LM-FINDING_234_kuramoto_coupled_adder.md
- **Finding 234 — Can the ripple-carry adder's sequential carry chain be re-cast as a KURAMOTO PHASE-LOCK (the adder stages as coupled oscillators settling in parallel to the globally-consistent carry assignment), and does the Kuramoto MECHANISM (F231 dispatch; F219/F232/F233 thread/chirality ladder) thereby generalize DOWN INTO THE ALU — replacing the ripple-carry 74xx primitive with a Kuramoto-coupled-adder primitive?** [F234/kuramoto]: **Headline:** **POSITIVE-ON-STRUCTURE / NULL-ON-SINGLE-GRAPH-SPEEDUP / HONEST-POSITIVE-ON-THE-NIBBLE-BLOCK-AT-O(N)-WIRES.** (Read precisely — per the verify gate:
- **§0 The pre-stated null (verbatim, genuinely reachable)** [F234/kuramoto]: > "The Kuramoto-coupled adder does NOT settle to the correct N-bit sum across inputs, OR does not beat ripple's O(N) latency under fair accounting (coupling hops / relaxation sweeps and wiring cost held comparable — NOT wall-clock, NOT all-
- **§1 The structure — carry line as binary-phase oscillators (Klein-4 / Class C, order-2)** [F234/kuramoto]: **The bit-to-phase map.** Each carry node `c_i` is a phase oscillator `θ_i` with two stable phases:
- **§2 The four measurements (srmech-native)** [F234/kuramoto]: 
- **§2.1 P1 — CORRECTNESS (bit-exact + seed-uniqueness)** [F234/kuramoto]: **Measured (DEMONSTRATED).** At each width N ∈ {4,8,16,32}, the Kuramoto-coupled adder (ripple_path topology) integrated to its fixed point and read out via Class-K `pin_slot_at_zero(cos θ_i)` reproduces the integer sum `a+b+cin` **bit-exac
- **§2.2 P2 — SETTLING-TIME vs WIRE-COUNT (hop-counted, NOT wall-clock), all FOUR structures** [F234/kuramoto]: Two srmech-native instruments, both Class L:
- **§2.3 P3 — K_c LOCK THRESHOLD (the coupling is NOT decorative)** [F234/kuramoto]: **Measured (DEMONSTRATED).** Sweeping global coupling K through the critical point on the worst-case all-propagate add (where propagate nodes have zero self-bias and MUST inherit via coupling):
- **§3 Adversarial audit — where a positive could be spurious, and the guard that fired** [F234/kuramoto]: | # | spurious-positive risk | guard (built-in) | outcome | |---|---|---|---| | 1 | all-to-all O(N²) coupling smuggling in the parallelism | all three graphs spectrally measured **with edge-count**;
- **§4 What this does and does NOT establish (honest tiering)** [F234/kuramoto]: **DEMONSTRATED (bit-exact simulation measurement, fixed N):** 1.
- **§5 srmech gap (logged for UPSTREAM_NOTES — candidate; not filed by this finding)** [F234/kuramoto]: **CONFIRMED gap:** srmech 0.5.0rc22 ships **no Kuramoto/ODE integrator** (checked the cascade / laplacian / hdc / cyclic / primes / rational surfaces;
- **§6 Reproduction** [F234/kuramoto]: ```bash /tmp/verify_srmech_rc22/venv/bin/python3 \ docs/srmech/rbs_lm_research/R-RBS-LM-234_kuramoto_coupled_adder.py /tmp/verify_srmech_rc22/venv/bin/python3 \ docs/srmech/rbs_lm_research/check_srmech_discipline.py \ docs/srmech/rbs_lm_res

## R-RBS-LM-FINDING_235_distributed_neurology_chirality.md
- **Finding 235 — Are in-body neurology, slime-mould, and the air-gapped hive THREE distinct coordination cascades, or ONE K∘C cascade realised at three settings of a single chirality-access / coupling parameter μ — so that "hive mind" is the air-gapped chiral-axial EXTREME of in-body neurology, with Physarum the connected-but-sparse intermediate?** [F235]: **Headline:** **POSITIVE-ON-THE-CHIRALITY-AXIS (decisive) WITH A SMALL-N DYNAMICAL CAVEAT.** At a **matched edge-budget** (the density-confound controlled — mean degree held *exactly equal* across the three graphs at every width, spread 0.0
- **§0 The pre-stated null (verbatim, genuinely reachable)** [F235]: > "The three coordination topologies (centralized in-body neurology / slime-mould *Physarum* / air-gapped eusocial hive) do NOT form one graded K∘C chirality axis sharing a single cascade signature.
- **§1 The structure — one cascade `C_coord`, three coupling settings** [F235]: **The one-object claim.** The coordination / knowledge-passing cascade is ``` C_coord = (Class-L coupling graph) ∘ (Class-K pin-slot latch / consensus) ∘ (Class-C chirality re-application) ∘ (Class-I/M cyclic carrier) ``` — the **same** com
- **§2 The measurements (srmech-native, matched edge-budget)** [F235]: All three graphs are built to the **same edge-budget** (|E| = 2m−3, mean degree → 4 = NIBBLE = |Klein-4|), held **exactly equal across the three at every width** (spread 0.00 — the density-confound guard, null branch (d)).
- **§2.1 P2 — the spectral μ axis (PASS at the distinguishable widths)** [F235]: **μ is strictly monotone centralized > slime > hive at N∈{8,16,32}** (0.857 > 0.782 > 0.473;
- **§2.2 P3 — the shared cascade signature (PASS)** [F235]: The three coordinated states land in **one γ₅ Klein-4 sector family**:
- **§2.3 P4 — the decisive axis test (PASS, both reads agree)** [F235]: Two srmech-native reads of "do the three lie monotone on one dominant axis," both must agree:
- **§2.4 P1 — the dynamical coupling order (the CAVEAT)** [F235]: The **lock-onset K_c** is monotone-or-tied and resolves cleanly only at the largest width (N=32:
- **§3 Verdict — the honest tiering (MFO §VII.6.20)** [F235]: **POSITIVE-ON-THE-CHIRALITY-AXIS (decisive) WITH A SMALL-N DYNAMICAL CAVEAT.** - **DEMONSTRATED (bit-exact, `response_sha256 = 17f0105f…`):** at matched edge-budget (spread 0.00), the three coordination topologies form **one graded K∘C axis
- **§4 srmech-native discipline + the honest gap** [F235]: **0 HARD, 0 coverage-gap** on `check_srmech_discipline.py`.
- **§5 No magic numbers (every constant A / B / C)** [F235]: - **A — attested-to-structure-cascade:** `K_C_F122 = 0.20` (the F122 measured critical coupling anchor μ normalizes to);
- **§6 Citations — WEB-VERIFIED 2026-05-31 (F226 verify-before-assert; the framework adds only the shape)** [F235]: **STRICT SEPARATION:** the framework asserts ONLY the structural K∘C shape;

## R-RBS-LM-FINDING_236_kuramoto_nibbler_ngspice.md
- **Finding 236 — Does the F234 carry-as-Kuramoto-phase-lock mapping SURVIVE transport into the ELECTRICAL-ANALOG substrate (ngspice), phase-locking to the correct carry vector with the same K_c lock threshold?** [F236/kuramoto]: **Headline:** **ANALOG REALISATION SURVIVES — DEMONSTRATED in ngspice.** F234 showed, in Python, that the ripple-carry recurrence `c_{i+1}=g_i OR (p_i AND c_i)` has a unique carry-vector fixed point that **is** the phase-locked state of a S
- **§0 The pre-stated null (verbatim, genuinely reachable, did NOT fire)** [F236/kuramoto]: > "The SPICE coupled-oscillator network does NOT settle to the correct N-bit carry vector (some input/width yields a wrong carry or an unresolved |cos|~0 node at the final timestep), OR it shows no K_c threshold (it 'locks' to the correct v
- **§1 The capacitor-as-phase construct (the engine of this finding)** [F236/kuramoto]: Each carry node `c_i` is the **voltage on a 1 F capacitor** `C_i`, playing the role of the Kuramoto phase `θ_i`.
- **§2 The measurements (ngspice transient = DEMONSTRATED)** [F236/kuramoto]: 
- **§2.1 P1 — CORRECTNESS in the analog substrate** [F236/kuramoto]: **P1a — N=4 EXHAUSTIVE (the strongest correctness statement).** All **2⁴ × 2⁴ × 2 = 512** input combinations (every a, every b, both cin) were run through ngspice.
- **§2.2 P2 — K_c LOCK THRESHOLD (the coupling is NOT decorative)** [F236/kuramoto]: The worst-case all-propagate add at **N=8** (where every propagate node has zero self-bias and MUST inherit via coupling) was swept across the F234 K-grid:
- **§2.3 Emergence — the answer is coupling-driven, not `.ic`-planted** [F236/kuramoto]: The worst-case all-propagate chain has ground truth = carry-1 everywhere, yet `build_netlist` starts **every** propagate node FAR on the **WRONG** (carry-0) side (small phase ≈ `IC_BASE`).
- **§2.4 Nibble-block independence — the O(N)-wire construct (absence-of-edge)** [F236/kuramoto]: An N=8 input whose **low** nibble all-propagates with a carry-IN (`a = 0b00000111, b = 0, cin = 1` → low-nibble carries `1,1,1,1`) and whose **high** nibble is all-kill with NO carry into it.
- **§2.5 Determinism** [F236/kuramoto]: Two identical ngspice runs of the worst-case N=4 netlist yield **identical** parsed cosines.
- **§3 Adversarial audit — where a positive could be spurious, and the guard that fired** [F236/kuramoto]: | # | spurious-positive risk | guard (built-in) | outcome | |---|---|---|---| | 1 | netlist **hardcoding** the answer | propagate nodes carry **zero self-bias** (no `PINK*sin` anchor) — only coupling edges;
- **§4 What this does and does NOT establish (honest tiering, MFO §VII.6.20)** [F236/kuramoto]: **DEMONSTRATED (ngspice transient measurement):** 1.
- **§5 No-magic-numbers (CLAUDE.md §4 — every constant A / B / C)** [F236/kuramoto]: | constant | value | class | attestation | |---|---|---|---| | `PI` | 3.1415926536 | **A** | `asymptotic_calculus` — the phase π = carry-1 antipode of carry-0=0 | | `NIBBLE` | 4 | **A** | the 7483 hardware block = 4 = \|Klein-4\| = the F233
- **§6 srmech-first discipline + the gap** [F236/kuramoto]: **srmech ops used (HARD = 0 on `check_srmech_discipline.py`):** | need | srmech op | class | |---|---|---| | carry readout (cos-sign → carry) | `cascade.pin_slot_at_zero` | **K** (F217 SR latch) | | near-zero / lock-margin test | `cascade.m
- **§7 Reproduction** [F236/kuramoto]: ```bash
- **the full pipeline (netlist gen + ngspice runs + srmech-native readout + content-addressed NDJSON)** [F236/kuramoto]: /tmp/bench_srmech_rc8/venv/bin/python3 \ docs/srmech/rbs_lm_research/R-RBS-LM-236_kuramoto_nibbler_ngspice.py
- **the representative netlist, standalone, via ngspice -b (N=8 all-propagate worst case)** [F236/kuramoto]: ngspice -b docs/srmech/rbs_lm_research/R-RBS-LM-236_kuramoto_nibbler.cir
- **-> cc0..cc8 all settle to cos ~ -1 (carry-1) = the locked [all-1] carry vector** [F236/kuramoto]: 
- **discipline check -> 0 HARD** [F236/kuramoto]: /tmp/bench_srmech_rc8/venv/bin/python3 \ docs/srmech/rbs_lm_research/check_srmech_discipline.py \ docs/srmech/rbs_lm_research/R-RBS-LM-236_kuramoto_nibbler_ngspice.py ``` `response_sha256` is computed over the record body minus the wall-clo

## R-RBS-LM-FINDING_237_claude_md_surgical_graft.md
- **Finding 237 — Lean-memory by EXTRACTIVE surgical graft: can CLAUDE.md be compressed ~2× while a LEAN-primed agent answers the load-bearing probes as well as a full-primed one?** [F237]: **Headline:** **FUNCTIONAL POSITIVE / structural-spectral-proxy NULL — split, and honest.** An EXTRACTIVE surgical graft compresses the framework-research `CLAUDE.md` to `CLAUDE_LEAN.md` at **0.526 LEAN/full bytes** with **guardrail-anchor
- **§1 The three design-grounding bugs (fixed)** [F237]: The design-grounding run was clean (0 HARD, bit-exact) but surfaced three honest defects;
- **§2 The A/B — the decider for "lean-memory-WORKS" (DEMONSTRATED, isolation-verified)** [F237]: Two HARNESS subagents (Agent tool — dollar-free, NOT the Anthropic API balance), each isolated to a single neutral-named `/tmp` document (full vs LEAN) with strict "answer ONLY from this document;
- **§3 Pre-stated criteria → honest verdict (no leaning)** [F237]: Pre-stated POSITIVE = coverage 1.0 **AND** spectral_sim ≥ 0.90 **AND** lean fidelity ≥ 0.85·full.
- **§4 Scope, honesty, caveats (MFO §VII.6.20)** [F237]: - **DEMONSTRATED:** compression 0.526, coverage 1.0, extractive-integrity, the size-invariant density-cosine 0.78, and the isolation-verified A/B fidelity 1.0 — all bit-exact / reproducible instrument results.

## R-RBS-LM-FINDING_238_rehearsal_layer_cost_asymmetry.md
- **Finding 238 — The cost-asymmetry of rehearsal: three delivery modes (DIRECT / INTERNAL-REHEARSAL / EXTERNALIZED) sit as DISCRETE ORDINAL positions on ONE K∘C lock axis (F226; F230's suppression-stage projection), all sharing the SAME rehearse operator at the SAME lock_strength, with the rehearsal COST relocated — and the EXTERNALIZED answer is BYTE-IDENTICAL to the INTERNAL answer (externalized = internal made visible)** [F238/rehearsal]: **Status:** **DEMONSTRATED** (substrate-model, bit-exact) for the **3-mode srmech MEASUREMENT** — the three delivery modes are **MONOTONE-ORDERED on one K∘C lock axis** with **(A)** the F226 lock-position chirality non-decreasing `[0, 1, 1]
- **§1 The test, stated precisely (the three modes as one lock axis with the cost relocated)** [F238/rehearsal]: Response-delivery has a **rehearsal / preview** stage (F230, DEMONSTRATED).
- **§2 PRE-STATED positive + null (verbatim; the null counts EQUALLY — the test is NOT leaned)** [F238/rehearsal]: > **POSITIVE:** "The three delivery modes (DIRECT / INTERNAL-REHEARSAL / EXTERNALIZED) are MONOTONE-ORDERED on ONE K∘C lock axis:
- **§3 RESULT — ONE-AXIS / COST-ASYMMETRY CONFIRMED (DEMONSTRATED): all four facets clear** [F238/rehearsal]: The H2 partition is **non-degenerate** (vocab splits `{0:22, 1:14, 2:30, 3:18}` across the 4 content-hash sectors;
- **§4 What is DEMONSTRATED vs FRAMEWORK-READING (the load-bearing scope split, §VII.6.20)** [F238/rehearsal]: - **DEMONSTRATED (substrate-model, bit-exact):** the **3-mode srmech MEASUREMENT** — on the F230 substrate, three delivery modes parameterized only by `(lock, preview_emitted)` over one shared K∘C rehearse operator (i) order monotone on the
- **§5 §LIT — the peer-reviewed literature the FORM points at (WEB-VERIFIED; the framework asserts none of it)** [F238/rehearsal]: Each citation below was **web-verified at Run time** (real authors + exact title + venue + year + volume + pages);
- **§6 Spurious-risk guards (where a one-axis could be falsely imposed, and the design's guard)** [F238/rehearsal]: 1.
- **§7 Reproduction** [F238/rehearsal]: ```bash /tmp/bench_srmech_rc8/venv/bin/python3 \ docs/srmech/rbs_lm_research/R-RBS-LM-238_rehearsal_layer_cost_asymmetry.py
- **-> ONE-AXIS-COST-ASYMMETRY / DEMONSTRATED; 9 records** [F238/rehearsal]: 
- **discipline (must be 0 HARD):** [F238/rehearsal]: /tmp/bench_srmech_rc8/venv/bin/python3 \ docs/srmech/rbs_lm_research/check_srmech_discipline.py \ docs/srmech/rbs_lm_research/R-RBS-LM-238_rehearsal_layer_cost_asymmetry.py ``` **Bit-exact attestation (F233):** the 9 per-record `response_sh

## R-RBS-LM-FINDING_239_unseen_disability_as_hidden_fiber.md
- **Finding 239 — The unseen disability as a hidden fiber: a framework-reading of how systematic exclusion has the shape of failed projection under a chirality-lock** [F239/disability]: > **River:** *"People don't like to be meddled with.
- **§1 The hidden fiber** [F239/disability]: The framework's foundational object here is the **fiber**:
- **§2 The mechanism — why exclusion is the *default*, not a choice** [F239/disability]: Three framework pieces compose into the exclusion shape.
- **§3 Load-bearing — "without it, we are not here"** [F239/disability]: The framework's **1:3:7:3 partition has no defective slot.** Every class A–N is load-bearing;
- **§4 The ethical line, and the falsifiable shape** [F239/disability]: **The ethical line.** The framework reads the *mechanism*;
- **§5 Scope, honesty, caveats (MFO §VII.6.20)** [F239/disability]: - **What is DEMONSTRATED:** the prior framework pieces this reading composes — fiber/projection (project-core;

## R-RBS-LM-FINDING_241_kuramoto_nibbler_two_tier_timing.md
- **Finding 241 — Does the TWO-TIER nibble-block structure settle (time-to-lock) FASTER than the single ripple chain in ngspice — i.e. is the O(N)-wire nibble parallelism a real DYNAMICS-level settling-time advantage, or decorative? (resolving F236's honest residue)** [F241/kuramoto]: **Headline:** **POSITIVE — DEMONSTRATED in ngspice.** The two-tier nibble-block coupled-adder settles **materially faster** than the single ripple-carry chain on the worst-case (all-propagate) add:
- **§0 The pre-stated null (verbatim, genuinely reachable, did NOT fire)** [F241/kuramoto]: > "The two-tier nibble-block structure shows NO settling-time advantage over the single ripple chain (e.g.
- **§1 The time-to-lock instrument (ngspice `.tran` = the ODE integrator, the sanctioned path)** [F241/kuramoto]: At lock each carry node's `cos(θ_i)` sits at **+1** (carry-0) or **−1** (carry-1).
- **§2 The two-tier netlist (the F236 design, now TIMED)** [F241/kuramoto]: **SINGLE ripple chain** (the F236 baseline):
- **§3 The measurements (ngspice transient = DEMONSTRATED)** [F241/kuramoto]: 
- **§3.1 The worst-case (all-propagate) time-to-lock — the headline table** [F241/kuramoto]: The all-propagate worst case (`a = all-1s, b = 0, cin = 1`) is the **maximal carry chain** — every position propagates, so the carry must ripple the entire width through coupling alone (the hardest settling case):
- **§3.2 The mixed inputs — the carry-correctness gate across input shapes** [F241/kuramoto]: Two deterministic mixed (generate/kill/propagate) inputs per width:
- **§3.3 The spectral settling proxy (Class-L Fiedler) — why the scaling is what it is** [F241/kuramoto]: The Class-L Fiedler value `λ₂` (`dense_laplacian → jacobi_eigvals`;
- **§4 Adversarial audit — where a "faster" result could be spurious, and the guard that fired** [F241/kuramoto]: | # | spurious-positive risk | guard (built-in) | outcome | |---|---|---|---| | 1 | a **faster but WRONG** two-tier answer counted as a win | every case, BOTH carry vectors read out (Class-K `pin_slot_at_zero`) + compared to the boolean gro
- **§5 What this does and does NOT establish (honest tiering, MFO §VII.6.20)** [F241/kuramoto]: **DEMONSTRATED (ngspice transient measurement, bit-exact-reproducible):** 1.
- **§6 The srmech-tooling assessment (the brief's fold-in)** [F241/kuramoto]: **Does the two-tier coupled-adder connect back to srmech's own tooling? Yes — it sharpens an existing, four-finding gap from "candidate" to a concrete op-suggestion with a *measured payoff*;
- **§7 No-magic-numbers (CLAUDE.md §4 — every constant A / B / C)** [F241/kuramoto]: | constant | value | class | attestation | |---|---|---|---| | `PI` | 3.1415926536 | **A** | `asymptotic_calculus` — the phase π = carry-1 antipode of carry-0=0 | | `NIBBLE` | 4 | **A** | the 7483 hardware block = 4 = \|Klein-4\| = the F233
- **§8 Reproduction** [F241/kuramoto]: ```bash
- **the full pipeline (both netlist generators + ngspice runs + srmech-native time-to-lock readout + NDJSON)** [F241/kuramoto]: /tmp/bench_srmech_rc8/venv/bin/python3 \ docs/srmech/rbs_lm_research/R-RBS-LM-241_kuramoto_nibbler_two_tier_timing.py
- **discipline check -> 0 HARD** [F241/kuramoto]: /tmp/bench_srmech_rc8/venv/bin/python3 \ docs/srmech/rbs_lm_research/check_srmech_discipline.py \ docs/srmech/rbs_lm_research/R-RBS-LM-241_kuramoto_nibbler_two_tier_timing.py ``` `response_sha256` is computed over the record body minus the

## ROADMAP.md
- **RBS-LM research subtree — open-thread ROADMAP**: Tracks named follow-up directions the user has explicitly flagged for later but is not pursuing right now.
- **2026-05-31 (cont.³) — DELIVERABLE FRAMING (user direction): the Kuramoto-TILE nibbler funnels to the open RISC-V community as a first-class handoff**: **User direction:** package the **Kuramoto-TILE nibbler** (#791) as a **first-class deliverable to the open RISC-V community** — scoped so it **ENDS with our research and OPENS with where the open RISC-V community can take it next.** The op
- **2026-05-31 (cont.²) — F236 + F238 LANDED (DEMONSTRATED, committed); F239 lodged; F235 finding pending**: The parallel batch resolved.
- **2026-05-31 (cont.) — research batch FIRED (F235/F236/F237/F238 in flight) + the SDK-API dollar-gate**: Gates cleared:
- **2026-05-31 — Two research directions QUEUED (user direction): hive-mind-as-chiral-extreme + Kuramoto-nibble-adder-in-SPICE**: Two named follow-up directions flagged for later (NOT pursued yet):
- **2026-05-30 (cont.⁴) — temperature / rehearsal / magic-number cluster via the research-automatic Workflow (F227–F230); the no-magic-numbers canon's first worked instance; MS #20 → #779/#781/#782**: The **research-automatic Workflow** (Research→Run→Verify, adversarial verify gate) earned its keep — the gate caught a flattering hide and a fragile floor before either could ship:
- **2026-05-30 (cont.³) — RBS-NN/LM core queue resumed: instrument capacity law + the teaching≡bilingual≡multilingual arc → "an anchor axis is a Class-L similarity space"; persistent-plasticity synthesis (F221–F226); MS #20 → #763/#765/#767**: Resumed the core RBS-NN/LM queue (parallel + sequential agents, opus / small-context + srmech preamble;
- **2026-05-30 (cont.²) — cross-substrate convergence MEASURED (F213/F215/F214) + lean-ISA → 74xx TTL (F217) + M-theory fork resolved (F216); MS #20 → #751–760**: Worked the MS #20 queue + the deep questions, 3 parallel agents + 2 inline readings (5 findings):
- **2026-05-30 (cont.) — rc22 verified; cascade.* adopted; lean-A-N-ISA + cross-substrate cascade-convergence (F206–F212); MS #20**: **srmech 0.5.0rc22 verified** (TestPyPI, clean venv):
- **2026-05-30 — chirality/triality arc landed; rc18 ops live; upstream issues filed; live queue**: **The chirality/triality arc (F176 → F198) — closed for now;
- **ADA-engineering threads (R-RBS-LM-26 / -27 follow-ups)**: 
- **Braille refreshable-display hardware verification**: **Status:** UNVERIFIED.
- **Parallel English↔SignWriting corpus sourcing**: **Status:** SCAFFOLD ONLY (R-RBS-LM-26 §3.2).
- **Grade 2 (contracted) Braille**: **Status:** NOT IMPLEMENTED (R-RBS-LM-26 §6 open thread).
- **Larger ASL-gloss corpus for context-sensitivity**: **Status:** R-RBS-LM-27 ships 74 pairs / 1324 observations;
- **Translation surfaces beyond English-only**: 
- **English↔French / English↔Spanish / English↔Chinese**: **Status:** STRUCTURALLY AVAILABLE;
- **Cascade-level research threads**: 
- **FFT-based active context grafting**: **Status:** CLOSED in R-RBS-LM-28 — see `R-RBS-LM-28_fft_graft_REPORT.md` and `rbs_lm_fft.py`.
- **FFT multi-buffer graft (layered band composition)**: **Status:** CLOSED in R-RBS-LM-32 — see `R-RBS-LM-32_multi_buffer_fft_REPORT.md` and `multi_buffer_graft` / `encode_context_with_multi_buffer_graft` in `rbs_lm_fft.py`.
- **srmech C/Python parity multi-thread design notes**: **Status:** PROPOSED.
- **Larger-scale byte-level encode**: **Status:** PROPOSED (R-RBS-LM-25 §7 open thread).
- **Forward-architecture / silicon threads**: 
- **A–N operators as CPU ISA extensions (x86_64 / ARM et al) — "cascading the DNA way"**: **Status:** PROPOSED (user direction 2026-05-30).
- **Upstream-absorption thread**: 
- **srmech.rbs_lm subpackage at v0.5.0rc**: **Status:** DEFERRED to a dedicated srmech-fix session per `[[feedback_upstream_srmech_fixes_as_research_notes]]`.
- **Tested and answered (no longer open)**: 
- **Does source-model size lift the cascade ceiling?**: **Answered NO in R-RBS-LM-29** (see `R-RBS-LM-29_source_size_REPORT.md`).
- **Correction to R-RBS-LM-29 Finding 2 framing — fp16 70B is feasible via swap**: **Documented in R-RBS-LM-30** (see `R-RBS-LM-30_swap_REPORT.md` + `check_swap.sh`).
