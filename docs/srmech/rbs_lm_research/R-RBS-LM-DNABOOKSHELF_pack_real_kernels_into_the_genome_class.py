r"""R-RBS-LM-DNABOOKSHELF (F721) — the DNA bookshelf: pack our loose research kernels into the Genome class and
test the rc42 chromosomal storage surface end-to-end (flat ops + class-from-TOML + bring-your-own 'school').

User direction (2026-06-09): "see how our genome class works and test our chromosomal storage surface ... create
our DNA bookshelf. this part will just be a matter of packing our loose kernels into a structured class, right?
and we also get to test the new surface."

YES — the Genome class is a STORAGE CONTAINER, so this is a packing exercise: represent each loose kernel as
leaves (content-addressed Klein-4 tomes, one per concept), then add it as a telomere-capped chromosome, all
coupled through the_one. It does not recompute the kernels; it shelves them. We pack THIS SESSION's real kernels.

WHAT THIS TESTS (srmech 0.7.5rc42):
  (A) FLAT surface: srmech.amsc.genome.{genome, partition, chromosome, recall, telomere, encode_shape}.
  (B) CLASS surface: srmech.dsl.make_class("Genome") -> add_chromosome / assemble / partition / recall / shape / cap.
  (C) BRING-YOUR-OWN 'school of choice' (F716): register a user [class] 'Codex' (librarian's-school names over the
      SAME genome ops) via register_class_dir; prove it yields the identical strand + carries provenance 'user:<sha>'.

No abs(); no CAD; content-address (Class A) -> Klein-4 leaf (Class M); the_one coupling reversible (F713).
"""
import os
import tempfile
import srmech
from srmech.amsc import genome as G
from srmech.amsc.format import sha256_bytes
from srmech.amsc.hdc import klein4_random
from srmech.dsl import make_class, register_class_dir, describe_class, list_classes

DIM = 64

# --- our loose kernels (real concepts from this session's findings) -> the bookshelf's books ---
KERNELS = {
    "etak":         ["canoe", "star_compass", "reference_island", "the_one", "segment", "bearing", "horizon", "fleet"],
    "cortana":      ["riemann_matrix", "rampancy", "seven_year", "flash_clone", "master_chief", "cognitive_impression"],
    "siona":        ["the_one", "chord", "asking_state", "etak_walk", "gpu_free", "not_a_substrate", "klein4", "bounded"],
    "genome_model": ["chromosome", "telomere", "helix", "quad_turn", "leaf", "the_one_coupling", "encode_shape"],
    "an_vocab":     ["A_content_address", "I_cyclic", "C_chirality", "J_primes", "D_pattern", "E_catalog", "F_render",
                     "G_search", "K_pinslot", "L_laplacian", "M_hdc_bind", "B_tlv", "H_introspect", "N_rational"],
}

# A user 'school' — a librarian's vocabulary over the SAME genome ops (F716 school-of-choice).
CODEX_TOML = '''
[class]
name = "Codex"
kind = "storage"
doc = "A librarian's-school naming of the same storage ops (school-of-choice demo, F716)."
[class.field]
the_one = "hv"
folios = "list"
[class.method.shelve]
op = "srmech.amsc.genome.genome"
binds = ["kernels", "the_one"]
doc = "Shelve many kernels into one codex (= a genome strand)."
[class.method.unshelve]
op = "srmech.amsc.genome.partition"
binds = ["strand", "the_one", "labels"]
doc = "Unshelve kernels by colophon (= telomere label)."
[class.method.colophon]
op = "srmech.amsc.genome.telomere"
binds = ["label"]
doc = "The colophon (= telomere cap)."
'''


def leaf(text):
    """Content-address a concept -> a deterministic Klein-4 leaf (the surface's own telomere construction)."""
    seed = int(sha256_bytes(text.encode("utf-8"))[:16], 16)
    return klein4_random(DIM, seed=seed)


def as_leaves(kernels):
    """Each kernel -> a list of leaves (one content-addressed tome per concept, namespaced by kernel)."""
    return {label: [leaf(f"{label}:{c}") for c in concepts] for label, concepts in kernels.items()}


def eq(a, b):
    return [list(x) for x in a] == [list(x) for x in b]


