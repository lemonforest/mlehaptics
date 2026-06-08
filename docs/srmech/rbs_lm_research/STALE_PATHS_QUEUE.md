# STALE_PATHS_QUEUE.md — research paths surfaced but not walked

Per `[[feedback_full_coverage_shipping_mpm_way]]` and `[[feedback_rolling_pr_partition_boundary_updates]]`: trailing research items that opened during sessions but weren't walked. Queue captured for future scope-specific sessions to avoid re-deriving the trail.

**Maintenance**: when a path is walked, move its entry to the finding that resolves it. When new paths surface, add them at the bottom of the relevant section.

---

## STATUS — All 44 original items addressed (2026-05-28)

Cleanup sweep completed in F144 → F148. Status legend:

- ✅ **RESOLVED** — empirical answer in cumulative findings
- 📖 **FRAMEWORK** — articulated reading; no empirical test scoped
- ⏸️ **DEFERRED** — explicit scope decision (defensive-scope / upstream / data-needed / out-of-domain)

| Item # | Subject | Status | Finding |
|---|---|---|---|
| 1 | Skip-zero polar similarity | ✅ RESOLVED | F144 — identical to default at D=10000 |
| 2 | Per-bit-info capacity | 📖 FRAMEWORK | F144 §2 — bipolar 1b, klein-4 2b, polar 1.06b |
| 3 | D-matched-bits comparison | ✅ RESOLVED | F144 — bipolar still wins by 0.04 |
| 4 | Noise robustness across variants | ✅ RESOLVED + NEW FINDING | F144 — klein-4 only variant above random at 50% noise |
| 5 | D-sweep chirality recall threshold | ✅ RESOLVED | F145 — D plateaus at 1024 |
| 6 | N-sweep at fixed D | ✅ RESOLVED | F145 — clean log-N degradation |
| 7 | Encoding refinement comparison | ✅ RESOLVED | F145 — random-projection > tile+quantise by 0.02 |
| 8 | Eigval-based sector assignment | ✅ RESOLVED | F145 — ≈ random sector (no improvement) |
| 9 | Very-high-N collapse | ✅ RESOLVED + NEW FINDING | F144 — log-N scaling; N=4096 ≈ random |
| 10 | Partial chirality flips | ✅ RESOLVED + NEW FINDING | F144 — only full CPT gives strong anti-correlation |
| 11 | Mixed-sector bundles | ✅ RESOLVED + NEW FINDING | F144 — symmetric retrieval (75/25 = 25/75) |
| 12 | D vs N Pareto for chirality | ✅ RESOLVED | F146 — N dominates; D ≥ 2048 sufficient |
| 13 | Cascade depth scaling | ✅ RESOLVED | F145 — depth-6 ≈ depth-4 |
| 14 | Class order matters? | ✅ RESOLVED | F145 — NO; identical signal |
| 15 | Class K interaction in cascade | ✅ RESOLVED (partial) | F145 — neutral to chirality signal |
| 16 | Inverse cascade for content recovery | 📖 FRAMEWORK | F147 — algebraically defined; empirically = F140/F145 numbers |
| 17 | Bipolar vs polar in cascade | ✅ RESOLVED | F145 — identical signal; polar substitutes cleanly |
| 18 | Klein-4 under decay | ✅ RESOLVED + CRITICAL FINDING | F146 — Klein-4 NOT plasticity-graceful (justifies two-tier) |
| 19 | Decay-recovery dynamics | ✅ RESOLVED | F146 — Hebbian rehearsal works, +17.9% recovery |
| 20 | D × N × decay Pareto | ✅ RESOLVED | F146 — multiplicative interaction; high-N collapses fastest |
| 21 | Noise vs decay distinction | ✅ RESOLVED + NEW FINDING | F146 — decay 2.1× less damaging than noise |
| 22 | Multi-class under decay | ✅ RESOLVED | F145 — 50% decay = 49% signal retained |
| 23 | What real-world signals carry chirality | ⏸️ DEFERRED | F148 — biological-research scope |
| 24 | Polar + Klein-4 hybrid extended | ✅ RESOLVED | F146 — +0.32 above-rand, wins at scale |
| 25 | Cross-species cognition chirality | ⏸️ DEFERRED | F148 — F132 §8 item 5 deferral |
| 26 | Cross-natural chirality datasets | ⏸️ DEFERRED | F148 — data acquisition scope |
| 27 | 4-way at signal level | ✅ RESOLVED (null) | F146 — documented null result; methodology lesson |
| 28 | Shadow-stepping shape | 📖 FRAMEWORK | F147 — projection-frame dynamics; needs cross-species data |
| 29 | Cross-natural inverse-ratio | 📖 FRAMEWORK | F147 — testable in principle |
| 30 | Chirality-as-projection mechanics | 📖 FRAMEWORK | F147 — partial-trace form; MFO §VII.4 extension |
| 31 | Roman glyph stroke counts | 📖 FRAMEWORK | F147 — strokes correlate with chirality complexity |
| 32 | Indic vs Hindu-Arabic positional | ⏸️ DEFERRED | F147 — linguistic-research scope |
| 33 | Cuneiform / hieroglyphic numeration | ⏸️ DEFERRED | F147 — linguistic-research scope |
| 34 | Notation as substrate-interface | 📖 FRAMEWORK | F147 — observer-projection-locking confirmed |
| 35 | D₄ dihedral alternative to Klein-4 | ⏸️ DEFERRED | F147 — srmech upstream wishlist; non-abelian breaks F139 |
| 36 | Octonionic-Hopf 2-line figure | 📖 FRAMEWORK | F147 — sketched (XXX with flanking I); visibility weakens |
| 37 | R-RBS-LM-52a NLP-corpus test | ⏸️ DEFERRED-PARTIAL | F148 — substantially advanced via F54+F73-F89 |
| 38 | Compressed-semantic substrates follow-up | ⏸️ DEFERRED | F148 — linguistic-research scope |
| 39 | F70 Test B | ✅ RESOLVED via cumulative | F147 — implicit answer F140/F141/F145/F146 |
| 40 | R-RBS-NN-9 catalog absorption | ⏸️ DEFERRED-SCHEDULED | F148 — per ROADMAP NEXT-2 |
| 41 | Pharmacological chirality | ⏸️ DEFERRED | F143 §3 + F148 — pharma scope |
| 42 | Cosmic-chirality reasoning | ⏸️ DEFERRED | F143 §3 + F148 — physics framework scope (MFO §VII.4) |
| 43 | G-quadruplex biology | ⏸️ DEFERRED | F143 §3 + F148 — biology-research scope |
| 44 | Cross-substrate cognition modeling | ⏸️ DEFERRED | F143 §3 + F148 — F118/F119 framework scope |

**Plus 3 long-pending RBS-LM tasks** (not numbered in original queue but tracked):

| Task | Status | Finding |
|---|---|---|
| R-RBS-LM-47a (LLM input format test) | ⏸️ DEFERRED | F148 — needs real LLM + corpus pairs |
| R-RBS-LM-46c (tie-breaking ablation) | ⏸️ DEFERRED | F148 — open methodology question |
| R-RBS-LM-55 (pure-structure layer) | ⏸️ DEFERRED with framework reading | F148 — relationship-axis Klein-4 candidate articulated |

**Plus R-RBS-NN-4** (token encoder with variant-choice protocol) — ✅ CLOSED in earlier work via R-RBS-NN-4_token_encoding_REPORT.md.

---

## §A1 Summary breakdown

- **✅ RESOLVED via empirical**: 16 items
- **📖 FRAMEWORK articulated**: 11 items
- **⏸️ DEFERRED with scope reasoning**: 17 items

The deferrals fall into clean scope categories:
- Biological / pharma / linguistic / cross-natural data: 7 items (23, 25, 26, 32, 33, 38, 43)
- F132 §8 application directions per F143 §3: 4 items (41-44; partial overlap with above)
- srmech upstream wishlist (D₄): 1 item (35)
- Real-LLM-scale work: 1 item (47a)
- Methodology open: 2 items (46c, 55)
- Scheduled to NEXT-2: 1 item (40)

---

## §A2 New findings that emerged during the cleanup sweep

