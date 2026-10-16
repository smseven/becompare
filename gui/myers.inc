; myers.inc - Myers O(ND) diff, used when the LCS table would be too large (included by textlib.asm)
;   myers_ops(din, p, n1, m1) -> rax = ops (bytes, REVERSED order: 0 common, 1 delete A line, 2 insert B line), rdx = count
;   rax = 0 when the edit distance exceeds MY_DMAX

%define MY_DMAX 3000
%define MY_OFF  (MY_DMAX+1)

%define Y_DIN  96
%define Y_P    104
%define Y_N    112
%define Y_M    120
%define Y_V    128
%define Y_SNAP 136
%define Y_D    144
%define Y_OPS  152
%define Y_K    160
%define Y_PK   168

myers_ops:
    PROLOG 224
    mov [rsp+Y_DIN], rcx
    mov [rsp+Y_P], rdx
    mov [rsp+Y_N], r8
    mov [rsp+Y_M], r9
    mov ecx, (2*MY_DMAX+8)*4
    call malloc
    mov [rsp+Y_V], rax
    test rax, rax
    jz .fail0
    mov rcx, (MY_DMAX+1)*(MY_DMAX+1)*4+64
    call malloc
    mov [rsp+Y_SNAP], rax
    test rax, rax
    jz .fail1
    mov rbx, [rsp+Y_V]
    mov dword [rbx+(MY_OFF+1)*4], 0
    mov rsi, [rsp+Y_DIN]
    mov rdi, [rsp+Y_P]
    xor r12d, r12d                   ; d
.dloop:
    cmp r12d, MY_DMAX
    ja .fail2
    mov r13d, r12d
    neg r13d                         ; k = -d
.kloop:
    cmp r13d, r12d
    jg .dsave
    lea eax, [r13+MY_OFF]
    movsxd rcx, eax                  ; idx
    mov eax, r12d
    neg eax
    cmp r13d, eax
    je .down
    cmp r13d, r12d
    je .right
    mov eax, [rbx+rcx*4-4]
    cmp eax, [rbx+rcx*4+4]
    jl .down
.right:
    mov r14d, [rbx+rcx*4-4]
    inc r14d
    jmp .xy
.down:
    mov r14d, [rbx+rcx*4+4]
.xy:
    mov r15d, r14d
    sub r15d, r13d                   ; y = x - k
.snake:
    cmp r14d, [rsp+Y_N]
    jge .snaked
    cmp r15d, [rsp+Y_M]
    jge .snaked
    lea rdx, [rdi+r14]
    lea r8, [rdi+r15]
    invoke keq, rsi, rdx, r8
    test eax, eax
    jz .snaked
    inc r14d
    inc r15d
    jmp .snake
.snaked:
    lea eax, [r13+MY_OFF]
    movsxd rcx, eax
    mov [rbx+rcx*4], r14d
    cmp r14d, [rsp+Y_N]
    jl .nextk
    cmp r15d, [rsp+Y_M]
    jl .nextk
    mov [rsp+Y_D], r12
    jmp .found
.nextk:
    add r13d, 2
    jmp .kloop
.dsave:
    ; snapshot V[-d..d] at (d*d) dwords
    mov eax, r12d
    imul eax, eax
    mov rdx, [rsp+Y_SNAP]
    lea rdx, [rdx+rax*4]             ; snap + d*d
    mov r13d, r12d
    neg r13d
.sv:
    cmp r13d, r12d
    jg .svd
    lea eax, [r13+MY_OFF]
    movsxd rcx, eax
    mov eax, [rbx+rcx*4]
    lea ecx, [r13+r12]               ; k + d
    mov [rdx+rcx*4], eax
    inc r13d
    jmp .sv
.svd:
    inc r12d
    jmp .dloop
.found:
    ; ---- backtrack from (N, M)
    mov rax, [rsp+Y_N]
    add rax, [rsp+Y_M]
    lea rcx, [rax+16]
    call malloc
    mov [rsp+Y_OPS], rax
    test rax, rax
    jz .fail2
    mov r8, rax                      ; ops
    mov r14d, [rsp+Y_N]              ; x
    mov r15d, [rsp+Y_M]              ; y
    xor ebp, ebp                     ; op count
    mov r13, [rsp+Y_D]               ; dd
    mov rsi, [rsp+Y_SNAP]
.bk:
    test r13d, r13d
    jz .bk0
    mov eax, r14d
    sub eax, r15d
    mov [rsp+Y_K], rax               ; k (signed 32 in the low half)
    movsxd r9, dword [rsp+Y_K]       ; k
    lea eax, [r13-1]
    mov ecx, eax                     ; dd-1
    imul eax, eax                    ; base of the previous snapshot (dwords)
    lea rdx, [rsi+rax*4]             ; prev[]
    ; pk
    mov r10, r13
    neg r10
    cmp r9, r10
    je .pk_up
    cmp r9, r13
    je .pk_dn
    lea eax, [r9-1+rcx]              ; k-1 + (dd-1)
    mov r11d, [rdx+rax*4]
    lea eax, [r9+1+rcx]
    cmp r11d, [rdx+rax*4]
    jl .pk_up
.pk_dn:
    lea r10, [r9-1]                  ; pk = k-1  (right move: delete)
    xor r11d, r11d
    jmp .pk
.pk_up:
    lea r10, [r9+1]                  ; pk = k+1  (down move: insert)
    mov r11d, 1
.pk:
    lea eax, [r10+rcx]               ; pk + (dd-1)
    movsxd rax, eax
    mov eax, [rdx+rax*4]             ; px
    mov edx, eax
    sub edx, r10d                    ; py = px - pk
    ; target after the edit: insert -> (px, py+1) ; delete -> (px+1, py)
    mov r9d, eax                     ; mx = px
    lea ecx, [rdx+1]                 ; my = py+1
    test r11d, r11d
    jnz .tgt
    lea r9d, [rax+1]                 ; mx = px+1
    mov ecx, edx                     ; my = py
.tgt:
.sn:
    cmp r14d, r9d
    jle .snd
    cmp r15d, ecx
    jle .snd
    dec r14d
    dec r15d
    mov byte [r8+rbp], 0
    inc rbp
    jmp .sn
.snd:
    mov byte [r8+rbp], 1             ; delete
    test r11d, r11d
    jz .st
    mov byte [r8+rbp], 2             ; insert
.st:
    inc rbp
    mov r14d, eax                    ; x = px
    mov r15d, edx                    ; y = py
    dec r13d
    mov rsi, [rsp+Y_SNAP]
    jmp .bk
.bk0:
    test r14d, r14d
    jle .done
    test r15d, r15d
    jle .done
    dec r14d
    dec r15d
    mov byte [r8+rbp], 0
    inc rbp
    jmp .bk0
.done:
    invoke free, [rsp+Y_V]
    invoke free, [rsp+Y_SNAP]
    mov rax, [rsp+Y_OPS]
    mov rdx, rbp
    EPILOG 224
.fail2:
    invoke free, [rsp+Y_SNAP]
.fail1:
    invoke free, [rsp+Y_V]
.fail0:
    xor eax, eax
    xor edx, edx
    EPILOG 224
