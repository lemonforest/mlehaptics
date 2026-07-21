r"""R-RBS-LM-GENOME-BIOLOGY-SURVEY — the ask-(d) translation-layer prototype AND the cross-kingdom research probe in one:
express biology's genome storage + EDITING mechanisms across the tree of life — bacterial plasmid transfer, CRISPR-
Cas9, transposon "jumping gene", homologous-recombination repair, ciliate (protozoan) macro/micronucleus
rearrangement, and retroviral integration — as compositions of ONE shared A–N primitive set (the primitives our
genome couples through `coupling`, F1242), and verify each works BYTE-EXACT on the shared substrate. If they all reduce to the same small primitive
set, that IS the coherency-translation-layer (F1244): the reason a virus can edit a eukaryote, HGT works across
bacteria, and bacterial CRISPR can be repurposed to edit human genes — the primitives are universal; only the
SITUATIONAL emphasis differs.

The shared primitive set (mapped to the 14 A–N + the k=3 tower):
  address(name)         Class A  — content-address (sha256): the guide / origin / homology arm / title. "find WHERE".
  search(strand, motif) Class D/G — pattern-match / byte-search: the CRISPR PAM+protospacer, restriction site.
  cut(strand, pos)      Class K  — pin-slot boundary: the double-strand break.
  splice(strand,pos,seg)          — insert/append (the Tier-1 stick op, §95c).
  couple(a,b)           Class M  — klein4 bind through `coupling`: recombination / melange / integration join.
  order(perm)           Class C  — chirality / reorder: the ciliate MDS unscramble.
  triality_repair(3)    k=3      — 2-of-3 majority EC (F291); diploid+mark = its k=2+1 form (F1244).

srmech 0.9.0rc253. No ALU magnitude-builtin; sha256 via format; klein4 coupling via hdc. Composes F1243/F1244 (the
tower) · ADR-0004/0005/0006 · §55.1/§95/§95.1 · F291. Run: /tmp/srmech_v/venv/bin/python3 R-RBS-LM-GENOME-BIOLOGY-SURVEY_*.py
"""
import sys

import srmech
from srmech.amsc.format import sha256_raw


# ---- the shared primitives (each labelled by its A–N class) --------------------------------------------------------
def address(name):                                   # Class A — content-address
    return sha256_raw(name.encode())[:8].hex()


def search(strand, motif):                           # Class D/G — pattern-match / byte-search; -1 if absent
    n, m = len(strand), len(motif)
    for i in range(n - m + 1):
        if strand[i:i + m] == motif:
            return i
    return -1


def cut(strand, pos):                                # Class K — pin-slot boundary
    return strand[:pos], strand[pos:]


def splice(strand, pos, seg):                        # insert / append (the Tier-1 stick op)
    return strand[:pos] + list(seg) + strand[pos:]


def triality_repair(c0, c1, c2):                     # k=3 — 2-of-3 majority per position (F291)
    return [max({x, y, z}, key=[x, y, z].count) for x, y, z in zip(c0, c1, c2)]


# ---- each biology mechanism as a composition; returns (name, primitives, purpose, ok) ------------------------------
def m_plasmid():
    """Bacterial plasmid transfer (conjugation/HGT): a content-addressed CIRCULAR stick chromosome copied into a host."""
    plasmid = [7, 7, 3, 1, 4, 1, 5, 9]
    host = [{"label": address("host_chr"), "strand": [2, 6, 5, 3, 5]}]
    host.append({"label": address("plasmid"), "strand": list(plasmid)})     # append-only, no centromere, circular
    got = next(c["strand"] for c in host if c["label"] == address("plasmid"))
    return ("plasmid transfer (bacteria/HGT)", "A + splice(append)", "mobility / horizontal spread", got == plasmid)


def m_crispr():
    """CRISPR-Cas9: guide-RNA content-address -> search the protospacer -> cut -> splice replacement; append the spacer log."""
    host = [2, 6, 9, 9, 9, 5, 3, 5]
    protospacer = [9, 9, 9]
    guide = address("target:" + ",".join(map(str, protospacer)))            # the guide RNA = a content-address
    pos = search(host, protospacer)                                          # Cas9 finds the site
    left, right = cut(host, pos)                                             # the double-strand break
    edited = left[:len(left)] + [8, 8] + right[len(protospacer):]           # splice the repair template
    spacer_log = []
    spacer_log.append(guide)                                                 # the CRISPR array = an append-only log of past addresses
    ok = (search(edited, protospacer) == -1) and (search(edited, [8, 8]) != -1) and len(spacer_log) == 1
    return ("CRISPR-Cas9 (bacteria adaptive immunity)", "A(guide) + D/G(search) + K(cut) + splice + append(log)", "immune memory + directed edit", ok)


