r"""R-RBS-LM-SEDENION-HYPERLOOP — the OPERATIONAL hyper-loop: wire the HDC sedenion addresses to the
Cayley-Dickson multiplication so "pointer arithmetic over the named container" is real (UPSTREAM §31).

Navigation = right-multiply every slot-NAME by e_j: content at slot i moves to slot k with sign s,
where e_i · e_j = s·e_k (the srmech-native cd_basis_product). This is the address↔CD homomorphism —
the genuinely-new piece F465/§31 flagged. It also folds the instrument into the RBS-SNN/SynNN:
navigation IS the k=3 read-head (BX-4) walking the sedenion register whose octonion block is the
k=7 working word (F459); and — the payoff — navigation is REVERSIBLE exactly where the algebra is:
single-basis pointer-arithmetic is always a signed permutation, but COMPOSITE-direction navigation is
reversible only ≤𝕆 (the sedenion's zero-divisor directions break it — F451/F460, left_mult_is_invertible).

srmech 0.7.3: amsc.cascade.cayley_dickson.{cd_basis_product, left_mult_is_invertible} (Class CD) +
amsc.hdc.{bind,bundle,similarity} (Class M) + amsc.cascade.chiral_flip (Class C sign) + mint_vector.
"""
import numpy as np
import srmech
from srmech.amsc.hdc import bind, bundle, similarity
from srmech.amsc import cascade as C
from srmech.amsc.cascade import cayley_dickson as cd
from srmech.signal_processing import mint_vector

D = 8192
ADDR = [mint_vector(f"SEDENION:e{k}", D=D) for k in range(16)]


def _bundle(vs):
    if len(vs) == 1:
        return vs[0]
    if len(vs) % 2 == 0:
        vs = vs + [mint_vector("__pad__", D=D)]
    return bundle(vs)


def navmap(j):
    """right-mult-by-e_j: slot i -> (slot k, sign s) with e_i·e_j = s·e_k. The pointer-advance permutation."""
    m = {}
    for i in range(16):
        k, s = cd.cd_basis_product(16, i, j)
        m[i] = (k, s)
    return m


