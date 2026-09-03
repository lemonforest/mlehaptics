"""rc297 (`#934`) — the GENERAL N-slot Cayley–Dickson register.

srmech shipped exactly one addressable register (``SedenionRegister``, hard-wired
to 16 slots), so research needing 32 slots had to write its own and correctly
flagged that as a confound. This suite is the reason the in-tree general register
removes the confound rather than merely relocating it.

THE FAITHFULNESS GATE MOVED TO ``test_cd_register_golden_rc464.py``, and this
docstring records why, because the move is the interesting part.

The brief's gate was "reproduce the shipped SedenionRegister at dim 16, 120/120
exact at D>=1024". That was never the gate this suite enforced, because it cannot
explain the known low-D divergence (the out-of-tree research register read 119/120
at D=256 where the shipped one read 116/120, with a different collision pattern).
A general implementation that matches only once capacity is adequate has an
unexplained difference in its minting or addressing. The gate was, and remains:
``CDRegister(dim=16, namespace="SEDENION")`` must be **bit-exact** — same key AND
same sign on every probe — at **every** D including the starved regime where both
fall short of 120/120.

What rc464 changed is the ORACLE, not the gate. It was the live
``SedenionRegister``; it is now that class's RECORDED output
(``tests/sedenion_register_golden_rc464.ndjson``, digest-pinned), because rc464
makes CDRegister the register shape and removes the 16-slot class. This suite
carried a test whose entire job was to FORBID that — asserting through
``inspect.getsource`` that the oracle does not mention the subject — and it was
right to: an oracle that delegates to its subject shares its failure modes. So
the guarantee MOVED rather than being deleted, from code independence to data
provenance, which is the stronger form of the same claim (recorded output cannot
acquire the subject's failure modes because it is not running).

What stays here is everything that never needed the 16-slot class.
``test_low_d_divergence_is_entirely_the_address_name_mint`` shows the divergence
is name-noise and not a property of either register, by demonstrating that the
ordering REVERSES with D and that the shipped namespace sits inside the spread of
arbitrary names.

THE STRUCTURAL INVARIANT (F1274 / F1275) is enforced, not assumed: addressing
survives past the Hurwitz boundary precisely because basis products are a signed
permutation while zero divisors are built from SUMS of basis elements — disjoint
properties. ``test_basis_product_is_a_signed_permutation_at_every_rung`` checks
that against a full exact-rational ``cd_mult`` (4096/4096 pairs at dim 64), which
is an independent code path from the ``cd_basis_product`` cocycle the register
actually uses.

numpy-free; no ``abs()``; exact integer address algebra.
"""

import ast
import importlib
import inspect

import pytest

from srmech import cascade
from srmech import _native
from srmech.cascade.cayley_dickson import CD_MAX_DIM

# NOTE: ``srmech.cascade.cd_register`` names BOTH the module and the factory
# function, and the cascade __init__ re-export shadows the module attribute — so
# ``from srmech.cascade import cd_register`` yields the FUNCTION. That is the
# established shipped convention ("module X re-exports callable X"; the dotted
# resolver prefers the callable — ``tests/test_cd_register_resolves.py``), so it
# is followed rather than broken here; the module object is fetched explicitly.
cd_register_mod = importlib.import_module("srmech.cascade.cd_register")

# Powers of two srmech builds tables for. 1 and 2 are degenerate (no imaginary
# direction to navigate) but must still satisfy the structural invariant.
RUNGS = (1, 2, 4, 8, 16, 32, 64)
NAV_RUNGS = (4, 8, 16, 32, 64)

