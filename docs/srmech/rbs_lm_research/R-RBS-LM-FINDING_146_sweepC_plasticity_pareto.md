# Finding 146 — Sweep C: plasticity dynamics + Pareto frontiers (stale items 12, 18-21, 24, 27)

**Status:** Empirical sweep covering 7 STALE_PATHS_QUEUE items
**Predecessors:** F137 (capacity), F141 (polar plasticity graceful), F144 (klein-4 noise robustness), F145 (cascade variations)
**Resolves:** STALE items 12, 18, 19, 20, 21, 24, 27 (with one important null)

---

## §1 Items walked + headline verdicts

| Item | Question | Verdict |
|---|---|---|
| 12 | D vs N Pareto for chirality | N dominates; D ≥ 2048 sufficient |
| 18 | **Klein-4 under decay** | **Klein-4 is NOT plasticity-graceful — collapses at decay** |
| 19 | Decay-recovery (Hebbian rehearsal) | Works — +17.9% recovery from 50% rehearsal |
| 20 | D × N × decay Pareto | Decay degrades cube-rule with N (high-N collapses fastest) |
| 21 | Noise vs decay distinction | **Decay LESS damaging than noise** (matched 30%, +0.16 advantage) |
| 24 | Polar + Klein-4 hybrid extended | +0.32 above-random — strong signal retention |
| 27 | 4-way signal-level discrimination | **NULL result** — same-sector clustering not visible at this setup |

---

## §2 Critical finding — Klein-4 is NOT plasticity-graceful

**Item 18 results (Klein-4 under decay, D=10000, N=16):**

| Decay frac | Klein-4 above-rand | Polar above-rand (F141) |
|---:|---:|---:|
| 0.00 | +0.143 | +0.237 |
| 0.10 | +0.107 (-25%) | +0.224 (-6%) |
| 0.30 | +0.033 (-77%) | +0.202 (-15%) |
| 0.50 | +0.005 (-97%) | +0.173 (-27%) |
| 0.70 | **+0.001 (-99%)** | **+0.143 (-40%)** |

**Klein-4 collapses CATASTROPHICALLY under decay; Polar degrades GRACEFULLY.**

**Why:** Klein-4's state 0 is the identity element of the F₂ × F₂ group — but it's just one of 4 equal-status states. Zeroing out positions doesn't preserve information; it injects RANDOM-LOOKING content (state 0 is structurally indistinguishable from any other state from the binding-algebra's point of view).

**Polar's** state 0 is **structurally privileged**: it's the absorbing element under multiplicative bind (0 × anything = 0), it doesn't contribute to bundle majority votes, and it explicitly marks "uncertain / dead-band" content.

### §2.1 Architectural pattern implication

This finding **JUSTIFIES the two-tier architecture** from `ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md`:

- **Tier 1 (Klein-4)** — chirality encoding (where it dominates per F139/F142)
- **Tier 2 (Polar)** — plasticity storage (where Klein-4 cannot operate)

You CANNOT use Klein-4 for plasticity-decaying memory storage; it collapses. The two-tier separation isn't optional — it's REQUIRED by the substrate-encoding properties of each variant.

---

## §3 Item 19 — Decay-recovery works (Hebbian rehearsal)

Setup: polar bind → apply 50% decay → measure → rehearse 50% of decayed positions → measure again.

| Stage | Above-random |
|---|---:|
| After 50% decay | +0.2625 |
| After 50% rehearsal | +0.3095 |
| Recovery | **+17.9%** |

**Hebbian-style rehearsal is operationally effective on polar HDC.** Partial restoration of decayed positions recovers proportional signal. This validates the F141 §6 "binding-confidence as first-class state" framework: positions transition 0 → ±1 on reinforcement, and the bundle signal recovers proportionally.

For RBS-NN plasticity dynamics, this means a Hebbian update rule on polar Tier 2 storage produces detectable improvement — a foundational ingredient for any plasticity-aware NN architecture.

---

## §4 Item 21 — Decay LESS damaging than noise (matched fraction)

| Corruption type | Above-random | Density |
|---|---:|---:|
| Sign-flip noise (30%) | +0.141 | 0.848 |
| Zero-decay (30%) | +0.297 | 0.824 |
| Decay-vs-noise advantage | **+0.156** | similar |

At matched 30% corruption fraction, **zero-decay preserves 2.1× more signal than sign-flip noise.**

Why: sign-flip noise injects WRONG INFORMATION (positions vote OPPOSITE the truth). Zero-decay injects NO INFORMATION (positions vote NEUTRAL). Per polar's multiplicative bind semantics, 0 is absorbing — it doesn't pollute the bundle majority.

This confirms F141 §5 framework: **the polar 0-state IS the operational Class K pin-slot dead-band**, and it provides genuine substrate-level advantage over sign-flip corruption (which has no neutral state in bipolar / Klein-4).

---

## §5 Items 12+20 — Pareto frontiers

**D vs N (klein-4 chirality at decay=0):**

| Config | Above-rand |
|---|---:|
| D=2048, N=8 | +0.204 |
| D=2048, N=32 | +0.098 |
| D=2048, N=128 | +0.045 |
| D=8192, N=8 | +0.209 |
| D=8192, N=32 | +0.099 |
| D=8192, N=128 | +0.047 |
| D=32768, N=8 | +0.207 |
| D=32768, N=32 | +0.101 |
| D=32768, N=128 | +0.049 |

