"""R-RBS-LM-88 — D + F cascade-detection signature attempt.

Per CLAUDE.md §1 + Finding 99, the 7-class cascade-detection heptad
(D, E, F, G, K, L, M) operates STRUCTURALLY on cooccurrence patterns
rather than delivering substrate-content vocabulary.

This test probes whether ANY of the detection ops have at least
PARTIAL surface vocabulary signatures, focusing on D and F which
have the most plausible direct vocabulary candidates:

  D = pattern-match / sequence detection
      Plausible vocabulary: pattern, repeat, sequence, follow, again
  F = render / output / serialization
      Plausible vocabulary: draw, paint, picture, image, depict

Prediction (form-iso, per MFO §VII.6.20):
  IF detection ops have surface signatures, art/composition material
  should peak on F (output vocabulary)
  IF they don't have signatures, the test shows generic distribution
  (no clean operator-subject mapping)

A NULL finding here CONFIRMS that cascade-detection is structural
rather than vocabularial — which is a valuable empirical closure.

Per `[[feedback_dont_pre_commit_spike_query_operators]]` —
null findings count.
"""

import json
import re
from collections import Counter
from pathlib import Path


# ===========================================================
# D signature — pattern-match / sequence detection vocabulary
# ===========================================================

D_SIGNATURE = {
    "pattern", "patterns",
    "repeat", "repeats", "repeated", "repeating", "repetition",
    "sequence", "sequences", "sequential",
    "follow", "follows", "followed", "following",
    "again", "similar", "similarly", "same",
    "match", "matches", "matching", "matched",
    "compare", "comparison", "comparisons", "compared",
    "order", "ordered", "ordering",
    "consecutive", "successive",
}


# ===========================================================
# F signature — render / output / serialization vocabulary
# ===========================================================

F_SIGNATURE = {
    "draw", "draws", "drawing", "drawings", "drawn",
    "paint", "paints", "painting", "paintings", "painted",
    "picture", "pictures",
    "image", "images",
    "depict", "depicts", "depicted", "depicting",
    "illustrate", "illustrates", "illustrated", "illustration",
    "portray", "portrays", "portrait", "portraits",
    "render", "renders", "rendering",
    "display", "displays", "displayed",
    "print", "prints", "printed",
    "describe", "describes", "describing", "description",
    "represent", "represents", "representation",
    "sketch", "sketches", "sketched",
}


# Reuse prior signatures for context
B_SIGNATURE = {
    "letter", "letters", "word", "words", "sound", "sounds",
    "read", "reading", "spell", "spelling", "syllable", "syllables",
    "say", "speak", "tell", "told", "name", "names",
    "book", "page", "line", "story", "stories", "tale", "tales",
    "saw", "seen", "look", "looks", "hear", "heard", "voice",
}

H_SIGNATURE = {
    "rule", "rules", "verb", "verbs", "noun", "nouns",
    "adjective", "adverb", "pronoun", "preposition", "conjunction",
    "clause", "clauses", "phrase", "phrases", "sentence", "sentences",
    "subject", "predicate", "object", "tense", "case",
    "grammar", "syntax", "parse", "form", "structure", "agreement",
    "means", "meaning", "definition", "define",
}

N_SIGNATURE = {
    "number", "numbers", "count", "counts", "measure", "measurement",
    "ratio", "ratios", "approximate", "approximately", "about",
    "star", "stars", "sun", "moon", "planet", "earth",
    "distance", "size", "weight", "length", "time",
    "year", "years", "day", "days", "hour", "minute",
    "degree", "circle", "diameter", "orbit",
}

C_SIGNATURE = {
    "north", "south", "east", "west",
    "northern", "southern", "eastern", "western",
    "left", "right", "above", "below",
    "over", "under", "inside", "outside",
    "forward", "backward", "around", "across",
    "through", "between", "beyond", "near",
    "cross", "turn", "rise", "fall",
    "rises", "falls", "crosses", "turns",
}

