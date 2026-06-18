"""``srmech class`` — discover user-declared ``[class]`` classes from the shell (rc41).

The CLI face of the class-from-TOML surface (#962 Part 2). Two sub-subcommands:

* ``srmech class list`` — enumerate every user-declared class (the shipped seed
  ``Genome`` PLUS any from a ``register_class_dir`` / ``SRMECH_CLASS_PATH`` dir),
  one ``name  (provenance)  — doc`` line each.
* ``srmech class describe NAME`` — the full JSON descriptor (fields + methods +
  ``binds`` + provenance) so a user / agent sees what a class offers before
  constructing it via ``srmech.dsl.make_class``.

Module is ``klass`` (``class`` is a Python keyword); the CLI token is ``class``.
Mirrors :mod:`srmech.cli.dsl`. Construction + method-run stays the Python /
``srmech.dsl.run_class_method`` surface (the methods take Klein-4 vectors, not
shell-ergonomic args) — this CLI is the discovery face.
"""

from __future__ import annotations

import argparse
import json

from srmech.dsl import describe_class, list_class_surface


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach ``srmech class`` subparsers to ``parser``."""
    sub = parser.add_subparsers(dest="class_command", required=False)
    sub.add_parser(
        "list",
        help="List every user-declared [class] (shipped seed + bring-your-own).",
        description=(
            "Enumerate the user-declared classes the class-catalog loader sees "
            "(srmech.dsl.list_classes) — the shipped Genome seed plus any from a "
            "register_class_dir / SRMECH_CLASS_PATH directory."
        ),
    )
    desc_p = sub.add_parser(
        "describe",
        help="Print the full JSON descriptor for one class (fields + methods).",
        description=(
            "Print the JSON descriptor for one user-declared class: its fields, "
            "its methods (each method's bound cascade op + the binds), and the "
            "MPM provenance tier. The shape srmech.dsl.make_class constructs."
        ),
    )
    desc_p.add_argument("name", help="the class name (e.g. 'Genome')")


def run(args: argparse.Namespace) -> int:
    """Dispatch one ``srmech class ...`` invocation."""
    cmd = getattr(args, "class_command", None)
    if cmd == "list":
        for c in list_class_surface():
            doc = (c.get("doc", "") or "").strip().splitlines()
            head = doc[0] if doc else ""
            print(f"{c['name']}  ({c['provenance']})  — {head}")
        return 0
    if cmd == "describe":
        print(json.dumps(describe_class(args.name), indent=2))
        return 0
    # No sub-subcommand: show the class list as the default discovery view.
    for c in list_class_surface():
        print(c["name"])
    return 0
