r"""R-RBS-LM-CITEKERNEL (#225/#216) — the CITATION notation (<ref>/{{cite …}}/{{sfn}}) as its own genome-encoded
sublanguage kernel: COMPREHEND a citation into an ATTESTABLE SOURCE RECORD + a (article)--cites-->(source) edge, never
strip it. This is the router's one surfaced residual gap (<ref>), and it is the framework's OWN discipline turned on the
corpus: a citation IS a relationship to an external source, and the AMSC/MPM attestation method (§2 — a citation without
a persistent identifier is weak; a DOI/arXiv/PMID is attestable) is exactly what this kernel scores. The (article -->
source) edges form the CITATION GRAPH (a Class-L scholarly backbone; CITE-1 #216 = the OpenAlex concept×concept peer).

COMPREHEND, not strip: the bibliographic RECORD (title/authors/year/venue) is the operand; the strongest persistent
IDENTIFIER (doi > arxiv > pmid > bibcode > isbn > … > url > author-year > title) is the canonical source node; the
attestation grade (persistent-id / url-ephemeral / weak-metadata) is the MPM verdict. Class-B/F FORM grammar (no numeric
primitive). srmech 0.9.0rc209. numpy-free; no Python abs builtin; no Counter; no CAD. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-CITEKERNEL_...py
"""
import re

CITE_FORM_CLASSES = ("short_ref", "web", "book", "journal", "news", "encyclopedia", "arxiv", "generic")
_SFN = ("sfn", "sfnp", "sfnm", "harv", "harvnb", "harvtxt", "harvcoltxt", "harvcol", "harvs")
# citation param -> identifier type; ordered by attestation strength (a persistent DOI/arXiv beats a URL).
_ID_PARAMS = (("doi", "doi"), ("arxiv", "arxiv"), ("eprint", "arxiv"), ("pmid", "pmid"), ("pmc", "pmc"),
              ("bibcode", "bibcode"), ("isbn", "isbn"), ("jstor", "jstor"), ("s2cid", "s2cid"), ("oclc", "oclc"),
              ("issn", "issn"), ("url", "url"), ("chapter-url", "url"))
_ID_PRIORITY = ("doi", "arxiv", "pmid", "bibcode", "isbn", "pmc", "jstor", "s2cid", "oclc", "issn", "url")
_PERSISTENT = ("doi", "arxiv", "pmid", "bibcode", "isbn")           # a resolvable, verifiable identifier (MPM-attestable)
_YEAR = re.compile(r"\b(1[5-9]\d\d|20\d\d)\b")


def _strip_wiki(s):
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", s or "")     # [[T|D]] -> D ; [[E]] -> E
    return re.sub(r"[\[\]'{}]", "", s).strip()


def _clean(s):
    return re.sub(r"[^0-9A-Za-z]", "", _strip_wiki(s))


def _authors(kv):
    out, i = [], 1
    while kv.get("last%d" % i) or kv.get("author%d" % i) or kv.get("author-last%d" % i):
        out.append(_strip_wiki(kv.get("last%d" % i) or kv.get("author%d" % i) or kv.get("author-last%d" % i)))
        i += 1
    if not out:
        a = kv.get("last") or kv.get("author") or kv.get("authors") or kv.get("vauthors") or kv.get("author-last")
        if a:
            out.append(_strip_wiki(a))
    return [a for a in out if a]


