r"""R-RBS-LM-CORE170 (F1255 §"Structural read" — the cheap NEXT) — are F1254's 170 conserved-core tokens the
ACYCLIC function-word spine, i.e. is the nuclear core provably ZERO-CURVATURE at glyph scale?

F1254 derived (never picked) k=10,714 from the section-count antimode and got a conserved core of
170 / 1,100,189 ids. F1255 then measured that a word's glyph-level "direction" is PURE GAUGE (endianness) iff
its glyph graph is acyclic, and that the corpus splits 49.08 % of TYPES / 66.47 % of TOKENS gauge-only.

THE QUESTION: are those two partitions the SAME partition seen twice? If the 170 are the short, glyph-distinct
function words, then the minted NUCLEAR CORE carries no glyph-scale curvature at all, and every bit of
glyph-level which-way lives in the plasmid ACCESSORY tail.

  H-same : the 170 are ~all acyclic (>> the 49.08 % baseline)  -> core == gauge, accessory == curvature
  H-diff : the 170 sit near the 49.08 % baseline               -> the two partitions are independent

METHOD — `section_count` IS document frequency (the count of sections/documents an id appears in), so it is
recomputable in ONE cheap streaming pass instead of a 22 h `section_counts()` re-derivation (F1253) or a
genome round-trip (the organized genome has no vocab chromosome, F1254). Keying the histogram by TOKEN rather
than global-id changes nothing about the antimode, and hands back the core as words directly.

RATCHET (this is the point of doing it this way): a faithful recomputation MUST reproduce F1254 exactly --
vocab = 1,100,189, derived k = 10,714, n_core = 170. Those three are asserted, not assumed. If they do not
reproduce, the tokenization drifted and the whole read is void.

srmech 0.9.0rc281. Integers only; no floats mid-cascade. Composes F1255 (the gauge decomposition, imported
verbatim), F1254 (the derived core), F1253, F1251, #231/PKG-3.
Run:  /tmp/srmech_rc272/venv/bin/python3 R-RBS-LM-CORE170_*.py
"""
import importlib.util as iu
import json
import sys
import time
from pathlib import Path

from srmech.amsc import plasmid as P, text as T

HERE = Path(__file__).resolve().parent
ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
REPORT = Path.home() / "corpora" / "wikipedia" / "simplewiki_core170.report.json"
# F1254's lodged numbers — the ratchet
EXPECT = {"vocab": 1100189, "k": 10714, "n_core": 170}
BASELINE_TYPE_ACYCLIC_PCT = 49.08          # F1255, all types
T0 = time.time()


def log(m):
    print("[%6.1fs] %s" % (time.time() - T0, m), flush=True)


