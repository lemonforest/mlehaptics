r"""R-RBS-LM-GENOMEREAD (F729) — how the genome of kernels is READ: a simple introspection that says what lives
BETWEEN THE TELOMERES. Answers the user's question (2026-06-13).

THE IDEA (F715): a genome is a flat HELIX (one strand) of fixed-width Klein-4 leaves. Each KERNEL is one
CHROMOSOME, and each chromosome is delimited by a TELOMERE — biology's repetitive non-coding chromosome-end CAP,
here a content-address marker. So reading the genome = walk the strand; every telomere cap is a boundary; the
leaves BETWEEN two telomeres are one kernel's tomes; the chromosome's LABEL is what that stretch MEANS.

TWO ways to read, both shown:
  1. genome_catalog(path)  -> the MANIFEST: the fast Class-H "what is stored?" answer (labels, tome-counts,
     telomere cap hashes, byte ranges) WITHOUT loading the leaf body. This is the introspection.
  2. walk the raw strand    -> physically show the [TELO][leaf][leaf]…[TELO]… structure and confirm the
     leaf-counts-between-caps match the manifest. This is what "between the telomeres" literally looks like.

Run (numpy-free):  <venv>/python R-RBS-LM-GENOMEREAD_introspect_between_telomeres.py
No abs(); no CAD; research-subtree provenance.
"""
import tempfile
import srmech
import srmech.amsc.genome as g
from srmech.amsc import hdc

DIM = 64
ONE = hdc.klein4_random(DIM, seed=0)                 # the coherence-anchor leaf ("the one")

# a small DNA-bookshelf: label -> (leaves, the researcher's human gloss of what this kernel MEANS)
SHELF = {
    "siona_identity": ([hdc.klein4_random(DIM, seed=10 + i) for i in range(5)], "who Siona is — her self-identity shelf"),
    "mfo_the_one":    ([hdc.klein4_random(DIM, seed=20 + i) for i in range(3)], "the MFO 'the one is the held invariant' kernel"),
    "dragon_taught":  ([hdc.klein4_random(DIM, seed=30 + i) for i in range(2)], "a tome taught at runtime via build-by-dialogue"),
}


def main():
    print(f"=== R-RBS-LM-GENOMEREAD — reading the genome between telomeres  (srmech {srmech.__version__}) ===\n")
    kernels = [(lab, leaves) for lab, (leaves, _) in SHELF.items()]
    labels = [lab for lab, _ in kernels]
    strand = g.genome(kernels, ONE)
    d = tempfile.mkdtemp(prefix="genomeread_")
    g.genome_save(strand, d, ONE, labels)

    # (1) the MANIFEST introspection — "what is stored", without touching the leaf body
    cat = g.genome_catalog(d)
    print(f"GENOME  format v{cat['format_version']}  leaf_dim={cat['leaf_dim']}  n_turns={cat['n_turns']}")
    print(f"  body_sha256 : {cat['body_sha256'][:24]}…   (content-address of the whole helix)")
    one_sha = cat['the_one']['sha256'] if isinstance(cat.get('the_one'), dict) else '—'
    print(f"  the_one cap : {one_sha[:24]}…   (the coherence leaf every tome is bound against)\n")
    print("  BETWEEN THE TELOMERES — each row is one chromosome (= one kernel):")
    print(f"    {'telomere cap':<14} {'label':<16} {'tomes':>5}  {'byte range':<14}  meaning")
    for ch in cat["chromosomes"]:
        lab = ch["label"]
        rng = f"{ch['byte_offset']}..{ch['byte_offset'] + ch['byte_len']}"
        gloss = SHELF[lab][1]
        print(f"    {ch['cap_sha256'][:12]}…  {lab:<16} {ch['leaf_count']:>5}  {rng:<14}  {gloss}")

    # (2) walk the RAW strand to SHOW the telomere-delimited helix physically
    print("\n  THE HELIX, walked leaf-by-leaf (○ = telomere cap = boundary, · = a tome leaf):")
    s2, one2, labs = g.genome_load(d)
    caps = [(lab, g.telomere(lab, DIM)) for lab in labs]   # the cap marker for each label
    line, cur, counts = [], None, {}
    for el in s2:
        hit = next((lab for lab, cap in caps if el == cap), None)
        if hit is not None:
            cur = hit; counts[cur] = 0; line.append(f"○{hit}")
        else:
            counts[cur] = counts.get(cur, 0) + 1; line.append("·")
    print("    " + " ".join(line))
    walk_ok = all(counts[lab] == cat_ch["leaf_count"] for lab, cat_ch in zip(labs, cat["chromosomes"]))
    print(f"    leaf-counts between telomeres match the manifest: {counts} -> {walk_ok}")

    # (3) page ONE kernel back by label (the targeted read) and decode it to raw tomes
    raw = [hdc.klein4_unbind(x, ONE) for x in g.genome_window(d, "mfo_the_one")]
    print(f"\n  TARGETED READ  genome_window('mfo_the_one') -> {len(raw)} tomes; decode==stored: "
          f"{raw == SHELF['mfo_the_one'][0]}")

    # (4) CHROMOSOME INTROSPECTION — the genes WITHIN one chromosome (F730/§43; rc138 gene-frame, tag=GENE_FRAME_TAG).
    print(f"\n  CHROMOSOME INTROSPECTION — several genes WITHIN a chromosome (gene-frame tag={g.GENE_FRAME_TAG}='{chr(g.GENE_FRAME_TAG)}'):")
    chrom_genes = [("intro",   [hdc.klein4_random(DIM, seed=200 + i) for i in range(2)]),
                   ("history", [hdc.klein4_random(DIM, seed=210 + i) for i in range(3)]),
                   ("refs",    [hdc.klein4_random(DIM, seed=220 + i) for i in range(1)])]
    multi = g.chromosome(genes=chrom_genes, the_one=ONE, label="siona_identity")
    inner = g.genes(multi, ONE)
    print(f"    chromosome 'siona_identity' (strand len {len(multi)}) holds {len(inner)} genes:")
    for gl, lv in inner:
        print(f"      ⟨gene:{gl:8}⟩  {len(lv)} tomes")
    print(f"    genes() round-trips the gene-frames exact: {inner == chrom_genes}  (several kernels per chromosome — §43)")
    print("    NOTE (honest gap): this is the chromosome-LEVEL read (in-memory). genome() + the disk path do NOT")
    print("      yet accept multi-gene chromosomes (genome() re-binds each leaf and chokes on the TLV frame bytes),")
    print("      so there is no genome->disk->window->genes round-trip yet. §43 follow-up (UPSTREAM §43.1).")

    print("\nVERDICT: the genome reads as a telomere-delimited helix. genome_catalog = the 'what's stored + what it")
    print("  means' introspection (label + tome-count + cap + byte-range, body untouched); genome_window pages one")
    print("  chromosome; recall/unbind decodes the tomes. The LABEL is the meaning-key; between two telomeres is")
    print("  exactly one kernel. (F729; composes F715 genome / F721 bookshelf / §42 disk-persist.)")


if __name__ == "__main__":
    main()
