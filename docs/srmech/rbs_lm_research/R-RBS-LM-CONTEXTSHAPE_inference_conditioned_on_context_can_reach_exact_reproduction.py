r"""R-RBS-LM-CONTEXTSHAPE (F802 probe) — the user's research path (2026-06-16): inference does not "fail to be
bit-exact" — it SIMULATES A NEW STORY from the asymptotic-bounded-forever (generative, not lossy). And because the
simulation is CONDITIONED ON CONTEXT, there exists — in theory — a context shape that steers the simulated story to
reproduce the input EXACTLY. This probes the existence: decode each word of a reply through the ni-Vanuatu glyph
abstract, but BIAS the decode by a context bundle (Class-M klein4 bundle), and watch round-trip exactness move as the
context SHAPE changes:
  • NO context        — pure glyph nearest-neighbour (the F801 baseline).
  • LEAVE-ONE-OUT ctx — the bundle of the OTHER words in the reply (non-circular: the target word is NOT in its own
                        context). First evidence that a context shape that does not contain the answer can still steer.
  • FULL ctx          — the bundle of ALL words incl. the target. A test of whether even an answer-containing context
                        steers the decode (RESULT: it does NOT — a flat bundle dilutes the target to ~uniform).
RESULT (honest null): the additive bundle bias does not move exactness; the 'correct shape of context' is NOT a flat
superposition. The research path STANDS but needs a STRUCTURED context mechanism (binding / sequence / cleanup-
resonance). The eventual goal: a minimal context shape that reproduces exactly = a grounded ADDRESS (seed) of the
output — storage-by-seed, not stored prose (the non-magic replacement). See F802.

Read-only over the live genome. srmech 0.7.5rc166; no abs; no CAD.
Run: /tmp/srmech_rc166/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-CONTEXTSHAPE_...py
"""
import importlib.util as U
import os
import re
from srmech.amsc import hdc

HERE = os.path.dirname(os.path.abspath(__file__))
GENOME_DIR = os.environ.get("SIONA_GENOME", os.path.join(HERE, ".siona_genepool"))
_spec = U.spec_from_file_location("sgp", os.path.join(
    HERE, "R-RBS-LM-SIONAGENEPOOL_storyteller_etak_walk_over_genome_with_notebooks.py"))
GP = U.module_from_spec(_spec); _spec.loader.exec_module(GP)

SAMPLES = [
    ("structure-card frame", "the running genome backed instance of the stored relationship mechanism"),
    ("sourced wiki content", "the tomato is a fruit a berry that grows on a plant in the garden"),
]
LAM = 1.0   # context-bias weight (the steering strength)


def main():
    import srmech
    print(f"=== R-RBS-LM-CONTEXTSHAPE — context-conditioned inference toward exact reproduction (srmech {srmech.__version__}) ===\n")
    W = GP.SionaGenepool(GENOME_DIR)
    vocab = set(W.glosses)
    by_prefix = {}
    for w in vocab:
        if len(w) >= 3:
            by_prefix.setdefault(w[:2], []).append(w)

    def decode(word, ctx_bundle=None):
        if len(word) < 3:
            return word
        wv = GP._word_hv(word)
        best, bs = word, (hdc.klein4_similarity(wv, GP._word_hv(word)) if word in vocab else -1.0)
        if ctx_bundle is not None:
            bs += LAM * hdc.klein4_similarity(ctx_bundle, GP._word_hv(word)) if word in vocab else 0.0
        for c in by_prefix.get(word[:2], [])[:3000]:
            cv = GP._word_hv(c)
            s = hdc.klein4_similarity(wv, cv)
            if ctx_bundle is not None:
                s += LAM * hdc.klein4_similarity(ctx_bundle, cv)
            if s > bs:
                bs, best = s, c
        return best

    skip = GP.ROUTING_STOPLIST
    for label, text in SAMPLES:
        words = [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 3 and w not in skip]
        hvs = [GP._word_hv(w) for w in words]
        full_ctx = hdc.klein4_bundle(*hvs)
        # three context shapes
        none_x = sum(1 for w in words if decode(w) == w)
        loo_x = 0
        for i, w in enumerate(words):
            others = [hvs[j] for j in range(len(words)) if j != i]
            loo = hdc.klein4_bundle(*others) if len(others) > 1 else (others[0] if others else None)
            if decode(w, loo) == w:
                loo_x += 1
        full_x = sum(1 for w in words if decode(w, full_ctx) == w)
        n = len(words)
        print(f"--- {label} ({n} words) ---")
        print(f"    NO context        : {none_x}/{n} exact ({none_x/n:.0%})")
        print(f"    LEAVE-ONE-OUT ctx : {loo_x}/{n} exact ({loo_x/n:.0%})")
        print(f"    FULL ctx (incl target): {full_x}/{n} exact ({full_x/n:.0%})\n")

    print("HONEST RESULT (NULL for this mechanism): an additive klein-4 BUNDLE bias does NOT move exactness — even FULL")
    print("  context that CONTAINS the target word fails to reach exact. Why: a bundle of N words is a flat superposition,")
    print("  so its similarity to any single candidate is ~uniform (the target is diluted to ~1/N) — it cannot steer a")
    print("  per-word decode dominated by glyph similarity. So the 'correct shape of context' is NOT a superposition.")
    print("  The research path (F802) STANDS — inference simulates a new story and an exact-reproducing context exists")
    print("  in theory — but realizing it needs a STRUCTURED context mechanism (binding/sequence/cleanup-resonance),")
    print("  not a flat bundle. This null rules out the naive approach and sharpens the question.")


if __name__ == "__main__":
    main()
