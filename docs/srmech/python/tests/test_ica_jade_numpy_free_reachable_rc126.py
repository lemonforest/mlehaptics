"""rc126 — ``signal_processing.closed_form_ops.ica_jade`` is IMPORT+RUN-reachable
numpy-FREE (#564), the LAST ``srmech.signal_processing`` carrier.

The carrier-removal arc flips JADE ICA onto the framework-native ``Mat`` carrier:
the covariance whitening eigendecomposition routes through
``mat_hermitian_eigendecompose`` (NOT the carrier ``hermitian_eigendecompose`` /
``dense_matmul_real`` / ``elementwise_sqrt``, which RAISE numpy-absent); the
fourth-order cumulant tensor is nested Python lists (``Mat`` is 2-D only); the
Givens-rotation joint diagonalisation is explicit numpy-free loops; the whitening
magnitudes use the Class-N ``rational.sqrt`` and the rotation angle the Class-N
``rational.atan2``/``cos``/``sin``. After the flip ``ica_jade`` imports AND runs
with numpy genuinely absent, and the WHOLE ``srmech.signal_processing`` subtree
is numpy-free.

Proving this needs a SUBPROCESS that blocks numpy at ``sys.meta_path`` BEFORE the
first import (see ``[[feedback_carrier_ratchet_misses_require_numpy_subpackage_gates]]``).
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

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


def test_ica_jade_imports_and_runs_numpy_free():
    """``ica_jade`` imports + recovers sources from a mixed signal numpy-absent."""
    proc = _run_numpy_free(
        """
        import random
        from srmech.signal_processing.closed_form_ops import ica_jade as m

        assert "numpy" not in sys.modules, "numpy imported by ica_jade"

        # 2 independent uniform sources, linearly mixed (X = S @ A.T).
        rng = random.Random(0)
        n = 150
        s_true = [[rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0)] for _ in range(n)]
        a_mix = [[1.0, 0.5], [0.3, 1.0]]
        X = [[s[0]*a_mix[r][0] + s[1]*a_mix[r][1] for r in range(2)] for s in s_true]

        S_hat, W = m.op(X, n_components=2, max_iter=10)
        assert type(S_hat).__name__ == "Mat" and type(W).__name__ == "Mat", (
            type(S_hat), type(W))
        assert S_hat.shape == (n, 2), S_hat.shape
        assert W.shape == (2, 2), W.shape
        # recovered sources are finite reals.
        assert all(abs(S_hat[t, c]) < 1e6 for t in range(n) for c in range(2))

        assert "numpy" not in sys.modules, "numpy entered sys.modules during op"
        print("ICA_JADE_OK")
        """
    )
    assert proc.returncode == 0, f"ica_jade not numpy-free:\n{proc.stderr}"
    assert "ICA_JADE_OK" in proc.stdout, proc.stdout


def test_whole_signal_processing_subtree_numpy_free():
    """``srmech.signal_processing`` (every closed_form_op) imports numpy-absent —
    ica_jade was the last carrier."""
    proc = _run_numpy_free(
        """
        import srmech.signal_processing as sp
        ops = sp.closed_form_ops
        # touch every op submodule; none may pull numpy.
        for name in ops.__all__ if hasattr(ops, "__all__") else []:
            getattr(ops, name)
        assert "numpy" not in sys.modules, sorted(
            n for n in sys.modules if n == "numpy" or n.startswith("numpy."))
        print("SP_SUBTREE_OK")
        """
    )
    assert proc.returncode == 0, f"signal_processing not numpy-free:\n{proc.stderr}"
    assert "SP_SUBTREE_OK" in proc.stdout, proc.stdout
