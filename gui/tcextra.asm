; tcextra.asm - TC-06: clipboard compare and Unix patch (unified diff) left/right view
%include "inc/macros.inc"
%include "inc/win.inc"
%include "inc/app.inc"

extern OpenClipboard, CloseClipboard, GetClipboardData, GlobalLock, GlobalUnlock
extern GetTempPathW, CreateDirectoryW, GetTickCount, CreateFileW, WriteFile, CloseHandle
extern malloc, free, wcslen, wcscat, _snwprintf, memcpy
extern read_file_bytes, write_utf8, add_session, browse_open, msgbox, set_status

global clip_compare, patch_open, patch_cmd
extern wcsncpy

section .rdata
WSTR s_tmpdir, "BeCompareAsm\"
WSTR f_clip, "clipboard_%X.txt"
WSTR f_pl, "patch_%X_old.txt"
WSTR f_pr, "patch_%X_new.txt"
WSTR s_empty, ""
WSTR s_noclip, "클립보드에 텍스트가 없습니다."
WSTR s_nopatch, "패치 파일을 읽을 수 없거나 비교할 변경 내용이 없습니다."
WSTR s_cantwrite, "임시 파일을 만들 수 없습니다."

section .text

; tc_tmp(out wchar[520], format, id) : %TEMP%\BeCompareAsm\<formatted name>
tc_tmp:
    PROLOG 64
    mov rbx, rcx
    mov rsi, rdx
    mov rdi, r8
    invoke GetTempPathW, 400, rbx
    invoke wcscat, rbx, &s_tmpdir
    invoke CreateDirectoryW, rbx, 0
    invoke wcslen, rbx
    lea r12, [rbx+rax*2]
    invoke _snwprintf, r12, 60, rsi, rdi
    EPILOG 64

; clip_compare(owner): a new text session whose right side is the clipboard text
clip_compare:
    PROLOG 1200
    mov rbx, rcx
    xor edi, edi
    invoke OpenClipboard, rbx
    test eax, eax
    jz .none
    invoke GetClipboardData, 13                       ; CF_UNICODETEXT
    test rax, rax
    jz .close
    mov rsi, rax
    invoke GlobalLock, rsi
    test rax, rax
    jz .close
    mov r12, rax
    invoke GetTickCount
    mov r13d, eax
    invoke tc_tmp, &rsp+96, &f_clip, r13
    invoke write_utf8, &rsp+96, r12, -1, 1
    mov edi, eax
    invoke GlobalUnlock, rsi
.close:
    invoke CloseClipboard
    test edi, edi
    jz .none
    invoke add_session, T_TEXT, &s_empty, &rsp+96, 0
    EPILOG 1200
.none:
    invoke msgbox, rbx, &s_noclip, MB_OK|MB_ICONINFO
    EPILOG 1200

; tc_put(handle, buf, len)
tc_put:
    PROLOG 64
    mov rbx, rcx
    mov rsi, rdx
    mov rdi, r8
    test rdi, rdi
    jz .d
    invoke WriteFile, rbx, rsi, rdi, &rsp+80, 0
.d:
    EPILOG 64

; patch_open(owner): choose a unified diff and show its old / new text side by side
%define P_OLD  96
%define P_NEW  1200
%define P_PATH 2304
patch_open:
    PROLOG 3440
    mov r14, rcx
    mov word [rsp+P_PATH], 0
    mov rax, [g_patch_pre]
    test rax, rax
    jz .ask
    invoke wcsncpy, &rsp+P_PATH, rax, 519
    mov word [rsp+P_PATH+1038], 0
    jmp .gotp
.ask:
    invoke browse_open, r14, &rsp+P_PATH
    test eax, eax
    jz .d
.gotp:
    invoke read_file_bytes, &rsp+P_PATH, &rsp+3360
    test rax, rax
    jz .bad
    mov r12, rax                       ; bytes
    mov r13, [rsp+3360]                ; size
    ; outputs: old / new byte buffers (each at most the input size + headers)
    lea rcx, [r13+r13+64]
    call malloc
    mov rbx, rax                       ; old
    lea rcx, [r13+r13+64]
    call malloc
    mov rbp, rax                       ; new
    mov [rsp+3368], rbx
    mov [rsp+3376], rbp
    mov rdi, rbx                       ; old write pointer
    mov rsi, rbp                       ; new write pointer
    xor r15d, r15d                     ; read index
    xor r11d, r11d                     ; inside a hunk
.line:
    cmp r15, r13
    jae .done
    lea r8, [r12+r15]                  ; line start
    xor ecx, ecx
.eol:
    lea rax, [r15+rcx]
    cmp rax, r13
    jae .gotl
    cmp byte [r12+rax], 10
    je .gotl
    inc ecx
    jmp .eol
.gotl:
    ; ecx = length without LF; strip a trailing CR
    mov r9d, ecx
    test r9d, r9d
    jz .adv
    cmp byte [r8+r9-1], 13
    jne .nocr
    dec r9d
