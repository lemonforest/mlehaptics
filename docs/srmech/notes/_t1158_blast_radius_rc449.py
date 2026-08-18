"""`#T1158` / rc449 — S8, the PRE-MERGE BLAST-RADIUS CENSUS.

Both new C validators REFUSE a declaration that rc448 accepted. Before that ships,
every chain descriptor IN THE TREE must be run through the same rule, because a
refusal is not a validator bug — it is a descriptor that has been declaring a key
its op does not have, and computing anyway.

⚠️ ANY OFFENDER IS A DESCRIPTOR DEFECT TO FIX IN THIS RC, NEVER A REASON TO LOOSEN
THE VALIDATOR. That inversion is how a real finding becomes a widened rule.

WHERE THE DESCRIPTORS ACTUALLY ARE — a correction to the rc449 brief, which
expected "every packaged ``cascade_catalog`` descriptor (20)". Measured: there are
21 ``.toml`` files under ``srmech/cascade/catalogs/cascade_catalog/`` (23 directory
entries, of which one is ``__pycache__`` and one a ``.py``), and NONE of them is a
chain descriptor. They are per-op catalog entries (``[cascade] name /
class_composition / purpose``) with no ``steps`` and no ``args``, so the key-set
rule cannot apply to them. A tree-wide search for TOML chain descriptors
(``[[steps]]``) returns ZERO. Chain descriptors in this tree are Python dict
literals, overwhelmingly in test fixtures — so those are the blast radius, and
this script censuses them by AST rather than by import (importing a test module
runs its collection side effects and would miss dicts built inside functions).

Both surfaces are covered:
  * compose steps  — ``{"op": ..., "args": {...}}``   legal set = params[*]
  * DSL stages     — ``{"op": ..., <kwarg>: ...}``    legal set = params[1..]

Run under WSL2 (numpy-absent):
    cd python && PYTHONPATH=. python3 ../notes/_t1158_blast_radius_rc449.py
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import List, Optional, Tuple

from srmech._resolve import resolve_dotted_callable
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

#: the seven ops srmech_dsl_chain_run really runs (DSL surface, params[1..])
DSL_LEAVES = ("magnitude", "reorient", "pin_slot_at_zero",
              "best_rational_signed", "chiral_flip", "net_chirality",
              "autocorrelation")

#: the twenty ops srmech_chain_run really runs (compose surface, params[*])
CR_OPS = ("pi_cascade_digits", "exp_series_truncate", "sin_series_truncate",
          "cos_series_truncate", "log1p_series_truncate", "atan_series_truncate",
          "rational_pow_uint", "rational_add", "rational_mul", "rational_div",
          "gcd", "mod_add", "mod_mul", "mod_mul_wide", "mod_pow", "mod_inv",
          "pin_slot_at_zero", "reorient", "chiral_flip", "autocorrelation")

#: the seven COMBINATOR discriminators dsl_stage_is_combinator diverts on. A stage
#: carrying any of them never reaches dsl_leaf_dispatch, so the leaf key-set rule
#: does not apply to it — that is the F5 surface rc449 files rather than closes.
COMBINATOR_KEYS = {"loop_n", "sub_chain", "fold_init", "fold_op", "reduce_op",
                   "parallel_body", "map_op"}


def _params_of(op_bare: str) -> Optional[List[str]]:
    """Live parameter names of the op the runners would bind, in order."""
    warmup_all()
    hits = [t.name for t in get_tool_schema().tools
            if t.name.rpartition(".")[2] == op_bare]
    if len(hits) != 1:
        return None
    try:
        fn = resolve_dotted_callable(hits[0])
        params = inspect.signature(fn).parameters
    except Exception:
        return None
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return ["**OPEN**"]
    return [n for n, p in params.items()
            if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                          inspect.Parameter.KEYWORD_ONLY)]


def _const_keys(node: ast.Dict) -> Optional[List[str]]:
    """The dict's string keys, or None if any key is not a plain string."""
    out = []
    for k in node.keys:
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            out.append(k.value)
        else:
            return None
    return out


