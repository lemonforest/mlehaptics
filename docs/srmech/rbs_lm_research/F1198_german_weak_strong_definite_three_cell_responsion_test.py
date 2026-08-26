"""F1198 (#243): the 3-cell responsion test on a language that SPELLS the distinction — German weak/strong definites.

English collapses DETECT (anaphoric "the") / RESPONSION (accommodation "the") / EXTERNAL (uniqueness "the sun") into one
word, which is why F1194–F1197 could not separate them. German SPELLS the split (Schwarz 2009, "Two Types of Definites",
web-verified): the preposition+article CONTRACTION (im/am/zum/zur/beim/vom/ins/ans/aufs) is the WEAK = situationally-unique
article; the FULL form (in dem / an dem / zu dem / …) is the STRONG = ANAPHORIC article, bearing an index like a pronoun
(it refers back to an antecedent). So the morphology gives the labels for FREE — no coreference needed for the weak/strong
axis. A light recency check then splits STRONG into the two k-cells:
  * WEAK (contracted)            = uniqueness / situational   (the EXTERNAL cell — no prior referent needed)
  * STRONG (full) + recent noun  = anaphoric                  (the DETECT cell, k=2 — the antecedent is there)
  * STRONG (full) + NO recent    = accommodation              (the RESPONSION cell — strong/anaphoric morphology used
                                                               WITHOUT an antecedent ⇒ the reader constructs one)

Two decisive checks (the "don't assume anything incompletely" ones):
  (1) VALIDATE the categories are real, not imposed: P(recent | STRONG) ≫ P(recent | WEAK), tested vs a label-shuffle null.
      If the gap is large, German morphology genuinely tracks anaphoric-vs-uniqueness — the reframe's cells are real.
  (2) Then MEASURE the responsion cell: is STRONG-but-not-recent (accommodation) non-trivial? If ~0, strong is purely
      anaphoric and there is NO separable responsion (F1195's "external" holds); if non-trivial, accommodation is a real
      third operation (the responsion, confirmed by morphology).

German nouns are CAPITALIZED → the head noun is the next Capitalized token (no tagger). "same" NPs excluded (Schwarz's
weak-anaphoric exception). Corpus: 5 Gutenberg German works. numpy-free; no magnitude-builtin; plain-dict tallies.
"""
import re, random

WORKS = [("Zauberberg (Mann)", "/tmp/de_65661.txt"), ("Mabuse (Jacques)", "/tmp/de_50285.txt"),
         ("Venus im Pelz (Sacher-Masoch)", "/tmp/de_56156.txt"), ("Traumdeutung (Freud)", "/tmp/de_40739.txt"),
         ("Humboldt Reise", "/tmp/de_24746.txt")]

WEAK = {"im", "am", "zum", "zur", "beim", "vom", "ins", "ans", "aufs"}          # contracted = weak/uniqueness (Schwarz)
STRONG_PAIRS = {("in", "dem"), ("in", "das"), ("an", "dem"), ("an", "das"), ("zu", "dem"), ("zu", "der"),
                ("bei", "dem"), ("von", "dem"), ("auf", "das")}                  # full = strong/anaphoric
PREPS = {p for p, _ in STRONG_PAIRS}
ARTS = {a for _, a in STRONG_PAIRS}
SAME = {"selbe", "selben", "gleiche", "gleichen", "nämliche", "nämlichen", "dieselbe", "derselbe", "dasselbe"}
WINDOW = 200                                                                     # a recent antecedent = within ~200 tokens


def tokenize(path):
    """→ list of (raw, lower); punctuation → boundary '·'. Case KEPT (German nouns are Capitalized = the head-noun cue)."""
    raw = open(path, encoding="utf-8", errors="replace").read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", raw); e = re.search(r"\*\*\* END OF", raw)
    body = raw[s.end():e.start()] if (s and e) else raw
    out, cur = [], []
    for ch in body:
        if ch.isalpha():
            cur.append(ch)
        else:
            if cur:
                w = "".join(cur); out.append((w, w.lower())); cur = []
            if ch in ".,;:!?—-\"'()»«„“”" and (not out or out[-1][0] != "·"):
                out.append(("·", "·"))
    if cur:
        w = "".join(cur); out.append((w, w.lower()))
    return out


