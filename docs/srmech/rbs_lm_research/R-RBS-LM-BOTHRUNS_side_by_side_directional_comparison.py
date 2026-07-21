import math
from itertools import permutations
from srmech.amsc import cascade

OLD = {  # F1268/F1269: n=50 probes, 8-point ladder
 512:([44,64,89,115,147,185,243,320],[1.00,0.98,0.96,0.84,0.69,0.58,0.38,0.26]),
 1024:([89,128,179,230,294,371,486,640],[1.00,0.98,0.88,0.86,0.59,0.51,0.26,0.24]),
 2048:([179,256,358,460,588,742,972,1280],[1.00,1.00,0.87,0.69,0.57,0.36,0.27,0.19]),
 4096:([358,512,716,921,1177,1484,1945,2560],[1.00,0.92,0.92,0.62,0.52,0.40,0.13,0.04]),
 8192:([716,1024,1433,1843,2355,2969,3891,5120],[0.98,0.92,0.81,0.50,0.43,0.18,0.12,0.08]),
}
NEW = {  # TAILFIX: n=80 probes, 13-point ladder to 4.3x
 512:([44,64,89,115,147,179,211,249,294,345,409,473,550],
      [1.0,0.984,0.955,0.87,0.728,0.611,0.481,0.398,0.337,0.264,0.146,0.147,0.109]),
 1024:([89,128,179,230,294,358,422,499,588,691,819,947,1100],
      [1.0,0.992,0.9,0.835,0.673,0.467,0.353,0.262,0.202,0.161,0.085,0.08,0.047]),
 2048:([179,256,358,460,588,716,844,998,1177,1382,1638,1894,2201],
      [1.0,0.977,0.9,0.707,0.595,0.422,0.235,0.286,0.129,0.11,0.122,0.0,0.049]),
 4096:([358,512,716,921,1177,1433,1689,1996,2355,2764,3276,3788,4403],
      [0.978,0.93,0.789,0.607,0.424,0.329,0.247,0.119,0.134,0.098,0.049,0.049,0.012]),
 8192:([716,1024,1433,1843,2355,2867,3379,3993,4710,5529,6553,7577,8806],
      [1.0,0.919,0.706,0.642,0.439,0.317,0.16,0.146,0.11,0.049,0.037,0.025,0.0]),
}
DIMS=[512,1024,2048,4096,8192]

def crossing(lad,rs,t):
    for i in range(len(lad)-1):
        r0,r1=rs[i],rs[i+1]
        if r0>=t>=r1 and r0!=r1:
            return lad[i]+(r0-t)/(r0-r1)*(lad[i+1]-lad[i])
    return None

def fit(pts):
    xs=[math.log(d) for d,_ in pts]; ys=[math.log(n) for _,n in pts]
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    a=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs)
    b=my-a*mx
    return a, max(cascade.magnitude(y-(a*x+b)) for x,y in zip(xs,ys))

def spectrum(C, thr):
    out=[]
    for t in thr:
        pts=[(d,crossing(*C[d],t)) for d in DIMS]
        pts=[(d,n) for d,n in pts if n]
        if len(pts)>=4:
            a,r=fit(pts); out.append((t,a,r))
    return out

def ptest(alphas):
    k=len(alphas)
    ag=sum(1 for i in range(k-1) if alphas[i]>=alphas[i+1])
    if k>9: return ag,None
    tot=cnt=0
    for p in permutations(range(k)):
        tot+=1
        if sum(1 for i in range(k-1) if p[i]>=p[i+1])>=ag: cnt+=1
    return ag, cnt/tot

THR=[0.91,0.84,0.76,0.69,0.62,0.55,0.48,0.40,0.33]
so=spectrum(OLD,THR); sn=spectrum(NEW,THR)
print("=== BOTH RUNS SIDE BY SIDE (same 9 thresholds) ===")
print("  %-8s %-22s %-22s %-9s" % ("thresh","OLD n=50 / 8pt","NEW n=80 / 13pt","shift"))
do=dict((t,(a,r)) for t,a,r in so); dn=dict((t,(a,r)) for t,a,r in sn)
for t in THR:
    o=do.get(t); n=dn.get(t)
    os="%.3f (r%.3f)"%o if o else "   --"
    ns="%.3f (r%.3f)"%n if n else "   --"
    sh="%+.3f"%(n[0]-o[0]) if (o and n) else "  --"
    print("  %-8.2f %-22s %-22s %-9s" % (t,os,ns,sh))

print()
for name,s in (("OLD (n=50, 8pt)",so),("NEW (n=80, 13pt)",sn)):
    al=[a for _,a,_ in s]
    ag,p=ptest(al)
    print("  %-18s k=%d  alphas %s" % (name,len(al)," ".join("%.3f"%x for x in al)))
    print("  %-18s adjacent-in-direction %d/%d   p(>=)= %.4g   spread %.3f  max resid %.3f"
          % ("",ag,len(al)-1,p,max(al)-min(al),max(r for _,_,r in s)))
    print("  %-18s monotone? %s" % ("", "YES" if ag==len(al)-1 else "NO"))
    print()
print("  NOTE: alphas within a run are NOT independent (one curve per dim, overlapping")
print("  interpolation intervals). Both p-values are OPTIMISTIC upper bounds on significance.")
