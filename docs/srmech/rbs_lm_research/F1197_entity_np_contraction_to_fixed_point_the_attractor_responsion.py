"""F1197 (#243): the RESPONSION as an attractor-contraction, taken literally — does a referring expression CONTRACT to a
fixed point across an entity's mentions? (the entity-scale test F1196's scene-scale null could not address)

F1196 refuted the SCENE-clock responsion (the ramp is dead; a boundary-burst is weak/mixed). Fable's cleaner intrinsic
test is the ENTITY scale: after an entity is introduced with a long NP ("a large old house"), later mentions contract
("the house" → "it") — the attractor-contraction (F1186: the responsion pulls the operand into its fixed-point slot),
visible entirely inside the text, per entity. This IS the well-attested referential-form / accessibility decay (Givón
topic-continuity, Ariel's accessibility scale) — the framework READS that phenomenon AS the responsion (no lineage claim;
it reads what the phenomenon already is).

Measurement: for each recurring, noun-like entity (a content lemma with >=5 mentions, determiner-preceded >=30% of the
time), compute each mention's NP LENGTH (the pre-nominal modifier run back to the determiner: "a large old house"=4,
"the house"=2), ordered by mention index. Signature: L(first mention) > mean L(later) — a contraction. DISCRIMINANT (the
attractor is ORDER-locked): shuffle which mention is "first" within each entity; if the real first-mention-longer effect
beats the shuffle null, the contraction is locked to actual mention ORDER (an attractor pulling later forms shorter), not
length variance. Also track P(definite) by mention index (the a→the shift = the same contraction on the article).

Corpus: 6 novels (#98/#829/#1342/#84/#1260/#120). Punctuation kept as NP boundaries. numpy-free; no magnitude-builtin;
plain-dict tallies; integer counts.
"""
import re, random

NOVELS = ["/tmp/gb_98_tale.txt", "/tmp/gb_829_gulliver.txt", "/tmp/gb_1342_pride.txt",
          "/tmp/gb_84_franken.txt", "/tmp/gb_1260_janeeyre.txt", "/tmp/gb_120_treasure.txt"]

DET = set("the a an this that these those his her its their my your our no some each every another such one".split())
FUNC = set((
    "the a an this that these those i you he she it we they me him her us them my your his its our their who whom whose "
    "which what of in on at by for with from to into onto upon over under above below between among through during before "
    "after since until about against without within along across behind beyond beside near off out up down and or but nor "
    "so yet as if than because while although though unless whereas whether when where why how is am are was were be been "
    "being have has had do does did will would shall should can could may might must ought not no too very just only also "
    "then there here now thus hence however moreover indeed all any some each every none both few many much more most less "
    "least several enough such same other another one two").split())


def tokenize(path):
    """→ list of tokens; punctuation collapses to the boundary marker '·' (an NP cannot span it)."""
    raw = open(path, encoding="utf-8", errors="replace").read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", raw); e = re.search(r"\*\*\* END OF", raw)
    body = raw[s.end():e.start()] if (s and e) else raw
    out, cur = [], []
    for ch in body.lower():
        if "a" <= ch <= "z":
            cur.append(ch)
        else:
            if cur:
                out.append("".join(cur)); cur = []
            if ch in ".,;:!?—-\"'()[]" and (not out or out[-1] != "·"):
                out.append("·")
    if cur:
        out.append("".join(cur))
    return out


def np_length(toks, i):
    """the pre-nominal NP of the noun at index i: walk back over modifiers to the determiner (incl.) or a boundary.
    Returns (length, article) where article ∈ {the, a, an, poss/dem/..., 'bare'}."""
    length = 1; art = "bare"; j = i - 1
    while j >= 0 and (i - j) <= 5:
        t = toks[j]
        if t == "·":
            break
        if t in DET:
            length += 1; art = t; break
        if t in FUNC:                      # a non-determiner function word = the NP's left boundary (bare NP)
            break
        length += 1; j -= 1                # a content token before the noun = a modifier
    return length, art


