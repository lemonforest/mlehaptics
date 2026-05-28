"""srmech.cli — command-line surface.

v0.4.6rc2 introduces the first CLI subcommand: ``srmech status`` per
the out-of-band introspection user direction 2026-05-28. Future
subcommands (sweep / verify / replay) will land alongside.

The module is also runnable directly: ``python -m srmech.cli ...``
forwards to :func:`main`. Plus ``python -m srmech ...`` (one level
up via :mod:`srmech.__main__`) does the same.
"""

from __future__ import annotations

from .main import main

__all__ = ["main"]
