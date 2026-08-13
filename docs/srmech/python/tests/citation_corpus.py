"""THE shared LITERATURE-citation parser — one definition, every citation gate.

v0.9.0rc428 (`#T1126`), the citation-contains-term arc.

⚠️ THIS IS A HELPER MODULE, NOT A TEST MODULE. Named ``citation_corpus.py``
rather than ``test_citation_corpus.py`` so pytest does not collect it. It is
the sibling of ``tests/adr_corpus.py``, which does the same job for the ADR
corpus's ``path:line`` citations. That module and this one share nothing but
the pattern, because they parse disjoint corpora: ``adr_corpus`` reads
``docs/srmech/adr/*.md`` for pointers INTO the tree; this module reads
hand-written **shipped package source** for pointers OUT to the literature.

WHY THIS FILE EXISTS
====================
srmech's MPM discipline is *a citation without attestation is not real; an
attestation that can't be re-verified is broken.* Measured at rc428: **zero**
gates covered literature citations in shipped source. All identifier-bearing
citations in the package — and their copies inside the generated artifacts that
reach users through ``describe()``, the MCP tool list and the compiled-in C
registry — were entirely ungated, which is how six citation defects reached
published wheels while every attestation gate stayed green.

Two of those gates were worse than absent. Six tests assert
``source_url == "https://arxiv.org/abs/math/0105155"`` — the tree asserting that
the tree says what it says. That literal *is* the citation that was FALSE at
``cayley_dickson.py``, and those tests were green throughout.

THE UNIT IS AN AST STRING CONSTANT, NOT A LINE
===============================================
Measured, and it is the single most load-bearing implementation choice here.
A line-based scan of this tree reports **four truncated DOIs** that do not
exist: all four are Python implicit string concatenation, e.g.::

    "... Turin (1960), IEEE Trans. Inform. Theory 6, DOI 10.1109/TIT."
    "1960.1057571. ..."

which is ONE citation spelling ``10.1109/TIT.1960.1057571`` correctly. A
line-based gate therefore invents defects in one direction and, in the other,
cannot see a citation whose identifier and claim sit on different source lines
— which is the normal shape of a wrapped docstring. Everything below reads
fully-resolved ``ast.Constant`` values.

MATCHING IS UNICODE-EXACT AND WHITESPACE-INSENSITIVE
=====================================================
Also measured, also in this tree rather than in a PDF. On the single most-cited
concept the tree spells ``Cayley–Dickson`` with an **en-dash 248 times** and
with an ASCII hyphen 164 times. An ASCII-only matcher sees 40% of it. Dash
folding here is the same fold the manifest builder applies, so a term crosses
the join intact.

THE AXES
========
Each is a SYNTACTIC subtraction, per the ``test_owner_axis_rc410.py`` model:
no file is named, no line is named, there is no ``noqa``. Each exists because a
measured false positive forced it, and none can delete a term from prose that
carries an attribution mark bound to an identifier — which is what a false
attributed claim looks like.

``A1`` SOURCE-LIST SEPARATOR
    ``;`` or a blank line ends claim scope. Forced by
    ``cd_register.py``'s ``Hurwitz (1898); Baez arXiv:math/0105155; Kanerva
    (2009) *Hyperdimensional Computing*.`` — three sources, each correctly
    attributed. A fixed-width window read Kanerva as a claim ABOUT Baez and
    reported a defect. That is trap 2 committed by the instrument measuring
    trap 2, and it is exactly the batch "fix" that would have broken a working
    citation.

``A2`` NO-CLAIM CITATION
    A citation with no attribution mark (`` — ``, `` – ``, `` (``, ``: ``)
    after its locator asserts nothing and cannot be false. Measured: **19.7%**
    of citation units are identifier + locator with no claim at all, and 53%
    make no attributed claim. A gate without this axis fires on half the corpus.

``A3`` MULTI-LOCATOR BINDING
    ``§3 (claimA) + §4.2 (claimB)`` binds each claim to ITS OWN locator. Forced
    by ``cayley_plane.py``'s module docstring, and treated as hostile because
    the rc428 architect's own parser got it wrong. It is also what makes the
    rc428 finding visible at all: that one parenthesis pair carries a CORRECT
    §4.2-for-𝕆P² claim and a FALSE §4.2-for-Hopf-fibration claim, and a parser
    that merges them can only return one verdict for both.

``A4`` CODE SPAN
    A token inside a ````...```` span is code, not a claim
    term. Forced by ``Iterable`` / ``Optional`` / ``Aut`` / ``Out`` appearing in
    a scan of candidate claim terms.

``A5`` BYLINE REGION
    Text BEFORE the identifier is bibliographic. Author names, journal, volume
    and page runs live there. Implemented by construction — claim scope starts
    at the identifier's end — rather than as a subtraction, which is why it
    cannot be tuned.

``A6`` NEGATED CLAIM — a claim asserting ABSENCE is not asserting presence
    Forced by the two prose sites that RECORD the rc427 fix. Both ship::

        "…cited here through rc426 for 'the Mal'cev tangent algebra' —
         contains NO occurrence of Mal'cev in any spelling…"
        "…rc427 narrowed it, because that section states no Moufang
         identity and the adjacent Moufang ops were citing it as though
         it did."

    Without this axis the gate fires on the paragraph written to record that
    the term is absent — it fires on the fix. The axis is the same
    *negative-existence* class the ADR bare-path survey found on its own side,
    arriving here from the citation direction.

    Scoped per SENTENCE — not per occurrence, and no longer whole-claim. The
    governing principle is that **a single assertion cannot coherently claim
    both that the source contains T at L and that it contains no T**; when
    prose does both, it is a correction record and the gate has nothing to
    falsify in it. That is why the axis is not per-occurrence: the Mal'cev
    paragraph names the term twice, once inside quote marks reproducing the
    RETRACTED claim and once under the negation, and a per-occurrence rule
    would fire on the first.

    ⚠️ It was WHOLE-CLAIM through rc429's first cut, and at that scope it
    laundered a false citation. Claim scope ends at ``;`` or a blank line, so
    it spans sentences — and ``"…§2 — the Moufang identities. There is no
    Moufang loop structure on the sedenions."`` had a TRUE second sentence
    about the mathematics silence a FALSE first one about a source. A sentence
    is the largest unit over which "this text denies the source has T" stays
    one assertion, so the coherence argument is applied there and stops at the
    full stop. Control C22.

    It cannot launder a real defect: every one of the four genuine rc428
    findings (three Hopf-at-§4.x, one Fano-at-§4.1) carries no negation token
    anywhere in its claim, and :func:`_self_check` control C10 pins that a
    plain false claim still fires with this axis live.

``A8`` WORD BOUNDARY IN THE ORIGINAL TEXT (rc429)
    ``densify`` deletes whitespace, so a dense match may span a join that never
    existed. Per-occurrence. See :func:`_bounded_occurrence`.

``A9`` CODE IDENTIFIER (rc429)
    A match inside ``moufang_residue`` or ``genome.cwf_consistency_mod2`` is a
    cross-reference, not a claim. A8 alone accepts them, because ``_`` and
    ``.`` are not alphanumeric and so read as word boundaries. Forced by a
    MEASURED false positive: a strict-zero arm fired on a field whose only
    match sat inside a dotted path. Per-occurrence. See
    :func:`_identifier_adjacent`.

WHAT THIS PARSER DELIBERATELY DOES NOT DO
==========================================
It does not EXTRACT claim terms. Auto-extraction was measured and REFUTED: a
scan of shipped citations yielded 175 distinct candidates whose most frequent
members were ``Crossref`` (31), ``Iterable``, ``Optional``, ``Jun`` and
``Der``. The vocabulary comes from the manifest and only from the manifest.

CONTROLS ABORT, THEY DO NOT REPORT
===================================
rc428 produced **four** distinct false nulls in its own instruments — a
``timeout`` returning 0 and being read as a clean result, an unescaped ``]``
that closed a character class early and yielded 0 DOIs from a tree with 37, a
minimal-match regex that reported the strict-zero class EMPTY, and an
extraction returning 0 for both "Moufang" and "octonion" from a paper titled
*The Octonions*. Every one was caught by a control, and none by review. So the
controls here are INLINE and they raise: see :func:`_self_check`, which runs at
import and refuses to hand out a parser that cannot parse its own fixtures.
"""

