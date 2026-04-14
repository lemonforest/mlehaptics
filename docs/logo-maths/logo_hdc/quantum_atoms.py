"""Part-A vocabulary: quantum-numbered command atoms.

Each of the ~12 LOGO commands gets a 5-tuple (category, arity, argtype,
reverse_axis, is_block_opener). The command atom is a *structured*
bundle_sum over role-value bindings, analogous to how chess pieces
derive their spectral value from their physical attributes:

    a_c = bundle_sum(
        bind(role_category, val_category[c]),
        bind(role_arity,    val_arity[c]),
        bind(role_argtype,  val_argtype[c]),
        bind(role_reverse,  val_reverse[c]),
        bind(role_block,    val_block[c]),
    )

Iteration-2 correction
----------------------
Iteration-1 claimed `bind(a_FORWARD, flip_axis) ≈ a_BACK ✓`. That was
wrong. Single-vector flip-binding cannot algebraically swap one role
inside a bundle_sum of 5 role-value bindings — measured cos with BACK
is -0.004, indistinguishable from the cos with RIGHT or LEFT. The high
FORWARD↔BACK structural similarity (~0.80) comes entirely from shared
quantum numbers (4/5 roles match), not from any flip operation.

The correct algebra is **role-level**:

    unbind_role(cmd_hv, "role_reverse", cb)
        = cmd_hv * cb["role_reverse"]
        ≈ cb["rev_TRANS_FWD"]   (with ~1/√5 SNR; the other 4 role
                                  bindings become orthogonal noise)

    swap_role_value(cmd_hv, "role_reverse", "rev_TRANS_FWD",
                    "rev_TRANS_REV", cb)
        = cmd_hv - bind(role_reverse, rev_TRANS_FWD)
                 + bind(role_reverse, rev_TRANS_REV)
        ≈ a_BACK   (clean swap because we operate on the unbinarized
                     bundle_sum representation)

The `bundle_sum` choice in iteration-1 was the right one, but for the
wrong reason — it preserves linearity for *role swaps*, not for
whole-atom flips. `flip_axis` and `REVERSE_OF` are deleted as part
of the correction.
"""
from __future__ import annotations

from typing import Dict, Tuple

from .hd import HD, DEFAULT_DIM, atom, bundle, bundle_sum, bind

# Quantum-number tuples: (category, arity, argtype, reverse_axis, block_opener)
# reverse_axis tags must be *pair-unique* — if FORWARD and RIGHT both used
# plain "FWD"/"REV", their quantum tuples would collide across the pair
# boundary (FORWARD would be indistinguishable from RIGHT, since they
# share category/arity/argtype/block). So each pair gets its own axis
# namespace: TRANS_*, ROT_*, PEN_*, ...
COMMAND_QUANTUM: Dict[str, Tuple[str, int, str, str, bool]] = {
    # spatial motions — translation pair
    "FORWARD": ("spatial", 1, "number",    "TRANS_FWD", False),
    "BACK":    ("spatial", 1, "number",    "TRANS_REV", False),
    # spatial motions — rotation pair (distinct axis from translation)
    "RIGHT":   ("spatial", 1, "number",    "ROT_FWD",   False),
    "LEFT":    ("spatial", 1, "number",    "ROT_REV",   False),
    # pen state
    "PENUP":   ("state",   0, "none",      "PEN_UP",    False),
    "PENDOWN": ("state",   0, "none",      "PEN_DOWN",  False),
    # control flow
    "REPEAT":  ("control", 2, "num_block", "LOOP",      True),
    "IF":      ("control", 2, "cond_block","COND",      True),
    "TO":      ("control", 1, "block",     "DEF_OPEN",  True),
    "END":     ("control", 0, "none",      "DEF_CLOSE", False),
    # binding
    "MAKE":    ("binding", 2, "name_expr", "SET",       False),
    "THING":   ("binding", 1, "name",      "GET",       False),
}

CATEGORIES = ("spatial", "state", "control", "binding")
ARGTYPES   = ("none", "number", "cond_block", "num_block", "block",
              "name", "name_expr")
REVERSE_AXES = (
    "TRANS_FWD", "TRANS_REV",
    "ROT_FWD",   "ROT_REV",
    "PEN_UP",    "PEN_DOWN",
    "DEF_OPEN",  "DEF_CLOSE",
    "SET",       "GET",
    "LOOP",      "COND",
)

# Roles (the `role_*` keys in the codebook). Public so role-level
# operations can validate inputs.
ROLE_NAMES = (
    "role_category", "role_arity", "role_argtype",
    "role_reverse",  "role_block",
)


