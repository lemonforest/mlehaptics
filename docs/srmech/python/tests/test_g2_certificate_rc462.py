"""rc462 (`#T1179`) — the ±G2 monomial claim, gated as a CERTIFICATE.

``g2_membership``'s docstring asserts, of the **2688** monomial elements of
``±G2``, that all 2688 pass both commutators and exactly **1344** — every
``−g`` — fail multiplicativity 64/64. rc461 shipped that sentence with a gate
covering **66** elements and recorded the rest as a live coverage gap, because
the full sweep costs minutes.

**The maintainer's rule for closing it was two-part**: measure the real cost
against a 30-minute CI ceiling, AND ask whether a different mathematical shape
does the same job cheaper — "if an invariant, a generator set, an
orbit-stabiliser count or a character-theoretic identity certifies the same
property, that is the better gate and the enumeration becomes its optional
oracle." Both halves were answered by measurement, on this box, numpy-absent.

**Obligation 1 — the cost, MEASURED.** A ``g2_membership`` call is 0.269 s
warm, and the op already returns ``negated_multiplicativity_failures`` in the
SAME call, so a "2688-element census" was always a **1344-call** census: 361 s
of calls on top of a ~73 s one-off cold start for the τ / S_B companion solve
(``_triality_generators_doubled`` is ``lru_cache``d, so that is paid once per
process, not per call). Against per-job maxima measured over five successful
``srmech-ci.yml`` runs via the Actions API, +361 s puts **three** cells past
30 minutes: ``ubuntu-latest • py3.10`` 27:07 → 33:08, ``windows-latest •
py3.12`` 25:11 → 31:12, ``ubuntu-latest • py3.12`` 24:43 → 30:44. And
``--dist loadfile`` puts a whole file on ONE worker, so it cannot be
parallelised away. **The enumeration does not land as a live gate.**

**Obligation 2 — the cheaper shape, DERIVED then EXECUTED.** The monomial
locus is a GROUP of order

    1344 = 8 · 168 = 2³ · (2³−1)(2³−2)(2³−4) = |AGL(3, 2)|

— 168 = |GL(3, 2)| Fano-preserving index permutations, each carrying exactly
8 admissible sign patterns (the (ℤ/2)³ kernel). ±G2 monomial = 2·1344 = 2688.
Five theorems collapse 1344 calls to 10, and each is EXECUTED here rather than
asserted, with the law named in the assertion message:

* **L1** ``G2 = Aut(𝕆)`` is a GROUP, so ``in_g2`` on a generating set certifies
  every element it generates.
* **L2** ``Ad`` is a homomorphism and the τ- / S_B-centralisers are subgroups,
  so centralising on generators certifies the group.
* **L3** ``Ad(−g) = Ad(g)``, because ``Ad`` factors through
  ``PSO(8) = SO(8)/{±I}`` — the claim ``tool_schema.py`` already makes.
* **L4** for ``h = −g`` with ``g`` an automorphism,
  ``h(x)·h(y) = g(x)·g(y) = g(xy) = −h(xy)``, so ``h`` fails EVERY pair on
  which ``g`` succeeds. "Exactly 1344 fail 64/64" is therefore a THEOREM, not
  a measurement.
* **L5** ``det(−g) = (−1)⁸ det(g) = det(g)`` in dim 8, so the determinant is
  not a discriminator — the reason the op is not named ``is_triality_fixed``.

The chain that makes 10 calls enough: **C3** proves the enumerated locus IS
``⟨g_a, g_b⟩`` (BFS closure, set equality, not sampled); **C2** proves the
enumeration is complete by orbit–stabiliser (168 fibres, every one of size 8,
checked for ALL 168); L1/L2/L3 lift the generator measurements to all 1344;
L4 lifts them to all 1344 negatives.

**Why the certificate is the BETTER gate, not merely the cheaper one.** The
enumeration's own construction predicate — the Fano index condition plus the
sign cocycle — IS the octonion-multiplicativity check restated. Sweeping the
set it built therefore re-derives how it was built. The certificate instead
binds the **shipped op** to the group structure, which is the only
non-redundant content in the claim.

**The enumeration stays in-tree as a falsifier**, env-gated and SKIPPED by
default (``SRMECH_RUN_G2_CENSUS=1``), following the in-tree
``SRMECH_RUN_AZ_HEAVY`` precedent. Deliberately NOT a ``slow`` marker: a
skipped test is still COLLECTED, but a ``-m "not slow"`` deselection would
break the shard-partition invariant two dedicated CI jobs exist to protect.
The variable is not set in any CI job.

⚠️ **A MEASURED CORRECTION carried in this file.** ``_ad_epq_columns`` stores
``Ad(g)`` COLUMN-wise. Read naively as ``A[i][j]``, the executed identity is
therefore ``A(g·h) == A(h)·A(g)``, and ``A(g·h) == A(g)·A(h)`` is **False** —
measured both ways below. That is the storage convention, not a broken
homomorphism: with ``A = M(g)ᵀ``, ``M(gh) = M(g)M(h)`` gives exactly
``A(gh) = A(h)A(g)``. Both spellings are asserted so a future reader cannot
mistake the convention for a defect, or "fix" the working one.

No numpy. No ``abs()``. Exact ℚ / integers throughout.
"""

