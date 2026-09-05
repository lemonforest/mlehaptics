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

import ast
import importlib
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

import srmech
from srmech.amsc.format import read_ndjson
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

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
        # ⚠️ rc428 repair: the matcher was ASYMMETRIC with the manifest. The
        # manifest counts a term across its measured VARIANTS ("Cayley plane"
        # is also spelled "octonionic projective plane", "\OP^2", "octonionic
        # projective space"), but this loop matched the CANONICAL spelling
        # alone. So a citation phrased in a variant was never evaluated at
        # all — it fell through as though it made no claim, which is the
        # SILENT direction: a false citation written the other way round is
        # not merely missed, it is invisible to every arm.
        #
        # It is not a corner case in this corpus: "Cayley plane" occurs 0
        # times in Baez under the canonical spelling and 14 times under the
        # variants. Measured on the shipped tree the fix surfaces no NEW
        # offender (variant-only claim rows = 0), so it closes a latent hole
        # rather than papering over an active one — recorded as BOUNDED, not
        # as a null result.
        spellings = [term] + list(TERMS[(unit.source_id, term)].get(
            "variants", []))
        if not any(CC.contains_term(unit.claim, s) for s in spellings):
            continue
        # Absence must be tested against the spelling the claim ACTUALLY
        # uses; asking about the canonical one would re-introduce the same
        # asymmetry inside axis A6.
        if any(CC.asserts_absence(unit.claim, s) for s in spellings
               if CC.contains_term(unit.claim, s)):
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


