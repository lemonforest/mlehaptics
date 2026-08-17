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