def _role_value_atoms(*, dim: int) -> Dict[str, HD]:
    """Atoms for the roles (role_category etc.) and for every value any
    role can take. One dict for discoverability."""
    names = list(ROLE_NAMES)
    # category values
    names += [f"cat_{c}" for c in CATEGORIES]
    # arity values (0..3)
    names += [f"arity_{i}" for i in range(4)]
    # argtype values
    names += [f"argtype_{a}" for a in ARGTYPES]
    # reverse-axis values
    names += [f"rev_{r}" for r in REVERSE_AXES]
    # block-opener booleans
    names += ["block_true", "block_false"]
    return {n: atom(n, dim=dim) for n in names}


def build_vocab_codebook(*, dim: int = DEFAULT_DIM) -> Dict[str, HD]:
    """Return {command → hv} for Part A. Deterministic; same dim → same HVs.

    Also exposes the role/value atoms used to *build* the commands via
    keys prefixed `role_`, `cat_`, `arity_`, `argtype_`, `rev_`,
    `block_`. Those are useful for downstream probing (e.g.,
    `unbind_role(a_FORWARD, "role_reverse", cb)` cleans to "rev_TRANS_FWD")
    without re-deriving the role atoms.
    """
    rv = _role_value_atoms(dim=dim)
    cb: Dict[str, HD] = dict(rv)   # include building blocks

    for cmd, (cat, arity, argtype, rev_axis, is_opener) in COMMAND_QUANTUM.items():
        parts = [
            bind(rv["role_category"], rv[f"cat_{cat}"]),
            bind(rv["role_arity"],    rv[f"arity_{arity}"]),
            bind(rv["role_argtype"],  rv[f"argtype_{argtype}"]),
            bind(rv["role_reverse"],  rv[f"rev_{rev_axis}"]),
            bind(rv["role_block"],
                 rv["block_true"] if is_opener else rv["block_false"]),
        ]
        # Unbinarized sum: keeps role-swap algebra linear, so
        # cmd_hv - bind(role, old_val) + bind(role, new_val)
        # cleanly produces the sibling pair member rather than
        # getting scrambled by majority-vote binarization.
        cb[cmd] = bundle_sum(parts)

    return cb


# ─── Role-level operations (iteration-2 corrected reversibility API) ─

def unbind_role(cmd_hv: HD, role_name: str, codebook: Dict[str, HD]) -> HD:
    """Extract the value-HV bound to `role_name` inside `cmd_hv`.

    Algebra: `cmd_hv = Σ_i bind(role_i, val_i)`. Binding with role_R
    self-inverts the role_R term and leaves the other 4 as noise:

        cmd_hv ⊙ role_R
          = bind(role_R, val_R) ⊙ role_R                   (self-inverse)
          + Σ_{i ≠ R} bind(role_i ⊙ role_R, val_i)          (noise)
          = val_R + (4 cross-terms ~ uncorrelated to anything)

    SNR is ~1/√5 — measured cosine to the true value-HV ≈ 0.45 at
    D=10000. Cleanup against the value-HV codebook recovers the
    quantum-number value.
    """
    if role_name not in ROLE_NAMES:
        raise KeyError(
            f"unknown role {role_name!r}; expected one of {ROLE_NAMES}"
        )
    return cmd_hv * codebook[role_name]


def swap_role_value(
    cmd_hv: HD,
    role_name: str,
    old_value_key: str,
    new_value_key: str,
    codebook: Dict[str, HD],
) -> HD:
    """Replace the value bound to `role_name` from old → new.

    Returns a fresh real-valued HV (still in the bundle_sum domain):

        cmd_hv' = cmd_hv
                  - bind(codebook[role_name], codebook[old_value_key])
                  + bind(codebook[role_name], codebook[new_value_key])

    Cleanup against the command codebook should retrieve the sibling
    pair member when (role, old → new) is the only differing quantum
    number — e.g. swap_role_value(a_FORWARD, "role_reverse",
    "rev_TRANS_FWD", "rev_TRANS_REV", cb) → cleans to a_BACK.
    """
    if role_name not in ROLE_NAMES:
        raise KeyError(
            f"unknown role {role_name!r}; expected one of {ROLE_NAMES}"
        )
    role_hv = codebook[role_name]
    old_binding = bind(role_hv, codebook[old_value_key])
    new_binding = bind(role_hv, codebook[new_value_key])
    return cmd_hv - old_binding + new_binding
