r"""R-RBS-LM-U1PARITY (F724) — §17.1 migration gate: do the shipped srmech.amsc.text ops (rc50) reproduce our
hand-rolled wiki-kernel edges? Parity check before migrating off content_words + build_edges_topk.

User direction (2026-06-09): "run that parity check (and, if it matches, do the migration)."

The migration (the §17.1 ours-side item): replace our hand-rolled content_words + build_edges_topk with
srmech.amsc.text.{tokenize, cooccurrence_edges} (rc50, F723), keeping ONLY our corpus-specific wiki-markup strip
(strip_wiki_markup_hardened, F700) in the adapter — markup-strip is correctly NOT tokenize's job (§40 boundary).

GATE = parity on a clean (markup-free) sample, with aligned params (same stoplist, same window, same vocab):
  (A) TOKENIZATION: ours = [w for w in content_words(a) if w not in DEFAULT_STOPLIST]  vs  tokenize(a, stoplist=…)
  (B) EDGES: our build_edges_topk(arts) vs cooccurrence_edges(shipped_docs, vocab=our_vocab) — same word-pairs +
      same weights?

Run with the rc50 venv: /tmp/srmech_rc50/venv/bin/python3. No abs(); srmech-first.
"""
import sys
import importlib.util as u

sys.path.insert(0, "docs/srmech/rbs_lm_research")
_spec = u.spec_from_file_location("wk", "docs/srmech/rbs_lm_research/R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py")
wk = u.module_from_spec(_spec); _spec.loader.exec_module(wk)
import srmech
from srmech.amsc import text as T

WINDOW = 2
ARTS = [
    "the sun is a star and the planet orbits the sun每 day",
    "a planet and a moon orbit a star in the galaxy",
    "café culture in the city is naïve about the café",
    "the moon and the sun and the star light the night",
]


def ours_tokens(a):
    return [w for w in wk.content_words(a) if w not in wk.DEFAULT_STOPLIST]


def edge_map(vocab, edges, weights):
    """{frozenset({wi, wj}): weight} keyed by words (index-order-independent)."""
    return {frozenset((vocab[i], vocab[j])): float(w) for (i, j), w in zip(edges, weights)}


def main():
    print(f"=== R-RBS-LM-U1PARITY (F724) — wiki kernel vs shipped srmech.amsc.text  (srmech {srmech.__version__}) ===\n")

    # (A) TOKENIZATION PARITY
    print("(A) TOKENIZATION parity (content_words+stoplist  vs  tokenize(stoplist=…)):")
    tok_match = 0
    shipped_docs = []
    for i, a in enumerate(ARTS):
        ours = ours_tokens(a)
        theirs = T.tokenize(a, stoplist=wk.DEFAULT_STOPLIST)
        shipped_docs.append(theirs)
        same = ours == theirs
        tok_match += same
        if not same:
            print(f"    art {i}: DIFFER")
            print(f"      ours  : {ours}")
            print(f"      theirs: {theirs}")
            only_o = [t for t in ours if t not in theirs]; only_t = [t for t in theirs if t not in ours]
            print(f"      ours-only: {only_o}  | theirs-only: {only_t}")
    print(f"    -> {tok_match}/{len(ARTS)} articles tokenize identically\n")

    # (B) EDGE PARITY (feed each side its OWN tokenization, aligned window; compare on the shared vocab)
    vocab_o, idx_o, edges_o, w_o, *_ = wk.build_edges_topk(ARTS, window=WINDOW, vocab_cap=None)
    n_t, edges_t, w_t = T.cooccurrence_edges(shipped_docs, window=WINDOW, vocab=vocab_o)
    map_o = edge_map(vocab_o, edges_o, w_o)
    map_t = edge_map(vocab_o, edges_t, w_t)
    pairs_match = set(map_o) == set(map_t)
    weights_match = map_o == map_t
    print("(B) EDGE parity (same vocab, window=2):")
    print(f"    ours: {len(map_o)} edges | shipped: {len(map_t)} edges | same PAIR set: {pairs_match}")
    print(f"    same weights too: {weights_match}")
    if not weights_match:
        diffs = {k: (map_o.get(k), map_t.get(k)) for k in (set(map_o) | set(map_t)) if map_o.get(k) != map_t.get(k)}
        for k, (vo, vt) in list(diffs.items())[:12]:
            print(f"      {tuple(sorted(k))}: ours={vo} shipped={vt}")
        print(f"    ({len(diffs)} differing edges)")
    print()

    full = (tok_match == len(ARTS)) and weights_match
    print("VERDICT (F724):")
    print(f"  • tokenization parity: {tok_match}/{len(ARTS)};  edge-pair parity: {pairs_match};  weight parity: {weights_match}")
    if full:
        print("  • FULL PARITY -> the migration is safe: swap content_words+build_edges_topk for the shipped ops,")
        print("    keeping strip_wiki_markup_hardened (F700) in the adapter.")
    else:
        print("  • NOT full parity -> deltas above are the migration gate; characterize before swapping (no silent")
        print("    migration). The shipped ops are adoptable where the deltas are understood/acceptable.")


if __name__ == "__main__":
    main()
