"""v0.9.0rc280 (§102 / F1253) — the targeted ``section_counts`` read.

rc278 shipped :func:`srmech.biology.plasmid.section_counts` as the genome-native SSoT
re-derivation of ``{global_id: n_sections}``. A downstream session then ran it over the
full simplewiki store — **240,881 sections** — and measured ~0.33 s/section: about
**22 HOURS**. They routed around it (rc279 made the free streamed accumulator the
default and the re-derivation opt-in), which was right, but left the fallback broken for
its two real jobs: RESUMING against a store you did not just build, and VERIFYING the
accumulator against the on-disk SSoT.

**Two costs, and the bigger one was not the one first diagnosed.**

1. *The catalog was re-derived per section.* A v12 HEAD-ONLY manifest stores no
   chromosome table, so :func:`genome.genome_window` derives it by reading the WHOLE
   body and re-folding its Merkle chain — and it did that once PER SECTION. That is
   O(P x whole body): **quadratic** in corpus size. Measured on this file's own fixtures
   it accounted for ~71 % of the runtime at P=80 and was growing.
2. *Every section's full graph was decoded* — edges, weights, charges — to reach a
   ``node_ids`` table the §89 payload places BEFORE all of them.

**No format change was needed** (``GENOME_FORMAT_VERSION`` stays 15). The payload is
``[vocab_size, n_node_ids] + node_ids + [n_extras] + extras + [n_edges] + edges…``, so
node_ids is a strict PREFIX; ``quad_turn`` is a per-leaf reversible XOR bind, so a prefix
of coupled leaves uncouples to exactly the prefix of the symbol stream; and the region's
integrity bound is its LEADING cap, so a prefix pays the SAME bound as a whole-region
read. The targeted read is not a weaker read — it is the same bound over fewer bytes.

Proven here:
  * **EQUIVALENCE (the SSoT check).** The targeted counts are IDENTICAL to the rc279
    full-decode derivation AND to ``plasmid_extract``'s free streamed accumulator, over
    fixtures with multiple sections and overlapping vocab. This must never drift.
  * **SCALING SHAPE — asserted structurally, not by wall-clock.** (a) the catalog is
    derived O(1) times per scan, not O(P) — the quadratic is gone; (b) per-section bytes
    read are independent of how many EDGES a section carries, so cost tracks node_ids,
    not section size.
  * §101 progress/cancel at whole-SECTION boundaries — and cancel RAISES rather than
    returning a partial, because a partial count is not a smaller valid count but a wrong
    one that would silently shift every downstream conservation threshold.
  * native == pure byte-parity for the whole scan.
  * the rc279 FAST PATH is not regressed: ``genome_integrate_plasmids(section_count=…)``
    still does zero re-derivation, and ``k_source`` semantics are intact.

numpy-free; integer/exact (Class-N); no ``abs()``.
"""
from __future__ import annotations

import tempfile

import pytest

from srmech.amsc import _native
from srmech.biology import genome as G
from srmech.biology import plasmid as P
from srmech.math.hdc import klein4_expand

_DIM = 64                                           # >= 52 (the §89 kernel header)


def _one(seed=1280):
    return klein4_expand(_DIM, seed)


def _store(docs, one, **kw):
    """A fresh plasmid section store over ``docs``; returns ``(path, extract_result)``."""
    d = tempfile.mkdtemp()
    return d, P.plasmid_extract(docs, d, one, **kw)


def _overlapping_docs():
    """Several sections with DELIBERATELY overlapping vocab — so the counts are a real
    distribution (ids at 1, 2 and 3 sections) rather than all-singletons."""
    return [
        ["alpha", "beta", "gamma", "delta", "alpha", "beta", "gamma"],
        ["beta", "gamma", "epsilon", "zeta", "beta", "gamma", "epsilon"],
        ["gamma", "zeta", "eta", "theta", "gamma", "zeta"],
        ["iota", "kappa", "alpha", "iota", "kappa"],
    ]


def _legacy_section_counts(store, one):
    """The rc279 derivation this rc replaces: census + a FULL graph decode per section.
    Kept HERE, in the test, as the independent oracle the fast path must match."""
    census = G.genome_census(store, coupling=one)
    counts = {}
    for chrom in census["chromosomes"]:
        if chrom["label"] == P.VOCAB_LABEL:
            continue
        graph = P._read_section_graph(store, chrom["label"], one)
        for nid in set(int(x) for x in graph["node_ids"]):
            counts[nid] = counts.get(nid, 0) + 1
    return counts


