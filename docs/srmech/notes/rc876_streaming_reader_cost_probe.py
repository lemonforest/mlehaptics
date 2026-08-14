"""rc876 streaming-reader design — COST PROBE (computational provenance).

Generates every timing / syscall number cited in
``rc876_streaming_reader_design.md`` §5 and in the ``kind":"measurement"`` rows of
``rc876_streaming_reader_design.ndjson``.

Measures, on a synthetic F1252 stage-1 plasmid store:

  1. the COLD-OPEN cost of a v12 head-only store (``_catalog_data``), split into
     its two terms — the block-stride scan vs. the region-Merkle + array build;
  2. STRIDE (classify caps, decode nothing) vs. RIDE (uncouple every data turn)
     vs. the rc280 TARGETED ``node_ids`` read;
  3. the number of ``turns.bin`` opens one targeted pass actually performs.

Run from ``docs/srmech/python`` (or anywhere — it locates the package relative to
this file). numpy-free; stdlib timing only. Emits NDJSON on stdout.

    python ../notes/rc876_streaming_reader_cost_probe.py
"""
import json
import sys
import tempfile
import time
from pathlib import Path

# notes/ -> docs/srmech/ -> docs/srmech/python
_PKG = Path(__file__).resolve().parents[1] / "python"
sys.path.insert(0, str(_PKG))

from srmech.biology import genome as G          # noqa: E402
from srmech.biology import plasmid as PL        # noqa: E402
from srmech.amsc.hv import HV                # noqa: E402

LEAF_DIM = 64
DATE = "2026-07-19"
PHASE = "rc876-design"
GEN = "rc876_streaming_reader_cost_probe.py"


def the_one(dim=LEAF_DIM):
    """A deterministic Klein-4 coupling invariant of width ``dim`` (>= 52 so the
    §89 uniformly-Klein-4 kernel header fits one leaf)."""
    return HV.from_sequence([(i * 7 + 3) % 4 for i in range(dim)], sectors=4)


def build_store(root, n_docs, doc_len=40, vocab_n=400):
    """Build a stage-1 plasmid store of ``n_docs`` sections from deterministic
    token streams (so a re-run reproduces the same body bytes)."""
    docs = [[f"w{(d * 17 + i * 5) % vocab_n}" for i in range(doc_len)]
            for d in range(n_docs)]
    one = the_one()
    PL.plasmid_extract(docs, root, one, window=2, k=8)
    return one


def timeit(fn, reps=3):
    """Best-of-``reps`` wall time. Best-of, not mean — we want the floor, and the
    noise here is all upward (GC, page-cache misses, OS scheduling)."""
    best = None
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        dt = time.perf_counter() - t0
        best = dt if best is None or dt < best else best
    return best


def sections_of(root, one):
    """The store's PLASMID section entries — the VOCAB karyotype chromosome
    EXCLUDED. Excluding it is not cosmetic: ``_section_node_ids`` on ``__vocab__``
    raises GenomeBoundingError, because the vocab chromosome carries the SAME 0x6B
    kernel telomere as a section but holds a raw Klein-4 byte blob rather than a
    §89 graph payload (anomaly A3)."""
    cat = G._catalog_data(root, one)
    return [c for c in cat["chromosomes"] if c["label"] != PL.VOCAB_LABEL]


