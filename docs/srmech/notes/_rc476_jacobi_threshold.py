"""rc476 (`#T1188`) — the generating code for the Jacobi stopping-rule repair.

WHAT THIS MEASURES, and why it is committed rather than quoted.

``tests/test_qm_gauge.py::test_gauge_path_segment_unitary`` went red in the
PURE (fallback) cells only, while both NATIVE cells stayed green. The numbers
that root-caused it — the off-diagonal trajectory of the cyclic Jacobi, where
each candidate stopping rule cuts that trajectory off, and what each stop
costs downstream — are load-bearing for the repair, so the code that produces
them ships with it (`[[feedback_computational_provenance_discipline]]`).

THE DEFECT. ``_jacobi_eigvals_py`` / ``_jacobi_eig_py`` stopped at
``off <= tolerance`` with ``tolerance = 1e-12`` read as an ABSOLUTE bound,
against a quantity carrying the scale of the matrix. Cyclic Jacobi converges
QUADRATICALLY, so ``off`` does not approach the threshold — it dives past it,
and the delivered accuracy is decided by where a collapsing sequence happens
to straddle a constant. The C twin ``srmech_laplacian_jacobi_eigvals``
(`c/src/srmech_laplacian.c`) has always used ``target = tolerance² ×
off_diag_sq(A₀)``, i.e. ``off <= tolerance × ‖offdiag(A₀)‖_F`` — RELATIVE —
so the two co-equal projections were running DIFFERENT stopping rules. That is
the whole finding; the repair adopts the C rule in Python.

HOW THE BEFORE/AFTER SURVIVES THE REPAIR. This file does NOT read the shipped
kernel's stopping rule. It carries its OWN faithful copy of the sweep loop and
drives it with each rule in turn, so both columns are re-derivable from the
current tree — the "before" number does not depend on a deleted code path.
The copy is checked against the shipped kernel: run with the relative rule it
must reproduce ``_jacobi_eig_py``'s own eigenvalues exactly (record
``kind="agree"``), and if it ever stops doing so the probe says so rather than
reporting a fiction.

Class-K discipline: no ``abs()``. Magnitudes are taken with the explicit
``if d < 0: d = -d`` pin-slot branch, and the rotation tangent's sign is the
``tau >= 0`` branch, exactly as the kernel spells them.

Usage (numpy-ABSENT, from ``docs/srmech/python``)::

    PYTHONDONTWRITEBYTECODE=1 python3 ../notes/_rc476_jacobi_threshold.py \
        ../notes/_rc476_jacobi_threshold.ndjson

With no argument it prints the records to stdout and writes nothing.
"""

import json
import sys

from srmech import _native
from srmech.math.laplacian import _fsqrt, _jacobi_eig_py
from srmech.math.mat import Mat
from srmech.physics.qm import gauge
import srmech


# The absolute constant the kernels used to compare `off` against directly,
# and the same number the relative rule scales by.
TOLERANCE = 1e-12
# The bound `test_gauge_path_segment_unitary` asserts.
GAUGE_BOUND = 1e-12


def _mag(x):
    """Class-K pin-slot magnitude — the spelling the kernels use, not abs()."""
    if x < 0:
        return -x
    return x


def _scaled(s, m):
    return Mat.from_rows(
        [[s * m[i, j] for j in range(m.shape[1])] for i in range(m.shape[0])],
        is_complex=True,
    )


def build_embedding():
    """The exact 6x6 real embedding the failing assertion's pure route builds.

    ``gauge_path_segment(A, su3_generators(), coupling=0.5)`` forms the
    Hermitian 3x3 ``H = g·Aᵃ Tᵃ`` and diagonalises it through the real
    ``2n x 2n`` embedding ``M = [[Re H, -Im H], [Im H, Re H]]``, whose spectrum
    is H's with every eigenvalue DOUBLED.
    """
    a_components = [0.1, -0.2, 0.3, 0.4, -0.5, 0.6, -0.7, 0.2]
    gens = gauge.su3_generators()
    h = _scaled(0.5, gauge.gauge_connection_matrix(a_components, gens))
    n = h.n_rows
    re = [[h[i, j].real for j in range(n)] for i in range(n)]
    im = [[h[i, j].imag for j in range(n)] for i in range(n)]
    m = 2 * n
    out = [[0.0] * m for _ in range(m)]
    for i in range(n):
        for j in range(n):
            out[i][j] = re[i][j]
            out[i][j + n] = -im[i][j]
            out[i + n][j] = im[i][j]
            out[i + n][j + n] = re[i][j]
    return out