# ── EQUIVALENCE — the SSoT check ─────────────────────────────────────────────

def test_counts_equal_the_full_decode_derivation_and_the_streamed_accumulator():
    """The three independent routes to the same integers agree EXACTLY."""
    one = _one()
    d, ext = _store(_overlapping_docs(), one)
    fast = P.section_counts(d, coupling=one)
    legacy = _legacy_section_counts(d, one)
    streamed = {int(k): int(v) for k, v in ext["section_count"].items()}
    assert fast == legacy, (
        "the targeted node_ids read DRIFTED from the full-decode derivation — this is "
        f"the SSoT check\n  targeted: {sorted(fast.items())}\n  full:     "
        f"{sorted(legacy.items())}")
    assert fast == streamed, (
        "the on-disk derivation disagrees with plasmid_extract's streamed accumulator")
    assert max(fast.values()) >= 2, "fixture is degenerate — no overlapping vocab"


@pytest.mark.parametrize("n_docs,size,stride", [(1, 8, 1), (2, 12, 3), (7, 30, 5),
                                                (13, 20, 7), (20, 45, 11)])
def test_equivalence_across_store_shapes(n_docs, size, stride):
    """Equivalence holds across section counts and section sizes — including P=1 and
    stores whose vocab saturates (so the two-pass prefix read must grow)."""
    one = _one()
    words = ["w%03d" % i for i in range(60)]
    docs = [[words[(i * stride + j * 3) % len(words)] for j in range(size)]
            for i in range(n_docs)]
    d, ext = _store(docs, one)
    fast = P.section_counts(d, coupling=one)
    assert fast == _legacy_section_counts(d, one)
    assert fast == {int(k): int(v) for k, v in ext["section_count"].items()}


def test_targeted_node_ids_match_the_full_graph_decode_per_section():
    """The prefix read recovers each section's node_ids table EXACTLY — same values,
    same order — as decoding that section's whole graph does."""
    one = _one()
    d, _ext = _store(_overlapping_docs(), one)
    leaf_dim, resolved, entries = P._section_entries(d, one)
    assert entries, "no plasmid sections in the store"
    for e in entries:
        targeted = G._section_node_ids(G.Path(d), e, leaf_dim, resolved)
        full = P._read_section_graph(d, e["label"], one, e, leaf_dim)["node_ids"]
        assert targeted == [int(x) for x in full], (
            f"section {e['label']!r}: targeted node_ids != full-decode node_ids")


def test_vocab_chromosome_is_excluded():
    """The shared VOCAB karyotype chromosome is not a plasmid section and must not be
    counted (it would inflate every id's count by one)."""
    one = _one()
    d, _ext = _store(_overlapping_docs(), one)
    _ld, _one_r, entries = P._section_entries(d, one)
    assert P.VOCAB_LABEL not in [e["label"] for e in entries]
    labels = {c["label"] for c in G.genome_census(d, coupling=one)["chromosomes"]}
    assert P.VOCAB_LABEL in labels, "fixture should HAVE a vocab chromosome to exclude"


# ── SCALING SHAPE (structural, not wall-clock) ───────────────────────────────

def test_catalog_is_derived_once_per_scan_not_once_per_section():
    """**The quadratic killer.** genome_window re-derives the whole catalog on every
    call, and on a v12 head-only manifest that re-reads and re-Merkle-folds the ENTIRE
    body. Doing it inside the per-section loop made the scan O(P x body). Assert the
    derivation count does NOT grow with P — that is the O(P)-with-a-small-constant
    claim, pinned structurally so no wall-clock flake can hide a regression."""
    one = _one()
    words = ["w%03d" % i for i in range(80)]
    seen = {}
    real = G._catalog_data

    def counting(path, coupling=None):
        seen["n"] = seen.get("n", 0) + 1
        return real(path, coupling)

    for P_sections in (4, 8, 16, 32):
        docs = [[words[(i * 5 + j * 3) % len(words)] for j in range(25)]
                for i in range(P_sections)]
        d, _ext = _store(docs, one)
        seen["n"] = 0
        G._catalog_data = counting
        try:
            P.section_counts(d, coupling=one)
        finally:
            G._catalog_data = real
        assert seen["n"] <= 2, (
            f"section_counts derived the catalog {seen['n']} times over {P_sections} "
            f"sections — it must be O(1) per scan, not O(P). A per-section derivation "
            f"re-reads the whole body each time (the O(P x body) quadratic that made "
            f"this a ~22-hour op at 240,881 sections).")


