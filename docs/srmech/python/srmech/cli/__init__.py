"""srmech.cli — command-line surface.

**Four subcommands** — ``status`` / ``bus`` / ``dsl`` / ``mcp``:

* v0.4.6rc2 introduced the first CLI subcommand: ``srmech status``
  (out-of-band introspection per user direction 2026-05-28).
* v0.5.0rc4 added the ``srmech bus`` subcommand family
  (``list / tap / pipe / send / serve``) for operating the
  v0.5.0 cross-process bus from the shell.
* v0.5.0 added ``srmech mcp`` (``emit-mcpb`` — emit a Claude Desktop
  Model Context Protocol bundle).
* v0.5.0rc8 added ``srmech dsl`` (``run`` / ``ops`` / ``visualize`` —
  compose and run cascade chains).

The module is also runnable directly: ``python -m srmech.cli ...``
forwards to :func:`main`. Plus ``python -m srmech ...`` (one level
up via :mod:`srmech.__main__`) does the same.
"""

from __future__ import annotations

from .main import main

__all__ = ["main"]
