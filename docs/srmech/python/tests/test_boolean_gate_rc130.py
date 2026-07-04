"""rc130 (UPSTREAM §130, #730) — the BOOLEAN REGULATORY GATE-TYPE (E2): arbitrary boolean
regulatory logic (AND/OR/NOT/XOR over the condition bits) as a GATE-TYPE in a dispatch family,
with rc129's Klein-4 activator/repressor mask (E1) kept as the fast common case.

rc128 gave ``gene_express`` an all-activator AND-mask; rc129 (E1) enriched it to a Klein-4
activator/repressor TWO-mask — still ONE conjunctive clause. E2 adds the GENERAL case: an
arbitrary boolean function over the condition bits, encoded as a DNF (disjunctive normal form —
an OR of ``(require-present, require-absent)`` AND-clauses). The gene expresses iff ANY clause
matches. DNF is functionally complete, so ANY boolean function is representable.

THE GATE-TYPE DISPATCH FAMILY (E1 ⊂ E2 — E1 is NOT replaced, it stays the fast path):
  * gate_type = klein4_mask (E1/rc129) → the 0x47/0x67 cap + the (cs & act)==act AND (cs & rep)==0
    rule. UNCHANGED — the compact fast common case.
  * gate_type = boolean (E2/rc130, NEW) → a 0x62 cap carrying a DNF; express iff ANY clause
    matches. The general escape hatch.
E1 ⊂ E2: the klein4_mask (activator, repressor) two-mask IS exactly a 1-CLAUSE DNF.

Attested biology (ONE FACET — genes have other regulation too; NOT a reduction):
  * Alberts et al., *Molecular Biology of the Cell* 4th ed. (Garland Science, 2002), "How
    Genetic Switches Work", NCBI Bookshelf NBK26872: the *Drosophila eve* gene is regulated by
    combinatorial controls — a COMBINATION of gene regulatory proteins, not a single one, sets
    expression (OA-verified first-hand). The activator/repressor operon exemplar stays Jacob &
    Monod (1961), *J Mol Biol* 3:318-356 (the E1 klein4_mask fast path).

Proven here (the ask's DoD):
  1. boolean logic exact — AND (E1 recovered as a 1-clause DNF), OR (2-clause), NOT (repressor),
     XOR (2-clause: (a & ¬b) OR (¬a & b));
  2. E1-as-1-term-DNF cross-check (a boolean gene == the rc129 klein4_mask gene, identical);
  3. THE LAC-OPERON via a 1-term DNF (cross-checked identical to rc129);
  4. THE op⊗operand THEOREM: same DNA, different cell_state → different expressed subset;
  5. the READ-TIME FILTER: the strand is byte-identical after gene_express (no mutation);
  6. back-compat: rc129 / rc128 / plain genes read + behave IDENTICALLY (byte-identical too);
  7. the bare strand SELF-DESCRIBES the gate_type + DNF (no manifest);
  8. format v8 → v9 (a NEW 0x62 block kind); a v9 genome saves + pages back; pre-rc130 reads
     identically;
  9. Python==C byte-identical (the per-gene DNF decision across AND/OR/NOT/XOR + a grid).

numpy-free; no abs() (the masks / cell_state are exact Class-I bitwise integers, never negated).
"""
from __future__ import annotations

import pytest

from srmech.amsc import genome as G
from srmech.amsc import _native
from srmech.amsc.hv import HV


def _one(dim=64):
    return G._default_the_one(dim)


def _leaves(n, dim=64, base=0):
    return [HV.from_sequence([(base + i + k) % 4 for k in range(dim)], sectors=4)
            for i in range(n)]


# condition bits used throughout: a = bit0, b = bit1, c = bit2
A, B, C = 0b001, 0b010, 0b100


def _boolean(dnf):
    return {"gate": "boolean", "dnf": dnf}


# ── (1) boolean logic exact — AND / OR / NOT / XOR ────────────────────────────

