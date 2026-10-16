; props_reg.inc - RG-01 registry compare: two keys, values and sub keys compared recursively

section .rdata
WSTR rn0, "HKEY_CLASSES_ROOT"
WSTR rn1, "HKCR"
WSTR rn2, "HKEY_CURRENT_USER"
WSTR rn3, "HKCU"
WSTR rn4, "HKEY_LOCAL_MACHINE"
WSTR rn5, "HKLM"
WSTR rn6, "HKEY_USERS"
WSTR rn7, "HKU"
WSTR rn8, "HKEY_CURRENT_CONFIG"
WSTR rn9, "HKCC"
WSTR f_pfx, "%s%s\"
WSTR f_vn, "%s%s"
WSTR s_keytag, "[키]"
WSTR s_defname, "(기본값)"
WSTR f_sz, "SZ: %s"
WSTR f_esz, "EXPAND_SZ: %s"
WSTR f_dw, "DWORD: 0x%08X (%u)"
WSTR f_qw, "QWORD: 0x%016llX"
WSTR f_tyn, "TYPE%u: "
WSTR s_bin, "BINARY: "
WSTR s_msz, "MULTI_SZ: "
WSTR s_bar, " | "
WSTR f_b2, "%02X "
WSTR f_more, "... (%u바이트)"
WSTR f_big, "(데이터 %u바이트, 읽지 않음)"

align 8
reg_names: dq rn0, rn1, rn2, rn3, rn4, rn5, rn6, rn7, rn8, rn9
reg_vals:  dq 0xFFFFFFFF80000000, 0xFFFFFFFF80000001, 0xFFFFFFFF80000002, 0xFFFFFFFF80000003, 0xFFFFFFFF80000005

; reg list: ptr, n, cap ; entry = name, value
%define RL_PTR 0
%define RL_N   8
%define RL_CAP 16
%define RL_SIZE 24

section .text

; rl_add(list, name, value)
rl_add:
    PROLOG 64
    mov rbx, rcx
    mov r12, rdx
    mov r13, r8
    mov rax, [rbx+RL_N]
    cmp rax, 400000
    jae .done
    cmp rax, [rbx+RL_CAP]
    jb .room
    lea r14, [rax*2+256]
    mov [rbx+RL_CAP], r14
    shl r14, 4
    invoke realloc, [rbx+RL_PTR], r14
    mov [rbx+RL_PTR], rax
.room:
    mov r14, [rbx+RL_N]
    shl r14, 4
    add r14, [rbx+RL_PTR]
    inc qword [rbx+RL_N]
    invoke str_dup, r12
    mov [r14], rax
    invoke str_dup, r13
    mov [r14+8], rax
.done:
    EPILOG 64

; rl_free(list)
rl_free:
    PROLOG 64
    mov rbx, rcx
    xor esi, esi
.l:
    cmp rsi, [rbx+RL_N]
    jae .d
    mov rdi, rsi
    shl rdi, 4
    add rdi, [rbx+RL_PTR]
    invoke free, [rdi]
    invoke free, [rdi+8]
    inc rsi
    jmp .l
.d:
    invoke free, [rbx+RL_PTR]
    EPILOG 64

; qsort comparator: entries by name, case-insensitive
rl_cmp:
    sub rsp, 40
    mov rcx, [rcx]
    mov rdx, [rdx]
    call _wcsicmp
    add rsp, 40
    ret

; reg_fmt(type, data, len, out): human readable value text (out holds 1100 wchar)
reg_fmt:
    PROLOG 128
    mov r12d, ecx
    mov r13, rdx
    mov r14d, r8d
    mov r15, r9
    mov word [r15], 0
    cmp r12d, 1
    je .sz
    cmp r12d, 2
    je .esz
    cmp r12d, 4
    je .dw
    cmp r12d, 7
    je .msz
    cmp r12d, 11
    je .qw
    jmp .bin
.sz:
    lea rbx, [f_sz]
    jmp .str
.esz:
    lea rbx, [f_esz]
.str:
    mov eax, r14d
    shr eax, 1
    mov word [r13+rax*2], 0
    invoke _snwprintf, r15, 1090, rbx, r13
    mov word [r15+2180], 0
    EPILOG 128
