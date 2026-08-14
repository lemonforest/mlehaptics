"""Filesystem acquisitions that cannot outlive the block that made them (`#T1132`).

WHY THIS MODULE EXISTS — the orphan the raise does not mention
=============================================================
An op that ACQUIRES a resource — creates a directory, opens a file for writing,
takes a handle — **before** it finishes validating leaves that resource behind on
the error path. The raise is loud; the orphaned node is silent. Nothing in the
traceback mentions it, and the next op to touch that path inherits a filesystem
in a state no caller asked for.

That is not hypothetical here. ``genome_save`` did ``path.mkdir(...)`` as the
first statement of its body, above every validation, so a REJECTED save still
left a directory at the target path. ``write_packed_graph`` then did
``open(path, "wb")`` on that same node and died on ``IsADirectoryError``. Both
ops were individually correct; the SUPPLY was wrong. rc431 fixed the supply
(a per-call sandbox slot). rc432 — this module — fixes the acquire-before-
validate sites themselves.

THE ARCHITECTURAL RULING THIS MODULE IS
=======================================
The srmech C library passes all ten Holzmann Power-of-Ten rules, and its error
paths hold zero handle leaks across every held-handle PAL site — by hand-placed
release, with no ``goto cleanup``. The temptation is to port the RULES into
Python. Do not. Port the INVARIANT the rules buy: **every acquisition is
released on every exit.**

Python's native primitive for that invariant is ``with`` / ``try/finally``, and
it is STRICTLY STRONGER than C's hand-placed release, because it cannot be
forgotten at a return statement a later edit adds. ``genome_save``'s mkdir was
precisely an acquisition that had escaped its scope.

The design note worth carrying: in C, **Rule 3 (no malloc) is what made Rule 1
(no goto) survivable** — remove the resource and the cleanup problem mostly
disappears. This module is the same move rather than the same rule: it does not
police where an acquisition may appear, it makes the acquisition OWNED by
something that cannot forget to release it.

⚠️ **Rule 5 (>=2 asserts per function) is deliberately NOT ported.** ``python -O``
deletes asserts, so validation placed in one vanishes in optimized mode — which
is the `#T1131` defect exactly. The transferable principle is the DISTINCTION,
not the count: **assertions are for invariants believed impossible to violate;
``raise`` is for inputs expected to be wrong.**

WHEN NOT TO USE THIS MODULE
===========================
**Do not reach for :func:`created_dirs` where a REORDER suffices.** If moving the
acquisition below the validations is a three-line change, that is the repair —
wrapping such a site in a context manager is complexity for uniformity's sake and
contradicts the ruling above. Five of the eight sites rc432 repaired are plain
reorders and import nothing from here. This module is for the two shapes a
reorder cannot reach: an acquisition that must precede a call which may itself
fail, and a scratch directory whose name the caller never learns.

Stdlib-only and importing NO srmech module, so ``amsc.format``, ``biology.genome``,
``mcp._mcpb`` and ``math.laplacian`` can all import it with no cycle. Peer to
``_json.py`` / ``_toml.py`` / ``_resolve.py`` / ``_handles.py``; the
``@contextlib.contextmanager`` idiom is already native to this tree (see
``genome.py``'s ``_body_handle``).
"""

from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
from typing import Iterator, List

__all__ = ["created_dirs", "owned_scratch_dir"]


def _levels_to_root(path: str) -> List[str]:
    """``path`` and every missing ancestor, SHALLOWEST first.

    Walks up with ``os.path.dirname`` until the parent stops changing (the
    filesystem root, or a bare relative name whose dirname is ``""``). Purely
    lexical — it touches no filesystem, so it cannot race anything. Whether a
    level actually needed creating is decided ATOMICALLY by :func:`created_dirs`,
    by whether ``os.mkdir`` on it succeeded.
    """
    levels: List[str] = []
    cur = os.path.abspath(path)
    while True:
        levels.append(cur)
        parent = os.path.dirname(cur)
        if parent == cur or not parent:
            break
        cur = parent
    levels.reverse()
    return levels


