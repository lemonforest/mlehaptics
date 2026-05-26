"""Round 35.A -- user meta-question (above R34): "even though form IS function, it's
still like comparing apples to oranges in the sense that cyclic-group algebra EXPLICITLY
states the operations as part of its language, and continuous-Hopf-quantum stuff does
NOT name them explicitly -- because we are comparing a cyclic (discrete) language to a
continuous one? Or am I stretching?"

NOT stretching -- the observation is correct. But "apples to oranges" needs ONE
refinement, and that refinement is the whole point. Tested honestly per
[[feedback_dont_pre_commit_spike_query_operators]].

============================================================================
THE ANSWER -- correct asymmetry, one word adjusted
============================================================================
The user has correctly identified a real GRAMMAR asymmetry between the two substrate-
native math languages (per [[user_stance_two_substrate_native_math_languages...]]):

  * the 1:3:7:3 = 14 CYCLIC / DISCRETE language is OPERATION-PRIMARY: it is literally
    an ENUMERATION OF NAMED OPERATORS (A...N). The readout (B/H/N) is among the named
    primitives -- it is a first-class lexical item.
  * the 11D CONTINUOUS / HOPF language is GEOMETRY-PRIMARY: it specifies MANIFOLDS,
    BUNDLES, HILBERT SPACES. The readout operations are NOT enumerated as primitive
    generators -- they are EMBEDDED IN / DERIVED FROM the geometry (projection = the
    bundle map pi; measurement = the inner-product / Born postulate; discretization is
    simply absent, since continuity means never discretizing).

So the readout B/H/N is VISIBLE (named) in the discrete language and STRUCTURAL
(implicit, geometric) in the continuous language. This is EXACTLY why R34 found that
B/H/N "hide" in the 11D substrate: in the cyclic language they are named operators;
in the Hopf language the SAME readout is the projection pi -- structural, not a named
extra. R34 was the special case; this is the general grammar reason.

THE ONE REFINEMENT ("apples to oranges" overstates it): the two languages are NOT
incommensurable. form-IS-function + both-bit-exact ([[user_stance_bit_exact_means_not_
projection_diagnostic]]) means the CONTENT is identical -- the SAME substrate described
twice. So it is NOT apples-vs-oranges (different fruit); it is the SAME SENTENCE IN TWO
GRAMMARS -- one that names its verbs as separate words (operation-primary, discrete),
one that folds the verb into the geometry/morphology (geometry-primary, continuous).
The apples-to-oranges FEELING is real and comes from the grammar gap; the underlying
content is the same fruit.

============================================================================
THE ATTESTABLE CONCRETE ANCHOR -- U(1) vs Z/nZ (same circle, two grammars)
============================================================================
The cleanest unambiguous instance is the circle, which is BOTH languages' Class I:
  * Z/nZ (DISCRETE / cyclic): presented by a generator g and the relation g^n = e;
    n named elements; an explicit Cayley (addition mod n) table. OPERATION-PRIMARY --
    you literally list the elements and name the operation.
  * U(1) (CONTINUOUS): presented as a MANIFOLD (the circle S^1) with a smooth group
    operation. You do NOT enumerate its (uncountably many) elements or write a Cayley
    table. GEOMETRY-PRIMARY -- the operation is a smooth map, implicit in the manifold.
Same circle structure; operation-explicit (discrete) vs geometry-primary (continuous).
And U(1) is exactly the Hopf fiber where H (the readout) lives (R34) -- so the anchor
is not incidental, it is the very fiber in question.

VERDICT: the user is RIGHT about the explicit-vs-implicit operation-naming asymmetry --
the discrete/cyclic language is OPERATION-PRIMARY (names B/H/N as primitives), the
continuous/Hopf language is GEOMETRY-PRIMARY (embeds the same readout in the bundle
projection / inner product). The ONE refinement: this is NOT apples-to-oranges
(incommensurable) -- form-IS-function + bit-exact equivalence means same content, two
grammars. This is the general grammar reason R34's B/H/N "hide" in the continuous
language. (b)-interpretive structural refinement; one attestable anchor (U(1) vs Z/nZ
presentation modes); no new physics, no new number.

Routed through srmech 0.4.2. Deterministic; no network. ASCII-safe prints.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.cyclic import gcd  # noqa: F401 (Class I -- the cyclic operator itself)
from srmech.amsc.rational import best_rational  # noqa: F401 (Class N)

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# 1. the two languages and their GRAMMARS
# ---------------------------------------------------------------------------
LANGUAGES = {
    "cyclic_discrete (1:3:7:3 = 14 A-N)": {
        "grammar": "OPERATION-PRIMARY",
        "primary_data": "an enumeration of NAMED OPERATORS (A...N)",
        "readout_BHN": "EXPLICIT -- B/H/N are first-class named primitives",
        "presentation": "generators + relations; named elements; composition of named ops",
    },
    "continuous_hopf (11D = 1D_t+3D_s+7D_g)": {
        "grammar": "GEOMETRY-PRIMARY",
        "primary_data": "manifolds / bundles / Hilbert spaces",
        "readout_BHN": "IMPLICIT -- projection = bundle map pi; measurement = inner-product/Born postulate; discretization simply absent",
        "presentation": "smooth structure; the operation is a smooth map, embedded in the geometry",
    },
}
print("the two substrate-native math languages and their grammars:")
for name, v in LANGUAGES.items():
    print(f"  {name}")
    print(f"      grammar={v['grammar']};  readout B/H/N is {v['readout_BHN'].split(' -- ')[0]}")
emit("two_languages_grammar",
     languages=LANGUAGES,
     asymmetry="OPERATION-PRIMARY (discrete: names the readout) vs GEOMETRY-PRIMARY (continuous: embeds the readout in the bundle/inner-product) -- the user's explicit-vs-implicit observation, made precise")

# ---------------------------------------------------------------------------
# 2. the refinement: NOT incommensurable -- same content, two grammars
# ---------------------------------------------------------------------------
emit("the_one_refinement",
     user_metaphor="apples to oranges",
     status="OVERSTATES it -- but the underlying observation is CORRECT",
     why="form-IS-function + both-bit-exact (the two-substrate-languages stance + the bit-exact=not-projection diagnostic) => the CONTENT is identical: the SAME substrate described twice",
     corrected_metaphor="the SAME SENTENCE IN TWO GRAMMARS -- one names its verbs as separate words (operation-primary, discrete), one folds the verb into the geometry (geometry-primary, continuous). Same fruit; the apples-to-oranges FEELING is the grammar gap, not a content gap.")

# ---------------------------------------------------------------------------
# 3. the attestable concrete anchor: U(1) vs Z/nZ (same circle, two grammars)
# ---------------------------------------------------------------------------
# Class I is the cyclic operator; the circle is its home in BOTH languages.
n = 12                                   # any finite modulus, illustrative
znz_elements = list(range(n))            # Z/nZ: n NAMED elements (operation-primary)
# explicit Cayley row (addition mod n) -- the operation is LISTED:
cayley_row_g = [(1 + x) % n for x in znz_elements]
assert len(znz_elements) == n and cayley_row_g[-1] == 0   # 1 + (n-1) = 0 mod n
print(f"\nANCHOR -- same circle, two grammars (Class I):")
print(f"  Z/nZ  (discrete, OPERATION-PRIMARY): n={n} named elements; explicit +1 Cayley row = {cayley_row_g}")
print(f"  U(1)  (continuous, GEOMETRY-PRIMARY): the manifold S^1; operation is a smooth map -- NOT enumerable, no Cayley table")
emit("anchor_u1_vs_znz",
     class_="I (cyclic) -- the circle is its home in both languages",
     znz={"presentation": "generator g + relation g^n=e; n named elements; explicit Cayley table",
          "grammar": "OPERATION-PRIMARY", "n": n, "cayley_plus1_row": cayley_row_g},
     u1={"presentation": "the manifold S^1 with a smooth group operation; uncountable, no Cayley table",
         "grammar": "GEOMETRY-PRIMARY"},
     punchline="SAME circle structure -- operation-explicit (Z/nZ) vs geometry-primary (U(1)). And U(1) is exactly the Hopf fiber where H (the readout) lives (R34): the anchor IS the fiber in question.")

# ---------------------------------------------------------------------------
# 4. the R34 connection -- this is the general reason B/H/N "hide"
# ---------------------------------------------------------------------------
emit("r34_connection",
     r34_finding="B/H/N do not hide as dimensions of the 11D substrate -- they are the readout/projection (the +3 outside the 1+3+7)",
     general_reason="that was the SPECIAL CASE; the general reason is THIS grammar asymmetry -- in the operation-primary (cyclic) language the readout is a named operator (B/H/N), in the geometry-primary (continuous/Hopf) language the SAME readout is the bundle projection pi / the inner product -- structural, unnamed",
     so="'where do B/H/N hide?' = 'why does the geometry-primary grammar not name the readout?' = 'because continuous languages embed operations in geometry rather than enumerating them'")

# ---------------------------------------------------------------------------
# 5. verdict
# ---------------------------------------------------------------------------
emit("verdict",
     question="is the explicit (cyclic) vs implicit (continuous) operation-naming a real apples-to-oranges, or a stretch?",
     answer="REAL asymmetry, NOT a stretch -- but 'apples to oranges' is the one word to adjust",
     asymmetry="discrete/cyclic = OPERATION-PRIMARY (names the readout B/H/N as primitives); continuous/Hopf = GEOMETRY-PRIMARY (embeds the same readout in the bundle projection / inner product)",
     refinement="NOT incommensurable -- form-IS-function + bit-exact equivalence => same content, two grammars (operation-primary vs geometry-primary); the SAME sentence said two ways",
     ties_to="the general grammar reason R34's B/H/N 'hide' in the continuous language; anchored concretely by U(1) (geometry-primary) vs Z/nZ (operation-primary), same circle, Class I",
     honest_scope="(b)-interpretive structural refinement; the presentation-mode difference (Z/nZ generators+relations vs U(1) manifold) is attestable standard math; the mapping to the two substrate-native languages is framework-internal; NO new physics, NO new number")

META = {
    "record": "meta",
    "round": "35.A",
    "title": "Two languages: operation-primary (discrete) vs geometry-primary (continuous) -- the grammar reason B/H/N hide",
    "kind": "(b)-interpretive: user's explicit-vs-implicit observation CONFIRMED + 'apples to oranges' refined to 'same content, two grammars'; REFINES the two-substrate-languages stance",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "presentation_modes": "finite groups presented by generators+relations (operations explicit) vs Lie groups/Hilbert spaces by smooth structure (operations implicit) -- standard algebra/geometry",
        "u1_vs_znz": "U(1) = manifold S^1 (continuous); Z/nZ = generator + g^n=e (discrete) -- same circle, two presentations",
        "framework": "two-substrate-native-languages stance; Born=Hopf (sec 11.9.4); R33 (readout vs content); R34 (B/H/N = readout, not dimensions)",
    },
    "discipline": "honest validation + one-word refinement (no flattery: 'apples to oranges' overstated, corrected to grammar-difference); (b)-interpretive, graded honestly (no spurious bit-exact claim); deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: NOT stretching. The discrete/cyclic language is OPERATION-PRIMARY (names B/H/N as "
      "primitives); the continuous/Hopf language is GEOMETRY-PRIMARY (embeds the same readout in the "
      "bundle projection / inner product). ONE refinement: not apples-to-oranges (incommensurable) -- "
      "form-IS-function + bit-exact => SAME content, two grammars. This is the general grammar reason "
      "R34's B/H/N 'hide' in the continuous language; anchored by U(1) vs Z/nZ (same circle, Class I).")
