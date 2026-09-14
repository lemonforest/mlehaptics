import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
path = sys.argv[1]; want = set(int(x) for x in sys.argv[2].split(',')); cap=int(sys.argv[3]) if len(sys.argv)>3 else 6000
with open(path,'rb') as f:
    for ln, raw in enumerate(f,1):
        if ln == 1:
            try: print('FIRST', json.loads(raw).get('timestamp'))
            except Exception: pass
        if ln not in want: continue
        o=json.loads(raw); msg=o.get('message') or {}; c=msg.get('content')
        out=[]
        if isinstance(c,str): out.append(c)
        elif isinstance(c,list):
            for x in c:
                if isinstance(x,dict) and x.get('type')=='text': out.append(x['text'])
        print(f"===== L{ln} {o.get('timestamp')} role={msg.get('role')} type={o.get('type')}")
        t='\n'.join(out); print(t[:cap]); print()
