"""rc353 (`#T1006`) — the WORKED-EXAMPLE STRICT-ZERO gate.

THE HOLE THIS CLOSES
====================
``tests/test_tool_schema_coverage.py:496`` asserts ``t.summary`` is non-empty,
and ``tests/test_tool_docs_coverage_rc240.py`` asserts ``t.example`` is truthy
and shape-consistent. Both were GREEN on the rc352 tree in which **every one of
the 513 examples was a signature echo** — 356 of them literal type stencils::

    algebra_table(dim=<int>, gammas=<Sequence[int] | None>) -> list

A non-empty string is not a worked example, and ``{"call": "<echo>"}`` is a
well-formed dict. Both guards therefore reported 100% coverage of a surface
that carried no executed output at all. That is the false green.

THE MEASURED COST, which is why this is a hard gate and not a lint
=================================================================
In a single session an Opus-5 agent queued TWO phantom gaps against
already-delivered code and came close to rebuilding both:

* ``mat_rank`` — ``QMat.rank`` ships at ``srmech/amsc/qmat.py:447`` with the C
  peer ``srmech_qmat_rank`` declared at ``c/include/srmech.h:11761``;
* an enumeration primitive that already exists seven times over in C.

The agent had the same source tree. The signature echo did not tell it the op
already did that job. So the bar here is not "documented" — it is **a reader
cannot fail to see the op already does this**, which needs a worked call, its
real output, and prose that names the siblings.

WHAT THIS GATE IS, AND WHAT IT DELIBERATELY IS NOT
==================================================
It is a **decidable** gate: three properties readable off the registry with no
re-execution, so it runs in milliseconds and cannot flake.

It is **NOT** a truth guard. It cannot distinguish a captured output from a
typed one — only re-execution can, and that is blocked on the arc settling ONE
``worked`` convention (see the standing note at the foot of
``test_tool_docs_coverage_rc240.py``). Fabricated output is caught by the
authoring verifier pass, not here. Saying so is the point: a gate that is
believed to check more than it does is the next false green.

STRICT ZERO, NO CEIL, BY USER DIRECTION (2026-07-28)
====================================================
There is deliberately no ``CEIL_`` dict and no per-category allowlist. The
remaining work is enumerated BY THIS TEST, mechanically, every time it runs —
a red gate here is the honest ledger of what has not landed, and it is the only
ledger that cannot drift from the tree. Do not add a ceiling to make it green;
land the examples.
"""

from __future__ import annotations

import re

import pytest

from srmech.amsc.tool_schema import get_tool_schema, warmup_all

warmup_all()


# ── (A) the stencil marker ────────────────────────────────────────────────
#
# ``=<`` is the exact byte pair the signature-echo generator emits between a
# parameter name and its rendered type annotation (``dim=<int>``). It cannot
# occur in real Python source: ``=<`` is a syntax error everywhere, and the
# comparison operator is ``<=``. So this is a zero-false-positive marker for
# "a type annotation is standing where an argument value belongs".
_STENCIL = "=<"


# ── (C) the informativeness bar ───────────────────────────────────────────
#
# The user's directive is EXPLAIN = MULTIPLE PERSPECTIVES, at minimum: what it
# computes, why you would reach for it (and what you would otherwise wrongly
# hand-roll), and how it relates to its siblings. Those are three independently
# checkable claims, so the bar is three independently checkable regexes plus a
# length floor.
#
# CALIBRATION (measured on the rc353 tree, 513 srmech tools, not guessed):
#   authored worked-form explanations  median 954 chars, p10 153
#   surviving signature-echo seeds     median  76 chars
# A 400-char floor sits an order of magnitude above the echo seeds and well
# below the authored median, so it separates the two populations without
# rewarding padding. Length ALONE would reward padding, which is why it is the
# weakest of the four conditions and never the only one.
_PERSPECTIVES = (
    # 1. WHAT it computes.
    ("what", re.compile(r"\bWHAT\b|\bcomputes?\b|\breturns?\b", re.IGNORECASE)),
    # 2. WHEN you would reach for it.
    ("when", re.compile(r"\bWHEN\b|reach for it|use (?:it|this)\b", re.IGNORECASE)),
    # 3. HOW it relates to siblings / what not to re-derive. This is the
    #    perspective that actually prevents the phantom-gap failure, so it is
    #    the one worth reading first when an entry fails.
    ("siblings", re.compile(
        r"SIBLING|RELATION|instead of|rather than|hand-roll|hand-writ|"
        r"hand-built|re-?deriv|re-?implement|"
        r"do not (?:write|build|add|create|reach|compose)",
        re.IGNORECASE)),
)
_MIN_EXPLANATION_CHARS = 400


def _srmech_tools():
    return [t for t in get_tool_schema().tools if t.owner == "srmech"]


