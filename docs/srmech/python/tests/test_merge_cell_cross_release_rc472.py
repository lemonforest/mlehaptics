"""rc472 W2 (`#T1188`) — merge_cell's FOURTH carry-forward refusal, red-proven.

Until rc472 ``merge_cell`` carried the OTHER cell's ``measured_at`` forward
with no comparison of either field, so a manifest whose two columns were
measured at two RELEASES could be produced and caught only later by the
version-stamp gate — after the cell's minutes were spent. The refusal is the
release; the interpreter is a printed WARNING, never a refusal (the rc471 arc
measured it non-causal, and asserting it would forbid the cross-interpreter
re-measure that showed so).

The last test is the SEAM rather than the helper: a planted manifest whose
other column carries this tree's three live digests (so the three earlier
refusals stay quiet) and a foreign release, with ``census`` replaced by a
function that fails the test if reached.

numpy-free. No ``abs()``. No ``hashlib``.
"""
import json
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import demotion_probe as _dp  # noqa: E402
import srmech  # noqa: E402

_LIVE_PY = f"{sys.version_info[0]}.{sys.version_info[1]}"


def test_a_column_measured_at_another_release_is_refused():
    with pytest.raises(SystemExit) as ei:
        _dp._refuse_cross_release(
            {"pure": {"srmech_version": "0.0.0", "python": _LIVE_PY}},
            "pure", srmech.__version__, sys.version_info, "x.ndjson")
    msg = str(ei.value)
    assert "REFUSING" in msg and "0.0.0" in msg and srmech.__version__ in msg


def test_the_same_release_is_not_refused_and_does_not_warn(capsys):
    _dp._refuse_cross_release(
        {"pure": {"srmech_version": srmech.__version__, "python": _LIVE_PY}},
        "pure", srmech.__version__, sys.version_info, "x.ndjson")
    assert "WARNING" not in capsys.readouterr().err


def test_an_interpreter_mismatch_warns_and_does_not_refuse(capsys):
    _dp._refuse_cross_release(
        {"pure": {"srmech_version": srmech.__version__, "python": "2.7"}},
        "pure", srmech.__version__, sys.version_info, "x.ndjson")
    err = capsys.readouterr().err
    assert "WARNING" in err and "2.7" in err and "Not a refusal" in err


def test_an_absent_or_unstamped_other_column_is_not_refused(capsys):
    _dp._refuse_cross_release({}, "pure", srmech.__version__,
                              sys.version_info, "x.ndjson")
    _dp._refuse_cross_release({"pure": {}}, "pure", srmech.__version__,
                              sys.version_info, "x.ndjson")
    assert "WARNING" not in capsys.readouterr().err


def test_merge_cell_refuses_a_foreign_release_BEFORE_the_census_runs(
        tmp_path, monkeypatch):
    me = _dp.cell()
    other = [c for c in _dp.CELLS if c != me][0]
    meta = {
        "record": "meta", "cells_measured": [other],
        "registry_signature_sha256": {other: _dp.registry_signature()},
        "reader_signature_sha256": {other: _dp.reader_signature()},
        "probe_signature_sha256": {other: _dp.probe_signature()},
        "measured_at": {other: {"srmech_version": "0.0.0", "python": _LIVE_PY}},
        "n_rows": 1, "n_ops": 1,
        "by_verdict": {other: {"EXACT": 1}}, "undeclared": {other: []},
        "divergent": [],
        "witness": {"P": str(_dp.P), "F": str(_dp.F), "G": str(_dp.G)},
    }
    row = {"op": "pkg.mod.alpha", "param": "xs", "type": "list[float]",
           "base_source": "ledger", other: {"verdict": "EXACT"}}
    p = tmp_path / "demotion_census.ndjson"
    text = (json.dumps(meta, sort_keys=True) + "\n"
            + json.dumps(row, sort_keys=True) + "\n")
    p.write_text(text, encoding="utf-8")

    def _never(progress=True):
        raise AssertionError("census() ran: the release refusal did not fire first")

    monkeypatch.setattr(_dp, "census", _never)
    with pytest.raises(SystemExit) as ei:
        _dp.merge_cell(p, progress=False)
    assert "0.0.0" in str(ei.value) and "REFUSING" in str(ei.value)
    # nothing was written: the refusal happened before the merge
    assert p.read_text(encoding="utf-8") == text
