"""rc124 — ``srmech.qm.pseudo_hermitian`` is IMPORT+RUN-reachable numpy-FREE (#564).

The carrier-removal arc flips ``qm/pseudo_hermitian.py`` (η-pseudo-Hermitian /
PT-symmetric framework) onto the framework-native ``Mat`` carrier: matrices are
``Mat``, state vectors are plain ``complex`` lists, the spectrum comes from
``mat_eigvals``, the η = (V V†)⁻¹ metric inverse from the well-conditioned HPD
``mat_solve``, and the general non-Hermitian eigenVECTORS (for the η
construction) are the null vectors of ``O − λI`` via deterministic Gaussian
elimination. This is the LAST qm carrier, so ``srmech.qm`` is now fully
numpy-free. After the flip pseudo_hermitian imports AND runs with numpy
genuinely absent.

Proving this needs a SUBPROCESS that blocks numpy at ``sys.meta_path`` BEFORE the
first import (the in-process ``monkeypatch`` only proves runtime-math-free, not
fresh-IMPORT-free — see
``[[feedback_carrier_ratchet_misses_require_numpy_subpackage_gates]]``).

The companion guard: ``signal_processing.closed_form_ops.ica_jade`` is now the
pure-wheel CI must-raise example (still a numpy carrier) — this file pins that it
STILL raises the clean ``[scientific]`` hint numpy-blocked, so the CI-guard move
(pseudo_hermitian -> ica_jade) is honest.
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


def test_pseudo_hermitian_imports_and_runs_numpy_free():
    """``qm.pseudo_hermitian`` imports + every public op runs numpy-absent."""
    proc = _run_numpy_free(
        """
        from srmech.qm import pseudo_hermitian as ph
        from srmech.amsc.mat import Mat

        I3 = Mat.from_rows(
            [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)],
            is_complex=True,
        )

        # inner_product_eta with η = I reduces to the standard inner product
        a = [1 + 2j, 3 - 1j, 0 + 1j]
        b = [2 + 0j, 1 + 1j, 4 - 2j]
        val = ph.inner_product_eta(a, b, I3)
        std = sum(a[i].conjugate() * b[i] for i in range(3))
        assert abs(val - std) < 1e-12, val

        # expectation_eta with η = I on a Hermitian O is real
        O = Mat.from_rows(
            [[2.0, 1 + 1j, 0.0], [1 - 1j, 3.0, 0.5j], [0.0, -0.5j, 1.0]],
            is_complex=True,
        )
        psi = [1 + 0.5j, -0.5 + 1j, 2 - 0.5j]
        ev = ph.expectation_eta(O, psi, I3)
        assert abs(ev.imag) < 1e-10, ev

        # construct_eta on a real-spectrum non-Hermitian O makes O η-pseudo-Herm
        T = Mat.from_rows(
            [[1.0, 0.5, 0.0], [0.0, 2.0, 0.5], [0.0, 0.0, 3.0]], is_complex=True
        )
        eta = ph.construct_eta_from_eigendecomposition(T)
        assert type(eta).__name__ == "Mat" and eta.shape == (3, 3)
        assert ph.is_pseudo_hermitian(T, eta, atol=1e-8), "O not eta-pseudo-Herm"
        assert ph.pseudo_hermitian_eigenvalues_real(T, eta, atol=1e-8)

        # complex spectrum is rejected (rotation has eigenvalues ±i)
        R = Mat.from_rows([[0.0, -1.0], [1.0, 0.0]], is_complex=True)
        try:
            ph.construct_eta_from_eigendecomposition(R)
        except ValueError:
            pass
        else:
            raise SystemExit("complex-spectrum O not rejected")
        print("PSEUDO_HERMITIAN_OK")
        """
    )
    assert proc.returncode == 0, f"pseudo_hermitian not numpy-free:\n{proc.stderr}"
    assert "PSEUDO_HERMITIAN_OK" in proc.stdout, proc.stdout


def test_full_qm_subpackage_imports_numpy_free():
    """Every ``srmech.qm`` submodule imports numpy-absent — pseudo_hermitian was
    the last qm carrier, so the whole subpackage is now numpy-free."""
    proc = _run_numpy_free(
        """
        from srmech.qm import (
            spin, bell, sm, single_particle, relativistic, gauge, potentials,
            octonion, so8, triality, propagators, pseudo_hermitian,
        )  # noqa: F401
        print("QM_ALL_OK")
        """
    )
    assert proc.returncode == 0, f"srmech.qm not fully numpy-free:\n{proc.stderr}"
    assert "QM_ALL_OK" in proc.stdout, proc.stdout


def test_ica_jade_still_raises_scientific_hint_numpy_free():
    """``ica_jade`` (the NEW pure-wheel must-raise example) still raises the clean
    ``[scientific]`` hint numpy-blocked — confirming the CI-guard move
    (pseudo_hermitian -> ica_jade) is honest: ica_jade is still a numpy carrier."""
    proc = _run_numpy_free(
        """
        try:
            from srmech.signal_processing.closed_form_ops import ica_jade  # noqa: F401
        except ImportError as exc:
            assert "srmech[scientific]" in str(exc), str(exc)
            print("HINT_OK")
        else:
            raise SystemExit("ica_jade unexpectedly importable numpy-free")
        """
    )
    assert proc.returncode == 0, f"ica_jade guard failed:\n{proc.stderr}"
    assert "HINT_OK" in proc.stdout, proc.stdout
