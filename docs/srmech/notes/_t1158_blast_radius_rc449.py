"""`#T1158` / rc449 — S8, the PRE-MERGE BLAST-RADIUS CENSUS.

Both new C validators REFUSE a declaration that rc448 accepted. Before that ships,
every chain descriptor IN THE TREE must be run through the same rule, because a
refusal is not a validator bug — it is a descriptor that has been declaring a key
its op does not have, and computing anyway.

⚠️ ANY OFFENDER IS A DESCRIPTOR DEFECT TO FIX IN THIS RC, NEVER A REASON TO LOOSEN
THE VALIDATOR. That inversion is how a real finding becomes a widened rule.

WHERE THE DESCRIPTORS ACTUALLY ARE — there are TWO populations, and an earlier
revision of this docstring got the first one flatly wrong.

⚠️ RETRACTED at rc449 pre-merge review, and recorded rather than quietly deleted.
This file previously claimed the 21 packaged ``cascade_catalog`` TOMLs carry "no
``steps`` and no ``args``", that "NONE of them is a chain descriptor", and that a
tree-wide search "returns ZERO". All three were false. The null came from
searching ``[[steps]]`` — THE WRONG OPERATOR; the shipped form is
``[[cascade.chain.steps]]``, and the tree's own notebook already records
``describe()["cascade_catalog"] == {"total": 21, "executable": 18, "leaf": 3}``.
Worse, the script did not parse a single TOML: it globbed them, printed that
sentence as a HARDCODED LITERAL, and censused only ``.py`` files by AST. **An
instrument that cannot return otherwise is not a measurement** — the exact
failure class rc449 exists to close, reproduced inside rc449's own verification
script. The earlier VERDICT (0 offenders) was correct; what was missing was the
act of measuring.

MEASURED NOW, parsing every file through srmech's own TOML front door
(``srmech._toml.loads``, native-first — never ``tomllib``/``tomli``, which the
self-hosting ban table lists FRONT_DOOR_ONLY):

  * **TOML population** — 21 packaged descriptors, of which **18 carry
    ``[[cascade.chain.steps]]``** with ``class`` / ``op`` / ``args`` (the
    Surface-A shape); 3 are declared leaves. These ARE chain descriptors and the
    key-set rule DOES apply to them. Recursively they hold **134 steps: 120
    op-bearing, 115 args-bearing** — and the args-bearing figure is the one the
    key-set rule actually ranges over.

    ⚠️ **THE STEPS NEST, AND A FLAT WALK SEES 54% OF THEM.** A ``map_over`` step
    carries no op-naming key itself; its ops live in a nested ``body`` list,
    which may hold further map steps (``kuramoto_step.toml`` nests body-in-body).
    Walking only ``chain["steps"]`` finds 72 of 134 steps and 62 of 115
    args-bearing ones — and still prints ``VERDICT: CLEAN``, because absence of
    offenders is indistinguishable from absence of looking. A first patch of this
    script did exactly that; it was caught only because its 62 CONTRADICTED the
    115 an independent verifier had measured. See ``_walk_steps``. The same
    revision also skipped ``fold_op`` steps, so a fold-only file counted as
    carrying no chain at all (17 files, not 18).
  * **Python population** — chain descriptors as dict literals, overwhelmingly in
    test fixtures. The Python half is censused by AST rather than
by import, because importing a test module runs its collection side effects and
would miss dicts built inside functions. Both halves are scanned below.

RUN IT AS:  ``PYTHONPATH=. python ../notes/_t1158_blast_radius_rc449.py``  from
``docs/srmech/python`` — ``sys.path[0]`` is the SCRIPT's directory, not the cwd.

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



def _walk_steps(steps):
    """Yield every step at EVERY nesting depth.

    ``map_over`` / ``parallel`` steps carry no op-naming key of their own — the
    ops live inside a nested ``body`` list, and that list may itself hold more
    map steps (``kuramoto_step.toml`` nests body-in-body). A flat walk over
    ``chain["steps"]`` therefore sees 72 of the tree's 134 steps and 62 of its
    115 args-bearing ones, i.e. it is blind to 54% of its own subject while
    reporting CLEAN. That is precisely the defect class rc449 exists to close,
    so this walk recurses.
    """
    for step in steps or []:
        yield step
        body = step.get("body")
        if isinstance(body, list):
            yield from _walk_steps(body)


def _scan_packaged_tomls(root):
    """PARSE every packaged cascade_catalog descriptor; check each step's args.

    Returns (offenders, n_tomls, n_steps, n_chain_files). An offender is a step
    whose ``args`` names a key its op does not accept — the rc449 rule.
    """
    from srmech import _toml

    tomls = sorted((root / "python" / "srmech").rglob("cascade_catalog/*.toml"))
    offenders, n_steps, n_chain_files = [], 0, 0
    for path in tomls:
        doc = _toml.loads(path.read_text(encoding="utf-8"))
        chains = (doc.get("cascade") or {}).get("chain") or []
        if isinstance(chains, dict):
            chains = [chains]
        saw = False
        for chain in chains:
            for step in _walk_steps(chain.get("steps")):
                saw = True
                n_steps += 1
                op = step.get("op") or step.get("fold_op")
                if not op:
                    continue
                params = _params_of(str(op).rpartition(".")[2])
                if params is None or params == ["**OPEN**"]:
                    continue
                extra = sorted(set(step.get("args") or {}) - set(params))
                if extra:
                    offenders.append(("toml", op, path.name, extra))
        if saw:
            n_chain_files += 1
    return offenders, len(tomls), n_steps, n_chain_files


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    targets = sorted(
        list((root / "python" / "tests").rglob("*.py"))
        + list((root / "python" / "srmech").rglob("*.py")))
    targets = [p for p in targets if "__pycache__" not in p.parts]

    print("== S8 blast radius: chain descriptors vs the rc449 key sets ==")
    print(f"   python files scanned : {len(targets)}")

    toml_off, n_tomls, n_steps, n_chain_files = _scan_packaged_tomls(root)
    print(f"   packaged cascade_catalog TOMLs : {n_tomls} "
          f"({n_chain_files} carry [[cascade.chain.steps]], "
          f"{n_steps} steps parsed)")

    offenders = list(toml_off)
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
