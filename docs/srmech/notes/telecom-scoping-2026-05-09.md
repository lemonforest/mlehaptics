# Telecom scoping for srmech — 2026-05-09 cross-domain absorption round

**Round:** Telecom (terrestrial: cellular / Wi-Fi / cable / fibre / sensor-mesh / SDR / cognitive-radio + orbital: satellite constellations / TT&C / inter-satellite links)
**Date:** 2026-05-09
**Method:** Dual-agent research pattern (`feedback_dual_agent_research_pattern.md`)

## Headline findings

1. **OFDM IS the `(Transform=DFT, λ_k=subcarrier-frequency, g(λ_k)=channel-equaliser-coefficient)` decomposition** — §3.0's universal decomposition is *the operating principle of every modern wireless standard*. 5G NR (3GPP TS 38.211), Wi-Fi 6/6E/7 (IEEE 802.11ax/be), DVB-T2, LTE, ADSL, DOCSIS 3.1. Transmitter applies IDFT to map data symbols onto orthogonal subcarriers; receiver applies DFT to recover them; channel equaliser is exactly `g(λ_k) = 1/H(λ_k)` per-subcarrier weighting. **Identity, not analogy** — comparable to GNM/NMA-on-RIN identity in protein round. Strongest cross-domain validation since protein.
2. **MIMO precoding via SVD = PCA sibling.** Channel `H = U Σ V*`; transmitter applies V precoding, receiver applies U* combining; parallel-channel gains σ_k are singular values. **Same primitive as protein-ensemble PCA, ephemerides Fiedler eigendecomposition, chess board-state PCA.** Same architectural slot, parameterised by what rows/cols of H represent.
3. **Satellite constellation ISL graph IS a graph-Laplacian-on-orbit problem — direct sibling of ephemerides 52-body resonance graph.** Starlink ~6500 sats × 4 lasers, Iridium NEXT 66 × 4, OneWeb 648, Telesat Lightspeed ~300. Time-varying graph; spectral graph partitioning predicts handover frontiers; Fiedler vector predicts congested gateways; algebraic connectivity predicts mesh resilience. **Path D spectral index is the natural pattern for satellite constellation queries.**
4. **UTLP IS a telecom protocol.** Per `UTLP_Specification.md`: BLE Mesh / ESP-NOW / LoRa transport-agnostic time-sync via stratum-hierarchy beacons. The "Glass Wall" architecture (Time Stack public, App Stack private) is structurally identical to UDP-on-IP-on-Ethernet's separation-of-concerns. **The project has been shipping a connectionless distributed-coordination telecom protocol since v0.3.0-beta.1, without using the word "telecom".**
5. **RFIP IS the positioning-spectral-index pattern (Path D) instantiated on radio.** RSSI / CSI / TDoA / FTM / UWB / AoA observations form a heavy-store; the layered fusion model produces position estimates as spectral-index queries. Channel State Information per OFDM subcarrier is *literally* `(Transform=DFT, λ_k=subcarrier, g(λ_k)=H_k)` — channel transfer function spectrum. RFIP fingerprint-based positioning is "spectral signature lookup over heavy radio store" — Path D in the radio domain.
6. **Cyclic-group HDC binding extends across telecom alphabets.** Z_QAM-orders (Z_4 QPSK, Z_16, Z_64, Z_256, Z_1024, Z_4096 — 5G NR / Wi-Fi 6E / DOCSIS 3.1) / Z_N OFDM bin / Walsh-Hadamard Z_2^k / Zadoff-Chu cyclic-shift / GPS Z_1023 / IP+MAC address spaces. **Multiple `SkPhase9BIP` cousins:** `SpectrumPhase4096BIP` (4096-QAM constellation), `OfdmGridPhaseBIP` (resource-grid usage), `IPMACPhaseBIP` (MAC/IP/ASN address spaces), `TLEPhaseBIP` (satellite catalogue cyclic structure). Most cyclic-group-rich domain scoped — more than chess Z_640.
7. **Config-vs-substrate ratio: ~70/30** — between graphics/audio (80/20) and protein (20/80). Closed-form covers OFDM equalisation, MIMO precoding (SVD), beamforming weights (DFT-on-array), filter design (FIR / IIR / RRC), error-correction algebra (BCH / RS / convolutional), CSI-based positioning. Substrate dominates iterative decoders (Turbo / LDPC / polar SCL), adaptive equalisers (LMS / RLS / Kalman channel tracking), cognitive-radio ML, neural channel estimators, satellite station-keeping, SDR runtime schedulers.
8. **AMSC `literature_curated` is the natural home for largest standards corpus scoped to date.** ITU-T (G/M/K series) / 3GPP TS (38.xxx for 5G NR, 36.xxx for LTE, 23.xxx SA, 33.xxx security) / IEEE (802.3 / 802.11 / 802.15.4 / 802.16) / IETF RFCs (entire TCP/IP) / DVB / ETSI / FCC Part 15. **Larger curated literature corpus than any prior srmech round.** `binary_archive` covers SDR I/Q recordings (GNU Radio file format), TLE catalogues (CelesTrak, Space-Track), antenna-radiation-pattern files, measured channel-impulse-response sounding data, modulation-symbol corpora.
9. **EMDR-project mission relevance: STRONGEST INFRASTRUCTURE FIT.** Audio was the strongest *modality* fit; protein was the strongest *cross-domain validation*; **telecom is the strongest *infrastructure* fit** — it's the substrate underneath audio, motor, LED, BLE, ESP-NOW, UTLP, RFIP, every coordinated bilateral pulse. If srmech earns its keep on telecom, it earns it on the project's actual operating environment.
10. **Path-D-on-UTLP-beacon-history is a concrete project-mission demo.** Every UTLP beacon has stratum / quality / drift_rate / timestamp; over time accumulates a per-device fingerprint (spectral signature of timing stability). Path D similarity query: "find devices whose timing fingerprint matches device X" → swarm coordination / failure-mode clustering / role-assignment heuristics. **Same primitive as ephemerides 52-body Path D, applied to the project's operating infrastructure. Plausibly v0.27.x to v0.28.x scope.**

