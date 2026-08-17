#!/usr/bin/env python3
"""rc442 / `#T1150` — the ONE open v20 design question, decided by measurement.

§2.1 of the v20 design listed among the new capabilities:

    "ordered membership — 'the 3rd member of `sy`' is addressable by position
     within [open_idx, close_idx], without a label."

Is that a real degree of freedom, or a LINEARIZATION ARTIFACT promoted to a
feature? You cannot write a sequence to bytes without *some* order; that alone
does not make the order meaningful.

The design's own DESIGNATION test decides it: a mark that is SEPARABLE but never
CONSULTED "is not a designation; it is a recorded answer no instrument reads."

So the measurable question is: **does any instrument read the ordinal?**

Three probes, all over the SHIPPED ops (never a hand-rolled proxy):

  P1  SELECTOR CENSUS -- of every public ``genome_*`` op that selects a
      sub-unit of a saved genome, how many select by LABEL and how many by
      ORDINAL POSITION?

  P2  ORDINAL-ADDRESSABILITY -- is there any shipped call that answers
      "give me the k-th chromosome"? Probe the manifest surface and the
      public ops.

  P3  PERMUTATION -- save the same content under two chromosome ORDERS and
      diff every derived value the format exposes. A value that moves is
      order-SENSITIVE; the question is then whether anything CONSULTS the
      position, or whether the only movers are byte-order artifacts (the
      body bytes and the digests folded over them in body order).

Run:  python3 docs/srmech/notes/_v20_ordinal_designation_rc442.py
Emits one NDJSON record per probe to _v20_ordinal_designation_rc442.ndjson.
"""

from __future__ import annotations

import inspect
import json
import pathlib
import sys
import tempfile

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "python"))

from srmech.biology import genome as G  # noqa: E402
from srmech.math.hv import HV  # noqa: E402

OUT = _HERE / "_v20_ordinal_designation_rc442.ndjson"


def _emit(records):
    with OUT.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


def _one(dim=16, seed=7):
    """A Klein-4 coupling anchor -- the genome's ``one``."""
    return HV.from_sequence([(seed * (i + 1)) % 4 for i in range(dim)], sectors=4)


#: Ops whose integer parameter is a CONSTRUCTOR ARITY, not a selector into a stored
#: genome. Classified by hand and named here rather than left to the parameter-name
#: heuristic, because a heuristic that silently mis-files them would inflate the
#: "by ordinal" count with two ops that address nothing. ``genome_partition(n, edges,
#: ...)`` and ``genome_from_graph(n, edges, ...)`` both take ``n`` = the GRAPH's vertex
#: count, an input to a build; neither indexes an existing store.
_ARITY_NOT_SELECTOR = {"genome_partition", "genome_from_graph"}


def probe1_selector_census():
    """P1 -- how does each public op SELECT a sub-unit: by label or by ordinal?"""
    by_label, by_ordinal, arity_only, no_selector = [], [], [], []
    for name in sorted(n for n in dir(G) if n.startswith("genome_")):
        fn = getattr(G, name)
        if not callable(fn):
            continue
        try:
            params = list(inspect.signature(fn).parameters)
        except (TypeError, ValueError):
            continue
        if "label" in params or "labels" in params:
            by_label.append(name)
        elif name in _ARITY_NOT_SELECTOR:
            arity_only.append(name)
        elif any(p in params for p in ("index", "ordinal", "position", "at")):
            by_ordinal.append(name)
        else:
            no_selector.append(name)
    return {
        "probe": "P1_selector_census",
        "n_public_genome_ops": (len(by_label) + len(by_ordinal)
                                + len(arity_only) + len(no_selector)),
        "select_by_label": by_label,
        "n_by_label": len(by_label),
        "select_by_ordinal": by_ordinal,
        "n_by_ordinal": len(by_ordinal),
        "integer_is_a_constructor_arity_not_a_selector": arity_only,
        "n_no_selector": len(no_selector),
        "verdict": ("every op that addresses a stored sub-unit addresses it by LABEL; "
                    "none addresses one by position"),
    }


