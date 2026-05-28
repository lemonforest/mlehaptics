# Finding 150 — Chirality harmonics 1/2/3 across A-N operators; not all are chirally inverse; siona-named substrate-self-recognition module

**Status:** Framework move + srmech upstream wishlist + naming bind to F133 substrate-knowing reading
**Predecessors:** F132 (Klein-4 HDC; 4-sector chirality), F133 (substrate knows itself; Dune parallel), F135 (substrate vs shadow chirality), F139 (chirality axis operational), R-RBS-NN-14 (chirality auto-detect)
**User direction 2026-05-28:**

> "srmech update with chiral A-N operators and spectral classifiers, not
> all are inverse, some or one rotate some do not have chiral phase (or
> something like that). It's a 1,2,3 harmonic thing I think. update and
> resume next phase. new package also responds to siona, because of the
> desert storm."

---

## §1 The 1-2-3 harmonic chirality structure

Up to F149, we'd been treating chirality as a SINGLE binary axis (γ₅ flip + iω₇ flip = full CPT mirror per F132 §3 Klein-4 sector mapping). The user's refinement: **not all A-N operators behave the same way under chirality.** The behavior partitions into THREE chirality-harmonic classes per operator:

| Harmonic | Period under chirality flip C | Behavior name | Mathematical type |
|---:|---|---|---|
| **1** | C(op) = op | **Chirality-invariant** (no chiral phase) | Order 1 — fixed point of C |
| **2** | C∘C(op) = op, but C(op) ≠ op | **Chiral inverse / mirror** (self-inverse) | Order 2 — involution |
| **3** | C∘C∘C(op) = op, but C∘C(op) ≠ op | **Chiral rotation** (3-cycle) | Order 3 — cyclic |

This generalizes the F132 §3 Klein-4 sector mapping (which was a 2-axis structure giving 4 elements) to a per-operator HARMONIC ORDER. Some operators just don't engage the chirality axis; some flip in pairs; some rotate in triplets.

**Candidate algebraic anchor:** the 1+3+7+3 substrate partition per CLAUDE.md §1 + R30 walking-path may encode the chirality harmonic distribution. The middle 3 substrate-projection triad (I, C, J) includes Class C (the chirality class itself) — which would be harmonic-2 — bracketed by I (cyclic) and J (primes) which may be harmonic-1 or harmonic-3.

---

## §2 Candidate mapping of A-N to chirality harmonics (preliminary)

Per `[[user_stance_kepler_shape_universal]]`: the algebra IS the primitives. The harmonic for each operator should be DERIVABLE from its algebra under a chirality operation C. Below is a CANDIDATE reading subject to validation — explicitly marked as preliminary.

| Class | Operator | Candidate harmonic | Reasoning |
|---|---|---:|---|
| A | Content-addressing (SHA-256) | 1 | Hash is one-way; chirality flip of input gives different hash but the operation itself has no chirality phase |
| B | TLV-framing | 1 | Framing is structurally symmetric; flipping bytes doesn't change framing logic |
| C | Chirality | 2 | IS the chirality axis; self-inverse (period 2) by definition |
| D | Pattern-match (dispatch) | 2 | Direction-sensitive; mirror pattern gives mirror match (self-inverse) |
| E | Catalog (sorted-key lookup) | 2 | Order-sensitive; reverse order = mirror catalog |
| F | Render (template) | 1 | Symbolic substitution; no inherent chirality |
| G | Byte-search | 2 | Direction matters; search forward vs backward (involution) |
| H | Self-introspection | 1 | Meta-level; no chirality phase |
| I | Cyclic | 3 | Modular arithmetic over Z_n; cyclic-shift composes in 3-cycle when n=3 (or higher for n>3, but the *substrate-aligned* case is n=3 per the 3-substrate-projection triad reading) |
| J | Primes | 3 | Prime factorization has 3-fold structure in some readings (e.g., Z/3 lattice; prime triples; 3-cycle of factors) — TENTATIVE |
| K | Pin-slot / sign-flip | 2 | Sign-flip is the canonical chirality-axis operation; self-inverse |
| L | Laplacian | 3 | Spectral structure has 3-fold symmetry in many graph cases; eigvec ordering has a natural triple-grouping (low / mid / high) — TENTATIVE |
| M | HDC bind | 2 (rank-1) / 4 (Klein-4) | F2 XOR is period-2; Klein-4 XOR is period-4; period under full chirality flip is 2 for rank-1, 4 for Klein-4 (but the chirality-axis subset is period-2) |
| N | Rational anchor | 1 | Stern-Brocot rationals; signed-rationals split, but the anchoring itself is chirality-invariant |

