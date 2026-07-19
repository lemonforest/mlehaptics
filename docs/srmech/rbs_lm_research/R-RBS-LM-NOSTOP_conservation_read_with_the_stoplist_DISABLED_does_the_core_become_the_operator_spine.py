r"""R-RBS-LM-NOSTOP (F1256 §"the surface this exposes" — the highest-value NEXT) — re-run the conservation read
with the STOPLIST DISABLED. Does the conserved core become the OPERATOR spine, and does the core/accessory
RATIO move toward F1251's attested ~16/84?

F1256 found the whole simplewiki genome was built on a stoplisted stream: `srmech.amsc.text.tokenize` applies
`DEFAULT_STOPLIST` (146 function words) by default, so the 170-token conserved core came out as Wikipedia's
FORM/boilerplate vocabulary and the OPERATOR layer was absent from the genome entirely -- every stored
relationship is operand<->operand. Per [[feedback_no_doctoring_ssot_use_sublanguage_kernels]] a strip HIDES a
missing kernel; per [[feedback_operators_declared_operands_by_meaning]] function words ARE the operators.

TWO QUESTIONS, both measured here side-by-side in one run (each pass ~40 s):
  Q1 IDENTITY -- with `stoplist=None`, does the derived core become the operator spine (the/of/and/...)?
  Q2 RATIO    -- does core/accessory move toward the attested ~16/84, or stay at F1254's 0.015/99.985?

`k` stays DERIVED in both arms (`conserved_core(k="auto")` measures the section-count antimode) -- we do not
get to pick it, so whatever it reports is the measured partition. The stoplisted arm must reproduce F1254
exactly (vocab 1,100,189 / k 10,714 / n_core 170) or the comparison is void: that is the ratchet.

ALSO MEASURED (a tokenizer property F1256 surfaced, not assumed): raw mode still drops SINGLE-CHARACTER
tokens -- tokenize("...is on a mat", stoplist=None) has no 'a'. So "stoplist off" is not the same as "raw
text"; the one-letter operators (a, I) remain unrepresentable. Reported explicitly.

Then the F1255 gauge decomposition on the new core, with the length-matched control that killed the last
enrichment (F1256) -- because a core of short function words would be acyclic-by-length all over again.

srmech 0.9.0rc281. Composes F1256, F1255, F1254, F1253, F1251, #231/PKG-3.
Run:  /tmp/srmech_rc272/venv/bin/python3 R-RBS-LM-NOSTOP_*.py
"""
import importlib.util as iu
import json
import random
import sys
import time
from pathlib import Path

from srmech.amsc import plasmid as P, text as T

HERE = Path(__file__).resolve().parent
ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
REPORT = Path.home() / "corpora" / "wikipedia" / "simplewiki_nostop.report.json"
EXPECT_STOPPED = {"vocab": 1100189, "k": 10714, "n_core": 170}      # F1254 — the ratchet
OPERATORS = ["the", "of", "and", "a", "in", "to", "is", "was", "for", "on", "with",
             "that", "by", "as", "it", "from", "at", "he", "she", "they", "his", "her"]
T0 = time.time()


def log(m):
    print("[%6.1fs] %s" % (time.time() - T0, m), flush=True)


def _load_gauge():
    path = next(HERE.glob("R-RBS-LM-GAUGE_*.py"))
    spec = iu.spec_from_file_location("rbs_gauge", path)
    mod = iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def doc_freq(stoplist_off):
    """One streaming pass -> {token: document frequency}. section_count IS document frequency (F1253)."""
    kw = {"stoplist": None} if stoplist_off else {}
    df, n_docs = {}, 0
    with open(ART) as f:
        for line in f:
            toks = T.tokenize(json.loads(line).get("text", ""), **kw)
            if not toks:
                continue
            n_docs += 1
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
    return df, n_docs


def derive(df):
    """conserved_core with a DERIVED k (never picked), keyed back to tokens."""
    tok_of = sorted(df)
    sc = {i: df[t] for i, t in enumerate(tok_of)}
    core = P.conserved_core(sc, k="auto")
    toks = sorted(tok_of[int(i)] for i in (core.get("core") or core.get("core_ids") or []))
    return core, toks


def gauge_split(G, words):
    acyc = curv = flat = 0
    for w in words:
        order, edges, charges = G.glyph_graph(w)
        if not edges:
            acyc += 1
            continue
        b1, nh, _, _ = G.gauge_decompose(len(order), edges, charges)
        if nh:
            curv += 1
        elif b1 == 0:
            acyc += 1
        else:
            flat += 1
    return acyc, flat, curv