def off_diag_norm(a, n):
    return _fsqrt(sum(a[p][q] * a[p][q] for p in range(n) for q in range(p + 1, n)))


def jacobi(matrix, rule, max_sweeps=100):
    """A faithful copy of the shipped sweep loop, with the stopping rule
    supplied by the caller.

    ``rule`` is ``"absolute"`` (the rc475 spelling: ``off <= TOLERANCE``) or
    ``"relative"`` (the C rule this release adopts: ``off <= TOLERANCE ×
    ‖offdiag(A₀)‖_F``). Returns ``(eigvals, V, trajectory, sweeps)``.
    """
    n = len(matrix)
    a = [[float(matrix[i][j]) for j in range(n)] for i in range(n)]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    if rule == "relative":
        target = TOLERANCE * off_diag_norm(a, n)
    elif rule == "absolute":
        target = TOLERANCE
    else:
        raise ValueError("rule must be 'absolute' or 'relative'")
    traj = []
    sweeps = 0
    for _sweep in range(max_sweeps):
        off = off_diag_norm(a, n)
        traj.append(off)
        if off <= target or off < 1e-300:
            break
        sweeps += 1
        for p in range(n - 1):
            for q in range(p + 1, n):
                apq = a[p][q]
                if apq == 0.0:
                    continue
                tau = (a[q][q] - a[p][p]) / (2.0 * apq)
                if tau >= 0.0:
                    t = 1.0 / (tau + _fsqrt(1.0 + tau * tau))
                else:
                    t = -1.0 / (-tau + _fsqrt(1.0 + tau * tau))
                c = 1.0 / _fsqrt(1.0 + t * t)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p] = c * vkp - s * vkq
                    v[k][q] = s * vkp + c * vkq
    order = sorted(range(n), key=lambda j: a[j][j])
    eigvals = [a[j][j] for j in order]
    vecs = [[v[i][order[j]] for j in range(n)] for i in range(n)]
    return eigvals, vecs, traj, sweeps


def orthonormality_dev(v):
    n = len(v)
    worst = 0.0
    for p in range(n):
        for q in range(n):
            d = sum(v[i][p] * v[i][q] for i in range(n))
            if p == q:
                d = d - 1.0
            d = _mag(d)
            if d > worst:
                worst = d
    return worst


def residual(matrix, eigvals, v):
    n = len(matrix)
    worst = 0.0
    for j in range(n):
        for i in range(n):
            d = sum(matrix[i][k] * v[k][j] for k in range(n)) - eigvals[j] * v[i][j]
            d = _mag(d)
            if d > worst:
                worst = d
    return worst


def unitarity_dev_from(eigvals, vecs, n_complex):
    """Rebuild U = V·diag(e^{iλ})·Vᴴ from the embedding and measure
    ``max |U Uᴴ − I|`` — the quantity the failing assertion bounds.

    The embedding's spectrum is doubled, so every SECOND column carries a
    distinct eigenvalue; the complex eigenvector is ``top + i·bottom``.
    """
    from srmech.math import rational as _srn

    cols = []
    lams = []
    for k in range(n_complex):
        col = 2 * k
        w = [complex(vecs[i][col], vecs[i + n_complex][col]) for i in range(n_complex)]
        nrm = _fsqrt(sum(x.real * x.real + x.imag * x.imag for x in w))
        cols.append([x / nrm for x in w])
        lams.append(eigvals[col])
    # U = sum_k e^{i l_k} |w_k><w_k|
    u = [[0j] * n_complex for _ in range(n_complex)]
    for k in range(n_complex):
        ph = _srn.cexp(lams[k])
        w = cols[k]
        for i in range(n_complex):
            for j in range(n_complex):
                u[i][j] = u[i][j] + ph * w[i] * w[j].conjugate()
    worst = 0.0
    for i in range(n_complex):
        for j in range(n_complex):
            d = sum(u[i][k] * u[j][k].conjugate() for k in range(n_complex))
            if i == j:
                d = d - 1.0
            mag = _fsqrt(d.real * d.real + d.imag * d.imag)
            if mag > worst:
                worst = mag
    return worst


