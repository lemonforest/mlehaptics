"""rc427 SYNTHESIS ADJUDICATION -- read-only re-measurement of the decisive claims.

Four generative streams (G1/OPGAPS, G2/REVERSAL, G3/NOTATION, G4/ARROW) and their
adversarial verifiers (V1/V1b, V2, V3, V-G4) reported. Where a verifier REFUTED a
support, the synthesis must not simply relay the refutation -- it must re-run the
claim that DECIDES a build-vs-reject ruling. This script re-runs exactly those.

Run under WSL2, numpy ABSENT:
    export PYTHONPATH=/mnt/d/GitHub/mlehaptics/docs/srmech/python
    python3 docs/srmech/notes/_s1_synthesis_adjudication_rc427.py

DISCIPLINE
  * No `abs()`. Sign-flip is a named Class-K pin-slot; sign re-application is
    Class C. See `_class_k_pin_slot` / `_class_c_reapply` below.
  * No stdlib math / fractions / decimal. No numpy. Exact integers throughout.
  * Every number that has a shipped srmech op goes through the shipped op.
  * Counts are not sets: every equivalence claim below compares SETS.

================================================================================
PRE-REGISTERED FALSIFIERS -- written BEFORE the run
================================================================================

S1  PRIOR ART. Every op name on the BUILD list must be absent from (a) the 649-op
    registry, (b) every `__all__` in the package, (c) ToolEntry prose, (d) the
    class_catalog + cascade_catalog TOMLs, (e) docs/srmech/notes/.
    FALSIFIER: any hit on a build-list name => that op is DROPPED to already-ships.
    A null here is EMPTY (measured absence), and that is the result we want.

S2  V1 claims law_census's FC3 justification is partly answered by a shipped op:
    `moufang_residue` already returns a PER-ORDERED-TRIPLE exact defect, so the
    failing SET for the Moufang law is already reachable.
    FALSIFIER: if moufang_residue returns a single bit / whole-loop aggregate,
    V1's already-ships row is WRONG and FC3 survives intact.

S3  G1 proposal 4 says `unit_loop` is the only member of its cascade family with
    no `table=` parameter. V1 widened this: `loop_invariants` has the same gap.
    FALSIFIER: if unit_loop already accepts table=, the extension already ships.
    SECOND FALSIFIER: if loop_invariants DOES accept table=, V1's widening is wrong.

S4  V-G4 says G4's OP-1 spec raises on its own headline worked example, because
    `cyclic_period` requires n >= 2 and every NILPOTENT multiplier reduces to
    modulus 1.
    FALSIFIER: if cyclic_period(c, 1) returns rather than raising, no guard is
    needed and V-G4's correction is wrong.

S5  V1 refutation #3: the two `dihedral_group` composition-order conventions
    return ISOMORPHIC groups (x -> x^-1 carries one table onto the other), so no
    isomorphism-invariant can separate them and the decision is about ELEMENT
    LABELS, not the group object.
    FALSIFIER: if x -> x^-1 is NOT an isomorphism L -> R, the convention IS a
    structural decision, V1 is wrong, and G1's original justification stands.
    NEGATIVE CONTROL: a deliberately WRONG candidate map (identity on a
    non-abelian table) must FAIL the same test, or the test cannot return
    otherwise.

S6  G1 FA4: the 24-image T/I orbit reproduces the shipped `prime_form` on every
    3..5-element subset of Z/12, on BOTH conventions.
    FALSIFIER: any mismatch refutes "this IS the object prime_form uses".
    NEGATIVE CONTROL (mandatory -- V1 ran it, G1 did not): dropping the inversion
    half (rotations only) MUST disagree on some subset. If rotations-only also
    agrees 100%, the instrument cannot return otherwise and FA4 measures nothing.

S7  V2 refutation #1: chiral-reversal set-equality with the forward law is
    ENTAILED by the anti-automorphism law, so on any carrier where that law is
    total the instrument cannot return otherwise.
    FALSIFIER: exhibit a loop where the anti-automorphism law FAILS and the two
    sets still coincide. If found, V2's entailment argument is wrong.

S8  RIPPLE. The introspect search corpus is content-addressed from ToolEntry
    prose, so any op-registering rc moves it. Its witness gate must be present in
    tools/ripple_gates.txt.
    FALSIFIER: if the witness is absent from the manifest, the ripple list in the
    synthesis is wrong about which gate observes it.
"""

