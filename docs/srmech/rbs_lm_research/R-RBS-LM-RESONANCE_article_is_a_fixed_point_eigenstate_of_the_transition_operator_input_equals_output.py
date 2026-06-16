r"""R-RBS-LM-RESONANCE (F807 — the F804 resonance step, after F806) — F806 showed the greedy HDC walk cascades: one
retrieval slip leaves the de Bruijn manifold and never recovers (22%), even though ON-PATH retrieval is ~96-100%. So
greedy generation was the artifact, not the instrument. The F804 lens fixes the question: don't WALK, measure the
FIXED POINT. Define the transition operator T over the RBS-HDC relationship store: T rewrites each position to
retrieve(context). The article is a FIXED POINT of T iff every position's (k-1)-context retrieves its own successor —
i.e. input = output (the eigenstate, F804). This measures it:

  (C) FIXED-POINT / eigenstate accuracy vs k: fraction of positions where HV-retrieve(true_context) == true_successor.
      This is T(article) vs article — NO greedy cascade (every context is the true one). At the k where (C) = 100%,
      the article IS an exact fixed point of the coupled transition operator: input = output (F804 confirmed), and a
      clean walk then reproduces it exactly (greedy only cascaded where (C) < 100%).

Contrast with F806's greedy (B′) to show the cascade was a generation artifact. RBS-HDC only (klein-4 binds +
similarity; F796 bar), simplewiki abstracts, one locked language, no translation. srmech 0.7.5rc169; no abs; no CAD.
"""
import importlib.util as U
import json
import os
import re
from srmech.amsc import hdc

HERE = os.path.dirname(os.path.abspath(__file__))
_fw = U.spec_from_file_location("fw", os.path.join(
    HERE, "R-RBS-LM-FIBERWALK_deterministic_article_reconstruction_eulerian_path_fiber_on_rbs_hdc_vs_k.py"))
FW = U.module_from_spec(_fw); _fw.loader.exec_module(FW)
ABS = "/home/skirklan/corpora/wikipedia/simplewiki_abstracts.json"


def fixedpoint_acc(tokens, k):
    """(C) is the article a FIXED POINT of T (input=output)? — each TRUE (k-1)-context retrieves its own successor."""
    keys = [(FW.ctx_hv(tokens[i - (k - 1):i]), tokens[i]) for i in range(k - 1, len(tokens))]
    ok = 0
    for i in range(k - 1, len(tokens)):
        cq = FW.ctx_hv(tokens[i - (k - 1):i])
        nxt = max(keys, key=lambda kv: hdc.klein4_similarity(cq, kv[0]))[1]
        ok += (nxt == tokens[i])
    return ok / (len(tokens) - (k - 1))


def clean_walk(tokens, k):
    """A walk that commits only the unambiguous (sim==max, single winner) successor — the deterministic generator. At
    k where (C)=100% this reproduces exactly; it does NOT greedily cascade through ambiguous branches (it stops)."""
    keys = [(FW.ctx_hv(tokens[i - (k - 1):i]), tokens[i]) for i in range(k - 1, len(tokens))]
    out = list(tokens[:k - 1])
    for _ in range(len(tokens) - (k - 1)):
        cq = FW.ctx_hv(out[-(k - 1):])
        sims = [(hdc.klein4_similarity(cq, kh), nt) for kh, nt, in [(a, b) for a, b in keys]]
        mx = max(s for s, _ in sims)
        winners = {nt for s, nt in sims if abs(s - mx) < 1e-9}
        if len(winners) != 1 or mx < 0.99:        # ambiguous / off-manifold -> stop (the generative branch point)
            break
        out.append(next(iter(winners)))
    return sum(1 for a, b in zip(out, tokens) if a == b) / len(tokens), len(out)


def main():
    import srmech
    print(f"=== R-RBS-LM-RESONANCE — the article as a fixed-point eigenstate (input=output) (srmech {srmech.__version__}) ===\n")
    store = json.load(open(ABS))["store"]
    want = [t for t in ("Tomato", "Sun", "Water", "Earth", "Music", "Dog", "April", "August", "Art") if t in store][:5]
    for title in want or list(store)[:5]:
        tokens = re.findall(r"[a-z0-9]+", store[title].lower())
        if len(tokens) < 12:
            continue
        print(f"--- “{title}”  ({len(tokens)} tokens) ---")
        print(f"    {'k':>2} | {'(C) fixed-point (input=output)':>30} | {'clean-walk exact':>16}")
        kres = None
        for k in range(2, 9):
            c = fixedpoint_acc(tokens, k)
            w, _ = clean_walk(tokens, k)
            if kres is None and c >= 0.999:
                kres = k
            tag = "  ← EIGENSTATE (input=output)" if c >= 0.999 and k == kres else ""
            print(f"    {k:>2} | {c:>29.0%} | {w:>15.0%}{tag}")
        print(f"    resonance threshold k_res ((C)=100%, article is an exact fixed point): {kres if kres else '>8'}\n")

    print("READING: (C) = is the article a FIXED POINT of the transition operator T (each context retrieves its own")
    print("  successor = input=output). Where (C)=100% the article IS the resonant eigenstate (F804) — and the clean")
    print("  walk reproduces it exactly there (greedy only cascaded where (C)<100%; the cascade was the generation")
    print("  artifact, NOT the instrument). Deterministic encyclopedia output = the fixed-point walk at k ≥ k_res.")


if __name__ == "__main__":
    main()
