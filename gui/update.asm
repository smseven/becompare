; update.asm - CU-03 update check: asks a release feed (GitHub releases API by default) for the newest tag
;   settings.ini  [Update]  Url=<feed url>   AutoCheck=1 (check once at start-up, result in the status bar)
%include "inc/macros.inc"
%include "inc/win.inc"

extern InternetOpenW, InternetOpenUrlW, InternetReadFile, InternetCloseHandle
extern MultiByteToWideChar, CreateThread, CloseHandle, GetPrivateProfileStringW, GetPrivateProfileIntW
extern SendMessageW, strstr, malloc, free, memset, _snwprintf
extern msgbox, g_ini, g_hstatus

global update_check, update_start

%define CUR_MAJ 1
%define CUR_MIN 0
%define CUR_PAT 0
%define UP_CAP  65536

section .rdata
WSTR s_up_agent, "BeCompare-update-check"
WSTR sec_upd, "Update"
WSTR k_upurl, "Url"
WSTR k_upauto, "AutoCheck"
WSTR d_upurl, "https://api.github.com/repos/smseven/demo/releases/latest"
WSTR s_up_hdr, `Accept: application/json\r\n`
j_tag: db '"tag_name"', 0
j_html: db '"html_url"', 0
WSTR f_up_new, `새 버전 %s 이(가) 있습니다.\n\n%s`
WSTR s_up_cur, "현재 최신 버전입니다. (v1.0.0)"
WSTR s_up_fail, "업데이트 확인에 실패했습니다. 네트워크 연결이나 설정의 [Update] Url 을 확인하세요."
WSTR s_up_none, "게시된 릴리스 정보를 찾지 못했습니다."
WSTR f_up_status, "새 버전 %s 사용 가능"

section .bss
alignb 8
g_up_status: resw 80

section .text

; up_fetch(buf, cap) -> eax bytes (0 = failure)
up_fetch:
    PROLOG 2320
    mov r12, rcx
    mov r13, rdx
    invoke GetPrivateProfileStringW, &sec_upd, &k_upurl, &d_upurl, &rsp+96, 1000, &g_ini
    invoke InternetOpenW, &s_up_agent, 0, 0, 0, 0
    mov rbx, rax
    test rax, rax
    jz .fail
    invoke InternetOpenUrlW, rbx, &rsp+96, &s_up_hdr, -1, 0x84000000, 0
    mov rdi, rax
    test rax, rax
    jz .closeb
    xor esi, esi
.rd:
    mov rax, r13
    sub rax, rsi
    dec rax
    jbe .rdone
    lea r14, [r12+rsi]
    mov r15, rax
    invoke InternetReadFile, rdi, r14, r15, &rsp+2300
    test eax, eax
    jz .rdone
    mov eax, [rsp+2300]
    test eax, eax
    jz .rdone
    add rsi, rax
    jmp .rd
.rdone:
    mov byte [r12+rsi], 0
    invoke InternetCloseHandle, rdi
    invoke InternetCloseHandle, rbx
    mov eax, esi
    EPILOG 2320
.closeb:
    invoke InternetCloseHandle, rbx
.fail:
    xor eax, eax
    EPILOG 2320

; up_json(buf, key, out (ansi, 256)) -> eax 1 when found
up_json:
    PROLOG 64
    mov rsi, rdx
    mov rdi, r8
    mov byte [rdi], 0
    invoke strstr, rcx, rsi
    test rax, rax
    jz .no
    mov rsi, rax
.c:
    movzx eax, byte [rsi]
    test eax, eax
    jz .no
    inc rsi
    cmp eax, ':'
    jne .c
.q:
    movzx eax, byte [rsi]
    test eax, eax
    jz .no
    inc rsi
    cmp eax, '"'
    jne .q
    xor ecx, ecx
.cp:
    movzx eax, byte [rsi+rcx]
    test eax, eax
    jz .no
    cmp eax, '"'
    je .done
    cmp ecx, 250
    jae .done
    mov [rdi+rcx], al
    inc ecx
    jmp .cp
