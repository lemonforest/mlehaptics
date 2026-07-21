#!/usr/bin/env python3
"""rc290 — the SHIPPED ONE-A14 coupling, measured against the design note.

Generating code for every number quoted in the rc290 CHANGELOG, the
``hdc.klein4_from_one`` / ``klein4_address`` / ``klein4_sector_frame``
docstrings, and the matching ``srmech.h`` blocks. Emits NDJSON on stdout.

Run it from anywhere::

    python3 docs/srmech/notes/rc290_one_a14_shipped_measure.py > out.ndjson

WHY THE PATH ASSERT BELOW EXISTS (design-note errata #5, and it bit the
design session for real). ``cwd`` wins over ``PYTHONPATH`` only for
``python3 -c`` / ``-m`` / stdin. For a script run BY PATH, ``sys.path[0]``
is the SCRIPT'S OWN DIRECTORY — and this file lives in ``notes/``, outside
the package tree. So a bare ``python3 notes/thisfile.py`` silently imports
whatever ``srmech`` is installed in user-site (the design session measured
against a stale rc224 while its worktree held rc288). This script inserts
its sibling ``../python`` at the FRONT of ``sys.path`` and then ASSERTS
which artifact it loaded, so it fails loudly rather than measuring the
wrong package.

The measured comparison against the design note is deliberately reported
as a DIFFERENCE, not a match: the shipped op folds ``content`` to a digest
before the counter loop (so the C peer needs no arena and has no ceiling),
which changes the exact bytes while leaving the statistics at the floor.
Both numbers are printed so the change is auditable rather than asserted.
"""
from __future__ import annotations

import json
import os
import sys
import zlib

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_ROOT = os.path.normpath(os.path.join(_HERE, "..", "python"))
sys.path.insert(0, _PKG_ROOT)

import srmech  # noqa: E402

_LOADED = os.path.normpath(os.path.dirname(os.path.dirname(
    os.path.abspath(srmech.__file__))))
assert _LOADED == _PKG_ROOT, (
    f"WRONG ARTIFACT: loaded srmech {srmech.__version__} from {_LOADED!r}, "
    f"expected the tree at {_PKG_ROOT!r}. Refusing to measure a stale package."
)

from srmech.amsc import _native  # noqa: E402
from srmech.amsc.cascade.one import the_one  # noqa: E402
from srmech.amsc.hdc import (  # noqa: E402
    klein4_address,
    klein4_bind,
    klein4_encode_bytes,
    klein4_expand,
    klein4_from_one,
    klein4_match_count,
    klein4_sector_frame,
)

D_GRID = 64
N_THETA = 120


def emit(rec: dict) -> None:
    sys.stdout.write(json.dumps(rec, separators=(",", ":")) + "\n")


# ── Class I: Euclid, so the theta grid carries no unreduced duplicates ──
# (the design session's first run reported 84 spurious "identical pairs"
# purely because (2,4) and (1,2) were both emitted).
def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def theta_grid(count: int) -> list[tuple[int, int]]:
    """``count`` DISTINCT reduced rationals ``theta = num/den``, den ascending."""
    seen: set[tuple[int, int]] = set()
    out: list[tuple[int, int]] = []
    den = 2
    while len(out) < count:
        for num in range(1, den):
            if gcd(num, den) != 1:
                continue
            if (num, den) in seen:
                continue
            seen.add((num, den))
            out.append((num, den))
            if len(out) >= count:
                break
        den += 1
    return out


def pairwise(vectors, D: int) -> dict:
    total = 0.0
    pairs = 0
    best = 0.0
    identical = 0
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            m = klein4_match_count(vectors[i], vectors[j])
            s = m / D
            total += s
            pairs += 1
            if s > best:
                best = s
            if m == D:
                identical += 1
    return {"pairs": pairs, "mean": round(total / pairs, 4),
            "max": round(best, 4), "identical": identical}


