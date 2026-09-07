"""The removed stale selector may not come back, and the sweep that says so is a
GATE rather than a note (rc469, `#T1188`).

WHAT WAS REMOVED, AND WHY A SWEEP IS THE RIGHT INSTRUMENT
=========================================================
``tools/run_worked_examples.py`` and ``tools/run_example_args.py`` carried a flag
that scoped a ledger re-run to rows whose SNIPPET TEXT hash had moved. Nine
fields ride each ledger row; that predicate consulted exactly one, so it was
structurally blind to the change it was most often reached for — an
implementation moving underneath a snippet whose text has not moved a byte.
rc468 measured the cost on the sibling ledger: a full re-harvest moved 20 rows,
17 of them pre-existing staleness the scoped path had been hiding.

The removal swept 27 live mentions out of 12 files. What makes that removal
DECIDABLE, rather than a thing a reader has to adjudicate case by case, is that
**no live file spells the flag any more** — not even the removal-rationale
section in ``run_worked_examples.py``'s own docstring, which points at the
CHANGELOG for the spelling instead. So the residual is exactly two DATED
records, and any future hit outside them is a defect with no allowlist to argue
about.

That property is worth precisely as much as the instrument that checks it. Until
this file, there was none: the sweep was run by hand once and nothing stopped
the name reappearing — in a remediation string, in a hook's operator text (which
is where the loudest live copy was), or in a new tool that copies an old one.
Three agents reached for the flag in the first place because a FAILING GATE had
named it; a fourth would only need one file to name it again.

WHY THE NEEDLE IS ASSEMBLED RATHER THAN WRITTEN
===============================================
A strict-zero sweep for a literal cannot contain that literal, or it matches
itself and every future reader has to be told about the exemption. The needle is
built from two halves at import time, the same reason ``test_jpl_audit`` masks C
literals before scanning for banned spellings: a gate that needs an exemption for
its own text has already lost the property that made it decidable.

WHAT IT WOULD MISS, SAID PLAINLY
================================
It is a TEXT sweep. It cannot see a differently-spelled selector that
reintroduces the same predicate — a ``--changed-only``, or a caller computing the
stale set itself and passing ``--only``. That second shape was explicitly
rejected during the removal (it re-implements the removed predicate in a third
file) and is guarded by review, not by this file. What this file guarantees is
narrow and total: THIS name does not come back to a live surface.
"""

from __future__ import annotations

import os
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PKG_ROOT = _HERE.parent                       # docs/srmech/python
_SRMECH_ROOT = _PKG_ROOT.parent                # docs/srmech

#: Assembled, never written whole — see the docstring.
_NEEDLES = ("--only" + "-stale", "only" + "_stale")
_NEEDLE_BYTES = tuple(n.encode("utf-8") for n in _NEEDLES)

#: The two DATED records that name the flag legitimately: a changelog entry
#: describing the release that removed it, and an ADR slice recording the state
#: of the tree when it was written. Rewriting either to match new reality would
#: FALSIFY it (ADR-0010 Amendment A.3), so they are exempt by identity rather
#: than by pattern — a pattern would quietly exempt the next file too.
_DATED_RECORDS = frozenset({
    "python/CHANGELOG.md",
    "adr/0010-namespace-declustering.md",
})

_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules",
              ".claude", "build", "_native", ".venv", "venv"}

_TEXT_SUFFIXES = {".py", ".md", ".c", ".h", ".txt", ".toml", ".cfg", ".yml",
                  ".yaml", ".sh", ".ndjson", ".json", ".rst"}


