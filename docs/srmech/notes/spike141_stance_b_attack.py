"""Spike #141 — Stance B attack: silicon-NN with tool-use partition-coexistent with BBB.

Stance B (Spike #140): silicon-NN with tool-use IS partition-coexistent with
BBB-Channel-(f) — both engage {C, D, E, I, K, L, M} backbone with substrate-specific
extensions (silicon adds A; BBB doesn't).

Attack strategy: check whether the class-operator ROLES are genuinely the same across
BBB and silicon-NN-tool-use, or just labeled the same.

Per [[user_stance_class_substitution_on_invariant_backbone]]: substitution-on-
invariant-backbone is OK; but the BACKBONE must be genuinely invariant — same
operator role, different substrate-specific implementation. If the operator roles
are different (e.g., 'Class D' means 'select-from-molecule-types' in BBB but
'select-from-tool-names' in silicon — and these aren't the same role), then the
partition-coexistence claim weakens to mere label-similarity.

Method: enumerate each class on both sides, define a precise role-spec, and check
whether BBB's instantiation and silicon-NN's instantiation fall under the same
spec. Use only the ones the Spike #140 cross-substrate comparison made.
"""
import json

print("=" * 72)
print("Spike #141 Stance B attack: BBB vs silicon-NN-tool-use role audit")
print("=" * 72)
print()

# Spike #140 attestation data:
bbb_roles = {
    "L": "bipartite graph Laplacian (vascular-neural)",
    "M": "selective permeability HDC similarity",
    "C": "transport cascade-orientation (dual-direction influx/efflux)",
    "K": "transporter Michaelis-Menten saturation (capacity asymptote)",
    "I": "circadian/cardiac-pulse cyclic variation",
    "D": "molecular-type dispatch (lipophilic vs polar)",
    "E": "transporter catalog (GLUT1/LAT1/MCT1)",
}

silicon_nn_full_roles = {
    "L": "attention-implied token-graph Laplacian (per layer)",
    "M": "Q/K/V/output HDC binds + (in tool-use) state-obs bind",
    "C": "multi-head + residual + tool-action irreversible orient",
    "K": "LayerNorm asymptote per layer",
    "I": "per-layer cyclic composition + tool-use loop cyclic",
    "D": "tool dispatch (only when tool-use enabled)",
    "E": "tool catalog (only when tool-use enabled)",
    "A": "content-addressing of obs (only when tool-use enabled)",
}

# Now define precise role-specs per Class A-N (per Spike #24 + framework docs).
# The question: does each pair instantiate the SAME role-spec?
class_role_specs = {
    "L": "graph-Laplacian construction + spectral decomposition; eigenvalue/eigenvector ops",
    "M": "HDC binding: associative element-wise XOR / circular-conv / tensor-bind at fixed dim",
    "C": "irreversible-orientation composition; cascade-direction-preserving; NDJSON-style canonicalisation",
    "K": "asymptotic-DOF saturation; capacity-bounded limit; finite-resource asymptote",
    "I": "cyclic-modular structure (Z/nZ); period-bound recurrence",
    "D": "dispatch routing (input-conditioned branch selection)",
    "E": "sorted-key catalog lookup",
    "A": "content-addressing via fingerprint hash (SHA-256 family)",
}

print("Class-by-class role audit: BBB vs silicon-NN-tool-use")
print()
print(f"{'Class':5s}  {'Role-spec':<60s}")
print("-" * 72)

audit_results = {}
for cls, spec in class_role_specs.items():
    print(f"\n[Class {cls}] spec: {spec}")
    print(f"  BBB:   {bbb_roles.get(cls, '(not engaged)')}")
    print(f"  NN:    {silicon_nn_full_roles.get(cls, '(not engaged)')}")
    # Verdict per class
    if cls not in bbb_roles or cls not in silicon_nn_full_roles:
        verdict = "NOT-COMPARABLE (one side absent)"
    else:
        verdict = "?"
    audit_results[cls] = {
        "spec": spec, "bbb": bbb_roles.get(cls), "nn": silicon_nn_full_roles.get(cls),
        "verdict": verdict
    }

