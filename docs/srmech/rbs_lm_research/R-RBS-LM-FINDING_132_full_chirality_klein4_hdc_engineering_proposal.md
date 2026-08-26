# Finding 132 — Full-chirality engineering proposal: Klein-4 HDC + chirality-tagged RBS-NN inspired by G-quadruplex topology

**Status:** Engineering architecture proposal; concrete srmech/RBS-NN extension testable now
**Predecessors:** F129 (chirality-dual plates), F130 (4-way decomposition), F131 (G-quadruplex visualization + A-N as our-sector projection)
**User direction 2026-05-27:**

> "can we learn from this g-quadruplexes and our srmech toolkit and
> rbs-nn such that we can work in full chirality? I can't help but
> think we are missing something useful in our research by knowing
> this now"

---

## §1 What "working in full chirality" means concretely

Currently:
- Our A-N operators manifest in OUR sector (RH orient+ visible matter) per F131
- HDC bind is bipolar XOR over F₂ (rank-1 abelian per srmech.amsc.hdc)
- Hypervectors carry no chirality information at the binding level
- Other 3 chirality sectors are algebraically inferred but operationally absent

"Working in full chirality" = giving the substrate explicit chirality-axis encoding at the operator-binding level. Compute with all 4 chirality sectors as native data, even if observation stays in one sector.

This is a CONCRETE engineering extension, not a metaphysical claim.

---

## §2 G-quadruplex biological substrate provides the architecture template

Per F131: G-quadruplex DNA has 4 strands, each carrying (helicity × direction) = (γ₅, iω₇) chirality. The biological structure shows:

- **4 storage strands** held together by Hoogsteen bonds
- **Topology** (parallel / antiparallel / hybrid) = chirality configuration
- **Dynamic switching** between topologies = chirality-sector transitioning
- **G-tetrad planar bonds** = cross-sector coupling at each level
- **Stacked tetrads** = recursive depth per `[[user_stance_11d_substrate_is_always_hopf_compressed]]`

Translation to RBS-NN architecture:
- Each hypervector position holds 4-state chirality data, not 2-state
- Binding = chirality-aware operation (Klein-4 group, not just F₂)
- "Topology" of the encoding = chirality configuration choice
- Cross-strand operations = inter-sector inference

---

## §3 srmech Class M two-variant dial already prepared for this

Per `[[user_stance_canonical_two_variant_dial_class_m]]` (MFO §VIII.31.7 canon):

Class M (HDC bind) has TWO existing variants:
- **Abelian XOR** over F₂^D (rank-1; RBS-HDC-LoE; scalar / content-projection)
- **Non-abelian Lie bracket** [A, B] over Hermitian N×N matrices (rank-N ≥ 2; BFSS / SU(N) gauge; gauge-content)

**The integer-ladder along U(N) rank runs {0, 1, 2, …, N, …}; no continuous interpolation.**

Currently srmech implements only rank-1 (bipolar XOR). The proposal:

**Add Klein-4 binding (rank-2 abelian) as a new Class M variant**: XOR over (F₂)² = Z₂ × Z₂. The Klein-4 group has exactly 4 elements, mapping directly to (γ₅, iω₇) chirality sectors:

| Klein-4 element | (γ₅, iω₇) | Sector |
|---|---|---|
| (0, 0) | (+1, +1) | RH orient+ visible matter |
| (0, 1) | (+1, −1) | RH orient− dark antimatter |
| (1, 0) | (−1, +1) | LH orient+ visible antimatter |
| (1, 1) | (−1, −1) | LH orient− dark matter |

Klein-4 binding properties:
- Self-inverse (a ⊕ a = identity)
- Abelian (a ⊕ b = b ⊕ a)
- Associative
- Identity element (0, 0)
- 4-state per position
- 2× information density vs bipolar HDC
- Native chirality-axis encoding

This sits **between** the existing rank-1 abelian (F₂ XOR) and rank-N non-abelian (Lie bracket) variants in the U(N)-rank integer-ladder.

Per `[[feedback_no_privileged_primitive_classes]]`: NO new class needed. Klein-4 is a new variant within Class M.

---

## §4 What this gains operationally