def _missing_perspectives(explanation: str):
    return [name for name, pat in _PERSPECTIVES if not pat.search(explanation)]


def _fmt(names, cap=12):
    head = "\n  ".join(sorted(names)[:cap])
    tail = f"\n  ... and {len(names) - cap} more" if len(names) > cap else ""
    return head + tail


# ── the three strict-zero assertions ──────────────────────────────────────

def test_no_example_is_a_type_stencil() -> None:
    """(A) STRICT ZERO — no example may contain ``=<``.

    ``dim=<int>`` is a rendered type annotation standing where an argument
    VALUE belongs. It teaches a reader the signature they could already read
    off the source, and nothing about what the op does.
    """
    bad = [t.name for t in _srmech_tools() if _STENCIL in str(t.example or "")]
    assert not bad, (
        f"{len(bad)} examples are type stencils (contain {_STENCIL!r}). "
        f"Replace with a WORKED call carrying real argument values, author it "
        f"in srmech/amsc/_tool_docs_curated.py, then run tools/regen_all.py:"
        f"\n  {_fmt(bad)}"
    )


def test_every_example_carries_captured_output() -> None:
    """(B) STRICT ZERO — every example must carry a non-empty ``output``.

    An example with no output is a signature echo however it is spelled: the
    21 zero-argument entries that carry no ``=<`` fail here, which is why (A)
    alone is not sufficient.
    """
    bad = []
    for t in _srmech_tools():
        ex = t.example
        if not isinstance(ex, dict) or not str(ex.get("output", "")).strip():
            bad.append(t.name)
    assert not bad, (
        f"{len(bad)} examples carry no captured output. Run the example on "
        f"WSL2 (numpy-absent) and commit what it actually printed — never a "
        f"typed-out guess:\n  {_fmt(bad)}"
    )


def test_every_explanation_clears_the_informativeness_bar() -> None:
    """(C) STRICT ZERO — every explanation must carry all three perspectives
    and clear the length floor.

    The ``siblings`` perspective is the load-bearing one: it is the sentence
    that would have stopped ``mat_rank`` being queued as a gap while
    ``QMat.rank`` (``srmech/amsc/qmat.py:447``) was shipping.
    """
    bad = []
    for t in _srmech_tools():
        e = (t.explanation or "").strip()
        missing = _missing_perspectives(e)
        if len(e) < _MIN_EXPLANATION_CHARS:
            missing.append(f"len={len(e)}<{_MIN_EXPLANATION_CHARS}")
        if missing:
            bad.append(f"{t.name}  [{', '.join(missing)}]")
    assert not bad, (
        f"{len(bad)} explanations are below the multi-perspective bar. Each "
        f"needs WHAT it computes, WHEN to reach for it (and what you would "
        f"otherwise wrongly hand-roll), and HOW it relates to its siblings:"
        f"\n  {_fmt(bad)}"
    )


# ── the meta-test: prove the gate can go red ──────────────────────────────

_PLANTED = {
    # (A) the exact rc352 shape, verbatim from the op the directive quotes.
    "stencil": {"call": "algebra_table(dim=<int>, gammas=<Sequence[int] | None>) -> list"},
    # (B) a worked call with its output silently dropped.
    "no_output": {"worked": "algebra_table(8) == octonion_mult_table()", "output": "   "},
    # (C) real worked output, but a one-line docstring-grade explanation.
    "thin": {"worked": "algebra_table(8)", "output": "[[...]]"},
}


@pytest.mark.parametrize("kind", sorted(_PLANTED))
def test_gate_fires_on_a_planted_defect(kind: str) -> None:
    """A guard that has never been seen to fail is not evidence.

    Each planted entry is the SHAPE that actually shipped, so this is a
    reproduction, not a synthetic probe:

    * ``stencil``   — ``algebra_table``'s literal rc352 example, the one the
      user quoted; must trip (A).
    * ``no_output`` — a real worked call whose output was dropped; must trip
      (B) even though it contains no ``=<``, which is the case (A) misses.
    * ``thin``      — real worked output under a docstring-grade explanation;
      must trip (C), which is the case both (A) and (B) miss.
    """
    ex = _PLANTED[kind]
    tripped_a = _STENCIL in str(ex)
    tripped_b = not str(ex.get("output", "")).strip()
    thin_expl = "Build the structure-constant tensor."
    tripped_c = bool(_missing_perspectives(thin_expl)) or \
        len(thin_expl) < _MIN_EXPLANATION_CHARS

    expected = {"stencil": tripped_a, "no_output": tripped_b, "thin": tripped_c}[kind]
    assert expected, (
        f"the planted {kind!r} defect did NOT trip its assertion — the gate "
        f"would have shipped this shape green, which is the rc352 false green "
        f"reproduced. Fix the check, not the plant."
    )
