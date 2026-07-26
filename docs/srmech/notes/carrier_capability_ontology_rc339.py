#!/usr/bin/env python3
"""rc339 (`#967` / `#965`) — the generating code for srmech's CARRIER CAPABILITY
ontology: the three ceilings ADDRESS / COMPOSE / TURN, measured rather than
asserted.

Why this file exists
--------------------
``srmech.introspect.describe()`` reports what this build can DO. Every number it
publishes about the carriers is derived here, so the published ontology is a
measurement with committed generating code
(``[[feedback_computational_provenance_discipline]]``) rather than a claim.

Before rc339 ``describe()["limits"]`` carried ``cd_max_dim`` = 256 and
``cd_dense_max_dim`` = 64 and nothing else. **Both are ADDRESSING ceilings.** A
caller — or an LLM driving the MCP surface, which is an explicit design goal —
could read 256 and try to TURN there, where non-commuting turn composition has
been dead since dim 8. Reporting only the permissive ceiling implies a
capability that does not exist.

The three capabilities
----------------------
ADDRESS
    Content-key a slot / carry an index lane. The Cayley--Dickson basis product
    is a SIGNED PERMUTATION whose destination index is exactly ``i XOR j``::

        e_i . e_j = +/- e_(i XOR j)

    Measured exact with zero failures at every rung through dim 64 (0 / 4096
    pairs at 64). No algebraic obstruction is known above it; the shipped
    ceiling ``CD_MAX_DIM`` = 256 is a tooling/verification bound, and
    ``CD_DENSE_MAX_DIM`` = 64 bounds only the dense ``dim x dim`` native path
    (past it the exact-rational oracle answers -- correct, slower).

COMPOSE
    Multiply without zero divisors (a normed composition algebra). Hurwitz
    (1898): 1, 2, 4, 8 and nothing else. Past dim 8 the sedenions carry zero
    divisors, so ``x . y == 0`` with ``x != 0`` and ``y != 0``.

TURN
    Compose two turns into one -- i.e. left multiplication is a representation::

        L_x o L_y == L_(x . y)     for all z:  x . (y . z) == (x . y) . z

    This is exactly associativity read as a statement about turns. NON-COMMUTING
    turn composition survives through dim 4 (H). At dim 8 (O) it dies.

The precise statement about what dies at O
------------------------------------------
"Turns stop at H" is the imprecise version already in circulation and it should
NOT be propagated. What is measured is stronger and more specific:

* At Q8 the turn-composing pairs are a STRICT SUPERSET of the commuting pairs --
  40 commute, 64 compose, so 24 NON-COMMUTING pairs still compose.
* At the octonion rung the turn-composing set and the commuting set are THE SAME
  SET -- 88 == 88, and BOTH set differences are empty. Not merely equal counts:
  equal as sets. The same identity holds at dim 16 and dim 32.

So turns DEGRADE TO ABELIAN-ONLY at O. The only surviving turn compositions are
the commuting ones. What dies at the octonion rung is specifically NON-COMMUTING
TURN COMPOSITION.

Corroboration by a second route: the 22 surviving BASIS pairs at dim 8 are
exactly ``{anything paired with the identity} U {every element with itself}``
(power-associativity, which every Cayley--Dickson rung keeps), and
22 basis pairs x 4 sign combinations = 88 signed-loop pairs. Two independent
measurements, one number.

Run
---
    cd docs/srmech/python && PYTHONPATH=$PWD python3 \
        ../notes/carrier_capability_ontology_rc339.py \
        > ../notes/carrier_capability_ontology_rc339.ndjson

Exhaustive, no sampling. ~1--10 min depending on ``--max-cd-dim`` (the CD sweep
is ``O(dim^3)`` products of ``O(dim^2)`` each; dim 64 dominates).

Pure integer / exact-rational arithmetic throughout: no float, no numpy, and no
``abs()`` (sign is Class K, never an ALU absolute value --
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).
"""

from __future__ import annotations

import argparse
import json
import sys

from srmech.amsc.cascade.cayley_dickson import cd_basis, cd_mult
from srmech.amsc.octonion import oct_mult
from srmech.amsc.q8 import q8_mult


def klein4_mult(a: int, b: int) -> int:
    """V4 = (F2)^2 -- the reversible Klein-4 XOR bind (the genome's default
    ``element_type``). Abelian, associative, self-inverse."""
    return a ^ b


#: (element_type name, header code, product, order of the element set).
#: The order is the SIGNED discrete carrier: V4 has 4 elements, Q8 = {+/-1,
#: +/-i, +/-j, +/-k} has 8, the octonion loop {+/-e0 .. +/-e7} has 16.
RUNGS = (
    ("klein4", 0, klein4_mult, 4),
    ("q8", 1, q8_mult, 8),
    ("octonion", 2, oct_mult, 16),
)