def head_noun(toks, j):
    """the next Capitalized noun from index j, skipping lowercase adjectives; None if a boundary/'same' comes first."""
    for k in range(j, min(j + 4, len(toks))):
        raw, low = toks[k]
        if raw == "·":
            return None
        if low in SAME:
            return None
        if raw[:1].isupper() and len(raw) >= 2 and raw.isalpha():
            return low
    return None


def analyze(path):
    toks = tokenize(path)
    n = len(toks)
    last_seen = {}
    ev = []                                            # (is_strong, recent)
    for i, (raw, low) in enumerate(toks):
        typ = head = None
        if low in WEAK:
            head = head_noun(toks, i + 1); typ = 0
        elif low in PREPS and i + 1 < n and toks[i + 1][1] in ARTS and (low, toks[i + 1][1]) in STRONG_PAIRS:
            if toks[i + 2][1] != "·" if i + 2 < n else False:
                head = head_noun(toks, i + 2); typ = 1
        if head is not None:
            recent = (i - last_seen.get(head, -10 ** 9)) <= WINDOW
            ev.append((typ, 1 if recent else 0))
        if raw[:1].isupper() and len(raw) >= 2 and raw.isalpha():   # a noun mention → update recency
            last_seen[low] = i
    return ev


def rate(ev, strong, recent):
    d = [e for e in ev if e[0] == strong]
    return (sum(1 for e in d if e[1] == recent) / len(d)) if d else 0.0, len(d)


if __name__ == "__main__":
    print("F1198 (#243): German weak/strong definites — the 3-cell responsion test (morphology labels the split)\n")
    for name, path in WORKS:
        ev = analyze(path)
        pw, nw = rate(ev, 0, 1)                        # P(recent | WEAK)
        ps, ns = rate(ev, 1, 1)                        # P(recent | STRONG)
        gap = ps - pw
        # label-shuffle null: is the strong-vs-weak recency gap real, or an artifact?
        recs = [e[1] for e in ev]; strs = [e[0] for e in ev]; nstrong = sum(strs)
        rng = random.Random(41); ge = 0
        for _ in range(1000):
            idx = list(range(len(ev))); rng.shuffle(idx)
            sset = set(idx[:nstrong])
            sr = [recs[k] for k in range(len(ev)) if k in sset]
            wr = [recs[k] for k in range(len(ev)) if k not in sset]
            g = (sum(sr) / len(sr) if sr else 0) - (sum(wr) / len(wr) if wr else 0)
            if g >= gap:
                ge += 1
        p = (ge + 1) / 1001
        # the 3 cells
        weak_frac = nw / len(ev) if ev else 0
        detect = ps                                    # strong & recent  (of strong)
        respn = 1 - ps                                 # strong & NOT recent = accommodation (of strong)
        print("  %-30s  %d weak(uniqueness) + %d strong events" % (name, nw, ns))
        print("     P(recent | WEAK)   = %.2f    P(recent | STRONG) = %.2f    gap = %+.2f   shuffle-null p = %.3f  %s" % (
            pw, ps, gap, p, "MORPHOLOGY TRACKS SEMANTICS" if (p < 0.05 and gap > 0.05) else "weak/absent"))
        print("     STRONG split →  DETECT (anaphoric, recent) %.2f   |   RESPONSION (accommodation, novel) %.2f" % (
            detect, respn))
        print()
    print("  READ: (1) P(recent|STRONG) ≫ P(recent|WEAK) with a below-.05 shuffle-null ⇒ the German morphology genuinely")
    print("  separates anaphoric (strong) from uniqueness (weak) — the reframe's cells are REAL, not our imposition. (2) The")
    print("  STRONG 'RESPONSION' fraction = strong/anaphoric morphology used with NO recent antecedent = accommodation (the")
    print("  reader constructs the referent) = the intrinsic responsion, MEASURED with morphology as ground truth, no coref.")
    print("  If that cell is non-trivial, the responsion is a real separable third op (vs F1195's all-external reading).")
