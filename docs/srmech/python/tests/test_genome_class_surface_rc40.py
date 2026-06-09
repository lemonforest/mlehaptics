"""v0.7.5rc40 — DSL class-awareness: one-shot introspect + run for user classes.

`describe_class` / `list_class_surface` give a JSON-able view of a user-declared
`[class]` (the rc39 CatalogClass); `run_class_method` is the stateless one-shot
(construct from `fields`, invoke `method` with `args`, return result + post-call
state). These are the surface the CLI + tool_schema/MCP (rc41) compose on.
"""
from __future__ import annotations

import json

import pytest

from srmech.amsc.hdc import klein4_random
from srmech.dsl import describe_class, list_class_surface, run_class_method


def test_describe_class_shape_is_jsonable():
    d = describe_class("Genome")
    assert d["name"] == "Genome" and d["provenance"] == "srmech"
    assert set(d["fields"]) == {"the_one", "chromosomes"}
    assert {"shape", "cap", "add_chromosome", "recall"} <= set(d["methods"])
    m = d["methods"]["add_chromosome"]
    assert m["op"] == "srmech.amsc.genome.chromosome"
    assert m["binds"] == ["leaves", "the_one"] and m["appends"] == "chromosomes"
    json.dumps(d)                                   # fully JSON-serialisable


def test_list_class_surface_includes_seed():
    names = [c["name"] for c in list_class_surface()]
    assert "Genome" in names
    json.dumps(list_class_surface())                # JSON-able for the LLM/CLI surface


def test_run_class_method_shape_op():
    out = run_class_method("Genome", "shape",
                           fields={"the_one": klein4_random(64, seed=1)},
                           args={"n": 5000})
    assert out["class"] == "Genome" and out["method"] == "shape"
    assert out["result"]["shape"] == "quad_strand" and out["result"]["depth"] == 3


def test_run_class_method_threads_state_and_round_trips():
    one = klein4_random(64, seed=5)
    leaves = [klein4_random(64, seed=s) for s in range(4)]
    # one-shot add: the post-call `fields` shows the appended chromosome
    added = run_class_method("Genome", "add_chromosome",
                             fields={"the_one": one},
                             args={"leaves": leaves, "label": "astronomy"})
    strand = added["result"]
    assert len(added["fields"]["chromosomes"]) == 1   # appends mutation visible in returned state
    # one-shot recall threads the SAME the_one back in as a field
    cap = run_class_method("Genome", "cap", fields={"the_one": one},
                           args={"label": "astronomy"})["result"]
    back = run_class_method("Genome", "recall",
                            fields={"the_one": one},
                            args={"strand": strand, "telomere": cap})["result"]
    assert [list(x) for x in back] == [list(l) for l in leaves]


def test_run_class_method_unknown_method_raises():
    with pytest.raises(AttributeError):
        run_class_method("Genome", "nope", fields={"the_one": klein4_random(64, seed=1)})
