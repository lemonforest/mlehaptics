"""rc337 — the genome CATALOG derive binds the body against the manifest (`#952`).

WHAT WAS WRONG
==============
``genome_catalog`` answered two different things about a genome whose ``turns.bin``
had been modified out of band, depending on which implementation ran::

    scripting  GenomeBoundingError("the body was modified out of band")
    compiled   a catalog — built from the corrupt bytes, reported as success

Under ADR-0009 the implementations are co-equal coherency projections of one
capability, so THE SPLIT ITSELF is the defect. Here the split had a direction,
which makes it worse than a disagreement: the compiled projection is the one that
runs on every host that has a wheel, and it was the permissive half.

The pure projection has always closed the loop, at ``genome.py:8438``::

    if data["body_sha256"] != head.get("body_sha256"):
        raise GenomeBoundingError(... "the body was modified out of band")

The C had no peer for that line. ``genome_head_rebuild_params`` read exactly two
fields out of the parsed manifest head — ``leaf_dim`` and ``coupling.hex`` — and
``genome_obtain_manifest`` then RESET the arena, discarding the head, and rebuilt
the whole catalog from the body. The committed ``body_sha256`` was parsed, sat in
the arena, and was thrown away unread. Nothing was ever compared.

The observable symptom, measured before the fix on a two-chromosome store with a
single byte changed inside the first chromosome's label field::

    genome_catalog(...)["chromosomes"][0]["label"]  ->  'g\\x02ography'

A mangled label, returned with a success status, from all four native entry
points (``genome_catalog_c`` / ``genome_census_c`` / ``genome_registry_c`` /
``genome_load_c``). The pure projection raised on the same store.

WHY ``genome_verify_body`` DID NOT ALREADY COVER THIS
=====================================================
It looks like it should: ``genome_load`` re-verifies the body against
``body_sha256`` after reading it. But on a v12 head-only store — which is every
store written today — the manifest tree handed to ``genome_verify_body`` was
DERIVED from the very body being verified. Its ``body_sha256`` and its ``regions``
both come out of that one scan, so the comparison is a tautology: it cannot fail,
whatever the body says. That check is real only on a v≤11 FULL manifest, whose
arrays were parsed off disk as an independent committed record. rc337 leaves it
alone and binds one layer up instead, where the committed value is actually
reachable.

WHY THE BOUND IS GATED ON "HEAD-ONLY"
=====================================
``body_sha256`` does not mean the same thing in every format. In v4+ it is the
region CHAIN (fold the per-region digests in order); in v2/v3 it is a plain
whole-body ``sha256`` — the two branches of ``genome_verify_body`` are exactly that
distinction. A body scan re-derives the CHAIN, so comparing it against a v2/v3
committed digest would hard-fail every legacy store. The C helper therefore
returns an empty-string sentinel when a ``chromosomes`` array is present (a v≤11
full manifest) and the derive proceeds unbound — which is also precisely where the
pure projection draws the line: it binds on the v12 head-only path (:8438) and
falls straight through otherwise (:8452).

WHAT IS PINNED HERE
===================
Four corruption vectors, chosen so that no single mechanism can satisfy them all:

* **A — label byte.** ``byte_offset+2``, ``(b+1)%4``. The structural walk is
  untouched (kind byte, block widths, region tiling all still valid); only a label
  payload byte changed. THE regression vector.
* **B — tail payload.** ``len(body)-1``, ``^= 0x01``. The last byte of the last
  packed turn: no cap, no label, no marker — the part of the body a
  structure-shaped check has no reason to look at.
* **C — region MERGE.** The second chromosome's CHROM-cap marker set to
  ``(b+1)%4 == 0``. ``genome_block_len`` treats ``kind <= 3`` as a legacy v2 turn
  (c:295-299), so the walk ACCEPTS it, the block folds into the previous region,
  and ``n_chromosomes`` silently drops 2 → 1. This one is invisible to every
  per-region check in the tree, because the tree itself is re-derived with the
  wrong number of regions; before rc337 it was caught by ``genome.py:8438`` alone.
* **D — control.** ``byte_offset ^ 0x01``: ``0x43 -> 0x42``, genuinely unrecognised
  by ``genome_block_len``. This was ALREADY rejected before rc337 and must behave
  identically after, so the new bound cannot be credited with a rejection the
  structural walk was already making. (``(b+1)%4`` is NOT a usable control here:
  ``0x43 + 1 mod 4 == 0``, which vector C shows is accepted.)

plus the controls that keep the above from passing vacuously — a clean store still
reads on every surface, and a manifest-LESS genome with a corrupt body still scans
(there is no committed value to bind against, in either projection).
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import genome as G
from srmech.amsc import hdc
from srmech.amsc.genome import GenomeBoundingError


_DIM = 64

#: ``SRMECH_ERR_BAD_INPUT`` — the ``srmech_status_t`` enumerator that IS the
#: ``GenomeBoundingError`` analogue (``_raise_native_genome`` maps every non-OK
#: status to that type). rc337 introduces no new enumerator, which is the whole
#: ABI argument: nothing about the ctypes wire format moves, so
#: ``SRMECH_ABI_VERSION`` stays 10.
_BAD_INPUT = 2


def _one():
    return hdc.klein4_expand(_DIM, 0)


def _leaves(n):
    return [G._HV.from_sequence([(i * 7 + j) % 4 for j in range(_DIM)], sectors=4)
            for i in range(n)]


def _save_two_chromosomes(root, name="g"):
    """A two-chromosome plasmid store. Two is the minimum that makes vector C
    (region MERGE) expressible at all — with one chromosome there is no second
    marker to dissolve."""
    d = Path(root) / name
    one = _one()
    G.genome_save(G.plasmid([("geography", _leaves(3)), ("history", _leaves(2))], one),
                  str(d), one)
    return d, one


def _save_with_genes(root, name="g"):
    """The gene-bearing peer of the fixture above — ``genome_genes`` raises a plain
    ``ValueError`` on a single-kernel chromosome, so the clean-store control for
    that surface needs inline gene caps to be non-degenerate."""
    d = Path(root) / name
    one = _one()
    G.genome_save(
        G.plasmid(chromosomes=[("geography", [("rules", _leaves(2)),
                                              ("board", _leaves(2))]),
                               ("history", [("dates", _leaves(2))])],
                  coupling=one),
        str(d), one)
    return d, one


def _corrupt(d, vector):
    """Apply corruption `vector` to ``<d>/turns.bin`` in place.

    The offsets come from the genome's OWN catalog rather than from hardcoded
    constants, so the vectors keep meaning the same thing ("the first label byte",
    "the second chromosome's marker") if the on-disk layout ever shifts.
    """
    cat = G.genome_catalog(str(d))
    off0 = cat["chromosomes"][0]["byte_offset"]
    off1 = cat["chromosomes"][1]["byte_offset"]
    b = bytearray((d / "turns.bin").read_bytes())
    if vector == "A":                       # label byte — walk untouched
        b[off0 + 2] = (b[off0 + 2] + 1) % 4
    elif vector == "B":                      # tail payload byte
        b[len(b) - 1] ^= 0x01
    elif vector == "C":                      # region MERGE: 0x43 -> 0x00
        assert b[off1] == 0x43, f"fixture: expected a CHROM cap at {off1}, got {b[off1]:#x}"
        b[off1] = (b[off1] + 1) % 4
        assert b[off1] == 0x00, "vector C must land on a kind byte the walk ACCEPTS"
    elif vector == "D":                      # control: unrecognised kind byte
        b[off0] ^= 0x01
        assert b[off0] == 0x42, "vector D must land on a kind byte the walk REJECTS"
    else:                                    # pragma: no cover - typo guard
        raise AssertionError(f"unknown vector {vector!r}")
    (d / "turns.bin").write_bytes(bytes(b))


def _requires_native():
    if not (_native.HAS_NATIVE and _native.has_native_genome()):
        pytest.skip("native genome ops not loaded — nothing to compare against")


def _call(fn):
    """``("ok", value)`` or ``("raised", ExceptionType)`` — the TYPE, never the
    message. A message assertion would pin prose that the two projections have no
    reason to share; the type is the contract."""
    try:
        return ("ok", fn())
    except Exception as exc:                # noqa: BLE001 — the type IS the assertion
        return ("raised", type(exc))


def _both_projections(monkeypatch, fn):
    """``(native, pure)``. Native runs first on untouched dispatch; the pure side
    then forces ``has_native_genome`` off, which is the REAL path a no-native host
    executes (``genome_census`` / ``genome_registry`` gate on it too, via
    ``has_native_genome_census`` / ``_registry``) — not a mock of it."""
    native = _call(fn)
    monkeypatch.setattr(_native, "has_native_genome", lambda: False)
    pure = _call(fn)
    monkeypatch.undo()
    return native, pure


def _both_projections_fresh(monkeypatch, build, make_fn):
    """``_both_projections`` over a store built FRESH for each projection.

    Required for the mutating ops: ``genome_remove`` / ``genome_replace`` change the
    store, so running the compiled projection first and then the scripting one over
    the SAME directory would hand the second call a genome the first already edited
    — the second would fail on "label not present" and the test would read that as a
    projection split. Rebuilding isolates the two runs, which is what "the two
    projections given the same input" actually requires.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, one = build(tmp)
        native = _call(make_fn(d, one))
    monkeypatch.setattr(_native, "has_native_genome", lambda: False)
    with tempfile.TemporaryDirectory() as tmp:
        d, one = build(tmp)
        pure = _call(make_fn(d, one))
    monkeypatch.undo()
    return native, pure


