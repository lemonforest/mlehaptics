"""siona.cli — the interactive command-line session.

``siona`` at a shell starts the grounded inference loop as a REPL: every line you type is one
``Session.turn`` — routed by the board's declared operators, grounded against srmech's live
tool_schema, driven (real srmech ops run), remembered (never-compacted working memory), and
answered with the calibrated honest-STOP when uncertain.

    $ siona
    siona> remember that water boils at 100 celsius
    [siona.remember] noted (1 items)
    siona> compute the gcd of the boiling point of water and 48
    [srmech] gcd(100, 48) = 4 [operand [100] resolved from: "water boils at 100 celsius"]
    siona> water boils at what fahrenheit
    [siona.answer] 212 fahrenheit (EXACT: ...)

Boards: ``--board english`` (default) | ``bislama`` (the UDHR-attested board) | ``merged``
(bilingual code-switching; the ``save`` homograph resolves by language vote or asks) | a path
to any board TOML descriptor.
"""
import argparse
import os
import sys

__all__ = ["main"]


def _resolve_board(name):
    from .boards import ENGLISH, load_board, merge_boards
    here = os.path.dirname(os.path.abspath(__file__))
    bis_path = os.path.join(here, "descriptors", "bislama_udhr.toml")
    if name == "english":
        return ENGLISH
    if name == "bislama":
        return load_board(bis_path)
    if name == "merged":
        board, conflicts = merge_boards(ENGLISH, load_board(bis_path))
        if conflicts:
            print("(bilingual board: %d homograph(s) resolve by language vote or ask: %s)"
                  % (len(conflicts), ", ".join(conflicts)))
        return board
    return load_board(name)  # a TOML descriptor path


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="siona",
        description="Siona — the grounded RBS-HDC inference session (on srmech).")
    ap.add_argument("--board", default="english",
                    help="english | bislama | merged | path/to/board.toml (default: english)")
    ap.add_argument("--dim", type=int, default=8192, help="hypervector dimension D (default 8192)")
    ap.add_argument("--load", metavar="INSTRUMENT",
                    help="load a knowledge instrument at startup (an RBS-HDC NDJSON + its title index)")
    ap.add_argument("--persist", metavar="STATE", nargs="?", const="",
                    help="checkpoint the session context (never-compacted memory + MPR attestations + "
                         "learned verbs) to this file after every turn (default: ~/.siona/state.json)")
    ap.add_argument("--continue", dest="cont", action="store_true",
                    help="resume the persisted context (from --persist's file or the default) and "
                         "keep checkpointing -- restoring is EXPLICIT, never implicit")
    ap.add_argument("--version", action="store_true", help="print version and exit")
    args = ap.parse_args(argv)

    import siona
    if args.version:
        print("siona", siona.__version__)
        return 0

    board = _resolve_board(args.board)
    print("siona %s — board: %s" % (siona.__version__, board.name))
    print("building the grounding index over srmech's live tool_schema (one-time, ~30s) ...")
    session = siona.Session(board=board, D=args.dim)
    print("ready — %d tools grounded. every line is one turn; 'exit' or Ctrl-D to leave."
          % len(session.g.tools))
    state = None
    if args.persist is not None or args.cont:
        state = args.persist or os.path.expanduser("~/.siona/state.json")
        if args.cont:
            n = session.load_state(state)
            print("[continue] context restored: %d note(s) + attestations from %s" % (n, state)
                  if n else "[continue] no prior context at %s -- starting fresh" % state)
        elif os.path.isfile(state):
            # --persist alone onto an EXISTING state would clobber someone's context: refuse.
            print("state exists at %s -- use --continue to resume it, or --persist <new-path>" % state)
            return 2
        os.makedirs(os.path.dirname(state) or ".", exist_ok=True)
    if args.load:
        print("[siona.load] %s" % session._impl["siona.knowledge.load"](args.load))

    interactive = sys.stdin.isatty()
    while True:
        try:
            line = input("siona> " if interactive else "")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        line = line.strip()
        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break
        if not interactive:
            print("siona> %s" % line)  # echo piped input so transcripts read as sessions
        try:
            _intent, tag, out = session.turn(line)
            print("[%s] %s" % (tag, out))
        except Exception as e:  # a turn must never kill the session
            print("[error] %s: %s" % (type(e).__name__, e))
        if state:
            session.save_state(state)  # crash-safe: every turn checkpoints the context
    return 0


if __name__ == "__main__":
    sys.exit(main())
