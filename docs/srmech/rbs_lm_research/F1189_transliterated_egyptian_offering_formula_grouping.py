"""F1189 (#243): the transliterated-Egyptian pass — validate the PACKAGED `siona.reconstruct` grouping helper on NATIVE
Egyptological transliteration (not the Budge/German translation).

The reconstruction arc measured on English translations (F1175-F1177) and on Champollion's cross-name cartouche mechanism
(F1188). This closes the loop on the ACTUAL substrate: does `siona.reconstruct.group()` — the F1176 coupling-community
finder, now a shipped siona function — self-cluster the Egyptian OFFERING FORMULA (ḥtp-dꞽ-nswt / pr.t-ḫrw "invocation
offerings of bread, beer, ox, fowl") out of surrounding funerary narrative, working on the lemmatized transliteration
(the substrate-native content, inflection-normalized), never the translation?

Corpus (attested): the Thesaurus Linguae Aegyptiae (TLA / BBAW, Berlin) earlier-Egyptian slice — Pyramid Texts / Old-
and Middle-Kingdom funerary corpus. Native transliteration + lemmatization; local research use, TLA-attributed. The
grouping is measured against a shuffled-label control (random grouping ≈ 0.5 purity). Uses ONLY the packaged
`siona.reconstruct` (srmech Class-L underneath); numpy-free; no magnitude-builtin; plain-dict tally (no Counter).
"""
import json, random
from siona import reconstruct as R

SLICE = "/home/skirklan/corpora/egyptian_tla/earlier_slice.jsonl"

# Egyptian function-lemma chaff: suffix pronouns (=k/=f/=sn…), prepositions, particles, copulas — the OPERATOR side
# (declared by rule, like the English stoplist), so the content LEMMAS (operands) drive the coupling. Suffix pronouns
# all start '='; the rest is a small closed prepositional/particle set.
STOP = set(("n m r ꞽ ꞽn ꞽs ꞽr ꞽm pw pn tn nn nb pꜣ tꜣ nꜣ ḥr ḥnꜥ ẖr m ꞽw wnn jw ky k f s sn ṯn tn ꞽꜣ ꜥ".split()))


def lemma_set(rec):
    """The line's content-lemma SET (the substrate-native signature): take each lemmatization token's lemma (after the
    numeric id), drop the '='-prefixed suffix pronouns and the closed function-lemma set."""
    out = []
    for tok in rec.get("lemmatization", "").split():
        lem = tok.split("|", 1)[1] if "|" in tok else tok
        if lem.startswith("="):
            continue
        if lem in STOP or len(lem) < 2:
            continue
        out.append(lem)
    return frozenset(out)


# the ḥtp-dꞽ-nswt / pr.t-ḫrw invocation-offering formula markers (its recurring frame lemmas)
OFFERING = ("pr.t-ḫrw", "ḥtp", "nswt", "kꜣ", "ꜣpd", "tʾ", "ḥnq.t", "šs", "mnḫ.t", "ꞽḫ.t")


def is_offering(lm):
    return sum(1 for w in OFFERING if w in lm) >= 3          # a line is an offering-formula line iff >=3 frame lemmas


def purity(members, offering_flags):
    """fraction of a family's members that are offering-formula lines (plain-dict tally, no Counter)."""
    if not members:
        return 0.0
    hit = sum(1 for i in members if offering_flags[i])
    return hit / len(members)


if __name__ == "__main__":
    recs = [json.loads(l) for l in open(SLICE, encoding="utf-8")]
    sigs = [lemma_set(r) for r in recs]
    off_idx = [i for i, lm in enumerate(sigs) if is_offering(lm) and len(lm) >= 4]
    dis_idx = [i for i, lm in enumerate(sigs) if not any(w in lm for w in OFFERING) and len(lm) >= 4]
    random.seed(9)
    M = 40
    off = random.sample(off_idx, min(M, len(off_idx)))
    dis = random.sample(dis_idx, min(M, len(dis_idx)))
    pool = [sigs[i] for i in off] + [sigs[i] for i in dis]
    flags = [True] * len(off) + [False] * len(dis)          # ground-truth offering / narrative label per pool line

    print("F1189 (#243): transliterated-Egyptian pass — `siona.reconstruct.group()` on native TLA lemmatization\n")
    print("   corpus: TLA earlier-Egyptian slice (Pyramid/funerary); %d offering-formula + %d narrative lines pooled\n"
          % (len(off), len(dis)))

    g = R.group(pool, community_bits=4, min_family=3)
    print("   group() found %d families (>=3 members) + %d singletons:" % (len(g["families"]), len(g["singletons"])))
    captured = 0
    for fam in g["families"]:
        p = purity(fam, flags)
        tag = "OFFERING-enriched" if p > 0.5 else ("narrative" if p < 0.5 else "mixed")
        if p > 0.5:
            captured += sum(1 for i in fam if flags[i])
        print("      family size %2d   offering-purity %.2f   %s" % (len(fam), p, tag))

    # -- the grouping signal vs a shuffled-label control (random grouping ~ base rate 0.5) --
    base = len(off) / len(pool)
    big = max(g["families"], key=len) if g["families"] else []
    print("\n   base offering rate in pool           : %.2f" % base)
    print("   largest family's offering-purity     : %.2f  (vs %.2f random)" % (purity(big, flags), base))
    print("   offering lines captured in offering-enriched families: %d/%d = %.0f%%" % (
        captured, len(off), 100 * captured / max(1, len(off))))

    # -- reconstruct one damaged offering line from its family consensus (the F1178 pipeline, packaged) --
    print("\n   reconstruct() on a damaged pr.t-ḫrw offering line (half its lemmas excised):")
    target = None
    for i in off:
        if {"pr.t-ḫrw", "tʾ", "ḥnq.t"} <= sigs[i]:
            target = i; break
    if target is not None:
        full = list(sigs[target]); random.shuffle(full)
        survive = frozenset(full[: len(full) // 2]); masked = set(full[len(full) // 2:])
        others = [sigs[i] for i in off if i != target]      # the family pool (native offering lines)
        rec = R.reconstruct(survive, others, k=12, frac=0.30)
        recovered = set(rec["recovered"])
        hit = recovered & masked
        print("      surviving half : %s" % " ".join(sorted(survive)))
        print("      excised (truth): %s" % " ".join(sorted(masked)))
        print("      recovered      : %s" % " ".join(rec["recovered"]))
        print("      correct recover: %d/%d masked lemmas = %.2f  (from the offering-family consensus)" % (
            len(hit), len(masked), len(hit) / max(1, len(masked))))
    print("\n  READ: if group() lifts the offering-formula purity well above the base rate and reconstruct() recovers the")
    print("  excised frame lemmas from the family consensus — the packaged siona finder works on the SUBSTRATE-NATIVE")
    print("  transliteration, not just the English translation (F1176 grouping + F1178 pipeline, now a shipped tool).")