**D doesn't matter much** at this regime. N is the dominant variable. 16× D change (2048 → 32768) gives ~0.005 above-rand change at any N.

**D × N × decay:**

| D | N | decay 0.0 | decay 0.3 | drop |
|---:|---:|---:|---:|---:|
| 4096 | 16 | +0.145 | +0.030 | -79% |
| 4096 | 64 | +0.068 | +0.003 | -96% |
| 16384 | 16 | +0.144 | +0.036 | -75% |
| 16384 | 64 | +0.069 | +0.002 | -97% |

**Decay-damage scales with N.** At low N, decay degrades 75% of signal; at higher N, decay degrades nearly 100% of signal. The interaction between N and decay is multiplicative: higher load + decay = catastrophic for Klein-4 (consistent with §2 finding).

---

## §6 Item 24 — Polar + Klein-4 hybrid extended

The hybrid encoding (Klein-4 sector + polar overlay) per `R-RBS-NN-4_token_encoder.py` produces above-random +0.3204 at D=10000, N=16. **Strong signal retention** — outperforms either pure variant individually at this scale.

| Variant | Above-random |
|---|---:|
| Bipolar pure | ~+0.14 |
| Klein-4 pure | +0.14 |
| Polar pure | +0.24 |
| **Hybrid (Klein-4 + Polar)** | **+0.32** |

The hybrid combines:
- Klein-4's chirality structure
- Polar's 0-state for sparse representation

It's empirically the best variant at this scale. Validates the R-RBS-NN-4 hybrid as a real research path, not just a theoretical construct.

---

## §7 Item 27 — 4-way signal-level NULL result

Tested: 4 chirality "sectors", 4 synthetic-signal instances per sector, klein-4 encoding with sector tag, bundle, then query with each sector and check if top-4 are from that sector.

**Result: 0/4 precision in EVERY sector.** Same-sector clustering not visible at this scale and setup.

**Why:** The 4 instances within each sector have DIFFERENT random content (different synthetic-signal seeds). Sector tag only XORs in a constant shift; it doesn't make same-sector content more SIMILAR to each other. The composite is essentially random with respect to which sector its contributors came from.

**For sector retrieval to work**: the SECTOR TAG would need to be the distinguishing feature (same as F139's test), not the content. When content varies per-instance and we query for sector, retrieval doesn't favor same-sector signals.

**This is a methodology lesson, not a Klein-4 failure.** F139 worked because same-sector concepts share their identity through unbind operations. F142 worked because the chirality WAS the load-bearing distinction. Item 27 didn't work because the test setup didn't make sector the load-bearing distinction.

**Operational guidance**: for sector clustering of multi-instance content, you'd need either (a) same-sector content to share substantial overlap a priori, or (b) a different retrieval methodology that operates on the sector layer specifically. This is open for future work.

---

## §8 What this sweep does NOT claim

- Does NOT claim that polar HDC is universally better than Klein-4 under decay. Polar wins on decay; Klein-4 wins on chirality discrimination (F139, F142) and bit-flip noise (F144).
- Does NOT establish a precise threshold for Klein-4 decay tolerance. Item 18 measures at D=10000, N=16; other scales may give different curves.
- Does NOT validate hybrid encoding for production. R-RBS-NN-4 §5 research-path status; further testing needed.
- Does NOT solve the multi-instance sector clustering problem. Item 27 is a null result, not a solution.
- Does NOT claim cube-rule scaling is exactly the form for D × N × decay. The product-effect pattern emerges from 4 data points; finer measurement would refine.

---

## §9 Cross-references

- F139 (chirality axis operational at scale; same-sector retrieval baseline)
- F141 (polar plasticity graceful; baseline for item 18 comparison)
- F142 (BCI chirality 13× advantage; chirality is load-bearing)
- F144 (klein-4 noise robustness; complementary to plasticity finding)
- F145 (cascade variations; chirality robust through composition)
- ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md (justified by §2.1)
- `[[user_stance_asymptotic_dof_sidesteps_infinity]]` (item 21 polar 0-state framework)
- R-RBS-NN-4 token encoder (item 24 hybrid encoding validated)

**Files committed:**
- `R-RBS-LM-105_sweepC_plasticity_pareto.py`
- `R-RBS-LM-105_results.json`
- `R-RBS-LM-FINDING_146_*.md`

**STALE_PATHS_QUEUE updates:** items 12, 18, 19, 20, 21, 24, 27 → RESOLVED by F146 (item 27 as documented null result).

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-27. Sweep C of stale-paths cleanup. 7 items walked. Headline:
Klein-4 is NOT plasticity-graceful — collapses catastrophically under decay (-99% at
70%). This JUSTIFIES the two-tier ARCHITECTURAL_PATTERN (Tier 1 Klein-4 chirality +
Tier 2 Polar plasticity) — separation isn't aesthetic, it's required by the substrate-
encoding properties. Decay-vs-noise distinction: zero-decay preserves 2.1× more signal
than sign-flip noise at matched 30%. Hebbian rehearsal recovers +17.9% signal from 50%
decay. Hybrid encoding (Klein-4 + Polar overlay) outperforms either pure variant at
+0.32 above-random. Item 27 multi-instance sector clustering is a documented null
result — methodology lesson, not Klein-4 failure.*
