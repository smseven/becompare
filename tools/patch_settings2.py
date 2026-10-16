import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


edit('main.asm', [
    (".c_open:\n    call open_file_dlg\n", ".c_settings:\n    invoke settings_show, rsi\n    jmp .ok0\n.c_open:\n    call open_file_dlg\n"),
    ('''.noctl:
    cmp edi, VK_F5
    je .run
    cmp edi, VK_ESCAPE
    je .esc
    cmp edi, VK_RETURN
    je .ret
    test r12d, r12d
    jz .no
    cmp edi, 'W'
    je .closetab
    cmp edi, 'S'
    je .save
    cmp edi, VK_TAB
    je .nexttab
.no:''', '''.noctl:
    invoke GetKeyState, VK_SHIFT
    mov ebp, r12d
    test ax, ax
    jns .noshift
    or ebp, 2
.noshift:
    lea r8, [g_keytab]
    xor ebx, ebx
.kl:
    cmp ebx, 6
    jae .fixed
    cmp [r8+rbx*8], edi
    jne .kn
    cmp [r8+rbx*8+4], ebp
    je .khit
.kn:
    inc ebx
    jmp .kl
.khit:
    cmp ebx, 0
    je .run
    cmp ebx, 1
    je .save
    cmp ebx, 2
    je .closetab
    cmp ebx, 3
    je .nexttab
    cmp ebx, 4
    je .nextdiff
    jmp .prevdiff
.fixed:
    cmp edi, VK_ESCAPE
    je .esc
    cmp edi, VK_RETURN
    je .ret
.no:'''),
    ('''.save:
    mov r13d, BC_SAVE
    mov r14d, 1
.dosend:''', '''.save:
    mov r13d, BC_SAVE
    mov r14d, 1
    jmp .dosend
.nextdiff:
    mov r13d, BC_NEXTDIFF
    mov r14d, 1
    jmp .dosend
.prevdiff:
    mov r13d, BC_PREVDIFF
    mov r14d, 1
.dosend:'''),
])
edit('settings.asm', [
    ("    invoke _snwprintf, &rsp+300, 20, &f_hex6, rcx\n", "    mov r14d, ecx\n    invoke _snwprintf, &rsp+300, 20, &f_hex6, r14\n"),
    ("    lea rdx, [rax+2]\n    invoke WritePrivateProfileStringW, &sec_ext, r14, rdx, &g_ini\n", "    lea r8, [rax+2]\n    invoke WritePrivateProfileStringW, &sec_ext, r14, r8, &g_ini\n"),
])
print('settings2 patched')
