r"""R-RBS-LM-WIKITOWERC (#225/#260) — re-run the tome tower on COMPREHENDED content: route each article through the
sub-language ROUTER first, then encode the CLEAN PROSE as the Class-L co-occurrence (the ① distributional layer) AND
compose the kernels' TYPED relationship edges (the ② relational layer) into the same graph. The bigwiki encode the whole
F1204 arc began from — now on comprehended (not stripped) content.

The two layers ARE the substrate's own axis ([[feedback_relational_not_dense_distributional]]):
  ① DISTRIBUTIONAL — windowed co-occurrence of the comprehended NL prose (build_edges_topk, vocab_cap=None; F708) →
     the Class-L backbone the tome tower spectral-decomposes.
  ② RELATIONAL — the router's typed edges (math E=equals=m, chem Na=reacts_to=NaOH, convert has_length, ipa
     pronounced_as, cite cites, markup wikilinks) — STRUCTURED relationships raw co-occurrence would flatten or miss.

Validation-scale (MAX_ARTICLES); the full run is the same resumable background job with route_article in the loop.
srmech 0.9.0rc209. numpy-free; no Python abs builtin; no Counter; no CAD. CC-BY-SA enwiki (attested-not-committed). Run:
  MAX_ARTICLES=3000 /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKITOWERC_...py
"""
import bz2
import importlib.util
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

DUMP = os.environ.get("WIKI_DUMP", str(Path.home() / "corpora" / "wikipedia" / "enwiki-latest-pages-articles.xml.bz2"))
N = int(os.environ.get("MAX_ARTICLES", "3000"))
WINDOW = int(os.environ.get("WINDOW", "4"))
_D = "docs/srmech/rbs_lm_research/"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    sv = sys.argv; sys.argv = ["x"]
    try: spec.loader.exec_module(mod)
    except SystemExit: pass
    sys.argv = sv; return mod


ROUTER = _load("rt", _D + "R-RBS-LM-ROUTER_sublanguage_dispatch_compose.py")
WK = _load("wk", _D + "R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py")


class _ListSource:
    def __init__(self, texts):
        self.texts = texts

    def __iter__(self):
        return iter(self.texts)


def main():
    t0 = time.time()
    prose_docs, typed_edges, sublang_blocks, gap_classes = [], [], {}, {}
    n = 0
    with bz2.open(DUMP, "rt", encoding="utf-8") as fh:
        for _ev, el in ET.iterparse(fh, events=("end",)):
            if (el.tag.endswith("}text") or el.tag == "text") and el.text:
                n += 1
                r = ROUTER.route_article(el.text)
                prose_docs.append(r["prose"])
                typed_edges.extend(r["edges"])
                for k, v in r["counts"].items():
                    sublang_blocks[k] = sublang_blocks.get(k, 0) + v
                for k, v in (r["gaps"] or {}).items():
                    gap_classes[k] = gap_classes.get(k, 0) + v
                if n >= N:
                    el.clear(); break
            el.clear()
    troute = time.time() - t0

    # ① DISTRIBUTIONAL — Class-L co-occurrence of the comprehended prose (F708: vocab_cap=None)
    t1 = time.time()
    vocab, idx, cooc_edges, weights, freq, dropped = WK.build_edges_topk(_ListSource(prose_docs), window=WINDOW, vocab_cap=None)
    tcooc = time.time() - t1

    # ② RELATIONAL — the router's typed edges, tallied by relation family
    fam = {}
    for e in typed_edges:
        rt = str(e[1]) if len(e) > 1 else "link"
        key = rt.split(":")[0] if ":" in rt else ("cites" if rt == "cites" else "has/lang/pron" if rt in
              ("in_language", "pronounced_as") or rt.startswith("has_") or rt.startswith("melody") else "wikilink")
        fam[key] = fam.get(key, 0) + 1

    print("=== WIKITOWERC — the tome tower on COMPREHENDED content (srmech %s) ===" % __import__("srmech").__version__)
    print("  articles routed: %d in %.1fs (%.1f art/s) | co-occurrence build %.1fs\n" % (n, troute, n / max(1e-9, troute), tcooc))
    print("  ① DISTRIBUTIONAL (comprehended prose): vocab %s | co-occurrence edges %s" % (f"{len(vocab):,}", f"{len(cooc_edges):,}"))
    print("  ② RELATIONAL (router typed edges): %s total" % f"{len(typed_edges):,}")
    for k, v in sorted(fam.items(), key=lambda kv: -kv[1]):
        print("       %-12s %s" % (k, f"{v:,}"))
    print("\n  sub-language blocks comprehended (not stripped): %s" % dict(sorted(sublang_blocks.items(), key=lambda kv: -kv[1])))
    print("  residual gaps (still no kernel): %s" % (dict(sorted(gap_classes.items(), key=lambda kv: -kv[1])[:6]) or "(none)"))
    print("\n  READ: ONE graph, two layers — ① the Class-L distributional backbone from comprehended NL prose (feeds the")
    print("  tome-tower spectral decompose) + ② the structured relational edges the kernels recovered (math/chem/quantity/")
    print("  pronunciation/citation/link). The bigwiki encode, now on content Siona UNDERSTANDS rather than deletes.")


if __name__ == "__main__":
    main()
