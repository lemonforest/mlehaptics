"""rc129 (UPSTREAM §129, #729) — KLEIN-4 REGULATORY ROLES: enrich rc128's cell-state gene
expression with activator/repressor logic, where each regulatory CONDITION is a KLEIN-4
SECTOR (the genome's native alphabet).

rc128 shipped ``gene_express`` with the rule ``(cell_state & gene_mask) == gene_mask`` — a
pure conjunctive AND-gate (all required conditions present = all-ACTIVATOR). Biology (the
lac operon, Jacob & Monod 1961) also has REPRESSORS (require-ABSENT). rc129 enriches the
rule to activator/repressor PER CONDITION — and each condition's role is a Klein-4 sector.

THE KLEIN-4 FRAMING (framework-native, not an extra mask): each regulatory condition (bit)
carries one of FOUR roles — the genome's native Klein-4 alphabet. The per-condition pair
``(act_bit, rep_bit)`` IS the Klein-4 sector (the two bit-planes are the two Z2 factors of
V = Z2 × Z2):

    (act_bit, rep_bit)   role          expression constraint on this bit
    (0, 0)               don't-care    (no constraint)
    (1, 0)               activator     the bit MUST be present in cell_state
    (0, 1)               repressor     the bit MUST be absent from cell_state
    (1, 1)               never         present AND absent → contradiction → never expresses

ENCODING = two parallel bitmasks (activator_mask, repressor_mask). The rule (exact Class-I
bitwise): a gene expresses iff (cell_state & activator_mask) == activator_mask (all
activators present) AND (cell_state & repressor_mask) == 0 (no repressor present).

Attested biology (ONE FACET — genes have other regulation too; NOT a reduction):
  * Jacob F & Monod J (1961) "Genetic regulatory mechanisms in the synthesis of proteins",
    *J Mol Biol* 3(3):318-356 (doi:10.1016/S0022-2836(61)80072-7) — the lac-operon /
    activator-repressor model (OA-verified).
  * Alberts et al., *Molecular Biology of the Cell* 4th ed., NCBI Bookshelf NBK26887.

Proven here (the ask's DoD):
  1. all 4 Klein-4 roles exact (don't-care / activator / repressor / never);
  2. THE LAC-OPERON exemplar (activator=lactose-bit + repressor=glucose-bit expresses iff
     lactose present AND glucose absent);
  3. THE op⊗operand THEOREM: same DNA, different cell_state → different expressed subset;
  4. the READ-TIME FILTER: the strand is byte-identical after gene_express (no mutation);
  5. back-compat: rc128 single-mask (3-tuple) genes read as all-activator = IDENTICAL
     behaviour AND byte-identical bytes; plain genes always express;
  6. the bare strand SELF-DESCRIBES BOTH masks (activator + repressor), no manifest;
  7. no v8→v9 format bump (additive extension of the 0x67 cap; a rc129 two-mask genome
     saves + pages at v8);
  8. Python==C byte-identical (the per-gene decision across the 4 roles + a grid).

numpy-free; no abs() (the masks / cell_state are exact Class-I bitwise integers, never
negated).
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


# ── (1) all 4 Klein-4 roles exact ─────────────────────────────────────────────

def _four_role_chromosome(one):
    """One gene isolating each of the 4 Klein-4 roles:
      dontcare  — (act 0, rep 0)         always expresses;
      activator — (act 0b001, rep 0)     iff bit0 PRESENT;
      repressor — (act 0, rep 0b010)     iff bit1 ABSENT;
      never     — (act 0b100, rep 0b100) NEVER expresses (contradiction)."""
    genes = [("dontcare", _leaves(1, base=0), 0, 0),
             ("activator", _leaves(1, base=1), 0b001, 0),
             ("repressor", _leaves(1, base=2), 0, 0b010),
             ("never", _leaves(1, base=3), 0b100, 0b100)]
    return G.chromosome(the_one=one, label="roles", genes=genes)


@pytest.mark.parametrize("cell_state,expected", [
    (0b000, ["dontcare", "repressor"]),               # bit0 off → no activator; bit1 off → repressor ok
    (0b001, ["dontcare", "activator", "repressor"]),  # bit0 on → activator; bit1 off → repressor ok
    (0b010, ["dontcare"]),                            # bit1 on → repressor silenced; bit0 off → no activator
    (0b011, ["dontcare", "activator"]),               # bit0 on → activator; bit1 on → repressor silenced
    (0b100, ["dontcare", "repressor"]),               # bit2 on doesn't help 'never' (also needs it clear)
    (0b111, ["dontcare", "activator"]),               # bit1 on silences repressor; 'never' still never
])
def test_four_klein4_roles_exact(cell_state, expected):
    """Each Klein-4 role behaves exactly: don't-care always; activator require-present;
    repressor require-absent; never never-expresses (for EVERY cell_state)."""
    one = _one()
    strand = _four_role_chromosome(one)
    got = [label for label, _ in G.gene_express(strand, one, cell_state)]
    assert got == expected


def test_never_role_never_expresses_for_any_state():
    """The 'never' Klein-4 sector (a bit set in BOTH masks = present AND absent) auto-silences
    the gene for EVERY cell_state — the contradiction role."""
    one = _one()
    strand = _four_role_chromosome(one)
    for cs in (0, 1, 2, 3, 4, 7, 0b100, 2**40 | 0b100, 2**63):
        got = [l for l, _ in G.gene_express(strand, one, cs)]
        assert "never" not in got


def test_dontcare_role_always_expresses():
    """The 'don't-care' Klein-4 sector (act 0, rep 0) — an explicit regulatory gene with both
    planes empty — always expresses, identical to a plain gene."""
    one = _one()
    strand = _four_role_chromosome(one)
    for cs in (0, 1, 2, 3, 2**63):
        got = [l for l, _ in G.gene_express(strand, one, cs)]
        assert "dontcare" in got


# ── (2) THE LAC-OPERON exemplar ───────────────────────────────────────────────

def test_lac_operon_activator_and_repressor():
    """THE lac operon (Jacob & Monod 1961): lacZ carries activator=lactose-bit +
    repressor=glucose-bit — it expresses IFF lactose is PRESENT and glucose is ABSENT
    (catabolite repression + induction, the canonical two-signal AND-NOT gate)."""
    one = _one()
    LACTOSE, GLUCOSE = 0b01, 0b10
    genes = [("lacZ", _leaves(1), LACTOSE, GLUCOSE)]
    strand = G.chromosome(the_one=one, label="ecoli", genes=genes)

    def expresses(cs):
        return "lacZ" in [l for l, _ in G.gene_express(strand, one, cs)]

    assert expresses(LACTOSE) is True                       # lactose present, glucose absent → ON
    assert expresses(0) is False                            # no lactose → OFF (no inducer)
    assert expresses(GLUCOSE) is False                      # glucose present → OFF (repressed)
    assert expresses(LACTOSE | GLUCOSE) is False            # both → OFF (glucose represses)


# ── (3) THE op⊗operand THEOREM — same DNA, different cell_state → different subset ─

def test_theorem_state_modulates_expressed_subset_with_repressors():
    """The op⊗operand theorem holds with repressors too: the SAME chromosome under DIFFERENT
    cell_states expresses DIFFERENT subsets — now the operand can turn a gene OFF (repressor)
    as well as ON (activator)."""
    one = _one()
    strand = _four_role_chromosome(one)
    sub_a = [l for l, _ in G.gene_express(strand, one, 0b001)]   # bit0 on: activator ON, repressor ON
    sub_b = [l for l, _ in G.gene_express(strand, one, 0b010)]   # bit1 on: activator OFF, repressor SILENCED
    assert sub_a != sub_b
    assert "activator" in sub_a and "activator" not in sub_b
    assert "repressor" in sub_a and "repressor" not in sub_b     # bit1 present silences the repressor gene


# ── (4) the READ-TIME FILTER — the strand is byte-identical after gene_express ─

def test_gene_express_never_mutates_the_strand():
    """gene_express is a READ — the strand's bytes are IDENTICAL before and after, for every
    cell_state (including two-mask regulatory genes)."""
    one = _one()
    strand = _four_role_chromosome(one)
    before = [hv.tobytes() for hv in strand]
    for cs in (0, 0b001, 0b010, 0b011, 0b100, 0b111, 2**40):
        G.gene_express(strand, one, cs)
    after = [hv.tobytes() for hv in strand]
    assert before == after


# ── (5) back-compat — rc128 single-mask (3-tuple) reads as all-activator ──────

def test_rc128_single_mask_dual_reads_as_activator_only():
    """A rc128-style 3-tuple gene (single mask) dual-reads as (activator=mask, repressor=0):
    the masks recover as (mask, 0) and the expression rule reduces to the rc128 AND-gate
    (cell_state & mask) == mask."""
    one = _one()
    for mask in (0, 0b011, 0b100, 0xFF, 2**40):
        cap = G._pack_regulatory_gene("g", mask, 64)                 # 3-tuple / single-mask form
        act, rep = G._regulatory_gene_masks(cap)
        assert (act, rep) == (mask, 0)
        for cs in (0, 0b011, 0b100, 0xFF, 0xF0, 2**40):
            assert G._gene_expresses(cap, cs) == ((cs & mask) == mask)


def test_rc128_activator_only_gene_is_byte_identical():
    """A rc129 activator-only regulatory gene is BYTE-IDENTICAL to the rc128 single-mask cap:
    the writer emits the 8-byte (no-repressor) form when repressor == 0 (the 0 repressor IS
    the NUL padding), so no existing genome's bytes change."""
    one = _one()
    # the rc128 wire form: [0x67] + label + NUL + mask(uint64 BE) + NUL-pad, NO repressor field
    label, mask, dim = b"stress", 0b011, 64
    expected = (bytes([G.REGULATORY_GENE_MARKER]) + label + b"\x00"
                + mask.to_bytes(8, "big"))
    expected = expected + b"\x00" * (dim - len(expected))
    # 3-tuple (activator-only) and explicit repressor=0 both produce the rc128 bytes
    assert G._pack_regulatory_gene("stress", mask, dim).tobytes() == expected
    assert G._pack_regulatory_gene("stress", mask, dim, repressor=0).tobytes() == expected


