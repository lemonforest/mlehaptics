"""R-RBS-LM-87 — I (cyclic) + J (primes) signature decomposition of math substrate.

Per CLAUDE.md §1 + Finding 99 + Finding 106:
  Math substrate = A + I + J
    A = foundational anchor (content-addressing; no surface vocabulary)
    I = cyclic / modular arithmetic
    J = primes / prime-field operations

Math's "flat" B/H/N/C profile in R-RBS-LM-85/86 was the expected
signature of an irrep that doesn't need projection-enablers. But math
SHOULD have HIGH signatures on I and J — the operators that ARE math.

Prediction (form-iso, per MFO §VII.6.20):
  Math materials peak on I (cyclic) and J (primes) signatures
  Non-math subjects show LOW I and J signatures
  Some non-math subjects may show I (calendar/season vocabulary) but
    very few should show J (factor/prime/multiply vocabulary)

If math peaks on I and J: Finding 99 math-as-A+I+J empirically confirmed
If math doesn't peak: math's irrep status is form-organization, not
  operationally detectable in surface vocabulary
"""

import json
import re
from collections import Counter
from pathlib import Path


# ===========================================================
# I signature — cyclic / modular arithmetic vocabulary
# ===========================================================
#
# I = cyclic-group operations / modular arithmetic
# Educationally appears as:
#   - Calendar / time-cycles (season, month, week, day, year)
#   - Period / repetition (cycle, period, round, repeat)
#   - Rotation / wheel (rotation, revolution, wheel)
#   - Modular arithmetic terms (mod, modular, remainder)

I_SIGNATURE = {
    # Cycle / period vocabulary
    "cycle", "cycles", "period", "periods", "periodic",
    "repeat", "repeats", "repeated", "repeating", "repetition",
    "round", "rounds", "rotation", "rotate", "rotates",
    "revolution", "revolutions", "revolve", "revolves",
    # Modular vocabulary
    "remainder", "remainders", "modular", "modulo", "mod",
    # Time-cycle vocabulary (calendar appears in I-substrate)
    "season", "seasons", "month", "months", "week", "weeks",
    "calendar", "clock", "hour", "wheel", "wheels",
}


# ===========================================================
# J signature — prime / factorisation vocabulary
# ===========================================================
#
# J = prime factorization / prime-field operations
# Educationally appears as:
#   - Factor / multiplication vocabulary
#   - Divisor / divisibility vocabulary
#   - Prime / composite vocabulary
#   - Exponent / power vocabulary

J_SIGNATURE = {
    # Factor / multiply vocabulary
    "factor", "factors", "factoring", "factorization",
    "multiply", "multiplied", "multiple", "multiples", "multiplication",
    "product", "products", "produce", "produces",
    # Divide vocabulary
    "divide", "divided", "divisible", "divisor", "divisors",
    "division", "divisions", "quotient", "quotients",
    # Prime / composite
    "prime", "primes", "composite", "composites",
    # Power / exponent
    "power", "powers", "exponent", "exponents", "exponential",
    "square", "squares", "squared", "cube", "cubed", "cubic",
    "root", "roots",
}


