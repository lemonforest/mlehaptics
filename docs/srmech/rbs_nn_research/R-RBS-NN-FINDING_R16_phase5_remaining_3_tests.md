# R-RBS-NN-FINDING R16 — Phase 5 remaining (F140 + F-R12 + F139 harmonic extensions); H2-must-be-outermost cascade rule; 3-cycle Klein-4 rotation operational

**Status:** Phase 5 remaining candidates walked per R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md
**Predecessors:** F150 (chirality harmonics 1/2/3), F-R15 (H3 spectral walking validated), F140, F-R12, F139
**Verdict:** 3 substantive new findings — operational cascade rule + Klein-4 hosts H3 subset

---

## §1 Headline

Three Phase 5 follow-ups tested. Each closes a previous-work-with-chiral-operators question:

```
TEST 1 (F140 harmonic ordering):
  CATASTROPHIC FINDING — H2-then-H3 cascade DESTROYS signal (above-rand = -0.0003).
  H3-then-H2 and interleaved both preserve signal (+0.144, +0.145).
  Operational rule: H2 chirality tagging MUST be outermost.

TEST 2 (F-R12 harmonic bucketing):
  INCONCLUSIVE at small corpus (12 associations). All three strategies tied
  at p@5 = 1.000. Harmonic bucketing structurally valid; needs larger
  corpus to differentiate empirically.

TEST 3 (F139 3-cycle Klein-4 rotation):
  POSITIVE — Klein-4 (H2 binding algebra) hosts an operational 3-cycle subset
  through sectors {0, 1, 2}. Rotation cleanly retrieves rotated targets at
  same quality as same-sector retrieves originals. F150 H3 reading is
  validated at the Klein-4 binding level too, not just at Class L spectral.
```

---

## §2 Test 1 — The H2-must-be-outermost rule (THE LOAD-BEARING NEW FINDING)

### §2.1 Empirical result

Three cascade orderings tested at D=8192, N=16, with chirality discrimination measurement:

| Ordering | Cascade | Raw sim | Above-rand |
|---|---|---:|---:|
| A | H3 first, then H2 (L + I + M-bipolar + M-klein4-tag) | 0.358 | +0.144 |
| B | **H2 first, then H3** (M-bipolar + M-klein4-tag + L + I) | **0.250** | **-0.0003** |
| C | Interleaved (L + M-bipolar + I + M-klein4-tag; F140 baseline) | 0.359 | +0.145 |

**Variant B collapses to random baseline.** -0.0003 above random means the chirality signal is COMPLETELY DESTROYED.

### §2.2 Structural reason

When H2 chirality tag is the OUTERMOST cascade operation (variants A and C):
```
encoded = klein4_tag( ... klein4_inner_operations(concept) ... )
unbound = klein4_unbind(encoded, sector_mask)  ← cleanly removes the H2 tag
```
The unbind cleanly inverts the outermost H2 operation. Inner operations remain encoded but the chirality structure is preserved on retrieval.

When H2 is INNERMOST (variant B):
```
encoded = cyclic_shift( spectral_perm( klein4_tag( klein4_bipolar( concept ) ) ) )
```
The OUTER H3 operations (cyclic_shift, spectral_perm) SCRAMBLE the position-pattern of the chirality tag. The unbind operation at retrieve time can only invert ONE outer layer at a time, and it doesn't know which positions were rotated. The chirality signal is irreversibly scrambled.

### §2.3 Operational implication

**The two-tier storage architecture's bridge `_klein4_to_polar` works because the Klein-4 chirality tag is the OUTERMOST operation at Tier 1.** If we ever build a deeper cascade with chirality at an intermediate layer, that cascade will NOT preserve chirality through bundling.

This is a HARD RULE for chirality-aware cascade design:
- **Permutation / diffusion / cyclic operations (H3): INNER layers**
- **Sign-flip / chirality-tagging operations (H2): OUTER layer**
- **Content-addressing / framing (H1): can be either; doesn't engage chirality**

