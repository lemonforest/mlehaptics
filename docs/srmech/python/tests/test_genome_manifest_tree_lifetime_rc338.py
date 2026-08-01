"""rc338 — the derived manifest TREE must not point into a dead stack frame (`#T956`).

THE DEFECT
==========
``genome_obtain_manifest`` (``c/src/srmech_genome.c``) answers the §44 "the strand
is the SSoT" contract: when ``manifest.json`` is absent, or is a v12 HEAD-ONLY head
(which is every store written today), it REBUILDS the full catalog by scanning
``turns.bin``. The scan writes its results into a ``genome_strings_t`` — the block
holding ``body_sha``, ``one_sha``, ``one_hex``, ``rule_hash``, ``descr_hash`` and
``parser_version`` as INLINE ``char`` arrays::

    genome_strings_t rstrs;                        /* <- a STACK local */
    st = genome_fill_strings(&rstrs, &a, body, blen, leaf_dim, one_ptr);
    ...
    return genome_build_manifest_tree(&rstrs, leaf_dim, blen, tws, tws_len,
                                      out, NULL, NULL, 0);

``srmech_json_new_string`` is a BY-REFERENCE constructor — ``srmech_json.c:1279``
is explicit, ``v->u.str.ptr = ptr;   /* not copied — caller keeps bytes alive */``.
So the returned tree, which lives in the caller's arena and is handed back to the
caller to walk and serialise, held six string nodes pointing into
``genome_obtain_manifest``'s own frame. That frame is dead the instant the function
returns. The tree's array-valued fields (``cap_sha[]`` / ``label[]`` /
``region_sha[]``) were always fine — those are arena-carved pointers; it is exactly
the six INLINE members that escaped.

WHY IT SHIPPED AND STAYED GREEN
===============================
Reading through a dangling stack pointer is not a crash; it is whatever the next
call happens to leave at that address. Every caller that serialises the tree
promptly — which is most of them, including ``_native.genome_catalog_c`` — does so
with a call chain shallow enough that the digest bytes were usually still sitting
undisturbed in the abandoned frame. The library was passing on stack-layout luck.

Windows is where the luck ran out. rc337's investigation chased what looked like a
CHAIN drift on MSVC while an instrumented probe proved the stores byte-identical
across platforms; the corruption was never in the DATA, it was in the POINTER, and
MSVC simply lays frames out differently. The wide first cut of rc337 also removed a
``char[4096]`` from that frame, which changed the layout that had been masking it.

WHAT THIS TEST DOES
===================
It stops relying on luck and makes the frame reuse DETERMINISTIC, with the most
faithful scribbler available: a second ``srmech_genome_catalog`` call. Called from
the same Python frame through the same ctypes trampoline, the second call re-enters
``genome_obtain_manifest`` at the identical stack depth, so its ``genome_strings_t``
lands on exactly the bytes the first call's did — and fills them with the SECOND
genome's digests.

The two calls are given SEPARATE arenas (``_native._genome_arena`` hands out one
shared, reused buffer, which would confound the reading by clobbering tree A's
nodes as well). With disjoint arenas the ONLY thing the two calls share is the
stack, so any difference in tree A after call B is, by construction, the lifetime
defect and nothing else.

Measured against the unfixed rc338 build (Linux gcc, Release), tree A's
``data.body_sha256`` after the intervening call read back as genome B's digest, and
``data.coupling.hex`` as genome B's coupling — a fully well-formed manifest
describing the WRONG genome, returned with a success status. That is the shape that
makes this worth an rc: not a crash, not a garbled string, but a plausible answer
about a different object.

WHY NOT JUST RUN ADDRESSSANITIZER
=================================
It was run, and it names the defect exactly — ``c/src/*.c`` + the C smoke built
``-fsanitize=address`` under ``ASAN_OPTIONS=detect_stack_use_after_return=1``
reports, against the pre-fix source::

    ERROR: AddressSanitizer: stack-use-after-return
    Address ... is located in stack of thread T0 at offset 368 in frame
        #0 genome_obtain_manifest srmech_genome.c:3632
        [368, 1240) 'rstrs' (line 3680) <== Memory access ... inside this variable

but it is not a substitute for this file, for two reasons. It needs a sanitizer
build, which no shipped configuration is; and its fake-stack machinery gives every
call its own frame, so under ASan the second call never lands on the first's
storage and the WRONG-GENOME symptom disappears entirely — the redzone poison is
what reports, not the value. The two are complementary. This file pins the
behaviour a user actually gets, in the build a user actually runs.

WHAT IS *NOT* CLAIMED
=====================
This pins the ONE escaping site. ``genome_census_build`` also holds a
``genome_strings_t`` on the stack, but the census tree references only
``s->label[]`` (arena-carved) plus string literals plus an arena-copied path — no
inline member escapes, so it is sound as written. ``genome_save`` and the O(1)
append hold theirs on the stack too and serialise INSIDE the call, before the frame
dies. Those three are covered by :func:`test_census_and_save_paths_are_unaffected`
below, which is a control, not a second regression.
"""

