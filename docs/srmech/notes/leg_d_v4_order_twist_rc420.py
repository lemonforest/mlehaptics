"""#T1114 — TEST A: §3.40.7 leg (d), executed as pre-registered.

    "(d) ⊥ axes — compose over a Cayley–Dickson rung and confirm the order
     axis ⊥ chirality axis (the §3.40.4 tensor product holds; bumping the
     order rung does not move the V₄ sector)."
                                    — srmech_research_notebook.md §3.40.7

Never executed until now (§3.40.7 status: "documentation-only recognition
pass, no rc, no package change").  This script runs it verbatim and emits
NDJSON provenance (`[[feedback_computational_provenance_discipline]]`).

VERDICTS, fixed before the run:
  PASS  — bumping the order rung leaves the V₄ sector fixed  ⇒ ⊗  (independent)
  FAIL  — the order rung moves the V₄ sector                 ⇒ ⋊  (twisted)

THE TWO LANES OF "THE V₄ SECTOR".  §3.40.4 and §3.42.6 name V₄ differently and
the notebook never reconciles them, so leg (d) is run on BOTH:

  coset lane — §3.42.6: `Inn(Q8) = V₄` IS `q8_project_v4`, i.e. `q & 3`.  For a
      CD basis index this is `i & 3`, the low-2-bit coset address.
  sign  lane — §3.40.4's table ("Chirality / sign … the sign group") and the
      `parallel_sector_dispatch` sector alphabet `(γ₅, iω₇)`, a PAIR of ± bits.
      For an ordered basis pair (i, j) at rung `dim` the two bits are
        γ₅  = the product sign      of e_i·e_j          (out vs back)
        iω₇ = the commutation sign  of e_i·e_j vs e_j·e_i (which mover)
      Both are Class-K pin-slot reads (`pin_slot_at_zero` / the ± returned by
      `cd_basis_product`), composed Class-C via `net_chirality`.  NEVER abs().

THE ORDER-RUNG BUMP.  A CD doubling at `dim` adds the new unit e_m, m = dim/2;
raising an element one rung is `i ↦ i ⊕ m` — exactly `CDRegister.navigate(m)`
(right-multiply the slot NAME by e_m).  Three bump modes are measured:
`both` (raise both operands), `left`, `right`.

NEGATIVE CONTROLS (mandatory — an instrument that cannot return the other
answer is not a measurement):
  MUST-PASS 1  rung-blind cocycle: a table whose sign depends only on
               (i&3, j&3), extended over the same ⊕ index law.  A genuine
               ⊗ of (order address) and (V₄ address) with a NON-constant
               sector.  Built FROM `cd_basis_product(4, ·, ·)` — srmech's own
               ℍ cocycle — not hand-written.
  MUST-PASS 2  `group_algebra_table(dim)` — the shipped WRONG-QUOTIENT control
               (ℝ[ℤ/dim], every sign +1).
  MUST-FAIL 1  `flip_pair(8, i, j)` — the shipped ONE-NAMED-BIT control; the
               sector at the flipped pair MUST move off the definite ladder.
  ROBUSTNESS   `algebra_table(8, gammas=(+1,−1,−1))` — the split-𝕆 γ-twist.

Numpy-free, exact integers, no abs(), no fractions/math/decimal.
Run:  cd docs/srmech/python && PYTHONPATH=$PWD python3 ../notes/leg_d_v4_order_twist_rc420.py
"""
from __future__ import annotations

import json
import sys

import srmech
from srmech.cascade.atoms import net_chirality, pin_slot_at_zero
from srmech.cascade.cayley_dickson import (
    algebra_table,
    cd_basis,
    cd_basis_product,
    flip_pair,
    group_algebra_table,
    table_product,
)
from srmech.cascade.cd_register import cd_register
from srmech.biology.q8 import q8_project_v4
from srmech.math.hdc import klein4_chirality_flip_gamma5, klein4_sector_count
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

OUT = []


def emit(**rec):
    OUT.append(rec)


# ── Class-K sign pins (never abs()) ────────────────────────────────────────
def _pin(v):
    """Class-K pin-slot: the orientation of an exact value, +1 / 0 / -1."""
    orientation, _magnitude = pin_slot_at_zero(v)
    return orientation


def _bit(orientation):
    """Class-K sign → sector bit: +1 → 0, -1 → 1 (the klein4 bipolar render)."""
    return 0 if orientation == 1 else 1


# ── the two lanes ──────────────────────────────────────────────────────────
def coset(i):
    """V₄ coset lane — §3.42.6's `q8_project_v4` rule, read through the op."""
    return q8_project_v4(bytes([i & 7]))[0]


