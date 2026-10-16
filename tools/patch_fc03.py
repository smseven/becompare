import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')


def edit(fn, pairs):
    t = open(fn, encoding='utf-8').read().replace('\r\n', '\n')
    for a, b in pairs:
        assert t.count(a) == 1, (fn, a[:70], t.count(a))
        t = t.replace(a, b)
    open(fn, 'w', encoding='utf-8', newline='\n').write(t)


edit('folder.asm', [
    ("%define F_SIZE    5120\n", "%define F_FMIN    5120\n%define F_FMAX    5128\n%define F_FCUT    5136\n%define F_FDAYS   5144\n%define F_SIZE    5152\n%define ID_LBL_FSZ   160\n%define ID_EDIT_FMIN 161\n%define ID_LBL_FTO   162\n%define ID_EDIT_FMAX 163\n%define ID_LBL_FDAY  164\n%define ID_EDIT_FDAYS 165\n"),
    ('WSTR s_excl, "제외:"', 'WSTR s_excl, "제외:"\nWSTR s_fsz, "파일 크기(KB) 최소~최대:"\nWSTR s_fto, "~"\nWSTR s_fday, "최근 수정(일 이내):"\nWSTR f_uint, "%u"\nf_filt: dw 0x1F, "%", "u", ",", "%", "u", ",", "%", "u", 0'),
    ("extern set_status_part, str_dup,", "extern wcstoul, GetSystemTimeAsFileTime, set_status_part, str_dup,"),
    ("""    invoke excl_match, &r12+F_EXCL, rsi
    test eax, eax
    jnz .next
    invoke vec_push, r15, 32
""", """    invoke excl_match, &r12+F_EXCL, rsi
    test eax, eax
    jnz .next
    ; FC-03: size / modification date filters (files only)
    test dword [rsp+L_FD+FD_ATTR], 0x10
    jnz .keep
    mov edx, [rsp+L_FD+FD_SZHI]
    shl rdx, 32
    mov eax, [rsp+L_FD+FD_SZLO]
    or rdx, rax
    mov rax, [r12+F_FMIN]
    test rax, rax
    jz .nomin
    cmp rdx, rax
    jb .next
.nomin:
    mov rax, [r12+F_FMAX]
    test rax, rax
    jz .nomax
    cmp rdx, rax
    ja .next
.nomax:
    mov rax, [r12+F_FCUT]
    test rax, rax
    jz .keep
    cmp [rsp+L_FD+FD_MTIME], rax
    jb .next
.keep:
    invoke vec_push, r15, 32
"""),
])

