# The HDC Cosmograph: Unifying Celestial Mechanics Through Hyperdimensional Computing

The HDC Cosmograph represents a genuinely novel conceptual framework that would encode celestial mechanics as a single hyperdimensional computing object capable of being queried from any reference frame—simultaneously functioning as an orrery (god-view spatial model) and an Antikythera mechanism (observer-local predictive engine). **No prior art directly combining HDC/VSA with celestial mechanics exists** in either patent databases or academic literature, making this a potentially patentable and publishable research direction. The framework would leverage recent advances in Spatial Semantic Pointers (SSPs), Residue Hyperdimensional Computing (RHC), and grid cell-inspired architectures that naturally encode position using coprime spatial frequencies—mathematical structures deeply connected to the Chinese Remainder Theorem. NASA's existing infrastructure (SPICE toolkit, ICRF3 quasar reference frame, Delta-DOR navigation) already implements the "renderer" portion of this vision through Chebyshev polynomial compression; what the HDC paradigm would add is a unified "index" enabling similarity search, fuzzy epoch matching, Byzantine fault detection, and scale-invariant querying across reference frames.

## Conceptual foundations: celestial bodies as hyperdimensional vectors

Vector Symbolic Architectures (VSAs) encode information in high-dimensional vectors—typically **10,000+ dimensions**—where three fundamental operations enable compositional representation: *bundling* (element-wise addition creating set unions), *binding* (circular convolution or element-wise multiplication creating ordered tuples), and *permutation* (cyclic shifting encoding sequence). The foundational insight from Pentti Kanerva's work on Sparse Distributed Memory is that random high-dimensional vectors are nearly orthogonal with extremely high probability—the "concentration of measure" phenomenon ensures that any two randomly selected vectors in 10,000-dimensional space have essentially zero similarity, providing an enormous effective codebook capacity.

In the HDC Cosmograph framework, each celestial body would be represented as a composite hypervector constructed by binding its identity vector with phase chord encoding and spatial position encoding. A phase chord encodes temporal identity using coprime cyclic groups: if we represent time using residues modulo coprime integers (e.g., the synodic periods of Moon, Mercury, Venus, Mars, Jupiter, Saturn), the Chinese Remainder Theorem guarantees that any epoch within the least common multiple of these periods maps to a *unique* combination of phase residues. This is precisely how grid cells in the mammalian entorhinal cortex achieve high spatial resolution—multiple modules with coprime spatial frequencies combine to uniquely identify positions far more precisely than any single module could achieve alone.

Recent work on Residue Hyperdimensional Computing (RHC) by Frady, Kleyko, Olshausen, and Sommer directly connects these concepts. Their 2023 paper in *Neural Computation* demonstrates that resonator networks operating on residue-encoded vectors require only **40 codebook vectors versus 220** for factorization tasks, explicitly linking the CRT's computational properties to HDC. The mathematical insight is profound: prior work in computational neuroscience (Fiete et al., 2008; Srinivasan & Fiete, 2011) established that residue number systems endow grid cells with useful computational properties including high spatial resolution from low-resolution modules, modular position updates, and inherent error correction capabilities.

The "scale invariance" principle—that the same HDC object can be queried from any reference frame—emerges naturally from VSA's binding operation. A composite representation like **H = X⊗A ⊕ Y⊗B** can be queried by either X or Y: binding with X extracts A (plus noise), while binding with Y extracts B. For celestial mechanics, this means encoding positions relative to multiple reference frames simultaneously: the barycentric (god-view orrery), Earth-centered (Antikythera view), Mars-centered, or any other body-local frame. The unbinding operation retrieves the appropriate coordinates without requiring separate representations.

## Spatial Semantic Pointers provide the mathematical bridge