# Reuse B/H/N/C signatures from R-RBS-LM-85/86 for context
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
    print("=" * 84)
    print("R-RBS-LM-87 — I+J signature decomposition of math substrate")
    print("(extends R-RBS-LM-85/86 to math-irrep components A+I+J)")
    print("=" * 84)
    print()
    print(f"Signature sizes:")
    print(f"  I (cyclic / modular): {len(I_SIGNATURE)} tokens")
    print(f"  J (primes / factor):  {len(J_SIGNATURE)} tokens")
    print(f"  (Reference: B={len(B_SIGNATURE)}, H={len(H_SIGNATURE)}, "
          f"N={len(N_SIGNATURE)}, C={len(C_SIGNATURE)})")
    print()

    # Load corpora
    subject_content = {}
    for subj, paths in SUBJECT_CORPORA.items():
        tokens = load_corpus(paths)
        if not tokens:
            continue
        subject_content[subj] = top_k_content(tokens, k=200)

    print("=" * 84)
    print("SIX-OPERATOR SIGNATURE SCORES")
    print("=" * 84)
    print()
    print(f"{'subject':<14} {'B':>7} {'H':>7} {'N':>7} {'C':>7} "
          f"{'I':>7} {'J':>7}  top")
    print("-" * 84)

    results = {}
    for subj, content in subject_content.items():
        b = score_signature(content, B_SIGNATURE)
        h = score_signature(content, H_SIGNATURE)
        n = score_signature(content, N_SIGNATURE)
        c = score_signature(content, C_SIGNATURE)
        i = score_signature(content, I_SIGNATURE)
        j = score_signature(content, J_SIGNATURE)
        results[subj] = {"B": b, "H": h, "N": n, "C": c, "I": i, "J": j}

        scores = {"B": b["score"], "H": h["score"], "N": n["score"],
                  "C": c["score"], "I": i["score"], "J": j["score"]}
        top = max(scores, key=scores.get)

        print(f"{subj:<14} {b['score']:>7.3f} {h['score']:>7.3f} "
              f"{n['score']:>7.3f} {c['score']:>7.3f} "
              f"{i['score']:>7.3f} {j['score']:>7.3f}  {top}")

    print()
    print("=" * 84)
    print("I + J HIT DETAILS (sorted by I+J combined score)")
    print("=" * 84)
    print()

    combined_ij = {s: results[s]["I"]["score"] + results[s]["J"]["score"]
                   for s in results}
    sorted_subjects = sorted(combined_ij.keys(),
                             key=lambda s: -combined_ij[s])

    for subj in sorted_subjects:
        i_hits = results[subj]["I"]["hits"]
        j_hits = results[subj]["J"]["hits"]
        i_score = results[subj]["I"]["score"]
        j_score = results[subj]["J"]["score"]
        combined = i_score + j_score
        print(f"[{subj}]  I={i_score:.3f}  J={j_score:.3f}  "
              f"I+J={combined:.3f}")
        print(f"  I-hits: {', '.join(i_hits) if i_hits else '(none)'}")
        print(f"  J-hits: {', '.join(j_hits) if j_hits else '(none)'}")
        print()

    print("=" * 84)
    print("VERDICT")
    print("=" * 84)
    print()

    # Math vs everyone-else comparison
    math_i = results.get("math", {}).get("I", {}).get("score", 0)
    math_j = results.get("math", {}).get("J", {}).get("score", 0)
    math_ij = math_i + math_j

    nonmath_ij = [
        results[s]["I"]["score"] + results[s]["J"]["score"]
        for s in results if s != "math"
    ]
    if nonmath_ij:
        avg_nonmath_ij = sum(nonmath_ij) / len(nonmath_ij)
        max_nonmath_ij = max(nonmath_ij)
    else:
        avg_nonmath_ij = 0
        max_nonmath_ij = 0

    print(f"Math I+J score:                {math_ij:.3f}")
    print(f"  Math I (cyclic):             {math_i:.3f}")
    print(f"  Math J (primes/factor):      {math_j:.3f}")
    print(f"Non-math avg I+J score:        {avg_nonmath_ij:.3f}")
    print(f"Non-math max I+J score:        {max_nonmath_ij:.3f}")
    print()

    if math_ij > max_nonmath_ij:
        ratio = math_ij / max(0.001, avg_nonmath_ij)
        print(f"VERDICT: Math I+J score ({math_ij:.3f}) EXCEEDS max non-math "
              f"({max_nonmath_ij:.3f}).")
        print(f"  Math/non-math-avg ratio: {ratio:.2f}x")
        print(f"  Math IS empirically the A+I+J irrep — Finding 99/106 "
              f"confirmed.")
    else:
        print(f"VERDICT: Math I+J ({math_ij:.3f}) NOT above all non-math.")
        print(f"  Inspect which non-math subject scored higher.")

    # Which subject has highest I (cyclic)?
    i_top = max(results.keys(), key=lambda s: results[s]["I"]["score"])
    i_top_score = results[i_top]["I"]["score"]
    print()
    print(f"Highest I (cyclic) overall: {i_top} ({i_top_score:.3f})")
    if i_top != "math":
        print(f"  Hits: {', '.join(results[i_top]['I']['hits'])}")

    # Which subject has highest J (primes)?
    j_top = max(results.keys(), key=lambda s: results[s]["J"]["score"])
    j_top_score = results[j_top]["J"]["score"]
    print(f"Highest J (primes) overall: {j_top} ({j_top_score:.3f})")
    print()

    print("Per MFO §VII.6.20: form-iso reading, not substrate-identity.")
    print()

    # Save
    out_path = Path(__file__).parent / "R-RBS-LM-87_ij_decomposition_results.json"
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
                "B": sorted(B_SIGNATURE), "H": sorted(H_SIGNATURE),
                "N": sorted(N_SIGNATURE), "C": sorted(C_SIGNATURE),
                "I": sorted(I_SIGNATURE), "J": sorted(J_SIGNATURE),
            },
            "results": serializable,
            "math_ij": math_ij,
            "math_i": math_i,
            "math_j": math_j,
            "avg_nonmath_ij": avg_nonmath_ij,
            "max_nonmath_ij": max_nonmath_ij,
        }, f, indent=2)
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
