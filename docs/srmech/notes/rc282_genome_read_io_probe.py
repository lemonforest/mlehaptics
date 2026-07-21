"""rc282 — the GENERATING CODE for the genome read-path I/O measurements
(computational-provenance discipline).

Measures, on a real plasmid section store, over a sweep of section counts P:

  * ``opens``      — how many times ``turns.bin`` is OPENED during one pure
                     :func:`plasmid.section_counts` scan (the syscall constant
                     rc280 left behind);
  * ``t_targeted`` — wall time of that scan (the rc280 "targeted" read);
  * ``t_ride``     — wall time of a FULL SEQUENTIAL decode of the entire body:
                     one ``read_bytes``, walk EVERY block, ``quad_turn`` every
                     data turn. This is the `#876` cost-probe's own baseline
                     (``rc876_streaming_reader_cost_probe.py::probe_skip_vs_ride``)
                     and the one its "1.8x slower" claim is measured against —
                     reproduced here so before/after are comparable to the prior art;
  * ``t_full``     — a second baseline that produces the IDENTICAL counts (one
                     whole-body read, every region's node_ids decoded in memory),
                     so the comparison is also like-for-like on RESULT;
  * ``cat_opens``  — how many times ``turns.bin`` is opened / how many whole-body
                     slurps ``_catalog_data`` performs deriving the catalog once.

The fixture matches the `#876` probe (``doc_len=40, vocab=400, window=2, k=8``)
so the "before" row here reproduces that note's measurement.

Run:  python3 rc282_genome_read_io_probe.py [--out FILE.ndjson] [--sweep 25,50,100,200]

Emits one NDJSON record per sweep point (NDJSON-over-bloated-JSON discipline).
numpy-free; integer/exact; no ``abs()``.
"""
from __future__ import annotations

import argparse
import builtins
import json
import pathlib
import sys
import tempfile
import time

from srmech.amsc import _native
from srmech.amsc import genome as G
from srmech.amsc import plasmid as P
from srmech.amsc.hdc import klein4_expand

_DIM = 64                                   # >= 52 (the §89 kernel header)


# ── open-counting instrumentation ────────────────────────────────────────────

class _OpenTally:
    """Counts opens of ``turns.bin`` by wrapping BOTH ``builtins.open`` and
    ``pathlib.Path.open`` — genome.py reaches the body through both seams
    (``(path / _BODY_NAME).open("rb")`` and ``_open_body_ro``'s ``open(str(...))``).
    Also counts whole-body slurps via ``Path.read_bytes``."""

    def __init__(self, body_name=G._BODY_NAME):
        self.body_name = body_name
        self.opens = 0
        self.slurps = 0
        self.slurp_bytes = 0
        self._open = builtins.open
        self._path_open = pathlib.Path.open
        self._read_bytes = pathlib.Path.read_bytes

    def _hit(self, name):
        return str(name).replace("\\", "/").endswith("/" + self.body_name)

    def __enter__(self):
        tally = self

        def open_(file, *a, **kw):
            if tally._hit(file):
                tally.opens += 1
            return tally._open(file, *a, **kw)

        def path_open(self_, *a, **kw):
            if tally._hit(self_):
                tally.opens += 1
            return tally._path_open(self_, *a, **kw)

        def read_bytes(self_):
            out = tally._read_bytes(self_)
            if tally._hit(self_):
                tally.slurps += 1
                tally.slurp_bytes += len(out)
            return out

        builtins.open = open_
        pathlib.Path.open = path_open
        pathlib.Path.read_bytes = read_bytes
        return self

    def __exit__(self, *exc):
        builtins.open = self._open
        pathlib.Path.open = self._path_open
        pathlib.Path.read_bytes = self._read_bytes
        return False


# ── the FULL SEQUENTIAL baseline ─────────────────────────────────────────────

def full_sequential_counts(store, one):
    """The baseline the targeted read must beat: ONE sequential read of the whole
    body, then every section's node_ids decoded from the in-memory slice. Same
    integers as :func:`plasmid.section_counts`, zero per-section syscalls."""
    leaf_dim, resolved, entries = P._section_entries(store, one)
    body = (pathlib.Path(store) / G._BODY_NAME).read_bytes()
    counts = {}
    for e in entries:
        off, ln = int(e["byte_offset"]), int(e["byte_len"])
        region = body[off:off + ln]
        if G._sha256_bytes(region[:leaf_dim]) != e["cap_sha256"]:
            raise G.GenomeBoundingError("cap integrity bound failed")
        ints, _used = G._graph_prefix_ints(
            G._prefix_syms(region, leaf_dim, resolved))
        n_nid = int(ints[1]) if len(ints) >= G._NODE_IDS_HEADER_INTS else 0
        seen = set()
        for v in ints[G._NODE_IDS_HEADER_INTS:G._NODE_IDS_HEADER_INTS + n_nid]:
            seen.add(int(v))
        for nid in seen:
            counts[nid] = counts.get(nid, 0) + 1
    return counts