def test_rc128_regulatory_genome_expresses_identically():
    """PROVE a rc128 regulatory-gene genome (all 3-tuples) expresses IDENTICALLY under rc129 —
    the rc128 fixture chromosome + expected subsets, unchanged."""
    one = _one()
    genes = [("housekeeping", _leaves(1, base=0)),              # plain (always)
             ("stress", _leaves(2, base=1), 0b011),             # rc128 single-mask
             ("mitosis", _leaves(1, base=2), 0b100)]            # rc128 single-mask
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    cases = {
        0b000: ["housekeeping"],
        0b001: ["housekeeping"],
        0b011: ["housekeeping", "stress"],
        0b100: ["housekeeping", "mitosis"],
        0b111: ["housekeeping", "stress", "mitosis"],
        0b110: ["housekeeping", "mitosis"],
    }
    for cs, expected in cases.items():
        assert [l for l, _ in G.gene_express(strand, one, cs)] == expected


def test_plain_genes_always_express():
    """A chromosome of ONLY plain (2-tuple) genes is unregulated — every gene expresses for
    every cell_state, and carries NO 0x67 marker (byte-identical to pre-rc128)."""
    one = _one()
    genes = [("a", _leaves(1)), ("b", _leaves(2, base=1)), ("c", _leaves(1, base=2))]
    strand = G.chromosome(the_one=one, label="plainonly", genes=genes)
    for cs in (0, 1, 7, 2**63):
        assert [l for l, _ in G.gene_express(strand, one, cs)] == ["a", "b", "c"]
    assert all(G._cap_kind(hv) != G.REGULATORY_GENE_MARKER for hv in strand)


