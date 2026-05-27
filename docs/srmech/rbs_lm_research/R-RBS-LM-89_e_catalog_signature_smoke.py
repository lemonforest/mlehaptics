"""R-RBS-LM-89 — E (catalog) signature test.

Per CLAUDE.md §1, E = catalog enumeration (cascade-detection class).

Plausible vocabulary: list / items / kinds / types / groups / classes /
named / categories. History materials are the strongest candidate
(history IS catalog of events, kings, dynasties).

Other plausible E-substrate candidates:
  - Geography (catalog of places, regions, countries)
  - Cookbooks (catalog of recipes)
  - Field guides (catalog of species; not in current corpus)

Per `[[feedback_dont_pre_commit_spike_query_operators]]` —
curate vocabulary from class semantics, not corpus-leaning.
"""

import json
import re
from collections import Counter
from pathlib import Path


# E signature — catalog enumeration vocabulary
E_SIGNATURE = {
    "list", "lists", "listed", "listing",
    "item", "items",
    "kind", "kinds", "type", "types",
    "sort", "sorts", "sorted", "sorting",
    "group", "groups", "grouped", "grouping",
    "class", "classes", "classified", "classification",
    "category", "categories", "categorized",
    "entry", "entries",
    "named", "naming",
    "chapter", "chapters",
    "section", "sections",
    "table", "tables",
    "index", "indices",
}


# Re-use prior signatures for context
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
    print("=" * 95)
    print("R-RBS-LM-89 — E (catalog) signature test")
    print("(extends to 9-operator coverage of A-N partition)")
    print("=" * 95)
    print()

    sig_sets = [
        ("B", B_SIGNATURE), ("H", H_SIGNATURE), ("N", N_SIGNATURE),
        ("C", C_SIGNATURE), ("I", I_SIGNATURE), ("J", J_SIGNATURE),
        ("D", D_SIGNATURE), ("E", E_SIGNATURE), ("F", F_SIGNATURE),
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

    print("=" * 95)
    print("NINE-OPERATOR SIGNATURE SCORES")
    print("=" * 95)
    print()
    header = f"{'subject':<14}"
    for name, _ in sig_sets:
        header += f" {name:>6}"
    header += "   top"
    print(header)
    print("-" * 95)

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
    print("=" * 95)
    print("E-SIGNATURE DETAILS")
    print("=" * 95)
    print()
    sorted_subj = sorted(results.keys(),
                         key=lambda s: -results[s]["E"]["score"])
    for subj in sorted_subj:
        r = results[subj]["E"]
        if r["overlap"] > 0:
            print(f"  {subj:<14}  score={r['score']:.3f}  hits: "
                  f"{', '.join(r['hits'])}")
    print()

    print("=" * 95)
    print("VERDICT")
    print("=" * 95)
    print()

    e_top = max(results.keys(), key=lambda s: results[s]["E"]["score"])
    e_top_score = results[e_top]["E"]["score"]

    print(f"E-signature top: {e_top} ({e_top_score:.3f})")
    print()
    print("Pre-test predictions:")
    print("  E: history / geography (catalog of events / places)")
    print()
    e_clean = e_top in ("history", "geography")
    print(f"E clean match (history/geography): "
          f"{'YES' if e_clean else f'NO (was {e_top})'}")
    print(f"E score signal strength: "
          f"{'STRONG' if e_top_score >= 0.20 else 'WEAK' if e_top_score >= 0.10 else 'NULL'}")

    print()
    if e_top_score >= 0.10:
        print(f"VERDICT: E has detectable surface signature.")
        print(f"  9 of 14 operators now attested at form-iso level.")
    else:
        print(f"VERDICT: E has NULL/weak surface signature.")
        print(f"  Confirms cascade-detection ops largely lack surface vocab.")

    print()
    print("Per MFO §VII.6.20: form-iso reading, not substrate-identity.")
    print()

    out_path = Path(__file__).parent / "R-RBS-LM-89_e_catalog_results.json"
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
            "e_top": e_top,
            "e_clean_match": e_clean,
        }, f, indent=2)
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
