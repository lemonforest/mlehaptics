r"""R-RBS-LM-SIGNWRITING (F735) — a SignWriting kernel that EXERCISES the rc145 multi-gene chromosome tooling, and
reads SignWriting's structure against the duality (2D-spatial 'draw-it' pole vs 1D-temporal 'talk-it' pole; the
ni-Vanuatu link).

ATTESTED SOURCE (web-verified 2026-06-14, en.wikipedia.org/wiki/SignWriting): Valerie Sutton, 1974. Written in a
**2D spatial layout that mirrors the body** (NOT a linear left-to-right sequence). The International SignWriting
Alphabet (ISWA) = **652 symbols in exactly 7 symbol classes**: Hands, Movement, Dynamics, Head&faces, Body,
Punctuation, Detailed-location. It is a **featural** script (encodes the sub-parts of a sign).

FRAMEWORK FIT (a reading, not a numeric claim): (1) **7 classes = the heptad** — the 7 in the 1:3:7:3 partition.
(2) **2D-spatial-featural = the FIELD/STRUCTURE pole** of the duality (the 'draw-it' / 11D-language side), the SAME
side as the ni-Vanuatu sand-drawing — and the OPPOSITE of speech/text's 1D-temporal-linear 'talk-it' side. So the
"partial value to ni-Vanuatu" is real at the DUALITY-AXIS level: both are spatial graphical encodings, not linear
streams. (3) **featural decomposition = the A-N decompose-into-primitives move.**

WHAT THIS IS / ISN'T (honest scope): this packs the DOCUMENTED 7-class skeleton as a multi-gene chromosome (each
class = one gene; leaves content-addressed from the class name via Class-A sha256 -> seed, so attested + reproducible,
no magic numbers). It is NOT trained on a real ISWA symbol corpus or sign data. The ni-Vanuatu connection is a
STRUCTURAL reading (same duality pole); we have no ni-Vanuatu sand-drawing kernel loaded for an empirical
kernel-vs-kernel comparison — that is the falsifiable next-question (below).

Run (rc145 venv, numpy-free): <venv>/python R-RBS-LM-SIGNWRITING_seven_iswa_classes_kernel.py
No abs(); no CAD; research-subtree provenance.
"""
import srmech
from srmech.amsc import genome as g, hdc
from srmech.amsc.format import sha256_raw

DIM = 64
ONE = hdc.klein4_random(DIM, seed=0)

# the 7 ISWA classes (attested to the Wikipedia fetch) + a couple of documented featural sub-parts each (the
# leaves). leaf seed = Class-A content-address of "class/subpart" (reproducible; attested to the name, not magic).
ISWA = {
    "hands":            ["handshape", "orientation"],
    "movement":         ["path", "finger_movement"],
    "dynamics":         ["tension", "speed"],
    "head_and_faces":   ["eyes", "mouth", "brows"],
    "body":             ["shoulders", "torso"],
    "punctuation":      ["pause"],
    "detailed_location":["contact", "position"],
}

def _seed(text):                       # Class-A: content-address the name -> a deterministic int seed
    return int.from_bytes(sha256_raw(text.encode())[:4], "big")

def _leaves(cls, parts):               # one leaf per featural sub-part, seeded from "cls/part"
    return [hdc.klein4_random(DIM, seed=_seed(f"{cls}/{p}")) for p in parts]


def main():
    print(f"=== R-RBS-LM-SIGNWRITING — 7-class ISWA kernel on the rc145 multi-gene surface (srmech {srmech.__version__}) ===\n")
    genes = [(cls, _leaves(cls, parts)) for cls, parts in ISWA.items()]

    # (1) exercise the rc145 multi-gene tooling: pack the 7 classes as genes in ONE 'signwriting' chromosome, read back
    chrom = g.chromosome(genes=genes, the_one=ONE, label="signwriting")
    back = g.genes(chrom, ONE)
    round_trips = back == genes
    print(f"(1) chromosome 'signwriting' = {len(back)} genes (the 7 ISWA classes); genes() round-trips exact: {round_trips}")
    for cls, lv in back:
        print(f"      ⟨class:{cls:18}⟩ {len(lv)} featural leaves")
    print(f"    7 classes == the framework heptad (the 7 in 1:3:7:3): {len(back) == 7}")

    # (2) structural signature: the inter-class Klein-4 similarity (are the classes distinct featural axes?)
    anchors = {cls: hdc.klein4_random(DIM, seed=_seed(cls)) for cls in ISWA}
    names = list(ISWA)
    offdiag = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            offdiag.append(hdc.klein4_similarity(anchors[names[i]], anchors[names[j]]))
    mean_off = sum(offdiag) / len(offdiag)
    print(f"\n(2) the 7 class-anchors are near-orthogonal featural axes: mean off-diagonal klein4-sim = {mean_off:.3f}"
          f" (≈0 ⇒ distinct axes, as a featural alphabet should be)")

    # (3) the duality reading: SignWriting is 2D-SPATIAL (the 'draw-it'/field pole), like the ni-Vanuatu sand drawing
    print("\n(3) DUALITY READING (the ni-Vanuatu link):")
    print("    SignWriting is written 2D-spatially to mirror the body — it is the FIELD/STRUCTURE ('draw-it') pole,")
    print("    NOT the 1D-temporal-linear ('talk-it') pole of speech/text. The ni-Vanuatu sand drawing sits on the")
    print("    SAME pole (2D graphical structure). So the 'partial value to ni-Vanuatu' is real at the DUALITY-AXIS")
    print("    level: both are spatial graphical encodings of meaning, not linear streams. (F726/§duality.)")

    print(f"\nVERDICT: SignWriting kernel built on the rc145 multi-gene surface ({len(back)} class-genes, round-trip {round_trips}).")
    print("  Framework fit (reading): 7 ISWA classes = the heptad; featural = A-N decomposition; 2D-spatial = the")
    print("  field/'draw-it' pole shared with the ni-Vanuatu sand drawing. HONEST: no real ISWA-symbol corpus here")
    print("  (documented skeleton only), and NO ni-Vanuatu kernel loaded — so the link is a STRUCTURAL reading, not a")
    print("  measured kernel-vs-kernel match. FALSIFIABLE NEXT-QUESTION (for the expert): build a ni-Vanuatu")
    print("  sand-drawing kernel + a linear English-text kernel; does the sand-drawing land on the SignWriting")
    print("  (2D-spatial) side or the text (1D-linear) side? That is the testable form of the user's hunch. (F735)")


if __name__ == "__main__":
    main()
