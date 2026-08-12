#!/usr/bin/env python3
"""P7 — the FIVE attested chart families, and the one that is not a chart
(rc426 research spike, read-only).

Why this exists
===============
P5 modelled two chart families (positional / differential) as a structural
guess.  The sourcing round returned **five** attested families, one of which
the carrier+chart design does not cover at all.  This script encodes the
taxonomy WITH its per-claim sourcing tier attached, and measures which
families are charts of the interval carrier and which are not.

⚠️ **SOURCING DISCIPLINE.** Every tradition claim below carries the tier it
was verified at.  The person who directed this work states plainly that they
read only Western notation, so an unverified claim about a living tradition
is the exact failure this project exists to prevent — and getting a
non-Western system wrong would privilege Western notation by default, which
is the one outcome the design is trying to avoid.  Tiers:

    VERIFIED-SELF the PDF was fetched and its text extracted and grepped IN
                  THIS SESSION by the author of this script — the strongest
                  tier here, and the only one not taken on report
    VERIFIED-OA   a source document was read (by a delegated reader)
    SECONDARY-OA  a readable OA source asserts it
    EXPERT-WEB    expert/institutional site, not peer-reviewed
    UNSOURCED     NOT verified — never stated as fact

⚠️ **TWO ROWS IN AN EARLIER VERSION OF THIS TABLE WERE WRONG, AND THE ERROR
WAS IN THIS ARTIFACT, NOT IN AN UPSTREAM SOURCE.** A second, independent
sourcing pass disagreed with the first about gongche and about kepatihan, so
the contested citation was fetched and its text extracted directly
(``docs/srmech/notes/`` provenance: the extractor is 25 lines of zlib over
FlateDecode streams; both PDFs were grepped, not summarised). Result:

* **Tse & Wong (2020) is REAL and correctly cited** — *"Analytical Approaches
  to World Music, Vol. 8, No. 2. Published December 7, 2020. Metrical
  Structure and Freedom in Qin Music of the Chinese Literati, Chun-Yan Tse
  and Chun-Fung Wong"* (verbatim from the extracted text). But its subject is
  METRICAL structure, and **it does not support the gongche claims** that
  were attributed to it: gongche appears only in a passing mention that
  ban/yan pulses are marked "by circles and dots ... adjacent to musical
  notes in gongche notation". The gongche row is therefore **downgraded to
  UNSOURCED**, which is also what the second pass independently reported.
* **The jianzipu STATEFULNESS rule is ABSENT from BOTH cited sources.**
  Grepped for persist / inherit / carry over / previous character /
  preceding character / omitted / abbreviat across 417 KB of extracted text
  from Eiso Chan, L2/22-206 (which IS real: *"Proposal to add 38 characters
  used for the Chinese traditional musical notation to UAX #45"*,
  2022-09-19) — **zero hits** — and absent from Tse & Wong likewise. See
  F24, which is reframed as a CONDITIONAL structural result rather than a
  measurement of an attested rule.

What Tse & Wong DOES support, verbatim and self-extracted: *"the tablature
score used for the qin notates the fingering. Each fingering notation is
formed by combining simplified components of Chinese characters and numerals
to indicate finger movement and position. ... By following these fingering
instructions, the player produces a musical note."* That is the
INSTRUMENT-ACTION family, and it is now the best-attested row in the table.

Pre-registered falsifiers
=========================
F22 Which families are charts of the INTERVAL carrier, i.e. a symbol plus a
    declared reference determines a carrier value?
F23 The ACTION families: is the action->pitch map a chart at all?  Measure
    injectivity in BOTH directions.  (Guitar tablature's pitch->tab
    one-to-many-ness is SOURCED, so this is a check against a source, not a
    free invention.)
F24 **THE STATEFUL FAMILY.**  Jianzipu characters may omit the left-hand half,
    meaning "position persists from the previous character" (VERIFIED-OA).
    So the symbol->carrier map is NOT a function of the symbol.  Measure it:
    the same symbol sequence read from two different starting states must
    produce different carrier sequences.  If it does, the object is a
    TRANSDUCER, not a chart, and the atlas language does not reach it.
NEG A stateless chart must NOT show the F24 effect.

Run:
    PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/_p7_chart_families_sourced_rc426.py
"""
from __future__ import annotations

