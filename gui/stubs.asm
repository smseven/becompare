; stubs.asm - placeholders for modules that are not implemented yet (STUB_<NAME> defines)
%include "inc/macros.inc"
%include "inc/win.inc"
%include "inc/app.inc"
extern CreateWindowExW, DefWindowProcW, FillRect, GetClientRect, MoveWindow
extern g_hinst, th_panelbrush
extern reg_class, mk

%macro STUB 1
%ifdef STUB_%1
global %1_register, %1_create
%1_register:
    PROLOG 64
    invoke reg_class, &cn_stub, &stub_proc, 0
    EPILOG 64
%1_create:
    PROLOG 128
    mov rbx, rcx
    mov rsi, rdx
    invoke CreateWindowExW, 0, &cn_stub, 0, WS_CHILD|WS_CLIPCHILDREN, 0, 0, 100, 100, rbx, 0, [g_hinst], rsi
    EPILOG 128
%endif
%endmacro

section .rdata
WSTR cn_stub, "BCStub"
WSTR cn_static, "STATIC"
WSTR s_stub, "이 모듈은 아직 구현되지 않았습니다."
section .text
STUB folder
STUB text
STUB table
STUB hex
STUB pic
STUB merge

stub_proc:
    PROLOG 192
    mov rsi, rcx
    mov edi, edx
    mov r12, r8
    mov r13, r9
    cmp edi, WM_CREATE
    je .create
    cmp edi, WM_ERASEBKGND
    je .erase
.def:
    invoke DefWindowProcW, rsi, rdi, r12, r13
    EPILOG 192
.create:
    invoke mk, rsi, &cn_static, &s_stub, 0, 1
    invoke MoveWindow, rax, 20, 20, 500, 24, 1
    xor eax, eax
    EPILOG 192
.erase:
    lea rbx, [rsp+96]
    invoke GetClientRect, rsi, rbx
    invoke FillRect, r12, rbx, [th_panelbrush]
    mov eax, 1
    EPILOG 192