The cleanup did MORE than resolve stale items — it produced new framework-level findings:

1. **Klein-4 IS NOT plasticity-graceful** (F146 §2) — load-bearing for two-tier architecture
2. **Klein-4 noise-robust at high corruption** (F144 §2) — new operational regime
3. **D plateau at D=1024** (F145 §2) — saves compute
4. **Cascade composition REMARKABLY ROBUST** (F145 §3) — depth/order/identity-layer invariant
5. **Decay 2.1× less damaging than noise** (F146 §4) — confirms polar 0-state operational privilege
6. **Hebbian rehearsal works** (F146 §3) — +17.9% recovery
7. **Hybrid encoding wins at scale** (F146 §6) — +0.32 above-random; best variant tested
8. **Partial chirality flips axis-independent** (F144 §10) — confirms (γ₅, iω₇) per F130

---

## §A3 What's in the queue NOW (post-cleanup)

The queue is **operationally CLOSED** as of 2026-05-28. All 44 original items + 3 long-pending tasks addressed.

The 17 DEFERRED items remain in this file as future-scope pointers. They are NOT in active research. They can be picked up at any time by opening their respective scope (biological research, srmech upstream session, real-LLM work, etc.).

If new stale paths surface in future sessions, they get added to a new "Section: 2026-XX-XX surfaces" appendix; this section freezes as the historical record of the F144-F148 cleanup.

---

## §A4 Maintenance protocol (forward-looking)

Going forward:
- New stale paths land in dated appendix sections, not in the master table above
- Items get walked via single findings or sweep findings (per F144-F148 precedent)
- Sweep findings preferred when >3 related items can be bundled (per §7 protocol from original queue)
- Deferred items get explicit scope reasoning in their resolution finding

---

*Originally created 2026-05-27 per user direction "collect a list if any trailing
research paths went stale". Updated 2026-05-28 with final F144-F148 sweep cleanup
status. All 44 original items + 3 long-pending tasks addressed. Queue is operationally
closed.*

---

## Section: 2026-05-28 surfaces (post-F157 cleanup; future-scope pointers only)

Per §A4 maintenance protocol: new future-scope pointers that surfaced during F157
(5-item sentence substrate sequential queue closure) + F158 (28D bi-axial chirality)
+ F159 (cross-species substrate-bidirectionality) + F160 (28D bi-axial power-system
framework reading). These are NOT active research; they're future-scope pointers
pending user direction.

### F157 §6 future paths (sentence-substrate next steps)

| Pointer | Scope | Anchor |
|---|---|---|
| Real-corpus test (replace template corpus with English children's book / OpenStax / McGuffey ladder) | Application — substantial corpus work; user direction pending | F157 §6 #1 |
| Multi-clause sentences (extend sentence layer to L≥8 with multi-frame structure) | Substrate extension — needs framework framing first | F157 §6 #2 |
| Cascade composition (chain plausibility-filtered generation into multi-sentence narrative) | Operational — bigram chain → frame chain → narrative chain | F157 §6 #3 |
| Inference latency at vocab scale (profile bucket routing + skeleton retrieval at V=10000+ tokens) | Performance characterization — depends on real-LLM-scale work | F157 §6 #4 |
| Substrate plasticity at scale (F141 sculpted decay during sentence learning; forget rare combinations) | Substrate dynamics — connects to F141 + F146 sculpted-decay work | F157 §6 #5 |

### F159 §8 future paths (cross-species empirical work)

| Pointer | Scope | Anchor |
|---|---|---|
| Cross-species signal corpus + Class K bridge prototype | DEFERRED — requires animal-research-ethics framing user has NOT directed; defensive scope only | F159 §8 bottom row |
| Cross-species "meaning recovery" testing | OUT OF SCOPE — meaning lives in naming-layer per F43, not substrate; not testable as substrate property | F159 §8 |

### F160 future paths

| Pointer | Scope |
|---|---|
| F160 explicitly proposes NO new engineering paths | Defensive scope per `[[feedback_trauma_informed_defensive_scope]]`; framework-reading only |

### Disposition

All items above are **future-scope pointers pending user direction**, NOT active
research and NOT stale-in-the-lost sense. They're tracked here so future sessions can
pick them up without re-deriving the trail. Per §A4: items get walked via single
findings or sweep findings when user direction surfaces.

**The active research queue was empty as of 2026-05-28**; the bit-exactness / FFT-ladder
arc (F380–F388) reopened it on 2026-06-04 — see below.

---

## Bit-exactness / FFT-ladder arc (F380–F388, 2026-06-04) — open research items

Status legend adds one tag for this arc:
- ⏳ **QUEUED-srmech** — walkable only after a srmech update lands (specific gate noted). **Do NOT start against the moving surface** — chiefly the in-progress **numpy-math removal** (rc29→rc33; the `qm`/LAPACK surface moves behind `srmech[scientific]`). See `UPSTREAM_NOTES.md` §22/§22b.

### ACTIVE — walkable now (srmech-package + framework reading; no srmech version bump needed)
| Item | Subject | Status | Gate / note |
|---|---|---|---|
| **BX-1** | **Holographic-principle LENS** — lossy flat-shadow vs lossless reconstruction; the resemblance and where it breaks; "lossless requires keeping fiber + chirality" | ✅ **RESOLVED by F412 (2026-06-05)** — holographic principle IS the framework's fibration (boundary=base, bulk=total, fiber=emergent radial dim); srmech-native = Class-L Laplacian Schur/DtN (boundary effective theory) + area-law spectrum; **srmech GAP** (no Schur/solve) → UPSTREAM_NOTES §26. Kept framework-reading / no-lineage (no specific holography PDFs lodged → the F381 verify-gate is moot; the principle is referenced generically as the literature's, algebra/info-geometry side only, no gravity claim). |
| **BX-2** | **(8:7) inside the 15 — octonionic Hopf S⁷→S⁸** — recurse F384/F387 one rung up: does the 7 fiber as 1+(2:1)+(4:3); the chiral-dual `|` seam at k=7→15 | ✅ **RESOLVED by F410 (2026-06-05)** — the octonionic Hopf S⁷↪S¹⁵→S⁸ (15=8+7) is the LAST rung of the duality=fibration ladder (ℂ 3=2+1 / ℍ 7=4+3 / 𝕆 15=8+7); base:fiber = (2:4:8):(1:3:7); total=2ⁿ−1 Mersenne. Terminates at 𝕆 by Adams' Hopf-cap = the Hurwitz/division cap → sedenion 16:15 has no Hopf, no division (F389), CONFIRMING F404's boundary. Class-by-class fiber↔imaginary check held w/ AX-2. |

