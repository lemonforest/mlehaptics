"""Register ephemerides' own config-driven srmech ``[class]`` catalog.

Currently ships one class — ``GatewayNavigation`` (the ITN / etak
gateway-navigation cascade; see ``class_catalog/gateway_navigation.toml``).
Per `[[feedback_prefer_config_driven_toml_classes]]` a domain object that
is a cascade-of-the-14 composition is declared as a ``[class]`` TOML
rather than hand-coded, with etak and ITN as two named views over the one
cascade instead of two parallel code paths.

The registration is idempotent and lazy: :func:`gateway_navigation_class`
registers the catalog dir on first use and returns the
:func:`srmech.dsl.make_class` factory. There is no import-time side
effect — :func:`register` is also exposed for callers (e.g. the LLM
discovery surface) that want the class visible in ``srmech`` introspection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

#: The directory holding ephemerides' ``[class]`` descriptor TOMLs.
CLASS_CATALOG_DIR: Path = Path(__file__).resolve().parent / "class_catalog"

_REGISTERED = False


def register() -> bool:
    """Register :data:`CLASS_CATALOG_DIR` with srmech (idempotent).

    Returns ``True`` if the catalog is registered (now or already), ``False``
    if srmech's class-catalog machinery isn't available or the directory is
    missing (e.g. a stripped install) — callers must not depend on the class
    in that case.
    """
    global _REGISTERED
    if _REGISTERED:
        return True
    if not CLASS_CATALOG_DIR.is_dir():
        return False
    try:
        from srmech.dsl import register_class_dir
    except Exception:
        return False
    register_class_dir(CLASS_CATALOG_DIR)
    _REGISTERED = True
    return True


def gateway_navigation_class() -> Any:
    """Return the ``GatewayNavigation`` DSL-class factory (registering the
    ephemerides class catalog on first call).

    Raises ``RuntimeError`` if the catalog can't be registered (srmech DSL
    absent or descriptor missing).
    """
    if not register():
        raise RuntimeError(
            "GatewayNavigation class unavailable: srmech.dsl class-catalog "
            f"machinery missing or {CLASS_CATALOG_DIR} not packaged"
        )
    from srmech.dsl import make_class
    return make_class("GatewayNavigation")


__all__ = ["CLASS_CATALOG_DIR", "register", "gateway_navigation_class"]
