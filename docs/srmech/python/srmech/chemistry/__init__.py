"""``srmech.chemistry`` — the CHEMISTRY domain: reaction networks as
exact-integer linear algebra.

A domain namespace named by its field (the ADR-0010 taxonomy: math / biology /
music / … → chemistry), landed fresh at v0.9.0rc379 (`#T1050`). It reads a
chemical reaction the way the rest of srmech reads everything — as exact
cyclic-group / spectral structure over ℚ, no float tolerance — and the three
math operators all COMPOSE the already-C-backed carrier surface (``QMat``
nullspace / rank, the graph Laplacian, and the rc378
``primitive_integer_vector`` keystone), so a balanced reaction, its conserved
moieties, and its Feinberg deficiency all fall out as INTEGERS with the same
provenance discipline as the primitives underneath.

WHAT IS HERE
============
``balance_reaction`` (Class L ∘ I/K/C)
    Signed balanced integer coefficients = the integer nullspace of the
    **element × species** matrix. ``["H2", "O2", "H2O"]`` → ``[2, 1, -2]`` (the
    sign carries direction; a negative coefficient is a product). Accepts
    formula strings, ``{element: count}`` dicts, or a raw element×species
    ``QMat``.

``conservation_laws`` (Class L ∘ I)
    The conserved moieties = an integer basis of the LEFT-nullspace of the
    **species × reaction** stoichiometric matrix ``N`` (each ``γ`` with
    ``γᵀN = 0``).

``deficiency`` (Class L ∘ J)
    The Feinberg deficiency ``δ = n − ℓ − s = rank(L_complex) − rank(N)`` — a
    non-negative integer fixed by network topology alone.

``parse_formula`` (Class F/G)
    The ergonomic input tokenizer: a formula string → an ``{element: count}``
    dict, with multi-letter symbols and nested parenthesised groups
    (``"Ca3(PO4)2"`` → ``{"Ca": 3, "P": 2, "O": 8}``). Dispatches to the C twin
    ``srmech_parse_formula``.

⚠️ TWO DIFFERENT MATRICES. ``balance_reaction`` builds **element × species**;
``conservation_laws`` / ``deficiency`` build **species × reaction**. They are
transposed in role — see :mod:`srmech.chemistry.reactions`.

The callables live in the submodules :mod:`srmech.chemistry.reactions` and
:mod:`srmech.chemistry.formula`, and are re-exported here for ergonomic access
(``srmech.chemistry.balance_reaction``), mirroring ``srmech.music``.
"""
from __future__ import annotations

from .formula import parse_formula
from .reactions import balance_reaction, conservation_laws, deficiency

__all__ = [
    "balance_reaction",
    "conservation_laws",
    "deficiency",
    "parse_formula",
]