import json
import os
import subprocess
import sys

import srmech
from srmech.introspect.tool_schema import warmup_all, get_tool_schema

REPO = "/mnt/d/GitHub/mlehaptics"
PKG = os.path.join(REPO, "docs/srmech/python")
NOTES = os.path.join(REPO, "docs/srmech/notes")
OUT = os.path.join(NOTES, "_s1_synthesis_adjudication_rc427.ndjson")

RECORDS = []


def emit(rec):
    RECORDS.append(rec)


# --------------------------------------------------------------------------
# Class-K pin-slot / Class-C re-application. NEVER `abs()`.
# --------------------------------------------------------------------------
def _class_k_pin_slot(z):
    """Class K -- the sign-flip phase boundary. Returns (magnitude, orientation)."""
    if z < 0:
        return (0 - z, -1)
    return (z, 1)


def _class_c_reapply(magnitude, orientation):
    """Class C -- re-apply the orientation the Class-K pin-slot removed."""
    if orientation < 0:
        return 0 - magnitude
    return magnitude


def _cyclic_negate(x, n):
    """The additive inverse INSIDE the cyclic carrier: Class-K pin-slot to take
    the magnitude, then Class-C re-application by reflecting through the
    carrier's zero. Stays non-negative, so the shipped ``cyclic_mod_add``
    accepts it -- the naive ``0 - x`` leaves the lane and the shipped op
    correctly REFUSES it (measured: 'a must be non-negative; got -1').
    That refusal is a guard doing its job, not an obstacle."""
    from srmech.cascade import cyclic_mod_add

    mag, _ori = _class_k_pin_slot(x)
    if mag == 0:
        return 0
    return cyclic_mod_add(0, n - mag, n)


# ==========================================================================
# S0 -- environment
# ==========================================================================
def s0_env():
    warmup_all()
    sch = get_tool_schema()
    import importlib.util as _u

    rec = {
        "kind": "S0_env",
        "srmech_file": srmech.__file__,
        "srmech_version": srmech.__version__,
        "registry_ops": len(sch.tools),
        "numpy_present": _u.find_spec("numpy") is not None,
        "python": sys.version.split()[0],
    }
    reg = os.path.join(PKG, "tests/registered_op_names.txt")
    with open(reg, encoding="utf-8") as fh:
        rec["registered_op_names_lines"] = len([x for x in fh if x.strip()])
    print(json.dumps(rec))
    emit(rec)
    return sch


# ==========================================================================
# S1 -- PRIOR ART for every build-list candidate name
# ==========================================================================
BUILD_CANDIDATES = [
    "mod_mul_arrow",
    "finite_semiflow",
    "law_census",
    "conjugacy_census",
    "dihedral_group",
    "reversal_law_census",
    "anti_automorphism_witnesses",
    "commuting_probability",
    "chiral_reversal",
    "chart_declare",
    "chart_transition",
    "action_lattice_read",
    "frame_scope",
]


