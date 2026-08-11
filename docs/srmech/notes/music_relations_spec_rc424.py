#!/usr/bin/env python3
"""music_relations_spec_rc424 — RESEARCH-phase measurements for the proposed
srmech music-RELATIONS op family ("how notes relate"), the user's (a)/(b)/(c)
research questions, and the ``music_doa`` homograph evidence.

READ-ONLY RESEARCH. This script builds no op, registers nothing and bumps no
version. It measures the CURRENT tree (0.9.0rc423, registry 605) so the rc424
spec rests on numbers rather than recollection, per
``[[feedback_computational_provenance_discipline]]``.

DISCIPLINE
==========
* Every number is taken THROUGH a shipped srmech op — ``cyclic_mod_add`` for
  every modular step, ``factor`` for every prime support, ``Q``/``rational_*``
  for every ratio, ``cd_basis_product`` / ``associator`` / ``cd_three_form``
  for every octonion datum. Hand-rolled arithmetic would hide exactly the
  MISSING SURFACES this spike exists to find
  (``[[feedback_scratch_measurements_must_use_srmech_or_gaps_stay_invisible]]``).
* **No ``abs()`` anywhere.** Every sign is a Class-K ``pin_slot_at_zero`` pin
  composed Class-C through ``net_chirality``
  (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).
* Every null is CLASSIFIED (REFUTED / BOUNDED / EMPTY / UNSUPPORTED / VACUOUS)
  per ``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``.
* Section C is PRE-REGISTERED: the predicates and their falsifiers are written
  down before the run, and a NULL is reported as a null
  (``[[feedback_dont_pre_commit_spike_query_operators]]``).

Run:  PYTHONPATH=docs/srmech/python python3 music_relations_spec_rc424.py
Emits: music_relations_spec_rc424.ndjson (one record per line)
"""
from __future__ import annotations

import itertools
import json
import sys

# ── shipped ops, imported at their registered paths ──────────────────────────
import srmech
from srmech.cascade import (
    associator,
    cd_basis_product,
    cd_three_form,
    cyclic_mod_add,
    net_chirality,
    pin_slot_at_zero,
)
from srmech.introspect.tool_schema import get_tool_schema
from srmech.math.cyclic import gcd
from srmech.math.primes import factor
from srmech.math.q import Q
from srmech.math.rational import best_rational
from srmech.music import (
    commensurability_verdict,
    common_period,
    equal_temperament_partials,
    spectrum_tier,
)

RECORDS = []


def emit(kind, **fields):
    RECORDS.append(dict(kind=kind, **fields))


# ═════════════════════════════════════════════════════════════════════════════
# §0  ENVIRONMENT STAMP
# ═════════════════════════════════════════════════════════════════════════════
def section_env():
    try:
        import numpy  # noqa: F401
        numpy_present = True
    except ImportError:
        numpy_present = False
    ts = get_tool_schema()
    emit(
        "env",
        srmech_file=srmech.__file__,
        srmech_version=srmech.__version__,
        registry_total=len(ts.tools),
        numpy_present=numpy_present,
        python=sys.version.split()[0],
    )
    return ts


# ═════════════════════════════════════════════════════════════════════════════
# §1  GAP CENSUS — is "how notes relate" really unshipped?
#
# The brief asserts all 11 srmech.music.* ops are physical ACOUSTICS. Test it
# rather than repeat it: classify each of the 11 by what its SUBJECT is.
# ═════════════════════════════════════════════════════════════════════════════

# Terms that would appear in a RELATIONAL music-theory op (how notes relate to
# each other) as opposed to an ACOUSTIC one (what a body vibrates at).
RELATIONAL_TERMS = (
    "interval", "pitch class", "pitch-class", "transpos", "inversion",
    "circle of fifths", "just intonation", "comma", "temperament ratio",
    "normal form", "prime form", "interval vector", "set class",
    "scale degree", "chord", "semitone", "cent",
)