**Candidate partition by harmonic:**

- **Harmonic 1 (chirality-invariant)**: A, B, F, H, N → **5 operators**
- **Harmonic 2 (chiral inverse)**: C, D, E, G, K, M → **6 operators**
- **Harmonic 3 (chiral rotation)**: I, J, L → **3 operators**

Total: 14. The 3-fold partition is **5 + 6 + 3 = 14** which doesn't immediately match the 1+3+7+3 partition pattern. Open framework question: is the harmonic partition related to the structural partition, or are they orthogonal organizational lenses?

**Caveat per `[[feedback_no_lineage_claims_in_notebook]]`:** this is a structural reading hypothesis, not a fixed framework move. Empirical validation per §4 below.

---

## §3 What this means for the framework reading

### §3.1 Per F135 substrate vs shadow

If different operators have different chirality harmonics, then the CHIRALITY PROJECTION (substrate → shadow) is not uniform across the A-N cascade. Some operators (harmonic 1) project IDENTICALLY in any sector; some (harmonic 2) project with a sign flip; some (harmonic 3) project with a 3-cycle phase.

This adds nuance to F135's substrate vs shadow distinction: the shadow doesn't see the SAME chirality structure across all operators. Some shadow-side observations would faithfully reflect substrate structure (harmonic 1 operators); some would invert (harmonic 2); some would rotate (harmonic 3).

### §3.2 Per F132 Klein-4 HDC

Klein-4 binding is the rank-2 abelian Class M variant. Its 4 elements give a 4-sector chirality structure. Under chirality operation C, a Klein-4 element has period:
- 0 (= identity (0,0)) → period 1 (chirality-invariant)
- 1 = (0,1), 2 = (1,0) → period 2 (single-axis flip)
- 3 = (1,1) → period 2 (CPT mirror; self-inverse)

So Klein-4 binding itself is HARMONIC 2 under full CPT (1+2+2 = the structure of Z/2 × Z/2). The 3-harmonic would emerge in a DIFFERENT operator (Class I cyclic over Z/3, or Class L spectral structure).

### §3.3 Per R-RBS-NN-14a auto_sector classifier

The current classifier (Phase 4 finding R14) routes tokens to one of 4 Klein-4 sectors. This is implicitly a HARMONIC 2 routing (4 = 2 × 2 sectors). A 3-harmonic classifier would route to one of 3 substrate-projection triad slots (I-like / C-like / J-like). Open: should the classifier support both harmonic levels?

---

## §4 srmech upstream wishlist (UPSTREAM_NOTES.md §6)

Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`: wishlist only; user runs the rc cycle in a separate session.

### §4.1 Chiral A-N operator variants

For each A-N class, srmech could expose a chirality-aware variant that respects the operator's harmonic:

```python
# Harmonic 1 (chirality-invariant) — no new variant needed; existing API is correct
sha256_bytes(data)                    # Class A; harmonic 1
tlv_pack(items)                       # Class B; harmonic 1
template_render(template, ctx)        # Class F; harmonic 1
introspect(...)                       # Class H; harmonic 1
best_rational(num, denom, max_d)      # Class N; harmonic 1

