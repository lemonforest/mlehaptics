"""v0.9.0rc282 (§102 / F1253) — the genome READ-PATH I/O ratchet.
v0.9.0rc296 — the ratchet learns to measure the projection it was blind to.

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

── rc296: the ratchet had the same shape of defect it was built to catch ───────

rc282 fixed the open-per-call defect in **both** coherency projections and said so.
But every one of the six tests in this file took a ``pure_only`` fixture that
monkeypatched native dispatch OFF. So the down-only ceiling constrained the
**scripting projection only**, and rc282's compiled-side measurement — *"4 / 4 / 4 / 4
turns.bin opens, constant in P"* — had **zero test coverage**. The compiled read path
could regress to per-call re-open (precisely the rc280 defect rc282 shipped to fix)
with this file still green.

That is an **ADR-0009 parity gap inside a ratchet**: if the capability is the
invariant, a ceiling that can only ever run one projection cannot enforce it.

Two things were wrong, and they are separable:

1. **The fixture was applied where it does nothing.** Only two of the six tests call
   :func:`plasmid.section_counts`, the one function here that dispatches. The other
   four exercise ``genome`` helpers (``_catalog_data`` / ``_section_node_ids`` /
   ``_read_region``…) that contain **no native dispatch at all** — verified by AST,
   not by eye. On those, ``pure_only`` was inert decoration that made a blanket
   application *look* like a deliberate per-test scoping decision. It is now applied
   only where it changes what runs, and the genuinely pure-scoped tests say why.
2. **The compiled projection was unmeasurable, not merely unmeasured.** Python's
   ``builtins.open`` / ``Path.open`` hooks cannot see an ``fopen`` inside
   ``libsrmech``, so no amount of test-side instrumentation could have covered it.
   rc296 adds the seam that makes it measurable: a read-path open counter in the PAL
   (``srmech_plat_file_opens`` / ``_reset``), diagnostic-only and additive — ABI
   stays 8.

**The rc282 number was right.** Re-measured at rc296 by both instruments and it
reproduces exactly: 4 turns.bin opens per scan on the native path, flat across the
25/50/100/200 sweep. The strace decomposition is 1 Python-side open
(``_section_entries`` derives the catalog before dispatch) + 3 C-side; the C library
performs 5 read-path opens in total per scan (2 ``manifest.json`` + 3 ``turns.bin``).
Generating code: ``notes/rc282_c_open_count_probe.sh`` — which rc296 also had to
repair, because the rc290 ``the_one`` → ``coupling`` rename left it raising
``TypeError``. Provenance that does not run is not provenance.

What is pinned:
  * opens of ``turns.bin`` do **not grow with section count** over a 4-point sweep,
    in **BOTH** projections — the O(P)-opens shape cannot come back to either;
  * the compiled projection's total read-path opens are constant in P;
  * the two projections agree on the counts they derive (ADR-0009 parity);
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
from srmech.biology import genome as G
from srmech.biology import plasmid as P
from srmech.math.hdc import klein4_expand

_DIM = 64                                           # >= 52 (the §89 kernel header)

# ── THE RATCHET CEILINGS — down-only ─────────────────────────────────────────
#
# Measured on the rc282 implementation, re-measured at rc296. A change that LOWERS a
# number should lower the ceiling in the same commit; a change that RAISES one is the
# regression this file exists to catch, and must not be "fixed" by raising the ceiling.
#
#   rc280 (the defect):  CEIL_BODY_OPENS_PER_SCAN grew as 2P + 1  (401 at P = 200)
#   rc282 (now):         constant, independent of P
#
#: Total opens of ``turns.bin`` for ONE whole ``section_counts`` scan, ANY P, on the
#: SCRIPTING projection. rc282 measures 2 (one for the catalog derivation, one held
#: across the scan).
CEIL_BODY_OPENS_PER_SCAN = 2

#: Whole-body ``read_bytes()`` slurps while deriving a catalog. rc282 measures 0.
CEIL_BODY_SLURPS_PER_CATALOG = 0

#: rc296 — the COMPILED projection's total read-path opens (ANY file: the C peer reads
#: ``manifest.json`` as well as ``turns.bin``) for ONE whole native scan, ANY P.
#: Measured 5 across the sweep: 2 manifest + 3 body. Counted inside the library by the
#: PAL counter, because a Python-side hook cannot see an ``fopen`` in the .so.
#:
#: rc282 (the C defect): sc_refill paged its window through
#: srmech_plat_file_read_region, which fopen/fcloses per call -> 28 / 53 / 103 / 203
#: over this same sweep, ~1 open per section. Now a held handle, constant in P.
CEIL_NATIVE_C_OPENS_PER_SCAN = 5

#: rc296 — Python-side opens of ``turns.bin`` that remain on the NATIVE path: the
#: pre-dispatch ``_section_entries`` catalog derivation. Measured 1, flat in P. Pinned
#: separately from the C count because they are different seams with different repair
#: paths; summed they are the 4 rc282 reported and strace still records.
CEIL_NATIVE_PY_BODY_OPENS_PER_SCAN = 1

#: The sweep. At least 4 points, spanning an 8x range, so "does not grow with P" is
#: a real observation and not two coincidences.
_SWEEP = (25, 50, 100, 200)

#: rc296 — the compiled projection is only measurable when it is actually loaded AND
#: the PAL counter is bound. A pure-Python install legitimately has neither, so these
#: SKIP rather than fail; the skip reason names exactly what is missing, because a
#: ratchet that quietly stops running is the failure mode this file is about.
_needs_native = pytest.mark.skipif(
    not (_native.has_native_genome_section_counts()
         and _native.has_native_file_open_counter()),
    reason=("compiled projection not measurable here: "
            f"native section_counts={_native.has_native_genome_section_counts()}, "
            f"PAL open counter={_native.has_native_file_open_counter()}"))


# ── instrumentation ──────────────────────────────────────────────────────────

class _BodyIOTally:
    """Counts opens + whole-body slurps of ``turns.bin`` **made from Python**.

    Wraps ``builtins.open``, ``pathlib.Path.open`` AND ``pathlib.Path.read_bytes``,
    because genome.py reaches the body through all three seams — instrumenting only
    one would let a regression through the others, which is exactly the kind of gap
    that let the original defect ship.

    **Scope limit, stated because rc282 tripped over it:** these hooks are blind to an
    ``fopen`` inside ``libsrmech``. On the native path this tally sees only the
    Python-side opens; the C side is counted by :class:`_CIOTally` below."""

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


class _CIOTally:
    """rc296 — counts read-path opens performed INSIDE ``libsrmech``.

    Reads the PAL counter (``srmech_plat_file_opens``) around the measured span. This
    is the seam that makes the compiled projection's I/O shape testable at all: it
    counts every read-path ``fopen`` ATTEMPT the C library makes — the same quantity
    ``strace -e trace=openat`` records — so the in-suite ratchet and the committed
    strace probe measure one thing and can be compared."""

    def __init__(self):
        self.opens = 0

    def __enter__(self):
        _native.file_opens_reset_c()
        return self

    def __exit__(self, *exc):
        self.opens = _native.file_opens_c()
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
def sweep_stores():
    """The 4-point sweep, built ONCE and shared by the pure and native open-count
    tests. Sharing is not only cheaper: it means both projections are measured against
    the **same bytes on disk**, so a difference between them is a difference in the
    code and not in the fixture."""
    one = _one()
    return one, {n: _store(n, one) for n in _SWEEP}


@pytest.fixture
def force_pure(monkeypatch):
    """Force the SCRIPTING projection by turning native ``section_counts`` dispatch off.

    **Load-bearing only where :func:`plasmid.section_counts` is called.** The
    ``genome`` helpers this file also exercises (``_catalog_data``,
    ``_section_node_ids``, ``_read_region``, ``_read_region_prefix``) contain no native
    dispatch, so applying this to them changes nothing — which is how rc282 ended up
    looking like it had made a scoping decision on all six tests when it had made one
    on two. Applied here only where it changes what runs.

    ``monkeypatch`` rather than manual save/restore so a failing assertion cannot leave
    dispatch globally disabled for the rest of the session."""
    monkeypatch.setattr(_native, "has_native_genome_section_counts", lambda: False)


# ── THE RATCHET — the scripting projection ───────────────────────────────────

def test_body_opens_do_not_grow_with_section_count(force_pure, sweep_stores):
    """**The load-bearing assertion, scripting projection.** Opens of ``turns.bin`` per
    ``section_counts`` scan must be CONSTANT in P. Under rc280 this was ``2P + 1`` —
    401 opens at P=200, ~481,762 extrapolated to the field store — while the code
    claimed to be the "targeted" fast read.

    Asserted on the syscall COUNT, not on wall-clock: the count is exact, portable and
    has no variance, whereas the time it costs is platform-dependent (on the machine
    that measured this rc the 200-section targeted read was ~0.78x a full sequential
    decode, not the 1.8x measured on the `#876` probe's host — same defect, different
    I/O economics). The count is the invariant; the seconds are not."""
    one, stores = sweep_stores
    observed = {}
    for n in _SWEEP:
        with _BodyIOTally() as tally:
            P.section_counts(stores[n], coupling=one)
        observed[n] = tally.opens

    # A seam that stops observing must FAIL, not pass with zeros: every scan opens
    # the body at least once, so a 0 here means the hooks came unstuck.
    assert min(observed.values()) > 0, (
        f"the I/O tally observed NO opens at all ({observed}) — the instrumentation "
        f"has stopped seeing the body reads, so every ceiling below it is vacuous.")

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


# ── THE RATCHET — the compiled projection (rc296) ────────────────────────────

@_needs_native
def test_native_c_side_opens_do_not_grow_with_section_count(sweep_stores):
    """**The assertion rc282 claimed and never made.** The COMPILED ``section_counts``
    must hold ONE handle for the whole scan, so its read-path opens are constant in P.

    Before rc282 the C refilled its 64 KiB sliding window through
    ``srmech_plat_file_read_region``, which ``fopen``/``fclose``s per call — measured
    28 / 53 / 103 / 203 over this exact sweep, ~1 open per section. That is the same
    defect shape as the scripting projection's, at a different constant, and per
    ADR-0009 it is the same invariant being violated: the capability is what must hold,
    not one projection's version of it.

    Counted inside the library (the PAL counter), because a Python ``open`` hook is
    structurally incapable of seeing this — which is why rc282 could report the number
    from an strace probe and still ship no test for it."""
    one, stores = sweep_stores
    observed = {}
    for n in _SWEEP:
        with _CIOTally() as tally:
            P.section_counts(stores[n], coupling=one)
        observed[n] = tally.opens

    # Dead-seam guard: the native scan MUST open files. A 0 means dispatch silently
    # fell back to pure, or the counter stopped counting — either way this test is
    # then measuring nothing and must say so rather than pass.
    assert min(observed.values()) > 0, (
        f"the C open counter recorded NO opens ({observed}) — either native dispatch "
        f"did not run (so this test measured the pure path) or the PAL counter is no "
        f"longer wired. Both make the ceiling vacuous.")

    assert max(observed.values()) <= CEIL_NATIVE_C_OPENS_PER_SCAN, (
        f"the compiled section_counts made more read-path opens than the "
        f"CEIL_NATIVE_C_OPENS_PER_SCAN={CEIL_NATIVE_C_OPENS_PER_SCAN} ratchet allows: "
        f"{observed}. DOWN-ONLY. If sc_refill has gone back to "
        f"srmech_plat_file_read_region (open/close per call) this is the rc280 defect "
        f"returning to the projection rc282 said it had fixed.")

    assert observed[_SWEEP[-1]] <= observed[_SWEEP[0]], (
        f"the compiled scan's opens GREW with section count ({observed}) — the "
        f"per-section open shape is back. srmech_genome_section_counts must page "
        f"through the srmech_plat_file_open_ro handle it holds for the whole scan.")


@_needs_native
def test_native_python_side_body_opens_do_not_grow_either(sweep_stores):
    """The native path is not all C: ``section_counts`` derives the store catalog in
    Python (``_section_entries``) BEFORE dispatching, and that opens the body. Pinned
    separately from the C count because it is a separate seam — a regression here would
    be a Python-side one on a code path whose tests all previously forced pure, so
    nothing watched it.

    1 Python-side open + 3 C-side = the 4 total opens of ``turns.bin`` rc282 measured
    by strace and rc296 re-measured unchanged."""
    one, stores = sweep_stores
    observed = {}
    for n in _SWEEP:
        with _BodyIOTally() as tally:
            P.section_counts(stores[n], coupling=one)
        observed[n] = tally.opens

    assert min(observed.values()) > 0, (
        f"no Python-side body opens observed on the native path ({observed}) — the "
        f"pre-dispatch catalog derivation cannot have run, so the tally is broken.")

    assert max(observed.values()) <= CEIL_NATIVE_PY_BODY_OPENS_PER_SCAN, (
        f"the native path's PYTHON-side opens of {G._BODY_NAME} exceeded "
        f"CEIL_NATIVE_PY_BODY_OPENS_PER_SCAN="
        f"{CEIL_NATIVE_PY_BODY_OPENS_PER_SCAN}: {observed}. DOWN-ONLY.")

    assert observed[_SWEEP[-1]] <= observed[_SWEEP[0]], (
        f"Python-side opens GREW with P on the native path ({observed}) — the catalog "
        f"must be derived ONCE for the whole scan, not per section.")


@_needs_native
def test_both_projections_derive_the_same_counts(sweep_stores, monkeypatch):
    """**ADR-0009 parity, asserted rather than assumed.** The two coherency projections
    must agree on every count for the same store. rc282 pinned the scripting
    projection's I/O and the compiled projection's I/O separately (one by test, one by
    probe) but never checked that the two still produce the same answer under the
    held-handle rewrite — and a read-path rewrite is exactly the kind of change that
    can silently truncate one projection's output.

    Measured on the same bytes, in one process, back to back."""
    one, stores = sweep_stores
    for n in _SWEEP:
        native = P.section_counts(stores[n], coupling=one)
        monkeypatch.setattr(_native, "has_native_genome_section_counts", lambda: False)
        pure = P.section_counts(stores[n], coupling=one)
        monkeypatch.undo()

        assert native == pure, (
            f"the compiled and scripting projections DISAGREE at {n} sections: "
            f"{len(native)} vs {len(pure)} distinct ids. Per ADR-0009 the capability "
            f"is the invariant — a projection that returns different counts is not a "
            f"projection of the same capability.")
        assert len(native) > 0, "fixture produced no counts — the store is degenerate"


# ── the catalog derivation (no native dispatch on this path) ─────────────────

def test_catalog_derivation_never_slurps_the_whole_body():
    """``_catalog_data`` on the v12+ HEAD-ONLY branch — the branch every store written
    today takes — must DERIVE the catalog by streaming, never by holding the entire
    body in RAM. Pinned as a ratchet because the slurp was invisible: it sat one line
    below a docstring bullet about the O(1) head.

    **Genuinely pure-scoped** (rc296): ``_catalog_data`` has no native dispatch — no
    ``_native`` reference anywhere in its body — so there is no compiled projection of
    this to measure. rc282's ``pure_only`` here was inert."""
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