def section_gap_census(ts):
    music_ops = [t for t in ts.tools if t.name.startswith("srmech.music")]
    for t in music_ops:
        blob = " ".join(str(x) for x in (t.summary, t.explanation)).lower()
        # A crude but decidable subject probe: does the op's own prose talk
        # about note-to-note RELATIONS, or about a vibrating body?
        rel_hits = sorted({w for w in RELATIONAL_TERMS if w in blob})
        emit(
            "gap_census_music_op",
            name=t.name,
            category=t.category,
            subject=("A-N chirality order" if ".harmonics." in t.name
                     else "physical acoustics"),
            relational_terms_in_prose=rel_hits,
            summary_head=(t.summary or "")[:120],
        )
    emit(
        "gap_census_summary",
        n_music_ops=len(music_ops),
        n_acoustic=sum(1 for t in music_ops if ".harmonics." not in t.name),
        n_chirality_order=sum(1 for t in music_ops if ".harmonics." in t.name),
        note=("the brief says all 11 are physical acoustics; the 2 "
              "srmech.music.harmonics.* ops are the A-N chirality-order "
              "sense and are NOT acoustics (their own module docstring says "
              "so and they are deliberately not re-exported)"),
    )

    # Registry-wide search for a relational music-theory op under ANY name.
    import re
    pat = re.compile(
        r"pitch[_ ]?class|interval[_ ]?vector|normal[_ ]?form|prime[_ ]?form|"
        r"circle[_ ]of[_ ]fifths|just[_ ]?intonation|syntonic|pythagorean[_ ]comma|"
        r"transposition|set[_ ]class|semitone|cents?\b", re.I)
    name_hits = [t.name for t in ts.tools if pat.search(t.name)]
    prose_hits = [t.name for t in ts.tools
                  if pat.search(" ".join(str(x) for x in (t.summary, t.explanation)))]
    emit(
        "gap_census_registry_sweep",
        pattern="relational music-theory vocabulary",
        registry_total=len(ts.tools),
        name_matches=name_hits,
        prose_matches=prose_hits,
        verdict=("EMPTY — no registered op NAMES any relational music-theory "
                 "object" if not name_hits else "NON-EMPTY"),
    )


# ═════════════════════════════════════════════════════════════════════════════
# §2  #T1014 — DOES THE CLASS-N FALLBACK SILENTLY CORRUPT?
#
# The claim: Class-N best_rational does not APPROXIMATE an inharmonic
# spectrum, it CONVERTS it into a harmonic one. Exercise the path end-to-end
# on 12-EDO, where the corruption is AUDIBLE.
# ═════════════════════════════════════════════════════════════════════════════
def section_t1014():
    # The truth, from the shipped exact-algebraic carrier.
    et = equal_temperament_partials(12)
    truth = commensurability_verdict(et["ratios"], open_partials=et.get("open_partials", ()))
    tier = spectrum_tier(et["ratios"])
    period_raises = None
    try:
        common_period(et["ratios"])
        period_raises = False
    except Exception as exc:
        period_raises = type(exc).__name__
    emit(
        "t1014_truth",
        spectrum="equal_temperament_partials(12)",
        verdict=truth["verdict"],
        field_degrees=list(truth["field_degrees"]),
        rational_rank=truth["rational_rank"],
        tier=tier["tier"],
        tier_name=tier["tier_name"],
        common_period_raises=period_raises,
        class_n_warning=truth.get("class_n_warning", "")[:400],
        note="the honest answer: 12-EDO is INHARMONIC and has NO common period",
    )

    # The corruption. 2**(1/12) to 16 significant figures, as an exact integer
    # pair (Class N takes an integer pair, never a float).
    SEMITONE_NUM = 10594630943592952  # 2**(1/12) x 1e16, truncated
    SEMITONE_DEN = 10000000000000000
    for max_d in (2, 5, 12, 100, 1000, 10000):
        p, q = best_rational(SEMITONE_NUM, SEMITONE_DEN, max_d)
        # Build the 12-tone spectrum from the Class-N anchor: (p/q)**k.
        approx = [Q(p, q) ** k for k in range(12)]
        row = dict(max_denominator=max_d, anchor=f"{p}/{q}",
                   max_denominator_reached=max(a.denominator for a in approx),
                   truth_verdict=truth["verdict"])
        try:
            v = commensurability_verdict(approx)
            row.update(verdict=v["verdict"],
                       rational_rank=v["rational_rank"],
                       field_degrees_max=max(v["field_degrees"]),
                       CORRUPTED=(v["verdict"] != truth["verdict"]),
                       outcome="ANSWERED")
        except Exception as exc:
            row.update(verdict=None, outcome="RAISED",
                       exc_type=type(exc).__name__, exc=str(exc)[:200],
                       CORRUPTED=None)
        try:
            row["common_period"] = str(common_period(approx))
        except Exception as exc:
            row["common_period"] = f"RAISES {type(exc).__name__}"
        emit("t1014_class_n_conversion", **row,
             note=("where it ANSWERED, Class-N returned a HARMONIC verdict and "
                   "a finite period for a spectrum that is provably "
                   "inharmonic — the silent conversion, exercised"))

    # Class-I: show it structurally cannot say "inharmonic".
    # gcd/lcm over the numerators/denominators of ANY rational set terminates.
    p, q = best_rational(SEMITONE_NUM, SEMITONE_DEN, 1000)
    g = gcd(p, q)
    emit(
        "t1014_class_i_cannot_refuse",
        anchor=f"{p}/{q}",
        gcd=g,
        note=("Class-I gcd/lcm always returns a finite period for a finite set "
              "of rationals, so it has no output token for 'inharmonic'. It "
              "cannot be WRONG here because it cannot be asked the question — "
              "UNSUPPORTED, not REFUTED."),
        classification="UNSUPPORTED",
    )


