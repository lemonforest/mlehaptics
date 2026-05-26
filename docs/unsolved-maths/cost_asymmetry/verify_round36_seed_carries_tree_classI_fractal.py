"""Round 36.A -- the seed-carries-the-tree (Class I) reconciliation + the apple tree as
the concrete figurative anchor for the substrate's fractal geometry.

Follows R35 ("apples to apple trees"): R35 left a wrinkle -- tree-vs-apple reads
PART-WHOLE, but the two substrate-native languages are bit-exact EQUIVALENT. R35's
rescue: the apple carries a SEED (the whole tree's generative program), and the seed/
codon is Class I cyclic. This round formalizes that rescue and shows it IS the fractal
mechanism. Tested honestly per [[feedback_dont_pre_commit_spike_query_operators]].

============================================================================
PART 1 -- the seed-carries-the-tree (Class I) reconciliation
============================================================================
How can a FINITE DISCRETE object (apple / named operators) be EQUIVALENT to a
CONTINUOUS one (tree / geometry)? Not by STORAGE (a finite object cannot store a
continuous one explicitly) -- by GENERATIVE RECIPE. The apple carries a finite,
discrete SEED that REGENERATES the continuous tree on germination. That is exactly how
a finite recipe specifies an unbounded fractal (Mandelbrot z->z^2+c is finite; its
output is unbounded detail).

  * the SEED's ENCODING (storage) = Class I cyclic: the genetic code IS Class I
    cyclic-3 (Spike #81 / [[user_stance_dna_is_partial_cascade_of_loe_operators]]);
    and Class I IS the discrete circle Z/nZ -- the discrete compression of the
    continuous U(1) (R35). So the seed = the Class-I (discrete-circle) compression of
    the continuous tree's program.
  * the SEED's UNFOLDING (germination) = a cascade (a rewrite/growth program) that
    renders the continuous tree geometry.

THE CLOSED LOOP (the genuine structural closure of R33->R35): form-IS-function
equivalence between the two languages is a CLOSED LOOP --
    continuous TREE  --[ B o H o N readout / "picking" ]-->  discrete APPLE + SEED
    discrete SEED (Class I)  --[ germination / unfolding cascade ]-->  continuous TREE
B/H/N is the forward readout (continuous->discrete, R33-35); Class I (the seed) is the
reverse generation (discrete->continuous). The loop closes; iterating it (tree->apple->
seed->tree->...) IS the fractal. (Loop-closure is a (b)-interpretive synthesis, not a
new bit-exact identity.)

============================================================================
PART 2 -- the apple tree shows the fractal geometry abstractly (rigorous anchor)
============================================================================
The rigorous, ATTESTED backbone is the L-SYSTEM (Lindenmayer 1968) -- THE standard
mathematical model of plant/tree growth: a finite DISCRETE rewrite grammar (the seed/
rules; operation-primary) that generates the branching TREE geometry (geometry-primary).
This is the exact discrete-grammar -> continuous-tree bridge (the framework already
ships a LOGO turtle-graphics -> cyclic-group encoder as a sister notebook). The apple
tree is the concrete figurative anchor (per [[feedback_aphantasia_means_more_figures_
not_fewer]]) for the framework's recursive-Hopf / fractal-shadow substrate (Spikes
#212-#216): finite recipe -> unbounded self-similar structure = the defining fractal
property.

BIT-EXACT CORE (Lindenmayer's original algae L-system): axiom A; rules A->AB, B->A.
The string LENGTHS are the Fibonacci numbers; consecutive ratios -> phi (the self-
similarity ratio); best_rational(phi) convergents climb the Fibonacci ladder (Class N)
-- tying to Spike #41 (Fibonacci/phi) and R26 (capsid phi->Fibonacci). So a finite
discrete grammar (seed) generates self-similar growth with ratio phi, read back via
Class N -- discrete recipe -> continuous fractal -> discrete rational readout, the loop.

Routed through srmech 0.4.2. Deterministic; no network. ASCII-safe prints.
Attested: Lindenmayer J.Theor.Biol. 18:280 (1968); Prusinkiewicz & Lindenmayer,
"The Algorithmic Beauty of Plants" (1990); Spike #81 (genetic code Class I); R35.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.rational import best_rational  # noqa: F401 (Class N)

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# PART 2 bit-exact core: Lindenmayer algae L-system -> Fibonacci -> phi -> Class N
# ---------------------------------------------------------------------------
def lsystem_step(s):
    # the SEED = two finite rewrite rules (operation-primary grammar): A->AB, B->A
    return "".join("AB" if c == "A" else "A" for c in s)


axiom = "A"
strings = [axiom]
for _ in range(9):
    strings.append(lsystem_step(strings[-1]))
lengths = [len(s) for s in strings]            # the "tree" grows; lengths = Fibonacci

# reference Fibonacci (1,2,3,5,8,...) -- Lindenmayer lengths start F: 1,2,3,5,8,13...
fib = [1, 2]
while len(fib) < len(lengths):
    fib.append(fib[-1] + fib[-2])
assert lengths == fib, (lengths, fib)          # BIT-EXACT: L-system lengths ARE Fibonacci
print("L-system (seed: A->AB, B->A) string lengths:", lengths)
print("  == Fibonacci sequence:", fib, "->", lengths == fib)
emit("lsystem_fibonacci",
     seed_rules={"A": "AB", "B": "A"}, axiom=axiom,
     lengths=lengths, fibonacci=fib, bit_exact_match=(lengths == fib),
     note="a FINITE discrete rewrite grammar (the seed; 2 rules) generates unbounded self-similar growth; lengths are EXACTLY Fibonacci (Lindenmayer 1968)")

# self-similarity ratio -> phi; best_rational(phi) climbs the Fibonacci ladder (Class N)
PHI_NUM, PHI_DEN = 1618033988749895, 1000000000000000     # phi to 15 dp (integer pair for Class N)
fib_ratio_set = {(fib[i + 1], fib[i]) for i in range(len(fib) - 1)}   # (3,2),(5,3),(8,5),...
print("\nphi convergents via srmech best_rational (Class N) -- climb the Fibonacci ladder:")
climbed = []
for max_d in [2, 3, 5, 8, 13, 21, 34]:
    p, q = best_rational(PHI_NUM, PHI_DEN, max_d)
    climbed.append((p, q))
    on_ladder = (p, q) in fib_ratio_set or (p, q) == (2, 1) or (p, q) == (1, 1)
    print(f"  best_rational(phi, max_d={max_d:2d}) = {p}/{q}   on Fibonacci ladder: {on_ladder}")
    assert on_ladder, (p, q)
emit("phi_classN_fibonacci_ladder",
     phi="(1+sqrt5)/2 ~ 1.6180339887 -- the L-system's self-similarity ratio",
     convergents=climbed,
     all_on_fibonacci_ladder=True,
     note="the fractal self-similarity ratio phi is read back as Class-N rational convergents = the Fibonacci ladder (ties Spike #41 + R26 capsid)")

# ---------------------------------------------------------------------------
# PART 1: the seed (Class I) reconciliation -- recipe-equivalence, not storage
# ---------------------------------------------------------------------------
emit("seed_carries_tree_classI",
     question="how can a FINITE DISCRETE apple be equivalent to a CONTINUOUS tree?",
     answer="by GENERATIVE RECIPE, not storage -- the apple carries a finite discrete SEED that regenerates the continuous tree (as a finite fractal recipe generates unbounded detail)",
     seed_encoding="Class I cyclic -- the genetic code IS Class I cyclic-3 (Spike #81); and Class I IS the discrete circle Z/nZ, the discrete compression of the continuous U(1) (R35). The seed = the Class-I discrete-circle compression of the tree's program.",
     seed_unfolding="a cascade (rewrite/growth program, e.g. the L-system) renders the continuous tree geometry",
     resolves_r35_wrinkle="tree-vs-apple looked part-whole; the seed restores EQUIVALENCE -- the whole tree's program rides inside the discrete fruit, so form-IS-function holds bidirectionally")

emit("closed_loop_form_is_function",
     forward="continuous TREE --[B o H o N readout / picking]--> discrete APPLE + SEED   (continuous->discrete; R33-35)",
     reverse="discrete SEED (Class I) --[germination / unfolding cascade]--> continuous TREE   (discrete->continuous; this round)",
     synthesis="B/H/N (readout) and Class I (the seed's germination) are INVERSE directions of one bridge; the loop closes, and iterating it (tree->apple->seed->tree) IS the fractal",
     status="(b)-interpretive synthesis -- the loop-closure is a structural reading, NOT a new bit-exact identity; the L-system->Fibonacci->phi piece IS bit-exact")

# ---------------------------------------------------------------------------
# PART 2 (figurative anchor) -- the apple tree IS the fractal, abstractly
# ---------------------------------------------------------------------------
emit("apple_tree_is_the_fractal_anchor",
     attested_backbone="L-system (Lindenmayer 1968): a finite DISCRETE rewrite grammar (the seed) generating the branching TREE geometry -- THE standard model of plant growth; the discrete-grammar->continuous-tree bridge (framework ships a LOGO turtle-graphics -> cyclic-group encoder)",
     fractal_property="finite recipe -> unbounded self-similar structure = the DEFINING fractal property; tree->apples->seed->tree is self-similar recursion",
     ties_to="recursive-Hopf at every cascade instantiation (Spikes #212-#216; depth-unbounded, ratio-agnostic) + fractal-shadow two-level; the apple tree is the concrete figurative anchor (per the aphantasia-more-figures discipline)",
     honest_scope="this does NOT 'discover' the substrate is fractal (established elsewhere); it gives a rigorous, attested concrete ANCHOR (L-system) for the seed->tree (discrete recipe -> continuous fractal) reconciliation")

# ---------------------------------------------------------------------------
# verdict
# ---------------------------------------------------------------------------
emit("verdict",
     reconciliation="the discrete<->continuous equivalence of the two substrate-native languages is a GENERATIVE-RECIPE equivalence: a finite discrete Class-I-cyclic SEED regenerates the continuous TREE (not storage). This resolves the R35 part-whole wrinkle and closes the form-IS-function loop: B/H/N reads continuous->discrete (picking), Class I germinates discrete->continuous (seed->tree); iterating = the fractal.",
     fractal_anchor="the apple tree is the concrete figurative anchor for the substrate's recursive/fractal structure; the L-system (Lindenmayer 1968) is the rigorous attested backbone -- finite discrete grammar -> self-similar tree geometry, with growth = Fibonacci, ratio = phi, read back via Class N.",
     bit_exact="L-system lengths == Fibonacci (exact); phi convergents == Fibonacci ladder via srmech best_rational (Class N)",
     honest_scope="(a)-bit-exact for the L-system/Fibonacci/phi/Class-N core (Lindenmayer 1968 attested); (b)-interpretive for the seed=Class-I-carrier reconciliation (built on Spike #81 + R35) and the closed-loop synthesis + the fractal figurative anchor (built on Spikes #212-216). No new physics.")

META = {
    "record": "meta",
    "round": "36.A",
    "title": "Seed-carries-the-tree (Class I) reconciliation + the apple tree as the substrate's fractal-geometry anchor",
    "kind": "(a)-bit-exact L-system/Fibonacci/phi/Class-N core + (b)-interpretive seed=Class-I recipe-equivalence reconciliation + closed-loop synthesis + fractal figurative anchor",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "lsystem": "Lindenmayer, J. Theor. Biol. 18:280 (1968); Prusinkiewicz & Lindenmayer, 'The Algorithmic Beauty of Plants' (1990)",
        "genetic_code_classI": "Spike #81 (genetic code = Class I cyclic-3 + Class C)",
        "phi_fibonacci": "best_rational convergents of phi = Fibonacci ladder (Spike #41; R26 capsid)",
        "framework": "R35 (operation-primary vs geometry-primary; Class I = discrete circle Z/nZ vs continuous U(1)); R33-34 (B/H/N readout); recursive-Hopf Spikes #212-216; LOGO turtle-graphics -> cyclic-group encoder sister notebook",
    },
    "discipline": "honest grading: bit-exact ONLY for the L-system/Fibonacci/phi/Class-N piece; the seed=Class-I reconciliation, the closed-loop, and the fractal anchor are (b)-interpretive (built on attested spikes); the apple tree is a pedagogical anchor, NOT a claim the substrate was newly discovered to be fractal; deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: the discrete<->continuous equivalence is a GENERATIVE-RECIPE equivalence -- a finite "
      "discrete Class-I-cyclic SEED regenerates the continuous TREE (not storage), resolving R35's "
      "part-whole wrinkle and CLOSING the form-IS-function loop (B/H/N reads continuous->discrete; "
      "Class I germinates discrete->continuous; iterating = the fractal). The apple tree is the concrete "
      "anchor; the L-system (Lindenmayer 1968) is the rigorous backbone: finite grammar -> self-similar "
      "tree, lengths = Fibonacci (bit-exact), ratio = phi, read back via Class N.")
