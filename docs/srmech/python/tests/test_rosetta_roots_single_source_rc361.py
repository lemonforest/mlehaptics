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
#:
#: v0.9.0rc362 — ``srmech.music`` APPENDED. This is the two-file edit the
#: assertion below asks for, made for the reason it asks for it: the acoustic
#: slice LANDED in this rc, so the package now EXISTS and the walk must reach
#: it. Widening for a package that does not exist is what rc361 refused; this
#: is the opposite case, and refusing it here would leave the nine
#: ``srmech.music.*`` ops outside the ledger's denominator — the very
#: invisibility ``tests/rosetta_roots.py`` was collapsed to prevent.
_EXPECTED_ROOTS = (
    "srmech.amsc",
    # v0.9.0rc381 (`#T1052`) — RENAMED IN PLACE from "srmech.qm". The ADR-0010
    # physics slice moved the whole qm subpackage under the new srmech.physics
    # DOMAIN (srmech.qm.X -> srmech.physics.qm.X, a whole-subpackage move rather
    # than a flat batch). This is the ONE root that is a rename, not an append:
    # qm was an original compute root, so its successor keeps that slot and the
    # walk recurses srmech.physics -> srmech.physics.qm. srmech.physics leaves
    # _ADR0010_NEW_NAMESPACES for _ADR0010_EXISTING_DESTINATIONS this rc (below),
    # which is the ONLY route out of test_the_roots_are_blind_to_ADR0010s_new_namespaces.
    "srmech.physics",
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
    "srmech.music",
    # v0.9.0rc364 — ``srmech.cascade`` APPENDED. The arc's first execution
    # slice landed the package (the built-in descriptor catalogs), so the same
    # two-file edit is made for the same reason. What is DIFFERENT from the
    # rc362 music case, and worth stating: this root adds ZERO ledger rows,
    # because the namespace holds TOML descriptors and no public callables.
    # It is still the right edit — an existing-but-empty root is a MEASURED
    # zero that can go red when a later slice moves ops in, whereas a missing
    # root would let those ops arrive silently outside the denominator.
    "srmech.cascade",
    # v0.9.0rc370 — ``srmech.apokatastasis`` APPENDED. The two-file edit again,
    # for the reason the assertion below asks for: the elliptic domain LANDED
    # its first module (``elliptic_partial_fraction``) this rc, so the package
    # now EXISTS and the walk must reach it. UNLIKE ``srmech.cascade``, this root
    # adds ONE ledger row (a ``c_dispatched`` op), because it is the first
    # DOMAIN-with-a-registered-op to land — contrast the structure-only cascade
    # slice. Widening for a package that does not exist is what rc361 refused;
    # this is the opposite case.
    "srmech.apokatastasis",
    # v0.9.0rc372 — ``srmech.math`` APPENDED. The two-file edit again: the
    # general-algebra / A-N-primitive domain LANDED its first slice this rc
    # (``octonion`` / ``kepler`` / ``modular_linalg``), so the package now EXISTS
    # and the walk must reach its 10 ops. Like ``srmech.apokatastasis`` and
    # UNLIKE the zero-op ``srmech.cascade``, this root arrives carrying walked
    # rows (7 ``c_dispatched`` + 3 ``composition_of_c``). The domain is only
    # PARTIALLY drained (3 of 22 modules), but package existence is binary — so
    # the root is added on the FIRST module, per the rc370 rule below.
    "srmech.math",
    # v0.9.0rc375 — ``srmech.biology`` APPENDED. The two-file edit again: the
    # biological-substrate domain LANDED its ONLY slice this rc (genome / plasmid /
    # q8 / coupling — the whole 4-module roster in one move), so the package now
    # EXISTS and the walk must reach its ops. Like ``srmech.apokatastasis`` /
    # ``srmech.math`` and UNLIKE the zero-op ``srmech.cascade``, this root arrives
    # carrying walked rows (the genome / q8 / coupling operator surface). Unlike the
    # partially-drained math bucket, biology is FULLY drained by this one slice (4
    # of 4 modules). genome is the arc's single largest C surface; the
    # srmech_genome_* C symbols are capability-named and DO NOT rename (ABI 10).
    "srmech.biology",
    # v0.9.0rc379 (`#T1050`) — srmech.chemistry APPENDED. The two-file
    # edit again, but for a NEW domain rather than an ADR-0010 move: the
    # chemistry namespace is BORN here (reaction networks as exact-integer
    # linear algebra), not migrated from an existing module. Because it is
    # not an ADR-0010 destination it is deliberately absent from both
    # _ADR0010_NEW_NAMESPACES and _ADR0010_EXISTING_DESTINATIONS below; the
    # blindness test asserts the ADR destinations are present and tolerates
    # extra roots, so a non-ADR domain root is correct here and there.
    "srmech.chemistry",
)

