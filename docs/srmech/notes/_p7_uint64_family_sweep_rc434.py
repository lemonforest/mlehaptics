"""`#T1130` P7 — sweep the "past uint64 it raises" FAMILY, and execute every member.

``cyclic_gcd`` was found by candidate enumeration.  The root cause is not the
op, it is a CLASS: rc167 (`#765`) deliberately removed ``gcd``'s compiled-in
uint64 rejection ("no compiled-in caps"), and every piece of prose that had
already described the cap became false.  A per-site fix leaves the rest of the
class unfound, so this sweeps the whole tree for the claim and fires it.

Instrument: find every op whose DOCSTRING or REGISTRY prose asserts a uint64 /
2**64 rejection, then call it with an out-of-uint64 operand and record whether
it actually raises.  A claim that survives execution is TRUE prose about a real
cap; one that does not is a member of the family.

Also settles the P6 rows that came back NOT_RAISED, by printing the registry
sentence that carries the claim, so a probe-inadequacy is not mis-reported as
a package defect.
"""

from __future__ import annotations

import inspect
import json
import os
import re
import sys

REPO = "/mnt/d/GitHub/mlehaptics"
PKG = os.path.join(REPO, "docs/srmech/python")
OUT = os.path.join(REPO, "docs/srmech/notes/_p7_uint64_family_sweep_rc434.ndjson")

sys.path.insert(0, PKG)

CAP_CLAIM = re.compile(
    r"(past uint64|past 2\*\*64|beyond uint64|exceeds uint64|exceeding the uint64|"
    r"outside uint64|bounded by uint64|uint64 (?:range|cap|ceiling))",
    re.IGNORECASE,
)
RAISE_WORD = re.compile(r"rais|reject|ValueError|OverflowError", re.IGNORECASE)

OVERSIZE = 2 ** 64 + 1

# how to call each op with ONE out-of-uint64 operand; None = no safe probe
PROBE_ARGS = {
    "srmech.math.cyclic.gcd": ((OVERSIZE, 5), {}),
    "srmech.cascade.cyclic_gcd": ((OVERSIZE, 5), {}),
    "srmech.math.cyclic.lcm": ((OVERSIZE, 5), {}),
    "srmech.math.cyclic.mod_add": ((OVERSIZE, 1, 7), {}),
    "srmech.math.cyclic.mod_mul": ((OVERSIZE, 1, 7), {}),
    "srmech.math.cyclic.mod_pow": ((OVERSIZE, 1, 7), {}),
    "srmech.math.cyclic.mod_inv": ((OVERSIZE, 7), {}),
    "srmech.math.cyclic.mod_mul_wide": ((OVERSIZE, 1, 7), {}),
    "srmech.cascade.cyclic_mod_add": ((OVERSIZE, 1, 7), {}),
    "srmech.cascade.cyclic_mod_mul": ((OVERSIZE, 1, 7), {}),
    "srmech.cascade.cyclic_mod_pow": ((OVERSIZE, 1, 7), {}),
    "srmech.cascade.cyclic_mod_inv": ((OVERSIZE, 7), {}),
    "srmech.cascade.cyclic_mod_mul_wide": ((OVERSIZE, 1, 7), {}),
    "srmech.math.primes.factor": ((OVERSIZE,), {}),
    "srmech.math.primes.cyclic_period": ((OVERSIZE, 7), {}),
    "srmech.math.rational.continued_fraction": ((OVERSIZE, 7), {}),
    "srmech.math.rational.best_rational": ((OVERSIZE, 7, 100), {}),
}


def resolve(dotted: str):
    parts = dotted.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        try:
            mod = __import__(".".join(parts[:cut]), fromlist=["*"])
        except Exception:
            continue
        obj = mod
        try:
            for a in parts[cut:]:
                obj = getattr(obj, a)
        except AttributeError:
            continue
        return obj
    raise ImportError(dotted)


