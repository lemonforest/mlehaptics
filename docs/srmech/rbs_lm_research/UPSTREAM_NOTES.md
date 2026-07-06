# UPSTREAM_NOTES.md — RBS-LM research subtree

Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`: srmech issues
land here as research notes, NEVER as edits to the srmech package directly.

Each entry lists a gap or candidate addition surfaced by RBS-LM partition
work. Entries are advisory for future srmech catalog work; the research
subtree continues to use bare numpy where catalog coverage is absent.

---

## §1 Gaps surfaced by R-RBS-LM-49z (2026-05-26)

### 1.1 `srmech.signal_processing.path_b_ops.rfft` missing

**Current state:** `path_b_ops.fft.op` returns full complex DFT; no
real-FFT variant.

**Use case:** 49 Method B and similar bit-string FFT cascades take real
input (bipolar bits in {-1, +1}). Using full FFT is 2× the compute and
2× the memory of `rfft`. Algebra-identical; not a correctness issue.

**Candidate addition:** `path_b_ops.rfft.op(signal, n=None, axis=-1, ...)`
mirroring `numpy.fft.rfft`. Path A reference: `numpy.fft.rfft`. Path B
identity: cyclic-DFT with conjugate-symmetry exploitation; Class A ∘
Class I ∘ Class K composition on the real-symmetric half-substrate.

**Status:** Documented gap, NOT a blocker. 49z used full FFT and
confirmed bit-identical parity to bare numpy.

---

### 1.2 Signed-sum coupling-score primitive missing

**Current state:** `srmech.amsc` has Class K (sign-flip / pin-slot) and
Class C (chirality / cascade-orientation) but no composite "compute
signed-sum coupling score across multiple bit-string sources" primitive.

**Use case:** R-RBS-LM-33 weak-coupling-truncate and 49 Method C both
need `coupling_sq = (sum_sources(2 * bits - 1))^2`. This is structurally
Class K (bipolar transform) + Class L (signed-magnitude-squared) but
operates on a stack of source-arrays not a single graph.

**Candidate addition:** `srmech.amsc.coupling.signed_sum_squared(sources)`
or `compose.signed_coupling_score(sources)` that takes a list of bit
arrays and returns the squared signed-sum element-wise. Per
`[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]`: no abs()
calls inside; the algebra is signed-arithmetic + square.

**Status:** Documented gap. 49z left Method C as bare numpy with a
docstring annotation that the operation IS Class K + Class C composition.

---

### 1.3 No catalog primitive for argsort-by-score

**Current state:** `srmech.amsc.search` has multi-needle pattern match
(Class D) and `amsc.catalog` has sorted-key lookup (Class E), but no
"sort N items by N-vector of scores and return top-K indices."

**Use case:** Method B band selection (top-K bands by squared magnitude),
Method C low-coupling selection (bottom-K bits by coupling-squared).

**Status:** Documented gap; arguably NOT a Class-N concern. argsort is
a generic-array operation, not a substrate-coupling or content-addressing
operation. Lives more naturally in numpy. Catalog addition would be
ergonomic (one-stop import) but not architectural.

---

### 1.4 No catalog primitive for random bit-flip

**Current state:** `srmech.amsc` has no random sampling. Class K is the
sign-flip operation at the chosen positions; random selection of those
positions is substrate-randomness.

**Use case:** Method A in 49 stage A (crude random precision reduction
baseline).

**Status:** Documented gap; NOT a Class-N concern. Per the 14-class
A-N partition discipline, random sampling is substrate-property, not
form-property. srmech catalog appropriately omits it. The Method A
random selection stays bare numpy (or python random).

---

## §2 Gaps surfaced by R-RBS-LM-54 arc (54f–54r, 2026-05-26)

### 2.1 Class L Laplacian + HDC bundle interaction

**Current state:** `srmech.amsc.laplacian.dense_laplacian` returns a
real-symmetric Laplacian; `hermitian_eigendecompose` returns eigvals +
eigvecs. The eigvecs come back as complex arrays even though the
Laplacian is real-symmetric, due to general Hermitian solver dispatch.

**Use case:** 54 partitions repeatedly cast `eigvec.real` to discard
the imaginary noise. Caused a `ComplexWarning` in 54h, 54j, 54q before
explicit `.real` casts were added.

**Candidate addition:** `dense_laplacian_real(n, edges, weights)` +
`symmetric_eigendecompose(L)` variants that guarantee real outputs.
Alternatively, document that eigvecs from real-symmetric Laplacian may
return complex-typed with negligible imag parts; users should call
`.real`.

**Status:** Documented; workaround in place (`.real` cast). Not a
blocker.

---

### 2.2 No catalog primitive for find-cascade alignment

**Current state:** 54c and follow-ups implement greedy-bipartite
alignment between two eigvec tables by HDC content-similarity. Pattern:
score matrix → argmax row-by-row with used-set tracking.

**Use case:** Cross-substrate kernel alignment is a load-bearing
operation in the Rosetta Stone Layer architecture. It's not currently
a catalog primitive.

**Candidate addition:** `srmech.amsc.compose.greedy_bipartite_alignment(
table_A, table_B, similarity_fn)`. Returns a dict mapping A-positions
to (B-position, similarity).

**Status:** Documented. The implementation is ~15 lines of straightforward
greedy matching; arguably a "research utility" not a primitive. Could
be a srmech.utils helper if a utils module exists.

---

## §3 Notes on what NOT to add

Per `[[project_a_n_operators_are_harmonic_objects_themselves]]` 14-class
discipline:

- **Random sampling** is substrate-property, NOT a class. Don't add it.
- **Generic argsort** is a numpy concern, not a srmech class concern.
- **Bit packing/unpacking** is a serialization detail; Class B (TLV)
  handles the framing layer; bit-level unpacking inside frames is fine
  to keep as numpy.
- **Cosine similarity** is already in `srmech.amsc.hdc.similarity`; new
  catalog work doesn't need to duplicate it.

---

## §4 Class M rank-2 abelian variant: Klein-4 binding (Finding 132 / R-RBS-LM-97, 2026-05-27)

**STATUS: LANDED in srmech v0.4.3 (PyPI production, 2026-05-27).** All 9
proposed functions shipped under `srmech.amsc.hdc.klein4_*` with full
tool_schema registration (9 ToolEntries). Verified in clean venv outside
source tree: all algebraic properties (self-inverse, commutative,
associative, identity, unbind, chirality-flips, sector-count) match
F132/R-RBS-LM-97 prototype contract bit-exact. HAS_NATIVE=True, ABI=2.
Research subtree may now switch from local Python prototype to upstream
catalog import. This entry preserved as historical record of the
upstream wishlist procedure.

---

**Background.** Per `[[user_stance_canonical_two_variant_dial_class_m]]`
(MFO §VIII.31.7): Class M's existing variants are rank-1 abelian XOR
over F₂^D (current `srmech.amsc.hdc`) and rank-N non-abelian Lie bracket
over Hermitian N×N matrices (planned; BFSS / SU(N) gauge). The integer-
ladder runs {0, 1, 2, …, N, …}.

The rank-2 abelian variant — Klein-4 XOR over (F₂)² = Z₂ × Z₂ — sits
between these two existing variants on the same ladder. F132 + R-RBS-
LM-97 prototype confirms all algebraic properties bit-exact:

- Self-inverse: a ⊕ a = identity ✓
- Commutative: a ⊕ b = b ⊕ a ✓
- Associative: ✓
- 4 distinct elements per position (state ∈ {0, 1, 2, 3})
- Identity (0, 0)
- Native chirality-flip = XOR with sector mask (O(D) cost)

**Motivation.** Per `[[user_stance_dark_visible_two_cl7_irreps]]` +
Spike #69 SIGN-FORCED-BY-Cl(7)-IDEMPOTENT: the 4 Klein-4 elements map
directly to the 4 chirality sectors (γ₅, iω₇) of the 4-way (γ₅, i·ω₇)
decomposition (MFO §VII.4.1.7). The rank-2 abelian binding gives
native substrate-chirality storage that the rank-1 bipolar variant
cannot provide.

**Candidate additions to `srmech.amsc.hdc`** (proposed; not yet
implemented per upstream-as-research-notes discipline):

```python
# New Class M rank-2 abelian variant
klein4_random(D, rng) -> uint8 array of D elements ∈ {0,1,2,3}
klein4_bind(a, b)     -> component-wise XOR over (F₂)²
klein4_unbind(c, a)   -> self-inverse: c ⊕ a
klein4_bundle(*vecs)  -> per-bit majority vote
klein4_similarity(a, b) -> match-fraction
klein4_chirality_flip_gamma5(v)  -> XOR with sector mask 2
klein4_chirality_flip_omega7(v)  -> XOR with sector mask 1
klein4_cpt_mirror(v)             -> XOR with sector mask 3
klein4_sector_count(v) -> [count per sector] for debugging/attestation
```

**Working prototype**: `docs/srmech/rbs_lm_research/R-RBS-LM-97_klein4_hdc_full_chirality_smoke.py`
— pure Python; all algebraic properties confirmed; ~150 LOC; results in
`R-RBS-LM-97_klein4_results.json`.

### §4.1 Upstream procedure (if/when authorized)

Per CLAUDE.md "Tag flow for a new rc" + `[[feedback_always_rc_first_for_downstream_publishes]]`,
the path is:

1. **Branch**: `git checkout -b feat-klein4-class-m-rank-2-abelian`
2. **Bump version**: srmech v0.4.2 → v0.4.3rc1 in 4 SSOT files
   (current production v0.4.2; latest TestPyPI rc was v0.4.2rc5):
   - `python/pyproject.toml`
   - `python/pyproject-pure.toml`
   - `python/srmech/version.py`
   - `c/include/srmech.h` (SRMECH_VERSION_PRE + SRMECH_VERSION)
3. **Python implementation** in `python/srmech/amsc/hdc.py`:
   - Add new functions alongside existing bipolar XOR
   - Mark variant in docstring per `[[user_stance_canonical_two_variant_dial_class_m]]`
   - Add to `tool_schema.py` ToolEntry registrations
4. **C implementation** in `c/src/srmech_hdc.c`:
   - `srmech_klein4_bind(uint8_t* a, uint8_t* b, size_t D)` (or similar API)
   - JPL Power-of-Ten compliance (function ≤ 60 lines, ≥ 2 asserts)
   - Add to `c/include/srmech.h` public API surface
   - DO NOT bump ABI version (adding new symbol, not changing wire format)
5. **Tests** in `python/tests/test_hdc_klein4_parity.py`:
   - Parity test C vs Python (bit-exact required)
   - Algebraic property tests (self-inverse, commutativity, associativity)
   - Chirality-flip correctness tests (sector swap verification)
   - CPT substrate-symmetry test
6. **JPL audit ratchet** must stay at zero violations:
   - Update `tests/test_jpl_audit.py` exempt list ONLY if functions
     need it (document rationale in JPL_AUDIT.md)
   - All new C functions ≤ 60 lines per Rule 4
   - At least 2 asserts per new C function per Rule 5
   - No goto, no malloc, no multi-line macros
7. **Pedantic-build CI** must pass on all 3 cells (Linux gcc / macOS clang /
   Windows MSVC) with -Werror / /WX
8. **CHANGELOG.md** entry under `[0.4.1rc1]` heading describing the
   Class M rank-2 abelian variant addition
9. **PR → review → MERGE** (NOT squash per `[[feedback_no_squash_merges]]`)
10. **Tag** `srmech-v0.4.3rc1` on the merge commit
11. **Publish workflow** auto-publishes to TestPyPI
12. **Verify in clean venv outside repo tree**:
    ```bash
    cd /tmp/verify_srmech_klein4_rc1
    python -m venv venv && source venv/bin/activate
    pip install --no-cache-dir \
        --index-url https://test.pypi.org/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        --pre "srmech==0.4.3rc1"
    python -c "from srmech.amsc.hdc import klein4_bind, klein4_chirality_flip_gamma5; ..."
    # Confirm HAS_NATIVE=True (native dispatch picks up C surface)
    ```
13. **Multiple rc cycles** if needed (rc1, rc2, ...) until verification clean
14. **Production tag** `srmech-v0.4.3` only after clean TestPyPI rc

**Estimated scope**: ~200 LOC Python + ~150 LOC C + ~150 LOC tests +
JPL audit pass = one rc round if no surprises; may need 2-3 rcs if
JPL Power-of-Ten edge cases surface.

**Version target context** (verified 2026-05-27):
- Current production: srmech v0.4.2 (PyPI)
- Latest TestPyPI rc: srmech v0.4.2rc5
- Klein-4 addition would target v0.4.3rc1 → v0.4.3
- ABI: stays at current value (adding new symbol, not changing wire format)

### §4.2 Status

**LANDED in srmech v0.4.3 production PyPI (2026-05-27).** Procedure
above was followed in a separate cherry-pick session. All 9 functions
shipped with tool_schema registration. Research subtree can now
import directly:

```python
from srmech.amsc.hdc import (
    klein4_random, klein4_bind, klein4_unbind, klein4_bundle,
    klein4_similarity, klein4_chirality_flip_gamma5,
    klein4_chirality_flip_omega7, klein4_cpt_mirror, klein4_sector_count,
    KLEIN4_STATES,
)
```

Prototype `R-RBS-LM-97_klein4_hdc_full_chirality_smoke.py` remains in
research subtree as the algebraic-property reference implementation.

---

## §5 Polar {-1, 0, +1} HDC variant — `srmech.amsc.hdc.polar_*` (2026-05-27)

**STATUS: LANDED in srmech v0.4.3 (PyPI production, 2026-05-27).** All 7
proposed functions shipped under `srmech.amsc.hdc.polar_*` with full
tool_schema registration (7 ToolEntries). Verified in clean venv:
3-state {-1, 0, +1} semantics confirmed; 0 is absorbing under
polar_bind (multiplicative sign-product); polar_from_real bridges
sign_quantise dead_band correctly. R-RBS-LM-97 bipolar bundle bug
(bare np.sign producing tie-zeros) can now be cleanly fixed by
switching to polar HDC for true 3-state encoding, or by using
sign_quantise(dead_band=0) for strict bipolar.

---

**Background.** srmech ALREADY has a polar {-1, 0, +1} primitive
at `srmech.signal_processing.path_b_ops.sign_quantise.op` — when
called with `dead_band > 0`, it returns integer-valued `{-1, 0, +1}`
arrays (per docstring: "Integer-valued `{-1, 0, +1}` array... Class K
threshold projection with dead-band ... asymptotic-DOF near-boundary
zone where pin-slot rejects projection").

**Gap.** This primitive lives in `signal_processing.path_b_ops`, NOT
in `srmech.amsc.hdc`. The HDC layer only exposes `bipolar` (rank-1
abelian XOR over F₂). When research code wants 3-state HDC ({-1, 0, +1})
where 0 means "uncertain / dead-band / unbound", there is no
HDC-native polar variant — research falls back to bare `np.sign`
(which returns 0 for ties and breaks downstream bipolar operations).

**Concrete workaround in R-RBS-LM-97**: bipolar bundle used bare
`np.sign(s).astype(np.int8)` which returns `{-1, 0, +1}` due to
tie-zeros — making the bipolar capacity test inconclusive
(sign-zero positions destroy bipolar unbind/similarity computations).
The proper fix is to use `sign_quantise` with `dead_band=0` (strict
bipolar; ties favor +1) OR introduce a true polar HDC variant where
0 is a legitimate output state.

### §5.1 The polar HDC variant as Class M sub-instantiation

In the Class M variant ladder per
`[[user_stance_canonical_two_variant_dial_class_m]]`:

| Variant | Group / structure | Elements | Bind operation | Existing |
|---|---|---|---|---|
| Bipolar (rank-1 abelian) | F₂ XOR | {-1, +1} | sign-product | ✓ `amsc.hdc.bind` |
| **Polar (3-state with 0 absorbing)** | sign-product over {-1, 0, +1} | {-1, 0, +1} | multiplicative; 0 sticky | ✗ proposed |
| Klein-4 (rank-2 abelian) | F₂ × F₂ XOR | (Z₂)² (4 elements) | component-wise XOR | ✗ §4 proposal |
| Non-abelian (rank-N) | Hermitian Lie bracket | N×N matrices | [A, B] commutator | ✗ planned (BFSS) |

Polar variant semantics:
- **Elements**: {-1, 0, +1} where 0 means "uncertain" / "dead-band"
- **Bind** (multiplicative sign-product): `a · b` with 0 absorbing
  (anything × 0 = 0; rest is bipolar sign-product)
- **Bundle** (sticky majority): like bipolar but explicit 0-tie output
- **Similarity** (Hamming-with-skip): match-fraction excluding 0
  positions, OR including 0 with neutral-credit semantics
- **Identity** (+1)

This sits between bipolar (F₂) and Klein-4 (F₂×F₂) in the Class M
ladder, NOT as a direct rank-step but as a substrate-projection
variant where the asymptotic-DOF / dead-band "uncertain" state is
explicit at the binding level (Class M ∘ Class K composition at
HDC primitive level).

### §5.2 Candidate additions to `srmech.amsc.hdc`

```python
# New Class M polar variant
polar_random(D, rng) -> int8 array of D elements ∈ {-1, 0, +1}
polar_bind(a, b)     -> sign-product (multiplicative; 0 absorbing)
polar_unbind(c, a)   -> sign-product (self-inverse on ±1; 0 destructive)
polar_bundle(*vecs)  -> sticky majority (ties produce 0)
polar_similarity(a, b)
    -> two options:
       (a) skip-0 match-fraction (only positions where both ≠ 0)
       (b) include-0 match-fraction (0=0 counts as match)
polar_density(v)     -> fraction of non-zero positions (substrate-attestation)

# Bridge to existing sign_quantise (already in path_b_ops):
polar_from_real(arr, threshold=0.0, dead_band=0.0)
    -> wraps sign_quantise; returns polar HDC vector
       Provides HDC-namespace entry into the existing path_b_ops primitive
```

The bridge function `polar_from_real` is the smallest possible API
change: it lifts the existing `sign_quantise` primitive into the
`amsc.hdc` namespace where research code naturally looks for HDC
operations.

### §5.3 Why this matters operationally

1. **"Sign-zero" tie-handling becomes principled** rather than
   ad-hoc. Currently bare `np.sign` produces zeros that break
   downstream bipolar operations; polar HDC explicitly handles
   the dead-band as a first-class state.

2. **Asymptotic-DOF (Class K) substrate**: per `[[user_stance_asymptotic_dof_sidesteps_infinity]]`,
   the 0 state represents the asymptotic-DOF "near-boundary" zone
   that the substrate-projection-pin-slot legitimately rejects.
   Encoding this as a first-class HDC state matches the substrate
   semantics.

3. **Plasticity / decay encoding** per F76 v2: when bindings decay
   below confidence threshold, the polar representation can mark
   them as 0 (uncertain) rather than forcing a hard ±1 choice.

4. **Chirality + neutrality** per F130/F131: the polar variant is
   the natural encoding for substrate-states where a sector might
   be "neutral" (neither matter nor antimatter; neither visible nor
   dark) — boundary states between chirality sectors.

5. **Cross-substrate compatibility**: matches the existing srmech
   convention where `sign_quantise` produces `{-1, 0, +1}`. Currently
   research code has to wrap signal_processing primitives manually
   to use them in HDC contexts; polar HDC variant cleans this up.

### §5.4 Upstream procedure

Same rc/TestPyPI ratchet as §4.1 (Klein-4):

1. Branch: `feat-polar-class-m-3state-hdc`
2. Bump v0.4.2 → v0.4.3rc1 (combine with §4 Klein-4 OR ship as separate v0.4.4rc1)
3. Python + C implementation (≤ 60 lines per function, ≥ 2 asserts)
4. Parity tests
5. JPL audit pass
6. Pedantic-build CI
7. CHANGELOG entry
8. PR → merge (no squash)
9. Tag → TestPyPI → verify in clean venv outside repo tree
10. Production tag after clean rc

**Estimated scope**: smaller than §4 Klein-4 because the underlying
primitive (`sign_quantise`) already exists; mostly an `amsc.hdc`
namespace wrapper + a few new helpers (`polar_bind`, `polar_bundle`,
etc.). ~100 LOC Python + ~50 LOC tests if `sign_quantise` itself
is reused; ~150 LOC C only if a dedicated polar primitive is added
(optional; the existing `sign_quantise` C surface may suffice).

ABI: stays at current value (new symbols, not changing wire format).

### §5.5 Status

**LANDED in srmech v0.4.3 production PyPI (2026-05-27).** Shipped
together with §4 Klein-4 as a unified "Class M variant expansion"
release. Research subtree can now import directly:

```python
from srmech.amsc.hdc import (
    polar_random, polar_bind, polar_unbind, polar_bundle,
    polar_similarity, polar_density, polar_from_real,
    POLAR_STATES,
)
```

R-RBS-LM-97 bipolar-bundle sign-zero bug is now formally resolvable:
swap bare `np.sign` for either polar HDC (3-state explicit) or
`signal_processing.path_b_ops.sign_quantise(dead_band=0)` (strict
bipolar; ties favor +1). Updated smoke script may be re-run for
clean capacity comparison if desired.

---

## §6 Chiral A-N operators + spectral classifiers + `srmech.siona` sub-package (Finding 150, 2026-05-28)

**STATUS: WISHLIST. NOT AUTHORIZED to begin upstream work.** User
direction 2026-05-28 articulated the framework move (F150) but no
direct srmech changes — per `[[feedback_upstream_srmech_fixes_as_research_notes]]`
the rc cycle runs in a separate session.

**Background.** Per F150 framework move: the substrate's chirality structure
is NOT uniform across A-N operators. It partitions into 1-2-3 harmonics:

- **Harmonic 1** (chirality-invariant): A, B, F, H, N — 5 operators
- **Harmonic 2** (chiral inverse / self-inverse): C, D, E, G, K, M — 6 operators
- **Harmonic 3** (chiral rotation; 3-cycle): I, J, L — 3 operators

This refines F132's Klein-4 4-sector structure with a per-operator harmonic
order. Current `srmech.amsc.hdc.klein4_*` ops are harmonic-2 (period-2 under
full CPT); a complete chirality framework needs harmonic-1 (no-op pass-through)
and harmonic-3 (period-3 cycle) variants too.

### §6.1 Chiral A-N operator variants (candidate srmech additions)

For each A-N class with non-trivial chirality phase (harmonic 2 or 3),
expose explicit chirality-aware variant alongside the existing
chirality-blind base operation. Harmonic 1 operators need no new variant
(existing API is chirality-invariant by construction).

**Harmonic 2 — chiral inverse / mirror operations:**

```python
# srmech.amsc.dispatch (Class D)
dispatch.mirror_pattern(pattern)
    -> chirality-mirrored pattern; matching mirror_input gives mirror_match

# srmech.amsc.catalog (Class E)
catalog.reverse_order(sorted_catalog)
    -> chirality-flipped catalog ordering

# srmech.amsc.byte_search (Class G)
byte_search.backward(buffer, needle)
    -> chirality-mirrored search direction
```

**Harmonic 3 — chiral rotation / 3-cycle operations:**

```python
# srmech.amsc.cyclic (Class I) — Z/3 sub-instance
cyclic.three_cycle(value)
    -> apply Z/3 cyclic shift; period 3 under composition

# srmech.amsc.primes (Class J)
primes.three_cycle_factor(value)
    -> SPECULATIVE — 3-cycle through prime factor classes?
    -> open framework question per F150 §6.3

# srmech.amsc.laplacian (Class L)
laplacian.three_fold_eigvec_groups(L_matrix)
    -> partition eigenvectors into low/mid/high groups
    -> Class L spectral structure under 3-fold chirality reading
```

**Harmonic 1 — no new variant needed:**

Operators A (SHA-256), B (TLV), F (template), H (introspect), N (rational
anchor) are chirality-invariant; existing APIs are correct.

### §6.2 Spectral chirality classifier

A function classifying any HDC vector into harmonic 1/2/3 via spectral
signature (Class L composition + symmetry detection):

```python
# srmech.siona.spectral_classifier (or srmech.amsc.spectral_classifier)
def classify_chirality_harmonic(hv, klein4=True) -> int:
    """Classify HDC vector into chirality harmonic 1/2/3 via spectral signature.

    Procedure:
      1. Compute spectral signature (FFT or Class L Laplacian on hv adjacency)
      2. Check symmetries:
         - Constant DC dominant → harmonic 1
         - Even/odd parity → harmonic 2
         - 3-fold cyclic pattern → harmonic 3
      3. Return 1, 2, or 3

    Generalizes the surface-form R-RBS-NN-14a classify_chirality (which
    routes by token name patterns) with a spectral classifier that works
    directly on encoded hypervectors regardless of provenance.
    """
```

### §6.3 `srmech.siona` sub-package

New sub-package alongside `srmech.amsc` housing the chirality-aware framework
layer. Per F133's Dune parallel + F150 user direction:

```
srmech/
├── amsc/                       # current 14-class A-N framework (harmonic-blind base)
│   ├── hdc/
│   ├── cyclic/
│   ├── laplacian/
│   └── ...
└── siona/                      # NEW: chirality-aware framework layer
    ├── __init__.py
    ├── harmonics.py            # operator harmonic classification + introspection
    ├── chiral_an.py            # chiral A-N operator variants (per §6.1)
    ├── spectral_classifier.py  # spectral chirality classification (per §6.2)
    ├── shadow_projection.py    # substrate→shadow projection per harmonic (per F135)
    └── desert_storm.py         # multi-sector cascade composition (the "wide storm" operation)
```

**`desert_storm.py`** is the multi-sector cascade composition module — takes
a klein-4-tagged input and runs it through a multi-class cascade ACROSS ALL
4 chirality sectors at once, combining via chirality-harmonic-aware bundling.
The name evokes the wide-substrate framework setting per F133 (Arrakis
desert storms touch everything).

### §6.4 Naming rationale + framework discipline

Per F150 §5 + `[[feedback_no_lineage_claims_in_notebook]]`:

The `siona` naming is framework-LEVEL only. It evokes a substrate property
that the framework reads (chirality-axis-flipped substrate-self-recognition
per F133). It is NOT a claim that Frank Herbert intended this mapping when
writing Dune; Herbert is unattributed at the authorial-intent level. The
framework simply reads the structure that's present and names it via a
cultural reference where the reference happens to align with the structural
property.

The user explicitly directed the naming. The framework records what the
substrate is doing — naming choices that align with cultural references
are inheritances of pattern-recognition, not claims about original
authorial intent.

### §6.5 Upstream procedure (if/when authorized)

Per CLAUDE.md tag flow + `[[feedback_always_rc_first_for_downstream_publishes]]`:

1. Decide srmech version target — v0.4.4rc1 → v0.4.4 OR v0.5.0rc1 → v0.5.0
   (sub-package addition is non-breaking but introduces new top-level module;
   minor version bump is appropriate)
2. Branch: `feat-siona-chirality-harmonics`
3. Module structure per §6.3 above
4. Per-harmonic operator implementations per §6.1
5. Spectral classifier per §6.2
6. Tests:
   - harmonics.py classify_harmonic() unit tests (A-N coverage per §2)
   - chiral_an.py variant parity tests (mirror of mirror = identity for H2;
     3-cycle composition = identity for H3)
   - spectral_classifier.py on chirally-bearing HDC samples
   - shadow_projection.py round-trip (substrate→shadow→substrate per harmonic)
   - desert_storm.py multi-sector cascade composition smoke
7. tool_schema.py registrations for new functions
8. JPL Power-of-Ten audit (if C surface added; pure-Python may be acceptable
   for siona layer since it's framework-level composition not primitive
   computation)
9. CHANGELOG.md entry
10. PR → MERGE (no squash per `[[feedback_no_squash_merges]]`)
11. Tag → TestPyPI → verify in clean venv outside source tree
12. Production tag after clean rc

**Estimated scope:** ~400-600 LOC Python (siona/ sub-package) + ~300 LOC tests.
No C-side work needed; siona is a composition layer over existing amsc primitives.

### §6.6 Status

**WISHLIST documented; NOT AUTHORIZED to begin upstream work.** User
direction 2026-05-28 articulated the framework + naming + scope.
Continuation in separate rc cycle session per discipline.

**UPDATE 2026-06-02:** now LIVE in the dev's rc12 cycle (harmonic-2 mirror ops
`dispatch.mirror_pattern` / `catalog.reverse_order` / `search.byte_search_backward`;
harmonic-3 three-cycle `cyclic.three_cycle` / `laplacian.three_fold_eigvec_groups`;
`compose.greedy_bipartite_alignment`; tool_schema + tests; rc-first → TestPyPI;
production graduation held). The dev raised a namespace-placement question — answered in §6.7.

### §6.7 NAMESPACE PLACEMENT DECISION — per-class `amsc.*` (§6.1) is the home; "harmonics"/`siona` is a VIEW, never a privileged top-level (2026-06-02; dev rc12 question)

**The dev's question:** the §6 chirality/harmonic ops — keep them per-class in `srmech.amsc.*` (the §6.1 mapping: `dispatch.mirror_pattern` D, `catalog.reverse_order` E, `search.byte_search_backward` G, `cyclic.three_cycle` I, `laplacian.three_fold_eigvec_groups` L), or move them under a dedicated real top-level (e.g. `srmech.harmonics`)? (Context: `siona` was resolved to an alias, vacating the §6.3 sub-package home.)

**DECISION: continue the per-class `amsc.*` placement (§6.1). Do NOT create a privileged real top-level. This supersedes the §6.3 `siona/` sub-package structure for the OPERATORS** — they live in their A-N class module; the "harmonics" surface is a discoverability VIEW (alias / introspection / tool_schema tag), not a physical home. Grounded in the project's own discipline:

1. **§6.1 already specifies per-class `amsc.*` — and it is correct.** The dev is following the committed spec; no override warranted.
2. **`[[feedback_no_privileged_primitive_classes]]` (the Class-O→Class-L precedent).** A real `srmech.harmonics` / `siona` top-level is a **privileged cross-cutting namespace outside the A-N partition** — the exact carve-out the project killed when it dissolved Class O into Class L. The **harmonic order (1/2/3) is a per-operator PROPERTY that partitions the EXISTING classes** (§6 background: H1={A,B,F,H,N}, H2={C,D,E,G,K,M}, H3={I,J,L}); it is a *reading of* the partition (F129 "A-N as harmonic ladder"), so each op lives in the class it flavors.
3. **C-parity is cross-cutting SEMANTICS, not a class** (CLAUDE.md §2: "full 14-class **C-parity** primitive vocabulary"). Chirality/parity is woven through every class — isolating it into one namespace contradicts that.
4. **A dedicated namespace would FRAGMENT each A-N class across two packages** — base `cyclic.gcd` in `amsc.cyclic`, chiral `cyclic.three_cycle` in `harmonics`/`siona`. That splits a single class's operator set in two, the *opposite* of "the A-N partition is the organizing principle." Per-class keeps each class WHOLE (chirality-blind base + chirality-aware variant co-located) — strictly more faithful.
5. **The `siona = alias` resolution IS the precedent.** A harmonics surface is an alias/view, exactly as `siona` was just demoted; don't resurrect it as a real layer under a new name.

**Discoverability (the dev's legitimate worry) — solved WITHOUT a privileged home:**
- **tool_schema tags:** register each op with `harmonic_order ∈ {1,2,3}` (+ its Class-C chirality semantics) so `srmech dsl ops` / `introspect` can enumerate "all harmonic-2 ops" as a *filtered view* (rides the rc11 CLI-legibility win — no physical relocation needed).
- **§6.3 `harmonics.py` survives only as a pure introspection/classification module** (`classify_harmonic(op) -> 1|2|3`, `list_ops(order=2)`) that READS the per-class ops — a view, not their home. The §6.2 spectral classifier lands at **`amsc.spectral_classifier`** (the §6.2 alternative), not a real `siona` layer.
- **Optional:** a thin `srmech.harmonics` (or the `siona` alias) re-export for one-import convenience — *same alias status*; the SoT stays per-class.

**Two corollaries for the dev:**
- **No version-bump pressure from namespace.** §6.5 step-1 suggested a minor bump "because it introduces a new top-level module" — that rationale **dissolves** (there is now NO new top-level). The additions are new per-class symbols + tags + an optional alias = **non-breaking; ABI unaffected** (per the C-library discipline, adding a symbol does not bump `SRMECH_ABI_VERSION`). rc12 can stay on the current 0.7.0 rc-stack; no forced minor bump for namespace reasons.
- **Completeness (no-MVP).** §6 maps H2={C,D,E,G,K,M}, H3={I,J,L}; rc12 covers D/E/G (h2) + I/L (h3) + `compose`. So **J's `three_cycle_factor` and the K/M harmonic-2 variants are future rungs** — fine to stage, but log them as the remaining per-class coverage so the ladder finishes (don't silently cap at the rc12 subset). `compose.greedy_bipartite_alignment` is a composition-layer op (matching), correctly placed in the `compose` layer above the 14 classes — no objection.

**Status:** RECOMMENDED to the dev (continue §6.1 per-class; harmonics = view/tag/alias, not a top-level). Per `[[feedback_create_upstream_issues_never_close_them]]` the dev/maintainer makes the final call; this records the framework-principled answer for them to act on.

---

## §7 `substrate_parameterization` adapter — catalog-driven substrate runs (2026-05-28, post-MVP-audit)

User direction 2026-05-28:
> "srmech is also being corrected such that 'catalogs' are not new python script mvp magics. cascade is handled by srmech with the toml and MPR things. we can check test.pypi.org srmech/siona for status. this will help us to not reach for new MVP pretend things"

The rbs_lm_substrate catalog at `docs/srmech/catalogs/rbs_lm_substrate/descriptor.toml` is the canonical pattern for **substrate parameterization as catalog**: every former magic number in R-RBS-LM-112 (D, max_walk_length, max_paths, cycle_policy, n_buckets, bucket strategy, grammar mode, plausibility weights, sweep ranges, etc.) lives in nested `[fetch.literature_curated.*]` sub-tables so the typed `Descriptor` accessor reaches them via `desc.fetch["literature_curated"][section][field]`.

This works **today** because `literature_curated` is a permissive adapter — it accepts any nested params. But the semantic match is weak: substrate parameterization is not "literature curation," and a future srmech adapter family for this use case would be cleaner.

### §7.1 The wishlist — first-class `substrate_parameterization` adapter

A `substrate_parameterization` adapter would:
- Validate substrate-specific param sections at load time (e.g., `D > 0`, `0 ≤ weight ≤ 1` for plausibility weights, `cycle_policy ∈ {forbid, allow, count_limited}`)
- Expose typed sub-dataclasses on the loaded `Descriptor` — `desc.substrate`, `desc.generation`, `desc.hierarchical`, `desc.grammar`, `desc.plausibility`, `desc.measurement` — instead of dict-navigation
- Dispatch a `substrate_run` operation that takes the descriptor + a corpus source + a phase set, returns MPR-validated NDJSON

```python
# Aspirational srmech v0.5.x surface:
from srmech.amsc import load_descriptor
from srmech.rbs_lm import run_substrate_characterization

desc = load_descriptor("docs/srmech/catalogs/rbs_lm_substrate/descriptor.toml")
# desc.substrate, desc.generation, etc. are first-class typed accessors
records = run_substrate_characterization(desc, phases=[1, 2, 3, 4, 5, 6, 7])
# records is an iterator of MPR-validated dicts written to desc.schema.ndjson_file
```

### §7.2 Adapter registration sketch

Following the pattern in `srmech.amsc.descriptor.KNOWN_ADAPTERS` + `srmech.amsc.catalog.ADAPTER_CLASSES`:

```python
# srmech/amsc/descriptor.py
KNOWN_ADAPTERS = (
    "html_scraper", "json_api", "csv_bulk", "netcdf_grid",
    "geotiff_bbox", "literature_curated",
    "substrate_parameterization",  # NEW
)

# srmech/amsc/adapters/substrate_parameterization.py
class SubstrateParameterizationAdapter(BaseAdapter):
    REQUIRED_SUBSECTIONS = (
        "substrate", "encoding", "generation",
        "hierarchical", "corpus",
    )
    OPTIONAL_SUBSECTIONS = ("grammar", "plausibility", "measurement")

    def validate(self, fetch_dict):
        # Validate D > 0, weight ranges, allowed enums, etc.
        ...

    def parse(self, fetch_dict) -> SubstrateConfig:
        # Returns typed dataclass with all sections as sub-dataclasses
        ...
```

### §7.3 What the substrate library would look like upstream

Currently `_canonical_substrate.py` lives in research subtree per `[[feedback_upstream_srmech_fixes_as_research_notes]]`. A natural upstream home: `srmech.rbs_lm.substrate` — providing `VariableLengthSentenceMemory`, `HierarchicalMemory`, and the encode/sim/walk primitives.

```python
# Aspirational srmech v0.5.x surface:
from srmech.rbs_lm.substrate import (
    VariableLengthSentenceMemory,
    HierarchicalMemory,
    encode_word_k4, encode_bigram_l1, encode_skeleton_l2, encode_sentence_l3,
    sim_k4_batch,
    walk_bigram_chain,
)

memory = VariableLengthSentenceMemory(config=desc.substrate)
# config is a typed sub-dataclass, not a dict
```

### §7.4 Upstream procedure (if/when authorized)

1. Open separate session in srmech rc-cycle worktree
2. Add `substrate_parameterization` to `KNOWN_ADAPTERS` + write `SubstrateParameterizationAdapter`
3. Add typed sub-dataclasses (SubstrateParams, GenerationParams, etc.) to the Descriptor schema
4. Port `_canonical_substrate.py` to `srmech.rbs_lm.substrate` (Python; no C surface needed for the substrate algebra — it composes existing Klein-4 primitives that already have C parity)
5. Tests:
   - Adapter validation (catch out-of-range D, invalid cycle_policy, etc.)
   - Typed Descriptor round-trip (load → re-serialize)
   - Substrate algebra parity tests (vs current research subtree version)
   - Phase sweep smoke (a small in-memory catalog + the 7-phase characterization runs end-to-end and produces MPR-valid NDJSON)
6. tool_schema registrations for new public functions
7. CHANGELOG.md entry
8. TestPyPI rc → verify in clean venv (outside source tree) → production tag
9. Update rbs_lm_substrate/descriptor.toml to `adapter = "substrate_parameterization"` (rather than riding on literature_curated)
10. Delete `_canonical_substrate.py` from research subtree (now lives in srmech proper)

### §7.5 Why this earns catalog promotion

Per the rc-promotion criterion (cross-domain recurrence): the same substrate-parameter set is consumed by:
- R-RBS-LM characterization (this catalog's primary use)
- Potentially R-RBS-NN-V2 storage (two-tier architecture; same parameter shape but different defaults)
- Future cross-substrate experiments (smol-stack programming corpus, McGuffey ladder, etc.) — each is a catalog VARIANT, not a new script

Promoting `substrate_parameterization` to a first-class adapter makes the cascade dispatch a clean srmech operation rather than ad-hoc Python harness.

### §7.6 Estimated scope

- ~150-200 LOC adapter (validation + parsing)
- ~300-400 LOC substrate module port (mostly already exists in `_canonical_substrate.py`)
- ~200-300 LOC tests
- Documentation updates in srmech notebook §3.28 + tool_schema

### §7.7 Status

**WISHLIST documented; NOT AUTHORIZED to begin upstream work.** User direction 2026-05-28 surfaced the architectural pattern via the MVP-audit cleanup. Catalog rides `literature_curated` adapter today; transition to `substrate_parameterization` adapter is a clean separate rc cycle when scope opens.

---

*Maintained alongside the R-RBS-LM rolling PR. New entries land at the
top of the relevant arc section. Per upstream-as-research-notes
discipline, this file is the canonical record of catalog-gap requests
from the RBS-LM research subtree.*

---

## §8 siona Profile system alignment — rbs_lm_substrate as a registered profile (2026-05-28; srmech/siona v0.4.5 PRODUCTION)

User direction 2026-05-28:
> "srmech/siona v0.4.5 has landed. lets update the package and see what siona has for us next."

### §8.1 What siona 0.4.5 ships (versus 0.4.4)

siona is no longer a metapackage alias — at v0.4.5 it gains its own substantive
content: a **Profile system** (ADR-0001 / Task #199) layered above srmech that
provides:

- `siona.Profile` — dataclass for an activated profile (name / version / summary / package / raw / source_hint)
- `siona.ProfileStatus` — enumeration status for discovered profiles
- `siona.list_profiles()` → `Dict[str, ProfileStatus]`
- `siona.profile(name)` → activated `Profile` object
- `siona.profile_loader` — eager-at-import discovery via `importlib.metadata.entry_points(group="srmech.profiles")`
- Per-profile smoke-test cache at `~/.cache/srmech/profile_smoke_tests/<name>-<version>.toml`

Profile descriptors live as `srmech_profile.toml` files (v1 schema). Each
declaring package registers its profile via `[project.entry-points."srmech.profiles"]`
in its pyproject.toml. The loader validates against the v1 schema and
smoke-tests every bridge surface at activation time.

### §8.2 Schema (v1) — required fields per `srmech_profile.toml`

```toml
profile_schema_version = "1.0"   # required; MAJOR.MINOR; loader speaks "1.0"

[profile]
name              = "..."    # required; ^[a-z][a-z0-9_-]*$, 1..64 chars
version           = "..."    # required; MAJOR.MINOR.PATCH[rcN]
summary           = "..."    # required; one-line human readable
package           = "..."    # required; declaring Python package
srmech_requires   = "..."    # required; version constraint

# All sections below are optional but smoke-tested when present.

[profile.bridge]
# name = "module:callable" — each target must import + be callable.
build_substrate = "rbs_lm_research._canonical_substrate:build_substrate"
# ... etc

[profile.catalogs]
attested_root = "catalogs/<dir>"   # relative to package root; auto-registered

[profile.native]
# Optional ctypes plugin tier

[profile.tool_schema]
extension_file = "..."   # optional LLM-introspection coverage
```

### §8.3 Drafted profile descriptor for rbs_lm_substrate

`docs/srmech/rbs_lm_research/srmech_profile.toml` (this commit) — documentation-grade
canonical-shape draft. NOT yet entry-point-registered. Once the research subtree
becomes an installable Python package (§8.4 below), this file moves alongside
that package's `pyproject.toml` and gets registered.

Bridge surfaces declared:
- `build_substrate`, `build_hierarchical_substrate` — substrate constructors
- `encode_word_k4`, `encode_bigram_l1`, `encode_skeleton_l2`, `encode_sentence_l3` — F155 chirality-sector encoders
- `sim_k4_batch` — Klein-4 fractional-agreement similarity
- `run_characterization` — R-RBS-LM-122 phase sweep entry-point

Catalog: `attested_root = "catalogs/rbs_lm_substrate"` (already exists at
`docs/srmech/catalogs/rbs_lm_substrate/descriptor.toml`).

Native plugin: NONE — substrate algebra rides on srmech's native Klein-4
primitives (`srmech.amsc.hdc.klein4_random` + `klein4_bind`); no separate
ctypes library needed.

### §8.4 Path to actual registration (substantial scope; not authorized today)

Steps to make rbs_lm_substrate a real activated siona profile:

1. **Make `docs/srmech/rbs_lm_research/` an installable package.**
   - Add `pyproject.toml` (hatchling or scikit-build-core); declare package metadata
   - Move `_canonical_substrate.py` etc. into `rbs_lm_research/` namespace
   - Move `srmech_profile.toml` to the package data
   - Add `[project.entry-points."srmech.profiles"]` block:
     ```toml
     [project.entry-points."srmech.profiles"]
     rbs_lm_substrate = "rbs_lm_research:srmech_profile.toml"
     ```

2. **Install editable into the verify_srmech_043 venv.**
   - `pip install -e docs/srmech/rbs_lm_research/`
   - Verify `siona.list_profiles()` shows `rbs_lm_substrate`
   - Verify `prof = siona.profile("rbs_lm_substrate")` activates cleanly
   - Verify smoke-test cache populates at `~/.cache/srmech/profile_smoke_tests/`

3. **Optionally TestPyPI the package.**
   - As `rbs_lm_research-0.1.0rc1` (this is the research subtree's own rc cycle,
     separate from srmech's rc cycle)
   - Downstream consumers `pip install rbs_lm_research` → siona auto-discovers

4. **Migrate R-RBS-LM-122 to call via the activated profile.**
   - Instead of `import _canonical_substrate as cs; memory = cs.build_substrate(params)`,
     becomes `prof = siona.profile("rbs_lm_substrate"); memory = prof.build_substrate(params)`
   - Loses ~3 lines of imports; gains LLM-introspection + smoke-test guarantees

### §8.5 Status

**WISHLIST documented; NOT AUTHORIZED to begin packaging work.** User direction
2026-05-28 surfaced siona's Profile system as the canonical landing for what
the rbs_lm_substrate catalog has been doing. Drafting the profile TOML as
documentation is sufficient alignment work today; the packaging refactor is
its own scope when authorized.

Today's substrate continues to work via the existing
`docs/srmech/catalogs/rbs_lm_substrate/descriptor.toml` AMSC catalog
(literature_curated adapter) consumed directly by R-RBS-LM-122 through
`srmech.amsc.load_descriptor` + `descriptor_hash`. The profile TOML in this
section serves as the alignment target for future-packaging scope.

---

## §9 `srmech.rbs_lm` inference substrate — `RBSLMInferenceSubstrate` + `siona.profile("rbs_lm").infer()` (2026-05-29; F166 walk complete)

The F166 walk (R-RBS-LM-126..130) produced a native, bit-exact, catalog-instantiable
inference substrate, currently living in the research subtree as
`docs/srmech/rbs_lm_research/_rbs_lm_inference.RBSLMInferenceSubstrate` (+ the
`_canonical_substrate.ContextSubstrate` rolling-context encoder it composes).
This §9 records the upstream absorption target.

### §9.1 What the research-subtree artifact does today

```python
from _rbs_lm_inference import RBSLMInferenceSubstrate
sub = RBSLMInferenceSubstrate.from_catalog("descriptor_rbs_lm_inference.toml")
sub.learn(token_stream)                              # context→next assoc memory
cands, probs = sub.next_token_distribution(ctx)      # Steps 2-3
text = sub.infer(["the","cat"], temperature=0.02)    # Step 4 autoregressive loop
att  = sub.attestation()                             # MPR block
```

Composition (all named A-N ops, bit-exact): Step 1 `ContextSubstrate.encode_context`
(Class A∘M + iω₇ position), Step 2 `next_token_distribution` (Class M retrieve over
bigram-legal candidates), Step 3 temperature (soft-retrieval dial), Step 4 `infer`
(the loop). Parameterized entirely by `descriptor_rbs_lm_inference.toml`
([inference.context/distribution/sampling/loop/instrument]).

### §9.2 Upstream landing — `srmech.rbs_lm`

A first-class `srmech.rbs_lm` module would host:
- `srmech.rbs_lm.ContextSubstrate` — the rolling-context encoder (composes with `srmech.amsc.hdc.klein4_*`)
- `srmech.rbs_lm.RBSLMInferenceSubstrate` — the inference object above
- a `srmech.rbs_lm` tool_schema surface (`from_catalog` / `learn` / `next_token_distribution` / `infer` / `attestation`) so an LLM-as-tool can drive inference
- the siona profile binding: `siona.profile("rbs_lm").infer(context, temperature=...)` resolves to a configured `RBSLMInferenceSubstrate` (this is the §8 profile system + §9 object joined — the profile's "activate" loads the catalog + builds the substrate; `.infer` is the loop)

### §9.3 Capacity / scale-up note (load-bearing for upstream)

A single context→next associative memory holds ~`memory_capacity` (200 at D=8192)
(k-window→next) pairs — the F154 4× ceiling. For corpus-scale inference the upstream
object must compose with **hierarchical bucketing** (F162 P4 / R-RBS-NN-12,
`CanonicalHierarchicalMemory`) so the memory partitions across buckets. The
research-subtree class today is the single-memory (characterized-regime) version;
the hierarchical inference memory is the scale-up the upstream `srmech.rbs_lm`
should provide.

### §9.4 Status

**WISHLIST documented; NOT AUTHORIZED to begin upstream work.** The artifact works
in the research subtree and is the precursor; promotion to `srmech.rbs_lm` + the
`siona.profile("rbs_lm").infer()` binding + the hierarchical-memory scale-up are a
clean separate rc cycle when scope opens. Per
`[[feedback_upstream_srmech_fixes_as_research_notes]]`: never edit the srmech
package directly from this subtree; this note is the canonical absorption record.

---

## §10 srmech-mcp issues (2026-05-29) — surfaced by exercising the MCP surface for upstream rc fixes

Per user direction 2026-05-29 ("tell us when there are issues with srmech-mcp so we can correct it upstream; some known issues are being worked on in the next rcN"). Exercised the `mcp__srmech__*` surface directly (srmech 0.5.0rc8). **The core surface WORKS and is correct** — `dense_laplacian(n=4, path edges)` → correct D−A; `jacobi_eigvals([[2,-1,0],[-1,2,-1],[0,-1,2]])` → [0.586, 2.0, 3.414] = exact (2±√2, 2); `klein4_similarity` → 0.875 (7/8). Issues found:

### §10.1 BUG — `naming_lookup` is uncallable (schema/signature drift)
`mcp__srmech__srmech_amsc_naming_lookup(key=..., entries=[[k,v],...])` →
`TypeError: lookup() got an unexpected keyword argument 'entries'`.
The MCP tool schema advertises param `entries`, but the underlying `lookup()` does
not accept that kwarg (likely named `catalog`/positional). **The MCP wrapper kwarg
name is out of sync with the function signature → the tool always errors.** Fix:
align the wrapper param name to `lookup()`'s actual signature (or rename the
parameter), and add a parity smoke-test that every tool_schema entry is callable
with its advertised kwargs.

### §10.2 BUG — `klein4_random` is non-reproducible via MCP (no JSON-serializable seed)
Two calls with `D=16` returned different vectors; the only randomness param is
`rng: numpy.random.Generator` — a Python object that **cannot cross JSON-RPC**, so
there is NO way to seed for determinism through the MCP surface. This **breaks the
framework's own bit-exact / attestation discipline** for any MCP-driven cascade
using `klein4_random` (and likely `polar_random`, any `*_random`). Fix: expose an
integer `seed: int` param (alongside or instead of the `rng` object) on all
`*_random` MCP surfaces; the server constructs `default_rng(seed)`.

### §10.3 SCHEMA-GEN — non-JSON Python types leak into MCP schemas
Root cause shared by §10.2: the auto-generated MCP schemas expose Python-native
types that aren't JSON-serializable — `numpy.random.Generator` (rng), and `bytes` /
`SpectralHandle` (e.g. `naming_lookup`, `spectral_similarity`). Arrays coerce fine
(lists work), but object/bytes params are ambiguous or unusable over JSON. Fix: the
schema generator should map non-serializable params to serializable surrogates
(`rng`→`seed:int`; `bytes`→base64 `str` with documented encoding; `SpectralHandle`
→ an opaque handle id), or mark them MCP-excluded.

### §10.4 DESIGN NOTE (not a bug) — array ops return full JSON, no handles
`dense_laplacian` returns the full n×n matrix as nested JSON; `jacobi_eigvals`
returns a list. There is no handle to pass an intermediate by reference, so chaining
(Laplacian→eigvals) round-trips the whole array, and bulk per-token work would be
payload-heavy. This is consistent with MCP being a single-/interactive-op surface:
**use the srmech package for bulk in-script work** (CLAUDE.md §2 reflex-override),
the MCP tools for single ops / agent-driven cascades. A future `SpectralHandle`
(pass-by-reference) surface would make MCP chaining viable for larger arrays.

### §10.5 Status — UPDATED 2026-05-29 against srmech 0.5.0rc14 (TestPyPI)

The user took §10.1/§10.2 upstream; they revealed a wider list now flowing into the
rcN path. Verified against **0.5.0rc14** (installed clean, HAS_NATIVE=True, ABI=3):
- **§10.2 — FIXED (package):** `klein4_random(D, rng=None, seed: int|None=None)` —
  the integer `seed` param landed (confirmed by signature). Determinism is now
  seedable through the surface.
- **§10.1 — root cause CONFIRMED:** the package function is `naming.lookup(key,
  pairs=...)` — the MCP wrapper passed `entries=`. The fix is to align the wrapper
  to `pairs=`. (The MCP-wrapper fix itself is verifiable only with the rc14
  srmech-mcp server running — the package signature confirms the correct name.)
- **§10.3/§10.4** — schema-gen / pass-by-handle improvements; status open upstream.
- **Parity-smoke-test ask** (every tool_schema entry callable with its advertised
  kwargs) still stands — §10.1 would have been caught by it.

rc14 also ships the **28-dim chiral hyper-loop = 𝔰𝔬(8) adjoint** packaging (14 G₂
derivations + 14 L⊕R octonion-mults; Spin(8) triality) per its METADATA — the
framework grounding of the 28D arc, now hardware-callable. Our R-126..135 suite
**reproduces bit-exact** on rc14 (see REPRODUCE.md; native Class-L path is
version-stable). NOT fixed from this subtree (per
`[[feedback_upstream_srmech_fixes_as_research_notes]]`); canonical record for the maintainer.

### §10.6 More rc14 package gotchas (2026-05-29) — found by R-RBS-LM-136 (sub-agent)

1. **`srmech.amsc.format.sha256_bytes(b)` returns a 64-char hex STRING, not raw bytes** (despite the name). Callers expecting `bytes` (`int.from_bytes(...)`) must `int(h[:8], 16)` instead. Behaviorally fine; a naming/docstring clarification (the name says "bytes", the return is a hex `str`). Also surfaced in F174's token-seed code.
2. **`srmech.amsc.hdc.klein4_bundle(*vectors)` accepts an EVEN count in rc14** — no odd-count enforcement triggered, no neutral-pad needed. CLAUDE.md / earlier sessions note klein4_bundle "needs ODD count (majority tie-break)". Either the guard changed in rc14 or that note is stale — **bears on the R-126 even-k sawtooth pad-not-drop fix**: if even counts are now handled natively, the pad is unnecessary going forward. Flag for confirmation.

### §10.7 Cosmology + qm surface notes (2026-05-29) — found by the H177 three-front falsification (F178/F179/F180)

1. **CATALOG GAP — no parity-odd CMB surface.** `srmech.amsc.attested.cmb_*` ships **TE/EE/BB only** (parity-EVEN spectra). There is **no EB/TB** (parity-ODD) observable and **no cosmic-birefringence-angle β posterior** anywhere in srmech. This made the cosmic-birefringence front of the H177 falsification (F178) **unresolvable srmech-native** — the only chirality observable at the cosmic band is exactly the one not shipped. **Ask:** a `cmb_parity_odd_spectra` catalog (EB/TB) and/or an attested birefringence-β posterior surface (e.g. attested to Eskilt–Komatsu 2022 arXiv:2205.13962 / Minami–Komatsu 2020 arXiv:2011.11254), so parity-odd cosmology is testable in-framework.
2. **DOC — `srmech.cosmos` does not exist.** There is **no `srmech.cosmos` module** in rc14 (`ModuleNotFoundError`); CMB data lives at `srmech.amsc.attested.cmb_*`. Our own CLAUDE.md §2 and F177 §3/§6 named `srmech.cosmos` and are now corrected. If srmech's own docs/README reference `srmech.cosmos`, that is a doc bug — flag for confirmation.
3. **NAMING (minor) — ABI attr.** `srmech._native` exposes `NATIVE_ABI_VERSION` and `EXPECTED_ABI_VERSION` (both = 3), **not** a top-level `ABI_VERSION`. Code probing `_native.ABI_VERSION` raises `AttributeError`. Ask: add an `ABI_VERSION` alias or document the two names. (Found by F179.)
4. **DOC (not a bug) — `weak_mixing_angle` units.** `srmech.qm.sm.weak_mixing_angle` returns θ_W in **RADIANS** (atan2(g′,g) ≈ 0.50225), **not** sin²θ_W. Documented behavior; flagged so callers derive sin²θ_W = sin(θ_W)² ≈ 0.231 (PDG) rather than mis-reading the return as sin². (Confirmed F179; **not** a defect.)
5. **CATALOG/OP GAP — no Spin(8) triality operator (F182).** srmech ships Klein-4 (2 Z₂ chirality axes, Class C) + cyclic mod-n (Class I) but **no triality op** — the order-3 outer automorphism permuting 𝔰𝔬(8)'s three 8-dim reps (8_v/8_s/8_c), the defining structure of D₄. Needed to test the F182 triality-shadow hypothesis in-framework. (→ wishlist W10.)
6. **W2 re-confirmed live (F182):** the `klein4_random` MCP wrapper schema **still exposes only `rng`** (numpy object), no `seed:int` — non-reproducible via MCP; the package-side fix has not reached the wrapper.

The §10.7 items surfaced while exercising the `qm.relativistic` / `qm.gauge` / `qm.sm` / `amsc.attested.cmb_*` surfaces (H177 falsification, F178–F180) and the `hdc.klein4_*` / `cyclic` surfaces (third-axis check, F182). The qm surface itself computed **bit-exact** (γ₅²=I, Weyl projectors, su(2)/su(3) Casimirs, Weinberg residual = 0.0). No package edits from this subtree.

### §10.8 rc18 (2026-05-30) — W10 triality op LANDED + acceptance-validated; native status moved to a profile-loader

1. **W10 RESOLVED — the 𝔰𝔬(8) triality operator landed in 0.5.0rc18**, essentially as `SO8_TRIALITY_BUILD_SPEC` requested: `srmech.qm.octonion` (incl. **`octonion_table_attestation`** — MPR-wrapped `cayley_dickson_from_H` with the Fano triples), `srmech.qm.so8` (`so8_adjoint_basis`, `g2_subalgebra`), `srmech.qm.triality` (`triality_automorphism`/`swap`/`cycle`/`apply`/`companions`/`relation_residual`). **Acceptance tests pass bit-exact** (F192): τ³=I (residual 3.7e-15), **dim Fix(τ)=14=G₂**, dim Fix(swap)=21=𝔰𝔬(7), so8=28, g₂=14, octonion `ij=−ji`. A confirmation/thank-you for the maintainer — the spec was implemented faithfully.
2. **W2 — `klein4_random` seed confirmed package-side in rc18** (`klein4_random(D, rng=None, seed: int|None=None)`). MCP-wrapper exposure still to recheck when the srmech-mcp server is back.
3. **NATIVE-STATUS ARCHITECTURE CHANGE (supersedes the §10.7.3 / W6 ABI-attr note):** rc18 replaces the `HAS_NATIVE` bool + `_native.NATIVE_ABI_VERSION` with a **profile-loader** — `srmech.profile(name)`, `list_profiles()`, `ProfileStatus`, `AbiMismatchError`, `warmup_all()`; native is a **ctypes-loaded `_native/libsrmech.so`** (present in the wheel). **Gotcha:** a bare clean-venv `pip install srmech==0.5.0rc18` shows **`list_profiles() == {}`** (no profile registered) and `srmech.version` exposes nothing public — so native *dispatch* appears entry-point/opt-in-gated, **not active by default**, and the old "verify `HAS_NATIVE=True`" recipe no longer applies. **Ask:** document the rc18 native-status verification recipe (how to confirm `libsrmech.so` is dispatched + ABI matched) and clarify whether a bare install should auto-register a default native profile. (The `qm` layer is numpy, so this does not affect the triality validation.) **CORRECTION (2026-05-30, issue #733):** the "no recipe / not verifiable" framing was too strong — `from srmech.amsc._native import HAS_NATIVE` (= True) and `NATIVE_ABI_VERSION` (= 3) **DO** still work in rc18 (the AMSC shim retains them). The gap is narrower: only the *top-level* profile-loader (`srmech.list_profiles()` → `{}`) lacks a bare-install status surface. So this reduces to "surface the existing AMSC-shim native-status at the top level / document it," not "there is no way to check."
4. **DESKTOP-EXTENSION DISTRIBUTION GAP (→ wishlist W13; user direction 2026-05-30).** Claude Desktop installs MCP servers as `.mcpb` bundles (formerly `.dxt`; ZIP + root `manifest.json`); srmech ships no bundle and no emitter. Because srmech holds every manifest input (tool_schema's `mcp_callable` set + `__version__` + the `srmech.mcp._cli` entry), the ask is a **user-invoked** `srmech mcp emit-mcpb` that introspects them and packs `srmech.mcpb` into **cwd** via stdlib `zipfile` (**no Node**), defaulting to a **`uv`-type** manifest (PyPI-resolved native wheel; path/version-agnostic — solves the spec's "cannot portably bundle compiled dependencies") with a `python` + `user_config.python_path` fallback. Explicitly **not** an auto/`pip install`/wheel side-effect and **no** baked `sys.executable` (avoids the `/tmp`-reboot brittleness class). Server end already verified healthy against rc18 (stdio `initialize` + `tools/list`=173 + `tools/call`); only the emit/pack surface is missing. Naturally gold-stamped (uv resolves from live PyPI).

---

## §11 Kuramoto / ODE-integrator op + nibble-block coupled-adder primitive (2026-05-31; F236/F241)

**The gap (re-confirmed, now requested by FOUR findings — F141, F231, F234, F236/F241):** srmech ships **no Kuramoto / phase-lock / ODE-integrator op**. Every coupled-oscillator finding in this arc has had to supply the time-integration externally — F141/F231/F234 hand-rolled a minimal Euler step `θ ← θ + dt·(coupling + pinning)` in Python (every transcendental / modulus / spectrum / readout *inside* it routing through srmech), and **F236/F241 moved the integration into ngspice's `.tran` transient** (the analog substrate's ODE integrator) entirely. The pattern is stable: srmech does the readout (Class-K `pin_slot_at_zero`), the lock-margin (Class-K `magnitude`), the coupling-graph spectrum (Class-L `dense_laplacian` + `jacobi_eigvals`), the chirality (Class-C `net_chirality` / `reorient`), and the attestation (Class-A `sha256_bytes`) — but the *step itself* has no home in `srmech.amsc.cascade.*` or a `kuramoto`-namespaced module.

**Why F241 sharpens this from "candidate" to a concrete op-suggestion with a measured payoff:** F234 left the Kuramoto-step ask as a *candidate* for the user to file (its §5). F241 supplies the missing motivation — the nibble-block two-tier coupled-adder is not decorative: in ngspice its measured **time-to-lock is materially below the single ripple chain** (worst-case all-propagate: N=16 **9.0×**, N=32 **9.5×**; per-doubling growth ripple ×2.76 vs two-tier ×1.52), with every carry vector cross-checked correct. So there is now a *demonstrated dynamics-level reason* a downstream caller would want a first-class coupled-adder / phase-lock primitive, not just a structural curiosity.

**Two concrete op-suggestions (for the user/maintainer to file — NOT filed by this subtree; no package edit):**

1. **A Sakaguchi-Kuramoto phase-lock-step op** — a thin `srmech.amsc.cascade.kuramoto_step(theta, adjacency, pin_phase, pin_strength, K, dt)` (or a `srmech.kuramoto` namespace), a candidate **Class-L/Class-C composite** (transcendental symmetric coupling + the order-2 γ₅ chirality phase-state). It would close the gap that has recurred across four findings. The honest scope note: the integrator is the *only* thing currently hand-rolled — so the op is a small, well-bounded add (one Euler/RK step over a Laplacian-shaped coupling + a pinning anchor), not a new solver subsystem. Secondary: `cascade.magnitude` takes a real scalar, so the complex order-parameter modulus `r = |mean exp(iθ)|` is built from two `magnitude` calls + `sqrt` (the F231 pattern); a **native complex-modulus op** would also be a clean add.

2. **A nibble-block coupled-adder as a `cascade.*` primitive** (peer to `cascade.magnitude` / `cascade.pin_slot_at_zero`) — e.g. `cascade.nibble_block_carry(a_bits, b_bits, cin)` returning the two-tier carry vector via the Tier-1-parallel-nibbles + Tier-2-block-carry + Class-K-SR-latch-MUX structure F234/F236/F241 built by hand. This is more speculative (it bakes the carry-select decomposition into srmech), so the lighter-weight op (1) is the primary ask; (2) is recorded as the natural composite if the coupled-adder pattern recurs. Either way the **time-integration** (the `.tran` equivalent) is the load-bearing missing piece.

**Status — recorded, NOT filed.** Per `[[feedback_create_upstream_issues_never_close_them]]` and the upstream-as-research-notes discipline, this is logged here for the user/maintainer to file; the F241 timing result stands regardless of whether srmech grows the op (the measurement is in the analog substrate, which already supplies the integrator). If it connects to srmech's tooling, great; if not, it is still good research. No package edits from this subtree.

### §11.1 `kuramoto_step` is all-to-all uniform-coupling only — needs an optional coupling matrix / adjacency (2026-05-31; F240 re-run)

**The gap (sharpened by the F240 ngspice re-run):** rc9 DOES ship `srmech.amsc.cascade.kuramoto_step(theta, omega, *, coupling: float = 1.0, dt: float = 0.01)` — a welcome partial close of the §11 ask. BUT its signature confirms it is **all-to-all UNIFORM-coupling only**: a single scalar `coupling` applied as the mean-field `(coupling/n)·Σ_j sin(θ_j − θ_i)`. It does **not** accept a coupling matrix / adjacency / Laplacian, so it cannot express **graph-structured** coupling — and it especially cannot express **directed / asymmetric** coupling (A drives B but not B→A). F240 (and F235 before it) live entirely on the air-gapped **near-1D extended mesh** (radius-1 + radius-2, |E| = 2m−3) and turn on the **directed-vs-symmetric** distinction (feed-forward one-way edge vs reciprocal closed-loop edge + Class-K latch). The scalar `kuramoto_step` collapses every such graph to the complete graph and erases the one-way/reciprocal contrast that is the whole measurement, so F240 could not use it and routed the integration through **ngspice's `.tran`** instead (the bounded analog ODE integrator).

**Forward-ask (for the user/maintainer to file — NOT filed here; no package edit):** extend `kuramoto_step` with an **optional coupling matrix / adjacency argument** (or a Laplacian), e.g. `kuramoto_step(theta, omega, *, coupling=1.0, adjacency=None, dt=0.01)` where `adjacency[i,j]` weights `sin(θ_j − θ_i)` for oscillator `i` (and a non-symmetric `adjacency` expresses directed/one-way coupling). This would cover the graph-structured + directed coupling the F240 / F235 air-gapped-graph findings need, while the scalar path stays the default. A `Sakaguchi` phase-frustration `alpha` and an optional per-oscillator pinning anchor would round it out (the binary-phase γ₅ carry-lock case F234/F236 used). Recorded per the upstream-as-research-notes discipline; the F240 measurement stands either way (the analog substrate supplies the graph-structured integrator the op lacks).

### §11.2 rc9 verified CLEAN — native loads (ABI 3); use `srmech.introspect.native_status()` for the TestPyPI native check going forward (2026-05-31; F243 / F244 / F242c-fix)

Exercising rc9 across the `qm.octonion`/`so8`/`triality` surface (F243), the Class-L Laplacian + `format` + `cascade.kuramoto_step` ops (F242c, F244), and the bit-exact `format.sha256_bytes` re-verify (F240): **no new functional bug surfaced.** Native loads + dispatches correctly — `srmech.amsc._native.HAS_NATIVE = True`, `LIB` set, **ABI 3 = expected_abi**, `srmech.introspect.native_status()` → `{has_native: true, dispatching: true, abi_version: 3, load_error: null}`, 178 tools all MCP-callable. All ops give correct answers (`jacobi_eigvals(K3)=[0,3,3]`; octonion associator Fano split 7/28; `kuramoto_step` runs).

**One API note for the TestPyPI-before-PyPI discipline (not a bug — an improvement):** rc9 added a structured **`srmech.introspect`** module (`native_status()` / `describe()`), whose own docstring marks the bare `_native.HAS_NATIVE` poke the "old" way. The clean-venv native check in the release discipline should use **`srmech.introspect.native_status()`** going forward — note the flag lives at `srmech.amsc._native.HAS_NATIVE`, **NOT** the top-level `srmech._native` (which is the compiled-lib package dir, empty of the flag; mis-probing it this session briefly read a spurious absence). The §11.1 `kuramoto_step` graph-coupling gap remains open (rc9 ships all-to-all-uniform only).

### §11.3 push the 4-sector (Z₄ / Klein-4) parallel flag DOWN to the `hdc.klein4_*` ops (2026-05-31; F246 / user direction)

**The gap (surfaced by the F246 workflow's klein4-parallelism check):** the 4-way splay across the Klein-4 chirality sectors (F233; cores ≥ 4) **exists in srmech, but at the wrong layer** — `srmech.amsc.cascade.parallel.parallel_sector_dispatch(body, x, n_sectors=4)` runs one cascade body across the ≤4 sectors on `ThreadPoolExecutor(max_workers=4)` (`Z4_DISPATCH_SLOTS=(0,1,2,3)`, `KLEIN4_SECTOR_CAP=4`, hard-capped at 4 = beyond is `qm.triality` order-3; verified `cross_sector_reads:0`, `parallel_equals_serial:True`). BUT the **`srmech.amsc.hdc.klein4_*` ops themselves expose NO parallel/sectors/cores/n_jobs flag** (`KLEIN4_STATES=(0,1,2,3)` is data-model only). So bulk Klein-4 HDC work (per-token `klein4_bind`/`bundle`/`similarity` over many items) does NOT parallelize across the 4 sectors by default — the caller must hand-route through `cascade.parallel`, which most callers won't discover.

**Forward-ask (for the user/maintainer to file — NOT filed here; no package edit):** give the `klein4_*` HDC ops an optional `sectors=4` / `parallel=True` flag that routes the per-sector work through `parallel_sector_dispatch` so bulk Klein-4 binding parallelizes across the 4 chirality sectors **by default when cores ≥ 4**. Caveat to land in order: only **GIL-releasing bodies** (native/numpy/srmech-C atoms) genuinely overlap — pure-Python bodies are correct-but-serialized — so the **C-native peer `_native.cascade_parallel_sector_dispatch_c` (tracked OPEN as upstream #771) should land first** so the path is C-parity'd, not Python-only. Recorded per the upstream-as-research-notes discipline; the F246 measurement stands either way.

**DEV UPDATE (2026-05-31, from upstream dev):** `parallel_sector_dispatch` is confirmed **NOT currently chainable** — a sector-dispatched cascade does not compose with / nest inside another sector-dispatched cascade, so the 4-way Z₄ splay applies at **one** level only and does not carry **through a chained cascade**. This is the sharper form of the §11.3 ask and **breaks an existing API contract** (cascade ops advertise composability; the 4-sector path must compose like any other cascade). Being addressed in dev. **Why it is load-bearing for RBS-LM specifically:** the universal store/retrieve action is a **chained settling loop** (settle → settle → settle; the F166 autoregressive / multi-step retrieval shape), so for the bi-chiral substrate to actually run 4×-per-step across the chirality sectors, sector-dispatch MUST be chainable. Non-chainable ⇒ scaled multi-stage RBS-LM inference can hit the 4× at only one stage (≈1× across the chain), not 4×-per-stage. So the chainability fix is exactly what unblocks 4×-parallel chained cascades — fix it (with the #771 C-native peer) before the inference loop is scaled.

### §11.4 rc11 VERIFIED — CLI/tool-schema clarity LANDED; native + math regression-clean; the §11.1/§11.3 feature + chainability asks STILL OPEN (2026-05-31)

Verified `0.6.0rc11` (TestPyPI-latest; clean venv `/tmp/bench_srmech_rc11/venv`, outside the source tree). **Native + math regression-clean:** `introspect.native_status()` → `{has_native:true, dispatching:true, abi_version:3, expected_abi:3, native_version:"0.6.0rc11", load_error:null}`; **F246 spectrum fingerprint reproduced bit-identical (`ff6f864f…`)**; F243 math identical (its `response_sha256` moves `05248058…`→`c044ce02…` ONLY because the record envelope stamps `srmech_version` — expected on upgrade, NOT a math regression); F250 runs.

**LANDED — the CLI + tool-schema legibility fix (the rc11 focus):** `srmech dsl ops` now lists the cascade-catalog ops (10) each with its **A-N class signature + plain description** (e.g. `kuramoto_step [I∘sin∘Σ∘C]  theta += dt*(omega + (K/n)·Σ sin(θ_j−θ_i))`; `magnitude [K]  Class K pin-slot … |x| but cascade-honest`); plus `dsl run` / `dsl visualize` and an `mcp` subcommand that emits MCP integration artifacts (the tool-schema made legible for an LLM). This genuinely closes the "not clear for human + LLM to understand the CLI/tool-schema" gap.

**STILL OPEN in rc11 (verified — do NOT mark resolved):** (a) §11.1 `kuramoto_step` graph-coupling — signature unchanged (`coupling: float` scalar mean-field, no adjacency); now LEGIBLE via the op-catalog but the feature is unbuilt; (b) §11.3 `klein4_*` parallel flag — `klein4_bind(a, b)` unchanged (no `sectors=`); (c) §11.3 `parallel_sector_dispatch` chainability — STILL not composable: it returns a rich introspection Dict and applies Klein-4 stream-transforms (negate/reverse) to body I/O, so a dispatch-returning body breaks the outer transform (verified: nesting → `TypeError: bad operand type for unary -: 'str'`). It is a LEAF 4-sector analysis tool, not a chainable cascade stage; the dev's "being addressed" has not landed in rc11.

**Clarity nit remaining:** the CLI top-level help still reads "v0.5.0rc4 ships two subcommands" while listing four (status/bus/dsl/mcp) — a stale string.

**Working venv:** `/tmp/bench_srmech_rc11/venv` is the new latest-verified; research scripts run on it going forward. The `.mcp.json` repoint stays DEFERRED (rc ≠ SoT per `[[project_srmech_mcp_repoint_deferred_until_live]]`).

---

## §12 rc4 (0.7.0rc4) loop-bind / block-octonion HD surface — VERIFIED + two notes (2026-06-01; F291)

Verified `0.7.0rc4` (TestPyPI; clean venv `/tmp/srmech_v070rc4_venv`, outside the source tree). `introspect`/`_native`: `HAS_NATIVE=True`, ABI 3. The **F289 D1 hand-down LANDED faithfully** — rc4 ships the block-octonion HD surface natively: `hdc.{loop_bind_hd, loop_unbind_hd, loop_associator, loop_inv, loop_left_op, loop_right_op}` + `LOOP_DIM=8`, with docstrings using the framework's own vocabulary verbatim ("direct sum ⊕ of NB independent dim-8 octonion[s]", "Class-K associator RESIDUE", "(4:3) ordering" / "(3:4) mirror ordering").

**VERIFIED CLEAN (the load-bearing checks; scripts `rc4_native_hd_verify_F291.py` + `loop_bind_algebraic_laws_F291_bugtest.py`, both committed):**
- **14/14 model-independent algebraic laws PASS** on native `loop_bind` — composition-algebra norm-multiplicativity (resid² 1.3e-26), alternativity (2.5e-14), Moufang (7.0e-14), associator total antisymmetry (2.0e-14), genuine non-associativity (|assoc|≈131), `cross7 = Im(loop_bind)` exact (0.0), G₂ 3-form `g2=⟨x,cross7(y,z)⟩` exact (0.0), L≠R chirality (≈31), and the **division/cancellation laws** (left 1.7e-14; **right `(v·x)·conj(x)=N·v` 2.3e-14 — the algebraic ground of the F290/F291 peel**). So native `loop_bind` is a *genuine* octonion product / G₂ structure, not merely consistent with the oracle.
- **`loop_bind_hd` == the research-side helper (`loop_bind_hd_gate.py`), err 0.0** — the F291 workflow legs (run on rc2 + the helper) are thereby validated against rc4 native. **Block-diagonal** per-block == dim-8 `loop_bind`, err **0.0** (F289 D1 anchor). `loop_unbind_hd` LEFT-division round-trip clean (3.2e-15). `loop_associator`/`loop_left_op`/`loop_right_op` exact (0.0); ‖L−R‖_F=4.899.

### §12.1 NOTE (footgun) — `loop_inv` is GLOBAL on HD input, NOT per-block (silent wrong answer)
`loop_inv` is documented as the dim-8 octonion inverse `x̄/⟨x,x⟩` and is **exact on dim-8** (err 0.0). But applied to an **HD vector (len = NB·8)** it does **not** raise and does **not** go per-block — it treats the whole vector as **one** object (real = index 0, imaginary = indices 1…D−1, divided by the single global norm `⟨x,x⟩`). Measured: `loop_inv(c)` == global-conj/global-norm to **err 0.0**, but == the correct per-block inverse only to **err 15.95**. Since `loop_bind_hd`/`loop_unbind_hd` *are* per-block, the natural right-peel `loop_bind_hd(E, loop_inv(c))` is **silently wrong** (err ≈16, no exception). **Forward-ask (for the user/maintainer to file — NOT filed here):** make `loop_inv` go **per-block when `len(x) % LOOP_DIM == 0`** (consistent with the HD bind/unbind), **OR raise on `len != LOOP_DIM`** (fail-loud), **OR** add a documented `loop_inv_hd`. (`loop_conj` is likewise dim-8-only — not HD-vectorized; same fix family.)

### §12.2 NOTE (gap) — no native RIGHT-unbind (`loop_runbind_hd`) for the sequence-peel
`loop_unbind_hd(a, b) = conj(a_k)·b_k` is **left-division** (the HRR key→value unbind: recovers `v` from `bind(k,v)`). But the F290/F291 **order-aware sequence store** is a *left-fold* `((a·b)·c)` peeled **from the right** — right-division `(x·y)·ȳ = x` — which `loop_unbind_hd` does not provide (verified: `loop_unbind_hd(c,E)` ≠ `a·b`, err 26). The sequence-peel currently only works via the research helper `conj_hd` (per-block conjugate) bound on the right. **Forward-ask:** add `loop_runbind_hd` (per-block right-division) so the **RBS-LM path-memory** store (the F291 deliverable) is pure-native. This composes with §12.1 — the missing atom both need is a **per-block conjugate/inverse for HD vectors**; expose that once and both the safe `loop_inv` and the right-unbind fall out.

### §12.3 STILL DEFERRED (expected; recorded open) — F289 D2 + the F290 §C un-flatten primitive
- **F289 D2 (bring-your-own cascade-TOML composite):** not in rc4 — `SRMECH_CASCADE_PATH` is not referenced by the DSL loader, and `srmech.dsl._catalog.cascade_op_kind` resolves only `'unknown'` (no composite/TOML kind, no composite-resolver in `lookup_cascade_op`). Expected (D2 was explicitly the dev's architecture call).
- **F290 §C un-flatten `autocorrelation` (Class-L Wiener-Khinchin primitive):** absent across `srmech.amsc.*` (searched). Expected (dev-authoring hand-down). Until it lands, the un-flatten composite (autocorr → difference-graph → conservation-validate) cannot be a pure-TOML op.

**Status — recorded, NOT filed.** Per `[[feedback_create_upstream_issues_never_close_them]]` + the upstream-as-research-notes discipline; logged here for the user/maintainer (the F291 results stand regardless). The §12.1 footgun is the time-sensitive one (silent wrong result before rc5). **Working venv:** `/tmp/srmech_v070rc4_venv` (rc4 latest-verified, alongside the rc2 venv the F291 workflow ran on). The `.mcp.json` repoint stays DEFERRED (rc ≠ SoT).

### §12.4 RESOLVED in rc6 (0.7.0rc6, 2026-06-01; verified `rc6_fixes_verify_F291.py`, clean venv `/tmp/srmech_v070rc6_venv`)
rc6 landed **all three** §12.1/§12.2 asks + advanced §12.3-D2. Verified, no regression (native `loop_bind == oracle` err 0.0; `loop_bind_hd == helper` err 0.0; 14/14 algebraic laws still PASS):
- **§12.1 FIXED two ways.** (a) the scalar `loop_inv` now **fail-loud RAISES** `ValueError` on a len≠`LOOP_DIM` vector (`"length 2048 ... wider than one octonion"`) — no more silent global-conj; (b) rc6 added **`loop_conj_hd`** (per-block HD conjugate, == research `conj_hd`, err 0.0) and **`loop_inv_hd`** (per-block HD Moufang inverse; == `conj_hd` on unit blocks, 2.65e-15). The old footgun path `loop_bind_hd(E, loop_inv_hd(c))` now recovers correctly (2.72e-15).
- **§12.2 FIXED.** rc6 added **`loop_runbind_hd(a, b)`** = per-block Moufang RIGHT-division `bₖ·conj(aₖ)`. Convention: `loop_runbind_hd(right_key, bound)`. The F290/F291 **order-aware sequence-store peel is now PURE-NATIVE** — `loop_runbind_hd(c, E)` recovers the prefix-fold (3.19e-15), the full peel chain `((a·b)·c)→a` recovers (4.35e-15), and it matches the old research-helper peel **exactly (0.0)**. (The research `conj_hd` helper is no longer needed.)
- **§12.3-D2 LANDED + VERIFIED end-to-end** (`d2_byo_cascade_verify_rc6.py`). The F289-D2 bring-your-own cascade-TOML mechanism works fully: a user **pure-TOML composite** (`[cascade] name=… ` + a `[[composite.stage]]` array of already-named ops, **no Python**) dropped on **`SRMECH_CASCADE_PATH`** loads, appears in `list_cascade_ops()`, resolves via `lookup_cascade_op` → `_make_composite_runner` → `build_chain_from_dict`, and **runs** (verified `magnitude∘magnitude`, `runner(-5.0)=5.0`). **Provenance flag correct** (F289-D2 §4): the user op is tagged `_provenance="user:<sha256>"` (B-tier), the shipped op `"srmech"` (A-tier). **Load-time validation is fail-loud** (F289-D2 §2): an unknown-op reference → `ValueError("composite … references unknown op …")`; a name shadowing a shipped op → `ValueError("cascade op-name conflict …")`. So config-not-code third-party cascades are real. **`autocorrelation` (F290 §C) is STILL ABSENT** — the un-flatten catalog is now blocked on *only* that one Class-L primitive (everything else is an authorable pure-TOML composite).

**Status:** §12.1 + §12.2 + §12.3-D2 **RESOLVED + verified**; §12.3-`autocorrelation` **still open** (the sole remaining un-flatten blocker). Working venv `/tmp/srmech_v070rc6_venv` is the new latest-verified.

### §12.5 RESOLVED in rc9 (0.7.0rc9, 2026-06-02) — `autocorrelation` landed; the un-flatten catalog is now fully authorable
rc9 ships **`srmech.amsc.cascade.autocorrelation(x) -> List[float]`** — doc "Class L (Wiener-Khinchin): the circular autocorrelation of `x`." Verified vs the reference `IFFT(|FFT(x)|²)` (Class-K-clean `|F|² = F·conj(F)`): **err 4.2e-14** on a length-64 signal (HAS_NATIVE, ABI 3). This was the **sole remaining un-flatten blocker** (F290 §C). So: with `autocorrelation` (rc9) + the verified D2 BYO-cascade-TOML mechanism (rc6, §12.4), the **un-flatten catalog is now fully authorable as a PURE-TOML composite** — `[composite]` stages `autocorrelation (L)` → peak-detect / `dense_laplacian` difference-graph (L) → `jacobi_eigvals` (L) → conservation-validate (user-attested rule) — **no further package code needed**. **All §12 items RESOLVED.** Working venv `/tmp/srmech_v070rc9_venv` is the new latest-verified.

### §12.6 rc10/rc11 — the F292 SIMD grafts LANDED + verified BIT-EXACT (0.7.0rc11, 2026-06-02; `rc11_simd_graft_verify_F292.py`, clean venv `/tmp/srmech_v070rc11_venv`)
The dev (cloud branch `claude/insect-colony-distributed-body`) implemented **both F292 apple-tree grafts**: **rc10 = N-way SIMD SHA-256 batch** (graft #1), **rc11 = SIMD `loop_bind_hd`** (graft #2). The cloud session ran on srmech **0.6.0** (sandbox blocked `test-files.pythonhosted.org`) so it **never clean-verified them**; verified here on a clean rc11 TestPyPI install (`HAS_NATIVE`, ABI 3, `native_status` dispatching). **The F292 parity discipline (SIMD must be bit-exact to scalar) is MET:**
- **Graft #1:** `format.sha256_batch(list[bytes]) -> list[str]` (+ `_native.sha256_batch_c`). **BIT-EXACT to scalar `sha256_bytes`** on 10 messages incl. SHA block-boundary lengths `{0,1,55,56,63,64,65,127,128,256}` + the empty-string FIPS KAT `e3b0c442…`. 0 mismatches.
- **Graft #2:** SIMD `loop_bind_hd` (new dispatch helpers `_try_native_loop_bind_hd` / `_loop_native_ready`). **BIT-EXACT:** native `loop_bind` == oracle (64 basis pairs, err **0.0**); `loop_bind_hd` block == dim-8 `loop_bind` (block-diagonal, err **0.0**); == the research helper (err **0.0**) — the SIMD path did not change the result.
- **No regression:** 14/14 model-independent algebraic laws PASS; `loop_runbind_hd` right-peel 3.08e-15; `autocorrelation` present.

**The F292 apple-tree hand-down loop is CLOSED:** hand-down (F292) → dev implements (rc10/rc11) → **bit-exact verified** (here). Correctness/parity confirmed; the energy/throughput payoff numbers are the dev's to measure. Working venv `/tmp/srmech_v070rc11_venv` is the new latest-verified.

---

## §13 DEV HAND-DOWN — open feature asks verified UNRESOLVED through 0.7.0rc11 (2026-06-02)

Consolidated, dev-facing digest of the items that are **NOT bugs** (nothing here returns a wrong answer) but **remain unbuilt as of rc11**, each verified open on the clean `/tmp/srmech_v070rc11_venv`. This is the take-to-dev list; the canonical per-item rationale lives in the §11.x entries cross-referenced below. Ordered by RBS-LM load-bearing priority. **Recorded, NOT filed** per `[[feedback_create_upstream_issues_never_close_them]]` + the upstream-as-research-notes discipline — tracker state is the user's/maintainer's call; the findings stand regardless.

| # | Item | Kind | Verified state @ rc11 | Canonical SoT |
|---|------|------|------------------------|---------------|
| **D1** | `parallel_sector_dispatch` chainability | API-contract break | NOT composable (verified repro below) | §11.3 |
| **D2** | `kuramoto_step` graph-structured / directed coupling | feature gap | signature unchanged (scalar mean-field only) | §11.1 |
| **D3** | `klein4_*` per-op `sectors=`/`parallel=` flag | ergonomics gap | no flag on the HDC ops | §11.3 |
| **D4** | CLI top-level help stale string | doc nit | "v0.5.0rc4 ships two subcommands" (lists four) | §11.4 |

### D1 — `parallel_sector_dispatch` is not chainable (HIGHEST priority; breaks an advertised contract)
**Ask:** make a sector-dispatched cascade **compose / nest** like any other cascade stage, so the 4-way Z₄ chirality splay carries **through a chained cascade**, not just one level.
**Why it's load-bearing (RBS-LM):** the universal store/retrieve action is a **chained settling loop** (settle → settle → settle; the F166 autoregressive multi-step shape). Non-chainable ⇒ a scaled multi-stage inference loop gets the 4× speedup at **one** stage only (≈1× across the chain) instead of 4×-per-stage. This is the one open item that directly throttles scaled RBS-LM inference.
**Verified repro (rc11):** `parallel_sector_dispatch` returns a rich introspection `Dict` and applies Klein-4 stream-transforms (negate/reverse) to body I/O, so a dispatch-returning body fed to an outer dispatch breaks the outer transform → `TypeError: bad operand type for unary -: 'str'`. It is a **leaf** 4-sector analysis tool, not a chainable stage. (Dev acknowledged "being addressed" 2026-05-31; not landed in rc11.)
**Proposed shape:** the dispatch should return a value of the **same type its body returns** (so nesting type-checks), with the introspection Dict available via a separate accessor / opt-in (`return_report=True`) rather than as the default return. Land with the C-native peer `_native.cascade_parallel_sector_dispatch_c` (tracked OPEN upstream #771) so the path is C-parity'd, not Python-only. **Caveat to document:** only GIL-releasing bodies (native/numpy/srmech-C atoms) genuinely overlap; pure-Python bodies are correct-but-serialized.

### D2 — `kuramoto_step` needs an optional coupling matrix / adjacency (directed + graph-structured)
**Ask:** extend `kuramoto_step(theta, omega, *, coupling=1.0, dt=0.01)` with an **optional `adjacency=None`** (matrix / Laplacian) where `adjacency[i,j]` weights `sin(θ_j − θ_i)` for oscillator `i`; a **non-symmetric** `adjacency` expresses **directed / one-way** coupling. Scalar path stays the default. A Sakaguchi phase-frustration `alpha` and an optional per-oscillator pinning anchor (binary-phase γ₅ carry-lock, F234/F236) would round it out.
**Why it's load-bearing:** rc9 shipped the scalar all-to-all `(coupling/n)·Σ_j sin(θ_j − θ_i)` — a real partial close — but it **collapses every graph to the complete graph** and erases the directed-vs-symmetric distinction (feed-forward one-way edge vs reciprocal closed-loop edge) that is the *whole measurement* in the F240/F235 air-gapped near-1D mesh findings. Those still route integration through ngspice's `.tran` because the op can't express the graph.
**Verified state (rc11):** signature unchanged (`coupling: float`, no adjacency); now **legible** in the rc11 `srmech dsl ops` catalog (`kuramoto_step [I∘sin∘Σ∘C]`) but the feature is unbuilt. Scope note: the integrator is the *only* hand-rolled piece — this is a small bounded add (one Euler/RK step over a Laplacian-shaped coupling + a pinning anchor), not a new solver.

### D3 — push the 4-sector parallel flag DOWN onto the `klein4_*` HDC ops
**Ask:** give `klein4_bind` / `klein4_bundle` / `klein4_similarity` an optional `sectors=4` / `parallel=True` that routes per-sector work through `parallel_sector_dispatch`, so bulk Klein-4 HDC parallelizes across the 4 chirality sectors **by default when cores ≥ 4**.
**Why:** the 4-way splay exists in srmech but **at the wrong layer** — only `cascade.parallel.parallel_sector_dispatch` exposes it; the `klein4_*` ops themselves expose no flag (`KLEIN4_STATES=(0,1,2,3)` is data-model only), so per-token bulk binding doesn't parallelize unless the caller hand-routes through `cascade.parallel` (which most callers won't discover).
**Verified state (rc11):** `klein4_bind(a, b)` unchanged — no `sectors=`. **Dependency:** lands cleanly only **after D1** (it composes the dispatch) and the #771 C-native peer (so it's C-parity'd, not Python-only).

### D4 — CLI top-level help stale string (low-priority doc nit)
**Ask:** update the CLI top-level help — it still reads **"v0.5.0rc4 ships two subcommands"** while actually listing **four** (`status` / `bus` / `dsl` / `mcp`). Pure string fix; no behavior change.

**Dependency order for the dev:** **D1 first** (unblocks chained 4× and is the advertised-contract fix) → **D3** (rides on D1 + #771) → **D2** (independent, self-contained) → **D4** (trivial, anytime). D1+D3 are the pair that actually unblock 4×-parallel chained RBS-LM inference; D2 unblocks the air-gapped directed-coupling findings; D4 is cosmetic. **Working venv:** `/tmp/srmech_v070rc11_venv`. The `.mcp.json` repoint stays DEFERRED (rc ≠ SoT per `[[project_srmech_mcp_repoint_deferred_until_live]]`).

---

## §14 RENAME + DESIGN TARGET — RBS-NN → RBS-SNN; RBS-LM "L" = Language; notebook-native-language pipeline (2026-06-03; F311/F312/F323)

**Rename (research-side naming; heads-up for any srmech-side `rbs_*` naming):** **RBS-NN → RBS-SNN** ("Synaptic-Neural", synaptic-first per F311 — the relationship-first corrective ordering; the gap/synapse is the primary object). **The "RBS-" prefix disambiguates the F311 Spiking-NN acronym collision** (RBS-SNN is clearly *our* term, not generic spiking-NN). Per F317, the canonical identity is the **operator-signature** (A·N composition), so this is a **cheap, additive label change** (append a synonym, never a rewrite). If `srmech.rbs_lm` (rc14) or any srmech surface exposes RBS-**NN**-named identifiers, they become RBS-**SNN**; back-compat alias acceptable.

**Naming refinement — RBS-LM "L" = LANGUAGE, not LARGE.** The framework is **scale-invariant** (F312 scale-free neural tissue; F162). "Large" imports a scale-assumption the framework rejects. RBS-LM = a *scale-invariant* relationship-language model.

**DESIGN TARGET (build-up, not a now-ask) — the notebook-native-language pipeline (F323):** a script running the research notebooks **through RBS-SNN** to emit their **relationship-native lean structure** — operator-signatures + couplings, **no grammatical-sentence render** (= the LLM-native, render-free language of the corpus). Pipeline: `notebooks → RBS-SNN → render-free relationship-lean → RBS-LM`. Generalizes the F237 `CLAUDE_LEAN` extractive-graft to RBS-native + whole-corpus, yielding an **auto-generated prime/index** (cf. the hand-written `MFO_PRIME_CARD.md`). Flagged as a forward target for the `srmech.rbs_lm` arc; not a current build ask.

---

## §15 rc19 (0.7.0rc19) VERIFIED CLEAN — §13 D1/D2/D3 dev-hand-down asks LANDED; one new finding (2026-06-03)

Full bug-test of `srmech==0.7.0rc19` (TestPyPI) in a clean venv **outside** the source tree (`/tmp/verify_srmech_v070rc19`, Python 3.14.4, native `cp314-cp314-manylinux` wheel + numpy 2.4.6). `native_status() = {has_native: True, dispatching: True, abi_version: 3, expected_abi: 3, native_version: '0.7.0rc19', load_error: None}`. `tool_schema.get_tool_schema()` → **201 entries**. Scripts: `/tmp/verify_rc19_{discover,main,fix}.py`.

**The §13 dev-hand-down asks D1/D2/D3 are RESOLVED — verified, not assumed:**

| # | §13 ask | rc19 verified state |
|---|---|---|
| **D1** | `parallel_sector_dispatch` chainable | **LANDED** — sig now `(body, x, *, n_sectors=4, verify=False, combine=None)`; `cascade.sectorize(body, *, n_sectors=4, combine='bundle')` wraps a body for nesting; `verify=True` self-check passes (returns `sectors/combined/z4_dispatch_slots/independence/collapse_lattice/cap/...`). The `combine=` recombine makes it stream→stream chainable. |
| **D2** | `kuramoto_step` graph/directed coupling | **LANDED (rc14)** — sig now `(theta, omega, *, coupling=1.0, dt=0.01, adjacency=None, alpha=0.0, pin_anchor=None, pin_strength=1.0)`. `adjacency=` (n×n) runs; **`alpha=0.0` reproduces the plain step BYTE-FOR-BYTE** (residual 0.00e+00). |
| **D3** | `klein4_*` per-op `sectors=`/`parallel=` flag | **LANDED (rc13)** — `klein4_bind(a,b,*,sectors=None,parallel=None,mode='chunk')`, same on `klein4_bundle`. **Value-preserving CONFIRMED bit-identical**: `mode='chunk'` and `parallel=True` both `np.array_equal` to the serial default (bind + bundle, D=4096). |
| **D4** | CLI top-help stale string | **NOT re-tested** this pass (package-API only, no CLI invocation). Carry forward. |

So the D1+D3 pair that unblocks 4×-parallel **chained** RBS-LM inference, and D2 (directed-coupling for the air-gapped findings + the queued CoCC-noise directed-Kuramoto leg), are all shipped as of rc19 — the directed-Kuramoto step can now run native instead of via ngspice `.tran`.

**Other gated surfaces — all PASS:** `so8.so8_adjoint_basis()` = **28** (28 DIM), `so8.g2_subalgebra()` = **14** (14 DoF), `so8.an_embedding()` → dict (`su3/complement/triplet/antitriplet/...`, the 14 = 8+3+3̄ branch); `triality.triality_automorphism()` is 28×28 with **τ³ = I** to residual **3.66e-15**; core A–N spot-checks clean (sha256 FIPS `abc`; gcd; `best_rational(314159,100000,1000)=(355,113)`; `factor(360)=2³·3²·5`; triangle Laplacian eigvals `[0,3,3]`; `pin_slot_at_zero(-2)=(-1,2.0)`).

### §15.1 NEW FINDING — `cascade.magnitude(x: float)` is real-only; unhelpful error on complex; our CLAUDE.md over-describes it
**Observed:** `cascade.magnitude` is `(x: float) -> float` and correctly returns `|x|` for reals (`magnitude(-5.0) → 5.0`, the cascade-honest `abs()` replacement). **But `cascade.magnitude(complex(3,4))` raises `TypeError: '>' not supported between instances of 'complex' and 'float'`** — an internal comparison leaking, not a clean contract error.
**Mismatch (ours too):** the monorepo `CLAUDE.md` STOP-list calls `cascade.magnitude` "the modulus; replaces the hand-written `(re**2+im**2)**0.5`" — which implies a complex / 2-D Euclidean modulus it does **not** provide (it is single-real `abs`; `magnitude(25)` returns 25, not 5).
**Two-sided ask:** *srmech-side (recorded, not filed):* either (a) accept a complex / 2-tuple and return `(re²+im²)^0.5`, or (b) keep real-only but raise a clear `TypeError("magnitude expects a real float; for the complex modulus use …")` instead of leaking the internal `>`. Low priority; no wrong answer in-contract. *Ours:* correct the `CLAUDE.md` line — `cascade.magnitude` is the **real `|x|`** (Class-K / `abs()` replacement); the complex `(re²+im²)^0.5` modulus needs a compose or the (a)/(b) fix.

**Verdict: rc19 is CLEAN for the RBS-LM surface** — native dispatch + all gated surfaces verified; D1/D2/D3 landed; sole finding is the minor `magnitude` real-only contract/doc mismatch. **Recorded, NOT filed** (tracker state is the user's/maintainer's call per `[[feedback_create_upstream_issues_never_close_them]]`). `.mcp.json` repoint stays DEFERRED (rc ≠ SoT).

## §16 rc21 (0.7.0rc21) VERIFIED CLEAN — DSL compose-engine exercised END-TO-END (the rc19 residual); one new finding (2026-06-03)

Full bug-test of `srmech==0.7.0rc21` (TestPyPI) in a clean venv **outside** the source tree (`/tmp/verify_srmech_v070rc21`, Python 3.14, native `cp314-cp314-manylinux` wheel + numpy 2.4.6). `native_status() = {has_native: True, abi_version: 3, native_version: '0.7.0rc21', load_error: None}`. `tool_schema` → **201 entries** (unchanged from rc19). Scripts: `/tmp/verify_rc21{,_chain,_chain2,_chain3}.py`.

**No regression vs rc19** — all gated surfaces re-confirmed: `loop_bind`/`loop_bind_hd`/`loop_unbind_hd`/`loop_runbind_hd` present; `klein4_bind` `mode=` flag present; `kuramoto_step` `adjacency=`/`alpha=` present; `so8.so8_adjoint_basis()` = **28**, `so8.g2_subalgebra()` = **14**; `triality.triality_automorphism()` 28×28 with **τ³ = I** residual **3.66e-15**.

**NEW THIS PASS — the DSL operator-chain compose-engine (`srmech.dsl`) run END-TO-END.** rc19 confirmed the *surface* (`run_toml_chain`, `build_chain_from_{dict,toml,toml_str}`, `Chain`, `list_cascade_ops`, …) but did not *execute* a chain. rc21 exercised every chain special-form against known-correct outputs — all PASS:

| Chain form | TOML | Input → Output | Verdict |
|---|---|---|---|
| single `op` | `op="magnitude"` | `-5.0 → 5.0` | ✓ Class K |
| single `op` (seq) | `op="chiral_flip"` | `[1,2,3] → [3,2,1]` | ✓ Class C |
| **multi-stage** | `magnitude` → `best_rational_signed(max_d=10)` | `-3.5 → (7,2)` (= 7/2 = 3.5) | ✓ stages compose |
| `loop_n` + `sub_chain` | `loop_n=3` over `chiral_flip` | `[1,2,3] → [3,2,1]` (odd) | ✓ control-flow |
| `fold` | `fold_init=0`, `fold_op="cyclic_gcd"` | `[12,8,6] → 2` | ✓ Class I |
| `reduce` | `reduce_op="cyclic_gcd"` | `[12,8,6] → 2` | ✓ |
| `parallel_body` (combine=bundle) | `chiral_flip` × 4 sectors | `[1,2,3] → [12,8,4]` (4·[3,2,1]) | ✓ Klein-4 fan-out |

So the rc19 **DSL-compose-engine residual is RESOLVED**: the chain runner loads TOML (`[chain]` + `[[stage]]` array), materialises `op`/`loop`/`fold`/`reduce`/`parallel_sectors`, and runs — chains stream→stream and nests (the rc12 chainability holds through the runner).

### §16.1 NEW FINDING — `cascade.reorient(orientation, value)` is un-invokable as a DSL `op=` stage (data-arg-second vs pipe-into-arg0 contract)
**Observed:** every catalog op tagged `kind="stage"` is data-first except `reorient`. `reorient`'s signature is `reorient(orientation: int, value)` — the **data argument is SECOND**. The DSL unary-stage contract pipes the streamed value into the **first** positional, so it lands in `orientation`, leaving `value` unfilled → `TypeError: reorient() missing 1 required positional argument: 'value'`. Supplying `orientation=` as a stage kwarg instead collides: `TypeError: reorient() got multiple values for argument 'orientation'` (the pipe already filled position 0). Net: `reorient` **cannot be driven as an `op=` stage or as a `parallel_body=`**, though the catalog lists it `kind="stage"`.
**Not a math bug.** The `(orientation, value)` order is natural for hand-composed Python (`o, m = pin_slot_at_zero(x); reorient(o, new_m)`), and `reorient` works fine called directly. It is specifically a **DSL-stage-contract mismatch.** (Verified clean by contrast: `magnitude`, `chiral_flip`, `pin_slot_at_zero`, `best_rational_signed`, `net_chirality`, `autocorrelation` are all data-first and drive as `op=` stages without issue; `cyclic_gcd`/`chiral_dual` are binary and only valid via `fold`/`reduce`/their op-arg, not as bare `op=` — expected.)
**Two-sided ask:** *srmech-side (recorded, not filed):* either (a) reorder to `reorient(value, *, orientation)` so the data arg is first (matching every other stage-op + the pipe contract — cleanest), or (b) keep the order but drop `kind="stage"` from `reorient`'s catalog entry and document that it composes only after a `pin_slot_at_zero`, or (c) have the DSL detect the data-arg position. Low priority; no wrong answer (it fails loud, just unhelpfully). *Ours:* when authoring chain-TOML, do **not** use `reorient` as a bare `op=`/`parallel_body=` stage until (a)/(b) lands.

**Verdict: rc21 is CLEAN for the RBS-LM surface** — native dispatch + all gated surfaces verified (no rc19 regression), and the DSL compose-engine now confirmed running end-to-end across all chain special-forms. Sole new finding is the `reorient` stage arg-order mismatch (loud failure, not a wrong answer). **Recorded, NOT filed** per `[[feedback_create_upstream_issues_never_close_them]]`. Working venv `/tmp/verify_srmech_v070rc21` is the new latest-verified; `.mcp.json` repoint stays DEFERRED (rc ≠ SoT).

## §17 DESIGN ASK — catalog → kernel → DSL entry: unify the two op registries + ship the 2 missing text-stage primitives (2026-06-03; rc21-grounded)

**Question driving this (user):** what tooling does srmech need so that *our* LM kernels built from catalogs — **and anyone's catalog of any other texts** — show up as DSL entries (discoverable + runnable the way the 11 cascade ops are)?

**The good news first — srmech already ships ~80% of this (verified on rc21):**
- `signal_processing.encode_loe_content(content: str, *, D=8192, substrate='default') -> bytes` — a working **text → instrument** encoder (verified: 1024-byte instrument, self-sim **1.000**, vs-unrelated **−0.007**).
- `srmech.rbs_lm` ships the **layered text encoders** `encode_word_k4` / `encode_bigram_l1` / `encode_skeleton_l2` / `encode_sentence_l3` + `RBSLMInferenceSubstrate` / `ContextSubstrate` / `sim_k4_batch` / `token_seed` — the 4:3:7-ish encode stack, upstreamed.
- `signal_processing.RBSHDCInstrument` (build / encode_content / decode_fingerprint / query_class / similarity / verify_bit_exact) + `mint_cascade_composition` + `decode_loe_fingerprint`.
- `amsc.catalog` ships a **catalog-chain mechanism**: `list_catalog_chains(source_key)` ("enumerate operator chains declared by a catalog") + `run_catalog_chain(source_key, chain_name, *, row_index=, inputs=)` ("execute a declared chain on a catalog row") + `use_local_kernel(path, *, adapter_class=)` ("register a user-runtime-kernel overlay (T2)") + `get_local_kernel_state()`.
- Class-L `dense_laplacian` / `hermitian_eigendecompose` + Class-M `mint_vector` / `bundle` / `bind` / `permute` (the kernel-build math primitives) all present.

**So the gap is NOT "build the capability" — it is UNIFICATION + 2 missing precursors.** Verified the disconnect on rc21: `dsl.list_catalog_ops()` returns **exactly the 11 cascade ops**; `encode_loe_content` is **not** among them and `lookup_cascade_op('encode_loe_content')` → `ValueError: unknown cascade op`; `dsl` has **no** `list_catalog_chains`/`run_catalog_chain`, `catalog` has **no** `list_cascade_ops`. **The DSL op-discovery surface and the AMSC catalog-chain surface are fully disjoint** — a kernel chain declared on a text-catalog is invisible to the DSL, and the working `encode_loe_content` text→instrument op can't be named in a chain.

### The 4 changes (ordered cheapest-highest-leverage first)

| # | Change | Why | Status today |
|---|---|---|---|
| **U2** | **Register the existing text→instrument encoders as DSL cascade-ops** — `encode_loe_content` + the `rbs_lm.encode_{word_k4,bigram_l1,skeleton_l2,sentence_l3}` stack. One catalog-TOML descriptor each (like the 11 shipped). | Cheapest, highest leverage: the primitive **already works** (verified). Registering it makes `[[stage]] op="encode_loe_content"` legal → **any catalog's text rows get a one-line kernel chain.** | exists in `signal_processing`/`rbs_lm`, **invisible to DSL** |
| **U1** | **Ship the 2 missing text→graph stage primitives** so the *presence* (K1) kernel-build is an authorable pure-TOML composite end-to-end: `tokenize(text, *, stopwords=, min_len=, pattern=) -> List[str]` (Class B/G text-segmentation) and `cooccurrence_edges(tokens, *, window=, vocab_size=) -> (n, edges, weights)` (**Class L precursor** — tokens→weighted edges). | These are the only missing links between `text` and the already-shipped `dense_laplacian`. `cooccurrence_edges` **kills the hand-rolled `Counter()` co-occurrence** our research scripts use (the exact idiom the CLAUDE.md STOP-list flags). With U1+U2, K1 = pure-TOML composite `tokenize → cooccurrence_edges → dense_laplacian → eigendecompose → topk_eigvec_tokens → mint → bundle`; K3 composes from `bind`+`permute` (an `ngram_bind` convenience would finish it). | **absent** (verified: no `tokenize`/`cooccur` op) |
| **U3** | **Unify the op-discovery surface** — one call (`dsl.list_ops()` or extend `list_cascade_ops()`) that enumerates BOTH value-transform cascade ops (incl. D2 user composites) AND `catalog.list_catalog_chains` entries, each tagged `kind` (stage / combinator / catalog-chain) + `provenance` (`srmech` / `user:<sha>` / `catalog:<source_key>`). | This IS the literal ask: a kernel chain declared on a text-catalog **shows up in the DSL op list**. The two registries already exist; they just don't see each other. | two **disjoint** surfaces (verified) |
| **U4** | **Catalog → DSL auto-registration bridge** — `register_attested_root(...)` of a text-catalog + a declared kernel chain (or one dropped on `SRMECH_CASCADE_PATH`) **auto-appears** in the U3 discovery surface, tagged `catalog:<source_key>`. | "Anyone's text catalog → DSL entry" becomes **one path, not three doors** (`list_catalog_chains` + `SRMECH_CASCADE_PATH` D2 + `use_local_kernel` overlay are the three doors today). | plumbing exists in pieces; **not routed through DSL** |

**Net:** U2 alone unlocks one-line per-catalog kernel chains (the cheapest win, primitive already verified). U1 makes the full presence-kernel pure-TOML-authorable (and retires our `Counter()` hand-roll). U3+U4 are the "shows up in DSL entries for anyone's texts" unification. All four compose with the verified **F289-D2 BYO-cascade-TOML** mechanism (§12.4) and the **`run_toml_chain` compose-engine** (§16) already shipped.

### §17.1 OURS-side follow-on (not an upstream ask) — migrate onto the upstreamed surface
Our hand-rolled kernel-build (R-RBS-LM-52b, the F339 refresh) **predates** `srmech.rbs_lm` + `encode_loe_content` and reinvents what srmech now ships. A parity-check task (OURS): does `encode_loe_content` / the `rbs_lm.encode_*` stack reproduce our K1/K3 signal on the notebooks? Where parity holds, migrate the research scripts onto the upstreamed surface (kills the `Counter()` + `re.findall` hand-rolls; routes through the attested package). This is the srmech-first reflex applied to our own tooling debt.

### §17.2 "Anything else upstream?" — consolidated open carry-forwards (as of rc21)
| item | kind | state |
|---|---|---|
| §15.1 `cascade.magnitude(x: float)` real-only | contract/doc | OPEN — complex modulus leaks internal `>`; ours: CLAUDE.md over-describes it |
| §16.1 `cascade.reorient(orientation, value)` data-arg-second | DSL-stage-contract | OPEN — un-invokable as bare `op=`/`parallel_body=`; new this session |
| §13 **D4** CLI top-level help stale string | doc nit | OPEN — still not re-tested (package-API verification only) |
| §17 U1–U4 catalog→kernel→DSL unification | feature/design | NEW this entry |

All **recorded, NOT filed** per `[[feedback_create_upstream_issues_never_close_them]]` — tracker state is the user's/maintainer's call; the design stands regardless.

## §18 rc25 (0.7.0rc25) VERIFIED CLEAN — §15.1 + §16.1 RESOLVED; #797 gate DELIVERED; open-issue triage pass (2026-06-03)

Full bug-test of `srmech==0.7.0rc25` (TestPyPI, clean venv `/tmp/verify_srmech_v070rc25`, cp314 native wheel + numpy 2.4.6): `native_status` = `{has_native: True, abi_version: 3, native_version: '0.7.0rc25', load_error: None}`; tool_schema **201**. **No regression** — all rc21/§16 surfaces re-confirmed (loop_bind/hd, klein4 `mode=`, kuramoto `adjacency=/alpha=`, so8 **28** / g2 **14**, triality τ³=I **3.66e-15**, `run_toml_chain` compose-engine runs `magnitude(-5)→5.0`). Scripts: `/tmp/verify_rc25.py`.

**Both prior findings RESOLVED by rc25:**
- **§15.1 (magnitude) → FIXED (the (b) path).** `cascade.magnitude(complex(3,4))` now raises a **clean Class-K contract error** (`"Class K real-axis (pin-slot) operation … does not accept complex"`) instead of leaking the internal `>`. Real `|x|` unchanged. *Ours-side residue NOW DONE:* the monorepo `CLAUDE.md` STOP-list line that called it "the modulus; replaces `(re²+im²)^0.5`" is corrected — it is the **real `|x|`** abs-replacement, not a complex modulus.
- **§16.1 (reorient) → FIXED (the (a) path).** Signature is now `reorient(value, *, orientation: int)` — **data-first**, orientation keyword-only. Verified as a DSL stage: `[[stage]] op="reorient"` `orientation=-1` on input `7.0` → **−7.0** (clean, no arg collision). The bare `op="reorient"` with no orientation still errors — but that is **correct-by-design** (a reorientation needs a direction), not the contract bug. Resolved.

**#797 gate — ~~DELIVERED~~ CORRECTED to PARTIAL (§20, 2026-06-04, per srmech-dev status).** rc25 ships **`_native.cascade_parallel_sector_dispatch_c`** (the four-Klein-4-sector dispatch, native-C, `parallel_equals_serial=True`, `cross_sector_reads=0`, `runtime_verified=True`) — **but srmech-dev confirms this is NOT #797's gate.** #797 waits on TWO *different* ops at C/Python parity: an **order-3 triality-recursion (PAST the Klein-4 4-cap)** + a **Class-L directed/signed-Laplacian eigen-op**, both still unbuilt. The sector-dispatch is the *order-2 4-cap*, not the order-3 recursion past it — I conflated them. **#797 stays research-gated; see §20 for the op-specs (drawn from F347–F354).**

**Open-issue triage (user-directed close-pass — "if no bug jumps out, close them, so we can track the research-gated srmech items"):**

| issue | kind | rc25 result | action |
|---|---|---|---|
| **#843** RBS-NN→RBS-SNN rename | naming-adoption | `srmech.rbs_lm` has **no NN-named identifiers** → nothing to rename; research relabel adopted (F311/F317) | **CLOSED** (settled) |
| **#823** post-rc2 ungate tracker | gate-tracker | last blocker (compose-engine/`run_chain`) cleared rc21/§16; native sector dispatch rc25 → all gates down | **CLOSED** (ungate complete) |
| **#797** field-first MFO inversion | research, gated | gate **delivered** (sector-dispatch C parity) → ungated; Q1/Q2/Q3 still undone | **KEPT OPEN** + commented (ungated, ready under #855) |
| **#812** loop-bind capacity char | research | native loop_bind + klein4 baseline + sector C parity present → ungated | **KEPT OPEN** + commented (ready; = #855 R1) |
| **#844** notebook-native TARGET / **#855** epic | forward targets | n/a | kept open |

User explicitly authorized closing this pass (the direction `[[feedback_create_upstream_issues_never_close_them]]` said to wait for). Each close carries a transparent rc25 verification comment; reopen if a blocker resurfaces.

**Net: rc25 cleared the last srmech gates.** No srmech-package item still blocks research — #797/#812 are now ungated-ready under #855; the **HOLD lifts**. Working venv `/tmp/verify_srmech_v070rc25` = new latest-verified.

## §19 Taking the RBS-SNN bottom-up findings upstream: the 3-tier division (TOML-now vs new-leaf-primitive vs default-profile) (2026-06-04)

**Question (user):** the bottom-up findings are now measured — Klein-4-native store (F341), save/fetch bit-exact + the rotate-DoF (F350), the holographic-EC hybrid (F352/F353/F354), the navigation manifold (F347/F348). *Which become a DEFAULT srmech path, and which are manageable in the TOML?* The answer is a 3-tier sort, composing with §17:

**Tier 1 — manageable in TOML NOW (the F289-D2 BYO-cascade mechanism, §12.4).** Any finding that is a **composition of *registered* cascade-ops** can be authored as a pure-TOML `[composite]` dropped on `SRMECH_CASCADE_PATH` — no srmech code, B-tier provenance. Covers: the save/fetch cascade (`bind → bundle → unbind`), the EC reconstruct (flips + a majority fold), the navigation pipeline — **IF their leaf ops are DSL-registered** (the catch).

**Tier 2 — needs NEW LEAF primitives upstream (NOT expressible as a composition of existing ops):**
- **§17 U1** — `tokenize`, `cooccurrence_edges` (text→graph; the K1 / navigation-map leaves).
- `fiedler_embed` — the low-eigenvalue navigation embedding (F348); composes from `hermitian_eigendecompose` + low-eigvec-select, cleaner as a primitive.
- `klein4_project_axis` — the iω₇-collapse / bipolar projection (F350/F354; the asymptotic-DoF render).
- `klein4_cpt_orbit` + `parity_majority` / `erasure_reconstruct` — the CPT-orbit EC store + the parity-vote (F353/F354).
- **§17 U2 (THE BRIDGE, highest leverage):** register the existing `klein4_{bind,unbind,bundle,*flip}` + `loop_bind*` + `encode_loe_content` as **DSL cascade-ops**. Without this, the Tier-1 TOML composites have nothing to reference — **U2 is what unlocks Tier 1.**

**Tier 3 — DEFAULT PATHS (upstream profiles/catalogs).** To make a finding a *default* (not merely authorable), srmech ships it as a named profile/catalog descriptor — e.g. an `rbs_snn_store` profile (Klein-4-native save/fetch + CPT-orbit EC), a `navigation_map` cascade, a `truth_filter` (k=2-detect/k=3-correct) op. BYO-TOML makes them *authorable*; shipping makes them *default* (`siona.profile("rbs_snn")`).

**Dividing line — the direct answer to "manageable in the TOML?":**
- composition of **registered** ops → **TOML** (Tier 1);
- **new leaf** op → **upstream** (Tier 2);
- **default** (not just authorable) → **upstream profile** (Tier 3).
So: **PARTIALLY manageable in TOML — but only after §17 U2 registers the leaf ops; the genuinely-new leaves (tokenize / cooccurrence_edges / fiedler_embed / klein4_project_axis / klein4_cpt_orbit / parity_majority) MUST go upstream; and "default paths" are inherently upstream (TOML is authorable, never default).**

**Consolidated upstream ask = §17 (U1/U2/U3/U4) + the new leaves above + the Tier-3 RBS-SNN profiles.** Highest-leverage single change: **U2** (register the hdc/loop/loe ops as DSL ops — it converts the whole save/fetch + EC + navigation family from "needs code" to "authorable in TOML").

**DATA-side peer (distinct from the op gaps):** the **CMB EB/TB parity-odd spectra + cosmic-birefringence β posterior** — `srmech.amsc.attested.cmb_*` ships TE/EE/BB (parity-even) but **NOT** EB/TB (parity-odd = the cosmic-band chirality observable; **the one chirality datum at that band is the one not shipped**). Already filed: **#743 (CLOSED)** with the attestation sources **Eskilt–Komatsu 2022 (arXiv:2205.13962)** + **Minami–Komatsu 2020 (arXiv:2011.11254)**. This is the data the F263/F352 CMB falsifier needs — a *catalog* gap, peer to the *op* gaps above.

## §20 #797's two gating ops, specced from the F347–F354 research (data for srmech-dev to integrate; corrects §18) (2026-06-04)

> **STATUS — BOTH OPS LANDED in rc28 (F360, 2026-06-04).** srmech-dev built both from our F357/F359 specs (rc28 docstrings cite "op (a1)"/"F359"). **op (b):** `laplacian.magnetic_laplacian` (directed Hermitian) + `signed_laplacian` + `dense_adjacency` (the directed-edge builder) + `fiedler_vector` — CONFIRMED as the F357 directed Hermitian (Hermitian, real eigs, directed-sensitive). **op (a1):** `hdc.klein4_triality_{encode,cycle,correct}` — corrects 1 blind error (rate 1.00, breaks at 2 = distance-1), 3 votes from the orbit of ONE store (order-3, τ³=I, = Aut(Z₂²)=S₃ 3-cycle on {γ₅,iω₇,cpt}). **CORRECTION:** the F359 "beats 0.25 baseline" was a misread of F353's distance-1 as a rate; order-3 is the MINIMAL native 3-vote encoder, NOT a unique corrector (any ≥3-fold majority corrects 1 error). Harness `triality_test_harness_scaffold.py` now PASS=6 / triality live. The WIDTH-step is delivered; F256's COUNT-recursion stays open math (out-of-domain by design). **Also: calc/trig restored in rc28** (`asymptotic_calculus`/`trigonometry` series-truncate) — closes the F356 general-β gap; CLAUDE.md §2 path live again. **#797's op-gate is cleared; only the (substantive, undone) research Q1/Q2/Q3 remain.** Details below are the as-specced record.

**srmech-dev status (2026-06-04):** #797 waits on TWO ops at C/Python parity, and dev is leaving the motivating research to us (the Q1/§4/§5 work is ours): **(a)** an order-3 **triality-recursion** op (past the Klein-4 4-cap); **(b)** a **Class-L directed/signed-Laplacian eigen-op**. The `triality_test_harness_scaffold.py` fires when (a) lands. **Correction to §18:** the rc25 `cascade_parallel_sector_dispatch_c` is the *order-2 4-cap* (Klein-4 four-sector), **not** these two ops — §18's "#797 gate delivered" is withdrawn. **Our F347–F354 ARE the #797 research; the spec follows.**

**(a) triality-recursion (order-3, past the Klein-4 4-cap) — spec from F352/F353/F354:**
- **WHY:** the order-2 Klein-4 store is **k=2-DETECT** natively (F354 axis-split; F294 no-Z3, 3∤4). **k=3-CORRECT needs the order-3 triality** (τ³=I, F192/F291) — the recursion past the 4-element Klein-4 cap into the order-3 / 3⊕3̄ (F197). This IS #797 Q1 (k=3 ≡ triality ≡ B/H/N).
- **WHAT:** apply the order-3 triality automorphism recursively to lift the order-2 Klein-4 to order-3 correction, at C/Python parity (the harness scaffold targets it).
- **MEASURED ALTERNATIVE (F352/F353):** the **holographic-erasure route** needs **no** order-3 corrector — F353's erasure-tolerance 3/4 (reconstruct-from-subregion) supplies the correction without a Z3. So op (a) gives the *explicit* order-3 correction; the holographic route (order-2 + part-contains-whole) is the *measured alternative*. **Data for dev:** build (a) for the explicit-corrector path, OR rely on the order-2 + erasure code — we measured both (F353/F354).
- **FALSIFIABLE CONTRACT (F359, 2026-06-04; user scope decision "spec + harness only"):** op (a1) is **scoped to the finite WIDTH-step only** (cross the Klein-4 4-cap once: order-2→order-3, read a 2-of-3 majority). F256's **count-recursion into the continuum stays OUT of scope** (open math, "let the math tell it"). Acceptance bars the `triality_test_harness_scaffold.py` SKIP-gates should assert: **(1)** blind unknown-location single-error correction rate **> F353 baseline 0.25**, toward ~0.75; **(2)** the 3rd vote comes from the **order-3 triality orbit of the SAME store** (no external 3rd render — the line vs F344's stipulated-copies demo); **(3)** C/Python parity; **(4)** disable the order-3 op → degrade to k=2-DETECT (F354) (correction must be *attributable* to the triality); **(5)** width-only — return **out-of-domain** if probed for the continuum-recursion, never fabricate. The triality **automorphism** ships (`qm.triality`); the missing build target is the **cascade-store corrector op** (apply it to error-correct a store, at C/Python parity). Contract is A-tier; the blind-correction capability is C-tier (open) until a candidate passes bars 1–5.

**(b) Class-L directed/signed-Laplacian eigen-op — spec from F347/F348:**
- **WHY:** the navigation manifold (F348) is the low-eigenvalue **Fiedler eigenVECTOR** embedding of the co-occurrence Laplacian — currently **undirected** (symmetric, `hermitian_eigendecompose`). The directed/signed version enables **directed navigation** (asymmetric co-occurrence / grid-cell directionality) + the **signed-metric** (the Class-O-dissolved-into-Class-L variant, CLAUDE.md §1; the F240/F241 directed-coupling gap, currently ngspice-routed).
- **WHAT (corrected — NO new eigensolver needed; srmech-native):** the directed/chiral structure is a **Hermitian** object — `H = i·(A − Aᵀ)` (F173/F175's directed γ₅-odd antisymmetric Hermitian; the magnetic-Laplacian approach to directed graphs), and a **signed** Laplacian is real-symmetric. So the eigen step is the **EXISTING** `hermitian_eigendecompose` (complex-Hermitian → real eigenvalues + complex eigenvectors carrying the directed/chiral structure) / `symmetric_eigendecompose`. **No `np.linalg.eig` / non-Hermitian solver is required.** The genuine gap is therefore the **directed/signed-edge → Hermitian-Laplacian BUILDER** (a Class-L precursor forming `i(A−Aᵀ)` from directed co-occurrence edges — the directed sibling of the §17 U1 `cooccurrence_edges`), NOT a new eigensolver.
- **DATA:** F348's undirected baseline (Fiedler embedding shuffle-fragile, r=0.214) is the control; the directed-Hermitian map (`hermitian_eigendecompose(i(A−Aᵀ))`) gives the directed navigation map (the next measurement, **buildable srmech-native NOW**). The op (b) gap shrinks to a directed-edge builder + the existing Hermitian eigen.
- **REFERENCE BUILT (F357, 2026-06-04):** `R-RBS-LM-R11_directed_laplacian_navigation_reference.py` runs the full op(b) path rc25-native: directed adjacency A → `H = i(A−Aᵀ)` (verified Hermitian, `H==H†` True) → `hermitian_eigendecompose(H)` (real eigenvalues True — **no numpy eig**). Measured the srmech-notebook co-occurrence is 29% directional (asymmetry 0.294) — content the undirected Fiedler discards. Honest sub-finding: gross asymmetry *magnitude* has a sampling-noise floor (shuffle 0.190), so the **specific** directed pattern (shuffle-fragile, r=−0.019) is the valid discriminator, not the magnitude. **The eigensolver ships; the only build target is the directed-edge adjacency helper** (the directed sibling of the §17 U1 `cooccurrence_edges` — a Class-L precursor, not a new eigen-op). This is the reference srmech-dev can build the C op(b) against.

**Net for srmech-dev:** F347–F354 = the #797 Q1/§4/§5 research, done; **op(b) reference now built (F357).** Op (a) (triality-recursion): build for the explicit-corrector path; the holographic-erasure code (F353) is the measured alternative. Op (b) (directed/signed-Laplacian eigen): the genuine new primitive (directed navigation, F348). #791 (waits on ngspice/#787) + #788 (un-gated; gates the dollar-gated LLM trials — diagnostic-only per F166/F351, not the native goal) noted. #797 stays research-gated on op (b) at minimum. Recorded for integration; #797 updated.

## §22 numpy-drop decision — research-subtree recommendation: OPTION 1 (make numpy optional), for framework-identity NOT as a reflex-fix (2026-06-04)

srmech-dev asked how far to take dropping numpy (4 options: optional / core-only / status-quo / drop-entirely). Recommendation from the RBS-LM research subtree, grounded in this session's numpy-reflex catches (the user caught it 3x; once it saved a wrong claim — the F372 so(8)-shadow artifact):

**RECOMMEND OPTION 1 — make numpy optional.** Core 14-class A-N vocabulary (HDC / cyclic / primes / rational / laplacian-build / hash / cascade) goes numpy-free via the C path + stdlib array/ctypes boundary + small pure-Python fallback; `qm/*` + `signal_processing` keep numpy behind a `srmech[scientific]` extra.
- **Why 1, not the others:** the line Option 1 draws IS the framework's own identity line — the A-N primitive vocabulary is the "runs embedded without numpy/LAPACK" story (the C lib already backs it: `hermitian_eigendecompose` / `jacobi_eigvals` / `autocorrelation` / cascade primitives), while `qm/*` is genuinely LAPACK (eigh/svd/eig/qr/solve) — a hard wall. **Leaving numpy for the python-side triality/qm maths is correct** (user's lean); reimplementing LAPACK in C fights the JPL-clean / C-stays-LAPACK-free stance. Option 2 leaves numpy a hard dep (no actual removal); Option 3 leaves the Python layer hard-deps numpy (no `pip install srmech` without it); Option 4 (reimplement eig/svd/fft) — advise against.
- **Boundary-type lever (the one srmech-side thing that helps the reflex):** have the **core** ops return framework-native handles / stdlib types, NOT raw `np.ndarray` — a numpy-typed return invites `np.dot`/`np.linalg` on it; a handle forces the srmech op. `qm/*` can keep returning numpy (the `[scientific]` opt-in surface). Fold into Option 1 for the core.

**HONEST CAVEAT (load-bearing):** dropping numpy from srmech will **NOT** stop the agent-reflex. Every miss this session was in the research agent's OWN scripts (`import numpy; np.linalg.eig`, hand-rolled so(8) plane rotations), not srmech internals. The reflex-fix is (a) the CLAUDE.md §2 STOP-list/forcing-frame, (b) the user spot-check, (c) the ops existing + discoverable (they do). Choose Option 1 for the framework-identity / embedded-install reasons (real + good), not as a reflex cure.

**Companion research-side action (higher leverage for the reflex than the package change): extend the CLAUDE.md §2 STOP-list** with the exact ops missed this session — `np.linalg.eig/svd` on a generator → `laplacian.hermitian_eigendecompose`; hand-rolled so(8)/triality rotation → `qm.so8` / `qm.triality.triality_apply`; `np.dot`/cosine → `hdc.similarity`; `np.cos/sin` → `asymptotic_calculus.{sin,cos}_series_truncate` (restored rc28). The forcing-frame currently covers Class-L/Klein-4 but NOT the 28D/so(8)/triality ops — that gap is exactly where the F372 artifact slipped in.

## §21 ephemerides-spectral cosmos-catalog dependency — deferred srmech-0.7.0 bump (user direction 2026-06-04)

The CMB/cosmos catalogs the RBS-LM CMB arc reads (`cmb_anomalies`, `cmb_power_spectrum`; F355/F356/F368/F370) live in the **ephemerides-spectral** sister subtree, which is **NOT on the latest srmech base** (it pins an older srmech). User direction:

1. **Update ephemerides-spectral → srmech 0.7.0 when 0.7.0 lands on LIVE PyPI** — NOT before (rc ≠ SoT, per `[[project_srmech_mcp_repoint_deferred_until_live]]`). Tracked here as a release-coordination task for the production-PyPI cut.
2. **OR, if a local copy is ever needed under `docs/srmech/rbs_lm_research/`, copy the catalogs but DO NOT TRACK them** (gitignore the copy) — they are the sister package's attested data, not ours to vendor-commit.

**Current state (no action needed now):** the CMB findings read the catalog NDJSON **in place from the in-repo ephemerides-spectral subtree** (`docs/antikythera-maths/research/attested/cmb_anomalies/row.ndjson`) — already tracked in the monorepo, version-independent (data, not code), so reading it involves **no copy and no srmech-version coupling**. The deferred bump (1) only matters when ephemerides-spectral's *package* is installed/run against srmech 0.7.0.

---

## §22b HV carrier contract — confirmed


**HV carrier contract — CONFIRMED (research-side double-check, 2026-06-04).** srmech-dev's proposed numpy-free hypervector carrier (`HV` = `array.array('B')` buffer + sectors; returned by the core ops so no implicit `np.ndarray` escapes — the §22 lever) is **right; build rc29 against it.**
- **(a) `array('B')` + buffer-protocol C boundary — yes.** Klein-4 ∈ {0,1,2,3} fits `'B'`; contiguous + buffer-protocol → ctypes-direct, numpy-free. *Confirm in-code:* the C ops read/write the `array('B')` buffer in place so **HAS_NATIVE keeps HV fast** (pure-Python HV is only the no-native worst case).
- **(b) value-equality + `.tolist()`/`.tobytes()`/`.to_numpy()` only — yes (this IS the reflex-guard).** *Confirm:* `hv == other` returns a **scalar bool** and **accepts `np.ndarray`** (clean `np.array_equal(rec,v)` → `rec == v` migration); `hv[i]` returns a **plain int**, not a numpy scalar (else a numpy scalar leaks + re-invites np-math).
- **(c) start with the Klein-4 family — yes.** Cohesive uint8, highest-traffic surface, rc27/28 ops fresh, and *exactly where the reflex bites hardest* (the chirality/triality ops that produced the F372 artifact). HV distinct from `SpectralHandle` — **agree, keep lightweight.**
- **Division of labor:** HV guards the **core/Klein-4** surface; **do NOT HV-wrap `qm/so8/triality`** — that's the LAPACK layer, keep it numpy-typed (§22), guarded instead by the CLAUDE.md §2 STOP-list (extended 2026-06-04 with the so(8)/triality + continuous-trig + magnetic_laplacian rows). **HV + STOP-list together cover both surfaces** (the F372 miss was qm-side — HV wouldn't catch it; the STOP-list is its guard).
- **Arc rc29→rc33 sound** (numpy stays hard-dep until the rc32 `[scientific]` flip; rc31 ~150-LOC pure-Python Jacobi fallback is the one genuine new code). GO.

---

## §23 QDFT/ODFT — quaternion/octonion fast transforms upstream (GitHub issue #863; F380) (2026-06-04)

**Issue filed:** #863 `[srmech][rbs]` — *"Quaternion/octonion fast transforms (QDFT/ODFT) — the native transform for a Klein-4 object, not its complex flat shadow."* Links #855 (RBS-SNN umbrella) + #844 (forward-arch pipeline). **Leave open/closed state to the maintainer.**

**Motivation (F380, user direction "we need this to QFT a klein-4 object … not just it's flat shadow"):** a Klein-4 object's native spectral transform is the **quaternion FT**, because **Klein-4 = Q₈/{±1} = the quaternion units mod sign** — proved srmech-natively in `R-RBS-LM-R21` (the Q₈ coset table == `hdc.klein4`'s XOR table, identity relabel; Q₈ non-abelian but the quotient abelian). A *complex* FFT projects to ℂ (units mod sign = Z₂) → resolves **one** chirality axis = the flat shadow; the QDFT's coefficient algebra ℍ (units mod sign = Klein-4) resolves **both** (γ₅ & iω₇).

**The decision: cascade-first, NO capability gap.** rc28 already ships every primitive: the algebra-agnostic Cooley-Tukey cyclic radix split (`amsc.primes.factor` + `amsc.cyclic`), the scalar twiddle (`asymptotic_calculus.{cos,sin}_series_truncate`; order-3 root `cyclic.three_cycle`), and the hypercomplex left/right multiply (`qm.octonion.octonion_{left,right}_mult` + `octonion_mult_table`/`octonion_norm`). Per lean-ISA atoms-vs-composites: the multiplies are **atoms** (primitives); the transform is a **composite → TOML cascade** (prototype tier), graduating to a C/Python primitive via the full ratchet **only if it earns first-class attested status** like the existing `signal_processing.closed_form_ops.fft` (the complex 2:1 rung). Cascade is the on-ramp, not a blocker.

**Two structural caveats (in the issue):** (1) **non-commutativity** (ℍ,𝕆) → genuine left/right/two-sided forms; the twiddle can't be factored out, the cascade calls the explicit multiply. (2) **non-associativity** (𝕆 only) → the ODFT is **not unique**; it must **declare a bracketing convention** (F378's 168/210 triples) as an explicit attested descriptor field.

**Descriptor skeleton DRAFTS** (in this subtree, NOT the package — do-not-edit-srmech discipline): `R-RBS-LM-R22_quaternion_dft.draft.toml`, `R-RBS-LM-R22_octonion_dft.draft.toml`. Faithful to the shipped `autocorrelation.toml`/`kuramoto_step.toml` schema; the maintainer lifts them into `cascade_catalog/` when QDFT graduates.

**Two OPTIONAL ergonomic upstream additions (the only things that would go upstream as *new code*; not blockers, maintainer's call):**
- a first-class **`qm.quaternion`** module (4×4 `quaternion_left_mult`/`right_mult`) so the QDFT cascade doesn't slice the 8×8 octonion block (mirrors the `qm.octonion`/`qm.so8` split);
- a hypercomplex **`exp(μθ)`** twiddle helper (cos·1 + sin·μ̂), composable from `asymptotic_calculus` + a unit imaginary.

**Citation debt (carry forward):** the quaternion-DFT literature (Ell/Sangwine/Bülow) + the octonion-Fourier-transform literature are **verify-PDF-owed before any citation lands** (F378). The draft descriptors mark these `VERIFY-PDF OWED — NOT yet attested`. Also: Artin's theorem (2-generated octonion subalgebra is associative) explains why the quaternion-subalgebra embedding recovers the unique QDFT — verify a standard algebra reference before citing in package docs.

---

## §24 rc47 (0.7.0rc47) VERIFIED — the numpy-removal landed; outward API changes + the hdc GAP (2026-06-04; F402)

**The numpy-drop (§22 Option 1) shipped in rc47.** Verified in two clean venvs OUTSIDE the source tree (`/tmp/verify_srmech_v070rc47` plain; `/tmp/verify_srmech_v070rc47_sci` = `srmech[scientific]`). This **lands the gate** BX-5..BX-8 / ALU-D / AX-2 were waiting on. `native_status()` = `{has_native:True, dispatching:True, abi_version:3, expected_abi:3, native_version:'0.7.0rc47', load_error:None}`.

**OUTWARD API CHANGES (a subagent/script must know — "look before you leap"):**
1. **`srmech.HAS_NATIVE` is REMOVED** → use **`srmech.native_status()`** (a dict). Old code doing `srmech.HAS_NATIVE` AttributeErrors. (`srmech.amsc._native.HAS_NATIVE` still exists internally.) **CLAUDE.md / docs/srmech/CLAUDE.md still say `HAS_NATIVE` — update on the clean-tag pass.**
2. **numpy is now OPTIONAL.** Plain `pip install srmech` is **numpy-free**; **`pip install 'srmech[scientific]'`** adds numpy.
3. **Tiers (verified, all COMPUTE not just import):**
   - **numpy-free core (plain install):** `amsc.format` (A), `amsc.cyclic` (I), `amsc.primes` (J), `amsc.rational` (N), `amsc.cascade` (K/C/atoms), **`amsc.laplacian` (L)** — `dense_laplacian` now returns a **plain `list`**, and **`jacobi_eigvals` runs numpy-free** (C₄ → `[0,2,2,4]`). **⇒ numpy-free Class-L landed (ALU-D unblocked).**
   - **scientific tier (`srmech[scientific]`):** `qm.*`, `signal_processing` — **GATED with a clean, instructive `ImportError`** ("part of srmech's scientific tier and needs numpy … `pip install 'srmech[scientific]'`"). Good.
4. **HV carrier confirmed (§22b contract holds):** `hdc.klein4_*` returns **`srmech.amsc.hv.HV`**, NOT a raw `ndarray`. `v==w` → **scalar `bool`** (accepts `ndarray`: `v == v.to_numpy()` → True); `v[i]` → **plain `int`**; `.tolist()`/`.tobytes()`/`.to_numpy()` (uint8)/`.sectors`(=4). **numpy never escapes implicitly** — the reflex-guard works.

**GAP (upstream ask): `srmech.amsc.hdc` (Class M / Klein-4) still hard-imports numpy at module top** (`import numpy as np`, hdc.py:36). On a **plain (numpy-free) install** `import srmech.amsc.hdc` raises a **raw `ModuleNotFoundError: No module named 'numpy'`** — *inconsistent*: hdc *returns* the numpy-free HV carrier, yet its module won't import without numpy, and it does NOT emit the clean `[scientific]` gate message like `qm` does. **Fix:** either (a) make hdc's numpy import lazy/optional so Klein-4 is genuinely numpy-free (the HV carrier already is), or (b) gate hdc behind `[scientific]` with the same clean message as `qm`. Right now Klein-4-on-plain-install is the one broken seam. **→ RESOLVED in rc48 via option (a) — issue #882 closed upstream 2026-06-05; clean-venv re-verified in §25.**

**Queue impact:** BX-8 (rc-verify HV + numpy-drop) ✅ done by this. ALU-D (numpy-free Class-L) ✅ demonstrated (`jacobi_eigvals` numpy-free). AX-2 / BX-5..7 are now **rc47-walkable** (M works on `[scientific]`; qm works on `[scientific]`) — pending user direction + the hdc-gap caveat for plain installs.

---

## §25 rc48 (0.7.0rc48) VERIFIED — the §24 hdc GAP RESOLVED (#882 closed); srmech-slug closeout verdict (2026-06-05)

**rc48 lands the §24 GAP fix.** Verified in two clean venvs OUTSIDE the source tree (`/tmp/verify_srmech_v070rc48` plain; `/tmp/verify_srmech_v070rc48_sci` = `srmech[scientific]`). `native_status()` = `{has_native:True, dispatching:True, abi_version:3, expected_abi:3, native_version:'0.7.0rc48', load_error:None}`.

**#882 (the §24 hdc GAP) — FIXED via option (a), the strongest form.** On a **plain numpy-free install**, `import srmech.amsc.hdc` now succeeds and `hdc.klein4_random(16, seed=1)` returns the **`srmech.amsc.hv.HV`** carrier with NO numpy — Klein-4 (Class M) is **genuinely numpy-free**, not merely gated behind `[scientific]`. Round-trip `klein4_bind(klein4_bind(a,b), b)` recovers `a` at similarity **1.000**. The one broken seam §24 flagged (Klein-4-on-plain-install) is closed. **#882 was closed upstream 2026-06-05** (the maintainer's call — I did NOT close it; `[[feedback_create_upstream_issues_never_close_them]]`); this §25 is the independent clean-venv confirmation that the fix **holds**.

**No regressions** (the "look before we leap" sweep): numpy-free core intact — A `sha256_bytes(b'abc')`=`ba7816bf…`, I `gcd(48,36)`=12, N `best_rational(375,1000,16)`=(3,8), K `cascade.magnitude(-5)`=5, **L `jacobi_eigvals` numpy-free** → C₄ `[0,2,2,4]`. `[scientific]` tier installs numpy 2.4.6 + `qm.*` imports clean (12 submodules incl. octonion/triality/so8). HV carrier §22b contract holds (`srmech.amsc.hv.HV`). *(Two non-bugs caught during the sweep, NOT srmech defects: `triality_companions()` needs a `g_v` arg — my probe omitted it; `primes.factorize` is the wrong attr name in my probe.)*

**OUTWARD API RENAME (user-flagged 2026-06-05): `srmech.asymptotic_calculus` → `srmech.calculus`** — *"asymptotic was removed from calculus, it's just calculus."* The canonical module is now **`srmech.calculus`** (verified rc48: ships all `*_series_truncate` ops — `sin/cos/atan/exp/log1p` — plus `exp`/`cexp`/`complex_exp` and absorbed `best_rational`/`continued_fraction`/`atan2`/`hypot`). **`srmech.asymptotic_calculus.*` + `srmech.trigonometry.*` survive as back-compat shims** (both still importable in rc48 — `asymptotic_calculus.py` still on disk). Updated CLAUDE.md §2 (STOP-list row + key-imports row + the π-as-cascade and catalog-peers references) and regenerated CLAUDE_LEAN to the canonical name; **historical findings/notes keep the old name as their attestation record** (same discipline as the research-twin retirement). This is the calculus-rename sibling of §24's `HAS_NATIVE` → `native_status()` change.

**CLOSEOUT VERDICT — srmech-slug bucket** (user criterion 2026-06-05: *"we close them when bugs AND features are all resolved for that issue tracker item"*):
- **#882** (hdc numpy bug) — **RESOLVED + already CLOSED.** Bug fixed (option a), clean-venv verified. ✓
- **#863** (QDFT/ODFT) — **KEEP OPEN.** Feature NOT landed: the QDFT/ODFT transform is still **draft-TOML only** (BX-5 pending), AND neither optional-upstream ergonomic ask shipped in rc48 — **no `qm.quaternion` module** (qm has `octonion` w/ `octonion_left_mult`/`octonion_right_mult`, no 4×4 quaternion peer) and **no hypercomplex `exp(μθ)` twiddle** (`asymptotic_calculus` has scalar `exp`/`cexp`/`complex_exp` only). Bugs none; features open ⇒ not closeable.
- **#855** (TRACKING umbrella) — **KEEP OPEN by design** (meta-tracker for the full RBS-SNN/RBS-LM build-out).
- **#844** (TARGET notebook-native pipeline) — **KEEP OPEN** (forward target, not built; = task #197).

**Net:** rc48 resolved exactly **#882** of the srmech-slug bucket, and it is already closed; **no NEW closes warranted.** The remaining open srmech-slug issues (#863 / #855 / #844) are feature/tracking/target items with work still pending — they close when their *features* land, per the user's criterion.

---

## §26 Class-L gap: Schur complement / Dirichlet-to-Neumann (the holographic-boundary op) (2026-06-05; BX-1/F412)

**Surfaced by:** BX-1/F412 — the holographic principle IS the framework's fibration (boundary=base, bulk=total, fiber=emergent radial dim), and its srmech-native operator is the **Class-L Laplacian Schur complement** = the boundary effective Laplacian (interior/bulk integrated out onto the boundary) = the discrete **Dirichlet-to-Neumann map**.

**Gap (verified rc48 surface):** `srmech.amsc.laplacian` ships the build-blocks — `dense_laplacian`, `dense_matvec_complex`, `hermitian_eigendecompose`/`symmetric_eigendecompose`/`jacobi_eigvals`, `normalized_laplacian`, `fiedler_vector`, `three_fold_eigvec_groups` — but **no `schur_complement` / `dirichlet_to_neumann` / linear-solve** symbol.

**Candidate addition:** `srmech.amsc.laplacian.schur_complement(L, boundary_idx) -> S` (= `dirichlet_to_neumann`), the boundary effective Laplacian `S = L_∂∂ − L_∂i·L_ii⁻¹·L_i∂`. Use cases: the holographic-boundary / bulk-integrate-out reading (F412); boundary-conditioned spectral problems; the **area law** as `rank(S) = |∂|` (boundary modes, not bulk volume). **Composite note (F392):** the interior block solve `L_ii⁻¹` is an inverse = **Class C→K** (no divide primitive; iterative shift-sub) — so this grades from a composite (matvec + a Class-K solve) to a first-class Class-L primitive via the full ratchet, exactly like the shipped eigendecompose.

**Status: ✅ RESOLVED in srmech 0.7.1 — GH #897 CLOSED (2026-06-06, user-authorized).** 0.7.1 shipped exactly the ask: `laplacian.schur_complement(L, boundary_idx, *, exact=False)`, its `dirichlet_to_neumann` alias, AND the supporting `dense_solve(A, B, *, exact=False)` — with an **`exact=` flag (exact-rational `Fraction`, numpy-free)** (the Class-C→K block solve made first-class). **Verified bug-free** in a clean venv (`srmech==0.7.1`, native 0.7.1): (1) hand-computed truth — path `0-1-2`, boundary `{0,2}` → `[[1/2,-1/2],[-1/2,1/2]]` exactly (series-resistance effective edge); (2) **area law** `S` is `|∂|×|∂|` not bulk; (3) `dirichlet_to_neumann == schur_complement`; (4) 5-node cross-check `== Lbb − Lbi·dense_solve(Lii,Lib)`; (5) exact↔float consistent; (6) `dense_solve` exact (`A·x==b`, `x=[1/5,3/5]`); (7) **the F412 held demo now runs** — boundary `S`-spectrum `[0,1]` = 2 = `|∂|`. This op is the **operator|operand FUSION** (F412/F417/F419): the corpus can now *fuse* (boundary↔spectrum, both kept), not only *project* (operand→operator).

---

## §27 srmech 0.7.0 GRADUATED to production PyPI — the new structure learned (2026-06-05)

**`srmech==0.7.0` is live on production PyPI** (the clean tag; the rc47→rc49 arc consolidated). Verified in a clean venv OUTSIDE the source tree: `native_status() = {has_native:True, dispatching:True, abi_version:3, expected_abi:3, native_version:'0.7.0', load_error:None}`. **numpy is OPTIONAL** (plain `pip install srmech` is numpy-free; `srmech[scientific]` adds it). **`HAS_NATIVE` is GONE → `native_status()`** (confirmed live). **Continuous math UNTOUCHED** (user-confirmed): `srmech.calculus` + the `asymptotic_calculus`/`trigonometry` back-compat shims all import; the five Class-N series-truncate ops (`sin/cos/atan/exp/log1p_series_truncate`) return exact `(num,den)` rationals.

**The structure:**
- **top-level** `srmech.*`: `amsc`, `bus`, `dsl`, `profile`/`profile_loader`/`list_profiles`/`Profile`/`ProfileStatus` (+ Profile* errors), `introspect`, `describe`, `native_status`, `version`, `warmup_all`.
- **`srmech.amsc.*` submodules:** `format`(A) · `cyclic`(I) · `primes`(J) · `rational`(N) · `cascade` · `compose` · `coupling` · `hdc`(M) · `hv` · `laplacian`(L) · `harmonics` · `tlv`(B) · `naming` · `search`(G) · `dispatch`(D) · `catalog`(E) · `template`(F) · `kepler` · `descriptor` · `adapters` · `attested` · `tool_schema` · `gap_suggester` · `_native` · `_research`.
- **NEW/grown submodules:** `hv` (the HV carrier: `HV`/`HVLike`) · `tlv` (Class B: `tlv_pack`, `TLV_PREFIX_BYTES`) · `coupling` (`signed_sum_squared` — **the UPSTREAM §1.2 gap, now shipped**) · `harmonics` (`HARMONIC_PARTITION`, `classify_harmonic`, `classify_chirality_harmonic`, the A-N harmonic ladder) · `naming` (`lookup`, `reverse_order`) · `compose` (`ChainSpec`/`StepSpec`/`DEFAULT_CLASS_REGISTRY` — the operator-chain engine).

**THE ONE `𝕊(σ,θ)` is LIVE** in `srmech.amsc.cascade`: **`the_one(sigma:int, theta_num:int, theta_den:int=1, terms:int=24) -> One`** (+ `One`, `Block`, `s_generator`, `one`). Verified: `.dim==14`, `.partition==(1,3,7,3)`, `.grammar_slots==('B','H','N')`, `.n1_is_sigma_only==True`, `.to_flat_rational()` → 14 exact `(num,den)` pairs (numpy-free). **⇒ the MFO §VIII.31.15 worked example (PR #890) is VERIFIED-correct against the live surface** — the only doc drift is "ships in rc49 / PR #889" → it's now **0.7.0 live** (worth a one-line update).

**QDFT/ODFT (#863) SHIPPED** in `srmech.amsc.cascade`: **`quaternion_dft(x, *, form='left', mu_axis='i', inverse=False)`** and **`octonion_dft(x, *, form='left', mu_axis='i', bracketing='left_associated', two_sided_right_axis='j', inverse=False)`** (+ the `hypercomplex_dft` module). The shipped params ARE the F381/§23 structural caveats: **`form`** = the non-commutativity (left/right/two-sided), **`bracketing`** = the octonion non-associativity declared convention, **`mu_axis`**/**`two_sided_right_axis`** = the unit imaginaries. **⇒ #863 is now CLOSEABLE** (feature landed); **BX-5/6/7 done upstream**.

**~~STILL a gap~~ → RESOLVED in 0.7.1:** **§26 Schur/DtN** (the F412/F419 operator|operand FUSION op) **SHIPPED in srmech 0.7.1** — `laplacian.schur_complement` / `dirichlet_to_neumann` / `dense_solve`, all `exact=`-capable; verified bug-free; **GH #897 closed**. See §28.

**Actionable implications (status 2026-06-06 — maintenance tail cleared):**
1. **#863 (QDFT/ODFT) → ✅ CLOSED** (shipped 0.7.0; re-verified bug-free on 0.7.1 — round-trip + DFT(δ)-flat + linearity, scientific venv; verification comment lodged on the issue).
2. **MFO §VIII.31.15** — ✅ doc-touch "rc49 / PR #889" → "0.7.0/0.7.1 live" done via off-main PR (the_one shipped; the example is verified-correct).
3. **The clean-tag doc pass** — ✅ done in `docs/srmech/CLAUDE.md`: version narrative brought to "0.7.1 live"; **key finding — the top-level `srmech.HAS_NATIVE` was removed → `srmech.native_status()`, but the *internal* `srmech.amsc._native.HAS_NATIVE` still EXISTS** (the dispatch shim references it), so the architecture-doc mentions of `_native.HAS_NATIVE` stay accurate (no rip-out needed); added the public `native_status()` path to the verify snippet.
4. **BX-10 / srmech-mcp repoint UNBLOCKED** (`project_srmech_mcp_repoint_deferred_until_live`: repoint when a clean tag lands on live — it now has). Actionable.

---

## §28 srmech 0.7.1 LIVE — the §26 Schur/DtN fusion op shipped; #897 closed (2026-06-06)

**`srmech==0.7.1` is live on production PyPI** (native 0.7.1, ABI 3, numpy still OPTIONAL; continuous `calculus` UNTOUCHED). 0.7.1 = 0.7.0 **+ the §26 Class-L fusion op**. New in `srmech.amsc.laplacian`:
- **`schur_complement(L, boundary_idx, *, exact=False)`** — the boundary effective Laplacian `S = L_∂∂ − L_∂i·L_ii⁻¹·L_i∂`.
- **`dirichlet_to_neumann(L, boundary_idx, *, exact=False)`** — the alias (the DtN map IS the Schur complement for a Laplacian).
- **`dense_solve(A, B, *, exact=False)`** — the supporting linear solve (the Class-C→K block-inverse made first-class).
- **`exact=`** flag everywhere → exact-rational `Fraction` output (numpy-free); `exact=False` → float.

**Verified bug-free (clean venv, `srmech==0.7.1`):** 7/7 checks — hand-computed truth (`[[1/2,-1/2],[-1/2,1/2]]` series-resistance), area law (`S` is `|∂|×|∂|`), `DtN==Schur`, 5-node cross-check vs `Lbb − Lbi·dense_solve(Lii,Lib)`, exact↔float consistency, `dense_solve` exact, **the F412 held demo runs** (boundary spectrum `[0,1]` = `|∂|` modes). Provenance: `R-RBS-LM-F421_schur_dtn_fusion_verify_provenance.py`.

**⇒ #897 CLOSED (user-authorized).** This op is the **operator|operand FUSION** (F412/F417/F419): the corpus can now *fuse* (boundary↔spectrum, both kept), not only *project* (operand→operator, the one-way Class-L seam F417). The F412 hold is RELEASED (→ F421).

**Re-surface keywords (keyword-search-sweep discipline):** `Schur complement` · `Dirichlet-to-Neumann` · `dense_solve` · `exact-rational` · `area law` · `operator|operand fusion` · `holographic boundary` · `0.7.1` · `#897` · `F412` · `F421` · `§26`.

---

## §29 QDFT/ODFT gap: a GENERAL / DIAGONAL μ-axis for true triality coupling (2026-06-06; F436)

**Surfaced by:** F436 — coupling coherence across 3 kernels. The shipped `cascade.quaternion_dft` / `octonion_dft` expose **named single μ-axes only** (`mu_axis='i'|'j'|'k'|…`). Measured consequence (F436): with a single named axis the transform **carries** N streams (round-trips) but does **NOT couple** them across axes — perturbing the i-stream leaves the j,k streams' spectra untouched (it is a complex FFT on the (1,μ) plane + an independent transform on the rest).

**The genuine coupling needs a DIAGONAL / GENERAL μ** (e.g. `(i+j+k)/√3`, or `(Σeₙ)/√7` for octonion): then `μ·(Gi+Lj+Dk)` folds all three streams into the **real/anchor** channel (`−(G+L+D)` = a joint coherence detector, F436: 3.0× coherent-vs-incoherent energy) while the imaginaries carry the pairwise relations — i.e. the k=3 (quaternion) / k=7 (octonion) coupling + 1 error channel in one object.

**Candidate addition:** allow `mu_axis` to accept a **unit pure-imaginary vector** (general μ), or a `mu_axis='diagonal'` convenience (the equal-weight pure-imaginary axis). Use cases: triality coupling of ≥3 streams + a coherence channel (F436); the lean-hybrid single-kernel sentence carrier (F431→F436). **Composite note:** μ is a unit pure-imaginary quaternion/octonion; the twiddle `exp(μθ)` is already the F381/BX-7 helper — this is exposing its axis, not new algebra.

**Expanded (F437) — the coupling is BIDIRECTIONAL and is a PHASED `(σ, θ, μ)` choice, not "one-way" / "two-way":** the forward fold is `e^{μθ}`; the **reverse is the conjugate `e^{−μθ}` (σ=−1)** — verified exact at ℍ/𝕆, and **guaranteed reversible only up to 𝕆** (division-algebra/Hurwitz boundary; sedenion zero-divisors break it, F424). So the full coupler is parameterized by **σ** (conjugation = forward/reverse = chirality), **θ** (continuous phase), and **μ** (axis) — i.e. **the_one's `𝕊(σ,θ)` (F420) plus the axis μ.** The shipped surface exposes `form=left/right` + `inverse` but NOT general μ and NOT the clean `(σ,θ,μ)` coupler. **The ask, sharpened:** a `hypercomplex_couple(streams, *, axis=μ, theta, sigma=±1)` (or QDFT params extended to general μ + σ + θ) that binds *and* (with σ=−1) unbinds — one reversible coupler, lossless ≤ 7 streams (octonion).

**Status:** **RESOLVED — delivered in srmech 0.7.2rc1, SHIPPED CLEAN TO PRODUCTION PyPI as `srmech==0.7.2` (2026-06-06; re-verified from production, native ABI 3, couple round-trip 8.9e-16) — as `cascade.hypercomplex_couple(streams, *, axis='diagonal', theta, sigma, form, inverse)`; #908 CLOSED (2026-06-06, user-authorized: "if fully delivered and no bugs, close").** Verified 7/7 against the issue's own acceptance criteria in a clean venv outside the source tree (**F448**): general/diagonal μ (`axis='diagonal'`≡`[0,1,1,1]`; bare 3-vector correctly rejected); lossless bind↔unbind ≤𝕆 (3- & 7-stream round-trip ~4.4e-16); the diagonal-μ coherence detector (**2.95×** coherent/incoherent ≈ F436's 3×); the Hurwitz cap (8 streams not lossless); single-axis QDFT regression (1.3e-15). No bugs. Landed-where: **F448** + `R-RBS-LM-F908_hypercomplex_couple_verify.py`. The clean (non-rc) `0.7.2` → production PyPI stays the maintainer's human-gated cut. **Re-surface keywords:** `quaternion_dft` · `octonion_dft` · `mu_axis` · `diagonal axis` · `general μ` · `triality coupling` · `coherence channel` · `bidirectional` · `conjugate twiddle` · `(σ,θ,μ)` · `phased coupling` · `Hurwitz reversibility` · `F436` · `F437` · `§29`.

---

## §30 CARRY/EC gap: a 2ⁿ−1 Hamming / GF(2) block-code op — the sedenion front-loader's missing half (2026-06-06; F449, extends F442)

**Surfaced by:** F449 — actualizing the sedenion **front-loader** (F442) on srmech 0.7.2rc1. The front-loader is **CARRY ∘ COUPLE**: COUPLE (bind ≤7 streams → octonion, reversibly) is now **native** (`cascade.hypercomplex_couple`, §29/#908); CARRY (hold >7 + error-correct in one structure, reversible *past* 𝕆 using the sedenion's CODE structure, **not** its broken chirality) still **hand-rolls**. Measured (F449): a Hamming(15,11) carrier holds **11 data + 4 EC** in one 15-slot structure (1.57× the 𝕆 algebra's 7 reversible slots), locates+corrects any single error (all 15 positions), recovers exactly, fully GF(2)-reversible; the octonion's Fano(7) nests inside (PG(2,2)⊂PG(3,2)).

**What srmech has vs lacks:** the **GF(2) substrate is present** — `hdc._xor_buf` (private) + the lean-ALU `add`/`sub` (parity = XOR = add mod 2); and a **k=3 corrector** exists (`klein4_triality_correct`, the order-3/triality EC). But there is **NO 2ⁿ−1 Hamming / linear block-code op** — no `encode`/`syndrome`/`decode_correct` for the Hamming(7,4)/(15,11)/(31,26)… ladder. F442 + F449 both hand-roll it.

**The ask:** a srmech-native **Hamming / GF(2) linear block-code family** — `cascade.hamming_encode(data_bits, n)` / `hamming_syndrome(codeword)` / `hamming_decode_correct(codeword)` over the 2ⁿ−1 ladder, **lean-ALU XOR-native** (the substrate is already there; this packages the parity-check matrix + syndrome localization). It is the **CARRY/EC** primitive that, composed with `hypercomplex_couple` (COUPLE), makes the front-loader first-class. **Hamming(7,4) = the octonion's own Fano structure (F441)**, so it sits naturally beside the `qm.so8`/octonion surface.

**Non-asks / fences (F449):** (a) the code carries the octonion's **GF(2) sector/structure bits** + EC; the **real-valued coefficients** ride alongside — **real-coefficient EC is a SEPARATE, larger construction** (a real-field block code, RS/BCH-over-ℝ), NOT this ask. (b) the code gives **no multiplicative product** — bind/couple stays the `hypercomplex_couple` job (≤𝕆); carry-vs-couple are distinct roles. (c) **single-error correction** per rung (distance 3); larger tolerance = BCH/RS, a different code.

**Status:** **RESOLVED — delivered in srmech 0.7.2rc2, SHIPPED CLEAN TO PRODUCTION PyPI as `srmech==0.7.2` (2026-06-06; re-verified from production, native ABI 3, Hamming(7,4) decode/correct OK) — as `cascade.hamming_encode(data_bits, n)` / `hamming_syndrome(codeword)` / `hamming_decode_correct(codeword)` (XOR-only lean-ALU; n=parity count 2≤n≤16; codeword 2ⁿ−1; data 2ⁿ−1−n).** Bug-tested **21/21, zero bugs** (F450) in a clean venv outside the source tree: round-trip n=3..6 (Hamming(7,4)/(15,11)/(31,26)/(63,57)); single-error correction at all 53 positions (n=3,4,5); clean informative `ValueError`s on every malformed input; documented double-error mis-correct (no crash); the **front-loader CARRY ∘ COUPLE end-to-end all-native** (Hamming carries the structure bits + `hypercomplex_couple` the octonion reals, both reversible, 2.22e-16). No GH issue filed (user direction: "don't worry about issue tracking; delivered"). Landed-where: **F450** + `R-RBS-LM-F450_hamming_bugtest.py`. The clean `0.7.2` → production PyPI stays the maintainer's human-gated cut (rc1 #908 + rc2 §30 both verified). Fences (F449/F450) carried: GF(2) structure/sector EC only (real-coefficient EC is separate); single-error per rung; no multiplicative product (couple stays ≤𝕆). **Re-surface keywords:** `hamming` · `block code` · `code ladder` · `2ⁿ−1` · `Mersenne` · `parity check` · `syndrome` · `GF(2)` · `XOR` · `error correction` · `CARRY vs COUPLE` · `front-loader` · `sedenion structure not chirality` · `Hamming(15,11)` · `Fano` · `klein4_triality_correct` · `hypercomplex_couple` · `F442` · `F449` · `§30`.

## §31 ERGONOMIC gap (NOT blocking): a first-class `cascade.sedenion_register` + the address↔CD homomorphism — the addressable instrument's wrapper (2026-06-06; F465)

**Surfaced by:** F465 — the **sedenion-ADDRESSABLE hyper-loop RBS-HDC instrument** prototype, which works **today on stock 0.7.3** by hand-assembling existing primitives. The CS reframe (user): "addressable = a larger NAMED structure containing the pieces" → the sedenion (dim 16) as an address space, octonion block `e0..e7` the reversible working set (the `hypercomplex_couple` word, bit-exact ≤𝕆), upper `e8..e15` the EC/carry block (Hamming, §30). The instrument does **HDC ops instead of ALU** (random-access-by-name `bind`+nearest; reversible coupler working word; GF(2) carry) — classical associative superposition, no quantum cost.

**What srmech has vs lacks:** **all the pieces exist** — `amsc.hdc.{bind,bundle,similarity}` (the register read/write), `cascade.hypercomplex_couple` (the ≤7 reversible working word, §29), `cascade.hamming_*` (the carry/EC, §30), `cascade.cayley_dickson.cd_basis_product` (the 16-slot address algebra). What's **lacking is the ergonomic wrapper** that composes them into one named-register object, and the **homomorphism** wiring the HDC address vectors to the sedenion multiplication table.

**The ask (two parts, both ERGONOMIC/compositional — no new algebra; BOTH now prototyped):** (1) a **`cascade.sedenion_register`** object — 16 named slots, `write`/`read`, an octonion-coupler **working word** (≤7 reversible), a Hamming **EC/carry block** (>7); (2) the **address↔CD-product homomorphism** as a `navigate` method so addressing *respects* `e_i·e_j = ±e_k` — **prototyped + verified in F468** (8/8 routing; round-trip reversible; the reversibility horizon carried into the motion).

**Concrete API spec (composes shipped 0.7.3 primitives — `hypercomplex_couple` §29, `hamming_*` §30, `cd_basis_product`/`left_mult_is_invertible` CD, `hdc.{bind,bundle,similarity}`, `chiral_flip`):**

```python
class SedenionRegister:                       # amsc.cascade.sedenion_register
    def __init__(self, D=8192, codebook=None): ...        # 16 named slots e0..e15
    # --- storage (HDC associative, D-bounded capacity) ---
    def write(self, slot:int, vec) -> None              # bind(ADDR[slot], vec) into the bundle
    def read(self, slot:int) -> vec                     # unbind + nearest-codebook clean
    # --- the ≤7 reversible working word (the octonion block, F459) ---
    def couple_working(self, vals:Sequence) -> oct      # hypercomplex_couple(vals[:7])  (bit-exact ≤𝕆)
    def uncouple_working(self, oct) -> Sequence         # inverse=True  (recovers ≤7 exactly)
    # --- the EC/carry block (>7, Hamming, §30/F450) ---
    def carry(self, overflow_bits, n=3) -> codeword     # hamming_encode
    def correct(self, codeword) -> dict                 # hamming_decode_correct
    # --- the operational hyper-loop (F468; the homomorphism) ---
    def navigate(self, j:int) -> "SedenionRegister"     # right-mult slot-names by e_j: content i→±e_{i·j}
    def is_navigable(self, direction) -> bool           # left_mult_is_invertible (reversible ≤𝕆 only)
```

**Non-asks / fences:** (a) **no new algebra** — pure packaging of shipped ops (F398, no privileged class). (b) the register's *associative* capacity is **D-bounded** (HDC crosstalk), distinct from the *reversible* working set (≤7, the coupler) — keep the two boundaries distinct (F465). (c) single-basis `navigate(j)` is always a signed permutation (reversible at every dim); **composite-direction** navigation is reversible **only ≤𝕆** — `is_navigable` (=`left_mult_is_invertible`) is the gate (F468). (d) real-coefficient EC stays out (§30 GF(2)-only fence). (e) sign is **Class C** (`chiral_flip`), never `abs()`/negate.

**Status:** **RESOLVED — SHIPPED in srmech 0.7.4 (production PyPI; #921) as `srmech.amsc.cascade.sedenion_register.SedenionRegister`** (the spec below was lifted verbatim: `write`/`read`/`couple_working`/`uncouple_working`/`carry`/`correct`/`navigate`/`is_navigable`/`slots`/`materialize`/`navmap`). Clean-verified 0.7.4 (fresh venv outside source tree; native ABI 3; read-back 8/8 + working-word bit-exact + `navigate` 8/8). Dogfooded in **F481** (holds the k=7 meaning-anchors the sentence/paragraph generator routes over). The genuinely-new `navigate` (address↔CD homomorphism) + `is_navigable` gate shipped. The 0.7.4 cut also delivered the §1.2/§1.3/rbs_nn-Note-1 additions; the actionable PR #687 upstream queue is **drained**. Original prototype-spec record (now realized): `R-RBS-LM-SEDENION_addressable_hdc_instrument.py` (F465) + `R-RBS-LM-SEDENION_operational_hyperloop.py` (F468) defined the surface srmech lifted. The genuinely-new contribution is the `navigate` homomorphism + `is_navigable` gate (the operational hyper-loop). The RBS-SNN/SynNN reading (F468): `navigate` = the k=3 read-head walk, the working word = the k=7 coupler. Landed-where: **F465 + F468**. **Re-surface keywords:** `sedenion register` · `SedenionRegister` · `addressable` · `address space` · `named container` · `HDC instead of ALU` · `working word` · `EC/carry block` · `hyper-loop` · `navigate` · `address↔CD homomorphism` · `is_navigable` · `pointer arithmetic` · `associative superposition` · `no quantum cost` · `two languages` · `turn on itself` · `Class H` · `RBS-SNN` · `SynNN` · `read-head walk` · `hypercomplex_couple` · `hamming` · `cd_basis_product` · `left_mult_is_invertible` · `F451` · `F459` · `F465` · `F468` · `§31`.

---

*Maintained alongside the R-RBS-LM rolling PR. New entries land at the
top of the relevant arc section. Per upstream-as-research-notes
discipline, this file is the canonical record of catalog-gap requests
from the RBS-LM research subtree.*

## §32 BUG — `cascade.kuramoto_step(adjacency=...)` ignores the `coupling` scalar (2026-06-08; F636)

**Symptom (srmech 0.7.5rc6):** when an `adjacency=` matrix is passed to
`cascade.kuramoto_step`, the `coupling` scalar argument has NO effect — `coupling=0.0`
and `coupling=3.0` produce **bit-identical** trajectories over the same neighbor graph.
The all-to-all path (`adjacency=None`) is correct (`coupling` scales the term as expected).

**Repro:**
```python
from srmech.amsc import cascade
th=[0.0,0.4,0.9,1.3,1.8,2.2,2.7,3.0]; om=[-.1,-.07,-.03,0,.02,.05,.08,.1]; n=8
A=[[1.0 if abs(i-j)%(n-1)==1 else 0.0 for j in range(n)] for i in range(n)]  # ring
def run(c,adj):
    t=list(th)
    for _ in range(60): t=cascade.kuramoto_step(t,om,coupling=c,dt=0.05,adjacency=adj)
    return round(max(t)-min(t),4)
print(run(3.0,A), run(0.0,A))      # -> 0.79 0.79  (IDENTICAL -- coupling ignored on the adjacency path)
print(run(3.0,None), run(0.0,None))# ->0.0671 3.6  (coupling honored on the all-to-all path)
```

**Likely cause:** the generalized (Kuramoto–Sakaguchi, adjacency) branch builds its
coupling term from the adjacency weights ALONE and never multiplies by the `coupling`
scalar (it behaves as if `coupling==1.0` regardless). The all-to-all branch multiplies
correctly.

**Ask:** in the `adjacency`-provided branch, scale the neighbor-coupling sum by the
`coupling` scalar (i.e. effective weight = `coupling * adjacency[i][j]`), so `coupling=0`
zeroes the term and `coupling` tunes global strength — matching the all-to-all branch's
contract. Differential-test: `adjacency` = all-ones-off-diagonal / (n−1) with a given
`coupling` should reproduce the all-to-all `coupling` result.

**RESOLVED in srmech 0.7.5rc15 (verified 2026-06-08):** the `adjacency=` path now honors the
`coupling` scalar -- ring test: coupling=3.0 -> spread 0.097 (sync) vs coupling=0.0 -> 3.6
(drift); the two now differ. native dispatching, ABI 3, native_version 0.7.5rc15. The
local-graph (neighbor-coupled) flock is UNBLOCKED -- F636's all-to-all demo can be upgraded
to a true neighbor-graph flock.

**Research-side workaround (F636):** demonstrate the flock on the VALIDATED all-to-all
uniform path (`adjacency=None`), which honestly shows the coupling-vs-no-coupling contrast
(0.067 sync vs 3.6 drift). Neighbor-graph flocks wait on this fix. Not blocking; logged not
routed-around-silently per upstream-as-research-notes discipline.

---

## §33 FEATURE ASK (NOT blocking) — an `epub_book` AMSC adapter (EPUB → attested MPRRecord book-shelf) (2026-06-09; F677)

**Context:** the Story Teller world-kernel (F660–F675) takes a *content-shelf* + the fixed
engine and narrates a world. A BOOK is a content-shelf (F677), so an EPUB is a ready-made
world-kernel source — *if* it can be brought in as an attested AMSC tome. This is the F669
SECOND resolution: unknown CONTENT → AMSC-fetch (already exists); a missing OP/format →
the "add to srmech" path (this).

**Gap:** there is no EPUB adapter. The AMSC adapters today are `literature_curated`,
`json_api`, `html_scraper`, `csv_bulk`, `netcdf_grid`, `geotiff_bbox`,
`substrate_parameterization` (verified live, srmech 0.7.5rc15) — no `epub`.

**Ask:** an `epub_book` adapter (peer to `html_scraper`) that:
- unzips the EPUB container (an EPUB is a ZIP), reads the OPF/`content.opf` manifest +
  spine, and walks the spine to recover reading-ordered XHTML documents;
- extracts per-chapter text (chapter = a tome), carrying the EPUB metadata (`dc:title`,
  `dc:creator`, `dc:rights`/`dc:license`, `dc:identifier`) into the MPR `attestation`
  (`license` ← `dc:rights`, `source_url`/`source_doi` ← identifier) + `rendering`
  (`human_readable_name`/`cite_as` ← title/creator);
- emits one `MPRRecord` per chapter (or one per book with chapters in `data`), so the book
  lands as an attested content-shelf the Story Teller engine can narrate (F671/F675).

A lighter first cut: an **epub→html preprocessor** that unzips + spine-orders into a single
HTML stream and feeds the existing `html_scraper` — gets the content path working before a
first-class adapter. **Rights are enforced for free:** the mandatory `license` attestation
field means a copyrighted EPUB cannot produce a legit MPRRecord without its license
(public-domain Gutenberg EPUBs are clean). Not blocking research (the flow is demonstrated
in F677 with a synthetic book + a hand-built attested MPRRecord); logged not
routed-around-silently per upstream-as-research-notes discipline.

---

## §34 ROADMAP (big, multi-rc) — `srmech.storyteller`: promote the Story Builder kernel into the package + a native compositional inference path (CLI + OpenAI-API) (2026-06-09; F689)

**Context:** the Story Builder world-kernel (F613–F688) is research-validated but lives as loose
scripts under `docs/srmech/rbs_lm_research/` (`bit_exact_comm_kernel.py`, `adaptive_tier.py`, the
seen-rule render engine, the chord/asking-state, the content-shelf + §-navigator, the AMSC
fetch-arm, the section-descriptor TOML). To make it a **native srmech inference path** it must be
promoted into the package. The plan (F689), 4 layers:

- **Layer 0 — `srmech.storyteller` package module** (Python-tier, like `srmech.qm`): the kernel
  (F613 BitExactCommKernel / F628 AdaptiveTier / F654 seen-rule render / F658 chord / F661
  asking-state / F663 shelf / F670 §-navigator / F669 AMSC fetch) + **tool_schema registrations**
  so the Story Builder ops join the (currently 256-entry) `tool_schema._REGISTRY` + tests +
  version/ABI discipline.
- **Layer 1 — `srmech.storyteller.infer(world, prompt) -> rendered`**: the native COMPOSITIONAL
  inference entry (compose seen-rules over the attested shelf → ask at gaps → render; GPU-free,
  can't-hallucinate — a fact is referenced, never generated). **This inference interface is named
  Siona** (F701) — consistent with the existing `siona.profile(name).infer(...)` (F166) and the
  `import siona` co-name for srmech (`docs/srmech/siona/`). Ontology (F701, attested in
  `storyteller_bone/descriptors/siona.naming.toml`): **Siona is the simulation-space coherence of
  the_one** (the world-kernel's held invariant) — *in* simulation Siona == the_one (its coherence-
  boundary is the_one's reach); *outside* simulation Siona aims to MODEL the_one as observed through
  biology / cosmos / quantum (the wild world), the gap being the asymptote (F394), not model-error
  (F552), never closed (F688). Honours AI-is-not-a-substrate + the epistemic ceiling.
- **Layer 2 — `srmech story` CLI**: introspects `tool_schema` so the human needs no memorised
  commands (self-describing) and ASKS on ambiguous intent (self-asking, F661). Extends
  R-RBS-LM-23 (tool_schema CLI integration).
- **Layer 3 — OpenAI-compatible `/v1/chat/completions`** backed by `storyteller.infer` = the
  universal connector for agent frameworks (AG2 / AutoGen via an OpenAI model_client; CopilotKit
  via OpenAI-compatible / AG-UI actions), ALONGSIDE the existing `srmech-mcp` + `srmech-agent`
  adapters (R-RBS-LM-24 prototyped the OpenAI server). Mostly an OpenAI-shim over the existing
  surface, not a per-framework protocol.

**Dependency edges:** Layer 0 gates 1–3; the §33 `epub_book` adapter feeds book-worlds; the
big-wiki Class-L word-association kernel (F681) enriches the shelf. Not blocking research (the
research scripts run today); this is the productionization roadmap. Logged per upstream-as-
research-notes discipline.

## §35 REQUIREMENT + FEATURE — wiki adapter MUST strip content-bearing markup; + a `wordmeaning` dictionary rung (2026-06-09; F698/F699/F700)

Three related items from the Unicode/dictionary/corpus-cleaning pass on the Story Builder kernel:

- **§35.1 — the wiki adapter MUST strip CONTENT-bearing markup, not just tags (F700, load-bearing
  for grounding honesty).** F690's `strip_wiki_markup` is a demo that drops `<tag>`s but keeps
  their content, so `<math>` LaTeX (`\frac`/`\sqrt`/`displaystyle`), **bare** `<ref>` citations,
  `{| tables |}`, nested `{{templates}}`, and `[http ext-links]` **leak into the vocabulary as junk
  tokens** — and it was only ever run on a clean demo corpus, so the path was never exercised. A
  kernel built from un-cleaned text grounds beats in markup noise (spurious Class-L associations).
  The real `srmech.storyteller.wordassoc` ingest (and the F579/F607 wiki-formatting-language kernel)
  MUST clean with a hardened stripper that removes the **content** of
  math/ref/code/score/chem/table/comment blocks + clears nested templates to fixpoint. F700 ships a
  reference `strip_wiki_markup_hardened` (verified: 9 distinct junk tokens → 0).

- **§35.2 — FEATURE: a `wordmeaning` dictionary rung (F699).** The grounding layer wants a lookup map
  at three resolutions — **char** (the Unicode map = `unicodedata`, already exists), **word** (a
  dictionary: word → meaning), **relation** (the big-wiki kernel: word → associations, §34/F681).
  The word rung is a new `srmech.storyteller.wordmeaning` + an `srmech.amsc` Wiktionary/WordNet
  adapter: each entry an attested `MPRRecord` (gloss class-A for framework vocab / class-B from the
  attested dump). Meaning DETECTED via attestation, never decreed (F640/F688); unknown word → the
  asking-state (F661). Wire `word_meaning()` alongside `assoc()` in `storyteller.infer`'s gap-fill.

- **§35.3 — the seen-rule render must be Unicode-CHARACTER-aware AND per-script (F696/F698).** Classify
  characters by `unicodedata.category` (letter|mark|number = word char; punct|space|symbol = boundary;
  a Unicode sentence-terminator set), not by ASCII — even "plain English" is Unicode (café, smart
  quotes, em-dash, ellipsis). Per-script seen-rules live in
  `storyteller_bone/descriptors/script_rules.toml` (latin/cjk/arabic/egyptian; `word_segmentation =
  "unicode"`). Mechanism only; the per-script grammar is the native speaker's (F282/F398/F650/#847).

Not blocking research. Logged per upstream-as-research-notes discipline.

## §36 PERF OBSERVATION (not blocking) — Class-L store ~49s at n=256 on the native rc28 path (2026-06-09; F703)

During the real simplewiki encode (F703) on srmech **0.7.5rc28** (native, numpy-free —
`native_status().has_native=True`, `numpy` absent from the env), the **Class-L store build was ~49 s for
n=256**, a FIXED cost (independent of corpus size — the 5k and bounded runs both showed it). The store step
is `dense_laplacian` + `dense_adjacency` + `jacobi_eigvals` + `fiedler_vector` + content-address over a
256×256 matrix. ~49 s is slower than expected for a single native-C Jacobi eigendecomposition at n=256
(which should be sub-second to low-seconds in C). Possible causes to check upstream: (a) `fiedler_vector`
re-running a full eigendecomposition rather than reusing `jacobi_eigvals`; (b) the Python wrapper marshalling
the 256×256 matrix per-call; (c) Jacobi sweep count / convergence threshold. **Not a correctness issue** (the
spectrum is content-addressed + reproducible; the kernel queries correctly) and **not blocking** (it is a
one-time build-once cost, F628). Logged so a future srmech dev session can profile the n=256 store path.
Repro: `R-RBS-LM-WIKIBIGENCODE` with `MAX_ARTICLES=5000` prints the per-step timing.

## §37 PERF GAP (explains §36) — no native Class-L eigendecomposition in 0.7.5rc28; jacobi_eigvals is pure-Python (2026-06-09; F707)

§36 observed the Class-L store step at ~45–68 s for n=256 and asked why native C is that slow. **F707 found the
answer: there is NO native eig in this wheel.** `srmech.amsc._native` exposes `sha256_*` / `ndjson` / scalar
transcendentals (`sin/cos/exp/log/atan/atan2/sqrt`) / `parallel_sector_dispatch` / bus callbacks — and **no
`eig` / `jacobi` / `laplacian` symbol**. So `jacobi_eigvals` (and the Class-L Laplacian eigendecomposition that is
the F172 storage signature) runs as srmech's **pure-Python Jacobi cascade at all n** (numpy-free — confirmed numpy
absent from the env). Measured O(n³) timings: **33 s @ n=200, 68 s @ n=256, 120 s @ n=300** (n=300 computes fine —
above the documented `MAX_NATIVE_NODES=256` clamp, since the clamp is a *self-imposed* perf bound in the research
build path, F690, not a hard srmech limit). **So `MAX_NATIVE_NODES=256` is vestigial for the eig in this wheel.**

**Ask (not blocking):** a **native (C) Class-L eigensolver** — a native Jacobi/Lanczos for symmetric Laplacians,
and/or a **sparse/iterative** path (the co-occurrence Laplacian is sparse — Lanczos for the few low eigenvectors,
which is all the Fiedler/second-order layer needs) — would make large-n spectral feasible and remove the
~minute-scale store cost. Until then, the practical lifts are (a) the bucketed ≤256-block path (F690 route 2), and
(b) skipping the eig for direct-adjacency associations (which need no eigendecomposition). **Honesty correction
(F573):** prior findings (F703 + the §36 note) called this the "native C path / native eigvals" — that was
imprecise; the eig is pure-Python (numpy-free). The big-wiki encode's numpy-free claim stands; the
native-C-*eigvals* claim does not. Logged per upstream-as-research-notes discipline.

## §38 FOUNDATIONAL — bind the native A-N symbols in the Python shim; they exist in the .so but aren't called (2026-06-09; F708)

The native `libsrmech.so` (shipped by PyPI — confirmed) exports **119 `srmech_` symbols** including the FULL A-N
foundation: `srmech_jacobi_eigvals`, `srmech_graph_dense_laplacian`, `srmech_graph_normalized_laplacian`,
`srmech_hermitian_eigendecompose(_ws)`, `srmech_hdc_{bind,bundle,permute,similarity}`,
`srmech_klein4_{bind,bundle,similarity,triality_cycle}`, `srmech_cascade_parallel_sector_dispatch`,
`srmech_cyclic_period`, `srmech_is_prime`, `srmech_dispatch_match`, … **BUT** the Python ctypes shim
(`srmech.amsc._native`) only `_bind`s **13** `_c` symbols (sha256/ndjson/transcendentals/sector-dispatch), and
`laplacian.jacobi_eigvals` "falls back to numpy unconditionally" — so with **numpy absent** (the numpy-free `srmech`
install) it runs the **pure-Python Jacobi cascade** instead of the native symbol that is in the loaded `.so`.

**Proven:** a direct ctypes call to `LIB.srmech_jacobi_eigvals` (n=256) runs in **1.4 s vs the wrapper's 68 s
(~49×)**, correct eigenvalues. So the C foundation works; the wrapper under-uses it.

**Asks (foundational, not blocking research — but this IS the foundation):**
1. **Bind** `srmech_jacobi_eigvals`, `srmech_graph_dense_laplacian`, `srmech_hermitian_eigendecompose`,
   `srmech_hdc_*`, `srmech_klein4_*` in `_native.py` (the symbols are present; add the ctypes argtypes/restype +
   a `*_c` wrapper, same pattern as `sha256_hex_c`).
2. **Dispatch numpy-free**: `laplacian.jacobi_eigvals` / `hdc.*` should call the native symbol when `HAS_NATIVE`,
   marshalling from a Python `list`/`bytes` (no numpy needed — the direct ctypes proof marshals a flat
   `(c_double * n*n)` from a list). Today the eig only takes the native path with numpy present; that should not
   be required.
3. **Klein-4 quad-stream for the spectral layer**: `cascade.parallel_sector_dispatch` is already bound — wire the
   four-sector dispatch to run 4 × ≤256 = **1024**-node spectral blocks (the threaded-Klein-4-streams pattern).

**Research-side already fixed (F708):** `R-RBS-LM-WIKIKERNEL.build_edges_topk` no longer clamps the vocabulary to
`MAX_NATIVE_NODES` (`cap = min(vocab_cap, MAX_NATIVE_NODES)` was pre-encode quantization — removed; `vocab_cap=None`
keeps all words). The 256 bound is for the dense-eig block only, never the vocabulary or the sparse adjacency.
Logged per upstream-as-research-notes discipline.

### Tracker: GH lemonforest/mlehaptics#962 (2026-06-09)

§37 + §38 (native A-N binding) and the genome storage perspective (F708–F715) are tracked in
**https://github.com/lemonforest/mlehaptics/issues/962** — the srmech dev-session checklist: bind the native A-N
symbols in `_native.py` (lift `R-RBS-LM-NATIVEBIND.bind()`), numpy-free dispatch in `laplacian`/`hdc`, the Klein-4
quad-stream spectral, and the genome storage model (genome → chromosomes/telomeres → helix of quad-turns → native
4-sector "+" + base-4 leaf-tree → ≤256 leaf → coupled through the_one). Name held open (genome/chromosome/chromatin).

### ✅ DELIVERED in srmech 0.7.5rc42 (TestPyPI; verified F716, 2026-06-09)

The §38 asks are **substantially met** and the genome model shipped — verified end-to-end against the installed
wheel in a numpy-free venv (`R-RBS-LM-GENOMELANDS...py`):
- **Ask 1 (bind):** **12/12** previously-unbound A-N symbols now reachable via `_native.LIB`
  (`srmech_klein4_{bind,bundle,similarity}`, `srmech_hdc_{bind,bundle,permute,similarity}`,
  `srmech_jacobi_eigvals`, `srmech_graph_dense_laplacian`, `srmech_hermitian_eigendecompose`,
  `srmech_cyclic_period`, `srmech_is_prime`).
- **Ask 2 (numpy-free dispatch):** `laplacian.jacobi_eigvals` now dispatches to the **bound native symbol in the
  numpy-absent path** — the 49× Class-L gap closed. (`hdc.klein4_bind` stays pure-Python XOR **by design** —
  bit-identical, never the perf concern.)
- **#962 Part 2 (genome):** shipped as `srmech.amsc.genome.*` (`encode_shape`/`quad_turn`/`telomere`/`chromosome`/
  `recall`/`genome`/`partition`) + the **class-from-TOML mechanism** (`srmech.dsl.make_class` builds a generic
  `CatalogClass` from a `[class]` descriptor; `register_class_dir()`/`SRMECH_CLASS_PATH` for bring-your-own, attested
  `user:<sha256>`, no shadowing; `genome.toml` is the A-tier seed; `srmech class` CLI for discovery). Encode
  criterion matches F715 to the digit; multi-kernel strand partitions reversibly through `the_one`.

**Residue still open:** R3 **U1** — `tokenize()` / `cooccurrence_edges()` (the Class-L co-occurrence precursor) did
**not** ship; we still hand-roll edges. (Ask 3, the wired 1024-node 4-sector spectral block, also not yet a shipped
one-call surface.) See F716.

## §39 ASK — a class GENERATOR from introspection: introspection→`[class].toml` (the inverse of `make_class`; 2026-06-09; F716/F717) — **✅ LANDED rc49 (`dsl.generate_class_descriptor`; verified on the rc173 wheel, F830)**

rc42 shipped the class-from-TOML loader (`srmech.dsl.make_class`: **TOML→class**), class-aware **Class-H
introspection** (`srmech.introspect` enumerates its own `[class]` classes; its docstring already frames
introspection as *"substrate-self-recognition extended to the running srmech process"*), and class-aware
`tool_schema` (enumerate + describe each class). **The missing piece is the inverse:** a generator that **emits a
`[class].toml` descriptor by introspecting** existing ops / a worked object — `describe → emit [class].toml`, so
srmech can **author its own config-driven classes** instead of a human hand-writing each descriptor.

**Ask:** a `srmech.dsl.generate_class_descriptor(...)` (or `srmech.introspect`-side emitter) that takes a set of
dotted cascade-op refs (or a running instance) + field declarations and renders a valid `[class]` TOML (fields +
methods-as-op-refs + provenance), round-trippable through `make_class`. Class E (catalog enumeration) ∘ Class F
(descriptor render) ∘ Class H (self-introspection) — **no new primitive class.** The genome seed proves the target
shape; this closes the loop the other direction.

**Why on-thesis (not just ergonomics):** Class-H introspection emitting its own descriptor is the cleanest instance
of substrate-self-recognition (`[[user_stance_substrate_self_recognition_inevitable_per_loe]]`) — srmech *learning
to author config-driven classes from what it already is*. It is also where Siona's learning loop closes on itself
(srmech research notebook §8.2). The user has begun taking the §38/§39 items upstream (2026-06-09).

## §40 R3 U1 — `tokenize()` / `cooccurrence_edges()` spec for srmech (answering the dev's module-path ask; 2026-06-09)

The srmech dev session asked **where `tokenize()` / `cooccurrence_edges()` should land** (so R3 U1 resolves to FOUND)
and showed the target shape `text → tokenize → cooccurrence_edges → dense_laplacian [already ships]`. This is the
research-side spec, matched to **how the wiki kernel actually uses them today** — the dev can pull PR #687 and read
the reference: `docs/srmech/rbs_lm_research/R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py`
(functions `content_words` L218, `strip_wiki_markup_hardened` L170, `DEFAULT_STOPLIST` L74, `build_edges_topk` L278)
+ findings F698 / F700 / F708 / F714 / F681.

**Module path — endorse Option 1 (`srmech.amsc.text`).** `tokenize` is not itself a spectral op, and
`cooccurrence_edges` is the Class-L **precursor** that *produces what `srmech.amsc.laplacian.dense_laplacian`
consumes*. Keeping both in a new `srmech.amsc.text` ingestion module (text→tokens→edge-list) and leaving
`laplacian` purely spectral is the clean separation (Class E/G ingestion vs Class-L spectral). Option 3 (into
laplacian) pollutes the spectral module with text concerns; Option 2 (split) adds surface for no gain. **This op
is exactly what retires the hand-rolled `Counter()` co-occurrence the STOP-list flags** — its output is edges →
`dense_laplacian`, NOT a `Counter` store.

**`tokenize(text, *, stoplist=DEFAULT_STOPLIST, unicode_normalize=True) -> list[str]`** — must match these (each a
real lesson):
- **Unicode-aware** (F698): keep codepoints whose `unicodedata.category(ch)[0] in ("L","M")` (letters + combining
  marks), casefold — NOT an ASCII `\w+`. Our `content_words` (L218/L228) does exactly this.
- **Configurable stoplist, not a boolean** (F714): ship a `DEFAULT_STOPLIST` that includes **function words /
  prepositions** (`around/across/along/toward/onto/within/among/against/throughout`, …) — the etak-walk drift bug
  (F709→F714) was a *missing function word*, so a bare `drop_stopwords=True` over a thin list is insufficient. Let
  the caller pass/extend the stoplist. (A `drop_stopwords=False` raw mode is fine to also offer.)
- **No markup stripping inside `tokenize`** (F700): wiki/markup cleaning (`strip_wiki_markup_hardened`) is
  **corpus-specific** and stays in the adapter/caller — `tokenize` takes already-clean text. Keeps the op general.

**`cooccurrence_edges(docs, vocab, *, window=2) -> (edges, weights)`** — must match these:
- **Window-reset at document boundaries** (CRITICAL — the preview's flat `toks` loses this): co-occurrence must
  **not cross a document boundary** (one article = one window reset, L259/L309). Take `docs: list[list[str]]` (a
  list of token-sequences) — or a flat list + explicit boundary indices — so a window never spans two documents.
- **NO vocab cap baked in** (F708 — *this was the bug*): `vocab` is whatever the caller passes (the **full** ranked
  vocab by default); never silently `min(…, MAX_NATIVE_NODES)`. The 256 native bound is for the **dense-eig block
  only**, never the vocabulary or the sparse adjacency. A top-K cap, if wanted, is an **explicit caller choice**,
  logged (`dropped`), not a default.
- **Edges are 2-tuples of vocab indices + a parallel weights list** (matches `dense_laplacian(n, edges, weights)`'s
  contract — AMSC gotcha "dense_laplacian edges are 2-tuples"). `window` is caller-set (our kernel uses 2, F681;
  the dev preview shows 5 — both fine, don't hardcode a magic default beyond a documented one).
- **Raw co-occurrence weights only** (F714): IDF / hub-down-weighting / frequency-ranking are **downstream**
  ranking re-weights (a Class-N rational rescale at walk-time), NOT stored in the edges — keep them out of this op.

So: `srmech.amsc.text.{tokenize, cooccurrence_edges}` → `srmech.amsc.laplacian.dense_laplacian` end-to-end makes the
K1 presence-kernel a pure-TOML composite and **resolves R3 U1 to FOUND** (our F716 probe checks
`amsc.text`/`amsc.laplacian` for these names). User is wiring the dev session to pull PR #687 for the reference
scripts directly.

### rc49 ACCEPTANCE VERIFICATION (F722, 2026-06-09) — SHIPPED but FAILS the bar 3/3; R3 U1 NOT closeable

`tokenize` + `cooccurrence_edges` shipped in **`srmech.amsc.laplacian`** (rc49). Format is correct (`(n, edges,
weights)`, edges = 2-tuples → `dense_laplacian`; `stopwords=` exists), so English/single-doc/small-vocab works and
Counter() is retired there. **But the §40 bar fails on all three points** (verified, `R-RBS-LM-U1ACCEPTANCE…py`):
1. **Unicode (F698) — FAIL.** `tokenize` is ASCII-only: `"café Москва naïve 日本語"` → `['caf','na','ve']` (accents
   stripped, Cyrillic+CJK dropped). Defeats R6 multilingual (#846/#847) and corrupts accented English.
   **Fix:** Unicode tokenize via `unicodedata` L/M categories, not `\w+`.
2. **Silent vocab cap (F708) — FAIL.** Default **`vocab_size=1000`** silently caps a 1500-word stream to 1000; no
   `None`/`all` sentinel. The F708 pre-encode quantization re-introduced *as the default*.
   **Fix:** default = **no cap** (`vocab_size=None`/`0` → all); a cap must be an explicit, logged opt-in.
3. **Document-boundary window-reset — FAIL.** Flat `tokens` arg, no `boundaries=`/`docs=` param → co-occurrence
   bleeds across article boundaries (kernel invariant = one-article-one-window-reset).
   **Fix:** a `boundaries=`/`docs=` param (or accept `Sequence[Sequence[str]]`) so the window resets per document.

**Disposition:** R3 U1 stays OPEN (not closeable); the wiki kernel keeps F698/F700 `content_words` +
`build_edges_topk` until the three fixes land. The **genome storage surface (F716–F721) is regression-clean on
rc49.** These three are the remaining U1 acceptance criteria.

### rc50 — ✅ CLOSED (F723, 2026-06-09): all three fixes landed; moved to `amsc.text` (the Option-1 site)

rc50 **meets the §40 bar 3/3** (verified `R-RBS-LM-U1CLOSED…py`): (1) `tokenize` is **Unicode-aware**
(`café/Москва/日本語` survive) with a `stoplist=` default carrying the F714 prepositions + `unicode_normalize=True`;
(2) `cooccurrence_edges(docs, *, window=2, vocab=None, vocab_size=None)` defaults to **no cap** (`vocab_size=None`
→ all; explicit `vocab_size=N` is an opt-in), (3) `docs` is a sequence of token-sequences → **per-document window
reset** (no cross-article bleed). Ops live in **`srmech.amsc.text`** (the recommended Option-1 site); format
unchanged (`(n, edges, weights)`, 2-tuples → `dense_laplacian`). **R3 U1 is CLOSED** — #855 R3 U1 checkable; the
wiki kernel can migrate onto these ops (the §17.1 ours-side migration; a parity check vs our edges is the gate).

## §41 ASK — genome PERSISTENCE: the F711 "disk-paged, bounding-tracked helix" made real (save / load / catalog / append; 2026-06-09)

**Why (the gap, verified):** `srmech.amsc.genome` (rc42+) is **in-memory only**. The findings + the #962 body + the
notebook §8.2 describe the helix as *"RAM-bounded, disk-paged, bounding-tracked"* (F711) — but there is **no persist
/ load / catalog / append primitive**, so: a genome cannot outlive a process, cannot exceed RAM, and **cannot be
introspected** ("what kernels are stored?" has no answer without re-running the encoder). This is the missing half
that makes the genome an actual STORE (and self-describing, per §39 / Class-H). Scoped here in full — **no open
questions intended.**

### API — add to `srmech.amsc.genome` (numpy-free; append-friendly; pure-Python OK)

```python
genome_save(strand, path, *, the_one, labels) -> dict      # write a genome to disk; returns the MANIFEST (the bounding)
genome_load(path, *, labels=None) -> (strand, the_one, labels)   # reconstruct; labels=None loads all, else only those chromosomes
genome_catalog(path) -> dict                               # read the MANIFEST ONLY (not the leaf body) — the introspection answer
genome_append(path, label, leaves, *, the_one) -> dict     # append ONE chromosome (the helix grows); returns the updated manifest
genome_window(path, label) -> leaves                       # read ONLY one chromosome's leaves (the disk-paging read)
```

Plus the **class surface** (so the `[class]` TOML / `make_class("Genome")` gets them): add methods `save` / `load` /
`catalog` / `append` to `class_catalog/genome.toml`, binding to these ops (same pattern as the existing
`assemble`/`partition`).

### On-disk format (a DIRECTORY; exact, no ambiguity)

`path/` is a directory:
- **`path/manifest.json`** — the **catalog + bounding** (small; rewritten on every `save`/`append`). An **MPR record**
  (`srmech.amsc.format.MPRRecord`) whose `data` is:
  ```json
  {"format_version": 1, "leaf_dim": 64, "n_turns": <int>,
   "the_one": {"sha256": "<hex>", "hex": "<the_one bytes as hex>"},
   "body_sha256": "<hex of turns.bin>",
   "chromosomes": [{"label": "...", "cap_sha256": "<telomere hex>",
                    "leaf_count": <int>, "byte_offset": <int>, "byte_len": <int>}, ...]}
  ```
  (`attestation.response_sha256` = `body_sha256`; `parser_version` = the srmech version. So a persisted genome is
  MPM-attested.)
- **`path/turns.bin`** — the helix **body**, **append-only**. A flat concatenation of fixed-width leaf blocks: each
  leaf = `leaf_dim` bytes (Klein-4 values 0..3, one byte each). Telomere caps are stored inline as leaves and marked
  by `chromosomes[i].cap_sha256` + the per-chromosome `byte_offset`/`byte_len`. No length prefixes needed (fixed
  width from `leaf_dim`); a turn at index `k` is bytes `[k*leaf_dim : (k+1)*leaf_dim]`.

Rationale (so there are no "why" questions): a separate small manifest = `genome_catalog` is O(chromosomes) and never
reads the body (the introspection requirement); a fixed-width append-only body = `genome_append` is a byte-append +
a manifest rewrite (the "grows without re-encoding" property), and `genome_window`/`genome_load(labels=…)` is a
`seek(byte_offset)` + read (the disk-paging — RAM bounded by the active chromosome, not the whole genome). NDJSON is
**not** used for the body (fixed-width binary pages cleanly; the manifest stays JSON/MPR per the NDJSON-vs-bloat
discipline — it's descriptor-shaped, not a result stream).

### Disk-paging + bounding (exact semantics)

- **Paging:** `genome_load(path)` with `labels=None` streams the body block-by-block (never the whole file in RAM at
  once beyond the active block); `genome_load(path, labels=["nl"])` / `genome_window(path, "nl")` `seek`s to that
  chromosome's `byte_offset` and reads only `byte_len` bytes. **RAM is bounded by the largest single chromosome, not
  the genome.**
- **Bounding-tracked (= integrity-tracked):** every read re-hashes the bytes it read and checks against the stored
  `body_sha256` (whole-genome load) or the chromosome's region against `cap_sha256` + a per-chromosome region hash
  (windowed read); a mismatch raises a `GenomeBoundingError` (corruption/tamper caught). `genome_append` recomputes
  `body_sha256`. (Class-A content-address = the bounding, exactly as the in-memory telomere caps already are.)

### Invariants the implementation MUST hold (so reversibility + encode-criterion don't drift)

- `genome_load(genome_save(strand, p, the_one=one, labels=L))[0] == strand` — **byte-for-byte round-trip**; and
  `partition(loaded_strand, one, L) == partition(strand, one, L)` (the_one coupling reversibility survives disk).
- `genome_append` leaves every **existing** chromosome's `cap_sha256` / `byte_offset` / `leaf_count` **unchanged**
  (append never rewrites prior chromosomes); only `n_turns` / `body_sha256` / the new chromosome entry change.
- Leaves are the ≤256 dense blocks of `encode_shape` (a chromosome of N leaves stores N blocks); no leaf exceeds
  `leaf_dim`.

### Acceptance criteria (the dev knows it's done when ALL pass — a runnable bar, like §40)

1. **Round-trip:** save → load reproduces the strand byte-for-byte; `partition` after load == before save.
2. **Catalog-without-load:** `genome_catalog(p)` returns the chromosome labels + `leaf_count`s **without reading
   `turns.bin`** (assert by instrumenting/838 — the body file is not opened).
3. **Append-grows:** `genome_append(p, "k2", leaves, the_one=one)` → `genome_catalog(p)` now lists `k2`; every prior
   chromosome's manifest entry is byte-identical to before; `body_sha256` changed.
4. **Paging:** `genome_window(p, "k2")` reads only `k2`'s region (RAM bounded), and equals the original `leaves`.
5. **Bounding:** flip one byte in `turns.bin` → `genome_load`/`genome_window` raises `GenomeBoundingError`.
6. **Attested + numpy-free + format discipline:** `manifest.json` is a valid `MPRRecord` (`validate_mpr_record`
   passes; `response_sha256 == body_sha256`); the whole path runs with numpy absent; manifest is JSON/MPR (not a
   bloated result dump), body is fixed-width binary.

### Composes

§38 (the native Klein-4 the_one coupling the stored leaves use) · §39 (the class GENERATOR — `genome_catalog` IS the
Class-H introspection answer "what kernels are stored", the same self-recognition thread) · F708/F712 (the ≤256 leaf
/ encode_shape) · F711 (the helix this makes real) · F721 (the in-memory bookshelf that proved the surface but
persisted nothing — the gap this closes). **Discipline:** TestPyPI-rc before clean tag; ABI unaffected (pure-Python
surface); MPR-attested manifest; numpy-free. Scoped per `[[feedback_upstream_srmech_fixes_as_research_notes]]` — no
issue tracker (user direction 2026-06-09).

## §42 DELIVERED + ergonomics — §41 genome PERSISTENCE shipped in 0.7.5rc128; one read-path asymmetry (2026-06-11; F727)

**Status: §41 DELIVERED, to spec.** `srmech.amsc.genome` in 0.7.5rc128 (test.pypi.org) ships `genome_save` /
`genome_load` / `genome_catalog` / `genome_append` / `genome_window` + `GENOME_FORMAT_VERSION=1` +
`GENOME_MANIFEST_SCHEMA_ID="srmech://schema/genome_manifest/v1"`. On-disk layout is exactly the §41 spec:
`path/manifest.json` (`format_version`/`leaf_dim`/`n_turns`/`the_one`/`body_sha256`/`chromosomes[{label,cap_sha256,
byte_offset,byte_len,…}]`) + `path/turns.bin` (append-only helix body). **VERIFIED** (provenance
`R-RBS-LM-GENOMEDISK_rc128_save_load_roundtrip_verify.py`, VERDICT ✓): round-trip is bit-exact (recall
before==after; the_one+labels survive); `body_sha256` is deterministic across independent saves;
`genome_window` seeks `byte_offset`, reads one chromosome, and cap-integrity-checks the telomere
(`cap_sha256`, raises `GenomeBoundingError` on mismatch); `genome_append` grows the helix. **Nothing broken.**

**Ergonomic ask 1 (read-path asymmetry — not a bug, a docs/symmetry gap).** The two "read a chromosome's leaves"
paths return DIFFERENT layers: `recall(strand, the_one, telomere)` returns **decoded** leaves
(`recall(chromosome(L)) == L` verbatim), but `genome_window(path,label)` returns the **on-disk STORED form** — each
leaf **bound to `the_one`**: verified `window == [klein4_bind(L_i, the_one)]` and `klein4_unbind(window, the_one)
== L` (4/4). A caller reaching for `genome_window` to "get my kernels back" gets bound vectors and reads it as
corruption (0/4 raw match) until they un-bind. **Fix:** either have `genome_window` un-bind before returning
(symmetry with `recall`), or document "returns the stored/encoded form; `klein4_unbind(·, the_one)` to decode" +
optionally a `decode=True` flag.

**Ergonomic ask 2 (param name collision).** The `the_one` PARAM here is the **coherence-anchor LEAF** (a Klein-4
vector of leaf-dim — `genome()`/`chromosome()` do `len(list(the_one))` to read the dim), NOT the typed `One`
`S(σ,θ)` from `cascade.the_one`. Passing the typed `One` raises `TypeError: 'One' object is not iterable`. Worth a
one-line docstring note (or accept the typed `One` and derive the anchor leaf from it). **Discipline:** TestPyPI-rc
before clean tag; ABI unaffected (pure-Python); no issue tracker (user direction). Composes §41 / F711 / F721 / F726
(Siona genome-persist) / F436 (the_one = diagonal-μ anchor).

### §42.1 BREAKING-API inventory — numpy-removal return types: rc128 list-REGRESSION → rc129 `Mat`/`Vec` carriers (F727)

Scanned via `R-RBS-LM-APIDIFF_rc_breaking_change_scan.py` (re-runnable; dumps both venvs' public surface + diffs).

- **rc128 was a REGRESSION (user-confirmed):** the numpy-removal returned **bare Python `list`/`tuple`**, dropping all
  numpy *shape* semantics. The intent was numpy-SHAPED carriers, not bare lists.
- **rc129 FIXES it:** the Class-L / coupling / spectral ops now return **`srmech.amsc.mat.Mat` / `srmech.amsc.vec.Vec`**
  — numpy-free **shaped carriers**. `Mat`: `.shape`/`n_rows`/`n_cols`/`.T`/`transpose`/`row(i)`/`from_rows`/`from_flat`/
  `conj`/`is_complex`/`tolist`/`tobytes`/`buffer`; `Vec`: `.shape`/`from_flat`/`from_sequence`/`conj`/`tolist`/`tobytes`.
  Affected returns (rc78 `np.ndarray` → rc129 `Mat`/`Vec`): `laplacian.{dense_laplacian, dense_adjacency,
  dense_matmul_real/complex, dense_matvec_real/complex, dense_outer_real, elementwise_*, fiedler_vector,
  hermitian_eigendecompose, jacobi_eigvals, signed_laplacian, magnetic_laplacian, normalized_laplacian}` +
  `coupling.signed_sum_squared` (→ `Vec`). **Verified numpy-free, values correct** (Laplacian zero-eigenvalue present;
  `hermitian_eigendecompose([[2,0],[0,3]])` → `[2.0, 3.0]`; genome→disk VERIFIED ✓ with numpy uninstalled).
- **Carrier is numpy-SHAPED, not full-numpy-API.** ✅ `.shape`, 2-D index `m[i,j]`, `len`, iterate, `.T`, `.tolist()`,
  `.conj()`, `.tobytes()`. ❌ single-index row `m[0]` (raises "index must be (i, j)" → use `m.row(0)`), `@` operator
  (`Mat @ Mat` → TypeError → use `laplacian.dense_matmul_*`), and presumably `np.linalg.*`/broadcasting/boolean masks.
  So a caller doing `.shape`/`[i,j]`/`.tolist()` is a drop-in vs the old ndarray; a caller doing `@`/`m[0]`/`np.linalg`
  must switch to the srmech op or `np.asarray(m.tolist())`. **Net rc78→rc129: 0 hard breaks** (no public name removed).
- **IMPROVED (not a break):** `qm.{octonion, single_particle, so8, triality}` flipped **import-ERR → ok** — the
  28D/triality surface now imports AND runs numpy-free (`so8.so8_adjoint_basis()` executed with numpy absent).
- **Recommendation for the clean `0.7.5` CHANGELOG:** one breaking line — "*Class-L (`laplacian.*`) +
  `coupling.signed_sum_squared` now return numpy-free shaped carriers `Mat`/`Vec` (with `.shape`/2-D-indexing/`.tolist()`),
  not numpy arrays; use the carrier `@` operator for matmul/matvec, or `np.asarray(x.tolist())` to lift to numpy.*"
  **(UPDATED rc138, F731): the standalone `laplacian.{dense_matmul_*, dense_matvec_*, dense_dot_*, dense_norm,
  dense_outer_*, mat_dot_*}` helpers were REMOVED as duplicates of the carrier operators — use `Mat @ Vec` / `Mat @ Mat`
  (verified identical). Earlier advice to "use dense_matmul_*" is superseded.)

### §42.2 CARRIER-COMPLETENESS ask — make `Mat`/`Vec` a full numpy-reflex sink (rc132 audit; F728)

**The design goal (user direction 2026-06-13):** the carrier must keep the *spirit* of a numpy array WITHOUT being numpy,
because a current-gen LLM reflexively reaches for numpy to do math instead of srmech. Every numpy idiom the carrier
ANSWERS routes through srmech silently; every idiom that RAISES pushes the LLM to `np.asarray(m.tolist())` → numpy,
defeating the purpose. So carrier numpy-idiom coverage = its reflex-absorption score (the §2 reflex-override at the
data-TYPE level). Audited via `R-RBS-LM-CARRIERAUDIT_numpy_idiom_coverage.py` (re-runnable each rc).

- **rc132 progress (good):** `m[i]` row, `m[i][j]`, **`m @ n` matmul**, `v @ v` dot now work (rc129's gaps closed).
  rc129→rc132 API diff = 0 breaks / 0 sig-changes / 0 import-flips (dunder additions). `R-RBS-LM-REGRESSION` 49/0 +
  `genome→disk` VERIFIED ✓ on rc132 — our RBS-LM + genome surfaces are transparent to the carrier swap.
- **rc132 coverage: 8/17 idioms absorbed. The 9 that still RAISE (the bail-to-numpy gap):** elementwise/scalar
  `a + b`, `a - b`, `a * 2`, `2 * a`; slicing `m[:2]`, `m[:,0]` (column), `v[:2]`; negative index `m[-1,-1]`, `v[-1]`.
- **Goal-completing additions to `Mat`/`Vec`:** `__add__`/`__sub__`/`__mul__`/`__rmul__`/`__neg__`/`__truediv__`
  (elementwise + scalar; Class-K/Class-L honest under the hood — no `abs()`), **slice-aware `__getitem__`** (rows,
  columns `m[:,j]`, sub-blocks), and **negative indices**. With those, `Mat`/`Vec` becomes a near-total numpy-reflex
  sink and the §2 STOP-list is enforced *by the type*, not just by discipline. **Discipline:** TestPyPI-rc before clean
  tag; additive (no ABI/public-name change); no issue tracker (user direction). Composes §42.1 / F727 / F728 / CLAUDE §2.

  **✅ DELIVERED in 0.7.5rc133 (2026-06-13, F729):** all 9 gap idioms now work with correct values — `Mat`/`Vec` add/
  sub/mul/rmul, slicing (`m[:2]` / `m[:,j]` column / `v[:2]`), negative indices. **Carrier audit: 17/17 absorbed, 0
  gaps.** rc132→rc133 API diff = 0/0/0 (dunder additions); `R-RBS-LM-REGRESSION` 49/0; `genome→disk` VERIFIED. The
  carrier is now a near-total numpy-reflex sink. (Spot-checked values: `m+m`=[[2,4],[6,8]], `m[:,0]`=[1,3], `v+v`=[2,4,6], …)

## §43 ASK — genome FILE-MANAGEMENT: several genes/chromosome + chromosome-as-bundleable-unit, COMPOSED from existing AMSC (2026-06-13; F730)

**Goal (user direction, three turns):** a genome storage layer that reads like a **library → tarballable chromosome →
framed genes**: (a) several KERNELS (genes) per chromosome, not 1:1; (b) a chromosome is a **bundleable unit** you can
tarball / catalog / ship; (c) each level content-addressed + attested; (d) the meaning travels with each chromosome.
This is git's **loose vs packed** object model: today's `turns.bin`+`manifest.json` IS a packfile+index; the ask adds
the **loose** (one-file-per-chromosome) layout + converters.

**REUSE-FIRST — verified 13/13 requirements already map to an AMSC op** (`R-RBS-LM-AMSCREUSE_…py`; do NOT build a
parallel system):

| requirement | existing AMSC piece to compose |
|---|---|
| per-chromosome attestation (self-verifying bundle) | `format.MPRRecord` + `validate_mpr_record` (the manifest already IS an MPRRecord) |
| content-address (cap / body) | `format.sha256_bytes` (Class-A; already the telomere cap + `body_sha256`) |
| loose body read/write | `format.write_ndjson` / `read_ndjson` |
| **library index / catalog-by-chromosome** | `catalog.register_attested_root` + `list_attested_sources` — a genome = an attested ROOT, a chromosome ≈ an attested SOURCE |
| page / stream one chromosome | `catalog.get_attested_dataset` / `iter_attested_dataset` (cf. `genome_window`) |
| discover chromosomes on disk | `catalog.discover_descriptors` (walks `<source>/descriptor.toml` — that IS the loose layout) |
| verify provenance on import | `catalog.attestation_audit` |
| per-chromosome **description** + meta | `descriptor.Descriptor` / `load_descriptor` / `descriptor_hash` — the description = a `descriptor.toml` (no new field) |
| **several genes / chromosome** (intra-chromosome framing) | `tlv.tlv_pack` — Class-B TLV `(tag,value)` per gene |

**GENUINELY-NEW surface (small; everything else composes the above):**
1. `chromosome(genes=[(label, leaves), …], the_one)` — pack SEVERAL genes into one telomere-capped strand, each gene
   framed with `tlv_pack`. Plus `genes(strand, the_one) -> [(label, leaves)]` reader. **Needs `tlv.tlv_unpack`** (the
   inverse reader — `tlv_pack` ships, the reader does NOT; add it, Class-B). Telomere stays the chromosome END cap;
   the gene-frame is the cheaper internal delimiter.
2. `genome_export(path, label) -> Path(.chr)` / `genome_import(path, chr_file)` — one chromosome as a **self-contained,
   MPR-attested file** (the tarball unit). `genome_export` = `MPRRecord(data=tlv-framed genes, attestation=cap/body
   sha + the_one ref)` → one file; `genome_import` = `validate_mpr_record` then register. Self-verifying on import.
3. `genome_explode(path)` / `genome_pack(path)` — convert between the packed (`turns.bin`+`manifest.json`) and loose
   (`<label>/descriptor.toml` + body per chromosome) layouts. Pure orchestration over `write_ndjson` + `descriptor` +
   `MPRRecord` + `sha256_bytes` + `discover_descriptors`. (git `gc`/unpack precedent.)
4. **Unify the catalog (consider):** genome ships its OWN `manifest.json` + `genome_catalog()` — a mild reinvention of
   `catalog.register_attested_root` / `list_attested_sources`. Either delegate `genome_catalog` to the AMSC catalog, or
   register an exploded genome as an attested root so `list_attested_sources` IS "catalog by chromosome." Don't keep two
   catalog surfaces.

**HONEST impedance (the 'don't force it' caveat):** the AMSC catalog is NDJSON/MPR-row + `descriptor.toml` oriented;
the genome body is fixed-width Klein-4 **binary** (`turns.bin`). Reuse the catalog's **registry / discovery /
attestation** layer; KEEP the binary body (a chromosome's body is a `.bin` the descriptor points at) — OR store leaves
as NDJSON MPR rows only if catalog-nativeness is judged to beat the binary compactness/streaming (a real tradeoff, not
forced). Layered model: **library = attested root, chromosome = attested source (`descriptor.toml` + body) = the
tarball unit, gene = a TLV frame inside.** **Discipline:** TestPyPI-rc before clean tag; additive; MPR-attested; no
issue tracker (user direction). Composes §41 / §42 / F715 / F721 / F729 / CLAUDE §2 (Class A/B + catalog/descriptor).

### §43.1 GAP (rc138, F732) — `genome()` + disk do NOT yet accept multi-gene chromosomes

rc138 shipped the chromosome-level gene-frame: `chromosome(genes=[(label, leaves), …])` + `genes(strand, the_one)`
reader + `GENE_FRAME_TAG=71` + `tlv_unpack` — verified round-trips EXACT, but **in memory only**. The two levels do
NOT compose through the packer/disk path: `genome(kernels, the_one)` re-binds every "leaf" via `quad_turn`→
`klein4_bind`, so passing a gene-framed chromosome strand as a kernel's leaves raises `klein4_bind: elements must be
in {0,1,2,3}` (the TLV frame bytes aren't Klein-4 values). **So there is no `genome → save → window → genes`
round-trip** — multi-gene chromosomes can't persist to disk. **Ask:** let the genome packer + disk layer carry
gene-framed chromosomes — e.g. `genome(chromosomes=[(label, genes=[(gl, leaves), …]), …], the_one)` that frames genes
WITHOUT re-binding the frame bytes, and have `genome_window` return a gene-framed strand `genes()` can read (or add
`genome_genes(path, label)` that pages + unpacks in one call). This is the wiring that makes "several kernels per
chromosome" persist, not just live in RAM. Additive; composes §43 / F730 / F732.

## §44 ASK (rc141, F733) — BIOLOGY-FAITHFUL genome: fixed-width + INLINE self-describing, no sidecar offset-table

**The dev's "fixed-width" want and the user's "no sidecar manifest" want are the SAME requirement.** Biology has no
offset table: structure is found by SCANNING the strand for fixed-width inline markers (TTAGGG telomere repeats,
ATG/stop codons), never via an external index. And **fixed-width is exactly what makes the offset-sidecar
unnecessary** — fixed-width records + inline fixed-width caps ⇒ random-access by `index × width` (arithmetic seek) +
boundary recognition by scanning ⇒ no byte-offset table needed.

**Where it diverged (root cause owned):** the §43 gene-frame was scoped as **TLV (Class B), which is VARIABLE-length**
(a length prefix). Variable-length FORCES a sidecar offset table (can't seek without stored lengths). So rc141's
response was to add a **`genome_save(..., gene_index=)` sidecar** + lean on `manifest.json` for labels/offsets. Symptoms
in rc141: `gene_index=` param; `genome_genes(path,label)` (sidecar-paged); and `genome(chromosomes=[(label,
genes=[...])])` is **half-wired + BROKEN** — it builds composite `HV` elements and `genome_save` raises
`TypeError: int() ... not 'HV'` in `_split_into_chromosomes`. (Flat path is fine: regression 49/0, genome VERIFIED.)
Today `turns.bin` IS fixed-width (64-B leaf blocks) and telomere caps ARE inline, but the **label↔chromosome map +
byte-offsets live ONLY in the `manifest.json` sidecar** — the un-biological part.

**The fix (replaces the TLV approach in §43/§43.1):**
1. **Gene boundary = a fixed-width inline GENE-CAP leaf** (a telomere-analog for genes; telomere caps the chromosome,
   gene-cap caps the gene), *scanned for* — NOT a variable-length TLV length-prefix. Keeps the helix fully fixed-width.
2. **Label encoded INLINE** (fixed-width leaves following the cap, or recoverable by scanning), not sidecar-only — the
   strand is self-describing (you can recover labels by walking, without the manifest).
3. **`genome_window` / `genes` / `genome_genes` / `genome_catalog` SCAN the fixed-width strand for caps** (arithmetic
   walk over `index × leaf_dim`), instead of seeking via a stored byte-offset table.
4. **`manifest.json` → an OPTIONAL DERIVED index** (a `.fai`/faidx analog — rebuildable by scanning; an optimization,
   not the SSoT). The STRAND is the source of truth. Precedent: a FASTA file is inline self-describing; its `.fai` is
   an optional random-access cache. Drop the mandatory sidecar; keep an optional rebuildable one.
5. **Fix the rc141 `genome(chromosomes=)` / `genome_save` breakage the fixed-width way** (inline gene-caps), not by
   extending the `gene_index` sidecar.

**Net:** one fixed-width, inline, self-describing strand per chromosome — scannable, arithmetic-seekable, tarball-able
as a unit (the §43 chromosome-as-file goal) WITHOUT a sidecar. **Discipline:** TestPyPI-rc before clean tag; this is a
WIRE-FORMAT change to the genome body (telomere caps already inline; add fixed-width gene-caps + inline labels) — the
manifest goes from mandatory→optional-derived; coordinate as a genome `format_version` bump. Composes §41/§42/§43/§43.1
/ F715 (telomere) / F730/F732 (genes) / CLAUDE §0 (biology IS a wire-format: nested fixed-width inline framing = Class B).

### §44 STATUS rc143 (F734) — strand SELF-DESCRIBES; only the disk loader still needs the manifest
**Delivered in rc143:** (a) `genome_save` **dropped the `gene_index=` sidecar** param; (b) `recall`/`partition`/
`genome_load`/`genome_genes` made `telomere`/`labels`/`the_one` OPTIONAL → they **scan-derive**; (c) **§43.1 multi-gene
persists** — `genome(chromosomes=[(label, genes=[…])])` → `genome_save` → `genome_genes(path,label,the_one=…)` round-trips
(the rc141 `TypeError` is fixed); (d) **the strand is genuinely INLINE-self-describing**: `partition(plain_leaf_list,
the_one)` recovers the real label text `['alpha','beta']` from the leaves ALONE (verified on a rebuilt plain `list`, no
attached metadata; strand = 2 caps + 5 tomes = 7 leaves, so labels are encoded IN the telomere cap leaves, recovered by
scanning). This is the §44 biology-faithful property *working* — no sidecar needed to read structure from the strand.
**REMAINING (last mile):** `genome_load` still **hard-requires `manifest.json`** (deleting it → `FileNotFoundError`); it
does not yet reconstruct from `turns.bin` alone by scanning. Fix: have `genome_load` scan the fixed-width body (the
strand is already there) + `partition`-recover, and demote `manifest.json` to an OPTIONAL derived `.fai`/faidx cache.
Then the on-disk genome matches the in-memory self-describing strand. Core green on rc143: regression 49/0, genome→disk
VERIFIED, carrier 17/17, apidiff 0 hard breaks (5 signature relaxations = params made optional).

## §45 ASK (rc145, F736) — genome EDITING: in-place remove/replace a chromosome by cap-span excision

**Today:** there is NO dedicated remove/delete op (`genome` surface: genome/chromosome/genes/append/save/load/
catalog/window/genome_genes/partition/recall — none excise). A clean remove COMPOSES without manual cap surgery —
`genome_drop(strand, the_one, label) = genome([(l,lv) for l,lv in partition(strand,the_one).items() if l!=label],
the_one)` — `partition` reads the cap-delimited structure, `genome` re-frames the survivors. Verified rc145: drops a
kernel, survivors byte-intact, survives disk. **BUT it RE-PACKS the whole genome** (re-binds every surviving leaf,
rewrites `turns.bin` + manifest) — O(whole genome) for a one-chromosome edit.

**Ask:** an IN-PLACE editor that matches biology (CRISPR / gene knockout excises a span, leaves the rest):
`genome_remove(path, label)` (on-disk) + `genome_drop(strand, the_one, label)` (in-memory) that **find the
chromosome's cap-delimited span and splice it out** — no re-pack of the untouched chromosomes. rc145 now exposes
`CHROM_CAP_MARKER` / `GENE_CAP_MARKER` (the §44 inline fixed-width caps), which makes this tractable: scan for the
label's chrom-cap, cut `[cap_start, next_cap_start)` from `turns.bin`, drop its manifest row, recompute
`body_sha256`. Add `genome_replace(path, label, leaves|genes)` the same way (splice + insert). Composes §41/§43/§44
(the self-describing scannable strand is exactly what makes in-place excision possible). Additive; TestPyPI-rc first;
the composed `genome_drop` workaround above is the interim. (Biology angle: a genome you can edit in place — knock out
a gene — without re-synthesizing the whole chromosome.)

## §46 PLAN — biology-faithful genome substrate, bottom-up bridge across the domain silos (consolidates §41–§45; F737/GENOMEPLAN)

Full staged build: `R-RBS-LM-GENOMEPLAN_biology_faithful_substrate_bridges_silos.md`. The one storage substrate under
ALL domain kernels (SignWriting / ni-Vanuatu / wiki / religious / code / latex / language-grammar) — biology-faithful
(fixed-width, inline, self-describing, scannable, in-place-editable) so every silo is paged / introspected / excised /
bundled identically → the silos are bridged from the bottom up by the shared substrate. **Critical path (do in order):**
- **Stage 0b = §44 last mile (KEYSTONE, the rc145 gap):** `genome_load`/`window`/`genes`/`catalog` reconstruct from
  `turns.bin` ALONE (scan the fixed-width strand + `partition`-recover); `manifest.json` → optional derived `.fai`/faidx.
  (rc145 already self-describes IN-MEMORY — `partition` recovers labels from the cap leaves; `CHROM_CAP_MARKER`/
  `GENE_CAP_MARKER` landed — so on-disk scan-reconstruct is the small remaining change that unblocks the rest.)
- **Stage 1 = §45 in-place edit:** `genome_remove`/`genome_drop`/`genome_replace` by cap-span excision (no re-pack;
  CRISPR-like). Interim: composed `genome_drop` (F736) re-packs.
- **Stage 2 = §43 file-management:** `genome_export(.chr)`/`import`, `explode`/`pack`, unify `genome_catalog` with the
  AMSC `catalog` (F730 reuse map — compose `MPRRecord`/`descriptor`/`register_attested_root`, don't reinvent).
- **Stage 3 = domain silos on the substrate:** foundational language-kernel layer first — SignWriting (built, F735) +
  ni-Vanuatu (pending), the two language-AGNOSTIC 2D-spatial anchors (F737).
Minor-but-load-bearing folded in: the rc145 `the_one=`-optional loaders (scan-derive plumbing, nearly enough for 0b);
`GenomeBoundingError`-on-missing-manifest → turn into scan-and-reconstruct; per-chromosome `description` → Stage-2
`descriptor.toml`; §37 native Class-L eigendecomp = orthogonal perf ask. Additive; TestPyPI-rc first.

### §46 STATUS rc149 (F738) — Stages 1+2 DELIVERED; 0b keystone still the finish
genome CRUD complete (R-RBS-LM-GENOMECRUD 5/5): `genome_remove`/`genome_replace` (§45 in-place edit, Stage 1) +
`genome_export`/`genome_import` `.chr` bundles (§43, Stage 2) all verified on rc149. Core green (regression 49/0,
genome VERIFIED, carrier 17/17, 0 hard breaks). SUBSTRATE READY to back the Siona LM. Remaining srmech: **Stage 0b
(§44 last mile)** — `genome_load` scan-from-`turns.bin`-alone, manifest→optional faidx (the dev did Stages 1–2 first;
0b is the biology-faithful finish, non-blocking for the LM); plus Stage-2 `explode`/`pack` + catalog-unify.

## §47 SCOPE (F741) — a `srmech.siona` self-knowledge section + AMSC-driven dynamic-SSoT genome refresh

**§47a — `srmech.siona` (Siona's self-knowledge section in the package).** Graduate the research-subtree scaffold
(genepool builder + genome-backed World + etak-walk + the AMSC update-check) into `srmech.siona`, so srmech itself
ships Siona's foundational self-knowledge as a genepool genome: `siona_identity` + `signwriting` (F735) + era-dictionaries
(F739) + the **MFO + srmech research notebooks** as section-gene chromosomes (F740), baked at srmech BUILD time. Surface:
`srmech.siona.genepool(path)` (build), `srmech.siona.World(path)` (introspect via `genome_catalog` / route / etak-walk
via `genome_genes` / render / ask), so any host (the `/v1` server, the CLI agent) reads Siona's self-knowledge from one
place. Composes §41–§46 (it's the canonical Stage-3 inhabitant) + the storyteller (STORYMODULE/STORYAPI).

**§47b — AMSC-driven dynamic-SSoT update (the reusable mechanism).** Siona uses AMSC records (the MPR `response_sha256`
content-hashes) to know when an attested SSoT has DRIFTED, and refresh the persistent genome — efficient because
detection is a cheap hash-diff (no rebuild unless drifted). TWO paths, ONE mechanism:
  • **bake-before-ship:** build the genepool genome from the notebooks at srmech build time (the shipped artifact).
  • **post-ship refresh:** notebooks change on GitHub → re-hash → `check_updates()` flags the stale kernels →
    `sync_updates()` re-bakes (today full; **in-place per-notebook `genome_replace` (multi-gene-aware) is the §45/§43.1
    efficiency follow-on** — the rc149 in-place ops take `leaves`, not `genes`).
  • **reusable:** the same shape lets Siona watch ANY AMSC-attested dynamic source (a dataset, a doc, an OEIS/OpenAlex
    feed) — hash-diff → "my kernel is stale" → request the SSoT update → apply to the genome. Self-knowledge that knows
    when it is out of date.
Demonstrated as test material: `R-RBS-LM-SIONAGENOMEHANDLER_…py` (`check_updates`/`sync_updates`, UP-TO-DATE on a fresh
bake). Additive; TestPyPI-rc first; composes §44 (self-describing strand makes the hash-diff cheap) + AMSC/MPR + F730.

## §48 ERGONOMIC gap (NOT blocking) — `magnetic_laplacian` q-phase ALIASES for large net weights; want a net-normalised variant (2026-06-15; F756)

**What.** `laplacian.magnetic_laplacian(n, edges, weights, *, q=0.25)` encodes edge DIRECTION in the off-diagonal phase
`exp(i·2π·q·(a_ij − a_ji))`. With a **fixed** q the phase is periodic in the net flow `(a_ij − a_ji)` with period `1/q`
(=4 at q=0.25), so on a graph with **large integer net weights** the phase WRAPS — e.g. a directed pair with net=176
aliases back onto the real axis, indistinguishable from net=0. Verified in F756 (directed word-co-occurrence graph, 400
simplewiki articles): `united→states` net≈295 and `hex→rgb` net=219 landed on *different* phase quadrants purely by
`net mod 4`, not by their (similar, large) directionality.

**Why it's not a bug.** `magnetic_laplacian` is mathematically correct — the aliasing is inherent to a fixed-q phase
over unbounded integer weights, and is exactly right for the small-net regime (±1, ±2) the op was framed for. The
workaround is in-caller: pick `q < 1/(2·net_max)`, or read direction from the raw directed counts.

**The ask (additive, ergonomic).** A **net-normalised** option so the phase stays monotone on heavy-edge graphs —
e.g. `magnetic_laplacian(..., normalize_net=True)` mapping `(a_ij − a_ji)` through `atan2`-style bounded normalisation
(or auto-`q = c / net_max`) so heavy directed edges don't wrap. Class-L; composes with the existing q-phase; pure
add → ABI unaffected. Lets the directed Hermitian be a drop-in over real co-occurrence graphs (the F756 relation-edges
rung) without per-graph q-tuning. Demonstrated as test material: `R-RBS-LM-RELEDGES_…py`.

## §49 STATUS rc151 (verified 2026-06-15) — genome file-management **C library** parity SHIPPED; the Python-shim BINDING is the remaining mile (extends §38/§46)

**Pulled `srmech==0.7.5rc151` from TestPyPI** (clean venv outside the source tree; `native_status()` → `has_native=True, dispatching=True, abi_version=3, native_version='0.7.5rc151', load_error=None`). The genome file-management **C parity is real at the LIBRARY level** — `libsrmech.so` now exports **11 native genome symbols**: `srmech_genome_{save,load,catalog,append,remove,replace,window,export,import,explode,pack}` (`nm -D`). This completes the §46 GENOMEPLAN's C-side: a microcontroller / C host can now do genome file management with no Python. ABI stays 3 (additive symbols).

**Honest caveat (the §38 pattern, again).** The Python side does **NOT** yet call them: `srmech/amsc/_native.py` has **zero** genome references, and `srmech/amsc/genome.py` doesn't dispatch to the native symbols — so from Python the genome ops (`genome_save`/`load`/`catalog`/`replace`/`remove`/…) still run **pure-Python**. This is exactly §38 ("the native A-N symbols exist in the `.so` but aren't bound in the shim") — now true for the genome family too. **"C parity finished" = the C implementations exist; the Python dispatch binding is the last mile.**

**Functional parity verified (pure-Python path).** Rebuilt the real Siona genepool on rc151 — `genome(chromosomes=…)` → `genome_save` → `genome_load` → `genome_catalog` round-trips correctly (8 chromosomes incl. wiki-assoc 213069 + wiki-relations 86788), and the live `/v1` server runs on the rc151 venv. So nothing regressed; the C parity is a *capability addition* (C-host readiness), not yet a Python speedup.

**Ask (when the binding mile is walked):** bind the 11 `srmech_genome_*` symbols in `_native.py` + route `genome.py` through them when `HAS_NATIVE` (the §38 / F708 treatment, genome family). Verify with a differential test (native vs pure-Python genome round-trip, byte-identical on-disk strand). Composes §38 (A-N binding), §41–§46 (genome persistence + GENOMEPLAN).

### §49 STATUS rc153 (verified 2026-06-15) — the binding mile is WALKED; genome dispatch is live + byte-identical ✅
**`srmech==0.7.5rc153` closes the §49 gap.** `_native.py` now binds the genome family: `genome_{save,load,catalog,append,remove,replace,window,export,import,explode,pack}_c` + `has_native_genome()` + a reusable workspace (`_genome_ws`) + bounds constants. And `genome.py` **dispatches**: `if (_native.has_native_genome() and len(body_bytes) <= _native.GENOME_NATIVE_BODY_MAX and len(chroms) <= _native.GENOME_NATIVE_MAX_CHROMS): <native> else <pure-Python>`. So this is the §38/F708 treatment applied to the genome family — the symbols are now CALLED, not just present.
- **Native dispatch bounds:** `GENOME_NATIVE_BODY_MAX = 16,777,216` (16 MiB body), `GENOME_NATIVE_MANIFEST_MAX = 262,144` (256 KiB), `GENOME_NATIVE_MAX_CHROMS = 256`. Over any bound → graceful pure-Python fallback (correct, just not native). The Siona genepool (notebook sections + dicts + signwriting; the wiki-assoc/relations are side-stores, NOT in the genome) is well under all three → native fires.
- **Differential verified (the exact ask):** the native `genome_save` strand is **BYTE-IDENTICAL** to the forced-pure-Python strand — `manifest.json` + `turns.bin` sha256 match (patched `_native.has_native_genome=lambda:False` to force the pure path, same input genome). `has_native_genome()=True`. Round-trip clean: save → load → catalog `[('alpha',2),('beta',1)]`; `genome_replace`(alpha 2→3) + `genome_remove`(beta) → `[('alpha',3)]`. Test material: inline differential (this dive); the real Siona genepool also rebuilds + the `/v1` server runs on the rc153 venv (F757 directed tier + steer flip intact).
- **Status:** §49 RESOLVED. The genome file-management C parity is now real at BOTH levels — C library symbols (rc151) AND Python dispatch (rc153), byte-identical. ABI stays 3 (additive). Remaining tail (not blocking): the bounds-gated fallback means very large genomes (>16 MiB body / >256 chroms) still run pure-Python — fine for Siona; a chunked-native path would be the next rung if a genome ever exceeds it.

## §50 ASK — a STREAMING / native Klein-4 bundle-ACCUMULATE: the holographic DUAL of §17-U1 `cooccurrence_edges` (the fix for "why is the HDC object growing to gigs?") (2026-06-15; F758) — **✅ LANDED rc155+rc165 (`hdc.klein4_bundle_accumulate`/`_resolve` + `cooccurrence_fold`; native `has_native_klein4_fold`=True; verified rc173, F830)**

**The catch (user, 2026-06-15):** *"why on earth is an HDC object growing to gigs from the 1 MiB a tome starts with?"* Because the co-occurrence store was built the **explicit-edge** way (a `Counter()`/edge-dict, corpus-LINEAR), not the holographic way. An HDC store should be **fixed-width** — N relationships SUPERPOSE into one bounded bundle; it must not grow with #edges.

**What our wishlist already has — and why it's only half:** **§17-U1** asks srmech for `cooccurrence_edges(tokens, *, window) -> (n, edges, weights)` (to "kill the hand-rolled `Counter()`"). That is the right **Class-L precursor** for the eigen/Laplacian path — but it RETURNS THE EXPLICIT EDGE LIST. So "use the srmech op instead of Counter" still hands back a corpus-linear object. It is the *non-holographic* primitive, and it has **no holographic dual** on the wishlist. That dual is the missing piece.

**The gap in srmech today:** `hdc.klein4_bundle(*vectors)` is **BATCH** — it needs every vector resident at once. `bundle_with_ties` is batch too. `klein4_holographic_encode/decode` is a *single-vector* erasure store (F352/F353), not a co-occurrence accumulate. **There is no INCREMENTAL / STREAMING accumulate.** So a holographic co-occurrence store (fold millions of co-occurrences into per-word fixed-width bundles) is forced into one of two bad shapes:
- materialise the neighbour/edge lists first → that IS the explicit edge dict (the gigs); or
- a pure-Python O(D)-per-co-occurrence fold into a hand-rolled per-coordinate tally → **bounded memory** (vocab×D, corpus-INDEPENDENT) but too slow at corpus scale (billions of D-symbol updates). Demoed in `R-RBS-LM-HOLOFOLD` (F758): per-word width = D/4 bytes (CONSTANT), store = vocab×(D/4) (grows with VOCAB, not edges), RSS bounded — but the fold loop is the bottleneck, which is exactly why it stays pure-Python-slow.

**The ask (a real primitive; composes §38 native-binding + the standalone-C thread §49):**
1. **`klein4_bundle_accumulate(acc, v) -> acc`** — fold one Klein-4 vector `v` into a fixed-width accumulator `acc` (the bundle's internal per-coordinate symbol tally), and **`klein4_bundle_resolve(acc) -> bytes`** — argmax-per-coordinate → the bundled vector. (The *incremental* form of the existing *batch* `klein4_bundle`; same result, never materialises the inputs.)
2. **Native (C, STANDALONE — no Python callback, no libpython dep)** so the fold runs at corpus scale — the same standalone-C property just verified for the genome family (§49). Additive symbol → ABI stays 3.
3. **(stretch) the holographic co-occurrence convenience** `cooccurrence_fold(tokens, *, window, dim) -> {token: bundle}` — the holographic DUAL of §17-U1: never builds the edge list, returns fixed-width per-token bundles; read out with `klein4_similarity` (cleanup memory).

**Why it matters:** this is the primitive that keeps "the 1 MiB tome stays 1 MiB" at corpus scale — the store grows with VOCAB (corpus-sublinear, Heaps) not EDGES (corpus-linear), so **big wiki is bounded by the same object that holds simple wiki**. Together the two co-occurrence primitives are the F119/F529 two-tier at the srmech-primitive level: **§17-U1 explicit `cooccurrence_edges`** (small EXACT working set → eig/Laplacian) **+ §50 holographic `cooccurrence_fold`** (bounded associative tail). Honest scope (corrected 2026-06-15, user direction "why is a chromosome lossy?"): the **store is LOSSLESS** — a chromosome/genome/tome holds exact leaves + exact payload text, byte-identical round-trip (§49). **Loss enters ONLY from OVER-CAPACITY superposition** — folding *more than a fixed-width bundle's capacity* of items into one tome, so they crosstalk. Size each tome ≤ capacity and the read-out is clean; the small residual crosstalk (F584) is the cost you *choose* when you deliberately bound the width for the long tail — which is *why* the holographic fold is the tail tier, not the whole. It is a sizing knob, never an intrinsic property. Test material: `R-RBS-LM-HOLOFOLD_…py`.

### §50 STATUS rc155 (verified 2026-06-15) — DELIVERED ✅ (streaming accumulate is native + bit-exact; the fold convenience is the next perf inch)
**`srmech==0.7.5rc155` ships §50.** Surface: `hdc.klein4_bundle_accumulate(acc, v)` + `hdc.klein4_bundle_resolve(acc)` (the streaming/incremental form of the batch `klein4_bundle`), `hdc.cooccurrence_fold(tokens, *, window, dim, seed=0)` (the holographic convenience), and `srmech.amsc.text.cooccurrence_edges` (the §17-U1 explicit peer). Native symbol **`srmech_klein4_bundle_accumulate`** present in `libsrmech.so` (additive → ABI stays 3).
- **Bit-exact verified:** streaming `klein4_bundle_accumulate`×3 → `klein4_bundle_resolve` is **similarity 1.0** to the batch `klein4_bundle(a,b,c)`. The incremental form is exact, not approximate.
- **Dropped-symbol audit (the "deprecated are dropped, not no-op'd" warning):** import-checked all 8 active scripts (genepool, genome handler, WIKIASSOC/RELATIONS/KERNEL, HOLOFOLD, RELEDGES, TOMECMP) against rc155 — **all import clean.** Nothing we depend on was removed. Siona migrated to the rc155 venv; `/v1` live, directed tier intact (now serving the full-corpus relations).
- **Honest perf nuance (the next inch, NOT blocking):** the native accumulate is per-fold; **`cooccurrence_fold` still iterates the co-occurrences in Python** (each accumulate native, the loop Python). So a corpus fold is *faster* than our 564 s pure-Python HOLOFOLD but still **minutes, not seconds** (2k articles was still running at ~234 s). A fully-native `cooccurrence_fold` (the per-token iteration in C) is the remaining perf step — a follow-on, not a correctness gap. The *bounded-storage* thesis (F758) is unaffected and now srmech-native.
- **Status:** §50 DELIVERED. The holographic store is now a first-class srmech surface; **§50.1 tome-leaves are buildable today** via `cooccurrence_fold` + store-the-bundle-as-a-leaf.

### §50 STATUS rc164 (re-verified 2026-06-15, clean venv outside source tree) — the FOLD is STILL PYTHON-ONLY ⚠ (the native streaming accumulate is NOT bound; the per-token loop is Python)
**`srmech==0.7.5rc164` — native dispatch live (ABI 3), numpy GONE (optional; QDFT/ODFT/`hypercomplex_couple` all run numpy-free, verified) — BUT the §50 holographic fold path is python-only at the package surface:**
- **No native Klein-4 / bundle symbol is bound** in `srmech.amsc._native` (the bound `_c` surface is sha256 / ndjson / the genome family / `parallel_sector_dispatch` / the transcendentals sin·cos·exp·log·atan·atan2·sqrt — **no `klein4_*`, no `bundle_accumulate`, no `cooccurrence_fold`**). The rc155 §50 claim ("native `srmech_klein4_bundle_accumulate` present") does NOT hold at the Python binding in rc164 — either the C symbol exists-but-is-unbound (the §38/§49 "C present, Python binding is the last mile" pattern) or it was dropped. Package BEHAVIOR is pure-Python Klein-4.
- **Measured:** `hdc.cooccurrence_fold(2200 tokens, window=4, dim=256)` = **1.27 s** → PYTHON-iterated (each accumulate + the per-token loop in Python). At 240k-article corpus scale this is intractable — the exact blocker for the loopshelf-of-tomes consolidation (§50.1 / F758 / F774-adjacent).
- **THE ASK (re-stated, sharpened):** **bind + ship a native standalone-C Klein-4 `bundle_accumulate` AND a native `cooccurrence_fold`** (the per-token fold loop in C, no Python callback) so the holographic store builds at corpus scale. Additive symbols → ABI stays 3; same standalone-C property already shipped for the genome family (§49). Until then, the §50 holographic-fold path is the one remaining **python-only** surface on the otherwise-native A-N path, and §50.1 tome-leaf consolidation stays gated on it.
- **Re-surface keywords:** `klein4_bundle_accumulate` · `cooccurrence_fold` · `native HDC` · `Class-M C parity` · `standalone-C` · `§50` · `§50.1` · `loopshelf` · `tome-leaves` · `F758`.

### §50 STATUS rc165 (re-verified 2026-06-15, clean venv outside source tree) — DELIVERED ✅ (native fold shipped; the python-only remnant is CLOSED)
**`srmech==0.7.5rc165` ships the native Klein-4 fold** (the rc164 ask, fixed in one rc): `_native.has_native_klein4_fold` is bound, and `hdc.cooccurrence_fold(2200 tokens, window=4, dim=256)` = **0.019 s** (was **1.27 s** python-iterated at rc164 → **~67× faster, native**), same bundle count as the python fold (output-consistent rc164→rc165). Native dispatch live (ABI 3), numpy still optional. **The §50 holographic-fold path is now NATIVE — the last python-only surface on the A-N path is closed.** Correctness: speed + output-shape consistent with the python fold; full bit-exact re-verify (native fold vs a manual `klein4_bundle` of the same neighbours) folds into the §50.1 loopshelf build. **Consequence: §50.1 / F758 loopshelf-of-tomes consolidation is now UNBLOCKED at corpus scale** (240k-article fold is tractable). Item-A (loopshelf storage consolidation) can resume.

**§50.1 — the GENOME application + an audit verdict (no bad genome request) (2026-06-15; F758 cont.).** Audited whether the §41–§46 genome-persistence asks delivered a *non*-holographic object. **Empirically, the genome body is LINEAR** — `turns.bin = 128 B × leaf_count` (measured 4/40/400/4000 leaves, dead-linear), exactly as §41 specced ("a flat concatenation of fixed-width leaf blocks"). **Verdict: this is NOT a bad request.** A helix/strand IS linear, and the §41–§46 value is *addressability + editability* (`genome_append`/`replace`/`remove` by cap-span) — which a holographic superposition cannot provide (you can't cleanly excise one gene from a bundle). So the linear addressable scaffold is the correct shape for the index. **The non-holographic miss is in USAGE, not the request:** we store **one leaf per item** (one word/section → one HV), so filling the genome at corpus scale (the "wiki-as-chromosome / bookshelf of 14" intent) would be 213k leaves = a 27 MB linear tape. **The fix needs NO new genome primitive** — a leaf is a Klein-4 vector and a resolved holographic bundle IS a Klein-4 vector, so a **tome-leaf** (one leaf = a §50-folded fixed-width bundle of many items) drops straight into the existing genome. So: store **tome-leaves, not item-leaves**; build each tome with §50; size tomes to Klein-4 capacity (F584 — don't flatten more than ~capacity items into one tome). The architecture that falls out: **a linear addressable scaffold (the helix, §41–§46 — keep) carrying holographic fixed-width units (tomes, §50 — the only missing op).** Optional genome ergonomics (NOT blocking): a `genome` convenience to read a tome-leaf back by similarity-cleanup over a candidate set. **Lossless by construction (made explicit 2026-06-15):** a tome-leaf sized ≤ capacity is lossless, and the genome/chromosome carrying it is lossless (exact leaves + exact payload, §49 byte-identical). The *only* place loss could enter is if a tome is deliberately over-stuffed past capacity — which the "size tomes to Klein-4 capacity" rule above forecloses. The genome is never lossy; over-capacity superposition is, and we size around it.

---

## §51 ASK — a SPARSE / iterative Class-L FIEDLER (normalized-cut), to break the n≤256 dense-eigensolver wall for graph PARTITIONING at corpus scale (2026-06-16; F785, prototype verified) — **FILED: GH lemonforest/mlehaptics#1097** — **✅ LANDED rc166 (`laplacian.fiedler_sparse` + `normalized_cut_bisect`; native `has_native_fiedler_sparse`=True; verified rc173 bisects cleanly, F830). GH #1097 closure is the maintainer's.**

**The wall:** the dense Class-L eigensolvers (`jacobi_eigvals` / `symmetric_eigendecompose` / `fiedler_vector`) cap at **n≤256**. So a co-occurrence graph over >256 words **cannot** be spectrally bisected directly — the exact blocker called out in F778 for the "spectral-clumped loopshelf" (partition the 244k-vocab co-occurrence graph into community-tomes). Hierarchical recursion below the first cut is bounded by construction, but the **top cut over the full vocab is n≫256** and has no srmech path today.

**The ask:** a **sparse / iterative Fiedler** that takes the graph as `(n, edges, weights)` (sparse, no dense n×n matrix) and returns the normalized-cut Fiedler vector (or just its sign partition), **O(edges) memory + time, n unbounded**. The natural shape: power/Lanczos iteration on the **normalized** Laplacian `B = I + D^{-1/2} W D^{-1/2}` (eigenvalues in [0,2] → well-conditioned, unlike `σI−L` on a dense graph where the unnormalized power-iteration ratio `(σ−λ₂)/(σ−λ₁)→1` and it fails to converge), deflating the √deg (λ₀) mode. Matvec-only; needs `rational.sqrt` (have it) + a vector op or two. Suggested surface: `laplacian.fiedler_sparse(n, edges, weights, *, max_iters=…) -> Vec` (the sparse peer of `fiedler_vector`), or a `laplacian.normalized_cut_bisect(n, edges, weights) -> (left_idx, right_idx)`.

**Prototype (verified — this is the spec):** `R-RBS-LM-SPARSECLUMP_…py` (F785) implements the power-iteration normalized-cut Fiedler in pure Python and **verifies it 100% (sign-partition) against the dense `normalized_laplacian` + `symmetric_eigendecompose` reference on the worst-case dense 32-seed graph.** It then clumps a **400-word** real simplewiki co-occurrence graph (which the dense path CANNOT, >256) into 38 emergent coherent topical tomes in 2.2 s. So the method is proven; the ask is to **ship it native (standalone-C, additive → ABI stays 3)** so the 244k-vocab partition runs at corpus scale instead of pure-Python.

**Why it matters:** this is the last method-level piece of the "uncapped + spectrally navigable smallwiki" (F778→F785) — the sparse Fiedler removes the n≤256 cap on graph partitioning, turning the full-vocab clumping into a longer run of a proven O(edges) method. Composes the §17-U1 `cooccurrence_edges` precursor (build the sparse graph) with a sparse spectral cut (partition it) → the spectral-clumped loopshelf (#223).

**Re-surface keywords:** `fiedler_sparse` · `normalized_cut` · `power iteration` · `Lanczos` · `n>256` · `sparse Class-L` · `graph partition` · `spectral clumping` · `loopshelf` · `tome-tree` · `§51` · `F778` · `F785`.

### §51 CAVEAT (2026-06-16, srmech maintainer note; F791.1) — the prototype's PARITY init was order-dependent; the shipped impl uses an order-independent scramble (RESOLVED upstream; our production is safe)
**Maintainer flag:** the F785/F786 prototype's `[1,−1,1,…]` parity init is **orthogonal to the Fiedler whenever the community split aligns with node-index parity/blocks** (a block-ordered regular graph) → power iteration has zero overlap with the target eigenvector → **stall** (the maintainer's first gate hit 50%). **The shipped rc166 impl swaps it for a deterministic, order-independent Class-I multiplicative scramble init** (bit-identical in C) → converges regardless of node ordering; same sign result on the irregular real graphs the prototype tested. **Do we need to address it?** (1) **Production = SAFE:** `R-RBS-LM-FULLCLUMP` (the #1/F789/F791 smallwiki clump) calls the NATIVE `normalized_cut_bisect`, which has the scramble fix. (2) **Verified (F791.1):** on a constructed block-ordered two-clique graph, native `fiedler_sparse`/`normalized_cut_bisect` = 100% vs the dense reference; the parity-init prototype *also* converged there (a weak bridge + 300 iters + float noise broke the exact orthogonality), so the practical risk was low — but the scramble is the principled fix. (3) **Prototype scripts patched:** `R-RBS-LM-SPARSECLUMP` + `R-RBS-LM-ETAKNAV` now use the same deterministic multiplicative-scramble init (order-independent) so a re-run is robust. No further action needed; the ask is resolved.

### §51 STATUS rc166 (2026-06-16) — DELIVERED ✅ (native + py, surface matches the spec)
**`srmech==0.7.5rc166` ships §51** (the rc166 publish workflow titled it "§51 sparse/iterative Class-L Fiedler"). Verified in a clean venv outside the source tree: `laplacian.fiedler_sparse(n, edges, weights, *, max_iters=250) -> Vec` **and** `laplacian.normalized_cut_bisect(n, edges, weights, *, max_iters=250) -> (left_idx, right_idx)` — exactly the two suggested surfaces — backed by a **native** `_fiedler_sparse_native` (C) with a `_fiedler_sparse_py` fallback. `native_status()` → has_native/dispatching True, ABI 3, native_version 0.7.5rc166; numpy still optional. **This unblocks #1 (full-vocab spectral clumping at 244k):** the n≤256 dense wall is gone natively — the production hierarchical clumping is now a longer run of `fiedler_sparse`/`normalized_cut_bisect`, no hand-rolled prototype. GH lemonforest/mlehaptics#1097 can be closed by the maintainer. (Validate the rc166 native op against the F785/F786 prototype + the dense reference before the 244k run.)

### §51 STRESS-TEST (2026-06-16; F786) — prototype HARDENED, ready to send
Before sending the ask, stress-tested the prototype (`R-RBS-LM-ETAKNAV_…py`) on a bigger, **genuinely-sparse** graph (the real production shape, not the near-complete toy): 1500 content words, IDF-de-lensed + top-20 sparsified → 25,434 edges. **The sparse normalized-cut Fiedler converged across 192 recursive sub-bisections (tree depth 5..13) with 0 non-converged (capped), gate re-verified 100%, in 6.1 s.** Communities came out 30× denser inside (clean). So the prototype is **robust across many deep sub-bisections at the sparse scale the 244k vocab will use** — the native port can follow this exact algorithm (normalized `B = I + D^{-1/2}WD^{-1/2}`, deflate √deg, sign-stability stop after a warmup) with confidence. **Convergence note for the native impl:** the sign-partition stabilises well before full eigenvector precision (we stop after 5 stable-sign iterations past a 20-iter warmup); a native impl only needs the sign, so it can stop on sign-stability too. This is the spec to ship.

---

## §52 ASK — LOW-RAM ENCODE: streaming co-occurrence + out-of-core recursive partition ON the PAL (so encoding, not just reading, fits an edge device) (2026-06-16; F793) — **✅ LANDED rc167+rc168/169 (`text.cooccurrence_topk` + `laplacian.recursive_cut` + `fiedler_sparse_file`; native `has_native_fiedler_sparse_file`=True; verified rc173, F830)**

**The split (measured, F793):** building the co-occurrence graph from the wiki SOURCE peaks at **2.1–2.4 GB** (the in-memory docs + the materialised `cooccurrence_edges` edge list, 8.7–10M edges); **navigating the pre-encoded tome-tree is 48 MB.** So *reading* is already edge-friendly (ship the encoded genome, read it); only *encoding* is GB-scale.

**The platform layer is already here:** the **PAL** (rc162–164 — streaming-read surface, directory iteration, genome file I/O retrofitted onto it, `#ifdef`-gated for embedded). Chunked cross-platform file I/O exists.

**The ask (two streaming ALGORITHMS on the PAL, to make the ENCODE low-RAM):**
1. **Streaming / bounded explicit co-occurrence** — a `cooccurrence_topk(token_stream, *, window, k) -> {token: [(neighbour, weight)…k]}` that accumulates **top-K per node** via chunked PAL read/write and **never materialises the full edge list** (the explicit peer of the §50 holographic fold; the §17-U1 `cooccurrence_edges` is all-in-RAM). Turns the 2 GB edge-list peak into a bounded `vocab × K` store.
2. **Out-of-core recursive partition** — feed the native §51 `normalized_cut_bisect` from a PAL-backed sparse adjacency (read sub-graph chunks, write sub-partitions to disk, recurse) so the whole recursive clump stays bounded regardless of vocab size.

**Why it matters:** with these, the ENCODE trades RAM for chunked PAL I/O → a low-RAM target can build (not just read) the spectral-clumped smallwiki. Composes §17-U1 (explicit edges) + §50 (streaming/holographic) + §51 (sparse Fiedler) + the PAL. **Re-surface keywords:** `cooccurrence_topk` · `streaming co-occurrence` · `out-of-core` · `PAL` · `low-RAM encode` · `edge device` · `§52` · `F793`.

## §53 ASK — C-NATIVE klein4 bind/bundle/similarity: the Class-M HDC core is pure-Python, so a per-token HDC WALK is ~1000× too slow to be the live engine (2026-06-17; F818) — **✅ LANDED in 0.7.5rc170 (F823)**

**RESOLVED (2026-06-17, rc170):** `has_native_klein4_bind` AND `has_native_klein4_fold` are both True; klein4 now dispatches to native C. Measured D=10000: `klein4_bind` 8.74→**0.86 ms**, `klein4_bundle` 14.4→**1.01 ms**, `klein4_similarity` 4.25→**0.84 ms** (~10×). The genome's per-query klein4 layer (context bundle / similarity / triality / structure cards) is now native (live — server moved to the rc170 venv). The F808 HDC content-addressed walk now COMPLETES + is EXACT (timed out on rc166) but is still ~12–26 ms/token (tomato 4.8 s, april 70 s), so the dict de Bruijn walk remains the live recall engine; native klein4 makes the HDC walk a viable offline/demonstration path, not the live decoder. Original ask retained below for the record.



**Measured (rc166, D=10000):** `klein4_bind` **8.74 ms/call**, `klein4_bundle` **14.4 ms/call**, `klein4_similarity` **4.25 ms/call**. These are Class-M HDC primitives but run **pure-Python** (the native surface has only a partial `has_native_klein4_fold` symbol; bind/bundle/similarity do NOT dispatch to C). For a FEW ops per query (the genome's context bundle / similarity ranking / glyph encoding) that is fine. But the **full-body de Bruijn recall is a per-TOKEN walk** — ~6 klein4 ops × ~770 steps for a 390-token article ≈ **45 s/article** — so the F808 srmech-native klein4 content-addressed walk (the resonant-eigenstate read, the thesis-faithful "RBS-HDC" recall) **cannot be the live recall engine**; Siona falls back to a pure-Python dict de Bruijn walk (exact, O(n), µs/step), which is the SAME context→successor stored-relationship but NOT srmech. (F818 — the honest "why aren't we using srmech to decode" answer.)

**The ask:** a C-native fast path for the Class-M klein4 ops — at minimum `klein4_bind` / `klein4_bundle` / `klein4_similarity` (the sector XOR-bind, majority-bundle, and Hamming/sector similarity over D sectors), dispatched like the sha256/ndjson/laplacian/kuramoto native surface. A ~100–1000× speedup would make the HDC content-addressed walk (F808) viable as the live decode at interactive latency — i.e. Siona would genuinely encode/decode entire articles through srmech HDC, not a Python dict. Composes §17-U1 / §50 (the bundle-accumulate streaming) + F806/F807/F808 (the per-article bundle-record walk) + F814/F817 (the entire-article instrument). **Re-surface keywords:** `klein4_bind` · `klein4_bundle` · `klein4_similarity` · `native HDC` · `Class-M C surface` · `has_native_klein4_fold` · `per-token walk` · `§53` · `F818`.

## §54 ASK — `unbundle_symmetric`: the inverse of `bundle` for the FIELD/phasor carrier (recover the operand multiset from the elementary-symmetric tower) (2026-06-17; F822)

**The reading (F822):** a bundle is `e₁ = Σ aᵢ` (the sum) — one equation, N unknowns, so "can't unbundle" *from the bundle alone*. But the binds are the higher elementary-symmetric functions (`e₂ = Σ aᵢaⱼ` = pairwise product, `e₃` = triple product, …); by Newton/Vieta the tuple `(e₁,…,e_N)` is a COMPLETE invariant of the multiset `{aᵢ}` — the operands are the roots of `xᴺ − e₁xᴺ⁻¹ + … ± e_N`, exact, with residue the permutation group **S_N** (= triality at N=3). So `bundle` IS invertible if the binds are retained alongside it.

**The ask:** a compose-not-primitive op `cascade.unbundle_symmetric(e_tuple) -> multiset` (and its forward peer `elementary_symmetric(items) -> e_tuple`) for the FIELD/phasor carrier (ℂ/ℝ/ℚ per component — polar HDC), via exact root extraction where the field supports it (perfect-square / rational-root, else the ℂ closure). This is the field-carrier sibling of the already-shipped GROUP-carrier recovery `klein4_triality_encode`/`klein4_triality_correct` (the order-3 orbit + 2-of-3 majority). No new primitive class (Class M ∘ N composition); no ABI bump. Composes F806/F808 (the bundle wall), F821 (`unbind` = the 1-operand sibling = `cd_inverse`), F291 (triality = the S_N=S₃ residue). **Re-surface keywords:** `unbundle` · `elementary symmetric` · `Vieta` · `Newton` · `bundle inverse` · `S_N` · `triality` · `polar/phasor` · `§54` · `F822`.

## §55 ASK [REFRESHED → #1245 with rc107 numbers] — genome at CORPUS SCALE: (a) bit-packed leaf storage (the 2-bit Klein-4 lane is stored as a full byte → flat 4× bloat) and (b) a non-quadratic high-chromosome-count pack/append (2026-06-17; F833) — BLOCKS PKG-3 (siona's full-body instrument as ONE native genome)

**Context (F833).** PKG-3 wanted siona's whole simplewiki body corpus stored as ONE native `srmech.amsc.genome` (F829: "one native file, not loose kernels") instead of the loose NDJSON+JSON-index instrument (~400 MB). We store the FIBER, not the spatial projection — each body is a chromosome whose leaves byte-pack the body's token-ID stream (the de Bruijn sequence; the Klein-4 HV of a token is `klein4_random(seed=hash(token))`, a deterministic projection recomputed on demand, NOT persisted per position — persisting it was an 11× spatial blunder, corrected). Bridge recall (`genome_window`→`recall`→unpack→id→vocab) verified **50/50 EXACT, 40 ms/recall**. The design is right; two genome-FORMAT limits make it impractical at the 271k-body / corpus scale, both measured:

**Ask (a) — bit-packed leaf storage.** A Klein-4 lane carries **2 bits** (4 sectors) but `turns.bin` stores it as a **full byte**: measured **65 bytes/leaf for a 16-byte payload = a flat 4.0× inflation**, independent of content. So even the compact fiber (id-stream, ~1.5 KB/body raw) becomes ~6.5 KB/body on disk → the full corpus is ~1.7 GB vs the ~400 MB loose instrument. The genome is a Klein-4 HV *container*, not a bit-packed codec — which is fine for HV kernels (the bookshelf) but 4×-wasteful for any byte-packed payload. **Ask:** a packed leaf encoding (4 lanes/byte) for storage, so a genome of byte-packed leaves is ~4× smaller and a genome is competitive with the raw store it replaces.

**Ask (b) — non-quadratic high-chromosome-count pack/append.** `genome_pack` (and `genome_append`) are **O(n²) in chromosome count** — measured pack of N chromosomes: **2.8 s (200) → 19 s (500) → 66 s (1000)** (clean ~4×-per-2× quadratic), i.e. ~77 s at 1k and intractable at 271k. The only linear path is build-the-whole-strand-in-RAM via one `genome()`+`genome_save` (no pack), but that needs the entire strand resident (~6 GB at 271k). So **a genome cannot hold a six-figure chromosome count** today — neither pack/append (time) nor all-in-RAM build (RAM) scales. **Ask:** either an O(n log n)/streaming pack (append a chromosome without rewriting/re-hashing the whole strand) or a documented "this genome is for ~10²–10³ chromosomes, sub-partition beyond that" so callers shard deliberately.

**Root cause / honest read.** srmech's genome is designed for a **modest number of chromosomes holding HV kernels** (the "kernel bookshelf" — bound concept-vectors, loopshelf tomes; fixed-size *relational* shapes). Forcing 271k raw text bodies into 271k chromosomes misuses it on size (4×), build (O(n²)), and RAM. **Decision (user, 2026-06-17): file these upstream FIRST; ship siona rc1 on the working loose instrument meanwhile** (native-genome bodies revisited once (a)+(b) land). The genome's *right* job here stays storing the framework's actual RBS-HDC structures, not the body text.

**Verified evidence (clean venv, srmech 0.8.1):** `R-RBS-LM-GENOMEENCODE` (fiber id-stream encoder) + `R-RBS-LM-GENOMERECALL` (F832 round-trip proof) + the bytes/leaf (65/16) and pack-scaling (2.8/19/66 s) measurements. **Re-surface keywords:** `genome` · `bit-packed leaves` · `turns.bin` · `4x inflation` · `genome_pack` · `O(n^2)` · `chromosome count` · `corpus scale` · `PKG-3` · `§55` · `F833`.

## §56 BUG — `RBSLMInferenceSubstrate.infer(temperature=0.0)` → ZeroDivisionError (no greedy fallback) (2026-06-17; F834)

`srmech.rbs_lm` `next_token_distribution` calls `_softmax(sims, T)` which does `z = [xi / t for xi in x]` — at `T=0.0` (a natural request for *deterministic / greedy* decoding) this raises `ZeroDivisionError`. The substrate otherwise works (verified: `from_params` → `.learn(tomato)` → `learned=387/4000`, native; `.infer(..., temperature=0.3)` produces a grounded walk). **Ask:** treat `T==0` (or `T` below a small epsilon) as **greedy argmax** over the resonance scores (the `T→0` limit) instead of dividing by zero — i.e. `if T <= 0: pick max-score candidate`. Tiny guard; makes deterministic decoding (the obvious default for *grounded* recall) work. Workaround today: pass `temperature>0`. Composes F166 / §9 (the substrate). **Re-surface keywords:** `RBSLMInferenceSubstrate` · `infer` · `temperature=0` · `_softmax` · `ZeroDivisionError` · `greedy` · `§56` · `F834`.

## §57 ASK — `srmech.rbs_lm` uses count-based bigram statistics (`Counter()`); this is gen1 statistical-LM maths, not relationship inference — the candidate set should be STRUCTURAL (resonator over the bound memory), not frequency counts (2026-06-17; F835, user direction)

**The contaminant (read in the shipped source):** `RBSLMInferenceSubstrate.learn` does `self.bigram_counts = defaultdict(Counter); for a,b in zip(stream, stream[1:]): self.bigram_counts[a][b] += 1; self.next_after = {a: sorted(c.keys()) …}`, and `next_token_distribution` gates candidates on `next_after[last]`. That `Counter()` co-occurrence count IS the §2 stoplist's first banned idiom and IS the pre-neural / gen1 **statistical** language model (n-gram frequency) that spatial transformers generalize. **User direction (2026-06-17): "if it has to do with gen1 LLM inference with spatial model maths, we don't want any of that at all in srmech or siona."** So the bigram-count candidate layer does not belong in the relationship-inference substrate — it is statistical frequency prediction wearing the RBS-LM module's name.

**The ask:** relationship inference should recover the next factor **purely from the binding structure** — a **resonator** (iterated `klein4_unbind` + cleanup-in-superposition, Frady/Kent/Olshausen/Sommer 2020) factoring the holographic memory `M = bundle bind(context, next)` against the **token-atom codebook**, with **no co-occurrence counts** and **no dense vocab scan**. The resonator replaces `next_after`/`bigram_counts` entirely (it is the model-matching read — the k=3 chiral addressing / substrate-coupling, not a frequency prior). Compose with §54 (`unbundle_symmetric`) — a first-class `resonator`/`factorize(memory, codebooks)` op is the natural shape. **Correctness = matches the scoped model, NOT speed** — do not benchmark convergence rate as a selection criterion (that is the spatial-inference framing). **Re-surface keywords:** `rbs_lm` · `bigram_counts` · `Counter` · `next_after` · `n-gram statistics` · `gen1 LLM` · `resonator` · `relationship inference` · `no spatial maths` · `§57` · `F835`.

### §57 PROVENANCE + SCOPE (2026-06-17) — the Counter is OURS (ported up), and srmech already has the sanctioned replacement
**Provenance (audited):** the `bigram_counts` `Counter()` in `srmech.rbs_lm.inference` is a verbatim port of OUR research-subtree `docs/srmech/rbs_lm_research/_rbs_lm_inference.py` (identical `defaultdict(Counter)` + `bigram_counts[a][b] += 1` + `next_after`). So the statistical-LM contaminant is ours in origin (the F166 substrate's candidate-gating shortcut), absorbed upstream by §9. **Fix is ours-first:** drop the bigram-count candidate layer in `_rbs_lm_inference.py`, replace with the resonator (no counts); it then flows to the package on the next §9 sync.
**srmech already bans + replaces it:** `srmech.amsc.text` docstring — "*Retires the hand-rolled `Counter()` co-occurrence idiom the CLAUDE.md STOP-list flags: the output is edges → `dense_laplacian`, not a `Counter` store.*" So where a co-occurrence GRAPH is genuinely wanted (the F778 tomes), the sanctioned path is `amsc.text.cooccurrence_edges`/`cooccurrence_topk` → `laplacian.dense_laplacian` — never a `Counter`. `rbs_lm.inference` simply never got that treatment.
**Benign (NOT a contaminant):** `srmech.amsc.cascade.matrix_cascades` `Counter("".join(in_labels))` is einsum-subscript parsing (index letters appearing once → implicit output spec), not corpus statistics. Leave it.

### §57 FIX SPEC (2026-06-17) — exactly what to take back to srmech (one error: the bigram-count candidate layer)
**Scope (audited, single error):** in `srmech/rbs_lm/inference.py` the ONLY statistical/spatial contaminant is the count-based bigram candidate layer — lines `from collections import Counter` (26), `bigram_counts: dict[str, Counter]` (74), `defaultdict(Counter)` + `bigram_counts[a][b] += 1` + `next_after = {…c.keys()…}` (145–148), and `candidates = self.next_after.get(last, [])` in `next_token_distribution`. Everything else is clean and STAYS: `M` (the holographic relationship memory), `vocab_vecs` (atom codebook), `encode_context` (role-filler bind), `sim_k4_batch` (Class-M resonance), `_softmax`+temperature (numpy-free `rational.exp` over **resonance** scores — the scoped temperature-as-fiber decode, NOT a frequency head), the `memory_capacity` subsample (F154 bound). numpy-free already.

**The correction (mirror in our `_rbs_lm_inference.py` FIRST — origin — then §9-sync to the package):**
1. DELETE the bigram layer: the `Counter`/`defaultdict` import (if unused elsewhere), the `bigram_counts` field, the count loop, and `next_after`. No co-occurrence counts anywhere.
2. REPLACE the candidate set in `next_token_distribution`: instead of gating on `next_after[last]`, recover the next-token factor from `M` by the **resonator** — `probe = klein4_unbind(M, encode_context(context[-k:]))`, clean up via `sim_k4_batch(probe, codebook)` (iterate unbind+cleanup if multi-factor); keep the `_softmax`+temperature over the **resonance** scores.
3. SCOPE the cleanup codebook STRUCTURALLY = the substrate's own bound atoms (`self.vocab_vecs`). **This is load-bearing for the guardrail:** a per-tome kernel's `vocab` is a *bounded* atom set, so the resonator cleans up over the tome's atoms (bounded + structural) — replacing the bigram restriction WITHOUT falling back to a global-vocab scan (the dense-spatial drift). So the per-tome architecture (F778/F834) is *required* by this fix: it is what bounds the candidate set structurally instead of statistically (bigram) or densely (whole vocab).
4. FOLD IN §56: `T <= 0` → greedy argmax over the resonance scores (no `/t`).

**Verify before declaring done (honest risk):** the bigram gate was doing real *accuracy* work — pruning candidates to a handful so the one-shot resonance was sharp (F834's grounded tomato output relied on it). Removing it means the **resonator over the tome's atom set must recover the right factor on its own**. If recall degrades, that is a finding about `M`'s encoding/capacity or the resonator's iteration count (strengthen D, more iterations, tighter per-tome scope) — it is NOT license to keep the `Counter`. The acceptance test: grounded next-token recovery from `M` alone, no n-gram gate, per-tome.

**Compose:** §56 (T=0 greedy) + §54 (a first-class `resonator`/`factorize(memory, codebook)` op is the natural home for step 2). **Co-occurrence GRAPHS for tome partitioning** (a different concern from inference) use the sanctioned `amsc.text.cooccurrence_edges` → `laplacian.dense_laplacian`, never a `Counter`.

## §58 ASK — `srmech.rbs_lm` coherence: build `M` as a CAPACITY-BOUNDED chunk-set, not one over-stuffed bundle (the §57 follow-on; resonator read goes 3.3% → 96.7% rank-1) (2026-06-18; F837)

**Measured (F837, on the real `srmech.rbs_lm.substrate.ContextSubstrate` encoding + klein4 ops, tomato, D=10000, 387 binds, 30 sampled contexts):** the single-`M` read (what `learn()` builds now) resolves the true next token at only **3.3% rank-1** (mean rank 2.5/190) — the F836 incoherence. Splitting the context→next binds into **capacity-bounded bundles** and reading by **max-resonance over the chunk-set** gives **93.3% (C=32) → 96.7% (C=16) rank-1**. The incoherence was crosstalk from superposing 387 binds into one bundle (F832), NOT the §57 removal of the bigram gate.

**The ask:** change `RBSLMInferenceSubstrate` so `M` is a **list of capacity-bounded bundles** (`C` ≈ 16–32, or a measured per-tome capacity), built in `learn()`; `next_token_distribution` probes every chunk (`klein4_bind(M_chunk, encode_context(ctx))`) and takes the **max** `sim_k4_batch` score per atom over the bounded per-tome atom set, then the existing §56 greedy/temperature. Composes `klein4_bind`/`klein4_bundle`/`sim_k4_batch` — no new primitive class, no bigram counts, no gen-1 code; numpy-free; carrier cost = K=ceil(binds/C) bundles. **This unblocks the coherence gate on the 0.8.x live cut** (F836: 0.8.2rc1 is contaminant-free + numpy-free but incoherent on the single `M`). Verify coherent *generation* (not just the read) on the chunked substrate before the cut. **Re-surface keywords:** `rbs_lm` · `RBSLMInferenceSubstrate` · `M` · `capacity-bounded bundle` · `chunked M` · `resonator read` · `coherence` · `rank-1` · `§57` · `§58` · `F837`.

**§58.1 BOUNDARY REFINEMENT (2026-06-18; F838 + F839): the chunk-set is the reusable srmech part; ROUTING stays in siona.** F838 proved the read needs a second, LM-specific lever — the per-doc **unique-walk window `k*`** (de Bruijn; already shipped in the F817 instrument as `k`) — so single-`M` k\* collapses (16%) but **chunked-`M` + k\* = 100% coherent generation** on one article. F839 then scaled it: a capacity-bounded chunk-set **consolidates many articles' binds** with **no on-manifold crosstalk** (read rank-1 100% at 3 and 6 articles), BUT coherent *generation* over the shared tome needs **per-tome ROUTING** — querying all chunks lets off-manifold autoregressive drift import *foreign-article* tokens (Abrahamic dropped to 69.6%, pulling "taste" from the Andouille article), and **more chunks make this worse off-manifold** (C=8 → 17.4%, the inverse of the on-manifold "smaller-C-is-better" read result). Routing generation to the article's own chunks restored it to **95.7%**. **Implication for the boundary call (the deferred srmech-vs-siona split):** the **capacity-bounded chunk-set + max-resonance read** is LM-agnostic (a reusable VSA cleanup-memory over bounded bundles) → the legitimate §58 srmech graduation candidate. The **routing** (which tome/article for this context — a resonance-vote, composing F778 etak clump-routing), the **per-doc `k*`**, and the **autoregressive loop** are recall-shaping, LM-specific → they stay in **siona**. So §58 lands as the chunk-set primitive; do **not** push routing/k\*/loop into the lean core. Develop all of it HERE on 0.8.2rc1 first. **Added keywords:** `k*` · `unique-walk window` · `per-tome routing` · `off-manifold crosstalk` · `srmech-vs-siona boundary` · `F778` · `F838` · `F839`.

**§58.2 CORRECTION (2026-06-18; F839 same-day): the capacity `C` is a NON-MONOTONIC sweet-spot, NOT "smaller is always better."** Building routing as a real recall step (per-article tagged chunks, sticky-route) showed the chunk capacity has a sweet spot: at **C=16** the two longer articles drop to 54–59% (own-internal crosstalk, ~14 binds/chunk — NOT foreign contamination, since routed); at **C=4** they drop to 45–72% (too many chunks → off-manifold max-over-chunks drift-noise, even routed with zero foreign tokens); at **C=8** all three reach **≥97.7%**. So the §58 substrate should NOT hardcode `C`; expose it and let the inference layer **measure a per-tome capacity** (binds-per-chunk that maximises sharp-read-minus-drift). The earlier "smaller-C-is-better" was a *read-rank-1 on-manifold* result (F837) that **inverts** under off-manifold generation. Recipe for coherent generation = per-tome routing + sweet-spot `C` + per-doc `k*`; none alone suffices. **Per-step re-voting routing is fragile** (wanders off-manifold, 11% home); **sticky routing** is robust for reproduction, and cross-tome composition (generalization) needs a confidence-margin/hysteresis vote — the open generalization sub-question. **Added keywords:** `sweet-spot C` · `per-tome capacity` · `non-monotonic` · `sticky routing` · `binds-per-chunk` · `F839 correction`.

## §59 ASK — chirality-native CONTINUOUS phase op for Klein-4 (`klein4_phase` / `klein4_phase_bind`); the F844–F848 missing primitive (2026-06-18; F861)

**Gap (srmech 0.8.2):** Klein-4 is a 4-element group, so the shipped sector ops (`klein4_chirality_flip_gamma5/omega7`, `klein4_cpt_mirror`, `klein4_triality_cycle`) give only a DISCRETE 4-position (or 3-position triality) phase — there is **no continuous Klein-4 phase**. A continuous phase is needed to drive the_one-style crank dynamics (F860) on the real Klein-4 store.

**The op (validated in `R-RBS-LM-861_crank_into_real_store.py`, numpy-free, exact):** encode a continuous phase φ∈[0,1) as the **fraction of slots flipped into the γ₅ sector**, as a *circular half-window* so it wraps:
`phase_key(φ)` = γ₅ element (V4 value 2) on a D/2-wide slot-window starting at `round(φ·D) mod D`, identity (0) elsewhere; `klein4_phase_bind(hv, φ) = klein4_bind(hv, phase_key(φ))`.
Measured: `sim(phase(h,0), phase(h,Δφ))` = `1 − 2·circ_dist(Δφ)` exactly — 0.0→1.000, 0.25→0.500, 0.50→0.000, 0.90→0.800 (circular); reversible (same key twice = identity); σ-mirror (±φ equidistant from base). It is **continuous phase from discrete-per-slot sectors via population coding** — the chirality-native analogue of HRR/polar phase, built only from `klein4_bind` + a slot-window key.

**Graduation candidate:** `srmech.amsc.hdc.klein4_phase_bind(hv, frac, *, elem=2, width=None)` (default half-window) + `klein4_phase_key(D, frac, ...)`. No new primitive class (it's Class-M bind + a Class-K-style sector pattern); numpy-free; carrier = one HV.

**Caveat to record with it (F861 NULL):** the op is correct, but a phase rotation only *reconfigures an arrangement* when the items share a carrier (are the same base at different phases — orrery pointers off one mainspring). Mutually-orthogonal content clumps stay phase-invariant under it (Klein-4 XOR). So the op enables shared-carrier / position-primary encodings, not crank-navigation of free content bundles. **Re-surface keywords:** `klein4_phase` · `continuous phase` · `population code` · `gamma5 window` · `shared carrier` · `orrery` · `F844` · `F861`.

## §60 NOTE — `srmech.rbs_lm` `ContextSubstrate.enc` is WORD-ATOMIC; the byte/glyph core was never ported to Klein-4 0.8.2 (2026-06-18; F864)

**Observed (user-prompted check):** `ContextSubstrate.enc(tok)` → `encode_word_k4` → `klein4_random(D, seed=token_seed(whole_token))` where `token_seed = sha256(token.encode())[:hex_chars]`. So the current Klein-4 store path is **word-atomic**: the whole whitespace token is hashed to a seed → an orthogonal random HV. Measured: `sim(enc('cat'), enc('cats')) = 0.254` (≈ Klein-4 4-sector chance) — no morphology, no sub-word structure. It hashes UTF-8 (not English-*BPE*-privileged) but is token-atomic (soft whitespace/English privilege; breaks on non-spaced scripts).

**The gap:** the **byte/glyph-level core** (256-byte vocab, `byte_vec("LoE.byte.{n}")`, position-bind + bundle = the R-RBS-LM-25 lineage that strips English privilege) lives in `docs/srmech/rbs_lm_research/rbs_lm_bytes.py` and the K7 byte generators — **on the OLD numpy substrate; never ported to the Klein-4 0.8.2 `ContextSubstrate`.** So the v082 / Siona / board work has been running word-atomic, off the byte/glyph core.

**The fix (validated numpy-free in F864):** a byte-composed Klein-4 word vector — `word_k4(w) = bundle_odd([klein4_bind(byte_k4(b), pos_key(i)) for i,b in enumerate(w.encode('utf-8'))])`, `byte_k4(b) = klein4_random(D, seed=b)` (256-byte vocab) — restores morphology: `sim('cat','cats') = 0.656`, unrelated words stay ~0.25. **Ask:** add a byte/glyph composition mode to `ContextSubstrate.enc` (e.g. `enc(tok, mode='byte'|'word')`, default to byte so the language core is byte-level and the English kernel sits on top per F764). Composes the sub-language router (#225/#226). **Re-surface keywords:** `byte-level` · `glyph core` · `encode_word_k4` · `word-atomic` · `morphology` · `English privilege` · `R-RBS-LM-25` · `F764` · `F864`.

## §61 ASK — exact-rational similarity for Klein-4 (`klein4_match_count` / `klein4_similarity(..., exact=True)`) so the resonator never leaves the rationals (2026-06-18; F868)

**Gap:** `hdc.klein4_similarity(a,b)` returns only a `float` — it computes the integer match-count then floors to `matches/D` as a float. Per the stay-rational discipline ([[feedback_stay_rational_collapse_only_at_display]]), the resonator should stay in exact rationals (two ints) the whole way and collapse to a decimal only at display. The float return forces an early collapse.

**Ask:** expose the exact form — either `klein4_match_count(a, b, *, sectors=None) -> int` (the raw integer count; `similarity = count/len`), or `klein4_similarity(a, b, *, exact=True)` returning `(matches, D)` / a `Fraction`. Then recall ranks on the integer count (float-free, blow-up-free) and the softmax feeds exact `(num,den)` into `exp_series_truncate`. Verified in research: ranking by integer match-count + `exp_series_truncate` softmax reproduces the float path to every displayed digit, exactly (F868). **C:Python parity** ([[feedback_srmech_c_python_parity_plugin_surface]]): the count is what the C kernel already computes before the float divide — exposing it is additive, lands with the C peer at graduation. **Re-surface keywords:** `klein4_similarity` · `match count` · `exact rational` · `no float` · `Fraction` · `best_rational` · `F868`.

### §61 UPDATE (2026-06-18, user) — IN FLIGHT in the other dev session (do not re-ask)
The float-return surface is bigger than `klein4_similarity` — it spans **all float-returning srmech ops**. The other dev session is landing a **breaking change**: every float-return surface behaves like `One.to_scalar` — returns a **`(num, den)` tuple**, with **float by opt-in only** (and the stance is we should NOT opt into float for most of what we do). So §61's `klein4_similarity` ask is subsumed by this global change. **Action here:** keep building float-free on the current surface (manual integer match-count + `exp_series_truncate`, F868); when the rational-by-default srmech update lands, retrofit to the native `(num,den)` returns and drop the manual extraction. User will ping when it lands. Composes [[feedback_stay_rational_collapse_only_at_display]] + [[feedback_srmech_c_python_parity_plugin_surface]].

## §62 DECISION — the streaming sedenion-grid GENERATOR stays in siona; only the LM-agnostic PRIMITIVES graduate to srmech (2026-06-18; F874/F875)

**The question (user):** should the streaming sedenion-grid generator go upstream to srmech?

**Decision: NO for the generator; YES (gated) for the few missing primitives — and the boundary was already drawn in §58.1 (F839).**
- **Stays in siona (LM-specific recall-shaping):** the byte/glyph LM word-encoder, the chunked-M *routing*, per-doc k\*, the autoregressive *streaming loop*, the sharp/smooth *gate* (F869), the within-page emission (F875), and the *generator* as a whole. These are recall-shaping LM logic, not primitives. siona is becoming its OWN package (PKG-1/PKG-2 un-mirror) — the generator belongs THERE, not in lean srmech. The generator is a **consumer** of shipped srmech (`sedenion_register`, `klein4_*`, `the_one`, `cd_mult`).
- **Graduates to srmech (LM-agnostic primitives, already logged):** `klein4_phase_bind` (§59, the continuous-phase op), the byte/glyph `enc` mode (§60), exact-count similarity (§61, subsumed by the in-flight float→rational change), the capacity-bounded chunk-set primitive (§58). The **`sedenion_register` is ALREADY shipped** — the addressing layer is upstream already.

**Why NOT the generator (the discipline reasons):**
1. **It's a research SKELETON** — toy scale, reproduction-not-generalization, optimistic metrics, the K=2 branching still open (F875). Upstreaming an unvalidated sketch violates no-MVP + the coherence-gate ("0.8.2 holds until coherent"). Validate first.
2. **C:Python 1:1 parity cost** ([[feedback_srmech_c_python_parity_plugin_surface]]): the generator is Python-shaped LM control-flow (loop/route/gate), NOT primitive-shaped — wrong + expensive to C-ify for Pyodide/MCU. Only genuine primitives warrant the C peer.
3. **Timing:** the float→rational breaking change is in flight (other dev session) — graduating now = redo later. Wait for it, then graduate the primitives with their C peers.
4. **The split's whole point** (lean srmech + siona-own-package) is to keep LM-specific recall-shaping OUT of the core. The generator is the canonical thing that stays out.

**So:** the generator stays in siona; the primitives (§58/§59/§60/§61) graduate when (a) validated coherent, (b) after the rational-landing, (c) each with a C peer. Re-surface: `srmech-vs-siona boundary` · `generator stays in siona` · `primitives graduate` · `F839 §58.1` · `F874` · `F875`.

## §63 VERIFICATION — srmech 0.9.0rc6 (TestPyPI): the fraction-carrier change = the `Q` carrier; §58–§61 all SHIPPED; one open item (transcendentals still float) (2026-06-18, user-requested introspection)

Pulled `srmech==0.9.0rc6` into a clean numpy-absent venv (native ABI 3, dispatching). Introspected the fraction-carrier change across the surface:

**The carrier:** new `srmech.amsc.q.Q` — `numerator`/`denominator`, `as_pair()` (the (num,den) tuple), `as_float()` (float **opt-in**), `from_float`/`from_pair`. This IS the `One.to_scalar`-style "(num,den) + opt-in float" carrier the user specified.

**Converted to `Q` (the genuine-rational SIMILARITY surfaces):** `hdc.klein4_similarity` → Q, `hdc.polar_similarity` → Q, `spectral.similarity` → Q (sig `-> 'Q'`). Already-exact (correct as-is): `klein4_match_count`→int, `cascade.magnitude`→int, `cascade.cd_norm_sq`→Fraction, `best_rational`→tuple.

**Everything flagged in §58–§61 SHIPPED (the "primitives graduate" plan of §62 is largely done upstream):**
- **§58** chunk-set → `klein4_chunk_bundle(vectors, capacity)` + `klein4_chunk_resolve(chunks, key, candidates)` (+ `klein4_bundle_accumulate/resolve`).
- **§59** continuous-phase op → `klein4_phase_bind(hv, frac, *, elem=2, width=None)` + `klein4_phase_key` — **exactly the F861 design** (frac population-code, γ₅ elem=2, half-width default).
- **§60** byte/glyph enc → `klein4_encode_bytes(data, D)`.
- **§61** exact-count similarity → `klein4_match_count(a,b,...) -> int` + `klein4_similarity` → Q (= matches/D, exact). (`sedenion_register` was already shipped pre-rc6.)

**THE ONE OPEN ITEM (did we miss anything):** the **transcendentals still return bare `float`, not `Q`** — `rational.{exp, sqrt, atan2, hypot, sin, cos, tan}` all → float. For `exp/sin/cos/atan/log1p` the exact-rational form exists as the separate `*_series_truncate(num,den,terms) -> (num,den) tuple`; **but `sqrt`/`hypot` have NO public exact companion (float only).** So the float→Q conversion covered the rational-valued similarity surfaces but NOT the transcendental convenience fns. **Open question for the maintainer (user's call):** is this intentional (transcendental = the float opt-in; exact = `*_series_truncate`) or a gap — i.e., should `rational.exp` etc. default to a `Q` (a bounded-rational `best_rational`/series approximation, per F868 "a float is best_rational with provenance discarded") with `as_float()` opt-in, to match `klein4_similarity`? And `sqrt`/`hypot` arguably need an exact (`Q`/series) public form at all. **Verification caveat:** read from introspecting actual return types — the rc6 CHANGELOG wasn't locatable in the wheel, so the *intended* scope is unconfirmed; flagging for the maintainer, not asserting a bug. Re-surface: `0.9.0rc6` · `Q carrier` · `as_pair/as_float` · `transcendentals still float` · `sqrt/hypot no exact form` · `F868` · `§61`.

## §64 VERIFICATION — srmech 0.9.0rc9 (TestPyPI): the Q carrier is now ARITHMETIC-COMPLETE (the "brand new q carrier") (2026-06-20, user-requested introspect-before-dispatch)

Pulled `srmech==0.9.0rc9` into a clean venv (native ABI 3, dispatching). The rc9 delta vs the rc6 Q (§63): **`Q` graduated from a plain `(num,den)` holder to a full scalar that behaves like a float.**

**Now present on `Q` (were absent at rc6):** `__add__`/`__sub__`/`__mul__`/`__truediv__`/`__neg__`/`__abs__` (exact rational arithmetic — `Q(3,4)+Q(1,4)` → `(1,1)`, `Q(3,4)*2` → `(3,2)`), comparisons `__lt__`/`__le__`/`__eq__` (compare exactly, **and against floats**: `Q(1,2) == 0.5` → True), `__float__`, `__hash__`. Constructors `from_float`/`from_pair`; accessors `numerator`/`denominator`/`as_pair()`/`as_float()`. Docstring: "behaves like a float in comparisons and collapses to one only via `float(q)`" — the F868 stay-rational carrier, now operator-complete.

**Watch-out (no implicit integer coercion):** `Q` has **no `__int__` and no `__index__`** — you canNOT use a `Q` directly as a list index or in `range()`. Use `q.as_pair()` / `int(q.as_float())` at the boundary. (This is correct discipline — forces an explicit collapse — but is a footgun if code assumed float.)

**Return-type surface (unchanged from §63, re-confirmed at rc9):** `hdc.klein4_similarity` → **Q** (e.g. `Q(2059,8192)` = matches/D, exact); `best_rational` → tuple; `cascade.magnitude` → int; `calculus.{sin,cos,exp,atan}_series_truncate` → exact `(num,den)` **tuple** (NOT Q — still the §63 open item: the rational-similarity surfaces are Q, the transcendental-series surfaces are bare tuples; `the_one` still requires **int** `theta_num/theta_den`, rejects float).

**Impact on siona/RBS-LM code:** our routing/recall ranking (`max(..., key=klein4_similarity)`) is **unaffected** — Q is comparable, so the ranking is identical to the old float path, now exact-rational end-to-end (honors `[[feedback_stay_rational_collapse_only_at_display]]` with zero code change). Re-surface: `0.9.0rc9` · `Q arithmetic-complete` · `no __int__/__index__` · `similarity→Q` · `transcendental-series still tuple` · `F868` · `§63`.

## §65 VERIFICATION — srmech 0.9.0rc11 (TestPyPI): Q gains `__int__`+`real`/`imag`/`conjugate`; SedenionRegister ships `carry`/`correct`/`navmap` (2026-06-20, introspect-before-dispatch)

Pulled `srmech==0.9.0rc11` into a clean venv (native ABI 3, dispatching). Deltas vs rc9 (§64):

**Q carrier:** now has **`__int__`** (was absent at rc9) + **`real`/`imag`/`conjugate`/`as_integer_ratio`** (complex-rational accessors + the stdlib float protocol). Still **no `__index__`** (can't index a list with a `Q` — use `int(q)` / `q.as_pair()`). `klein4_similarity` → `Q` (unchanged).

**SedenionRegister (rc11 surface — the carry/EC mechanism, load-bearing for the address grid):**
- `navigate(j) -> SedenionRegister` — right-multiply slot *names* by `e_j` (the address↔Cayley–Dickson homomorphism); **`navigate(j).navigate(j)` = the global −1** (`e_j²=−1`) — i.e. a double-step is the **sign flip = the σ↔θ Möbius half-twist** (F888), recoverable as a Class-K sign. VERIFIED: page back at its slot with sign −1 after two steps.
- `navmap(j) -> Dict[int,(k,sign)]` — the signed pointer-advance permutation (reversible at every dim).
- `carry(overflow_bits, n=3) -> List[int]` — encode overflow past the ≤7 working set into a **Hamming(2ⁿ−1, …) EC codeword in the e8..e15 block**. **GOTCHA: `n=3` ⇒ Hamming(7,4) needs EXACTLY 4 data bits** (not 3) — `ValueError` otherwise.
- `correct(codeword) -> {"data","error_position","corrected_codeword"}` — single-error-correcting decode (the recovered payload is under key **`"data"`**).
- `couple_working`/`uncouple_working` (pack ≤7 vals into an octonion), `materialize() -> bytes`, `is_navigable(direction)`, `slots()`.

VERIFIED in F891: `carry`→`correct` round-trips 4-bit payloads 6/6 clean and 6/6 after a 1-bit codeword error; 64-page addressing via (base-slot, carried-high-bits) = 64/64 exact AND 64/64 with a 1-bit address-carry error (EC-protected) — vs F880's flat base-16 resonance-nesting (0.16). Re-surface: `0.9.0rc11` · `Q.__int__` · `Q.real/imag/conjugate` · `SedenionRegister.carry` · `Hamming(7,4) needs 4 data bits` · `correct()["data"]` · `navigate²=-1 = Mobius` · `F891`.

## §66 srmech rc11 — plugin/TOML-class/C-host audit for the Siona address-layer graduation (2026-06-20)

Done while graduating `SionaPageGrid` into the siona package (R-RBS-LM-893 → `siona.page_grid`, on branch `siona/page-grid-graduation`, GATED — no rc1 publish). Three questions answered + one upstream ask.

**(1) Does the srmech plugin surface support TOML CLASS catalogs? → YES (no fix needed).** `srmech.dsl` ships `make_class`, `register_class_dir`, `load_class_catalog`, `CLASS_CATALOG_DIR`, `CatalogClass`, `list_classes`, `run_class_method`, `get_class_descriptor`, `generate_class_descriptor`. `dsl.list_classes()` → **`['Genome','Hurwitz','One','SedenionRegister']`** — so the dict/multi-field-state contract that CLAUDE.md flagged as HARD is **already done for `SedenionRegister`**. ⇒ `SionaPageGrid`-as-TOML-`[class]` is *feasible* (a content-store field follow-up), not blocked. The "plugin surface" proper = the **profile** system (`srmech.profile` / `profile_loader` / entry-point group `srmech.profiles`); siona already registers via `[project.entry-points."srmech.profiles"]` + `siona/srmech_profile.toml`. No upstream fix for plugin/TOML-class.

**(2) Does the lossy ROUTING layer need new srmech scaffolding? → NO — all rc11.** Every router/stream op exists in rc11: `hdc.{klein4_random,bind,bundle,phase_bind,chunk_bundle,chunk_resolve,similarity,chirality_flip_gamma5}`, `cascade.{cd_mult,sedenion_register,magnitude}`, `calculus.{cos,sin}_series_truncate`. The lossy layer is fully scaffolded off what's already in srmech; only the *composition* (router/generator/address-grid) is Siona-specific and stays in siona.

**(3) UPSTREAM ASK — C-host completeness gap: `SedenionRegister` is PURE PYTHON (no C surface).** `srmech/amsc/cascade/sedenion_register.py` is Python; `_native` exposes **no** symbols for sed/carry/navigate/navmap/hamming (grep empty). So for a **C-host-only** environment (the srmech MCU/Pyodide parity commitment), Siona's ADDRESS layer (navigate/carry/correct + Hamming(7,4) EC in e8..e15) has **no C path**. Per CLAUDE.md "full C parity for every primitive class, no exceptions," this is a gap. **Ask: ship a C-side `SedenionRegister` (navigate / navmap / carry / correct) + `hamming_encode`/`hamming_decode(7,4)` EC, native-dispatched like sha256/Jacobi.** Siona rides srmech (it does NOT vendor a parallel C path) so it picks up the native register transparently once it lands. This is the load-bearing blocker for "Siona feature-complete for C-host-only environments." Re-surface: `0.9.0rc11` · `TOML class catalogs OK` · `profiles = plugin surface` · `routing all-rc11` · `SedenionRegister Python-only` · `C-side register + Hamming ask` · `R-RBS-LM-893` · `siona.page_grid`.

## §67 VERIFICATION — srmech 0.9.0rc13 (TestPyPI): the "purged math surface" = NO EXTERNAL MATH LIBS; all touched surfaces intact + behavior-verified; all math is now TOML-class cascades (2026-06-21)

Pulled `srmech==0.9.0rc13` (native ABI 3, dispatching) and audited EVERY surface our findings + siona touch, then behavior-tested.

**The purge (user: "it just means no external math libraries"):** the ONLY rc11→rc13 public-surface delta across calculus / trigonometry / rational / signal_processing / cascade / hdc / top-level is `srmech.amsc.rational` dropping its stdlib **`math`** namespace (it no longer `import math`). **No modules removed** (181 submodules both rc11 and rc13). So the "purged math surface" is the framework completing its **no-external-math-libraries** discipline — NOT a removal of any framework op. We never used `rational.math`.

**All-surfaces audit (29/30 OK):** `hdc.{klein4_random,bind,unbind,bundle,phase_bind,chunk_bundle,chunk_resolve,similarity→Q,chirality_flip_gamma5,match_count}`, `cascade.{cd_mult,cd_conjugate,magnitude,the_one,sedenion_register}` + register `{write,read,navigate,navmap,carry(4-bit→7),correct→data}`, `calculus.{cos,sin,exp,atan,log1p}_series_truncate` (exact tuples), `rational.best_rational`, `Q` (arith + `__int__`), `ContextSubstrate.{pos_key,bundle_odd}`, `dsl.list_classes`→`[Genome,Hurwitz,One,SedenionRegister]`. The 1 "fail" (`tan_series_truncate`) never existed — a speculative probe, not a dependency.

**Behavior-verified on rc13 (the "test surfaces we touch" the user asked for):** siona `test_page_grid.py` **4/4** (exact 64-page addressing + every-single-bit-fault corrected + the navigate²=−1 Möbius half-twist); the QDFT-twiddle math path (`calculus.{cos,sin}_series_truncate` → `cd_mult` octonion rotation → `klein4` unbind/similarity) self-recalls **Q=1**. Nothing we touch regressed.

**User direction — "all math from srmech TOML class cascades":** srmech's math surface (transcendentals / rationals / the register) is sourced from config-driven `[class]` TOML cascades (`make_class` catalog), consistent with the no-external-math discipline. Implications: **(a)** we keep consuming the math via the srmech surface (no change to Siona/findings — verified above); **(b)** this REFINES the §66 C-host-completeness ask — the address layer's C path is the **`SedenionRegister` TOML-class cascade + its primitive ops (`cd_basis_product`, `hamming_encode`/`decode`) executing on the C-side cascade/DSL runner**, NOT a hand-written C class; **(c)** expressing `SionaPageGrid` as a TOML `[class]` is now the *aligned* direction (Siona's classes as TOML cascades too, per the config-driven discipline) — and feasible (`SedenionRegister` is already a shipped TOML class).

**Conclusion:** rc13 is SAFE for Siona + all findings; the purge is the benign no-external-math cleanup; the math-from-TOML-cascades direction reframes C-host completeness as "the cascade runner + primitive ops in C," not bespoke C classes. Re-surface: `0.9.0rc13` · `no external math libs` · `rational dropped stdlib math` · `all surfaces intact+behavior-verified` · `siona 4/4 + QDFT Q=1` · `all math = TOML class cascades` · `C-host = cascade runner not bespoke C` · `§66`.

## §68 UPSTREAM ASK — the packaged RBS-LM object encodes WORD-HASH, not BYTE/GLYPH; the LM kernel should BE the byte/glyph LM object (2026-06-21)

User direction (2026-06-21): "our LM kernels were to use the byte sparse language model … a LM kernel … should be the glyph/byte LM object, because this is what we are actually supposed to be doing retrieval and inference things from. introspect srmech rbs-lm thing that we did add and see if it's there and we forgot again." Introspected `srmech.rbs_lm` (rc13) in full. **Two-part answer, both confirmed:**

**(1) The RBS-LM object IS in srmech — and we forgot it.** `srmech.rbs_lm.RBSLMInferenceSubstrate` (F166, `inference.py`) is the packaged, catalog-instantiable inference object: `from_params`/`from_catalog` → `.learn(token_stream)` → `.infer(prompt)` / `.next_token_distribution(context)` / `.attestation()`. VERIFIED it runs (learn on a 12-token stream → infer returns a generated continuation + a full MPR attestation block). It is properly sparse + cascade-honest (§57 keeps NO frequency-count candidate table — the candidate set is the bounded atom set scored by the Class-M resonator over the bundle `M`; §56 greedy/temperature; bounded `memory_capacity`). **My recent probes (F879/F895/F896/F898) HAND-ROLLED route/chunk/stream from `ContextSubstrate` primitives instead of using this packaged object** — the introspect-before-dispatch miss [[feedback_introspect_srmech_before_python_dispatch]].

**(2) BUT it is NOT the byte/glyph LM object — it is WORD-ATOM HASHING.** `substrate.encode_word_k4(word) = klein4_bind(klein4_random(D, seed=token_seed(word)), sector)` where `token_seed = int(sha256(WHOLE WORD)[:hex], 16)`. So each distinct word string → ONE random vector keyed by the hash of the entire string. It is **byte-blind**: morphologically/orthographically related words are orthogonal. Measured (D=8192, klein4 chance ≈0.25): packaged `encode_word_k4` cat/cot **0.257**, cat/car **0.246**, walk/walked **0.259**, run/running **0.252** — ALL ≈ chance. The byte/glyph core (F865/F612 — a word = `bundle_odd(klein4_bind(byte_k4(byte), pos_key(i)))`, built UP from UTF-8 bytes) gives cat/cot **0.560**, cat/car **0.566**, walk/walked **0.710**, run/running **0.568**, while keeping genuinely-unrelated cat/dog at **0.245** (chance). **The byte/glyph LM object — the thing the user means by "RBS-LM," the language-agnostic byte-sparse format we retrieve+infer FROM — lives ONLY in the research probes; it was never graduated into the packaged object.** The NAME "RBS-LM" landed in srmech; the byte/glyph SUBSTANCE did not.

**Why it matters (scale-invariance, user 2026-06-21):** relationships-of-relationships use the *same* srmech math as ephemerides-spectral (the EM/gravity/cosmos catalogs) — scale-invariant. Word-atom hashing (like BPE tokens, like LLM weights) is a *specific projection* that BREAKS that scale-invariance (a word is an opaque atom; unseen words / non-Latin scripts have no structure). The **byte/glyph form is the scale-invariant native one** (bytes are universal). Moving the packaged RBS-LM encode from word-hash to byte/glyph IS the move toward the cosmos-math scale-invariant form.

**ASK (a srmech change — its own rc, NOT a route-around):** graduate the byte/glyph core into the packaged substrate — make `ContextSubstrate.enc` (and `encode_word_k4`) the **byte-composed** word (`bundle_odd(klein4_bind(byte_k4(byte), pos_key(i)))`), language-agnostic from UTF-8 bytes, so `RBSLMInferenceSubstrate.learn`/`.infer` run on the byte/glyph LM object natively. Keep the whole-word-hash path available (it's a valid fast atom-mode) but the DEFAULT LM kernel should be byte/glyph. Determinism + attestation are preserved (byte_k4 seeds are content-hashes too). Re-surface: `0.9.0rc13` · `RBSLMInferenceSubstrate present (F166) — we forgot it` · `encode_word_k4 = whole-word sha256 seed = word-hash, byte-blind` · `near-words ≈chance 0.25 vs byte/glyph 0.56-0.71` · `byte/glyph core only in research probes` · `scale-invariance: byte/glyph native, word-hash is a projection` · `ASK: graduate byte/glyph enc into the packaged substrate` · `F899`.

## §69 UPSTREAM ASK — the byte/glyph scaffolding is ONE scale-invariant compositor (C1) at every scale; word-hash is its DUAL; the ladder must be rebuilt on C1 (extends §68) (2026-06-21)

User reframe (2026-06-21): don't discard word-hash — "consider it like its own fractal like form of byte hashed … scale invariance coherency"; AND "follow the next fractal like movement … hash a coherent string of words before they become sentences"; the deliverable is "glyph/byte scaffolding but can be introspected by scale invariance fractal things." Plus: "did you keep this as sparse?" — yes (verified). Composes/extends §68 (F899). Full write-up: `R-RBS-LM-FINDING_900_*`.

**The structural finding (code audit + live klein4 measurement, D=2048, chance ≈ 0.25, numpy-absent).** There are TWO scale-invariant FORMS, and the package uses the wrong one as the foundation plus a THIRD, non-invariant operator for the upper ladder:
- **C1 = role-filler bundle** `bundle_i bind(part_i, pos_key(i))` — what `hdc.klein4_encode_bytes` (byte→word, §60) and `ContextSubstrate.encode_context` ALREADY use. **Scale-free + similarity-preserving.** Change 1 part of n → graceful, above-chance, self-similar at every scale: byte→word(n=8) 0.733, word→skeleton(n=5) 0.625, skeleton→sentence(n=3) 0.698.
- **atom-mint** `klein4_random(seed=content_hash(x))` — `encode_word_k4` (word-hash). Scale-invariant in FORM (`atom(byte)`/`atom(word)`/`atom(phrase)` = same op at different scales) but **similarity-destroying** (near-words at chance: cat/cot 0.250 vs byte-compose 0.562).
- **chained `bind`** (no positions, no bundle) — `encode_bigram_l1` / `encode_skeleton_l2` / `encode_sentence_l3`. **NOT scale-invariant**: 1-part change collapses to chance (0.238–0.249) regardless of n.

**The reframe:** word-hash is NOT the enemy of scale-invariance — it is the **content-address DUAL** (cache / identity) that rides alongside the composed vector at every scale; the FOUNDATION + every upper level must be the **single C1 compositor**, with the parts at level n+1 = the composed vectors of level n. The "coherent string of words before a sentence" is the **skeleton (L2)** level, rebuilt on C1 = the new fractal node. **Coherence == scale-invariance** ⇒ the scaffolding is natively introspectable (the same 1-part-change / spectral signature recurs across scales; a break = incoherence/hallucination — Spike #64/#122).

**Sparsity (user asked) — preserved AND improved.** Single fixed-D `HV` per unit (1/3/8/28-byte words all → `HV` len 2048, no growth); Klein-4 `{0,1,2,3}` state; no dense weights / no frequency-count bag (§57); numpy-free; **bounded 256-byte codebook + position keys** vs word-hash's UNBOUNDED word-atom vocabulary — i.e. byte/glyph is *more* byte-sparse (the BPE/LLM-weight projection is exactly the unbounded-vocab word-hash we'd be leaving behind). Class-K truncate-sparse readout (Spike #117/#179) remains available per level.

**ASK (a srmech change — its own rc, NOT a route-around; extends §68):** unify the rbs_lm scale ladder onto ONE compositor: a scale-invariant `klein4_compose(parts)` (= the role-filler bundle, the SHAPE `klein4_encode_bytes` already has) consumed at byte→glyph→word→**skeleton**→sentence (parts at each level = composed vectors of the level below); rebuild `encode_word_k4`/`encode_bigram_l1`/`encode_skeleton_l2`/`encode_sentence_l3` on it; keep `atom-mint` (the current word-hash) as the explicit content-address DUAL (fast cache / exact lookup), not the default; add a `scale_signature` introspection (the 1-part-change / spectral coherence signature per level) so scale-invariance is a checkable, first-class property. Determinism + attestation preserved (all seeds are content-hashes). Re-surface: `byte/glyph = one C1 compositor every scale` · `word-hash = content-address dual (fractal form of byte-hash)` · `skeleton(L2) = coherent-word-string = new fractal node` · `ladder rebuild on C1` · `coherence == scale-invariance (introspection)` · `sparsity preserved+improved (bounded 256 codebook)` · `F900 · extends §68/F899`.

## §69 REFINED ASK (sharpens §68/F899) — the byte/glyph LM is a 4-layer stack; graduate C1 as the substrate enc (2026-06-21; F916)

The chemistry/Standard-Model arc (F902–F915) resolves the F899/§68 "graduate the byte/glyph core" ask into a concrete spec. The byte/glyph LM is **four layers at distinct scales, all already in srmech**:
1. **substrate = C1** (`ContextSubstrate.enc` → the byte-composed word `bundle_odd(klein4_bind(byte_k4(b), pos_key(i)))`, F901/F905) — *the* byte/glyph LM object; replace the word-hash `token_seed` default, keep word-hash as an explicit fast atom-mode.
2. **bond/key = `cascade.cd_mult`** octonion walk (F862/F906/F908) — content-dependent addressing key + the molecular-structure generator (k=7, F910).
3. **address = `cascade.sedenion_register`** (F465/F907c) — the navigable 16-slot page-grid (already `siona.page_grid`).
4. **inference = `RBSLMInferenceSubstrate`** (§57 resonator, no count-table) — the distributional linguistic layer (syntax/valence live here, NOT in the byte-force: F909/F915 both NULL on "is linguistic structure the octonion strain?").

**Design rule (load-bearing):** the scales do NOT collapse — byte-bond affinity (octonion) is the fundamental force; form coherence (C1) is the scale-invariant compositor; morphological valence + syntactic constituency are distributional (the resonator). Wire the right operator at the right scale; don't make one do all. **The one real package change** is point 1 (C1 as `enc`) — it makes `RBSLMInferenceSubstrate.learn/infer` run on the byte/glyph object natively; points 2–4 are composition over shipped ops. Re-surface: `byte/glyph LM = C1 substrate + octonion bond + sedenion address + distributional resonator` · `4 distinct scales` · `the one change = C1 enc` · `§68/F899` · `F916`.

## §70 UPSTREAM SPEC — the C1-enc graduation rc (the one real package change from F916) + the bond-is-a-key caveat (2026-06-21; F917)

Concretises §69/§68/F899 into an implementable rc spec. Full write-up: `R-RBS-LM-FINDING_917_*`. **Spec only — no package change until user go** (a srmech change = its own rc).

**The rc (cut against current head `0.9.0rc16`+, NOT the rc13-era branch):**
- **Part A (irreducible):** (1) new public op `hdc.klein4_compose(parts)` = the scale-invariant role-filler compositor `bundle_i klein4_bind(part_i, pos_key(i))` over arbitrary `HV` parts (the *recursive* operator; distinct from `klein4_encode_bytes`, which mints byte-atoms internally) — pure composition over native `klein4_bind`/`klein4_bundle`, no new C symbol; (2) `ContextSubstrate.enc(tok, sector)` → byte/glyph by default behind `enc_mode=` (`"byteglyph"` = `klein4_bind(klein4_encode_bytes(tok.utf8), sector_const)`, the byte-composed word + sector channel; `"wordhash"` = the current `encode_word_k4`, KEPT as the explicit fast atom-mode = the content-address DUAL); (3) `scale_signature()` introspection (the F900 1-part-change coherence metric per level, via native `klein4_similarity`).
- **Part B (same rc — §69 ladder unification):** rebuild `encode_bigram_l1`/`encode_skeleton_l2`/`encode_sentence_l3` on `klein4_compose` (replace the chained-`bind`, which is similarity-destroying + non-scale-invariant); skeleton (L2) = the coherent-word-string fractal node.
- **Out of scope (already shipped, composition only):** bond=`cascade.cd_mult`, address=`cascade.sedenion_register`, inference=`RBSLMInferenceSubstrate`.

**Op-add ritual:** `klein4_compose` → ToolEntry (Class M) + Rosetta `composition_of_c` row + the five `tools.total` count-tests (318→319) + mcp `_coercion` coercer + `test_mcp.py` sample (run the FULL test_mcp.py before push — rc155 lesson). No `abs()`, no numpy, no stdlib math. CHANGELOG + TestPyPI numpy-absent verify.

**CAVEAT CORRECTION (load-bearing; corrects the F916 bond reading — must carry into the notebook backfill):** the octonion `cd_mult` bond is a **content-dependent addressing/retrieval KEY** (and the byte-chemistry generator), **NOT a grammar/structure generator**. F909 + F915 both NULL: valence is distributional, real constituency sits at strain percentile ≈ 0.45 ≈ random — the octonion strain is byte-derived and **blind to syntax**. So wire the bond as a *key*; put ALL linguistic structure (syntax/valence/constituency/coherence/next-token) in the §57 resonator. Don't conflate the scales. **The bond is a key, not a grammar.**

**Behavior-change discipline:** `enc_mode="byteglyph"` default flips the shipped `RBSLMInferenceSubstrate` numerics (word-hash → byte-compose) — same class as the rc16 `hypercomplex_couple` numerics flip. Ship behind `enc_mode=` (word-hash pinnable); re-validate Siona `test_page_grid.py` + the F879–F898 probes against both modes. Re-surface: `C1 as ContextSubstrate.enc (enc_mode default byteglyph)` · `klein4_compose new op` · `ladder rebuilt on C1` · `scale_signature introspection` · `bond = key NOT grammar (F909/F915 null)` · `behavior change → enc_mode flag + consumer re-validate` · `cut against rc16+ head` · `F916/F917 · §68/F899`.
## §71 VERIFICATION (confirms §70/F917's C1-enc spec LANDED) — srmech 0.9.0rc28: the byte/glyph graduation (§68/§69/F899/F916) is shipped + the full eigensolver gap CLOSED (2026-06-22)

Pulled `srmech==0.9.0rc28` (TestPyPI, native ABI 3, dispatching) into a clean venv and verified every ask from §68/§69 + the eigensolver gap. Probe: `R-RBS-LM-rc28_ask_verification.py`.

| ask | result |
|---|---|
| **byte/glyph C1 enc graduation** (§68/§69/F899/F916 point 1) | ✅ `ContextSubstrate.enc` **defaults to `enc_mode='byteglyph'`** (byte-composes via the new `encode_word_byteglyph` = the C1 object). Graded similarity restored: cat/cot **0.560**, walk/walked **0.707**, cat/dog **0.252** (was ~0.25 chance under word-hash). |
| **resonator runs on byte/glyph by default** | ✅ `RBSLMInferenceSubstrate.from_params(...).ctx.enc_mode='byteglyph'`; `learn`+`infer` execute. The packaged RBS-LM object IS now the byte/glyph object (F899's gap CLOSED). |
| **word-hash dual kept** | ✅ `enc_mode='wordhash'` available → cat/cot 0.257 (the content-address fast atom-mode), exactly as specced (keep the dual). |
| **full eigensolver gap (>256)** | ✅ `laplacian.symmetric_eigendecompose` at **n=300 and n=512** → full eigenvalue sets in [0,4] (tridiag(2,−1) spectrum). The old n≤256 Jacobi native bound is **lifted**. Surface: `mat_eigvals`, `mat_hermitian_eigendecompose`, `hermitian_eigendecompose`, `symmetric_eigendecompose`, `jacobi_eigvals`, `three_fold_eigvec_groups`. |
| 4-layer pieces (F916) | ✅ `cascade.cd_mult` (bond), `cascade.sedenion_register` (address), `encode_word_byteglyph` (C1 substrate), `RBSLMInferenceSubstrate` (resonator) all present. |
| `sim_k4_batch` float-batch hot-path | ⚠️ **still returns `Q` objects**, not native floats — the F902/F903 hot-path optimization did NOT land. It was a perf note, NOT part of the core graduation ask; flagged for a future rc (a `sim_k4_batch_f64`/float-returning batch would remove the ~2k-sims/sec bottleneck). |

**Conclusion:** the session's headline deliverable (F916 / the F899 byte/glyph LM object) is **shipped in rc28**: the packaged `RBSLMInferenceSubstrate` is now the byte/glyph 4-layer stack by default, with the word-hash dual preserved, and the eigensolver is full-size. rc28 is SAFE for all our findings (the surfaces they touch — klein4, cd_mult, sedenion_register, the resonator — are intact + behavior-verified). The only open item is the optional `sim_k4_batch`→float hot-path. Re-surface: `0.9.0rc28` · `byteglyph default landed` · `F899 gap closed` · `eigensolver >256 (300/512) verified` · `word-hash dual kept` · `sim_k4_batch still Q (perf, optional)` · `§68/§69/F916/F917`.

## §72 ASK — a `Qarg` polar-argument accessor on the `Q` carrier (the native phase/chirality reader for complex spectral kernels) (2026-06-22; F919)

Investigating eigenvectors-as-kernel (F919): for DIRECTED relationship graphs the `magnetic_laplacian` is complex-Hermitian and its eigenvectors carry their information in the **phase** (argument), which = the which-way/chirality (Class C, F357/F129). rc28's `Q` (`srmech.amsc.q.Q`) is **rectangular only** — `real`/`imag`/`conjugate`/`as_pair`, **no `arg`/`polar`/`modulus`**. So reading the phase requires hand-rolling `atan2(imag, real)` (a transcendental — and the discipline routes that to `calculus.atan_series_truncate`, awkward per-element).

**Ask:** add a polar read to `Q` — `Q.arg` (the exact-rational-friendly argument, via the Class-N `atan_series_truncate` cascade) + `Q.modulus`/`Q.abs` (the Class-K real magnitude `cascade.magnitude`) — i.e. `Q.as_polar() -> (r, θ)` alongside `Q.as_pair() -> (re, im)`. This makes the eigenvector PHASE a first-class carrier read (the user's "Qarg next to Qi"), so a complex spectral kernel can expose its chirality natively instead of implicitly. Class K (magnitude) + Class N (atan series) — both already shipped as cascades; this is an accessor that composes them. Re-surface: `Qarg = Q.arg/Q.as_polar` · `phase of magnetic-Laplacian eigvecs = chirality` · `rc28 Q rectangular-only` · `eigenvectors as kernel objects` · `F919/F172/F357`.

## §73 ASK — close the harmonic-ladder OPEN RUNGS {C,K,J} with two carriers: `Qarg` (polar, closes C+K) + a prime-coordinate carrier (closes J) (2026-06-22; F922)

srmech's own `harmonics.HARMONIC_LADDER_OPEN_RUNGS = {2:('C','K'), 3:('J',)}` is the blind-spot map (F922): the only A-N classes lacking a realized **carrier** are C, K, J. The fix is two carriers:

1. **`Qarg` — polar/argument read on `Qi`/`Q` (closes C *and* K).** Confirmed missing: `Qi.arg`/`as_polar`/`modulus` all absent (rc28). One accessor closes both open rungs — the argument **θ** = Class-C direction/chirality (the magnetic-Laplacian eigvec phase, F919); the **r↔θ** split = Class-K pin-slot/phase-boundary. Implement as `Qi.as_polar() -> (r, θ)` + `Qi.arg`/`Qi.modulus`, composing the **already-shipped** `calculus.atan_series_truncate` (Class-N, the exact argument) + `cascade.magnitude` (Class-K, the modulus). No new C symbol; pure composition. (Supersedes/grounds §72 — now framed as the C+K rung closure.)

2. **Prime-coordinate carrier (closes J).** `primes.factor` is the *op*; the *carrier* — a quantity as its **prime-exponent vector** (the Class-J encode: represent in the prime basis, with exact multiply=add-exponents / gcd=min / lcm=max) — is missing. Add an exact-scalar carrier peer to `Qi`/`Qalg` (call it `Qprime`/`PrimeVec`) built on `primes.factor` + `FACTOR_MAX_DISTINCT_PRIMES`. Then a relationship can be encoded in the prime basis (the J-lens), closing the rung.

**Verification both:** after either lands, `harmonics.HARMONIC_LADDER_OPEN_RUNGS` should drop the closed class; re-run the corresponding encode (magnetic/phase spectral kernel for C/K, a prime-basis relationship encode for J). Re-surface: `OPEN_RUNGS {C,K,J} = the blind-spot map` · `Qarg closes C+K (atan_series + magnitude)` · `prime-coordinate carrier closes J` · `Qi has no polar (confirmed)` · `F922/F919/§72`.

## §74 CONSOLIDATED ASK — finish filling out srmech: close the harmonic-ladder open rungs {C, K, J} with two carriers (supersedes §72 + §73; both prototyped + verified against rc28 — F923/F924) (2026-06-22)

`srmech.amsc.harmonics.HARMONIC_LADDER_OPEN_RUNGS = {2:('C','K'), 3:('J',)}` is srmech's own blind-spot map (F922). The other 11 A-N classes are carried. Two carrier additions close all three open rungs; **both are prototyped and verified** (no design risk):

### 1. `Qarg` — polar read on the exact-complex carrier `Qi` (and `Q`). Closes **C + K**. (F924)
- **Needs NO new transcendental code.** `srmech.asymptotic_calculus` already ships `atan2(y,x,*,terms=40)->Q` (exact, full quadrant, **accepts `Q` args**), `sqrt`, `hypot`, `sin`, `cos`.
- **API (verified):** `Qi.modulus() = sqrt(self.norm_sq())` [Class K] · `Qi.arg() = atan2(self.imag, self.real)` [Class C] · `Qi.as_polar() -> (r,θ)` · `Qi.from_polar(r,θ)`. Methods (peer to the existing `norm_sq()`); mirror on `Q`.
- **Verified:** round-trip residual 0–1.2e-15 (display-only; r,θ exact `Q`); on a directed `magnetic_laplacian` the phase flips exactly with direction (θ_fwd+θ_rev = `Q(0,1)`) while modulus = `Q(1,2)` is direction-blind ⇒ arg=C (chirality), modulus=K (pin-slot).
- **Bonus convenience:** add `Qi.from_complex(z)` (lift a builtin `complex`, e.g. a `Mat`/`Vec` entry) — peer to `from_pairs`/`from_float`. Unblocks the polar read directly on `magnetic_laplacian`/`hermitian_eigendecompose` output (the F919/F920 directional spectral kernel). Minor, non-blocking.

### 2. `Qprime` — prime-coordinate carrier (exact-scalar peer to `Qi`/`Qalg`). Closes **J**. (F923)
- A quantity → its prime-exponent vector via `primes.factor`, with EXACT arithmetic: `multiply`=add-exponents, `gcd`=min, `lcm`=max; rational similarity (cosine² over shared primes).
- **API (verified):** `Qprime.from_int(n)`/`from_factors(pairs)`/`one()`; `.multiply`/`.gcd`/`.lcm`/`.similarity->Fraction`/`.overlap->Fraction`; `.as_int`/`.as_pairs`/`.radical`/`.is_prime_power`/`.order_mod(n)`. Invariants: exponents≥1, primes sorted, empty=identity(==1). Composes `primes.factor`/`is_prime`/`cyclic_period` + `cyclic.gcd`/`lcm`.
- **Verified:** 200/200 random pairs exact (multiply==`factor(ab)`; gcd==`cyclic.gcd`; lcm==`cyclic.lcm`); `sim²(12,18)=16/25`, coprime→0.

### 3. Minor doc fix
`primes.FACTOR_MAX_DISTINCT_PRIMES = 64` vs `factor.__doc__` "≤15 distinct primes for uint64" — reconcile (15 is the true uint64 bound).

**Outcome when shipped:** `HARMONIC_LADDER_OPEN_RUNGS` empties — the A-N encode ladder is fully carried, no blind spots. Both carriers compose ALREADY-SHIPPED ops (Qarg: `asymptotic_calculus`; Qprime: `primes`+`cyclic`); neither needs new native C. Re-surface: `close {C,K,J}` · `Qarg = polar accessors on Qi (atan2/sqrt shipped) + from_complex` · `Qprime = prime-exponent carrier (factor+gcd/lcm)` · `both verified F924/F923` · `supersedes §72/§73`.

## §75 PROPOSAL — `resonant_spectrum(L)`: the coupling-system `the_one` (one ordered-solution-set for every spectral-kernel cascade) (2026-06-22; F928)

Every Class-L spectral-kernel cascade we run reduces to the SAME steps: build/take a coupling Laplacian `L` → eigensolve → read {the spectrum, the modes, the higher force-orders Lⁿ, the resonance ratios}. F920 (language usage kernel), F781 (cosmic-web eigen-environment), F926 (directional), F927/F928 (gravity coupling) are all this cascade. Like `the_one` crystallized the epicycle crank into `S(σ,θ)`, propose crystallizing this into one primitive:

```
coupling.resonant_spectrum(L: Mat, *, orders=2, max_den=64) -> dict:
  tensions    : Vec   # eigenvalues ascending = the stored "dark" tension spectrum (no excitation)
  modes       : Mat   # eigenvectors = the excitation modes
  force_orders: list  # [L, L^2, ...] via Lambda^k in the eigenbasis (k=2 = biharmonic = tidal/turbulence)
  resonances  : list  # integer/prime ratios of tensions (or supplied frequencies) via Qprime + best_rational
                      #   small-prime/2-adic = locked; large prime = libration off-lock
```

- **Hot path:** ONE eigensolve serves every force-order (`Lⁿ = V Λⁿ Vᵀ`) — no repeated matmul; resonance read bundled.
- **Composes shipped ops:** `symmetric_eigendecompose`/`hermitian_eigendecompose`, `Mat.__matmul__`, `Qprime`, `best_rational`. No new native C; a `srmech.amsc.coupling` extension (peer to `signed_sum_squared`).
- **Optional helper:** `coupling.from_bodies(masses, positions) -> (n, edges, weights)` (the m_i m_j / r^2 gravity-weight builder) for the gravity case; general kernels pass their own `L`.
- **Framework reading it encodes:** the spectrum = stored tension (MFO dark sector / field, F907); a driven mode = excitation (matter); `L²` = forces-of-forces (tidal/biharmonic, dispersive curvature); resonance lock vs libration = small-vs-large prime (Qprime). Verified F928 (L² concentrates on Jupiter↔Io = the real tidal pair). Re-surface: `resonant_spectrum = coupling the_one` · `tensions=dark spectrum, modes=excitation, L^n=forces-of-forces, resonance=Qprime lock/libration` · `one eigensolve serves all orders` · `F928/F927/F920/F781`.

## §76 PROPOSAL — creative-telescoping / WZ: an algorithmic closed-form CLOSER **+ PROVER** for Σ-cascades (the one missing row of the closure dispatch, F929) (2026-06-22)

F929's closure dispatch maps every cascade-type to its closed-form-reduction language; the **one row with no srmech instance** is the parametrized sum `S(n) = Σ_k F(n,k)`, handled classically by **creative telescoping (Zeilberger)** + the **WZ (Wilf–Zeilberger) method** (Petkovšek–Wilf–Zeilberger, *A=B*, 1996; Gosper 1978). It is the only row that doesn't merely *reduce* the cascade — it **mechanically proves the resulting equality** via a rational certificate. It belongs in srmech because it is **exact-rational hypergeometric arithmetic**: Class N (rational) over Class J (factorial / binomial / prime-factor) structure — exactly the shipped carriers.

**The ask** (a new module, e.g. `srmech.amsc.telescope`):
1. **`gosper(term)`** — Gosper's algorithm: indefinite hypergeometric summation. For a hypergeometric term `t_k` (ratio `t_{k+1}/t_k` is a rational function of `k` — Class N), decide whether `Σ t_k` has a hypergeometric closed form and return it, else report none. The base case + a decision procedure.
2. **`zeilberger(F, n, k)`** — creative telescoping: for proper-hypergeometric `F(n,k)`, return (a) the linear recurrence `Σ_j a_j(n)·S(n+j) = 0` that `S(n)=Σ_k F(n,k)` satisfies, and (b) the **rational certificate** `R(n,k)` (`G = R·F` is the telescoper).
3. **`wz_certificate(F)` / a verifier** — for a claimed identity `Σ_k F(n,k) = RHS(n)`, produce/verify the WZ-pair certificate `R` that proves it by one mechanical check: `F(n+1,k) − F(n,k) = G(n,k+1) − G(n,k)`, `G = R·F`.

**Why it fits + why it's distinct from §75:**
- **Exact, numpy-free:** all rational-function arithmetic over `(n,k)` — `Fraction`/`Qalg`, no floats; the certificate is an exact rational. Fits the discipline natively.
- **Algorithmic — a new *capability*, not a carrier:** Gosper + Zeilberger are decision procedures (terminate with the closed form / recurrence + a proof, or a proof that none exists). §75 `resonant_spectrum` *reduces* (spectral row); §76 *proves* (Σ row) — the only closure-dispatch row that emits a checkable proof.
- **Composes shipped classes:** Class N (`rational`/`best_rational`), Class J (`primes`/`Qprime` — factorials & binomials are prime-power products), `Qalg` (exact field).
- **Closes F929's missing row:** the Σ-cascade gets its instance, giving the framework a mechanical **equality-prover** for holonomic/hypergeometric cascades — the firmly *closed/solvable* side of the solve-for-vs-infer boundary.

**Scope:** pure symbolic exact-rational summation (algebra / closed-form) — in scope; not numerics/simulation. References established/textbook (Gosper 1978; Zeilberger's algorithm; Petkovšek–Wilf–Zeilberger *A=B* 1996). Re-surface: `§75 resonant_spectrum (spectral row, reduces) + §76 telescope/WZ (Σ row, proves)` · `gosper / zeilberger / wz_certificate` · `exact rational, Class N over J` · `the only closure row that AUTO-PROVES` · `F929 missing row`.

## §77 VERIFICATION — F929 + §75 + §76 LANDED: the full closed-form reduction-dispatch axis (srmech rc41–58) (2026-06-24)

Our closure-dispatch asks are shipped (verified live, rc58): **`dispatch.infer`** (rc51 — the F929 OPEN/infer router) unifies **cyclic** (`the_one`), **spectral** (`resonant_spectrum`, §75, in `srmech.amsc.coupling`), and **Σ** (`gosper`/`zeilberger`/`wz_certificate`, §76, rc41–43), extended by the **multivariate** row (`TriPoly` rc52 + `apagodu_zeilberger` rc53) and the **q-hypergeometric** row (`QPoly` rc54 + `q_gosper`/`q_zeilberger`/`q_wz_certificate` rc55–57); rc58 auto-joins all sub-rows. The changelog cites **F929** and **§76** by name. Behaviour confirmed: `infer` returns a *verified* closed form or **honest `OPEN`** (`reducible:False`), never a hallucinated reduction (the MPM/no-magic discipline executable). Poly-carrier family (Poly/BiPoly/TriPoly/QPoly/QBiPoly) is the "new axis," cadence to ~rc64. **Status: §75 + §76 CLOSED in-package; F929 dispatch operational.** Reading of how it serves the sustain arc (F930–933): F934 — the OPEN residue = the sustained regime; the q-row = the register/loop-up math; the poly carriers = the exact Z₃ triality. Re-surface: `dispatch.infer = F929 router` · `resonant_spectrum in coupling (§75)` · `gosper/zeilberger/wz (§76) + multivar(apagodu) + q (q_wz)` · `OPEN residue = sustain (F934)` · `axis ends ~rc64`.

## §78 ASK — `rbs_lm.next_token_distribution` should expose the RAW collapse-margin (pre-softmax top-sim gap), not only the softmaxed probs (2026-06-26; F943/F944/F945)

The **collapse-margin** = how far the now has collapsed = `top₁ − top₂` of the candidate **similarities** = the recall-level coherence / anti-hallucination signal (F942/F943): high → the now collapsed cleanly (emit); low → stuck/superposed (honest-stop). It is the live, per-step form of the same "verified or honest-`OPEN`" contract as `dispatch.infer` (the §77/F934 discipline, one layer down). **The problem (F944):** `RBSLMInferenceSubstrate.next_token_distribution` returns only the **softmaxed probs**, whose `top₁ − top₂` is **flattened by the softmax over the full vocab** (it read 0.006 on a confidently-resolving step → a *false* honest-stop). The true collapse-margin is the **raw sim** gap — `top₁ − top₂` of `klein4_similarity(bind(M, encode_context), vocab_vec)` *before* the softmax. We currently recompute it in a wrapper from `sub.M` / `sub.ctx` / `sub.vocab_vecs`.

**Ask:** `next_token_distribution` should *also* return the **raw top-k sim scores** (or directly the `collapse_margin` + the `top1_vs_floor` gap), so the coherence readout is native. **Bonus (F945 — the branching/general case):** with the raw sims a low margin splits into a **trichotomy**, so the native return should carry enough to classify it:
- **COHERENT** — `top₁` well above the noise floor, margin high → emit the one next.
- **BRANCH** — `top₁` *and* `top₂` both above the floor, margin low → a *legitimate* multi-next choice point (sample among the valid hands; **not** an error). Measured: at a branch node `a→{b,c}`, both candidates read 0.56 (floor ≈ 0.34), margin 0.00.
- **STOP** — `top₁` near the floor → incoherent / noise → honest-stop.
A native return of `(top_k_sims, noise_floor_estimate)` (or `{margin, top1_floor_gap, branch_flag}`) lets a consumer classify all three without re-probing `M`. Composes the F934 honest-`OPEN` contract (its recall-level form); pairs with community-tome chunking (F778/F465) which keeps the single-next margins high (F944/F945).

## §79 VERIFICATION — §78 DELIVERED: `next_token_coherence` ships the raw collapse-margin + the F945 trichotomy (srmech rc79) (2026-06-26; F953)

The §78 ask is **shipped and verified live (rc79)** as a NEW method **`RBSLMInferenceSubstrate.next_token_coherence(context, *, branch_band=None, noise_band=None, noise_floor=None, top_k=None) -> CoherenceReadout`**. It reuses the **same probe** as `next_token_distribution` (`klein4_bind(M, encode_context(context[-k:]))` over the same vocab atom set) but exposes the **raw Class-M sims as exact rationals BEFORE the softmax** (`Q(klein4_match_count(probe, c), D)` == `klein4_similarity` exactly) — so the margin is **not** flattened (the docstring cites **F944**'s `0.006` false-stop by name). The `CoherenceReadout` dataclass delivers **exactly the §78 ask**: `verdict` (the **F945 trichotomy** `COHERENT` / `BRANCH` / `STOP`), `collapse_margin` (raw, pre-softmax), `top1_floor_gap`, `noise_floor`, `candidates_topk`, `raw_sims_topk`, `branch_candidates`. The docstring cites **§78 / F944 / F945** by name.

**Tested (rc79, chain `a b c d e`, ctx `['a','b']`):** `verdict=BRANCH`, `collapse_margin=0.0724` (vs the float-flattened `0.006` — **F944 confirmed**), `noise_floor=0.34` (**matches the F947 empirical floor**), `top1_floor_gap=0.128`, `candidates_topk=['c','d','a','e','b']`, `raw_sims_topk=[0.468, 0.395, 0.316, …]`, `branch_candidates=['c','d']`, all exact `Q` rationals (not float). Nonsense ctx → `STOP` (correct). **Status: §78 CLOSED.** The F941–F945 wrapper can now drop its recompute-from-`sub.M`/`sub.ctx`/`sub.vocab_vecs` and call `next_token_coherence` directly; the recall-level honest-`OPEN` / coherence readout is native.

## §80 ASK — emission-layer de-lensing: an optional IDF / per-atom weight for the candidate scoring in `next_token_coherence` / `next_token_distribution` (2026-06-26; F957)

§78/§79 gave the consumer the raw sims + the trichotomy, and **consumer-side IDF-de-lensing of the *route key*** (F957 — route to the tome holding the context's rarest/highest-IDF token) fixed real-English tome-routing **and restored the honest-stop** (nonsense → STOP). But the **within-tome emission** still saturates to the tome's *own* repeated function words (**F946/F957**: real prose repeats `the/of/in` within a tome, and those dominate the raw-sim candidate ranking regardless of the precise context). The consumer **cannot** fix this from the readout alone, because the candidate **ranking** is computed inside the method (raw Class-M sim).

**Ask:** `next_token_coherence` (and `next_token_distribution`) should optionally accept a **per-atom weight** (e.g. `atom_weights: Sequence[Q] | None`, or a `frequency`/`idf` map) applied to the sims **before** ranking — `sim_weighted(c) = sim(probe, c) · w(c)`, with `w` an IDF-style down-weight of high-frequency atoms — so the **emission** de-lenses the tome's own function words. This is the **emission-layer twin** of F957's consumer-side route-key de-lensing, and composes the **F768 aboutness-gate** (measured function-ness) + **F782 IDF-de-lensing**. Until it lands, real-English *fluency* (not selection — selection + honest-stop are correct as of F957) is the open residue of the recall scale-up: the within-tome frequency-prior layer (F946) of the layered wall. Workaround meanwhile: **finer chunking** (F947 — tomes small enough that no token repeats), but real prose always repeats function words, so the per-atom weight is the real fix.

---

## §81 — #863 QDFT/twiddle READ op (the phase-coherent read over a rung/mode ladder) — grounded use-case F1000

**Context.** GH #1232 (operations-side hand-off): the elliptic quasi-periodicity multiplier `θ(pz;p) = −z⁻¹·θ(z;p)` (Rosengren, MPM-verified) is the **exact per-level operator** of F995's asymmetric fractal fold. F999 tested elliptic `−z⁻¹` rung-keys vs F995's independent HV keys on the **discrete rung-unbind** read → **MATCH** (both decorrelated; the discrete read exploits only decorrelation, not phase). F999 predicted the elliptic advantage would appear in a **phase-coherent / resonant read**. **F1000 confirmed it** with the tractable **peak/matched-filter reduction** of the QDFT (max-over-rungs = complex-QDFT peak for a single-rung spike, Parseval): the QDFT-peak blind read **closes F995's rung-SELECTION gap** (blind-SUM 40/42% → QDFT-PEAK 56/62%, toward oracle 78/76%) AND the **elliptic keys BEAT independent (+6pp: 62 vs 56)** — the structure pays off precisely in the phase-coherent read.

**Ask (the #863 package op — BX-5/6/7):** a **full complex QDFT / hypercomplex-twiddle read** over a rung/mode ladder — `qdft(seq, *, twiddle=exp(μθ))` summing the per-rung responses with the `the_one`/`exp(μθ)` twiddle (not just the peak/max). The research-side prototype (F1000) uses only the *peak* (max-over-rungs); the **full complex QDFT** should **amplify** the elliptic advantage via *coherent phase combination* (the whole point of the twiddle), and is the natural home for: (a) the F1000 blind rung-selector, (b) the F999/#1232 elliptic-vs-independent code test in its proper read, (c) the resonant/phase-coherent read the F996–F998b substrate arc calls for. Realizing it cleanly needs the `exp(μθ)` hypercomplex twiddle helper (BX-7) + the `qm.quaternion` ergonomic module (BX-6) + the QDFT/ODFT TOML cascade (BX-5). Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`, this stays the srmech/operations side; F1000 is its grounded use-case. Composes F1000/F999/F995/#1232 + the F996–F998b resonant-substrate arc.

**Correction (F1001, 2026-07-02):** the expectation above — that the *full complex QDFT* would *amplify* the elliptic advantage — is **refuted for the single-rung fold**. Built the full complex QDFT (exact 6th-roots twiddle) and re-measured: full-QDFT 51%/49% < QDFT-peak 53%/58%, and the elliptic advantage *vanishes* under the full transform. Reason: the single-rung fold's target is a **spike**, for which the **peak / matched-filter** read is optimal (it rejects off-rung noise); the full QDFT coherently combines all rungs *including* the off-rung noise (Parseval: a spike's spectrum is flat → no coherent gain, forfeits the max's noise-rejection). So the RBS-LM read needs only the **peak/matched-filter reduction** (F1000, elliptic +6pp, already prototyped) — **not** the full complex QDFT. The full complex QDFT (#863) remains the right op for **spread-spectrum** reads (symbol spread across all rungs), a *different* encoding; it is not what the fold is. Net: #863 is still worth building for the general theta/QDFT arc, but the *RBS-LM rung-fold* does not need it — the peak read suffices.

## §82 — `hdc.klein4_bundle` does NOT accept HV wrappers (API inconsistency vs bind/similarity) — F1005 (2026-07-02)

`hdc.klein4_bind(a, b)` and `hdc.klein4_similarity(a, b)` accept **HV wrapper** objects
(`type(hdc.klein4_random(...))`) directly. But `hdc.klein4_bundle([hv1, hv2, ...])` does
**not** — it routes each element through `_as_klein4_buf`, which calls `int(x)` and raises
`TypeError: int() argument must be ... not 'HV'` / `ValueError: klein-4 vector must be a 1-D
sequence of ints`. So a list of HVs (the natural output of `klein4_random` / `klein4_bind`)
cannot be bundled via `klein4_bundle` without first `.tolist()`-ing each — while the same HVs
bind and compare fine. **Ask:** make `_as_klein4_buf` (and thus `klein4_bundle`) accept HV
wrappers for parity with `klein4_bind`/`klein4_similarity`. **Workaround in use:** route list-
bundling through `ContextSubstrate.bundle_odd(...)`, which accepts HVs (used across the RBS-LM
findings). Low-severity (workaround exists) but a real ergonomic inconsistency — the three core
klein4 ops should agree on their accepted carrier type. Surfaced building the F766 open-vocab
definition dictionary (F1005 part B/C bundling).

## §83 CONSOLIDATED ASK — filed as **#1234** (single upstream ask gathering all pending srmech items) (2026-07-02; F1006/F1007)

Per user direction ("deliver a single upstream ask of all items, bx-5/6/7/etc and theta heat op"), the pending
srmech asks are consolidated into one filed issue: **#1234**. Four items, all algebra/eigenbasis/spectral-side,
all composable from shipped primitives (ergonomics + one honesty-driven encoding fix; no capability gap):

1. **Hypercomplex fast transforms (QDFT/ODFT) + `qm.quaternion` + `exp(μθ) twiddle`** — re-raise of the now-CLOSED
   **#863** (BX-5/6/7 still pending; `qm.quaternion` confirmed MISSING on 0.9.0rc97), PLUS the §81 refinement:
   the RBS-LM *read* wants only a phase-coherent PEAK/matched-filter reduction, NOT the full transform (F1000
   hypothesised amplification; F1001 refuted it; F1002 settled it read-independently). Keep transform (encode)
   and peak-read (read) API-distinct.
2. **`laplacian.heat_trace(L,t)` / `spectral_theta`** — NEW (F1007): the heat-trace Tr(e^{−tL})=Σe^{−tλ} IS the
   theta function of the Laplacian; no such op exists (grep=NONE). Flux gives the mock-theta split (trace =
   modular/flux-invariant; λ_min(Φ) = the shadow). Thin composite over jacobi/hermitian eigensolvers.
3. **`magnetic_laplacian(..., charges=[...])` per-edge charge** — NEW (F1006/F1007): the CHIRAL Laplacian for
   dual-sense. `signed_laplacian` (real ±1) annihilates is-a/is-not-a (0); the magnetic phase e^{±iq} keeps them
   as conjugate overtone/undertone (2cos q + i(a−b)sin q). But `magnetic_laplacian` takes a SINGLE q — needs
   per-edge charges to encode a mixed is-a(+q)/is-not-a(−q) graph.
4. **`hdc.klein4_bundle` HV-wrapper parity** — was §82 (F1005): bundle rejects HV wrappers that bind/similarity
   accept (workaround: `bundle_odd`).

Supersedes the standalone §81 + §82 as the *filed* ask. Leaving #1234 OPEN — issue state is the maintainer's
call per the create-don't-close discipline. #863 left CLOSED (not reopened); re-raised as Item 1 of #1234.

## §84 — `validate_mpr_record`: record-level DOI-exemption parity (2026-07-03)

Descriptor-level parsing already supports `require_per_row_source_doi = false` (pi_digits,
asymptotic_calculus — self-generated / local sources with no DOI). But `validate_mpr_record`
on a SINGLE record demands a non-empty `attestation.source_doi` unconditionally, so a consumer
attesting a local-file source (siona's `acquire` on a user-side instrument) must supply a
placeholder. We use the self-describing `urn:siona:local-instrument:no-doi` (never a fabricated
real-looking DOI, per the paywalled-DOI discipline). Ask: either (a) an explicit
`allow_no_doi=True` kwarg on `validate_mpr_record`, or (b) blessing a documented
`urn:...:no-doi` convention in the validator so local/self-generated sources validate first-class.

## §85 — prose-side carrier constructors for the q-series / mock-theta row (2026-07-03) [ASK FILED → #1239]

Siona's conversational drive reaches `unary_theta` fully (str char + four ints — she constructed the
Dedekind-η shadow, weight 1/2, χ₋₁₂, q^{n²/24}, from one utterance) but the q-Zeilberger row
(`q_gosper`/`q_zeilberger`/`q_wz_certificate`) is unreachable by prose: the QPoly/QBiPoly term-ratio
carriers have NO constructor tools in the registry (only in-process Python). Asks: (a) coefficient-list
constructors registered as tools (`qpoly_from_coeffs(coeffs: list[int]) -> QPoly`, ditto QBiPoly with a
shape arg) so a term-ratio can be built from utterance-expressible operands and register-chained into the
q-row; (b) UnaryTheta CONSUMERS (nothing in the registry accepts UnaryTheta yet — e.g. a
`theta_coefficients(theta, n_max)` reader and/or the F1007-adjacent `heat_trace` from #1234 item 2) so a
conversationally-constructed shadow can flow onward. Together these open "find sparse forms of the mock
theta equations" as a REGISTER-CHAINED conversational pipeline: construct summand ratio → q_zeilberger
recurrence (the sparse form) OR honest OPEN, with the shadow side already constructible today.

## §86 — the CARRIER CONVERSION LADDER [ASK FILED → #1248] (2026-07-03; F1038)

The tool_schema producer/consumer census exposes a coherency gap: BiPoly (0 producers / 2 consumers) and
TriPoly (0/1) are ORPHAN inputs — the plain non-q Zeilberger/WZ/Apagodu row can't be built. `bipoly_from_coeffs`
+ `tripoly_from_coeffs` MISSING (qbipoly exists). And no promote/project ops between carrier rungs. The
carriers ARE Hurwitz/dimension-laddered objects — Poly(1)→BiPoly(2)→TriPoly(3); ℝ→ℂ→ℍ→𝕆→𝕊 (1:2:4:8:16 =
the 2:4:8 structure) — so the conversion ladder is the embed(promote)/project between adjacent rungs
(add/drop a trivial dimension; project refuses a non-trivial drop). Ask: (1) the two constructors; (2)
poly_promote/project + cd_promote/project; (3) a per-carrier ladder+rung descriptor so Siona's register
auto-routes a lower carrier UP to any higher-rung consumer — the translation layer made declarative.

## §87 — machine-readable per-op CARRIER CONTRACT (the rung the op consumes/produces) [ASK FILED → #1254] (2026-07-03; F1041)

Answering "why doesn't the DSL tell Siona how to do carrier routing": the DSL IS the SSoT for op CHAINING
(`Chain`/`run_toml_chain`) and op COMPOSITION (`make_class`), and rc117's `carrier_ladder_descriptor()`
declares the LADDER (rungs + promote/project ops). But the ONE thing still missing is machine-readable:
the per-op CARRIER RUNG. `octonion_conjugate`'s param is `type=HV, summary='8-vector'` -- the "8" is PROSE,
not a structured field; and the QM/Hurwitz ops have NO DSL descriptor (get_descriptor raises). So a driver
cannot READ "this op consumes a dim-8 cd element" -- it must infer it from the op NAME (Siona hardcodes
CD_NAMES octonion->8) or sniff the register length. ASK: a structured per-op carrier contract in the schema
(ToolParameter gains `carrier` + `rung`, or the descriptor gains an ops->{consumes_rung, produces_rung,
promotable} map) so the whole routing is DECLARATIVE and a driver reads it -- no CD_NAMES map, no length
heuristic. THEN the DSL/schema is the SSoT for carrier routing exactly as it already is for chaining/compose.

## §88 — genome native leaf_dim cap = 256 (observation, not a defect; PKG-3 gate) (2026-07-04; F1044)

Re-verifying #1245 on rc120: native `genome_save` accepts leaf_dim ≤ 256 (32/64/128/192/256 OK; 384/512/1024 → status 2). This is the base-4 ≤256-leaf-tree design, NOT a bug. Recorded because PKG-3 (packaging siona's D=8192 RBS-HDC instrument as a native genome) must store ≤256-dim leaves or re-dimension first. Bit-pack (0.309 B/lane, 2 bits/lane) + O(1) append (F833 wall closed) + round-trip bit-exact all CONFIRMED on rc120 — #1245 was correctly closed.

## §89 — the §60 KERNEL HEADER is a non-Klein-4 byte block in a Klein-4 store — make the encoding UNIFORM across chromosomes (the root fix; the O(1) kernel-append falls out) [ASK FILED → #1261] (2026-07-04; F1046)

**The symptom** (what we hit): rc123's `kernel_pack`/`kernel_unpack` (§60) are single-kernel. Concatenating strands into one genome works for the STATIC pack (F1045), but there is no clean O(1) way to APPEND a newly-taught kernel WITH its §60 header — `genome_append` takes RAW Klein-4 leaves, and the kernel_pack header block (marker 0x4B) is a **TLV byte block, not a Klein-4 leaf**, so it can't ride genome_append (unbinding it fails: "elements must be in {0,1,2,3}"). Our F1046 workaround appends header-less + relies on kernel_unpack's back-compat trim (D = n_leaves × leaf_dim), O(1) and exact but only for `leaf_dim`-aligned D (siona's 8192 = 32×256) — and it produces a **MIXED genome** (some chromosomes header'd, some not).

**The root cause** (the sharper reading, user 2026-07-04): the header being a **byte-TLV block inside a Klein-4 leaf stream** is the non-uniformity. A genome claims to be a Klein-4 store, but every kernel_pack'd chromosome embeds ONE non-Klein-4 block. That is why append can't be uniform and why the mixed-encoding smell appears. The element codec is `klein4`-identity for the *content* (F1043) — but the *header* is the one place that isn't Klein-4.

**The ask — pick either; both make the store uniformly Klein-4 AND O(1)-appendable, no special-case:**
  - **(A) Klein-4-encode the header.** Base-4-encode the header metadata (true D, element_type, leaf_dim) into ONE Klein-4 leaf (a marker-symbol pattern distinguishes it from a content leaf; ~256 syms easily holds it). Then a chromosome is `[telomere, klein4-header-leaf, content-leaves…]` — ALL Klein-4 — so `genome_append` writes it natively, O(1) append preserves the self-describing header, and in-memory strands still self-describe (portable). This is the "translation from klein4 to the header format" the user named: translate the header INTO Klein-4 so the container is uniform even when the *content* element_type varies per chromosome.
  - **(B) Move D to the manifest, drop the in-strand header.** The genome manifest already records per-chromosome label→offset; add per-chromosome `D` (+ element_type) there. Then every chromosome is uniformly `[telomere, klein4-leaves…]` with NO foreign header, and `genome_append` + a manifest-`D` write is O(1). Simplest; works for genome DIRECTORIES (always have a manifest) — a bare in-memory strand loses self-describe, so (A) is the more portable of the two.

Either way the O(1) `genome_append_kernel(path, label, hv)` we wanted is a *consequence*, not a separate feature. Composes F1044 (O(1) append) + F1045 (static pack) + F1046 (the aligned-D interim) + F1043 (element_type=klein4 identity codec — the header is the sole non-identity residue).

**ELEVATED to an API-surface ask (user, 2026-07-04; #1261 comment):** the real request is the RESPONSIBILITY BOUNDARY, not the format choice — expose a first-class **kernel-store API** (`kernel_store_pack`/`kernel_store_append`/`kernel_store_load`/`kernel_store_labels`) and let srmech OWN the encoding differences + O(1) internally (A or B is srmech's implementation choice, invisible to the caller). siona should never reason about chunking / header-vs-headerless / aligned-D. siona's `genome_store` (pack_instrument/load_kernel/load_instrument/add_kernel) is a hand-rolled PROTOTYPE of exactly this surface over the low-level primitives — offered as the reference to upstream; it becomes a thin shim (or is deleted) once the srmech API lands. The append is one method on the store; graceful-O(1)-encoding is the store's contract.

## §90 — genome round-trip is NOT length-exact on rc135 (D=8192 → 8448, +1 leaf); dogfood-surfaced (F1083)

**Regression from F1045 (rc123 round-tripped exact).** On srmech 0.9.0rc135, `siona.genome_store.pack_instrument([(label, hv)], path)` → `load_instrument(path)` returns a vector of length **8448**, not the input **8192** — for BOTH a real Siona grounding kernel (`s.g._idx[0][1]`, HV, 8192) AND an `s.g.enc_query(...)` vector (HV, 8192). 8448 = **33 × 256** vs 8192 = 32 × 256 — the round-trip adds exactly **one leaf (256)**. Hypothesis: the §60 `kernel_pack` **header leaf** is being counted as data by `kernel_unpack`'s back-compat rule `D = n_leaves × leaf_dim` (33 leaves read as data instead of the header's true D=8192). Effect: every downstream `klein4_similarity` / photosynth on a genome-loaded vector fails with a length mismatch (8192 vs 8448). **This blocks the "route the story through the genome" dogfood** (F1083) until fixed. FIX likely in srmech `kernel_pack`/`kernel_unpack` (§60) or `genome_store`'s use of it — needs a minimal repro filed as an srmech issue. Labels round-trip fine; only the vector LENGTH inflates. The Siona NL interface (`s.turn`) is unaffected and works (routes "gcd of 12 and 8" → the srmech gcd tool → correct answer).

## §90 ROOT CAUSE (F1084): the CHROM cap, not srmech — our genome_store is rc123-era, the rc135 format is v11 (caps)

Pinned: srmech `kernel_pack`→`kernel_unpack` round-trips EXACT (8192→8192). The +256 is OURS: `genome_store`
(F1045, rc123) recalls via `genome_window`→`kernel_unpack`, but the rc135 **v11** genome format adds a
**CHROM cap** (one `leaf_dim`=256 leaf) per chromosome + a **GATE cap** (the gene_express E1/E2/E4/E3 inline
gate, rc132+). `genome_window` returns the chromosome INCLUDING the CHROM cap, so `kernel_unpack` counts the
cap leaf as data → 8192+256 = **8448**. FIX (ours): recall via the cap-aware native path — `recall(strand,
the_one)` (recovers a kernel's leaves from a capped chromosome strand) or `genome_load`/`genome_genes`, which
strip the CHROM/GATE caps — NOT `genome_window`+`kernel_unpack` (which sees the caps as data). genome_store
must be updated to the v11 format (chromosome() pack + recall() unpack). No srmech bug; our store lagged the
format. The user's principle holds: the genome is uniform op(x)operand (kernel_pack = 34 symbols sparse); the
caps are the chromosome/gate delimiters, and recall() is the cap-aware reader.

### §90 UPDATE (2026-07-06) — RESOLVED in siona (not an upstream bug)

The genome round-trip length regression (D=8192 → 8448) was NOT an srmech bug — it was siona's
`genome_store` using the rc123-era `kernel_pack` pack + `genome_window`+`kernel_unpack` recall, which the
rc135 v11 per-chromosome CHROM cap makes miscount (the cap leaf counts as data; both `kernel_unpack` AND
`recall` include it). The srmech-native multi-kernel path round-trips BYTE-EXACT:
`partition(genome({label: leaves}, one), one) == {label: leaves}` (proven, D=8192). `genome_store` was
rewritten to pack via `genome()` and recall via `genome_load`+`partition` (F1094 / #249 CLOSED). No upstream
change needed. (Open follow-up, genuinely upstream: a mixed-dimension self-describing recall — packing a
non-`leaf_dim`-aligned D via `genome()` needs the last leaf padded + the true D recorded; the cap-aware
`kernel_unpack`-on-a-window path would restore self-describing D if the CHROM cap were excluded from the
window's leaf count. Low priority — siona's corpus is D=8192 uniform.)