import itertools
import os
import time

import pytest

from srmech.physics.qm import so8
from srmech.physics.qm.octonion import (
    octonion_mult_table,
    octonion_table_attestation,
)
from srmech.physics.qm.so8 import g2_membership

# ── the two generators, named STRUCTURALLY (index permutation + sign pattern),
#    never by enumeration index and never as inlined matrices. The matrices are
#    always looked up out of the derived locus, so a table move reds C3 with a
#    diagnosable cause rather than silently certifying a different group.
GEN_A_KEY = ((1, 2, 3, 5, 4, 7, 6), (1, 0, 1, 0, 0, 0, 0))
GEN_B_KEY = ((2, 4, 6, 1, 3, 5, 7), (1, 1, 0, 0, 0, 0, 0))

#: |GL(3,2)| — the Fano-plane collineation group; also |PSL(2,7)|.
GL_3_2 = (8 - 1) * (8 - 2) * (8 - 4)
#: |AGL(3,2)| = 2³ · |GL(3,2)| — the closed form the locus size must equal.
AGL_3_2 = 8 * GL_3_2

RECOVERY = (
    "If this reds after an octonion-table or fixture change, the recovery is "
    "to RE-DERIVE the generating pair from the locus (any pair whose BFS "
    "closure has 1344 elements) and re-pin GEN_A_KEY / GEN_B_KEY. It is not a "
    "mystery failure: the generators are enumeration-independent keys, but "
    "they are keys into a table that has a content address."
)


# ══════════════════════════════════════════════════════════════════════════
# FIXTURES — everything DERIVED, nothing inlined.
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def structure_constants():
    """``{(i, j): (k, c)}`` with ``e_i·e_j = c·e_k`` for ``i ≠ j`` in 1..7."""
    table = octonion_mult_table()
    out = {}
    for i in range(1, 8):
        for j in range(1, 8):
            if i == j:
                continue
            v = table[i][j]
            nz = [t for t in range(8) if v[t] != 0]
            assert len(nz) == 1, (i, j, v)
            out[(i, j)] = (nz[0], v[nz[0]])
    return out


@pytest.fixture(scope="module")
def fano_index_perms(structure_constants):
    """Every index permutation of ``1..7`` that preserves the Fano structure."""
    struct = structure_constants
    out = []
    for perm in itertools.permutations(range(1, 8)):
        p = {i + 1: perm[i] for i in range(7)}
        if any(p[k] != struct[(p[i], p[j])][0]
               for (i, j), (k, _c) in struct.items()):
            continue
        out.append(perm)
    return out


@pytest.fixture(scope="module")
def monomial_locus(structure_constants, fano_index_perms):
    """The FULL monomial ``G2`` locus as ``{(perm, signbits): 8×8 matrix}``.

    Built from the Fano + sign-cocycle conditions directly — the same
    construction rc461's 32-element fixture uses, with its ``e₁→e₂→e₃`` filter
    removed, so the 1344 is DERIVED rather than pinned.
    """
    struct = structure_constants
    out = {}
    for perm in fano_index_perms:
        p = {i + 1: perm[i] for i in range(7)}
        for bits in range(128):
            s = {i + 1: (1 if not (bits >> i) & 1 else -1) for i in range(7)}
            if all(c * s[k] == s[i] * s[j] * struct[(p[i], p[j])][1]
                   for (i, j), (k, c) in struct.items()):
                g = [[0] * 8 for _ in range(8)]
                g[0][0] = 1
                for i in range(1, 8):
                    g[p[i]][i] = s[i]
                out[(perm, tuple((bits >> i) & 1 for i in range(7)))] = g
    return out


def _mm8(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(8)) for j in range(8))
                 for i in range(8))


def _mm28(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(28)) for j in range(28)]
            for i in range(28)]


def _t(m):
    return [[m[j][i] for j in range(len(m))] for i in range(len(m))]


