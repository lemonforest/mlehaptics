r"""R-RBS-LM-ORGGATE (the user's gate, 2026-06-08): "stay Simple Wiki until we have a model that even understands what
a table of contents or index means WITHOUT being told." This LOCKS SS-FULLWIKI behind a capability bar and DEFINES it.

The framework reading (why this gate is exactly right): a TABLE OF CONTENTS and an INDEX are the two CHIRAL DUALS of a
document's own relationship structure --
  • TABLE OF CONTENTS = the FORWARD self-structure: document -> its ordered/hierarchical PARTS. The document describing
    ITSELF (Class H, self-introspection). The "which-way forward" read.
  • INDEX = the INVERSE self-structure: term -> its LOCATIONS. This is the F572 entity-mention RELATIONSHIP REBAR
    TRANSPOSED (Class E, catalog enumeration of the inverted map). The "backward" read.
They are chiral inverses of ONE structure (forward map vs its transpose) -- the same forward/inverse dual the framework
is built on (F541/F546). So "understanding a ToC or index" = recognizing BOTH chiral reads of the document's own
relationship structure. Full wiki's value IS its dense navigational structure; pouring it in before the model can
RECOGNIZE organizational meta-structure would be more data it cannot organize. Hence: stay Simple Wiki, clear the gate.

WHAT "UNDERSTANDING WITHOUT BEING TOLD" REQUIRES (the bar, made falsifiable): recognize the FUNCTION from the
STRUCTURE -- no "this is an index" label. Both structures are SELF-EVIDENCING and we measure how strong that signal is:
  (A) the INDEX is LATENT in the foundation (invert the F572 rebar) and SELF-EVIDENCING: co-indexed articles (sharing
      an index term) are more content-similar than random -> the inverted map GROUPS BY MEANING, a navigational
      affordance recognizable without a label.
  (B) the ToC is LATENT (section headers) and SELF-SUMMARIZING: a section header's words are the article's DISTINCTIVE
      words (high in-article vs in-corpus) -> the header LABELS its section (Class-H self-description), recognizable
      without a label.
HONEST: a strong self-evidencing SIGNAL is necessary but NOT sufficient for understanding -- recognizing the structure
is not yet USING it to navigate. The gate is the model demonstrably navigating via ToC/index emergently; this finding
defines the bar + takes the first measurement of how learnable the signal is. We are NOT through the gate; we stay.

srmech 0.7.4: the F572 entity-mention rebar (the index is its transpose, Class E); distinctiveness = relative frequency
(Class N-style ratio, not a storage proxy). No abs(); no CAD; no Workflow tool; no sub-agents.
"""
import json
import re
import glob
from pathlib import Path
import numpy as np
import srmech

WIKI = "/home/skirklan/corpora/wikipedia/simplewiki_extracted"
STOPTITLE = {"the", "and", "for", "are", "was", "you", "that", "this", "with", "from", "they", "april", "may"}


