"""Cascade-op TOML descriptors — declarative side of full C/Python parity.

Each ``<op>.toml`` in this directory declares a cascade op's A–N class
composition, signature, native C-symbol mapping, and attestation block.
The Python module ``srmech.amsc.cascade`` is the imperative side; this
directory is the declarative SSoT for cascade STRUCTURE.

In v0.4.5rc1 the descriptors are documentation-grade — read by humans
and tools but not yet consumed by a TOML-driven cascade-op registry
(planned for v0.5.0). They ship as part of the wheel so downstream
consumers can introspect the cascade catalog without re-importing
``srmech.amsc.cascade`` Python source.
"""