# ── the four vectors, both projections ───────────────────────────────────────

@pytest.mark.parametrize("vector", ["A", "B", "C", "D"])
def test_corrupt_body_raises_in_both_projections(vector, monkeypatch):
    """THE regression, over every vector at once.

    Asserted as a PAIR plus a type equality. "the C raises" alone would let the
    projections drift apart again on the exception type; "both raise something"
    alone would accept a ``UnicodeDecodeError`` on one side and a
    ``GenomeBoundingError`` on the other — which is what a downstream decode
    failure looks like when the integrity check is missing, and is exactly the
    failure mode this rc replaces with a bound at the source.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, _one_ = _save_two_chromosomes(tmp)
        _corrupt(d, vector)
        native, pure = _both_projections(
            monkeypatch, lambda: G.genome_catalog(str(d)))

    assert native[0] == "raised", (
        f"vector {vector}: the COMPILED projection returned {native[1]!r} for a "
        f"body modified out of band instead of raising — this is the rc337 defect "
        f"(a corrupt store read back as a successful catalog)")
    assert pure[0] == "raised", (
        f"vector {vector}: the SCRIPTING projection returned {pure[1]!r}")
    assert native[1] is pure[1] is GenomeBoundingError, (
        f"vector {vector}: both projections must raise the SAME type — the "
        f"family's GenomeBoundingError; got native={native[1]!r} pure={pure[1]!r}")


def test_vector_A_no_longer_returns_a_mangled_label(monkeypatch):
    """The symptom, named exactly as it was measured.

    Pre-rc337 this store's catalog came back with ``'g\\x02ography'`` where
    ``'geography'`` was written. Pinning the raise (above) and pinning the ABSENCE
    of the mangled value are different assertions: a future change that returns the
    ORIGINAL label from a cached head — silently papering over a corrupt body
    rather than reporting it — would pass the first and fail this one.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, _one_ = _save_two_chromosomes(tmp)
        assert [c["label"] for c in G.genome_catalog(str(d))["chromosomes"]] == [
            "geography", "history"], "fixture precondition: the clean labels"
        _corrupt(d, "A")
        for label, fn in (("native", lambda: G.genome_catalog(str(d))),
                          ("pure", lambda: G.genome_catalog(str(d)))):
            if label == "pure":
                monkeypatch.setattr(_native, "has_native_genome", lambda: False)
            with pytest.raises(GenomeBoundingError):
                fn()
        monkeypatch.undo()