## Operator counts

- **Manifolds:** ~20 (main agent) / ~30+ (sub-agent — exhaustive across Euclidean grid 1D/2D, sphere S², flat torus T², triangle mesh, general graph terrestrial + general graph orbital, special-structure)
- **Transforms:** ~25 (main) / **37 named** (sub) — DFT/IDFT, DCT, STFT, Walsh-Hadamard, Zadoff-Chu, Gold/Kasami, m-sequences, Hilbert, KLT/PCA/SVD, wavelet, cyclostationary spectral correlation, polyphase filterbank, FBMC, GFDM, OTFS, MUSIC, ESPRIT, Capon/MVDR, spherical harmonics, vector spherical harmonics, graph Fourier, SGWT, NUFFT, tensor decomposition (CANDECOMP/PARAFAC), DPSS/Slepian, Wigner-Ville, Cohen's class, matrix-pencil, trellis-coded modulation, Reed-Solomon transform, BCH transform, LDPC sparse-matrix
- **Closed-form `g(λ)` operators:** 50+ (main) / **80+ (sub)** across 11 thematic groups: modulation, channel-coding (algebra), equalisation, MIMO precoding, beamforming, filter design (RBJ-cookbook-equivalent), spectrum sensing / cognitive radio, RFIP / positioning, satellite / orbital, information-theoretic / spectral, cross-domain ports (graphics → telecom)
- **Substrate primitives:** 25 (main) / **52 (sub)** across iterative decoding (Viterbi / BCJR / Turbo / LDPC / Polar SC/SCL / RS Berlekamp-Massey / CCSDS turbo), adaptive filters (LMS / NLMS / RLS / Kalman / EKF / UKF / particle filter), AEC/ANC/ASLC, cognitive-radio / SDR runtime, neural deep-learning (DnCNN-CSI, AutoEncoder transceiver), satellite station-keeping (Cowell / Encke / RAIM / TRIAD / QUEST / EKF), networking control plane (RIP / OSPF / BGP / TCP / AQM / MPLS / SDN), cryptographic (AES / DH / RSA / Kyber / Dilithium)
- **HDC cyclic groups:** 15+ — Z_2 OOK/BPSK, Z_4 QPSK, Z_16 16-QAM, Z_64 64-QAM, Z_256 256-QAM, Z_1024 1024-QAM, Z_4096 4096-QAM, Z_32768 optical-coherent (research), Z_128/Z_256 byte/nibble, Z_2163 OFDM-bin (5G NR), Z_1023 GPS C/A chip phase, Z_2^48 MAC, Z_2^128 IPv6, Z_2^32 ASN, D_n dihedral on APSK, GF(2^m) primitive root for RS/BCH

## Cross-pollination — 7+ direct identity claims

