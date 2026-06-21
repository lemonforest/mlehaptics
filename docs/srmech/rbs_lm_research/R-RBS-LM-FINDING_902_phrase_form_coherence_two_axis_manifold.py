"""F902 (re-run after power loss) — phrase-level FORM coherence via the C1 scale-invariance manifold.
Two axes, the fractal "a coherent whole is made of on-manifold parts":
 LEXICAL    = word-level on-manifold (each word's max-sim to the real-word rung)   -> catches gibberish words
 SEQUENTIAL = bigram-level on-manifold (each adjacency's max-sim to the real-ADJACENCY rung) -> catches scrambles
Tested: coherent / scrambled / random-word / gibberish. Native sim_k4_batch for speed. srmech rc13; no bag."""
import json, random, statistics as st
from srmech.amsc import hdc
from srmech.rbs_lm import ContextSubstrate, sim_k4_batch

D = 8192
def fl(q): return q.as_float() if hasattr(q, "as_float") else q
_cs = ContextSubstrate(D=D, hex_chars=16)
def bundle_odd(v): return _cs.bundle_odd(list(v))
def pos_key(i): return hdc.klein4_random(D, seed=0x70000000 + i)
def byte_atom(b): return hdc.klein4_random(D, seed=b)
def compose(parts): return bundle_odd([hdc.klein4_bind(p, pos_key(i)) for i, p in enumerate(parts)])
_WC = {}
def word_C1(w):
    if w not in _WC: _WC[w] = compose([byte_atom(b) for b in w.encode("utf-8")])
    return _WC[w]
def bigram_C1(a, b): return compose([word_C1(a), word_C1(b)])
def maxbatch(v, M): return max(fl(s) for s in sim_k4_batch(v, M))   # native batch neighbor-density

path = "/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson"
toks = []
with open(path) as f:
    for line in f:
        toks += json.loads(line)["s"].split()
        if len(toks) >= 4000: break
toks = toks[:4000]
vocab = sorted(set(toks)); rng = random.Random(12345)
real_bigrams = list({(toks[i], toks[i+1]) for i in range(len(toks)-1)})
MANI = [bigram_C1(a, b) for a, b in rng.sample(real_bigrams, min(700, len(real_bigrams)))]
WREF = [word_C1(w) for w in rng.sample(vocab, min(500, len(vocab)))]
print(f"=== F902 phrase FORM coherence (D={D}, |adjacency manifold|={len(MANI)}, |word ref|={len(WREF)}) ===")

def lexical(words):    return st.mean(maxbatch(word_C1(w), WREF) for w in words)
def sequential(words): return st.mean(maxbatch(bigram_C1(words[i], words[i+1]), MANI) for i in range(len(words)-1))

PL, N = 5, 24
starts = [i for i in range(len(toks)-PL) if all(toks[i+j].isalpha() for j in range(PL))]
coherent = [toks[s:s+PL] for s in rng.sample(starts, N)]
scrambled = []
for p in coherent:
    q = p[:]
    while q == p: rng.shuffle(q)
    scrambled.append(q)
randword = [[rng.choice(vocab) for _ in range(PL)] for _ in range(N)]
gibberish = [["".join(chr(rng.randint(97,122)) for _ in range(rng.randint(3,9))) for _ in range(PL)] for _ in range(N)]

print(f"\n  {'phrase type':<14}{'LEXICAL (words real?)':>24}{'SEQUENTIAL (adjacencies real?)':>32}")
R = {}
for name, ph in [("coherent",coherent),("scrambled",scrambled),("random-word",randword),("gibberish",gibberish)]:
    lex = st.mean(lexical(p) for p in ph); seq = st.mean(sequential(p) for p in ph); R[name] = (lex, seq)
    print(f"  {name:<14}{lex:>24.3f}{seq:>32.3f}")
print("\n  (chance ~0.25) LEXICAL flags gibberish (off the word manifold); SEQUENTIAL flags scrambles + random")
print("  (real words, fake adjacencies). Two-axis FORM coherence from the SAME C1 scale-invariance, one rung up.")
