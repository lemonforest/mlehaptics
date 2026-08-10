"""#T1121 — ADJUDICATION: the 7th (order-3) lean-ISA opcode — notebook vs code.

THE CONFLICT (F208 / F220). The lean A-N ISA is the 6-instruction order-2
core (`cascade.atoms`; classes K+C only). F220: a COMPLETE ISA needs a 7th,
order-3 "triality" opcode. The two artifacts name different objects:

  notebook §3.34.3  — the 7th opcode IS `klein4_triality_cycle`
                      "(the V4-carrier sibling of the qm.triality tau engine)"
  code              — `lean_isa_seventh_primitive` presents
                      `triality_automorphism` (28x28 so(8) tau) and never
                      mentions `klein4_triality_cycle`.

PRE-REGISTERED DECISION RULE (fixed before the run):
  BOTH_TRUE_DIFFERENT_CARRIERS — if BOTH candidates measure order 3 (not 2),
      and EACH generates S3 with its own carrier's measured order-2 partner
      via the SAME presentation  < a, s | a^3 = s^2 = 1, s.a.s = a^2 >,
      and the carriers are type-disjoint (no shipped op maps one to the
      other), and every negative control returns the other answer.
  NOTEBOOK_RIGHT / CODE_RIGHT — if exactly one candidate fails its order-3
      certificate or its S3 presentation.
  NOT_RESOLVABLE — if the discriminating measurements cannot be made.

k=3 SENSE DISCIPLINE (§3.29.3 — four senses, do NOT conflate): both
candidates are declared as SENSE 3 (rep-triality S3) at two different
carriers; the run must show the resolution does NOT link sense 3 to sense 4
(the associator triangle) — negative control NC4.

NEGATIVE CONTROLS (an instrument that cannot return otherwise is not a
measurement):
  NC1 must-FAIL  V4 carrier: pair sigma with a V4 TRANSLATION (XOR flip,
                 an object the automorphism permutes, NOT an element of
                 Aut(V4)) — the S3 presentation must FAIL.
  NC2 must-FAIL  so(8) carrier: pair tau with the central involution -I28
                 (coexists, commutes) — the presentation must FAIL.
  NC3 must-REJECT the §3.29.3 "single most common triality error" (the
                 order-2 swap where the order-3 element is meant): the
                 order-3 certificate must REJECT triality_swap and the
                 measured V4 transposition.
  NC4 must-SEPARATE sense 4: the associator triangle is 0/64 at H (where
                 both S3 carriers already exist) and turns on only at O
                 (168/512) — the S3 is not the associator.

srmech ops only (klein4_triality_cycle, triality_automorphism, triality_swap,
klein4_bind, klein4 flips, cd_basis_product, cd_basis, associator, q8_mult,
q8_project_v4, atoms.pin_slot_at_zero / net_chirality / magnitude,
math.cyclic.mod_add). No abs(), no numpy/fractions/math/decimal.

Leans on the leg-(d) instrument (notes/leg_d_v4_order_twist_rc420.py) for the
CD-rung-bump-induced V4 transposition; re-measured here so this record is
self-contained.

Run:  cd docs/srmech/python && PYTHONPATH=$PWD python3 \
          ../notes/seventh_opcode_carrier_adjudication_rc420.py
"""
from __future__ import annotations

import inspect
import json
import sys
from array import array

import srmech
from srmech.cascade import associator, magnitude
from srmech.cascade.atoms import net_chirality, pin_slot_at_zero
from srmech.cascade.cayley_dickson import cd_basis, cd_basis_product
from srmech.math import hdc
from srmech.math.cyclic import mod_add
from srmech.math.hv import HV
from srmech.math.laplacian import mat_matmul, mat_norm
from srmech.math.mat import Mat
from srmech.physics.qm import triality as qt
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

OUT = []
TOL = 1e-9   # matches qt._FIX_TOL


def emit(**rec):
    OUT.append(rec)


# ── Class-K sign helpers (never abs()) ─────────────────────────────────────
def _orient(v):
    o, _m = pin_slot_at_zero(v)
    return o


def _bit(orientation):
    return 0 if orientation == 1 else 1


