import os, re
os.chdir(r'C:\Users\charles\workspace\becompare\gui')
exec(open('../tools/ph.py', encoding='utf-8').read())

patch('inc/win.inc', [("%define ID_BROWSE_O     110\n", "%define ID_BROWSE_O     110\n%define ID_SWAP         112\n")])

# ---------------------------------------------------------------- util.asm: icon font
u = open('util.asm', encoding='utf-8').read()
def repu(a, b, cnt=1):
    global u
    assert u.count(a) == cnt, (a[:60], u.count(a))
    u = u.replace(a, b)
repu("global g_hinst, g_hframe,", "global g_iconfont\nglobal g_hinst, g_hframe,")
repu('WSTR s_consolas, "Consolas"', 'WSTR s_consolas, "Consolas"\nWSTR s_mdl2, "Segoe MDL2 Assets"')
repu("g_mono:         resq 1\n", "g_mono:         resq 1\ng_iconfont:     resq 1\n")
repu("""    mov [g_mono], rax
    EPILOG 160""", """    mov [g_mono], rax
    invoke CreateFontW, rbx, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET, 0, 0, 5, 0, &s_mdl2
    mov [g_iconfont], rax
    EPILOG 160""")
open('util.asm', 'w', encoding='utf-8', newline='\n').write(u)

# ---------------------------------------------------------------- pathbar.asm: icon buttons, tooltips, swap
p = open('pathbar.asm', encoding='utf-8').read()
def repp(a, b, cnt=1):
    global p
    assert p.count(a) == cnt, (a[:60], p.count(a))
    p = p.replace(a, b)
repp("global ctl_color, mk_btn,", "global mk_icon, tip_add, glyph_swap\nglobal ctl_color, mk_btn,")
repp("extern mk, scl, browse_folder, browse_open", "extern mk, scl, browse_folder, browse_open, g_iconfont, g_hinst, CreateWindowExW, GetParent, GetWindowLongPtrW, PostMessageW")
repp('WSTR s_dots, "…"', 'WSTR s_dots, "…"\nWSTR cn_tip, "tooltips_class32"\nWSTR s_tip_swap, "좌우 경로 바꾸기"\nglyph_swap: dw 0xE8AB, 0')
repp("section .bss\n", "section .bss\n") if "section .bss" in p else None
p = p.replace("section .text\n\n; ctl_color", "section .bss\nalignb 8\ng_tip: resq 1\nsection .text\n\n; ctl_color", 1)

# mk_icon + tip_add after mk_lbl
repp("; mk_edit(parent, id)", """; mk_icon(parent, glyph string, id): flat icon button using the Segoe MDL2 glyph font
mk_icon:
    PROLOG 64
    mov rsi, rdx
    mov rdi, r8
    invoke mk, rcx, &cn_button, rsi, WS_TABSTOP, rdi
    mov rbx, rax
    test rax, rax
    jz .d
    invoke SendMessageW, rbx, WM_SETFONT, [g_iconfont], 1
.d:
    mov rax, rbx
    EPILOG 64

; tip_add(control hwnd, text): tooltip for a control (text must stay valid)
tip_add:
    PROLOG 192
    mov rsi, rcx
    mov rdi, rdx
    cmp qword [g_tip], 0
    jne .have
    invoke CreateWindowExW, 8, &cn_tip, 0, WS_POPUP|3, #0x80000000, #0x80000000, #0x80000000, #0x80000000, 0, 0, [g_hinst], 0
    mov [g_tip], rax
.have:
    invoke memset, &rsp+96, 0, 72
    mov dword [rsp+96], 72
    mov dword [rsp+100], 0x11          ; TTF_IDISHWND | TTF_SUBCLASS
    invoke GetParent, rsi
    mov [rsp+104], rax
    mov [rsp+112], rsi
    mov [rsp+144], rdi
    invoke SendMessageW, [g_tip], 0x0432, 0, &rsp+96     ; TTM_ADDTOOLW
    EPILOG 192

; mk_edit(parent, id)""")
p = p.replace("extern mk, scl,", "extern memset\nextern mk, scl,", 1)

# pb_create: swap button
repp("""    invoke mk_btn, rsi, &s_dots, ID_BROWSE_B
    invoke mk_btn, rsi, &s_compare, ID_COMPARE""", """    invoke mk_btn, rsi, &s_dots, ID_BROWSE_B
    invoke mk_icon, rsi, &glyph_swap, ID_SWAP
    invoke tip_add, rax, &s_tip_swap
    invoke mk_btn, rsi, &s_compare, ID_COMPARE""")

