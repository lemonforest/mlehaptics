"""rc4_native_hd_verify_F291.py — verify rc4's NATIVE block-octonion HD surface against
the F289 D1 anchors AND the research-side helper (loop_bind_hd_gate.py) the F291 workflow legs used.

rc4 shipped natively: hdc.{loop_bind_hd, loop_unbind_hd, loop_associator, loop_inv, loop_left_op,
loop_right_op}. This checks:
  (1) native loop_bind_hd == research-helper loop_bind_hd  (validates the legs' helper vs native)
  (2) block-diagonal: per-block of native loop_bind_hd == native dim-8 loop_bind  (F289 D1, err 0.0)
  (3) native loop_unbind_hd round-trip (LEFT-division: unbind(k, bind(k,v)) == v)
  (4) the F290 SEQUENCE PEEL (right-cancellation ((a.b).c).conj(c)=a.b): which native idiom realizes it?
      -> discover whether native loop_conj / loop_inv operate per-block on HD vectors (needed for the right-peel),
         and whether there is a GAP (no native right-unbind / conj_hd) to hand to the dev.
  (5) loop_associator == (ab)c - a(bc); loop_left_op/right_op are the L_a/R_a operators (L != R).

Class-K clean (Born inner products; no abs). rc4 native. Scope: algebra only; benign; bug-test record.
"""
import os
import sys

import numpy as np

RESEARCH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RESEARCH)
from srmech.amsc import hdc                                          # noqa: E402  rc4 native
from loop_bind_hd_gate import (loop_bind_hd as helper_bind, conj_hd, rand_unit_blocks,  # noqa: E402
                               D, BS, NB)
import loop_bind_moufang as oracle                                  # noqa: E402  dim-8 oracle


def nrm(v):
    return float(np.linalg.norm(v))