def main() -> None:
    emit({"measure": "environment", "srmech_version": srmech.__version__,
          "loaded_from": _LOADED, "has_native": _native.HAS_NATIVE,
          "abi": _native.NATIVE_ABI_VERSION})

    grid = theta_grid(N_THETA)

    # ── M1 · the headline: ONE-A14 across a spread theta grid ──────────
    vecs = [klein4_from_one(the_one(1, tn, td, 4), D_GRID) for tn, td in grid]
    stats = pairwise(vecs, D_GRID)
    emit({"measure": "M1_one_a14_spread_theta", "D": D_GRID,
          "n_theta": len(grid), **stats,
          "design_note_mean": 0.2491, "design_note_identical": 0,
          "drawn_incumbent_mean": 0.2498,
          "note": "F1/F3. The shipped op folds content to a digest before the "
                  "counter loop (no C arena, no ceiling), so the exact bytes "
                  "differ from the design prototype; the statistic does not."})

    # ── M2 · F2: theta CLUSTERED IN VALUE (the case that killed ONE-D4) ──
    # ONE-D4 degraded to 0.3336 / 0.4477 here because cos is continuous, so
    # nearby theta share leading base-4 digits. A Class-A address has no
    # such continuity — that is the whole point of the rejection.
    for den in (100, 1000, 100000):
        cl = [klein4_from_one(the_one(1, 1 + k, den, 4), D_GRID)
              for k in range(40)]
        s = pairwise(cl, D_GRID)
        emit({"measure": "M2_one_a14_clustered_theta", "D": D_GRID,
              "denominator": den, **s,
              "one_d4_rejected_mean": {100: 0.2747, 1000: 0.3336,
                                       100000: 0.4477}[den],
              "note": "F2. ONE-D4 was rejected on this row; ONE-A14 stays at "
                      "the floor because a content address has no continuity "
                      "in theta."})

    # ── M3 · F4: strip the sector frame -> the raw Class-A expansion ────
    one = the_one(1, 1, 4)
    v = klein4_from_one(one, D_GRID)
    stripped = klein4_bind(v, klein4_sector_frame(D_GRID))
    preimage = json.dumps(one._to_jsonable(), sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
    emit({"measure": "M3_strip_sector_frame_recovers_address",
          "D": D_GRID, "recovered": list(stripped) == list(
              klein4_address(D_GRID, preimage)),
          "note": "F4. The (1,3,7,3) frame is a falsifiable structural "
                  "invariant, not decoration — even though it is "
                  "statistically inert (M6)."})

    # ── M4 · ADR-0009: native and pure byte-identical, both projections ──
    saved = _native.HAS_NATIVE
    ok = True
    try:
        for D in (1, 7, 13, 14, 15, 64, 65, 128, 1000):
            _native.HAS_NATIVE = True
            nat_a = list(klein4_address(D, b"cat"))
            nat_f = list(klein4_sector_frame(D))
            nat_o = list(klein4_from_one(one, D))
            nat_e = list(klein4_expand(D, 42))
            _native.HAS_NATIVE = False
            ok = ok and nat_a == list(klein4_address(D, b"cat"))
            ok = ok and nat_f == list(klein4_sector_frame(D))
            ok = ok and nat_o == list(klein4_from_one(one, D))
            ok = ok and nat_e == list(klein4_expand(D, 42))
    finally:
        _native.HAS_NATIVE = saved
    emit({"measure": "M4_native_pure_byte_identical", "identical": ok,
          "ops": ["klein4_address", "klein4_sector_frame", "klein4_from_one",
                  "klein4_expand"],
          "note": "F5 / ADR-0009. Both coherency projections, D divisible and "
                  "not divisible by 14."})

    # ── M5 · F1260's teaching case: ADDRESS vs REPRESENTATION ───────────
    D2 = 8192
    a = klein4_address(D2, b"cat")
    b = klein4_address(D2, b"cats")
    c = klein4_address(D2, b"dog")
    e1 = klein4_encode_bytes(b"cat", D2)
    e2 = klein4_encode_bytes(b"cats", D2)
    emit({"measure": "M5_address_vs_representation", "D": D2,
          "address_cat_cats": round(klein4_match_count(a, b) / D2, 4),
          "address_cat_dog_control": round(klein4_match_count(a, c) / D2, 4),
          "encode_bytes_cat_cats": round(klein4_match_count(e1, e2) / D2, 4),
          "note": "The 1-char edit is INVISIBLE to the address and LOUD to "
                  "the encoder. High diffusion makes a good ADDRESS and "
                  "disqualifies it as a REPRESENTATION — same axis, opposite "
                  "requirement. This is why the regimes are separate ops."})

    # ── M6 · the sector frame is statistically INERT (honest disclosure) ─
    masked = [klein4_from_one(the_one(1, tn, td, 4), D_GRID)
              for tn, td in grid[:40]]
    frame = klein4_sector_frame(D_GRID)
    unmasked = [klein4_bind(v_, frame) for v_ in masked]
    sm, su = pairwise(masked, D_GRID), pairwise(unmasked, D_GRID)
    emit({"measure": "M6_sector_frame_is_statistically_inert",
          "masked": sm, "unmasked": su, "identical_statistics": sm == su,
          "note": "XOR-by-constant is a Hamming isometry, so the frame CANNOT "
                  "change a pairwise statistic. Carried for legibility and "
                  "attestation only — stated, not hidden."})

    # ── M7 · incompressibility is the TARGET, not a defect ──────────────
    raw = bytes(klein4_from_one(the_one(1, 1, 4), D2))
    emit({"measure": "M7_incompressible_is_correct", "D": D2,
          "zlib_bytes": len(zlib.compress(raw)),
          "ratio": round(len(zlib.compress(raw)) / D2, 4),
          "design_note_zlib_bytes": 2639, "drawn_incumbent_zlib_bytes": 2612,
          "note": "A coupling is consumed by quad_turn as a uniform XOR, and "
                  "XOR-by-constant is an isometry — so it CANNOT carry "
                  "structure into stored content whatever vector sits in the "
                  "slot. What must be short is the DESCRIPTION (three "
                  "integers), not the vector."})

    # ── M8 · F7 null result: 14-divisibility earns nothing ──────────────
    for d14, p2 in ((56, 64), (112, 128), (224, 256), (448, 512), (896, 1024)):
        row = {}
        for label, D in (("div14", d14), ("pow2", p2)):
            vs = [klein4_from_one(the_one(1, tn, td, 4), D)
                  for tn, td in grid[:40]]
            row[label] = pairwise(vs, D)
        emit({"measure": "M8_D_divisibility_null", "div14_D": d14,
              "pow2_D": p2, **row,
              "note": "F7 returns FALSE. 14 = 2*7 and 7 never divides 2^n, so "
                      "no power of two is divisible by 14 — but the partition "
                      "enters as a period-14 MASK, well-defined at every D, so "
                      "the ratio never matters. Recorded as a null result."})


if __name__ == "__main__":
    main()
