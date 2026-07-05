"""rc131 (UPSTREAM §131, #731) — the THRESHOLD REGULATORY GATE-TYPE (E4): a linear-threshold
(perceptron) gate ``Σᵢ weightᵢ·bit_i(cell_state) ≥ threshold`` as a THIRD gate-type in the
E1(klein4_mask, 0x67) / E2(boolean_dnf, 0x62) dispatch family.

rc129 (E1) gave ``gene_express`` a Klein-4 activator/repressor two-mask (ONE conjunctive clause);
rc130 (E2) added arbitrary boolean logic as a DNF (an OR of AND-clauses). E4 adds the
LINEAR-THRESHOLD gate: a per-condition SIGNED integer WEIGHT vector + an integer THRESHOLD; the
gene expresses iff the exact integer weighted sum of the PRESENT conditions ≥ the threshold.

WHY E4 IS GENUINELY DISTINCT FROM E2 (not redundant):
  E2's DNF is functionally complete, so it CAN represent any boolean function — but a
  linear-threshold function (e.g. MAJORITY-of-n) needs an EXPONENTIALLY-large DNF: the minimal
  DNF for MAJORITY-of-n has C(n, ⌈n/2⌉) clauses. E4 captures COMPACTLY (one weight vector) what
  E2 cannot (linear-threshold functions ⊄ small-DNF). test_majority_e4_one_gene_vs_e2_exponential
  makes this concrete: MAJORITY-of-5 is ONE E4 gene (5 weights) but needs C(5,3)=10 E2 clauses.

THE MECHANIC:
  * gate_type = threshold (E4/rc131, NEW) → a 0x77 ('w' weighted) cap carrying [weights, θ];
    express iff Σᵢ weightᵢ·bit_i(cell_state) ≥ θ.
  * SIGNED weights allowed (an inhibitory input — a repressive TF — is a NEGATIVE weight).
  * the decision is the SIGN of (Σ − θ): a Class-K sign-branch, NEVER abs(). INCLUSIVE boundary
    (Σ==θ expresses; Σ==θ−1 doesn't).
  * exact Class-I/N integer arithmetic; NO float.

Attested biology (ONE FACET — genes have other regulation too; NOT a reduction):
  * Alberts et al., *Molecular Biology of the Cell* 4th ed. (Garland Science, 2002), "Drosophila
    and the Molecular Genetics of Pattern Formation: Genesis of the Body Plan", NCBI Bookshelf
    NBK26906 (OA-verified first-hand): the Dorsal morphogen "turns on or off the expression of
    different sets of genes depending on its concentration" — a graded morphogen crossing distinct
    THRESHOLD concentrations sets which genes express (the additive weighted-dose-sum ≥ threshold
    model). The operon exemplar stays Jacob & Monod (1961) (the E1 fast path).

Proven here (the ask's DoD):
  1. threshold rule exact — SIGNED (inhibitory) weights + the boundary (Σ==θ expresses, Σ==θ−1
     doesn't);
  2. MAJORITY gate (weights all 1, θ=⌈n/2⌉) — and the E2-can't-do-compactly contrast;
  3. THE FAMILY DISPATCH: E1 / E2 / E4 genes coexist in one chromosome, back-compat;
  4. THE op⊗operand THEOREM: same DNA, different cell_state → different expressed subset;
  5. the READ-TIME FILTER: the strand is byte-identical after gene_express (no mutation);
  6. back-compat: rc130 / rc129 / rc128 / plain genes read + behave IDENTICALLY (byte-identical);
  7. the bare strand SELF-DESCRIBES the weights + threshold (no manifest);
  8. format v9 → v10 (a NEW 0x77 block kind); a v10 genome saves + pages back; pre-rc131 reads
     identically;
  9. Python==C byte-identical (the per-gene threshold decision incl. signed + boundary + majority).

numpy-free; NO abs() (the sum is signed exact Class-I/N; the decision is the SIGN, never abs).
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native
from srmech.amsc.hv import HV


def _one(dim=96):
    return G._default_the_one(dim)


def _leaves(n, dim=96, base=0):
    return [HV.from_sequence([(base + i + k) % 4 for k in range(dim)], sectors=4)
            for i in range(n)]


# condition bits used throughout: a = bit0, b = bit1, c = bit2, d = bit3, e = bit4
A, B, C, D, E = 1 << 0, 1 << 1, 1 << 2, 1 << 3, 1 << 4


def _threshold(weights, theta):
    return {"gate": "threshold", "weights": list(weights), "threshold": theta}


def _popcount(x):
    n = 0
    while x:
        n += x & 1
        x >>= 1
    return n


# ── (1) threshold rule exact — SIGNED weights + the boundary ──────────────────

def test_threshold_rule_exact_positive_weights():
    """A pure positive-weight perceptron: weights=[3,2,1] over (a,b,c), θ=4 → express iff the
    weighted sum of present conditions ≥ 4."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _threshold([3, 2, 1], 4))])

    def on(cs):
        return "g" in [l for l, _ in G.gene_express(strand, one, cs)]

    assert on(A | B) is True       # 3+2 = 5 ≥ 4
    assert on(A) is False          # 3 < 4
    assert on(B | C) is False      # 2+1 = 3 < 4
    assert on(A | C) is True       # 3+1 = 4 ≥ 4 (boundary)
    assert on(0) is False          # 0 < 4


