# R-RBS-NN-FINDING R13b — Mixed-precision Tier 1: F146 §6 hybrid-wins prediction does NOT transfer to storage context; klein-4 default is fine

**Status:** Phase 3b of R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md CLOSED
**Predecessors:** F146 §6 (hybrid wins at +0.32 above-rand in controlled binding test), R-RBS-NN-4 (token encoder with hybrid variant), R-RBS-NN-10 (storage)
**Result:** Storage retrieval performance is variant-agnostic at moderate N; klein-4 default works fine

---

## §1 Headline

The F146 §6 finding that **hybrid encoding (Klein-4 + polar overlay) wins at scale** does NOT transfer to the storage retrieval context. At N ∈ {50, 100, 200}, the three variants (klein-4, polar, hybrid) all sit within ±0.05 in p@3:

```
N=50:   klein4=0.755  polar=0.704  hybrid=0.735     winner: klein-4 (+0.020 over hybrid)
N=100:  klein4=0.698  polar=0.709  hybrid=0.698     winner: polar    (+0.011 over both)
N=200:  klein4=0.615  polar=0.575  hybrid=0.585     winner: klein-4 (+0.030 over hybrid)
```

**No variant dominates the others.** Klein-4 default (current R-RBS-NN-10 / R-RBS-NN-12 behavior) is operationally fine.

---

## §2 Why F146 §6's hybrid-wins prediction didn't transfer

F146 §6 measured hybrid in a **direct binding+bundle** test (bind N pairs, query, recover). The hybrid encoding's chirality structure + polar 0-state combined to give +0.32 above-rand at D=10000, N=16.

In the storage context (R-RBS-NN-13b), the three variants all pass through the **Class K bridge to polar** before Tier 2 operations. The bridge:
- **Klein-4 → polar**: XOR-bit-sign extraction (state-pair XOR → ±1; dense polar)
- **Polar → polar**: identity (passes through unchanged)
- **Hybrid → polar**: identity (hybrid encoder produces polar directly)

After the bridge, all three become polar HVs operated on by polar_bind / polar_bundle / polar_similarity. The hybrid encoder's advantage — combining Klein-4 chirality structure with polar 0-state — was preserved INSIDE the hybrid HV but its CHIRALITY METADATA was lost in the bridging step.

**Specifically:** the hybrid encoder produces polar HVs with ~50% zeros (per density 0.5 default). The Klein-4 bridge produces dense polar HVs (no zeros). At Tier 2:
- Klein-4-bridged: 100% of positions vote
- Hybrid-bridged: 50% of positions vote (zeros are absorbing/neutral)

Klein-4 wins on raw signal voting power; hybrid loses voting density but gains nothing because the chirality structure isn't queried at retrieve time (we don't compare sectors; we compare polar values).

---

## §3 Empirical results

| Variant | N=50 p@3 | N=100 p@3 | N=200 p@3 | Composite density |
|---|---:|---:|---:|---|
| klein4 | **0.755** | 0.698 | **0.615** | 0.945-0.975 (dense) |
| polar | 0.704 | **0.709** | 0.575 | 0.925-0.964 |
| hybrid | 0.735 | 0.698 | 0.585 | 0.923-0.963 (zeros from density 0.5) |

At every N, all three variants are within ±0.05 in p@3 — substantially **less variation than between scales** (N=50 vs N=200 differs by ~0.15 within each variant).

The dominant factor is **N (capacity load)**, not variant choice.

---

## §4 Hypothesis verdict

| Predicted | Verdict |
|---|---|
| H1: hybrid > both klein4 and polar at all N | ❌ FAIL — hybrid wins zero of three scales |
| H2: hybrid competitive (within 0.05) at all N | ✅ PASS — hybrid within ±0.05 at every N |
| H3: klein-4 default is fine for storage | ✅ PASS — klein-4 wins or ties at most scales |

The framework hypothesis (hybrid wins at scale per F146 §6) does NOT generalize to the storage operational context. **In storage, variant choice is essentially a wash** at moderate N.

---

