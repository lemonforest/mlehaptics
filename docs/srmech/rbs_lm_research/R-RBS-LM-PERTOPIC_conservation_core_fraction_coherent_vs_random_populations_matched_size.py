r"""R-RBS-LM-PERTOPIC (F1254 follow-up) — is the 0.015 % core a LEVEL MISMATCH or an OPEN-CLASS ceiling?

F1254 measured, at whole-corpus scale (240,881 docs), a data-DERIVED k=10,714 giving a conserved core of
170 / 1,100,189 ids = 0.015 % — two orders of magnitude off F1251's attested ~16/84 in *K. pneumoniae*. Two
competing explanations:

  (H1) LEVEL MISMATCH — Shropshire's 16/84 is measured WITHIN a clonal group (CG307), a coherent lineage, not
       across all bacteria. We compared all-of-simplewiki to one clonal group. The right unit is a topically
       COHERENT population. Prediction: coherent populations show a MUCH HIGHER core fraction than random ones
       at the SAME size.
  (H2) OPEN-CLASS CEILING — word vocabulary is open-class (Heaps' law: vocab keeps growing with N) while
       bacterial gene content is effectively closed, so the accessory denominator runs away and the ratio can
       never match at ANY level. Prediction: coherent ~ random, and BOTH core fractions shrink with N.

THE DISCRIMINATOR: coherent-vs-random at MATCHED N. H1 predicts a large gap; H2 predicts little gap + a decay
in N. Both are measured here, using the REAL pipeline (`plasmid_extract` -> the free `section_count` ->
`conserved_core(k="auto")`), so `k` stays DERIVED and is never hand-picked (the F1253 discipline).

Coherent populations are the "clonal group" analog: documents sharing a marker token (a lineage marker). Note
the seed itself is trivially in 100 % of its population — one id of inflation, reported and immaterial at these
vocab sizes.

srmech 0.9.0rc281. No numpy; no abs-builtin. Composes F1254/F1253/F1251/F1250, §102.
Run (background):  /tmp/srmech_rc272/venv/bin/python3 R-RBS-LM-PERTOPIC_*.py
"""
import json
import random
import shutil
import sys
import time
from pathlib import Path

from srmech.amsc import hdc, plasmid as P, text as T

LEAF = 64
COUPLE = hdc.klein4_random(LEAF, seed=1080)
ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
TMP = Path("/tmp/pertopic_pops")
REPORT = Path.home() / "corpora" / "wikipedia" / "simplewiki_pertopic.report.json"
SEEDS = ["music", "football", "species", "river"]     # topical lineage markers (common enough to fill buckets)
SIZES = [100, 300, 1000, 3000]
MAXN = max(SIZES)
SCAN_CAP = 150000                                      # stop scanning once buckets fill (or at this many docs)
T0 = time.time()


def log(m):
    print("[%7.1fs] %s" % (time.time() - T0, m), flush=True)


def collect():
    """ONE pass: fill a random bucket + one bucket per topical seed (docs containing that marker)."""
    rng = random.Random(1080)
    buckets = {("coherent", s): [] for s in SEEDS}
    buckets[("random", None)] = []
    seedset = set(SEEDS)
    scanned = 0
    with open(ART) as f:
        for line in f:
            if scanned >= SCAN_CAP:
                break
            rec = json.loads(line)
            toks = T.tokenize(rec.get("text", ""))
            if not toks:
                continue
            scanned += 1
            if len(buckets[("random", None)]) < MAXN and rng.random() < 0.10:
                buckets[("random", None)].append(toks)
            present = seedset.intersection(toks)
            for s in present:
                b = buckets[("coherent", s)]
                if len(b) < MAXN:
                    b.append(toks)
            if all(len(v) >= MAXN for v in buckets.values()):
                break
    log("scanned %d docs; bucket sizes: %s" % (scanned, {("%s:%s" % (k[0], k[1] or "-")): len(v)
                                                         for k, v in buckets.items()}))
    return buckets


def measure(docs, label):
    """Run the REAL pipeline on this population -> derived k + core fraction."""
    store = TMP / ("pop_" + label.replace(":", "_"))
    if store.exists():
        shutil.rmtree(store, ignore_errors=True)
    ext = P.plasmid_extract(iter(docs), str(store), COUPLE)
    sc = ext.get("section_count") or {}
    core = P.conserved_core(sc, k="auto")
    n_core = core.get("n_core", 0)
    vocab = len(sc)
    shutil.rmtree(store, ignore_errors=True)
    return {"label": label, "n_docs": len(docs), "vocab": vocab, "k": core.get("k"),
            "k_source": core.get("k_source"), "bimodal": core.get("bimodal"),
            "n_core": n_core, "core_pct": round(100.0 * n_core / max(1, vocab), 4),
            "gap": core.get("gap")}


def main():
    import srmech
    log("=== PER-TOPIC conservation test (srmech %s) — coherent vs random at matched N ===" % srmech.__version__)
    TMP.mkdir(parents=True, exist_ok=True)
    buckets = collect()

    rows = []
    for (kind, seed), docs in sorted(buckets.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")):
        for n in SIZES:
            if len(docs) < n:
                continue
            label = "%s:%s@%d" % (kind, seed or "-", n)
            t = time.time()
            r = measure(docs[:n], label)
            r["kind"], r["seed"], r["seconds"] = kind, seed, round(time.time() - t, 1)
            rows.append(r)
            log("  %-26s vocab=%-7d k=%-6s bimodal=%-5s core=%-5d (%.4f%%)" %
                (label, r["vocab"], r["k"], r["bimodal"], r["n_core"], r["core_pct"]))

    # ---- the discriminator: coherent vs random at matched N ----
    log("")
    log("=== DISCRIMINATOR — core %% at matched N (H1 level-mismatch predicts a LARGE coherent>random gap) ===")
    log("  %-8s %-12s %-12s %s" % ("N", "random", "coherent(mean)", "ratio"))
    for n in SIZES:
        rnd = [r for r in rows if r["kind"] == "random" and r["n_docs"] == n]
        coh = [r for r in rows if r["kind"] == "coherent" and r["n_docs"] == n]
        if not rnd or not coh:
            continue
        r0 = rnd[0]["core_pct"]
        c0 = sum(r["core_pct"] for r in coh) / len(coh)
        log("  %-8d %-12.4f %-12.4f %.2fx" % (n, r0, c0, (c0 / r0) if r0 else float("inf")))

    # ---- the Heaps / open-class check: does vocab keep growing with N? ----
    log("")
    log("=== OPEN-CLASS CHECK (H2) — vocab growth + core%% decay with N (random populations) ===")
    for n in SIZES:
        rnd = [r for r in rows if r["kind"] == "random" and r["n_docs"] == n]
        if rnd:
            log("  N=%-6d vocab=%-8d core=%-5d core%%=%.4f" % (n, rnd[0]["vocab"], rnd[0]["n_core"], rnd[0]["core_pct"]))
    log("  (whole corpus, F1254: N=240881 vocab=1100189 core=170 core%%=0.0155)")

    REPORT.write_text(json.dumps({"srmech": srmech.__version__, "seeds": SEEDS, "sizes": SIZES,
                                  "rows": rows, "seconds": round(time.time() - T0, 1)}) + "\n")
    log("report -> %s" % REPORT)
    log("VERDICT: see the discriminator table — a large coherent>random gap supports H1 (level mismatch); "
        "similar values with core%% decaying in N support H2 (open-class ceiling).")
    shutil.rmtree(TMP, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
