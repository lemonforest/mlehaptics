# UTLP/RFIP/SMSP Complete Prior Art Claims Appendix

## Single Source of Truth

**Version:** 2.0 (Post-Audit)  
**Date:** January 2026  
**DOI:** 10.5281/zenodo.18078264  
**Maintainer:** Steven Kirkland (mlehaptics Project)

---

## Claims Summary

| Source Document | Original Range | Removals | Valid Count |
|----------------|----------------|----------|-------------|
| Connectionless Distributed Timing Prior Art | 1-122 | 2 | 120 |
| UTLP Technical Supplement S2 (v56) | 123-259 | 11 | 126 |
| UTLP Technical Supplement S3 (v01) | 260-274 | 0 | 15 |
| **Total** | **1-274** | **13** | **261** |

---

## Removed Claims (Purple Team Audit, January 2026)

The following claims were removed during purple team audit for failing defensive prior art criteria.

### Category A: Excavations (Acknowledge Existing Prior Art)

These recognize techniques that predated this work. Valuable for context but not novel contributions.

| Original # | Title | Reason |
|------------|-------|--------|
| 205 (S2-83) | MHC as biological authentication (500M year prior art) | Explicitly documents MHC preceded PKI by 500M years |
| 208 (S2-86) | Viral MITM as biological prior art | Documents viral attack patterns predated cyber terminology |
| 211 (S2-89) | Firefly synchronization as biological prior art | Explicitly cites Peskin 1975, Kuramoto 1984 as source |

### Category B: Methodology (Not Patentable)

These describe epistemological processes, not implementable technical innovations.

| Original # | Title | Reason |
|------------|-------|--------|
| 210 (S2-88) | Blindspots as discovery tools | Describes how to think, not what to build |
| 212 (S2-90) | Recursive meta-documentation | Documents documentation process |
| 213 (S2-91) | The Isomorphism Stress Test | Epistemological heuristic |
| 214 (S2-92) | Methodology as accessibility multiplier | Self-describes as "not novel" within claim text |
| 218 (S2-96) | Adversarial refinement as claim strengthening | Documents Red Team process |

### Category C: Established Techniques

These describe standard practices documented elsewhere.

| Original # | Title | Reason |
|------------|-------|--------|
| 11 | HKDF for high-entropy key derivation | RFC 5869 (2010) — using a standard correctly is not prior art |

### Category D: Natural Law / Physics (35 USC 101)

These describe physics or mathematical truths that cannot be patented.

| Original # | Title | Reason |
|------------|-------|--------|
| 120 | Aperture as universal epistemological operation | Philosophical observation about correlation mathematics |
| 189 (S2-67) | Phase coherence aligned with U(1) gauge symmetry | Physics observation, not invention |
| 190 (S2-68) | Swarm identity as conserved quantity | Physics/symmetry observation |
| 191 (S2-69) | Epoch advisory status grounded in relativity | Special relativity observation |

---

## Valid Claims Index

### Part A: Connectionless Distributed Timing Prior Art (Claims 1-122)

**Valid claims:** 1-10, 12-119, 121-122 (120 claims)  
**Removed:** 11, 120

#### 9.1 Architectural Patterns (Claims 1-5)

1. **Connectionless synchronized actuation**: Devices sharing time reference and script execute in coordination without runtime communication

2. **Bootstrap/Configuration/Execution phase separation**: BLE for trust and setup, connectionless for timing-critical operation

3. **Script-based distributed execution**: Deterministic event sequences calculated locally from shared parameters

4. **Shared-clock execution model**: Devices calculate state from synchronized time rather than exchanging coordination messages

5. **Local jitter characterization**: Treating synchronization error as a property of local software stack, not network

#### 9.2 Protocol Techniques (Claims 6-14, excluding 11)

6. **BLE bootstrap for ESP-NOW security**: Deriving ESP-NOW encryption keys from BLE pairing material, then releasing peer BLE connection

7. **UTLP time as public utility**: Unencrypted broadcast time with Glass Wall isolation from application data