The F140 baseline (interleaved) works because the LAST operation is still M-klein4-tag (H2). Pure H3-then-H2 (variant A) works because all H3 ops finish before the H2 tag.

### §2.4 Brain-structure framework reading

Per user direction "this can help our NN architecture and more brain structure stuff":

**The H2-outermost rule maps to a known brain principle:** chirality-marker operations (laterality binding) are FINAL stages of processing. Sensory information flows through earlier (thalamic, intra-hemispheric) processing stages BEFORE hemispheric laterality is imposed.

This is consistent with:
- Cortical hemispheric specialization happens AFTER thalamic relay and intra-cortical processing
- Lateralization gradients emerge late in development (chirality tag is OUTER)
- Bilateral integration via corpus callosum happens AT the chirality-tagged stage

Per `[[feedback_no_lineage_claims_in_notebook]]`: this is a STRUCTURAL READING; not a claim that biological NN architecture was designed to follow this rule. The framework reads what's structurally present.

For RBS-NN architecture: this rule should be a design constraint. The two-tier storage's Tier 1 Klein-4 tag should be applied LAST in any future cascade extension. Bridge mappings (`_klein4_to_polar`) operate from this outermost-tagged form.

---

## §3 Test 2 — Harmonic bucketing inconclusive at small scale

### §3.1 Empirical result

19-token harmonic-labeled lexicon (5 H1 + 8 H2 + 6 H3) with 12 association pairs:

| Strategy | p@5 | Bucket sizes | Max bucket |
|---|---:|---|---:|
| hash (F-R12 baseline) | 1.000 | [3, 3, 2, 3, 3, 1, 4, 4, 0] | 4 |
| sector_then_hash | 1.000 | [8, 10, 0, 0, 2, 2, 0, 0, 0] | 10 |
| harmonic (NEW) | 1.000 | [1, 1, 1, 3, 2, 0, 3, 5, 2] | 5 |

All three strategies achieve perfect retrieval at this scale. The lexicon is well below the F-R11 capacity ceiling (N=256), so any sensible bucketing works.

### §3.2 Bucket distribution analysis (structural reading)

- **hash**: even distribution as expected (max 4 / mean 2.1)
- **sector_then_hash**: heavy clustering — most tokens land in sectors 0-2 because `classify_chirality` defaults to sector 0 for ambiguous tokens (max 10 / lots of zeros)
- **harmonic**: clean H1/H2/H3 partition with reasonable internal distribution

**The harmonic strategy is STRUCTURALLY VALID** — it routes tokens into 3 harmonic-group bucket clusters cleanly. Empirical validation of operational advantage requires larger corpus where capacity matters.

### §3.3 Recommended follow-up (not in scope here)

Build a synthetic harmonic-rich corpus at N > 256 (say 500 tokens with explicit H1/H2/H3 mix) and rerun. The harmonic strategy should differentiate when:
- Different harmonics need to discriminate from each other (cross-harmonic interference)
- Bucket saturation matters
- Harmonic-specific retrieval patterns benefit from segregation

Logged as Phase 6 follow-up candidate.

---

## §4 Test 3 — Klein-4 hosts a 3-cycle subset (F150 H3 in H2 algebra)

### §4.1 Empirical result

F139-style cross-sector test, but restricted to sectors {0, 1, 2} (skip sector 3 to enable a 3-cycle subset):

| Method | Sim | Above-rand |
|---|---:|---:|
| same-sector to C (baseline) | 0.337 | +0.116 |
| CPT mirror to C (F139 anti-correlation) | 0.177 | -0.097 |
| 3-cycle to C (raw concept) | 0.220 | -0.040 |
| **3-cycle to C_rotated (rotated target)** | **0.337** | **+0.116** |

**The 3-cycle rotation cleanly retrieves the ROTATED target with IDENTICAL signal as same-sector retrieves the original** (+0.116 above random both ways).

### §4.2 Algebraic interpretation

