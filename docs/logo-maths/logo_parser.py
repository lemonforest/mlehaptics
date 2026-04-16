"""LOGO tokenizer + recursive-descent parser for the research-spike subset.

Subset covered:
    FORWARD <num>   BACK <num>   LEFT <num>   RIGHT <num>
    PENUP           PENDOWN
    REPEAT <num> [ ... ]
    IF <num> [ ... ]
    TO <name> [:params...] <body> END
    MAKE "<name> <expr>
    :<var>          (variable reference inside expressions)
    <literal>       (float or int)
    ( <expr> <op> <expr> )   for '+', '-', '*', '/'
    <name>( <args> )         call user-defined procedure (simple form)

Intentionally *not* covered: lists beyond [..] blocks, strings, RUN,
IFELSE, OUTPUT, infix operator precedence, negative-number-as-unary.
The research-spike corpus stays within this subset.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from logo_ast import (
    Block, Program, MotionStmt, PenStmt, RepeatStmt, IfStmt, ToStmt,
    CallStmt, MakeStmt, NumLit, VarRef, BinOp, Expr, Stmt,
)

# ─── Tokenizer ─────────────────────────────────────────────────────

_MOTIONS = {"FORWARD", "FD", "BACK", "BK", "LEFT", "LT", "RIGHT", "RT"}
_PEN     = {"PENUP", "PU", "PENDOWN", "PD"}
_MOTION_CANON = {
    "FORWARD": "FORWARD", "FD": "FORWARD",
    "BACK":    "BACK",    "BK": "BACK",
    "LEFT":    "LEFT",    "LT": "LEFT",
    "RIGHT":   "RIGHT",   "RT": "RIGHT",
}
_PEN_CANON = {
    "PENUP":   "PENUP",   "PU": "PENUP",
    "PENDOWN": "PENDOWN", "PD": "PENDOWN",
}
_KEYWORDS = _MOTIONS | _PEN | {"REPEAT", "IF", "TO", "END", "MAKE"}

# Token = (kind, text); kinds: LBRACK RBRACK LPAREN RPAREN OP NUM
# NAME VAR QUOTED KW
_TOKEN_RE = re.compile(
    r"""
    \s+                                # whitespace (discarded)
    | ;[^\n]*                           # ; comment to EOL
    | (?P<LBRACK>\[)
    | (?P<RBRACK>\])
    | (?P<LPAREN>\()
    | (?P<RPAREN>\))
    | (?P<OP>[+\-*/])
    | (?P<NUM>-?\d+(?:\.\d+)?)
    | :(?P<VAR>[A-Za-z_][A-Za-z0-9_]*)
    | "(?P<QUOTED>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<NAME>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)


@dataclass
class Token:
    kind: str       # 'LBRACK','RBRACK','LPAREN','RPAREN','OP','NUM','VAR','QUOTED','KW','NAME'
    text: str


def tokenize(src: str) -> List[Token]:
    out: List[Token] = []
    i = 0
    while i < len(src):
        m = _TOKEN_RE.match(src, i)
        if not m:
            raise SyntaxError(f"Unexpected char {src[i]!r} at offset {i}")
        i = m.end()
        if m.lastgroup is None:
            continue
        kind = m.lastgroup
        text = m.group(kind)
        if kind == "NAME" and text.upper() in _KEYWORDS:
            out.append(Token("KW", text.upper()))
        elif kind == "NAME":
            out.append(Token("NAME", text))
        else:
            out.append(Token(kind, text))
    return out


# ─── Parser ────────────────────────────────────────────────────────

