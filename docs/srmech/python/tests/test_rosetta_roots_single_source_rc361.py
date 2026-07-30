"""rc361 (`#T1034`) — the Rosetta walk roots have ONE definition, and stay that way.

WHY THIS EXISTS. The 12-entry Rosetta walk-root tuple was hardcoded in FOUR
places, each under a comment asking the next author to keep all four in step:

    tests/test_rosetta_completeness.py        _ROOTS
    tests/conftest.py                         _ROSETTA_ROOTS
    tests/test_rosetta_transitive_standalone.py _ROOTS
    notes/_rosetta_inventory.py               ROOTS

Measured at rc361 before the collapse: all four were IDENTICAL in content —
same 12 entries in the same order. The only divergence was a shape one
(``notes/`` used a ``list``, the three test sites used a ``tuple``), which
changes nothing that reads them. So this was latent duplication rather than an
already-diverged bug, and rc361 collapsed it to ``tests/rosetta_roots.py``
before ADR-0010 gave it a chance to diverge.

WHY IT IS LOAD-BEARING FOR THE DECLUSTERING ARC. This tuple is the DENOMINATOR
of the Rosetta ledger walk. A namespace not listed in it is not walked, so ops
that move there become invisible to ``rosetta_live_objects()``. The ledger then
fires its STALE assertion (a classified row whose live op vanished) and never
its UNCLASSIFIED one (a live op with no bucket) — so a MOVE is reported with
the signature of a DELETION. With four copies, a partial update produces
exactly that misleading diagnosis; with one, the rename edits one tuple.

WHAT THIS FILE ASSERTS RATHER THAN DESCRIBES:
  1. the canonical value is what the arc expects (pinned, so widening is a
     deliberate edit and not a drift);
  2. no consumer holds its own copy — checked by scanning the tree for the
     literal tuple shape, so a FIFTH copy fails the build;
  3. the scan can actually detect a copy (non-vacuity — it is fed one);
  4. the measured GAP: the roots contain none of ADR-0010's NEW namespaces,
     and a root naming a package that does not exist is silently skipped, which
     is why rc361 deliberately does NOT pre-widen the tuple.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SR_ROOT = _HERE.parent.parent          # docs/srmech

if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from rosetta_roots import ROSETTA_ROOTS  # noqa: E402

#: The canonical module, and the ONLY file allowed to spell the tuple out.
_CANONICAL_REL = "python/tests/rosetta_roots.py"

#: The rc361 root set, pinned so a widening is a deliberate two-file edit.
_EXPECTED_ROOTS = (
    "srmech.amsc",
    "srmech.qm",
    "srmech.signal_processing",
    "srmech.bus",
    "srmech.dsl",
    "srmech.mcp",
    "srmech.cli",
    "srmech.llm",
    "srmech.spectral",
    "srmech.rbs_lm",
    "srmech.introspect",
    "srmech.profile_loader",
)

#: ADR-0010's destination namespaces that DO NOT EXIST YET.
#:
#: Read off the ADR's own namespace table and its per-destination count table.
#: ``srmech.apokatastasis`` is the largest single destination (31 modules, 41%
#: of the moves) and, like the rest of these, is absent from the walk roots.
_ADR0010_NEW_NAMESPACES = (
    "srmech.math",
    "srmech.physics",
    "srmech.biology",
    "srmech.music",
    "srmech.apokatastasis",
    "srmech.cascade",
    "srmech.external",
)

#: ADR-0010 destinations that ALREADY EXIST as walk roots.
#:
#: ⚠️ These matter to the honesty of the gap claim. The rc361 brief said the
#: roots contain NONE of ADR-0010's target namespaces; the TREE says otherwise —
#: ``srmech.amsc`` (which KEEPS 4 modules) and ``srmech.introspect`` (which
#: GAINS 10) are both destinations and both are already roots, and ``srmech.dsl``
#: stays put. So the blindness is PARTIAL, not total: ops moving to
#: ``introspect`` stay visible to the walk, ops moving to the seven namespaces
#: above do not. Asserted below so the correction cannot be lost.
_ADR0010_EXISTING_DESTINATIONS = ("srmech.amsc", "srmech.introspect", "srmech.dsl")

#: Detects a spelled-out copy of the root tuple: the quoted literal every copy
#: ended with. Measured at rc361 — this token appeared in EXACTLY the four known
#: copies and nowhere else in ``docs/srmech``, which is what makes it a precise
#: detector rather than a heuristic. A prose mention would have to quote the
#: string WITH its double quotes to trip it.
_COPY_TOKEN = re.compile(r'"srmech\.profile_loader"')

#: Files that legitimately contain the token for a reason other than being a
#: copy: the canonical module, and this test (which pins the value and therefore
#: must spell it out to be able to compare).
_ALLOWED = frozenset({_CANONICAL_REL, "python/tests/" + Path(__file__).name})


def _files_spelling_the_tuple() -> "list[str]":
    """Every file under ``docs/srmech`` that spells the root tuple out."""
    hits: list[str] = []
    for path in sorted(_SR_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts or "worktrees" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:                                    # pragma: no cover
            continue
        if _COPY_TOKEN.search(text):
            hits.append(path.relative_to(_SR_ROOT).as_posix())
    return hits


def test_the_canonical_root_set_is_what_the_arc_expects() -> None:
    """Pinned, so ADR-0010's widening is a deliberate edit in two files."""
    assert ROSETTA_ROOTS == _EXPECTED_ROOTS, (
        "the canonical Rosetta walk roots changed.\n"
        f"  canonical: {ROSETTA_ROOTS}\n"
        f"  expected:  {_EXPECTED_ROOTS}\n"
        "If ADR-0010 is now moving modules, update BOTH tests/rosetta_roots.py "
        "and _EXPECTED_ROOTS here, in the same commit as the module move.")
    assert len(set(ROSETTA_ROOTS)) == len(ROSETTA_ROOTS), "duplicate root"