def _near(x, target):
    """Class-K magnitude of the deviation, compared to TOL."""
    return magnitude(x - target) < TOL


# ── permutation helpers on the 4-letter Klein alphabet (pure ints) ─────────
def compose(p, q):
    """(p o q)(x) = p(q(x)); perms as length-4 image tuples."""
    return tuple(p[q[x]] for x in range(4))


IDENT = (0, 1, 2, 3)


def perm_order(p):
    n, acc = 1, p
    while acc != IDENT:
        acc = compose(p, acc)
        n += 1
        assert n <= 24
    return n


def closure(gens):
    seen = {IDENT}
    frontier = [IDENT]
    while frontier:
        nxt = []
        for g in frontier:
            for h in gens:
                c = compose(h, g)
                if c not in seen:
                    seen.add(c)
                    nxt.append(c)
        frontier = nxt
    return seen


def order_census(group):
    census = {}
    for p in group:
        o = perm_order(p)
        census[o] = census.get(o, 0) + 1
    return census


# ── read a shipped HV op as an alphabet permutation ────────────────────────
def hv_perm(fn, **kw):
    out = fn(HV(array("B", [0, 1, 2, 3]), sectors=4), **kw)
    return tuple(out.buffer)


# ── the leg-(d) sign-lane (re-measured; credit leg_d_v4_order_twist_rc420) ─
def sign_sector(dim, i, j):
    """(gamma5, iomega7) = (product-sign bit, commutation-sign bit)."""
    _k, s_ij = cd_basis_product(dim, i, j)
    _k2, s_ji = cd_basis_product(dim, j, i)
    return (_bit(_orient(s_ij)), _bit(net_chirality([s_ij, s_ji])))


def measured_rung_transposition(dim, m):
    """The V4 map induced by the CD order-rung bump (mode 'both'), as an
    alphabet permutation (state = g5*2 + iw7; identity 0 fixed)."""
    induced = {}
    for i in range(1, m):
        for j in range(1, m):
            g0 = sign_sector(dim, i, j)
            g1 = sign_sector(dim, i ^ m, j ^ m)
            a0 = 2 * g0[0] + g0[1]
            a1 = 2 * g1[0] + g1[1]
            induced.setdefault(a0, set()).add(a1)
    assert all(len(v) == 1 for v in induced.values()), "not single-valued"
    img = {k: next(iter(v)) for k, v in induced.items()}
    img.setdefault(0, 0)                      # Aut(V4) fixes the identity
    assert sorted(img) == [0, 1, 2, 3] and sorted(img.values()) == [0, 1, 2, 3]
    return tuple(img[x] for x in range(4))


