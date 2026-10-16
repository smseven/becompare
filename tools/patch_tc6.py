import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


edit('tcextra.asm', [(""".copy:
    xor eax, eax
.cl:
    cmp eax, r8d
    jae .cd
    mov r9b, [rdx+rax]
    mov [rcx+rax], r9b
    inc eax
    jmp .cl
.cd:
    add rax, rcx
    ret""", """.copy:
    push r9
    xor eax, eax
.cl:
    cmp eax, r8d
    jae .cd
    mov r9b, [rdx+rax]
    mov [rcx+rax], r9b
    inc eax
    jmp .cl
.cd:
    add rax, rcx
    pop r9
    ret""")])
edit('inc/app.inc', [("%define IDM_UPDATE     1070\n", "%define IDM_UPDATE     1070\n%define IDM_CLIP       1071\n%define IDM_PATCH      1072\n")])
edit('main.asm', [
    ("g_keytab, update_check, update_start\n", "g_keytab, update_check, update_start, clip_compare, patch_open\n"),
    ("    invoke AppendMenuW, rbx, MF_STRING, IDM_NEW_FMERGE, &m_nfm\n", "    invoke AppendMenuW, rbx, MF_STRING, IDM_NEW_FMERGE, &m_nfm\n    invoke AppendMenuW, rbx, MF_STRING, IDM_CLIP, &m_clip\n    invoke AppendMenuW, rbx, MF_STRING, IDM_PATCH, &m_patch\n"),
    ('WSTR m_upd, "업데이트 확인..."\n', 'WSTR m_upd, "업데이트 확인..."\nWSTR m_clip, "클립보드와 텍스트 비교"\nWSTR m_patch, "패치 파일(diff) 보기..."\n'),
    ("    cmp eax, IDM_UPDATE\n    je .c_update\n", "    cmp eax, IDM_UPDATE\n    je .c_update\n    cmp eax, IDM_CLIP\n    je .c_clip\n    cmp eax, IDM_PATCH\n    je .c_patch\n"),
    (".c_update:\n    invoke update_check, rsi, 0\n    jmp .ok0\n", ".c_update:\n    invoke update_check, rsi, 0\n    jmp .ok0\n.c_clip:\n    invoke clip_compare, rsi\n    jmp .ok0\n.c_patch:\n    invoke patch_open, rsi\n    jmp .ok0\n"),
])
edit('../build-gui.ps1', [("'conv','update'", "'conv','update','tcextra'")])
print('ok')