## §5 What this finding refines about the architectural pattern

`ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md` proposes:
> Tier 1: Klein-4 chirality-tagged concept storage
> Tier 2: Polar associative memory

R-RBS-NN-13b confirms this is the right architectural choice **for retrieval performance**. Klein-4 Tier 1 + polar Tier 2 (the default) gives equal or better retrieval than hybrid Tier 1 + polar Tier 2.

**The hybrid encoding may still matter in other contexts:**
- BCI applications with chirality-bearing input signals (F142 chirality-pure scenario)
- Multi-axis chirality tasks where the 4-sector structure is the load-bearing distinction
- Plasticity-decay tasks where the 0-state must be a first-class state at Tier 1

For pure storage/retrieval, **Klein-4 stays the recommended default**.

---

## §6 Where the bridge gets in hybrid's way (and a possible refinement)

The current bridge collapses Klein-4 sectors via state-bit XOR:
```
klein4 0 (00) → polar +1
klein4 1 (01) → polar -1
klein4 2 (10) → polar -1
klein4 3 (11) → polar +1
```

This treats sectors 0+3 as "+1" and sectors 1+2 as "-1". The 4-way chirality structure collapses to 2-way at the bridge.

A more chirality-preserving bridge might:
- Use TWO polar HVs per concept (one for γ₅ axis, one for iω₇ axis)
- Or extend Tier 2 to be Klein-4 also (Tier 2 polar → Tier 2 klein-4)

The first option doubles storage; the second loses polar's plasticity-graceful behavior (per F146 §2 critical finding). Neither is a clear win.

**Conclusion:** the bridge's chirality-collapse is a structural choice with downstream consequences — hybrid Tier 1 doesn't help BECAUSE the bridge loses what hybrid encoded. To get hybrid's full benefit, either don't bridge (use Klein-4 in Tier 2) or use a different bridge.

This is logged as future-scope work; not in the current Phase 3b scope.

---

## §7 What this finding does NOT claim

Per MFO §VII.6.20:

- Does NOT claim hybrid is useless. It's tied or close to klein-4 at retrieval; its value may emerge in other tasks (chirality-axis discrimination, BCI scenarios).
- Does NOT claim klein-4 is universally optimal. At N > 200, the test wasn't run.
- Does NOT claim the bridge is wrong. The XOR-bit-sign mapping is one candidate; alternatives exist.
- Does NOT test mixed-bag storage (some concepts klein-4, some polar, some hybrid). Only homogeneous configurations tested.
- Does NOT change the recommended default of the storage class. Klein-4 stays the default.

---

## §8 Cross-references

- R-RBS-NN-10 (storage; klein-4 default preserved)
- R-RBS-NN-4 (token encoder; hybrid variant API stays available)
- F146 §6 (hybrid wins at +0.32 above-rand in CONTROLLED test; this finding shows it doesn't transfer to storage)
- ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md (validated; klein-4 Tier 1 stays canonical)
- F142 §6 (chirality-pure cases where hybrid may still matter — separate context)

**Files committed:**
- `R-RBS-NN-13b_mixed_precision_tier1.py`
- `R-RBS-NN-13b_results.json`
- `R-RBS-NN-FINDING_R13b_*.md`

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-28. Phase 3b closed with null-result-like finding. F146 §6's
hybrid-wins prediction does NOT transfer to storage retrieval context. At N ∈ {50, 100,
200}, klein-4 / polar / hybrid all sit within ±0.05 p@3 — variant choice is a wash at
moderate N. Klein-4 default (current R-RBS-NN-10/-12 behavior) is operationally fine.
Structural reason: the Class K bridge collapses the 4-sector chirality structure to
2-way (XOR-bit-sign mapping), losing what hybrid encoded. Hybrid's full benefit would
require either no bridge (keep Klein-4 at Tier 2; loses polar plasticity per F146 §2)
or a different bridge (e.g., dual polar HVs per concept). Both are future scope. The
finding confirms the ARCHITECTURAL_PATTERN_two_tier_klein4_polar canonical setup.*
