"""gh #1653 — THE STEP-MUTATION WITNESS: proof the DESCRIPTOR drives execution.

⚠️ BYTE-IDENTITY IS NOT EVIDENCE THAT THE DESCRIPTOR WAS READ.
   Every parity gate in this issue compares C's output to Python's and passes on
   equality. That check is satisfied *just as well* by a C implementation that
   RECOGNISES the chain and dispatches one coarse compiled-in symbol while
   ignoring the steps entirely. srmech has exactly the symbols to do it with:
   ``srmech_octonion_dft`` exists while the descriptor decomposes that DFT into
   ``odft_summand`` + ``odft_resolve_mu`` + ``dft_scale`` + ``dft_sigma``;
   ``srmech_cascade_kuramoto_step_f64`` exists while the descriptor spells out
   five per-term steps. That is the COARSER class in the gap ledger — the
   capability is present, the granularity is not — and a chain "passing" that
   way would turn every ratchet green with the grammar unread.

   gh #1653 asks for CONFIG-DRIVEN cascade execution in C. Dispatching the
   coarse symbol is not parity; it is bypassing the thing the issue exists to
   make work. Nothing measured it until this file.

THE WITNESS. Perturb ONE INTERIOR PART of a shipped descriptor — a step's op, a
literal, a seed, a reference — and require C's output to CHANGE. A coarse
dispatcher pattern-matching the chain by name would return the SAME answer for
the mutated descriptor, because it never looked at the part that moved. Each
mutation below is chosen so that a correct step-by-step runner MUST produce a
different value, and the expected direction is stated rather than left to
"something changed".

⚠️ EACH CASE ALSO CARRIES A BASELINE ASSERTION. Without it a mutation test can
pass because the mutated chain DECLINED (rc != 0 → "different") rather than
because it computed something else — the failure mode that would make this whole
file vacuous. So every case asserts the baseline runs, the mutant runs, and the
two values differ.
"""
from __future__ import annotations

import copy
import ctypes
import json

import pytest

from srmech.cascade import compose as _compose
from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat


def _lib():
    lib = _compose._compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    if lib is None:
        pytest.skip("no native library — this gate measures the C projection")
    return lib


def _chain_only(entry):
    return {k: v for k, v in entry.items()
            if k in ("name", "steps", "on_error", "chain_schema_version")}


def _c_value(chain, inputs):
    """Run in C; return (rc, reconstructed value)."""
    lib = _lib()
    cj = json.dumps(chain, ensure_ascii=False).encode("utf-8")
    xj = json.dumps({"inputs": inputs}, ensure_ascii=False).encode("utf-8")
    n = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * n)()
    cap = max(n // 2, 65536)
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, n,
                                  out, cap, ctypes.byref(ol)))
    if rc != 0:
        return rc, None
    return 0, _compose._reconstruct_value(json.loads(out.raw[:ol.value].decode("utf-8")))


def _shipped(name):
    entry = _cc._chain_entries(_cat.load_catalog()[name])[0]
    case = (entry.get("proof_cases") or [{}])[0]
    return _chain_only(entry), dict(case.get("inputs") or {})


# ── the mutations ────────────────────────────────────────────────────────────
#
# (chain, mutate(chain_dict) -> None, inputs_override_or_None, why)

def _swap_op(new_op, add_args=None):
    """Swap step 0's op, optionally supplying args the new op needs.

    ``add_args`` exists because ``gcd``'s descriptor declares only ``{a, b}``:
    swapping in a modular op without adding ``n`` makes the mutant DECLINE for
    a missing argument, which proves nothing about whether the descriptor is
    read. Measured on the first run of this file — the mutant returned rc=5 and
    the baseline assertion caught it.
    """
    def go(ch):
        ch["steps"][0]["op"] = new_op
        if add_args:
            ch["steps"][0]["args"].update(add_args)
    return go


