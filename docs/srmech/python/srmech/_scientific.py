"""srmech scientific-tier gate (v0.7.0rc47 — the numpy-optional capstone).

numpy is an **optional** dependency from v0.7.0 onward. The Class-N cascade
core — ``srmech.amsc.*`` (the A-N primitives, the rational/cyclic/laplacian
cascades) and the native C surface — runs with **zero numpy** (the §22 +
C-transpile arcs delivered that). The array-numerical **scientific tier** —
``srmech.qm.*`` and ``srmech.signal_processing.*`` — still uses numpy as its
ergonomic array engine and lives behind the ``scientific`` extra.

This module is itself numpy-free; it just turns the bare
``ModuleNotFoundError: No module named 'numpy'`` those subpackages would raise
into a pointed install hint.
"""
from __future__ import annotations


def require_numpy(feature: str):
    """Return the imported ``numpy`` module, or raise a helpful ImportError.

    Called at the top of the scientific-tier subpackage ``__init__`` files so a
    no-numpy install fails with an actionable message instead of an opaque
    ``No module named 'numpy'``. ``ImportError`` (numpy's own error subclasses
    it) so existing ``except ImportError`` handlers keep working.
    """
    try:
        import numpy  # noqa: F401
    except ImportError as exc:  # exercised in numpy-absent installs
        raise ImportError(
            f"{feature} is part of srmech's scientific tier and needs numpy, "
            "an optional dependency as of v0.7.0. Install it with:\n"
            "    pip install 'srmech[scientific]'\n"
            "The Class-N cascade core (srmech.amsc.* and the native C surface) "
            "runs without numpy."
        ) from exc
    return numpy


class _LazyNumpy:
    """A lazy numpy proxy (v0.7.0rc48). Importing the holding module is
    numpy-free; the FIRST numpy attribute access imports numpy or raises the
    ``[scientific]`` hint via :func:`require_numpy`. Used by the ``srmech.amsc``
    modules that mix a numpy-free path (e.g. the Klein-4 HV carrier) with
    ndarray-typed ops (bipolar HDC, the loop family) in one file — so the
    module imports on a plain install and only the ndarray ops trigger the hint.
    """

    def __init__(self, feature):
        # bypass __getattr__ during init
        object.__setattr__(self, "_feature", feature)
        object.__setattr__(self, "_mod", None)

    def __getattr__(self, name):
        mod = object.__getattribute__(self, "_mod")
        if mod is None:
            mod = require_numpy(object.__getattribute__(self, "_feature"))
            object.__setattr__(self, "_mod", mod)
        return getattr(mod, name)


def lazy_numpy(feature: str) -> "_LazyNumpy":
    """Return a lazy numpy proxy for ``feature`` (see :class:`_LazyNumpy`)."""
    return _LazyNumpy(feature)


def make_lazy_op_getattr(package_name: str, op_modules):
    """Build a PEP-562 module ``__getattr__`` for an op-package ``__init__``.

    The scientific-tier op packages (``signal_processing.closed_form_ops`` /
    ``.path_b_ops``) historically did ``from . import (…every op…)`` at package
    import — which transitively imports every op's ``import numpy`` and makes
    ``import srmech.signal_processing`` need numpy even for the numpy-FREE ops
    (rc71). Replacing the eager block with ``__getattr__ = make_lazy_op_getattr(
    __name__, _OP_MODULES)`` defers each op-module import to first attribute
    access — so the package imports with NO numpy, the numpy-free ops
    (the FFT family) import + run numpy-free, and a numpy op imports numpy only
    when *it* is accessed. A numpy ``ModuleNotFoundError`` is re-raised as the
    clean ``[scientific]`` hint (one chokepoint, not a per-module guard).
    """
    import importlib
    import sys

    op_set = frozenset(op_modules)

    def __getattr__(name):
        if name not in op_set:
            raise AttributeError(
                f"module {package_name!r} has no attribute {name!r}"
            )
        try:
            mod = importlib.import_module(f".{name}", package_name)
        except ModuleNotFoundError as exc:
            if (exc.name or "").split(".")[0] == "numpy":
                require_numpy(f"{package_name}.{name}")  # raises the clean hint
            raise
        setattr(sys.modules[package_name], name, mod)  # cache; skip next time
        return mod

    return __getattr__
