"""rc462 (`#T1179`) — the ``content_address_fields`` CLASS declaration.

**What this closes.** srmech ships Class-A digests on op payloads —
``matrices_sha256``, ``cayley_sha256``, ``operator_sha256``,
``procedure_sha256``, and 50-odd more. rc461's 19-mutation adversarial pass
measured that these fields were **ungated by default**: a digest could be
replaced with a constant and the suite stayed green. The instance holes were
then closed one at a time, by hand, as ``test_g14_*`` gates in the file that
happened to ship the op. Eleven such gates exist, rc109 → rc461.

**Hand-written instance gates are a RATCHET: they cover what someone
remembered.** This module is the DRAIN. A field is covered because it is
DECLARED, and the gate over this declaration is strict-zero in BOTH
directions — an undeclared emitted field is red, and a declared field that is
no longer emitted is red too. A new op is covered the day it is declared, and
it cannot ship undeclared.

**Why it lives in ``tools/`` and not on ``ToolEntry`` (Phase 1 of 2).** The
natural home is a ``content_address_fields`` key on each ``ToolEntry``, and
that remains the target. It is deferred with its reason MEASURED: the
precedent commit for adding a ToolEntry field moved ``srmech.h`` +40 and
``srmech_tool_registry.c`` +1375, added a 173-line key-set pin, **and moved
``tool_schema_sha256``** — the wrong ripple to stack on an rc whose core is a
hash-serializer widening that must not move a shipped ℚ hash. Phase 2 promotes
this table to the registry; nothing here is thrown away when it does, because
the executors take ``(op, path, decl)`` and do not care where ``decl`` came
from.

**The five kinds are DERIVED from the eleven existing gates, not invented.**
Each is a different CONTRACT, and reading all five as "stable and
distinguishing" is what made three of them vacuous:

``answer``
    Addresses the op's OWN result. Stable for a fixed input; MOVES when the
    answer moves.
``operand``
    Addresses an INPUT the op read (``cayley_sha256`` addresses the Cayley
    table it was handed). Stable for a fixed operand; moves when that operand
    moves; and — the part a name-match cannot know — EQUAL across two
    different ops handed the same operand.
``procedure``
    Addresses the op's own rule. **CONSTANT across different inputs.** A
    "stable and distinguishing" gate on this field asserts the opposite of its
    contract. Its verdict is VACUOUS unless the ANSWER moved under the same
    perturbation, which is asserted.
``echo``
    Repeats another surface's address verbatim (``g2_membership``'s
    ``frame_sha256`` IS ``epq_frame_address()``). Checked against the named
    source, never against a copy of it.
``pinned``
    A shipped attestation constant, carried here as a literal so a silent
    change to a citation's ``response_sha256`` is red.

**Discipline.** No numpy. No new ``hashlib.sha256`` — digests are read, never
minted here. No ``abs()``. The perturbation corpus is BUILT from the shipped
constructors at call time, never inlined as literal tables, so it cannot rot
into a copy of the thing under test.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import example_args as _ea  # noqa: E402

#: The five contracts. Every declaration names exactly one.
KINDS: Tuple[str, ...] = ("answer", "operand", "procedure", "echo", "pinned")

#: The MPR attestation of Baez, *The Octonions* (arXiv:math/0105155) — the
#: shipped citation behind the so8 branching ops. Constant by contract: it
#: addresses the CITED SOURCE, not the answer.
_BAEZ_OCTONIONS_MPR = \
    "055ee0200fdb6483dd567df582547788b93c8e8ef1cbfbe5129c9787f264f731"


class Decl:
    """One declared content-address field."""

    __slots__ = ("kind", "why", "echo_source", "pinned", "empty_ok")

    def __init__(self, kind: str, why: str, echo_source: Optional[str] = None,
                 pinned: Optional[str] = None, empty_ok: bool = False) -> None:
        if kind not in KINDS:
            raise ValueError(f"unknown kind {kind!r}; expected one of {KINDS}")
        if (kind == "echo") != (echo_source is not None):
            raise ValueError("kind 'echo' needs echo_source, and only it may")
        if (kind == "pinned") != (pinned is not None):
            raise ValueError("kind 'pinned' needs pinned, and only it may")
        self.kind = kind
        self.why = why
        self.echo_source = echo_source
        self.pinned = pinned
        self.empty_ok = empty_ok

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Decl({self.kind!r})"


_A = "answer"
_O = "operand"
_P = "procedure"
_E = "echo"
_N = "pinned"

_PROC_WHY = ("addresses the op's own RULE — constant across inputs by "
             "contract, so a 'distinguishing' assertion here would be false")
_OPERAND_WHY = "addresses the Cayley table the op was HANDED, not its answer"

#: (op dotted name, dotted field path in the payload) -> Decl.
#: MEASURED at rc462 by driving every ``ok`` row of the example-args ledger and
#: walking the returned payload for ``*_sha256`` leaves: 29 ops, 55 pairs.
DECLARATIONS: Dict[Tuple[str, str], Decl] = {
    # ── AMSC ──────────────────────────────────────────────────────────────
    ("srmech.amsc.catalog.get_attested_dataset",
     "rows[].attestation.response_sha256"): Decl(
        _O, "addresses the fetched SOURCE bytes for the row, not the query"),

    # ── cascade ───────────────────────────────────────────────────────────
    ("srmech.cascade.anti_automorphism_witnesses", "anti_sha256"): Decl(_A, ""),
    ("srmech.cascade.anti_automorphism_witnesses", "commuting_sha256"): Decl(_A, ""),
    ("srmech.cascade.anti_automorphism_witnesses", "direct_sha256"): Decl(_A, ""),
    ("srmech.cascade.conjugacy_census", "class_partition_sha256"): Decl(_A, ""),
    ("srmech.cascade.finite_semiflow", "eventual_image_sha256"): Decl(_A, ""),
    ("srmech.cascade.reversal_law_census", "bare_sha256"): Decl(_A, ""),
    ("srmech.cascade.reversal_law_census",
     "bare_vs_chiral_flat_intersection_sha256"): Decl(_A, ""),
    ("srmech.cascade.reversal_law_census",
     "bare_vs_chiral_flat_left_only_sha256"): Decl(_A, ""),
    ("srmech.cascade.reversal_law_census",
     "bare_vs_chiral_flat_right_only_sha256"): Decl(_A, ""),
    ("srmech.cascade.reversal_law_census",
     "bare_vs_chiral_intersection_sha256"): Decl(_A, ""),
    ("srmech.cascade.reversal_law_census",
     "bare_vs_chiral_left_only_sha256"): Decl(
        _A,
        "EMPTY_OK. MEASURED: on the shipped example this field is exactly "
        "sha256_bytes(b'') — the left-only difference set is empty. 'Stable "
        "and distinguishing' therefore passes on it VACUOUSLY, and it stays "
        "empty under every perturbation tried. Declared with its reason "
        "rather than silently satisfying a gate it cannot exercise.",
        empty_ok=True),
    ("srmech.cascade.reversal_law_census",
     "bare_vs_chiral_right_only_sha256"): Decl(_A, ""),
    ("srmech.cascade.reversal_law_census", "chiral_flat_sha256"): Decl(_A, ""),
    ("srmech.cascade.reversal_law_census", "chiral_sha256"): Decl(_A, ""),
    ("srmech.cascade.reversal_law_census", "half_inversion_sha256"): Decl(_A, ""),

    # ── introspect ────────────────────────────────────────────────────────
    ("srmech.introspect.op_provenance.carry",
     "provenance.chain_sha256"): Decl(_A, "addresses the recorded CHAIN"),

    # ── groups ────────────────────────────────────────────────────────────
    ("srmech.math.groups.abelianization",
     "quotient.coset_partition_sha256"): Decl(_A, ""),
    ("srmech.math.groups.cayley_graph", "edges_sha256"): Decl(_A, ""),
    ("srmech.math.groups.character_table", "cayley_sha256"): Decl(_O, _OPERAND_WHY),
    ("srmech.math.groups.character_table", "table_sha256"): Decl(_A, ""),
    ("srmech.math.groups.conjugacy_classes",
     "class_partition_sha256"): Decl(_A, ""),
    ("srmech.math.groups.derived_subgroup", "elements_sha256"): Decl(_A, ""),
    ("srmech.math.groups.direct_sum_representation",
     "cayley_sha256"): Decl(_O, _OPERAND_WHY),
    ("srmech.math.groups.direct_sum_representation",
     "matrices_sha256"): Decl(
        _A, "addresses the NEW matrices — the reason a name-match cannot "
            "infer 'echo' from a shared field name"),
    ("srmech.math.groups.intertwiner_space", "basis_sha256"): Decl(_A, ""),
    ("srmech.math.groups.intertwiner_space",
     "cayley_sha256"): Decl(_O, _OPERAND_WHY),
    ("srmech.math.groups.permutation_representation",
     "cayley_sha256"): Decl(_O, _OPERAND_WHY),
    ("srmech.math.groups.permutation_representation",
     "matrices_sha256"): Decl(_A, ""),
    ("srmech.math.groups.quotient_group",
     "coset_partition_sha256"): Decl(_A, ""),
    ("srmech.math.groups.semidirect_product", "table_sha256"): Decl(_A, ""),
    ("srmech.math.groups.tensor_product_representation",
     "cayley_sha256"): Decl(_O, _OPERAND_WHY),
    ("srmech.math.groups.tensor_product_representation",
     "matrices_sha256"): Decl(
        _A, "addresses the NEW matrices, as for direct_sum"),

    # ── laplacian / weight lattice ────────────────────────────────────────
    ("srmech.math.laplacian.cyclic_laplacian_spectrum",
     "procedure_sha256"): Decl(_P, _PROC_WHY),
    ("srmech.math.laplacian.cyclic_laplacian_spectrum",
     "spectrum_sha256"): Decl(_A, ""),
    ("srmech.math.weight_lattice.affine_fusion_multiplicities",
     "fusion_sha256"): Decl(_A, ""),
    ("srmech.math.weight_lattice.affine_fusion_multiplicities",
     "procedure_sha256"): Decl(_P, _PROC_WHY),
    ("srmech.math.weight_lattice.affine_modular_s_matrix",
     "procedure_sha256"): Decl(_P, _PROC_WHY),
    ("srmech.math.weight_lattice.affine_modular_s_matrix",
     "s_sha256"): Decl(_A, ""),
    ("srmech.math.weight_lattice.alcove_fold",
     "procedure_sha256"): Decl(_P, _PROC_WHY),
    ("srmech.math.weight_lattice.dominant_weight",
     "label_sha256"): Decl(_A, ""),
    ("srmech.math.weight_lattice.dominant_weight",
     "procedure_sha256"): Decl(_P, _PROC_WHY),
    ("srmech.math.weight_lattice.integrable_weights",
     "procedure_sha256"): Decl(_P, _PROC_WHY),
    ("srmech.math.weight_lattice.integrable_weights",
     "weights_sha256"): Decl(_A, ""),
    ("srmech.math.weight_lattice.tensor_product_multiplicities",
     "fusion_sha256"): Decl(_A, ""),
    ("srmech.math.weight_lattice.tensor_product_multiplicities",
     "procedure_sha256"): Decl(_P, _PROC_WHY),
    ("srmech.math.weight_lattice.verlinde_fusion_multiplicities",
     "fusion_sha256"): Decl(_A, ""),
    ("srmech.math.weight_lattice.verlinde_fusion_multiplicities",
     "procedure_sha256"): Decl(_P, _PROC_WHY),
    ("srmech.math.weight_lattice.weight_multiplicities",
     "procedure_sha256"): Decl(_P, _PROC_WHY),
    ("srmech.math.weight_lattice.weight_multiplicities",
     "weights_sha256"): Decl(_A, ""),

    # ── so8 ───────────────────────────────────────────────────────────────
    ("srmech.physics.qm.so8.an_embedding",
     "attestation.attestation.response_sha256"): Decl(
        _N, "the shipped MPR attestation of arXiv:math/0105155",
        pinned=_BAEZ_OCTONIONS_MPR),
    ("srmech.physics.qm.so8.quaternion_subalgebra_stabilizer",
     "attestation.attestation.response_sha256"): Decl(
        _N, "the same citation as an_embedding — MEASURED equal, which is why "
            "both are pinned to one literal rather than to each other",
        pinned=_BAEZ_OCTONIONS_MPR),
    ("srmech.physics.qm.so8.g2_membership", "frame_sha256"): Decl(
        _E, "IS epq_frame_address() — the E_pq frame the commutators are read "
            "in, shared by every op that reads in it",
        echo_source="srmech.physics.qm.so8.epq_frame_address"),
    ("srmech.physics.qm.so8.g2_membership", "operator_sha256"): Decl(_A, ""),
    ("srmech.physics.qm.so8.g2_membership", "table_sha256"): Decl(
        _E, "IS the octonion table attestation's response_sha256",
        echo_source="srmech.physics.qm.octonion.octonion_table_attestation"
                    "|attestation.response_sha256"),
}


# ══════════════════════════════════════════════════════════════════════════
# THE PERTURBATION CORPUS — BUILT from the shipped constructors, never inlined.
# ══════════════════════════════════════════════════════════════════════════

_CORPUS: Optional[Dict[str, Any]] = None


def corpus() -> Dict[str, Any]:
    """Typed fixtures, constructed by the shipped ops at first use.

    A literal table here would be a COPY of the object under test, which is
    the failure mode the whole module exists to remove. Measured reach of the
    two perturbation styles over the 55 declared pairs: a scalar-only bump
    (``n + 1``, flip a bool) moves **10**; adding real group tables moves
    **29**; the typed operands below (rep payloads, an 8×8 orthogonal, a
    provenance chain) take the movable set to its full extent.
    """
    global _CORPUS
    if _CORPUS is None:
        from srmech.cascade import dihedral_group, unit_loop
        from srmech.math.groups import cyclic_group, permutation_representation
        c = {f"C{n}": cyclic_group(n)["cayley_table"] for n in (2, 3, 4, 5)}
        c["D4"] = dihedral_group(4, "rotation_first")["cayley_table"]
        c["Q8"] = unit_loop(4)["cayley_table"]
        c["C4_REGULAR"] = permutation_representation(c["C4"], c["C4"])
        c["I8"] = [[1 if i == j else 0 for j in range(8)] for i in range(8)]
        _CORPUS = c
    return _CORPUS


def alternate_args(op: str) -> Optional[Dict[str, Any]]:
    """The kwargs OVERRIDE that perturbs ``op``'s input, or ``None``.

    Declared per op because a generic bump does not reach a typed operand: a
    rep payload, a valid normal subgroup and an orthogonal 8×8 all have to be
    constructed, not incremented.
    """
    c = corpus()
    table = {
        "srmech.amsc.catalog.get_attested_dataset": {"offset": 1, "limit": 1},
        "srmech.cascade.anti_automorphism_witnesses": {"cayley_table": c["Q8"]},
        "srmech.cascade.conjugacy_census": {"cayley_table": c["Q8"]},
        "srmech.cascade.finite_semiflow": {"table": [0, 0, 1, 1, 2, 2, 3, 3]},
        "srmech.cascade.reversal_law_census": {"cayley_table": c["D4"]},
        "srmech.introspect.op_provenance.carry": {
            "op": "srmech.math.rational.sin_series_truncate",
            "inputs": {"numerator": 1, "denominator": 2},
            "params": {"num_terms": 6}},
        "srmech.math.groups.abelianization": {"cayley_table": c["Q8"]},
        "srmech.math.groups.cayley_graph": {"cayley_table": c["Q8"]},
        "srmech.math.groups.character_table": {"cayley_table": c["Q8"]},
        "srmech.math.groups.conjugacy_classes": {"cayley_table": c["Q8"]},
        "srmech.math.groups.derived_subgroup": {"cayley_table": c["Q8"]},
        "srmech.math.groups.direct_sum_representation": {
            "rep1": c["C4_REGULAR"], "rep2": c["C4_REGULAR"]},
        "srmech.math.groups.intertwiner_space": {
            "rep1": c["C4_REGULAR"], "rep2": c["C4_REGULAR"]},
        "srmech.math.groups.permutation_representation": {
            "cayley_table": c["C4"], "action": c["C4"]},
        "srmech.math.groups.quotient_group": {
            "cayley_table": c["C4"], "normal_elements": [0, 2]},
        "srmech.math.groups.semidirect_product": {
            "n_table": c["C5"], "h_table": c["C2"],
            "action": [[0, 1, 2, 3, 4], [0, 4, 3, 2, 1]]},
        "srmech.math.groups.tensor_product_representation": {
            "rep1": c["C4_REGULAR"], "rep2": c["C4_REGULAR"]},
        "srmech.math.laplacian.cyclic_laplacian_spectrum": {"n": 7},
        "srmech.math.weight_lattice.affine_fusion_multiplicities": {"level": 3},
        "srmech.math.weight_lattice.affine_modular_s_matrix": {"level": 3},
        "srmech.math.weight_lattice.alcove_fold": {"weight": [3, 1]},
        "srmech.math.weight_lattice.dominant_weight": {"p": 2, "q": 1},
        "srmech.math.weight_lattice.integrable_weights": {"level": 3},
        "srmech.math.weight_lattice.tensor_product_multiplicities": {
            "a": [2, 0]},
        "srmech.math.weight_lattice.verlinde_fusion_multiplicities": {
            "level": 3},
        "srmech.math.weight_lattice.weight_multiplicities": {"p": 2, "q": 0},
        "srmech.physics.qm.so8.an_embedding": {"imaginary_unit": 2},
        "srmech.physics.qm.so8.g2_membership": {"matrix": c["I8"]},
        "srmech.physics.qm.so8.quaternion_subalgebra_stabilizer": {
            "quaternion_index": 2},
    }
    return table.get(op)


# ══════════════════════════════════════════════════════════════════════════
# DRIVING + WALKING
# ══════════════════════════════════════════════════════════════════════════

_DIGEST_KEY = re.compile(r"^[a-z0-9_]*sha256$")
_CACHE: Dict[Tuple[str, str], Any] = {}


def digest_paths(value: Any, prefix: str = "") -> Iterable[Tuple[str, str]]:
    """``(dotted path, digest)`` for every ``*sha256`` string leaf.

    List indices collapse to ``[]`` — the declaration is about the FIELD, and
    a per-index path would make the drain direction depend on how many rows a
    catalog happened to return.
    """
    if isinstance(value, dict):
        for key, sub in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(sub, str) and _DIGEST_KEY.match(str(key)):
                yield path, sub
            else:
                yield from digest_paths(sub, path)
    elif isinstance(value, (list, tuple)):
        for i, sub in enumerate(value):
            if i > 3:          # bounded: a catalog row set can be long
                break
            yield from digest_paths(sub, f"{prefix}[]")


def digest_map(value: Any) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for path, digest in digest_paths(value):
        out.setdefault(path, digest)
    return out


def ledger_args(op: str) -> Optional[Dict[str, Any]]:
    row = _ea.load_ledger().get(op)
    if not row or row.get("status") != "ok":
        return None
    args = row.get("args")
    return dict(args) if isinstance(args, dict) else None


def drivable_ops() -> List[str]:
    """Every op the example-args ledger can drive, in name order."""
    out = []
    for op, row in _ea.load_ledger().items():
        if row.get("status") == "ok" and isinstance(row.get("args"), dict):
            if _ea.resolve(op) is not None:
                out.append(op)
    return sorted(out)


def call(op: str, args: Dict[str, Any]) -> Any:
    """Drive ``op``; results are memoised per (op, canonical args)."""
    key = (op, json.dumps(args, sort_keys=True, default=repr))
    if key not in _CACHE:
        res = _ea.resolve(op)
        if res is None:
            raise LookupError(op)
        _CACHE[key] = res[2](**args)
    return _CACHE[key]


def emitted_over_drivable() -> Set[Tuple[str, str]]:
    """Every ``(op, path)`` that a drivable op ACTUALLY emits.

    This is the discovery half, and it is what makes the declaration a DRAIN
    rather than a ratchet: an op that starts emitting a digest is red until it
    is declared, without anyone remembering to write a gate. Measured marginal
    cost of scanning all drivable ops rather than only the declared ones: the
    389 non-emitting ops add ~10 s, because the expensive term is one op's
    ``lru_cache``d companion solve which the declared set pays anyway.
    """
    found: Set[Tuple[str, str]] = set()
    for op in drivable_ops():
        args = ledger_args(op)
        if args is None:
            continue
        try:
            out = call(op, args)
        except Exception:  # noqa: BLE001 - an op that raises emits nothing
            continue
        for path in digest_map(out):
            found.add((op, path))
    return found


def declared_paths() -> Set[Tuple[str, str]]:
    return set(DECLARATIONS)


def declared_ops() -> Set[str]:
    return {op for op, _p in DECLARATIONS}


# ══════════════════════════════════════════════════════════════════════════
# THE CLASSIFIER — a pure function over three measured booleans, so it can be
# unit-tested on synthetic counts. A classifier that always answers one
# verdict cannot ship past `test_the_classifier_itself_distinguishes`.
# ══════════════════════════════════════════════════════════════════════════

def classify(field_stable: bool, field_moved: bool, answer_moved: bool) -> str:
    """The verdict for one (op, field) from three measurements.

    ``field_stable``  — same digest on a repeated call with identical args.
    ``field_moved``   — digest differs under the declared perturbation.
    ``answer_moved``  — the op's non-digest RESULT differs under it.
    """
    if not field_stable:
        return "unstable"
    if field_moved:
        return "distinguishing"
    if answer_moved:
        return "constant_under_a_moved_answer"
    return "vacuous"


# ══════════════════════════════════════════════════════════════════════════
# THE FIVE EXECUTORS. One per kind, named, and mechanically bound below.
# Each returns ``(ok, detail)``.
# ══════════════════════════════════════════════════════════════════════════

def _strip_digests(value: Any) -> Any:
    """``value`` with every ``*sha256`` leaf removed — the ANSWER alone."""
    if isinstance(value, dict):
        return {k: _strip_digests(v) for k, v in value.items()
                if not (isinstance(v, str) and _DIGEST_KEY.match(str(k)))}
    if isinstance(value, list):
        return [_strip_digests(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_strip_digests(v) for v in value)
    return value


def _measure(op: str, path: str) -> Dict[str, Any]:
    base_args = ledger_args(op)
    assert base_args is not None, op
    base = call(op, base_args)
    again = _ea.resolve(op)[2](**base_args)      # a genuinely fresh call
    base_map, again_map = digest_map(base), digest_map(again)
    out: Dict[str, Any] = {
        "value": base_map.get(path),
        "field_stable": base_map.get(path) == again_map.get(path),
        "field_moved": False,
        "answer_moved": False,
        "perturbed": None,
    }
    alt = alternate_args(op)
    if alt is not None:
        args = dict(base_args)
        args.update(alt)
        try:
            other = call(op, args)
        except Exception as exc:  # noqa: BLE001
            out["error"] = f"{type(exc).__name__}: {exc}"
            return out
        other_map = digest_map(other)
        out["perturbed"] = other_map.get(path)
        out["field_moved"] = (other_map.get(path) is not None
                              and other_map.get(path) != base_map.get(path))
        out["answer_moved"] = (json.dumps(_strip_digests(other), sort_keys=True,
                                          default=repr)
                               != json.dumps(_strip_digests(base),
                                             sort_keys=True, default=repr))
    return out


def _hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and \
        all(ch in "0123456789abcdef" for ch in value)


def execute_answer(op: str, path: str, decl: Decl) -> Tuple[bool, str]:
    m = _measure(op, path)
    if not _hex64(m["value"]):
        return False, f"{op}.{path}: not a 64-hex digest: {m['value']!r}"
    if not m["field_stable"]:
        return False, f"{op}.{path}: kind 'answer' must be STABLE across calls"
    if decl.empty_ok:
        return True, f"{op}.{path}: EMPTY_OK — {decl.why[:40]}"
    verdict = classify(m["field_stable"], m["field_moved"], m["answer_moved"])
    if verdict != "distinguishing":
        return False, (f"{op}.{path}: kind 'answer' must MOVE when the answer "
                       f"moves; verdict {verdict}, perturbed={m['perturbed']}")
    return True, f"{op}.{path}: answer, distinguishing"


def execute_operand(op: str, path: str, decl: Decl) -> Tuple[bool, str]:
    m = _measure(op, path)
    if not _hex64(m["value"]):
        return False, f"{op}.{path}: not a 64-hex digest"
    if not m["field_stable"]:
        return False, f"{op}.{path}: kind 'operand' must be STABLE"
    if not m["field_moved"]:
        return False, (f"{op}.{path}: kind 'operand' must MOVE when the "
                       f"OPERAND moves; the declared perturbation replaces it")
    return True, f"{op}.{path}: operand, moves with its operand"


def execute_procedure(op: str, path: str, decl: Decl) -> Tuple[bool, str]:
    m = _measure(op, path)
    if not _hex64(m["value"]):
        return False, f"{op}.{path}: not a 64-hex digest"
    if not m["field_stable"]:
        return False, f"{op}.{path}: kind 'procedure' must be STABLE"
    if m["field_moved"]:
        return False, (f"{op}.{path}: kind 'procedure' addresses the RULE and "
                       f"must NOT move with the input; it moved to "
                       f"{m['perturbed']}")
    if not m["answer_moved"]:
        return False, (f"{op}.{path}: VACUOUS — the field held constant but so "
                       f"did the answer, so nothing was tested. The "
                       f"perturbation for {op} must change the result.")
    return True, f"{op}.{path}: procedure, constant under a MOVED answer"


def execute_echo(op: str, path: str, decl: Decl) -> Tuple[bool, str]:
    import importlib
    src, _, sub = (decl.echo_source or "").partition("|")
    mod_name, _, fname = src.rpartition(".")
    value = getattr(importlib.import_module(mod_name), fname)()
    for step in [s for s in sub.split(".") if s]:
        value = value[step]
    m = _measure(op, path)
    if m["value"] != value:
        return False, (f"{op}.{path}: kind 'echo' must equal {decl.echo_source}"
                       f" — got {m['value']}, source says {value}")
    if m["field_moved"]:
        return False, (f"{op}.{path}: an echo of a fixed surface must not move "
                       f"with the op's input")
    return True, f"{op}.{path}: echo of {decl.echo_source}"


def execute_pinned(op: str, path: str, decl: Decl) -> Tuple[bool, str]:
    m = _measure(op, path)
    if not _hex64(decl.pinned):
        return False, f"{op}.{path}: the PIN itself is not a 64-hex digest"
    if m["value"] != decl.pinned:
        return False, (f"{op}.{path}: kind 'pinned' moved — declared "
                       f"{decl.pinned}, emitted {m['value']}. A shipped "
                       f"attestation constant changed.")
    if m["field_moved"]:
        return False, f"{op}.{path}: a pinned constant must not vary with input"
    return True, f"{op}.{path}: pinned"


#: kind -> the NAMED function that executes it. The gate asserts this covers
#: KINDS exactly, which is what stops the vocabulary becoming a second
#: aspirational taxonomy: the precedent gate in this tree prints "N of M
#: strings are of an EXECUTABLE kind — NONE is executed yet."
EXECUTED_BY = {
    "answer": execute_answer,
    "operand": execute_operand,
    "procedure": execute_procedure,
    "echo": execute_echo,
    "pinned": execute_pinned,
}


def execute_all() -> List[Tuple[Tuple[str, str], bool, str]]:
    out = []
    for (op, path), decl in sorted(DECLARATIONS.items()):
        ok, detail = EXECUTED_BY[decl.kind](op, path, decl)
        out.append(((op, path), ok, detail))
    return out


# ══════════════════════════════════════════════════════════════════════════
# THE LEXICAL SCAN — the second instrument, and it is NOT redundant.
#
# Driving finds fields the EMITTED PROSE does not mention; the scan finds
# fields the prose PROMISES that the ledger cannot drive. Measured at rc462:
# `triality_frame_action` promises `action_sha256` / `frame_sha256` /
# `procedure_sha256` and is not drivable, so only the scan sees it.
# ══════════════════════════════════════════════════════════════════════════

_LEX = re.compile(r"([a-z0-9_]+_sha256)")

#: Field names that belong to the MPR ATTESTATION BLOCK, not to an op's own
#: payload. Every attested op's prose describes them; they are the schema, not
#: a per-op content address.
ATTESTATION_FIELDS = frozenset({
    "response_sha256", "upstream_response_sha256", "srmech_sha256",
})


def lexical_mentions() -> Dict[str, List[str]]:
    """``{op: [field names promised in its RETURNS prose]}``.

    Scoped to ``returns`` — the payload contract — not the whole ToolEntry.
    Whole-blob scanning finds 115 ops and is dominated by every attested op
    describing the MPR attestation schema, which is not a per-op address.
    """
    from srmech.introspect.tool_schema import get_tool_schema
    out: Dict[str, List[str]] = {}
    for tool in get_tool_schema().tools:
        blob = json.dumps(tool.to_jsonable().get("returns", ""),
                          ensure_ascii=False)
        names = sorted(set(_LEX.findall(blob)) - ATTESTATION_FIELDS)
        if names:
            out[tool.name] = names
    return out


def undeclared_lexical() -> List[str]:
    """Ops that PROMISE a content address in emitted prose and declare none."""
    have = declared_ops()
    return sorted(op for op in lexical_mentions() if op not in have)
