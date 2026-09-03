"""`#T1188` — every ABI pin literal in tests/ must equal the live ABI, in BOTH
spellings: the comment a sweep can grep for, and the local it cannot.

THE DEFECT CLASS, MEASURED THREE TIMES IN THIRTEEN RCS. ``test_bus.py`` holds
its ABI pin as a local, then interpolates it into the failure message::

    # ABI-PIN: EXPECTED_ABI_VERSION == 25      <- a sweep CAN see this
    want_abi = 24                              <- a sweep CANNOT, and this is
    assert _native.EXPECTED_ABI_VERSION == want_abi, (      the asserted one
        f"EXPECTED_ABI_VERSION should be {want_abi}; got ..."
    )

The indirection is CORRECT and rc449 introduced it on purpose: naming the value
once means the failure message cannot disagree with the assertion, a drift that
had shipped a message reading "should be 15" beside an assert of 18. But it
moves the literal off the assert line, where a ``*_ABI_VERSION == <n>`` sweep
can no longer see it. The comment above it exists to give that sweep a target.

⚠️ THE TARGET WORKED AND THE OUTCOME STILL FAILED, THREE TIMES. rc452, rc455 and
rc464 each swept the comments to the new value and left the locals on the old
one, shipping both bus tests RED. rc464 is the sharpest case: the CHANGELOG
names this exact file as a site the bump covered, and it did cover it — it
edited the grep targets and not the values. A grep target is a message to a
HUMAN reader; all three bumps were driven by a script, which read the message,
did what it literally said, and stopped. Two rounds of increasingly emphatic
prose in ``test_bus.py`` did not prevent the third occurrence, so the remedy is
no longer prose.

WHAT THIS GATE READS. Both spellings, over every module in ``tests/``:

  * COMMENT form — an ``ABI-PIN: <NAME> == <N>`` comment, via :mod:`tokenize`,
    so only real comment tokens match. A docstring that merely QUOTES the
    pattern (as this file's own docstring does, above) is excluded
    structurally rather than by exempting this file, which would blind the
    gate to any pin that later lands here.
  * LOCAL form — any :class:`ast.Assign` binding an int literal to a name
    matching ``/abi/i``, which is the grep-invisible half. Measured at rc464:
    exactly two such sites exist tree-wide, both in ``test_bus.py``, and both
    were the stale ones. There are no others to grandfather, so this is
    strict-zero rather than a down-only ceiling.

Both are compared against ``_native.EXPECTED_ABI_VERSION`` — the compiled-against
value, which is an ``int`` whether or not a library loaded, so THIS GATE RUNS ON
THE PURE PATH. ``NATIVE_ABI_VERSION`` (the loaded library's own report) is
``None`` with no native lib, and that it AGREES with the expected value when a
library IS present is a different claim, asserted by ``test_bus.py`` itself and
by the loader in ``srmech/_native/__init__.py``.

⚠️ WHAT THIS CANNOT DETECT. A pin held in a module-level CONSTANT that is not
named for the ABI, a pin spelled as a keyword-argument default, and any pin
outside ``tests/`` (``srmech.h`` and ``_native/__init__.py`` are the SOURCES the
pins are checked against, not pins themselves). It also cannot see a pin whose
literal is correct but whose surrounding PROSE is stale — rc464 shipped exactly
that in ``test_bus.py``'s first failure message, which still credited the bump
to rc455's arena change, and it was fixed by reading rather than by this gate.
"""
from __future__ import annotations

import ast
import os
import re
import tokenize

from srmech import _native

_TESTS = os.path.dirname(os.path.abspath(__file__))

#: ``ABI-PIN: EXPECTED_ABI_VERSION == 25  (any trailing prose)``, as it appears
#: inside a comment token. Two of the three live sites carry a ``⚠️`` before the
#: keyword, which sits outside the match rather than needing to be spelled.
_PIN_COMMENT = re.compile(r"ABI-PIN:\s*(\w*ABI\w*)\s*==\s*(\d+)")

#: A local holding an ABI literal — the half a ``== <n>`` sweep cannot see.
_ABI_NAME = re.compile(r"abi", re.IGNORECASE)


def _modules():
    for entry in sorted(os.listdir(_TESTS)):
        if entry.endswith(".py") and entry.startswith("test_"):
            yield entry, os.path.join(_TESTS, entry)


