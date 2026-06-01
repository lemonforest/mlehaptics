"""rc6_fixes_verify_F291.py — verify srmech 0.7.0rc6 RESOLVED the UPSTREAM_NOTES §12 footguns.

rc4 logged two HD-surface asks (§12.1 loop_inv GLOBAL-not-per-block silent footgun; §12.2 no native
right-unbind for the sequence-peel). rc6 added loop_conj_hd / loop_inv_hd / loop_runbind_hd and made
the scalar loop_inv RAISE on HD input. This script checks the fixes are correct + no regression.

Checks:
  R0  no regression: native loop_bind == oracle (64 basis pairs); loop_bind_hd == research helper (err 0)
  F1  §12.1a: scalar loop_inv RAISES (fail-loud) on a len!=LOOP_DIM vector (no more silent global-conj)
  F2  §12.1b: loop_conj_hd == per-block research conj_hd (err 0)
  F3  §12.1c: loop_inv_hd == per-block conj/N (for unit blocks == conj_hd); and the natural right-peel
              loop_bind_hd(E, loop_inv_hd(c)) now recovers (the old footgun path) correctly
  F4  §12.2 : loop_runbind_hd does per-block RIGHT-division; the F290/F291 sequence-peel is now
              PURE-NATIVE and matches the old research-helper peel (loop_bind_hd(E, conj_hd(c)))

Class-K clean (Born inner products; no abs). rc6 native. Scope: algebra only; benign; bug-test record.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc import hdc                                                  # noqa: E402  rc6 native
from loop_bind_hd_gate import loop_bind_hd as helper_bind, conj_hd, rand_unit_blocks, D, BS, NB  # noqa: E402
import loop_bind_moufang as oracle                                          # noqa: E402


def nrm(v):
    return float(np.dot(v, v)) ** 0.5      # Born norm, no abs


def main():
    import srmech
    print(f"=== rc6 ({srmech.__version__}) — verify UPSTREAM §12 fixes (D={D}, BS={BS}, NB={NB}) ===\n")
    rng = np.random.default_rng(606)
    a, b, c = (rand_unit_blocks(rng) for _ in range(3))

    # R0 — no regression
    e = oracle.e
    me = max(nrm(np.asarray(hdc.loop_bind(e(i), e(j)), float) - np.asarray(oracle.loop_bind(e(i), e(j)), float))
             for i in range(BS) for j in range(BS))
    reg = nrm(hdc.loop_bind_hd(a, b) - helper_bind(a, b))
    print(f"[R0] native loop_bind == oracle (64 pairs): max err {me:.2e}; loop_bind_hd == helper: err {reg:.2e}  "
          f"-> {'NO REGRESSION' if me < 1e-12 and reg < 1e-12 else 'REGRESSION!'}")

    # F1 — §12.1a: scalar loop_inv RAISES on HD (fail-loud), no more silent global-conj
    try:
        hdc.loop_inv(c)            # c is a 2048-vec
        f1 = "DID NOT RAISE (footgun NOT fixed)"
    except Exception as ex:
        f1 = f"RAISES {type(ex).__name__} (fail-loud) — footgun fixed"
    print(f"[F1 §12.1a] scalar loop_inv on HD input: {f1}")

    # F2 — §12.1b: loop_conj_hd == per-block research conj_hd
    f2 = nrm(hdc.loop_conj_hd(c) - conj_hd(c))
    print(f"[F2 §12.1b] loop_conj_hd == research conj_hd (per-block): err {f2:.2e}  -> {'OK' if f2 < 1e-12 else 'MISMATCH'}")

    # F3 — §12.1c: loop_inv_hd per-block (unit blocks -> == conj_hd); and the natural right-peel works
    f3a = nrm(hdc.loop_inv_hd(c) - conj_hd(c))          # unit blocks: inverse == conjugate
    E = hdc.loop_bind_hd(hdc.loop_bind_hd(a, b), c)     # left-fold ((a.b).c)
    ab_true = hdc.loop_bind_hd(a, b)
    f3b = nrm(hdc.loop_bind_hd(E, hdc.loop_inv_hd(c)) - ab_true)   # the OLD footgun path, now correct
    print(f"[F3 §12.1c] loop_inv_hd == conj_hd on unit blocks: err {f3a:.2e}; "
          f"natural right-peel loop_bind_hd(E, loop_inv_hd(c)) recovers a.b: err {f3b:.2e}  "
          f"-> {'OK (footgun path fixed)' if f3a < 1e-12 and f3b < 1e-9 else 'FAIL'}")

    # F4 — §12.2: loop_runbind_hd right-division; the F290/F291 sequence-peel is now PURE-NATIVE.
    # Determine the arg convention empirically: which of runbind(c,E) / runbind(E,c) recovers a.b?
    r_cE = hdc.loop_runbind_hd(c, E)
    r_Ec = hdc.loop_runbind_hd(E, c)
    err_cE, err_Ec = nrm(r_cE - ab_true), nrm(r_Ec - ab_true)
    which = "loop_runbind_hd(c, E)" if err_cE < err_Ec else "loop_runbind_hd(E, c)"
    best = min(err_cE, err_Ec)
    print(f"[F4 §12.2 ] right-unbind peel: {which} recovers a.b: err {best:.2e}  "
          f"(runbind(c,E)={err_cE:.2e}, runbind(E,c)={err_Ec:.2e})")
    # full pure-native peel chain ((a.b).c) -> a.b -> a, and match vs the old research-helper peel
    peel1 = hdc.loop_runbind_hd(c, E) if err_cE < err_Ec else hdc.loop_runbind_hd(E, c)
    peel2 = hdc.loop_runbind_hd(b, peel1) if err_cE < err_Ec else hdc.loop_runbind_hd(peel1, b)
    chain_err = nrm(peel2 - a)
    helper_peel = helper_bind(E, conj_hd(c))            # the old research-helper right-peel
    match_helper = nrm(peel1 - helper_peel)
    print(f"[F4 §12.2 ] pure-native peel chain ((a.b).c)->a: err {chain_err:.2e}; "
          f"matches old research-helper peel: err {match_helper:.2e}")
    print(f"  -> the F290/F291 order-aware sequence store PEEL is now PURE-NATIVE (no research conj_hd needed).")

    ok = (me < 1e-12 and reg < 1e-12 and "fixed" in f1 and f2 < 1e-12 and f3a < 1e-12
          and f3b < 1e-9 and best < 1e-9 and chain_err < 1e-9)
    print(f"\n  === rc6 §12 fixes: {'ALL RESOLVED, no regression' if ok else 'CHECK FAILURES ABOVE'} ===")


if __name__ == "__main__":
    main()
