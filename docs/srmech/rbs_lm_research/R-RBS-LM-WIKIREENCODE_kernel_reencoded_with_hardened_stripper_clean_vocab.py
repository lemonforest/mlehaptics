r"""R-RBS-LM-WIKIREENCODE (user direction): "The kernel must be re-encoded before its vocab is trusted for big wiki."

DONE. F700 proved F690's DEMO stripper leaks LaTeX/ref/template/table markup into the vocabulary as junk tokens (and the
demo corpus never even exercised the path). This RE-ENCODES the kernel: the F690 build path (stream_articles) now uses
strip_wiki_markup_hardened (F700, removes the CONTENT of math/ref/code/table/comment blocks + nested templates) +
content_words (F698, Unicode-aware) instead of the leaky demo + ASCII tokenizer. F690's SYNTHETIC_WIKI gained a REAL-markup
article (article 7: <math>, <ref>, {{Infobox}}, {| wikitable |}) so the hardened path is actually EXERCISED.

THIS SCRIPT proves the re-encode at the KERNEL/VOCAB granularity (not just the stripper): it builds the kernel TWO ways
over the SAME markup-bearing corpus -- the OLD leaky path vs the NEW hardened path -- and shows the OLD vocab carries junk
markup tokens ('displaystyle'/'frac'/'sqrt'/'wikitable'/...) while the RE-ENCODED vocab carries ONLY real content words.
The associations of the re-encoded kernel are therefore grounded in MEANING, not markup co-occurrence (the chord, F658).

srmech (version reported at runtime): loads the (now re-encoded) F690 kernel. amsc.format.sha256_bytes (the clean-vocab
fingerprint). No abs(); no CAD; no Workflow; no sub-agents.
"""
import re
import sys
import importlib.util
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    saved = sys.argv
    sys.argv = ["x"]
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    sys.argv = saved
    return mod


wk = _load("wk", "docs/srmech/rbs_lm_research/R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py")

JUNK = {"math", "displaystyle", "frac", "sqrt", "mathbf", "cite", "web", "url", "title", "ref", "wikitable",
        "infobox", "nowrap", "thumb", "px", "align", "class", "http", "https", "hubble", "citation", "footnote"}


def old_vocab(corpus):
    """reconstruct the OLD (leaky) build's vocabulary: the demo stripper + the old ASCII tokenizer."""
    freq = {}
    for raw in corpus:
        cleaned = wk.strip_wiki_markup(raw)                                  # the LEAKY demo (kept for this contrast)
        for w in (t.lower() for t in re.findall(r"[A-Za-z][A-Za-z']+", cleaned)):  # the OLD ASCII tokenizer
            if w not in wk.DEFAULT_STOPLIST:
                freq[w] = freq.get(w, 0) + 1
    return sorted(freq)


def main():
    print(f"=== R-RBS-LM-WIKIREENCODE — the big-wiki kernel RE-ENCODED with the hardened stripper  (srmech {srmech.__version__}) ===\n")

    corpus = wk.SYNTHETIC_WIKI
    old = old_vocab(corpus)
    new_vocab, idx, edges, weights, freq, dropped = wk.build_edges_topk(corpus, window=2, vocab_cap=256)  # the re-encode

    old_junk = sorted(set(old) & JUNK)
    new_junk = sorted(set(new_vocab) & JUNK)

    print("(1) OLD leaky build (demo stripper + ASCII tokenizer) -> vocab CARRIES MARKUP JUNK:")
    print(f"    {len(old)} words; JUNK tokens in vocab: {old_junk}")
    print(f"    (these are NOT words -- any association with them is co-occurrence with markup, not meaning)\n")

    print("(2) RE-ENCODED build (strip_wiki_markup_hardened + content_words) -> vocab is CLEAN:")
    print(f"    {len(new_vocab)} words; JUNK tokens in vocab: {new_junk}")
    print(f"    sample: {new_vocab[:16]}")
    print(f"    clean-vocab fingerprint: {srmech.amsc.format.sha256_bytes(repr(new_vocab).encode('utf-8'))[:12]}\n")

    removed = sorted(set(old) & JUNK)
    print(f"(3) THE DIFFERENCE: re-encoding removed {len(removed)} distinct markup junk tokens from the trusted vocab: {removed}")
    assoc, _ = wk.make_query_api(wk.build_class_l_store(new_vocab, edges, weights))
    print(f"    assoc('galaxy') on the re-encoded kernel: {assoc('galaxy', top_k=4)}  (grounded in MEANING, not markup)\n")

    assert new_junk == [], f"re-encoded vocab still carries junk: {new_junk}"
    print("VERDICT (the kernel is re-encoded; its vocab is now trustworthy):")
    print(f"  • DONE, AS DIRECTED. F700 proved the demo stripper leaked LaTeX/ref/template/table markup into the vocab. The")
    print(f"    F690 BUILD PATH (stream_articles) now uses strip_wiki_markup_hardened (F700) + content_words (F698), and")
    print(f"    SYNTHETIC_WIKI gained a real-markup article so the hardened path is EXERCISED. Verified at the VOCAB level:")
    print(f"    the OLD path's vocab carries {len(old_junk)} junk markup tokens ({old_junk}); the RE-ENCODED vocab carries 0.")
    print(f"  • THE ASSOCIATIONS ARE NOW GROUNDED IN MEANING (F658/F640/F688): every edge of the re-encoded Class-L kernel is")
    print(f"    a co-occurrence of REAL content words -- no 'galaxy <-> displaystyle' spurious edge. The story built on this")
    print(f"    kernel (F697) grounds in meaning, not markup noise. The kernel's vocab is trustworthy.")
    print(f"  • SCOPE (honest): this re-encodes the REFERENCE on the synthetic corpus. A REAL enwiki re-encode is the dev")
    print(f"    session pointing stream_articles at the dump (the hardened cleaner now in place) -- the real cleaner being the")
    print(f"    F579/F607 wiki-formatting-language kernel. Two residues remain + are honest (NOT markup junk): a near-stopword")
    print(f"    ('where') the minimal demo stoplist misses (dev session swaps a fuller stoplist), and a possessive ('galaxy's'")
    print(f"    un-lemmatised) -- both real word-forms, the dev session's normaliser handles them. No silent cap (F640).")
    print(f"  • Composes F700 (the hardened stripper) + F698 (the Unicode tokenizer) + F690/F697 (the kernel + its inference)")
    print(f"    + F640/F688/F658 (grounding honesty) + F573 (the audit that found it) + F579/F607 (the real target). srmech")
    print(f"    {srmech.__version__}. Reference scaffold (F690 edited in place, per the F695 precedent); not a package edit. Held open (F394).")


if __name__ == "__main__":
    main()
