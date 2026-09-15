"""rc473 instrument repair 2 (`#T1188`): which removals a collection-count plugin reports, in a sandbox.

Usage:  python3 notes/_rc473_instr_r2_order_probe.py <plugin .py file> [<filter> ...]

Builds a temporary sandbox holding a 4-item probe file (``test_b[1]``, ``test_b[2]``, ``test_b[3]``,
``test_c``), copies the given plugin file in as ``tests/_collection_count_plugin.py``, and for each
filter below runs pytest twice with ``-p tests._collection_count_plugin``:

* with ``--collect-only`` — the view of the manifest meta-test's COLLECTION check;
* as a run — the view of ``tools/ripple_check.py``'s gate run.

Every filter except ``none`` and the two option rows drops ``test_b[2]``. A filter marked ``conftest``
is written to the sandbox's ``conftest.py``; one marked ``env`` is written to a module the run names in
``PYTEST_PLUGINS`` (the conftest is then empty). For each run it prints the counts the plugin wrote and
a verdict:

* collect-only, the meta-test predicate: ``selected != collected`` or any ``deselected``;
* run, the runner predicate: the same, or ``ran != collected`` where the plugin writes ``ran``.

A plugin that writes no ``ran`` (the instrument-repair-1 plugin) is judged on the run by the meta-test
predicate, which is what that runner's ``judge_counts`` read. Asserts nothing; removes its sandbox.
numpy-free; no hashlib; no abs().
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DROP_ITEMS = "    items[:] = [i for i in items if not i.nodeid.endswith('test_b[2]')]\n"
DROP_SESSION = "    session.items[:] = [i for i in session.items if not i.nodeid.endswith('test_b[2]')]\n"
IMP = "import pytest\n\n\n"

#: name -> (source, where, extra pytest args)
FILTERS = {
    "none": ("", "conftest", ()),
    "modifyitems_plain": ("def pytest_collection_modifyitems(config, items):\n" + DROP_ITEMS, "conftest", ()),
    "modifyitems_tryfirst": (IMP + "@pytest.hookimpl(tryfirst=True)\n"
                             "def pytest_collection_modifyitems(config, items):\n" + DROP_ITEMS, "conftest", ()),
    "modifyitems_wrapper_old_after_yield": (IMP + "@pytest.hookimpl(hookwrapper=True, tryfirst=True)\n"
                                            "def pytest_collection_modifyitems(config, items):\n    yield\n"
                                            + DROP_ITEMS, "conftest", ()),
    "modifyitems_wrapper_old_before_yield": (IMP + "@pytest.hookimpl(hookwrapper=True, tryfirst=True)\n"
                                             "def pytest_collection_modifyitems(config, items):\n"
                                             + DROP_ITEMS + "    yield\n", "conftest", ()),
    "modifyitems_wrapper_new_before_yield": (IMP + "@pytest.hookimpl(wrapper=True, tryfirst=True)\n"
                                             "def pytest_collection_modifyitems(config, items):\n"
                                             + DROP_ITEMS + "    return (yield)\n", "conftest", ()),
    "modifyitems_wrapper_old_before_yield_ENV": (IMP + "@pytest.hookimpl(hookwrapper=True, tryfirst=True)\n"
                                                 "def pytest_collection_modifyitems(config, items):\n"
                                                 + DROP_ITEMS + "    yield\n", "env", ()),
    "modifyitems_wrapper_new_before_yield_ENV": (IMP + "@pytest.hookimpl(wrapper=True, tryfirst=True)\n"
                                                 "def pytest_collection_modifyitems(config, items):\n"
                                                 + DROP_ITEMS + "    return (yield)\n", "env", ()),
    "collection_finish_trylast": (IMP + "@pytest.hookimpl(trylast=True)\n"
                                  "def pytest_collection_finish(session):\n" + DROP_SESSION, "conftest", ()),
    "collection_finish_trylast_ENV": (IMP + "@pytest.hookimpl(trylast=True)\n"
                                      "def pytest_collection_finish(session):\n" + DROP_SESSION, "env", ()),
    "collection_finish_wrapper_before_yield": (IMP + "@pytest.hookimpl(hookwrapper=True, tryfirst=True)\n"
                                               "def pytest_collection_finish(session):\n"
                                               + DROP_SESSION + "    yield\n", "conftest", ()),
    "runtestloop_wrapper_before_yield": (IMP + "@pytest.hookimpl(hookwrapper=True, tryfirst=True)\n"
                                         "def pytest_runtestloop(session):\n" + DROP_SESSION + "    yield\n",
                                         "conftest", ()),
    "runtestloop_wrapper_before_yield_ENV": (IMP + "@pytest.hookimpl(hookwrapper=True, tryfirst=True)\n"
                                             "def pytest_runtestloop(session):\n" + DROP_SESSION
                                             + "    yield\n", "env", ()),
    "runtest_protocol_returns_true": (IMP + "@pytest.hookimpl(tryfirst=True)\n"
                                      "def pytest_runtest_protocol(item, nextitem):\n"
                                      "    if item.nodeid.endswith('test_b[2]'):\n        return True\n",
                                      "conftest", ()),
    "option_k": ("", "conftest", ("-k", "test_c")),
    "option_o_addopts_k": ("", "conftest", ("-o", "addopts=-k test_c")),
    # outside the class the count check names: the item never reaches pytest_itemcollected, or it runs
    "LIMIT_make_collect_report_wrapper": (IMP + "@pytest.hookimpl(hookwrapper=True)\n"
                                          "def pytest_make_collect_report(collector):\n"
                                          "    outcome = yield\n    rep = outcome.get_result()\n"
                                          "    if rep.result:\n"
                                          "        rep.result[:] = [r for r in rep.result"
                                          " if not r.nodeid.endswith('test_b[2]')]\n", "conftest", ()),
    "LIMIT_runtest_setup_skips": (IMP + "def pytest_runtest_setup(item):\n"
                                  "    if item.nodeid.endswith('test_b[2]'):\n"
                                  "        pytest.skip('planted')\n", "conftest", ()),
}


def run(tmp: Path, name: str, collect_only: bool):
    source, where, extra = FILTERS[name]
    (tmp / "conftest.py").write_text(source if where == "conftest" else "", encoding="utf-8")
    (tmp / "r2_envplug.py").write_text(source if where == "env" else "", encoding="utf-8")
    out = tmp / "counts.json"
    if out.exists():
        out.unlink()
    env = dict(os.environ, SRMECH_COLLECTION_COUNT_OUT=str(out), PYTHONPATH=str(tmp))
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    if where == "env":
        env["PYTEST_PLUGINS"] = "r2_envplug"
    argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "-p", "tests._collection_count_plugin", "test_probe.py", *extra]
    if collect_only:
        argv.append("--collect-only")
    proc = subprocess.run(argv, cwd=str(tmp), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=300)
    try:
        got = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        got = None
    lines = [ln for ln in proc.stdout.decode("utf-8", "replace").splitlines() if ln.strip()]
    return proc.returncode, got, (lines[-1] if lines else "")


def seen(got, use_ran: bool):
    if got is None or got.get("collected") is None:
        return "NO COUNTS"
    removed = got.get("selected") != got["collected"] or bool(got.get("deselected"))
    if use_ran and "ran" in got:
        removed = removed or got["ran"] != got["collected"]
    return "SEEN" if removed else "not seen"


def main(argv):
    plugin = Path(argv[1]).resolve()
    names = argv[2:] or list(FILTERS)
    import pytest
    import pluggy
    print(f"python {sys.version.split()[0]} pytest {pytest.__version__} pluggy {pluggy.__version__} "
          f"plugin {plugin} ({plugin.stat().st_size} bytes)")
    tmp = Path(tempfile.mkdtemp(prefix="ir2_order_"))
    try:
        (tmp / "tests").mkdir()
        (tmp / "tests" / "__init__.py").write_text("", encoding="utf-8")
        shutil.copy(plugin, tmp / "tests" / "_collection_count_plugin.py")
        (tmp / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
        (tmp / "test_probe.py").write_text(
            "import pytest\n\n\n@pytest.mark.parametrize('n', [1, 2, 3])\n"
            "def test_b(n):\n    assert n\n\n\ndef test_c():\n    assert True\n", encoding="utf-8")
        for name in names:
            crc, cgot, _clast = run(tmp, name, True)
            rrc, rgot, rlast = run(tmp, name, False)
            print(f"{name:42s} collect-only exit {crc} {cgot} meta-test predicate {seen(cgot, False)}")
            print(f"{'':42s} run exit {rrc} {rgot} runner predicate {seen(rgot, True)} | {rlast}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        print("sandbox removed:", not tmp.exists())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
