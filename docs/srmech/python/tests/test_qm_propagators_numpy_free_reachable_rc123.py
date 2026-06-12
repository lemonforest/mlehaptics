"""rc123 — ``srmech.qm.propagators`` is IMPORT+RUN-reachable numpy-FREE (#564).

The carrier-removal arc flips ``qm/propagators.py`` (Feynman scalar / fermion /
photon / massive-vector propagators) onto the framework-native ``Mat`` carrier:
the scalar propagator ``i/(k²−m²+iε)`` is a plain ``complex``, the 4×4 numerators
are ``Mat`` (consumed straight from the numpy-free :mod:`srmech.qm.relativistic`
producers), and the ``kᵘkᵛ`` outer product rides the column·row Class-L
``mat_matmul`` cascade. After the flip propagators imports AND runs with numpy
genuinely absent.

Proving this needs a SUBPROCESS that blocks numpy at ``sys.meta_path`` BEFORE the
first import (the in-process ``monkeypatch.setitem(sys.modules,'numpy',None)``
only proves runtime-math-free, not fresh-IMPORT-free, because the module is
already bound at collection time — see
``[[feedback_carrier_ratchet_misses_require_numpy_subpackage_gates]]`` /
``test_signal_processing_numpy_free_reachable_rc71``). Each test spawns a child
with the meta-path finder installed up front, so numpy is absent from the very
first import, reproducing a clean numpy-absent install.

The companion guard: ``qm/pseudo_hermitian`` is now the pure-wheel CI must-raise
example (still a numpy carrier) — this file pins that it STILL raises the clean
``[scientific]`` hint numpy-blocked, so the CI-guard move is honest.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

# Block numpy at the meta-path level BEFORE the first import. Works whether or
# not numpy is installed in the test environment — the finder raises for any
# `numpy` / `numpy.*` import attempt, reproducing a clean numpy-absent install.
_BLOCK_NUMPY = textwrap.dedent(
    """
    import sys
    class _NoNumpy:
        def find_spec(self, name, path=None, target=None):
            if name == "numpy" or name.startswith("numpy."):
                raise ModuleNotFoundError("No module named 'numpy'", name="numpy")
            return None
    sys.meta_path.insert(0, _NoNumpy())
    """
)


def _run_numpy_free(body: str) -> subprocess.CompletedProcess:
    """Run ``body`` in a subprocess with numpy blocked from the first import.

    The child inherits the parent's import search path (so ``import srmech``
    resolves to the same source tree pytest is exercising)."""
    script = _BLOCK_NUMPY + textwrap.dedent(body)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in sys.path if p)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
    )


def test_propagators_imports_and_runs_numpy_free():
    """``qm.propagators`` imports + all four propagators run numpy-absent."""
    proc = _run_numpy_free(
        """
        from srmech.qm import propagators as prop
        from srmech.amsc.laplacian import mat_matmul, mat_norm
        from srmech.amsc.mat import Mat
        from srmech.qm import relativistic as rel

        # scalar propagator i/(k²−m²) is a plain complex (no numpy)
        G = prop.feynman_scalar_propagator(k_squared=10.0, m=1.0)
        assert abs(G - 1j / 9.0) < 1e-12, G

        # fermion propagator is a 4×4 Mat; (γ·k − m) S_F = i I_4
        k = [3.0, 1.0, 0.0, 0.0]
        S = prop.feynman_fermion_propagator(k, m=1.0)
        assert type(S).__name__ == "Mat" and S.shape == (4, 4), S.shape
        D = rel.dirac_operator_momentum_space(k, 1.0)   # γ·k − m I (Mat)
        prod = mat_matmul(D, S)
        target = Mat.from_rows(
            [[1j if i == j else 0.0 for j in range(4)] for i in range(4)],
            is_complex=True,
        )
        diff = Mat.from_rows(
            [[prod[i, j] - target[i, j] for j in range(4)] for i in range(4)],
            is_complex=True,
        )
        assert mat_norm(diff) < 1e-12, mat_norm(diff)

        # photon propagator in Feynman gauge is a 4×4 Mat with the η signature
        Dph = prop.feynman_photon_propagator(k_squared=4.0)
        assert type(Dph).__name__ == "Mat" and Dph.shape == (4, 4)
        assert abs(Dph[0, 0] - (-1j / 4.0)) < 1e-12, Dph[0, 0]
        assert abs(Dph[1, 1] - (1j / 4.0)) < 1e-12, Dph[1, 1]

        # general covariant gauge exercises the kᵘkᵛ mat_matmul outer cascade
        Dxi = prop.feynman_photon_propagator(k_squared=4.0, gauge_xi=0.5, k=k)
        assert type(Dxi).__name__ == "Mat" and Dxi.shape == (4, 4)

        # massive vector propagator is a 4×4 Mat
        Dm = prop.feynman_massive_vector_propagator(k, m=2.0)
        assert type(Dm).__name__ == "Mat" and Dm.shape == (4, 4)
        print("PROPAGATORS_OK")
        """
    )
    assert proc.returncode == 0, f"propagators not numpy-free:\n{proc.stderr}"
    assert "PROPAGATORS_OK" in proc.stdout, proc.stdout


def test_pseudo_hermitian_still_raises_scientific_hint_numpy_free():
    """``qm.pseudo_hermitian`` (the NEW pure-wheel must-raise example) still
    raises the clean ``[scientific]`` hint numpy-blocked — confirming the CI-guard
    move (propagators -> pseudo_hermitian) is honest: pseudo_hermitian is still a
    numpy carrier, so it must NOT import numpy-absent."""
    proc = _run_numpy_free(
        """
        try:
            from srmech.qm import pseudo_hermitian  # noqa: F401
        except ImportError as exc:
            assert "srmech[scientific]" in str(exc), str(exc)
            print("HINT_OK")
        else:
            raise SystemExit("pseudo_hermitian unexpectedly importable numpy-free")
        """
    )
    assert proc.returncode == 0, f"pseudo_hermitian guard failed:\n{proc.stderr}"
    assert "HINT_OK" in proc.stdout, proc.stdout
