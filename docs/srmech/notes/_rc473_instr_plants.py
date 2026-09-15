"""rc473 instrument round (`#T1188`): the planted regressions behind the round's can-fail figures.

Usage:  python3 notes/_rc473_instr_plants.py <docs/srmech root of a CLONE> <plant id>
        python3 notes/_rc473_instr_plants.py <root> revert <rev> <docs/srmech-relative path> ...
        python3 notes/_rc473_instr_plants.py <root> rowdiff <ledger: worked|args> <rev>
        python3 notes/_rc473_instr_plants.py --list

Every text plant is an exact substitution that must match EXACTLY ONCE, or the plant aborts
before writing anything. Ledger plants rewrite only the targeted rows' field and must not be a
no-op. Reverts write a whole blob of <rev>. Restoring is the caller's `git checkout --
docs/srmech`, followed by a printed tracked-changes count (notes/_rc473_instr_canfail.sh).

Git is read-only here (`git show`), through tests/_git_env.py: a scrubbed child environment and
the per-invocation location lookup. Never point this at the live repository.

The advice plants construct their text at run time (the verb and the variable names are
joined here, never spelled whole in this file), because tests/test_git_export_advice_absent_rc473.py
scans notes/ and would otherwise read this file as advice.
numpy-free; no hashlib; no abs().
"""
import json
import subprocess
import sys
from pathlib import Path

B = chr(92)                          # a backslash, spelled without an escape
VERB = "ex" + "port"
D, W = "GIT_" + "DIR", "GIT_" + "WORK_TREE"
P = "python/"
WORKED = P + "tests/worked_examples_result.ndjson"
ARGS = P + "tests/example_args_ledger.ndjson"
DOCS = P + "srmech/introspect/_tool_docs.py"
KEPLER = ("srmech.math.kepler.equation_of_centre", "srmech.math.kepler.kepler_solve",
          "srmech.math.kepler.pin_slot")

TEXT = {
    # B — the git-environment layers, one at a time
    "L1e_invoke_unscrub": [(P + "tools/hooks/check_hooks.py",
        '    env = dict(os.environ)\n    H.scrub_git_env(env)\n    env["CLAUDE_PROJECT_DIR"]',
        '    env = dict(os.environ)\n    env["CLAUDE_PROJECT_DIR"]')],
    "L1f_hooklib_git_unscrub": [(P + "tools/hooks/_hooklib.py",
        "    return run([git_exe(), *where, *args], cwd=cwd, timeout=timeout,\n               env=_GIT_ENV.scrubbed())",
        "    return run([git_exe(), *where, *args], cwd=cwd, timeout=timeout,\n               env=None)")],
    "L2d_redirect_empty": [(P + "tests/_git_env.py",
        'GIT_WRITE_REDIRECT_ENV = ("GIT_NAMESPACE", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM")',
        "GIT_WRITE_REDIRECT_ENV = ()")],
    "L2n_namespace_dropped": [(P + "tests/_git_env.py",
        'GIT_WRITE_REDIRECT_ENV = ("GIT_NAMESPACE", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM")',
        'GIT_WRITE_REDIRECT_ENV = ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM")')],
    # A3 — a frozen gate narrowed in the manifest; a deselect the manifest cannot show
    "M_node": [(P + "tools/ripple_gates.txt",
        "\ntests/test_git_env_cannot_reach_a_repository_rc473.py\n",
        "\ntests/test_git_env_cannot_reach_a_repository_rc473.py::test_the_git_writing_tests_cannot_reach_a_repository_GIT_DIR_names\n")],
    "M_deselect_conftest": [(P + "tests/conftest.py",
        "from tests import _git_env_guard  # noqa: E402,F401  (import-time scrub)\n",
        "from tests import _git_env_guard  # noqa: E402,F401  (import-time scrub)\n\n\n"
        "def pytest_collection_modifyitems(config, items):\n"
        "    items[:] = [i for i in items if 'suite_conftest_loads_the_guard' not in i.nodeid]\n")],
    # B — the export advice, back in shipped text (and two controls that must stay green)
    "P1_hooklib_remedy": [(P + "tools/hooks/_hooklib.py",
        "Do NOT " + VERB + " " + D + " or " + W,
        "Or " + VERB + " " + D + " and " + W)],
    "P3_readme_advice": [(P + "tools/hooks/README.md",
        "falsehood was fixed, and the instrument still demonstrably fires on the same\nclass.\n",
        "falsehood was fixed, and the instrument still demonstrably fires on the same\nclass.\n\n"
        "If that fails, " + VERB + " " + D + " and " + W + ".\n")],
    "P5_notes_shell": [("notes/_rc473_final_layer3_geometry.sh",
        'exit "$fail"\n',
        'exit "$fail"\n' + VERB + " " + D + "=/mnt/d/GitHub/mlehaptics/.git\n")],
    "P6_cmd_prefix": [(P + "tools/ripple_check.py",
        'if __name__ == "__main__":\n',
        "# Run as " + D + "=D:/x/.git " + W + "=D:/x python -m pytest tests/\n"
        'if __name__ == "__main__":\n')],
    "P7_changelog_green": [(P + "CHANGELOG.md",
        "\n## [0.9.0rc472]",
        "\nIf that fails, " + VERB + " " + D + " and " + W + ".\n\n## [0.9.0rc472]")],
    "P10_allow_reworded": [(P + "tools/census_regen_diff.py",
        "the obvious workaround", "the plain workaround")],
    "P13_negated_green": [(P + "tools/ripple_check.py",
        'if __name__ == "__main__":\n',
        "# never " + VERB + " " + D + " for this\n" + 'if __name__ == "__main__":\n')],
    # C — a registry drift gate t1 planted (curated + generated, registry not regenerated),
    #     and a length-changing registry-only drift for the codegen idempotence node
    "R_t1_3b": [(P + "srmech/introspect/_tool_docs_curated.py",
        "so the mechanism approximates the anomaly; it does not compute it exactly",
        "so the mechanism approximates the anomaly; it does not compute it at all"),
                (DOCS,
        "so the mechanism approximates the anomaly; it does not compute it exactly",
        "so the mechanism approximates the anomaly; it does not compute it at all")],
    "R_registry_len": [("c/src/srmech_tool_registry.c",
        "at double precision, which is not a bound", "at double precision, which is a bound")],
}

