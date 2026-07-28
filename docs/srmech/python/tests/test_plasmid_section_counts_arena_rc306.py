"""v0.9.0rc306 (§102 / task #899) — ``section_counts`` becomes CALLER-ARENA.

rc280 shipped the native ``srmech_genome_section_counts`` scan against THREE file-scope
static scratch buffers: a 32 MiB catalog arena, a 2^18-slot count table and a 64 KiB
window (+ a static distinct-id counter). Two defects rode on that:

  1. **A corpus cap.** The catalog arena is sized by
     ``srmech_genome_arena_bytes(body_len, n_chroms, 0)``, whose per-chromosome term
     (~2.7 KiB) dominates — so the 32 MiB static admitted only **~11,000 chromosomes**.
     A bigger store returned OVERFLOW and silently fell back to the pure body.
  2. **Non-reentrancy.** Four mutable process-globals mean two threads sharing
     ``libsrmech`` corrupt each other's scan — at odds with the reentrant-C-core claim
     (#772).

rc306 converts the op to srmech's own caller-arena pattern (the same one the JSON/TOML
parsers and the CD dimension #933 use): the count table + window are carved off a caller
``ws``, and its untouched TAIL is the catalog arena. No static state remains — the op is
reentrant, and the corpus/id bounds are whatever ``ws`` the caller sizes (via the new
``srmech_genome_section_counts_arena_bytes`` helper). Adding the ``(ws, ws_len)`` params
to the exported signature bumps ``SRMECH_ABI_VERSION`` 8 -> 9. ``GENOME_FORMAT_VERSION``
stays 15 (no on-disk change); the counts stay byte-identical to the pure body.

Proven here:
  * the sizing helper SCALES the catalog term with n_chroms — well past the old 32 MiB
    static (so past the ~11k-section cap) — and scales the count table with out_cap,
    past the old 196,608 distinct-id ceiling;
  * the three statics + their two macros are GONE from the C source (the reentrancy
    proof the task asks for);
  * native == pure byte-for-byte across small AND larger fixtures;
  * the caller-arena retry-grow loop engages (and stays correct) when the initial
    capacity is deliberately tiny — the count table is genuinely caller-sized, not a
    fixed 2^18.

numpy-free; integer/exact (Class-N); no ``abs()``.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tests._native_gate import require_native
from srmech.amsc import _native
from srmech.amsc import plasmid as P
from srmech.amsc.hdc import klein4_expand

_DIM = 64
_OLD_STATIC_ARENA = 32 * 1024 * 1024        # the removed SRMECH_GENOME_SC_ARENA_BYTES
_OLD_ID_CEILING = (1 << 18) // 4 * 3        # the removed 2^18 * 3/4 == 196,608
_C_GENOME = (Path(__file__).resolve().parent.parent.parent
             / "c" / "src" / "srmech_genome.c")


def _one(seed=1280):
    return klein4_expand(_DIM, seed)


def _store(docs, one, **kw):
    d = tempfile.mkdtemp()
    return d, P.plasmid_extract(docs, d, one, **kw)


def _pure_counts(store, one):
    """section_counts with the native peer forced OFF — the byte-parity oracle."""
    real = _native.has_native_genome_section_counts
    _native.has_native_genome_section_counts = lambda: False
    try:
        return P.section_counts(store, coupling=one)
    finally:
        _native.has_native_genome_section_counts = real


def _native_direct(store, one):
    """Call the native caller-arena peer directly (sizing the arena the way
    plasmid.section_counts does) and return ``(counts_dict, cancelled)`` — or ``None``
    if the peer DECLINED. Lets a test assert the native scan actually ran, so a
    native==pure check can never be a silent pure-vs-pure false green."""
    leaf_dim, resolved, entries = P._section_entries(Path(store), one)
    body_len = (Path(store) / P._genome._BODY_NAME).stat().st_size
    res = _native.genome_section_counts_c(
        str(store), P._coupling_block_bytes(resolved), leaf_dim,
        body_len=body_len, n_chroms=len(entries) + 1)
    if res is None:
        return None
    ids, cnts, _done, cancelled = res
    return {int(v): int(c) for v, c in zip(ids, cnts)}, bool(cancelled)


def _arena_bytes(body_len, n_chroms, out_cap):
    import ctypes
    return int(_native.LIB.srmech_genome_section_counts_arena_bytes(
        ctypes.c_size_t(body_len), ctypes.c_uint32(n_chroms), ctypes.c_size_t(out_cap)))


_HAVE_HELPER = (_native.HAS_NATIVE and _native.LIB is not None
                and hasattr(_native.LIB, "srmech_genome_section_counts_arena_bytes"))
_need_helper = pytest.mark.skipif(not _HAVE_HELPER,
                                  reason="native section_counts arena helper not built")


# ── the cap is gone: the arena SCALES ────────────────────────────────────────

@_need_helper
def test_arena_scales_with_n_chroms_past_the_old_32mib_cap():
    """The catalog term scales LINEARLY with n_chroms and blows well past the old
    32 MiB static — i.e. the ~11,000-section cap is gone. A corpus of 100,000
    chromosomes sizes an arena many times the old fixed 32 MiB, and the size is
    strictly monotonic in n_chroms (no plateau at any ceiling)."""
    body = 4096
    sizes = [_arena_bytes(body, n, 1 << 16)
             for n in (1000, 5000, 11000, 20000, 50000, 100000)]
    assert sizes == sorted(sizes) and len(set(sizes)) == len(sizes), (
        f"arena size must strictly grow with n_chroms; got {sizes}")
    # 100k chromosomes: ~100k * ~2.7 KiB catalog >> the old 32 MiB static.
    assert sizes[-1] > 4 * _OLD_STATIC_ARENA, (
        f"100k-chromosome arena {sizes[-1]} did not exceed 4x the old 32 MiB static "
        f"({_OLD_STATIC_ARENA}) — the corpus cap is not actually gone")
    # linear scaling: doubling the chromosome count past the old cap adds a
    # proportional slab, it does not saturate.
    d_10_20 = _arena_bytes(body, 20000, 1 << 16) - _arena_bytes(body, 10000, 1 << 16)
    assert d_10_20 > 10 * 1024 * 1024, (
        f"+10,000 chromosomes added only {d_10_20} bytes — expected a ~27 MB slab")


@_need_helper
def test_count_table_scales_with_out_cap_past_the_old_196k_ceiling():
    """The count table is sized from out_cap, so a caller can census a corpus with far
    more than the old fixed 2^18 * 3/4 == 196,608 distinct ids: growing out_cap from
    ~1k to ~1M enlarges the arena by tens of MB of table (24 B/slot)."""
    body, nchrom = 4096, 100
    small = _arena_bytes(body, nchrom, 1 << 10)
    big = _arena_bytes(body, nchrom, 1 << 20)      # 1,048,576 distinct ids
    assert big - small > 32 * 1024 * 1024, (
        f"the count table did not scale with out_cap (delta {big - small}) — the old "
        f"{_OLD_ID_CEILING}-id ceiling would still be in force")
    assert _arena_bytes(body, nchrom, _OLD_ID_CEILING * 4) > \
        _arena_bytes(body, nchrom, _OLD_ID_CEILING), "table must grow past the old ceiling"


# ── reentrancy: the statics are GONE from the C source ───────────────────────

@pytest.mark.skipif(not _C_GENOME.exists(), reason="C source not in this tree")
def test_the_three_statics_and_two_macros_are_removed_from_the_c_source():
    """The reentrancy proof. The four process-global statics (g_sc_arena, g_sc_slots,
    g_sc_win, g_sc_n_ids) and the two cap macros (SRMECH_GENOME_SC_ARENA_BYTES /
    _HASH_SLOTS) must not survive as declarations/uses — only prose may mention them.
    The function must take a ``void *ws``."""
    src = _C_GENOME.read_text(encoding="utf-8", errors="replace")
    for static in ("static unsigned char g_sc_arena", "static sc_slot_t g_sc_slots",
                   "static unsigned char g_sc_win", "g_sc_n_ids ="):
        assert static not in src, f"a removed section-counts static survives: {static!r}"
    for macro in ("SRMECH_GENOME_SC_ARENA_BYTES", "SRMECH_GENOME_SC_HASH_SLOTS"):
        assert macro not in src, f"a removed section-counts cap macro survives: {macro!r}"
    assert "srmech_genome_section_counts(" in src
    assert "void *ws, size_t ws_len" in src, "the caller-arena params are missing"


# ── native == pure across sizes ──────────────────────────────────────────────

@pytest.mark.parametrize("n_docs,size,stride", [(1, 8, 1), (5, 25, 3), (40, 60, 7),
                                                (120, 90, 11)])
def test_native_equals_pure_across_small_and_large_fixtures(n_docs, size, stride):
    """The counts the caller-arena native scan derives are byte-identical to the pure
    body, from a single section up to a store with many overlapping-vocab sections."""
    require_native("the caller-arena section_counts C peer")
    one = _one()
    words = ["w%04d" % i for i in range(200)]
    docs = [[words[(i * stride + j * 3) % len(words)] for j in range(size)]
            for i in range(n_docs)]
    d, _ext = _store(docs, one)
    pure = _pure_counts(d, one)
    # integration path (P.section_counts dispatches to native) ...
    assert P.section_counts(d, coupling=one) == pure, "section_counts drifted from pure"
    # ... AND the native peer DIRECTLY (proving it ran, not a silent pure fallback).
    direct = _native_direct(d, one)
    assert direct is not None, "native peer DECLINED — the parity check would be pure-vs-pure"
    got, cancelled = direct
    assert not cancelled and got == pure, "native caller-arena counts != pure"
    if n_docs > 1:
        assert max(pure.values()) >= 2, "fixture is degenerate (no shared vocab)"


def test_native_path_is_actually_exercised_not_silently_declining():
    """Guard against a false green: the native branch must run the C peer, not decline
    to pure and compare pure-to-pure."""
    require_native("the section_counts native-path claim")
    assert _native.has_native_genome_section_counts(), (
        "native section_counts not loaded — the parity tests would be pure-vs-pure")


# ── the retry-grow loop: the count table is genuinely caller-sized ───────────

def test_retry_grow_engages_when_the_initial_cap_is_tiny():
    """Forcing the first-attempt capacity to 2 makes the count table + out arrays too
    small on attempt 0, so the caller-arena retry-grow MUST re-size ``ws`` and try
    again — and still land on the exact counts. A fixed 2^18 static table could never
    exercise this path; a genuinely caller-sized one must."""
    require_native("the caller-arena retry-grow loop")
    one = _one()
    words = ["r%04d" % i for i in range(90)]
    docs = [[words[(i * 7 + j) % len(words)] for j in range(40)] for i in range(12)]
    d, _ext = _store(docs, one)
    expected = _pure_counts(d, one)
    assert len(expected) > 2, "fixture must have > 2 distinct ids to force a retry"
    real_cap0 = _native._SECTION_COUNTS_CAP0
    _native._SECTION_COUNTS_CAP0 = 2                 # attempt 0 overflows on purpose
    try:
        direct = _native_direct(d, one)              # the NATIVE peer, not the pure fallback
    finally:
        _native._SECTION_COUNTS_CAP0 = real_cap0
    assert direct is not None, (
        "with cap0=2 the native peer DECLINED instead of growing ws and retrying — "
        "the caller-arena retry-grow is broken (a pure fallback would mask it)")
    grown, cancelled = direct
    assert not cancelled and grown == expected, (
        "the retry-grow loop lost or corrupted counts — caller-arena sizing is broken")


def test_two_disjoint_stores_census_independently():
    """Each scan carves its own ws, so two different stores derive their own counts with
    no cross-call residue (the old shared statics were the reentrancy hazard)."""
    one = _one()
    da, _a = _store([["a", "b", "a"], ["b", "c", "b"]], one)
    db, _b = _store([["x", "y", "z", "x"], ["y", "z", "y"], ["z", "w", "z"]], one)
    ca, cb = P.section_counts(da, coupling=one), P.section_counts(db, coupling=one)
    assert ca == _pure_counts(da, one)
    assert cb == _pure_counts(db, one)
    assert ca != cb, "two different stores must not produce the same histogram"
