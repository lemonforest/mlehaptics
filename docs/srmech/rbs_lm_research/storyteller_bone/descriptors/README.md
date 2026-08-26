# `descriptors/` — the attested TOML foundational forms

The MPM-attested TOML 'bone' the dev session fills. Three forms:

- **`storyteller_world.descriptor.toml`** — an attested World descriptor (per-tome content_sha256 + attestation
  class; the shelf the Story Teller narrates). Peer to the F670 MFO §-section descriptor. → a `srmech.storyteller`
  World loader reads it.
- **`storyteller.amsc_catalog.toml`** — an AMSC catalog descriptor (the 6 mandatory sections). → `srmech.amsc`
  registers the storyteller as an attested data source.
- **`storyteller_ops.tool_schema.toml`** — the tool_schema op registrations as TOML. → `srmech.amsc.tool_schema`.

All ATTESTED (F640/F669): a tome without a content-address / a source without attestation is not real.
