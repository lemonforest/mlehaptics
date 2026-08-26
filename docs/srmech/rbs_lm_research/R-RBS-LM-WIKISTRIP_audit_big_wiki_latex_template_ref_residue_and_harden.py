r"""R-RBS-LM-WIKISTRIP (user catch -- a real provenance worry): "if big wiki was not recently encoded, are we sure it was
not stripped of latex and things?"

THE HONEST ANSWER: NO, WE WERE NOT SURE -- AND THE USER IS RIGHT. Two compounding gaps in F690:
  1. F690's strip_wiki_markup is a DEMO stripper that does exactly three things:
        [[a|b]] / [[b]]  -> b           (wikilinks: OK)
        {{...}}          -> drop         (templates: SINGLE-LEVEL only -- nested {{a{{b}}c}} leaks the inner residue)
        <...>            -> drop the TAG (so <math>\frac{a}{b}</math> drops the <math> TAGS but LEAVES the LaTeX
                                          CONTENT '\frac{a}{b}' as raw text -> 'displaystyle'/'frac'/'mathbf' become
                                          VOCAB TOKENS. Same for <ref>...</ref> (citation text/URLs survive).)
  2. F690 was only ever RUN on the clean hand-written demo CORPUS (galaxy/shell/helix sentences) -- which contains NO
     <math>, NO <ref>, NO nested templates, NO tables. So the LaTeX/markup path was NEVER EXERCISED. We verified the
     stripper on text that had nothing for it to fail on.

WHY IT MATTERS (the MPM / no-magic discipline, F640/F688): a kernel built from un-cleaned wiki text has UNATTESTED JUNK
tokens ('displaystyle', 'frac', 'cite', 'web', 'wikitable', 'thumb') in its vocabulary. Those are NOT WORDS -- so every
association the Class-L kernel forms with them is SPURIOUS (a co-occurrence with markup, not with meaning). The kernel
would 'ground' a story in markup noise. That is exactly the grounding-honesty the whole Story Teller rests on, broken at
the corpus-cleaning layer.

THIS SCRIPT: (1) feeds REAL wiki markup (with <math> LaTeX, <ref>, nested {{templates}}, a {| table |}, a <!-- comment -->,
== headers ==, [http ext links]) through F690's DEMO stripper and SHOWS the residue pollution; (2) provides a HARDENED
stripper that removes <math>/<ref>/<score>/<chem>/<syntaxhighlight>/<code> CONTENT (not just tags), nested templates
(iterate to fixpoint), tables, comments, ext-link wrappers -- and shows the clean vocab; (3) quantifies the junk-token
reduction. The honest conclusion: the big-wiki kernel MUST be RE-ENCODED with the hardened stripper before its vocab is
trusted; the real target is the F579/F607 wiki-formatting-language kernel (the dev session, per F690's own docstring).

srmech (version reported at runtime): loads F690 (strip_wiki_markup) + reuses the F698 unicode_tokenize. amsc.format
.sha256_bytes for the content-address of the cleaned text. No abs(); no CAD; no Workflow; no sub-agents.
"""
import re
import sys
import importlib.util
import unicodedata
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    saved = sys.argv
    sys.argv = ["x"]
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    sys.argv = saved
    return mod


wk = _load("wk", "docs/srmech/rbs_lm_research/R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py")


def unicode_tokenize(text):
    """F698 Unicode-aware tokenizer: runs of Unicode letter|mark|number; everything else is a boundary."""
    words, cur = [], []
    for ch in text:
        if unicodedata.category(ch)[0] in ("L", "M", "N"):
            cur.append(ch)
        else:
            if cur:
                words.append("".join(cur)); cur = []
    if cur:
        words.append("".join(cur))
    return words