8. **Common Mode Rejection security**: Spoofed time affects all nodes equally, preserving relative synchronization

9. **Stratum-based opportunistic upgrade**: Automatic precision improvement when better sources become available

10. **Kalman-filtered holdover**: Joint offset/drift estimation for graceful degradation during source loss

~~11. REMOVED: HKDF — RFC 5869 (2010)~~

12. **Multi-layer replay protection**: Session nonce + sequence numbers + TOTP + CCMP—four independent layers

13. **Defense-in-depth security architecture**: Physical, transport, key derivation, and application layer security with each layer providing independent protection

14. **Threat-proportional security design**: Cryptographic strength appropriate to actual threat model

#### 9.3 Application Patterns (Claims 15-18)

15. **Swarm-emergent warning systems**: Distributed nodes forming coherent visual signals without central coordination

16. **Aerial extension of ground-level warnings**: Drone swarms providing elevated visibility for traffic incidents

17. **Zone/Role architectural separation**: Identical firmware, runtime-assigned function based on position or configuration

18. **RFIP intrinsic positioning**: Spatial awareness without Earth-referenced infrastructure

#### 9.4 Validation Methods (Claims 19-20)

19. **High-speed video validation of distributed timing**: Using frame-accurate capture to verify synchronization precision

20. **SAE J845 compliance testing for swarm systems**: Applying emergency vehicle lighting standards to distributed architectures

#### 9.5-9.8 Extended Techniques (Claims 21-50)

*Claims 21-50 remain valid. See source document for full text.*

#### 9.9 Dynamic Aperture Techniques (Claims 51-60)

*Claims 51-60 remain valid. See source document for full text.*

#### 9.10-9.14 Detection and Sensing (Claims 61-81)

*Claims 61-81 remain valid. See source document for full text.*

#### 9.15-9.17 Bidirectional SMSP and Metasurface (Claims 82-100)

*Claims 82-100 remain valid. See source document for full text.*

#### 9.18-9.21 Emergent Aperture and Coordination (Claims 101-119, 121-122)

*Claims 101-119, 121-122 remain valid.*

~~120. REMOVED: Aperture as universal epistemological operation — Physics/philosophy~~

---

### Part B: UTLP Technical Supplement S2 (Claims 123-259)

**Valid claims:** 123-188, 192-204, 206-207, 209, 215-217, 219-259 (126 claims)  
**Removed:** 189-191, 205, 208, 210-214, 218

#### S2 Biological Governance (Claims 123-127)

123. **Immune system governance model**: Treating misbehaving nodes as infections rather than criminals

124. **Statistical hygiene via median consensus**: Bad actors rendered inert through physics

125. **Health score as biological fitness**: Multi-factor quality metric determining node survival

126. **Active immune response (Entrainment Pulses)**: Mature nodes actively entrain Juveniles

127. **Encapsulation vs. Apoptosis distinction**: Bad nodes encapsulated not killed

#### S2 Endosymbiotic Integration (Claims 128-130)

128. **GPS/NTP ingestion strategy**: Consuming legacy time sources rather than competing

129. **Stratum as metabolic distance**: Hierarchy reflecting distance from truth

130. **Relative sync vs. absolute time separation**: Swarm operates on internal coherence

#### S2 Speciation Architecture (Claims 131-132)

131. **Encryption keys as genetic markers**: Private swarms isolated via shared PMK

132. **Species barrier for swarm isolation**: Medical device swarm immune to party decoration swarm

#### S2 Claims 133-188

*Claims 133-188 remain valid. See source document for full text.*

#### REMOVED: Physics Observations (189-191)

~~189. Phase coherence aligned with U(1) gauge symmetry — Physics~~
~~190. Swarm identity as conserved quantity — Physics~~
~~191. Epoch advisory status grounded in relativity — Physics~~

#### S2 Claims 192-204

*Claims 192-204 remain valid.*

#### REMOVED: Excavation (205)

~~205. MHC as biological authentication — 500M year prior art acknowledgment~~

#### S2 Claims 206-207