def test_bytes_read_per_section_is_independent_of_edge_count():
    """**The targeted-read claim.** Two stores over the SAME documents differing only in
    the co-occurrence ``window`` carry the SAME node_ids but very different edge
    payloads — a wider window adds neighbours per node without adding nodes. Bytes read
    must track node_ids, NOT section size: cost is O(node_ids), not O(section). Asserted
    on bytes (deterministic) rather than seconds (flaky)."""
    one = _one()
    words = ["t%04d" % i for i in range(400)]
    docs = [[words[(i * 97 + j * 7) % len(words)] for j in range(120)]
            for i in range(4)]

    def read_bytes_for(window):
        d, _ext = _store(docs, one, window=window, k=64)
        leaf_dim, resolved, entries = P._section_entries(d, one)
        tally = {"read": 0, "region": 0, "ids": []}
        real = G._read_region_prefix

        def spy(path, entry, ld, max_bytes, f=None):
            # rc282 threads an already-open body handle through this read; the spy
            # forwards it so the tally measures the SAME bytes it always did.
            out = real(path, entry, ld, max_bytes, f)
            tally["read"] += len(out)
            return out

        G._read_region_prefix = spy
        try:
            for e in entries:
                tally["region"] += int(e["byte_len"])
                tally["ids"].append(
                    G._section_node_ids(G.Path(d), e, leaf_dim, resolved))
        finally:
            G._read_region_prefix = real
        return tally

    small, large = read_bytes_for(2), read_bytes_for(16)
    assert small["ids"] == large["ids"], (
        "fixture invalid — widening the window changed the node_ids, so a read-size "
        "difference would not isolate the EDGE payload")
    assert large["region"] > small["region"] * 2, (
        "fixture failed to produce a meaningful section-size difference "
        f"({small['region']} vs {large['region']} bytes) — the test would prove nothing")
    # Identical node_ids on both sides, so a node_ids-targeted read must not grow with
    # the (much larger) edge payload.
    assert large["read"] <= small["read"] * 2, (
        f"bytes read grew with EDGE count ({small['read']} -> {large['read']}) while the "
        f"node_ids tables are identical — the read is not targeted, it is still paying "
        f"O(section)")
    assert large["read"] < large["region"], (
        f"read {large['read']} of {large['region']} region bytes — a targeted read must "
        f"page strictly less than the whole region on an edge-heavy section")


def test_read_is_bounded_by_the_region_and_never_short():
    """The growth loop terminates at the whole region and never returns a SHORT table
    (a short node_ids table would silently UNDER-count, the one failure mode that would
    corrupt k without any error surfacing)."""
    one = _one()
    words = ["z%04d" % i for i in range(500)]
    docs = [[words[(i * 13 + j) % len(words)] for j in range(300)] for i in range(3)]
    d, _ext = _store(docs, one)
    leaf_dim, resolved, entries = P._section_entries(d, one)
    for e in entries:
        targeted = G._section_node_ids(G.Path(d), e, leaf_dim, resolved)
        full = [int(x) for x in
                P._read_section_graph(d, e["label"], one, e, leaf_dim)["node_ids"]]
        assert len(targeted) == len(full) and targeted == full


# ── §101 progress + cancel ───────────────────────────────────────────────────

def test_progress_ticks_between_whole_sections():
    one = _one()
    docs = _overlapping_docs()
    d, _ext = _store(docs, one)
    evs = []

    def tick(ev):
        evs.append(dict(ev))
        return False

    counts = P.section_counts(d, coupling=one, progress=tick)
    assert counts == _legacy_section_counts(d, one), "progress= changed the result"
    assert len(evs) == len(docs), f"expected one tick per section, got {len(evs)}"
    assert {e["phase"] for e in evs} == {_native.SRMECH_PHASE_EXTRACTING}
    assert [e["done"] for e in evs] == list(range(len(docs)))
    assert {e["total"] for e in evs} == {len(docs)}
    assert {e["struct_size"] for e in evs} == {_native.PROGRESS_STRUCT_SIZE}