def strip_wiki_markup_hardened(text):
    """harden F690: remove CONTENT-bearing markup (math/ref/code/tables/comments/nested templates), not just tags.

    Order matters: kill the content-bearing blocks BEFORE the generic tag-drop, else the LaTeX inside survives.
    Reference only -- the real target is the F579/F607 wiki-formatting-language kernel (dev session). MECHANISM scaffold.
    """
    # 1. HTML comments (may span lines)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    # 2. content-bearing tag pairs: drop the WHOLE element incl. its inner text (LaTeX / citation / code / music / chem)
    for tag in ("math", "ref", "code", "syntaxhighlight", "score", "chem", "hiero", "gallery", "timeline"):
        text = re.sub(rf"<{tag}\b[^>]*>.*?</{tag}>", " ", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(rf"<{tag}\b[^>]*/\s*>", " ", text, flags=re.IGNORECASE)            # self-closing <ref .../>
    # 3. wiki tables {| ... |} (may nest; iterate to fixpoint)
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\|[^{]*?\|\}", " ", text, flags=re.DOTALL)
    # 4. templates {{ ... }} -- iterate to fixpoint so NESTED {{a{{b}}c}} fully clears
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{[^{}]*\}\}", " ", text, flags=re.DOTALL)
    # 5. wikilinks [[a|b]] -> b ; external links [http://x label] -> label
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[(?:https?|ftp)://[^\s\]]+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"\[(?:https?|ftp)://[^\s\]]+\]", " ", text)                            # bare ext link, no label
    # 6. any REMAINING tag (now safe -- content blocks already gone)
    text = re.sub(r"<[^>]+>", " ", text)
    # 7. emphasis / headers / list bullets / table-cell leftovers
    text = re.sub(r"'{2,}", "", text)                                                     # ''' bold '' italic
    text = re.sub(r"^[\s]*[*#:;=|!-]+", " ", text, flags=re.MULTILINE)                     # bullets / headers / cell marks
    text = re.sub(r"={2,}", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# a REAL wiki-markup sample (the kind of thing F690's DEMO stripper never saw):
RAW_WIKI = r"""
A '''galaxy''' is a [[gravitationally bound]] system of stars.<ref>Hubble plain citation footnote 1929</ref>
The rotation curve is <math>v(r) = \sqrt{\frac{G M(r)}{r}}</math> where <math>\displaystyle M(r)</math> is the enclosed mass.<ref>{{cite web|url=http://x.org|title=Galaxies}}</ref>
{{Infobox galaxy | name = Milky Way | type = {{nowrap|barred spiral}} | mass = 1.5e12 }}
<!-- editorial note: verify the mass figure -->
== Structure ==
* A spiral galaxy turns and coils its [[galactic arm|arms]].
See also [http://example.org/galaxies the external catalogue].
{| class="wikitable"
! Type !! Count
|-
| spiral || many
|}
"""


def main():
    print(f"=== R-RBS-LM-WIKISTRIP — audit + harden F690's LaTeX/template/ref stripping  (srmech {srmech.__version__}) ===\n")

    demo = wk.strip_wiki_markup(RAW_WIKI)
    hard = strip_wiki_markup_hardened(RAW_WIKI)
    demo_toks = unicode_tokenize(demo.lower())
    hard_toks = unicode_tokenize(hard.lower())

    JUNK = {"math", "displaystyle", "frac", "sqrt", "mathbf", "cite", "web", "url", "title", "ref", "wikitable",
            "infobox", "nowrap", "thumb", "px", "align", "class", "http", "https", "hubble", "citation", "footnote"}
    demo_junk = sorted({t for t in demo_toks if t in JUNK})
    hard_junk = sorted({t for t in hard_toks if t in JUNK})

    print("(1) F690's DEMO stripper on REAL markup -> LaTeX/template/ref RESIDUE leaks into the text (the user's worry):")
    print(f"    {demo!r}\n")
    print(f"    -> junk tokens that became VOCAB: {demo_junk}")
    print(f"    -> the LaTeX '\\sqrt{{\\frac{{G M(r)}}{{r}}}}' + '\\displaystyle' survived as 'sqrt'/'frac'/'displaystyle';")
    print(f"       the BARE <ref>Hubble plain citation...</ref> survived as 'hubble'/'citation'/'footnote'; the {{| table |}}")
    print(f"       leaked as 'class'/'wikitable'; the [http ...] ext-link leaked as 'http'. (The TEMPLATE-wrapped <ref>{{{{cite")
    print(f"       web}}}}</ref> happened to be caught by the {{{{...}}}}-drop -- but a BARE ref is NOT, which is the real leak.)\n")

    print("(2) THE HARDENED stripper (remove CONTENT of math/ref/code/table/comment + nested templates) -> clean:")
    print(f"    {hard!r}\n")
    print(f"    -> junk tokens remaining: {hard_junk}   (content-address {srmech.amsc.format.sha256_bytes(hard.encode('utf-8'))[:12]})\n")

    print("(3) THE NUMBERS (junk-token pollution, the no-magic/grounding-honesty measure F640/F688):")
    print(f"    demo stripper : {len(demo_toks):3d} tokens, {len(demo_junk)} distinct JUNK markup tokens -> {demo_junk}")
    print(f"    hardened      : {len(hard_toks):3d} tokens, {len(hard_junk)} distinct JUNK markup tokens -> {hard_junk}")
    real_words = [t for t in hard_toks if t not in JUNK and len(t) > 1]
    print(f"    hardened real-word sample: {real_words[:14]}\n")

    print("VERDICT (are we sure big-wiki wasn't stripped of LaTeX? -- NO, and now fixed):")
    print(f"  • THE USER IS RIGHT: F690's strip_wiki_markup is a DEMO that drops <tag>S but KEEPS their CONTENT, so <math>")
    print(f"    LaTeX ('\\frac', '\\sqrt', '\\displaystyle') + BARE <ref> citations + tables + ext-links ALL LEAK as vocab")
    print(f"    tokens. AND it was only ever run on the clean hand-written demo corpus (no <math> in it) -- so the")
    print(f"    LaTeX/markup path was NEVER EXERCISED. We were NOT sure; the worry was correct.")
    print(f"  • WHY IT MATTERS (grounding honesty, F640/F688): a kernel built from un-cleaned text carries UNATTESTED junk")
    print(f"    tokens ('displaystyle'/'cite'/'wikitable') -- not words. Every Class-L association with them is SPURIOUS")
    print(f"    (co-occurrence with markup, not meaning). The story would 'ground' in markup noise -- breaking the chord (F658).")
    print(f"  • THE FIX (this script): a HARDENED stripper removes the CONTENT of math/ref/code/score/chem/table/comment")
    print(f"    blocks (not just the tags) + clears NESTED templates to fixpoint + unwraps ext-links. Verified: the demo's")
    print(f"    {len(demo_junk)} distinct junk tokens drop to {len(hard_junk)}. So the big-wiki kernel MUST BE RE-ENCODED with the hardened")
    print(f"    stripper before its vocab is trusted (the demo numbers in F690/F697 are clean ONLY because the demo corpus")
    print(f"    had no real markup -- the LOGIC is sound, the CLEANING was not exercised).")
    print(f"  • THE REAL TARGET is the F579/F607 wiki-formatting-language kernel (this is a reference scaffold, per F690's own")
    print(f"    docstring) -- the dev session lands the full form-tier + determinative-routed sub-language family. Add a note")
    print(f"    to the bone (wordassoc/README) + UPSTREAM_NOTES that the wiki adapter MUST strip content-bearing markup.")
    print(f"  • Composes F690/F697 (the big-wiki kernel -- this audits its cleaning) + F698 (the Unicode tokenizer used here)")
    print(f"    + F640/F688 (no-magic / grounding honesty) + F573 (the honesty audit -- we tested on text with nothing to")
    print(f"    fail on) + F579/F607 (the real formatting-language-kernel target). srmech {srmech.__version__}. Reference scaffold;")
    print(f"    not a package edit. Held open (F394).")


if __name__ == "__main__":
    main()
