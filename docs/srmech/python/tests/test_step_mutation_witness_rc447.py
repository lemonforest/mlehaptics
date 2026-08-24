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
    # rc452 (gh #1653 finding (b)): the runner now REFUSES a headerless chain
    # (name/summary/returns required — the rule every parse layer already
    # enforced), so the harness synthesizes the header the way
    # cascade_chain_specs does. See the rc446 ratchet's _chain_only docstring
    # for the full finding; this copy stays a copy on purpose (standalone
    # collection), matching the value-parity file's.
    out = {k: v for k, v in entry.items()
           if k in ("name", "summary", "returns", "steps", "on_error",
                    "chain_schema_version")}
    out.setdefault("name", str(entry.get("variant", "chain")))
    out.setdefault("summary", "")
    out.setdefault("returns", "")
    return out


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


def _pin_mod_inv_modulus(ch):
    """cyclic_mod_inv — the rc452 exemption FALSIFIED, first of three.

    The exemption read "single op, no second op shares its (a, n) arity — a
    swap would decline rather than compute". True, and beside the point: a
    witness does not need an OP swap. Pinning the modulus REFERENCE to a
    literal is a one-line argument mutation the runner executes.
    """
    ch["steps"][0]["args"]["n"] = 11


def _pin_mul_wide_factor(ch):
    """cyclic_mod_mul_wide — second falsified exemption.

    "Routes to the SAME arm as cyclic_mod_mul, which is covered" — also true,
    also beside the point: THIS chain's own descriptor was never witnessed,
    and a dispatcher keyed on THIS chain's name would have passed unread.
    Shared arm or not, the document is its own subject.
    """
    ch["steps"][0]["args"]["b"] = 9


def _pin_pow_exponent(ch):
    """cyclic_mod_pow — third falsified exemption.

    "Swapping in mod_mul changes the arg NAMES (k vs b), so the mutant
    declines" — true of the swap, irrelevant to the witness: mutate the
    EXPONENT argument instead and the mutant computes.
    """
    ch["steps"][0]["args"]["k"] = 4


def _pin_kuramoto_dt(ch):
    """kuramoto_step (simple variant): the outer map's `dt` BIND reference
    pinned to the literal 0 — an interior edit the fused kuramoto symbols
    cannot see (they read dt from the ctx wire, not from the bind table)."""
    ch["steps"][2]["bind"]["dt"] = 0


def _bump_qdft_fold_seed(ch):
    """quaternion_dft: the Σ_m fold seed inside the outer map's body."""
    ch["steps"][5]["body"][1]["fold_init"] = [1.0, 0.5, 0.0, 0.0]


def _bump_odft_fold_seed(ch):
    """octonion_dft: the Σ_m fold seed inside the outer map's body."""
    ch["steps"][6]["body"][1]["fold_init"] = [1.0, 0.0, 0.0, 0.0,
                                              0.0, 0.0, 0.0, 0.25]