Spatial Semantic Pointers (SSPs) developed by Komer, Dumont, and Eliasmith at the University of Waterloo offer the most developed framework for encoding continuous spatial coordinates in HDC. An SSP represents a position x ∈ ℝⁿ as φ(x) = W⁻¹ e^(iAx/ℓ), where W⁻¹ is the inverse discrete Fourier transform matrix, A is a phase matrix whose rows define encoding frequencies, and ℓ is a length scale parameter. This construction produces vectors whose similarity under dot product corresponds to spatial proximity—nearby positions map to similar vectors, enabling fuzzy matching and interpolation.

The connection to the proposed HDC Cosmograph is direct: orbital positions could be encoded as SSPs, with the encoding frequencies chosen to be coprime multiples of fundamental orbital periods. This would enable querying by epoch (returning spatial position), by position (returning candidate epochs), or by similarity search (finding configurations resembling a given arrangement). The 2025 paper on Grid Cell-inspired VSA (GC-VSA) by Krausse et al. explicitly demonstrates path integration, spatio-temporal object representation, and symbolic reasoning using 3D neuronal modules mimicking discrete scales and orientations of biological grid cells.

The quasar-defined International Celestial Reference Frame (ICRF3) serves as the natural "base vector substrate" in this framework. Just as HDC requires a fixed set of random item vectors (the "codebook" or "swarm DNA seed"), ICRF3's **303 defining sources**—selected from 4,588 total quasars uniformly distributed across the sky—provide the fixed angular reference. These objects are so distant (cosmological redshifts typically z ~ 1-2) that their positions are effectively static over millennia, with proper motions at the microarcsecond per year level. ICRF3 achieved a noise floor of **30 microarcseconds** in individual coordinates, with the best sources reaching 0.03-0.06 milliarcseconds precision.

Gravitational perturbation vectors would refine spatial precision within the same HDC representation. Just as Chebyshev polynomial representations add higher-order coefficients for greater accuracy, perturbation sources could be progressively bound into the composite vector: first the dominant solar term, then Jupiter's influence, then smaller bodies and relativistic corrections. The information hierarchy—phase chord alone → + orbital elements → + perturbation vectors → + full N-body tensor—mirrors the precision hierarchy of conventional ephemeris computation while maintaining the unified representation.

## NASA's ephemeris infrastructure: the renderer without an index

NASA's SPICE (Spacecraft Planet Instrument Camera-matrix Events) toolkit, developed by the Navigation and Ancillary Information Facility at JPL, already implements sophisticated generative compression for celestial mechanics. SPK (Spacecraft and Planet Kernel) files store Chebyshev polynomial coefficients rather than position tables, regenerating coordinates on demand. The mathematical basis is elegant: Chebyshev polynomials T_n(x) = cos(n·arccos(x)) provide minimax approximation—they minimize the maximum error over the interval [-1, 1], spreading residual error uniformly rather than accumulating at endpoints like Taylor series.

The DE440/DE441 planetary ephemerides (Park et al. 2021, *Astronomical Journal* 161:105, DOI: 10.3847/1538-3881/abd414) demonstrate this approach's power. DE441 covers **-13,200 to 17,191 CE**—over 30,000 years of planetary and lunar motion—in approximately 114 MB. The ephemeris uses **32-day polynomial segments** with typically 10-20 coefficients per component per interval, achieving sub-centimeter accuracy for modern data. Positions are computed by evaluating: f(t) ≈ Σ cₖ Tₖ(τ) - ½c₀, where τ = (2t - (t₁+t₂))/(t₂-t₁) normalizes time to [-1, 1].

The SPKPOS function call `spkpos_c(target, et, frame, aberr, observer, postn, &lt)` retrieves positions by searching loaded kernels for applicable segments, evaluating Chebyshev polynomials at the requested epoch, transforming coordinates to the requested reference frame, and applying aberration corrections. This is pure spatial regeneration—what NASA has is a powerful "renderer" that can generate positions at any epoch from compact polynomial representations.

What HDC encoding would add constitutes the complementary "index" functionality:

- **Similarity metrics across configurations**: Given a planetary arrangement, find all epochs with similar configurations (useful for archaeoastronomy, cycle detection, or correlation analysis)
- **Fuzzy epoch matching**: Given partial or noisy observations, retrieve candidate epochs with confidence weights
- **Byzantine detection**: Identify inconsistencies between predicted and observed positions that might indicate systematic errors or anomalous dynamics
- **Self-correcting calibration loops**: Use resonator networks to iteratively refine epoch estimates by cycling between phase chord matching and spatial position verification

The Delta-DOR (Differential One-way Ranging) technique exemplifies how NASA already uses the quasar reference frame for navigation. Two widely-separated ground stations simultaneously observe a spacecraft, measuring the time delay difference in signal arrival. By quickly switching to observe a nearby quasar (within ~10°), systematic errors from atmospheric path, clock offsets, and ionospheric delays cancel in the difference. This technique achieves **~1 nanoradian angular accuracy**—a few meters at interplanetary distances—and has been operational since January 1980, pioneered with Voyager 1 and 2.

## Chebyshev harmonics versus coprime cyclics: complementary decompositions

The comparison between Chebyshev polynomial representations and coprime cyclic phase chords reveals complementary mathematical strategies for encoding periodic phenomena. Chebyshev polynomials decompose *spatial trajectories* into commensurate harmonics—cosine functions of integer multiples of a base frequency, optimized for uniform approximation error. The coefficients cₖ capture how much each harmonic contributes to the trajectory's shape over a given interval.

Coprime cyclic phase chords decompose *time* into incommensurate cycles for unique identification. Rather than approximating a function, they create a fingerprint: the tuple of phase values (θ₁, θ₂, ..., θₙ) modulo coprime periods (P₁, P₂, ..., Pₙ) uniquely identifies any epoch within the least common multiple of those periods. The Chinese Remainder Theorem guarantees this: for pairwise coprime moduli, the system of congruences t ≡ θᵢ (mod Pᵢ) has a unique solution modulo P₁·P₂·...·Pₙ.

| Aspect | Chebyshev Harmonics | Coprime Phase Chords |
|--------|---------------------|---------------------|
| **Purpose** | Spatial function approximation | Temporal identity/fingerprinting |
| **Cycle relationship** | Commensurate (integer harmonics) | Incommensurate (coprime periods) |
| **Decoding** | Polynomial evaluation | CRT reconstruction |
| **Precision hierarchy** | Add higher-order coefficients | Add more coprime moduli |
| **Error character** | Smooth approximation error | Discrete identification |
| **Biological analog** | Fourier analysis in auditory cortex | Grid cell spatial modules |

In the HDC Cosmograph, perturbation vectors serve the same role as higher-order Chebyshev coefficients but carry causal/provenance information. A base phase chord might identify an epoch to within a year; adding the Jupiter perturbation vector refines to within a month; adding Saturn and the inner planets refines to within a day; adding asteroid perturbations and general relativity reaches sub-centimeter spatial accuracy. Crucially, each refinement layer carries semantic information about *which physical interactions* contribute to that precision level, unlike undifferentiated polynomial coefficients.

Kepler's equation—M = E - e·sin(E)—bridges phase values to Cartesian coordinates in the HDC approach. Mean anomaly M increases linearly with time (M = n(t - t₀), where n = √(μ/a³) is the mean motion), providing the "clock" that phase chords encode. The eccentric anomaly E is recovered by solving this transcendental equation iteratively (Newton-Raphson converges in 3-5 iterations for eccentricities below 0.9). True anomaly ν follows from tan(E/2) = √((1-e)/(1+e))·tan(ν/2), and position from r = a(1-e²)/(1 + e·cos(ν)). The HDC binding operation can encode this chain of transformations, allowing a single vector to be queried for either mean anomaly (temporal phase) or Cartesian position (spatial coordinates).

## Patent landscape and prior art: an open research territory