def _emit(record: dict) -> None:
    """One NDJSON row per measurement (``[[feedback_ndjson_over_bloated_json]]``)."""
    sys.stdout.write(json.dumps(record, sort_keys=True) + "\n")


def measure_element_types() -> None:
    """The three genome ``ELEMENT_TYPE_*`` rungs as a CAPABILITY LADDER.

    Emits, per rung: commuting pairs, associating triples, turn-composing pairs,
    and the SET IDENTITY between the commuting and turn-composing sets (the
    load-bearing part -- matching counts would not be enough).
    """
    for name, code, mul, order in RUNGS:
        dom = range(order)
        commuting = {(a, b) for a in dom for b in dom if mul(a, b) == mul(b, a)}
        associating = sum(
            mul(mul(a, b), c) == mul(a, mul(b, c))
            for a in dom for b in dom for c in dom
        )
        turning = {
            (a, b) for a in dom for b in dom
            if all(mul(a, mul(b, z)) == mul(mul(a, b), z) for z in dom)
        }
        _emit({
            "measurement": "element_type_rung",
            "element_type": name,
            "code": code,
            "order": order,
            "commutes": [len(commuting), order * order],
            "associates": [associating, order ** 3],
            "turns_compose": [len(turning), order * order],
            # The set identity, not just the counts.
            "turn_set_equals_commute_set": turning == commuting,
            "commute_only": len(commuting - turning),
            "turn_only": len(turning - commuting),
        })


def _turn_composes(basis, i: int, j: int) -> bool:
    """Does the turn by ``e_i`` compose with the turn by ``e_j``?

    ``L_(e_i) o L_(e_j) == L_(e_i . e_j)`` tested on the whole basis.
    """
    left, right = basis[i], basis[j]
    product = cd_mult(left, right)
    return all(
        cd_mult(left, cd_mult(right, z)) == cd_mult(product, z) for z in basis
    )


def measure_cd_turn_capacity(max_dim: int) -> None:
    """The turn-capacity ladder over the Cayley--Dickson tower.

    For each rung: how many BASIS pairs have composing turns, how many commute,
    whether those two sets coincide, and the largest power-of-two sub-rung all
    of whose turns compose (the "how much real dimension fits in ONE coherent
    rotation" number -- it saturates at 4 and never grows again).
    """
    dim = 1
    while dim <= max_dim:
        basis = [cd_basis(dim, i) for i in range(dim)]
        turning = {(i, j) for i in range(dim) for j in range(dim)
                   if _turn_composes(basis, i, j)}
        commuting = {(i, j) for i in range(dim) for j in range(dim)
                     if cd_mult(basis[i], basis[j]) == cd_mult(basis[j], basis[i])}
        best, sub = 0, 1
        while sub <= dim:
            block = basis[:sub]
            if all(cd_mult(x, cd_mult(y, z)) == cd_mult(cd_mult(x, y), z)
                   for x in block for y in block for z in block):
                best = sub
            sub *= 2
        # The dim-8 characterisation: identity-paired OR self-paired.
        power_assoc = {(i, j) for (i, j) in turning if i == 0 or j == 0 or i == j}
        _emit({
            "measurement": "cd_turn_capacity",
            "dim": dim,
            "turns_compose": [len(turning), dim * dim],
            "commutes": [len(commuting), dim * dim],
            "turn_set_equals_commute_set": turning == commuting,
            "largest_sub_rung_whose_turns_compose": best,
            "survivors_are_identity_or_self_paired": turning == power_assoc,
        })
        dim *= 2


def measure_addressing(max_dim: int) -> None:
    """The ADDRESS lane: is ``e_i . e_j`` a single signed basis element whose
    index is exactly ``i XOR j``? Exhaustive over all ``dim^2`` pairs."""
    dim = 2
    while dim <= max_dim:
        basis = [cd_basis(dim, i) for i in range(dim)]
        failures = 0
        for i in range(dim):
            for j in range(dim):
                product = cd_mult(basis[i], basis[j])
                occupied = [k for k, v in enumerate(product) if v != 0]
                if len(occupied) != 1 or occupied[0] != (i ^ j):
                    failures += 1
        _emit({
            "measurement": "xor_index_lane",
            "dim": dim,
            "failures": failures,
            "pairs": dim * dim,
            "exact": failures == 0,
        })
        dim *= 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-cd-dim", type=int, default=32,
                        help="highest Cayley-Dickson rung for the turn sweep "
                             "(O(dim^5) overall; 32 is ~1 min, 64 is ~1 h)")
    parser.add_argument("--max-address-dim", type=int, default=64,
                        help="highest rung for the XOR-index-lane sweep")
    args = parser.parse_args()

    measure_element_types()
    measure_cd_turn_capacity(args.max_cd_dim)
    measure_addressing(args.max_address_dim)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
