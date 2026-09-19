"""`#T1188` — every ABI pin literal in tests/ must equal the live ABI, in BOTH
spellings: the comment a sweep can grep for, and the local it cannot.

THE DEFECT CLASS, MEASURED THREE TIMES IN THIRTEEN RCS. ``test_bus.py`` holds
its ABI pin as a local, then interpolates it into the failure message::

    # ABI-PIN: EXPECTED_ABI_VERSION == 26      <- a sweep CAN see this
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

#: ``ABI-PIN: EXPECTED_ABI_VERSION == 29  (any trailing prose)``, as it appears
#: inside a comment token. Two of the live sites carry a ``⚠️`` before the
#: keyword, which sits outside the match rather than needing to be spelled.
#:
#: ⚠️ rc475 (`#T1188`): THIS COMMENT IS ITSELF A PIN, and the gate is right to
#: say so. It is a ``#:`` comment, not part of the docstring, so ``tokenize``
#: yields it as a genuine COMMENT token and the pattern above matches its own
#: example. The rc475 ABI sweep updated the four sites in ``test_bus.py`` and
#: ``test_introspect.py``, missed this one, and the gate caught it — which is
#: the gate working, and a fifth consecutive rc in which an ABI sweep left a
#: pin behind. The example is deliberately NOT de-fanged (by mangling the
#: keyword, say): a pattern that cannot match its own documentation is a
#: pattern nobody can check by eye. It moves with the number, like any pin.
_PIN_COMMENT = re.compile(r"ABI-PIN:\s*(\w*ABI\w*)\s*==\s*(\d+)")

#: A local holding an ABI literal — the half a ``== <n>`` sweep cannot see.
_ABI_NAME = re.compile(r"abi", re.IGNORECASE)

#: "abi" inside an EXPRESSION, not preceded by a letter. See
#: :func:`_subscript_pins` for the false positive this exists to exclude.
_ABI_IN_EXPR = re.compile(r"(?<![A-Za-z])abi", re.IGNORECASE)

#: ``(module, expression)`` rows that read "abi" and are NOT live pins: a
#: cascade DESCRIPTOR's declared graduation ABI is DATED data about when the C
#: peer landed, and moving it with a bump would falsify the record. Held as an
#: explicit, exactly-asserted pair rather than as a file exemption, so a THIRD
#: such row has to be adjudicated instead of joining them silently.
_DESCRIPTOR_ABI_ROWS = frozenset({
    ("test_octonion_dft_rc111.py", "cascade['native']['abi_version']"),
    ("test_quaternion_dft_rc110.py", "cascade['native']['abi_version']"),
})


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


def _subscript_pins():
    """``(module, lineno, expression, literal)`` for the SUBSCRIPT form.

    ⚠️ THE THIRD SPELLING, AND IT SHIPPED STALE AT rc476 (`#T1188`). The rc476
    sweep enumerated every site both predicates above know — 4 comment tokens,
    2 grep-invisible locals, 21 assert lines, 5 sources — moved all of them,
    ran THIS FILE GREEN, and still left ``test_introspect.py``'s
    ``assert status["expected_abi"] == 27`` behind, because the value sits in a
    ``Compare`` against a ``Subscript`` and is therefore neither an
    ``ast.Assign`` to an /abi/i NAME (the local form) nor a
    ``(NATIVE|EXPECTED)_ABI_VERSION == <n>`` line (the ad-hoc grep form). Its
    ABI-PIN comment two lines above WAS updated, which is the rc452 / rc455 /
    rc464 defect exactly: edit the grep target, stop. The comment at that site
    has named itself "the SUBSCRIPT form ... the sweep could not see" since
    rc455, and prose was not enough — twice.

    The predicate is an equality comparison whose LEFT side's source text
    mentions "abi" NOT PRECEDED BY A LETTER, against a plain int literal. Keyed
    on the left side rather than on a key name so ``status["expected_abi"]``,
    ``native["abi_version"]`` and any future ``foo.abi_version`` all land in it.

    The letter guard is not decoration: without it the scan matched
    ``commensurability_verdict(ok)['period_multiplier'] == 17948700`` in
    ``test_music_relations_rc424.py`` — "commensur-ABI-lity" — which is a
    17-million-line away from an ABI pin and would have made this gate demand
    that the music ledger track the ABI.

    :data:`_DESCRIPTOR_ABI_ROWS` carries the rows that ARE ``abi`` and are NOT
    live pins, with the reason, rather than exempting their files.
    """
    for name, path in _modules():
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        try:
            tree = ast.parse(src)
        except SyntaxError:                                  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            if len(node.ops) != 1 or not isinstance(node.ops[0], ast.Eq):
                continue
            right = node.comparators[0]
            if not (isinstance(right, ast.Constant)
                    and isinstance(right.value, int)
                    and not isinstance(right.value, bool)):
                continue
            if not isinstance(node.left, (ast.Subscript, ast.Attribute)):
                continue
            try:
                text = ast.unparse(node.left)
            except Exception:                                # pragma: no cover
                continue
            if not _ABI_IN_EXPR.search(text):
                continue
            if (name, text) in _DESCRIPTOR_ABI_ROWS:
                continue
            yield name, node.lineno, text, right.value


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


def test_abi_pin_expressions_match_the_live_abi():
    """The SUBSCRIPT / ATTRIBUTE form — added rc476 (`#T1188`), because the
    rc476 sweep shipped it stale after passing every other clause in this file.

    Strict zero, same reasoning as the locals: every site this finds compares a
    LIVE ABI reading against a literal, and a literal that disagrees with the
    live value is simply wrong.
    """
    live = _native.EXPECTED_ABI_VERSION
    stale = [p for p in _subscript_pins() if p[3] != live]
    assert not stale, (
        f"ABI pin expression(s) left behind by a bump to {live}: "
        + "; ".join(f"{m}:{ln} has {ex} == {got}" for m, ln, ex, got in stale)
        + ". This is the SUBSCRIPT / ATTRIBUTE spelling — the value is not "
        "bound to an ABI-named local and the line does not read "
        "`(NATIVE|EXPECTED)_ABI_VERSION == <n>`, so neither of the other two "
        "predicates sees it. Update the EXPRESSION, not just the ABI-PIN "
        "comment above it."
    )


def test_the_scan_finds_all_three_spellings():
    """A negative control: no half may silently find nothing.

    Every assertion above passes vacuously if its scan returns an empty list,
    which is exactly how a broken regex or a renamed pin would read as green.
    """
    comments = list(_comment_pins())
    locals_ = list(_local_pins())
    exprs = list(_subscript_pins())
    assert len(comments) >= 3, (
        f"expected at least the 3 ABI-PIN comments measured at rc464, "
        f"found {len(comments)}: {comments}"
    )
    assert len(locals_) >= 2, (
        f"expected at least the 2 grep-invisible locals measured at rc464 "
        f"(both in test_bus.py), found {len(locals_)}: {locals_}"
    )
    assert len(exprs) >= 22, (
        f"expected at least the 22 expression-form pins measured at rc476 "
        f"(21 `_native.*_ABI_VERSION` attribute comparisons plus "
        f"test_introspect.py's `status['expected_abi']`), found "
        f"{len(exprs)}: {exprs}"
    )
    assert any(m == "test_introspect.py" for m, _ln, _ex, _v in exprs), (
        "the expression scan no longer sees test_introspect.py's "
        "`status['expected_abi']` — the one site that motivated this predicate "
        "and the one no other clause in this file can reach"
    )


def test_the_descriptor_rows_are_exactly_the_two_measured():
    """The excluded rows are DATA, and the exclusion cannot grow quietly.

    A cascade descriptor's `native.abi_version` records the ABI its C peer
    graduated at. It is a dated fact and must NOT move with a bump — but it
    reads "abi" and compares against an int, so the predicate would demand it.
    Two such rows exist; this asserts EXACTLY two, so a third is adjudicated
    rather than appended.
    """
    found = set()
    for name, path in _modules():
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        try:
            tree = ast.parse(src)
        except SyntaxError:                                  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare) or len(node.ops) != 1:
                continue
            if not isinstance(node.ops[0], ast.Eq):
                continue
            right = node.comparators[0]
            if not (isinstance(right, ast.Constant)
                    and isinstance(right.value, int)
                    and not isinstance(right.value, bool)):
                continue
            if not isinstance(node.left, (ast.Subscript, ast.Attribute)):
                continue
            text = ast.unparse(node.left)
            if _ABI_IN_EXPR.search(text) and (name, text) in _DESCRIPTOR_ABI_ROWS:
                found.add((name, text))
    assert found == set(_DESCRIPTOR_ABI_ROWS), (
        "the descriptor-ABI exclusion list does not match what the tree "
        f"carries. missing: {sorted(set(_DESCRIPTOR_ABI_ROWS) - found)}; "
        f"unexpected: {sorted(found - set(_DESCRIPTOR_ABI_ROWS))}. An entry "
        "that no longer matches is an exclusion protecting nothing."
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
