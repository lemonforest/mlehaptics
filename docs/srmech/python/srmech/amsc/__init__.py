"""Attested Multi-Source Collector/Catalog (AMSC) framework.

Both names work for AMSC — at *collection time* (T1/T3) the
framework's adapter classes are *collecting* attested rows from
upstream archives; at *read time* the resulting NDJSON SSOTs are a
*catalog* of attested data that downstream packages register and
query via the universal bridge. Same abbreviation either way;
either reading is correct, pick whichever fits the lifecycle stage
you're naming.

The framework's modules and their public re-exports:

* :mod:`srmech.amsc.format` — Mathematical Provenance Record (MPR) v1
  on-disk format (``MPRRecord``, NDJSON IO, ``sha256_bytes``).
* :mod:`srmech.amsc.descriptor` — descriptor TOML loader
  (``Descriptor``, ``load_descriptor``, ``discover_descriptors``,
  ``render_template``, ``descriptor_hash``).
* :mod:`srmech.amsc.catalog` — universal bridge surface
  (``list_attested_sources``, ``get_attested_dataset``,
  ``get_attested_descriptor``, ``attestation_audit``,
  ``register_attested_root``, T2 local-kernel overlay).
* :mod:`srmech.amsc.gap_suggester` — schema-gap-driven trigger.
* :mod:`srmech.amsc.adapters` — adapter implementations
  (html_scraper, json_api, csv_bulk, netcdf_grid, geotiff_bbox,
  literature_curated).

The ergonomic re-exports below let consumers ``from srmech.amsc
import MPRRecord, Descriptor`` etc. without reaching into each
submodule.
"""

from __future__ import annotations

from .catalog import (
    attestation_audit,
    clear_local_kernel,
    get_attested_dataset,
    get_attested_descriptor,
    get_local_kernel_state,
    iter_attested_dataset,
    list_attested_sources,
    list_registered_roots,
    register_attested_root,
    use_local_kernel,
)
from .descriptor import (
    Descriptor,
    DescriptorValidationError,
    descriptor_hash,
    discover_descriptors,
    load_descriptor,
    render_template,
)
from .format import (
    MANDATORY_ATTESTATION_FIELDS,
    MANDATORY_RENDERING_FIELDS,
    MPR_SCHEMA_VERSION,
    MPRRecord,
    MPRValidationError,
    read_ndjson,
    sha256_bytes,
    sha256_hex,
    sha256_raw,
    validate_mpr_record,
    write_ndjson,
)
# The exact number-field carrier Qalg = ℚ[x]/(m) — the generalisation of the
# Gaussian-rational Qi (= Qalg over x²+1). Exact-substrate algebraic numbers
# (rotation-last roadmap rc-C). A carrier, not a ToolEntry (mirrors Qi).
from .qalg import Qalg
# The exact prime-coordinate carrier Qprime — a positive int as its exponent
# vector {prime: exponent} of n = ∏ pᵉ (FTA). The Class-J exact carrier
# (multiply=add-exponents, gcd=min, lcm=max, multiplicative-order period); the
# F923 / §74 capstone that closes the last harmonic-ladder rung. A carrier, not
# a ToolEntry (mirrors Qi / Qalg).
from .qprime import Qprime
# The exact-rational matrix carrier QMat — the bigint peer of the float64 Mat
# (exact dense linear algebra over ℚ, no magnitude ceiling). A carrier, not a
# ToolEntry, mirrors Qi / Qalg / Qprime.
from .qmat import QMat
# The exact-rational polynomial carrier Poly — the 1-D polynomial peer of QMat
# (exact univariate algebra over ℚ: long division, monic GCD, dispersion shift,
# Horner eval; no magnitude ceiling). The FOUNDATION carrier of the §76 telescope
# Σ-row prover (rc39+). A carrier, not a ToolEntry, mirrors Qi / Qalg / Qprime /
# QMat.
from .poly import Poly
# The exact-rational TRIVARIATE polynomial carrier TriPoly — the 3-variable
# sibling of BiPoly (exact ℚ[n,j,k]: the free variable n + two summation
# variables j, k, with shift_n/shift_j/shift_k + delta_j/delta_k difference
# operators). The foundation of the multivariate "sums of sums" creative-
# telescoping row (the rc53 apagodu_zeilberger op consumes it). A carrier, not a
# ToolEntry, mirrors Poly / QMat / Qi / Qalg / Qprime.
from .tripoly import TriPoly
# The exact ADDITIVE theta-function carrier ThetaSum — a ℚ(q,p)-linear SUM of
# theta-products over a single theta-product denominator. The additive layer over
# the multiplicative EllRatio (rc60) that GENUINE elliptic creative telescoping
# needs (theta-quotients are not additively closed). Its is_zero decides theta
# identities EXACTLY by the elliptic degree bound (quasi-periodicity grouping + the
# Fundamental Theorem of Elliptic Functions). A carrier, not a ToolEntry, mirrors
# EllRatio / QMat / Poly / TriPoly.
from .thetasum import ThetaSum
# v0.3.0 — tool_schema introspection (Task #198) registers srmech's
# own AMSC tools at import time. Profile-contributed tools register
# later, at profile-activation time via profile_loader.
from . import tool_schema  # noqa: F401  (side effect: register tools)

__all__ = [
    # format
    "MANDATORY_ATTESTATION_FIELDS",
    "MANDATORY_RENDERING_FIELDS",
    "MPR_SCHEMA_VERSION",
    "MPRRecord",
    "MPRValidationError",
    "read_ndjson",
    "sha256_bytes",
    "sha256_hex",
    "sha256_raw",
    "validate_mpr_record",
    "write_ndjson",
    # descriptor
    "Descriptor",
    "DescriptorValidationError",
    "descriptor_hash",
    "discover_descriptors",
    "load_descriptor",
    "render_template",
    # catalog
    "attestation_audit",
    "clear_local_kernel",
    "get_attested_dataset",
    "get_attested_descriptor",
    "get_local_kernel_state",
    "iter_attested_dataset",
    "list_attested_sources",
    "list_registered_roots",
    "register_attested_root",
    "use_local_kernel",
    # carriers
    "Qalg",
    "Qprime",
    "QMat",
    "Poly",
    "TriPoly",
    "ThetaSum",
]
