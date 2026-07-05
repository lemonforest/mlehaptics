"""rc134 (UPSTREAM §133, #733) — MODULATOR-CONSTRAINT (M3): the COMPLETE inverse of gene_express.

The LAST rung of the E-M ladder. M1 (modulator_recover) gives the SOUND two-sided FLOOR from the
EXPRESSED genes; M2 (modulator_consistent) forward-CHECKS one candidate. M3 returns the EXACT
CONSTRAINT characterizing the WHOLE set of cell-states consistent with an observed expression — a
COMPACT structured constraint, NEVER an enumeration (the consistent set can be exponential).

  * modulator_constraint(strand, the_one, expressed_labels) -> dict
      certain_on / certain_off  = M1's floor (the pinned bits)
      clauses                   = disjunctive bit-clauses:
          {"kind":"nand", "any_absent":mask, "any_present":mask}   (un-expressed E1/E2 -> the gene
              NOT expressing: some activator absent OR some repressor present; all ANDed)
          {"kind":"or_terms", "terms":[{"present":a, "absent":r}, ...]}   (expressed pure-boolean
              label with >= 2 terms -> the FULL disjunction: >= 1 term fully matches)
      inequalities              = E4 threshold {"weights":[...], "threshold":theta, "sense":">="|"<"}
      levels                    = E3 graded {"weights":[...], "denom":D, "positive":bool}
      satisfiable / free_bits / solution_note / sound_complete / sound_only_labels
  * modulator_constraint_satisfies(constraint, candidate) -> bool  (the runnable checker)

SOUND: every M2-consistent cell_state satisfies the constraint. COMPLETE (satisfies <=> consistent)
for the BOOLEAN gate-types E1/E2 at ANY label multiplicity + a UNIQUE single E4/E3 gene; SOUND-ONLY
(honestly flagged) for an EXPRESSED cross-type-OR label. Proven by an EXHAUSTIVE cross-check.

numpy-free; NO abs() (exact Class-I bitwise; Class-N sums; Class-K inequality sign); read-only.
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


# condition bits: a = bit0, b = bit1, c = bit2, d = bit3, e = bit4
A, B, C, D, E = 1 << 0, 1 << 1, 1 << 2, 1 << 3, 1 << 4


def _graded(weights, denom):
    return {"gate": "graded", "weights": list(weights), "denom": denom}


def _threshold(weights, theta):
    return {"gate": "threshold", "weights": list(weights), "threshold": theta}


def _boolean(dnf):
    return {"gate": "boolean", "dnf": list(dnf)}


def _expressed(strand, one, cs):
    return sorted({lab for lab, _l in G.gene_express(strand, one, cs)})


# ── (1) UN-expressed genes give DISJUNCTIVE nand-clauses (what M1 left out) ────

def test_unexpressed_e1_gives_a_nand_clause():
    """An UN-expressed E1 gene (activator a, repressor b) proves (cs & a) != a OR (cs & b) != 0 —
    a single nand-clause {any_absent:a, any_present:b}. M1 gave nothing for it."""
    one = _one()
    genes = [("g1", _leaves(1), A, B)]              # expresses iff a present AND b absent
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    con = G.modulator_constraint(strand, one, [])  # g1 NOT expressed
    nand = [c for c in con["clauses"] if c["kind"] == "nand"]
    assert len(nand) == 1
    assert nand[0] == {"kind": "nand", "any_absent": A, "any_present": B}
    # the clause exactly means "g1 does not express": a absent OR b present
    assert not G.modulator_constraint_satisfies(con, A)         # a present, b absent -> WOULD express
    assert G.modulator_constraint_satisfies(con, A | B)        # b present -> silent -> consistent
    assert G.modulator_constraint_satisfies(con, 0)            # a absent -> silent -> consistent


def test_unexpressed_e2_ands_one_nand_per_dnf_term():
    """An UN-expressed E2 (boolean DNF) gene proves NO clause matched = a CONJUNCTION of nand-clauses
    (one per DNF term). expresses iff (a) OR (c); un-expressed -> a absent AND c absent."""
    one = _one()
    genes = [("b", _leaves(1), _boolean([(A, 0), (C, 0)]))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    con = G.modulator_constraint(strand, one, [])
    nand = [c for c in con["clauses"] if c["kind"] == "nand"]
    assert len(nand) == 2                          # one per DNF term
    assert {"kind": "nand", "any_absent": A, "any_present": 0} in nand
    assert {"kind": "nand", "any_absent": C, "any_present": 0} in nand
    assert not G.modulator_constraint_satisfies(con, A)        # a present -> b would express
    assert G.modulator_constraint_satisfies(con, B)           # neither a nor c -> silent


# ── (2) the FULL expressed-E2 disjunction (M1 only took the intersection) ──────

def test_expressed_e2_disjunction_is_an_or_terms_clause():
    """An EXPRESSED E2 gene with >= 2 DNF clauses -> an or_terms clause carrying the FULL disjunction
    (>= 1 term fully matches). M1 only pinned the sound intersection-over-clauses."""
    one = _one()
    genes = [("b", _leaves(1), _boolean([(A | B, 0), (A | C, 0)]))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    con = G.modulator_constraint(strand, one, ["b"])
    ors = [c for c in con["clauses"] if c["kind"] == "or_terms"]
    assert len(ors) == 1
    terms = {(t["present"], t["absent"]) for t in ors[0]["terms"]}
    assert terms == {(A | B, 0), (A | C, 0)}       # BOTH clauses (not just the a-intersection)
    # a alone is NOT enough (M1's floor pins a, but the exact constraint needs a full clause)
    assert not G.modulator_constraint_satisfies(con, A)
    assert G.modulator_constraint_satisfies(con, A | B)
    assert G.modulator_constraint_satisfies(con, A | C)


def test_duplicate_boolean_label_is_a_full_disjunction():
    """Two E1 genes sharing a label -> the label expresses iff EITHER expresses = an or_terms clause
    with both genes' terms (M1 gave nothing — a duplicated label can't be attributed)."""
    one = _one()
    genes = [("dup", _leaves(1), A, 0), ("dup", _leaves(1), B, 0)]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    con = G.modulator_constraint(strand, one, ["dup"])
    ors = [c for c in con["clauses"] if c["kind"] == "or_terms"]
    assert len(ors) == 1
    terms = {(t["present"], t["absent"]) for t in ors[0]["terms"]}
    assert terms == {(A, 0), (B, 0)}
    assert con["certain_on"] == 0                  # the floor pins NOTHING (label not unique)
    assert G.modulator_constraint_satisfies(con, A)
    assert G.modulator_constraint_satisfies(con, B)
    assert not G.modulator_constraint_satisfies(con, C)   # neither dup gene expresses


# ── (3) the general-gate inverse — E4 inequalities + E3 levels ─────────────────

def test_e4_threshold_inequalities():
    """An EXPRESSED E4 threshold gene -> Sum w_i*bit_i >= theta (sense '>='); UN-expressed -> Sum <
    theta (sense '<'). Exact linear inequalities, not a mask-OR."""
    one = _one()
    genes = [("t", _leaves(1), _threshold([2, -1, 1], 1))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    con_on = G.modulator_constraint(strand, one, ["t"])
    assert con_on["inequalities"] == [{"weights": [2, -1, 1], "threshold": 1, "sense": ">="}]
    con_off = G.modulator_constraint(strand, one, [])
    assert con_off["inequalities"] == [{"weights": [2, -1, 1], "threshold": 1, "sense": "<"}]
    # a present (w0=2) -> Sum 2 >= 1 -> expresses -> consistent with ["t"], NOT with []
    assert G.modulator_constraint_satisfies(con_on, A)
    assert not G.modulator_constraint_satisfies(con_off, A)
    assert not G.modulator_constraint_satisfies(con_on, B)     # b alone: Sum -1 < 1 -> silent
    assert G.modulator_constraint_satisfies(con_off, B)


def test_e3_graded_levels():
    """An EXPRESSED E3 graded gene -> the dose Sum w_i*bit_i >= 1 (positive True, level > 0);
    UN-expressed -> Sum <= 0 (positive False, level 0)."""
    one = _one()
    genes = [("d", _leaves(1), _graded([1, 1, -1, 0], 4))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    con_on = G.modulator_constraint(strand, one, ["d"])
    assert con_on["levels"] == [{"weights": [1, 1, -1, 0], "denom": 4, "positive": True}]
    con_off = G.modulator_constraint(strand, one, [])
    assert con_off["levels"] == [{"weights": [1, 1, -1, 0], "denom": 4, "positive": False}]
    assert G.modulator_constraint_satisfies(con_on, A)         # dose 1 >= 1 -> expresses
    assert not G.modulator_constraint_satisfies(con_off, A)
    assert G.modulator_constraint_satisfies(con_off, C)        # dose -1 <= 0 -> silent


# ── (4) SOUND-AND-COMPLETE exhaustive cross-check (satisfies <=> consistent) ────

def _assert_sound_and_complete(strand, one, k, *, expect_complete):
    """For EVERY observed expressed set (keyed by a true cell_state in [0, 2**k)), M3's constraint
    must be SOUND (every M2-consistent state satisfies it) and — when expect_complete — COMPLETE
    (satisfies <=> consistent) for EVERY cell_state. Returns (any_sound_only_flagged)."""
    saw_sound_only = False
    for true_state in range(1 << k):
        expressed = _expressed(strand, one, true_state)
        con = G.modulator_constraint(strand, one, expressed)
        if not con["sound_complete"]:
            saw_sound_only = True
        # the true state is itself consistent AND must satisfy (sanity)
        assert G.modulator_constraint_satisfies(con, true_state), (true_state, expressed)
        for s in range(1 << k):
            consistent = (G.modulator_consistent(strand, one, expressed, s) == "CONSISTENT")
            satisfied = G.modulator_constraint_satisfies(con, s)
            # SOUND ALWAYS: every consistent state satisfies the constraint
            if consistent:
                assert satisfied, ("SOUND violated", true_state, s, expressed)
            if expect_complete:
                assert satisfied == consistent, ("COMPLETE violated", true_state, s, expressed)
    return saw_sound_only


def test_complete_e1_chromosome():
    one = _one()
    genes = [("p", _leaves(1)), ("g1", _leaves(1), A, B), ("g2", _leaves(1), C, A)]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    assert _assert_sound_and_complete(strand, one, 4, expect_complete=True) is False


def test_complete_e1_e2_chromosome():
    one = _one()
    genes = [("g1", _leaves(1), A, 0),
             ("b", _leaves(1), _boolean([(A, B), (C, 0)])),   # (a AND not b) OR c
             ("r", _leaves(1), 0, D)]                          # expresses iff d absent
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    assert _assert_sound_and_complete(strand, one, 4, expect_complete=True) is False


def test_complete_unexpressed_heavy_chromosome():
    """UN-expressed-heavy: many genes reference distinct bits; most are silent for most states. The
    un-expressed disjunctive clauses must make it COMPLETE (un-expressed labels are complete for
    every gate-type — a conjunction of exact silence constraints)."""
    one = _one()
    genes = [("g1", _leaves(1), A, B),
             ("g2", _leaves(1), C, 0),
             ("g3", _leaves(1), D, 0),
             ("g4", _leaves(1), E, 0),
             ("b", _leaves(1), _boolean([(A | C, 0), (D, E)]))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    assert _assert_sound_and_complete(strand, one, 5, expect_complete=True) is False


def test_complete_unique_label_full_mix_chromosome():
    """A UNIQUE-labelled full mix (E1 + E2 + E4 + E3, all distinct labels) is sound-AND-complete for
    EVERY gate-type — the E4 inequality / E3 level are exact per-gene constraints."""
    one = _one()
    genes = [("p", _leaves(1)),
             ("g1", _leaves(1), A, B),
             ("bool", _leaves(1), _boolean([(A | C, 0), (B, 0)])),
             ("thr", _leaves(1), _threshold([1, 1, -1], 1)),
             ("grad", _leaves(1), _graded([1, 1, 1, 0], 4))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    assert _assert_sound_and_complete(strand, one, 4, expect_complete=True) is False


# ── (5) the SOUND-ONLY cross-type-OR case — SOUND, honestly flagged ────────────

def test_cross_type_or_is_sound_only_and_flagged():
    """A DUPLICATED label whose genes span boolean AND threshold is a genuine CROSS-TYPE OR with no
    exact flat-clause form. M3 stays SOUND (every consistent state satisfies) but is NOT complete —
    and it HONESTLY flags the label in sound_only_labels (sound_complete=False)."""
    one = _one()
    genes = [("dup", _leaves(1), A, 0),                                  # E1: expresses iff a
             ("dup", _leaves(1), _threshold([0, 1], 1)),                 # E4: expresses iff b
             ("u", _leaves(1), C, 0)]                                    # a clean unique gene
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    # when "dup" is expressed the constraint is sound-only + flagged
    con = G.modulator_constraint(strand, one, ["dup"])
    assert con["sound_complete"] is False
    assert con["sound_only_labels"] == ["dup"]
    # SOUND everywhere (exhaustive), NOT complete (over-approx on the cross-type OR)
    saw = _assert_sound_and_complete(strand, one, 4, expect_complete=False)
    assert saw is True                              # at least one observed set was sound-only


# ── (6) satisfiable — True for a real expression, False for a contradiction ────

def test_satisfiable_true_for_a_real_expression():
    one = _one()
    genes = [("g1", _leaves(1), A, B), ("g2", _leaves(1), C, 0)]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    for cs in range(16):
        expressed = _expressed(strand, one, cs)
        con = G.modulator_constraint(strand, one, expressed)
        assert con["satisfiable"] is True, (cs, expressed)   # a real state is always achievable


def test_satisfiable_false_for_two_genes_that_cannot_co_express():
    """A hand-crafted CONTRADICTION: g1 expresses iff bit a is SET, g2 expresses iff bit a is CLEAR
    (repressor a). Observing BOTH expressed requires a set AND clear -> unsatisfiable (a
    pin-contradiction; the sound detector fires)."""
    one = _one()
    genes = [("g1", _leaves(1), A, 0),             # expresses iff a present
             ("g2", _leaves(1), 0, A)]             # expresses iff a absent
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    con = G.modulator_constraint(strand, one, ["g1", "g2"])
    assert con["satisfiable"] is False
    # and indeed NO cell_state is consistent with both expressed
    assert all(G.modulator_consistent(strand, one, ["g1", "g2"], s) == "INCONSISTENT"
               for s in range(16))


def test_satisfiable_false_for_a_nonexistent_expected_label():
    one = _one()
    strand = G.chromosome(the_one=one, label="cell", genes=[("g", _leaves(1), A, 0)])
    con = G.modulator_constraint(strand, one, ["g", "ghost"])   # "ghost" is no gene's label
    assert con["satisfiable"] is False


# ── (7) never-enumerate — the return is compact + an honest size note ──────────

def test_never_enumerates_the_solution_set():
    """The constraint is a COMPACT structure + an HONEST size note — it NEVER carries the (possibly
    exponential) enumeration of consistent states. free_bits characterizes the size."""
    one = _one()
    # 6 don't-care bits (only bit a is read) -> the consistent set is large but the constraint is 1 pin
    strand = G.chromosome(the_one=one, label="cell", genes=[("g", _leaves(1), A, 0)])
    con = G.modulator_constraint(strand, one, ["g"])
    assert con["certain_on"] == A
    assert con["free_bits"] == 0                    # only bit a is referenced, and it is pinned
    assert "NOT enumerated" in con["solution_note"]
    # a truly under-determined case: g reads a|b|c but only needs a -> b,c are free referenced bits
    strand2 = G.chromosome(the_one=one, label="cell",
                           genes=[("g", _leaves(1), _boolean([(A, 0)])),
                                  ("h", _leaves(1), B | C, 0)])
    con2 = G.modulator_constraint(strand2, one, ["g"])   # g expressed, h NOT
    assert con2["free_bits"] >= 1
    assert "2^" in con2["solution_note"]            # a size bound, never the enumeration


# ── (8) read-only — the strand is byte-identical after both ops ────────────────

def test_read_only_strand_byte_identical():
    one = _one()
    genes = [("g1", _leaves(2), A, B),
             ("b", _leaves(1), _boolean([(A, 0), (C, 0)])),
             ("t", _leaves(1), _threshold([1, 1], 2)),
             ("d", _leaves(1), _graded([1, 1, 1, 1], 4))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    before = [hv.tobytes() for hv in strand]
    con = G.modulator_constraint(strand, one, ["g1", "b"])
    _ = G.modulator_constraint_satisfies(con, A)
    after = [hv.tobytes() for hv in strand]
    assert before == after


# ── (9) input validation ───────────────────────────────────────────────────────

def test_expressed_labels_must_be_a_sequence_not_a_bare_string():
    one = _one()
    strand = G.chromosome(the_one=one, label="cell", genes=[("g", _leaves(1), A, 0)])
    with pytest.raises(ValueError):
        G.modulator_constraint(strand, one, "g")


def test_candidate_must_be_a_nonneg_int():
    one = _one()
    strand = G.chromosome(the_one=one, label="cell", genes=[("g", _leaves(1), A, 0)])
    con = G.modulator_constraint(strand, one, ["g"])
    with pytest.raises(ValueError):
        G.modulator_constraint_satisfies(con, -1)
    with pytest.raises(ValueError):
        G.modulator_constraint_satisfies(con, 1.5)


# ── (10) Python==C byte-identical on the emitted BOOLEAN constraint ─────────────

def _mixed_strand(one):
    genes = [("p", _leaves(1)),
             ("g1", _leaves(1), A, B),
             ("g2", _leaves(1), A | C, D),
             ("bool", _leaves(1), _boolean([(A | B, 0), (A | C, D)])),
             ("thr", _leaves(1), _threshold([2, -1, 1], 1)),
             ("grad", _leaves(1), _graded([1, 1, 1, 1], 4)),
             ("dup", _leaves(1), A, 0),
             ("dup", _leaves(1), B, 0)]
    return G.chromosome(the_one=one, label="cell", genes=genes)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not built")
def test_python_equals_c_boolean_constraint_emit():
    """The C peer srmech_genome_modulator_constraint emits the BOOLEAN part (floor + nand / or_terms
    clauses) BYTE-IDENTICALLY to the pure Python serialization, over every observed label subset."""
    from itertools import combinations
    one = _one()
    strand = _mixed_strand(one)
    body = G._modulator_gene_body(strand)
    uniq = list(dict.fromkeys(lab for lab, _l in G.genes(strand, one)))
    for r in range(len(uniq) + 1):
        for subset in combinations(uniq, r):
            labels = list(subset)
            blob = b"".join(lb.encode("utf-8") + b"\x00" for lb in dict.fromkeys(labels))
            c_bytes = _native.genome_modulator_constraint_c(body, len(one), blob)
            on, off, nand_list, or_list = G._modulator_constraint_bool_pure(strand, labels)
            py_bytes = G._serialize_bool_constraint(on, off, nand_list, or_list)
            assert c_bytes == py_bytes, (labels, c_bytes.hex(), py_bytes.hex())
            # and the C bytes round-trip back to the SAME structure
            assert G._deserialize_bool_constraint(c_bytes) == (on, off, nand_list, or_list)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not built")
def test_python_equals_c_constraint_satisfies_boolean():
    """The C peer srmech_genome_modulator_constraint_satisfies gives the SAME boolean-part verdict as
    the pure Python _satisfies_bool, over a grid of observed sets + candidate cell_states."""
    one = _one()
    strand = _mixed_strand(one)
    for obs_state in range(32):
        observed = _expressed(strand, one, obs_state)
        con = G.modulator_constraint(strand, one, observed)
        nand_list = [(c["any_absent"], c["any_present"]) for c in con["clauses"]
                     if c["kind"] == "nand"]
        or_list = [[(t["present"], t["absent"]) for t in c["terms"]]
                   for c in con["clauses"] if c["kind"] == "or_terms"]
        buf = G._serialize_bool_constraint(con["certain_on"], con["certain_off"],
                                           nand_list, or_list)
        for cs in range(32):
            c_ok = _native.genome_modulator_constraint_satisfies_c(buf, cs)
            py_ok = G._satisfies_bool(con["certain_on"], con["certain_off"], con["clauses"], cs)
            assert c_ok == py_ok, (observed, cs, c_ok, py_ok)


# ── (11) no genome-format bump (a READ over existing gene caps) ────────────────

def test_no_genome_format_bump():
    """rc134 adds NO new marker / block KIND — M3 is a READ over the existing gene caps, so the
    genome format stays v11 (the rc132 value)."""
    assert G.GENOME_FORMAT_VERSION == 11


# ── (12) the return dict is JSON-serializable ──────────────────────────────────

def test_constraint_is_json_serializable():
    import json
    one = _one()
    strand = _mixed_strand(one)
    con = G.modulator_constraint(strand, one, ["g1", "bool", "thr", "grad"])
    round_trip = json.loads(json.dumps(con))       # masks=int, clauses/ineq/levels = list[dict]
    assert round_trip["certain_on"] == con["certain_on"]
    assert round_trip["clauses"] == con["clauses"]
