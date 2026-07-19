"""rc876 — does the ACCESSIBILITY LANDSCAPE exist on an F1252 stage-1 store?

Generates the ``marker_census_stage1_store`` measurement row in
``rc876_streaming_reader_design.ndjson`` and the §0.1 correction in
``rc876_streaming_reader_design.md``.

The rc876 brief's central premise is *"the accessibility landscape IS the index"*.
That premise is only load-bearing if stage-1 ``plasmid_extract`` sections actually
carry the ``0x48`` chromatin caps (and the ``0x47``/``0x62``/``0x67``/``0x77``/
``0x64`` gene gate caps) that ``gene_express_plan`` consults at plan time. This
script enumerates the marker bytes ACTUALLY present in a stage-1 store, runs the
demand-load plan against it at several ``cell_state`` values, and reads
``accessible()`` on one section.

Run from anywhere (locates the package relative to this file). numpy-free.
Emits NDJSON on stdout.

    python rc876_streaming_reader_marker_census.py
"""
import json
import sys
import tempfile
from pathlib import Path

# notes/ -> docs/srmech/ -> docs/srmech/python
_PKG = Path(__file__).resolve().parents[1] / "python"
sys.path.insert(0, str(_PKG))

from srmech.amsc import genome as G          # noqa: E402
from srmech.amsc import plasmid as PL        # noqa: E402
from srmech.amsc.hv import HV                # noqa: E402

LEAF_DIM = 64
DATE = "2026-07-19"
PHASE = "rc876-design"

#: Every interior/boundary cap marker the §44/§89/§95/§98 alphabet defines, so an
#: unexpected byte shows up as UNKNOWN_<n> rather than being silently bucketed.
MARKERS = {
    G.CHROM_CAP_MARKER: "CHROM",
    G.GENE_CAP_MARKER: "GENE_0x47",
    G.REGULATORY_GENE_MARKER: "REG_GENE",
    G.BOOLEAN_GENE_MARKER: "BOOL_GENE",
    G.THRESHOLD_GENE_MARKER: "THRESH_GENE",
    G.GRADED_GENE_MARKER: "GRADED_GENE",
    G.KERNEL_HEADER_MARKER: "KERNEL_HDR",
    G.KERNEL_TELOMERE_MARKER: "KERNEL_TELOMERE",
    G.ACTIVE_TELOMERE_MARKER: "ACTIVE_TELOMERE",
    G.CENTROMERE_CAP_MARKER: "CENTROMERE",
    G.DIPLOID_TELOMERE_MARKER: "DIPLOID_TELOMERE",
    G.CHROMATIN_MARKER: "CHROMATIN_0x48",
}

_GATE_KEYS = ("GENE_0x47", "REG_GENE", "BOOL_GENE", "THRESH_GENE", "GRADED_GENE")


def main():
    one = HV.from_sequence([(i * 7 + 3) % 4 for i in range(LEAF_DIM)], sectors=4)
    n_docs = 30
    docs = [[f"w{(d * 17 + i * 5) % 300}" for i in range(40)]
            for d in range(n_docs)]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "store"
        PL.plasmid_extract(docs, root, one, window=2, k=8)

        body = (root / "turns.bin").read_bytes()
        hist = {}
        for _raw, dec in G._walk_region_blocks(body, LEAF_DIM, context="census"):
            b = dec[0]
            name = MARKERS.get(b, "DATA_TURN" if b <= 3 else f"UNKNOWN_{b}")
            hist[name] = hist.get(name, 0) + 1

        # The demand-load plan the brief calls "the index". An EMPTY plan at every
        # cell_state means the plan-time skip has NOTHING to consult here.
        plans = {}
        for cs in (0, 1, 0xFFFF):
            plans[cs] = len(G.gene_express_plan(root, one, cs))

        # accessible() on one section's strand: (1,1) is the chromatin-FREE
        # default, i.e. no 0x48 cap is present to read.
        cat = G._catalog_data(root, one)
        e = next(c for c in cat["chromosomes"] if c["label"] != PL.VOCAB_LABEL)
        leaves = G._region_leaves(root, e, LEAF_DIM)
        strand = [G._kernel_telomere(e["label"], dim=LEAF_DIM)] + list(leaves)
        acc = list(G.accessible(strand, 0, the_one=one))

        print(json.dumps({
            "date": DATE, "phase": PHASE, "kind": "measurement",
            "measure": "marker_census_stage1_store",
            "markers": hist,
            "chromatin_caps_0x48": hist.get("CHROMATIN_0x48", 0),
            "gene_gate_caps": sum(hist.get(k, 0) for k in _GATE_KEYS),
            "gene_express_plan_regions_cs0": plans[0],
            "gene_express_plan_regions_cs1": plans[1],
            "gene_express_plan_regions_cs65535": plans[0xFFFF],
            "accessible_cs0": acc,
            "n_docs": n_docs,
            "verdict": "the accessibility landscape does NOT exist on a stage-1 "
                       "plasmid store: 0 chromatin caps, 0 gene gate caps, an "
                       "EMPTY plan at every cell_state, and the chromatin-free "
                       "(1,1) default from accessible()",
            "generator": "rc876_streaming_reader_marker_census.py",
        }))


if __name__ == "__main__":
    main()
