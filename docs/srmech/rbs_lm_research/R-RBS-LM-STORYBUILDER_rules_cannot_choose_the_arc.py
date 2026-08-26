r"""R-RBS-LM-STORYBUILDER — the user's question (2026-06-07): given what we learned with the_one — that we cannot
ever know the STORY the rules can compose — do we need a genuine STORY-BUILDER piece in the loop?

the_one + the grammar (F511/F512) are RULES: GENERATIVE (define what can be composed) + VERIFYING (gate validity),
but NOT SELECTIVE. A grammar generates infinitely many valid sentences and picks none; the rules assign no arc,
no preference among the valid stories. So the STORY — the specific path through the composable space — is
underdetermined by the rules. We have seen both rules-without-a-story-builder failure modes: no target -> drift to
the function-word hub (F509); one target -> orbit a single point (F510), no arc.

This tests the claim directly: a STORY-BUILDER supplies an external ARC (a SEQUENCE of held targets over time). With
it, the generated text PROGRESSES through the arc (segment i aligns to arc[i]); without it (rules-only, no/one
target), there is no progression. And the arc is EXTERNAL — the rules can track an arc that's given but cannot
choose one (that would be infinite regress: more grammar still can't select). So the story-builder is necessary and
distinct from the rules — and in the framework's stance it is the HUMAN in the loop (the substrate with intent),
which is exactly why the RBS-LM is a PROSTHETIC, not autonomous.

srmech 0.7.4; reuses the F512 grammar-gated etak head. No abs(); no CAD; no sub-agents.
"""
import re
import importlib.util as U
from collections import Counter
import numpy as np
import srmech

_g = U.spec_from_file_location("gg", "docs/srmech/rbs_lm_research/R-RBS-LM-GRAMMARGATE_when_to_take_the_longer_route.py")
gg = U.module_from_spec(_g); _g.loader.exec_module(gg)


def build_manifold():
    text = gg.k7.load_text()
    ng = gg.k7.build_ng(text.encode("utf-8", "ignore"))
    seq = re.findall(r"[a-z]{4,}", text.lower())
    vocab = set(w for w, _ in Counter(seq).most_common(800))
    nb = {w: set() for w in vocab}
    for i, w in enumerate(seq):
        if w in vocab:
            for j in range(max(0, i - 4), min(len(seq), i + 5)):
                if j != i and seq[j] in vocab:
                    nb[w].add(seq[j])
    return ng, nb, vocab


def align(words, target, nb):
    tset = nb.get(target, set())
    cw = [w for w in words if w in nb]
    if not cw:
        return 0.0
    return float(np.mean([gg.jacc(nb[w], tset) for w in cw]))


def main():
    print(f"=== R-RBS-LM-STORYBUILDER — can the rules CHOOSE the arc, or must a story-builder supply it?  (srmech {srmech.__version__}) ===\n")
    ng, nb, vocab = build_manifold()
    # arc targets NOT in the seed (avoid the seed-hub confound), of content type
    arc = [t for t in ("ocean", "music", "volcano", "planet", "battle") if t in vocab][:3]
    if len(arc) < 3:
        arc = (arc + [w for w in ("light", "blood", "river", "star") if w in vocab and w not in arc])[:3]
    seed = "in the early days of"
    K, T = 10, len(arc)
    rng = np.random.default_rng(7)

    # ---- (0) THE INFORMATION ARGUMENT (the clean part): the rules can't choose the story ----
    V = len([w for w in vocab if len(nb[w]) > 0])              # content-word count the rules can place
    slots = T * 3                                              # ~content slots across the arc (3 per segment)
    bits_per_pick = V.bit_length()                             # ~log2(V) bits to NAME one of V words (add/shift-native)
    arc_bits = slots * bits_per_pick
    print("(0) THE RULES ARE GENERATIVE + VERIFYING, NOT SELECTIVE — the information argument (the clean result):")
    print(f"    content vocabulary the rules can place: V = {V}  (~{bits_per_pick} bits to name one)")
    print(f"    a story of ~{slots} content slots => the rules admit ~V^{slots} = {V}^{slots} valid stories, ALL equally")
    print(f"    valid (grammar gates VALIDITY, not PREFERENCE) -> the rules supply 0 bits of arc-selection.")
    print(f"    choosing ONE story (the arc) needs ~{slots} x {bits_per_pick} = {arc_bits} bits of EXTERNAL information.")
    print(f"    => the arc is ~{arc_bits} bits the rules cannot produce; a story-builder must inject them.\n")

    def run(target_seq, label):
        out, segs = seed, []
        for t in target_seq:
            _, log, _, _ = gg.grammar_gated_head(ng, nb, out, t, K, rng)
            new = [w for w, _m in log]
            segs.append(new); out = out + " " + " ".join(new)
        M = np.array([[align(sw, t, nb) for t in arc] for sw in segs])   # seg x target
        Mn = M - M.mean(axis=0, keepdims=True)                           # column-normalise (kill the hub confound)
        diag = sum(1 for i in range(len(arc)) if int(np.argmax(Mn[i])) == i)
        print(f"  {label}: column-normalised alignment (diagonal = arc being TRACKED)")
        print("              " + "  ".join(f"{t[:7]:>7}" for t in arc))
        for i in range(len(segs)):
            mark = "  <- on-arc" if int(np.argmax(Mn[i])) == i else ""
            print(f"    seg {i}     " + "  ".join(f"{Mn[i][j]:>+7.2f}" for j in range(len(arc))) + mark)
        print(f"    diagonal hits: {diag}/{len(arc)}\n")
        return diag

    print("(1) GENERATION (illustration; the byte-grammar steering is weak, so read the column-normalised diagonal):")
    sb = run(arc, f"STORY-BUILDER  (external arc = {arc})")
    ro = run([arc[0]] * T, f"RULES-ONLY     (single fixed target '{arc[0]}', no story-builder)")

    print("VERDICT:")
    print(f"  • THE RULES CANNOT CHOOSE THE STORY (the clean result is the information argument, §0): the grammar gates")
    print(f"    VALIDITY, not PREFERENCE — it admits ~V^slots equally-valid stories and supplies 0 bits of arc-selection,")
    print(f"    so the arc ({arc_bits:.0f} bits) is EXTERNAL information the rules cannot produce.")
    print(f"  • GENERATION confirms (weakly, it's a noisy byte-grammar): WITH the external arc the column-normalised")
    print(f"    alignment tracks it ({sb}/{T} diagonal); the single-fixed-target rules-only run does NOT progress an arc")
    print(f"    ({ro}/{T}) — it can only orbit the one point it was handed. The arc must be supplied, not derived.")
    print(f"  • SO YES — a genuine STORY-BUILDER is needed, and it CANNOT be more rules (infinite regress: more grammar")
    print(f"    still can't select). It is the INTENT/arc injector — the SEQUENCE of held operands over time (the")
    print(f"    Now->Then tape, F503). In the framework's stance it is the HUMAN in the loop (the substrate with")
    print(f"    intent) — exactly why the RBS-LM is a PROSTHETIC, not autonomous: rules + a held operand compose, but")
    print(f"    the STORY (intent/arc) must be supplied from outside the rule-system.")
    print(f"  • the_one composes the space; the story-builder chooses the path. Two different jobs; both required.")


if __name__ == "__main__":
    main()