# rc464: the C-PEER agreement rungs, which are NOT the same set. RUNGS /
# NAV_RUNGS bound the O(dim^4) cross-path checks below and deliberately stop at
# 64 (rc298 measured ~2.8 min at 128 and ~32 min at 256 for those, and covers
# the upper rungs by sample instead). The three C-vs-pure agreement tests are
# O(dim^2) and cost well under a second at 256 -- measured 0.188 s for the full
# 65,536-call pure sweep -- so there is no reason for them to stop where the
# expensive ones do. They stopped anyway, because `cd_navmap_c` /
# `cd_navigate_c` / `cd_navmap_is_signed_permutation_c` each carried a
# `dim > 64 -> return None` domain guard while the C peers behind them have
# accepted every power of two up to SRMECH_CD_MAX_DIM = 256 since rc298. With
# the guards respelled, THESE are the rungs that actually measure the claim
# "real C peers reachable through dispatch glue" at the rungs the register
# reaches -- a claim that was false above 64 from rc298 to rc463 with no
# instrument able to say so.
C_RUNGS = RUNGS + (128, 256)
C_NAV_RUNGS = NAV_RUNGS + (128, 256)

NAMES = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
         "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi",
         "rho", "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega",
         "aleph", "bet", "gimel", "dalet", "he", "vav", "zayin", "het"]


def _basis(i, d):
    return tuple(1 if k == i else 0 for k in range(d))


def _probe_roundtrip(make, keys, directions):
    """Write ``keys`` into slots 0.., navigate each direction, read back at the
    navmap-predicted destination. Returns the per-probe (key, sign, hit) list —
    the RAW outcomes, so callers can compare bit-exactly and not merely by count.
    """
    out = []
    for j in directions:
        r = make()
        for i, k in enumerate(keys):
            r.write(i, k)
        nav = r.navmap(j)
        moved = r.navigate(j)
        for i, k in enumerate(keys):
            dest, sign = nav[i]
            got_key, got_sign = moved.read(dest)
            out.append((got_key, got_sign, got_key == k and got_sign == sign))
    return out


# ──────────────────────────────────────────────────────────────────────
# THE ADDRESS-MINT MECHANISM — what the faithfulness gate localised the entire
# low-D divergence TO. The gate itself is now
# test_cd_register_golden_rc464.py::test_the_nine_d_bit_exact_gate_against_the_record
# (same nine D, same 120 probes; the oracle recorded rather than live).
# ──────────────────────────────────────────────────────────────────────

def test_low_d_divergence_is_entirely_the_address_name_mint():
    """EXPLAIN the known low-D discrepancy rather than smoothing it over.

    The out-of-tree research register read 119/120 at D=256 where the shipped
    register read 116/120, with a different collision pattern. Two facts localise
    that completely to the address-name mint:

    1. With ``namespace="SEDENION"`` the general register is bit-exact with the
       shipped one at D=256 (asserted above) — so the construction is identical
       and the name is the only free variable.
    2. The ordering REVERSES with D. At D=256 the ``CD16`` namespace scores
       higher; at D=320 the ``SEDENION`` namespace scores higher. A register that
       were structurally "easier" could not lose at a lower capacity.

    So "the research register scored better" was never a property of that
    register. Different names mint different address hypervectors, and at starved
    D the crosstalk between them decides which reads survive.
    """
    keys, dirs = NAMES[:8], list(range(1, 16))

    def hits(D, ns):
        return sum(h for _, _, h in _probe_roundtrip(
            lambda: cascade.cd_register(16, D=D, namespace=ns), keys, dirs))

    # (1) the two namespaces genuinely differ at a starved D ...
    assert hits(256, "SEDENION") == 116, (
        "the starved-capacity score this whole explanation is about moved — it is "
        "116/120, recorded in tests/sedenion_register_golden_rc464.ndjson")
    assert hits(256, "CD16") != hits(256, "SEDENION")
    # (2) ... and the ordering REVERSES, which kills "one register is easier".
    assert hits(256, "CD16") > hits(256, "SEDENION")
    assert hits(320, "CD16") < hits(320, "SEDENION")