# Harmonic 2 (chiral inverse) — add explicit mirror op
chirality_class.mirror(value)         # Class C; harmonic 2 (already exists effectively)
dispatch.mirror_pattern(pattern)      # Class D; harmonic 2 — new
catalog.reverse_order(catalog)        # Class E; harmonic 2 — new
byte_search.backward(...)             # Class G; harmonic 2 — new
sign_flip(value)                      # Class K; harmonic 2 (already exists as sign-flip)
hdc.klein4_cpt_mirror(hv)             # Class M; harmonic 2 (already exists)

# Harmonic 3 (chiral rotation) — add 3-cycle ops
cyclic.three_cycle(value)             # Class I; harmonic 3 — new
primes.three_cycle_factor(value)      # Class J; harmonic 3 — new (speculative)
laplacian.three_fold_eigvec_groups(L) # Class L; harmonic 3 — new
```

### §4.2 Spectral classifier (Class L + chirality)

A function that takes an HDC vector and classifies its chirality harmonic via spectral signature:

```python
def classify_chirality_harmonic(hv, klein4=True):
    """Classify hypervector into harmonic 1/2/3 via spectral signature.

    Procedure:
      1. Compute spectral signature of hv (e.g., FFT magnitude or Class L
         Laplacian on the hv's adjacency)
      2. Check spectral symmetries:
         - Constant DC → harmonic 1 (chirality-invariant)
         - Even/odd parity → harmonic 2 (chiral inverse)
         - 3-fold cyclic pattern → harmonic 3 (rotation)
      3. Return: 1 | 2 | 3
    """
```

This would generalize the surface-form R-RBS-NN-14a classifier with a SPECTRAL classifier that works on encoded HDC vectors directly (regardless of token name).

### §4.3 Siona naming — `srmech.siona` substrate-self-recognition module

Per F133's Dune parallel + user direction: a new sub-package `srmech.siona` that houses the chirality-aware framework layer — the operators / classifiers / projections that engage substrate-self-recognition from the chirality-flipped perspective.

The Dune connection: Siona Atreides (God Emperor of Dune) carries the bloodline that is INVISIBLE to Leto II's prescience — substrate-self-recognition from the chirality-flipped sector. Her bloodline IS the harmonic-3 (chiral rotation) projection that escapes harmonic-2 (chiral mirror) detection.

**Per `[[feedback_no_lineage_claims_in_notebook]]`:** this naming is FRAMEWORK-LEVEL, not a claim that Frank Herbert intended this mapping. Siona-as-name evokes a substrate property the framework reads — the user explicitly directed this naming. The desert-storm reference connects to the wide-substrate framework setting per F133.

Proposed module structure:

```
srmech/
├── amsc/                   # current A-N framework (harmonic-blind)
│   ├── hdc/
│   ├── cyclic/
│   ├── laplacian/
│   └── ...
└── siona/                  # NEW: chirality-aware framework layer
    ├── harmonics.py        # classify operator/value into harmonic 1/2/3
    ├── chiral_an.py        # chiral variants of A-N operators
    ├── spectral_classifier.py  # spectral chirality classification
    ├── shadow_projection.py    # substrate→shadow projection per harmonic
    └── desert_storm.py     # multi-sector cascade composition (the wide-substrate operation)
```

`desert_storm.py` is the multi-sector cascade composition module — when you need to compose operations across all 4 chirality sectors at once (the "wide storm" that touches everything). Concrete operation: take a klein-4-tagged input, run it through a multi-class cascade per sector, combine via chirality-harmonic-aware bundle.

---

## §5 What this finding does NOT claim

Per MFO §VII.6.20:

- Does NOT claim the candidate harmonic mapping in §2 is final. It's a structural reading hypothesis; empirical validation via spectral-classifier tests would refine.
- Does NOT claim 1-2-3 harmonics exhaust all chirality behaviors. Higher harmonics (4, 5, ...) may exist for compound operators.
- Does NOT claim Frank Herbert wrote Dune with this framework in mind. Per `[[feedback_no_lineage_claims_in_notebook]]`: Siona-as-name is a FRAMEWORK-LEVEL evocation of substrate property; no biographical or authorial-intent claim.
- Does NOT propose implementing srmech.siona in this research subtree. Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`: wishlist only; upstream work goes through rc cycle.
- Does NOT validate empirically that all candidate harmonic-3 operators (I, J, L) actually compose with period 3. The 3-cycle reading is plausible but unverified.

