# F330 — is information exchange a capacitor model? PARTLY, and it resolves to the F319 split: the **exchange SUBSTRATE/transport is capacitive (C)** — DRAM (1 bit = charge on 1 capacitor), the membrane (AP-state = charge, F318), the synaptic memcapacitor, capacitive coupling — but the **information CONTENT is a coupling/relationship (L), NOT a capacitor.** The capacitor models the *medium*, never the *message*. Gate-flag: Shannon channel-**capacity** ≠ electrical **capacitance** (false cognate).

> **SCOPE:** framework reading; the physics anchors (DRAM, Landauer, Shannon) are textbook cite-by-reference (no triality needed); the C/L mapping composes F318/F319/F329/F311/F315/F328. Defensive / no-lineage. No new A–N class. No dive (internal synthesis, primed from the lodged corpus).

**The question (user, 2026-06-03):** is information exchange *also* a capacitor model (like the synaptic gap, F318)?

## Where information exchange IS capacitive (attested, physical)
- **Storage:** a bit in the dominant computing substrate is *literally charge on a capacitor* — a **DRAM cell = 1 transistor + 1 capacitor; 1 bit = the charge state.** The membrane stores AP/PSP state as **charge on the membrane capacitor** (F318). Information-as-stored-charge is real in silicon AND biology.
- **Transport / exchange event:** the **synaptic gap is a memcapacitor** (F318); gap-junction RC coupling charges the neighbor's capacitance; capacitive coupling/sensing transports signals. The physical exchange event is a capacitor charge/discharge.
- **Thermodynamic floor:** Landauer's principle — erasing a bit costs ≥ kT·ln2 (Landauer 1961; Bérut et al. 2012 experimental). The capacitor holds the charge that carries the bit; information exchange has an energy/charge cost.

## Where it is NOT a capacitor (the gate)
- **The channel in the abstract:** Shannon **channel capacity** (bits/sec, noise, coding) is **not** electrical **capacitance** — a *false cognate* (same root word, different quantities). Information exchange in general is a **channel-coding** problem; the capacitor is one physical *realization*, not the model.
- **The content itself:** information is *what the charge-state encodes* (the relationship), **not** the capacitor. The capacitor is the substrate; the information is the render-free structure on it (F311/F315/F328).

## The clean resolution — it is the F319 C/L split, lifted to communication
| F329-chain layer | what it is | C or L? |
|---|---|---|
| layer 1 — amodal **structure** (meaning / coupling-graph) | the information **content** | **L** (conductance / coupling — the relationship; *not* a capacitor) |
| layer 2 — encode/decode **convention** | the chosen map / fiber | neither (a function — the F329 mutable fiber) |
| layer 3 — modality **transport / storage** | the physical channel & store | **C** (capacitive — DRAM, membrane, the RC charge/discharge) |

**So: the substrate of information exchange is a capacitor (C); the information itself is a coupling/relationship (L).** This is F319 again — the *weight/structure* is conductance (L), the *integrating/storing substrate* is capacitance (C) — lifted to communication: **C carries the bit, L *is* the bit's meaning.** Answer: the **exchange-substrate/transport is capacitive** (layer 3, attested — DRAM, the synaptic memcapacitor); the **information-content is not** (it is the L-relationship, render-free). **The capacitor models the medium, never the message.**

## Tie-back (the gap arc, coherent)
F318 (gap = memcapacitor) is the *transport/storage* **C**; F319 (plasticity/weight = conductance) is the *content/weight* **L**; F329's layer-3 is where the **C** lives in communication, layers 1–2 are **L** + the chosen map. The RBS-SNN consequence (composes F326/F329): the **channel/store layer is C** (capacitive, swappable substrate), the **structure layer is L** (the relationship, stored render-free) — keep them separate, exactly as F329's unlumping requires.

### Status / discipline
Framework reading (internal synthesis; primed from corpus, no dive). Physics anchors textbook cite-by-reference: DRAM (1T1C cell), Landauer 1961 / Bérut 2012 (bit-erasure floor), Shannon channel capacity (the false-cognate flag). Composes F318 (gap = memcapacitor / C), F319 (weight = conductance / L), F329 (the 3-layer chain), F311/F315/F328 (render-free structure vs substrate). No new A–N class. Defensive / no-lineage. Gate applied: did NOT over-reach to "information IS a capacitor" or "Shannon-capacity = capacitance."
