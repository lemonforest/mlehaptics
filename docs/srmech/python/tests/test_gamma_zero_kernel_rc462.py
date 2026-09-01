"""rc462 (`#T1179`) — the γ = 0 arm of the Cayley–Dickson cocycle.

**Why this file exists, and why every assertion here reaches a PRIVATE name.**

Two defects were located in :mod:`srmech.cascade.cayley_dickson`:

a) ``_gamma_basis_product``'s ``(ph, qh) == (1, 1)`` branch read
   ``if (ql == 0) if gamma < 0 else (ql != 0): sign = -sign`` — a *dichotomy*
   standing in for a parameter whose natural domain has three values. γ = 0
   fails ``gamma < 0``, fell through the ``else``, and was therefore computed
   as γ = +1. MEASURED at HEAD: the γ = 0 table came back **bit-identical to
   the SPLIT table** at dims 2, 4 and 8, and on the mixed ``(0, −1)`` vector.

b) ``cd_norm_sq``'s routing predicate read ``any(v > 0 for v in g)`` — which
   names the SPLIT twists, not the non-definite ones. The two sets coincide
   only while γ ∈ {+1, −1}. This is the defect that would have SURVIVED the
   fix to (a): with the kernel correct at zero the cocycle says ``N(e₁) = 0``
   while ``any(v > 0)`` routes γ = 0 to the ``Σ xᵢ²`` fast path and answers 1.

**Both were LATENT, never live, and that is exactly why this file is shaped the
way it is.** ``_normalise_gammas`` (Python) and ``cd_check_gammas`` (C) refuse
γ = 0 at every public entry — MEASURED on all four, and asserted below as a
tripwire. So a public-API test of this defect **passes vacuously**: it cannot
construct the input that exposes it. A gate written that way would join the
tree's instrument-blind-to-its-own-subject family (`#T1136` / `#T1138` /
`#T1182` / `#T1183`). Every measurement here therefore calls
``_gamma_basis_product`` / ``_normalise_gammas`` directly, or the C symbol
``srmech_algebra_table`` directly, and the public surface appears only in the
TRIPWIRE class — the assertions that rc462 did **not** open γ = 0.

**The independent recursion below is a SANCTIONED HAND-ROLL. Do not
"simplify" it to call ``algebra_table``.** Its entire value is that it shares
no code with either projection: it is the generalised Cayley–Dickson doubling
written straight from the defining formula on dense coefficient vectors,
recursive where the shipped kernel is a loop. A reviewer who repoints it at
the shipped op destroys the gate, and it still passes green.

No numpy. No ``abs()`` — every sign here is Class-K pin-slot composition.
"""

import ctypes
import itertools

import pytest

from srmech import _native
from srmech.cascade import cayley_dickson as cd
from srmech.math.q import Q

# ══════════════════════════════════════════════════════════════════════════
# THE INDEPENDENT RECURSION — sanctioned hand-roll; shares no code with the
# shipped kernel or its C peer.
#
#     (a1, a2)(b1, b2) = (a1·b1 + γ·conj(b2)·a2,  b2·a1 + a2·conj(b1))
#     conj(a1, a2)     = (conj(a1), −a2)
#
# on DENSE integer coefficient vectors of length 2ⁿ, recursing on n. `gammas`
# is in LADDER order, so ``gammas[n-1]`` is the OUTERMOST doubling — the one
# this call performs — and the recursive calls see ``gammas[:n-1]``.
# ══════════════════════════════════════════════════════════════════════════


def _ref_conj(n, x):
    if n == 0:
        return x
    h = 1 << (n - 1)
    return _ref_conj(n - 1, x[:h]) + tuple(-v for v in x[h:])


def _ref_mul(n, gammas, x, y):
    if n == 0:
        return (x[0] * y[0],)
    h = 1 << (n - 1)
    a1, a2 = x[:h], x[h:]
    b1, b2 = y[:h], y[h:]
    gamma = gammas[n - 1]
    cross = _ref_mul(n - 1, gammas, _ref_conj(n - 1, b2), a2)
    first = tuple(u + gamma * v
                  for u, v in zip(_ref_mul(n - 1, gammas, a1, b1), cross))
    second = tuple(u + v
                   for u, v in zip(_ref_mul(n - 1, gammas, b2, a1),
                                   _ref_mul(n - 1, gammas, a2,
                                            _ref_conj(n - 1, b1))))
    return first + second


