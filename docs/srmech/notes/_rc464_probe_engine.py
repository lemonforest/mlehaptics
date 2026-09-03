"""rc464 scratch probe: the cdr vtable vs the pure CatalogClass."""
import base64, json, sys

import srmech
from srmech import _native
from srmech.cascade.cd_register import CDRegister
from srmech.dsl import make_class
from srmech.dsl._class_catalog import CLASS_CATALOG_DIR, CatalogClass

print("srmech", srmech.__file__, srmech.__version__, "native", _native.HAS_NATIVE)
TOML = (CLASS_CATALOG_DIR / "cd_register.toml").read_text(encoding="utf-8")


def norm(x):
    if isinstance(x, bytes):
        return base64.b64encode(x).decode("ascii")
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [norm(e) for e in x]
    return x


def run_c(method, fields, args):
    d, t = _native.make_class_run_c(TOML, method, fields, args)
    return d, (json.loads(t) if t is not None else None)


def wire(reg, coupling=None, ec=None):
    return {
        "dim": reg.dim, "D": reg.D, "namespace": reg.namespace,
        "codebook": {k: base64.b64encode(v).decode("ascii")
                     for k, v in reg.codebook.items()},
        "slots": {str(k): [v[0], v[1]] for k, v in reg._slots.items()},
        "coupling": reg._coupling, "error_correction": reg._error_correction,
    }


def pyfields(reg):
    return {
        "dim": reg.dim, "D": reg.D, "namespace": reg.namespace,
        "codebook": dict(reg.codebook),
        "slots": {k: (v[0], v[1]) for k, v in reg._slots.items()},
        "coupling": reg._coupling, "error_correction": reg._error_correction,
    }


fails = []


def check(label, method, reg, args, expect_dispatch=True):
    f = wire(reg)
    d, got = run_c(method, f, args)
    inst = make_class("CDRegister")(**pyfields(reg))
    try:
        pure = getattr(inst, method)(**args)
    except Exception as exc:                      # pure raises -> C must DEFER
        status = "DISPATCHED(but pure raised!)" if d else "defer"
        print(f"  {label:52s} pure-raises={type(exc).__name__:12s} c={status}")
        if d:
            fails.append((label, "C dispatched where pure raises"))
        return
    if not d:
        print(f"  {label:52s} DEFER  (pure ok)")
        if expect_dispatch:
            fails.append((label, "DEFER but expected dispatch"))
        return
    if isinstance(pure, CatalogClass):
        exp_result = norm(pure.fields)
    else:
        exp_result = norm(pure)
    ok_r = got["result"] == exp_result
    exp_fields = norm(pyfields(inst) if False else inst.fields)
    ok_f = got["fields"] == exp_fields
    print(f"  {label:52s} dispatched result={'OK' if ok_r else 'MISMATCH'} "
          f"fields={'OK' if ok_f else 'MISMATCH'}")
    if not ok_r:
        fails.append((label, f"result {json.dumps(got['result'])[:160]} != "
                             f"{json.dumps(exp_result)[:160]}"))
    if not ok_f:
        fails.append((label, f"fields {json.dumps(got['fields'])[:160]} != "
                             f"{json.dumps(exp_fields)[:160]}"))


