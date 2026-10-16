; folder_rep.inc - FC-05 per-file detail reports linked from the folder HTML report

extern text_load, lines_split, compare_lines, hunk_free

section .rdata
WSTR s_fr_head, `<!doctype html><html><head><meta charset="utf-8"><title>BeCompare 파일 비교</title><style>body{font-family:Consolas,'Segoe UI',monospace;font-size:13px;margin:16px}table{border-collapse:collapse;width:100%}td{padding:1px 6px;vertical-align:top;white-space:pre-wrap;word-break:break-all}td.n{color:#888;width:3.5em;text-align:right;white-space:nowrap}td.l{background:#ffdcdc;width:47%}td.r{background:#dcf5dc;width:47%}td.c{width:47%}tr.gap td{color:#888;text-align:center;background:#f2f2f2}</style></head><body><h3>`
WSTR s_fr_mid, `</h3><p>`
WSTR s_fr_tab, `</p><table>\n`
WSTR s_fr_foot, `</table></body></html>\n`
WSTR s_fr_tr, `<tr><td class="n">`
WSTR s_fr_tdl, `</td><td class="l">`
WSTR s_fr_tdr, `</td><td class="r">`
WSTR s_fr_tdc, `</td><td class="c">`
WSTR s_fr_tdn, `</td><td class="n">`
WSTR s_fr_end, `</td></tr>\n`
WSTR f_fr_gap, `<tr class="gap"><td colspan="4">… %u줄 생략 …</td></tr>\n`
WSTR f_fr_num, "%u"
WSTR s_fr_nodiff, `<tr class="gap"><td colspan="4">(차이가 없습니다)</td></tr>\n`

section .text

; fr_isbinary(path) -> eax 1 when the first 4 KB contain a NUL byte (or the file cannot be read)
fr_isbinary:
    PROLOG 4160
    mov rsi, rcx
    invoke CreateFileW, rsi, GENERIC_READ, 3, 0, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, 0
    cmp rax, -1
    je .bin
    mov rbx, rax
    mov dword [rsp+4112], 0
    invoke ReadFile, rbx, &rsp+96, 4000, &rsp+4112, 0
    invoke CloseHandle, rbx
    mov ecx, [rsp+4112]
    xor edx, edx
.l:
    cmp edx, ecx
    jae .text
    cmp byte [rsp+96+rdx], 0
    je .bin
    inc edx
    jmp .l
.text:
    xor eax, eax
    EPILOG 4160
.bin:
    mov eax, 1
    EPILOG 4160

; fr_row(ctx {sb*, LA*, LB*}, aidx, bidx, cls)  (aidx / bidx = -1: no line on that side; cls 1 = changed)
fr_row:
    PROLOG 192
    mov rbx, rcx
    movsxd r12, edx
    movsxd r13, r8d
    mov r14d, r9d
    mov r15, [rbx]
    invoke sb_append, r15, &s_fr_tr
    test r12, r12
    js .noa
    lea rax, [r12+1]
    invoke _snwprintf, &rsp+96, 16, &f_fr_num, rax
    invoke sb_append, r15, &rsp+96
.noa:
    lea rdx, [s_fr_tdc]
    cmp r14d, 1
    jne .ca
    test r12, r12
    js .ca
    lea rdx, [s_fr_tdl]
.ca:
    invoke sb_append, r15, rdx
    test r12, r12
    js .nta
    mov rax, [rbx+8]
    mov rax, [rax]
    mov rdx, [rax+r12*8]
    invoke sb_append_esc, r15, rdx
.nta:
    invoke sb_append, r15, &s_fr_tdn
    test r13, r13
    js .nob
    lea rax, [r13+1]
    invoke _snwprintf, &rsp+96, 16, &f_fr_num, rax
    invoke sb_append, r15, &rsp+96
.nob:
    lea rdx, [s_fr_tdc]
    cmp r14d, 1
    jne .cb
    test r13, r13
    js .cb
    lea rdx, [s_fr_tdr]
.cb:
    invoke sb_append, r15, rdx
    test r13, r13
    js .ntb
    mov rax, [rbx+16]
    mov rax, [rax]
    mov rdx, [rax+r13*8]
    invoke sb_append_esc, r15, rdx
.ntb:
    invoke sb_append, r15, &s_fr_end
    EPILOG 192

%define FR_TA   96                   ; TXT (32)
%define FR_TB   128
%define FR_LA   160                  ; LINES (16)
%define FR_LB   176
%define FR_HV   192                  ; vec (24)
%define FR_SB   224                  ; sb (24)
%define FR_CTX  256                  ; {sb*, LA*, LB*}
%define FR_BUF  288                  ; wchar[40]

