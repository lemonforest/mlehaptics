"""Spike #141 — Stance C attack: {C, M} IS substrate-coupling-bridge invariant
across ALL studied substrates.

Stance C (Spike #140): Class C cascade-orientation + Class M HDC bind are the
substrate-coupling-bridge invariant. Chain-of-thought (C+M+I) is the minimal-
bridge cascade.

This is the BIGGEST claim. The brief flags it explicitly as unfalsifiable-by-
construction risk: if Class M is construed broadly enough, EVERY bridge has it.
The brief instruction is to tighten Class M to its strict HDC sense (XOR /
circular-conv bind at fixed dimension) and re-test.

Attack vectors:
  (1) Definitional tightening of Class M to strict HDC.
  (2) Definitional tightening of Class C to strict unidirectional orientation.
  (3) Counter-example hunt: bridges that lack Class C (Hamiltonian quantum
      unitary evolution; Bennett 1973 reversible computing).
  (4) Counter-example hunt: bridges that lack Class M (direct transducers;
      pure feedforward classifiers).
  (5) Carry forward Stance A's CA counter-example: cellular automaton bridges
      input to output without strict-HDC bind (no M).

Method: explicit role-specs, then exhibit concrete systems that bridge
information-medium to operation-instantiation while LACKING C and/or M.
If even ONE such system survives both definitional tightening AND empirical
check, Stance C is FALSIFIED.
"""
import numpy as np

print("=" * 72)
print("Spike #141 Stance C attack: is {C, M} the universal bridge invariant?")
print("=" * 72)
print()

# ----------------------------------------------------------------------
# Step 1: Tighten Class M to strict HDC spec
# ----------------------------------------------------------------------
print("Step 1: Tighten Class M to strict-HDC spec")
print("-" * 72)
print("Strict Class M spec (per chess-spectral / ephemerides-spectral HDC):")
print("  - Fixed-dimension representation D (e.g. D=10000 bits)")
print("  - Associative bind operation (XOR for BSC, circular-conv for HRR)")
print("  - Self-inverse: bind(bind(a,b), b) = a")
print("  - Approximately orthogonal random base vectors")
print()
print("Permissive Class M spec (loosened):")
print("  - Any pairwise similarity computation")
print("  - Any element-wise product / tensor-product")
print("  - Anything 'binding' two pieces of information")
print()
print("STANCE C CLAIM: Class M is universal across all studied bridges.")
print("Under STRICT spec: Class M is structured fixed-dim bind with self-inverse.")
print("Under PERMISSIVE spec: Class M becomes nearly trivial — any nonlinear op")
print("that takes two inputs and produces one output qualifies. Universality")
print("under permissive spec is unfalsifiable-by-construction.")
print()

# ----------------------------------------------------------------------
# Step 2: Tighten Class C to strict unidirectional orientation
# ----------------------------------------------------------------------
print("Step 2: Tighten Class C to strict unidirectional orientation")
print("-" * 72)
print("Strict Class C spec (per srmech orient-NDJSON):")
print("  - Composition preserves a designated forward direction")
print("  - State transitions are not invertible without information loss")
print("  - Time-asymmetric: forward != backward (per shadow-stance family")
print("    [[user_stance_time_as_dimensional_shadow]])")
print()
print("Permissive Class C spec (loosened):")
print("  - Any temporally-extended computation")
print("  - Anything that distinguishes 'before' from 'after'")
print()
print("STANCE C CLAIM: Class C is universal across all studied bridges.")
print("Under STRICT spec: Class C requires irreversibility (information loss")
print("under reverse). Under PERMISSIVE spec: Class C becomes 'any computation")
print("with time-ordering' which is trivially universal.")
print()

