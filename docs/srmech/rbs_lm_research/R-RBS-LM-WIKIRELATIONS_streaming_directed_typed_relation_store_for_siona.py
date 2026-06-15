r"""R-RBS-LM-WIKIRELATIONS (F757 infra) — the persisted DIRECTED + TYPED relation store for Siona, the F756 rung
made into a Siona tier. The F754 assoc tier is UNDIRECTED/UNTYPED ("X near Y"); this is the directional, typed layer:
for each subject, its strongest DIRECTED out-edges (objects that FOLLOW it in reading order = what it does / leads to /
has) with the FRAME word that labels the edge when there is one (X —from→ Y, X —than→ Y). Direction = reading order
(the sentence is a directed story); the F756 magnetic-Laplacian reading is the spectral form of this same directed graph.

Memory-safe streaming (the WIKIASSOC pattern): one parse, a per-subject bounded heap of top-K directed-typed out-edges.
Emits simplewiki_relations.json:
  { "subjects": { word: [ [object, count, relation], ... top-K ], ... }, "attestation": {...} }
where `relation` = the dominant CLEAN frame word on that subject→object edge (prepositions / comparatives / copula),
or "→" for a plain directed adjacency (determiners the/a/an are dropped — they are "X of the Y" noise, F756).

srmech 0.7.5rc149. No abs(); no CAD; CC-BY-SA simplewiki source. Run (background, no timeout):
  MAX_ARTICLES=3000 /tmp/srmech_rc149/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKIRELATIONS_...py
"""
import json
import os
import re
import time
import heapq
from pathlib import Path
import srmech
from srmech.amsc.format import sha256_raw

ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
OUT = Path.home() / "corpora" / "wikipedia" / "simplewiki_relations.json"
N = int(os.environ.get("MAX_ARTICLES", "3000"))
K = int(os.environ.get("REL_K", "8"))                 # directed-typed out-edges kept per subject
# frame words = relation-label vocabulary (F753/F751). DETERMINERS are dropped (the "X of the Y" noise, F756).
FUNC = frozenset("""a an the is are was were be been being of in on to by with from as at for and or that which who
whom whose this these those it its their his her they he she we you i but not no than then so such into over under
between through during before after above below up down out off only also can could will would shall should may might
must do does did has have had having about against among around because while when where why how what""".split())
DET = frozenset("a an the this that these those its his her their it".split())


def main():
    print(f"=== R-RBS-LM-WIKIRELATIONS — streaming directed/typed relation store (N={N} articles, K={K}; "
          f"srmech {srmech.__version__}) ===")
    t0 = time.time()
    # edge[(s,o)] = [count, {clean_rel: count}]  — clean_rel dict is usually empty (most edges are adjacency)
    edge = {}
    freq = {}
    n_art = 0
    with open(ART) as f:
        for i, line in enumerate(f):
            if i >= N:
                break
            try:
                text = json.loads(line).get("text", "")
            except ValueError:
                continue
            n_art += 1
            for sent in re.split(r"[.!?]+", text):
                toks = [(w, w not in FUNC) for w in re.findall(r"[a-z]+", sent.lower()) if len(w) >= 3]
                last, buf = None, []
                for w, is_c in toks:
                    if is_c:
                        freq[w] = freq.get(w, 0) + 1
                        if last is not None and last != w:
                            e = edge.get((last, w))
                            if e is None:
                                e = edge[(last, w)] = [0, {}]
                            e[0] += 1
                            rel = next((b for b in buf if b not in DET), None)  # first clean (non-determiner) frame word
                            if rel:
                                e[1][rel] = e[1].get(rel, 0) + 1
                        last, buf = w, []
                    elif last is not None:
                        buf.append(w)
    print(f"  parsed {n_art} articles -> {len(freq)} content words, {len(edge)} directed pairs ({time.time()-t0:.1f}s)")

    # per-subject bounded heap of top-K out-edges by count
    heaps = {}
    for (s, o), (c, rels) in edge.items():
        rel = max(rels, key=rels.get) if rels else "→"     # dominant clean frame word, else plain "→"
        h = heaps.get(s)
        if h is None:
            heaps[s] = [(c, o, rel)]
        elif len(h) < K:
            heapq.heappush(h, (c, o, rel))
        elif c > h[0][0]:
            heapq.heapreplace(h, (c, o, rel))
    subjects = {s: [[o, c, rel] for c, o, rel in sorted(h, reverse=True)] for s, h in heaps.items()}

    OUT.write_text(json.dumps({
        "wiki": "simplewiki", "articles": n_art, "subjects_count": len(subjects), "K": K,
        "subjects": subjects,
        "attestation": {"source_url": "https://dumps.wikimedia.org/simplewiki/latest/", "license": "CC-BY-SA-4.0",
                        "response_sha256": sha256_raw(",".join(sorted(subjects)).encode()).hex(),
                        "parser_version": f"srmech {srmech.__version__}"}}))
    print(f"  wrote {OUT.name} ({OUT.stat().st_size/1e6:.1f} MB) — directed/typed out-edges for {len(subjects)} subjects")

    print("\n  spot-check (subject -> directed-typed out-edges; objects that FOLLOW = what it does/leads to):")
    for w in ("volcano", "bread", "dragon", "tea", "computer", "more", "earth"):
        if w in subjects:
            print(f"    {w:9}: " + ", ".join(f"{rel}→{o}({c})" if rel != "→" else f"→{o}({c})"
                                             for o, c, rel in subjects[w][:6]))
        else:
            print(f"    {w:9}: (not a subject in this cut)")


if __name__ == "__main__":
    main()