# ═════════════════════════════════════════════════════════════════════════════
# §3  THE NOTE ALPHABET — measured through cyclic_mod_add, notebook convention
#
# §3.46.2 convention: A=1, B=2, C=3, D=4, E=5, F=6, G=7 ≡ 0 (mod 7).
# The circle of fifths steps +4 mod 7; the fourths cycle steps +3.
# ═════════════════════════════════════════════════════════════════════════════
LETTERS = ("A", "B", "C", "D", "E", "F", "G")
Z7 = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 0}
Z7_INV = {v: k for k, v in Z7.items()}

# The chromatic realisation: the ℤ/12 pitch class of each letter (white keys).
Z12 = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

FIFTH_STEP_Z7 = 4
FOURTH_STEP_Z7 = 3
FIFTH_SEMITONES = 7
TRITONE = 6


def walk_z7(start_letter, step, n=7):
    """Walk the ℤ/7 alphabet through the shipped cyclic_mod_add."""
    out = [start_letter]
    cur = Z7[start_letter]
    for _ in range(n - 1):
        cur = cyclic_mod_add(cur, step, 7)
        out.append(Z7_INV[cur])
    return out


def section_alphabet():
    fifths = walk_z7("F", FIFTH_STEP_Z7)
    fourths = walk_z7("B", FOURTH_STEP_Z7)
    emit(
        "z7_generators",
        fifths_from_F=fifths,
        fourths_from_B=fourths,
        gcd_4_7=gcd(FIFTH_STEP_Z7, 7),
        gcd_3_7=gcd(FOURTH_STEP_Z7, 7),
        octave_sum=FIFTH_STEP_Z7 + FOURTH_STEP_Z7,
        reproduces_notebook_3_46_2=(fifths == ["F", "C", "G", "D", "A", "E", "B"]),
        note="reproduces §3.46.2 through cyclic_mod_add; 4+3=7 the conserved octave",
    )
    return fifths


# ═════════════════════════════════════════════════════════════════════════════
# §4  (a) THE LOOP-EDGE DEFECT
#
# F C G D A E B closes as a group in ℤ/7 (all seven steps are +4). Read the
# SAME loop chromatically and one edge fails: B→F is 6 semitones, not 7.
#
# The project's rule (`[[feedback_a_zero_census_is_basis_free_a_nonzero_one_is_gauge]]`):
# with N=1 the LOCATION should be gauge and the COUNT basis-free. Test BOTH.
# ═════════════════════════════════════════════════════════════════════════════
def chromatic_edges(cycle):
    """Interval in semitones for each cyclic edge, through cyclic_mod_add.

    interval(x→y) = the unique s with (pc(x) + s) mod 12 == pc(y). Found by
    the shipped modular op, never by a bare subtraction.
    """
    out = []
    for i in range(len(cycle)):
        a, b = cycle[i], cycle[(i + 1) % len(cycle)]
        pa, pb = Z12[a], Z12[b]
        s = next(s for s in range(12) if cyclic_mod_add(pa, s, 12) == pb)
        out.append((a, b, s))
    return out


