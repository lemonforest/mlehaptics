"""rc132 (UPSTREAM §132, #732) — the GRADED / ANALOG expression LEVEL (E3), the LAST rung of the
enrichment ladder: an exact-rational expression LEVEL (a dose-response) as an ORTHOGONAL axis on
top of the gate-type family (E1 klein4_mask / E2 boolean_dnf / E4 threshold).

The gate-type family decides IF a gene expresses (a BINARY switch). E3 adds the orthogonal axis:
HOW MUCH — a graded / analog LEVEL (real biology: expression is quantitative, not just on/off).

THE DESIGN (a NEW op, not a breaking change to gene_express):
  * ``gene_express`` (UNCHANGED) returns the binary expressed SET ``[(label, leaves), ...]``.
  * ``gene_express_levels`` (NEW) returns ``[(label, leaves, (num, den)), ...]`` — each EXPRESSED
    gene WITH its exact-rational LEVEL. Both reads coexist.

THE MECHANIC:
  * a GRADED gene (a NEW 0x64 'd'=dose cap) carries a per-condition SIGNED integer LEVEL-WEIGHT
    vector + a POSITIVE integer DENOMINATOR; its LEVEL is the reduced exact rational
    ``Σᵢ (level_weightᵢ · bit_i(cell_state)) / denom`` CLAMPED to [0, 1] (Class-K sign-branch,
    never abs; the fraction reduced by the Class-I gcd). The dose-response IS the gate — present
    iff LEVEL > 0.
  * a BINARY gene (plain 0x47 / klein4-mask 0x67 / boolean 0x62 / threshold 0x77) is the
    DEGENERATE {0, 1} graded case → LEVEL (1, 1) iff its gate passes, else absent.

Attested biology (ONE FACET — genes have other regulation too; NOT a reduction):
  * Alberts et al., *Molecular Biology of the Cell* 4th ed. (Garland Science, 2002), "How Genetic
    Switches Work" → "Gene Activator Proteins Work Synergistically", NCBI Bookshelf NBK26872
    (OA-verified first-hand): the joint effect of several activators on the transcription RATE is
    "not merely the sum ... but the product" — a graded, analog modulation of the expression LEVEL,
    not a binary switch.

Proven here (the ask's DoD):
  1. the graded level exact-rational (reduced fractions) — weights=[1,1,1,1], denom=4, popcount-2
     cell_state → level 1/2;
  2. binary genes → level 1 (in gene_express_levels) + present in gene_express;
  3. the gate composes — a graded gene is level 0/absent when its dose fails, the rational when it
     passes (the level>0 IS the gate); SIGNED (inhibitory) weights + clamp to [0, 1];
  4. THE THEOREM: cell_state modulates the LEVEL (same DNA, different cell_state → different LEVELS);
  5. the READ-TIME FILTER: the strand is byte-identical after gene_express_levels (no mutation);
  6. back-compat: rc131 / rc130 / rc129 / rc128 / plain genes read + behave IDENTICALLY in BOTH
     gene_express (binary) AND gene_express_levels (level 1);
  7. the bare strand SELF-DESCRIBES the level-weights + denom (no manifest);
  8. format v10 → v11 (a NEW 0x64 block kind); a v11 genome saves + pages back; pre-rc132 reads
     identically;
  9. Python==C byte-identical (the per-gene level (num, den) for graded genes + level 1 for binary).

numpy-free; NO abs() (the raw dose is signed exact Class-N; the clamp is the SIGN, never abs; the
gcd-reduce is Class-I over non-negative parts).
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


# condition bits used throughout: a = bit0, b = bit1, c = bit2, d = bit3
A, B, C, D = 1 << 0, 1 << 1, 1 << 2, 1 << 3


def _graded(weights, denom):
    return {"gate": "graded", "weights": list(weights), "denom": denom}


def _threshold(weights, theta):
    return {"gate": "threshold", "weights": list(weights), "threshold": theta}


def _boolean(dnf):
    return {"gate": "boolean", "dnf": list(dnf)}


def _levels(strand, one, cs):
    return {lab: lvl for lab, _leaves_, lvl in G.gene_express_levels(strand, one, cs)}


def _binary(strand, one, cs):
    return [lab for lab, _leaves_ in G.gene_express(strand, one, cs)]


# ── (1) the graded level exact-rational — reduced fractions ───────────────────

def test_graded_level_reduced_half():
    """The ask's headline case: weights=[1,1,1,1], denom=4, a popcount-2 cell_state → LEVEL 1/2
    (2/4 reduced by the Class-I gcd)."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _graded([1, 1, 1, 1], 4))])
    lv = _levels(strand, one, A | B)          # two of the first four bits present -> dose 2
    assert lv["g"] == (1, 2)                   # 2/4 reduced -> 1/2