| Telecom feature | srmech primitive | Match strength |
|---|---|---|
| **OFDM equaliser** | `(Transform=DCT/DFT, λ_k=spatial-or-spectral-frequency, g(λ)=correction)` | **Identity** — same architectural slot |
| **MIMO precoding SVD** | Protein-ensemble PCA + chess board-state PCA + ephemerides Fiedler | Same eigendecomposition; same primitive |
| **CSI-based positioning fingerprint** | Heat-kernel signature on graph (Sun-Ovsjanikov-Guibas) | Same heat-equation eigenvalue pattern; different graph |
| **Beamforming weight vector** | DFT-on-array eigenfunction | Spatial-frequency analogue of OFDM time-frequency |
| **Walsh-Hadamard CDMA spreading** | Chess D₄ symmetry / cyclic-group HDC | Same Z_2^k algebra |
| **Satellite ISL graph Laplacian** | Ephemerides 52-body resonance graph | **Identity** — same Fiedler/algebraic-connectivity primitive |
| **TDoA hyperbolic intersection** | Varadhan SDF reconstruction | Both recover position from heat-kernel-decay measurements |
| **Sheaf-Laplacian on telecom networks** | Doom-spectral §3 sheaf-Laplacian raycasting + protein-round sheaf-Laplacian on RIN | Network-wide consistency / fault tolerance |
| **Heat-kernel blur on CIR / spectrogram** | Audio spectrogram smoothing + graphics heat-kernel blur | Direct port |
| **Power-spectrum noise on RF** | Audio noise generators + graphics power-spectrum noise | Direct port |

## EMDR-project-specific opportunities — STRONGEST INFRASTRUCTURE FIT

### Direct project-internal protocols ARE telecom-spectral

- **UTLP** → connectionless time-sync model (stratum hierarchy, baton-passing, holdover-mode flywheel) competes with PTP (IEEE 1588) at BLE/ESP-NOW transport layer. Could be filed as a contribution to IETF/3GPP if formalised.
- **RFIP** → Layered Fusion Model with RSSI/CSI/TDoA/FTM/UWB/AoA observations IS a Path D pattern. CSI fingerprint mode is most spectrally direct.
- **BLE + ESP-NOW dual-transport** → control plane + data plane separation; classic telecom architecture pattern.
- **Phase-6r drift-continuation-during-disconnect** → closed-form spectral primitive (`g(t) = drift_rate · t` extrapolation) sitting in substrate context.

### Productisation candidates (in approximate roadmap order)

1. **`srmech.kernels.utlp` — UTLP beacon-history spectral index** — Path D demo on project's own infrastructure
2. **`srmech.kernels.rfip` — RFIP-CSI-fingerprint similarity** — Path D in radio-positioning domain
3. **`srmech.kernels.satellite_constellation` — TLE catalogue spectral index** — open-data demo (CelesTrak), structurally identical to ephemerides 52-body Fiedler
4. **`srmech.kernels.ofdm_eq` — OFDM equaliser config catalogue** — pure-config closed-form `g(λ)` family
5. **`srmech.kernels.spectrum_allocation` — ITU-R/3GPP/IEEE/FCC band allocation cyclic groups** — AMSC-attested table + HDC binding via `SpectrumPhase4096BIP`

## Disability-accommodation dimension (per memory)

Telecom is the substrate of accessibility tech:

- **Hearing impairment**: Bluetooth LE Audio with LC3 codec (Auracast); cochlear-implant streaming; bone-conduction over BLE
- **Visual impairment / blindness**: BLE-beacon indoor wayfinding; RFIP would directly serve this; audio-only telecom modalities
- **Aphantasia** (user has it): non-visual coordination via timing (UTLP) + audio + haptic (motor); telecom is the cross-modality glue
- **Photosensitivity / migraine**: telecom enables non-flicker delivery
- **Cognitive load / ADHD / executive-function**: BLE Smart pairing / NFC-tap reduces setup friction
- **Motor disabilities**: BLE switch-control assistive devices (Apple Switch Control / Android Switch Access)
- **Speech impairments**: AAC (Augmentative and Alternative Communication) over BLE
- **eSIM accessibility** for cognitively/physically demanding SIM swaps

## Trauma-informed defensive scope (per memory)