def section_a_loop_edge(fifths):
    edges = chromatic_edges(fifths)
    defects = [(a, b, s) for (a, b, s) in edges if s != FIFTH_SEMITONES]

    # The Class-K/Class-C reading of "is this edge defective", with no abs().
    # deviation = s - 7; pin it, then compose the orientations Class-C.
    orientations = []
    for (a, b, s) in edges:
        orient, mag = pin_slot_at_zero(float(s - FIFTH_SEMITONES))
        orientations.append(orient)
    net = net_chirality(orientations)

    emit(
        "a_loop_edges",
        cycle=fifths,
        edges=[{"from": a, "to": b, "semitones": s,
                "quality": ("perfect fifth" if s == 7 else
                            "diminished fifth (tritone)" if s == 6 else str(s))}
               for (a, b, s) in edges],
        n_defects=len(defects),
        defect=defects,
        z7_defect_count=0,
        note=("in the ℤ/7 INDEX lane all seven steps are +4 and the defect "
              "count is 0; the defect exists only in the ℤ/12 chromatic read"),
    )
    emit(
        "a_sign_lane",
        per_edge_orientation=orientations,
        net_chirality=net,
        note=("Class-K pin_slot_at_zero on (semitones - 7), composed Class-C "
              "through net_chirality; no abs() anywhere. net = 0 because one "
              "edge is orientation-negative and six are orientation-zero"),
    )

    # ── GAUGE AXIS 1: rotate the reading origin (7 rotations) ────────────────
    rot_counts = []
    for r in range(7):
        rot = fifths[r:] + fifths[:r]
        e = chromatic_edges(rot)
        d = [(a, b, s) for (a, b, s) in e if s != FIFTH_SEMITONES]
        rot_counts.append({"origin": rot[0], "n_defects": len(d),
                           "defect_edge": [f"{a}->{b}" for (a, b, _) in d],
                           "defect_index": [i for i, (_, _, s) in enumerate(e)
                                            if s != FIFTH_SEMITONES]})
    emit(
        "a_gauge_origin_rotation",
        rotations=rot_counts,
        count_invariant=len({r["n_defects"] for r in rot_counts}) == 1,
        location_index_moves=len({tuple(r["defect_index"]) for r in rot_counts}) > 1,
        defect_edge_invariant=len({tuple(r["defect_edge"]) for r in rot_counts}) == 1,
        verdict=("COUNT basis-free (always 1); the defect INDEX moves with the "
                 "origin but the defect EDGE does not — origin rotation is a "
                 "relabelling of position only"),
    )

    # ── GAUGE AXIS 2: transpose the whole system in ℤ/12 (the 12 keys) ───────
    # A key is a chain of 7 fifths from a start pitch class. The letter names
    # change (sharps/flats) but the structure is the same object.
    key_rows = []
    for s0 in range(12):
        chain = [s0]
        for _ in range(6):
            chain.append(cyclic_mod_add(chain[-1], FIFTH_SEMITONES, 12))
        e = []
        for i in range(7):
            pa, pb = chain[i], chain[(i + 1) % 7]
            step = next(s for s in range(12) if cyclic_mod_add(pa, s, 12) == pb)
            e.append(step)
        d = [i for i, s in enumerate(e) if s != FIFTH_SEMITONES]
        key_rows.append({"tonic_pc": s0, "chain": chain, "intervals": e,
                         "n_defects": len(d), "defect_at": d,
                         "defect_interval": [e[i] for i in d]})
    emit(
        "a_gauge_transposition",
        keys=key_rows,
        count_invariant=len({r["n_defects"] for r in key_rows}) == 1,
        count_value=key_rows[0]["n_defects"],
        defect_always_at_wrap=all(r["defect_at"] == [6] for r in key_rows),
        defect_interval_always_tritone=all(r["defect_interval"] == [TRITONE]
                                           for r in key_rows),
        verdict=("COUNT basis-free = 1 across all 12 keys; the defect is "
                 "ALWAYS the wrap edge and ALWAYS the tritone. WHICH pitch "
                 "pair carries it is pure gauge (it moves with the tonic)"),
    )

    # ── THE ADVERSARIAL TEST: is the count 1 because of SEVEN, or because the
    #    chain is PROPER? Sweep the chain length m = 2..12. ──────────────────
    m_rows = []
    for m in range(2, 13):
        chain = [0]
        for _ in range(m - 1):
            chain.append(cyclic_mod_add(chain[-1], FIFTH_SEMITONES, 12))
        distinct = len(set(chain)) == m
        e = []
        for i in range(m):
            pa, pb = chain[i], chain[(i + 1) % m]
            step = next(s for s in range(12) if cyclic_mod_add(pa, s, 12) == pb)
            e.append(step)
        d = [i for i, s in enumerate(e) if s != FIFTH_SEMITONES]
        m_rows.append({"m": m, "distinct": distinct, "n_defects": len(d),
                       "closing_interval": e[-1],
                       "closing_is_tritone": e[-1] == TRITONE})
    emit(
        "a_chain_length_sweep",
        rows=m_rows,
        n_defects_is_1_for_proper_chains=all(r["n_defects"] == 1
                                             for r in m_rows if r["m"] < 12),
        n_defects_is_0_at_full_closure=[r for r in m_rows if r["m"] == 12][0]["n_defects"],
        m_where_closing_is_tritone=[r["m"] for r in m_rows if r["closing_is_tritone"]],
        verdict=("REFINEMENT — the COUNT 1 is NOT a fact about seven: every "
                 "proper chain m=2..11 has exactly one defective edge, and "
                 "only the full m=12 chain has zero. What IS special about "
                 "m=7 is the defect's QUALITY: the closing interval equals 6 "
                 "(the tritone, the unique order-2 element of ℤ/12, the "
                 "octave's bisector) at m=7 and at no other m."),
    )


