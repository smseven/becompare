; inflate.asm - DEFLATE decoder (port of the classic "puff" algorithm) + IEEE CRC-32
%include "inc/macros.inc"
%include "inc/win.inc"

extern memcpy, memset

global inflate_buf, crc32_update, crc32_init

; ---- decoder state (lives in the caller's frame; rsi points at it everywhere)
%define IS_OUT    0
%define IS_OUTLEN 8
%define IS_OUTCNT 16
%define IS_IN     24
%define IS_INLEN  32
%define IS_INCNT  40
%define IS_BITBUF 48
%define IS_BITCNT 56
%define IS_ERR    64
%define IS_SIZE   72

; ---- Huffman table: count dd[16], symbol dd[288]
%define H_COUNT   0
%define H_SYM     64
%define H_SIZE    (64+288*4)

section .rdata
align 4
lbase: dd 3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258
lext:  dd 0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0
dbase: dd 1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577
dext:  dd 0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13
order: dd 16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15

section .bss
alignb 4
crc_table: resd 256
crc_ready: resd 1

section .text

; ---------------------------------------------------------------- CRC-32 (IEEE 802.3, reflected 0xEDB88320)
crc32_init:
    cmp dword [crc_ready], 0
    jne .d
    xor ecx, ecx
.n:
    mov eax, ecx
    mov r8d, 8
.b:
    shr eax, 1
    jnc .nx
    xor eax, 0xEDB88320
.nx:
    dec r8d
    jnz .b
    lea rdx, [crc_table]
    mov [rdx+rcx*4], eax
    inc ecx
    cmp ecx, 256
    jb .n
    mov dword [crc_ready], 1
.d:
    ret

; crc32_update(ecx = running crc (start with 0), rdx = data, r8 = length) -> eax
crc32_update:
    PROLOG 64
    mov ebx, ecx
    mov rsi, rdx
    mov rdi, r8
    call crc32_init
    lea r9, [crc_table]
    not ebx
    xor ecx, ecx
.l:
    cmp rcx, rdi
    jae .d
    movzx eax, byte [rsi+rcx]
    xor al, bl
    movzx eax, al
    shr ebx, 8
    xor ebx, [r9+rax*4]
    inc rcx
    jmp .l
.d:
    not ebx
    mov eax, ebx
    EPILOG 64

; ---------------------------------------------------------------- bit reader (rsi = state)
; inf_bits(edx = count) -> eax
inf_bits:
    mov r8, [rsi+IS_BITBUF]
    mov r9d, [rsi+IS_BITCNT]
.n:
    cmp r9d, edx
    jae .h
    mov rax, [rsi+IS_INCNT]
    cmp rax, [rsi+IS_INLEN]
    jae .eof
    mov r10, [rsi+IS_IN]
    movzx r10d, byte [r10+rax]
    inc rax
    mov [rsi+IS_INCNT], rax
    mov ecx, r9d
    shl r10, cl
    or r8, r10
    add r9d, 8
    jmp .n
.h:
    mov ecx, edx
    mov eax, 1
    shl eax, cl
    dec eax
    and eax, r8d
    shr r8, cl
    sub r9d, edx
    mov [rsi+IS_BITBUF], r8
    mov [rsi+IS_BITCNT], r9d
    ret
.eof:
    mov dword [rsi+IS_ERR], 1
    xor eax, eax
    ret

; inf_decode(rdi = huffman table) -> eax symbol or -1
inf_decode:
    PROLOG 64
    xor r12d, r12d                   ; code
    xor r13d, r13d                   ; first
    xor r14d, r14d                   ; index
    mov r15d, 1                      ; len
.l:
    mov edx, 1
    call inf_bits
    cmp dword [rsi+IS_ERR], 0
    jne .bad
    or r12d, eax
    mov eax, [rdi+H_COUNT+r15*4]
    mov ecx, r12d
    sub ecx, eax
    cmp ecx, r13d
    jl .found
    add r14d, eax
    add r13d, eax
    shl r13d, 1
    shl r12d, 1
    inc r15d
    cmp r15d, 15
    jbe .l
.bad:
    mov eax, -1
    EPILOG 64
.found:
    mov eax, r12d
    sub eax, r13d
    add eax, r14d
    mov eax, [rdi+H_SYM+rax*4]
    EPILOG 64

; inf_construct(rdi = table, rdx = lengths (dd[]), r8d = n) -> eax (0 complete, >0 incomplete, <0 over-subscribed)
inf_construct:
    PROLOG 224
    mov r12, rdx
    mov r13d, r8d
    xor ecx, ecx
.z:
    mov dword [rdi+H_COUNT+rcx*4], 0
    inc ecx
    cmp ecx, 16
    jb .z
    xor ecx, ecx
.c:
    cmp ecx, r13d
    jae .cd
    mov eax, [r12+rcx*4]
    inc dword [rdi+H_COUNT+rax*4]
    inc ecx
    jmp .c
.cd:
    cmp [rdi+H_COUNT], r13d
    jne .go
    xor eax, eax
    EPILOG 224
.go:
    mov eax, 1                       ; left
    mov ecx, 1
.lft:
    cmp ecx, 15
    ja .offs
    shl eax, 1
    sub eax, [rdi+H_COUNT+rcx*4]
    js .ret
    inc ecx
    jmp .lft
.offs:
    mov [rsp+96], eax                ; left
    mov dword [rsp+128+4], 0         ; offs[1] = 0   (offs[len] at [rsp+128+len*4])
    mov ecx, 1
.of:
    cmp ecx, 15
    jae .fill
    mov eax, [rsp+128+rcx*4]
    add eax, [rdi+H_COUNT+rcx*4]
    mov [rsp+128+rcx*4+4], eax
    inc ecx
    jmp .of
.fill:
    xor ecx, ecx
.s:
    cmp ecx, r13d
    jae .done
    mov eax, [r12+rcx*4]
    test eax, eax
    jz .sn
    mov edx, [rsp+128+rax*4]
    mov [rdi+H_SYM+rdx*4], ecx
    inc edx
    mov [rsp+128+rax*4], edx
.sn:
    inc ecx
    jmp .s
.done:
    mov eax, [rsp+96]
.ret:
    EPILOG 224

; ---------------------------------------------------------------- blocks
; inf_codes(rdi = length table, rdx = distance table) -> eax 0 ok
inf_codes:
    PROLOG 64
    mov r12, rdi
    mov r13, rdx
.loop:
    mov rdi, r12
    call inf_decode
    test eax, eax
    js .err
    cmp eax, 256
    jb .lit
    je .ok
    sub eax, 257
    cmp eax, 29
    jae .err
    mov ebx, eax
    lea rcx, [lext]
    mov edx, [rcx+rbx*4]
    call inf_bits
    lea rcx, [lbase]
    add eax, [rcx+rbx*4]
    mov r14d, eax                    ; length
    mov rdi, r13
    call inf_decode
    test eax, eax
    js .err
    cmp eax, 30
    jae .err
    mov ebx, eax
    lea rcx, [dext]
    mov edx, [rcx+rbx*4]
    call inf_bits
    lea rcx, [dbase]
    add eax, [rcx+rbx*4]
    mov r15d, eax                    ; distance
    mov rax, [rsi+IS_OUTCNT]
    cmp r15, rax
    ja .err
    lea rcx, [rax+r14]
    cmp rcx, [rsi+IS_OUTLEN]
    ja .err
    mov rdx, [rsi+IS_OUT]
    mov r8, rax
    sub r8, r15                      ; source index
    xor r9d, r9d
.cp:
    cmp r9d, r14d
    jae .cpd
    mov cl, [rdx+r8]
    mov [rdx+rax], cl
    inc r8
    inc rax
    inc r9d
    jmp .cp
.cpd:
    mov [rsi+IS_OUTCNT], rax
    jmp .loop
.lit:
    mov rcx, [rsi+IS_OUTCNT]
    cmp rcx, [rsi+IS_OUTLEN]
    jae .err
    mov rdx, [rsi+IS_OUT]
    mov [rdx+rcx], al
    inc rcx
    mov [rsi+IS_OUTCNT], rcx
    jmp .loop
.ok:
    xor eax, eax
    EPILOG 64
.err:
    mov eax, 1
    EPILOG 64

inf_stored:
    PROLOG 64
    mov qword [rsi+IS_BITBUF], 0
    mov dword [rsi+IS_BITCNT], 0
    mov rax, [rsi+IS_INCNT]
    lea rcx, [rax+4]
    cmp rcx, [rsi+IS_INLEN]
    ja .err
    mov rdx, [rsi+IS_IN]
    movzx r8d, word [rdx+rax]        ; len
    movzx r9d, word [rdx+rax+2]      ; nlen
    not r9d
    and r9d, 0xFFFF
    cmp r8d, r9d
    jne .err
    mov [rsi+IS_INCNT], rcx
    lea r10, [rcx+r8]
    cmp r10, [rsi+IS_INLEN]
    ja .err
    mov r11, [rsi+IS_OUTCNT]
    lea r10, [r11+r8]
    cmp r10, [rsi+IS_OUTLEN]
    ja .err
    mov rbx, r8
    mov rdi, [rsi+IS_OUT]
    add rdi, r11
    mov rdx, [rsi+IS_IN]
    add rdx, rcx
    invoke memcpy, rdi, rdx, rbx
    add [rsi+IS_INCNT], rbx
    add [rsi+IS_OUTCNT], rbx
    xor eax, eax
    EPILOG 64
.err:
    mov eax, 1
    EPILOG 64

; inf_fixed() -> eax 0 ok
inf_fixed:
    PROLOG 3840
    lea r12, [rsp+96]                ; length table
    lea r13, [rsp+96+H_SIZE]         ; distance table
    lea r14, [rsp+96+2*H_SIZE]       ; lengths dd[320]
    xor ecx, ecx
.a:
    cmp ecx, 144
    jae .b0
    mov dword [r14+rcx*4], 8
    inc ecx
    jmp .a
.b0:
    cmp ecx, 256
    jae .c0
    mov dword [r14+rcx*4], 9
    inc ecx
    jmp .b0
.c0:
    cmp ecx, 280
    jae .d0
    mov dword [r14+rcx*4], 7
    inc ecx
    jmp .c0
.d0:
    cmp ecx, 288
    jae .e0
    mov dword [r14+rcx*4], 8
    inc ecx
    jmp .d0
.e0:
    mov rdi, r12
    mov rdx, r14
    mov r8d, 288
    call inf_construct
    xor ecx, ecx
.f:
    cmp ecx, 30
    jae .g
    mov dword [r14+rcx*4], 5
    inc ecx
    jmp .f
.g:
    mov rdi, r13
    mov rdx, r14
    mov r8d, 30
    call inf_construct
    mov rdi, r12
    mov rdx, r13
    call inf_codes
    EPILOG 3840

; inf_dynamic() -> eax 0 ok
inf_dynamic:
    PROLOG 3840
    lea r12, [rsp+96]
    lea r13, [rsp+96+H_SIZE]
    lea r14, [rsp+96+2*H_SIZE]
    mov edx, 5
    call inf_bits
    lea r15d, [rax+257]              ; nlen
    mov edx, 5
    call inf_bits
    lea ebp, [rax+1]                 ; ndist
    mov edx, 4
    call inf_bits
    lea ebx, [rax+4]                 ; ncode
    cmp r15d, 286
    ja .err
    cmp ebp, 30
    ja .err
    xor ecx, ecx
.z:
    mov dword [r14+rcx*4], 0
    inc ecx
    cmp ecx, 320
    jb .z
    xor edi, edi
.cl:
    cmp edi, ebx
    jae .cld
    mov edx, 3
    call inf_bits
    lea rcx, [order]
    mov ecx, [rcx+rdi*4]
    mov [r14+rcx*4], eax
    inc edi
    jmp .cl
.cld:
    mov rdi, r12
    mov rdx, r14
    mov r8d, 19
    call inf_construct
    test eax, eax
    jnz .err
    xor ebx, ebx                     ; idx
    lea eax, [r15+rbp]
    mov [rsp+80], eax                ; total
.ld:
    mov eax, [rsp+80]
    cmp ebx, eax
    jae .built
    mov rdi, r12
    call inf_decode
    test eax, eax
    js .err
    cmp eax, 16
    jae .rep
    mov [r14+rbx*4], eax
    inc ebx
    jmp .ld
.rep:
    xor r11d, r11d                     ; value to repeat
    cmp eax, 16
    jne .r17
    test ebx, ebx
    jz .err
    mov r11d, [r14+rbx*4-4]
    mov edx, 2
    call inf_bits
    add eax, 3
    jmp .go
.r17:
    cmp eax, 17
    jne .r18
    mov edx, 3
    call inf_bits
    add eax, 3
    jmp .go
.r18:
    mov edx, 7
    call inf_bits
    add eax, 11
.go:
    lea ecx, [rbx+rax]
    cmp ecx, [rsp+80]
    ja .err
.fl:
    test eax, eax
    jz .ld
    mov [r14+rbx*4], r11d
    inc ebx
    dec eax
    jmp .fl
.built:
    cmp dword [r14+256*4], 0
    je .err
    mov rdi, r12
    mov rdx, r14
    mov r8d, r15d
    call inf_construct
    test eax, eax
    js .err
    mov rdi, r13
    lea rdx, [r14+r15*4]
    mov r8d, ebp
    call inf_construct
    test eax, eax
    js .err
    mov rdi, r12
    mov rdx, r13
    call inf_codes
    EPILOG 3840
.err:
    mov eax, 1
    EPILOG 3840

; inflate_buf(src, srclen, dst, dstlen) -> eax 1 on success, rdx = bytes produced
inflate_buf:
    PROLOG 160
    mov [rsp+96+IS_IN], rcx
    mov [rsp+96+IS_INLEN], rdx
    mov [rsp+96+IS_OUT], r8
    mov [rsp+96+IS_OUTLEN], r9
    xor eax, eax
    mov [rsp+96+IS_OUTCNT], rax
    mov [rsp+96+IS_INCNT], rax
    mov [rsp+96+IS_BITBUF], rax
    mov [rsp+96+IS_BITCNT], eax
    mov [rsp+96+IS_ERR], eax
    lea rsi, [rsp+96]
.blk:
    mov edx, 1
    call inf_bits
    mov ebx, eax                     ; last
    mov edx, 2
    call inf_bits
    cmp dword [rsi+IS_ERR], 0
    jne .fail
    test eax, eax
    jz .stored
    cmp eax, 1
    je .fixed
    cmp eax, 2
    je .dyn
    jmp .fail
.stored:
    call inf_stored
    jmp .res
.fixed:
    call inf_fixed
    jmp .res
.dyn:
    call inf_dynamic
.res:
    test eax, eax
    jnz .fail
    cmp dword [rsi+IS_ERR], 0
    jne .fail
    test ebx, ebx
    jz .blk
    mov rdx, [rsi+IS_OUTCNT]
    mov eax, 1
    EPILOG 160
.fail:
    xor eax, eax
    xor edx, edx
    EPILOG 160