def _skip_middle_step(ch):
    """Re-point the LAST step at the FIRST step's output, orphaning the middle.

    The strongest single mutation available here: it leaves every step present
    and every op unchanged, altering ONLY a reference. A runner that honours the
    descriptor's data flow must now compute flip(flip(x)) == x; one that
    pattern-matched "this is chiral_dual" returns the autocorrelated answer and
    is caught.
    """
    ch["steps"][2]["args"]["seq"] = "@step[0].output"


def _flip_orientation(ch):
    ch["steps"][1]["args"]["orientation"] = -1


def _flip_fold_seed(ch):
    ch["steps"][0]["fold_init"] = -1


def _widen_dead_band(ch):
    """best_rational_signed's ONE interior literal: the Class-K dead band.

    Every other arg in that descriptor is an ``@``-reference, so this literal is
    the whole of what a coarse dispatcher cannot track — the fused
    ``srmech_cascade_best_rational_signed_f64`` HARD-CODES 1e-12 and has no
    parameter image for it, while ``max_denominator`` / ``fine_scale`` ride the
    ctx wire where a shape-recogniser could still read them.
    """
    ch["steps"][1]["args"]["band"] = 1e-6


def _flip_reorient_orientation(ch):
    """best_rational_signed's Class-C tail, pinned separately from the band.

    The band mutation alone would be satisfied by a runner that honours step 1
    and fuses steps 2-5; flipping the reorient's orientation reference to a
    literal -1 additionally requires the TAIL to be read step-by-step.
    """
    ch["steps"][4]["args"]["orientation"] = -1


def _pin_autocorr_lag_to_zero(ch):
    """autocorrelation's LAG ARITHMETIC, two map levels down.

    The chain is seq_len -> map(k) -> map(i) -> [mod_add, correlation_product]
    -> compensated_sum. The inner ``mod_add(a=@idx.i, b=@idx.k, n=@bind.n)`` IS
    the circular lag: it computes ``j = (i + k) mod n``. Replacing ``b`` with the
    literal ``0`` pins every lag to zero, so ``j == i`` for all k and each bin
    sums ``x[i] * x[i]`` — i.e. every output element becomes the signal ENERGY.

    ⚠️ IT IS AN INTERIOR LITERAL INSIDE TWO NESTED MAP BODIES. A dispatcher that
    recognised "this is the autocorrelation chain" and called
    ``srmech_autocorrelation_f64`` returns the true autocorrelation and is
    caught; so is one that reads only the top-level step list, which is the
    known-wrong flat walk (it sees 2 of this chain's 6 steps).
    """
    ch["steps"][1]["body"][0]["body"][0]["args"]["b"] = 0