LEDGER_FIELDS = {
    "F_worked_defblob_kepler": (WORKED, "name", "02051b004^", "def_blob", KEPLER),
    "F_args_defblob_kepler": (ARGS, "op", "02051b004^", "def_blob", KEPLER),
    "F_worked_src_atan2": (WORKED, "name", "02051b004^", "src_sha256", ("srmech.math.rational.atan2",)),
    "F_args_src_atan2": (ARGS, "op", "02051b004^", "src_sha256", ("srmech.math.rational.atan2",)),
}
REVERTS = {
    "V_worked_d346173fc": ("d346173fc", WORKED), "V_args_d346173fc": ("d346173fc", ARGS),
    "V_worked_1ab8d405b": ("1ab8d405b", WORKED), "V_args_1ab8d405b": ("1ab8d405b", ARGS),
}
OTHER = ("F_worked_defmodule_pinslot", "S_pin_slot_snippet", "K_c_revert")


def git_show(root: Path, rev: str, rel: str) -> bytes:
    py = root / "python"
    sys.path.insert(0, str(py))
    from tests import _git_env
    proc = subprocess.run(_git_env.git_argv(py, ["show", f"{rev}:docs/srmech/{rel}"]), cwd=str(py),
                          env=_git_env.scrubbed(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise SystemExit(f"git show {rev}:docs/srmech/{rel} exited {proc.returncode}: "
                         f"{proc.stderr.decode('utf-8', 'replace').strip()}")
    return proc.stdout


def text_plant(root: Path, pid: str) -> None:
    edits = []
    for rel, old, new in TEXT[pid]:
        text = (root / rel).read_bytes().decode("utf-8")
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"{pid}: {rel}: expected exactly one match, found {n}; nothing written")
        edits.append((rel, text.replace(old, new)))
    for rel, text in edits:
        (root / rel).write_bytes(text.encode("utf-8"))
        print(f"planted {pid}: {rel}")


def rows_of(raw: bytes, key: str):
    meta, rows = {}, {}
    for line in raw.decode("utf-8").splitlines():
        if line.strip():
            obj = json.loads(line)
            if obj.get("record") == "meta":
                meta = obj
            else:
                rows[obj[key]] = obj
    return meta, rows


def rewrite_rows(root: Path, rel: str, key: str, change) -> int:
    path = root / rel
    lines = path.read_bytes().decode("utf-8").split("\n")
    done = 0
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("record") != "meta" and change(obj):
            lines[i] = json.dumps(obj, sort_keys=True)
            done += 1
    path.write_bytes("\n".join(lines).encode("utf-8"))
    return done


def field_plant(root: Path, pid: str) -> None:
    rel, key, rev, field, names = LEDGER_FIELDS[pid]
    _meta, old = rows_of(git_show(root, rev, rel), key)

    def change(obj):
        if obj.get(key) not in names:
            return False
        want = old[obj[key]][field]
        if obj[field] == want:
            raise SystemExit(f"{pid}: {obj[key]}.{field} already equals {rev}'s value (a no-op plant)")
        obj[field] = want
        return True

    done = rewrite_rows(root, rel, key, change)
    if done != len(names):
        raise SystemExit(f"{pid}: planted {done} of {len(names)} rows")
    print(f"planted {pid}: {field} <- {rev} on {done} row(s) of {rel}")


def other_plant(root: Path, pid: str) -> None:
    if pid == "F_worked_defmodule_pinslot":
        def change(obj):
            if obj.get("name") != "srmech.math.kepler.pin_slot":
                return False
            obj["def_module"] = "srmech.math.rational"
            return True
        done = rewrite_rows(root, WORKED, "name", change)
        if done != 1:
            raise SystemExit(f"{pid}: planted {done} rows")
        print(f"planted {pid}: kepler.pin_slot def_module -> srmech.math.rational in {WORKED}")
    elif pid == "S_pin_slot_snippet":
        path = root / DOCS
        text = path.read_bytes().decode("utf-8")
        anchor = '    "srmech.math.kepler.pin_slot": {'
        if text.count(anchor) != 1:
            raise SystemExit(f"{pid}: anchor count {text.count(anchor)}")
        i = text.index(anchor)
        nxt = text.find('\n    "', i + len(anchor))
        end = len(text) if nxt < 0 else nxt
        for quote in ("'worked': '", "'worked': \""):
            j = text.find(quote, i, end)
            if j >= 0:
                k = j + len(quote)
                break
        else:
            raise SystemExit(f"{pid}: no worked literal in the pin_slot entry")
        path.write_bytes((text[:k] + "# planted" + B + "n" + text[k:]).encode("utf-8"))
        print(f"planted {pid}: a '# planted' line opens kepler.pin_slot's worked snippet in {DOCS}")
    elif pid == "K_c_revert":
        rel = "c/src/srmech_kepler.c"
        head = (root / rel).read_bytes().decode("utf-8")
        base = git_show(root, "1ab8d405b", rel).decode("utf-8")
        call = "    return srmech_trig_kepler_q61(M_rad, e, tolerance, max_iter, out_E_rad);\n}\n"
        start = "    /* Smith (1979) initial guess: E_0 = M + e * sin(M). Converges in 4-6\n"
        stop = "    *out_E_rad = E;\n    return SRMECH_ERR_OVERFLOW;\n}\n"
        for text, needle, what in ((base, start, "base start"), (base, stop, "base end"), (head, call, "head call")):
            if text.count(needle) != 1:
                raise SystemExit(f"{pid}: {what}: {text.count(needle)} matches")
        body = base[base.index(start):base.index(stop) + len(stop)]
        (root / rel).write_bytes(head.replace(call, body).encode("utf-8"))
        print(f"planted {pid}: srmech_kepler_solve's Q61 call -> {body.count(chr(10))} lines of 1ab8d405b's double Newton loop")


def rowdiff(root: Path, which: str, rev: str) -> None:
    rel, key = (WORKED, "name") if which == "worked" else (ARGS, "op")
    _hm, head = rows_of((root / rel).read_bytes(), key)
    _om, old = rows_of(git_show(root, rev, rel), key)
    moved = {n: sorted(k for k in set(head[n]) | set(old[n]) if head[n].get(k) != old[n].get(k))
             for n in set(head) & set(old)}
    moved = {n: f for n, f in moved.items() if f}
    blob = sorted(n for n, f in moved.items() if "def_blob" in f)
    src = sorted(n for n, f in moved.items() if "src_sha256" in f and "def_blob" not in f)
    other = sorted((n, f) for n, f in moved.items() if not {"def_blob", "src_sha256"} & set(f))
    print(f"rowdiff {which} <- {rev}: {len(head)} rows, moved {len(moved)}: def_blob {len(blob)}, "
          f"src_sha256 without def_blob {len(src)}, either key {len(blob) + len(src)}, neither {other}; "
          f"added {len(set(head) - set(old))} removed {len(set(old) - set(head))}")
    print("  def_blob:", blob)
    print("  src_sha256 only:", src)


def main(argv):
    if argv[1:2] == ["--list"]:
        for pid in list(TEXT) + list(LEDGER_FIELDS) + list(REVERTS) + list(OTHER):
            print(pid)
        return 0
    root, pid = Path(argv[1]), argv[2]
    if pid == "revert":
        rev = argv[3]
        for rel in argv[4:]:
            (root / rel).write_bytes(git_show(root, rev, rel))
            print(f"reverted {rel} <- {rev}")
    elif pid == "rowdiff":
        rowdiff(root, argv[3], argv[4])
    elif pid in TEXT:
        text_plant(root, pid)
    elif pid in LEDGER_FIELDS:
        field_plant(root, pid)
    elif pid in REVERTS:
        rev, rel = REVERTS[pid]
        (root / rel).write_bytes(git_show(root, rev, rel))
        print(f"planted {pid}: {rel} <- {rev}")
    elif pid in OTHER:
        other_plant(root, pid)
    else:
        raise SystemExit(f"unknown plant {pid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