.dw:
    cmp r14d, 4
    jb .bin
    mov eax, [r13]
    invoke _snwprintf, r15, 1090, &f_dw, rax, rax
    EPILOG 128
.qw:
    cmp r14d, 8
    jb .bin
    invoke _snwprintf, r15, 1090, &f_qw, [r13]
    EPILOG 128
.msz:
    invoke wcscpy, r15, &s_msz
    mov r14d, r14d
    shr r14d, 1
    xor ebx, ebx                      ; chars consumed
.ml:
    cmp ebx, r14d
    jae .mdone
    lea rsi, [r13+rbx*2]
    cmp word [rsi], 0
    je .mdone
    invoke wcslen, rsi
    mov rdi, rax
    lea ebp, [rbx+rdi+1]
    mov ebx, ebp
    invoke wcslen, r15
    add rax, rdi
    cmp rax, 1000
    ja .mdone
    invoke wcscat, r15, rsi
    invoke wcscat, r15, &s_bar
    jmp .ml
.mdone:
    EPILOG 128
.bin:
    cmp r12d, 3
    jne .othertype
    invoke wcscpy, r15, &s_bin
    jmp .bytes
.othertype:
    invoke _snwprintf, r15, 30, &f_tyn, r12
    mov word [r15+58], 0
.bytes:
    invoke wcslen, r15
    lea rbx, [r15+rax*2]              ; write cursor
    xor esi, esi
.bl:
    cmp esi, r14d
    jae .bdone
    cmp esi, 48
    jae .bmore
    movzx eax, byte [r13+rsi]
    invoke _snwprintf, rbx, 4, &f_b2, rax
    add rbx, 6
    inc esi
    jmp .bl
.bmore:
    invoke _snwprintf, rbx, 30, &f_more, r14
.bdone:
    EPILOG 128

; reg_walk(hkey, prefix, list, depth)
%define W_NAME  96                     ; 520 wchar
%define W_FULL  1140                   ; 1100 wchar
%define W_TEXT  3340                   ; 1100 wchar
%define W_DATA  5540                   ; 4104 bytes
%define W_NL    9660
%define W_DL    9664
%define W_TY    9668
%define W_HSUB  9672
reg_walk:
    PROLOG 9744
    mov r12, rcx
    mov r13, rdx
    mov r14, r8
    mov r15d, r9d
    xor ebx, ebx
.vl:
    mov dword [rsp+W_NL], 520
    mov dword [rsp+W_DL], 4096
    mov dword [rsp+W_TY], 0
    invoke RegEnumValueW, r12, rbx, &rsp+W_NAME, &rsp+W_NL, 0, &rsp+W_TY, &rsp+W_DATA, &rsp+W_DL
    cmp eax, 259
    je .vdone
    cmp eax, 234
    je .big
    test eax, eax
    jnz .vdone
    mov esi, [rsp+W_TY]
    mov r8d, [rsp+W_DL]
    invoke reg_fmt, rsi, &rsp+W_DATA, r8, &rsp+W_TEXT
    jmp .have
.big:
    mov eax, [rsp+W_DL]
    invoke _snwprintf, &rsp+W_TEXT, 1090, &f_big, rax
.have:
    lea rdi, [rsp+W_NAME]
    cmp word [rdi], 0
    jne .nm
    lea rdi, [s_defname]
.nm:
    invoke _snwprintf, &rsp+W_FULL, 1090, &f_vn, r13, rdi
    mov word [rsp+W_FULL+2180], 0
    invoke rl_add, r14, &rsp+W_FULL, &rsp+W_TEXT
    inc ebx
    jmp .vl
.vdone:
    xor ebx, ebx
.kl:
    mov dword [rsp+W_NL], 520
    invoke RegEnumKeyExW, r12, rbx, &rsp+W_NAME, &rsp+W_NL, 0, 0, 0, 0
    test eax, eax
    jnz .kdone
    invoke _snwprintf, &rsp+W_FULL, 1090, &f_pfx, r13, &rsp+W_NAME
    mov word [rsp+W_FULL+2180], 0
    invoke rl_add, r14, &rsp+W_FULL, &s_keytag
    cmp r15d, 24
    jae .knext
    invoke RegOpenKeyExW, r12, &rsp+W_NAME, 0, 0x20019, &rsp+W_HSUB
    test eax, eax
    jnz .knext
    lea edi, [r15+1]
    invoke reg_walk, [rsp+W_HSUB], &rsp+W_FULL, r14, rdi
    invoke RegCloseKey, [rsp+W_HSUB]
