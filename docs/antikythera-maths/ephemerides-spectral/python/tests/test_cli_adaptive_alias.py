"""v0.9.2 — `adaptive` is the primary subcommand for state-dependent
coupling LUT modulation; `breathing` is preserved as a hidden synonym.

These tests prove:
  1. Both subcommands dispatch through the same handler and produce
     byte-identical JSON output.
  2. `adaptive` appears in the toplevel `--help` listing.
  3. `breathing` is suppressed from the toplevel `--help` listing
     (registered with help=argparse.SUPPRESS) but still parses.
  4. The toplevel description references the adaptive-networks
     vocabulary (Gross & Blasius 2008 / adaptive Kuramoto).
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from typing import Any, Dict

import pytest

from ephemerides_spectral.cli import _make_parser, main


def _run_cli_json(*argv: str) -> Dict[str, Any]:
    """Run the CLI and parse the JSON object from its stdout.

    The CLI may prefix the JSON with one-time DEBUG lines from the
    skyfield kernel loader (e.g. when an auxiliary kernel download
    is attempted on first use). We look for the first ``{`` and
    parse from there.
    """
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(list(argv))
    assert rc == 0, f"CLI exited non-zero: argv={argv!r}"
    text = buf.getvalue()
    brace = text.find("{")
    assert brace != -1, f"no JSON in CLI stdout: {text!r}"
    return json.loads(text[brace:])


def test_adaptive_and_breathing_produce_identical_output() -> None:
    """Both subcommands dispatch the same handler — same JSON output."""
    common = ("--jd", "2451545.0",
              "--pair-a", "jupiter", "--pair-b", "saturn",
              "--n-a", "5", "--n-b", "2",
              "--kernel", "de441")
    j_adaptive = _run_cli_json("adaptive", *common)
    j_breathing = _run_cli_json("breathing", *common)
    assert j_adaptive == j_breathing, (
        "adaptive and breathing must produce identical JSON — they "
        "share a single handler. Drift here means the subparsers "
        "are no longer registered through the shared helper."
    )
    # Sanity: neither was a silent error response.
    assert j_adaptive.get("ok") is True, j_adaptive


def test_adaptive_visible_in_toplevel_help() -> None:
    """`adaptive` is the canonical name and must appear in --help."""
    parser = _make_parser()
    help_text = parser.format_help()
    assert "adaptive" in help_text, (
        "`adaptive` should appear as a visible subcommand in the "
        "toplevel --help listing (it is the canonical name for "
        "state-dependent coupling modulation)."
    )


def test_breathing_hidden_from_toplevel_help() -> None:
    """`breathing` is registered with help=SUPPRESS — invisible in --help."""
    parser = _make_parser()
    help_text = parser.format_help()
    # The subcommand listing block is the only place subparsers are
    # advertised. `breathing` must not appear there. (It may legitimately
    # appear in the toplevel description / epilog as a cross-reference.)
    # Argparse renders the subcommand listing as either a `{a,b,c}` choice
    # block or a series of indented entries; in either case, a SUPPRESSed
    # subparser is absent. The simplest robust check is: `breathing` does
    # not appear inside the `{...}` choice listing.
    import re
    choice_blocks = re.findall(r"\{[^{}]*\}", help_text)
    for block in choice_blocks:
        assert "breathing" not in block, (
            f"`breathing` leaked into subcommand listing block: {block!r}. "
            "It should be hidden via help=argparse.SUPPRESS."
        )


def test_breathing_subparser_still_parses() -> None:
    """Hidden does not mean removed — typing `breathing` must still work."""
    parser = _make_parser()
    args = parser.parse_args([
        "breathing", "--jd", "2451545.0",
        "--pair-a", "neptune", "--pair-b", "pluto",
        "--n-a", "3", "--n-b", "2",
    ])
    # The parsed args carry the same handler and the same field names
    # as the `adaptive` subcommand.
    assert args.pair_a == "neptune"
    assert args.pair_b == "pluto"
    assert args.n_a == 3
    assert args.n_b == 2
    assert callable(getattr(args, "func", None))


def test_toplevel_description_references_adaptive_vocabulary() -> None:
    """The framing must point to the network-science literature.

    Visual readers reach for `breathing`; rigorous readers reach for
    `adaptive`. Both names should land them in the same intellectual
    neighborhood once they read the description.
    """
    parser = _make_parser()
    full_help = parser.format_help()
    desc_lower = full_help.lower()
    assert "adaptive" in desc_lower, (
        "Toplevel description should mention `adaptive` so users "
        "discover the canonical name."
    )
    assert "breathing" in desc_lower, (
        "Toplevel description should mention `breathing` so users "
        "who learned the visual metaphor can find their command."
    )


@pytest.mark.parametrize("subcommand", ["adaptive", "breathing"])
def test_subcommand_help_text_renders(subcommand: str) -> None:
    """Both subcommand `--help` outputs must render without crashing."""
    parser = _make_parser()
    sub_parser_action = next(
        a for a in parser._actions if hasattr(a, "choices") and a.choices
        and subcommand in a.choices
    )
    subp = sub_parser_action.choices[subcommand]
    text = subp.format_help()
    # Both must mention --jd (the only required argument).
    assert "--jd" in text
    assert "--pair-a" in text
    assert "--pair-b" in text
