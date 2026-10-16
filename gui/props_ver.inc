; props_ver.inc - VR-01 file version compare (version.dll)

section .rdata
WSTR q_root, "\"
WSTR q_trans, "\VarFileInfo\Translation"
WSTR f_vq, "\StringFileInfo\%04X%04X\%s"
WSTR f_ver4, "%u.%u.%u.%u"
WSTR k_company, "CompanyName"
WSTR k_desc, "FileDescription"
WSTR k_fver, "FileVersion"
WSTR k_internal, "InternalName"
WSTR k_copyright, "LegalCopyright"
WSTR k_orig, "OriginalFilename"
WSTR k_prod, "ProductName"
WSTR k_pver, "ProductVersion"
WSTR k_comments, "Comments"
WSTR k_trade, "LegalTrademarks"
WSTR k_priv, "PrivateBuild"
WSTR k_special, "SpecialBuild"
WSTR l_size, "파일 크기 (바이트)"
WSTR l_mtime, "수정 시각"
WSTR l_fixfv, "파일 버전 (고정 정보)"
WSTR l_fixpv, "제품 버전 (고정 정보)"
WSTR l_company, "회사 (CompanyName)"
WSTR l_desc, "설명 (FileDescription)"
WSTR l_fver, "파일 버전 (FileVersion)"
WSTR l_internal, "내부 이름 (InternalName)"
WSTR l_copyright, "저작권 (LegalCopyright)"
WSTR l_orig, "원본 파일 이름 (OriginalFilename)"
WSTR l_prod, "제품 이름 (ProductName)"
WSTR l_pver, "제품 버전 (ProductVersion)"
WSTR l_comments, "설명 메모 (Comments)"
WSTR l_trade, "상표 (LegalTrademarks)"
WSTR l_priv, "개인 빌드 (PrivateBuild)"
WSTR l_special, "특수 빌드 (SpecialBuild)"

align 8
ver_keys:   dq k_company, k_desc, k_fver, k_internal, k_copyright, k_orig, k_prod, k_pver, k_comments, k_trade, k_priv, k_special
ver_labels: dq l_size, l_mtime, l_fixfv, l_fixpv, l_company, l_desc, l_fver, l_internal, l_copyright, l_orig, l_prod, l_pver, l_comments, l_trade, l_priv, l_special
align 4
ver_cands:  dd 0, 0x04B00409, 0x04B00412, 0x04E40409

%define VF_NSLOT 16
%define VF_SLOTB 260                 ; bytes per value slot (130 wchar)

section .text

; ver_load(path) -> malloc'd version block or 0
ver_load:
    PROLOG 128
    mov rsi, rcx
    invoke GetFileVersionInfoSizeW, rsi, &rsp+96
    mov ebx, eax
    test ebx, ebx
    jz .no
    invoke malloc, rbx
    mov rdi, rax
    test rax, rax
    jz .no
    invoke GetFileVersionInfoW, rsi, 0, rbx, rdi
    test eax, eax
    jnz .ok
    invoke free, rdi
.no:
    xor eax, eax
    EPILOG 128
.ok:
    mov rax, rdi
    EPILOG 128

; ver_str(blob, key, out): fetch one StringFileInfo value, trying the file translation first -> eax 1/0
ver_str:
    PROLOG 560
    mov r12, rcx
    mov r13, rdx
    mov r14, r8
    mov qword [rsp+160], 0
    mov dword [rsp+168], 0
    mov dword [rsp+176], 0x04B00409
    invoke VerQueryValueW, r12, &q_trans, &rsp+160, &rsp+168
    test eax, eax
    jz .cands
    cmp dword [rsp+168], 4
    jb .cands
    mov rax, [rsp+160]
    mov eax, [rax]
    mov [rsp+176], eax
.cands:
    mov dword [rsp+180], 0x04B00409
    mov dword [rsp+184], 0x04B00412
    mov dword [rsp+188], 0x04E40409
    xor ebx, ebx
.try:
    cmp ebx, 4
    jae .none
    mov eax, [rsp+176+rbx*4]
    movzx r15d, ax
    shr eax, 16
    mov ebp, eax
    invoke _snwprintf, &rsp+192, 150, &f_vq, r15, rbp, r13
    mov qword [rsp+160], 0
    mov dword [rsp+168], 0
    invoke VerQueryValueW, r12, &rsp+192, &rsp+160, &rsp+168
    test eax, eax
    jz .next
    cmp dword [rsp+168], 1
    jbe .next
    mov rax, [rsp+160]
    cmp word [rax], 0
    je .next
    invoke wcsncpy, r14, rax, 128
    mov word [r14+256], 0
    mov eax, 1
    EPILOG 560