def _ref_basis_product(dim, gammas, i, j):
    """``e_i·e_j`` read off the dense reference product, as ``(index, sign)``.

    The generalised product is monomial, so at most one coordinate is nonzero.
    When the whole vector is zero — which is what a degenerate rung produces —
    the index is still ``i ⊕ j`` and the sign is ``0``, matching the shipped
    kernel's convention that the index is structural and the sign carries the
    vanishing.
    """
    n = dim.bit_length() - 1
    ei = tuple(1 if k == i else 0 for k in range(dim))
    ej = tuple(1 if k == j else 0 for k in range(dim))
    prod = _ref_mul(n, tuple(gammas), ei, ej)
    nz = [(k, v) for k, v in enumerate(prod) if v != 0]
    assert len(nz) <= 1, f"reference product is not monomial: {prod}"
    if not nz:
        return (i ^ j, 0)
    return nz[0]


# ══════════════════════════════════════════════════════════════════════════
# THE PRE-rc462 SPELLINGS, kept verbatim as CONTROLS.
#
# These are the exact lines rc462 replaced. They are here so the gate can prove
# it distinguishes: the fix must be a NO-OP on ±1 (where the old spelling is
# correct) and must DISAGREE at γ = 0 (where it was not). A gate that cannot
# show both halves is not a measurement.
# ══════════════════════════════════════════════════════════════════════════


def _pre_rc462_basis_product(dim, gammas, i, j):
    """``_gamma_basis_product`` as it stood before rc462 — the dichotomy form."""
    sign = 1
    index = 0
    p, q = i, j
    cur = dim
    while cur > 1:
        m = cur >> 1
        gamma = gammas[cur.bit_length() - 2]
        ph = 1 if p >= m else 0
        qh = 1 if q >= m else 0
        pl = p - m if ph else p
        ql = q - m if qh else q
        if ph == 0 and qh == 0:
            top, p, q = 0, pl, ql
        elif ph == 0 and qh == 1:
            top, p, q = 1, ql, pl
        elif ph == 1 and qh == 0:
            top, p, q = 1, pl, ql
            if ql != 0:
                sign = -sign
        else:
            top, p, q = 0, ql, pl
            if (ql == 0) if gamma < 0 else (ql != 0):
                sign = -sign
        if top:
            index += m
        cur = m
    return index, sign


def _pre_rc462_norm_route(g):
    """``cd_norm_sq``'s pre-rc462 routing predicate."""
    return any(v > 0 for v in g)


def _rc462_norm_route(g):
    """``cd_norm_sq``'s rc462 routing predicate — the law the fast path needs."""
    return any(v != -1 for v in g)


def _pm1_vectors(max_levels):
    for n in range(0, max_levels + 1):
        for g in itertools.product((1, -1), repeat=n):
            yield (1 << n), g


# ══════════════════════════════════════════════════════════════════════════
# CLASS 1 — the fix is a NO-OP on the shipped ±1 domain.
# ══════════════════════════════════════════════════════════════════════════


def test_pm1_domain_is_unmoved_127_vectors_299593_cells():
    """Every ±1 γ vector at dims 1–64: shipped kernel == pre-rc462 spelling."""
    vectors = 0
    cells = 0
    mismatches = []
    for dim, g in _pm1_vectors(6):
        vectors += 1
        for i in range(dim):
            for j in range(dim):
                cells += 1
                got = cd._gamma_basis_product(dim, g, i, j)
                want = _pre_rc462_basis_product(dim, g, i, j)
                if got != want:
                    mismatches.append((dim, g, i, j, got, want))
    assert vectors == 127, vectors
    assert cells == 299593, cells
    assert mismatches == [], mismatches[:5]


def test_definite_ladder_still_equals_cd_basis_product():
    """γ = −1 everywhere IS :func:`cd_basis_product`, the shipped algebra."""
    bad = []
    for n in range(0, 7):
        dim = 1 << n
        g = (-1,) * n
        for i in range(dim):
            for j in range(dim):
                if cd._gamma_basis_product(dim, g, i, j) != cd.cd_basis_product(dim, i, j):
                    bad.append((dim, i, j))
    assert bad == [], bad[:5]


