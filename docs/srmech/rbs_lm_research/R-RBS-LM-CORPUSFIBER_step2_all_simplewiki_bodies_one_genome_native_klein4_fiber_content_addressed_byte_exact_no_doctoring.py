r"""R-RBS-LM-CORPUSFIBER (PKG-3 / #231 / Siona ADR step 2) — encode the ENTIRE simplewiki (all ~240,881 FULL article
bodies) into ONE genome-native Klein-4 (G4) DNA fiber store: one content-addressed chromosome per body + one
`__vocab__` codebook chromosome. This COLLAPSES the loose plaintext NDJSON instrument + its JSON index into a single
attested native srmech genome (`srmech.amsc.genome`). It is the corpus-scale run of the proven R-RBS-LM-FIBERGENOME
atom, and the enactment of the siona ADRs:

  * ADR-0001  genome-native, not plaintext — the store IS the encoding (a fiber genome), no plaintext NDJSON.
  * ADR-0003  no plaintext TOC — the index IS the content-address `sha256(title)[:16]` (Class A); the vocab is a
              chromosome, not a JSON sidecar.
  * ADR-0005  byte/glyph, NO DOCTORING — tokenise the RAW article text with `\w+|\s+|[^\w\s]` so word-runs,
              whitespace-runs AND punctuation/markup are ALL kept as tokens; `"".join(tokens)` reproduces the source
              BYTE-EXACT. (The old F814/F817 instrument stripped markup + lowercased + `[a-z0-9]+` — doctoring; not
              reused here. This reads `articles.jsonl` directly.)
  * ADR-0002  the fiber IS the responsion/ordered read ("what it IS"); the co-occurrence Laplacian is the edges read.
  * ADR-0006  this simplewiki genome is ONE organism of the lichen (a peer genome co-expressed on demand).

Design (the verified F833 R-RBS-LM-GENOMEENCODE layout, un-doctored + streamed):
  * STORE THE FIBER, NOT THE SPATIAL PROJECTION — persist the vocab codebook once + a per-body token-ID stream; the
    Klein-4 HV of a token is a deterministic projection recomputed on demand, never stored per position (F833).
  * `__vocab__` chromosome — the sorted distinct-token codebook, TLV-framed (4-byte length + utf-8 per token, so a
    token may itself contain `\n`), byte-packed into 64-lane Klein-4 leaves (16 bytes/leaf, 2 bits/lane). Its length
    fixes the id width. Recovered FROM the genome (no plaintext).
  * one chromosome per body — LABEL = `sha256(title.lower())[:16].hex()` (length-immune content-address; lowercase =
    the F817 last-wins dedup contract); leaves = the body's token-ID stream (each id = fixed-width big-endian), byte-
    packed. Self-describing: pack_bytes writes a 4-byte length header, so n_tokens = len(id_bytes)/id_width on read.

Scale: `genome_append` is O(1)-per-call at srmech rc257+ WHEN the returned catalog is THREADED (§95.3/§95.5) — the v12
head-only manifest tail-extends turns.bin + updates the threaded catalog in place (no O(n) rebuild), leaves bit-packed
(~0.25 B/symbol). So we STREAM one body at a time (RAM-bounded, no batch/explode/pack). Per-body cost is the coupling
of ~400 leaves + the per-call turns.bin/manifest write (~30 ms/body, I/O-bound but FLAT in chromosome count). Recall is
exact-by-readback; verified on a sample every run.

Usage:  python R-RBS-LM-CORPUSFIBER_*.py --out <genome_dir> [--limit N] [--verify K] [--src articles.jsonl]
srmech 0.9.0rc265 (venv). No ALU magnitude-builtin; sha256 via sha256_raw; no CAD. Composes F833/F1241/F1242 + §95.3/§95.5 + siona ADR-0001..0006.
"""
import argparse
import json
import shutil
import time
from pathlib import Path

from srmech.amsc import genome as g, hdc
from srmech.amsc.format import sha256_raw
import re

DIM = 64
VOCAB_LABEL = "__vocab__"
ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
TOK = re.compile(r"\w+|\s+|[^\w\s]")           # byte-exact partition: word-run | whitespace-run | one other char


def the_one():
    return hdc.klein4_random(DIM, seed=0)       # the held invariant (F833 seed=0), content-addressed into the manifest


def toks(text):
    return TOK.findall(text)                     # "".join(toks(text)) == text, byte-exact, no doctoring (ADR-0005)


def body_key(title):
    return sha256_raw(title.lower().encode())[:16].hex()   # content-address = the index (Class A / ADR-0003)


def id_width(n_vocab):
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


