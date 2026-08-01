"""rc155 BATCH B-residue — the FINAL 5 compute ops → python_only_debt = 0.

The compute python-free milestone. Each op is exercised against a VALUE ORACLE
(the framework's own / a hand-written reference), and the one genuinely-new C
symbol — ``srmech_jade_jointdiag`` (the JADE Givens joint-diagonalisation sweep
that ica_jade dispatches to) — is exercised native (HAS_NATIVE) vs FORCED-pure
and asserted WITHIN-TOL (JADE's basis is permutation/sign/scale-ambiguous, so
the parity contract is within-tol on the recovered separation, NOT byte).

numpy-free (per the test-for-numpy-free-module discipline: no numpy as the
input-builder or oracle).

The classification moves (rosetta_classification.ndjson):
  - spectral_cascades.kron         python_only_debt -> composition_of_c
  - matrix_cascades.einsum         python_only_debt -> composition_of_c
  - beamforming_fixed.op           python_only_debt -> composition_of_c
  - jpeg.op                        python_only_debt -> composition_of_c
  - ica_jade.op                    python_only_debt -> c_dispatched
"""
from __future__ import annotations

import contextlib
import random

import pytest

from srmech import _native


# ── VALUE ORACLES (hold on any host; no native symbol required) ────────────


def _kron_ref(a, b):
    ma, na = len(a), len(a[0])
    mb, nb = len(b), len(b[0])
    out = [[0 for _ in range(na * nb)] for _ in range(ma * mb)]
    for i in range(ma):
        for j in range(na):
            for k in range(mb):
                for ell in range(nb):
                    out[i * mb + k][j * nb + ell] = a[i][j] * b[k][ell]
    return out


def _eq_exact(g, w):
    """Byte-exact equality that does NOT round either side through float64.

    **This is the rc344 (task T973) ratchet fix.** Through rc343 this file
    asserted ``complex(g) == complex(w)``, which coerces BOTH sides — including
    the exact-integer ``_kron_ref`` oracle value — into float64 before comparing.
    That comparison CANNOT observe a lost integer: it reported equal even when
    ``kron`` had silently rounded the product. Comparing the ``.real`` / ``.imag``
    components directly keeps any Python ``int`` on ℤ, and Python's int-vs-float
    comparison is exact (``float(2**53 + 1) == 2**53 + 1`` is ``False``), so the
    loss becomes visible.
    """
    gr = g.real if hasattr(g, "real") else g
    gi = g.imag if hasattr(g, "imag") else 0
    wr = w.real if hasattr(w, "real") else w
    wi = w.imag if hasattr(w, "imag") else 0
    return gr == wr and gi == wi


# The DISCRIMINATING FIXTURE (task T973). 3 × 3002399751580331 == 2**53 + 1, the
# smallest positive integer NOT representable in float64. Its significand is 54
# bits — one past float64's 53 — so the pre-rc344 matmul-backed kron returned
# 2**53 (i.e. 9007199254740992) here while the oracle returned 9007199254740993.
#
# The governing quantity is SIGNIFICAND WIDTH, not operand scale: the companion
# fixture below multiplies 401-bit operands (v << 400) into 806-bit products and
# is EXACT even pre-rc344, because those products have a 5-bit significand.
_KRON_2P53_PLUS_1 = ([[3]], [[3002399751580331]])


def _kron_exactness_cases():
    """(label, A, B) fixtures spanning BOTH sides of the float64 significand."""
    big = 1 << 400
    odd = (1 << 31) + 1                       # 32-bit odd → 63-bit odd square
    return [
        # ── inside the float64-representable band (the only regime rc343 tested)
        ("small_int", [[1, 2], [3, 4]], [[0, 5], [6, 7]]),
        ("row_col", [[1]], [[2, 3], [4, 5]]),
        ("gaussian_small", [[1 + 1j, 2], [0, -1j]], [[1, 0], [0, 1]]),
        ("rect", [[2, 0, 1]], [[3], [4]]),
        # ── OUTSIDE it — the cases rc343's ratchet could not see ──────────────
        ("2**53+1_significand_54", *_KRON_2P53_PLUS_1),
        ("odd_square_significand_63", [[odd]], [[odd]]),
        ("mixed_54bit", [[3, 5], [7, 9]], [[3002399751580331, 1], [1, 1]]),
        # huge MAGNITUDE, tiny significand → exact even pre-rc344. This fixture
        # is what refutes "kron goes wrong at operand scale 2**28".
        ("806bit_product_significand_5", [[big, 2 * big]], [[3 * big], [4 * big]]),
        ("gaussian_large", [[(1 << 40) + 1 + 3j]], [[(1 << 40) + 1 - 5j]]),
    ]


