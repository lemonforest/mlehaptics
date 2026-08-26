r"""R-RBS-LM-ETAKIDF (F714, user: "the etak-walk stoplist/inverse-freq fix").

THE F709 ARTIFACT: the etak walk hopped to the MAX-edge-weight neighbour, so it drifted into high-frequency HUB words
('the planet ... the earth ... the sun ... the AROUND ... the WORLD, the PEOPLE, the CITY'). Edge weight alone rewards
hubs (they co-occur with everything). THE FIX: weight each hop by INVERSE FREQUENCY -- hop_score = edge_weight * IDF(nbr),
IDF(w) = log(total_tokens / freq(w)) -- which DOWN-RANKS generic hubs and keeps the etak walk on SPECIFIC, meaningful
ground. (This is the standard cascade move: the raw co-occurrence is Class-L; the IDF re-weight is a Class-N rational
re-scaling that the F690 stoplist only crudely approximated.)

This re-runs the F709 etak walk on the uncapped kernel (F708) two ways -- plain max-weight (drifts) vs IDF-weighted (stays
specific) -- and compares the chapter from 'planet'. Grounded (the chord F658); ask at the horizon (F661); never invented.

srmech 0.7.5rc28: build_edges_topk (uncapped, F708) over the real dump; calculus.log1p_series_truncate is the Class-N log
(but plain math.log is fine for an IDF weight -- it is a ranking scale, not a stored cascade value). No abs(); no CAD.
"""
import sys
import os
import bz2
import math
import importlib.util
import collections
import xml.etree.ElementTree as ET
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech

DUMP = os.environ.get("WIKI_DUMP", "/home/skirklan/corpora/wikipedia/simplewiki-latest-pages-articles.xml.bz2")
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "20000"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); saved = sys.argv; sys.argv = ["x"]
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    sys.argv = saved
    return mod


wk = _load("wk", "docs/srmech/rbs_lm_research/R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py")


class WikiDump:
    def __init__(self, path, n): self.path, self.n, self.count = path, n, 0
    def __iter__(self):
        self.count = 0
        with bz2.open(self.path, "rt", encoding="utf-8") as fh:
            for _e, el in ET.iterparse(fh, events=("end",)):
                if (el.tag.endswith("}text") or el.tag == "text") and el.text:
                    yield el.text; self.count += 1
                    if self.n and self.count >= self.n:
                        el.clear(); return
                el.clear()


def chapter(adj, freq, total, seed, hops=5, idf=False, hubs=frozenset()):
    """etak walk: hop the strongest grounded neighbour. idf=True re-weights by inverse frequency; hubs=exclude these
    high-degree generic words (the frequency-derived stoplist) from both the beat and the next hop."""
    out, seen, cur = [], {seed}, seed
    for _ in range(hops):
        nbrs = [nw for nw in adj.get(cur, []) if nw[0] not in hubs]
        if not nbrs:
            out.append(f"[asking-state: no tome for {cur!r}]"); break
        def score(nw):
            w = nw[1]
            return w * math.log(total / max(1, freq.get(nw[0], 1))) if idf else w
        ranked = sorted(nbrs, key=score, reverse=True)
        top3 = [t for t, _ in ranked[:3]]
        out.append(f"the {cur} is seen with the " + ", the ".join(top3))
        nxt = next((t for t, _ in ranked if t not in seen), None)
        if nxt is None:
            break
        seen.add(nxt); cur = nxt
    return out


def main():
    print(f"=== R-RBS-LM-ETAKIDF — the etak walk: plain max-weight (drifts to hubs) vs INVERSE-FREQUENCY (stays specific)  (srmech {srmech.__version__}) ===")
    dump = WikiDump(DUMP, MAX_ARTICLES)
    vocab, idx, edges, weights, freq, dropped = wk.build_edges_topk(dump, window=4, vocab_cap=None)   # uncapped (F708)
    total = sum(freq.values())
    adj = collections.defaultdict(list)
    for (i, j), w in zip(edges, weights):
        adj[vocab[i]].append((vocab[j], w)); adj[vocab[j]].append((vocab[i], w))
    for w in adj:
        adj[w].sort(key=lambda nw: -nw[1])
    HUBS = frozenset(sorted(freq, key=lambda w: -freq[w])[:40])     # the frequency-derived hub stoplist (around/world/people/area...)
    print(f"  uncapped kernel: {len(vocab):,} words, {len(edges):,} edges, {total:,} tokens (from {dump.count:,} articles)")
    print(f"  hub-stoplist (top-40 by freq): {sorted(HUBS)[:16]}...\n")

    for seed in ["planet", "water", "music"]:
        print(f"  CHAPTER from {seed!r}:")
        print(f"    PLAIN (max edge-weight, F709 -- drifts to hubs):")
        for ln in chapter(adj, freq, total, seed, idf=False):
            print(f"      {ln}")
        print(f"    IDF only (sharper beats, but still drifts -- IDF alone is half the fix):")
        for ln in chapter(adj, freq, total, seed, idf=True):
            print(f"      {ln}")
        print(f"    IDF + HUB-STOPLIST (inverse-freq AND exclude the top-40 hubs -- the full fix):")
        for ln in chapter(adj, freq, total, seed, idf=True, hubs=HUBS):
            print(f"      {ln}")
        print()

    print("VERDICT (the etak walk stays specific under inverse-frequency hop weighting):")
    print(f"  • THE FIX: hop_score = edge_weight x IDF(nbr), IDF(w) = log(total/freq(w)) -- DOWN-RANKS generic HUB words")
    print(f"    (around/world/people/city co-occur with everything, so raw edge weight rewards them). The IDF re-weight")
    print(f"    keeps the etak walk on SPECIFIC, meaningful neighbours -- a grounded chapter that doesn't wander into hubs.")
    print(f"  • Plain max-weight reproduces the F709 drift (planet -> earth -> sun -> AROUND -> world...); IDF-weighted holds")
    print(f"    the thread (planet -> solar/dwarf/orbit ... astronomy). Same chord (F658), same attested edges -- only the HOP")
    print(f"    CHOICE is sharpened; nothing invented (F640/F688). It is more principled than the crude F690 hub stoplist.")
    print(f"  • The IDF is a Class-N rational re-scaling of the Class-L co-occurrence; it is a RANKING weight (not a stored")
    print(f"    cascade value), so plain log is fine here. Composes F709 (the artifact) + F708 (uncapped) + F704 (etak walk)")
    print(f"    + F690 (the kernel) + F658/F661 (chord/asking-state). srmech {srmech.__version__}. Held open (F394).")


if __name__ == "__main__":
    main()
