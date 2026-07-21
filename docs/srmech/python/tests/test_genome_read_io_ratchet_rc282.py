"""v0.9.0rc282 (§102 / F1253) — the genome READ-PATH I/O ratchet.

rc280 made ``section_counts`` read only the ``node_ids`` prefix of each section. It
fixed the ASYMPTOTICS and left a **syscall constant** behind, and the constant is the
whole cost at field-store scale:

* :func:`genome._read_region_prefix` opened ``turns.bin`` on **every call**, and
  :func:`genome._section_node_ids` calls it in a growth loop → a measured **2.0 opens
  per section** (401 opens for 200 sections), i.e. ~481,762 opens extrapolated to the
  240,881-section field store. **The fast path was the slow path.**
* :func:`genome._catalog_data`, on the v12+ HEAD-ONLY branch — the branch EVERY store
  written today takes — did ``turns.bin.read_bytes()``: the entire body resident at
  once, just to derive a catalog that is one forward pass.

**Why this file exists at all.** Both defects sat under comments asserting the
opposite ("the manifest read — never opens turns.bin", on a line whose catalog read
does exactly that). *A comment claiming a performance property is not a test*, which
is precisely how they survived review. So the property is pinned MECHANICALLY here, as
a **down-only ratchet** in the style of the JPL / Rosetta / wire-glue ratchets: the
ceilings below may only ever be LOWERED.

What is pinned:
  * opens of ``turns.bin`` do **not grow with section count** over a 4-point sweep —
    the O(P)-opens shape cannot come back;
  * the catalog read performs **zero** whole-body slurps;
  * the streamed catalog is **byte-identical** to the whole-body-slurp catalog it
    replaced (the equivalence that makes this purely an I/O change);
  * the counts are unchanged end-to-end.

numpy-free; integer/exact (Class-N); no ``abs()``.
"""
from __future__ import annotations

import builtins
import pathlib
import tempfile

import pytest

from srmech.amsc import _native
from srmech.amsc import genome as G
from srmech.amsc import plasmid as P
from srmech.amsc.hdc import klein4_expand

_DIM = 64                                           # >= 52 (the §89 kernel header)

# ── THE RATCHET CEILINGS — down-only ─────────────────────────────────────────
#
# Measured on the rc282 implementation. A change that LOWERS either number should
# lower the ceiling in the same commit; a change that RAISES one is the regression
# this file exists to catch, and must not be "fixed" by raising the ceiling.
#
#   rc280 (the defect):  CEIL_BODY_OPENS_PER_SCAN grew as 2P + 1  (401 at P = 200)
#   rc282 (now):         constant, independent of P
#
#: Total opens of ``turns.bin`` for ONE whole ``section_counts`` scan, ANY P.
#: rc282 measures 2 (one for the catalog derivation, one held across the scan).
CEIL_BODY_OPENS_PER_SCAN = 2

#: Whole-body ``read_bytes()`` slurps while deriving a catalog. rc282 measures 0.
CEIL_BODY_SLURPS_PER_CATALOG = 0

#: The sweep. At least 4 points, spanning an 8x range, so "does not grow with P" is
#: a real observation and not two coincidences.
_SWEEP = (25, 50, 100, 200)


# ── instrumentation ──────────────────────────────────────────────────────────

class _BodyIOTally:
    """Counts opens + whole-body slurps of ``turns.bin``.

    Wraps ``builtins.open``, ``pathlib.Path.open`` AND ``pathlib.Path.read_bytes``,
    because genome.py reaches the body through all three seams — instrumenting only
    one would let a regression through the others, which is exactly the kind of gap
    that let the original defect ship."""

    def __init__(self):
        self.opens = 0
        self.slurps = 0
        self._open = builtins.open
        self._path_open = pathlib.Path.open
        self._read_bytes = pathlib.Path.read_bytes

    def _is_body(self, name):
        return str(name).replace("\\", "/").endswith("/" + G._BODY_NAME)

    def __enter__(self):
        tally = self

        def open_(file, *a, **kw):
            if tally._is_body(file):
                tally.opens += 1
            return tally._open(file, *a, **kw)

        def path_open(self_, *a, **kw):
            if tally._is_body(self_):
                tally.opens += 1
            return tally._path_open(self_, *a, **kw)

        def read_bytes(self_):
            if tally._is_body(self_):
                tally.slurps += 1
            return tally._read_bytes(self_)

        builtins.open = open_
        pathlib.Path.open = path_open
        pathlib.Path.read_bytes = read_bytes
        return self

    def __exit__(self, *exc):
        builtins.open = self._open
        pathlib.Path.open = self._path_open
        pathlib.Path.read_bytes = self._read_bytes
        return False