import json
import os
import sys

import srmech
from srmech.cascade import cyclic_mod_add

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_p7_chart_families_sourced_rc426.ndjson")
RECS = []


def emit(**kw):
    kw.setdefault("srmech_version", srmech.__version__)
    RECS.append(kw)


# ══════════════════════════════════════════════════════════════════════════
# THE TAXONOMY, with per-row sourcing.  This is a DATA TABLE, deliberately —
# the structural claim is what this script measures; the tradition claims are
# carried as attested strings and are NOT measured by anything here.
# ══════════════════════════════════════════════════════════════════════════
FAMILIES = [
    {
        "family": "DIFFERENTIAL (first-difference)",
        "atoms_denote": "a signed step-count from the PREVIOUS note",
        "reference_device": "an explicit origin declaration",
        "is_chart_of_interval_carrier": True,
        "instances": [{
            "name": "Byzantine neumes (psaltic)",
            "claim": "quantitative signs 'designate the number of degrees "
                     "covered by each ascending or descending shift'; the "
                     "MARTYRIA declares genus, echos and the starting note",
            "tier": "VERIFIED-OA",
            "source": "Skoulios, Markos. 'Modern theory and notation of "
                      "Byzantine chanting tradition — A Near Eastern "
                      "musicological perspective.' NEMO-Online 1/1 (Nov "
                      "2012): 19-38.",
            "caveat": "72 dodekatemoria are NOMINAL values that practice "
                      "deviates from — the same theory/practice gap as "
                      "maqam. 'Byzantine = 72-EDO' is an idealisation. "
                      "⚠️ TWO REFINEMENTS from a second sourcing pass: (a) "
                      "Skoulios calls the system CONTEXTUALIZED rather than "
                      "purely intervallic — sign realisation depends on "
                      "phrase, rhythm and mode, so it is intervallic AND "
                      "context-sensitive; (b) pre-1814 layers were "
                      "STENOGRAPHIC, the singer realising them by learned "
                      "rules (Conomos, GOARCH School of Byzantine Music). "
                      "The New Method made an already-intervallic system "
                      "more EXPLICIT; it did not make it intervallic.",
        }],
    },
    {
        "family": "SCALE-DEGREE (interval-from-a-declared-origin)",
        "atoms_denote": "a position WITHIN a declared mode",
        "reference_device": "a written or named tonic/mode declaration",
        "is_chart_of_interval_carrier": True,
        "instances": [
            {"name": "Jianpu 简谱",
             "claim": "digits 1-7 are scale degrees, movable, with a written "
                      "key declaration '1=C' at the head of the score",
             "tier": "VERIFIED-OA",
             "source": "ANU CCME; TablEdit manual (mechanics)",
             "caveat": "⚠️ NOT a good example of 'non-Western'. Genealogy "
                       "VERIFIED: Rousseau 1742 -> Galin-Paris-Cheve -> "
                       "L. W. Mason in Meiji Japan (from 1880) -> Chinese "
                       "students c.1905-12. Zhang, Na. PhD, Universite "
                       "Paris-Saclay, 15 Dec 2016, HAL tel-04190628 "
                       "(metadata verified; body NOT read)."},
            {"name": "Gongche 工尺譜",
             "claim": "NOTHING IS CLAIMED. An earlier version of this row "
                      "asserted movable solmization degrees and skeletal "
                      "status on the authority of Tse & Wong (2020). Direct "
                      "extraction of that PDF shows it mentions gongche "
                      "ONLY in passing, for ban/yan pulse marks — it does "
                      "not support the pitch claims at all. A second "
                      "independent sourcing pass also returned gongche as "
                      "entirely unverified.",
             "tier": "UNSOURCED",
             "source": "NONE. The previously cited source was checked "
                       "directly and does not support the claim.",
             "caveat": "This row is retained as an EXPLICIT GAP rather than "
                       "deleted, so the table cannot silently look complete. "
                       "Anything downstream that needs gongche must source "
                       "it first."},
            {"name": "Sargam (Hindustani and Carnatic)",
             "claim": "RELATIVE; 'Sa, the tonic, can be any frequency'. "
                      "Hindustani: the tonic is an attribute of the "
                      "PERFORMER, not of the piece. Reference device is the "
                      "tanpura/tambura DRONE — an acoustic object, not a "
                      "written symbol",
             "tier": "VERIFIED-OA",
             "source": "Gulati, MSc, MTG-UPF 2012; Koduri et al., ISMIR "
                       "2011; Ranjani & Sreenivas, arXiv:1711.11357",
             "caveat": "⚠️ The 22-shruti question is a LIVE scholarly "
                       "DISAGREEMENT with several competing schemes "
                       "(Western Compilation / Deval / Nagoji Row), none "
                       "matching experiment well; Rao & van der Meer call "
                       "explaining contemporary intonation via the 22 'a "
                       "meaningless endeavour'. Reported as disagreement, "
                       "NOT resolved. ⚠️ 'Movable' needs BOTH halves or it "
                       "is misleading: the artist CHOOSES the tonic (Gulati "
                       "et al.), and it then remains FIXED throughout an "
                       "entire concert (Schachter, MTO 21/4, 2015). "
                       "Quoting either half alone misrepresents it."},
            {"name": "Arabic maqam / ajnas",
             "claim": "ajnas are defined by intervals 'which don't change "
                      "when transposed'",
             "tier": "EXPERT-WEB",
             "source": "MaqamWorld (Johnny Farraj), companion to Farraj & "
                       "Abu Shumays, Inside Arabic Music, OUP 2019",
             "caveat": "⚠️ 24-tone equal division is a NOMENCLATURE, not a "
                       "realised tuning — 'the Arabic half-flat and "
                       "half-sharp symbols do not mean exact quartertones'. "
                       "⚠️ The '1932 Cairo Congress' date for staff "
                       "adoption is WRONG: staff notation entered via "
                       "French-instructed Egyptian military schools in the "
                       "EARLY 19th c. via French-instructed Egyptian "
                       "military schools — BUT this is PROVISIONAL: the "
                       "Popper source (PhD, UCSB 2019, eScholarship "
                       "qt80x2c647) was located only as a snippet, its PDF "
                       "being too large to fetch. The 1932 date is refuted; "
                       "the replacement date is not yet attested. "
                       "⚠️ An older ABJAD notation existed — and al-Farabi "
                       "specifically IS sourced: Camprubi, M., 'Arabic "
                       "Music Theory and Manuscript Studies: Greek Notation "
                       "in al-Farabi's Great Book on Music?', History of "
                       "Music Theory (SMT IG & AMS SG), 10 Apr 2022. The "
                       "wider chain (al-Kindi, Ibn Sina, al-Urmawi) is "
                       "SECONDARY at best. ⚠️ Do NOT overstate the "
                       "24-tone-is-theoretical point from Bozkurt et al. "
                       "(JNMR 38/1, 2009): that paper RANKS which models "
                       "conform best, it does not assert blanket "
                       "divergence."},
        ],
    },
    {
        "family": "ABSOLUTE-POSITION",
        "atoms_denote": "a position on a grid, read against a declared "
                        "reference",
        "reference_device": "THE CLEF",
        "is_chart_of_interval_carrier": True,
        "instances": [{
            "name": "Western staff notation",
            "claim": "'A clef indicates which pitches are assigned to the "
                     "lines and spaces on a staff'; the C-clef 'locates C4 "
                     "regardless of what line it is placed upon'; G and F "
                     "clefs 'were also once moveable'",
            "tier": "VERIFIED-OA",
            "source": "LibreTexts Open Music Theory; Ewell & "
                      "Schmidt-Jones (CC BY)",
            "caveat": "'Absolute' is absolute-relative-to-a-DECLARED-"
                      "STANDARD: the pitch standard was unstable until the "
                      "20th c. (Handel A=423, Mozart A=422). So even the "
                      "reference chart's reference is a convention.",
        }],
    },
    {
        "family": "INSTRUMENT-ACTION",
        "atoms_denote": "an ACTION on an instrument; pitch is an OUTPUT",
        "reference_device": "the instrument's tuning / named mode",
        "is_chart_of_interval_carrier": False,
        "instances": [
            {"name": "Jianzipu 減字譜 (guqin)",
             "claim": "VERBATIM, self-extracted: 'the tablature score used "
                      "for the qin notates the fingering. Each fingering "
                      "notation is formed by combining simplified "
                      "components of Chinese characters and numerals to "
                      "indicate finger movement and position. ... By "
                      "following these fingering instructions, the player "
                      "produces a musical note.' Also verbatim: rhythm is "
                      "not notated, and lost pieces are reconstructed "
                      "through dapu.",
             "tier": "VERIFIED-SELF",
             "source": "Tse Chun-Yan & Wong Chun-Fung, 'Metrical Structure "
                       "and Freedom in Qin Music of the Chinese Literati', "
                       "Analytical Approaches to World Music 8/2 (pub. 7 "
                       "Dec 2020) — PDF fetched and text extracted in "
                       "session. Eiso Chan, Unicode L2/22-206, 'Proposal to "
                       "add 38 characters used for the Chinese traditional "
                       "musical notation to UAX #45' (2022-09-19) — also "
                       "fetched and extracted; confirms compound "
                       "left-hand/right-hand characters.",
             "caveat": "⚠️ The STATEFULNESS rule is **UNSOURCED** — see "
                       "F24. It is ABSENT from both of these documents "
                       "(grepped, 0 hits). Pitch-as-output IS attested; "
                       "position-inheritance is NOT."},
            {"name": "Lute tablature",
             "claim": "'a purely prescriptive form of notation... it merely "
                      "provides the actions a player must take'",
             "tier": "VERIFIED-OA",
             "source": "Dalitz, Christoph & Crawford, Tim. Phoibos 2/2013: "
                       "167-185"},
            {"name": "Guitar tablature",
             "claim": "numbers on 6 lines = fret on string; pitch->tab is "
                      "ONE-TO-MANY",
             "tier": "VERIFIED-OA",
             "source": "Wiggins & Kim, ISMIR 2019 (CC BY)"},
        ],
    },
    {
        "family": "DEGREE-FIXED / PITCH-FLOATING",
        "atoms_denote": "an index into the instrument's PHYSICAL key order",
        "reference_device": "the tuning (laras/embat) of the particular "
                            "instrument set",
        "is_chart_of_interval_carrier": False,
        "instances": [{
            "name": "Kepatihan (Javanese gamelan cipher notation)",
            "claim": "ciphers index the physical key-order of the saron, "
                     "counted from lowest; changing pathet does NOT "
                     "renumber the ciphers. 'there is no standard tuning' — "
                     "each gamelan set has its own embat",
            "tier": "CONTESTED",
            "source": "Claimed: Brandts Buys, J. S. 'The common Javanese "
                      "cipher notation (The Kepatihan notation from Solo).' "
                      "Translingual Discourse in Ethnomusicology 5 (2019): "
                      "1-72, doi:10.17440/tde027 (orig. Djawa 20, 1940); "
                      "Sumarsam, Wesleyan",
            "caveat": "⚠️ CONTESTED BETWEEN TWO SOURCING PASSES: pass 1 "
                      "reported this VERIFIED-OA with the DOI above; pass 2 "
                      "reported kepatihan as entirely UNSOURCED. It was NOT "
                      "independently checked here (the contested-citation "
                      "budget went to the two rows that F23/F24 depend on), "
                      "so it is marked CONTESTED rather than promoted or "
                      "discarded. Treat the STRUCTURAL point — that a "
                      "degree-fixed/pitch-floating family exists and is "
                      "neither tonic-relative nor absolute — as the "
                      "load-bearing claim, and re-source it before any use "
                      "that depends on the tradition rather than the shape. "
                      "A Galin-Paris-Cheve/missionary lineage is UNSOURCED "
                      "under both passes.",
        }],
    },
]