def _neg(m):
    return [[-x for x in row] for row in m]


def _identity8():
    return tuple(tuple(1 if i == j else 0 for j in range(8)) for i in range(8))


def _closure(gens, cap=40000):
    """BFS closure of ``gens`` under multiplication, capped."""
    seen = {_identity8()}
    seen.update(gens)
    frontier = list(gens)
    while frontier:
        nxt = []
        for x in frontier:
            for y in gens:
                z = _mm8(x, y)
                if z not in seen:
                    seen.add(z)
                    nxt.append(z)
        frontier = nxt
        if len(seen) > cap:
            return seen
    return seen


@pytest.fixture(scope="module")
def generators(monomial_locus):
    for key in (GEN_A_KEY, GEN_B_KEY):
        assert key in monomial_locus, f"generator key {key} not in locus. {RECOVERY}"
    ga = tuple(tuple(r) for r in monomial_locus[GEN_A_KEY])
    gb = tuple(tuple(r) for r in monomial_locus[GEN_B_KEY])
    return ga, gb


@pytest.fixture(scope="module")
def generating_set(generators):
    """``{g_a, g_b, g_a·g_b, g_a⁻¹, g_b⁻¹}`` — the 5 matrices the shipped op
    is asked about. Inverses are transposes: every element is orthogonal."""
    ga, gb = generators
    return {
        "g_a": [list(r) for r in ga],
        "g_b": [list(r) for r in gb],
        "g_a*g_b": [list(r) for r in _mm8(ga, gb)],
        "g_a^-1": _t([list(r) for r in ga]),
        "g_b^-1": _t([list(r) for r in gb]),
    }


# ══════════════════════════════════════════════════════════════════════════
# C1 — CLOSED FORM. No enumeration at all.
# ══════════════════════════════════════════════════════════════════════════


def test_c1_the_locus_order_is_a_closed_form_not_a_count():
    assert GL_3_2 == 168, GL_3_2
    assert AGL_3_2 == 1344, AGL_3_2
    assert 2 * AGL_3_2 == 2688
    # the two factors are the two structures, named
    assert AGL_3_2 == 8 * 168          # (ℤ/2)³ sign kernel × Fano collineations
    assert GL_3_2 == 7 * 6 * 4         # |GL(3,2)| as the standard product


# ══════════════════════════════════════════════════════════════════════════
# C2 — ORBIT–STABILISER. The enumeration is complete because every fibre has
# the same size, checked for ALL 168 — not sampled.
# ══════════════════════════════════════════════════════════════════════════


def test_c2_orbit_stabiliser_every_fibre_is_exactly_eight(
        monomial_locus, fano_index_perms):
    assert len(fano_index_perms) == GL_3_2, (
        f"{len(fano_index_perms)} Fano-preserving index permutations, "
        f"expected |GL(3,2)| = {GL_3_2}. {RECOVERY}")
    assert len(monomial_locus) == AGL_3_2, len(monomial_locus)
    fibres = {}
    for perm, _bits in monomial_locus:
        fibres[perm] = fibres.get(perm, 0) + 1
    assert len(fibres) == GL_3_2, len(fibres)
    # ALL 168, not a sample — this is the orbit–stabiliser claim itself
    assert set(fibres.values()) == {8}, sorted(set(fibres.values()))
    assert sum(fibres.values()) == AGL_3_2
    # the matrices are distinct as matrices, so the key is faithful
    assert len({tuple(tuple(r) for r in g) for g in monomial_locus.values()}) \
        == AGL_3_2


def test_c2_the_locus_is_bound_to_the_octonion_table_it_was_built_from(
        generating_set):
    """The certificate's operand and the shipped op's table are the SAME table.

    Without this, "re-derive the generators" is a mystery instruction; with it,
    a red here names the cause.
    """
    addr = octonion_table_attestation()["attestation"]["response_sha256"]
    assert len(addr) == 64
    assert g2_membership(generating_set["g_a"])["table_sha256"] == addr


# ══════════════════════════════════════════════════════════════════════════
# C3 — THE GROUP. Two generators close to exactly the enumerated set.
# This is what makes L1/L2/L3 apply to all 1344.
# ══════════════════════════════════════════════════════════════════════════


