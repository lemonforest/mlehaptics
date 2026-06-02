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

*Maintained alongside the R-RBS-LM rolling PR. New entries land at the
top of the relevant arc section. Per upstream-as-research-notes
discipline, this file is the canonical record of catalog-gap requests
from the RBS-LM research subtree.*