def test_cancel_raises_rather_than_returning_a_partial_count():
    """A cancelled ENCODE returns a valid shorter genome; a cancelled COUNT cannot
    return anything valid, so it RAISES. The partial rides on the exception."""
    one = _one()
    docs = _overlapping_docs()
    d, _ext = _store(docs, one)
    with pytest.raises(P.SectionCountsCancelled) as exc:
        P.section_counts(d, coupling=one, progress=lambda ev: ev["done"] >= 2)
    assert exc.value.done == 2
    assert exc.value.total == len(docs)
    assert exc.value.counts, "the partial counts should be carried on the exception"
    full = _legacy_section_counts(d, one)
    assert exc.value.counts != full, (
        "the fixture must actually be truncated — otherwise the test proves nothing")
    for node, c in exc.value.counts.items():
        assert c <= full[node], "a partial count can never EXCEED the full count"


def test_a_tick_that_never_cancels_is_equivalent_to_no_tick():
    one = _one()
    d, _ext = _store(_overlapping_docs(), one)
    assert P.section_counts(d, coupling=one, progress=lambda ev: False) == \
        P.section_counts(d, coupling=one)


# ── native == pure ───────────────────────────────────────────────────────────

def test_native_and_pure_agree_byte_for_byte():
    """The C peer (when built) and the pure body derive the SAME integers. With no C
    peer present this still exercises the pure path end-to-end."""
    one = _one()
    d, _ext = _store(_overlapping_docs(), one)
    native_result = P.section_counts(d, coupling=one)
    real = _native.has_native_genome_section_counts
    _native.has_native_genome_section_counts = lambda: False
    try:
        pure_result = P.section_counts(d, coupling=one)
    finally:
        _native.has_native_genome_section_counts = real
    assert native_result == pure_result, (
        f"native/pure divergence: {sorted(native_result.items())} != "
        f"{sorted(pure_result.items())}")
    assert pure_result == _legacy_section_counts(d, one)


# ── the rc279 fast path must NOT regress ─────────────────────────────────────

def test_supplied_section_count_still_skips_the_scan_entirely():
    """rc279's contract: passing the free streamed accumulator does ZERO re-derivation.
    rc280 fixes the FALLBACK; it must not have made the fast path do any work."""
    one = _one()
    d, ext = _store(_overlapping_docs(), one)
    calls = {"n": 0}
    real = P.section_counts

    def counting(*a, **kw):
        calls["n"] += 1
        return real(*a, **kw)

    P.section_counts = counting
    try:
        org = P.genome_integrate_plasmids(d, one, section_count=ext["section_count"])
    finally:
        P.section_counts = real
    assert calls["n"] == 0, "the fast path re-derived the counts — rc279 regression"
    assert org["status"] == "ok"
    assert org["n_sections"] == len(_overlapping_docs())


def test_fallback_and_supplied_counts_produce_the_same_organize():
    """Omitting ``section_count`` (the rc280 fallback) organizes IDENTICALLY to passing
    the streamed accumulator — including ``k`` and ``k_source``."""
    one = _one()
    d, ext = _store(_overlapping_docs(), one)
    supplied = P.genome_integrate_plasmids(d, one, section_count=ext["section_count"])
    derived = P.genome_integrate_plasmids(d, one)
    for key in ("k", "k_source", "bimodal", "one_dna_type", "core", "counts",
                "n_sections", "n_integrated", "histogram", "status"):
        assert supplied[key] == derived[key], f"{key} diverged between the two paths"
    assert supplied["strand"] == derived["strand"], "the organized genomes differ"


def test_k_source_semantics_are_intact():
    """rc279's provenance contract survives: a caller-supplied k is POLICY, an
    auto-derivation that finds no qualifying antimode DECLINES, and neither is
    presented as the other."""
    one = _one()
    d, ext = _store(_overlapping_docs(), one)
    counts = P.section_counts(d, coupling=one)
    assert P.conserved_core(counts, k=2)["k_source"] == P.K_POLICY
    auto = P.conserved_core(counts)
    assert auto["k_source"] in (P.K_DERIVED, P.K_DECLINED)
    if auto["k_source"] == P.K_DECLINED:
        assert auto["k"] == 0 and auto["one_dna_type"] and not auto["core"]