def _load_gauge():
    """Import F1255's decomposition verbatim — same code, not a re-implementation."""
    path = next(HERE.glob("R-RBS-LM-GAUGE_*.py"))
    spec = iu.spec_from_file_location("rbs_gauge", path)
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    import srmech
    G = _load_gauge()
    log("=== CORE170 — is the conserved core the acyclic spine? (srmech %s) ===" % srmech.__version__)

    # ---------- document frequency == section_count, one streaming pass ----------
    df = {}
    n_docs = 0
    with open(ART) as f:
        for line in f:
            toks = T.tokenize(json.loads(line).get("text", ""))
            if not toks:
                continue
            n_docs += 1
            for t in set(toks):                       # SET: document frequency, one vote per document
                df[t] = df.get(t, 0) + 1
    log("streamed %d documents -> vocab %d" % (n_docs, len(df)))

    # ---------- the ratchet: must reproduce F1254 ----------
    # conserved_core requires INTEGER ids. Our own id assignment is fine: the antimode is computed over the
    # HISTOGRAM OF COUNTS, which is identical to srmech's whenever the vocab matches (asserted below).
    tok_of = sorted(df)
    id_of = {t: i for i, t in enumerate(tok_of)}
    sc = {id_of[t]: c for t, c in df.items()}
    core = P.conserved_core(sc, k="auto")
    core_toks = sorted(tok_of[int(i)] for i in (core.get("core") or core.get("core_ids") or []))
    got = {"vocab": len(df), "k": core.get("k"), "n_core": len(core_toks)}
    log("derived: k=%s (%s) bimodal=%s gap=%s | core=%d / %d" %
        (core.get("k"), core.get("k_source"), core.get("bimodal"), core.get("gap"), len(core_toks), len(df)))
    ok = all(got[key] == EXPECT[key] for key in EXPECT)
    for key in EXPECT:
        log("  ratchet %-8s expected %-9s got %-9s %s" %
            (key, EXPECT[key], got[key], "OK" if got[key] == EXPECT[key] else "*** DRIFT ***"))
    if not ok:
        log("RATCHET FAILED — tokenization drifted from F1254; the read below would not be comparable. STOP.")
        return 1

    # ---------- the measurement: gauge-decompose the core ----------
    acyc = curv = cyc_flat = 0
    rows = []
    for w in core_toks:
        order, edges, charges = G.glyph_graph(w)
        if not edges:
            acyc += 1
            rows.append((w, 0, 0, "acyclic"))
            continue
        b1, nh, mh, _ = G.gauge_decompose(len(order), edges, charges)
        if nh:
            curv += 1
            rows.append((w, b1, nh, "CURVATURE"))
        elif b1 == 0:
            acyc += 1
            rows.append((w, b1, 0, "acyclic"))
        else:
            cyc_flat += 1
            rows.append((w, b1, 0, "cyclic-zero-holonomy"))

    n = max(1, len(core_toks))
    pct_gauge = 100.0 * (acyc + cyc_flat) / n
    log("")
    log("--- the %d conserved-core tokens, gauge-decomposed ---" % len(core_toks))
    log("  acyclic (endianness only)      %3d  (%.2f%%)" % (acyc, 100.0 * acyc / n))
    log("  cyclic but zero holonomy       %3d  (%.2f%%)" % (cyc_flat, 100.0 * cyc_flat / n))
    log("  GENUINE CURVATURE              %3d  (%.2f%%)" % (curv, 100.0 * curv / n))
    log("")
    log("  core PURE GAUGE = %.2f%%   vs all-types baseline %.2f%%  (F1255)" %
        (pct_gauge, BASELINE_TYPE_ACYCLIC_PCT))

    log("")
    log("  the core tokens (curvature-bearing marked *):")
    line = []
    for w, b1, nh, verdict in rows:
        line.append(("*" + w) if verdict == "CURVATURE" else w)
        if len(line) == 12:
            log("    " + " ".join(line))
            line = []
    if line:
        log("    " + " ".join(line))

    # ---------- THE CONTROL: is the enrichment just LENGTH? ----------
    # Common words are short (Zipf's law of abbreviation) and short words are acyclic by topology, so a
    # length-matched control decides whether "conserved-core membership" explains anything beyond length.
    import random
    by_len = {}
    for w in df:
        by_len.setdefault(len(w), []).append(w)
    rng = random.Random(1080)
    trials, ctrl_pcts = 20, []
    for _ in range(trials):
        sample, g = [], 0
        for w in core_toks:
            pool = by_len.get(len(w))
            if pool:
                sample.append(rng.choice(pool))
        for w in sample:
            order, edges, charges = G.glyph_graph(w)
            if not edges:
                g += 1
                continue
            b1, nh, _, _ = G.gauge_decompose(len(order), edges, charges)
            if nh == 0:
                g += 1
        ctrl_pcts.append(100.0 * g / max(1, len(sample)))
    ctrl_mean = sum(ctrl_pcts) / len(ctrl_pcts)
    ctrl_lo, ctrl_hi = min(ctrl_pcts), max(ctrl_pcts)
    log("")
    log("--- CONTROL: length-matched random tokens (%d trials) ---" % trials)
    log("  core            PURE GAUGE = %.2f%%" % pct_gauge)
    log("  length-matched  PURE GAUGE = %.2f%%  (range %.2f–%.2f over %d trials)" %
        (ctrl_mean, ctrl_lo, ctrl_hi, trials))
    log("  all-types baseline         = %.2f%%" % BASELINE_TYPE_ACYCLIC_PCT)
    explained = "LENGTH ALONE explains it" if ctrl_lo <= pct_gauge <= ctrl_hi else \
                "core membership adds signal BEYOND length"
    log("  => %s" % explained)

    verdict = ("H-same: the core IS the gauge-only spine" if pct_gauge >= 90.0 else
               "H-diff: the core tracks the corpus baseline — independent partitions"
               if pct_gauge < BASELINE_TYPE_ACYCLIC_PCT + 15.0 else
               "PARTIAL: core is gauge-enriched but not gauge-pure")
    log("")
    log("VERDICT: %s" % verdict)

    REPORT.write_text(json.dumps({
        "srmech": srmech.__version__, "n_docs": n_docs, "vocab": len(df),
        "k": core.get("k"), "k_source": core.get("k_source"), "n_core": len(core_toks),
        "ratchet_ok": ok, "core_tokens": core_toks,
        "acyclic": acyc, "cyclic_zero_holonomy": cyc_flat, "curvature": curv,
        "core_pure_gauge_pct": round(pct_gauge, 2),
        "length_matched_control_pct": round(ctrl_mean, 2),
        "length_matched_control_range": [round(ctrl_lo, 2), round(ctrl_hi, 2)],
        "length_explains": explained,
        "baseline_all_types_acyclic_pct": BASELINE_TYPE_ACYCLIC_PCT,
        "curvature_bearing": [w for w, _, _, v in rows if v == "CURVATURE"],
        "verdict": verdict, "seconds": round(time.time() - T0, 1)}) + "\n")
    log("report -> %s" % REPORT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