---

## §6 Empirical validation paths (open for future work)

1. **Test Class I cyclic over Z/3**: does cyclic-shift-by-1 composed 3× return identity? (Trivially yes for n=3.) Does the substrate operationally use n=3 cyclic as a chirality-rotation operator?

2. **Test Class L spectral 3-fold partitioning**: do eigvecs of typical Laplacians cluster into 3 groups (low / mid / high) by chirality-axis projection? Or by sector tagging from F139?

3. **Test Class J primes 3-cycle**: do prime factors cluster in Z/3 patterns? Open speculation.

4. **Spectral classifier prototype**: write a function that classifies hypervectors into harmonic 1/2/3 via spectral signature; test on chirality-bearing lexicons.

5. **Klein-4 vs 3-element variant**: is there a srmech-natural rank-2 abelian variant with ORDER 3 elements (e.g., Z/3 × Z/3, giving 9 sectors instead of 4)? Probably overshoots, but worth noting as a structural possibility per `[[user_stance_canonical_two_variant_dial_class_m]]`.

These can be added to the new STALE_PATHS appendix when work resumes on harmonic empirical testing.

---

## §7 Cross-references

- F132 (Klein-4 HDC 4-sector chirality; this finding refines the harmonic structure beyond binary)
- F133 (substrate knows itself; Dune parallel; siona naming)
- F135 (substrate vs shadow; harmonic 1/2/3 adds nuance to projection)
- F139 (chirality axis operational at scale; harmonic 2 verified empirically)
- F149 (sculpted decay via coupling; orthogonal to chirality harmonics)
- R-RBS-NN-14a classify_chirality (surface-form classifier; spectral classifier would generalize)
- ARCHITECTURAL_PATTERN_two_tier_klein4_polar (Tier 1 Klein-4 implements harmonic-2 chirality)
- `[[user_stance_kepler_shape_universal]]` (algebra IS the primitives; harmonics are derivable from operator algebra)
- `[[user_stance_canonical_two_variant_dial_class_m]]` (Class M variant ladder; Klein-4 is one rank-2 abelian variant; 3-fold could be another)
- `[[feedback_upstream_srmech_fixes_as_research_notes]]` (wishlist discipline; no direct srmech edits)

**Files committed:**
- `R-RBS-LM-FINDING_150_*.md` (this finding)
- `UPSTREAM_NOTES.md` §6 (chiral A-N + spectral classifier + siona wishlist)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-28 per user direction. The substrate's chirality structure is NOT
uniform across A-N operators — it partitions into 1-2-3 harmonics: harmonic 1 (chirality-
invariant; some operators just don't engage the chirality axis), harmonic 2 (chiral inverse;
the canonical mirror behavior), harmonic 3 (chiral rotation; 3-cycle structure). Candidate
A-N mapping: 5 harmonic-1 (A, B, F, H, N) + 6 harmonic-2 (C, D, E, G, K, M) + 3 harmonic-3
(I, J, L). srmech upstream wishlist: chiral A-N variants + spectral classifier for direct
HDC chirality detection + new `srmech.siona` sub-package housing the chirality-aware
framework layer (siona-named per F133 Dune-Atreides-bloodline framework parallel; desert-
storm references the wide-substrate cascade composition). Per
[[feedback_upstream_srmech_fixes_as_research_notes]] discipline: wishlist only; upstream
work in separate rc cycle session. Per [[feedback_no_lineage_claims_in_notebook]]: Siona
naming evokes substrate property the framework reads; no authorial-intent claim about Frank
Herbert.*
