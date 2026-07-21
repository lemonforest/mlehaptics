"""rc294 — an unopenable registry ROOT is an ERROR in BOTH projections (`#924`).

WHAT WAS WRONG
==============
``genome_registry`` answered two different things on a root that cannot be
opened, depending on which implementation ran::

    scripting  Path(root).iterdir()  -> FileNotFoundError
    compiled   n_genomes: 0,           SRMECH_OK

Under ADR-0009 the implementations are co-equal coherency projections of one
capability, so THE SPLIT ITSELF is the defect — there is no "the C is wrong" or
"the Python is wrong" reading available, only "these do not agree".

The deciding fact was in ``c/src/srmech_genome.c``::

    if (st != SRMECH_OK) { *count = 0u; return SRMECH_OK; }   /* no root -> none */

The comment claims "no root". The code means "ANY failure". Every
``srmech_plat_dir_open`` failure became "0 genomes, success": absent path,
permission denied, path-is-a-file, I/O error alike. A caller who typo'd a corpus
path was told — with a success status — that their corpus was empty. That is the
worst available failure mode for this surface: not a crash, not a wrong number,
but a confident zero.

Three further reasons it was the C that had to move, not the Python:

* SIBLING CONTRACT — ``genome_census`` on an absent path already raises
  (``GenomeBoundingError``). ``genome_registry`` was the outlier in its own
  family, which is pinned below by :func:`test_registry_now_matches_its_family`.
* THE DOCSTRING NEVER SANCTIONED IT — it promises "A dir with no genome subdirs
  yields ``n_genomes`` 0". That is an EMPTY dir. It says nothing about an absent
  one, and rc294 leaves the empty-dir contract exactly as it was.
* NO TEST EVER BLESSED IT — rc289 met this split head-on and deliberately
  declined to pin either side (see the note it left in
  ``test_asserts_live_smoke_rc289.py``), precisely so that pinning it could not
  happen by accident. rc294 is the rc that settles it, so that note is now
  discharged rather than deleted.

WHY THE FIX IS NOT ``return st``
================================
A bare propagation would have made the EMPTY-ROOT contract hostage to how each
platform reports an empty directory, and Windows genuinely differs: ``opendir``
distinguishes "opened but empty" from "could not open" natively, while
``FindFirstFile`` signals an empty match set with ``ERROR_FILE_NOT_FOUND``,
indistinguishable at that layer from a failure to open. Most Windows volumes
hand back "." and ".." so the wildcard always matches — but a FAT/exFAT ROOT
directory has no such entries, and an empty root there would have started
erroring. That would have traded an ADR-0009 split along a LANGUAGE seam for a
fresh one along a PLATFORM seam.

So the distinction is drawn in the PAL, where the knowledge lives:
``srmech_plat_dir_open`` now returns SRMECH_OK plus an EXHAUSTED iterator for
"opened, no entries" on every backend, and non-OK strictly means "could not
open". The empty-root cases below are the regression test for that half.

WHAT IS PINNED HERE
===================
Both halves, in both projections, because either one alone can pass while the
capability is still broken:

* an UNOPENABLE root ERRORS — absent, not-a-directory, permission denied — and
  errors as the SAME exception type on both sides (a shared "it raised" with
  divergent types is the same defect one layer in);
* an EMPTY root still yields ``n_genomes`` 0 — byte-identically across the two
  projections, extending the rc289 empty-root parity pin to its companion case;
* a POPULATED root still censuses, so none of the above can pass by having
  degenerated into "error on everything" or "empty for everything".
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import genome as G
from srmech.amsc import hdc
from srmech.amsc.genome import GenomeBoundingError


# ── helpers (the rc289 fixtures, same shapes so the two files stay comparable) ─

_DIM = 64


def _one():
    return hdc.klein4_expand(_DIM, 0)


def _leaves(n):
    return [G._HV.from_sequence([(i * 7 + j) % 4 for j in range(_DIM)], sectors=4)
            for i in range(n)]


def _both_projections(root, monkeypatch):
    """``(native_result, pure_result)`` where each is ``("ok", tree)`` or
    ``("raised", ExceptionType)``.

    Native runs first on untouched dispatch; the pure side then forces the
    native registry off, which is the REAL fallback a no-native host executes —
    not a mock of it.
    """
    def call():
        try:
            return ("ok", G.genome_registry(str(root)))
        except Exception as exc:            # noqa: BLE001 — the type IS the assertion
            return ("raised", type(exc))

    native = call()
    monkeypatch.setattr(_native, "has_native_genome_registry", lambda: False)
    pure = call()
    return native, pure


def _requires_native_registry():
    if not (_native.HAS_NATIVE and _native.has_native_genome_registry()):
        pytest.skip("native genome_registry not loaded — nothing to compare against")


# ── the unopenable-root half ─────────────────────────────────────────────────

def test_absent_root_errors_in_both_projections(monkeypatch):
    """THE regression. Pre-rc294 the native half returned ``n_genomes: 0`` with a
    success status here while the pure half raised — the ADR-0009 split.

    Asserted as a PAIR plus a type equality. Pinning only "the C raises" would
    let the projections drift apart again on the exception type, and pinning only
    "both raise something" would accept ``FileNotFoundError`` on one side and
    ``GenomeBoundingError`` on the other.
    """
    missing = str(Path(tempfile.gettempdir()) / "srmech_rc294_no_such_root_ever")
    assert not Path(missing).exists(), "fixture precondition: the path must be absent"

    native, pure = _both_projections(missing, monkeypatch)

    assert native[0] == "raised", (
        f"the COMPILED projection returned {native[1]!r} for an absent root "
        f"instead of raising — this is exactly the rc294 defect (a typo'd corpus "
        f"path reported as an empty corpus, with a success status)")
    assert pure[0] == "raised", (
        f"the SCRIPTING projection returned {pure[1]!r} for an absent root")
    assert native[1] is pure[1] is GenomeBoundingError, (
        f"both projections must raise the SAME type — the family's "
        f"GenomeBoundingError; got native={native[1]!r} pure={pure[1]!r}")


def test_root_that_is_a_file_errors_in_both_projections(monkeypatch):
    """A path that EXISTS but is not a directory.

    Distinct from the absent case in the C: ``opendir`` fails with ENOTDIR
    rather than ENOENT, and Win32 with ERROR_DIRECTORY (267) rather than
    ERROR_PATH_NOT_FOUND — different errno, same required verdict. The old
    swallow flattened every one of these into "0 genomes, success".
    """
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "not_a_directory.txt"
        f.write_text("x", encoding="utf-8")
        native, pure = _both_projections(f, monkeypatch)
        assert native[0] == "raised" and pure[0] == "raised", (
            f"a file-as-root must ERROR in both projections; "
            f"got native={native!r} pure={pure!r}")
        assert native[1] is pure[1] is GenomeBoundingError


@pytest.mark.skipif(sys.platform == "win32",
                    reason="POSIX mode bits; Windows ACLs do not deny a dir open this way")
def test_unreadable_root_errors_in_both_projections(monkeypatch):
    """Permission denied — the case that most deserves an error and was most
    dangerous as a silent zero, because the directory genuinely exists and may
    genuinely be full of genomes the caller simply cannot see."""
    if os.geteuid() == 0:
        pytest.skip("running as root: mode 0o000 does not deny access")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "unreadable"
        d.mkdir()
        os.chmod(d, 0o000)
        try:
            native, pure = _both_projections(d, monkeypatch)
        finally:
            os.chmod(d, 0o755)            # so the TemporaryDirectory can clean up
        assert native[0] == "raised" and pure[0] == "raised", (
            f"an unreadable root must ERROR in both projections; "
            f"got native={native!r} pure={pure!r}")
        assert native[1] is pure[1] is GenomeBoundingError


def test_registry_now_matches_its_family(monkeypatch):
    """The SIBLING-CONTRACT reason, asserted rather than asserted-in-prose.

    ``genome_census`` and ``genome_catalog`` already raised on an unopenable
    path; ``genome_registry`` did not. This pins the family agreeing, so a future
    change that re-splits ``genome_registry`` away from its siblings fails here
    with the reason attached — and so does one that quietly relaxes a SIBLING to
    match the old registry behaviour instead.
    """
    missing = str(Path(tempfile.gettempdir()) / "srmech_rc294_no_such_root_ever")
    for fn in (G.genome_census, G.genome_catalog, G.genome_registry):
        with pytest.raises(GenomeBoundingError):
            fn(missing)


# ── the empty-root half: unchanged, and pinned so it STAYS unchanged ──────────

def test_empty_root_still_yields_zero_in_both_projections(monkeypatch):
    """The contract rc294 must NOT have broken.

    ``n_genomes`` 0 was always the promise for an EMPTY dir, and the whole point
    of routing the fix through the PAL rather than propagating the status was to
    keep this true on every backend. Byte-identity via ``json.dumps`` (not just
    ``==``) so the two trees agree on serialised form, matching how rc289 pinned
    the same root.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "empty"
        root.mkdir()
        native, pure = _both_projections(root, monkeypatch)
        expected = {"root": str(root), "n_genomes": 0, "genomes": []}
        assert native == ("ok", expected), (
            f"an EMPTY root must still census as n_genomes 0; got {native!r}")
        assert pure == ("ok", expected), (
            f"an EMPTY root must still census as n_genomes 0; got {pure!r}")
        assert (json.dumps(native[1], sort_keys=True)
                == json.dumps(pure[1], sort_keys=True))


