r"""R-RBS-LM-ROUTER (#225) — the sub-language ROUTER: a Class-D DISPATCH that scans a whole article, routes each
detected construct to its comprehension kernel, HANDLES NESTING (\ce inside <math>, {{lang}} embedded-NL), and COMPOSES
every kernel's typed relationship-edges + the wikitext outer grammar into ONE relationship graph per article.

This is the tier that ties the F1204 formal-sublanguage kernels together with understand_markup (F764, the wikitext
outer grammar). The dispatch itself IS srmech Class-D (multi-needle pattern match → handler). The pipeline:
  1. EXTRACT each formal sublanguage block (math/chem/score/ipa/convert/lang), route it to its kernel → a typed
     comprehension + typed edges, and REPLACE the block in-place with a placeholder ⟦type:i⟧ (comprehend, don't strip —
     the block's structure is kept in `blocks`, and the placeholder keeps its POSITION so its nodes co-occur with the
     surrounding prose).
  2. NESTING: a <math> body's \ce{…} sub-blocks route to the CHEM kernel first (mhchem-in-TeX); the rest to LaTeX.
  3. understand_markup(remaining, gaps) → clean NL prose + the curated wikilink EDGES + the residual missing-kernel MAP
     (gaps) for whatever STILL has no kernel (the honest F819 surface, now much smaller).
  4. COMPOSE: union all edges (markup links + every kernel's typed edges) → one graph; the prose (with placeholders)
     is the NL stream that feeds the tome-tower co-occurrence.

srmech 0.9.0rc209. Pure Class-B/D/F composition (no numeric primitive). numpy-free; no Python abs builtin; no Counter;
no CAD. Run:  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-ROUTER_...py
"""
import importlib.util
import re
import sys

_D = "docs/srmech/rbs_lm_research/"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    sv = sys.argv; sys.argv = ["x"]
    try: spec.loader.exec_module(mod)
    except SystemExit: pass
    sys.argv = sv; return mod


MARKUP = _load("mk", _D + "R-RBS-LM-MARKUPGRAMMAR_class_bf_form_layer_understand_not_strip.py")
LATEX = _load("lx", _D + "R-RBS-LM-LATEXKERNEL_math_notation_sublanguage_comprehend_not_strip.py")
CHEM = _load("ch", _D + "R-RBS-LM-CHEMKERNEL_ce_reaction_notation_sublanguage_reaction_graph.py")
SCORE = _load("sc", _D + "R-RBS-LM-SCOREKERNEL_music_notation_sublanguage_pitch_class_cycle.py")
IPA = _load("ip", _D + "R-RBS-LM-IPAKERNEL_phonetic_notation_sublanguage_pronunciation_sequence.py")
CONVERT = _load("cv", _D + "R-RBS-LM-CONVERTKERNEL_quantity_unit_sublanguage_the_mass_count_determinative.py")

_CE_IN_MATH = re.compile(r"\\ce\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}")
_LANG = re.compile(r"\{\{\s*lang(?:-([a-z][a-z][a-z]?))?\s*\|([^{}]*)\}\}", re.I)      # {{lang|fr|x}} / {{lang-fr|x}}


def _edges_from(typ, comp):
    r"""pull the typed relationship edges out of a kernel's comprehension dict (each tagged with its sublanguage)."""
    e = []
    if typ == "math":
        for rel in comp.get("relations", []):
            a, rt, b = rel[0], rel[1], rel[2]
            e.append((a, "math:" + rt, b))
    elif typ == "chem":
        for ed in comp.get("edges", []):
            e.append((ed[0], "chem:" + ed[1], ed[2]))
    elif typ in ("convert", "ipa", "score"):
        ed = comp.get("edge")
        if ed:
            e.append((ed[0], ed[1], ed[2]))
    return e