def _comment_pins():
    """``(module, lineno, name, literal)`` for every ABI-PIN comment.

    Uses :mod:`tokenize` rather than a line scan so that only genuine COMMENT
    tokens match. This file's docstring quotes the pattern; a line regex would
    flag it, and the usual repair — exempting the gate's own file — would stop
    it from checking any pin that later lands here.
    """
    for name, path in _modules():
        with open(path, "rb") as fh:
            try:
                toks = list(tokenize.tokenize(fh.readline))
            except (tokenize.TokenError, SyntaxError):  # pragma: no cover
                continue
        for tok in toks:
            if tok.type != tokenize.COMMENT:
                continue
            m = _PIN_COMMENT.search(tok.string)
            if m:
                yield name, tok.start[0], m.group(1), int(m.group(2))


def _local_pins():
    """``(module, lineno, target, literal)`` for every int bound to an ABI name."""
    for name, path in _modules():
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        try:
            tree = ast.parse(src)
        except SyntaxError:  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if not isinstance(node.value, ast.Constant):
                continue
            if isinstance(node.value.value, bool):
                continue
            if not isinstance(node.value.value, int):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and _ABI_NAME.search(target.id):
                    yield name, node.lineno, target.id, node.value.value


def test_abi_pin_comments_match_the_live_abi():
    """The grep-target comments are what a sweep edits — they must be right."""
    live = _native.EXPECTED_ABI_VERSION
    pins = list(_comment_pins())
    assert pins, (
        "no ABI-PIN comments found in tests/ — the grep targets are the "
        "mechanism by which an ABI bump locates its pins, and rc464 measured "
        "three of them (test_bus.py x2, test_introspect.py x1). Finding zero "
        "means the scan broke, not that the targets were retired."
    )
    stale = [p for p in pins if p[3] != live]
    assert not stale, (
        f"ABI-PIN comment(s) disagree with EXPECTED_ABI_VERSION == {live}: "
        + "; ".join(f"{m}:{ln} says {nm} == {got}" for m, ln, nm, got in stale)
    )


def test_abi_pin_locals_match_the_live_abi():
    """⚠️ THE HALF A SWEEP CANNOT SEE — stale at rc452, rc455 AND rc464.

    Strict-zero, not a ceiling: every site this finds is a pin on a value that
    moves, and a pin that disagrees with the live value is simply wrong.
    """
    live = _native.EXPECTED_ABI_VERSION
    stale = [p for p in _local_pins() if p[3] != live]
    assert not stale, (
        f"ABI pin local(s) left behind by a bump to {live}: "
        + "; ".join(f"{m}:{ln} has {nm} = {got}" for m, ln, nm, got in stale)
        + ". This is the grep-invisible spelling: the ABI-PIN comment above "
        "each of these was updated and the assigned value was not. Update the "
        "LOCAL, then re-run the module the bump edited."
    )


def test_the_scan_finds_both_spellings():
    """A negative control: neither half may silently find nothing.

    Both assertions above pass vacuously if their scan returns an empty list,
    which is exactly how a broken regex or a renamed pin would read as green.
    """
    comments = list(_comment_pins())
    locals_ = list(_local_pins())
    assert len(comments) >= 3, (
        f"expected at least the 3 ABI-PIN comments measured at rc464, "
        f"found {len(comments)}: {comments}"
    )
    assert len(locals_) >= 2, (
        f"expected at least the 2 grep-invisible locals measured at rc464 "
        f"(both in test_bus.py), found {len(locals_)}: {locals_}"
    )


def test_the_stale_local_would_be_caught():
    """Prove the predicates can FAIL — they could not, for three rcs.

    Replays rc464's actual defect (an int bound to an ABI-named local holding
    the PREVIOUS value) through the same predicates the gate uses, and requires
    both to flag it. Without this, a scan that matched nothing would report the
    same green as a scan that matched everything correctly.
    """
    live = _native.EXPECTED_ABI_VERSION

    planted = ast.parse(f"want_abi = {live - 1}\n")
    node = planted.body[0]
    assert isinstance(node, ast.Assign)
    target = node.targets[0]
    assert isinstance(target, ast.Name)
    assert _ABI_NAME.search(target.id), "the name predicate must match want_abi"
    assert isinstance(node.value, ast.Constant)
    assert node.value.value != live, "the planted pin must be stale by construction"

    m = _PIN_COMMENT.search(f"# ABI-PIN: EXPECTED_ABI_VERSION == {live - 1}")
    assert m is not None, "the comment predicate must match the live spelling"
    assert int(m.group(2)) != live
