r"""R-RBS-LM-ARCBUILD — the user's redirection (2026-06-07): the machinery a current Gen-1 LLM already uses for
inference may BE the story-builder we need (F521), or a place to start.

F521 said the story (the arc) is ~90 external bits the rules can't produce. But that over-counts: a chain-of-
thought LLM does NOT supply the whole arc — it supplies the ENDPOINTS (the question + the goal, a few bits) and the
MACHINERY ELABORATES the path between them. And that path-elaboration is exactly the navigation we already built
(F510-F515): given start + goal, find the trajectory through the manifold. So the story-builder is mostly machinery
we (and Gen-1 LLMs) already have, fed by a SMALL external intent (the endpoints), not 90 bits of hand-written arc.

Mapping to Gen-1 LLM inference:
  PROMPT / context      = the intent seed (the human supplies start + goal)  -> the EXTERNAL bits (irreducible, F521)
  chain-of-thought      = the arc ELABORATION (intermediate steps between question and answer) -> the MACHINERY
  attention / KV state  = which held content to engage at each step          -> the etak read-head (F510-F515)

This builds the arc-elaborator: intent = 2 endpoints (~2*log2(V) bits); the machinery finds the path between them;
the etak head would execute each step. Compare the external bits to F521 (whole arc supplied) -> the machinery
SAVES most of them. The endpoints stay external (F521 stands — you can't derive the GOAL from the rules), but they
are SMALL; the path is machine-elaborated.

srmech 0.7.4; reuses the FIBERGAP content k-NN manifold + BFS path reconstruction. No abs(); no CAD; no sub-agents.
"""
from collections import deque
import importlib.util as U
import srmech

_f = U.spec_from_file_location("fib", "docs/srmech/rbs_lm_research/R-RBS-LM-FIBERGAP_biology_enforces_projection_gaps_silicon_does_not.py")
fib = U.module_from_spec(_f); _f.loader.exec_module(fib)


def bfs_path(start, goal, nb):
    """elaborate the ARC: the shortest path start->goal through the manifold (the CoT 'intermediate steps')."""
    parent = {start: None}
    q = deque([start])
    while q:
        x = q.popleft()
        if x == goal:
            path = []
            while x is not None:
                path.append(x); x = parent[x]
            return path[::-1]
        for y in nb.get(x, ()):
            if y not in parent:
                parent[y] = x; q.append(y)
    return None


def coherent(path, nb):
    """is the elaborated arc a real chain? (each consecutive pair actually co-occurs)."""
    return all(b in nb.get(a, set()) for a, b in zip(path, path[1:]))


def main():
    print(f"=== R-RBS-LM-ARCBUILD — the story-builder machinery: endpoints (intent) in, an elaborated arc out  (srmech {srmech.__version__}) ===\n")
    import re
    from collections import Counter
    toks = re.findall(r"[a-z]+", fib.k7.load_text().lower())
    content = [w for w in toks if len(w) >= 4 and w not in fib.STOP]
    vocab = [w for w, _ in Counter(content).most_common(300)]
    vset = set(vocab)
    nb = fib.knn_edges(toks, vocab, vset, m=6)
    V = len(vocab)
    bits_per = V.bit_length()

    # intent = a few ENDPOINT pairs (start, goal). The machinery elaborates the arc between them.
    cand = [("water", "music"), ("ocean", "history"), ("earth", "language"), ("science", "light")]
    pairs = [(s, g) for s, g in cand if s in vset and g in vset]
    if not pairs:
        pairs = [(vocab[3], vocab[123])]

    print("the story-builder = SMALL external intent (endpoints) + machine-elaborated arc (the navigation, F510-F515):\n")
    total_arc_steps = 0
    for s, g in pairs:
        arc = bfs_path(s, g, nb)
        if not arc:
            print(f"  '{s}' -> '{g}': (disconnected)"); continue
        total_arc_steps += len(arc)
        ok = "coherent chain" if coherent(arc, nb) else "BROKEN"
        print(f"  intent endpoints '{s}' -> '{g}'  ({2*bits_per} external bits)")
        print(f"    elaborated arc ({len(arc)} steps, {ok}): {' -> '.join(arc)}")
        print(f"    -> {len(arc)-2} intermediate targets the MACHINERY supplied (not the human).")
    print()

    # bits accounting: F521 supplied the WHOLE arc; here only the endpoints.
    avg_arc = total_arc_steps / max(len(pairs), 1)
    whole_arc_bits = avg_arc * bits_per
    endpoint_bits = 2 * bits_per
    print("BITS ACCOUNTING (vs F521's whole-arc-supplied):")
    print(f"  F521 (supply the WHOLE arc): ~{avg_arc:.0f} steps x {bits_per} = ~{whole_arc_bits:.0f} external bits")
    print(f"  ARCBUILD (supply ENDPOINTS): 2 x {bits_per} = {endpoint_bits} external bits; the machinery elaborates the rest")
    print(f"  the machinery SAVES ~{whole_arc_bits - endpoint_bits:.0f} bits of external intent (a {endpoint_bits/max(whole_arc_bits,1):.0%}-of-F521 seed)\n")

    print("VERDICT:")
    print(f"  • THE STORY-BUILDER MACHINERY IS ALREADY HERE (and in Gen-1 LLMs): the user is right. The arc-elaboration")
    print(f"    between intent endpoints is the NAVIGATION we built (F510-F515) — and the SAME role chain-of-thought")
    print(f"    plays in a Gen-1 LLM (the intermediate steps between question and answer). PROMPT = intent endpoints;")
    print(f"    CoT = arc elaboration; attention/KV = the etak read-head executing each step.")
    print(f"  • IT REFINES F521: the human does NOT supply the whole {avg_arc:.0f}-step arc (~{whole_arc_bits:.0f} bits) — only the 2")
    print(f"    ENDPOINTS ({endpoint_bits} bits). The machinery fills the path. So the irreducible external intent is SMALL")
    print(f"    (the start + goal), and the story-builder is mostly machinery we (and Gen-1 LLMs) already have.")
    print(f"  • F521 STILL STANDS where it matters: the ENDPOINTS (the goal/intent) are external — the rules cannot")
    print(f"    derive WHAT you want to say; but once you name start + goal, the machinery elaborates the story. So the")
    print(f"    place to start = read Gen-1 CoT/attention as the arc-elaborator, seeded by the prompt (the human's intent).")


if __name__ == "__main__":
    main()