def test_graded_level_sweeps_the_dose_response():
    """A denom=4 all-ones-weight gene: the LEVEL rises 0 -> 1/4 -> 1/2 -> 3/4 -> 1 as more
    conditions are present. Each fraction is REDUCED (2/4->1/2, 4/4->1)."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _graded([1, 1, 1, 1], 4))])
    assert "g" not in _levels(strand, one, 0)          # dose 0 -> off (absent)
    assert _levels(strand, one, A) == {"g": (1, 4)}    # 1/4
    assert _levels(strand, one, A | B) == {"g": (1, 2)}       # 2/4 -> 1/2
    assert _levels(strand, one, A | B | C) == {"g": (3, 4)}   # 3/4
    assert _levels(strand, one, A | B | C | D) == {"g": (1, 1)}  # 4/4 -> 1 (clamp/reduce)


def test_graded_level_arbitrary_reduced_fraction():
    """A non-power-of-two denom: weights=[1,1,1], denom=9, two conditions present -> 2/9 (already
    in lowest terms; gcd(2, 9) == 1)."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _graded([1, 1, 1], 9))])
    assert _levels(strand, one, A | B) == {"g": (2, 9)}
    assert _levels(strand, one, A | B | C) == {"g": (1, 3)}   # 3/9 -> 1/3 reduced


# ── (2) binary genes → level 1 in gene_express_levels; present in gene_express ─

def test_binary_genes_level_one_and_present_in_both():
    """Every binary gate-type (plain / klein4-mask / boolean / threshold) that PASSES is level
    exact-rational 1 = (1, 1) in gene_express_levels AND present in gene_express (the degenerate
    {0, 1} graded case)."""
    one = _one()
    genes = [
        ("plain", _leaves(1)),                                   # unregulated -> always
        ("act",   _leaves(1), A, 0),                             # klein4-mask activator = a
        ("bexpr", _leaves(1), _boolean([(A, 0)])),               # boolean: expresses iff a
        ("thr",   _leaves(1), _threshold([1, 1], 2)),            # threshold: a AND b (sum>=2)
    ]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    cs = A | B
    lv = _levels(strand, one, cs)
    assert lv == {"plain": (1, 1), "act": (1, 1), "bexpr": (1, 1), "thr": (1, 1)}
    # and each is present in the BINARY read
    assert set(_binary(strand, one, cs)) == {"plain", "act", "bexpr", "thr"}


def test_levels_and_binary_agree_exactly_over_prior_genes():
    """gene_express_levels(level == (1,1)) == gene_express EXACTLY, over a mix of every prior
    gate-type, across many cell_states — the two reads are the same on binary genes."""
    one = _one()
    genes = [
        ("p", _leaves(1)),
        ("reg", _leaves(1), B, A),                               # activator=b, repressor=a
        ("bool", _leaves(1), _boolean([(A, 0), (C, 0)])),        # a OR c
        ("thr", _leaves(1), _threshold([2, -1], 1)),             # 2a - b >= 1
    ]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    for cs in range(16):
        at_one = {lab for lab, lvl in _levels(strand, one, cs).items() if lvl == (1, 1)}
        assert at_one == set(_binary(strand, one, cs)), cs


# ── (3) the gate composes — level>0 is the gate; signed weights + clamp ────────

def test_zero_dose_absent_positive_dose_present():
    """The dose-response IS the gate: a graded gene with dose 0 is ABSENT (from BOTH ops); dose > 0
    is present at that rational (and expresses in the binary read too)."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _graded([1, 1], 4))])
    assert "g" not in _levels(strand, one, 0)          # dose 0 -> absent
    assert "g" not in _binary(strand, one, 0)          # binary reading: level 0 -> off
    assert _levels(strand, one, A) == {"g": (1, 4)}    # dose 1 -> 1/4
    assert _binary(strand, one, A) == ["g"]            # binary reading: level>0 -> on


def test_signed_inhibitory_weight_clamps_to_zero():
    """A NEGATIVE (inhibitory) level-weight REDUCES the dose; a non-positive dose clamps to level 0
    (absent). abs()-ing the dose would break this — the sign is load-bearing (Class-K)."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _graded([2, -5], 10))])
    assert _levels(strand, one, A) == {"g": (1, 5)}    # dose 2 -> 2/10 -> 1/5
    assert "g" not in _levels(strand, one, A | B)      # dose 2-5 = -3 -> clamp 0 -> absent
    assert "g" not in _levels(strand, one, B)          # dose -5 -> clamp 0 -> absent


