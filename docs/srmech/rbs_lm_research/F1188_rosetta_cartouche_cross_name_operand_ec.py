"""F1188 (#243): the literal Rosetta operand-EC — the cross-name CARTOUCHE check (Champollion's actual method).

The Rosetta's three scripts are k=3 redundancy (F1177). But the DECIPHERMENT operand-EC is cross-NAME, not just
cross-version: a hieroglyphic phonetic glyph (the OPERAND — a sound value) is recovered because the SAME sound recurs
across many royal cartouches (Ptolemy, Cleopatra, Alexander, Berenike, Arsinoe), and the shared-position CONSISTENCY
across names is the error-correction — the same responsion (a sound must map to the same glyph everywhere). This is
Champollion's Ptolemy-vs-Cleopatra cross-check (Lettre à M. Dacier, 1822): the letters shared between the two names,
appearing at the corresponding positions, confirmed the phonetic values.

Model: each royal name is a phonetic-letter sequence (standard Egyptological cartouche transliterations); each letter =
a hieroglyphic glyph; the SAME letter -> the SAME glyph across all names (the phonetic principle = op(x)operand). Test:
corrupt a glyph occurrence; is the letter (operand) recoverable from another name where it recurs? = cross-name k-of-n
operand-EC. numpy-free; no magnitude-builtin; plain-dict tally.
"""

# standard cartouche phonetic transliterations (attested Egyptological readings of the royal names)
NAMES = {
    "Ptolemy":   list("ptolmys"),
    "Cleopatra": list("kleopatra"),
    "Alexander": list("alksantrs"),
    "Berenike":  list("brnika"),
    "Arsinoe":   list("arsina"),
    "Philip":    list("pilipos"),
}

# each phonetic letter (the OPERAND — a sound value) -> its cross-name redundancy (how many cartouches it appears in)
letters = {}
for nm, seq in NAMES.items():
    for ch in set(seq):
        letters.setdefault(ch, set()).add(nm)

print("F1188 (#243): the Rosetta cartouche operand-EC — a sound (operand) is recovered by its RECURRENCE across names\n")
print("   %d royal cartouches; %d distinct phonetic glyphs (the operand alphabet)\n" % (len(NAMES), len(letters)))
print("   glyph(sound)   appears in # cartouches (its cross-name redundancy k)   attestable?")
for ch in sorted(letters, key=lambda c: -len(letters[c])):
    k = len(letters[ch])
    tag = "k>=3 MAJORITY-CORRECTABLE" if k >= 3 else ("k=2 cross-checkable (detect)" if k == 2 else "k=1 UN-attestable (needs a 4th name)")
    print("     %s              %d                                           %s" % (ch, k, tag))

# --- the operand-EC: corrupt a glyph occurrence, recover the sound from another cartouche where it recurs ---
attest = sum(1 for ch in letters if len(letters[ch]) >= 2)
majority = sum(1 for ch in letters if len(letters[ch]) >= 3)
recoverable_occ = tot_occ = 0
for nm, seq in NAMES.items():
    for i, ch in enumerate(seq):
        tot_occ += 1
        if len(letters[ch] - {nm}) >= 1:       # the sound recurs in >=1 OTHER cartouche -> recoverable if damaged here
            recoverable_occ += 1

print("\n   operand-EC summary:")
print("     glyphs cross-checkable (k>=2, in >=2 names)  : %d/%d = %.0f%%" % (attest, len(letters), 100 * attest / len(letters)))
print("     glyphs MAJORITY-correctable (k>=3, in >=3)   : %d/%d = %.0f%%" % (majority, len(letters), 100 * majority / len(letters)))
print("     glyph OCCURRENCES recoverable if damaged     : %d/%d = %.0f%%  (the sound recurs elsewhere)" % (
    recoverable_occ, tot_occ, 100 * recoverable_occ / tot_occ))
print("\n  READ: the Rosetta decipherment IS op(x)operand(x)responsion at the cross-NAME scale — op = 'read this cartouche")
print("  slot', operand = the sound value, responsion = the cross-name consistency (a sound maps to the SAME glyph in EVERY")
print("  cartouche). A glyph in >=2 names is cross-checkable (Champollion's Ptolemy-vs-Cleopatra, k=2 DETECT); in >=3 names")
print("  it is majority-CORRECTABLE (k>=3, F1177). The k=1 glyphs (a sound in only one name) are the un-attestable residue")
print("  — needing a further parallel source (a 4th cartouche), exactly F1177's all-differ residue handed to the expert (F282).")
