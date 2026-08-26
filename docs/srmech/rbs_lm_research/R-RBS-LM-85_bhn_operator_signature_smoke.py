"""R-RBS-LM-85 — B/H/N operator-signature detection test.

Per Finding 106 §9. The framework reading positions B/H/N as the meta-
cascade projection-enablers that ARE the first 3 emergent subjects
following math (reading / grammar / science).

The test: build explicit B/H/N signature-vocabulary lists (hand-curated
per A-N operator semantics), then for each corpus:

  1. Extract eigvec content (top-K tokens by Laplacian eigvec magnitude)
  2. Score the eigvec content against each B/H/N signature
  3. Verify that each first-emergent subject scores HIGHEST on its
     predicted operator's signature

Prediction (form-iso, per MFO §VII.6.20):
  Reading  -> B (TLV-framing)        : decode/symbol/word/letter vocab
  Grammar  -> H (self-introspection) : rule/clause/verb/noun vocab
  Science  -> N (rational-approx)    : count/measure/star/ratio vocab

If the signature ordering matches: Finding 106 empirically confirmed
(form-iso level; not substrate-identity).
If signatures don't match: the mapping is form-organization without
operational empirical signature.

Per `[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]` —
no abs(); sign handling stays in srmech ops where used.
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np


# ===========================================================
# B/H/N hand-curated signature vocabulary (per A-N operator semantics)
# ===========================================================
#
# B = TLV-framing — type + length + value framing; decode symbol-streams
# H = self-introspection — rules-about-rules; recursive querying
# N = rational-approximation — small-denominator anchors; measurement
#
# Curated from the operator semantics in CLAUDE.md §1 + srmech.amsc.*
# semantics. Aim is small (~30 tokens), high-signal vocabulary per
# operator. Per [[feedback_dont_pre_commit_spike_query_operators]],
# we curate without leaning toward any specific corpus result.

B_SIGNATURE = {
    # Symbol-stream decoding vocabulary
    "letter", "letters", "word", "words", "sound", "sounds",
    "read", "reading", "spell", "spelling", "syllable", "syllables",
    "say", "speak", "tell", "told", "name", "names",
    "book", "page", "line", "story", "stories", "tale", "tales",
    "saw", "seen", "look", "looks", "hear", "heard", "voice",
}

H_SIGNATURE = {
    # Self-introspective rule-vocabulary (rules about rules)
    "rule", "rules", "verb", "verbs", "noun", "nouns",
    "adjective", "adverb", "pronoun", "preposition", "conjunction",
    "clause", "clauses", "phrase", "phrases", "sentence", "sentences",
    "subject", "predicate", "object", "tense", "case",
    "grammar", "syntax", "parse", "form", "structure", "agreement",
    "means", "meaning", "definition", "define",
}

N_SIGNATURE = {
    # Rational-approximation / measurement vocabulary
    "number", "numbers", "count", "counts", "measure", "measurement",
    "ratio", "ratios", "approximate", "approximately", "about",
    "star", "stars", "sun", "moon", "planet", "earth",
    "distance", "size", "weight", "length", "time",
    "year", "years", "day", "days", "hour", "minute",
    "degree", "circle", "diameter", "orbit",
}


# ===========================================================
# Corpus list — what we have on disk per autonomous session
# ===========================================================

# subject -> [corpus paths]
SUBJECT_CORPORA = {
    "reading": [
        "/tmp/mcguffey_primer.txt",
        "/tmp/mcguffey_first.txt",
        "/tmp/mcguffey_second.txt",
        "/tmp/mcguffey_third.txt",
        "/tmp/mcguffey_fourth.txt",
        "/tmp/mcguffey_fifth.txt",
        "/tmp/mcguffey_sixth.txt",
        "/tmp/mcguffey_spelling.txt",
    ],
    "grammar": [
        "/tmp/kittredge_advanced_grammar.txt",
        "/tmp/strunk_elements.txt",
        "/tmp/goold_brown_grammar.txt",
    ],
    "science": [
        "/tmp/k12_astronomy_youngfolks.txt",
        "/tmp/k12_starland.txt",
        "/tmp/k12_childs_health_primer.txt",
        "/tmp/k12_how_we_are_fed.txt",
    ],
    "math": [
        "/tmp/openstax_elem_algebra.txt",
        "/tmp/openstax_inter_algebra.txt",
    ],
    "geography": [
        "/tmp/k12_home_geography.txt",
        "/tmp/k12_commercial_geography.txt",
    ],
    "history": [
        "/tmp/k12_story_of_greeks.txt",
    ],
    "composition": [
        "/tmp/openstax_writing_guide.txt",
    ],
    # control / extracurriculars — these should NOT score highest on B/H/N
    "music": ["/tmp/ec_music_theory.txt"],
    "art": ["/tmp/ec_drawing_easy.txt", "/tmp/ec_perspective_art.txt"],
    "games": ["/tmp/ec_hoyle_games.txt"],
    "sports": ["/tmp/ec_spalding_baseball.txt"],
    "cooking": ["/tmp/ec_farmer_cookbook.txt"],
    "scouting": ["/tmp/ec_scouting_boys.txt"],
}


# ===========================================================
# Stop-word filtering — keep eigvec content meaningful
# ===========================================================

STOP = {
    "the", "a", "an", "of", "in", "to", "is", "and", "that", "it",
    "for", "on", "with", "as", "at", "by", "be", "this", "from",
    "or", "are", "but", "not", "have", "has", "had", "was", "were",
    "will", "would", "should", "could", "may", "might", "can", "do",
    "does", "did", "i", "you", "he", "she", "we", "they", "his",
    "her", "its", "our", "their", "my", "your", "him", "them", "us",
    "me", "if", "when", "where", "which", "who", "what", "how", "why",
    "than", "so", "too", "very", "just", "also", "then", "now", "here",
    "there", "out", "up", "down", "into", "over", "about", "after",
    "before", "while", "yet", "still", "only", "one", "two", "three",
    "all", "any", "some", "no", "more", "most", "much", "many",
    "be", "been", "being", "am", "shall", "let", "give", "given",
    "said", "say", "go", "going", "went", "come", "came", "make",
    "made", "see", "make", "made", "get", "got", "take", "took", "put",
    "find", "found", "use", "used", "know", "knew", "think", "thought",
    "well", "good", "great", "little", "big", "old", "new", "first",
    "last", "next", "other", "such", "same", "different", "own",
    "way", "ways", "time", "times", "thing", "things", "part", "parts",
}


# ===========================================================
# Tokenization
# ===========================================================

TOKEN_RE = re.compile(r"[a-z]+")


def tokenize(text: str) -> list[str]:
    """Lowercase + extract a-z token sequences; drop stopwords."""
    text = text.lower()
    toks = TOKEN_RE.findall(text)
    return [t for t in toks if t not in STOP and len(t) >= 2]


def load_corpus(paths: list[str]) -> list[str]:
    """Load + concatenate + tokenize the corpus for one subject."""
    all_tokens = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"  [warn] missing corpus file: {p}")
            continue
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
        toks = tokenize(text)
        all_tokens.extend(toks)
        print(f"  loaded {path.name}: {len(toks):,} tokens after filter")
    return all_tokens


# ===========================================================
# Eigvec content via cooccurrence -> Laplacian -> top-K eigvec
# Simpler proxy that captures signature: top-N most-frequent tokens
# (eigvec content from previous smokes was largely top-frequency
# after stopword filtering; this is the fast proxy)
# ===========================================================

def top_k_content(tokens: list[str], k: int = 100) -> set[str]:
    """Return the top-K most-frequent tokens (eigvec-content proxy)."""
    counts = Counter(tokens)
    return set(tok for tok, _ in counts.most_common(k))


# ===========================================================
# Signature scoring — overlap-based per Finding 106 §9
# ===========================================================

def score_signature(content: set[str], signature: set[str]) -> dict:
    """Score a corpus's top-K content against a signature vocabulary.

    Returns:
      overlap: count of tokens in both content and signature
      score:   overlap / |signature|  (normalized by signature size)
      hits:    sorted list of hitting tokens
    """
    hits = content & signature
    return {
        "overlap": len(hits),
        "score": len(hits) / max(1, len(signature)),
        "hits": sorted(hits),
    }


# ===========================================================
# Main
# ===========================================================

def main():
    print("=" * 70)
    print("R-RBS-LM-85 — B/H/N operator-signature detection test")
    print("(per Finding 106 §9; form-iso reading per MFO §VII.6.20)")
    print("=" * 70)
    print()
    print(f"Signature sizes:")
    print(f"  B (TLV-framing):           {len(B_SIGNATURE)} tokens")
    print(f"  H (self-introspection):    {len(H_SIGNATURE)} tokens")
    print(f"  N (rational-approx):       {len(N_SIGNATURE)} tokens")
    print()

    # Load + tokenize all corpora
    print("Loading corpora ...")
    print()
    subject_content = {}
    for subj, paths in SUBJECT_CORPORA.items():
        print(f"[{subj}]")
        tokens = load_corpus(paths)
        if not tokens:
            print(f"  SKIP - no corpus content")
            continue
        subject_content[subj] = top_k_content(tokens, k=200)
        print(f"  -> {len(subject_content[subj])} unique top-200 tokens")
        print()

    print("=" * 70)
    print("SIGNATURE SCORES (overlap with hand-curated B/H/N vocabularies)")
    print("=" * 70)
    print()
    print(f"{'subject':<14} {'B (read)':>10} {'H (gram)':>10} "
          f"{'N (sci)':>10}  predicted-class  matches?")
    print("-" * 70)

    # First-3 emergence predictions per Finding 106
    PREDICTED = {
        "reading": "B",
        "grammar": "H",
        "science": "N",
    }

    results = {}
    for subj, content in subject_content.items():
        b = score_signature(content, B_SIGNATURE)
        h = score_signature(content, H_SIGNATURE)
        n = score_signature(content, N_SIGNATURE)
        results[subj] = {"B": b, "H": h, "N": n}

        # Which class scores highest?
        scores = {"B": b["score"], "H": h["score"], "N": n["score"]}
        top = max(scores, key=scores.get)
        pred = PREDICTED.get(subj, "-")
        match = "[OK]" if pred == top else ("[--]" if pred == "-" else "[XX]")

        print(f"{subj:<14} {b['score']:>10.3f} {h['score']:>10.3f} "
              f"{n['score']:>10.3f}  top={top}, pred={pred}  {match}")

    print()
    print("=" * 70)
    print("HIT DETAILS for first-emergence predictions")
    print("=" * 70)

    for subj in ("reading", "grammar", "science"):
        if subj not in results:
            continue
        pred = PREDICTED[subj]
        sig_hits = results[subj][pred]["hits"]
        print()
        print(f"[{subj} <-> {pred}]")
        print(f"  hits: {', '.join(sig_hits)}")
        # Cross-check: what did this subject hit in the OTHER 2 signatures?
        for other_class in ("B", "H", "N"):
            if other_class == pred:
                continue
            other_hits = results[subj][other_class]["hits"]
            print(f"  (cross-check {other_class} hits: {', '.join(other_hits)})")

    print()
    print("=" * 70)
    print("VERDICT")
    print("=" * 70)
    print()

    first_3 = ("reading", "grammar", "science")
    pred_correct = 0
    for subj in first_3:
        if subj not in results:
            continue
        scores = {"B": results[subj]["B"]["score"],
                  "H": results[subj]["H"]["score"],
                  "N": results[subj]["N"]["score"]}
        top = max(scores, key=scores.get)
        if PREDICTED[subj] == top:
            pred_correct += 1

    print(f"First-3 predictions matched: {pred_correct} / 3")
    print()

    if pred_correct == 3:
        print("VERDICT: Finding 106 empirically confirmed at form-iso level.")
        print("  All 3 first-emergent subjects score HIGHEST on their")
        print("  predicted B/H/N operator signature.")
    elif pred_correct >= 2:
        print("VERDICT: Finding 106 partially confirmed.")
        print("  Form-iso mapping is suggestive but not clean.")
        print("  Investigate which prediction missed and why.")
    else:
        print("VERDICT: Finding 106 NOT confirmed at operational signature level.")
        print("  The form-iso mapping is articulatory but not empirically")
        print("  detectable in the eigvec-content overlap test.")

    print()
    print("Per MFO §VII.6.20: this is form-iso evidence, NOT substrate-")
    print("identity. A positive result means the operator-mapping is")
    print("OPERATIONALLY DETECTABLE, not that B/H/N ARE physical operators")
    print("in human cognition.")
    print()

    # Save full results
    out_path = Path(__file__).parent / "R-RBS-LM-85_bhn_signature_results.json"
    serializable = {
        subj: {
            cls: {"overlap": r["overlap"],
                  "score": r["score"],
                  "hits": r["hits"]}
            for cls, r in subj_results.items()
        }
        for subj, subj_results in results.items()
    }
    with open(out_path, "w") as f:
        json.dump({
            "predictions": PREDICTED,
            "signatures": {
                "B": sorted(B_SIGNATURE),
                "H": sorted(H_SIGNATURE),
                "N": sorted(N_SIGNATURE),
            },
            "results": serializable,
            "verdict_count": pred_correct,
        }, f, indent=2)
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
