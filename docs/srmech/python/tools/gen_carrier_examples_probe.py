#!/usr/bin/env python3
"""Dev-time PROBE that constructs each CARRIER the canonical way + captures a
real executed construction example {"construct": <expr>, "yields": <repr>}.

Prefers the canonical factory/op (the "better example", e.g. Mat via
dense_laplacian, One via the_one) over a raw buffer constructor; falls back to
a direct constructor, else an honest producing-op usage snippet (never a
fabricated result). NOT the SSoT — the human reviews the emitted skeleton and
folds it into carrier_schema._CARRIERS. Run from docs/srmech/python.
"""
from __future__ import annotations
import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import srmech  # noqa: F401,E402
from srmech.amsc.tool_schema import warmup_all  # noqa: E402
warmup_all()

# a namespace of the imports the construction expressions use
import array  # noqa: E402
from fractions import Fraction  # noqa: E402
from srmech.amsc import Poly, TriPoly, ThetaSum  # noqa: E402
from srmech.amsc.carrier_ladder import BiPoly, QPoly, QBiPoly  # noqa: E402
from srmech.amsc.apagodu_zeilberger import Q  # noqa: E402
from srmech.amsc.hdc import Mat, HV  # noqa: E402
from srmech.amsc.coupling import Vec  # noqa: E402
from srmech.amsc.carrier_spectrum import CarrierSpectrum, EllMonomial, EllRatio  # noqa: E402
from srmech.amsc.ellbase import Theta  # noqa: E402  (rc363: the elliptic ATOM)
from srmech.amsc.riemann_theta_multisum import ThetaBracketSum  # noqa: E402
from srmech.amsc.harmonic_maass import MockQSeries, UnaryTheta, HarmonicMaass  # noqa: E402
from srmech.amsc import laplacian as _lap  # noqa: E402
from srmech.amsc import hdc as _hdc  # noqa: E402
from srmech.amsc.cascade import the_one, sedenion_register, cd_register  # noqa: E402

_NS = dict(globals())
_NS.update(dict(array=array, Fraction=Fraction, Q=Q, Poly=Poly, BiPoly=BiPoly,
                TriPoly=TriPoly, QPoly=QPoly, QBiPoly=QBiPoly, Mat=Mat, Vec=Vec,
                HV=HV, EllMonomial=EllMonomial, EllRatio=EllRatio,
                ThetaSum=ThetaSum, ThetaBracketSum=ThetaBracketSum,
                Theta=Theta, CarrierSpectrum=CarrierSpectrum,
                MockQSeries=MockQSeries, UnaryTheta=UnaryTheta,
                HarmonicMaass=HarmonicMaass, the_one=the_one,
                sedenion_register=sedenion_register, cd_register=cd_register,
                dense_laplacian=_lap.dense_laplacian,
                jacobi_eigvals=_lap.jacobi_eigvals,
                fiedler_vector=_lap.fiedler_vector, hdc=_hdc))

# carrier -> the canonical construction expression (evaluated in _NS).
# Cayley-Dickson scalar carriers (complex/quaternion/octonion/sedenion) are
# represented AS float sequences per the schema — a plain literal is the honest
# construction, so those are supplied as snippet-only below.
_CONSTRUCT = {
    "Poly": "Poly([Q(1), Q(2), Q(3)])",
    "BiPoly": "BiPoly([Poly([Q(1), Q(2)]), Poly([Q(0), Q(1)])])",
    "TriPoly": "TriPoly([BiPoly([Poly([Q(1)])])])",
    "QPoly": "QPoly([Poly([Q(1)]), Poly([Q(1)])], x_low=0)",
    "QBiPoly": "QBiPoly([QPoly([Poly([Q(1)])])])",
    "Fraction": "Fraction(3, 4)",
    "Q": "Q(3, 4)",
    "Mat": "dense_laplacian(4, [(0, 1), (1, 2), (2, 0), (2, 3)], [1.0, 1.0, 1.0, 1.0])",
    "Vec": "fiedler_vector(dense_laplacian(4, [(0,1),(1,2),(2,0),(2,3)], [1.0]*4))",
    "HV": "hdc.klein4_bind(hdc.HV(array.array('B', [1,2,3,0])), hdc.HV(array.array('B', [3,2,1,0])))",
    "EllMonomial": "EllMonomial(Q(1), {'q': 2})",
    # rc363 (`#T1046`): the elliptic ATOM, registered when the C3 use-derivation
    # measured five ops accepting it directly. x is the summation variable
    # (x = qⁿ), so θ(x; p) is the smallest genuine theta factor.
    "Theta": "Theta(EllMonomial(Q(1), {'x': 1}))",
    # rc363: the READ the carrier_spectrum op produces. Built from the smallest
    # element that has a non-trivial σ-spectrum, so `yields` shows both channels.
    "CarrierSpectrum": "CarrierSpectrum(EllRatio.theta(Theta(EllMonomial(Q(1), {'x': 1}))))",
    "MockQSeries": "MockQSeries('qpoly', Q(1), [(0, 1), (1, 1)])",
    "One": "the_one(1, 1, 4, w=(1, 0, 1))",
    "ThetaSum": "ThetaSum(terms=[(Q(1), EllMonomial(Q(1), {}), [])])",
    "ThetaBracketSum": "ThetaBracketSum({(('u', 1),): Q(1)})",
    "SedenionRegister": "sedenion_register(D=256)",
    # dim 32 DELIBERATELY, not 16: the whole point of CDRegister is that the slot
    # count is a PARAMETER, and an example at n=16 would document it as a sedenion
    # register with extra steps — the reader would learn nothing the
    # SedenionRegister row above does not already say. 32 is also the live
    # research need (𝕋, where composition fails for most generic pairs while
    # addressing is intact), and it is well inside CD_MAX_DIM=64.
    "CDRegister": "cd_register(32, D=256)",
}
# carriers whose honest example is a usage snippet (float-seq scalars, or a
# constructor that needs domain objects better shown by its producing op).
_SNIPPET = {
    "float": "1.0  # the FPU last-mile scalar; exact carriers collapse to float only at the observed-frame read-out",
    "complex": "complex(1.0, 2.0)  # rung-2 (re, im) scalar; the spectral read-out",
    "quaternion": "(1.0, 2.0, 3.0, 4.0)  # length-4 (1,i,j,k) seq → qm.quaternion.*",
    "octonion": "(1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)  # length-8 e0..e7 → qm.octonion.* / octonion DFT",
    "sedenion": "(0.0,)*16  # length-16 e0..e15; past-Hurwitz zero-divisor demonstrator",
    "int": "1  # Python arbitrary-precision int, mirrored by srmech_bigint in C",
    "EllRatio": "elliptic_gosper(...) operand — prefactor·∏(num θ)/∏(den θ) over an EllMonomial",
    "UnaryTheta": "UnaryTheta(char, j, a, b, D)  # the SHADOW slot of a harmonic-Maass pair",
    "HarmonicMaass": "HarmonicMaass(hol=MockQSeries(...), shadow=UnaryTheta(...))  # (hol, shadow) pair",
}