def test_shipped_namespace_is_inside_the_spread_of_arbitrary_names():
    """The starved-D score is a draw from a name-dependent distribution, not a
    quality ranking: arbitrary namespaces span a range at D=256 and the shipped
    register's namespace sits inside it. Guards against ever reading the 116/120
    as "the shipped register is worse"."""
    keys, dirs = NAMES[:8], list(range(1, 16))
    scores = {}
    for ns in ("SEDENION", "CD16", "REG", "HV", "E", "ADDR", "ZZ", "Q"):
        scores[ns] = sum(h for _, _, h in _probe_roundtrip(
            lambda: cascade.cd_register(16, D=256, namespace=ns), keys, dirs))
    assert min(scores.values()) < max(scores.values()), (
        "the namespace sweep is degenerate — the mechanism claim is untested")
    assert min(scores.values()) <= scores["SEDENION"] <= max(scores.values())
    # And every one of them is fine once capacity is adequate.
    for ns in scores:
        ok = sum(h for _, _, h in _probe_roundtrip(
            lambda: cascade.cd_register(16, D=4096, namespace=ns), keys, dirs))
        assert ok == 120, f"namespace {ns!r} failed at adequate D — not name-noise"


# ──────────────────────────────────────────────────────────────────────
# THE STRUCTURAL INVARIANT — enforced, not incidental (F1274 / F1275)
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim", RUNGS)
def test_basis_product_is_a_signed_permutation_at_every_rung(dim):
    """Addressing survives past the Hurwitz boundary because ``e_i·e_j = ±e_k``
    is a SIGNED PERMUTATION, while zero divisors are built from SUMS of basis
    elements — disjoint properties.

    Checked against the full exact-rational ``cd_mult``, which is an INDEPENDENT
    code path from the ``cd_basis_product`` cocycle the register uses: every one
    of the dim² basis pairs must produce exactly one nonzero coefficient, that
    coefficient must be ±1, and its index/sign must agree with the cocycle.
    4096/4096 at dim=64.
    """
    for i in range(dim):
        for j in range(dim):
            prod = cascade.cd_mult(_basis(i, dim), _basis(j, dim))
            nz = [(k, v) for k, v in enumerate(prod) if v != 0]
            assert len(nz) == 1, (
                f"e{i}·e{j} at dim {dim} is NOT a single basis element ({nz}) — "
                f"the premise the whole address layer rides on has failed")
            k, v = nz[0]
            assert v in (1, -1), f"e{i}·e{j} coefficient {v} is not ±1"
            assert (k, v) == cascade.cd_basis_product(dim, i, j), (
                f"the cd_basis_product cocycle disagrees with the full cd_mult "
                f"at dim {dim}, e{i}·e{j}")


@pytest.mark.parametrize("dim", RUNGS)
def test_navmap_is_a_bijection_for_every_direction(dim):
    """``navmap(j)`` must be a bijection on ``[0, dim)`` for EVERY j at EVERY
    rung — the runtime-checkable form of the invariant above."""
    for j in range(dim):
        m = cascade.cd_navmap(dim, j)
        assert sorted(k for k, _ in m.values()) == list(range(dim))
        assert all(s in (1, -1) for _, s in m.values())
    assert cascade.cd_navmap_is_signed_permutation(dim) is True


def test_signed_permutation_holds_where_composition_fails():
    """The contrast that makes the invariant meaningful: at dim 32 composition
    (norm-multiplicativity) is broken for generic pairs, yet addressing is
    completely intact. If this test ever inverts, the general register's
    justification is gone."""
    def derived(t, dim, salt=0):
        return tuple(((t * 31 + k * 17 + salt * 7) % 11) - 5 for k in range(dim))

    fails = total = 0
    for n in range(40):
        x, y = derived(n, 32, 0), derived(n, 32, 1)
        if all(c == 0 for c in x) or all(c == 0 for c in y):
            continue
        total += 1
        lhs = sum(a * a for a in cascade.cd_mult(x, y))
        rhs = sum(a * a for a in x) * sum(a * a for a in y)
        if lhs != rhs:
            fails += 1
    assert total > 0
    assert fails / total > 0.5, (
        "composition was expected to be badly broken at dim 32 — the contrast "
        "this test rests on is not present")
    assert cascade.cd_navmap_is_signed_permutation(32) is True


