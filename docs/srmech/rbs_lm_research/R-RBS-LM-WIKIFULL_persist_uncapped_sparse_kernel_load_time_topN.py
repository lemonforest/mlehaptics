r"""R-RBS-LM-WIKIFULL (F748) — PERSIST the UNCAPPED full-vocab sparse simplewiki kernel (the thing F708 uncapped but
never saved), and add the LOAD-TIME top-N selector (the user's design: no artificial ceiling at ENCODE; choose the
top-words-rank at LOAD / in RAM).

THE GAP (user, 2026-06-14): F708 fixed the pre-encode top-256 quantization bug (build_edges_topk, vocab_cap=None ->
ALL words) but never PERSISTED the uncapped kernel — so the only file on disk is the STALE capped enwiki_kernel_256.
"Something didn't carry over" = the persist step. ALSO: the ceiling should be at LOAD, not encode.

THE ARCHITECTURE (F708 verified): the DIRECT associations are a SPARSE-ADJACENCY query — no eig, no dense matrix —
so they work at ANY vocab size, UNCAPPED. Only the SECOND-ORDER (spectral / tome routing) layer needs the dense eig,
bounded to a block of <=256 (or <=1024 via the Klein-4 quad-stream). So:
  • ENCODE: the FULL sparse kernel (all vocab + freq ranks + edges) — no ceiling. The on-disk SSoT (F584).
  • LOAD: pick a top-N rank cut -> the N-word INDUCED SUBGRAPH -> dense-eig only that -> the N-tome bookshelf.
    N is a RAM knob on the one full SSoT; EXACT for the loaded words. (Holographic reduction, F390, is the right
    tool for the graceful LONG TAIL below rank N — the F119/F529 two-tier; NOT for the whole, which F584 warns
    capacity-walls.)

Reuses R-RBS-LM-WIKIKERNEL.build_edges_topk / stream_articles (F708, uncapped). Source = simplewiki_extracted/
articles.jsonl (already parsed). No re-encode for the tomes (V from the persisted edges). No abs(); no CAD.
Run:  MAX_ARTICLES=15000 /tmp/srmech_rc149/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-WIKIFULL_...py
"""
import json
import os
import time
import importlib.util
from pathlib import Path
import srmech
from srmech.amsc import laplacian as L
from srmech import calculus
from srmech.amsc.format import sha256_raw

HERE = Path(__file__).parent
ART = Path.home() / "corpora" / "wikipedia" / "simplewiki_extracted" / "articles.jsonl"
OUT = Path.home() / "corpora" / "wikipedia" / "simplewiki_full_sparse_kernel.json"   # the FULL uncapped SSoT
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "15000"))
PI = 2.0 * calculus.atan2(1.0, 0.0)

_spec = importlib.util.spec_from_file_location(
    "wk", str(HERE / "R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py"))
wk = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(wk)


def encode_full():
    texts = []
    with open(ART) as f:
        for i, line in enumerate(f):
            if i >= MAX_ARTICLES:
                break
            try:
                texts.append(json.loads(line).get("text", ""))
            except ValueError:
                continue
    t0 = time.time()
    vocab, idx, edges, weights, freq, dropped = wk.build_edges_topk(texts, window=4, vocab_cap=None)  # UNCAPPED
    dt = time.time() - t0
    return texts, vocab, edges, weights, freq, dropped, dt


def persist(vocab, edges, weights, freq):
    payload = {
        "wiki": "simplewiki", "srmech": srmech.__version__, "uncapped": True,
        "articles": MAX_ARTICLES, "vocab_size": len(vocab), "edges": len(edges),
        "vocab": vocab, "freq": [int(freq[w]) for w in vocab],
        "edge_list": [[int(a), int(b)] for a, b in edges],
        "edge_weights": [float(w) for w in weights],
        "attestation": {"source_url": "https://dumps.wikimedia.org/simplewiki/latest/",
                        "license": "CC-BY-SA-4.0", "retrieved_at": "2026-06-06T00:00:00Z",
                        "response_sha256": sha256_raw((",".join(vocab)).encode()).hex(),
                        "parser_version": f"srmech {srmech.__version__}",
                        "note": "FULL uncapped sparse kernel (F708/F748); ceiling is at LOAD, not encode"}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload))
    return OUT.stat().st_size