def _logic_chromosome(one):
    """One boolean gene per gate, over conditions a=bit0, b=bit1:
      AND(a,b) = 1-clause [(a|b, 0)]        (= E1 recovered as a 1-clause DNF)
      OR(a,b)  = 2-clause [(a,0),(b,0)]
      NOT(a)   = 1-clause [(0,a)]           (a repressor)
      XOR(a,b) = 2-clause [(a,b),(b,a)]     ((a & ¬b) OR (¬a & b))"""
    genes = [("AND", _leaves(1, base=0), _boolean([(A | B, 0)])),
             ("OR",  _leaves(1, base=1), _boolean([(A, 0), (B, 0)])),
             ("NOT", _leaves(1, base=2), _boolean([(0, A)])),
             ("XOR", _leaves(1, base=3), _boolean([(A, B), (B, A)]))]
    return G.chromosome(the_one=one, label="logic", genes=genes)


@pytest.mark.parametrize("cell_state", [0b00, 0b01, 0b10, 0b11])
def test_boolean_and_or_not_xor_exact(cell_state):
    """Each boolean gate matches its truth table for every (a, b) combination."""
    one = _one()
    strand = _logic_chromosome(one)
    got = set(l for l, _ in G.gene_express(strand, one, cell_state))
    a, b = bool(cell_state & A), bool(cell_state & B)
    assert ("AND" in got) == (a and b)
    assert ("OR" in got) == (a or b)
    assert ("NOT" in got) == (not a)
    assert ("XOR" in got) == (a != b)


def test_xor_is_the_genuine_generalisation():
    """XOR is the gate E1 (a single conjunctive clause) CANNOT express — it needs a DISJUNCTION
    of two clauses. It expresses for exactly the odd-parity states (01, 10), not (00, 11)."""
    one = _one()
    strand = _logic_chromosome(one)
    on = [cs for cs in (0b00, 0b01, 0b10, 0b11)
          if "XOR" in [l for l, _ in G.gene_express(strand, one, cs)]]
    assert on == [0b01, 0b10]