def test_signed_inhibitory_weight():
    """A NEGATIVE weight is an INHIBITORY input (a repressive TF): weights=[10, -10] over (a,b),
    θ=1 → 'a' activates, but 'b' cancels it. abs()-ing the sum would break this (it would treat
    -10 as +10) — the sign is load-bearing (Class-K, never abs)."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _threshold([10, -10], 1))])

    def on(cs):
        return "g" in [l for l, _ in G.gene_express(strand, one, cs)]

    assert on(A) is True           # +10 ≥ 1
    assert on(A | B) is False      # 10 - 10 = 0 < 1 (b INHIBITS a)
    assert on(B) is False          # -10 < 1 (inhibitor alone)
    assert on(0) is False          # 0 < 1


@pytest.mark.parametrize("cs,total", [(0, 0), (A, 5), (B, -3), (A | B, 2), (A | C, 9), (B | C, 1)])
def test_boundary_is_inclusive(cs, total):
    """The boundary is INCLUSIVE: with weights=[5,-3,4] over (a,b,c) and θ set to the exact sum,
    Σ==θ EXPRESSES and Σ==θ−1 does NOT (the Class-K sign of Σ−θ; ≥, not >)."""
    one = _one()
    weights = [5, -3, 4]
    # θ = total → Σ == θ → expresses (≥ is inclusive)
    s_eq = G.chromosome(the_one=one, label="c",
                        genes=[("g", _leaves(1), _threshold(weights, total))])
    assert "g" in [l for l, _ in G.gene_express(s_eq, one, cs)], f"Σ==θ={total} must express"
    # θ = total + 1 → Σ == θ − 1 → does NOT express
    s_hi = G.chromosome(the_one=one, label="c",
                        genes=[("g", _leaves(1), _threshold(weights, total + 1))])
    assert "g" not in [l for l, _ in G.gene_express(s_hi, one, cs)], "Σ==θ−1 must NOT express"


def test_pure_evaluator_matches_hand_computation():
    """The pure evaluator _threshold_expresses is exactly Σ wᵢ·bit_i(cs) ≥ θ."""
    weights = [7, -4, 2, -1]
    for cs in range(16):
        total = sum(w for i, w in enumerate(weights) if (cs >> i) & 1)
        for theta in (total - 1, total, total + 1):
            assert G._threshold_expresses(weights, theta, cs) == (total >= theta)


# ── (2) MAJORITY gate — and the E2-can't-do-compactly contrast ─────────────────

@pytest.mark.parametrize("n", [3, 5, 7])
def test_majority_gate(n):
    """MAJORITY-of-n: all-ones weights + θ = ⌈n/2⌉ → express iff a MAJORITY of the n conditions
    are present. Checked across every popcount."""
    one = _one()
    theta = (n + 1) // 2                                    # ⌈n/2⌉
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("maj", _leaves(1), _threshold([1] * n, theta))])
    for cs in range(1 << n):
        want = _popcount(cs) >= theta
        got = "maj" in [l for l, _ in G.gene_express(strand, one, cs)]
        assert got is want, (n, cs, _popcount(cs), theta)


def test_majority_e4_one_gene_vs_e2_exponential():
    """THE 'E4 ⊄ small-DNF' PROOF made concrete: MAJORITY-of-5 is ONE E4 threshold gene (5
    weights) but its minimal E2 DNF needs C(5,3) = 10 clauses (the OR over all 3-subsets). Both
    express IDENTICALLY across all 32 states — so E4 is a genuine COMPACT capture of what E2 can
    only do at exponential cost, NOT a redundant re-skin of E2."""
    import itertools
    dim = 256                                              # the 10-clause DNF needs a wide leaf
    one = _one(dim=dim)
    n, theta = 5, 3
    # E4: ONE gene, 5 weights.
    s_e4 = G.chromosome(the_one=one, label="c",
                        genes=[("maj", _leaves(1, dim=dim), _threshold([1] * n, theta))])
    # E2: the minimal DNF = OR over every 3-subset (require those 3 present). 10 clauses.
    dnf = [(sum(1 << i for i in combo), 0)
           for combo in itertools.combinations(range(n), theta)]
    assert len(dnf) == 10                                   # C(5,3) = 10 (exponential in general)
    s_e2 = G.chromosome(the_one=one, label="c",
                        genes=[("maj", _leaves(1, dim=dim), {"gate": "boolean", "dnf": dnf})])
    for cs in range(1 << n):
        r4 = "maj" in [l for l, _ in G.gene_express(s_e4, one, cs)]
        r2 = "maj" in [l for l, _ in G.gene_express(s_e2, one, cs)]
        assert r4 == r2 == (_popcount(cs) >= theta), (cs, r4, r2)


# ── (3) THE FAMILY DISPATCH — E1 / E2 / E4 coexist ────────────────────────────

def _family_chromosome(one):
    """One chromosome carrying ALL THREE gate-types over conditions a=bit0, b=bit1, c=bit2:
      E1 klein4_mask : lacZ = (activator=a, repressor=b)              [4-tuple]
      E2 boolean_dnf : xor  = XOR(a,b) = [(a,b),(b,a)]                [dict 'boolean']
      E4 threshold   : dose = weights [2,2,-3], θ=2                   [dict 'threshold']"""
    return G.chromosome(the_one=one, label="cell", genes=[
        ("lacZ", _leaves(1, base=0), A, B),
        ("xor", _leaves(1, base=1), {"gate": "boolean", "dnf": [(A, B), (B, A)]}),
        ("dose", _leaves(1, base=2), _threshold([2, 2, -3], 2)),
    ])


def test_family_dispatch_e1_e2_e4_coexist():
    """E1, E2 and E4 genes coexist in ONE chromosome; gene_express dispatches EACH on its own
    gate-type. The three markers 0x67 / 0x62 / 0x77 all appear."""
    one = _one()
    strand = _family_chromosome(one)
    markers = {G._cap_kind(hv) for hv in strand}
    assert G.REGULATORY_GENE_MARKER in markers             # E1 0x67
    assert G.BOOLEAN_GENE_MARKER in markers                # E2 0x62
    assert G.THRESHOLD_GENE_MARKER in markers              # E4 0x77

    def sub(cs):
        return set(l for l, _ in G.gene_express(strand, one, cs))

    # cs=a: lacZ ON (a present, b absent); xor ON (a xor b); dose = 2 ≥ 2 ON
    assert sub(A) == {"lacZ", "xor", "dose"}
    # cs=a|b: lacZ OFF (b represses); xor OFF (a==b); dose = 2+2 = 4 ≥ 2 ON
    assert sub(A | B) == {"dose"}
    # cs=c: lacZ OFF; xor OFF; dose = -3 < 2 OFF
    assert sub(C) == set()
    # cs=b: lacZ OFF; xor ON; dose = 2 ≥ 2 ON
    assert sub(B) == {"xor", "dose"}


def test_gate_type_self_reported_across_family():
    """Each gene reports its declared gate_type via _gene_gate_type (E1=0, E2=1, E4=2)."""
    one = _one()
    strand = _family_chromosome(one)
    types = {}
    for hv in strand:
        k = G._cap_kind(hv)
        if k in (G.GENE_CAP_MARKER, G.REGULATORY_GENE_MARKER,
                 G.BOOLEAN_GENE_MARKER, G.THRESHOLD_GENE_MARKER):
            _m, label = G._unpack_cap(hv)
            types[label] = G._gene_gate_type(hv)
    assert types == {"lacZ": G.GATE_TYPE_KLEIN4_MASK,
                     "xor": G.GATE_TYPE_BOOLEAN_DNF,
                     "dose": G.GATE_TYPE_THRESHOLD}


# ── (4) THE op⊗operand THEOREM — cell_state modulates the expressed subset ─────

def test_theorem_state_modulates_threshold_subset():
    """Same DNA, different cell_state → different expressed subset, with threshold gates."""
    one = _one()
    strand = _family_chromosome(one)
    assert set(l for l, _ in G.gene_express(strand, one, A)) != \
        set(l for l, _ in G.gene_express(strand, one, C))


# ── (5) the READ-TIME FILTER — the strand is byte-identical after gene_express ─

def test_threshold_gene_express_never_mutates_the_strand():
    """gene_express is a READ — the strand's bytes are IDENTICAL before and after, for every
    cell_state (including threshold 0x77 genes)."""
    one = _one()
    strand = _family_chromosome(one)
    before = [hv.tobytes() for hv in strand]
    for cs in (0, A, B, C, A | B | C, 0xFF, 2**40):
        G.gene_express(strand, one, cs)
    assert before == [hv.tobytes() for hv in strand]


# ── (6) back-compat — rc130 / rc129 / rc128 / plain read + behave IDENTICALLY ──

def test_plain_rc128_rc129_rc130_genes_unchanged_bytes_and_behaviour():
    """A chromosome of plain (2-tuple) + rc128 (3-tuple int) + rc129 (4-tuple) + rc130 (boolean
    dict) genes is BYTE-IDENTICAL under rc131 (no 0x77 marker appears) AND expresses identically
    to rc130 (the klein4_mask / boolean dispatch paths are untouched)."""
    one = _one()
    genes = [("housekeeping", _leaves(1, base=0)),                 # plain (always)
             ("stress", _leaves(1, base=1), 0b011),                # rc128 single-mask
             ("lacZ", _leaves(1, base=2), A, B),                   # rc129 two-mask
             ("xor", _leaves(1, base=3), {"gate": "boolean", "dnf": [(A, B), (B, A)]})]  # rc130
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    # NO threshold-gene marker anywhere (byte-level back-compat)
    assert all(G._cap_kind(hv) != G.THRESHOLD_GENE_MARKER for hv in strand)
    cases = {
        0: ["housekeeping"],
        A: ["housekeeping", "lacZ", "xor"],                        # a present, b absent
        A | B: ["housekeeping", "stress"],                         # stress on; lacZ off (b); xor off
        B: ["housekeeping", "xor"],                                # xor on (b); lacZ off
    }
    for cs, expected in cases.items():
        assert [l for l, _ in G.gene_express(strand, one, cs)] == expected


def test_rc130_boolean_and_rc129_caps_bytes_unchanged_under_rc131():
    """A rc130 boolean cap and a rc129 klein4-mask cap pack to the EXACT same bytes under rc131
    (only a NEW 0x77 marker was added; 0x62 / 0x67 layouts are untouched)."""
    dim = 96
    b_cap = G._pack_boolean_gene("g", [(A, B), (B, A)], dim)
    assert b_cap.tobytes()[0] == G.BOOLEAN_GENE_MARKER            # still 0x62
    r_cap = G._pack_regulatory_gene("lacZ", A, dim, repressor=B)
    assert r_cap.tobytes()[0] == G.REGULATORY_GENE_MARKER         # still 0x67


# ── (7) the bare strand self-describes the weights + threshold ────────────────

def test_bare_strand_self_describes_weights_and_threshold():
    """The chromosome self-describes each threshold gene's weights + threshold by bare-strand SCAN
    (no manifest): a 0x77 cap yields (GATE_TYPE_THRESHOLD, weights, threshold)."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c", genes=[
        ("dose", _leaves(1, base=0), _threshold([5, -3, 4], 2)),
        ("maj", _leaves(1, base=1), _threshold([1, 1, 1, 1, 1], 3)),
    ])
    found = {}
    for hv in strand:
        if G._cap_kind(hv) == G.THRESHOLD_GENE_MARKER:
            _m, label = G._unpack_cap(hv)
            gt, weights, theta = G._threshold_gene_spec(hv)
            found[label] = (gt, weights, theta)
            assert G._gene_gate_type(hv) == G.GATE_TYPE_THRESHOLD
    assert found == {
        "dose": (G.GATE_TYPE_THRESHOLD, [5, -3, 4], 2),
        "maj": (G.GATE_TYPE_THRESHOLD, [1, 1, 1, 1, 1], 3),
    }


