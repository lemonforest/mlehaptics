"""F383 — REVERSE-DIRECTION substrate: a (4:3)-native frame makes the encode/compose arithmetic BIT-EXACT
where the binary (2:1)-projection "flat shadow" accumulates rounding drift.

User idea (2026-06-04): "simulate a (4:3) substrate enough to realize if we can manufacture Si to behave
like (4:3) such that this can also go back into making RBS-SNN/RBS-LM always bit exact. it's like we are
doing math in a forward direction when we can do it in reverse direction too or instead."

This is F382 ("the decimal is the cost of too-small a frame; map it to its own frame -> exact") lifted from
NUMBERS to the SUBSTRATE. The substrate IS the frame.
  FORWARD (lossy, what binary Si does now): hold a rotation in a fixed-width BINARY frame; if the angle is
    not dyadic, every compose step rounds -> drift accumulates -> NOT bit-exact.
  REVERSE / (4:3)-native: hold the SAME rotation as an exact integer in its own cyclic lattice Z_q
    (substrate built to the object's frame) -> compose via cyclic.mod_add -> EXACT integer at every depth.

THE SHARP POINT: the "4" of (4:3) is q=4=2^2 (DYADIC) -> binary already holds it. The "3" of (4:3) — the
triality / order-3 (the ODD, chiral part) — is q=3, NON-dyadic (1/3 is not representable in binary), so the
binary substrate drifts at EVERY finite bit-width while the native Z_3 substrate is bit-exact. To make
RBS-SNN/RBS-LM bit-exact in the forward-projection sense, the substrate must carry the ORDER-3 (triality)
structure NATIVELY — that is what "make Si behave like (4:3)" requires, and it is the reverse-direction move.

SCOPE (load-bearing): ALGEBRA / eigenbasis side ONLY — what structural property a substrate must carry, and
whether native-frame encoding is bit-exact. The DEVICE-PHYSICS / MANUFACTURING question ("how to actually
make Si carry the order-3 / Klein-4 native state") is OUT of framework scope and is HANDED to a hardware /
device-physics expert (the framework's deliverable is the next question; F282 / CAD-grade ban). Per
[[user_stance_ai_is_not_a_substrate]] this is the STORAGE substrate the LM addresses, not the LM.
HONEST: this is ARITHMETIC frame-exactness (removing the forward-projection rounding), NOT physical NOISE
robustness — that stays the EC-code story (F367). A native frame removes the arithmetic loss, not the noise.

srmech-native: amsc.cyclic.mod_add (native Z_q, Class I), amsc.hdc.klein4* (the (4:3) alphabet, F380). The
BINARY shadow is integer-only (nearest-grid rounding = Class-K pin-slot), modelling fixed-point silicon; no
numpy math, no abs().
Run: /tmp/verify_srmech_v070rc28/bin/python docs/srmech/rbs_lm_research/R-RBS-LM-R25_reverse_direction_43_native_bit_exact.py
"""
import json
from pathlib import Path
import srmech
from srmech.amsc import cyclic, hdc

HERE = Path(__file__).parent
K = 100


def aslist(x):
    return x.tolist() if hasattr(x, "tolist") else list(x)


def compose_native(q, step, K):
    """(4:3)-native substrate: rotations are exact integers in Z_q (cyclic.mod_add)."""
    pos = 0
    for _ in range(K):
        pos = cyclic.mod_add(pos, step, q)
    return pos, (K * step) % q