from __future__ import annotations

import ctypes
import json
import os
import tempfile
from pathlib import Path

import pytest

from srmech import _native
from srmech.biology import genome as G
from srmech.math import hdc


_DIM = 64


def _requires_native():
    if not (_native.HAS_NATIVE and _native.has_native_genome()):
        pytest.skip("native genome ops not loaded — there is no C tree to outlive")


def _leaves(n, seed):
    return [G._HV.from_sequence([(i * 7 + j + seed) % 4 for j in range(_DIM)],
                                sectors=4)
            for i in range(n)]


def _save(root, name, seed, labels):
    """A distinct store per seed: a different coupling (so ``coupling.hex`` and
    ``coupling.sha256`` differ) over different content (so ``body_sha256`` differs).
    Both genomes must be head-only v12 stores — that is the branch that REBUILDS."""
    d = Path(root) / name
    one = hdc.klein4_expand(_DIM, seed)
    G.genome_save(
        G.plasmid([(lab, _leaves(2 + i, seed)) for i, lab in enumerate(labels)], one),
        str(d), one)
    head = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    assert "chromosomes" not in head["data"], (
        "fixture precondition: a v12 HEAD-ONLY manifest — a v<=11 full manifest is "
        "returned by the PARSE branch and never reaches the rebuild this pins")
    return d, G._coupling_bytes_or_empty(one)


def _private_arena(d: str, coupling: bytes):
    """An arena sized by the C layout SSoT, private to one call.

    ``_native._genome_arena`` deliberately reuses one shared, growing buffer. That
    is right for the shipping path and wrong here: two calls sharing an arena would
    overwrite tree A's json nodes outright, which is a different (and uninteresting)
    failure than the one under test.
    """
    fn = _native.LIB.srmech_genome_arena_bytes
    fn.restype = ctypes.c_size_t
    fn.argtypes = [ctypes.c_size_t, ctypes.c_uint32, ctypes.c_size_t]
    body_sz = _native._genome_file_size(os.path.join(d, "turns.bin"))
    man_sz = _native._genome_file_size(os.path.join(d, "manifest.json"))
    need = int(fn(ctypes.c_size_t(max(man_sz, body_sz)),
                  ctypes.c_uint32(_native._genome_chrom_count(d, coupling)),
                  ctypes.c_size_t(0)))
    return (ctypes.c_char * need)()


def _catalog_tree(d: str, coupling: bytes):
    """``(tree, arena)`` from ``srmech_genome_catalog`` — the tree WITHOUT the
    serialisation step ``genome_catalog_c`` normally fuses onto it. The arena is
    returned so the caller keeps it alive; the tree lives inside it."""
    arena = _private_arena(d, coupling)
    tree = ctypes.c_void_p()
    rc = _native.LIB.srmech_genome_catalog(
        d.encode("utf-8"), _native._u8(coupling), ctypes.c_size_t(len(coupling)),
        ctypes.cast(arena, ctypes.c_void_p), ctypes.c_size_t(len(arena)),
        ctypes.byref(tree))
    assert rc == 0, f"srmech_genome_catalog({d}) returned {rc}"
    return tree, arena


def _tree_json(tree, d: str) -> dict:
    cap = max(256 * 1024,
              4 * _native._genome_file_size(os.path.join(d, "turns.bin")))
    return json.loads(_native._genome_tree_to_text(tree, cap))


