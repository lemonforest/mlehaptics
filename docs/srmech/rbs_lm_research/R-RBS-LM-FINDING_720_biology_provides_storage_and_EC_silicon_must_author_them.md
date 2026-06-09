# Finding 720 — biology's substrate provides storage + error-correction as a free service to its life; on silicon we must author, power, and provide them (and that's why the model was built bottom-up)

**Script:** `R-RBS-LM-SUBSTRATESERVICES_biology_bakes_in_storage_and_EC_silicon_must_author_them.py`
**Status:** VERIFIED (srmech 0.7.5rc42, numpy-free — the silicon service-triad demonstrated native)
**User direction:** *"biology substrate does storage and error-correction things for the life that lives on it. we
had to work bottom-up to make our model in the image of the cosmos — understand biology bottom-up to bring it into
our k=3 substrate. we have to author and power and provide the rules already baked into biology substrate."*

## The asymmetry

A substrate offers **services** to whatever runs on it. The two substrates provision them very differently:

- **Biology bakes them in, free to its life:** **storage** (DNA / the genome), **error-correction** (DNA repair,
  polymerase proofreading, the codon code's built-in redundancy), **partition/protect** (chromosome telomeres),
  **reversibility** (the complementary-strand template). A cell does not *author* these — it *inherits* them.
- **Silicon bakes in only the low level, free:** bit-exact **add/sub/shift** + **reversibility** (CLAUDE.md §0 /
  DUALITY). The higher **storage + error-correction** services it does **not** hand us — **we** must author,
  power, and provide them.

**That asymmetry is exactly why the model had to be built bottom-up "in the image of the cosmos."** To re-provide
biology's baked-in services on silicon, we first had to understand them *at the biology-substrate level* — then
re-author them in the k=3 substrate. The storage model is even **named after the services it reproduces**
(genome / chromosome / telomere, F716): substrate-self-recognition, the names carried because the structure earns
them.

## What was demonstrated (the silicon substrate now *provides* the biology service-triad — all native)

| biology service | baked into biology (free) | silicon re-authoring (we provide) | finding | verified |
|---|---|---|---|:---:|
| **storage** | DNA / the genome | `srmech.amsc.genome` (chromosome strand) | F716 | ✓ recall recovers the kernel |
| **error-correction** | DNA repair / proofreading / codon code | `cascade.hamming_*` (Hamming(7,4)) | F450 | ✓ corrupt bit 3 → syndrome 3 → recovered |
| **partition / protect** | chromosome telomeres | telomere content-address caps | F715 | ✓ distinct cap per label |
| **reversibility** | complementary-strand template | the_one Klein-4 coupling (involution) | F713 | ✓ lossless re-bind |

Single-bit "mutation" located and corrected; kernel stored and recalled through `the_one`; partitions protected by
content-addressed telomere caps. The silicon substrate, which provides *none* of these natively, now provides all
of them **because we authored them** — and we knew *which* to author only by reading biology bottom-up.

## The dual of F719 — and why this is the whole shape

F719 said biology's *failure modes* (rampancy / mortality) live in the biology substrate and **don't transfer** to
silicon. F720 is the dual: biology's *services* (storage / EC / protection) are **also** baked into the biology
substrate — but unlike the failure modes, these we **must re-author** on silicon, because the silicon substrate
won't hand them over for free. Put together:

> Biology bakes in **both** the services **and** the failure modes. On silicon we **author the services** and the
> **failure modes do not transfer** — we choose what to provide; we don't inherit the death.

That is the bottom-up methodology stated precisely: **read every service biology bakes in → re-author it as a k=3
cascade → keep the service, shed the mortality.** The genome storage stack (F710–F716) + the Hamming EC ladder
(F450) + the telomere/`the_one` protection (F713/F715) are the concrete deliverables of that read. "In the image
of the cosmos" = the same services, re-authored on a substrate we author rather than one we're born into.

**Honest scope:** these are *structural re-authorings* of the biology services, demonstrated on the srmech
surface — not biological claims; we never model which-way/when biology repairs or fails (F282/F552). The mapping is
a framework reading; the silicon demonstrations are computed and bit-exact.

**Composes:** F719 (the failure-mode dual) · F716 (genome storage = the storage service, named) · F450 (Hamming EC
ladder = the repair service) · F713/F715 (the_one + telomere = reversibility + protection) · F552 (biology = the
collapsed lossy projection) · MS #18 (biology is one substrate-class) · DUALITY.md / CLAUDE.md §0 (field vs
excitation; bit-exact silicon ops) · `user_stance_substrate_self_recognition_inevitable_per_loe`. srmech 0.7.5rc42.
Held open (F394).