def test_every_shipped_row_obeys_the_schema_it_declares() -> None:
    """The catalog's own ``row.schema.json`` must DESCRIBE the shipped rows.

    ⚠️ **rc428 repair — the schema said ``additionalProperties: false`` and
    nothing enforced it.** The repair pass added three fields to the source
    row and the whole suite stayed green, because no read path validates
    against this schema (a sibling catalog's test says so in as many words).
    A contract document that the data may silently contradict is not a
    contract; it is a comment with punctuation — and this rc is about exactly
    that failure mode, so leaving it would have been committing the defect
    while documenting it.

    Checked by hand rather than with ``jsonschema``: that is not a dependency
    of this package, and the properties worth enforcing here are structural.
    """
    schema = json.loads(
        (MANIFEST_DIR / "row.schema.json").read_text(encoding="utf-8"))
    declared = set(schema["properties"])
    required = set(schema["required"])
    assert schema.get("additionalProperties") is False, (
        "the schema stopped forbidding undeclared properties — if that was "
        "deliberate this test is the wrong shape, and if it was not, the "
        "catalog just lost its only field-level contract")

    rows = [json.loads(l) for l in
            MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert rows, "no rows"
    for i, row in enumerate(rows, 1):
        undeclared = sorted(set(row) - declared)
        assert not undeclared, (
            f"row {i} ({row.get('row_type')}/{row.get('source_id')}) carries "
            f"{undeclared}, which row.schema.json does not declare while "
            f"setting additionalProperties=false. Declare the field or stop "
            f"emitting it — a row that violates its own published schema is "
            f"an attestation nobody can re-verify.")
        missing = sorted(required - set(row))
        assert not missing, f"row {i} is missing required {missing}"

    # Non-vacuity: the fields the repair pass added must actually be present,
    # or this test would pass just as happily against a schema describing rows
    # that no longer exist.
    src = [r for r in rows if r["row_type"] == "source"]
    assert src, "no source rows"
    for r in src:
        for field in ("controls", "source_tex_encoding", "extraction_chars"):
            assert field in r, (r["source_id"], field)


def test_a7_a_claim_written_in_a_VARIANT_spelling_is_still_evaluated() -> None:
    """Axis A7 — the matcher and the manifest must share a vocabulary.

    ⚠️ **This test exists because its fix would otherwise be invisible.**
    ``_evaluate`` matched only the CANONICAL spelling while the manifest
    counts each term across its measured variants. Repairing that asymmetry
    changes **nothing** on the shipped corpus — measured: 57 (unit, term)
    pairs matched before, 57 after, 0 variant-only claims — so the repaired
    and unrepaired code are indistinguishable from the tree alone.

    Shipping a guard no test can tell from its absence is precisely the
    defect this rc is about, one level up. So the distinction is forced here
    with a constructed unit rather than left to wait for a real one.

    The hole is real even though it is currently unoccupied: "Cayley plane"
    occurs **0** times in Baez under its canonical spelling and **63** across
    its variants. A citation phrased "the octonionic projective plane @ §9"
    named a term the manifest tracks, in a spelling the matcher could not
    see, and was therefore skipped ENTIRELY — not judged and passed, but
    never judged. That is the silent direction: invisible to every arm.
    """
    bare = "math/0105155"
    row = TERMS[(bare, "Cayley plane")]
    variants = [v for v in row["variants"] if v != "Cayley plane"]
    assert variants, "fixture gone: the Cayley plane row has no variants"
    assert int(row["occurrences_by_section"].get("§3.4", 0)) > 0

    # Canonical spelling: matched before AND after the repair.
    canonical = CC.Unit(bare, "", "§3.4", "the Cayley plane construction",
                        "test", 0, "")
    assert [t for t, _n in _evaluate(canonical)] == ["Cayley plane"]

    # Variant spelling: skipped ENTIRELY before the repair, judged after.
    for variant in variants:
        unit = CC.Unit(bare, "", "§3.4", f"the {variant} construction",
                       "test", 0, "")
        named = [t for t, _n in _evaluate(unit)]
        assert "Cayley plane" in named, (
            f"a claim spelled {variant!r} names a term the manifest tracks "
            f"under {variants!r}, but _evaluate did not evaluate it — the "
            f"matcher and the manifest disagree about what the term IS")

    # And a variant claim at a section where the term is genuinely ABSENT
    # must be JUDGED (non-zero occurrences would make this vacuous).
    absent_at = [s for s in SOURCES[bare]["sections"]
                 if s not in row["occurrences_by_section"]]
    assert absent_at, "fixture gone: the term occurs in every section"
    unit = CC.Unit(bare, "", absent_at[0],
                   f"the {variants[0]} construction", "test", 0, "")
    # Membership, not list equality: "octonionic projective plane" legitimately
    # also matches the SEPARATE watchlist term "projective plane", and both
    # correctly read 0 here. Asserting the exact list would be asserting an
    # accident of the watchlist rather than the property under test.
    assert ("Cayley plane", 0) in _evaluate(unit), (
        "a variant-spelled claim at a section the term is absent from must "
        "evaluate to 0 — that is the offender this axis is meant to catch")


def test_s5_every_control_the_builder_computed_is_carried_and_clean() -> None:
    """Arm S5 — the controls must SHIP, and all of them must be clean.

    ⚠️ **This arm exists because the rc that was written to detect dead seams
    contained one.** ``run_controls`` computed four independent controls; the
    build path read ``positive_control["count"]`` and discarded the rest.
    Three of the four keys — ``negative_verdict``, ``always_true_terms``,
    ``u_fffd_present`` — were read NOWHERE in the tree, and the second
    backend's controls were computed into a dropped return value.

    That was not theoretical. Ghostscript text decoded as latin-1 gives::

        octonion       = 172  PASS   <- ASCII, sails through the misdecode
        Cayley-Dickson = 4    (22)   <- the en-dashed spellings vanish
        U+FFFD present = False       <- the other tell does not fire either

    The one control that would have caught it was computed and thrown away.
    A control the manifest does not CARRY is a control this gate cannot
    CHECK, so the row now carries all four per backend and this arm asserts
    them — which is what makes the guard falsifiable from outside the tool
    that produced it.

    ``collapsed`` rather than ``verdict`` is the asserted field, deliberately:
    a rendered PDF may legitimately carry MORE occurrences than its e-print
    (Rosengren's "Frenkel–Turaev" is 8 in LaTeX, 9 in ghostscript, all nine
    real — the PDF has a table-of-contents line the body source lacks). Only
    a collapse BELOW the floor is the encoding trap.
    """
    for bare, row in sorted(SOURCES.items()):
        controls = row.get("controls") or {}
        assert set(controls) >= {"tex", "gs"}, (
            f"{bare}: source row carries controls for {sorted(controls)}; "
            f"both backends must be represented or a backend's controls are "
            f"being computed and discarded, which is this arm's whole subject")
        for backend, c in sorted(controls.items()):
            where = f"{bare}/{backend}"
            assert int(c["positive_control"]["count"]) > 0, where
            ms = c["multi_spelling"]
            assert ms["collapsed"] is False, (
                f"{where}: multi-spelling control {ms['term']!r} COLLAPSED to "
                f"{ms['count']} below its floor {ms['expected']} "
                f"({ms['by_dash_variant']}) — the encoding-trap signature. "
                f"Every count from this extraction is untrustworthy.")
            assert c["negative_verdict"] == "PASS", (
                f"{where}: terms that must be absent were found "
                f"({c['always_true_terms']}) — the matcher is always-true, so "
                f"its PRESENCE findings carry no information")
            assert c["u_fffd_present"] is False, (
                f"{where}: U+FFFD in the extracted text — a zero is "
                f"undecidable between 'absent' and 'mangled'")
        # The encoding is RECORDED, not assumed. See backend_tex.
        assert row.get("source_tex_encoding"), bare
        assert int(row.get("extraction_chars", 0)) > 0, bare


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
#: through ``help()``, the MCP tool list and the compiled-in C
#: registry, and it shipped with no verdict attached. **Removing a false
#: citation is not a fix; it is a change of defect class**, and nothing in the
#: tree noticed for a whole rc.
#:
#: A ``DERIVED-AND-MEASURED`` verdict also requires a NAMED TEST that EXECUTES
#: the claim, recorded here. Without one it is ``UNSOURCED`` wearing a better
#: word — an ASSERTED algebraic property is not a MEASURED one.
#:
#: ⚠️ **rc428 repair.** The row's fifth field — the OP the named test must
#: actually call — is new, and it exists because the arm was checking the
#: weakest possible thing. S3 asserted ``named_test.exists()`` and nothing
#: more, so it could not distinguish "a test that measures this claim" from
#: "any real file". The row named ``tests/test_loop_bind_moufang.py``, which
#: contains **zero** occurrences of ``malcev_defect``; the file that calls the
#: op and asserts ``d["malcev"] == 0`` is ``tests/test_moufang_loop_rc398.py``.
#: The docstring's substantive claim was true — the named file does verify the
#: Mal'cev identity on 𝕆 by another route — which is precisely why an
#: existence check could not catch it. **A path that resolves is not evidence
#: that the thing at the end of it measures anything.**
S3_VERDICT_CLAIMS: Tuple[Tuple[str, str, str, str, str], ...] = (
    ("Mal'cev", "DERIVED-AND-MEASURED", "tests/test_moufang_loop_rc398.py",
     "cascade/cayley_dickson.py", "malcev_defect"),
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
    for term, verdict, named_test, rel, op in S3_VERDICT_CLAIMS:
        test_path = CC.PY_ROOT / named_test
        assert test_path.exists(), (
            f"{term}: verdict {verdict} names {named_test}, which does not "
            f"exist. A DERIVED-AND-MEASURED verdict with no test that "
            f"EXECUTES the claim is UNSOURCED wearing a better word.")
        # EXISTENCE IS NOT EXERCISE. The named test must actually call the op
        # whose claim it vouches for — see the note on S3_VERDICT_CLAIMS.
        test_src = test_path.read_text(encoding="utf-8")
        assert op in test_src, (
            f"{term}: verdict {verdict} names {named_test}, which exists but "
            f"contains no occurrence of {op!r} — so it does not EXERCISE the "
            f"claim it is cited as measuring. Name the test that calls the "
            f"op, or downgrade the verdict to UNSOURCED.")
        # And the shipped artifact must point at the SAME test, or the row and
        # the docstring can drift apart while both look right in isolation.
        shipped = (CC.PKG_ROOT / rel).read_text(encoding="utf-8")
        assert named_test in shipped, (
            f"{term}: {rel} does not name {named_test}. The row and the "
            f"shipped claim must agree on which test measures it.")
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


# ══ rc429 (`#T1128`) — S6 and S7 ══════════════════════════════════════
#
# WHAT rc428 COULD NOT SEE, AND WHAT rc429 DOES INSTEAD
# =====================================================
# rc428's gate verifies that a cited source CONTAINS the cited claim. A claim
# with **no source** has nothing to check, so that gate cannot see the class by
# construction — and the class is live, shipped, and one instance was created by
# rc427's own fix.
#
# The obvious response — "gate every claim term that has no identifier" — was
# measured and REJECTED. The population is ~1,420 string constants, and the
# discriminators score like this on a 72-site hand-labelled sample:
#
#   bare-eponym-stating-a-relation   262 sites   precision  0/14   ⛔
#   credit-verb ("due to"/"proved")   11 fires   precision  0/11   ⛔
#   ref-block                          0 fires   cannot fire       ⛔
#   auto-extracted eponym vocabulary  6,590 "terms" incl. ABOUT, Optional, Jun
#
# 66 of 72 hand-labelled sites are MENTIONS — using a standard name for a
# standard object, the way "Fourier transform" is used. A gate demanding
# citations on 1,420 sites would provoke bolting a plausible-looking reference
# onto each, **manufacturing exactly the hallucinated-citation defect this arc
# exists to eliminate.** So no attribution-vs-mention classifier ships.
#
# S6 subtracts MENTION **syntactically, by never including it**: its population
# is ``roster × op-fields``, not "strings containing a term". A mention is out of
# scope because nobody put it on the roster, not because a heuristic ruled on it.
# The roster is a TEST-SIDE scope statement, not a source-side escape hatch — a
# module cannot exempt itself, and there is no marker, no ``noqa`` and no opt-in
# field a module can write about itself.

#: The EMITTED PROSE fields of a registered op. Deliberately NOT the whole
#: ``example`` dict.
#:
#: ⚠️ ``worked`` / ``input`` / ``output`` / ``setup`` are EXCLUDED, and the
#: reason is a gate collision rather than taste: ``worked`` is EXECUTED by
#: ``test_worked_examples_execute_rc354.py``, ``input`` is schema-validated by
#: ``test_tool_example_input_schema_rc355.py``, and ``output`` is a literal
#: transcript of what the op prints. A provenance verdict cannot legitimately be
#: placed in any of them. Gating a field whose only repair another gate rejects
#: is a gate demanding an edit the tree forbids — and the predictable escape
#: from that is to weaken one of the two.
#:
#: ⚠️ **This tuple was DECLARED AND NEVER READ through rc429's first cut**, and
#: the comment beside it read *"these four are the fields where prose lives"* —
#: a statement of the gate's scope that was both unenforced and FALSE.
#: :func:`_emitted_fields` hardcoded its own labels, so editing the constant
#: that states the scope changed nothing; and ``ToolEntry.returns.shape`` is
#: emitted prose the constant did not name. Measured: ``moufang_residue``'s
#: shape string is *"one exact Q — 0 iff all three Moufang identities hold at
#: (x, y, z)"*, it occurs **2×** in ``c/src/srmech_tool_registry.c``, and it
#: reaches users through the compiled-in C registry on a path C19 does not
#: cover. Adding it surfaced **2 genuinely bare claims** that had been shipping.
#: The constant is now the single source :func:`_emitted_fields` reads.
#:
#: ``returns.shape`` is safe to gate for the reason ``worked``/``input`` are
#: not: no sibling gate executes or schema-validates it, so a verdict CAN go
#: there. It is prose, in the wheel, read by users.
S6_PROSE_FIELDS: Tuple[str, ...] = ("docstring", "summary", "explanation",
                                    "example.why", "returns.shape")

#: One hand-adjudicated claim: an op, the term naming it, every spelling the
#: tree uses, the WARRANTS that discharge it, and the test that EXECUTES it.
#:
#: ``warrants`` is what makes this arm honest about ``moufang_residue``. Its
#: summary carries a REAL attribution — *Schafer (1966), An Introduction to
#: Nonassociative Algebras, ch. III eqns (7)–(9), read verbatim from Project
#: Gutenberg #25156* — with a chapter-and-equation locator and a public-domain
#: retrieval path. rc428's grammar recognises **arXiv identifiers only**, so it
#: reads that field as bare. Firing there would demand a SECOND citation for a
#: claim that already has a verified one, which is the citation-minting failure
#: mode this whole arc exists to prevent. The row therefore declares ``Schafer``
#: a warrant, and the repair CARRIES the existing attribution into the fields
#: that lack it. **No citation is minted anywhere in this arm.**
S6_ROSTER: Tuple[Tuple[str, str, Tuple[str, ...], Tuple[str, ...], str], ...] = (
    # rc427 deleted a FALSE Baez attribution here and left the claim bare. The
    # docstring and summary were repaired at rc428; the explanation was not.
    ("srmech.cascade.malcev_defect", "Mal'cev", ("Mal'cev",),
     ("DERIVED-AND-MEASURED", "UNSOURCED", "not cited",
      "no attestation is claimed"),
     "tests/test_moufang_loop_rc398.py"),
    # ATTRIBUTED, not unsourced — see the note above. The defect here is that
    # the attribution reaches the summary and not the other three fields.
    ("srmech.cascade.moufang_residue", "Moufang", ("Moufang",),
     ("Schafer", "DERIVED-AND-MEASURED", "UNSOURCED", "not cited",
      "no attestation is claimed"),
     "tests/test_moufang_loop_rc398.py"),
    # The original `#T962` instance: three surnames, zero identifiers, and
    # rc428's arm S3 has no row for it at all. The canonical CWF sources
    # (Călugăreanu 1959–61, White 1969, Fuller 1971 PNAS) are paywalled-only or
    # offline, so under [[feedback_paywalled_doi_cannot_be_attested]] a
    # substituted second unverified citation would be the same defect wearing a
    # different name. DERIVED-AND-MEASURED, and no citation is minted.
    ("srmech.biology.genome.cwf_consistency_mod2", "Calugareanu",
     ("Calugareanu", "Călugăreanu", "CWF"),
     ("DERIVED-AND-MEASURED", "UNSOURCED", "not cited",
      "no attestation is claimed"),
     "tests/test_discrete_writhe_cwf_rc313.py"),
    # A THIRD site the brief did not name. Any repair that fixed only the two
    # briefed sites would have left this one shipping.
    ("srmech.math.covering.linking_number_cwf", "Calugareanu",
     ("Calugareanu", "Călugăreanu", "CWF"),
     ("DERIVED-AND-MEASURED", "UNSOURCED", "not cited",
      "no attestation is claimed"),
     "tests/test_covering_layer_rc422.py"),
)

#: The measured row count. A roster that SHRINKS is a gate being edited toward
#: green, so it is floored rather than trusted.
S6_ROSTER_FLOOR = 4


def _registry():
    warmup_all()
    return get_tool_schema()


def _entry(name: str):
    for tool in _registry().tools:
        if tool.name == name:
            return tool
    raise AssertionError("%s is not in the live registry" % name)


def _callable_for(name: str):
    mod, _, attr = name.rpartition(".")
    return getattr(importlib.import_module(mod), attr)


def _emitted_fields(name: str) -> List[Tuple[str, str]]:
    """``[(field label, text)]`` for every EMITTED PROSE field of one op.

    Reads :data:`S6_PROSE_FIELDS` rather than restating it. The labels and the
    accessors used to be two independent lists, which is how the constant
    stating this gate's scope became unreadable and stale at the same time.
    """
    entry, fn = _entry(name), _callable_for(name)
    example = entry.example or {}
    source = {
        "docstring": lambda: fn.__doc__ or "",
        "summary": lambda: entry.summary or "",
        "explanation": lambda: entry.explanation or "",
        "example.why": lambda: str(example.get("why", "")),
        "returns.shape": lambda: getattr(entry.returns, "shape", "") or "",
    }
    missing = [f for f in S6_PROSE_FIELDS if f not in source]
    assert not missing, (
        "S6_PROSE_FIELDS names %s with no accessor here. The constant and this "
        "function are ONE scope statement — a field named but unreadable is "
        "the declared-and-never-read defect regenerating." % missing)
    return [(label, source[label]()) for label in S6_PROSE_FIELDS]


def _term_present(text: str, spellings: Tuple[str, ...]) -> List[str]:
    return [s for s in spellings if CC.contains_term(text, s)]


def _is_attributed(text: str, present: List[str]) -> bool:
    """Does an identifier-bearing citation in this field CLAIM the term?

    Reuses axes A1–A6 wholesale by going through :func:`CC.parse_units`, so
    source lists, no-claim citations, code spans and multi-locator binding are
    subtracted for free.

    ⚠️ A6 is applied at **CLAIM** scope, and the distinction is load-bearing
    rather than pedantic — my own first probe ran it at FIELD scope, as the
    architect spec specified, and MEASURED the cost: it silenced 7 of 16 sites,
    including four of the five this rc was called for. A whole docstring almost
    always carries one of the eight negation tokens within 60 characters of some
    occurrence of the term, and here they were all statements about the
    MATHEMATICS rather than about a source — "𝕊 is not even alternative, so not
    Moufang", "nor an integer-level CWF", "never rounded". A6 asks whether a
    CLAIM asserts a source LACKS a term; a whole emitted field is not a claim,
    and running the axis there turns it from a subtraction into a blindfold.

    ⚠️ **The occurrence must share a SENTENCE with the identifier**, and that
    bound is a repair. Claim scope runs from the id to the next ``;`` or blank
    line, so through rc429's first cut it swallowed whole following sentences
    and a TOPICALLY UNRELATED identifier laundered a bare claim. Measured::

        See arXiv:1608.06161 — a foundational reference for the theta
        machinery. Separately, the Moufang loops satisfy the identity used
        here.

    read as ATTRIBUTED: the em-dash after a theta-machinery citation opened a
    claim that reached across a full stop and adopted a disconnected sentence
    about Moufang loops. No axis checks topical relevance and none should — that
    is a classifier. A sentence is the syntactic unit over which "this
    identifier is being offered as the warrant for this term" holds, and it is
    the same bound A6 now uses next door, for the same reason.
    """
    for unit in CC.parse_units(text):
        for spelling in present:
            hits = CC.occurrences(unit.claim, spelling)
            if not hits:
                continue
            if CC.asserts_absence(unit.claim, spelling):
                continue        # a negation RECORD, not an attribution
            # The identifier opens the claim at offset 0; an occurrence past
            # the first sentence break is not what the identifier warrants.
            first = CC._sentence_bounds(unit.claim, 0)
            if not any(at < first[1] for at, _end in hits):
                continue
            return True
    return False


def _s6_offenders() -> List[str]:
    out: List[str] = []
    for name, term, spellings, warrants, _test in S6_ROSTER:
        for label, text in _emitted_fields(name):
            present = _term_present(text, spellings)
            if not present:
                continue
            if any(w in text for w in warrants):
                continue
            if _is_attributed(text, present):
                continue
            out.append(
                "%s :: %s\n"
                "    carries %r (spelled %s) with NO identifier and NO warrant\n"
                "    this field SHIPS to users via help() / describe() / the "
                "MCP tool list / the compiled-in C registry"
                % (name, label, term, "/".join(present)))
    return out


def _ast_calls(path: Path, op: str) -> int:
    """How many times ``path`` CALLS ``op`` — ``ast.Call``, never a substring.

    rc428 caught arm S3 asserting ``named_test.exists()``, repaired it to
    ``op in test_src`` — and that is a SUBSTRING match, which ``# see
    malcev_defect`` satisfies. Four files in this tree name ``malcev_defect``
    without calling it. A DERIVED-AND-MEASURED verdict is a claim about what a
    test MEASURES, so the check has to be about execution.
    """
    tree = ast.parse(path.read_bytes(), filename=str(path))
    n = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == op:
            n += 1
        elif isinstance(func, ast.Attribute) and func.attr == op:
            n += 1
    return n


def test_s6_roster_is_not_vacuous() -> None:
    """Three guards, ALL before any offender loop.

    A roster row that no longer resolves, or whose claim has moved, would let
    this arm pass by observing nothing — which is the failure mode the whole rc
    is about, committed by the gate written to catch it.
    """
    assert len(S6_ROSTER) >= S6_ROSTER_FLOOR, (
        "the S6 roster shrank to %d rows (floor %d). A row is removed only when "
        "the CLAIM is gone, and then the term-presence guard below fails first. "
        "A shrinking roster is a gate being edited toward green."
        % (len(S6_ROSTER), S6_ROSTER_FLOOR))

    live = {t.name for t in _registry().tools}
    for name, term, spellings, _warrants, named_test in S6_ROSTER:
        assert name in live, (
            "%s is on the S6 roster but not in the live registry" % name)
        fields = _emitted_fields(name)
        assert any(_term_present(text, spellings) for _l, text in fields), (
            "%s no longer carries a %r claim in any emitted prose field. If the "
            "claim MOVED, move this row; if it was DELETED, delete this row. A "
            "vacuously-passing arm is exactly what rc428 found in arm S3."
            % (name, term))
        path = CC.PY_ROOT / named_test
        assert path.exists(), (name, named_test)
        short = name.rpartition(".")[2]
        assert _ast_calls(path, short) >= 1, (
            "%s: %s does not CALL %s (ast.Call == 0). Existence is not "
            "exercise and a substring is not a call — four files in this tree "
            "name malcev_defect without calling it. Name the test that calls "
            "the op, or downgrade the verdict to UNSOURCED."
            % (name, named_test, short))


def test_s6_call_counter_can_return_zero() -> None:
    """NEGATIVE CONTROL on the ``ast.Call`` counter.

    An instrument that cannot return otherwise is not a measurement. This pins
    BOTH directions on the same fixture text: a file that only NAMES the op in a
    string and a comment reads 0, and the real test reads more than 0.
    """
    named_only = ("# see malcev_defect for the tangent algebra\n"
                  "DOC = 'malcev_defect returns jacobi and malcev'\n"
                  "def test_x():\n"
                  "    assert 'malcev_defect' in DOC\n")
    tmp = CC.PY_ROOT / "tests" / "_s6_control_named_only.py"
    tmp.write_text(named_only, encoding="utf-8")
    try:
        assert _ast_calls(tmp, "malcev_defect") == 0, (
            "the ast.Call counter scored a file that only NAMES the op — it is "
            "measuring substrings, which is the rc428 defect it replaces")
    finally:
        tmp.unlink()
    real = CC.PY_ROOT / "tests" / "test_moufang_loop_rc398.py"
    assert _ast_calls(real, "malcev_defect") >= 1, (
        "the counter reads 0 on a file that demonstrably calls the op — it is "
        "broken, and every zero it has reported is silence, not measurement")


def test_s6_a_claim_with_no_identifier_carries_a_warrant() -> None:
    """Arm S6 — STRICT ZERO, per emitted PROSE FIELD.

    rc428's arm S3 is a hardcoded ONE-ROW tuple, keyed per FILE. Measured on the
    live registry, it sees **1** of the bare (op, term, field) triples this arm
    covers. Per-file is the wrong grain twice over: one verdict in one artifact
    is read as covering several claims in several others, and a claim that ships
    only through ``_tool_docs_curated.py`` is invisible because the file it is
    keyed to looks clean.
    """
    assert S6_ROSTER, "the roster is empty"
    offenders = _s6_offenders()
    assert not offenders, (
        "%d shipped prose field(s) carry a named-source claim with no "
        "identifier and no warrant:\n\n%s\n\n"
        "⚠️ FIX BY CARRYING THE VERDICT, NOT BY MINTING A CITATION. The repair "
        "is to move the DERIVED-AND-MEASURED / UNSOURCED verdict (or an "
        "attribution ALREADY VERIFIED in this tree) into the field that lacks "
        "it. Do NOT type a DOI or an arXiv id from memory, and do NOT copy a "
        "sibling op's citation because the surname matches — that is the rc426 "
        "defect regenerating. If this fired on prose that is CORRECT, the GATE "
        "is wrong: re-scope it by naming an axis in tests/citation_corpus.py, "
        "or remove the roster row and say why in the commit."
        % (len(offenders), "\n\n".join(offenders)))


def test_s6_the_verdict_reaches_the_compiled_registry() -> None:
    """C19 — the verdict must survive codegen into the artifacts users read.

    ``srmech_tool_registry.c`` carries Mal'cev and CWF claim strings and is
    compiled into the wheel, and ``citation_corpus`` walks ``*.py`` only — so
    every arm of this gate is blind to it. The fix is NOT to extend the corpus
    there: that double-counts (measured amplification ~1.94x) and invites a
    hand-edit which the next ``regen_all`` silently reverts, the same trap
    ``GENERATED_MODULES`` already documents for ``_tool_docs.py``.

    Instead the composition ``curated seed → _tool_docs.py → ToolEntry →
    srmech_tool_registry.c`` is ASSERTED rather than assumed. This is the only
    place this file reads C, and it is READ-ONLY.
    """
    generated = CC.PKG_ROOT / "introspect" / "_tool_docs.py"
    registry_c = CC.PKG_ROOT.parent.parent / "c" / "src" / "srmech_tool_registry.c"
    assert generated.exists(), generated
    assert registry_c.exists(), registry_c
    gen_text = generated.read_text(encoding="utf-8")
    c_text = registry_c.read_text(encoding="utf-8", errors="replace")

    checked = 0
    for name, term, _spellings, warrants, _test in S6_ROSTER:
        explanation = _entry(name).explanation or ""
        marker = next((w for w in warrants if w in explanation), None)
        if marker is None:
            continue
        checked += 1
        for artifact, text in (("_tool_docs.py", gen_text),
                               ("srmech_tool_registry.c", c_text)):
            assert marker in text, (
                "%s: the %r warrant for %r is in the ToolEntry explanation but "
                "NOT in %s. Fix the CURATED seed "
                "(srmech/introspect/_tool_docs_curated.py) and run "
                "tools/regen_all.py; NEVER hand-edit either generated file — "
                "the next regen reverts it."
                % (name, marker, term, artifact))
    assert checked >= 1, (
        "no roster row put a warrant in its explanation, so this control "
        "asserted nothing — it cannot distinguish a working codegen path from "
        "an absent one")


# ── S7: identifier-free bibliographies (CEIL, COVERAGE) ───────────────

#: Hand-written string constants carrying a parenthesised year and NO machine
#: identifier anywhere in the constant. **DOWN ONLY.**
#:
#: ⚠️ This is a COVERAGE number, NOT a defect count. It is the class rc428's
#: gate cannot read AT ALL: no identifier means no ``Unit``, so these are not
#: even in S4's coverage residual. Per
#: ``[[feedback_ungated_surfaces_trickle_gated_surfaces_race_to_100]]`` an
#: ungated surface becomes BELIEVED ABSENT, which is why it is counted at all.
#:
#: Most of these are CORRECT. The sharpest example measured is
#: ``_tool_docs_curated.py``'s *"Lenstra-Lenstra-Lovasz reduction (Math. Ann.
#: 261 (1982) 515-534; Cohen, Algorithm 2.6.3)"* — a resolvable, unhallucinated
#: bibliography this gate simply cannot machine-check.
#:
#: Precision at this scale is **UNSUPPORTED**: the year discriminator was
#: measured at 100%/75% on THREE fires in a 72-site sample, not at n=250. A
#: ceiling is a COUNT, which needs no precision — never restate it as a defect
#: count.
#:
#: ⚠️ **Seeded at the POST-repair value, and the direction is instructive.**
#: rc429 measured **250** before its own repair and **253** after. The repair
#: minted no citation: it CARRIED an already-verified attribution (Schafer 1966
#: ch. III eqns (7)–(9)) into the emitted fields that lacked it. S7 counts
#: identifier-free string CONSTANTS, not distinct claims, so propagating one
#: good attribution into three more artifacts necessarily raises it by three.
#:
#: That is not a regression, and reading it as one would invert the incentive:
#: it would reward leaving a verdict stranded in a single artifact — which is
#: precisely the defect arm S6 exists to catch. The two arms pull in opposite
#: directions on purpose, and S7 is the one that must yield, because it is a
#: COVERAGE count and S6 is a defect gate.
#:
#: ⚠️ **The ceiling therefore carries STATED HEADROOM, and it is not slack.**
#: Seeded at the post-repair residual EXACTLY, it had zero — so the very next
#: S6 repair, which works by carrying a verdict into MORE artifacts, would red
#: CI and the tree's only green path would be to strand the verdict. A ratchet
#: whose cheapest satisfying move is the defect it guards against is pointed
#: the wrong way. The headroom is **6**: one roster row's worth of propagation
#: — its 5 emitted prose fields (:data:`S6_PROSE_FIELDS`) plus the curated seed
#: — so a single S6 repair never has to touch this number, and a SECOND one
#: cannot ride through unnoticed.
#:
#: It stays DOWN-ONLY. Headroom is granted once, in the open, with the amount
#: derived from a countable thing; it is not re-granted when consumed. If a
#: repair exhausts it, re-seed at the new residual and say which repair spent
#: it — never widen the allowance.
CEIL_S7_IDENTIFIER_FREE_CITATION = 259

#: A parenthesised year in the range a bibliography uses.
_S7_YEAR = re.compile(r"\((?:1[6-9]\d\d|20[0-2]\d)\)")

#: Any machine identifier. Its PRESENCE removes a constant from this class.
_S7_IDENTIFIER = re.compile(r"arXiv:|10\.\d{4,}/|https?://|ISBN",
                            re.IGNORECASE)


def _s7_residual() -> List[str]:
    out: List[str] = []
    for path in CC.shipped_modules():
        rel = path.relative_to(CC.PKG_ROOT).as_posix()
        for line, value in CC.string_constants(path):
            if _S7_YEAR.search(value) and not _S7_IDENTIFIER.search(value):
                out.append("%s:%d" % (rel, line))
    return out


def test_s7_identifier_free_citation_ceiling() -> None:
    """How many bibliographies ship that NO arm of this gate can verify.

    ⚠️ **There is deliberately NO ``test_s7_ceiling_is_not_slack`` companion,
    and saying why is more load-bearing than the guard would be.** S4 has one
    because S4 drains by ATTESTING a source — a verification act, which is work
    this project wants pressure toward. S7 would drain by ADDING IDENTIFIERS TO
    PROSE — a MINTING act. A not-slack guard on a minting drain applies steady
    pressure toward typing plausible-looking references, which is precisely the
    hallucinated-citation defect this entire arc exists to eliminate. The
    ratchet is one-directional on purpose.
    """
    residual = _s7_residual()
    assert residual, (
        "the S7 residual is ZERO — that is a broken scanner, not a clean tree. "
        "80 modules carried this shape when the ceiling was seeded, and a "
        "measurement that cannot return non-zero is not a measurement.")
    assert len(residual) <= CEIL_S7_IDENTIFIER_FREE_CITATION, (
        "S7 rose to %d identifier-free citations (ceiling %d).\n"
        "Sample — the first 10 of the FULL path-sorted residual, NOT the "
        "entries that entered (this label read 'New:' until the rc456 CI "
        "repair, and it sent the responder to ten long-standing "
        "apokatastasis rows while the one genuine entrant sat in "
        "math/groups.py; diff _s7_residual() against the previous release "
        "tip to locate what actually entered): %s\n\n"
        "⚠️ Lower this ONLY by verifying a source through "
        "tools/build_citation_manifest.py and carrying the identifier IT "
        "RETURNS. **Never type a DOI or an arXiv id from memory to drain this "
        "number.** A ceiling drained with invented identifiers is worse than a "
        "ceiling that never moved."
        % (len(residual), CEIL_S7_IDENTIFIER_FREE_CITATION,
           ", ".join(residual[:10])))


def test_the_validate_entry_point_exits_nonzero_on_a_failing_control() -> None:
    """``--validate`` must FAIL LOUD, not print a summary and return 0.

    rc428's control runner printed ``DEAD SEAM`` and returned success. An entry
    point that reports instead of exiting is how a dead control survives a whole
    rc, so the exit path is pinned here rather than trusted.
    """
    import os
    import subprocess
    import sys

    script = CC.PY_ROOT / "tests" / "citation_corpus.py"
    env = dict(os.environ, PYTHONPATH=str(CC.PY_ROOT))
    env_ok = subprocess.run([sys.executable, str(script), "--validate"],
                            capture_output=True, text=True,
                            cwd=str(CC.PY_ROOT), env=env)
    assert env_ok.returncode == 0, (env_ok.returncode, env_ok.stdout,
                                    env_ok.stderr)
    assert "PASS" in env_ok.stdout, env_ok.stdout

    # The namespace-shadowing trap must name itself. Without PYTHONPATH the
    # source tree imports srmech as a NAMESPACE package (__file__ is None) and
    # this used to surface as a bare pathlib TypeError.
    shadowed = subprocess.run(
        [sys.executable, str(script), "--validate"], capture_output=True,
        text=True, cwd=str(CC.PY_ROOT),
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"})
    if shadowed.returncode != 0:
        assert "NAMESPACE PACKAGE" in shadowed.stderr, (
            "the shadowed import failed WITHOUT naming the cause:\n"
            + shadowed.stderr[-800:])

    # And it must be ABLE to exit non-zero: no argument is a usage error.
    bad = subprocess.run([sys.executable, str(script)], capture_output=True,
                         text=True, cwd=str(CC.PY_ROOT), env=env)
    assert bad.returncode != 0, (
        "citation_corpus.py returned 0 without --validate — an entry point "
        "that cannot exit non-zero cannot report a failing control either")


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
    s6_fires = [f for f in S6_BITE_FIXTURES if f[2]]
    s6_silents = [f for f in S6_BITE_FIXTURES if not f[2]]
    assert len(s6_fires) >= 4, "S6's bite is unproven"
    assert len(s6_silents) >= 6, "S6's false positives are unguarded"

    # A SILENT fixture carrying no roster term short-circuits at
    # `bool(present)` and cannot fire whatever the axes do — so counting it as
    # a false-positive guard is the count lying. Measured at rc429: 6 of 7
    # silents were vacuous, and the guard above was satisfied entirely by rows
    # that could not fire. Require the axes to actually be REACHED.
    reaching = [f for f in s6_silents if _term_present(f[1], f[3])]
    assert len(reaching) >= 3, (
        "only %d of %d SILENT S6 fixtures carry a roster term at all; the "
        "rest short-circuit at `bool(present)` and prove nothing about false "
        "positives. Add fixtures whose term IS present and which are silenced "
        "by a REASON — a warrant, an attribution, or a named axis."
        % (len(reaching), len(s6_silents)))

    # …and at least one must reach the ATTRIBUTED branch, or _is_attributed's
    # True side has no fixture at all (measured: 0 of 75 live fields take it).
    attributed = [f for f in s6_silents
                  if _is_attributed(f[1], _term_present(f[1], f[3]))]
    assert attributed, (
        "no SILENT fixture drives _is_attributed True. That branch is then "
        "untaken by the tree AND unexercised by the suite, which is "
        "indistinguishable from dead code.")


# ── S6's own both-sides bite ──────────────────────────────────────────
#
# Every fixture is TREE TEXT — the four FIRE cases are the shipped prose as it
# stood at rc428, so the bite survives its own repair. rc428 states the
# principle and it applies with more force here: a gate whose bite depends on a
# live defect stops biting the moment the defect is fixed, and this rc fixes all
# four of them in the same commit.
#
# The SILENT cases are drawn from the 66 hand-labelled MENTIONS in rc429's
# scope sample, cited by sample index. If S6 ever fires on one of them, the
# roster has become a classifier and the arm is wrong.
S6_BITE_FIXTURES: Tuple[Tuple[str, str, bool, Tuple[str, ...], str], ...] = (
    ("site 1 — _tool_docs.py:233 explanation, rc428 state",
     "The tangent algebra of a Moufang loop under the commutator bracket "
     "[x,y]=x.y-y.x is a MAL'CEV algebra: anticommutative, but the Jacobi "
     "identity FAILS -- replaced by the weaker Mal'cev identity "
     "J(x,y,[x,z])=[J(x,y,z),x]",
     True, ("Mal'cev",),
     "Term present, no identifier, no verdict, no negation. This SHIPPED to "
     "users via the MCP tool list and the compiled-in C registry."),
    ("site 2 — tool_schema.py cwf summary, rc428 state",
     "rc313 — the mod-2 Calugareanu-White-Fuller consistency check on a "
     "strand: Lk == Tw + Wr (mod 2). Three INDEPENDENTLY-computed reads.",
     True, ("Calugareanu", "Călugăreanu", "CWF"),
     "11 of 11 CWF carriers were bare and rc428's arm S3 has no CWF row at "
     "all, so no arm of the shipped gate could see this."),
    ("site 3 — covering.py:288, the NON-ASCII spelling",
     "``Lk = Tw + Wr`` — the INTEGER invariant recovered from two "
     "frame-relative rationals (Călugăreanu–White–Fuller). The theorem's "
     "content is an asymmetry the mod-2 shadow destroys",
     True, ("Calugareanu", "Călugăreanu", "CWF"),
     "The en-dashed, diacritic spelling. ZERO of rc428's 32 manifest terms "
     "match any CWF spelling, so the vocabulary was blind to it by "
     "construction. Neither briefed defect named this site."),
    ("site 4 — moufang_residue explanation, rc428 state",
     "WHAT: the Moufang defect of an ordered triple (x, y, z) -- the max, "
     "over the three Moufang identities M1 x.(y.(x.z))=((x.y).x).z",
     True, ("Moufang",),
     "The fifth site, named by neither the brief nor the scope arms in full. "
     "The Schafer attribution reached the summary and not this field."),
    ("MENTION sample 16 — Frenkel–Turaev",
     "the Frenkel–Turaev ₈ω₇ summation over a balanced very-well-poised "
     "series",
     False, ("Moufang", "Mal'cev", "Calugareanu"),
     "A standard NAME for a standard object. Not on the roster, so out of "
     "S6's population entirely — subtracted syntactically, not judged."),
    ("MENTION sample 23 — Faddeev-Leverrier",
     "the characteristic polynomial via Faddeev-Leverrier",
     False, ("Moufang", "Mal'cev", "Calugareanu"), "MENTION."),
    ("MENTION sample 21 — Apagodu-Zeilberger",
     "Apagodu-Zeilberger creative telescoping over the summand",
     False, ("Moufang", "Mal'cev", "Calugareanu"), "MENTION."),
    ("AMBIGUOUS — cd_register.py:721, one of the sample's 2",
     "capped at min(dim,8)−1 by Hurwitz",
     False, ("Moufang", "Mal'cev", "Calugareanu"),
     "If S6 fires here the roster has become a classifier and the arm is "
     "wrong. It stays silent because no roster row names this op."),
    ("the REPAIRED malcev summary — A6 must subtract it",
     "The Mal'cev verdict is DERIVED-AND-MEASURED, not cited: rc427 verified "
     "that Baez arXiv:math/0105155 — cited here through rc426 for 'the "
     "Mal'cev tangent algebra' — contains NO occurrence of Mal'cev in any "
     "spelling.",
     False, ("Mal'cev",),
     "Without A6 at CLAIM scope this reads as an attribution of Mal'cev to "
     "Baez — the exact claim rc427 deleted — and S6 would score the FIX as "
     "the defect."),
    ("A8 — the live phantom",
     "the dual of an operator-side honest",
     False, ("Fano",),
     "densify() joins 'of an o' into 'ofano'. Silent today only because "
     "1009.0369 is unattested; attesting it would make S1 fire on correct "
     "prose."),
    ("A8 — the inflection arm, INVERSE polarity",
     "factorization of elliptic functions",
     False, ("Moufang",),
     "Carries no roster term, so S6 is silent. Its A8 half — that "
     "'elliptic function' MUST still match the plural — is control C15."),
    # ── NON-VACUOUS silents (rc429 repair) ───────────────────────────
    # Every SILENT row above is silent because _term_present returns [] — the
    # predicate short-circuits at `bool(present)` and NEVER REACHES the axes it
    # is supposed to be proving. Measured: 6 of 7. They are kept (they pin that
    # a MENTION stays out of scope) but they cannot guard a false positive,
    # because a fixture carrying no term cannot fire whatever the axes do. The
    # three rows below DO carry a roster term and are silenced by a REASON.
    ("NON-VACUOUS silent — warranted by an existing attribution",
     "The MOUFANG DEFECT of an ordered triple, measured against the three "
     "Moufang identities of Schafer ch. III eqns (7)-(9).",
     False, ("Moufang",),
     "present=['Moufang'] — the term IS here, so the predicate runs to the "
     "end. Silenced by the WARRANT arm, on an attribution this tree already "
     "verified. No citation is minted to make this pass."),
    ("NON-VACUOUS silent — ATTRIBUTED, the only control on that branch",
     "Baez (2002), arXiv:math/0105155, §3 — the Moufang plane and its "
     "collineation group",
     False, ("Moufang",),
     "The ONLY fixture that drives _is_attributed True. Measured: 0 of 75 "
     "live emitted fields carrying a roster spelling are attributed, so that "
     "branch is BOUNDED-at-zero by the tree, not EMPTY — and an untaken "
     "branch with no fixture is indistinguishable from a dead one. "
     "SYNTHETIC and labelled as such: no tree text exercises it, which is "
     "the measurement, not an excuse."),
    ("NON-VACUOUS silent — A9, the identifier that is not a claim",
     "SIBLINGS -- ``srmech.biology.genome.cwf_consistency_mod2`` checks the "
     "same relation mod 2, and this op keeps the exact rational.",
     False, ("Calugareanu", "Călugăreanu", "CWF"),
     "covering.py's rc428 explanation, VERBATIM. Its only CWF match sat "
     "inside a dotted path, and the strict-zero arm fired on a field with no "
     "claim in it. present=[] here only BECAUSE axis A9 subtracts it — "
     "control C20 pins that the term is otherwise found, so this row measures "
     "the axis rather than an absence."),
)


@pytest.mark.parametrize("label,text,should_fire,spellings,why",
                         S6_BITE_FIXTURES,
                         ids=[f[0] for f in S6_BITE_FIXTURES])
def test_s6_still_bites(label: str, text: str, should_fire: bool,
                        spellings: Tuple[str, ...], why: str) -> None:
    """Both sides of S6's predicate, on real tree text and with no repo edit.

    The predicate is exercised directly rather than through the roster, because
    the roster is a SCOPE statement and the thing under test is whether the rule
    can tell a bare claim from an attributed one and from a mention.
    """
    present = _term_present(text, spellings)
    warranted = any(w in text for w in ("DERIVED-AND-MEASURED", "UNSOURCED",
                                        "not cited", "Schafer",
                                        "no attestation is claimed"))
    fired = bool(present) and not warranted and not _is_attributed(text, present)

    if should_fire:
        assert fired, (
            f"{label}: S6 did NOT fire on prose known to carry a bare claim.\n"
            f"  {why}\n  text: {text[:120]!r}\n"
            f"  present={present} warranted={warranted}\n"
            f"A guard that cannot fire is decorative, and every verdict this "
            f"arm has rendered is downgraded to UNSUPPORTED.")
    else:
        assert not fired, (
            f"{label}: S6 FIRED on prose known to be FINE {present!r}.\n"
            f"  {why}\n  text: {text[:120]!r}\n"
            f"⚠️ Do NOT add a citation to silence this. The ARM is wrong — "
            f"either the roster has become a classifier, or an axis in "
            f"tests/citation_corpus.py needs re-scoping. Minting a reference "
            f"to make this green is the defect this whole arc exists to "
            f"eliminate.")


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