def test_signed_weights_roundtrip_extremes():
    """SIGNED int64 extremes round-trip through the cap (two's-complement encode/decode)."""
    dim = 128
    weights = [G._THRESHOLD_I64_MAX, G._THRESHOLD_I64_MIN, -1, 0, 1]
    theta = G._THRESHOLD_I64_MIN
    cap = G._pack_threshold_gene("g", weights, theta, dim)
    gt, got_w, got_t = G._threshold_gene_spec(cap)
    assert (gt, got_w, got_t) == (G.GATE_TYPE_THRESHOLD, weights, theta)


# ── (8) format v9 → v10; a v10 genome saves + pages; pre-rc131 reads identically ─

def test_format_bumped_to_v10():
    assert G.GENOME_FORMAT_VERSION == 11       # rc132 §132 bumped v10->v11 (0x64 graded gene)


def test_threshold_genome_saves_v10_and_pages_back(tmp_path):
    """A genome carrying a threshold gene saves at format_version 10, pages back gate-agnostically,
    and gene_express filters the loaded strand under a cell_state (from disk)."""
    one = _one()
    genes = [("housekeeping", _leaves(1)),
             ("maj", _leaves(1, base=1), _threshold([1, 1, 1], 2))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    p = tmp_path / "g"
    man = G.genome_save(strand, p, one)
    assert man["format_version"] == 11                          # rc132 §132 bumped v10->v11; a v11 writer stamps 11
    paged = G.genome_genes(p, "cell", the_one=one)
    assert [l for l, _ in paged] == ["housekeeping", "maj"]     # gate-agnostic recovery
    s2, o2, _ = G.genome_load(p)
    assert set(l for l, _ in G.gene_express(s2, o2, A | B)) == {"housekeeping", "maj"}  # 2 ≥ 2
    assert set(l for l, _ in G.gene_express(s2, o2, A)) == {"housekeeping"}             # 1 < 2


def test_rebuild_by_scan_recovers_the_threshold(tmp_path):
    """§44: with NO manifest, the strand is the SSoT — rebuild-by-scan reproduces the threshold
    gene and gene_express still filters correctly (the weights + threshold live in the body)."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c", genes=[
        ("dose", _leaves(1), _threshold([3, 2, 1], 4))])
    p = tmp_path / "g"
    G.genome_save(strand, p, one)
    (p / "manifest.json").unlink()                             # drop the derived cache
    s2, o2, _ = G.genome_load(p, the_one=one)
    assert set(l for l, _ in G.gene_express(s2, o2, A | B)) == {"dose"}   # 3+2 = 5 ≥ 4
    assert set(l for l, _ in G.gene_express(s2, o2, A)) == set()          # 3 < 4


# ── (9) guard cases ──────────────────────────────────────────────────────────

def test_threshold_spec_requires_weights_key():
    one = _one()
    with pytest.raises(ValueError, match="weights"):
        G.chromosome(the_one=one, label="c",
                     genes=[("g", _leaves(1), {"gate": "threshold", "threshold": 1})])


def test_threshold_spec_requires_threshold_key():
    one = _one()
    with pytest.raises(ValueError, match="threshold"):
        G.chromosome(the_one=one, label="c",
                     genes=[("g", _leaves(1), {"gate": "threshold", "weights": [1, 2]})])


def test_threshold_weight_must_be_int():
    one = _one()
    with pytest.raises(ValueError, match="exact int"):
        G.chromosome(the_one=one, label="c",
                     genes=[("g", _leaves(1), _threshold([1.5, 2], 1))])


def test_threshold_value_must_fit_int64():
    one = _one()
    with pytest.raises(ValueError, match="int64"):
        G.chromosome(the_one=one, label="c",
                     genes=[("g", _leaves(1), _threshold([1 << 63], 0))])
    with pytest.raises(ValueError, match="int64"):
        G.chromosome(the_one=one, label="c",
                     genes=[("g", _leaves(1), _threshold([1], -(1 << 63) - 1))])


def test_attestation_documented():
    """The morphogen-threshold (§131) + operon (§128/§129) attestations are documented."""
    assert "NBK26906" in G.gene_express.__doc__
    assert "Jacob" in G.gene_express.__doc__ and "Monod" in G.gene_express.__doc__


# ── (10) Python==C byte-identical ─────────────────────────────────────────────

# non-overflowing cases (weights + reachable sums stay well within int64)
_THRESHOLD_CASES = [
    ("dose", [3, 2, 1], 4),
    ("signed", [10, -10, 5], 1),
    ("majority5", [1, 1, 1, 1, 1], 3),
    ("all_negative", [-1, -2, -3], -4),
    ("wide", [1000000, -999999, 500000], 1),
    ("boundary", [5, -3, 4], 6),
    ("empty", [], 0),        # no weights → Σ = 0; expresses iff 0 ≥ θ
    ("empty_hi", [], 1),     # Σ = 0 < 1 → never
]


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("_name,weights,theta", _THRESHOLD_CASES)
@pytest.mark.parametrize("cs", [0, A, B, C, A | B, A | C, B | C, A | B | C,
                                A | B | C | D | E, 0xFF, 2**40])
def test_python_equals_c_threshold_decision(_name, weights, theta, cs):
    """The native per-gene threshold decision (srmech_genome_gene_express, 0x77 branch) is
    BYTE-IDENTICAL to the pure Python _threshold_expresses across signed / boundary / majority /
    wide cases + a grid (incl. the Σ==θ / Σ==θ−1 boundary implicit in the cases)."""
    cap = G._pack_threshold_gene("g", weights, theta, 128)
    total = sum(w for i, w in enumerate(weights) if (cs >> i) & 1)
    expected = total >= theta
    assert _native.genome_gene_express_c(cap.tobytes(), 128, cs) is expected


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("cs", [0, A, B, C, A | B, A | B | C])
def test_python_equals_c_family_subset(cs):
    """gene_express returns the SAME expressed subset via native and forced-pure paths on the
    E1/E2/E4 family chromosome."""
    one = _one()
    strand = _family_chromosome(one)
    native = [l for l, _ in G.gene_express(strand, one, cs)]
    real = _native.has_native_genome
    _native.has_native_genome = lambda: False
    try:
        pure = [l for l, _ in G.gene_express(strand, one, cs)]
    finally:
        _native.has_native_genome = real
    assert native == pure


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
def test_python_equals_c_genome_save_threshold(tmp_path):
    """genome_save writes turns.bin + manifest.json BYTE-IDENTICALLY on a genome carrying a
    threshold gene, native-vs-forced-pure."""
    one = _one()
    strand = G.chromosome(the_one=one, label="cell", genes=[
        ("maj", _leaves(2), _threshold([1, 1, 1, 1, 1], 3))])
    dn = tmp_path / "native"
    G.genome_save(strand, dn, one)
    n_body = (dn / "turns.bin").read_bytes()
    n_man = (dn / "manifest.json").read_bytes()
    real = _native.has_native_genome
    _native.has_native_genome = lambda: False
    try:
        dp = tmp_path / "pure"
        G.genome_save(strand, dp, one)
        p_body = (dp / "turns.bin").read_bytes()
        p_man = (dp / "manifest.json").read_bytes()
    finally:
        _native.has_native_genome = real
    assert n_body == p_body
    assert n_man == p_man


# ── (11) native overflow deferral — the exact pure path takes over ────────────

@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
def test_native_defers_on_int64_overflow_pure_is_exact():
    """When the int64 accumulate would OVERFLOW, the native returns SRMECH_ERR_OVERFLOW (raising
    NativeGenomeError on a direct call) and gene_express falls back to the EXACT pure (bignum)
    path — so the answer is still correct. 3·2^62 overflows int64 but is exactly ≥ 0."""
    one = _one()
    big = 1 << 62
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _threshold([big, big, big], 0))])
    # direct native call raises (it cannot represent the sum exactly in int64) ...
    cap = G._pack_threshold_gene("g", [big, big, big], 0, 128)
    with pytest.raises(_native.NativeGenomeError):
        _native.genome_gene_express_c(cap.tobytes(), 128, A | B | C)
    # ... but gene_express still returns the correct answer via the pure bignum path.
    assert "g" in [l for l, _ in G.gene_express(strand, one, A | B | C)]   # 3·2^62 ≥ 0
    # and a genuinely-negative huge sum stays OFF against a positive θ.
    strand_neg = G.chromosome(the_one=one, label="c",
                              genes=[("g", _leaves(1), _threshold([-big, -big, -big], 1))])
    assert "g" not in [l for l, _ in G.gene_express(strand_neg, one, A | B | C)]  # -3·2^62 < 1
