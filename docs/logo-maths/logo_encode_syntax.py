"""Part-B encoder: program → two HVs characterizing its syntactic shape.

Mirrors `logo_encode_vocab` but over production rules:

    syn_lex  — sum of r_* rule HVs weighted by occurrence count.
    syn_ctx  — bundled (rule, position-in-preorder-walk) bindings.

Like Part A, these are independently inferable — sim(syn_lex, rule_HV)
tells you whether that rule appeared without touching anything else.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

import numpy as np

from logo_ast import Program, walk
from logo_encode_vocab import position_atom
from logo_hdc import HD, bind, bundle_sum, DEFAULT_DIM


def rule_sequence(prog: Program) -> List[str]:
    """Preorder list of rule_names encountered during AST walk."""
    from logo_ast import ALL_RULES
    allowed = set(ALL_RULES)
    out = []
    for node in walk(prog):
        rn = getattr(node, "rule_name", None)
        # Only concrete productions — base classes like r_NUM / r_STMT
        # carry the non-terminal name and aren't real rules.
        if rn and rn in allowed:
            out.append(rn)
    return out


def encode_syn_lex(prog: Program, rule_cb: Dict[str, HD]) -> HD:
    seq = rule_sequence(prog)
    counts = Counter(seq)
    if not counts:
        ref = next(iter(rule_cb.values()))
        return np.zeros_like(ref)
    parts = [count * rule_cb[r] for r, count in counts.items()
             if r in rule_cb]
    if not parts:
        ref = next(iter(rule_cb.values()))
        return np.zeros_like(ref)
    return bundle_sum(parts)


def encode_syn_ctx(
    prog: Program,
    rule_cb: Dict[str, HD],
    *,
    dim: int = DEFAULT_DIM,
    max_slots: int = 64,
) -> HD:
    seq = rule_sequence(prog)
    if not seq:
        ref = next(iter(rule_cb.values()))
        return np.zeros_like(ref)
    parts = []
    for i, rn in enumerate(seq):
        if rn not in rule_cb:
            continue
        s = min(i, max_slots - 1)
        parts.append(bind(rule_cb[rn], position_atom(s, dim=dim)))
    if not parts:
        ref = next(iter(rule_cb.values()))
        return np.zeros_like(ref)
    return bundle_sum(parts)


def encode_syntax_program(
    prog: Program,
    rule_cb: Dict[str, HD],
    *,
    dim: int = DEFAULT_DIM,
    max_slots: int = 64,
) -> Tuple[HD, HD]:
    lex = encode_syn_lex(prog, rule_cb)
    ctx = encode_syn_ctx(prog, rule_cb, dim=dim, max_slots=max_slots)
    return lex, ctx
