"""LOGO tree-walk interpreter.

Two outputs per run:

1. **Trace**: list of turtle segments, each `(x0, y0, x1, y1, pen_down)`.
   Only `pen_down` segments draw lines; pen-up segments are still
   returned so geometry encoders can weight "time spent" vs "ink".

2. **Rule-firing log**: multiset of `rule_name → count`. This is what
   Part-B and fiber F₁ consume — it says which productions participated
   in producing this trace. Driven by the `rule_name` attribute on AST
   nodes + command-level firings emitted by the interpreter.

JPL-ish constraints: every loop has a bounded step budget (no infinite
recursion). All state lives on the Turtle and InterpContext.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from logo_ast import (
    Program, Block, Stmt, Expr,
    MotionStmt, PenStmt, RepeatStmt, IfStmt, ToStmt, CallStmt, MakeStmt,
    NumLit, VarRef, BinOp,
    walk,
)


# Execution budget to guarantee termination on any input.
MAX_STEPS = 200_000


# ─── Turtle ────────────────────────────────────────────────────────

@dataclass
class Turtle:
    x: float = 0.0
    y: float = 0.0
    heading_deg: float = 0.0      # 0 = +y (north). Right-turn positive.
    pen_down: bool = True

    def forward(self, d: float) -> Tuple[float, float, float, float]:
        rad = math.radians(self.heading_deg)
        nx = self.x + d * math.sin(rad)
        ny = self.y + d * math.cos(rad)
        seg = (self.x, self.y, nx, ny)
        self.x, self.y = nx, ny
        return seg

    def right(self, a: float) -> None:
        self.heading_deg = (self.heading_deg + a) % 360.0


@dataclass
class Segment:
    x0: float
    y0: float
    x1: float
    y1: float
    pen_down: bool


@dataclass
class Trace:
    segments: List[Segment] = field(default_factory=list)

    def add(self, seg: Tuple[float, float, float, float], pen_down: bool) -> None:
        self.segments.append(Segment(*seg, pen_down))

    def bbox(self) -> Tuple[float, float, float, float]:
        if not self.segments:
            return (0.0, 0.0, 0.0, 0.0)
        xs = [s.x0 for s in self.segments] + [s.x1 for s in self.segments]
        ys = [s.y0 for s in self.segments] + [s.y1 for s in self.segments]
        return (min(xs), min(ys), max(xs), max(ys))


# ─── Interpreter context ───────────────────────────────────────────

@dataclass
class InterpContext:
    turtle: Turtle = field(default_factory=Turtle)
    trace: Trace = field(default_factory=Trace)
    env: Dict[str, float] = field(default_factory=dict)
    procs: Dict[str, ToStmt] = field(default_factory=dict)
    rule_fires: Counter = field(default_factory=Counter)
    # Command-level firings — Part-A equivalent of rule_fires but for
    # vocabulary atoms (FORWARD, BACK, REPEAT, ...).
    cmd_fires: Counter = field(default_factory=Counter)
    steps: int = 0


def _fire_rule(ctx: InterpContext, name: str) -> None:
    ctx.rule_fires[name] += 1


def _fire_cmd(ctx: InterpContext, name: str) -> None:
    ctx.cmd_fires[name] += 1


def _tick(ctx: InterpContext) -> None:
    ctx.steps += 1
    if ctx.steps > MAX_STEPS:
        raise RuntimeError(f"MAX_STEPS {MAX_STEPS} exceeded — runaway program?")


# ─── Expression evaluator ──────────────────────────────────────────

def eval_expr(e: Expr, ctx: InterpContext) -> float:
    _tick(ctx)
    _fire_rule(ctx, e.rule_name)
    if isinstance(e, NumLit):
        return e.value
    if isinstance(e, VarRef):
        if e.name not in ctx.env:
            raise NameError(f"Unbound variable :{e.name}")
        return ctx.env[e.name]
    if isinstance(e, BinOp):
        a = eval_expr(e.left, ctx)
        b = eval_expr(e.right, ctx)
        if   e.op == "+": return a + b
        elif e.op == "-": return a - b
        elif e.op == "*": return a * b
        elif e.op == "/": return a / b if b != 0 else 0.0
        raise ValueError(f"Bad op {e.op}")
    raise TypeError(f"Unknown expr node {type(e).__name__}")


# ─── Statement executor ────────────────────────────────────────────

def exec_stmt(s: Stmt, ctx: InterpContext) -> None:
    _tick(ctx)
    _fire_rule(ctx, s.rule_name)

    if isinstance(s, MotionStmt):
        _fire_cmd(ctx, s.cmd)
        arg = eval_expr(s.arg, ctx)
        if s.cmd == "FORWARD":
            seg = ctx.turtle.forward(arg)
            ctx.trace.add(seg, ctx.turtle.pen_down)
        elif s.cmd == "BACK":
            seg = ctx.turtle.forward(-arg)
            ctx.trace.add(seg, ctx.turtle.pen_down)
        elif s.cmd == "LEFT":
            ctx.turtle.right(-arg)
        elif s.cmd == "RIGHT":
            ctx.turtle.right(arg)
        return

    if isinstance(s, PenStmt):
        _fire_cmd(ctx, s.cmd)
        ctx.turtle.pen_down = (s.cmd == "PENDOWN")
        return

    if isinstance(s, RepeatStmt):
        _fire_cmd(ctx, "REPEAT")
        n = int(eval_expr(s.count, ctx))
        if n < 0 or n > MAX_STEPS:
            raise ValueError(f"REPEAT count out of range: {n}")
        for _ in range(n):
            _tick(ctx)
            exec_block(s.body, ctx)
        return

    if isinstance(s, IfStmt):
        _fire_cmd(ctx, "IF")
        if eval_expr(s.cond, ctx) != 0.0:
            exec_block(s.body, ctx)
        return

    if isinstance(s, ToStmt):
        _fire_cmd(ctx, "TO")
        # TO + END both fire; END is implicit since it closes the body
        _fire_cmd(ctx, "END")
        ctx.procs[s.name] = s
        return

    if isinstance(s, CallStmt):
        proc = ctx.procs.get(s.name)
        if proc is None:
            raise NameError(f"Undefined procedure {s.name}")
        if len(s.args) != len(proc.params):
            raise ValueError(
                f"{s.name}: expected {len(proc.params)} args, got {len(s.args)}"
            )
        # Evaluate args in *caller* env, then push new env for callee.
        call_vals = [eval_expr(a, ctx) for a in s.args]
        saved = ctx.env
        ctx.env = dict(zip(proc.params, call_vals))
        try:
            exec_block(proc.body, ctx)
        finally:
            ctx.env = saved
        return

    if isinstance(s, MakeStmt):
        _fire_cmd(ctx, "MAKE")
        ctx.env[s.name] = eval_expr(s.value, ctx)
        return

    raise TypeError(f"Unknown stmt node {type(s).__name__}")


def exec_block(b: Block, ctx: InterpContext) -> None:
    _fire_rule(ctx, b.rule_name)
    for s in b.stmts:
        exec_stmt(s, ctx)


def run(prog: Program, ctx: Optional[InterpContext] = None) -> InterpContext:
    ctx = ctx if ctx is not None else InterpContext()
    _fire_rule(ctx, prog.rule_name)
    for s in prog.stmts:
        exec_stmt(s, ctx)
    return ctx


# ─── Static rule inventory ────────────────────────────────────────

def static_rule_counts(prog: Program) -> Counter:
    """Count rule occurrences by AST traversal (no execution).

    Distinct from `InterpContext.rule_fires`, which is execution-weighted
    (REPEAT n fires the body n times). `static_rule_counts` counts every
    node exactly once.
    """
    counts = Counter()
    for n in walk(prog):
        rn = getattr(n, "rule_name", None)
        if rn is not None:
            counts[rn] += 1
    return counts


def static_cmd_counts(prog: Program) -> Counter:
    """Count command occurrences by AST traversal (no execution)."""
    counts = Counter()
    for n in walk(prog):
        if isinstance(n, MotionStmt):
            counts[n.cmd] += 1
        elif isinstance(n, PenStmt):
            counts[n.cmd] += 1
        elif isinstance(n, RepeatStmt):
            counts["REPEAT"] += 1
        elif isinstance(n, IfStmt):
            counts["IF"] += 1
        elif isinstance(n, ToStmt):
            counts["TO"] += 1
            counts["END"] += 1
        elif isinstance(n, MakeStmt):
            counts["MAKE"] += 1
        elif isinstance(n, VarRef):
            counts["THING"] += 1
    return counts