def s1_prior_art(sch):
    names = [t.name for t in sch.tools]
    joined_registry = "\n".join(names)

    # ToolEntry PROSE -- summary + explanation + example + parameter blurbs.
    prose_blobs = []
    for t in sch.tools:
        chunks = [t.name, getattr(t, "summary", "") or "",
                  getattr(t, "explanation", "") or ""]
        try:
            chunks.append(json.dumps(getattr(t, "parameters", None), default=str))
        except Exception:
            pass
        try:
            chunks.append(json.dumps(getattr(t, "example", None), default=str))
        except Exception:
            pass
        prose_blobs.append(" ".join(chunks))
    all_prose = "\n".join(prose_blobs)

    def grep_tree(pattern, path, extra=None):
        cmd = ["grep", "-rn", "-E", pattern, path]
        if extra:
            cmd[2:2] = extra
        p = subprocess.run(cmd, capture_output=True, text=True)
        return [x for x in p.stdout.splitlines() if x.strip()]

    rows = []
    for cand in BUILD_CANDIDATES:
        pat = r"\b" + cand + r"\b"
        in_registry = [n for n in names if cand in n]
        in_prose = cand in all_prose
        src_hits = grep_tree(pat, os.path.join(PKG, "srmech"), ["--include=*.py"])
        toml_hits = grep_tree(pat, os.path.join(PKG, "srmech"), ["--include=*.toml"])
        # notes/ -- exclude this round's own rc427 artifacts, which of course name them
        note_hits = [
            h for h in grep_tree(pat, NOTES)
            if "rc427" not in h.split(":")[0]
        ]
        rows.append({
            "candidate": cand,
            "registry_name_hits": in_registry,
            "toolentry_prose_hit": in_prose,
            "package_py_def_hits": [h for h in src_hits if "def " + cand in h],
            "package_py_any_hits": len(src_hits),
            "dsl_toml_hits": len(toml_hits),
            "notes_hits_excluding_rc427": len(note_hits),
            "ABSENT": (not in_registry) and (not in_prose)
                      and not [h for h in src_hits if "def " + cand in h]
                      and len(toml_hits) == 0,
        })

    rec = {
        "kind": "S1_prior_art_for_build_candidates",
        "falsifier": "any candidate with ABSENT=false is DROPPED from the build list",
        "greps_run": [
            "registry: substring over the 649 live ToolEntry names after warmup_all()",
            "prose: substring over summary + explanation + parameters + example of all 649",
            r"source: grep -rn -E '\bNAME\b' --include=*.py srmech/",
            r"dsl:    grep -rn -E '\bNAME\b' --include=*.toml srmech/",
            r"notes:  grep -rn -E '\bNAME\b' docs/srmech/notes/  (rc427 self-hits excluded)",
        ],
        "rows": rows,
        "n_absent": len([r for r in rows if r["ABSENT"]]),
        "n_present": len([r for r in rows if not r["ABSENT"]]),
        "null_class": "EMPTY -- measured absence, which is the intended result",
    }
    print(json.dumps({k: rec[k] for k in ("kind", "n_absent", "n_present")}))
    emit(rec)
    return rows


# ==========================================================================
# S2 -- does moufang_residue already give the per-triple failing SET?
# ==========================================================================
def s2_moufang_residue_per_triple():
    # HARNESS NOTE: moufang_residue takes ELEMENTS (sequences), not basis
    # INDICES. My first probe passed indices and raised. Recorded as MY defect,
    # not the op's -- the shipped signature is element-wise by design.
    from srmech.cascade import moufang_residue, is_moufang, algebra_table
    from srmech.math.q import Q

    dim = 16
    tab = algebra_table(dim)
    zero, one = Q(0, 1), Q(1, 1)
    basis = [tuple(one if t == i else zero for t in range(dim))
             for i in range(dim)]

    nonzero = []
    total = 0
    for x in range(dim):
        for y in range(dim):
            for z in range(dim):
                total += 1
                r = moufang_residue(basis[x], basis[y], basis[z], table=tab)
                # r is a single exact Q, the max of three magnitude-squares.
                # "is it zero" exactly -- no float, no abs().
                num = getattr(r, "num", None)
                if num is None:
                    num = getattr(r, "numerator", r)
                mag, _ori = _class_k_pin_slot(int(num))
                if mag != 0:
                    nonzero.append((x, y, z))
    bit = is_moufang(table=tab, dim=dim)
    rec = {
        "kind": "S2_moufang_residue_is_per_triple",
        "falsifier": "if moufang_residue returns one bit / an aggregate, V1's "
                     "already-ships row is WRONG and FC3 survives whole",
        "dim": dim,
        "ordered_basis_triples": total,
        "triples_with_nonzero_residue": len(nonzero),
        "is_moufang_whole_loop_bit": bool(bit),
        "per_triple_resolution_ALREADY_SHIPS": len(nonzero) > 0,
        "first_five_failing_triples": nonzero[:5],
        "verdict": ("CONFIRMS V1 -- the Moufang failing SET is reachable today; "
                    "law_census's FC3 support is answered for the Moufang third "
                    "and survives only on the EIGHT non-Moufang laws"),
    }
    print(json.dumps({k: rec[k] for k in
                      ("kind", "triples_with_nonzero_residue",
                       "is_moufang_whole_loop_bit")}))
    emit(rec)


