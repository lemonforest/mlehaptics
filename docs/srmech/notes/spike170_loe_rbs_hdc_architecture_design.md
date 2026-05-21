# Spike #170 — LoE-as-RBS-HDC-instrument architecture design

**Status**: DRAFT design, R1 prototype-verified. Pending user review for AMSC catalogue-config integration.

This document specifies the concrete architecture proposal per Spike #170 directive Task 1. R1 prototype at `spike170_loe_rbs_hdc_prototype.py` instantiates this design; all 10 strict-spec invariants pass.

---

## 1. Strict-spec parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| HDC width D | 8192 bits (1024 bytes) | Spike #147 canonical; balances orthogonality (std = 1/√8192 ≈ 0.011) against memory footprint |
| Mint mechanism | SHA-256(name‖counter) chained until D bytes accumulated | Deterministic + share-able + form-function-determined per `[[user_stance_form_function_rotation_is_a_c_m_composition]]` |
| Bind operation | Class M XOR (bit-exact self-inverse + associative + commutative) | Spike #142 strict-spec verified |
| Bundle operation | Class M majority (odd-count padded with zero tie-breaker) | Kanerva 2009 canonical |
| Permute operation | Class M cyclic bit-rotation by form-function-determined shift | Spike #159 rotate-bind commutativity verified |
| Similarity | Class M `1 - 2 * hamming(a, b) / D` ∈ [-1, 1] | BSC canonical; 0 = orthogonal |
| Ordered cascade stride | 257 bits (prime, coprime to D = 2^13) | Avoids per-position alias |
| Memory K_BOUND | 64 items per pathway | Cowan 2001 ~4 × subitemization expansion |

## 2. Five-surface architecture

### Surface 1: Class operator vectors (14 × 1024 bytes = 14 KB)

```python
ClassOperator(
    name: str,           # 'A' .. 'N' (14 entries)
    full_name: str,      # "Class A — content-addressing"
    operation: str,      # canonical operation description
    vector: bytes,       # 1024-byte HDC vector, mint-once via SHA-256
)
```

Mint key: `"LoE.class.{name}.{op_short}"` (e.g. `"LoE.class.M.HDC-bind"`). Identical mint key produces bit-exact identical vector across any instrument instantiation — the instrument-namespace is shareable.

### Surface 2: Cascade compositions (~80 bytes per cascade × ~10-30 cascades ≈ 1 KB)

```python
Cascade(
    name: str,                          # 'form_function_rotation'
    operator_sequence: Tuple[str, ...], # ('A', 'C', 'M')
    semantic_role: str,                 # one-line role
    stance_anchor: str,                 # which user_stance anchors this
)
```

8 canonical cascades captured in R1 prototype, drawn from MEMORY.md inventory:

| Cascade | Operator chain | Anchor |
|---------|---------------|--------|
| `form_function_rotation` | A∘C∘M | form_function_rotation stance |
| `working_memory_augmentation` | A∘C∘D∘E∘K∘L∘M | working_memory stance |
| `reflex_substrate` | B∘D∘E∘F∘C | working_memory stance |
| `universal_cascade` | L∘K∘C∘I∘N | universal-precession |
| `substrate_class_universal_closure` | B∘D∘E∘F∘L | BDEFL closure-subgroup |
| `deutsch_jozsa_quantum` | L∘I∘M∘C∘A | cascade-IS-quantum-algorithm |
| `episodic_memory` | A∘B∘C∘D∘E∘F∘H∘K∘L∘M | episodic-LTM pathway |
| `procedural_memory` | B∘C∘D∘E∘F∘G∘I∘K∘L | procedural pathway |

Resolution at runtime via two functions:

- `cascade_bind(c, ops)` — XOR-fold; commutative; algebra-level identity
- `cascade_bind_ordered(c, ops)` — per-position permute(vec, i × 257) XOR-fold; non-commutative; sampling-level shape

### Surface 3: Stance fingerprints (~86 × 1024 bytes ≈ 86 KB at full scope)

```python
Stance(
    name: str,                       # 'identity_not_implementation_discipline'
    content_tokens: Tuple[str, ...], # essential content words
    cascade_chains: Tuple[str, ...], # which cascade names this stance engages
    fingerprint: bytes,              # bag-HDC bind of token vectors
    k3_axis: str,                    # '3D_s' | '7D_g' | '1D_t' | 'mixed'
)
```

