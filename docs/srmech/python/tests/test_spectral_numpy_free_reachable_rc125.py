"""rc125 — ``srmech.spectral`` is IMPORT+RUN-reachable numpy-FREE (#564).

The carrier-removal arc flips ``srmech/spectral/__init__.py`` (Spike #115 runtime
spectral decompose / delta / recompose / similarity / predict / prediction_error
/ truncate_sparse) onto the framework-native ``Mat`` carrier: the Hermitian
eigendecomposition routes through ``mat_hermitian_eigendecompose``, the
projection / reconstruction are explicit numpy-free matvecs, the complex128
coefficient bytes are ``struct``-packed (byte-identical to the prior layout), the
predict phase is the Class-N ``rational.cexp``, and the truncation magnitudes are
squared-moduli (no abs/sqrt). After the flip ``srmech.spectral`` imports AND runs
with numpy genuinely absent.

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


def test_spectral_imports_and_runs_numpy_free():
    """``srmech.spectral`` imports + the full op surface runs numpy-absent."""
    proc = _run_numpy_free(
        """
        from srmech import spectral as sp

        # path-graph Laplacian (real symmetric Hermitian) as a list-of-lists
        L = [[1.0, -1.0, 0.0, 0.0],
             [-1.0, 2.0, -1.0, 0.0],
             [0.0, -1.0, 2.0, -1.0],
             [0.0, 0.0, -1.0, 1.0]]
        state = [1.0, 2.0, -1.0, 0.5]

        # decompose -> recompose roundtrip (Class-L eigenbasis projection)
        h = sp.decompose(state, L)
        rec = sp.recompose(h, L)
        assert isinstance(rec, list) and len(rec) == 4, type(rec)
        assert max(abs(rec[i] - state[i]) for i in range(4)) < 1e-10

        # predict steps=0 is the identity (phase = 1); byte-identical
        p0 = sp.predict(h, L, steps=0)
        assert p0.coefficients_bytes == h.coefficients_bytes

        # predict steps=2 then recompose stays finite (Class-C phase cascade)
        p = sp.predict(h, L, steps=2, dt=0.3)
        rp = sp.recompose(p, L)
        assert all(abs(x) < 1e6 for x in rp)

        # truncate_sparse keep_k=2 -> exactly 2 nonzero complex128 modes
        t = sp.truncate_sparse(h, keep_k=2)
        chunks = [t.coefficients_bytes[i:i+16]
                  for i in range(0, len(t.coefficients_bytes), 16)]
        nz = sum(1 for c in chunks if c != b"\\x00" * 16)
        assert nz == 2, nz

        # delta / similarity (Class-M HDC on bytes)
        d = sp.delta(h, p)
        assert len(d) == len(h.coefficients_bytes)
        assert abs(sp.similarity(h, h) - 1.0) < 1e-12
        print("SPECTRAL_OK")
        """
    )
    assert proc.returncode == 0, f"spectral not numpy-free:\n{proc.stderr}"
    assert "SPECTRAL_OK" in proc.stdout, proc.stdout