def unpack_bytes(flat):
    """the pack_bytes inverse: flat 64-lane symbols -> the original bytes (via the 4-byte length header)."""
    raw = bytes(((flat[i * 4] & 3) << 6) | ((flat[i * 4 + 1] & 3) << 4) | ((flat[i * 4 + 2] & 3) << 2) | (flat[i * 4 + 3] & 3)
                for i in range(len(flat) // 4))
    n = int.from_bytes(raw[:4], "big")
    return raw[4:4 + n]


def tlv(tokens):
    out = bytearray()
    for w in tokens:
        b = w.encode("utf-8")
        out += len(b).to_bytes(4, "big") + b
    return bytes(out)


def untlv(blob):
    out, p = [], 0
    while p < len(blob):
        n = int.from_bytes(blob[p:p + 4], "big")
        p += 4
        out.append(blob[p:p + n].decode("utf-8"))
        p += n
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="genome output directory (a DIRECTORY)")
    ap.add_argument("--limit", type=int, default=0, help="encode only the first N records (0 = all)")
    ap.add_argument("--verify", type=int, default=200, help="byte-exact round-trip check on the first K bodies")
    ap.add_argument("--src", default=str(ART))
    ap.add_argument("--report", default="", help="optional path to write a JSON measurement record")
    args = ap.parse_args()
    import srmech
    print(f"=== R-RBS-LM-CORPUSFIBER — simplewiki -> ONE genome-native Klein-4 fiber (srmech {srmech.__version__}) ===", flush=True)
    one = the_one()
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)

    # pass 1 — global vocab (byte-exact tokens, incl whitespace/punct) + last-line dedup by content-address
    t0 = time.time()
    vocab, last_line, n_lines, empties = set(), {}, 0, 0
    with open(args.src) as f:
        for i, line in enumerate(f):
            if args.limit and n_lines >= args.limit:
                break
            rec = json.loads(line)
            tk = toks(rec["text"])
            if not tk:
                empties += 1
            vocab.update(tk)
            last_line[body_key(rec["title"])] = i
            n_lines += 1
    vocab = sorted(vocab)
    tid = {t: k for k, t in enumerate(vocab)}
    w = id_width(len(vocab))
    t_p1 = time.time() - t0
    print(f"pass1: {n_lines} records, {len(last_line)} distinct title-keys, {len(vocab)} distinct tokens, "
          f"id_width={w}, {empties} empty-body — {t_p1:.1f}s", flush=True)

    # seed the genome with the __vocab__ codebook chromosome (TLV -> byte-packed); KEEP the returned catalog to THREAD
    t1 = time.time()
    vblob = tlv(vocab)
    cat = g.genome_save(g.genome([(VOCAB_LABEL, pack_bytes(vblob))], one), str(out), one, labels=[VOCAB_LABEL])
    print(f"seed: __vocab__ chromosome ({len(vblob) / 1e6:.2f} MB TLV blob) — {time.time() - t1:.1f}s", flush=True)

    # pass 2 — STREAM each body (last-wins) as a byte-packed token-ID stick chromosome via O(1) genome_append.
    # rc257+ (§95.3/§95.5): genome_append is O(1)/call when the returned catalog is threaded — no batch/explode/pack.
    t2, done = time.time(), 0
    verify_raw = {}
    with open(args.src) as f:
        for i, line in enumerate(f):
            if args.limit and i >= args.limit:
                break
            rec = json.loads(line)
            key = body_key(rec["title"])
            if last_line[key] != i:          # emit each content-address once, at its last occurrence
                continue
            text = rec["text"]
            ids = b"".join(tid[t].to_bytes(w, "big") for t in toks(text))
            cat = g.genome_append(str(out), key, pack_bytes(ids), one, catalog=cat)   # O(1) — thread the catalog
            if len(verify_raw) < args.verify:
                verify_raw[key] = text
            done += 1
            if done % 20000 == 0:
                print(f"  appended {done}/{len(last_line)} bodies — {time.time() - t2:.1f}s "
                      f"({1000 * (time.time() - t2) / done:.2f} ms/body)", flush=True)
    t_p2 = time.time() - t2
    print(f"pass2: appended {done} body chromosomes (O(1) stream) — {t_p2:.1f}s ({1000 * t_p2 / max(1, done):.2f} ms/body)", flush=True)

    nbytes = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"disk: genome {nbytes / 1e6:.1f} MB ({nbytes / max(1, done):.0f} bytes/body)", flush=True)

    # verify — recover the vocab FROM the genome (no plaintext), decode the sample, compare BYTE-EXACT to raw text
    ch, _a, _b = g.genome_load(str(out), labels=[VOCAB_LABEL], the_one=one)
    rvocab = untlv(unpack_bytes([int(x) for x in g.kernel_unpack(ch, one)]))
    vocab_ok = (rvocab == vocab)
    exact = 0
    for key, text in verify_raw.items():
        ch, _a, _b = g.genome_load(str(out), labels=[key], the_one=one)
        idb = unpack_bytes([int(x) for x in g.kernel_unpack(ch, one)])
        recon = "".join(rvocab[int.from_bytes(idb[j:j + w], "big")] for j in range(0, len(idb), w))
        exact += (recon == text)
    print(f"verify: vocab recovered byte-exact={vocab_ok}; bodies byte-exact {exact}/{len(verify_raw)}", flush=True)

    verdict = vocab_ok and exact == len(verify_raw)
    print(f"VERDICT: {'PASS' if verdict else 'FAIL'} — {done} bodies collapsed into ONE genome-native Klein-4 fiber, "
          f"content-addressed, punctuation+whitespace byte-exact, no plaintext.", flush=True)

    if args.report:
        rec = {"srmech": srmech.__version__, "records": n_lines, "bodies": done, "vocab": len(vocab),
               "id_width": w, "empties": empties, "pass1_s": round(t_p1, 2), "pass2_s": round(t_p2, 2),
               "ms_per_body": round(1000 * t_p2 / max(1, done), 3), "genome_mb": round(nbytes / 1e6, 2),
               "bytes_per_body": round(nbytes / max(1, done), 1), "verify_bodies": len(verify_raw),
               "verify_exact": exact, "vocab_ok": vocab_ok, "verdict": "PASS" if verdict else "FAIL"}
        Path(args.report).write_text(json.dumps(rec) + "\n")
        print("report ->", args.report, flush=True)
    return 0 if verdict else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