def _zero_klein4_frame(ch):
    """klein4_from_one (rest): the (1,3,7,3) sector-mask BIND table zeroed.

    `frame14` is an interior LITERAL of the map step's bind block —
    `srmech_klein4_from_one` (the fused whole-address symbol) hard-codes the
    same period-14 mask and has no parameter image of the descriptor's table,
    so a dispatcher keyed on this chain's name returns the MASKED address and
    is caught. With the mask all-zero the V4 Cayley XOR is against 0 =
    identity, so the expected value is the chain's own crumbs UNMASKED — a
    hand-derivable prediction (see the MUTATIONS row).
    """
    ch["steps"][9]["bind"]["frame14"] = [0] * 14


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
    # ── rc452 (`#T1166`) Phase 2: the three chains that were EXEMPT, each with
    # the witness its exemption claimed impossible. All three exemptions were
    # justified solely by prose about OP swaps; every one is answered by a
    # ONE-LINE ARGUMENT mutation, verified by execution before landing here.
    ("cyclic_mod_inv", _pin_mod_inv_modulus, None, 4,
     "mod_inv(3, 7) = 5; pinning the modulus reference '@input.n' to the "
     "literal 11 gives mod_inv(3, 11) = 4 (3*4 = 12 === 1 mod 11). The rc452 "
     "exemption claimed no witness exists because no op SWAP computes; the "
     "witness needed an argument, not a swap"),
    ("cyclic_mod_mul_wide", _pin_mul_wide_factor, None, 3,
     "mod_mul_wide(7, 8, 12) = 8; pinning b to 9 gives 63 mod 12 = 3. A "
     "coarse dispatcher keyed on this chain's NAME returns 8 — the shared "
     "dispatch arm the exemption cited never made this descriptor read"),
    ("cyclic_mod_pow", _pin_pow_exponent, None, 1,
     "mod_pow(3, 7, 10) = 2187 mod 10 = 7; pinning the exponent k to 4 gives "
     "81 mod 10 = 1. The k-vs-b arg-name mismatch the exemption cited blocks "
     "an op swap, not an argument mutation"),
    # ── rc452 Phase 3 (`#T1166`): the three newly-unblocked map chains, each
    # witnessed through an INTERIOR literal the fused whole-transform symbol
    # has no parameter image of, with the expected value derivable EXACTLY by
    # hand (no float derivation is trusted to narration).
    ("kuramoto_step", _pin_kuramoto_dt, None, [0.1, 2.0, -1.0],
     "pin the OUTER MAP's bind `dt` reference to the literal 0. The combine is "
     "float(theta_i + float(dt)*(om + inv_n*s)): with dt = 0 the exact-Q "
     "product 0*(...) is Q(0, 1) and theta_i + 0 collapses to theta_i EXACTLY, "
     "so the mutant returns the input phases [0.1, 2.0, -1.0] verbatim. "
     "srmech_cascade_kuramoto_step_f64 exists, reads dt from the CTX wire, and "
     "has no image of the descriptor's bind table — a dispatcher keyed on this "
     "chain's name returns the baseline (moved phases) and is caught"),
    ("quaternion_dft", _bump_qdft_fold_seed,
     {"x": [[1.0, 2.0, 3.0, 4.0]], "mu_axis": "j", "inverse": False,
      "left": True},
     [[2.0, 2.5, 3.0, 4.0]],
     "the Σ_m fold SEED, one map level down. On the N=1 'single' case the "
     "twiddle angle is σ·2π·(0·0 mod 1)/1 = 0, so W = exp(0) = [1,0,0,0] and "
     "L_W is the identity: the summand IS x[0] and scale = 1.0. Bumping the "
     "seed [0,0,0,0] -> [1.0, 0.5, 0, 0] must move the spectrum to "
     "[[1+1, 0.5+2, 3, 4]] = [[2.0, 2.5, 3.0, 4.0]] — every add exact. "
     "srmech_quaternion_dft seeds its own accumulator and returns the "
     "baseline [[1, 2, 3, 4]], so a coarse dispatch is caught"),
    ("octonion_dft", _bump_odft_fold_seed,
     {"x": [[1.0, 2.0, 3.0, 4.0]], "mu_axis": "e4", "mu_r_axis": "e4",
      "form": "left", "bracketing": "left_associated", "inverse": False},
     [[2.0, 2.0, 3.0, 4.0, 0.0, 0.0, 0.0, 0.25]],
     "the octonion twin of the QDFT seed witness, on the 'quat_embed' N=1 "
     "case: as_oct8 zero-extends [1,2,3,4] into O, the k=m=0 twiddle is the "
     "identity, scale = 1.0. Seed [0]*8 -> [1.0, 0, 0, 0, 0, 0, 0, 0.25] "
     "moves the spectrum to [[2.0, 2.0, 3.0, 4.0, 0, 0, 0, 0.25]] exactly; "
     "srmech_octonion_dft has no image of the seed and is caught"),
    # ── rc452 (gh #1653): klein4_from_one, unblocked in the registry-ripple
    # phase. The mask table is an interior BIND literal; zeroing it makes the
    # V4 XOR the identity, so the prediction is the UNMASKED crumb sequence —
    # derived INDEPENDENTLY of srmech: coreutils sha256sum over the preimage
    # {"sigma":1,"terms":24,"theta":[1,1]} gives h =
    # 5ee9cb2584d75d0374b481b86108c422d52a47c413b2bfb8bd40f8236dc6514e, then
    # sha256sum over h||"|0" gives the counter-block digest
    # a6a8e26568ca872670d49f75caeb60ed20eb07a779d10d5d8021407f6b10b2c9, and
    # per hex byte the four crumbs are (lo%4, lo//4, hi%4, hi//4) — the FIPS
    # digest plus grade-school base-4 arithmetic, no srmech call anywhere in
    # the derivation.
    ("klein4_from_one", _zero_klein4_frame, None,
     [2, 1, 2, 2, 0, 2, 2, 2, 2, 0, 2, 3, 1, 1, 2, 1,
      0, 2, 2, 1, 2, 2, 0, 3, 3, 1, 0, 2, 2, 1, 2, 0,
      0, 0, 3, 1, 0, 1, 1, 3, 3, 3, 1, 2, 1, 1, 3, 1,
      2, 2, 0, 3, 3, 2, 2, 3, 0, 0, 2, 1, 1, 3, 2, 3],
     "zero the (1,3,7,3) frame BIND table on the rest case 0: XOR against 0 "
     "is the identity, so the mutant must return the RAW crumbs of counter "
     "block 0 — the 64 values above, hand-derived from the independent "
     "sha256sum digest a6a8e265... . The fused srmech_klein4_from_one "
     "hard-codes the mask and returns the MASKED baseline, so a coarse "
     "dispatch is caught; so is a runner that reads only the top-level step "
     "list, which never meets the bind table at all"),
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

    ⚠️ THE EXEMPTION MECHANISM IS GONE — rc452 (`#T1166`) Phase 2. Through the
    first half of rc452 this test carried a three-entry ``exempt`` map
    (``cyclic_mod_inv`` / ``cyclic_mod_mul_wide`` / ``cyclic_mod_pow``), each
    justified solely by prose about why an OP SWAP would decline. All three
    justifications were TRUE and all three exemptions were FALSE: each chain
    carries a value-predicted witness via a one-line ARGUMENT mutation, now in
    MUTATIONS with its expected value. An exemption is a claim that no witness
    exists, and that claim is only ever provable by execution — three prose
    exemptions went 0-for-3 against one afternoon of trying, so the mechanism
    itself is removed. A chain that runs with no witness FAILS here until it
    has one; if a witness is ever genuinely impossible, prove it by execution
    in a test beside this one, not by a string in a dict.
    """
    covered = {m[0] for m in MUTATIONS}
    catalog = _cat.load_catalog()
    running = set()
    for nm in sorted(catalog):
        if _cc.descriptor_status(catalog[nm]) != "executable":
            continue
        ch, inp = _shipped(nm)
        if _c_value(ch, inp)[0] == 0:
            running.add(nm)
    assert running, "no chain ran in C — the coverage claim would be vacuous"
    uncovered = sorted(running - covered)
    assert not uncovered, (
        "these chains run in C with no step-mutation witness: %s" % uncovered)

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
#       ⚠️ When this banner was written the seam was LATENT (all four
#       multi-variant rows — klein4_from_one rest/wound, kuramoto_step
#       simple/general — were C-rejected on every proof case), and its own
#       prediction fired TWICE inside rc452: kuramoto's unblock measured the
#       seam LIVE (see _all_running_rows' comment) and klein4's closure walked
#       through the widened population from day one. All four variants RUN
#       now; the wider tests below are what covers them, and this narrower
#       test stays as the cheap first line.
#
#   SEAM 2 — IT IS CHAIN-LEVEL, NOT STEP-LEVEL. One mutation per chain proves
#       ONE literal in ONE step is read. `best_rational_signed` has SIX steps and
#       two mutations; `chiral_dual` has three steps and one. Nothing pins that
#       the remaining steps are read at all, which is the same coarse-dispatch
#       question this file exists for, asked at the granularity where the answer
#       could still be no.
# ══════════════════════════════════════════════════════════════════════════════

BOGUS_OP = "__no_such_op_rc452_step_drive__"

#: rc452 (`#T1171`) — the population `test_every_step_of_every_running_chain_is
#: _actually_read` walks, pinned so the figure in its docstring cannot rot. Both
#: MEASURED at rc452 with a freshly built libsrmech (HAS_NATIVE=True, ABI 21):
#: 11 chain x variant rows carrying 22 steps at full depth through Phase 2;
#: Phase 3 (`#T1166`) unblocks kuramoto_step (BOTH variants — 5 steps each),
#: quaternion_dft (9) and octonion_dft (10), re-measured at 15 rows / 51 steps
#: with all four arms (decline + value-move, per step) firing.
#: 51 -> 107 / 15 -> 17 when klein4_from_one closed (rc452, gh #1653): its two
#: variants carry 9 plain top-level steps + 19 map-body steps each at full
#: depth (the map container itself carries no op key and is not a step row).
EXPECTED_STEPS = 107
EXPECTED_RUNNING_CHAINS = 17


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
                # rc452 Phase 3: the descriptor's input_defaults /
                # optional_inputs merge UNDER the case, the same construction
                # the rc450 parity population uses. Without it every
                # kuramoto_step/general case failed `@input.pin_anchor`
                # resolution and the variant fell OUT of this population the
                # moment it started running in C — SEAM 1's docstring
                # predicted exactly this opening, and it measured LIVE on the
                # first post-unblock run: 14 rows where the parity population
                # holds 15, with the general variant's 5 steps unwitnessed.
                from srmech.dsl._cascade_chain import chain_input_defaults
                inputs = dict(chain_input_defaults(entry))
                inputs.update(dict(case.get("inputs") or {}))
                try:
                    rc, _val = _c_value(chain, inputs)
                except Exception:                      # noqa: BLE001
                    continue
                if rc == 0:
                    rows.append((nm, variant, entry, inputs))
    return rows


def test_mutation_coverage_over_every_variant_and_case():
    """SEAM 1. Coverage decided over the FULL population, not `[0]` of each.

    Same MUTATIONS roster as the test above — deliberately, so the two cannot
    disagree about what is covered. The only thing that widens is the set of
    chains asked. (The exempt map both tests once shared is gone for the
    reason the narrower test's docstring states: all three entries were
    falsified by executed one-line argument mutations.)

    RED-PLANT that proves it fires: delete the `("cyclic_mod_add", ...)` row from
    MUTATIONS. `cyclic_mod_add` runs in C on all four of its proof cases, so it
    lands in `running` and this reds naming it. (The same plant reds the
    narrower test too — that is the point: this one must not be WEAKER, only
    wider.)
    """
    covered = {m[0] for m in MUTATIONS}
    rows = _all_running_rows()
    assert rows, "no chain ran in C — the coverage claim would be vacuous"
    running = {nm for nm, _v, _e, _i in rows}
    uncovered = sorted(running - covered)
    assert not uncovered, (
        "these chains run in C on at least one (variant, proof case) with no "
        "step-mutation witness: %s" % uncovered)


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


#: ── rc452 (`#T1166`) Phase 2: the per-step VALUE probes ─────────────────────
#: bare op name -> (label, mutate(step_dict) -> None). Each probe is a one-line
#: ARGUMENT mutation the C runner can EXECUTE (rc == 0) whose result must
#: differ from the baseline on at least one proof case.
#:
#: WHY THESE EXIST. Through the first half of rc452 the step gate scored a step
#: as "read" if the chain EITHER declined a bogus op name OR ran it to a moved
#: value — and measured over all 22 steps, the value arm had fired ZERO times:
#: an unresolvable op always declines, so the OR was decided by the decline arm
#: alone. That makes the old gate a step-REACHABILITY instrument (a runner that
#: VALIDATES op names up front without executing steps passes it), a weaker
#: property than its name and docstring claimed. These probes are the value
#: half made real: a name-validating non-executor declines nothing here — the
#: mutant is a legal descriptor — so only a runner that EXECUTES the step with
#: its mutated argument can produce the moved value the gate demands.
VALUE_PROBES = {
    "gcd":            ("args.b -> 1",
                       lambda s: s["args"].__setitem__("b", 1)),
    "mod_add":        ("args.b -> 1",
                       lambda s: s["args"].__setitem__("b", 1)),
    "mod_mul":        ("args.b -> 1",
                       lambda s: s["args"].__setitem__("b", 1)),
    "mod_mul_wide":   ("args.b -> 1",
                       lambda s: s["args"].__setitem__("b", 1)),
    "mod_pow":        ("args.k -> 1",
                       lambda s: s["args"].__setitem__("k", 1)),
    "mod_inv":        ("args.n -> 11",
                       lambda s: s["args"].__setitem__("n", 11)),
    "chiral_flip":    ("args.seq -> [9.0, 4.0]",
                       lambda s: s["args"].__setitem__("seq", [9.0, 4.0])),
    "autocorrelation": ("args.x -> [9.0, 4.0]",
                        lambda s: s["args"].__setitem__("x", [9.0, 4.0])),
    "pin_slot_at_zero": ("args.x -> -9.5",
                         lambda s: s["args"].__setitem__("x", -9.5)),
    "reorient":       ("args.orientation -> -1",
                       lambda s: s["args"].__setitem__("orientation", -1)),
    "dead_band":      ("args.band -> 1e6",
                       lambda s: s["args"].__setitem__("band", 1e6)),
    "scale_round_half_even": ("args.scale -> 10",
                              lambda s: s["args"].__setitem__("scale", 10)),
    "best_rational":  ("args.max_denominator -> 1",
                       lambda s: s["args"].__setitem__("max_denominator", 1)),
    # ⚠️ pair's probe was `second -> 99` through the rc452 Phase-3 round and
    # was RETUNED to 1 when klein4_from_one closed: its map body feeds the
    # pair into a seq_get whose result indexes the 4-row V4 Cayley table, so
    # 99 made the mutant DECLINE (out of range) rather than move — a probe
    # that kills the chain proves nothing. 1 is in-range for the crumb domain
    # AND still moves best_rational_signed ((22, 7) -> (22, 1)).
    "pair":           ("args.second -> 1",
                       lambda s: s["args"].__setitem__("second", 1)),
    "seq_len":        ("args.seq -> [1.0, 2.0]",
                       lambda s: s["args"].__setitem__("seq", [1.0, 2.0])),
    "correlation_product": ("args.i -> 0",
                            lambda s: s["args"].__setitem__("i", 0)),
    "compensated_sum": ("args.values -> [7.5]",
                        lambda s: s["args"].__setitem__("values", [7.5])),
    # ── rc452 Phase 3: the kuramoto / hypercomplex-DFT step ops ─────────────
    "seq_get":        ("args.i -> 0",
                       lambda s: s["args"].__setitem__("i", 0)),
    "vec_scale":      ("args.s -> 42.0",
                       lambda s: s["args"].__setitem__("s", 42.0)),
    "kuramoto_inv_n": ("args.coupling -> 9.5",
                       lambda s: s["args"].__setitem__("coupling", 9.5)),
    "kuramoto_sin_term": ("args.j -> 0",
                          lambda s: s["args"].__setitem__("j", 0)),
    "kuramoto_out_simple": ("args.dt -> 97.0",
                            lambda s: s["args"].__setitem__("dt", 97.0)),
    "kuramoto_gen_term": ("args.alpha -> 1.25",
                          lambda s: s["args"].__setitem__("alpha", 1.25)),
    "kuramoto_gen_out": ("args.dt -> 97.0",
                         lambda s: s["args"].__setitem__("dt", 97.0)),
    "as_quat4":       ("args.v -> [5.0, 0.0, 0.0, 0.0]",
                       lambda s: s["args"].__setitem__(
                           "v", [5.0, 0.0, 0.0, 0.0])),
    "as_oct8":        ("args.vec -> [5.0, 0.0, 0.0, 0.0]",
                       lambda s: s["args"].__setitem__(
                           "vec", [5.0, 0.0, 0.0, 0.0])),
    "qdft_resolve_mu": ("args.mu_axis -> 'k'",
                        lambda s: s["args"].__setitem__("mu_axis", "k")),
    "odft_resolve_mu": ("args.mu_axis -> 'e5'",
                        lambda s: s["args"].__setitem__("mu_axis", "e5")),
    "dft_sigma":      ("args.inverse -> True",
                       lambda s: s["args"].__setitem__("inverse", True)),
    "dft_scale":      ("args.inverse -> True",
                       lambda s: s["args"].__setitem__("inverse", True)),
    "qdft_summand":   ("args.m -> 0",
                       lambda s: s["args"].__setitem__("m", 0)),
    "odft_summand":   ("args.m -> 0",
                       lambda s: s["args"].__setitem__("m", 0)),
    # ── rc452 (gh #1653): the klein4_from_one string/bytes leaves ────────────
    # A 64-char hex literal is the probe text wherever the mutated value flows
    # into the chain's crumb reads: the body indexes hexb up to char 33 and
    # feeds each char through the hexval table, so a SHORT or non-hex probe
    # value makes the mutant DECLINE (out-of-range lookup) instead of moving —
    # measured while tuning these, not guessed.
    "render_template": ("args.template -> 'probe-template'",
                        lambda s: s["args"].__setitem__(
                            "template", "probe-template")),
    "utf8_encode":    ("args.text -> '0123...cdef' (64 hex chars)",
                       lambda s: s["args"].__setitem__(
                           "text", "0123456789abcdef" * 4)),
    "str_concat":     ("args.text -> 'X'",
                       lambda s: s["args"].__setitem__("text", "X")),
    "byte_slice":     ("args.start -> 0, args.stop -> 1",
                       lambda s: (s["args"].__setitem__("start", 0),
                                  s["args"].__setitem__("stop", 1))),
    # sha256_bytes / int_parse_le have ONE argument each, and its only legal
    # value is a ref to the one bytes-typed producer in scope — the wire has
    # no bytes literal to substitute (that is the filed `b`-kind gap). So the
    # probe swaps the OP for one that emits a legal constant the downstream
    # steps accept: a str for the hash (the render of a 64-hex literal), an
    # in-domain int for the parse (97 = 'a', whose hexval index is 49). A
    # name-validating non-executor still fails these — the mutant is a legal
    # descriptor whose VALUE only an executing runner can produce.
    "sha256_bytes":   ("op -> render_template('0123...cdef')",
                       lambda s: (s.__setitem__(
                           "op", "srmech.amsc.descriptor.render_template"),
                           s.__setitem__(
                               "args", {"template": "0123456789abcdef" * 4,
                                        "context": {}}))),
    "int_parse_le":   ("op -> mod_add(97, 0, 257) [the constant 'a' code]",
                       lambda s: (s.__setitem__(
                           "op", "srmech.math.cyclic.mod_add"),
                           s.__setitem__(
                               "args", {"a": 97, "b": 0, "n": 257}))),
}

#: rc452 (gh #1653) — PER-STEP probe OVERRIDES, keyed (chain name, step path).
#: The bare-op table above is one probe per OP; two klein4 steps need a
#: DIFFERENT mutation than their op's default because the default is an
#: identity there (a probe that cannot move is not a probe):
#:   * step[8] (seq_get): its `i` is already the literal 0 — the only index
#:     its 1-element seq literal accepts — so `i -> 0` moves nothing. The
#:     override shrinks the SEQ literal to a 16-entry quotient table, which a
#:     step-reading runner must honour by producing 16 crumbs instead of 64.
#:   * body[8] (mod_add): the default `b -> 1` sends every hexval index to
#:     ascii+1, which exceeds the 55-entry table for any digest containing
#:     '6'..'9' or 'a'..'f' — i.e. always — so the mutant DECLINES. The
#:     override pins `a` to 48 ('0'), whose index is exactly 0: executable,
#:     and every nibble becomes 0 where the baseline's vary.
VALUE_PROBE_OVERRIDES = {
    ("klein4_from_one", (8,)): (
        "args.seq -> [[0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3]]",
        lambda s: s["args"].__setitem__(
            "seq", [[0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3]])),
    ("klein4_from_one", (9, "body", 8)): (
        "args.a -> 48 [the constant '0' code; hexval index 0]",
        lambda s: s["args"].__setitem__("a", 48)),
}

#: rc452 (gh #1653) — steps whose VALUE is FORCED by executability: every
#: one-line argument mutation either leaves the value unchanged or makes the
#: chain decline, so the value arm CANNOT fire and demanding it would demand
#: the impossible. This is the "prove it by execution in a test beside this
#: one, not by a string in a dict" clause of the coverage docstring, honoured:
#: membership here is admissible ONLY with an executed exhaustion proof —
#: test_forced_steps_are_actually_forced below runs the candidate mutation
#: family and asserts every member is identity-or-decline. The DECLINE arm
#: still applies to these steps in full (they must be REACHABLE); only the
#: value-move demand is discharged by the proof.
#:
#: klein4 body[5] is mod_add(a=@step[4], b=1, n=257) — the byte-slice STOP,
#: which downstream executability pins to exactly start+1: any other stop
#: yields an empty slice (int 0 -> hexval index 209, out of range) or a
#: multi-byte slice whose folded value leaves the hexval domain for some j of
#: every real digest. The step's only executable output is its baseline's.
FORCED_VALUE_STEPS = frozenset({
    ("klein4_from_one", (9, "body", 5)),
})

#: How many times the population walk MEETS a forced step — one per running
#: VARIANT that carries it (klein4's rest AND wound bodies are the same
#: pipeline at the same paths, so its one forced path is walked twice).
#: Pinned tight so a forced row can neither appear nor vanish silently.
EXPECTED_FORCED_STEP_WALKS = 2


def _value_probe_for(step, chain=None, path=None):
    """(label, mutate) for one step, or None if no probe covers its op.

    A FOLD step has no ``args`` to mutate; its probe flips ``fold_init``, which
    a correct runner must thread through every application of the fold body
    (and return unchanged on the empty fold — either way the value moves).
    A VECTOR fold (rc452 Phase 3 — the DFT chains' vec_add seed is a list)
    bumps element 0 instead: a scalar ``-1`` seed on a vec_add fold is a
    LENGTH-MISMATCHED descriptor both projections refuse, so it would score
    the step dead for the wrong reason.

    rc452 (gh #1653): a ``(chain, path)`` pair in ``VALUE_PROBE_OVERRIDES``
    outranks the bare-op table — the op's default probe is an IDENTITY on two
    klein4 steps (see the overrides' own comments), and a probe that cannot
    move is not a probe.
    """
    if chain is not None and path is not None:
        ov = VALUE_PROBE_OVERRIDES.get((chain, tuple(path)))
        if ov is not None:
            return ov
    if "fold_op" in step:
        if isinstance(step.get("fold_init"), list):
            def _bump0(s):
                s["fold_init"] = [1.0] + list(s["fold_init"][1:])
            return ("fold_init[0] -> 1.0", _bump0)
        return ("fold_init -> -1", lambda s: s.__setitem__("fold_init", -1))
    bare = str(step.get("op", "")).rsplit(".", 1)[-1]
    return VALUE_PROBES.get(bare)


def test_every_step_of_every_running_chain_is_actually_read():
    """SEAM 2, both halves. Every step must (1) DECLINE an unresolvable op and
    (2) MOVE THE VALUE under a legal one-line argument mutation.

    Half (1) — reachability. Point the step's op at a name nothing can
    resolve; the chain must refuse to run. A step whose bogus op is accepted
    with an identical value is a step the resolver never visited.

    Half (2) — value-drive, rc452 (`#T1166`) Phase 2. Reachability alone is
    weaker than this gate's name: a runner that VALIDATES every op name up
    front and then dispatches something coarse passes half (1) with the steps
    driving nothing. Measured mid-rc452: all 22 steps scored via the decline
    arm and the value arm of the old EITHER/OR had fired ZERO times — the
    gate could not return otherwise on the property its docstring claimed.
    So each step now also carries a VALUE probe from ``VALUE_PROBES`` (or a
    per-step override in ``VALUE_PROBE_OVERRIDES``): a mutation the runner
    must EXECUTE (rc == 0) to a value that differs from the baseline. Both
    halves are asserted per step, so neither arm is decorative. The ONE
    admissible exception is a step in ``FORCED_VALUE_STEPS`` — a step whose
    value is pinned by executability itself — and its exception is not a
    string in a dict but an EXECUTED exhaustion proof
    (test_forced_steps_are_actually_forced); the decline arm still binds it.

    ⚠️ A STEP IS JUDGED OVER ALL ITS PROOF CASES, NOT case[0]. `net_chirality`'s
    fold is genuinely vacuous on `{"orientations": []}` — an empty fold returns
    `fold_init` without ever invoking `fold_op`, so a bogus op there is correctly
    a no-op. Judging that step on case[0] alone reports a false DEAD. It reacts
    on all six non-empty cases. This is the same vacuity that rc447's
    `_widen_dead_band` mutation hit on `best_rational_signed` case 6, and the
    same answer: require the reaction on SOME case, not on an arbitrary one.

    MEASURED at rc452 Phase 3: 51 steps over 15 running chain-variants; 51
    decline, 51 move. Re-measured when klein4_from_one closed (the registry-
    ripple phase): 107 steps over 17 rows; 107 decline, 106 move + 1 forced.

    ⚠️ The docstring figure said "18 steps over 10 running chains" for part of
    rc452 — measured mid-rc, then falsified by the rc's own `autocorrelation`
    commit (8649917b5), which added the 11th running chain with 4 steps and
    moved `CEIL_C_REJECTED_CHAINS` 8 -> 7 in the same stroke, staling three
    prose numbers in three files at once. Corrected before rc452 shipped, and
    the counts are PINNED rather than narrated so it cannot recur silently.

    RED-PLANTS, both executed: (1) in the C resolver (`cr_dispatch` over the
    `CR_OP_REG` table in src/srmech_compose_run.c — `cr_dispatch_real` was
    deleted by the rc452 A1 reshape) return SRMECH_OK with the input passed
    through for an unresolved op: every step accepts the bogus name and half
    (1) reds naming each step. (2) point one op's VALUE probe at the value the
    baseline already uses (gcd `args.b -> 18` on the (12, 18) case): the
    mutant equals the baseline and half (2) reds naming the step and the arm.
    A cheaper Python-side plant: make `_step_paths` return `[]` — the
    self-check below reds first, which is what it is for.
    """
    by_chain = {}
    for nm, variant, entry, inputs in _all_running_rows():
        by_chain.setdefault((nm, variant, id(entry)), [entry, []])[1].append(inputs)

    probed = declined = value_moved = forced = 0
    dead = []
    for (nm, variant, _k), (entry, input_list) in sorted(
            by_chain.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        base = _chain_only(entry)
        for path, opkey in _step_paths(base.get("steps")):
            probed += 1
            step_id = "%s/%s step[%s].%s" % (
                nm, variant, ".".join(str(x) for x in path), opkey)

            # ── half (1): the unresolvable op must be DECLINED ──────────
            step_declined = False
            for inputs in input_list:
                rc_b, _val_b = _c_value(base, inputs)
                if rc_b != 0:
                    continue
                mutant = copy.deepcopy(base)
                _at(mutant, path)[opkey] = BOGUS_OP
                if _c_value(mutant, inputs)[0] != 0:
                    step_declined = True
                    break
            if step_declined:
                declined += 1
            else:
                dead.append("%s [DECLINE arm: bogus op accepted]" % step_id)

            # ── half (2): the VALUE probe must run AND move the value ───
            # A FORCED step (executability pins its value — see
            # FORCED_VALUE_STEPS) discharges this arm through the executed
            # exhaustion proof one test down, never through a probe; the
            # decline arm above still binds it in full.
            if (nm, tuple(path)) in FORCED_VALUE_STEPS:
                forced += 1
                continue
            probe = _value_probe_for(_at(base, path), nm, path)
            if probe is None:
                dead.append(
                    "%s [VALUE arm: no probe in VALUE_PROBES for this op — "
                    "add one; an unprobed step is unmeasured, not exempt]"
                    % step_id)
                continue
            label, mutate = probe
            step_moved = False
            for inputs in input_list:
                rc_b, val_b = _c_value(base, inputs)
                if rc_b != 0:
                    continue
                mutant = copy.deepcopy(base)
                mutate(_at(mutant, path))
                rc_m, val_m = _c_value(mutant, inputs)
                if rc_m == 0 and _bits_of(val_m) != _bits_of(val_b):
                    step_moved = True
                    break
            if step_moved:
                value_moved += 1
            else:
                dead.append(
                    "%s [VALUE arm: probe %r never ran to a moved value — "
                    "the step's argument is not driving the C execution]"
                    % (step_id, label))

    # SELF-CHECK FIRST: a probe that reached no step would report a clean zero.
    assert probed > 0, (
        "no step was probed — either no chain runs in C or _step_paths walked "
        "nothing, and a green here would mean neither")
    # rc452 (`#T1171`): PIN the population this docstring advertises. A measured
    # figure with no tie to the measurement rots — mid-rc452 the docstring said
    # "18 steps over 10 chains" because a later commit in the same rc added a
    # chain and nobody re-ran the count. Raising these is EXPECTED when a chain
    # starts running in C; the point is that it cannot happen silently, and the
    # docstring above is updated in the same edit.
    assert (probed, len(by_chain)) == (EXPECTED_STEPS, EXPECTED_RUNNING_CHAINS), (
        "step-mutation population moved: probed %d steps over %d running chains, "
        "this file documents %d over %d. If a chain started (or stopped) running "
        "in C, update BOTH these constants and the docstring figure above — and "
        "check python/README.md's `CEIL_C_REJECTED_CHAINS` sentence, which moves "
        "with the same commits."
        % (probed, len(by_chain), EXPECTED_STEPS, EXPECTED_RUNNING_CHAINS))
    assert declined > 0 and value_moved > 0, (
        "an entire arm never fired (declined=%d, value_moved=%d over %d steps) "
        "— the mutation is not reaching the document and every row below is an "
        "artifact" % (declined, value_moved, probed))
    assert not dead, (
        "steps failing the read-and-driving contract (arm named per row): %s"
        % dead)
    # BOTH arms across the WHOLE population — the claim the gate's name makes.
    # A FORCED step counts through its executed exhaustion proof
    # (test_forced_steps_are_actually_forced), never as a free pass: the set
    # is pinned tight here so a forced row cannot appear or vanish silently.
    assert forced == EXPECTED_FORCED_STEP_WALKS, (
        "forced-step population mismatch: walked %d, EXPECTED_FORCED_STEP_"
        "WALKS is %d — a pinned forced step is not in the running population "
        "(stale pin), a new one appeared unproven, or a variant carrying one "
        "started/stopped running"
        % (forced, EXPECTED_FORCED_STEP_WALKS))
    assert declined == probed and value_moved + forced == probed, (
        "arm coverage is partial: %d/%d declined, %d value-moved + %d forced "
        "of %d. A step counted by only one arm is reachability without drive "
        "(or drive without a decline contract), and the docstring above "
        "explains why neither alone is the property this gate sells."
        % (declined, probed, value_moved, forced, probed))


def _bits_of(v):
    """Typed identity for the step-drive comparison — never `==`.

    `_c_value` returns RECONSTRUCTED values, so a step whose mutation turns
    `Q(5, 6)` into `(5, 6)` must count as MOVED. `==` says those are equal (it
    cross-multiplies through `_as_pair`) and would score that step DEAD.
    """
    from test_c_cascade_value_parity_rc450 import _bits as _b
    return _b(v)


def test_forced_steps_are_actually_forced():
    """The EXECUTED exhaustion proof behind ``FORCED_VALUE_STEPS``.

    A forced-step entry claims "no one-line argument mutation of this step
    both runs and moves the value", and per the coverage docstring that claim
    is only ever provable by execution. So: for each pinned step, run a
    CANDIDATE FAMILY of argument mutations spanning every argument and the
    mechanistically distinct values (the identity-mod-n wrap, the off-by-one
    stops, an empty-slice constant, a modulus narrowing), and assert every
    member is IDENTITY-OR-DECLINE — and that at least one member DECLINES, so
    the family demonstrably reaches the executing step rather than a
    dead branch.

    The family is bounded, not universal — no finite test enumerates every
    int64 — but each candidate is chosen against the step's OWN mechanism
    (klein4 body[5] computes the byte-slice stop; the family covers stop
    shifted down, up, wrapped by a modulus, pinned constant, and the
    b === 1 (mod n) identity images), so a runner for which any of these
    moved the value would be caught. If a mutation outside the family is
    ever found to move it, the fix is to DELETE the FORCED row and write the
    probe — this proof then reds on the next population walk.
    """
    fam = [("args.b -> 0", lambda s: s["args"].__setitem__("b", 0)),
           ("args.b -> 2", lambda s: s["args"].__setitem__("b", 2)),
           ("args.b -> 3", lambda s: s["args"].__setitem__("b", 3)),
           ("args.b -> -1", lambda s: s["args"].__setitem__("b", -1)),
           ("args.b -> 258 [=== 1 mod 257: the identity image]",
            lambda s: s["args"].__setitem__("b", 258)),
           ("args.a -> 0", lambda s: s["args"].__setitem__("a", 0)),
           ("args.a -> 1", lambda s: s["args"].__setitem__("a", 1)),
           ("args.a -> 32", lambda s: s["args"].__setitem__("a", 32)),
           ("args.n -> 2", lambda s: s["args"].__setitem__("n", 2)),
           ("args.n -> 33", lambda s: s["args"].__setitem__("n", 33)),
           ("args.n -> 514 [char_idx+1 < n: the identity image]",
            lambda s: s["args"].__setitem__("n", 514))]
    for nm, path in sorted(FORCED_VALUE_STEPS):
        rows = [(v, e, i) for (n2, v, e, i) in _all_running_rows() if n2 == nm]
        assert rows, "%s is pinned FORCED but not running — stale pin" % nm
        proved_identity = declined_once = False
        for variant, entry, inputs in rows:
            base = _chain_only(entry)
            rc_b, val_b = _c_value(base, inputs)
            if rc_b != 0:
                continue
            for label, mutate in fam:
                mutant = copy.deepcopy(base)
                mutate(_at(mutant, path))
                rc_m, val_m = _c_value(mutant, inputs)
                if rc_m != 0:
                    declined_once = True
                    continue
                assert _bits_of(val_m) == _bits_of(val_b), (
                    "%s %s: candidate %r RAN TO A MOVED VALUE — the step is "
                    "not forced. Delete its FORCED_VALUE_STEPS row and give "
                    "it that mutation as a probe (via VALUE_PROBE_OVERRIDES)."
                    % (nm, path, label))
                proved_identity = True
        assert proved_identity and declined_once, (
            "%s %s: the family never produced BOTH an executed identity and "
            "a decline (identity=%r, declined=%r) — the exhaustion proof is "
            "not reaching the step and proves nothing"
            % (nm, path, proved_identity, declined_once))
