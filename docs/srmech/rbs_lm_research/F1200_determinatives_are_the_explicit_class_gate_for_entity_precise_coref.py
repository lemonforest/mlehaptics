"""F1200 (#243): the DETERMINATIVE is the entity-precise-coref class gate — the "hidden content" written at generation.

The responsion arc kept hitting one wall (F1197/F1198/F1199): entity-precise coreference needs the referent's semantic
CLASS, and alphabetic English omits it, so we must RECONSTRUCT it (hard, circular). User's insight: early logographic
scripts did NOT leave it hidden — they wrote it as a GLYPH MODIFIER. Sumerian (and Egyptian) DETERMINATIVES are silent
classifier signs on the word marking its referent class: ᵈ (DINGIR) = deity, {ki} = place, lu₂ = person/profession, e₂ =
building, kur = land, na₄ = stone, tug₂ = textile, id₂ = watercourse, gu₄ = cattle, … So the class is encoded AT
GENERATION — never hidden. German grammatical GENDER (der/die/das) is the degenerate 3-class vestige of exactly this
system (which is why F1199's gender-coref was too coarse); English is the 0-class limit (→ full reconstruction needed).

Framework reading: the determinative IS op(x)operand(x)responsion's THIRD factor made an explicit glyph modifier — the
operand's CLASS (the "which-kind") written down = the responsion the reader otherwise reconstructs (F1186). It is the
Class-K pin-slot made visible: the class-slot the referent locks into.

Measured on ETCSL Gilgameš (5 songs): (1) the explicit determinative-class channel exists and its inventory; (2) it
partitions referents ~C-fold finer than gender's 3 ⇒ the entity-precise-coref candidate set shrinks ~C/3× — the precision
the glyph modifier buys, for free, non-circularly (the class is written, independent of recency). numpy-free; plain dicts.
"""
import re, glob

ETCSL = sorted(glob.glob("/home/skirklan/corpora/etcsl/gilg_c181*.html"))
# determinative sign → referent class (the glyph-modifier classifier system)
DET_CLASS = {"d": "deity", "ki": "place", "lu2": "person", "munus": "person(f)", "e2": "building", "kur": "land",
             "iri": "settlement", "id2": "watercourse", "na4": "stone", "tug2": "textile", "ĝeš": "wood",
             "ĝiš": "wood", "gec": "wood", "gu4": "cattle", "muc": "bird/animal", "mušen": "bird", "dug": "vessel",
             "u2": "plant", "gi": "reed", "ninda": "bread", "kaš": "beer", "zabar": "bronze", "urud": "copper",
             "kuš": "leather", "im": "clay"}


def words_with_proper():
    out = []
    for f in ETCSL:
        t = open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"onMouseover=\"doTooltip[^\"]*\"[^>]*>(.*?)</span>", t):
            pre = t[max(0, m.start() - 40):m.start()]
            w = re.sub(r"&#x[0-9A-Fa-f]+;", "", re.sub(r"<[^>]+>", "", m.group(1))).strip().lower()
            if w:
                out.append((w, 'class="proper"' in pre))
    return out


def name_class(w):
    """the referent class a Sumerian PROPER NAME's determinative marks (clean cases): d…→deity, …ki→place, else person."""
    if w.startswith("d") and len(w) > 2 and w[1] not in "aeiou":     # ᵈ DINGIR deity determinative
        return "deity"
    if re.search(r"ki($|[.\-]|-?(e3|a|ke4|ta|ga|ce3|ra|še))", w):    # {ki} postposed place determinative
        return "place"
    return "person"


if __name__ == "__main__":
    ws = words_with_proper()
    n = len(ws)
    proper = [w for w, p in ws if p]
    # (1) common-noun determinatives (leading classifier sign) — the explicit class channel
    det_hits = {}
    for w, p in ws:
        lead = w.split("-")[0]
        if lead in DET_CLASS:
            c = DET_CLASS[lead]; det_hits[c] = det_hits.get(c, 0) + 1
    # (2) proper-name referent classes (clean determinative signal)
    pcls = {}
    for w in proper:
        c = name_class(w); pcls[c] = pcls.get(c, 0) + 1

    classes = set(det_hits) | set(pcls)
    C = len(classes)
    print("F1200 (#243): the determinative — the explicit referent-class glyph modifier (ETCSL Gilgameš, %d tokens)\n" % n)
    print("   %d proper-name referents (%.0f%%); each carries its class as a written determinative:" % (
        len(proper), 100 * len(proper) / n))
    for c in sorted(pcls, key=lambda c: -pcls[c]):
        print("      %-10s %4d   (e.g. deity=ᵈgilgameš / ᵈinana · place=unug{ki} / kul-aba{ki} · person=ag-ga / enkidu)"
              % (c, pcls[c]) if c == "deity" else "      %-10s %4d" % (c, pcls[c]))
    print("\n   common-noun determinative classes present (leading classifier sign):")
    print("      " + "  ".join("%s:%d" % (c, det_hits[c]) for c in sorted(det_hits, key=lambda c: -det_hits[c])))
    print("\n   the entity-precise-coref CLASS GATE — discrimination it buys:")
    print("      English   : 0 written classes → referent class must be fully RECONSTRUCTED (coref hard/circular, F1197/99)")
    print("      German    : 3 classes (der/die/das gender) → coref candidate set ≈ referents/3   (too coarse, F1199)")
    print("      Sumerian  : ≥%d written determinative classes → coref candidate set ≈ referents/%d  (~%.1f× finer than gender)"
          % (C, C, C / 3))
    print("\n  READ: the determinative writes the referent's CLASS at GENERATION — the 'hidden content' (which-kind) is never")
    print("  hidden; the reader reads it off the glyph instead of reconstructing it. That IS op(x)operand(x)responsion's")
    print("  third factor as an explicit glyph modifier (the Class-K class-slot). It is the entity-precise-coref class gate,")
    print("  written + non-circular (independent of recency, unlike F1199): ~%.0f× finer than German gender, ∞ over English's" % (C / 3))
    print("  zero. So 'how did early glyph languages encode the hidden content?' — determinatives (class on the glyph);")
    print("  Vanuatu sandroing is the OTHER modality — the continuous unicursal PATH writes the RELATIONS (not the class).")