def test_norm_sq_routing_predicate_agrees_on_all_63_pm1_vectors():
    """The pre-rc462 and rc462 routing predicates agree on every ±1 vector."""
    n_vectors = 0
    disagreements = []
    for _dim, g in _pm1_vectors(5):
        n_vectors += 1
        if _pre_rc462_norm_route(g) != _rc462_norm_route(g):
            disagreements.append(g)
    assert n_vectors == 63, n_vectors
    assert disagreements == [], disagreements


def test_norm_sq_values_unmoved_on_every_pm1_twist():
    """``cd_norm_sq`` on every basis element of every ±1 twist, dims 2–32.

    Read against the cocycle's own diagonal, which is what the op claims to
    compute: ``N(x) = Σᵢ xᵢ·x̄ᵢ·sign_γ(i, i)``.
    """
    bad = []
    for dim, g in _pm1_vectors(5):
        if dim == 1:
            continue
        for i in range(dim):
            e = [0] * dim
            e[i] = 1
            _idx, sign = cd._gamma_basis_product(dim, g, i, i)
            want = Q(sign) * (Q(1) if i == 0 else Q(-1))
            if cd.cd_norm_sq(e, gammas=g) != want:
                bad.append((dim, g, i))
    assert bad == [], bad[:5]


def test_definite_norm_sq_still_takes_the_coordinate_fast_path():
    """γ = −1 everywhere must answer exactly as ``gammas=None`` — Σ xᵢ²."""
    bad = []
    for n in range(1, 6):
        dim = 1 << n
        for i in range(dim):
            e = [0] * dim
            e[i] = 3
            if cd.cd_norm_sq(e) != cd.cd_norm_sq(e, gammas=(-1,) * n):
                bad.append((dim, i))
    assert bad == [], bad


# ══════════════════════════════════════════════════════════════════════════
# CLASS 2 — the kernel is now CORRECT at γ = 0, measured against the
# independent recursion. 39 patterns = 3 (dim 2) + 9 (dim 4) + 27 (dim 8)
# over γ ∈ {−1, 0, +1}.
# ══════════════════════════════════════════════════════════════════════════


def _trichotomy_patterns():
    for n in (1, 2, 3):
        for g in itertools.product((-1, 0, 1), repeat=n):
            yield (1 << n), g


def test_kernel_matches_independent_recursion_on_all_39_patterns():
    n_patterns = 0
    agree = 0
    failures = []
    for dim, g in _trichotomy_patterns():
        n_patterns += 1
        ok = True
        for i in range(dim):
            for j in range(dim):
                if cd._gamma_basis_product(dim, g, i, j) != _ref_basis_product(dim, g, i, j):
                    ok = False
                    failures.append((dim, g, i, j))
        if ok:
            agree += 1
    assert n_patterns == 39, n_patterns
    assert agree == 39, (agree, failures[:5])


def test_the_gate_can_fail_pre_rc462_spelling_scores_14_of_39():
    """VACUITY CONTROL. The pre-rc462 spelling agrees on exactly the 14
    all-±1 patterns (2 + 4 + 8) and on none of the 25 that contain a zero.

    Without this, ``39/39`` above could be an instrument that cannot return
    otherwise.
    """
    n_patterns = 0
    agree = 0
    agreeing = []
    for dim, g in _trichotomy_patterns():
        n_patterns += 1
        if all(_pre_rc462_basis_product(dim, g, i, j)
               == _ref_basis_product(dim, g, i, j)
               for i in range(dim) for j in range(dim)):
            agree += 1
            agreeing.append(g)
    assert n_patterns == 39, n_patterns
    assert agree == 14, (agree, agreeing)
    assert all(0 not in g for g in agreeing), agreeing
    assert sum(1 for _d, g in _trichotomy_patterns() if 0 not in g) == 14


