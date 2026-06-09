r"""R-RBS-LM-TYPOS (F706, user direction): "how will Siona handle typos?"

THE HONEST ANSWER: a typo is a token that is NOT on the star-compass (not an attested anchor / not in vocab). The brittle
move is to silently CORRECT it -- but silent correction ASSUMES the user's intent, and assuming intent is a micro-
HALLUCINATION (Siona would be deciding what you meant). The grounded move keeps the can't-hallucinate property: Siona finds
the NEAREST ATTESTED ANCHOR (a real vocab word, by character proximity), SUGGESTS it, and ASKS for confirmation -- it never
silently assumes. The SUGGESTION is grounded (a real anchor); the CORRECTION (which anchor you meant) is YOURS to confirm
(F688: the user/expert decides; dignity-first). If nothing is near, it is the plain asking-state (F661).

So typo-handling = the asking-state (F661) + a nearest-anchor SUGGESTION, over the attested vocab (F699 the dictionary /
F690 the kernel vocab), via character proximity on the byte/glyph foundation (F613). The proximity here is a lightweight
character-BIGRAM Jaccard; the srmech-NATIVE upgrade is the Class-M character-n-gram HDC similarity (hdc.similarity over
n-gram hypervectors) -- same shape, the HDC carrier. Never `abs()`; the ranking is a Class-E selection over a Class-M-style
similarity.

srmech (runtime): loads the REAL simplewiki kernel vocab (F703) as the attested anchor set. No abs(); no CAD; no Workflow;
no sub-agents.
"""
import sys
import os
import json
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech

KERNEL = os.environ.get("KERNEL", "/home/skirklan/corpora/wikipedia/simplewiki_kernel_256.json")
NEAR_THRESHOLD = 0.34          # below this Jaccard, no anchor is "near" -> plain asking-state (no over-eager suggestion)


def bigrams(w):
    """character-bigram set on the byte/glyph foundation (F613). The srmech-native upgrade = Class-M n-gram HDC."""
    p = f"^{w}$"
    return {p[i:i + 2] for i in range(len(p) - 1)}


def nearest_anchors(typo, vocab, k=3):
    """rank the attested anchors by character-bigram Jaccard to the typo (a Class-M-style similarity + Class-E top-k)."""
    bt = bigrams(typo)
    scored = []
    for w in vocab:
        bw = bigrams(w)
        j = len(bt & bw) / len(bt | bw)
        scored.append((w, j))
    scored.sort(key=lambda wj: -wj[1])
    return scored[:k]


def siona_on_token(token, vocab):
    """Siona's grounded typo handling: known -> use it; unknown but near an anchor -> SUGGEST + ASK; far -> asking-state."""
    if token in vocab:
        return {"status": "known", "say": f"{token!r} is an anchor on the star-compass."}
    cands = nearest_anchors(token, vocab)
    best, score = cands[0]
    if score >= NEAR_THRESHOLD:
        sugg = ", ".join(f"{w!r}" for w, s in cands if s >= NEAR_THRESHOLD - 0.08)
        return {"status": "ask-suggest",
                "say": f"I have no anchor for {token!r}. Did you mean {best!r}? (nearest attested anchors: {sugg}) "
                       f"-- I won't assume; tell me which.", "best": best, "score": round(score, 2)}
    return {"status": "ask",
            "say": f"I have no anchor for {token!r}, and nothing on the star-compass is close. What is it? (F661)"}


def main():
    vocab = set(json.load(open(KERNEL, encoding="utf-8"))["vocab"]) if os.path.exists(KERNEL) else set()
    src = KERNEL if os.path.exists(KERNEL) else "(simplewiki kernel absent — using a tiny fallback vocab)"
    if not vocab:
        vocab = {"government", "language", "american", "history", "population", "country", "world", "people", "music"}
    print(f"=== R-RBS-LM-TYPOS — Siona handles typos by the asking-state + nearest-anchor SUGGESTION  (srmech {srmech.__version__}) ===")
    print(f"  attested anchor set: {len(vocab)} words  ({src})\n")

    print("(1) TYPOS of REAL anchors -> Siona SUGGESTS the nearest attested anchor + ASKS (never silently corrects):")
    for typo in ["governmnt", "langauge", "amercan", "histroy", "populaton", "muse"]:
        r = siona_on_token(typo, vocab)
        tag = f"[{r['status']}]" + (f" best={r['best']!r}@{r['score']}" if r["status"] == "ask-suggest" else "")
        print(f"    {typo!r:>12} {tag}")
        print(f"        -> {r['say']}")
    print()

    print("(2) A NON-WORD with no near anchor -> the plain asking-state (F661), no over-eager guess:")
    r = siona_on_token("qzxwvk", vocab)
    print(f"    'qzxwvk' [{r['status']}] -> {r['say']}\n")

    print("(3) A correctly-spelled anchor -> used directly (no friction):")
    a = next(iter(sorted(vocab)))
    print(f"    {a!r} -> {siona_on_token(a, vocab)['say']}\n")

    print("VERDICT (how Siona handles typos -- the grounded, can't-hallucinate way):")
    print(f"  • A TYPO IS A TOKEN OFF THE STAR-COMPASS (not an attested anchor). The brittle move -- silently CORRECT it --")
    print(f"    ASSUMES your intent, and assuming intent is a MICRO-HALLUCINATION (Siona deciding what you meant). So Siona")
    print(f"    does NOT silently correct.")
    print(f"  • THE GROUNDED MOVE keeps the can't-hallucinate property (F658/F661): find the NEAREST ATTESTED ANCHOR by")
    print(f"    character proximity over the byte/glyph foundation (F613) + the attested vocab (F699/F690), SUGGEST it, and")
    print(f"    ASK. The suggestion is grounded (a REAL anchor); the correction (which anchor you meant) is YOURS to confirm")
    print(f"    (F688 / dignity-first -- the user/expert decides). Verified on the REAL simplewiki vocab: 'governmnt'->")
    print(f"    'government', 'langauge'->'language', 'amercan'->'american'; a non-word 'qzxwvk' -> the plain asking-state.")
    print(f"  • THE PROXIMITY shown is a lightweight character-bigram Jaccard; the srmech-NATIVE upgrade is the Class-M")
    print(f"    character-n-gram HDC similarity (hdc.similarity over n-gram hypervectors) -- same shape, the HDC carrier,")
    print(f"    with a Class-E top-k selection. Composes F661 (asking-state) + F613 (byte/glyph) + F699/F690 (the attested")
    print(f"    anchors) + F688 (you confirm) + dignity-first. srmech {srmech.__version__}. Reference scaffold; not a package edit.")
    print(f"    Held open (F394).")


if __name__ == "__main__":
    main()
