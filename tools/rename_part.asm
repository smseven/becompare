
; fold_rename(hwnd, fold, visible index): rename the entry (both sides when it exists on both)
fold_rename:
    PROLOG 5008
    mov rsi, rcx
    mov rbx, rdx
    mov r12, r8
    mov rax, [rbx+F_KIND]
    or rax, [rbx+F_KIND+8]
    jnz .ro
    test qword [g_policy], 1
    jnz .pol
    cmp r12, [rbx+F_NVIS]
    jae .d
    invoke fold_ent, rbx, r12
    mov r13, rax
    invoke wcsncpy, &rsp+96, [r13+E_NAME], 519
    mov word [rsp+96+1038], 0
    lea rdi, [rsp+96]
    invoke wcsrchr, rdi, 0x5C
    test rax, rax
    jz .lf
    lea rdi, [rax+2]
.lf:
    invoke wcsncpy, &rsp+1200, rdi, 259
    mov word [rsp+1200+518], 0
    invoke input_box, rsi, &s_ren_title, &rsp+1200
    test eax, eax
    jz .d
    cmp word [rsp+1200], 0
    je .bad
    xor ecx, ecx
.v:
    movzx eax, word [rsp+1200+rcx*2]
    test eax, eax
    jz .vd
    cmp eax, 0x5C
    je .bad
    cmp eax, '/'
    je .bad
    cmp eax, ':'
    je .bad
    cmp eax, '*'
    je .bad
    cmp eax, '?'
    je .bad
    cmp eax, '"'
    je .bad
    cmp eax, '<'
    je .bad
    cmp eax, '>'
    je .bad
    cmp eax, '|'
    je .bad
    inc ecx
    jmp .v
.vd:
    invoke wcsncpy, &rsp+1760, &rsp+96, 519
    mov word [rsp+1760+1038], 0
    invoke wcsrchr, &rsp+1760, 0x5C
    test rax, rax
    jz .nodir
    mov word [rax+2], 0
    jmp .cat
.nodir:
    mov word [rsp+1760], 0
.cat:
    invoke wcscat, &rsp+1760, &rsp+1200
    xor edi, edi
.side:
    cmp edi, 2
    jae .done
    mov eax, 1
    mov ecx, edi
    shl eax, cl
    test [r13+E_FLAGS], eax
    jz .nx
    lea rbp, [rbx+F_ROOTA]
    test edi, edi
    jz .rt
    lea rbp, [rbx+F_ROOTB]
.rt:
    invoke _snwprintf, &rsp+2840, 1030, &f_path, rbp, &rsp+96
    invoke _snwprintf, &rsp+3920, 1030, &f_path, rbp, &rsp+1760
    invoke MoveFileW, &rsp+2840, &rsp+3920
.nx:
    inc edi
    jmp .side
.done:
    invoke fold_start, rsi, rbx
.d:
    EPILOG 5008
.bad:
    invoke msgbox, rsi, &s_ren_bad, MB_OK|MB_ICONWARNING
    EPILOG 5008
.ro:
    invoke msgbox, rsi, &s_ro, MB_OK|MB_ICONINFO
    EPILOG 5008
.pol:
    invoke msgbox, rsi, &s_pol_blocked, MB_OK|MB_ICONWARNING
    EPILOG 5008

