r"""R-RBS-LM-RAWENCODE (F817) — re-encode the ENTIRE simple wiki into the RBS-HDC walkable-shape instrument FROM THE
RAW DUMP, with NO doctoring: the markup is COMPREHENDED by the F764 understand_markup sublanguage kernel, never
stripped (user direction 2026-06-17: "do not use stripping from SSoT. we MUST use sublanguage kernels to understand.
no doctoring the data before consumption").

The correction this makes to F814: the F814 encode ran on `simplewiki_extracted/articles.jsonl`, which is itself a
WIKIEXTRACTOR PROJECTION of the wiki — the raw markup ([[links]], {{templates}}, ==headings==) was already stripped
to ~0.1% BEFORE we consumed it (the doctoring happened upstream), leaving pipe/`thumb`/`$latex$` residue that
polluted the token walk. The TRUE SSoT is the raw MediaWiki dump (simplewiki-latest-pages-articles.xml.bz2). Here we
stream that dump, and for each main-namespace non-redirect page we run understand_markup(raw_wikitext) ->
(clean_prose, edges): it UNWRAPS link/emphasis/heading CONTENT (keeps the words), EXTRACTS the curated relationship
edges (the [[Target]] outlinks — stronger than co-occurrence), and removes ONLY pure FORM (template/ref/table/css/
latex/code). Then we tokenise the clean prose, find the minimal unique-walk window k*, and persist the walkable token
SHAPE + k* (the de Bruijn fiber, F805/F813) PLUS the curated edge list (so "everything AND its relationships" survive
the read). Recall = WALK the shape from a seed (F808/F814; HVs are deterministic functions of tokens, computed on
demand — not stored, edge-portable).

Output (OUTSIDE the repo, gitignored): an NDJSON instrument (one page per line: title / k* / n-tokens / unique-flag /
shape / edges) + a title->byte-offset index for O(1) random access (low-RAM read, F793). STREAMING (one page in RAM
at a time, §52) so RAM stays flat over the whole corpus. srmech rc169. Run in the background; progress every 10k.

Composes F814 (the instrument it corrects), F764 (the understand_markup kernel — now hardened for raw-wikitext
nesting), F805/F808/F813 (fiber / context-addressed walk / entire-article reconstruction), §52 (streaming),
#225/#226 (the sub-language router + remaining kernels — the deeper path).
"""
import bz2
import importlib.util
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

DUMP = "/home/skirklan/corpora/wikipedia/simplewiki-latest-pages-articles.xml.bz2"
OUT = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_instrument.ndjson"
IDX = "/home/skirklan/corpora/wikipedia/simplewiki_rawbody_index.json"
KMAX = 16
MIN_TOK = 12                                                     # skip stubs / template-only pages

# import the F764 SSoT markup-understanding kernel by path (the filename is not import-safe)
_MG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "R-RBS-LM-MARKUPGRAMMAR_class_bf_form_layer_understand_not_strip.py")
_spec = importlib.util.spec_from_file_location("markupgrammar", _MG_PATH)
mg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mg)


def _localname(tag):
    return tag.rsplit("}", 1)[-1]


def kstar(tokens):
    """Minimal context window k whose forward walk is unique (the de Bruijn fiber pin, F805)."""
    for k in range(2, KMAX + 1):
        g = defaultdict(set)
        ok = True
        for i in range(k - 1, len(tokens)):
            c = tuple(tokens[i - (k - 1):i])
            g[c].add(tokens[i])
            if len(g[c]) > 1:
                ok = False
                break
        if ok:
            return k, True
    return KMAX, False


def main():
    import srmech
    sys.stderr.write(f"=== R-RBS-LM-RAWENCODE — entire simplewiki FROM RAW DUMP via understand_markup "
                     f"(NO doctoring; srmech {srmech.__version__}) ===\n")
    sys.stderr.flush()
    index = {}
    n = nuniq = toktot = edgetot = 0
    ksum = 0
    title = ns = txt = None
    isredir = False
    with open(OUT, "w") as fout:
        ctx = ET.iterparse(bz2.open(DUMP, "rt", encoding="utf-8"), events=("end",))
        for _ev, el in ctx:
            tag = _localname(el.tag)
            if tag == "title":
                title = el.text
            elif tag == "ns":
                ns = el.text
            elif tag == "redirect":
                isredir = True
            elif tag == "text":
                txt = el.text
            elif tag == "page":
                if ns == "0" and not isredir and txt and len(txt) > 200:
                    clean, edges = mg.understand_markup(txt)
                    toks = re.findall(r"[a-z0-9]+", clean.lower())
                    if len(toks) >= MIN_TOK:
                        k, uniq = kstar(toks)
                        off = fout.tell()
                        rec = {"t": title, "k": k, "n": len(toks), "u": uniq,
                               "s": " ".join(toks), "e": " ".join(edges)}
                        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        index[title.lower()] = off
                        n += 1
                        nuniq += uniq
                        toktot += len(toks)
                        edgetot += len(edges)
                        ksum += k
                        if n % 10000 == 0:
                            sys.stderr.write(f"  {n} pages | {toktot:,} tokens | uniq-walk {nuniq / n:.1%} | "
                                             f"mean k* {ksum / n:.1f} | mean edges {edgetot / n:.1f}\n")
                            sys.stderr.flush()
                title = ns = txt = None
                isredir = False
                el.clear()
    json.dump(index, open(IDX, "w"))
    sys.stderr.write(f"\nDONE: {n} pages encoded from RAW dump | {toktot:,} tokens | uniq-walk {nuniq / n:.1%} | "
                     f"mean k* {ksum / n:.1f} | {edgetot:,} curated edges (mean {edgetot / n:.1f}/page)\n")
    sys.stderr.write(f"instrument: {OUT} ({os.path.getsize(OUT) // (1024 * 1024)} MB) | "
                     f"index: {IDX} ({len(index)} titles)\n")
    sys.stderr.flush()


if __name__ == "__main__":
    main()