def test_gamma_zero_is_no_longer_the_split_table():
    """The single sharpest statement of defect (a): at HEAD these were equal."""
    def table(dim, g):
        return [[cd._gamma_basis_product(dim, g, i, j) for j in range(dim)]
                for i in range(dim)]

    for dim, n in ((2, 1), (4, 2), (8, 3)):
        zero = table(dim, (0,) * n)
        split = table(dim, (1,) * n)
        definite = table(dim, (-1,) * n)
        assert zero != split, dim
        assert zero != definite, dim
        # and the pre-rc462 spelling is where they WERE equal
        pre_zero = [[_pre_rc462_basis_product(dim, (0,) * n, i, j)
                     for j in range(dim)] for i in range(dim)]
        pre_split = [[_pre_rc462_basis_product(dim, (1,) * n, i, j)
                      for j in range(dim)] for i in range(dim)]
        assert pre_zero == pre_split, dim
    # mixed vector: the aliasing was per-rung, not only all-zero
    assert (table(4, (0, -1)) != table(4, (1, -1)))
    assert ([[_pre_rc462_basis_product(4, (0, -1), i, j) for j in range(4)]
             for i in range(4)]
            == [[_pre_rc462_basis_product(4, (1, -1), i, j) for j in range(4)]
                for i in range(4)])


def test_gamma_zero_at_dim_2_is_the_dual_number_table():
    """ℝ[ε]/(ε²): e₀ is the unit, e₁² = 0. The degenerate rung, named."""
    got = [[cd._gamma_basis_product(2, (0,), i, j) for j in range(2)]
           for i in range(2)]
    assert got == [[(0, 1), (1, 1)], [(1, 1), (0, 0)]], got


def test_gamma_zero_sign_is_absorbing_across_levels():
    """A zero at any rung survives every later rung — the sign is a product."""
    # dim 8, γ = 0 only at the OUTERMOST rung: every cross term through that
    # rung vanishes, and nothing downstream can revive it.
    zeros = 0
    total = 0
    for i in range(8):
        for j in range(8):
            total += 1
            _idx, sign = cd._gamma_basis_product(8, (-1, -1, 0), i, j)
            if sign == 0:
                zeros += 1
    assert total == 64
    assert zeros == 16, zeros          # the (ph, qh) == (1, 1) quadrant
    # and never a value outside {-1, 0, 1}
    seen = {cd._gamma_basis_product(8, g, i, j)[1]
            for g in itertools.product((-1, 0, 1), repeat=3)
            for i in range(8) for j in range(8)}
    assert seen == {-1, 0, 1}, seen


def test_norm_sq_routing_predicate_disagrees_exactly_where_it_must():
    """The rc462 predicate routes γ = 0 to the cocycle; the old one did not.

    This is defect (b) stated as a measurement. It is invisible on ±1 (proved
    above) and decides the answer the moment a zero appears.
    """
    disagreeing = [g for n in (1, 2, 3)
                   for g in itertools.product((-1, 0, 1), repeat=n)
                   if _pre_rc462_norm_route(g) != _rc462_norm_route(g)]
    assert disagreeing, "predicate control cannot fire"
    assert all(0 in g for g in disagreeing), disagreeing
    # every vector containing a 0 and no +1 is exactly the disagreement set
    expected = [g for n in (1, 2, 3)
                for g in itertools.product((-1, 0, 1), repeat=n)
                if 0 in g and 1 not in g]
    assert disagreeing == expected, (disagreeing, expected)
    # and the consequence, executed on the kernel: N(e₁) at γ = 0
    _idx, sign = cd._gamma_basis_product(2, (0,), 1, 1)
    assert sign == 0
    cocycle_answer = Q(sign) * Q(-1)          # x₁·x̄₁ = 1·(−1)
    coordinate_answer = Q(1)                  # Σ xᵢ² for e₁
    assert cocycle_answer == Q(0)
    assert cocycle_answer != coordinate_answer


# ══════════════════════════════════════════════════════════════════════════
# CLASS 3 — THE TRIPWIRE. rc462 did NOT open γ = 0. If any of these stops
# raising, the public contract has moved and this whole file's "latent"
# framing is false.
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda: cd.algebra_table(2, (0,)), id="algebra_table_dim2"),
        pytest.param(lambda: cd.algebra_table(4, (0, -1)), id="algebra_table_mixed"),
        pytest.param(lambda: cd.algebra_table(8, (-1, -1, 0)), id="algebra_table_outer"),
        pytest.param(lambda: cd.cd_norm_sq([1, 2], gammas=(0,)), id="cd_norm_sq"),
        pytest.param(lambda: cd._normalise_gammas(2, (0,)), id="_normalise_gammas"),
    ],
)
def test_public_contract_still_refuses_gamma_zero(call):
    with pytest.raises(ValueError) as exc:
        call()
    assert "sign, not a scale" in str(exc.value)