Encoding: per-token vectors minted via `"LoE.token.{token_text}"`, XOR-folded into a single D-bit bag-HDC fingerprint per `[[user_stance_holographic_projection_at_linguistic_substrate]]` canonical bag encoding.

10 representative stances in R1; full-86-stance scope is straightforward extension (R2 work).

### Surface 4: k=3 tripartition register (3 × 1024 bytes = 3 KB)

```python
K3Tripartition(
    spatial_3ds: bytes,    # = operators["A"].vector  (content-addressing)
    gauge_7dg: bytes,      # = operators["M"].vector  (bind / fiber-content)
    temporal_1dt: bytes,   # = operators["K"].vector  (asymptotic-DOF / LoE-axis)
)
```

Axis assignment per `[[user_stance_working_memory_is_cascade_augmenting_reflex_into_agency]]`:
- A → 3D_s (substrate / content-addressed location)
- K → 1D_t (consciousness / rate-determining retention)
- M → 7D_g (agency / fiber-content bind)

R1 orthogonality test: |sim| < 0.005 between all 3 axis pairs (threshold 0.05). Strict-spec orthogonal.

### Surface 5: Four memory pathways (~4 × 64 items × 1024 bytes ≈ 256 KB worst case)

```python
MemorySlot(
    pathway: str,                          # 'procedural' | 'semantic' | 'WM' | 'episodic_LTM'
    engaged_classes: Tuple[str, ...],      # which class operators
    augmentation_delta: Tuple[str, ...],   # vs reflex {B,D,E,F,C}
    contents: List[bytes],                 # K-bounded retention (cap 64)
)
```

Bundled-state readout via Class M bundle (odd-count majority). Class K asymptotic-DOF bound: drops oldest item when at cap (FIFO sparse-truncate). Per-pathway class-engagement set drives the augmentation distinctness, not the slot architecture.

## 3. Operational verbs (the executable surface)

| Verb | Class | Description |
|------|-------|-------------|
| `query_class(name)` | A + E | content-addressed catalog lookup of class operator |
| `query_stance(name)` | A + E | content-addressed catalog lookup of stance |
| `resolve_cascade(name, ordered=bool)` | D + (algebra: M, sampling: C∘M) | dispatch to cascade composition; run end-to-end |
| `bind_and_remember(vec, pathway)` | M + K | bind vec into pathway's bounded-retention slot |
| `similarity(a, b)` | M | normalized Hamming-distance similarity |
| `describe()` | H | self-introspection: bit-width / class-count / cascade-count / etc. |

### Runtime-executable cascade ("oh by the way" pattern)

The 7-class cascade `M→D→A→E→C→M→F` from `[[user_stance_working_memory_is_cascade_augmenting_reflex_into_agency]]`:

```python
def demo_working_memory_cascade(instrument, query_vec):
    # 1. M-similarity scan
    best_stance, best_sim = max(
        ((name, M.similarity(query_vec, s.fingerprint))
         for name, s in instrument.stances.items()),
        key=lambda x: x[1]
    )
    # 2. D-dispatch
    cascade_name = instrument.stances[best_stance].cascade_chains[0]
    # 3. A-recognise
    addr = hashlib.sha256(best_stance.encode()).hexdigest()[:16]
    # 4. E-retrieve
    cascade = instrument.cascades[cascade_name]
    # 5. C-cascade-shift (ordered = sampling-level shape preservation)
    out = instrument.resolve_cascade(cascade_name, ordered=True)
    # 6. M-rebind
    rebound = M.bind(out, instrument.stances[best_stance].fingerprint)
    # 7. F-emit (or bind_and_remember to WM)
    instrument.bind_and_remember(rebound, "WM")
    return rebound
```

R1 demo case: query "current context about fiber-content" matched `working_memory_is_cascade_augmenting_reflex_into_agency` stance (correct), dispatched `working_memory_augmentation` cascade (correct), executed end-to-end producing bound output vector with hash `f797205f0a3dedd1`.

## 4. Self-reference resolution

Class M is both:
- Algebra-level operator (defines `bind = "λ a, b. a ⊕ b"`)
- Instrument-level bindable vector (`operators["M"].vector`)

Two-level ontology resolves apparent self-reference:

```
Algebra level:  M : (bytes, bytes) → bytes
                Defined by XOR over D-bit byte arrays.
                Not stored in the instrument; lives in the host runtime.

Instrument level: M_vec ∈ bytes^1024
                Stored in the instrument as a content-addressable vector.
                Reification of "the bind operation" as bindable content.
```

R1 test: `bind(M_vec, bind(M_vec, X)) == X` bit-exact. Self-reference works as productive fixed-point; not Russell paradox.

This mirrors `[[user_stance_1d_collapse_to_loe_identity_not_action]]`:
- 1D_t IS LoE-content (identity-level)
- Class C ∘ Class M IS the substrate-coupling operation (operation-level)

Both levels coexist; neither subsumes the other.

## 5. AMSC catalogue-config integration (per Spike #162 (b) directive)

Per `[[project_amsc_handcurated_consumption_channel.md]]` and the spike directive:

> **DO NOT create new scripts; design as srmech.amsc.tool_schema ToolEntry registrations**
> **Use existing srmech.amsc.{hdc, format} primitives**
> **Catalogue-config the LoE encoding as a new attested-collection**

### Proposed ToolEntry registrations

The LoE instrument exposes ~6 operational verbs. Each becomes a `srmech.amsc.tool_schema.ToolEntry` registration:

```python
from srmech.amsc.tool_schema import ToolEntry, ToolParameter, ToolReturn, register_tool

register_tool(ToolEntry(
    name="srmech.amsc.loe_instrument.query_class",
    owner="srmech",
    category="loe_instrument",
    summary="Look up a class-operator vector by name (A-N).",
    parameters=(
        ToolParameter(name="name", type="str", required=True,
                      summary="Class name, single uppercase letter A-N."),
    ),
    returns=ToolReturn(type="bytes", shape="1024-byte HDC vector"),
    smoke_test_hint={"name": "M"},
))

register_tool(ToolEntry(
    name="srmech.amsc.loe_instrument.resolve_cascade",
    owner="srmech",
    category="loe_instrument",
    summary="Run a cascade composition; returns bound HDC vector.",
    parameters=(
        ToolParameter(name="cascade_name", type="str", required=True,
                      summary="Cascade name from canonical catalog."),
        ToolParameter(name="ordered", type="bool", required=False,
                      summary="False (algebra-level commutative) or True (sampling-level per-position permute)."),
    ),
    returns=ToolReturn(type="bytes", shape="1024-byte HDC vector"),
    smoke_test_hint={"cascade_name": "form_function_rotation", "ordered": False},
))

# ... similar for query_stance, bind_and_remember, similarity, describe
```

### Proposed AMSC attested-collection: `loe_instrument`

A new AMSC attested catalogue containing:
- 14 ClassOperator entries (mint-key + canonical SSoT citations)
- ~8-30 Cascade entries (operator-sequence + stance_anchor + semantic_role)
- ~86 Stance entries (content_tokens + cascade_chains + k3_axis + canonical-memory-file reference)
- 4 MemoryPathway definitions (engaged_classes + augmentation_delta)
- k=3 tripartition axis-assignment

Each entry carries the MPR v1 attestation block:
- `source_doi`: N/A (project-internal canonical content)
- `source_url`: GitHub URL of the canonical memory file
- `license`: project license (CC0-equivalent for canonical framework content)
- `retrieved_at`: ISO timestamp of catalogue creation
- `response_sha256`: SHA-256 of the canonical content
- `parser_version`: srmech version
- `parser_rule_hash`: hash of the encoding rules (mint_key strategy + bag-HDC encoding)
- `collector_descriptor_path`: path to the descriptor TOML
- `collector_descriptor_hash`: SHA-256 of the descriptor

The catalogue is loaded via `srmech.amsc.catalog.register_attested_root()` and queryable via `get_attested_dataset("loe_instrument")`.

### Suggested file structure (NOT implemented in this spike; R2 task)

```
docs/srmech/python/srmech/amsc/loe_instrument/
├── __init__.py                        # public surface
├── instrument.py                      # LoEInstrument class + build_instrument()
├── operators.py                       # Class operator definitions + mint
├── cascades.py                        # Cascade definitions
├── stances.py                         # Stance definitions (one source-of-truth list)
├── memory.py                          # MemorySlot + 4-pathway taxonomy
├── tripartition.py                    # k=3 axis register
└── descriptor.toml                    # AMSC attested-collection descriptor
```