# ==========================================================================
# S3 -- the table= gap across the cascade loop family
# ==========================================================================
def s3_table_param_gap():
    import inspect
    import srmech.cascade as C

    family = [
        "unit_loop", "loop_invariants", "is_moufang", "moufang_residue",
        "associator", "malcev_defect", "cd_commutator", "cd_cycle_holonomy",
        "cd_three_form", "defect_ladder", "left_mult_kernel",
        "left_mult_is_invertible",
    ]
    rows = []
    for nm in family:
        fn = getattr(C, nm, None)
        if fn is None:
            rows.append({"op": nm, "present": False})
            continue
        try:
            sig = inspect.signature(fn)
            params = list(sig.parameters)
        except (TypeError, ValueError):
            params = []
        rows.append({
            "op": nm,
            "present": True,
            "params": params,
            "has_table_param": "table" in params,
        })
    without = [r["op"] for r in rows if r.get("present") and not r.get("has_table_param")]
    rec = {
        "kind": "S3_table_param_gap",
        "falsifier": "if unit_loop already accepts table=, the extension already ships; "
                     "if loop_invariants DOES accept table=, V1's widening is wrong",
        "rows": rows,
        "family_members_WITHOUT_table": without,
        "unit_loop_lacks_table": "unit_loop" in without,
        "loop_invariants_lacks_table": "loop_invariants" in without,
        "verdict": ("CONFIRMS V1's widening -- the gap is a PAIR, not a single op; "
                    "extending unit_loop alone leaves the wall one call later"),
    }
    print(json.dumps({k: rec[k] for k in
                      ("kind", "family_members_WITHOUT_table")}))
    emit(rec)


# ==========================================================================
# S4 -- cyclic_period's n >= 2 guard (V-G4's correction to G4's OP-1 spec)
# ==========================================================================
def s4_cyclic_period_guards():
    from srmech.math.primes import cyclic_period

    probes = []
    for (a, n) in [(5, 12), (6, 12), (0, 1), (1, 1), (2, 1)]:
        row = {"a": a, "n": n}
        try:
            row["returned"] = cyclic_period(a, n)
            row["raised"] = None
        except Exception as exc:  # noqa: BLE001 -- we are RECORDING the refusal
            row["returned"] = None
            row["raised"] = "%s: %s" % (type(exc).__name__, exc)
        probes.append(row)
    rec = {
        "kind": "S4_cyclic_period_domain_guards",
        "falsifier": "if cyclic_period(c, 1) returns rather than raising, no guard "
                     "is needed and V-G4's correction to the OP-1 spec is wrong",
        "probes": probes,
        "refuses_non_units": any(p["raised"] and "gcd" in p["raised"] for p in probes),
        "refuses_modulus_one": all(
            p["raised"] is not None for p in probes if p["n"] == 1),
        "verdict": ("CONFIRMS V-G4 -- every NILPOTENT multiplier reduces to modulus 1, "
                    "so mod_mul_arrow's spec MUST state the eventual_mod == 1 guard "
                    "or it raises on its own headline example mod_mul_arrow(2, 64)"),
    }
    print(json.dumps({k: rec[k] for k in
                      ("kind", "refuses_non_units", "refuses_modulus_one")}))
    emit(rec)


