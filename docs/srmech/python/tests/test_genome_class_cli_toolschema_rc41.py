"""v0.7.5rc41 — CLI + tool_schema/introspect class-awareness (#962 Part 2).

Closes the genome surface: `srmech class list` / `srmech class describe NAME`
(the CLI discovery face), `introspect.describe()["classes"]` (the package
recognises its own user-class surface), and 2 ToolEntries
(`srmech.dsl.list_class_surface` / `describe_class`) so the LLM tool list
includes class discovery.
"""
from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from srmech import introspect
from srmech.amsc.tool_schema import get_tool_schema
from srmech.cli.main import main as cli_main


# ── CLI: srmech class list / describe ────────────────────────────────────────

def test_cli_class_list_shows_genome():
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["class", "list"])
    out = buf.getvalue()
    assert rc == 0
    assert "Genome" in out and "(srmech)" in out


def test_cli_class_describe_is_json():
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["class", "describe", "Genome"])
    assert rc == 0
    d = json.loads(buf.getvalue())          # the describe output is valid JSON
    assert d["name"] == "Genome"
    assert "add_chromosome" in d["methods"]


# ── introspect.describe() gains a "classes" key ──────────────────────────────

def test_describe_has_classes_key():
    d = introspect.describe()
    assert "classes" in d
    assert d["classes"]["total"] >= 1
    assert "Genome" in d["classes"]["names"]
    # the tools.total is the (unchanged-by-classes) tool count — classes are
    # a sibling surface, not tools.
    assert isinstance(d["tools"]["total"], int)


# ── tool_schema: the 2 class-discovery ToolEntries are registered ────────────

def test_class_surface_tools_registered():
    names = {t.name for t in get_tool_schema().tools}
    assert "srmech.dsl.list_class_surface" in names
    assert "srmech.dsl.describe_class" in names


def test_introspect_tools_total_is_276():
    # rc41 registered list_class_surface + describe_class (270→272);
    # rc42 added genome + partition ToolEntries (272→274);
    # rc43 added laplacian.tokenize + cooccurrence_edges (§17 U1; 274→276).
    # rc108 added laplacian.mat_svd (full-SVD Mat foundation; 289→290).
    # F929 router: dispatch.infer ToolEntry (the OPEN/infer meta-dispatcher
    # over the cyclic/spectral/Σ reduction rows; non_compute orchestration,
    # no C peer) — 330→331.
    assert introspect.describe()["tools"]["total"] == 395