#: ADR-0010's destination namespaces that DO NOT EXIST YET.
#:
#: Read off the ADR's own namespace table and its per-destination count table.
#: ``srmech.physics`` / ``srmech.biology`` are now the destinations that have NOT
#: begun to land, and, like ``srmech.external``, are absent from the walk roots.
#: (``srmech.apokatastasis`` — A.2's largest at 31 — LEFT this tuple at rc370;
#: ``srmech.math`` — A.2's second-largest at 22 — LEFT it at rc372; see the notes
#: below.)
#:
#: ⚠️ ``srmech.music`` LEFT THIS TUPLE at v0.9.0rc362 and moved to
#: ``_ADR0010_EXISTING_DESTINATIONS`` below. It is the FIRST of ADR-0010's new
#: namespaces to land, so it is no longer a member of the "does not exist yet"
#: class — leaving it here would have made the gap claim false in the one
#: direction that matters, asserting a blindness the tree no longer has.
#: ⚠️ ``srmech.cascade`` LEFT THIS TUPLE at v0.9.0rc364, by the same one route:
#: the arc's first execution slice landed it. Six namespaces became five.
#: ⚠️ ``srmech.apokatastasis`` LEFT THIS TUPLE at v0.9.0rc370, by that same
#: route: its first module-moving slice (``elliptic_partial_fraction``) landed
#: the package, so it is no longer a "does not exist yet" namespace. The domain
#: is only PARTIALLY drained (1 of 31 modules), but package EXISTENCE is binary —
#: once one module lands, the root exists and the walk must reach it — so the
#: root migrates to ``_ADR0010_EXISTING_DESTINATIONS`` on the FIRST module, not
#: the last.
#: ⚠️ ``srmech.math`` LEFT THIS TUPLE at v0.9.0rc372, by that same route: its
#: first slice (``octonion`` / ``kepler`` / ``modular_linalg``) landed the
#: package. The domain is only PARTIALLY drained (3 of 22 modules), but package
#: existence is binary, so the root migrates on the FIRST slice. Four namespaces
#: became three; ``srmech.physics`` / ``srmech.biology`` / ``srmech.external``
#: are what remain absent.
#: ⚠️ ``srmech.biology`` LEFT THIS TUPLE at v0.9.0rc375, by that same route: its
#: ONLY slice (genome / plasmid / q8 / coupling — the whole 4-module roster) landed
#: the package. Unlike the domains before it, biology is FULLY drained by this one
#: slice, but the migration rule is unchanged (package existence is binary; the root
#: migrates the moment ANY module lands). Three namespaces became two;
#: ``srmech.physics`` / ``srmech.external`` are what remain absent.
#: ⚠️ ``srmech.physics`` LEFT THIS TUPLE at v0.9.0rc381 (`#T1052`), by that same
#: route: the ADR-0010 physics slice moved the whole ``qm`` subpackage under it
#: (``srmech.qm`` -> ``srmech.physics.qm``), so the package now EXISTS and the
#: walk reaches it (``srmech.physics`` is the walk root, recursing into ``qm``).
#: Two namespaces became ONE. ``srmech.external`` is the last ADR-0010
#: destination that has not begun to land — so ``len(_ADR0010_NEW_NAMESPACES)``
#: is now the tamper-proof "arc-complete when 0" oracle (asserted below).
_ADR0010_NEW_NAMESPACES = (
    "srmech.external",
)