def test_overshoot_dose_clamps_to_one():
    """A dose >= denom clamps to level 1 (fully on) — the upper Class-K clamp."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _graded([3, 3], 4))])
    assert _levels(strand, one, A) == {"g": (3, 4)}    # dose 3 -> 3/4
    assert _levels(strand, one, A | B) == {"g": (1, 1)}  # dose 6 >= 4 -> clamp to 1


# ── (4) THE THEOREM — cell_state modulates the LEVEL ──────────────────────────

def test_cell_state_modulates_the_level():
    """The op⊗operand theorem refined to a QUANTITY: SAME DNA, DIFFERENT cell_state → DIFFERENT
    expression LEVELS (not just a different on/off subset). A graded gene's level is a strictly
    increasing function of how much of its dose is present."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("morph", _leaves(1), _graded([1, 1, 1, 1], 4))])
    seen = [_levels(strand, one, cs).get("morph") for cs in (0, A, A | B, A | B | C, A | B | C | D)]
    assert seen == [None, (1, 4), (1, 2), (3, 4), (1, 1)]   # the graded dose-response
    # DIFFERENT cell_states genuinely give DIFFERENT levels (not a constant)
    present = [s for s in seen if s is not None]
    assert len(set(present)) == len(present)


# ── (5) the READ-TIME FILTER — the strand is byte-identical after ─────────────

def test_read_time_filter_strand_byte_identical():
    """gene_express_levels NEVER mutates the strand (biology reads the regulatory region, it does
    not rewrite the DNA). The strand is byte-identical after the call."""
    one = _one()
    genes = [("g", _leaves(2), _graded([1, 1, 1, 1], 4)),
             ("h", _leaves(1), _threshold([1, 1], 2)),
             ("p", _leaves(1))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    before = [hv.tobytes() for hv in strand]
    _ = G.gene_express_levels(strand, one, A | B)
    after = [hv.tobytes() for hv in strand]
    assert before == after


# ── (6) back-compat — prior-rc genes identical in BOTH ops ────────────────────

def test_back_compat_prior_rc_genes_identical_both_ops():
    """A chromosome of ONLY prior-rc genes (plain / rc129 klein4-mask / rc130 boolean / rc131
    threshold) behaves IDENTICALLY in gene_express (binary) and gene_express_levels (level 1) — the
    new op is additive, the old op UNCHANGED. Proven across all 16 cell_states."""
    one = _one()
    genes = [
        ("plain", _leaves(1)),
        ("k4", _leaves(1), A, B),                                # rc129 activator=a, repressor=b
        ("bool", _leaves(1), _boolean([(A, 0), (C, 0)])),        # rc130 a OR c
        ("thr", _leaves(1), _threshold([1, 1, 1], 2)),           # rc131 majority-of-3
    ]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    for cs in range(16):
        binset = set(_binary(strand, one, cs))
        levset = {lab for lab, lvl in _levels(strand, one, cs).items() if lvl == (1, 1)}
        assert binset == levset, cs
        # every prior gene that expresses is level exactly (1, 1) — never a sub-unit fraction
        for lab, lvl in _levels(strand, one, cs).items():
            assert lvl == (1, 1)


def test_back_compat_mixed_graded_and_prior_coexist():
    """A graded gene coexists with prior gate-types in ONE chromosome; each read agrees on the
    prior genes (level 1) and the graded gene carries its rational level."""
    one = _one()
    genes = [
        ("plain", _leaves(1)),
        ("thr", _leaves(1), _threshold([1, 1], 2)),
        ("grad", _leaves(2), _graded([1, 1, 1, 1], 4)),
    ]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    cs = A | B
    lv = _levels(strand, one, cs)
    assert lv["plain"] == (1, 1)
    assert lv["thr"] == (1, 1)                  # 1+1 = 2 >= 2
    assert lv["grad"] == (1, 2)                 # 2/4 -> 1/2
    # binary read: the graded gene is present (level>0), the prior genes unchanged
    assert set(_binary(strand, one, cs)) == {"plain", "thr", "grad"}


# ── (7) the bare strand SELF-DESCRIBES the weights + denom ─────────────────────

def test_bare_strand_self_describes_weights_and_denom():
    """A graded gene's weights + denom are recoverable from the BARE strand (no manifest) — the §44
    self-describing property. _graded_gene_spec reads them back exactly."""
    one = _one()
    weights, denom = [3, -2, 5, 1], 7
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _graded(weights, denom))])
    caps = [hv for hv in strand if G._cap_kind(hv) == G.GRADED_GENE_MARKER]
    assert len(caps) == 1
    gate_type, w, dn = G._graded_gene_spec(caps[0])
    assert gate_type == G.GATE_TYPE_GRADED
    assert w == weights and dn == denom


def test_graded_gene_reports_graded_gate_type():
    """A graded gene self-describes its gate_type (GATE_TYPE_GRADED = 3), distinct from the binary
    E1/E2/E4 gate-types — the ORTHOGONAL level axis."""
    one = _one()
    strand = G.chromosome(the_one=one, label="c",
                          genes=[("g", _leaves(1), _graded([1, 1], 2))])
    caps = [hv for hv in strand if G._cap_kind(hv) == G.GRADED_GENE_MARKER]
    assert G._gene_gate_type(caps[0]) == G.GATE_TYPE_GRADED
    assert G.GATE_TYPE_GRADED == 3
    assert G.GRADED_GENE_MARKER == 0x64


