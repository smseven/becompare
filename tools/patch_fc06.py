import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


# --- fix register hazards in the include
edit('folder_pair.inc', [
    ("""    mov rcx, [rsp+120]
    mov rdx, [rcx]                    ; A name
    mov rcx, [rax]                    ; B name
    mov r8, [rsp+128]
    cmp r8, 1
    jne .p2
    test dword [r12+F_OPT], 0x80
    jz .Bn
    invoke pr_norm, rdx, rcx
    jmp .tst
.p2:
    cmp r8, 2
    jne .p3
    invoke pr_mask, r12, rdx, rcx
    jmp .tst
""", """    mov rcx, [rsp+120]
    mov r10, [rcx]                    ; A name
    mov r11, [rax]                    ; B name
    mov r8, [rsp+128]
    cmp r8, 1
    jne .p2
    test dword [r12+F_OPT], 0x80
    jz .Bn
    invoke pr_norm, r10, r11
    jmp .tst
.p2:
    cmp r8, 2
    jne .p3
    invoke pr_mask, r12, r10, r11
    jmp .tst
"""),
    ("    invoke pr_ext, rdx, rcx\n.tst:", "    invoke pr_ext, r10, r11\n.tst:"),
    ("""    mov rcx, [rsp+120]
    mov rdx, [rcx]
    cmp word [r13], 0
    je .norel1
    invoke _snwprintf, &rsp+200, 1030, &f_path, r13, rdx
    jmp .k1
.norel1:
    invoke _snwprintf, &rsp+200, 1030, &f_str, rdx
.k1:
    mov rcx, [rsp+152]
    mov rdx, [rcx]
    cmp word [r13], 0
    je .norel2
    invoke _snwprintf, &rsp+1260, 1030, &f_path, r13, rdx
    jmp .k2
.norel2:
    invoke _snwprintf, &rsp+1260, 1030, &f_str, rdx
.k2:""", """    mov rcx, [rsp+120]
    mov r10, [rcx]
    cmp word [r13], 0
    je .norel1
    invoke _snwprintf, &rsp+200, 1030, &f_path, r13, r10
    jmp .k1
.norel1:
    invoke _snwprintf, &rsp+200, 1030, &f_str, r10
.k1:
    mov rcx, [rsp+152]
    mov r10, [rcx]
    cmp word [r13], 0
    je .norel2
    invoke _snwprintf, &rsp+1260, 1030, &f_path, r13, r10
    jmp .k2
.norel2:
    invoke _snwprintf, &rsp+1260, 1030, &f_str, r10
.k2:"""),
])

# --- folder.asm
edit('folder.asm', [
    ("%define ID_CHK_ASFILE 170\n", "%define ID_CHK_ASFILE 170\n%define ID_CHK_LOOSE 174\n%define ID_LBL_MASK 175\n%define ID_EDIT_MASK 176\n%define F_ALT 5184\n%define F_MASKS 5208\n%define EF_ALT 0x1000000\n"),
    ("%define F_SIZE    5184\n", "%define F_SIZE    5472\n"),
    ('WSTR s_c_asfile,', 'WSTR s_c_loose, "이름 느슨하게 맞춤(유니코드·확장자)"\nWSTR s_l_mask, "마스크(*.txt=*.bak;..):"\nWSTR s_c_asfile,'),
    ("extern GetNamedSecurityInfoW,", "extern NormalizeString, GetNamedSecurityInfoW,"),
    ("    invoke enum_dir, r12, 1, r13, &rsp+L_VB\n", "    invoke enum_dir, r12, 1, r13, &rsp+L_VB\n    invoke pair_names, r12, r13, &rsp+L_VA, &rsp+L_VB\n"),
    ("""    invoke str_dup, &rsp+L_REL
    mov [rdi+E_NAME], rax
    mov [rdi+E_DEPTH], r14d
""", """    invoke str_dup, &rsp+L_REL
    mov [rdi+E_NAME], rax
    mov [rdi+E_DEPTH], r14d
    cmp qword [r12+F_ALT+8], 0
    je .noalt
    invoke alt_find, r12, [rdi+E_NAME]
    test rax, rax
    jz .noalt
    or dword [rdi+E_FLAGS], EF_ALT
.noalt:
"""),
    ("    invoke _snwprintf, &rsp+2296, 1100, &f_path, &r12+F_ROOTB, r15\n    test ebx, 4\n", "    invoke alt_bpath, r12, r15\n    invoke _snwprintf, &rsp+2296, 1100, &f_path, &r12+F_ROOTB, rax\n    test ebx, 4\n"),
])
t = open('folder.asm', encoding='utf-8').read().rstrip('\n') + '\n%include "folder_pair.inc"\n'
open('folder.asm', 'w', encoding='utf-8', newline='\n').write(t)

