"""ADVERSARIAL round-3: check the keyset prototype's SSOT + link-table claims.

Claims under test
  A. registry params[] names/required == inspect.signature over the 10 link rows
     ("9/9 name agreement, 9/9 required agreement over the C-named leaf/body ops")
  B. leaf_best_rational's C defaults (100, 1000000) == Python's
     DEFAULT_MAX_DENOMINATOR / DEFAULT_FINE_SCALE
  C. piped positional counts: leaf 1, body 2
  D. "2/48 prefix rule", "35/48 python identity", "3 descriptor op names with no
     registry row", "10 class-scoped bare names"
  E. registry_rows_without_a_live_callable == 0  (NOT re-derived here, see notes)
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "python"))

import srmech  # noqa: E402
from srmech.introspect import tool_schema as TS  # noqa: E402
from srmech.dsl import lookup_cascade_op  # noqa: E402

# ── A. the 10 link rows: registry declaration vs inspect.signature ──────────
LINKS = [
    ("magnitude", "srmech.cascade.magnitude"),
    ("reorient", "srmech.cascade.reorient"),
    ("pin_slot_at_zero", "srmech.cascade.pin_slot_at_zero"),
    ("best_rational_signed", "srmech.cascade.best_rational_signed"),
    ("chiral_flip", "srmech.cascade.chiral_flip"),
    ("net_chirality", "srmech.cascade.net_chirality"),
    ("autocorrelation", "srmech.cascade.autocorrelation"),
    ("cyclic_gcd", "srmech.cascade.cyclic_gcd"),
    ("srmech.cascade.leaves.seq_get", "srmech.cascade.seq_get"),
    ("srmech.cascade.leaves.orientation_compose", "srmech.cascade.orientation_compose"),
]

_sch = TS.get_tool_schema()
entries = {e.name: e for e in _sch.tools}
if False:
    reg = TS.tool_schema()
    entries = {t["name"]: t for t in reg["tools"]} if isinstance(reg, dict) else None

print(f"srmech {srmech.__version__}")
print(f"tool_schema rows: {len(entries)}")
print()

name_ok = req_ok = 0
rows = []
for stage_op, reg_name in LINKS:
    e = entries.get(reg_name)
    fn = lookup_cascade_op(stage_op)
    sig = inspect.signature(fn)
    live = [(p.name, p.default is inspect.Parameter.empty) for p in sig.parameters.values()]
    if e is None:
        rows.append({"stage_op": stage_op, "reg": reg_name, "registry": None,
                     "live": live, "name_match": False, "req_match": False})
        continue
    if isinstance(e, dict):
        params = e.get("parameters", e.get("params", []))
        decl = [(p["name"], bool(p.get("required"))) for p in params]
    else:
        decl = [(p.name, bool(p.required)) for p in e.parameters]
    nm = [d[0] for d in decl] == [l[0] for l in live]
    rq = [d[1] for d in decl] == [l[1] for l in live]
    name_ok += nm
    req_ok += rq
    rows.append({"stage_op": stage_op, "reg": reg_name, "registry": decl,
                 "live_signature": live, "name_match": nm, "req_match": rq})

for r in rows:
    print(json.dumps(r))
print(f"\nA. name agreement  : {name_ok}/{len(LINKS)}")
print(f"A. required agree  : {req_ok}/{len(LINKS)}")

# ── B. best_rational_signed defaults ────────────────────────────────────────
import srmech.cascade as C  # noqa: E402

brs = lookup_cascade_op("best_rational_signed")
defaults = {p.name: p.default for p in inspect.signature(brs).parameters.values()
            if p.default is not inspect.Parameter.empty}
print(f"\nB. best_rational_signed python defaults: {defaults}")
for nm in ("DEFAULT_MAX_DENOMINATOR", "DEFAULT_FINE_SCALE"):
    found = None
    for modname in ("srmech.cascade", "srmech.cascade.atoms", "srmech.cascade.leaves"):
        try:
            m = __import__(modname, fromlist=["x"])
        except Exception:  # noqa: BLE001
            continue
        if hasattr(m, nm):
            found = (modname, getattr(m, nm))
            break
    print(f"B. {nm}: {found}")

# ── C. piped positional counts ─────────────────────────────────────────────
print("\nC. piped positional counts, derived from the shipped builders:")
from srmech.dsl import _control_flow as CF  # noqa: E402

print("   _chain.py:556 leaf call    -> op_fn(value, **kwargs)          piped=1")
for nm in ("make_fold_stage", "make_reduce_stage", "make_map_indexed_stage"):
    src = inspect.getsource(getattr(CF, nm))
    calls = [ln.strip() for ln in src.split("\n")
             if ("op_fn(" in ln or "body_fn(" in ln or "op(" in ln) and "def " not in ln]
    print(f"   {nm}: {calls}")

# ── D. the 48 descriptor-referenced op names ───────────────────────────────
CAT = HERE.parent / "python" / "srmech" / "cascade" / "catalogs" / "cascade_catalog"
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

op_names: set[str] = set()
op_class_pairs: set[tuple] = set()
for p in sorted(CAT.glob("*.toml")):
    d = tomllib.loads(p.read_text(encoding="utf-8"))
    casc = d.get("cascade", {})
    ch = casc.get("chain", {})
    for st in ch.get("steps", []) or []:
        for key in ("op", "fold_op", "reduce_op", "map_op", "parallel_body"):
            v = st.get(key)
            if isinstance(v, str):
                op_names.add(v)
                op_class_pairs.add((st.get("class"), v))
    for st in d.get("stage", []) or []:
        for key in ("op", "fold_op", "reduce_op", "map_op", "parallel_body"):
            v = st.get(key)
            if isinstance(v, str):
                op_names.add(v)
                op_class_pairs.add((None, v))

print(f"\nD. distinct descriptor-referenced op names: {len(op_names)}")
prefix_hits = sorted(n for n in op_names if ("srmech.cascade." + n) in entries)
print(f"D. prefix rule 'srmech.cascade.'+name resolves: {len(prefix_hits)}/{len(op_names)}"
      f"  -> {prefix_hits}")

identity_hits, no_row, unresolvable = [], [], []
by_callable = {}
for nm, e in entries.items():
    fnobj = getattr(e, "fn", None) if not isinstance(e, dict) else None
    if fnobj is not None:
        by_callable.setdefault(fnobj, []).append(nm)
for n in sorted(op_names):
    try:
        fn = lookup_cascade_op(n)
    except Exception:  # noqa: BLE001
        unresolvable.append(n)
        continue
    hit = by_callable.get(fn)
    if hit:
        identity_hits.append(n)
    else:
        no_row.append(n)
print(f"D. python callable-identity resolves: {len(identity_hits)}/{len(op_names)}")
print(f"D. resolvable but NO registry row ({len(no_row)}): {no_row}")
print(f"D. lookup_cascade_op cannot resolve ({len(unresolvable)}): {unresolvable}")
bare = sorted(n for n in unresolvable if "." not in n)
print(f"D. of those, class-scoped BARE names ({len(bare)}): {bare}")
