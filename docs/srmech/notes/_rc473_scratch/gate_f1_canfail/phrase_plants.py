"""M4 driver: re-insert each removed Kepler-identity sentence on ONE shipped surface at a time and run
the phrase gate (a fresh pytest per plant). Usage: python phrase_plants.py <repo_root> <out.ndjson>
Standard plants: 15 phrases x 6 surfaces, each in that surface's native form (single-line string
surfaces: appended inside the pin_slot sentence; wrapped surfaces: two new lines under the measured
replacement sentence, carrying that line's comment prefix, split mid-phrase). Probe plants: the phrase
split across an escaped newline inside the string surfaces (backslash-n + "# " in the Python files,
backslash-backslash-n + "# " in the C registry, the encoding a worked-comment newline has there).
File bytes restored after every plant and compared."""
import importlib.util, json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(sys.argv[1]); PY = ROOT / "docs/srmech/python"; SR = ROOT / "docs/srmech"
OUT = Path(sys.argv[2])
GATE = "tests/test_kepler_identity_phrases_absent_rc473.py"
spec = importlib.util.spec_from_file_location("gate_phr", PY / GATE)
gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
NEEDLE = "comparing a bronze linkage with Kepler" + chr(39) + "s equation"
SINGLE = ("python/srmech/introspect/_tool_docs_curated.py", "python/srmech/introspect/_tool_docs.py",
          "c/src/srmech_tool_registry.c")
WRAPPED = {"c/include/srmech.h": "read Kepler" + chr(39) + "s equation as pin-slot composition",
           "python/srmech/math/kepler.py": "read Kepler-equation algebra as pin-slot composition",
           "c/src/srmech_kepler.c": "read Kepler-equation algebra as pin-slot composition"}
ENV = dict(os.environ, PATH=os.path.expanduser("~/.local/bin") + ":" + os.environ["PATH"],
           PYTHONDONTWRITEBYTECODE="1", SRMECH_EXPECT_PURE="1")
ENV.pop("SRMECH_ALLOW_STALE_NATIVE", None)
BS = chr(92)


def split(phrase, original):
    words = phrase.split()
    k = (len(words) + 1) // 2
    i = original.lower().find(phrase.lower())
    if i < 0:
        sp = [m.start() for m in re.finditer(" ", original)]
        pos = sp[len(sp) // 2]
    else:
        pos = i + len(" ".join(words[:k]))
    return original[:pos].rstrip(), original[pos:].lstrip()


def plant(rel, text, key, form):
    phrase, original = gate.REMOVED[key]
    if form == "native" and rel in SINGLE:
        assert text.count(NEEDLE) == 1, (rel, text.count(NEEDLE))
        return text.replace(NEEDLE, NEEDLE + "; " + original)
    if form == "native":
        m = gate._pattern(WRAPPED[rel]).search(text)
        assert m, rel
        eol = text.index("\n", m.end())
        line = text[text.rfind("\n", 0, eol) + 1:eol]
        prefix = re.match(r"[ \t]*(?:\*[ \t]|#[ \t])?", line).group(0)
        a, b = split(phrase, original)
        return text[:eol] + "\n" + prefix + a + "\n" + prefix + b + text[eol:]
    sep = {"esc_py": BS + "n# ", "esc_c": BS + BS + "n# "}[form]
    a, b = split(phrase, original)
    assert text.count(NEEDLE) == 1
    return text.replace(NEEDLE, NEEDLE + "; " + a + sep + b)


def run_gate():
    p = subprocess.run(["uv", "run", "--python", "3.12", "--no-project", "--offline", "--with", "pytest",
                        "python", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rf", GATE],
                       cwd=str(PY), env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
    out = p.stdout.decode("utf-8", "replace")
    summ = [l for l in out.splitlines() if re.search(r"\d+ (passed|failed|error)", l)]
    failed = sorted(set(re.findall(r"^FAILED \S+::(\S+)", out, re.M)))
    return p.returncode, (summ[-1] if summ else out[-300:]), failed


plans = [(k, rel, "native") for k in gate.REMOVED for rel in gate.SURFACES]
plans += [(k, "c/src/srmech_tool_registry.c", "esc_c") for k in gate.REMOVED]
plans += [(k, rel, "esc_py") for k in list(gate.REMOVED)[:3]
          for rel in ("python/srmech/introspect/_tool_docs_curated.py", "python/srmech/introspect/_tool_docs.py")]
print("plans", len(plans), flush=True)
shown = set()
with OUT.open("w") as fh:
    for key, rel, form in plans:
        path = SR / rel
        orig = path.read_bytes()
        text = orig.decode("utf-8")
        new = plant(rel, text, key, form)
        path.write_bytes(new.encode("utf-8"))
        scan = bool(gate._pattern(gate.REMOVED[key][0]).search(new))
        if (rel, form) not in shown:
            shown.add((rel, form))
            old_lines, new_lines = text.splitlines(), new.splitlines()
            d = [i for i, (x, y) in enumerate(zip(old_lines, new_lines)) if x != y]
            ln = d[0] if d else 0
            print(f"--- sample {rel} [{form}] {key}, from line {ln + 1}:", flush=True)
            for l in new_lines[ln:ln + 3]:
                j = l.find(NEEDLE)
                print("   |", l[:200] if j < 0 else l[j:j + 260], flush=True)
        rc, summ, failed = run_gate()
        path.write_bytes(orig)
        assert path.read_bytes() == orig
        main = "test_no_shipped_surface_carries_a_removed_kepler_identity_sentence" in failed
        rec = dict(key=key, surface=rel, form=form, direct_scan=scan, exit=rc, summary=summ.strip(),
                   failed=failed, gate_red=main)
        fh.write(json.dumps(rec) + "\n"); fh.flush()
        print(f"{'RED  ' if main else 'GREEN'} exit={rc} scan={scan} {form:6s} {rel:48s} {key:32s} | {summ.strip()}", flush=True)