# ── fixtures ─────────────────────────────────────────────────────────────────

def build_store(n_sections, doc_len=40, vocab=400, window=2, seed=1282):
    """A plasmid section store with ``n_sections`` sections — the SAME fixture shape
    the `#876` cost probe used (``doc_len=40, vocab=400, window=2, k=8``), so the
    "before" numbers here reproduce that note's measurement."""
    one = klein4_expand(_DIM, seed)
    docs = [[f"w{(d * 17 + i * 5) % vocab}" for i in range(doc_len)]
            for d in range(n_sections)]
    dpath = tempfile.mkdtemp(prefix="rc282_")
    P.plasmid_extract(docs, dpath, one, window=window, k=8)
    return dpath, one


def ride_whole_body(store, one):
    """The `#876` probe's FULL SEQUENTIAL DECODE baseline: read the body once, walk
    every block, uncouple every data turn. The number the 1.8x claim is against."""
    body = (pathlib.Path(store) / G._BODY_NAME).read_bytes()
    n = 0
    for _raw, dec in G._walk_region_blocks(body, _DIM, context="rc282_ride"):
        if dec[0] <= 3:                         # a Klein-4 data turn
            n += len(G.quad_turn(G._hv_from_block(dec), one))
    return n


# ── one sweep point ──────────────────────────────────────────────────────────

def measure(n_sections, repeats=1):
    store, one = build_store(n_sections)

    # Force the PURE path — this rc is about the scripting projection's I/O.
    real_native = _native.has_native_genome_section_counts
    _native.has_native_genome_section_counts = lambda: False
    try:
        # catalog-derivation cost, measured on its own (part B)
        with _OpenTally() as cat:
            t0 = time.perf_counter()
            G._catalog_data(pathlib.Path(store), one)
            t_catalog = time.perf_counter() - t0

        with _OpenTally() as tally:
            t0 = time.perf_counter()
            for _ in range(repeats):
                targeted = P.section_counts(store, coupling=one)
            t_targeted = (time.perf_counter() - t0) / repeats

        t0 = time.perf_counter()
        for _ in range(repeats):
            full = full_sequential_counts(store, one)
        t_full = (time.perf_counter() - t0) / repeats

        t0 = time.perf_counter()
        for _ in range(repeats):
            ride_whole_body(store, one)
        t_ride = (time.perf_counter() - t0) / repeats
    finally:
        _native.has_native_genome_section_counts = real_native

    if targeted != full:
        raise AssertionError(
            "the targeted read and the full sequential decode DISAGREE — the "
            "measurement is meaningless until they match")

    body_bytes = (pathlib.Path(store) / G._BODY_NAME).stat().st_size
    return {
        "n_sections": n_sections,
        "repeats": repeats,
        "body_bytes": body_bytes,
        "opens_total": tally.opens,
        "opens_per_section": round(tally.opens / n_sections, 4),
        "body_slurps": tally.slurps,
        "body_slurp_bytes": tally.slurp_bytes,
        "catalog_opens": cat.opens,
        "catalog_slurps": cat.slurps,
        "catalog_slurp_bytes": cat.slurp_bytes,
        "t_catalog_s": round(t_catalog, 6),
        "t_targeted_s": round(t_targeted, 6),
        "t_ride_full_decode_s": round(t_ride, 6),
        "t_full_sequential_counts_s": round(t_full, 6),
        # the `#876` headline ratio: targeted vs a full sequential decode of the body
        "targeted_over_ride": round(t_targeted / t_ride, 4) if t_ride > 0 else None,
        "targeted_over_full_counts": round(t_targeted / t_full, 4) if t_full > 0 else None,
        "n_distinct_ids": len(targeted),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", default="25,50,100,200")
    ap.add_argument("--out", default=None)
    ap.add_argument("--label", default="")
    ap.add_argument("--repeats", type=int, default=1,
                    help="timing repeats per point; wall-clock is noisy, "
                         "the syscall counts are exact at repeats=1")
    args = ap.parse_args(argv)

    rows = []
    for n in [int(x) for x in args.sweep.split(",")]:
        row = measure(n, repeats=args.repeats)
        row["label"] = args.label
        rows.append(row)
        print(json.dumps(row), flush=True)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