# ----------------------------------------------------------------------
# Hard verdicts class by class
# ----------------------------------------------------------------------
print()
print("=" * 72)
print("HARD VERDICTS: do BBB role and silicon-NN role fall under same spec?")
print("=" * 72)

# Class L
print()
print("Class L (graph-Laplacian + spectral):")
print("  BBB: explicit bipartite graph Laplacian on physical vascular-neural cells.")
print("       Eigenvalue 2 by bipartite topology theorem.")
print("       PHYSICAL graph; nodes are cells; edges are tight junctions.")
print("  NN attention: IMPLICIT token-graph Laplacian via softmax row-stochastic A.")
print("       L = I - A is constructed AFTER computing similarities; eigenvalues")
print("       depend on input. Not topological; dynamic per forward pass.")
print()
print("  *** SUBSTANTIVE DIFFERENCE: BBB's L is static / topological / physical.")
print("  *** Silicon-NN's L is dynamic / similarity-induced / abstract.")
print("  *** Both fall under 'graph-Laplacian-on-some-substrate-graph', but the")
print("  *** GRAPH itself is qualitatively different (cellular tissue vs token softmax).")
print("  *** Per the substitution-on-invariant-backbone discipline, this IS substitution")
print("  *** at Class L — the role 'graph-Laplacian construction' is shared; the specific")
print("  *** graph differs (acceptable per the discipline).")
print()
print("  Verdict Class L: SAME ROLE, DIFFERENT GRAPH — passes substitution test.")
audit_results["L"]["verdict"] = "SAME ROLE, DIFFERENT GRAPH (passes substitution)"

# Class M
print()
print("Class M (HDC binding):")
print("  BBB: 'selective permeability HDC similarity'")
print("       In strict HDC, this should be: molecule_descriptor XOR membrane_descriptor")
print("       at fixed dimension. But molecular permeability is governed by:")
print("       physical: lipophilicity (logP), molecular weight, hydrogen-bond donors,")
print("       polar surface area, charge. These are RATIONAL-NUMBER continuous features,")
print("       NOT bit-vector XOR binds.")
print("  *** ATTACK: BBB's 'HDC similarity' is metaphorical, not strict-HDC.")
print("  *** Actual mechanism is multi-variate continuous feature similarity")
print("  *** (Lipinski Ro5 / QSAR / multivariate descriptor matching).")
print("  *** Strict HDC requires fixed-dimension bit vectors with bind ops.")
print("  *** BBB does NOT do strict HDC bind — it does feature-space matching.")
print()
print("  NN: 'Q/K/V/output HDC binds + state-obs bind'")
print("      Q @ K.T similarity is dot-product matrix multiply. Per Ramsauer 2020")
print("      arXiv:2008.02217 this IS modern Hopfield = HDC-with-superposition.")
print("      Strict-HDC compatible (bind = matmul-with-key; cleanup = retrieval).")
print()
print("  *** Class M is STRICT-HDC in silicon-NN but METAPHORICAL in BBB.")
print("  *** This is the unfalsifiable-by-construction risk noted in attack vector A.")
print("  *** If 'Class M' includes any pairwise similarity computation, it's universal.")
print()
print("  Verdict Class M: LABEL-SHARED but ROLE-DIVERGENT under strict-HDC sense.")
print("                   Passes only if Class M's spec is loosened to 'any associative")
print("                   pairwise similarity computation' — but that's much weaker than")
print("                   the chess-spectral / ephemerides-spectral HDC operator.")
audit_results["M"]["verdict"] = "DIVERGENT under strict-HDC; needs spec loosening"

