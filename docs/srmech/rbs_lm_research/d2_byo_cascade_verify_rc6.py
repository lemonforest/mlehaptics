"""d2_byo_cascade_verify_rc6.py — end-to-end acceptance test of the F289-D2 bring-your-own
cascade-TOML mechanism, landed in srmech 0.7.0rc6 (SRMECH_CASCADE_PATH + pure-TOML composite resolver).

F289 D2 asked for: a user descriptor whose behaviour IS a validated chain of already-named A-N/cascade
ops (pure TOML, no Python), discoverable via SRMECH_CASCADE_PATH, validated LOUDLY at load, surfaced
with a provenance flag (user/B-tier, not srmech/A-tier). This checks all four:

  P  POSITIVE: author a user composite (magnitude ∘ magnitude) on SRMECH_CASCADE_PATH; confirm it
     loads, appears in list_cascade_ops(), resolves via lookup_cascade_op, and RUNS (no Python op written).
  Pr PROVENANCE: the user op is tagged _provenance "user:<sha256>" (B-tier), NOT "srmech" (A-tier).
  N1 NEGATIVE (unknown op): a composite referencing a non-existent op FAILS LOUD at load (ValueError).
  N2 NEGATIVE (shadow): a user op-name that shadows a shipped op FAILS LOUD at load (ValueError).

No package edits (writes only to a temp user-catalog dir). Scope: tooling-verification; benign.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def write_toml(d, fname, body):
    p = os.path.join(d, fname)
    with open(p, "w") as f:
        f.write(body)
    return p


def fresh_catalog(envdir):
    """point SRMECH_CASCADE_PATH at envdir and force a cache-clear reload."""
    os.environ["SRMECH_CASCADE_PATH"] = envdir
    from srmech.dsl import _catalog
    _catalog.load_catalog.cache_clear()
    return _catalog


def main():
    import srmech
    from srmech import dsl
    print(f"=== F289-D2 BYO cascade-TOML acceptance test (srmech {srmech.__version__}) ===\n")
    tmp = tempfile.mkdtemp(prefix="d2_user_catalog_")

    # ---- P: a valid user composite = pure TOML, no Python ----
    write_toml(tmp, "magnitude_twice.toml", '''
[cascade]
name = "magnitude_twice"
class_composition = "K"
purpose = "user composite: magnitude applied twice (idempotent demo; pure TOML, no Python)"

[[composite.stage]]
op = "magnitude"

[[composite.stage]]
op = "magnitude"
''')
    cat = fresh_catalog(tmp)
    ops = dsl.list_cascade_ops()
    present = "magnitude_twice" in ops
    print(f"[P ] user composite 'magnitude_twice' in list_cascade_ops(): {present}")
    runner = dsl.lookup_cascade_op("magnitude_twice")
    out = runner(-5.0)                       # magnitude(magnitude(-5.0)) = 5.0
    print(f"[P ] lookup_cascade_op runs it (no Python op authored): runner(-5.0) = {out}  "
          f"-> {'OK' if abs(out - 5.0) < 1e-12 else 'WRONG'}")

    # ---- Pr: provenance is user/B-tier, not srmech/A-tier ----
    prov = dsl.get_descriptor("magnitude_twice").get("_provenance", "<none>")
    shipped_prov = dsl.get_descriptor("magnitude").get("_provenance", "<none>")
    print(f"[Pr] provenance: user op = {prov!r}  ;  shipped 'magnitude' = {shipped_prov!r}  "
          f"-> {'OK (B-tier user, A-tier srmech)' if prov.startswith('user') and 'srmech' in shipped_prov else 'CHECK'}")

    # ---- N1: composite referencing an unknown op fails LOUD at load ----
    tmp2 = tempfile.mkdtemp(prefix="d2_bad_unknown_")
    write_toml(tmp2, "bad_unknown.toml", '''
[cascade]
name = "bad_unknown"
purpose = "references a non-existent op; must fail loud at load"

[[composite.stage]]
op = "this_op_does_not_exist"
''')
    cat2 = fresh_catalog(tmp2)
    try:
        cat2.load_catalog()
        n1 = "DID NOT RAISE (validation gap!)"
    except ValueError as ex:
        n1 = f"RAISES ValueError (fail-loud): {str(ex)[:70]}"
    print(f"\n[N1] unknown-op composite at load: {n1}")

    # ---- N2: a user op-name shadowing a shipped op fails LOUD ----
    tmp3 = tempfile.mkdtemp(prefix="d2_bad_shadow_")
    write_toml(tmp3, "shadow.toml", '''
[cascade]
name = "magnitude"
purpose = "shadows the shipped 'magnitude'; must fail loud at load"

[[composite.stage]]
op = "magnitude"
''')
    cat3 = fresh_catalog(tmp3)
    try:
        cat3.load_catalog()
        n2 = "DID NOT RAISE (shadow allowed!)"
    except ValueError as ex:
        n2 = f"RAISES ValueError (fail-loud): {str(ex)[:70]}"
    print(f"[N2] shadowing-shipped-op at load: {n2}")

    # ---- cleanup env ----
    os.environ.pop("SRMECH_CASCADE_PATH", None)
    cat.load_catalog.cache_clear()

    ok = (present and abs(out - 5.0) < 1e-12 and prov.startswith("user")
          and "RAISES" in n1 and "RAISES" in n2)
    print(f"\n  === F289-D2 BYO cascade-TOML: {'FULLY WORKING (config-not-code, validated, provenance-flagged)' if ok else 'CHECK FAILURES ABOVE'} ===")


if __name__ == "__main__":
    main()
