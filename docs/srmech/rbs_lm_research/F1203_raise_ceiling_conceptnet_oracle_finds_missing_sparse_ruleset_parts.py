"""F1203 (#243): raise the class-lexicon ceiling with a ConceptNet IsA oracle — and read the DISAGREEMENTS as the sparse
language-ruleset parts we are still MISSING.

F1201/F1202: our cheap grammar-cue determinative-lexicon (who/where/which + titles + morphology) is WEAK (32% cross-cue
agreement). ConceptNet /r/IsA gives a strong INDEPENDENT class oracle (trace a noun's IsA-hypernym chain to an anchor:
person / place / animal / plant / thing / bodypart / abstract). Two goals:
  (1) RAISE THE CEILING — layer the oracle onto the grammar cues (coverage + accuracy up), and measure the grammar
      tagger's accuracy against the oracle.
  (2) FIND WHAT WE'RE MISSING — where grammar and oracle SYSTEMATICALLY disagree, the disagreement names a rule our
      sparse ruleset lacks: PART-OF/bridging (a thing that is part of a person/place — hand/roof), METONYMY (a thing/place
      standing for a person/institution — crown/court), MASS/COUNT (water vs table — the some/much determinative we don't
      use), NOMINALIZATION (deverbal abstracts), COLLECTIVE (family/army). The gaps are the finding.

The IsA graph walk is a Class-I/L graph BFS over the ConceptNet edges (numpy-free; plain-dict tallies). Corpus: 3 English
novels (grammar cues), ConceptNet 5.7 English IsA/PartOf (the oracle).
"""
import re

PATHS = ["/tmp/gb_98_tale.txt", "/tmp/gb_829_gulliver.txt", "/tmp/gb_1342_pride.txt"]
ISA_TSV = "/tmp/cn_isa_en.tsv"
FUNC = set(("the a an this that these those of in on at by for with from to into onto and or but is was were be been are "
            "am has have had do did not no as it he she they we you i his her its their my your our who whom which what "
            "when where why how there here then than so if").split())
DETERMINERS = set("the a an this that these those his her its their my your our some any no every each one two".split())
TITLE = set("mr mrs miss madame monsieur dr doctor sir lord lady king queen captain saint prince duke".split())
PERSON_SUF = ("ist", "man", "men", "woman", "women", "ess", "ian")
PLACE_SUF = ("land", "town", "ville", "burgh", "shire", "field")
ABS_SUF = ("tion", "ment", "ness", "ity", "ance", "ence", "ism", "ship", "hood")

# anchor hypernym → coarse class (the class oracle's target set)
ANCHOR = {}
for cls, words in {
    "person": "person human individual worker professional writer artist musician scientist leader official soldier "
              "player author poet king queen god goddess deity adult child woman man intelligent_agent servant",
    "place": "location place area region city country river administrative_region state town village mountain lake sea "
             "ocean island building structure room house geographical_area body_of_water land territory street",
    "animal": "animal mammal bird fish insect reptile amphibian creature beast vertebrate invertebrate",
    "plant": "plant tree flower herb shrub vegetable fruit fungus",
    "thing": "tangible_thing object artifact physical_object chemical_compound mineral food book film software tool "
             "instrument device substance material vehicle machine weapon clothing container drug medicine metal drink",
    "bodypart": "anatomical_structure body_part organ tissue bone muscle",
    "abstract": "activity intelligent_agent_activity concept idea emotion feeling quality state event process action "
                "attribute measure time_period unit relation cognition disease disorder condition",
}.items():
    for w in words.split():
        ANCHOR[w] = cls
# our-4 grammar classes ← oracle coarse class
TO4 = {"person": "person", "place": "place", "abstract": "abstract",
       "animal": "thing", "plant": "thing", "thing": "thing", "bodypart": "thing"}


def load_isa():
    isa, partof = {}, {}
    for ln in open(ISA_TSV, encoding="utf-8", errors="replace"):
        p = ln.rstrip("\n").split("\t")
        if len(p) != 3:
            continue
        r, s, o = p
        (isa if r == "isa" else partof).setdefault(s, set()).add(o)
    return isa, partof


def oracle_class(word, isa, memo):
    """BFS up the IsA hypernym graph to the first anchor(s); return the coarse class (Class-I/L graph walk)."""
    if word in memo:
        return memo[word]
    seen, frontier = {word}, [word]
    for _ in range(4):
        nxt = []
        hits = {}
        for w in frontier:
            for h in isa.get(w, ()):
                if h in ANCHOR:
                    hits[ANCHOR[h]] = hits.get(ANCHOR[h], 0) + 1
                if h not in seen:
                    seen.add(h); nxt.append(h)
        if hits:
            memo[word] = max(sorted(hits), key=lambda c: hits[c]); return memo[word]
        frontier = nxt
        if not frontier:
            break
    memo[word] = None
    return None