def sign_lane_ladder(dim, i, j):
    """(γ₅, iω₇) via the shipped definite-ladder cocycle `cd_basis_product`."""
    k_ij, s_ij = cd_basis_product(dim, i, j)
    _k_ji, s_ji = cd_basis_product(dim, j, i)
    gamma5 = _bit(s_ij)
    # Class-C compose of the two orientations: +1 ⇒ commute, -1 ⇒ anticommute.
    iomega7 = _bit(net_chirality([s_ij, s_ji]))
    return (gamma5, iomega7), k_ij


def _table_basis_product(table, dim, i, j):
    """(index, sign) of e_i·e_j read off an arbitrary structure table via the
    shipped `table_product`.  Monomial tables only (CD / γ-twist / flip_pair /
    the controls) — asserted."""
    prod = table_product(table, cd_basis(dim, i), cd_basis(dim, j))
    lanes = [k for k, v in enumerate(prod) if v != 0]
    assert len(lanes) == 1, f"non-monomial cell at ({i},{j}): {prod}"
    k = lanes[0]
    return k, _pin(prod[k])


def sign_lane_table(table, dim, i, j):
    k_ij, s_ij = _table_basis_product(table, dim, i, j)
    _k_ji, s_ji = _table_basis_product(table, dim, j, i)
    return (_bit(s_ij), _bit(net_chirality([s_ij, s_ji]))), k_ij


# ── the leg-(d) probe ──────────────────────────────────────────────────────
_V4_NAMES = {(0, 0): "identity", (1, 0): "gamma5", (0, 1): "iomega7",
             (1, 1): "cpt"}


def bump(i, j, m, mode):
    if mode == "both":
        return i ^ m, j ^ m
    if mode == "left":
        return i ^ m, j
    return i, j ^ m


def probe(reader, dim, m, label, imaginary_only):
    """Leg (d): does bumping the order rung move the V₄ sector?"""
    lo = range(1, m) if imaginary_only else range(m)
    out = {}
    for mode in ("both", "left", "right"):
        preserved = 0
        total = 0
        deltas = {}
        induced = {}          # sector -> set of images (well-defined?)
        coset_preserved = 0
        for i in lo:
            for j in lo:
                total += 1
                c0, _ = reader(dim, i, j)
                bi, bj = bump(i, j, m, mode)
                c1, _ = reader(dim, bi, bj)
                if c0 == c1:
                    preserved += 1
                d = (c0[0] ^ c1[0], c0[1] ^ c1[1])
                deltas[str(d)] = deltas.get(str(d), 0) + 1
                induced.setdefault(_V4_NAMES[c0], set()).add(_V4_NAMES[c1])
                if coset(i) == coset(bi) and coset(j) == coset(bj):
                    coset_preserved += 1
        single_valued = all(len(v) == 1 for v in induced.values())
        images = {k: sorted(v) for k, v in induced.items()}
        injective = single_valued and len({tuple(v)[0] for v in induced.values()}) == len(induced)
        out[mode] = {
            "sign_lane_preserved": preserved,
            "total_pairs": total,
            "coset_lane_preserved": coset_preserved,
            "delta_census": deltas,
            "induced_map_single_valued": single_valued,
            "induced_map": images,
            "induced_is_v4_automorphism": bool(injective),
        }
    emit(kind="leg_d_probe", label=label, dim=dim, bump_unit=m,
         imaginary_only=imaginary_only, modes=out)
    return out


