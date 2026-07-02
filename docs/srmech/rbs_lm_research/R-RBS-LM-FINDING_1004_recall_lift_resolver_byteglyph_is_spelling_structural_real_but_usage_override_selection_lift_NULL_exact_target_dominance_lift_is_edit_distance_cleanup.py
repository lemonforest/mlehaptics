"""F1004 (F769 / #222) — recall-lift resolver: EDIT-DISTANCE (spelling) cleanup + USAGE-overrides-valid-word.
Premise (F920): the byte-glyph EMISSION carries SPELLING similarity (cat~cot), orthogonal to USAGE (king~
emperor) -- so a resolver must SPLIT them (edit-distance for cleanup; usage to select, overriding spelling).
Per feedback_read_independent_structure_check_first, the STRUCTURAL test comes first (no recall): is byte-glyph
sim really SPELLING not usage? Then the recall-lift demo (usage-selection beats spelling-selection). Sparse."""
from srmech.amsc import hdc
from srmech.rbs_lm import substrate as S
D=8192; cs=S.ContextSubstrate(D=D, hex_chars=16); bind=hdc.klein4_bind
def fl(q): return q.as_float() if hasattr(q,'as_float') else float(q)
ROLE=hdc.klein4_random(D, seed=4242)
enc=cs.enc                                          # byte-glyph word encoder (encode_word_byteglyph)
def sim(a,b): return fl(hdc.klein4_similarity(a,b))
# ---- (A) READ-INDEPENDENT structural: is byte-glyph sim SPELLING or USAGE? ----
spell=[('cat','cot'),('cat','cut'),('run','ran'),('big','bag'),('hat','hot'),('sing','ring')]
usage=[('king','queen'),('king','emperor'),('big','large'),('dog','puppy'),('happy','glad'),('car','vehicle')]
sp=[sim(enc(a),enc(b)) for a,b in spell]; us=[sim(enc(a),enc(b)) for a,b in usage]
print("F769 recall-lift resolver -- STRUCTURAL first (read-independent): byte-glyph sim = SPELLING or USAGE?")
print("  byte-glyph sim of SPELLING pairs (cat~cot): mean %.3f  [%s]"%(sum(sp)/len(sp), ' '.join('%.2f'%x for x in sp)))
print("  byte-glyph sim of USAGE pairs (king~emperor): mean %.3f  [%s]"%(sum(us)/len(us), ' '.join('%.2f'%x for x in us)))
print("  => byte-glyph sim is %s (spelling %.3f vs usage %.3f) -- confirms word-encoding=SPELLING, orthogonal to usage (F920)"%(
      'SPELLING' if sum(sp)/len(sp) > sum(us)/len(us) else 'usage?', sum(sp)/len(sp), sum(us)/len(us)))
# ---- (B) the CONSEQUENCE: byte-glyph SELECTION can't SEPARATE spelling-neighbors; USAGE selection can ----
def dseed(w): return (sum((i+1)*ord(ch) for i,ch in enumerate(w)) % 90000) + 3   # deterministic seed (no hash())
c='pope'; b='church'; bprime='churchy'   # bprime = usage-distinct but spelling-neighbor of b (edit-1)
cands=['church','chairs','people','history','chinese','chess', bprime]
# realistic recall regime: c->b stored inside a BUNDLE of distractor relationships (probe is degraded, not clean)
import random as _r  # only for a fixed distractor word-pair list (seeded, deterministic)
distract=[('a','history'),('is','people'),('the','chinese'),('of','chess'),('in','chairs'),('was','people'),
          ('and','history'),('to','chinese'),('for','chess'),('on','chairs'),('that','people'),('it','history')]