def test_c3_two_generators_close_to_exactly_the_enumerated_locus(
        generators, monomial_locus):
    ga, gb = generators
    closed = _closure([ga, gb])
    assert len(closed) == AGL_3_2, (
        f"⟨g_a, g_b⟩ has {len(closed)} elements, not {AGL_3_2}. {RECOVERY}")
    locus_set = {tuple(tuple(r) for r in g) for g in monomial_locus.values()}
    assert closed == locus_set, (
        "the generated group and the enumerated locus differ as SETS — "
        f"{len(closed - locus_set)} generated-not-enumerated, "
        f"{len(locus_set - closed)} enumerated-not-generated. {RECOVERY}")


def test_c3_fault_one_generator_alone_does_not_close(generators):
    """FAULT INJECTION. Without this, "the closure is 1344" could be an
    instrument that always answers 1344."""
    ga, gb = generators
    assert len(_closure([ga])) == 2, len(_closure([ga]))
    assert len(_closure([gb])) == 3, len(_closure([gb]))


def test_c3_fault_dropping_the_sign_law_inflates_the_locus(fano_index_perms):
    """FAULT INJECTION. The sign cocycle is load-bearing: without it the
    candidate set is 168 × 128 = 21504, sixteen times too large."""
    assert len(fano_index_perms) * 128 == 21504
    assert 21504 == 16 * AGL_3_2


# ══════════════════════════════════════════════════════════════════════════
# L1–L5 — the theorems, EXECUTED, each with its law in the message.
# ══════════════════════════════════════════════════════════════════════════


def test_l1_in_g2_holds_on_a_generating_set_so_it_holds_on_the_group(
        generating_set):
    """L1: ``Aut(𝕆)`` is a GROUP. 10 calls, not 1344."""
    for name, m in generating_set.items():
        r = g2_membership(m)
        assert r["in_g2"] is True, (
            f"L1: {name} must be an octonion automorphism for the group "
            f"argument to certify all {AGL_3_2}; got "
            f"{r['multiplicativity_failures']} failures")
        assert r["multiplicativity_failures"] == 0, name
        assert r["center_coset"] == "G2", name
        assert r["centralizes_tau"] is True, name
        assert r["centralizes_swap"] is True, name
        assert r["induced_outer_class"] == "inner", name


def test_l2_ad_is_a_homomorphism_executed_in_both_spellings(generators):
    """L2: ``Ad(gh) = Ad(g)Ad(h)``, so the τ-centraliser is a SUBGROUP.

    ⚠️ ``_ad_epq_columns`` stores ``Ad`` COLUMN-wise, so read as ``A[i][j]``
    the identity that HOLDS is ``A(gh) == A(h)·A(g)`` and the row-major
    spelling is FALSE. Both are asserted, so the convention cannot be mistaken
    for a defect — and so nobody "fixes" the working one.
    """
    ga, gb = generators
    A = so8._ad_epq_columns([list(r) for r in ga])
    B = so8._ad_epq_columns([list(r) for r in gb])
    AB = so8._ad_epq_columns([list(r) for r in _mm8(ga, gb)])
    assert len(A) == 28 and len(A[0]) == 28
    assert AB == _mm28(B, A), (
        "L2: Ad(g·h) must equal Ad(h)·Ad(g) in the COLUMN storage "
        "_ad_epq_columns uses — the homomorphism, transposed")
    assert AB != _mm28(A, B), (
        "L2 convention control: the row-major product must NOT match, or the "
        "storage convention has changed and the assertion above is vacuous")
    # and the untransposed reading IS the homomorphism
    assert _t(AB) == _mm28(_t(A), _t(B)), "L2: M(gh) = M(g)·M(h)"


def test_l2_centralising_on_generators_certifies_the_group(generators):
    """The subgroup argument, executed on the residuals the op reads."""
    ga, gb = generators
    for name, g in (("g_a", ga), ("g_b", gb), ("g_a*g_b", _mm8(ga, gb))):
        cols = so8._ad_epq_columns([list(r) for r in g])
        tau_r, swap_r = so8._ad_center_residuals(cols)
        assert (tau_r, swap_r) == (0, 0), (
            f"L2: {name} must centralise both generators; the centraliser is "
            f"a SUBGROUP, which is what lifts this to all {AGL_3_2}")


def test_l3_ad_of_the_negative_is_ad_because_ad_factors_through_pso8(
        generators):
    """L3: ``Ad(−g) = Ad(g)``. This is why the commutators CANNOT separate the
    two cosets, and why the census's "all 2688 pass" needs only 1344 of them
    examined — in fact only the generators."""
    ga, gb = generators
    for name, g in (("g_a", ga), ("g_b", gb)):
        pos = so8._ad_epq_columns([list(r) for r in g])
        neg = so8._ad_epq_columns(_neg([list(r) for r in g]))
        assert neg == pos, (
            f"L3: Ad({name}) and Ad(−{name}) must be EQUAL — Ad factors "
            f"through PSO(8) = SO(8)/{{±I}}")
        assert so8._ad_center_residuals(neg) == (0, 0)


