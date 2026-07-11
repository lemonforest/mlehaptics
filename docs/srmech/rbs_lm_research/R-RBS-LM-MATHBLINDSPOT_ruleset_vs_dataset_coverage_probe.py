r"""R-RBS-LM-MATHBLINDSPOT (#226) — find the LaTeX-kernel's BLIND SPOTS by running the hand-authored RULESET against a
real DATASET of math notation, WITHOUT training on it (user 2026-07-10: "look at openstax mathematic texts for our math
language, not to use it for the kernel like we learned with the grammar texts, but to find our blind spots in sparse
kernel creation from rulesets vs datasets").

METHOD (rulesets vs datasets = the relational-vs-distributional axis): the LaTeX kernel (understand_latex) is a sparse
RULESET hand-authored from ~12 samples — it WILL be blind to constructs it never saw. We do NOT fit it to data (the
dataset/distributional way). We run it over a large real LaTeX-SOURCE corpus and CENSUS what it fails to comprehend:
  * every `\command` in a real <math> block is either RECOGNIZED (in the kernel's rule sets) or falls to the generic
    'func' bucket = a BLIND SPOT. The frequency-ranked unrecognized commands ARE the missing rules (the F819 gapmap
    discipline applied to the kernel itself: a strip/fallback HIDES a missing rule — surface it, count it, add it).
  * plus coverage: what fraction of expressions yield >=1 symbol and >=1 relation.

CORPUS: enwiki <math>/{{math}} blocks — genuine LaTeX SOURCE at scale (OpenStax PDFs extract to RENDERED unicode, not
LaTeX source, so they probe CONCEPT vocabulary, not NOTATION; arXiv source is the deeper follow-up). No training; pure
coverage measurement. srmech 0.9.0rc209. No numpy, no Python abs builtin, no Counter, no CAD. Run in the background:
  MAX_ARTICLES=15000 /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-MATHBLINDSPOT_...py
"""
import bz2, importlib.util, os, re, sys, time
import xml.etree.ElementTree as ET
from pathlib import Path

DUMP = str(Path.home() / "corpora" / "wikipedia" / "enwiki-latest-pages-articles.xml.bz2")
N = int(os.environ.get("MAX_ARTICLES", "15000"))
_MATH = re.compile(r"<math\b[^>]*>(.*?)</math>", re.S | re.I)
_TMATH = re.compile(r"\{\{\s*math\s*\|(.*?)\}\}", re.S | re.I)
_CMD = re.compile(r"\\([a-zA-Z]+)")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    sv = sys.argv; sys.argv = ["x"]
    try: spec.loader.exec_module(mod)
    except SystemExit: pass
    sys.argv = sv; return mod


K = _load("latexk", "docs/srmech/rbs_lm_research/R-RBS-LM-LATEXKERNEL_math_notation_sublanguage_comprehend_not_strip.py")
# the kernel's KNOWN command vocabulary (a \cmd not in here falls through to 'func' = a blind spot)
KNOWN = set(K.GREEK) | set(K.ACCENTS) | set(K.BIG_OPS) | set(K.FMT) | {"frac", "dfrac", "tfrac", "cfrac", "text"}
KNOWN |= set(K.FUNCTIONS) | set(K.NUMSETS) | set(K.CONSTANTS) | set(K.DELIMS) | set(K.ELLIPSES)
KNOWN |= {c[1:] for c in K.RELATIONS if c.startswith("\\")}
KNOWN |= {c[1:] for c in K.BINARY if c.startswith("\\")}


def main():
    t0 = time.time()
    exprs = 0; with_sym = 0; with_rel = 0; cmd_total = 0
    unknown = {}; unknown_arts = {}
    n = 0
    with bz2.open(DUMP, "rt", encoding="utf-8") as fh:
        for _e, el in ET.iterparse(fh, events=("end",)):
            if (el.tag.endswith("}text") or el.tag == "text") and el.text:
                n += 1; raw = el.text
                blocks = _MATH.findall(raw) + _TMATH.findall(raw)
                seen_here = set()
                for b in blocks:
                    exprs += 1
                    r = K.understand_latex(b)
                    if r["symbols"]:
                        with_sym += 1
                    if r["relations"]:
                        with_rel += 1
                    for cmd in _CMD.findall(b):
                        cmd_total += 1
                        if cmd not in KNOWN:
                            unknown[cmd] = unknown.get(cmd, 0) + 1
                            seen_here.add(cmd)
                for cmd in seen_here:
                    unknown_arts[cmd] = unknown_arts.get(cmd, 0) + 1
                if n >= N:
                    el.clear(); break
            el.clear()
    print(f"=== MATHBLINDSPOT — ruleset-vs-dataset LaTeX coverage ({n} articles, {exprs:,} <math> exprs, {time.time()-t0:.0f}s) ===\n")
    print(f"  COVERAGE: expr with >=1 symbol {with_sym:,}/{exprs:,} = {100*with_sym/max(1,exprs):.0f}%   "
          f"with >=1 relation {with_rel:,} = {100*with_rel/max(1,exprs):.0f}%")
    print(f"  commands seen {cmd_total:,} | UNRECOGNIZED (blind spots) {sum(unknown.values()):,} = "
          f"{100*sum(unknown.values())/max(1,cmd_total):.0f}% of command tokens | distinct unknown {len(unknown):,}\n")
    print("  TOP-45 BLIND SPOTS (unrecognized \\command by frequency) = the missing rules to add:")
    top = sorted(unknown.items(), key=lambda kv: -kv[1])[:45]
    for i in range(0, len(top), 3):
        row = top[i:i + 3]
        print("    " + "   ".join(f"\\{c:<14} {n:>6}" for c, n in row))
    print("\n  READ: high per-token recognized fraction = the ruleset covers the common notation; the ranked unknown"
          "\n  commands are the systematic blind spots (add them to GREEK/RELATIONS/BINARY/BIG_OPS/FMT/functions).")


if __name__ == "__main__":
    main()
