# 사용: ctl.py "명령들"  예) "wait 3; press start; shot a.png; key x"
import sys,time,os
sys.path.insert(0,os.path.dirname(__file__))
from emu import Emu
e=Emu.attach()
for c in ' '.join(sys.argv[1:]).split(';'):
    c=c.strip().split()
    if not c: continue
    if c[0]=='wait': time.sleep(float(c[1]))
    elif c[0]=='press': e.press(' '.join(c[1:]),0.4)
    elif c[0]=='hold': e.key(c[1],float(c[2]))
    elif c[0]=='shot': e.grab(os.path.join('shots',c[1]))
    elif c[0]=='rep':
        for i in range(int(c[2])): e.key(c[1]); time.sleep(float(c[3]) if len(c)>3 else 0.4)
    elif c[0]=='ss': e.savestate()
    elif c[0]=='eshot': e.shot(os.path.join('shots',c[1]))
e.detach()
