"""F1033 probe — rc105 CHIRAL EDGES over quantized spans: the black-hole--singularity edge.
Wiki's black-hole article ASSERTS singularity (+q edge); MFO §VII.4.1 says 'WITHOUT literal
singularity' (a negation token within the span window -> -q edge). Build the tiny knowledge
graph, run the REAL srmech rc105 magnetic_laplacian(charges=) vs signed_laplacian:
the contested edge must SURVIVE as imaginary chiral flux where signed ANNIHILATES.
Plus the corpus-scale edge census (single-word-title mentions over quantized spans)."""
import json, re
from srmech.amsc import laplacian as L

NEG = {"not", "no", "never", "without"}
NUM = {"one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve",
       "twenty","thirty","forty","fifty","hundred","thousand","first","second","third","fourth",
       "fifth","sixth","seventh","eighth","ninth","tenth","eleventh","twelfth"}

def quantize(title, toks, W=12, S=6):
    t = set(title.lower().split())
    a = [w.isdigit() or w in t or w in NUM for w in toks]
    keep = [False]*len(toks)
    for i in range(0, max(1, len(toks)-W+1), S):
        if sum(a[i:i+W]) >= 2:
            for j in range(i, min(i+W, len(toks))): keep[j] = True
    return [w for w,k in zip(toks,keep) if k]

# --- the black-hole neighborhood, from BOTH sources ---
idx = json.load(open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_index.json'))
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    f.seek(idx['black hole']); wiki = json.loads(f.readline())['s'].split()
fidx = json.load(open('/home/skirklan/corpora/framework_notebooks/framework_index.json'))
mfo_t = next(t for t in fidx if 'dark stars end at the 2d boundary' in t)
with open('/home/skirklan/corpora/framework_notebooks/framework_instrument.ndjson') as f:
    f.seek(fidx[mfo_t]); mfo = json.loads(f.readline())['s'].split()

def edge_sense(toks, anchor, target, win=8):
    """Directed sense of anchor->target in this text: -1 if a negation token sits within
    `win` tokens BEFORE a target mention, else +1. None if target absent."""
    senses = []
    for i, w in enumerate(toks):
        if w == target:
            senses.append(-1 if any(t in NEG for t in toks[max(0, i-win):i]) else +1)
    if not senses:
        return None
    return -1 if -1 in senses else +1     # any negated mention marks the negated sense

for name, toks in (('wiki black-hole', wiki), ('mfo vii.4.1', mfo)):
    s = edge_sense(toks, 'black hole', 'singularity')
    print("%-16s singularity mentions -> sense %s" % (name, s))

# --- the rc105 demo: signed annihilates, magnetic SURVIVES (q=0.125; q=0.25 is the one
# degenerate point where cos(pi/2)=0 kills the balanced real part -- caught by first run) ---
# weights = REAL mention counts: wiki asserts 'singularity' a times; mfo negates it b times
a_w = sum(1 for w in wiki if w == 'singularity')
b_w = sum(1 for w in mfo if w == 'singularity')
print("\nmention counts: wiki(+) a=%d | mfo(-) b=%d" % (a_w, b_w))
q = 0.125
edges  = [(0,1), (0,1), (0,2)]
sgn    = L.signed_laplacian(3, edges, [float(a_w), -float(b_w), 1.0])
mag    = L.magnetic_laplacian(3, edges, [float(a_w), float(b_w), 1.0], charges=[+q, -q, +q])
def c(v): return complex(getattr(v, 'real', v), getattr(v, 'imag', 0.0))
print("signed  [bh, singularity] = %s   (balanced dispute -> 0; imbalance -> partial only)" % c(sgn[0][1]))
m = c(mag[0][1])
print("magnetic(rc105, q=1/8) [bh, singularity] = %.4f%+.4fi" % (m.real, m.imag))
print("  REAL part carries the SUM (a+b)cos -- the coupling SURVIVES even when balanced;")
print("  IMAG part carries the DISPUTE (a-b)sin -- the chiral flux = %.4f" % m.imag)
# balanced control: a=b=1 -> signed EXACTLY 0, magnetic real still -cos(pi/4)
sgn0 = L.signed_laplacian(2, [(0,1),(0,1)], [1.0, -1.0])
mag0 = L.magnetic_laplacian(2, [(0,1),(0,1)], [1.0, 1.0], charges=[+q, -q])
print("balanced control: signed = %s | magnetic = %.4f%+.4fi  <- ANNIHILATED vs SURVIVES"
      % (c(sgn0[0][1]), c(mag0[0][1]).real, c(mag0[0][1]).imag))

# --- corpus-scale census: single-word-title mention edges over quantized spans ---
titles1 = {t for t in idx if ' ' not in t and len(t) > 3}
E = 0
neg_E = 0
n = 0
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        rec = json.loads(line)
        t = (rec.get('t') or '').lower()
        q_toks = quantize(t, rec['s'].split())
        seen = set()
        for i, w in enumerate(q_toks):
            if w in titles1 and w not in t.split() and w not in seen:
                seen.add(w)
                E += 1
                if any(x in NEG for x in q_toks[max(0, i-8):i]):
                    neg_E += 1
        n += 1
        if n >= 30000:
            break
print("\ncensus (30k articles, quantized spans, single-word-title mentions):")
print("  %d edges (~%.1f per article) | %d negation-sensed (%.1f%%) | full-corpus est. ~%.1fM edges,"
      % (E, E/n, neg_E, 100.0*neg_E/max(1,E), E/n*240880/1e6))
print("  ~%.0f MB raw (u32,u32,i8) -> the chiral edge layer is kernel-artifact-sized" % (E/n*240880*9/1e6))
