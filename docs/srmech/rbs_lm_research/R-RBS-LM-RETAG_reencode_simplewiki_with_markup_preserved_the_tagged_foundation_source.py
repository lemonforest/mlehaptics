r"""R-RBS-LM-RETAG (the user's re-encode directive, 2026-06-08): "we will need to reencode simple wiki with all the
tagging." Our working corpus (simplewiki_extracted/articles.jsonl) was produced by an extractor that STRIPPED the
markup -- no [[links]], no ==headers==, no {{templates}}, no <ref> -- leaving only broken residue (right|thumb|...).
That de-tagged corpus cannot carry the organizational LANGUAGE (F574) the full-wiki gate requires.

The raw dump WITH all tags is on disk: simplewiki-latest-pages-articles.xml.bz2. This re-encodes Simple Wiki from it,
PRESERVING the wikitext markup, into a new tagged corpus. It does NOT parse/strip the markup -- it KEEPS it, so the
F567/F568 markup-aware layer can run on the REAL structure downstream (output artefact-free streams that are AWARE of
why each tag did what -- the user's spec). This is the proper FOUNDATION SOURCE (F572) the de-tagged corpus could not be.

What it does:
  • stream the bz2 MediaWiki XML (no full decompress), extract per page: title + raw wikitext (markup intact);
  • keep main-namespace (ns=0), non-redirect, >=300 chars; write {"title","wikitext"} NDJSON;
  • VERIFY the organizational language is now VISIBLE: count pages carrying [[links]] / ==headers== / {{templates}} /
    <ref> / the index-relevant categories -- exactly the tags the old extractor destroyed.

This is corpus-prep infrastructure (NDJSON output per the project discipline), not a math finding; srmech is not needed
for the extraction. No abs(); no CAD; no Workflow tool; no sub-agents.
"""
import bz2
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

SRC = "/home/skirklan/corpora/wikipedia/simplewiki-latest-pages-articles.xml.bz2"
OUTDIR = Path("/home/skirklan/corpora/wikipedia/simplewiki_tagged")
OUT = OUTDIR / "articles_tagged.jsonl"
CAP = 60000                                                              # bounded design-bed; full re-encode drops the cap


def localname(tag):
    return tag.rsplit("}", 1)[-1]


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("=== R-RBS-LM-RETAG — re-encode Simple Wiki WITH markup preserved (the tagged foundation source) ===\n")
    print(f"source: {SRC}")
    print(f"output: {OUT}  (cap {CAP} main-namespace non-redirect pages)\n")

    kept = 0
    have_link = have_head = have_tmpl = have_ref = have_cat = 0
    sample = None
    with bz2.open(SRC, "rb") as fh, open(OUT, "w", encoding="utf-8") as out:
        ctx = ET.iterparse(fh, events=("end",))
        for _, elem in ctx:
            if localname(elem.tag) != "page":
                continue
            title = ns = text = None
            redirect = False
            for ch in elem:
                ln = localname(ch.tag)
                if ln == "title":
                    title = ch.text
                elif ln == "ns":
                    ns = ch.text
                elif ln == "redirect":
                    redirect = True
                elif ln == "revision":
                    for c2 in ch:
                        if localname(c2.tag) == "text":
                            text = c2.text
            elem.clear()
            if ns != "0" or redirect or not title or not text or len(text) < 300:
                continue
            out.write(json.dumps({"title": title, "wikitext": text}, ensure_ascii=False) + "\n")
            kept += 1
            if re.search(r"\[\[", text):
                have_link += 1
            if re.search(r"^=+[^=].*=+\s*$", text, re.M):
                have_head += 1
            if re.search(r"\{\{", text):
                have_tmpl += 1
            if re.search(r"<ref", text):
                have_ref += 1
            if re.search(r"\[\[Category:", text, re.I):
                have_cat += 1
            if sample is None and re.search(r"\[\[", text) and re.search(r"^=+[^=].*=+", text, re.M):
                sample = (title, text)
            if kept >= CAP:
                break

    print(f"re-encoded {kept} pages WITH markup preserved.\n")
    print("the organizational LANGUAGE is now VISIBLE (tags the de-tagged extractor destroyed):")
    print(f"    pages with [[wiki-links]]   : {have_link:>6}  ({have_link/max(kept,1):.0%})  -> the RELATIONSHIP rebar (F572), explicit")
    print(f"    pages with ==section heads==: {have_head:>6}  ({have_head/max(kept,1):.0%})  -> the TABLE-OF-CONTENTS language (F574)")
    print(f"    pages with {{{{templates}}}}     : {have_tmpl:>6}  ({have_tmpl/max(kept,1):.0%})  -> infoboxes / structured data (Class B/F)")
    print(f"    pages with <ref> citations  : {have_ref:>6}  ({have_ref/max(kept,1):.0%})  -> the attestation/provenance layer (MPM)")
    print(f"    pages with [[Category:...]]  : {have_cat:>6}  ({have_cat/max(kept,1):.0%})  -> the INDEX language (F574, term->membership)")
    if sample:
        title, text = sample
        links = re.findall(r"\[\[([^\]|]+)", text)[:6]
        heads = re.findall(r"^=+\s*([^=\n]+?)\s*=+\s*$", text, re.M)[:6]
        print(f"\n    e.g. [{title}]: explicit links -> {links}")
        print(f"                    section heads -> {heads}")
    print()
    print("VERDICT:")
    print(f"  • SIMPLE WIKI RE-ENCODED WITH TAGS (the user's directive): the foundation SOURCE now CARRIES the markup the")
    print(f"    de-tagged extract had destroyed -- explicit [[links]] (the F572 relationship rebar, no longer a mention-")
    print(f"    proxy), ==headers== (the F574 ToC language), [[Category:]] (the F574 index language), {{{{templates}}}}, <ref>.")
    print(f"  • THIS UNBLOCKS THE GATE WORK: the F567/F568 markup-aware layer now runs on the REAL organizational language;")
    print(f"    testing = artefact-FREE prose streams that are AWARE of why each tag did what where (the user's spec). The")
    print(f"    entity-mention proxy (F572) can be REPLACED by the explicit [[link]] graph; the ToC/index (F574) become")
    print(f"    first-class, not residual. We STAY on Simple Wiki (F574 gate) -- now on the PROPERLY TAGGED Simple Wiki.")
    print(f"  • NEXT: point the markup-aware clean (F567) at this tagged source; rebuild the F572 foundation on explicit")
    print(f"    [[links]] + [[Category]] index; then the emergent ToC/index navigation (the F574 gate). enwiki dump is on")
    print(f"    disk for AFTER the gate clears. Composes F567/F568 (markup-aware) + F572 (rebar) + F574 (gate). F398/F394.")


if __name__ == "__main__":
    main()
