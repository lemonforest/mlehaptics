"""rc459 — NO SM-REPRODUCTION CLAIM ON ANY SHIPPED SURFACE.

WHY THIS EXISTS — one comment carried the whole claim, and nothing read it
=========================================================================
Through rc458, ``c/src/srmech_laplacian.c`` opened by describing Class L as
"the spectral substrate underpinning cascade-composition mass-spectrum
reproduction (bonus 10 SUCCESS at log-L2 = 0.614 dex)".

Measured at rc459, before the fix: that was the **only** SM-reproduction claim
on any shipped surface in the tree. The Python package grepped clean for every
phrase in ``_BANNED`` below — zero hits — so the entire live claim was those
two lines of C. The research record now types 0.614 as the instrument's
GRANULARITY FLOOR, i.e. chance, and the SUCCESS framing fails an acceptance
predicate four independent ways.

WHY IT IS A GATE RATHER THAN A ONE-TIME EDIT
============================================
A comment is the easiest surface in the tree to regress on: it compiles
regardless, no test reads it, and ``test_c_cascade_coherence`` /
``test_jpl_audit`` both STRIP comments before their scans, by design. So the
claim's own removal was the only thing standing between the tree and its
return, and that is exactly the shape
``[[feedback_ungated_surfaces_trickle_gated_surfaces_race_to_100]]`` names.

WHAT IT DOES **NOT** ASSERT
===========================
This gate takes no position on whether 0.614 dex is a good or bad number, and
it must not be read as one. It asserts that a *shipped* surface — C source, C
headers, wheel Python — does not carry a spectrum-reproduction claim. Where
such a claim belongs, if anywhere, is a research notebook that can carry its
own provenance. The fix for an overclaiming comment is not a better-calibrated
claim in the same place; it is the claim's absence from a place that cannot
carry evidence.

THE PREDICATE NORMALISES, BECAUSE THE ORIGINAL WRAPPED
======================================================
In the rc458 source the phrase "mass-spectrum reproduction" straddled a line
break and the block-comment continuation marker, so a naive substring scan
would have missed it while matching only the two shorter needles. ``_normalise``
therefore strips per-line comment furniture and collapses whitespace runs
before matching. This was found by writing the mutation witness first: the
witness failed against the naive predicate, which is the witness doing its job.

SCOPE IS THE EXEMPTION MECHANISM — THERE IS NO EXEMPTION LIST
=============================================================
Scratch notes under ``docs/srmech/notes/`` legitimately carry ``0.614`` about
ten times: that is a research record doing its job. They are excluded because
they are not a shipped surface, which the PATH SCOPE expresses. An exemption
list would have to be maintained and would rot; a scope statement cannot.

THE MUTATION WITNESS IS NOT OPTIONAL
====================================
``test_the_gate_would_have_fired_on_the_rc458_comment`` feeds the exact
pre-rc459 text through the same predicate and requires it to trip. Without it
this file is an instrument that cannot return otherwise
(``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``)
— a strict-zero assertion over a corpus is indistinguishable from a typo in a
glob until something proves the needle would be seen.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[3]
_PKG_ROOT = _HERE.parent / "srmech"
_C_ROOT = _HERE.parents[1] / "c"

# Each entry is (regex source, a sample that MUST match, a sample that MUST
# NOT). Matched against normalised, lowercased text, so sources are lowercase
# and single-spaced.
#
# ⚠️ THE NEEDLES ARE WORD-BOUNDED, AND THE NEAR-MISS COLUMN IS WHY.
# Written first as plain substrings, this gate's first run failed on THREE
# innocent shipped files: ``_tool_docs.py``, ``_tool_docs_curated.py`` and
# ``srmech_tool_registry.c`` all carry a ``bigint_mul`` claim reading "the same
# call that reproduces the **sm**all Antikythera multiples 669 and 940" — of
# which ``reproduces the sm`` is a prefix. A gate that cries wolf on the
# Antikythera multiples gets deleted, so every needle now ends on ``\b`` and
# every near-miss that actually occurred in the tree is pinned below as a
# negative control (``[[feedback_negative_controls_for_carrier_claims_...]]``).
# ``undiscovered particles?`` takes the optional plural deliberately: the
# boundary must reject a DIFFERENT word, not a different number of them.
_BANNED: tuple[tuple[str, str, str], ...] = (
    (r"bonus 10\b", "bonus 10 SUCCESS", "bonus 100 substrates"),
    (r"0\.614\b", "log-L2 = 0.614 dex", "tolerance 0.6142"),
    (
        r"mass[- ]spectrum reproduction",
        "cascade-composition mass-spectrum reproduction",
        "mass spectrum of the operator",
    ),
    (
        r"reproduces the sm\b",
        "the cascade reproduces the SM",
        "reproduces the small Antikythera multiples 669 and 940",
    ),
    (
        r"undiscovered particles?\b",
        "predicts an undiscovered particle",
        "undiscovered particulars",
    ),
)

_PATTERNS = tuple((src, re.compile(src)) for src, _, _ in _BANNED)

# The rc458 text, byte-for-byte as it stood in srmech_laplacian.c lines 7-9.
# Note the line break INSIDE "mass-spectrum reproduction" — that is the reason
# the predicate normalises rather than matching raw.
_RC458_COMMENT = (
    " * substrates per the cumulative cross-substrate audit) and the\n"
    " * spectral substrate underpinning cascade-composition mass-spectrum\n"
    " * reproduction (bonus 10 SUCCESS at log-L2 = 0.614 dex).\n"
)

# Leading comment furniture on a continuation line: C ``*``, Python ``#``, or
# reST/markdown quote markers, after any indent.
_LINE_FURNITURE = re.compile(r"(?m)^[ \t]*(?:\*|#|//|>)[ \t]?")
_WS_RUN = re.compile(r"\s+")


def _normalise(text: str) -> str:
    """Lowercase, drop per-line comment markers, collapse whitespace runs.

    A claim that wraps across a source line is the same claim.
    """
    return _WS_RUN.sub(" ", _LINE_FURNITURE.sub(" ", text)).lower()


def _hits(text: str) -> list[str]:
    """Return every banned pattern present in ``text``. The predicate."""
    flat = _normalise(text)
    return [src for src, rx in _PATTERNS if rx.search(flat)]


def _shipped_files() -> list[Path]:
    """Every file that travels to a user: wheel Python + the C library."""
    files = sorted(_PKG_ROOT.rglob("*.py"))
    files += sorted(_C_ROOT.glob("src/*.c"))
    files += sorted(_C_ROOT.glob("include/*.h"))
    return files


def test_the_shipped_surfaces_are_reachable_at_all() -> None:
    """A path-scoped gate that finds no files returns a FALSE green.

    Per ``[[feedback_citation_gates_return_zero_inside_a_session_worktree]]``,
    a scope that silently resolves to nothing passes a strict-zero assertion
    for the wrong reason. Prove the corpus exists before asserting over it.
    """
    assert _PKG_ROOT.is_dir(), f"package root not found at {_PKG_ROOT}"
    assert _C_ROOT.is_dir(), f"C root not found at {_C_ROOT}"

    files = _shipped_files()
    py = [f for f in files if f.suffix == ".py"]
    c_src = [f for f in files if f.suffix == ".c"]
    c_hdr = [f for f in files if f.suffix == ".h"]

    assert len(py) > 100, f"expected the whole package, scanned {len(py)} .py"
    assert len(c_src) > 10, f"expected the C sources, scanned {len(c_src)} .c"
    assert c_hdr, "expected at least srmech.h"

    names = {f.name for f in c_src}
    assert "srmech_laplacian.c" in names, (
        "srmech_laplacian.c is the file this gate was written for and it is "
        f"not in scope; scanned {len(names)} .c files"
    )


def test_no_sm_reproduction_claim_on_any_shipped_surface() -> None:
    """STRICT ZERO. Not a ceiling — there is no legitimate residual."""
    offenders: list[str] = []
    for path in _shipped_files():
        found = _hits(path.read_text(encoding="utf-8", errors="replace"))
        if found:
            offenders.append(f"{path.relative_to(_REPO_ROOT)}: {found}")

    assert not offenders, (
        "SM-reproduction claim(s) on a shipped surface — this class of claim "
        "belongs in a research notebook that can carry its own provenance, "
        "not in source that ships to users:\n  " + "\n  ".join(offenders)
    )


@pytest.mark.parametrize("src,hit,_miss", _BANNED, ids=[b[0] for b in _BANNED])
def test_every_banned_pattern_is_individually_detectable(
    src: str, hit: str, _miss: str
) -> None:
    """Each needle is separately live, so a typo in one cannot hide."""
    assert _hits(f"prefix {hit} suffix") == [src]


@pytest.mark.parametrize("src,_hit,miss", _BANNED, ids=[b[0] for b in _BANNED])
def test_every_banned_pattern_rejects_its_real_near_miss(
    src: str, _hit: str, miss: str
) -> None:
    """NEGATIVE CONTROL. Each near-miss is a string that occurs, or plausibly
    occurs, in this tree and must NOT trip the gate.

    ``reproduces the small Antikythera multiples`` is not hypothetical: three
    shipped files carry it, and the unbounded first draft of this gate flagged
    all three.
    """
    assert src not in _hits(f"prefix {miss} suffix")


@pytest.mark.parametrize("src,hit,_miss", _BANNED, ids=[b[0] for b in _BANNED])
def test_every_banned_pattern_is_detectable_when_it_wraps(
    src: str, hit: str, _miss: str
) -> None:
    """The wrapped form is the form that actually shipped.

    Split each sample at its last space and rejoin it across a C continuation
    line. If normalisation ever regresses, this is what notices.
    """
    head, _, tail = hit.rpartition(" ")
    assert head, f"sample {hit!r} has no space to wrap at"
    wrapped = f" * lead-in {head}\n * {tail} trailer\n"
    assert _hits(wrapped) == [src]


def test_the_gate_would_have_fired_on_the_rc458_comment() -> None:
    """THE MUTATION WITNESS. The removed text must trip the predicate.

    If this ever passes vacuously the gate above is decorative.
    """
    found = _hits(_RC458_COMMENT)
    assert r"bonus 10\b" in found, f"'bonus 10' not detected; matched {found}"
    assert r"0\.614\b" in found, f"'0.614' not detected; matched {found}"
    assert r"mass[- ]spectrum reproduction" in found, (
        "the hyphenated phrase spans a line break in the original comment; if "
        f"it is not matched, normalisation has regressed. Matched: {found}"
    )


def test_the_laplacian_header_states_the_ops_actual_role() -> None:
    """The fix is a DELETION plus a role statement, not a rival claim.

    Guards the other failure mode: replacing "0.614 dex is a SUCCESS" with
    "0.614 dex is at the granularity floor" would clear the gate above while
    keeping a spectrum-interpretation claim in a C comment.
    """
    src = (_C_ROOT / "src" / "srmech_laplacian.c").read_text(
        encoding="utf-8", errors="replace"
    )
    header = _normalise(src[: src.index("*/")])
    assert "diagonalises it" in header or "diagonalizes it" in header, (
        "the header should say what the file DOES (construct + diagonalise)"
    )
    assert "caller" in header, (
        "the header should locate the interpretation with the caller"
    )
    for word in ("granularity floor", "log-l2", "mass spectrum"):
        assert word not in header, (
            f"{word!r} re-imports the retracted claim's subject into a C "
            "comment; the deletion is the fix, not a recalibration"
        )
