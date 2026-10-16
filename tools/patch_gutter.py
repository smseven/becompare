import os
os.chdir(r'C:\Users\charles\workspace\becompare\gui')
exec(open('../tools/ph.py', encoding='utf-8').read())

g = open('text_gutter.inc', encoding='utf-8').read()
def repg(a, b, cnt=1):
    global g
    assert g.count(a) == cnt, (a[:60], g.count(a))
    g = g.replace(a, b)
repg("""    lea edx, [rcx+1]
    invoke _snwprintf, &rsp+P_BUF, 12, &f_lineno, rdx""", """    lea r13d, [rcx+1]
    invoke _snwprintf, &rsp+P_BUF, 12, &f_lineno, r13""")
repg("0x8822   ; DT_RIGHT | DT_VCENTER | DT_SINGLELINE | DT_NOPREFIX", "0x0826   ; DT_RIGHT | DT_VCENTER | DT_SINGLELINE | DT_NOPREFIX")
repg("0x8820            ; DT_LEFT variant: DT_VCENTER | DT_SINGLELINE | DT_NOPREFIX", "0x0824            ; DT_LEFT | DT_VCENTER | DT_SINGLELINE | DT_NOPREFIX")
open('text_gutter.inc', 'w', encoding='utf-8', newline='\n').write(g)

# ---- text.asm
t = open('text.asm', encoding='utf-8').read()
def rept(a, b, cnt=1):
    global t
    assert t.count(a) == cnt, (a[:60], t.count(a))
    t = t.replace(a, b)
rept("%define TV_NLA    2256\n%define TV_NLB    2264\n%define TV_SIZE   2280", """%define TV_NLA    2256
%define TV_NLB    2264
%define TV_GT0    2272
%define TV_GT1    2296
%define TV_HGL    2320
%define TV_HGR    2328
%define TV_HMM    2336
%define TV_FORCE  2344
%define TV_SIZE   2368
%define ID_GUL    263
%define ID_GUR    264
%define ID_MINI   265""")
rept("extern g_hinst,", "extern DrawTextW, SelectObject, SetBkMode, SetTextColor, FrameRect, CreateSolidBrush, DeleteObject, BeginPaint, EndPaint\nextern g_font, g_iconfont, th_same, th_conf\nextern g_hinst,")
rept("""    invoke reg_class, &cn_text, &tv_proc, 0
""", """    invoke reg_class, &cn_text, &tv_proc, 0
    invoke reg_class, &cn_gutter, &gt_proc, 0
    invoke reg_class, &cn_mini, &mm_proc, 0
""")
rept('WSTR f_info, "차이 %llu개 · 현재 %llu/%llu · 줄 %llu ↔ %llu"', '''WSTR f_info, "차이 %llu개 · 현재 %llu/%llu · 줄 %llu ↔ %llu · %s · %s"
WSTR en_ansi, "ANSI"
WSTR en_utf8, "UTF-8"
WSTR en_utf8b, "UTF-8 BOM"
WSTR en_u16, "UTF-16"
WSTR eol_lf, "LF"
WSTR eol_crlf, "CRLF"''')
rept("WSTR f_same, \"두 파일이 같습니다 · 줄 %llu ↔ %llu\"", "WSTR f_same, \"두 파일이 같습니다 · 줄 %llu ↔ %llu · %s · %s\"")
rept("section .text\n\ntext_register:", "section .rdata\nalign 8\nenc_names: dq en_ansi, en_utf8, en_utf8b, en_u16\neol_names: dq eol_lf, eol_crlf\nsection .text\n\ntext_register:")
t = t.rstrip('\n') + '\n%include "text_gutter.inc"\n'
open('text.asm', 'w', encoding='utf-8', newline='\n').write(t)

# ---- text_ui.inc
u = open('text_ui.inc', encoding='utf-8').read()
def repu(a, b, cnt=1):
    global u
    assert u.count(a) == cnt, (a[:60], u.count(a))
    u = u.replace(a, b)

# tv_info with encoding / eol, bigger frame
a = u.index("; tv_info(hwnd, tv)")
b = u.index("; ---------------------------------------------------------------- compare")
u = u[:a] + r'''; tv_info(hwnd, tv)
tv_info:
    PROLOG 400
    mov rsi, rcx
    mov rbx, rdx
    mov r12, [rbx+TV_NBLK]
    mov eax, [rbx+TV_TXA+16]
    and eax, 3
    lea rcx, [enc_names]
    mov r14, [rcx+rax*8]
    mov eax, [rbx+TV_TXA+20]
    and eax, 1
    lea rcx, [eol_names]
    mov r15, [rcx+rax*8]
    test r12, r12
    jnz .diffs
    mov r9, [rbx+TV_NLA]
    mov rax, [rbx+TV_NLB]
    mov [rsp+32], rax
    mov [rsp+40], r14
    mov [rsp+48], r15
    lea rcx, [rsp+96]
    mov edx, 140
    lea r8, [f_same]
    call _snwprintf
    jmp .set
.diffs:
    mov rax, [rbx+TV_CUR]
    inc rax
    mov [rsp+32], r12
    mov rcx, [rbx+TV_NLA]
    mov [rsp+40], rcx
    mov rcx, [rbx+TV_NLB]
    mov [rsp+48], rcx
    mov [rsp+56], r14
    mov [rsp+64], r15
    mov r9, rax
    lea rcx, [rsp+96]
    mov edx, 140
    lea r8, [f_info]
    ; args: buf, cnt, fmt, nblk, cur, nblk, NLA, NLB, enc, eol -> r9 = nblk
    mov r9, r12
    mov [rsp+32], rax
    mov [rsp+40], r12
    mov rax, [rbx+TV_NLA]
    mov [rsp+48], rax
    mov rax, [rbx+TV_NLB]
    mov [rsp+56], rax
    mov [rsp+64], r14
    mov [rsp+72], r15
    call _snwprintf
.set:
    invoke GetDlgItem, rsi, ID_LBL_INFO
    invoke SetWindowTextW, rax, &rsp+96
    EPILOG 400

''' + u[b:]
# same-file format needs enc/eol as 3rd/4th args: fix f_same call (r8=NLA r9=NLB, stack enc/eol) -> uses [rsp+32],[rsp+40] already