def test_no_consumer_keeps_its_own_copy_of_the_root_tuple() -> None:
    """⚠️ THE FIFTH-COPY GATE. The whole point of rc361's instrument 2.

    Four copies drifting apart is the failure this rc removed. Re-inlining the
    list — in a new test, a new note script, a new tool — would restore it
    silently, because every consumer would still work in isolation.
    """
    spelled = _files_spelling_the_tuple()
    extra = [f for f in spelled if f not in _ALLOWED]
    assert not extra, (
        f"{len(extra)} file(s) spell the Rosetta root tuple out instead of "
        f"importing it:\n" + "\n".join(f"    {f}" for f in extra)
        + f"\n\nThe canonical definition is {_CANONICAL_REL}. Import it:\n"
          "    from rosetta_roots import ROSETTA_ROOTS\n"
          "(guarding tests/ onto sys.path first — tests/ is a package, so "
          "pytest's prepend import-mode does not add it). From OUTSIDE the "
          "package and outside tests/, load it by path with "
          "importlib.util.spec_from_file_location — see notes/_rosetta_inventory.py. "
          "rc361 collapsed four copies into one so the ADR-0010 rename edits "
          "one tuple; do not grow a fifth.")
    assert _CANONICAL_REL in spelled, (
        f"{_CANONICAL_REL} no longer spells the tuple out — either it moved (fix "
        f"_CANONICAL_REL) or the detector has stopped matching, which would make "
        f"the assertion above vacuous.")


def test_the_fifth_copy_detector_can_actually_fail(tmp_path: Path) -> None:
    """⚠️ NON-VACUITY. A scan that matches nothing would pass forever.

    Write a plausible fifth copy into a scratch tree and prove the detector
    fires on it, and that it does NOT fire on a file that merely imports.
    """
    copy = tmp_path / "a_fifth_copy.py"
    copy.write_text(
        '_ROOTS = (\n'
        '    "srmech.amsc", "srmech.qm", "srmech.signal_processing",\n'
        '    "srmech.introspect", "srmech.profile_loader",\n'
        ')\n', encoding="utf-8")
    assert _COPY_TOKEN.search(copy.read_text(encoding="utf-8")), (
        "the detector missed a hand-written fifth copy — the fifth-copy gate "
        "above is inert.")

    importer = tmp_path / "an_importer.py"
    importer.write_text(
        "from rosetta_roots import ROSETTA_ROOTS\n_ROOTS = ROSETTA_ROOTS\n",
        encoding="utf-8")
    assert not _COPY_TOKEN.search(importer.read_text(encoding="utf-8")), (
        "the detector fires on a file that only IMPORTS the tuple — it would "
        "punish the very fix it asks for.")


def test_all_four_original_consumers_now_resolve_the_canonical_value() -> None:
    """The collapse actually reached all four sites, not just the easy three.

    Imports each consumer the way its own runtime does and compares the value.
    ``notes/_rosetta_inventory.py`` is the interesting one: it is outside the
    package AND outside ``tests/``, so it loads the canonical module by PATH.
    """
    import importlib.util

    from conftest import _ROSETTA_ROOTS as conftest_roots
    from test_rosetta_completeness import _ROOTS as completeness_roots
    from test_rosetta_transitive_standalone import _ROOTS as transitive_roots

    assert conftest_roots == ROSETTA_ROOTS, "conftest.py drifted"
    assert completeness_roots == ROSETTA_ROOTS, "test_rosetta_completeness.py drifted"
    assert transitive_roots == ROSETTA_ROOTS, "transitive-standalone drifted"

    # The out-of-tree consumer. Loaded by path, exactly as it loads its own
    # canonical source, so this proves the path-based single-source path works.
    inv = _SR_ROOT / "notes" / "_rosetta_inventory.py"
    assert inv.is_file(), inv
    spec = importlib.util.spec_from_file_location("_inv_probe", inv)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert tuple(mod.ROOTS) == ROSETTA_ROOTS, (
        "notes/_rosetta_inventory.py resolves a DIFFERENT root set than the "
        f"canonical one:\n  notes: {tuple(mod.ROOTS)}\n  canonical: {ROSETTA_ROOTS}")


