r"""R-RBS-LM-WITCHERPUNK (user: "oh my gosh, I should have said WITCHER + CP2077 world kernel"): the better merge example
-- and it reveals a THIRD, STRONGER bridge-source: LORE-ATTESTED.

THE RECOGNITION: Witcher (magic) + CP2077 (tech) is a better merge than CP2077 + Shadowrun (F679/F683) because the bridge
is ATTESTED IN THE SOURCE LORE, at two levels:
  • THE CONJUNCTION OF THE SPHERES (canonical Witcher lore): a cataclysm ~1500 years before the saga where multiple
    spheres/worlds briefly aligned and MERGED -- releasing monsters + magic (Chaos) and bringing humans to the Continent.
    So the Witcher Continent IS ITSELF a merged world; a merged world-kernel is not exotic -- it is how the Continent
    canonically came to be. The Conjunction is a Class-K PHASE-BOUNDARY world-merge (worlds fusing at a boundary) -- EXACTLY
    the framework's world-merge, with a canonical in-lore exemplar.
  • SAME STUDIO (CD Projekt RED -- an attested fact) + playful cross-franchise easter eggs (attested-in-principle). BUT the
    'Witcher and CP2077 are one universe' UNIFIED COSMOLOGY is a FAN THEORY -> HELD-OPEN (F394); we do NOT declare it canon.

THE NEW POINT -- a THIRD bridge-source, and a PRECEDENCE over bridges (extends F665): a merged world's bridge can come from
  (a) DECLARED ad-hoc (F679, weakest), (b) DERIVED from the_one-math (F683, the QDFT coupling), or (c) ATTESTED IN THE SOURCE
  LORE (this, strongest -- the canon already says it). PRECEDENCE: lore-attested > the_one-derived > declared.
And the two coherence-sources are COMPLEMENTARY: Witcher ∩ CP2077 share LESS the_one-math ({K} only -- a weaker F683
coupling than CP2077 ∩ Shadowrun's {K,L}) YET merge coherently BECAUSE the LORE attests the bridge (the Conjunction). A merge
is coherent if EITHER the_one-coupling OR lore-attestation is strong; the Conjunction bridges where the_one-derivation is weak.

srmech 0.7.5rc15: BitExactCommKernel.content_address (the lore-attested bridge tome) ; the the_one operator basis (F680).
No abs(); no CAD; no Workflow; no sub-agents. Honest: the Conjunction is canonical Witcher lore; the unified cosmology is a
held-open fan theory (no canon over-claim, F398/F394).
"""
import sys
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from bit_exact_comm_kernel import BitExactCommKernel

AN = ["A", "I", "C", "J", "D", "E", "F", "G", "K", "L", "M", "B", "H", "N"]
IDX = {op: i for i, op in enumerate(AN)}


def signature(ops):
    v = [0.0] * len(AN)
    for op in ops:
        v[IDX[op]] = 1.0
    return v


