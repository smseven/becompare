import os
os.chdir(r'C:\Users\charles\workspace\becompare')
p = 'README.md'
s = open(p, encoding='utf-8').read()
for a, b in [("# BeCompare — x64 NASM 구현 (Win32 GUI)", "# BeCompare — x64 어셈블리 구현 (Win32 GUI)"),
             ("**x64 NASM**으로 구현한", "**x64 NASM 어셈블리**로 구현한"),
             ("모두 NASM 코드입니다.", "모두 어셈블리입니다."),
             ("INI/설정 파일", "어셈블리/INI")]:
    assert a in s, a
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