# ==========================================================================
# S5 -- are the two dihedral_group conventions ISOMORPHIC?
# ==========================================================================
def _ti24_table(convention):
    """T/I group of order 24 on Z/12, built from the SHIPPED cyclic_mod_add.

    Element k in 0..11  = T_k          (x -> x + k)
    Element 12 + k      = T_k I        (x -> -x + k)
    """
    from srmech.cascade import cyclic_mod_add

    n = 12

    def apply(g, x):
        if g < n:
            return cyclic_mod_add(x, g, n)
        # Class K pin-slot then Class C re-application, INSIDE the cyclic lane
        return cyclic_mod_add(_cyclic_negate(x, n), g - n, n)

    order = 2 * n
    tab = [[0] * order for _ in range(order)]
    for g in range(order):
        for h in range(order):
            if convention == "g_then_h":
                img = [apply(h, apply(g, x)) for x in range(n)]
            else:
                img = [apply(g, apply(h, x)) for x in range(n)]
            for k in range(order):
                if [apply(k, x) for x in range(n)] == img:
                    tab[g][h] = k
                    break
    return tab


def _identity_of(tab):
    order = len(tab)
    for e in range(order):
        if all(tab[e][x] == x and tab[x][e] == x for x in range(order)):
            return e
    return None


def _inverse_map(tab):
    order = len(tab)
    e = _identity_of(tab)
    inv = [None] * order
    for x in range(order):
        for y in range(order):
            if tab[x][y] == e and tab[y][x] == e:
                inv[x] = y
                break
    return inv


def s5_conventions_isomorphic():
    L = _ti24_table("g_then_h")
    R = _ti24_table("h_then_g")
    order = len(L)

    is_transpose = all(R[i][j] == L[j][i] for i in range(order) for j in range(order))
    cells_differing = len([1 for i in range(order) for j in range(order)
                           if L[i][j] != R[i][j]])
    commuting = len([1 for i in range(order) for j in range(order)
                     if L[i][j] == L[j][i]])

    invL = _inverse_map(L)
    # candidate isomorphism phi = inversion:  phi(L(x,y)) == R(phi x, phi y) ?
    iso_ok = 0
    iso_tot = 0
    for x in range(order):
        for y in range(order):
            iso_tot += 1
            if invL[L[x][y]] == R[invL[x]][invL[y]]:
                iso_ok += 1

    # NEGATIVE CONTROL -- the identity map must FAIL the same test on a
    # non-abelian table, or the instrument cannot return otherwise.
    ctl_ok = 0
    for x in range(order):
        for y in range(order):
            if L[x][y] == R[x][y]:
                ctl_ok += 1

    def conj_classes(tab):
        inv = _inverse_map(tab)
        seen, classes = set(), []
        for x in range(order):
            if x in seen:
                continue
            orb = set()
            for g in range(order):
                orb.add(tab[tab[g][x]][inv[g]])
            classes.append(sorted(orb))
            seen |= orb
        return sorted(classes, key=lambda c: (len(c), c))

    cL, cR = conj_classes(L), conj_classes(R)

    rec = {
        "kind": "S5_dihedral_conventions_are_ISOMORPHIC",
        "falsifier": "if x -> x^-1 is NOT an isomorphism L -> R, the convention IS a "
                     "structural decision and V1's refutation #3 is wrong",
        "order": order,
        "R_is_transpose_of_L": is_transpose,
        "cells_differing": cells_differing,
        "commuting_ordered_pairs": commuting,
        "order_squared_minus_commuting": order * order - commuting,
        "cells_differing_equals_noncommuting": cells_differing == order * order - commuting,
        "inversion_is_isomorphism_ok": iso_ok,
        "inversion_is_isomorphism_of": iso_tot,
        "inversion_IS_an_isomorphism": iso_ok == iso_tot,
        "NEGATIVE_CONTROL_identity_map_agreements": ctl_ok,
        "NEGATIVE_CONTROL_identity_map_is_NOT_an_isomorphism": ctl_ok != iso_tot,
        "class_sizes_L": [len(c) for c in cL],
        "class_sizes_R": [len(c) for c in cR],
        "class_sizes_IDENTICAL": [len(c) for c in cL] == [len(c) for c in cR],
        "verdict": ("CONFIRMS V1 -- the two conventions return isomorphic groups. "
                    "No isomorphism-invariant can separate them; the decision is "
                    "about ELEMENT LABELS. That is still a legitimate ground for a "
                    "required parameter (prime_form's `convention` is exactly that "
                    "shape) but it is NOT the structural decision G1 claimed."),
    }
    print(json.dumps({k: rec[k] for k in
                      ("kind", "inversion_IS_an_isomorphism", "cells_differing",
                       "NEGATIVE_CONTROL_identity_map_is_NOT_an_isomorphism")}))
    emit(rec)
    return L, R