def route_article(raw):
    r"""Route one raw wikitext article → {prose, edges, blocks, gaps, counts}. The Class-D dispatch + compose."""
    blocks, edges = [], []
    text = raw

    def _emit(typ, comp):
        i = len(blocks)
        blocks.append({"type": typ, "comprehension": comp})
        edges.extend(_edges_from(typ, comp))
        return " ⟦%s:%d⟧ " % (typ, i)

    def _math(m):
        body = m.group(1)
        for cm in _CE_IN_MATH.finditer(body):                      # NESTING: mhchem-in-TeX -> chem kernel first
            _emit("chem", CHEM.understand_chem(cm.group(1)))
        body = _CE_IN_MATH.sub(" ", body)
        return _emit("math", LATEX.understand_latex(body))

    # 1. formal sublanguage blocks — TAG-delimited first (they can contain | that would break template scans)
    text = re.sub(r"<math\b[^>]*>(.*?)</math>", _math, text, flags=re.S | re.I)
    text = re.sub(r"<(?:ce|chem)\b[^>]*>(.*?)</(?:ce|chem)>",
                  lambda m: _emit("chem", CHEM.understand_chem(m.group(1))), text, flags=re.S | re.I)
    text = re.sub(r"<score\b[^>]*>(.*?)</score>",
                  lambda m: _emit("score", SCORE.understand_score(m.group(1))), text, flags=re.S | re.I)
    # 2. template-delimited formal blocks
    text = re.sub(r"\{\{\s*math\s*\|(.*?)\}\}",
                  lambda m: _emit("math", LATEX.understand_latex(m.group(1))), text, flags=re.S | re.I)
    text = re.sub(r"\{\{\s*(?:cvt|convert)\s*\|([^{}]*?)\}\}",
                  lambda m: _emit("convert", CONVERT.understand_convert(m.group(1))), text, flags=re.I)
    text = re.sub(r"\{\{\s*IPA[a-zA-Z-]*\s*\|([^{}]*?)\}\}",
                  lambda m: _emit("ipa", IPA.understand_ipa(m.group(1))), text, flags=re.I)

    # 3. {{lang}} embedded-NL — comprehend as (inner text) --in_language--> (code); route-ready for Siona's NL typology
    def _lang(m):
        code = (m.group(1) or "").lower()
        parts = [p for p in m.group(2).split("|") if "=" not in p]
        if not code and parts:
            code = parts[0].lower(); parts = parts[1:]
        inner = " ".join(parts).strip()
        i = len(blocks)
        blocks.append({"type": "lang", "comprehension": {"lang": code, "text": inner}})
        if inner and code:
            edges.append((inner[:40], "in_language", code))
        return " " + inner + " "                                    # keep the foreign text inline (route to NL kernel later)
    text = _LANG.sub(_lang, text)

    # 4. the wikitext OUTER grammar: links -> curated edges, prose; residual gaps = what STILL has no kernel (F819)
    gaps = {}
    prose, markup_edges = MARKUP.understand_markup(text, gaps=gaps)
    edges.extend(markup_edges)

    counts = {}
    for b in blocks:
        counts[b["type"]] = counts.get(b["type"], 0) + 1
    return {"prose": prose, "edges": edges, "blocks": blocks, "gaps": gaps, "counts": counts}


if __name__ == "__main__":
    ART = (
        "The '''albedo''' {{IPA|/ælˈbiːdoʊ/}} of [[Earth]] is about {{convert|0.3|}} on average. "
        "Sodium reacts with water: <ce>2 Na + 2 H2O -> 2 NaOH + H2 ^</ce>, releasing hydrogen. "
        "The energy is <math>E = mc^2</math> where <math>c</math> is the speed of light. "
        "The [[Sun]] is {{convert|149.6|e6km|mi}} from Earth. A French phrase: {{lang|fr|bonjour le monde}}. "
        "See also [[Solar radiation]].<ref>{{cite web|title=Albedo|url=http://x}}</ref>"
    )
    r = route_article(ART)
    print("=== ROUTER — one article dispatched to every kernel + composed into one graph ===\n")
    print("  sublanguage blocks routed:", r["counts"])
    print("  residual gaps (still no kernel):", r["gaps"] or "(none)")
    print("\n  clean NL prose (blocks lifted to placeholders):")
    print("   ", " ".join(r["prose"].split())[:300])
    print("\n  COMPOSED relationship graph (%d edges) — sample across sublanguages:" % len(r["edges"]))
    for e in r["edges"][:16]:
        print("     ", e)