from __future__ import annotations

import ast
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import srmech

#: The installed package root — the same anchor ``adr_corpus`` uses.
#:
#: ⚠️ ``srmech.__file__ is None`` means a NAMESPACE PACKAGE was imported, not
#: the real one — the source-tree shadowing this project has been bitten by
#: before (``[[feedback_verify_the_artifact_under_test_is_the_one_you_think]]``).
#: Left unguarded it surfaced as a bare ``TypeError: expected str … not
#: NoneType`` from inside ``pathlib``, which names neither the cause nor the
#: fix. Measured while building the ``--validate`` entry point at rc429.
if srmech.__file__ is None:                            # pragma: no cover
    raise ImportError(
        "srmech imported as a NAMESPACE PACKAGE (__file__ is None), so this "
        "corpus would scan nothing. Put the package root on PYTHONPATH — e.g. "
        "PYTHONPATH=<repo>/docs/srmech/python — and re-run.")
PKG_ROOT = Path(srmech.__file__).resolve().parent

#: ``python/`` — the package's parent, holding ``tests/`` and ``tools/``.
PY_ROOT = PKG_ROOT.parent


# ── the population ────────────────────────────────────────────────────


#: Files under ``srmech/`` that a GENERATOR writes. Their citation text is a
#: COPY of hand-written prose (measured amplification: ~1.94x), so gating them
#: would double-count every defect and, worse, invite a fix applied to the
#: generated copy — which the next ``regen_all`` silently reverts.
#:
#: Derived from ``tools/codegen_manifest`` declarations at rc428; asserted
#: against the live manifest by the gate's own non-vacuity guard rather than
#: trusted, because a new generator landing here unnoticed is exactly how a
#: generated file gets hand-edited.
GENERATED_MODULES: Tuple[str, ...] = (
    "introspect/_tool_docs.py",
    "introspect/_c_claims.py",
)

#: Directory names never walked. Same list as ``adr_corpus.EXCLUDED_DIR_NAMES``
#: and for the same measured reason: a stale session worktree under
#: ``docs/srmech/.claude/worktrees/`` shadows ``tool_schema.py``, and a scanner
#: that reads it reports a clean corpus from a snapshot months old.
#:
#: ⚠️ :func:`_excluded` matches ANY path component, so an EXCLUDED ANCESTOR
#: zeroes the corpus — an ad-hoc script run from inside a session worktree
#: scans nothing at all. That is the intended behaviour and not a hole in CI:
#: the non-vacuity floors below (``>= 200`` modules, ``>= 100`` units, ``>= 15``
#: sources) are real assertions that FAIL LOUD on an empty walk rather than
#: reporting a clean tree. It is called out here because the symptom in a
#: scratch measurement is a confident zero, and a zero from this cause looks
#: exactly like a zero from a clean corpus.
EXCLUDED_DIR_NAMES = frozenset({
    "__pycache__", ".claude", "worktrees", "build", "_skbuild",
    "site-packages", "node_modules", ".git", "dist", ".venv",
})


def _excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


@lru_cache(maxsize=1)
def shipped_modules() -> Tuple[Path, ...]:
    """Every HAND-WRITTEN ``.py`` under ``srmech/``, generated files removed."""
    gen = {(PKG_ROOT / g).resolve() for g in GENERATED_MODULES}
    return tuple(sorted(
        p for p in PKG_ROOT.rglob("*.py")
        if not _excluded(p) and p.resolve() not in gen))


@lru_cache(maxsize=1)
def generated_modules() -> Tuple[Path, ...]:
    """The generator-written peers, for the amplification measurement."""
    return tuple(sorted(p for g in GENERATED_MODULES
                        if (p := PKG_ROOT / g).exists()))