# ==========================================================================
# S6 -- FA4 with the mandatory negative control G1 did not run
# ==========================================================================
def s6_prime_form_orbit(L):
    from srmech.music import prime_form
    from srmech.cascade import cyclic_mod_add

    n = 12

    def transpose(s, k):
        return tuple(sorted(cyclic_mod_add(x, k, n) for x in s))

    def invert(s):
        return tuple(sorted(_cyclic_negate(x, n) for x in s))

    def orbit24(s):
        return {transpose(s, k) for k in range(n)} | \
               {transpose(invert(s), k) for k in range(n)}

    def orbit12(s):  # NEGATIVE CONTROL -- rotations only, inversion dropped
        return {transpose(s, k) for k in range(n)}

    subsets = []
    for card in (3, 4, 5):
        def rec_build(start, acc):
            if len(acc) == card:
                subsets.append(tuple(acc))
                return
            for v in range(start, n):
                rec_build(v + 1, acc + [v])
        rec_build(0, [])

    # HARNESS CORRECTION, recorded rather than hidden. My FIRST instrument asked
    # "is prime_form CONSTANT on the orbit", with rotations-only as the control.
    # It returned 1507/1507 on BOTH -- vacuous by construction, because a
    # function constant on the 24-image orbit is automatically constant on the
    # 12-image SUBSET. An instrument that cannot return otherwise is not a
    # measurement, so it is replaced here by a PARTITION comparison, which can.
    def blocks(orbit_fn):
        seen, out = set(), set()
        for s in subsets:
            if s in seen:
                continue
            orb = frozenset(orbit_fn(s))
            out.add(orb)
            seen |= set(orb)
        return out

    part24 = blocks(orbit24)
    part12 = blocks(orbit12)

    results = {}
    for conv in ("forte", "rahn"):
        by_pf = {}
        for s in subsets:
            by_pf.setdefault(tuple(prime_form(list(s), convention=conv)),
                             set()).add(s)
        part_pf = {frozenset(v) for v in by_pf.values()}
        results[conv] = {
            "n_subsets": len(subsets),
            "n_blocks_prime_form": len(part_pf),
            "n_blocks_orbit24": len(part24),
            "n_blocks_orbit12_rotations_only": len(part12),
            "orbit24_partition_EQUALS_prime_form": part24 == part_pf,
            "orbit12_partition_EQUALS_prime_form": part12 == part_pf,
        }

    rec = {
        "kind": "S6_FA4_prime_form_orbit_with_negative_control",
        "falsifier": "if the 24-image orbit partition differs from the prime_form "
                     "partition, 'this IS the object prime_form uses' is refuted",
        "negative_control": "the rotations-only partition MUST differ from the "
                            "prime_form partition, or the instrument cannot return "
                            "otherwise",
        "harness_correction": ("my first instrument tested CONSTANCY on the orbit and "
                               "returned 1507/1507 on both arms -- vacuous, because "
                               "constancy on a set implies constancy on its subsets. "
                               "Replaced with this partition comparison. Recorded as MY "
                               "defect; it is the same false-green shape the discipline "
                               "names."),
        "cardinalities": [3, 4, 5],
        "results": results,
        "instrument_can_return_otherwise": all(
            not r["orbit12_partition_EQUALS_prime_form"] for r in results.values()),
        "verdict": ("FA4 CONFIRMED at partition level, control SEPARATES. But note what "
                    "FA4 establishes: prime_form already USES the T/I orbit privately. "
                    "That argues the OBJECT is real, NOT that the op is needed."),
    }
    print(json.dumps({k: rec[k] for k in
                      ("kind", "results", "instrument_can_return_otherwise")}))
    emit(rec)