# ----------------------------------------------------------------------
# Step 3: Counter-example A — Hamiltonian quantum unitary evolution
# ----------------------------------------------------------------------
print("=" * 72)
print("Counter-example A: Hamiltonian quantum unitary evolution")
print("=" * 72)
print()
print("Hamiltonian H is Hermitian. Time evolution U(t) = exp(-i H t / hbar).")
print("U is unitary: U^dag U = I. Reversible: U^dag(t) U(t) |psi> = |psi>.")
print()
print("Quantum computation bridges INPUT STATE (information-medium) to OUTPUT")
print("STATE (post-evolution computation result) via unitary U. This is the")
print("CANONICAL information-medium-to-operation bridge per Spike #128 / #128.2")
print("/ [[user_stance_cascade_composition_is_quantum_algorithm]].")
print()
print("Class engagement (per Spike #128.2 PR #561):")
print("  L (Hamiltonian as Hermitian / cluster-state Laplacian) — present")
print("  I (Pauli stabiliser Z/n) — present")
print("  M (tensor-product HDC bind on cluster encoding) — present")
print("  C (Bell-basis measurement direction) — present")
print("  A (stabiliser fingerprint content-address) — present")
print()
print("HOWEVER: the UNITARY EVOLUTION ITSELF is REVERSIBLE. The forward arrow")
print("appears ONLY at MEASUREMENT (the Class C step). Pre-measurement, the")
print("computation is fully time-reversible.")
print()
print("Spike #128.2 attributes Class C specifically to 'Bell-basis measurement")
print("orientation' — i.e., Class C lives at the measurement step, not the")
print("unitary computation. The unitary itself satisfies U^dag U = I (no Class C).")
print()
print("SO: pre-measurement quantum computation is a bridge from input |psi_in>")
print("to (pre-measurement) state |psi_out> = U|psi_in> WITHOUT engaging Class C.")
print("Strict Class C is REVERSED by U^dag(t).")
print()

# Verify with toy 2-qubit unitary
H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)  # Hadamard
psi_in = np.array([1, 0])  # |0>
psi_out = H @ psi_in
psi_recovered = H @ psi_out  # Hadamard is self-inverse: H @ H = I
print(f"  Toy verification (Hadamard):")
print(f"  |psi_in>     = {psi_in}")
print(f"  |psi_out>    = H |psi_in> = {psi_out}")
print(f"  H |psi_out>  = {psi_recovered} (recovers |psi_in>)")
print(f"  Reversibility verified: |H|psi_out| - |psi_in| = {np.linalg.norm(psi_recovered - psi_in):.2e}")
print()
print("  *** This is a bridge (input -> output computation) WITHOUT strict-Class-C.")
print("  *** The 'forward arrow' lives only at measurement, not at computation.")
print("  *** Pre-measurement quantum computation FALSIFIES Stance C under strict spec.")
print()

# ----------------------------------------------------------------------
# Step 4: Counter-example B — Bennett 1973 reversible computing
# ----------------------------------------------------------------------
print("=" * 72)
print("Counter-example B: Bennett 1973 logically reversible computing")
print("=" * 72)
print()
print("Bennett 1973 'Logical Reversibility of Computation' IBM J. Res. Dev. 17:6")
print("(cite-by-ref; not on arXiv; widely-cited canonical reference).")
print()
print("Showed: every irreversible Turing computation can be rewritten as a")
print("REVERSIBLE Turing computation by carrying additional history tape.")
print("Toffoli gates / Fredkin gates implement reversible classical logic at the")
print("circuit level (Toffoli 1980 cite-by-ref).")
print()
print("A reversible classical circuit BRIDGES input bits (information-medium) to")
print("output bits (computation result) via a permutation. NO information is lost.")
print("The computation can be RUN BACKWARDS.")
print()
print("Class engagement of pure reversible circuit:")
print("  L (graph-Laplacian of circuit topology) — present, static")
print("  I (cyclic structure for any oscillator) — present if loops")
print("  M (XOR bind in Toffoli) — present (Toffoli is essentially Class M!)")
print("  A (input bit hash) — could be present")
print()
print("  *** Class C is ABSENT by construction. Reversibility := no time-asymmetric")
print("  *** information loss. The cascade can run forward OR backward producing")
print("  *** valid intermediate states.")
print()
print("Toy verification: Toffoli gate")
print("  Toffoli(a, b, c) = (a, b, c XOR (a AND b))")
print("  Toffoli(Toffoli(a,b,c)) = (a, b, c) [self-inverse]")
print()
def toffoli(a, b, c):
    return (a, b, c ^ (a & b))