# ──────────────────────────────────────────────────────────────────────
# The general ops agree with their C PEERS, at every rung the register reaches
# (the dim-16 agreement with the recorded 16-slot answers is gated in
# test_cd_register_golden_rc464.py, against the record rather than a peer)
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim", C_NAV_RUNGS)
def test_cd_navmap_c_matches_the_pure_oracle(dim):
    """C/Python parity for ``srmech_cd_navmap`` over every direction."""
    if not _native.has_native_cd_navmap():
        pytest.skip("no native library loaded")
    for j in range(dim):
        native = _native.cd_navmap_c(dim, j)
        assert native is not None
        pure = {i: cascade.cd_basis_product(dim, i, j) for i in range(dim)}
        assert native == pure


@pytest.mark.parametrize("dim", C_NAV_RUNGS)
def test_cd_navigate_c_matches_the_pure_oracle(dim):
    """C/Python parity for ``srmech_cd_navigate``, including the Class-C sign
    composition on negatively-signed records."""
    if not _native.has_native_cd_navigate():
        pytest.skip("no native library loaded")
    slots = list(range(dim))
    signs = [1 if (s % 3) else -1 for s in slots]
    for j in range(dim):
        native = _native.cd_navigate_c(dim, j, slots, signs)
        assert native is not None
        exp_slots, exp_signs = [], []
        for s, g in zip(slots, signs):
            k, sign = cascade.cd_basis_product(dim, s, j)
            exp_slots.append(k)
            exp_signs.append(g * sign)
        assert native == (exp_slots, exp_signs)


@pytest.mark.parametrize("dim", C_RUNGS)
def test_cd_navmap_is_signed_permutation_c_matches_the_pure_oracle(dim):
    """C/Python parity on the invariant bool."""
    if not _native.has_native_cd_navmap_is_signed_permutation():
        pytest.skip("no native library loaded")
    assert _native.cd_navmap_is_signed_permutation_c(dim) is True


# ──────────────────────────────────────────────────────────────────────
# The register itself, at rungs the sedenion one cannot reach
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim", NAV_RUNGS)
def test_involution_navigate_twice_is_the_global_minus_one(dim):
    """``navigate(j).navigate(j)`` returns content to its original slots with
    every Class-C sign flipped (``e_j² = −1``). This is F1274's mechanism —
    involution + a sign needs no norm, so it is rung-independent — and it must
    hold at 32 and 64 exactly as at 8."""
    r = cascade.cd_register(dim, D=1024)
    for i, k in enumerate(NAMES[:min(4, dim)]):
        r.write(i, k)
    before = r.slots()
    after = r.navigate(min(3, dim - 1)).navigate(min(3, dim - 1)).slots()
    assert sorted(after) == sorted(before)
    for i in before:
        assert after[i][0] == before[i][0], "content did not return to its slot"
        assert after[i][1] == -before[i][1], "the involution sign did not flip"