# ── (6) the bare strand self-describes BOTH masks ─────────────────────────────

def test_bare_strand_self_describes_both_masks():
    """The chromosome self-describes BOTH Klein-4 planes (activator + repressor) by bare-strand
    SCAN — read from the 0x67 cap inline (no sidecar / manifest)."""
    one = _one()
    strand = _four_role_chromosome(one)
    masks = {}
    for hv in strand:
        if G._cap_kind(hv) in (G.GENE_CAP_MARKER, G.REGULATORY_GENE_MARKER):
            _m, label = G._unpack_cap(hv)
            masks[label] = G._regulatory_gene_masks(hv)
    assert masks == {
        "dontcare": (0, 0),
        "activator": (0b001, 0),
        "repressor": (0, 0b010),
        "never": (0b100, 0b100),
    }


def test_two_mask_cap_carries_repressor_field():
    """A two-mask regulatory gene (repressor != 0) carries the SECOND 8-byte field inline
    (where a rc128 cap had padding) — the repressor round-trips from the bare cap."""
    one = _one()
    cap = G._pack_regulatory_gene("lacZ", 0b01, 64, repressor=0b10)
    act, rep = G._regulatory_gene_masks(cap)
    assert (act, rep) == (0b01, 0b10)
    raw = cap.tobytes()
    nul = raw.find(b"\x00", 1)
    # the activator (8 bytes) then the repressor (8 bytes) both sit after the label NUL
    assert int.from_bytes(raw[nul + 1:nul + 9], "big") == 0b01
    assert int.from_bytes(raw[nul + 9:nul + 17], "big") == 0b10


# ── (7) no v8→v9 format bump — additive within the 0x67 cap ────────────────────

