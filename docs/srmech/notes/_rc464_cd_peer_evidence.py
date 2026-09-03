"""rc464 (`#T1188`) — the EXECUTED evidence behind the CHANGELOG's dim-128/256
table for `srmech_cd_navmap` / `srmech_cd_navigate` /
`srmech_cd_navmap_is_signed_permutation`.

Committed as provenance, not as a test: it calls the C peers through RAW
ctypes, deliberately bypassing the three `_native` wrappers, because at rc463
those wrappers carried a `dim > 64 -> return None` domain predicate in front of
peers whose own `cdr_dim_ok` (c/src/srmech_cd_register.c:67-74) has admitted
every power of two up to SRMECH_CD_MAX_DIM = 256 since rc298. The point of the
script is to show that the peer answers where the wrapper declined; a test
written against the wrappers could not have shown that, which is precisely why
the defect survived from rc298 to rc463.

Run it from `docs/srmech/python` under WSL2 AFTER a rebuild:

    cmake --build build -- -k && cp build/libsrmech.so \
        python/srmech/_native/libsrmech.so && cd python && \
        python3 ../notes/_rc464_cd_peer_evidence.py

Recorded run (rc464, libsrmech.so built 2026-09-02, ABI 24, HAS_NATIVE True,
numpy ABSENT):

    navmap   dim=128 j in {0,1,127}      rc=SRMECH_OK  128 rows each  0 mismatches
    navmap   dim=256 j in {0,1,127,255}  rc=SRMECH_OK  256 rows each  0 mismatches
    navigate dim=128 j in {0,1,127}      rc=SRMECH_OK    4 recs each  0 mismatches
    navigate dim=256 j in {0,1,127,255}  rc=SRMECH_OK    4 recs each  0 mismatches
    is_signed_permutation dim=128 -> True   1.281 ms  (16,384 cocycle calls)
    is_signed_permutation dim=256 -> True   5.212 ms  (65,536 cocycle calls)
    cd_navmap_c(128, 1)                     -> None    (the rc463 guard)
    cd_navigate_c(256, 1, [0], [1])         -> None    (the rc463 guard)
    cd_navmap_is_signed_permutation_c(256)  -> None    (the rc463 guard)

The three `-> None` lines are the rc463 behaviour and are what rc464 removed;
re-running this script on an rc464-or-later tree prints real values there.

No numpy. No `abs()`: the sign a navigate record carries is composed
multiplicatively (Class-K pin-slot phase boundary composed with the Class-C
reorientation), never dropped and re-applied.
"""

import ctypes
import sys
import time
from pathlib import Path

# The script lives in docs/srmech/notes/ but the package lives in
# docs/srmech/python/; running it by path puts sys.path[0] on notes/, so point
# it at the tree explicitly rather than relying on the caller's cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import srmech
import srmech._native as N
from srmech.cascade import cayley_dickson as CDK

SRMECH_OK = 0
JS = (0, 1, 127, 255)


def main() -> int:
    print("srmech.__file__      :", srmech.__file__)
    print("srmech.__version__   :", srmech.__version__)
    print("HAS_NATIVE           :", N.HAS_NATIVE)
    print("NATIVE_ABI_VERSION   :", N.NATIVE_ABI_VERSION)
    print("EXPECTED_ABI_VERSION :", N.EXPECTED_ABI_VERSION)
    print("LOAD_ERROR           :", N.LOAD_ERROR)
    if not N.HAS_NATIVE or N.LIB is None:
        print("no native library — nothing to measure")
        return 1
    lib = N.LIB
    print()

    for dim in (128, 256):
        js = [j for j in JS if j < dim]
        for j in js:
            dest = (ctypes.c_int * dim)()
            sign = (ctypes.c_int * dim)()
            rc = lib.srmech_cd_navmap(
                ctypes.c_int(dim), ctypes.c_int(j), dest, sign)
            assert rc == SRMECH_OK, (dim, j, rc)
            bad = sum(
                1 for i in range(dim)
                if (int(dest[i]), int(sign[i])) != CDK.cd_basis_product(dim, i, j))
            print(f"navmap   dim={dim:3d} j={j:3d} rc={rc} rows={dim} "
                  f"mismatches={bad}")
            assert bad == 0

        for j in js:
            in_slots = [0, 1, dim // 2, dim - 1]
            in_signs = [1, -1, 1, -1]
            cnt = len(in_slots)
            isl = (ctypes.c_int * cnt)(*in_slots)
            isg = (ctypes.c_int * cnt)(*in_signs)
            osl = (ctypes.c_int * cnt)()
            osg = (ctypes.c_int * cnt)()
            rc = lib.srmech_cd_navigate(
                ctypes.c_int(dim), ctypes.c_int(j), isl, isg,
                ctypes.c_size_t(cnt), osl, osg)
            assert rc == SRMECH_OK, (dim, j, rc)
            bad = 0
            for m in range(cnt):
                pi, ps = CDK.cd_basis_product(dim, in_slots[m], j)
                # Class-K pin-slot phase boundary composed with the incoming
                # Class-C orientation — a product, never an abs().
                if (int(osl[m]), int(osg[m])) != (pi, ps * in_signs[m]):
                    bad += 1
            print(f"navigate dim={dim:3d} j={j:3d} rc={rc} recs={cnt} "
                  f"mismatches={bad}")
            assert bad == 0

    for dim in (128, 256):
        out_ok = ctypes.c_int(-1)
        t0 = time.perf_counter()
        rc = lib.srmech_cd_navmap_is_signed_permutation(
            ctypes.c_int(dim), ctypes.byref(out_ok))
        dt = time.perf_counter() - t0
        print(f"is_signed_permutation dim={dim:3d} rc={rc} "
              f"value={bool(out_ok.value)} wall={dt * 1000:.3f} ms  "
              f"({dim * dim} cocycle calls)")
        assert rc == SRMECH_OK

    print()
    print("through the PUBLIC wrappers (None on an rc463 tree, real values on rc464+):")
    print("  cd_navmap_c(128, 1)                    ->",
          "None" if N.cd_navmap_c(128, 1) is None else "dict of 128")
    print("  cd_navigate_c(256, 1, [0], [1])        ->",
          N.cd_navigate_c(256, 1, [0], [1]))
    print("  cd_navmap_is_signed_permutation_c(256) ->",
          N.cd_navmap_is_signed_permutation_c(256))
    print()
    print("ALL EXECUTED CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
