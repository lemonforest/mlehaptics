"""rc123/124/125 — the octonion CONNECTED COMPONENT is IMPORT+RUN-reachable
numpy-FREE (#564).

The carrier-removal arc flips the octonion connected component together:
``amsc/hdc.py`` (the Moufang loop-bind family) → ``qm/octonion.py`` →
{``qm/so8.py``, ``qm/triality.py``, ``amsc/cascade/hypercomplex_dft.py``}. After
the flip EVERY module imports AND runs with numpy genuinely absent.

Proving this needs a SUBPROCESS that blocks numpy at ``sys.meta_path`` BEFORE
the first import (the in-process ``monkeypatch.setitem(sys.modules,'numpy',None)``
only proves runtime-math-free, not fresh-IMPORT-free, because the module is
already bound at collection time — see
``[[feedback_carrier_ratchet_misses_require_numpy_subpackage_gates]]`` /
``test_signal_processing_numpy_free_reachable_rc71``). Each test spawns a child
with the meta-path finder installed up front, so numpy is absent from the very
first import, reproducing a clean numpy-absent install.
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


def test_octonion_imports_and_runs_numpy_free():
    """``qm.octonion`` imports + the table / L-mult / norm run numpy-absent."""
    proc = _run_numpy_free(
        """
        from srmech.qm import octonion
        tbl = octonion.octonion_mult_table()
        assert isinstance(tbl, list) and tbl[1][2][3] == 1, tbl[1][2][3]
        L = octonion.octonion_left_mult([1.0, 0, 0, 0, 0, 0, 0, 0])
        assert type(L).__name__ == "Mat" and L.shape == (8, 8), L.shape
        # the attestation content-address is reproducible numpy-free.
        att = octonion.octonion_table_attestation()
        assert len(att["attestation"]["response_sha256"]) == 64
        assert abs(octonion.octonion_norm([3.0, 4, 0, 0, 0, 0, 0, 0]) - 5.0) < 1e-12
        print("OCTONION_OK")
        """
    )
    assert proc.returncode == 0, f"octonion not numpy-free:\n{proc.stderr}"
    assert "OCTONION_OK" in proc.stdout, proc.stdout


def test_so8_imports_and_runs_numpy_free():
    """``qm.so8`` imports + g2 / so8-adjoint / an_embedding run numpy-absent."""
    proc = _run_numpy_free(
        """
        from srmech.qm import so8
        g2 = so8.g2_subalgebra()
        assert len(g2) == 14 and type(g2[0]).__name__ == "Mat", len(g2)
        adj = so8.so8_adjoint_basis()
        assert len(adj) == 28, len(adj)
        emb = so8.an_embedding()
        assert len(emb["su3"]) == 8 and len(emb["triplet"]) == 3
        q = so8.quaternion_subalgebra_stabilizer()
        assert q["killing_rank"] == 6 and len(q["killing_spectrum"]) == 6
        print("SO8_OK")
        """
    )
    assert proc.returncode == 0, f"so8 not numpy-free:\n{proc.stderr}"
    assert "SO8_OK" in proc.stdout, proc.stdout


def test_triality_imports_and_runs_numpy_free():
    """``qm.triality`` imports + the order-3 tau / companions run numpy-absent."""
    proc = _run_numpy_free(
        """
        from srmech.qm import triality
        from srmech.amsc.laplacian import mat_matmul, mat_norm
        from srmech.amsc.mat import Mat
        tau = triality.triality_automorphism()
        assert type(tau).__name__ == "Mat" and tau.shape == (28, 28)
        t3 = mat_matmul(mat_matmul(tau, tau), tau)
        I = Mat.from_rows([[1.0 if i == j else 0.0 for j in range(28)] for i in range(28)])
        d = Mat.from_rows([[t3[i, j] - I[i, j] for j in range(28)] for i in range(28)])
        assert mat_norm(d) < 1e-9, mat_norm(d)
        cert = triality.lean_isa_seventh_primitive()["certificate"]
        assert cert["triality_order"] == 3 and cert["chirality_complete_core"] == 7
        print("TRIALITY_OK")
        """
    )
    assert proc.returncode == 0, f"triality not numpy-free:\n{proc.stderr}"
    assert "TRIALITY_OK" in proc.stdout, proc.stdout


def test_hdc_loop_family_imports_and_runs_numpy_free():
    """``amsc.hdc`` imports + the loop / polar families run numpy-absent."""
    proc = _run_numpy_free(
        """
        from srmech.amsc import hdc
        c = hdc.loop_bind([1.0, 2, 3, 4, 5, 6, 7, 8], [8.0, 7, 6, 5, 4, 3, 2, 1])
        assert isinstance(c, list) and len(c) == 8, type(c)
        L = hdc.loop_left_op([1.0, 0, 0, 0, 0, 0, 0, 0])
        assert type(L).__name__ == "Mat" and L.shape == (8, 8)
        x = hdc.cross7([0, 1.0, 0, 0, 0, 0, 0, 0], [0, 0, 1.0, 0, 0, 0, 0, 0])
        assert isinstance(x, list) and abs(x[3] - 1.0) < 1e-12, x
        hd = hdc.loop_bind_hd([1.0] * 16, [2.0] * 16)
        assert isinstance(hd, list) and len(hd) == 16
        # polar family numpy-free (array('b') carrier).
        p = hdc.polar_random(16, seed=1)
        assert p.typecode == "b" and len(p) == 16
        assert set(hdc.polar_bind(p, p)) <= {-1, 0, 1}
        # klein-4 HV carrier still numpy-free.
        kv = hdc.klein4_random(32, seed=2)
        assert type(kv).__name__ == "HV"
        print("HDC_OK")
        """
    )
    assert proc.returncode == 0, f"hdc not numpy-free:\n{proc.stderr}"
    assert "HDC_OK" in proc.stdout, proc.stdout


def test_hypercomplex_dft_imports_and_runs_numpy_free():
    """``amsc.cascade.hypercomplex_dft`` imports + QDFT / coupler run numpy-absent."""
    proc = _run_numpy_free(
        """
        from srmech.amsc.cascade import quaternion_dft, octonion_dft, hypercomplex_couple
        X = quaternion_dft([[1.0, 0, 0, 0], [0, 1.0, 0, 0]])
        assert len(X) == 2 and len(X[0]) == 4, X
        # forward then inverse round-trips (both Z2 axes).
        inv = quaternion_dft(X, inverse=True)
        assert abs(inv[0][1] - 0.0) < 1e-9 and abs(inv[1][1] - 1.0) < 1e-9, inv
        out = hypercomplex_couple([1.0, 2, 3])
        assert len(out) == 4, out
        O = octonion_dft([[1.0, 0, 0, 0, 0, 0, 0, 0]])
        assert len(O) == 1 and len(O[0]) == 8, O
        print("HYPERCOMPLEX_OK")
        """
    )
    assert proc.returncode == 0, f"hypercomplex_dft not numpy-free:\n{proc.stderr}"
    assert "HYPERCOMPLEX_OK" in proc.stdout, proc.stdout