def test_dim_32_addressing_end_to_end_over_a_D_sweep():
    """The live research need: 32 slots. Reported as a SWEEP — 32 slots need more
    bundle capacity than 16, so a shortfall at fixed D is a capacity fact, not an
    algebra fact, and a single-D number would confuse the two."""
    dirs = [1, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
    scores = {}
    for D in (4096, 16384, 65536):
        res = _probe_roundtrip(lambda: cascade.cd_register(32, D=D), NAMES[:32], dirs)
        scores[D] = sum(h for _, _, h in res) / len(res)
    assert scores[65536] >= scores[4096], (
        f"addressing did not improve with capacity — {scores}; that would mean "
        f"the shortfall is NOT a capacity effect and needs a different account")
    assert scores[65536] > 0.95, (
        f"dim-32 addressing failed at adequate capacity: {scores}")


def test_read_write_roundtrip_at_every_rung():
    """Basic storage/retrieval at each navigable rung, with capacity scaled to
    the slot count."""
    for dim in NAV_RUNGS:
        r = cascade.cd_register(dim, D=8192)
        keys = NAMES[:min(dim, 8)]
        for i, k in enumerate(keys):
            r.write(i, k)
        for i, k in enumerate(keys):
            assert r.read(i) == (k, 1), f"dim {dim} slot {i} did not round-trip"


def test_class_c_sign_survives_write_and_read():
    r = cascade.cd_register(32, D=8192)
    r.write(0, "alpha", sign=1)
    r.write(1, "beta", sign=-1)
    assert r.read(0) == ("alpha", 1)
    assert r.read(1) == ("beta", -1)


def test_block_structure_is_the_octonion_seven_at_every_rung():
    """Going to 32 or 64 slots buys ADDRESS SPACE, never a longer reversible
    word: the working block is the octonion's first 8 slots at every rung."""
    for dim in (8, 16, 32, 64):
        r = cascade.cd_register(dim, D=256)
        assert r.working_block() == tuple(range(8))
        assert r.carry_block() == tuple(range(8, dim))
    assert cascade.cd_register(4, D=256).working_block() == (0, 1, 2, 3)
    assert cd_register_mod.WORKING_WORD_CAP == 7


def test_navigate_carries_dim_D_namespace_and_COPIES_the_codebook():
    """rc297 precision fix. Both registers' docstrings said navigate "shares the
    codebook"; ``__init__`` takes ``dict(codebook)``, so the mapping is COPIED —
    the minted ``bytes`` are shared, but a later write to the parent does not
    appear in the child. Behaviour is unchanged and correct; the wording was
    wrong, and this test pins the real contract so it cannot drift back."""
    r = cascade.cd_register(32, D=1024, namespace="NS")
    r.write(0, "alpha")
    moved = r.navigate(1)
    assert moved.namespace == "NS"
    assert moved.dim == 32 and moved.D == 1024
    assert moved.codebook == r.codebook
    assert moved.codebook is not r.codebook          # copied, not aliased
    assert moved.codebook["alpha"] is r.codebook["alpha"]   # vectors ARE shared
    r.write(1, "beta")
    assert "beta" not in moved.codebook              # the copy does not track


def test_is_navigable_gate_single_basis_versus_zero_divisor():
    """A single basis direction is navigable at EVERY rung; the classic sedenion
    zero-divisor direction is not."""
    r = cascade.cd_register(16, D=256)
    assert r.is_navigable([1 if k == 3 else 0 for k in range(16)]) is True
    zd = [0] * 16
    zd[1], zd[10] = 1, 1                 # e1 + e10 — a sum, hence a zero divisor
    assert r.is_navigable(zd) is False


# ──────────────────────────────────────────────────────────────────────
# Domain / discipline
# ──────────────────────────────────────────────────────────────────────

# rc298 (`#933`): 128 and 256 LEFT this list — they are shipped rungs now.
@pytest.mark.parametrize("bad", [0, 3, 5, 6, 7, 12, 24, 48, 512, 1024, -1, -16])
def test_dim_must_be_a_power_of_two_within_the_cap(bad):
    with pytest.raises(ValueError, match="power of two"):
        cascade.cd_register(bad)


def test_dim_cap_is_the_shipped_cd_max_dim():
    """The cap pin. rc297 set it at 64 and said raising it was task `#933`;
    rc298 IS that task, so the pin MOVED to 256 rather than being deleted — a
    cap with no pin is a cap that drifts silently.

    256 is the addressing cap. The dense n-by-n path keeps its own smaller
    ceiling (``CD_DENSE_MAX_DIM``); the two are decoupled on purpose and
    ``test_cd_rungs_rc298.py`` pins that separation."""
    assert CD_MAX_DIM == 256
    assert cascade.cd_register(64, D=256).dim == 64
    assert cascade.cd_register(128, D=256).dim == 128
    assert cascade.cd_register(256, D=256).dim == 256
    with pytest.raises(ValueError, match="power of two"):
        cascade.cd_register(512)


def test_slot_and_direction_domains_are_enforced():
    r = cascade.cd_register(32, D=256)
    with pytest.raises(ValueError, match="address space"):
        r.write(32, "x")
    with pytest.raises(ValueError, match="address space"):
        r.write(-1, "x")
    with pytest.raises(ValueError, match="navigation basis"):
        r.navmap(32)
    with pytest.raises(ValueError, match="navigation basis"):
        r.navigate(-1)
    with pytest.raises(ValueError, match="empty"):
        cascade.cd_register(8, D=256).materialize()


def test_cd_navigate_rejects_mismatched_and_out_of_domain_records():
    with pytest.raises(ValueError, match="same length"):
        cascade.cd_navigate(16, 1, [0, 1], [1])
    with pytest.raises(ValueError, match="address space"):
        cascade.cd_navigate(16, 1, [16], [1])
    with pytest.raises(ValueError, match="Class C"):
        cascade.cd_navigate(16, 1, [0], [0])


def test_empty_register_reads_none():
    assert cascade.cd_register(16, D=256).read(0) == (None, 1)


def test_navigating_an_empty_register_is_a_clean_no_op_in_both_projections():
    """count == 0 reaches the C peer as a zero-length array pair. Pinned because
    it is the one input shape where the native and pure paths could plausibly
    disagree (a NULL-vs-empty-pointer confusion in the C null-arg guard) and
    nothing else in the suite exercises it."""
    assert cascade.cd_navigate(32, 1, [], []) == ([], [])
    assert cascade.cd_register(32, D=256).navigate(1).slots() == {}
    if _native.has_native_cd_navigate():
        assert _native.cd_navigate_c(32, 1, [], []) == ([], [])


def test_module_is_numpy_free_and_uses_no_builtin_abs():
    """Cascade-honesty: sign handling is a Class-K pin-slot composed with
    Class-C, never ``abs()``; and the whole instrument stays numpy-free.

    Checked on the AST, not by regex over the source text. A text scan cannot
    tell a CALL from PROSE — the first draft of this test failed on the module
    docstring's own sentence saying ``abs()`` must never be used, which is the
    text-scan failure mode in miniature: it would equally have passed a real
    ``abs()`` hidden inside a string. The AST sees calls and imports only.
    """
    tree = ast.parse(inspect.getsource(cd_register_mod))
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == "abs"]
    assert not calls, (
        f"builtin abs() called in cascade code at line(s) "
        f"{[n.lineno for n in calls]} — sign is Class-K pin-slot ∘ Class-C")

    banned = {"numpy", "math", "fractions"}
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            imported.add(n.module.split(".")[0])
    assert not (imported & banned), (
        f"external math library imported in shipping cascade code: "
        f"{sorted(imported & banned)}")


def test_the_abs_guard_actually_fires():
    """A guard that cannot fail is not a guard. Prove the AST scan catches a real
    ``abs()`` call AND is not fooled by the word appearing in a string."""
    real = ast.parse("def f(x):\n    return abs(x)\n")
    prose = ast.parse('def f(x):\n    """never abs() here"""\n    return x\n')

    def abs_calls(tree):
        return [n for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "abs"]

    assert abs_calls(real), "the guard would MISS a real abs() call"
    assert not abs_calls(prose), "the guard fires on prose — false positive"


def test_public_surface_is_exported_from_cascade():
    for name in ("CDRegister", "cd_register", "cd_navmap", "cd_navigate",
                 "cd_navmap_is_signed_permutation"):
        assert hasattr(cascade, name), f"cascade.{name} is not exported"
        assert name in cascade.__all__
