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
| **BX-1** | **Holographic-principle LENS** (next-available finding #; F389=sedenion, F390=division-cascade now taken) — lossy flat-shadow vs lossless reconstruction; the resemblance and where it breaks; "lossless requires keeping fiber + chirality" | 📖 FRAMEWORK / offered | none to start; holography refs (’t Hooft / Susskind / Bekenstein / AdS-CFT) go through **k=3 triality verify-PDF** before lodging (F381 discipline); no-lineage + defensive scope (algebra/info-geometry side only, no gravity claim) |
| **BX-2** | **(8:7) inside the 15 — octonionic Hopf S⁷→S⁸** — recurse F384/F387 one rung up: does the 7 fiber as 1+(2:1)+(4:3); the chiral-dual `|` seam at k=7→15 | active | srmech-native (octonion table already shipped, `qm.octonion`); read-only, no version bump |

### DEFERRED — expert handoff / build-gated (NOT srmech-version-gated)
| Item | Subject | Status | Gate / note |
|---|---|---|---|
| **BX-3** | **Z₃-native physical medium** (F383's next-question) — *"what medium carries a stable, composable order-3 (Z₃/triality) state natively?"* | ⏸️ DEFERRED-expert | device-physics / fabrication is OUT of framework scope (CAD-ban). In-scope as a **literature reading** of known Z₃ physical systems (triality dive, lens-only); the engineering is the expert's (F282) |
| **BX-4** | **Coupled read-head as an actual RBS-SNN read mechanism** (F386+F388 → prototype) — phase-lock the readout into the RBS-SNN | ⏸️ DEFERRED-build | gated on the RBS-SNN build target (#855 / #844 / task #197); the algebra (`cascade.kuramoto_step` pin) is shipped — the integration waits on the SNN pipeline |

### ⏳ QUEUED-srmech — wait for srmech updates (numpy removal IN PROGRESS)
| Item | Subject | Gate |
|---|---|---|
| **BX-5** | **#863 QDFT/ODFT TOML cascade build** — author `quaternion_dft.toml` / `octonion_dft.toml` as live `cascade_catalog` descriptors (drafts done: R22) | **numpy-removal**: the cascade composes `qm.octonion` left/right-mult (the numpy/LAPACK surface), mid-rework (rc29→rc33, `qm` → `srmech[scientific]`). Building against the moving surface is premature. Resume after the numpy-free landing **and** srmech-dev picks up #863. |
| **BX-6** | **#863 `qm.quaternion` ergonomic module** (first-class 4×4 left/right mult) — NEW srmech code | same numpy-removal gate + srmech-dev |
| **BX-7** | **#863 `exp(μθ)` hypercomplex twiddle helper** — NEW srmech code | same gate |
| **BX-8** | **rc29 verification** — when rc29 (numpy-drop Option 1 + HV carrier) lands: verify the HV contract (UPSTREAM §22b) + STOP-list coverage in a clean venv OUTSIDE the source tree | rc29 published to TestPyPI |
| **BX-9** | **ephemerides-spectral → srmech 0.7.0 bump** (UPSTREAM §21) | live PyPI (rc ≠ SoT) |
| **BX-10** | **srmech-mcp repoint + restart** (project memory: deferred) | live PyPI clean (non-rc) tag |

### Disposition
**BX-1, BX-2 are walkable in the next research session** (no srmech bump). **BX-3, BX-4** await user direction / the SNN build. **BX-5–BX-10 are blocked on srmech updates — chiefly the in-progress numpy-math removal** (do not author the QDFT cascade against the moving `qm` surface; resume post-numpy-free + #863 pickup). Durable handoffs for the whole arc: issue **#863** + the **R22 descriptor drafts** + findings **F356→F388** + the re-prime artifact.

---

## ALU-native A–N thread (F393, 2026-06-04) — does the whole 14-class vocabulary reduce to add/subtract/shift + sign(handedness)?

**Spec/test-plan: F393** (anchor R35: multiply=shift-add, CORDIC rotation=shift-add+sign; + F392 divide=shift-subtract+handedness). **Hypothesis:** every A–N class reduces to **{add, subtract, shift, sign(handedness=C/K), compare, xor·and}** — no multiply unit, no divide unit, no FPU transcendental.

| Item | Subject | Status | Gate / note |
|---|---|---|---|
| **ALU-A** | **Attestation pass (research-triality)** — verify-PDF the CS reductions: CORDIC (Volder 1959), Booth multiply (1951), restoring/non-restoring division, binary GCD (Stein 1967), SHA-256 (FIPS 180-4) | **ACTIVE / EARLY** | **runnable NOW — no srmech update needed**; this is the early research/attestation the user flagged; F381 triality + verify-PDF discipline; no-lineage (CS literature's) |
| **ALU-B** | the per-class reduction map (14 classes → the minimal ALU set) | ✅ **DONE** | F393 |
| **ALU-C** | the **13 rc28-walkable classes** — srmech-native demo that each shipped primitive's output == an add/sub/shift+sign cascade (A/B/C/D/E/F/G/H/I/J/K/M/N) | **ACTIVE / now** | rc28; no version bump |
| **ALU-D** | the **numpy-free Class-L leg** — eigendecomp = Jacobi = CORDIC = shift-add+sign, fully numpy-free | ⏳ **QUEUED-srmech** | gated on the numpy removal (rc31 pure-Python Jacobi; UPSTREAM §22) — **same gate as BX-5..BX-8**; possible upstream ask: a CORDIC / shift-add atom |

### Prior art (cross-ref — this thread is a convergent rederivation, NOT new)
The lean-ISA arc already recognized most of this from the silicon angle (corpus-is-proof): **#751/F208** (6 atom intrinsics + divide/rational as iterative composites), **#761/F220** (6 order-2 + 1 order-3 triality = 7 = chirality-complete core), **F206/F208/F217** (the 2-bit Klein-4 sector lane is the *only* genuinely-new silicon; atoms ARE 74xx TTL; ~3-opcode RISC-V custom-ext). ALU-A/ALU-C should **cross-reference**, not re-derive these. What F392/F393 genuinely add: the **CORDIC reduction of the continuous/transcendental ops (trig/rotation/sqrt → Class-L eigendecomp)** = shift-add+sign.

### Disposition + HOLD
**ALU-A (attestation)** is walkable now (no srmech). **ALU-C (13 classes)** and **ALU-D (Class-L)** both **RUN srmech → HELD for extra srmech testing (user direction 2026-06-04)** — do not execute srmech-importing R-scripts until srmech has had extra testing (this composes with: don't build on the moving numpy surface). So the only truly-early item is **ALU-A** (literature/attestation via research-triality), and even that awaits a user go. Anchor + spec: F393; reductions proven: multiply (R35), divide (F392), trig/rotation/sqrt/L (R35 CORDIC).

---

## Anchor-axis thread (F396, 2026-06-04) — "the other axis is the anchor (reach within, not up)"

**Spec: F396.** Determination: WORTH RESEARCHING, two legs.

| Item | Subject | Status | Gate / note |
|---|---|---|---|
| **AX-1** | **no-magic-numbers check on 2:4:8** — is `1:3:7:3 = 2:4:8 = (1+1):(3+1):(7+1)` a STRUCTURAL partition of the A–N 14, and is the +3 meta-triad (B/H/N) = the 3 division-algebra anchors? | **ACTIVE / now** (framework+algebra, no srmech) | **must clear the nesting gate** (ℂ⊂ℍ⊂𝕆 → 2+4+8 double-counts; graded pieces = 2+2+4=8≠14). **Pre-stated null:** if no disjoint/graded 2:4:8 structure exists, 14=2:4:8 is falsified → dropped as coincidence (Class-C until grounded). |
| **AX-2** | **consolidated bit-exact ℍ+𝕆 demo** — exact integer algebra + within-rung-conjugate EC over dyadic components, no rung-climb, no FPU (continuous ops via CORDIC). **Concrete mechanism (F397):** the octonion k=7 as **two Kuramoto-coupled Klein-4 streams (both quads, each k=(2+2))**, the coupling = the within-rung EC (the \| seam / k=2 parity as a phase-lock). | ⏳ **QUEUED-srmech (HELD)** | mostly already proven (F389/F392/F385/F393); demo runs `cascade.kuramoto_step` + `hdc.klein4_*` → held. **Null to pre-state (F397):** do two coupled Klein-4 streams reproduce the FULL octonion product, or only its chirality skeleton? |

### Disposition
**AX-1** is walkable now (no srmech) but **may falsify** — that's fine (F394). **AX-2** is srmech-held. Leg-1 conclusion (anchor = the other axis; bit-exact within-rung; no climb) is high-confidence + mostly already shown; Leg-2 (the 2:4:8 partition) is gated behind AX-1's no-magic test.
