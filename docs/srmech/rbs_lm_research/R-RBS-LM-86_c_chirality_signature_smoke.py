"""R-RBS-LM-86 — C (chirality) signature test for places-and-things partition.

Per CLAUDE.md §1, the 14-class A-N partition has:
  1 — foundational anchor: A
  3 — substrate-projection triad: I (cyclic), C (chirality), J (primes)
  7 — cascade-detection heptad: D, E, F, G, K, L, M
  3 — meta-cascade triad: B, H, N

Per Finding 99 + Finding 106:
  Math substrate          = A + I + J  (foundational anchor + 2 of substrate-projection)
  Meta-cascade projection = B + H + N  (3 projection-enablers; Finding 106 confirmed)
  Substrate-projection    = C          (1 chirality / direction class)
  Cascade-detection       = D-M        (7 ops)

R-RBS-LM-85 confirmed B/H/N at form-iso level. R-RBS-LM-86 extends to C.

Prediction (form-iso, per MFO §VII.6.20):
  Places-and-things subjects (geography, sports, scouting, cooking,
  history) should carry C-direction vocabulary (north/south/east/west/
  left/right/forward/back/over/under/across/...)

If C lights up places-and-things subjects more than math/communication
subjects: substrate-projection axis empirically attested.
If C doesn't differentiate: the C ↔ places-and-things mapping is
form-organization without operational signature.

Per `[[feedback_dont_pre_commit_spike_query_operators]]` — curate
vocabulary from operator semantics, not corpus-leaning.
"""

import json
import re
from collections import Counter
from pathlib import Path


# ===========================================================
# C signature — chirality / cascade-orientation vocabulary
# ===========================================================
#
# C = cascade-orientation / chirality / direction / "which-way"
#
# In srmech.amsc, C provides sign-application / direction handling.
# Educationally, the C primitive shows up as:
#   - Cardinal directions (north/south/east/west)
#   - Relative directions (left/right/up/down/over/under)
#   - Path words (forward/back/across/through/around)
#   - Place-orientation words (above/below/inside/outside/between)
#   - Motion words (go/come/move/travel/cross/turn)

C_SIGNATURE = {
    # Cardinal directions
    "north", "south", "east", "west",
    "northern", "southern", "eastern", "western",
    # Relative directions
    "left", "right", "above", "below",
    "over", "under", "inside", "outside",
    # Path words
    "forward", "backward", "around", "across",
    "through", "between", "beyond", "near",
    # Motion / cross
    "cross", "turn", "rise", "fall",
    "rises", "falls", "crosses", "turns",
}


# ===========================================================
# Re-import B/H/N signatures from R-RBS-LM-85 for full-table render
# ===========================================================

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
    "music": ["/tmp/ec_music_theory.txt"],
    "art": ["/tmp/ec_drawing_easy.txt", "/tmp/ec_perspective_art.txt"],
    "games": ["/tmp/ec_hoyle_games.txt"],
    "sports": ["/tmp/ec_spalding_baseball.txt"],
    "cooking": ["/tmp/ec_farmer_cookbook.txt"],
    "scouting": ["/tmp/ec_scouting_boys.txt"],
}


# Stop-word set (same as R-RBS-LM-85)
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


def tokenize(text: str) -> list[str]:
    text = text.lower()
    toks = TOKEN_RE.findall(text)
    return [t for t in toks if t not in STOP and len(t) >= 2]


def load_corpus(paths: list[str]) -> list[str]:
    all_tokens = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            continue
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
        toks = tokenize(text)
        all_tokens.extend(toks)
    return all_tokens


def top_k_content(tokens: list[str], k: int = 200) -> set[str]:
    counts = Counter(tokens)
    return set(tok for tok, _ in counts.most_common(k))


def score_signature(content: set[str], signature: set[str]) -> dict:
    hits = content & signature
    return {
        "overlap": len(hits),
        "score": len(hits) / max(1, len(signature)),
        "hits": sorted(hits),
    }