#: Vocabulary warning worth carrying into any write-up.
SEEGER_WARNING = (
    "⚠️ DO NOT USE 'prescriptive/descriptive' AS THE AXIS. Seeger 1958 is "
    "verified (The Musical Quarterly XLIV/2: 184-195, DOI "
    "10.1093/mq/XLIV.2.184; PAYWALLED — read via the 1977 Studies in "
    "Musicology reprint), and his sense is 'blueprint of how a piece shall "
    "be made to sound' vs 'report of how a performance did sound'. But the "
    "Carnatic literature INVERTS it: Ranjani & Sreenivas write 'Descriptive "
    "notations (followed in western classical music) offer a precise rule'. "
    "Half the literature will read the term backwards. Use COMPLETE vs "
    "SKELETAL instead, applied PER DIMENSION — jianzipu is complete on "
    "action and empty on time; gongche is skeletal on pitch and partial on "
    "time.")


def main() -> int:
    print("srmech.__file__    =", srmech.__file__)
    print("srmech.__version__ =", srmech.__version__)
    try:
        import numpy  # noqa: F401
        print("!! numpy PRESENT — environment wrong")
    except ImportError:
        print("numpy              = ABSENT (correct)")

    # ── F22 — the taxonomy, and which families are charts ────────────────
    print("\nF22   the five attested chart families")
    print("      family                              charts the interval "
          "carrier?  instances  tiers")
    for f in FAMILIES:
        tiers = sorted({i["tier"] for i in f["instances"]})
        print(f"      {f['family']:35s} {str(f['is_chart_of_interval_carrier']):5s}"
              f"{'':20s}{len(f['instances']):5d}      {tiers}")
    n_chart = sum(1 for f in FAMILIES if f["is_chart_of_interval_carrier"])
    n_inst = sum(len(f["instances"]) for f in FAMILIES)
    tier_counts = {}
    for f in FAMILIES:
        for i in f["instances"]:
            tier_counts[i["tier"]] = tier_counts.get(i["tier"], 0) + 1
    print(f"\n      {n_chart} of {len(FAMILIES)} families are charts of the "
          f"INTERVAL carrier; {len(FAMILIES) - n_chart} are charts of "
          f"something else (an instrument's configuration)")
    print(f"      {n_inst} instances, sourcing tiers: {tier_counts}")
    emit(finding="F22_chart_family_taxonomy", families=FAMILIES,
         n_families=len(FAMILIES), n_charting_interval_carrier=n_chart,
         n_instances=n_inst, tier_counts=tier_counts,
         seeger_vocabulary_warning=SEEGER_WARNING,
         verdict="THREE families are charts of the interval carrier "
                 "(differential / scale-degree / absolute-position). TWO are "
                 "NOT: instrument-action notations chart the INSTRUMENT's "
                 "configuration space, with pitch as an OUTPUT of executing "
                 "the action, and kepatihan indexes a physical key order "
                 "whose absolute realisation floats per instrument set. "
                 "Modelling all five as charts of one pitch carrier would "
                 "be wrong, and the two that resist are NOT the exotic "
                 "ones — Western lute and guitar tablature sit in the same "
                 "bucket as jianzipu.")

    # ── F23 — the ACTION families: injectivity in both directions ────────
    # A 6-course instrument with a declared tuning and F frets.  The action
    # space is (course, fret); the carrier value is the pitch.  This is a
    # STRUCTURAL model of the shape the guitar-tab source reports; it is not
    # a claim about any specific instrument's tuning.
    print("\nF23   ACTION family: is action->pitch a chart?")
    TUNING = (0, 5, 10, 15, 19, 24)      # 6 courses, structural
    FRETS = 12
    actions = [(c, f) for c in range(len(TUNING)) for f in range(FRETS + 1)]
    fwd = {a: TUNING[a[0]] + a[1] for a in actions}
    pre = {}
    for a, p in fwd.items():
        pre.setdefault(p, []).append(a)
    hist = {}
    for p, aa in pre.items():
        hist[len(aa)] = hist.get(len(aa), 0) + 1
    fwd_total = len(fwd) == len(actions)
    back_inj = all(len(aa) == 1 for aa in pre.values())
    worst = max(pre.items(), key=lambda kv: len(kv[1]))
    print(f"      {len(actions)} actions -> {len(pre)} distinct pitches")
    print(f"      action -> pitch: TOTAL and single-valued: {fwd_total}")
    print(f"      pitch -> action: injective: {back_inj}; preimage-size "
          f"histogram {dict(sorted(hist.items()))}")
    print(f"      worst cell: pitch {worst[0]} reachable by "
          f"{len(worst[1])} distinct actions {worst[1]}")
    print(f"      => matches the SOURCED claim that pitch->tab is "
          f"ONE-TO-MANY (Wiggins & Kim, ISMIR 2019)")
    emit(finding="F23_action_family_injectivity",
         n_actions=len(actions), n_pitches=len(pre),
         forward_total=fwd_total, backward_injective=back_inj,
         preimage_histogram={str(k): v for k, v in sorted(hist.items())},
         worst_cell={"pitch": worst[0], "n_actions": len(worst[1])},
         matches_source="Wiggins & Kim, ISMIR 2019 (CC BY): pitch->tab is "
                        "one-to-many",
         verdict="The action->pitch map is a total function but NOT "
                 "injective backwards, so it is a chart of the ACTION space "
                 "onto the pitch carrier and NOT an atlas chart of the "
                 "pitch carrier: you cannot recover the notation from the "
                 "music. The loss is not spelling (as in F7's enharmonic "
                 "case) — it is which physical action was taken, which the "
                 "pitch carrier structurally does not hold.")

    # ── F24 — THE STATEFUL FAMILY.  This is the one that breaks the design.
    print("\nF24   STATEFUL chart — the symbol->carrier map is NOT a function")
    print("      ⚠️ REFRAMED. An earlier version of this block opened with "
          "'SOURCED:' and attributed a position-inheritance rule to "
          "Tse & Wong (2020) and Unicode L2/22-206. BOTH PDFs were then "
          "fetched and grepped directly: the rule is ABSENT from both "
          "(0 hits for persist/inherit/carry over/previous character/"
          "omitted across 417 KB). The attribution was wrong, and it was "
          "wrong in THIS artifact.")
    print("      What is ATTESTED (verbatim, self-extracted) is only that "
          "jianzipu notates FINGERING and the player 'produces a musical "
          "note' by executing it — i.e. pitch is an OUTPUT. That supports "
          "F23, not F24.")
    print("      So F24 is now a CONDITIONAL structural result: IF a "
          "notation carries reading state, THEN the atlas language does not "
          "reach it. The antecedent is not claimed of any named tradition "
          "here. The measurement below is of the MODEL, and it is worth "
          "keeping because the consequent is what bounds the design.")

    HOLD = None   # the 'upper half omitted' symbol: inherit the position

    def read_stateful(symbols, start_state, n=12):
        """(symbol, state) -> (carrier value, new state).  A TRANSDUCER."""
        out, st = [], start_state
        for s in symbols:
            if s is not HOLD:
                st = s
            out.append(cyclic_mod_add(st, 0, n))
        return out, st

    # ⚠️ THE FIRST VERSION OF THIS TEST FAILED TO DEMONSTRATE ANYTHING, and
    # the reason is worth keeping: it used the sequence [3, HOLD, HOLD, 7,
    # ...], which OPENS with a position-setting symbol.  That symbol
    # overwrites the start state on step 1, so the two readings agreed and
    # the test reported "identical? True" — not because the notation is
    # stateless, but because the probe destroyed the state before it could
    # matter.  The correct probe OPENS WITH A HOLD, which is exactly the
    # real-world case: a fragment entered mid-piece, where the inherited
    # position is not on the page at all.
    seq = [HOLD, HOLD, 7, HOLD, 2, HOLD]
    r1, _ = read_stateful(seq, 0)
    r2, _ = read_stateful(seq, 9)
    print(f"      symbol sequence      : "
          f"{['HOLD' if x is HOLD else x for x in seq]}")
    print(f"      read from state 0    : {r1}")
    print(f"      read from state 9    : {r2}")
    print(f"      identical? {r1 == r2}  -> the SAME symbols give "
          f"{'the same' if r1 == r2 else 'DIFFERENT'} carrier values")

    # how many of the positions differ, and where?
    diffs = [i for i, (a, b) in enumerate(zip(r1, r2)) if a != b]
    print(f"      positions that differ: {diffs} of {len(seq)}  — exactly "
          f"the leading HOLD prefix, before the first position-setting "
          f"symbol re-anchors the reading")
    # and the sweep: over ALL start states, how many distinct readings?
    readings = {tuple(read_stateful(seq, s)[0]) for s in range(12)}
    print(f"      distinct readings over all 12 start states: "
          f"{len(readings)}  -> the page under-determines the music by a "
          f"factor of {len(readings)}")

    # NEGATIVE CONTROL: a stateless chart must NOT show this
    def read_stateless(symbols, start_state, n=12):
        return [cyclic_mod_add(s, 0, n) for s in symbols if s is not HOLD]

    stateless_seq = [3, 5, 7, 2]
    q1 = read_stateless(stateless_seq, 0)
    q2 = read_stateless(stateless_seq, 9)
    print(f"      NEG control (stateless chart, same two start states): "
          f"{q1} vs {q2}  identical? {q1 == q2}  "
          f"{'instrument OK' if q1 == q2 else '!! CONTROL FAILED'}")
    emit(finding="F24_stateful_chart_is_a_transducer",
         modelled_rule="a notation symbol may omit its position component, "
                       "meaning the position persists from the previous "
                       "symbol",
         rule_attribution_status="UNSOURCED — this rule is NOT attributed "
                                 "to any tradition. It was previously "
                                 "attributed to Tse & Wong (2020) and "
                                 "Unicode L2/22-206; both PDFs were fetched "
                                 "and grepped in session and the rule is "
                                 "ABSENT from both (0 hits across 417 KB). "
                                 "The claim is retracted.",
         result_form="CONDITIONAL — if a notation carries reading state, "
                     "then the atlas language does not reach it. The "
                     "antecedent is not claimed of any named tradition.",
         tier="UNSOURCED (antecedent) / MEASURED (consequent)",
         symbol_sequence=["HOLD" if x is HOLD else x for x in seq],
         read_from_state_0=r1, read_from_state_9=r2,
         identical=r1 == r2, differing_positions=diffs,
         distinct_readings_over_all_start_states=len(readings),
         negative_control_stateless_identical=q1 == q2,
         instrument_valid=(q1 == q2) and (r1 != r2),
         probe_design_note="The first probe used a sequence OPENING with a "
                           "position-setting symbol, which overwrote the "
                           "start state on step 1 and made the test report "
                           "'identical' for a reason having nothing to do "
                           "with the notation. The corrected probe opens "
                           "with a HOLD — the real case of a fragment "
                           "entered mid-piece, where the inherited position "
                           "is not on the page.",
         verdict="CONDITIONAL RESULT. A chart in the atlas sense is a "
                 "FUNCTION from symbols to carrier values. A stateful "
                 "reading is a TRANSDUCER: (symbol, state) -> (value, "
                 "state'). Measured on the model: one 6-symbol sequence "
                 "yields 12 distinct readings across 12 start states, and "
                 "the stateless negative control shows no such effect — so "
                 "the effect is a property of the STATE and not of the "
                 "harness. What this does NOT establish is that any "
                 "particular notation is stateful; that antecedent is "
                 "unsourced and is not asserted. The design consequence "
                 "survives either way, because it is a statement about what "
                 "the atlas language can express: a carrier+chart spec "
                 "covers functions and must say so, rather than quietly "
                 "assuming every notation is one.")

    # ── the connection worth naming, stated as a QUESTION not a claim ────
    print("\n      Connection to the 'active carrier' thread — stated as a "
          "question, not a claim:")
    print("      F24's statefulness and P3's F9 path-dependence are the SAME "
          "SHAPE (the reading depends on the route taken, not only on the "
          "symbols), but they are NOT the same object: F24's state is a "
          "notational convention about ink, and F9's is the algebra's "
          "associator. FORM, not identity "
          "(`[[user_stance_cascade_matching_substrate_blind_form_not_identity]]`). "
          "Whether a shared name is doing any work here is exactly the kind "
          "of question the epistemic ceiling exists to keep open.")
    emit(finding="F24b_relation_to_active_carrier_thread",
         claim_status="OPEN QUESTION, deliberately not resolved",
         shared_form="the reading depends on the route, not only on the "
                     "symbols",
         why_not_identity="F24's state is a notational convention about "
                          "ink; F9's is the algebra's associator. A shared "
                          "structural name is not object identity.",
         memory="[[user_stance_cascade_matching_substrate_blind_form_not_identity]]")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECS:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"\nwrote {len(RECS)} records -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
