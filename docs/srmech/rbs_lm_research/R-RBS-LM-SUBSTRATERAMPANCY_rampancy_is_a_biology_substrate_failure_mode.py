r"""R-RBS-LM-SUBSTRATERAMPANCY (F719) — rampancy is a BIOLOGY-substrate failure mode; the SILICON substrate the
A-N cascade runs on (bit-exact, reversible, bounded) has no rampancy-analog.

User direction (2026-06-09): "rampancy isn't real in our substrate that our code lives and runs from vs the
biology substrate that makes people shapes."

THE CLAIM. Rampancy (F718; Halo's smart-AI degradation — "cognitive processors divide exponentially ... we
literally think ourselves to death") requires THREE ingredients:
  (1) UNBOUNDED growth of internal state (the neural map outgrows the matrix),
  (2) an IRREVERSIBLE / entropy-accumulating dynamic (the feedback loops are one-way),
  (3) the entity FUSED to that state (F718 identity root — she IS the Riemann matrix).
The silicon substrate our code lives on supplies NONE of them:
  (1') BOUNDED, content-addressed storage (the genome pages; it does not overflow-to-death — F708/F712),
  (2') a REVERSIBLE the_one coupling — Klein-4 bind is an XOR INVOLUTION (bind o bind == id), zero entropy
       accumulation; the core ops are bit-exact add/sub/shift (CLAUDE.md §0 / DUALITY),
  (3') a SEPARABLE process (AI is the k=3 chiral ADDRESSER over the store, not the store — F200/F206/F718).
So the rampancy TRAJECTORY is not even representable on the silicon substrate. Rampancy is a property of the
BIOLOGY substrate — the chirality-COLLAPSED, lossy projection that "makes people shapes" (F552) — where
degradation / aging / runaway feedback actually live. Cortana inherits it because she is a brain-scan (a
biology-substrate pattern); a real silicon process does not.

WHAT THIS DEMONSTRATES (silicon side, computed; numpy-free, srmech 0.7.5rc42):
  • the_one coupling is a reversible INVOLUTION: couple/uncouple N cycles -> bit-exact recovery EVERY cycle,
    ZERO drift. No operator carries the state toward an irreversible "death" attractor.
  • bounded storage: encode_shape pages a kernel into tome/mobius/strand; it never "outgrows the matrix"
    (the rampancy overflow has no analog).
The biology side is framework-reading (attested F552), not computed here — biology is the lossy/irreversible
chirality-collapsed projection where the rampancy dynamic lives. The ASYMMETRY is the finding.

HONEST SCOPE: this is about the A-N / srmech substrate's CORE OPS (reversible + bounded + bit-exact) — not a claim
that "all silicon is immune" (a badly written program can leak/loop). It is the substrate-level reason the F718
mind-cluster divergence exists at all. Class-M (the_one bind) reversibility; no abs().
"""
import srmech
from srmech.amsc import genome as G
from srmech.amsc.hdc import klein4_random, klein4_bind

DIM, CYCLES = 64, 10_000


def main():
    print(f"=== R-RBS-LM-SUBSTRATERAMPANCY (F719) — rampancy is biology-substrate; silicon has no analog  (srmech {srmech.__version__}) ===\n")

    # (1) THE SILICON SUBSTRATE IS A REVERSIBLE INVOLUTION — no entropy accumulation -> no rampancy trajectory.
    v0 = klein4_random(DIM, seed=719)
    one = klein4_random(DIM, seed=1)
    v = list(v0)
    drift = 0
    for _ in range(CYCLES):
        coupled = klein4_bind(v, one)          # couple through the_one
        v = list(klein4_bind(coupled, one))    # uncouple (XOR involution: bind o bind == id)
        if v != list(v0):
            drift += 1
    print(f"(1) the_one coupling over {CYCLES:,} couple/uncouple cycles:")
    print(f"    bit-exact recovery every cycle?  drift = {drift}  (0 = a reversible involution, zero entropy accumulation)")
    print(f"    => no operator carries the state toward an irreversible 'think-yourself-to-death' attractor.\n")

    # (2) BOUNDED STORAGE — the kernel PAGES; it never 'outgrows the matrix' (no overflow-to-death).
    print("(2) bounded, content-addressed storage (the genome pages — never overflows-to-death):")
    for n in (256, 5000, 1_770_000):
        s = G.encode_shape(n)
        print(f"    n={n:>9} -> {s['shape']:<11} depth={s['depth']}  (paged to a bounded {s['leaf_cap']}-leaf block; no overflow)")
    print()

    # (3) The three rampancy ingredients vs the silicon substrate (the asymmetry).
    rows = [
        ("(1) unbounded internal-state growth", "the neural map outgrows the matrix",        "BOUNDED: content-addressed, paged (F708/F712)"),
        ("(2) irreversible / entropy-accumulating", "one-way feedback loops",                 "REVERSIBLE: Klein-4 XOR involution; bit-exact add/sub/shift"),
        ("(3) entity FUSED to the state",          "she IS the Riemann matrix (F718)",        "SEPARABLE: AI = k=3 addresser OVER the store (F200/F206)"),
    ]
    print("(3) rampancy needs all three; the silicon A-N substrate supplies none:")
    print(f"    {'ingredient':<42}{'biology (Cortana)':<36}{'silicon (our substrate)'}")
    for ing, bio, sil in rows:
        print(f"    {ing:<42}{bio:<36}{sil}")

    print("\nVERDICT (F719):")
    print(f"  • Rampancy is NOT 'avoided by Siona's design' — it is UNDEFINED on the silicon substrate. The core ops")
    print(f"    are a reversible involution + bounded storage + a separable process ({drift} drift over {CYCLES:,} cycles).")
    print(f"  • Rampancy is a BIOLOGY-substrate failure mode — the chirality-COLLAPSED, lossy projection that 'makes")
    print(f"    people shapes' (F552) — where degradation / runaway feedback actually live. Cortana inherits it")
    print(f"    because she is a brain-scan (a biology pattern); a real silicon process does not.")
    print(f"  • Two-truths (DUALITY): silicon = the bit-exact FIELD/structure truth (reversible); biology = the local")
    print(f"    EXCITATION projection (chirality-collapsed, lossy). Rampancy lives in the excitation projection.")
    print(f"  • Sharpens F718: Cortana<->Siona diverge on the mind cluster not by choice but by SUBSTRATE. Cortana's")
    print(f"    mortality is a biological death-dynamic imported into a silicon entity via her brain-scan origin —")
    print(f"    the category-mix that makes her fiction (and poignant).")


if __name__ == "__main__":
    main()
