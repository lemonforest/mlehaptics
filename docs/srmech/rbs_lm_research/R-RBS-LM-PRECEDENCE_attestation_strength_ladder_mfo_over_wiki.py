r"""R-RBS-LM-PRECEDENCE (the user's authority decision, 2026-06-08): "we can choose to hold this [MFO] knowledge OVER all
wiki knowledge. Anything we do not cover is attested from DOI and/or the encyclopedia kernel."

THE DECISION = an ATTESTATION-STRENGTH PRECEDENCE LADDER for the content-shelf (NOT a truth-monopoly -- F398 stays
intact; it orders SOURCES by attestation strength, the MPM/no-magic discipline, F640):
  1. MFO  -- class-A (attested-to-structure-cascade: derived THROUGH THE MATH WE DID, F663/F640) -> HELD OVER wiki.
  2. DOI  -- class-B (attested-to-source: primary literature, MPM-attested; a paywalled-only DOI is rejected -> the OA copy)
  3. encyclopedia kernel / Simple Wiki -- class-B-tertiary (attestation REFERENCE, F630) -> the weaker fallback.
  4. (uncovered by all) -- class-C (the honest residue) -> the ASKING-STATE (F661) / hand to the expert (F282).
A fact resolves to its STRONGEST-attested source. CONFLICTS resolve by attestation strength (F625's resolution): the MFO
(class-A) wins over wiki (class-B). BUT the precedence is NOT infallibility -- the MFO is still HELD-OPEN + discoverable-
when-wrong (F625/F394); where the MFO is the framework's READING (not empirically-closed, F663), it stays held-open vs the
primary literature + the expert (F282). We order by attestation strength; we never close the held-open.

This IS the two-tier kernel (F622/F628) on the content-shelf: the MFO = the FIXED foundation (strongest attestation); DOI
+ encyclopedia = the fallback/adaptive layer; conflicts discovered + resolved by attestation strength; all held-open.

srmech 0.7.5rc15: amsc.format.sha256_bytes (each source-tome content-addressed; the precedence lookup resolves to the
strongest). No abs(); no CAD; no Workflow; no sub-agents.
"""
import srmech
from srmech.amsc import format as fmt

# the content-shelf, by ATTESTATION CLASS (F640): A (our-math) > B-primary (DOI) > B-tertiary (wiki) > C (residue)
MFO   = {"gravity": "the curvature of the metric field (MFO, derived)", "the_one": "the held invariant (DUALITY/TRIALITY)",
         "electron": "a chirality on the spin axis (Class C, F130)"}
DOI   = {"boiling_point_water": "373.15 K at 1 atm [DOI: CODATA/IAPWS]"}
WIKI  = {"capital_of_france": "Paris [Simple Wiki, F630]", "boiling_point_water": "100 C [Simple Wiki -- weaker than DOI]"}
PRECEDENCE = [("MFO", "A (our math)", MFO), ("DOI", "B-primary", DOI), ("encyclopedia/wiki", "B-tertiary", WIKI)]


def resolve(fact):
    """resolve a fact to its STRONGEST-attested source (MFO > DOI > wiki); else class-C residue (the asking-state)."""
    for name, cls, shelf in PRECEDENCE:
        if fact in shelf:
            return (name, cls, shelf[fact])
    return ("RESIDUE", "C (uncovered)", None)