def _scan() -> dict[str, list[int]]:
    """``{repo-relative path: [1-indexed line numbers]}`` for every live hit."""
    # ``os.walk`` with IN-PLACE dir pruning, not ``rglob`` — measured on this
    # tree: ``rglob("*")`` plus a ``is_file()`` per entry walks 14,726 paths and
    # stats every one of them, 90 s of it on a Windows-mounted filesystem, most
    # spent inside ``__pycache__`` subtrees that are then filtered out anyway.
    # Pruning at the directory level never descends into them.
    hits: dict[str, list[int]] = {}
    for dirpath, dirnames, filenames in os.walk(_SRMECH_ROOT):
        dirnames[:] = [x for x in dirnames if x not in _SKIP_DIRS]
        base = Path(dirpath)
        for fname in filenames:
            if os.path.splitext(fname)[1] not in _TEXT_SUFFIXES:
                continue
            path = base / fname
            rel = path.relative_to(_SRMECH_ROOT).as_posix()
            if rel in _DATED_RECORDS:
                continue
            try:
                data = path.read_bytes()
            except OSError:                      # pragma: no cover
                continue
            # BYTES first: the generated C registry alone is 3.6 MB and the
            # scanned set is 186 MB, so decoding every file to find nothing is
            # pure cost. Only a file that actually matches is decoded, and only
            # then to turn the hit into a LINE NUMBER an operator can open.
            if not any(n in data for n in _NEEDLE_BYTES):
                continue
            text = data.decode("utf-8", errors="replace")
            lines = [i for i, ln in enumerate(text.splitlines(), 1)
                     if any(n in ln for n in _NEEDLES)]
            if lines:
                hits[rel] = lines
    return hits


def test_no_live_surface_names_the_removed_stale_selector():
    """STRICT ZERO. Two dated records are exempt; nothing else is."""
    hits = _scan()
    assert hits == {}, (
        "the removed stale ledger selector is named on a LIVE surface again:\n"
        + "\n".join(f"  {rel}:{','.join(str(n) for n in lines)}"
                    for rel, lines in sorted(hits.items()))
        + "\n\nIt hashes the snippet TEXT, so it cannot see an implementation "
          "moving under an unchanged snippet — which is the case a ledger "
          "re-run is usually reached for. Re-run the ledger IN FULL instead, "
          "and see the rc469 CHANGELOG entry for the measurement."
    )


def test_the_two_dated_records_still_carry_the_name():
    """The exemptions must be LIVE, or the sweep is exempting nothing.

    An allowlist entry that no longer matches anything is the quiet way a
    strict-zero gate turns into a gate over an empty set: the file gets renamed
    or the record edited, the entry stays, and the next reader believes two
    surfaces were adjudicated when zero were. It also pins the other half of the
    discipline — those records are DATED, and removing the name from them to
    make the tree "clean" would falsify them.
    """
    missing = []
    for rel in sorted(_DATED_RECORDS):
        path = _SRMECH_ROOT / rel
        if not path.exists():
            missing.append(f"{rel} (file is gone)")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not any(n in text for n in _NEEDLES):
            missing.append(f"{rel} (no longer names it)")
    assert missing == [], (
        "dated-record exemption(s) that exempt nothing: " + ", ".join(missing)
        + "\nEither the record moved (repoint the entry) or its text was "
          "rewritten (which falsifies a dated record — ADR-0010 Amendment A.3)."
    )


def test_the_gate_can_actually_fire():
    """The needle matches the real spelling.

    Without this the whole file could be a sweep for a string that never occurs,
    passing forever on a typo. It re-derives the two halves and checks them
    against the dated record that legitimately carries them.
    """
    changelog = (_SRMECH_ROOT / "python" / "CHANGELOG.md").read_text(
        encoding="utf-8", errors="replace")
    assert _NEEDLE_BYTES == tuple(n.encode("utf-8") for n in _NEEDLES)
    for needle in _NEEDLES:
        assert len(needle) > 6 and needle not in __doc__, (
            f"the needle {needle!r} leaked into this file's own text; a "
            f"strict-zero sweep that matches itself needs an exemption for "
            f"itself, which is the property it exists to avoid"
        )
    assert _NEEDLES[0] in changelog, (
        f"{_NEEDLES[0]!r} does not appear in CHANGELOG.md, so the sweep above "
        f"is scanning for a string this tree never used — check the spelling"
    )
