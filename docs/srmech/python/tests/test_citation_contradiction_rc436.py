"""THE citation-CONTRADICTION gate — v0.9.0rc436 (local task T1141).

Two strict zeros, both decidable from the tree alone:

**S1 — CONTRADICTION.** No source may be asserted both RETRIEVABLE and
UNRETRIEVABLE in the same wheel.

**S2 — CONFLATION.** No clause may call a PMC-hosted source "OA" without saying
it is not in the PMC Open Access Subset. PMC hosting is a RETRIEVABILITY fact;
Open Access is a LICENCE fact. Conflating them is what produced S1's defect.

WHY THIS GATE EXISTS — AND WHY BOTH SHIPPED SURFACES WERE WRONG
===============================================================
rc317 registered ``srmech.math.rational.relative_writhe`` saying, of Fuller
1971::

    ... doi 10.1073/pnas.68.4.815, PMC389050 ... both OA.

rc429 then wrote, of the same paper::

    The canonical CWF sources (Calugareanu 1959-61, White 1969, Fuller 1971)
    are paywalled-only or offline ...

Both shipped, for four releases (rc429 → rc435), across **seven** surfaces
reaching users through ``describe()``, the MCP tool list and the compiled-in C
registry. The obvious reading is that one of them was right.

**Neither was.** Measured against NCBI E-utilities rather than against either
srmech surface — since both were in dispute — ``oa.fcgi`` returns::

    <error code="idIsNotOpenAccess">identifier 'PMC389050' is not Open Access</error>

for **both** PMC389050 and PMC392823. So the paper is **free-to-read at PMC but
not in the PMC Open Access Subset**: rc429 understated its AVAILABILITY and
rc317 overstated its LICENCE. The true statement is a third thing neither
surface made, and the reason the tree could hold two contradictory beliefs for
four releases is that nothing distinguished the two questions.

``[[feedback_paywalled_doi_cannot_be_attested]]`` keys on **retrievability**, so
Fuller 1971 is attestable — and rc436 attests it properly, from the author's own
institutional repository (Caltech), content-addressed. That is *stronger* than
the secondary-review chain the original complaint was about.

A four-route retrievability sweep (2026-08-15, F1354) then found **all three**
sources on the first search — Fuller at Caltech, White 1969 in the Edinburgh
archive, Călugăreanu 1959–61 in DML-CZ — so there is **no residual
not-retrievable list**. Only Fuller is content-addressed, so only Fuller carries
an MPR-grade record; the other two are retrievable and merely not yet hashed.

**"We could not retrieve it" is a fact about the ATTEMPT, never about the
SOURCE.** A publisher 403 is bot-blocking, not evidence — an automated client is
not a reader. That is why the UNRETRIEVABLE population below is expected to be
EMPTY on a healthy tree, and why the planted controls, not the live population,
are what prove this instrument can fire.

WHAT S2 BUYS THAT S1 DOES NOT
=============================
S1 catches the tree disagreeing with itself. It could not have caught rc317
alone, because rc317's overclaim was internally consistent — nothing
contradicted it until rc429 arrived. S2 catches the *category error itself*, in
a single clause, with no second surface required: "this is on PMC, therefore it
is OA" is wrong the moment it is written.

S2 is deliberately narrow. It does **not** ban the word OA — arXiv really is
open, and ``octonion_table_attestation`` says so correctly. It fires only where
an OA claim rides a **PMC** identifier, which is the measured confusion.

DESIGN — NO ROSTER, SO NOTHING ROTS
===================================
Both axes derive their subject from the tree. The surname roster is built by
name-adjacent-to-year and then tested by PRESENCE, because a well-formed
citation separates the surname from the year. There is no list of paper names
to go stale, and no list of "known OA" sources to maintain.

SCOPE, STATED
=============
Scanned: ``srmech/**/*.py`` (including the generated ``_tool_docs.py``) and
``c/src/srmech_tool_registry.c`` — the surfaces that travel inside the wheel.
NOT scanned: ``CHANGELOG.md``, a dated record whose rc429 entry is annotated in
place rather than rewritten, so it deliberately contains the false sentence
beside the words retracting it; and ``tests/``, which is not shipped.

CLAUSES, NOT SENTENCES
======================
Resolution is per clause (split on ``. `` ``; `` and spaced dashes — never a
bare ``.``, which shreds a DOI). The corrected prose legitimately names all
three sources in one sentence: Fuller in a clause affirming retrievability,
Călugăreanu and White in a clause denying it. Double-quoted spans are stripped
before judging, so prose that DOCUMENTS a retracted claim by quoting it is not
read as asserting it — the ref-notation gate's code-span exemption, same idea.

NON-CLAIM
=========
Neither axis checks whether a retrievability claim is TRUE; that needs an
external measurement and is ``test_citation_manifest_rc428.py``'s axis. These
check only that the tree does not hold two incompatible claims (S1) and does not
derive a licence from a host (S2).
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

#: Phrases that ASSERT a source CAN be retrieved. Note these are RETRIEVABILITY
#: claims, not licence claims — the distinction this gate exists to keep.
RETRIEVABLE = (
    "is retrievable",
    "retrievable and",
    "free-to-read",
    "free to read",
    "openly retrievable",
    "is attested",
    "and is attested",
)

#: Phrases that assert an OPEN LICENCE. A different question entirely.
OA_CLAIM = ("both oa", "is oa", ", oa.", " oa,", "open access")

#: Saying the quiet part: an OA mention that is EXPLICITLY scoped as a denial or
#: a correction is not an OA claim. These are the words rc436 added.
OA_SCOPED = (
    "idisnotopenaccess",
    "not in the pmc open access subset",
    "neither is in the pmc open access",
    "not \"oa\"",
    "not oa",
)

#: An identifier: PubMed Central, or a DOI.
IDENTIFIER = re.compile(r"PMC\d{4,}|10\.\d{4,}/[^\s,)\"]+")
PMC_ID = re.compile(r"PMC\d{4,}")

#: A cited surname IMMEDIATELY followed by a year. Builds the ROSTER only.
CITED_NAME = re.compile(
    r"\b([A-Z][\wÀ-ɏ]{3,})\s*\(?\s*(?:1[89]\d\d|20\d\d)\b")

_QUOTED = re.compile(r'"[^"]*"')

#: Markdown emphasis and code ticks, stripped before phrase matching. Without
#: this, a scoping phrase written as "though **not** in the PMC Open Access
#: Subset" does not match "not in the pmc open access subset" and the gate fires
#: on prose that is already correct — measured on covering.py while writing this.
_EMPH = re.compile(r"[*`_]+")

#: Split on period-SPACE, semicolon-SPACE and spaced dashes — never a bare ".",
#: which would shred "10.1073/pnas.68.4.815" and hide the identifier from its
#: own clause. That bug made the first draft report Fuller as un-cited.
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
        yield raw, _QUOTED.sub(" ", raw)


def _scan():
    """(retrievable_names, unretrievable_hits, oa_conflations)."""
    surfaces = [(label, " ".join(text.split())) for label, text in _surfaces()]

    roster = set()
    for _label, flat in surfaces:
        roster |= {m.group(1) for m in CITED_NAME.finditer(flat)}

    ok, bad, conflate = set(), {}, []
    for label, flat in surfaces:
        for raw, judged in _clauses(flat):
            low = _EMPH.sub("", judged.lower())
            has_id = bool(IDENTIFIER.search(judged))
            hit_ok = any(p in low for p in RETRIEVABLE) and has_id
            hit_bad = any(p in low for p in UNRETRIEVABLE)

            # S2: an OA LICENCE claim riding a PMC (host) identifier, unscoped.
            if (PMC_ID.search(judged)
                    and any(p in low for p in OA_CLAIM)
                    and not any(s in low for s in OA_SCOPED)):
                conflate.append((label, raw.strip()[:220]))

            if not (hit_ok or hit_bad):
                continue
            present = {n for n in roster
                       if re.search(rf"\b{re.escape(n)}\b", judged)}
            if hit_ok:
                ok |= present
            if hit_bad:
                for n in present:
                    bad.setdefault(n, []).append((label, raw.strip()[:220]))
    return ok, bad, conflate


def test_s1_no_source_is_both_retrievable_and_unretrievable():
    """STRICT ZERO — the rc429-vs-rc317 defect, as a standing gate."""
    ok, bad, _ = _scan()
    both = sorted(set(ok) & set(bad))
    assert not both, (
        "a source is asserted BOTH retrievable AND unretrievable in the same "
        "wheel — the rc429/rc317 defect, recurring:\n"
        + "\n".join(
            f"  {n}: retrievability asserted elsewhere, but denied at\n"
            + "\n".join(f"      {lab}: {frag}" for lab, frag in bad[n])
            for n in both)
        + "\n\nFix the claim that is WRONG. Do not delete the citation to "
          "silence this — that converts a contradiction into an unsourced "
          "claim, a change of defect class rather than a repair.")


def test_s2_no_pmc_hosted_source_is_called_open_access():
    """STRICT ZERO — the CATEGORY ERROR, catchable in one clause.

    PMC hosting is retrievability; the Open Access Subset is licence. rc317's
    "both OA" was internally consistent and no contradiction existed until rc429
    arrived, so S1 alone could not have caught it. Measured: NCBI oa.fcgi returns
    idIsNotOpenAccess for BOTH PMC389050 and PMC392823.
    """
    _, _, conflate = _scan()
    assert not conflate, (
        "a PMC-hosted source is called OPEN ACCESS without saying it is not in "
        "the PMC Open Access Subset:\n"
        + "\n".join(f"  {lab}: {frag}" for lab, frag in conflate)
        + "\n\nPMC hosting is a RETRIEVABILITY fact; OA is a LICENCE fact. Say "
          "free-to-read, or say explicitly that it is not in the Open Access "
          "Subset. Verify with NCBI oa.fcgi rather than by inspecting the tree, "
          "which is what made this wrong for four releases.")


def test_the_scan_is_not_vacuous():
    """A null from an instrument that visited nothing is not a measurement.

    Note what is NOT asserted: that the UNRETRIEVABLE population is non-empty.
    After the 2026-08-15 sweep the healthy state of this tree is that no source
    is claimed unretrievable at all, so requiring a live example would be a gate
    demanding the defect it exists to forbid. The planted controls carry that
    burden instead — they prove the negative detector still fires on prose the
    tree no longer contains.
    """
    ok, _bad, _ = _scan()
    assert ok, "no retrievability-asserted source names found — that half is dead"
    assert "Fuller" in ok, (
        "Fuller is no longer detected as retrievability-asserted. rc436 attests "
        "it from the Caltech institutional repository and both "
        "cwf_consistency_mod2 and relative_writhe say so; if that is genuinely "
        "gone, this gate lost its subject.")


def test_no_source_is_claimed_unretrievable_at_all():
    """The sweep's consequence, pinned.

    All three CWF sources were found on the first search, so the package should
    make NO source-level unretrievability claim about them. This is the positive
    form of the amendment: not "the list shrank" but "there is no list".

    It is deliberately narrow — it names the three papers rather than asserting
    the global population is empty, because an unrelated future citation might
    legitimately record a failed attempt in ATTEMPT language this scanner would
    not match anyway.
    """
    _, bad, _ = _scan()
    offenders = {n: hits for n, hits in bad.items()
                 if n.startswith(("Calugareanu", "Călug", "White", "Fuller"))}
    assert not offenders, (
        "a CWF source is still claimed unretrievable, but the 2026-08-15 "
        "four-route sweep found all three on the first search:\n"
        + "\n".join(f"  {n}: {hits}" for n, hits in sorted(offenders.items()))
        + "\n\n'We could not retrieve it' is a fact about the ATTEMPT, never "
          "about the SOURCE. Rewrite it as an attempt, or drop it.")


@pytest.mark.parametrize("planted", [
    "The canonical CWF sources (Calugareanu 1959-61, White 1969, Fuller 1971) "
    "are paywalled-only or offline, so no attestation is claimed.",
    "Fuller (1971) is paywalled-only from here, so nothing is attested.",
])
def test_control_s1_fires_on_a_planted_contradiction(monkeypatch, planted):
    """MANDATORY CONTROL — an instrument that cannot return otherwise is not a
    measurement. Plant the retracted sentence and assert S1 would FAIL."""
    real = _surfaces

    def _with_planted():
        yield from real()
        yield "planted://rc429-regression", planted

    monkeypatch.setitem(globals(), "_surfaces", _with_planted)
    ok, bad, _ = _scan()
    assert "Fuller" in ok, "control precondition: Fuller must read as retrievable"
    assert "Fuller" in bad, (
        "THE CONTROL FAILED: the planted rc429 contradiction was NOT detected, "
        "so S1 proves nothing. Fix the scanner.")


@pytest.mark.parametrize("planted", [
    # the exact rc317 overclaim, restored
    "Cites F. Brock Fuller PNAS 68(4):815-819 (1971, doi 10.1073/pnas.68.4.815, "
    "PMC389050) + PNAS 75(8):3557-3561 (1978, doi 10.1073/pnas.75.8.3557, "
    "PMC392823), both OA.",
    # the same category error in other words
    "Freely available as Open Access at PMC389050.",
])
def test_control_s2_fires_on_a_planted_conflation(monkeypatch, planted):
    """MANDATORY CONTROL for the second axis, including the verbatim rc317 line."""
    real = _surfaces

    def _with_planted():
        yield from real()
        yield "planted://rc317-overclaim", planted

    monkeypatch.setitem(globals(), "_surfaces", _with_planted)
    _, _, conflate = _scan()
    assert any(lab.startswith("planted://") for lab, _ in conflate), (
        "THE CONTROL FAILED: the planted PMC-is-OA conflation was NOT detected, "
        f"so S2 proves nothing. Detected: {conflate}")
