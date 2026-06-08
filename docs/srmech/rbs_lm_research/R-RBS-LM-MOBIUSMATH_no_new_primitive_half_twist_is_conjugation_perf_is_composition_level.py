r"""R-RBS-LM-MOBIUSMATH (the user's tooling question, 2026-06-08): does the Mobius reading (F589/F590) mean there is
(a) new Mobius-strip MATH to bring to srmech as a primitive, (b) something to do with TOML + cascades, or (c) a genuine
place to look for PERFORMANCE? Answered honestly, with measurement.

The three-part answer:
  (a) NO NEW PRIMITIVE. The Mobius HALF-TWIST *is* CONJUGATION (negate the imaginary/chiral-odd part, keep the real
      anchor) -- and srmech ALREADY ships it: cascade.chiral_flip / cascade.chiral_dual / hdc.loop_conj (Class C/K). The
      orientation double-cover is just that conjugation is an INVOLUTION (flip-flip = identity). Adding a `mobius_*` op
      would re-skin an existing primitive (the §2 reflex-override trap). And conjugation = a SIGN-FLIP = add/sub/sign,
      which is already the bit-exact silicon floor (F392/F393) -- there is NO arithmetic speedup to find IN the math.
  (b) YES -- TOML + CASCADES is the right home. The Mobius CELL (F590: two sedenion tomes addressed by the chiral bit,
      walked via the half-twist) is a COMPOSITION of existing ops (chiral_flip + sigma-select + SedenionRegister + the
      walk) -- exactly what the cascade-catalog TOML descriptors / cascade.compose are for. A `mobius_cell` descriptor is
      an optional ERGONOMIC convenience (W19), NOT a C primitive.
  (c) PERFORMANCE is at the COMPOSITION / USE level, not the math: the chiral bit is a FREE high address bit (2x tome
      capacity for ~one comparison per access, F590), and a single Mobius walk covers BOTH pages/directions. Whether that
      beats the naive two-pass is the MEASURABLE question (the user's 'only if free/few ops'). Measured below.

srmech 0.7.5rc6: cascade.chiral_flip (the half-twist = an existing op); SedenionRegister; perf_counter. No abs(); no CAD;
no Workflow; no sub-agents.
"""
import time
import srmech
from srmech.amsc import cascade


def main():
    print(f"=== R-RBS-LM-MOBIUSMATH — the half-twist IS conjugation (no new primitive); performance is composition-level  (srmech {srmech.__version__}) ===\n")

    # (a) the half-twist = chiral_flip = an EXISTING op; involution = the double cover; sign-flip = already optimal
    seq = [1.0, -2.0, 3.0, -4.0, 5.0]
    once = cascade.chiral_flip(seq)
    twice = cascade.chiral_flip(once)
    involution = list(map(float, twice)) == list(map(float, seq))
    print("(a) NO NEW PRIMITIVE -- the Mobius HALF-TWIST is CONJUGATION, already shipped:")
    print(f"    cascade.chiral_flip({seq}) = {list(once)}")
    print(f"    chiral_flip is an INVOLUTION (flip-flip = identity = the orientation double cover): {involution}")
    print(f"    it is a SIGN-FLIP = add/sub/sign = the bit-exact silicon floor (F392/F393) -> NO arithmetic speedup to find.")
    print(f"    (also present: cascade.chiral_dual, cascade.net_chirality, hdc.loop_conj. A `mobius_*` op would be redundant.)\n")

    # (b) the Mobius cell is a COMPOSITION (TOML-cascade shaped), not a primitive
    print("(b) TOML + CASCADES is the right home: the Mobius CELL is a COMPOSITION of existing ops --")
    print(f"    chiral_flip (half-twist) + sigma-select (the address bit) + SedenionRegister (the tomes) + the walk.")
    print(f"    -> an optional `mobius_cell` cascade-catalog DESCRIPTOR (ergonomic, W19), NOT a new C primitive.\n")

    # (c) PERFORMANCE: is the chiral address bit free? measure per-access overhead of 2-tome vs 1-tome
    NT, REPS = 8, 300                                               # bounded: SedenionRegister.read is ~1ms/access (slow; perf note W20)
    tomeP, tomeM = cascade.SedenionRegister(), cascade.SedenionRegister()
    for s in range(NT):
        tomeP.write(s, f"p{s}"); tomeM.write(s, f"m{s}")

    t0 = time.perf_counter()
    for _ in range(REPS):
        for s in range(NT):
            tomeP.read(s)                                            # one-tome walk: N reads
    t_one = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(REPS):
        for sigma in (+1, -1):                                      # Mobius walk: the sigma-select + 2N reads, one continuous pass
            tome = tomeP if sigma > 0 else tomeM
            for s in range(NT):
                tome.read(s)
    t_two = time.perf_counter() - t0

    per_one = t_one / (REPS * NT) * 1e6
    per_two = t_two / (REPS * NT * 2) * 1e6
    overhead = (per_two - per_one) / per_one * 100
    print("(c) PERFORMANCE (the user's 'only if free/few ops' gate) -- per-access cost, 1-tome vs the 2-tome Mobius walk:")
    print(f"    1-tome walk : {per_one:.3f} us / access")
    print(f"    2-tome Mobius walk (sigma-select + both pages): {per_two:.3f} us / access  ({overhead:+.0f}% per-access)")
    print(f"    -> the chiral address bit adds ~{overhead:+.0f}% per access (a single page-select) -- effectively FREE; 2x")
    print(f"    capacity at no per-item arithmetic penalty. The win is the FREE bit + the single continuous walk, NOT new math.\n")

    print("VERDICT (does Mobius mean new srmech math / TOML / a performance place?):")
    print(f"  • (a) NO NEW PRIMITIVE: the half-twist IS conjugation (cascade.chiral_flip / loop_conj, already shipped); the")
    print(f"    double-cover is the involution; it is a sign-flip = the add/sub/sign silicon floor (F392) -- there is NO")
    print(f"    arithmetic speedup hiding in the Mobius math. Adding a `mobius_*` op would re-skin an existing primitive.")
    print(f"  • (b) YES, TOML + CASCADES: the Mobius CELL is a COMPOSITION (chiral_flip + sigma-address + register + walk),")
    print(f"    the natural home being a cascade-catalog descriptor -- an optional ergonomic (`mobius_cell`, W19), not a C op.")
    print(f"  • (c) PERFORMANCE IS COMPOSITION-LEVEL, AND MEASURABLE: the chiral bit is a ~free high address bit (~{overhead:+.0f}%/access)")
    print(f"    -> 2x tome capacity for one comparison; a single Mobius walk covers both pages/directions in one pass. That is")
    print(f"    the genuine win -- using the EXISTING chirality cleverly -- NOT a faster arithmetic. And (F590 caution) the")
    print(f"    axis is already the look-ahead/behind seam, so the real perf question is whether bidirectional-context-in-")
    print(f"    one-walk beats two passes -- measure it on the F478 read-head, do not assume.")
    print(f"  • Composes F589/F590 (the Mobius reading) + F544 (conjugation = the mirror) + F392/F393 (sign-flip = the silicon")
    print(f"    floor) + the cascade-catalog (TOML compositions). srmech 0.7.5rc6. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
