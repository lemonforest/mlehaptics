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

**The active research queue is empty as of 2026-05-28.** The next user direction
opens the next arc.
