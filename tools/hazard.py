# flags invoke lines where a later argument reads a register that an earlier argument already overwrote
import re,sys,glob
dest=['rcx','rdx','r8','r9']
alias={'rcx':['rcx','ecx','cx','cl'],'rdx':['rdx','edx','dx','dl'],'r8':['r8','r8d','r8w','r8b'],'r9':['r9','r9d','r9w','r9b']}
def split_args(s):
    out=[];cur='';depth=0
    for ch in s:
        if ch=='[':depth+=1
        if ch==']':depth-=1
        if ch==',' and depth==0: out.append(cur.strip());cur=''
        else: cur+=ch
    out.append(cur.strip());return out
bad=0
for p in glob.glob('gui/*.asm')+glob.glob('gui/*.inc'):
    for n,line in enumerate(open(p,encoding='utf-8'),1):
        m=re.match(r'\s*(PROLOG|EPILOG)\s+(\d+)',line)
        if m and int(m.group(2))%16:
            print(f'{p}:{n}: frame size {m.group(2)} is not a multiple of 16'); bad+=1
for p in glob.glob('gui/*.asm')+glob.glob('gui/*.inc'):
    for n,line in enumerate(open(p,encoding='utf-8'),1):
        m=re.match(r'\s*invoke\s+\w+\s*,\s*(.*?)(;.*)?$',line)
        if not m: continue
        args=split_args(m.group(1))
        for i in range(1,min(len(args),4)):
            a=args[i].lstrip('&#')
            for j in range(0,i):
                if j==i: continue
                for al in alias[dest[j]]:
                    if re.search(r'\b'+al+r'\b',a):
                        print(f'{p}:{n}: arg{i} "{args[i]}" reads {dest[j]} already overwritten by arg{j} -> {line.strip()}')
                        bad+=1;break
        # stack args (index>=4) read after all four regs were set
        for i in range(4,len(args)):
            a=args[i].lstrip('&#')
            for j in range(0,4):
                for al in alias[dest[j]]:
                    if re.search(r'\b'+al+r'\b',a) and not (len(args)>j and args[j].lstrip('&#')==a):
                        print(f'{p}:{n}: stack arg{i} "{args[i]}" reads {dest[j]} -> {line.strip()}')
                        bad+=1;break
print('hazards:',bad)