@lru_cache(maxsize=512)
def string_constants(path: Path) -> Tuple[Tuple[int, str], ...]:
    """Every ``str`` constant in a module as ``(lineno, fully-joined value)``.

    ``ast`` resolves implicit concatenation for us, which is the whole point —
    see the module docstring on the four DOIs a line scan invents. A file that
    does not parse RAISES rather than yielding nothing: a parser that returns
    an empty tuple for a broken file is a false null with a friendly face.
    """
    tree = ast.parse(path.read_bytes(), filename=str(path))
    out: List[Tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append((node.lineno, node.value))
    return tuple(out)


# ── normalisation: the same fold the manifest builder applies ─────────

#: Every dash spelling a typesetter or an author may emit. Folded to a single
#: class so ``Cayley–Dickson`` and ``Cayley-Dickson`` are one term. The 248-vs-164
#: split on this exact name is measured IN THIS TREE, not in a PDF.
DASHES = "-‐‑‒–—―−"
APOSTROPHES = "'’ʼ′´`"


def densify_indexed(text: str) -> Tuple[str, List[int]]:
    """``(dense, idx)`` where ``idx[k]`` is ``dense[k]``'s offset in ``text``.

    The index is what lets axis A6 read a window of the ORIGINAL prose around a
    hit found in the dense copy. Without it, negation detection would have to
    run on whitespace-stripped text, where ``"statesnoMoufang"`` has no word
    boundaries left for the negation tokens to anchor to.
    """
    chars: List[str] = []
    idx: List[int] = []
    for i, ch in enumerate(text):
        if ch.isspace():
            continue
        chars.append("-" if ch in DASHES else ch)
        idx.append(i)
    return "".join(chars), idx


def densify(text: str) -> str:
    """Whitespace-stripped, dash-folded matching copy.

    Whitespace-insensitivity is load-bearing rather than decorative: the
    manifest builder measured ``"Cayley–Dick son"`` out of one PDF backend and
    ``"Thm\\n   3"`` wraps occur in this tree's own docstrings. A gate written
    the obvious way reports 16 of 22 — a CORRECT citation called false, which
    is the mirror of a false null and equally damaging.
    """
    return densify_indexed(text)[0]


def term_pattern(term: str) -> str:
    """Regex for ``term`` against DENSE text. Mirrors the manifest builder.

    ⚠️ The dash class is dash-**optional** (``[DASHES]*``), not dash-normalising,
    and that is deliberate rather than a loose quantifier nobody chose. It is
    forced by :func:`densify`: whitespace is DELETED before matching, so the
    perfectly ordinary spelling ``Cayley Dickson`` arrives as ``CayleyDickson``
    with no separator left to match. A ``?`` or a ``+`` would report that
    correct spelling as absent, which is the false-negative half of the same
    error A8's inflection arm was added to avoid.

    The measured cost of ``*`` is that ``CayleyDickson`` — a typo, not a
    spelling — also matches. That is accepted: this axis exists to make a
    citation harder to falsely clear, and a typo matching its own term errs
    toward EVALUATING a claim rather than silencing one. Control C25 pins both
    halves, because a quantifier documented only in a maintainer's head is
    indistinguishable from one that was never chosen.
    """
    out: List[str] = []
    for ch in term:
        if ch in DASHES:
            out.append("[%s]*" % re.escape(DASHES))
        elif ch in APOSTROPHES:
            out.append("[%s]" % re.escape(APOSTROPHES))
        elif ch.isspace():
            continue
        else:
            out.append(re.escape(ch))
    return "".join(out)


# ── axis A8: the match needs a word boundary in the ORIGINAL text ─────

#: An English inflection the trailing boundary tolerates. Measured, and the
#: measurement is the whole justification: with a STRICT trailing rule the
#: shipped corpus carries **2** phantoms, one of which is a FALSE NEGATIVE —
#: ``math/carrier_spectrum.py``'s "factorization of elliptic functions" stops
#: matching the watchlist term ``elliptic function``, silencing a legitimate
#: plural claim. With the inflection arm it carries **1**, the real one. A8 is
#: therefore correct-in-BOTH-directions only with this arm, and the strict form
#: is a measured false negative rather than a tighter gate.
#:
#: Deliberately NOT widened to ``-ian`` / ``-ic``: no site in this tree forces
#: them, and an unforced widening is an exemption nobody measured.
_INFLECTIONS: Tuple[str, ...] = ("'s", "’s", "es", "s")


def _alnum(ch: str) -> bool:
    return ch.isalnum()


def _bounded_occurrence(text: str, lo: int, hi: int) -> bool:
    """Axis A8 — does ``text[lo:hi]`` sit on a word boundary in the ORIGINAL?

    ``densify`` DELETES whitespace, so a match found in the dense copy may span
    a join that never existed in the source. :func:`term_pattern` builds a bare
    regex with no boundary of its own, and the two together invent identifiers.
    Measured LIVE in this tree, inside a string a citation unit really parses::

        apokatastasis/riemann_theta.py — "…the dual of an operator-side honest…"
        dense: "…thedual[ofano]perator-sidehonest…"   ⇒  contains "Fano"

    That phantom is silent TODAY only because ``1009.0369`` is not attested, so
    the unit sits in S4's coverage residual rather than in S1's strict-zero
    population. S4 is a down-only CEIL **designed to drain by attesting
    sources** — so the moment somebody performs the one action the gate asks
    for, "Fano" is evaluated against a Riemann-theta / Schottky paper, reads 0,
    and the STRICT-ZERO arm fires **on correct prose**. That is precisely the
    rc427 failure this gate's own docstring forbids, armed and waiting behind
    the gate's own drain path. It is a live defect, not a hypothetical.

    The second measured phantom is ``Bott`` — S1's census found **33** dense
    hits in the tree and **0** real ones: every occurrence is ``Bottom``.

    SCOPED PER-OCCURRENCE, NOT WHOLE-CLAIM — and the difference from A6 is
    deliberate rather than accidental. A6 is whole-claim because *a single
    claim cannot coherently assert both that a source contains T and that it
    contains none*, so a mixed claim is a correction record with nothing to
    falsify. A8 has no such coherence argument available: a phantom is a
    parsing accident with no relationship to the genuine occurrence beside it,
    so a whole-claim veto would let one accidental substring silence a real
    false citation in the same sentence. The two axes therefore run at
    OPPOSITE scopes, on purpose, and control C18b pins the mixed case.
    """
    if lo > 0 and _alnum(text[lo - 1]):
        return False
    if hi >= len(text) or not _alnum(text[hi]):
        return True
    tail = text[hi:]
    for suffix in _INFLECTIONS:
        if tail.startswith(suffix):
            after = hi + len(suffix)
            if after >= len(text) or not _alnum(text[after]):
                return True
    return False


# ── axis A9: a CODE IDENTIFIER is not a claim (rc429 repair) ──────────


def _identifier_adjacent(text: str, lo: int, hi: int) -> bool:
    """Axis A9 — is ``text[lo:hi]`` part of a longer CODE IDENTIFIER?

    A8 asks for a word boundary and gets one from ``_`` and ``.``, because
    neither is alphanumeric. So ``srmech.biology.genome.cwf_consistency_mod2``
    contains a *bounded occurrence* of the term ``CWF``, and a cross-reference
    to a sibling op is scored as a claim about a source.

    THAT IS NOT HYPOTHETICAL, AND IT IS NOT SYMMETRIC WITH A8'S PHANTOM.
    Measured on this tree at the rc428 state, arm S6 evaluated four ops across
    ten emitted prose fields, and ``srmech.math.covering.linking_number_cwf ::
    explanation`` carried **exactly one** occurrence of any CWF spelling — the
    one inside that dotted path, in a ``SIBLINGS --`` cross-reference. The field
    contained no claim at all, and a STRICT-ZERO arm fired on it and demanded a
    prose edit.

    That is the failure mode this whole arc exists to prevent, arriving from
    the gate's own side: a provenance gate that fires on prose carrying no
    claim applies steady pressure to bolt a plausible-looking reference onto
    correct text. The gate's own failure message says so — *"If this fired on
    prose that is CORRECT, the GATE is wrong: re-scope it by naming an axis"* —
    so this is that axis, named, rather than a roster row quietly deleted or a
    file exempted.

    The rule is deliberately NARROW, and each clause is forced by a measured
    spelling rather than chosen for symmetry:

    * ``_`` on either side. Prose never puts an underscore against a word;
      ``moufang_residue``, ``is_moufang`` and ``cwf_consistency_mod2`` all do.
    * ``.`` on the LEFT with an alphanumeric or ``_`` before it — a dotted
      continuation, as in ``genome.cwf_consistency_mod2``.

    A trailing ``.`` is deliberately NOT a marker. In prose it is overwhelmingly
    a sentence terminator, and treating it as an identifier join would silence
    every claim term that happens to end a sentence — trading this false
    positive for a far larger false negative.

    Measured blast radius over the whole shipped corpus: **204** occurrences
    removed, of which **0** sit inside a parsed citation ``Unit`` claim. Arms
    S1/S2/S3/S4 read exactly the same numbers before and after; every removal is
    a C symbol name or a dotted Python path. Control C20 pins the live site,
    C21 pins the negative direction.
    """
    if lo > 0 and text[lo - 1] == "_":
        return True
    if hi < len(text) and text[hi] == "_":
        return True
    if (lo >= 2 and text[lo - 1] == "."
            and (text[lo - 2].isalnum() or text[lo - 2] == "_")):
        return True
    return False


def occurrences(text: str, term: str) -> List[Tuple[int, int]]:
    """Every A8- and A9-bounded occurrence of ``term`` as ``(start, end)``.

    THE single definition of what an occurrence IS. :func:`contains_term` and
    :func:`asserts_absence` both route through it so the two axes cannot
    disagree about what they are looking at — a disagreement there re-opens the
    hole A6's control C10 closes, from the other side. A9 is applied HERE, at
    the same per-occurrence scope as A8, for that same reason: an axis applied
    on one side of that pair and not the other is how the two stop agreeing.
    """
    dense, idx = densify_indexed(text)
    out: List[Tuple[int, int]] = []
    for m in re.finditer(term_pattern(term), dense, re.IGNORECASE):
        if m.start() >= len(idx):                      # pragma: no cover
            continue
        lo = idx[m.start()]
        hi = idx[m.end() - 1] + 1
        if _bounded_occurrence(text, lo, hi) and not _identifier_adjacent(
                text, lo, hi):
            out.append((lo, hi))
    return out


def contains_term(haystack: str, term: str) -> bool:
    """Is ``term`` present in ``haystack``, dash- and whitespace-insensitively?

    Axis A8 applies: a dense match with no word boundary in the ORIGINAL text
    is a join artifact, not an occurrence.
    """
    return bool(occurrences(haystack, term))


# ── axis A6: an absence-assertion is not a presence-assertion ─────────

#: The negation tokens. A FIXED, SHORT, word-boundaried list — not a pattern
#: language. Word boundaries are load-bearing: an unanchored ``no`` matches
#: inside ``norm``, ``normalise``, ``nonzero`` and ``notation``, all of which
#: occur in this tree's citation prose, and each such match would silence a
#: real claim.
#:
#: ⚠️ ``"zero"`` was a token through rc429's first cut and is REMOVED, under
#: this list's own stated standard. The A8 inflection note next door refuses to
#: widen to ``-ian``/``-ic`` because *"no site in this tree forces them, and an
#: unforced widening is an exemption nobody measured"* — and every token here
#: SILENCES a claim, so an unforced token is that same exemption with more
#: consequence. Measured: **0** live citation units in the shipped corpus have
#: their absence-assertion resting on ``"zero"``; removing it moves no verdict.
#: What it did carry was a false positive, in a tree where "zero" is a QUANTITY
#: on nearly every line — ``"the ring has zero divisors, and the Moufang
#: identities are established"`` read as an assertion that the source LACKS
#: "Moufang", silencing a real claim that ordinary docstring prose would write
#: by accident. Control C23 pins it.
NEGATION_TOKENS: Tuple[str, ...] = (
    "no", "not", "never", "none", "nor", "absent", "without",
)

_NEGATION = re.compile(
    r"\b(" + "|".join(NEGATION_TOKENS) + r")\b", re.IGNORECASE)

#: How far back a negation may govern a term. Measured against the two real
#: sites: ``contains NO occurrence of Mal'cev`` needs 21 characters and
#: ``states no Moufang identity`` needs 10. 60 leaves headroom for a wrapped
#: docstring without reaching into a neighbouring sentence, and a sentence
#: terminator inside the window stops the search regardless.
NEGATION_WINDOW = 60


#: A sentence break in the ORIGINAL prose: a terminator followed by space.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s")


def _sentence_bounds(text: str, at: int) -> Tuple[int, int]:
    """``(lo, hi)`` of the sentence containing offset ``at``."""
    lo = 0
    for m in _SENTENCE_BREAK.finditer(text[:at]):
        lo = m.end()
    nxt = _SENTENCE_BREAK.search(text, at)
    return lo, (nxt.start() if nxt else len(text))


def _negated_at(claim: str, at: int) -> bool:
    """Is the occurrence at ``at`` governed by a negation token before it?"""
    window = claim[max(0, at - NEGATION_WINDOW):at]
    # A sentence terminator ends the governing clause.
    for stop in (". ", ".\n", "! ", "? "):
        cut = window.rfind(stop)
        if cut != -1:
            window = window[cut + len(stop):]
    return _NEGATION.search(window) is not None


def asserts_absence(claim: str, term: str) -> bool:
    """Axis A6 — does ``claim`` assert that the source LACKS ``term``?

    True iff **every sentence of the claim that carries an occurrence of
    ``term`` carries a NEGATED one.** Governing is backward-only within a
    sentence: a negation governs what FOLLOWS it, and scanning forward as well
    would let ``the Moufang identities. This does not …`` silence a real claim
    from the next sentence.

    ⚠️ **Whole-claim OR was the rc429 spelling and it laundered a false
    citation. The scope is now the SENTENCE, and the reason is precisely the
    coherence argument the OR was built on.** That argument — *a single claim
    cannot coherently assert both that a source contains T and that it contains
    none, so a mixed claim is a correction record with nothing to falsify* — is
    sound, and it is why this is not simply an AND over occurrences. It has to
    stay an OR *within* a sentence, or the tree's real correction records break:
    ``cited here through rc426 for 'the Mal'cev tangent algebra' — contains NO
    occurrence of Mal'cev in any spelling`` has a BARE first occurrence and a
    negated second one, in one sentence, and it is exactly the paragraph written
    to record a fix (control C10).

    What the argument does NOT license is reaching across a full stop. Measured:

        Baez arXiv:math/0105155, §2 — the Moufang identities. There is no
        Moufang loop structure on the sedenions.

    Sentence one is a false citation; sentence two is an independently TRUE
    statement about the mathematics. Under whole-claim OR the true sentence
    silenced the false citation, and the rc426 defect class re-opened wearing an
    ordinary compound sentence. Sentence-scoped, sentence one carries a bare
    occurrence, ``all()`` fails, and the claim is evaluated. Control C22.

    This is the same distinction the S6 arm hit from the other side: field-scope
    A6 silenced 7 of 16 sites because a whole docstring almost always contains a
    negation about the MATHEMATICS somewhere. A sentence is the largest unit
    over which "this text is denying the source has T" stays a single assertion.

    Iterates the SAME A8/A9-bounded occurrences :func:`contains_term` sees. If
    the two disagreed, a phantom could be read as a negated claim and silence a
    real one — the C10 hole arriving from the other side.
    """
    occ = occurrences(claim, term)
    if not occ:
        return False
    by_sentence: Dict[Tuple[int, int], bool] = {}
    for at, _end in occ:
        span = _sentence_bounds(claim, at)
        by_sentence[span] = by_sentence.get(span, False) or _negated_at(
            claim, at)
    return all(by_sentence.values())


# ── the grammar ───────────────────────────────────────────────────────

#: An arXiv identifier in either scheme, with an optional version suffix.
#: Old scheme ``math/0105155``; new scheme ``1608.06161``. The version is
#: captured SEPARATELY because the manifest keys on the bare id and carries the
#: version as an attribute — otherwise a tree spelling both ``1608.06161`` and
#: ``1608.06161v3`` reports one of them as an uncovered phantom source.
_ARXIV = re.compile(
    r"arXiv:\s*("
    r"(?:[a-z-]+(?:\.[A-Z]{2})?/\d{7})"        # math/0105155
    r"|(?:\d{4}\.\d{4,5})"                      # 1608.06161
    r")(v\d+)?", re.IGNORECASE)

#: A section locator. ``§4.2``, ``§1``, and the RANGE forms ``§1–§2`` /
#: ``§4.1–§4.2`` the tree really uses. Ranges are expanded by
#: :func:`_expand_range` rather than treated as one opaque label.
_LOCATOR = re.compile(
    r"§\s*(\d+(?:\.\d+)*)"
    r"(?:\s*[%s]\s*§?\s*(\d+(?:\.\d+)*))?" % re.escape(DASHES))

#: The marks that turn following prose into an ATTRIBUTED CLAIM (axis A2).
#: An em/en dash, an opening parenthesis, or a colon. A comma is deliberately
#: NOT one: ``arXiv:math/0105155, §4.2`` is a citation continuing to its own
#: locator, not an attribution.
_ATTRIBUTION_MARKS = ("—", "–", "(", ":")

#: Ends claim scope (axis A1). ``;`` separates SOURCES in a source list; a
#: blank line ends the citation paragraph.
_SCOPE_END = re.compile(r";|\n\s*\n")

#: A code span (axis A4).
_CODE_SPAN = re.compile(r"``.*?``|`[^`]*`", re.DOTALL)


def _expand_range(lo: str, hi: Optional[str]) -> Tuple[str, ...]:
    """``(§1, §2)`` -> ``("§1", "§2")``; ``(§4.1, §4.2)`` -> both.

    Only expands when the two endpoints share a parent and differ in the LAST
    component, which is the only range shape this tree writes. Anything else
    keeps both endpoints verbatim rather than inventing the span between them
    — a gate that guesses at ``§2–§4`` would silently widen every claim's
    scope, and widening scope is how a false citation passes.
    """
    if hi is None:
        return ("§" + lo,)
    lo_parts, hi_parts = lo.split("."), hi.split(".")
    if len(lo_parts) == len(hi_parts) and lo_parts[:-1] == hi_parts[:-1]:
        try:
            a, b = int(lo_parts[-1]), int(hi_parts[-1])
        except ValueError:
            return ("§" + lo, "§" + hi)
        if 0 <= b - a <= 12:
            head = lo_parts[:-1]
            return tuple("§" + ".".join(head + [str(k)])
                         for k in range(a, b + 1))
    return ("§" + lo, "§" + hi)


def _strip_code_spans(text: str) -> str:
    """Axis A4 — blank out code spans, preserving length so offsets survive."""
    return _CODE_SPAN.sub(lambda m: " " * len(m.group(0)), text)


class Unit:
    """One citation unit: an identifier, its locators, and what each claims."""

    __slots__ = ("source_id", "version", "locator", "claim", "path", "line",
                 "raw")

    def __init__(self, source_id: str, version: str, locator: Optional[str],
                 claim: str, path: str, line: int, raw: str) -> None:
        #: BARE arXiv id, e.g. ``math/0105155`` — never versioned.
        self.source_id = source_id
        #: ``"v3"`` or ``""``. An attribute, never part of the key.
        self.version = version
        #: A canonical ``§N.M`` label, or ``None`` for a presence-only unit.
        self.locator = locator
        #: The attributed claim text, code spans blanked. ``""`` = axis A2.
        self.claim = claim
        self.path = path
        self.line = line
        self.raw = raw

    @property
    def has_claim(self) -> bool:
        return bool(self.claim.strip())

    def __repr__(self) -> str:                          # pragma: no cover
        return "Unit(%s %s %r @%s:%d)" % (
            self.source_id, self.locator, self.claim[:40], self.path,
            self.line)


def parse_units(text: str, path: str = "", line: int = 0) -> List[Unit]:
    """Every citation unit in one resolved string constant.

    Staged, NOT one regex. The rc428 architect's first attempt was a single
    pattern with an optional locator group and a non-greedy middle; on the real
    string ``arXiv:math/0105155, §2 — the Cayley–Dickson doubling convention``
    it matched MINIMALLY and returned no locator and no claim. Had that been
    trusted it would have reported the strict-zero population EMPTY and killed
    this gate as unbuildable. Stages cannot do that to you silently, and
    :func:`_self_check` pins this exact string.
    """
    units: List[Unit] = []
    for m in _ARXIV.finditer(text):
        sid = m.group(1)
        version = (m.group(2) or "").lower()

        # ── A1 + A5: scope runs from the id's END to the next source break.
        rest = text[m.end():]
        stop = _SCOPE_END.search(rest)
        scope = rest[:stop.start()] if stop else rest

        # ── A4: code spans are not prose. Length-PRESERVING, so every offset
        #        below indexes both copies identically.
        raw_scope, scope = scope, _strip_code_spans(scope)

        locs = list(_LOCATOR.finditer(scope))
        if not locs:
            units.append(Unit(sid, version, None,
                              _claim_after(raw_scope, scope, 0),
                              path, line, scope[:160]))
            continue

        # ── A3: each locator owns the text up to the NEXT locator.
        for i, lm in enumerate(locs):
            end = locs[i + 1].start() if i + 1 < len(locs) else len(scope)
            claim = _claim_after(raw_scope, scope, lm.end(), end)
            for label in _expand_range(lm.group(1), lm.group(2)):
                units.append(Unit(sid, version, label, claim, path, line,
                                  scope[lm.start():end][:160]))
    return units


def _claim_after(raw: str, stripped: str, start: int,
                 end: Optional[int] = None) -> str:
    """Axis A2 — the attributed claim following an attribution MARK, or ``""``.

    Everything between ``start`` and the first mark is citation apparatus
    (``, §4.2``, ``[math.CA] (2017)``) and asserts nothing. If no mark is
    present the unit carries no claim, cannot be false, and is never evaluated.

    ⚠️ **The mark is located in ``raw`` and the claim is taken from
    ``stripped``**, and splitting the two is a repair rather than a nicety.
    Both were read from the code-span-stripped copy through rc429, so a mark
    that happened to fall INSIDE a code span was blanked with it — and since a
    unit with no mark carries no claim, the entire following sentence left the
    strict-zero population. Measured on ``arXiv:math/0105155, §3 `` ``—`` `` the
    exceptional Jordan algebra is discussed at length``: the claim read ``''``
    with the span and ``'the exceptional Jordan algebra is discussed at
    length'`` without it. Real prose escaping S1 by construction is the same
    class of hole as a false claim passing it, approached from the other end.

    A4's actual purpose survives untouched: code-span CONTENTS are still not
    claim terms, because the claim text still comes from ``stripped``.
    :func:`_strip_code_spans` is length-preserving precisely so the two copies
    share an index space and this split costs nothing. Control C24.
    """
    hi = end if end is not None else len(raw)
    window = raw[start:hi]
    best = -1
    for mark in _ATTRIBUTION_MARKS:
        at = window.find(mark)
        if at != -1 and (best == -1 or at < best):
            best = at + len(mark)
    if best == -1:
        return ""
    return stripped[start + best:hi].strip()


def units_in(path: Path) -> List[Unit]:
    """Every citation unit in one module."""
    rel = path.relative_to(PKG_ROOT).as_posix()
    out: List[Unit] = []
    for lineno, value in string_constants(path):
        out.extend(parse_units(value, rel, lineno))
    return out


@lru_cache(maxsize=1)
def all_units() -> Tuple[Unit, ...]:
    """Every citation unit in hand-written shipped source."""
    out: List[Unit] = []
    for path in shipped_modules():
        out.extend(units_in(path))
    return tuple(out)


# ── locator coverage: the dotted-prefix rule ──────────────────────────


def covers(cited: str, actual: str) -> bool:
    """Does a cited locator COVER an actual manifest section? Dotted prefix.

    ``§3`` covers §3, §3.1 … §3.4; ``§4.2`` covers §4.2 and deeper but NOT §4.
    The dot boundary is required so §1 never covers §10 — Rosengren really has
    a §2.10 and a §2.11 next to its §2.1.

    This rule DECIDES verdicts rather than tidying them. Baez's "exceptional
    Jordan" reads 3 hits in §3's own prose and 4 more in §3.4, so
    ``cayley_plane.py``'s ``§3 (the exceptional Jordan algebra)`` is VERIFIED
    at 7 under prefix matching and REFUTED-at-3 under equality — same citation,
    opposite verdict.

    It is an identical copy of ``tools/build_citation_manifest.py``'s
    :func:`covers` by intent: the manifest writes labels with one rule and the
    gate reads them with the same one. The gate's own test pins that they agree.
    """
    if cited == actual:
        return True
    if not cited.startswith("§") or not actual.startswith("§"):
        return False
    return actual.startswith(cited + ".")


# ── inline controls: these RAISE, they do not report ──────────────────


def _self_check() -> None:
    """Parser controls, run at import. A failure here ABORTS the import.

    Every one of these is a real string from the tree or a real failure the
    rc428 build committed. They live HERE rather than in the gate because a
    control that lives in a test file only runs when that test runs, and the
    four false nulls this rc measured were each produced by an instrument used
    outside its own test.
    """
    # C1 — the string that defeated the single-regex parser. Locator AND claim
    #      must both survive.
    u = parse_units("arXiv:math/0105155, §2 — the Cayley–"
                    "Dickson doubling convention.")
    assert len(u) == 1, u
    assert u[0].source_id == "math/0105155", u[0].source_id
    assert u[0].locator == "§2", u[0].locator
    assert "Cayley" in u[0].claim, u[0].claim

    # C2 — axis A1. A source LIST must not read a later source's title as an
    #      earlier source's claim. This is `cd_register.py` verbatim.
    u = parse_units("Hurwitz (1898); Baez arXiv:math/0105155; Kanerva (2009) "
                    "*Hyperdimensional Computing*.")
    assert len(u) == 1, u
    assert not contains_term(u[0].claim, "Kanerva"), u[0].claim

    # C3 — axis A2. Locator, no attribution mark, therefore no claim.
    u = parse_units("Baez (2002), arXiv:math/0105155, §4.2.")
    assert len(u) == 1 and not u[0].has_claim, u

    # C4 — axis A3. Two locators, two claims, bound separately. This is the
    #      shape that makes the rc428 finding visible at all.
    u = parse_units("arXiv:math/0105155, §3 (the exceptional Jordan "
                    "algebra) + §4.2 (the Cayley plane).")
    assert len(u) == 2, u
    by = {x.locator: x.claim for x in u}
    assert "Jordan" in by["§3"], by
    assert "Jordan" not in by["§4.2"], by

    # C5 — range expansion, both shapes the tree writes.
    u = parse_units("arXiv:math/0105155, §1–§2 — x")
    assert {x.locator for x in u} == {"§1", "§2"}, u
    u = parse_units("arXiv:math/0105155, §4.1–§4.2 — x")
    assert {x.locator for x in u} == {"§4.1", "§4.2"}, u

    # C6 — the versioned spelling keys on the BARE id.
    u = parse_units("arXiv:1608.06161v3 [math.CA], §1.3 — theta")
    assert u[0].source_id == "1608.06161" and u[0].version == "v3", u

    # C7 — NEGATIVE control. The parser must be able to return nothing, or
    #      "no units" carries no information at all.
    assert parse_units("no citation here, just prose about octonions.") == []

    # C8 — dash / whitespace folding, both directions, plus a true negative.
    assert contains_term("the Cayley–Dickson ladder", "Cayley-Dickson")
    assert contains_term("Cayley-\n    Dickson", "Cayley-Dickson")
    assert not contains_term("the octonion ladder", "Cayley-Dickson")

    # C9 — the prefix rule, both directions.
    assert covers("§3", "§3.4") and covers("§3", "§3")
    assert not covers("§4.2", "§4")
    assert not covers("§1", "§10")

    # C10 — axis A6, BOTH SIDES. The two shipped absence-assertions are
    #       recognised; a plain false claim is NOT laundered by the axis.
    assert asserts_absence(
        "cited here through rc426 for 'the Mal'cev tangent algebra' — "
        "contains NO occurrence of Mal'cev in any spelling", "Mal'cev")
    assert asserts_absence(
        "because that section states no Moufang identity and the adjacent "
        "Moufang ops were citing it as though it did", "Moufang")
    # the four genuine rc428 findings, verbatim — none may be silenced
    assert not asserts_absence(
        "the Cayley plane 𝕆P², the octonionic Hopf fibration", "Hopf")
    assert not asserts_absence(
        "φ, its Fano-plane values and G₂ = Aut(𝕆)", "Fano")
    # C11 — the word-boundary guard. An unanchored `no` lives inside all of
    #       these, and every one occurs in this tree's citation prose.
    for decoy in ("the norm form and the Moufang identities",
                  "normalise the Moufang residue",
                  "a nonzero Moufang defect",
                  "the notation for the Moufang loop"):
        assert not asserts_absence(decoy, "Moufang"), decoy
    # C12 — a sentence terminator ends the governing clause.
    assert not asserts_absence(
        "there is no associator. The Moufang identities hold", "Moufang")

    # ── axis A8 (rc429, `#T1128`) ────────────────────────────────────
    # C13 — THE LIVE PHANTOM, verbatim from apokatastasis/riemann_theta.py.
    #       "…the dual of an operator-side honest…" densifies to
    #       "…thedual[ofano]perator…" and matched the watchlist term "Fano"
    #       before A8. Silent today only because 1009.0369 is unattested; the
    #       moment S4 drains by attesting it, S1 fires on correct prose.
    assert not contains_term("the dual of an operator-side honest", "Fano")

    # C14 — "Bott" measured at 33 dense hits tree-wide and 0 real ones: every
    #       occurrence is "Bottom".
    assert not contains_term("Bottom of the ladder", "Bott")
    assert not contains_term("the bottleneck", "Bott")

    # C15 — the INFLECTION arm, on a real corpus string. Without it A8 is a
    #       measured FALSE NEGATIVE: a legitimate plural claim stops matching.
    assert contains_term("factorization of elliptic functions",
                         "elliptic function")
    assert contains_term("the Moufang identities' scope", "Moufang identities")

    # C16 — A8 must not weaken C8. Dash / whitespace folding still holds.
    assert contains_term("the Cayley–Dickson ladder", "Cayley-Dickson")
    assert contains_term("Cayley-\n    Dickson", "Cayley-Dickson")

    # C17 — A6 and A8 must agree on what an OCCURRENCE is. A phantom must not
    #       be readable as a negated claim either, or the disagreement
    #       re-opens C10's hole from the other side.
    assert not asserts_absence("no operator of an operand", "Fano")
    assert asserts_absence("contains no Moufang identity", "Moufang")

    # C18 — NEGATIVE CONTROL on the predicate itself. _bounded_occurrence must
    #       be able to return BOTH False and True, or it is not a measurement.
    assert _bounded_occurrence("a Fano plane", 2, 6)
    assert not _bounded_occurrence("ofanoperator", 1, 5)

    # C18b — A8 is PER-OCCURRENCE, not a whole-claim veto. A claim carrying a
    #        phantom AND a genuine occurrence of the same term must still be
    #        evaluated on the genuine one. This is where A8 and A6 deliberately
    #        run at OPPOSITE scopes; see _bounded_occurrence.
    mixed = "the dual of an operator; the Fano plane at §2.1"
    assert contains_term(mixed, "Fano"), mixed
    assert len(occurrences(mixed, "Fano")) == 1, occurrences(mixed, "Fano")

    # ── axis A9 (rc429 repair) ───────────────────────────────────────
    # C20 — THE LIVE FALSE POSITIVE, verbatim from covering.py's rc428 state.
    #       This was arm S6's ONLY occurrence in that field, and a strict-zero
    #       arm fired on it and demanded an edit to prose carrying no claim.
    sibling = ("SIBLINGS -- ``srmech.biology.genome.cwf_consistency_mod2`` "
               "checks the same relation mod 2")
    assert not contains_term(sibling, "CWF"), sibling
    assert not contains_term("the moufang_residue helper", "Moufang")
    assert not contains_term("whole-loop verdict: is_moufang", "Moufang")

    # C21 — A9 must be able to return BOTH ways, or it is an exemption rather
    #       than an axis. The SAME term in ordinary prose still matches, and
    #       every roster op keeps a real prose occurrence somewhere.
    assert contains_term("the CWF relation Lk = Tw + Wr", "CWF")
    assert contains_term("all three Moufang identities", "Moufang")
    assert _identifier_adjacent("genome.cwf_consistency_mod2", 7, 10)
    assert not _identifier_adjacent("the CWF relation", 4, 7)
    # A trailing full stop is a SENTENCE, not an identifier join.
    assert contains_term("...hold on every Moufang.", "Moufang")

    # ── axis A6, sentence scope (rc429 repair) ───────────────────────
    # C22 — whole-claim OR laundered a false citation through a TRUE sentence
    #       about the mathematics. Both halves, on one text.
    launder = ("the Moufang identities. There is no Moufang loop structure "
               "on the sedenions.")
    assert contains_term(launder, "Moufang"), launder
    assert not asserts_absence(launder, "Moufang"), launder
    # …while the one-sentence correction record still reads as one.
    assert asserts_absence(
        "cited here through rc426 for 'the Mal'cev tangent algebra' — "
        "contains NO occurrence of Mal'cev in any spelling", "Mal'cev")

    # C23 — "zero" is a QUANTITY in this tree, not a negation. Removing it
    #       moved 0 live verdicts and closed a false positive that ordinary
    #       docstring prose writes by accident.
    assert not asserts_absence(
        "the ring has zero divisors, and the Moufang identities are "
        "established", "Moufang")
    assert "zero" not in NEGATION_TOKENS
    # …and the tokens that ARE forced still fire.
    assert asserts_absence("contains no Moufang identity", "Moufang")

    # C24 — A2 x A4. A mark inside a code span must not blank the claim that
    #       follows it, while the span's CONTENTS remain non-prose.
    spanned_mark = ("arXiv:math/0105155, §3 ``—`` the exceptional Jordan "
                    "algebra is discussed")
    u = parse_units(spanned_mark)
    assert u and contains_term(u[0].claim, "Jordan"), u
    u = parse_units("arXiv:math/0105155, §2 — see ``Moufang`` below")
    assert u and not contains_term(u[0].claim, "Moufang"), u

    # C25 — term_pattern's dash quantifier, BOTH halves. The separator-free
    #       form must match (densify deletes the space in "Cayley Dickson")…
    assert contains_term("the Cayley Dickson ladder", "Cayley-Dickson")
    assert contains_term("the CayleyDickson ladder", "Cayley-Dickson")
    # …and the quantifier must not make the term match a different word.
    assert not contains_term("the Cayley plane", "Cayley-Dickson")
    assert not contains_term("Dickson's theorem", "Cayley-Dickson")


_self_check()


def _validate() -> int:                                # pragma: no cover
    """``python3 tests/citation_corpus.py --validate`` — run every control.

    Prints ONE LINE PER CONTROL with PASS/FAIL and exits **non-zero** on any
    failure. It must never print a summary and return 0: rc428's ``main()``
    did exactly that — it printed ``DEAD SEAM`` and returned success — and a
    reporting entry point is how a dead control stays alive for a whole rc.
    """
    checks = [
        ("C13 A8 live phantom (riemann_theta 'ofano')",
         lambda: not contains_term("the dual of an operator-side honest",
                                   "Fano")),
        ("C14 A8 Bott/Bottom (33 dense, 0 real)",
         lambda: not contains_term("Bottom of the ladder", "Bott")),
        ("C15 A8 inflection arm (elliptic function/s)",
         lambda: contains_term("factorization of elliptic functions",
                               "elliptic function")),
        ("C16 A8 does not weaken C8 (dash fold)",
         lambda: contains_term("the Cayley–Dickson ladder", "Cayley-Dickson")),
        ("C17 A6 and A8 agree on an occurrence",
         lambda: not asserts_absence("no operator of an operand", "Fano")),
        ("C18 negative control: predicate returns both ways",
         lambda: _bounded_occurrence("a Fano plane", 2, 6)
         and not _bounded_occurrence("ofanoperator", 1, 5)),
        ("C18b A8 is per-occurrence, not a whole-claim veto",
         lambda: len(occurrences(
             "the dual of an operator; the Fano plane", "Fano")) == 1),
        ("C20 A9 live false positive (covering.py SIBLINGS xref)",
         lambda: not contains_term(
             "SIBLINGS -- ``srmech.biology.genome.cwf_consistency_mod2`` "
             "checks the same relation mod 2", "CWF")),
        ("C21 A9 negative control: prose still matches",
         lambda: contains_term("the CWF relation Lk = Tw + Wr", "CWF")
         and contains_term("...hold on every Moufang.", "Moufang")
         and not _identifier_adjacent("the CWF relation", 4, 7)),
        ("C22 A6 sentence scope: cross-sentence launder fires",
         lambda: not asserts_absence(
             "the Moufang identities. There is no Moufang loop structure on "
             "the sedenions.", "Moufang")
         and asserts_absence("cited here through rc426 for 'the Mal'cev "
                             "tangent algebra' — contains NO occurrence of "
                             "Mal'cev in any spelling", "Mal'cev")),
        ("C23 'zero' is a quantity, not a negation",
         lambda: "zero" not in NEGATION_TOKENS and not asserts_absence(
             "the ring has zero divisors, and the Moufang identities are "
             "established", "Moufang")
         and asserts_absence("contains no Moufang identity", "Moufang")),
        ("C24 A2xA4: a code-span mark does not blank the claim",
         lambda: contains_term(parse_units(
             "arXiv:math/0105155, §3 ``—`` the exceptional Jordan algebra "
             "is discussed")[0].claim, "Jordan")
         and not contains_term(parse_units(
             "arXiv:math/0105155, §2 — see ``Moufang`` below")[0].claim,
             "Moufang")),
        ("C25 term_pattern dash quantifier, both halves",
         lambda: contains_term("the Cayley Dickson ladder", "Cayley-Dickson")
         and not contains_term("Dickson's theorem", "Cayley-Dickson")),
        ("corpus resolves and is non-empty",
         lambda: len(shipped_modules()) >= 200),
        ("units parse and are non-empty",
         lambda: len(all_units()) >= 100),
    ]
    bad = 0
    for label, fn in checks:
        try:
            ok = bool(fn())
        except Exception as exc:                       # noqa: BLE001
            ok, label = False, "%s  [%s: %s]" % (label, type(exc).__name__, exc)
        print("%-4s %s" % ("PASS" if ok else "FAIL", label))
        if not ok:
            bad += 1
    print("%d control(s) FAILED" % bad if bad else "all controls PASS")
    return 1 if bad else 0


if __name__ == "__main__":                             # pragma: no cover
    import sys as _sys

    if "--validate" not in _sys.argv[1:]:
        print("usage: python3 tests/citation_corpus.py --validate")
        raise SystemExit(2)
    raise SystemExit(_validate())