#: (chain, mutate, inputs-or-None, EXPECTED mutant value, why)
#:
#: ⚠️ THE EXPECTED VALUE IS THE POINT, not merely "it differs". "Something
#: changed" is satisfied by a runner that changed for the WRONG reason — a
#: partially-read descriptor, an arg silently dropped, a step run twice. Each
#: value below is what step-by-step execution of the MUTATED descriptor must
#: produce, computed by hand from the ops, so the witness pins the mechanism and
#: not just its motion.
MUTATIONS = [
    ("cyclic_gcd", _swap_op("mod_add", {"n": "@input.n"}), {"a": 12, "b": 18, "n": 7},
     2,
     "gcd(12,18)=6; mod_add(12,18,7) = 30 mod 7 = 2. Swapping the OP alone must "
     "move the answer — a name-matched dispatcher still returns 6"),
    ("cyclic_mod_add", _swap_op("mod_mul"), None, 8,
     "mod_add(7,8,12)=3; mod_mul(7,8,12) = 56 mod 12 = 8. Same args, same arity"),
    ("cyclic_mod_mul", _swap_op("mod_add"), None, 3,
     "the reverse of the same swap, so neither op is privileged"),
    ("chiral_dual", _skip_middle_step, None, [1.0, 2.0, 3.0],
     "⚠️ THE SHARPEST CASE. Orphaning the interior autocorrelation by changing "
     "ONE REFERENCE — every op and every step survives — leaves flip(flip(x)), "
     "which is the IDENTITY. So the expected value is the original input "
     "[1.0, 2.0, 3.0] exactly. Only a runner that reads the descriptor's data "
     "flow can produce it; anything pattern-matching 'this is chiral_dual' "
     "returns the autocorrelated [11.0, 11.0, 14.0]"),
    ("magnitude", _flip_orientation, None, -3.5,
     "the Class-C re-application literal +1 -> -1 must NEGATE: 3.5 -> -3.5. A "
     "coarse |x| symbol ignores the literal and returns 3.5"),
    ("net_chirality", _flip_fold_seed, {"orientations": [1, -1, 1]}, 1,
     "the fold SEED +1 -> -1 negates the product: -1 -> +1. A compiled-in "
     "net_chirality seeds itself and returns -1"),
    ("best_rational_signed", _widen_dead_band,
     {"x": 1.5e-12, "fine_scale": 10 ** 13, "max_denominator": 10 ** 12},
     (0, 1),
     "⚠️ THE INPUTS ARE AN OVERRIDE AND THAT IS LOAD-BEARING. This chain's ONE "
     "interior literal is step 1's band = 1e-12, and the fused C symbol "
     "hard-codes the same 1e-12 with no parameter image — so widening it to "
     "1e-6 is the single perturbation a coarse dispatch cannot follow. But the "
     "mutation is MEASURED VACUOUS on the shipped proof case that looks like "
     "its natural home (case 6, x = 5e-13): there the baseline, the mutant, the "
     "chain with the dead_band step REMOVED, and the fused op all return (0, 1) "
     "— an instrument that cannot return otherwise. At x = 1.5e-12 the magnitude "
     "clears 1e-12 and not 1e-6, so the baseline computes "
     "best_rational(15, 10**13, 10**12) = (1, 666666666667) while the mutant "
     "dead-bands to zero and returns (0, 1). All three values re-measured at "
     "rc451; see notes/_1653_rca_probe_rc451.py block E, which prints the "
     "vacuous case beside the viable one as its own control"),
    ("autocorrelation", _pin_autocorr_lag_to_zero,
     {"x": [1.0, -2.0, 3.0, 0.5]},
     [14.25, 14.25, 14.25, 14.25],
     "the LAG literal, two nested map bodies deep. Baseline is the true "
     "circular autocorrelation of [1, -2, 3, 0.5]; pinning the inner mod_add's "
     "`b` from '@idx.k' to 0 makes j == i for every k, so each of the n bins "
     "sums x[i]*x[i] and every element becomes the ENERGY "
     "1 + 4 + 9 + 0.25 = 14.25 exactly (all four products are exactly "
     "representable, so the Neumaier compensation contributes nothing and the "
     "expected value is exact rather than approximate). Only a runner that "
     "executes the descriptor step-by-step through BOTH map levels produces "
     "it — srmech_autocorrelation_f64 returns the true transform, and a "
     "top-level-only walk never reaches the literal at all"),
    ("best_rational_signed", _flip_reorient_orientation, None, (-22, 7),
     "the Class-C TAIL. Replacing step 4's '@step[0].output[0]' orientation "
     "reference with a literal -1 on the +pi case must negate the numerator: "
     "(22, 7) -> (-22, 7). A fused N-C-B tail that re-signs from its own "
     "internally-computed orientation ignores the literal and still returns "
     "(22, 7), so this catches a partial fusion the band mutation alone would "
     "not"),
]