.nocr:
    movzx eax, byte [r8]
    test r9d, r9d
    jz .blank
    ; file headers
    cmp eax, '+'
    jne .ncp
    cmp r9d, 3
    jb .ncp
    cmp word [r8+1], '++'
    jne .ncp
    cmp byte [r8+3], ' '
    jne .ncp
    xor r11d, r11d
    jmp .hdr
.ncp:
    cmp eax, '-'
    jne .nhm
    cmp r9d, 3
    jb .nhm
    cmp word [r8+1], '--'
    jne .nhm
    cmp byte [r8+3], ' '
    jne .nhm
    xor r11d, r11d
    jmp .hdr
.nhm:
    cmp eax, '@'
    jne .body
    cmp r9d, 2
    jb .body
    cmp byte [r8+1], '@'
    jne .body
    mov r11d, 1
    jmp .hdr
.body:
    test r11d, r11d
    jz .adv                            ; text outside hunks (diff --git, index, ...)
    cmp eax, ' '
    je .ctx
    cmp eax, '-'
    je .rem
    cmp eax, '+'
    je .add
    cmp eax, '\'
    je .adv                            ; "\ No newline at end of file"
    jmp .adv
.blank:
    test r11d, r11d
    jz .adv
    jmp .ctxblank
.hdr:
    ; headers go to both sides so the files stay aligned
    mov r10d, ecx
    mov rdx, r8
    ; old side
    mov rcx, rdi
    mov rdx, r8
    mov r8d, r9d
    call .copy
    mov rdi, rax
    mov byte [rdi], 10
    inc rdi
    lea r8, [r12+r15]
    mov rcx, rsi
    mov rdx, r8
    mov r8d, r9d
    call .copy
    mov rsi, rax
    mov byte [rsi], 10
    inc rsi
    mov ecx, r10d
    jmp .adv
.ctx:
    lea rdx, [r8+1]
    lea r8d, [r9-1]
    mov r10d, ecx
    mov rcx, rdi
    call .copy
    mov rdi, rax
    mov byte [rdi], 10
    inc rdi
    lea r8, [r12+r15]
    lea rdx, [r8+1]
    lea r8d, [r9-1]
    mov rcx, rsi
    call .copy
    mov rsi, rax
    mov byte [rsi], 10
    inc rsi
    mov ecx, r10d
    jmp .adv
.ctxblank:
    mov byte [rdi], 10
    inc rdi
    mov byte [rsi], 10
    inc rsi
    jmp .adv
.rem:
    lea rdx, [r8+1]
    lea r8d, [r9-1]
    mov r10d, ecx
    mov rcx, rdi
    call .copy
    mov rdi, rax
    mov byte [rdi], 10
    inc rdi
    mov ecx, r10d
    jmp .adv
.add:
    lea rdx, [r8+1]
    lea r8d, [r9-1]
    mov r10d, ecx
    mov rcx, rsi
    call .copy
    mov rsi, rax
    mov byte [rsi], 10
    inc rsi
    mov ecx, r10d
.adv:
    lea r15, [r15+rcx+1]
    jmp .line
; .copy(dst rcx, src rdx, len r8d) -> rax = dst end
.copy:
    push r9
    xor eax, eax
.cl:
    cmp eax, r8d
    jae .cd
    mov r9b, [rdx+rax]
    mov [rcx+rax], r9b
    inc eax
    jmp .cl
.cd:
    add rax, rcx
    pop r9
    ret
.done:
    ; sizes
    sub rdi, rbx
    mov [rsp+3384], rdi
    sub rsi, rbp
    mov [rsp+3392], rsi
    test rdi, rdi
    jnz .have
    test rsi, rsi
    jz .empty
.have:
    invoke GetTickCount
    mov r13d, eax
    invoke tc_tmp, &rsp+P_OLD, &f_pl, r13
    invoke tc_tmp, &rsp+P_NEW, &f_pr, r13
    invoke CreateFileW, &rsp+P_OLD, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0
    cmp rax, -1
    je .werr
    mov r15, rax
    invoke tc_put, r15, rbx, [rsp+3384]
    invoke CloseHandle, r15
    invoke CreateFileW, &rsp+P_NEW, GENERIC_WRITE, 0, 0, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, 0
    cmp rax, -1
    je .werr
    mov r15, rax
    invoke tc_put, r15, rbp, [rsp+3392]
    invoke CloseHandle, r15
    invoke free, rbx
    invoke free, rbp
    invoke free, r12
    invoke add_session, T_TEXT, &rsp+P_OLD, &rsp+P_NEW, 0
    jmp .d
.werr:
    invoke free, rbx
    invoke free, rbp
    invoke free, r12
    invoke msgbox, r14, &s_cantwrite, MB_OK|MB_ICONWARNING
    jmp .d
.empty:
    invoke free, rbx
    invoke free, rbp
    invoke free, r12
.bad:
    invoke msgbox, r14, &s_nopatch, MB_OK|MB_ICONINFO
.d:
    EPILOG 3440

section .bss
alignb 8
g_patch_pre: resq 1
section .text

; patch_cmd(path): command line entry (bcgui patch FILE)
patch_cmd:
    PROLOG 64
    mov [g_patch_pre], rcx
    xor ecx, ecx
    call patch_open
    mov qword [g_patch_pre], 0
    EPILOG 64