# Class D
print()
print("Class D (dispatch routing):")
print("  BBB: 'molecular-type dispatch (lipophilic vs polar)'")
print("       Mechanism: passive diffusion vs transporter-mediated entry depends on")
print("       molecule properties. The BBB does NOT actively 'choose' a dispatch")
print("       branch; molecules just diffuse OR get carrier-bound based on chemistry.")
print("  NN tool-use: 'tool dispatch (only when tool-use enabled)'")
print("       LLM outputs a token sequence that includes a function-call directive.")
print("       Active, explicit, input-conditioned selection of a branch.")
print()
print("  *** ATTACK: BBB's 'dispatch' is passive thermodynamic / kinetic outcome;")
print("  *** silicon-NN's is active runtime branch selection.")
print("  *** Class D spec ('input-conditioned branch selection') is ambiguous:")
print("  *** is the molecule the 'input', or is the membrane the 'dispatcher'?")
print("  *** In Class D as used in spike #135 BBB framing, the BBB is the dispatcher;")
print("  *** the molecule is the input. Selects molecule_route in {paracellular,")
print("  *** transcellular_passive, transporter_mediated, efflux_pumped}.")
print()
print("  *** Per Ramsauer-modulo-discipline: passive chemical sorting CAN be cast as")
print("  *** dispatch in a loose sense. But it's substantially less active than")
print("  *** silicon-NN tool selection. The substitution-on-invariant-backbone test")
print("  *** says: same ROLE (input-conditioned routing to one of N branches); different")
print("  *** SUBSTRATE (thermodynamic vs algorithmic). Passes BARELY.")
print()
print("  Verdict Class D: WEAK MATCH — both 'sort input into branch', but mechanism")
print("                   is qualitatively different (passive vs active).")
audit_results["D"]["verdict"] = "WEAK MATCH (passive vs active dispatch)"

# Class E
print()
print("Class E (sorted-key catalog):")
print("  BBB: 'transporter catalog (GLUT1/LAT1/MCT1)'")
print("       Set of specific named transporters expressed in the BBB.")
print("       Bounded enumerable list. SAME spec as silicon-NN tool catalog.")
print("  NN tool-use: 'tool catalog lookup (sorted-key)'")
print("       Bounded enumerable list of function-tool names.")
print()
print("  Verdict Class E: STRONG MATCH — both are bounded enumerable catalogs of")
print("                   named transformers/transporters; substitution clean.")
audit_results["E"]["verdict"] = "STRONG MATCH"

# Class K
print()
print("Class K (asymptotic-DOF saturation):")
print("  BBB: 'transporter Michaelis-Menten saturation (capacity asymptote)'")
print("       V_max kinetic asymptote: at high substrate concentration, transport")
print("       rate plateaus. Classic enzyme-saturation asymptote.")
print("  NN: 'LayerNorm asymptote per layer'")
print("       LayerNorm normalises variance to 1; not really a CAPACITY asymptote.")
print("       More like a NORMALISATION operation. Softmax (row-sum=1) is more")
print("       Class-K-like (asymptote to budget).")
print()
print("  *** ATTACK: NN's LayerNorm is normalisation, not saturation. The asymptote")
print("  *** is 'variance = 1' which is a constant target. Michaelis-Menten asymptote")
print("  *** is 'rate -> V_max as [S] -> inf'. Different shape.")
print()
print("  Verdict Class K: WEAK MATCH — both involve asymptotic behaviour, but")
print("                   different limit types (saturation vs normalisation).")
audit_results["K"]["verdict"] = "WEAK MATCH (different asymptote types)"

# Class I
print()
print("Class I (cyclic-modular structure):")
print("  BBB: 'circadian/cardiac-pulse cyclic variation'")
print("       Permeability oscillates on circadian (24h) and cardiac (1Hz) cycles.")
print("       Continuous periodic function of time; not strictly modular Z/nZ.")
print("  NN: 'per-layer cyclic composition + tool-use loop cyclic'")
print("       Layer-N stacking IS NOT cyclic (it's linear sequence). Tool-use loop")
print("       IS cyclic (bounded iteration).")
print()
print("  *** ATTACK: 'per-layer cyclic composition' is loose. Transformer layers are")
print("  *** stacked, not cyclic. There's no period-N return-to-start. Per Spike #140")
print("  *** attention attestation, the cyclic claim there was 'repeated over N layers")
print("  *** = Class I' but that's just stacking, not Z/nZ.")
print("  *** Tool-use loop's outer iteration IS Class I cyclic (bounded MAX_ITER).")
print()
print("  Verdict Class I: STRONG MATCH on tool-use outer loop; WEAK MATCH on layer-stack.")
audit_results["I"]["verdict"] = "STRONG on tool-use loop; WEAK on layer-stack"