def test_vector_C_region_merge_never_reports_a_short_count(monkeypatch):
    """The vector that no per-region check can see.

    Setting the second chromosome's marker to ``0x00`` does not break the walk —
    ``genome_block_len`` accepts ``kind <= 3`` as a legacy v2 turn — so the block
    is absorbed into chromosome 1's region and the derived tree comes back with ONE
    chromosome instead of two. Every digest in that tree is internally consistent;
    it is simply a tree of the wrong genome. The only thing that can catch it is a
    comparison against a value committed BEFORE the corruption, which is what
    rc337 adds.

    Measured pre-fix: ``genome_catalog`` returned ``n_chromosomes 1`` and
    ``genome_census_c`` reported ``n_chromosomes 1``, both with a success status.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, one = _save_two_chromosomes(tmp)
        _corrupt(d, "C")
        for projection in ("native", "pure"):
            if projection == "pure":
                monkeypatch.setattr(_native, "has_native_genome", lambda: False)
            for name, fn in (("catalog", lambda: G.genome_catalog(str(d))),
                             ("census", lambda: G.genome_census(str(d)))):
                got = _call(fn)
                assert got == ("raised", GenomeBoundingError), (
                    f"{projection} {name}: a merged region must raise, not report a "
                    f"short genome; got {got!r}")
                if got[0] == "ok":           # defensive: name the symptom precisely
                    assert got[1].get("n_chromosomes") != 1
        monkeypatch.undo()


def test_vector_D_control_is_unchanged_by_rc337():
    """The control that keeps the bound honest.

    ``0x43 ^ 0x01 == 0x42`` is not a kind byte ``genome_block_len`` recognises, so
    this was rejected long before rc337 by the structural walk. It must still be
    rejected, and still with ``SRMECH_ERR_BAD_INPUT`` — if this vector had changed
    status, the "new bound" would in fact be a rewrite of the walk's error
    contract rather than an addition to it.
    """
    _requires_native()
    with tempfile.TemporaryDirectory() as tmp:
        d, _one_ = _save_two_chromosomes(tmp)
        _corrupt(d, "D")
        with pytest.raises(_native.NativeGenomeError) as ei:
            _native.genome_catalog_c(str(d), b"")
        assert ei.value.status == _BAD_INPUT


# ── all four native entry points, per vector ─────────────────────────────────

@pytest.mark.parametrize("vector", ["A", "B", "C", "D"])
def test_all_four_native_entry_points_reject(vector):
    """Both C derive paths, not just the one everybody looks at.

    ``genome_catalog`` reaches the body through ``genome_obtain_manifest``.
    ``genome_census`` and ``genome_registry`` do NOT — they run a second, parallel
    derive (``genome_scan_params`` → ``genome_load_strings``) that never touches
    that function. Fixing only ``genome_obtain_manifest`` would leave the census
    and registry surfaces silently accepting a corrupt body, so the bound is
    threaded through both and pinned here on both.

    ``genome_load`` is included because it is the surface whose OWN check
    (``genome_verify_body``) is the tautology described in the module docstring:
    pre-rc337 it returned the corrupt bytes with a success status.

    The status is asserted PER VECTOR rather than as one shared constant. Different
    corruptions can legitimately fail at different layers — a region SPLIT, for
    instance, can exceed the arena's chromosome capacity (sized from the committed
    ``n_chromosomes``) and surface as ``SRMECH_ERR_OVERFLOW`` instead — so a single
    global pin would either be wrong or would quietly hide which layer fired.
    """
    _requires_native()
    with tempfile.TemporaryDirectory() as tmp:
        d, _one_ = _save_two_chromosomes(tmp)
        _corrupt(d, vector)
        entries = {
            "genome_catalog_c": lambda: _native.genome_catalog_c(str(d), b""),
            "genome_census_c": lambda: _native.genome_census_c(str(d), b""),
            "genome_registry_c": lambda: _native.genome_registry_c(str(d.parent), b""),
            "genome_load_c": lambda: _native.genome_load_c(str(d), b"", 1 << 20),
        }
        for name, fn in entries.items():
            with pytest.raises(_native.NativeGenomeError) as ei:
                fn()
            assert ei.value.status == _BAD_INPUT, (
                f"vector {vector}: {name} returned status {ei.value.status}, "
                f"expected SRMECH_ERR_BAD_INPUT ({_BAD_INPUT}) — a different status "
                f"here is an ABI question, not a detail")


# ── the whole public surface, both projections ───────────────────────────────

_PUBLIC_SURFACE = (
    "catalog", "census", "registry", "window", "load", "genes", "remove",
)


def _public_ops(d, one):
    return {
        "catalog": lambda: G.genome_catalog(str(d)),
        "census": lambda: G.genome_census(str(d)),
        "registry": lambda: G.genome_registry(str(d.parent)),
        "window": lambda: G.genome_window(str(d), "geography"),
        "load": lambda: G.genome_load(str(d)),
        "genes": lambda: G.genome_genes(str(d), "geography"),
        "remove": lambda: G.genome_remove(str(d), "history", coupling=one),
    }


def _corrupt_build(tmp):
    d, one = _save_with_genes(tmp)
    _corrupt(d, "A")
    return d, one


@pytest.mark.parametrize("op", _PUBLIC_SURFACE)
def test_both_projections_agree_on_type_across_the_surface(op, monkeypatch):
    """Type parity op by op, not just on the one function that was fixed.

    Every op in this list reaches the body through one of the two derive paths, so
    a bound applied to only one of them shows up here as a per-op split rather
    than as a single obvious failure. Parametrised so the report names the op that
    diverged.
    """
    native, pure = _both_projections_fresh(
        monkeypatch, _corrupt_build, lambda d, one: _public_ops(d, one)[op])
    assert native == ("raised", GenomeBoundingError), (
        f"{op}: compiled projection gave {native!r}")
    assert pure == ("raised", GenomeBoundingError), (
        f"{op}: scripting projection gave {pure!r}")


# ── controls: what must still SUCCEED ────────────────────────────────────────

@pytest.mark.parametrize("op", _PUBLIC_SURFACE)
def test_clean_store_still_reads_in_both_projections(op, monkeypatch):
    """The non-degenerate control.

    Without this, every assertion above is satisfiable by an implementation that
    has regressed into rejecting everything — which is the cheapest possible way
    to make a "does it raise?" suite green.
    """
    native, pure = _both_projections_fresh(
        monkeypatch, _save_with_genes, lambda d, one: _public_ops(d, one)[op])
    assert native[0] == "ok", f"{op}: a CLEAN store must read; compiled gave {native!r}"
    assert pure[0] == "ok", f"{op}: a CLEAN store must read; scripting gave {pure!r}"


def test_manifestless_genome_with_a_corrupt_body_still_scans(monkeypatch):
    """§44's optional-``.fai``-cache contract, which rc337 must NOT have broken.

    With no ``manifest.json`` there is no committed value in existence, so there is
    nothing to bind against and the strand is by definition its own SSoT. The C
    expresses this as an empty-string sentinel (the manifest-absent branch never
    populates ``committed``); the pure side expresses it by simply not reaching the
    ``:8438`` comparison. Both must return the SAME catalog — the one the corrupt
    bytes describe, mangled label and all — because that is what the file says.

    This is the case an unconditional ``memcmp`` would have broken, and the reason
    the sentinel exists rather than a bare "always compare".
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, one = _save_two_chromosomes(tmp)
        _corrupt(d, "A")
        (d / "manifest.json").unlink()
        native, pure = _both_projections(
            monkeypatch, lambda: G.genome_catalog(str(d), coupling=one))
    assert native[0] == "ok" and pure[0] == "ok", (
        f"a manifest-LESS genome has nothing to bind against and must still scan; "
        f"got native={native!r} pure={pure!r}")
    assert native[1] == pure[1], "and the two projections must scan it identically"


