#!/usr/bin/env python3
"""``regen-all`` — regenerate every generated file, in derived order (rc346, `#T975`).

    python3 tools/regen_all.py            # from docs/srmech/python
    python3 tools/regen_all.py --check    # CI: content-equality, writes nothing
    python3 tools/regen_all.py --list     # show the derived order + the graph

THE PROBLEM THIS REPLACES
=========================
Six generators feed the shipped tree, three of them downstream of a fourth,
and running them by hand had three ways to look like success while producing
a stale tree:

1. **The order is load-bearing.** ``gen_tool_docs`` writes ``_tool_docs.py``,
   ``tool_schema`` merges that into every ``ToolEntry.explanation``, and
   ``gen_tool_registry`` bakes the merged prose into a C const table. Run the
   registry first and it is stale against the very docs it contains —
   measured at rc346 by injecting 14 bytes into ``_tool_docs.py`` and
   watching ``srmech_tool_registry.c`` move 827380 -> 827394, exactly those
   bytes. No test that does not diff generator output can see it.

2. **Four generators wrote to STDOUT.** ``python3 c/tools/gen_tool_registry.py``
   with no redirect changed nothing at all, exited 0, and printed 800 KB of C
   to the terminal. Every one of them documented itself with a ``> file``
   redirect the caller had to remember.

3. **Line endings.** Generators emitted LF unconditionally; the working tree
   is mixed (measured rc346: ``_tool_docs.py``, ``srmech_responsion_registry.c``
   and ``srmech_class_registry.c`` CRLF, the other three LF, no
   ``.gitattributes``, ``core.autocrlf=true``). A wrong-convention write
   rewrites every line on disk while ``git diff`` stays clean, so a real
   one-line change hides inside a whole-file rewrite.

All three are now unreachable from the caller. The order is DERIVED from
:mod:`codegen_manifest` rather than remembered; the runner owns every write,
so there is no stdout to misroute; and each file is written back in the
convention it already uses, so unchanged content moves zero bytes.

WHY NOT AN MTIME CHECK
======================
"Fail if ``_tool_docs.py`` is newer than the registry" is a trap. mtime is
not a dependency signal in a git checkout — clone, rebase and ``git checkout``
all set mtimes in arbitrary order, so such a guard false-fires constantly and
gets suppressed, and a suppressed guard is worse than none. The robust form
is CONTENT equality: recompute what each file would be and compare. That is
``--check``.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import os
import sys
import time
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import codegen_manifest as cm  # noqa: E402

#: Set while the runner drives a generator, so a generator's standalone
#: refusal guard knows it is being run as part of the full ordered pass.
#: Declared once in the manifest; re-exported here for readability.
RUNNING_ENV = cm.RUNNING_ENV


def _load(gen: cm.Generator):
    """Import a generator script as a module (never as a subprocess).

    Module import, not ``subprocess`` + shell redirect, is what removes trap
    2 structurally: the runner calls ``generate()`` and receives a string, so
    there is no stdout channel for the output to be lost down.
    """
    spec = importlib.util.spec_from_file_location(
        f"_regen_{gen.name}", gen.script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {gen.script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render_one(gen: cm.Generator, accept_seed_drift: bool = False) -> str:
    """Render a single generator's full output text, in THIS process."""
    mod = _load(gen)
    sink = io.StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        return cm.get_renderer(gen, mod)(accept_seed_drift=accept_seed_drift)


def render_all(accept_seed_drift: bool = False) -> "Dict[str, str]":
    """Render every generator against the CURRENT on-disk tree, in one
    process. Used by ``--check``, which writes nothing.

    Sharing a process is faithful HERE precisely because nothing is written:
    every generator reads the same on-disk state a fresh interpreter would
    read, so the verdict is identical and ~6x cheaper. It is NOT faithful
    once writes are involved — see :func:`regen_sequential`.
    """
    return {gen.name: render_one(gen, accept_seed_drift)
            for gen in cm.resolve_order()}


def regen_sequential(accept_seed_drift: bool = False
                     ) -> "Tuple[Dict[str, str], Dict[str, bool]]":
    """Regenerate every file in derived order, ONE SUBPROCESS PER GENERATOR.

    The subprocess boundary is load-bearing and was found by demonstration,
    not by design. The first version of this runner rendered all six in one
    process, and it silently reproduced the exact defect it exists to
    prevent: ``srmech.amsc.tool_schema`` merges ``TOOL_DOCS`` into every
    ``ToolEntry`` at IMPORT time, so writing ``_tool_docs.py`` part-way
    through a run does not reach a module already imported. ``gen_tool_docs``
    wrote correct new docs, and ``gen_tool_registry`` — running microseconds
    later in the same interpreter — still rendered from the pre-write schema
    and emitted a table 20 bytes stale. In-process ordering is not ordering;
    it just looks like it.

    A fresh interpreter per generator is the only version of "runs after"
    that survives an arbitrary future generator's import-time caching, which
    is the property this manifest promises. The parent still owns every
    write, so traps 2 and 3 stay absorbed in exactly one place.
    """
    order = cm.resolve_order()
    texts: Dict[str, str] = {}
    changed: Dict[str, bool] = {}
    for gen in order:
        texts[gen.name] = _render_in_subprocess(gen, accept_seed_drift)
        changed[gen.name] = cm.write_preserving_eol(
            gen.output_path, texts[gen.name])
    return texts, changed