def shipped_gauge_dev():
    """``max |U Uᴴ − I|`` through the SHIPPED op, exactly as the test calls it."""
    from srmech.math.laplacian import mat_matmul

    gens = gauge.su3_generators()
    a_components = [0.1, -0.2, 0.3, 0.4, -0.5, 0.6, -0.7, 0.2]
    u = gauge.gauge_path_segment(a_components, gens, coupling=0.5)
    prod = mat_matmul(u, u.conj().T)
    worst = 0.0
    n = prod.shape[0]
    for i in range(n):
        for j in range(n):
            d = prod[i, j]
            if i == j:
                d = d - 1.0
            mag = _fsqrt(d.real * d.real + d.imag * d.imag)
            if mag > worst:
                worst = mag
    return worst


def main(argv):
    out = []

    out.append(
        {
            "kind": "env",
            "srmech_version": srmech.__version__,
            "has_native": bool(_native.HAS_NATIVE),
            "native_abi": _native.NATIVE_ABI_VERSION,
            "expected_abi": _native.EXPECTED_ABI_VERSION,
        }
    )

    m = build_embedding()
    n = len(m)
    n_complex = n // 2
    fro = _fsqrt(sum(m[i][j] * m[i][j] for i in range(n) for j in range(n)))
    off0 = off_diag_norm(m, n)
    out.append(
        {
            "kind": "norm",
            "n": n,
            "fro": repr(fro),
            "offdiag0": repr(off0),
            "tolerance": repr(TOLERANCE),
            "target_absolute": repr(TOLERANCE),
            "target_relative": repr(TOLERANCE * off0),
        }
    )

    results = {}
    for rule in ("absolute", "relative"):
        eigvals, vecs, traj, sweeps = jacobi(m, rule)
        results[rule] = (eigvals, vecs, traj, sweeps)
        for i, off in enumerate(traj):
            out.append(
                {"kind": "trajectory", "rule": rule, "sweep": i, "off": repr(off)}
            )
        out.append(
            {
                "kind": "stop",
                "rule": rule,
                "sweeps": sweeps,
                "off_at_stop": repr(traj[-1]),
                "vtv_dev": repr(orthonormality_dev(vecs)),
                "residual": repr(residual(m, eigvals, vecs)),
                "unitarity_dev": repr(unitarity_dev_from(eigvals, vecs, n_complex)),
                "bound": repr(GAUGE_BOUND),
                "within_bound": unitarity_dev_from(eigvals, vecs, n_complex)
                < GAUGE_BOUND,
            }
        )

    # The pair separations, so "no degeneracy" is measured and not asserted.
    ev = results["relative"][0]
    out.append(
        {
            "kind": "spectrum",
            "embedding_eigvals": [repr(e) for e in ev],
            "pair_gaps": [repr(ev[2 * k + 2] - ev[2 * k]) for k in range(n_complex - 1)],
            "doubling_dev": [repr(ev[2 * k + 1] - ev[2 * k]) for k in range(n_complex)],
        }
    )

    # This probe's copy of the loop must agree with the SHIPPED kernel under
    # the rule the kernel now uses — otherwise the two columns above describe
    # something other than the code that ships.
    shipped_vals, _shipped_vecs = _jacobi_eig_py(m)
    agree = all(
        shipped_vals[i] == results["relative"][0][i] for i in range(len(shipped_vals))
    )
    out.append(
        {
            "kind": "agree",
            "probe_matches_shipped_kernel": agree,
            "shipped_eigvals": [repr(e) for e in shipped_vals],
        }
    )

    dev = shipped_gauge_dev()
    out.append(
        {
            "kind": "gauge",
            "route": "shipped gauge_path_segment",
            "max_dev_identity": repr(dev),
            "bound": repr(GAUGE_BOUND),
            "passes": dev < GAUGE_BOUND,
        }
    )

    lines = [json.dumps(r, sort_keys=True) for r in out]
    if len(argv) > 1:
        with open(argv[1], "w", encoding="utf-8", newline="\n") as fh:
            for line in lines:
                fh.write(line + "\n")
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
