"""Regression test: ``__version__`` must match the installed dist
version reported by ``importlib.metadata``.

History: between v1.2.3 and v1.3.1 (six version bumps to
pyproject.toml), `chess_spectral/__init__.py` was never updated and
kept reporting "1.2.3" via ``__version__`` while
``importlib.metadata.version("chess-spectral")`` correctly tracked
the actual dist. The fix derives ``__version__`` dynamically; this
test pins the contract so the two strings can't drift again.

For ``chess_spectral_4d``, the ``VERSION`` constant is the *encoder
format version* (used by cli.py for the format banner) and is
intentionally separate from the dist version. ``__version__`` is
the PEP 396 dist-version and should match ``importlib.metadata``.
"""
from __future__ import annotations

import importlib.metadata


def test_chess_spectral_version_matches_dist():
    """``chess_spectral.__version__`` equals the installed dist
    version. Pre-1.3.2 this was hardcoded and drifted; after the
    fix it derives from ``importlib.metadata``."""
    import chess_spectral
    expected = importlib.metadata.version("chess-spectral")
    assert chess_spectral.__version__ == expected, (
        f"chess_spectral.__version__ = {chess_spectral.__version__!r} "
        f"but the installed dist is {expected!r}. The package's "
        "`__version__` derives from importlib.metadata; if this "
        "assertion fails, the dynamic-derivation pattern in "
        "chess_spectral/__init__.py is broken."
    )


def test_chess_spectral_4d_version_matches_dist():
    """``chess_spectral_4d.__version__`` equals the installed dist
    version (NOT the encoder format ``VERSION`` constant)."""
    import chess_spectral_4d
    expected = importlib.metadata.version("chess-spectral")
    assert chess_spectral_4d.__version__ == expected, (
        f"chess_spectral_4d.__version__ = "
        f"{chess_spectral_4d.__version__!r} but the installed dist is "
        f"{expected!r}. PEP 396 says __version__ should reflect the "
        "package version, not the internal encoder-format version."
    )


def test_chess_spectral_4d_VERSION_alias_matches_dist():
    """``VERSION`` is preserved as a back-compat alias for
    ``__version__`` (downstream callers may have imported the old
    name). Pre-1.3.2 it carried an encoder-format version that
    drifted from the dist; collapsed to the dist version for the
    same reason ``__version__`` did."""
    import chess_spectral_4d
    expected = importlib.metadata.version("chess-spectral")
    assert chess_spectral_4d.VERSION == expected, (
        f"chess_spectral_4d.VERSION = {chess_spectral_4d.VERSION!r} "
        f"but the installed dist is {expected!r}. VERSION is now an "
        "alias for __version__; both should equal the dist version."
    )