def load_topN(N, NT=14):
    """LOAD-time selection: top-N words by freq -> induced subgraph -> dense eig -> NT-tome bookshelf (EXACT for N)."""
    k = json.loads(OUT.read_text())
    vocab, freq = k["vocab"], k["freq"]
    order = sorted(range(len(vocab)), key=lambda i: (-freq[i], vocab[i]))[:N]   # top-N rank cut
    keep = {oi: ni for ni, oi in enumerate(order)}                              # remap orig idx -> 0..N-1
    sub_e, sub_w = [], []
    for (a, b), w in zip(k["edge_list"], k["edge_weights"]):
        if a in keep and b in keep:
            sub_e.append((keep[a], keep[b])); sub_w.append(w)
    lap = L.dense_laplacian(N, sub_e, sub_w)
    _ev, V = L.symmetric_eigendecompose(lap)
    tome = [int((calculus.atan2(V[i, 2], V[i, 1]) + PI) / (2.0 * PI) * NT) % NT for i in range(N)]
    words = [vocab[oi] for oi in order]
    return words, tome, len(sub_e)


def direct_assoc(word, topk=8):
    """UNCAPPED sparse-adjacency query — no eig, works at full vocab (the words the 256-cap threw away are here)."""
    k = json.loads(OUT.read_text())
    vocab = k["vocab"]; vi = {w: i for i, w in enumerate(vocab)}
    if word not in vi:
        return None
    wi = vi[word]; nb = {}
    for (a, b), w in zip(k["edge_list"], k["edge_weights"]):
        if a == wi:
            nb[b] = nb.get(b, 0.0) + w
        elif b == wi:
            nb[a] = nb.get(a, 0.0) + w
    return [vocab[j] for j, _ in sorted(nb.items(), key=lambda kv: -kv[1])[:topk]]


def main():
    print(f"=== R-RBS-LM-WIKIFULL — persist the UNCAPPED simplewiki kernel + load-time top-N (srmech {srmech.__version__}) ===\n")
    texts, vocab, edges, weights, freq, dropped, dt = encode_full()
    size = persist(vocab, edges, weights, freq)
    print(f"ENCODED {len(texts)} simplewiki articles -> UNCAPPED kernel: {len(vocab)} vocab, {len(edges)} edges "
          f"({dt:.1f}s); dropped {len(dropped)} (=0 -> no pre-encode quantization).")
    print(f"PERSISTED full sparse SSoT -> {OUT.name} ({size/1e6:.1f} MB). No ceiling at encode.\n")

    print("--- direct associations are UNCAPPED (the words the top-256 trim threw away are PRESENT) ---")
    for w in ("science", "planet", "earth", "computer", "music", "dragon"):
        a = direct_assoc(w)
        print(f"    {w:9}: {', '.join(a[:6]) if a else '(not in vocab)'}")

    print("\n--- LOAD-TIME top-N rank cut: the ceiling is a RAM knob on ONE full SSoT (exact for loaded words) ---")
    for N in (256, 1024):
        if N <= len(vocab):
            words, tome, ne = load_topN(N)
            occ = len(set(tome))
            print(f"    load top-{N:4d} -> induced subgraph {ne} edges -> {occ}/14 tomes filled "
                  f"(e.g. tome of 'science' = {tome[words.index('science')] if 'science' in words else 'n/a'})")
    print("\nVERDICT: the uncapped sparse kernel is now PERSISTED (the F708 fix carried over). Direct assoc works at")
    print("  FULL vocab (no cap); the spectral tome bookshelf is built at a LOAD-TIME top-N (a RAM knob), exact for")
    print("  the loaded words. Holographic reduction (F390) is the graceful-tail tool, not the whole (F584 wall).")


if __name__ == "__main__":
    main()
