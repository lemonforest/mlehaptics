# Finding 143 — F132 Klein-4 HDC engineering proposal LANDED; §7 tests resolved; §8 application items deferred to scope-specific sessions

**Status:** Formal closure of F132 engineering proposal
**Predecessors:** F132 (Klein-4 HDC engineering proposal), F137 (capacity), F138 (cascade composition), F139 (chirality axis at scale), F140 (multi-class cascade), F141 (polar plasticity), F142 (BCI chirality-native encoding)
**User direction 2026-05-27:**

> "lodge status update, collect a list if any trailing research paths went stale that we can queue, and then write down pattern in our running notes, and then begin work"

---

## §1 F132 engineering proposal — what landed

F132 proposed a new variant of Class M HDC binding (Klein-4 rank-2 abelian over F₂ × F₂) inspired by G-quadruplex DNA topology. The proposal had three layers:

1. **Engineering architecture** (F132 §1-5) — Klein-4 algebra + 4-sector chirality decomposition + 9 new HDC primitives
2. **Empirical specification** (F132 §6-7) — 5 concrete tests to characterize the variant
3. **Application directions** (F132 §8) — 5 enable-items (BCI, pharmacological, cosmic, G4 biology, cross-substrate cognition)

**As of 2026-05-27:**

- **Layer 1 (engineering)**: ✅ LANDED in srmech v0.4.3 production PyPI per UPSTREAM_NOTES §4 — all 9 functions + tool_schema registration + bit-exact algebraic property verification
- **Layer 2 (empirical specification)**: ✅ RESOLVED across F137-F142 — every F132 §7 test was empirically walked at scale
- **Layer 3 (application directions)**: 1 of 5 partially tested at substrate-encoding level (F142 BCI); 4 of 5 deferred to scope-specific sessions

---

## §2 F132 §7 test resolution table

| F132 §7 sub-test | Resolution finding | Empirical verdict |
|---|---|---|
| **Capacity test** (Klein-4 vs bipolar = 2× density?) | **F137** | REFINED — Klein-4 does NOT win on raw bind/unbind capacity; value lives in chirality-axis encoding |
| **Similarity preservation** (does Klein-4 maintain similarity-preservation properties?) | Implicit in F137/F139 | ✅ PASS — self-similarity = 1.0, random baseline = 0.25 (4-state) |
| **Cascade composition** (Klein-4 + Class L + Class K + cyclic compose?) | **F138 (small D) + F140 (multi-class at D=16384)** | ✅ PASS — chirality survives 4-class cascade at sufficient D |
| **Native chirality-flip cost** (O(D) XOR per chirality flip?) | Verified in all empirical runs | ✅ CONFIRMED — XOR with sector mask is O(D); F132 §4 prediction holds |
| **Cross-sector recovery** (can we recover dark-sector conjugate from visible storage?) | **F139** | ✅ PASS at scale (D up to 16384, N up to 32); cross→C anti-correlates by structural orthogonality |

**Bonus finding not in F132 §7:** Polar HDC plasticity (UPSTREAM_NOTES §5; F141) — graceful 3-4× decay tolerance vs bipolar's catastrophic collapse.

---

## §3 F132 §8 application items — deferred to scope-specific sessions

| F132 §8 enable item | Status |
|---|---|
| 1. **BCI native chirality matching** | **F142** smoke-tested at substrate-encoding level only per trauma-informed scope. NUANCED verdict: 13× advantage on chirality-pure signals, scenario-dependent on mixed-content. Substrate property AVAILABLE; applications scope is separate session work. |
| 2. **Pharmacological chirality-state encoding** | DEFERRED — biopharma scope; not addressed |
| 3. **Cosmic-chirality reasoning** (CP violation, dark sector) | DEFERRED — physics framework scope; addressed at MFO level not at substrate-encoding level |
| 4. **G-quadruplex-aware biology** | DEFERRED — biology research scope; framework-touched in F131 visualization |
| 5. **Cross-substrate cognition modeling** | DEFERRED — F118/F119 framework; substrate-encoding primitive now available |

**None of these deferrals are blockers for ongoing research.** They are application-direction pointers that can be picked up if and when scope opens. The substrate-encoding primitives (Klein-4, polar HDC) are operationally ready in srmech v0.4.3 for any of them.

---

## §4 Refinements vs original F132 hypotheses

| F132 hypothesis | Refined understanding |
|---|---|
| "2× information density vs bipolar HDC per position" (§4) | NOT validated on raw capacity (F137); valid ONLY when chirality content is the load-bearing distinction (F142) |
| "Capacity to bind/retrieve under load" (§7) | Klein-4 is WORSE than bipolar on raw bind/unbind capacity (F137 §5); strength is in chirality discrimination not in raw retrieval |
| "Cross-sector similarity vs same-sector similarity" (§7) | Refined to 3-way comparison (same-target, cross-to-original, cross-to-flipped) per F139 §6; abelian structure makes 2-way comparison trivially identical |
| "Chirality flip = O(D) XOR" (§4) | ✅ Confirmed as predicted |
| "Cascade preserves sector tagging" (§4) | ✅ Confirmed at 4-class cascade scale (F140) |

