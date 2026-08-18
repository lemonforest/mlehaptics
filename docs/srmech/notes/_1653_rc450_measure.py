#!/usr/bin/env python3
"""rc450 (`#T1160`, gh #1653) — the MEASUREMENT script behind every number rc450
writes into prose, a gate literal or a ledger row.

Computational-provenance discipline: a figure quoted in shipped text must have
its generating code committed beside it, and the PREDICATE must be stated so a
later reader can reproduce or refute it rather than re-derive it from scratch.

Run from ``docs/srmech/python`` with ``PYTHONPATH=.``::

    PYTHONPATH=. python3 ../notes/_1653_rc450_measure.py

Every section prints its predicate first and its measurement second. Nothing
here asserts; this is an instrument, and its output is the evidence.

⚠️ THE FLAT-WALK TRAP, stated because it has bitten this arc twice. A cascade
step may carry ``body`` (map) or nested ``steps``; a walk that iterates
``chain["steps"]`` without descending sees roughly half the population and
CANNOT tell that from "there is nothing else to see". Both walks are printed
below, side by side, so a number quoted from one can never be mistaken for the
other.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                "..", "python")))

from srmech.dsl import _cascade_chain as _cc          # noqa: E402
from srmech.dsl import _catalog as _cat               # noqa: E402


# ── step-form census ──────────────────────────────────────────────────────────

def _classify(step: dict) -> str:
    """The step FORM, by the same key-presence predicate ``cr_step_form`` uses.

    ``map_over`` -> map, ``fold_op``/``fold_over``/``over`` with a fold class ->
    fold, else plain. Stated rather than assumed: this is the predicate, and a
    different one will give a different census.
    """
    if "map_over" in step:
        return "map"
    if "fold_op" in step or "fold_class" in step:
        return "fold"
    return "plain"


def _walk_recursive(steps, out):
    for st in steps or ():
        out.append(st)
        for key in ("body", "steps"):
            sub = st.get(key)
            if isinstance(sub, list):
                _walk_recursive(sub, out)


def step_census():
    """Returns (flat_counts, recursive_counts, n_descriptors, n_variants)."""
    catalog = _cat.load_catalog()
    names = sorted(n for n, d in catalog.items()
                   if _cc.descriptor_status(d) == "executable")
    flat = {"plain": 0, "map": 0, "fold": 0}
    rec = {"plain": 0, "map": 0, "fold": 0}
    n_variants = 0
    for name in names:
        for entry in _cc._chain_entries(catalog[name]):
            n_variants += 1
            top = entry.get("steps") or []
            for st in top:
                flat[_classify(st)] += 1
            allsteps: list = []
            _walk_recursive(top, allsteps)
            for st in allsteps:
                rec[_classify(st)] += 1
    return flat, rec, len(names), n_variants


# ── the C dispatch table ──────────────────────────────────────────────────────

def c_op_table():
    """The op spellings ``cr_dispatch`` accepts, parsed from CR_OP_REG.

    Predicate: read ``c/src/srmech_compose_run.c``, find the ``CR_OP_REG``
    initialiser, and collect every double-quoted first field. Parsed, not
    grepped — a grep over the whole file also catches the arms' string
    comparisons and over-counts (23 vs 20 in the rc450 preflight).
    """
    path = os.path.join(os.path.dirname(__file__), "..", "c", "src",
                        "srmech_compose_run.c")
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read().replace("\r\n", "\n")
    marker = "CR_OP_REG["
    i = text.find(marker)
    if i < 0:
        return None, None
    decl_end = text.find("\n", i)
    decl = text[i:decl_end]
    # ⚠️ The opening brace of the initialiser is on the DECLARATION line
    # (``} CR_OP_REG[20] = {``), not after it. A first version of this parser
    # searched from ``decl_end`` and so latched onto the FIRST ENTRY's brace,
    # matched its close, and reported ONE op. It was caught only because 1
    # contradicts the ``[20]`` printed one line above it — an instrument whose
    # own declaration disagrees with its own count. Search from ``i``.
    body_start = text.find("{", i)
    depth, j = 0, body_start
    while j < len(text):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                break
        j += 1
    body = text[body_start:j]
    ops = []
    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("{"):
            continue
        q = line.find('"')
        if q < 0:
            continue
        q2 = line.find('"', q + 1)
        ops.append(line[q + 1:q2])
    return decl, sorted(set(ops))


# ── the accepted/rejected split, by EXECUTION ────────────────────────────────

def accepted_split():
    """Import the ratchet's own ``_measure`` so this cannot disagree with it."""
    sys.path.insert(0, os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "python", "tests")))
    import test_c_cascade_parity_ratchet_rc446 as ratchet
    rejected, accepted = ratchet._measure()
    return sorted(accepted), sorted(rejected)


def main() -> int:
    print("=" * 74)
    print("rc450 measurement — gh #1653 / `#T1160`")
    print("=" * 74)

    flat, rec, n_desc, n_var = step_census()
    print("\n[1] STEP-FORM CENSUS over the executable descriptors")
    print("    predicate: key-presence (map_over / fold_op|fold_class / else "
          "plain)")
    print("    population: %d executable descriptors, %d chain variants"
          % (n_desc, n_var))
    print("    FLAT      (chain['steps'] only, NO descent): "
          "plain=%d map=%d fold=%d  total=%d"
          % (flat["plain"], flat["map"], flat["fold"], sum(flat.values())))
    print("    RECURSIVE (descends body/steps)            : "
          "plain=%d map=%d fold=%d  total=%d"
          % (rec["plain"], rec["map"], rec["fold"], sum(rec.values())))

    decl, ops = c_op_table()
    print("\n[2] C DISPATCH TABLE (CR_OP_REG), parsed")
    print("    declaration: %s" % (decl or "<not found>"))
    print("    distinct op spellings: %d" % (len(ops) if ops else 0))
    print("    %s" % (ops,))
    # SELF-CHECK: the declared array length and the parsed entry count must
    # agree. Without this the parser can under-read and still print a number.
    if decl and ops is not None:
        declared = decl[decl.find("[") + 1:decl.find("]")]
        print("    SELF-CHECK declared=%s parsed=%d  %s"
              % (declared, len(ops),
                 "AGREE" if declared.isdigit() and int(declared) == len(ops)
                 else "DISAGREE — the parser is under-reading"))

    acc, rej = accepted_split()
    print("\n[3] srmech_chain_run ACCEPT/REJECT, by execution")
    print("    accepted (%d): %s" % (len(acc), acc))
    print("    rejected (%d): %s" % (len(rej), rej))

    print("\n[4] JSON one-liner (for pasting into a ledger row)")
    print(json.dumps({
        "flat": flat, "recursive": rec,
        "executable_descriptors": n_desc, "chain_variants": n_var,
        "c_op_table": len(ops or []),
        "accepted": len(acc), "rejected": len(rej),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
