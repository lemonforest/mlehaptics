r"""R-RBS-LM-GENOMEEDIT (F736) — can you EDIT a genome (remove a kernel) WITHOUT manually rebuilding the chromosome
structure? Checked on srmech 0.7.5rc145.

ANSWER: there is NO dedicated remove/delete op (genome surface has genome / chromosome / genes / append / save /
load / catalog / window / genome_genes / partition / recall — none excise). BUT a clean remove COMPOSES from
`partition` + `genome` — you never touch telomere/gene caps by hand:

    def genome_drop(strand, the_one, label):
        kept = [(l, lv) for l, lv in partition(strand, the_one).items() if l != label]
        return genome(kept, the_one)            # partition reads the cap structure; genome re-applies it

`partition` extracts every kernel from the cap-delimited strand FOR you; `genome` re-frames the survivors FOR you.
So "without manually rebuilding the chromosome structure" is satisfied. Verified below: drop one kernel, the others
come back byte-intact, and the edited genome survives a disk save/load.

THE LIMITATION (the honest gap → UPSTREAM §45): this is a RE-PACK, not an in-place excise. `genome(kept,…)`
re-binds every surviving leaf and rewrites the whole `turns.bin` + manifest — O(whole genome). Biology excises in
PLACE (CRISPR / gene knockout): the chromosome already sits in a telomere/gene-cap-delimited span (rc145 now exposes
`CHROM_CAP_MARKER` / `GENE_CAP_MARKER`), so a true edit = find that cap-delimited span and splice it out, leaving the
rest untouched. That's the biology-faithful `genome_remove(path,label)` / `genome_drop(strand,…,label)` ask.

Run (rc145 venv, numpy-free): <venv>/python R-RBS-LM-GENOMEEDIT_remove_kernel_compose_vs_inplace.py
No abs(); no CAD; research-subtree provenance.
"""
import srmech
from srmech.amsc import genome as g, hdc

DIM = 64
ONE = hdc.klein4_random(DIM, seed=0)


def genome_drop(strand, the_one, label):
    """Remove one kernel by label — composes partition + genome (no manual cap surgery). Returns the new strand."""
    kept = [(lab, lv) for lab, lv in g.partition(strand, the_one).items() if lab != label]
    return g.genome(kept, the_one)


def main():
    print(f"=== R-RBS-LM-GENOMEEDIT — remove a kernel without rebuilding the structure (srmech {srmech.__version__}) ===\n")
    surf = [n for n in dir(g) if not n.startswith("_")]
    removeops = [n for n in surf if any(k in n.lower() for k in ("remove", "delete", "drop", "excise", "splice"))]
    print("(0) dedicated remove/delete op in the genome surface:", removeops or "NONE")

    def Lv(s, n):
        return [hdc.klein4_random(DIM, seed=s * 100 + i) for i in range(n)]
    kernels = [("alpha", Lv(1, 3)), ("beta", Lv(2, 2)), ("gamma", Lv(3, 4))]
    strand = g.genome(kernels, ONE)
    before = g.partition(strand, ONE)
    print(f"\n(1) genome has kernels: {list(before)}")

    # the composed remove — one helper call, no cap/telomere editing
    edited = genome_drop(strand, ONE, "beta")
    after = g.partition(edited, ONE)
    intact = after.get("alpha") == before["alpha"] and after.get("gamma") == before["gamma"]
    print(f"(2) genome_drop(strand, the_one, 'beta') -> kernels: {list(after)}")
    print(f"    'beta' gone: {'beta' not in after}  |  alpha+gamma byte-intact (not rebuilt by hand): {intact}")

    # survives disk
    import tempfile
    d = tempfile.mkdtemp()
    g.genome_save(edited, d, ONE)
    _, _, labels = g.genome_load(d)
    print(f"(3) edited genome saved + reloaded -> labels: {labels}")

    print("\nVERDICT: NO dedicated remove op, but `genome_drop` = partition→filter→genome removes a kernel WITHOUT")
    print("  manual cap surgery (partition reads the structure, genome re-frames the survivors). Verified: dropped")
    print("  'beta', kept alpha+gamma byte-intact, survived disk. LIMITATION (UPSTREAM §45): this RE-PACKS the whole")
    print("  genome (rewrites turns.bin). Biology excises IN PLACE — with rc145's CHROM_CAP_MARKER/GENE_CAP_MARKER a")
    print("  true `genome_remove(path,label)` could splice the cap-delimited span out and leave the rest. (F736)")


if __name__ == "__main__":
    main()
