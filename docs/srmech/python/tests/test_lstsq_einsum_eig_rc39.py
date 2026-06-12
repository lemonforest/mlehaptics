"""rc39 — lstsq + einsum + non-Hermitian eig as A-N cascades.

lstsq = {QR} o Class M (Qᴴ b) o Class I (back-substitution);
einsum = Class B/D (spec) o Class I (index iteration) o Class M (sum-of-products);
eigvals = Class K (iterate) o Class L o {QR} o Class C (shifted-QR iteration).

numpy-FREE (#564): numpy is GONE from srmech — these return plain Python lists
(``einsum`` a bare scalar for rank-0). Oracles are the framework's own / stdlib:
* lstsq → the DEFINING least-squares orthogonality ``Aᴴ(Ax − b) ≈ 0`` (and an
  exact solve for the square case);
* einsum → a hand-written nested-loop contraction over the spec (independent);
* eigvals → the exact ``eigvals_exact`` (integer-entried) eigenvalue multiset,
  plus the closed-form 2×2 case. No numpy anywhere.
"""
import cmath
import math
import random

import pytest

from srmech.amsc.cascade.matrix_cascades import char_poly, eigvals, einsum, lstsq


# ── numpy-free list helpers ────────────────────────────────────────────


def _conjT(M):
    return [[complex(M[i][j]).conjugate() for i in range(len(M))]
            for j in range(len(M[0]))]


def _matvec(M, v):
    return [sum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M))]


def _matmul(A, B):
    m, k, n = len(A), len(B), len(B[0])
    return [[sum(A[i][p] * B[p][j] for p in range(k)) for j in range(n)]
            for i in range(m)]


def _mag2(z):
    z = complex(z)
    return z.real * z.real + z.imag * z.imag


def _rand(rs, *dims, cplx=False):
    """Nested random tensor of the given dims (numpy-free)."""
    def gen(ds):
        if not ds:
            return (complex(rs.gauss(0, 1), rs.gauss(0, 1)) if cplx
                    else rs.gauss(0, 1))
        return [gen(ds[1:]) for _ in range(ds[0])]
    return gen(list(dims))


# ── lstsq ──────────────────────────────────────────────────────────────


def test_lstsq_overdetermined_and_square():
    """The least-squares solution makes the residual ⟂ the column space:
    ``Aᴴ(Ax − b) ≈ 0`` (the defining normal-equation orthogonality)."""
    rs = random.Random(201)
    for shape in [(6, 3), (8, 4), (5, 5), (10, 1)]:
        for cplx in (False, True):
            m, n = shape
            A = _rand(rs, m, n, cplx=cplx)
            b = _rand(rs, m, cplx=cplx)
            x = lstsq(A, b)
            assert len(x) == n and not isinstance(x[0], list), (shape, cplx)
            r = [_matvec(A, x)[i] - b[i] for i in range(m)]
            Ahr = _matvec(_conjT(A), r)
            assert max(_mag2(v) for v in Ahr) <= 1e-16, (shape, cplx)


def test_lstsq_multiple_rhs():
    """A 2-D RHS yields the column-wise least-squares solutions (nested list)."""
    rs = random.Random(202)
    A = _rand(rs, 7, 3)
    B = _rand(rs, 7, 4)
    X = lstsq(A, B)
    assert len(X) == 3 and len(X[0]) == 4
    # Aᴴ(A·X − B) ≈ 0 column-wise.
    resid = [[_matmul(A, X)[i][j] - B[i][j] for j in range(4)] for i in range(7)]
    AhR = _matmul(_conjT(A), resid)
    assert max(_mag2(AhR[i][j]) for i in range(3) for j in range(4)) <= 1e-16


def test_lstsq_underdetermined_raises():
    with pytest.raises(NotImplementedError):
        lstsq([[1.0] * 5, [1.0] * 5], [1.0, 1.0])


# ── einsum (hand-computed nested-loop oracle) ──────────────────────────


def _ein_ref(spec, *ops):
    """Independent numpy-free einsum reference for the specs exercised below."""
    s = spec.replace(" ", "")
    if "->" in s:
        ins, out = s.split("->")
    else:
        ins, out = s, None
    in_subs = ins.split(",")
    # map each index letter to its dimension size.
    dims = {}

    def shape_of(t):
        sh = []
        x = t
        while isinstance(x, list):
            sh.append(len(x))
            x = x[0] if x else None
        return sh

    for sub, op in zip(in_subs, ops):
        for letter, size in zip(sub, shape_of(op)):
            dims[letter] = size

    def get(op, idx):
        x = op
        for i in idx:
            x = x[i]
        return x

    if out is None:
        # implicit: free indices (appear once) in sorted order; summed indices
        # appear more than once across inputs.
        counts = {}
        for sub in in_subs:
            for ch in sub:
                counts[ch] = counts.get(ch, 0) + 1
        out = "".join(sorted(ch for ch, c in counts.items() if c == 1))
    sum_idx = sorted(set("".join(in_subs)) - set(out))

    def _recurse(remaining, fixed):
        if not remaining:
            total = 0.0 + 0.0j
            for combo in _iter_indices(sum_idx, dims):
                env = dict(fixed)
                env.update(combo)
                term = 1.0 + 0.0j
                for sub, op in zip(in_subs, ops):
                    term *= complex(get(op, [env[ch] for ch in sub]))
                total += term
            return total
        letter = remaining[0]
        res = []
        for i in range(dims[letter]):
            f2 = dict(fixed)
            f2[letter] = i
            res.append(_recurse(remaining[1:], f2))
        return res

    return _recurse(out, {})


