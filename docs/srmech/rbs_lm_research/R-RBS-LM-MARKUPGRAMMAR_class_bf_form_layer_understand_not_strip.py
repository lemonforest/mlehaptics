r"""R-RBS-LM-MARKUPGRAMMAR (F764) — the unified markup grammar as a SHARED, IMPORTABLE language-layer component:
markup is a Class-B/F FORM layer Siona COMPREHENDS, never strips (the F762 correction made operational + put in the
genome language layer, per the user 2026-06-15: "we don't strip markup, we make a kernel to understand it like with
latex and markdown … you can't just strip things Siona needs to understand").

What "understand, don't strip" means concretely (the difference from R-RBS-LM-CLEANGATE's demo-only blanket strip):
  * a LINK / BOLD / ITALIC / HEADING wraps CONTENT — the word is real; we UNWRAP it (keep the word, drop the syntax).
  * a TEMPLATE / REF / TABLE / CSS-attr / LaTeX-cmd / CODE-fence is PURE FORM — no prose inside; we remove the form.
  * the LINK forms carry CURATED RELATIONSHIP edges (wiki [[Target]] / markdown [text](url)) — stronger than
    co-occurrence; we EXTRACT them as edges so "everything and its relationships" survives the read.
So `understand_markup(text) -> (clean_prose, edges)`: comprehend the form, keep the content + relationships.

This is the SSoT grammar both R-RBS-LM-WIKIGLOSS (the definition tier) and the SionaGenepool language layer import —
markup is now a genome language-layer FORM vocabulary (a `markup` chromosome of form-classes, sibling to SignWriting),
not a one-off research script. Composes F762 (comprehend-not-discard), F761 (the language layer), F567/CLEANGATE
(the unified wiki+LaTeX+HTML+CSS+Markdown+code grammar), Class-B (TLV-framing) / Class-F (render).

srmech 0.7.5rc155. Pure form-grammar (Class-B/F) — no math primitive, no abs(), no CAD. CC-BY-SA simplewiki.
"""
import re

# The language-layer FORM vocabulary — the Class-B/F framing classes the genome carries (used as the `markup`
# chromosome's gene labels; chosen so none collides with a common bare English query word — e.g. *_emphasis not "bold").
MARKUP_FORM_CLASSES = (
    "wiki_link", "md_link", "bold_emphasis", "italic_emphasis", "section_heading",
    "bullet_list", "blockquote", "template", "citation_ref", "html_tag",
    "css_style", "latex_cmd", "code_span",
)

# RELATIONSHIP-bearing link forms (the curated edges).
_WIKI_LINK_DISP = re.compile(r"\[\[(?:[^\]|]+)\|([^\]]+)\]\]")   # [[Target|Display]] -> Display (the CONTENT shown)
_WIKI_LINK      = re.compile(r"\[\[([^\]|]+)\]\]")                # [[Entity]]         -> Entity
_MD_LINK        = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")          # [text](url)        -> text
_WIKI_LINK_TGT  = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")   # the link TARGET (the relationship edge)

