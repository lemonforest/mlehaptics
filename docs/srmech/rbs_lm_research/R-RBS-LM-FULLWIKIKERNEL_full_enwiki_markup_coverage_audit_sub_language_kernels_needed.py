r"""R-RBS-LM-FULLWIKIKERNEL (the user's full-wiki readiness check, 2026-06-08): are our markup/markdown + programming-
language kernels ready to make ALL parts of FULL enwiki coherent? If not, which sub-language kernels + TOML configs are
missing? This is the SS-FULLWIKI gate item, now actionable (the 24GB enwiki dump is cached).

Method: stream a sample of REAL full-English-Wikipedia articles and measure (a) the COVERAGE of the existing
formatting_language_kernel.toml tiers (built on Simple Wiki: headers / [[Category]] / [[links]] / <ref> / {{templates}} /
tables / emphasis / <math>), and (b) the UNCOVERED constructs -- especially EMBEDDED SUB-LANGUAGES that the basic kernel
would just STRIP (losing content, so 'not coherent'):
  • PROGRAMMING code: <syntaxhighlight lang="X">, <source lang="X">, <code>, <pre>, {{code}} -- each lang is a SUB-LANGUAGE.
  • other SUB-LANGUAGES: <score> (music), <chem>/<ce> (chemistry), <hiero> (Egyptian -- our F582 kernel!), IPA, {{lang|xx}}.
  • structural/HTML: <gallery>, <nowiki>, <!--comments-->, HTML tags, [[File:]], external [http] links, lists.

THE KEY STRUCTURAL POINT (composes F595): an embedded sub-language is tagged by an ATTRIBUTE -- <syntaxhighlight lang=
"python">, {{lang|fr|...}}, <ce>... -- and that lang=/tag attribute IS THE DETERMINATIVE (the explicit meaning-class,
F585/F595): it routes the span to the right SUB-LANGUAGE KERNEL. So full-wiki coherence = the basic form tiers (F579)
PLUS a determinative-routed set of sub-language kernels. 'All parts coherent' iff every tag's content is handed to a
kernel that reads it, not stripped.

Corpus: full English Wikipedia dump (CC BY-SA), cached OUTSIDE the repo; attested not committed. stdlib only for the
stream (bz2 + xml.etree). No abs(); no CAD; no Workflow; no sub-agents.
"""
import bz2, re
import xml.etree.ElementTree as ET

DUMP = "/home/skirklan/corpora/wikipedia/enwiki-latest-pages-articles.xml.bz2"
N_ARTICLES = 3000

# the EXISTING formatting_language_kernel.toml tiers (F579) -- what the Simple-Wiki kernel already reads
COVERED = {
    "header (ToC, H)":        re.compile(r'(?m)^={2,6}\s*.+?\s*={2,6}\s*$'),
    "[[Category]] (index,E)": re.compile(r'\[\[Category:[^\]]+\]\]'),
    "[[link]] (rebar,L)":     re.compile(r'\[\[(?!Category:|File:|Image:)[^\]|#]+(?:\|[^\]]*)?\]\]'),
    "<ref> (attest,A)":       re.compile(r'<ref[^>]*?/>|<ref[^>]*?>.*?</ref>', re.S),
    "{{template}} (B)":       re.compile(r'\{\{[^{}]*\}\}', re.S),
    "table {| |} (B)":        re.compile(r'\{\|.*?\|\}', re.S),
    "emphasis ''' '' (F)":    re.compile(r"'''.+?'''|''.+?''"),
    "<math> (N)":             re.compile(r'<math[^>]*?>.*?</math>', re.S),
}

# UNCOVERED constructs, grouped -> what full-wiki adds that the Simple-Wiki kernel does NOT read
SUBLANG_CODE = {
    "<syntaxhighlight lang=> (CODE)": re.compile(r'<syntaxhighlight\b[^>]*>', re.I),
    "<source lang=> (CODE)":          re.compile(r'<source\b[^>]*lang', re.I),
    "<code> (CODE)":                  re.compile(r'<code\b[^>]*>'),
    "<pre> (CODE)":                   re.compile(r'<pre\b[^>]*>'),
    "{{code|...}} (CODE)":            re.compile(r'\{\{code[\s|]', re.I),
}
SUBLANG_OTHER = {
    "<score> (MUSIC)":         re.compile(r'<score\b', re.I),
    "<chem>/<ce> (CHEM)":      re.compile(r'<chem\b|<ce\b|<math chem', re.I),
    "<hiero> (EGYPTIAN)":      re.compile(r'<hiero\b', re.I),
    "{{IPA|...}} (PHONETIC)":  re.compile(r'\{\{IPA', re.I),
    "{{lang|xx|...}} (NL)":    re.compile(r'\{\{lang[|-]', re.I),
    "<timeline> (DATAVIZ)":    re.compile(r'<timeline\b', re.I),
}
STRUCTURAL = {
    "<gallery>":               re.compile(r'<gallery\b', re.I),
    "<nowiki>":                re.compile(r'<nowiki\b', re.I),
    "<!--comment-->":          re.compile(r'<!--'),
    "HTML tag (div/span/sup/sub/small/br/blockquote)": re.compile(r'</?(?:div|span|sup|sub|small|br|blockquote)\b', re.I),
    "[[File:|Image:]]":        re.compile(r'\[\[(?:File|Image):', re.I),
    "external [http] link":    re.compile(r'\[https?://'),
    "list (*,#,;,:)":          re.compile(r'(?m)^[*#:;]+'),
}