- ✅ **Mesh-network failover after disaster** — defensive scope (post-earthquake / post-hurricane civilian comms restoration); ship physics + standards refs (LoRaWAN, MeshTastic, BLE Mesh, Iridium PTT)
- ✅ **Crisis-line / 911 / emergency-broadcast resilience** — defensive scope; cite IETF RFC 7852, 3GPP TS 22.071
- ✅ **Time-sync hardening against spoofing** — defensive (UTLP's "Common Mode Rejection" already has this framing)
- ❌ **NEVER**: targeting, jamming, capability-assessment, offensive-EW. Document the math and standards; refuse to elaborate operational application for any offensive purpose.

## Comparison: main-agent vs sub-agent

| Dimension | Main-agent (with conversation context) | Sub-agent (independent fresh-read) |
|---|---|---|
| Manifolds | ~20 | **~30+** (more thorough on Euclidean 1D/2D split, special-structure substrate-leaning) |
| Transforms | ~25 | **37 named** (added: cyclostationary spectral correlation, FBMC, GFDM, OTFS, vector spherical harmonics, Khatri-Rao tensor decomposition, NUFFT, DPSS multitaper, Wigner-Ville / Cohen's class) |
| Closed-form ops | 50+ | **80+ in 11 named families** with explicit standard citations |
| Substrate primitives | 25 | **52 explicit** (added: Cowell/Encke orbital propagation, RAIM, TRIAD/QUEST attitude, BGP/AQM/MPLS/SDN networking, Kyber/Dilithium PQ-crypto) |
| **OFDM = identity claim** | Implied | **Sharp framing**: "OFDM literally is the (DFT, subcarrier-frequency, channel-equaliser-coefficient) decomposition — operating principle of every modern wireless standard" |
| **UTLP project-internal framing** | Caught | **Sharper**: "the project has been shipping a connectionless distributed-coordination telecom protocol since v0.3.0-beta.1, without using the word telecom" |
| **Path-D-on-UTLP demo proposal** | Mentioned | **Concrete v0.27.x roadmap candidate** with 6 named productisation kernels |
| Citation specificity | 3GPP TS / IEEE 802 names | **Specific section numbers** — 3GPP TS 38.211 §4.4, §5.1, §5.2.2, §6.3.1.5; IEEE 802.11ax §27.5 |
| Standards corpus | Listed families | **Comprehensive** — ITU-T (G/M/K), ITU-R (M.2150 IMT-2020, P-series, S-series, SM-series), 3GPP TS+TR, IEEE 802 family, IETF RFC, DVB, ETSI, CCSDS, FCC Part 15/25/80/90/95, ISO/IEC |
| **HDC cousin naming** | Implied AudioPhase12BIP-cousin | **Multiple named**: `SpectrumPhase4096BIP`, `OfdmGridPhaseBIP`, `IPMACPhaseBIP`, `TLEPhaseBIP` |
| **Disability-accommodation memory** | Caught (BLE switch / AAC) | **Applied broadly** with 8 distinct accessibility dimensions |
| **Trauma-informed memory** | Missed | **Applied** with explicit ✅/❌ defensive boundary |
| OTFS as 6G candidate | Caught | Caught |
| **Inter-planetary internet / DTN Bundle Protocol** | Missed | **Caught** — IETF RFC 5050, CCSDS 734.2-B-1 |
| **CCSDS for satellite TT&C** | Missed | **Caught** — 132.0-B (TM Space Data Link), 133.0-B (TC) |
| **Standards version drift caveat** (release-attestation discipline) | Missed | **Caught** — 3GPP releases 8–19 each redefine table values |
| **Encryption breaks spectral analysis caveat** | Missed | **Caught** — AES-encrypted payload looks like white noise; substrate-level header parsing provides spectral surface |
| **CP enforces DFT diagonalisation caveat** | Missed | **Caught** — non-obvious framework-edge |

**Convergent core:** all 10 headline findings above. Highest cross-pollination breadth + most cyclic-group-rich HDC alphabets + strongest project-mission infrastructure fit of any round.

**Sub-agent's biggest unique contributions:**
1. Standards version drift discipline (release-attestation in AMSC catalogues)
2. Encryption-breaks-spectral-analysis caveat (sharp framework-edge note)
3. CP-enforces-DFT-diagonalisation caveat
4. Inter-planetary internet / DTN Bundle Protocol (multi-domain scope)
5. CCSDS coverage for satellite TT&C
6. Multiple BIP-cousin naming discipline (4 explicit `SkPhase9BIP` siblings)
7. 6 productisation kernels with project-roadmap relevance ordering

## Takeaways landed in master srmech notebook

- §3.5 cross-manifold table: telecom instantiation column added (terrestrial + orbital). **OFDM = identity claim**: "OFDM IS the (Transform=DFT, λ_k=subcarrier-frequency, g(λ_k)=channel-equaliser-coefficient) decomposition — operating principle of every modern wireless standard"
- §4.2 calibration: telecom profile is **~70/30, intermediate** between graphics/audio (80/20) and protein/power (20/80–30/70). **Pattern: substrate dominates where physics nonlinearly state-coupled; closed-form dominates in passive signal-processing; telecom intermediate because both apply.**
- §5.4 absorption-round subsection (next): headline findings + link to this file. **OFDM-is-identity + UTLP-is-telecom + Path-D-on-UTLP-demo framing is the load-bearing contribution.**
- §1.5 future-notebook candidates: telecom row added (status: scoped; **strongest project-mission infrastructure fit**; UTLP/RFIP direct connection; productisation-relevant for v0.27.x to v0.28.x)
- §5.4 dual-agent pattern subsection: telecom round confirms convergence pattern across 4 rounds (graphics, audio, protein, telecom). Sub-agent consistently catches: memory application (disability + trauma), citation specificity, framework-edge caveats. Main agent consistently catches: framework-edge first-principles, cross-conversation synthesis. Combined > either alone.