def main():
    warmup_all()
    registry = len(get_tool_schema().tools)
    emit(kind="env", version=srmech.__version__, srmech_file=srmech.__file__,
         registry=registry,
         has_native=bool(getattr(srmech, "HAS_NATIVE", False)),
         numpy_present="numpy" in sys.modules,
         task="#T1121",
         test="ADJUDICATION — the 7th (order-3) opcode: notebook vs code")
    assert registry == 598, f"registry drift: {registry}"

    # ── R1: k=3 sense declaration (§3.29.3, four senses) ──────────────────
    emit(kind="k3_sense_declaration",
         klein4_triality_cycle=(
             "SENSE 3 (rep-triality S3) at the V4-SECTOR-ALPHABET carrier: "
             "the order-3 generator of Aut(V4)=S3 (triality_s3_klein4.toml); "
             "NOT sense 1 (B/H/N operators), NOT sense 2 (3/7/1 fibers), "
             "NOT sense 4 (associator triangle)"),
         triality_automorphism=(
             "SENSE 3 (rep-triality S3) at the so(8)-ADJOINT carrier: "
             "tau = S_B.S_C, order 3, Fix(tau)=g2=14; the {8v,8s,8c} "
             "rep-permutation; same sense, different carrier"),
         cross_carrier_caveat=(
             "the identification of Aut(V4)=S3 with Out(Spin(8))=S3 is the "
             "§3.42.6 lift, notebook-tagged 'expert-to-pin'; this run "
             "measures a MATCHED S3 PRESENTATION at both carriers — evidence "
             "of a link at this junction, NEVER object-identity "
             "(FORM-not-identity ceiling)"))

    # ── R2: candidate census — the three naming sites + the strangers fact ─
    atoms_all = __import__("srmech.cascade.atoms", fromlist=["__all__"]).__all__
    par_src = inspect.getsource(
        __import__("srmech.cascade.parallel",
                   fromlist=["parallel_sector_dispatch"]))
    emit(kind="candidate_census",
         lean_isa_atoms_triality_py=list(qt._LEAN_ISA_ATOMS),
         cascade_atoms_all=list(atoms_all),
         atoms_agree=tuple(qt._LEAN_ISA_ATOMS) == tuple(atoms_all),
         parallel_refs_lean_isa_seventh=par_src.count(
             "lean_isa_seventh_primitive"),
         parallel_refs_klein4_triality_cycle=par_src.count(
             "klein4_triality_cycle"))

    # ── R3: carrier A — the V4 sector alphabet ────────────────────────────
    sigma = hv_perm(hdc.klein4_triality_cycle)
    sigma_inv = hv_perm(hdc.klein4_triality_cycle, inverse=True)
    sigma2 = compose(sigma, sigma)
    # automorphism law sigma(u XOR v) = sigma(u) XOR sigma(v), all 16 pairs,
    # through the shipped klein4_bind (bind IS the V4 group op)
    u16 = HV(array("B", [u for u in range(4) for _ in range(4)]), sectors=4)
    v16 = HV(array("B", [v for _ in range(4) for v in range(4)]), sectors=4)
    lhs = hdc.klein4_triality_cycle(hdc.klein4_bind(u16, v16))
    rhs = hdc.klein4_bind(hdc.klein4_triality_cycle(u16),
                          hdc.klein4_triality_cycle(v16))
    homomorphism_16 = list(lhs.buffer) == list(rhs.buffer)
    # the toml conjugation cascade T.flip_a.T^-1 = flip_{T(a)}
    flips = {1: hdc.klein4_chirality_flip_omega7,
             2: hdc.klein4_chirality_flip_gamma5,
             3: hdc.klein4_cpt_mirror}
    conj = {}
    for a, fn in flips.items():
        p = compose(sigma, compose(hv_perm(fn), sigma_inv))
        conj[a] = {"equals_flip_of": [b for b in flips
                                      if p == hv_perm(flips[b])],
                   "expected": sigma[a]}
    conj_ok = all(c["equals_flip_of"] == [c["expected"]]
                  for c in conj.values())
    emit(kind="carrier_A_v4_sigma",
         op="srmech.math.hdc.klein4_triality_cycle",
         sigma=list(sigma), sigma_squared=list(sigma2),
         order=perm_order(sigma),
         fixes_only_identity=(sigma[0] == 0 and all(sigma[x] != x
                                                    for x in (1, 2, 3))),
         inverse_flag_is_sigma_squared=(sigma_inv == sigma2),
         v4_homomorphism_all_16_pairs=homomorphism_16,
         conjugation_cascade={str(k): v for k, v in conj.items()},
         conjugation_cascade_ok=conj_ok)

    # the order-2 partner at carrier A: the CD-rung-bump transposition
    t8 = measured_rung_transposition(8, 4)
    t16 = measured_rung_transposition(16, 8)
    emit(kind="carrier_A_transposition",
         source="CD order-rung bump, mode both (leg-(d) instrument re-run)",
         t_dim8=list(t8), t_dim16=list(t16), same_at_both_rungs=(t8 == t16),
         order=perm_order(t8),
         reading="the transposition (1 3): iomega7 <-> cpt, gamma5 fixed "
                 "(alphabet state = 2*g5 + iw7)")

    # the S3 presentation at carrier A
    rel_a = compose(t8, compose(sigma, t8))
    s3_a = closure([sigma, t8])
    emit(kind="carrier_A_s3_presentation",
         a="klein4_triality_cycle (order 3)",
         s="CD-rung transposition (order 2)",
         a_cubed_is_id=(compose(sigma, sigma2) == IDENT),
         s_squared_is_id=(compose(t8, t8) == IDENT),
         s_a_s_equals_a_squared=(rel_a == sigma2),
         generated_group_order=len(s3_a),
         generated_order_census={str(k): v
                                 for k, v in order_census(s3_a).items()},
         is_s3=(len(s3_a) == 6))

    # ── R4: carrier B — the 28-dim so(8) adjoint ──────────────────────────
    tau = qt.triality_automorphism()
    s_b = qt.triality_swap()
    tau2 = mat_matmul(tau, tau)
    tau3 = mat_matmul(tau2, tau)
    sb2 = mat_matmul(s_b, s_b)
    stag = mat_matmul(s_b, mat_matmul(tau, s_b))       # S.tau.S
    n = 28
    eye = Mat.from_rows([[1.0 if i == j else 0.0 for j in range(n)]
                         for i in range(n)])

    def diff_norm(a: Mat, b: Mat) -> float:
        ar, br = a.tolist(), b.tolist()
        return mat_norm(Mat.from_rows(
            [[ar[i][j] - br[i][j] for j in range(n)] for i in range(n)]))

    tau_l, tau2_l = tau.tolist(), tau2.tolist()
    sb_l = s_b.tolist()
    fix_tau_trace = sum((1.0 + tau_l[i][i] + tau2_l[i][i]) / 3.0
                        for i in range(n))
    fix_swap_trace = sum((1.0 + sb_l[i][i]) / 2.0 for i in range(n))
    emit(kind="carrier_B_so8_s3_presentation",
         a="triality_automorphism tau = S_B.S_C (order 3)",
         s="triality_swap S_B (order 2)",
         tau_cubed_residual=diff_norm(tau3, eye),
         tau_not_identity=diff_norm(tau, eye),
         tau_squared_not_identity=diff_norm(tau2, eye),
         swap_squared_residual=diff_norm(sb2, eye),
         swap_not_identity=diff_norm(s_b, eye),
         s_a_s_equals_a_squared_residual=diff_norm(stag, tau2),
         fix_tau_projector_trace=fix_tau_trace,
         fix_tau_equals_g2_14=_near(fix_tau_trace, 14.0),
         fix_swap_projector_trace=fix_swap_trace,
         fix_swap_equals_so7_21=_near(fix_swap_trace, 21.0),
         presentation_holds=(diff_norm(tau3, eye) < TOL
                             and diff_norm(sb2, eye) < TOL
                             and diff_norm(stag, tau2) < TOL
                             and diff_norm(tau, eye) > 1.0
                             and diff_norm(tau2, eye) > 1.0))

    # label-level shadow: triality_cycle is the 3-cycle on {v,s,c}
    labels = ["v", "s", "c"]
    lab_cycle = {f: qt.triality_cycle(f) for f in labels}
    emit(kind="carrier_B_label_shadow",
         triality_cycle=lab_cycle,
         is_3_cycle=(sorted(lab_cycle.values()) == sorted(labels)
                     and all(lab_cycle[f] != f for f in labels)),
         note="the frame-label 3-cycle 8v->8s->8c; sigma 3-cycles the three "
              "non-identity sectors — both are the 3-cycle on a 3-element "
              "set; NO in-tree op pins a dictionary {v,s,c}<->{iw7,g5,cpt} "
              "(measured absence, see kind='carrier_disjointness')")

    # ── R5: negative controls ─────────────────────────────────────────────
    # NC1: V4 TRANSLATION in place of the automorphism partner — must FAIL
    g5 = hv_perm(hdc.klein4_chirality_flip_gamma5)
    rel_nc1 = compose(g5, compose(sigma, g5))
    grp_nc1 = closure([sigma, g5])
    emit(kind="negative_control_1_translation_pairing",
         expectation="FAIL — a translation is an OBJECT the automorphism "
                     "permutes, not an element of Aut(V4)",
         s_a_s_equals_a_squared=(rel_nc1 == sigma2),
         generated_group_order=len(grp_nc1),
         is_s3=(len(grp_nc1) == 6),
         control_behaves=(rel_nc1 != sigma2))

    # NC2: the central involution -I28 in place of the swap — must FAIL
    neg_eye = Mat.from_rows([[-1.0 if i == j else 0.0 for j in range(n)]
                             for i in range(n)])
    rel_nc2 = mat_matmul(neg_eye, mat_matmul(tau, neg_eye))
    emit(kind="negative_control_2_central_involution",
         expectation="FAIL — (-I).tau.(-I) = tau != tau^2",
         s_squared_residual=diff_norm(mat_matmul(neg_eye, neg_eye), eye),
         s_a_s_equals_a_squared_residual=diff_norm(rel_nc2, tau2),
         control_behaves=(diff_norm(rel_nc2, tau2) > 1.0))

    # NC3: the §3.29.3 most-common error — order-2 objects must be REJECTED
    #      by the order-3 certificate on BOTH carriers
    swap3 = mat_matmul(sb2, s_b)
    emit(kind="negative_control_3_swap_for_cycle_error",
         expectation="REJECT — the order-2 swap is not the order-3 element",
         v4_transposition_order=perm_order(t8),
         v4_transposition_cubed_is_id=(compose(t8, compose(t8, t8)) == IDENT),
         so8_swap_cubed_residual=diff_norm(swap3, eye),
         so8_swap_is_order_3=(diff_norm(swap3, eye) < TOL),
         control_behaves=(perm_order(t8) == 2
                          and diff_norm(swap3, eye) > 1.0))

    # NC4: sense-4 separation — associator census at H (0) vs O (168)
    def assoc_census(dim):
        nonzero = 0
        for i in range(dim):
            for j in range(dim):
                for k in range(dim):
                    d = associator(cd_basis(dim, i), cd_basis(dim, j),
                                   cd_basis(dim, k))
                    if any(v != 0 for v in d):
                        nonzero += 1
        return nonzero
    nz4, nz8 = assoc_census(4), assoc_census(8)
    emit(kind="negative_control_4_sense4_separation",
         expectation="SEPARATE — sense 4 (associator triangle) is trivial "
                     "where both S3 carriers already exist",
         associator_nonzero_dim4=nz4, of_dim4=64,
         associator_nonzero_dim8=nz8, of_dim8=512,
         control_behaves=(nz4 == 0 and nz8 == 168))

    # ── R6: the ISA's carrier — type-level measurement ────────────────────
    stream = HV(array("B", [0, 1, 2, 3, 2, 1]), sectors=4)
    sigma_out = hdc.klein4_triality_cycle(stream)
    seventh = qt.lean_isa_seventh_primitive()
    cert = dict(seventh)
    tau_obj = cert.pop("triality")
    cert_json = json.dumps(cert, default=str)
    emit(kind="isa_carrier",
         dispatch_alphabet="the Klein-4 sectors {0,1,2,3} "
                           "(cascade.parallel_sector_dispatch; klein4_* HV)",
         klein4_triality_cycle_type=(
             f"{type(stream).__name__} -> {type(sigma_out).__name__} "
             "(stream -> stream on the dispatch alphabet; composable opcode)"),
         triality_automorphism_type=(
             f"() -> {type(tau_obj).__name__} 28x28 (a constant engine "
             "matrix; does not act on the dispatch alphabet)"),
         lean_isa_seventh_primitive_type=(
             f"() -> {type(seventh).__name__} (a certificate/report op, "
             "not a data-path opcode)"),
         seventh_names_order_three=cert["order_three_primitive"],
         seventh_mentions_klein4_sibling=("klein4" in cert_json.lower()),
         registry_has_klein4_triality_cycle=any(
             t.name == "srmech.math.hdc.klein4_triality_cycle"
             for t in get_tool_schema().tools),
         registry_has_lean_isa_seventh=any(
             t.name.endswith("lean_isa_seventh_primitive")
             for t in get_tool_schema().tools))

    # carrier disjointness: no shipped op maps the 28-dim adjoint carrier
    # onto the 4-letter alphabet or back (name-level census of the registry)
    bridge_hits = [t.name for t in get_tool_schema().tools
                   if ("klein4" in t.name and "so8" in t.name)
                   or ("klein4" in t.name
                       and "triality_automorphism" in t.name)]
    emit(kind="carrier_disjointness",
         registry_bridge_ops=bridge_hits,
         no_shipped_intertwiner=(len(bridge_hits) == 0),
         note="the matched presentation is therefore FORM evidence at two "
              "carriers; object-identity is not measurable in-tree")

    # ── R7: Lagrange survival + what each generation route reaches ────────
    xor1, xor2, xor3 = (hv_perm(hdc.klein4_chirality_flip_omega7),
                        hv_perm(hdc.klein4_chirality_flip_gamma5),
                        hv_perm(hdc.klein4_cpt_mirror))
    g_toggles = closure([xor1, xor2, xor3])
    g_plus_t = closure([xor1, xor2, xor3, t8])
    g_plus_both = closure([xor1, xor2, xor3, t8, sigma])
    emit(kind="lagrange_survival",
         three_divides_8=(mod_add(0, 8, 3) == 0),
         three_divides_3=(mod_add(0, 3, 3) == 0),
         toggles_group_order=len(g_toggles),
         toggles_order_census={str(k): v
                               for k, v in order_census(g_toggles).items()},
         toggles_plus_rung_transposition_order=len(g_plus_t),
         toggles_plus_rung_order_census={
             str(k): v for k, v in order_census(g_plus_t).items()},
         toggles_plus_rung_reaches_order_3=(
             3 in order_census(g_plus_t)),
         toggles_plus_seventh_order=len(g_plus_both),
         toggles_plus_seventh_order_census={
             str(k): v for k, v in order_census(g_plus_both).items()},
         reading="the atoms' toggles form a 2-group; adding the CD-ladder "
                 "transposition still gives a 2-group (order 8, 3 does not "
                 "divide 8 — Lagrange UNTOUCHED and leg-(d)-STRENGTHENED); "
                 "only the 7th opcode unlocks order 3 (group -> 24 = "
                 "V4 x| S3, the Aut(Q8)=S4 echo)")

    # ── VERDICT ───────────────────────────────────────────────────────────
    a_ok = next(r for r in OUT if r["kind"] == "carrier_A_s3_presentation")
    b_ok = next(r for r in OUT
                if r["kind"] == "carrier_B_so8_s3_presentation")
    controls = [r for r in OUT if r["kind"].startswith("negative_control")]
    carrier_a_holds = (a_ok["a_cubed_is_id"] and a_ok["s_squared_is_id"]
                       and a_ok["s_a_s_equals_a_squared"] and a_ok["is_s3"])
    carrier_b_holds = b_ok["presentation_holds"]
    controls_behave = all(r["control_behaves"] for r in controls)
    if carrier_a_holds and carrier_b_holds and controls_behave:
        verdict = "BOTH_TRUE_DIFFERENT_CARRIERS"
    elif carrier_a_holds != carrier_b_holds:
        verdict = "NOTEBOOK_RIGHT" if carrier_a_holds else "CODE_RIGHT"
    else:
        verdict = "NOT_RESOLVABLE"
    emit(kind="verdict", verdict=verdict,
         carrier_A_v4_presentation_holds=carrier_a_holds,
         carrier_B_so8_presentation_holds=carrier_b_holds,
         negative_controls_behave=controls_behave,
         isa_slot=("klein4_triality_cycle — the instantiation acting on the "
                   "ISA's own dispatch alphabet (stream -> stream, C peer)"),
         other_is_for=("triality_automorphism — the certifying engine "
                       "(tau^3=I, Fix(tau)=g2=14) that PROVES order-3-ness; "
                       "lean_isa_seventh_primitive is its certificate/report "
                       "surface, not a data-path opcode"),
         lagrange_argument="SURVIVES (about the generated group, not the "
                           "chosen extension; strengthened by leg (d): "
                           "toggles+rung-transposition is still a 2-group)")

    path = __file__.replace(".py", ".ndjson")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for rec in OUT:
            fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
    print(f"wrote {len(OUT)} records -> {path}")
    for rec in OUT:
        if rec["kind"] in ("verdict", "carrier_A_s3_presentation",
                           "carrier_B_so8_s3_presentation"):
            print(json.dumps(rec, sort_keys=True, default=str)[:1600])


if __name__ == "__main__":
    main()
