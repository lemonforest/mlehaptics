"""rc289 — the ASSERTS-LIVE smoke: documented edge-case inputs, both projections.

WHY THIS MODULE EXISTS
======================
srmech's C library carries ~2 asserts per non-exempt function by JPL Rule 5, and
``tests/test_jpl_audit.py`` ratchets that count down-only. Every shipped build,
and every configuration CI exercised before rc289, compiles ``-DNDEBUG`` — which
strips ``assert`` entirely. So the whole Rule-5 discipline bought **nothing on
any path CI ran**: those asserts were decorative in the only configuration that
executed. A wrong assert could sit in the tree indefinitely and no run would see
it.

rc289 is what that gap cost. ``genome_list_genomes`` asserted ``max_n > 0u``
whenever ``names != NULL``, but the two-pass registry caller legitimately reaches
pass 2 with capacity 0 whenever pass 1 counted no genomes — i.e. on an EMPTY
ROOT, a documented supported input whose docstring promises ``n_genomes: 0``.
Under NDEBUG the code returned the right answer; under an asserts-live build the
process **aborted** (SIGABRT, exit 134). One projection answered correctly while
the other killed the host — the worst shape of ADR-0009 violation, and one a
bare-C host could not even trap. Every CI run was green throughout.

WHAT THIS MODULE IS FOR
=======================
This is the target of the ``asserts-live-smoke`` CI cell
(``.github/workflows/srmech-ci.yml``), which builds the C library WITHOUT
``NDEBUG`` and runs exactly this file. Under a Release build these tests still
pass — they are simply weaker, because there are no asserts left to trip. Their
teeth come from the asserts-live cell. That is the point: the value is in the
BUILD CONFIGURATION, not in the assertions written here.

``test_asserts_are_actually_live`` is the tripwire on the tripwire. The rc289
brief's warning applies with full force — a green result from a build whose
asserts were silently stripped proves nothing at all. When
``SRMECH_ASSERTS_LIVE=1`` is set (the CI cell sets it), that test HARD-FAILS if
the loaded library carries no assert machinery, so a misconfigured cell can
never pass quietly.

SCOPE NOTE — why a targeted smoke and not the full suite under asserts-live.
A full asserts-live run of ``tests/`` was measured for this rc (489 files, each
in its own process so an abort is recorded rather than destroying the session).
It surfaced exactly ONE aborting module, from exactly ONE wrong assert — the one
fixed here. There was no pile of pre-existing aborts to work through, so a second
full ~12-14 min suite in CI would spend the budget to re-prove a null. This file
covers the documented edge-case inputs where a boundary assert is most likely to
be wrong (empty containers, zero counts, zero-length labels, absent paths). If a
future rc has reason to believe the class is broader, widening the cell's
selection is a one-line change to the workflow.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import genome as G
from srmech.amsc import hdc


_DIM = 64


def _one():
    return hdc.klein4_random(_DIM, seed=0)


def _leaves(n):
    return [G._HV.from_sequence([(i * 7 + j) % 4 for j in range(_DIM)], sectors=4)
            for i in range(n)]


def _asserts_live() -> bool:
    """True iff the loaded native library still carries assert machinery.

    Read structurally, not guessed: an ``assert`` that survives compilation emits
    a call to libc ``__assert_fail``, whose name lands in the library's dynamic
    string table. ``-DNDEBUG`` removes every assert, so the reference disappears
    with them. Verified both ways for rc289 against a Debug and a Release build
    of this same source (present / absent respectively), and agreeing with
    ``nm -u``. Returns False when no native library is loaded at all.
    """
    path = _native._find_library()
    if path is None:
        return False
    try:
        return b"__assert_fail" in Path(path).read_bytes()
    except OSError:
        return False


# ── the tripwire on the tripwire ────────────────────────────────────────────

def test_asserts_are_actually_live():
    """Under the asserts-live CI cell, prove the asserts really are live.

    Without this, a build-type flag that silently stopped taking effect would
    turn the entire cell into a very expensive no-op that reports success. The
    env var is what distinguishes "this cell is SUPPOSED to have asserts" from
    an ordinary developer/Release run, where being assert-free is correct.
    """
    if os.environ.get("SRMECH_ASSERTS_LIVE") != "1":
        pytest.skip("not the asserts-live cell (SRMECH_ASSERTS_LIVE unset)")
    assert _native.HAS_NATIVE, (
        "SRMECH_ASSERTS_LIVE=1 but no native library loaded — the cell is not "
        "exercising C at all, so it cannot trip a C assert. Check the build.")
    assert _asserts_live(), (
        "SRMECH_ASSERTS_LIVE=1 but the loaded library has no __assert_fail "
        "reference: it was compiled with NDEBUG and every assert was stripped. "
        "A green run from this build would prove nothing. Check that the "
        "asserts-live cell's build-type override actually reached CMake.")


# ── rc289 regression — the abort, and ADR-0009 agreement on the fixed input ──

def _registry_both_projections(root, monkeypatch):
    """Return (native, pure) registry trees for `root`.

    Native first (untouched dispatch), then the REAL fallback with the native
    registry forced off — the same os/pathlib roll-up a no-native host runs.
    """
    native = G.genome_registry(str(root))
    monkeypatch.setattr(_native, "has_native_genome_registry", lambda: False)
    pure = G.genome_registry(str(root))
    return native, pure


def test_registry_empty_root_does_not_abort_and_projections_agree(monkeypatch):
    """rc289: an EMPTY root is a documented supported input — both projections.

    This is the regression. Against the pre-rc289 tree this test does not FAIL,
    it ABORTS: the C assert kills the interpreter at exit 134 and pytest never
    reports anything. Reaching the assertions below at all is the fix.

    Asserted as an ADR-0009 pair, not merely as "C stopped crashing": the
    scripting projection already returned the right answer, so a test that only
    pinned the compiled one could pass while the two still disagreed.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "empty"
        root.mkdir()
        native, pure = _registry_both_projections(root, monkeypatch)
        expected = {"root": str(root), "n_genomes": 0, "genomes": []}
        assert native == expected
        assert pure == expected
        assert native == pure