def main():
    import srmech
    G = _load_gauge()
    log("=== NOSTOP — conservation read with the stoplist DISABLED (srmech %s) ===" % srmech.__version__)

    arms = {}
    for label, off in (("stoplisted", False), ("raw (stoplist=None)", True)):
        t = time.time()
        df, n_docs = doc_freq(off)
        core, toks = derive(df)
        arms[label] = {"df": df, "core": core, "toks": toks, "n_docs": n_docs}
        log("%-22s docs=%d vocab=%-9d k=%-7s (%s) bimodal=%s gap=%s core=%d (%.4f%%)  [%.0fs]" %
            (label, n_docs, len(df), core.get("k"), core.get("k_source"), core.get("bimodal"),
             core.get("gap"), len(toks), 100.0 * len(toks) / max(1, len(df)), time.time() - t))

    # ---------- the ratchet ----------
    a = arms["stoplisted"]
    got = {"vocab": len(a["df"]), "k": a["core"].get("k"), "n_core": len(a["toks"])}
    ok = all(got[k] == EXPECT_STOPPED[k] for k in EXPECT_STOPPED)
    log("")
    for k in EXPECT_STOPPED:
        log("  ratchet %-8s expected %-9s got %-9s %s" %
            (k, EXPECT_STOPPED[k], got[k], "OK" if got[k] == EXPECT_STOPPED[k] else "*** DRIFT ***"))
    if not ok:
        log("RATCHET FAILED — the stoplisted arm no longer reproduces F1254; comparison void. STOP.")
        return 1

    b = arms["raw (stoplist=None)"]

    # ---------- the tokenizer property (measured, not assumed) ----------
    single = [w for w in b["df"] if len(w) == 1]
    log("")
    log("--- tokenizer property: single-character tokens in RAW mode ---")
    log("  distinct 1-char tokens in raw vocab: %d  %s" % (len(single), sorted(single)[:20]))
    log("  => 'stoplist off' is NOT 'raw text': one-letter operators stay unrepresentable if this is 0")

    # ---------- Q1: does the core become the OPERATOR spine? ----------
    core_b = set(b["toks"])
    present = [w for w in OPERATORS if w in core_b]
    in_vocab = [w for w in OPERATORS if w in b["df"]]
    log("")
    log("--- Q1 IDENTITY — is the raw-mode core the operator spine? ---")
    log("  operators in raw VOCAB : %2d/%d  %s" % (len(in_vocab), len(OPERATORS), in_vocab))
    log("  operators in raw CORE  : %2d/%d  %s" % (len(present), len(OPERATORS), present))
    log("  raw core size %d; operators are %.1f%% of it" %
        (len(core_b), 100.0 * len(present) / max(1, len(core_b))))
    log("  the raw core:")
    line = []
    for w in b["toks"]:
        line.append(w)
        if len(line) == 14:
            log("    " + " ".join(line)); line = []
    if line:
        log("    " + " ".join(line))

    # ---------- Q2: does the RATIO move? ----------
    ra = 100.0 * len(a["toks"]) / max(1, len(a["df"]))
    rb = 100.0 * len(b["toks"]) / max(1, len(b["df"]))
    log("")
    log("--- Q2 RATIO — does core/accessory move toward the attested ~16/84? ---")
    log("  %-22s core %8.4f%%  accessory %8.4f%%" % ("stoplisted (F1254)", ra, 100.0 - ra))
    log("  %-22s core %8.4f%%  accessory %8.4f%%" % ("raw (stoplist off)", rb, 100.0 - rb))
    log("  %-22s core %8.4f%%  accessory %8.4f%%" % ("attested K. pneumoniae", 16.0, 84.0))
    moved = "MOVED toward 16/84" if rb > ra * 5 else "did NOT move — still orders of magnitude off"
    log("  => %s" % moved)

    # ---------- the gauge read + the length-matched control (F1256's lesson) ----------
    acyc, flat, curv = gauge_split(G, b["toks"])
    n = max(1, len(b["toks"]))
    pct = 100.0 * (acyc + flat) / n
    by_len = {}
    for w in b["df"]:
        by_len.setdefault(len(w), []).append(w)
    rng = random.Random(1080)
    ctrl = []
    for _ in range(20):
        sample = [rng.choice(by_len[len(w)]) for w in b["toks"] if by_len.get(len(w))]
        ca, cf, cc = gauge_split(G, sample)
        ctrl.append(100.0 * (ca + cf) / max(1, len(sample)))
    cm, clo, chi = sum(ctrl) / len(ctrl), min(ctrl), max(ctrl)
    log("")
    log("--- gauge read on the raw core, WITH the length-matched control ---")
    log("  raw core        PURE GAUGE = %.2f%%  (%d acyclic, %d flat, %d curvature)" % (pct, acyc, flat, curv))
    log("  length-matched  PURE GAUGE = %.2f%%  (range %.2f–%.2f, 20 trials)" % (cm, clo, chi))
    log("  => %s" % ("LENGTH ALONE explains it" if clo <= pct <= chi else
                     "core membership adds signal BEYOND length"))

    REPORT.write_text(json.dumps({
        "srmech": srmech.__version__, "ratchet_ok": ok,
        "stoplisted": {"vocab": len(a["df"]), "k": a["core"].get("k"), "n_core": len(a["toks"]),
                       "core_pct": round(ra, 4)},
        "raw": {"vocab": len(b["df"]), "k": b["core"].get("k"), "n_core": len(b["toks"]),
                "core_pct": round(rb, 4), "core_tokens": b["toks"],
                "operators_in_vocab": in_vocab, "operators_in_core": present,
                "single_char_tokens": sorted(single)},
        "gauge": {"core_pure_gauge_pct": round(pct, 2), "control_pct": round(cm, 2),
                  "control_range": [round(clo, 2), round(chi, 2)]},
        "ratio_verdict": moved, "seconds": round(time.time() - T0, 1)}) + "\n")
    log("report -> %s" % REPORT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
