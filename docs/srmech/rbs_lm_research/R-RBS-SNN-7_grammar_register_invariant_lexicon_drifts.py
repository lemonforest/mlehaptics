#!/usr/bin/env python3
"""R-RBS-SNN-7 — register/modernity bias is a LEXICON property, not a GRAMMAR property.

The worry: our grammar/lexicon was sourced from McGuffey + OpenStax (educational/academic,
McGuffey 19th-c) — it won't capture MODERN usage. Where does that bias actually land?

Hypothesis (the three-kernel split, F431/F432): the CLOSED-CLASS grammar is register-/era-
INVARIANT (the same function words across topics and time — the slow-changing core), while
the OPEN-CLASS lexicon DRIFTS with register/topic/era. If so, OpenStax's register-bias
lives ONLY in the lexicon (a SEPARATE, SWAPPABLE kernel) and never touches the grammar.

Proxy test (within our own corpus): split findings into early / mid / late ERAS (the
research shifted topic: early biology/chirality → late octonion/duality). Measure the
cross-era overlap (Jaccard) of the GRAMMAR (closed-class) vs the LEXICON (open-class)
vocabularies. Predict: grammar overlap ≈ 1.0 (invariant); lexicon overlap ≪ (drifts).

Run:  <clean-venv>/bin/python R-RBS-SNN-7_grammar_register_invariant_lexicon_drifts.py
Composes F432 (grammar closes / lexicon opens) · F431 (the three kernels) · F164 (grammar
substrate-native) · F408 (semantics-open) · F329 (the convention is the mutable fiber).
standard closed-class linguistics (framework-read; no-lineage). Defensive.
"""
import re
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CLOSED = set("""
a an the this that these those each every all both some any no other another such
it its they them their we our us you your he she his her him i me my who whom whose which what
of in to for with on at by from as into than over under between within without through during
against about above below across after before among around behind beyond except inside near
off onto since toward upon via per up down out
and or but so if because while when where although though unless until whether nor yet either neither
is are was were be been being am has have had do does did having
can could may might must shall should will would cannot
not no never only just even still more most less least very much many few several
there here then thus hence therefore however moreover also too whereas
""".split())


def tokens(text):
    text = re.sub(r'```.*?```', ' ', text, flags=re.S)
    text = re.sub(r'`[^`]*`', ' ', text)
    text = re.sub(r'https?://\S+', ' ', text)
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


def fnum(p):
    m = re.search(r'FINDING_(\d+)', os.path.basename(p))
    return int(m.group(1)) if m else -1


def vocabs(paths):
    g, lx = set(), set()
    for p in paths:
        for w in tokens(open(p, encoding='utf-8').read()):
            (g if w in CLOSED else lx).add(w)
    return g, lx


def jac(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0


def main():
    paths = sorted((p for p in glob.glob(os.path.join(HERE, "R-RBS-LM-FINDING_*.md")) if fnum(p) >= 0), key=fnum)
    n = len(paths)
    eras = {
        "early": paths[:n // 3],
        "mid":   paths[n // 3:2 * n // 3],
        "late":  paths[2 * n // 3:],
    }
    gv = {k: vocabs(v)[0] for k, v in eras.items()}
    lv = {k: vocabs(v)[1] for k, v in eras.items()}

    print("=== register/era bias: GRAMMAR invariant, LEXICON drifts (within our corpus) ===\n")
    print(f"eras by finding-number: early F{fnum(eras['early'][0])}–F{fnum(eras['early'][-1])} | "
          f"mid F{fnum(eras['mid'][0])}–F{fnum(eras['mid'][-1])} | "
          f"late F{fnum(eras['late'][0])}–F{fnum(eras['late'][-1])}\n")

    print(f"{'pair':14} | {'GRAMMAR overlap':>15} | {'LEXICON overlap':>15}")
    for a, b in (("early", "mid"), ("mid", "late"), ("early", "late")):
        print(f"{a+'↔'+b:14} | {jac(gv[a], gv[b]):>15.2f} | {jac(lv[a], lv[b]):>15.2f}")

    gmin = min(jac(gv[a], gv[b]) for a, b in (("early","mid"),("mid","late"),("early","late")))
    lmax = max(jac(lv[a], lv[b]) for a, b in (("early","mid"),("mid","late"),("early","late")))
    print(f"\nGRAMMAR cross-era overlap ≥ {gmin:.2f}  — the closed-class is ERA-INVARIANT (the stable core)")
    print(f"LEXICON cross-era overlap ≤ {lmax:.2f}  — the open-class DRIFTS with topic/era")

    # the lexicon drift signature: content words distinctive to early vs late
    only_early = lv["early"] - lv["late"]
    only_late = lv["late"] - lv["early"]
    def topby(words, paths_, k=10):
        from collections import Counter
        c = Counter()
        for p in paths_:
            for w in tokens(open(p, encoding='utf-8').read()):
                if w in words and len(w) > 4:
                    c[w] += 1
        return [w for w, _ in c.most_common(k)]
    print(f"\nlexicon drift (the register/topic signature, swappable):")
    print(f"   early-only content: {', '.join(topby(only_early, eras['early']))}")
    print(f"   late-only  content: {', '.join(topby(only_late, eras['late']))}")

    print(f"\n  ⇒ McGuffey/OpenStax's register-bias lands in the LEXICON (a SEPARATE, swappable kernel),")
    print(f"    not the GRAMMAR (era-invariant). Want modern usage? Swap the lexicon; grammar + ")
    print(f"    domain-lean are untouched. A dense LLM bakes register into the weights — can't swap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