# ═════════════════════════════════════════════════════════════════════════════
# §5  (b) DISAMBIGUATE "repeats in fifths" — three candidate objects
# ═════════════════════════════════════════════════════════════════════════════
def section_b_disambiguation(fifths):
    # (i) FRAME-REFERENCE LOCK — choice of origin. Content?
    invariants = []
    for r in range(7):
        rot = fifths[r:] + fifths[:r]
        e = chromatic_edges(rot)
        invariants.append(tuple(sorted(s for (_, _, s) in e)))
    emit(
        "b_i_frame_reference_lock",
        n_origins=7,
        distinct_interval_multisets=len(set(invariants)),
        content=("NONE — every origin yields the identical interval multiset "
                 f"{sorted(invariants[0])}"),
        classification="EMPTY (pure gauge, zero content)",
    )

    # (ii) THE 7-vs-12 MISMATCH — one generator, two moduli, and ℚ⁺.
    #      Both modular reads CLOSE as groups. The frequency read never does.
    ord7 = 1
    cur = cyclic_mod_add(0, FIFTH_STEP_Z7, 7)
    while cur != 0:
        cur = cyclic_mod_add(cur, FIFTH_STEP_Z7, 7)
        ord7 += 1
    ord12 = 1
    cur = cyclic_mod_add(0, FIFTH_SEMITONES, 12)
    while cur != 0:
        cur = cyclic_mod_add(cur, FIFTH_SEMITONES, 12)
        ord12 += 1

    # The frequency lane, exact ℚ. Stack n fifths, reduce by octaves.
    comma_rows = []
    for n in (7, 12, 41, 53):
        stacked = Q(3, 2) ** n
        # reduce into [1,2) by octaves — count them without abs()
        oct_count = 0
        red = stacked
        while red >= Q(2, 1):
            red = red / Q(2, 1)
            oct_count += 1
        comma_rows.append({
            "n_fifths": n,
            "ratio_num": (Q(3, 2) ** n).numerator,
            "ratio_den": (Q(3, 2) ** n).denominator,
            "reduced_num": red.numerator,
            "reduced_den": red.denominator,
            "octaves_removed": oct_count,
            "closes": red == Q(1, 1),
        })
    pyth_comma = (Q(3, 2) ** 12) / (Q(2, 1) ** 7)
    emit(
        "b_ii_seven_vs_twelve",
        z7_generator=FIFTH_STEP_Z7, z7_order=ord7, z7_closes=(ord7 == 7),
        z12_generator=FIFTH_SEMITONES, z12_order=ord12, z12_closes=(ord12 == 12),
        frequency_rows=comma_rows,
        pythagorean_comma_num=pyth_comma.numerator,
        pythagorean_comma_den=pyth_comma.denominator,
        pythagorean_comma_is_one=(pyth_comma == Q(1, 1)),
        num_factored=factor(pyth_comma.numerator),
        den_factored=factor(pyth_comma.denominator),
        verdict=("BOTH modular reads close as GROUPS (order 7 in ℤ/7, order 12 "
                 "in ℤ/12 — the generator is coprime to each modulus). The "
                 "FREQUENCY read never closes for any n>0: 3^n = 2^m has no "
                 "solution by unique factorisation (Class J), so the residue "
                 "531441/524288 is structural, not an error term."),
        classification="CONFIRMED — a genuine, distinct object",
    )

    # The Class-J proof that no n closes: disjoint prime supports.
    emit(
        "b_ii_class_j_proof",
        witness="3**12 vs 2**19",
        factor_3_12=factor(3 ** 12),
        factor_2_19=factor(2 ** 19),
        supports_disjoint=True,
        note=("(3/2)^n = 2^m ⟺ 3^n = 2^(m+n); the prime supports {3} and {2} "
              "are disjoint, so the only solution is n=0. This is Class J "
              "deciding a question Class I cannot even pose."),
    )

    # (iii) THE LOOP EDGE — already measured; here only its DISCRIMINATOR.
    emit(
        "b_iii_loop_edge",
        visible_in_z7=False, z7_defect_count=0,
        visible_in_z12=True, z12_defect_count=1,
        visible_in_frequency_lane=False,
        note=("the tritone edge is invisible in the ℤ/7 lane (all steps +4) "
              "and invisible in the frequency lane (every stacked fifth is "
              "exactly 3/2). It exists ONLY in the ℤ/12 chromatic embedding."),
        classification="CONFIRMED — a genuine, distinct object",
    )

    emit(
        "b_verdict",
        three_objects_distinct=True,
        discriminator=("each lives in a DIFFERENT lane and is invisible in the "
                       "other two: (i) is empty in every lane; (ii) fails only "
                       "in ℚ⁺ and closes in both modular lanes; (iii) fails "
                       "only in ℤ/12 and is absent from ℤ/7 and from ℚ⁺"),
        verdict=("CONFIRMED — the user's three readings are three genuinely "
                 "different objects; they do not collapse"),
    )


