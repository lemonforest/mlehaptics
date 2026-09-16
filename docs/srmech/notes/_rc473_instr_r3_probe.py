"""rc473 instrument repair 3 (`#T1188`): does the count check see a run that ran nothing, or ran the wrong items?

Usage:  python3 notes/_rc473_instr_r3_probe.py <plugin .py file> <ripple_check .py file> [<case> ...]

Gate round j1 raised two geometries the instrument-repair-2 count check reads as green, neither of
them a removal:

* a **setup-only protocol** — ``--setup-plan`` or ``--setup-only`` arriving through an ini
  ``addopts`` or set on ``config.option`` by a ``conftest`` ``pytest_configure``. Every item is
  collected, kept and given a ``setup`` report, and no test body runs;
* a **count-preserving substitution** — a ``pytest_collection_modifyitems`` that drops one item and
  appends (or substitutes) a second reference to another, so ``collected``, ``selected`` and ``ran``
  are all unchanged while one of the manifest's items never runs.

This probe builds a four-item sandbox (``test_b[1]``, ``test_b[2]``, ``test_b[3]``, ``test_c``),
copies the given plugin in as ``tests/_collection_count_plugin.py``, runs pytest once per case with
``-p tests._collection_count_plugin``, and prints, for each case:

* the payload the plugin wrote;
* the node ids whose BODY executed (each body appends its own id to a file, so this counts
  executions, not reports) — the ground truth the counts are judged against;
* the verdict of ``judge_counts`` imported from the given ``tools/ripple_check.py``, with pytest's
  own return code, which is what the runner would exit with.

A case named ``LIMIT_*`` is one the check is NOT claimed to see; it is pinned here so a change in
either direction is reported. Asserts nothing; removes its sandbox.
numpy-free; no hashlib; no abs().
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

IMP = "import pytest\n\n\n"
DROP = "    kept = [i for i in items if not i.nodeid.endswith('test_b[2]')]\n"

#: name -> (conftest source, ini body, description)
CASES = {
    "none": ("", "[pytest]\n", "control: nothing planted"),
    # --- gate round j1 can-fail B1: a protocol that runs no test body ---
    "ini_addopts_setup_plan": ("", "[pytest]\naddopts = --setup-plan\n",
                               "j1 B1: --setup-plan through an ini addopts"),
    "ini_addopts_setup_only": ("", "[pytest]\naddopts = --setup-only\n",
                               "j1 B1: --setup-only through an ini addopts"),
    "conftest_configure_setuponly": ("def pytest_configure(config):\n"
                                     "    config.option.setuponly = True\n", "[pytest]\n",
                                     "j1 B1: setuponly set on config.option by a conftest"),
    # --- gate round j1 can-fail B2 / disclosure B1: the counts are preserved ---
    "drop_and_duplicate": ("def pytest_collection_modifyitems(config, items):\n" + DROP
                           + "    dup = [i for i in kept if i.nodeid.endswith('test_b[1]')]\n"
                             "    items[:] = kept + dup[:1]\n", "[pytest]\n",
                           "j1 B2: one item dropped, another appended a second time"),
    "substitute_in_place": ("def pytest_collection_modifyitems(config, items):\n"
                            "    keep = [i for i in items if i.nodeid.endswith('test_b[1]')]\n"
                            "    items[:] = [keep[0] if i.nodeid.endswith('test_b[2]') else i\n"
                            "                for i in items]\n", "[pytest]\n",
                            "j1 disclosure B1: one item REPLACED by a second reference to another"),
    # --- controls that must stay seen (instrument repair 2's classes) ---
    "modifyitems_plain": ("def pytest_collection_modifyitems(config, items):\n" + DROP
                          + "    items[:] = kept\n", "[pytest]\n",
                          "repair 2: a plain removal at collection"),
    "collection_finish_trylast": (IMP + "@pytest.hookimpl(trylast=True)\n"
                                  "def pytest_collection_finish(session):\n"
                                  "    session.items[:] = [i for i in session.items\n"
                                  "                        if not i.nodeid.endswith('test_b[2]')]\n",
                                  "[pytest]\n", "repair 2: a removal after collection finished"),
    # --- limits: pinned as NOT seen ---
    "LIMIT_pyfunc_call_true": (IMP + "@pytest.hookimpl(tryfirst=True)\n"
                               "def pytest_pyfunc_call(pyfuncitem):\n"
                               "    if pyfuncitem.nodeid.endswith('test_b[2]'):\n        return True\n",
                               "[pytest]\n",
                               "j1 can-fail N1: the item runs; only its BODY is replaced"),
    "LIMIT_setup_skips": (IMP + "def pytest_runtest_setup(item):\n"
                          "    if item.nodeid.endswith('test_b[2]'):\n        pytest.skip('planted')\n",
                          "[pytest]\n", "repair 2 limit: the item runs and is reported skipped"),
}

PROBE = ("import os\nimport pytest\n\n\n"
         "def _mark(nodeid):\n"
         "    with open(os.environ['R3_BODIES'], 'a', encoding='utf-8') as fh:\n"
         "        fh.write(nodeid + '\\n')\n\n\n"
         "@pytest.mark.parametrize('n', [1, 2, 3])\n"
         "def test_b(request, n):\n    _mark(request.node.nodeid)\n    assert n\n\n\n"
         "def test_c(request):\n    _mark(request.node.nodeid)\n    assert True\n")


def load_judge(path: Path):
    spec = importlib.util.spec_from_file_location("r3_ripple_check", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(tmp: Path, name: str):
    source, ini, _why = CASES[name]
    (tmp / "conftest.py").write_text(source, encoding="utf-8")
    (tmp / "pytest.ini").write_text(ini, encoding="utf-8")
    out, bodies = tmp / "counts.json", tmp / "bodies.txt"
    for f in (out, bodies):
        if f.exists():
            f.unlink()
    env = dict(os.environ, SRMECH_COLLECTION_COUNT_OUT=str(out), R3_BODIES=str(bodies),
               PYTHONPATH=str(tmp))
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
            "-p", "tests._collection_count_plugin", "test_probe.py"]
    proc = subprocess.run(argv, cwd=str(tmp), env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=300)
    try:
        got = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        got = None
    ran = bodies.read_text(encoding="utf-8").split() if bodies.exists() else []
    lines = [ln for ln in proc.stdout.decode("utf-8", "replace").splitlines() if ln.strip()]
    return proc.returncode, got, ran, (lines[-1] if lines else "")


def main(argv):
    plugin, checker = Path(argv[1]).resolve(), Path(argv[2]).resolve()
    names = argv[3:] or list(CASES)
    import pytest
    import pluggy
    rc = load_judge(checker)
    print(f"python {sys.version.split()[0]} pytest {pytest.__version__} pluggy {pluggy.__version__}")
    print(f"plugin {plugin} ({plugin.stat().st_size} bytes)")
    print(f"ripple_check {checker} ({checker.stat().st_size} bytes)")
    tmp = Path(tempfile.mkdtemp(prefix="ir3_probe_"))
    try:
        (tmp / "tests").mkdir()
        (tmp / "tests" / "__init__.py").write_text("", encoding="utf-8")
        shutil.copy(plugin, tmp / "tests" / "_collection_count_plugin.py")
        (tmp / "test_probe.py").write_text(PROBE, encoding="utf-8")
        for name in names:
            prc, got, ran, last = run(tmp, name)
            small = None if got is None else {k: got[k] for k in ("collected", "selected",
                                                                  "deselected", "ran") if k in got}
            verdict = rc.judge_counts(prc, got)
            print(f"{name:30s} pytest exit {prc} {small} bodies {len(ran)} {sorted(ran)}")
            print(f"{'':30s} judge_counts -> {verdict} ({'GREEN' if verdict == 0 else 'red'}) | {last}")
            if got is not None:
                extra = {k: v for k, v in got.items()
                         if k not in ("collected", "selected", "deselected", "ran")}
                if extra:
                    print(f"{'':30s} accounting {json.dumps(extra, sort_keys=True)[:300]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        print("sandbox removed:", not tmp.exists())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
