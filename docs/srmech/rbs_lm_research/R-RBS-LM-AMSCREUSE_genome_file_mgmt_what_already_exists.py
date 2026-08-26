r"""R-RBS-LM-AMSCREUSE (F730) — before specifying a genome file-management layer, INTROSPECT AMSC and check what
already exists to CHAIN instead of reinvent (user direction 2026-06-13: "make sure we are not re-creating pieces…
but doesn't mean force it").

Maps each requirement of the §43 genome file-management design to an EXISTING AMSC piece (or flags it genuinely new).
Re-runnable: asserts the reusable surfaces are present, and flags the real gaps. NOT a package edit.
"""
import importlib

def has(modname, attr):
    try:
        return hasattr(importlib.import_module(modname), attr)
    except Exception:
        return False

# requirement -> (already-have AMSC piece, present?)  ;  None target = genuinely-new
fmt, cat, desc, tlv = "srmech.amsc.format", "srmech.amsc.catalog", "srmech.amsc.descriptor", "srmech.amsc.tlv"
REUSE = [
    ("per-chromosome ATTESTATION (self-verifying bundle)", fmt, "MPRRecord", "the manifest already IS an MPRRecord; reuse it per-chromosome"),
    ("content-address (cap / body hash)",                  fmt, "sha256_bytes", "Class-A; already used by telomere caps + body_sha256"),
    ("write/read the loose body rows",                     fmt, "write_ndjson", "+ read_ndjson — NDJSON discipline already here"),
    ("validate a bundle on import",                        fmt, "validate_mpr_record", "self-verify a shipped chromosome"),
    ("LIBRARY index / catalog-by-chromosome",              cat, "register_attested_root", "a genome = an attested ROOT (don't build a parallel catalog)"),
    ("enumerate chromosomes",                              cat, "list_attested_sources", "= 'catalog by chromosome'"),
    ("page ONE chromosome",                                cat, "get_attested_dataset", "paginated row content (cf. genome_window)"),
    ("stream a chromosome",                                cat, "iter_attested_dataset", "streaming read"),
    ("discover chromosomes on disk",                       cat, "discover_descriptors", "walks <source>/descriptor.toml — the loose layout already!"),
    ("verify a chromosome's provenance",                   cat, "attestation_audit", "per-row attestation, no payload"),
    ("per-chromosome DESCRIPTION + meta",                  desc, "load_descriptor", "the 'description field' = a descriptor.toml (no new field)"),
    ("content-address the meta",                           desc, "descriptor_hash", "canonical descriptor hash"),
    ("intra-chromosome GENE framing (several/chromosome)", tlv, "tlv_pack", "Class-B TLV (tag,value) — frame each gene"),
]
print("=== AMSC REUSE MAP — genome file-management: what ALREADY exists to chain (F730) ===\n")
reused = 0
for req, mod, attr, note in REUSE:
    ok = has(mod, attr)
    reused += ok
    print(f"  [{'HAVE' if ok else 'MISS'}] {req}\n         -> {mod.split('.')[-1]}.{attr}  — {note}")
print(f"\n  {reused}/{len(REUSE)} requirements map to an EXISTING AMSC op (compose, don't reinvent).")

print("\n=== GENUINELY-NEW surface (small; flagged honestly) ===")
gaps = [
    ("tlv_unpack / a TLV reader", "tlv.tlv_pack exists but the inverse reader is " +
        ("PRESENT" if has(tlv, "tlv_unpack") else "ABSENT — needed to read gene frames back")),
    ("genome speaks the AMSC catalog", "genome ships its OWN manifest.json + genome_catalog() instead of "
        "register_attested_root/list_attested_sources — a mild EXISTING reinvention to consider unifying"),
    ("genome_explode / genome_pack", "loose<->packed converters (orchestration only; compose write_ndjson + "
        "descriptor + MPRRecord + sha256 + discover_descriptors)"),
    ("chromosome(genes=[(label,leaves),…])", "wire tlv_pack into the genome so a chromosome holds SEVERAL genes"),
]
for name, note in gaps:
    print(f"  - {name}: {note}")

print("\n=== HONEST IMPEDANCE (the 'don't force it' caveats) ===")
print("  • AMSC catalog is NDJSON/MPR-row + descriptor.toml oriented; genome body is fixed-width Klein-4 BINARY")
print("    (turns.bin). Reuse the catalog's REGISTRY/DISCOVERY/ATTESTATION layer; keep genome's binary body")
print("    (or store leaves as NDJSON rows IF catalog-nativeness beats compactness — a real tradeoff, not forced).")
print("  • So: a chromosome ~ an attested SOURCE (descriptor.toml + body); a genome ~ an attested ROOT; the")
print("    loose 'tarball one chromosome' layout = exactly catalog's <root>/<source>/ convention. Compose it.")


if __name__ == "__main__":
    pass
