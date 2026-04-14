"""LOGO AST node definitions.

Kept intentionally small — the LOGO subset has ~20 productions and
we want every node type discoverable at a glance. Each node class
carries a `rule_name` that doubles as the Part-B rule key in the HDC
codebook (so `MotionStmt` → `r_STMT_is_MOTION_NUM`, etc.).

Design principle: AST nodes are dataclasses of *kids*. The rule_name
is a class attribute, not an instance field — it identifies the
production, not the node.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Union


# ─── Expressions (numeric) ─────────────────────────────────────────

class Expr:
    """Base class for numeric expressions (NUM non-terminal)."""
    rule_name: str = "r_NUM"


@dataclass
class NumLit(Expr):
    value: float
    rule_name: str = field(default="r_NUM_is_literal", init=False, repr=False)


@dataclass
class VarRef(Expr):
    """:foo — variable reference, same as THING "foo in classic LOGO."""
    name: str
    rule_name: str = field(default="r_NUM_is_VAR", init=False, repr=False)


@dataclass
class BinOp(Expr):
    op: str           # '+', '-', '*', '/'
    left: Expr
    right: Expr
    rule_name: str = field(default="r_NUM_is_BINOP_NUM_NUM", init=False, repr=False)


# ─── Statements ────────────────────────────────────────────────────

class Stmt:
    """Base class for statements (STMT non-terminal)."""
    rule_name: str = "r_STMT"


@dataclass
class MotionStmt(Stmt):
    """FORWARD / BACK / LEFT / RIGHT <num>."""
    cmd: str          # 'FORWARD', 'BACK', 'LEFT', 'RIGHT'
    arg: Expr
    rule_name: str = field(default="r_STMT_is_MOTION_NUM", init=False, repr=False)


@dataclass
class PenStmt(Stmt):
    """PENUP / PENDOWN (arity-0)."""
    cmd: str          # 'PENUP', 'PENDOWN'
    rule_name: str = field(default="r_STMT_is_PEN", init=False, repr=False)


@dataclass
class RepeatStmt(Stmt):
    count: Expr
    body: "Block"
    rule_name: str = field(default="r_STMT_is_REPEAT_NUM_BLOCK", init=False, repr=False)


@dataclass
class IfStmt(Stmt):
    cond: Expr
    body: "Block"
    rule_name: str = field(default="r_STMT_is_IF_COND_BLOCK", init=False, repr=False)


@dataclass
class ToStmt(Stmt):
    """TO <name> [:arg ...] <body> END — procedure definition."""
    name: str
    params: List[str]
    body: "Block"
    rule_name: str = field(default="r_STMT_is_TO_NAME_ARGS_BLOCK_END", init=False, repr=False)


@dataclass
class CallStmt(Stmt):
    """Invoke a user-defined procedure by name."""
    name: str
    args: List[Expr]
    rule_name: str = field(default="r_STMT_is_CALL_ARGS", init=False, repr=False)


@dataclass
class MakeStmt(Stmt):
    """MAKE "name <expr> — variable binding."""
    name: str
    value: Expr
    rule_name: str = field(default="r_STMT_is_MAKE_NAME_EXPR", init=False, repr=False)


@dataclass
class Block:
    """[ STMT* ] — a bracketed list of statements."""
    stmts: List[Stmt]
    rule_name: str = field(default="r_BLOCK_is_STMT_star", init=False, repr=False)


@dataclass
class Program:
    stmts: List[Stmt]
    rule_name: str = field(default="r_PROG_is_STMT_star", init=False, repr=False)


# ─── Rule enumeration ──────────────────────────────────────────────
# Canonical list of every production rule name. Used as the Part-B
# codebook index. Order matters (it's the row/column order in the
# fiber matrix).

ALL_RULES: list[str] = [
    # Program / block structure
    "r_PROG_is_STMT_star",
    "r_BLOCK_is_STMT_star",
    # Statement forms
    "r_STMT_is_MOTION_NUM",
    "r_STMT_is_PEN",
    "r_STMT_is_REPEAT_NUM_BLOCK",
    "r_STMT_is_IF_COND_BLOCK",
    "r_STMT_is_TO_NAME_ARGS_BLOCK_END",
    "r_STMT_is_CALL_ARGS",
    "r_STMT_is_MAKE_NAME_EXPR",
    # Numeric expressions
    "r_NUM_is_literal",
    "r_NUM_is_VAR",
    "r_NUM_is_BINOP_NUM_NUM",
]


def walk(node: Any):
    """Recursive AST traversal; yields every node including the root."""
    yield node
    if isinstance(node, (Program, Block)):
        for s in node.stmts:
            yield from walk(s)
    elif isinstance(node, MotionStmt):
        yield from walk(node.arg)
    elif isinstance(node, RepeatStmt):
        yield from walk(node.count)
        yield from walk(node.body)
    elif isinstance(node, IfStmt):
        yield from walk(node.cond)
        yield from walk(node.body)
    elif isinstance(node, ToStmt):
        yield from walk(node.body)
    elif isinstance(node, CallStmt):
        for a in node.args:
            yield from walk(a)
    elif isinstance(node, MakeStmt):
        yield from walk(node.value)
    elif isinstance(node, BinOp):
        yield from walk(node.left)
        yield from walk(node.right)
    # NumLit / VarRef / PenStmt: leaves