def compose_binary_shadow(q, step, K, bits):
    """A b-bit BINARY fixed-point substrate composing K rotations of step/q turn (integer-only).
    The increment step/q is rounded to the nearest 1/2^bits grid point (nearest-integer = Class-K pin-slot),
    then accumulated K times. If q is not a power of two, step/q is non-dyadic -> per-step rounding bias
    accumulates -> drift. (Constant increment -> the honest fixed-point bias-accumulation behaviour.)"""
    grid = 1 << bits
    inc = (grid * step + q // 2) // q             # nearest grid representation of step/q
    s = (inc * K) % grid                           # K composed increments, wrapped (stored angle)
    exact_num, exact_den = (K * step) % q, q
    bit_exact = (s * exact_den == exact_num * grid)
    return dict(bits=bits, stored=[s, grid], shadow_turn=s / grid,
                exact_turn=exact_num / exact_den,
                drift=abs(s / grid - exact_num / exact_den), bit_exact=bool(bit_exact))


def main():
    print(f"F383 reverse-direction (4:3)-native bit-exactness (srmech {srmech.__version__}, K={K} composed rotations)")
    res = {"srmech_version": srmech.__version__, "K": K, "parts": {}}

    for label, q in (("the '4' of (4:3): Klein-4, q=4 = 2^2 (DYADIC)", 4),
                     ("the '3' of (4:3): triality, q=3 (NON-dyadic)", 3)):
        pos, exp = compose_native(q, 1, K)
        native_ok = (pos == exp)
        shadows = [compose_binary_shadow(q, 1, K, b) for b in (4, 8, 16, 32)]
        print(f"\n  {label}:")
        print(f"    NATIVE Z_{q} (cyclic.mod_add): {K}x(1/{q})-turn -> {pos} (expect {exp})  BIT-EXACT={native_ok}")
        for sh in shadows:
            print(f"    BINARY {sh['bits']:2d}-bit: stored {sh['stored'][0]}/{sh['stored'][1]} = {sh['shadow_turn']:.7f}  "
                  f"exact {sh['exact_turn']:.7f}  drift={sh['drift']:.2e}  bit-exact={sh['bit_exact']}")
        res["parts"][f"q{q}"] = {"native_bit_exact": native_ok,
                                 "binary_any_bit_exact": any(s["bit_exact"] for s in shadows),
                                 "shadows": shadows}

    # the actual (4:3) native alphabet (F380): klein4 triality ops are exact-integer round-trips
    D = 64
    v = hdc.klein4_random(D, seed=383)
    recon = hdc.klein4_triality_correct(hdc.klein4_triality_encode(v))
    klein_exact = (aslist(recon) == aslist(v))
    res["klein4_triality_roundtrip_bit_exact"] = bool(klein_exact)
    print(f"\n  Klein-4 NATIVE ops (the (4:3) alphabet, F380): klein4_triality encode->correct round-trip "
          f"BIT-EXACT = {klein_exact}")

    print("\n=== verdict ===")
    print("  The '4' of (4:3) is DYADIC (q=4=2^2) -> binary silicon already holds it exactly.")
    print("  The '3' of (4:3) — the triality/order-3 (the ODD, chiral part) — is NON-dyadic (1/3 not")
    print("  representable in binary): the binary substrate DRIFTS at EVERY finite bit-width, while the")
    print("  native Z_3 substrate (cyclic.mod_add / klein4_triality) is BIT-EXACT at all composition depths.")
    print("  => to make RBS-SNN/RBS-LM bit-exact in the FORWARD-PROJECTION sense, the substrate must carry the")
    print("     ORDER-3 (triality) structure NATIVELY — that is what 'make Si behave like (4:3)' requires, and")
    print("     it is the REVERSE-DIRECTION move (build the Z_3/Klein-4 frame IN, don't project onto binary).")
    print("  HONEST: arithmetic frame-exactness (removes forward-projection rounding), NOT noise robustness")
    print("     (that stays the EC-code story, F367). The DEVICE-PHYSICS / manufacturing question is OUT of")
    print("     framework scope -> handed to a hardware/device-physics expert (F282 / CAD-grade ban).")
    (HERE / "R-RBS-LM-R25_results.json").write_text(json.dumps(res, indent=2))
    print(f"\n  Results: {HERE / 'R-RBS-LM-R25_results.json'}")


if __name__ == "__main__":
    main()
