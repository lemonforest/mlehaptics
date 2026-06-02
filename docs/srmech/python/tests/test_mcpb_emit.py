"""Tests for ``srmech mcp emit-mcpb`` — the Claude Desktop .mcpb emitter
(issue #749 / MS #19 / wishlist W13, v0.5.0).

The manifest is built ENTIRELY from srmech introspection: the version is
``srmech.__version__`` (asserted NOT-frozen), the tool list is the
ADVERTISED ``tool_entries_to_mcp_defs()`` surface (asserted equal to that
iterator, not a 174 literal), and the ``.mcpb`` is a stdlib-``zipfile``
ZIP whose root carries ``manifest.json``. server.type defaults to the
spec-valid ``"uv"``; ``"python"`` is a ``user_config``-gated fallback with
NO baked interpreter path.
"""

import json
import sys
import zipfile
from pathlib import Path

import srmech
from srmech.amsc.tool_schema import get_tool_schema
from srmech.cli.main import main as cli_main
from srmech.mcp._mcpb import build_manifest, pack_mcpb
from srmech.mcp._tools import tool_entries_to_mcp_defs

# anthropics/mcpb REQUIRED top-level fields (verified against MANIFEST.md).
_REQUIRED = {
    "manifest_version",
    "name",
    "version",
    "description",
    "author",
    "server",
}


def test_manifest_has_all_required_fields():
    m = build_manifest()
    assert _REQUIRED <= set(m)
    assert isinstance(m["author"], dict) and m["author"].get("name")
    assert m["server"]["type"] == "uv"
    assert m["server"]["entry_point"] == "server/main.py"
    assert "mcp_config" not in m["server"]  # uv omits it


def test_version_is_derived_not_frozen():
    # No literal rc string in this file — the version flows from the
    # package attribute on both the top-level field and the attestation.
    assert build_manifest()["version"] == srmech.__version__
    assert build_manifest()["attestation"]["srmech_version"] == srmech.__version__


def test_tool_list_matches_advertised_introspection():
    m = build_manifest()
    names_manifest = {t["name"] for t in m["tools"]}
    names_adv = {d["name"] for d in tool_entries_to_mcp_defs()}
    assert names_manifest == names_adv
    assert len(m["tools"]) == len(names_adv)
    assert m["tools_generated"] is False


def test_default_type_is_spec_valid_uv():
    assert build_manifest()["server"]["type"] in {
        "node",
        "python",
        "binary",
        "uv",
    }
    assert build_manifest(server_type="uv")["server"] == build_manifest()["server"]


def test_python_fallback_carries_user_config_path():
    m = build_manifest(server_type="python")
    assert m["server"]["type"] == "python"
    assert m["server"]["mcp_config"]["command"] == "${user_config.python_path}"
    assert "-m" in m["server"]["mcp_config"]["args"]
    assert "srmech.mcp._cli" in m["server"]["mcp_config"]["args"]
    assert m["user_config"]["python_path"]["required"] is True
    assert m["user_config"]["python_path"]["type"] == "string"


def test_no_baked_interpreter_path():
    # The emitter's own python path must NOT leak into the bundle (issue
    # #749 portability bug — the .mcpb installs on a different machine).
    blob = json.dumps(build_manifest(server_type="python"))
    assert sys.executable not in blob


def test_attestation_block():
    a = build_manifest()["attestation"]
    assert a["srmech_version"] == srmech.__version__
    h = a["tool_schema_sha256"]
    assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)
    assert a["tool_count"] == len(list(tool_entries_to_mcp_defs()))
    assert a["mpr_version"] == "1.0"


def test_pack_mcpb_is_valid_zip_with_root_manifest(tmp_path):
    p = pack_mcpb(str(tmp_path))
    assert p.is_absolute() and p.exists() and p.suffix == ".mcpb"
    assert zipfile.is_zipfile(p)
    with zipfile.ZipFile(p) as zf:
        nl = zf.namelist()
        assert "manifest.json" in nl
        assert "server/main.py" in nl
        assert "pyproject.toml" in nl
        m = json.loads(zf.read("manifest.json"))
        assert m["version"] == srmech.__version__
        py = zf.read("pyproject.toml").decode()
        assert f"srmech=={srmech.__version__}" in py


def test_manifest_only_writes_only_manifest(tmp_path):
    p = pack_mcpb(str(tmp_path), manifest_only=True)
    assert p.name == "manifest.json" and p.is_absolute()
    assert not (tmp_path / "srmech.mcpb").exists()


def test_filter_narrows_tool_list(tmp_path):
    from srmech.mcp._tools import compile_filter

    m = build_manifest(name_filter=compile_filter("srmech.amsc.cyclic.*"))
    names = {t["name"] for t in m["tools"]}
    assert names and all(n.startswith("srmech.amsc.cyclic.") for n in names)
    assert len(names) < len(list(tool_entries_to_mcp_defs()))


def test_cli_emit_manifest_only_smoke(tmp_path, capsys):
    rc = cli_main(
        ["mcp", "emit-mcpb", "--manifest-only", "--out", str(tmp_path)]
    )
    assert rc == 0
    out = capsys.readouterr().out.strip()
    printed = Path(out)
    assert printed.exists() and printed.name == "manifest.json"
    assert json.loads(printed.read_text())["version"] == srmech.__version__


def test_cli_emit_full_bundle_smoke(tmp_path, capsys):
    rc = cli_main(["mcp", "emit-mcpb", "--out", str(tmp_path)])
    assert rc == 0
    printed = Path(capsys.readouterr().out.strip())
    assert printed.suffix == ".mcpb" and zipfile.is_zipfile(printed)
