r"""R-RBS-LM-APIDIFF (F727 addendum) — re-runnable BREAKING-API scan between two srmech installs.

Dumps the public callable+signature surface of the srmech modules the research subtree uses, in EACH of two
venvs, then diffs: REMOVED names (hard breaks), SIGNATURE changes (param/return), and import-status flips.

Usage:
  python3 R-RBS-LM-APIDIFF_rc_breaking_change_scan.py <old_python> <new_python>
  e.g.  python3 …APIDIFF… /tmp/srmech_rc78/venv/bin/python3 /tmp/srmech_rc128/venv/bin/python3

rc78 -> rc128 RESULT (2026-06-11): 0 hard breaks; the only behavioral break is the numpy-removal return-type
shift `np.ndarray -> list/tuple` across laplacian.* + coupling.signed_sum_squared + harmonics (values verified
correct, executes numpy-free); qm.{octonion,single_particle,so8,triality} flipped import-ERR -> OK (now numpy-free).
No abs(); no CAD; research-subtree provenance.
"""
import json
import subprocess
import sys

_DUMP = r'''
import json, inspect, importlib
MODS = ["srmech","srmech.amsc.format","srmech.amsc.genome","srmech.amsc.hdc","srmech.amsc.cascade",
 "srmech.amsc.laplacian","srmech.amsc.rational","srmech.amsc.cyclic","srmech.amsc.primes","srmech.amsc.harmonics",
 "srmech.amsc.dispatch","srmech.amsc.search","srmech.amsc.tlv","srmech.amsc.template","srmech.amsc.descriptor",
 "srmech.amsc.catalog","srmech.amsc.coupling","srmech.amsc.naming","srmech.amsc.kepler","srmech.amsc.tool_schema",
 "srmech.qm.so8","srmech.qm.triality","srmech.qm.octonion","srmech.qm.single_particle","srmech.calculus",
 "srmech.signal_processing","srmech.dsl"]
out={}
for m in MODS:
    try: mod=importlib.import_module(m)
    except Exception as e: out[m]={"__import_error__":f"{type(e).__name__}: {e}"}; continue
    s={}
    for n in dir(mod):
        if n.startswith("_"): continue
        o=getattr(mod,n)
        if not (callable(o) or inspect.isclass(o)): continue
        mo=getattr(o,"__module__","") or ""
        if mo and not mo.startswith("srmech"): continue
        try: sig=str(inspect.signature(o))
        except Exception: sig="(class)" if inspect.isclass(o) else "(?)"
        s[n]=sig
    out[m]=s
print(json.dumps(out, sort_keys=True))
'''


def dump(py):
    r = subprocess.run([py, "-c", _DUMP], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"dump failed for {py}:\n{r.stderr}")
    return json.loads(r.stdout)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    a, b = dump(sys.argv[1]), dump(sys.argv[2])
    hard, sigchg, impchg, added = [], [], [], []
    for m in sorted(set(a) | set(b)):
        A, B = a.get(m, {}), b.get(m, {})
        ae, be = "__import_error__" in A, "__import_error__" in B
        if ae != be:
            impchg.append(f"{m}: old={'ERR' if ae else 'ok'} new={'ERR:'+B['__import_error__'] if be else 'ok'}")
            continue
        if ae and be:
            continue
        an, bn = set(A) - {"__import_error__"}, set(B) - {"__import_error__"}
        hard += [f"{m}.{n}  (was {A[n]})" for n in sorted(an - bn)]
        added += [f"{m}.{n}{B[n]}" for n in sorted(bn - an)]
        for n in sorted(an & bn):
            if A[n] != B[n] and "(?)" not in (A[n], B[n]) and "(class)" not in (A[n], B[n]):
                sigchg.append(f"{m}.{n}\n      old: {A[n]}\n      new: {B[n]}")

    def sec(t, items):
        print(f"\n### {t} ({len(items)})")
        for x in (items or ["(none)"]):
            print("  -", x)
    print(f"=== BREAKING-API DIFF  {sys.argv[1]} -> {sys.argv[2]} ===")
    sec("HARD BREAKS — public names REMOVED", hard)
    sec("SIGNATURE CHANGES (param/return)", sigchg)
    sec("MODULE IMPORT status flips", impchg)
    print(f"\n(non-breaking additions: {len(added)} new public names)")


if __name__ == "__main__":
    main()