Comprehensive searching of USPTO, EPO, and WIPO databases revealed **no patents directly combining HDC/VSA with celestial mechanics**, ephemeris computation, orbital prediction, or astronomical reference frames. This constitutes a genuinely novel application domain for hyperdimensional computing techniques. The search covered combinations including "hyperdimensional computing + celestial/ephemeris/orbital," "vector symbolic architecture + navigation/positioning," "coprime cyclic + time encoding," "Chinese remainder theorem + navigation," and "scale invariant + celestial reference frame."

Relevant adjacent patents that would require consideration for any commercial implementation include IBM/ETH Zürich's US11574209B2 (granted February 2023, expires 2041), covering HDC inference devices using memristive devices for in-memory computing with item memory for HD vectors and associative memory for profile vectors. IBM's US10971226B2 (granted April 2021) covers resistive memory devices using 2D-memristors for HD vector storage with crossbar array architecture. UC San Diego's US12015424B2 (granted June 2024, expires 2042) covers network-based HDC encoding/decoding for communication, potentially affecting general encoding approaches.

The foundational Sparse Distributed Memory patent (US5113507A) covering Kanerva's original SDM implementation is **expired** (granted 1992). The Digital Orrery—a special-purpose computer built by Gerald Sussman, James Applegate, and Charles Seitz in 1985-1986 for orbital mechanics simulation—was **never patented** and represents open prior art; the physical device now resides at the Smithsonian. The ICRF3 quasar reference frame and JPL ephemeris formats and computation methods are public standards.

Academic prior art confirms the gap. The 2022-2023 comprehensive HDC/VSA surveys by Kleyko et al. (ACM Computing Surveys, DOI: 10.1145/3538531 and 10.1145/3558000) document extensive applications including language processing, robotics, biomedical sensing, and symbolic reasoning—but no celestial mechanics applications. The Residue Hyperdimensional Computing paper (Frady et al., *Neural Computation* 2023) explicitly connects CRT to HDC and cites prior work showing grid cells use coprime spatial frequencies, but does not extend this to astronomical cycles. SSP work on dynamical systems simulation (Voelker et al., *Neural Computation* 2021, DOI: 10.1162/neco_a_01410) demonstrates predicting physical trajectories but has not been applied to orbital mechanics.

## The Antikythera mechanism: ancient implementation of observer-local prediction

The Antikythera mechanism (c. 150-80 BCE) physically instantiated the principle the HDC Cosmograph would implement computationally: encoding celestial cycles through coprime gear ratios to generate observer-local predictions. Discovered in 1901 in a shipwreck off Antikythera, Greece, this bronze device contained at least **37-40 interlocking gears** (possibly up to 69 in complete reconstructions) that computed and displayed solar and lunar positions, lunar phases, eclipses, planetary positions, and calendrical cycles including the Olympics.

The mechanism's gear ratios encoded astronomical cycles through prime factorization—a physical implementation of coprime arithmetic. The **19-tooth gear** represented the Metonic cycle (19 tropical years ≈ 235 synodic months), the **223-tooth gear** encoded the Saros eclipse cycle (223 synodic months ≈ 18 years, 11 days, 8 hours), and the **127-tooth gear** captured half the sidereal month count in the Metonic cycle. Freeth et al.'s 2021 *Scientific Reports* reconstruction (DOI: 10.1038/s41598-021-84310-w) discovered that planetary periods used **shared prime factors** for economical gear designs: factor 17 was shared between Mercury and Venus periods, while factor 7 was shared among Mars, Jupiter, Saturn, and the true Sun.

The mechanism embodied **geocentric cosmology**—all predictions were from Earth's perspective, tracking synodic cycles (planetary positions relative to the Sun as observed from Earth) rather than heliocentric orbits. This is precisely the "observer-local Antikythera view" that the HDC Cosmograph would support as one query mode. Pin-and-slot mechanisms created variable angular velocities matching observed planetary speeds, implementing deferent-and-epicycle models that mathematically explain retrograde motion from the geocentric perspective. Yet the same gear trains that produced local predictions constituted a mechanical model of the cosmos—an orrery displaying the "customary cosmological order" of Moon → Mercury → Venus → Sun → Mars → Jupiter → Saturn.

