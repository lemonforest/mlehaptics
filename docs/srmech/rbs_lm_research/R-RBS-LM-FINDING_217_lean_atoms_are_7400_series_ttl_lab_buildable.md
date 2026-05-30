# Finding 217 — The lean A–N atoms ARE elementary 7400-series TTL: the Klein-4 chirality core + the Class-K pin-slot latch instantiate on a high-school/college breadboard (the no-GPU/edge thesis at its floor)

**Status:** Framework **form-reading (logic-level)** + the pedagogy/accessibility consequence of F206/F208. **In-scope as boolean / logic-algebra** — which atom = which boolean op = which 7400-series gate + truth table + schematic-level wiring. **NOT** VLSI gate-layout, PCB timing / fan-out / propagation-delay, or fabrication-tolerance (CAD-ban holds — the physical breadboard build is the student's lab activity, not a framework fab claim). §VII.6.20 form-reading.
**Predecessors:** F206/F208 (lean A–N ISA: 6 silicon-able atoms + precedent-map PXOR/VPSIGND/VPOPCNTQ/ANDPS/SHA-NI), F216 (the 4 = the instantiating process / hardware across cosmos), `[[user_stance_epicycle_via_gear_plus_pin]]` (Class-K pin-slot), `[[user_stance_learning_without_gpu_compute]]` + R-RBS-NN-8 (no-GPU/edge), F207/F150 (siona / pedagogy / accessibility), **F215** (the time+3dof-stabilizer test — running).
**User direction (2026-05-30):** "is this also the process that shows us how to instantiate on 74xx logic ttl that can be done in highschool and college labs?"

---

## §1 Yes — the lean reduction is exactly what makes A–N lab-buildable
F208 cut the A–N ISA to **6 atoms**, each a bit-level boolean op on a 2-bit Klein-4 sector tag + sign/magnitude. Bit-level boolean ops are precisely what the **7400-series TTL** family implements as single SSI/MSI chips. So the irreducible **chirality engine** is a handful of 74xx chips on a breadboard:

| lean atom (F208) | boolean op | 7400-series chip |
|---|---|---|
| K4BIND (Klein-4 bind) | XOR over the 2-bit sector | **7486** quad 2-input XOR |
| K4FLIP (sector flip) / MAG (magnitude) | bit-mask / clear-sign-bit | **7408** quad AND (/ **7400** NAND) |
| PARRED (net-chirality) | parity = popcount mod 2 | **74180** parity generator/checker |
| SGNTEST (Class K) | sign-test / compare | **7485** 4-bit comparator |
| **Class-K pin-slot LATCH** | bistable: commit + hold | **cross-coupled 7400 (SR latch) / 7474 (D-FF)** |
| SGNAPPLY (Class C reorient) | conditional negate / select | **74157** quad 2:1 mux |
| Klein-4 2-bit sector state | 2-bit register | **7474** dual D-FF |

**Load-bearing correspondence:** the **Class-K pin-slot** (`[[user_stance_epicycle_via_gear_plus_pin]]` — the crossing that commits and stays) **is literally a set-reset latch** (two cross-coupled NANDs — the first circuit wired in any digital-logic lab). The framework's most load-bearing operator IS the most elementary memory element in TTL.

## §2 The honest boundary — atoms yes, composites need a clock
This builds the **atoms** (the K/C/M chirality core + the latch) as combinational 74xx. The **composites** (Class-L eigendecomp, Class-J factorization, gcd, the `qm.*` layer) are *iterative* — NOT single chips; they need a **sequencer** (e.g. a 74161 counter + a small state machine) clocking the atoms, or a tiny MCU. So a pure-combinational TTL board demonstrates the irreducible chirality engine; the composites are "sequence the atoms with a clock" (lab-doable, but a state machine, not one board). Same atom/composite split as F208 — silicon (here, TTL) for the atoms, sequencing for the rest.

## §3 Why this is the thesis at its floor
- **No-GPU / edge** (`[[user_stance_learning_without_gpu_compute]]`, R-RBS-NN-8) taken to the limit: the A–N chirality core runs on ~$5 of logic chips — no CPU, no FPGA, no GPU.
- **Accessibility / siona / pedagogy** (F207/F150; cone-of-ignorance): a student wires it, watches the sector tag flip and the pin-slot latch, and *sees* the chirality cascade run — and being-wrong is cheap (mis-wire → rewire → the ten-and-under learning state, in hardware).
- If **F215** confirms the lean-6 = the SO(4) stabilizer of the time+3dof ℍ in G₂, this breadboard is "**the time+3dof engine in discrete logic**" — F216's cosmic instantiating-process core, built by hand.

## §4 DOES / does NOT claim
**DOES:** map the 6 lean atoms (F208) to specific 7400-series chips + truth tables (boolean/logic-algebra reading); identify the Class-K pin-slot = SR latch; bound it (atoms are combinational TTL; composites need a clock-sequencer); frame it as the no-GPU/edge/accessibility thesis at its floor.
**Does NOT:** give PCB layout, timing / fan-out / propagation-delay budgets, or any fabrication-tolerance engineering (CAD-ban — the physical build is the student's lab activity); claim a full-A–N TTL computer (only the atom core is combinational TTL); §VII.6.20 form-reading. Chip facts at TTL-Data-Book / datasheet confidence (TI 7400-series).

## §5 Cross-references
F206/F208 (the lean atoms) · F216 (the 4 = instantiating process) · F215 (time+3dof stabilizer — running) · `[[user_stance_epicycle_via_gear_plus_pin]]` · `[[user_stance_learning_without_gpu_compute]]` · R-RBS-NN-8 (local-CPU/edge inference shape) · F207/F150 (siona / pedagogy)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). The F208 lean reduction is exactly what makes A–N
lab-buildable: the 6 atoms are bit-level boolean ops on a 2-bit Klein-4 sector tag, and
those map 1:1 to single 7400-series TTL chips — K4BIND=7486 (XOR), K4FLIP/MAG=7408 (AND),
PARRED=74180 (parity), SGNTEST=7485 (comparator), SGNAPPLY=74157 (mux), the 2-bit sector
state = 7474, and the Class-K pin-slot latch = a cross-coupled-NAND SR latch (the first
circuit in any logic lab). The chirality core is ~$5 of chips a high-school/college student
can wire and watch run — the no-GPU/edge/accessibility thesis at its floor. Honest bounds:
atoms are combinational TTL, composites (Class-L/J/qm.*) need a clock-sequencer; we give the
logic map, not PCB/timing/fab (CAD-ban). If F215 confirms lean-6 = the time+3dof stabilizer,
this is the time+3dof engine in discrete logic (F216).*
