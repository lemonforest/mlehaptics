"""srmech-primary research catalog SSOT root.

Houses declarative descriptor catalogs the framework ships as part of
its public research output (cascade catalog, future per-domain registry
entries). Each subdirectory carries TOML descriptors plus optional
NDJSON / schema files following the AMSC attested-catalog convention.

v0.4.5rc1 introduces ``cascade_catalog/`` — the TOML side of the
cascade-op C-parity + TOML retrofit per the v0.4.5 line; corrects the
v0.4.3rc6 / v0.4.4rc1 carve-out that shipped ``srmech.amsc.cascade``
without dedicated C symbols or TOML descriptors.
"""