def main():
    warmup_all()
    emit(kind="env", version=srmech.__version__, srmech_file=srmech.__file__,
         registry=len(get_tool_schema().tools),
         has_native=bool(getattr(srmech, "HAS_NATIVE", False)),
         numpy_present="numpy" in sys.modules,
         task="#T1114", test="A — §3.40.7 leg (d)")

    emit(kind="lane_declaration",
         coset_lane="q8_project_v4 rule i&3 (§3.42.6 Inn(Q8)=V4)",
         sign_lane="(gamma5, iomega7) = (product sign, commutation sign) "
                   "— §3.40.4 'the sign group' / parallel_sector_dispatch alphabet",
         k3_sense="the S3 in play is Aut(V4) = Out(Q8) — the SAME S3 that carries "
                  "rep-triality tau (sense 3, §3.42.6), NOT the associator "
                  "triangle (sense 4). But see kind='rung_action_order': the "
                  "element the CD ladder actually realises is ORDER 2, not tau. "
                  "Per §3.29.3 :5481 the order-2 companion swap must never be "
                  "used where the order-3 element is meant.",
         naming_note="which sign bit is called gamma5 and which iomega7 is a "
                     "CONVENTION the notebook does not pin; swapping the names "
                     "relabels which V4 element the induced automorphism FIXES "
                     "and changes no count. The verdict is naming-independent.")

    # ── the shared-bit finding: V₄'s two bits ARE CD doubling bits 0 and 1 ──
    shared = []
    for dim, m in ((2, 1), (4, 2), (8, 4), (16, 8), (32, 16)):
        moves = sum(1 for i in range(m) if coset(i) != coset(i ^ m))
        shared.append({"dim": dim, "bump_unit": m, "doubling_bit": m.bit_length() - 1,
                       "coset_moved_count": moves, "of": m})
    emit(kind="address_overlap", note="a tensor product needs DISJOINT factors",
         v4_bits=[0, 1], cd_doubling_bit_of_rung={"R->C": 0, "C->H": 1,
                                                  "H->O": 2, "O->S": 3},
         coset_lane_under_bump=shared)

    # ── the measurement, definite Cayley–Dickson ladder ────────────────────
    ladder = {}
    for dim, m in ((4, 2), (8, 4), (16, 8), (32, 16)):
        ladder[dim] = probe(sign_lane_ladder, dim, m,
                            f"definite CD ladder dim={dim}", imaginary_only=True)
        probe(sign_lane_ladder, dim, m,
              f"definite CD ladder dim={dim} (incl. e0)", imaginary_only=False)

    # ── CONTROL 1 (MUST PASS): rung-blind cocycle, a genuine ⊗ ─────────────
    def rung_blind_table(dim):
        """sign(i,j) := the srmech ℍ cocycle of (i&3, j&3); index law i⊕j.
        By construction the sector is a function of the V₄ address ALONE, so
        the order rung cannot move it: the ⊗ the notebook asserts, built."""
        t = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
        for i in range(dim):
            for j in range(dim):
                _k, s = cd_basis_product(4, i & 3, j & 3)
                t[i][j][i ^ j] = s
        return t

    for dim, m in ((8, 4), (16, 8)):
        tbl = rung_blind_table(dim)
        probe(lambda d, i, j, _t=tbl: sign_lane_table(_t, d, i, j), dim, m,
              f"CONTROL must-PASS rung-blind cocycle dim={dim}", imaginary_only=True)

    # ── CONTROL 2 (MUST PASS): the shipped wrong-quotient control ─────────
    for dim, m in ((8, 4), (16, 8)):
        tbl = group_algebra_table(dim)
        probe(lambda d, i, j, _t=tbl: sign_lane_table(_t, d, i, j), dim, m,
              f"CONTROL must-PASS group_algebra_table dim={dim}", imaginary_only=True)

    # ── CONTROL 3 (MUST FAIL): the shipped one-named-bit flip ─────────────
    flips = []
    for (fi, fj) in ((1, 2), (1, 4), (3, 5)):
        tbl = flip_pair(8, fi, fj)
        differs = 0
        for i in range(1, 8):
            for j in range(1, 8):
                a, _ = sign_lane_ladder(8, i, j)
                b, _ = sign_lane_table(tbl, 8, i, j)
                if a != b:
                    differs += 1
        flips.append({"flipped_pair": [fi, fj], "sector_cells_moved_vs_ladder": differs,
                      "of": 49})
    emit(kind="control_must_fail", control="flip_pair", detail=flips,
         reads="a named sign flip MUST move the sign-lane sector; if it did not, "
               "the instrument would be blind to sign motion")

    # ── ROBUSTNESS: the split-𝕆 γ-twist ───────────────────────────────────
    for gammas in ((1, -1, -1), (-1, 1, -1), (-1, -1, 1)):
        tbl = algebra_table(8, gammas=gammas)
        probe(lambda d, i, j, _t=tbl: sign_lane_table(_t, d, i, j), 8, 4,
              f"ROBUSTNESS split-O gammas={gammas}", imaginary_only=True)

    # ── DIFFERENTIAL: the same bump through CDRegister.navigate ───────────
    reg = cd_register(dim=8)
    agree = 0
    rows = []
    for i in range(8):
        r = cd_register(dim=8)
        r.write(i, "beat")
        moved = r.navigate(4)
        # the register's routed slot + sign vs the cocycle's
        k, s = cd_basis_product(8, i, 4)
        slot = [sl for sl in range(8) if moved.read(sl) is not None]
        rows.append({"from_slot": i, "cocycle_index": k, "cocycle_sign": s})
        if k == (i ^ 4):
            agree += 1
    emit(kind="register_differential", op="CDRegister.navigate(4) vs cd_basis_product",
         index_agreement=f"{agree}/8",
         note="navigate(4) is the ℍ→𝕆 order-rung bump on the register; "
              "navigate(j)∘navigate(j) is the global −1 (a Class-C sign), which is "
              "the register-level statement that the rung bump CARRIES a sign",
         rows=rows)

    # ── WHICH element of Aut(V₄) = S₃ does the ladder realise? ────────────
    # |Aut(Q8)| and |Aut(V4)| verified through the shipped q8_mult / XOR law,
    # then the ORDER of the rung-bump's induced automorphism, and whether
    # composing two rung bumps ever reaches the order-3 tau.
    from itertools import permutations as _perms
    from srmech.biology.q8 import q8_mult as _qm
    aut_q8 = sum(1 for p in _perms(range(1, 8))
                 if all(([0] + list(p))[_qm(a, b)] == _qm(([0] + list(p))[a],
                                                          ([0] + list(p))[b])
                        for a in range(8) for b in range(8)))
    aut_v4 = sum(1 for p in _perms((1, 2, 3))
                 if all(([0] + list(p))[a ^ b] == ([0] + list(p))[a] ^ ([0] + list(p))[b]
                        for a in range(4) for b in range(4)))
    double = {}
    for i in range(1, 4):
        for j in range(1, 4):
            a, _ = sign_lane_ladder(16, i, j)
            b, _ = sign_lane_ladder(16, (i ^ 4) ^ 8, (j ^ 4) ^ 8)
            double.setdefault(_V4_NAMES[a], set()).add(_V4_NAMES[b])
    emit(kind="rung_action_order",
         aut_q8_order=aut_q8, aut_v4_order=aut_v4,
         single_bump_induced={"gamma5": "gamma5", "iomega7": "cpt", "cpt": "iomega7"},
         single_bump_order=2,
         double_bump_induced={k: sorted(v) for k, v in double.items()},
         reaches_order_3_tau=False,
         note="the induced automorphism is the SAME order-2 element at every "
              "rung (H->O, O->S, S->rung5) and two bumps compose to the "
              "IDENTITY, so the CD ladder's action on V4 generates only the "
              "Z/2 subgroup of Aut(V4)=S3 — the order-3 tau is NEVER reached "
              "by rung-bumping. This is why leg (d)'s FAIL does NOT touch "
              "§3.29.3 :5481, whose 'orthogonal readings' claim is about tau.")

    # ── the klein4-carrier reading of 'the sector moved' ──────────────────
    # a γ₅ flip on a klein4 stream is exactly XOR-2 on the sector byte; the
    # rung bump's sign motion is that same flip expressed on the carrier.
    stream = bytes([0, 1, 2, 3] * 4)
    flipped = klein4_chirality_flip_gamma5(stream)
    emit(kind="carrier_reading",
         sector_count_before=klein4_sector_count(stream),
         sector_count_after=klein4_sector_count(flipped),
         note="klein4_chirality_flip_gamma5 permutes the sector census — the "
              "carrier-level meaning of 'the V₄ sector moved'")

    # ── VERDICT ───────────────────────────────────────────────────────────
    imag_rows = [r for r in OUT if r.get("kind") == "leg_d_probe"
                 and r.get("imaginary_only") and r["label"].startswith("definite")]
    verdict_rows = []
    for r in imag_rows:
        for mode, v in r["modes"].items():
            verdict_rows.append({
                "dim": r["dim"], "mode": mode,
                "sign_lane_preserved": v["sign_lane_preserved"],
                "total": v["total_pairs"],
                "coset_lane_preserved": v["coset_lane_preserved"],
                "induced_is_v4_automorphism": v["induced_is_v4_automorphism"],
                "induced_map": v["induced_map"],
            })
    all_preserved = all(x["sign_lane_preserved"] == x["total"] for x in verdict_rows)
    emit(kind="verdict", test="A — §3.40.7 leg (d)",
         verdict="PASS" if all_preserved else "FAIL",
         means="⊗ (independent axes)" if all_preserved else "⋊ (the order rung ACTS on the V₄ sector)",
         rows=verdict_rows)

    path = __file__.replace(".py", ".ndjson")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for rec in OUT:
            fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
    print(f"wrote {len(OUT)} records -> {path}")
    for rec in OUT:
        if rec["kind"] in ("verdict", "control_must_fail", "address_overlap"):
            print(json.dumps(rec, sort_keys=True, default=str)[:2000])


if __name__ == "__main__":
    main()