edit('folder_ui.inc', [
    ("fold_read_ui:\n    PROLOG 64\n", "fold_read_ui:\n    PROLOG 160\n"),
    ("""    invoke GetDlgItem, rsi, ID_EDIT_EXCL
    invoke GetWindowTextW, rax, &rbx+F_EXCL, 255
    EPILOG 64
""", """    invoke GetDlgItem, rsi, ID_EDIT_EXCL
    invoke GetWindowTextW, rax, &rbx+F_EXCL, 255
    ; FC-03 filters
    invoke GetDlgItem, rsi, ID_EDIT_FMIN
    invoke GetWindowTextW, rax, &rsp+96, 18
    invoke wcstoul, &rsp+96, 0, 10
    mov eax, eax
    shl rax, 10
    mov [rbx+F_FMIN], rax
    invoke GetDlgItem, rsi, ID_EDIT_FMAX
    invoke GetWindowTextW, rax, &rsp+96, 18
    invoke wcstoul, &rsp+96, 0, 10
    mov eax, eax
    shl rax, 10
    mov [rbx+F_FMAX], rax
    invoke GetDlgItem, rsi, ID_EDIT_FDAYS
    invoke GetWindowTextW, rax, &rsp+96, 18
    invoke wcstoul, &rsp+96, 0, 10
    mov [rbx+F_FDAYS], eax
    mov qword [rbx+F_FCUT], 0
    test eax, eax
    jz .nofcut
    mov r12d, eax
    invoke GetSystemTimeAsFileTime, &rsp+136
    mov rax, 864000000000
    imul rax, r12
    mov rcx, [rsp+136]
    sub rcx, rax
    jbe .nofcut
    mov [rbx+F_FCUT], rcx
.nofcut:
    EPILOG 160
"""),
])
# fold_read_ui: epilogue replaced above. fold_collect: append the filter suffix
f = open('folder_ui.inc', encoding='utf-8').read().replace('\r\n', '\n')
a = f.index("fold_collect:")
b = f.index("; fold_opts_apply(hwnd, sess, fold)")
seg = f[a:b]
seg = seg.replace("    lea r8, [f_opts]\n    call _snwprintf\n    EPILOG 160\n", """    lea r8, [f_opts]
    call _snwprintf
    invoke wcslen, &rdi+SS_OPTS
    lea r15, [rdi+SS_OPTS]
    lea r15, [r15+rax*2]
    mov r12, [rbx+F_FMIN]
    shr r12, 10
    mov r13, [rbx+F_FMAX]
    shr r13, 10
    mov r14d, [rbx+F_FDAYS]
    invoke _snwprintf, r15, 40, &f_filt, r12, r13, r14
    EPILOG 160
""")
f = f[:a] + seg + f[b:]
f = f.replace("""fold_opts_apply:
    PROLOG 64
""", """fold_opts_apply:
    PROLOG 160
""")
a = f.index("fold_opts_apply:")
b = f.index("; fold_theme(fold)")
seg = f[a:b]
seg = seg.replace("""    invoke GetDlgItem, rsi, ID_EDIT_EXCL
    invoke SetWindowTextW, rax, &rbx+18
.d:
    EPILOG 64
""", """    lea r13, [rbx+18]
.f1f:
    movzx eax, word [r13]
    test eax, eax
    jz .nof
    cmp eax, 0x1F
    je .gotf
    add r13, 2
    jmp .f1f
.gotf:
    mov word [r13], 0
    invoke GetDlgItem, rsi, ID_EDIT_EXCL
    invoke SetWindowTextW, rax, &rbx+18
    mov word [r13], 0x1F
    lea r14, [r13+2]
    xor r15d, r15d
.pf:
    cmp r15d, 3
    jae .d
    invoke wcstoul, r14, &rsp+96, 10
    mov r12d, eax
    mov eax, ID_EDIT_FMIN
    cmp r15d, 1
    jb .have
    mov eax, ID_EDIT_FMAX
    cmp r15d, 2
    jb .have
    mov eax, ID_EDIT_FDAYS
.have:
    mov [rsp+104], eax
    mov word [rsp+112], 0
    test r12d, r12d
    jz .set
    invoke _snwprintf, &rsp+112, 16, &f_uint, r12
.set:
    mov eax, [rsp+104]
    invoke GetDlgItem, rsi, rax
    invoke SetWindowTextW, rax, &rsp+112
    mov r14, [rsp+96]
    cmp word [r14], ','
    jne .d
    add r14, 2
    inc r15d
    jmp .pf
.nof:
    invoke GetDlgItem, rsi, ID_EDIT_EXCL
    invoke SetWindowTextW, rax, &rbx+18
.d:
    EPILOG 160
""")
seg = seg.replace("EPILOG 64", "EPILOG 160") if "EPILOG 64" in seg else seg
f = f[:a] + seg + f[b:]
open('folder_ui.inc', 'w', encoding='utf-8', newline='\n').write(f)

edit('folder_ui.inc', [
    ("    PLACE ID_BTN_COLLAP, 76\n    lea r13d, [r13+r15]\n    add r13d, r14d                   ; y of the list\n",
     "    PLACE ID_BTN_COLLAP, 76\n    lea r13d, [r13+r15]\n    add r13d, r14d\n    mov r12d, r14d\n    PLACE ID_LBL_FSZ, 170\n    PLACE ID_EDIT_FMIN, 70\n    PLACE ID_LBL_FTO, 16\n    PLACE ID_EDIT_FMAX, 70\n    PLACE ID_LBL_FDAY, 130\n    PLACE ID_EDIT_FDAYS, 50\n    lea r13d, [r13+r15]\n    add r13d, r14d                   ; y of the list\n"),
    ("    invoke mk_lbl, rsi, &s_excl, ID_LBL_EXCL\n    invoke mk_edit, rsi, ID_EDIT_EXCL\n",
     "    invoke mk_lbl, rsi, &s_excl, ID_LBL_EXCL\n    invoke mk_edit, rsi, ID_EDIT_EXCL\n    invoke mk_lbl, rsi, &s_fsz, ID_LBL_FSZ\n    invoke mk_edit, rsi, ID_EDIT_FMIN\n    invoke mk_lbl, rsi, &s_fto, ID_LBL_FTO\n    invoke mk_edit, rsi, ID_EDIT_FMAX\n    invoke mk_lbl, rsi, &s_fday, ID_LBL_FDAY\n    invoke mk_edit, rsi, ID_EDIT_FDAYS\n"),
])
print('fc03 patched')
