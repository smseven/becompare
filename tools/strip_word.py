import os
os.chdir(r'C:\Users\charles\workspace\becompare')


def sub(p, pairs):
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (p, a)
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='\n').write(s)


sub('gui/main.asm', [("BeCompare 어셈블리 구현\\n", "BeCompare\\n")])
sub('gui/util.asm', [('"BeCompare (어셈블리)"', '"BeCompare"')])
sub('README.md', [("# BeCompare — x64 어셈블리 구현 (Win32 GUI)", "# BeCompare — x64 NASM 구현 (Win32 GUI)"),
                  ("**x64 NASM 어셈블리**로 구현한", "**x64 NASM**으로 구현한"),
                  ("모두 어셈블리입니다.", "모두 NASM 코드입니다."),
                  ("어셈블리/INI", "INI/설정 파일")])
sub('src/bc.asm', [("compare tool in x64 assembly", "compare tool (x64 NASM)")])