# ── (8) format v10 → v11; a v11 genome saves + pages; pre-rc132 reads identically ─

def test_format_bumped_to_v11():
    assert G.GENOME_FORMAT_VERSION == 11


def test_graded_genome_saves_v11_and_pages_back(tmp_path):
    """A genome carrying a graded gene saves at format_version 11, pages back gate-agnostically, and
    gene_express_levels reports the exact rational level on the loaded (from-disk) strand."""
    one = _one()
    genes = [("housekeeping", _leaves(1)),
             ("dose", _leaves(1, base=1), _graded([1, 1, 1, 1], 4))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    p = tmp_path / "g"
    man = G.genome_save(strand, p, one)
    assert man["format_version"] == 11                          # the v11 bump
    paged = G.genome_genes(p, "cell", the_one=one)
    assert [l for l, _ in paged] == ["housekeeping", "dose"]    # gate-agnostic recovery
    s2, o2, _ = G.genome_load(p)
    lv = _levels(s2, o2, A | B)
    assert lv["housekeeping"] == (1, 1)
    assert lv["dose"] == (1, 2)                                 # 2/4 -> 1/2 from disk


def test_pre_rc132_genome_reads_identically(tmp_path):
    """A genome built with ONLY pre-rc132 genes reads + behaves identically under the v11 writer —
    back-compat is STRUCTURAL (the read path is version-independent)."""
    one = _one()
    genes = [("p", _leaves(1)), ("thr", _leaves(1), _threshold([1, 1], 2))]
    strand = G.chromosome(the_one=one, label="cell", genes=genes)
    p = tmp_path / "g"
    G.genome_save(strand, p, one)
    s2, o2, _ = G.genome_load(p)
    # both ops agree with the in-memory strand
    assert _binary(s2, o2, A | B) == _binary(strand, one, A | B)
    assert _levels(s2, o2, A | B) == _levels(strand, one, A | B)


# ── (9) Python==C byte-identical (the per-gene level decision) ─────────────────

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not built")
def test_python_equals_c_graded_level():
    """The C peer srmech_genome_gene_express_levels computes the SAME reduced exact-rational level
    as the pure Python path, over a grid of graded weights / denom / cell_state (incl. signed
    weights + the clamp branches)."""
    dim = 128
    cases = [
        ([1, 1, 1, 1], 4),
        ([3, 3], 4),
        ([2, -5], 10),
        ([1, 1, 1], 9),
        ([5, 3, -2, 7], 11),
        ([0, 0], 4),
        ([100], 3),
    ]
    for weights, denom in cases:
        cap = G._pack_graded_gene("g", weights, denom, dim)
        for cs in range(1 << min(len(weights) + 1, 8)):
            c_level = _native.genome_gene_express_levels_c(cap.tobytes(), len(cap), cs)
            py_level = G._graded_level(weights, denom, cs)
            assert c_level == py_level, (weights, denom, cs, c_level, py_level)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not built")
def test_python_equals_c_binary_level_is_one():
    """The C peer returns level (1, 1) / (0, 1) for a BINARY gene exactly as the pure path (the
    degenerate {0, 1} case) — plain / regulatory / boolean / threshold."""
    dim = 128
    caps = [
        G._gene_cap("p", dim),
        G._pack_regulatory_gene("r", A, dim, repressor=B),
        G._pack_boolean_gene("b", [(A, 0), (C, 0)], dim),
        G._pack_threshold_gene("t", [1, 1, 1], 2, dim),
    ]
    for cap in caps:
        for cs in range(16):
            c_level = _native.genome_gene_express_levels_c(cap.tobytes(), len(cap), cs)
            expressed = G._gene_expresses(cap, cs)
            assert c_level == ((1, 1) if expressed else (0, 1)), (cap.tobytes()[:1], cs, c_level)


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library not built")
def test_native_overflow_defers_to_pure():
    """An int64 dose-accumulate OVERFLOW makes the native raise NativeGenomeError so the caller
    falls to the exact pure (arbitrary-precision) path — which still computes the correct clamped
    level."""
    dim = 128
    cap = G._pack_graded_gene("o", [(1 << 62), (1 << 62), (1 << 62)], 5, dim)
    with pytest.raises(_native.NativeGenomeError):
        _native.genome_gene_express_levels_c(cap.tobytes(), len(cap), 0b111)
    # the pure path handles it (huge dose >= denom -> clamp to 1)
    assert G._gene_level(cap, 0b111) == (1, 1)