def test_l4_the_sign_law_makes_1344_failing_64_of_64_a_theorem(generating_set):
    """L4: for ``h = −g`` with ``g ∈ Aut(𝕆)``,
    ``h(x)·h(y) = g(x)·g(y) = g(xy) = −h(xy)``, and ``g(xy) ≠ 0``, so ``h``
    fails EVERY one of the 64 basis pairs. "Exactly 1344 fail 64/64" is a
    consequence of "all 1344 are in G2", not an independent measurement."""
    mf = so8._octonion_multiplicativity_failures
    for name, m in generating_set.items():
        assert mf(m) == 0, name
        assert mf(_neg(m)) == 64, (
            f"L4: −{name} must fail ALL 64 pairs — sign is quadratic on the "
            f"left and linear on the right, so no pair can survive")
        # and the op reports the same number without a second call
        assert g2_membership(m)["negated_multiplicativity_failures"] == 64, name


def test_l5_the_determinant_is_not_a_discriminator_in_dimension_eight(
        generating_set):
    """L5: ``det(−g) = (−1)⁸ det(g) = det(g)``. The reason the op is called
    ``g2_membership`` and not ``is_triality_fixed``."""
    for name, m in generating_set.items():
        assert g2_membership(m)["determinant"] == 1, name
        assert g2_membership(_neg(m))["determinant"] == 1, (
            f"L5: det(−{name}) must equal det({name}) in even dimension")


def test_the_negatives_are_certified_as_minus_g2_not_as_automorphisms(
        generating_set):
    """The half of the claim the commutators cannot see, on the generators."""
    for name, m in generating_set.items():
        r = g2_membership(_neg(m))
        assert r["fixed_mod_center"] is True, name     # ← "fixed" would lie
        assert r["in_g2"] is False, name
        assert r["multiplicativity_failures"] == 64, name
        assert r["center_coset"] == "minus_G2", (
            f"the coset name for a negative is the string 'minus_G2'; "
            f"got {r['center_coset']!r}")


def test_fault_an_off_locus_signed_permutation_is_not_in_g2():
    """FAULT INJECTION. A monomial orthogonal matrix whose index permutation
    does NOT preserve the Fano structure must be rejected — otherwise the
    certificate would pass on any monomial matrix at all."""
    off = [[0] * 8 for _ in range(8)]
    off[0][0] = 1
    for i in range(1, 8):
        off[(i % 7) + 1][i] = 1
    r = g2_membership(off)
    assert r["in_g2"] is False
    assert r["multiplicativity_failures"] > 0, r["multiplicativity_failures"]
    assert r["center_coset"] is None


# ══════════════════════════════════════════════════════════════════════════
# THE ORACLE — the 1344-call enumeration, kept in-tree and FALSIFIABLE.
# SKIPPED by default; not a `slow` marker (a deselection filter would break the
# shard-partition invariant two CI jobs exist to protect). Not set in any CI job.
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(
    os.environ.get("SRMECH_RUN_G2_CENSUS") != "1",
    reason="the full ±G2 census is 1344 g2_membership calls (~361 s measured, "
           "plus a ~73 s cold companion solve) and breaches the 30-minute CI "
           "ceiling in three cells; set SRMECH_RUN_G2_CENSUS=1 to run it as "
           "the certificate's falsifier")
def test_oracle_the_full_2688_element_census(monomial_locus):
    """The enumeration the certificate replaces, retained so the certificate
    stays falsifiable rather than merely cheaper."""
    started = time.perf_counter()
    in_g2 = 0
    neg_64 = 0
    both_commutators = 0
    for g in monomial_locus.values():
        r = g2_membership(g)
        if r["in_g2"]:
            in_g2 += 1
        if r["negated_multiplicativity_failures"] == 64:
            neg_64 += 1
        if r["centralizes_tau"] and r["centralizes_swap"]:
            both_commutators += 1
        rn = g2_membership(_neg(g))
        assert rn["centralizes_tau"] and rn["centralizes_swap"]
        assert rn["in_g2"] is False
        assert rn["center_coset"] == "minus_G2"
    assert in_g2 == AGL_3_2
    assert neg_64 == AGL_3_2
    assert both_commutators == AGL_3_2
    print(f"\n±G2 census: 2*{AGL_3_2} elements in "
          f"{time.perf_counter() - started:.1f}s")
