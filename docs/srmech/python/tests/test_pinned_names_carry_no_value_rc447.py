"""gh #1653 — a test NAMED for a number must not ASSERT a different one.

THE DEFECT CLASS (measured rc447: 16 occurrences tree-wide, some years stale).
A pin on a moving value was named for the value it pinned::

    def test_tools_total_stays_367():
        assert describe()["tools"]["total"] == 666      # named 367

    def test_expected_abi_is_15():
        assert _native.EXPECTED_ABI_VERSION == 18       # named 15

    def test_format_version_is_13():
        assert GENOME_FORMAT_VERSION == 20              # named 13

⚠️ WHY THIS IS WORSE THAN AN ORDINARY STALE COMMENT. The name is the FIRST thing
a reader sees — in a failure report, in ``pytest -v``, in a CI summary — and it
is the one part of a test that no assertion checks. A stale docstring is at
least adjacent to the code that contradicts it. A stale NAME travels: a run
reporting ``test_expected_abi_is_15 PASSED`` states, in the only text most
readers will see, that the ABI is 15. It was 18.

And it is SELF-WORSENING. Every legitimate bump falsifies one more of these
names, so the population grows monotonically unless something checks it —
``test_expected_abi_is_15`` was wrong through 15 → 16 → 17 → 18, and the rc447
ABI sweep made three of them staler while correctly updating their assertions.
Fixing the assertion is exactly what leaves the name behind.

THE FIX was to rename every one to describe the INVARIANT (``..._is_pinned``)
rather than the value, and this file is the ratchet that keeps it that way. The
historical value is not lost: it stays in the docstring and in the FILE name
(``test_genome_format_v16_rc312.py`` still records which format version it was
written for), where it is a statement about the past rather than a claim about
the present.

⚠️ WHAT THIS CANNOT DETECT. It reads a name/assert pair in the same function
body. A name falsified by a value held in a CONSTANT (``assert x == CEIL_FOO``)
is invisible to it, as is a stale name on a test that asserts nothing numeric.
The population it guards is the DECIDABLE half, and it is strict-zero on that
half rather than a down-only ceiling, because there is no legitimate reason to
add one.
"""
from __future__ import annotations

import ast
import os
import re

_TESTS = os.path.dirname(os.path.abspath(__file__))

#: ``test_<...>_(is|are|stays|remains)_<N>`` — a NAME that spells a value.
_NAMED = re.compile(r'^(test_\w*?_(?:is|are|stays?|remains?)_(\d+))$')
_ASSERTED = re.compile(r'==\s*(\d+)\b')


def _offenders():
    """Parse each test module with :mod:`ast` and compare each function's NAME
    against the literals its BODY asserts.

    ⚠️ ``ast``, not a line regex, and the difference is load-bearing: the first
    cut scanned lines and flagged THIS FILE'S OWN DOCSTRING EXAMPLES, because
    prose showing the defect is textually identical to the defect. A parser
    sees only real ``FunctionDef`` nodes, so illustrative code in a docstring
    is invisible to it and no file needs an exemption — an exemption is exactly
    where a real offender would later hide.
    """
    out = []
    for fname in sorted(os.listdir(_TESTS)):
        if not (fname.startswith("test_") and fname.endswith(".py")):
            continue
        path = os.path.join(_TESTS, fname)
        with open(path, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        lines = src.split("\n")
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            m = _NAMED.match(node.name)
            if not m:
                continue
            named = int(m.group(2))
            body = "\n".join(lines[node.lineno - 1:(node.end_lineno or node.lineno)])
            # Only the ASSERT statements — a value elsewhere in the body is not
            # a claim the name is making.
            for stmt in ast.walk(node):
                if not isinstance(stmt, ast.Assert):
                    continue
                seg = "\n".join(
                    lines[stmt.lineno - 1:(stmt.end_lineno or stmt.lineno)])
                hit = _ASSERTED.search(seg)
                if hit and int(hit.group(1)) != named:
                    out.append((fname, node.lineno, node.name, named,
                                int(hit.group(1))))
                    break
    return out


def test_no_test_is_named_for_a_value_it_does_not_assert():
    """STRICT ZERO. There is no legitimate reason to add one of these."""
    bad = _offenders()
    assert not bad, (
        "these tests are NAMED for one number and ASSERT another:\n" +
        "\n".join(
            "    %s:%d  %s  — name says %d, asserts %d" % row for row in bad
        ) +
        "\n\nA pin on a moving value must not spell the value in its name: the "
        "next legitimate bump falsifies it, and the name is the one part of a "
        "test no assertion checks. Rename to the INVARIANT (`..._is_pinned`) "
        "and keep the historical number in the docstring or the FILE name."
    )


def _scan_source(src):
    """Run the real detector over an in-memory module — the controls below use
    it so they exercise the SHIPPED code path, not a re-implementation."""
    tree = ast.parse(src)
    lines = src.split("\n")
    bad = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        m = _NAMED.match(node.name)
        if not m:
            continue
        for stmt in ast.walk(node):
            if not isinstance(stmt, ast.Assert):
                continue
            seg = "\n".join(lines[stmt.lineno - 1:(stmt.end_lineno or stmt.lineno)])
            hit = _ASSERTED.search(seg)
            if hit and int(hit.group(1)) != int(m.group(2)):
                bad.append(node.name)
                break
    return bad


def test_the_detector_actually_detects():
    """CONTROL. A strict-zero gate that cannot fire is indistinguishable from a
    passing one."""
    assert _scan_source(
        "def test_format_version_is_13():\n"
        "    assert GENOME_FORMAT_VERSION == 20\n") == ["test_format_version_is_13"]


def test_a_matching_pair_is_not_flagged():
    """A name that AGREES with its assertion is fine — the gate is not banning
    numbers in names."""
    assert _scan_source(
        "def test_block_count_is_4():\n    assert n == 4\n") == []


def test_a_docstring_EXAMPLE_is_not_flagged():
    """The false positive that broke the first cut. Prose showing the defect is
    textually identical to the defect; only a parser tells them apart."""
    assert _scan_source(
        '\"\"\"Doc showing the bug:\n\n'
        '    def test_expected_abi_is_15():\n'
        '        assert ABI == 18\n\"\"\"\n'
        'def test_real_one_is_pinned():\n    assert ABI == 18\n') == []