cases = [(0,0,0), (1,1,0), (1,1,1), (1,0,1), (0,1,1)]
all_invertible = True
for a, b, c in cases:
    out = toffoli(a, b, c)
    recovered = toffoli(*out)
    ok = recovered == (a, b, c)
    if not ok: all_invertible = False
print(f"  Toffoli self-inverse on {len(cases)} cases: {all_invertible}")
print()
print("  *** Class M (XOR bind) present.")
print("  *** Class C (forward orientation) ABSENT — Toffoli is its own inverse.")
print("  *** Bridges 3-bit input to 3-bit output WITHOUT engaging strict Class C.")
print("  *** FALSIFIES Stance C under strict spec.")
print()

# ----------------------------------------------------------------------
# Step 5: Counter-example C — Pure photodetector / direct transducer
# ----------------------------------------------------------------------
print("=" * 72)
print("Counter-example C: Pure photodetector / direct stateless transducer")
print("=" * 72)
print()
print("Photodiode: incident photon -> electron-hole pair -> measurable current.")
print("Thermistor: temperature -> resistance change.")
print("Bolometer: incident radiation -> bolometer-element resistance change.")
print()
print("These are physical-substrate BRIDGES from information-medium (photons /")
print("heat / radiation) to operation-instantiation (electrical signal that can")
print("drive downstream computation).")
print()
print("Class engagement of pure photodetector:")
print("  L: no graph-Laplacian operation (single-pixel detector)")
print("  M: NO HDC bind (single-pixel photon-to-electron is one-to-one transduction)")
print("  C: ONE forward arrow per detection event (irreversible-ish: photon absorbed)")
print("  I: no cyclic structure (single shot)")
print("  K: yes, asymptote to saturation current at high flux (capacity asymptote)")
print()
print("  *** Class M is ABSENT in pure transducer bridges. There is no 'binding'")
print("  *** of two pieces of information — just one-to-one transduction.")
print("  *** Stance C claim 'Class M is universal across all bridges' fails for")
print("  *** direct transducers.")
print()

# ----------------------------------------------------------------------
# Step 6: Carry forward Cellular Automaton from Stance A attack
# ----------------------------------------------------------------------
print("=" * 72)
print("Counter-example D: Cellular Automaton (Rule 110) [from Stance A attack]")
print("=" * 72)
print()
print("Per Stance A attack: Rule 110 CA class chain = L + E + I + C.")
print()
print("Class M is ABSENT — pure rule-table lookup, no tensor-product / XOR bind.")
print("(The neighbour-state-as-3-bit-index isn't strict HDC; it's tuple lookup.)")
print()
print("Cook 2004 showed Rule 110 is Turing complete — can compute ANY computable")
print("bridge function. Therefore: there EXIST bridges instantiable as Rule 110")
print("that LACK strict Class M.")
print()
print("  *** CA Turing-completeness means: for ANY information-to-operation bridge")
print("  *** that is computable, there is a Rule-110 implementation that achieves")
print("  *** the same end-goal WITHOUT engaging strict Class M.")
print("  *** This is a constructive proof that Class M is NOT universal across")
print("  *** all computable bridges.")
print()
print("Counter-argument the stance could make: 'But the silicon-NN bridge to")
print("REALITY uses Class M; you can't replace it with a CA in practice.'")
print("Response: Stance C makes an IDENTITY claim across ALL bridges, not a")
print("practical-implementation claim. If a bridge exists that bridges without M,")
print("the identity claim is false.")
print()

