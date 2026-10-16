import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


stamp = r'''
; copy_acl(src, dst): SY-06 copy the NTFS DACL
copy_acl:
    PROLOG 64
    mov rsi, rcx
    mov rdi, rdx
    mov qword [rsp+80], 0
    mov qword [rsp+88], 0
    invoke GetNamedSecurityInfoW, rsi, 1, 4, 0, 0, &rsp+80, 0, &rsp+88
    test eax, eax
    jnz .d
    invoke SetNamedSecurityInfoW, rdi, 1, 4, 0, 0, [rsp+80], 0
    invoke LocalFree, [rsp+88]
.d:
    EPILOG 64

; fold_stamp(hwnd, fold, dir 0 = A->B / 1 = B->A): SY-04 copy modification time and attributes onto the other side
fold_stamp:
    PROLOG 4400
    mov rsi, rcx
    mov rbx, rdx
    mov r12d, r8d
    mov rax, [rbx+F_KIND]
    or rax, [rbx+F_KIND+8]
    jnz .ro
    test qword [g_policy], 1
    jnz .pol
    mov rdi, -1
.n:
    invoke SendMessageW, [rbx+F_HLIST], LVM_GETNEXTITEM, rdi, LVNI_SELECTED
    movsxd rdi, eax
    test rdi, rdi
    js .done
    invoke fold_ent, rbx, rdi
    mov r13, rax
    mov eax, [r13+E_FLAGS]
    and eax, EF_EXA|EF_EXB|EF_DIRA|EF_DIRB
    cmp eax, EF_EXA|EF_EXB
    jne .n
    invoke _snwprintf, &rsp+96, 1099, &f_path, &rbx+F_ROOTA, [r13+E_NAME]
    invoke _snwprintf, &rsp+2300, 1099, &f_path, &rbx+F_ROOTB, [r13+E_NAME]
    lea r14, [rsp+96]                 ; source
    lea r15, [rsp+2300]               ; target
    mov rbp, [r13+E_MTA]
    test r12d, r12d
    jz .go
    xchg r14, r15
    mov rbp, [r13+E_MTB]
.go:
    mov [rsp+4380], rbp
    invoke GetFileAttributesW, r14
    mov ebp, eax
    invoke SetFileAttributesW, r15, 0x80
    invoke CreateFileW, r15, 0x100, 7, 0, OPEN_EXISTING, 0x02000000, 0
    cmp rax, -1
    je .attr
    mov r13, rax
    invoke SetFileTime, r13, 0, 0, &rsp+4380
    invoke CloseHandle, r13
.attr:
    cmp ebp, -1
    je .n
    and ebp, 0x27                    ; read-only, hidden, system, archive
    invoke SetFileAttributesW, r15, rbp
    jmp .n
.done:
    invoke fold_start, rsi, rbx
    EPILOG 4400
.ro:
    invoke msgbox, rsi, &s_ro, MB_OK|MB_ICONINFO
    EPILOG 4400
.pol:
    invoke msgbox, rsi, &s_pol_blocked, MB_OK|MB_ICONWARNING
    EPILOG 4400
'''

edit('folder.asm', [
    ("%define ID_CHK_ASFILE 170\n", "%define ID_CHK_ASFILE 170\n%define ID_BTN_STAMPLR 171\n%define ID_BTN_STAMPRL 172\n%define ID_CHK_ACL 173\n"),
    ('WSTR s_c_asfile,', 'WSTR s_b_stamplr, "→ 시각·속성 맞춤"\nWSTR s_b_stamprl, "← 시각·속성 맞춤"\nWSTR s_c_acl, "복사 시 NTFS 권한(ACL) 포함"\nWSTR s_c_asfile,'),
    ("extern icon_set,", "extern GetNamedSecurityInfoW, SetNamedSecurityInfoW, LocalFree, SetFileAttributesW, SetFileTime, icon_set,"),
])
f = open('folder_ui.inc', encoding='utf-8').read().replace('\r\n', '\n')
pairs = [
    ("    invoke CopyFileW, rsi, rdi, 0\n    EPILOG 2400\n", """    invoke CopyFileW, rsi, rdi, 0
    mov ebx, eax
    test eax, eax
    jz .cfd
    test dword [r12+F_OPT], 0x100
    jz .cfd
    invoke copy_acl, rsi, rdi
.cfd:
    mov eax, ebx
    EPILOG 2400
"""),
    ("    PLACE ID_BTN_MOVERL, 56\n", "    PLACE ID_BTN_MOVERL, 56\n    PLACE ID_BTN_STAMPLR, 150\n    PLACE ID_BTN_STAMPRL, 150\n"),
    ("    invoke mk_btn, rsi, &s_b_moverl, ID_BTN_MOVERL\n", "    invoke mk_btn, rsi, &s_b_moverl, ID_BTN_MOVERL\n    invoke mk_btn, rsi, &s_b_stamplr, ID_BTN_STAMPLR\n    invoke mk_btn, rsi, &s_b_stamprl, ID_BTN_STAMPRL\n"),
    ("    PLACE ID_CHK_ASFILE, 250\n", "    PLACE ID_CHK_ASFILE, 250\n    PLACE ID_CHK_ACL, 220\n"),
    ("    invoke mk_chk, rsi, &s_c_asfile, ID_CHK_ASFILE, 0\n", "    invoke mk_chk, rsi, &s_c_asfile, ID_CHK_ASFILE, 0\n    invoke mk_chk, rsi, &s_c_acl, ID_CHK_ACL, 0\n"),
    ("    cmp ebx, ID_BTN_MOVERL\n    je .b_mrl\n", "    cmp ebx, ID_BTN_MOVERL\n    je .b_mrl\n    cmp ebx, ID_BTN_STAMPLR\n    je .b_slr\n    cmp ebx, ID_BTN_STAMPRL\n    je .b_srl\n"),
    (".b_mrl:\n    invoke fold_move, rsi, r15, 1\n    jmp .zero\n", ".b_mrl:\n    invoke fold_move, rsi, r15, 1\n    jmp .zero\n.b_slr:\n    invoke fold_stamp, rsi, r15, 0\n    jmp .zero\n.b_srl:\n    invoke fold_stamp, rsi, r15, 1\n    jmp .zero\n"),
]
for a, b in pairs:
    assert f.count(a) == 1, a[:60]
    f = f.replace(a, b)
f = f.rstrip('\n') + '\n' + stamp
# ACL flag into F_OPT (bit 8)
a = "    invoke get_chk, rsi, ID_CHK_ATTR\n    shl eax, 6\n    or edi, eax\n"
assert f.count(a) == 1
f = f.replace(a, a + "    invoke get_chk, rsi, ID_CHK_ACL\n    shl eax, 8\n    or edi, eax\n")
open('folder_ui.inc', 'w', encoding='utf-8', newline='\n').write(f)
print('sy ok')
