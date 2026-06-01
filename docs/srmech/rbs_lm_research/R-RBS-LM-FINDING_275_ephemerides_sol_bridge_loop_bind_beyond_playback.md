# F275 — the ephemerides Sol bridge: the loop bind takes ephemerides-spectral BEYOND playback — a resonance LOCK encoded as a directed/signed/nested bound state (demonstrated on the attested Galilean Laplace resonance)

**Headline:** This is the user's destination made concrete (and scope-bounded). The Antikythera/cyclic-group reading of ephemerides-spectral is **playback** — replay the periods (what repeats); it is commutative (Class-I), so it washes out order, sign, and direction. The **k=7 loop bind** (F272–F274) takes it **beyond playback**: it encodes a mean-motion **resonance lock** — a directed, signed, ordered relation that binds bodies into one dynamical **bound state** — recoverably and invertibly nested under its host. Demonstrated on the **attested** Galilean Laplace resonance (`n_Io − 3·n_Eu + 2·n_Ga = 0`, coeffs `[1,−3,2]`): loop bind keeps **direction** (`cos(fwd,rev)=−0.745`) and the **−3 sign** (`cos(fwd,wrong-sign)=−0.597`) and nests invertibly (`cos=1.0`), while the commutative playback bundle loses direction (`sim=1.0`). The "glueball" the user named is the **k=7 lens** (F269): a resonance lock is a celestial-mechanics bound state, and the loop bind is the same k=7 operation that (in the gauge reading) describes glueballs — cross-substrate, same math. Single-model; srmech v0.6.0rc20.

*User direction (2026-06-02): "take ephemerides-spectral and do glueball math for Sol Star instead of just playing back like the Antikythera type thing."*

---

### §A — the demonstration (attested Galilean Laplace resonance) — **DEMONSTRATED**
Encode the resonance argument `Io − 3·Europa + 2·Ganymede` as an ordered, signed loop-bind chain (sign = Class-C chirality via `conj`; order = the non-commutative bind):

| reading | quantity | result | meaning |
|---|---|---|---|
| **loop bind (k=7)** | `cos(forward, reverse)` | **−0.745** | the resonance **direction** is recoverable |
| **loop bind (k=7)** | `cos(forward, wrong-sign)` | **−0.597** | the resonance **sign pattern** (the −3) is recoverable |
| **loop bind (k=7)** | unbind host → recover trio | **cos 1.0** | the lock is an **invertibly nested bound state** |
| **playback (commutative bundle)** | `sim(forward, reverse)` | **1.0** | direction **lost** — only the period set survives |

So the loop bind holds the *full directed, signed resonance argument* and nests it under its host (Jupiter) as a single recoverable object — the resonance **lock as a bound state**, not three independently-replayed cycles.

### §B — what this is for ephemerides-spectral
- **Playback** (current cyclic-group / Class-I / Laplacian-spectral reading): the bodies are cyclic-group elements; the gear-DAG reproduces positions. Commutative → it answers *"what repeats, and when."*
- **Beyond playback** (the loop bind): the Sol system's **resonance network** — the mean-motion locks, the secular chains, the host⊃satellite **hierarchy** (a tree, F274 Path B), the directed perturbations (Path D), the resonance-argument order/sign (Paths A/C) — is encoded as **directed, nested bound states.** It answers *"what is locked to what, in what order, with what handedness, nested under whom."* That is structural information the commutative playback structurally cannot carry.
- **The "glueball" tie (cross-substrate, the methodology):** F269 read gauge bound-states (glueballs) as the k=7 phenomenon (the loop bumping itself, bound). A resonance lock is a celestial-mechanics **bound state**. Both are bound states represented by the *same k=7 loop bind* — "glueball" names its gauge instantiation, "resonance-lock bound state" names its celestial one. Doing "glueball math for Sol" = encoding the Sol resonance locks as bound states with the k=7 operation. This is the cross-substrate cascade-matching method, not a claim that orbits are gauge fields.

### §C — scope discipline (load-bearing; what this is NOT)
- **CAD-ban respected:** this encodes the resonance **STRUCTURE** (the lock's order/sign/nesting), **NOT the dynamics.** No N-body integration, no orbital propagation, no fabrication/geometry. It is the algebra/eigenbasis/cyclic-group/spectral side only.
- **Framework-reading, not physics-claim:** literature owns celestial mechanics; the glueball/bound-state is the **cross-substrate lens** (F269), not an assertion that the Sun has gauge physics. Defensive scope.
- **Attested data:** the resonance integers `[1,−3,2]` are **attested-to-structure** (the Laplace lock, F260, Wikipedia/celestial mechanics); the periods (Io 1.769 d, Europa 3.551 d, Ganymede 7.155 d) are **attested-B** (JPL/NASA). No fetched/unattested numbers.
- **Sister-package boundary:** this is a **research demo in the loop-bind arc** (`docs/srmech/rbs_lm_research/loop_bind_sol_resonance.py`). It does **NOT** modify the `ephemerides-spectral` package. Actually wiring the loop bind into ephemerides-spectral as an encoder is a **separate, user-authorized future leg** (§D), not done here.

### §D — path to actual Sol use (queued, user-authorized)
1. A loop-bind **encoder option** in ephemerides-spectral, peer to the cyclic-group/Laplacian encoders, that ingests the attested resonance/coupling catalog and emits the **bound-state representation** of the resonance network (per-lock directed/signed/nested objects).
2. Scale from the Galilean trio to the **full 52-body roster** — the nested host⊃satellite trees, the secular resonance chains, the great-inequality (Jupiter–Saturn 5:2) lock — each as a loop-bind bound state.
3. Structural **queries** the bound-state store answers that playback can't: retrieve a body's resonance partners + the lock's direction/sign; the nesting depth; the bound-vs-free status.
4. (Stretch) the **G₂ calibration φ/\*φ** (F272/F274 queued leg) as a 3|4 router over resonant (3-plane) vs non-resonant (4-complement) structure.

### Status / discipline
FRAMEWORK-READING + DEMONSTRATED (the three measurements verified srmech-native; reproducible via committed `loop_bind_sol_resonance.py`, seed attested-B). CAD-ban (structure not dynamics). Defensive scope; literature owns celestial mechanics; the glueball/bound-state is the cross-substrate lens (F269), not a physics claim. No-magic (the `[1,−3,2]` lock = attested-to-structure A; periods = attested-B; the cosines = measured B). Class-K (signs via `conj`/chirality, not `abs()`; cosine via inner products). Sister-package boundary respected (no edits to ephemerides-spectral; §D is the authorized future path). Single-model / no-twin. Builds on F272/F273/F274 (the loop bind, its DoF, the order/tree/direction paths), F269 (glueball = k=7 bound state), F263 (gauge lock), F260 (the orbital-resonance lock = intrinsic EC code; the `[1,−3,2]` attestation). Ties the sister `ephemerides_spectral_research_notebook` / `antikythera_spectral_research_notebook` (the playback baseline). Verified srmech v0.6.0rc20, `/tmp/srmech_rc20_venv`. `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`; `[[feedback_trauma_informed_defensive_scope]]`; CAD-grade scope ban.