def test_empty_dnf_never_expresses():
    """The empty DNF (0 clauses) is the OR-identity FALSE — the gene never expresses."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c", genes=[("never", _leaves(1), _boolean([]))])
    for cs in (0, 1, 2, 3, 0xFF, 2**63):
        assert [l for l, _ in G.gene_express(strand, one, cs)] == []


# ── (2) E1-as-1-term-DNF cross-check ──────────────────────────────────────────

@pytest.mark.parametrize("activator,repressor", [
    (0, 0), (A, 0), (0, B), (A, B), (0b011, 0b100), (0xFF, 0xFF00), (2**40, 2**41),
])
def test_e1_klein4_equals_one_clause_boolean(activator, repressor):
    """E1 ⊂ E2: a rc129 klein4_mask gene (activator, repressor) is behaviour-identical to a
    boolean gene with the SINGLE DNF clause [(activator, repressor)], for every cell_state."""
    one = _one()
    s_e1 = G.chromosome(the_one=one, label="e1", genes=[("g", _leaves(1), activator, repressor)])
    s_e2 = G.chromosome(the_one=one, label="e2",
                        genes=[("g", _leaves(1), _boolean([(activator, repressor)]))])
    for cs in (0, A, B, C, A | B, A | B | C, 0xFF, 0xF0, 2**40, 2**40 | 2**41):
        r1 = "g" in [l for l, _ in G.gene_express(s_e1, one, cs)]
        r2 = "g" in [l for l, _ in G.gene_express(s_e2, one, cs)]
        assert r1 == r2, (activator, repressor, cs, r1, r2)


# ── (3) THE LAC-OPERON via a 1-term DNF (identical to rc129) ───────────────────

def test_lac_operon_via_one_clause_dnf():
    """THE lac operon (Jacob & Monod 1961) as a 1-clause DNF: activator=lactose, repressor=glucose
    → expresses iff lactose PRESENT and glucose ABSENT. Cross-checked IDENTICAL to the rc129
    klein4_mask (0x67) lacZ gene."""
    one = _one()
    LACTOSE, GLUCOSE = 0b01, 0b10
    s62 = G.chromosome(the_one=one, label="ecoli",
                       genes=[("lacZ", _leaves(1), _boolean([(LACTOSE, GLUCOSE)]))])
    s67 = G.chromosome(the_one=one, label="ecoli",
                       genes=[("lacZ", _leaves(1), LACTOSE, GLUCOSE)])

    def on(strand, cs):
        return "lacZ" in [l for l, _ in G.gene_express(strand, one, cs)]

    for cs, want in [(LACTOSE, True), (0, False), (GLUCOSE, False), (LACTOSE | GLUCOSE, False)]:
        assert on(s62, cs) is want
        assert on(s67, cs) == on(s62, cs)                     # E1 == E2 1-clause DNF


# ── (4) THE op⊗operand THEOREM — cell_state modulates the expressed subset ─────

def test_theorem_state_modulates_boolean_subset():
    """Same DNA, different cell_state → different expressed subset, with boolean gates too."""
    one = _one()
    strand = _logic_chromosome(one)
    sub_00 = set(l for l, _ in G.gene_express(strand, one, 0b00))   # NOT only
    sub_01 = set(l for l, _ in G.gene_express(strand, one, 0b01))   # OR, XOR
    sub_11 = set(l for l, _ in G.gene_express(strand, one, 0b11))   # AND, OR
    assert sub_00 == {"NOT"}
    assert sub_01 == {"OR", "XOR"}
    assert sub_11 == {"AND", "OR"}
    assert sub_00 != sub_01 != sub_11


# ── (5) the READ-TIME FILTER — the strand is byte-identical after gene_express ─

def test_boolean_gene_express_never_mutates_the_strand():
    """gene_express is a READ — the strand's bytes are IDENTICAL before and after, for every
    cell_state (including boolean 0x62 genes)."""
    one = _one()
    strand = _logic_chromosome(one)
    before = [hv.tobytes() for hv in strand]
    for cs in (0, 1, 2, 3, 0xFF, 2**40):
        G.gene_express(strand, one, cs)
    assert before == [hv.tobytes() for hv in strand]


# ── (6) back-compat — rc129 / rc128 / plain read + behave IDENTICALLY ──────────

def test_plain_rc128_rc129_genes_unchanged_bytes_and_behaviour():
    """A chromosome of plain (2-tuple) + rc128 (3-tuple int) + rc129 (4-tuple) genes is
    BYTE-IDENTICAL under rc130 (no 0x62 marker appears) AND expresses identically to rc129."""
    one = _one()
    genes = [("housekeeping", _leaves(1, base=0)),              # plain (always)
             ("stress", _leaves(2, base=1), 0b011),             # rc128 single-mask
             ("lacZ", _leaves(1, base=2), 0b01, 0b10)]          # rc129 two-mask
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    # no boolean-gene marker anywhere (byte-level back-compat)
    assert all(G._cap_kind(hv) != G.BOOLEAN_GENE_MARKER for hv in strand)
    cases = {
        0b000: ["housekeeping"],
        0b001: ["housekeeping", "lacZ"],                       # lactose present, glucose absent
        0b011: ["housekeeping", "stress"],                     # both bits → stress ON; glucose → lacZ OFF
        0b010: ["housekeeping"],                               # glucose present → lacZ repressed
        0b111: ["housekeeping", "stress"],                     # glucose present → lacZ off
    }
    for cs, expected in cases.items():
        assert [l for l, _ in G.gene_express(strand, one, cs)] == expected


def test_rc129_two_mask_cap_bytes_unchanged_under_rc130():
    """A rc129 klein4_mask cap packs to the EXACT same bytes under rc130 (the 0x67 layout is
    untouched — only a NEW 0x62 marker was added)."""
    label, dim = "lacZ", 64
    cap = G._pack_regulatory_gene(label, 0b01, dim, repressor=0b10)
    raw = cap.tobytes()
    assert raw[0] == G.REGULATORY_GENE_MARKER                  # still 0x67, not 0x62
    nul = raw.find(b"\x00", 1)
    assert int.from_bytes(raw[nul + 1:nul + 9], "big") == 0b01
    assert int.from_bytes(raw[nul + 9:nul + 17], "big") == 0b10


# ── (7) the bare strand self-describes the gate_type + DNF ─────────────────────

def test_bare_strand_self_describes_gate_type_and_dnf():
    """The chromosome self-describes each gene's gate_type + DNF by bare-strand SCAN (no
    manifest): a 0x62 cap yields (GATE_TYPE_BOOLEAN_DNF, its DNF term list)."""
    one = _one()
    strand = _logic_chromosome(one)
    found = {}
    for hv in strand:
        if G._cap_kind(hv) == G.BOOLEAN_GENE_MARKER:
            _m, label = G._unpack_cap(hv)
            gt, dnf = G._boolean_gene_dnf(hv)
            found[label] = (gt, dnf)
            assert G._gene_gate_type(hv) == G.GATE_TYPE_BOOLEAN_DNF
    assert found == {
        "AND": (G.GATE_TYPE_BOOLEAN_DNF, [(A | B, 0)]),
        "OR":  (G.GATE_TYPE_BOOLEAN_DNF, [(A, 0), (B, 0)]),
        "NOT": (G.GATE_TYPE_BOOLEAN_DNF, [(0, A)]),
        "XOR": (G.GATE_TYPE_BOOLEAN_DNF, [(A, B), (B, A)]),
    }


def test_klein4_genes_report_klein4_gate_type():
    """A plain (0x47) and a klein4-mask (0x67) gene both report gate_type = klein4_mask (the
    fast path) — the dispatch family is complete."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("plain", _leaves(1)), ("reg", _leaves(1), 0b01, 0b10)])
    gate_types = {}
    for hv in strand:
        k = G._cap_kind(hv)
        if k in (G.GENE_CAP_MARKER, G.REGULATORY_GENE_MARKER):
            _m, label = G._unpack_cap(hv)
            gate_types[label] = G._gene_gate_type(hv)
    assert gate_types == {"plain": G.GATE_TYPE_KLEIN4_MASK, "reg": G.GATE_TYPE_KLEIN4_MASK}


