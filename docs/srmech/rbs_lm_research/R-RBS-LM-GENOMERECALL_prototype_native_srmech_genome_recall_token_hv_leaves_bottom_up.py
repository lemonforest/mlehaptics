r"""R-RBS-LM-GENOMERECALL (F832) — bottom-up PROOF that siona's full-body recall can ride srmech's NATIVE genome
file-management (PKG-3), exact, on the live MIT srmech 0.8.1.

Bottom-up introspection (the load-bearing facts, verified, not assumed):
  * `srmech.amsc.genome` is a Klein-4 HV store: a chromosome's leaves MUST be length-DIM klein4 HVs (int-vector
    leaves error: "klein4_bind: lengths must match"); genome_save -> genome_window -> recall round-trips the leaves
    EXACTLY (window returns the_one-COUPLED leaves; you MUST recall() to un-couple — using window output directly is
    the bug). DIM=64 here (siona's the_one width).
  * So the recall design: store each body as its ORDERED sequence of token-HV leaves (one leaf = leaf(token), a
    deterministic klein4 HV; injective at DIM=64 -> a reverse-map HV->token is exact). genome_window pages ONE body
    (RAM bounded), recall un-couples -> the body's HVs in order -> reverse-map -> the tokens. The genome STORES the
    full ordered sequence, so recall is exact-by-readback — no de Bruijn walk needed (the walk was the NDJSON shape
    compression; the genome is storage+retrieval, F826's thesis literal).

Consequence for EC-recall: under full-sequence genome storage there is NO de Bruijn non-unique-branch tail to
error-correct (recall is exact readback). So triality 2-of-3 (F826) is NOT branch-disambiguation here; its coherent
role is CORRUPTION-correction (encode each body's leaves as the order-3 triality orbit -> 2-of-3 recover a flipped/
erased leaf), a 3x-storage robustness tier ON TOP of the genome's existing cap_sha256 integrity. Optional, not needed
for exactness.

Cost (DIM=64): ~800 MB for the full corpus (2x the token NDJSON; the HV blowup is only catastrophic at large DIM —
124 GB at DIM=10000). Latency ~50 us/token (tomato 390 tok 21 ms; france 3275 tok 174 ms) — fine for interactive
recall. The remaining wrinkle is the VOCAB: reverse-map needs the token STRINGS; store them natively as a vocab
chromosome-set (gene label = token, leaf = leaf(token)) so genome_catalog's labels rebuild the reverse-map — no
loose text side-channel.

srmech 0.8.1 (live, MIT). No abs(); no CAD. Composes F818/F823 (the de Bruijn / klein4-walk recall), F826 (genome =
storage+retrieval; triality), F829 (genome persistence is srmech-core), F831 (0.8.1 floor). Verified output in the
finding R-RBS-LM-FINDING_832.
"""
import json
import tempfile
import time

from srmech.amsc import genome as g, hdc
from srmech.amsc.format import sha256_raw

DIM = 64
INST = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument.ndjson"
IDX = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_index.json"
_LEAF = {}


def _seed(s):
    return int.from_bytes(sha256_raw(s.encode())[:8], "big")


def leaf(tok):
    if tok not in _LEAF:
        _LEAF[tok] = hdc.klein4_random(DIM, seed=_seed(tok))   # deterministic, injective at DIM=64
    return _LEAF[tok]


def main():
    import srmech
    print(f"=== R-RBS-LM-GENOMERECALL — native srmech-genome full-body recall, bottom-up (srmech {srmech.__version__}) ===\n")
    one = hdc.klein4_random(DIM, seed=0)
    idx = json.load(open(IDX))
    bodies = {}
    with open(INST) as f:
        for nm in ("tomato", "art", "france"):
            f.seek(idx[nm])
            bodies[nm] = json.loads(f.readline())["s"].split()

    vocab = sorted({t for toks in bodies.values() for t in toks})
    rev = {tuple(leaf(t)): t for t in vocab}                   # HV -> token (exact; injective check below)
    print(f"vocab {len(vocab)} | reverse-map injective: {len(rev) == len(vocab)}")

    d = tempfile.mkdtemp()
    strand = g.genome(kernels=[(nm, [leaf(t) for t in toks]) for nm, toks in bodies.items()], the_one=one)
    g.genome_save(strand, d, one, list(bodies))
    print("genome_catalog:", [c["label"] for c in g.genome_catalog(d, the_one=one)["chromosomes"]])

    for nm, toks in bodies.items():
        t0 = time.time()
        hvs = g.recall(g.genome_window(d, nm, the_one=one), one)   # page ONE body -> un-couple
        recov = [rev[tuple(h)] for h in hvs]                       # HVs -> tokens (the genome stores the sequence)
        print(f"  {nm:7s} n={len(toks):4d} native-genome recall EXACT: {recov == toks} | {(time.time() - t0) * 1000:.1f} ms")


if __name__ == "__main__":
    main()