# --- folder_vfs.inc: B path of a renamed entry
edit('folder_vfs.inc', [
    (".a:\n    invoke _snwprintf, r14, 519, &f_path, r15, r13\n    mov eax, 1\n    EPILOG 1600", ".a:\n    test r12d, r12d\n    jz .noaltp\n    invoke alt_bpath, rbx, r13\n    mov r13, rax\n.noaltp:\n    invoke _snwprintf, r14, 519, &f_path, r15, r13\n    mov eax, 1\n    EPILOG 1600"),
])

# --- folder_ui.inc
edit('folder_ui.inc', [
    ("    invoke fold_ent, r12, rbx\n    mov r14, rax\n    cmp r13d, 1\n    je .lr\n", "    invoke fold_ent, r12, rbx\n    mov r14, rax\n    test dword [r14+E_FLAGS], EF_ALT\n    jnz .next\n    cmp r13d, 1\n    je .lr\n"),
    ("    mov esi, [rdi+E_FLAGS]\n    and esi, EF_DIRA|EF_DIRB         ; nonzero = directory\n", "    mov esi, [rdi+E_FLAGS]\n    test esi, EF_ALT\n    jnz .n\n    and esi, EF_DIRA|EF_DIRB         ; nonzero = directory\n"),
    ("    mov r13, rax\n    mov eax, [r13+E_FLAGS]\n    and eax, EF_EXA|EF_EXB|EF_DIRA|EF_DIRB\n", "    mov r13, rax\n    test dword [r13+E_FLAGS], EF_ALT\n    jnz .n\n    mov eax, [r13+E_FLAGS]\n    and eax, EF_EXA|EF_EXB|EF_DIRA|EF_DIRB\n"),
    ("    invoke fold_ent, rbx, r12\n    mov r13, rax\n    invoke wcsncpy, &rsp+96, [r13+E_NAME], 519\n", "    invoke fold_ent, rbx, r12\n    mov r13, rax\n    test dword [r13+E_FLAGS], EF_ALT\n    jnz .d\n    invoke wcsncpy, &rsp+96, [r13+E_NAME], 519\n"),
    ("    invoke _snwprintf, &rsp+2760, 1099, &f_path, &rbx+F_ROOTB, [r13+E_NAME]\n", "    invoke alt_bpath, rbx, [r13+E_NAME]\n    invoke _snwprintf, &rsp+2760, 1099, &f_path, &rbx+F_ROOTB, rax\n"),
    ("    mov dword [rbx+F_SCANERR], 0\n", "    mov dword [rbx+F_SCANERR], 0\n    invoke alt_clear, rbx\n"),
    ("    invoke get_chk, rsi, ID_CHK_ACL\n    shl eax, 8\n    or edi, eax\n", "    invoke get_chk, rsi, ID_CHK_ACL\n    shl eax, 8\n    or edi, eax\n    invoke get_chk, rsi, ID_CHK_LOOSE\n    shl eax, 7\n    or edi, eax\n"),
    ("    ; FC-04: letters -> excluded attribute mask\n", "    invoke GetDlgItem, rsi, ID_EDIT_MASK\n    invoke GetWindowTextW, rax, &rbx+F_MASKS, 120\n    ; FC-04: letters -> excluded attribute mask\n"),
    ("    PLACE ID_CHK_ACL, 220\n", "    PLACE ID_CHK_ACL, 220\n    PLACE ID_CHK_LOOSE, 270\n    PLACE ID_LBL_MASK, 170\n    PLACE ID_EDIT_MASK, 200\n"),
    ("    invoke mk_chk, rsi, &s_c_acl, ID_CHK_ACL, 0\n", "    invoke mk_chk, rsi, &s_c_acl, ID_CHK_ACL, 0\n    invoke mk_chk, rsi, &s_c_loose, ID_CHK_LOOSE, 0\n    invoke mk_lbl, rsi, &s_l_mask, ID_LBL_MASK\n    invoke mk_edit, rsi, ID_EDIT_MASK\n"),
])
edit('../build-gui.ps1', [("-lversion -ladvapi32", "-lversion -ladvapi32 -lnormaliz")])
edit('../tools/test_regressions.py', [("shlwapi version advapi32", "shlwapi version advapi32 normaliz")])
print('fc06 ok')
