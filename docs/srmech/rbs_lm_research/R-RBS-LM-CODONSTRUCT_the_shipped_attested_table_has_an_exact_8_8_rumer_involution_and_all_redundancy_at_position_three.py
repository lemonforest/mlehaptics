"""Verify the codon-table structure against srmech's OWN MPR-attested genetic_code row.

Reads the shipped MPR v1 envelope, recovers the 64-codon table from `ncbieaa`, and
measures: the 8/8 fully-degenerate vs split root partition, the split signatures, the
per-position synonymy counts, and Rumer's T<->G / C<->A involution on the two-base root.

srmech 0.9.0rc336. Exhaustive. Pure integer/string -- no float, no abs(), no numpy, no RNG.
"""
import json, os
import srmech.amsc.attested.genetic_code as GC

fail = []
def check(label, got, want):
    ok = got == want
    print(f"  {'OK ' if ok else 'XX '} {label}: {got}")
    if not ok: fail.append((label, got, want))

p = list(GC.__path__)[0]
rows = [json.loads(l) for l in open(os.path.join(p, "row.ndjson"))
        if l.strip() and not l.startswith("#")]
r = rows[0]; d = r["data"]
ncbieaa = d["ncbieaa"]
print(f"=== srmech's own MPR-attested genetic_code (transl_table {d['transl_table_id']}) ===")
print(f"  response_sha256 : {r['attestation']['response_sha256']}")
print(f"  ncbieaa         : {ncbieaa}")
check("64 codons", len(ncbieaa), 64)

B = "TCAG"                                   # NCBI base order
codons = [a + b + c for a in B for b in B for c in B]
cmap = dict(zip(codons, ncbieaa))
roots = [x + y for x in B for y in B]
full  = [q for q in roots if len({cmap[q + z] for z in B}) == 1]
split = [q for q in roots if len({cmap[q + z] for z in B}) > 1]

print("\n=== 1. the 16 roots partition 8 / 8 ===")
check("fully-degenerate roots (third base irrelevant)", sorted(full),
      ["AC", "CC", "CG", "CT", "GC", "GG", "GT", "TC"])
check("split roots", sorted(split),
      ["AA", "AG", "AT", "CA", "GA", "TA", "TG", "TT"])

print("\n=== 2. the split signature is near-uniform 2+2 ===")
sig = {}
for q in split:
    g = {}
    for z in B: g.setdefault(cmap[q + z], []).append(z)
    sig[q] = tuple(sorted(len(v) for v in g.values()))
check("roots splitting 2+2 (pyrimidine {T,C} vs purine {A,G})",
      sum(1 for q in split if sig[q] == (2, 2)), 6)
check("the two irregulars", {q: sig[q] for q in split if sig[q] != (2, 2)},
      {"TT": (2, 2)} if False else {"TG": (1, 1, 2), "AT": (1, 3)})

print("\n=== 3. redundancy is overwhelmingly at position 3 ===")
syn = {0: 0, 1: 0, 2: 0}
for c in cmap:
    for pos in range(3):
        for b in B:
            if b == c[pos]: continue
            if cmap[c[:pos] + b + c[pos + 1:]] == cmap[c]: syn[pos] += 1
check("synonymous single substitutions per position (of 192 each)",
      [syn[0], syn[1], syn[2]], [8, 2, 128])
print("      => position 2 is almost perfectly NON-redundant (2/192); position 3 carries")
print("         two-thirds of all single-substitution synonymy (128/192).")

print("\n=== 4. Rumer's involution T<->G, C<->A on the ROOT ===")
R = str.maketrans({"T": "G", "C": "A", "A": "C", "G": "T"})
img = {q: q.translate(R) for q in roots}
check("it IS an involution (applying twice = identity)",
      all(img[img[q]] == q for q in roots), True)
check("it is FIXED-POINT-FREE", [q for q in roots if img[q] == q], [])
check("fully-degenerate roots mapped INTO the split octet", 
      sum(1 for q in full if img[q] in split), 8)
for q in sorted(full):
    print(f"      {q} -> {img[q]}   ({'split' if img[q] in split else 'FULL'})")
print("      => a fixed-point-free ORDER-2 involution on the 4-letter alphabet exchanges")
print("         the two octets exactly. Class C (an order-2 chirality on the root alphabet),")
print("         NOT a Class I rotation.")

print("\n" + ("ALL CHECKS PASSED" if not fail else f"FAILURES: {fail}"))
raise SystemExit(1 if fail else 0)
