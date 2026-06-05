"""Smoke-test the facade modules for de441-spectral."""

from __future__ import annotations

import pytest

def _assert_dunder_all_resolves(module) -> None:
    missing = [n for n in module.__all__ if not hasattr(module, n)]
    assert not missing, f"{module.__name__}: __all__ lists missing names: {missing}"

def test_bridge_facade() -> None:
    from ephemerides_spectral import bridge
    _assert_dunder_all_resolves(bridge)
    assert hasattr(bridge, "get_system_state")
    assert hasattr(bridge, "get_local_view")
    assert hasattr(bridge, "get_eclipse_probability")

def test_version_facade() -> None:
    from ephemerides_spectral import version
    assert hasattr(version, "__version__")
    assert isinstance(version.__version__, str)


def test_default_backend_auto_resolves() -> None:
    """Regression (v0.29.3rc2): ``get_eclipse_probability`` and
    ``get_local_view`` must accept their OWN default ``backend="auto"``.

    A premature ``_validate_backend(backend)`` in the validate-tuple rejected
    the raw ``"auto"`` before the ``auto -> concrete`` resolution two lines
    below — and against the wrong roster (``{bip, complex128, c}`` instead of
    these functions' ``{auto, bip, c, fpu-ref}``). A default-argument call
    therefore returned ``ok=False``. The ``chosen not in {...}`` gate after the
    resolution is the correct check.
    """
    from ephemerides_spectral import bridge

    j2000 = 2451545.0
    ecl = bridge.get_eclipse_probability(j2000)  # default backend="auto"
    assert ecl.get("ok") is True, ecl
    assert ecl["backend"] in ("bip", "c", "fpu-ref")
    assert 0.0 <= ecl["probability"] <= 1.0

    lv = bridge.get_local_view(j2000, "luna", 0.0, 0.0)  # default backend="auto"
    assert lv.get("ok") is True, lv
    assert lv["backend"] in ("bip", "c", "fpu-ref")

    # An invalid backend is still rejected (the resolution gate, not _validate_backend).
    bad = bridge.get_eclipse_probability(j2000, backend="nope")
    assert bad.get("ok") is False