# forced block in tv_copy
repu("""    invoke tv_curblock, rbx
    cmp rax, -1
    je .none
    mov r14, rax
    mov rcx, [rbx+TV_BLK]""", """    mov rax, [rbx+TV_FORCE]
    cmp rax, -1
    jne .forced
    invoke tv_curblock, rbx
    cmp rax, -1
    je .none
    jmp .gotblk
.forced:
    mov qword [rbx+TV_FORCE], -1
.gotblk:
    mov r14, rax
    mov rcx, [rbx+TV_BLK]""")

# redraw hooks
repu("""    invoke tv_info, rsi, rbx
    cmp qword [rbx+TV_NBLK], 0
    je .ok
    invoke tv_goto, rsi, rbx, 0""", """    invoke tv_info, rsi, rbx
    invoke tv_redraw_aux, rbx
    cmp qword [rbx+TV_NBLK], 0
    je .ok
    invoke tv_goto, rsi, rbx, 0""")
repu("""    mov [rbx+TV_CUR], r12
    invoke tv_info, rsi, rbx
    EPILOG 96""", """    mov [rbx+TV_CUR], r12
    invoke tv_info, rsi, rbx
    invoke tv_redraw_aux, rbx
    EPILOG 96""")

# layout of gutters / panes / map
a = u.index(".h:\n    mov ebx, [rsp+104]\n    shr ebx, 1\n    sub ebx, 2                       ; width of one pane")
b = u.index("; ---------------------------------------------------------------- options string")
u = u[:a] + r'''.h:
    mov ecx, 46
    call scl
    mov r14d, eax                    ; gutter width
    mov ecx, 14
    call scl
    mov r12d, eax                    ; overview map width
    mov eax, [rsp+104]
    mov ecx, r14d
    shl ecx, 1
    sub eax, ecx
    sub eax, r12d
    sub eax, 8
    jns .pw
    xor eax, eax
.pw:
    shr eax, 1
    mov ebx, eax                     ; pane width
    MVID rsi, ID_GUL, 0, r13, r14, rbp
    MVID rsi, ID_RA, r14, r13, rbx, rbp
    mov edi, r14d
    add edi, ebx
    add edi, 4
    MVID rsi, ID_GUR, rdi, r13, r14, rbp
    add edi, r14d
    MVID rsi, ID_RB, rdi, r13, rbx, rbp
    add edi, ebx
    add edi, 2
    MVID rsi, ID_MINI, rdi, r13, r12, rbp
    EPILOG 192

''' + u[b:]

# create gutters + map
repu("""    invoke rich_create, rsi, ID_RB
    mov [r15+TV_HB], rax
""", """    invoke rich_create, rsi, ID_RB
    mov [r15+TV_HB], rax
    mov qword [r15+TV_FORCE], -1
    mov [r15+TV_GT0], r15
    mov qword [r15+TV_GT0+8], 0
    mov [r15+TV_GT0+16], rsi
    mov [r15+TV_GT1], r15
    mov qword [r15+TV_GT1+8], 1
    mov [r15+TV_GT1+16], rsi
    invoke CreateWindowExW, 0, &cn_gutter, 0, WS_CHILD|WS_VISIBLE|WS_CLIPSIBLINGS, 0, 0, 10, 10, rsi, ID_GUL, [g_hinst], &r15+TV_GT0
    mov [r15+TV_HGL], rax
    invoke CreateWindowExW, 0, &cn_gutter, 0, WS_CHILD|WS_VISIBLE|WS_CLIPSIBLINGS, 0, 0, 10, 10, rsi, ID_GUR, [g_hinst], &r15+TV_GT1
    mov [r15+TV_HGR], rax
    invoke CreateWindowExW, 0, &cn_mini, 0, WS_CHILD|WS_VISIBLE|WS_CLIPSIBLINGS, 0, 0, 10, 10, rsi, ID_MINI, [g_hinst], r15
    mov [r15+TV_HMM], rax
""")
# scrolling repaints the gutters (deferred, the control scrolls after notifying)
repu(""".rich:
    cmp ebp, EN_VSCROLL
    jne .zero""", """.rich:
    cmp ebp, EN_VSCROLL
    jne .zero
    invoke PostMessageW, rsi, WM_APP+50, 0, 0""")
repu("""    cmp edi, BC_THEME
    je .theme
    cmp edi, WM_CTLCOLOREDIT""", """    cmp edi, BC_THEME
    je .theme
    cmp edi, WM_APP+50
    je .redraw
    cmp edi, WM_CTLCOLOREDIT""")
repu(""".run:
    invoke text_compare, rsi, r15, r14
    jmp .zero""", """.run:
    invoke text_compare, rsi, r15, r14
    jmp .zero
.redraw:
    invoke tv_redraw_aux, r15
    jmp .zero""")
open('text_ui.inc', 'w', encoding='utf-8', newline='\n').write(u)
t = open('text.asm', encoding='utf-8').read()
t = t.replace("extern CreateWindowExW, DefWindowProcW, SendMessageW,", "extern PostMessageW\nextern CreateWindowExW, DefWindowProcW, SendMessageW,", 1)
open('text.asm', 'w', encoding='utf-8', newline='\n').write(t)
print('gutter patched')
