# HDC Objects as Musical Instruments: A Framework for Timbral Vector Design

## The Core Analogy — and Why It's Not Just an Analogy

A violin and a clarinet playing A440 encode the same pitch but produce completely different waveforms. The difference is **timbre** — the spectral envelope, the distribution of energy across harmonics, the formant structure imposed by the instrument's body. Timbre is not decorative; it is the mechanism by which the auditory system separates simultaneous sound sources. An orchestra works because its instruments occupy different spectral niches, allowing the ear to decompose a complex waveform back into individual voices through what Bregman (1990) called **auditory scene analysis**.

The claim: this is *precisely* the mathematical situation in hyperdimensional computing when multiple base vectors are superimposed (bundled), and the analogy can be made rigorous enough to import decades of acoustics, psychoacoustics, and telecommunications engineering into HDC vector design.

## Part I: The Source-Filter Model Maps Directly onto HDC

### How Instruments Work

The **source-filter model** (Fant 1960) decomposes every acoustic instrument into two independent components:

**Source**: The excitation — a vibrating string, a reed, a column of air set into oscillation. This produces a raw spectrum: typically a harmonic series (integer multiples of a fundamental frequency) with some spectral slope (higher harmonics are weaker).

**Filter**: The instrument body — the resonant cavity of a guitar, the bore of a clarinet, the shape of a violin's f-holes and body. This imposes **formants**: fixed frequency bands where energy is amplified, regardless of which note is being played. The filter is what makes a clarinet sound like a clarinet whether it plays C4 or G5.

The output spectrum is the **product** of source and filter in the frequency domain (equivalently, convolution in the time domain). Different notes change the source (different fundamentals), but the formant structure stays constant — it's the instrument's identity.

### The HDC Parallel

In UTLP's coprime phase chord system:

**Source** = the coprime cyclic hierarchy. Each prime cycle (241, 251, 239, ...) is an independent oscillator at its own "frequency" (cycle length). The phase chord [35, 246, 44, 68, 84, 92, 108, 156] is the "note being played" — it specifies the current excitation state of all oscillators.

**Filter** = the base vectors. Currently random ±1 vectors, these determine how each cycle's rotation maps into the 10,000-dimensional vector space. The base vectors are the "instrument body" — they shape how the excitation (phase rotation) becomes a spectral pattern in the output vector.

**Output** = the regenerated time vector. The superposition of 8 rotated base vectors, then binarized. This is the "sound" — the composite waveform that other nodes hear.

