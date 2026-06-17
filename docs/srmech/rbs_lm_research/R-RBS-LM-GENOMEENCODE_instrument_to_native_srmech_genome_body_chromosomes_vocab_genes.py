r"""R-RBS-LM-GENOMEENCODE (F833) — build-once encoder: the F817 token instrument -> a SINGLE native srmech genome
(srmech.amsc.genome), so siona ships ONE integrity-checked native file instead of a loose NDJSON+JSON-index pair
(F829's "native file-management, not loose kernels"; PKG-3).

STATUS: DEFERRED (F833 / UPSTREAM_NOTES §55). The design here (fiber id-stream, not spatial HV-per-token) is correct
and recalls exactly, but the genome format walls at corpus scale on three axes — 4× lane-inflation (2-bit lane stored
as a byte), O(n²) `genome_pack`/`genome_explode` in chromosome count (this script's stage→pack path is itself O(n²)),
and a ~6 GB all-in-RAM build. siona rc1 ships on the loose instrument; this is the fiber encoder to revive once §55
(bit-packed leaves + a non-quadratic high-chromosome pack) lands upstream. Kept as the verified design artifact.

STORE THE FIBER, NOT THE SPATIAL PROJECTION (F833 correction, user-caught). A first cut stored leaf(token) — a full
DIM=64 Klein-4 HV — at EVERY token position: 64.3 bytes/token, 11x the raw text, ~4.4 GB for the corpus. That is the
SPATIAL projection of each token (its coordinate in Klein-4 space), not the relationships. Per the project's "fiber
as spatially-absent encoding" stance, leaf(token) = klein4_random(seed=hash(token)) is a deterministic PROJECTION of
the token — recomputable, so persisting it per position is redundant. We store the FIBER (the relational content):
the vocab codebook once + a per-body token-ID stream. The HV projection is recomputed on demand at inference.

Layout:
  * `__vocab__` chromosome: the sorted distinct-token codebook, BYTE-PACKED into Klein-4 leaves (16 bytes/leaf, 2
    bits/lane at DIM=64). The bridge decodes it -> the id->token table (and its length fixes the id width).
  * one chromosome per body: chromosome-LABEL = sha256(title.lower())[:16].hex() (length-immune; titles can exceed
    the 63-byte label cap); leaves = the body's token-ID stream (each id = fixed-width big-endian, width =
    bytes(len(vocab)-1)), byte-packed. ~2 bytes/token — SMALLER than the 5.8-byte text (a repeat costs an id, not
    its letters). The genome stores the SEQUENCE (the order IS the relationships); the de Bruijn walk shape is a
    derived view, regenerable from the sequence, not a separate store.

Recall is exact-by-readback. Lowercased-title duplicates (e.g. "GNOME"/"Gnome" -> "gnome") match the F817 index's
last-wins contract (pass 1 keeps each key's last line; each key emitted once).

SCALING (F833): `genome_append` is O(n)/call (O(n^2) total), so we build in BATCHES — each batch built in-RAM
(`genome()` + `genome_save`) and `genome_explode`d into a shared loose `.chr` dir; one final `genome_pack` (O(n))
seals the corpus into ONE native genome. O(n) time, RAM bounded by the batch. No per-token Klein-4 work (we pack ids,
not HVs), so it is also far faster than the spatial-projection cut.

Usage:  python R-RBS-LM-GENOMEENCODE_*.py --out <genome_dir> [--limit N] [--batch 20000]
srmech 0.8.1 (live, MIT). No abs(); no hashlib (sha256_raw); no CAD. Composes F817/F818/F823/F826/F829/F831/F832.
"""
import argparse
import json
import shutil
import time
from pathlib import Path

from srmech.amsc import genome as g, hdc
from srmech.amsc.format import sha256_raw

DIM = 64
VOCAB_LABEL = "__vocab__"
INST = Path.home() / "corpora" / "wikipedia" / "simplewiki_rawbody_instrument.ndjson"


def the_one():
    return hdc.klein4_random(DIM, seed=0)


def body_key(title):
    """A length-immune chromosome label for a body (titles can exceed the 63-byte label cap)."""
    return sha256_raw(title.lower().encode())[:16].hex()