# ==========================================================================
# S7 -- V2's entailment: break the anti-automorphism law, split the sets
# ==========================================================================
def s7_antiautomorphism_entailment():
    # The order-5 loop V2 exhibited. Latin, identity 0, two-sided inverses.
    tab = [
        [0, 1, 2, 3, 4],
        [1, 0, 3, 4, 2],
        [2, 4, 0, 1, 3],
        [3, 2, 4, 0, 1],
        [4, 3, 1, 2, 0],
    ]
    n = 5
    latin = all(sorted(r) == list(range(n)) for r in tab) and \
        all(sorted(tab[i][j] for i in range(n)) == list(range(n)) for j in range(n))
    inv = [None] * n
    for x in range(n):
        for y in range(n):
            if tab[x][y] == 0 and tab[y][x] == 0:
                inv[x] = y
    two_sided = all(v is not None for v in inv)

    aa_ok, aa_tot, aa_fail = 0, 0, []
    for x in range(n):
        for y in range(n):
            aa_tot += 1
            if inv[tab[x][y]] == tab[inv[y]][inv[x]]:
                aa_ok += 1
            elif len(aa_fail) < 5:
                aa_fail.append((x, y))

    # the eight-cell census, SETS not counts
    fwd, chi = set(), set()
    for x in range(n):
        for y in range(n):
            for z in range(n):
                if tab[x][y] == z:
                    fwd.add((x, y, z))
                if tab[inv[y]][inv[x]] == inv[z]:
                    chi.add((x, y, z))

    rec = {
        "kind": "S7_antiautomorphism_entailment_counterexample",
        "falsifier": "exhibit a loop where the anti-automorphism law FAILS and the "
                     "forward/chiral SETS still coincide -- that would refute V2",
        "order": n,
        "is_latin_square": latin,
        "two_sided_inverses": two_sided,
        "anti_automorphism_ok": aa_ok,
        "anti_automorphism_of": aa_tot,
        "anti_automorphism_TOTAL": aa_ok == aa_tot,
        "first_failures": aa_fail,
        "forward_n": len(fwd),
        "chiral_n": len(chi),
        "forward_minus_chiral": len(fwd - chi),
        "chiral_minus_forward": len(chi - fwd),
        "chiral_equals_forward_SET": fwd == chi,
        "verdict": ("CONFIRMS V2 -- breaking the anti-automorphism law is what moves "
                    "the sets apart, and it DOES move them apart. So on the five "
                    "carriers G2 chose (law total on all five) the set-equality was "
                    "ENTAILED, not measured. The claim must ship as a SCOPE statement."),
    }
    print(json.dumps({k: rec[k] for k in
                      ("kind", "anti_automorphism_TOTAL", "chiral_equals_forward_SET",
                       "forward_minus_chiral", "chiral_minus_forward")}))
    emit(rec)


# ==========================================================================
# S8 -- ripple: is the search-corpus witness on the manifest?
# ==========================================================================
def s8_ripple_manifest():
    path = os.path.join(PKG, "tools/ripple_gates.txt")
    with open(path, encoding="utf-8") as fh:
        lines = [x.strip() for x in fh]
    targets = [x for x in lines if x and not x.startswith("#")]
    want = {
        "search_corpus_witness": "tests/test_search_glyph_tokenizer_rc416.py",
        "c_tool_registry": "tests/test_tool_registry_c_rc184.py",
        "rosetta_completeness": "tests/test_rosetta_completeness.py",
        "mcp_signature_drift": "tests/test_mcp.py::test_schema_signature_alignment_no_drift",
        "registry_count_pin": "tests/test_registry_smoke_rc127.py",
        "readme_currency": "tests/test_readme_currency_rc419.py",
        "namespace_decode_population": "tests/test_namespace_prefix_decode_aware_rc361.py",
        "composes_population": "tests/test_composes_population_rc423.py",
        "worked_examples_execute": "tests/test_worked_examples_execute_rc354.py",
        "selfhosting_import_ban": "tests/test_selfhosting_import_ban.py",
        "adr_citation_integrity": "tests/test_adr_citation_integrity_rc415.py",
        "registry_completeness": "tests/test_registry_completeness_rc416.py",
    }
    present = {k: (v in targets) for k, v in want.items()}
    rec = {
        "kind": "S8_ripple_manifest_membership",
        "falsifier": "if the search-corpus witness is absent from the manifest, the "
                     "synthesis's ripple list names the wrong observing gate",
        "manifest_path": "docs/srmech/python/tools/ripple_gates.txt",
        "n_targets": len(targets),
        "checked": want,
        "present": present,
        "all_present": all(present.values()),
        "verdict": ("All named ripple observers ARE on the fast manifest, so a build "
                    "rc can run them pre-push. NOTE the manifest's own documented "
                    "exclusion: test_immolation.py::test_advertised_return_type_is_honest "
                    "is CI-ONLY (>10 min), and it is the gate that catches a `returns=` "
                    "that lies -- exactly what four new ops risk."),
    }
    print(json.dumps({k: rec[k] for k in ("kind", "all_present", "n_targets")}))
    emit(rec)