def test_root_with_only_non_genome_dirs_still_yields_zero(monkeypatch):
    """Zero MATCHES from a scan that actually RAN — the other route to 0.

    Separate from the empty root in the C: the iteration loop executes and
    rejects entries, rather than falling out immediately. A fix that erroneously
    keyed "0 genomes" off "the directory was empty" would pass the test above
    and fail this one.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "cell"
        root.mkdir()
        (root / "not_a_genome").mkdir()
        (root / "not_a_genome" / "readme.txt").write_text("x", encoding="utf-8")
        (root / "also_not").mkdir()
        native, pure = _both_projections(root, monkeypatch)
        assert native[0] == "ok" and native[1]["n_genomes"] == 0
        assert native[1] == pure[1]


def test_populated_root_still_censuses(monkeypatch):
    """The non-degenerate control.

    Without this, every assertion above could be satisfied by a registry that
    had regressed into raising on everything, or into reporting every root as
    empty. This is the test that makes the others mean something.
    """
    _requires_native_registry()
    one = _one()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "cell"
        root.mkdir()
        G.genome_save(G.plasmid([("mt1", _leaves(2))], one), str(root / "aaa"), one)
        G.genome_save(G.plasmid([("mt2", _leaves(3))], one), str(root / "bbb"), one)
        native, pure = _both_projections(root, monkeypatch)
        assert native[0] == "ok" and pure[0] == "ok"
        assert native[1]["n_genomes"] == 2
        assert [Path(g["path"]).name for g in native[1]["genomes"]] == ["aaa", "bbb"]
        assert native[1] == pure[1]


# ── the C-level status, so a bare-C host's contract is pinned too ────────────

def test_native_status_is_io_not_a_new_enumerator():
    """The compiled projection must report SRMECH_ERR_IO (3) — a status ALREADY
    in this export's documented error set.

    This is the ABI argument made executable. rc294 introduces no new
    ``srmech_status_t`` enumerator and changes no signature, so the ctypes wire
    format is untouched and ``SRMECH_ABI_VERSION`` does not move. If a later
    change routes this through a NEW status, this test fails and the ABI
    question has to be re-answered deliberately rather than by omission.
    """
    _requires_native_registry()
    missing = str(Path(tempfile.gettempdir()) / "srmech_rc294_no_such_root_ever")
    with pytest.raises(_native.NativeGenomeError) as ei:
        _native.genome_registry_c(missing, b"")
    assert ei.value.status == 3, (
        f"expected SRMECH_ERR_IO (3) for an unopenable root; got "
        f"{ei.value.status} — a different status here is an ABI question")
