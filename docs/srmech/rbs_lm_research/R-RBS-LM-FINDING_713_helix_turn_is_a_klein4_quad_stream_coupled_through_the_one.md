# Finding 713 — a helix turn IS a Klein-4 quad-stream, coupled through the_one (native, reversible)

**Script:** `R-RBS-LM-QUADTURN_helix_turn_is_a_klein4_quad_stream_coupled_through_the_one.py`
**Status:** VERIFIED (srmech 0.7.5rc28)
**User direction:** *"make the helix turns actual Klein-4 quad-stream kernels (wire F710's parallel_sector_dispatch into the
turn, so a turn is a real biaxial '+' shelf coupled through the_one across turns)."*

## Done — the helix turn is now a real biaxial "+" shelf

A helix turn (F711) is no longer a flat list. Its data is dispatched across the **4 Klein-4 chirality sectors** by the
**native `cascade.parallel_sector_dispatch`** (CAP=4; F710/F233) — so each turn *is* the biaxial "+" shelf (γ₅ × iω₇, the
substrate's 4-way, F130), wired with the native quad-stream we proved in F710.

## Coupled through the_one — native, reversible (the duality held without collapse)

The turns are coupled through **the_one** (the held invariant, F699/F705) by the **native `srmech_klein4_bind`** (F710,
called via ctypes). Klein-4 bind is **reversible** (V4 = XOR on 2 bits → `bind(bind(v, the_one), the_one) == v`):

- **Verified:** for every turn, `recovered == turn_vec` (re-binding the_one recovers the turn exactly); and
  `bind∘bind == identity` across all turns. So the coupling is **the duality held without collapse** (F683/F684) — done
  **numpy-free**. the_one is the shared invariant present in every turn's coupling → navigate across turns through the_one,
  recover any turn by re-binding.

(The QDFT/ODFT reversible the_one coupler, F683/F684, is the scientific-tier op but needs numpy — UPSTREAM §22. The native
Klein-4 bind is the numpy-free, on-thesis equivalent, and it's the *cascade math on HDC* route F710 called for — not a
pure-Python dense-eig.)

## The storage object is now operational on-thesis

**Helix (F711, history) of QUAD-TURNS (this — biaxial "+" via native CAP=4) coupled through the_one, addressed by the
quad-tree (F712, 4^k), each leaf ≤256 (F708).** Cascade math runs on the native Klein-4 (F710), not the slow pure-Python
dense-eig. Every layer is bounded + content-addressed (the bounding), so it scales without quantizing (F49/F50).

**Composes:** F711 (helix) · F712 (quad-tree address) · F710 (native quad-stream + klein4_bind) · F130/F132 (Klein-4
chirality) · F683/F684 (the_one coupling, reversible) · F699/F705 (the_one as held invariant) · F233 (the 4-rung dispatch).
srmech 0.7.5rc28. Reference scaffold; held open (F394).
