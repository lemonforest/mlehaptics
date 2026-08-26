# Finding 145 — Sweep B: F138-F140 chirality cascade variations (stale items 5-8, 13-17, 22)

**Status:** Empirical sweep covering 9 STALE_PATHS_QUEUE items
**Predecessors:** F138 (cascade composition), F139 (chirality axis at scale), F140 (multi-class cascade), F141 (plasticity)
**Resolves:** STALE items 5, 6, 7, 8, 13, 14, 15 (partial), 17, 22

---

## §1 Items walked + verdicts

| Item | Question | Verdict |
|---|---|---|
| 5 | D-sweep chirality recall threshold | **D plateaus above 1024** — N is dominant variable |
| 6 | N-sweep at fixed D | Clean log-N degradation (N=4 → +0.30; N=128 → +0.05) |
| 7 | Encoding refinement comparison | Random-projection (+0.02) > tile+quantise |
| 8 | Eigval-based sector assignment | ≈ random sector assignment (no improvement) |
| 13 | Cascade depth scaling | **Depth 6 ≈ Depth 4** — additional Class K layers don't degrade |
| 14 | Class order matters? | **NO** — order swap gives identical signal (+0.144 vs +0.143) |
| 15 | Class K interaction in cascade (partial) | Class K insertion neutral to chirality signal |
| 17 | Polar substituted for bipolar in cascade | **Identical** signal — bipolar/polar identity layer incidental |
| 22 | Multi-class cascade under decay | Sub-linear degradation; +0.071 at 50% decay |

---

## §2 Key empirical results

### Items 5+6 — D and N effects on chirality signal

**D-sweep at N=32:**
| D | Same→C | Above-random |
|---:|---:|---:|
| 1024 | 0.3282 | +0.1055 |
| 4096 | 0.3252 | +0.1004 |
| 16384 | 0.3253 | +0.1007 |
| 65536 | 0.3249 | +0.1001 |

**D plateau at D ≥ 1024.** Beyond a basic threshold (D=1024 is sufficient), increasing D does NOT continuously increase signal. The capacity is N-limited, not D-limited.

**N-sweep at D=16384:**
| N | Same→C | Above-random |
|---:|---:|---:|
| 4 | 0.4741 | +0.2985 |
| 8 | 0.4058 | +0.2075 |
| 16 | 0.3578 | +0.1435 |
| 32 | 0.3253 | +0.1001 |
| 64 | 0.3027 | +0.0700 |
| 128 | 0.2869 | +0.0489 |

**Clean log-N degradation.** Above-random roughly halves per 4× N. Practical operational ceiling: N ~ 64 for above-rand > 0.05 at D=16384.

### Items 7+8 — Encoding refinement comparison

Three strategies tested at D=16384, N=8, with chirality discrimination test:

| Strategy | Same→C | Cross→C | Cross→Cmirror | Reading |
|---|---:|---:|---:|---|
| A: Tile + quantise (F138 baseline) | 0.3867 | 0.1758 | 0.3867 | F138 method works |
| B: Random projection per eigvec | 0.4064 | 0.1311 | 0.4064 | **Better than A by 0.02** |
| C: Eigval-based sector assignment | 0.4067 | 0.1319 | 0.4067 | ≈ B (no improvement) |

