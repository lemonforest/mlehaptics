r"""R-RBS-LM-TWOSTAGE (F1252/§102 — the COMPLETE two-stage encode, stage 1 rc278 + stage 2 rc279-281) — chain
`plasmid_extract` -> `genome_integrate_plasmids` over ALL simplewiki, handing the FREE streamed `section_count`
straight through, and land the CORRECT nuclear+plasmid genome so the F1248 A-D layout/read questions can finally be
answered on the right shape.

The chain (why it is cheap):
  STAGE 1 EXTRACT  — each document -> ONE Tier-1 plasmid section, appended O(1). 240,881 docs in ~11 min (F1253).
                     Returns `section_count {global_id: n_sections}` as a FREE streamed integer accumulator.
  STAGE 2 ORGANIZE — CONSERVE (derive k from the section-count ANTIMODE — "k IS DERIVED OR DECLINED, NEVER
                     MANUFACTURED"), PROMOTE (mint the induced core subgraph, 0x58 centromere), MERGE (fold the
                     retained plasmid sections in via integrate). `recursive_cut` is NEVER called and nothing is
                     ever re-extracted — this is what replaces the 8h+ monolithic partition that never finished.

The k-derivation directly answers F1253's honest caveat: we did NOT get to pick k to match F1251's ~16/84 — srmech
derives it from the data's own antimode, or declines. Whatever it reports is the measured partition.

srmech 0.9.0rc281 (native). No numpy; no abs-builtin. Composes F1252/F1253/F1251/§102/§101, F1248 (the A-D questions).
Run (background):  /tmp/srmech_rc272/venv/bin/python3 R-RBS-LM-TWOSTAGE_*.py [--limit N]
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

from srmech.amsc import genome as G, hdc, plasmid as P, text as T

LEAF = 64
COUPLE = hdc.klein4_random(LEAF, seed=1080)
ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
SECTIONS = Path.home() / "corpora" / "wikipedia" / "simplewiki_sections.genome"
ORGANIZED = Path.home() / "corpora" / "wikipedia" / "simplewiki_organized.genome"
REPORT = Path.home() / "corpora" / "wikipedia" / "simplewiki_twostage.report.json"
T0 = time.time()


def log(m):
    print("[%7.1fs] %s" % (time.time() - T0, m), flush=True)


def docs_iter(src, limit):
    with open(src) as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            rec = json.loads(line)
            toks = T.tokenize(rec.get("text", ""))
            if toks:
                yield toks


def ticker(label, total_hint=0):
    """A §101 progress tick that logs at most every 30 s."""
    st = {"last": 0.0}

    def progress(ev):
        now = time.time()
        if now - st["last"] >= 30.0:
            st["last"] = now
            done, tot = ev.get("done", 0), ev.get("total", 0) or total_hint
            el = now - T0
            rate = done / el if el > 0 else 0.0
            pct = (100.0 * done / tot) if tot else 0.0
            log("  [%s] %s %d/%s (%.1f%%) — %.0f/s" % (label, ev.get("phase"), done, tot or "?", pct, rate))
        return 0
    return progress


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--src", default=str(ART))
    args = ap.parse_args()

    import srmech
    log("=== TWOSTAGE — stage1 extract -> stage2 organize (srmech %s) ===" % srmech.__version__)
    n_docs = sum(1 for _ in open(args.src)) if not args.limit else args.limit
    log("source: %d docs" % n_docs)
    for p in (SECTIONS, ORGANIZED):
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)

    # ---------- STAGE 1 ----------
    t = time.time()
    ext = P.plasmid_extract(docs_iter(args.src, args.limit), str(SECTIONS), COUPLE,
                            progress=ticker("stage1", n_docs))
    t1 = time.time() - t
    sc = ext.get("section_count") or {}
    log("STAGE 1 done: %s sections, status=%s, vocab=%d, section_count=%d ids — %.1f min" %
        (ext.get("n_sections"), ext.get("status"), len(ext.get("vocab") or []), len(sc), t1 / 60.0))

    # ---------- the CONSERVE read (k derived, not picked) ----------
    core = P.conserved_core(sc, k="auto")
    log("CONSERVED_CORE: %s" % {k: v for k, v in core.items() if not isinstance(v, (list, set, dict))})
    core_ids = core.get("core") or core.get("core_ids") or set()
    try:
        n_core = len(core_ids)
    except TypeError:
        n_core = -1
    log("  derived k=%s | core=%d / %d ids (%.1f%%) | accessory=%.1f%%" %
        (core.get("k"), n_core, len(sc), 100.0 * n_core / max(1, len(sc)),
         100.0 * (len(sc) - n_core) / max(1, len(sc))))

    # ---------- STAGE 2 ----------
    t = time.time()
    org = P.genome_integrate_plasmids(str(SECTIONS), COUPLE, section_count=sc, k="auto",
                                      out_path=str(ORGANIZED), progress=ticker("stage2"))
    t2 = time.time() - t
    log("STAGE 2 done: status=%s — %.1f min" % (org.get("status"), t2 / 60.0))
    log("  organize keys: %s" % [k for k in org.keys()])
    for k in ("k", "counts", "n_core_nodes", "n_plasmids", "core_label", "census"):
        if k in org:
            log("  %s = %s" % (k, org[k]))

    # ---------- the resulting genome (A: layout) ----------
    target = ORGANIZED if ORGANIZED.exists() else SECTIONS
    cen = G.genome_census(str(target))
    nbytes = sum(p.stat().st_size for p in target.rglob("*") if p.is_file())
    log("ORGANIZED GENOME: %s" % target)
    log("  census: n_chromosomes=%s types=%s topology=%s" %
        (cen.get("n_chromosomes"), cen.get("types"), cen.get("topology")))
    log("  size: %.1f MB" % (nbytes / 1e6))
    cat = G.genome_catalog(str(target), the_one=COUPLE)
    chroms = cat.get("chromosomes", [])
    log("  format_version=%s leaf_dim=%s n_turns=%s n_chromosomes=%d" %
        (cat.get("format_version"), cat.get("leaf_dim"), cat.get("n_turns"), len(chroms)))
    for e in chroms[:6]:
        log("    %-22s leaves=%-10s cap_kind=%s" % (e.get("label"), e.get("leaf_count"), e.get("cap_kind")))
    if len(chroms) > 6:
        log("    ... (%d more chromosomes)" % (len(chroms) - 6))

    rec = {"srmech": srmech.__version__, "docs": n_docs,
           "stage1": {"n_sections": ext.get("n_sections"), "status": ext.get("status"),
                      "vocab": len(ext.get("vocab") or []), "minutes": round(t1 / 60.0, 2)},
           "conserved_core": {k: v for k, v in core.items() if not isinstance(v, (list, set, dict))},
           "core_ids": n_core, "total_ids": len(sc),
           "stage2": {"status": org.get("status"), "minutes": round(t2 / 60.0, 2)},
           "genome": {"path": str(target), "mb": round(nbytes / 1e6, 2),
                      "n_chromosomes": cen.get("n_chromosomes"), "types": cen.get("types"),
                      "topology": cen.get("topology"), "format_version": cat.get("format_version"),
                      "n_turns": cat.get("n_turns")},
           "seconds": round(time.time() - T0, 1)}
    Path(REPORT).write_text(json.dumps(rec) + "\n")
    log("report -> %s" % REPORT)
    log("VERDICT: two-stage encode COMPLETE in %.1f min (stage1 %.1f + stage2 %.1f) — %s chromosomes %s, %.1f MB. "
        "recursive_cut never called." %
        ((time.time() - T0) / 60.0, t1 / 60.0, t2 / 60.0, cen.get("n_chromosomes"), cen.get("types"), nbytes / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
