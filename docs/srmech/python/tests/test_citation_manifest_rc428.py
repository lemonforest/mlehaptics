"""THE citation-contains-term gate — v0.9.0rc428 (`#T1126`).

Fails the build when a shipped citation attributes a claim to a section that
does not contain it, and stays SILENT on the section-anchored citations that
are correct.

WHY THIS GATE EXISTS
====================
srmech's MPM discipline is *a citation without attestation is not real; an
attestation that can't be re-verified is broken*. Measured at rc428, it had no
mechanical check for the thing that matters most: **whether the cited source
actually contains the cited claim.** Zero gates covered literature citations in
shipped package source. All identifier-bearing citations in the package — and
their copies in the generated artifacts that reach users via ``describe()``,
the MCP tool list and the compiled-in C registry — were entirely ungated.

Two existing tests were worse than absent. Six of them assert
``source_url == "https://arxiv.org/abs/math/0105155"`` — the tree asserting
that the tree says what it says. That literal IS the citation that was FALSE at
``cascade/cayley_dickson.py``, and every one of them was green throughout.
An attestation gate that reads only the tree cannot discriminate; this one
reads an EXTERNAL measurement of the source and joins the tree to it.

WHAT IT FOUND ON ITS FIRST RUN
===============================
Four further citation halves were FALSE AS CITED, all the same shape as the
rc426 defect (right paper, wrong locator), all in prose that ships:

===========================================  ==========  ====================
site                                         cited       actually
===========================================  ==========  ====================
``cayley_plane.py`` module docstring          §4.2        §3.1 (Hopf fibration)
``cayley_plane.py:octonion_hopf_base``        §4.1–§4.2   §3.1
``tool_schema.py`` octonion_hopf_base entry   §4.1–§4.2   §3.1
``cayley_dickson.py:cd_three_form``           §4.1        §2.1 (Fano plane)
===========================================  ==========  ====================

"Hopf" occurs **0 times** in Baez §4.1 or §4.2 — §4.1 is G₂ and §4.2 is F₄ —
while the fibration table ``𝕆: S⁷ ↪ S¹⁵ → S⁸`` and ``𝕆P¹ ≅ S⁸`` are both set in
§3.1 "Projective Lines". "Fano" occurs 0 times in §4.1; the Fano plane is §2.1.

**The first of those sat inside a parenthesis whose OTHER half is correct** —
§4.2 really is where Baez says F₄'s 16-dimensional projective plane "is none
other than 𝕆P²". rc427 verified that half and rightly left it alone; the Hopf
half rode along in the same parenthesis and nothing looked at it. That is why
axis A3 binds each claim to ITS OWN locator, and it is why a gate that merges
them can only ever return one verdict for two claims.

Every one was fixed by RE-POINTING THE LOCATOR. **Removing a citation is not a
fix** — it converts a false citation into an UNSOURCED claim, a change of
defect class, measured on ``malcev_defect`` where rc427's removal did exactly
that and nothing in the tree noticed. Arm S3 exists to catch that specific
move.

THE TWO GOVERNING RULES, RESTATED WHERE THEY WILL BE READ
==========================================================
1. **Never edit a citation to make this gate green.** If it fires on something
   correct, the GATE is wrong. Re-scope it by naming a syntactic AXIS in
   ``citation_corpus.py`` — no ``noqa``, no named file, no named line. Two of
   the six axes there exist because this gate fired on correct prose:
   ``cd_register.py``'s three-source list (A1) and the two paragraphs that
   RECORD the rc427 fix (A6).
2. **Existence proves nothing; TOPICALITY decides.** "Moufang" IS in Baez —
   §3, as Ruth Moufang and the Moufang plane. A gate blind to section passes
   the false §2 claim, and a batch fix keyed on "the string is absent" breaks
   the correct §3 ones.

THE FOUR ARMS, AND WHY ONLY ONE IS STRICT ZERO
===============================================
``S1``  STRICT ZERO — units with an identifier, a section locator, AND an
        attributed claim, on a source the manifest attests. This is the
        decidable class and it is SMALL: measured at 35 units corpus-wide.
``S2``  CEIL, presence-only — a claim with an identifier but no locator can
        only be checked against the whole document.
``S3``  CEIL — a term whose provenance verdict is DERIVED-AND-MEASURED or
        UNSOURCED must carry that verdict in the SAME artifact as the claim.
``S4``  CEIL, coverage — citation units naming a source the manifest does not
        attest. Counted, not judged; drains monotonically as sources are added.

A strict-zero arm over the whole corpus would be dishonest: only ~10% of
citation units carry (identifier + locator + claim), and 53% make no attributed
claim at all. The split is measured, not chosen.

NON-VACUITY IS NOT OPTIONAL
============================
An all-zero manifest would make every citation fire and every "silent"
assertion below meaningless — and an empty corpus would make the whole file
pass by observing nothing. Both are guarded explicitly, because rc428's own
instruments produced FOUR false nulls before any of this shipped and not one
was caught by review.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

import srmech
from srmech.amsc.format import read_ndjson

import citation_corpus as CC

# ── the manifest ──────────────────────────────────────────────────────

MANIFEST_DIR = CC.PKG_ROOT / "amsc" / "attested" / "literature_claims"
MANIFEST = MANIFEST_DIR / "row.ndjson"

#: The gate's own scope statement. A source row must declare EXACT section
#: attribution before any locator-scoped verdict is drawn from it. From a
#: rendered PDF alone the heading map is a heuristic that also matches table
#: rows like ``"3 H ⊕ H"``, so such a source supports presence/absence only.
_EXACT = "EXACT"


def _load() -> Tuple[Dict[str, dict], Dict[Tuple[str, str], dict]]:
    """``(source rows by bare id, term rows by (bare id, term))``.

    Reads the committed bytes. It does NOT re-derive them — per
    ``srmech.amsc.format``, *we trust the committed bytes at runtime and never
    recompute*. Re-derivation is ``tools/build_citation_manifest.py --check``,
    which needs the network and therefore cannot be a gate.
    """
    sources: Dict[str, dict] = {}
    terms: Dict[Tuple[str, str], dict] = {}
    with MANIFEST.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = json.loads(line)
            bare = row["source_id"].split(":", 1)[1]
            if row["row_type"] == "source":
                sources[bare] = row
            elif row["row_type"] == "term":
                terms[(bare, row["term"])] = row
            else:                                        # pragma: no cover
                raise AssertionError(
                    "unknown row_type %r at line %d" % (row["row_type"],
                                                        lineno))
    return sources, terms


SOURCES, TERMS = _load()


def _occurrences(bare: str, term: str, locator: str | None) -> int:
    """Occurrences of ``term`` within ``locator``'s scope. Prefix rule.

    ``locator is None`` means presence-only: the whole document.
    """
    row = TERMS[(bare, term)]
    if locator is None:
        return int(row["document_total"])
    return sum(n for sec, n in row["occurrences_by_section"].items()
               if CC.covers(locator, sec))


def _watchlist(bare: str) -> List[str]:
    return sorted(t for (s, t) in TERMS if s == bare)


def _evaluate(unit: CC.Unit) -> List[Tuple[str, int]]:
    """``[(term, occurrences)]`` for every watchlist term the claim names.

    Axis A6 is applied HERE rather than in the parser because it is a property
    of the (claim, term) pair, not of the citation's syntax: a claim asserting
    that the source LACKS a term is not asserting that it contains one, and a
    gate that fires on the paragraph recording a fix is firing on the fix.
    """
    out: List[Tuple[str, int]] = []
    for term in _watchlist(unit.source_id):
        if not CC.contains_term(unit.claim, term):
            continue
        if CC.asserts_absence(unit.claim, term):
            continue
        out.append((term, _occurrences(unit.source_id, term, unit.locator)))
    return out


def _attested() -> frozenset:
    """Sources with EXACT section attribution — the only ones S1 may judge."""
    return frozenset(k for k, r in SOURCES.items()
                     if r.get("section_attribution") == _EXACT)


# ── non-vacuity: run these FIRST or nothing below means anything ──────


def test_the_corpus_is_not_empty() -> None:
    """A parser that silently stops observing must crash, not green."""
    assert len(CC.shipped_modules()) >= 200, len(CC.shipped_modules())
    units = CC.all_units()
    assert len(units) >= 100, len(units)
    assert len({u.source_id for u in units}) >= 15


def test_the_manifest_is_not_vacuous() -> None:
    """An all-zero manifest makes every citation fire and every silence lie.

    So this asserts BOTH directions: the watchlist is non-empty, AND at least
    one term is actually PRESENT somewhere. A manifest of nothing but zeros
    would pass a presence-only check and turn the whole gate into noise.
    """
    assert SOURCES, "no source rows"
    assert len(SOURCES) >= 2, (
        "one source cannot distinguish 'the schema works' from 'the schema "
        "fits Baez'; the second source IS the negative control on the design")
    assert TERMS, "no term rows"
    present = [r for r in TERMS.values() if int(r["document_total"]) > 0]
    assert present, "every watchlist term reads zero — the manifest is dead"
    assert len(present) >= 10, len(present)


def test_every_source_row_carries_a_live_positive_control() -> None:
    """The single most load-bearing field in the manifest.

    rc428 measured an extraction returning 0 for BOTH "Moufang" and "octonion"
    from a paper titled *The Octonions*. An instrument that can return a
    spurious zero silently blesses every citation in the tree, so a source with
    no live positive control may not be used to judge anything.
    """
    for bare, row in sorted(SOURCES.items()):
        control = row.get("positive_control") or {}
        assert control.get("term"), bare
        assert int(control.get("occurrences", 0)) > 0, (
            f"{bare}: positive control {control.get('term')!r} reads "
            f"{control.get('occurrences')} — this extraction is BROKEN and "
            f"every zero derived from it is silence, not measurement")


def test_source_rows_declare_their_section_attribution_and_hashes() -> None:
    """A locator-scoped verdict requires EXACT attribution and real bytes."""
    for bare, row in sorted(SOURCES.items()):
        assert row.get("section_attribution") in (_EXACT, "PRESENCE_ONLY"), bare
        assert len(row.get("sections") or []) >= 5, bare
        for field in ("source_eprint_sha256", "source_pdf_sha256"):
            digest = row.get(field, "")
            assert len(digest) == 64 and all(
                c in "0123456789abcdef" for c in digest), (bare, field)


def test_the_manifest_and_the_parser_agree_on_the_prefix_rule() -> None:
    """Two copies of :func:`covers` exist; they must be one rule.

    The manifest WRITES section labels with one implementation and the gate
    READS them with another. That is a convention two sites agree by, and a
    convention two sites agree by eventually stops holding — so it is pinned
    rather than trusted. The builder lives in ``tools/`` (not packaged), so it
    is imported by path rather than by name.
    """
    import importlib.util

    builder_path = CC.PY_ROOT / "tools" / "build_citation_manifest.py"
    assert builder_path.exists(), builder_path
    spec = importlib.util.spec_from_file_location("_rc428_builder",
                                                  builder_path)
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    cases = [("§3", "§3.4", True), ("§3", "§3", True), ("§4.2", "§4", False),
             ("§1", "§10", False), ("§2", "§2.2", True),
             ("§2.4", "§2", False), ("BIBLIOGRAPHY", "BIBLIOGRAPHY", True),
             ("§1", "BIBLIOGRAPHY", False)]
    for cited, actual, want in cases:
        assert CC.covers(cited, actual) is want, (cited, actual)
        assert builder.covers(cited, actual) is want, (cited, actual)


# ── S1: STRICT ZERO ───────────────────────────────────────────────────


def _s1_units() -> List[CC.Unit]:
    ok = _attested()
    return [u for u in CC.all_units()
            if u.source_id in ok and u.locator is not None and u.has_claim]


def test_s1_no_shipped_citation_claims_a_term_its_section_lacks() -> None:
    """STRICT ZERO. The gate's whole reason for existing.

    A unit fires iff the manifest attests its source, its claim names a
    watchlist term, the claim is not asserting that term's ABSENCE, and the
    cited section's occurrence count for that term is **0** with the source's
    positive control alive.
    """
    units = _s1_units()
    assert units, (
        "the strict-zero population is EMPTY — that is a broken parser, not a "
        "clean corpus. rc428's first grammar returned exactly this by matching "
        "minimally, and it would have killed this gate as unbuildable.")

    offenders: List[str] = []
    for unit in units:
        for term, count in _evaluate(unit):
            if count == 0:
                control = SOURCES[unit.source_id]["positive_control"]
                offenders.append(
                    f"{unit.path}:{unit.line}\n"
                    f"    cites  arXiv:{unit.source_id} {unit.locator}\n"
                    f"    claims {term!r}\n"
                    f"    but    {unit.locator} contains 0 occurrences of "
                    f"{term!r}\n"
                    f"    (positive control {control['term']!r} = "
                    f"{control['occurrences']} on the same extraction, so this "
                    f"zero is a MEASUREMENT, not silence)\n"
                    f"    claim text: {unit.claim[:150]!r}")

    assert not offenders, (
        "%d shipped citation(s) attribute a claim to a section that does not "
        "contain it:\n\n%s\n\n"
        "⚠️ FIX BY RE-POINTING THE LOCATOR, and only after reading the source. "
        "Do NOT delete the citation — that converts a false citation into an "
        "UNSOURCED claim, which is a change of defect class and not a fix "
        "(measured on malcev_defect at rc427). Do NOT weaken this gate: if it "
        "fired on something CORRECT, the gate is wrong, and the repair is a "
        "new syntactic AXIS in tests/citation_corpus.py — never a noqa and "
        "never a named file."
        % (len(offenders), "\n\n".join(offenders)))


# ── S2 / S3 / S4: down-only CEILs ─────────────────────────────────────

#: Presence-only residual: an identifier + claim with NO locator, naming a
#: watchlist term the whole document lacks. Seeded at the measured value.
#: DOWN ONLY.
CEIL_S2_PRESENCE_ONLY = 0

#: Shipped prose carrying a claim whose provenance verdict is
#: DERIVED-AND-MEASURED or UNSOURCED, where the verdict does NOT travel in the
#: same artifact as the claim. DOWN ONLY. rc428 drove this to 0.
CEIL_S3_VERDICT_NOT_WITH_CLAIM = 0

#: Citation units naming a source the manifest does not yet attest. This is a
#: COVERAGE number, not a defect count — it says how much of the corpus this
#: gate can currently see. DOWN ONLY; it drains as sources are added.
CEIL_S4_UNATTESTED_SOURCES = 22


def test_s2_presence_only_claims_ceiling() -> None:
    """A claim with no locator can only be checked against the whole document.

    Weaker than S1 by construction, so it is a CEIL rather than strict zero —
    but it still catches the sharpest defect class of all, the one where the
    term is absent from the ENTIRE paper. That is what "Mal'cev" was.
    """
    ok = _attested()
    offenders: List[str] = []
    for unit in CC.all_units():
        if unit.source_id not in ok or unit.locator is not None:
            continue
        if not unit.has_claim:
            continue
        for term, count in _evaluate(unit):
            if count == 0:
                offenders.append(f"{unit.path}:{unit.line} arXiv:"
                                 f"{unit.source_id} claims {term!r}, absent "
                                 f"from the whole document")
    assert len(offenders) <= CEIL_S2_PRESENCE_ONLY, (
        "S2 presence-only residual rose to %d (ceiling %d):\n  %s"
        % (len(offenders), CEIL_S2_PRESENCE_ONLY, "\n  ".join(offenders)))


#: Terms whose provenance is DERIVED-AND-MEASURED or UNSOURCED rather than
#: cited, mapped to the shipped artifacts that must carry the verdict beside
#: the claim.
#:
#: This is the arm that catches what rc427's own FIX created. rc427 removed a
#: false Baez citation for "the Mal'cev tangent algebra" and wrote the
#: reasoning into a ``#`` comment — which does not ship. The claim ships:
#: through ``help()``, ``describe()``, the MCP tool list and the compiled-in C
#: registry, and it shipped with no verdict attached. **Removing a false
#: citation is not a fix; it is a change of defect class**, and nothing in the
#: tree noticed for a whole rc.
#:
#: A ``DERIVED-AND-MEASURED`` verdict also requires a NAMED TEST that EXECUTES
#: the claim, recorded here. Without one it is ``UNSOURCED`` wearing a better
#: word — an ASSERTED algebraic property is not a MEASURED one.
S3_VERDICT_CLAIMS: Tuple[Tuple[str, str, str, str], ...] = (
    ("Mal'cev", "DERIVED-AND-MEASURED", "tests/test_loop_bind_moufang.py",
     "cascade/cayley_dickson.py"),
)

#: The tokens that count as a verdict travelling with the claim.
_VERDICT_MARKERS = ("DERIVED-AND-MEASURED", "UNSOURCED", "not cited",
                    "no attestation is claimed")


def test_s3_a_derived_verdict_travels_with_the_claim_it_governs() -> None:
    """The verdict and the claim must ship in the SAME artifact.

    A provenance verdict living in a ``#`` comment while the claim it governs
    ships in a docstring is not provenance — it is a note to whoever opens the
    file, and users never open the file.
    """
    offenders: List[str] = []
    for term, verdict, named_test, rel in S3_VERDICT_CLAIMS:
        assert (CC.PY_ROOT / named_test).exists(), (
            f"{term}: verdict {verdict} names {named_test}, which does not "
            f"exist. A DERIVED-AND-MEASURED verdict with no test that "
            f"EXECUTES the claim is UNSOURCED wearing a better word.")
        path = CC.PKG_ROOT / rel
        assert path.exists(), rel
        carriers = [text for _line, text in CC.string_constants(path)
                    if CC.contains_term(text, term)]
        assert carriers, (
            f"{rel} no longer carries a shipped {term!r} claim — if the claim "
            f"moved, move this row; if it was deleted, delete this row. A "
            f"vacuously-passing arm is the failure this whole rc is about.")
        for text in carriers:
            if not any(marker in text for marker in _VERDICT_MARKERS):
                offenders.append(
                    f"{rel}: a shipped string claims {term!r} but carries no "
                    f"{verdict} verdict. The claim reaches users through "
                    f"help() / describe() / the MCP list / the C registry; a "
                    f"verdict in a # comment does not travel with it.")
    assert len(offenders) <= CEIL_S3_VERDICT_NOT_WITH_CLAIM, (
        "S3 residual rose to %d (ceiling %d):\n  %s"
        % (len(offenders), CEIL_S3_VERDICT_NOT_WITH_CLAIM,
           "\n  ".join(offenders)))


def test_s4_manifest_coverage_ceiling_drains() -> None:
    """How much of the corpus this gate can currently SEE.

    A coverage number, not a defect count — an unattested source is not a bad
    citation, it is one nobody has checked. It is a CEIL so the uncovered set
    can only shrink, per
    ``[[feedback_ungated_surfaces_trickle_gated_surfaces_race_to_100]]``: an
    ungated surface does not trickle toward coverage, it becomes BELIEVED
    ABSENT.
    """
    ok = _attested()
    uncovered = sorted({u.source_id for u in CC.all_units()
                        if u.source_id not in ok})
    assert len(uncovered) <= CEIL_S4_UNATTESTED_SOURCES, (
        "S4 coverage regressed: %d unattested sources (ceiling %d).\n"
        "New sources are cited faster than the manifest attests them:\n  %s\n"
        "Either attest them in tools/build_citation_manifest.py or RAISE this "
        "ceiling deliberately, in a commit that says why."
        % (len(uncovered), CEIL_S4_UNATTESTED_SOURCES, "\n  ".join(uncovered)))


def test_s4_ceiling_is_not_slack() -> None:
    """A CEIL far above its residual is not a ratchet, it is a comment."""
    ok = _attested()
    uncovered = {u.source_id for u in CC.all_units() if u.source_id not in ok}
    assert len(uncovered) >= CEIL_S4_UNATTESTED_SOURCES - 6, (
        "the S4 ceiling (%d) is now well above the residual (%d) — lower it, "
        "or it stops ratcheting" % (CEIL_S4_UNATTESTED_SOURCES,
                                    len(uncovered)))


# ── the both-sides bite test ──────────────────────────────────────────

#: Four fixtures, all VERBATIM from the tree at rc426/rc427/rc428. No repo edit
#: is involved, so this test proves the predicate rather than the current state
#: of the files — a gate whose bite depends on a live defect stops biting the
#: moment the defect is fixed.
BITE_FIXTURES: Tuple[Tuple[str, str, bool, str], ...] = (
    ("rc426 false citation, verbatim",
     "Baez, J.C. (2002), *The Octonions*, arXiv:math/0105155, §2 (the octonion "
     "Moufang identities, alternativity, and the Mal'cev tangent algebra)",
     True,
     "§2 is 'Constructing the Octonions' and contains 0 'Moufang'; the 5 "
     "occurrences are 3 in §3 (Ruth Moufang, the Moufang plane) and 2 in the "
     "bibliography. THIS SHIPPED INSIDE PUBLISHED WHEELS."),
    ("rc427 false citation, the half nobody checked",
     "Baez (2002), arXiv:math/0105155, §4.1–§4.2 (the octonionic Hopf "
     "fibration S⁷↪S¹⁵↠S⁸ and 𝕆P¹≅S⁸)",
     True,
     "§4.1 is G₂ and §4.2 is F₄; 'Hopf' occurs 0 times in either. The "
     "fibration is §3.1 'Projective Lines'."),
    ("CORRECT §3 citation — must survive",
     "J.C. Baez (2002), arXiv:math/0105155, §3 (the exceptional Jordan "
     "algebra)",
     False,
     "§3 carries 3 occurrences in its own prose and 4 more in §3.4, so the "
     "PREFIX rule verifies it at 7. Under equality it would read 3 and still "
     "pass, but a §3 citation of a §3.4-only term would falsely fire."),
    ("CORRECT §4.2 citation for 𝕆P² — must survive",
     "Baez (2002), arXiv:math/0105155, §4.2 (the Cayley plane 𝕆P²)",
     False,
     "Baez writes 'Cayley plane' NOWHERE, but §4.2 states F₄ 'is the isometry "
     "group of a 16-dimensional projective plane … none other than 𝕆P²'. The "
     "declared variant set is what keeps this correct citation silent."),
    ("A1 source list — must survive",
     "Hurwitz (1898); Baez arXiv:math/0105155; Kanerva (2009) "
     "*Hyperdimensional Computing*.",
     False,
     "Three sources, each correctly attributed. A fixed-width window read "
     "Kanerva as a claim ABOUT Baez and reported a defect — trap 2 committed "
     "by the instrument measuring trap 2."),
    ("A2 no claim — must survive",
     "Baez (2002), arXiv:math/0105155, §4.2.",
     False,
     "A locator with no attribution mark asserts nothing and cannot be false. "
     "19.7% of citation units are this shape."),
    ("A6 the paragraph recording the fix — must survive",
     "Baez arXiv:math/0105155 — cited here through rc426 for 'the Mal'cev "
     "tangent algebra' — contains NO occurrence of Mal'cev in any spelling.",
     False,
     "Prose asserting ABSENCE is not asserting presence. Without A6 the gate "
     "fires on the paragraph written to record the fix."),
    ("A6 must not launder a plain false claim",
     "Baez arXiv:math/0105155, §4.2 — the octonionic Hopf fibration",
     True,
     "No negation governs 'Hopf' here, so A6 leaves it alone and it fires. "
     "This is the both-sides half of A6: an axis that silences everything is "
     "an exemption wearing an axis's name."),
)


@pytest.mark.parametrize("label,text,should_fire,why", BITE_FIXTURES,
                         ids=[f[0] for f in BITE_FIXTURES])
def test_the_citation_gate_still_bites(label: str, text: str,
                                       should_fire: bool, why: str) -> None:
    """Both sides. A gate that only ever passes is indistinguishable from one
    that cannot fail, and a gate that fires on correct prose is worse than none.
    """
    ok = _attested()
    fired: List[Tuple[str, str, int]] = []
    for unit in CC.parse_units(text, "<bite>", 0):
        if unit.source_id not in ok or not unit.has_claim:
            continue
        for term, count in _evaluate(unit):
            if count == 0:
                fired.append((str(unit.locator), term, count))

    if should_fire:
        assert fired, (
            f"{label}: the gate did NOT fire on a citation known to be FALSE.\n"
            f"  {why}\n  text: {text!r}\n"
            f"A guard that cannot fire is decorative, and every verdict this "
            f"gate has ever rendered is downgraded to UNSUPPORTED.")
    else:
        assert not fired, (
            f"{label}: the gate FIRED on a citation known to be CORRECT "
            f"{fired!r}.\n  {why}\n  text: {text!r}\n"
            f"⚠️ Do NOT edit the citation. The GATE is wrong — re-scope it by "
            f"naming a syntactic axis in tests/citation_corpus.py.")


def test_the_bite_fixtures_exercise_both_directions() -> None:
    """The bite suite itself must be non-vacuous in both directions."""
    fires = [f for f in BITE_FIXTURES if f[2]]
    silents = [f for f in BITE_FIXTURES if not f[2]]
    assert len(fires) >= 2, "no FIRE fixtures — the gate's bite is unproven"
    assert len(silents) >= 4, "no SILENT fixtures — false positives unguarded"


# ── the axes are exercised, not merely declared ───────────────────────


def test_every_declared_axis_is_load_bearing() -> None:
    """An axis nothing exercises is an exemption nobody is auditing.

    Each assertion below removes ONE axis's effect and shows the corpus verdict
    would change. If any of these stops holding, that axis has become dead
    weight and must be deleted rather than left as a silent subtraction.
    """
    # A1 — without the source-list break, Kanerva reads as a Baez claim.
    src = ("Hurwitz (1898); Baez arXiv:math/0105155; Kanerva (2009) "
           "*Hyperdimensional Computing*.")
    assert not CC.contains_term(CC.parse_units(src)[0].claim, "Kanerva")
    assert "Kanerva" in src                     # it IS there, before the axis

    # A3 — two locators, two claims; merging them would cross-contaminate.
    two = CC.parse_units("arXiv:math/0105155, §3 (the exceptional Jordan "
                         "algebra) + §4.2 (the Cayley plane)")
    assert len(two) == 2
    assert {u.locator for u in two} == {"§3", "§4.2"}
    assert not CC.contains_term(
        next(u for u in two if u.locator == "§4.2").claim, "Jordan")

    # A4 — a code span is not a claim term.
    spanned = CC.parse_units("arXiv:math/0105155, §2 — see ``Moufang`` below")
    assert not CC.contains_term(spanned[0].claim, "Moufang")

    # A6 — both sides, on the two shipped absence-assertions.
    assert CC.asserts_absence("contains NO occurrence of Mal'cev", "Mal'cev")
    assert not CC.asserts_absence("the octonionic Hopf fibration", "Hopf")


def test_the_version_under_test_is_the_one_expected() -> None:
    """Print-and-pin the artifact, per
    ``[[feedback_verify_the_artifact_under_test_is_the_one_you_think]]``."""
    assert Path(srmech.__file__).resolve().parent == CC.PKG_ROOT
    assert MANIFEST.exists(), MANIFEST
    assert read_ndjson is not None      # the framework reader is importable