def understand_citation(src, tmpl="cite"):
    r"""Comprehend a citation template body into a source record + edge. Returns:
        ctype       : short_ref / web / book / journal / news / encyclopedia / arxiv / generic
        title, authors, year, venue : the bibliographic record (the operand)
        ids         : {doi/arxiv/pmid/isbn/…/url: value}
        source_id   : the canonical source node (strongest persistent id, else author-year, else title)
        attestation : 'persistent-id' | 'url-ephemeral' | 'weak-metadata' | 'harvard-pointer' — the MPM grade
        edge        : ('__article__', 'cites', source_id) — the citation relationship
    """
    tmpl = (tmpl or "cite").lower().strip()
    kv, pos = {}, []
    for p in src.split("|"):
        p = p.strip()
        if not p:
            continue
        if "=" in p:
            k, v = p.split("=", 1)
            kv[k.strip().lower()] = v.strip()
        else:
            pos.append(p)
    is_sfn = any(tmpl.startswith(x) for x in _SFN) or (not kv and len(pos) >= 2)

    if is_sfn:                                                        # {{sfn|Author|Author|Year|p=..}} — Harvard pointer
        year = next((x for x in pos if re.fullmatch(r"\d{4}[a-z]?", x)), None)
        authors = [x for x in pos if x != year and not re.fullmatch(r"\d{4}[a-z]?", x)]
        page = kv.get("p") or kv.get("pp") or kv.get("page") or kv.get("pages") or kv.get("loc")
        sid = "-".join(_clean(a) for a in authors[:3]) + (("-" + year) if year else "")
        return {"ctype": "short_ref", "title": None, "authors": authors, "year": year, "venue": None, "page": page,
                "ids": {}, "source_id": sid or None, "attestation": "harvard-pointer",
                "edge": ("__article__", "cites", sid) if sid else None}

    ctype = tmpl.replace("cite", "").strip() or ("generic" if "citation" in tmpl else "generic")
    if ctype not in CITE_FORM_CLASSES:
        ctype = "generic"
    title = _strip_wiki(kv.get("title") or kv.get("wstitle") or kv.get("chapter") or "")
    ym = _YEAR.search(kv.get("year") or kv.get("date") or "")
    year = ym.group(1) if ym else None
    authors = _authors(kv)
    venue = _strip_wiki(kv.get("journal") or kv.get("work") or kv.get("newspaper") or kv.get("magazine")
                        or kv.get("encyclopedia") or kv.get("website") or kv.get("publisher") or "") or None
    ids = {}
    for param, idt in _ID_PARAMS:
        if kv.get(param) and idt not in ids:
            ids[idt] = _strip_wiki(kv[param])
    sid = next(("%s:%s" % (idt, ids[idt]) for idt in _ID_PRIORITY if ids.get(idt)), None)
    if not sid:
        sid = ("-".join(_clean(a) for a in authors[:2]) + (("-" + year) if year else "")) or _clean(title)[:40] or None
    att = ("persistent-id" if any(ids.get(k) for k in _PERSISTENT)
           else "url-ephemeral" if ids.get("url") else "weak-metadata")
    return {"ctype": ctype, "title": title or None, "authors": authors, "year": year, "venue": venue,
            "ids": ids, "source_id": sid, "attestation": att,
            "edge": ("__article__", "cites", sid) if sid else None}


if __name__ == "__main__":
    SAMPLES = [
        ("sfn", "Gelb|Whiting|1998|p=45"),
        ("cite book", "title=Anarchy, State, and Utopia|last=Nozick|first=Robert|publisher=[[Basic Books]]|year=1974|isbn=978-0465097203"),
        ("cite journal", "last=Carter |first=April |date=1978 |title=Anarchism and violence |journal=Nomos |volume=19"),
        ("cite arxiv", "title=The spherical bolometric albedo for planet Mercury |first=Anthony |last=Mallama |date=2017 |class=astro-ph.EP |eprint=1703.02670"),
        ("cite web", "date=2011 |title=Greenland's Ice Is Growing Darker |url=https://earthobservatory.nasa.gov/images/76916"),
        ("cite encyclopedia", "encyclopedia=American National Biography|title=Lincoln, Abraham|last=McPherson|first=James|date=2024|doi=10.1093/anb/9780198606697"),
    ]
    print("=== CITEKERNEL — comprehend a citation into an attestable source record + edge (not strip) ===\n")
    for tmpl, s in SAMPLES:
        r = understand_citation(s, tmpl)
        print(f"  {{{{{tmpl}|{s[:60]}...}}}}")
        print(f"    {r['ctype']:11} authors={r['authors']} year={r['year']} venue={r['venue']}")
        print(f"    ids={r['ids']}  source_id={r['source_id']}  attestation=[{r['attestation']}]")
        print(f"    edge: {r['edge']}\n")
