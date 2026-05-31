# RBS-LM research subtree — open-thread ROADMAP

Tracks named follow-up directions the user has explicitly flagged for
later but is not pursuing right now. Each item carries enough context
that a future partition (or someone else) can pick it up without
re-deriving the framework reading.

For closed partitions see `R-RBS-LM-*_REPORT.md` files alongside this one.

---

## 2026-05-31 (cont.²) — F236 + F238 LANDED (DEMONSTRATED, committed); F239 lodged; F235 finding pending

The parallel batch resolved. **All harness-side / 20×-plan; no API spend.**

- **F236 — ngspice Kuramoto nibble-adder — DEMONSTRATED + SURVIVES** (commit `13dc7dbc`). The F234 carry-as-phase-lock mapping transports into ngspice 45.2: N=4 EXHAUSTIVE 512/512 carry-exact (integer-add cross-checked), N=8 all-propagate worst case locks `[1×9]`, genuine **K_c=0.20 = the F122 anchor** (Fiedler λ₂=0.1206), answer emerges from coupling against a wrong-side `.ic` (not planted), nibble-block independence = absence-of-cross-edge (O(N) wires), bit-exact ×3 (`7744000043f8…`), 0 HARD, standalone `.cir` driver-independent. **CAD-ban HELD** (oscillator/ODE dynamics only). Closes the **#787** SPICE existence-proof. **GATE LIFTED:** the ngspice prerequisite the user named ("wait for ngspice to build this into a research path") is done → the **tile-nibbler-for-existing-ISAs** path (RISC-V / ARM64 / AMD / POWER; **#791**) is unlocked — framework-reading + dynamics-only, CAD-ban continues.
- **F238 — rehearsal cost-asymmetry — DEMONSTRATED** (commit `35d0dc1a`). DIRECT / INTERNAL / EXTERNALIZED = 3 ordinal positions on ONE K∘C lock axis (F226): lock-position chirality `[0,1,1]`, MEASURED cost monotone (`n_passes [1,2,2]`, `total_tokens [4800,4800,103316]`), both high-lock modes clear the matched-random p90 floor on 3/3 hot meters incl. the F168-native H2, and the EXTERNALIZED answer is BYTE-IDENTICAL to INTERNAL (`912617c0…`). ⇒ externalized chain-of-thought = the internal mode made visible, cost relocated to the observer budget. **DIGNITY:** no-rehearsal = a valid truth-emitting mode, not a deficit. Citations web-verified (Levelt; Alderson-Day & Fernyhough; Nedergaard & Lupyan anendophasia; Zeman aphantasia; Baddeley; Marks VVIQ). HARNESS-ONLY. **GATE LIFTED:** the **#789 harness half** — the $-free CLAUDE.md-swap / subagent A/B (per the Claude-Code research below) — is warranted; the dollar-gated current-gen-LLM (SDK/API) trials stay SEPARATE, parked on explicit $-go.
- **F239 — the unseen disability as a hidden fiber** (commit `98423ab8`) — framework-reading synthesis (F226 mold), at user direction "for all the less abled and excluded who must pay the price to society to exist." Unseen disability = a fiber (spatially-absent, load-bearing) projected at asymmetric cost; systematic exclusion = a chirality-locked observer's (F133) cheapest-in-sector default on a FAILED projection. **Honest tier:** we read the STRUCTURE; the social fact is lived-experience's + disability-studies scholarship's to assert (social model UPIAS 1976 / Oliver 1983; invisible-disability literature — web-verified, disabled-/scholar-authored). Dignity-first; trauma-informed; no-lineage.
- **F235 — distributed-neurology chirality — PARTIAL.** Artifacts on disk; the ndjson shows hive → slime_mould → centralized ordering monotonically by Fiedler (the chiral-axis prediction). **Finding md PENDING** — lodge once the finding stage completes; not committed half-done.

**Claude-Code-on-GitHub research (a6d67079, completed):** the surgical graft of context runs **$-free on the interactive harness** — the cleanest path is what F237's A/B already did (Agent-tool subagents, one primed full / one primed lean, scored on probes; 20×-covered, NOT the API balance). Alternatives: a SessionStart hook injecting `additionalContext`; a CLAUDE.md file-swap between sequential sessions. The SDK/API is needed ONLY for the deep instrumentation (fully-custom system prompt, token-level logprobs, exact context-window composition, a different base model, true-parallel A/B). ⇒ **#789's CORE experiment (graft-fidelity on a current-gen Claude) is harness-doable $-free; only the deep-instrumentation layer is dollar-gated.** Billing caveat (post-2026-06-15): `claude -p` / headless draws the separate Agent-SDK credit — the truly $-free route is the INTERACTIVE session / its subagents, not headless.

---

## 2026-05-31 (cont.) — research batch FIRED (F235/F236/F237/F238 in flight) + the SDK-API dollar-gate