def _render_in_subprocess(gen: cm.Generator, accept_seed_drift: bool) -> str:
    """Render ``gen`` in a FRESH interpreter and return its output text."""
    import subprocess

    argv = [sys.executable, str(Path(__file__).resolve()),
            "--render-one", gen.name]
    if accept_seed_drift:
        argv.append("--accept-seed-drift")
    env = dict(os.environ, **{RUNNING_ENV: "1"})
    proc = subprocess.run(argv, capture_output=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(
            f"{gen.name} failed (exit {proc.returncode}):\n"
            + proc.stderr.decode("utf-8", "replace").strip())
    return proc.stdout.decode("utf-8")


# ── commands ──────────────────────────────────────────────────────────


def cmd_list() -> int:
    order = cm.resolve_order()
    print("DERIVED run order (from codegen_manifest declarations):\n")
    for i, gen in enumerate(order, 1):
        print(f"  {i}. {gen.name}")
        print(f"       {gen.script}  ->  {gen.output}")
        print(f"       consumes: {', '.join(gen.consumes)}")
        print(f"       produces: {', '.join(gen.produces)}")
        if gen.note:
            print(f"       note: {gen.note}")
    print("\nEdges implied by those declarations (before -> after):")
    for a, b in sorted(set(cm.edges())):
        print(f"  {a} -> {b}")
    print("\nResource derivations (key is built FROM values):")
    for r, srcs in sorted(cm.DERIVES.items()):
        print(f"  {r} <- {', '.join(srcs)}")
    print("\nDeliberately EXCLUDED from the pass:")
    for script, reason in sorted(cm.EXCLUDED.items()):
        head = reason.split(".")[0]
        print(f"  {script}\n       {head}.")
    return 0


def cmd_check(accept_seed_drift: bool) -> int:
    """Content-equality: is every generated file what its generator would
    produce right now? Writes nothing. This is the CI half."""
    t0 = time.time()
    try:
        texts = render_all(accept_seed_drift=accept_seed_drift)
    except RuntimeError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    stale: List[str] = []
    for gen in cm.resolve_order():
        want = cm.normalise(texts[gen.name])
        if not gen.output_path.exists():
            stale.append(f"{gen.output} (MISSING)")
            continue
        have = cm.normalise(gen.output_path.read_text(encoding="utf-8"))
        mark = "ok  " if want == have else "STALE"
        if want != have:
            stale.append(f"{gen.output} ({len(have)} on disk vs {len(want)} "
                         f"regenerated)")
        print(f"  {mark} {gen.output}")
    dt = time.time() - t0
    if stale:
        print(f"\n{len(stale)} generated file(s) are STALE:", file=sys.stderr)
        for s in stale:
            print(f"  {s}", file=sys.stderr)
        print("\nRegenerate with:  python3 tools/regen_all.py",
              file=sys.stderr)
        return 1
    print(f"\nall {len(texts)} generated files are up to date ({dt:.1f}s)")
    return 0


def cmd_regen(accept_seed_drift: bool, verify: bool) -> int:
    """Regenerate everything in derived order, then PROVE idempotence."""
    order = cm.resolve_order()
    print("regen-all — derived order: "
          + " -> ".join(g.name for g in order) + "\n")
    t0 = time.time()

    try:
        first, changed = regen_sequential(accept_seed_drift=accept_seed_drift)
    except RuntimeError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    for gen in order:
        flag = "WROTE" if changed[gen.name] else "same "
        print(f"  {flag} {gen.output}")

    if not verify:
        print("\n(idempotence verification skipped: --no-verify)")
        return 0

    # ── the built-in idempotence proof ────────────────────────────────
    # Regenerate a SECOND time from the tree the first pass produced and
    # require byte-identical output. A generator whose result depends on
    # the previous state of its own output file — or on any sibling's —
    # fails here rather than in whatever consumes it three rcs later.
    print("\nverifying idempotence (second pass)…")
    try:
        second, rewrote_map = regen_sequential(
            accept_seed_drift=accept_seed_drift)
    except RuntimeError as exc:
        print(f"SECOND PASS REFUSED: {exc}", file=sys.stderr)
        return 1

    drifted = [g.name for g in order
               if cm.normalise(first[g.name]) != cm.normalise(second[g.name])]
    if drifted:
        print(f"\nNOT IDEMPOTENT — {len(drifted)} generator(s) produced "
              f"different output on the second pass: {', '.join(drifted)}",
              file=sys.stderr)
        return 1

    rewrote = [n for n, moved in rewrote_map.items() if moved]
    if rewrote:
        print(f"\nNOT IDEMPOTENT — the second pass moved bytes for: "
              f"{', '.join(rewrote)}", file=sys.stderr)
        return 1

    dt = time.time() - t0
    n_moved = sum(1 for v in changed.values() if v)
    print(f"  idempotent: all {len(order)} outputs byte-identical across "
          f"two passes")
    print(f"\nregen-all OK — {n_moved} file(s) changed, {dt:.1f}s")
    return 0


def cmd_only(name: str, accept_seed_drift: bool) -> int:
    """Run ONE generator. Reachable only behind --force-partial."""
    match = [g for g in cm.GENERATORS if g.name == name]
    if not match:
        print(f"unknown generator {name!r}; known: "
              f"{', '.join(g.name for g in cm.GENERATORS)}", file=sys.stderr)
        return 2
    gen = match[0]
    downstream = sorted({b for a, b in cm.edges() if a == gen.name})
    mod = _load(gen)
    sink = io.StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        text = cm.get_renderer(gen, mod)(accept_seed_drift=accept_seed_drift)
    moved = cm.write_preserving_eol(gen.output_path, text)
    print(f"{'WROTE' if moved else 'same '} {gen.output}")
    if downstream:
        print(f"\nWARNING: {gen.name} feeds {', '.join(downstream)}, which "
              f"were NOT regenerated.\nThe tree may now be internally stale. "
              f"Run: python3 tools/regen_all.py", file=sys.stderr)
    return 0


def main(argv: "Optional[List[str]]" = None) -> int:
    ap = argparse.ArgumentParser(
        prog="regen_all.py",
        description="Regenerate every generated file in dependency order.")
    ap.add_argument("--check", action="store_true",
                    help="content-equality only; write nothing; exit 1 if "
                         "any generated file is stale (the CI half)")
    ap.add_argument("--list", action="store_true",
                    help="print the derived order and the declared graph")
    ap.add_argument("--only", metavar="NAME",
                    help="run a single generator — REFUSED unless "
                         "--force-partial is also given")
    ap.add_argument("--force-partial", action="store_true",
                    help="acknowledge that --only can leave the tree stale")
    ap.add_argument("--accept-seed-drift", action="store_true",
                    help="pass through to gen_tool_docs: allow a stale "
                         "auto-seed field to be replaced")
    ap.add_argument("--no-verify", action="store_true",
                    help="skip the built-in idempotence second pass")
    ap.add_argument("--render-one", metavar="NAME",
                    help=argparse.SUPPRESS)  # internal: subprocess child
    args = ap.parse_args(argv)

    os.environ[RUNNING_ENV] = "1"

    if args.render_one:
        # Internal child mode: render exactly one generator in this fresh
        # interpreter and hand the bytes back to the parent, which owns the
        # write. Not a user-facing way to run one generator — that is
        # --only, and it refuses without --force-partial.
        match = [g for g in cm.GENERATORS if g.name == args.render_one]
        if not match:
            print(f"unknown generator {args.render_one!r}", file=sys.stderr)
            return 2
        text = render_one(match[0], accept_seed_drift=args.accept_seed_drift)
        # BYTES, not text: a text-mode write would apply the platform's
        # newline translation on the way out and the parent would receive
        # CRLF it never rendered — trap 3 reintroduced through the back
        # door, on Windows only, invisibly.
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.flush()
        return 0

    if args.list:
        return cmd_list()
    if args.check:
        return cmd_check(args.accept_seed_drift)
    if args.only:
        # Requirement 3: the default path is the correct one. Running a
        # single generator is exactly how rc345 shipped a stale carrier
        # table, so it is not reachable by accident.
        if not args.force_partial:
            downstream = sorted({b for a, b in cm.edges() if a == args.only})
            print(
                f"REFUSING to run {args.only!r} alone.\n\n"
                f"Generated files in this tree feed each other; running one "
                f"generator leaves the rest stale against it, which is how "
                f"rc345 shipped a carrier registry that had gone stale "
                f"against a tool-list it never re-read.\n"
                + (f"\n{args.only} feeds: {', '.join(downstream)}\n"
                   if downstream else "")
                + f"\nRun the full ordered pass:   python3 tools/regen_all.py"
                  f"\nOr, if you really mean it:   python3 tools/regen_all.py "
                  f"--only {args.only} --force-partial\n",
                file=sys.stderr)
            return 2
        return cmd_only(args.only, args.accept_seed_drift)
    return cmd_regen(args.accept_seed_drift, verify=not args.no_verify)


if __name__ == "__main__":
    raise SystemExit(main())
