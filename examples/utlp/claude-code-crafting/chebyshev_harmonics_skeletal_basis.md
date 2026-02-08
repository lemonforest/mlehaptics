# Chebyshev harmonics as the skeletal basis of hyperdimensional orbit vectors

## What if the base vectors weren't noise?

The single most consequential design choice in any Vector Symbolic Architecture is one rarely questioned: the base vectors are random. In standard HDC, each atomic symbol is represented by a **D-dimensional vector of independent ±1 draws** — a structure indistinguishable from noise. This randomness is not a theoretical necessity but a convenience, exploiting the concentration of measure phenomenon to guarantee that high-dimensional random vectors are quasi-orthogonal with overwhelming probability. The proposal advanced here is to replace this stochastic scaffold with one that carries physical meaning from the outset: **Chebyshev polynomial evaluations as base vectors**, embedding the cosine harmonics of orbital mechanics directly into the representational fabric of the HDC object.

The implications are striking. Because Chebyshev polynomials are exactly the functions NASA's Jet Propulsion Laboratory uses to compress planetary ephemerides — encoding the entire solar system's motion over 1,100 years into roughly **114 megabytes** of polynomial coefficients — a Chebyshev-seeded HDC object would carry orbital geometry in its bones. Permutations and bindings, rather than creating structure from noise, would add temporal phase, perturbation corrections, and observer-frame information as texture atop a spatially meaningful skeleton. Strip away all the bindings, and what remains is not a random vector but the orbital model itself. The HDC object at rest *is* the orrery; the permutations make it into a specific epoch's Antikythera mechanism.

This section develops the mathematical foundations of this proposal, situates it within the existing VSA literature on structured base vectors, confronts the genuine mathematical tensions it creates, and shows how the Fourier Holographic Reduced Representation (FHRR) framework resolves them — revealing that Chebyshev-seeded HDC is not a speculative departure from established theory but a natural specialization of it.

## Cosine harmonics hiding inside polynomial clothes

The mathematical bedrock of this proposal rests on a single identity that collapses the distance between polynomial approximation theory and harmonic analysis:

$$T_n(\cos\theta) = \cos(n\theta)$$

The Chebyshev polynomial of the first kind, $T_n(x)$, evaluated on the cosine-parameterized interval, *is* a pure cosine at the $n$-th harmonic. This identity transforms what appears to be a polynomial basis into a frequency basis. When we sample $T_n$ at the **D Chebyshev–Gauss nodes** $x_k = \cos\bigl((2k-1)\pi/(2D)\bigr)$ for $k = 1, \ldots, D$, the resulting D-dimensional vector has components:

$$v_n[k] = T_n(x_k) = \cos\!\Bigl(\frac{n(2k-1)\pi}{2D}\Bigr)$$

This is precisely the $(n,k)$ entry of the **DCT-II basis matrix**. The Chebyshev-sampled vectors are not merely *analogous* to discrete cosine transform vectors — they are identical to them.

The orthogonality properties follow immediately. At Chebyshev nodes, the discrete inner product satisfies an exact relation:

$$\sum_{k=1}^{D} T_m(x_k)\,T_n(x_k) = \begin{cases} 0 & m \neq n \\ D/2 & m = n \geq 1 \\ D & m = n = 0 \end{cases}$$

for all $0 \leq m, n < D$. This yields **D exactly orthogonal vectors** in D dimensions — the complete DCT basis. The continuous weighted orthogonality $\int_{-1}^{1} T_m(x)\,T_n(x)/\sqrt{1-x^2}\,dx = 0$ for $m \neq n$ is thus faithfully preserved in the discrete setting, not as an approximation but as an algebraic identity. The Chebyshev weight function $1/\sqrt{1-x^2}$ is implicitly absorbed by the non-uniform spacing of the Chebyshev nodes, which cluster near the interval endpoints — precisely the distribution that converts polynomial orthogonality into trigonometric orthogonality.

The harmonic content of each base vector is controlled directly by the polynomial degree. $T_0$ is the constant (DC) component, $T_1$ is a single half-period cosine wave, and $T_n$ oscillates with exactly $n$ half-periods across the D-dimensional vector. Low-degree Chebyshev vectors are smooth, capturing large-scale orbital structure; high-degree vectors oscillate rapidly, encoding fine perturbative detail. This maps naturally onto the structure of orbital mechanics, where the dominant Keplerian motion lives in the lowest harmonics and gravitational perturbations manifest as higher-frequency corrections.