rels=[(c,b)]+distract
# (B1) SEPARATION MARGIN of the spelling-neighbours in each representation (structural, ~read-independent)
uv={w: hdc.klein4_random(D, seed=dseed(w)) for w in set(cands+[c]+[x for p in rels for x in p])}
m_bg = sim(enc(b), enc(bprime))          # how confusable are b / b' in byte-glyph (spelling) space?
m_us = sim(uv[b], uv[bprime])            # ... in usage (relationship) space?
print("  (B1) SEPARATION of spelling-neighbours %r / %r (structural, lower=more separable):"%(b,bprime))
print("       byte-glyph sim(%s,%s)=%.3f (FUSED -- spelling collapses the usage distinction) | usage sim=%.3f (SEPARATE)"%(b,bprime,m_bg,m_us))
# (B2) AGGREGATE recall-lift: many targets, EACH with a spelling-neighbour competitor in the candidate set.
# spelling-neighbour = b with its last char doubled (edit-1, a real byte-glyph confuser, usage-distinct).
ctx=['pope','china','music','river','planet','engine','doctor','island','forest','castle']
tgt=['church','empire','melody','valley','saturn','turbine','patient','harbour','meadow','fortress']
neigh=[w[:-1]+w[-1]+w[-1] for w in tgt]   # churchh, empiree, ... spelling-neighbours (edit-1)
allw=set(ctx+tgt+neigh+[x for p in distract for x in p])
uv={w: hdc.klein4_random(D, seed=dseed(w)) for w in allw}
rels_bg=[(ctx[i],tgt[i]) for i in range(len(tgt))]+distract
Mbg=cs.bundle_odd([bind(bind(enc(x),ROLE), enc(y)) for x,y in rels_bg])
Mus=cs.bundle_odd([bind(bind(uv[x],ROLE), uv[y]) for x,y in rels_bg])
def recall(M,vf,ci,candset):
    probe=bind(M, bind(vf(ci),ROLE))
    return max(candset, key=lambda t: sim(probe, vf(t)))
ok_bg=ok_us=lost_to_neigh=0
for i in range(len(tgt)):
    cset=tgt+neigh                                     # every target competes with ALL spelling-neighbours
    pbg=recall(Mbg, enc, ctx[i], cset); pus=recall(Mus, lambda w:uv[w], ctx[i], cset)
    ok_bg+= (pbg==tgt[i]); ok_us+= (pus==tgt[i]); lost_to_neigh += (pbg==neigh[i])
print("  (B2) AGGREGATE recall-lift over %d targets, each vs ALL %d spelling-neighbours (bundle noise):"%(len(tgt),len(neigh)))
print("       byte-glyph (SPELLING) selection top-1: %d/%d = %.0f%%  (of misses, %d went to the spelling-neighbour)"%(ok_bg,len(tgt),100*ok_bg/len(tgt),lost_to_neigh))
print("       USAGE-override        selection top-1: %d/%d = %.0f%%  (usage separates the spelling-neighbours)"%(ok_us,len(tgt),100*ok_us/len(tgt)))
# ---- edit-distance cleanup: snap a noisy emission to the nearest valid word (the OTHER resolver half) ----
def edit(a,b):
    if not a or not b: return max(len(a),len(b))
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1): cur.append(min(prev[j]+1, cur[-1]+1, prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]
# (C) where the recall-lift ACTUALLY is: edit-distance CLEANUP of corrupted emissions + usage-override at TIES.
vocab=tgt+neigh                              # 20 valid words incl. spelling-neighbour pairs (church/churchh...)
def corrupt(w): return w[:len(w)//2]+w[len(w)//2+1:]   # drop the middle char (edit-1 corruption of the emission)
rec=ties=usage_fixed=0
for i,w in enumerate(tgt):
    e=corrupt(w)
    d=[(edit(e,v),v) for v in vocab]; md=min(x[0] for x in d)
    winners=[v for dd,v in d if dd==md]      # all valid words at the min edit distance
    if len(winners)==1:
        rec += (winners[0]==w)
    else:                                    # TIE -> this is where usage-override earns its keep
        ties += 1
        probe=bind(Mus, bind(uv[ctx[i]],ROLE))
        pick=max(winners, key=lambda v: sim(probe, uv[v]))   # usage breaks the spelling tie
        usage_fixed += (pick==w); rec += (pick==w)
print("  (C) recall-lift WHERE IT IS -- edit-distance CLEANUP of corrupted emissions (drop 1 char) over %d words:"%len(tgt))
print("      recovered to the intended valid word: %d/%d = %.0f%%   (spelling-fusion used CONSTRUCTIVELY)"%(rec,len(tgt),100*rec/len(tgt)))
print("      edit-distance TIES needing usage-override: %d ; usage broke correctly: %d/%d"%(ties,usage_fixed,ties))
print("=> HONEST split: byte-glyph=spelling (A, real, read-independent) FUSES neighbours (0.707) -- but this does NOT")
print("   hurt next-token SELECTION (B2 null: 100%%=100%%, exact-target dominates its degraded neighbour). The resolver's")
print("   recall-lift is the CLEANUP half (C: noisy emission -> valid word, fusion used constructively) + usage-override")
print("   only at edit-distance TIES. The 'usage-beats-spelling-in-selection' lift I hypothesised is NOT supported (B2).")
