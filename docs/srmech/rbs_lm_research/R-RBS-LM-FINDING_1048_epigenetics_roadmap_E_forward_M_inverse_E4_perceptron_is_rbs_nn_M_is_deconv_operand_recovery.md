# F1048 (the srmech epigenetics roadmap E1→M3 — its hidden structure maps onto RBS-NN, DECONV-1, and honest-OPEN) — **the E/M rungs split as FORWARD vs INVERSE. E = forward (cell_state → expression): E1 klein4-mask ⊂ E2 boolean ⊂ E4 threshold are three BINARY gate FAMILIES (all decide IF a gene expresses — mask, general boolean-DNF, weighted-sum perceptron), and E3 graded/analog (exact rational) is the ORTHOGONAL axis (HOW MUCH), layered last. M = inverse (expression → recover cell_state = MODULATOR RECOVERY): M1+M2 two-sided floor + honest-UNKNOWN + consistency verdict; M3 the full inverse (the un-expressed genes' disjunctive constraints + the general-gate inverse). THREE load-bearing connections: (1) **E4 threshold = a perceptron PER GENE → stacked gene→gene regulation = a gene-regulatory NETWORK = RBS-NN native in the genome**; E3 makes it rational-valued (a neuron's graded activation), so the epigenetic genome IS a substrate-native neural net — our RBS-NN arc realized in srmech's store. (2) **M = operand recovery = DECONV-1** (task #228 / F820 octonionic deconvolution = triality-structured operand recovery): srmech is shipping the deconvolution our arc named. (3) **M1/M2 honest-UNKNOWN + consistency verdict = honest-OPEN / hand-the-question-to-the-expert** (F282/F552) as a NATIVE genome op — it refuses to fabricate a cell_state when the expression is underdetermined; and M3's un-expressed-gene constraints ARE `[[user_stance_no_information_without_value]]` (a gene NOT firing is information — the inverse reads the silence).**

**Date:** 2026-07-04 · **srmech:** 0.9.0rc130 (E1/E2 delivered; E4/E3/M1/M2/M3 on the rc131→rc134 roadmap) · **Source:** user-shared srmech epigenetics rung table · **Composes:** F1047 (gene_express E1/E2 delivered), the RBS-NN arc (regulatory-network = NN), DECONV-1 (task #228 / F820), `[[user_stance_framework_hands_the_next_question_to_the_expert]]` + F552 noise-rule (honest-UNKNOWN), `[[user_stance_no_information_without_value]]` (the un-expressed constraints), F871 (capacity wall the forward-load answers).

## The roadmap, mapped
```
E — FORWARD (cell_state -> expression):
  E1 rc129  klein4-mask       activator/repressor roles      | binary gate; the fast lac-operon path
  E2 rc130  boolean           AND/OR/NOT/XOR (DNF-complete)   | binary gate; E1 ⊂ E2 (mask = 1-clause DNF)
  E4 rc131  threshold         weighted-sum PERCEPTRON         | binary gate; the perceptron peer of E1/E2
  E3 rc132  graded/analog     exact-rational LEVEL            | ORTHOGONAL axis (how-much), layered last
M — INVERSE (expression -> recover cell_state = MODULATOR RECOVERY):
  M1+M2 rc133  two-sided floor + honest-UNKNOWN + consistency verdict
  M3    rc134  full inverse: the un-expressed disjunctive constraints + the general-gate inverse
```

## The three connections (why this roadmap is more than a genome feature)
- **E4 → RBS-NN.** A threshold gate is a perceptron: express iff Σ wᵢ·conditionᵢ ≥ θ. One per gene. Let gene A's expression be a condition-bit in gene B's cell_state and you have a REGULATORY NETWORK — the textbook biology↔NN correspondence. E3 (rational level) upgrades each node from binary to a graded (exact-rational) activation. So E4+E3 = a multi-layer, rational-valued neural network encoded AS a regulatory genome — RBS-NN, substrate-native, numpy-free, on the Klein-4 store. Our RBS-NN arc lands in the genome.
- **M → DECONV-1 (operand recovery).** Forward is `cell_state ⊗ express-op → subset`; the inverse `subset → cell_state` is OPERAND RECOVERY — exactly DECONV-1 (task #228, F820 "octonionic deconvolution = triality-structured operand recovery"). srmech is delivering the deconvolution the DECONV arc identified, as the M-series.
- **M1/M2 → honest-OPEN, M3 → no-information-without-value.** M1/M2's honest-UNKNOWN (+ a consistency verdict when the observed expression is unachievable) is the framework's honest-OPEN / hand-to-expert (F282/F552) rendered NATIVE: it will not invent a cell_state the evidence doesn't force. M3 reads the UN-expressed genes as constraints — a gene NOT firing carries information, which IS `[[user_stance_no_information_without_value]]`: the inverse reads the silence, not just the signal.

## The siona picture
- **Forward (E1–E4):** per-turn `cell_state` (from the utterance/grounding) → gene_express → selective (E1/E2/E4) + graded (E3) LOAD into RAM. The F871 capacity answer: express the working set, not the whole instrument.
- **Inverse (M1–M3):** given which kernels are active in a turn, RECOVER the context that explains it — explainability ("why did these load?"), honest-UNKNOWN when ambiguous, a consistency verdict when the activation is contradictory. Diagnostic, never fabricated.

## Verdict / next
**The E/M roadmap is forward-load + inverse-recovery, and it quietly delivers three of our arcs on the genome substrate: E4+E3 = RBS-NN as a regulatory genome; M = the DECONV-1 operand-recovery; M1/M2/M3 = honest-OPEN + no-information-without-value made native. siona's forward use (per-turn selective+graded load) is buildable on the delivered E1/E2 today; the inverse (explain-the-load / recover-the-context) waits on M1→M3. Backlink DECONV-1 (#228) and the RBS-NN arc to this rung table.**