# ── (8) format v8 → v9; a v9 genome saves + pages; pre-rc130 reads identically ─

def test_format_bumped_to_v9():
    assert G.GENOME_FORMAT_VERSION == 10       # rc131 §131 bumped v9->v10 (0x77 threshold gene)


def test_boolean_genome_saves_v9_and_pages_back(tmp_path):
    """A genome carrying a boolean gene saves at format_version 9, pages back gate-agnostically,
    and gene_express filters the loaded strand under a cell_state (from disk)."""
    one = _one()
    genes = [("housekeeping", _leaves(1)),
             ("xor_ab", _leaves(2, base=1), _boolean([(A, B), (B, A)]))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    p = tmp_path / "g"
    man = G.genome_save(strand, p, one)
    assert man["format_version"] == 10                         # rc131 bumped v9->v10; a v10 writer stamps 10
    paged = G.genome_genes(p, "cell", the_one=one)
    assert [l for l, _ in paged] == ["housekeeping", "xor_ab"]  # gate-agnostic recovery
    s2, o2, _ = G.genome_load(p)
    assert set(l for l, _ in G.gene_express(s2, o2, 0b01)) == {"housekeeping", "xor_ab"}
    assert set(l for l, _ in G.gene_express(s2, o2, 0b11)) == {"housekeeping"}  # XOR off at 11


def test_rebuild_by_scan_recovers_the_dnf(tmp_path):
    """§44: with NO manifest, the strand is the SSoT — rebuild-by-scan reproduces the boolean
    gene and gene_express still filters correctly (the gate_type + DNF live in the body)."""
    one = _one()
    strand = _logic_chromosome(one)
    p = tmp_path / "g"
    G.genome_save(strand, p, one)
    (p / "manifest.json").unlink()                             # drop the derived cache
    s2, o2, _ = G.genome_load(p, the_one=one)
    assert set(l for l, _ in G.gene_express(s2, o2, 0b01)) == {"OR", "XOR"}
    assert set(l for l, _ in G.gene_express(s2, o2, 0b11)) == {"AND", "OR"}


# ── (9) guard cases ──────────────────────────────────────────────────────────

def test_boolean_spec_requires_dnf_key():
    one = _one()
    with pytest.raises(ValueError, match="dnf"):
        G.chromosome(the_one=one, label="c", genes=[("g", _leaves(1), {"gate": "boolean"})])


def test_boolean_spec_rejects_unknown_gate():
    one = _one()
    with pytest.raises(ValueError, match="gate"):
        G.chromosome(the_one=one, label="c",
                     genes=[("g", _leaves(1), {"gate": "truth_table", "dnf": [(1, 0)]})])


def test_dnf_mask_must_be_nonnegative_int():
    one = _one()
    with pytest.raises(ValueError, match="non-negative"):
        G.chromosome(the_one=one, label="c", genes=[("g", _leaves(1), _boolean([(1, -1)]))])
    with pytest.raises(ValueError, match="exact int"):
        G.chromosome(the_one=one, label="c", genes=[("g", _leaves(1), _boolean([(1.5, 0)]))])


def test_dnf_term_must_be_pair():
    one = _one()
    with pytest.raises(ValueError, match="2-tuple"):
        G.chromosome(the_one=one, label="c", genes=[("g", _leaves(1), _boolean([(1, 0, 0)]))])


def test_attestation_documented():
    """The combinatorial-control (§130) + operon (§128/§129) attestations are documented."""
    assert "NBK26872" in G.gene_express.__doc__ or "How Genetic Switches" in G.gene_express.__doc__
    assert "Jacob" in G.gene_express.__doc__ and "Monod" in G.gene_express.__doc__


# ── (10) Python==C byte-identical ─────────────────────────────────────────────

_DNF_CASES = [
    ("AND", [(A | B, 0)]),
    ("OR", [(A, 0), (B, 0)]),
    ("NOT", [(0, A)]),
    ("XOR", [(A, B), (B, A)]),
    ("empty", []),
    ("wide", [(0xFF, 0xFF00), (2**40, 2**41)]),
    ("three", [(A, 0), (B, C), (0, A | B | C)]),
]


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("_name,dnf", _DNF_CASES)
@pytest.mark.parametrize("cell_state", [0b000, 0b001, 0b010, 0b011, 0b100, 0b111,
                                        0xFF, 0xFFFF, 2**40, 2**40 | 2**41])
def test_python_equals_c_boolean_decision(_name, dnf, cell_state):
    """The native per-gene DNF decision (srmech_genome_gene_express, 0x62 branch) is
    BYTE-IDENTICAL to the pure Python _dnf_expresses across AND/OR/NOT/XOR + wide/multi-clause."""
    cap = G._pack_boolean_gene("g", dnf, 128)
    expected = any((cell_state & act) == act and (cell_state & rep) == 0 for act, rep in dnf)
    assert _native.genome_gene_express_c(cap.tobytes(), 128, cell_state) is expected


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("cell_state", [0b00, 0b01, 0b10, 0b11])
def test_python_equals_c_logic_subset(cell_state):
    """gene_express returns the SAME expressed subset via native and forced-pure paths on the
    AND/OR/NOT/XOR boolean chromosome."""
    one = _one()
    strand = _logic_chromosome(one)
    native = [l for l, _ in G.gene_express(strand, one, cell_state)]
    real = _native.has_native_genome
    _native.has_native_genome = lambda: False
    try:
        pure = [l for l, _ in G.gene_express(strand, one, cell_state)]
    finally:
        _native.has_native_genome = real
    assert native == pure


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
def test_python_equals_c_genome_save_boolean(tmp_path):
    """genome_save writes turns.bin + manifest.json BYTE-IDENTICALLY on a genome carrying a
    boolean gene, native-vs-forced-pure."""
    one = _one()
    strand = _logic_chromosome(one)
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