; fold_filereport(pathA, pathB, out path) -> eax 1 when written
fold_filereport:
    PROLOG 528
    mov r12, rcx
    mov r13, rdx
    mov r14, r8
    invoke fr_isbinary, r12
    test eax, eax
    jnz .fail
    invoke fr_isbinary, r13
    test eax, eax
    jnz .fail
    invoke memset, &rsp+FR_TA, 0, 64
    invoke text_load, r12, &rsp+FR_TA
    test eax, eax
    jz .fail
    invoke text_load, r13, &rsp+FR_TB
    test eax, eax
    jz .fail
    invoke lines_split, [rsp+FR_TA], [rsp+FR_TA+8], &rsp+FR_LA
    invoke lines_split, [rsp+FR_TB], [rsp+FR_TB+8], &rsp+FR_LB
    invoke memset, &rsp+FR_HV, 0, 24
    invoke compare_lines, &rsp+FR_LA, &rsp+FR_LB, 0, &s_empty, &rsp+FR_HV
    lea rax, [rsp+FR_SB]
    mov [rsp+FR_CTX], rax
    lea rax, [rsp+FR_LA]
    mov [rsp+FR_CTX+8], rax
    lea rax, [rsp+FR_LB]
    mov [rsp+FR_CTX+16], rax
    invoke sb_init, &rsp+FR_SB
    invoke sb_append, &rsp+FR_SB, &s_fr_head
    invoke sb_append_esc, &rsp+FR_SB, r12
    invoke sb_append, &rsp+FR_SB, &s_fr_mid
    invoke sb_append_esc, &rsp+FR_SB, r13
    invoke sb_append, &rsp+FR_SB, &s_fr_tab
    mov r15, [rsp+FR_HV]              ; hunk array
    mov rbp, [rsp+FR_HV+8]            ; count
    xor ebx, ebx
    xor edi, edi                      ; rows written
.h:
    cmp rbx, rbp
    jae .hd
    lea rax, [rbx+rbx*2]
    shl rax, 3
    lea rsi, [r15+rax]                ; hunk
    cmp dword [rsi], 0
    jne .chg
    ; equal run: only the lines touching a change are shown
    xor r8d, r8d                      ; previous hunk is a change
    test rbx, rbx
    jz .np
    cmp dword [rsi-24], 0
    je .np
    mov r8d, 1
.np:
    xor r9d, r9d                      ; next hunk is a change
    lea rax, [rbx+1]
    cmp rax, rbp
    jae .nn
    cmp dword [rsi+24], 0
    je .nn
    mov r9d, 1
.nn:
    mov r10d, [rsi+8]                 ; length
    xor r11d, r11d                    ; lines shown at the start
    test r8d, r8d
    jz .s1
    mov r11d, 2
    cmp r11d, r10d
    jbe .s1
    mov r11d, r10d
.s1:
    xor eax, eax                      ; lines shown at the end
    test r9d, r9d
    jz .s2
    mov eax, 2
    mov ecx, r10d
    sub ecx, r11d
    cmp eax, ecx
    jbe .s2
    mov eax, ecx
.s2:
    mov [rsp+FR_BUF+208], r11d
    mov [rsp+FR_BUF+212], eax
    mov r12d, r10d                    ; reuse r12 (path A no longer needed)
    xor r13d, r13d                    ; k
.e1:
    cmp r13d, [rsp+FR_BUF+208]
    jae .e1d
    mov edx, [rsi+4]
    add edx, r13d
    mov r8d, [rsi+12]
    add r8d, r13d
    invoke fr_row, &rsp+FR_CTX, rdx, r8, 0
    inc edi
    inc r13d
    jmp .e1
.e1d:
    mov eax, r12d
    sub eax, [rsp+FR_BUF+208]
    sub eax, [rsp+FR_BUF+212]
    jbe .e2
    invoke _snwprintf, &rsp+FR_BUF, 100, &f_fr_gap, rax
    invoke sb_append, &rsp+FR_SB, &rsp+FR_BUF
.e2:
    mov r13d, r12d
    sub r13d, [rsp+FR_BUF+212]
.e2l:
    cmp r13d, r12d
    jae .nexth
    mov edx, [rsi+4]
    add edx, r13d
    mov r8d, [rsi+12]
    add r8d, r13d
    invoke fr_row, &rsp+FR_CTX, rdx, r8, 0
    inc edi
    inc r13d
    jmp .e2l
.chg:
    mov r12d, [rsi+8]
    cmp r12d, [rsi+16]
    jae .mx
    mov r12d, [rsi+16]
.mx:
    xor r13d, r13d
.cl:
    cmp r13d, r12d
    jae .nexth
    mov edx, -1
    cmp r13d, [rsi+8]
    jae .noa
    mov edx, [rsi+4]
    add edx, r13d
.noa:
    mov r8d, -1
    cmp r13d, [rsi+16]
    jae .nob
    mov r8d, [rsi+12]
    add r8d, r13d
.nob:
    invoke fr_row, &rsp+FR_CTX, rdx, r8, 1
    inc edi
    inc r13d
    jmp .cl
.nexth:
    inc rbx
    jmp .h
.hd:
    test edi, edi
    jnz .foot
    invoke sb_append, &rsp+FR_SB, &s_fr_nodiff
.foot:
    invoke sb_append, &rsp+FR_SB, &s_fr_foot
    invoke write_utf8, r14, [rsp+FR_SB], [rsp+FR_SB+8], 1
    mov ebx, eax
    invoke sb_free, &rsp+FR_SB
    invoke hunk_free, &rsp+FR_HV
    invoke free, [rsp+FR_TA]
    invoke free, [rsp+FR_TB]
    invoke free, [rsp+FR_LA]
    invoke free, [rsp+FR_LB]
    test ebx, ebx
    jz .writefail
    mov eax, 1
    EPILOG 528
.writefail:
    mov eax, -1
    EPILOG 528
.fail:
    xor eax, eax
    EPILOG 528