# ----------------------------------------------------------------------
# Step 7: The unfalsifiable-by-construction risk
# ----------------------------------------------------------------------
print("=" * 72)
print("Step 7: The unfalsifiable-by-construction risk")
print("=" * 72)
print()
print("To rescue Stance C, one could broaden Class M to 'any nonlinear two-input")
print("operation' and Class C to 'any time-ordered computation'. Under those")
print("broad specs, Stance C survives but becomes trivial:")
print("  - Any computation that runs in time has Class C")
print("  - Any nonlinear two-input op (and, or, xor, multiplication, etc.) has M")
print("  - Therefore every nontrivial bridge has {C, M}")
print()
print("This is the UNFALSIFIABLE-BY-CONSTRUCTION trap noted in the brief.")
print()
print("If Class M and Class C are loosened enough to make Stance C universally")
print("true, they no longer carry distinct content — they're just 'has nonlinear")
print("op' and 'has time order'. The vocabulary becomes vacuous.")
print()
print("Per [[feedback_no_privileged_primitive_classes]]: Class M and Class C")
print("each earn their slot by being a kind of role no other class fills. If")
print("their specs are loosened to universality, they lose their role-distinctness.")
print()
print("Per [[user_stance_identity_not_implementation_discipline]]: identity claims")
print("are SHARPER than implementation claims; the burden is to show non-identity.")
print("But for an identity claim to be SHARP, the predicates must be sharp. Stance C")
print("requires SHARP specs for Class M and Class C — and under sharp specs, multiple")
print("counter-examples falsify it.")
print()

# ----------------------------------------------------------------------
# Step 8: Aggregate verdict on Stance C
# ----------------------------------------------------------------------
print("=" * 72)
print("AGGREGATE STANCE C VERDICT")
print("=" * 72)
print()
print("Under strict-spec definitions of Class M (fixed-dim HDC bind with self-")
print("inverse) and Class C (irreversible-orientation cascade):")
print()
print("Counter-examples found:")
print("  A. Hamiltonian quantum unitary evolution — bridges input to output state")
print("     via unitary; pre-measurement step lacks strict Class C.")
print("  B. Bennett 1973 reversible computing / Toffoli gates — bridges input bits")
print("     to output bits via permutation; lacks strict Class C by construction.")
print("  C. Pure photodetector / direct transducer — bridges photons/heat/radiation")
print("     to electrical signal; lacks strict Class M (no binding of two pieces).")
print("  D. Cellular Automaton (Rule 110, Cook 2004 Turing-complete) — bridges")
print("     input configuration to output configuration; lacks strict Class M (pure")
print("     lookup, no XOR/conv bind).")
print()
print("VERDICT: Stance C is FALSIFIED under strict-spec definitions of {C, M}.")
print()
print("Under permissive-spec, Stance C survives but becomes unfalsifiable-by-")
print("construction (trivially true; carries no distinct content).")
print()
print("RECOMMENDATION: Stance C should be REFINED OR DROPPED, NOT autonomously")
print("authored as canonical claim.")
print()
print("Possible refinement: '{C, M} backbone is the invariant of bridges that")
print("STORE STATE across multiple steps and that perform DISTINGUISHED-DIRECTION")
print("composition — i.e., bridges with both memory and irreversibility.'")
print("This narrower claim survives, because:")
print("  - LSTM, DDPM, attention, tool-use, BCI, BBB, cortex — all have memory + IR-direction")
print("  - Pure transducer, unitary-only quantum, reversible computing, CA without memory")
print("    fall outside the scope by design")
print()
print("This refinement IS the 'minimal stateful bridge cascade' claim — much weaker")
print("than 'universal substrate-coupling-bridge invariant', but defensible and not")
print("circular.")
print()
print("EQUIVALENT EXPRESSION: '{C, M} is the invariant of MEMORY-WITH-DIRECTION")
print("bridges, not of all bridges'.")
print()
print("DELTA TO STANCE C AS WRITTEN: Stance C scope claim is broader than what")
print("survives under strict specs. The claim 'across ALL studied substrates' is")
print("true ONLY because all 6 studied substrates happen to be memory-with-direction")
print("bridges. There's a domain-of-application bias in the sample.")