@contextlib.contextmanager
def created_dirs(path) -> Iterator[str]:
    """Create ``path`` and any missing parents; on a raise, remove EXACTLY the
    nodes THIS call created. Pre-existing nodes are never touched.

    The success path is indistinguishable from ``os.makedirs(path,
    exist_ok=True)``: same directories, same permissions, same result when the
    tree already exists — **and the same REJECTIONS**, which points 3 and 4
    below are what buy. Only the ERROR path differs, and that is the point.

    FOUR IMPLEMENTATION POINTS THAT ARE LOAD-BEARING AND MUST NOT BE "SIMPLIFIED"
    ----------------------------------------------------------------------------
    1. **Per-level ``os.mkdir`` in a ``try/except FileExistsError``, NOT
       ``os.makedirs(exist_ok=True)``.** ``exist_ok=True`` cannot report
       created-versus-existed, and a rollback that cannot tell them apart deletes
       the CALLER'S pre-existing directory — strictly worse than the orphan it
       was written to fix. Per-level ``os.mkdir`` learns it atomically from the
       syscall's own result, with no TOCTOU window: if the ``mkdir`` returned, we
       made it; if it raised ``FileExistsError``, we did not.

       (This is the exact blindness that defers the C half of the same repair:
       ``srmech_plat_mkdir`` maps ``EEXIST`` to ``SRMECH_OK`` deliberately, so C
       cannot make this distinction without a new symbol. See `#T1133`.)

    2. **Roll back with ``os.rmdir``, DEEPEST-FIRST, each in
       ``try/except OSError: pass``.** ``os.rmdir`` fails on a non-empty
       directory, and that is the fail-safe rather than a limitation: this helper
       NEVER deletes content. If the body wrote something into a directory we
       created and then raised, the write is evidence and it survives. Swallowing
       the rollback error is mandatory — a rollback failure must not replace, or
       chain onto, the original exception the caller needs to see.

    3. **``FileExistsError`` is only "already done" when the node is a
       DIRECTORY.** rc432 shipped a bare ``except FileExistsError: continue``,
       and it was WRONG in a way that matters here more than anywhere: given a
       path that already exists as a FILE, it swallowed the error and yielded,
       so the caller received a path it believed was a directory and was not
       (measured: ``isdir=False, isfile=True``, where ``os.makedirs(exist_ok=
       True)`` raises). That is rc431's own defect class INVERTED — rc431 was a
       directory found where a file was wanted; this was a file accepted where a
       directory was promised — re-introduced by the helper written to close it.
       An ``isdir`` re-check costs one syscall and restores makedirs parity.

    4. **A non-``EEXIST`` ``OSError`` is tolerated ONLY if the level is already
       the directory we wanted.** On Windows :func:`_levels_to_root` always
       reaches the drive root, and ``os.mkdir("C:\\\\")`` raises
       ``PermissionError [WinError 5]``, NOT ``FileExistsError`` — so the rc432
       build shipped a helper that failed on EVERY absolute path on Windows, and
       with it ``genome_register_attested`` and native ``genome_import``. POSIX
       hid it completely, because ``os.mkdir("/")`` there raises
       ``FileExistsError`` like any other existing directory. A cross-platform
       existence check cannot be spelled with an exception TYPE.

    ⚠️ **The rollback stays exact, and this is the invariant to preserve if these
    clauses are ever touched:** a level joins ``made`` only when its ``os.mkdir``
    RETURNED. The ``isdir`` probes added by points 3 and 4 decide raise-versus-
    continue and NOTHING else, so they can never enrol a pre-existing directory
    for deletion. Point 1's atomicity argument is about what we DELETE, and it is
    untouched.

    Yields the absolute path as a ``str``.
    """
    made: List[str] = []
    try:
        for level in _levels_to_root(os.fspath(path)):
            try:
                os.mkdir(level)
            except FileExistsError:
                # The node is there. It is only "already done" if it is a
                # DIRECTORY — see point 3.
                if not os.path.isdir(level):
                    raise
                continue
            except OSError:
                # Point 4: a level that exists but refuses mkdir for a reason
                # other than EEXIST. Tolerated ONLY when it is already the
                # directory we wanted; any other OSError is the caller's to see.
                if os.path.isdir(level):
                    continue
                raise
            made.append(level)
        yield os.path.abspath(os.fspath(path))
    except BaseException:
        for level in reversed(made):
            try:
                os.rmdir(level)
            except OSError:
                pass
        raise


@contextlib.contextmanager
def owned_scratch_dir(prefix: str) -> Iterator[str]:
    """``mkdtemp`` a scratch directory and remove it on ANY exception.

    For the shape where the acquisition's NAME is minted inside the op and
    reaches the caller only through a return value — so when the op raises, the
    caller is handed an orphan it cannot even name, let alone clean up. That is
    strictly worse than a caller-named directory left behind, because there is no
    party who could ever remove it.

    Recursive delete (``shutil.rmtree``) is justified HERE AND ONLY HERE, and the
    three conditions are worth stating because they are what make it safe: we
    minted the name, the directory was empty when we made it, and everything
    inside it was written by the body of this ``with``. None of the three holds
    for a caller-supplied path, which is why :func:`created_dirs` uses ``rmdir``
    and refuses to delete content.

    Catches ``BaseException`` rather than ``Exception`` on purpose: a
    ``KeyboardInterrupt`` through a long cut is exactly the case that leaves an
    unnameable orphan, and it is not an ``Exception``.

    Yields the scratch directory path as a ``str``.
    """
    scratch = tempfile.mkdtemp(prefix=prefix)
    try:
        yield scratch
    except BaseException:
        shutil.rmtree(scratch, ignore_errors=True)
        raise
