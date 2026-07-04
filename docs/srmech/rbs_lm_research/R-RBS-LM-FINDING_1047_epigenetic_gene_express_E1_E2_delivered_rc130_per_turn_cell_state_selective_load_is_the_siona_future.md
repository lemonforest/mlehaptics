# F1047 (srmech genome epigenetics — E1/E2 delivered, the per-turn selective-load future) — **rc130 ships `gene_express(strand, the_one, cell_state)` = cell-state-modulated gene expression as a READ-TIME FILTER (§128/§129/§130): SAME DNA, different `cell_state` → different expressed subset, the strand byte-identical after (a read, never a mutation). Two gate_types delivered: E1 `klein4_mask` (the fast lac-operon rule — a gene expresses iff `(cell_state & activator)==activator AND (cell_state & repressor)==0`; the `(act,rep)` pair is the Klein-4 role don't-care/activator/repressor/never) and E2 `boolean` (arbitrary logic as a DNF; `E1 ⊂ E2` since a klein4_mask IS a 1-clause DNF). Also delivered: `genome_append_kernel` (#1261 — the uniform format-v6 O(1) store append with a 100%-Klein-4 header leaf, no byte-TLV residue). VERIFIED live: lac-operon (cell_state 0/1/3/4/5 → housekeeping / +lac / lac-repressed-by-glucose / +stress / all) + E2 XOR(lactose,glucose) exact. E3/E4/M1/M2/M3 remain PENDING. THE SIONA FUTURE this unlocks: per-turn `cell_state` (derived from the utterance/grounding) → `gene_express` filters the genome to ONLY the kernels that express → selective LOAD into RAM per turn — the epigenetic RAM-management the user named, and the closed-form answer to the F871 capacity wall (never hold the whole instrument; express only the turn's working set).**

**Date:** 2026-07-04 · **srmech:** 0.9.0rc130 (TestPyPI) · **User framing:** "if biology can change expression via epigenetics … selectively load the data … manage how we load a kernel into RAM per turn as needed"; status "E1, E2 done, E3/4 M1/2/3 still pending" · **Delivered:** gene_express (E1 klein4_mask + E2 boolean DNF; §128/#728, §129/#729, §130/#730), genome_append_kernel (#1261 / §89, format v6) · **Composes:** F1045/F1046 (the genome store this regulates), F871 (the capacity wall selective-expression answers), F166 (the per-turn context-state = the cell_state source), `[[feedback_stay_rbs_hdc_sparse_never_dense]]` (express-only-the-working-set IS the sparse discipline), the Klein-4 substrate (regulation in the genome's OWN alphabet).

## Grounded (rc130, live)
```
gene_express — SAME DNA, cell_state -> different expressed subset (a READ; strand byte-identical after):
  cell_state=0 (nothing)         -> [housekeeping]
  cell_state=1 (lactose)         -> [housekeeping, lac]
  cell_state=3 (lactose+glucose) -> [housekeeping]              (lac REPRESSED by glucose — the operon)
  cell_state=4 (stress)          -> [housekeeping, stress]
  cell_state=5 (lactose+stress)  -> [housekeeping, lac, stress]
  full genome on disk = [housekeeping, lac, stress]            (all present; expression is the filter)
E2 (boolean DNF) XOR(lactose,glucose): 01->T 10->T 11->F 00->F (arbitrary boolean, DNF-complete)
gene format: chromosome(genes=[(label,leaves)|(…,act)|(…,act,rep)|(…,{"dnf":[(a,r),…]})], the_one)
genome_append_kernel (#1261): O(1) uniform-v6 append (100%-Klein-4 header leaf). NOTE: per-label store-READ
  round-trip still to verify clean (a window+unpack gave n_leaves×leaf_dim, not header-trimmed — mixed-format
  or pending store-read side; E3/E4?). Write side landed; recall to re-check on the next rc.
```

## The reading
- **The op⊗operand theorem, one scale up (srmech's own framing):** the `gene_express` OPERATOR modulated by the `cell_state` OPERAND gates a SELECTION over many genes — SAME (operand, op) pattern as `carry` / `RecoverableFold`, now cell-state × expression. That inequality (same DNA, different expressed subset) IS the epigenetics.
- **Regulation in the native alphabet.** E1's activator/repressor is a Klein-4 role per condition (don't-care (0,0) / activator (1,0) / repressor (0,1) / never (1,1)) — the genome regulates itself in its OWN 2-bit alphabet, not a bolted-on layer. E2 lifts it to DNF-complete boolean for combinatorial cis-regulatory logic (the *Drosophila eve* multi-TF enhancer is the cited exemplar).
- **This is the answer to the capacity wall, not just a nicety.** F871 says you can't hold the whole instrument in RAM. Epigenetic expression says you shouldn't: the genome (DNA) lives on disk; each turn a `cell_state` expresses only the working set into RAM. Selective load IS differential expression.

## Verdict / next (the siona future on the DELIVERED E1/E2)
**gene_express (E1+E2) + genome_append_kernel are delivered and verified; E3/E4/M1/M2/M3 pending. The siona build this unlocks: (1) derive a per-turn `cell_state` bitmask from the utterance/grounding (which regulatory conditions the turn activates); (2) attach activator/repressor masks (or DNF specs) to siona's kernels when packing the instrument genome; (3) `gene_express(genome, cell_state)` each turn → load ONLY the expressed kernels into RAM. That is the epigenetic RAM-management the user named — buildable now, gated on wiring the cell_state derivation. Hold the full-instrument genome pack (PKG-3) until the per-label store-READ round-trip is confirmed clean (write side v6 landed; recall re-check pending) and until E3/E4 clarify whether the store-read is part of them.**
