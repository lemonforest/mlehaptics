"""rc459 — A ``docs/``-ROOTED PATH IN A NOTEBOOK MUST RESOLVE, OR SAY WHERE IT LIVES.

WHY THIS EXISTS — artefacts cited as in-repo that are on a branch
=================================================================
Both research notebooks cite files by path in backticked code spans, and a
reader — human or agent — treats such a span as a working-tree path.

MEASURED at ``125f23f48`` by running ``_unresolved`` below over both
notebooks — **four** spans did not resolve, three of them in the SRMECH
notebook and one in MFO:

* ``srmech_research_notebook.md:8017`` — ``R-RBS-LM-ATTEST_furey_1611_09182.md``
* ``srmech_research_notebook.md:8030`` — ``R-RBS-LM-TENSORVSCD_ladder_vs_tensor_product.py``
* ``mfo_spectral_research_notebook.md:6392`` — ``R-RBS-LM-TRIALITY_F296_F304_verdict.md``
* ``srmech_research_notebook.md:844`` — a renumbered ADR, below.

The three RBS-LM artefacts exist only on ``origin/research/rbs-lm-rolling-2``,
the branch carried by the open PR gh #687, which stays open by maintainer
ruling. Nothing in the prose said so, so each read as a file you could open.

The fourth was a different failure with the same symptom: the srmech notebook
cited ``docs/srmech/adr/0002-phase-1-operator-chain-schema.md``, which was
RENUMBERED to ``0008-…`` on 2026-07-17 (the ADR records the move in its own
header). The citation was correct when written and the file moved out from
under it.

⚠️ THIS DOCSTRING FIRST SAID "five ... four RBS-LM artefacts", and located
three of them in "the MFO notebook's tensor-vs-CD backlinks". Both halves were
wrong and the second was inverted: the MFO backlinks line cites those
filenames **bare**, which the ``docs/``-prefix requirement below puts out of
scope, and ``R-RBS-LM-FUREYALG_…py`` is never cited ``docs/``-rooted anywhere
in the tree (``git grep`` at the base commit: zero). Corrected at rc459 review.
A census written from memory rather than from the predicate is the same defect
class this gate exists to catch, one level up — so the numbers above name the
exact file and line they came from.

WHAT IS DECIDABLE HERE, AND WHAT IS NOT
=======================================
Decidable: *does this path exist on disk*. That is what this gate asserts, at
**strict zero** — not a ceiling, because there is no legitimate residual of
paths that neither resolve nor say where they live.

NOT decidable BY THIS GATE, and deliberately out of scope: whether a path that
resolves is the RIGHT path for the sentence around it. **Existence proves
nothing; topicality decides**, and topicality is not mechanisable.

⚠️ But "not mechanisable" is not "unknowable", and rc459 conflated the two.
This docstring first declared ``ADR-0002 §3 (parent)`` — on the same srmech
notebook line B5 fixed — undecidable between the renumbered schema ADR and
``0002-catalog-as-computation``. It is answered outright by the header of the
very file that edit read: ``docs/srmech/adr/0008-…:14-15`` states **"Status of
parent ADR: ADR-0002 (catalog-as-computation)"** and **"Relates to: ADR-0002 §3
(the sketch this document formalises)"**. So the citation means
``0002-catalog-as-computation`` and is correct as written. Reported as an open
question at rc459 and closed at rc459 review; the gate's scope is unchanged,
only the claim about what was knowable.

Also out of scope by construction: **bare filenames with no directory**.
Measured at THIS commit with ``grep -o '`R-RBS-LM-[A-Za-z0-9_.]*`'`` over both
notebooks: **19 spans, 14 distinct filenames** (srmech 5 spans / 3 distinct;
MFO 14 spans / 13 distinct). This said "20 ... 3 in srmech, 17 in MFO" with no
predicate given, and an unstated predicate is why a count cannot be re-derived
— which is the whole reason the command is written out here. The
``docs/``-prefix requirement cannot see any of them; resolving them needs a
repo-wide filename index and a per-file pass, which is a sweep and not a
correction.

⚠️ This count MOVES with ordinary prose edits and nothing gates it — rc459
review's own srmech-notebook fix added one span. Treat it as a dated
measurement, not a constant, and re-run the command rather than quoting it.

THE EXEMPTION IS A QUALIFIER IN THE PROSE, NOT A PATH IN A LIST
==============================================================
A line whose text already tells the reader where the file lives —
``origin/research/…``, ``NOT ON `main` ``, "never tracked in git", "renumbered"
— has done the job this gate exists to enforce, so it is exempt. That keeps the
exemption mechanism *in the surface being checked*, where a reader sees it,
rather than in a side list that rots. Three pre-existing sites already qualify
themselves this way (the Killing-Yano review and two never-committed sources);
they were exempt before this rc and stay exempt for their own stated reason.

⚠️ REACHABILITY IS ASSERTED FIRST, AND THAT IS NOT CEREMONY
===========================================================
Per ``[[feedback_citation_gates_return_zero_inside_a_session_worktree]]``: a
path-scoped gate whose corpus resolves to nothing passes a strict-zero
assertion for entirely the wrong reason. Six gates once read as real ripple
while scanning 0 of 264 modules. Both notebooks are asserted reachable, and a
floor is put under the number of spans actually examined, before any verdict.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[3]

_NOTEBOOKS = {
    "srmech": _REPO_ROOT / "docs" / "srmech" / "srmech_research_notebook.md",
    "mfo": (
        _REPO_ROOT
        / "docs"
        / "antikythera-maths"
        / "mfo_spectral_research_notebook.md"
    ),
}

#: A backticked code span. Non-greedy, single-line — a span never wraps.
_SPAN = re.compile(r"`([^`\n]+)`")

#: Glob / placeholder metacharacters. A span carrying one is a PATTERN, not a
#: path, and asking it to resolve is a category error.
_META = set("*{}?<>|")

#: A trailing line anchor: ``:404`` or ``:237-253``. This tree cites source by
#: line constantly and that is a GOOD habit, so the anchor is stripped and the
#: FILE is resolved. Measured: the unstripped first draft flagged four such
#: citations across the two notebooks whose files all exist
#: (``spike88_m_top_2_56_anchor.py:237-253``, ``CHANGELOG.md:5466``,
#: ``gear_database.py:404``, ``antikythera_spectral_research_notebook.md:112``).
#: ⚠️ Whether the LINE NUMBER still points at the claimed thing is NOT checked
#: here and must not be read as checked — line numbers drift with every edit,
#: and a gate on them would be red permanently and switched off within a day.
_LINE_ANCHOR = re.compile(r":\d+(?:-\d+)?$")

#: Prose that tells the reader the file is not in the working tree. Matched
#: against the whole LINE, case-insensitively.
#:
#: ⚠️ ``renumbered`` sat in this tuple as a BARE ENGLISH WORD through rc459,
#: which made it the weakest entry by a distance: any line using it in an
#: unrelated sense exempted every span on that line. It moved to
#: ``_QUALIFIER_PATTERNS`` below and now requires an attached ISO date — the
#: form the one real site uses ("renumbered 2026-07-17 from ...") — so it has
#: to point at a specific move rather than merely sound like one.
_QUALIFIERS = (
    "origin/research/",
    "branch `research/",
    "not on `main`",
    "never committed",
    "never tracked in git",
)

#: Qualifiers that need internal structure to count. See the note above.
_QUALIFIER_PATTERNS = (re.compile(r"renumbered\s+\d{4}-\d{2}-\d{2}"),)


def _spans(line: str) -> list[str]:
    """Backticked spans on ``line`` that claim to be ``docs/``-rooted paths."""
    out = []
    for span in _SPAN.findall(line):
        tok = span.strip()
        if not tok.startswith("docs/"):
            continue
        if _META & set(tok):
            continue
        out.append(_LINE_ANCHOR.sub("", tok))
    return out


def _is_qualified(line: str) -> bool:
    """⚠️ LINE-scoped, not SPAN-scoped, and that is a deliberate trade.

    These notebooks put whole paragraphs on one physical line, and the real
    qualifying sentences deliberately cover every filename around them ("read
    every filename in this line as ``origin/research/…``"). Span-scoping would
    go red on prose that is already doing the right thing.

    The cost is a real hole, and
    ``test_the_exemption_is_line_scoped_which_is_a_known_hole`` EXECUTES it
    rather than leaving it as a comment: a line carrying one QUALIFIED
    branch-only path and one GENUINELY DEAD path is exempt for both. Not
    present in the tree today; not hypothetical either. If it ever bites, the
    fix is to scope to the qualifying sentence, not to drop the exemption.
    """
    low = line.lower()
    if any(q in low for q in _QUALIFIERS):
        return True
    return any(rx.search(low) for rx in _QUALIFIER_PATTERNS)


def _unresolved(path: Path) -> tuple[list[str], int]:
    """``(offending "lineno: span" strings, total spans examined)``."""
    bad: list[str] = []
    seen = 0
    text = path.read_text(encoding="utf-8", errors="replace")
    for lineno, line in enumerate(text.splitlines(), start=1):
        spans = _spans(line)
        seen += len(spans)
        if not spans or _is_qualified(line):
            continue
        for tok in spans:
            if not (_REPO_ROOT / tok).exists():
                bad.append(f"{path.name}:{lineno}: `{tok}`")
    return bad, seen


@pytest.mark.parametrize("name", sorted(_NOTEBOOKS))
def test_the_notebook_is_reachable_at_all(name: str) -> None:
    """A gate that scans nothing passes for the wrong reason. Prove otherwise."""
    nb = _NOTEBOOKS[name]
    assert nb.is_file(), (
        f"{name} notebook not found at {nb} — this gate would then return a "
        "FALSE green rather than a pass"
    )
    _, seen = _unresolved(nb)
    assert seen >= 5, (
        f"{name} notebook yielded only {seen} docs/-rooted spans; the scanner "
        "has probably stopped matching rather than the notebook having stopped "
        "citing"
    )


@pytest.mark.parametrize("name", sorted(_NOTEBOOKS))
def test_every_cited_docs_path_resolves_or_is_branch_qualified(name: str) -> None:
    """STRICT ZERO, per notebook."""
    bad, _ = _unresolved(_NOTEBOOKS[name])
    assert not bad, (
        f"{len(bad)} cited `docs/`-rooted path(s) in the {name} notebook "
        "neither resolve on disk nor carry a branch/commit qualifier. Either "
        "fix the path or say where the file actually lives — a reader treats a "
        "backticked path as a file they can open:\n  " + "\n  ".join(bad)
    )


def test_the_predicate_would_fire_on_a_dead_path() -> None:
    """MUTATION WITNESS on the resolver half.

    Uses the exact string B5 removed, so the witness stays tied to a defect
    that really shipped rather than to an invented one.
    """
    dead = "docs/srmech/adr/0002-phase-1-operator-chain-schema.md"
    assert not (_REPO_ROOT / dead).exists(), (
        "the renumbered-away ADR filename now exists again; this witness is "
        "measuring nothing and needs a new subject"
    )
    line = f"Phase 1 schema doc (`{dead}`), Phase 1 report."
    assert _spans(line) == [dead]
    assert not _is_qualified(line)


def test_the_predicate_would_fire_on_a_branch_only_path() -> None:
    """MUTATION WITNESS on the branch-only half, and on the exemption.

    The unqualified form must be caught AND the qualified form must be let
    through — an exemption that never exempts is as broken as one that always
    does.
    """
    branch_only = (
        "docs/srmech/rbs_lm_research/R-RBS-LM-ATTEST_furey_1611_09182.md"
    )
    assert not (_REPO_ROOT / branch_only).exists(), (
        "this file is now on main; pick another branch-only subject or drop "
        "this witness — it must stay tied to a real absence"
    )
    naked = f"Attestation: `{branch_only}`."
    assert _spans(naked) == [branch_only]
    assert not _is_qualified(naked), "the unqualified form must NOT be exempt"

    qualified = (
        f"Attestation: `origin/research/rbs-lm-rolling-2:{branch_only}` — "
        "**NOT ON `main`**."
    )
    assert _is_qualified(qualified), "the qualified form MUST be exempt"


@pytest.mark.parametrize(
    "cited,base",
    [
        (
            "docs/srmech/notes/spike88_m_top_2_56_anchor.py:237-253",
            "docs/srmech/notes/spike88_m_top_2_56_anchor.py",
        ),
        (
            "docs/antikythera-maths/research/gear_database.py:404",
            "docs/antikythera-maths/research/gear_database.py",
        ),
    ],
)
def test_a_line_anchor_is_stripped_and_the_file_is_what_resolves(
    cited: str, base: str
) -> None:
    """Both samples are REAL citations in these notebooks, not invented ones.

    If the anchor stripping regresses, these are the four sites that go red.
    """
    assert _spans(f"see `{cited}`") == [base]
    assert (_REPO_ROOT / base).exists(), f"{base} should resolve"


def test_the_renumbered_qualifier_needs_a_date_attached() -> None:
    """The weakest exemption, tightened — and both directions proved.

    ``renumbered`` alone must NOT exempt (it is ordinary English and would
    hand any line using it a free pass); ``renumbered <ISO date>`` must, since
    that is the form the one real site writes.
    """
    dead = "docs/srmech/adr/0002-phase-1-operator-chain-schema.md"
    loose = f"The clause list was renumbered last week; see `{dead}`."
    assert _spans(loose) == [dead]
    assert not _is_qualified(loose), (
        "a bare 'renumbered' must not exempt — that was the rc459 behaviour"
    )

    real = (
        f"Phase 1 schema doc (`docs/srmech/adr/0008-phase-1-operator-chain-"
        f"schema.md`, renumbered 2026-07-17 from `{dead}`)."
    )
    assert _is_qualified(real), "the real qualifying form MUST still exempt"


def test_the_exemption_is_line_scoped_which_is_a_known_hole() -> None:
    """EXECUTES the documented limitation instead of only asserting it.

    A comment saying "this is line-scoped" is prose. This is the measurement:
    one qualified path and one dead path on the same line, and the dead one
    goes unreported. If someone later makes the exemption span-scoped, this
    test fails and points at the docstring that must change with it — which
    is the outcome we want, not a silent behaviour swap.
    """
    branch_only = (
        "docs/srmech/rbs_lm_research/R-RBS-LM-ATTEST_furey_1611_09182.md"
    )
    dead = "docs/srmech/adr/0002-phase-1-operator-chain-schema.md"
    for tok in (branch_only, dead):
        assert not (_REPO_ROOT / tok).exists(), f"{tok} now resolves"

    mixed = (
        f"See `origin/research/rbs-lm-rolling-2` for `{branch_only}`, and "
        f"the schema at `{dead}`."
    )
    assert set(_spans(mixed)) == {branch_only, dead}
    assert _is_qualified(mixed), "the origin/research/ token qualifies the line"
    # …and therefore the genuinely dead second path is NOT reported. This
    # assertion documents the hole; it is not an endorsement of it.
    assert _is_qualified(mixed) and not (_REPO_ROOT / dead).exists()


def test_a_resolving_path_is_not_flagged() -> None:
    """NEGATIVE CONTROL: the common case must stay silent."""
    live = "docs/srmech/adr/0008-phase-1-operator-chain-schema.md"
    assert (_REPO_ROOT / live).exists(), f"{live} should exist"
    assert _spans(f"see (`{live}`) for the schema") == [live]


@pytest.mark.parametrize(
    "span",
    [
        "docs/srmech/notes/*.ndjson",
        "docs/srmech/rbs_lm_research/R-RBS-LM-FINDING_{257,306}.md",
        "origin/research/rbs-lm-rolling-2:docs/srmech/rbs_lm_research/x.md",
        "srmech.math.laplacian.dense_laplacian",
    ],
)
def test_non_path_spans_are_not_asked_to_resolve(span: str) -> None:
    """Globs, placeholders, branch-prefixed refs and dotted module paths are
    not working-tree paths and must not be treated as such."""
    assert _spans(f"see `{span}` here") == []