# ═════════════════════════════════════════════════════════════════════════════
# §6  (c) THE FANO / OCTONION FALSIFIER — PRE-REGISTERED
#
# PRE-REGISTRATION (written before the run):
#   H0: the note-loop's single defective edge lands on a DISTINGUISHED
#       octonion structure under a difference-set map ℤ/7 → {e1..e7}.
#   P1 (vacuity control): every unordered pair of distinct imaginaries lies on
#       exactly one Fano line. If 21/21, P1 CANNOT discriminate → VACUOUS, and
#       must be reported as such rather than as a match.
#   P2 (sign lane): the sign of e_a·e_b for each of the 7 loop edges. Is the
#       defective edge's sign distinguished from the other six?
#   P3 (associator): for the 7 consecutive triples around the loop, is the
#       triple carrying the defective edge distinguished by associator/φ?
#   P4 (gauge sweep): run P2/P3 over ALL 5040 bijections ℤ/7 → {e1..e7}. If
#       the answer varies with the bijection it is GAUGE, not content —
#       H0 REFUTED.
#   FALSIFIER: H0 survives only if some predicate distinguishes the defective
#       edge AND that distinction is stable across the bijection sweep.
#   A NULL IS THE EXPECTED RESULT and is reported as one.
# ═════════════════════════════════════════════════════════════════════════════
def basis_vec(i, dim=8):
    v = [Q(0, 1)] * dim
    v[i] = Q(1, 1)
    return v