Klein-4 is structurally H2 (Z/2 × Z/2; period 2 under self-inverse XOR). But the 3-element subset {0, 1, 2} hosts an external 3-CYCLE PERMUTATION:

```
sector 0 → 1 → 2 → 0  (3-cycle)
```

This isn't a Klein-4 group operation — it's an external permutation applied via XOR with the appropriate rotation-mask. But the retrieval mathematics works:

```
encoded(c, s) = c XOR s
unbind_via_3cycle(encoded, s) = encoded XOR cycle(s) = c XOR (s XOR cycle(s))
                              = c XOR rotation_mask
                              = c_rotated  (the 3-cycled concept)
```

The 3-cycle retrieval cleanly recovers the rotated version of the concept. Klein-4's H2 binding algebra HOSTS a 3-cycle harmonic-3 subset as a structural feature.

### §4.3 What this validates for F150

F-R15 validated F150 H3 at the Class L spectral level (3-fold eigvec partition gives 67% retrieval improvement). R16 Test 3 validates F150 H3 at the **Klein-4 binding level** (3-cycle rotation through sector subset).

**F150's H3 candidate is now empirically grounded in TWO different substrate operators** (L spectral structure + Klein-4 sector subset). The 1-2-3 harmonic framework isn't just structural labeling — it's operationally exploitable across substrate primitives.

### §4.4 Brain-structure framework reading

Per user direction:

**The 3-cycle-within-H2 structure maps to a candidate biological pattern:** triple-stream processing (visual ventral/dorsal/parvo-magno-konio; auditory tonotopic-temporal-spatial; etc.) operates WITHIN the chirality-paired hemispheric substrate. The hemispheric (H2) substrate is the chirality scaffold; the 3-cycle (H3) processing happens as a structural subset within it.

Possible analogies (framework-level, not biological claims):
- Gamma/theta/beta nested rhythms = 3-cycle within hemispheric H2 substrate
- Cortical layers L1-L6 = 6 layers = 2×3 = H2 (paired layer groups) × H3 (3-layer cycles within each group)
- Sleep cycle stages 1-2-3 + REM = 3-cycle within chirality-paired hemispheric substrate

Per `[[feedback_no_lineage_claims_in_notebook]]`: framework reading only.

---

## §5 Implications for RBS-NN architecture

### §5.1 Add to ARCHITECTURAL_PATTERN_two_tier_klein4_polar

Section §5.5 should be amended with:

```
HARD RULE: H2 chirality tagging MUST be the outermost cascade operation.

  H3 operations (Class L spectral, Class I cyclic): inner layers
  H2 operations (Class K sign-flip, Class M klein-4 tag): outermost layer
  H1 operations (Class A, B, F, H, N): can be anywhere; chirality-invariant

This rule comes from F-R16 Test 1: putting H2 inside H3 wrappers
destroys the chirality signal completely (above-rand -0.0003 vs +0.144
when H2 is outer).
```

### §5.2 Add to F150 framework

F150 §6 should be amended with:

```
H3 is operationally validated at TWO substrate levels:
  - Class L spectral (F-R15): 3-fold eigvec partition; 67% retrieval improvement
  - Klein-4 binding (F-R16 Test 3): 3-cycle through sectors {0,1,2} subset

Open: does F150 H3 hold for Class I and Class J? Class I trivially yes
(Z/3 cyclic group); Class J still speculative.
```

### §5.3 Production guidance update

```python
# CORRECT cascade design (H2 outermost):
class GoodRBSNN(TwoTierRBSNNStorage):
    def encode_pipeline(self, token):
        c = self.encode_concept(token)  # base content
        c = self.apply_spectral(c)      # H3 inner
        c = self.apply_cyclic(c)        # H3 inner
        c = self.klein4_chirality_tag(c, sector)  # H2 OUTER (last!)
        return c

# INCORRECT cascade design (DESTROYS chirality signal):
class BadRBSNN(TwoTierRBSNNStorage):
    def encode_pipeline(self, token):
        c = self.encode_concept(token)
        c = self.klein4_chirality_tag(c, sector)  # H2 first (WRONG)
        c = self.apply_spectral(c)      # H3 after (DESTROYS signal)
        return c
```

