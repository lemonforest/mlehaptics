"""rc434 (`#T1130`) — the DECLARED-vs-ENFORCED execution corpus, and a floor under it.

WHY THIS IS AN EXECUTION GATE AND NOT A STATIC ONE
==================================================
A static prototype for this defect class was built, measured and REJECTED. It
is recorded here because the negative result is the reason this file has the
shape it does, and a later reader who "simplifies" it back to a name-comparison
will be rebuilding a thing that was measured not to work.

    static prototype, measured on the rc432 tree:
        precision  0 / 7   every flag was a false positive, cleared by execution
        recall     0 / 1   it MISSED the one real defect entirely

It missed the real defect for a structural reason, not a tuning one. The
falsehood lived at **clause** level::

    ValueError: ... for negative inputs OR inputs exceeding the uint64
                parity surface.

Both clauses name the SAME exception, and the first clause is true. Any
instrument that compares the SET OF NAMES a docstring declares against the SET
OF NAMES a body raises sees ``{ValueError}`` on both sides and reports CLEAN.
Name-level comparison is *structurally blind* to a false clause. Only firing
the input class the clause names can tell you.

So this file ships the measurement instead of the predicate: a corpus of probes
that each fire one declared trigger against the real shipped op.

WHAT RATCHETS, AND IN WHICH DIRECTION
=====================================
A **coverage FLOOR that rises**, not a defect CEIL.

The defect cannot be detected statically, but the *measurement* can always be
extended — so the honest ratchet is "the set of clauses under execution may
only grow". A CEIL would be the wrong instrument twice over: it would imply the
population of defects is knowable (it is not, that is the whole finding), and
it would go green by DELETING probes.

Following ``test_invocable_returned_floor_rc431.py``: the floor is a SORTED SET
of clause keys in ``declared_raises_covered_rc434.txt``, not a cardinal.
*Counts are not sets.* A cardinal cannot say WHICH clause lost coverage, and it
cannot see a swap that leaves the total unchanged. Direction: a clause leaving
the set FAILS; a clause newly covered is REPORTED and passes, because a gate
that punishes improvement gets improvements reverted.

Refresh the file deliberately, in the commit that earns the new members::

    python -m tests.test_declared_raises_execution_rc434    # rewrites the floor

THE THREE BINS THE STATIC SCOPE PRODUCED, AND WHY ONLY ONE SHIPS
================================================================
==========  ===========================================  ==================
BIN-1       a declared name that is not a real           **strict zero**
            exception class anywhere the package
            can see (i.e. a typo)
BIN-2       declared, and no ``raise`` of that name is    not shipped: 0 today
            statically reachable                         and it is the bin the
                                                         prototype scored 0/7 on
BIN-3       declared name reachable only through a       not shipped: undecidable
            dynamic or cross-module call                 by construction
==========  ===========================================  ==================

BIN-1 ships because it is genuinely decidable. It needs ONE allowlist entry to
be strict-zero: ``TOMLDecodeError`` is a REAL third-party class (``tomllib`` /
``tomli``), not a typo — it is simply not importable from a name the AST walk
can resolve. Without the allowlist this bin would be permanently at 1 and would
therefore never fail on a real typo. See ``_THIRD_PARTY_EXCEPTIONS``.

THIS IS AN srmech-LOCAL INVARIANT, NOT A POWER-OF-TEN RULE
==========================================================
Holzmann's Power of Ten has exactly ten rules and ``tests/test_jpl_audit.py``
iterates ``range(1, 11)``. Nothing here is an eleventh rule and it must not be
numbered as one.

NEGATIVE CONTROLS ARE MANDATORY HERE
====================================
The research round that produced this corpus retracted FOUR of its own
instruments. Two of the retractions are encoded as controls below, because both
failure modes are re-inventable in an afternoon:

  * a flat regex over a whole docstring, which reads a sentence describing the
    NAIVE ALTERNATIVE ("writing it yourself produces a ZeroDivisionError") as
    a contract of the op — see ``test_prose_mention_is_not_a_declared_clause``;
  * an instrument that cannot report otherwise — see
    ``test_coverage_is_zero_when_the_corpus_is_empty``.
"""

from __future__ import annotations

import ast
import builtins
import functools
import importlib
import inspect
import sys
from pathlib import Path

import pytest

import srmech

_HERE = Path(__file__).resolve().parent
#: Scan what is actually IMPORTED, never a path guessed from ``__file__`` --
#: "verify the artifact under test is the one you think". Under the CI's
#: ``pip install -e`` this is the source tree; under a wheel it is the wheel.
_SRC = Path(srmech.__file__).resolve().parent
_FLOOR_PATH = _HERE / "declared_raises_covered_rc434.txt"

#: A real third-party exception class that no AST walk over ``srmech/`` can
#: resolve, because the package never defines it and never imports it under a
#: bare name. It is NOT a typo, so BIN-1 cannot be strict-zero without it.
#: Add to this list only after confirming by IMPORT that the class exists.
_THIRD_PARTY_EXCEPTIONS = frozenset({"TOMLDecodeError"})

_NO_RAISE = "<no-raise>"


# ────────────────────────────────────────────────────────── docstring parsing


def _indent_of(line: str) -> int:
    n = 0
    for ch in line:
        if ch == " ":
            n += 1
        elif ch == "\t":
            n += 8
        else:
            break
    return n


_EXC_SUFFIXES = (
    "Error",
    "Exception",
    "Warning",
    "Exit",
    "Interrupt",
    "Iteration",
    "NotFound",
)
_EXC_EXACT = frozenset(
    {
        "StopIteration",
        "StopAsyncIteration",
        "KeyboardInterrupt",
        "SystemExit",
        "GeneratorExit",
    }
)


def _looks_like_exception(name: str) -> bool:
    tail = name.rsplit(".", 1)[-1]
    if tail in _EXC_EXACT:
        return True
    if not tail[:1].isupper():
        return False
    return any(tail.endswith(s) for s in _EXC_SUFFIXES)