def test_registry_root_with_only_non_genome_dirs(monkeypatch):
    """Zero MATCHES from a non-empty scan — the same capacity-0 pass-2 shape.

    Distinct from the empty-root case in the C: the dir iteration actually runs
    and rejects entries, rather than terminating immediately. Both routes land
    on pass 2 with capacity 0, which is what rc289's assert forbade.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "cell"
        root.mkdir()
        (root / "not_a_genome").mkdir()
        (root / "not_a_genome" / "readme.txt").write_text("x", encoding="utf-8")
        (root / "also_not").mkdir()
        native, pure = _registry_both_projections(root, monkeypatch)
        assert native["n_genomes"] == 0
        assert native == pure


def test_registry_populated_root_still_agrees(monkeypatch):
    """The non-zero control, so the two tests above cannot pass by returning
    empty for everything. A capacity-0 fix that broke real scanning would show
    up here rather than hiding behind an all-empty expectation."""
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "cell"
        root.mkdir()
        G.genome_save(G.plasmid([("mt1", _leaves(2))], one), str(root / "aaa"), one)
        G.genome_save(G.plasmid([("mt2", _leaves(3))], one), str(root / "bbb"), one)
        native, pure = _registry_both_projections(root, monkeypatch)
        assert native["n_genomes"] == 2
        assert [Path(g["path"]).name for g in native["genomes"]] == ["aaa", "bbb"]
        assert native == pure


# ── documented edge-case inputs — asserts-live exercise of the boundaries ────
#
# Each of these was probed against an asserts-live build for rc289 and does NOT
# abort. They are here so the asserts-live cell keeps EXECUTING these C
# boundaries: a future wrong assert on a zero count, an empty container or an
# absent path trips here instead of reaching a release.

def test_empty_containers_do_not_abort():
    """Zero-element genome / plasmid — empty is a legal shape at this layer."""
    one = _one()
    assert len(list(G.genome([], one))) == 0
    assert len(list(G.plasmid([], one))) == 0


def test_zero_leaf_and_zero_length_label_do_not_abort():
    """n == 0 leaves, and a zero-length label (a classic wrong-assert target —
    ``label[0] != '\\0'`` is asserted in several C helpers)."""
    one = _one()
    assert len(list(G.chromosome(_leaves(0), one, label="c"))) >= 1
    assert len(list(G.chromosome(_leaves(2), one, label=""))) >= 1


def test_absent_path_declines_cleanly_not_by_aborting():
    """An absent path must DECLINE, not abort. ``genome_census`` /
    ``genome_catalog`` raise ``GenomeBoundingError`` here in both projections.

    Deliberately NOT asserted for ``genome_registry``: that surface has a
    separate, pre-existing ADR-0009 split on an absent root (the compiled
    projection returns ``n_genomes`` 0 while the scripting projection raises
    ``FileNotFoundError``). rc289 fixes the ABORT on that input but does not
    pick a winner between those two behaviours — that is a semantic decision
    with a migration cost, reported rather than settled here. Pinning either
    side in a test would silently make this rc the decision.
    """
    missing = "/nonexistent/srmech/rc289/no/such/root"
    for fn in (G.genome_census, G.genome_catalog):
        with pytest.raises(Exception):
            fn(missing)


def test_zero_node_graph_surfaces_do_not_abort():
    """n == 0 through the graph-shaped genome surfaces.

    ``genome_from_graph`` is asserted non-empty rather than merely "returned":
    a zero-node graph still emits its cap structure, so an empty result would
    mean the surface had silently degenerated rather than handled the boundary.
    """
    one = _one()
    part = G.genome_partition(0, [])
    assert part["n"] == 0
    assert part["n_communities"] >= 1
    assert len(list(G.genome_from_graph(0, [], the_one=one))) > 0
