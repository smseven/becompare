
; ---------------------------------------------------------------- tiny modal text input
extern IsDialogMessageW
global input_box

section .rdata
WSTR cn_ib, "BCInputBox"
WSTR s_ib_ok, "확인"
WSTR s_ib_cancel, "취소"

section .bss
alignb 8
g_ib_result: resq 1
g_ib_wc: resq 1

section .text

ib_proc:
    PROLOG 320
    mov rsi, rcx
    mov edi, edx
    mov r12, r8
    mov r13, r9
    cmp edi, WM_CREATE
    je .create
    cmp edi, WM_COMMAND
    je .command
    cmp edi, WM_CLOSE
    je .close
    cmp edi, WM_ERASEBKGND
    je .erase
    cmp edi, WM_CTLCOLORSTATIC
    je .cstatic
    cmp edi, WM_CTLCOLOREDIT
    je .cedit
    cmp edi, WM_CTLCOLORBTN
    je .cstatic
.def:
    invoke DefWindowProcW, rsi, rdi, r12, r13
    EPILOG 320
.create:
    mov rax, [r13]
    mov r14, [rax]                    ; buffer
    invoke SetWindowLongPtrW, rsi, GWLP_USERDATA, r14
    invoke mk_edit, rsi, 801
    mov rbx, rax
    invoke SetWindowTextW, rbx, r14
    mov ecx, 12
    call scl
    mov r12d, eax
    mov ecx, 14
    call scl
    mov r13d, eax
    mov ecx, 480
    call scl
    mov r15d, eax
    mov ecx, 26
    call scl
    invoke MoveWindow, rbx, r12, r13, r15, rax, 1
    invoke mk_btn, rsi, &s_ib_ok, 1
    mov rbx, rax
    invoke SendMessageW, rbx, 0xF4, 1, 1             ; BM_SETSTYLE: default push button
    mov ecx, 296
    call scl
    mov r12d, eax
    mov ecx, 58
    call scl
    mov r13d, eax
    mov ecx, 90
    call scl
    mov r15d, eax
    mov ecx, 28
    call scl
    invoke MoveWindow, rbx, r12, r13, r15, rax, 1
    invoke mk_btn, rsi, &s_ib_cancel, 2
    mov rbx, rax
    mov ecx, 396
    call scl
    mov r12d, eax
    mov ecx, 28
    call scl
    invoke MoveWindow, rbx, r12, r13, r15, rax, 1
    invoke GetDlgItem, rsi, 801
    mov rbx, rax
    invoke SetFocus, rbx
    invoke SendMessageW, rbx, EM_SETSEL, 0, -1
    xor eax, eax
    EPILOG 320
.command:
    movzx eax, r12w
    cmp eax, 1
    je .ok
    cmp eax, 2
    je .close
    jmp .zero
.ok:
    invoke GetWindowLongPtrW, rsi, GWLP_USERDATA
    mov r14, rax
    invoke GetDlgItem, rsi, 801
    invoke GetWindowTextW, rax, r14, 259
    mov qword [g_ib_result], 1
    jmp .zero
.close:
    mov qword [g_ib_result], 0
    jmp .zero
.erase:
    invoke GetClientRect, rsi, &rsp+96
    invoke FillRect, r12, &rsp+96, [th_panelbrush]
    mov eax, 1
    EPILOG 320
.cstatic:
    invoke ctl_color, r12, 1
    EPILOG 320
.cedit:
    invoke ctl_color, r12, 0
    EPILOG 320
.zero:
    xor eax, eax
    EPILOG 320

; input_box(owner, title, buf (in: initial text, out: result, 260 wchar)) -> eax 1 when confirmed
input_box:
    PROLOG 256
    mov rbx, rcx
    mov rsi, rdx
    mov [rsp+192], r8
    cmp qword [g_ib_wc], 0
    jne .have
    invoke reg_class, &cn_ib, &ib_proc, [th_panelbrush]
    mov qword [g_ib_wc], 1
.have:
    invoke GetWindowRect, rbx, &rsp+96
    mov ecx, 520
    call scl
    mov r12d, eax
    mov ecx, 130
    call scl
    mov r14d, eax
    mov eax, [rsp+104]
    sub eax, [rsp+96]
    sub eax, r12d
    sar eax, 1
    add eax, [rsp+96]
    mov r13d, eax
    mov eax, [rsp+108]
    sub eax, [rsp+100]
    sub eax, r14d
    sar eax, 1
    add eax, [rsp+100]
    mov r15d, eax
    mov qword [g_ib_result], -1
    invoke CreateWindowExW, 1, &cn_ib, rsi, WS_POPUP|WS_CAPTION|WS_SYSMENU|WS_VISIBLE|WS_CLIPCHILDREN, r13, r15, r12, r14, rbx, 0, [g_hinst], &rsp+192
    mov rdi, rax
    test rax, rax
    jz .fail
    invoke EnableWindow, rbx, 0
.loop:
    cmp qword [g_ib_result], -1
    jne .done
    invoke GetMessageW, &rsp+96, 0, 0, 0
    test eax, eax
    jle .quit
    invoke IsDialogMessageW, rdi, &rsp+96
    test eax, eax
    jnz .loop
    invoke TranslateMessage, &rsp+96
    invoke DispatchMessageW, &rsp+96
    jmp .loop
.quit:
    mov qword [g_ib_result], 0
    invoke PostQuitMessage, 0
.done:
    invoke EnableWindow, rbx, 1
    invoke DestroyWindow, rdi
    invoke SetFocus, rbx
    mov rax, [g_ib_result]
    EPILOG 256
.fail:
    xor eax, eax
    EPILOG 256