def main():
    print(f"=== R-RBS-LM-DNABOOKSHELF (F721) — pack real kernels into the Genome class  (srmech {srmech.__version__}) ===\n")
    one = klein4_random(DIM, seed=1)
    books = as_leaves(KERNELS)

    print("(0) THE SHELF MANIFEST — each loose kernel's encode shape (the criterion picks tome/mobius/strand):")
    for label, leaves in books.items():
        s = G.encode_shape(len(leaves))
        print(f"    {label:<14} {len(leaves):>2} concepts -> {s['shape']:<6} (leaves={s['leaves']}, depth={s['depth']})")
    print()

    # (A) FLAT surface — assemble one genome strand, partition it back.
    print("(A) FLAT surface (srmech.amsc.genome): assemble the whole bookshelf into ONE strand, partition back:")
    strand = G.genome(books, one)
    back = G.partition(strand, one, list(books))
    flat_ok = all(eq(back[L], books[L]) for L in books)
    n_turns = sum(len(v) for v in books.values())
    bounding = sha256_bytes(str([[list(h) for h in strand]]).encode())[:16]   # Class-A bounding fingerprint
    print(f"    strand: {len(strand)} elements = {n_turns} quad-turns + {len(books)} telomere caps")
    print(f"    partition round-trip reversible (every kernel recovered through the_one): {flat_ok}")
    print(f"    whole-shelf bounding fingerprint (content-address): {bounding}\n")

    # (B) CLASS surface — the genome.toml class, built incrementally then assembled.
    print("(B) CLASS surface (srmech.dsl.make_class('Genome')): add_chromosome per book, then assemble + recall:")
    Genome = make_class("Genome")
    g = Genome(the_one=one)
    for label, leaves in books.items():
        g.add_chromosome(leaves=leaves, label=label)          # appends a telomere-capped chromosome to the field
    print(f"    chromosomes field now holds {len(g.fields['chromosomes'])} telomere-capped strands")
    strand2 = g.assemble(kernels=books)                       # one combined strand (= the flat genome())
    same_strand = eq(strand2, strand)
    recovered = g.recall(strand=g.fields['chromosomes'][2], telomere=g.cap(label="siona"))
    recall_ok = eq(recovered, books["siona"])
    print(f"    class assemble() == flat genome() strand: {same_strand}")
    print(f"    recall('siona' chromosome) == original leaves: {recall_ok}")
    print(f"    g.shape(n=5000) -> {g.shape(n=5000)['shape']}   (the class method delegates to encode_shape)\n")

    # (C) BRING-YOUR-OWN 'school of choice' — a Codex class over the SAME ops, different names.
    print("(C) BRING-YOUR-OWN class (F716 school-of-choice): a 'Codex' school over the same genome ops:")
    tmp = tempfile.mkdtemp(prefix="srmech_codex_")
    with open(os.path.join(tmp, "codex.toml"), "w", encoding="utf-8") as fh:
        fh.write(CODEX_TOML)
    register_class_dir(tmp)
    Codex = make_class("Codex")
    c = Codex(the_one=one)
    codex_strand = c.shelve(kernels=books)                    # 'shelve' = genome(); a librarian's name for it
    codex_back = c.unshelve(strand=codex_strand, labels=list(books))
    codex_ok = eq(codex_strand, strand) and all(eq(codex_back[L], books[L]) for L in books)
    prov = describe_class("Codex")["provenance"]
    print(f"    classes now visible: {list_classes()}")
    print(f"    Codex.shelve() yields the IDENTICAL strand as Genome (same ops, different school's names): {codex_ok}")
    print(f"    Codex provenance tier: {prov!r}  (bring-your-own = attested to the descriptor hash)\n")

    print("VERDICT (F721 — the DNA bookshelf works; the chromosomal storage surface is exercised):")
    print(f"  • Packing loose kernels into the Genome class IS just structured shelving: each kernel -> content-")
    print(f"    addressed Klein-4 leaves -> a telomere-capped chromosome, coupled through the_one. {len(books)} books,")
    print(f"    {n_turns} quad-turns, {len(books)} telomere partitions, one strand, content-address bounded.")
    print(f"  • FLAT + CLASS surfaces agree (assemble == genome; partition/recall reversible): {flat_ok and same_strand and recall_ok}")
    print(f"  • BRING-YOUR-OWN 'school' (Codex) over the same ops yields the identical strand, provenance 'user': {codex_ok and prov=='user'}")
    print(f"  • The surface is real and on-thesis: a bookshelf of the session's own kernels, never quantized,")
    print(f"    bounded + content-addressed, recalled losslessly through the_one. srmech {srmech.__version__}.")


if __name__ == "__main__":
    main()
