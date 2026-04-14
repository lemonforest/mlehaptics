"""Hand-curated LOGO program corpus for fiber-matrix construction.

The corpus is organized by shape family so F₂ has a real chance of
revealing symmetry structure:

    POLYGON family        — REPEAT n [FORWARD d RIGHT 360/n] variants
    SPIRAL family         — REPEAT with growing step
    FRACTAL family        — procedures that call themselves
    FREESTYLE family      — pen lifts, variable bindings, mixed motion
    DEGENERATE family     — edge cases: only pen toggles, only binding

We keep programs in the research subset the parser handles (no lists,
no infix op precedence) and stay well under the MAX_STEPS budget.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class CorpusEntry:
    name: str
    family: str
    source: str
    # Symmetry label for supervised evaluation (approximate — for
    # validation of F₂'s symmetry-recovery prediction).
    symmetry: str = "none"


CORPUS: List[CorpusEntry] = [
    # ── POLYGON family ──
    CorpusEntry("triangle", "polygon",
                "REPEAT 3 [FORWARD 80 RIGHT 120]", "D3"),
    CorpusEntry("square",   "polygon",
                "REPEAT 4 [FORWARD 60 RIGHT 90]",  "D4"),
    CorpusEntry("pentagon", "polygon",
                "REPEAT 5 [FORWARD 50 RIGHT 72]",  "D5"),
    CorpusEntry("hexagon",  "polygon",
                "REPEAT 6 [FORWARD 40 RIGHT 60]",  "D6"),
    CorpusEntry("octagon",  "polygon",
                "REPEAT 8 [FORWARD 30 RIGHT 45]",  "D8"),
    CorpusEntry("dodecagon","polygon",
                "REPEAT 12 [FORWARD 20 RIGHT 30]", "D12"),
    CorpusEntry("circle",   "polygon",
                "REPEAT 360 [FORWARD 1 RIGHT 1]",  "SO2"),

    # ── SPIRAL family ──
    CorpusEntry("spiral_lin", "spiral",
                """
                MAKE "d 1
                REPEAT 60 [
                  FORWARD :d
                  RIGHT 20
                  MAKE "d (:d + 1)
                ]
                """, "spiral"),
    CorpusEntry("spiral_square", "spiral",
                """
                MAKE "d 5
                REPEAT 40 [
                  FORWARD :d
                  RIGHT 90
                  MAKE "d (:d + 5)
                ]
                """, "spiral"),
    CorpusEntry("spiral_tight", "spiral",
                """
                MAKE "d 2
                REPEAT 80 [
                  FORWARD :d
                  RIGHT 10
                  MAKE "d (:d + 1)
                ]
                """, "spiral"),

    # ── FRACTAL family (bounded recursion via REPEAT, not self-call) ──
    # Nested REPEATs produce fractal-ish rosettes.
    CorpusEntry("rosette_6", "fractal",
                """
                REPEAT 6 [
                  REPEAT 4 [FORWARD 30 RIGHT 90]
                  RIGHT 60
                ]
                """, "D6"),
    CorpusEntry("rosette_8", "fractal",
                """
                REPEAT 8 [
                  REPEAT 3 [FORWARD 25 RIGHT 120]
                  RIGHT 45
                ]
                """, "D8"),
    CorpusEntry("star_5", "fractal",
                """
                REPEAT 5 [FORWARD 80 RIGHT 144]
                """, "D5"),
    CorpusEntry("nested_squares", "fractal",
                """
                REPEAT 6 [
                  REPEAT 4 [FORWARD 20 RIGHT 90]
                  PENUP FORWARD 10 PENDOWN
                ]
                """, "D4"),

    # ── PROCEDURES family (TO/END and recursion-via-REPEAT) ──
    CorpusEntry("proc_poly", "procedures",
                """
                TO poly :n :d
                  REPEAT :n [FORWARD :d RIGHT (360 / :n)]
                END
                poly(7 30)
                """, "D7"),
    CorpusEntry("proc_two_polys", "procedures",
                """
                TO poly :n :d
                  REPEAT :n [FORWARD :d RIGHT (360 / :n)]
                END
                poly(3 40)
                PENUP FORWARD 60 PENDOWN
                poly(6 20)
                """, "mixed"),

    # ── FREESTYLE family — mixed motion + pen-up jumps ──
    CorpusEntry("dashed_line", "freestyle",
                """
                REPEAT 10 [
                  PENDOWN FORWARD 10
                  PENUP   FORWARD 5
                ]
                """, "C1"),
    CorpusEntry("zigzag", "freestyle",
                """
                REPEAT 8 [
                  FORWARD 20 RIGHT 45
                  FORWARD 20 LEFT 45
                ]
                """, "translation"),
    CorpusEntry("cond_guard", "freestyle",
                """
                MAKE "n 5
                IF :n [
                  REPEAT 5 [FORWARD 20 RIGHT 72]
                ]
                """, "D5"),

    # ── DEGENERATE family — for null-space analysis ──
    CorpusEntry("only_pen", "degenerate",
                "PENUP PENDOWN PENUP PENDOWN", "none"),
    CorpusEntry("only_bind", "degenerate",
                """
                MAKE "x 5
                MAKE "y 10
                """, "none"),
]


def get(name: str) -> CorpusEntry:
    for e in CORPUS:
        if e.name == name:
            return e
    raise KeyError(name)


def by_family(family: str) -> List[CorpusEntry]:
    return [e for e in CORPUS if e.family == family]