def _pure_catalog(d: Path, monkeypatch) -> dict:
    """The scripting projection's answer — the reference the compiled one owes."""
    monkeypatch.setattr(_native, "has_native_genome", lambda: False)
    try:
        return G.genome_catalog(str(d))
    finally:
        monkeypatch.undo()


# ── THE regression ───────────────────────────────────────────────────────────

def test_derived_tree_survives_a_later_catalog_call(monkeypatch):
    """A rebuilt manifest tree must still describe ITS OWN genome after another
    rebuild has run over the same stack.

    Pre-fix this fails on ``body_sha256`` and ``coupling.hex`` together, both
    reading back as genome B's values: the tree is well-formed, the status is
    success, and the answer is about the wrong genome.
    """
    _requires_native()
    with tempfile.TemporaryDirectory() as tmp:
        d_a, one_a = _save(tmp, "alpha", 0, ["geography", "history"])
        d_b, one_b = _save(tmp, "beta", 1, ["chemistry", "botany", "physics"])
        want_a = _pure_catalog(d_a, monkeypatch)
        want_b = _pure_catalog(d_b, monkeypatch)
        assert want_a["body_sha256"] != want_b["body_sha256"], (
            "fixture precondition: the two genomes must be distinguishable")
        assert want_a["coupling"]["hex"] != want_b["coupling"]["hex"], (
            "fixture precondition: the two couplings must be distinguishable")

        # Call A, then call B — same Python frame, same trampoline, same depth, so
        # B's genome_strings_t lands exactly where A's did. Separate arenas, so the
        # stack is the ONLY thing the two calls share.
        tree_a, _ws_a = _catalog_tree(str(d_a), one_a)
        tree_b, _ws_b = _catalog_tree(str(d_b), one_b)
        got_a = _tree_json(tree_a, str(d_a))["data"]
        got_b = _tree_json(tree_b, str(d_b))["data"]

    assert got_a["body_sha256"] == want_a["body_sha256"], (
        f"#T956: the tree from genome A reported body_sha256="
        f"{got_a['body_sha256']!r} after a second catalog call. Genome A's true "
        f"digest is {want_a['body_sha256']!r}"
        + (f" — the value reported is genome B's ({want_b['body_sha256']!r}), i.e. "
           f"the string node is reading the SECOND call's genome_strings_t out of "
           f"the first call's dead stack frame."
           if got_a["body_sha256"] == want_b["body_sha256"]
           else " — the string node is reading a dead stack frame."))
    assert got_a["coupling"]["hex"] == want_a["coupling"]["hex"], (
        "#T956: the tree from genome A reported the wrong coupling.hex after a "
        "second catalog call — one_hex escaped its frame with body_sha")
    assert got_a["coupling"]["sha256"] == want_a["coupling"]["sha256"], (
        "#T956: coupling.sha256 escaped its frame")
    # B is the LAST writer of that frame, so B alone would pass even unfixed. It is
    # asserted so a "fix" that merely swapped which genome gets corrupted is caught.
    assert got_b["body_sha256"] == want_b["body_sha256"]
    assert got_b["coupling"]["hex"] == want_b["coupling"]["hex"]


def test_derived_tree_matches_the_scripting_projection_in_full(monkeypatch):
    """The whole derived tree, not just the two fields the frame reuse makes most
    legible — ``parser_version`` / ``parser_rule_hash`` /
    ``collector_descriptor_hash`` / ``response_sha256`` are inline members of the
    same block and escape with them (ADR-0009: one capability, co-equal
    projections, so the compiled answer owes the scripting one field-for-field)."""
    _requires_native()
    with tempfile.TemporaryDirectory() as tmp:
        d_a, one_a = _save(tmp, "alpha", 2, ["geography", "history"])
        d_b, one_b = _save(tmp, "beta", 3, ["chemistry", "botany"])
        want = _pure_catalog(d_a, monkeypatch)
        tree_a, _ws_a = _catalog_tree(str(d_a), one_a)
        _tree_b, _ws_b = _catalog_tree(str(d_b), one_b)
        got = _tree_json(tree_a, str(d_a))

    assert got["data"] == want, (
        "#T956: the compiled projection's derived data block diverged from the "
        "scripting projection's after an intervening rebuild")
    att = got["attestation"]
    assert att["response_sha256"] == want["body_sha256"], (
        "#T956: attestation.response_sha256 (the same body_sha buffer) escaped")
    assert att["parser_version"].startswith("srmech "), (
        f"#T956: attestation.parser_version read back as {att['parser_version']!r} "
        f"— the version string escaped its frame")
    for key in ("parser_rule_hash", "collector_descriptor_hash"):
        assert len(att[key]) == 64 and all(c in "0123456789abcdef" for c in att[key]), (
            f"#T956: attestation.{key} read back as {att[key]!r}, not 64 lowercase "
            f"hex — the digest escaped its frame")