def parse_raises_block(doc: str) -> list[str]:
    """Exception names from a Google- or numpydoc-style ``Raises`` SECTION.

    Indentation-aware ON PURPOSE. A flat regex over the whole docstring is the
    instrument that had to be retracted: it reads any capitalised ``*Error``
    token anywhere in the prose as a declaration, including one in a sentence
    about a DIFFERENT function. The block boundary is found by dedent, and only
    the first indent level inside the block yields names.
    """
    if not doc:
        return []
    lines = doc.splitlines()
    names: list[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        is_google = stripped == "Raises:"
        is_numpy = (
            stripped == "Raises"
            and i + 1 < len(lines)
            and lines[i + 1].strip() != ""
            and set(lines[i + 1].strip()) == {"-"}
        )
        if not (is_google or is_numpy):
            i += 1
            continue
        header_indent = _indent_of(lines[i])
        j = i + 2 if is_numpy else i + 1
        body_indent = None
        while j < len(lines):
            line = lines[j]
            if line.strip() == "":
                j += 1
                continue
            ind = _indent_of(line)
            if is_numpy:
                if ind < header_indent:
                    break
                if (
                    j + 1 < len(lines)
                    and lines[j + 1].strip() != ""
                    and set(lines[j + 1].strip()) == {"-"}
                ):
                    break
            elif ind <= header_indent:
                break
            if body_indent is None:
                body_indent = ind
            if ind == body_indent:
                label = line.strip().split(":", 1)[0].strip()
                cleaned = label.replace("|", " ").replace(",", " ").replace(" or ", " ")
                for tok in cleaned.split():
                    tok = tok.strip("`*'\"()[]")
                    if tok and _looks_like_exception(tok):
                        names.append(tok.rsplit(".", 1)[-1])
            j += 1
        i = j
    seen: list[str] = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return seen


# ──────────────────────────────────────────────────────────────── AST corpus


def _module_dotted(path: Path) -> str:
    rel = path.relative_to(_SRC.parent).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


@functools.lru_cache(maxsize=1)
def _scan_declared_clauses() -> dict[str, dict]:
    """``{"<module>.<qualname>::<Exc>": {...}}`` for every declared clause.

    Cached: the walk is pure over an immutable tree and several gates want it.
    """
    out: dict[str, dict] = {}
    for path in sorted(_SRC.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:  # pragma: no cover - reported, never silent
            pytest.fail(f"could not parse {path}")
        modname = _module_dotted(path)

        def walk(node, scope: tuple[str, ...]) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.ClassDef):
                    walk(child, scope + (child.name,))
                elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qual = ".".join(scope + (child.name,))
                    doc = ast.get_docstring(child) or ""
                    for exc in parse_raises_block(doc):
                        out[f"{modname}.{qual}::{exc}"] = {
                            "module": modname,
                            "qualname": qual,
                            "exception": exc,
                            "lineno": child.lineno,
                            "public": not any(
                                p.startswith("_") for p in scope + (child.name,)
                            ),
                        }
                    walk(child, scope + (child.name,))
                else:
                    walk(child, scope)

        walk(tree, ())
    return out


@functools.lru_cache(maxsize=1)
def _known_exception_names() -> frozenset[str]:
    names = {
        n
        for n in dir(builtins)
        if isinstance(getattr(builtins, n, None), type)
        and issubclass(getattr(builtins, n), BaseException)
    }
    for path in _SRC.rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and _looks_like_exception(node.name):
                names.add(node.name)
    return frozenset(names)


# ─────────────────────────────────────────────────────────────── the corpus
#
# (probe_id, dotted_path, expect, args, kwargs, what_it_fires)
#
# ``expect`` is an exception NAME, or ``_NO_RAISE`` for a probe that pins the
# ABSENCE of a raise. The absence pins matter as much as the presence ones:
# three of them are the rc167 no-upper-cap contract, which is exactly the thing
# four pieces of shipped prose contradicted.
#
# DELIBERATELY EXCLUDED: ``srmech.bus._client.connect`` (declares
# FileNotFoundError, measured ENFORCED on Linux). Its trigger is an absent unix
# socket under ``$HOME``; the CI matrix includes windows-latest, so the probe
# would be measuring the host, not the contract.

PROBES: list[tuple] = [
    # ---- biology.genome ---------------------------------------------------
    ("genome.discrete_writhe/self-meet", "srmech.biology.genome.discrete_writhe",
     "ValueError", ([(0, 0, 0), (1, 0, 0), (0, 0, 0), (1, 0, 0)],), {},
     "strand meets itself in 3D"),
    # `gains` MUST be a valid Q8 4-vector even though the clause under test is
    # the zero-cycle one. rc434 first wrote this probe with `gains=[0]`, which
    # PASSED on the pure path for the wrong reason -- the cycle check happens to
    # run before the gains are read -- and failed on every NATIVE cell, where
    # marshalling the gains first leaks `TypeError: 'int' object is not
    # iterable`. A probe that fires a DIFFERENT error than the clause it names
    # is not evidence about that clause, and here it made the corpus
    # projection-dependent. With a valid gain BOTH projections raise the
    # declared ValueError.
    ("genome.cwf_consistency_mod2/tree", "srmech.biology.genome.cwf_consistency_mod2",
     "ValueError", ([(0, 1)], [[1, 0, 0, 0]]), {"n": 2},
     "tree has zero fundamental cycles"),
    ("genome.genome_fiber_holonomy/no-leaf-dim",
     "srmech.biology.genome.genome_fiber_holonomy",
     "ValueError", (b"\x00\x01",), {}, "missing leaf_dim"),
    ("genome.genome_fiber_holonomy/bad-byte",
     "srmech.biology.genome.genome_fiber_holonomy",
     "ValueError", (b"\xff\xff",), {"leaf_dim": 2}, "non-Q8 byte"),
    ("genome.genome_octonion_holonomy/bad-byte",
     "srmech.biology.genome.genome_octonion_holonomy",
     "ValueError", (b"\xff\xff",), {"leaf_dim": 2}, "non-octonion byte"),
    ("genome.genome_octonion_associator/bad-byte",
     "srmech.biology.genome.genome_octonion_associator",
     "ValueError", (b"\xff\xff",), {"leaf_dim": 2}, "non-octonion byte"),
    # rc434 `#T1130`: registry named ValueError, docstring was silent
    ("genome.centromere/bad-sector", "srmech.biology.genome.centromere",
     "ValueError", (b"",), {}, "orientation is not a Klein-4 sector 0..3"),
    # ---- biology.q8 -------------------------------------------------------
    ("q8.q8_mult/bad", "srmech.biology.q8.q8_mult", "ValueError", (99, 0), {},
     "not a valid Q8 element"),
    ("q8.q8_conjugate/bad", "srmech.biology.q8.q8_conjugate", "ValueError", (99,), {},
     "not a valid Q8 element"),
    ("q8.q8_project_v4/bad", "srmech.biology.q8.q8_project_v4", "ValueError",
     (bytes([99]),), {}, "non-Q8 byte"),
    # ---- cascade.atoms ----------------------------------------------------
    ("atoms.pin_slot_at_zero/complex", "srmech.cascade.atoms.pin_slot_at_zero",
     "TypeError", (complex(1, 2),), {}, "complex operand"),
    ("atoms.magnitude/complex", "srmech.cascade.atoms.magnitude",
     "TypeError", (complex(1, 2),), {}, "complex operand"),
    # ---- cascade.cayley_dickson ------------------------------------------
    ("cd.table_product/empty-table", "srmech.cascade.cayley_dickson.table_product",
     "ValueError", ([], [1], [1]), {}, "empty table"),
    ("cd.table_product/float-const", "srmech.cascade.cayley_dickson.table_product",
     "TypeError", ([[[1.5]]], [1], [1]), {}, "non-int structure constant"),
    ("cd.defect_ladder/unequal", "srmech.cascade.cayley_dickson.defect_ladder",
     "ValueError", ([1, 0], [1, 0, 0], [1, 0]), {}, "operands of unequal length"),
    ("cd.defect_ladder/non-power-of-two", "srmech.cascade.cayley_dickson.defect_ladder",
     "ValueError", ([1, 0, 0], [1, 0, 0], [1, 0, 0]), {}, "dim is not a power of two"),
    ("cd.inertia_signature/empty", "srmech.cascade.cayley_dickson.inertia_signature",
     "ValueError", ([],), {}, "empty table"),
    ("cd.inertia_signature/ragged", "srmech.cascade.cayley_dickson.inertia_signature",
     "ValueError", ([[[1], [0]], [[0]]],), {}, "not dim x dim x dim"),
    ("cd.inertia_signature/float-const",
     "srmech.cascade.cayley_dickson.inertia_signature",
     "TypeError", ([[[1.5]]],), {}, "non-int structure constant"),
    # ---- cascade.composites ----------------------------------------------
    ("composites.cyclic_gcd/negative", "srmech.cascade.composites.cyclic_gcd",
     "ValueError", (-1, 5), {}, "negative input"),
    ("composites.cyclic_gcd/not-int", "srmech.cascade.composites.cyclic_gcd",
     "TypeError", ("x", 5), {}, "non-int operand"),
    # THE rc167 NO-UPPER-CAP CONTRACT. Four pieces of shipped prose claimed a
    # ValueError here through rc433. It does not happen at ANY magnitude, and
    # re-adding the cap would break the ~100-digit One-scale rationals.
    ("composites.cyclic_gcd/oversize-2**64", "srmech.cascade.composites.cyclic_gcd",
     _NO_RAISE, (2 ** 64, 5), {}, "uncapped: just past uint64"),
    ("composites.cyclic_gcd/oversize-2**64+7", "srmech.cascade.composites.cyclic_gcd",
     _NO_RAISE, (2 ** 64 + 7, 3), {}, "uncapped: past uint64, odd"),
    ("composites.cyclic_gcd/oversize-2**200", "srmech.cascade.composites.cyclic_gcd",
     _NO_RAISE, (2 ** 200, 2 ** 199), {}, "uncapped: 2**200"),
    ("cyclic.gcd/oversize-2**64", "srmech.math.cyclic.gcd",
     _NO_RAISE, (2 ** 64, 5), {}, "uncapped primitive: just past uint64"),
    ("cyclic.gcd/oversize-2**200", "srmech.math.cyclic.gcd",
     _NO_RAISE, (2 ** 200, 2 ** 199), {}, "uncapped primitive: 2**200"),
    ("cyclic.gcd/negative", "srmech.math.cyclic.gcd", "ValueError", (-1, 5), {},
     "negative operand -- the clause that IS true"),
    ("cyclic.gcd/not-int", "srmech.math.cyclic.gcd", "TypeError", ("x", 5), {},
     "non-int operand"),
    ("composites.cyclic_mod_mul/zero-mod", "srmech.cascade.cyclic_mod_mul",
     "ValueError", (1, 1, 0), {}, "modulus is 0"),
    ("composites.cyclic_mod_mul/not-int", "srmech.cascade.cyclic_mod_mul",
     "TypeError", ("x", 1, 5), {}, "non-int operand"),
    ("composites.cyclic_mod_mul_wide/zero-mod", "srmech.cascade.cyclic_mod_mul_wide",
     "ValueError", (1, 1, 0), {}, "modulus is 0"),
    ("composites.cyclic_mod_mul_wide/not-int", "srmech.cascade.cyclic_mod_mul_wide",
     "TypeError", ("x", 1, 5), {}, "non-int operand"),
    # ---- cascade.exact_dft ------------------------------------------------
    ("exact_dft.exact_idft/short", "srmech.cascade.exact_dft.exact_idft",
     "ValueError", ([],), {}, "N < 2"),
    # ---- cascade.hamming --------------------------------------------------
    ("hamming.hamming_syndrome/bad-length", "srmech.cascade.hamming_syndrome",
     "ValueError", ([1, 0, 1, 1],), {}, "length is not 2**n - 1"),
    # ---- cascade.frame_carrier -------------------------------------------
    ("frame_carrier/bad-func", "srmech.cascade.frame_carrier.frame_carrier",
     "ValueError", ("no_such_func", 1, 1, 3), {}, "bad func name"),
    ("frame_carrier/zero-den", "srmech.cascade.frame_carrier.frame_carrier",
     "ValueError", ("sin", 1, 0, 3), {}, "zero denominator (VALIDATE, not divide)"),
    ("frame_carrier/bad-sigma", "srmech.cascade.frame_carrier.frame_carrier",
     "ValueError", ("sin", 1, 2, 3), {"sigma": 7}, "sigma not in {+1,-1}"),
    # ---- cascade.compose (rc434 `#T1134`) ---------------------------------
    ("compose.parse_catalog_chains/not-a-mapping",
     "srmech.cascade.compose.parse_catalog_chains",
     "ChainSpecError", ("[[[ not toml",), {},
     "a str reaches a PUBLIC entry point -- was a bare AttributeError"),
    ("compose.parse_catalog_chains/catalog-not-a-table",
     "srmech.cascade.compose.parse_catalog_chains",
     "ChainSpecError", ({"catalog": "nope"},), {}, "[catalog] is not a table"),
    ("compose.parse_catalog_chains/missing-schema-version",
     "srmech.cascade.compose.parse_catalog_chains",
     "ChainSpecError", ({"catalog": {"operator_chain": [{"name": "x"}]}},), {},
     "chain present, chain_schema_version absent"),
    # ---- chemistry --------------------------------------------------------
    ("reactions.balance_reaction/bad-type",
     "srmech.chemistry.reactions.balance_reaction",
     "TypeError", ([1, 2],), {}, "unsupported species entry type"),
    ("reactions.balance_reaction/unbalanceable",
     "srmech.chemistry.reactions.balance_reaction",
     "ValueError", (["H2", "O2"],), {}, "UNBALANCEABLE (trivial kernel)"),
    # ---- dsl --------------------------------------------------------------
    ("dsl.build_chain_from_toml_str/malformed",
     "srmech.dsl._toml_chain.build_chain_from_toml_str",
     "TOMLDecodeError", ("[[[ not toml",), {}, "malformed TOML"),
    ("dsl.build_chain_from_toml_str/schema",
     "srmech.dsl._toml_chain.build_chain_from_toml_str",
     "ValueError", ('[chain]\nname="d"\n[[stage]]\nop="no_such_op_t1130"\n',), {},
     "schema mismatch / unknown op"),
    ("dsl.run_toml_chain/unknown-op", "srmech.dsl._tool_surface.run_toml_chain",
     "ValueError", ('[chain]\nname="d"\n[[stage]]\nop="no_such_op_t1130"\n', 1), {},
     "unknown cascade op"),
    ("dsl.run_toml_chain/malformed", "srmech.dsl._tool_surface.run_toml_chain",
     "ValueError", ("[[[ not toml", 1), {}, "malformed spec"),
    ("dsl.run_toml_chain/not-str", "srmech.dsl._tool_surface.run_toml_chain",
     "TypeError", (123, 1), {}, "spec is not a string"),
    # ---- math.covering ----------------------------------------------------
    ("covering.linking_number_cwf/zero-den",
     "srmech.math.covering.linking_number_cwf",
     "ValueError", ((1, 0), (1, 2)), {}, "denominator is 0 (VALIDATE precedent)"),
    ("covering.linking_number_cwf/not-ints",
     "srmech.math.covering.linking_number_cwf",
     "ValueError", ((1.5, 2), (1, 2)), {}, "pair is not two ints"),
    # ---- math.cyclic ------------------------------------------------------
    ("cyclic.lcm/overflow", "srmech.math.cyclic.lcm", "OverflowError",
     (2 ** 63, 2 ** 63 - 1), {}, "RESULT exceeds uint64 (both projections)"),
    ("cyclic.lcm/negative", "srmech.math.cyclic.lcm", "ValueError", (-1, 5), {},
     "negative operand"),
    ("cyclic.lcm/oversize-operand", "srmech.math.cyclic.lcm", "ValueError",
     (2 ** 65, 2), {}, "OPERAND past uint64 -- lcm DOES cap, unlike gcd"),
    ("cyclic.lcm/not-int", "srmech.math.cyclic.lcm", "TypeError", ("x", 5), {},
     "non-int operand"),
    ("cyclic.primitive_integer_vector/bad-shape",
     "srmech.math.cyclic.primitive_integer_vector",
     "TypeError", (object(),), {}, "unsupported input shape"),
    ("cyclic.primitive_integer_vector/zero-den",
     "srmech.math.cyclic.primitive_integer_vector",
     "ValueError", ([(1, 0), (2, 1)],), {}, "zero denominator (VALIDATE precedent)"),
    # ---- math.hdc ---------------------------------------------------------
    ("hdc.hamming/zero-len", "srmech.math.hdc.hamming", "ValueError", (b"", b""), {},
     "lengths are zero"),
    ("hdc.hamming/differ", "srmech.math.hdc.hamming", "ValueError",
     (b"\x00", b"\x00\x00"), {}, "lengths differ"),
    ("hdc.similarity/zero-len", "srmech.math.hdc.similarity", "ValueError",
     (b"", b""), {}, "lengths are zero"),
    ("hdc.similarity/differ", "srmech.math.hdc.similarity", "ValueError",
     (b"\x00", b"\x00\x00"), {}, "lengths differ"),
    # ---- math.laplacian ---------------------------------------------------
    ("laplacian.dense_solve/singular-exact", "srmech.math.laplacian.dense_solve",
     "ZeroDivisionError", ([[1, 1], [1, 1]], [[1], [1]]), {"exact": True},
     "singular A on the exact path (DIVIDE precedent)"),
    ("laplacian.dense_solve/nonsquare", "srmech.math.laplacian.dense_solve",
     "ValueError", ([[1, 1, 1], [1, 1, 1]], [[1], [1]]), {}, "non-square A"),
    ("laplacian.dense_solve/B-rowcount", "srmech.math.laplacian.dense_solve",
     "ValueError", ([[1, 0], [0, 1]], [[1], [1], [1]]), {}, "B row count mismatch"),
    ("laplacian.schur_complement/singular-interior",
     "srmech.math.laplacian.schur_complement",
     "ZeroDivisionError", ([[0, 0], [0, 0]], [0]), {"exact": True},
     "singular interior block (DIVIDE precedent)"),
    ("laplacian.schur_complement/nonsquare",
     "srmech.math.laplacian.schur_complement",
     "ValueError", ([[1, 1, 1], [1, 1, 1]], [0]), {}, "non-square L"),
    ("laplacian.schur_complement/empty-boundary",
     "srmech.math.laplacian.schur_complement",
     "ValueError", ([[1, 0], [0, 1]], []), {}, "empty boundary_idx"),
    ("laplacian.schur_complement/oob-boundary",
     "srmech.math.laplacian.schur_complement",
     "ValueError", ([[1, 0], [0, 1]], [99]), {}, "boundary index out of range"),
    ("laplacian.schur_complement/dup-boundary",
     "srmech.math.laplacian.schur_complement",
     "ValueError", ([[1, 0], [0, 1]], [0, 0]), {}, "duplicate boundary index"),
    ("laplacian.quaternion_laplacian/bad-n",
     "srmech.math.laplacian.quaternion_laplacian",
     "ValueError", (-1, []), {}, "bad n"),
    ("laplacian.quaternion_laplacian/bad-gain",
     "srmech.math.laplacian.quaternion_laplacian",
     "ValueError", (2, [(0, 1)]), {"gains": [[0, 0, 0]]}, "non-4-vector gain"),
    ("laplacian.octonion_laplacian/bad-n",
     "srmech.math.laplacian.octonion_laplacian",
     "ValueError", (-1, []), {}, "bad n"),
    ("laplacian.octonion_laplacian/bad-gain",
     "srmech.math.laplacian.octonion_laplacian",
     "ValueError", (2, [(0, 1)]), {"gains": [[0, 0, 0]]}, "non-8-vector gain"),
    ("laplacian.responsion/bad-kind", "srmech.math.laplacian.responsion",
     "ValueError", ([[1, 0], [0, 1]], [1, 0], 0), {"kind": "no_such_kind"},
     "unknown kind"),
    ("laplacian.responsion/resolvent-pole", "srmech.math.laplacian.responsion",
     "ZeroDivisionError", ([[1, 0], [0, 1]], [1, 0], 1), {"kind": "resolvent"},
     "z in the spectrum (DIVIDE precedent)"),
    # ---- math.octonion ----------------------------------------------------
    ("octonion.oct_mult/bad", "srmech.math.octonion.oct_mult", "ValueError",
     (999, 0), {}, "not a valid octonion element"),
    ("octonion.oct_conjugate/bad", "srmech.math.octonion.oct_conjugate", "ValueError",
     (999,), {}, "not a valid octonion element"),
    ("octonion.oct_torsor_act/bad", "srmech.math.octonion.oct_torsor_act", "ValueError",
     (999, 0), {}, "not a valid octonion element"),
    # ---- math.primes ------------------------------------------------------
    ("primes.factor/negative", "srmech.math.primes.factor", "ValueError", (-1,), {},
     "negative n"),
    ("primes.factor/not-int", "srmech.math.primes.factor", "TypeError", ("x",), {},
     "non-int n"),
    ("primes.factor/oversize", "srmech.math.primes.factor", "ValueError",
     (2 ** 64,), {}, "exceeds uint64 range -- factor DOES cap, unlike gcd"),
    # ---- math.qpoly / qbipoly --------------------------------------------
    ("qpoly.qpoly_from_coeffs/non-sequence", "srmech.math.qpoly.qpoly_from_coeffs",
     "TypeError", ("nope",), {}, "a str is a sequence, so refuse by TYPE"),
    ("qbipoly.qbipoly_from_coeffs/non-sequence",
     "srmech.math.qbipoly.qbipoly_from_coeffs",
     "TypeError", ("nope",), {}, "a str is a sequence, so refuse by TYPE"),
    # ---- math.rational ----------------------------------------------------
    ("rational.continued_fraction/zero-den", "srmech.math.rational.continued_fraction",
     "ValueError", (1, 0), {}, "denominator is 0"),
    ("rational.continued_fraction/oversize-num",
     "srmech.math.rational.continued_fraction",
     "ValueError", (2 ** 64 + 1, 7), {},
     "numerator past uint64 -- continued_fraction DOES cap"),
    # ---- music ------------------------------------------------------------
    ("spectra.spectrum_tier/empty", "srmech.music._spectra.spectrum_tier",
     "ValueError", ([],), {}, "empty spectrum"),
    ("spectra.spectrum_tier/float", "srmech.music._spectra.spectrum_tier",
     "TypeError", ([1.5, 2.0],), {}, "a float ratio"),
    ("spectra.spectrum_tier/bad-open", "srmech.music._spectra.spectrum_tier",
     "ValueError", ([(1, 1), (2, 1)],), {"open_partials": (99,)},
     "out-of-range open index"),
    ("spectra.commensurability_verdict/empty",
     "srmech.music._spectra.commensurability_verdict",
     "ValueError", ([],), {}, "empty spectrum"),
    ("spectra.commensurability_verdict/float",
     "srmech.music._spectra.commensurability_verdict",
     "TypeError", ([1.5, 2.0],), {}, "a float ratio"),
    ("spectra.common_period/open", "srmech.music._spectra.common_period",
     "ValueError", ([(1, 1), (2, 1)],), {"open_partials": (0,)},
     "spectrum is open"),
    ("spectra.common_period/float", "srmech.music._spectra.common_period",
     "TypeError", ([1.5, 2.0],), {}, "a float ratio"),
    # rc434 `#T1130`: ENFORCED-NOT-DECLARED. A HARMONIC spectrum whose reduced-
    # denominator lcm leaves the Class-I parity surface.
    ("spectra.common_period/overflow", "srmech.music._spectra.common_period",
     "OverflowError",
     ([(1, 1)] + [(1, p) for p in (
         2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
         67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
     )],), {}, "harmonic, but lcm of denominators overflows uint64"),
    ("music.normal_order/non-sequence", "srmech.music.normal_order",
     "TypeError", ("nope", "forte"), {}, "pcs is a str, not a sequence of ints"),
    ("music.normal_order/empty", "srmech.music.normal_order",
     "ValueError", ([], "forte"), {}, "pcs is empty"),
    ("music.normal_order/bad-convention", "srmech.music.normal_order",
     "ValueError", ([0, 4, 7], "straus"), {}, "convention is not forte/rahn"),
    # ---- physics.qm.octonion ---------------------------------------------
    ("qm.octonion_left_mult/short", "srmech.physics.qm.octonion.octonion_left_mult",
     "ValueError", ([1, 0, 0],), {}, "not an 8-vector"),
    ("qm.octonion_right_mult/short", "srmech.physics.qm.octonion.octonion_right_mult",
     "ValueError", ([1, 0, 0],), {}, "not an 8-vector"),
    ("qm.octonion_conjugate/short", "srmech.physics.qm.octonion.octonion_conjugate",
     "ValueError", ([1, 0, 0],), {}, "not an 8-vector"),
    ("qm.octonion_norm/short", "srmech.physics.qm.octonion.octonion_norm",
     "ValueError", ([1, 0, 0],), {}, "not an 8-vector"),
    # ---- physics.qm.quaternion -------------------------------------------
    ("qm.quaternion_left_mult/short",
     "srmech.physics.qm.quaternion.quaternion_left_mult",
     "ValueError", ([1, 0],), {}, "not a 4-vector"),
    ("qm.quaternion_right_mult/short",
     "srmech.physics.qm.quaternion.quaternion_right_mult",
     "ValueError", ([1, 0],), {}, "not a 4-vector"),
    ("qm.quaternion_conjugate/short",
     "srmech.physics.qm.quaternion.quaternion_conjugate",
     "ValueError", ([1, 0],), {}, "not a 4-vector"),
    ("qm.quaternion_norm/short", "srmech.physics.qm.quaternion.quaternion_norm",
     "ValueError", ([1, 0],), {}, "not a 4-vector"),
    ("qm.quaternion_log/short", "srmech.physics.qm.quaternion.quaternion_log",
     "ValueError", ([1, 0],), {}, "not a 4-vector"),
    ("qm.quaternion_slerp/short", "srmech.physics.qm.quaternion.quaternion_slerp",
     "ValueError", ([1, 0], [1, 0, 0, 0], 0.5), {}, "q0 not a 4-vector"),
    # ---- physics.qm.triality ---------------------------------------------
    ("qm.triality_cycle/unknown", "srmech.physics.qm.triality.triality_cycle",
     "ValueError", ("no_such_frame",), {}, "unknown frame string"),
    ("qm.triality_companions/short", "srmech.physics.qm.triality.triality_companions",
     "ValueError", ([[1, 0], [0, 1]],), {}, "not shape (8,8)"),
    ("qm.triality_relation_residual/short",
     "srmech.physics.qm.triality.triality_relation_residual",
     "ValueError", ([[1, 0], [0, 1]], [[1, 0], [0, 1]], [[1, 0], [0, 1]]), {},
     "not shape (8,8)"),
    # ---- signal_processing ------------------------------------------------
    ("dispatcher.dispatch/unknown-op",
     "srmech.signal_processing.cascade_dispatcher.dispatch",
     "UnknownOperationError", ("no_such_op_t1130",), {}, "op_name not registered"),
    ("ffr.verify_rotation_class_n_cycle_order/bad-D",
     "srmech.signal_processing.form_function_rotation."
     "verify_rotation_class_n_cycle_order",
     "ValueError", (1,), {"D": 7}, "D is invalid"),
    # ---- spectral ---------------------------------------------------------
    ("spectral.similarity/differ", "srmech.spectral.similarity", "ValueError",
     (b"\x00", b"\x00\x00"), {}, "different byte-lengths"),
    ("spectral.similarity/zero-len", "srmech.spectral.similarity", "ValueError",
     (b"", b""), {}, "zero-length inputs"),
]


def _resolve(dotted: str):
    parts = dotted.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        try:
            mod = importlib.import_module(".".join(parts[:cut]))
        except ImportError:
            continue
        obj = mod
        try:
            for attr in parts[cut:]:
                obj = getattr(obj, attr)
        except AttributeError:
            continue
        return obj
    raise ImportError(dotted)


def _clause_key_for(fn) -> str:
    target = inspect.unwrap(fn)
    return f"{target.__module__}.{target.__qualname__}"


def _run_probe(probe: tuple) -> dict:
    """Fire one probe. Returns a classification record; never raises."""
    probe_id, dotted, expect, args, kwargs, what = probe
    rec = {"probe_id": probe_id, "op": dotted, "expect": expect, "tests": what}
    try:
        fn = _resolve(dotted)
    except ImportError as exc:
        rec["outcome"] = "UNRESOLVED"
        rec["detail"] = str(exc)
        return rec
    rec["clause_owner"] = _clause_key_for(fn)
    try:
        value = fn(*args, **kwargs)
    except BaseException as exc:  # noqa: BLE001 - classifying, not handling
        got = type(exc).__name__
        rec["observed"] = got
        rec["message"] = str(exc)[:200]
        mro = [c.__name__ for c in type(exc).__mro__]
        rec["mro"] = mro[:6]
        if expect is _NO_RAISE:
            rec["outcome"] = "UNEXPECTED_RAISE"
        elif got == expect or expect in mro:
            rec["outcome"] = "ENFORCED"
        else:
            rec["outcome"] = "TYPE_MISMATCH"
        return rec
    rec["returned_type"] = type(value).__name__
    rec["returned_repr"] = repr(value)[:120]
    rec["outcome"] = "NO_RAISE_CONFIRMED" if expect is _NO_RAISE else "NOT_ENFORCED"
    return rec


def _covered_clause_keys(probes, declared: set[str] | None = None) -> set[str]:
    """Clause keys the corpus puts under EXECUTION, with the outcome to prove it.

    INTERSECTED with the declared population by construction. A probe may well
    fire an exception the docstring never promised -- that is a finding, but it
    is not COVERAGE of a clause, and letting it inflate the floor would make
    the floor grow by writing probes rather than by writing declarations.
    """
    if declared is None:
        declared = set(_scan_declared_clauses())
    covered: set[str] = set()
    for probe in probes:
        if probe[2] is _NO_RAISE:
            continue  # pins an absence; there is no clause to cover
        rec = _run_probe(probe)
        if rec["outcome"] != "ENFORCED":
            continue
        key = f"{rec['clause_owner']}::{probe[2]}"
        if key in declared:
            covered.add(key)
    return covered


# ───────────────────────────────────────────────────────────────── the gates


def test_every_probe_matches_its_declaration():
    """Fire every probe; each must produce exactly what the corpus expects."""
    bad = []
    for probe in PROBES:
        rec = _run_probe(probe)
        if rec["outcome"] not in ("ENFORCED", "NO_RAISE_CONFIRMED"):
            bad.append(rec)
    assert not bad, (
        f"{len(bad)} of {len(PROBES)} probes did not match their declaration.\n"
        + "\n".join(
            f"  {r['probe_id']}: expect={r['expect']} outcome={r['outcome']} "
            f"observed={r.get('observed', r.get('returned_type'))} "
            f"{r.get('message', r.get('returned_repr', ''))}"
            for r in bad
        )
    )


def test_declared_clause_coverage_floor_holds():
    """The covered-clause SET may grow. It may not shrink.

    A clause leaving this set means either the probe stopped firing it or the
    declaration was deleted. Both are things a human must look at, which is
    why the failure names the clause rather than a number.
    """
    assert _FLOOR_PATH.exists(), (
        f"{_FLOOR_PATH.name} is missing -- regenerate it with\n"
        f"    python -m tests.{Path(__file__).stem}"
    )
    floor = {
        line.strip()
        for line in _FLOOR_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    covered = _covered_clause_keys(PROBES)
    lost = sorted(floor - covered)
    assert not lost, (
        f"{len(lost)} clause(s) LEFT the execution floor -- coverage may only "
        f"rise:\n  " + "\n  ".join(lost)
    )
    gained = sorted(covered - floor)
    if gained:  # reported, never a failure: a gate that punishes improvement
        print(f"\n[rc434] {len(gained)} clause(s) newly covered (refresh the floor "
              f"in the commit that earns them):\n  " + "\n  ".join(gained))


def test_bin1_declared_names_are_all_real_exception_classes():
    """STRICT ZERO. A declared name that is not an exception class is a typo.

    This is the one bin the static scope produced that is genuinely decidable.
    """
    known = _known_exception_names() | _THIRD_PARTY_EXCEPTIONS
    clauses = _scan_declared_clauses()
    unknown = sorted(
        {k for k, v in clauses.items() if v["exception"] not in known}
    )
    assert not unknown, (
        f"{len(unknown)} declared exception name(s) resolve to no class:\n  "
        + "\n  ".join(unknown)
        + "\n\nIf one is a real third-party class, add it to "
        "_THIRD_PARTY_EXCEPTIONS *after confirming by import that it exists*."
    )


def test_third_party_allowlist_entries_are_real_and_load_bearing():
    """Each allowlist entry must (a) really exist and (b) still be needed.

    Without (b) the allowlist silently accumulates entries that mask typos.
    """
    try:  # py3.11+ stdlib; `tomli` on the 3.10 CI cell
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - 3.10 only
        import tomli as tomllib

    assert issubclass(tomllib.TOMLDecodeError, Exception)
    known = _known_exception_names()
    for name in _THIRD_PARTY_EXCEPTIONS:
        assert name not in known, (
            f"{name} is now resolvable from the package itself -- drop it from "
            "_THIRD_PARTY_EXCEPTIONS so the bin keeps its teeth."
        )
    declared = {v["exception"] for v in _scan_declared_clauses().values()}
    unused = sorted(_THIRD_PARTY_EXCEPTIONS - declared)
    assert not unused, (
        f"allowlist entries no longer declared anywhere: {unused} -- remove them."
    )


# ─────────────────────────────────────────────────────────── negative controls


def test_prose_mention_is_not_a_declared_clause():
    """A sentence ABOUT another function is not a declaration of this one.

    This is a retracted instrument, encoded so it cannot come back. A flat
    regex read ``feynman_scalar_propagator``'s sentence -- *"writing
    1j/(k2 - m*m) yourself produces a ZeroDivisionError"* -- as a contract.
    It describes the NAIVE ALTERNATIVE. The op raises ValueError.
    """
    doc = (
        "Compute the propagator.\n\n"
        "Writing 1j/(k2 - m*m) yourself produces a ZeroDivisionError at the\n"
        "pole; this op raises instead.\n\n"
        "Raises:\n"
        "    ValueError: on-shell pole with epsilon = 0.\n"
    )
    assert parse_raises_block(doc) == ["ValueError"], (
        "the clause parser leaked a prose mention into the declared set -- "
        "this is exactly the retracted flat-regex behaviour"
    )


def test_clause_parser_handles_both_docstring_dialects_and_stops_at_dedent():
    """Google + numpydoc sections parse; a following section does not bleed in."""
    google = (
        "Summary.\n\n"
        "Raises:\n"
        "    ValueError: bad value.\n"
        "    TypeError: bad type.\n\n"
        "Returns:\n"
        "    RuntimeError is mentioned here and must NOT be picked up.\n"
    )
    assert parse_raises_block(google) == ["ValueError", "TypeError"]

    numpy = (
        "Summary.\n\n"
        "Raises\n"
        "------\n"
        "OverflowError\n"
        "    too big.\n\n"
        "Notes\n"
        "-----\n"
        "KeyError appears here and must NOT be picked up.\n"
    )
    assert parse_raises_block(numpy) == ["OverflowError"]

    assert parse_raises_block("") == []
    assert parse_raises_block("No sections at all, but ValueError in prose.") == []


def test_coverage_is_zero_when_the_corpus_is_empty():
    """An instrument that cannot return otherwise is not a measurement.

    The floor gate is only worth having if an empty corpus reports ZERO
    coverage rather than inheriting it from somewhere.
    """
    assert _covered_clause_keys([]) == set()


def test_coverage_counter_ignores_a_probe_that_stops_raising():
    """Mutation: a probe whose op returns instead of raising must NOT count."""
    fake = (
        "control/op-that-returns",
        "srmech.math.cyclic.gcd",
        "ValueError",
        (4, 6),  # perfectly valid input -> returns 2, raises nothing
        {},
        "negative control: the declared trigger is not fired",
    )
    assert _covered_clause_keys([fake]) == set(), (
        "the coverage counter credited a clause whose probe did not raise"
    )


def test_coverage_counter_ignores_an_undeclared_raise():
    """Mutation: a raise the docstring never promised is NOT clause coverage.

    Otherwise the floor could be grown by writing probes instead of by writing
    declarations, which inverts what the ratchet is for. ``sha256_bytes``
    declares nothing, so its TypeError cannot be coverage of anything.
    """
    undeclared = (
        "control/undeclared-raise",
        "srmech.amsc.format.sha256_bytes",
        "TypeError",
        ("not-bytes",),
        {},
        "negative control: real raise, no declaration behind it",
    )
    rec = _run_probe(undeclared)
    assert rec["outcome"] == "ENFORCED", (
        f"control is inert -- sha256_bytes no longer raises TypeError here: {rec}"
    )
    assert _covered_clause_keys([undeclared]) == set(), (
        "an undeclared raise was credited as clause coverage"
    )


def test_probe_runner_fails_an_inverted_expectation():
    """Mutation: invert one probe's expectation; the runner must classify it bad."""
    inverted = (
        "control/inverted",
        "srmech.math.cyclic.gcd",
        "OverflowError",  # it actually raises ValueError
        (-1, 5),
        {},
        "negative control",
    )
    rec = _run_probe(inverted)
    assert rec["outcome"] == "TYPE_MISMATCH", rec
    assert rec["observed"] == "ValueError", rec

    absent = (
        "control/expects-no-raise-but-raises",
        "srmech.math.cyclic.gcd",
        _NO_RAISE,
        (-1, 5),
        {},
        "negative control",
    )
    assert _run_probe(absent)["outcome"] == "UNEXPECTED_RAISE"


def test_bin1_flags_a_planted_unknown_class_name():
    """Mutation: BIN-1 must actually fire on a name that resolves to nothing."""
    known = _known_exception_names() | _THIRD_PARTY_EXCEPTIONS
    assert "NoSuchThingError" not in known
    planted = parse_raises_block(
        "Summary.\n\nRaises:\n    NoSuchThingError: planted.\n"
    )
    assert planted == ["NoSuchThingError"]
    assert planted[0] not in known, "BIN-1 would not have flagged a planted typo"


def test_the_corpus_is_not_trivially_satisfiable():
    """Every probe must name a DISTINCT id, and the absence-pins must exist.

    A corpus of duplicates would pass while measuring one thing many times.
    """
    ids = [p[0] for p in PROBES]
    assert len(ids) == len(set(ids)), "duplicate probe ids"
    absence = [p for p in PROBES if p[2] is _NO_RAISE]
    assert len(absence) >= 5, (
        "the rc167 no-upper-cap contract needs its absence-pins: they are the "
        "only thing standing between the tree and re-writing the four pieces "
        "of prose rc434 corrected"
    )


def test_scan_finds_a_substantial_declared_population():
    """Guard the scanner itself: a path bug would silently report 0 clauses."""
    clauses = _scan_declared_clauses()
    assert len(clauses) > 150, (
        f"only {len(clauses)} declared clauses found under {_SRC} -- the scan "
        "root is probably wrong"
    )


def _regenerate() -> int:
    covered = sorted(_covered_clause_keys(PROBES))
    _FLOOR_PATH.write_text(
        "# rc434 `#T1130` -- declared Raises: clauses under EXECUTION.\n"
        "# A FLOOR: this set may grow, never shrink. Regenerate with\n"
        f"#     python -m tests.{Path(__file__).stem}\n"
        + "\n".join(covered)
        + "\n",
        encoding="utf-8",
    )
    total = len(_scan_declared_clauses())
    print(f"srmech {srmech.__version__} @ {_SRC}")
    print(f"probes={len(PROBES)} covered={len(covered)} of {total} declared clauses")
    print(f"wrote {_FLOOR_PATH}")
    return 0


if __name__ == "__main__":  # pragma: no cover - maintenance entry point
    sys.exit(_regenerate())