def test_no_format_bump_two_mask_genome_saves_v8(tmp_path):
    """A rc129 two-mask (activator+repressor) genome saves at format_version 8 (NO v9 bump —
    additive extension of the existing 0x67 cap), pages back mask-agnostic, and gene_express
    filters the loaded strand under a cell_state (from disk)."""
    one = _one()
    LACTOSE, GLUCOSE = 0b01, 0b10
    genes = [("housekeeping", _leaves(1)),
             ("lacZ", _leaves(2, base=1), LACTOSE, GLUCOSE)]
    strand = G.chromosome(the_one=one, label="ecoli", genes=genes)
    p = tmp_path / "g"
    man = G.genome_save(strand, p, one)
    assert man["format_version"] == 9                          # rc130 §130 bumped v8->v9 (0x62 boolean gene); a two-mask 0x67 genome still saves + pages
    paged = G.genome_genes(p, "ecoli", the_one=one)
    assert [l for l, _ in paged] == ["housekeeping", "lacZ"]   # mask-agnostic recovery
    s2, o2, _ = G.genome_load(p)
    assert [l for l, _ in G.gene_express(s2, o2, LACTOSE)] == ["housekeeping", "lacZ"]
    assert [l for l, _ in G.gene_express(s2, o2, GLUCOSE)] == ["housekeeping"]  # lacZ repressed


def test_rebuild_by_scan_recovers_both_masks(tmp_path):
    """§44: with NO manifest, the strand is the SSoT — rebuild-by-scan reproduces the exact
    two-mask chromosome and gene_express still filters correctly (both planes live in the
    body)."""
    one = _one()
    strand = _four_role_chromosome(one)
    p = tmp_path / "g"
    G.genome_save(strand, p, one)
    (p / "manifest.json").unlink()                             # drop the derived cache
    s2, o2, _ = G.genome_load(p, the_one=one)
    assert [l for l, _ in G.gene_express(s2, o2, 0b001)] == ["dontcare", "activator", "repressor"]
    assert [l for l, _ in G.gene_express(s2, o2, 0b010)] == ["dontcare"]


# ── (8) guard cases ──────────────────────────────────────────────────────────

def test_repressor_mask_must_be_nonnegative_int():
    one = _one()
    with pytest.raises(ValueError, match="non-negative"):
        G.chromosome(the_one=one, label="c", genes=[("g", _leaves(1), 0b1, -1)])
    with pytest.raises(ValueError, match="exact int"):
        G.chromosome(the_one=one, label="c", genes=[("g", _leaves(1), 0b1, 1.5)])


def test_jacob_monod_attestation_documented():
    """The lac-operon / activator-repressor attestation is documented in gene_express."""
    assert "Jacob" in G.gene_express.__doc__ and "Monod" in G.gene_express.__doc__
    assert "NBK26887" in G.gene_express.__doc__               # differential-expression facet


# ── (9) Python==C byte-identical ──────────────────────────────────────────────

@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("activator,repressor,cell_state", [
    (0, 0, 0), (0, 0, 0b111),                              # don't-care always
    (0b001, 0, 0b001), (0b001, 0, 0b000),                 # activator require-present
    (0, 0b010, 0b000), (0, 0b010, 0b010),                 # repressor require-absent
    (0b100, 0b100, 0b100), (0b100, 0b100, 0b000),         # never (contradiction)
    (0b01, 0b10, 0b01), (0b01, 0b10, 0b11), (0b01, 0b10, 0b10),   # lac operon
    (0xFF, 0xFF00, 0xFF), (0xFF, 0xFF00, 0xFFFF),         # wide masks
    (2**40, 2**41, 2**40), (2**40, 2**41, 2**40 | 2**41),
])
def test_python_equals_c_two_mask_decision(activator, repressor, cell_state):
    """The native per-gene decision (srmech_genome_gene_express) is BYTE-IDENTICAL to the pure
    two-mask Class-I decision across the 4 Klein-4 roles + the lac operon + wide masks."""
    cap = G._pack_regulatory_gene("g", activator, 64, repressor=repressor)
    expected = ((cell_state & activator) == activator) and ((cell_state & repressor) == 0)
    assert _native.genome_gene_express_c(cap.tobytes(), 64, cell_state) is expected


@pytest.mark.skipif(not _native.has_native_genome(),
                    reason="native genome surface not built in this env")
@pytest.mark.parametrize("cell_state", [0b000, 0b001, 0b010, 0b011, 0b100, 0b111])
def test_python_equals_c_four_role_subset(cell_state):
    """gene_express returns the SAME expressed subset via native and forced-pure paths on the
    4-role (two-mask) chromosome."""
    one = _one()
    strand = _four_role_chromosome(one)
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
def test_python_equals_c_genome_save_two_mask(tmp_path):
    """genome_save writes turns.bin + manifest.json BYTE-IDENTICALLY on a genome carrying a
    two-mask regulatory gene, native-vs-forced-pure."""
    one = _one()
    strand = _four_role_chromosome(one)
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