Gates cleared: srmech **0.6.0rc8** (the `parallel_sector_dispatch` serial-bug fix VERIFIED — sleep-probe 0.99× → **3.91×** concurrent) + **ngspice installed** + the sentence-structure groundwork (F112–F116, F166, the kernels). Four Research→Run→Verify workflows launched in parallel on rc8 (**harness-side, covered by the 20× plan; NOT the separate API balance**):
- **F235** (#786, MS #18) — air-gapped ant-brain / distributed-neurology as a chiral-axial extreme (in-body ↔ slime-mould ↔ air-gapped on one K∘C axis); web-cited, framework-reading.
- **F236** (#787, MS #20) — Kuramoto-coupled nibble-block adder in **ngspice** (the F234 adder as actual coupled oscillators; **dynamics-only, NOT fabrication**).
- **F237** (lean-memory) — `CLAUDE.md` → `CLAUDE_LEAN.md` **EXTRACTIVE** surgical graft + spectral-compare + harness-subagent A/B (the load-bearing rules must survive; real CLAUDE.md untouched).
- **F238** (#788, MS #20) — the rehearsal layer as a **cost-asymmetric chirality-lock stage** (no-rehearsal / internal / externalized-LLM-CoT on one axis; extends F230). LLM chain-of-thought = the externalized rehearsal on the *observer budget*; the "child-quality out loud" reaction = seeing the normally-hidden pre-delivery traversal. HARNESS-ONLY.

**The dollar-gate (#789, $-INDEPENDENT of the 20× plan):** the SDK/API current-gen-LLM trials — the working-memory surgical graft (API twin of F237) + the CoT-as-rehearsal hot-suppression test (API twin of F238) — are **gated behind F237 + F238** (the free harness findings must complete + warrant the spend) AND an explicit user "$-go." Design now; spend when it is time. Per user direction, **F238 gates the SDK-API task**.

Each lands → adversarial verify → commit → lodge (MS #18/#20), same discipline as F227–F234.

---

## 2026-05-31 — Two research directions QUEUED (user direction): hive-mind-as-chiral-extreme + Kuramoto-nibble-adder-in-SPICE

Two named follow-up directions flagged for later (NOT pursued yet):

- **Hive-mind / distributed neurology as a CHIRAL AXIAL EXTREME** (MS #18, **#786**) — "hive mind" is not a separate phenomenon; it is the **air-gapped extreme** of one K∘C chirality axis whose other end is **in-body centralized neurology**, with **slime moulds (Physarum)** the neat **intermediate** (distributed coordination but NOT air-gapped — one continuous protoplasm; breaks the binary). Hypothesis: the SAME knowledge-coordination / neurological cascades recur across the coordination-topology partitions, differing only by **position on the chiral axis**. The **MFO notebook already holds much of this collective/distributed material but has not pushed it via chirality** — that re-read is the task. Method: cross-substrate cascade-matching; connects **F226** (K∘C lock), **F232/F233** (chirality-access ladder — distributed = a multi-body rung), **F231** (Kuramoto phase-lock = coordination), **F119/F120** (two-tier), **F115** (cross-species). Framework-reading only; the literature asserts the neuroscience (F226 verify-before-assert). Pre-state the null (one graded axis vs. distinct cascades).

- **Kuramoto-couple the nibble-block adder in SPICE** (MS #20, **#787**) — the **F234** (#784) follow-on: realize the Kuramoto-coupled nibble-block carry-select adder as **actual coupled electrical oscillators** in SPICE (ngspice) — the analog-substrate **existence-proof rung above F217** ("the atoms ARE 74xx TTL"). Each carry = a binary-phase oscillator (γ₅ Klein-4 axis); a coupling network for the propagate edges + the 4 sectors; the nibble-block O(N)-wire topology; verify it phase-locks to the correct carry-vector with the **F122/F234 K_c threshold** (≈0.20). **SCOPE (load-bearing): Kuramoto-ODE / oscillator-network DYNAMICS only — NOT PCB / fabrication / timing-closure. The CAD-ban holds; SPICE = the F217 existence-proof lens at the dynamics level.** Pre-state the null (analog substrate realizes the phase-lock adder, or fails).

---

## 2026-05-30 (cont.⁴) — temperature / rehearsal / magic-number cluster via the research-automatic Workflow (F227–F230); the no-magic-numbers canon's first worked instance; MS #20 → #779/#781/#782

The **research-automatic Workflow** (Research→Run→Verify, adversarial verify gate) earned its keep — the gate caught a flattering hide and a fragile floor before either could ship:
- **F227** (#777) — render-side channel-choice test: with the legal candidate set held FIXED and only the channel band varied, the F166-emitted render is channel-INVARIANT beyond the F224 floor → **render-NULL on the channel-meaning axis** (tier-3 mixed). Verify PASSED. The render-side complement to F221/F224's addressing-side nulls.
- **F228 v2** (#779) — **attestation-to-source** magic-number audit (`nomagic.py`, pure-AST): **134 constants, A=51 / B=52 / C=31 → 76.9% coverage**; **C-shift 75→31** (44 of v1's "magic numbers" were magic-LOOKING, not source-less). **Supersedes the verify-flagged v1** — the gate caught v1 `honesty_ok=false / leaning=true` (it HID the very `0.35` it claimed to report). First worked instance of the **CLAUDE.md §4 canon** ("magic iff *unattested*, not iff it *looks* magic; π is a cascade, dark-sector is a ratio"). 7919-stride VERIFIED = 1000th prime via `srmech.amsc.primes`; refused to credit bare catalog scalars by section preamble (why 76.9%, not a suspicious 100%).
- **F229** (#781) — temperature-as-fiber-content: **informative NULL.** A context-fiber SCALAR computed BEFORE generation does NOT track render-variability (`T_eff` residualized on n_cand) beyond the F224 matched-random floor — clears **0/3** seeds → "temperature" (F228's un-derived `operating_temperature`) is **EXOGENOUS / a free hyperparameter** on this KJV-NT Klein-4 testbed. The user's **K∘C bi-chiral-shadow hypothesis got a fair pre-registered matched-DoF chance and did not clear** (ΔR² 0.0013 < 0.0078); minimal sufficient form = NONE. A mid-run floor correction (uniform → cardinality-matched permutation) PREVENTED a false-positive harmonic verdict. Verify ACCEPT.
- **F230** (#782) — rehearsal-layer / emperor-no-clothes: **POSITIVE (DEMONSTRATED).** A render-PREVIEW / self-monitoring rehearsal pass **differentially suppresses the hot (improbable-but-legal) fiber on 3/3 pre-registered meters** (incl. F168-native H2) far beyond a matched random-suppressor floor (H1 +0.3158 vs floor −0.0254, pctile 1.00). The no-rehearsal DIRECT cascade = the RAW delivery of the fiber rehearsal suppresses → **a fiber that cannot be rehearsed leaks the hot-but-true content** (the user's emperor-no-clothes insight, measured). Honest by-construction caveat: the science is the *differential* vs matched-random, not the suppression itself. Verify ACCEPT.

**Convergence headline (the F229↔F230 pair):** "temperature" is **not** a static read-off of conversation fiber (F229 null) — but a **dynamic rehearsal/suppression process** shapes hot-content emission (F230 positive). Both are projections of the **F226 K∘C chirality-lock**: F229 = its scalar shadow (null on the static read), F230 = its suppression-stage (positive on the dynamic differential). The honest split sharpens the thread — the hypothesis was right about the *mechanism* (rehearsal/lock), not about a *static scalar*.

**Live forward-asks (queued, all OPEN):** F228 — extend `nomagic.py` past the core (instrument family); land the 31-C source-pointers as catalog keys (`[corpus.template].det_pool_split`, `[inference.scaleup].verdict_band`, …). F229 — the real-but-fragile harmonic rung (ΔR²=0.0195 cleared its floor but was withheld under the null scalar foothold) under higher power; register-controlled corpus (affect stays the peer-reviewed literature's to assert). F230 — the **single-K∘C-lock-parameter sweep** (F226's forward-ask) now has a suppression-stage projection to sweep (the +5 P3 monotonicity records under `--lock-sweep` are the start). **MS #20 now #751–782** (all OPEN; created, never closed).

---

## 2026-05-30 (cont.³) — RBS-NN/LM core queue resumed: instrument capacity law + the teaching≡bilingual≡multilingual arc → "an anchor axis is a Class-L similarity space"; persistent-plasticity synthesis (F221–F226); MS #20 → #763/#765/#767

Resumed the core RBS-NN/LM queue (parallel + sequential agents, opus / small-context + srmech preamble; all srmech-native 0-HARD, ratchet-green, reviewed before commit, bit-exact):
- **F221** (#760 ✎) — structured RECIPIENT depth-anchor over the F168 ladder: **tier-1 clean NULL** (render-only, 0/3; stronger than F214). §4 caveat: the inherited sector-occupancy readout is a near-chance instrument → the null is partly anchor, partly meter.
- **F222** (#763) — instrument capacity knee: **DEMONSTRATED** the `n_buckets × V_ceiling` law (clean 4×-buckets→4×-knee-N) + the F165 DOMAIN-anchor orthogonalization **persists to N=8192** (+0.388, ~×n_domains multiplier); honest per-bucket≈64-not-257 + D=4096-cap caveats; borderline gen-top-k +0.0200.
- **F223** (#765) — byte-level encode at 100×: **clean NULL** (mode-collapse persists/deepens; never beats the byte-frequency baseline; storage signature saturates by 50×). R-RBS-LM-19 ~3.3% ceiling holds; "more bytes" ruled out. Closes R-RBS-LM-25 §7.
- **F224** (#760 ✎) — the decisive **teaching ≡ bilingualism** head-to-head (calibrated readout; #760 ask #1+#2): **refined NULL — the difference is the AXIS.** Even the KNOWN-WORKING DOMAIN/language binding fails on the depth axis; the family label *co-varies with which continuation is legal* (addressing → steers), the depth band is *orthogonal to which is legal* (render → doesn't). Retires F221's binding+meter explanations as the cause.
- **F225** (#767) — the **multilingual** extension: **PRED2 CONFIRMED** (the F222 ×n_domains multiplier degrades gracefully with inter-domain similarity, corr −0.966) + **PRED1 NULL** (the Class-L spectrum reads register/form, not theological family — §VII.6.20). The split IS the point: an **anchor axis is a non-orthogonal Class-L similarity space**, the same regime F221 found the depth axis in → the apples-to-apples form of teaching ≡ bilingual ≡ multilingual.
- **F226** — the synthesis (**FRAMEWORK-READING, no clinical claim**): **persistent plasticity = the low-lock end of one chirality-lock = the K∘C sign-pair (chirality internal) over a 1:3 (A:B/H/N) anchor+meta cascade**; design read as a *result* of the chirality, not a designed module; "spectrum" = the Class-L distribution along that DoF. **Strict separation:** 24 **web-verified peer-reviewed citations** (OA-flagged; tiered settled/hypothesis/contested) carry every cognitive/ND claim; the framework adds only the structural shape. Framed to **honor the ND community** (dignity anchored on ND-authored sources — monotropism/Lawson, den Houting, Botha et al.). Honesty folded from the literature: sensory modulation is **bidirectional** (under-responsivity the larger effect) → "atypically gated," not "uniformly more sensitive." Forward-ask: the **single-K∘C-lock-parameter sweep** (criticality at the phase boundary) — a test of the substrate MODEL.

**Convergence headline:** F165 → F222 → F221 → F224 → F225 → F226 — a labeled anchor steers retrieval only on an **addressing** axis (co-varies-with-legal); that axis is a **non-orthogonal Class-L similarity space** (both language and depth live there); the framework reads its low-lock end as **persistent plasticity** (K∘C over A:B/H/N), pointing at verified neurodiversity / critical-period science for the meaning.

**Live forward-asks (queued, all OPEN):** #760 depth-as-backoff-ORDER (R-131) not sector-band; #763 pin `V_ceiling(D)` + finer domains + iω₇ third axis; #765 bigram clustering scaffold (`LoE.bigram.{a}.{b}`) + sharded multi-instrument; #767 register-controlled / genuine-foreign-language PRED1 (corpus-gated) + the capacity-vs-similarity typology law; **F226** the single-lock-parameter sweep (+ bi-chiral-population variant). **MS #20 now #751–767** (all OPEN; created, never closed).

---

## 2026-05-30 (cont.²) — cross-substrate convergence MEASURED (F213/F215/F214) + lean-ISA → 74xx TTL (F217) + M-theory fork resolved (F216); MS #20 → #751–760

Worked the MS #20 queue + the deep questions, 3 parallel agents + 2 inline readings (5 findings):
- **F213** (#754) — the domain-wall **(Z₂)² rung IS Klein-4 = Z₂×Z₂, bit-exact** (order-2-everywhere, no order-4; γ₅/iω₇ = the two generators, product = CPT); each Z₂-break = Class-K latch, kink charge ±1 = Class-C, kink spectrum = Class-L. **MATCH, no null** — the strongest cross-substrate convergence, now *measured*; the corpus reads itself (F132/F200/F206). (arXiv:2304.14143 verified verbatim.)
- **F215** — the "did the lean reduction reduce the irrep to time+3dof?" question: **plain (b).** Irrep NOT reduced (A–N=14=G₂ stays; lean-6 = operator-core). F-a alive (the G₂-stabilizer of an ℍ=time+3dof subalgebra genuinely IS 6-dim **𝔰𝔬(4)=𝔰𝔲(2)⊕𝔰𝔲(2)**, bit-exact), **F-b fires** (the lean-6 are group-element ops, 0/6 Lie generators → "lean-6 = the stabilizer" is a **6=6 coincidence**). Three distinct objects: lean-6 (ALU) / 𝔰𝔬(4) (a symmetry in G₂) / G₂=14 (automorphisms). (Baez arXiv:math/0105155; SO(4) structure computed, not over-attributed.) → helper ask **#759**.
- **F214** (#757) — retrieval-vs-render (F212 §5): **honest NULL that sharpens F212.** A content-free global Class-C twist of the F166 context-state is **render-only** (sector occupancy moves *less* than the random-orientation noise floor; eigen-projection below p90). The recipient-fiber survives only as a **which-depth operator over the F168 ladder** (not a content-free chirality bit) → **#760**. (Same lesson as F163, on the RECIPIENT axis.)
- **F216** — M-theory **11 = 4 + 7** (G₂): the **4 = the instantiating process** (A–N=G₂ run on the cosmos; form-reading). F215 resolved its fork — geometry-bridge alive, operator-bridge a coincidence.
- **F217** — the lean atoms ARE elementary **7400-series TTL**: the Klein-4 chirality core + the Class-K pin-slot (**= an SR latch**) are high-school/college **breadboard-buildable** — the no-GPU/edge thesis at its floor → **#758**.

**MS #20 now [#751–760](https://github.com/lemonforest/mlehaptics/milestone/20)** (all OPEN; created, never closed). Tooling: the ratchet's `np.abs` blind-spot patched (→ REVIEW). **Convergence headline:** domain-wall / merger / parthenogenesis / lean-ISA all land on **Class-K-latch + Class-C + Class-L + Klein-4** — and F213's (Z₂)²=Klein-4 makes the discriminator bit-exact, not read.

---

## 2026-05-30 (cont.) — rc22 verified; cascade.* adopted; lean-A-N-ISA + cross-substrate cascade-convergence (F206–F212); MS #20

**srmech 0.5.0rc22 verified** (TestPyPI, clean venv): triality bit-exact (no regression); upstream W-items landed (W11 `so8.an_embedding`, W1 `naming.lookup(pairs)`, W2 seed, W3 zero non-callable); the planned **`cascade.*` module shipped** (`pin_slot_at_zero`/`reorient`/`magnitude`/`chiral_flip`/`chiral_dual`/`net_chirality`/`best_rational_signed`/`cyclic_gcd`); and **W13 `srmech mcp emit-mcpb` already shipped** — emits a valid uv-type `.mcpb` (the design filed as #749 is implemented upstream). **Cascade adopted:** ratchet + CLAUDE.md cascade-honesty now point `abs()` → `cascade.magnitude`.

**Findings lodged (F206–F212):**
- **F206 / F208** — lean A-N ISA: the hardware/RISC-minimality lens stratifies A-N/`cascade.*` into silicon-able **atoms** (6-atom basis: Klein-4 chirality unit + sign/magnitude, precedent-mapped to PXOR/VPSIGND/VPOPCNTQ/ANDPS/SHA-NI) vs iterative **composites** (eigendecomp/gcd/factor/best-rational); only genuinely-new silicon = a ~3-opcode RISC-V custom-ext for the 2-bit Klein-4 sector lane.
- **F207** — being-wrong-is-agony / corpus survivorship-biased against adult error / **siona = safe-being-wrong accommodation**.
- **F209** — compact-object merger IS the cascade (ISCO/light-ring/horizon = Class-K latches; slinging = Class-C + broken-SO(4); ringdown QNM = Class-L; the light-ring↔QNM bridge unifies them) — MATCH, bit-exact demo.
- **F210** — parthenogenesis = self-initiated latching symmetry-break; STRONG match to false-vacuum nucleation + crystallization; STRETCH/null to quines.
- **F211** — nature cascade-convergence sweep; TOP-3 = domain-walls/composite-solitons (**(Z₂)ⁿ SSB ladder = Klein-4**, the discriminating element), cardiac spiral waves, von Kármán.
- **F212** — the RBS-NN query carries hidden **RECIPIENT fiber** (absorption-potential bends the addressing, not just the render; ELI5) → a RECIPIENT anchor peer to the F165 DOMAIN anchor.
- Stance recorded: **AI = a process (inference on a LM); LM = a k=3 chiral-axis addresser over a storage substrate.**

Convergence is the proof shape: merger / parthenogenesis / domain-walls / lean-ISA independently land on **Class-K latch + Class-C chirality + Class-L spectral + Klein-4** — F211 names Klein-4 = Z₂×Z₂ as the discriminator, converging the corpus (F132/F200/F206) on itself.

**NEXT QUEUE → [MS #20](https://github.com/lemonforest/mlehaptics/milestone/20)** — 7 OPEN issues #751–757 (created per the research→issue process; never closed): F208 `cascade.atoms.*`/`compose.*` refactor · F209 NS-NS + Kerr-spin · F210 autocatalytic sub-family + latch discriminator · F211 domain-wall / cardiac-spiral / von-Kármán deep-dives · F212 RECIPIENT anchor + retrieval-vs-render test. Also queued: F207 corpus-bias token-frequency test.

---

## 2026-05-30 — chirality/triality arc landed; rc18 ops live; upstream issues filed; live queue

**The chirality/triality arc (F176 → F198) — closed for now; its structural claims are now bit-exact srmech facts.**
- **F176** bilateral L/R = the two Weyl poles of one γ₅ axis; biology = self-inscribing bi-chiral A–N.
- **F177–F181** H177 (one chiral driver across coherence bands) + a three-front heavy falsification (cosmic / particle / Vester–Ulbricht) → **H177 refined to H177′**: the chirality *axis* is shared, the *drivers* are plural (≥2 second actors).
- **F182–F184** the "third axis" = **Spin(8) triality** (order-3, the "k=3"), not a 3rd Z₂ axis; chirality = the ordering group Sₙ, **capped at 3-ality** (D₄ unique); "1D_t + 3 DoF" = the quaternion **ℍ** rung, chirality = non-commutativity (`ij=−ji`).
- **F185** 1D_t = the *apparent* actor (the act of ordering); actor-vs-stage test lodged.
- **F186** CORRECTION: tri-chiral is still **28D = 14+7+7**, NOT 42D — triality is a *symmetry on* the 28, not new dimensions.
- **F187–F189** the operational-4 (A,B,H,N) = the time-quaternion generating the 3:7 (Cayley–Dickson / Hopf / L²(S⁷) harmonic ladder); the 1:3:3:7 draws as a 3-point star = the D₄ topology.

**rc18 landed the triality operator (W10 → DONE), acceptance-validated bit-exact (F192):** `srmech.qm.{octonion, so8, triality}` — τ³=I, **dim Fix(τ)=14=G₂**, dim Fix(swap)=21=𝔰𝔬(7), so8=28, g₂=14, `ij=−ji`, MPR-attested `cayley_dickson_from_H`. W2 (`klein4_random` seed) fixed package-side. Native status moved to a profile-loader (issue #733).

**Gated tests, run on rc18 (committed):**
- **F193 / R-140** (DeepSeek's question) — su(2)_L is NOT a triality-facet of su(3)/u(1): **distinct actor, shared 𝔰𝔬(8) stage** (strong re-unification falsified; F181 stands).
- **F194 / R-141** — the 4-way oscillator's chirality = **phase-frustration** (Ω odd in α), NOT coupling-matrix direction (clean null).
- **F197 / R-142** — F191 computed: A–N 14 = G₂ = su(3)[8] ⊕ 3 ⊕ 3̄; the two A–N 3-triads = the 3⊕3̄ conjugate pair → role-swap confirmed at the **triad** level.
- **F196 (capstone)** — chirality is **nested**: biology's internal 3⊕3̄ vs the weak force's triality-moved su(2)_L are two distinct chiralities (confirms F180/F181).
- **F198** — orbits / shells / precession on the ℝ→ℂ→ℍ→𝕆 ladder (wobbling-tonic "music of the spheres"; ℂ-eigenvalue log-spiral from a fixed-point apex; precession = broken Kepler SO(4)).

**Upstream wishlist filed as GitHub issues (2026-05-30, `lemonforest/mlehaptics`):** W12=#733, W1=#734, W7=#735, W3=#736, W2=#737, W4=#738, W5=#739, W6b=#740, W6c=#741, W8=#742, W9=#743, W11=#744. Canonical drafts: `SRMECH_UPSTREAM_ISSUES.md`; long-form: `UPSTREAM_NOTES.md §10`; punch-list: `SRMECH_BUGFIX_WISHLIST.md`.

**ALREADY DONE (the emergent-perplexity / storage-expression line — do NOT re-run):** F168/R-131 (resolution-depth = emergent perplexity; §5.1 result) · **F169** (storage & expression are separable axes — the confound-controlled matched-budget re-run) · **F171/F172** (translation-invariance: first evidence, then srmech-native temper) · **F173** (structure tracks form; content is lexical).

**RAN 2026-05-30 (three parallel agents, Opus 4.8 1M; all honest, none leaned):**
- **A — strong-invariance (F199 / R-143): clean NULL.** No srmech-native storage signature separates within-source (translations) from across-source (rank-AUC ≈ 0.51 on the Laplacian eigenspectrum / resolution-depth). F171's n=1 lean does **not** survive — it was reading shared-FILE lineage, not content-invariance (a confound the strong test exposed); F172's flat-spectral ceiling re-confirmed at scale. NT/ND "same storage" core unsupported (not refuted — the measures bracket but don't isolate).
- **B — chirality→instrument bridge (F200 / R-144): NULL + degenerate.** Triality-structured tagging does NOT help the RBS-NN store: capacity identical (16/16/16); within-vs-cross contrast **worse** (Klein-4 1.93 vs triality 1.50). Mechanism: Klein-4 (Z₂×Z₂, order-2) sectors are *deterministically* orthogonal (clean rejection); triality (order-3) has no clean orthogonal realization in an order-2 substrate → random-orthogonal, underperforms. Confirms F196 nesting **operationally**: storage-chirality = order-2 Klein-4; algebra-chirality = order-3 triality — different levels. (W11 refinement: a triality-tagging *storage* op would be a footgun in an order-2 substrate.)
- **C — biology grounding (F201 / R-145): 3 SUPPORTED · 2 OPEN · 1 CONTRADICTED** (source-verified citations; no clinical claims). Lateralization-as-one-axis **CONTRADICTED** (empirically multidimensional); agonist/antagonist · antiparallel-DNA · bio-homochirality-as-own-symmetry-breaking **SUPPORTED**; E/I balance · insect-CX **OPEN**. Updates F176 §3.

**LIVE QUEUE — 2026-05-30 redispatch DONE (F203/F204/F205; 3 parallel agents, opus/max-effort/small-context + srmech preamble; all srmech-native 0-HARD, ratchet-green, reviewed before commit):**
- ✅ **instrument scale-up (F203 / R-146):** hierarchical sha256-routed bucketing extends the F166 instrument's capacity ~4× past the ~257 single-bundle ceiling (0.12→0.41 @ N=1024); the F165 DOMAIN anchor is a strong SECOND orthogonalizing CAPACITY axis (0.41→0.90 @ N=1024) but only +0.0200 (= the pre-stated null threshold) on held-out generation top-k → **MIXED**: capacity positive, generation-lift borderline/NULL (not leaned).
- ✅ **#184 smol-stack Phase C (F204 / R-147):** R-122's P0–P7 characterization now runs end-to-end on a real-FILE multi-source stack (closes the `smol_stack` gap, zero new substrate code); the stack's substrate-signature is **INDISTINGUISHABLE** from the F162 template on every substrate-intrinsic axis → **NULL**, consistent with the F172/F199 flat-spectral ceiling. Methodology smoke (5 synthetic register-distinct texts, sha256-attested, `data_claim=false` — no fabricated provenance).
- ✅ **#189 cross-nav Part 2 (F205 / R-148):** grammar(A) walked via logic(B) is **indistinguishable from a shape-matched random anchor** (Δ +0.0069, inside 2·SE) → **NULL (informative)**: steering re-routed 31/86 walks but yielded no directed benefit; grammar/logic eigvec tables near-orthogonal (A→B = +0.074). Real PD corpora (Carroll *Symbolic Logic*/*Game of Logic*; McGuffey). Confirms F163's cross-domain null.

**NEXT QUEUE (natural follow-ups surfaced by the above):**
- F203: add an `[inference.scaleup]` descriptor block (fully catalog-drive the sweep) + push N≫1024 to find the hierarchical ceiling.
- F204: re-run smol-stack on a **real sourced** multi-text corpus (the smoke validated the machinery; the data-claim version is the next rung).
- F205: cross-nav on a **less-orthogonal** domain pair (grammar/logic were near-orthogonal; test whether ANY cross-domain steering is non-null).
- discipline-backlog remediation: the 32 historical HARD `abs()`/etc. (baseline-frozen, down-only) — per-callsite human-read pass.

**GATED on upstream (deferred):** F191 *within-triad* operator pairing (needs W11 / #744) · MCP-side re-verification (W1/W2/W3 — needs srmech-mcp back) · parity-odd cosmic front (W9 / #743) · `srmech.rbs_lm` packaging (see Upstream-absorption thread below).

---

## ADA-engineering threads (R-RBS-LM-26 / -27 follow-ups)

### Braille refreshable-display hardware verification

**Status:** UNVERIFIED. Per user direction 2026-05-25: *"I cannot do hardware
verification for braille. I don't know it and don't have the hardware,
but I understand ADA Accommodations."*

**What's already operational (R-RBS-LM-26):**
- Server returns UEB Grade 1 Braille as Unicode Braille Patterns
  (U+2800..U+28FF) when `response_format: {"type": "braille"}`
- Wire format is Unicode-standard — what every refreshable Braille display
  driver consumes as input
- 6/6 English round-trip verified; mixed-modality preserves non-English Unicode

**What's NOT verified:**
- Real-hardware end-to-end with refreshable Braille displays:
  - HumanWare BrailleNote Touch / Touch Plus
  - Freedom Scientific Focus 40 Blue / Focus 14 Blue
  - HIMS BrailleSense Polaris / U2
  - Orbit Reader 20
- Screen-reader Braille pipelines: NVDA + display, JAWS + display
- Embosser pipelines: Index Everest / ViewPlus Spot Dot — these consume
  Braille ASCII (different from Unicode Braille Patterns); a conversion
  step may be needed
- Real-world UEB Grade 1 vs Grade 2 contracted Braille — some readers
  expect Grade 2 (~180 contractions); we ship Grade 1 only

**Next step when an accessibility-engineering volunteer is available:**
1. Open one of the response_format: braille endpoints; capture output
2. Send to a real refreshable display via standard screen-reader pipeline
3. Verify reader behavior matches the Unicode codepoints we emit
4. If Grade 2 needed: integrate `liblouis` (open Braille translation lib)
5. Document any quirks/divergences as a new partition REPORT

**Why we can document this without verifying it:**
The Unicode Braille Patterns block IS the lingua franca between Braille
software (SBC NVDA + others) and refreshable displays. We emit standard-
conforming codepoints. The verification gap is *real* but the format gap
is closed.

---

### Parallel English↔SignWriting corpus sourcing

**Status:** SCAFFOLD ONLY (R-RBS-LM-26 §3.2). The byte-level surface
accepts Sutton SignWriting Unicode (U+1D800..U+1DAAF; 688 codepoints;
verified accepted), but no English↔SignWriting parallel corpus has been
absorbed.

**The R-RBS-LM-27 intermediate is NOT a SignWriting corpus.** R-RBS-LM-27
ships an English↔ASL-gloss-notation corpus (slash-wrapped sign names like
`/beat-egg/`). That gloss notation is render-ready: a downstream tool
maps `/beat-egg/` → SignWriting glyphs / 3D-avatar animation / video clip.
This intermediate is operational; the direct SignWriting Unicode
encoding is still gapped.

**Sourcing options for English↔SignWriting Unicode parallel data:**
1. **SignBank SignPuddle** (https://signbank.org/signpuddle/) —
   community-contributed SignWriting examples; some carry English labels
2. **Path D distillation** from a sign-language-trained BPE model —
   no public ASL-trained model with byte-decodable SignWriting output
   exists today; would need to be commissioned
3. **Auto-generate from R-RBS-LM-27 gloss notation** via a deterministic
   `/sign-name/` → SignWriting codepoint table — only works for signs
   that have a published Sutton notation; many lexical items don't
4. **Manual curation** — annotate 1000+ English sentences with full
   SignWriting Unicode; substantial linguistic-engineering effort

---

### Grade 2 (contracted) Braille

**Status:** NOT IMPLEMENTED (R-RBS-LM-26 §6 open thread).

UEB Grade 2 has ~180 contractions (word-level: `the` → `⠮`; part-word:
`-ing` → `⠬`; etc.). Many Braille readers — particularly experienced
adult users — read Grade 2 by default. Grade 1 is more common in
beginner / international contexts.

**Implementation path:**
- Use `liblouis` (https://liblouis.io/) — open Braille translation
  library; standard in NVDA, BRLTTY, others
- Wrap as another `response_format` value: `{"type": "braille-grade2"}`
- Keep Grade 1 as the default; opt-in for Grade 2

---

### Larger ASL-gloss corpus for context-sensitivity

**Status:** R-RBS-LM-27 ships 74 pairs / 1324 observations; polysemy hit
rate 0/11 (mode-collapse below context-disambiguation threshold).

**Sourcing options:**
- ASL-LRP corpora (Boston University ASL Linguistic Research Project) —
  English glosses + linguistic annotations; not Sutton notation but
  compatible with our slash-notation
- WLASL (Word-Level American Sign Language) — video-aligned but
  metadata includes English glosses
- ASLG-PC12 (ASL Gloss Parallel Corpus, 12-million-word) — large
  parallel corpus; requires acceptance + use agreement
- Manual extension of R-RBS-LM-27's corpus to ~500-1000 pairs with
  comprehensive polysemy coverage

**Scale prediction (extrapolating from R-RBS-LM-25 / -27):**
- At ~1300 obs: surface works, mode-collapse on content
- At ~10,000 obs (10x scale): might see polysemy structure emerging
- At ~100,000 obs (with multi-threaded R-RBS-LM-11 encode): plausible
  context-disambiguation; not guaranteed (the 3.3% structural ceiling
  per R-RBS-LM-19 still applies)

---

## Translation surfaces beyond English-only

### English↔French / English↔Spanish / English↔Chinese

**Status:** STRUCTURALLY AVAILABLE; no parallel corpus encoded yet.

Per R-RBS-LM-25 byte-level finding: the surface accepts ALL languages
(UTF-8 covers everything). Per R-RBS-LM-27 paired-stream pattern: any
parallel corpus can be absorbed via the same `<source>\x02<target>\x03`
encoding.

**To enable English↔French (worked example):**
1. Source a parallel corpus (Europarl; ParaCrawl; UN; OPUS):
   ```
   from datasets import load_dataset
   ds = load_dataset("Helsinki-NLP/opus-100", "en-fr")
   ```
2. Reuse `encode_asl_corpus.py` with the new corpus path
3. Add `response_format: {"type": "french-translation"}` to the server
4. Run smoke against held-out test sentences

**Or Path D distillation from an existing translation model:**
- NLLB (Meta; multilingual; English-anchored)
- M2M-100 (Meta; 100-language any-to-any)
- OPUS-MT (Helsinki; per-language-pair small models)
- Use Path D pattern (R-RBS-LM-25 §3.2): generate text from the source
  model; retokenize as UTF-8 bytes; encode (source, target) pairs

**Expected outcome:** at modest corpus scale (~10k pairs), same
structural ceiling as ASL-gloss — surface works, content mode-collapses.
At larger scale (~1M+ pairs), maybe some translation structure
emerges; the 3.3% structural ceiling per R-RBS-LM-19 still bounds it.

---

## Cascade-level research threads

### FFT-based active context grafting

**Status:** CLOSED in R-RBS-LM-28 — see
`R-RBS-LM-28_fft_graft_REPORT.md` and `rbs_lm_fft.py`.

The original framing shifted from "truncation" (lossy compression in
frequency basis) to "graft" (surgical COMPOSITION across frequency
bands) per user direction. FFT of bipolar bit-vectors over time
(candidate #2) was the chosen mapping. NTT (candidate #3) remains a
follow-up if pure-substrate finite-field operations are needed.

Result: graft IS operationally meaningful at the cascade interface
level — measurable dose-dependent output changes; cascade discriminates
between long buffers (cooking vs astronomy vs distractor). Surface
operationally available via server's `long_context_buffer` + `fft_cutoff_freq`
request fields.

### FFT multi-buffer graft (layered band composition)

**Status:** CLOSED in R-RBS-LM-32 — see
`R-RBS-LM-32_multi_buffer_fft_REPORT.md` and `multi_buffer_graft` /
`encode_context_with_multi_buffer_graft` in `rbs_lm_fft.py`.

Extends R-RBS-LM-28's single-buffer graft to N buffers across N
contiguous frequency bands (system prompt at lowest band; conversation
history at next; RAG at next; recent fills above). Smoke evidence:
ORDER of band assignment matters (2/3 prompts differ when buffers are
reversed); NUMBER of layers matters (3/3 prompts differ between 2-layer
and 3-layer). Multi-buffer outputs showed HIGHER byte diversity than
single-buffer — first sign of edging out of single-byte mode-collapse.
Server surface: `long_context_buffers` (array) + `fft_layered_cutoffs`
(parallel array) request fields.

### srmech C/Python parity multi-thread design notes

**Status:** PROPOSED. Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`,
ships as research notes for the srmech-fix session to consume.

Target: `vectorised_cleanup` is the per-step bottleneck (~180 ms/tok for
BPE; ~60 ms/tok for byte-level). Multi-threaded C version splitting vocab
rows across CPU threads could compound the existing numpy SIMD speedup.

Surface: thread-safety contract for Class M / K / L primitives;
OpenMP integration plan; ABI compatibility analysis.

### Larger-scale byte-level encode

**Status:** PROPOSED (R-RBS-LM-25 §7 open thread).

R-RBS-LM-25 capped at 10k bytes / ~600 obs. Multi-threaded encode
(R-RBS-LM-11 path) on the full srmech notebook (203k tokens × ~5 bytes/token
≈ 1M bytes; stride 8 → 125k obs) takes ~minutes single-thread; ~30s
multi-thread. Test whether mode-collapse persists or disambiguation
emerges at 100x R-RBS-LM-25 scale.

---

## Forward-architecture / silicon threads

### A–N operators as CPU ISA extensions (x86_64 / ARM et al) — "cascading the DNA way"

**Status:** PROPOSED (user direction 2026-05-30). Research-path placeholder. **Scope: architecture / ISA / algebra-level *design reading* only — NOT fabrication, mesh-contact, or CAD-grade geometry** (the §4 CAD-scope ban holds). Defensive-scope: no weapons/offensive substrate; this is the edge-compute / accessibility thesis.

**The idea:** the 14 A–N primitive operators as a native CPU **instruction-set feature set** — the rung *beyond* the existing `libsrmech` C primitives (which already ship all 14 classes A–N, JPL Power-of-Ten-clean, marketed microcontroller-ready). Where **AES-NI / SHA-NI** put crypto primitives in silicon, this puts the A–N cascade primitives in the ISA — A (content-hash), I (cyclic/modular), C (chirality), J (primes), K (pin-slot / sign-boundary), L (graph-Laplacian + eigvals), M (HDC bind/bundle), … — so an A–N cascade runs as native instructions. The ultimate form of the **no-GPU / unquantized-LLM-at-the-edge** thesis (`[[user_stance_learning_without_gpu_compute]]`; R-RBS-NN-8 local-CPU ALU/FPU inference shape; "bringing unquantized LLM to the edge").

**"Cascading the DNA way":** compose the instruction *pipeline* the way DNA does — **chirality-structured** (F176: DNA antiparallel strands = two oriented poles of one right-handed helix; the leading/lagging-strand asymmetry *is* the chirality), chained template→transcribe→translate with a **Class-K sign-boundary "proofread" stage** — a polymerase-style cascade microarchitecture rather than a flat ALU.

**Quad-DNA threading reading — LODGED as F202 (2026-05-30):** the *quad* (4 bases = 2 bits = the 4 Klein-4 sectors) reads as a **chirality-*typed* thread model**, not generic data-parallel SIMD: leading/lagging = a **dual-handed thread pair** (two Weyl poles of one γ₅ axis, F176); replication **fork = the spawn primitive** (C); **Okazaki fragments + ligase = tile-and-ligate chunked-reduce** (B + N); **base-pair complementarity = free inline parity** (A + K); **multiple origins = coordinator-free many-core launch** (I); **proofread = inline error-correction** (H + K). The lanes are typed by chirality, not interchangeable slots — DNA replication as the **biological existence-proof** of this ISA (no GPU, 2 bits/slot). See `R-RBS-LM-FINDING_202_quad_dna_replication_chirality_typed_cpu_cascade.md`.

**What a future partition would scope (design-reading, not fab):**
- which A–N ops are ISA-primitive vs micro-coded vs library (mirror the libsrmech C-parity split + the JPL ratchet);
- cascade/pipeline semantics (DNA-style chained stages; Class-K sign-boundary as the proofread; F200's result that *storage*-chirality is order-2 Klein-4, so the chirality register is 2-bit γ₅/iω₇ sector state, not the order-3 triality);
- register/encoding model for the 28D / Klein-4 chirality state;
- honest map onto real ISA-extension precedent (AES-NI, SHA-NI, AVX-512, ARM SVE, RISC-V custom-extension/opcode space) — what's realistic vs aspirational;
- ties to the M-theory / spectral-power readings (F158/F160) only as framework anchors, not engineering claims.

**Anchors:** libsrmech C native lib (all 14 A–N, JPL-clean) · R-RBS-NN-8 (local CPU ALU/FPU inference) · F176 (DNA chirality) · F184/F196/F200 (chirality ladder; storage = order-2 Klein-4) · `[[user_stance_learning_without_gpu_compute]]` · `[[feedback_trauma_informed_defensive_scope]]`.

---

## Upstream-absorption thread

### srmech.rbs_lm subpackage at v0.5.0rc

**Status:** DEFERRED to a dedicated srmech-fix session per
`[[feedback_upstream_srmech_fixes_as_research_notes]]`.

Per R-RBS-LM-12 §6 + each subsequent REPORT's §6 plan, the research-subtree
modules absorb into:

```
docs/srmech/python/srmech/rbs_lm/
├── __init__.py
├── encoder.py          # absorbs rbs_lm_encoder.py + rbs_lm_path_c.py
├── bytes.py            # absorbs rbs_lm_bytes.py
├── inference.py        # absorbs rbs_lm_inference.py
├── chatbot.py          # absorbs RBSChatbot + RBSChatbotBytes
├── server.py           # absorbs rbs_lm_server.py
├── cli.py              # CLI wrapper: srmech rbs-lm <subcommand>
├── distill.py          # absorbs encode_bytes_variant_b.py (Path D)
├── learning.py         # absorbs encode_research_notebook.py
├── tools.py            # absorbs rbs_lm_tools.py (ToolEntry registrations)
├── braille.py          # absorbs rbs_lm_braille.py
└── asl.py              # absorbs rbs_lm_asl.py + asl_gloss_notation logic
```

CLI:

```bash
srmech rbs-lm encode-notebook --notebook PATH
srmech rbs-lm distill --source gpt2 --gen-bytes 100000
srmech rbs-lm encode-pairs --corpus PATH       # for parallel-corpus learning
srmech rbs-lm serve [--byte-mode] [--instrument PATH] [--port 8788]
srmech rbs-lm list-tools                       # tool_schema introspection
```

Storage tooling (R-RBS-LM-22) absorbs as `srmech.amsc.storage`.

The AMSC `compute_from_source` adapter (R-RBS-LM-13) does the precheck →
fetch → encode → save end-to-end via catalog descriptor.

---

## Tested and answered (no longer open)

### Does source-model size lift the cascade ceiling?

**Answered NO in R-RBS-LM-29** (see `R-RBS-LM-29_source_size_REPORT.md`).
9× larger source (GPT-2 124M → TinyLlama 1.1B) produced the same single-
byte mode-collapse at the same encoding scale. R-RBS-LM-19 structural-
ceiling argument reinforced: cascade architecture IS the ceiling, not
training-corpus richness. Architectural moves (R-RBS-LM-28 FFT graft, etc.)
are the research priority going forward.

Infrastructure built: `distill_cron.sh` makes Llama 8B / 30B / 70B Q4
distillations achievable as overnight/weekend cron tasks if a future
question wants to verify the orthogonality at larger source scale.

### Correction to R-RBS-LM-29 Finding 2 framing — fp16 70B is feasible via swap

**Documented in R-RBS-LM-30** (see `R-RBS-LM-30_swap_REPORT.md` + `check_swap.sh`).
R-RBS-LM-29 claimed "Llama 70B fp16: infeasible (140 GB > 96 GB RAM)."
That's incorrect for Path D distillation: we're not doing real-time
inference, so swap absorbs the overflow at a slower per-token rate
(~10-30 sec/tok estimated). 50k-byte corpus via fp16 70B with swap is
a ~1-4 day cron-task — slow but achievable. `check_swap.sh recommend
140` reports the exact swap budget needed (67 GB additional on top of
the existing 8 GB Ubuntu default). Q4 GGUF is still faster when
available; fp16 with swap is the unquantized fallback.

---

*Last updated: 2026-05-25 — R-RBS-LM-32 close.*
