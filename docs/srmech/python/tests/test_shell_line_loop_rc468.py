"""Strict zero: no shell line-loop in the tree can silently drop its last row.
(rc468, `#T1188`)

THE DEFECT, MEASURED TWICE IN ONE rc
====================================
``while read -r n; do ... done < names.txt`` does not process a final line that
has no trailing newline. ``read`` returns nonzero at EOF *after* it has already
assigned the variables, so the bare form assigns and then discards. In rc467
that happened twice while driving the worked-example ledger by name: one pass
silently covered **70 of 71** rows, another **54 of 55** — and the row the
second one missed was ``quaternion_twiddle``, one of the very ops that rc's
change was about. Both were caught only by diffing ran-against-wanted
afterwards.

MEASURED, WSL2 / bash 5.1.16, over a 3-line file with NO trailing newline::

    while read -r x; do ...                     ->  2      DROPS
    cat f | while read -r x; do ...             ->  2      DROPS
    wc -l < f                                   ->  2
    while read -r x || [ -n "$x" ]; do ...      ->  3      correct
    mapfile -t arr < f                          ->  3      correct
    grep -c . f                                 ->  3

⚠️ NOTE THE THIRD ROW. A count assertion built on ``wc -l`` **agrees with the
broken loop** — both report N-1 — so it cannot fail on this class. That is why
the rc467 catch used ``grep -c .``, which is newline-independent.

WHAT THIS GATE IS, AND HONESTLY IS NOT
======================================
Its live population is **ZERO**: exactly one shell read-loop exists in the
tracked tree (``docs/srmech/rbs_lm_research/check_swap.sh``, reading
``/proc/swaps``, which IS newline-terminated), and rc468 converted it to the
guarded form rather than allowlisting it — an exemption is a place for the rule
to rot. Both rc467 incidents were **session one-liners**, in no committed file,
so this gate could not have caught either of them and it is not claimed to.

The CLASS guard for that lives at the instrument the loops drive:
``tools/run_worked_examples.py`` now takes N names and refuses an unknown one,
and — the part that catches a drop from ANY driver, including a shell loop this
file never sees — every ledger row carries a ``def_blob`` content stamp, so a
row a partial pass skipped keeps its old stamp and
``tools/hooks/derived_ledger_freshness.py`` names it at the next Stop.

This gate's job is narrower and worth having anyway: it stops the idiom from
being *re-introduced* into a committed script, where it would then be run by CI
or by a human indefinitely.

SCOPE
=====
Tracked ``.sh`` / ``.yml`` / ``.yaml``, plus ``bash`` / ``sh`` / ``shell``
fenced blocks in tracked ``.md``. Enumerated with ``git ls-files``, so
``node_modules/``, ``lib/``, ``bin/`` and other untracked trees are excluded by
construction rather than by an exclusion list that can drift. Prose OUTSIDE a
shell fence is not scanned — describing the bad idiom in a paragraph is how
this file itself documents it. PowerShell is out of scope; ``Get-Content`` does
not have this failure mode.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]


def _is_checkout() -> bool:
    """The population comes from ``git ls-files``, so say so when it cannot.

    A SKIP is reported and visible; a hard failure outside a checkout would be
    a false red, and silently scanning nothing would be the vacuous pass this
    file exists to avoid. CI runs in a checkout, which is where it matters.
    """
    if shutil.which("git") is None:
        return False
    p = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                       cwd=str(REPO), stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL, check=False)
    return p.returncode == 0


_NEEDS_GIT = pytest.mark.skipif(
    not _is_checkout(),
    reason="the scan population is `git ls-files`; not a git checkout")

#: a ``while``/``until`` line that runs ``read``. The guard clause, when
#: present, is on the same line by construction — it is part of the loop
#: condition.
_LOOP = re.compile(r"\b(?:while|until)\b[^\n#]*?\bread\b")

#: the accepted repairs. ``|| [ -n "$v" ]`` / ``|| [[ -n $v ]]`` re-enters the
#: body for the unterminated final line; ``read -d`` changes the delimiter
#: entirely (``-d ''`` for NUL-separated input) and is a different contract.
_GUARDED = re.compile(r"\|\|\s*\[\[?\s*(?:!\s*-z|-n)\b|\bread\b[^\n#]*?\s-\w*d\b")

_FENCE = re.compile(r"^\s*```+\s*(\w*)", re.M)


def _tracked(suffixes: tuple) -> list:
    out = subprocess.run(["git", "ls-files"], cwd=str(REPO),
                         stdout=subprocess.PIPE, check=False)
    if out.returncode != 0:
        return []
    return [REPO / p for p in out.stdout.decode("utf-8", "replace").split("\n")
            if p and p.endswith(suffixes)]


def _shell_lines(path: Path) -> list:
    """``[(lineno, text)]`` of the lines this gate is entitled to judge."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.split("\n")
    if path.suffix != ".md":
        return list(enumerate(lines, start=1))
    # markdown: only inside a bash/sh/shell fence
    out, lang = [], None
    for i, line in enumerate(lines, start=1):
        m = _FENCE.match(line)
        if m:
            lang = None if lang is not None else (m.group(1) or "").lower()
            continue
        if lang in {"bash", "sh", "shell", "console"}:
            out.append((i, line))
    return out


def _offenders() -> list:
    bad = []
    for path in _tracked((".sh", ".yml", ".yaml", ".md")):
        for lineno, line in _shell_lines(path):
            if _LOOP.search(line) and not _GUARDED.search(line):
                bad.append((path.relative_to(REPO).as_posix(), lineno,
                            line.strip()[:110]))
    return bad


def test_the_predicate_can_actually_fire() -> None:
    """NON-VACUITY. A strict-zero gate over a population of zero proves
    nothing unless the predicate is shown to discriminate."""
    bare = 'while read -r name; do echo "$name"; done < names.txt'
    guarded = 'while read -r name || [ -n "$name" ]; do echo "$name"; done < f'
    piped = 'cat f | while IFS= read -r line; do :; done'
    nul = "find . -print0 | while IFS= read -r -d '' p; do :; done"
    assert _LOOP.search(bare) and not _GUARDED.search(bare)
    assert _LOOP.search(piped) and not _GUARDED.search(piped)
    assert _LOOP.search(guarded) and _GUARDED.search(guarded)
    assert _LOOP.search(nul) and _GUARDED.search(nul)
    assert not _LOOP.search("for f in *.txt; do read_config; done")


@_NEEDS_GIT
def test_the_scan_population_is_not_empty() -> None:
    """The other half of non-vacuity: the file list must be real."""
    files = _tracked((".sh", ".yml", ".yaml", ".md"))
    assert len(files) > 100, (
        f"only {len(files)} tracked files matched — `git ls-files` failed or "
        "this is not a checkout, and the strict zero below would be vacuous")


@_NEEDS_GIT
def test_no_unguarded_shell_line_loop_is_tracked() -> None:
    bad = _offenders()
    assert not bad, (
        "unguarded shell line-loop(s) — these DROP a final line with no "
        "trailing newline, which is how rc467 ran 70 of 71 and then 54 of 55 "
        "rows without noticing:\n"
        + "\n".join(f"  {p}:{n}  {t}" for p, n, t in bad)
        + "\n\nUse `while read -r v || [ -n \"$v\" ]; do` (re-enters the body "
          "for the unterminated line), or `mapfile -t`, or drive the list from "
          "Python. Do NOT check the count with `wc -l`: it under-reports by "
          "one on the same input and therefore agrees with the broken loop.")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
