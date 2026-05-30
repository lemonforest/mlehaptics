"""``srmech mcp`` subcommand group.

v0.5.0 ships one sub-subcommand: ``emit-mcpb`` — emit a Claude
Desktop ``.mcpb`` bundle generated entirely from srmech introspection
(issue #749 / MS #19 / wishlist W13). The bundle's manifest version +
tool list are DERIVED from ``srmech.__version__`` and the advertised
``tool_schema`` surface; nothing is hand-authored.

Mirrors :mod:`srmech.cli.bus`'s nested-subparser shape (``add_arguments``
attaches a sub-subparser set; :func:`run` dispatches on
``args.mcp_subcommand``).

Framework reading: emitting the bundle is Class F (render srmech's own
shape to the Claude Desktop substrate-class) ∘ Class H (self-
introspection) — the package describing its callable shape to another
substrate-class-instance.
"""

from __future__ import annotations

import argparse
import sys
from typing import List


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach the ``srmech mcp`` sub-subparsers to ``parser``."""
    sub = parser.add_subparsers(
        dest="mcp_subcommand", metavar="SUBCOMMAND", required=False,
    )

    p_emit = sub.add_parser(
        "emit-mcpb",
        help="Emit a Claude Desktop .mcpb bundle from srmech introspection.",
        description=(
            "Build manifest.json (version + tool list DERIVED from srmech "
            "introspection; MPR attestation block) and pack <name>.mcpb "
            "(a ZIP with root manifest.json). server.type defaults to "
            "'uv' (host fetches the platform wheel from PyPI at install — "
            "portably handles the compiled libsrmech native dep); "
            "'python' is a user_config-gated fallback."
        ),
    )
    p_emit.add_argument(
        "--out", default=".", metavar="DIR",
        help="Output directory (default: current dir).",
    )
    p_emit.add_argument(
        "--type", dest="server_type", choices=("uv", "python"), default="uv",
        help=(
            "server.type. 'uv' (default, recommended): host fetches the "
            "platform wheel via uv at install. 'python': bundle a "
            "python-type server whose interpreter path is a required "
            "user_config field."
        ),
    )
    p_emit.add_argument(
        "--name", default="srmech",
        help="Bundle + server name (default: srmech).",
    )
    p_emit.add_argument(
        "--manifest-only", dest="manifest_only", action="store_true",
        help="Write only manifest.json (skip the .mcpb ZIP).",
    )
    p_emit.add_argument(
        "--filter", dest="name_filter", default=None, metavar="GLOB",
        help=(
            "Only include tools whose name matches GLOB (fnmatch). "
            "Default: all advertised tools."
        ),
    )


def run(args: argparse.Namespace) -> int:
    """Dispatch the ``mcp`` subcommand parsed into ``args``."""
    sub = getattr(args, "mcp_subcommand", None)
    if sub is None:
        print("usage: srmech mcp {emit-mcpb} ...", file=sys.stderr)
        print(
            "(Run 'srmech mcp emit-mcpb --help' for help.)", file=sys.stderr,
        )
        return 0
    if sub == "emit-mcpb":
        from ..mcp._mcpb import pack_mcpb
        from ..mcp._tools import compile_filter

        nf = compile_filter(getattr(args, "name_filter", None))
        path = pack_mcpb(
            args.out,
            name=args.name,
            server_type=args.server_type,
            manifest_only=args.manifest_only,
            name_filter=nf,
        )
        print(str(path))  # ABSOLUTE path -> discoverable
        return 0
    print(f"unknown mcp subcommand: {sub!r}", file=sys.stderr)
    return 2


__all__ = ["add_arguments", "run"]