def analyze(path):
    toks = tokenize(path)
    ment = {}                              # lemma -> list of (np_length, is_definite) in mention order
    detc = {}; totc = {}
    for i, w in enumerate(toks):
        if w == "·" or w in FUNC or len(w) < 3:
            continue
        L, art = np_length(toks, i)
        ment.setdefault(w, []).append((L, 1 if art == "the" else 0))
        totc[w] = totc.get(w, 0) + 1
        if art != "bare":
            detc[w] = detc.get(w, 0) + 1
    # noun-like recurring entities: >=5 mentions AND determiner-preceded >=30%
    ents = [w for w in ment if totc[w] >= 5 and detc.get(w, 0) / totc[w] >= 0.30]
    # per-entity contraction: L(first) - mean L(rest)
    deltas = []; seqs = []
    binL = {1: [], 2: [], 3: [], 4: []}; binDef = {1: [], 2: [], 3: [], 4: []}
    for w in ents:
        seq = ment[w]
        Ls = [x[0] for x in seq]
        rest = Ls[1:]
        if rest:
            deltas.append(Ls[0] - sum(rest) / len(rest))
        seqs.append((w, Ls))
        for k, (L, d) in enumerate(seq):
            b = min(k + 1, 4)
            binL[b].append(L); binDef[b].append(d)
    amp_true = sum(deltas) / len(deltas) if deltas else 0.0
    # ORDER-LOCK null: within each entity, randomly pick which mention is "first"
    rng = random.Random(29)
    ge = 0
    for _ in range(1000):
        acc = []
        for w in ents:
            Ls = [x[0] for x in ment[w]]
            k = rng.randrange(len(Ls))
            rest = Ls[:k] + Ls[k + 1:]
            if rest:
                acc.append(Ls[k] - sum(rest) / len(rest))
        amp = sum(acc) / len(acc) if acc else 0.0
        if amp >= amp_true:
            ge += 1
    pval = (ge + 1) / 1001
    meanL = {b: (sum(binL[b]) / len(binL[b]) if binL[b] else 0.0) for b in (1, 2, 3, 4)}
    pdef = {b: (sum(binDef[b]) / len(binDef[b]) if binDef[b] else 0.0) for b in (1, 2, 3, 4)}
    return len(ents), amp_true, pval, meanL, pdef, seqs


if __name__ == "__main__":
    print("F1197 (#243): entity-level NP contraction to a fixed point — the responsion as attractor-contraction\n")
    beats = 0
    for path in NOVELS:
        name = path.split("/")[-1]
        ne, amp, p, meanL, pdef, seqs = analyze(path)
        beats += 1 if p < 0.05 else 0
        print("  %-20s  %d entities" % (name, ne))
        print("     mean NP length by mention-index  1:%.2f  2:%.2f  3:%.2f  4+:%.2f   (contraction if 1 > 4+)"
              % (meanL[1], meanL[2], meanL[3], meanL[4]))
        print("     P(definite) by mention-index     1:%.2f  2:%.2f  3:%.2f  4+:%.2f   (the a→the shift)"
              % (pdef[1], pdef[2], pdef[3], pdef[4]))
        print("     first-mention-longer amplitude = %+.3f   order-shuffle null p = %.3f   %s" % (
            amp, p, "ORDER-LOCKED CONTRACTION (beats null)" if p < 0.05 else "within null"))
        ex = sorted(seqs, key=lambda s: -len(s[1]))[:2]
        for w, Ls in ex:
            print("       e.g. '%s' NP-lengths across mentions: %s" % (w, Ls[:12]))
        print()
    print("  READ: mean NP length index-1 > index-4+ AND first-mention-longer amplitude beats the ORDER-shuffle null ⇒ the")
    print("  referring form CONTRACTS to a fixed point across mentions, locked to mention ORDER = the attractor-contraction")
    print("  (F1186), the responsion at the ENTITY scale, entirely inside the text. If it holds where the SCENE-clock")
    print("  (F1196) did not, the responsion lives at the entity scale — the a→the shift (P(def) rising) is the same")
    print("  contraction on the article. (Framework READS the attested referential-form decay AS the responsion.)")