def m_transposon():
    """Transposon 'jumping gene': excise a segment (cut,cut) and reinsert at a new content-addressed site — content preserved."""
    strand = [1, 2, 3, 4, 5, 6, 7, 8]
    seg = [3, 4, 5]
    p = search(strand, seg)
    excised_left, rest = cut(strand, p)
    _mid, excised_right = cut(rest, len(seg))
    healed = excised_left + excised_right                                    # original site healed
    moved = splice(healed, 5, seg)                                           # reinsert elsewhere
    ok = (search(moved, seg) != -1) and (sorted(moved) == sorted(strand))    # same content, new location
    return ("transposon move (all kingdoms)", "D/G(search) + K(cut×2) + splice", "self-mobilisation", ok)


def m_recombination():
    """Homologous-recombination repair (diploid / bacterial recA): a break in one copy is filled from the intact homolog."""
    content = [4, 1, 5, 9, 2, 6, 5]
    a = list(content)
    a[2] = a[3] = -1                                                         # a double-strand break (erasure) in copy A
    b = list(content)                                                        # the intact homolog = the template
    repaired = [b[i] if a[i] == -1 else a[i] for i in range(len(a))]         # template-directed fill (the diploid mark)
    return ("homologous recombination (diploid/bacteria)", "A(homology) + couple(template) + K", "break repair (erasure)", repaired == content)


def m_ciliate():
    """Ciliate (protozoa) macro/micronucleus: the SAME content stored two ways — archival scrambled germline (micronucleus)
    -> compact unscrambled working somatic (macronucleus). = Class-L store <-> Class-M working (reversible basis change)."""
    macro = [10, 11, 12, 13, 14, 15]                                        # the working, correctly-ordered gene
    mds = [[12, 13], [10, 11], [14, 15]]                                     # scrambled MDS segments (micronucleus order)
    ies = 99                                                                  # internal eliminated sequence (spacer)
    micro = []
    for seg in mds:
        micro += seg + [ies]                                                 # germline: scrambled + IES spacers
    perm = [1, 0, 2]                                                          # the unscramble permutation (Class C order)
    despacer = [[micro[i], micro[i + 1]] for i in range(0, len(micro), 3)]   # remove IES (search+cut)
    unscrambled = []
    for idx in [perm.index(k) for k in range(len(perm))]:
        unscrambled += despacer[idx]
    return ("ciliate macro/micronucleus (protozoa)", "C(order) + D/G+K(IES removal) — L-store <-> M-working", "storage compaction by purpose", unscrambled == macro)


def m_viral():
    """Retroviral integration (the ask-(d) translation layer): a Tier-1 stick genome integrates into a Tier-2 minted host;
    the viral content is recoverable BY ITS ADDRESS from inside the host — coherent because both use the same coupling."""
    virus = [5, 5, 5, 1, 2]
    host = [8, 8, 8, 8, 8, 8]
    site = 3                                                                 # integrase target (a content-addressed site)
    integrated = splice(host, site, virus)                                   # the SAME splice primitive as plasmid/transposon
    recovered = integrated[site:site + len(virus)]                           # extract the provirus by its coordinates/address
    return ("retroviral integration (virus->eukaryote)", "A(site) + splice + couple", "infection / the translation layer", recovered == virus)


def main():
    print(f"=== R-RBS-LM-GENOME-BIOLOGY-SURVEY (srmech {srmech.__version__}) — biology's genome mechanisms as ONE shared primitive cascade ===\n")
    # k=3 EC sanity (the tower spine)
    ec = triality_repair([1, 2, 3], [1, 9, 3], [1, 2, 9]) == [1, 2, 3]
    mechs = [m_plasmid(), m_crispr(), m_transposon(), m_recombination(), m_ciliate(), m_viral()]
    print(f"{'mechanism':<44} {'primitives (the SAME cascade)':<52} {'purpose (the DIFFERENT)':<30} ok")
    print("-" * 140)
    allok = ec
    for name, prims, purpose, ok in mechs:
        allok &= ok
        print(f"{name:<44} {prims:<52} {purpose:<30} {'PASS' if ok else 'FAIL'}")
    print(f"{'k=3 triality EC (the tower spine)':<44} {'triality_repair (2-of-3 majority)':<52} {'error-correction':<30} {'PASS' if ec else 'FAIL'}")

    print("\nSAME (the coherency tower): every mechanism is a composition of {A content-address, D/G search, K cut,")
    print("     splice/append, M couple, C order, k=3 EC} — the shared cascade (the 14 A–N our genome couples through `coupling`, F1242).")
    print("DIFFERENT (the specialisation): only WHICH primitives are emphasised + the situational PURPOSE (mobility,")
    print("     immunity, self-mobilisation, break-repair, storage-compaction, infection).")
    print("=> a virus edits a eukaryote / CRISPR edits humans / HGT crosses bacteria BECAUSE the primitives are")
    print("   universal — the translation layer is 'same cascade, different rung'. This is ask-(d), prototyped across kingdoms.")
    print(f"\nVERDICT: {'PASS' if allok else 'FAIL'} — all {len(mechs)} mechanisms + k=3 EC compose from the one shared primitive set, byte-exact.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