def test_the_validator_is_the_only_thing_standing_there_and_says_so():
    """``_normalise_gammas`` is the PUBLIC CONTRACT, and its docstring says so.

    The defect's real shape was that this function was doing correctness work
    while presenting as input hygiene. After rc462 it does contract work only —
    and the docstring has to carry that, because the next reader of the kernel
    will otherwise re-derive the same wrong conclusion.
    """
    doc = cd._normalise_gammas.__doc__ or ""
    assert "PUBLIC CONTRACT" in doc
    assert "0" in doc and "degenerate" in doc


def test_kernel_docstring_states_the_multiplicative_law_not_the_dichotomy():
    doc = cd._gamma_basis_product.__doc__ or ""
    # the exact pre-rc462 sentence, which lived on one line
    assert "flips the sign exactly when" not in doc
    assert "MULTIPLICATION by" in doc
    assert "LATENT, never live" in doc


# ══════════════════════════════════════════════════════════════════════════
# CLASS 4 — the C peer. cd_gamma_basis is `static` and no file in c/test/
# #includes a ../src/*.c, so the C half of this fix is unreachable from the
# C-side tests: this is the ONLY place it is measured.
# ══════════════════════════════════════════════════════════════════════════


def _c_algebra_table(lib, dim, g):
    n = len(g)
    arr = (ctypes.c_int * n)(*g) if n else None
    buf = (ctypes.c_int64 * (dim * dim * dim))()
    rc = lib.srmech_algebra_table(dim, arr, ctypes.c_size_t(n), buf)
    if rc != 0:
        return rc, None
    return rc, [[[buf[(i * dim + j) * dim + k] for k in range(dim)]
                 for j in range(dim)] for i in range(dim)]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native library loaded")
def test_c_peer_unmoved_on_every_pm1_gamma_vector():
    """63 ±1 vectors, dims 1–32: the C table is the Python table, cell for cell."""
    lib = _native.LIB
    assert lib is not None
    checked = 0
    bad = []
    for dim, g in _pm1_vectors(5):
        checked += 1
        rc, got = _c_algebra_table(lib, dim, g)
        if rc != 0 or got != cd.algebra_table(dim, g):
            bad.append((dim, g, rc))
    assert checked == 63, checked
    assert bad == [], bad[:5]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native library loaded")
def test_c_definite_cocycle_bit_identical_over_5461_cells():
    lib = _native.LIB
    cells = 0
    bad = []
    for n in range(0, 7):
        dim = 1 << n
        for i in range(dim):
            for j in range(dim):
                cells += 1
                oi, os_ = ctypes.c_int(), ctypes.c_int()
                rc = lib.srmech_cd_basis_product(dim, i, j, ctypes.byref(oi),
                                                 ctypes.byref(os_))
                if rc != 0 or (oi.value, os_.value) != cd.cd_basis_product(dim, i, j):
                    bad.append((dim, i, j))
    assert cells == 5461, cells
    assert bad == [], bad[:5]


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="no native library loaded")
def test_c_peer_still_refuses_gamma_zero():
    """``cd_check_gammas`` is the C half of the contract, and it did not move."""
    lib = _native.LIB
    for dim, g in ((2, (0,)), (4, (0, -1)), (8, (-1, -1, 0))):
        rc, got = _c_algebra_table(lib, dim, g)
        assert rc == _native.SRMECH_ERR_BAD_INPUT, (dim, g, rc)
        assert got is None


