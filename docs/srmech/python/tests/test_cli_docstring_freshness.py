"""§13 D4 anti-staleness ratchet — CLI docstrings enumerate all subcommands.

v0.7.0rc25 (UPSTREAM_NOTES §13 D4). The ``srmech.cli`` module docstrings
had frozen at the v0.5.0rc4 *two-subcommand era* (``status`` + ``bus``),
silently omitting ``dsl`` (v0.5.0rc8) and ``mcp`` (v0.5.0) even after the
live CLI grew to four subcommands — the argparse ``--help`` was refreshed
(v0.6.0rc12) but the module docstrings drifted.

This ratchet pins the module docstrings (and the argparse top-level
description) to enumerate **every** registered top-level subcommand, so a
future subcommand addition that forgets the docstring fails CI rather than
drifting unnoticed. It reads the live subparser registry — no hard-coded
list to itself go stale.
"""
import argparse
import importlib

# NB: ``srmech.cli.__init__`` does ``from .main import main``, which rebinds
# the name ``srmech.cli.main`` to the *function* and shadows the *module*.
# Resolve the module via importlib so we get ``build_parser`` regardless.
_cli_pkg = importlib.import_module("srmech.cli")
_cli_main = importlib.import_module("srmech.cli.main")


def _registered_subcommands():
    """The live set of top-level subcommand names from the argparse tree."""
    parser = _cli_main.build_parser()
    names = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            names.update(action.choices.keys())
    return names


def test_registry_has_the_four_known_subcommands():
    """Sanity floor: the four shipped subcommands are all registered."""
    names = _registered_subcommands()
    assert {"status", "bus", "dsl", "mcp"} <= names, names


def test_cli_main_docstring_enumerates_every_subcommand():
    """``srmech.cli.main`` module docstring names every live subcommand."""
    doc = _cli_main.__doc__ or ""
    missing = [n for n in _registered_subcommands() if n not in doc]
    assert not missing, (
        f"srmech.cli.main docstring omits subcommand(s) {missing}; refresh it "
        f"when adding a subcommand (UPSTREAM_NOTES §13 D4 staleness ratchet)."
    )


def test_cli_package_docstring_enumerates_every_subcommand():
    """``srmech.cli`` package docstring names every live subcommand."""
    doc = _cli_pkg.__doc__ or ""
    missing = [n for n in _registered_subcommands() if n not in doc]
    assert not missing, (
        f"srmech.cli package docstring omits subcommand(s) {missing}; refresh "
        f"it when adding a subcommand (UPSTREAM_NOTES §13 D4 staleness ratchet)."
    )


def test_top_level_help_description_enumerates_every_subcommand():
    """The argparse top-level ``description`` names every live subcommand."""
    parser = _cli_main.build_parser()
    desc = parser.description or ""
    missing = [n for n in _registered_subcommands() if n not in desc]
    assert not missing, (
        f"top-level --help description omits subcommand(s) {missing}."
    )
