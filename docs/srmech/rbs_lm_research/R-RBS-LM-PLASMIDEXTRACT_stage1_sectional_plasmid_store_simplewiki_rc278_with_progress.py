r"""R-RBS-LM-PLASMIDEXTRACT (F1252 §102 STAGE 1, delivered rc278) — stream ALL simplewiki articles into an APPEND-ONLY
SECTIONAL PLASMID store: each article → ONE Tier-1 plasmid chromosome (its LOCAL window co-occurrence graph, §89
kernel chromosome, GLOBAL node-ids, no centromere), appended O(1). This REPLACES the monolithic path that ran 8+ hours
blind and was lost whole to a power outage.

Why this shape (F1252/§102, now shipped):
  * EXTRACT-ONCE + APPEND — adding a document appends ONE bounded plasmid section; never re-extract dense→graph-L.
    Retires the loose monolithic `simplewiki_directed_sparse_kernel.json` (~916 MB) at the graph-L layer.
  * CHECKPOINTED — each section is a COMPLETE chromosome the moment it lands; an interruption costs one section, not
    the whole run (the power-outage lesson: the monolithic genome_from_graph wrote only at the end → 8 h lost whole).
  * VISIBLE + CANCELLABLE — the rc275 §101 progress tick (phase=EXTRACTING, exact int done/total; nonzero return
    cancels cleanly at a section boundary, leaving no partial section).
  * STAGE 2 (rc279) then PROMOTES by CONSERVATION — `section_counts` gives {global_id: n_sections}; a node conserved
    across >= k sections becomes NUCLEAR (minted). A plain integer accumulator — NO spectral solve. That is F1251's
    attested biology (core genome = conserved across isolates; accessory = variable) giving the cheap algorithm.

srmech 0.9.0rc278 (native). No numpy; no abs-builtin. Composes F1252/§102, F1251, F1247, §101, #231.
Run (background):  /tmp/srmech_rc272/venv/bin/python3 R-RBS-LM-PLASMIDEXTRACT_*.py [--limit N]
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

from srmech.amsc import hdc, plasmid as P, text as T

LEAF = 64                                   # >= 52 required (the §89 kernel header fits one leaf)
COUPLE = hdc.klein4_expand(LEAF, 1080)  # the store's canonical coupling seed
ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
OUT = Path.home() / "corpora" / "wikipedia" / "simplewiki_sections.genome"
REPORT = Path.home() / "corpora" / "wikipedia" / "simplewiki_sections.report.json"
T0 = time.time()


def log(m):
    print("[%7.1fs] %s" % (time.time() - T0, m), flush=True)


def docs_iter(src, limit):
    """Stream articles.jsonl -> token sequences (srmech-native tokenizer, consistent with cooccurrence_topk)."""
    with open(src) as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            rec = json.loads(line)
            toks = T.tokenize(rec.get("text", ""))
            if toks:
                yield toks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--src", default=str(ART))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--window", type=int, default=2)
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--verify-counts", action="store_true",
                    help="re-derive section_counts as an SSoT check (SLOW: ~0.33 s/section)")
    args = ap.parse_args()

    import srmech
    log("=== PLASMIDEXTRACT stage 1 — sectional plasmid store (srmech %s) ===" % srmech.__version__)
    n_docs = sum(1 for _ in open(args.src)) if not args.limit else args.limit
    log("source: %s (%d docs) -> %s" % (args.src, n_docs, args.out))
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out, ignore_errors=True)

    # the §101 heartbeat we have been missing: exact ints, phase, and a cancel channel.
    state = {"last": 0.0, "done": 0}

    def progress(ev):
        state["done"] = ev.get("done", 0)
        now = time.time()
        if now - state["last"] >= 30.0:                      # log at most every 30 s
            state["last"] = now
            done = ev.get("done", 0)
            el = now - T0
            rate = done / el if el > 0 else 0.0
            eta = (n_docs - done) / rate if rate > 0 else 0.0
            log("  %s %d/%d (%.1f%%) — %.0f docs/s, ETA %.0f min" %
                (ev.get("phase"), done, n_docs, 100.0 * done / max(1, n_docs), rate, eta / 60.0))
        return 0                                             # 0 = continue (nonzero would cancel cleanly)

    t = time.time()
    info = P.plasmid_extract(docs_iter(args.src, args.limit), str(out), COUPLE,
                             window=args.window, k=args.k, progress=progress)
    dt = time.time() - t
    log("EXTRACT done: n_sections=%s status=%s vocab=%d — %.1f min (%.1f ms/doc)" %
        (info.get("n_sections"), info.get("status"), len(info.get("vocab") or []), dt / 60.0,
         1000.0 * dt / max(1, info.get("n_sections") or 1)))

    nbytes = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    from srmech.amsc import genome as G
    cen = G.genome_census(str(out))
    log("store: %.1f MB | census types=%s topology=%s n_chromosomes=%s" %
        (nbytes / 1e6, cen.get("types"), cen.get("topology"), cen.get("n_chromosomes")))

    # Conservation counts = what stage 2 (rc279) promotes on. Use the FREE streamed accumulator that
    # plasmid_extract already returns; `section_counts()` is the SSoT RE-DERIVATION (a verification re-read),
    # measured at 0.33 s/section on the smoke -> ~22 h at 240k sections, so it is opt-in only (--verify-counts).
    counts = info.get("section_count") or {}
    log("section_count (streamed accumulator, free): %d global ids" % len(counts))
    conserved = {k: sum(1 for c in counts.values() if c >= k) for k in (2, 5, 10, 25, 50, 100)}
    log("conservation (nodes appearing in >= k sections): %s" % conserved)
    if args.verify_counts:
        t = time.time()
        derived = P.section_counts(str(out), the_one=COUPLE)
        same = (derived == counts)
        log("VERIFY section_counts re-derived in %.1f min — matches the streamed accumulator? %s"
            % ((time.time() - t) / 60.0, same))

    rec = {"srmech": srmech.__version__, "docs": n_docs, "n_sections": info.get("n_sections"),
           "status": info.get("status"), "vocab": len(info.get("vocab") or []),
           "store_mb": round(nbytes / 1e6, 2), "extract_min": round(dt / 60.0, 2),
           "census": {"types": cen.get("types"), "topology": cen.get("topology")},
           "conserved_at_k": conserved, "seconds": round(time.time() - T0, 1)}
    Path(REPORT).write_text(json.dumps(rec) + "\n")
    log("report -> %s" % REPORT)
    log("VERDICT: stage-1 sectional plasmid store BUILT — %s sections, %.1f MB, %.1f min. Stage 2 (rc279) promotes "
        "conserved nodes to NUCLEAR by integer section-count, no spectral solve." %
        (info.get("n_sections"), nbytes / 1e6, dt / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
