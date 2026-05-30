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

---

*Maintained alongside the R-RBS-LM rolling PR. New entries land at the
top of the relevant arc section. Per upstream-as-research-notes
discipline, this file is the canonical record of catalog-gap requests
from the RBS-LM research subtree.*