def main():
    import srmech
    print(f"=== rc4 ({srmech.__version__}) native block-octonion HD verification (D={D}, BS={BS}, NB={NB}) ===\n")
    rng = np.random.default_rng(291)
    x = rand_unit_blocks(rng); y = rand_unit_blocks(rng)

    # (1) native loop_bind_hd == research-helper loop_bind_hd
    nz = hdc.loop_bind_hd(x, y)
    hz = helper_bind(x, y)
    print(f"[1] native loop_bind_hd == research-helper loop_bind_hd : err={nrm(nz - hz):.2e}  "
          f"-> {'MATCH (legs validated vs native)' if nrm(nz - hz) < 1e-10 else 'MISMATCH!'}")

    # (2) block-diagonal: per-block == native dim-8 loop_bind (F289 D1 anchor, expect 0.0)
    blk = 7
    xb = x.reshape(NB, BS)[blk]; yb = y.reshape(NB, BS)[blk]
    per_block = hdc.loop_bind(xb, yb)
    err_bd = nrm(nz.reshape(NB, BS)[blk] - per_block)
    print(f"[2] block {blk}: native loop_bind_hd block == dim-8 loop_bind(x_blk,y_blk) : err={err_bd:.2e}  "
          f"-> {'BLOCK-DIAGONAL (direct sum, no coupling)' if err_bd < 1e-12 else 'COUPLED?!'}")

    # (3) native loop_unbind_hd LEFT-division round-trip: unbind(k, bind(k,v)) == v
    k = rand_unit_blocks(rng); v = rand_unit_blocks(rng)
    bound = hdc.loop_bind_hd(k, v)
    rec = hdc.loop_unbind_hd(k, bound)
    print(f"[3] native loop_unbind_hd(k, loop_bind_hd(k,v)) == v (LEFT-division) : err={nrm(rec - v):.2e}  "
          f"-> {'ROUND-TRIP OK' if nrm(rec - v) < 1e-9 else 'FAIL'}")

    # (4) the F290 SEQUENCE PEEL = right-cancellation. E = (a.b).c ; want a.b = E . conj(c).
    a = rand_unit_blocks(rng); b = rand_unit_blocks(rng); c = rand_unit_blocks(rng)
    E = hdc.loop_bind_hd(hdc.loop_bind_hd(a, b), c)
    ab_true = hdc.loop_bind_hd(a, b)

    # 4a. does native loop_conj operate PER-BLOCK on an HD vector? (needed to build conj(c) for the right-peel)
    try:
        cc_native = hdc.loop_conj(c)
        per_block_conj_ok = (cc_native.shape == c.shape) and \
            np.allclose(cc_native.reshape(NB, BS)[blk], hdc.loop_conj(c.reshape(NB, BS)[blk]), atol=1e-12)
    except Exception as ex:
        cc_native = None; per_block_conj_ok = False
        print(f"[4a] native loop_conj on HD vector: RAISED {type(ex).__name__}: {ex}")
    if cc_native is not None:
        print(f"[4a] native loop_conj operates per-block on HD (len {len(c)}): {per_block_conj_ok}")

    # 4b. does native loop_inv operate per-block on HD?
    try:
        ci_native = hdc.loop_inv(c)
        inv_hd_ok = (ci_native.shape == c.shape)
    except Exception as ex:
        ci_native = None; inv_hd_ok = False
        print(f"[4b] native loop_inv on HD vector: RAISED {type(ex).__name__}: {ex}")
    if ci_native is not None:
        print(f"[4b] native loop_inv returns HD-shaped output (len {len(c)}): {inv_hd_ok}  "
              f"(NB: shape only — value is GLOBAL not per-block, see [4f])")

    # 4c. the right-peel via the research conj_hd (always available) — confirm F290 peel still holds on rc4 native bind
    ab_peeled_helper = hdc.loop_bind_hd(E, conj_hd(c))
    print(f"[4c] F290 right-peel via research conj_hd: E.conj(c) recovers a.b : err={nrm(ab_peeled_helper - ab_true):.2e}")

    # 4d. the right-peel via NATIVE conj (if per-block) — is there a pure-native right-peel?
    if per_block_conj_ok:
        ab_peeled_native = hdc.loop_bind_hd(E, cc_native)
        print(f"[4d] F290 right-peel via NATIVE loop_conj: E.conj(c) recovers a.b : err={nrm(ab_peeled_native - ab_true):.2e}  -> pure-native right-peel AVAILABLE")
    else:
        print(f"[4d] GAP: native loop_conj is NOT per-block on HD -> no pure-native RIGHT-unbind (sequence peel). "
              f"native loop_unbind_hd is LEFT-division only. -> upstream note: add loop_conj_hd / loop_runbind_hd.")

    # 4e. confirm native loop_unbind_hd is the WRONG side for the right-peel (left-division != right-peel)
    wrong = hdc.loop_unbind_hd(c, E)   # = conj(c).E  (LEFT) -- should NOT equal a.b
    print(f"[4e] sanity: loop_unbind_hd(c,E)=conj(c).E (LEFT) vs a.b : err={nrm(wrong - ab_true):.2e}  "
          f"-> {'as expected, LEFT-div != right-peel' if nrm(wrong - ab_true) > 1e-3 else 'unexpected'}")

    # 4f. FOOTGUN: loop_inv is GLOBAL on HD input (whole-vector-as-one-object), NOT per-block.
    #     loop_bind_hd/loop_unbind_hd ARE per-block, so loop_bind_hd(E, loop_inv(c)) (the natural
    #     right-peel) is SILENTLY WRONG. Document precisely for the dev (UPSTREAM_NOTES).
    li = hdc.loop_inv(c)
    gconj = c.copy(); gconj[1:] *= -1                       # global conj
    err_global = nrm(li - gconj / float(np.dot(c, c)))       # global conj / global norm
    err_perblk = nrm(li - conj_hd(c))                        # per-block conj (the correct HD inverse, unit blocks)
    print(f"[4f] loop_inv(HD) == GLOBAL conj/N : err={err_global:.2e}  ;  == per-block conj_hd : err={err_perblk:.2e}")
    print(f"     -> loop_inv is GLOBAL on HD (footgun): the natural right-peel loop_bind_hd(E, loop_inv(c)) is "
          f"SILENTLY WRONG (err {nrm(hdc.loop_bind_hd(E, li) - ab_true):.1e}). UPSTREAM: loop_inv should go per-block "
          f"or RAISE on len != LOOP_DIM; add loop_runbind_hd (right-division) for the sequence-peel.")

    # (5) loop_associator + L_a/R_a operators
    aa = oracle  # noqa
    x8 = np.zeros(8); x8[1] = 1.0
    y8 = np.zeros(8); y8[2] = 1.0
    z8 = np.zeros(8); z8[4] = 1.0
    assoc_native = hdc.loop_associator(x8, y8, z8)
    assoc_def = hdc.loop_bind(hdc.loop_bind(x8, y8), z8) - hdc.loop_bind(x8, hdc.loop_bind(y8, z8))
    print(f"\n[5] loop_associator(x,y,z) == (xy)z-x(yz) : err={nrm(assoc_native - assoc_def):.2e}")
    La = hdc.loop_left_op(x8); Ra = hdc.loop_right_op(x8)
    # L_a(y) = a.y ; R_a(y) = y.a
    lerr = nrm(La @ y8 - hdc.loop_bind(x8, y8)); rerr = nrm(Ra @ y8 - hdc.loop_bind(y8, x8))
    print(f"[5] loop_left_op: L_a y == a.y : err={lerr:.2e} ; loop_right_op: R_a y == y.a : err={rerr:.2e}")
    print(f"[5] L_a != R_a (the (4:3)|(3:4) chirality) : ||L-R||_F={nrm(La - Ra):.3f}")


if __name__ == "__main__":
    main()