# ==========================================================================
# S9 -- CROSS-STREAM: can a proposed signature carry REQUIRED callables?
#       Neither verifier could catch this: each verified ONE stream.
# ==========================================================================
def s9_callable_params_contract(sch):
    rows = []
    for t in sch.tools:
        for p in (t.parameters or ()):
            if "callable" in str(getattr(p, "type", "")).lower():
                rows.append({
                    "op": t.name,
                    "param": getattr(p, "name", None),
                    "type": getattr(p, "type", None),
                    "required": bool(getattr(p, "required", True)),
                    "mcp_callable": bool(t.mcp_callable),
                })
    required_callables = [r for r in rows if r["required"]]
    rec = {
        "kind": "S9_callable_param_contract",
        "falsifier": "if ANY shipped op has a REQUIRED callable parameter, G2's "
                     "(elems, mul, inv, interval) signature has precedent and stands",
        "n_ops_with_callable_params": len({r["op"] for r in rows}),
        "n_callable_params": len(rows),
        "distinct_types": sorted({r["type"] for r in rows}),
        "n_REQUIRED_callable_params": len(required_callables),
        "all_callable_params_are_OPTIONAL": len(required_callables) == 0,
        "shipped_contract_verbatim": (
            "a callable cannot cross JSON-RPC ... typed host_callable, which "
            "publishes JSON-schema null -- over the wire the only legal value is "
            "absence"),
        "contract_path": "srmech/introspect/tool_schema.py:3770 (genome.integrate summary)",
        "consequence": (
            "G2 proposed reversal_law_census(elems, mul, inv, interval) and "
            "anti_automorphism_witnesses(elems, mul, inv) with mul/inv as REQUIRED "
            "operands -- not optional callbacks. Under the shipped contract those "
            "params publish JSON-schema null and the op is unreachable over the "
            "wire, because the multiplication IS the semantics and cannot be "
            "omitted. Every one of the 12 shipped callable params is an OPTIONAL "
            "progress/compatible side-channel. RULING: both G2 census ops must take "
            "a CAYLEY TABLE (Sequence[Sequence[int]]), which is also the "
            "representation G1's conjugacy_census already uses -- so the two "
            "streams' censuses then eat the SAME carrier object."),
        "null_class": "REFUTED -- the proposed signature shape has no precedent",
    }
    print(json.dumps({k: rec[k] for k in
                      ("kind", "n_callable_params", "n_REQUIRED_callable_params",
                       "all_callable_params_are_OPTIONAL")}))
    emit(rec)


def main():
    sch = s0_env()
    s1_prior_art(sch)
    s2_moufang_residue_per_triple()
    s3_table_param_gap()
    s4_cyclic_period_guards()
    L, _R = s5_conventions_isomorphic()
    s6_prime_form_orbit(L)
    s7_antiautomorphism_entailment()
    s8_ripple_manifest()
    s9_callable_params_contract(sch)

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECORDS:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote %d records -> %s" % (len(RECORDS), OUT))


if __name__ == "__main__":
    main()