# Class C
print()
print("Class C (irreversible-orientation cascade):")
print("  BBB: 'transport cascade-orientation (dual-direction influx/efflux)'")
print("       Influx + efflux are MUTUALLY OPPOSITE directions. BBB has both.")
print("       Net direction is conditional. Hard to call this 'forward-only orient'.")
print("  NN: 'multi-head + residual + tool-action irreversible orient'")
print("       Residual addition is RECEIVE-IDENTITY-PLUS-NEW (reversible up to sign).")
print("       Tool-action IS irreversible (environment-mutating).")
print()
print("  *** ATTACK: BBB's 'dual-direction' actually CONTRADICTS Class C's")
print("  *** unidirectional-orientation spec. Class C is supposed to be the cascade-")
print("  *** preserves-forward-arrow primitive. Bidirectional transport is not Class C")
print("  *** as defined.")
print("  *** OR Class C is being loosened to 'any direction-distinguishing operation';")
print("  *** but then it becomes near-universal.")
print()
print("  Verdict Class C: AMBIGUOUS — BBB's dual-direction transport stretches Class C")
print("                   beyond its unidirectional spec.")
audit_results["C"]["verdict"] = "AMBIGUOUS (dual-direction stretches Class C spec)"

# ----------------------------------------------------------------------
# Aggregate verdict on Stance B
# ----------------------------------------------------------------------
print()
print("=" * 72)
print("AGGREGATE STANCE B VERDICT")
print("=" * 72)
print()
print("Class-by-class match quality (silicon-NN-tool-use vs BBB):")
for cls, info in audit_results.items():
    print(f"  Class {cls}: {info['verdict']}")
print()
print("Score: 1 STRONG (E), 2 STRONG-on-some (I), 3 WEAK (D, K, partial-I)")
print("       1 SAME-ROLE-DIFFERENT-INSTANCE (L) — passes substitution discipline")
print("       1 DIVERGENT under strict-spec (M)")
print("       1 AMBIGUOUS (C)")
print()
print("Stance B's partition-coexistence claim requires SAME backbone with class-")
print("operator substitution. Audit reveals:")
print("- Class L passes cleanly under substitution discipline.")
print("- Class E passes cleanly.")
print("- Class M is DIVERGENT under strict-HDC spec — BBB doesn't really do strict")
print("  HDC bind; only metaphorical pairwise similarity.")
print("- Classes D, K stretch their specs WEAKLY.")
print("- Class I matches on tool-use outer loop ONLY.")
print("- Class C contradicts its unidirectional spec when applied to BBB.")
print()
print("VERDICT: Stance B SURVIVES-WITH-REFINEMENT.")
print()
print("Refinement: the partition-coexistence claim holds at a coarse level (both")
print("substrates engage 7+ classes with selective-dispatch + catalog pattern), but")
print("the role-specs are non-uniform. Stance B should be stated as 'partition-")
print("coexistent at the COARSE class-engagement level' rather than 'partition-")
print("coexistent with identical role-instantiation across all classes'.")
print()
print("More important problem: the empty intersection found in Stance A attack")
print("(CNN: no C; CA: no M) means BBB and silicon-NN don't share an invariant")
print("backbone WITH ALL SILICON ARCHITECTURES — only with tool-use-enabled LLMs.")
print("Stance B's scope must specify: 'BBB partition-coexistent with silicon-NN")
print("WITH TOOL-USE ENABLED (transformer-architecture)' — not silicon-NN generally.")