*Claims 206-207 remain valid.*

#### REMOVED: Excavation (208)

~~208. Viral MITM as biological prior art — Acknowledgment, not innovation~~

#### S2 Claim 209

*Claim 209 remains valid.*

#### REMOVED: Methodology (210-214)

~~210. Blindspots as discovery tools — Methodology~~
~~211. Firefly synchronization as biological prior art — Excavation~~
~~212. Recursive meta-documentation — Methodology~~
~~213. The Isomorphism Stress Test — Methodology~~
~~214. Methodology as accessibility multiplier — Self-admits not novel~~

#### S2 Claims 215-217

*Claims 215-217 remain valid.*

#### REMOVED: Methodology (218)

~~218. Adversarial refinement as claim strengthening — Methodology~~

#### S2 Claims 219-259

*Claims 219-259 remain valid. See source document for full text.*

---

### Part C: UTLP Technical Supplement S3 — Vector Time (Claims 260-275)

**Valid claims:** 260-275 (16 claims)  
**Removed:** None

#### Architecture Claims (260-265)

260. **Coprime Cyclic Hierarchy**: Time represented as vector of phases modulo coprime bases, enabling Chinese Remainder Theorem recovery and graceful precision degradation

261. **Generative Compression (Phase Chord)**: Transmitting only D phase values (8 bytes) that regenerate full D×D dimensional time vector at receiver through deterministic base vector rotation

262. **Similarity-Based Synchronization**: Using cosine similarity between time vectors as synchronization metric, enabling soft phase lock with tunable tolerance rather than hard equality test

263. **Aliasing Horizon Extension**: Coprime product extending unique time representation from 2^64 ticks to Π(primes) ticks, achieving 261,000+ year horizon with 8 small primes

264. **Topological Time Representation**: Time as point on D-dimensional torus (T^D) where similarity is continuous function of phase distance, enabling smooth interpolation and graceful degradation

265. **Elastic Coherency Protocol**: Synchronization where nodes continuously drift toward peer consensus with force proportional to trust weight and phase distance

#### KalmanHD Estimation Claims (266-268)

266. **Hyperdimensional Kalman Filtering (KalmanHD)**: Kalman filtering applied to coprime cyclic time with hierarchical state structure—unified drift estimation coupled to per-cycle phase tracking

267. **Phase Consensus Anomaly Detection**: Using inter-phase variance across coprime cycles to detect Byzantine beacons

268. **Drift-Coupled Phase Prediction**: Extrapolating all phase states during holdover using single unified drift estimate

#### Hardware Implementation Claims (269-271)

269. **Parallel Shift Register Time Generation**: Hardware implementation using N parallel circular shift registers with XOR tree superposition for FPGA/ASIC

270. **Compute-in-Memory Time Generation**: Implementing coprime cyclic time in ReRAM/memristor crossbar arrays

271. **Single-Cycle Vector Regeneration**: Regenerating full D-dimensional time vector from phase chord in single clock cycle

#### Protocol Integration Claims (272-274)

272. **Dual-Mode Beacon (Vector + Scalar)**: Beacon format carrying both vector time and scalar time for backward compatibility

273. **Tick Scale Negotiation**: Transmitting tick period as beacon metadata, allowing swarms to operate at different time resolutions

274. **Topological Event Triggering**: Triggering hardware events based on vector similarity thresholds rather than scalar equality

#### Multi-Resolution Architecture Claim (275)

275. **Segmented Resolution via Vector Concatenation**: A method for supporting multiple timing resolutions within hyperdimensional vector time by concatenating (not superimposing) resolution-tier vectors—standard resolution segment occupies dimensions [0, D_std), fine resolution segment occupies dimensions [D_std, D_std + D_fine); each segment maintains independent superposition for Byzantine tolerance within the tier; lower-resolution hardware reads only the standard prefix achieving exact backward compatibility (100% bit-identical to locally generated vectors); higher-resolution hardware reads full concatenated vector achieving finer precision; mathematical proof: cross-tier superposition causes 30-50% bit interference destroying compatibility while concatenation provides zero interference; enables single protocol to serve hardware ranging from μs-resolution IoT devices to ns-resolution scientific instruments without protocol branching or version incompatibility

