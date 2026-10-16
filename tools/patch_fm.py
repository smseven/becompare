import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')
p = 'fmerge.asm'
s = open(p, encoding='utf-8').read().replace('\r\n', '\n')


def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (a[:60], s.count(a))
    s = s.replace(a, b)


rep("    sub rsp, 0                         ; (alignment preserved)\n    mov dword [rsp+32], 0\n", "")
# fm_path rewrite
a = s.index("; fm_path(fm, e, side, out)")
b = s.index("; fm_openmerge(hwnd, fm)")
s = s[:a] + """; fm_path(fm, e, side, out): full path of an entry on one side
fm_path:
    PROLOG 64
    mov rsi, rcx
    mov rdi, rdx
    mov rbx, r9
    imul eax, r8d, 1040
    lea r12, [rsi+FM_ROOT+rax]
    invoke _snwprintf, rbx, 1090, &f_full, r12, [rdi+FE_NAME]
    EPILOG 64

""" + s[b:]
# openmerge buffers
a = s.index("fm_openmerge:")
b = s.index("; fm_samepath(a, b)")
body = s[a:b]
body = body.replace("PROLOG 4400", "PROLOG 9000").replace("EPILOG 4400", "EPILOG 9000")
body = body.replace("&rsp+1200", "&rsp+2300").replace("&rsp+2304", "&rsp+4500").replace("[rsp+2304]", "[rsp+4500]").replace("&rsp+3408", "&rsp+6700")
body = body.replace("    invoke wcscpy, &rsp+96-0+0, &rsp+96\n", "")
s = s[:a] + body + s[b:]
# fm_run buffers
a = s.index("fm_run:")
b = s.index("; ---------------------------------------------------------------- view")
body = s[a:b]
body = body.replace("PROLOG 2704", "PROLOG 4600").replace("EPILOG 2704", "EPILOG 4600")
body = body.replace("&rsp+1300", "&rsp+2300").replace("[rsp+2600]", "[rsp+4500]").replace("[rsp+2604]", "[rsp+4504]")
body = body.replace("""    mov [rsp+32], r15
    invoke _snwprintf, &rsp+96, 100, &f_done, r12, r13, r14
""", """    invoke _snwprintf, &rsp+96, 100, &f_done, r12, r13, r14, r15
""")
s = s[:a] + body + s[b:]
rep("""    lea eax, [r12-3]
    mov r13d, eax                     ; side
    mov ecx, 1
    shl ecx, cl
    test [rsi+FE_FLAGS], ecx
    jz .dash""", """    lea eax, [r12-3]
    mov r13d, eax                     ; side
    mov ecx, r13d
    mov eax, 1
    shl eax, cl
    test [rsi+FE_FLAGS], eax
    jz .dash""")
open(p, 'w', encoding='utf-8', newline='\n').write(s)


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:60], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


edit('inc/app.inc', [
    ("%define T_EDIT    10\n", "%define T_EDIT    10\n%define T_FMERGE  11\n"),
    ("%define IDM_NEW_EDIT   1010\n", "%define IDM_NEW_EDIT   1010\n%define IDM_NEW_FMERGE 1011\n"),
])
edit('main.asm', [
    ("extern props_register, props_create, edit_create\n", "extern props_register, props_create, edit_create\nextern fmerge_register, fmerge_create\n"),
    ("    call props_register\n", "    call props_register\n    call fmerge_register\n"),
    (".mkedit:\n    invoke edit_create, [g_hframe], rbx\n    jmp .made", ".mkedit:\n    cmp r12, T_FMERGE\n    jae .mkfm\n    invoke edit_create, [g_hframe], rbx\n    jmp .made\n.mkfm:\n    invoke fmerge_create, [g_hframe], rbx\n    jmp .made"),
    ("    invoke AppendMenuW, rbx, MF_STRING, IDM_NEW_EDIT, &m_ned\n", "    invoke AppendMenuW, rbx, MF_STRING, IDM_NEW_EDIT, &m_ned\n    invoke AppendMenuW, rbx, MF_STRING, IDM_NEW_FMERGE, &m_nfm\n"),
    ('WSTR m_ned, "새 텍스트 편집"\n', 'WSTR m_ned, "새 텍스트 편집"\nWSTR m_nfm, "새 폴더 병합 (3-way)"\n'),
    ('WSTR tt_edit, "텍스트 편집"\n', 'WSTR tt_edit, "텍스트 편집"\nWSTR tt_fmerge, "폴더 병합"\n'),
    ('WSTR tn_edit, "edit"\n', 'WSTR tn_edit, "edit"\nWSTR tn_fmerge, "foldermerge"\n'),
    ("tn_media, tn_edit\n", "tn_media, tn_edit, tn_fmerge\n"),
    ("tt_media, tt_edit\n", "tt_media, tt_edit, tt_fmerge\n"),
    ("    cmp ebx, 11\n    jae .alias", "    cmp ebx, 12\n    jae .alias"),
    ("    cmp eax, IDM_NEW_EDIT\n    ja .cmd_other", "    cmp eax, IDM_NEW_FMERGE\n    ja .cmd_other"),
])
edit('home.asm', [
    ('b_d1:     dw __utf16__("폴더 병합 (Pro)"), 13, 10, __utf16__("미구현"), 0\n', 'b_d1:     dw __utf16__("폴더 병합 (Pro)"), 13, 10, __utf16__("3개 폴더 병합 · 충돌 해결"), 0\n'),
])
h = open('home.asm', encoding='utf-8').read()
h = h.replace("    cmp ebp, 11\n", "    cmp ebp, 11\n").replace("    cmp ebp, 10\n    jb .idok", "    cmp ebp, 11\n    jb .idok").replace("    cmp ebx, 10\n    jb .idok", "    cmp ebx, 11\n    jb .idok").replace("    cmp eax, 1010\n    ja .chk_list", "    cmp eax, 1011\n    ja .chk_list")
open('home.asm', 'w', encoding='utf-8', newline='\n').write(h)
b = open('../build-gui.ps1', encoding='utf-8').read().replace("'vtab','props'", "'vtab','props','fmerge'")
open('../build-gui.ps1', 'w', encoding='utf-8', newline='\n').write(b)
print('fm patched')