.knext:
    inc ebx
    jmp .kl
.kdone:
    EPILOG 9744

; reg_collect(path, list) -> eax 1 ok
reg_collect:
    PROLOG 400
    mov r12, rcx
    mov r13, rdx
    invoke wcschr, r12, 0x5C
    mov r14, rax
    test rax, rax
    jz .whole
    mov rcx, rax
    sub rcx, r12
    shr rcx, 1
    jmp .have
.whole:
    invoke wcslen, r12
    mov rcx, rax
.have:
    cmp rcx, 40
    jae .fail
    mov r15, rcx
    invoke wcsncpy, &rsp+96, r12, r15
    mov word [rsp+96+r15*2], 0
    xor ebx, ebx
.find:
    cmp ebx, 10
    jae .fail
    lea rax, [reg_names]
    invoke _wcsicmp, &rsp+96, [rax+rbx*8]
    test eax, eax
    jz .found
    inc ebx
    jmp .find
.found:
    shr ebx, 1
    lea rax, [reg_vals]
    mov rbx, [rax+rbx*8]
    lea rsi, [s_empty]
    test r14, r14
    jz .open
    lea rsi, [r14+2]
.open:
    invoke RegOpenKeyExW, rbx, rsi, 0, 0x20019, &rsp+200
    test eax, eax
    jnz .fail
    invoke reg_walk, [rsp+200], &s_empty, r13, 0
    invoke RegCloseKey, [rsp+200]
    mov eax, 1
    EPILOG 400
.fail:
    xor eax, eax
    EPILOG 400

; pr_reg(P, pathA, pathB) -> eax 1 ok
pr_reg:
    PROLOG 160
    mov rbx, rcx
    mov r12, rdx
    mov r13, r8
    lea r14, [rsp+96]                ; list A
    lea r15, [rsp+96+RL_SIZE]        ; list B
    xor eax, eax
    mov [r14], rax
    mov [r14+8], rax
    mov [r14+16], rax
    mov [r15], rax
    mov [r15+8], rax
    mov [r15+16], rax
    invoke reg_collect, r12, r14
    test eax, eax
    jz .failA
    invoke reg_collect, r13, r15
    test eax, eax
    jz .fail
    invoke qsort, [r14], [r14+8], 16, &rl_cmp
    invoke qsort, [r15], [r15+8], 16, &rl_cmp
    xor esi, esi                      ; i
    xor edi, edi                      ; j
.m:
    mov rax, [r14+8]
    mov rcx, [r15+8]
    cmp rsi, rax
    jae .aend
    cmp rdi, rcx
    jae .onlya
    mov rax, rsi
    shl rax, 4
    add rax, [r14]
    mov rdx, rdi
    shl rdx, 4
    add rdx, [r15]
    mov rbp, rax                      ; entry A
    mov r12, rdx                      ; entry B
    invoke _wcsicmp, [rbp], [r12]
    test eax, eax
    js .onlya
    jg .onlyb
    invoke pr_add, rbx, [rbp], [rbp+8], [r12+8]
    inc rsi
    inc rdi
    jmp .m
.aend:
    cmp rdi, rcx
    jae .done
.onlyb:
    mov r12, rdi
    shl r12, 4
    add r12, [r15]
    invoke pr_add, rbx, [r12], 0, [r12+8]
    inc rdi
    jmp .m
.onlya:
    mov rbp, rsi
    shl rbp, 4
    add rbp, [r14]
    invoke pr_add, rbx, [rbp], [rbp+8], 0
    inc rsi
    jmp .m
.done:
    invoke rl_free, r14
    invoke rl_free, r15
    mov eax, 1
    EPILOG 160
.fail:
    invoke rl_free, r15
.failA:
    invoke rl_free, r14
    xor eax, eax
    EPILOG 160