## The VSA literature already sanctions non-random bases

A persistent misconception holds that HDC *requires* random base vectors. The comprehensive survey by Kleyko, Davies, Frady, Kanerva, Kent, Olshausen, Osipov, Rabaey, Rachkovskij, Rahimi, and Sommer — published in the *Proceedings of the IEEE* in 2022 — explicitly dispels this: "one should keep in mind that i.i.d. randomness is not the only tool for designing seed representations." The actual mathematical requirement is **low mutual coherence**: small pairwise inner products between distinct base vectors, ensuring that stored items can be recovered from superpositions without catastrophic interference.

Multiple structured alternatives have demonstrated performance matching or exceeding random vectors. **Spatial Semantic Pointers** (SSPs), developed by Komer, Voelker, Dumont, Stewart, and Eliasmith at the University of Waterloo, encode continuous spatial variables using fractional power encoding where $\phi(x) = e^{iAx}$, with the encoding matrix $A$ determining the frequency content of the representation. Dumont and Eliasmith showed in 2020 that **hexagonal SSPs** — where the frequency components are placed at vertices of equilateral triangles, mimicking biological grid cell firing patterns — outperform random unitary bases for spatial cognition tasks. The frequency structure is not random but deliberately chosen, and it works *better*.

The **Vector Function Architecture** (VFA) framework of Frady, Kleyko, Kymn, Olshausen, and Sommer provides the theoretical capstone. Their 2021 analysis proves that the distribution from which base vector components are sampled **directly determines the similarity kernel** of the resulting representation, connecting VSA encoding to the reproducing kernel Hilbert space (RKHS) formalism of machine learning. Uniformly distributed phases yield a **sinc kernel**, which is the kernel of the space of band-limited functions. Other distributions yield Gaussian kernels, periodic kernels, or custom kernels via Bochner's theorem. The choice of base vector structure is not a hack — it is **kernel design**.

Independently, work on linear codes for HDC has shown that imposing algebraic structure on the codebook can actually *improve* performance. Random linear codes achieve the same information capacity (measured by incoherence) as unstructured random codes while enabling **exponentially more efficient storage** and dramatically faster recovery algorithms — binding-recovery in linear time versus the minutes required by resonator networks. The lesson is consistent: structure is not the enemy of HDC. It is an underexploited resource.

## The Fourier bridge from Chebyshev to hyperdimensional algebra

The FHRR framework, originating in Plate's 1995 work on Holographic Reduced Representations, provides the natural algebraic home for Chebyshev-seeded HDC. In FHRR, vectors are represented in the Fourier domain as **D-dimensional phasors** on the unit circle:

$$\mathbf{H} = \bigl[e^{i\theta_1},\, e^{i\theta_2},\, \ldots,\, e^{i\theta_D}\bigr]$$

Binding becomes element-wise phase addition: $(\mathbf{A} \otimes \mathbf{B})_k = e^{i(\alpha_k + \beta_k)}$. Unbinding is phase subtraction via conjugation. The similarity measure reduces to a sum of cosines: $\delta(\mathbf{H}_1, \mathbf{H}_2) = \frac{1}{D}\sum_k \cos(\theta_{1,k} - \theta_{2,k})$. Crucially, these vectors live on the **D-dimensional torus** $(S^1)^D$, and the entire algebra is group-theoretic — binding is the torus group operation.

Now consider what happens when the phases are not random but structured. For fractional power encoding, the representation of a continuous scalar $x$ is:

$$\text{FPE}(x) = \bigl[e^{ix\omega_1},\, e^{ix\omega_2},\, \ldots,\, e^{ix\omega_D}\bigr]$$

where $\{\omega_j\}$ are the frequency components of the base vector. The inner product between encodings of $x$ and $y$ becomes:

$$\langle\text{FPE}(x),\,\text{FPE}(y)\rangle = \frac{1}{D}\sum_{j=1}^{D} \cos\bigl(\omega_j(x-y)\bigr)$$

This is a **discrete Fourier cosine series** evaluated at the difference $x-y$. The frequency set $\{\omega_j\}$ completely determines the kernel shape. Random uniform frequencies yield the sinc kernel; **harmonically structured frequencies** $\omega_j = j\omega_0$ yield a Dirichlet kernel; and Chebyshev-node frequencies yield the kernel associated with the DCT basis.