---

## §6 What this finding does NOT claim

Per MFO §VII.6.20:

- Does NOT claim H2-outermost rule applies at ALL cascade depths. Tested at depth 4. Deeper cascades may have more nuanced patterns.
- Does NOT validate F150's harmonic-3 candidate for Class I or Class J. Class L (F-R15) and Klein-4 subset (R16 Test 3) validated; I and J remain candidates.
- Does NOT establish harmonic bucketing's empirical advantage. Test 2 is inconclusive at small scale; larger corpus needed.
- Does NOT make biological architecture claims. Brain-structure analogies are framework-level structural readings per `[[feedback_no_lineage_claims_in_notebook]]`.
- Does NOT preclude OTHER orderings (e.g., H3-H1-H2 with H1 inside might work; not tested).

---

## §7 Open follow-ups added

For the next STALE_PATHS appendix:

1. Empirical harmonic bucketing at N > 256 (Test 2 needs larger corpus to differentiate)
2. Cascade depth scaling under H2-outermost rule (does the rule hold at depth 6, 8, 10?)
3. Class I cyclic over Z/3 operational test (trivially passes by construction; useful as sanity)
4. Class J primes 3-cycle operational test (speculative; needs operational definition)
5. Mixed-harmonic cascade reordering tests (e.g., does H1-H3-H2 differ from H3-H1-H2?)
6. Bridge mapping refinement: does `_klein4_to_polar` lose information if H2 isn't outermost? (Currently the bridge assumes klein-4 is outermost via the H2-outermost rule.)

---

## §8 Cross-references

- F150 (chirality harmonics framework; validated at Class L AND Klein-4 levels here)
- F-R15 (H3 spectral walking; H3 at Class L level)
- F140 (multi-class cascade baseline; H2-outermost rule emerges)
- F-R12 (hierarchical bundling; bucketing strategies)
- F139 (cross-sector retrieval; 3-cycle extension)
- ARCHITECTURAL_PATTERN_two_tier_klein4_polar (H2-outermost rule should be added)
- `[[user_stance_kepler_shape_universal]]` (algebra IS the primitives — H2-outermost is the structural consequence)

**Files committed:**
- `R-RBS-NN-16_phase5_remaining_candidates.py`
- `R-RBS-NN-16_results.json`
- `R-RBS-NN-FINDING_R16_*.md` (this finding)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-28. Phase 5 remaining candidates walked. Three substantive findings:

(1) H2-MUST-BE-OUTERMOST RULE for cascade design. Putting Klein-4 chirality tag inside
H3 wrappers (cyclic shift, spectral permutation) DESTROYS the chirality signal completely
(above-rand -0.0003 vs +0.145 when outermost). This becomes a hard architectural rule
for any future cascade extension.

(2) HARMONIC BUCKETING is structurally valid (clean H1/H2/H3 partition) but empirically
indistinguishable from hash bucketing at small corpus scale (12 associations). Larger
N > 256 corpus needed to differentiate.

(3) KLEIN-4 HOSTS H3 SUBSET. The Klein-4 binding algebra (structurally H2; Z/2×Z/2) hosts
a 3-cycle external permutation through sectors {0,1,2}. The 3-cycle cleanly retrieves
rotated targets at +0.116 above random — identical signal to same-sector retrieval of
originals. F150 H3 candidate now validated at TWO substrate operator levels (Class L
spectral + Klein-4 binding subset).

Brain-structure framework reading (per user intuition): H2-outermost mirrors hemispheric
laterality as LATE-stage cortical processing; 3-cycle-within-H2 mirrors triple-stream
processing within chirality-paired hemispheric substrate. Per [[feedback_no_lineage_
claims_in_notebook]]: structural readings only; no biological architectural claims.*