.next:
    inc ebx
    jmp .try
.none:
    xor eax, eax
    EPILOG 560

; ver_fill(blob or 0, path, slots): fill VF_NSLOT value slots for one side
ver_fill:
    PROLOG 480
    mov r12, rcx
    mov r13, rdx
    mov r14, r8
    invoke GetFileAttributesExW, r13, 0, &rsp+160
    test eax, eax
    jz .nofile
    mov eax, [rsp+160+32]
    mov edx, [rsp+160+28]
    shl rdx, 32
    or rdx, rax
    invoke fmt_size, r14, rdx
    mov rdx, [rsp+160+20]
    invoke fmt_time, &r14+VF_SLOTB, rdx
.nofile:
    test r12, r12
    jz .done
    invoke VerQueryValueW, r12, &q_root, &rsp+96, &rsp+104
    test eax, eax
    jz .strs
    cmp dword [rsp+104], 20
    jb .strs
    mov rbx, [rsp+96]
    movzx esi, word [rbx+10]
    movzx edi, word [rbx+8]
    movzx r15d, word [rbx+14]
    movzx ebp, word [rbx+12]
    invoke _snwprintf, &r14+VF_SLOTB*2, 60, &f_ver4, rsi, rdi, r15, rbp
    movzx esi, word [rbx+18]
    movzx edi, word [rbx+16]
    movzx r15d, word [rbx+22]
    movzx ebp, word [rbx+20]
    invoke _snwprintf, &r14+VF_SLOTB*3, 60, &f_ver4, rsi, rdi, r15, rbp
.strs:
    xor ebp, ebp
.sl:
    cmp ebp, 12
    jae .done
    lea rax, [ver_keys]
    mov r15, [rax+rbp*8]
    lea eax, [rbp+4]
    imul eax, eax, VF_SLOTB
    lea rdi, [r14+rax]
    invoke ver_str, r12, r15, rdi
    inc ebp
    jmp .sl
.done:
    EPILOG 480


; pr_emit(P, slots, labels): one row per non-empty slot pair (A at slots, B at slots + VF_NSLOT slots)
pr_emit:
    PROLOG 64
    mov rbx, rcx
    mov r14, rdx
    mov r12, r8
    xor ebp, ebp
.row:
    cmp ebp, VF_NSLOT
    jae .done
    imul eax, ebp, VF_SLOTB
    lea r8, [r14+rax]
    xor r9d, r9d
    cmp word [r8], 0
    je .a0
    mov r9, r8
.a0:
    lea r15, [r8+VF_NSLOT*VF_SLOTB]
    xor ecx, ecx
    cmp word [r15], 0
    je .b0
    mov rcx, r15
.b0:
    test r9, r9
    jnz .add
    test rcx, rcx
    jz .skip
.add:
    mov rdx, [r12+rbp*8]
    mov r8, r9
    mov r9, rcx
    invoke pr_add, rbx, rdx, r8, r9
.skip:
    inc ebp
    jmp .row
.done:
    EPILOG 64

; pr_ver(P, pathA, pathB) -> eax 1 ok
pr_ver:
    PROLOG 64
    mov rbx, rcx
    mov r12, rdx
    mov r13, r8
    invoke GetFileAttributesW, r12
    cmp eax, -1
    je .fail
    invoke GetFileAttributesW, r13
    cmp eax, -1
    je .fail
    invoke calloc, 2*VF_NSLOT, VF_SLOTB
    mov r14, rax
    test rax, rax
    jz .fail
    invoke ver_load, r12
    mov rsi, rax
    invoke ver_load, r13
    mov rdi, rax
    invoke ver_fill, rsi, r12, r14
    lea r8, [r14+VF_NSLOT*VF_SLOTB]
    invoke ver_fill, rdi, r13, r8
    invoke free, rsi
    invoke free, rdi
    invoke pr_emit, rbx, r14, &ver_labels
.done:
    invoke free, r14
    mov eax, 1
    EPILOG 64
.fail:
    xor eax, eax
    EPILOG 64