def suite(title, reg, slots_probe, j_probe):
    print(f"\n== {title} ==")
    check("slots", "slots", reg, {})
    check("working_block", "working_block", reg, {})
    check("carry_block", "carry_block", reg, {})
    check("element", "element", reg, {})
    check("materialize", "materialize", reg, {})
    for sl in slots_probe:
        check(f"read(slot={sl})", "read", reg, {"slot": sl})
    check("write(new slot)", "write", reg, {"slot": slots_probe[0], "key": "zz",
                                            "sign": -1})
    for j in j_probe:
        check(f"navmap(j={j})", "navmap", reg, {"j": j})
        check(f"navigate(j={j})", "navigate", reg, {"j": j})
    one_hot = [0] * reg.dim
    one_hot[1] = 1
    check("is_navigable(e1)", "is_navigable", reg, {"direction": one_hot},
          expect_dispatch=(reg.dim <= 64))
    check("carry(n=3)", "carry", reg, {"overflow_bits": [1, 0, 1, 1]})
    check("correct", "correct", reg, {"codeword": [1, 0, 1, 1, 0, 1, 0]})
    check("couple_working", "couple_working", reg, {"vals": [1.0, 2.0]},
          expect_dispatch=False)
    check("uncouple_working", "uncouple_working", reg,
          {"word": [1.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}, expect_dispatch=False)
    check("norm", "norm", reg, {}, expect_dispatch=False)
    check("conjugate", "conjugate", reg, {}, expect_dispatch=False)


# ── dim 16, the subsuming spelling ──────────────────────────────────────────
r16 = CDRegister(16, D=256, namespace="SEDENION", coupling=True,
                 error_correction=True)
r16.write(0, "alpha")
r16.write(3, "beta", sign=-1)
r16.write(6, "gamma")
suite("dim 16 / SEDENION / flags on", r16, [0, 3, 6], [0, 1, 7, 15])

# ── dim 256, slots straddling the 100 boundary ──────────────────────────────
r256 = CDRegister(256, D=256)
for sl, key, sg in [(0, "a", 1), (7, "b", -1), (99, "c", 1), (100, "d", -1),
                    (128, "e", 1), (255, "f", -1)]:
    r256.write(sl, key, sign=sg)
suite("dim 256 / CD256 default ns / flags off", r256, [0, 99, 100, 255],
      [0, 1, 100, 255])

# ── dim= only: every scalar default resolved identically ───────────────────
print("\n== dim-only field state (D / namespace / flags all absent) ==")
bare = {"dim": 8}
d, got = run_c("navigate", bare, {"j": 1})
inst = CatalogClass(json.loads(json.dumps({})) or None, ) if False else \
    make_class("CDRegister")(dim=8)
pure = inst.navigate(j=1)
exp = norm(pure.fields)
print("  navigate dispatched:", d, " result==pure:", got and got["result"] == exp)
if not d or got["result"] != exp:
    fails.append(("dim-only navigate", f"{got} != {exp}"))

d2, got2 = run_c("materialize", {"dim": 8, "slots": {"0": ["k", 1]}}, {})
inst2 = make_class("CDRegister")(dim=8, slots={0: ("k", 1)})
exp2 = norm(inst2.materialize())
print("  materialize dispatched:", d2, " result==pure:", got2 and got2["result"] == exp2)
if not d2 or got2["result"] != exp2:
    fails.append(("dim-only materialize", "mismatch"))

# ── a namespace too long for the address buffer must DEFER, not truncate ───
print("\n== namespace over the address-buffer cap ==")
longns = "N" * 59
d3, _ = run_c("materialize", {"dim": 4, "D": 256, "namespace": longns,
                              "slots": {"0": ["k", 1]}}, {})
print("  59-char namespace dispatched:", d3, "(expect False = declared DEFER)")
if d3:
    fails.append(("long namespace", "dispatched; must DEFER"))
d4, got4 = run_c("materialize", {"dim": 4, "D": 256, "namespace": "N" * 57,
                                 "slots": {"0": ["k", 1]}}, {})
inst4 = make_class("CDRegister")(dim=4, D=256, namespace="N" * 57,
                                 slots={0: ("k", 1)})
print("  57-char namespace dispatched:", d4,
      " result==pure:", got4 and got4["result"] == norm(inst4.materialize()))
if not d4 or got4["result"] != norm(inst4.materialize()):
    fails.append(("57-char namespace", "mismatch/defer"))

print("\nFAILURES:", len(fails))
for f in fails:
    print("  !", f[0], "::", f[1][:400])
sys.exit(1 if fails else 0)
