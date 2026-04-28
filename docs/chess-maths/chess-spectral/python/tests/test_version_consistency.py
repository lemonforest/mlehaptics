"""Regression test: ``__version__`` must match the installed dist
version reported by ``importlib.metadata``.

History: between v1.2.3 and v1.3.1 (six version bumps to
pyproject.toml), `chess_spectral/__init__.py` was never updated and
kept reporting "1.2.3" via ``__version__`` while
``importlib.metadata.version("chess-spectral")`` correctly tracked
the actual dist. The fix derives ``__version__`` dynamically; this
test pins the contract so the two strings can't drift again.

This test runs in two CI contexts:

  1. Inside a wheel-test phase (verify-wheels / publish): the wheel
     is pip-installed, so ``importlib.metadata.version("chess-spectral")``
     succeeds and returns the dist version. The test asserts that
     ``__version__`` matches.
  2. Against a source tree without ``pip install -e .`` (the
     `build / test` job that runs CMake + pytest directly): no dist
     metadata is registered. ``importlib.metadata`` raises
     ``PackageNotFoundError``; the package's own fallback returns
     ``"0.0.0+unknown"``. The test asserts the sentinel matches.

Both contexts validate the dynamic-derivation contract — the second
context just exercises the fallback path instead of the happy path.
"""
from __future__ import annotations

import importlib.metadata


def _dist_version_or_none() -> str | None:
    """Return the installed dist version of `chess-spectral`, or
    None if the package isn't pip-installed (e.g., source-tree-only
    pytest invocations like the `build / test` job)."""
    try:
        return importlib.metadata.version("chess-spectral")
    except importlib.metadata.PackageNotFoundError:
        return None


_DIST = _dist_version_or_none()
_FALLBACK = "0.0.0+unknown"


def test_chess_spectral_version_matches_dist_or_fallback():
    """``chess_spectral.__version__`` equals the installed dist
    version (when installed) or the sentinel fallback (when run
    against a non-installed source tree)."""
    import chess_spectral
    expected = _DIST if _DIST is not None else _FALLBACK
    assert chess_spectral.__version__ == expected, (
        f"chess_spectral.__version__ = {chess_spectral.__version__!r}; "
        f"expected {expected!r} (installed dist: {_DIST!r}). The "
        "dynamic-derivation pattern in chess_spectral/__init__.py "
        "broke."
    )


def test_chess_spectral_4d_version_matches_dist_or_fallback():
    """``chess_spectral_4d.__version__`` equals the installed dist
    version (NOT the old encoder-format VERSION constant)."""
    import chess_spectral_4d
    expected = _DIST if _DIST is not None else _FALLBACK
    assert chess_spectral_4d.__version__ == expected, (
        f"chess_spectral_4d.__version__ = "
        f"{chess_spectral_4d.__version__!r}; expected {expected!r} "
        f"(installed dist: {_DIST!r}). PEP 396 says __version__ "
        "should reflect the package version; the dynamic-derivation "
        "pattern in chess_spectral_4d/__init__.py broke."
    )


def test_chess_spectral_4d_VERSION_alias_matches_version():
    """``VERSION`` is preserved as a back-compat alias for
    ``__version__``. Pre-1.3.2 it was a separate encoder-format
    version string that drifted from the dist; post-1.3.2 the two
    are aliased and must always agree."""
    import chess_spectral_4d
    assert chess_spectral_4d.VERSION == chess_spectral_4d.__version__, (
        f"chess_spectral_4d.VERSION = {chess_spectral_4d.VERSION!r} "
        f"but __version__ = {chess_spectral_4d.__version__!r}. "
        "VERSION is now an alias for __version__; the two must "
        "agree regardless of install state."
    )
