"""siona — a co-name for **srmech** (Stored-Relationship Mechanism).

Installing ``siona`` installs ``srmech`` (its sole dependency) and makes
``import siona`` resolve to exactly the same objects as ``import srmech``.
Every srmech submodule is aliased under the ``siona.*`` namespace, so
``import siona.amsc.cascade`` and ``from siona.amsc import cascade`` work and
return the *same* module objects — srmech stays the single source of truth
(the native library, ``__version__``, and tool-schema all live in srmech).

This is a packaging alias, not a fork: no logic is duplicated here.
"""

import importlib as _importlib
import pkgutil as _pkgutil
import sys as _sys

import srmech as _srmech

# Re-export srmech's public top-level surface so `siona.<name>` works.
for _name in dir(_srmech):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_srmech, _name)
del _name

__version__ = _srmech.__version__
__all__ = [n for n in dir(_srmech) if not n.startswith("_")]
__doc__ = (_srmech.__doc__ or "") + "\n\n(Imported via the `siona` co-name alias.)"

# Alias every srmech submodule under `siona.*` so the import system resolves
# `import siona.<sub>` to the already-imported `srmech.<sub>` module object,
# and bind each as an attribute on its parent so plain attribute access
# (`siona.amsc.cascade`) works too. walk_packages is top-down, so a parent
# alias is always registered before its children.
_self = _sys.modules[__name__]
for _info in _pkgutil.walk_packages(
    _srmech.__path__, _srmech.__name__ + ".", onerror=lambda _n: None
):
    _alias = "siona" + _info.name[len("srmech"):]
    try:
        _mod = _importlib.import_module(_info.name)
    except Exception:  # optional-dependency submodules stay unaliased
        continue
    _sys.modules[_alias] = _mod
    _parent, _, _child = _alias.rpartition(".")
    _pmod = _sys.modules.get(_parent)
    if _pmod is not None:
        setattr(_pmod, _child, _mod)
