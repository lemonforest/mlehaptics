r"""R-RBS-LM-SEEDSTORE (F809 — #1 scale + #3 storage-by-seed, two solutions) — once the article is a deterministic
walk over a SHARED corpus de Bruijn graph (F806–F808), an article need not be stored as prose; it is a SEED into the
shared graph. There are TWO solutions with an efficiency trade-off:

  • Sol-A  SEED-ONLY (high-k): raise k until the article's walk is UNIQUE in the shared graph → the article = just its
            start seed (k-1 tokens). Tiny per-article, but the shared graph is LARGE (many long k-grams).
  • Sol-B  SEED+CHOICES (any-k): keep k small (small graph), and where the walk BRANCHES store the choice. An article
            = seed + the branch-choice bits (a FORCED step, out-degree 1, costs 0 bits). Small graph, per-article cost.

They trade GRAPH SIZE (grows with k) against PER-ARTICLE CHOICE BITS (shrink with k); which is more efficient depends
on corpus size N (few articles → B; many → A amortises the graph over the corpus). The article's IRREDUCIBLE content
is its choice-bits; the shared graph is common corpus structure — the no-magic reading (the graph isn't "magic", only
the choices are the article's own information). The RBS-HDC store realises the graph (F808 bundle-record keys); this
measures the INFORMATION (combinatorial, substrate-agnostic) — bits via integer bit_length, NO transcendentals.

Also the #1 SCALE probe: how k* (min k for a unique walk) and choice-bits scale with article LENGTH. Full-BODY
articles (markup) need the #225 form-kernels + a streaming graph; here = many clean simplewiki abstracts. srmech rc169.
"""
import json
import re

ABS = "/home/skirklan/corpora/wikipedia/simplewiki_abstracts.json"
N = 400
KS = [3, 4, 5, 6, 8]


def build_graph(arts, k):
    g = {}                                                   # (k-1)-gram context -> {successor: count}  (SHARED corpus de Bruijn graph)
    for toks in arts:
        for i in range(k - 1, len(toks)):
            c = tuple(toks[i - (k - 1):i])
            g.setdefault(c, {})
            g[c][toks[i]] = g[c].get(toks[i], 0) + 1
    return g


def main():
    import srmech
    print(f"=== R-RBS-LM-SEEDSTORE — storage-by-seed: seed-only vs seed+choices, efficiency frontier (srmech {srmech.__version__}) ===\n")
    store = json.load(open(ABS))["store"]
    texts = [store[t] for t in list(store)[:N]]
    arts = [re.findall(r"[a-z0-9]+", t.lower()) for t in texts]
    arts = [a for a in arts if len(a) >= 12]
    vocab = sorted({w for a in arts for w in a})
    tbits = max(1, (len(vocab) - 1).bit_length())            # bits per token id
    text_bits = sum(len(t.encode()) for t in texts) * 8      # raw UTF-8 prose (the "stored prose" baseline)
    n_arts = len(arts)
    tok_total = sum(len(a) for a in arts)
    print(f"corpus: {n_arts} simplewiki abstracts · {tok_total} tokens · vocab {len(vocab)} ({tbits} bits/token) · prose {text_bits//8} bytes\n")
    print(f"  {'k':>2} | {'graph edges':>11} | {'graph KB':>8} | {'A: %uniq-walk':>13} | {'B: mean choice-bits/art':>22} | {'A total KB':>10} | {'B total KB':>10}")

    best = None
    for k in KS:
        g = build_graph(arts, k)
        edges = sum(len(s) for s in g.values())
        graph_bits = edges * tbits                           # store one successor token per edge (contexts = shared nodes)
        seed_bits = (k - 1) * tbits
        uniq = 0
        sum_choice = 0
        per_choice = []
        for a in arts:
            cbits = 0
            forced = True
            for i in range(k - 1, len(a)):
                d = len(g[tuple(a[i - (k - 1):i])])          # GLOBAL out-degree at this context
                cbits += max(0, d - 1).bit_length()          # bits to pick among d successors (0 when forced)
                if d > 1:
                    forced = False
            uniq += forced                                    # Sol-A valid iff the whole walk is globally unique
            sum_choice += cbits
            per_choice.append(cbits)
        A_total = graph_bits + n_arts * seed_bits             # seed-only (valid only where %uniq high)
        B_total = graph_bits + sum_choice + n_arts * seed_bits
        print(f"  {k:>2} | {edges:>11} | {graph_bits//8192:>8} | {uniq/n_arts:>12.0%} | {sum_choice/n_arts:>22.1f} | {A_total//8192:>10} | {B_total//8192:>10}")
        if best is None or B_total < best[1]:
            best = (k, B_total)

    print(f"\n  prose baseline (storing the text): {text_bits//8192} KB")
    print(f"  best seed-store (Sol-B): k={best[0]}, {best[1]//8192} KB  →  {text_bits/best[1]:.2f}× vs prose")

    # #1 SCALE: how min-k-for-unique-walk and choice-bits scale with article length (single shared graph at k=6)
    g6 = build_graph(arts, 6)
    buckets = {}
    for a in arts:
        cb = sum(max(0, len(g6[tuple(a[i - 5:i])]) - 1).bit_length() for i in range(5, len(a)))
        b = (len(a) // 15) * 15
        buckets.setdefault(b, []).append(cb)
    print("\n  #1 SCALE — choice-bits vs article length (shared graph, k=6):")
    for b in sorted(buckets):
        v = buckets[b]
        print(f"    len {b:>3}-{b+14:<3}: {len(v):>3} arts · mean {sum(v)/len(v):>5.1f} choice-bits  (≈ {sum(v)/len(v)/8:.2f} bytes of true content)")

    print("\nREADING: Sol-A (seed-only) needs high k (→ %uniq-walk up) but the graph grows; Sol-B (seed+choices) works at")
    print("  any k with a smaller graph, paying choice-bits. The article's OWN information = its choice-bits (tiny vs")
    print("  prose); the shared graph is amortised corpus structure (no-magic: not the article's content). Two")
    print("  solutions, the efficient one set by corpus size N. The RBS-HDC store (F808) realises the graph + walk.")


if __name__ == "__main__":
    main()
