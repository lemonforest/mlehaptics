"""rc71 — ``srmech.signal_processing`` is IMPORT-reachable numpy-FREE (#564).

rc70 flipped the FFT op-family's *runtime math* numpy-free, but a fresh
``import srmech.signal_processing`` on a numpy-absent install still raised: the
package ``__init__`` called ``_require_numpy(...)`` eagerly (layer 2), and every
op module was imported eagerly for registry population (layer 3) — so the numpy
ops' ``import numpy`` fired transitively even for the numpy-free ops.

rc71 makes op-registration LAZY (``closed_form_ops`` / ``path_b_ops`` defer each
op-module import to first attribute access via a PEP-562 ``__getattr__``; the
numpy Path-B ops register a deferred loader with the ``path_registry`` so
``lookup`` / ``has_path`` / ``dispatch`` still resolve them by importing-on-
demand) and removes the eager ``__init__`` gate. Net: the package imports with
numpy ABSENT and the FFT family is reachable + runnable numpy-free.

(#564 capstone: numpy has been removed entirely from srmech — there is no
``[scientific]`` extra and nothing raises the old hint, so the former
``test_numpy_op_raises_clean_scientific_hint_numpy_free`` guard has been
deleted. ``registered_ops()`` still lists the former numpy Path-B ops, which
now resolve numpy-free.)

The in-process ``monkeypatch.setitem(sys.modules, "numpy", None)`` pattern (see
``test_fft_family_numpy_absent_rc70``) proves runtime-math numpy-freedom but
NOT fresh-import-numpy-freedom — the module is already bound at collection time,
so the parent ``__init__`` gate is bypassed. To prove the import path itself, we
spawn a SUBPROCESS that blocks numpy via a ``sys.meta_path`` finder *before*
importing anything, so numpy is genuinely absent from the very first import.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

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


def test_import_signal_processing_numpy_free():
    """A fresh ``import srmech.signal_processing`` succeeds with numpy absent."""
    proc = _run_numpy_free(
        """
        import srmech.signal_processing as sp
        print("OK", "dispatch" in dir(sp))
        """
    )
    assert proc.returncode == 0, f"import failed numpy-free:\n{proc.stderr}"
    assert "OK True" in proc.stdout, proc.stdout


def test_fft_family_reachable_and_runs_numpy_free():
    """``closed_form_ops.fft.op`` is reachable + returns a list numpy-free."""
    proc = _run_numpy_free(
        """
        import srmech.signal_processing as sp
        out = sp.closed_form_ops.fft.op([1.0, 2.0, 3.0, 4.0])
        assert isinstance(out, list), type(out)
        assert abs(out[0] - (10 + 0j)) < 1e-9, out[0]
        print("FFT_OK", type(out).__name__)
        """
    )
    assert proc.returncode == 0, f"FFT family not reachable numpy-free:\n{proc.stderr}"
    assert "FFT_OK list" in proc.stdout, proc.stdout


def test_dispatch_fft_numpy_free():
    """The public ``dispatch('fft', ..., path='A')`` resolves numpy-free."""
    proc = _run_numpy_free(
        """
        import srmech.signal_processing as sp
        out = sp.dispatch("fft", [1.0, 2.0, 3.0, 4.0], path="A")
        assert isinstance(out, list), type(out)
        assert abs(out[0] - (10 + 0j)) < 1e-9, out[0]
        print("DISPATCH_OK")
        """
    )
    assert proc.returncode == 0, f"dispatch failed numpy-free:\n{proc.stderr}"
    assert "DISPATCH_OK" in proc.stdout, proc.stdout


def test_registered_ops_declarative_numpy_free():
    """``registered_ops()`` lists the lazily-registrable numpy ops (e.g.
    ``matched_filter``) WITHOUT forcing their numpy-pulling import — declarative
    even on a numpy-absent install."""
    proc = _run_numpy_free(
        """
        import srmech.signal_processing as sp
        ops = set(sp.registered_ops())
        # the numpy-free FFT family is eagerly registered ...
        assert "fft" in ops and "ifft" in ops, sorted(ops)
        # ... and the numpy Path-B ops are listed as pending (lazy) without import
        assert "matched_filter" in ops, sorted(ops)
        assert "sign_quantise" in ops and "wiener" in ops, sorted(ops)
        print("DECLARATIVE_OK", len(ops))
        """
    )
    assert proc.returncode == 0, f"registered_ops not declarative numpy-free:\n{proc.stderr}"
    assert "DECLARATIVE_OK" in proc.stdout, proc.stdout


def test_no_eager_require_numpy_gate_in_init():
    """Static guard: ``signal_processing/__init__.py`` no longer calls
    ``_require_numpy(...)`` / ``require_numpy(...)`` at package import (layer-2
    gate removed in rc71). Down-only — re-adding the eager gate would reinstate
    the numpy-import barrier this rc removed."""
    import srmech

    init = (
        __import__("pathlib").Path(srmech.__file__).parent
        / "signal_processing"
        / "__init__.py"
    )
    text = init.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        assert "_require_numpy(" not in line, (
            "signal_processing/__init__.py reintroduced an eager _require_numpy() "
            "gate — that blocks numpy-free import (rc71 removed it)"
        )
        assert "require_numpy(" not in line, (
            "signal_processing/__init__.py reintroduced an eager require_numpy() "
            "gate — that blocks numpy-free import (rc71 removed it)"
        )