### Capacity
- **4 states per position** vs 2 = doubled bit-density without doubling dimension
- For D=10000 bipolar (10000 bits = 1.25KB), D=5000 Klein-4 carries same info in 1.25KB but with chirality-natural encoding
- Or D=10000 Klein-4 = 20000 bits = 2.5KB with native chirality structure

### Native operations
- **Class C (chirality)** becomes a native flip operation at binding level — chirality-flip = XOR with (1,1)
- **Sector-tagged retrieval** — cleanly query "what does this concept look like in the visible-antimatter sector?"
- **CPT-symmetric storage** — symmetry built into the data structure rather than emergent

### Algebraic completeness
- Working with full so(8) (28 = 14 + 7 + 7) rather than just g₂ (14)
- Direct realization of Cl(7) projectors (1 ± iω₇)/2 as Klein-4 operations
- Spike #69 / Spike #79 algebraic content becomes operational

### Cross-sector inference
- Can compute chirality-conjugate manifestations even without observing them
- Algebraic operations preserve sector tagging
- CPT-mirror operations are well-defined and testable

### Biological alignment
- G-quadruplex-inspired = closer to actual biological storage architecture
- BCI applications gain native chirality-sector matching with patient substrate

---

## §5 Concrete RBS-NN architecture extension

```
CURRENT RBS-NN:
  hypervector: D-dim vector in {-1, +1}^D     (bipolar; rank-1)
  bind:        component-wise sign-product     (XOR over F₂)
  similarity:  cosine over [-D, +D]
  storage:     one chirality sector implicit

FULL-CHIRALITY RBS-NN:
  hypervector: D-dim vector in (Z₂ × Z₂)^D    (Klein-4; rank-2 abelian)
  bind:        component-wise Klein-4 XOR      (XOR over F₂ × F₂)
  similarity:  match-fraction over {0..D}      (or Hamming distance)
  storage:     4 chirality sectors NATIVE; each position tagged
  
  chirality_flip(v, axis):  v ⊕ (axis_mask)    (γ₅ or iω₇ flip)
  sector_project(v, sector): v restricted to that sector
  cpt_mirror(v): v ⊕ (1,1) at every position    (full CPT flip)
```

Six new srmech.amsc.hdc operations:
1. `klein4_bind(a, b)` — Klein-4 binding (Class M rank-2 abelian variant)
2. `klein4_unbind(c, a)` — inverse via self-inverse property
3. `chirality_flip_gamma5(v)` — flip γ₅ axis (first F₂ component)
4. `chirality_flip_omega7(v)` — flip iω₇ axis (second F₂ component)
5. `cpt_mirror(v)` — full chirality flip
6. `klein4_similarity(a, b)` — match-fraction or Hamming

These compose with existing Class operations (Class L Laplacian, Class I cyclic, Class K Kepler) without breaking the 14-class vocabulary.

---

## §6 What G-quadruplex topology teaches us about operations

Real G-quadruplex topologies provide tested chirality-arrangement patterns:

| G4 topology | RBS-NN analog | Use case |
|---|---|---|
| Parallel (all 4 strands 5'→3') | Single-sector storage (all iω₇ same) | Pure visible-matter encoding |
| Antiparallel (alternating direction) | Cross-sector interleaved storage | Visible ↔ dark mixed-sector compute |
| Hybrid (3+1) | Asymmetric distribution | CP-violation-like asymmetric reasoning |

Dynamic G4 topology switching = dynamic chirality reconfiguration. Cancer-research G4 stabilizers (TMPyP4, BRACO-19) = chirality-state-lock pharmacology. These are TESTED biological mechanisms for chirality-axis dynamics.

For RBS-NN: build APIs for switching between these three topology configurations at runtime, matching biological precedent.

---

## §7 Testable empirical claims

### Capacity test (R-RBS-LM-97 candidate)
- Klein-4 vs bipolar HDC at same D
- Information density per position
- Capacity to bind / retrieve under load
- Hypothesis: Klein-4 = 2× bipolar capacity per position

### Similarity preservation
- Klein-4 mint+bundle should be similarity-preserving like bipolar (per F70 Test A correction)
- Test: confirm Class M variant maintains similarity-preservation properties