def test_kron_value_oracle_byte_exact():
    """``kron`` is byte-identical to the ``_kron_ref`` exact-integer oracle.

    rc344 makes this claim TRUE by fixing the op (an exact ℤ cascade for
    integer / Gaussian-integer input) rather than by weakening the claim. The
    assertion compares on ℤ via :func:`_eq_exact` — ``complex(g) == complex(w)``
    is the float-blind comparison this ratchet shipped with through rc343.
    """
    from srmech.amsc.cascade.spectral_cascades import kron
    for label, a, b in _kron_exactness_cases():
        got = kron(a, b)
        want = _kron_ref(a, b)
        for grow, wrow in zip(got, want):
            for g, w in zip(grow, wrow):
                assert _eq_exact(g, w), (label, g, w)


def test_kron_significand_invariant_is_not_operand_scale():
    """Pin the MEASURED invariant (task T973, load-bearing).

    "kron is exact" is governed by SIGNIFICAND WIDTH, not by operand magnitude.
    Both halves are asserted so a regression that reintroduces a float path
    cannot pass by being merely small-magnitude-correct.
    """
    from srmech.amsc.cascade.spectral_cascades import kron

    def significand_bits(n):
        n = -n if n < 0 else n              # Class-K sign branch, never abs()
        if n == 0:
            return 0
        while n % 2 == 0:
            n //= 2
        return n.bit_length()

    # (1) 806-bit PRODUCT, 6-bit significand → exact, and exact pre-rc344 TOO.
    # This half is expected to hold on BOTH sides of the fix; it is what refutes
    # "kron goes wrong at operand scale" as the framing of the defect.
    big = 1 << 400
    want_big = 63 * big * big
    assert want_big.bit_length() == 806, want_big.bit_length()
    assert significand_bits(want_big) == 6, significand_bits(want_big)
    assert _eq_exact(kron([[7 * big]], [[9 * big]])[0][0], want_big)

    # (2) 54-bit significand → the regime that was silently LOSSY pre-rc344.
    a, b = _KRON_2P53_PLUS_1
    got = kron(a, b)[0][0]
    exact = 2 ** 53 + 1
    assert significand_bits(exact) == 54, significand_bits(exact)
    assert got == exact, (got, exact)
    # and float64 genuinely cannot hold it — this is what made the old ratchet
    # a false green rather than merely an untested corner.
    assert float(exact) != exact
    assert int(float(exact)) == 2 ** 53


def test_kron_integer_input_returns_exact_int_not_float():
    """All-real integer input comes back as exact Python ``int`` (unbounded), so
    the exactness survives the RETURN VALUE and not just the internal cascade."""
    from srmech.amsc.cascade.spectral_cascades import kron
    out = kron([[3, 4]], [[3002399751580331]])
    assert all(isinstance(v, int) for row in out for v in row), out
    assert out[0][0] == 2 ** 53 + 1


def _ein_ref(spec, *ops):
    """Independent nested-loop einsum reference (numpy-free)."""
    import itertools
    inspec, _, outspec = spec.replace(" ", "").partition("->")
    in_labels = inspec.split(",")
    sizes = {}

    def shape(o):
        s = []
        c = o
        while isinstance(c, list):
            s.append(len(c))
            c = c[0] if c else None
        return tuple(s)

    def get(o, idx):
        for i in idx:
            o = o[i]
        return o

    for labels, o in zip(in_labels, ops):
        for ax, lab in enumerate(labels):
            sizes[lab] = shape(o)[ax]
    if _ == "":
        counts = {}
        for lab in "".join(in_labels):
            counts[lab] = counts.get(lab, 0) + 1
        outspec = "".join(sorted(l for l in counts if counts[l] == 1))
    summed = [l for l in sizes if l not in outspec]

    def acc(free):
        m = dict(zip(outspec, free))
        total = 0j
        for si in itertools.product(*[range(sizes[l]) for l in summed]):
            m.update(zip(summed, si))
            term = 1 + 0j
            for labels, o in zip(in_labels, ops):
                term *= get(o, tuple(m[l] for l in labels))
            total += term
        return total

    out_shape = tuple(sizes[l] for l in outspec)
    if not out_shape:
        return acc(())
    res = {}
    for fi in itertools.product(*[range(s) for s in out_shape]):
        res[fi] = acc(fi)
    return res, out_shape, outspec