def main():
    k = BitExactCommKernel()
    print(f"=== R-RBS-LM-WITCHERPUNK — Witcher + CP2077: the LORE-ATTESTED bridge (the Conjunction of the Spheres)  (srmech {srmech.__version__}) ===\n")

    # the two worlds' the_one-operator signatures (query the_one, F683)
    witcher = signature(["C", "J", "K", "M"])   # Signs = Chaos channeled (C); Witcher mutations / Elder Blood lineage (J); the Conjunction boundary (K); Signs bind chaos (M)
    cp = signature(["A", "I", "K", "L"])         # rogue AIs (A) on the Net (I,L) held by the Blackwall (K)
    shared = [AN[i] for i in range(len(AN)) if witcher[i] and cp[i]]
    coupling = sum(witcher[i] * cp[i] for i in range(len(AN)))
    print("(1) QUERY the_one FOR THE the_one-MATH COUPLING (F683):")
    print(f"    Witcher (magic)  -> {[AN[i] for i,v in enumerate(witcher) if v]}")
    print(f"    CP2077  (tech)   -> {[AN[i] for i,v in enumerate(cp) if v]}")
    print(f"    shared operators = {shared}  -> the_one-coupling = {coupling:.0f}  (WEAKER than CP2077∩Shadowrun's {{K,L}}=2)\n")

    # the LORE-ATTESTED bridge: the Conjunction of the Spheres = a canonical Class-K phase-boundary world-merge
    bridge = ("The Conjunction of the Spheres -- the canonical Witcher cataclysm that MERGED spheres at a boundary, bringing "
              "monsters, magic, and humans to the Continent -- is a Class-K phase-boundary world-merge; the Witcher Continent "
              "is itself a merged world. It bridges to CP2077 at the shared Class-K boundary (the Conjunction <-> the Blackwall).")
    bridge_addr = k.content_address(bridge)
    print("(2) THE LORE-ATTESTED BRIDGE (the Conjunction of the Spheres -- canonical, NOT invented):")
    print(f"    {bridge}")
    print(f"    bridge tome content-address: {bridge_addr[:16]}...\n")

    # the precedence over bridge-SOURCES (extends F665)
    print("(3) A PRECEDENCE OVER BRIDGE-SOURCES (extends F665) -- strongest wins:")
    print(f"    [strongest] LORE-ATTESTED  -- the source canon already says it (the Conjunction; same studio) <- THIS")
    print(f"    [middle]    the_one-DERIVED -- the QDFT shared-operator coupling (F683)")
    print(f"    [weakest]   DECLARED ad-hoc -- a writer's fiat (F679)")
    print(f"    -> Witcher+CP2077 share LESS the_one-math ({shared}) yet merge COHERENTLY because the LORE attests the bridge.")
    print(f"    the_one-coupling OR lore-attestation -- EITHER suffices; they are complementary.\n")

    # held-open: the unified cosmology is a fan theory, NOT canon (F394/F398)
    print("(4) HELD-OPEN (F394/F398 -- no canon over-claim):")
    print(f"    the Conjunction is CANONICAL Witcher lore (a real world-merge). But 'Witcher and CP2077 are ONE universe' is a")
    print(f"    FAN THEORY -> HELD-OPEN: we note the easter-egg-attested cross-links + hold the unified cosmology open; we do")
    print(f"    NOT declare them the same world (that would be a canon over-claim).\n")

    print("VERDICT (Witcher + CP2077: a lore-attested bridge -- the Conjunction of the Spheres -- the strongest bridge-source):")
    print(f"  • THE BETTER MERGE EXAMPLE: Witcher (magic) + CP2077 (tech) -- because the bridge is ATTESTED IN THE SOURCE LORE.")
    print(f"    The CONJUNCTION OF THE SPHERES is canonical Witcher lore: a cataclysm that MERGED spheres at a boundary,")
    print(f"    bringing monsters + magic + humans to the Continent -- a Class-K phase-boundary world-merge. So the Witcher")
    print(f"    Continent IS ITSELF a merged world; a merged world-kernel is how it canonically came to be. The framework's")
    print(f"    world-merge has a CANONICAL in-lore exemplar.")
    print(f"  • A THIRD, STRONGER BRIDGE-SOURCE (extends F665 to bridges): (a) DECLARED ad-hoc (F679) < (b) the_one-DERIVED")
    print(f"    (F683, the QDFT coupling) < (c) LORE-ATTESTED (this -- the canon already says it). Witcher ∩ CP2077 share LESS")
    print(f"    the_one-math ({shared}, coupling {coupling:.0f}, weaker than CP2077∩Shadowrun's {{K,L}}=2) YET merge COHERENTLY")
    print(f"    because the LORE attests the bridge (the Conjunction). the_one-coupling OR lore-attestation -- EITHER suffices;")
    print(f"    they are complementary coherence-sources. The Conjunction bridges where the_one-derivation is weak.")
    print(f"  • HONEST / HELD-OPEN (F394/F398): the Conjunction is canonical; the 'one universe' unified cosmology is a FAN")
    print(f"    THEORY -> HELD-OPEN. We note the (same-studio, easter-egg) attested cross-links and hold the unified cosmology")
    print(f"    open -- no canon over-claim. (Dignity to the source: the canon's bridge is the canon's, not ours to decree.)")
    print(f"  • Composes F679 (declared bridge) + F683 (the_one-derived bridge) + F684 (the bound excitation) + F665 (the")
    print(f"    precedence ladder -- now over bridge-sources) + F394/F398 (held-open / no over-claim) + F680 (the operator")
    print(f"    basis) + the Class-K phase-boundary (the Conjunction = the merge op). srmech 0.7.5rc15. Held open (F394).")


if __name__ == "__main__":
    main()