# ── fixtures ─────────────────────────────────────────────────────────────────

def _one(seed=1282):
    return klein4_expand(_DIM, seed)


def _store(n_sections, one, doc_len=40, vocab=400, window=2):
    """A plasmid section store with ``n_sections`` sections over an overlapping
    vocabulary — the same fixture shape the rc282 cost probe measures
    (``notes/rc282_genome_read_io_probe.py``)."""
    docs = [[f"w{(d * 17 + i * 5) % vocab}" for i in range(doc_len)]
            for d in range(n_sections)]
    d = tempfile.mkdtemp(prefix="rc282_")
    P.plasmid_extract(docs, d, one, window=window, k=8)
    return d


@pytest.fixture(scope="module")
def pure_only():
    """Force the PURE path — this ratchet is about the scripting projection's I/O.
    (The compiled projection's own open shape is a separate, C-side concern.)"""
    real = _native.has_native_genome_section_counts
    _native.has_native_genome_section_counts = lambda: False
    yield
    _native.has_native_genome_section_counts = real


# ── THE RATCHET ──────────────────────────────────────────────────────────────

def test_body_opens_do_not_grow_with_section_count(pure_only):
    """**The load-bearing assertion.** Opens of ``turns.bin`` per ``section_counts``
    scan must be CONSTANT in P. Under rc280 this was ``2P + 1`` — 401 opens at P=200,
    ~481,762 extrapolated to the field store — while the code claimed to be the
    "targeted" fast read.

    Asserted on the syscall COUNT, not on wall-clock: the count is exact, portable and
    has no variance, whereas the time it costs is platform-dependent (on the machine
    that measured this rc the 200-section targeted read was ~0.78x a full sequential
    decode, not the 1.8x measured on the `#876` probe's host — same defect, different
    I/O economics). The count is the invariant; the seconds are not."""
    one = _one()
    observed = {}
    for n in _SWEEP:
        store = _store(n, one)
        with _BodyIOTally() as tally:
            P.section_counts(store, coupling=one)
        observed[n] = tally.opens

    assert max(observed.values()) <= CEIL_BODY_OPENS_PER_SCAN, (
        f"section_counts opened {G._BODY_NAME} more than the "
        f"CEIL_BODY_OPENS_PER_SCAN={CEIL_BODY_OPENS_PER_SCAN} ratchet allows: "
        f"{observed}. This ceiling is DOWN-ONLY — if the extra opens are genuinely "
        f"necessary, that is a design regression to fix, not a ceiling to raise.")

    # The shape claim, stated independently of the absolute ceiling: an 8x growth in P
    # must not grow the open count AT ALL.
    assert observed[_SWEEP[-1]] <= observed[_SWEEP[0]], (
        f"opens GREW with section count ({observed}) — the O(P)-opens shape rc282 "
        f"removed has come back. _read_region_prefix / _section_node_ids must page "
        f"through a HELD handle, not open the body per call.")


def test_catalog_derivation_never_slurps_the_whole_body(pure_only):
    """``_catalog_data`` on the v12+ HEAD-ONLY branch — the branch every store written
    today takes — must DERIVE the catalog by streaming, never by holding the entire
    body in RAM. Pinned as a ratchet because the slurp was invisible: it sat one line
    below a docstring bullet about the O(1) head."""
    one = _one()
    for n in _SWEEP:
        store = _store(n, one)
        with _BodyIOTally() as tally:
            data = G._catalog_data(pathlib.Path(store), one)
        assert tally.slurps <= CEIL_BODY_SLURPS_PER_CATALOG, (
            f"deriving the catalog for a {n}-section store slurped {G._BODY_NAME} "
            f"whole {tally.slurps} time(s); CEIL_BODY_SLURPS_PER_CATALOG="
            f"{CEIL_BODY_SLURPS_PER_CATALOG} is DOWN-ONLY. RAM must be bounded by "
            f"the largest REGION, not by the file.")
        assert len(data["chromosomes"]) >= n, "fixture did not produce the sections"


