"""rc68 — real-skew `np.linalg.eig` → iS-Hermitian cascade route.

The 2 `np.linalg.eig` sites in `qm/so8.py` operate on **real antisymmetric**
matrices (the `J` complex-structure operator and `ad(H)` for a Cartan element —
both with purely-imaginary `±i·weight` spectra). For real skew `S`, `iS` is
Hermitian, so eigenpairs come from the C-backed `hermitian_eigendecompose(iS)`:
eigenvalues `λ_S = −i·μ` (μ real, ascending), eigenvectors the **same** `V`. The
new private `so8._eig_real_skew` routes both onto that Hermitian cascade — no
`numpy.linalg.eig`.

The eigenvector phase / degenerate-eigenspace basis is solver-chosen (exactly as
`np.linalg.eig` already left it), so this is only sound because so8 consumes `V`
*invariantly*: 584 uses the `+i` eigenspace SPAN (projector basis-invariant) to
rebuild the triplet, 646 uses scale/phase-invariant Rayleigh-quotient weights.
Both invariances are checked here against `numpy.linalg.eig`, on a degenerate
(mult-3, like so8's `J`) real-skew matrix.
"""

from __future__ import annotations

import re
import pathlib

import numpy as np

from srmech.qm.so8 import _eig_real_skew
from srmech.amsc.laplacian import dense_dot_complex


def _degenerate_real_skew(seed: int = 0, n_blocks: int = 3) -> np.ndarray:
    """A real antisymmetric matrix with eigenvalues ±i each of multiplicity
    ``n_blocks`` (the so8-`J` shape), randomly conjugated to be dense."""
    rng = np.random.default_rng(seed)
    n = 2 * n_blocks
    S = np.zeros((n, n))
    for b in range(n_blocks):
        S[2 * b, 2 * b + 1] = 1.0
        S[2 * b + 1, 2 * b] = -1.0
    q, _ = np.linalg.qr(rng.standard_normal((n, n)))
    S = q @ S @ q.T
    return 0.5 * (S - S.T)  # re-skew-symmetrise the round-off


def test_eig_real_skew_reconstructs():
    """S·V = V·diag(λ), λ purely imaginary, on degenerate + non-degenerate skew."""
    for seed, nb in [(0, 3), (1, 2), (2, 1), (7, 4)]:
        S = _degenerate_real_skew(seed, nb)
        lam, V = _eig_real_skew(S)
        np.testing.assert_allclose(S @ V, V * lam, atol=1e-9)        # eigrelation
        np.testing.assert_allclose(lam.real, 0.0, atol=1e-9)         # purely imaginary
        np.testing.assert_allclose(V.conj().T @ V, np.eye(S.shape[0]), atol=1e-9)  # unitary


def test_plus_eigenspace_span_matches_numpy_eig():
    """The +i eigenspace PROJECTOR (basis-invariant) matches numpy.linalg.eig —
    so so8:584's triplet span is preserved even though the degenerate basis differs."""
    S = _degenerate_real_skew(0, 3)
    for ev, V in (np.linalg.eig(S), _eig_real_skew(S)):
        pass
    ev_np, V_np = np.linalg.eig(S)
    ev_h, V_h = _eig_real_skew(S)

    def plus_projector(ev, V):
        cols = [V[:, k] for k in range(V.shape[1]) if ev[k].imag > 0.5]
        P = np.column_stack(cols)
        return P @ np.linalg.pinv(P)

    np.testing.assert_allclose(plus_projector(ev_np, V_np),
                               plus_projector(ev_h, V_h), atol=1e-9)


def test_rayleigh_weights_match_numpy_eig():
    """Per-column Rayleigh-quotient weights (so8:646; scale/phase-invariant) match."""
    S = _degenerate_real_skew(3, 3)

    def weights(V):
        return sorted(
            round(float((dense_dot_complex(V[:, k].conj(), 1j * S @ V[:, k])
                         / dense_dot_complex(V[:, k].conj(), V[:, k])).real), 6)
            for k in range(V.shape[1])
        )

    _, V_np = np.linalg.eig(S)
    _, V_h = _eig_real_skew(S)
    assert weights(V_np) == weights(V_h)


def test_no_np_linalg_eig_call_in_so8():
    """so8 no longer CALLS numpy eig (only _eig_real_skew); the helper is wired."""
    import srmech

    src = (pathlib.Path(srmech.__file__).parent / "qm" / "so8.py").read_text(encoding="utf-8")
    assert not re.search(r"\bnp\.linalg\.eig\s*\(", src)
    assert src.count("_eig_real_skew(") >= 3  # def + 2 call sites
