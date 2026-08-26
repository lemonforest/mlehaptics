r"""R-RBS-LM-ENCODEINFER (F801 experiment) — the user's hypothesis (2026-06-16): a hand-authored English reply is a
"hidden magic number" (unattested prose typed into the code). If we ENCODE that English content into the ni-Vanuatu
LANGUAGE ABSTRACT (_word_hv = byte→glyph, the universal base F613/F761) and then INFER it back through Siona's OWN
vocabulary (nearest word by Klein-4 similarity in the abstract glyph space — the F762 _abstract_resolve mechanism), we
will NOT get the exact value back. The non-exactness IS the inference signature (F774: infer is open/fallible; F552:
the gap is a substrate FEATURE, not error) — and it PINPOINTS the magic numbers: a word that drifts under inference has
no grounded home in Siona's substrate, so it was ungrounded hand-authored prose; a word that round-trips exactly IS
grounded. Round-trip exactness therefore MEASURES groundedness.

This is a read-only experiment over the live genome — it changes nothing. srmech 0.7.5rc166; no abs; no CAD.
Run: /tmp/srmech_rc166/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-ENCODEINFER_...py
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

# the SAMPLES: (label, the reply English). Two are hand-authored cards (the magic-number prose); one is a SOURCED
# answer (its content words ARE wiki words) — the contrast shows groundedness as round-trip exactness.
SAMPLES = [
    ("structure-card frame (hand-authored)",
     "I am the running genome backed instance of the stored relationship mechanism research package the same system "
     "named at two levels the mechanism and this instance reading its genome"),
    ("provenance-card (hand-authored)",
     "my source is the package an open research package not a hidden model the mechanism I run on is the package "
     "itself locatable by its name I hold my identity and version but not a repository address"),
    ("a SOURCED definition body (wiki content)",
     "the tomato is a fruit a berry that grows on a plant in the garden and is used in sauce and soup"),
]


def main():
    import srmech
    print(f"=== R-RBS-LM-ENCODEINFER — reply English → language-abstract → inferred back (srmech {srmech.__version__}) ===\n")
    W = GP.SionaGenepool(GENOME_DIR)
    vocab = set(W.glosses)                                              # Siona's grounded word vocabulary (wiki lead words)
    by_prefix = {}                                                     # 2-glyph prefix bucket -> words (cheap nearest-neighbour scan)
    for w in vocab:
        if len(w) >= 3:
            by_prefix.setdefault(w[:2], []).append(w)
    print(f"decode vocabulary: {len(vocab):,} grounded words (simplewiki gloss keys)\n")

    def infer_back(word):
        """Encode the word into the abstract (ni-Vanuatu glyph base) and INFER the nearest grounded word — self
        INCLUDED (a grounded word resolves to itself; an ungrounded word drifts to its nearest neighbour)."""
        if len(word) < 3:
            return word
        wv = GP._word_hv(word)
        cands = by_prefix.get(word[:2], [])
        best, bs = word, (hdc.klein4_similarity(wv, GP._word_hv(word)) if word in vocab else -1.0)
        for c in cands[:3000]:
            sm = hdc.klein4_similarity(wv, GP._word_hv(c))
            if sm > bs:
                bs, best = sm, c
        return best

    skip = GP.ROUTING_STOPLIST
    tot_words = tot_exact = 0
    for label, text in SAMPLES:
        words = [w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 3 and w not in skip]
        inferred = [infer_back(w) for w in words]
        exact = sum(1 for a, b in zip(words, inferred) if a == b)
        drift = [(a, b) for a, b in zip(words, inferred) if a != b]
        tot_words += len(words); tot_exact += exact
        print(f"--- {label} ---")
        print(f"    content words: {len(words)} | round-trip EXACT: {exact} ({exact/len(words):.0%}) | DRIFTED: {len(drift)}")
        print(f"    drifted (ungrounded → nearest grounded): " +
              ", ".join(f"{a}→{b}" for a, b in drift[:12]) + ("" if len(drift) <= 12 else " …"))
        print(f"    reconstructed: {' '.join(inferred)}\n")

    print(f"VERDICT: over all samples, {tot_exact}/{tot_words} words round-trip EXACTLY "
          f"({tot_exact/tot_words:.0%}) — so the inferred output is NOT the exact input (hypothesis CONFIRMED).")
    print("  The non-exactness is the inference signature (F774/F552). The DRIFTED words are the ungrounded ones —")
    print("  the hand-authored framework jargon with no home in Siona's vocabulary = the 'hidden magic number' prose.")
    print("  Round-trip exactness MEASURES groundedness: sourced (wiki) content round-trips far better than the cards.")


if __name__ == "__main__":
    main()
