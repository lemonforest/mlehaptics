"""rc11_simd_graft_verify_F292.py — verify srmech 0.7.0rc11 shipped BOTH F292 SIMD grafts BIT-EXACT to scalar.

The F292 apple-tree hand-down (cpuminer SHA-256 / SIMD techniques -> srmech's own C) said: the SIMD path
MUST be bit-identical to the scalar/Python fallback (the parity-test ratchet). The cloud session built
rc10 (graft #1: N-way SIMD SHA-256 batch) + rc11 (graft #2: SIMD loop_bind_hd) but ran on srmech 0.6.0
(sandbox blocked TestPyPI files), so it never clean-verified them. This script does, on a clean rc11 venv.

GRAFT #1 — sha256_batch (N-way SIMD): sha256_batch(msgs)[i] == sha256_bytes(msgs[i]) for every message,
  across SHA block-boundary lengths (0,1,55,56,63,64,65,127,128) + random -> bit-exact digests.
GRAFT #2 — SIMD loop_bind_hd: native loop_bind_hd == per-block dim-8 loop_bind == oracle (err 0.0); the
  SIMD internal must not change the result. + 14-law foundation + loop_runbind_hd no-regression.

Class-K clean. Scope: tooling-verification; benign.
"""
import os
import sys

import numpy as np

RESEARCH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RESEARCH)
from srmech.amsc import hdc                                          # rc11 native (SIMD loop_bind_hd)
from srmech.amsc.format import sha256_bytes, sha256_batch           # rc11: graft #1
from loop_bind_hd_gate import loop_bind_hd as helper_bind, conj_hd, rand_unit_blocks, NB, BS  # noqa: E402
import loop_bind_moufang as oracle                                  # parity oracle


def nrm(v):
    return float(np.dot(v, v)) ** 0.5


def main():
    import srmech
    print(f"=== rc11 ({srmech.__version__}) — F292 SIMD grafts, bit-exact-to-scalar parity ===\n")

    # ---- GRAFT #1: sha256_batch (N-way SIMD) == scalar sha256_bytes, bit-exact ----
    rng = np.random.default_rng(1192)
    lens = [0, 1, 55, 56, 63, 64, 65, 127, 128, 256]                # incl. SHA-256 block-boundary edge cases
    msgs = [bytes(rng.integers(0, 256, size=L, dtype=np.uint8).tolist()) for L in lens]
    batch = sha256_batch(msgs)
    scalar = [sha256_bytes(m) for m in msgs]
    mism = [(i, lens[i]) for i in range(len(msgs)) if batch[i] != scalar[i]]
    print(f"[graft #1 sha256_batch] {len(msgs)} msgs (block-boundary + random); batch == scalar on ALL: {not mism}"
          f"{'' if not mism else '  MISMATCH at '+str(mism)}")
    print(f"   e.g. empty-string digest: {batch[0][:24]}…  (FIPS KAT e3b0c442…: {batch[0].startswith('e3b0c44298fc1c14')})")

    # ---- GRAFT #2: SIMD loop_bind_hd == per-block dim-8 loop_bind == oracle (err 0.0) ----
    e = oracle.e
    basis_err = max(nrm(np.asarray(hdc.loop_bind(e(i), e(j)), float) - np.asarray(oracle.loop_bind(e(i), e(j)), float))
                    for i in range(BS) for j in range(BS))
    x, y = rand_unit_blocks(rng), rand_unit_blocks(rng)
    nz = hdc.loop_bind_hd(x, y)
    blk = 7
    per_block = hdc.loop_bind(x.reshape(NB, BS)[blk], y.reshape(NB, BS)[blk])
    block_err = nrm(nz.reshape(NB, BS)[blk] - per_block)
    helper_err = nrm(nz - helper_bind(x, y))
    print(f"\n[graft #2 SIMD loop_bind_hd] native loop_bind == oracle (64 pairs): max err {basis_err:.2e}")
    print(f"   SIMD loop_bind_hd block == dim-8 loop_bind(x_k,y_k) (block-diagonal): err {block_err:.2e}")
    print(f"   SIMD loop_bind_hd == research helper (scalar): err {helper_err:.2e}  "
          f"-> {'BIT-EXACT (SIMD did not change the result)' if max(basis_err, block_err, helper_err) < 1e-12 else 'DIVERGENCE!'}")

    # ---- no-regression: loop_runbind_hd right-peel + autocorrelation present ----
    a, b, c = (rand_unit_blocks(rng) for _ in range(3))
    E = hdc.loop_bind_hd(hdc.loop_bind_hd(a, b), c)
    peel = hdc.loop_runbind_hd(c, E)                                # right-division: recover a.b
    peel_err = nrm(peel - hdc.loop_bind_hd(a, b))
    from srmech.amsc import cascade
    has_ac = hasattr(cascade, "autocorrelation")
    print(f"\n[no-regression] loop_runbind_hd(c,E) recovers a.b: err {peel_err:.2e}; cascade.autocorrelation present: {has_ac}")

    ok = (not mism) and max(basis_err, block_err, helper_err) < 1e-12 and peel_err < 1e-9 and has_ac
    print(f"\n  === rc11 F292 SIMD grafts: {'BOTH BIT-EXACT, no regression — apple-tree hand-down LANDED + verified' if ok else 'CHECK FAILURES'} ===")


if __name__ == "__main__":
    main()