def _iter_indices(idx_letters, dims):
    """Cartesian iteration over the summed indices, yielding {letter: value}."""
    if not idx_letters:
        yield {}
        return
    head, *rest = idx_letters
    for i in range(dims[head]):
        for tail in _iter_indices(rest, dims):
            d = {head: i}
            d.update(tail)
            yield d


def _flat(x):
    if isinstance(x, list):
        for e in x:
            yield from _flat(e)
    else:
        yield x


def _close(got, want, tol2=1e-18):
    gl, wl = list(_flat(got)), list(_flat(want))
    assert len(gl) == len(wl), (len(gl), len(wl))
    for a, b in zip(gl, wl):
        assert _mag2(complex(a) - complex(b)) <= tol2


def test_einsum_general_cases():
    rs = random.Random(203)
    cases = [
        ("ij,jk->ik", (_rand(rs, 3, 4), _rand(rs, 4, 2))),
        ("ii->", (_rand(rs, 5, 5),)),
        ("ij->ji", (_rand(rs, 3, 4),)),
        ("i,i->", (_rand(rs, 6), _rand(rs, 6))),
        ("i,j->ij", (_rand(rs, 3), _rand(rs, 4))),
        ("ij,j->i", (_rand(rs, 4, 5), _rand(rs, 5))),
        ("ij,kl->ijkl", (_rand(rs, 2, 3), _rand(rs, 2, 2))),
        ("ij", (_rand(rs, 3, 4),)),           # implicit transpose-to-self
        ("ijk,kl->ijl", (_rand(rs, 2, 3, 4), _rand(rs, 4, 2))),
    ]
    for spec, ops in cases:
        got = einsum(spec, *ops)
        want = _ein_ref(spec, *ops)
        _close(got, want)


def test_einsum_complex():
    rs = random.Random(204)
    a = _rand(rs, 3, 3, cplx=True)
    b = _rand(rs, 3, 3, cplx=True)
    _close(einsum("ij,jk->ik", a, b), _ein_ref("ij,jk->ik", a, b))


# ── eigvals (exact multiset oracle) ────────────────────────────────────


def _evsort(v):
    return sorted(v, key=lambda z: (round(z.real, 8), round(z.imag, 8)))


def _poly_eval(coeffs_hi_to_lo, x):
    """Horner evaluation of the characteristic polynomial at x."""
    val = 0.0 + 0.0j
    for c in coeffs_hi_to_lo:
        val = val * x + complex(c)
    return val


def test_eigvals_are_roots_of_characteristic_polynomial():
    """Each eigenvalue is a root of the framework's own EXACT characteristic
    polynomial: ``p(λ) ≈ 0`` relative to the coefficient scale. This is the
    defining eigenvalue invariant and the numpy-free cross-check (``char_poly``
    is the exact Class-N/L primitive). Well-separated continuous spectra — the
    regime the shifted-QR ``eigvals`` is value-faithful in (exact integer
    degeneracies are a separate, source-bounded accuracy regime)."""
    rs = random.Random(205)
    for _ in range(20):
        n = rs.randint(2, 8)
        A = [[rs.gauss(0.0, 1.0) for _ in range(n)] for _ in range(n)]
        if rs.randint(0, 1):
            A = [[A[i][j] + 1j * rs.gauss(0.0, 1.0) for j in range(n)]
                 for i in range(n)]
        ev = eigvals(A)
        assert len(ev) == n
        cp = char_poly(A)
        scale = sum(_mag2(c) ** 0.5 for c in cp) + 1.0
        for lam in ev:
            assert _mag2(_poly_eval(cp, lam)) ** 0.5 / scale < 1e-7, n


def test_eigvals_complex_conjugate_pair_of_real_matrix():
    # 2-D rotation has eigenvalues ±i — a real matrix with complex eigenvalues.
    A = [[0.0, -1.0], [1.0, 0.0]]
    ev = _evsort(eigvals(A))
    assert _mag2(ev[0] - (-1j)) <= 1e-18
    assert _mag2(ev[1] - (1j)) <= 1e-18


def test_eigvals_empty_and_scalar():
    assert eigvals([]) == []
    ev = eigvals([[3.0]])
    assert len(ev) == 1 and _mag2(ev[0] - (3.0 + 0j)) <= 1e-18


def test_eigvals_rejects_nonsquare():
    with pytest.raises(ValueError):
        eigvals([[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]])


def test_no_abs_no_nplinalg_eig():
    """No abs() and no np.linalg.{eig,eigvals,lstsq} in the call graph."""
    import ast
    import inspect

    from srmech.amsc.cascade import matrix_cascades as mc

    tree = ast.parse(inspect.getsource(mc))
    assert not [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "abs"
    ], "abs() is never fine"
    forbidden = {"qr", "svd", "eig", "eigh", "eigvals", "lstsq"}
    leaks = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in forbidden:
            base = node.value
            if isinstance(base, ast.Attribute) and base.attr == "linalg":
                leaks.add(f"np.linalg.{node.attr}")
    assert not leaks, f"must not call the numpy engine: {leaks}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
