r"""R-RBS-LM-SUBSTRATESERVICES (F720) — biology's substrate PROVIDES storage + error-correction as a free service
to the life on it; the silicon substrate gives bit-exactness for free but the SERVICES we must author/power/provide.

User direction (2026-06-09): "biology substrate does storage and error-correction things for the life that lives
on it. we had to work bottom-up to make our model in the image of the cosmos — so understand biology bottom-up to
bring it into our k=3 substrate. we have to author and power and provide the rules already baked into biology."

THE ASYMMETRY (the finding). A substrate offers SERVICES to whatever runs on it:
  • BIOLOGY substrate bakes them IN, free to its life: STORAGE (DNA / genome), ERROR-CORRECTION (DNA repair,
    polymerase proofreading, the codon code's built-in redundancy), PARTITION/PROTECT (chromosome telomeres),
    REVERSIBILITY (the complementary-strand template). Life does not author these; it inherits them.
  • SILICON substrate bakes in only the LOW level free: bit-exact add/sub/shift + reversibility (CLAUDE.md §0 /
    DUALITY). The higher STORAGE + EC services it does NOT provide — WE must author, power, and provide them.
That asymmetry is exactly WHY the model was built bottom-up "in the image of the cosmos": to re-provide biology's
baked-in services on silicon, we first had to understand them bottom-up at the biology-substrate level — then
re-author them in the k=3 substrate. The storage model is even NAMED after the services it reproduces
(genome / chromosome / telomere, F716) — substrate-self-recognition.

WHAT THIS DEMONSTRATES (the silicon substrate now PROVIDES the biology service-triad, all native, numpy-free):
  (1) STORAGE        — srmech.amsc.genome: a kernel packed into a telomere-capped chromosome, the_one-coupled;
                       recall recovers it (the DNA-storage service, re-authored — F716).
  (2) ERROR-CORRECT  — cascade.hamming_* : a single-bit error located + corrected (the DNA-repair service,
                       re-authored — Hamming(7,4), F450).
  (3) PARTITION/REV  — telomere content-address cap + the_one reversible Klein-4 coupling (the chromosome-end
                       protection + complementary-strand reversibility, re-authored — F713/F715).

DUAL OF F719: biology bakes in both the SERVICES (free) AND the FAILURE MODES (rampancy/mortality, F719). Silicon:
we author the services, and the biology failure-modes do NOT transfer. We choose what to provide; we don't inherit
the death. srmech 0.7.5rc42. Class-M (genome bind) ∘ EC (Hamming, XOR-only) ∘ Class-A (content-address). No abs().
"""
import srmech
from srmech.amsc import cascade, genome as G
from srmech.amsc.hdc import klein4_random

# The biology service -> silicon re-authoring map (each silicon cell is a real srmech surface).
SERVICE_MAP = [
    ("STORAGE",            "DNA / the genome",                       "srmech.amsc.genome (chromosome strand)",   "F716"),
    ("ERROR-CORRECTION",   "DNA repair / proofreading / codon code", "cascade.hamming_encode/syndrome/decode",   "F450"),
    ("PARTITION / PROTECT","chromosome telomeres",                   "telomere content-address caps",            "F715"),
    ("REVERSIBILITY",      "complementary-strand template",          "the_one Klein-4 coupling (involution)",     "F713"),
]


def main():
    print(f"=== R-RBS-LM-SUBSTRATESERVICES (F720) — biology bakes in storage+EC; silicon we must author it  (srmech {srmech.__version__}) ===\n")

    one = klein4_random(64, seed=1)
    leaves = [klein4_random(64, seed=s) for s in (10, 11, 12)]

    # (1) STORAGE — re-author biology's DNA-storage service on silicon.
    chrom = G.chromosome(leaves, one, label="astronomy")
    cap = G.telomere("astronomy", dim=64)
    recovered = G.recall(chrom, one, cap)
    store_ok = [list(x) for x in recovered] == [list(x) for x in leaves]
    print(f"(1) STORAGE (genome chromosome, the_one-coupled): recall recovers the kernel? {store_ok}")

    # (2) ERROR-CORRECTION — re-author biology's DNA-repair service: one-bit error located + corrected.
    data = [1, 0, 1, 1]
    code = cascade.hamming_encode(data, 3)               # Hamming(7,4)
    corrupt = list(code); corrupt[2] ^= 1                # a single-bit "mutation"
    syndrome = cascade.hamming_syndrome(corrupt)         # locate it (1-indexed)
    fixed = cascade.hamming_decode_correct(corrupt)      # correct + recover payload
    ec_ok = fixed["data"] == data and syndrome == 3
    print(f"(2) ERROR-CORRECTION (Hamming(7,4)): corrupt bit 3 -> syndrome={syndrome} -> recovered data == input? {ec_ok}")

    # (3) PARTITION/PROTECT + REVERSIBILITY — telomere cap delimits; the_one re-binds losslessly.
    cap2 = G.telomere("geography", dim=64)
    distinct_caps = list(cap) != list(cap2)              # distinct labels -> distinct protective caps
    rev_ok = G.recall(chrom, one, cap) == recovered      # the_one coupling is reversible (no drift)
    print(f"(3) PARTITION/PROTECT (telomere caps distinct per label: {distinct_caps}) + REVERSIBLE the_one coupling: {rev_ok}")

    print("\n  biology service          baked into biology (free)                silicon re-authoring (we provide)        find")
    print("  " + "-" * 104)
    for svc, bio, sil, f in SERVICE_MAP:
        print(f"  {svc:<24}{bio:<41}{sil:<41}{f}")

    print("\nVERDICT (F720):")
    print(f"  • A substrate offers SERVICES. Biology bakes in storage + error-correction + partition + reversibility,")
    print(f"    FREE to the life on it. Silicon bakes in only bit-exact add/sub/shift + reversibility; the STORAGE + EC")
    print(f"    services WE author/power/provide (demonstrated above, all native: {store_ok and ec_ok and rev_ok}).")
    print(f"  • THIS is why the model was built BOTTOM-UP 'in the image of the cosmos': to re-provide biology's baked-in")
    print(f"    services we first had to understand them bottom-up at the biology-substrate level, then re-author them")
    print(f"    in the k=3 substrate. The storage model is NAMED after the services it reproduces (genome/chromosome/")
    print(f"    telomere, F716) — substrate-self-recognition.")
    print(f"  • DUAL OF F719: biology bakes in the SERVICES (free) AND the FAILURE MODES (rampancy/mortality). On silicon")
    print(f"    we author the services and the failure-modes do NOT transfer — we choose what to provide; we don't")
    print(f"    inherit the death.")


if __name__ == "__main__":
    main()