#: ADR-0010 destinations that ALREADY EXIST as walk roots.
#:
#: ⚠️ These matter to the honesty of the gap claim. The rc361 brief said the
#: roots contain NONE of ADR-0010's target namespaces; the TREE says otherwise —
#: ``srmech.amsc`` (which KEEPS 4 modules) and ``srmech.introspect`` (which
#: GAINS 10) are both destinations and both are already roots, and ``srmech.dsl``
#: stays put. So the blindness is PARTIAL, not total: ops moving to
#: ``introspect`` stay visible to the walk, ops moving to the six namespaces
#: above do not. Asserted below so the correction cannot be lost.
#:
#: v0.9.0rc362 — ``srmech.music`` joins them, by the ONE route this tuple
#: accepts: the modules landed, so the root was widened in the SAME rc. That is
#: the sequencing rule stated positively rather than as a prohibition.
#:
#: v0.9.0rc364 — ``srmech.cascade`` joins them by the same route. It is the
#: first STRUCTURE home (as opposed to a domain) to land, and the first to
#: arrive carrying zero ops; see the note at ``_EXPECTED_ROOTS``.
#:
#: v0.9.0rc370 — ``srmech.apokatastasis`` joins them by the same route. It is the
#: first DOMAIN-with-a-registered-op to land (contrast cascade's zero-op
#: structure slice), so it arrives carrying exactly one ``c_dispatched`` ledger
#: row; see the note at ``_EXPECTED_ROOTS``.
#:
#: v0.9.0rc372 — ``srmech.math`` joins them by the same route. Its first slice
#: (``octonion`` / ``kepler`` / ``modular_linalg``) arrives carrying 10 walked
#: rows (7 ``c_dispatched`` + 3 ``composition_of_c``); see ``_EXPECTED_ROOTS``.
#:
#: v0.9.0rc375 — ``srmech.biology`` joins them by the same route. Its ONLY slice
#: (genome / plasmid / q8 / coupling — the whole 4-module roster) arrives carrying
#: the genome / q8 / coupling operator surface; see ``_EXPECTED_ROOTS``.
#:
#: v0.9.0rc381 (`#T1052`) — ``srmech.physics`` joins them by the same route. Its
#: slice moved the whole ``qm`` subpackage under it (``srmech.qm`` ->
#: ``srmech.physics.qm``); the walk root is the DOMAIN ``srmech.physics``, which
#: recurses into ``qm`` and its 15 submodules. This is the LAST ADR-0010 DOMAIN
#: to land; only the ``srmech.external`` structure home remains unlanded.
_ADR0010_EXISTING_DESTINATIONS = ("srmech.amsc", "srmech.introspect",
                                  "srmech.dsl", "srmech.music",
                                  "srmech.cascade", "srmech.apokatastasis",
                                  "srmech.math", "srmech.biology",
                                  "srmech.physics")

#: ⚠️ THE UNION-PIN (rc381, `#T1052`). The FIXED full set of ADR-0010 destination
#: namespaces. Every ADR-0010 target is either still-unlanded
#: (``_ADR0010_NEW_NAMESPACES``) or landed (``_ADR0010_EXISTING_DESTINATIONS``),
#: and the two are disjoint — so their UNION must equal this constant AT EVERY rc,
#: forever. Pinning the union (not just each half) closes a hole the two tuples
#: had on their own: before rc381 a name silently DELETED from
#: ``_ADR0010_NEW_NAMESPACES`` — rather than moved to the EXISTING tuple — still
#: passed green (``test_the_roots_are_blind_...`` only checks NEW names are ABSENT
#: from the roots, which a deleted name trivially is). The union pin makes a name
#: able to move ONLY NEW->EXISTING; it can never leave the accounting. Derived
#: from ADR-0010's own namespace table (``docs/srmech/adr/0010-namespace-declustering.md``),
#: the ten destinations are: the SIX that were NEW namespaces at the arc's start
#: and have since landed — music / cascade / apokatastasis / math / biology /
#: physics — plus the THREE pre-existing destinations already serving as roots —
#: amsc / introspect / dsl — plus the ONE still-unlanded structure home, external.
#: This is a CONSTANT: edit it only if ADR-0010 itself gains or drops a
#: destination namespace, never as a side effect of a move.
_ADR0010_ALL_NAMESPACES = frozenset(
    _ADR0010_NEW_NAMESPACES) | frozenset(_ADR0010_EXISTING_DESTINATIONS)