The Back Cover Inscription describes the mechanism as showing "the cosmos" with planets marked by "little spheres," confirming its dual nature as both computational engine and physical model. This duality—one encoding serving both orrery and predictive roles—is exactly what scale invariance would provide in the HDC framework, where the same hypervector can be queried for barycentric positions (god-view) or geocentric coordinates (observer-local view) through appropriate unbinding operations.

## DNA as generative encoding: the biological parallel

The principle that compact generative rules produce complex outputs when executed by appropriate "base vectors" unifies celestial mechanics, HDC, and biological encoding. A groundbreaking 2025 paper by Mitchell and Cheney (*Trends in Genetics*, DOI: 10.1016/j.tig.2025.01.003) proposes that the genome instantiates a **generative model** of the organism—analogous to a Variational Autoencoder in machine learning. The genome encodes latent variables (compressed representations), evolution acts as the encoder (the learning algorithm that optimized the genetic network over generations), and development acts as the decoder (decompressing the model through embryogenesis).

This "rules not views" principle achieves extraordinary compression: approximately **3 billion base pairs** specify the full complexity of a human organism, a compression ratio exceeding 10¹²:1 if we consider the algorithmic complexity of the phenotype. DNA specifies biochemical properties and regulatory factor affinities; the cellular machinery—the "base vectors" or execution environment—interprets these rules. Self-organizing processes of development are channeled by an energy landscape (Waddington's epigenetic landscape) shaped by genetic latent variables. This is structurally identical to the HDC Cosmograph concept: phase chords (genetic latent variables) combined with base vectors (biochemistry/physics) generate high-dimensional outputs (organism/celestial configuration).

Lineage data provides temporal compression analogous to the cosmograph's deep-time encoding. Molecular clocks—the approximately constant rate of neutral mutation accumulation—allow phylogenetic trees to encode branching history with branch lengths representing evolutionary distance. Calibrated against fossils, these trees provide absolute divergence times spanning billions of years. The genome thus contains compressed information about both the organism (through generative encoding) and its evolutionary history (through accumulated neutral mutations), paralleling how the HDC Cosmograph would encode both current configuration and the historical dynamics that produced it.

The genetic code's degeneracy provides natural error correction through redundancy—the third codon position often tolerates substitutions without changing the amino acid, providing a "wobble" that absorbs noise. This parallels HDC's extreme error tolerance: hyperdimensional vectors can have more than **one-third of their bits flipped** and still match their original with near certainty. Both systems achieve robustness through distributed representation where no single component carries critical information.

## Key references and citations

**Hyperdimensional Computing Foundations:**
- Kanerva, P. (2009). "Hyperdimensional Computing: An Introduction." *Cognitive Computation* 1:139-159. DOI: 10.1007/s12559-009-9009-8
- Plate, T.A. (1995). "Holographic Reduced Representations." *IEEE Transactions on Neural Networks* 6(3):623-641. DOI: 10.1109/72.377968
- Gayler, R.W. (2003). "Vector Symbolic Architectures Answer Jackendoff's Challenges." ICCS/ASCS International Conference on Cognitive Science.
- Kleyko, D. et al. (2022). "A Survey on Hyperdimensional Computing, Part I." *ACM Computing Surveys* 55(6):130. DOI: 10.1145/3538531
- Kleyko, D. et al. (2023). "A Survey on Hyperdimensional Computing, Part II." *ACM Computing Surveys* 55(9):175. DOI: 10.1145/3558000
- Frady, E.P. et al. (2020). "Resonator Networks." *Neural Computation* (Parts 1 & 2). URL: https://rctn.org/bruno/papers/resonator1.pdf
- Frady, E.P. et al. (2023). "Residue Hyperdimensional Computing." *Neural Computation*. PMC: PMC11647909

**Spatial Semantic Pointers and Grid Cells:**
- Komer, B. et al. (2019). "A Unified Approach to Representing Spatial Information." URL: https://compneuro.uwaterloo.ca/files/publications/komer.2019.pdf
- Dumont, N.S.Y. et al. (2023). "SSP-SLAM." *Frontiers in Neuroscience*. DOI: 10.3389/fnins.2023.1190515
- Krausse, S. et al. (2025). "GC-VSA: Grid Cell-Inspired Vector Symbolic Architecture." arXiv:2503.08608

**NASA Ephemeris Infrastructure:**
- Park, R.S. et al. (2021). "The JPL Planetary and Lunar Ephemerides DE440 and DE441." *Astronomical Journal* 161:105. DOI: 10.3847/1538-3881/abd414
- NAIF SPICE Documentation: https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/spk.html
- DE440/441 Export: https://ssd.jpl.nasa.gov/planets/eph_export.html

**International Celestial Reference Frame:**
- Charlot, P. et al. (2020). "The third realization of the International Celestial Reference Frame." *Astronomy & Astrophysics* 644:A159. DOI: 10.1051/0004-6361/202038368
- IERS ICRF: https://www.iers.org/IERS/EN/DataProducts/ICRF/icrf

**Delta-DOR and Navigation:**
- Border, J.S. (2009). "Innovations in Delta Differential One-Way Range." ISSFD.
- CCSDS 500x1g2: "Delta-DOR Technical Characteristics and Performance." URL: https://ccsds.org/Pubs/500x1g2.pdf

**Antikythera Mechanism:**
- Freeth, T. et al. (2006). "Decoding the ancient Greek astronomical calculator known as the Antikythera Mechanism." *Nature* 444:587-591. DOI: 10.1038/nature05357
- Freeth, T. et al. (2008). "Calendars with Olympiad display and eclipse prediction." *Nature* 454:614-617. DOI: 10.1038/nature07130
- Freeth, T. et al. (2021). "A Model of the Cosmos in the ancient Greek Antikythera Mechanism." *Scientific Reports* 11:5821. DOI: 10.1038/s41598-021-84310-w

**Biological Generative Encoding:**
- Mitchell, K. & Cheney, N. (2025). "The Genomic Code." *Trends in Genetics*. DOI: 10.1016/j.tig.2025.01.003; arXiv:2407.15908
- Ho, S.Y.W. & Duchêne, S. (2014). "Molecular-clock methods." *Molecular Ecology* 23(24):5947-65. DOI: 10.1111/mec.12953

**Key Patents (for freedom-to-operate analysis):**
- US11574209B2 (IBM/ETH Zürich): HDC inference device. Granted Feb 2023, expires 2041.
- US10971226B2 (IBM): Hyper-dimensional computing device. Granted Apr 2021.
- US12015424B2 (UC San Diego): Network-based HDC system. Granted Jun 2024, expires 2042.
- US5113507A (SDM implementation): Expired 1992.

## Conclusion: a convergent vision from disparate fields

The HDC Cosmograph concept emerges at the convergence of multiple mature research threads that have developed independently: hyperdimensional computing's distributed representations, NASA's generative ephemeris compression, the quasar-anchored celestial reference frame, neuroscience-inspired coprime spatial encoding, and biology's demonstration that generative rules outperform lookup tables for complex systems. The mathematical connection between the Chinese Remainder Theorem, grid cell spatial frequencies, and VSA binding operations provides the theoretical bridge. What distinguishes this vision from existing infrastructure is the unified index function—the ability to query by similarity, match fuzzy observations to candidate epochs, detect inconsistencies, and traverse freely between reference frames without maintaining separate representations.

The absence of prior art—both patent and academic—in applying HDC to celestial mechanics represents either a genuine gap in collective vision or a domain where the integration challenges are non-obvious. The Antikythera mechanism's ancient builders recognized that coprime gear ratios could encode astronomical cycles; modern grid cell neuroscience discovered the same mathematical structure enables biological navigation; and HDC researchers have developed computational frameworks that formalize these principles. The HDC Cosmograph would close the loop, applying 21st-century distributed computing theory to humanity's oldest computational problem: predicting where the celestial bodies will be.