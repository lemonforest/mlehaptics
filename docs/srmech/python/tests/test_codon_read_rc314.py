"""rc314 — the CODON READ-LAYER prove-gates (C1–C5).

Biology reads the genome in CODONS (triplets — the genetic code); that reading
is a PROCESS the ribosome imposes over the stored strand, not stored substrate.
:func:`srmech.amsc.genome.codon_read` is therefore a PURE READ (stores nothing,
changes no format) and :func:`srmech.amsc.genome.codon_frame_monodromy` reads the
Z3 reading-frame monodromy of a circular strand.

Three distinct invariants are kept SEPARATE (C3):
  (a) the reading-frame phase  φ ∈ {0,1,2}  — a cyclic C3 (the ribosome window);
  (b) klein4 triality           — the base-axis order-3 automorphism;
  (c) the winding Lk            — the Q8 center-parity / SIGN BIT.

The 64 → 20(+stop) codon table is the MPR-attested Standard Genetic Code (NCBI
translation table 1), NEVER an inline invented dict (C5).

This test is numpy-free (it imports nothing that needs numpy) so it runs in the
numpy-ABSENT gate.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from srmech.amsc.genome import (
    CODON_BASES,
    codon_frame_monodromy,
    codon_read,
)
from srmech.math.hdc import klein4_triality_cycle
from srmech.amsc.q8 import q8_project_v4

# Base labelling of the read layer: coset 0->U/T, 1->C, 2->A, 3->G (CODON_BASES).
_B = {"U": 0, "T": 0, "C": 1, "A": 2, "G": 3}


def _codons(seq: str):
    """DNA/RNA string -> list of V4 base symbols (the codon-read input)."""
    return [_B[c] for c in seq]


# ─────────────────────────────────────────────────────────────────────────
# C1 — codon_read on KNOWN sequences gives the correct amino acids.
# ─────────────────────────────────────────────────────────────────────────

def test_c1_start_codon_atg_is_met():
    assert codon_read(_codons("ATG")) == "M"


def test_c1_three_stop_codons():
    assert codon_read(_codons("TAA")) == "*"
    assert codon_read(_codons("TAG")) == "*"
    assert codon_read(_codons("TGA")) == "*"


def test_c1_orf_reads_to_stop():
    # ATG GGG TAA  ->  Met Gly Stop
    assert codon_read(_codons("ATGGGGTAA")) == "MG*"


def test_c1_with_indices_matches_ncbi_index():
    protein, idx = codon_read(_codons("ATGTGGTAA"), with_indices=True)
    assert protein == "MW*"           # Met Trp Stop
    assert idx == [35, 15, 10]        # NCBI transl_table=1 codon indices


def test_c1_stop_at_stop_truncates():
    # stop_at_stop halts (inclusive) at the first stop.
    assert codon_read(_codons("ATGGGGTAAAAA"), stop_at_stop=True) == "MG*"
    # without it, the read runs the whole frame (AAA = Lys).
    assert codon_read(_codons("ATGGGGTAAAAA")) == "MG*K"


def test_c1_all_64_codons_cover_20_aas_plus_stop():
    seen = set()
    for b0 in range(4):
        for b1 in range(4):
            for b2 in range(4):
                seen.add(codon_read([b0, b1, b2]))
    assert "*" in seen                # stop present
    assert len(seen - {"*"}) == 20    # exactly 20 amino acids
    assert seen == set("ACDEFGHIKLMNPQRSTVWY*")


def test_c1_codon_bases_labelling():
    assert CODON_BASES == ("U", "C", "A", "G")


# ─────────────────────────────────────────────────────────────────────────
# C2 — winding-invariance: a Q8 genome (nonzero winding) and its q8_project_v4
# give BYTE-IDENTICAL codon_read output. The sign bit must not touch identity.
# ─────────────────────────────────────────────────────────────────────────

def test_c2_winding_does_not_touch_amino_acid_identity():
    base = _codons("ATGTGGTAAGGGCAT")           # V4 symbols in [0,4)
    # Set the Q8 CENTER SIGN BIT (+4) on an arbitrary subset -> nonzero winding.
    wound = [b + 4 if (i % 3 == 0) else b for i, b in enumerate(base)]
    assert any(x >= 4 for x in wound)            # genuinely wound
    assert list(q8_project_v4(wound)) == base    # projection strips the sign
    # BYTE-IDENTICAL across every reading frame.
    for phase in (0, 1, 2):
        assert codon_read(wound, phase=phase) == codon_read(base, phase=phase)


def test_c2_all_sign_patterns_agree():
    base = _codons("ATGAAACCCGGG")
    ref = codon_read(base)
    # Every one of the 2**len sign-bit patterns reads identically (spot-check a
    # deterministic spread rather than the full 4096).
    for mask in range(0, 1 << len(base), 7):
        wound = [b + 4 if (mask >> i) & 1 else b for i, b in enumerate(base)]
        assert codon_read(wound) == ref


# ─────────────────────────────────────────────────────────────────────────
# C3 — the three order-3 objects are provably DISTINCT.
#   phase (reading frame)  regroups the triplets;
#   klein4 triality        relabels the bases (same frame);
#   winding Lk (sign bit)  leaves the read INVARIANT.
# Three different behaviours over ONE constructed strand => separate invariants.
# ─────────────────────────────────────────────────────────────────────────

def test_c3_three_order3_objects_distinct():
    s = _codons("ATGTGG")                 # [2,0,3,2,3,3]

    # (a) reading-frame phase φ — a genuine cyclic C3; regroups the window.
    r0 = codon_read(s, phase=0)
    r1 = codon_read(s, phase=1)
    r2 = codon_read(s, phase=2)
    assert r0 != r1                       # the frame shift changes the read

    # (b) klein4 triality — the base-axis automorphism (order 3), SAME frame.
    t1 = list(klein4_triality_cycle(bytes(s)).tobytes())
    rt = codon_read(t1, phase=0)
    assert rt != r0                       # relabelled bases -> different aa
    assert rt != r1 and rt != r2          # NOT reproducible by any phase shift
    # triality is order 3: T^3 == identity (on the base axis).
    t2 = list(klein4_triality_cycle(bytes(t1)).tobytes())
    t3 = list(klein4_triality_cycle(bytes(t2)).tobytes())
    assert t3 == s

    # (c) winding Lk — lives in the Q8 sign bit; codon read is INVARIANT to it.
    wound = [b + 4 for b in s]            # flip every center sign -> new winding
    assert codon_read(wound, phase=0) == r0     # winding does NOT touch identity
    # ... yet the winding IS a real, separate quantity: the sign bits differ.
    assert [x >> 2 for x in wound] != [x >> 2 for x in s]

    # The three transformations act on genuinely different structure:
    #   phase   -> changes the read (frame regroup),
    #   triality-> changes the read differently (base relabel), and
    #   winding -> does not change the read at all.
    assert len({r0, r1, rt}) == 3


def test_c3_triality_is_not_a_frame_shift():
    # Over a longer strand, no phase of the original reproduces the triality read
    # (the two order-3 objects are independent, not two views of one thing).
    s = _codons("ATGTGGGGGCATAAA")
    tri = list(klein4_triality_cycle(bytes(s)).tobytes())
    rt = codon_read(tri, phase=0)
    assert rt not in {codon_read(s, phase=p) for p in (0, 1, 2)}


# ─────────────────────────────────────────────────────────────────────────
# C4 — frame-monodromy: codon_frame_monodromy returns L mod 3 on circular
# strands of known length; phase composes correctly around the loop.
# ─────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("length", [0, 1, 2, 3, 7, 9, 10, 11, 12, 100])
def test_c4_monodromy_is_len_mod_3(length):
    strand = ([2, 0, 3] * ((length // 3) + 1))[:length]
    assert codon_frame_monodromy(strand) == length % 3


def test_c4_monodromy_invariant_under_winding():
    base = _codons("ATGTGGTAAC")            # length 10 -> monodromy 1
    wound = [b + 4 if i % 2 else b for i, b in enumerate(base)]
    assert codon_frame_monodromy(base) == 1
    assert codon_frame_monodromy(wound) == 1


def test_c4_phase_composes_around_the_loop():
    # The frame monodromy is ADDITIVE around laps: going k times around a
    # circular strand shifts the reading frame by (k * L) mod 3. So
    # monodromy(k laps) == (k * monodromy(1 lap)) mod 3, and the frame CLOSES
    # back to 0 after 3 laps (or after 1 lap when 3 divides L).
    base = _codons("ATGTGGTAAC")            # L = 10, monodromy 1
    m1 = codon_frame_monodromy(base)
    assert m1 == len(base) % 3 == 1
    for k in range(1, 6):
        assert codon_frame_monodromy(base * k) == (k * m1) % 3
    assert codon_frame_monodromy(base * 3) == 0     # 3 laps always closes

    tri = _codons("ATGTGGTAA")              # L = 9, monodromy 0 (already closed)
    assert codon_frame_monodromy(tri) == 0
    assert codon_frame_monodromy(tri * 4) == 0


# ─────────────────────────────────────────────────────────────────────────
# C5 — attestation: the genetic-code datum passes MPRRecord attestation-block
# validation (all mandatory fields present, response_sha256 matches).
# ─────────────────────────────────────────────────────────────────────────

_DATUM = (
    Path(__file__).resolve().parent.parent
    / "srmech" / "amsc" / "attested" / "genetic_code" / "row.ndjson"
)


def _load_record():
    from srmech.amsc.format import read_ndjson
    rows = list(read_ndjson(_DATUM))
    assert len(rows) == 1
    return rows[0]


def test_c5_datum_exists_and_is_single_row():
    assert _DATUM.is_file()
    _load_record()


def test_c5_mpr_record_validates():
    from srmech.amsc.format import validate_mpr_record
    validate_mpr_record(_load_record())     # raises MPRValidationError on failure


def test_c5_all_mandatory_attestation_fields_present():
    from srmech.amsc.format import MANDATORY_ATTESTATION_FIELDS
    rec = _load_record()
    for field in MANDATORY_ATTESTATION_FIELDS:
        assert rec.attestation.get(field), f"missing attestation.{field}"


def test_c5_response_sha256_matches_source_bytes():
    from srmech.amsc.format import sha256_bytes
    rec = _load_record()
    source = rec.data["source_response"]
    assert sha256_bytes(source.encode("utf-8")) == rec.attestation["response_sha256"]


def test_c5_attestation_is_open_access_not_a_placeholder():
    rec = _load_record()
    # A real OA DOI (NCBI Taxonomy resource paper), a real NCBI source URL.
    assert rec.attestation["source_doi"] == "10.1093/database/baaa062"
    assert "ncbi.nlm.nih.gov" in rec.attestation["source_url"]
    assert rec.attestation["parser_version"].startswith("srmech ")
    # No zenodo/placeholder DOI (the fluent-domain-vocabulary failure mode).
    assert "placeholder" not in rec.attestation["source_doi"].lower()


def test_c5_table_comes_from_attested_datum_not_inline():
    # codon_read's table is parsed from the attested source_response; the parsed
    # ncbieaa must equal the ncbieaa field, and both must drive the same read.
    rec = _load_record()
    source = rec.data["source_response"]
    line = [ln for ln in source.splitlines() if ln.startswith("ncbieaa")][0]
    parsed = line.split('"')[1]
    assert parsed == rec.data["ncbieaa"]
    assert len(parsed) == 64
    # The read layer uses exactly this table.
    assert codon_read([2, 0, 3]) == parsed[35] == "M"


# ─────────────────────────────────────────────────────────────────────────
# Surface hygiene — bounds, empties, HV input.
# ─────────────────────────────────────────────────────────────────────────

def test_phase_out_of_range_raises():
    with pytest.raises(ValueError):
        codon_read([2, 0, 3], phase=3)


def test_short_and_empty_strands_read_empty():
    assert codon_read([]) == ""
    assert codon_read([2, 0]) == ""        # < 3 symbols -> no codon
    assert codon_read([2, 0, 3], phase=1) == ""   # frame runs off the end


def test_hv_input_reads_the_same():
    from srmech.amsc.hv import HV
    s = _codons("ATGTGGTAA")
    hv = HV.from_sequence(bytes(s), sectors=4)
    assert codon_read(hv) == codon_read(s) == "MW*"


# ─────────────────────────────────────────────────────────────────────────
# ADR-0009 multi-implementation parity — the C peer and the pure fallback are
# byte-identical over a spread of strands, phases, and the attested table.
# Skips (rather than passes vacuously) when the native lib is absent.
# ─────────────────────────────────────────────────────────────────────────

def test_native_equals_pure_codon_read():
    from srmech.amsc import _native
    from srmech.amsc.genome import (
        _codon_native_ready, _codon_read_native, _codon_read_pure,
        _genetic_code_table,
    )
    from srmech.amsc.q8 import q8_project_v4
    if not _codon_native_ready("srmech_genome_codon_read"):
        pytest.skip("native srmech_genome_codon_read not loaded")
    ncbieaa, _ = _genetic_code_table()
    # a deterministic spread of Q8 strands (bytes 0..7 -> winding included).
    for seed in range(0, 240, 7):
        n = (seed % 31)
        strand = bytes(((seed * 13 + j * 7) % 8) for j in range(n))
        proj = q8_project_v4(strand)
        for phase in (0, 1, 2):
            nat = _codon_read_native(proj, phase, ncbieaa)
            pure = _codon_read_pure(proj, phase, ncbieaa)
            assert nat == pure, (seed, phase, nat, pure)


def test_native_equals_pure_frame_monodromy():
    from srmech.amsc import _native
    from srmech.amsc.genome import _codon_native_ready, codon_frame_monodromy
    if not _codon_native_ready("srmech_genome_codon_frame_monodromy"):
        pytest.skip("native srmech_genome_codon_frame_monodromy not loaded")
    # codon_frame_monodromy already routes through the C peer when present; the
    # value must equal the closed-form len mod 3 for every length.
    for length in range(0, 50):
        strand = ([2, 0, 3] * ((length // 3) + 1))[:length]
        assert codon_frame_monodromy(strand) == length % 3