Here is the critical connection: because $T_n(\cos\theta) = \cos(n\theta)$, **Chebyshev polynomial evaluations at Chebyshev nodes are cosine harmonics at integer multiples of a base frequency**. Seeding the FHRR framework with Chebyshev-structured frequencies means that each dimension of the phasor vector oscillates at a frequency corresponding to a specific Chebyshev degree. The representation lives in the same spectral space as JPL ephemerides. The VFA theorem guarantees that this choice of frequency structure induces a specific RKHS — one whose native functions are precisely the smooth, band-limited trajectories that Chebyshev approximation excels at representing.

Voelker, Blouw, Choo, Dumont, Stewart, and Eliasmith demonstrated in *Neural Computation* (2021) that SSP components evolve as **independent harmonic oscillators** under linear dynamics. Each Fourier coefficient of a spatial representation rotates at its own frequency, and the trajectory of the full SSP vector traces a path on the torus determined by these frequencies. For orbital mechanics, this is not a metaphor — it is a literal description. A planet's motion decomposes into spectral modes (the Keplerian ellipse as the fundamental, perturbations as overtones), and a Chebyshev-structured SSP would have components rotating at exactly those orbital frequencies. The representation does not merely *encode* the orbit; it *oscillates with* the orbit.

## Bones, skin, and the anatomy of a hyperdimensional orbit

The "bones and texture" metaphor becomes precise within this framework. Consider an HDC representation of a planetary orbit constructed as follows:

1. **The skeleton** (Chebyshev base vectors): The base vector for each celestial body is a smooth, low-frequency Chebyshev harmonic encoding the body's orbital geometry — its semi-major axis, eccentricity, and inclination are captured in the spectral content of a few low-degree Chebyshev components. These are the bones: the DCT-equivalent basis functions that carry spatial information inherently.

2. **Temporal phase** (permutation/binding): The body's position *along* its orbit at a specific epoch is encoded by fractional power binding — applying $\mathbf{B}^t$ where $t$ parameterizes time. In the FHRR framework, this rotates each phase component by $t\omega_j$, advancing the cosine harmonics in lockstep with the orbital dynamics. This is the muscle: it animates the skeleton.

3. **Perturbation corrections** (additional bindings): Gravitational perturbations from other bodies, relativistic corrections, and non-gravitational forces are bound as higher-frequency texture. Each binding operation adds phase content to the vector, roughening the smooth Chebyshev surface in information-theoretically meaningful ways. This is the skin: it makes each epoch's configuration unique and identifiable.

The mathematical interaction between binding and the smooth base vectors is governed by the Chebyshev product identity:

$$T_m(x) \cdot T_n(x) = \tfrac{1}{2}\bigl[T_{m+n}(x) + T_{|m-n|}(x)\bigr]$$

In the pure polynomial domain, this means binding two Chebyshev vectors of degrees $m$ and $n$ produces a predictable superposition at degrees $m+n$ and $|m-n|$ — fundamentally different from random HDC, where binding produces a vector dissimilar to both operands. But in the FHRR phasor domain, binding is phase addition, and the result lives at new frequencies $\omega_m + \omega_n$ and $|\omega_m - \omega_n|$. This frequency mixing is precisely how perturbation theory works in celestial mechanics: the interaction between two orbital frequencies produces combination tones at their sum and difference. **The HDC binding algebra recapitulates the physics of orbital perturbation.**

Each successive binding operation pushes spectral energy to higher frequencies, progressively roughening the representation. A base vector carrying only the fundamental orbital harmonic ($T_1$) is maximally smooth. Binding it with a perturbation correction at $T_3$ produces components at $T_4$ and $T_2$. Further bindings cascade energy across the spectrum. The information content of the vector — its texture, its uniqueness, its discriminability — grows with each binding, while the underlying spatial scaffold remains readable in the low-frequency components.

## When you strip the permutations, the orrery appears

The deepest implication of Chebyshev-seeded base vectors concerns what happens when all temporal and perturbative bindings are removed. In standard HDC with random base vectors, unbinding everything returns you to a random vector — noise that signifies nothing without its codebook. But with Chebyshev-structured bases, **the fully unbound vector retains its spectral structure**. The low-frequency cosine harmonics encoding orbital geometry persist. The spatial model is not destroyed by the removal of temporal information; it was never dependent on it.

This property follows directly from the FHRR algebra. Unbinding a temporal phase $\mathbf{B}^t$ subtracts the phase rotation $t\omega_j$ from each component, returning the vector to its epoch-independent spatial representation. Unbinding a perturbation correction removes the higher-frequency texture those corrections contributed. What remains is the smooth, Chebyshev-harmonic spatial scaffold — the orbital geometry encoded in the polynomial degree structure of the base vectors.