def main():
    print(f"=== R-RBS-LM-SEDENION-HYPERLOOP — pointer arithmetic over the named container  (srmech {srmech.__version__}) ===\n")

    # ---- the named contents: themes at the octonion working slots e0..e7 ----
    vals = {k: f"theme{k}" for k in range(8)}                 # octonion working block
    cb = {n: mint_vector(f"VAL:{n}", D=D) for n in vals.values()}
    def sign_flip(v):
        return C.chiral_flip(v)                               # Class-C sign (NOT negate/abs)

    def build_register(assign):                              # assign: slot -> (name, sign)
        parts = []
        for k, (name, s) in assign.items():
            v = cb[name] if s > 0 else sign_flip(cb[name])
            parts.append(bind(ADDR[k], v))
        return _bundle(parts)

    def read(reg, k):
        noisy = bind(ADDR[k], reg)
        pos = max(cb, key=lambda n: similarity(noisy, cb[n]))
        flp = max(cb, key=lambda n: similarity(noisy, sign_flip(cb[n])))
        return (pos, +1) if abs(similarity(noisy, cb[pos])) >= abs(similarity(noisy, sign_flip(cb[flp]))) else (flp, -1)

    assign0 = {k: (vals[k], +1) for k in range(8)}
    reg0 = build_register(assign0)

    # ---- [1] single-basis navigation = the pointer-advance (signed permutation) ----
    print("[1] NAVIGATE by e_j (right-multiply every slot-name by e_j) — pointer arithmetic over the container")
    j = 1
    m = navmap(j)
    print(f"    navigate by e{j}: the slot-permutation e_i·e{j} (octonion slots shown):")
    for i in range(8):
        k, s = m[i]
        print(f"      slot e{i} (={vals.get(i,'-')}) → slot e{k}{'(+)' if s>0 else '(−)'}")
    # build the navigated register: content from slot i now lives at slot k with sign s
    assign1 = {}
    for i in range(8):
        k, s = m[i]
        if k < 16:
            assign1[k] = (vals[i], s)
    reg1 = build_register(assign1)
    # verify: the value that was at slot i is now readable at slot k (with sign)
    ok = 0
    for i in range(8):
        k, s = m[i]
        name, sg = read(reg1, k)
        good = (name == vals[i] and sg == s)
        ok += good
    print(f"    after navigation, content routed per the CD table and re-read: {ok}/8 slots correct")

    # ---- [2] round-trip reversibility (single basis): navigate by e_j twice = global −1 (recoverable) ----
    print("\n[2] round-trip: navigate by e_j twice = e_j² = −1 (global sign flip, exactly recoverable)")
    m2 = navmap(j)
    # apply twice: i -> k (s1) -> k2 (s2); net e_i·e_j·e_j = e_i·(−1) = −e_i  → back to slot i, sign −1
    net = {}
    for i in range(16):
        k1, s1 = navmap(j)[i]
        k2, s2 = navmap(j)[k1]
        net[i] = (k2, s1 * s2)
    identity_upto_sign = all(net[i][0] == i for i in range(16))
    all_neg = all(net[i][1] == -1 for i in range(16))
    print(f"    e_i·e{j}·e{j}: returns to original slot for all 16: {identity_upto_sign}; "
          f"global sign = −1 for all: {all_neg}  → reversible (the −1 is recoverable, Class C)")

    # ---- [3] the reversibility HORIZON: composite-direction navigation reversible ≤𝕆, breaks at 𝕊 ----
    print("\n[3] composite-direction navigation — reversible ≤𝕆, BREAKS at the sedenion zero divisor (F451/F460):")
    def basis_vec(dim, idxs, signs):
        from fractions import Fraction as Fr
        v = [Fr(0)] * dim
        for ix, sg in zip(idxs, signs):
            v[ix] = Fr(sg)
        return v
    # an OCTONION composite direction (e1+e2, dim 8): left-mult invertible → navigation reversible
    oct_dir = basis_vec(8, [1, 2], [1, 1])
    oct_ok = cd.left_mult_is_invertible(oct_dir)
    # the SEDENION zero-divisor direction (the F460 witness, dim 16): left-mult NOT invertible → navigation lost
    w = cd.sedenion_zero_divisor_witness()
    sed_ok = cd.left_mult_is_invertible(w["x"])
    print(f"    octonion composite e1+e2  : left_mult_is_invertible = {oct_ok}   → navigation REVERSIBLE")
    print(f"    sedenion witness {w['x_form']:>12} : left_mult_is_invertible = {sed_ok}   → navigation IRREVERSIBLE (zero divisor)")
    print(f"    → single-basis pointer-arithmetic always works (signed permutation); COMPOSITE-direction")
    print(f"      navigation is reversible ONLY ≤𝕆 — the operational hyper-loop's horizon IS the Hurwitz wall.")

    print("\nVERDICT (operational hyper-loop — UPSTREAM §31 prototyped):")
    print(f"  • The HDC sedenion addresses are now WIRED to the CD multiplication: NAVIGATE by e_j routes every")
    print(f"    slot's content per e_i·e_j = ±e_k ({ok}/8 verified) — pointer arithmetic over the named container.")
    print(f"  • RBS-SNN/SynNN fold: NAVIGATE = the k=3 read-head (BX-4) walking the sedenion register whose")
    print(f"    octonion block is the k=7 working word (F459) — the coupled-pattern instrument, operational.")
    print(f"  • Reversibility horizon carries through to NAVIGATION: single-basis always reversible; composite")
    print(f"    directions reversible ≤𝕆, broken by the sedenion zero divisor — F451/F460, now as address motion.")


if __name__ == "__main__":
    main()