### DEFERRED — expert handoff / build-gated (NOT srmech-version-gated)
| Item | Subject | Status | Gate / note |
|---|---|---|---|
| **BX-3** | **Z₃-native physical medium** (F383's next-question) — *"what medium carries a stable, composable order-3 (Z₃/triality) state natively?"* | ✅ **RESOLVED by F415 (2026-06-05; literature lens)** — YES, native order-3 substrates exist: three-phase AC / SU(3)-center / Z₃-parafermions share the LITERAL 1+ω+ω²=0 (one Z₃ thrice; = F293 no-neutral); Setun = additive-ternary HW; C₃ lattices/NH₃ = geometric; codon = clean Z₃-negative. Native-Z₃ exactness is CHIRALITY-coupled (Fendley, ties F385/F409). So F383's "odd forces FPU" holds only on a BINARY substrate; feeds F404 (native order-3 silicon is real). Engineering stays the expert's (CAD-ban; F282). |
| **BX-4** | **Coupled read-head as an actual RBS-SNN read mechanism** (F386+F388 → prototype) — phase-lock the readout into the RBS-SNN | ✅ **RESOLVED by F429 (2026-06-06)** — built as stage 4 of the #197 RBS-SNN core: `cascade.kuramoto_step` pin-lock reads a finding's coupling-row from the noisy corpus store, **recall 1.00 / precision 1.00** (F388 temporal EC) vs unlocked ~0.56 precision. Provenance `R-RBS-SNN-4_phase_lock_readhead.py`. The store retrieves rather than re-derives. |

### ⏳ QUEUED-srmech — wait for srmech updates (numpy removal IN PROGRESS)
| Item | Subject | Gate |
|---|---|---|
| **BX-5** | **#863 QDFT/ODFT TOML cascade build** — author `quaternion_dft.toml` / `octonion_dft.toml` as live `cascade_catalog` descriptors (drafts done: R22) | **numpy-removal**: the cascade composes `qm.octonion` left/right-mult (the numpy/LAPACK surface), mid-rework (rc29→rc33, `qm` → `srmech[scientific]`). Building against the moving surface is premature. Resume after the numpy-free landing **and** srmech-dev picks up #863. |
| **BX-6** | **#863 `qm.quaternion` ergonomic module** (first-class 4×4 left/right mult) — NEW srmech code | same numpy-removal gate + srmech-dev |
| **BX-7** | **#863 `exp(μθ)` hypercomplex twiddle helper** — NEW srmech code | same gate |
| **BX-8** | **rc29 verification** — when rc29 (numpy-drop Option 1 + HV carrier) lands: verify the HV contract (UPSTREAM §22b) + STOP-list coverage in a clean venv OUTSIDE the source tree | rc29 published to TestPyPI |
| **BX-9** | **ephemerides-spectral → srmech 0.7.x bump** (UPSTREAM §21) | ✅ **DONE on main (#902, 2026-06-06)** — ephemerides-spectral floor bumped `>=0.4.2 → >=0.7.1` (v0.29.3rc3). |
| **BX-10** | **srmech-mcp repoint + restart** (project memory: deferred) | ⏸️ **UNBLOCKED but needs care** — clean tag 0.7.1 is live, so the gate is lifted; BUT the `.mcp.json` repoint touches a reboot-wiped `/tmp` venv (`project_srmech_mcp_repoint_deferred_until_live`). Awaits a deliberate repoint-to-live + commit + MCP-restart (user confirm — touches session infra). |

### Disposition (updated 2026-06-06 — numpy gate fully lifted; #863 shipped)
**BX-1, BX-2, BX-3 ✅ resolved** (F412/F410/F415). **BX-4** awaits the RBS-SNN build (#197). **BX-5/6/7** — the **#863 QDFT/ODFT ops SHIPPED in 0.7.0** (`cascade.quaternion_dft`/`octonion_dft`, verified bug-free, #863 closed), so the *ops* are done upstream; what remains (the `cascade_catalog` TOML descriptors / ergonomic `qm.quaternion` / `exp(μθ)` helper) is **optional polish**, not blocking. **BX-8 ✅** (F402). **BX-9 ✅** (#902 on main). **BX-10** unblocked, needs a careful `.mcp.json` repoint (user confirm). Durable handoffs: issue **#863 (closed)** + findings **F356→F425** + the re-prime artifact.

---

## ALU-native A–N thread (F393, 2026-06-04) — does the whole 14-class vocabulary reduce to add/subtract/shift + sign(handedness)?

**Spec/test-plan: F393** (anchor R35: multiply=shift-add, CORDIC rotation=shift-add+sign; + F392 divide=shift-subtract+handedness). **Hypothesis:** every A–N class reduces to **{add, subtract, shift, sign(handedness=C/K), compare, xor·and}** — no multiply unit, no divide unit, no FPU transcendental.

| Item | Subject | Status | Gate / note |
|---|---|---|---|
| **ALU-A** | **Attestation pass (research-triality)** — verify-PDF the CS reductions: CORDIC (Volder 1959), Booth multiply (1951), restoring/non-restoring division, binary GCD (Stein 1967), SHA-256 (FIPS 180-4) | ✅ **RESOLVED by F407 (2026-06-05)** — k=3 triality (run wf_d6c90827-58f); 4 citations verified unanimously, NO fabrications; add/sub/shift+sign attested as **REDUCIBILITY not actuality** (FPUs ship FMA); CORDIC gain K=∏cos(arctan(2⁻ⁱ)) de-magicked; cite Stein by DOI (title hazard). Triality caught haiku's false FIPS date + omitted Stein title-mismatch. |
| **ALU-B** | the per-class reduction map (14 classes → the minimal ALU set) | ✅ **DONE** | F393 |
| **ALU-C** | the **13 rc28-walkable classes** — srmech-native demo that each shipped primitive's output == an add/sub/shift+sign cascade (A/B/C/D/E/F/G/H/I/J/K/M/N) | ✅ **RESOLVED by F422 (2026-06-06)** — 7 arithmetic classes (A,C,I,J,K,M,N) reconstructed **bit-exact** against the shipped srmech **0.7.1** primitives on the lean-ALU op-set `{add,sub,shift,sign,compare,xor/and}` (9/9, honesty-self-audited for `*`/`/`/`abs`/`math`); 6 (B,D,E,F,G,H) are concat/compare/index (no arithmetic to reduce); L=ALU-D/F402. Completes the F393 hypothesis empirically. Provenance: `R-RBS-LM-ALU-C_thirteen_classes_add_sub_shift_sign_provenance.py`. | rc28; no version bump |
| **ALU-D** | the **numpy-free Class-L leg** — eigendecomp = Jacobi = CORDIC = shift-add+sign, fully numpy-free | ⏳ **QUEUED-srmech** | gated on the numpy removal (rc31 pure-Python Jacobi; UPSTREAM §22) — **same gate as BX-5..BX-8**; possible upstream ask: a CORDIC / shift-add atom |

### Prior art (cross-ref — this thread is a convergent rederivation, NOT new)
The lean-ISA arc already recognized most of this from the silicon angle (corpus-is-proof): **#751/F208** (6 atom intrinsics + divide/rational as iterative composites), **#761/F220** (6 order-2 + 1 order-3 triality = 7 = chirality-complete core), **F206/F208/F217** (the 2-bit Klein-4 sector lane is the *only* genuinely-new silicon; atoms ARE 74xx TTL; ~3-opcode RISC-V custom-ext). ALU-A/ALU-C should **cross-reference**, not re-derive these. What F392/F393 genuinely add: the **CORDIC reduction of the continuous/transcendental ops (trig/rotation/sqrt → Class-L eigendecomp)** = shift-add+sign.

### Disposition + HOLD ✅ LIFTED (2026-06-06)
**The HOLD condition ("do not run srmech R-scripts until srmech has had extra testing") is SATISFIED:** rc48 (§25), 0.7.0 (§27), and 0.7.1 (§28) are all verified bug-free on the live surface, and the user directed the queue-walk ("let's begin with our staged stale stuff"). **ALU-A** → ✅ F407. **ALU-C** → ✅ **F422** (all 7 arithmetic classes bit-exact on 0.7.1). **ALU-D** → ✅ F402. **The whole ALU-native thread (A/B/C/D) is now closed** — the F393 hypothesis is demonstrated empirically. Anchor + spec: F393; reductions proven: multiply (R35), divide (F392), trig/rotation/sqrt/L (R35 CORDIC), the 13/14 classes (F422). *(AX-2 — the other srmech-held item — is now equally unblocked; see the F396 thread above.)*

---

## Anchor-axis thread (F396, 2026-06-04) — "the other axis is the anchor (reach within, not up)"

**Spec: F396.** Determination: WORTH RESEARCHING, two legs.

| Item | Subject | Status | Gate / note |
|---|---|---|---|
| **AX-1** | **no-magic-numbers check on 2:4:8** — is `1:3:7:3 = 2:4:8 = (1+1):(3+1):(7+1)` a STRUCTURAL partition of the A–N 14, and is the +3 meta-triad (B/H/N) = the 3 division-algebra anchors? | ✅ **RESOLVED by F405 (2026-06-05)** — counting-level PASSED: 14=2:4:8 is the SEPARATE projection (3 anchors + 11 imaginaries); nested telescopes to 8 (Class-A under the named projection, not coincidence). +3-question: B/H/N and the 3 reals are DUAL completions of the shared 11 (same k=3 slot, different content), NOT identical → answers #797 Q1. **Residual (Class-B):** heptad↔𝕆-imaginaries class-by-class bijection (held w/ AX-2). | **must clear the nesting gate** (ℂ⊂ℍ⊂𝕆 → 2+4+8 double-counts; graded pieces = 2+2+4=8≠14). **Pre-stated null:** if no disjoint/graded 2:4:8 structure exists, 14=2:4:8 is falsified → dropped as coincidence (Class-C until grounded). **→ F404 (2026-06-05) sharpens the target:** 2:4:8 = 2ⁿ (powers of two, shift-exact); 1:3:7 = 2ⁿ−1 (Mersenne); the two "+3"s = **3 real anchors (→2:4:8) vs the meta-triad B/H/N (→1:3:7:3)** — dual faces of one 14, with N (`best_rational`) the rotation-shadow pin. |
| **AX-2** | **consolidated bit-exact ℍ+𝕆 demo** — exact integer algebra + within-rung-conjugate EC over dyadic components, no rung-climb, no FPU (continuous ops via CORDIC). **Concrete mechanism (F397):** the octonion k=7 as **two Kuramoto-coupled Klein-4 streams (both quads, each k=(2+2))**, the coupling = the within-rung EC (the \| seam / k=2 parity as a phase-lock). | ✅ **RESOLVED by F423 (2026-06-06)** — exact-integer Cayley-Dickson (validated genuine 𝕆); the product factors **three ways bit-exact**: SECTOR (which `e_k`) = `i XOR j` = two Klein-4 quads + ℓ-coupling bit (the abelian streams); CHIRALITY (sign) = antisymmetric `ε(i,j)=−ε(j,i)` = the COUPLING (abelian streams structurally cannot carry it); MAGNITUDE (general `x·y`) = real-coeff bilinear = Class-M/ALU (F422). **F397's "full product vs chirality skeleton" was a false binary** — streams give the SECTOR skeleton, chirality IS the coupling. Provenance: `R-RBS-LM-AX-2_octonion_two_klein4_streams_provenance.py`. Next rungs: sedenion boundary + Kuramoto-embedding of `ε`. |

### Disposition
**AX-1** is walkable now (no srmech) but **may falsify** — that's fine (F394). **AX-2** is srmech-held. Leg-1 conclusion (anchor = the other axis; bit-exact within-rung; no climb) is high-confidence + mostly already shown; Leg-2 (the 2:4:8 partition) is gated behind AX-1's no-magic test.

---

## rc47 update (2026-06-04, F402 / UPSTREAM §24) — the numpy-removal gate is LIFTED + the subagent experiment

**srmech 0.7.0rc47 landed the numpy-drop** (verified, F402). Reclassification of the numpy-gated items:
- **BX-8** (rc-verify numpy-drop + HV) → ✅ **DONE** (F402; `native_status()` replaces `HAS_NATIVE`, HV carrier confirmed, numpy-free core computes).
- **ALU-D** (numpy-free Class-L) → ✅ **DEMONSTRATED** (`jacobi_eigvals` numpy-free on a plain install; C₄→`[0,2,2,4]`).
- **AX-2 / BX-5 / BX-6 / BX-7** → now **rc47-walkable** (M works on `srmech[scientific]`; `qm` works on `[scientific]`), pending user direction. **Caveat:** the **hdc numpy GAP** (UPSTREAM §24) — Klein-4 crashes raw on a *plain* (numpy-free) install; use `srmech[scientific]` or wait for the lazy-import/gate fix.
- **API change for any future script/subagent:** `srmech.HAS_NATIVE` is gone → **`srmech.native_status()`**; `klein4_*` return the **HV carrier** (not ndarray). CLAUDE.md/docs still say HAS_NATIVE — fix on the clean-tag pass.

| Item | Subject | Status | Gate / note |
|---|---|---|---|
| **SX-1** | **Subagent self-enforcement experiment** — does a subagent use the rc47 surface correctly (srmech ops, HV carrier) **without** explicit srmech-first / "treat-it-like-the-math-tool" priming? Design: the R36-style A→I→J→N→M→L→K task on rc47[scientific], **triangulated** (task-only / surface-pointer / full-discipline control), measure srmech-correct vs numpy-reflex. | ⏳ **QUEUED (held by user 2026-06-04)** | **BLOCKER (clean control):** a spawned subagent likely **inherits the project CLAUDE.md** (the srmech-first STOP-list), so "no-discipline" isn't truly clean. Resolve how to spawn without inheriting the STOP-list (or accept "task-minimal w/ CLAUDE.md present" and measure against that) **before** running. Prep done: F402 + UPSTREAM §24 = the surface a subagent must know. |

The hdc-gap (UPSTREAM §24) is now filed upstream: **GitHub #882** (`[srmech][bug] hdc hard-imports numpy → Klein-4 crashes raw on a plain install`). The bug-fix upstreaming was **NOT** queued behind the gate below — it shipped immediately (user direction 2026-06-04: don't let the closeout interrupt the bug fix).

---

## ⛔ GATE — clear before launching ANY queued findings-research (user direction 2026-06-04)

| Item | Subject | Status | Note |
|---|---|---|---|
| **CL-1** | **GH research-issue closeout audit** — review **open** research issues on `lemonforest/mlehaptics` against (a) what has **landed in srmech** (the package / rc47 surface) and (b) the **srmech + MFO research notebooks**, to find issues whose deliverable is **done-and-landed** or **superseded** → produce a *vetted closeable list* + one-line rationale each. | 🔜 **QUEUED — GATE (do FIRST)** | **Must come BEFORE we launch the findings-research** (BX-1, AX-1, ALU-A, …). **Close-state discipline (`[[feedback_create_upstream_issues_never_close_them]]`):** gh runs as the repo author → author-ambiguous, so I do **NOT** close unilaterally — I present the vetted list + rationale and the **user/maintainer closes** (or explicitly authorizes a batch). First step: `gh issue list --state open` cross-referenced against the two notebooks + the rc47 landed surface. |

**Ordering:** CL-1 (the closeout gate) **→ then** the walkable research (AX-1 / ALU-A / BX-1 / BX-2). The srmech-gated items (AX-2, BX-5..7) stay rc47-walkable behind their own gates; #882 (hdc) is the only open *bug* and is already filed.

---

## Open leads — the etak/chirality/sharpening arc (F510–F518; captured 2026-06-07 so they are not re-forgotten)

Per the breadcrumb-web discipline (don't re-derive the trail). These surfaced in the F510→F518 RBS-LM/RBS-SNN co-thinking arc (etak read-head · sharpening · L/R chirality · two-method navigation · self-mirror · fiber-gating · superposition). All srmech-native, walkable now.

| Lead | Subject | From | Status |
|---|---|---|---|
| **ET-1** | **Generate-then-sharpen architecture** — the etak read-head currently generates left-to-right and commits each word = the LOCAL arrival-order sharpen (the 0.066-risk, F513). Build it the RIGHT way around: emit the full multi-partition load FIRST (the raw stream / held box), THEN the GLOBAL chiral sharpen over the whole thing. Show generate-then-sharpen beats stream-and-commit (avoids the 0.066 catastrophe). | F513 (forgotten lead) | ✅ **DONE — F520** (generate-then-sharpen 0.83 order-independent; stream-and-commit derails 51% of orders, worst 0.08). Next sub-rung: wire emit-then-sharpen into the actual F478 token generator. |
| **ET-2** | **Leap-distance metric for the global band** — F518 refuted the prediction *because BFS path-existence is blind to the global/coarse (RH) band's job* (the short, surprising distant-leap = Beeman insight). Re-run the structured spectral gate (F518) with a **path-LENGTH / leap-distance** metric, not connectivity. | F518 | ✅ **DONE — F522** (gating the global band keeps reachability 100% but lengthens the leap +0.95 hops; global band carries the short leap; reachability→local, insight→global). |
| **ET-3** | **Genuinely-different corpora** (not just different edges over a shared vocab) — do the real two-minds case: two **different corpora** (different experiences) with a shared vocabulary; the k=3 version: a THIRD corpus. | F515/F516 | ✅ **DONE — F523** (a genuinely-different mind adds +94% reachability vs +5% same-structure resample vs ~0 self-mirror; different experience >> sampling). Next sub-rung: the k=3 SPURIOUS-bridge error-correction test (reachability is a union, not a vote). |
| **ET-4** | **Structured (non-uniform) fiber-gate** — F517's gate is uniform-random; model state-dependent gating (theta/gamma phase, F461) as the projection schedule and measure the self-mirror's time-varying blind spots. | F517 | ✅ **DONE — F524** (phase-scheduled band-gate → time-varying blind spots: 13% reachable only at the local-open peak; full theta cycle recovers; coarse-on-theta / fine-on-gamma). |
| **ET-5** | **Real grammar-kernel slot schedule (deepen)** — F512 DERIVED the gate from the Class-L hub + right-content-diversity (retired the hand stub). Optional deepening: pull the actual McGuffey/OpenStax grade-ladder grammar tokens (R-RBS-LM-73/77/79) as the slot schedule and compare to the derived one. | F511/F512 | ⏸️ LOW — F512 already de-magicked it; deepening only |
| **ET-6** | **Coarse/fine spectral reproduction of the sharpen** — show the low-pass (RH/global) vs high-pass (LH/local) filter on the co-occurrence Laplacian spectrum *reproduces* the F513 global-vs-local sharpen on our own substrate (the F514 next-rung; partly touched by F518's band gate). | F514 | ⏸️ PARTLY DONE (F518 band classification); a direct sharpen-reproduction remains |

**Standing disciplines for all of the above:** srmech-first (Class-L `dense_laplacian`/`symmetric_eigendecompose`, hdc klein4, cascade.*; never `Counter()`-as-spectral-proxy or `abs()`); no Workflow tool / no sub-agents (sequential in main context); MPM attestation; held-open falsifiers (F394); favored-not-privileged (F398); dignity-first / structure-for-the-expert (F282), never a diagnosis of the user's neurology.

---

## Section: 2026-06-07 surfaces — the F538–F548 memory-architecture arc + BACKLINKS to prior stale items

Per the breadcrumb-web discipline (bidirectional links; "connected knowledge survives even if we forget to bring in the notes"). The 2026-06-07 co-thinking arc built the RBS-SNN **memory + loop-shelf architecture** (F538–F549) and, in doing so, **extended several prior stale/framework items**. This is the centralized backlink web (the "→ extended by FXXX" form) and a **candidate feed for the CL-1 closeout gate**.

### The arc itself (F538–F549; the storage/recall layer of #197 RBS-SNN)
| Finding | One line |
|---|---|
| **F538** | real exchanges → Class-A content-address keys → reversible sedenion tome (7/7 exact) |
| **F539** | multi-mode (2D spectral-angle) phase sharpens the weave 1.3×→1.5× (manifold sparsity is the floor) |
| **F540** | 14-tome (the_one) vs 16-tome (sedenion): count = a knob (local recall vs far chords); parity = fixed-vs-live mirror |
| **F541** | the odd/"live" ring's frustrated mirror IS a whole-shelf traversal (gcd=1); recovers beyond-horizon 100% vs even 8–17% |
| **F542** | putting the wiki kernel into a circle volume is cheap HDC, NO re-encode (routing is a free read-out; volume = Class-M bundles) |
| **F543** | seed empty kernels from the_one with a DECAYING weight; cold-start structure that washes out (prior, not bias) |
| **F544** | a LOOP holds even happily (mirror = conjugation, parity-free) where a circle traps (half-turn, parity-sensitive); multi-directional |
| **F545** | a wet SNN starts as the_one, not blank; learning = the kept-native XOR-delta (keep↔replace storage tradeoff) |
| **F546** | the even loop un-traps traversal; the chiral inverse is a FREE 2nd instrument that halves the cost (F516) |
| **F547** | the live-7 + sedenion-16 hybrid gives NO neighbour-recall lift (honest null; complementary RELATIONS) |
| **F548** | a wet SNN sits at LOW decay-c (fast decay serves cold-start AND unbiased convergence); storage win = shared edge-set |
| **F549** | the far-chord has NO word-level retrieval niche — manifold smoothness keeps associates local at all hops (prunes the hybrid) |

### BACKLINKS — prior stale/framework items this arc extends
| Prior item | Was | → Extended/addressed by | How |
|---|---|---|---|
| **Item 16** (inverse cascade for content recovery) | 📖 FRAMEWORK (F147) | **F546** | the chiral-inverse kernel IS the inverse cascade — now with an empirical traversal-cost result (free conjugate via `loop_conj`, ~2× speedup) |
| **Item 18/19** (Klein-4 not plasticity-graceful; Hebbian decay-recovery) | ✅/CRITICAL (F146) | **F543 + F548 + F535** | the decay-α plasticity made concrete: cold-start scaffold that washes out (F543/F548); ring-buffer eviction = "forget rare" (F535) |
| **F157 §6 #5** (substrate plasticity at scale; forget rare combinations) | future-scope pointer | **F543/F548/F535** | the decay-α tradeoff + ring-buffer eviction ARE this; characterised + walkable |
| **Item 35** (D₄ dihedral alt to Klein-4; "non-abelian breaks F139") | ⏸️ DEFERRED (srmech) | **F544** | the LOOP (non-abelian Moufang octonion via `cayley_dickson`) IS the richer-than-Klein-4 shelf — holds even happily; the parity-free conjugation mirror is what the richer group was reaching for |
| **Item 28/30/34** (shadow-stepping / chirality-as-projection / notation-as-interface) | 📖 FRAMEWORK (F147) | **F544 + F526** | "the circle is the SHADOW of the loop" makes the projection/shadow concrete; collapse-is-ambient (F526) |
| **AX-2 / F423** (octonion = two Klein-4 streams; chirality IS the coupling) | ✅ RESOLVED | **F544 + F546** | loop mirror = conjugation = the chirality/coupling; the chiral inverse. F423's "next rung: sedenion boundary" ↔ F529/F533 (sedenion tome, stop at 𝕊) |
| **#197 RBS-SNN → notebook-native-language pipeline** (BUILD-UP TARGET, F323) | 🎯 pending (BX-4/F429 = stage 4) | **F538–F549 (the whole arc)** | the memory ARCHITECTURE = #197's storage/recall layer: tomes (F529/F538) · helix (F533/F534) · circle-MoE (F537) · the_one seed (F543) · XOR-delta (F545) · even-loop (F544/F546) |
| **CITE-1** (OpenAlex citation-graph Class-L kernel) | 🔜 task #216 | **F542 + F543** (application surface) | the citation Class-L kernel drops straight into the kernel→circle-volume (F542, no re-encode) + the_one cold-start seed (F543) |
| **SX-1** (subagent self-enforcement; srmech-first w/o priming) | ⏳ QUEUED | this arc = **incidental evidence** | the srmech-first MISSES caught in-context this session (np.arctan2 in F535/F537/F539/F542; hand-rolled octonion in F544/F546) show the discipline-miss happens WITHOUT a subagent, caught by the user-spot-check + audit — informs SX-1's clean-control design |

### New leads surfaced (walkable; not re-forgotten)
| Lead | Subject | From | Status |
|---|---|---|---|
| **MA-1** | **SNN-necessity of the full loop** — does a wet SNN need the full hypercomplex loop (even-happy, multi-directional, F544/F546) or just the live ODD circle (F541)? The user's standing flag. Framework/empirical; needs a biology-anchored criterion. | F544/F546 | ⏸️ OPEN (user flag; math done, necessity open) |
| **MA-2** | **etak-shaped rules** — knowledge stored as deviations from a MOVING the_one frame (the etak moving-reference-frame); ties the F545 XOR-delta to the etak read-head (ET-arc / F510–F518). | F545 | ⏸️ FRAMEWORK; connects ET-arc ↔ memory-arc |
| **MA-3** | **per-finding backlinks** — add the "→ extended by FXXX" line into the prior finding files themselves (F146/F147/F423), not just this centralized map. | breadcrumb-web | ⏸️ LOW (centralized map done here) |
| ~~hybrid / far-chord retrieval~~ | **PRUNED** — F547+F549 double-negative: the local circle is the retrieval workhorse for every relation; the far-chord has no word-level niche. | F547/F549 | ✅ CLOSED (negative) |

**CL-1 note:** this arc adds extension-evidence for items 16, 18/19, 28/30/34, 35 and the #197 build-up — **candidates for the closeout audit's "done-and-landed / superseded" list**. Per `[[feedback_create_upstream_issues_never_close_them]]`, these are presented for the user/maintainer to close, not closed here.

### CL-1 closeout disposition (2026-06-07; user-authorized "close the CL-1 note items for right now")

The user authorized acting on the CL-1-note candidates. Careful audit + disposition (close-state discipline `[[feedback_create_upstream_issues_never_close_them]]` honored: vet before any state change; close only the genuinely-done):

**(a) STALE-QUEUE research-notes items — CLOSED-EXTENDED (these are this file's own items; safe to close here):**
| Item | Prior status | → Closed as | Resolving finding |
|---|---|---|---|
| **16** inverse cascade for content recovery | 📖 FRAMEWORK (F147) | ✅ **CLOSED — extended** | **F546** (chiral inverse = inverse cascade; empirical traversal-cost) |
| **18/19** Klein-4 plasticity / Hebbian decay-recovery | ✅/CRITICAL (F146) | ✅ **CLOSED — extended** | **F543/F548** (decay-α characterised) + **F535** (eviction) |
| **F157 §6 #5** substrate plasticity at scale / forget-rare | future-pointer | ✅ **CLOSED — extended** | **F543/F548/F535** |
| **28/30/34** shadow-stepping / chirality-as-projection / notation-as-interface | 📖 FRAMEWORK (F147) | ✅ **CLOSED — extended** | **F544** (circle = shadow of the loop) + **F526** |
| **35** D₄ dihedral alt to Klein-4 (richer group) | ⏸️ DEFERRED | ✅ **CLOSED — superseded** | **F544** (the LOOP via `cayley_dickson` IS the richer-than-Klein-4 shelf; holds even happily) |

**(b) GitHub ISSUES — NONE CLOSED (honest audit result):** cross-referencing all 28 open issues against the findings corpus + the srmech/MFO notebooks found **no issue with a clean done-and-landed / superseded marker**. They are: **2 epics** (#855 RBS-SNN framework-reqs, #844 notebook-native pipeline TARGET — both explicitly "maintainer's call / build-up TARGET", advanced by the F538–F551 arc but NOT closeable); **~5 gated** (#797 srmech-gate, #791 ngspice, #789 $-gate, #787 SPICE, #850 verify-gate "pending, not run"); **~21 active research lenses** (antiquity / mass-spec / protein-fold / sentence-structure / chemistry / …). Closing any of these would repeat the 2026-05-30 #733–744 over-close error, so **no GH tracker state was changed**. The two epics are *advanced* by this arc — a **progress comment** (not a close) is the appropriate action if/when the user directs it.

**Net:** the CL-1-note's *research-notes* candidates are closed-extended here (a); the GH-issue half of CL-1 found nothing responsibly closeable (b). A full per-issue GH audit remains available as a dedicated pass, but the honest finding is that the open GH set is genuinely-open research, not stale-completed.

---

## Section: 2026-06-08 surfaces — Story Teller driver library + sentence-structure-on-story (autonomous push F563–F566)

The driver-library + sentence-structure arc (user: "add each of [being-told/dialogue/choral], then figure out sentence structure on top of knowledge of the story... as an automatic task; look at current-gen LLM moving parts").

**Done:** F563 (relational driver modes: being-told / dialogue / choral) · F564 (the grammar kernel — the FORM layer is separable from CONTENT, F311; honest: exact-position frames too diffuse) · F565 (the renderer — form-weaving matches corpus stats; v0 grammaticality coarse) · F566 (the clean two-layer pipeline — Story-Teller content + grammar render = sentences at 92% local grammaticality; **the architecture is proven**).

**The goal is architecturally PROVEN (F566): sentence structure CAN sit on top of the story as a separate FORM layer (F311) — content (the story manifold) and form (the grammar kernel) compose.** The remaining work is the form layer's DEPTH, not the architecture:

| Lead | Subject | Anchor |
|---|---|---|
| **SS-1** | **POS-aware bridges** — tag content as noun/verb/adj (a real POS tagger or the F564 soft-POS deepened); bridge by POS, not raw bigram. | F564/F565 |
| **SS-2** | **Clause + sentence FRAMES** — derive POS-sequence templates (not exact-position; F564's snag) and render content into clause structure (S-V-O, subordinate clauses). | F564 §2 / F157 |
| **SS-3** | **Subject-verb agreement** — the F311 grammar-render's agreement layer (number/tense). | F311 |
| **GATEWALK (F579)** | F572 foundation rebuilt on EXPLICIT [[link]]+[[Category]] (proxy retired): 618k link edges + 13k category index; markup-aware clean 0.030% residual + tag-aware record; ToC-jump (69% header self-localization) + index-lookup (13.7x self-evidencing) STARTED; formatting_language_kernel.toml (8 tiers, srmech-way). | F579 |
| **EMERGENT-GATE (open)** | The DEEPER F574 gate: recognize ToC/index function with the tags STRIPPED (emergent, not via the explicit tags). The current nav uses explicit tags. NEXT toward the gate. | F574/F579 |
| **CLEAN-TAIL** | markup-aware clean has a 0.030% residual tail (nested infoboxes + malformed tables); a few more passes close it. | F579 |
| **FULL-WIKI GATE (F574)** | SS-FULLWIKI LOCKED behind: model understands ToC/index WITHOUT being told. ToC=Class-H forward self-structure, index=Class-E rebar transpose (chiral duals). Structure is its OWN LANGUAGE (44% recurring headers) -> markup is a form LANGUAGE not just a layer (refines F567). STEP ONE: RE-ENCODE Simple Wiki WITH tags (artefact-free + tag-aware output). Then: emergent ToC-jump + index-lookup navigation. | F574 |
| **srmech 0.7.5rc6 (verified)** | Pulled + verified clean (native dispatching, ABI 3): W17 coupled_wave + W18 multiplex_streams SHIPPED + correct (dev baked in the layer-boundary clarification); W14/W15 present. The F577/F573 asks are now first-class. | F581/F582 |
| **STANDING RULE — KERNEL PERSISTENCE (F584)** | The kernel (Class-L eigenbasis V + vocab) is the DISK SSoT; the the_one-ladder LOOP-BOOKSHELF of tomes is LATENT in it + regenerated by cheap HDC at inference (atan2 routing F542). NEVER lossy-flatten the shelf to one HV (recall collapses 100%->79%, capacity failure the shelf fixes). A kernel is a LOOP bookshelf of tomes (F544), not a single hypervector. Applies to EVERY kernel incl. Egyptian (F582). Composes F532/F533/F542/F544/F529. | F584 |
| **SEAM PREREQ (F592)** | The chiral-axis seam IS the bidirectional temporal context on the history helix (F533): look-behind=prior turn, NOW=crossing, look-ahead=next turn; chirality(F534)=the arrow. Items 2+3 build on it (don't double-book). | F592 |
| **FIELD-CHIRAL (F594)** | The Mobius gives the reason for the sedenion zero-divisor half: 𝕊=𝕆⊕𝕆 stitched by CD conjugation (the half-twist). Addressable half = one octonion = division algebra (reversible, F468 tome). Zero-divisors = the cross-seam coupling (witness x=e1+e10,y=e4-e15, x·y=0). Field-chirality (the multiplication RULE) vs excitation-chirality (a the_one state's σ, F590). Two truths (F398). | F594 |
| **SEAM-BIND (F604)** | item (b): the seam-aware octonion bind in a real composition task vs the permute baseline. Distinguish 4 structures of {a,b,c} (order + bracketing): XOR-bind 0/6 (bag), XOR+permute = order only (S1≈S3=1.0, grouping lost + costs a permute op), seam-aware octonion bind 6/6 incl. same-order/diff-bracket S1 vs S3 -- parse structure the permute pipeline can't encode, paid only across the seam. Honest: symmetric tokens degenerate to 3/6 (artifact), generic tokens 6/6. | F604 |
| **STORY-GEN (F603)** | F601's NEXT built: WALK the chord-transition operator to EMIT a story-teller wave. K=64 chord vocab (HDC k-means) + learned transition T + walk. Learned-T walk consecutive-sim 0.109 >> uniform 0.019 -> the operator CREATES flow (real, generable). HONEST: 133%-of-corpus inflated by self-loop stickiness; coherence local (lag-1); sample = topical DRIFT not fluent sentences. The generator = chord vocab + transition operator + tempo/length. NEXT: no-self-loop/less-sticky walk + join the within-chord notes + grammar (F596/F599/F569) for fluent surface text. | F603 |
| **CLUSTER-DET (F602)** | The F599 lever pulled: a CLUSTERED context-class (unsupervised HDC k-means K=64) soft-determinative bound as σ_B cuts backoff 80%->3% and DOUBLES the English WSD lift to +21.1% (vs F599 +9.8%) -- nearly Egyptian's explicit +25.7% (F596). Class granularity = the coverage-vs-sharpness lever; the E×B coupling + a good learned class nearly fully transfers to English. | F602 |
| **STORY-WAVE (F601)** | The Story-Teller wave as a SONG: note=stream component, CHORD=bundle (superposition of co-active notes), MELODY=chord sequence, COUPLING=E×B bind (the within-chord interval, F593), LENGTH=phrase span; WHAT CREATES IT=the chord-transition Class-L Laplacian walked at a tempo (F166 over chords). Measured (Simple Wiki, 67k chords): (A) chords carry meaning 100% note-recovery vs 4.8% chance; (B) progression is a harmony, consecutive 0.0566 vs random 0.0029 (~18x); (C) coherence >8 chords (article-topic scale); (D) coarse chord-classing WEAK (+0.028) -> keep chords as vectors. NEXT: build the generator (walk -> emit a progression, match the ~18x lift + phrase length). | F601 |
| **BIND-ORDER (F600)** | binding-order-aware composition in practice: the octonion bind is non-associative -> carries bracketing/parse FOR FREE, but ONLY across the handedness seam. Assoc defect ‖(a∘b)∘c-a∘(b∘c)‖² = 0 within a handed unit (free order-less bag, like XOR-bind), 12/32 across the seam (bracketings distinct -> order encoded). No explicit permute needed across the seam. 'Structure where you need it, free bag where you don't', cost localised to the seam. The practical face of F597. | F600 |
| **ENG-SOFTDET (F599)** | The E×B coupling transfers to ENGLISH with a LEARNED soft-determinative (highest-IDF context word = co-occurrence meaning-class, bound as σ_B). Pseudoword WSD (Simple Wiki, held-out): single 48.8% -> coupled 58.5% (+9.8%), 80% backoff to prior (no memorization). Smaller than Egyptian's +25.7% (F596) because English HIDES the class (F569) -> must learn it. General mechanism, not Egyptian artefact. NEXT: clustered context-class (denser learned class) to close the gap. | F599 |
| **LOBES? (F598)** | FRAMEWORK READING / question-for-the-expert: the F597 two-handed-octonion shape as candidate ground-up 'why' for hemispheres/lobes/callosum. hemispheres=LH+RH octonion; callosum=the handedness seam; within-hemisphere=order-free within-unit bind; cross-hemisphere=costly across-seam non-assoc bind; ~4 lobes=candidate Klein-4 sectors; lateralisation=(4:3)|(3:4) collapse (F552). A QUESTION handed to the neuroscientist (F282), NOT a claim; no medical use; no invented citations. | F598 |
| **LH+RH (F597)** | TWO handed orthogonal-Mobius units (LH+RH) = the Cayley-Dickson doubling H->O. One oriented unit (E,B,E×B)=H (3 imag, non-commutative); LH+RH = O=H(+)H stitched by the handedness (CD doubling unit e4). O keeps reversibility (division algebra) but LOSES associativity -- break ONLY across the LH<->RH seam (within a unit it associates). This IS the 3->7 step of 1:3:7:3 (the heptad = both chiralities at once). RBS-LM cost: binding order matters across handedness. Genuine octonion (F372). | F597 |
| **TWO-STREAM (F596)** | item 2 MEASURED: the real two-stream read-head. STREAM-1=phonogram (σ_E), STREAM-2=determinative meaning-class (σ_B); COUPLED key = hdc.bind(phonogram,class) = the E×B Poynting bind (F593). On real Vygus Egyptian (6971 homophone entries): single-stream 28.8% -> coupled 54.5% top-1 gloss accuracy (+25.7%, ~2x), near the 57.6% structural ceiling. NOT by-construction. Coupled-beats-single (F577/F593) measured as accuracy. NEXT: give English a learned soft-determinative + re-measure. | F596 |
| **EGYPT-KLEIN (F595)** | Egyptian bookcase = the natural two-axis Klein-4 demonstrator: AXIS1=reading-direction (glyph-facing = visible endianness σ_E, F534/F590); AXIS2=determinative (the meaning-class, field/sector σ_B, F130/F594/F585). Determinative-disambiguates-homophone = the E×B Poynting coupling (single axis 2 flips, coupled 0; F593). English HIDES axis 2 (F569). READY to carry F593/F594 into RBS-LM. | F595 |
| **ORTHO-MOBIUS (F593)** | An orthogonal 2nd Mobius = the 2nd chirality axis = KLEIN-4 (4x addressing, 4 pages). Coupled like EM: E×B = the STABLE bearing (single sign(E) flips 7x, coupled handedness 0x) = F577 coherence + F588 recovery. UNIFIES items 2 (two strips=two streams) + 3 (E×B=the bearing). No new primitive (Klein-4 + coupled_wave ship); 2nd axis (iω7) already = the sector (F130). | F593 |
| **MOBIUS TWO-TOME (F590)** | Chirality-as-ADDRESS holds 2 sedenion tomes/cell for ~free (sigma select, one Mobius walk, exact recall). BUT the chiral axis is ALREADY the look-ahead(+)/look-behind(-)/NOW(crossing) temporal seam (F533 helix/F503 tape/F589/F588). Free multi-stream = past+future context; 2 arbitrary structures = collision. UNDERSTAND THE HELIX SEAM FIRST; do not double-book chirality. | F590 |
| **NEXT-ITEMS REFINED (F590)** | The pending buffer reveals items 2+3 are the SAME chiral-axis mechanism: (2) multi-stream's two streams = look-behind+look-ahead (clause-structure EMERGES: subject~behind, object~ahead, verb~now-crossing); (3) etak read-head peek + recovery loop + coupled bearing = ONE walk through NOW (F580+F577+F588); (1) F586 Egyptian = corpus magnitude, runs on (3)'s read-head. PREREQ: understand the chiral-axis seam (history helix) first. | F590 |
| **MOBIUS = THE LOOP (F589)** | The substrate loop, in 3D, IS a Mobius strip: anchor=core circle, imaginary band=the strip, CONJUGATION (F544)=the half-twist. WHY loop-not-circle: chirality = the orientation-reversing twist -> non-orientable. ASYMPTOTE FOR FREE: fixed-point-free involution (conj^2=I, double cover) = held-without-collapse (DUALITY). Higher-rank twisted bundle (Mobius=3D shadow, Hopf F124=higher rungs). CONJECTURE (open): sign-flip ~ axial-crossing ~ strong-coherence (F588). | F589 |
| **RECOVERY (F588)** | Orchestra missed-note: recovery from coherence loss = RE-COUPLING to a surviving coherent reference (Kuramoto). Few-missed+strong->recover; weak/no-field->no; WHOLE section scrambled RE-COHERES to a PINNED conductor (pin_anchor); total scramble + no reference -> no. The user's 'if you can still couple with something' shown cleanly. RBS-LM: the read-head should re-couple (etak F580 / a tome F584), not restart. Composes Kuramoto/F580/F577/F584/F552. | F588 |
| **CAPSTONE (F587)** | Complete English->Egyptian ETAK-HEAD kernel renders HIEROGLYPHIC UNICODE (man,water -> 𓀀 𓁷𓂋𓅱𓂝𓏤𓈒𓏥). Non-English-sentence output is 100% attested-move = coherent-as-Egyptian (F581 keystone confirmed). Honest: 100% is by-construction (local legality, not deep grammar); fidelity rough (join/gloss noise -> F586 blockers). Wires F580+F581+F582+F583+F585. | F587 |
| **SHARPENED F583 (F586)** | Earlier-Egyptian rules + Vygus English cross-check: (a) per-sentence German = 1.5x (marginal real gain over F583 1.4x, cleaner corpus); (b) per-lemma Vygus English = DIRECTIONAL only (random~0 -> artifact ratio; join 24%). Did NOT cleanly beat 1.4x. BLOCKERS: scheme-aligned TLA<->Vygus join + non-sparse meaning metric (semantic-category/embedding, not exact-word Jaccard). | F586 |
| **STANDING DIRECTION — all knowledge -> PR687 -> srmech** | All RBS-HDC/SNN/ML findings land in PR #687 (research/rbs-lm-rolling-2); corpora stay outside repo, findings attest. No-privileged-language (F398) => research is headed for srmech; end goal = RBS-LM as the human-language ROSETTA STONE for the srmech CLI/tool_schema (composes R-RBS-LM-54). | F586 |
| **EGYPT DATASETS (F585)** | Assessed the user's HF datasets: ancient-egyptian-multilingual-premium (vygus_2018 per-word dict: transliteration+English gloss+gardiner_signs, 100% tagged) = the SHARP per-word English CROSS-CHECK (F581: not a source) + bridges F582 via gardiner_signs + fixes F583's coarse proxy. egyptian-dict-ancient_egypt: transient fail, retry. CONFIRMED F581: the determinative IS the explicit meaning class (A->man/god/king, N->water/sky, O->stone/tomb). Verify HF license per MPM. NEXT: Earlier-Egyptian corpus + this dict cross-check -> re-run meaning-falls-out (beat F583 1.4x). | F585 |
| **EGYPTIAN L2 (F583)** | Meaning-falls-out test on REAL Egyptian (TLA Demotic 6k): supplied co-occurrence RULES (chess move-graph) -> meaning precipitates 1.3-1.4x (mechanism shown, magnitude weak: ligatured Demotic + per-sentence German proxy). Strengtheners: Earlier-Egyptian dataset / per-lemma glosses / larger slice / sharper metric. CHESS = INVERSE ETAK (fixed-surface/rule-constrained vs moving-ref/deviation); kernel has both the rule-graph manifold + the etak read-head (F580). | F583 |
| **EGYPTIAN ARC (F581/F582)** | Stance lodged (meaning falls out / structure held-open / determinative=explicit form-signal / first-perspective) + keystone (complex language ≅ continuous math). Layer-1 spine built: 1072 signs <-> Gardiner <-> 28-cat taxonomy from stdlib unicodedata (Unicode 16.0), license-clean, Class-A attested. NEXT: Layer-2 PD corpus (TLA/Worterbuch) -> the meaning-falls-out test; do NOT impose a sentence grammar. | F581/F582 |
| **ETAK READ-HEAD (F580)** | The etak/trig lens (F578) on SNN navigation: MEMORY is already etak (F551 native+delta) but NAVIGATION is absolute-sweep (wanders, 19% reach). Make the read-head ETAK GOAL-DIRECTED (steer deviation to a target -> 100% reach, directed retrieval). Unifies native+delta memory (F551) + goal-directed nav (F578) + coupled-wave bearing (F577) = an etak read-head. NEXT: wire the goal-directed etak read-head into the token generator (F478). | F580 |
| **ETAK MATH PEDAGOGY (F578)** | Teach trig+calculus the etak way: find a solution = NAVIGATE by deviation from a moving reference. TRIG=CORDIC (navigate to a bearing; (x,y)=(cos,sin), shift-add); CALCULUS derivative=etak progress-rate (discrete h-cascade), root-finding=Newton deviation-navigation, integration=dead reckoning. The discrete cascade under the continuous formula (continuous-number-line pedagogy); already what srmech.calculus + best_rational compute. NEXT: a teachable walkthrough / figure set (aphantasia: more figures). | F578 |
| **ETAK vein (F575)** | core already ours (F551); cognitive-science framing (navigation=substrate-distributed computation) + progress=rate-of-bearing-change UNMINED; candidate sources flagged-from-memory, MUST PDF-verify per MPM before citing. | F575 |
| **RE-ENCODE-TAGS DONE** | F576: Simple Wiki re-encoded WITH markup (60k pages -> simplewiki_tagged/articles_tagged.jsonl): 100% [[links]], 79% ==headers==, 97% [[Category:]], 98% {{templates}}, 50% <ref>. Explicit [[link]] graph RETIRES the F572 mention-proxy; ToC/index first-class. NEXT: point F567 markup-aware clean at the tagged source; rebuild F572 on explicit links + [[Category]] index; emergent ToC/index navigation (F574 gate). | F576 |
| **SS-FULLWIKI** | **Encode FULL wiki for wider knowledge testing** — READY (F568: SimpleWiki is markup+markdown-clean 0.43% residual + relationship-aware; pipeline validated). Needs the full-wiki dump (data-acquisition, user-directed); the markup/markdown-aware clean + link->relationship extraction carries over directly. | F568 |
| **FOUNDATION DONE** | F572: [[link]]->entity-mention relationship rebar + native+delta slab (SS-0+SS-4) held as ONE load-bearing foundation; 80,626 edges/2,393 entities (33.7/entity), 43% load-bearing long-range, exact+reversible pour, columns stand, scales. Designed on SimpleWiki to hold full EN wiki. | F572 |
| **COUPLED WAVE (F577)** | A coupled (EM E/B quadrature) drive removes verb-direction flips a flat scalar injects (gate 7->0; telling 5->2). Flat=collapsed 1-bit chirality, coupled=full 2D-rotation (gamma5/Klein-4). STRUCTURE-correctness, not embellishment. | F577 |
| **MULTI-STREAM RE-AIM** | F573 framed 3/7 streams as richness/breadth -- WRONG goal (user: multi-stream is for CORRECT sentence structure, not embellishment). Re-aim: assign the 3/7 streams to CLAUSE ROLES (S-V-O slots) to build correct structure. NEXT. | F573/F577 |
| **DRIVER DONE** | F573: story-wave ENSEMBLE = a TRAJECTORY richness axis complementary to substrate-mixing's ACCESS axis; MULTIPLEX (coverage) richer (+41 breadth, breadth-not-specificity), triad(3) sweet spot > heptad(7); PICK-BEST/SUPERPOSE worse (honest negatives); mixing still reaches more (complementary). | F573 |
| **SS-5 main shape DONE** | Attention-factorization landed (F571): long-range subject->verb bond is 4.2x content-coupled (lives in the manifold, not the form window); LLM attention FACTORS into FORM 43% + CONTENT 21% = 64%, residual 36%. The separation IS the factorization. Remaining depth: the 36% residual, backoff/smoothing (F570), long-range agreement, SS-4 (wire native+delta store F551/F538 as content source). | F571 |
| **SS-3 local DONE** | POS-order sharpener landed (F570): POS class-n-gram order 2->3->4 sharpens real-vs-shuffled 1.27->2.08->4.37x; trigram sweet spot; ~52% subject->verb deps exceed a 4-gram window = the bounded-range CEILING = the attention gap. Long-range agreement -> SS-5. | F570 |
| **SS-1/SS-2 DONE** | POS-frame depth landed (F569): storage eigenbasis = TOPIC (not POS); grammar's signal lives in the DISCARDED function-word context; induced noun/verb POS frame is a real-but-SOFT bigram grammar (real 98% > shuffled 77%, +6% generalization). Refines F311 -> disjoint-signal. | F569 |
| **SS-0** | **MARKUP+MARKDOWN-AWARE content source (F567/F568)** — replace F566's blocklist with the markup-aware layer; feed [[links]]→relationships + <ref>→attestation into the content graph. The content source for SS-* must be markup-aware. | F567 |
| **SS-4** | **Wire the native+delta store (F551/F538)** as the content source — the Story Teller reads real content-addressed exchanges, the grammar render shapes them. | F551/F538 |
| **SS-5** | **The LLM moving-parts comparison (deepen)** — RBS-LM separates content/form where the LLM entangles them in attention; characterise what attention's long-range syntax would map to in the separated architecture (a syntax kernel over the form layer). | F564/F50 |

These are walkable now (srmech 0.7.x; the form layer is plain corpus statistics + the Story Teller content). Standing disciplines unchanged.