def _op_value(node: ast.Dict) -> Optional[str]:
    for k, v in zip(node.keys, node.values):
        if (isinstance(k, ast.Constant) and k.value == "op"
                and isinstance(v, ast.Constant) and isinstance(v.value, str)):
            return v.value
    return None


def _scan(path: Path) -> List[Tuple[str, str, str, List[str]]]:
    """(surface, op, where, offending_keys) for every chain-ish dict in a file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = _const_keys(node)
        if keys is None or "op" not in keys:
            continue
        op = _op_value(node)
        if op is None:
            continue
        bare = op.rpartition(".")[2]
        where = f"{path.name}:{node.lineno}"

        # ── compose step: {"op": ..., "args": {...}} ──
        if "args" in keys and bare in CR_OPS:
            for k, v in zip(node.keys, node.values):
                if (isinstance(k, ast.Constant) and k.value == "args"
                        and isinstance(v, ast.Dict)):
                    akeys = _const_keys(v)
                    if akeys is None:
                        continue
                    params = _params_of(bare)
                    if params is None or params == ["**OPEN**"]:
                        continue
                    extra = sorted(set(akeys) - set(params))
                    if extra:
                        found.append(("compose", op, where, extra))

        # ── DSL stage: {"op": ..., <kwarg>: ...} with no "args" ──
        # Three exclusions, each because the dict CANNOT reach dsl_leaf_keyset_ok:
        #  * a COMBINATOR discriminator — dsl_stage_is_combinator diverts the
        #    stage before dsl_leaf_dispatch is ever called. (Measured false
        #    positive: tests/test_dsl.py's multi-discriminator negative case,
        #    {"op":"chiral_flip","reduce_op":"cyclic_gcd"}, which asserts the
        #    PYTHON builder raises "multiple discriminators". That is the F5
        #    surface rc449 explicitly FILES rather than closes.)
        #  * a DOTTED op — dsl_leaf_dispatch compares exact bare names with an
        #    exact-length memcmp, so a dotted spelling defers and is never
        #    validated. (Measured false positive: tests/test_mcp.py's
        #    invoke_tool("srmech.cascade.chiral_dual", {"op": ..., "x": ...}),
        #    which is not a stage at all — it is chiral_dual's own ARGUMENTS,
        #    where both "op" and "x" are real parameters.)
        #  * this rc's own refusal harness, whose malformed stages are the point.
        elif "args" not in keys and bare in DSL_LEAVES:
            if "." in op:
                continue
            if set(keys) & COMBINATOR_KEYS:
                continue
            if path.name == "test_t1158_refusal_set_equality_rc449.py":
                continue
            params = _params_of(bare)
            if params is None or params == ["**OPEN**"]:
                continue
            legal = set(params[1:]) | {"op"}
            extra = sorted(set(keys) - legal)
            if extra:
                found.append(("dsl", op, where, extra))
    return found


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    targets = sorted(
        list((root / "python" / "tests").rglob("*.py"))
        + list((root / "python" / "srmech").rglob("*.py")))
    targets = [p for p in targets if "__pycache__" not in p.parts]

    print("== S8 blast radius: chain descriptors vs the rc449 key sets ==")
    print(f"   python files scanned : {len(targets)}")

    tomls = list((root / "python" / "srmech").rglob(
        "cascade_catalog/*.toml"))
    print(f"   packaged cascade_catalog TOMLs : {len(tomls)} "
          f"(none is a chain descriptor — see the module docstring)")

    offenders = []
    for p in targets:
        offenders.extend(_scan(p))

    print(f"   OFFENDING descriptors : {len(offenders)}")
    for surface, op, where, extra in offenders:
        params = _params_of(op.rpartition(".")[2])
        print(f"     !! [{surface}] {where}  {op} declares {extra}; "
              f"live params = {params}")

    print()
    if not offenders:
        print("VERDICT: CLEAN — no in-tree chain descriptor declares a key its "
              "op does not have. The validators refuse nothing that ships.")
        return 0
    print("VERDICT: DEFECT — fix these descriptors in this rc. Do NOT loosen "
          "the validator; an accepted-but-meaningless key is the finding.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