def test_three_trees_alive_at_once(monkeypatch):
    """The generalisation: N rebuilt trees held simultaneously must each answer for
    their own genome. Held separately from the two-call case because a fix that
    merely deferred the frame's death by one call would pass that and fail this."""
    _requires_native()
    with tempfile.TemporaryDirectory() as tmp:
        specs = [(0, ["geography", "history"]),
                 (1, ["chemistry", "botany", "physics"]),
                 (2, ["arithmetic"])]
        stores = [_save(tmp, f"g{i}", seed, labels)
                  for i, (seed, labels) in enumerate(specs)]
        want = [_pure_catalog(d, monkeypatch) for d, _one in stores]
        held = [_catalog_tree(str(d), one) for d, one in stores]
        got = [_tree_json(tree, str(d))["data"]
               for (tree, _ws), (d, _one) in zip(held, stores)]

    for i, (g, w) in enumerate(zip(got, want)):
        assert g["body_sha256"] == w["body_sha256"], (
            f"#T956: tree {i} of 3 reported body_sha256={g['body_sha256']!r}, "
            f"expected {w['body_sha256']!r}")
        assert g["coupling"]["hex"] == w["coupling"]["hex"], (
            f"#T956: tree {i} of 3 reported the wrong coupling.hex")


# ── controls — the sites that were already sound, pinned so they stay sound ───

def test_census_and_save_paths_are_unaffected(monkeypatch):
    """``genome_census_build`` keeps its ``genome_strings_t`` on the stack too, and
    that is CORRECT: the census tree references ``s->label[]`` (arena-carved), the
    §96 cap-kind / topology string literals, and an arena-COPIED path — no inline
    member of the block escapes. Pinned as a control so a future edit that adds,
    say, ``body_sha256`` to the census root is caught rather than shipped."""
    _requires_native()
    if not _native.has_native_genome_census():
        pytest.skip("native census not in this build")
    with tempfile.TemporaryDirectory() as tmp:
        d_a, one_a = _save(tmp, "alpha", 4, ["geography", "history"])
        d_b, one_b = _save(tmp, "beta", 5, ["chemistry", "botany", "physics"])
        cen_a = json.loads(_native.genome_census_c(str(d_a), one_a))
        cen_b = json.loads(_native.genome_census_c(str(d_b), one_b))
        pure_a = _pure_catalog(d_a, monkeypatch)

    assert [c["label"] for c in cen_a["chromosomes"]] == ["geography", "history"]
    assert cen_a["n_chromosomes"] == len(pure_a["chromosomes"])
    assert [c["label"] for c in cen_b["chromosomes"]] == [
        "chemistry", "botany", "physics"]


def test_the_shipping_catalog_path_is_correct_for_repeated_reads(monkeypatch):
    """The everyday path (``genome_catalog_c`` — catalog then serialise, on the
    shared arena) over an alternating read sequence. This is the surface a user
    touches; it was USUALLY right before the fix, which is why the defect shipped,
    so it is a control that must be right ALWAYS, not evidence on its own."""
    _requires_native()
    with tempfile.TemporaryDirectory() as tmp:
        d_a, _one_a = _save(tmp, "alpha", 6, ["geography", "history"])
        d_b, _one_b = _save(tmp, "beta", 7, ["chemistry", "botany"])
        want_a = _pure_catalog(d_a, monkeypatch)
        want_b = _pure_catalog(d_b, monkeypatch)
        seq = [G.genome_catalog(str(d)) for d in (d_a, d_b, d_a, d_b, d_a)]

    for i, got in enumerate(seq):
        want = want_a if i % 2 == 0 else want_b
        assert got["body_sha256"] == want["body_sha256"], (
            f"#T956: read {i} of the alternating sequence returned the wrong "
            f"body_sha256")
        assert got["coupling"]["hex"] == want["coupling"]["hex"]
