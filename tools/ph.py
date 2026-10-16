# shared patch helper: LF everywhere
import glob
def norm_all():
    for p in glob.glob('*.asm')+glob.glob('*.inc')+glob.glob('inc/*.inc'):
        s=open(p,encoding='utf-8').read()
        open(p,'w',encoding='utf-8',newline='\n').write(s)
def patch(p, pairs):
    s=open(p,encoding='utf-8').read()
    for a,b in pairs:
        assert s.count(a)==1,(p,a[:70],s.count(a))
        s=s.replace(a,b)
    open(p,'w',encoding='utf-8',newline='\n').write(s)