# Fully HAND-AUTHORED rows, applied last and never derived. The module docstring
# has claimed since rc241 that "hand-curated construction examples ... are
# preserved"; it was not true — `main()` rewrites the whole file from the two
# dicts above, so a row added by hand to `_carrier_examples.py` vanished on the
# next regeneration with nothing going red. Measured at rc363: regenerating for
# the two new carriers silently DROPPED the rc362 `Qalg` row, whose `yields`
# carries the zero-divisor/irrationality witness a bare repr cannot show. This
# dict is where such a row lives so the claim is structurally true.
_CURATED = {
    "Qalg": {
        "construct": "Qalg.alpha([-2, 0, 1])  # a root of x**2 - 2, carried EXACTLY",
        "yields": ("Qalg(degree=2, coords=(Q(0, 1), Q(1, 1)), m=x**2-2); "
                   "(α*α).as_rational() == Q(2, 1) and "
                   "α.is_rational() is False"),
    },
}


def _rs(v):
    r = repr(v)
    return r if len(r) <= 160 else r[:157] + "..."


def build_examples(apply_curated: bool = True, quiet: bool = False) -> dict:
    """The CARRIER_EXAMPLES payload, built but not written.

    Extracted from ``main()`` at rc363 so a test can call it. A generator whose
    only entry point WRITES cannot be checked for idempotence without a
    filesystem side effect, and the rc363 finding here — that the curated rows
    this module promised to preserve were being dropped on every run — is
    exactly the kind of defect an idempotence check catches. The three layers
    are applied in order, LAST WINS: derived constructions, then snippets, then
    the hand-authored ``_CURATED`` rows.

    ``apply_curated=False`` builds WITHOUT the last layer. It exists so
    ``tests/test_tool_docs_coverage_rc240.py`` can prove the layer does
    something: a preservation test that cannot observe the un-preserved state
    is not a measurement of preservation."""
    def _say(msg):
        if not quiet:
            print(msg)

    out = {}
    for name, expr in _CONSTRUCT.items():
        try:
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                res = eval(expr, _NS)  # noqa: S307 dev tool
            r = _rs(res)
            # an uninformative default object repr adds nothing — construct-only.
            out[name] = ({"construct": expr} if r.startswith("<")
                         else {"construct": expr, "yields": r})
            _say(f"OK   {name:16} -> {r[:52]}")
        except Exception as e:  # noqa: BLE001
            _say(f"FAIL {name:16} {type(e).__name__}: {e}")
    for name, snip in _SNIPPET.items():
        out[name] = {"construct": snip}
        _say(f"snip {name:16} {snip[:52]}")
    if apply_curated:
        for name, row in _CURATED.items():
            out[name] = dict(row)
            _say(f"hand {name:16} {row['construct'][:52]}")
    return out


def main():
    out = build_examples()

    import json
    lines = [
        '"""_carrier_examples.py — GENERATED by tools/gen_carrier_examples_probe.py.',
        "DO NOT EDIT auto rows by hand (regenerate); hand-curated construction",
        "examples may be added here and are preserved. The rc241 (#839) carrier-side",
        "peer of _tool_docs.py: a per-carrier CONSTRUCTION example (how to build/obtain",
        "the carrier), merged into carrier_schema()'s per-carrier payload so it flows",
        'through the srmech_carrier_registry const table + its sha256 attestation."""',
        "from __future__ import annotations",
        "",
        "from typing import Any, Dict",
        "",
        "CARRIER_EXAMPLES: Dict[str, Dict[str, Any]] = {",
    ]
    for name in sorted(out):
        lines.append(f"    {json.dumps(name)}: "
                     f"{json.dumps(out[name], sort_keys=True, ensure_ascii=False)},")
    lines.append("}")
    lines.append("")
    dest = Path(__file__).resolve().parent.parent / "srmech" / "amsc" / "_carrier_examples.py"
    dest.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"\nwrote {dest} — {len(out)} carrier examples "
          f"({sum(1 for v in out.values() if 'yields' in v)} executed)")


if __name__ == "__main__":
    main()