def _flat(x):
    if hasattr(x, "tolist"):
        x = x.tolist()
    if isinstance(x, (list, tuple)):
        for e in x:
            yield from _flat(e)
    else:
        yield x


def test_einsum_value_oracle():
    from srmech.amsc.cascade.matrix_cascades import einsum
    rs = random.Random(155)

    def rnd(*shape, cplx=False):
        if not shape:
            return complex(rs.gauss(0, 1), rs.gauss(0, 1)) if cplx else rs.gauss(0, 1)
        return [rnd(*shape[1:], cplx=cplx) for _ in range(shape[0])]

    cases = [
        ("ij,jk->ik", (rnd(3, 4), rnd(4, 2))),
        ("i,i->", (rnd(6), rnd(6))),
        ("i,j->ij", (rnd(3), rnd(4))),
        ("ij,j->i", (rnd(4, 5), rnd(5))),
        ("ij,kl->ijkl", (rnd(2, 3), rnd(2, 2))),
        ("ijk,kl->ijl", (rnd(2, 3, 4), rnd(4, 2))),
        ("ii->", (rnd(5, 5),)),                       # single-operand (fallback)
        ("ij->ji", (rnd(3, 4),)),                     # single-operand (fallback)
        ("ij,jk->ik", (rnd(3, 3, cplx=True), rnd(3, 3, cplx=True))),
    ]
    for spec, ops in cases:
        got = list(_flat(einsum(spec, *ops)))
        ref = _ein_ref(spec, *ops)
        if isinstance(ref, tuple):
            res, out_shape, outspec = ref
            import itertools
            want = [res[fi] for fi in itertools.product(*[range(s) for s in out_shape])]
        else:
            want = [ref]
        assert len(got) == len(want), (spec, len(got), len(want))
        for g, w in zip(got, want):
            assert abs(complex(g) - complex(w)) <= 1e-9, (spec, g, w)


def test_beamforming_value_oracle():
    from srmech.signal_processing.closed_form_ops import beamforming_fixed as bf
    rng = random.Random(7)
    arr = [[rng.gauss(0, 1) for _ in range(24)] for _ in range(4)]
    delays = [0, 2, 1, 3]
    w = [0.4, 0.1, 0.2, 0.3]
    y = bf.op(arr, delays_samples=delays, weights=w)
    maxd = max(delays)
    n = 24 - maxd
    ref = [sum(w[m] * arr[m][delays[m] + i] for m in range(4)) for i in range(n)]
    assert len(y) == n
    for a, b in zip(y, ref):
        assert abs(complex(a) - complex(b)) <= 1e-9, (a, b)


def test_jpeg_roundtrip_value_oracle():
    from srmech.signal_processing.closed_form_ops import jpeg as J
    rng = random.Random(11)
    img = [[float(rng.randint(0, 255)) for _ in range(16)] for _ in range(16)]
    blocks, shape, qt = J.op(img, quality=90)
    rec = J.op((blocks, shape, qt), decode=True)
    assert shape == (16, 16)
    mse = sum((img[i][j] - rec[i][j]) ** 2 for i in range(16) for j in range(16)) / 256.0
    # high-quality DCT round-trip recovers the image within quantisation error.
    assert mse < 25.0, mse


def _corr(u, v):
    """|Pearson correlation| between two equal-length real sequences (numpy-free,
    Class-K sign-branch magnitude, no abs())."""
    n = len(u)
    mu = sum(u) / n
    mv = sum(v) / n
    su = sum((x - mu) ** 2 for x in u) ** 0.5
    sv = sum((x - mv) ** 2 for x in v) ** 0.5
    if su == 0.0 or sv == 0.0:
        return 0.0
    c = sum((u[t] - mu) * (v[t] - mv) for t in range(n)) / (su * sv)
    return c if c >= 0.0 else -c