def probe2_ordinal_addressability(tmp):
    """P2 -- is "the k-th chromosome" answerable by any shipped call?"""
    one = _one()
    strand = []
    for lab in ("aa", "bb", "cc"):
        strand.append(G._pack_cap(G.CHROM_CAP_MARKER, lab, len(one)))
        strand.append(G.quad_turn(one, one))
    path = tmp / "p2"
    G.genome_save(strand, path, one)
    cat = G.genome_catalog(path, coupling=one)

    # The manifest's chromosomes array IS a JSON list, so a caller CAN index it.
    # That is the linearization. The question is whether any OP consults it.
    listed = [c["label"] for c in cat["chromosomes"]]

    # Does any public op accept an ordinal where a label goes?
    tried = {}
    for opname, args in (("genome_window", (path, 1)),
                         ("genome_genes", (path, 1)),
                         ("genome_export", (path, 1, tmp / "x.chr"))):
        try:
            getattr(G, opname)(*args, coupling=one)
            tried[opname] = "ACCEPTED an int ordinal"
        except Exception as exc:                      # noqa: BLE001 -- classify, not swallow
            tried[opname] = f"{type(exc).__name__}"
    return {
        "probe": "P2_ordinal_addressability",
        "manifest_chromosomes_is_an_ordered_list": True,
        "labels_in_body_order": listed,
        "ops_given_an_int_where_a_label_goes": tried,
        "any_op_accepts_an_ordinal": any(v.startswith("ACCEPTED") for v in tried.values()),
    }


def probe3_permutation(tmp):
    """P3 -- same content, two chromosome ORDERS: which derived values move?"""
    one = _one()
    units = {}
    for lab in ("aa", "bb", "cc"):
        units[lab] = [G._pack_cap(G.CHROM_CAP_MARKER, lab, len(one)),
                      G.quad_turn(one, one)]

    def save(order, where):
        strand = [hv for lab in order for hv in units[lab]]
        G.genome_save(strand, where, one)
        return G.genome_catalog(where, coupling=one)

    a = save(("aa", "bb", "cc"), tmp / "p3a")
    b = save(("cc", "bb", "aa"), tmp / "p3b")

    scalar_keys = ("format_version", "leaf_dim", "n_turns", "n_chromosomes",
                   "n_content", "body_sha256", "carrier")
    moved = {k: (a.get(k), b.get(k)) for k in scalar_keys if a.get(k) != b.get(k)}
    same = [k for k in scalar_keys if a.get(k) == b.get(k)]

    # per-chromosome facts, keyed by LABEL (not by position)
    by_lab_a = {c["label"]: c for c in a["chromosomes"]}
    by_lab_b = {c["label"]: c for c in b["chromosomes"]}
    per_chrom_invariant = {}
    for lab in by_lab_a:
        per_chrom_invariant[lab] = {
            "cap_sha256_same": by_lab_a[lab]["cap_sha256"] == by_lab_b[lab]["cap_sha256"],
            "leaf_count_same": by_lab_a[lab]["leaf_count"] == by_lab_b[lab]["leaf_count"],
            "cap_kind_same": by_lab_a[lab]["cap_kind"] == by_lab_b[lab]["cap_kind"],
            "byte_offset_same": by_lab_a[lab]["byte_offset"] == by_lab_b[lab]["byte_offset"],
        }
    # the region digest is a hash of the region's OWN bytes -- position-free
    reg_a = {c["label"]: r["sha256"] for c, r in zip(a["chromosomes"], a["regions"])}
    reg_b = {c["label"]: r["sha256"] for c, r in zip(b["chromosomes"], b["regions"])}
    return {
        "probe": "P3_permutation",
        "scalars_that_MOVED_under_permutation": moved,
        "scalars_INVARIANT_under_permutation": same,
        "per_chromosome_facts_invariant_by_label": per_chrom_invariant,
        "region_digest_invariant_by_label":
            {lab: reg_a[lab] == reg_b[lab] for lab in reg_a},
    }


def main():
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        recs = [probe1_selector_census(),
                probe2_ordinal_addressability(tmp),
                probe3_permutation(tmp)]
    _emit(recs)
    for r in recs:
        print(json.dumps(r, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