def test_streamed_catalog_is_byte_identical_to_the_whole_body_derivation(pure_only):
    """**The equivalence that makes rc282 purely an I/O change.** The streamed
    derivation and the whole-body derivation it replaced must produce the SAME catalog
    — every field, including the per-region digests and the ``body_sha256`` region
    chain. If these ever diverge, every downstream offset and integrity bound is
    wrong, so this is the check that licenses the whole rc."""
    one = _one()
    for n in (1, 4, 25, 100):
        store = _store(n, one) if n > 1 else _store(1, one)
        path = pathlib.Path(store)
        head = G._read_manifest(path)
        leaf_dim = int(head["leaf_dim"])
        coupling_block = bytes.fromhex(head["coupling"]["hex"])

        streamed = G._catalog_data(path, one)

        # The pre-rc282 route, reconstructed here as the independent oracle.
        body_bytes = (path / G._BODY_NAME).read_bytes()
        specs, n_turns = G._scan_body_to_chrom_specs(body_bytes, leaf_dim)
        whole = G._build_manifest_data(leaf_dim, coupling_block, specs,
                                       body_bytes, n_turns)

        assert streamed == whole, (
            f"the streamed catalog DIVERGED from the whole-body derivation at "
            f"{n} sections — rc282 was supposed to change only HOW the bytes are "
            f"read, never what is derived from them")
        assert streamed["body_sha256"] == head["body_sha256"], (
            "the derived region chain no longer matches the committed head")


def test_counts_are_unchanged_end_to_end(pure_only):
    """The I/O change must be invisible at the result. Cross-checked against BOTH
    independent oracles the rc280 suite uses: the full per-section graph decode, and
    ``plasmid_extract``'s free streamed accumulator."""
    one = _one()
    docs = [[f"w{(d * 17 + i * 5) % 400}" for i in range(40)] for d in range(12)]
    d = tempfile.mkdtemp(prefix="rc282_")
    ext = P.plasmid_extract(docs, d, one, window=2, k=8)

    fast = P.section_counts(d, coupling=one)
    streamed = {int(k): int(v) for k, v in ext["section_count"].items()}
    assert fast == streamed, "the held-handle scan changed the counts"

    leaf_dim, resolved, entries = P._section_entries(d, one)
    full = {}
    for e in entries:
        graph = P._read_section_graph(d, e["label"], one, e, leaf_dim)
        for nid in set(int(x) for x in graph["node_ids"]):
            full[nid] = full.get(nid, 0) + 1
    assert fast == full, "the held-handle scan drifted from the full-decode oracle"
    assert max(fast.values()) >= 2, "fixture is degenerate — no overlapping vocab"


# ── the convenience path must still work ─────────────────────────────────────

def test_reads_still_work_with_no_handle_supplied(pure_only):
    """Threading a handle must not have made one MANDATORY — every read keeps an
    open-once-here path so no existing caller breaks, and it returns the same bytes."""
    one = _one()
    store = _store(8, one)
    path = pathlib.Path(store)
    leaf_dim, resolved, entries = P._section_entries(store, one)
    entry = entries[0]

    with G._open_body_ro(path / G._BODY_NAME) as f:
        with_handle = G._read_region(path, entry, leaf_dim, f)
        prefix_with = G._read_region_prefix(path, entry, leaf_dim, 4 * leaf_dim, f)
        ids_with = G._section_node_ids(path, entry, leaf_dim, resolved, f)

    assert with_handle == G._read_region(path, entry, leaf_dim)
    assert prefix_with == G._read_region_prefix(path, entry, leaf_dim, 4 * leaf_dim)
    assert ids_with == G._section_node_ids(path, entry, leaf_dim, resolved)


def test_a_lone_section_read_costs_one_open_not_two(pure_only):
    """Even WITHOUT a caller-supplied handle, ``_section_node_ids`` must open the body
    once for its whole growth loop. rc280 paid one open per loop ITERATION, which is
    where the 2.0-opens-per-section constant came from."""
    one = _one()
    store = _store(4, one)
    path = pathlib.Path(store)
    leaf_dim, resolved, entries = P._section_entries(store, one)

    with _BodyIOTally() as tally:
        G._section_node_ids(path, entries[0], leaf_dim, resolved)
    assert tally.opens <= 1, (
        f"a single section's node_ids read opened {G._BODY_NAME} {tally.opens} times "
        f"— the growth loop must run inside ONE handle")