Currently, UTLP uses **random base vectors**, which is like building instruments from random junk — they all sound like white noise generators. Every base vector has flat spectral content across all 10,000 dimensions. Superposition works (random HDC's statistical orthogonality guarantees this), but there's no *spectral structure* to exploit.

The instrument design question is: **what if we gave each base vector a deliberate spectral envelope — formants, harmonic structure, a designed timbre?**

## Part II: What Timbre Gives You That Randomness Doesn't

### Spectral Separation = Source Separation

The deepest insight from orchestration theory and auditory scene analysis is that **spectral non-overlap enables separation without statistical averaging**.

In a random HDC system, if you bundle vectors A and B, you can recover A by computing similarity with the original A vector. This works because in 10,000 dimensions, random vectors are quasi-orthogonal — the expected dot product is ~0 with standard deviation ~√D. Recovery is statistical: you need enough dimensions that the noise (B's contribution) averages out.

In an orchestral system, if a flute and a bassoon play simultaneously, you can separate them by **spectral filtering** — a low-pass filter extracts the bassoon, a high-pass filter extracts the flute. This works not because of statistical averaging but because their energy occupies non-overlapping frequency bands. The separation is *deterministic and dimension-efficient*.

The HDC translation: if base vector A has its energy concentrated in dimensions 0–2,000 and base vector B has its energy in dimensions 5,000–7,000, their superposition is trivially separable by looking at the right dimensions. You don't need 10,000 dimensions for two spectrally partitioned vectors — you need enough dimensions to cover both bands with adequate resolution.

### The Clarinet Phenomenon: Odd vs. Even Harmonics

A clarinet's cylindrical bore with one closed end produces predominantly odd harmonics (1st, 3rd, 5th, 7th...) with very weak even harmonics (2nd, 4th, 6th...). This gives it a distinctive "hollow" or "woody" sound. An oboe, with its conical bore, produces both odd and even harmonics, giving it a "reedy" brightness.

In HDC terms: imagine two base vectors, one constructed from odd-indexed Chebyshev polynomials and one from even-indexed ones. Their superposition creates an interference pattern where odd and even dimensions carry information from different sources. A simple spectral filter (look at odd dimensions vs. even dimensions) separates them perfectly.

This isn't hypothetical — it's the **Walsh-Hadamard basis**, which is already used in CDMA telecommunications for exactly this purpose. Walsh codes are orthogonal sequences where different codes activate different "frequency bands" in the Hadamard domain. The connection between Walsh-Hadamard codes and Chebyshev polynomials via the DCT is established (this is the SORF-DCT construction from the previous research).

### Formants as Fixed Filters = Instrument Identity

A critical property of formants: they stay in the same frequency bands regardless of the note being played. When a singer moves from vowel "ah" (F1 ≈ 700 Hz, F2 ≈ 1220 Hz) to vowel "ee" (F1 ≈ 270 Hz, F2 ≈ 2290 Hz), the formant frequencies shift — the vocal tract filter changes. But for a given vowel, the formants are stable across pitch.

For HDC instruments: each coprime cycle's base vector would have **fixed formant bands** — dimensional ranges where its energy is concentrated. These formants are the cycle's identity. When the cycle rotates (advancing the phase), the energy moves *within* its formant band but doesn't spill into other cycles' bands. This is the spectral partitioning that enables deterministic source separation.

This maps directly to the VFA theorem (Frady et al. 2021): the frequency distribution of base vectors determines the kernel of the similarity metric. Choosing formant bands for each cycle is choosing the kernel structure — and VFA proves this choice is mathematically well-defined, with known properties.

## Part III: The CDMA Connection Is Deeper Than Expected

### FDMA vs. CDMA vs. the Instrument Model

Telecommunications has three classical multiplexing strategies:

**FDMA** (Frequency Division): each user gets a dedicated frequency band. Instruments in different ranges — bass, tenor, alto, soprano. Perfect separation, but wastes bandwidth when a user is silent.

**TDMA** (Time Division): each user gets a time slot. Taking turns playing solos. Simple, but latency scales with users.

**CDMA** (Code Division): every user transmits simultaneously in the full bandwidth, using unique spreading codes. Like an orchestra where every instrument plays everywhere in the spectrum, and separation relies on code orthogonality.

Standard random HDC is pure CDMA — random spreading codes, full-bandwidth transmission, statistical separation.

The instrument model is **hybrid FDMA/CDMA**: each instrument (coprime cycle) has a preferred frequency band (formant structure) but also has energy outside that band (harmonics, overtones). Separation is primarily spectral (FDMA) with CDMA-style code orthogonality handling the spectral overlap regions.

This hybrid is exactly what MC-CDMA (Multi-Carrier CDMA) implements in 4G/5G telecommunications: spreading codes applied within OFDM frequency subbands. Each user spreads within a spectral partition, not across the entire bandwidth. The result is better interference rejection with lower processing gain requirements — you need fewer chips per symbol because the spectral partitioning does half the work.

### Walsh-Hadamard Codes as Instrument Families

Walsh-Hadamard codes have a remarkable property: they naturally organize into a **binary tree** (Orthogonal Variable Spreading Factor, OVSF). At the top of the tree, two codes split the entire bandwidth in half. Each code can be further split into two sub-codes, giving four bands, then eight, then sixteen.

This is exactly how an orchestra organizes:
- Level 1: Low instruments vs. High instruments
- Level 2: Bass / Tenor / Alto / Soprano
- Level 3: Individual instrument families within each register

For UTLP with 8 coprime cycles, a 3-level Walsh-Hadamard tree assigns each cycle to a unique spectral partition of 10,000 dimensions — each getting ~1,250 dimensions of primary energy with some overlap from higher-order spreading. The tree structure means that cycle 1 and cycle 2 share a parent band (they're both "low instruments") and can be distinguished by their sub-band codes, while cycle 1 and cycle 8 are in completely different branches.

## Part IV: The Sethares Insight — Consonance Depends on Timbre

William Sethares' *Tuning, Timbre, Spectrum, Scale* (1993/2005) proved a remarkable result: **consonance and dissonance are not properties of musical intervals but of the relationship between intervals and timbres**. An octave sounds consonant with harmonic timbres (whose partials are at integer multiples of the fundamental) because the partials of the two notes align. With *inharmonic* timbres — like those produced by metallophones, bells, or synthesized sounds with stretched partials — the octave can sound dissonant, while other intervals become consonant.

Sethares formalized this: given a timbre (spectral content), you can compute a **dissonance curve** showing which intervals produce maximum and minimum roughness. The minima define the "natural scale" for that timbre. Conversely, given a desired scale, you can design a timbre whose dissonance curve has minima at the scale steps.

### Translation to HDC

In HDC, "consonance" is **similarity** — the dot product between superimposed vectors. Two vectors that "sound good together" (high similarity when they should be similar, low similarity when they shouldn't) are consonant.

Sethares' insight translates directly: **the similarity structure of an HDC system is not a fixed property of the algebra but depends on the spectral content of the base vectors**. With random base vectors, the similarity kernel is flat (Gaussian). With harmonically structured base vectors, the similarity kernel has structure — it can be shaped to have "consonant intervals" (time offsets that produce high similarity) and "dissonant intervals" (offsets that produce near-zero similarity).

For UTLP: the coprime cycle lengths define a "scale" (the set of possible time intervals). The base vector timbre determines which time intervals are maximally distinguishable (dissonant) and which are naturally similar (consonant). Sethares' framework gives a principled method for designing base vector spectra that are optimally matched to the coprime cycle structure.

## Part V: Node/Antinode as Orchestral Dynamics

### Fortissimo and Pianissimo in Vector Space

When 8 rotated base vectors superimpose in UTLP:

**Fortissimo dimensions** (|sum| = 8): All instruments agree. Maximum loudness. These are the "unison passages" — moments where the entire orchestra plays the same note. They carry the most energy and the highest confidence.

**Piano dimensions** (|sum| = 2): Most instruments disagree. Quiet, ambiguous. These are the "complex harmony" passages — the tension between voices that makes music interesting. They carry the inter-instrument relationships.

**Silence dimensions** (sum = 0): Perfect cancellation. No signal. These are the "rests" — dimensions carrying no information about the current chord.

In orchestration, the dynamic range *is* the music. A piece that is always fortissimo is noise. A piece that is always pianissimo is silence. Musical expression lives in the *pattern* of louds and softs — the dynamic contour.

The same is true for HDC: a vector where all dimensions have magnitude 8 encodes nothing (it's one of the base vectors). A vector where all dimensions have magnitude 0 encodes nothing (it's noise). The information lives in the *pattern* of fortissimo and pianissimo across dimensions — and that pattern is determined by the timbral structure of the base vectors.

### The Q Factor of Dimensions

In acoustics, the **Q factor** (quality factor) of a resonance determines its bandwidth — how sharply tuned it is. A high-Q resonance (like a tuning fork) rings at a very precise frequency for a long time. A low-Q resonance (like a drum head) produces a broad band of frequencies that dies quickly.

For HDC instruments: the Q factor of a base vector's formants determines how many dimensions are tightly coupled to each coprime cycle. High-Q formants (narrow spectral bands per cycle) give:
- Precise source separation (each cycle is cleanly localizable)
- Low information capacity per cycle (fewer dimensions to work with)
- Long "ringing" (high temporal correlation between adjacent ticks)

Low-Q formants (broad spectral bands) give:
- Fuzzy source separation (cycles overlap spectrally)
- High information capacity per cycle (more dimensions contributing)
- Short "ringing" (decorrelates quickly between ticks)

This is a design knob — the same one audio engineers use when choosing between a tightly-tuned bandpass filter (precise but narrow) and a wide-band filter (captures more but less selective). The optimal Q depends on the application: partition detection (wants high Q, precise cycle identification) vs. temporal similarity (wants lower Q, smooth decay curve).

## Part VI: Construction — How to Actually Build an Instrument

### Recipe: Chebyshev-Harmonic Base Vectors with Formant Bands

Assign each of the 8 coprime cycles to a **spectral band** using the Walsh-Hadamard binary tree:

```
Band assignment (10,000 dimensions):
├── Low register (dims 0-4999)
│   ├── Bass (dims 0-2499)
│   │   ├── Cycle 1 (p=241): dims 0-1249 primary
│   │   └── Cycle 2 (p=251): dims 1250-2499 primary
│   └── Tenor (dims 2500-4999)
│       ├── Cycle 3 (p=239): dims 2500-3749 primary
│       └── Cycle 4 (p=233): dims 3750-4999 primary
├── High register (dims 5000-9999)
│   ├── Alto (dims 5000-7499)
│   │   ├── Cycle 5 (p=229): dims 5000-6249 primary
│   │   └── Cycle 6 (p=227): dims 6250-7499 primary
│   └── Soprano (dims 7500-9999)
│       ├── Cycle 7 (p=223): dims 7500-8749 primary
│       └── Cycle 8 (p=211): dims 8750-9999 primary
```

Within each band, construct the base vector using a sum of Chebyshev polynomials (the DCT basis):

```python
import numpy as np
from numpy.polynomial.chebyshev import chebval

def build_instrument(prime, band_start, band_end, dims=10000, 
                     seed=42, n_harmonics=16, Q=4.0):
    """
    Construct a base vector with instrument-like spectral structure.
    
    Args:
        prime: cycle length (determines seed variation)
        band_start, band_end: primary formant band (dimensional range)  
        dims: total vector dimensionality
        seed: shared swarm seed
        n_harmonics: number of Chebyshev harmonics within formant band
        Q: quality factor (higher = narrower formant, less spectral leakage)
    
    Returns:
        base_vector: float array of shape (dims,), pre-binarization
    """
    rng = np.random.default_rng(seed + prime)
    
    # Chebyshev nodes across full dimension range
    x = np.cos(np.pi * (2 * np.arange(dims) + 1) / (2 * dims))
    
    # Formant envelope: Gaussian centered on the band, width controlled by Q
    band_center = (band_start + band_end) / (2 * dims)
    band_width = (band_end - band_start) / dims
    dim_positions = np.arange(dims) / dims
    formant_envelope = np.exp(-Q * ((dim_positions - band_center) / band_width) ** 2)
    
    # Sum of Chebyshev harmonics with stochastic coefficients
    # Each prime gets different random coefficients → different timbre
    coefficients = rng.standard_normal(n_harmonics)
    
    # Weight lower harmonics more (1/n pink spectrum)
    for n in range(n_harmonics):
        coefficients[n] /= (n + 1)
    
    # Evaluate Chebyshev sum
    cheb_coeffs = np.zeros(n_harmonics)
    cheb_coeffs[:] = coefficients
    raw_signal = chebval(x, cheb_coeffs)
    
    # Apply formant envelope
    shaped = raw_signal * formant_envelope
    
    # Normalize and binarize for standard HDC compatibility
    # But KEEP the pre-binarization magnitudes for weighted similarity
    pre_bin = shaped / (np.std(shaped) + 1e-10)
    binary = np.sign(pre_bin).astype(np.int8)
    
    return binary, pre_bin
```

### What This Gives You

Each base vector now has three layers of structure:

1. **Formant identity**: Energy concentrated in a specific dimensional band, enabling spectral filtering for source separation.

2. **Harmonic texture**: Within the formant band, the Chebyshev polynomial structure creates smooth gradients between adjacent dimensions. Neighboring dimensions are correlated, enabling local error correction.

3. **Stochastic individuality**: The random coefficients ensure each prime's base vector is unique, maintaining the codebook diversity needed for the CRT aliasing horizon.

When 8 such instruments superimpose:
- The fortissimo/pianissimo pattern is no longer random — it has spatial structure aligned with the formant bands.
- Spectral filtering (looking at dimensions 0–1249) isolates Cycle 1's contribution.
- Weighted similarity using pre-binarization magnitudes gives confidence-weighted matching.
- Errors in a specific cycle manifest as spectral anomalies in that cycle's formant band, enabling cycle-specific fault diagnosis.

## Part VII: What We Don't Know Yet — The Open Questions

### 1. Codebook Size vs. Spectral Partitioning
Random HDC gets exponential codebook size because random vectors in high dimensions are quasi-orthogonal with overwhelming probability. Spectral partitioning reduces each cycle's effective dimensionality to ~1,250. Does concentration-of-measure still give adequate codebook size within each band? This is the CDMA capacity question: how many spreading codes fit in a sub-band before interference degrades performance? CDMA theory gives precise answers (Erlang capacity formulas) that should translate.

### 2. Binding Under Spectral Structure
UTLP's binding operation is cyclic rotation. With random base vectors, rotation shuffles all dimensions uniformly. With spectrally structured vectors, rotation shifts energy within the formant band — which is fine for small rotations but wraps around at the band edges. Does this create artifacts? The Chebyshev product identity (Tm · Tn = ½[Tm+n + T|m-n|]) controls how binding affects spectral content, but the interaction with formant envelope shaping needs characterization.

### 3. Optimal Q for Different Applications
The formant width (Q factor) is a design parameter with no obvious universal optimum. Narrow formants (high Q) favor source separation; wide formants (low Q) favor smooth similarity decay. The right Q depends on what matters more: partition detection speed or synchronization gradient quality. This is an empirical question that needs benchmarking against the existing random-vector baseline.

### 4. The "Orchestration" Question
Given 8 coprime cycles, what's the optimal assignment of spectral bands? The binary tree above is one option. But maybe cycles with larger primes (more phase values, finer temporal resolution) should get wider bands (more dimensions), and shorter cycles should get narrower bands. Or maybe the assignment should follow the harmonic series (cycle 1 gets the fundamental band, cycle 2 gets the second harmonic, etc.). This is the orchestration problem — choosing which instruments play which parts.

### 5. Does Timbral Structure Enable New Operations?
This is the most exciting unknown. Random HDC supports bundling, binding, and permutation. Spectrally structured HDC might support additional operations:
- **Spectral filtering**: Extract one cycle's contribution from a bundled vector without knowing the full chord.
- **Timbral distance**: Compare the spectral shapes of two vectors, not just their element-wise similarity.
- **Harmonic analysis**: Decompose a bundled vector into its constituent instruments using DCT/FFT of the dimensional magnitude pattern.
- **Orchestral mixing**: Combine vectors from different "ensembles" (swarms with different base vector timbres) by spectral interleaving.

None of these exist in the random HDC literature because random vectors have no spectral structure to operate on. But they're standard operations in audio signal processing, and the mathematical translation should be straightforward.

## Part VIII: Where This Sits in the Literature

### What exists
- **Source-filter model** (Fant 1960): The decomposition of acoustic instruments into excitation and resonance. Well-established physics and signal processing. Direct mathematical parallel to HDC's base-vector + rotation architecture.
- **Auditory scene analysis** (Bregman 1990): How the brain separates simultaneous sources using spectral, temporal, and spatial cues. The perceptual counterpart of spectral filtering in signal processing.
- **Sethares' consonance-spectrum theory** (1993): The proof that consonance/dissonance depends on timbre, not just intervals. Provides the mathematical framework for matching similarity kernels to the coprime cycle structure.
- **CDMA spreading codes** (qualcomm, 1990s): The telecommunications implementation of orthogonal multiplexing in a shared bandwidth. Provides capacity formulas, interference models, and the Walsh-Hadamard tree structure.
- **VFA** (Frady et al. 2021): The theorem that frequency selection in HDC base vectors determines the similarity kernel. The mathematical license to do everything proposed here.
- **RHC** (Kymn et al. 2024): Coprime residue encoding in HDC with structured deterministic base vectors. The closest prior art — does coprime cycles in HDC, but not with spectral partitioning or instrument-like timbral design.
- **SORF-DCT** (Zhang & Zhou 2024): DCT-based structured random features for kernel approximation. The construction method — DCT + random sign flips — is directly usable for Chebyshev-harmonic base vectors.

### What doesn't exist
Nobody has:
1. Framed HDC base vector design as an **instrument design** problem with source-filter decomposition
2. Used **spectral partitioning** (FDMA-style formant bands) within HDC vector spaces
3. Connected **Sethares' timbre-scale relationship** to VFA's frequency-kernel theorem
4. Applied **auditory scene analysis** principles (spectral segregation, harmonic grouping) to HDC vector decomposition
5. Used the **Q factor** of dimensional formants as a design parameter controlling the precision/capacity tradeoff

The framework proposed here sits at the intersection of:
- Musical acoustics (timbre, formants, orchestration)
- Telecommunications (CDMA, Walsh-Hadamard, MC-OFDM)
- Hyperdimensional computing (VSA, VFA, resonator networks)
- Signal processing (source-filter models, spectral analysis)

These fields share mathematical foundations (Fourier analysis, orthogonal decompositions, correlation-based detection) but have never been unified under the instrument design metaphor for the specific purpose of constructing HDC base vectors with exploitable spectral structure.

## Conclusion: Why Instruments, Not Just Better Vectors

The practical advantage of spectrally structured base vectors — better source separation, weighted confidence, cycle-specific error diagnosis — could probably be achieved by various engineering approaches. What the instrument metaphor adds is a **design language**.

Engineers have spent centuries optimizing instrument design through an iterative dialogue between physical construction and perceptual evaluation. The resulting vocabulary — timbre, formant, resonance, Q factor, orchestration, consonance, masking, dynamic range — is rich, precise, and intuitive. It maps onto HDC design parameters in a way that's more natural than the mathematical abstractions alone.

When you say "this cycle should be a bassoon" you're specifying a low-frequency formant band, moderate Q, warm harmonic content. When you say "that cycle should be a piccolo" you're specifying a high-frequency band, narrow formant, piercing overtones. These are concise design specifications that encode a huge amount of acoustical engineering knowledge.

The deeper reason is that musical instruments are the most successful engineered resonators in human history. Stradivari didn't know about formant theory, but he optimized the spectral envelope of his violins through centuries of accumulated craft. The acoustic principles encoded in instrument design — how to shape resonances for maximum expressiveness within physical constraints — are the same principles needed for designing HDC base vectors that are maximally informative within computational constraints.

The journey from random noise to musical instruments might be the journey from brute-force HDC to something genuinely new.