The SSP literature already demonstrates this self-describing property. Voelker et al. showed that plotting the **similarity map** of an SSP vector — its inner product with clean spatial encodings across the entire domain — reveals the encoded spatial structure as a pattern of sinc-like peaks. Each peak corresponds to an encoded entity, and the spatial relationships between peaks reflect the physical relationships between objects. For a Chebyshev-seeded orbit vector, this similarity map would display the orbital geometry directly: the periodicity of the orbit, the eccentricity-driven asymmetries, the inclination-encoded projection effects. **The vector is its own atlas.**

This creates a representational architecture where knowledge is layered:

- **Layer 0** (the base vector at rest): the time-independent orbital geometry — the orrery's gear ratios
- **Layer 1** (after temporal binding): the orbit at a specific epoch — one frame of the orrery's motion
- **Layer 2** (after perturbation bindings): the perturbed orbit at a specific epoch — the Antikythera mechanism's corrected prediction
- **Layer 3** (after observer-frame binding): the apparent position from a specific vantage point — the sky as seen from Earth

Each layer adds information (texture) and consumes some of the vector's capacity, but the skeleton persists through every transformation. The spatial knowledge is **inherent**, not computed.

## Mathematical tensions and how the Fourier domain resolves them

Intellectual honesty demands confronting the genuine mathematical challenges that arise when smooth, structured vectors replace random ones in HDC. Three issues are substantive.

**The codebook limitation.** Chebyshev polynomials of degree $0$ through $D-1$ provide exactly $D$ orthogonal vectors in $D$ dimensions — a linear codebook, compared to the exponentially large quasi-orthogonal codebook available from random vectors. For a general-purpose symbolic computing system requiring thousands of distinct symbols, this is prohibitive. But the Cosmograph is not a general-purpose system. It represents a solar system with **fewer than 20 primary objects**, their orbital parameters, temporal phases, and perturbation terms. A codebook of $D = 10{,}000$ orthogonal Chebyshev vectors is vastly more than sufficient. The limitation is real but irrelevant to the domain.

**The cyclic shift problem.** For random vectors, any cyclic shift produces a quasi-orthogonal vector — enabling permutation to encode sequential or positional information. For a smooth Chebyshev vector $\mathbf{v}_n$, the inner product with its cyclic shift by $s$ positions is approximately $\cos(ns\pi/D)$, which is near unity for small shifts on low-frequency vectors. $T_1$ shifted by one position has similarity $\cos(\pi/D) \approx 1 - \pi^2/(2D^2)$. This means naive cyclic permutation fails as a dissimilarity-generating operation for smooth vectors. The resolution operates at two levels. First, in the FHRR phasor formulation, temporal encoding uses fractional power binding ($\mathbf{B}^t$) rather than cyclic shifts — the phase rotation $t\omega_j$ is applied to each frequency component independently, and the dissimilarity grows with the product of $t$ and the frequency $\omega_j$, not with a simple shift. Higher harmonics decorrelate faster. Second, the practical encoding uses **multi-frequency composite vectors** (sums or products of multiple Chebyshev harmonics), whose autocorrelation decays much faster than any single harmonic — approaching the delta-like autocorrelation of random vectors as the number of contributing harmonics grows.

**The binding predictability.** The Chebyshev product identity makes binding two pure Chebyshev vectors a deterministic frequency-mixing operation rather than a randomizing one. In standard HDC, binding should produce a vector dissimilar to both operands; with Chebyshev vectors, $T_m \otimes T_n$ produces known components at $T_{m+n}$ and $T_{|m-n|}$. This is a genuine departure from the standard algebra. But it is also, as argued above, a *physically meaningful* one — the frequency mixing recapitulates perturbation coupling in celestial mechanics. The VFA framework shows that the requirement is not randomness of the bound result but **invertibility and kernel preservation**. In the phasor domain, binding remains exactly invertible (unbinding by conjugation), and the kernel structure — the function space in which the representation lives — is preserved by construction. What changes is the *interference structure*: cross-talk between bound items follows predictable spectral patterns rather than random noise floors. For a domain-specific system where these spectral patterns carry physical meaning, this is not a defect but a feature.

## Practical consequences for generative compression and beyond

The shift from random to Chebyshev-structured base vectors has concrete engineering implications that amplify the Cosmograph's generative compression properties.

