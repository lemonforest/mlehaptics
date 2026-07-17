r"""R-RBS-LM-GENOME-CENSUS — answer "what is IN a genome, and how does it partition?" the way biology asks it:
how many chromosomes, of which TYPE (plasmid/stick vs eukaryotic/minted-centromere vs diploid pair), and — across a
ROOT of genomes (a "cell") — which genome is the NUCLEUS (big, minted chromosomes) vs an ORGANELLE (a small circular
plasmid-like stick genome, mitochondrion/chloroplast). This is what we CAN answer today by composing srmech reads,
and the concrete target for a NATIVE `genome_census` op (§96).

What srmech gives today (rc265):
  * `genome_catalog(path)` → the top-level introspection: `{format_version, leaf_dim, n_turns, chromosomes:[{label,
    leaf_count, byte_len, byte_offset, cap_sha256}], regions, body_sha256, the_one}`. So the CHROMOSOME COUNT
    (len(chromosomes)) + each chromosome's label/size/offset are one call — but the entry carries **no TYPE / cap-kind**.
  * The TYPE (stick / minted / diploid) is in the BODY (the cap markers telomere / `0x58` centromere / `0x44` diploid
    drive partition / centromere_of / recover_diploid), so we recover it by probing each chromosome — O(n) loads.
  * There is NO cross-genome registry: a genome = one directory; "how many genomes" (the melange / the cell, ADR-0006)
    is a filesystem/caller concern.

census_one(path) composes those into the makeup; census_root(root) scans a directory of genomes (a cell) and reads
each one's nuclear-vs-organelle topology from its makeup.

srmech 0.9.0rc265. No ALU magnitude-builtin. Composes §95/§96, ADR-0006 (the lichen/melange = the cell), F1243/F1245.
Run:  /tmp/srmech_latest/venv/bin/python3 R-RBS-LM-GENOME-CENSUS_*.py
"""
import sys
from pathlib import Path

from srmech.amsc import genome as G, hdc

VOCAB_LABELS = {"__vocab__"}                                  # non-chromosomal codebook labels to report separately


def classify(path, one, label):
    """The TYPE of ONE chromosome — probe the cap (srmech gives no type in the catalog today)."""
    chrom, _a, _b = G.genome_load(str(path), labels=[label], the_one=one)
    if G.centromere_of(chrom) is not None:
        cen = G.centromere_of(chrom)
        return "minted", {"orientation": cen["orientation"], "arm_ratio": cen["arm_ratio"]}
    try:
        if G.recover_diploid(chrom, one) is not None:
            return "diploid", {}
    except Exception:
        pass
    return "stick", {}


def census_one(path, one):
    """Chromosome-type makeup of one genome + a nuclear-vs-organelle topology read."""
    cat = G.genome_catalog(str(path), the_one=one)
    entries = cat.get("chromosomes", [])
    types = {"stick": 0, "minted": 0, "diploid": 0}
    detail, codebooks, leaf_tot = [], 0, 0
    for e in entries:
        lab = e["label"] if isinstance(e, dict) else e[0]
        nleaf = e.get("leaf_count", 0) if isinstance(e, dict) else 0
        leaf_tot += nleaf
        if lab in VOCAB_LABELS:
            codebooks += 1
            continue
        kind, meta = classify(path, one, lab)
        types[kind] += 1
        detail.append({"label": lab, "type": kind, "leaves": nleaf, **meta})
    n_chr = types["stick"] + types["minted"] + types["diploid"]
    # topology (structural, biology-native): the caller confirms the ROLE, srmech reads the SHAPE.
    if types["minted"] or types["diploid"]:
        topo = "nuclear-like (has minted/centromere or diploid chromosomes — a eukaryotic nucleus)"
    elif n_chr and leaf_tot / max(1, n_chr) <= 8:
        topo = "organelle-like (all small stick chromosomes — a mitochondrion/chloroplast plasmid genome)"
    elif n_chr:
        topo = "plasmid/prokaryote-like (all stick chromosomes, no centromere)"
    else:
        topo = "empty / codebook-only"
    return {"path": str(path), "n_chromosomes": n_chr, "codebooks": codebooks, "types": types,
            "total_leaves": leaf_tot, "topology": topo, "detail": detail}


def is_genome_dir(p):
    return p.is_dir() and (p / "turns.bin").exists() and (p / "manifest.json").exists()


def census_root(root, one):
    """The CELL: every genome under `root`, each with its makeup + nuclear/organelle role (the melange census)."""
    genomes = sorted(p for p in Path(root).iterdir() if is_genome_dir(p))
    return {"root": str(root), "n_genomes": len(genomes), "genomes": [census_one(p, one) for p in genomes]}


def _demo():
    import tempfile
    one = hdc.klein4_random(64, seed=0)
    def leaves(n): return [[(i * 7 + j) % 4 for j in range(64)] for i in range(n)]
    root = Path(tempfile.mkdtemp())
    # a "nucleus": mixed stick + minted (the umbrella auto-mints ≥5-leaf kernels)
    nuc = root / "nucleus.genome"
    G.genome_save(G.genome([("chrX", leaves(9)), ("chrY", leaves(12)), ("plasmidP", leaves(3))], one), str(nuc), one,
                  labels=["chrX", "chrY", "plasmidP"])
    # a "mitochondrion": a small all-stick (plasmid-scale) genome
    mito = root / "mito.genome"
    G.genome_save(G.plasmid([("mt1", leaves(2)), ("mt2", leaves(3))], one), str(mito), one, labels=["mt1", "mt2"])

    print("=== census_one(nucleus) ===")
    for k, v in census_one(nuc, one).items():
        print(f"  {k}: {v}")
    print("\n=== census_root(cell) — total genomes + each one's role ===")
    r = census_root(root, one)
    print(f"  n_genomes: {r['n_genomes']}")
    for g in r["genomes"]:
        print(f"  - {Path(g['path']).name:16} {g['n_chromosomes']} chromosomes {g['types']} -> {g['topology']}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:                                     # census a real genome dir (or a root of genomes)
        one = hdc.klein4_random(64, seed=0)
        target = Path(sys.argv[1])
        out = census_root(target, one) if not is_genome_dir(target) else census_one(target, one)
        import json
        print(json.dumps(out, indent=2, default=str))
        sys.exit(0)
    sys.exit(_demo())