def main():
    print("=" * 80)
    print("R-RBS-LM-86 — C (chirality) signature test for places-and-things")
    print("(extends R-RBS-LM-85 / Finding 107 to substrate-projection axis)")
    print("=" * 80)
    print()
    print(f"Signature sizes:")
    print(f"  B (TLV-framing):           {len(B_SIGNATURE)} tokens")
    print(f"  H (self-introspection):    {len(H_SIGNATURE)} tokens")
    print(f"  N (rational-approx):       {len(N_SIGNATURE)} tokens")
    print(f"  C (chirality / direction): {len(C_SIGNATURE)} tokens")
    print()

    # Load corpora
    print("Loading corpora (silent) ...")
    subject_content = {}
    for subj, paths in SUBJECT_CORPORA.items():
        tokens = load_corpus(paths)
        if not tokens:
            continue
        subject_content[subj] = top_k_content(tokens, k=200)

    # Predicted partitions per Finding 99 + Finding 106
    # First-3 (meta-cascade): reading -> B, grammar -> H, science -> N
    # Places-and-things (substrate-projection): geography expected to top C
    PREDICTED = {
        "reading": "B",
        "grammar": "H",
        "science": "N",
        "geography": "C",  # NEW prediction
    }

    print()
    print("=" * 80)
    print("FOUR-OPERATOR SIGNATURE SCORES")
    print("=" * 80)
    print()
    print(f"{'subject':<14} {'B':>8} {'H':>8} {'N':>8} {'C':>8}  "
          f"top  pred  match")
    print("-" * 80)

    results = {}
    for subj, content in subject_content.items():
        b = score_signature(content, B_SIGNATURE)
        h = score_signature(content, H_SIGNATURE)
        n = score_signature(content, N_SIGNATURE)
        c = score_signature(content, C_SIGNATURE)
        results[subj] = {"B": b, "H": h, "N": n, "C": c}

        scores = {"B": b["score"], "H": h["score"],
                  "N": n["score"], "C": c["score"]}
        top = max(scores, key=scores.get)
        pred = PREDICTED.get(subj, "-")
        if pred == "-":
            match = "[--]"
        elif pred == top:
            match = "[OK]"
        else:
            match = "[XX]"

        print(f"{subj:<14} {b['score']:>8.3f} {h['score']:>8.3f} "
              f"{n['score']:>8.3f} {c['score']:>8.3f}  "
              f"{top}  {pred}   {match}")

    print()
    print("=" * 80)
    print("C-SIGNATURE HIT DETAILS")
    print("=" * 80)
    print()
    print(f"{'subject':<14}  hits")
    print("-" * 80)
    # Sort subjects by C-score descending
    sorted_subjects = sorted(
        results.keys(),
        key=lambda s: results[s]["C"]["score"],
        reverse=True,
    )
    for subj in sorted_subjects:
        hits = results[subj]["C"]["hits"]
        score = results[subj]["C"]["score"]
        print(f"{subj:<14}  ({score:.3f}) {', '.join(hits)}")

    print()
    print("=" * 80)
    print("VERDICT")
    print("=" * 80)
    print()

    # Check Finding 106 predictions still hold
    f106_correct = 0
    for subj in ("reading", "grammar", "science"):
        if subj not in results:
            continue
        scores = {k: results[subj][k]["score"] for k in ("B", "H", "N", "C")}
        if PREDICTED[subj] == max(scores, key=scores.get):
            f106_correct += 1
    print(f"Finding 106 B/H/N first-3 predictions (after adding C):")
    print(f"  {f106_correct} / 3 still hold with C in the comparison")

    # Check geography ↔ C prediction
    geog_top = max(
        {k: results["geography"][k]["score"]
         for k in ("B", "H", "N", "C")},
        key=lambda k: results["geography"][k]["score"],
    ) if "geography" in results else None
    print()
    print(f"Geography ↔ C prediction:")
    if geog_top == "C":
        print(f"  CONFIRMED — geography tops C (substrate-projection axis "
              f"empirically attested)")
    else:
        print(f"  NOT CONFIRMED — geography tops {geog_top}")

    # Which subjects have the HIGHEST C-score?
    c_top_score = max(results[s]["C"]["score"] for s in results)
    c_top_subjects = [s for s in results if results[s]["C"]["score"]
                      == c_top_score]
    print()
    print(f"Highest C-score: {c_top_score:.3f}")
    print(f"Subjects with highest C: {c_top_subjects}")

    print()
    print("Per MFO §VII.6.20: form-iso reading, not substrate-identity.")
    print()

    # Save
    out_path = Path(__file__).parent / "R-RBS-LM-86_c_chirality_results.json"
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
                "C": sorted(C_SIGNATURE),
            },
            "results": serializable,
            "f106_correct": f106_correct,
            "geography_top": geog_top,
        }, f, indent=2)
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