def test_the_canonical_module_stays_importable_from_out_of_tree() -> None:
    """It must keep importing NOTHING.

    ``notes/_rosetta_inventory.py`` loads this module by file path, with no
    package context. That works only while the module has no imports to
    resolve. An added ``import pytest`` (or ``import srmech``) would break the
    out-of-tree consumer while every in-tree test stayed green — a silent
    one-way break, so it is asserted here.
    """
    src = (_SR_ROOT / _CANONICAL_REL).read_text(encoding="utf-8")
    code = [ln for ln in src.splitlines()
            if re.match(r"\s*(import|from)\s+\w", ln)]
    assert code == [], (
        f"tests/rosetta_roots.py has grown import statement(s): {code}. It is "
        "loaded BY PATH from notes/_rosetta_inventory.py with no package "
        "context, so it must stay dependency-free.")


def test_the_roots_are_blind_to_ADR0010s_new_namespaces() -> None:
    """⚠️ THE MEASURED GAP, asserted rather than described.

    This is the state rc361 is documenting, not a defect to fix here: the walk
    roots name none of ADR-0010's seven NEW namespaces, so the moment a module
    moves to one of them its ops leave the ledger's denominator.

    ⚠️ AND THE PARTIAL-BLINDNESS CORRECTION. ``srmech.amsc`` and
    ``srmech.introspect`` are ALSO ADR-0010 destinations and ARE already roots,
    so the blindness is partial. Both halves are asserted so neither can be
    misremembered as the whole story.
    """
    present = [ns for ns in _ADR0010_NEW_NAMESPACES if ns in ROSETTA_ROOTS]
    assert not present, (
        f"the walk roots now name {present}, which ADR-0010 lists as NEW "
        "namespaces. rc361 deliberately does NOT pre-widen: a root naming a "
        "package that does not exist is silently skipped by every walker "
        "(import_module raises, the except continues), so pre-adding it would "
        "look like preparation while changing nothing — and would make the "
        "eventual real move indistinguishable from the no-op. Widen the tuple "
        "in the SAME rc that moves the modules.")

    already = [ns for ns in _ADR0010_EXISTING_DESTINATIONS
               if ns in ROSETTA_ROOTS]
    assert already == list(_ADR0010_EXISTING_DESTINATIONS), (
        "an ADR-0010 destination that was already a walk root has left the "
        f"roots: expected {_ADR0010_EXISTING_DESTINATIONS}, found {already}. "
        "The gap is PARTIAL — ops moving to srmech.introspect stay visible — "
        "and that correction is part of the finding.")


def test_a_root_naming_a_nonexistent_package_is_silently_skipped() -> None:
    """⚠️ The mechanism behind the gap, proven rather than asserted from memory.

    The reason a missing root is dangerous (and the reason a PREMATURE root is
    useless) is the same: the walkers swallow the ImportError. If this ever
    started raising, pre-widening would become a safe, self-announcing edit and
    the reasoning above would need revisiting.
    """
    from conftest import rosetta_live_objects

    baseline = rosetta_live_objects()
    assert baseline, "the live-op walk returned nothing — probe is inert"

    import conftest
    saved = conftest._ROSETTA_ROOTS
    try:
        conftest._ROSETTA_ROOTS = saved + ("srmech.apokatastasis",)
        widened = rosetta_live_objects()
    finally:
        conftest._ROSETTA_ROOTS = saved

    assert set(widened) == set(baseline), (
        "adding a root for a package that does not exist CHANGED the live-op "
        "set. That contradicts the rc361 reasoning for not pre-widening the "
        "tuple — re-examine test_rosetta_roots_single_source_rc361's docstring.")
    assert rosetta_live_objects() == baseline, "the probe leaked global state"


def test_the_scan_covers_the_notes_consumer_which_srmech_ci_does_not_watch() -> None:
    """``notes/`` is outside srmech-ci's trigger but inside the ref-guard's.

    The fifth-copy scan reads all of ``docs/srmech`` so it can see a copy
    re-inlined in ``notes/``. That is the rc359 trigger-gap lesson applied
    here: a guard reading a directory no workflow watches is armed and silent.
    This test records that the notes consumer is genuinely in scope, and the
    SCAN_ROOTS meta-test in test_ref_notation_emitted_rc348.py is what checks
    the trigger side.
    """
    scanned = _files_spelling_the_tuple()
    inv = _SR_ROOT / "notes" / "_rosetta_inventory.py"
    assert inv.is_file(), inv
    assert "notes/_rosetta_inventory.py" not in scanned, (
        "notes/_rosetta_inventory.py spells the tuple out again — it must "
        "import the canonical module by path instead.")
    # ...and prove the scan genuinely reaches notes/ rather than stopping at
    # python/, which would make the assertion above vacuous.
    reached = [p for p in _SR_ROOT.rglob("notes/*.py")
               if "__pycache__" not in p.parts]
    assert reached, "the rglob does not reach notes/ at all — scan is too narrow"
