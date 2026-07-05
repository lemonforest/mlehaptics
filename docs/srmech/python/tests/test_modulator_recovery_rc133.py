"""rc133 (UPSTREAM §133, #733) — MODULATOR-RECOVERY (M1 + M2): the INVERSE of gene_express.

The E-ladder (rc128-132) is the FORWARD map (cell_state -> expressed genes). rc133 begins the
INVERSE (the #728 candidate-b): GIVEN an OBSERVED expressed set (+ the strand's gene regulatory
specs), recover what the cell_state that produced it must look like. It is UNDER-DETERMINED (many
cell_states -> the SAME expressed subset), so the exact cell_state is IRRECOVERABLE BY
CONSTRUCTION — the only honest form is a ONE-SIDED verdict (the op_verdict EQUAL/UNKNOWN contract,
rc117): recover the EXACT complement we can PROVE, flag the rest UNKNOWN.

  * M1 — modulator_recover(strand, the_one, expressed_labels) -> dict
      certain_on   = bits every consistent cell_state MUST have SET (OR expressed E1 activators +
                     intersection-over-clauses activator of expressed E2 genes)
      certain_off  = bits every consistent state MUST have CLEAR (the repressor duals)
      undetermined = the referenced condition bits (union any gene reads) minus (on | off)
      verdict      = EXACT (floor covers all referenced) / PARTIAL (some pinned) / UNKNOWN (none)
      E4 threshold / E3 graded / un-expressed genes contribute NOTHING (SOUND, not over-claiming).
  * M2 — modulator_consistent(strand, the_one, expressed_labels, candidate) -> str
      set(gene_express(candidate) labels) == set(expressed_labels) -> "CONSISTENT" else
      "INCONSISTENT". ONE-SIDED (could be the state; never IS the state). Reuses the forward
      gene_express.

THE SOUNDNESS CONTRACT (the load-bearing DoD): for EVERY cell_state M2 reports CONSISTENT,
(state & certain_on) == certain_on AND (state & certain_off) == 0. Proven by an EXHAUSTIVE
cross-check on small chromosomes over ≥ 3 mixed chromosomes.

Attested biology (ONE FACET — the inverse of expression; #728 discipline, NOT a claim srmech
reproduces it): gene-regulatory-network (GRN) inference — reverse-engineering the regulatory state
from an expression pattern — Marbach D, Costello JC, Küffner R, et al., "Wisdom of crowds for robust
gene network inference", Nature Methods 9(8):796-804 (2012), DOI 10.1038/nmeth.2016 (OA: NIH
PMC3512113 — the DREAM5 blind assessment).

numpy-free; NO abs() (exact Class-I bitwise); read-only.
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
    """The OBSERVED expressed label SET produced by gene_express at cell_state cs."""
    return sorted({lab for lab, _l in G.gene_express(strand, one, cs)})


# ── (1) M1 — the E1 two-sided floor (OR expressed activators / repressors) ─────

def test_m1_e1_two_sided_floor_exact():
    """E1 chromosome: certain_on = OR of the expressed genes' activator masks, certain_off = OR of
    their repressor masks. When the floor covers every referenced bit -> verdict EXACT."""
    one = _one()
    genes = [("g1", _leaves(1), A, B),          # activator=a, repressor=b
             ("g2", _leaves(1), A | C, D)]       # activator=a|c, repressor=d
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    cs = A | C                                   # both g1 and g2 express
    assert _expressed(strand, one, cs) == ["g1", "g2"]
    rec = G.modulator_recover(strand, one, ["g1", "g2"])
    assert rec["certain_on"] == (A | C)          # a from g1, a|c from g2
    assert rec["certain_off"] == (B | D)         # b from g1, d from g2
    assert rec["undetermined"] == 0              # a|b|c|d all pinned
    assert rec["verdict"] == "EXACT"


def test_m1_unexpressed_gene_makes_it_partial():
    """An UN-expressed E1 gene contributes NOTHING to the floor but its referenced bit stays in the
    universe -> undetermined != 0 -> verdict PARTIAL (honest: we can't pin its bit)."""
    one = _one()
    genes = [("g1", _leaves(1), A, B),
             ("g3", _leaves(1), E, 0)]           # references bit e; needs e present to express
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    cs = A                                        # g1 expresses; g3 does NOT (e absent)
    assert _expressed(strand, one, cs) == ["g1"]
    rec = G.modulator_recover(strand, one, ["g1"])
    assert rec["certain_on"] == A
    assert rec["certain_off"] == B
    assert rec["undetermined"] == E              # g3's bit is referenced but unpinned
    assert rec["verdict"] == "PARTIAL"


# ── (2) M1 — E2 clause-intersection contributes soundly ───────────────────────

def test_m1_e2_intersection_over_clauses_activator():
    """A 2-clause boolean gene where bit a is an activator in BOTH clauses -> a is certain-on (the
    intersection-over-clauses activator); bits present in only one clause are NOT pinned."""
    one = _one()
    strand = G.chromosome(the_one=one, label="cell",
                          genes=[("b", _leaves(1), _boolean([(A | B, 0), (A | C, 0)]))])
    cs = A | B                                    # clause 1 matches -> b expresses
    assert _expressed(strand, one, cs) == ["b"]
    rec = G.modulator_recover(strand, one, ["b"])
    assert rec["certain_on"] == A                 # a is required by EVERY clause
    assert rec["certain_off"] == 0
    assert rec["undetermined"] == (B | C)         # b, c present in only one clause each
    assert rec["verdict"] == "PARTIAL"


def test_m1_e2_intersection_over_clauses_repressor():
    """A 2-clause boolean gene where bit d is a repressor in BOTH clauses -> d is certain-off."""
    one = _one()
    strand = G.chromosome(the_one=one, label="cell",
                          genes=[("b2", _leaves(1), _boolean([(A, D), (C, D)]))])
    cs = A                                         # clause 1 (a present, d absent) matches
    assert _expressed(strand, one, cs) == ["b2"]
    rec = G.modulator_recover(strand, one, ["b2"])
    assert rec["certain_on"] == 0                  # a & c = 0 (no common activator)
    assert rec["certain_off"] == D                 # d forbidden by EVERY clause


# ── (3) M1 — E4 / E3 contribute NOTHING (sound, not over-claiming) ────────────

def test_m1_threshold_and_graded_contribute_nothing():
    """E4 threshold + E3 graded genes give NO clean single-bit certainty -> they contribute NOTHING
    to certain_on / certain_off (only an E1 gene's clean masks pin bits). This is the SOUNDNESS
    of not-over-claiming from a disjunctive gate."""
    one = _one()
    genes = [("e1", _leaves(1), A, 0),                              # E1 activator=a
             ("t",  _leaves(1), _threshold([1, 1], 1)),             # E4: a OR b
             ("d",  _leaves(1), _graded([1, 1, 1, 1], 4))]          # E3 dose-response
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    cs = A                                                          # all three express
    assert _expressed(strand, one, cs) == ["d", "e1", "t"]
    rec = G.modulator_recover(strand, one, ["d", "e1", "t"])
    assert rec["certain_on"] == A                                  # ONLY from e1, NOT t/d
    assert rec["certain_off"] == 0
    # t reads a|b, d reads a|b|c|d -> all referenced, only a pinned
    assert rec["undetermined"] == (B | C | D)
    assert rec["verdict"] == "PARTIAL"


# ── (4) the verdict — EXACT / PARTIAL / UNKNOWN (honest one-sidedness) ─────────

def test_verdict_unknown_when_nothing_pins():
    """UNKNOWN when NO bit is pinned: an empty observed set (nothing expressed to prove ON), OR only
    threshold/graded genes expressed (no clean floor). pinned == 0 -> UNKNOWN (never over-claim)."""
    one = _one()
    genes = [("g1", _leaves(1), A, B), ("t", _leaves(1), _threshold([1, 1], 1))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    # (a) empty observed set -> nothing to pin
    rec_empty = G.modulator_recover(strand, one, [])
    assert rec_empty["certain_on"] == 0 and rec_empty["certain_off"] == 0
    assert rec_empty["verdict"] == "UNKNOWN"
    # (b) only the threshold gene expressed -> a disjunctive gate pins nothing
    strand_t = G.chromosome(the_one=one, label="cell",
                            genes=[("t", _leaves(1), _threshold([1, 1], 1))])
    rec_t = G.modulator_recover(strand_t, one, ["t"])
    assert rec_t["certain_on"] == 0 and rec_t["certain_off"] == 0
    assert rec_t["verdict"] == "UNKNOWN"          # referenced != 0 but pinned == 0


# ── (5) THE SOUNDNESS CROSS-CHECK — every M2-consistent state agrees with M1 ───

def _assert_sound(strand, one, k):
    """For EVERY observed expressed set (keyed by a true cell_state in [0, 2**k)), M1's floor must
    hold for EVERY cell_state M2 calls CONSISTENT with that set: (s & certain_on) == certain_on AND
    (s & certain_off) == 0. This is the load-bearing soundness contract — M1 never over-claims."""
    for true_state in range(1 << k):
        expressed = _expressed(strand, one, true_state)
        rec = G.modulator_recover(strand, one, expressed)
        on, off = rec["certain_on"], rec["certain_off"]
        # the true state is itself consistent (sanity)
        assert G.modulator_consistent(strand, one, expressed, true_state) == "CONSISTENT"
        for s in range(1 << k):
            if G.modulator_consistent(strand, one, expressed, s) == "CONSISTENT":
                assert (s & on) == on, (true_state, s, on, expressed)
                assert (s & off) == 0, (true_state, s, off, expressed)


def test_soundness_e1_chromosome():
    one = _one()
    genes = [("p", _leaves(1)),                   # unregulated (always)
             ("g1", _leaves(1), A, B),            # act=a, rep=b
             ("g2", _leaves(1), C, A)]            # act=c, rep=a
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    _assert_sound(strand, one, 4)


def test_soundness_e1_e2_chromosome():
    one = _one()
    genes = [("g1", _leaves(1), A, 0),
             ("b", _leaves(1), _boolean([(A, B), (C, 0)])),   # (a AND not b) OR c
             ("r", _leaves(1), 0, D)]                          # expresses iff d absent
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    _assert_sound(strand, one, 4)


def test_soundness_full_mix_chromosome():
    one = _one()
    genes = [("p", _leaves(1)),                                     # unregulated
             ("g1", _leaves(1), A, B),                              # E1
             ("bool", _leaves(1), _boolean([(A | C, 0), (B, 0)])),  # E2
             ("thr", _leaves(1), _threshold([1, 1, -1], 1)),        # E4 (signed)
             ("grad", _leaves(1), _graded([1, 1, 1, 1], 4))]        # E3
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    _assert_sound(strand, one, 4)


def test_soundness_duplicate_label_guard():
    """SOUNDNESS with a DUPLICATED gene label: the label collapses in the observed SET, so NEITHER
    duplicate can be attributed -> neither contributes to the floor (the uniqueness guard). Proven
    sound by the exhaustive cross-check."""
    one = _one()
    genes = [("dup", _leaves(1), A, 0),           # two genes share the label "dup"
             ("dup", _leaves(1), B, 0),
             ("u", _leaves(1), C, 0)]             # a uniquely-labelled gene
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    # the duplicated label pins NOTHING; only the unique "u" pins bit c
    rec = G.modulator_recover(strand, one, ["dup", "u"])
    assert rec["certain_on"] == C                 # NOT a|b|c — the guard prevents over-claim
    _assert_sound(strand, one, 4)


# ── (6) M2 — consistent / inconsistent + one-sidedness ────────────────────────

def test_m2_consistent_and_inconsistent():
    one = _one()
    genes = [("g1", _leaves(1), A, B), ("g2", _leaves(1), C, 0)]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    cs = A | C
    observed = _expressed(strand, one, cs)                         # ["g1", "g2"]
    assert G.modulator_consistent(strand, one, observed, cs) == "CONSISTENT"
    # a state producing a DIFFERENT set is INCONSISTENT
    assert G.modulator_consistent(strand, one, observed, C) == "INCONSISTENT"   # only g2
    assert G.modulator_consistent(strand, one, observed, A | B | C) == "INCONSISTENT"  # g1 off (b)


def test_m2_is_one_sided_many_states_consistent():
    """ONE-SIDEDNESS: expression is under-determined, so MANY cell_states are CONSISTENT with one
    observed set (CONSISTENT = 'could be the state', never 'IS the state'). Here g's activator=a,
    and bits b/c are unread, so a-present states with any b/c are all consistent."""
    one = _one()
    strand = G.chromosome(the_one=one, label="cell", genes=[("g", _leaves(1), A, 0)])
    observed = ["g"]                                               # g expressed (a present)
    consistent = [s for s in range(16)
                  if G.modulator_consistent(strand, one, observed, s) == "CONSISTENT"]
    assert len(consistent) > 1                                     # under-determined
    assert all((s & A) == A for s in consistent)                  # every one has a present
    # and every consistent state agrees with M1's floor (certain_on = a)
    rec = G.modulator_recover(strand, one, observed)
    assert rec["certain_on"] == A
    assert all((s & rec["certain_on"]) == rec["certain_on"] for s in consistent)


def test_m2_never_false_identifies():
    """M2 NEVER returns CONSISTENT for a state whose forward expression differs from the observed set
    (no false positive-identification) — checked exhaustively against the ground-truth forward map."""
    one = _one()
    genes = [("g1", _leaves(1), A, B), ("b", _leaves(1), _boolean([(A, 0), (C, 0)]))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    observed = _expressed(strand, one, A)
    for s in range(16):
        verdict = G.modulator_consistent(strand, one, observed, s)
        truth = (_expressed(strand, one, s) == observed)
        assert (verdict == "CONSISTENT") == truth, (s, verdict, truth)


# ── (7) read-only — the strand is byte-identical after both ops ───────────────

def test_read_only_strand_byte_identical():
    one = _one()
    genes = [("g1", _leaves(2), A, B),
             ("b", _leaves(1), _boolean([(A, 0), (C, 0)])),
             ("t", _leaves(1), _threshold([1, 1], 2)),
             ("d", _leaves(1), _graded([1, 1, 1, 1], 4))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    before = [hv.tobytes() for hv in strand]
    _ = G.modulator_recover(strand, one, ["g1", "b"])
    _ = G.modulator_consistent(strand, one, ["g1", "b"], A)
    after = [hv.tobytes() for hv in strand]
    assert before == after


# ── (8) input validation ──────────────────────────────────────────────────────

def test_expressed_labels_must_be_a_sequence_not_a_bare_string():
    one = _one()
    strand = G.chromosome(the_one=one, label="cell", genes=[("g", _leaves(1), A, 0)])
    with pytest.raises(ValueError):
        G.modulator_recover(strand, one, "g")            # a single string is NOT a label set


def test_candidate_cell_state_must_be_nonneg_int():
    one = _one()
    strand = G.chromosome(the_one=one, label="cell", genes=[("g", _leaves(1), A, 0)])
    with pytest.raises(ValueError):
        G.modulator_consistent(strand, one, ["g"], -1)
    with pytest.raises(ValueError):
        G.modulator_consistent(strand, one, ["g"], 1.5)


# ── (9) Python==C byte-identical ──────────────────────────────────────────────

def _mixed_strand(one):
    genes = [("p", _leaves(1)),
             ("g1", _leaves(1), A, B),
             ("g2", _leaves(1), A | C, D),
             ("bool", _leaves(1), _boolean([(A | B, 0), (A | C, D)])),
             ("thr", _leaves(1), _threshold([2, -1, 1], 1)),
             ("grad", _leaves(1), _graded([1, 1, 1, 1], 4))]
    return G.chromosome(the_one=one, label="cell", genes=genes)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not built")
def test_python_equals_c_modulator_recover():
    """The whole-strand C peer srmech_genome_modulator_recover produces byte-identical dict fields +
    verdict to the pure Python _modulator_recover_pure, over every observed label subset."""
    from itertools import combinations
    one = _one()
    strand = _mixed_strand(one)
    all_labels = [lab for lab, _l in G.genes(strand, one)]
    body = G._modulator_gene_body(strand)
    for r in range(len(all_labels) + 1):
        for subset in combinations(all_labels, r):
            labels = list(subset)
            blob = b"".join(lb.encode("utf-8") + b"\x00" for lb in dict.fromkeys(labels))
            c_on, c_off, c_und, c_verdict = _native.genome_modulator_recover_c(
                body, len(one), blob)
            py = G._modulator_recover_pure(strand, labels)
            assert c_on == py["certain_on"], (labels, c_on, py)
            assert c_off == py["certain_off"], (labels, c_off, py)
            assert c_und == py["undetermined"], (labels, c_und, py)
            assert G._MODULATOR_VERDICTS[c_verdict] == py["verdict"], (labels, c_verdict, py)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not built")
def test_python_equals_c_modulator_consistent():
    """The whole-strand C peer srmech_genome_modulator_consistent produces the SAME CONSISTENT /
    INCONSISTENT verdict as the pure Python set comparison, over a grid of observed sets +
    candidate cell_states (incl. signed-weight threshold + graded genes)."""
    one = _one()
    strand = _mixed_strand(one)
    body = G._modulator_gene_body(strand)
    for obs_state in range(32):
        observed = _expressed(strand, one, obs_state)
        blob = b"".join(lb.encode("utf-8") + b"\x00" for lb in dict.fromkeys(observed))
        for cs in range(32):
            c = _native.genome_modulator_consistent_c(body, len(one), blob, cs)
            py = (sorted({lab for lab, _l in G.gene_express(strand, one, cs)}) == observed)
            assert c == py, (observed, cs, c, py)


# ── (10) no genome-format bump (a READ over existing gene caps) ────────────────

def test_no_genome_format_bump():
    """rc133 adds NO new marker / block KIND — the modulator ops are a READ over the existing gene
    caps, so the genome format stays v11 (the rc132 value)."""
    assert G.GENOME_FORMAT_VERSION == 11
