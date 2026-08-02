"""``srmech.qm`` — DEPRECATION ALIAS for :mod:`srmech.physics.qm`.

ADR-0010 (*namespace declustering*) moved the QM/QFT/SM operations layer under
the new ``srmech.physics`` domain (v0.9.0rc381, `#T1052`): every
``srmech.qm.<sub>`` is now ``srmech.physics.qm.<sub>``. Because ``srmech.qm``
has been a public API since v0.4.0, the break is SOFT for one release — this
module keeps the old dotted path importable by re-exporting the real subpackage
and aliasing each submodule into :data:`sys.modules`, so BOTH forms still work::

    import srmech.qm                              # -> srmech.physics.qm
    from srmech.qm.single_particle import tise_solve

Both emit a :class:`DeprecationWarning`. **The alias will be removed in a future
release** — repoint imports to ``srmech.physics.qm``.

Implementation note. The ``qm`` subpackage is fully numpy-free (#564), so the
eager import of every submodule here is safe on a numpy-absent install (no
``[scientific]`` gate is bypassed). Registering the submodules in
``sys.modules`` under this package's dotted names is what makes
``from srmech.qm.<sub> import ...`` resolve to the moved module rather than
raising ``ModuleNotFoundError`` for a directory that no longer holds those
files.
"""

from __future__ import annotations

import importlib as _importlib
import sys as _sys
import warnings as _warnings

_MOVED_MSG = (
    "srmech.qm moved to srmech.physics.qm in v0.9.0rc381; the alias will be "
    "removed in a future release"
)

_warnings.warn(_MOVED_MSG, DeprecationWarning, stacklevel=2)

# The real subpackage. Importing it also imports srmech.physics (its parent).
_target = _importlib.import_module("srmech.physics.qm")

#: Re-export the moved subpackage's public submodule list verbatim.
__all__ = list(_target.__all__)

# Alias every submodule under this package's dotted path so that both
# ``import srmech.qm.<sub>`` and ``from srmech.qm.<sub> import ...`` resolve to
# the moved module object. Eager (not lazy) because the register-in-sys.modules
# step is what the from-import machinery consults, and qm is numpy-free.
for _sub_name in __all__:
    _mod = _importlib.import_module(f"srmech.physics.qm.{_sub_name}")
    _sys.modules[f"{__name__}.{_sub_name}"] = _mod
    globals()[_sub_name] = _mod


def __getattr__(name):  # PEP 562 — delegate any other attribute to the target.
    return getattr(_target, name)


def __dir__():
    return sorted(set(globals()) | set(__all__))