def test_c_source_carries_no_gamma_sign_branch_and_no_dichotomy_prose():
    """The C hunk landed. Read the CODE, not the prose about it.

    Both source-level assertions below run over comment-masked text, because
    this rc's own explanatory comments *quote the removed spelling verbatim* —
    a substring scan over raw source cannot tell a ban from its own statement,
    and the first draft of this gate failed on exactly that.
    """
    import pathlib
    from tests.test_jpl_audit import _mask_c_literals
    here = pathlib.Path(__file__).resolve()
    c_src = here.parents[2] / "c" / "src" / "srmech_cayley_dickson.c"
    if not c_src.is_file():        # wheel install — no C sources alongside
        pytest.skip("C sources not present (installed package, not source tree)")
    raw = c_src.read_text(encoding="utf-8")
    code = _mask_c_literals(raw)
    assert "gamma < 0" not in code, "the dichotomy branch is still live C code"
    assert "sign * ((ql == 0) ? gamma : -gamma)" in code
    # the tripwire assert stays STRICT — it is what says the contract is closed
    assert "assert(sign == 1 || sign == -1);" in code
    # the prose moved too (checked on the RAW text, where comments survive)
    assert "flips it exactly when ql != 0" not in raw
    assert "MULTIPLICATION by the" in raw


def test_no_c_test_file_can_reach_the_static_kernel():
    """The structural reason the C half is measured HERE and nowhere else.

    ``cd_gamma_basis`` is ``static``. The C tests LINK the library, so a static
    is invisible to them — and zero files in ``c/test/`` ``#include`` a
    ``../src/*.c``. This is also why rc462 did not add a C-side γ = 0 refusal:
    it would be a permanently unreachable, unexecutable branch.
    """
    import pathlib
    here = pathlib.Path(__file__).resolve()
    c_test = here.parents[2] / "c" / "test"
    if not c_test.is_dir():
        pytest.skip("C sources not present (installed package, not source tree)")
    files = sorted(c_test.glob("*.c"))
    assert files, c_test
    including_src = [
        p.name for p in files
        for line in p.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith("#include") and "src/" in line
    ]
    assert including_src == [], including_src
    c_src = (here.parents[2] / "c" / "src" / "srmech_cayley_dickson.c")
    from tests.test_jpl_audit import _mask_c_literals
    code = _mask_c_literals(c_src.read_text(encoding="utf-8"))
    assert "static srmech_status_t cd_gamma_basis(" in code


def test_python_kernel_never_COMPARES_gamma_it_MULTIPLIES_by_it():
    """The structural statement of the fix, by AST — no substring involved.

    A comparison against γ is what encoded the dichotomy; the parameter's
    natural domain has three values, so any comparison silently partitions it
    into two. After rc462 the kernel contains **zero** comparisons naming
    ``gamma`` and composes it multiplicatively instead.
    """
    import ast
    import inspect
    fn = ast.parse(inspect.getsource(cd._gamma_basis_product)).body[0]
    assert isinstance(fn, ast.FunctionDef) and fn.name == "_gamma_basis_product"
    body = fn.body[1:] if (fn.body and isinstance(fn.body[0], ast.Expr)
                           and isinstance(fn.body[0].value, ast.Constant)) else fn.body
    code = "\n".join(ast.unparse(stmt) for stmt in body)
    compares_gamma = [
        node for stmt in body for node in ast.walk(stmt)
        if isinstance(node, ast.Compare)
        and any(isinstance(x, ast.Name) and x.id == "gamma"
                for x in [node.left] + list(node.comparators))
    ]
    assert compares_gamma == [], ast.unparse(compares_gamma[0])
    assert "gamma if ql == 0 else -gamma" in code
    assert "sign * (" in code


def test_python_norm_sq_routes_on_not_definite_not_on_positive():
    """``cd_norm_sq``'s guard, by AST — comments cannot mask this one either."""
    import ast
    import inspect
    fn = ast.parse(inspect.getsource(cd.cd_norm_sq)).body[0]
    assert isinstance(fn, ast.FunctionDef)
    code = ast.unparse(fn)
    assert "v > 0 for v in g" not in code
    assert "v != -1 for v in g" in code


def test_no_alu_abs_call_in_the_cascade_module():
    """Cascade-honesty: sign handling is Class-K ∘ Class-C, never ``abs()``.

    By AST walk, not substring — the module's own prose says ``abs()`` several
    times to forbid it, and a substring scan cannot tell a ban from its own
    statement.
    """
    import ast
    import pathlib
    tree = ast.parse(pathlib.Path(cd.__file__).read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == "abs"]
    assert calls == [], [n.lineno for n in calls]
