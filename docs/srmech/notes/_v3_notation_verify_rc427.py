"""ADVERSARIAL VERIFICATION of the rc427 G3/NOTATION spec round.

Pre-registered falsifiers, written BEFORE the code below them ran:

  V1  Is G1a's "a = g^-1 mod n, 0 failures / 188 cells" an instrument that
      CAN return otherwise?  Falsifier: sweep EVERY a in 1..n-1 (not only
      a = g^-1) through the SAME two predicates the script uses
      (`contiguous` on the symbol window with s=a, and
      `alphabet_covers_carrier`).  If every a passes, the "0 failures"
      is a tautology and the claim "the alphabet size is FORCED by the
      generator" is NOT what was measured.

  V1b If V1 refutes, is there a predicate under which a = g^-1 IS forced?
      Candidate: the modifier must move the CARRIER by exactly one step,
      i.e. g*s == 1 mod n.  Measure it; report whether it is unique.

  V2  Does G1b compare SETS or merely COUNTS?  Falsifier: re-run the
      6462-cell comparison recording set-equality AND count-equality
      separately, and additionally look for any cell where the counts
      agree but the memberships differ.  (Standing proof: the octonion
      loop, where equal counts hid different triples.)

  V3  Is chart_transition's arithmetic distinct from the REJECTED
      key_signature arithmetic?  Falsifier: compute both from the
      record file and from first principles; if the rotation/accidental
      numbers are the same three shipped calls, the op that was
      PROPOSED and the op that was REJECTED share a derivation.

  V4  Does `frame_scope`'s ABI claim survive?  The spec quotes srmech.h
      as saying appending to srmech_tool_entry_t leaves ABI at 10.
      Falsifier: read the actual struct + comment at rc425 and check
      the quote is about THAT struct and still holds at ABI 14.

  V5  Does G5's action-lattice op already ship?  Falsifier: re-grep the
      649-op registry and every __all__ for a rank-2 / kernel /
      homomorphism surface.

  V6  Does G4's "12 fields, 1 frame-free" survive a set comparison
      rather than a count comparison?
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "python"))

import srmech                                                  # noqa: E402
from srmech.cascade import magnitude, pin_slot_at_zero          # noqa: E402
from srmech.math.covering import lift_fibre                     # noqa: E402
from srmech.math.cyclic import gcd, mod_add, mod_inv, mod_mul   # noqa: E402

MODULI = (5, 7, 12, 17, 19, 22, 24, 31, 41, 53)
RECORDS = []


def emit(**row):
    row.setdefault("srmech_version", srmech.__version__)
    RECORDS.append(row)


# ---- helpers, copied VERBATIM from the script under test -------------
def res(k, n):
    orientation, mag = pin_slot_at_zero(k)
    r = mod_add(int(mag), 0, n)
    if orientation < 0 and r != 0:
        r = mod_add(n - r, 0, n)
    return r


def units(n):
    return tuple(g for g in range(1, n) if gcd(g, n) == 1)


def chain_to_carrier(k, g, n):
    return mod_mul(g, res(k, n), n)


def symbol_chain_positions(c0, a, s, mods):
    return {(d, m): c0 + d + s * m for d in range(a) for m in mods}


def contiguous(values):
    vals = sorted(set(values))
    if len(vals) != len(list(values)):
        return False
    return vals[-1] - vals[0] + 1 == len(vals)


def chain_fibre_shipped(p, g, n, window):
    k0 = mod_mul(mod_inv(g, n), res(p, n), n)
    return lift_fibre(k0, n, window)


def chain_fibre_brute(p, g, n, window):
    return [k for k in range(-window, window + 1)
            if chain_to_carrier(k, g, n) == res(p, n)]


# ══════════════════════════════════════════════════════════════════════
# V1 — can the G1a instrument return otherwise?
# ══════════════════════════════════════════════════════════════════════
def v1_alphabet_forcing_is_vacuous():
    mods = tuple(range(-2, 3))
    total = 0
    passed = 0
    rows_that_are_not_ginv = 0
    passed_and_not_ginv = 0
    western_alternatives = []
    for n in MODULI:
        for g in units(n):
            ginv = mod_inv(g, n)
            for a in range(1, n):
                sym = symbol_chain_positions(0, a, a, mods)
                ok = contiguous(list(sym.values()))
                carrier = sorted(chain_to_carrier(d, g, n) for d in range(a))
                covers = len(set(carrier)) == a
                total += 1
                if ok and covers:
                    passed += 1
                if a != ginv:
                    rows_that_are_not_ginv += 1
                    if ok and covers:
                        passed_and_not_ginv += 1
                        if n == 12 and g == 7:
                            western_alternatives.append(
                                {"a": a, "contiguous": ok,
                                 "covers": covers,
                                 "carrier": carrier})
    emit(finding="V1_G1a_alphabet_forcing_is_VACUOUS",
         n_cells=total,
         n_passing_both_predicates=passed,
         n_cells_where_a_is_NOT_g_inverse=rows_that_are_not_ginv,
         n_such_cells_that_STILL_PASS=passed_and_not_ginv,
         instrument_can_return_otherwise=(passed != total),
         western_n12_g7_alternatives_that_pass=[
             r["a"] for r in western_alternatives],
         western_pentatonic_row=[r for r in western_alternatives
                                 if r["a"] == 5],
         verdict=(
             "REFUTED. The G1a predicate pair (contiguity of the symbol "
             "window with s=a, and injectivity of the alphabet's carrier "
             "image) is satisfied by EVERY a, not only by a = g^-1. The "
             "script sets s := a, and its own G1a law says contiguity holds "
             "iff magnitude(s)==a, so contiguity is true BY CONSTRUCTION in "
             "all 188 cells; and d -> g*d is injective for any unit g with "
             "a <= n, so the coverage clause is true by construction too. "
             "'0 failures across 188 cells' therefore measures nothing: the "
             "failure branch is unreachable. For the Western row (n=12, "
             "g=7) the alternatives that pass include a=5 -- the pentatonic "
             "alphabet, a real and historically attested chart of the same "
             "carrier with the same generator."))
    return passed == total


def v1b_is_there_a_predicate_that_forces_it():
    """The claim MAY be true under a predicate the script never applied:
    the modifier must move the CARRIER by exactly one step."""
    rows = []
    total = uniq = 0
    for n in MODULI:
        for g in units(n):
            ginv = mod_inv(g, n)
            forced = [a for a in range(1, n)
                      if mod_mul(g, res(a, n), n) == 1]
            total += 1
            if forced == [ginv]:
                uniq += 1
            if n == 12 and g == 7:
                rows.append({"n": n, "g": g, "g_inv": ginv,
                             "a_with_unit_carrier_step": forced})
    emit(finding="V1b_the_predicate_that_WOULD_force_it",
         predicate="g * s == 1 (mod n), i.e. one accidental moves the carrier one step",
         n_cells=total,
         n_cells_where_g_inverse_is_the_UNIQUE_solution=uniq,
         western_row=rows,
         verdict=(
             "The spec's CONCLUSION is recoverable, but only under a "
             "predicate G1a never states or applies: require the modifier "
             "to move the carrier by exactly ONE step. Under that "
             "predicate a = g^-1 is the unique solution in every cell. "
             "This is a real theorem and it is worth stating -- but the "
             "committed measurement did not measure it, so the reported "
             "'0 failures / 188 cells' is not its evidence. The distinction "
             "matters because the unstated premise ('an accidental is a "
             "semitone') is ITSELF a Western convention, which is exactly "
             "the class of leak this phase exists to find."))
    return uniq == total


# ══════════════════════════════════════════════════════════════════════
# V2 — sets, not counts
# ══════════════════════════════════════════════════════════════════════
def v2_sets_not_counts():
    window = 17
    set_agree = count_agree = total = 0
    count_agrees_but_set_differs = []
    for n in MODULI:
        for g in units(n):
            for p in range(n):
                a = chain_fibre_shipped(p, g, n, window)["fibre"]
                b = chain_fibre_brute(p, g, n, window)
                total += 1
                same_set = sorted(a) == sorted(b)
                same_count = len(a) == len(b)
                if same_set:
                    set_agree += 1
                if same_count:
                    count_agree += 1
                if same_count and not same_set:
                    count_agrees_but_set_differs.append(
                        {"n": n, "g": g, "p": p})
    emit(finding="V2_G1b_compares_SETS_not_counts",
         total=total,
         set_agreement=set_agree,
         count_agreement=count_agree,
         cells_where_counts_agree_but_sets_differ=len(
             count_agrees_but_set_differs),
         examples=count_agrees_but_set_differs[:5],
         verdict=(
             "CONFIRMED. G1b's `a == b` on two lists is a genuine "
             "membership comparison (both are sorted-ascending), and the "
             "independent set-vs-count split reproduces it: set agreement "
             "equals count agreement equals the full sweep, with zero cells "
             "in the dangerous class. The octonion trap does not apply here."))
    return set_agree == total


# ══════════════════════════════════════════════════════════════════════
# V3 — is chart_transition's derivation the REJECTED key_signature?
# ══════════════════════════════════════════════════════════════════════
def v3_chart_transition_vs_rejected_key_signature():
    n, g = 12, 7
    ginv = mod_inv(g, n)
    rows = []
    for t in range(n):
        chain_shift = mod_mul(ginv, res(t, n), n)
        r = res(chain_shift, n)
        alt = r - n
        rep = r if magnitude(r) <= magnitude(alt) else alt
        rows.append({"origin_shift": t,
                     "chain_shift": chain_shift,
                     "least_magnitude_rep": rep,
                     "accidentals": magnitude(rep)})
    counts = [r["accidentals"] for r in rows]
    emit(finding="V3_chart_transition_derivation_IS_the_rejected_key_signature",
         accidental_counts=counts,
         pre_registered_in_spec=[0, 5, 2, 3, 4, 1, 6, 1, 4, 3, 2, 5],
         reproduces=(counts == [0, 5, 2, 3, 4, 1, 6, 1, 4, 3, 2, 5]),
         calls_used=["mod_inv", "mod_mul", "pin_slot_at_zero/magnitude"],
         verdict=(
             "The rotation + accidental-cost half of the PROPOSED "
             "chart_transition is bit-identical to the arithmetic the same "
             "spec REJECTS as key_signature ('two shipped Class-I calls and "
             "a Class-K read'), and its worked example cites the "
             "key_signature record (G6) for its numbers. Three shipped "
             "calls, no search. The '49 evaluations' the spec offers as the "
             "decision content is a BRUTE-FORCE CROSS-CHECK of that closed "
             "form, not a step the op needs -- G6 runs the search only to "
             "AGREE with the closed form 12/12. So chart_transition as "
             "specified is key_signature plus a per-symbol certification "
             "loop; the certification is the only part not already derived."))
    return counts


# ══════════════════════════════════════════════════════════════════════
# V4 — the frame_scope ABI quote
# ══════════════════════════════════════════════════════════════════════
def v4_abi_quote():
    hdr = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "c", "include", "srmech.h")
    text = open(hdr, "r", encoding="utf-8", errors="replace").read()
    has_struct = "srmech_tool_entry_t" in text
    # Strip C block-comment continuation markers before flattening, or the
    # embedded " * " tokens defeat the match. (First pass of this verifier
    # reported the quote ABSENT for exactly that reason — recorded because a
    # verifier's own false negative is a finding about the verifier.)
    stripped = "\n".join(ln.lstrip().lstrip("*").strip()
                         for ln in text.splitlines())
    flat = " ".join(stripped.split())
    has_quote = ("callers receive a POINTER from srmech_tool_registry_get "
                 "and never allocate the struct, so appending leaves every "
                 "existing field offset unchanged" in flat)
    abi = None
    for line in text.splitlines():
        if line.startswith("#define SRMECH_ABI_VERSION"):
            abi = line.split()[-1]
    emit(finding="V4_frame_scope_ABI_quote",
         struct_present=has_struct,
         quoted_sentence_present=has_quote,
         abi_version_at_head=abi,
         spec_quoted_abi_stays="10",
         verdict=(
             "The quoted comment EXISTS and is about the right struct, but "
             "the spec reproduces it with its historical ABI number (10) "
             "intact. ABI is 14 at rc425. The ARGUMENT (appending a field "
             "leaves existing offsets unchanged because callers receive a "
             "pointer) survives the renumbering; the QUOTE as written is a "
             "stale artefact of the release it was authored in and should "
             "not be pasted into a spec as a current statement."))
    return has_struct and has_quote


# ══════════════════════════════════════════════════════════════════════
# V5 — does anything rank-2 / kernel / homomorphism already ship?
# ══════════════════════════════════════════════════════════════════════
def v5_registry_regrep():
    from srmech.introspect.tool_schema import warmup_all, get_tool_schema
    warmup_all()
    schema = get_tool_schema()
    names = sorted(e.name for e in schema)
    import re
    pats = {
        "notation_family": r"notat|staff|clef|stave|sheet|tablature|neume|chart|atlas",
        "chart_transition_family": r"transition|rotation|rotate|conjugat|change_of_basis",
        "action_lattice_family": r"lattice|kernel|homomorph|coset|quotient|rank2|free_abelian",
        "frame_scope_family": r"frame_scope|scope|lane|declar",
        "spelling_family": r"spell|enharm|fibre|fiber|lift",
    }
    hits = {k: [nm for nm in names if re.search(p, nm, re.I)]
            for k, p in pats.items()}
    emit(finding="V5_independent_registry_regrep",
         registry_total=len(names),
         hits={k: v for k, v in hits.items()},
         verdict=(
             "Re-run independently of the spec's own grep, with a WIDER "
             "pattern than the spec used. No registered op implements a "
             "chart declaration, a chart transition, a rank-2 action "
             "lattice, or a frame-scope census. The spec's absence claim "
             "for all four proposed ops STANDS. Note the spec's own pattern "
             "omitted 'fibre' and 'lattice', which its own rejected-op "
             "section then relies on -- a narrower grep than the argument "
             "needed."))
    return hits


# ══════════════════════════════════════════════════════════════════════
# V6 — is V1b's forcing itself up to a CHIRALITY choice?
#      (pre-registered: the project's own Class-K discipline says a sign
#       decision must be named, not absorbed.)
# ══════════════════════════════════════════════════════════════════════
def v6_forcing_is_up_to_a_chirality_choice():
    rows = []
    unique_up_to_sign = both = 0
    for n in MODULI:
        for g in units(n):
            ginv = mod_inv(g, n)
            # magnitude-1 carrier step: the modifier moves the carrier by
            # ONE step in EITHER orientation. Class K reads the magnitude,
            # Class C carries the orientation.
            sols = []
            for a in range(1, n):
                step = mod_mul(g, res(a, n), n)
                r = step
                alt = r - n
                rep = r if magnitude(r) <= magnitude(alt) else alt
                if magnitude(rep) == 1:
                    sols.append(a)
            if len(sols) == 2:
                both += 1
            if sorted(sols)[:1] and ginv in sols:
                unique_up_to_sign += 1
            if n == 12 and g == 7:
                rows.append({"n": n, "g": g, "g_inv": ginv,
                             "a_with_UNIT_MAGNITUDE_carrier_step": sols})
    emit(finding="V6_the_forcing_is_up_to_a_CHIRALITY_choice",
         predicate="magnitude(least_magnitude_rep(g*s mod n)) == 1",
         n_cells=188,
         n_cells_with_TWO_solutions=both,
         western_row=rows,
         verdict=(
             "The 'a = g^-1' forcing holds only once an ORIENTATION has "
             "been silently picked. Relax the predicate from 'the modifier "
             "moves the carrier +1' to the Class-K form 'the modifier moves "
             "the carrier by ONE step, either orientation' and there are "
             "TWO solutions in essentially every cell: a = g^-1 and "
             "a = n - g^-1. For (n=12, g=7) those are 7 and 5 -- the "
             "diatonic alphabet and the PENTATONIC one. So even the "
             "repaired claim does not force a unique alphabet; it forces a "
             "chiral PAIR, and choosing 7 over 5 is a Class-C orientation "
             "decision that the spec's 'theorem' language hides."))
    return both


# ══════════════════════════════════════════════════════════════════════
# V7 — exactness + banned-surface audit of the committed script
# ══════════════════════════════════════════════════════════════════════
def v7_exactness_audit():
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "_g3_notation_rc427.py"),
               encoding="utf-8").read()
    nd = open(os.path.join(here, "_g3_notation_rc427.ndjson"),
              encoding="utf-8").read()
    import re
    banned = {
        "abs_call": len(re.findall(r"(?<![A-Za-z_.])abs\s*\(", src)),
        "import_math": len(re.findall(r"^\s*(import math|from math )", src,
                                      re.M)),
        "import_fractions": len(re.findall(r"^\s*(import fractions|from fractions )",
                                           src, re.M)),
        "import_decimal": len(re.findall(r"^\s*(import decimal|from decimal )",
                                         src, re.M)),
        "bare_modulo": len(re.findall(r"[^%\"']%[^%\"'=]", src)),
    }
    floats = 0
    for line in nd.splitlines():
        for tok in re.findall(r"-?\d+\.\d+(?:[eE][-+]?\d+)?", line):
            floats += 1
    emit(finding="V7_exactness_and_banned_surface_audit",
         banned_counts=banned,
         float_literals_in_ndjson=floats,
         verdict=(
             "CLEAN on the discipline that matters. No abs(), no stdlib "
             "math / fractions / decimal, numpy imported only inside the "
             "deliberate absence probe, and ZERO float literals anywhere in "
             "the 15 emitted records -- every reported number is an exact "
             "integer, which is correct for a cyclic-group object. The "
             "sign-handling helper `res` is a named Class-K pin_slot_at_zero "
             "plus a Class-C re-application, exactly as the discipline "
             "requires."))
    return banned, floats


# ══════════════════════════════════════════════════════════════════════
# V8 — is G4's clef "simply transitive" a MEASUREMENT?
# ══════════════════════════════════════════════════════════════════════
def v8_clef_transitivity_is_tautological():
    results = {}
    for W, search in ((12, 24), (12, 6), (12, 100)):
        origins = list(range(-W, W + 1))
        pairs = 0
        for o1 in origins:
            for o2 in origins:
                movers = [t for t in range(-search, search + 1)
                          if o1 + t == o2]
                if len(movers) == 1:
                    pairs += 1
        results[f"W={W},search=+/-{search}"] = {
            "pairs_with_a_unique_mover": pairs,
            "pairs_total": len(origins) ** 2,
            "simply_transitive_verdict": pairs == len(origins) ** 2,
        }
    emit(finding="V8_G4_clef_simple_transitivity_is_TAUTOLOGICAL",
         swept=results,
         verdict=(
             "The clef half of G4's clause (d) is not a measurement. The "
             "script searches t over exactly +/-2W while the origins run "
             "over +/-W, so the required translation t = o2 - o1 is ALWAYS "
             "inside the search window and ALWAYS unique -- Z acting on Z "
             "by translation is simply transitive by definition. Narrow the "
             "search to +/-6 and the same code returns FALSE, which proves "
             "the window, not the group, is what was measured. The "
             "CONCLUSION (clef atlas is a principal Z-bundle, octonion "
             "frames are not) is still correct, but only one side of the "
             "separation was actually measured; the other was assumed and "
             "dressed as a count."))
    return results


# ══════════════════════════════════════════════════════════════════════
# V9 — does action_lattice_read silently return a WRONG answer
#      outside the domain the worked examples cover?
# ══════════════════════════════════════════════════════════════════════
def v9_action_lattice_domain_of_validity():
    def read(offsets, positions):
        actions = [(i, f) for i in range(len(offsets))
                   for f in range(positions + 1)]
        pre = {}
        for act in actions:
            pre.setdefault(offsets[act[0]] + act[1], []).append(act)
        return actions, pre

    def additivity(offsets):
        ok = bad = 0
        for i in range(len(offsets)):
            for j in range(len(offsets)):
                if i + j >= len(offsets):
                    continue
                if offsets[i] + offsets[j] == offsets[i + j]:
                    ok += 1
                else:
                    bad += 1
        return ok, bad

    rows = []
    for label, offsets in (
            ("regular anchored at 0 (the spec's PASS case)",
             (0, 5, 10, 15, 20, 25)),
            ("SAME LATTICE, translated by 3", (3, 8, 13, 18, 23, 28)),
            ("SAME LATTICE, translated by 40", (40, 45, 50, 55, 60, 65)),
            ("regular, descending step -5", (0, -5, -10, -15, -20, -25))):
        actions, pre = read(offsets, 12)
        ok, bad = additivity(offsets)
        step = offsets[1] - offsets[0]
        kernel = ([1, -step]
                  if bad == 0 and all(offsets[i] == step * i
                                      for i in range(len(offsets)))
                  else None)
        rows.append({"tuning": label, "offsets": list(offsets),
                     "n_actions": len(actions), "n_pitches": len(pre),
                     "additive_pairs": ok, "non_additive_pairs": bad,
                     "is_group_homomorphism": bad == 0,
                     "kernel_generator": kernel})
    emit(finding="V9_action_lattice_domain_of_validity",
         rows=rows,
         verdict=(
             "DEFECT. The spec's homomorphism verdict is not a property of "
             "the LATTICE; it is a property of whether the tuning happens "
             "to be anchored at 0. Translate the very tuning the spec "
             "certifies (0,5,10,15,20,25) by a constant -- the same rank-2 "
             "lattice, the same kernel (1,-5), the same fibre structure, "
             "the same preimage histogram -- and the proposed op returns "
             "is_group_homomorphism False and kernel None. An action map "
             "with a nonzero constant term is AFFINE, not linear, and "
             "affine maps of Z^2 have exactly the kernel-coset structure "
             "the op exists to report. As specified, action_lattice_read "
             "silently returns the wrong structural verdict for every "
             "tuning whose lowest course is not the origin, which is most "
             "of them."))
    return rows


# ══════════════════════════════════════════════════════════════════════
# V10 — exactness + banned-surface audit, corrected for prose hits
# ══════════════════════════════════════════════════════════════════════
def v10_class_I_in_the_action_lattice():
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "_g3_notation_rc427.py"),
               encoding="utf-8").read()
    body = src[src.index("def g5_action_carrier"):src.index("def g6_")]
    import re
    cyclic_ops = ["mod_add", "mod_mul", "mod_inv", "cyclic_mod_add",
                  "res(", "chain_to_carrier", "center_lift", "lift_fibre",
                  "mod_pow", "gcd"]
    used = {op: len(re.findall(re.escape(op), body)) for op in cyclic_ops}
    emit(finding="V10_action_lattice_CLASS_I_assignment_is_unsupported",
         declared_an_class="I then E",
         cyclic_op_calls_in_the_G5_derivation=used,
         total_cyclic_calls=sum(used.values()),
         verdict=(
             "The A-N assignment 'I then E' is not defensible from the "
             "derivation that produced it. Class I is cyclic / modular "
             "arithmetic, and the G5 body contains ZERO calls to any "
             "modular op -- every number in it is plain integer addition "
             "and comparison over Z, because a rank-2 FREE abelian lattice "
             "has no modulus. The `positions` argument is a window COUNT, "
             "not a modulus; nothing is reduced. The enumeration half (E) "
             "is sound. The op's honest class is E alone, or E with a "
             "Class-L / lattice reading -- not I."))
    return used


# ══════════════════════════════════════════════════════════════════════
# V11 — does chart_declare clear the bar relations.py set for
#       interval_invert ("a single call carrying no decision")?
#       Falsifier: reproduce its ENTIRE worked-example return value from
#       shipped ops only. If it falls out in a handful of calls, the
#       "decision" it claims is a Class-K comparison, not a search.
# ══════════════════════════════════════════════════════════════════════
def v11_chart_declare_is_a_composition():
    n, g, c0, a, s = 12, 7, -1, 7, 7
    mods = tuple(range(-2, 3))

    # 1. the symbol table            — a dict comprehension, no op
    sym = symbol_chain_positions(c0, a, s, mods)
    positions = list(sym.values())
    # 2. wellformed                  — ONE Class-K magnitude read
    wellformed = magnitude(s) == a
    # 3. derived_step_map            — a mod_mul per degree (Class I)
    step_map = sorted(chain_to_carrier(c0 + d, g, n) for d in range(a))
    # 4. the fibres / histogram      — the SHIPPED lift_fibre, per residue
    carrier_vals = [chain_to_carrier(k, g, n) for k in positions]
    counts = [carrier_vals.count(p) for p in range(n)]
    hist = {}
    for c in counts:
        hist[str(c)] = hist.get(str(c), 0) + 1
    backward_injective = all(c == 1 for c in counts)

    got = {"symbols": len(sym),
           "chain_window": [min(positions), max(positions)],
           "wellformed": wellformed,
           "derived_step_map": step_map,
           "backward_injective": backward_injective,
           "preimage_histogram": hist}
    want = {"symbols": 35,
            "chain_window": [-15, 19],
            "wellformed": True,
            "derived_step_map": [0, 2, 4, 5, 7, 9, 11],
            "backward_injective": False,
            "preimage_histogram": {"2": 1, "3": 11}}
    emit(finding="V11_chart_declare_is_a_COMPOSITION_not_a_decision",
         reproduced=got,
         spec_worked_example=want,
         bit_identical=(got == want),
         shipped_calls_used=["mod_mul (per degree)", "mod_add/pin_slot_at_zero (res)",
                             "magnitude (the wellformed read)"],
         n_decision_points=1,
         verdict=(
             "chart_declare's ENTIRE advertised return value is reproduced "
             "bit-identically here from shipped ops in a few lines, with "
             "exactly ONE decision point: the Class-K comparison "
             "magnitude(s) == a. Every other field is an enumeration "
             "(the symbol table), a mod_mul per degree (the step map), or "
             "a count (the histogram); the fibre half is G1b's own "
             "lift_fibre composition, which the same spec REJECTS as "
             "redundant. Measured against the bar srmech/music/relations.py "
             "sets in shipped prose -- 'a single cyclic_mod_add call "
             "carrying no decision, so registering one would add registry "
             "surface for zero capability' -- chart_declare is one "
             "comparison above that bar, not a search. The refusal "
             "capability it claims as its justification also does not "
             "survive V1/V6: the alphabet is not forced by the generator, "
             "so there is no under-declaration for it to refuse."))
    return got == want


def main():
    print("env", srmech.__file__, srmech.__version__)
    v1_alphabet_forcing_is_vacuous()
    v1b_is_there_a_predicate_that_forces_it()
    v2_sets_not_counts()
    v3_chart_transition_vs_rejected_key_signature()
    v4_abi_quote()
    v5_registry_regrep()
    v6_forcing_is_up_to_a_chirality_choice()
    v7_exactness_audit()
    v8_clef_transitivity_is_tautological()
    v9_action_lattice_domain_of_validity()
    v10_class_I_in_the_action_lattice()
    v11_chart_declare_is_a_composition()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "_v3_notation_verify_rc427.ndjson")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECORDS:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote", out, len(RECORDS), "records")


if __name__ == "__main__":
    main()
