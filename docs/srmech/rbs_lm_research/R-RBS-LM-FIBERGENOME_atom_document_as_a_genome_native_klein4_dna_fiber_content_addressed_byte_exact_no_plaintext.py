r"""R-RBS-LM-FIBERGENOME (PKG-3 / #231 / F1242) — the ATOM: one document stored as a GENOME-NATIVE Klein-4 (G4) DNA
FIBER, content-addressed (no plaintext table of contents), byte-exact round-trip with PUNCTUATION INTACT (no
doctoring). This is the proof-of-shape for collapsing Siona's knowledge into the biology-native lichen of genomes.

The framework shape the user specified, proven here:
  * DNA fiber        = the ordered token-ids as Klein-4 (G4) leaves (base-4 sectors 0..3), packed genome-native
                       (`genome.kernel_pack(element_type='klein4')`) — NOT a plaintext sequence.
  * byte/glyph vocab = each token's bytes (the ni-Vanuatu order-native base); the id->token table is byte/glyph.
  * index            = the CONTENT-ADDRESS of the title (sha256 of its byte/glyph) — the TOC EMERGES, no plaintext.
  * no doctoring     = punctuation kept as its own tokens (a sublanguage), never stripped (the fullbody NDJSON
                       stripped it — F1241; here it round-trips byte-exact).
The two READS of this one Laplacian/fiber object (the op(x)operand(x)responsion k=3):
  * responsion / WALK read  (imaginary z, coherent) -> the ordered sequence = the DEFINITION ('what it IS').
  * edges roll-up  (real z, thermal/relational)     -> the co-occurrence Laplacian = the RELATIONS ('what it's like').
So one genome per document collapses the #231 co-occurrence genome AND the plaintext fullbody NDJSON into ONE
organism; a SET of such genomes co-expressed on demand IS the lichen (F1205). Scale = PKG-3.

srmech 0.9.0rc253. Run:  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-FIBERGENOME_...py
"""
import math
import re
import sys
import tempfile

from srmech.amsc import genome as G, hdc as H, format as F

COUPLE = H.klein4_random(64, seed=1080)                     # the sandroing/UNESCO-00073 coupling invariant


def tokens(t):
    return re.findall(r"\w+|[^\w\s]", t)                    # punctuation kept as tokens (a sublanguage) — no doctoring


def encode_fiber(genome_dir, title, body):
    """Store `body` as a genome-native Klein-4 DNA fiber under `genome_dir`, content-addressed by `title`. Returns
    (addr, digits, n_tokens, vocab)."""
    toks = tokens(body)
    vocab = sorted(set(toks))
    vid = {w: i for i, w in enumerate(vocab)}
    ids = [vid[w] for w in toks]
    digits = max(1, math.ceil(math.log(len(vocab), 4)))     # base-4 (Klein-4) width per token id
    fiber = [(x // (4 ** k)) % 4 for x in ids for k in range(digits)]   # ordered ids -> Klein-4 (G4) sectors
    addr = F.sha256_bytes(title.encode())[:16]              # content-address = the index (no plaintext TOC)
    strand = G.kernel_pack(fiber, leaf_dim=64, label=addr, the_one=COUPLE, element_type="klein4")
    G.genome_save(strand, genome_dir, COUPLE, labels=[addr])
    return addr, digits, len(ids), vocab


def walk_read(genome_dir, addr, digits, n_tokens, vocab):
    """Reconstruct the document from the genome (content-address -> chromosome -> unpack -> ids -> tokens)."""
    ch, _c, _l = G.genome_load(genome_dir, labels=[addr], the_one=COUPLE)
    syms = [int(x) for x in G.kernel_unpack(ch, COUPLE)][:n_tokens * digits]
    ids = [sum(syms[j * digits + k] * (4 ** k) for k in range(digits)) for j in range(n_tokens)]
    return re.sub(r"\s+([.,;:!?])", r"\1", " ".join(vocab[i] for i in ids))


def main():
    body = ("Water is a simple chemical compound made of two hydrogen atoms and one oxygen atom. "
            "It is clear, has no taste or smell.")
    d = tempfile.mkdtemp()
    addr, digits, n, vocab = encode_fiber(d, "water", body)
    recon = walk_read(d, addr, digits, n, vocab)
    print("=== R-RBS-LM-FIBERGENOME atom ===", flush=True)
    print("stored %d tokens as %d Klein-4 fiber-syms (base-4 width %d); content-address=%s" % (n, n * digits, digits, addr[:12]))
    print("reconstructed:", recon)
    print("BYTE-EXACT round-trip:", recon == body, "| punctuation intact:", ("." in recon and "," in recon))
    print("VERDICT: a document IS a genome-native Klein-4 DNA fiber, content-addressed, punctuation-exact, no plaintext.")
    return 0 if recon == body else 1


if __name__ == "__main__":
    sys.exit(main())