def claim_sentences(text: str) -> list[str]:
    out = []
    for sent in re.split(r"(?<=[.;])\s+", text or ""):
        if CAP_CLAIM.search(sent) and RAISE_WORD.search(sent):
            out.append(sent.strip()[:300])
    return out


def main() -> int:
    import srmech
    from srmech import _native
    from srmech.introspect.tool_schema import get_tool_schema

    fh = open(OUT, "w", encoding="utf-8")

    def emit(rec):
        fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    emit(
        {
            "record": "meta",
            "srmech_file": srmech.__file__,
            "srmech_version": srmech.__version__,
            "has_native": bool(_native.HAS_NATIVE),
            "oversize_operand": str(OVERSIZE),
        }
    )

    schema = get_tool_schema()
    tools = {t.name: t for t in schema.tools}

    # ---- who CLAIMS a uint64 rejection, on which surface -------------------
    claimants: dict[str, dict] = {}
    for name, t in tools.items():
        reg_text = " ".join(x for x in (t.summary, t.explanation) if x)
        reg_claims = claim_sentences(reg_text)
        try:
            doc = inspect.getdoc(resolve(name)) or ""
        except Exception:
            doc = ""
        doc_claims = claim_sentences(doc)
        if reg_claims or doc_claims:
            claimants[name] = {
                "registry_claims": reg_claims,
                "docstring_claims": doc_claims,
            }

    emit({"record": "claimant_summary", "n_claimants": len(claimants)})

    # ---- execute each claimant with an out-of-uint64 operand ---------------
    tally: dict[str, int] = {}
    for name in sorted(claimants):
        rec = {"record": "claimant", "op": name}
        rec.update(claimants[name])
        spec = PROBE_ARGS.get(name)
        if spec is None:
            rec["outcome"] = "UNSUPPORTED"
            rec["detail"] = "no safe out-of-uint64 probe authored for this signature"
            try:
                rec["signature"] = str(inspect.signature(resolve(name)))
            except Exception:
                pass
        else:
            args, kwargs = spec
            try:
                fn = resolve(name)
                v = fn(*args, **kwargs)
                rec["outcome"] = "CLAIM_FALSE_NO_RAISE"
                rec["returned_type"] = type(v).__name__
                rec["returned_repr"] = repr(v)[:120]
            except BaseException as exc:  # noqa: BLE001
                rec["observed"] = type(exc).__name__
                rec["message"] = str(exc)[:180]
                rec["outcome"] = "CLAIM_TRUE_RAISES"
        tally[rec["outcome"]] = tally.get(rec["outcome"], 0) + 1
        emit(rec)

    emit({"record": "tally", "by_outcome": tally})

    # ---- settle P6's NOT_RAISED rows by showing the actual claim -----------
    for name in (
        "srmech.signal_processing.cascade_dispatcher.resolve_path",
        "srmech.signal_processing.path_registry.has_path",
        "srmech.biology.genome.kernel_pack",
        "srmech.signal_processing.stft",
        "srmech.signal_processing.cross_spectral",
        "srmech.signal_processing.rfft",
        "srmech.math.template.render",
        "srmech.math.rational.log",
        "srmech.physics.qm.propagators.feynman_scalar_propagator",
        "srmech.cascade.compose.parse_catalog_chains",
    ):
        t = tools.get(name)
        if t is None:
            emit({"record": "p6_settle", "op": name, "in_registry": False})
            continue
        blob = " ".join(x for x in (t.summary, t.explanation) if x)
        sents = [
            s.strip()[:300]
            for s in re.split(r"(?<=[.;])\s+", blob)
            if re.search(r"Error|raise|Warning", s)
        ]
        emit(
            {
                "record": "p6_settle",
                "op": name,
                "in_registry": True,
                "claim_sentences": sents[:4],
            }
        )

    fh.close()
    print(f"wrote {OUT}  tally={tally}  claimants={len(claimants)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
