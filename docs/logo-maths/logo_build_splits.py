"""Build SplitObject₁ and the coincidence stream for fiber matrices.

Given a corpus of parsed programs, emit the (command, rule) and
(rule, geom-dim-bucket) coincidence streams that feed
`build_fiber_matrix`. Kept separate from the HDC primitives so the
counting logic is testable without numpy heavyweight.

Coincidence semantics
---------------------
For F₁ we count, per rule r, which commands c appear *inside* the
static subtree of that rule:

    coincidence(c, r) += 1  for every occurrence of c under a node
                            that fires r

Concretely, walking the AST in preorder: every time we enter a node
whose `rule_name` is r, we add 1 for every command-atom token found
while walking its subtree. This captures "FORWARD participates in
MOTION_NUM", "REPEAT participates in REPEAT_NUM_BLOCK", and so on, at
*the static structural level* — execution counts are irrelevant here.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable, List, Tuple

from logo_ast import (
    Program, Block, Stmt, MotionStmt, PenStmt, RepeatStmt, IfStmt,
    ToStmt, CallStmt, MakeStmt, VarRef, walk, ALL_RULES,
)
from logo_hdc.quantum_atoms import COMMAND_QUANTUM


ALL_COMMANDS: List[str] = list(COMMAND_QUANTUM.keys())


def _cmd_tokens(node) -> List[str]:
    """Return command names (Part-A atoms) that appear under `node`."""
    out: List[str] = []
    for n in walk(node):
        if isinstance(n, MotionStmt):
            out.append(n.cmd)
        elif isinstance(n, PenStmt):
            out.append(n.cmd)
        elif isinstance(n, RepeatStmt):
            out.append("REPEAT")
        elif isinstance(n, IfStmt):
            out.append("IF")
        elif isinstance(n, ToStmt):
            out.append("TO")
            out.append("END")
        elif isinstance(n, MakeStmt):
            out.append("MAKE")
        elif isinstance(n, VarRef):
            out.append("THING")
    return out


def f1_coincidences(prog: Program) -> Iterable[Tuple[str, str, float]]:
    """Yield (command, rule, weight) coincidences from a single program.

    For each AST node that fires a rule, we attribute 1.0 to every
    command-token that appears directly *inside its immediate body*
    (not the whole subtree — that would double-count enclosing rules).

    'Immediate body' = the node's own shape; e.g., MotionStmt
    immediate-body is just the command it holds; RepeatStmt's is
    {REPEAT} + body's own top-level commands.
    """
    for n in walk(prog):
        rn = getattr(n, "rule_name", None)
        if rn not in ALL_RULES:
            continue
        # Immediate tokens at this node
        toks: List[str] = []
        if isinstance(n, MotionStmt):
            toks.append(n.cmd)
        elif isinstance(n, PenStmt):
            toks.append(n.cmd)
        elif isinstance(n, RepeatStmt):
            toks.append("REPEAT")
        elif isinstance(n, IfStmt):
            toks.append("IF")
        elif isinstance(n, ToStmt):
            toks.extend(("TO", "END"))
        elif isinstance(n, MakeStmt):
            toks.append("MAKE")
        elif isinstance(n, CallStmt):
            pass  # no direct command token
        elif isinstance(n, VarRef):
            toks.append("THING")
        # Program / Block / NumLit / BinOp: no direct command token
        for t in toks:
            yield (t, rn, 1.0)


def f1_coincidences_corpus(programs: Iterable[Program]) -> List[Tuple[str, str, float]]:
    """Flatten (command, rule) coincidences across an entire corpus."""
    out: List[Tuple[str, str, float]] = []
    for p in programs:
        out.extend(f1_coincidences(p))
    return out