#: The pinned value the union must equal at every rc. A move edits the two source
#: tuples in lockstep and this stays put; a DELETION (name vanishes from NEW
#: without arriving in EXISTING) shrinks the union and fails the pin below.
_ADR0010_ALL_NAMESPACES_PINNED = frozenset({
    "srmech.amsc", "srmech.introspect", "srmech.dsl", "srmech.music",
    "srmech.cascade", "srmech.apokatastasis", "srmech.math", "srmech.biology",
    "srmech.physics", "srmech.external",
})

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
        # rc364: RELATIVE parts, not absolute — an absolute-path test for
        # "worktrees" matches EVERY file when the scan itself runs from a
        # `.claude/worktrees/` checkout, which emptied this scan and made the
        # `_CANONICAL_REL in spelled` non-vacuity assert below the only thing
        # standing between the fifth-copy gate and a silent pass. Same defect,
        # same fix, as tests/test_ref_notation_emitted_rc348.py.
        rel_parts = path.relative_to(_SR_ROOT).parts
        if "__pycache__" in rel_parts or "worktrees" in rel_parts:
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
    roots name none of ADR-0010's UNLANDED namespaces, so the moment a module
    moves to one of them its ops leave the ledger's denominator.

    ⚠️ AND THE PARTIAL-BLINDNESS CORRECTION. ``srmech.amsc`` and
    ``srmech.introspect`` are ALSO ADR-0010 destinations and ARE already roots,
    so the blindness is partial. Both halves are asserted so neither can be
    misremembered as the whole story.

    ⚠️ WHAT rc362 CHANGED, AND WHY IT IS NOT A LOOSENING. ``srmech.music`` was
    in ``_ADR0010_NEW_NAMESPACES`` and is now in
    ``_ADR0010_EXISTING_DESTINATIONS``, because the acoustic slice LANDED. The
    tuple membership tracks a FACT about the tree (does this package exist?),
    not a wish about the arc, and a namespace that has landed belongs in the
    second list by construction. The prohibition rc361 wrote down is unmoved:
    a root may not name a package that does not exist. Seven became six by a
    module move, not by an exemption — and the second assertion below is what
    keeps the migration honest, since a namespace deleted from the first tuple
    without arriving in the second would fail there.
    """
    present = [ns for ns in _ADR0010_NEW_NAMESPACES if ns in ROSETTA_ROOTS]
    assert not present, (
        f"the walk roots now name {present}, which ADR-0010 lists as NEW "
        "namespaces that DO NOT EXIST YET. rc361 deliberately does NOT "
        "pre-widen: a root naming a package that does not exist is silently "
        "skipped by every walker (import_module raises, the except continues), "
        "so pre-adding it would look like preparation while changing nothing — "
        "and would make the eventual real move indistinguishable from the "
        "no-op. Widen the tuple in the SAME rc that moves the modules, and in "
        "that rc move the namespace from _ADR0010_NEW_NAMESPACES to "
        "_ADR0010_EXISTING_DESTINATIONS — that is what rc362 did for "
        "srmech.music, and it is the ONLY route out of this assertion.")

    already = [ns for ns in _ADR0010_EXISTING_DESTINATIONS
               if ns in ROSETTA_ROOTS]
    assert already == list(_ADR0010_EXISTING_DESTINATIONS), (
        "an ADR-0010 destination that was already a walk root has left the "
        f"roots: expected {_ADR0010_EXISTING_DESTINATIONS}, found {already}. "
        "The gap is PARTIAL — ops moving to srmech.introspect stay visible — "
        "and that correction is part of the finding.")


def test_the_ADR0010_namespace_accounting_is_closed() -> None:
    """⚠️ THE UNION-PIN RATCHET (rc381, `#T1052`). A name may move NEW->EXISTING;
    it can never leave the accounting.

    The two ADR-0010 tuples partition the destination namespaces into
    not-yet-landed and landed. On their own, each is blind to a specific silent
    error: ``test_the_roots_are_blind_...`` checks that NEW names are ABSENT from
    the roots and that EXISTING names are PRESENT, but a name simply DELETED from
    ``_ADR0010_NEW_NAMESPACES`` — instead of being moved to the EXISTING tuple —
    is trivially absent from the roots and so passes green while its landing goes
    unrecorded. This closes that hole three ways:

      1. the two tuples are DISJOINT (a name is landed xor unlanded, never both);
      2. their UNION equals the fixed full ADR-0010 destination set — so a name
         cannot vanish from the accounting, only migrate within it;
      3. neither tuple has an internal duplicate.

    The fixed set is a CONSTANT read off ADR-0010's own namespace table; it moves
    only if the ADR itself gains or drops a destination, never as a side effect
    of a module move.
    """
    new = set(_ADR0010_NEW_NAMESPACES)
    existing = set(_ADR0010_EXISTING_DESTINATIONS)

    assert len(new) == len(_ADR0010_NEW_NAMESPACES), "duplicate in NEW tuple"
    assert len(existing) == len(_ADR0010_EXISTING_DESTINATIONS), (
        "duplicate in EXISTING tuple")

    overlap = new & existing
    assert not overlap, (
        f"a namespace is in BOTH ADR-0010 tuples: {sorted(overlap)}. A "
        "destination is either still-unlanded (NEW) or landed (EXISTING), never "
        "both — moving one means DELETING it from NEW in the same edit that "
        "APPENDS it to EXISTING.")

    assert _ADR0010_ALL_NAMESPACES == _ADR0010_ALL_NAMESPACES_PINNED, (
        "the ADR-0010 destination accounting changed.\n"
        f"  NEW  ∪ EXISTING = {sorted(_ADR0010_ALL_NAMESPACES)}\n"
        f"  pinned          = {sorted(_ADR0010_ALL_NAMESPACES_PINNED)}\n"
        f"  missing from the union: "
        f"{sorted(_ADR0010_ALL_NAMESPACES_PINNED - _ADR0010_ALL_NAMESPACES)}\n"
        f"  extra in the union:     "
        f"{sorted(_ADR0010_ALL_NAMESPACES - _ADR0010_ALL_NAMESPACES_PINNED)}\n"
        "A move edits NEW and EXISTING in lockstep and this union stays put. If a "
        "name went MISSING, it was deleted from NEW without being appended to "
        "EXISTING — restore the accounting. Change the PINNED set only if "
        "ADR-0010 itself added or removed a destination namespace.")


def test_the_new_namespace_count_is_the_arc_complete_oracle() -> None:
    """⚠️ ``len(_ADR0010_NEW_NAMESPACES)`` == outstanding ADR-0010 destinations.

    Because the union is pinned (test above), the count of NEW namespaces is a
    tamper-proof measure of what the arc has left to land: every NEW name is a
    real, still-unlanded destination, and the arc is COMPLETE exactly when this
    reaches 0. It cannot be gamed by deleting a name (the union pin catches that)
    nor by adding a spurious one (each NEW name is asserted genuinely absent from
    both the landed tuple and the walk roots).

    At rc381 the physics slice landed the LAST DOMAIN, leaving one structure home
    (``srmech.external``) unlanded — so the oracle reads 1.
    """
    outstanding = len(_ADR0010_NEW_NAMESPACES)
    assert outstanding == 1, (
        f"the ADR-0010 arc has {outstanding} destination namespace(s) still "
        f"unlanded: {sorted(_ADR0010_NEW_NAMESPACES)}. At rc381 exactly one "
        "remains (srmech.external). When a slice lands one, MIGRATE it "
        "NEW->EXISTING (never delete it) and lower this count; the arc is "
        "COMPLETE when it reaches 0.")

    for ns in _ADR0010_NEW_NAMESPACES:
        assert ns not in _ADR0010_EXISTING_DESTINATIONS, (
            f"{ns} is listed as unlanded but also as a landed destination")
        assert ns not in ROSETTA_ROOTS, (
            f"{ns} is listed as unlanded but is already a walk root — an "
            "unlanded namespace must not be walked (a root naming a nonexistent "
            "package is silently skipped; see the next test).")


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
    # ⚠️ v0.9.0rc381 (`#T1052`) — the witness points at ``srmech.external``, the
    # LAST member of ``_ADR0010_NEW_NAMESPACES`` and genuinely without a package
    # dir. (rc372 used ``srmech.physics`` — valid then, but the physics slice
    # LANDED it this rc, so it is no longer a still-nonexistent witness; rotated
    # back to ``srmech.external``, which rc370 already used. Any member of
    # ``_ADR0010_NEW_NAMESPACES`` is a correct still-nonexistent witness for the
    # ImportError-swallow — and there is now exactly one left.)
    try:
        conftest._ROSETTA_ROOTS = saved + ("srmech.external",)
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