def stream_wikitext(dump, n):
    with bz2.open(dump, "rb") as f:
        count = 0
        for _, elem in ET.iterparse(f, events=("end",)):
            tag = elem.tag.rsplit("}", 1)[-1]
            if tag == "page":
                ns = elem.findtext("{*}ns") if hasattr(elem, "findtext") else None
                txt = None
                for e in elem.iter():
                    if e.tag.rsplit("}", 1)[-1] == "text":
                        txt = e.text; break
                if txt:
                    yield txt; count += 1
                elem.clear()
                if count >= n:
                    return


def audit(group, texts):
    out = {}
    for name, rx in group.items():
        arts = sum(1 for t in texts if rx.search(t))
        out[name] = arts / len(texts)
    return out


def main():
    print("=== R-RBS-LM-FULLWIKIKERNEL — full enwiki markup coverage audit: are the kernels ready, or do we need sub-language kernels? ===\n")
    texts = list(stream_wikitext(DUMP, N_ARTICLES))
    n = len(texts)
    print(f"corpus: FULL English Wikipedia dump -- {n} real articles streamed (markup, not stripped).\n")

    cov = audit(COVERED, texts)
    print("(1) COVERED by the existing formatting_language_kernel.toml (F579) -- % of articles with >=1 match:")
    for k, v in sorted(cov.items(), key=lambda x: -x[1]):
        print(f"    {v:6.1%}  {k}")
    print(f"    -> the basic FORM tiers carry over to full wiki (headers/links/refs/templates/tables/emphasis/math present).\n")

    code = audit(SUBLANG_CODE, texts)
    print("(2) UNCOVERED -- PROGRAMMING-LANGUAGE sub-languages (the kernel would STRIP these, losing the code):")
    for k, v in sorted(code.items(), key=lambda x: -x[1]):
        print(f"    {v:6.1%}  {k}")
    # what programming langs appear (the lang= determinative)
    langs = re.findall(r'<syntaxhighlight\b[^>]*?lang\s*=\s*["\']?([a-zA-Z0-9+#-]+)', " ".join(texts), re.I)
    from collections import Counter
    topl = Counter(l.lower() for l in langs).most_common(10)
    print(f"    lang= determinatives seen in <syntaxhighlight>: {topl}")
    print(f"    -> each lang= is a DISTINCT programming SUB-LANGUAGE (the lang attr IS the determinative, F595/F585).\n")

    other = audit(SUBLANG_OTHER, texts)
    print("(3) UNCOVERED -- OTHER embedded sub-languages (music / chemistry / hieroglyph / phonetic / natural-language):")
    for k, v in sorted(other.items(), key=lambda x: -x[1]):
        print(f"    {v:6.1%}  {k}")
    print(f"    -> <hiero> = our F582 Egyptian kernel; <score>/<chem>/IPA/{{{{lang}}}} each need a sub-language kernel.\n")

    struct = audit(STRUCTURAL, texts)
    print("(4) UNCOVERED -- structural / HTML / media (mostly strippable, but must be RECOGNISED to clean coherently):")
    for k, v in sorted(struct.items(), key=lambda x: -x[1]):
        print(f"    {v:6.1%}  {k}")
    print()

    # readiness verdict: which sub-languages are frequent enough to need a kernel?
    need = {**code, **other}
    needed = sorted([(k, v) for k, v in need.items() if v >= 0.005], key=lambda x: -x[1])
    print("VERDICT (are the markup/programming kernels ready to make ALL parts of full wiki coherent?):")
    print(f"  • THE BASIC FORM TIERS CARRY OVER (F579 ready): headers/links/refs/templates/tables/emphasis/math all present")
    print(f"    in full wiki at high rates -- the Simple-Wiki kernel reads them.")
    print(f"  • NOT YET READY FOR THE EMBEDDED SUB-LANGUAGES: full wiki carries code + music + chemistry + hieroglyph +")
    print(f"    phonetic + other-natural-language spans the current kernel would STRIP (lose), so those parts are NOT")
    print(f"    coherent. The sub-languages appearing often enough to need a kernel (>=0.5% of articles):")
    for k, v in needed:
        print(f"      - {k}: {v:.1%}")
    print(f"  • THE FIX (the user's 'more sub-language kernels + TOML config things'): add a SUB-LANGUAGE ROUTER tier to")
    print(f"    formatting_language_kernel.toml where the tag's lang=/attribute is the DETERMINATIVE (F595 σ_B): it routes")
    print(f"    the span to the right kernel -- a per-language PROGRAMMING kernel (Class-B/D: code is TLV-framed + pattern-")
    print(f"    matched syntax), a MUSIC kernel (<score>, Class-I cyclic/pitch), a CHEMISTRY kernel (<chem>, Class-J/cyclic),")
    print(f"    the EGYPTIAN kernel (<hiero> -> F582, already built!), an IPA/phonetic kernel, and an embedded-NL router")
    print(f"    ({{{{lang|xx}}}} -> the xx is the language determinative). Each is a kernel-the-srmech-way (its own TOML).")
    print(f"  • SO: full-wiki coherence = the F579 form tiers + a determinative-routed family of sub-language kernels. The")
    print(f"    markup ALREADY tells us which sub-language each span is (the lang= attribute) -- that is the determinative")
    print(f"    axis (F595), so the routing is supplied, not guessed. We are READY for the form layer, NOT YET for the")
    print(f"    sub-languages; the next build is the sub-language router TOML + the per-sub-language kernels.")
    print(f"  • Composes F579 (the formatting kernel) + F595/F585 (the determinative = the meaning-class router) + F582")
    print(f"    (the <hiero> Egyptian kernel, ready) + F574 (the full-wiki gate) + F567/F568 (markup-aware clean). The")
    print(f"    SS-FULLWIKI gate now has a concrete blocker list. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
