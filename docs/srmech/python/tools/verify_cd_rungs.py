#!/usr/bin/env python3
"""EXHAUSTIVE cross-path proof of the Cayley-Dickson address layer at every rung.

rc298 (`#933`) — the generating code behind the rung numbers quoted in the
CHANGELOG. Committed per the computational-provenance discipline: a load-bearing
count ("65536/65536 at dim 256") ships with the code that produced it.

WHAT IT PROVES, and why it is not the suite's job
-------------------------------------------------
For every basis pair (i, j) at a rung, the full exact-rational ``cd_mult`` --
an INDEPENDENT code path from the ``cd_basis_product`` cocycle the register
addresses through -- must yield exactly one nonzero coefficient, that
coefficient must be +-1, and its (index, sign) must agree with the cocycle.
That is the F1274/F1275 premise the whole N-slot address layer rides on.

The check is O(dim^2) cd_mult calls and each cd_mult is O(dim^2) rational
multiplies, so it is O(dim^4) overall:

    dim  |  pairs  |  measured wall time
     64  |   4096  |  ~35 s
    128  |  16384  |  ~2.8 min
    256  |  65536  |  ~32 min

The pytest suite ratchets the exhaustive form at dim <= 64 and a deterministic
SAMPLE at 128/256 (see tests/test_cd_rungs_rc298.py). This tool is how the
exhaustive claim at the two new rungs was actually established. Re-run it when
the cocycle, cd_mult, or CD_MAX_DIM changes:

    python3 tools/verify_cd_rungs.py            # every rung in CD_DIMS
    python3 tools/verify_cd_rungs.py 128 256    # just the named rungs

Emits NDJSON (one record per rung) on stdout per the project's NDJSON-for-new-
outputs discipline; a human summary goes to stderr. Exit 0 iff every rung passed.
"""

from __future__ import annotations

import json
import os
import sys
import time

# SHADOW GUARD. Run as `python3 tools/verify_cd_rungs.py`, sys.path[0] is
# tools/ -- NOT the package root -- so an installed srmech in site-packages
# wins over the working tree and this tool cheerfully "proves" a stale wheel.
# That actually happened while writing this file. Put the package root first,
# then say out loud which srmech answered.
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

import srmech  # noqa: E402

if os.path.dirname(os.path.dirname(os.path.abspath(srmech.__file__))) != _PKG_ROOT:
    raise SystemExit(
        f"REFUSING TO RUN: this tool lives under {_PKG_ROOT} but imported "
        f"srmech from {srmech.__file__}. A shadowed install would verify the "
        f"wrong artifact.")

from srmech.cascade.cayley_dickson import (  # noqa: E402
    CD_DIMS,
    CD_MAX_DIM,
    cd_basis,
    cd_basis_product,
    cd_mult,
)
from srmech.cascade.cd_register import (  # noqa: E402
    cd_navmap,
    cd_navmap_is_signed_permutation,
)


def verify_rung(dim: int) -> dict:
    """Exhaustively verify one rung. Returns the NDJSON record."""
    started = time.time()
    pairs = 0
    failures = []

    for i in range(dim):
        for j in range(dim):
            prod = cd_mult(cd_basis(dim, i), cd_basis(dim, j))
            nz = [(k, v) for k, v in enumerate(prod) if v != 0]
            if len(nz) != 1:
                failures.append(f"e{i}*e{j}: {len(nz)} nonzero coefficients")
                continue
            k, v = nz[0]
            if v not in (1, -1):
                failures.append(f"e{i}*e{j}: coefficient {v} is not +-1")
                continue
            if (k, v) != cd_basis_product(dim, i, j):
                failures.append(
                    f"e{i}*e{j}: cocycle {cd_basis_product(dim, i, j)} != "
                    f"full cd_mult {(k, v)}")
                continue
            pairs += 1

    # The navmap face of the same invariant: a bijection with +-1 signs for
    # EVERY direction, cross-checked against the C peer's own verdict.
    bijective = True
    for j in range(dim):
        nav = cd_navmap(dim, j)
        dests = sorted(v[0] for v in nav.values())
        if dests != list(range(dim)):
            bijective = False
            failures.append(f"navmap(dim={dim}, j={j}) is not a bijection")
        if any(v[1] not in (1, -1) for v in nav.values()):
            bijective = False
            failures.append(f"navmap(dim={dim}, j={j}) has a sign outside +-1")

    return {
        "rung": dim,
        "pairs_checked": pairs,
        "pairs_expected": dim * dim,
        "signed_permutation": cd_navmap_is_signed_permutation(dim),
        "navmap_bijective": bijective,
        "ok": pairs == dim * dim and bijective and not failures,
        "failures": failures[:20],
        "n_failures": len(failures),
        "seconds": round(time.time() - started, 3),
    }


def main(argv: list) -> int:
    print(f"srmech {srmech.__version__} from {srmech.__file__}", file=sys.stderr)
    rungs = [int(a) for a in argv[1:]] or list(CD_DIMS)
    bad = [d for d in rungs if d > CD_MAX_DIM]
    if bad:
        print(f"rungs {bad} exceed CD_MAX_DIM={CD_MAX_DIM}", file=sys.stderr)
        return 2

    all_ok = True
    for dim in rungs:
        rec = verify_rung(dim)
        all_ok = all_ok and rec["ok"]
        print(json.dumps(rec, sort_keys=True), flush=True)
        print(
            f"dim={dim:4d}  {rec['pairs_checked']}/{rec['pairs_expected']} pairs"
            f"  signed_perm={rec['signed_permutation']}"
            f"  bijective={rec['navmap_bijective']}"
            f"  {rec['seconds']:.1f}s"
            f"  {'OK' if rec['ok'] else 'FAILED'}",
            file=sys.stderr, flush=True)

    print(f"{'ALL RUNGS OK' if all_ok else 'FAILURES PRESENT'}", file=sys.stderr)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
