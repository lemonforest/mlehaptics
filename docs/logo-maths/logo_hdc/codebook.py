"""Part-B rule codebook. Structured rule HVs, built from each
production's constituents.

Each rule is a bundle over:
    - its `kind` (e.g., STMT / NUM / BLOCK / PROG)
    - its `shape` — an anonymous per-rule atom so two rules with the
      same kind (e.g., two STMT productions) can still be told apart
    - per-child position bindings: bind(pos_i, child_kind_atom_i)

This mirrors Part-A's "bundle over role-value bindings" pattern; rules
get the same independent-inferability property — you can probe a rule
HV for its kind, its shape, or for what appears at slot i, without
fully decoding.
"""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

from .hd import HD, DEFAULT_DIM, atom, bundle, bundle_sum, bind

from logo_ast import ALL_RULES


# Mapping: each rule → (kind, shape, [child_kinds_by_position])
# `kind` is the non-terminal this rule produces (PROG / STMT / BLOCK / NUM).
# `shape` is a rule-unique tag that separates same-kind productions.
# `children` are the kinds (or commands) appearing in the rule body.

RULE_STRUCTURE: Dict[str, Tuple[str, str, List[str]]] = {
    "r_PROG_is_STMT_star":        ("PROG",  "list_of_stmt",   ["STMT"]),
    "r_BLOCK_is_STMT_star":       ("BLOCK", "list_of_stmt",   ["STMT"]),
    "r_STMT_is_MOTION_NUM":       ("STMT",  "motion_num",     ["MOTION", "NUM"]),
    "r_STMT_is_PEN":              ("STMT",  "pen_toggle",     ["PEN"]),
    "r_STMT_is_REPEAT_NUM_BLOCK": ("STMT",  "repeat",         ["REPEAT", "NUM", "BLOCK"]),
    "r_STMT_is_IF_COND_BLOCK":    ("STMT",  "cond",           ["IF", "NUM", "BLOCK"]),
    "r_STMT_is_TO_NAME_ARGS_BLOCK_END": ("STMT", "define_proc",
                                         ["TO", "NAME", "PARAMS", "BLOCK", "END"]),
    "r_STMT_is_CALL_ARGS":        ("STMT",  "call_proc",      ["NAME", "NUM"]),
    "r_STMT_is_MAKE_NAME_EXPR":   ("STMT",  "bind_var",       ["MAKE", "NAME", "NUM"]),
    "r_NUM_is_literal":           ("NUM",   "literal",        []),
    "r_NUM_is_VAR":               ("NUM",   "var_ref",        ["THING"]),
    "r_NUM_is_BINOP_NUM_NUM":     ("NUM",   "binop",          ["OP", "NUM", "NUM"]),
}

KINDS = ("PROG", "STMT", "BLOCK", "NUM")


def build_rule_codebook(*, dim: int = DEFAULT_DIM) -> Dict[str, HD]:
    """Return {rule_name → hv} for Part B, plus the structural atoms
    used to build them (role_kind, role_shape, pos_i, kind_*, ...).
    """
    # Structural / role atoms.
    cb: Dict[str, HD] = {
        "role_kind":  atom("role_kind",  dim=dim),
        "role_shape": atom("role_shape", dim=dim),
    }
    # Per-position atoms — up to 5 children.
    for i in range(5):
        cb[f"pos_{i}"] = atom(f"pos_{i}", dim=dim)

    # kind atoms (inherent to non-terminals)
    for k in KINDS:
        cb[f"kind_{k}"] = atom(f"kind_{k}", dim=dim)
    # child-type atoms beyond bare non-terminals (terminals / lists)
    for extra in ("MOTION", "PEN", "REPEAT", "IF", "TO", "END", "MAKE",
                  "THING", "NAME", "PARAMS", "OP"):
        cb[f"kind_{extra}"] = atom(f"kind_{extra}", dim=dim)

    # Assemble rule HVs. Check ALL_RULES is covered.
    for rname in ALL_RULES:
        if rname not in RULE_STRUCTURE:
            raise KeyError(f"RULE_STRUCTURE missing {rname}")
    for rname in RULE_STRUCTURE:
        if rname not in ALL_RULES:
            raise KeyError(f"ALL_RULES missing {rname} "
                           f"(declared in RULE_STRUCTURE)")

    for rname, (kind, shape, children) in RULE_STRUCTURE.items():
        parts = [
            bind(cb["role_kind"],  cb[f"kind_{kind}"]),
            bind(cb["role_shape"], atom(f"shape_{shape}", dim=dim)),
        ]
        for i, ck in enumerate(children):
            parts.append(bind(cb[f"pos_{i}"], cb[f"kind_{ck}"]))
        # Unbinarized: keeps kind-locality sim margins interpretable
        # and makes sum-of-rules in encoders additive without
        # re-thresholding.
        cb[rname] = bundle_sum(parts)

    return cb
