"""Part-A encoder: program → two HVs characterizing its vocabulary use.

Returned per program:

    lex_hv  — lexicon HV:  sum over used commands of (count * a_c)
              Probes: sim(lex_hv, a_FORWARD) > 0 iff FORWARD appeared.

    ctx_hv  — context HV:  sum over (command, order-slot) pairs of
              bind(a_c, pos_slot). Probes: unbind(ctx_hv, a_FORWARD)
              cleans to the position-HV of the slot(s) FORWARD
              occupied.

Both are *standalone inferable* — neither requires the fiber to decode.
That's the independent-inferability property the plan demands.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

import numpy as np

from logo_ast import (
    Program, Block, MotionStmt, PenStmt, RepeatStmt, IfStmt, ToStmt,
    CallStmt, MakeStmt, VarRef,
)
from logo_hdc import HD, atom, bind, bundle_sum, DEFAULT_DIM


# ─── Command-order extraction ─────────────────────────────────────

def command_sequence(prog: Program) -> List[str]:
    """Depth-first preorder list of command names encountered.

    Each command firing is one token. REPEAT / IF are counted *once*
    per lexical appearance (not per iteration) so the vocab HV is
    stable across runs with different REPEAT counts.
    """
    out: List[str] = []

    def visit(node):
        if isinstance(node, (Program, Block)):
            for s in node.stmts:
                visit(s)
            return
        if isinstance(node, MotionStmt):
            out.append(node.cmd)
            return
        if isinstance(node, PenStmt):
            out.append(node.cmd)
            return
        if isinstance(node, RepeatStmt):
            out.append("REPEAT")
            visit(node.body)
            return
        if isinstance(node, IfStmt):
            out.append("IF")
            visit(node.body)
            return
        if isinstance(node, ToStmt):
            out.append("TO")
            visit(node.body)
            out.append("END")
            return
        if isinstance(node, CallStmt):
            # User procs don't map to a vocab atom — skip.
            return
        if isinstance(node, MakeStmt):
            out.append("MAKE")
            return
        if isinstance(node, VarRef):
            out.append("THING")
            return

    visit(prog)
    return out


# ─── Encoders ─────────────────────────────────────────────────────

def encode_lex(prog: Program, vocab_cb: Dict[str, HD]) -> HD:
    """Lexicon HV: weighted sum of commands used.

    lex = Σ_c count(c) * a_c

    Probing: sim(lex, a_c) is monotone in count(c), zero-ish if c
    didn't appear.
    """
    seq = command_sequence(prog)
    counts = Counter(seq)
    if not counts:
        ref = next(iter(vocab_cb.values()))
        return np.zeros_like(ref)
    parts = [count * vocab_cb[cmd] for cmd, count in counts.items()]
    return bundle_sum(parts)


# Position atoms for context encoding. Cached so the same D gives
# stable slot HVs across programs.
_POS_CACHE: Dict[tuple[int, int], HD] = {}


def position_atom(slot: int, *, dim: int = DEFAULT_DIM) -> HD:
    key = (slot, dim)
    if key not in _POS_CACHE:
        _POS_CACHE[key] = atom(f"slot_{slot}", dim=dim)
    return _POS_CACHE[key]


def encode_ctx(
    prog: Program,
    vocab_cb: Dict[str, HD],
    *,
    dim: int = DEFAULT_DIM,
    max_slots: int = 64,
) -> HD:
    """Context HV: bundled (command, position) bindings.

    ctx = Σ_i bind(a_{cmd_i}, slot_i)

    where slot_i = position_atom(min(i, max_slots-1)). The last slot
    aliases for any command past `max_slots` — trace bounded.

    Probe: unbind(ctx, a_c) ≈ Σ over slots where c appears of slot_i.
    Cleanup against {slot_0, ..., slot_{max_slots-1}} returns those
    positions.
    """
    seq = command_sequence(prog)
    if not seq:
        ref = next(iter(vocab_cb.values()))
        return np.zeros_like(ref)
    parts = []
    for i, cmd in enumerate(seq):
        if cmd not in vocab_cb:
            continue
        s = min(i, max_slots - 1)
        parts.append(bind(vocab_cb[cmd], position_atom(s, dim=dim)))
    if not parts:
        ref = next(iter(vocab_cb.values()))
        return np.zeros_like(ref)
    return bundle_sum(parts)


def encode_vocab_program(
    prog: Program,
    vocab_cb: Dict[str, HD],
    *,
    dim: int = DEFAULT_DIM,
    max_slots: int = 64,
) -> Tuple[HD, HD]:
    """One-shot: returns (lex_hv, ctx_hv) for the program."""
    lex = encode_lex(prog, vocab_cb)
    ctx = encode_ctx(prog, vocab_cb, dim=dim, max_slots=max_slots)
    return lex, ctx
