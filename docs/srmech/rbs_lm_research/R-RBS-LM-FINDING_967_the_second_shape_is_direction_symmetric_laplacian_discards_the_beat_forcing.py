"""F967 — the SECOND SHAPE (user) is DIRECTION: the symmetric Laplacian encodes the fractal (community/
scale-invariant content) but DISCARDS the forcing that decides the stop. Grounded: 99% of content bigrams
are purely ONE-directional (a->b exists, b->a never); the F960 symmetric recursive_cut (min/max edges)
throws this away. So the knowledge tome has the fractal (WHAT clusters) but not the beat-forcing (WHICH WAY /
WHERE TO STOP) -- why a phrase doesn't cleanly stop (F958/F965). The forcing = the beat chirality (F948
rotation-first vs rotation-last), the_one sigma (time-direction), or the magnetic/directed Laplacian.
srmech rc97; no numpy; no dense matrix (directed edge COUNTS only)."""
import json
toks=[]
with open('/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson') as f:
    for line in f:
        toks.extend(json.loads(line)['s'].split())
        if len(toks)>=2000: break
toks=toks[:2000]
stop=set('the of in a is and to as for on it was were are that with by an at from or be'.split())
know=[t for t in toks if t not in stop]
dc={}
for a,b in zip(know,know[1:]):
    if a!=b: dc[(a,b)]=dc.get((a,b),0)+1
seen=set(); asym=0; total=0
for (a,b) in dc:
    if (a,b) in seen or (b,a) in seen: continue
    seen.add((a,b)); total+=1
    if dc.get((b,a),0)==0: asym+=1
print('content bigrams: %d distinct pairs; purely one-directional: %d (%.0f%%)'%(total,asym,100*asym/total))
print('=> symmetric Laplacian (F960) discards this -> the fractal has no forcing -> the phrase does not stop')
print('=> the second shape = DIRECTION (beat chirality F948 / the_one sigma / magnetic_laplacian)')