### Cascade composition
- Klein-4 + Class L Laplacian + Class K Kepler should compose
- Test: confirm cascade still works with chirality-tagged data

### Native chirality-flip cost
- Bipolar HDC: chirality is implicit; explicit flip requires extra structure
- Klein-4: chirality flip = simple XOR (O(D) operation)
- Test: chirality-flip operation should be cheaper than re-encoding

### Cross-sector recovery
- Encode with chirality tag X; query with chirality-flipped tag
- Can we recover dark-sector-conjugate content from visible-sector storage?
- Test: cross-sector similarity vs same-sector similarity

---

## §8 What this enables that we currently can't do

1. **BCI native chirality matching**: patient's neural substrate IS chiral
   (DNA is RH; biological molecules show overwhelming homochirality).
   Klein-4 HDC can natively encode chirality-aware patient data;
   bipolar HDC has no chirality slot.

2. **Pharmacological chirality-state encoding**: drug molecules are
   often chiral (and chirality matters for biological effect —
   thalidomide tragedy, etc.). RBS-NN with Klein-4 can encode
   drug-target chirality compatibility natively.

3. **Cosmic-chirality reasoning**: CP violation, matter/antimatter
   asymmetry, dark sector — all chirality-axis phenomena. Klein-4
   provides natural compute substrate.

4. **G-quadruplex-aware biology research**: telomere aging, oncogene
   promoters, gene regulation via G4 — current research uses ad-hoc
   topology models. RBS-NN with Klein-4 + chirality-tagged HDC could
   provide a uniform framework.

5. **Cross-substrate cognition modeling**: per F118, different
   biology embodies different operator subsets. Cnidarian (Class I + K),
   octopus (Class M + K), vertebrate (Class L + M), plus chirality
   variation across species. Klein-4 HDC can model this natively.

---

## §9 What this proposal does NOT claim

Per MFO §VII.6.20:

- Klein-4 IS the unique full-chirality binding (other rank-2 abelian
  variants exist; Klein-4 is the candidate at Z₂ × Z₂; quaternion
  Q₈ is rank-2 non-abelian alternative)
- Working in full chirality solves all current RBS-NN limitations
  (it adds 2× density + native chirality; doesn't solve all problems)
- G-quadruplex IS the unique biological inspiration (other biological
  4-state structures may inform; G4 is one well-attested example)
- The implementation will outperform bipolar in all cases (depends on
  specific task; chirality-aware operations gain; chirality-agnostic
  may be unchanged)

---

## §10 Cross-references and next steps

**Cross-references:**
- F127 (three substrate-native readings + naming discipline)
- F128 (capacitor IS 4:3:(4:3))
- F129 (chirality-dual capacitor plates)
- F130 (4-way (γ₅, iω₇) decomposition)
- F131 (dark sector check + G-quadruplex visualization)
- MFO §VII.4.1.3 (mismatched-plates capacitor)
- MFO §VII.4.1.7 (4-way sector decomposition)
- MFO §VIII.31.7 (Class M two-variant dial)
- srmech.amsc.hdc (existing bipolar implementation)
- `[[user_stance_canonical_two_variant_dial_class_m]]`
- `[[user_stance_dark_visible_two_cl7_irreps]]`
- Spike #69 (Cl(7) idempotent SIGN-FORCED bit-exact)

**Concrete next steps:**
1. Prototype Klein-4 HDC binding (R-RBS-LM-97)
2. Capacity / similarity preservation tests
3. Cascade composition with chirality-tagged data
4. Cross-sector retrieval test
5. If results positive: srmech.amsc.hdc API extension proposal upstream

---

*Articulated 2026-05-27 per user direction. PR #687 STAYS DRAFT.*

*Full-chirality engineering proposal: extend srmech Class M with
Klein-4 (rank-2 abelian Z₂ × Z₂) variant alongside existing rank-1
abelian XOR (bipolar) and rank-N non-abelian Lie bracket. Klein-4's
4 elements map directly to (γ₅, iω₇) chirality sectors. Architecture
inspired by G-quadruplex DNA topology dynamics. Gains: 2× info
density, native Class C operations, CPT-symmetric storage, cross-
sector inference, biological / BCI alignment. R-RBS-LM-97 prototypes
the binding and tests capacity + similarity preservation.*