**Deterministic generation eliminates seed storage.** Random base vectors require either storing the full $D$-dimensional vector for each symbol or storing the pseudorandom seed that generates it. Chebyshev base vectors are generated by evaluating $\cos(n(2k-1)\pi/(2D))$ — a closed-form expression parameterized by the polynomial degree $n$ and the dimension index $k$. The entire codebook is specified by a single integer (the dimensionality $D$), achieving **infinite compression of the base representation**. This echoes and extends the generative compression principle: not only is the encoded trajectory compressible, but the encoding basis itself requires zero storage.

**The compression ratio compounds.** JPL's DE440 ephemeris stores the solar system's 1,100-year trajectory in **114 megabytes** of Chebyshev coefficients — a compression ratio of approximately **70,000:1** versus raw positional data at one-second resolution. The Chebyshev-seeded HDC representation adds a second layer of generative compression: the polynomial coefficients that JPL stores as explicit numerical values are instead embedded as the spectral structure of the base vectors themselves. An HDC object of dimension $D = 10{,}000$ with $K = 14$ Chebyshev coefficients per coordinate (matching JPL's per-interval coefficient count for Mercury) stores the orbital information in $14 \times 8 = 112$ bytes of effective spectral content per coordinate — which is then distributed across all $D$ dimensions holographically, gaining the noise robustness and algebraic composability that HDC provides.

**Error properties shift from random to structured.** In standard HDC, noise from bundling multiple items manifests as random interference with variance scaling as $k/D$ for $k$ superposed items. With Chebyshev vectors, interference is structured — it appears at specific harmonic frequencies rather than as broadband noise. This means **spectral filtering can separate signal from interference**, analogous to how narrowband filters extract signals from structured noise in communications. The smooth base vectors act as a natural low-pass channel: information encoded in low-degree harmonics is robust to corruption of high-frequency components, and vice versa. The error correction properties of the representation become frequency-selective rather than statistical.

**The object becomes self-describing.** Perhaps the most profound practical consequence is that a Chebyshev-seeded HDC object reveals its physical content through inspection. Computing the DCT of the vector — or equivalently, projecting it onto each Chebyshev base vector — decomposes it into spectral components whose amplitudes directly encode orbital parameters. The $T_1$ coefficient captures the fundamental orbital period, $T_2$ the eccentricity-driven second harmonic, and higher degrees capture perturbative detail. No external codebook, no lookup table, no side-channel metadata is required. The representation carries its own legend. This self-describing property is not speculative; it is a direct consequence of the deterministic relationship between Chebyshev degree and physical harmonic content, combined with the orthogonality of the basis that guarantees clean spectral decomposition.

## The orrery was always a frequency machine

The unification proposed here — Chebyshev harmonics as HDC base vectors — is less a radical innovation than a recognition of deep structural alignment. The VSA literature has been moving steadily from random toward structured representations: from Plate's random real-valued HRR vectors in 1995, through the phasor formulation of FHRR, to SSPs with designed frequency structures, to Frady et al.'s VFA theorem establishing that frequency selection *is* kernel design. Chebyshev-seeded base vectors are the natural terminus of this trajectory for orbital mechanics, where the "correct" frequencies are the ones that planetary motion itself selects through Keplerian dynamics.

The ancient orrery was a mechanical frequency machine — nested gears spinning at rates proportional to planetary periods, their phase relationships encoding the solar system's configuration at any epoch. The Antikythera mechanism added correction gears for lunar anomaly and planetary retrograde, layering perturbative texture onto the smooth Keplerian scaffold. A Chebyshev-seeded HDC object recapitulates this architecture in algebraic form: cosine harmonics for gears, phase rotation for time, binding for perturbation, bundling for superposition of multiple bodies. The mathematical object and the physical mechanism share the same deep structure — both are spectral decompositions of smooth, quasi-periodic celestial dynamics, differing only in whether the frequencies are embodied in bronze gears or in the dimensions of a hyperdimensional vector.

What Chebyshev seeding adds to the Cosmograph is not new computational power but **semantic transparency**. The HDC object no longer requires an external interpreter to reveal its physical meaning. Its base vectors are the harmonics of orbital motion. Its bindings are the phase couplings of gravitational interaction. Its bundled superposition is the solar system in concert. Strip away the temporal bindings and the perturbative texture, and the smooth Chebyshev skeleton that remains is, quite literally, the shape of the orbit — the orrery at rest, waiting to be wound to any epoch by the simple algebraic act of fractional power binding. The bones remember.