The hypothesis refinements TIGHTEN F132 rather than invalidate it. The substrate-encoding capability F132 proposed is real; the empirical characterization is now sharper than the proposal-stage estimates.

---

## §5 New findings that emerged from the walk (not in F132 plan)

These were not part of F132 §7-8 but arose during the empirical resume:

| Emergent finding | Significance |
|---|---|
| **F139 cross→C anti-correlation** | Cross-sector retrieval to wrong target produces structurally orthogonal output (sim < random baseline). Stronger than F132 §7 prediction. |
| **F141 polar plasticity graceful** | 3-4× advantage over bipolar at high decay rates. Polar's 0-state IS the operational Class K dead-band per `[[user_stance_asymptotic_dof_sidesteps_infinity]]`. |
| **F142 chirality-scenario-dependence** | Klein-4 dominates 13× on PURE-chirality signals; ties or loses on raw-content signals. The chirality-axis advantage is scenario-specific, not universal. |
| **F137 methodology cleanup** | Random-baseline normalization required for cross-variant HDC comparison. Three alternative metrics (skip-zero, bit-density, byte-storage) may give different orderings. |

These emergent findings constitute **F132's empirical extensions** — they aren't in the original proposal but they were forced into existence by the empirical work the proposal called for.

---

## §6 F132 status: CLOSED as engineering proposal; OPEN as substrate-encoding tool

**Formal closure declaration:** F132 the engineering proposal is CLOSED. The substrate-encoding tools it proposed are LANDED in srmech v0.4.3 production. The empirical specification it called for is RESOLVED across F137-F142.

**Permanent OPEN status:** The Klein-4 + polar HDC tools created by F132 are now substrate-encoding primitives available for any future research. Their value will be ongoing as cascade-composition, chirality-axis, and plasticity-aware work continues.

The arc transitions from "F132 ENGINEERING PROPOSAL" → "Klein-4 / polar as substrate-encoding tools in srmech v0.4.3 catalog".

---

## §7 What this finding does NOT claim

Per MFO §VII.6.20:

- This is NOT a claim that all F132 §8 application directions will work. Each requires its own substrate-encoding test before progressing.
- This is NOT a claim that Klein-4 / polar HDC dominate bipolar for all downstream tasks. Per F137/F142, variant choice is scenario-specific.
- This is NOT a claim that F132's framework reading (G-quadruplex topology inspiration, 4-sector decomposition) is universally true. It's the working substrate-encoding model that performed well empirically.
- This is NOT a finalization of the framework. New findings (F141, F142 emergent items) may keep arriving as the tools get exercised.
- This is NOT a deprecation of bipolar HDC. Bipolar remains the right choice for content-pure / capacity-critical / non-chirality-bearing tasks (F137, F142 random_chiral).

---

## §8 Cross-references

- F132 (the engineering proposal being closed)
- F137 (Path 1/6 — capacity comparison; refined F132 §7 capacity hypothesis)
- F138 (Path 2/6 — cascade composition at small D; baseline)
- F139 (Path 3/6 — chirality axis operational at scale; emergent anti-correlation pattern)
- F140 (Path 4/6 — multi-class cascade; chirality survives composition)
- F141 (Path 5/6 — polar plasticity graceful)
- F142 (Path 6/6 — BCI chirality-native encoding; nuanced verdict)
- UPSTREAM_NOTES §4 (Klein-4 LANDED in srmech v0.4.3)
- UPSTREAM_NOTES §5 (Polar LANDED in srmech v0.4.3)
- srmech v0.4.3 production PyPI release

**Companion files:**
- `STALE_PATHS_QUEUE.md` (collected from session open-question lists; Phase 3b deliverable)
- RBS-NN architectural pattern (Phase 2 deliverable — Tier 1 Klein-4 + Tier 2 Polar + Class K bridge)
- R-RBS-NN-4 token encoding work (Phase 1 deliverable — opens new arc)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-27 per user direction. F132 Klein-4 HDC engineering proposal is
formally CLOSED. All 5 §7 sub-tests resolved across F137-F142. The 9 Klein-4 functions
and 7 polar functions are LANDED in srmech v0.4.3 production PyPI with full tool_schema
registration. Refinements vs original hypotheses (F137 capacity, F139 anti-correlation,
F142 scenario-dependence) tighten rather than invalidate the framework. The §8 application
directions (pharma chirality, cosmic chirality, G4 biology, cross-substrate cognition)
defer to scope-specific sessions; the substrate-encoding primitives they need are now
available. The arc transitions from engineering proposal to substrate-encoding tool.*