class Parser:
    def __init__(self, toks: List[Token]):
        self.toks = toks
        self.p = 0

    def _peek(self, offset: int = 0) -> Optional[Token]:
        i = self.p + offset
        return self.toks[i] if i < len(self.toks) else None

    def _eat(self, kind: str, text: Optional[str] = None) -> Token:
        t = self._peek()
        if t is None or t.kind != kind or (text is not None and t.text != text):
            want = f"{kind}{'/' + text if text else ''}"
            got = f"{t.kind}/{t.text}" if t else "EOF"
            raise SyntaxError(f"Expected {want}, got {got}")
        self.p += 1
        return t

    def parse_program(self) -> Program:
        stmts = self._parse_stmts_until(None)
        return Program(stmts)

    def _parse_stmts_until(self, terminator: Optional[str]) -> List[Stmt]:
        """Parse statements until we hit the specified token kind, or EOF."""
        stmts: List[Stmt] = []
        # safety bound: grammar is bounded by token count
        max_iters = len(self.toks) + 1
        for _ in range(max_iters):
            t = self._peek()
            if t is None:
                if terminator is not None:
                    raise SyntaxError(f"Expected {terminator}, got EOF")
                break
            if terminator == "RBRACK" and t.kind == "RBRACK":
                break
            if terminator == "END" and t.kind == "KW" and t.text == "END":
                break
            stmts.append(self._parse_stmt())
        return stmts

    def _parse_stmt(self) -> Stmt:
        t = self._peek()
        assert t is not None
        if t.kind == "KW":
            k = t.text
            if k in _MOTION_CANON:
                self._eat("KW")
                arg = self._parse_expr()
                return MotionStmt(_MOTION_CANON[k], arg)
            if k in _PEN_CANON:
                self._eat("KW")
                return PenStmt(_PEN_CANON[k])
            if k == "REPEAT":
                self._eat("KW")
                count = self._parse_expr()
                body = self._parse_block()
                return RepeatStmt(count, body)
            if k == "IF":
                self._eat("KW")
                cond = self._parse_expr()
                body = self._parse_block()
                return IfStmt(cond, body)
            if k == "TO":
                self._eat("KW")
                name_tok = self._eat("NAME")
                # Parameter list of :foo tokens.
                params: List[str] = []
                while self._peek() is not None and self._peek().kind == "VAR":
                    params.append(self._eat("VAR").text)
                body_stmts = self._parse_stmts_until("END")
                self._eat("KW", "END")
                return ToStmt(name_tok.text, params, Block(body_stmts))
            if k == "MAKE":
                self._eat("KW")
                name_tok = self._eat("QUOTED")
                value = self._parse_expr()
                return MakeStmt(name_tok.text, value)
            raise SyntaxError(f"Unexpected keyword {k}")
        if t.kind == "NAME":
            # Call: NAME ( arg1 arg2 ... )  — or space-separated simple form
            name = self._eat("NAME").text
            args: List[Expr] = []
            if self._peek() is not None and self._peek().kind == "LPAREN":
                self._eat("LPAREN")
                while self._peek() is not None and self._peek().kind != "RPAREN":
                    args.append(self._parse_expr())
                self._eat("RPAREN")
            return CallStmt(name, args)
        raise SyntaxError(f"Unexpected token {t.kind}/{t.text} at stmt start")

    def _parse_block(self) -> Block:
        self._eat("LBRACK")
        stmts = self._parse_stmts_until("RBRACK")
        self._eat("RBRACK")
        return Block(stmts)

    def _parse_expr(self) -> Expr:
        t = self._peek()
        if t is None:
            raise SyntaxError("Expected expression, got EOF")
        if t.kind == "NUM":
            self._eat("NUM")
            return NumLit(float(t.text))
        if t.kind == "VAR":
            self._eat("VAR")
            return VarRef(t.text)
        if t.kind == "LPAREN":
            self._eat("LPAREN")
            left = self._parse_expr()
            op_tok = self._eat("OP")
            right = self._parse_expr()
            self._eat("RPAREN")
            return BinOp(op_tok.text, left, right)
        raise SyntaxError(f"Unexpected token {t.kind}/{t.text} in expression")


def parse(src: str) -> Program:
    toks = tokenize(src)
    return Parser(toks).parse_program()