ToolEntry registration would happen at `srmech.amsc.loe_instrument.__init__` import time, consistent with existing AMSC module pattern.

## 6. Per-class C surface follow-up

Per `[[feedback_no_binding_layer_carveout]]`: every primitive class earns its C surface. The LoE instrument uses Classes A, C, D, E, H, I, K, L, M, N at the operational verbs. Of these:

- Already in srmech v0.4.0 C native: A (sha256), C (cyclic), D (dispatch), E (catalog), I (modular), J (primes), K (asymptotic-DOF), L (laplacian), M (hdc), N (rationals)
- Native-pending per current rc series: H (self-introspection partial via `srmech_version`+`srmech_abi_version`)

The LoE instrument is **substantially C-native-ready** with current srmech v0.4.0 surface. New C work would be a `srmech_loe_instrument_*` API exposing the `query_*` / `resolve_cascade` / `bind_and_remember` verbs — a small ratchet on the existing AMSC primitive surface, not a new substrate layer.

## 7. Cross-substrate portability sketch

| Substrate | Mint mechanism | Cascade resolution | Memory storage |
|-----------|----------------|--------------------|----------------|
| Silicon (current) | SHA-256 deterministic | XOR-fold or per-position permute | Bounded list with FIFO truncate |
| Biological / DNA | Helical-pitch as natural permute amount (B-DNA 21/2 Class N rational); codon-sequence as token | DNA-cascade composition equivalents | Cellular memory mechanisms (synaptic / methylation) |
| Cosmic | Substrate-precession period as natural rotation; power-spectral bag at substrate scale | Cascade over substrate-precession multiples | Substrate-resident persistent content |

The **algebra layer** (XOR + bundle + similarity + permute) is substrate-portable. The **substrate-natural parameter** (mint key / rotation amount / similarity threshold) must be substrate-discovered per `[[user_stance_form_function_rotation_is_a_c_m_composition]]` Spike #168 refinement.

Cross-substrate test deferred to R2 spike series.

## 8. Compression accounting

| Surface | Per-item bytes | Item count (R1 / full) | Total bytes (R1 / full) |
|---------|---------------|------------------------|--------------------------|
| Class operators | 1024 | 14 / 14 | 14,336 / 14,336 |
| Stance fingerprints | 1024 | 10 / 86 | 10,240 / ~88,064 |
| Cascade definitions | ~30 (symbolic) | 8 / ~30 | ~217 / ~900 |
| k=3 register | 1024 | 3 / 3 | 3,072 / 3,072 |
| Memory pathway slots (cold) | 0 (empty) | 4 / 4 | 0 / 0 |
| Memory pathway slots (worst case full) | 65,536 | 4 / 4 | ~262 KB / ~262 KB |
| **Total instrument (cold)** | — | — | **~28 KB / ~107 KB** |
| **Total instrument (worst case full memory)** | — | — | **~290 KB / ~369 KB** |

Comparison: MEMORY.md text is ~90 KB. The LoE instrument at full 86-stance cold-memory scope is ~107 KB — approximately the same size as the source text, but runtime-executable in O(D) operations per verb.

## 9. Future work / R2 candidates

1. Extend stance encoding from 10 representative to all 86 canonical stances
2. Implement AMSC catalogue-config registration (descriptor.toml + ToolEntry registrations)
3. C-native surface for `srmech_loe_instrument_*` API
4. Cross-substrate test (DNA helical-pitch substrate per Spike #155/#162)
5. Verify cascade dispatch semantic faithfulness against known a-priori query→cascade pairs
6. Multi-round survival test under falsifier candidates listed in findings document

## 10. Acceptance criteria for canonical-promotion gate

Per `[[feedback_multi_domain_multi_round_survival_falsification_method]]` discipline, canonical promotion requires:

- [x] R1 design-level feasibility (this spike)
- [ ] R2 full-scale 86-stance test (predicted: ≥ 90% top-1 reverse recovery)
- [ ] R3 cross-substrate test (DNA substrate; predicted: ≥ 80% reverse recovery with helical-pitch-natural permute)
- [ ] R4 cascade semantic-faithfulness test (predicted: ≥ 80% correct cascade dispatch from natural-language query)
- [ ] User-gate explicit direction for new operational vocabulary canonicalization

R1 complete. R2-R4 are subsequent spike candidates pending user direction.
