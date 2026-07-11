r"""R-RBS-LM-CHEMBLINDSPOT (#226) — the rulesets-vs-dataset blind-spot ratchet for the CHEM kernel (same method as
MATHBLINDSPOT): run understand_chem over real enwiki <ce>/<chem> blocks + \ce{...}-in-math, measure coverage, and
CENSUS the failures — blocks that yield NO species (hard parse failure) and the \commands appearing in chem context
that the kernel does not handle. Not training; pure coverage measurement (the F819 gapmap discipline per-kernel).

srmech 0.9.0rc209. No numpy, no Python abs builtin, no Counter, no CAD. Run in the background:
  MAX_ARTICLES=40000 /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-CHEMBLINDSPOT_...py
"""
import bz2, importlib.util, os, re, sys, time
import xml.etree.ElementTree as ET
from pathlib import Path

DUMP = str(Path.home() / "corpora" / "wikipedia" / "enwiki-latest-pages-articles.xml.bz2")
N = int(os.environ.get("MAX_ARTICLES", "40000"))
_CE_TAG = re.compile(r"<(?:ce|chem)\b[^>]*>(.*?)</(?:ce|chem)>", re.S | re.I)
_CE_CMD = re.compile(r"\\ce\s*\{")                     # \ce{...} inside <math>: balanced-brace scan below
_CMD = re.compile(r"\\([a-zA-Z]+)")
KNOWN_CMD = set(("ce chem longrightarrow rightarrow to longleftrightarrow rightleftharpoons uparrow downarrow gas sld "
                 "alpha beta gamma Delta delta quad").split())


def _brace_span(s, i):
    depth, j = 0, i
    while j < len(s):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def _extract_ce_in_math(raw):
    out = []
    for cm in _CE_CMD.finditer(raw):
        inner, _ = _brace_span(raw, cm.end() - 1)
        if inner.strip():
            out.append(inner)
    return out


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    sv = sys.argv; sys.argv = ["x"]
    try: spec.loader.exec_module(mod)
    except SystemExit: pass
    sys.argv = sv; return mod


K = _load("chemk", "docs/srmech/rbs_lm_research/R-RBS-LM-CHEMKERNEL_ce_reaction_notation_sublanguage_reaction_graph.py")


def main():
    t0 = time.time()
    blocks = 0; with_species = 0; with_reaction = 0; hard_fail = 0
    unknown = {}; fails = []
    n = 0
    with bz2.open(DUMP, "rt", encoding="utf-8") as fh:
        for _e, el in ET.iterparse(fh, events=("end",)):
            if (el.tag.endswith("}text") or el.tag == "text") and el.text:
                n += 1; raw = el.text
                srcs = _CE_TAG.findall(raw) + _extract_ce_in_math(raw)
                for b in srcs:
                    if len(b) > 4000:
                        continue
                    blocks += 1
                    r = K.understand_chem(b)
                    if r["species"]:
                        with_species += 1
                    else:
                        hard_fail += 1
                        if len(fails) < 20:
                            fails.append(" ".join(b.split())[:80])
                    if r["reactions"]:
                        with_reaction += 1
                    for cmd in _CMD.findall(b):
                        if cmd not in KNOWN_CMD:
                            unknown[cmd] = unknown.get(cmd, 0) + 1
                if n >= N:
                    el.clear(); break
            el.clear()
    print(f"=== CHEMBLINDSPOT — ruleset-vs-dataset <ce> coverage ({n} articles, {blocks:,} chem exprs, {time.time()-t0:.0f}s) ===\n")
    print(f"  COVERAGE: >=1 species {with_species:,}/{blocks:,} = {100*with_species/max(1,blocks):.0f}%   "
          f">=1 reaction {with_reaction:,} = {100*with_reaction/max(1,blocks):.0f}%   HARD-FAIL (0 species) {hard_fail:,} = "
          f"{100*hard_fail/max(1,blocks):.0f}%")
    print("\n  TOP-30 unhandled \\commands in chem context (blind spots — bond/annotation notation):")
    top = sorted(unknown.items(), key=lambda kv: -kv[1])[:30]
    for i in range(0, len(top), 3):
        print("    " + "   ".join(f"\\{c:<14} {n:>6}" for c, n in top[i:i + 3]))
    print("\n  sample HARD-FAIL blocks (0 species — parse gaps to inspect):")
    for f in fails[:12]:
        print(f"     | {f}")


if __name__ == "__main__":
    main()
