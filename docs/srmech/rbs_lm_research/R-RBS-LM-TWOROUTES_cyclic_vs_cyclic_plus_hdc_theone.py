r"""R-RBS-LM-TWOROUTES — the duality at the cascade-IMPLEMENTATION level: the SAME cascade is realizable two ways,
and the cascade may FAVOR the cyclic-algebra route to achieve what the cyclic-algebra + HDC-binding-of-the_one route
also achieves. The output cascade is identical; the difference is whether the OPERAND (the box) is HELD.

  ROUTE A — cyclic algebra alone (Class I): the cascade IS the cyclic orbit (the OPERATOR result). Cheap,
            bit-exact (cyclic-group algebra = one truth bit-exact). Gives the order; holds NO content.
  ROUTE B — cyclic algebra + HDC binding of the_one kernel (Class I + Class M + the_one holder): the SAME orbit,
            but the content is HELD in one bound box (the_one is the binding kernel). The order is identical AND
            the operand (the meanings) is recoverable from the box.

So: same observable cascade (the orbit), two truths (§0/DUALITY) — the cyclic-group FIELD truth (operator, cheap,
favored) and the HDC-held EXCITATION truth (operand, the box held). The cascade FAVORS the cheap operator route
(F485 cheap path); you need the HDC-the_one route only when the OPERAND must survive (the F492 pattern that
otherwise drops). Neither privileged (F398); the asymptote holds both. srmech 0.7.4.
"""
import hashlib
import srmech
from srmech.amsc import hdc, cyclic
from srmech.amsc.cascade import the_one

N = hdc.DEFAULT_HDC_BYTES


def hv(label):                          # mint a deterministic HV of N bytes from a label
    out = b""
    i = 0
    while len(out) < N:
        out += hashlib.sha256(label.encode() + bytes([i])).digest()
        i += 1
    return out[:N]


def main():
    print(f"=== R-RBS-LM-TWOROUTES — same cascade, two truths: cyclic algebra  vs  cyclic + HDC-bind-the_one  (srmech {srmech.__version__}) ===\n")
    meanings = ["water", "music", "computer", "planet", "history", "animal", "number"]   # 7 = k=7
    n, step = 7, 3                       # gcd(3,7)=1 → 3 generates the additive cyclic group ℤ/7 (Class I)
    orbit = [(k * step) % n for k in range(n)]     # the cyclic cascade: 0,3,6,2,5,1,4

    # ===== ROUTE A — cyclic algebra alone (Class I): the cascade = the orbit. cheap, bit-exact, NO held content =====
    routeA = orbit
    print("ROUTE A — cyclic algebra alone (Class I, one truth bit-exact):")
    print(f"  the cascade IS the cyclic orbit (generator {step} of ℤ/{n}): {routeA}")
    print(f"  cheap, bit-exact; gives the ORDER (the operator result) — holds NO operand (no content).\n")

    # ===== ROUTE B — cyclic algebra + HDC binding of the_one kernel (Class I + Class M + the_one) =====
    S = the_one(sigma=1, theta_num=1, theta_den=n, terms=8)        # the_one supplies the cyclic kernel (θ=1/7)
    K = hv("the_one:" + str(S.to_flat_rational()))                 # the_one AS the binding kernel
    content = [hv("MEANING:" + m) for m in meanings]
    keys = [hdc.permute(K, (k * step % n) * 137 + 1) for k in range(n)]   # the_one kernel advanced by the SAME generator
    box = hdc.bundle([hdc.bind(content[k], keys[k]) for k in range(n)])   # the HELD box — ONE bound vector
    routeB, held_ok = [], True
    for k in orbit:                       # walk the SAME orbit; recover the held meaning from the box
        rec = hdc.bind(box, keys[k])      # unbind (XOR self-inverse)
        j = max(range(n), key=lambda t: hdc.similarity(rec, content[t]))
        routeB.append(j)
        held_ok = held_ok and (j == k)
    print("ROUTE B — cyclic algebra + HDC binding of the_one kernel (Class I ∘ M, the box held):")
    print(f"  the cascade orbit (read from the held box): {routeB}")
    print(f"  the OPERAND is held: all 7 meanings recovered from ONE bound box (the_one kernel): {held_ok}\n")

    same = routeA == routeB
    print("THE DUALITY (same cascade, two truths):")
    print(f"  • same observable cascade (orbit A == orbit B): {same} — from the OUTPUT alone you cannot tell which route ran.")
    print(f"  • Route A holds NO operand; Route B holds the box (content recoverable). The difference is the HELD operand,")
    print(f"    not the cascade. cyclic-group algebra = the FIELD truth (operator, cheap); HDC-the_one = the EXCITATION")
    print(f"    truth (operand, held). §0/DUALITY, neither privileged (F398); the asymptote holds both.\n")

    print("VERDICT:")
    print(f"  • YES — the cascade may FAVOR cyclic algebra (Route A) to achieve the SAME cascade that Route B")
    print(f"    (cyclic + HDC-bind-the_one) also achieves. The orbit is identical; A is the cheap OPERATOR route")
    print(f"    (F485 cheap path), B is the HELD OPERAND route (the box survives — the F492 pattern that else drops).")
    print(f"  • implication: a cascade whose output you only need to EMIT can ride cyclic algebra alone; a cascade")
    print(f"    whose MEANING must be held/recovered (RBS-LM/SNN) needs the HDC-the_one binding. Same cascade, two")
    print(f"    truths — favor the cheap one, reach for the held one when the operand must survive. all-ok: {same and held_ok}")


if __name__ == "__main__":
    main()