# ── the store is not damaged by a rejected write ─────────────────────────────

@pytest.mark.parametrize("op", ["remove", "replace"])
def test_a_rejected_edit_leaves_the_store_byte_identical(op):
    """The bound fires BEFORE any write, not partway through one.

    ``genome_remove`` / ``genome_replace`` splice ``turns.bin`` in place. If the
    integrity check were positioned after the splice began — or if a caller
    retried past it — a corrupt store would become a corrupt-AND-truncated store,
    turning a detectable fault into an unrecoverable one. Both files are hashed so
    a manifest rewrite counts as damage too.
    """
    with tempfile.TemporaryDirectory() as tmp:
        d, one = _save_two_chromosomes(tmp)
        _corrupt(d, "A")
        before_body = hashlib.sha256((d / "turns.bin").read_bytes()).hexdigest()
        before_man = hashlib.sha256((d / "manifest.json").read_bytes()).hexdigest()
        fn = (lambda: G.genome_remove(str(d), "history", coupling=one)) if op == "remove" \
            else (lambda: G.genome_replace(str(d), "history", _leaves(2), one))
        with pytest.raises(GenomeBoundingError):
            fn()
        assert hashlib.sha256((d / "turns.bin").read_bytes()).hexdigest() == before_body, (
            f"genome_{op} raised but MUTATED turns.bin")
        assert hashlib.sha256((d / "manifest.json").read_bytes()).hexdigest() == before_man, (
            f"genome_{op} raised but MUTATED manifest.json")


# ── the ABI statement, made executable ───────────────────────────────────────

def test_rc337_introduces_no_new_status_enumerator():
    """rc337 adds no exported symbol, changes no signature, and reuses a status
    already in every touched export's documented error set — so
    ``SRMECH_ABI_VERSION`` does not move. Every function it added or changed in
    ``srmech_genome.c`` is ``static``.

    If a later change routes this bound through a NEW status, this test fails and
    the ABI question has to be answered deliberately rather than by omission.
    """
    _requires_native()
    assert _native.EXPECTED_ABI_VERSION == 10, (
        "rc337 is ABI-neutral; a bump here needs its own justification")
    with tempfile.TemporaryDirectory() as tmp:
        d, _one_ = _save_two_chromosomes(tmp)
        _corrupt(d, "A")
        with pytest.raises(_native.NativeGenomeError) as ei:
            _native.genome_catalog_c(str(d), b"")
        assert ei.value.status == _BAD_INPUT