def probe_catalog(root, one):
    """Term-split the cold-open cost of a v12 HEAD-ONLY store."""
    body = (Path(root) / "turns.bin").read_bytes()
    t_catalog = timeit(lambda: G._catalog_data(Path(root), one))
    t_scan = timeit(lambda: G._scan_body_to_chrom_specs(body, LEAF_DIM))
    specs, n_turns = G._scan_body_to_chrom_specs(body, LEAF_DIM)
    ob = G._leaf_blocks([one])[0]
    t_build = timeit(lambda: G._build_manifest_data(LEAF_DIM, ob, specs, body,
                                                    n_turns))

    def stream():
        n = 0
        for _raw, dec in G._walk_region_blocks(body, LEAF_DIM, context="probe"):
            if dec[0] in (G.CHROM_CAP_MARKER, G.KERNEL_TELOMERE_MARKER,
                          G.ACTIVE_TELOMERE_MARKER, G.DIPLOID_TELOMERE_MARKER):
                n += 1
        return n
    t_stream = timeit(stream)
    return {
        "date": DATE, "phase": PHASE, "kind": "measurement",
        "measure": "cost_probe", "impl": "scripting-coherency (HAS_NATIVE=false)",
        "leaf_dim": LEAF_DIM,
        "n_sections": len(specs), "body_bytes": len(body), "n_blocks": n_turns,
        "t_catalog_cold_s": round(t_catalog, 6),
        "t_scan_only_s": round(t_scan, 6),
        "t_build_manifest_s": round(t_build, 6),
        "t_stream_walk_s": round(t_stream, 6),
        "build_frac_of_catalog": round(t_build / t_catalog, 4),
        "generator": GEN,
    }


def probe_skip_vs_ride(root, one):
    """STRIDE vs RIDE vs the rc280 TARGETED node_ids read, over the same body."""
    body = (Path(root) / "turns.bin").read_bytes()
    ents = sections_of(root, one)

    def stride():
        n = 0
        for _raw, dec in G._walk_region_blocks(body, LEAF_DIM, context="x"):
            if dec[0] == G.KERNEL_TELOMERE_MARKER:
                n += 1
        return n

    def ride():
        n = 0
        for _raw, dec in G._walk_region_blocks(body, LEAF_DIM, context="x"):
            if dec[0] <= 3:                     # a Klein-4 data turn
                n += len(G.quad_turn(G._hv_from_block(dec), one))
        return n

    def targeted():
        return sum(len(G._section_node_ids(root, e, LEAF_DIM, one)) for e in ents)

    ts, tr, tp = timeit(stride), timeit(ride), timeit(targeted)
    return {
        "date": DATE, "phase": PHASE, "kind": "measurement",
        "measure": "skip_vs_ride", "impl": "scripting-coherency (HAS_NATIVE=false)",
        "leaf_dim": LEAF_DIM, "n_sections": len(ents), "body_bytes": len(body),
        "t_stride_s": round(ts, 5),
        "t_ride_full_decode_s": round(tr, 5),
        "t_targeted_node_ids_all_sections_s": round(tp, 5),
        "ride_over_stride": round(tr / ts, 2),
        "prefix_over_stride": round(tp / ts, 2),
        "generator": GEN,
    }


def probe_syscalls(root, one):
    """Count ``turns.bin`` opens during ONE full targeted node_ids pass.

    ``_read_region_prefix`` opens the body fresh on every call and
    ``_section_node_ids`` calls it in a growth loop — so this is the syscall
    constant rc280 left behind (anomaly A2)."""
    ents = sections_of(root, one)
    orig = Path.open
    n = [0]

    def counting(self, *a, **k):
        n[0] += 1
        return orig(self, *a, **k)

    Path.open = counting
    try:
        for e in ents:
            G._section_node_ids(root, e, LEAF_DIM, one)
    finally:
        Path.open = orig
    # The field store is 240,881 sections; extrapolate the per-section constant.
    per = n[0] / len(ents)
    return {
        "date": DATE, "phase": PHASE, "kind": "measurement",
        "measure": "targeted_read_syscall_count",
        "n_sections": len(ents), "body_file_opens": n[0],
        "opens_per_section": round(per, 2),
        "extrapolated_opens_field_store": int(round(per * 240881)),
        "note": "_read_region_prefix opens turns.bin fresh on EVERY call and "
                "_section_node_ids calls it in a growth loop",
        "generator": GEN,
    }


def main():
    for n in (25, 50, 100, 200):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "store"
            one = build_store(root, n)
            print(json.dumps(probe_catalog(root, one)))
    # The skip/ride + syscall probes want ONE store at the largest size.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "store"
        one = build_store(root, 200)
        print(json.dumps(probe_skip_vs_ride(root, one)))
        print(json.dumps(probe_syscalls(root, one)))


if __name__ == "__main__":
    main()
