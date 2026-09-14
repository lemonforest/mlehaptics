import json, re, sys, io
path = sys.argv[1]
pat = re.compile(sys.argv[2], re.I)
roles = sys.argv[3].split(',') if len(sys.argv) > 3 else ['user','assistant']
win = int(sys.argv[4]) if len(sys.argv) > 4 else 160
maxhits = int(sys.argv[5]) if len(sys.argv) > 5 else 400
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
n=0
with open(path, 'rb') as f:
    for ln, raw in enumerate(f, 1):
        try:
            s = raw.decode('utf-8', 'replace')
        except Exception:
            continue
        if not pat.search(s):
            continue
        try:
            o = json.loads(s)
        except Exception:
            continue
        typ = o.get('type')
        ts = o.get('timestamp','')
        msg = o.get('message') or {}
        role = msg.get('role', typ)
        content = msg.get('content')
        parts = []
        if isinstance(content, str):
            parts.append(('text', content))
        elif isinstance(content, list):
            for c in content:
                if not isinstance(c, dict): continue
                ct = c.get('type')
                if ct == 'text':
                    parts.append(('text', c.get('text','')))
                elif ct == 'tool_result':
                    cc = c.get('content')
                    if isinstance(cc, list):
                        cc = ' '.join(x.get('text','') for x in cc if isinstance(x, dict))
                    parts.append(('tool_result', str(cc)))
                elif ct == 'tool_use':
                    parts.append(('tool_use', json.dumps(c.get('input',''))))
                elif ct == 'thinking':
                    parts.append(('thinking', c.get('thinking','')))
        else:
            parts.append(('other', s))
        for kind, txt in parts:
            if role not in roles and not ('any' in roles): continue
            label = role + ':' + kind
            if 'kinds' in sys.argv[6:7] : pass
            for m in pat.finditer(txt):
                a = max(0, m.start()-win); b = min(len(txt), m.end()+win)
                print(f"L{ln} {ts} {label} sid={o.get('sessionId','')[:8]} :: " + txt[a:b].replace('\n',' | '))
                n+=1
                if n>=maxhits: sys.exit(0)
