import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


edit('tcextra.asm', [
    ("global clip_compare, patch_open\n", "global clip_compare, patch_open, patch_cmd\nextern wcsncpy\n"),
    ("""    mov word [rsp+P_PATH], 0
    invoke browse_open, r14, &rsp+P_PATH
    test eax, eax
    jz .d
""", """    mov word [rsp+P_PATH], 0
    mov rax, [g_patch_pre]
    test rax, rax
    jz .ask
    invoke wcsncpy, &rsp+P_PATH, rax, 519
    mov word [rsp+P_PATH+1038], 0
    jmp .gotp
.ask:
    invoke browse_open, r14, &rsp+P_PATH
    test eax, eax
    jz .d
.gotp:
"""),
])
t = open('tcextra.asm', encoding='utf-8').read().rstrip('\n') + """

section .bss
alignb 8
g_patch_pre: resq 1
section .text

; patch_cmd(path): command line entry (bcgui patch FILE)
patch_cmd:
    PROLOG 64
    mov [g_patch_pre], rcx
    xor ecx, ecx
    call patch_open
    mov qword [g_patch_pre], 0
    EPILOG 64
"""
open('tcextra.asm', 'w', encoding='utf-8', newline='\n').write(t)
edit('main.asm', [
    ("clip_compare, patch_open\n", "clip_compare, patch_open, patch_cmd\n"),
    ('WSTR sw_shellcmp, "/shellcompare"\n', 'WSTR sw_shellcmp, "/shellcompare"\nWSTR sw_patch, "patch"\n'),
    ("    invoke _wcsicmp, rsi, &sw_shellcmp\n    test eax, eax\n    jz .shellcmp\n", "    invoke _wcsicmp, rsi, &sw_shellcmp\n    test eax, eax\n    jz .shellcmp\n    invoke _wcsicmp, rsi, &sw_patch\n    test eax, eax\n    jz .patchcmd\n"),
    (".shellcmp:\n    cmp r13d, 3\n", ".patchcmd:\n    cmp r13d, 3\n    jl .free\n    invoke patch_cmd, [rbx+16]\n    jmp .free\n.shellcmp:\n    cmp r13d, 3\n"),
])
print('ok')