def test_streamed_catalog_is_byte_identical_to_the_whole_body_derivation():
    """**The equivalence that makes rc282 purely an I/O change.** The streamed
    derivation and the whole-body derivation it replaced must produce the SAME catalog
    — every field, including the per-region digests and the ``body_sha256`` region
    chain. If these ever diverge, every downstream offset and integrity bound is
    wrong, so this is the check that licenses the whole rc.

    **Genuinely pure-scoped** (rc296): both sides of this equivalence are Python
    derivations with no native dispatch."""
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


def test_counts_are_unchanged_end_to_end(force_pure):
    """The I/O change must be invisible at the result. Cross-checked against BOTH
    independent oracles the rc280 suite uses: the full per-section graph decode, and
    ``plasmid_extract``'s free streamed accumulator.

    ``force_pure`` IS load-bearing here — this calls ``section_counts``. It pins the
    SCRIPTING projection against the oracles; the compiled projection is held to the
    same result by ``test_both_projections_derive_the_same_counts`` above, so between
    them both projections are checked against the oracle rather than one."""
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

def test_reads_still_work_with_no_handle_supplied():
    """Threading a handle must not have made one MANDATORY — every read keeps an
    open-once-here path so no existing caller breaks, and it returns the same bytes.

    **Genuinely pure-scoped** (rc296): these are ``genome`` region readers with no
    native dispatch."""
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


def test_a_lone_section_read_costs_one_open_not_two():
    """Even WITHOUT a caller-supplied handle, ``_section_node_ids`` must open the body
    once for its whole growth loop. rc280 paid one open per loop ITERATION, which is
    where the 2.0-opens-per-section constant came from.

    **Genuinely pure-scoped** (rc296): ``_section_node_ids`` has no native dispatch."""
    one = _one()
    store = _store(4, one)
    path = pathlib.Path(store)
    leaf_dim, resolved, entries = P._section_entries(store, one)

    with _BodyIOTally() as tally:
        G._section_node_ids(path, entries[0], leaf_dim, resolved)
    assert tally.opens > 0, (
        "no opens observed at all — the tally has stopped seeing the read, which "
        "would make the ceiling below it vacuous")
    assert tally.opens <= 1, (
        f"a single section's node_ids read opened {G._BODY_NAME} {tally.opens} times "
        f"— the growth loop must run inside ONE handle")