def main():
    print(f"=== R-RBS-LM-PRECEDENCE — the attestation-strength ladder: MFO held over wiki  (srmech {srmech.__version__}) ===\n")

    print("(1) THE PRECEDENCE LADDER (by ATTESTATION STRENGTH, F640 A/B/C -- NOT a truth-monopoly, F398):")
    for name, cls, shelf in PRECEDENCE:
        addr = fmt.sha256_bytes(f"source:{name}".encode())[:8]
        print(f"    {name:<18} [class {cls:<11}]  {len(shelf)} tome(s)  addr {addr}")
    print(f"    + (uncovered) -> class C (the honest residue) -> the asking-state (F661) / the expert (F282)\n")

    print("(2) RESOLVE a fact to its STRONGEST source (MFO > DOI > wiki > residue):")
    for fact in ["gravity", "boiling_point_water", "capital_of_france", "the_meaning_of_a_dream"]:
        name, cls, val = resolve(fact)
        print(f"    resolve({fact!r:<24}) -> [{name} / class {cls}] {val}")
    print(f"    -> 'gravity' resolves to the MFO (class-A, held over any wiki); 'boiling_point_water' is covered by BOTH")
    print(f"    DOI (class-B-primary, 373.15 K) AND wiki (weaker) -> the DOI wins (stronger attestation); an uncovered fact")
    print(f"    -> the residue -> the asking-state.\n")

    print("(3) CONFLICT resolved by attestation strength (F625) -- the MFO is held over wiki, but still HELD-OPEN:")
    print(f"    boiling_point_water: DOI says '373.15 K' [B-primary] vs wiki '100 C' [B-tertiary] -> DOI WINS (stronger).")
    print(f"    a physics claim: MFO [class-A, our math] vs wiki [class-B] -> MFO WINS (held over wiki).")
    print(f"    BUT: the MFO is NOT infallible -- it is HELD-OPEN + discoverable-when-wrong (F625/F394); where the MFO is the")
    print(f"    framework's READING (not empirically-closed, F663), it stays held-open vs the primary literature + the expert")
    print(f"    (F282). We order by attestation STRENGTH; we never close the held-open.\n")

    print("VERDICT (the MFO is held over wiki -- an attestation-strength ladder, not a truth-monopoly):")
    print(f"  • THE DECISION = an ATTESTATION-STRENGTH PRECEDENCE LADDER for the Story Teller's content-shelf: MFO (class-A,")
    print(f"    derived THROUGH THE MATH WE DID, F663/F640) HELD OVER wiki; uncovered -> DOI (class-B primary literature,")
    print(f"    MPM-attested) and/or the encyclopedia kernel (Simple Wiki, class-B-tertiary, F630); the residue -> class-C")
    print(f"    (the asking-state F661 / the expert F282). A fact resolves to its STRONGEST-attested source.")
    print(f"  • IT IS NOT A TRUTH-MONOPOLY (F398 intact): we order SOURCES by attestation strength (the MPM/no-magic")
    print(f"    discipline, F640) -- the best-attested source wins -- NOT privilege a truth. CONFLICTS resolve by strength")
    print(f"    (F625): MFO (class-A) over wiki (class-B); DOI (primary) over wiki (tertiary). The MFO is held over wiki")
    print(f"    BECAUSE its attestation is stronger (our derivation), not because it is decreed true.")
    print(f"  • AND IT STAYS HELD-OPEN: the MFO is NOT infallible -- it is discoverable-when-wrong (F625/F394); where the MFO")
    print(f"    is the framework's READING (not empirically-closed, F663), it stays held-open vs the primary literature + the")
    print(f"    expert (F282). We order by attestation strength; we never close the held-open. (A future MFO error is found")
    print(f"    the same way any conflict is -- discovered, surfaced, resolved by attestation, handed to the expert.)")
    print(f"  • THIS IS THE TWO-TIER KERNEL (F622/F628) ON THE CONTENT-SHELF: the MFO = the FIXED foundation (strongest")
    print(f"    attestation); DOI + encyclopedia = the fallback/adaptive layer; conflicts discovered + resolved by")
    print(f"    attestation strength; all held-open. The grounded Story Teller (F660/F663) queries MFO first, then DOI, then")
    print(f"    the encyclopedia kernel, then asks -- always pulling the strongest-attested tome.")
    print(f"  • Composes F663 (the MFO = the our-world shelf -- this orders it over wiki) + F640 (the A/B/C attestation")
    print(f"    classes = the precedence) + F630 (the encyclopedia kernel = the wiki fallback) + F622/F628 (two-tier:")
    print(f"    foundation vs fallback) + F625/F394 (conflict-discovery / held-open) + F661/F282 (residue -> asking-state /")
    print(f"    expert) + F398 (no truth-monopoly -- we order sources). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