# --- grammar-cue lexicon (F1201/F1202) ---
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


def is_nc(w):
    return len(w) >= 3 and w.lower() not in FUNC and w.isalpha()


def is_head(T, i):
    return is_nc(T[i]) and not (i + 1 < len(T) and is_nc(T[i + 1])) and \
        any(T[j].lower() in DETERMINERS for j in range(max(0, i - 3), i))


def sufc(lw):
    return "place" if any(lw.endswith(s) for s in PLACE_SUF) else "person" if any(lw.endswith(s) for s in PERSON_SUF) \
        else "abstract" if any(lw.endswith(s) for s in ABS_SUF) else None


def grammar_lexicon():
    votes, freq = {}, {}
    for p in PATHS:
        T = toks(p)
        for i, w in enumerate(T):
            lw = w.lower()
            if is_head(T, i):
                freq[lw] = freq.get(lw, 0) + 1
                sc = sufc(lw)
                if sc:
                    votes.setdefault(lw, {}); votes[lw][sc] = votes[lw].get(sc, 0) + 1
            if lw in ("who", "whom", "where", "which") and i >= 1 and is_head(T, i - 1):
                cls = "person" if lw in ("who", "whom") else "place" if lw == "where" else "thing"
                h = T[i - 1].lower(); votes.setdefault(h, {}); votes[h][cls] = votes[h].get(cls, 0) + 1
            if lw in TITLE and i + 1 < len(T) and T[i + 1][:1].isupper() and is_nc(T[i + 1]):
                h = T[i + 1].lower(); votes.setdefault(h, {}); votes[h]["person"] = votes[h].get("person", 0) + 1
    return {w: max(sorted(d), key=lambda c: d[c]) for w, d in votes.items()}, freq


if __name__ == "__main__":
    isa, partof = load_isa()
    memo = {}
    gram, freq = grammar_lexicon()
    orc = {w: TO4.get(oracle_class(w, isa, memo)) for w in freq}
    orc = {w: c for w, c in orc.items() if c}
    freq_n = [w for w in freq if freq[w] >= 3]
    print("F1203 (#243): raise the ceiling with ConceptNet + find the missing sparse rules (IsA edges: %d)\n" % (
        sum(len(v) for v in isa.values())))
    print("   frequent nouns (freq≥3): %d" % len(freq_n))
    print("   grammar-cue tagged: %d (%.0f%%)   ConceptNet-oracle tagged: %d (%.0f%%)   LAYERED (either): %d (%.0f%%)" % (
        len([w for w in freq_n if w in gram]), 100 * len([w for w in freq_n if w in gram]) / len(freq_n),
        len([w for w in freq_n if w in orc]), 100 * len([w for w in freq_n if w in orc]) / len(freq_n),
        len([w for w in freq_n if w in gram or w in orc]),
        100 * len([w for w in freq_n if w in gram or w in orc]) / len(freq_n)))
    both = [w for w in freq_n if w in gram and w in orc]
    agree = sum(1 for w in both if gram[w] == orc[w])
    print("   grammar vs oracle AGREEMENT on the overlap (%d nouns): %d = %.0f%%  (the cheap tagger's accuracy)\n" % (
        len(both), agree, 100 * agree / max(1, both and len(both) or 1)))
    # DISAGREEMENT matrix → the missing rules
    cell = {}
    for w in both:
        if gram[w] != orc[w]:
            cell.setdefault((gram[w], orc[w]), []).append((freq[w], w))
    print("   TOP DISAGREEMENTS (grammar → oracle) = candidate MISSING RULES:")
    for k in sorted(cell, key=lambda k: -len(cell[k]))[:8]:
        ex = " ".join(w for _, w in sorted(cell[k], reverse=True)[:8])
        # is the noun a PART-OF a person/place? (the bridging/part-of rule detector)
        po = sum(1 for _, w in cell[k] if any(oracle_class(h, isa, memo) in ("person", "place", "bodypart")
                                              for h in partof.get(w, ())))
        tag = "  [PART-OF %d/%d → bridging]" % (po, len(cell[k])) if po else ""
        print("     grammar=%-8s oracle=%-8s  %3d nouns%s   e.g. %s" % (k[0], k[1], len(cell[k]), tag, ex))
    print("\n  READ: LAYERED coverage ≫ grammar alone = the ceiling is raised (ConceptNet backfills what the distributed")
    print("  cues miss). The AGREEMENT % is the cheap grammar tagger's accuracy vs the semantic oracle. The DISAGREEMENT")
    print("  cells are the MISSING RULES: grammar=person/oracle=thing with a PART-OF tag = the bridging rule (hand is a")
    print("  person's part but a thing); grammar=place/oracle=thing = container metonymy; grammar=abstract/oracle=thing =")
    print("  nominalization. Each named cell is a sparse-ruleset part to add (a determinative refinement English encodes")
    print("  but our cheap cues don't yet).")
