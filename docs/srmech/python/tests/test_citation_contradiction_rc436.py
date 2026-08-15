"""THE citation-CONTRADICTION gate — v0.9.0rc436 (local task T1141).

Fails the build when the SAME shipped wheel asserts, of one source, both that
it is openly retrievable and that it is not.

WHY THIS GATE EXISTS
====================
rc317 registered ``srmech.math.rational.relative_writhe`` with this in its
``ToolEntry`` summary, and it was CORRECT::

    Cites F. Brock Fuller PNAS 68(4):815-819 (1971,
    doi 10.1073/pnas.68.4.815, PMC389050) ... both OA.

rc429 then wrote a provenance paragraph for the Călugăreanu–White–Fuller
relation which said, of the same paper::

    The canonical CWF sources (Calugareanu 1959-61, White 1969, Fuller 1971)
    are paywalled-only or offline, so no attestation is claimed for the name
    and none is substituted unverified.

Both shipped. For four releases (rc429 → rc435) the wheel simultaneously told
users that Fuller 1971 was OA with two identifiers AND that it was
paywalled-only or offline, across **seven** source surfaces — the C tool
registry (×4), ``CHANGELOG.md``, ``biology/genome.py``,
``introspect/tool_schema.py``, ``introspect/_tool_docs.py``,
``introspect/_tool_docs_curated.py`` and ``math/covering.py`` — reaching users
through ``describe()``, the MCP tool list and the compiled-in C registry.

**Nothing in the tree could see it.** ``test_citation_manifest_rc428.py`` is the
citation gate, and it asks a different question: does the cited SOURCE contain
the cited CLAIM. It joins the tree to an external measurement of a source. This
contradiction needs no external measurement at all — it is decidable from the
tree alone, because the tree disagrees with ITSELF. That is the gap this file
closes, and it is why the fix for rc436 is a gate and not just a string edit:
the string edit repairs one paper, the gate repairs the CLASS.

WHAT IT CHECKS
==============
For every source SURNAME the tree cites with an OA identifier, that surname must
not appear in any clause asserting non-retrievability, anywhere in the
wheel-shipping surfaces.

Both halves are DERIVED from the tree, not listed here — there is no hardcoded
roster of paper names to go stale. The gate discovers the surnames itself.

SCOPE, STATED
=============
Scanned: ``srmech/**/*.py`` (which includes the generated ``_tool_docs.py``) and
``c/src/srmech_tool_registry.c``. Those are the surfaces that travel inside the
wheel and reach users through ``describe()``, the MCP tool list and the
compiled-in C registry — the same population ``test_citation_manifest_rc428.py``
targets and for the same reason.

**NOT scanned: ``CHANGELOG.md``.** It is a dated historical record, and the
rc429 entry there is annotated in place with its correction rather than
rewritten, so it deliberately contains the false sentence beside the words that
retract it. A gate over it would be measuring history, not shipped claims.

CLAUSES, NOT SENTENCES
======================
Resolution is per CLAUSE (split on ``.`` ``;`` ``—``), because the corrected
prose legitimately names all three sources in one sentence: Fuller in a clause
that affirms retrievability, Călugăreanu and White in a clause that denies it.
A sentence-level gate would fire on correct prose, which per the rc428 rule
("never edit a citation to make a gate green — if it fires on something correct,
the GATE is wrong") would make the gate the defect.

Double-quoted spans are stripped before a clause is judged, so prose that
DOCUMENTS a retracted claim by quoting it is not read as asserting it. Same
exemption principle as the ref-notation gate's code spans.

NON-CLAIM
=========
This gate does not check whether any retrievability claim is TRUE. It checks
only that the tree does not make both claims about one source. A wheel that
uniformly asserts something false about a paper passes here — that is
``test_citation_manifest_rc428.py``'s axis, and the two are complementary.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SR_ROOT = Path(__file__).resolve().parents[2]
PKG = SR_ROOT / "python" / "srmech"
C_REGISTRY = SR_ROOT / "c" / "src" / "srmech_tool_registry.c"

#: Phrases that ASSERT a source cannot be retrieved.
UNRETRIEVABLE = (
    "paywalled-only or offline",
    "paywalled-only",
    "paywalled only",
    "offline from here",
)

#: Phrases that ASSERT a source IS retrievable. An OA identifier alone is not
#: enough — a DOI can be printed for a paywalled paper, which is precisely the
#: case `[[feedback_paywalled_doi_cannot_be_attested]]` is about.
OA_POSITIVE = (
    "both oa",
    "is oa",
    "openly retrievable",
    "free pdf",
    "is open (",
    ", oa",
)

#: An OA identifier: PubMed Central, or a DOI.
IDENTIFIER = re.compile(r"PMC\d{4,}|10\.\d{4,}/[^\s,)\"]+")

#: A cited surname IMMEDIATELY followed by a year — "Fuller 1971", "White 1969",
#: "Fuller (1971", "Calugareanu 1959-61". Accents allowed. This builds the
#: ROSTER only; membership on each side is then tested by word presence, because
#: a correct OA citation does not keep the name adjacent to the year
#: ("Cites F. Brock Fuller PNAS 68(4):815-819 (1971, doi …)").
CITED_NAME = re.compile(
    r"\b([A-Z][\wÀ-ɏ]{3,})\s*\(?\s*(?:1[89]\d\d|20\d\d)\b")

_QUOTED = re.compile(r'"[^"]*"')

#: Split on period-SPACE, semicolon-SPACE and spaced dashes — never on a bare
#: ".", which would shred a DOI ("10.1073/pnas.68.4.815") and a version string
#: into fragments and hide the identifier from its own clause. That bug made the
#: first draft of this gate report Fuller as un-cited; the control caught it.
_CLAUSE_SPLIT = re.compile(r"(?<=[.;])\s+|\s—\s|\s--\s")


def _surfaces():
    """Every wheel-shipping surface, as (label, text)."""
    for p in sorted(PKG.rglob("*.py")):
        yield str(p.relative_to(SR_ROOT)), p.read_text(encoding="utf-8")
    if C_REGISTRY.exists():
        yield (str(C_REGISTRY.relative_to(SR_ROOT)),
               C_REGISTRY.read_text(encoding="utf-8", errors="replace"))


def _clauses(text: str):
    for raw in _CLAUSE_SPLIT.split(text):
        # A clause that only CONTAINS a phrase inside quotes is documenting it,
        # not asserting it.
        yield raw, _QUOTED.sub(" ", raw)


def _scan():
    """(oa_names, unretrievable_hits) derived wholly from the tree.

    Two passes. The FIRST builds the surname roster by name-adjacent-to-year,
    which is reliable but strict. The SECOND asks, per clause, whether a roster
    surname is PRESENT in an OA-asserting clause or in an unretrievable-asserting
    one — presence, not adjacency, because a well-formed citation separates the
    surname from the year with the journal and volume.
    """
    surfaces = [(label, " ".join(text.split())) for label, text in _surfaces()]

    roster = set()
    for _label, flat in surfaces:
        roster |= {m.group(1) for m in CITED_NAME.finditer(flat)}

    oa_names, unret = set(), {}
    for label, flat in surfaces:
        for raw, judged in _clauses(flat):
            low = judged.lower()
            hit_oa = (any(p in low for p in OA_POSITIVE)
                      and IDENTIFIER.search(judged))
            hit_neg = any(p in low for p in UNRETRIEVABLE)
            if not (hit_oa or hit_neg):
                continue
            present = {n for n in roster
                       if re.search(rf"\b{re.escape(n)}\b", judged)}
            if hit_oa:
                oa_names |= present
            if hit_neg:
                for n in present:
                    unret.setdefault(n, []).append((label, raw.strip()[:220]))
    return oa_names, unret


def test_no_source_is_both_oa_and_unretrievable():
    """STRICT ZERO. The defect rc436 repaired, as a standing gate."""
    oa_names, unret = _scan()
    both = sorted(set(oa_names) & set(unret))
    assert not both, (
        "a source is asserted BOTH openly-retrievable AND unretrievable in the "
        "same wheel — the rc429 Fuller defect, recurring:\n"
        + "\n".join(
            f"  {n}: OA asserted elsewhere, but denied at\n"
            + "\n".join(f"      {lab}: {frag}" for lab, frag in unret[n])
            for n in both)
        + "\n\nFix the claim that is WRONG. Do not delete the OA citation to "
          "silence this — that converts a contradiction into an unsourced "
          "claim, which is a change of defect class, not a repair.")


def test_the_scan_is_not_vacuous():
    """A null from an instrument that visited nothing is not a measurement.

    Both halves must be non-empty on the shipped tree, or the strict zero above
    could be a false green from a regex that matches nothing.
    """
    oa_names, unret = _scan()
    assert oa_names, "no OA-asserted source names found — the OA half is dead"
    assert unret, ("no unretrievable-asserted source names found — the "
                   "negative half is dead")
    assert "Fuller" in oa_names, (
        "Fuller is no longer detected as OA-asserted. relative_writhe has "
        "shipped that citation since rc317 and cwf_consistency_mod2 since "
        "rc436; if it is genuinely gone, this gate lost its subject.")


def test_calugareanu_and_white_are_still_on_the_unretrievable_list():
    """The repair was SCOPED, and this pins that it stayed scoped.

    rc436 corrected the claim about Fuller ONLY. Nothing was verified about
    Călugăreanu 1959–61 or White 1969, so no claim about them changed and they
    must still be recorded as not retrievable. A later edit that quietly
    promoted them to OA — the easy over-correction — lands here.
    """
    _, unret = _scan()
    names = set(unret)
    assert any(n.startswith("Calugareanu") or n.startswith("Călug") for n in names), (
        f"Calugareanu dropped off the unretrievable list; found {sorted(names)}")
    assert "White" in names, (
        f"White dropped off the unretrievable list; found {sorted(names)}")


@pytest.mark.parametrize("planted", [
    # the exact rc429 sentence, restored
    "The canonical CWF sources (Calugareanu 1959-61, White 1969, Fuller 1971) "
    "are paywalled-only or offline, so no attestation is claimed.",
    # the same defect wearing different words
    "Fuller (1971) is paywalled-only from here, so nothing is attested.",
])
def test_control_the_gate_fires_on_a_planted_contradiction(monkeypatch, planted):
    """MANDATORY CONTROL — an instrument that cannot return otherwise is not a
    measurement.

    Plant the retracted sentence back into the scanned population and assert the
    strict-zero test would FAIL. Without this, a regex that silently stopped
    matching would leave the gate permanently, invisibly green.
    """
    real = _surfaces

    def _with_planted():
        yield from real()
        yield "planted://rc429-regression", planted

    monkeypatch.setitem(globals(), "_surfaces", _with_planted)
    oa_names, unret = _scan()
    assert "Fuller" in oa_names, "control precondition: Fuller must read as OA"
    assert "Fuller" in unret, (
        "THE CONTROL FAILED: the planted rc429 contradiction was NOT detected, "
        "so the strict-zero test above proves nothing. Fix the scanner.")
