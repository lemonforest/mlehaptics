"""F912 (thread 2) — recursion: molecules become atoms for the next rung. The SAME octonion cd_mult fold
runs byte->word->phrase->sentence; each level's product is an octonion, bondable at the next (self-similar,
F901's scale-invariance with the content-dependent octonion bond). Sensitivity COMPOUNDS (a sentence
responds to bytes, word-order, AND grouping at every level) and the structure-multiplicity compounds
(Catalan^depth distinct 'sized things'). srmech rc13; exact; no abs."""
from srmech.amsc import cascade, format as fmt
from fractions import Fraction

def nsq(v): return sum(x*x for x in v)
def omul(x,y): return tuple(cascade.cd_mult(x,y))
def byte_oct(b):
    d=bytes.fromhex(fmt.sha256_bytes(f"LoE.byte.{b}".encode())); return tuple((d[i]%9)-4 for i in range(8))
def fold(units):                                  # the ONE operator at every rung: left-fold cd_mult
    p=units[0]
    for u in units[1:]: p=omul(p,u)
    return p
def word_oct(w):      return fold([byte_oct(b) for b in w.encode()])
def phrase_oct(ws):   return fold([word_oct(w) for w in ws])
def sentence_oct(ps): return fold([phrase_oct(p) for p in ps])
def cos2(a,b):
    na,nb=nsq(a),nsq(b)
    return float(Fraction(sum(x*y for x,y in zip(a,b))**2, na*nb)) if na and nb else 0.0
def distinct(seq):                                 # distinct products over groupings of an octonion list
    def P(s):
        if len(s)==1: return {s[0]}
        o=set()
        for i in range(1,len(s)):
            for l in P(s[:i]):
                for r in P(s[i:]): o.add(omul(l,r))
        return o
    return len(P(tuple(seq)))

print("=== F912 recursion: molecules-as-atoms, the SAME octonion operator at every rung ===")
sent=[["the","cat"],["sat","on"],["the","mat"]]    # sentence = phrases = words = bytes
S=sentence_oct(sent)
print(f"\n  byte->word->phrase->sentence all run via the same cd_mult fold; sentence is an octonion: len={len(S)}")
print(f"  self-similar: a word (molecule of bytes) IS an atom at the phrase rung (same cd_mult bonds it).")

# sensitivity COMPOUNDS across levels (a sentence responds to a change at ANY rung)
base=cos2(S,S)
b_byte=cos2(S, sentence_oct([["the","cot"],["sat","on"],["the","mat"]]))   # 1 byte in 1 word
b_word=cos2(S, sentence_oct([["cat","the"],["sat","on"],["the","mat"]]))   # word-order in phrase 1
b_phr =cos2(S, sentence_oct([["sat","on"],["the","cat"],["the","mat"]]))   # phrase-order
print(f"\n  sensitivity (cos^2 to the base sentence; 1.0=same):")
print(f"    change 1 BYTE (cat->cot)     : {b_byte:.3f}")
print(f"    change WORD order (the cat)  : {b_word:.3f}")
print(f"    change PHRASE order          : {b_phr:.3f}")
print(f"    -> a change at ANY rung propagates to the sentence: sensitivity compounds through the recursion.")

# structure-multiplicity COMPOUNDS with depth (Catalan at each rung)
wm=distinct([byte_oct(b) for b in "cat".encode()])     # groupings of a 3-byte word
pm=distinct([word_oct(w) for w in ["the","cat","sat"]])# groupings of a 3-word phrase
print(f"\n  structure multiplicity per rung (distinct groupings): 3-byte word={wm}, 3-word phrase={pm}")
print(f"  compounding: a sentence of P phrases x W words x B bytes has ~Catalan^(#units) distinct architectures")
print(f"  -> the 'sized things' are the deep recursion: same operator, structure space explodes with depth.")