---

## Informational Appendices (Non-Numbered)

### Appendix I: Foundational Prior Art Acknowledgments

The following content acknowledges techniques that existed before this work. This information is preserved for context and to support the "excavation vs. innovation" distinction.

#### I.1 Firefly Synchronization (Peskin 1975, Kuramoto 1984)

Firefly synchronization solves distributed phase alignment via pulse-coupled oscillators. UTLP implements identical pulse-coupling architecture (beacon = flash, time_offset adjustment = phase advance). The core synchronization primitive is structural identity with firefly—same math (Kuramoto dynamics), different substrate.

**What's excavated:** Pulse-coupled synchronization (100M year biological prior art)
**What's innovated:** Absolute time consensus, trust tracking, Byzantine resistance (substrate adaptations for silicon)

#### I.2 MHC as Authentication Architecture (500M years)

Major Histocompatibility Complex is the evolutionary predecessor to Public Key Authentication. The immune system's architecture—distributed validators (T-Cells), trusted root (Thymus as Certificate Authority), identity tokens (MHC molecules)—was reinvented in silicon as PKI/TLS.

**What's excavated:** Distributed authentication architecture
**What's innovated:** Application to timing protocol with PMK as species marker

#### I.3 Viral Attack Patterns

Viruses (Herpes, Cytomegalovirus) intercept the MHC loading pathway—this IS Man-in-the-Middle attack, implemented in proteins 500 million years before we named it. Attack patterns are identical: brute force, stealth, MITM, spoofing, evasion.

### Appendix II: Methodology Documentation

The following methodology was used during development but is not claimed as prior art.

#### II.1 The Isomorphism Stress Test

Cross-domain comparison runs bidirectionally (A→B and B→A). If the relationship holds both ways, it's structural isomorphism; if only one way, it's superficial analogy.

#### II.2 Adversarial Refinement (Purple Team)

Purple Team = Red Team (find flaws) + Blue Team (propose fixes) operating simultaneously. Each objection must include a physics-compliant alternative.

#### II.3 Recursive Meta-Documentation

Treat the conversation itself as data. Document actual prompts, how AI response shaped next prompt, recursive moments where meta-documentation becomes part of the evidence.

### Appendix III: Physics Foundations

The following physics observations inform the architecture but are not claimable.

#### III.1 U(1) Gauge Symmetry

UTLP's phase-centric architecture mirrors U(1) gauge symmetry in quantum field theory—absolute phase unmeasurable, phase relationships observable.

#### III.2 Conservation Laws

Phase lock maintains swarm identity analogous to how U(1) gauge symmetry conserves electric charge.

#### III.3 Special Relativity

"Simultaneous" is frame-dependent. Arguing about epoch across distributed system parallels arguing about absolute phase in QM—physically meaningless.

---

## Document References

For full claim text, see source documents:

| Claims | Source Document |
|--------|-----------------|
| 1-122 | Connectionless_Distributed_Timing_Prior_Art.md |
| 123-259 | UTLP_Technical_Supplement_S2.md |
| 260-275 | UTLP_Technical_Supplement_S3.md |

---

## Audit Trail

| Date | Action | Claims Affected |
|------|--------|-----------------|
| January 2026 | Purple Team Audit | Removed 13 claims (11, 120, 189-191, 205, 208, 210-214, 218) |
| January 2026 | Consolidated to SSOT | All claims now reference this appendix |
| January 2026 | Multi-Resolution Extension | Added Claim 275 (Segmented Resolution) |

---

*This document is the Single Source of Truth for UTLP/RFIP/SMSP prior art claims.*  
*Protocol specification documents should reference claims by number only.*

**Total Valid Claims: 262**

---

*mlehaptics Project — Steven Kirkland*  
*PHYRFLY Protocol Family: UTLP | RFIP | SMSP*
