"""F1201 (#243): FEASIBILITY of #2 (Siona "write determinatives") — is the English determinative RECOVERABLE?

#2 wants Siona to emit a class-tag (person/place/thing…) with each entity at generation (F1200: write the determinative,
don't reconstruct it). Feasible only if we can cheaply ASSIGN a class to an English noun. Hypothesis (composes
[[feedback_relational_not_dense_distributional]]): English HAS determinatives — it just DISTRIBUTES them across the
grammar instead of writing one glyph. The scattered class-markers:
  * RELATIVIZER   — "the man WHO…" → person · "the place WHERE…" → place · "the thing WHICH…" → thing
  * TITLE          — Mr/Mrs/Dr/Lord/Captain/Saint + Name → person
  * (morphology)   — -ist/-man/-ess → person · -land/-town/-shire → place · -tion/-ness/-ity → abstract
So the "hidden content" (referent class) is not absent in English — it is DISTRIBUTED (Sumerian = class LOCAL on the glyph;
English = class DISTRIBUTED across the discourse), and #2 = harvest + RE-CONCENTRATE it into an explicit tag.

Feasibility test (coref-FREE, local cues only, the cheapest possible tagger): harvest the cues per noun; a tagger is
feasible iff (a) COVERAGE — a decent fraction of frequent nouns get ≥1 cue — and (b) AGREEMENT — where ≥2 cue TYPES fire
on the same noun, they AGREE on the class (the distributed determinative is coherent, not noise). Corpus: 3 English novels
(#98/#829/#1342). numpy-free; plain-dict tallies.
"""
import re

PATHS = ["/tmp/gb_98_tale.txt", "/tmp/gb_829_gulliver.txt", "/tmp/gb_1342_pride.txt"]
FUNC = set(("the a an this that these those of in on at by for with from to into onto and or but is was were be been are "
            "am has have had do did not no as it he she they we you i his her its their my your our who whom which what "
            "when where why how there here then than so if").split())
TITLE = set(("mr mrs miss madame madam mademoiselle monsieur dr doctor sir lord lady king queen captain saint st "
             "mother father uncle aunt prince princess duke duchess mister").split())
PERSON_SUF = ("ist", "man", "men", "woman", "women", "ess", "ian")
PLACE_SUF = ("land", "town", "ville", "burgh", "shire", "ton", "ham", "field")
ABS_SUF = ("tion", "ment", "ness", "ity", "ance", "ence", "ism", "ship", "hood")


def toks(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", raw); e = re.search(r"\*\*\* END OF", raw)
    body = raw[s.end():e.start()] if (s and e) else raw
    out, cur = [], []
    for ch in body:
        if ch.isalpha():
            cur.append(ch)
        elif cur:
            out.append("".join(cur)); cur = []
    if cur:
        out.append("".join(cur))
    return out


DETERMINERS = set(("the a an this that these those his her its their my your our some any no every each one two three "
                   "mr mrs").split())


def is_noun_cand(w):
    lw = w.lower()
    return len(lw) >= 3 and lw not in FUNC and w.isalpha()


def is_np_head(T, i):
    """token i is a genuine NOUN (NP head): a determiner within 3 tokens back, and the NP ends here (next is not another
    content word) — the parser-free head-noun heuristic English needs because it does not mark nouns (unlike German
    capitals / Sumerian determinatives)."""
    if not is_noun_cand(T[i]):
        return False
    if i + 1 < len(T) and is_noun_cand(T[i + 1]):
        return False
    return any(T[j].lower() in DETERMINERS for j in range(max(0, i - 3), i))


def suffix_class(lw):
    if any(lw.endswith(s) for s in PLACE_SUF):
        return "place"
    if any(lw.endswith(s) for s in PERSON_SUF):
        return "person"
    if any(lw.endswith(s) for s in ABS_SUF):
        return "abstract"
    return None


if __name__ == "__main__":
    cues = {}          # lemma -> {cuetype -> {class -> count}}
    freq = {}
    for p in PATHS:
        T = toks(p)
        for i, w in enumerate(T):
            lw = w.lower()
            if is_np_head(T, i):
                freq[lw] = freq.get(lw, 0) + 1
                sc = suffix_class(lw)                                 # MORPHOLOGY: the noun's own suffix
                if sc:
                    d = cues.setdefault(lw, {}).setdefault("suf", {}); d[sc] = d.get(sc, 0) + 1
            # RELATIVIZER: the NP-HEAD immediately before who/where/which gets its class
            if lw in ("who", "whom", "where", "which"):
                cls = "person" if lw in ("who", "whom") else "place" if lw == "where" else "thing"
                if i - 1 >= 0 and is_np_head(T, i - 1):
                    d = cues.setdefault(T[i - 1].lower(), {}).setdefault("rel", {})
                    d[cls] = d.get(cls, 0) + 1
            # TITLE: following capitalized name → person
            if lw in TITLE and i + 1 < len(T) and T[i + 1][:1].isupper() and is_noun_cand(T[i + 1]):
                d = cues.setdefault(T[i + 1].lower(), {}).setdefault("title", {})
                d["person"] = d.get("person", 0) + 1

    def top(d):
        return max(sorted(d), key=lambda c: d[c]) if d else None
    freq_nouns = [w for w in freq if freq[w] >= 3]
    tagged = {w: top({c: sum(cd.get(c, 0) for cd in cues[w].values())
                      for c in ("person", "place", "thing", "abstract")}) for w in cues if w in freq}
    tagged = {w: c for w, c in tagged.items() if c}
    coverage = len([w for w in freq_nouns if w in tagged]) / max(1, len(freq_nouns))
    # AGREEMENT: nouns with >=2 distinct cue-types — do the types agree on the class?
    multi = agree = 0
    for w, ct in cues.items():
        types = {t: top(cd) for t, cd in ct.items() if top(cd)}
        if len(types) >= 2:
            multi += 1
            if len(set(types.values())) == 1:
                agree += 1
    inv = {}
    for w, c in tagged.items():
        inv.setdefault(c, []).append((freq.get(w, 0), w))

    print("F1201 (#243): feasibility of #2 — is the English (distributed) determinative recoverable?\n")
    print("   frequent nouns (freq≥3): %d;  nouns given a class by ≥1 grammatical cue: %d  → COVERAGE %.0f%%" % (
        len(freq_nouns), len([w for w in freq_nouns if w in tagged]), 100 * coverage))
    print("   cross-cue AGREEMENT (nouns with ≥2 cue-types agree on the class): %d/%d = %.0f%%\n" % (
        agree, multi, 100 * agree / max(1, multi)))
    print("   recovered class inventory (the distributed English determinative), top nouns per class:")
    for c in sorted(inv, key=lambda c: -len(inv[c])):
        ex = " ".join(w for _, w in sorted(inv[c], reverse=True)[:10])
        print("      %-9s %4d nouns   e.g. %s" % (c, len(inv[c]), ex))
    print("\n  READ: high AGREEMENT (the grammatical cues converge) + decent COVERAGE ⇒ the English determinative is REAL but")
    print("  DISTRIBUTED across the grammar (who/where/which + titles + morphology), recoverable coref-FREE — so #2 is")
    print("  FEASIBLE: harvest the scattered class-markers and RE-CONCENTRATE them into an explicit tag (write the")
    print("  determinative). Sumerian = class LOCAL on the glyph; English = class DISTRIBUTED — both carry it. This same")
    print("  tag is #1's non-circular coref CLASS GATE (F1200). If agreement is low, the cues are noise → #2 not feasible cheaply.")