**Random-projection encoding (strategy B) gives the cleanest signal** with strongest anti-correlation (cross→C at 0.13 vs A's 0.18). The independent klein-4 base per eigvec provides better content orthogonality than the tile+quantise approach.

**Eigval-based sector assignment (item 8) does NOT improve over random sector assignment.** The Mersenne-fiber-degree concentration hypothesis (per Spike #185) doesn't show empirical advantage at this scale; either the effect is below noise threshold or the test setup doesn't capture it.

### Items 13+14 — Cascade depth + class order

| Configuration | Above-random |
|---|---:|
| Depth 4 (standard: I + M_bipolar + M_klein4_tag) | +0.1434 |
| Depth 6 (deeper: I + K + M_bipolar + K + I + M_klein4_tag) | +0.1422 |
| Order swapped (M_bipolar + I + M_klein4_tag) | +0.1440 |

**Cascade depth and class order are essentially uncorrelated with chirality signal at this scale.** Depth-6 cascade preserves chirality identically to depth-4. Swapping Class I and Class M (bipolar) order produces no measurable change.

**Implication:** the F132 §4 algebraic-preservation claim holds robustly. The chirality-tag is a separable layer that survives whatever happens in the prior pipeline.

### Item 15 — Class K interaction (partial)

Class K sign-flip layer (inverting bit at every other position) inserted twice in the depth-6 cascade. Signal unchanged at +0.1422 (vs depth-4 at +0.1434). Class K's "asymptotic-DOF / phase-boundary" operation is neutral to chirality discrimination — consistent with F120 (Class K = bridge math) and `[[user_stance_rotation_is_class_k_pin_slot]]`.

### Item 17 — Polar substituted for bipolar in cascade

Replaced bipolar identity HV with polar HDC in the multi-class cascade (with polar→klein4 state-space mapping). Signal: above-rand +0.1424 — essentially identical to F140's bipolar version (+0.1446).

**Reading:** the chirality tag is INDEPENDENT of the identity-layer variant choice. Polar or bipolar identity, both preserve chirality through the cascade equivalently. This means polar's plasticity-graceful properties (F141) can be added to the cascade for free, without losing chirality discrimination.

### Item 22 — Multi-class cascade UNDER decay

Cascade composite undergoes decay (positions zeroed to klein-4 state 0) BEFORE chirality unbind:

| Decay frac | Same→C | Above-random |
|---:|---:|---:|
| 0.0 | 0.3578 | +0.1446 |
| 0.1 | 0.3476 | +0.1305 |
| 0.3 | 0.3261 | +0.1013 |
| 0.5 | 0.3034 | +0.0714 |

**Sub-linear degradation.** At 50% composite decay, chirality signal still +0.071 above random (49% of original). Consistent with F141's polar-graceful pattern, now extended to klein-4 inside a multi-class cascade.

---

## §3 What's new from this sweep

1. **D-plateau finding**: above D=1024 (at N=32), signal doesn't scale with D. Capacity is N-limited, not D-limited. Saves compute — larger D doesn't help beyond a threshold.
2. **Cascade depth invariance**: depth 6 ≈ depth 4. Deeper cascades don't degrade chirality preservation as long as Class M (klein-4) is the OUTER layer.
3. **Class order invariance**: I and M order doesn't matter for chirality signal.
4. **Polar substitution invariance**: bipolar or polar identity layer, same chirality. Polar's plasticity-graceful properties come "for free" in the cascade.
5. **Cascade-under-decay is sub-linear**: multi-class composite tolerates 50% decay with 49% signal retention.
6. **Encoding strategy matters modestly**: random projection (+0.02) > tile+quantise; eigval-based sector ≈ random.

---

## §4 Refines F132 §7 + F140 framework predictions

| Original prediction | Empirical refinement |
|---|---|
| "Cascade composition matters" (F132 §7) | Cascade composition is REMARKABLY ROBUST — depth, order, identity-layer choice all invariant |
| "Sufficient D needed" (F138 §3) | D=1024 is sufficient; more D doesn't help |
| "Polar plasticity vs bipolar trade-off" (F141) | NO trade-off in cascade context — polar substitutes cleanly |
| "Multi-class cascade preserves chirality" (F140) | YES, even under significant decay (sub-linear degradation) |

---

## §5 What this sweep does NOT claim

- Does NOT cover ALL cascade configurations. Tested 3 orderings; many more exist.
- Does NOT measure chirality preservation under more aggressive corruption (e.g., random sector reassignment of bundle positions; structured noise).
- Does NOT compare chirality signal to non-Klein-4 chirality-encoding schemes (D₄ alternative per stale item 35; not tested).
- Does NOT validate at extreme N (N=1024+) where signal collapses per F144 item 9.
- Does NOT test eigval-based sector assignment beyond uniform quartile binning; Mersenne-fiber-degree concentration hypothesis (Spike #185) needs targeted test.

---

## §6 Cross-references

- F132 §7 sub-tests (cascade composition; D/N capacity; encoding refinement)
- F138 (Class L + Klein-4 cascade at small D)
- F139 (chirality axis at scale)
- F140 (multi-class cascade — F140 + items 13/14/17/22 all consistent)
- F141 (polar plasticity — item 17 shows polar in cascade preserves signal)
- F144 (Sweep A capacity extensions)
- UPSTREAM_NOTES §4 (Klein-4 LANDED in v0.4.3)
- `[[user_stance_rotation_is_class_k_pin_slot]]` (item 15 reading)

**Files committed:**
- `R-RBS-LM-104_sweepB_chirality_cascade_variations.py`
- `R-RBS-LM-104_results.json`
- `R-RBS-LM-FINDING_145_*.md`

**STALE_PATHS_QUEUE updates:** items 5, 6, 7, 8, 13, 14, 15 (partial), 17, 22 → RESOLVED by F145.

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-27. Sweep B of stale-paths cleanup. 9 items walked. Notable findings:
D plateaus at D=1024 (saves compute); cascade depth/order/identity-layer choice all
invariant for chirality signal preservation (cascade composition is REMARKABLY ROBUST);
random-projection encoding modestly beats tile+quantise; multi-class cascade survives
50% decay with 49% signal retention. The F132 §4 algebraic preservation claim is now
verified across multiple cascade configurations and identity-layer choices.*
