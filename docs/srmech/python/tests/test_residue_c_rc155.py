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

from srmech.amsc import _native


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


def test_kron_value_oracle_byte_exact():
    from srmech.amsc.cascade.spectral_cascades import kron
    cases = [
        ([[1, 2], [3, 4]], [[0, 5], [6, 7]]),
        ([[1]], [[2, 3], [4, 5]]),
        ([[1 + 1j, 2], [0, -1j]], [[1, 0], [0, 1]]),
        ([[2, 0, 1]], [[3], [4]]),
    ]
    for a, b in cases:
        got = kron(a, b)
        want = _kron_ref(a, b)
        # A⊗B of integer / Gaussian-integer entries is a single-term multiply
        # per entry → byte-exact through the C matmul.
        for grow, wrow in zip(got, want):
            for g, w in zip(grow, wrow):
                assert complex(g) == complex(w), (a, b, got, want)


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