I_SIGNATURE = {
    "cycle", "cycles", "period", "periods", "periodic",
    "repeat", "repeats", "repeated", "repeating", "repetition",
    "round", "rounds", "rotation", "rotate", "rotates",
    "revolution", "revolutions", "revolve", "revolves",
    "remainder", "remainders", "modular", "modulo", "mod",
    "season", "seasons", "month", "months", "week", "weeks",
    "calendar", "clock", "hour", "wheel", "wheels",
}

J_SIGNATURE = {
    "factor", "factors", "factoring", "factorization",
    "multiply", "multiplied", "multiple", "multiples", "multiplication",
    "product", "products", "produce", "produces",
    "divide", "divided", "divisible", "divisor", "divisors",
    "division", "divisions", "quotient", "quotients",
    "prime", "primes", "composite", "composites",
    "power", "powers", "exponent", "exponents", "exponential",
    "square", "squares", "squared", "cube", "cubed", "cubic",
    "root", "roots",
}


# NOTE: D and I both include "repeat" / "round" — that's OK, the test
# is measuring shared structural primitives. The overlap is a feature
# not a bug; D-as-sequence-detector and I-as-cyclic both involve
# repetition, just in different operational ways.


SUBJECT_CORPORA = {
    "reading": [
        "/tmp/mcguffey_primer.txt", "/tmp/mcguffey_first.txt",
        "/tmp/mcguffey_second.txt", "/tmp/mcguffey_third.txt",
        "/tmp/mcguffey_fourth.txt", "/tmp/mcguffey_fifth.txt",
        "/tmp/mcguffey_sixth.txt", "/tmp/mcguffey_spelling.txt",
    ],
    "grammar": [
        "/tmp/kittredge_advanced_grammar.txt",
        "/tmp/strunk_elements.txt",
        "/tmp/goold_brown_grammar.txt",
    ],
    "science": [
        "/tmp/k12_astronomy_youngfolks.txt", "/tmp/k12_starland.txt",
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
    "history": ["/tmp/k12_story_of_greeks.txt"],
    "composition": ["/tmp/openstax_writing_guide.txt"],
    "music": ["/tmp/ec_music_theory.txt"],
    "art": ["/tmp/ec_drawing_easy.txt", "/tmp/ec_perspective_art.txt"],
    "games": ["/tmp/ec_hoyle_games.txt"],
    "sports": ["/tmp/ec_spalding_baseball.txt"],
    "cooking": ["/tmp/ec_farmer_cookbook.txt"],
    "scouting": ["/tmp/ec_scouting_boys.txt"],
}

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

TOKEN_RE = re.compile(r"[a-z]+")


def tokenize(text):
    text = text.lower()
    toks = TOKEN_RE.findall(text)
    return [t for t in toks if t not in STOP and len(t) >= 2]


def load_corpus(paths):
    all_tokens = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            continue
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
        all_tokens.extend(tokenize(text))
    return all_tokens


def top_k_content(tokens, k=200):
    counts = Counter(tokens)
    return set(tok for tok, _ in counts.most_common(k))


def score_signature(content, signature):
    hits = content & signature
    return {
        "overlap": len(hits),
        "score": len(hits) / max(1, len(signature)),
        "hits": sorted(hits),
    }


def main():
    print("=" * 90)
    print("R-RBS-LM-88 — D + F cascade-detection signature attempt")
    print("(extends 85/86/87 to cascade-detection heptad sample)")
    print("=" * 90)
    print()

    sig_sets = [
        ("B", B_SIGNATURE), ("H", H_SIGNATURE), ("N", N_SIGNATURE),
        ("C", C_SIGNATURE), ("I", I_SIGNATURE), ("J", J_SIGNATURE),
        ("D", D_SIGNATURE), ("F", F_SIGNATURE),
    ]
    print(f"Signature sizes: " + ", ".join(
        f"{name}={len(sig)}" for name, sig in sig_sets))
    print()

    subject_content = {}
    for subj, paths in SUBJECT_CORPORA.items():
        tokens = load_corpus(paths)
        if not tokens:
            continue
        subject_content[subj] = top_k_content(tokens, k=200)

    print("=" * 90)
    print("EIGHT-OPERATOR SIGNATURE SCORES")
    print("=" * 90)
    print()
    header = f"{'subject':<14}"
    for name, _ in sig_sets:
        header += f" {name:>6}"
    header += "   top"
    print(header)
    print("-" * 90)

    results = {}
    for subj, content in subject_content.items():
        row = {}
        scores = {}
        for name, sig in sig_sets:
            r = score_signature(content, sig)
            row[name] = r
            scores[name] = r["score"]
        results[subj] = row

        top = max(scores, key=scores.get)
        cells = "".join(f" {row[n]['score']:>6.3f}" for n, _ in sig_sets)
        print(f"{subj:<14}{cells}   {top}")

    print()
    print("=" * 90)
    print("D AND F SIGNATURE DETAILS")
    print("=" * 90)
    print()

    for op in ("D", "F"):
        print(f"--- {op} signature ---")
        sorted_subj = sorted(results.keys(),
                             key=lambda s: -results[s][op]["score"])
        for subj in sorted_subj:
            r = results[subj][op]
            if r["overlap"] > 0:
                print(f"  {subj:<14}  score={r['score']:.3f}  hits: "
                      f"{', '.join(r['hits'])}")
        print()

    print("=" * 90)
    print("VERDICT")
    print("=" * 90)
    print()

    # Find which subject tops D
    d_top = max(results.keys(), key=lambda s: results[s]["D"]["score"])
    d_top_score = results[d_top]["D"]["score"]
    # Find which subject tops F
    f_top = max(results.keys(), key=lambda s: results[s]["F"]["score"])
    f_top_score = results[f_top]["F"]["score"]

    print(f"D-signature top: {d_top} ({d_top_score:.3f})")
    print(f"F-signature top: {f_top} ({f_top_score:.3f})")

    # Predictions:
    # - F should peak on art / composition (output / render vocabulary)
    # - D's prediction is ambiguous; might peak on grammar/math (sequence)
    print()
    print("Pre-test predictions:")
    print("  F: art and/or composition (output/render vocabulary)")
    print("  D: ambiguous; possibly math/grammar (sequence/pattern)")
    print()

    f_clean = f_top in ("art", "composition")
    print(f"F clean match (art/composition): "
          f"{'YES' if f_clean else f'NO (was {f_top})'}")
    print(f"F score signal strength: "
          f"{'STRONG' if f_top_score >= 0.20 else 'WEAK' if f_top_score >= 0.10 else 'NULL'}")

    print()

    # Verdict
    if f_clean and f_top_score >= 0.20:
        print("VERDICT: F cascade-detection HAS surface signature.")
        print("  Render-operator detectable in output-producing materials.")
        print("  7 of 14 operators now attested.")
    elif f_top_score >= 0.10:
        print("VERDICT: F shows WEAK surface signature.")
        print("  Some render-vocabulary present but not a clean operator-")
        print("  subject mapping.")
    else:
        print("VERDICT: F has NULL surface signature.")
        print("  Confirms cascade-detection ops are structural, not")
        print("  vocabularial. Their attestation needs cooccurrence-")
        print("  pattern signatures rather than token-overlap signatures.")

    print()
    print("Per MFO §VII.6.20: form-iso reading, not substrate-identity.")
    print()

    out_path = Path(__file__).parent / "R-RBS-LM-88_df_detection_results.json"
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
            "signatures": {
                name: sorted(sig) for name, sig in sig_sets
            },
            "results": serializable,
            "d_top": d_top,
            "f_top": f_top,
            "f_clean_match": f_clean,
        }, f, indent=2)
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