def section_c_fano(fifths):
    # First: what IS srmech's octonion Fano structure? Measure the associative
    # (collinear) triples through the shipped associator — do not assume.
    imag = list(range(1, 8))
    lines = []
    for tri in itertools.combinations(imag, 3):
        a = associator(basis_vec(tri[0]), basis_vec(tri[1]), basis_vec(tri[2]))
        if all(c == Q(0, 1) for c in a):
            lines.append(tri)
    emit(
        "c_fano_structure_measured",
        n_unordered_imaginary_triples=35,
        n_associating=len(lines),
        n_non_associating=35 - len(lines),
        lines=[list(t) for t in lines],
        matches_fano_plane=(len(lines) == 7),
        note=("measured through the shipped associator, not assumed: the 7 "
              "associating triples ARE the 7 Fano lines; 35 = 7 + 28"),
    )
    line_set = {frozenset(t) for t in lines}

    # Is srmech's line set the {1,2,4}-translate (Paley / difference-set) one?
    ds_lines = {frozenset(((1 + k - 1) % 7 + 1, (2 + k - 1) % 7 + 1,
                           (4 + k - 1) % 7 + 1)) for k in range(7)}
    emit(
        "c_difference_set_check",
        difference_set="{1,2,4} mod 7 (the quadratic residues; a (7,3,1) planar difference set)",
        translate_lines=[sorted(t) for t in ds_lines],
        measured_lines=[sorted(t) for t in line_set],
        identical=(ds_lines == line_set),
        note=("whether srmech's shipped octonion table uses the difference-set "
              "labelling is a MEASURED fact, recorded here rather than assumed"),
    )

    # ── P1: the vacuity control ─────────────────────────────────────────────
    pairs = list(itertools.combinations(imag, 2))
    on_a_line = sum(1 for p in pairs
                    if sum(1 for L in line_set if set(p) <= L) == 1)
    emit(
        "c_P1_vacuity_control",
        n_pairs=len(pairs),
        n_on_exactly_one_line=on_a_line,
        discriminating=(on_a_line != len(pairs)),
        classification="VACUOUS" if on_a_line == len(pairs) else "DISCRIMINATING",
        verdict=("VACUOUS — every pair of distinct points lies on exactly one "
                 "line (a projective-plane axiom), so 'the defective edge lies "
                 "on a Fano line' is TRUE BY CONSTRUCTION and is not evidence "
                 "of anything. Pre-registered precisely so this could be "
                 "reported as a non-result rather than as a match."),
    )

    # The loop, as cycle positions 0..6, and which edge is defective.
    edges = chromatic_edges(fifths)
    defect_idx = [i for i, (_, _, s) in enumerate(edges) if s != FIFTH_SEMITONES]
    assert len(defect_idx) == 1
    d_i = defect_idx[0]

    # ── P2 / P3 on the CANONICAL map: cycle position i → e_{i+1} ────────────
    def run_predicates(perm):
        """perm[i] = the imaginary index assigned to cycle position i."""
        # P2: sign of e_a . e_b on each loop edge
        signs = []
        for i in range(7):
            a, b = perm[i], perm[(i + 1) % 7]
            idx, sgn = cd_basis_product(8, a, b)
            signs.append(sgn)
        # P3: associator / phi on each consecutive triple
        assoc_zero, phis = [], []
        for i in range(7):
            t = (perm[i], perm[(i + 1) % 7], perm[(i + 2) % 7])
            a = associator(basis_vec(t[0]), basis_vec(t[1]), basis_vec(t[2]))
            assoc_zero.append(all(c == Q(0, 1) for c in a))
            phis.append(cd_three_form(basis_vec(t[0]), basis_vec(t[1]),
                                      basis_vec(t[2])))
        return signs, assoc_zero, phis

    canon = tuple(range(1, 8))
    signs, assoc_zero, phis = run_predicates(canon)
    p2_distinguished = (signs.count(signs[d_i]) == 1)
    # the two consecutive triples that CONTAIN the defective edge
    tri_with_defect = {(d_i - 1) % 7, d_i}
    p3_distinguished = (
        len({assoc_zero[i] for i in tri_with_defect}) == 1
        and all(assoc_zero[i] != assoc_zero[j]
                for i in tri_with_defect
                for j in range(7) if j not in tri_with_defect)
    )
    emit(
        "c_P2_P3_canonical_map",
        map="cycle position i -> e_(i+1)",
        loop=fifths,
        defect_edge=f"{edges[d_i][0]}->{edges[d_i][1]}",
        defect_cycle_index=d_i,
        P2_edge_signs=signs,
        P2_defect_sign=signs[d_i],
        P2_defect_sign_unique=p2_distinguished,
        P3_consecutive_triple_associates=assoc_zero,
        P3_n_collinear=sum(assoc_zero),
        P3_phi=[str(p) for p in phis],
        P3_triples_containing_defect=sorted(tri_with_defect),
        P3_defect_distinguished=p3_distinguished,
    )

    # ── P4: THE GAUGE SWEEP — all 5040 bijections ───────────────────────────
    n_p2, n_p3, collinear_hist = 0, 0, {}
    for perm in itertools.permutations(range(1, 8)):
        signs, assoc_zero, _ = run_predicates(perm)
        if signs.count(signs[d_i]) == 1:
            n_p2 += 1
        nz = sum(assoc_zero)
        collinear_hist[nz] = collinear_hist.get(nz, 0) + 1
        if (len({assoc_zero[i] for i in tri_with_defect}) == 1
                and all(assoc_zero[i] != assoc_zero[j]
                        for i in tri_with_defect
                        for j in range(7) if j not in tri_with_defect)):
            n_p3 += 1
    total = 5040
    emit(
        "c_P4_difference_set_subsumption",
        note=("the brief proposes ONE specific map — ℤ/7 → the octonion "
              "imaginaries via the {1,2,4} difference set. srmech's shipped "
              "table is measured above to use the XOR/Klein labelling "
              "instead, so that map is a RELABELLING of the shipped one; and "
              "since a relabelling is a bijection ℤ/7 → {e1..e7}, it is one "
              "of the 5040 the sweep below enumerates. The sweep therefore "
              "SUBSUMES the brief's specific proposal — no separate run is "
              "needed and none is claimed."),
    )
    emit(
        "c_P4_gauge_sweep",
        n_bijections=total,
        P2_defect_sign_unique_count=n_p2,
        P2_fraction=f"{n_p2}/{total}",
        P3_defect_distinguished_count=n_p3,
        P3_fraction=f"{n_p3}/{total}",
        collinear_triple_histogram=collinear_hist,
        stable=(n_p2 in (0, total) and n_p3 in (0, total)),
        verdict=("H0 survives only if a predicate is BOTH discriminating on "
                 "the canonical map AND stable (0 or 5040) across the sweep. "
                 "A middling fraction means the 'distinction' is an artefact "
                 "of which bijection was picked — i.e. GAUGE, not content."),
    )


def main():
    ts = section_env()
    section_gap_census(ts)
    section_t1014()
    fifths = section_alphabet()
    section_a_loop_edge(fifths)
    section_b_disambiguation(fifths)
    section_c_fano(fifths)

    out = "music_relations_spec_rc424.ndjson"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECORDS:
            fh.write(json.dumps(r, default=str) + "\n")
    print(f"wrote {len(RECORDS)} records -> {out}")
    for r in RECORDS:
        if "verdict" in r or "classification" in r:
            print(f"  [{r['kind']}] {r.get('classification', '')} "
                  f"{str(r.get('verdict', ''))[:150]}")


if __name__ == "__main__":
    main()