# pb_layout rewrite
a = p.index("; pb_layout(hview, width, y)")
b = p.index("; pb_load(hview, sess)")
p = p[:a] + r'''; pb_layout(hview, width, y) -> eax = y of the row below the path bar
pb_layout:
    PROLOG 96
    mov rsi, rcx
    mov r12d, edx                    ; width
    mov r13d, r8d                    ; y
    mov ecx, 4
    call scl
    mov r14d, eax                    ; gap
    mov ecx, 30
    call scl
    mov r15d, eax                    ; browse / swap button width
    mov ecx, 26
    call scl
    mov ebp, eax                     ; row height
    ; half = (width - 4*gap - swap) / 2
    mov eax, r14d
    shl eax, 2
    add eax, r15d
    mov edx, r12d
    sub edx, eax
    jns .pos
    xor edx, edx
.pos:
    shr edx, 1
    mov edi, edx                     ; half
    mov ebx, edi
    sub ebx, r15d                    ; edit width
    MVID rsi, ID_EDIT_A, r14, r13, rbx, rbp
    lea r12d, [r14+rbx]
    MVID rsi, ID_BROWSE_A, r12, r13, r15, rbp
    lea r12d, [r14+rdi]
    add r12d, r14d                   ; x of the swap button
    MVID rsi, ID_SWAP, r12, r13, r15, rbp
    add r12d, r15d
    add r12d, r14d                   ; x of the B cell
    MVID rsi, ID_EDIT_B, r12, r13, rbx, rbp
    add r12d, ebx
    MVID rsi, ID_BROWSE_B, r12, r13, r15, rbp
    lea eax, [r13+rbp]
    add eax, r14d
    EPILOG 96

''' + p[b:]

# pb_command: swap
repp("""pb_command:
    PROLOG 1200
    mov rsi, rcx
    mov r12d, edx
    mov r13d, r8d
    mov ebx, ID_EDIT_A""", """pb_command:
    PROLOG 1200
    mov rsi, rcx
    mov r12d, edx
    mov r13d, r8d
    cmp r12d, ID_SWAP
    je .swap
    mov ebx, ID_EDIT_A""")
repp(""".go:
    invoke GetDlgItem, rsi, rbx
    mov rdi, rax""", """.swap:
    lea r14, [rsp+96]
    lea r15, [rsp+640]
    invoke GetDlgItem, rsi, ID_EDIT_A
    mov rdi, rax
    invoke GetWindowTextW, rdi, r14, 259
    invoke GetDlgItem, rsi, ID_EDIT_B
    mov rbx, rax
    invoke GetWindowTextW, rbx, r15, 259
    invoke SetWindowTextW, rdi, r15
    invoke SetWindowTextW, rbx, r14
    invoke GetWindowLongPtrW, rsi, GWLP_USERDATA
    test rax, rax
    jz .swd
    mov rax, [rax+SS_TYPE]
    cmp rax, T_TEXT                  ; text views may hold unsaved edits: do not reload automatically
    je .swd
    cmp rax, T_MERGE
    je .swd
    invoke PostMessageW, rsi, WM_COMMAND, ID_COMPARE, 0
.swd:
    mov eax, 1
    EPILOG 1200
.go:
    invoke GetDlgItem, rsi, rbx
    mov rdi, rax""")
open('pathbar.asm', 'w', encoding='utf-8', newline='\n').write(p)

# ---------------------------------------------------------------- route ID_SWAP in every view
for fn in ['folder_ui.inc', 'text_ui.inc', 'hex_ui.inc', 'pic_ui2.inc', 'merge_ui.inc', 'table.asm']:
    s = open(fn, encoding='utf-8').read()
    n = s.count("    cmp ebx, ID_BROWSE_B\n    je .browse\n")
    assert n >= 1, (fn, n)
    s = s.replace("    cmp ebx, ID_BROWSE_B\n    je .browse\n", "    cmp ebx, ID_BROWSE_B\n    je .browse\n    cmp ebx, ID_SWAP\n    je .browse\n")
    open(fn, 'w', encoding='utf-8', newline='\n').write(s)

# ---------------------------------------------------------------- dark list-view headers
def header_theme(fn, listreg, themeregs):
    pass
f = open('folder_ui.inc', encoding='utf-8').read()
a = """    invoke SetWindowTheme, rsi, rdx, 0
    invoke InvalidateRect, rsi, 0, 1
    invoke theme_checks, [rbx+F_HVIEW]"""
assert f.count(a) == 1
f = f.replace(a, """    invoke SetWindowTheme, rsi, rdx, 0
    invoke SendMessageW, rsi, 0x101F, 0, 0                  ; LVM_GETHEADER
    lea rdx, [s_light_theme]
    cmp qword [g_dark], 0
    je .ht
    lea rdx, [s_dark_hdr]
.ht:
    invoke SetWindowTheme, rax, rdx, 0
    invoke InvalidateRect, rsi, 0, 1
    invoke theme_checks, [rbx+F_HVIEW]""")
open('folder_ui.inc', 'w', encoding='utf-8', newline='\n').write(f)
fo = open('folder.asm', encoding='utf-8').read()
fo = fo.replace('WSTR s_dark_theme, "DarkMode_Explorer"', 'WSTR s_dark_theme, "DarkMode_Explorer"\nWSTR s_dark_hdr, "DarkMode_ItemsView"', 1)
open('folder.asm', 'w', encoding='utf-8', newline='\n').write(fo)
print('ui1 patched')
