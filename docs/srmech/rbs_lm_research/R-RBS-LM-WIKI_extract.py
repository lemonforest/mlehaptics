"""R-RBS-LM-WIKI extractor — stream a LOCAL Wikipedia .bz2 dump to clean-text
JSONL, version-proof (wikiextractor crashes on Python 3.11+ with a re inline-
flag PatternError). Pure stdlib bz2 + ElementTree.iterparse + mwparserfromhell
strip_code. Root-clearing keeps memory bounded so this scales from simplewiki
(~250k articles) to full enwiki (~6.5M) without loading the tree.

Only namespace-0 (content) articles, non-redirect, >= min_chars after strip.
Output: <out>/articles.jsonl  (one {"title","text"} per line).

  /tmp/verify_srmech_071_sci/bin/python R-RBS-LM-WIKI_extract.py \
    --dump /home/skirklan/corpora/wikipedia/simplewiki-latest-pages-articles.xml.bz2 \
    --out  /home/skirklan/corpora/wikipedia/simplewiki_extracted
"""

import argparse
import bz2
import html
import json
import re
from pathlib import Path
from xml.etree.ElementTree import iterparse

import mwparserfromhell

# --- markup-cleaning (F447 residue + F-WIKI-MARKUP scan): drop math/ref SOURCE
# before strip_code so LaTeX (\frac, \displaystyle) + citation markup never leak
# as tokens; then unescape entities + strip residual HTML tags. Dependency-free.
# Negligible for simplewiki (measured <0.5%); load-bearing for full enwiki (math-heavy). ---
_MATH_RE = re.compile(r"<\s*math\b[^>]*>.*?<\s*/\s*math\s*>", re.S | re.I)
_REF_RE = re.compile(r"<\s*ref\b[^>]*>.*?<\s*/\s*ref\s*>", re.S | re.I)
_DISP_RE = re.compile(r"\{\\displaystyle[^{}]*\}")
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean(wikitext):
    s = _MATH_RE.sub(" ", wikitext)               # drop <math>…</math> LaTeX source
    s = _REF_RE.sub(" ", s)                        # drop <ref>…</ref> citation source
    s = mwparserfromhell.parse(s).strip_code()     # wikitext markup
    s = html.unescape(s)                           # &amp; &lt; … → chars
    s = _DISP_RE.sub(" ", s)                       # any {\displaystyle …} residue
    s = _TAG_RE.sub(" ", s)                        # residual HTML tags
    return _WS_RE.sub(" ", s).strip()


def localname(tag):
    return tag.rsplit("}", 1)[-1]


def extract(dump_path, out_dir, max_articles=0, min_chars=200, log_every=20000):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "articles.jsonl"

    title = ns = text = None
    redirect = False
    root = None
    pages = kept = 0

    with bz2.open(dump_path, "rb") as fh, open(out_path, "w", encoding="utf-8") as out:
        ctx = iterparse(fh, events=("start", "end"))
        for event, elem in ctx:
            tag = localname(elem.tag)
            if event == "start":
                if root is None:
                    root = elem
                continue
            # end events
            if tag == "title":
                title = elem.text
            elif tag == "ns":
                ns = elem.text
            elif tag == "redirect":
                redirect = True
            elif tag == "text":
                text = elem.text
            elif tag == "page":
                pages += 1
                if ns == "0" and not redirect and text:
                    try:
                        plain = _clean(text)
                    except Exception:
                        plain = text
                    if len(plain) >= min_chars:
                        out.write(json.dumps({"title": title, "text": plain},
                                             ensure_ascii=False) + "\n")
                        kept += 1
                title = ns = text = None
                redirect = False
                root.clear()          # bounded memory: drop accumulated <page> children
                if kept and kept % log_every == 0:
                    print(f"  ...{pages:,} pages scanned / {kept:,} articles kept")
                if max_articles and kept >= max_articles:
                    break
    print(f"  done: {pages:,} pages scanned, {kept:,} content articles -> {out_path}")
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-articles", type=int, default=0)
    ap.add_argument("--min-chars", type=int, default=200)
    args = ap.parse_args()
    print(f"=== WIKI extract: {args.dump} ===")
    extract(args.dump, args.out, args.max_articles, args.min_chars)


if __name__ == "__main__":
    main()