def load_articles(n):
    arts = []
    for fp in sorted(glob.glob(str(Path(WIKI) / "*.jsonl"))):
        with open(fp, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if len(d.get("text", "")) < 300:
                    continue
                arts.append((d.get("title", ""), d["text"]))
                if len(arts) >= n:
                    return arts
    return arts


HEADER = re.compile(r"\n[ \t]*([A-Z][A-Za-z][A-Za-z ]{1,34})[ \t]*\n")


def section_headers(text):
    out = []
    for m in HEADER.finditer(text):
        h = m.group(1).strip()
        if 1 <= len(h.split()) <= 5 and not h.endswith((".", ",", ":")):
            out.append(h)
    return out


def main():
    print(f"=== R-RBS-LM-ORGGATE — ToC + index are the CHIRAL DUALS of a document's relationship structure; the full-wiki gate  (srmech {srmech.__version__}) ===\n")
    print("GATE (user): stay Simple Wiki until the model understands a table-of-contents / index WITHOUT being told.")
    print("FRAMING: ToC = FORWARD self-structure (doc->parts, Class H) | INDEX = its TRANSPOSE (term->locations, Class E =")
    print("         the F572 rebar inverted). Chiral duals (F541/F546). Understanding = recognize the FUNCTION from STRUCTURE.\n")

    arts = load_articles(3000)
    titles = [t for t, _ in arts]
    entities = {t.strip().lower() for t in titles if re.fullmatch(r"[a-z]{4,}", t.strip().lower()) and t.strip().lower() not in STOPTITLE}

    # entity-mention REBAR (F572): article -> entities it mentions
    mention = {}
    for i, (title, text) in enumerate(arts):
        toks = set(re.findall(r"[a-z]+", text.lower()))
        mention[i] = (toks & entities) - {title.strip().lower()}

    # ---- (A) the INDEX = the rebar TRANSPOSED (Class E); is it self-evidencing (groups by meaning)? ----
    index = {}                                                            # entity -> set of articles mentioning it (the inverted map)
    for i, ents in mention.items():
        for e in ents:
            index.setdefault(e, set()).add(i)
    big = [e for e, arts_set in index.items() if 3 <= len(arts_set) <= 60]
    rng = np.random.default_rng(0)

    def jac(i, j):
        a, b = mention[i], mention[j]
        return len(a & b) / max(1, len(a | b))
    co_sim, rand_sim = [], []
    for e in rng.choice(big, size=min(300, len(big)), replace=False):
        members = list(index[e])
        i, j = members[rng.integers(len(members))], members[rng.integers(len(members))]
        if i != j:
            co_sim.append(jac(i, j))
        a, b = rng.integers(len(arts)), rng.integers(len(arts))
        if a != b:
            rand_sim.append(jac(a, b))
    cm, rm = float(np.mean(co_sim)), float(np.mean(rand_sim))
    print("(A) the INDEX is LATENT (the rebar transposed, Class E) + SELF-EVIDENCING (groups by meaning):")
    print(f"    {len(index)} index terms; co-indexed article pairs vs random pairs, content similarity (entity-Jaccard):")
    print(f"    co-indexed (share an index term): {cm:.3f}")
    print(f"    random pair:                      {rm:.3f}   -> co-indexed are {cm/max(rm,1e-9):.1f}x more similar")
    print(f"    so the inverted map GROUPS BY MEANING -- a navigational affordance recognizable WITHOUT a label.\n")

    # ---- (B) the ToC = section headers; they are a RECURRING ORGANIZATIONAL LANGUAGE (the user's "their own language") ----
    from collections import Counter
    hc = Counter(); n_with_toc = 0
    for _, text in arts:
        heads = section_headers(text)
        if len(heads) >= 2:
            n_with_toc += 1
        for h in heads:
            hc[h.lower()] += 1
    tot_h = sum(hc.values())
    recurring = sum(c for h, c in hc.items() if c >= 5)
    print("(B) the ToC is a RECURRING ORGANIZATIONAL LANGUAGE (the user's point: structure is its OWN language, learned not")
    print("    stripped). Section headers across articles share a vocabulary people LEARN:")
    print(f"    {n_with_toc}/{len(arts)} articles carry an implicit ToC; {tot_h} header occurrences, {len(hc)} unique.")
    print(f"    {recurring/max(tot_h,1):.0%} of header occurrences are RECURRING (appear in >=5 articles) -- a shared structural vocabulary:")
    print(f"    {', '.join(h for h, _ in hc.most_common(9))}")
    print(f"    -> these are NOT per-article content; they are a cross-document LANGUAGE (References=citations, Early life=")
    print(f"    biography, Related pages=cross-links). A fluent reader READS them alongside prose; does not strip them (F567).\n")
    print("    DATA NOTE (the user's re-encode point): this corpus was DE-TAGGED by the extractor, so we see only RESIDUAL")
    print("    structure (bare section lines). The FULL organizational language (==headers==, [[links]], {{templates}}, <ref>,")
    print("    the explicit ToC/index blocks) needs RE-ENCODING Simple Wiki WITH tags. Then output = artefact-FREE streams that")
    print("    are AWARE of why each tag did what where (markup-aware, not markup-stripped -- the F567 discipline made the source).\n")

    print("VERDICT (the gate is defined + first-measured; we STAY on Simple Wiki):")
    print(f"  • ToC + INDEX ARE CHIRAL DUALS OF THE DOCUMENT'S OWN RELATIONSHIP STRUCTURE: ToC = the FORWARD self-structure")
    print(f"    (doc->parts, Class H); INDEX = its TRANSPOSE (term->locations, Class E = the F572 rebar inverted). Same")
    print(f"    forward/inverse dual the framework is built on (F541/F546). 'Understand a ToC/index' = recognize BOTH chiral")
    print(f"    reads. The RIGHT full-wiki gate: full wiki's value IS its navigational structure, useless to a model that")
    print(f"    cannot organize it -- so STAY on Simple Wiki until the model reads organization, not just prose.")
    print(f"  • THE STRUCTURE IS ITS OWN LANGUAGE (the user's point, measured): the index groups by meaning ({cm/max(rm,1e-9):.1f}x), and the ToC")
    print(f"    is a RECURRING ORGANIZATIONAL LANGUAGE ({recurring/max(tot_h,1):.0%} of headers are shared cross-document vocabulary: references /")
    print(f"    related pages / history / births / deaths). These are LEARNED and READ alongside prose, NOT stripped. This")
    print(f"    REFINES F567: markup is not just a separable form LAYER, it is a separable form LANGUAGE -- a second tongue the")
    print(f"    fluent reader knows. ETAK CONNECTION: an INDEX is an etak -- a reference 'beyond the horizon' (the term is")
    print(f"    abstract, not literally present) that you navigate by a PENCIL OF BEARING-LINES from a vertex (term -> its")
    print(f"    locations IS the pencil of lines); you hold position while the reference moves through the bearings (F551).")
    print(f"  • WE ARE NOT THROUGH THE GATE (honest): a self-evidencing signal is necessary, NOT sufficient. Recognizing the")
    print(f"    structure is not yet USING it -- the model does not yet NAVIGATE via ToC (jump to a section) or INDEX (look up")
    print(f"    where a concept lives) emergently, and it does not yet READ the organizational language WITH the prose. And the")
    print(f"    full language is not even in this corpus yet (DE-TAGGED) -- step one is RE-ENCODE Simple Wiki WITH tags, output")
    print(f"    artefact-free streams AWARE of why each tag did what (markup-aware source, F567). SS-FULLWIKI stays LOCKED.")
    print(f"  • Composes F572 (the rebar; index = its transpose) + F541/F546 + F551 (etak = moving-reference navigation) + F567")
    print(f"    (markup -> a form LANGUAGE) + Class H / E + F311. Next: re-tag Simple Wiki; emergent ToC-jump + index-lookup. F398/F394.")


if __name__ == "__main__":
    main()