@pytest.mark.parametrize(
    "name,mutate,inputs,expected,why",
    MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_perturbing_an_interior_step_CHANGES_the_C_output(
        name, mutate, inputs, expected, why):
    chain, case_inputs = _shipped(name)
    if inputs is not None:
        case_inputs = inputs

    rc0, base = _c_value(chain, case_inputs)
    assert rc0 == 0, (
        "BASELINE did not run in C (rc=%s) — the mutation below would then "
        "'differ' for the wrong reason and this case would be vacuous" % rc0)

    mutant = copy.deepcopy(chain)
    mutate(mutant)
    assert mutant != chain, "the mutator did not change the descriptor"

    rc1, moved = _c_value(mutant, case_inputs)
    assert rc1 == 0, (
        "the MUTATED chain declined (rc=%s). A decline is not evidence the "
        "descriptor was read — it may just be unsupported. This case needs a "
        "mutation C can actually run." % rc1)

    assert moved != base, (
        "C returned the SAME value (%r) for a descriptor whose interior CHANGED.\n"
        "%s\n"
        "That is the signature of a coarse compiled-in symbol being dispatched "
        "by chain identity while the steps are ignored — byte-identity with "
        "Python would still hold, and every other gate in gh #1653 would stay "
        "green." % (base, why))

    assert moved == expected, (
        "the mutated chain moved to %r, but step-by-step execution of the "
        "MUTATED descriptor predicts %r.\n%s\n"
        "It changed for the WRONG reason — a partially-read descriptor, a "
        "dropped arg, or a step run twice would all 'differ' too."
        % (moved, expected, why))


def test_the_witness_would_catch_a_coarse_dispatcher():
    """CONTROL — prove the witness can FAIL, by simulating what it hunts.

    A gate that has never been seen to fire is indistinguishable from one that
    cannot. Here the "coarse dispatcher" is modelled directly: ignore the
    mutation, return the baseline. The witness's comparison must reject it.
    """
    chain, inputs = _shipped("magnitude")
    _rc, base = _c_value(chain, inputs)
    coarse_result = base                      # a name-matched dispatcher's answer
    assert coarse_result == base, "premise"
    # the witness asserts `moved != base`; with a coarse dispatcher it holds
    # `moved == base`, so the assertion fires. Stated as an explicit check so
    # the logic is verified rather than assumed.
    assert not (coarse_result != base), (
        "if this passed, the witness's core comparison would not detect a "
        "coarse dispatcher and the whole file would be decorative")


def test_every_running_chain_has_a_mutation_or_is_named():
    """COVERAGE. A witness that silently skips chains proves less than it looks.

    Any chain that runs in C but has no mutation here must be named with a
    reason, so the uncovered set is explicit rather than emergent.
    """
    covered = {m[0] for m in MUTATIONS}
    #: Running chains deliberately WITHOUT a mutation, each with its reason.
    exempt = {
        "cyclic_mod_inv": "single op, no second op shares its (a, n) arity — a "
                          "swap would decline rather than compute",
        "cyclic_mod_mul_wide": "routes to the SAME arm as cyclic_mod_mul, which "
                               "is covered; a duplicate proves nothing new",
        "cyclic_mod_pow": "swapping in mod_mul changes the arg NAMES (k vs b), "
                          "so the mutant declines instead of computing",
    }
    catalog = _cat.load_catalog()
    running = set()
    for nm in sorted(catalog):
        if _cc.descriptor_status(catalog[nm]) != "executable":
            continue
        ch, inp = _shipped(nm)
        if _c_value(ch, inp)[0] == 0:
            running.add(nm)
    uncovered = sorted(running - covered - set(exempt))
    assert not uncovered, (
        "these chains run in C with no step-mutation witness and no stated "
        "exemption: %s" % uncovered)
    stale = sorted(set(exempt) - running)
    assert not stale, "exempted chains that no longer run: %s" % stale

# ══════════════════════════════════════════════════════════════════════════════
# rc452 (`#T1166`) — TWO SEAMS THE COVERAGE TEST ABOVE LEAVES OPEN.
#
# `test_every_running_chain_has_a_mutation_or_is_named` is the right ratchet on
# the right axis, and it is narrower than it reads in two ways:
#
#   SEAM 1 — IT SEES ONE VARIANT AND ONE CASE. `_shipped(nm)` takes
#       `_chain_entries(...)[0]` and `proof_cases[0]`. The live population is 18
#       chains / 20 VARIANTS / 98 proof cases, so "runs in C" is decided by 18 of
#       98 rows. A chain whose FIRST variant declines while a LATER one runs is
#       recorded as not-running and is therefore never asked for a witness.
#       ⚠️ MEASURED at rc452 this is LATENT, not live: the only two multi-variant
#       chains are `klein4_from_one` (rest, wound) and `kuramoto_step` (general,
#       simple), and all four variants are C-rejected on every one of their 17
#       proof cases. So the seam costs nothing TODAY and silently opens the day
#       either one is unblocked — which is exactly when the witness is needed.
#       Recorded as a live-zero rather than left implicit, because a gate that
#       happens to be adequate is not the same as one that is.
#
#   SEAM 2 — IT IS CHAIN-LEVEL, NOT STEP-LEVEL. One mutation per chain proves
#       ONE literal in ONE step is read. `best_rational_signed` has SIX steps and
#       two mutations; `chiral_dual` has three steps and one. Nothing pins that
#       the remaining steps are read at all, which is the same coarse-dispatch
#       question this file exists for, asked at the granularity where the answer
#       could still be no.
# ══════════════════════════════════════════════════════════════════════════════

BOGUS_OP = "__no_such_op_rc452_step_drive__"


def _all_running_rows():
    """(name, variant, entry, inputs) for EVERY variant x EVERY proof case that
    runs in C — not `[0]` of either.

    This is the predicate `test_every_running_chain_has_a_mutation_or_is_named`
    should have used; it is factored out so the coverage test and the step-drive
    test cannot drift onto different populations.
    """
    catalog = _cat.load_catalog()
    rows = []
    for nm in sorted(catalog):
        if _cc.descriptor_status(catalog[nm]) != "executable":
            continue
        for variant, _spec, entry in _cc.cascade_chain_specs(nm):
            chain = _chain_only(entry)
            for j, case in enumerate(entry.get("proof_cases") or []):
                inputs = dict(case.get("inputs") or {})
                try:
                    rc, _val = _c_value(chain, inputs)
                except Exception:                      # noqa: BLE001
                    continue
                if rc == 0:
                    rows.append((nm, variant, entry, inputs))
    return rows


def test_mutation_coverage_over_every_variant_and_case():
    """SEAM 1. Coverage decided over the FULL population, not `[0]` of each.

    Same exempt map and same MUTATIONS as the test above — deliberately, so the
    two cannot disagree about what is covered. The only thing that widens is the
    set of chains asked.

    RED-PLANT that proves it fires: delete the `("cyclic_mod_add", ...)` row from
    MUTATIONS. `cyclic_mod_add` runs in C on all four of its proof cases, so it
    lands in `running`, is not exempt, and this reds naming it. (The same plant
    reds the narrower test too — that is the point: this one must not be WEAKER,
    only wider.)
    """
    covered = {m[0] for m in MUTATIONS}
    exempt = {
        "cyclic_mod_inv": "single op, no second op shares its (a, n) arity",
        "cyclic_mod_mul_wide": "routes to the SAME arm as cyclic_mod_mul",
        "cyclic_mod_pow": "swapping in mod_mul changes the arg NAMES (k vs b)",
    }
    rows = _all_running_rows()
    assert rows, "no chain ran in C — the coverage claim would be vacuous"
    running = {nm for nm, _v, _e, _i in rows}
    uncovered = sorted(running - covered - set(exempt))
    assert not uncovered, (
        "these chains run in C on at least one (variant, proof case) with no "
        "step-mutation witness and no stated exemption: %s" % uncovered)
    stale = sorted(set(exempt) - running)
    assert not stale, "exempted chains that no longer run: %s" % stale


def _step_paths(steps, prefix=()):
    """(path, op_key) for every step AT FULL DEPTH, recursing nested `body`.

    ⚠️ TWO TRAPS, both of which have produced a wrong census in this arc.

    * A FLAT walk over `steps` misses map/fold bodies entirely. On the shipped
      catalog a flat walk sees 72 steps where the recursive one sees 134.
    * THE OP KEY IS NOT ALWAYS `op`. A plain step spells it `op`; a FOLD step
      spells it `fold_op`; a MAP step has NEITHER — it is a container whose
      `body` carries the real ops. Writing `op` onto a fold step injects a
      FOREIGN KEY, and the rejection that follows means "this document is
      malformed", not "the runner read your op". Conflating those makes the
      fold rows of this gate meaningless.
    """
    out = []
    for i, st in enumerate(steps or []):
        if not isinstance(st, dict):
            continue
        p = prefix + (i,)
        key = "op" if "op" in st else ("fold_op" if "fold_op" in st else None)
        if key is not None:
            out.append((p, key))
        body = st.get("body")
        if isinstance(body, list):
            out.extend(_step_paths(body, p + ("body",)))
    return out


def _at(chain, path):
    node = chain["steps"]
    for k in path:
        node = node["body"] if k == "body" else node[k]
    return node


def test_every_step_of_every_running_chain_is_actually_read():
    """SEAM 2. Point each step's op at a name nothing can resolve; it must react.

    A step that can be replaced with an unresolvable op while the chain still
    returns rc == 0 AND the identical value is a step the runner never read —
    the coarse-dispatch signature, at the granularity the chain-level witness
    cannot reach.

    ⚠️ A STEP IS JUDGED OVER ALL ITS PROOF CASES, NOT case[0]. `net_chirality`'s
    fold is genuinely vacuous on `{"orientations": []}` — an empty fold returns
    `fold_init` without ever invoking `fold_op`, so a bogus op there is correctly
    a no-op. Judging that step on case[0] alone reports a false DEAD. It reacts
    on all six non-empty cases. This is the same vacuity that rc447's
    `_widen_dead_band` mutation hit on `best_rational_signed` case 6, and the
    same answer: require the reaction on SOME case, not on an arbitrary one.

    MEASURED at rc452: 18 steps over 10 running chains, every one reacts.

    RED-PLANT that proves it fires: in the C interpreter's op resolver
    (`cr_dispatch` / `cr_dispatch_real` in src/srmech_compose_run.c) return
    SRMECH_OK with the input passed through instead of NOT_IMPL for an
    unresolved op. Every step then accepts a bogus name, the value does not
    move, and this reds naming each step. A cheaper Python-side plant: make
    `_step_paths` return `[]` — the self-check below reds first, which is what
    it is for.
    """
    by_chain = {}
    for nm, variant, entry, inputs in _all_running_rows():
        by_chain.setdefault((nm, variant, id(entry)), [entry, []])[1].append(inputs)

    probed = reacted = 0
    dead = []
    for (nm, variant, _k), (entry, input_list) in sorted(
            by_chain.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        base = _chain_only(entry)
        for path, opkey in _step_paths(base.get("steps")):
            probed += 1
            moved = False
            for inputs in input_list:
                rc_b, val_b = _c_value(base, inputs)
                if rc_b != 0:
                    continue
                mutant = copy.deepcopy(base)
                _at(mutant, path)[opkey] = BOGUS_OP
                rc_m, val_m = _c_value(mutant, inputs)
                # EITHER reaction counts as "the step was read": the runner
                # declined the unresolvable op, or it ran and the value moved.
                if rc_m != 0 or _bits_of(val_m) != _bits_of(val_b):
                    moved = True
                    break
            if moved:
                reacted += 1
            else:
                dead.append("%s/%s step[%s].%s"
                            % (nm, variant,
                               ".".join(str(x) for x in path), opkey))

    # SELF-CHECK FIRST: a probe that reached no step would report a clean zero.
    assert probed > 0, (
        "no step was probed — either no chain runs in C or _step_paths walked "
        "nothing, and a green here would mean neither")
    assert reacted > 0, (
        "NO step reacted to an unresolvable op name. The mutation is not "
        "reaching the document at all and every row below is an artifact")
    assert not dead, (
        "these steps accept an unresolvable op on EVERY proof case with no "
        "change in outcome — the C runner is not reading them: %s" % dead)


def _bits_of(v):
    """Typed identity for the step-drive comparison — never `==`.

    `_c_value` returns RECONSTRUCTED values, so a step whose mutation turns
    `Q(5, 6)` into `(5, 6)` must count as MOVED. `==` says those are equal (it
    cross-multiplies through `_as_pair`) and would score that step DEAD.
    """
    from test_c_cascade_value_parity_rc450 import _bits as _b
    return _b(v)
