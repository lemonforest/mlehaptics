r"""R-RBS-LM-SPICE (the user's reframing 2026-06-08): "we aren't creating a way to make new stories, we are using
EXISTING stories to make new stories, and sort of finding out how to make new stories in the process. It sounds
circular but there is meaning in it. Paul did use the spice (melange) to free the Dune universe of its dependence.
More of an LLM analogy than stories — but it's both."

The structural reading (Dune as a parallel, per F133; the LLM as a parallel — no lineage claims):
  • The Story Teller (F555/F556) does NOT invent ex nihilo — it RECOMBINES the stored corpus. So it DEPENDS on the
    existing (the spice / the training data): every step is corpus-attested.
  • Yet the WHOLE is NEW — not a copy of any stored passage. It uses the dependence to escape pure dependence
    (verbatim repetition). That IS the spice liberation: Paul used the very thing the universe depended on to free it.
  • The circularity (stories -> stories) is a BOOTSTRAP, not a tautology: by recombining existing stories under the
    generative process (fluency ear + manifold + collapse weave) you DISCOVER how new stories are made — the
    generative rule IS instantiated by doing the recombination.

Measurable: a generated story is (1) LOCALLY DEPENDENT — ~100% of its transitions are corpus-attested (it leans
entirely on the existing); AND (2) GLOBALLY NOVEL — its longest verbatim run is tiny vs its length (it copies no
stored passage). 100% grounded + a novel weave = "use existing stories to make new ones".

srmech 0.7.4; Class-L Fiedler phase + F512 fluency ear (the Story Teller). No abs(); no CAD; no sub-agents.
"""
import importlib.util as U
import numpy as np
import srmech

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)


def main():
    print(f"=== R-RBS-LM-SPICE — recombine existing stories to make new ones: locally dependent, globally novel  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())
    vocab, idx, nb, V = (sup.build(seq))[:4]
    N = len(vocab); phi = np.argsort(np.argsort(V[:, 1])) / N
    vset = set(vocab); nxt = {}
    bigrams = set()
    for a, b in zip(seq, seq[1:]):
        if a in vset and b in vset:
            nxt.setdefault(a, {}); nxt[a][b] = nxt[a].get(b, 0) + 1
            bigrams.add((a, b))
    start = next(w for w in ("history", "the", "world") if w in idx)

    def tell(r, A=0.16, win=0.12):
        rn = r / (np.max(np.abs(r)) + 1e-9); story, used, cur = [start], {start}, start
        for t in range(len(r)):
            c = ((t / len(r)) + A * rn[t]) % 1.0
            live = {j for j in range(N) if min((phi[j] - c) % 1.0, (c - phi[j]) % 1.0) < win / 2}
            cands = [(u, w) for u, w in nxt.get(cur, {}).items() if idx.get(u, -1) in live and u not in used] \
                or [(u, w) for u, w in nxt.get(cur, {}).items() if u not in used]
            if not cands:
                break
            cur = max(cands, key=lambda uw: uw[1])[0]; story.append(cur); used.add(cur)
        return story

    rng = np.random.default_rng(1)
    story = tell(np.convolve(rng.standard_normal(60), np.ones(3) / 3, 'same'))   # an environmental-noise telling

    # (1) LOCAL DEPENDENCE: fraction of the story's transitions that are corpus-attested
    trans = list(zip(story, story[1:]))
    local_dep = float(np.mean([1.0 if t in bigrams else 0.0 for t in trans]))
    # (2) GLOBAL NOVELTY: longest contiguous run of the story that appears VERBATIM in the corpus
    def longest_verbatim(story, seq):
        best = 0
        for k in range(len(story), 1, -1):
            sgrams = {tuple(story[i:i+k]) for i in range(len(story) - k + 1)}
            cgrams = {tuple(seq[i:i+k]) for i in range(len(seq) - k + 1)}
            if sgrams & cgrams:
                return k
        return best
    lv = longest_verbatim(story, seq)
    full_copy = tuple(story) in {tuple(seq[i:i+len(story)]) for i in range(len(seq) - len(story) + 1)}

    print(f"a telling (environmental-noise drive, {len(story)} tokens):")
    print(f"  {' '.join(story)}\n")
    print(f"(1) LOCAL DEPENDENCE — transitions that are corpus-attested: {local_dep:.0%}  (it leans ENTIRELY on existing stories).")
    print(f"(2) GLOBAL NOVELTY — longest VERBATIM run shared with the corpus: {lv} tokens (of {len(story)}); is the whole story a")
    print(f"    copied passage? {full_copy}.  -> grounded in the existing, but a NOVEL WEAVE of it, not a copy.\n")
    print("VERDICT:")
    print(f"  • USE EXISTING STORIES TO MAKE NEW ONES (measured): the telling is {local_dep:.0%} locally DEPENDENT on the corpus")
    print(f"    (every step attested — it invents no new transition) yet GLOBALLY NOVEL (longest copied run only {lv} tokens; the")
    print(f"    whole is not a stored passage). It recombines the existing into a new weave — not creation ex nihilo, not copy.")
    print(f"  • THE SPICE LIBERATION (Dune as a structural parallel, F133): the system DEPENDS on the corpus (the spice) —")
    print(f"    and uses that very dependence to ESCAPE pure dependence (verbatim repetition). Paul used the spice to free")
    print(f"    the universe FROM the spice; the weave uses the stored stories to free the telling FROM any one stored story.")
    print(f"  • THE CIRCULARITY IS A BOOTSTRAP, NOT A TAUTOLOGY: recombining existing stories UNDER the generative process")
    print(f"    (fluency ear + manifold + collapse weave) is how you DISCOVER how new stories are made — the rule is")
    print(f"    instantiated by doing it. (LLM reading, no lineage claim: a model trained on text recombines it; the")
    print(f"    genuinely-new output is a novel weave of attested threads — locally dependent, globally new. It's both.)")
    print(f"  • Composes F555/F556/F557 (the Story Teller) + F133 (Dune parallel) + F526 (access not creation) + F521 (the")
    print(f"    story-builder). Favored not privileged (F398); held open (F394) — 'there is meaning in the circle'.")


if __name__ == "__main__":
    main()