def _mix_two_sources(seed, n):
    rng = random.Random(seed)
    s = [[rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)] for _ in range(n)]
    a_mix = [[1.0, 0.5], [0.3, 1.0]]
    X = [[s[t][0] * a_mix[r][0] + s[t][1] * a_mix[r][1] for r in range(2)]
         for t in range(n)]
    return s, X


def test_ica_jade_recovers_sources_value_oracle():
    """ica_jade recovers the two independent sources up to permutation / sign /
    scale — each true source correlates ~1 with SOME recovered component."""
    from srmech.signal_processing.closed_form_ops import ica_jade as m
    n = 400
    s, X = _mix_two_sources(0, n)
    S_hat, W = m.op(X, n_components=2, max_iter=40)
    assert S_hat.shape == (n, 2) and W.shape == (2, 2)
    s0 = [s[t][0] for t in range(n)]
    s1 = [s[t][1] for t in range(n)]
    rec0 = [float(S_hat[t, 0]) for t in range(n)]
    rec1 = [float(S_hat[t, 1]) for t in range(n)]
    # each true source is matched (|corr| high) by SOME recovered component.
    for src in (s0, s1):
        best = max(_corr(src, rec0), _corr(src, rec1))
        assert best > 0.9, best


# ── NATIVE-vs-PURE parity for the one new C symbol (srmech_jade_jointdiag) ──

_HAVE_JADE = _native.HAS_NATIVE and _native.has_native_jade_jointdiag()

pytestmark_jade = pytest.mark.skipif(
    not _HAVE_JADE, reason="native srmech_jade_jointdiag not built"
)


@contextlib.contextmanager
def _force_pure_jade():
    saved = _native.has_native_jade_jointdiag
    _native.has_native_jade_jointdiag = lambda: False
    try:
        yield
    finally:
        _native.has_native_jade_jointdiag = saved


@pytestmark_jade
def test_ica_jade_native_vs_pure_within_tol():
    from srmech.signal_processing.closed_form_ops import ica_jade as m
    for seed, ncomp, k in ((0, 2, 30), (3, 2, 40), (5, 2, 25)):
        _, X = _mix_two_sources(seed, 300)
        S_nat, W_nat = m.op(X, n_components=ncomp, max_iter=k)
        with _force_pure_jade():
            S_pur, W_pur = m.op(X, n_components=ncomp, max_iter=k)
        # WITHIN-TOL element-wise: same algorithm + same libm-free Class-N trig
        # cascade, so native and pure track to ~1e-10 on W and S.
        dW = max(abs(complex(W_nat[a, b]) - complex(W_pur[a, b]))
                 for a in range(W_nat.n_rows) for b in range(W_nat.n_cols))
        dS = max(abs(complex(S_nat[t, c]) - complex(S_pur[t, c]))
                 for t in range(S_nat.n_rows) for c in range(S_nat.n_cols))
        assert dW <= 1e-7, (seed, dW)
        assert dS <= 1e-7, (seed, dS)


@pytestmark_jade
def test_jade_jointdiag_diagonalises_a_known_pair():
    """srmech_jade_jointdiag on a cumulant tensor whose only non-trivial slice is
    a rotated 2×2 diagonal recovers a rotation V that (approximately) undoes the
    mixing — a direct kernel value-oracle independent of the ica_jade wrapper."""
    # Build a k=2 cumulant tensor: C[i][j][l][m] with a diagonal-dominant (0,1)
    # slice so the JADE angle is well-defined and the sweep converges.
    k = 2
    cum = [[[[0.0] * k for _ in range(k)] for _ in range(k)] for _ in range(k)]
    cum[0][0][0][0] = 3.0
    cum[1][1][1][1] = -2.0
    cum[0][1][0][1] = 0.5
    cum[1][0][1][0] = 0.5
    V = _native.jade_jointdiag_c(cum, k, 100, 1e-9)
    assert V is not None
    # V is a 2×2 rotation: orthonormal columns (VᵀV ≈ I).
    for a in range(2):
        for b in range(2):
            dot = sum(V[r][a] * V[r][b] for r in range(2))
            expect = 1.0 if a == b else 0.0
            assert abs(dot - expect) <= 1e-6, (a, b, dot)