def id_width(n_vocab):
    """Fixed byte width to hold any id in [0, n_vocab-1]."""
    return max(1, ((max(1, n_vocab) - 1).bit_length() + 7) // 8)


def pack_bytes(data):
    """bytes -> list of 64-lane Klein-4 leaves (16 bytes/leaf; a 4-byte big-endian length header disambiguates pad)."""
    blob = len(data).to_bytes(4, "big") + data
    blob += b"\x00" * ((-len(blob)) % 16)
    leaves = []
    for i in range(0, len(blob), 16):
        lanes = []
        for byte in blob[i:i + 16]:
            lanes += [(byte >> 6) & 3, (byte >> 4) & 3, (byte >> 2) & 3, byte & 3]
        leaves.append(lanes)
    return leaves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="genome output directory")
    ap.add_argument("--limit", type=int, default=0, help="encode only the first N bodies (0 = all)")
    ap.add_argument("--batch", type=int, default=20000, help="bodies built in-RAM per stage before explode")
    ap.add_argument("--inst", default=str(INST))
    args = ap.parse_args()
    import srmech
    print(f"=== R-RBS-LM-GENOMEENCODE — instrument -> native srmech genome, FIBER (id-stream) not spatial-HV (srmech {srmech.__version__}) ===")
    one = the_one()
    out = Path(args.out)
    loose = out.parent / (out.name + "_loose")
    if loose.exists():
        shutil.rmtree(loose)
    loose.mkdir(parents=True)

    def stage(kernels):
        labels = [lbl for lbl, _ in kernels]
        tmp = out.parent / (out.name + "_stage")
        if tmp.exists():
            shutil.rmtree(tmp)
        g.genome_save(g.genome(kernels=kernels, the_one=one), str(tmp), one, labels)
        for _ in g.genome_explode(str(tmp), str(loose), the_one=one):
            pass
        shutil.rmtree(tmp)

    # pass 1: distinct vocab + key -> LAST line (lowercased-title dupes -> last-wins, matching the F817 index)
    t0 = time.time()
    vocab, last_line, n_lines = set(), {}, 0
    with open(args.inst) as f:
        for i, line in enumerate(f):
            rec = json.loads(line)
            vocab.update(rec["s"].split())
            last_line[body_key(rec["t"])] = i
            n_lines += 1
            if args.limit and n_lines >= args.limit:
                break
    vocab = sorted(vocab)
    tid = {t: i for i, t in enumerate(vocab)}
    w = id_width(len(vocab))
    print(f"pass1: {n_lines} records, {len(last_line)} distinct title-keys, {len(vocab)} distinct tokens, id_width={w} — {time.time()-t0:.1f}s")

    # vocab codebook chromosome
    t1 = time.time()
    blob = "\n".join(vocab).encode("utf-8")
    stage([(VOCAB_LABEL, pack_bytes(blob))])
    print(f"staged __vocab__ ({len(blob)/1e6:.2f} MB blob) — {time.time()-t1:.1f}s")

    # pass 2: stage each body as a byte-packed token-ID stream (emit each key once, at its last line)
    t2, batch, done = time.time(), [], 0
    with open(args.inst) as f:
        for i, line in enumerate(f):
            if args.limit and i >= args.limit:
                break
            rec = json.loads(line)
            key = body_key(rec["t"])
            if last_line[key] != i:
                continue
            ids = b"".join(tid[tok].to_bytes(w, "big") for tok in rec["s"].split())
            batch.append((key, pack_bytes(ids)))
            if len(batch) >= args.batch:
                stage(batch)
                done += len(batch)
                batch = []
                print(f"  staged {done}/{len(last_line)} bodies — {time.time()-t2:.1f}s")
    if batch:
        stage(batch)
        done += len(batch)
    print(f"pass2: staged {done} body chromosomes — {time.time()-t2:.1f}s")

    # final pack: seal the loose .chr dir into ONE native genome (O(n) single pass)
    t3 = time.time()
    g.genome_pack(str(loose), str(out), the_one=one)
    shutil.rmtree(loose)
    nbytes = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"pack: sealed {done + 1} chromosomes into {out} — {time.time()-t3:.1f}s")
    print(f"DONE: genome {nbytes/1e6:.1f} MB ({nbytes/max(1,done):.0f} bytes/body) | total {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