# Per-form-class detectors (for detect_markup — so the genome can SAY which forms it recognized).
_DETECT = {
    "wiki_link":       re.compile(r"\[\[[^\]]+\]\]"),
    "md_link":         re.compile(r"\[[^\]]+\]\([^)]+\)"),
    "bold_emphasis":   re.compile(r"'''[^']+'''|\*\*[^*]+\*\*|__[^_]+__"),
    "italic_emphasis": re.compile(r"''[^']+''"),
    "section_heading": re.compile(r"={2,6}[^=\n]+={2,6}|^#{1,6}\s", re.M),
    "bullet_list":     re.compile(r"^\s*[-*+]\s|^\s*\d+\.\s", re.M),
    "blockquote":      re.compile(r"^\s*>\s", re.M),
    "template":        re.compile(r"\{\{[^{}]*\}\}|\{\|.*?\|\}", re.S),
    "citation_ref":    re.compile(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", re.S | re.I),
    "html_tag":        re.compile(r"</?[a-z][^>]*>", re.I),
    "css_style":       re.compile(r'\b[a-z-]+\s*=\s*"[^"]*"|\b\d+px\b', re.I),
    "latex_cmd":       re.compile(r"\\[a-zA-Z]+\{[^}]*\}|\\[a-zA-Z]+"),
    "code_span":       re.compile(r"```.*?```|`[^`]+`", re.S),
}


def detect_markup(text):
    """Which Class-B/F form-classes appear in `text` — the genome's "I recognize this form" read-out."""
    t = text or ""
    return [c for c in MARKUP_FORM_CLASSES if _DETECT[c].search(t)]


def extract_edges(text):
    """The CURATED relationship edges the markup carries (link targets/text) — stronger than co-occurrence."""
    t = text or ""
    edges = []
    for tgt in _WIKI_LINK_TGT.findall(t):
        e = tgt.strip().lower()
        if e and len(e) < 60 and ":" not in e:                   # ":" = a namespace (File:/Image:/Category:) — not a prose entity
            edges.append(e)
    for disp, _url in _MD_LINK.findall(t):
        e = disp.strip().lower()
        if e and len(e) < 60:
            edges.append(e)
    seen, uniq = set(), []
    for e in edges:                                              # dedup, order-preserving
        if e not in seen:
            seen.add(e); uniq.append(e)
    return uniq


def understand_markup(text):
    """COMPREHEND markup, do NOT discard it. Returns (clean_prose, edges): extract the relationship edges, UNWRAP
    inline content (keep the word a link/emphasis/heading wraps), and remove ONLY pure-form syntax (template/ref/
    table/css/latex/code). Markup is a separable FORM layer the language layer understands (F762)."""
    t = text or ""
    edges = extract_edges(t)
    # 1) PURE-FORM blocks (no prose inside) — remove form + content
    t = _DETECT["code_span"].sub(" ", t)                         # ``` fences ``` / `inline code`
    t = _DETECT["citation_ref"].sub(" ", t)                      # <ref>…</ref>
    t = re.sub(r"\{\{[^{}]*\}\}", " ", t)                        # {{templates}} (one nesting level)
    t = re.sub(r"\{\|.*?\|\}", " ", t, flags=re.S)               # {| tables |}
    t = re.sub(r"\[\[(?:File|Image):[^\]]*\]\]", " ", t, flags=re.I)   # media links = pure form (caption is not the lead)
    t = re.sub(r"\$[^$]+\$", " ", t)                             # inline LaTeX math $…$ = notation form
    # 2) UNWRAP inline content — KEEP the word the form wraps (the comprehend-not-discard core)
    t = _WIKI_LINK_DISP.sub(r"\1", t)                            # [[Target|Display]] -> Display
    t = _WIKI_LINK.sub(r"\1", t)                                 # [[Entity]]         -> Entity
    t = _MD_LINK.sub(r"\1", t)                                   # [text](url)        -> text
    t = re.sub(r"'''([^']+)'''", r"\1", t)                       # wiki '''bold'''
    t = re.sub(r"''([^']+)''", r"\1", t)                         # wiki ''italic''
    t = re.sub(r"\*\*([^*]+)\*\*|__([^_]+)__", lambda m: m.group(1) or m.group(2), t)   # markdown **bold**/__bold__
    t = re.sub(r"\*([^*]+)\*", r"\1", t)                         # markdown *italic*
    t = re.sub(r"={2,6}\s*([^=\n]+?)\s*={2,6}", r"\1. ", t)      # wiki ==Heading== -> "Heading." (its own sentence)
    t = re.sub(r"^#{1,6}\s*(.+?)\s*$", r"\1. ", t, flags=re.M)   # markdown # Heading -> "Heading."
    # 3) remaining PURE-form syntax (no content to keep)
    t = re.sub(r"</?[a-z][^>]*>", " ", t, flags=re.I)            # html tags
    t = re.sub(r'\b[a-z-]+\s*=\s*"[^"]*"|\b\d+px\b', " ", t, flags=re.I)   # css attr="…" / 100px
    t = re.sub(r"\\[a-zA-Z]+(?:\{[^}]*\})*|\\[a-zA-Z]+", " ", t) # LaTeX \cmd{…}{…} (all args) / bare \cmd
    t = re.sub(r"^\s*[-*+>]\s|^\s*\d+\.\s|^-{3,}$", " ", t, flags=re.M)    # list / quote / hr markers
    t = re.sub(r"[\[\]{}|]", " ", t)                            # stray bracket/pipe residue
    t = re.sub(r"\s+", " ", t).strip()
    return t, edges


def main():                                                      # self-test on representative leads
    import srmech
    print(f"=== R-RBS-LM-MARKUPGRAMMAR — understand (don't strip) Class-B/F markup (srmech {srmech.__version__}) ===\n")
    samples = [
        "The [[tomato]] ('''Solanum lycopersicum''') is a [[fruit|fruit]], specifically a [[berry]].",
        "==Volcanoes==The plural of volcano can be either volcanos or volcanoes.",
        "{{Infobox food|name=Pizza}} '''Pizza''' is a dish of [[Italy|Italian]] origin.<ref>x</ref>",
        "A **computer** is a [machine](https://x) that runs `code` and uses $E=mc^2$ \\frac{a}{b}.",
        "<div style=\"width:100px\">thumb|right|250px|A caption.</div> The Earth is a [[planet]].",
    ]
    for s in samples:
        clean, edges = understand_markup(s)
        print(f"  forms : {detect_markup(s)}")
        print(f"  clean : {clean!r}")
        print(f"  edges : {edges}\n")


if __name__ == "__main__":
    main()
