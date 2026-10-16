; table_date.inc - TB-02 date aware tolerance: "yyyy-mm-dd[ hh:mm[:ss]]" cells compare within the tolerance (seconds)

; dp_num(rcx = p) -> rax value, rdx = new p, r8 = number of digits
dp_num:
    xor eax, eax
    xor r8d, r8d
.l:
    movzx edx, word [rcx]
    sub edx, '0'
    cmp edx, 9
    ja .d
    imul eax, eax, 10
    add eax, edx
    inc r8d
    add rcx, 2
    cmp r8d, 8
    jb .l
.d:
    mov rdx, rcx
    ret

; date_parse(wchar*) -> rax = seconds since 1970 (or -1 when the text is not a date)
date_parse:
    PROLOG 64
    mov rsi, rcx
.sp:
    cmp word [rsi], ' '
    jne .y
    add rsi, 2
    jmp .sp
.y:
    mov rcx, rsi
    call dp_num
    cmp r8d, 4
    jne .bad
    mov r12d, eax                     ; year
    mov rsi, rdx
    movzx eax, word [rsi]
    cmp eax, '-'
    je .m
    cmp eax, '/'
    je .m
    cmp eax, '.'
    jne .bad
.m:
    mov ebp, eax                      ; separator
    lea rcx, [rsi+2]
    call dp_num
    test r8d, r8d
    jz .bad
    cmp r8d, 2
    ja .bad
    mov r13d, eax                     ; month
    mov rsi, rdx
    cmp bp, [rsi]
    jne .bad
    lea rcx, [rsi+2]
    call dp_num
    test r8d, r8d
    jz .bad
    cmp r8d, 2
    ja .bad
    mov r14d, eax                     ; day
    mov rsi, rdx
    xor r15d, r15d                    ; seconds of the day
    movzx eax, word [rsi]
    test eax, eax
    jz .calc
    cmp eax, ' '
    je .t
    cmp eax, 'T'
    jne .bad
.t:
.ts:
    add rsi, 2
    cmp word [rsi], ' '
    je .ts
    mov rcx, rsi
    call dp_num
    test r8d, r8d
    jz .trail
    cmp r8d, 2
    ja .bad
    cmp eax, 23
    ja .bad
    imul r15d, eax, 3600
    mov rsi, rdx
    cmp word [rsi], ':'
    jne .bad
    lea rcx, [rsi+2]
    call dp_num
    test r8d, r8d
    jz .bad
    cmp eax, 59
    ja .bad
    imul eax, eax, 60
    add r15d, eax
    mov rsi, rdx
    cmp word [rsi], ':'
    jne .trail
    lea rcx, [rsi+2]
    call dp_num
    test r8d, r8d
    jz .bad
    cmp eax, 59
    ja .bad
    add r15d, eax
    mov rsi, rdx
.trail:
    cmp word [rsi], ' '
    jne .endchk
    add rsi, 2
    jmp .trail
.endchk:
    cmp word [rsi], 0
    jne .bad
.calc:
    cmp r13d, 1
    jb .bad
    cmp r13d, 12
    ja .bad
    cmp r14d, 1
    jb .bad
    cmp r14d, 31
    ja .bad
    ; days from civil
    mov eax, r12d
    cmp r13d, 2
    jg .ny
    dec eax
.ny:
    mov edi, eax                      ; y (shifted)
    mov eax, edi
    cdq
    mov ecx, 400
    idiv ecx                          ; eax = era (y is positive here)
    mov esi, eax                      ; era
    imul eax, esi, 400
    mov ecx, edi
    sub ecx, eax                      ; yoe
    mov ebx, ecx                      ; keep yoe
    ; doy = (153*(m + (m>2 ? -3 : 9)) + 2)/5 + d - 1
    mov eax, r13d
    cmp eax, 2
    jg .m3
    add eax, 9
    jmp .m4
.m3:
    sub eax, 3
.m4:
    imul eax, eax, 153
    add eax, 2
    cdq
    mov ecx, 5
    idiv ecx
    add eax, r14d
    dec eax                           ; doy
    mov ecx, eax
    ; doe = yoe*365 + yoe/4 - yoe/100 + doy
    imul eax, ebx, 365
    add eax, ecx
    mov ecx, ebx
    shr ecx, 2
    add eax, ecx
    mov ecx, ebx
    push rax
    mov eax, ecx
    xor edx, edx
    mov ecx, 100
    div ecx
    mov ecx, eax
    pop rax
    sub eax, ecx                      ; doe
    imul esi, esi, 146097
    add eax, esi
    sub eax, 719468                   ; days since 1970
    movsxd rax, eax
    imul rax, rax, 86400
    movsxd rcx, r15d
    add rax, rcx
    EPILOG 64
.bad:
    mov rax, -1
    EPILOG 64

; date_eq(a, b, tb) -> eax 1 when both are dates no further apart than the tolerance (seconds)
date_eq:
    PROLOG 64
    mov rsi, rcx
    mov rdi, rdx
    mov rbx, r8
    mov rcx, rsi
    call date_parse
    mov r12, rax
    cmp rax, -1
    je .no
    mov rcx, rdi
    call date_parse
    cmp rax, -1
    je .no
    sub rax, r12
    jns .abs
    neg rax
.abs:
    cvtsi2sd xmm1, rax
    ucomisd xmm1, [rbx+TB_TOL]
    jp .no
    ja .no
    mov eax, 1
    EPILOG 64
.no:
    xor eax, eax
    EPILOG 64