.done:
    mov byte [rdi+rcx], 0
    mov eax, 1
    EPILOG 64
.no:
    xor eax, eax
    EPILOG 64

; up_newer(tag ansi) -> eax 1 when the tag is newer than this build
up_newer:
    PROLOG 64
    mov rsi, rcx
    xor ebx, ebx                      ; component index
    xor r12d, r12d                    ; packed major<<20 | minor<<10 | patch
.skip:
    movzx eax, byte [rsi]
    test eax, eax
    jz .cmp
    sub eax, '0'
    cmp eax, 9
    jbe .num
    inc rsi
    jmp .skip
.num:
    xor ecx, ecx
.d:
    movzx eax, byte [rsi]
    sub eax, '0'
    cmp eax, 9
    ja .store
    imul ecx, ecx, 10
    add ecx, eax
    inc rsi
    jmp .d
.store:
    cmp ecx, 1000
    jb .okv
    mov ecx, 1000
.okv:
    shl r12d, 10
    or r12d, ecx
    inc ebx
    cmp ebx, 3
    jb .skip
.cmp:
    ; pad missing components
.pad:
    cmp ebx, 3
    jae .go
    shl r12d, 10
    inc ebx
    jmp .pad
.go:
    xor eax, eax
    cmp r12d, (CUR_MAJ<<20)|(CUR_MIN<<10)|CUR_PAT
    seta al
    EPILOG 64

; update_check(owner, silent) -> eax 1 when a newer version exists
update_check:
    PROLOG 1600
    mov rbx, rcx
    mov r12d, edx
    mov ecx, UP_CAP
    call malloc
    mov r13, rax
    test rax, rax
    jz .out0
    invoke up_fetch, r13, UP_CAP
    test eax, eax
    jz .failed
    invoke up_json, r13, &j_tag, &rsp+96
    test eax, eax
    jz .none
    invoke up_newer, &rsp+96
    test eax, eax
    jz .current
    invoke up_json, r13, &j_html, &rsp+400
    invoke MultiByteToWideChar, 65001, 0, &rsp+96, -1, &rsp+700, 120
    invoke MultiByteToWideChar, 65001, 0, &rsp+400, -1, &rsp+1000, 250
    test r12d, r12d
    jnz .silentnew
    invoke _snwprintf, &rsp+96, 280, &f_up_new, &rsp+700, &rsp+1000
    invoke msgbox, rbx, &rsp+96, MB_OK|MB_ICONINFO
    jmp .new1
.silentnew:
    invoke _snwprintf, &g_up_status, 79, &f_up_status, &rsp+700
    invoke SendMessageW, [g_hstatus], SB_SETTEXTW, 0, &g_up_status
.new1:
    invoke free, r13
    mov eax, 1
    EPILOG 1600
.current:
    test r12d, r12d
    jnz .out
    invoke msgbox, rbx, &s_up_cur, MB_OK|MB_ICONINFO
    jmp .out
.none:
    test r12d, r12d
    jnz .out
    invoke msgbox, rbx, &s_up_none, MB_OK|MB_ICONINFO
    jmp .out
.failed:
    test r12d, r12d
    jnz .out
    invoke msgbox, rbx, &s_up_fail, MB_OK|MB_ICONWARNING
.out:
    invoke free, r13
.out0:
    xor eax, eax
    EPILOG 1600

upd_thread:
    PROLOG 64
    xor ecx, ecx
    mov edx, 1
    call update_check
    xor eax, eax
    EPILOG 64

; update_start(): background check when [Update] AutoCheck=1
update_start:
    PROLOG 64
    invoke GetPrivateProfileIntW, &sec_upd, &k_upauto, 0, &g_ini
    test eax, eax
    jz .d
    invoke CreateThread, 0, 0, &upd_thread, 0, 0, 0
    test rax, rax
    jz .d
    invoke CloseHandle, rax
.d:
    EPILOG 64
